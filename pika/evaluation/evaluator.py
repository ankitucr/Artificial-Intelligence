import ast
import re
from typing import Any


class Evaluator:
    """
    PIKA task-aware evaluator.

    The evaluator validates output according to the task:
      - code-only tasks -> validate extracted code
      - explanation/design tasks -> validate the embedded code when present,
        but do not treat natural-language explanation as Python
      - general tasks -> validate non-empty structured output

    The evaluator never claims that code was executed unless execution
    evidence was actually supplied by the worker.
    """

    def evaluate(
        self,
        result: dict[str, Any],
        task: str = "",
    ) -> dict[str, Any]:

        worker_success = bool(result.get("success"))
        output = str(result.get("output") or "").strip()

        issues: list[str] = []
        checks: dict[str, Any] = {}

        checks["worker_success"] = worker_success

        if not worker_success:
            error = result.get("error") or "Worker reported failure."
            issues.append(str(error))

            return {
                "passed": False,
                "score": 0.0,
                "reason": "Worker execution failed.",
                "issues": issues,
                "checks": checks,
                "feedback": (
                    "The worker failed before producing a usable result. "
                    f"Worker error: {error}"
                ),
                "normalized_output": output,
            }

        if not output:
            issues.append("Worker returned empty output.")

            return {
                "passed": False,
                "score": 0.0,
                "reason": "Empty worker output.",
                "issues": issues,
                "checks": checks,
                "feedback": "Return a complete usable answer.",
                "normalized_output": "",
            }

        # ---------------------------------------------------------
        # Task classification
        # ---------------------------------------------------------

        task_lower = task.lower()

        code_task = self._is_code_task(task_lower)
        code_only = self._is_code_only_task(task_lower)

        checks["task_is_code_related"] = code_task
        checks["task_requires_code_only"] = code_only

        # ---------------------------------------------------------
        # Extract / normalize code intelligently
        # ---------------------------------------------------------

        normalized = self._normalize_output(output)

        checks["code_fence_detected"] = self._has_code_fence(output)
        checks["code_extracted"] = normalized != output

        # ---------------------------------------------------------
        # Code validation
        # ---------------------------------------------------------

        if code_task:

            code_to_validate = normalized

            # If this is an explanation/design task, the complete response
            # may contain prose around a fenced code block. Prefer the
            # extracted fenced Python block.
            if not code_only:
                fenced_code = self._extract_python_code(output)

                if fenced_code:
                    code_to_validate = fenced_code
                    checks["embedded_python_extracted"] = True
                else:
                    checks["embedded_python_extracted"] = False

                    # If there is no fenced block, only attempt to parse
                    # the complete output when it appears to be code-only.
                    if not self._looks_like_standalone_python(output):
                        checks["python_syntax"] = "not_applicable"
                        checks["python_validation_mode"] = (
                            "explanation_with_no_extractable_code"
                        )
                        code_to_validate = ""

                        # Non-inline code needs actual successful test evidence.
                        workspace = result.get("workspace_execution")
                        if isinstance(workspace, dict):
                            commands = []

                            def collect_commands(value):
                                if isinstance(value, dict):
                                    command = value.get("command")
                                    if isinstance(command, list) and all(
                                        isinstance(part, str) for part in command
                                    ):
                                        commands.append((command, value))
                                    for child in value.values():
                                        collect_commands(child)
                                elif isinstance(value, list):
                                    for child in value:
                                        collect_commands(child)

                            collect_commands(workspace)

                            def is_test_command(command):
                                lowered = [part.lower() for part in command]
                                joined = " " + " ".join(lowered) + " "
                                return (
                                    "pytest" in lowered
                                    or "unittest" in lowered
                                    or any(
                                        part.startswith("test_")
                                        or part.endswith("_test.py")
                                        or part.endswith("test.py")
                                        for part in lowered
                                    )
                                    or " -m pytest " in joined
                                    or " -m unittest " in joined
                                )

                            successful_tests = [
                                (command, record)
                                for command, record in commands
                                if is_test_command(command)
                                and (
                                    record.get("success") is True
                                    or (
                                        isinstance(record.get("result"), dict)
                                        and record["result"].get("success") is True
                                        and record["result"].get("returncode", 0) == 0
                                    )
                                )
                            ]
                            checks["independent_test_evidence"] = bool(
                                workspace.get("success") is True and successful_tests
                            )
                            if not checks["independent_test_evidence"]:
                                issues.append(
                                    "Workspace output contained no extractable Python "
                                    "code and lacked a successful recorded independent "
                                    "test command. Syntax checks alone do not prove "
                                    "task correctness."
                                )
                        else:
                            issues.append(
                                "Code-related task produced no extractable code and "
                                "supplied no verified workspace execution evidence."
                            )
                    else:
                        code_to_validate = output

            if code_to_validate:
                syntax_ok, syntax_error = self._check_python_syntax(
                    code_to_validate
                )

                checks["python_syntax"] = syntax_ok

                if not syntax_ok:
                    issues.append(
                        f"Python syntax validation failed: {syntax_error}"
                    )

            # -----------------------------------------------------
            # Requested function validation
            # -----------------------------------------------------

            function_name = self._extract_requested_function(task)

            if function_name and code_to_validate:
                function_ok = self._contains_function(
                    code_to_validate,
                    function_name,
                )

                checks["requested_function"] = function_ok
                checks["function_name"] = function_name

                if not function_ok:
                    issues.append(
                        f"Expected Python function '{function_name}' "
                        "was not found."
                    )

            elif function_name:
                checks["requested_function"] = "not_applicable"

        # ---------------------------------------------------------
        # General output validation
        # ---------------------------------------------------------

        checks["non_empty"] = bool(output)

        # ---------------------------------------------------------
        # Final result
        # ---------------------------------------------------------

        if issues:

            score = max(
                0.0,
                1.0 - (0.30 * len(issues)),
            )

            return {
                "passed": False,
                "score": round(score, 2),
                "reason": "Output failed one or more validation checks.",
                "issues": issues,
                "checks": checks,
                "feedback": self._build_feedback(issues),
                "normalized_output": normalized,
            }

        return {
            "passed": True,
            "score": 1.0,
            "reason": "Output passed task-aware independent validation.",
            "issues": [],
            "checks": checks,
            "feedback": (
                "Output passed task-aware independent validation."
            ),
            "normalized_output": normalized,
        }

    # =============================================================
    # Task classification
    # =============================================================

    @staticmethod
    def _is_code_task(task_lower: str) -> bool:
        markers = (
            "python",
            "python code",
            "python function",
            "python class",
            "write code",
            "write a function",
            "implement a function",
            "implement code",
            "program",
            "script",
            "def ",
            "class ",
            "async def",
        )

        return any(marker in task_lower for marker in markers)

    @staticmethod
    def _is_code_only_task(task_lower: str) -> bool:
        code_only_markers = (
            "return only the function code",
            "return only code",
            "output only code",
            "code only",
            "return just the code",
            "just the code",
            "only the implementation",
        )

        return any(
            marker in task_lower
            for marker in code_only_markers
        )

    # =============================================================
    # Output normalization
    # =============================================================

    @staticmethod
    def _has_code_fence(output: str) -> bool:
        return "```" in output

    @staticmethod
    def _extract_python_code(output: str) -> str | None:
        patterns = [
            r"```python\s*\n(.*?)```",
            r"```py\s*\n(.*?)```",
            r"```\s*\n(.*?)```",
        ]

        for pattern in patterns:
            match = re.search(
                pattern,
                output,
                flags=re.IGNORECASE | re.DOTALL,
            )

            if match:
                return match.group(1).strip()

        return None

    @classmethod
    def _normalize_output(cls, output: str) -> str:
        text = output.strip()

        extracted = cls._extract_python_code(text)

        if extracted:
            return extracted

        # Handle a response consisting entirely of one code fence even
        # when formatting differs slightly.
        if text.startswith("```") and text.endswith("```"):
            lines = text.splitlines()

            if len(lines) >= 3:
                first = lines[0].strip().lower()

                if first in (
                    "```",
                    "```python",
                    "```py",
                ):
                    return "\n".join(lines[1:-1]).strip()

        return text

    @staticmethod
    def _looks_like_standalone_python(output: str) -> bool:
        stripped = output.strip()

        if not stripped:
            return False

        python_starters = (
            "def ",
            "class ",
            "import ",
            "from ",
            "@",
            "async def ",
        )

        return stripped.startswith(python_starters)

    # =============================================================
    # Python validation
    # =============================================================

    @staticmethod
    def _check_python_syntax(
        code: str,
    ) -> tuple[bool, str | None]:

        try:
            ast.parse(code)
            return True, None

        except SyntaxError as exc:
            location = f"line {exc.lineno}"

            if exc.offset:
                location += f", column {exc.offset}"

            return (
                False,
                f"{exc.msg} ({location})",
            )

        except Exception as exc:
            return False, str(exc)

    # =============================================================
    # Requested function detection
    # =============================================================

    @staticmethod
    def _extract_requested_function(
        task: str,
    ) -> str | None:

        patterns = [
            r"function\s+(?:named\s+)?([A-Za-z_][A-Za-z0-9_]*)",
            r"function\s+called\s+([A-Za-z_][A-Za-z0-9_]*)",
            r"def\s+([A-Za-z_][A-Za-z0-9_]*)",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                task,
                flags=re.IGNORECASE,
            )

            if match:
                return match.group(1)

        return None

    @staticmethod
    def _contains_function(
        code: str,
        function_name: str,
    ) -> bool:

        try:
            tree = ast.parse(code)

        except Exception:
            return False

        for node in ast.walk(tree):

            if isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            ):
                if node.name == function_name:
                    return True

        return False

    # =============================================================
    # Feedback
    # =============================================================

    @staticmethod
    def _build_feedback(
        issues: list[str],
    ) -> str:

        lines = [
            "Fix the following validation problems before retrying:"
        ]

        for issue in issues:
            lines.append(f"- {issue}")

        lines.append(
            "Return the corrected final result without claiming "
            "that untested code was tested."
        )

        return "\n".join(lines)
