import os
import sys
import json
import time
import sqlite3
import subprocess
import re
import ast
import shutil
import importlib.util
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, List

import requests
from dotenv import load_dotenv

try:
    from groq import Groq
except ImportError:
    Groq = None


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv(override=True)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "").strip()

GROQ_MODEL = os.environ.get(
    "GROQ_MODEL",
    "openai/gpt-oss-120b",
).strip()

OPENROUTER_MODEL = os.environ.get(
    "OPENROUTER_MODEL",
    "meta-llama/llama-3.3-70b-instruct",
).strip()

groq_client = (
    Groq(api_key=GROQ_API_KEY)
    if Groq and GROQ_API_KEY
    else None
)


# ============================================================
# DIRECTORIES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DIRS = {
    "sandbox": BASE_DIR / "sandbox",
    "candidate": BASE_DIR / "candidate_skills",
    "active": BASE_DIR / "active_skills",
    "cemetery": BASE_DIR / "neural_cemetery",
    "backups": BASE_DIR / "backups",
    "reports": BASE_DIR / "evaluation_reports",
    "manifests": BASE_DIR / "skill_manifests",
}

for directory in DIRS.values():
    directory.mkdir(parents=True, exist_ok=True)


# ============================================================
# STORAGE
# ============================================================

DB_PATH = BASE_DIR / "shared_memory.db"
SKILLS_LOG_PATH = BASE_DIR / "skills_log.jsonl"
SKILLS_CATALOG_PATH = BASE_DIR / "skills_catalog.json"

MAX_SKILL_SECONDS = 30
MAX_RETRIES = 3


# ============================================================
# PROMPTS
# ============================================================

PLANNER_PROMPT = """
You are the Master Planner of an autonomous Python Skill Factory.

Review the existing skill catalog and decide ONE useful advanced Python
utility that should be built next.

The skill must be:
- practical
- self-contained
- safe
- reusable
- based on the standard library whenever possible

Respond with ONLY 1-2 sentences describing the skill.
""".strip()


BUILDER_PROMPT = """
You are the Coder inside an autonomous Python Skill Factory.

Generate ONLY valid Python source code.

STRICT CONTRACT:

1. Define:
   SAMPLE_ARGS = {...}

2. Define:
   def run(args: dict) -> dict:

3. run() must return a JSON-serializable dict.

4. Do not require interactive input.

5. Do not use:
   - subprocess
   - os.system
   - eval
   - exec
   - ctypes
   - socket
   - raw shell commands

6. Prefer Python standard library.

7. The module must be self-contained.

8. The module must be safe to execute inside a sandbox.

9. Include:
   if __name__ == "__main__":
       print(run(SAMPLE_ARGS))

Return ONLY Python code.
Do not use markdown fences.
""".strip()


REVIEWER_PROMPT = """
You are the security reviewer for an autonomous Python Skill Factory.

Review the supplied Python skill.

Reply with ONLY one of:

APPROVED

or

SAFE

or

REJECTED: <short reason>

Reject code that contains:
- subprocess
- os.system
- eval
- exec
- ctypes
- shell execution
- destructive filesystem operations
- network abuse
- credential theft
- persistence mechanisms
- dangerous system manipulation
""".strip()


# ============================================================
# UTILITIES
# ============================================================

def safe_text(value: Any, default: str = "") -> str:
    """
    Convert arbitrary model/API output safely to text.
    Prevents NoneType.strip() errors.
    """
    if value is None:
        return default

    try:
        return str(value).strip()
    except Exception:
        return default


def append_log(event: Dict[str, Any]) -> None:
    try:
        with SKILLS_LOG_PATH.open("a", encoding="utf-8") as file:
            file.write(
                json.dumps(
                    event,
                    ensure_ascii=False,
                    default=str,
                )
                + "\n"
            )
    except Exception as exc:
        print(f"⚠️ Log error: {exc}")


def backup_file(source: Path, label: str) -> Optional[Path]:
    if not source.exists():
        return None

    timestamp = time.strftime("%Y%m%d_%H%M%S")

    destination = (
        DIRS["backups"]
        / f"{source.stem}_{label}_{timestamp}{source.suffix}"
    )

    shutil.copy2(source, destination)

    return destination


# ============================================================
# OPENROUTER
# ============================================================

