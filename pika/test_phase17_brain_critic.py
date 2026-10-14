from core.brain import PIKABrain
from core.critic import Critic


class TestAgent:

    name = "test-actor"

    capabilities = [
        "coding",
        "generation",
        "reasoning",
        "analysis",
    ]

    def __init__(self):
        self.calls = 0

    async def execute(
        self,
        task,
        context=None,
    ):
        self.calls += 1

        if self.calls == 1:
            print(
                "[TEST ACTOR] Returning wrong function"
            )

            return {
                "success": True,
                "agent": self.name,
                "provider": "test",
                "model": "test-actor",
                "output": (
                    "def wrong_name(a, b):\n"
                    "    return a + b"
                ),
                "error": None,
            }

        print(
            "[TEST ACTOR] Returning corrected function"
        )

        return {
            "success": True,
            "agent": self.name,
            "provider": "test",
            "model": "test-actor",
            "output": (
                "def add_numbers(a, b):\n"
                "    return a + b"
            ),
            "error": None,
        }


class TestRouter:

    def __init__(self):
        self.agent = TestAgent()

    def select(
        self,
        required_capabilities=None,
    ):
        return self.agent


class TestMemory:

    def __init__(self):
        self.episodes = []
        self.failures = []

    def retrieve(self, task):
        return {
            "episodes": self.episodes,
            "failures": self.failures,
            "skills": [],
            "knowledge": [],
            "lessons": [],
        }

    def remember_episode(self, episode):
        self.episodes.append(episode)

    def remember_failure(self, failure):
        self.failures.append(failure)

    def remember_lesson(self, lesson):
        pass


class TestPlanner:

    def plan(
        self,
        task,
        memories=None,
    ):
        return [
            "Understand task",
            "Generate Python function",
            "Validate output",
        ]


class TestExperience:

    def create_experience(
        self,
        task,
        result,
        evaluation,
    ):
        return {
            "task": task,
            "result": result,
            "evaluation": evaluation,
            "lesson": {
                "type": "critic_feedback",
                "learned": True,
            },
        }


class TestEvaluator:

    def evaluate(
        self,
        result,
        task=None,
    ):
        # Deliberately accepts syntactically valid output.
        # Critic is responsible for task-aware validation.
        return {
            "passed": bool(
                result.get("success")
            ),
            "score": 1.0 if result.get(
                "success"
            ) else 0.0,
            "reason": "Worker reported success.",
            "feedback": "",
            "normalized_output": result.get(
                "output",
                "",
            ),
        }


async def main():

    print("=" * 60)
    print("PIKA PHASE 17")
    print("BRAIN + CRITIC INTEGRATION TEST")
    print("=" * 60)

    task = (
        "Write a Python function named "
        "add_numbers that adds two numbers."
    )

    memory = TestMemory()

    brain = PIKABrain(
        router=TestRouter(),
        memory=memory,
        planner=TestPlanner(),
        evaluator=TestEvaluator(),
        experience=TestExperience(),
        critic=Critic(),
        max_retries=2,
    )

    print()
    print("TASK:")
    print(task)

    print()
    print("STARTING BRAIN...")

    result = await brain.think(task)

    print()
    print("=" * 60)
    print("PHASE 17 RESULT")
    print("=" * 60)

    print()
    print("FINAL STATUS:")
    print(result["final_status"])

    print()
    print("ATTEMPT COUNT:")
    print(result["attempt_count"])

    print()
    print("ATTEMPT DETAILS:")

    for attempt in result["attempts"]:

        evaluation = attempt["evaluation"]

        print()
        print(
            f"Attempt {attempt['attempt']}:"
        )

        print(
            "Evaluator passed:",
            evaluation.get("passed"),
        )

        critic = evaluation.get(
            "critic"
        )

        if critic:
            print(
                "Critic passed:",
                critic.get("passed"),
            )

            print(
                "Critic issues:",
                critic.get("issues"),
            )

    print()
    print("FINAL OUTPUT:")
    print(
        result["result"]["output"]
    )

    final_critic = result[
        "evaluation"
    ].get("critic")

    print()
    print("FINAL CRITIC:")
    print(final_critic)

    print()
    print("MEMORY:")
    print(
        "episodes =",
        len(memory.episodes),
    )

    print(
        "failures =",
        len(memory.failures),
    )

    first = result["attempts"][0]
    second = result["attempts"][1]

    first_critic = first["evaluation"].get(
        "critic"
    )

    second_critic = second["evaluation"].get(
        "critic"
    )

    passed = (
        result["final_status"] == "success"
        and result["attempt_count"] == 2

        # Actor's first result was worker-success,
        # but Critic rejected it.
        and first["result"]["success"] is True
        and first_critic is not None
        and first_critic["passed"] is False

        # Brain converted Critic rejection into
        # a failed evaluation and retried.
        and first["evaluation"]["passed"] is False

        # Second output passed Critic.
        and second_critic is not None
        and second_critic["passed"] is True

        # Correct final output.
        and "def add_numbers" in (
            result["result"]["output"]
        )
    )

    print()

    if passed:
        print(
            "PIKA PHASE 17 BRAIN+CRITIC TEST: PASSED"
        )
    else:
        print(
            "PIKA PHASE 17 BRAIN+CRITIC TEST: FAILED"
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
