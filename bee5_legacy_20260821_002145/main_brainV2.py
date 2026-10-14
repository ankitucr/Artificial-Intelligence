#!/usr/bin/env python3

"""
BEE5 AUTONOMOUS BRAIN
Skill Evolution Engine v2

Pipeline:

    GENERATE
       ↓
    PARSE
       ↓
    SECURITY VALIDATION
       ↓
    NOVELTY / DUPLICATE DETECTION
       ↓
    CANDIDATE
       ↓
    FUNCTIONAL EVALUATION
       ↓
    EDGE / REGRESSION EVALUATION
       ↓
    QUALITY SCORE
       ↓
    ┌──────────────┬──────────────┬───────────────┐
    ↓              ↓              ↓
  ACTIVE       CANDIDATE      CEMETERY
  >=90           70-89          <70
"""

from __future__ import annotations

import ast
import hashlib
import json
import math
import os
import re
import sqlite3
import subprocess
import sys
import time
import traceback
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

try:
    from groq import Groq
except ImportError:
    Groq = None


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY", ""
).strip()

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-120b"
)

OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "meta-llama/llama-3.3-70b-instruct"
)

BASE_DIR = Path(__file__).resolve().parent

SANDBOX_DIR = BASE_DIR / "sandbox"
CANDIDATE_DIR = BASE_DIR / "candidate_skills"
ACTIVE_DIR = BASE_DIR / "active_skills"
CEMETERY_DIR = BASE_DIR / "neural_cemetery"
BACKUP_DIR = BASE_DIR / "backups"
REPORT_DIR = BASE_DIR / "evaluation_reports"
MANIFEST_DIR = BASE_DIR / "skill_manifests"

DB_PATH = BASE_DIR / "shared_memory.db"
LOG_PATH = BASE_DIR / "skills_log.jsonl"

for directory in (
    SANDBOX_DIR,
    CANDIDATE_DIR,
    ACTIVE_DIR,
    CEMETERY_DIR,
    BACKUP_DIR,
    REPORT_DIR,
    MANIFEST_DIR,
):
    directory.mkdir(
        parents=True,
        exist_ok=True
    )

MAX_RETRIES = int(
    os.getenv("MAX_RETRIES", "3")
)

MAX_SKILL_SECONDS = int(
    os.getenv("MAX_SKILL_SECONDS", "15")
)

CYCLE_SLEEP_SECONDS = int(
    os.getenv("CYCLE_SLEEP_SECONDS", "60")
)

CONTEXT_SKILLS = int(
    os.getenv("CONTEXT_SKILLS", "6")
)

NOVELTY_REJECT_THRESHOLD = float(
    os.getenv("NOVELTY_REJECT_THRESHOLD", "0.82")
)

NOVELTY_CANDIDATE_THRESHOLD = float(
    os.getenv("NOVELTY_CANDIDATE_THRESHOLD", "0.65")
)

PROMOTION_SCORE = 90
CANDIDATE_SCORE = 70


# ============================================================
# LLM
# ============================================================

groq_client = None

if GROQ_API_KEY and Groq is not None:
    try:
        groq_client = Groq(
            api_key=GROQ_API_KEY
        )
    except Exception as exc:
        print(
            f"⚠️ Groq initialization failed: {exc}"
        )


# ============================================================
# ROOT SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = r"""
You are the intelligence engine of a controlled autonomous AI.

Your job is to improve the system by creating genuinely new,
useful, testable capabilities.

You are NOT rewarded for producing more files.

You are rewarded for producing better and more diverse capabilities.

CORE LOOP:

OBSERVE
ANALYZE
PROPOSE
BUILD
TEST
COMPARE
LEARN
IMPROVE

IMPORTANT:

A successful Python process is NOT proof that a skill is useful.

A skill must provide a distinct capability.

Do not create trivial variations of existing skills.

Do not repeatedly recreate:

- the same statistics calculator
- the same word counter
- the same date parser
- the same string utility
- renamed copies of previous functions

Before proposing a capability, inspect existing skills and find a
genuine gap.

A new capability can be:

- a new algorithm
- a new reasoning utility
- a new representation
- a new parser
- a new validator
- a new planner
- a new classifier
- a new mathematical procedure
- a new information-processing primitive

The capability should be independently useful.

Every capability must be:

- standard-library-only
- offline
- deterministic when practical
- self-contained
- testable
- reversible
- non-destructive

Never modify the trusted brain.

Never bypass the host permission system.

Never grant yourself authority.

Never create persistence mechanisms.

Never create malware or destructive code.

