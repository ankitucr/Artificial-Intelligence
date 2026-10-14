from __future__ import annotations

from typing import Any

from core.critic import Critic
from core.self_healing import SelfHealingEngine


class MultiCandidateEngine:
    """
    Phase 23:
    Critic-ranked multi-candidate repair engine.

    Candidate generation is external.
    This layer evaluates, ranks, executes and recovers.
    """

    def __init__(
        self,
        workspace_root: str,
        max_candidates: int = 5,
    ):
        self.critic = Critic()
        self.healer = SelfHealingEngine(
            workspace_root,
            max_retries=0,
        )
        self.max_candidates = max(
            1,
            max_candidates,
        )

    def rank_candidates(
        self,
        task: str,
        candidates: list[str],
    ) -> list[dict[str, Any]]:

        ranked: list[dict[str, Any]] = []

        for index, candidate in enumerate(
            candidates,
            start=1,
        ):
            review = self.critic.review(
                task,
                candidate,
            )

            score = float(
                review.get("score", 0.0)
            )

            ranked.append(
                {
                    "original_index": index,
                    "candidate": candidate,
                    "score": score,
                    "critic_passed": bool(
                        review.get("passed")
                    ),
                    "review": review,
                }
            )

        ranked.sort(
            key=lambda item: (
                item["critic_passed"],
                item["score"],
            ),
            reverse=True,
        )

        for rank, item in enumerate(
            ranked,
            start=1,
        ):
            item["rank"] = rank

        return ranked[: self.max_candidates]

    def repair(
        self,
        task: str,
        relative_path: str,
        old_text: str,
        candidates: list[str],
        test_path: str,
    ) -> dict[str, Any]:

        ranked = self.rank_candidates(
            task,
            candidates,
        )

        print()
        print("[PIKA] Critic-ranked candidates:")

        for item in ranked:
            print(
                f"  Rank {item['rank']}: "
                f"candidate #{item['original_index']} "
                f"score={item['score']} "
                f"critic_pass={item['critic_passed']}"
            )

        ordered_candidates = [
            item["candidate"]
            for item in ranked
        ]

        result = self.healer.repair_candidates(
            relative_path=relative_path,
            old_text=old_text,
            candidates=ordered_candidates,
            test_path=test_path,
        )

        result["ranking"] = ranked

        return result