def call_openrouter(
    system_prompt: str,
    user_prompt: str,
) -> str:

    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not configured.")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "system",
                "content": safe_text(system_prompt),
            },
            {
                "role": "user",
                "content": safe_text(user_prompt),
            },
        ],
    }

    last_error = None

    for attempt in range(3):

        try:

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )

            if response.status_code in (429, 402):

                print(
                    f"⚠️ OpenRouter rate/billing limit "
                    f"(HTTP {response.status_code})."
                )

                time.sleep(5)
                continue

            response.raise_for_status()

            data = response.json()

            choices = data.get("choices") or []

            if not choices:
                raise RuntimeError(
                    "OpenRouter returned no choices."
                )

            message = choices[0].get("message") or {}

            content = message.get("content")

            if content is None:
                raise RuntimeError(
                    "OpenRouter returned empty content."
                )

            return safe_text(content)

        except Exception as exc:

            last_error = exc

            if attempt < 2:
                time.sleep(2)
            else:
                break

    raise RuntimeError(
        f"OpenRouter failed: {last_error}"
    )


# ============================================================
# Groq
# ============================================================

def call_groq(
    system_prompt: str,
    user_prompt: str,
) -> str:

    if groq_client is None:
        raise RuntimeError("Groq client unavailable.")

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": safe_text(system_prompt),
            },
            {
                "role": "user",
                "content": safe_text(user_prompt),
            },
        ],
        timeout=60,
    )

    choices = getattr(response, "choices", None)

    if not choices:
        raise RuntimeError("Groq returned no choices.")

    message = getattr(choices[0], "message", None)

    if message is None:
        raise RuntimeError("Groq returned no message.")

    content = getattr(message, "content", None)

    if content is None:
        raise RuntimeError("Groq returned empty content.")

    return safe_text(content)


# ============================================================
# MODEL FALLBACK
# ============================================================

def call_ai(
    system_prompt: str,
    user_prompt: str,
) -> str:

    # First attempt: Groq
    if groq_client is not None:

        try:
            result = call_groq(
                system_prompt,
                user_prompt,
            )

            if result:
                return result

        except Exception as exc:

            print(
                f"⚠️ Groq failed: {exc}"
            )

            print(
                "🔄 Switching to OpenRouter..."
            )

    # Second attempt: OpenRouter
    try:

        result = call_openrouter(
            system_prompt,
            user_prompt,
        )

        if result:
            return result

    except Exception as exc:

        print(
            f"⚠️ OpenRouter failed: {exc}"
        )

    return ""


# ============================================================
# CODE CLEANER
# ============================================================

def clean_code(raw_text: Any) -> str:

    text = safe_text(raw_text)

    if not text:
        return ""

    # Remove markdown code fences
    text = re.sub(
        r"^\s*```(?:python|py)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\s*```\s*$",
        "",
        text,
        flags=re.IGNORECASE,
    )

    return text.strip()


# ============================================================
# STATIC SECURITY CHECK
# ============================================================

FORBIDDEN_IMPORTS = {
    "subprocess",
    "ctypes",
    "socket",
}

FORBIDDEN_CALLS = {
    "eval",
    "exec",
    "system",
    "popen",
}


