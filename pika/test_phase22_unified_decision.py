from __future__ import annotations

import asyncio
from pathlib import Path

from core.decision_loop import UnifiedDecisionLoop
from core.experience_learner import ExperienceLearner


ROOT = Path(__file__).resolve().parent
STORE = (
    ROOT
    / "data"
    / "phase22"
    / "experience.json"
)


class TestActor:
    """
    Deterministic Actor used only for integration testing.
    """

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
                "agent": "test_actor",
                "output": (
                    "def wrong_function(a, b):\n"
                    "    return a + b\n"
                ),
            }

        print(
            "[TEST ACTOR] Returning corrected function"
        )

        return {
            "success": True,
            "agent": "test_actor",
            "output": (
                "def add_numbers(a, b):\n"
                "    return a + b\n"
            ),
        }


class TestEvaluator:

    def evaluate(
        self,
        result,
        task=None,
    ):
        output = result.get(
            "output",
            "",
        )

        passed = (
            "def add_numbers"
            in output
            and "return a + b"
            in output
        )

        return {
            "passed": passed,
            "score": 1.0 if passed else 0.0,
            "feedback": (
                "Execution evaluation passed."
                if passed
                else "Required implementation not found."
            ),
        }


class TestExperience:
    """
    Minimal compatibility object proving that
    UnifiedDecisionLoop can coexist with the
    existing ExperienceEngine interface.
    """

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
        }


async def main():

    print("=" * 60)
    print("PIKA PHASE 22")
    print("UNIFIED DECISION LOOP")
    print("=" * 60)

    STORE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if STORE.exists():
        STORE.unlink()

    learner = ExperienceLearner(
        STORE
    )

    actor = TestActor()

    loop = UnifiedDecisionLoop(
        worker=actor,
        evaluator=TestEvaluator(),
        experience=TestExperience(),
        learner=learner,
        storage_path=STORE,
    )

    task = (
        "Write a Python function named "
        "add_numbers that adds two numbers."
    )

    print()
    print("TASK:")
    print(task)

    print()
    print("STARTING UNIFIED DECISION LOOP...")

    result = await loop.run(
        task,
        memory={
            "source": "phase22-test",
        },
        plan=[
            "generate implementation",
            "critic review",
            "evaluate result",
        ],
        max_attempts=3,
    )

    print()
    print("=" * 60)
    print("PHASE 22 RESULT")
    print("=" * 60)

    print()
    print("SUCCESS:")
    print(result["success"])

    print()
    print("ATTEMPT COUNT:")
    print(result["attempt_count"])

    print()
    print("ATTEMPTS:")

    for item in result["attempts"]:
        print(
            f"Attempt {item['attempt']}: "
            f"critic={item['critic']['passed']} "
            f"evaluation={item['evaluation']['passed']} "
            f"success={item['success']}"
        )

    print()
    print("FINAL OUTPUT:")

    print(
        result["final_result"].get(
            "output",
            "",
        )
    )

    print()
    print("LEARNING SIGNAL:")

    print(
        result.get(
            "learning_signal"
        )
    )

    stats = learner.stats()

    print()
    print("MEMORY STATS:")
    print(stats)

    passed = (
        result["success"] is True
        and result["attempt_count"] == 2
        and result["attempts"][0]["critic"]["passed"]
        is False
        and result["attempts"][1]["critic"]["passed"]
        is True
        and result["attempts"][1]["evaluation"]["passed"]
        is True
        and "def add_numbers"
        in result["final_result"]["output"]
        and stats["experiences"] == 2
        and stats["failures"] == 1
        and stats["successes"] == 1
        and STORE.exists()
    )

    print()

    if passed:
        print(
            "PIKA PHASE 22 UNIFIED-DECISION TEST: PASSED"
        )
    else:
        print(
            "PIKA PHASE 22 UNIFIED-DECISION TEST: FAILED"
        )

    if STORE.exists():
        STORE.unlink()

    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
