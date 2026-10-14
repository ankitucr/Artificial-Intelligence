from __future__ import annotations

import re
from typing import Any


class ErrorAnalyzer:
    """
    Converts raw execution failures into structured recovery data.

    Dependency detection is generic. No specific package is required
    by the analyzer.
    """

    DEPENDENCY_PATTERNS = (
        "modulenotfounderror",
        "no module named",
        "package is not installed",
        "distribution was not found",
        "could not find a version",
        "no command ",
        "command not found",
        ": not found",
    )

    CODE_PATTERNS = (
        "syntaxerror",
        "indentationerror",
        "nameerror",
        "typeerror",
        "attributeerror",
        "keyerror",
        "indexerror",
        "valueerror",
        "unboundlocalerror",
        "recursionerror",
    )

    TEST_PATTERNS = (
        "failed",
        "failure",
        "assertionerror",
        "test failed",
        "tests failed",
        "error during collection",
        "traceback",
    )

    CONFIG_PATTERNS = (
        "environment variable",
        "configuration",
        "config",
        ".env",
        "invalid configuration",
        "missing configuration",
    )

    PERMISSION_PATTERNS = (
        "permission denied",
        "operation not permitted",
        "access denied",
    )

    NETWORK_PATTERNS = (
        "connection refused",
        "connection reset",
        "timed out",
        "timeout",
        "dns",
        "name or service not known",
        "network is unreachable",
        "connection error",
    )

    COMMAND_POLICY_PATTERNS = (
        "only 'python -m py_compile'",
        "command is not allowed",
        "command not allowed",
    )

    @staticmethod
    def _text(
        result: dict[str, Any],
    ) -> str:

        pieces: list[str] = []

        def collect(value: Any) -> None:
            if value is None:
                return

            if isinstance(value, dict):
                for key in (
                    "error",
                    "stderr",
                    "stdout",
                    "message",
                ):
                    if key in value:
                        collect(value.get(key))

                for key in (
                    "result",
                    "underlying_result",
                ):
                    if key in value:
                        collect(value.get(key))

            elif isinstance(value, list):
                for item in value:
                    collect(item)

            else:
                pieces.append(str(value))

        collect(result)

        return "\n".join(pieces).lower()

    @staticmethod
    def _extract_package(
        text: str,
    ) -> str | None:

        patterns = (
            r"no module named ['\"]([^'\"]+)['\"]",
            r"no module named ([a-zA-Z0-9_.-]+)",
            r"no command ([a-zA-Z0-9_.-]+) found",
            r"command ([a-zA-Z0-9_.-]+) not found",
            r"\b([a-zA-Z0-9_.-]+): not found\b",
        )

        for pattern in patterns:
            match = re.search(pattern, text)

            if match:
                package = match.group(1).strip()

                if package:
                    return package.split(".")[0]

        return None

    @staticmethod
    def _contains_any(
        text: str,
        patterns: tuple[str, ...],
    ) -> bool:

        return any(
            pattern in text
            for pattern in patterns
        )

    def analyze(
        self,
        result: dict[str, Any],
    ) -> dict[str, Any]:

        text = self._text(result)

        if not text:
            return {
                "success": True,
                "error_type": "unknown",
                "confidence": 0.0,
                "root_cause": (
                    "No error information available."
                ),
                "recommended_action": "inspect_result",
                "retry_allowed": False,
            }

        if self._contains_any(
            text,
            self.COMMAND_POLICY_PATTERNS,
        ):
            return {
                "success": True,
                "error_type": "command_policy",
                "confidence": 0.99,
                "root_cause": (
                    "The requested command is blocked "
                    "by the workspace execution policy."
                ),
                "recommended_action": (
                    "change_execution_strategy"
                ),
                "retry_allowed": True,
            }

        if self._contains_any(
            text,
            self.DEPENDENCY_PATTERNS,
        ):
            package = self._extract_package(text)

            if package:
                return {
                    "success": True,
                    "error_type": "dependency_missing",
                    "confidence": 0.97,
                    "package": package,
                    "root_cause": (
                        "A required software dependency "
                        "appears to be unavailable."
                    ),
                    "recommended_action": (
                        "install_dependency"
                    ),
                    "retry_allowed": True,
                }

        if self._contains_any(
            text,
            self.PERMISSION_PATTERNS,
        ):
            return {
                "success": True,
                "error_type": "permission_error",
                "confidence": 0.96,
                "root_cause": (
                    "The operation does not have "
                    "sufficient permissions."
                ),
                "recommended_action": (
                    "inspect_permissions"
                ),
                "retry_allowed": True,
            }

        if self._contains_any(
            text,
            self.NETWORK_PATTERNS,
        ):
            return {
                "success": True,
                "error_type": "network_error",
                "confidence": 0.90,
                "root_cause": (
                    "The operation appears to have "
                    "failed because of a network/runtime "
                    "connection problem."
                ),
                "recommended_action": (
                    "retry_with_backoff"
                ),
                "retry_allowed": True,
            }

        if self._contains_any(
            text,
            self.CONFIG_PATTERNS,
        ):
            return {
                "success": True,
                "error_type": "configuration_error",
                "confidence": 0.88,
                "root_cause": (
                    "The failure appears related to "
                    "configuration or environment settings."
                ),
                "recommended_action": (
                    "repair_configuration"
                ),
                "retry_allowed": True,
            }

        if self._contains_any(
            text,
            self.CODE_PATTERNS,
        ):
            return {
                "success": True,
                "error_type": "code_error",
                "confidence": 0.94,
                "root_cause": (
                    "The program appears to contain "
                    "a runtime or syntax-level code error."
                ),
                "recommended_action": "repair_code",
                "retry_allowed": True,
            }

        if self._contains_any(
            text,
            self.TEST_PATTERNS,
        ):
            return {
                "success": True,
                "error_type": "test_failure",
                "confidence": 0.82,
                "root_cause": (
                    "The implementation did not satisfy "
                    "one or more tests."
                ),
                "recommended_action": (
                    "inspect_test_failure"
                ),
                "retry_allowed": True,
            }

        return {
            "success": True,
            "error_type": "unknown",
            "confidence": 0.40,
            "root_cause": (
                "The error could not be confidently "
                "classified."
            ),
            "recommended_action": "deep_diagnosis",
            "retry_allowed": True,
        }