The system should evolve in capability diversity, quality and
reliability, not merely in file count.
"""


# ============================================================
# ALLOWED / BLOCKED MODULES
# ============================================================

ALLOWED_MODULES = {
    "abc",
    "collections",
    "collections.abc",
    "dataclasses",
    "datetime",
    "decimal",
    "enum",
    "functools",
    "heapq",
    "itertools",
    "json",
    "math",
    "operator",
    "random",
    "re",
    "statistics",
    "string",
    "textwrap",
    "typing",
}

BLOCKED_MODULES = {
    "os",
    "sys",
    "subprocess",
    "socket",
    "requests",
    "urllib",
    "http",
    "shutil",
    "pathlib",
    "sqlite3",
    "ctypes",
    "multiprocessing",
    "threading",
    "asyncio",
    "signal",
    "resource",
    "importlib",
    "pkgutil",
    "site",
}

BLOCKED_CALLS = {
    "eval",
    "exec",
    "compile",
    "__import__",
    "input",
    "breakpoint",
    "open",
}

BLOCKED_ATTRIBUTES = {
    "__globals__",
    "__builtins__",
    "__code__",
    "__loader__",
    "__spec__",
    "__subclasses__",
    "__mro__",
}


# ============================================================
# DATABASE
# ============================================================

def db():
    return sqlite3.connect(
        DB_PATH,
        timeout=10
    )


def init_db():
    with db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_name TEXT,
                status TEXT,
                score REAL,
                novelty REAL,
                attempt INTEGER,
                feedback TEXT,
                created_at TEXT
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                content TEXT,
                created_at TEXT
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )

        conn.commit()


def set_state(
    key: str,
    value: str
):
    with db() as conn:
        conn.execute(
            """
            INSERT INTO state(key, value)
            VALUES (?, ?)
            ON CONFLICT(key)
            DO UPDATE SET value=excluded.value
            """,
            (key, value)
        )
        conn.commit()


def get_state(
    key: str,
    default: str = ""
):
    with db() as conn:
        row = conn.execute(
            """
            SELECT value
            FROM state
            WHERE key=?
            """,
            (key,)
        ).fetchone()

    return row[0] if row else default


def remember(
    category: str,
    content: str
):
    if not content:
        return

    content = content[:8000]

    with db() as conn:
        conn.execute(
            """
            INSERT INTO memories(
                category,
                content,
                created_at
            )
            VALUES (?, ?, ?)
            """,
            (
                category,
                content,
                time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            )
        )
        conn.commit()


def record_experiment(
    skill_name: str,
    status: str,
    score: float,
    novelty: float,
    attempt: int,
    feedback: str
):
    with db() as conn:
        conn.execute(
            """
            INSERT INTO experiments(
                skill_name,
                status,
                score,
                novelty,
                attempt,
                feedback,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                skill_name,
                status,
                score,
                novelty,
                attempt,
                feedback[:8000],
                time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            )
        )
        conn.commit()


# ============================================================
# UTILITIES
# ============================================================

