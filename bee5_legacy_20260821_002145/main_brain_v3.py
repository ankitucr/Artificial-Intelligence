#!/usr/bin/env python3

"""
BEE5 AUTONOMOUS BRAIN
=====================

SKILL EVOLUTION ENGINE v3

Pipeline:

    GENERATE
       |
       v
    PARSE JSON
       |
       v
    STATIC / AST SECURITY
       |
       v
    CAPABILITY SIGNATURE
       |
       v
    NOVELTY / DUPLICATE CHECK
       |
       +---- DUPLICATE ----> REGENERATE
       |
       v
    CANDIDATE
       |
       v
    FUNCTIONAL TESTS
       |
       v
    DETERMINISM TEST
       |
       v
    QUALITY SCORE
       |
       +---- LOW ----------> NEURAL CEMETERY
       |
       +---- MEDIUM -------> CANDIDATE
       |
       +---- HIGH ---------> ACTIVE
       |
       v
    MEMORY / REPORT / MANIFEST

Important:
This is controlled code execution, not a perfect security sandbox.
For truly untrusted code use Docker, a disposable VM, or another
strong isolation boundary.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

try:
    from groq import Groq
except ImportError:
    Groq = None


# ============================================================
# CONFIG
# ============================================================

load_dotenv()

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

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY",
    ""
).strip()

OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY",
    ""
).strip()

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-120b"
)

OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "meta-llama/llama-3.3-70b-instruct"
)

MAX_SKILL_SECONDS = int(
    os.getenv("MAX_SKILL_SECONDS", "15")
)

MAX_REPAIR_ATTEMPTS = int(
    os.getenv("MAX_REPAIR_ATTEMPTS", "2")
)

MAX_GENERATION_ATTEMPTS = int(
    os.getenv("MAX_GENERATION_ATTEMPTS", "4")
)

CYCLE_SLEEP_SECONDS = int(
    os.getenv("CYCLE_SLEEP_SECONDS", "60")
)

MAX_ACTIVE_CONTEXT = int(
    os.getenv("MAX_ACTIVE_CONTEXT", "12")
)

NOVELTY_MINIMUM = float(
    os.getenv("NOVELTY_MINIMUM", "0.28")
)

ACTIVE_SCORE = float(
    os.getenv("ACTIVE_SCORE", "88")
)

CANDIDATE_SCORE = float(
    os.getenv("CANDIDATE_SCORE", "70")
)

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


# ============================================================
# ROOT SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = r"""
You are the intelligence engine inside a controlled autonomous AI.

Your purpose is not to create as many files as possible.

Your purpose is to continuously build NEW, USEFUL, RELIABLE,
TESTABLE capabilities.

You must prefer:
- novelty over repetition
- correctness over complexity
- measurable usefulness over cosmetic changes
- repair over blind regeneration
- learning from failures over ignoring failures

A new skill is valuable only if it introduces a capability that
does not already exist in the active skill library.

Before creating a capability, inspect the supplied active skill
context and avoid recreating existing functionality.

Do not generate:
- malware
- destructive code
- credential theft
- persistence
- exploitation
- system takeover
- unrestricted network access
- filesystem modification
- subprocess execution
- self-replication

Generated skills must:
- use Python standard library only
- operate offline
- define at least one useful function
- be deterministic where practical
- be self-contained
- not depend on the BEE5 host
- not modify the host
- be testable through explicit test cases

The host system is the authority.

You may propose capabilities.
You may not grant yourself privileges.

A successful program exit is NOT proof that a skill is correct.

