from __future__ import annotations

from typing import Any


class CandidateRanker:
    """
    Ranks repair candidates using independent Critic feedback.

    Higher-quality candidates are placed first.
    Original ordering is preserved when scores are equal.
    """

    def __init__(
        self,
        critic,
        learner=None,
    ):
        self.critic = critic
        self.learner = learner

    def rank(
        self,
        task: str,
        candidates: list[str],
    ) -> list[dict[str, Any]]:

        ranked: list[dict[str, Any]] = []

        for index, candidate in enumerate(candidates):
            review = self.critic.review(
                task,
                candidate,
            )

            checks = review.get("checks", {})

            score = float(
                review.get("score", 0.0)
            )

            passed = bool(
                review.get("passed", False)
            )

            issues = review.get(
                "issues",
                [],
            )

            critic_score = (
                (1000 if passed else 0)
                + (score * 100)
                - (len(issues) * 10)
                - (
                    len(
                        review.get(
                            "checks",
                            {},
                        ).get(
                            "forbidden_operations",
                            [],
                        )
                    )
                    * 100
                )
            )

            learning = {
                "known": False,
                "bonus": 0.0,
            }

            if self.learner is not None:
                learning = (
                    self.learner.get_candidate_signal(
                        candidate
                    )
                )

            learning_bonus = float(
                learning.get(
                    "bonus",
                    0.0,
                )
            )

            quality_score = (
                critic_score
                + learning_bonus
            )

            ranked.append(
                {
                    "original_index": index,
                    "candidate": candidate,
                    "review": review,
                    "critic_score": critic_score,
                    "learning": learning,
                    "learning_bonus": learning_bonus,
                    "quality_score": quality_score,
                    "passed_critic": passed,
                    "python_syntax": checks.get(
                        "python_syntax",
                        False,
                    ),
                }
            )

        ranked.sort(
            key=lambda item: (
                item["quality_score"],
                -item["original_index"],
            ),
            reverse=True,
        )

        for rank, item in enumerate(
            ranked,
            start=1,
        ):
            item["rank"] = rank

        return ranked