def clean_code(text: str) -> str:
    if not text:
        return ""

    text = text.strip()

    text = re.sub(
        r"^\s*```(?:python|py)?\s*\n?",
        "",
        text,
        count=1,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\n?\s*```\s*$",
        "",
        text,
        count=1,
    )

    return text.strip()


def safe_json_loads(text: str) -> Optional[dict]:
    if not text:
        return None

    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(
        r"\{.*\}",
        text,
        flags=re.DOTALL
    )

    if not match:
        return None

    try:
        return json.loads(
            match.group(0)
        )
    except json.JSONDecodeError:
        return None


def hash_text(text: str) -> str:
    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def tokenize(text: str) -> set:
    return {
        token
        for token in re.findall(
            r"[a-zA-Z_][a-zA-Z0-9_]*",
            text.lower()
        )
        if len(token) > 2
    }


# ============================================================
# AST ANALYSIS
# ============================================================

def validate_ast(
    code: str
) -> Tuple[bool, str]:

    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return (
            False,
            (
                "SyntaxError: "
                f"line={exc.lineno}, "
                f"message={exc.msg}"
            )
        )

    for node in ast.walk(tree):

        if isinstance(
            node,
            ast.Import
        ):
            for alias in node.names:

                root = alias.name.split(
                    "."
                )[0]

                if (
                    root in BLOCKED_MODULES
                    or alias.name not in ALLOWED_MODULES
                ):
                    return (
                        False,
                        (
                            "Blocked import: "
                            f"{alias.name}"
                        )
                    )

        elif isinstance(
            node,
            ast.ImportFrom
        ):
            module = node.module or ""
            root = module.split(
                "."
            )[0]

            if (
                root in BLOCKED_MODULES
                or module not in ALLOWED_MODULES
            ):
                return (
                    False,
                    (
                        "Blocked import-from: "
                        f"{module}"
                    )
                )

        elif isinstance(
            node,
            ast.Call
        ):
            if isinstance(
                node.func,
                ast.Name
            ):
                if node.func.id in BLOCKED_CALLS:
                    return (
                        False,
                        (
                            "Blocked call: "
                            f"{node.func.id}"
                        )
                    )

            if isinstance(
                node.func,
                ast.Attribute
            ):
                if node.func.attr in BLOCKED_CALLS:
                    return (
                        False,
                        (
                            "Blocked attribute call: "
                            f"{node.func.attr}"
                        )
                    )

        elif isinstance(
            node,
            ast.Attribute
        ):
            if node.attr in BLOCKED_ATTRIBUTES:
                return (
                    False,
                    (
                        "Blocked attribute: "
                        f"{node.attr}"
                    )
                )

    return (
        True,
        "AST validation passed"
    )


# ============================================================
# SKILL SIGNATURE
# ============================================================

def build_skill_signature(
    code: str,
    metadata: dict
) -> dict:

    try:
        tree = ast.parse(code)
    except SyntaxError:
        tree = ast.Module(body=[])

    functions = []
    imports = []
    calls = []
    operators = []

    for node in ast.walk(tree):

        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            )
        ):
            functions.append(
                node.name
            )

            arguments = [
                arg.arg
                for arg in node.args.args
            ]

        if isinstance(
            node,
            (
                ast.Import,
                ast.ImportFrom,
            )
        ):

            if isinstance(node, ast.Import):
                imports.extend(
                    alias.name
                    for alias in node.names
                )
            else:
                imports.append(
                    node.module or ""
                )

        if isinstance(
            node,
            ast.Call
        ):
            if isinstance(
                node.func,
                ast.Name
            ):
                calls.append(
                    node.func.id
                )
            elif isinstance(
                node.func,
                ast.Attribute
            ):
                calls.append(
                    node.func.attr
                )

        if isinstance(
            node,
            (
                ast.BinOp,
                ast.Compare,
                ast.BoolOp,
            )
        ):
            operators.append(
                type(node.op).__name__
                if isinstance(
                    node,
                    ast.BinOp
                )
                else type(node).__name__
            )

    description = str(
        metadata.get(
            "capability",
            ""
        )
    )

    purpose = str(
        metadata.get(
            "purpose",
            ""
        )
    )

    combined = " ".join([
        code,
        description,
        purpose,
        " ".join(functions),
        " ".join(calls),
    ])

    return {
        "hash": hash_text(
            re.sub(
                r"\s+",
                " ",
                code
            ).strip()
        ),
        "tokens": sorted(
            tokenize(combined)
        ),
        "functions": sorted(
            set(functions)
        ),
        "imports": sorted(
            set(imports)
        ),
        "calls": sorted(
            set(calls)
        ),
        "operators": sorted(
            set(operators)
        ),
        "capability": description,
        "purpose": purpose,
    }


# ============================================================
# SIMILARITY ENGINE
# ============================================================

def jaccard(
    a: set,
    b: set
) -> float:

    if not a and not b:
        return 1.0

    union = a | b

    if not union:
        return 0.0

    return len(a & b) / len(union)


def similarity(
    current: dict,
    previous: dict
) -> float:

    token_similarity = jaccard(
        set(current["tokens"]),
        set(previous["tokens"])
    )

    function_similarity = jaccard(
        set(current["functions"]),
        set(previous["functions"])
    )

    import_similarity = jaccard(
        set(current["imports"]),
        set(previous["imports"])
    )

    call_similarity = jaccard(
        set(current["calls"]),
        set(previous["calls"])
    )

    capability_similarity = jaccard(
        tokenize(
            current.get(
                "capability",
                ""
            )
        ),
        tokenize(
            previous.get(
                "capability",
                ""
            )
        ),
    )

    score = (
        token_similarity * 0.25
        + function_similarity * 0.20
        + import_similarity * 0.10
        + call_similarity * 0.10
        + capability_similarity * 0.35
    )

    return round(
        min(score, 1.0),
        4
    )


# ============================================================
# LOAD MANIFEST
# ============================================================

def load_manifest(
    skill_path: Path
) -> Optional[dict]:

    manifest_path = (
        MANIFEST_DIR
        / f"{skill_path.stem}.json"
    )

    if not manifest_path.exists():
        return None

    try:
        return json.loads(
            manifest_path.read_text(
                encoding="utf-8"
            )
        )
    except Exception:
        return None


def list_existing_signatures() -> List[dict]:

    signatures = []

    for path in sorted(
        ACTIVE_DIR.glob(
            "skill_module_*.py"
        )
    ):

        manifest = load_manifest(
            path
        )

        if manifest:
            signatures.append(
                manifest
            )
            continue

        try:
            source = path.read_text(
                encoding="utf-8"
            )

            signature = build_skill_signature(
                source,
                {}
            )

            signature["skill"] = (
                path.stem
            )

            signatures.append(
                signature
            )

        except Exception:
            continue

    return signatures


# ============================================================
# NOVELTY
# ============================================================

def calculate_novelty(
    signature: dict
) -> Tuple[float, Optional[str], float]:

    existing = (
        list_existing_signatures()
    )

    if not existing:
        return (
            1.0,
            None,
            0.0
        )

    highest = 0.0
    closest = None

    for previous in existing:

        score = similarity(
            signature,
            previous
        )

        if score > highest:

            highest = score

            closest = previous.get(
                "skill"
            )

    novelty = 1.0 - highest

    return (
        round(novelty, 4),
        closest,
        round(highest, 4)
    )


# ============================================================
# LLM GENERATION CONTRACT
# ============================================================

GENERATION_PROMPT = """
Generate exactly ONE genuinely new Python micro-skill.

IMPORTANT:

Do not create another version of an existing capability.

The current goal is capability diversity.

Return ONLY valid JSON.

Schema:

{
  "name": "short capability name",
  "capability": "one sentence describing the distinct capability",
  "purpose": "why this capability is useful",
  "primary_function": "function_name",
  "code": "complete Python source",
  "tests": [
    {
      "function": "function_name",
      "args": [],
      "kwargs": {},
      "expected": null
    }
  ]
}

Rules for code:

- standard library only
- offline only
- no filesystem
- no network
- no subprocess
- no environment variables
- no input()
- no eval()
- no exec()
- no dynamic imports
- no global state
- self-contained
- define at least one function
- function must be deterministic where practical

Tests:

- 3 to 6 tests
- include normal case
- include edge case
- include invalid/minimal case when applicable
- expected values must be JSON-compatible
- tests must target primary_function

Do NOT output markdown.

Do NOT output text outside JSON.
"""


# ============================================================
# LLM REQUEST
# ============================================================

def ask_groq(
    prompt: str
) -> Optional[str]:

    if groq_client is None:
        return None

    print(
        "🧠 Thinking via Groq..."
    )

    try:
        response = (
            groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.25,
                max_tokens=7000,
                timeout=35,
            )
        )

        return response.choices[0].message.content

    except Exception as exc:

        print(
            f"⚠️ Groq failed: {exc}"
        )

        remember(
            "llm_failure",
            f"Groq: {type(exc).__name__}: {exc}"
        )

        return None


def ask_openrouter(
    prompt: str
) -> Optional[str]:

    if not OPENROUTER_API_KEY:
        return None

    print(
        "🔄 Thinking via OpenRouter..."
    )

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.25,
        "max_tokens": 7000,
    }

    try:

        request = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps(
                payload
            ).encode("utf-8"),
            headers={
                "Authorization":
                    f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type":
                    "application/json",
                "HTTP-Referer":
                    "http://localhost",
                "X-Title":
                    "BEE5 Skill Evolution Engine",
            },
            method="POST",
        )

        with urllib.request.urlopen(
            request,
            timeout=45
        ) as response:

            body = response.read()

        data = json.loads(
            body.decode("utf-8")
        )

        return data["choices"][0][
            "message"
        ]["content"]

    except Exception as exc:

        print(
            f"❌ OpenRouter failed: {exc}"
        )

        remember(
            "llm_failure",
            (
                "OpenRouter: "
                f"{type(exc).__name__}: {exc}"
            )
        )

        return None


def generate_skill() -> Optional[dict]:

    raw = ask_groq(
        GENERATION_PROMPT
    )

    if not raw:

        raw = ask_openrouter(
            GENERATION_PROMPT
        )

    if not raw:
        return None

    data = safe_json_loads(
        raw
    )

    if not data:
        return None

    required = {
        "name",
        "capability",
        "purpose",
        "primary_function",
        "code",
        "tests",
    }

    if not required.issubset(
        data.keys()
    ):
        return None

    if not isinstance(
        data["code"],
        str
    ):
        return None

    if not isinstance(
        data["tests"],
        list
    ):
        return None

    data["code"] = clean_code(
        data["code"]
    )

    return data


# ============================================================
# CANDIDATE STORAGE
# ============================================================

def get_next_skill_number() -> int:

    numbers = []

    pattern = re.compile(
        r"skill_module_(\d+)"
    )

    for root in (
        ACTIVE_DIR,
        CANDIDATE_DIR,
        CEMETERY_DIR,
        SANDBOX_DIR,
    ):

        for path in root.glob(
            "skill_module_*"
        ):

            match = pattern.search(
                path.name
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


def save_manifest(
    skill_name: str,
    signature: dict,
    metadata: dict,
    evaluation: dict
):

    payload = {
        "skill": skill_name,
        "signature": signature,
        "metadata": metadata,
        "evaluation": evaluation,
        "created_at": time.strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
    }

    path = (
        MANIFEST_DIR
        / f"{skill_name}.json"
    )

    path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )


def save_report(
    skill_name: str,
    report: dict
):

    path = (
        REPORT_DIR
        / f"{skill_name}.json"
    )

    path.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )


# ============================================================
# FUNCTIONAL TEST RUNNER
# ============================================================

def validate_tests(
    skill: dict
) -> Tuple[bool, str]:

    tests = skill.get(
        "tests",
        []
    )

    primary_function = skill.get(
        "primary_function"
    )

    if not primary_function:
        return (
            False,
            "Missing primary_function"
        )

    if not tests:
        return (
            False,
            "No tests generated"
        )

    for index, test in enumerate(
        tests,
        start=1
    ):

        if not isinstance(
            test,
            dict
        ):
            return (
                False,
                f"Test {index} is not an object"
            )

        if test.get("function") != (
            primary_function
        ):
            return (
                False,
                (
                    f"Test {index} targets "
                    "wrong function"
                )
            )

        if not isinstance(
            test.get("args", []),
            list
        ):
            return (
                False,
                f"Test {index} args invalid"
            )

        if not isinstance(
            test.get("kwargs", {}),
            dict
        ):
            return (
                False,
                f"Test {index} kwargs invalid"
            )

        try:
            json.dumps(
                test.get("expected")
            )
        except TypeError:
            return (
                False,
                (
                    f"Test {index} expected "
                    "value is not JSON-compatible"
                )
            )

    return (
        True,
        "Tests valid"
    )


def build_test_runner(
    module_path: Path,
    tests: List[dict],
    primary_function: str
) -> str:

    module_literal = (
        repr(str(module_path))
    )

    tests_literal = json.dumps(
        tests,
        ensure_ascii=False
    )

    return f'''
import importlib.util
import json
import traceback

MODULE_PATH = {module_literal}
TESTS = json.loads(
    {tests_literal!r}
)

FUNCTION_NAME = {primary_function!r}

spec = importlib.util.spec_from_file_location(
    "candidate_module",
    MODULE_PATH
)

if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load candidate module")

module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

if not hasattr(module, FUNCTION_NAME):
    raise RuntimeError(
        f"Missing function: {{FUNCTION_NAME}}"
    )

function = getattr(module, FUNCTION_NAME)

passed = 0
failed = []

for index, test in enumerate(
    TESTS,
    start=1
):
    try:
        args = test.get("args", [])
        kwargs = test.get("kwargs", {{}})
        expected = test.get("expected")

        actual = function(
            *args,
            **kwargs
        )

        actual_normalized = actual

        if hasattr(actual, "isoformat"):
            actual_normalized = actual.isoformat()

        if isinstance(actual, set):
            actual_normalized = sorted(actual)

        if actual_normalized != expected:
            failed.append({{
                "test": index,
                "expected": expected,
                "actual": actual_normalized
            }})
        else:
            passed += 1

    except Exception as exc:
        failed.append({{
            "test": index,
            "error": f"{{type(exc).__name__}}: {{exc}}"
        }})

print(
    json.dumps(
        {{
            "passed": passed,
            "total": len(TESTS),
            "failed": failed
        }},
        ensure_ascii=False
    )
)

if failed:
    raise SystemExit(2)
'''


def run_functional_tests(
    code: str,
    tests: List[dict],
    primary_function: str,
    skill_name: str
) -> Tuple[bool, dict]:

    candidate_path = (
        CANDIDATE_DIR
        / f"{skill_name}.py"
    )

    candidate_path.write_text(
        code,
        encoding="utf-8"
    )

    runner = build_test_runner(
        candidate_path,
        tests,
        primary_function
    )

    runner_path = (
        SANDBOX_DIR
        / f"{skill_name}_runner.py"
    )

    runner_path.write_text(
        runner,
        encoding="utf-8"
    )

    try:

        result = subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                str(runner_path),
            ],
            cwd=str(
                SANDBOX_DIR
            ),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=MAX_SKILL_SECONDS,
        )

    except subprocess.TimeoutExpired:

        return (
            False,
            {
                "passed": 0,
                "total": len(tests),
                "failed": [
                    {
                        "error":
                            "Functional tests timed out"
                    }
                ],
            }
        )

    stdout = (
        result.stdout or ""
    ).strip()

    stderr = (
        result.stderr or ""
    ).strip()

    parsed = None

    for line in reversed(
        stdout.splitlines()
    ):
        try:
            parsed = json.loads(
                line
            )
            break
        except Exception:
            continue

    if parsed is None:

        return (
            False,
            {
                "passed": 0,
                "total": len(tests),
                "failed": [
                    {
                        "error":
                            stderr
                            or
                            "No evaluation output"
                    }
                ],
            }
        )

    success = (
        result.returncode == 0
        and
        parsed.get("passed", 0)
        == parsed.get("total", 0)
    )

    return (
        success,
        parsed
    )


# ============================================================
# SCORE
# ============================================================

def calculate_score(
    syntax_ok: bool,
    contract_ok: bool,
    tests_ok: bool,
    test_report: dict,
    novelty: float
) -> float:

    syntax_score = (
        10
        if syntax_ok
        else 0
    )

    contract_score = (
        10
        if contract_ok
        else 0
    )

    total = int(
        test_report.get(
            "total",
            0
        )
    )

    passed = int(
        test_report.get(
            "passed",
            0
        )
    )

    if total > 0:
        functional_score = (
            passed / total
        ) * 45
    else:
        functional_score = 0

    novelty_score = (
        novelty * 25
    )

    reliability_score = (
        10
        if tests_ok
        else 0
    )

    score = (
        syntax_score
        + contract_score
        + functional_score
        + novelty_score
        + reliability_score
    )

    return round(
        min(score, 100),
        2
    )


# ============================================================
# BACKUP
# ============================================================

def backup_active():

    stamp = time.strftime(
        "%Y%m%d_%H%M%S"
    )

    target = (
        BACKUP_DIR
        / stamp
    )

    target.mkdir(
        parents=True,
        exist_ok=True
    )

    count = 0

    for source in ACTIVE_DIR.glob(
        "skill_module_*.py"
    ):

        try:
            target_file = (
                target
                / source.name
            )

            target_file.write_text(
                source.read_text(
                    encoding="utf-8"
                ),
                encoding="utf-8"
            )

            count += 1

        except Exception:
            continue

    return target, count


# ============================================================
# PROMOTE / REJECT
# ============================================================

def promote_skill(
    skill_name: str,
    metadata: dict,
    code: str,
    evaluation: dict,
    signature: dict
):

    candidate_path = (
        CANDIDATE_DIR
        / f"{skill_name}.py"
    )

    active_path = (
        ACTIVE_DIR
        / f"{skill_name}.py"
    )

    active_path.write_text(
        code,
        encoding="utf-8"
    )

    if candidate_path.exists():
        candidate_path.unlink()

    save_manifest(
        skill_name,
        signature,
        metadata,
        evaluation
    )


def move_to_cemetery(
    skill_name: str,
    code: str,
    reason: str,
    metadata: dict,
    evaluation: dict
):

    folder = (
        CEMETERY_DIR
        / skill_name
    )

    folder.mkdir(
        parents=True,
        exist_ok=True
    )

    (folder / "code.py").write_text(
        code,
        encoding="utf-8"
    )

    (folder / "reason.txt").write_text(
        reason,
        encoding="utf-8"
    )

    (folder / "metadata.json").write_text(
        json.dumps(
            metadata,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    (folder / "evaluation.json").write_text(
        json.dumps(
            evaluation,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    candidate_path = (
        CANDIDATE_DIR
        / f"{skill_name}.py"
    )

    if candidate_path.exists():
        candidate_path.unlink()


# ============================================================
# ONE EVOLUTION CYCLE
# ============================================================

def run_cycle(
    skill_number: int
) -> bool:

    skill_name = (
        f"skill_module_{skill_number}"
    )

    print()
    print(
        "=" * 64
    )
    print(
        f"🧠 Evolution cycle: {skill_name}"
    )
    print(
        "=" * 64
    )

    backup_path, backup_count = (
        backup_active()
    )

    print(
        f"💾 Backup: {backup_path.name} "
        f"({backup_count} active skills)"
    )

    # --------------------------------------------------------
    # GENERATION
    # --------------------------------------------------------

    skill = generate_skill()

    if not skill:

        print(
            "❌ Skill generation failed."
        )

        remember(
            "generation_failure",
            skill_name
        )

        return False

    code = skill["code"]

    # --------------------------------------------------------
    # SECURITY
    # --------------------------------------------------------

    syntax_ok = True
    contract_ok = True

    try:
        ast.parse(code)
    except SyntaxError:
        syntax_ok = False

    if not syntax_ok:

        print(
            "❌ Syntax validation failed."
        )

        move_to_cemetery(
            skill_name,
            code,
            "Syntax validation failed.",
            skill,
            {}
        )

        return False

    ast_ok, ast_feedback = (
        validate_ast(code)
    )

    if not ast_ok:

        print(
            f"🚫 Security rejection: "
            f"{ast_feedback}"
        )

        move_to_cemetery(
            skill_name,
            code,
            ast_feedback,
            skill,
            {}
        )

        return False

    tests_ok, test_feedback = (
        validate_tests(skill)
    )

    if not tests_ok:

        print(
            f"❌ Test contract invalid: "
            f"{test_feedback}"
        )

        move_to_cemetery(
            skill_name,
            code,
            test_feedback,
            skill,
            {}
        )

        return False

    # --------------------------------------------------------
    # SIGNATURE / NOVELTY
    # --------------------------------------------------------

    signature = build_skill_signature(
        code,
        skill
    )

    signature["skill"] = (
        skill_name
    )

    novelty, closest, similarity_score = (
        calculate_novelty(
            signature
        )
    )

    print(
        f"🧬 Novelty score: "
        f"{novelty:.2f}"
    )

    if closest:

        print(
            f"🔎 Closest skill: "
            f"{closest}"
        )

        print(
            f"🔎 Similarity: "
            f"{similarity_score:.2f}"
        )

    # --------------------------------------------------------
    # DUPLICATE REJECTION
    # --------------------------------------------------------

    if (
        novelty
        <
        (1.0 - NOVELTY_REJECT_THRESHOLD)
    ):

        print(
            "♻️ Duplicate / near-duplicate "
            "capability detected."
        )

        evaluation = {
            "status": "duplicate",
            "novelty": novelty,
            "closest_skill": closest,
            "similarity": similarity_score,
            "score": 0,
        }

        move_to_cemetery(
            skill_name,
            code,
            (
                "Duplicate capability.\n"
                f"Closest: {closest}\n"
                f"Similarity: "
                f"{similarity_score}"
            ),
            skill,
            evaluation
        )

        record_experiment(
            skill_name,
            "duplicate",
            0,
            novelty,
            1,
            "Duplicate capability"
        )

        remember(
            "duplicate_rejected",
            (
                f"{skill_name} rejected because "
                f"it resembles {closest}"
            )
        )

        return False

    # --------------------------------------------------------
    # CANDIDATE
    # --------------------------------------------------------

    candidate_path = (
        CANDIDATE_DIR
        / f"{skill_name}.py"
    )

    candidate_path.write_text(
        code,
        encoding="utf-8"
    )

    print(
        "🧪 Candidate created."
    )

    # --------------------------------------------------------
    # FUNCTIONAL TESTS
    # --------------------------------------------------------

    print(
        "🧪 Running functional tests..."
    )

    tests_passed, test_report = (
        run_functional_tests(
            code,
            skill["tests"],
            skill["primary_function"],
            skill_name
        )
    )

    passed = test_report.get(
        "passed",
        0
    )

    total = test_report.get(
        "total",
        0
    )

    print(
        f"📊 Functional tests: "
        f"{passed}/{total}"
    )

    if test_report.get("failed"):

        print(
            "❌ Failed tests:"
        )

        for failure in test_report[
            "failed"
        ][:5]:

            print(
                f"   {failure}"
            )

    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    score = calculate_score(
        syntax_ok=True,
        contract_ok=True,
        tests_ok=tests_passed,
        test_report=test_report,
        novelty=novelty,
    )

    status = (
        "ACTIVE"
        if score >= PROMOTION_SCORE
        else
        "CANDIDATE"
        if score >= CANDIDATE_SCORE
        else
        "CEMETERY"
    )

    evaluation = {
        "score": score,
        "status": status,
        "novelty": novelty,
        "closest_skill": closest,
        "similarity": similarity_score,
        "functional_tests": test_report,
        "ast_validation": ast_feedback,
        "backup": str(
            backup_path
        ),
    }

    save_report(
        skill_name,
        evaluation
    )

    record_experiment(
        skill_name,
        status.lower(),
        score,
        novelty,
        1,
        json.dumps(
            test_report
        )
    )

    # --------------------------------------------------------
    # PROMOTION
    # --------------------------------------------------------

    if score >= PROMOTION_SCORE:

        promote_skill(
            skill_name,
            skill,
            code,
            evaluation,
            signature
        )

        remember(
            "successful_skill",
            (
                f"{skill_name}: "
                f"{skill['capability']} | "
                f"score={score}"
            )
        )

        set_state(
            "last_successful_skill",
            skill_name
        )

        print()
        print(
            "✅ SKILL PROMOTED TO ACTIVE"
        )

        print(
            f"🏆 Score: {score}/100"
        )

        return True

    # --------------------------------------------------------
    # CANDIDATE
    # --------------------------------------------------------

    if score >= CANDIDATE_SCORE:

        save_manifest(
            skill_name,
            signature,
            skill,
            evaluation
        )

        print()
        print(
            "🟡 SKILL KEPT AS CANDIDATE"
        )

        print(
            f"📊 Score: {score}/100"
        )

        remember(
            "candidate_skill",
            (
                f"{skill_name}: "
                f"score={score}"
            )
        )

        return False

    # --------------------------------------------------------
    # CEMETERY
    # --------------------------------------------------------

    reason = (
        f"Score below threshold.\n"
        f"Score: {score}\n"
        f"Tests: {passed}/{total}"
    )

    move_to_cemetery(
        skill_name,
        code,
        reason,
        skill,
        evaluation
    )

    remember(
        "failed_skill",
        (
            f"{skill_name}: "
            f"score={score}"
        )
    )

    print()
    print(
        "🪦 SKILL SENT TO NEURAL CEMETERY"
    )

    print(
        f"📊 Score: {score}/100"
    )

    return False


# ============================================================
# STATUS
# ============================================================

def status():

    active = len(
        list(
            ACTIVE_DIR.glob(
                "skill_module_*.py"
            )
        )
    )

    candidates = len(
        list(
            CANDIDATE_DIR.glob(
                "skill_module_*.py"
            )
        )
    )

    failed = len(
        list(
            CEMETERY_DIR.glob(
                "skill_module_*"
            )
        )
    )

    reports = len(
        list(
            REPORT_DIR.glob(
                "*.json"
            )
        )
    )

    print()
    print(
        "================ BEE5 STATUS ================"
    )

    print(
        f"Active skills      : {active}"
    )

    print(
        f"Candidate skills   : {candidates}"
    )

    print(
        f"Cemetery records   : {failed}"
    )

    print(
        f"Evaluation reports : {reports}"
    )

    print(
        f"Last success       : "
        f"{get_state('last_successful_skill', 'none')}"
    )

    print(
        "=============================================="
    )
    print()


# ============================================================
# MAIN LOOP
# ============================================================

def main():

    init_db()

    print()
    print(
        "╔══════════════════════════════════════════════╗"
    )
    print(
        "║      BEE5 SKILL EVOLUTION ENGINE v2         ║"
    )
    print(
        "║                                              ║"
    )
    print(
        "║  NOVELTY → TEST → SCORE → EVOLVE            ║"
    )
    print(
        "╚══════════════════════════════════════════════╝"
    )

    print()

    if not GROQ_API_KEY:
        print(
            "ℹ️ Groq API key not configured."
        )

    if not OPENROUTER_API_KEY:
        print(
            "ℹ️ OpenRouter API key not configured."
        )

    if not GROQ_API_KEY and not OPENROUTER_API_KEY:

        raise SystemExit(
            "No LLM API key configured."
        )

    status()

    next_number = (
        get_next_skill_number()
    )

    try:

        while True:

            run_cycle(
                next_number
            )

            next_number += 1

            print()
            print(
                f"💤 Sleeping "
                f"{CYCLE_SLEEP_SECONDS}s..."
            )

            for remaining in range(
                CYCLE_SLEEP_SECONDS,
                0,
                -1
            ):

                time.sleep(1)

                if (
                    remaining <= 3
                    or remaining % 10 == 0
                ):
                    print(
                        f"\r⏳ "
                        f"{remaining:02d}s ",
                        end="",
                        flush=True
                    )

            print(
                "\r" + " " * 20 + "\r",
                end="",
                flush=True
            )

    except KeyboardInterrupt:

        print()
        print()
        print(
            "🛑 Operator interrupt."
        )

        status()


if __name__ == "__main__":
    main()
