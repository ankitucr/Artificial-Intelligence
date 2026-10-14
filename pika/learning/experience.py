from datetime import datetime, timezone
from typing import Any


class ExperienceEngine:

    def create_experience(
        self,
        task: str,
        result: dict[str, Any],
        evaluation: dict[str, Any],
        decision: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        passed = bool(evaluation.get("passed"))
        decision = decision or {}

        lesson = self._derive_lesson(
            task=task,
            result=result,
            evaluation=evaluation,
            decision=decision,
        )

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task": task,
            "result": result,
            "evaluation": evaluation,
            "decision": decision,
            "strategy": decision.get("mode"),
            "task_signature": decision.get("task_signature"),
            "outcome": "success" if passed else "failure",
            "lesson": lesson,
        }

    @staticmethod
    def _derive_lesson(
        task: str,
        result: dict[str, Any],
        evaluation: dict[str, Any],
        decision: dict[str, Any],
    ) -> dict[str, Any]:

        passed = bool(evaluation.get("passed"))
        mode = decision.get("mode", "unknown")
        signature = decision.get("task_signature", "unknown")

        if passed:
            return {
                "type": "success",
                "task": task,
                "task_signature": signature,
                "strategy": mode,
                "rule": (
                    f"Strategy '{mode}' successfully solved "
                    f"task signature '{signature}'."
                ),
            }

        issues = evaluation.get("issues", [])

        return {
            "type": "failure",
            "task": task,
            "task_signature": signature,
            "strategy": mode,
            "issues": issues,
            "rule": (
                f"Strategy '{mode}' failed for "
                f"task signature '{signature}'. "
                "Avoid repeating the same strategy when the evidence "
                "shows a better alternative."
            ),
        }
