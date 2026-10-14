#!/usr/bin/env python3

"""
BEE5 TRUE EVOLUTION ENGINE
==========================

Safety-first, evaluator-driven mutation engine.

Core properties:

1. Parent source is NEVER overwritten during evolution.
2. Every mutation is created from the original parent.
3. Mutations are syntax checked.
4. Mutations are evaluated against the real evaluator.
5. Candidate must strictly improve the parent's score.
6. Failed candidates are rejected and archived as evidence.
7. Multiple mutation rounds are supported.
8. Evaluator failures are fed back into later LLM attempts.
9. Deterministic generic operators can compete with LLM mutations.
10. Mutation is restricted to the discovered target function.
11. Parent/candidate hashes are recorded.
12. Full diff and lineage metadata are preserved.
13. Structured JSON mutation is used instead of raw source generation.
14. Model reasoning output is disabled so structured output remains clean.
15. No mutation is promoted merely because it "looks correct".
16. Real evaluator evidence is the acceptance authority.

IMPORTANT:
This engine does NOT modify the live target automatically.
A winning mutation is archived first.
That keeps the live parent protected.
"""


import ast
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from bee5_runtime import LLAMA, MODEL


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parent

EVOLUTION_ROOT = ROOT / "evolution"

WORKSPACE = EVOLUTION_ROOT / "workspace"
ARCHIVE = EVOLUTION_ROOT / "archive"
REJECTED = EVOLUTION_ROOT / "rejected"
LOGS = EVOLUTION_ROOT / "logs"

LINEAGE = EVOLUTION_ROOT / "lineage.jsonl"


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_COMMAND_TIMEOUT = 300
DEFAULT_MUTATION_ROUNDS = 3
DEFAULT_GENERATION_RETRIES = 3
DEFAULT_REASONING_BUDGET = 0


# ============================================================
# BASIC UTILITIES
# ============================================================

def sha256_file(path: Path) -> str:
    """
    Calculate SHA-256 hash of a file.
    """

    h = hashlib.sha256()

    with path.open("rb") as f:

        while True:

            chunk = f.read(1024 * 1024)

            if not chunk:
                break

            h.update(chunk)

    return h.hexdigest()


def write_jsonl(path: Path, data):
    """
    Append one JSON object to a JSONL file.
    """

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with path.open(
        "a",
        encoding="utf-8"
    ) as f:

        f.write(
            json.dumps(
                data,
                ensure_ascii=False
            )
            + "\n"
        )


def run_command(
    command,
    timeout=DEFAULT_COMMAND_TIMEOUT
):
    """
    Execute a subprocess in the BEE5 root.

    stdout and stderr remain separate.
    """

    return subprocess.run(
        command,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=timeout,
    )


# ============================================================
# SYNTAX
# ============================================================

def syntax_check(path: Path):
    """
    Validate complete Python source syntax.
    """

    source = path.read_text(
        encoding="utf-8"
    )

    ast.parse(source)

    return {
        "ok": True
    }


# ============================================================
# EVALUATION
# ============================================================

def evaluate(
    target: Path,
    evaluator: Path
):
    """
    Execute the evaluator against a candidate.

    Evaluator stdout is treated as JSON.
    stderr is diagnostic only.
    """

    result = run_command(
        [
            sys.executable,
            str(evaluator),
            str(target)
        ],
        timeout=DEFAULT_COMMAND_TIMEOUT
    )

    stdout = result.stdout.strip()
    stderr = result.stderr.strip()

    try:

        data = json.loads(
            stdout
        )

    except Exception:

        data = {
            "ok": False,
            "error": (
                "Evaluator did not return valid JSON."
            ),
            "stdout": stdout,
            "stderr": stderr,
        }

    data["returncode"] = result.returncode

    if result.returncode != 0:
        data["ok"] = False

    if stderr:
        data["_stderr"] = stderr

    return data


