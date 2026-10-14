from typing import Any

from .planner import Planner
from .router import AgentRouter
from .task_analyzer import TaskAnalyzer
from .tool_runtime import ToolRuntime
from .critic import Critic

from memory.manager import MemoryManager
from evaluation.evaluator import Evaluator
from learning.experience import ExperienceEngine


class PIKABrain:

    def __init__(
        self,
        router: AgentRouter,
        memory: MemoryManager,
        planner: Planner,
        evaluator: Evaluator,
        experience: ExperienceEngine,
        task_analyzer: TaskAnalyzer | None = None,
        tool_runtime: ToolRuntime | None = None,
        max_retries: int = 2,
        critic: Critic | None = None,
    ):
        self.router = router
        self.memory = memory
        self.planner = planner
        self.evaluator = evaluator
        self.experience = experience

        self.task_analyzer = (
            task_analyzer or TaskAnalyzer()
        )

        self.tool_runtime = tool_runtime
        self.critic = critic

        self.max_retries = max(
            0,
            max_retries,
        )

    async def think(
        self,
        task: str,
    ) -> dict[str, Any]:

        # ---------------------------------------------------------
        # Persistent memory
        # ---------------------------------------------------------

        memories = self.memory.retrieve(
            task
        )

        # ---------------------------------------------------------
        # Task intelligence
        # ---------------------------------------------------------

        task_analysis = (
            self.task_analyzer.analyze(
                task,
                memories=memories,
            )
        )

        # ---------------------------------------------------------
        # Tool path
        # ---------------------------------------------------------

        if (
            task_analysis.get("tool_required")
            and self.tool_runtime is not None
        ):

            tool_result = (
                self.tool_runtime.execute_for_task(
                    task,
                    task_analysis[
                        "tool_capabilities"
                    ],
                )
            )

            if tool_result.get("success"):

                result = {
                    "success": True,
                    "agent": "tool",
                    "provider": "builtin",
                    "model": None,
                    "output": tool_result[
                        "output"
                    ],
                    "tool_used": tool_result[
                        "tool_used"
                    ],
                    "tool_discovery": tool_result[
                        "discovery"
                    ],
                    "error": None,
                }

                evaluation = (
                    self.evaluator.evaluate(
                        result,
                        task=task,
                    )
                )

                if evaluation.get("passed"):

                    episode = (
                        self.experience
                        .create_experience(
                            task,
                            result,
                            evaluation,
                        )
                    )

                    self.memory.remember_episode(
                        episode
                    )

                    lesson = episode.get(
                        "lesson"
                    )

                    if lesson:
                        self.memory.remember_lesson(
                            {
                                **lesson,
                                "timestamp": episode.get(
                                "timestamp"
                            ),
                            }
                        )

                    return {
                        "task": task,
                        "task_analysis": task_analysis,
                        "plan": [],
                        "agent": "tool",
                        "result": result,
                        "evaluation": evaluation,
                        "attempts": [
                            {
                                "attempt": 1,
                                "result": result,
                                "evaluation": evaluation,
                            }
                        ],
                        "attempt_count": 1,
                        "final_status": "success",
                        "memory_used": memories,
                        "tool_used": result[
                            "tool_used"
                        ],
                    }

        # ---------------------------------------------------------
        # Normal agent path
        # ---------------------------------------------------------

        plan = self.planner.plan(
            task,
            memories=memories,
        )

        agent = self.router.select(
            required_capabilities=(
                task_analysis["capabilities"]
            )
        )

        attempts: list[dict[str, Any]] = []

        feedback = ""

        total_attempts = (
            self.max_retries + 1
        )

        for attempt_number in range(
            1,
            total_attempts + 1,
        ):

            context = {
                "plan": plan,
                "memory": memories,
                "task_analysis": task_analysis,
                "attempt": attempt_number,
                "max_attempts": total_attempts,
                "previous_feedback": feedback,
            }

            result = await agent.execute(
                task,
                context=context,
            )

            evaluation = self.evaluator.evaluate(
                result,
                task=task,
            )

            # -------------------------------------------------
            # Independent Critic
            # -------------------------------------------------
            # The Evaluator checks the worker result.
            # The Critic independently reviews the generated
            # output. Both must pass.
            # -------------------------------------------------

            critic_review = None

            if self.critic is not None:
                candidate_output = result.get(
                    "output",
                    "",
                )

                normalized_candidate = (
                    evaluation.get(
                        "normalized_output"
                    )
                    or candidate_output
                )

                critic_review = self.critic.review(
                    task,
                    normalized_candidate,
                )

                evaluation["critic"] = critic_review

                if not critic_review.get("passed"):
                    evaluation["passed"] = False
                    evaluation["score"] = min(
                        float(
                            evaluation.get(
                                "score",
                                0.0,
                            )
                        ),
                        float(
                            critic_review.get(
                                "score",
                                0.0,
                            )
                        ),
                    )

                    evaluation["feedback"] = (
                        "Critic rejected Actor output: "
                        + str(
                            critic_review.get(
                                "feedback",
                                "Correction required.",
                            )
                        )
                    )

            normalized_output = evaluation.get(
                "normalized_output"
            )

            if normalized_output:
                result["output"] = (
                    normalized_output
                )

            attempt_record = {
                "attempt": attempt_number,
                "result": result,
                "evaluation": evaluation,
            }

            attempts.append(
                attempt_record
            )

            if evaluation.get("passed"):

                episode = (
                    self.experience
                    .create_experience(
                        task,
                        result,
                        evaluation,
                    )
                )

                self.memory.remember_episode(
                    episode
                )

                lesson = episode.get(
                    "lesson"
                )

                if lesson:
                    self.memory.remember_lesson(
                        {
                            **lesson,
                            "timestamp": episode.get("timestamp"),
                        }
                    )

                return {
                    "task": task,
                    "task_analysis": task_analysis,
                    "plan": plan,
                    "agent": agent.name,
                    "result": result,
                    "evaluation": evaluation,
                    "attempts": attempts,
                    "attempt_count": attempt_number,
                    "final_status": "success",
                    "memory_used": memories,
                    "tool_used": None,
                }

            feedback = str(
                evaluation.get(
                    "feedback",
                    "Previous attempt failed validation.",
                )
            )

            self.memory.remember_failure(
                {
                    "task": task,
                    "attempt": attempt_number,
                    "result": result,
                    "evaluation": evaluation,
                    "task_analysis": task_analysis,
                }
            )

            if attempt_number < total_attempts:

                print()
                print(
                    f"[PIKA BRAIN] Evaluation failed "
                    f"(attempt "
                    f"{attempt_number}/"
                    f"{total_attempts})."
                )

                print(
                    "[PIKA BRAIN] Feedback:",
                    feedback,
                )

                print(
                    "[PIKA BRAIN] Retrying worker..."
                )

        final_result = attempts[-1]["result"]

        final_evaluation = attempts[-1][
            "evaluation"
        ]

        episode = (
            self.experience
            .create_experience(
                task,
                final_result,
                final_evaluation,
            )
        )

        self.memory.remember_episode(
            episode
        )

        lesson = episode.get("lesson")

        if lesson:
            self.memory.remember_lesson(
                {
                    **lesson,
                    "timestamp": episode.get("timestamp"),
                }
            )

        return {
            "task": task,
            "task_analysis": task_analysis,
            "plan": plan,
            "agent": agent.name,
            "result": final_result,
            "evaluation": final_evaluation,
            "attempts": attempts,
            "attempt_count": len(attempts),
            "final_status": "failed",
            "memory_used": memories,
            "tool_used": None,
        }
