import asyncio

from core.brain import PIKABrain
from core.planner import Planner
from core.runtime import create_runtime
from memory.manager import MemoryManager
from evaluation.evaluator import Evaluator
from learning.experience import ExperienceEngine


async def main():

    print("=" * 60)
    print("PIKA PHASE 2")
    print("MODEL-AGNOSTIC RUNTIME")
    print("=" * 60)

    router = create_runtime()

    brain = PIKABrain(
        router=router,
        memory=MemoryManager(),
        planner=Planner(),
        evaluator=Evaluator(),
        experience=ExperienceEngine(),
    )

    result = await brain.think(
        "Create a Python function that adds two numbers."
    )

    print()
    print("AGENT:", result["agent"])

    print(
        "PROVIDER:",
        result["result"].get("provider"),
    )

    print(
        "MODEL:",
        result["result"].get("model"),
    )

    print()
    print("MODEL OUTPUT:")
    print(result["result"]["output"])

    print()
    print("EVALUATION:")
    print(result["evaluation"])

    print()
    print("REGISTERED AGENTS:")
    print(list(router._agents.keys()))

    print()
    print("PIKA PHASE 2 TEST: PASSED")


if __name__ == "__main__":
    asyncio.run(main())