# ============================================================
# DIFF
# ============================================================

def make_diff(
    parent: Path,
    candidate_path: Path
):
    """
    Generate unified diff between parent and candidate.
    """

    old = parent.read_text(
        encoding="utf-8"
    ).splitlines(
        keepends=True
    )

    new = candidate_path.read_text(
        encoding="utf-8"
    ).splitlines(
        keepends=True
    )

    return "".join(
        difflib.unified_diff(
            old,
            new,
            fromfile=str(parent),
            tofile=str(candidate_path)
        )
    )


# ============================================================
# FUNCTION DISCOVERY
# ============================================================

def _find_function(
    tree: ast.Module,
    name: str = None
):
    """
    Locate target function.

    Priority:

    1. Explicit function name.
    2. BEE5_TARGET_FUNCTION environment variable.
    3. First top-level function.
    """

    override = (
        name
        or os.environ.get(
            "BEE5_TARGET_FUNCTION"
        )
    )

    functions = [
        node
        for node in tree.body
        if isinstance(
            node,
            ast.FunctionDef
        )
    ]

    if override:

        for node in functions:

            if node.name == override:
                return node

        return None

    return (
        functions[0]
        if functions
        else None
    )


def _function_source(
    source: str,
    function_node: ast.FunctionDef
):
    """
    Extract exact target function source.
    """

    lines = source.splitlines(
        keepends=True
    )

    return "".join(
        lines[
            function_node.lineno - 1:
            function_node.end_lineno
        ]
    )


# ============================================================
# TARGET FUNCTION RANGE
# ============================================================

def _target_range(
    source: str,
    function_node: ast.FunctionDef
):
    """
    Return target function source line range.
    """

    lines = source.splitlines(
        keepends=True
    )

    start = function_node.lineno - 1
    end = function_node.end_lineno

    return (
        start,
        end,
        lines
    )


# ============================================================
# GENERIC DETERMINISTIC OPERATOR
# ============================================================

def build_deterministic_candidate(
    source: str,
    function_node: ast.FunctionDef
):
    """
    Generic normalization operator.

    If the target contains a return expression, wrap the returned
    string expression with a generic punctuation-spacing cleanup.

    Example:

        return " ".join(text.strip().split())

    becomes conceptually:

        return _BEE5_PUNCT_RE.sub(
            r"\\1",
            " ".join(text.strip().split())
        )

    This is NOT tied to a specific evaluator input.

    The evaluator remains the final authority.
    """

    lines = source.splitlines(
        keepends=True
    )

    func_start = (
        function_node.lineno - 1
    )

    func_end = (
        function_node.end_lineno
    )

    target_idx = None
    indent = None
    expr = None

    for i in range(
        func_start,
        func_end
    ):

        stripped = lines[i].rstrip(
            "\n"
        )

        match = re.match(
            r"^(\s*)return (.+)$",
            stripped
        )

        if match:

            target_idx = i
            indent = match.group(1)
            expr = match.group(2).strip()

            break

    if target_idx is None:
        return None

    if "_BEE5_PUNCT_RE" in source:
        return None

    newline = (
        "\n"
        if lines[target_idx].endswith("\n")
        else ""
    )

    lines[target_idx] = (
        f'{indent}'
        f'return _BEE5_PUNCT_RE.sub('
        f'r"\\1", '
        f'{expr}'
        f'){newline}'
    )

    combined = "".join(
        lines
    )

    if "_BEE5_PUNCT_RE =" not in combined:

        helper_block = (
            "import re as _bee5_re\n"
            "_BEE5_PUNCT_RE = "
            '_bee5_re.compile(r"\\s+([,.!?;:])")\n'
            "\n"
        )

        combined_lines = combined.splitlines(keepends=True)

        if combined_lines and combined_lines[0].startswith("#!"):
            # Keep the shebang as the very first line.
            combined = (
                combined_lines[0]
                + helper_block
                + "".join(combined_lines[1:])
            )
        else:
            combined = (
                helper_block
                + combined
            )

    return combined


