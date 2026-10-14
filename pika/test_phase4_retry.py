import asyncio

from core.brain import PIKABrain
from core.planner import Planner
from evaluation.evaluator import Evaluator
from learning.experience import ExperienceEngine
from memory.manager import MemoryManager


class RetryTestAgent:

    name = "retry-test"

    def __init__(self):
        self.calls = 0

    async def execute(self, task, context=None):

        self.calls += 1

        if self.calls == 1:
            print("[TEST WORKER] Returning intentionally broken code")

            return {
                "success": True,
                "agent": self.name,
                "provider": "test",
                "model": "retry-test-model",
                "output": (
                    "def add_numbers(a, b)\n"
                    "    return a + b"
                ),
            }

        print("[TEST WORKER] Returning corrected code")

        return {
            "success": True,
            "agent": self.name,
            "provider": "test",
            "model": "retry-test-model",
            "output": (
                "def add_numbers(a, b):\n"
                "    return a + b"
            ),
        }


class RetryTestRouter:

    def __init__(self, agent):
        self.agent = agent

    def select(self):
        return self.agent

    def list(self):
        return [self.agent.name]


async def main():

    print("=" * 60)
    print("PIKA PHASE 4 RETRY TEST")
    print("FAILURE → FEEDBACK → RETRY → PASS")
    print("=" * 60)

    agent = RetryTestAgent()

    memory = MemoryManager()

    brain = PIKABrain(
        router=RetryTestRouter(agent),
        memory=memory,
        planner=Planner(),
        evaluator=Evaluator(),
        experience=ExperienceEngine(),
        max_retries=2,
    )

    task = (
        "Write a Python function named add_numbers "
        "that adds two numbers. "
        "Return only the function code."
    )

    print()
    print("TASK:")
    print(task)

    print()
    print("Starting controlled failure test...")
    print()

    result = await brain.think(task)

    print()
    print("=" * 60)
    print("RETRY TEST RESULT")
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
            f"Attempt {attempt['attempt']}: "
            f"passed={evaluation.get('passed')} "
            f"score={evaluation.get('score')}"
        )

        print(
            "Reason:",
            evaluation.get("reason"),
        )

        print(
            "Issues:",
            evaluation.get("issues"),
        )

    print()
    print("FINAL OUTPUT:")
    print(result["result"]["output"])

    print()
    print("MEMORY:")
    print(
        f"episodes={len(memory.episodes)} "
        f"failures={len(memory.failures)}"
    )

    print()
    print("=" * 60)

    if (
        result["final_status"] == "success"
        and result["attempt_count"] == 2
        and len(memory.failures) == 1
        and len(memory.episodes) == 1
        and result["evaluation"].get("passed")
    ):
        print("PIKA PHASE 4 RETRY TEST: PASSED")
    else:
        print("PIKA PHASE 4 RETRY TEST: FAILED")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