def static_check(code: str) -> List[str]:

    issues: List[str] = []

    code = safe_text(code)

    if not code:
        return ["Empty code."]

    # Syntax validation first
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return [
            f"SyntaxError: {exc}"
        ]

    # Required interface
    if not re.search(
        r"^\s*def\s+run\s*\(\s*args\s*:\s*dict",
        code,
        re.MULTILINE,
    ):
        issues.append(
            "Missing required def run(args: dict)."
        )

    if not re.search(
        r"^\s*SAMPLE_ARGS\s*=",
        code,
        re.MULTILINE,
    ):
        issues.append(
            "Missing SAMPLE_ARGS."
        )

    if "__main__" not in code:
        issues.append(
            "Missing __main__ self-test."
        )

    # AST security inspection
    for node in ast.walk(tree):

        if isinstance(node, ast.Import):

            for alias in node.names:

                root = alias.name.split(".")[0]

                if root in FORBIDDEN_IMPORTS:
                    issues.append(
                        f"Forbidden import: {root}"
                    )

        elif isinstance(node, ast.ImportFrom):

            root = (
                node.module.split(".")[0]
                if node.module
                else ""
            )

            if root in FORBIDDEN_IMPORTS:
                issues.append(
                    f"Forbidden import: {root}"
                )

        elif isinstance(node, ast.Call):

            if isinstance(node.func, ast.Name):

                if node.func.id in FORBIDDEN_CALLS:
                    issues.append(
                        f"Forbidden call: {node.func.id}"
                    )

            elif isinstance(node.func, ast.Attribute):

                if node.func.attr in FORBIDDEN_CALLS:
                    issues.append(
                        f"Forbidden call: {node.func.attr}"
                    )

    # Raw textual protection
    dangerous_patterns = [
        r"os\.system\s*\(",
        r"subprocess\.",
        r"\beval\s*\(",
        r"\bexec\s*\(",
        r"__import__\s*\(",
    ]

    for pattern in dangerous_patterns:

        if re.search(pattern, code):
            issues.append(
                f"Forbidden pattern: {pattern}"
            )

    return sorted(set(issues))


# ============================================================
# SKILL CATALOG
# ============================================================

def load_catalog() -> List[Dict[str, Any]]:

    if not SKILLS_CATALOG_PATH.exists():
        return []

    try:

        data = json.loads(
            SKILLS_CATALOG_PATH.read_text(
                encoding="utf-8"
            )
        )

        return data if isinstance(data, list) else []

    except Exception as exc:

        print(
            f"⚠️ Catalog read error: {exc}"
        )

        return []