# ============================================================
# MUTATION SCHEMA
# ============================================================

MUTATION_SCHEMA = {

    "type": "object",

    "properties": {

        "operation": {
            "type": "string",
            "enum": [
                "replace_text"
            ]
        },

        "target": {
            "type": "string"
        },

        "replacement": {
            "type": "string"
        },

        "reason": {
            "type": "string"
        }
    },

    "required": [
        "operation",
        "target",
        "replacement",
        "reason"
    ],

    "additionalProperties": False
}


# ============================================================
# JSON EXTRACTION
# ============================================================

def _extract_json_object(text: str):
    """
    Extract first valid JSON object from model stdout.
    """

    decoder = json.JSONDecoder()

    for index, char in enumerate(text):

        if char != "{":
            continue

        try:

            obj, _ = decoder.raw_decode(
                text[index:]
            )

        except Exception:
            continue

        if isinstance(
            obj,
            dict
        ):
            return obj

    raise RuntimeError(
        "No valid mutation JSON object found."
    )


# ============================================================
# STRUCTURED MUTATION GENERATOR
# ============================================================

def generate_mutation(
    parent: Path,
    task: str,
    parent_eval: dict,
    extra_feedback: str = None
):
    """
    Generate a structured mutation.

    The model does NOT generate the complete file.

    It proposes:

        target
        replacement

    The engine performs the actual source reconstruction.

    This prevents arbitrary model output from directly becoming
    executable source.
    """

    source = parent.read_text(
        encoding="utf-8"
    )

    failures = parent_eval.get(
        "failures",
        []
    )

    tree = ast.parse(
        source
    )

    function_node = _find_function(
        tree
    )

    if function_node is None:

        raise RuntimeError(
            "No target function found in parent source."
        )

    function_source = _function_source(
        source,
        function_node
    )

    function_name = function_node.name

    reasoning_budget = int(
        os.environ.get(
            "BEE5_REASONING_BUDGET",
            str(DEFAULT_REASONING_BUDGET)
        )
    )

    last_error = ""

    for attempt in range(
        1,
        DEFAULT_GENERATION_RETRIES + 1
    ):

        prompt = f"""
You are BEE5's controlled mutation planner.

Your job is to propose ONE small, real source mutation.

TASK:
{task}

TARGET FUNCTION:
{function_name}

CURRENT FUNCTION:
----- BEGIN FUNCTION -----
{function_source}
----- END FUNCTION -----

PARENT EVALUATION:
{json.dumps(
    parent_eval,
    ensure_ascii=False,
    indent=2
)}

PARENT FAILURES:
{json.dumps(
    failures,
    ensure_ascii=False,
    indent=2
)}

FEEDBACK FROM PREVIOUS REJECTED CANDIDATE:
{extra_feedback or "None. This is the first candidate."}

PREVIOUS MUTATION-FORMAT ERROR:
{last_error or "None."}

Before producing the JSON, silently verify the proposed mutation
against every supplied evaluator failure and all supplied
regression information.

Do not output your reasoning.

IMPORTANT:

- Return exactly ONE mutation.
- operation MUST be "replace_text".
- target MUST be an exact substring of the current target function.
- target MUST occur exactly once.
- replacement MUST be different from target.
- Resulting source MUST remain valid Python.
- Preserve all existing passing behavior.
- Fix the actual failure instead of hiding it.
- Do NOT truncate output.
- Do NOT discard input.
- Do NOT limit tokens.
- Do NOT use arbitrary slicing.
- Do NOT introduce [:2], [:3], [:-1] or similar destructive edits.
- Do NOT delete information merely to make a test pass.
- Do NOT rename the function.
- Do NOT change the public function contract.
- Prefer the smallest semantic correction.
- Do NOT invent test results.
- Do NOT return the whole function.
- Do NOT return markdown.
- Do NOT include explanatory text outside the JSON.
- "target" MUST be copied verbatim from the CURRENT FUNCTION block
  above (real Python source code). It must NEVER be a literal test
  input or expected output string taken from PARENT FAILURES — those
  are data used only to understand what is wrong, not text to search
  for inside the source.

Return ONLY:

{{
  "operation": "replace_text",
  "target": "exact existing source text",
  "replacement": "replacement source text",
  "reason": "brief explanation"
}}
""".strip()

        temp = round(
            0.2 + (attempt - 1) * 0.2,
            2
        )

        command = [

            str(LLAMA),

            "-m",
            str(MODEL),

            "-p",
            prompt,

            "-n",
            "256",

            "-j",
            json.dumps(
                MUTATION_SCHEMA,
                separators=(
                    ",",
                    ":"
                )
            ),

            "--reasoning-budget",
            str(reasoning_budget),

            "--reasoning-format",
            "none",

            "--temp",
            str(temp),

            "--top-k",
            "20",

            "-st",

            "--no-display-prompt",

            "--simple-io",

            "--single-turn",
        ]

        try:

            result = run_command(
                command,
                timeout=DEFAULT_COMMAND_TIMEOUT
            )

        except subprocess.TimeoutExpired as exc:

            last_error = (
                "Mutation model timeout."
            )

            raw_path = (
                LOGS
                / f"structured_mutation_attempt_{attempt}.txt"
            )

            raw_path.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            raw_path.write_text(
                str(exc),
                encoding="utf-8"
            )

            continue

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        raw_path = (
            LOGS
            / f"structured_mutation_attempt_{attempt}.txt"
        )

        raw_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        raw_path.write_text(
            "===== STDOUT =====\n"
            + stdout
            + "\n\n"
            + "===== STDERR =====\n"
            + stderr,
            encoding="utf-8"
        )

        if result.returncode != 0:

            last_error = (
                stderr
                or stdout
                or "Mutation command failed."
            )

            continue

        try:

            proposal = _extract_json_object(
                stdout
            )

        except Exception as exc:

            last_error = str(
                exc
            )

            continue

        if proposal.get(
            "operation"
        ) != "replace_text":

            last_error = (
                "Unsupported mutation operation: "
                + str(
                    proposal.get(
                        "operation"
                    )
                )
            )

            continue

        target = proposal.get(
            "target",
            ""
        )

        replacement = proposal.get(
            "replacement",
            ""
        )

        if not isinstance(
            target,
            str
        ) or not target:

            last_error = (
                "Mutation target is empty."
            )

            continue

        if not isinstance(
            replacement,
            str
        ):

            last_error = (
                "Mutation replacement is not text."
            )

            continue

        if target == replacement:

            last_error = (
                "Mutation is identical."
            )

            continue

        occurrences = function_source.count(
            target
        )

        if occurrences != 1:

            _looks_like_test_data = any(
                isinstance(_f, dict)
                and (
                    target == _f.get("input")
                    or target == _f.get("expected")
                    or target == _f.get("actual")
                )
                for _f in failures
            )

            if _looks_like_test_data:

                last_error = (
                    "Rejected: target matches a test input/expected/"
                    "actual value from PARENT FAILURES, not real "
                    "source code. You must edit the FUNCTION SOURCE, "
                    "not hardcode this specific test case's input or "
                    "output as a literal string replacement."
                )

            else:

                last_error = (
                    "Mutation target must occur exactly "
                    f"once in the function source; found "
                    f"{occurrences}. Copy 'target' verbatim from "
                    "the CURRENT FUNCTION block."
                )

            continue

        mutated_function = (
            function_source.replace(
                target,
                replacement,
                1
            )
        )

        if mutated_function == function_source:

            last_error = (
                "Mutation produced no source change."
            )

            continue

        # ----------------------------------------------------
        # Static guard: reject destructive slicing patterns.
        #
        # The model repeatedly proposes truncating slices such as
        # [:2], [:-1], [2:] to force a failing test to pass instead
        # of fixing the actual semantic defect. This is checked
        # programmatically rather than trusted to the prompt, since
        # the prompt instruction alone has proven insufficient.
        # ----------------------------------------------------

        _FORBIDDEN_SLICE_PATTERNS = (
            r"\[\s*:\s*-?\d+\s*\]",   # [:N] or [:-N]
            r"\[\s*-?\d+\s*:\s*\]",   # [N:] or [-N:]
        )

        _slice_hit = None

        for _pattern in _FORBIDDEN_SLICE_PATTERNS:

            if re.search(_pattern, replacement):
                _slice_hit = _pattern
                break

        if _slice_hit is not None:

            last_error = (
                "Rejected: replacement contains a destructive "
                "truncating slice (matched pattern "
                f"{_slice_hit!r}). Do not limit, truncate, or "
                "discard tokens to make a test pass. Fix the "
                "actual formatting/semantic defect instead."
            )

            continue

        # ----------------------------------------------------
        # Reconstruct only the target function.
        # ----------------------------------------------------

        start = (
            function_node.lineno - 1
        )

        end = (
            function_node.end_lineno
        )

        lines = source.splitlines(
            keepends=True
        )

        candidate_lines = (

            lines[:start]

            + mutated_function.splitlines(
                keepends=True
            )

            + lines[end:]
        )

        candidate_source = "".join(
            candidate_lines
        )

        # ----------------------------------------------------
        # Candidate syntax.
        # ----------------------------------------------------

        try:

            ast.parse(
                candidate_source
            )

        except SyntaxError as exc:

            last_error = (
                "Candidate syntax error: "
                + str(exc)
            )

            continue

        # ----------------------------------------------------
        # Verify target function still exists.
        # ----------------------------------------------------

        try:

            candidate_tree = ast.parse(
                candidate_source
            )

        except Exception as exc:

            last_error = (
                "Candidate parse error: "
                + str(exc)
            )

            continue

        candidate_function = _find_function(
            candidate_tree,
            function_name
        )

        if candidate_function is None:

            last_error = (
                "Mutation removed target function."
            )

            continue

        print(
            f"✅ Structured mutation generated "
            f"on internal attempt {attempt}"
        )

        reason = proposal.get(
            "reason",
            ""
        )

        if reason:

            print(
                "Mutation reason:",
                reason
            )

        return candidate_source

    raise RuntimeError(
        "Structured mutation generation failed "
        f"after {DEFAULT_GENERATION_RETRIES} attempts. "
        f"Last error: {last_error}"
    )


