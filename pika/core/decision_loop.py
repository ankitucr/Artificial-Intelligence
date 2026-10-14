from __future__ import annotations

from typing import Any

from core.critic import Critic
from core.candidate_ranker import CandidateRanker
from core.experience_learner import ExperienceLearner


class UnifiedDecisionLoop:
    """
    PIKA Phase 22.

    Unified lifecycle:

        task
          ↓
        worker
          ↓
        critic
          ↓
        ranking
          ↓
        execution/evaluation
          ↓
        experience
          ↓
        persistent learning

    This coordinator does not modify files itself.
    It coordinates existing PIKA intelligence components.
    """

    def __init__(
        self,
        worker,
        evaluator,
        experience,
        learner: ExperienceLearner,
        storage_path,
    ):
        self.worker = worker
        self.evaluator = evaluator
        self.experience = experience

        self.learner = learner
        self.critic = Critic()

        self.ranker = CandidateRanker(
            self.critic,
            learner=self.learner,
        )

        self.storage_path = storage_path

    async def run(
        self,
        task: str,
        memory: Any = None,
        plan: Any = None,
        max_attempts: int = 3,
    ) -> dict[str, Any]:

        attempts: list[dict[str, Any]] = []

        previous_feedback = ""

        for attempt_number in range(
            1,
            max_attempts + 1,
        ):
            context = {
                "memory": memory or {},
                "plan": plan or [],
                "attempt": attempt_number,
                "max_attempts": max_attempts,
                "previous_feedback": previous_feedback,
            }

            # ------------------------------------------
            # Worker / Actor
            # ------------------------------------------

            result = await self.worker.execute(
                task,
                context=context,
            )

            output = str(
                result.get(
                    "output",
                    "",
                )
            )

            # ------------------------------------------
            # Independent Critic
            # ------------------------------------------

            critic_review = self.critic.review(
                task,
                output,
            )

            # ------------------------------------------
            # Candidate ranking
            # ------------------------------------------

            ranking = self.ranker.rank(
                task,
                [output],
            )

            ranking_item = ranking[0]

            # ------------------------------------------
            # Evaluator
            # ------------------------------------------

            evaluation = self.evaluator.evaluate(
                result,
                task=task,
            )

            passed = bool(
                evaluation.get("passed")
            ) and bool(
                critic_review.get("passed")
            )

            attempt = {
                "attempt": attempt_number,
                "result": result,
                "critic": critic_review,
                "ranking": ranking_item,
                "evaluation": evaluation,
                "success": passed,
            }

            attempts.append(attempt)

            # ------------------------------------------
            # SUCCESS
            # ------------------------------------------

            if passed:

                final_result = result

                learning_candidates = [
                    {
                        "candidate": output,
                        "rank": ranking_item.get(
                            "rank",
                            1,
                        ),
                        "quality_score": ranking_item.get(
                            "quality_score",
                            0.0,
                        ),
                        "passed_critic": True,
                        "success": True,
                    }
                ]

                experience = self.learner.learn(
                    task,
                    learning_candidates,
                    {
                        "success": True,
                    },
                )

                return {
                    "success": True,
                    "task": task,
                    "attempt_count": attempt_number,
                    "attempts": attempts,
                    "final_result": final_result,
                    "critic": critic_review,
                    "evaluation": evaluation,
                    "experience": experience,
                    "learning_signal": (
                        self.learner
                        .get_candidate_signal(
                            output
                        )
                    ),
                }

            # ------------------------------------------
            # FAILURE
            # ------------------------------------------

            previous_feedback = str(
                critic_review.get(
                    "feedback",
                    evaluation.get(
                        "feedback",
                        "Previous attempt failed.",
                    ),
                )
            )

            self.learner.learn(
                task,
                [
                    {
                        "candidate": output,
                        "rank": ranking_item.get(
                            "rank",
                            1,
                        ),
                        "quality_score": ranking_item.get(
                            "quality_score",
                            0.0,
                        ),
                        "passed_critic": bool(
                            critic_review.get(
                                "passed",
                                False,
                            )
                        ),
                        "success": False,
                    }
                ],
                {
                    "success": False,
                },
            )

        return {
            "success": False,
            "task": task,
            "attempt_count": len(
                attempts
            ),
            "attempts": attempts,
            "final_result": attempts[-1][
                "result"
            ],
            "critic": attempts[-1][
                "critic"
            ],
            "evaluation": attempts[-1][
                "evaluation"
            ],
            "experience": None,
        }
