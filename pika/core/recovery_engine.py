from __future__ import annotations

from typing import Any


class RecoveryEngine:
    """
    Chooses the next recovery action from an ErrorAnalyzer result.

    This layer decides WHAT should happen.
    The actual action is performed by PIKA tools.
    """

    MAX_AUTOMATIC_RECOVERY_ATTEMPTS = 3

    def decide(
        self,
        diagnosis: dict[str, Any],
        attempt: int,
    ) -> dict[str, Any]:

        error_type = diagnosis.get(
            "error_type",
            "unknown",
        )

        confidence = float(
            diagnosis.get(
                "confidence",
                0.0,
            )
        )

        retry_allowed = bool(
            diagnosis.get(
                "retry_allowed",
                False,
            )
        )

        if attempt >= self.MAX_AUTOMATIC_RECOVERY_ATTEMPTS:
            return {
                "action": "rollback",
                "reason": (
                    "Automatic recovery attempt limit "
                    "has been reached."
                ),
                "confidence": confidence,
            }

        if not retry_allowed:
            return {
                "action": "rollback",
                "reason": (
                    "The error is not considered "
                    "automatically recoverable."
                ),
                "confidence": confidence,
            }

        actions = {
            "dependency_missing": "install_dependency",
            "code_error": "repair_code",
            "test_failure": "repair_code",
            "configuration_error": "repair_configuration",
            "permission_error": "inspect_permissions",
            "network_error": "retry_with_backoff",
            "command_policy": "change_execution_strategy",
            "unknown": "deep_diagnosis",
        }

        action = actions.get(
            error_type,
            "deep_diagnosis",
        )

        return {
            "action": action,
            "reason": diagnosis.get(
                "root_cause",
                "Unknown recovery reason.",
            ),
            "confidence": confidence,
            "attempt": attempt,
        }
