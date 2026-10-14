from __future__ import annotations

from typing import Any

from core.critic import Critic
from core.self_healing import SelfHealingEngine


class CriticRepairEngine:
    """
    Connects independent Critic validation with the existing
    SelfHealingEngine.

    Critic decides which candidates are structurally acceptable.
    SelfHealingEngine performs the actual edit, test, rollback,
    and finalization.
    """

    def __init__(
        self,
        workspace_root: str,
        max_retries: int = 2,
    ):
        self.critic = Critic()
        self.healer = SelfHealingEngine(
            workspace_root,
            max_retries=max_retries,
        )

    def review_candidates(
        self,
        task: str,
        candidates: list[str],
    ) -> dict[str, Any]:

        reviewed: list[dict[str, Any]] = []
        accepted: list[str] = []

        for index, candidate in enumerate(
            candidates,
            start=1,
        ):
            review = self.critic.review(
                task,
                candidate,
            )

            item = {
                "candidate": candidate,
                "review": review,
                "accepted": review.get("passed", False),
            }

            reviewed.append(item)

            if review.get("passed"):
                accepted.append(candidate)

        return {
            "reviewed": reviewed,
            "accepted_candidates": accepted,
            "rejected_count": len(candidates) - len(accepted),
            "accepted_count": len(accepted),
        }

    def repair(
        self,
        task: str,
        relative_path: str,
        old_text: str,
        candidates: list[str],
        test_path: str,
    ) -> dict[str, Any]:

        review_result = self.review_candidates(
            task,
            candidates,
        )

        accepted = review_result[
            "accepted_candidates"
        ]

        if not accepted:
            return {
                "success": False,
                "stage": "critic",
                "error": "Critic rejected all repair candidates.",
                "review": review_result,
            }

        repair_result = self.healer.repair_candidates(
            relative_path=relative_path,
            old_text=old_text,
            candidates=accepted,
            test_path=test_path,
        )

        return {
            "success": repair_result.get(
                "success",
                False,
            ),
            "stage": "repair",
            "review": review_result,
            "repair": repair_result,
        }