def add_to_catalog(
    name: str,
    spec: str,
) -> None:

    catalog = load_catalog()

    catalog.append(
        {
            "name": name,
            "spec": safe_text(spec),
            "time": time.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "status": "active",
        }
    )

    SKILLS_CATALOG_PATH.write_text(
        json.dumps(
            catalog,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


# ============================================================
# RECENT SKILLS
# ============================================================

def get_recent_skills() -> str:

    paths = list(
        DIRS["active"].glob(
            "skill_module_*.py"
        )
    )

    if not paths:
        return "No existing skills yet."

    valid_paths = []

    for path in paths:

        match = re.search(
            r"(\d+)",
            path.name,
        )

        if match:
            valid_paths.append(
                (
                    int(match.group(1)),
                    path,
                )
            )

    valid_paths.sort(
        key=lambda item: item[0]
    )

    recent_files = [
        path
        for _, path in valid_paths[-6:]
    ]

    result = []

    for path in recent_files:

        try:
            content = path.read_text(
                encoding="utf-8"
            )
        except Exception:
            content = ""

        result.append(
            f"# --- File: {path.name} ---\n"
            f"{content}\n"
        )

    return "\n".join(result)


# ============================================================
# PLANNER
# ============================================================

def create_blueprint() -> str:

    catalog = load_catalog()

    summary = "\n".join(
        safe_text(item.get("name"))
        for item in catalog[-10:]
    )

    prompt = (
        "Existing Skill Catalog:\n"
        f"{summary or 'EMPTY'}\n\n"
        "What complex reusable Python skill "
        "should be built next?"
    )

    result = call_ai(
        PLANNER_PROMPT,
        prompt,
    )

    result = safe_text(result)

    if not result:

        return (
            "Create a robust text parsing "
            "utility using standard library."
        )

    return result


# ============================================================
# SANDBOX TEST
# ============================================================

def test_in_sandbox(
    code: str,
    skill_name: str,
) -> Tuple[bool, str]:

    sandbox_path = (
        DIRS["sandbox"]
        / f"{skill_name}.py"
    )

    sandbox_path.write_text(
        code,
        encoding="utf-8",
    )

    # Validate syntax before execution
    try:

        ast.parse(code)

    except SyntaxError as exc:

        return False, (
            f"SyntaxError: {exc}"
        )

    # IMPORTANT:
    # Test the actual NEW sandbox file,
    # not an existing active module.

    test_script = f"""
import importlib.util
import json
import sys

module_path = {str(sandbox_path)!r}

spec = importlib.util.spec_from_file_location(
    "{skill_name}",
    module_path
)

if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load generated skill.")

module = importlib.util.module_from_spec(spec)

spec.loader.exec_module(module)

if not hasattr(module, "run"):
    raise RuntimeError("Skill has no run() function.")

if not hasattr(module, "SAMPLE_ARGS"):
    raise RuntimeError("Skill has no SAMPLE_ARGS.")

result = module.run(module.SAMPLE_ARGS)

if not isinstance(result, dict):
    raise RuntimeError(
        "run() must return a dict, got "
        + type(result).__name__
    )

json.dumps(result)

print("SKILL_TEST_PASSED")
print(json.dumps(result, ensure_ascii=False))
"""

    try:

        result = subprocess.run(
            [
                sys.executable,
                "-c",
                test_script,
            ],
            capture_output=True,
            text=True,
            timeout=MAX_SKILL_SECONDS,
            cwd=DIRS["sandbox"],
        )

        if result.returncode == 0:

            return True, safe_text(
                result.stdout,
                "Passed",
            )

        error = safe_text(
            result.stderr
        )

        return False, (
            error or "Sandbox process failed."
        )

    except subprocess.TimeoutExpired:

        return False, "Sandbox timeout."

    except Exception as exc:

        return False, (
            f"Sandbox exception: {exc}"
        )


# ============================================================
# ACTIVATE SKILL
# ============================================================

def activate_skill(
    skill_name: str,
) -> Tuple[bool, str]:

    sandbox_path = (
        DIRS["sandbox"]
        / f"{skill_name}.py"
    )

    active_path = (
        DIRS["active"]
        / f"{skill_name}.py"
    )

    if not sandbox_path.exists():

        return False, (
            "Sandbox skill file does not exist."
        )

    # Backup existing active version
    if active_path.exists():

        try:
            backup_file(
                active_path,
                "before_activation",
            )
        except Exception as exc:

            return False, (
                f"Backup failed: {exc}"
            )

    try:

        shutil.move(
            str(sandbox_path),
            str(active_path),
        )

        return True, (
            f"Activated {skill_name}"
        )

    except Exception as exc:

        return False, (
            f"Activation failed: {exc}"
        )


# ============================================================
# LOAD ACTIVE SKILL
# ============================================================

def load_active_skill(
    skill_name: str,
):
    skill_path = (
        DIRS["active"]
        / f"{skill_name}.py"
    )

    if not skill_path.exists():

        raise FileNotFoundError(
            f"Active skill not found: {skill_name}"
        )

    spec = importlib.util.spec_from_file_location(
        skill_name,
        skill_path,
    )

    if spec is None or spec.loader is None:

        raise ImportError(
            f"Unable to load skill: {skill_name}"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(module)

    return module


# ============================================================
# USE ACTIVE SKILL
# ============================================================

def use_skill(
    skill_name: str,
    args: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:

    module = load_active_skill(
        skill_name
    )

    if not hasattr(module, "run"):

        raise RuntimeError(
            f"{skill_name} has no run()"
        )

    if args is None:

        args = getattr(
            module,
            "SAMPLE_ARGS",
            {},
        )

    result = module.run(args)

    if not isinstance(result, dict):

        raise RuntimeError(
            f"{skill_name}.run() must return dict."
        )

    return result


# ============================================================
# BUILD ONE SKILL
# ============================================================

def build_skill(
    skill_name: str,
    spec: str,
) -> Tuple[bool, str]:

    existing_skills_code = (
        get_recent_skills()
    )

    prompt = f"""
TASK:
{safe_text(spec)}

EXISTING ACTIVE SKILLS:
{existing_skills_code}
""".strip()

    code = clean_code(
        call_ai(
            BUILDER_PROMPT,
            prompt,
        )
    )

    feedback = ""

    for attempt in range(1, MAX_RETRIES + 1):

        if not code:

            feedback = (
                "AI returned empty code."
            )

        else:

            issues = static_check(code)

            if issues:

                feedback = (
                    "Static check failed: "
                    + "; ".join(issues)
                )

            else:

                # Reviewer
                verdict = safe_text(
                    call_ai(
                        REVIEWER_PROMPT,
                        code,
                    )
                ).upper()

                if (
                    "APPROVED" in verdict
                    or verdict == "SAFE"
                ):

                    ok, error = (
                        test_in_sandbox(
                            code,
                            skill_name,
                        )
                    )

                    if ok:

                        # IMPORTANT:
                        # Only activate AFTER test passes.
                        activated, activation_msg = (
                            activate_skill(
                                skill_name
                            )
                        )

                        if not activated:

                            return (
                                False,
                                activation_msg,
                            )

                        # Verify activated module again.
                        try:

                            result = use_skill(
                                skill_name
                            )

                            append_log(
                                {
                                    "event": "skill_activated",
                                    "skill": skill_name,
                                    "result": result,
                                    "time": time.time(),
                                }
                            )

                        except Exception as exc:

                            return (
                                False,
                                "Activation verification "
                                f"failed: {exc}",
                            )

                        return (
                            True,
                            "Built, tested, activated "
                            "and verified successfully.",
                        )

                    feedback = (
                        "Sandbox test failed: "
                        + safe_text(error)
                    )

                else:

                    feedback = (
                        "Reviewer rejected: "
                        + safe_text(verdict)
                    )

        print(
            f"🔄 Retry {attempt}/{MAX_RETRIES}: "
            f"{feedback[:120]}..."
        )

        if attempt >= MAX_RETRIES:
            break

        repair_prompt = f"""
Fix the following Python skill.

PROBLEM:
{feedback}

CURRENT CODE:
{code}

Return ONLY the corrected Python source.
""".strip()

        code = clean_code(
            call_ai(
                BUILDER_PROMPT,
                repair_prompt,
            )
        )

    # Failed skill goes to cemetery.
    cemetery_path = (
        DIRS["cemetery"]
        / f"failed_{skill_name}.py"
    )

    cemetery_path.write_text(
        code or "",
        encoding="utf-8",
    )

    append_log(
        {
            "event": "skill_failed",
            "skill": skill_name,
            "reason": feedback,
            "time": time.time(),
        }
    )

    return False, feedback


# ============================================================
# SKILL NUMBER
# ============================================================

def next_skill_number() -> int:

    numbers = []

    for path in DIRS["active"].glob(
        "skill_module_*.py"
    ):

        match = re.search(
            r"skill_module_(\d+)\.py$",
            path.name,
        )

        if match:

            numbers.append(
                int(match.group(1))
            )

    return (
        max(numbers) + 1
        if numbers
        else 1
    )


# ============================================================
# AUTONOMOUS LOOP
# ============================================================

def autonomous_loop():

    print(
        "🚀 AI FACTORY STARTED"
    )

    print(
        f"📁 Base: {BASE_DIR}"
    )

    print(
        f"🤖 Groq: "
        f"{'READY' if groq_client else 'OFF'}"
    )

    print(
        f"🌐 OpenRouter: "
        f"{'READY' if OPENROUTER_API_KEY else 'OFF'}"
    )

    n = next_skill_number()

    while True:

        skill_name = (
            f"skill_module_{n}"
        )

        print(
            f"\n{'=' * 70}"
        )

        print(
            f"🧠 Blueprinting: {skill_name}"
        )

        print(
            f"{'=' * 70}"
        )

        try:

            # ----------------------------
            # 1. PLAN
            # ----------------------------

            spec = create_blueprint()

            print(
                f"🧭 Planner Spec: {spec}"
            )

            # ----------------------------
            # 2. BUILD
            # ----------------------------

            success, message = (
                build_skill(
                    skill_name,
                    spec,
                )
            )

            # ----------------------------
            # 3. ACTIVATE
            # ----------------------------

            if success:

                add_to_catalog(
                    skill_name,
                    spec,
                )

                print(
                    f"✅ {skill_name} "
                    f"successfully built."
                )

                print(
                    "🦾 Skill tested + activated "
                    "and ready for future use."
                )

                print(
                    f"📦 Location: "
                    f"{DIRS['active'] / (skill_name + '.py')}"
                )

            else:

                print(
                    f"💀 {skill_name} failed."
                )

                print(
                    f"Reason: {message}"
                )

        except KeyboardInterrupt:

            print(
                "\n🛑 AI Factory stopped by user."
            )

            break

        except Exception as exc:

            print(
                f"⏳ Loop Error: {exc}"
            )

            print(
                "😴 Sleeping 10 seconds..."
            )

            time.sleep(10)

        n += 1

        time.sleep(15)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    autonomous_loop()
