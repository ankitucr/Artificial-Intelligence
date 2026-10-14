import asyncio
import sys

from core.brain import PIKABrain
from core.planner import Planner
from core.runtime import create_runtime
from memory.manager import MemoryManager
from evaluation.evaluator import Evaluator
from learning.experience import ExperienceEngine
from core.task_analyzer import TaskAnalyzer


async def run_task(task: str):
    print("=" * 70)
    print("PIKA PHASE 25")
    print("REAL TASK EXECUTION")
    print("=" * 70)

    router = create_runtime()
    memory = MemoryManager()

    brain = PIKABrain(
        router=router,
        memory=memory,
        planner=Planner(),
        evaluator=Evaluator(),
        experience=ExperienceEngine(),
        task_analyzer=TaskAnalyzer(),
        max_retries=2,
    )

    print()
    print("BRAIN: ONLINE")
    print("WORKER: API")
    print("PROVIDER: COHERE")
    print("MODEL: command-a-03-2025")
    print()
    print("TASK:")
    print(task)
    print()
    print("STARTING BRAIN...")
    print("-" * 70)

    result = await brain.think(task)

    print()
    print("=" * 70)
    print("PIKA RESULT")
    print("=" * 70)

    print()
    print("STATUS:")
    print(result.get("final_status"))

    print()
    print("ATTEMPTS:")
    print(result.get("attempt_count"))

    print()
    print("AGENT:")
    print(result.get("agent"))

    worker_result = result.get("result", {})

    print()
    print("PROVIDER:")
    print(worker_result.get("provider"))

    print()
    print("MODEL:")
    print(worker_result.get("model"))

    print()
    print("OUTPUT:")
    print(worker_result.get("output", ""))

    print()
    print("EVALUATION:")
    print(result.get("evaluation"))

    print()
    print("MEMORY:")
    print(
        f"episodes={len(memory.episodes)} "
        f"failures={len(memory.failures)}"
    )

    print()
    if result.get("final_status") == "success":
        print("PIKA PHASE 25 REAL-TASK TEST: PASSED")
    else:
        print("PIKA PHASE 25 REAL-TASK TEST: FAILED")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print('python pika.py "your task here"')
        sys.exit(1)

    task = " ".join(sys.argv[1:])

    asyncio.run(run_task(task))


if __name__ == "__main__":
    main()