# ============================================================
# FEEDBACK BUILDER
# ============================================================

def build_feedback(
    parent_eval: dict,
    candidate_eval: dict,
    rejected_diff: str = None
):
    """
    Convert evaluator evidence into concrete feedback
    for the next mutation candidate.

    Includes the actual rejected diff so the model sees
    exactly which transformation already failed, instead
    of only an abstract failure list.
    """

    parent_score = parent_eval.get(
        "score",
        -1
    )

    candidate_score = candidate_eval.get(
        "score",
        -1
    )

    failures = candidate_eval.get(
        "failures",
        []
    )

    diff_section = (
        f"Exact rejected transformation (do NOT reproduce this):\n"
        f"{rejected_diff}\n"
        if rejected_diff else ""
    )

    return (
        "Previous candidate was rejected.\n"
        f"Parent score: "
        f"{parent_score}/"
        f"{parent_eval.get('total', '?')}\n"
        f"Candidate score: "
        f"{candidate_score}/"
        f"{candidate_eval.get('total', '?')}\n"
        "Candidate failures:\n"
        f"{json.dumps(
            failures,
            ensure_ascii=False,
            indent=2
        )}\n"
        "\n"
        f"{diff_section}"
        "Do NOT repeat the previous mutation.\n"
        "Preserve all previously passing cases.\n"
        "Find a genuinely different semantic correction, not a "
        "cosmetic variant of the rejected one."
    )


