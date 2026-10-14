from __future__ import annotations

import ast
import json
import math
import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Optional


# ============================================================
# CONFIGURATION
# ============================================================

TOOLS_DIR = Path("neurons/tools")
CANDIDATE_DIR = TOOLS_DIR / "candidates"
ARCHIVE_DIR = TOOLS_DIR / "archive"

TOOLS_DIR.mkdir(parents=True, exist_ok=True)
CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)


MAX_TOOL_TIME = 0.75
MAX_OUTPUT_BYTES = 32_000

MIN_PROMOTE_SCORE = 0.62
PROMOTION_MARGIN = 0.03

FITNESS_DECAY = 0.10
FITNESS_REWARD = 0.08


# ============================================================
# RESULT OBJECT
# ============================================================

@dataclass
class EvaluationResult:
    status: str
    score: float
    latency_ms: float
    output_valid: bool
    deterministic: bool
    error: Optional[str] = None
    result: Any = None

    def to_dict(self):
        return asdict(self)


# ============================================================
# SAFE-ish GENERATED CODE VALIDATION
# ============================================================

class StaticValidator:

    BLOCKED_IMPORTS = {
        "os",
        "sys",
        "subprocess",
        "socket",
        "ctypes",
        "multiprocessing",
        "threading",
        "asyncio",
        "shutil",
        "pathlib",
        "importlib",
        "pickle",
        "marshal",
    }

    BLOCKED_CALLS = {
        "eval",
        "exec",
        "compile",
        "__import__",
        "open",
    }

    def validate(self, code: str):
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, f"SyntaxError: {e}"

        found_execute = False

        for node in ast.walk(tree):

            # imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]

                    if root in self.BLOCKED_IMPORTS:
                        return False, f"Blocked import: {root}"

            if isinstance(node, ast.ImportFrom):
                if node.module:
                    root = node.module.split(".")[0]

                    if root in self.BLOCKED_IMPORTS:
                        return False, f"Blocked import: {root}"

            # dangerous builtins
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.BLOCKED_CALLS:
                        return False, f"Blocked call: {node.func.id}"

            # execute function
            if isinstance(node, ast.FunctionDef):
                if node.name == "execute":
                    found_execute = True

        if not found_execute:
            return False, "Missing execute(state) function"

        return True, "OK"


# ============================================================
# PROCESS SANDBOX
# ============================================================

