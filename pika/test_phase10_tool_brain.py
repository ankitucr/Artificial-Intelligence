import asyncio

from core.brain import PIKABrain
from core.planner import Planner
from core.runtime import (
    create_runtime,
    create_tool_runtime,
)
from evaluation.evaluator import Evaluator
from learning.experience import ExperienceEngine
from memory.manager import MemoryManager


async def main():

    print("=" * 60)
    print("PIKA PHASE 10")
    print("TOOL-AWARE BRAIN INTEGRATION TEST")
    print("=" * 60)

    router = create_runtime()

    tool_runtime = create_tool_runtime()

    memory = MemoryManager(
        storage_path="data/phase10_test_memory.json"
    )

    brain = PIKABrain(
        router=router,
        memory=memory,
        planner=Planner(),
        evaluator=Evaluator(),
        experience=ExperienceEngine(),
        tool_runtime=tool_runtime,
        max_retries=2,
    )

    task = (
        "Calculate the sum of 10 and 32."
    )

    print()
    print("TASK:")
    print(task)

    print()
    print("THINKING...")

    result = await brain.think(
        task
    )

    print()
    print("=" * 60)
    print("PHASE 10 RESULT")
    print("=" * 60)

    print()
    print("TASK TYPE:")
    print(
        result["task_analysis"]["task_type"]
    )

    print()
    print("TOOL REQUIRED:")
    print(
        result["task_analysis"]["tool_required"]
    )

    print()
    print("AGENT:")
    print(result["agent"])

    print()
    print("TOOL USED:")
    print(result.get("tool_used"))

    print()
    print("OUTPUT:")
    print(
        result["result"]["output"]
    )

    print()
    print("EVALUATION:")
    print(result["evaluation"])

    print()
    print("MEMORY:")
    print(memory.stats())

    passed = (
        result["final_status"] == "success"
        and result["agent"] == "tool"
        and result["tool_used"]
        == "calculator_sum"
        and result["result"]["output"]
        == "42"
        and result["evaluation"]["passed"]
    )

    print()

    if passed:
        print(
            "PIKA PHASE 10 TOOL-BRAIN TEST: PASSED"
        )
    else:
        print(
            "PIKA PHASE 10 TOOL-BRAIN TEST: FAILED"
        )


if __name__ == "__main__":
    asyncio.run(main())