# ============================================================
# MAIN EVOLUTION CYCLE
# ============================================================

def main():

    if len(sys.argv) < 3:

        print(
            'Usage: python evolution_engine.py '
            '"target.py" "evaluator.py" '
            '"improvement task"'
        )

        return 1

    target = Path(
        sys.argv[1]
    ).resolve()

    evaluator = Path(
        sys.argv[2]
    ).resolve()

    task = " ".join(
        sys.argv[3:]
    )

    if not target.exists():

        print(
            f"Target not found: {target}"
        )

        return 2

    if not evaluator.exists():

        print(
            f"Evaluator not found: {evaluator}"
        )

        return 2

    # ========================================================
    # RUN DIRECTORY
    # ========================================================

    run_id = str(
        time.time_ns()
    )

    run_dir = (
        WORKSPACE
        / run_id
    )

    run_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    # ========================================================
    # PROTECTED PARENT COPY
    # ========================================================

    parent = (
        run_dir
        / "parent.py"
    )

    shutil.copy2(
        target,
        parent
    )

    parent_hash = sha256_file(
        parent
    )

    # ========================================================
    # HEADER
    # ========================================================

    print(
        "========================================"
    )

    print(
        "      BEE5 TRUE EVOLUTION CYCLE"
    )

    print(
        "========================================"
    )

    print(
        f"Run ID      : {run_id}"
    )

    print(
        f"Parent hash : {parent_hash}"
    )

    print(
        f"Target      : {target}"
    )

    print(
        f"Evaluator   : {evaluator}"
    )

    # ========================================================
    # PARENT EVALUATION
    # ========================================================

    print(
        "\n===== PARENT EVALUATION ====="
    )

    parent_eval = evaluate(
        parent,
        evaluator
    )

    print(
        json.dumps(
            parent_eval,
            ensure_ascii=False,
            indent=2
        )
    )

    parent_score = parent_eval.get(
        "score",
        -1
    )

    parent_total = parent_eval.get(
        "total",
        None
    )

    # ========================================================
    # PARENT MUST BE EVALUABLE
    # ========================================================

    if parent_score < 0:

        print(
            "\n❌ Parent evaluation is invalid."
        )

        destination = (
            REJECTED
            / run_id
        )

        destination.mkdir(
            parents=True,
            exist_ok=True
        )

        (
            destination
            / "parent_evaluation.json"
        ).write_text(
            json.dumps(
                parent_eval,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )

        return 5

    # ========================================================
    # MUTATION ROUND CONFIG
    # ========================================================

    max_rounds = int(
        os.environ.get(
            "BEE5_MAX_MUTATION_ROUNDS",
            str(DEFAULT_MUTATION_ROUNDS)
        )
    )

    if max_rounds < 1:
        max_rounds = 1

    # ========================================================
    # BUILD DETERMINISTIC CANDIDATE
    # ========================================================

    rounds = []

    try:

        source = parent.read_text(
            encoding="utf-8"
        )

        tree = ast.parse(
            source
        )

        function_node = _find_function(
            tree
        )

        if function_node is not None:

            deterministic_source = (
                build_deterministic_candidate(
                    source,
                    function_node
                )
            )

        else:

            deterministic_source = None

    except Exception as exc:

        deterministic_source = None

        print(
            "⚠️ Deterministic operator skipped:",
            exc
        )

    disable_deterministic = (
        os.environ.get(
            "BEE5_DISABLE_DETERMINISTIC",
            "0"
        ) == "1"
    )

    if deterministic_source and not disable_deterministic:

        rounds.append(
            (
                "deterministic-1",
                deterministic_source
            )
        )

    # ========================================================
    # LLM ROUNDS
    # ========================================================

    for i in range(
        1,
        max_rounds + 1
    ):

        rounds.append(
            (
                f"llm-{i}",
                None
            )
        )

    # ========================================================
    # ATTEMPT LOOP
    # ========================================================

    attempted_log = []

    feedback = None

    accepted_round = None
    accepted_source = None
    accepted_eval = None

    for label, precomputed_source in rounds:

        print(
            f"\n===== ATTEMPT: {label} ====="
        )

        # ----------------------------------------------------
        # Generate candidate
        # ----------------------------------------------------

        if precomputed_source is not None:

            candidate_source = (
                precomputed_source
            )

            print(
                "Candidate source: "
                "deterministic operator"
            )

        else:

            try:

                candidate_source = generate_mutation(
                    parent,
                    task,
                    parent_eval,
                    extra_feedback=feedback
                )

            except Exception as exc:

                print(
                    f"❌ Mutation generation failed "
                    f"({label}): {exc}"
                )

                attempted_log.append(
                    {
                        "round": label,
                        "stage": "generation",
                        "error": str(exc)
                    }
                )

                continue

        # ----------------------------------------------------
        # Candidate path
        # ----------------------------------------------------

        candidate_path = (
            run_dir
            / f"candidate_{label}.py"
        )

        candidate_path.write_text(
            candidate_source,
            encoding="utf-8"
        )

        # ----------------------------------------------------
        # Diff
        # ----------------------------------------------------

        diff = make_diff(
            parent,
            candidate_path
        )

        if not diff.strip():

            print(
                f"❌ REJECTED ({label}): "
                "candidate identical to parent."
            )

            attempted_log.append(
                {
                    "round": label,
                    "stage": "diff",
                    "error": (
                        "identical to parent"
                    )
                }
            )

            continue

        # ----------------------------------------------------
        # Syntax
        # ----------------------------------------------------

        try:

            syntax = syntax_check(
                candidate_path
            )

        except Exception as exc:

            syntax = {
                "ok": False,
                "error": repr(exc)
            }

        if not syntax.get(
            "ok"
        ):

            print(
                f"❌ REJECTED ({label}): "
                f"syntax failure: "
                f"{syntax.get('error')}"
            )

            attempted_log.append(
                {
                    "round": label,
                    "stage": "syntax",
                    "error": syntax.get(
                        "error"
                    )
                }
            )

            feedback = (
                "Previous mutation produced invalid "
                "Python.\n"
                f"Error: {syntax.get('error')}\n"
                "Produce valid Python."
            )

            continue

        # ----------------------------------------------------
        # Candidate evaluation
        # ----------------------------------------------------

        candidate_eval = evaluate(
            candidate_path,
            evaluator
        )

        candidate_score = candidate_eval.get(
            "score",
            -1
        )

        print(
            json.dumps(
                candidate_eval,
                ensure_ascii=False,
                indent=2
            )
        )

        # ----------------------------------------------------
        # STRICT IMPROVEMENT
        # ----------------------------------------------------

        improved = (

            candidate_eval.get(
                "ok"
            )

            and candidate_score
            > parent_score
        )

        attempted_log.append(
            {
                "round": label,
                "stage": "evaluated",
                "score": candidate_score,
                "total": candidate_eval.get(
                    "total"
                ),
                "ok": candidate_eval.get(
                    "ok"
                ),
                "failures": candidate_eval.get(
                    "failures",
                    []
                ),
            }
        )

        if improved:

            accepted_round = label

            accepted_source = (
                candidate_source
            )

            accepted_eval = (
                candidate_eval
            )

            print(
                "\n✅ GENUINE IMPROVEMENT FOUND"
            )

            print(
                f"Score: "
                f"{parent_score}"
                f"/"
                f"{parent_total}"
                " -> "
                f"{candidate_score}"
                f"/"
                f"{candidate_eval.get('total')}"
            )

            break

        # ----------------------------------------------------
        # REJECTION FEEDBACK
        # ----------------------------------------------------

        feedback = build_feedback(
            parent_eval,
            candidate_eval,
            diff
        )

        print(
            f"⚠️ {label} rejected."
        )

        print(
            f"Score remained/became "
            f"{candidate_score}"
            f"/"
            f"{candidate_eval.get('total', '?')}"
        )

        print(
            "➡️ Feeding evaluator evidence "
            "into next mutation."
        )

    # ========================================================
    # NO WINNER
    # ========================================================

    if accepted_round is None:

        destination = (
            REJECTED
            / run_id
        )

        destination.mkdir(
            parents=True,
            exist_ok=True
        )

        (
            destination
            / "attempts.json"
        ).write_text(
            json.dumps(
                attempted_log,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )

        (
            destination
            / "parent_evaluation.json"
        ).write_text(
            json.dumps(
                parent_eval,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )

        (
            destination
            / "parent.py"
        ).write_text(
            parent.read_text(
                encoding="utf-8"
            ),
            encoding="utf-8"
        )

        print(
            "\n========================================"
        )

        print(
            "❌ MUTATION REJECTED"
        )

        print(
            "========================================"
        )

        print(
            "All candidate mutations failed "
            "the strict evaluator gate."
        )

        print(
            f"Attempts tried: "
            f"{len(attempted_log)}"
        )

        print(
            f"Rejected evidence: "
            f"{destination}"
        )

        return 6

    # ========================================================
    # WINNING CANDIDATE
    # ========================================================

    candidate = (
        run_dir
        / "candidate.py"
    )

    candidate.write_text(
        accepted_source,
        encoding="utf-8"
    )

    candidate_hash = sha256_file(
        candidate
    )

    diff = make_diff(
        parent,
        candidate
    )

    diff_path = (
        run_dir
        / "mutation.diff"
    )

    diff_path.write_text(
        diff,
        encoding="utf-8"
    )

    # ========================================================
    # METADATA
    # ========================================================

    metadata = {

        "run_id":
            run_id,

        "accepted_round":
            accepted_round,

        "attempts":
            attempted_log,

        "parent_hash":
            parent_hash,

        "candidate_hash":
            candidate_hash,

        "task":
            task,

        "parent_evaluation":
            parent_eval,

        "candidate_evaluation":
            accepted_eval,

        "accepted":
            True,

        "live_parent_modified":
            False,

        "diff":
            diff,

        "timestamp":
            time.time(),
    }

    # ========================================================
    # ARCHIVE
    # ========================================================

    destination = (
        ARCHIVE
        / candidate_hash
    )

    destination.mkdir(
        parents=True,
        exist_ok=True
    )

    shutil.copy2(
        candidate,
        destination / "candidate.py"
    )

    shutil.copy2(
        parent,
        destination / "parent.py"
    )

    (
        destination
        / "mutation.diff"
    ).write_text(
        diff,
        encoding="utf-8"
    )

    (
        destination
        / "metadata.json"
    ).write_text(
        json.dumps(
            metadata,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    write_jsonl(
        LINEAGE,
        metadata
    )

    # ========================================================
    # SUCCESS
    # ========================================================

    print(
        "\n========================================"
    )

    print(
        "✅ MUTATION ACCEPTED"
    )

    print(
        "========================================"
    )

    print(
        f"Winning round : {accepted_round}"
    )

    print(
        f"Score         : "
        f"{parent_score}"
        f" -> "
        f"{accepted_eval.get('score')}"
    )

    print(
        f"Parent hash   : {parent_hash}"
    )

    print(
        f"Candidate hash: {candidate_hash}"
    )

    print(
        f"Archive       : {destination}"
    )

    print(
        "\n⚠️ LIVE PARENT WAS NOT MODIFIED."
    )

    return 0


# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":

    raise SystemExit(
        main()
    )

