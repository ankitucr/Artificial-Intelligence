from __future__ import annotations

import ast
from typing import Any


class Critic:
    """
    Independent validation layer for Actor output.

    The Critic does not modify the Actor's result.
    It only evaluates it and produces structured feedback.
    """

    def review(
        self,
        task: str,
        output: str,
    ) -> dict[str, Any]:

        issues: list[str] = []
        checks: dict[str, Any] = {}

        text = (output or "").strip()

        checks["non_empty"] = bool(text)

        if not text:
            issues.append(
                "Actor returned empty output."
            )

            return self._result(
                False,
                issues,
                checks,
            )

        # --------------------------------------------------
        # Python syntax
        # --------------------------------------------------

        try:
            tree = ast.parse(text)
            checks["python_syntax"] = True
        except SyntaxError as exc:
            checks["python_syntax"] = False

            issues.append(
                "Python syntax error: "
                f"{exc.msg} "
                f"(line {exc.lineno}, column {exc.offset})"
            )

            return self._result(
                False,
                issues,
                checks,
            )

        # --------------------------------------------------
        # Task-aware function detection
        # --------------------------------------------------

        requested_function = self._extract_function_name(task)

        if requested_function:

            functions = [
                node.name
                for node in ast.walk(tree)
                if isinstance(node, ast.FunctionDef)
            ]

            checks["requested_function"] = (
                requested_function in functions
            )

            if requested_function not in functions:
                issues.append(
                    "Expected Python function "
                    f"'{requested_function}' was not found."
                )

        # --------------------------------------------------
        # Basic unsafe import check
        # --------------------------------------------------

        forbidden_imports = {
            "os.system",
            "subprocess",
            "shutil.rmtree",
        }

        found_forbidden: list[str] = []

        for node in ast.walk(tree):

            if isinstance(node, ast.Call):

                if isinstance(node.func, ast.Attribute):
                    if isinstance(
                        node.func.value,
                        ast.Name,
                    ):
                        name = (
                            f"{node.func.value.id}."
                            f"{node.func.attr}"
                        )

                        if name in forbidden_imports:
                            found_forbidden.append(name)

        checks["forbidden_operations"] = (
            found_forbidden
        )

        if found_forbidden:
            issues.append(
                "Forbidden operation detected: "
                + ", ".join(found_forbidden)
            )

        passed = not issues

        return self._result(
            passed,
            issues,
            checks,
        )

    @staticmethod
    def _extract_function_name(
        task: str,
    ) -> str | None:

        text = task or ""

        marker = "function named "

        if marker in text.lower():

            lower = text.lower()
            index = lower.find(marker)

            remainder = text[
                index + len(marker):
            ]

            name = ""

            for char in remainder:

                if (
                    char.isalnum()
                    or char == "_"
                ):
                    name += char
                else:
                    break

            return name or None

        return None

    @staticmethod
    def _result(
        passed: bool,
        issues: list[str],
        checks: dict[str, Any],
    ) -> dict[str, Any]:

        return {
            "passed": passed,
            "score": 1.0 if passed else 0.0,
            "issues": issues,
            "checks": checks,
            "feedback": (
                "Output passed independent Critic review."
                if passed
                else "Actor output requires correction."
            ),
        }
