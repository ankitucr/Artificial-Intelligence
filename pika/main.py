import asyncio

from core.brain import PIKABrain
from core.planner import Planner
from core.runtime import (
    create_runtime,
    create_tool_runtime,
)
from memory.manager import MemoryManager
from evaluation.evaluator import Evaluator
from learning.experience import ExperienceEngine


async def run_task(
    brain: PIKABrain,
    task: str,
):
    print()
    print("=" * 72)
    print("PHASE 31 ENGINEERING TASK")
    print("=" * 72)
    print(task)
    print("=" * 72)

    result = await brain.think(task)

    print()
    print("=" * 72)
    print("PIKA RESULT")
    print("=" * 72)

    print()
    print("STATUS:")
    print("SUCCESS" if result.get("success") else "FAILED")

    print()
    print("TASK ANALYSIS:")
    print(result.get("task_analysis"))

    print()
    print("DECISION TRACE:")
    for index, decision in enumerate(
        result.get("decision_trace", []),
        start=1,
    ):
        print(f"Decision {index}:")
        print(decision)

    print()
    print("AGENT:")
    print(result.get("agent"))

    print()
    print("PROVIDER:")
    print(result.get("provider"))

    print()
    print("MODEL:")
    print(result.get("model"))

    print()
    print("ATTEMPTS:")
    print(len(result.get("attempts", [])))

    for index, attempt in enumerate(
        result.get("attempts", []),
        start=1,
    ):
        print()
        print(f"ATTEMPT {index}")
        print("-" * 72)

        print("Decision:")
        print(attempt.get("decision"))

        print()
        print("Evaluation:")
        print(attempt.get("evaluation"))

        attempt_result = attempt.get(
            "result",
            {},
        )

        if "workspace_execution" in attempt_result:
            print()
            print("Workspace Execution:")
            print(
                attempt_result.get(
                    "workspace_execution"
                )
            )

        if attempt_result.get("error"):
            print()
            print("Error:")
            print(
                attempt_result.get("error")
            )

    print()
    print("OUTPUT:")
    print(result.get("output", ""))

    print()
    print("FINAL EVALUATION:")
    print(result.get("evaluation"))

    print()
    print("EXPERIENCE:")
    print(result.get("experience"))

    return result


async def main():

    print("=" * 72)
    print("PIKA PHASE 31")
    print("WORKSPACE EXECUTION BRAIN")
    print("=" * 72)

    router = create_runtime()
    tool_runtime = create_tool_runtime()

    memory = MemoryManager()

    brain = PIKABrain(
        router=router,
        memory=memory,
        planner=Planner(),
        evaluator=Evaluator(),
        experience=ExperienceEngine(),
        tool_runtime=tool_runtime,
        max_retries=2,
    )

    print()
    print("BRAIN: ONLINE")
    print("DECISION ENGINE: ONLINE")
    print("PLANNER: ONLINE")
    print("WORKSPACE EXECUTOR: ONLINE")
    print("API WORKER: COHERE")
    print("MODEL: command-a-03-2025")

    print()
    print("REGISTERED AGENTS:")
    print(router.list())

    print()
    print("REGISTERED SKILLS:")
    print(tool_runtime.skills.list())

    print()
    print("REGISTERED TOOLS:")
    print(tool_runtime.tools.list())

    # =========================================================
    # REAL PHASE 31 ENGINEERING TASK
    # =========================================================

    task = """
Create a Python CLI Todo application inside the PIKA workspace.

Requirements:

1. Create a file named todo_app.py.
2. The application must support:
   - adding a todo
   - listing todos
   - marking a todo as completed
3. Store todos persistently in a JSON file named todos.json.
4. Handle invalid commands and invalid todo indexes safely.
5. Create automated tests in test_todo_app.py.
6. The tests must verify:
   - adding a todo
   - listing todos
   - completing a todo
   - invalid todo handling
7. The implementation must use only Python standard-library modules.
8. The application must be executable from the workspace.
9. Run the tests after creating the files.
10. If tests or execution fail, diagnose the failure, modify the files, and retry.
11. Finish only after the implementation passes verification.

Work directly inside the controlled PIKA workspace.

Do not merely explain the solution.
Actually create the files, run the tests, fix failures, and verify the final implementation.
""".strip()

    result = await run_task(
        brain,
        task,
    )

    print()
    print("=" * 72)
    print("PHASE 31 SUMMARY")
    print("=" * 72)

    print()
    print(
        "FINAL STATUS:",
        "PASS" if result.get("success") else "FAIL",
    )

    print(
        "MEMORY:",
        f"episodes={len(memory.episodes)}",
        f"failures={len(memory.failures)}",
    )

    print()
    print(
        "PIKA PHASE 31 WORKSPACE EXECUTION TEST: COMPLETE"
    )


if __name__ == "__main__":
    asyncio.run(main())