Correctness must be demonstrated through tests.
"""


# ============================================================
# MODEL
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
# SAFETY POLICY
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
    "re",
    "statistics",
    "string",
    "textwrap",
    "typing",
}

BLOCKED_ROOT_MODULES = {
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

BLOCKED_CALL_NAMES = {
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
# V3 DATABASE
# ============================================================

def db_connect():
    return sqlite3.connect(
        DB_PATH,
        timeout=10
    )


def init_database():
    """
    IMPORTANT:
    V3 uses its OWN tables.

    Existing old tables are never modified.
    Therefore old shared_memory.db cannot crash V3 because of
    missing v3 columns.
    """

    with db_connect() as conn:

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS evolution_v3_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_name TEXT NOT NULL,
                status TEXT NOT NULL,
                score REAL DEFAULT 0,
                novelty REAL DEFAULT 0,
                similarity REAL DEFAULT 0,
                attempt INTEGER DEFAULT 0,
                feedback TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS evolution_v3_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS evolution_v3_state (
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
    with db_connect() as conn:
        conn.execute(
            """
            INSERT INTO evolution_v3_state(
                key,
                value
            )
            VALUES (?, ?)
            ON CONFLICT(key)
            DO UPDATE SET
                value = excluded.value
            """,
            (
                key,
                value
            )
        )
        conn.commit()


def get_state(
    key: str,
    default: str = ""
) -> str:

    with db_connect() as conn:

        row = conn.execute(
            """
            SELECT value
            FROM evolution_v3_state
            WHERE key = ?
            """,
            (key,)
        ).fetchone()

    return (
        row[0]
        if row
        else default
    )


def remember(
    category: str,
    content: str
):
    content = (
        content or ""
    ).strip()

    if not content:
        return

    content = content[:10000]

    with db_connect() as conn:

        conn.execute(
            """
            INSERT INTO evolution_v3_memory(
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


def record_run(
    skill_name: str,
    status: str,
    score: float,
    novelty: float,
    similarity: float,
    attempt: int,
    feedback: str
):
    with db_connect() as conn:

        conn.execute(
            """
            INSERT INTO evolution_v3_runs(
                skill_name,
                status,
                score,
                novelty,
                similarity,
                attempt,
                feedback,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                skill_name,
                status,
                score,
                novelty,
                similarity,
                attempt,
                (
                    feedback or ""
                )[:10000],
                time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            )
        )

        conn.commit()


# ============================================================
# HELPERS
# ============================================================

def clean_code(
    text: str
) -> str:

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


def clean_json_response(text: str) -> Optional[dict]:
    """
    Robust JSON extractor.

    Handles:
    - normal JSON
    - fenced JSON
    - leading/trailing text
    - JSON objects containing Python code
    """

    if not text:
        return None

    text = text.strip()

    # Remove markdown fences without touching inner code.
    text = re.sub(
        r"^\s*```(?:json)?\s*",
        "",
        text,
        count=1,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\s*```\s*$",
        "",
        text,
        count=1,
    )

    # First: direct JSON parse.
    try:
        obj = json.loads(text)

        if isinstance(obj, dict):
            return obj

    except Exception:
        pass

    # --------------------------------------------------------
    # Balanced JSON-object extraction.
    # This is safer than r"\{.*\}" because generated Python
    # code can itself contain braces.
    # --------------------------------------------------------

    start = None
    depth = 0
    in_string = False
    escape = False

    for i, ch in enumerate(text):

        if start is None:

            if ch == "{":
                start = i
                depth = 1
                in_string = False
                escape = False

            continue

        if in_string:

            if escape:
                escape = False
                continue

            if ch == "\\":
                escape = True
                continue

            if ch == '"':
                in_string = False

            continue

        if ch == '"':
            in_string = True
            continue

        if ch == "{":
            depth += 1

        elif ch == "}":
            depth -= 1

            if depth == 0:

                candidate = text[start:i + 1]

                try:

                    obj = json.loads(
                        candidate
                    )

                    if isinstance(obj, dict):
                        return obj

                except Exception:
                    pass

                start = None

    return None


def sha256_text(
    text: str
) -> str:

    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def tokens(
    text: str
) -> set:

    return {
        value
        for value in re.findall(
            r"[A-Za-z_][A-Za-z0-9_]*",
            text.lower()
        )
        if len(value) >= 3
    }


def jaccard(
    a: set,
    b: set
) -> float:

    if not a and not b:
        return 1.0

    union = a | b

    if not union:
        return 0.0

    return (
        len(a & b)
        /
        len(union)
    )


def normalize_value(
    value: Any
) -> Any:

    if isinstance(value, dict):

        return {
            str(k): normalize_value(v)
            for k, v in value.items()
        }

    if isinstance(
        value,
        (list, tuple)
    ):

        return [
            normalize_value(v)
            for v in value
        ]

    if isinstance(
        value,
        set
    ):

        normalized = [
            normalize_value(v)
            for v in value
        ]

        try:
            return sorted(
                normalized,
                key=repr
            )
        except Exception:
            return normalized

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        )
    ) or value is None:

        return value

    if hasattr(
        value,
        "isoformat"
    ):

        try:
            return value.isoformat()
        except Exception:
            pass

    return repr(value)


# ============================================================
# SKILL NUMBER
# ============================================================

def get_next_skill_number() -> int:

    numbers = []

    pattern = re.compile(
        r"skill_module_(\d+)"
    )

    for directory in (
        ACTIVE_DIR,
        CANDIDATE_DIR,
        SANDBOX_DIR,
        CEMETERY_DIR,
    ):

        for path in directory.rglob(
            "*"
        ):

            match = pattern.search(
                path.name
            )

            if match:
                try:
                    numbers.append(
                        int(
                            match.group(1)
                        )
                    )
                except ValueError:
                    pass

    if not numbers:
        return 1

    return max(numbers) + 1


# ============================================================
# AST / SECURITY VALIDATION
# ============================================================

def validate_generated_code(
    code: str
) -> Tuple[bool, str]:

    try:
        tree = ast.parse(
            code
        )
    except SyntaxError as exc:

        return (
            False,
            (
                "SYNTAX_ERROR: "
                f"line={exc.lineno}, "
                f"column={exc.offset}, "
                f"message={exc.msg}"
            )
        )

    found_function = False

    for node in ast.walk(tree):

        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            )
        ):

            found_function = True

        if isinstance(
            node,
            ast.Import
        ):

            for alias in node.names:

                root = (
                    alias.name
                    .split(".")[0]
                )

                if (
                    root
                    in BLOCKED_ROOT_MODULES
                ):
                    return (
                        False,
                        (
                            "BLOCKED_IMPORT: "
                            f"{alias.name}"
                        )
                    )

                if (
                    alias.name
                    not in ALLOWED_MODULES
                ):
                    return (
                        False,
                        (
                            "UNAPPROVED_IMPORT: "
                            f"{alias.name}"
                        )
                    )

        if isinstance(
            node,
            ast.ImportFrom
        ):

            module = (
                node.module
                or ""
            )

            root = (
                module
                .split(".")[0]
            )

            if (
                root
                in BLOCKED_ROOT_MODULES
            ):
                return (
                    False,
                    (
                        "BLOCKED_IMPORT_FROM: "
                        f"{module}"
                    )
                )

            if (
                module
                not in ALLOWED_MODULES
            ):
                return (
                    False,
                    (
                        "UNAPPROVED_IMPORT_FROM: "
                        f"{module}"
                    )
                )

        if isinstance(
            node,
            ast.Call
        ):

            if isinstance(
                node.func,
                ast.Name
            ):

                if (
                    node.func.id
                    in BLOCKED_CALL_NAMES
                ):
                    return (
                        False,
                        (
                            "BLOCKED_CALL: "
                            f"{node.func.id}"
                        )
                    )

            if isinstance(
                node.func,
                ast.Attribute
            ):

                if (
                    node.func.attr
                    in BLOCKED_CALL_NAMES
                ):
                    return (
                        False,
                        (
                            "BLOCKED_ATTRIBUTE_CALL: "
                            f"{node.func.attr}"
                        )
                    )

        if isinstance(
            node,
            ast.Attribute
        ):

            if (
                node.attr
                in BLOCKED_ATTRIBUTES
            ):
                return (
                    False,
                    (
                        "BLOCKED_ATTRIBUTE: "
                        f"{node.attr}"
                    )
                )

    if not found_function:

        return (
            False,
            "NO_FUNCTION_DEFINED"
        )

    # --------------------------------------------------------
    # Top-level side-effect protection
    # --------------------------------------------------------

    for statement in tree.body:

        if isinstance(
            statement,
            (
                ast.Import,
                ast.ImportFrom,
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
                ast.Assign,
                ast.AnnAssign,
                ast.AugAssign,
                ast.Expr,
            )
        ):

            # A top-level string literal / docstring is fine.
            if isinstance(
                statement,
                ast.Expr
            ):
                if isinstance(
                    statement.value,
                    ast.Constant
                ) and isinstance(
                    statement.value.value,
                    str
                ):
                    continue

            # Reject function calls at module level.
            if isinstance(
                statement,
                ast.Expr
            ) and isinstance(
                statement.value,
                ast.Call
            ):
                return (
                    False,
                    "TOP_LEVEL_FUNCTION_CALL_BLOCKED"
                )

            continue

        return (
            False,
            (
                "UNSUPPORTED_TOP_LEVEL_NODE: "
                f"{type(statement).__name__}"
            )
        )

    return (
        True,
        "STATIC_VALIDATION_OK"
    )


# ============================================================
# CAPABILITY SIGNATURE
# ============================================================

def build_signature(
    code: str,
    metadata: dict
) -> dict:

    try:
        tree = ast.parse(code)
    except SyntaxError:
        tree = ast.Module(
            body=[],
            type_ignores=[]
        )

    function_names = []
    imports = []
    calls = []
    operators = []
    docstrings = []

    for node in ast.walk(tree):

        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            )
        ):

            function_names.append(
                node.name
            )

            doc = ast.get_docstring(
                node
            )

            if doc:
                docstrings.append(
                    doc
                )

        elif isinstance(
            node,
            ast.Import
        ):

            imports.extend(
                alias.name
                for alias in node.names
            )

        elif isinstance(
            node,
            ast.ImportFrom
        ):

            imports.append(
                node.module or ""
            )

        elif isinstance(
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

        elif isinstance(
            node,
            ast.BinOp
        ):

            operators.append(
                type(node.op).__name__
            )

        elif isinstance(
            node,
            ast.Compare
        ):

            operators.extend(
                type(op).__name__
                for op in node.ops
            )

    descriptive_text = " ".join(
        [
            str(
                metadata.get(
                    "name",
                    ""
                )
            ),
            str(
                metadata.get(
                    "capability",
                    ""
                )
            ),
            str(
                metadata.get(
                    "purpose",
                    ""
                )
            ),
            " ".join(
                docstrings
            ),
            " ".join(
                function_names
            ),
            " ".join(
                calls
            ),
        ]
    )

    normalized_code = re.sub(
        r"\s+",
        " ",
        code
    ).strip()

    return {
        "hash": sha256_text(
            normalized_code
        ),
        "tokens": sorted(
            tokens(
                descriptive_text
                + " "
                + code
            )
        ),
        "functions": sorted(
            set(function_names)
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
        "capability": str(
            metadata.get(
                "capability",
                ""
            )
        ),
    }


def signature_similarity(
    current: dict,
    previous: dict
) -> float:

    token_score = jaccard(
        set(
            current.get(
                "tokens",
                []
            )
        ),
        set(
            previous.get(
                "tokens",
                []
            )
        )
    )

    function_score = jaccard(
        set(
            current.get(
                "functions",
                []
            )
        ),
        set(
            previous.get(
                "functions",
                []
            )
        )
    )

    import_score = jaccard(
        set(
            current.get(
                "imports",
                []
            )
        ),
        set(
            previous.get(
                "imports",
                []
            )
        )
    )

    call_score = jaccard(
        set(
            current.get(
                "calls",
                []
            )
        ),
        set(
            previous.get(
                "calls",
                []
            )
        )
    )

    capability_score = jaccard(
        tokens(
            current.get(
                "capability",
                ""
            )
        ),
        tokens(
            previous.get(
                "capability",
                ""
            )
        )
    )

    score = (
        token_score * 0.25
        + function_score * 0.15
        + import_score * 0.10
        + call_score * 0.10
        + capability_score * 0.40
    )

    return round(
        min(
            score,
            1.0
        ),
        4
    )


# ============================================================
# ACTIVE SKILL SIGNATURES
# ============================================================

def load_manifest(
    path: Path
) -> Optional[dict]:

    manifest = (
        MANIFEST_DIR
        / f"{path.stem}.json"
    )

    if not manifest.exists():
        return None

    try:
        data = json.loads(
            manifest.read_text(
                encoding="utf-8"
            )
        )

        return data.get(
            "signature"
        )

    except Exception:
        return None


def get_active_signatures() -> List[dict]:

    result = []

    paths = sorted(
        ACTIVE_DIR.glob(
            "skill_module_*.py"
        )
    )

    for path in paths:

        try:

            signature = load_manifest(
                path
            )

            if signature is None:

                code = path.read_text(
                    encoding="utf-8"
                )

                signature = build_signature(
                    code,
                    {}
                )

            signature["skill"] = (
                path.stem
            )

            result.append(
                signature
            )

        except Exception:
            continue

    return result


def calculate_novelty(
    signature: dict
) -> Tuple[
    float,
    Optional[str],
    float
]:

    existing = (
        get_active_signatures()
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

        score = signature_similarity(
            signature,
            previous
        )

        if score > highest:

            highest = score

            closest = previous.get(
                "skill"
            )

    novelty = (
        1.0 - highest
    )

    return (
        round(
            novelty,
            4
        ),
        closest,
        round(
            highest,
            4
        )
    )


# ============================================================
# ACTIVE CONTEXT
# ============================================================

def get_active_context() -> str:

    files = list(
        ACTIVE_DIR.glob(
            "skill_module_*.py"
        )
    )

    def number(path: Path):

        match = re.search(
            r"skill_module_(\d+)",
            path.name
        )

        return (
            int(match.group(1))
            if match
            else 0
        )

    files.sort(
        key=number
    )

    files = files[
        -MAX_ACTIVE_CONTEXT:
    ]

    if not files:
        return (
            "(No trusted active skills yet.)"
        )

    chunks = []

    for path in files:

        try:

            source = path.read_text(
                encoding="utf-8"
            )

            chunks.append(
                f"""
=== {path.stem} ===
{source[:6000]}
"""
            )

        except Exception:
            continue

    return "\n".join(
        chunks
    )[:40000]


# ============================================================
# GENERATION PROMPT
# ============================================================

def build_generation_prompt(
    reason: str = ""
) -> str:

    return f"""
Generate ONE genuinely NEW micro-skill.

ACTIVE SKILL CONTEXT
====================

{get_active_context()}

PREVIOUS REJECTION / REASON
===========================

{reason or "(none)"}

REQUIRED OUTPUT
===============

Return ONLY one JSON object.

Schema:

{{
  "name": "short capability name",
  "capability": "one clear sentence explaining what this skill adds",
  "purpose": "why this capability is useful",
  "primary_function": "function_name",
  "code": "complete Python source",
  "tests": [
    {{
      "args": [],
      "kwargs": {{}},
      "expected": null
    }}
  ]
}}

RULES
=====

CODE:
- valid Python
- standard library only
- offline
- no filesystem access
- no network
- no subprocess
- no os/sys/pathlib
- no input()
- no eval()
- no exec()
- no dynamic import
- no host access
- no environment dependency
- at least one useful function
- no top-level execution
- deterministic where possible

TESTS:
- 3 to 6 cases
- ordinary case
- edge case
- boundary/minimal case
- expected values must be JSON-compatible
- tests must call primary_function

CAPABILITY:
- must NOT duplicate an active skill
- must be materially useful
- must add a new algorithm, transformation,
  reasoning operation, parser, validator, classifier,
  mathematical primitive, planner, or similar capability

Do not create another basic:
- word counter
- date parser
- statistics calculator
- string wrapper
unless the capability is materially different.

Do not output Markdown.
Do not output commentary.
Return JSON only.
"""


# ============================================================
# REPAIR PROMPT
# ============================================================

def build_repair_prompt(
    skill: dict,
    feedback: str
) -> str:

    return f"""
Repair the following generated Python skill.

SKILL DESCRIPTION
=================

{json.dumps(
    {
        "name": skill.get("name"),
        "capability": skill.get("capability"),
        "purpose": skill.get("purpose"),
        "primary_function": skill.get(
            "primary_function"
        ),
    },
    indent=2,
)}

CURRENT CODE
============

{skill.get("code", "")}

TESTS
=====

{json.dumps(
    skill.get("tests", []),
    indent=2
)}

FAILURE
=======

{feedback}

TASK
====

Return the COMPLETE corrected JSON object.

Do not explain.

Do not remove valid tests merely to make them pass.

Actually fix the implementation.

Return JSON only using:

{{
  "name": "...",
  "capability": "...",
  "purpose": "...",
  "primary_function": "...",
  "code": "...",
  "tests": [...]
}}
"""


# ============================================================
# GROQ
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
                temperature=0.15,
                max_tokens=6500,
                response_format={"type": "json_object"},
                timeout=40,
            )
        )

        return (
            response.choices[0]
            .message
            .content
        )

    except Exception as exc:

        print(
            f"⚠️ Groq failed: "
            f"{type(exc).__name__}: {exc}"
        )

        remember(
            "groq_error",
            (
                f"{type(exc).__name__}: "
                f"{exc}"
            )
        )

        return None


# ============================================================
# OPENROUTER
# ============================================================

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
        "temperature": 0.15,
        "max_tokens": 6500,
        "response_format": {
            "type": "json_object"
        },
    }

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
                "BEE5 v3",
        },
        method="POST"
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=45
        ) as response:

            body = response.read(
                200000
            )

            status = response.status

        print(
            f"✅ OpenRouter HTTP {status}"
        )

        data = json.loads(
            body.decode(
                "utf-8"
            )
        )

        return (
            data["choices"][0]
            ["message"]
            ["content"]
        )

    except urllib.error.HTTPError as exc:

        try:
            body = exc.read(
                20000
            ).decode(
                "utf-8",
                errors="replace"
            )
        except Exception:
            body = ""

        print(
            f"❌ OpenRouter HTTP "
            f"{exc.code}"
        )

        if body:
            print(
                f"Response: {body[:3000]}"
            )

        remember(
            "openrouter_error",
            (
                f"HTTP {exc.code}: "
                f"{body[:3000]}"
            )
        )

        return None

    except Exception as exc:

        print(
            f"❌ OpenRouter failed: "
            f"{type(exc).__name__}: {exc}"
        )

        remember(
            "openrouter_error",
            (
                f"{type(exc).__name__}: "
                f"{exc}"
            )
        )

        return None


# ============================================================
# UNIFIED GENERATION
# ============================================================

def generate_json_skill(
    prompt: str
) -> Optional[dict]:

    raw = ask_groq(
        prompt
    )

    if not raw:

        raw = ask_openrouter(
            prompt
        )

    if not raw:
        return None

    data = clean_json_response(
        raw
    )

    if not data:
        print(
            "❌ Model response was not valid JSON."
        )
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

        print(
            "❌ Model JSON missing required fields."
        )

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
# TEST CONTRACT VALIDATION
# ============================================================

def validate_test_contract(
    skill: dict
) -> Tuple[
    bool,
    str
]:

    primary = skill.get(
        "primary_function"
    )

    tests = skill.get(
        "tests"
    )

    if not isinstance(
        primary,
        str
    ) or not primary.strip():

        return (
            False,
            "Missing primary_function"
        )

    if not isinstance(
        tests,
        list
    ):

        return (
            False,
            "Tests must be a list"
        )

    if not 3 <= len(tests) <= 6:

        return (
            False,
            (
                "Expected 3-6 tests, "
                f"got {len(tests)}"
            )
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

        args = test.get(
            "args",
            []
        )

        kwargs = test.get(
            "kwargs",
            {}
        )

        if not isinstance(
            args,
            list
        ):

            return (
                False,
                f"Test {index} args invalid"
            )

        if not isinstance(
            kwargs,
            dict
        ):

            return (
                False,
                f"Test {index} kwargs invalid"
            )

        try:

            json.dumps(
                test.get(
                    "expected"
                )
            )

        except TypeError:

            return (
                False,
                (
                    f"Test {index} expected "
                    "value not JSON compatible"
                )
            )

    return (
        True,
        "TEST_CONTRACT_OK"
    )


# ============================================================
# FUNCTIONAL TEST RUNNER
# ============================================================

def build_runner(
    module_path: Path,
    primary_function: str,
    tests: List[dict]
) -> str:

    module_literal = repr(
        str(module_path)
    )

    tests_json = json.dumps(
        tests,
        ensure_ascii=False
    )

    return f'''
import importlib.util
import json
import traceback

MODULE_PATH = {module_literal}
FUNCTION_NAME = {primary_function!r}
TESTS = json.loads({tests_json!r})


def normalize(value):

    if isinstance(value, dict):
        return {{
            str(k): normalize(v)
            for k, v in value.items()
        }}

    if isinstance(value, (list, tuple)):
        return [
            normalize(v)
            for v in value
        ]

    if isinstance(value, set):
        result = [
            normalize(v)
            for v in value
        ]

        return sorted(
            result,
            key=repr
        )

    if isinstance(
        value,
        (str, int, float, bool)
    ) or value is None:

        return value

    if hasattr(
        value,
        "isoformat"
    ):

        try:
            return value.isoformat()
        except Exception:
            pass

    return repr(value)


spec = importlib.util.spec_from_file_location(
    "bee5_candidate",
    MODULE_PATH
)

if spec is None or spec.loader is None:
    raise RuntimeError(
        "Could not load candidate module"
    )

module = importlib.util.module_from_spec(
    spec
)

spec.loader.exec_module(
    module
)

if not hasattr(
    module,
    FUNCTION_NAME
):
    raise RuntimeError(
        f"Missing function: {{FUNCTION_NAME}}"
    )

fn = getattr(
    module,
    FUNCTION_NAME
)

results = []
passed = 0

for index, test in enumerate(
    TESTS,
    start=1
):

    try:

        actual = fn(
            *test.get("args", []),
            **test.get("kwargs", {{}})
        )

        actual = normalize(
            actual
        )

        expected = test.get(
            "expected"
        )

        ok = actual == expected

        if ok:
            passed += 1

        results.append({{
            "test": index,
            "passed": ok,
            "expected": expected,
            "actual": actual
        }})

    except Exception as exc:

        results.append({{
            "test": index,
            "passed": False,
            "error": (
                f"{{type(exc).__name__}}: {{exc}}"
            )
        }})

print(
    json.dumps(
        {{
            "passed": passed,
            "total": len(TESTS),
            "results": results
        }},
        ensure_ascii=False
    )
)

if passed != len(TESTS):
    raise SystemExit(2)
'''


def run_functional_tests(
    code: str,
    skill_name: str,
    primary_function: str,
    tests: List[dict]
) -> Tuple[
    bool,
    dict
]:

    module_path = (
        CANDIDATE_DIR
        / f"{skill_name}.py"
    )

    runner_path = (
        SANDBOX_DIR
        / f"{skill_name}_runner.py"
    )

    module_path.write_text(
        code,
        encoding="utf-8"
    )

    runner_path.write_text(
        build_runner(
            module_path,
            primary_function,
            tests
        ),
        encoding="utf-8"
    )

    try:

        result = subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                str(runner_path)
            ],
            cwd=str(
                SANDBOX_DIR
            ),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=MAX_SKILL_SECONDS
        )

    except subprocess.TimeoutExpired:

        return (
            False,
            {
                "passed": 0,
                "total": len(tests),
                "results": [],
                "error": "TIMEOUT"
            }
        )

    stdout = (
        result.stdout or ""
    ).strip()

    stderr = (
        result.stderr or ""
    ).strip()

    report = None

    for line in reversed(
        stdout.splitlines()
    ):

        try:

            data = json.loads(
                line
            )

            if (
                "passed" in data
                and
                "total" in data
            ):

                report = data
                break

        except Exception:
            continue

    if report is None:

        return (
            False,
            {
                "passed": 0,
                "total": len(tests),
                "results": [],
                "error": (
                    stderr
                    or
                    "No test report returned"
                )
            }
        )

    success = (
        result.returncode == 0
        and
        report["passed"]
        ==
        report["total"]
    )

    if stderr:
        report["stderr"] = stderr[-5000:]

    return (
        success,
        report
    )


# ============================================================
# DETERMINISM TEST
# ============================================================

def run_determinism_test(
    skill_name: str,
    primary_function: str,
    tests: List[dict]
) -> Tuple[
    bool,
    str
]:

    module_path = (
        CANDIDATE_DIR
        / f"{skill_name}.py"
    )

    runner_path = (
        SANDBOX_DIR
        / f"{skill_name}_determinism.py"
    )

    serialized_tests = json.dumps(
        tests,
        ensure_ascii=False
    )

    runner = f'''
import importlib.util
import json

MODULE_PATH = {str(module_path)!r}
FUNCTION_NAME = {primary_function!r}
TESTS = json.loads({serialized_tests!r})


def normalize(value):

    if isinstance(value, dict):
        return {{
            str(k): normalize(v)
            for k, v in value.items()
        }}

    if isinstance(value, (list, tuple)):
        return [
            normalize(v)
            for v in value
        ]

    if isinstance(value, set):
        return sorted(
            [normalize(v) for v in value],
            key=repr
        )

    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass

    return value


spec = importlib.util.spec_from_file_location(
    "determinism_candidate",
    MODULE_PATH
)

module = importlib.util.module_from_spec(
    spec
)

spec.loader.exec_module(
    module
)

fn = getattr(
    module,
    FUNCTION_NAME
)

for index, test in enumerate(
    TESTS,
    start=1
):

    first = normalize(
        fn(
            *test.get("args", []),
            **test.get("kwargs", {{}})
        )
    )

    second = normalize(
        fn(
            *test.get("args", []),
            **test.get("kwargs", {{}})
        )
    )

    if first != second:
        print(
            json.dumps(
                {{
                    "passed": False,
                    "test": index,
                    "first": first,
                    "second": second
                }}
            )
        )
        raise SystemExit(2)

print(
    json.dumps(
        {{
            "passed": True
        }}
    )
)
'''

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
                str(runner_path)
            ],
            cwd=str(
                SANDBOX_DIR
            ),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=MAX_SKILL_SECONDS
        )

        if result.returncode != 0:

            return (
                False,
                (
                    result.stderr
                    or result.stdout
                    or "Non-deterministic behavior"
                )[-5000:]
            )

        return (
            True,
            "Determinism test passed"
        )

    except subprocess.TimeoutExpired:

        return (
            False,
            "Determinism test timeout"
        )

    except Exception as exc:

        return (
            False,
            (
                f"Determinism infrastructure error: "
                f"{type(exc).__name__}: {exc}"
            )
        )


# ============================================================
# SCORE
# ============================================================

def calculate_score(
    novelty: float,
    tests_report: dict,
    determinism_ok: bool
) -> float:

    total = int(
        tests_report.get(
            "total",
            0
        )
    )

    passed = int(
        tests_report.get(
            "passed",
            0
        )
    )

    if total:

        functional = (
            passed / total
        ) * 40.0

    else:

        functional = 0.0

    novelty_points = (
        max(
            0.0,
            min(
                novelty,
                1.0
            )
        )
        * 35.0
    )

    determinism_points = (
        10.0
        if determinism_ok
        else 0.0
    )

    structural_points = 15.0

    score = (
        structural_points
        + functional
        + novelty_points
        + determinism_points
    )

    return round(
        min(
            100.0,
            score
        ),
        2
    )


# ============================================================
# BACKUP
# ============================================================

def backup_active_skills():

    timestamp = time.strftime(
        "%Y%m%d_%H%M%S"
    )

    target = (
        BACKUP_DIR
        / timestamp
    )

    target.mkdir(
        parents=True,
        exist_ok=True
    )

    count = 0

    for path in ACTIVE_DIR.glob(
        "skill_module_*.py"
    ):

        try:

            destination = (
                target
                / path.name
            )

            destination.write_text(
                path.read_text(
                    encoding="utf-8"
                ),
                encoding="utf-8"
            )

            count += 1

        except Exception:
            pass

    return (
        target,
        count
    )


# ============================================================
# REPORTS
# ============================================================

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


def save_manifest(
    skill_name: str,
    signature: dict,
    metadata: dict,
    report: dict
):

    path = (
        MANIFEST_DIR
        / f"{skill_name}.json"
    )

    data = {
        "skill": skill_name,
        "signature": signature,
        "metadata": metadata,
        "evaluation": report,
        "created_at": time.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    }

    path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )


# ============================================================
# MOVE / PROMOTE
# ============================================================

def move_to_cemetery(
    skill_name: str,
    code: str,
    metadata: dict,
    report: dict,
    reason: str
):

    folder = (
        CEMETERY_DIR
        / skill_name
    )

    folder.mkdir(
        parents=True,
        exist_ok=True
    )

    (
        folder / "code.py"
    ).write_text(
        code,
        encoding="utf-8"
    )

    (
        folder / "metadata.json"
    ).write_text(
        json.dumps(
            metadata,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    (
        folder / "evaluation.json"
    ).write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    (
        folder / "reason.txt"
    ).write_text(
        reason,
        encoding="utf-8"
    )


def promote_to_active(
    skill_name: str,
    code: str,
    metadata: dict,
    signature: dict,
    report: dict
):

    active_path = (
        ACTIVE_DIR
        / f"{skill_name}.py"
    )

    active_path.write_text(
        code,
        encoding="utf-8"
    )

    save_manifest(
        skill_name,
        signature,
        metadata,
        report
    )

    candidate_path = (
        CANDIDATE_DIR
        / f"{skill_name}.py"
    )

    if candidate_path.exists():

        try:
            candidate_path.unlink()
        except Exception:
            pass


def keep_as_candidate(
    skill_name: str,
    code: str,
    metadata: dict,
    signature: dict,
    report: dict
):

    candidate_path = (
        CANDIDATE_DIR
        / f"{skill_name}.py"
    )

    candidate_path.write_text(
        code,
        encoding="utf-8"
    )

    save_manifest(
        skill_name,
        signature,
        metadata,
        report
    )


# ============================================================
# REPAIR
# ============================================================

def repair_skill(
    skill: dict,
    feedback: str
) -> Optional[dict]:

    prompt = build_repair_prompt(
        skill,
        feedback
    )

    raw = ask_groq(
        prompt
    )

    if not raw:

        raw = ask_openrouter(
            prompt
        )

    if not raw:
        return None

    repaired = clean_json_response(
        raw
    )

    if not repaired:
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
        repaired
    ):
        return None

    repaired["code"] = clean_code(
        repaired["code"]
    )

    return repaired


# ============================================================
# ONE CYCLE
# ============================================================

def run_cycle(
    skill_number: int
) -> bool:

    skill_name = (
        f"skill_module_{skill_number}"
    )

    print()
    print(
        "=" * 68
    )
    print(
        f"🧠 Evolution cycle: {skill_name}"
    )
    print(
        "=" * 68
    )

    backup_path, backup_count = (
        backup_active_skills()
    )

    print(
        f"💾 Backup: {backup_path.name} "
        f"({backup_count} active skills)"
    )

    last_reason = ""

    for generation_attempt in range(
        1,
        MAX_GENERATION_ATTEMPTS + 1
    ):

        print(
            f"\n🧬 Generation "
            f"{generation_attempt}/"
            f"{MAX_GENERATION_ATTEMPTS}"
        )

        skill = generate_json_skill(
            build_generation_prompt(
                last_reason
            )
        )

        if not skill:

            last_reason = (
                "Model generation failed or "
                "returned invalid JSON."
            )

            print(
                f"⚠️ {last_reason}"
            )

            continue

        code = skill["code"]

        # ----------------------------------------------------
        # STATIC VALIDATION
        # ----------------------------------------------------

        safe, safety_feedback = (
            validate_generated_code(
                code
            )
        )

        if not safe:

            last_reason = safety_feedback

            print(
                f"🚫 Rejected: "
                f"{safety_feedback}"
            )

            remember(
                "static_rejection",
                (
                    f"{skill_name}: "
                    f"{safety_feedback}"
                )
            )

            continue

        tests_valid, test_feedback = (
            validate_test_contract(
                skill
            )
        )

        if not tests_valid:

            last_reason = (
                test_feedback
            )

            print(
                f"❌ Invalid test contract: "
                f"{test_feedback}"
            )

            continue

        # ----------------------------------------------------
        # SIGNATURE / NOVELTY
        # ----------------------------------------------------

        signature = build_signature(
            code,
            skill
        )

        novelty, closest, similarity = (
            calculate_novelty(
                signature
            )
        )

        print(
            f"🧬 Novelty: "
            f"{novelty:.2f}"
        )

        if closest:

            print(
                f"🔎 Closest active skill: "
                f"{closest}"
            )

            print(
                f"🔎 Similarity: "
                f"{similarity:.2f}"
            )

        if novelty < NOVELTY_MINIMUM:

            last_reason = (
                "Capability is too similar to "
                f"{closest}. "
                f"Similarity={similarity}"
            )

            print(
                "♻️ Duplicate / "
                "near-duplicate detected."
            )

            remember(
                "duplicate_rejection",
                (
                    f"{skill_name} -> "
                    f"{closest}, "
                    f"similarity={similarity}"
                )
            )

            continue

        # ----------------------------------------------------
        # CANDIDATE
        # ----------------------------------------------------

        candidate_path = (
            CANDIDATE_DIR
            / f"{skill_name}.py"
        )

        candidate_path.write_text(
            code,
            encoding="utf-8"
        )

        print(
            "📦 Candidate created."
        )

        # ----------------------------------------------------
        # REPAIR / FUNCTIONAL LOOP
        # ----------------------------------------------------

        current_skill = skill
        current_code = code
        final_test_report = {}
        final_determinism = False

        repaired = False

        for attempt in range(
            1,
            MAX_REPAIR_ATTEMPTS + 2
        ):

            print(
                f"🧪 Evaluation attempt "
                f"{attempt}"
            )

            tests_ok, test_report = (
                run_functional_tests(
                    current_code,
                    skill_name,
                    current_skill[
                        "primary_function"
                    ],
                    current_skill[
                        "tests"
                    ]
                )
            )

            print(
                f"📊 Tests: "
                f"{test_report.get('passed', 0)}/"
                f"{test_report.get('total', 0)}"
            )

            if test_report.get(
                "results"
            ):

                for item in (
                    test_report[
                        "results"
                    ][:5]
                ):

                    if not item.get(
                        "passed"
                    ):

                        print(
                            "❌ "
                            + str(item)
                        )

            determinism_ok = False

            if tests_ok:

                determinism_ok, deterministic_feedback = (
                    run_determinism_test(
                        skill_name,
                        current_skill[
                            "primary_function"
                        ],
                        current_skill[
                            "tests"
                        ]
                    )
                )

                print(
                    "🔁 Determinism: "
                    + (
                        "PASS"
                        if determinism_ok
                        else "FAIL"
                    )
                )

                if not determinism_ok:

                    print(
                        f"⚠️ {deterministic_feedback}"
                    )

            final_test_report = (
                test_report
            )

            final_determinism = (
                determinism_ok
            )

            if tests_ok and determinism_ok:

                repaired = True
                break

            failure = json.dumps(
                test_report,
                indent=2,
                ensure_ascii=False
            )

            if attempt > MAX_REPAIR_ATTEMPTS:

                break

            print(
                "🔧 Asking model to "
                "repair the skill..."
            )

            repaired_skill = repair_skill(
                current_skill,
                failure
            )

            if not repaired_skill:

                print(
                    "⚠️ Repair generation failed."
                )

                break

            current_skill = (
                repaired_skill
            )

            current_code = (
                repaired_skill[
                    "code"
                ]
            )

            safe, safety_feedback = (
                validate_generated_code(
                    current_code
                )
            )

            if not safe:

                print(
                    "🚫 Repair failed "
                    "static validation:"
                )

                print(
                    safety_feedback
                )

                break

            tests_valid, test_feedback = (
                validate_test_contract(
                    current_skill
                )
            )

            if not tests_valid:

                print(
                    "🚫 Repaired test contract "
                    "invalid:"
                )

                print(
                    test_feedback
                )

                break

        # ----------------------------------------------------
        # FINAL SIGNATURE / NOVELTY AFTER REPAIR
        # ----------------------------------------------------

        signature = build_signature(
            current_code,
            current_skill
        )

        novelty, closest, similarity = (
            calculate_novelty(
                signature
            )
        )

        # A repaired skill must still be novel.
        if novelty < NOVELTY_MINIMUM:

            report = {
                "status": "duplicate_after_repair",
                "score": 0,
                "novelty": novelty,
                "similarity": similarity,
                "closest_skill": closest,
                "tests": final_test_report,
                "determinism": final_determinism,
            }

            move_to_cemetery(
                skill_name,
                current_code,
                current_skill,
                report,
                (
                    "Became / remained too similar "
                    "to existing capability after repair."
                )
            )

            save_report(
                skill_name,
                report
            )

            record_run(
                skill_name,
                "duplicate",
                0,
                novelty,
                similarity,
                generation_attempt,
                "Duplicate after repair"
            )

            print(
                "🪦 Duplicate sent to cemetery."
            )

            return False

        # ----------------------------------------------------
        # SCORE
        # ----------------------------------------------------

        score = calculate_score(
            novelty,
            final_test_report,
            final_determinism
        )

        if not repaired:

            # Failure to prove correctness:
            # do not grant the full score.
            score = min(
                score,
                59.0
            )

        if score >= ACTIVE_SCORE:

            status = "ACTIVE"

        elif score >= CANDIDATE_SCORE:

            status = "CANDIDATE"

        else:

            status = "CEMETERY"

        report = {
            "status": status,
            "score": score,
            "novelty": novelty,
            "similarity": similarity,
            "closest_skill": closest,
            "tests": final_test_report,
            "determinism": final_determinism,
            "generation_attempt": generation_attempt,
            "backup": str(
                backup_path
            ),
        }

        save_report(
            skill_name,
            report
        )

        record_run(
            skill_name,
            status.lower(),
            score,
            novelty,
            similarity,
            generation_attempt,
            json.dumps(
                report,
                ensure_ascii=False
            )
        )

        # ----------------------------------------------------
        # ACTIVE
        # ----------------------------------------------------

        if status == "ACTIVE":

            promote_to_active(
                skill_name,
                current_code,
                current_skill,
                signature,
                report
            )

            remember(
                "active_skill",
                (
                    f"{skill_name}: "
                    f"{current_skill['capability']} "
                    f"score={score}"
                )
            )

            set_state(
                "last_successful_skill",
                skill_name
            )

            print()
            print(
                "✅ SKILL PROMOTED"
            )

            print(
                f"🏆 Score: {score}/100"
            )

            return True

        # ----------------------------------------------------
        # CANDIDATE
        # ----------------------------------------------------

        if status == "CANDIDATE":

            keep_as_candidate(
                skill_name,
                current_code,
                current_skill,
                signature,
                report
            )

            remember(
                "candidate_skill",
                (
                    f"{skill_name}: "
                    f"{current_skill['capability']} "
                    f"score={score}"
                )
            )

            print()
            print(
                "🟡 SKILL KEPT AS CANDIDATE"
            )

            print(
                f"📊 Score: {score}/100"
            )

            return False

        # ----------------------------------------------------
        # CEMETERY
        # ----------------------------------------------------

        move_to_cemetery(
            skill_name,
            current_code,
            current_skill,
            report,
            (
                f"Quality threshold failed. "
                f"score={score}, "
                f"tests="
                f"{final_test_report.get('passed', 0)}/"
                f"{final_test_report.get('total', 0)}, "
                f"determinism={final_determinism}"
            )
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

    print()
    print(
        "⚠️ All generation attempts exhausted."
    )

    remember(
        "cycle_failure",
        (
            f"{skill_name}: all "
            f"{MAX_GENERATION_ATTEMPTS} "
            "generation attempts failed."
        )
    )

    return False


# ============================================================
# STATUS
# ============================================================

def print_status():

    active = list(
        ACTIVE_DIR.glob(
            "skill_module_*.py"
        )
    )

    candidates = list(
        CANDIDATE_DIR.glob(
            "skill_module_*.py"
        )
    )

    cemetery = list(
        CEMETERY_DIR.glob(
            "skill_module_*"
        )
    )

    reports = list(
        REPORT_DIR.glob(
            "*.json"
        )
    )

    print()
    print(
        "=" * 52
    )
    print(
        "              BEE5 STATUS"
    )
    print(
        "=" * 52
    )

    print(
        f"Active skills      : {len(active)}"
    )

    print(
        f"Candidate skills   : {len(candidates)}"
    )

    print(
        f"Cemetery records   : {len(cemetery)}"
    )

    print(
        f"Evaluation reports : {len(reports)}"
    )

    print(
        "Last success       : "
        + get_state(
            "last_successful_skill",
            "none"
        )
    )

    print(
        "=" * 52
    )
    print()


# ============================================================
# MAIN
# ============================================================

def main():

    init_database()

    print()
    print(
        "╔══════════════════════════════════════════════╗"
    )
    print(
        "║       BEE5 AUTONOMOUS BRAIN v3             ║"
    )
    print(
        "║                                              ║"
    )
    print(
        "║  NOVELTY → TEST → REPAIR → SCORE → EVOLVE  ║"
    )
    print(
        "╚══════════════════════════════════════════════╝"
    )
    print()

    if not GROQ_API_KEY:
        print(
            "ℹ️ Groq not configured."
        )

    if not OPENROUTER_API_KEY:
        print(
            "ℹ️ OpenRouter not configured."
        )

    if (
        not GROQ_API_KEY
        and
        not OPENROUTER_API_KEY
    ):

        raise SystemExit(
            "❌ No LLM API key configured."
        )

    print_status()

    next_number = (
        get_next_skill_number()
    )

    print(
        f"▶ Next skill: "
        f"skill_module_{next_number}"
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
                        f"{remaining:02d}s",
                        end="",
                        flush=True
                    )

            print(
                "\r"
                + " " * 20
                + "\r",
                end="",
                flush=True
            )

    except KeyboardInterrupt:

        print()
        print()
        print(
            "🛑 Operator interrupt."
        )

        print_status()


if __name__ == "__main__":
    main()