class ProcessSandbox:
    """
    Thread sandbox ki jagah PROCESS use karta hai.

    Process timeout hone par terminate/kill kiya ja sakta hai.
    """

    def __init__(self, timeout=MAX_TOOL_TIME):
        self.timeout = timeout

    def run(
        self,
        tool_path: str,
        state: Dict[str, Any],
    ) -> EvaluationResult:

        runner = self._create_runner()

        start = time.perf_counter()

        try:
            proc = subprocess.Popen(
                [
                    sys.executable,
                    str(runner),
                    str(tool_path),
                    json.dumps(state, ensure_ascii=False),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                text=True,
            )

            try:
                stdout, stderr = proc.communicate(
                    timeout=self.timeout
                )

            except subprocess.TimeoutExpired:

                proc.kill()

                stdout, stderr = proc.communicate()

                latency = (
                    time.perf_counter() - start
                ) * 1000

                return EvaluationResult(
                    status="TIMEOUT",
                    score=0.0,
                    latency_ms=latency,
                    output_valid=False,
                    deterministic=False,
                    error="Tool exceeded timeout",
                )

            latency = (
                time.perf_counter() - start
            ) * 1000

            if proc.returncode != 0:

                return EvaluationResult(
                    status="CRASH",
                    score=0.0,
                    latency_ms=latency,
                    output_valid=False,
                    deterministic=False,
                    error=stderr[-4000:],
                )

            if len(stdout.encode("utf-8")) > MAX_OUTPUT_BYTES:

                return EvaluationResult(
                    status="OUTPUT_LIMIT",
                    score=0.0,
                    latency_ms=latency,
                    output_valid=False,
                    deterministic=False,
                    error="Output exceeded limit",
                )

            try:
                payload = json.loads(stdout)

            except json.JSONDecodeError:

                return EvaluationResult(
                    status="INVALID_OUTPUT",
                    score=0.0,
                    latency_ms=latency,
                    output_valid=False,
                    deterministic=False,
                    error="Tool did not return valid JSON",
                )

            return EvaluationResult(
                status="SUCCESS",
                score=1.0,
                latency_ms=latency,
                output_valid=True,
                deterministic=True,
                result=payload,
            )

        except Exception:

            return EvaluationResult(
                status="SANDBOX_ERROR",
                score=0.0,
                latency_ms=0,
                output_valid=False,
                deterministic=False,
                error=traceback.format_exc(),
            )

        finally:

            try:
                runner.unlink()
            except Exception:
                pass

    def _create_runner(self):

        fd, path = tempfile.mkstemp(
            prefix="brain_runner_",
            suffix=".py",
        )

        os.close(fd)

        code = r'''
import json
import sys
import importlib.util


def main():

    tool_path = sys.argv[1]
    state = json.loads(sys.argv[2])

    spec = importlib.util.spec_from_file_location(
        "candidate_tool",
        tool_path
    )

    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    result = module.execute(state)

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            default=str
        )
    )


if __name__ == "__main__":
    main()
'''

        with open(path, "w", encoding="utf-8") as f:
            f.write(code)

        return Path(path)


# ============================================================
# TOOL RECORD
# ============================================================

@dataclass
class ToolRecord:

    name: str
    path: str

    fitness: float = 0.50
    evaluations: int = 0
    successes: int = 0
    failures: int = 0

    generation_created: int = 0

    parent: Optional[str] = None

    promoted: bool = False


# ============================================================
# EVOLUTION ENGINE
# ============================================================

class SelfEvaluatingEvolutionEngine:

    def __init__(self, brain_reference):

        self.brain = brain_reference

        self.validator = StaticValidator()
        self.sandbox = ProcessSandbox()

        self.tools: Dict[str, ToolRecord] = {}

        self.best_tool: Optional[str] = None

        self.mutation_queue = queue.Queue()

        self.lock = threading.RLock()

        self.is_evolving = False

        self.total_candidates = 0
        self.total_promoted = 0
        self.total_rejected = 0

        self.history = []

        self.worker = threading.Thread(
            target=self._worker_loop,
            daemon=True,
            name="EvolutionWorker",
        )

        self.worker.start()

        print(
            "[EVOLUTION] Self-evaluating engine online"
        )

    # ========================================================
    # REQUEST MUTATION
    # ========================================================

    def request_mutation(
        self,
        issue_description: str,
        state_context: Dict[str, Any],
    ):

        with self.lock:

            self.mutation_queue.put(
                (
                    issue_description,
                    state_context,
                )
            )

            print(
                f"[EVOLUTION] Mutation queued: "
                f"{issue_description}"
            )

    # ========================================================
    # WORKER
    # ========================================================

    def _worker_loop(self):

        while True:

            issue, context = self.mutation_queue.get()

            try:

                self.is_evolving = True

                self._process_mutation(
                    issue,
                    context,
                )

            except Exception:

                print(
                    "[EVOLUTION] Worker failure:"
                )

                traceback.print_exc()

            finally:

                self.is_evolving = False

                self.mutation_queue.task_done()

    # ========================================================
    # MUTATION PIPELINE
    # ========================================================

    def _process_mutation(
        self,
        issue,
        context,
    ):

        print(
            f"[EVOLUTION] Analysing issue: {issue}"
        )

        compressed = self._compress_context(
            context
        )

        # ----------------------------------------------------
        # LLM GENERATION
        # ----------------------------------------------------

        code = self._generate_candidate(
            issue,
            compressed,
        )

        if not code:

            print(
                "[EVOLUTION] Candidate generation failed"
            )

            return

        self.total_candidates += 1

        candidate_name = (
            f"candidate_g"
            f"{getattr(self.brain, 'generation', 0)}_"
            f"{self.total_candidates}"
        )

        candidate_path = (
            CANDIDATE_DIR /
            f"{candidate_name}.py"
        )

        candidate_path.write_text(
            code,
            encoding="utf-8",
        )

        print(
            f"[EVOLUTION] Candidate created: "
            f"{candidate_name}"
        )

        # ----------------------------------------------------
        # STATIC VALIDATION
        # ----------------------------------------------------

        valid, reason = self.validator.validate(
            code
        )

        if not valid:

            print(
                f"[EVOLUTION] REJECTED static: "
                f"{reason}"
            )

            self.total_rejected += 1

            return

        # ----------------------------------------------------
        # BASELINE
        # ----------------------------------------------------

        baseline_score = 0.0

        if self.best_tool:

            baseline_score = self._evaluate_tool(
                self.tools[self.best_tool],
                context,
            )

        # ----------------------------------------------------
        # CANDIDATE EVALUATION
        # ----------------------------------------------------

        candidate_score = (
            self._evaluate_candidate(
                candidate_path,
                context,
            )
        )

        print(
            f"[EVOLUTION] Candidate score="
            f"{candidate_score:.3f} | "
            f"baseline={baseline_score:.3f}"
        )

        # ----------------------------------------------------
        # PROMOTION DECISION
        # ----------------------------------------------------

        if self._should_promote(
            candidate_score,
            baseline_score,
        ):

            self._promote_candidate(
                candidate_name,
                candidate_path,
                candidate_score,
            )

        else:

            self._reject_candidate(
                candidate_name,
                candidate_path,
                candidate_score,
                baseline_score,
            )

    # ========================================================
    # CANDIDATE EVALUATION
    # ========================================================

    def _evaluate_candidate(
        self,
        path: Path,
        state,
    ) -> float:

        scores = []

        # Same state multiple times.
        # This tests repeatability.

        for i in range(3):

            result = self.sandbox.run(
                str(path),
                state,
            )

            score = self._score_result(
                result
            )

            scores.append(score)

            if result.status != "SUCCESS":

                break

        if not scores:
            return 0.0

        average = sum(scores) / len(scores)

        # ----------------------------------------------------
        # DETERMINISM
        # ----------------------------------------------------

        if len(scores) == 3:

            spread = max(scores) - min(scores)

            if spread > 0.20:
                average *= 0.80

        # ----------------------------------------------------
        # REGRESSION
        # ----------------------------------------------------

        regression = self._regression_test(
            path,
            state,
        )

        average = (
            average * 0.70 +
            regression * 0.30
        )

        return max(
            0.0,
            min(1.0, average)
        )

    # ========================================================
    # RESULT SCORING
    # ========================================================

    def _score_result(
        self,
        result: EvaluationResult,
    ) -> float:

        if result.status != "SUCCESS":
            return 0.0

        score = 0.50

        # Output validity
        if result.output_valid:
            score += 0.20

        # Latency
        if result.latency_ms < 50:
            score += 0.20

        elif result.latency_ms < 150:
            score += 0.10

        elif result.latency_ms > 500:
            score -= 0.15

        # Result should not be None
        if result.result is not None:
            score += 0.10

        return max(
            0.0,
            min(1.0, score)
        )

    # ========================================================
    # REGRESSION TEST
    # ========================================================

    def _regression_test(
        self,
        path: Path,
        original_state,
    ) -> float:

        states = self._build_test_states(
            original_state
        )

        results = []

        for state in states:

            result = self.sandbox.run(
                str(path),
                state,
            )

            if result.status == "SUCCESS":
                results.append(
                    self._score_result(result)
                )
            else:
                results.append(0.0)

        if not results:
            return 0.0

        return sum(results) / len(results)

    # ========================================================
    # TEST STATES
    # ========================================================

    def _build_test_states(
        self,
        state,
    ):

        base = dict(state)

        tests = [
            base,
            dict(base),
            {},
        ]

        # Perturb numeric sensor values

        perturbed = {}

        for key, value in base.items():

            if isinstance(value, (int, float)):

                perturbed[key] = value * 1.05

            else:

                perturbed[key] = value

        tests.append(perturbed)

        return tests

    # ========================================================
    # PROMOTION
    # ========================================================

    def _should_promote(
        self,
        candidate_score,
        baseline_score,
    ):

        if candidate_score < MIN_PROMOTE_SCORE:
            return False

        if self.best_tool is None:
            return True

        return (
            candidate_score >=
            baseline_score + PROMOTION_MARGIN
        )

    # ========================================================
    # PROMOTE
    # ========================================================

    def _promote_candidate(
        self,
        name,
        path,
        score,
    ):

        final_path = (
            TOOLS_DIR /
            f"{name}.py"
        )

        shutil.copy2(
            path,
            final_path,
        )

        parent = self.best_tool

        # Archive previous best

        if parent:

            old_path = Path(
                self.tools[parent].path
            )

            if old_path.exists():

                archive_path = (
                    ARCHIVE_DIR /
                    f"{parent}.py"
                )

                shutil.copy2(
                    old_path,
                    archive_path,
                )

                self.tools[parent].promoted = False

        record = ToolRecord(
            name=name,
            path=str(final_path),
            fitness=score,
            evaluations=1,
            successes=1,
            failures=0,
            generation_created=getattr(
                self.brain,
                "generation",
                0,
            ),
            parent=parent,
            promoted=True,
        )

        self.tools[name] = record

        self.best_tool = name

        self.total_promoted += 1

        self.history.append(
            {
                "event": "PROMOTED",
                "tool": name,
                "parent": parent,
                "score": score,
                "generation":
                    getattr(
                        self.brain,
                        "generation",
                        0,
                    ),
                "time": time.time(),
            }
        )

        print(
            f"[EVOLUTION] "
            f"✓ PROMOTED {name} "
            f"score={score:.3f}"
        )

    # ========================================================
    # REJECT
    # ========================================================

    def _reject_candidate(
        self,
        name,
        path,
        candidate_score,
        baseline_score,
    ):

        self.total_rejected += 1

        self.history.append(
            {
                "event": "REJECTED",
                "tool": name,
                "candidate_score":
                    candidate_score,
                "baseline_score":
                    baseline_score,
                "time": time.time(),
            }
        )

        print(
            f"[EVOLUTION] "
            f"✗ REJECTED {name} "
            f"candidate={candidate_score:.3f} "
            f"baseline={baseline_score:.3f}"
        )

    # ========================================================
    # LIVE TOOL EVALUATION
    # ========================================================

    def evaluate_tools(
        self,
        current_state,
    ):

        with self.lock:

            if not self.best_tool:

                return None

            record = self.tools.get(
                self.best_tool
            )

            if not record:

                return None

            result = self.sandbox.run(
                record.path,
                current_state,
            )

            record.evaluations += 1

            if result.status == "SUCCESS":

                record.successes += 1

                reward = self._score_result(
                    result
                )

                record.fitness = min(
                    1.0,
                    record.fitness +
                    FITNESS_REWARD *
                    reward
                )

                return result.result

            # ------------------------------------------------
            # FAILURE
            # ------------------------------------------------

            record.failures += 1

            record.fitness = max(
                0.0,
                record.fitness -
                FITNESS_DECAY
            )

            print(
                f"[EVOLUTION] "
                f"Tool failure: "
                f"{result.status}"
            )

            # ------------------------------------------------
            # AUTO PRUNE
            # ------------------------------------------------

            if record.fitness < 0.15:

                self._prune_tool(
                    self.best_tool
                )

            return None

    # ========================================================
    # PRUNING
    # ========================================================

    def _prune_tool(self, name):

        record = self.tools.pop(
            name,
            None
        )

        if not record:
            return

        try:
            Path(
                record.path
            ).unlink(
                missing_ok=True
            )
        except Exception:
            pass

        if self.best_tool == name:

            self.best_tool = None

        print(
            f"[EVOLUTION] "
            f"PRUNED weak tool: {name}"
        )

    # ========================================================
    # CONTEXT COMPRESSION
    # ========================================================

    def _compress_context(
        self,
        context,
    ):

        if not isinstance(
            context,
            dict
        ):
            return context

        compressed = {}

        for key, value in list(
            context.items()
        )[:100]:

            if isinstance(
                value,
                (int, float, str, bool)
            ):
                compressed[key] = value

        return compressed

    # ========================================================
    # LLM GENERATION
    # ========================================================

    def _generate_candidate(
        self,
        issue,
        context,
    ):

        """
        Yahan actual Ollama / DeepSeek / local model
        integrate karna hai.

        Filhaal intentionally deterministic candidate.
        """

        return '''
def execute(state):
    """
    Candidate tool.
    Must return JSON-serializable data.
    """

    numeric = []

    for key, value in state.items():

        if isinstance(value, (int, float)):

            numeric.append(float(value))

    if not numeric:

        return {
            "action": "observe",
            "confidence": 0.10,
            "reason": "no_numeric_sensor_data"
        }

    magnitude = sum(
        abs(x) for x in numeric
    ) / max(1, len(numeric))

    if magnitude > 5.0:

        action = "observe_high_activity"

    else:

        action = "observe_stable"

    return {
        "action": action,
        "confidence": min(
            1.0,
            magnitude / 10.0
        ),
        "sensor_magnitude": magnitude
    }
'''

    # ========================================================
    # STATUS
    # ========================================================

    def status(self):

        with self.lock:

            tools = []

            for record in self.tools.values():

                tools.append(
                    {
                        **asdict(record)
                    }
                )

            return {
                "best_tool":
                    self.best_tool,

                "total_candidates":
                    self.total_candidates,

                "total_promoted":
                    self.total_promoted,

                "total_rejected":
                    self.total_rejected,

                "tools":
                    tools,

                "history":
                    self.history[-20:],
            }

    # ========================================================
    # SAVE EVOLUTION STATE
    # ========================================================

    def save_state(
        self,
        filename="neurons/evolution_state.json",
    ):

        data = self.status()

        tmp = (
            filename +
            ".tmp"
        )

        with open(
            tmp,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                data,
                f,
                indent=2,
                ensure_ascii=False,
            )

        os.replace(
            tmp,
            filename,
        )

        print(
            f"[EVOLUTION] "
            f"State saved: {filename}"
        )
