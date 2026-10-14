from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path

from core.learning_repair_bridge import LearningRepairBridge
from core.phase33_controller import Phase33Controller
from core.repair_candidate_generator import RepairCandidateGenerator
from workspace.manager import WorkspaceManager


ROOT = (
    Path(__file__).resolve().parents[1]
    / "workspace"
    / "__phase34_real_e2e__"
)

LEARNING_DB = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "__phase34_e2e_test__"
    / "learning_engine.json"
)

TARGET = "calculator.py"
TEST = "test_calculator.py"

BROKEN_SOURCE = """def add(a, b):
    return a - b
"""

TEST_SOURCE = """from calculator import add

def test_add():
    assert add(2, 3) == 5

if __name__ == "__main__":
    test_add()
    print("TEST PASS")
"""

TASK = (
    "repair calculator add function failing arithmetic test "
    "when addition returns the wrong result"
)

DIAGNOSIS = {
    "error_type": "test_failure",
    "root_cause": (
        "add function uses subtraction instead of addition"
    ),
    "error_message": (
        "expected 5 but received -1"
    ),
}


def write_initial_workspace():
    if ROOT.exists():
        shutil.rmtree(ROOT)

    ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    (ROOT / TARGET).write_text(
        BROKEN_SOURCE,
        encoding="utf-8",
    )

    (ROOT / TEST).write_text(
        TEST_SOURCE,
        encoding="utf-8",
    )


def run_real_test():
    manager = WorkspaceManager(ROOT)

    return manager.run_command(
        ["python", TEST]
    )


def assert_real_failure():
    result = run_real_test()

    print(
        "[BASELINE] success =",
        result.get("success"),
    )

    print(
        "[BASELINE] stderr =",
        result.get("stderr", ""),
    )

    assert result.get("success") is False

    print(
        "[BASELINE] REAL TEST FAILURE: VERIFIED"
    )


async def run_round_1():
    print()
    print("================================================")
    print("ROUND 1 — REAL COHERE + REAL PHASE 33")
    print("================================================")

    generator = RepairCandidateGenerator(
        max_candidates=3,
        workspace_root=ROOT,
    )

    # IMPORTANT:
    # Phase 33 receives the ORIGINAL worker action plan,
    # not the Phase 32 execution-result dictionary.
    #
    # This reproduces the real Brain -> Phase32 -> Phase33
    # data flow exactly.
    target_source = (
        (ROOT / TARGET).read_text(
            encoding="utf-8"
        )
    )

    worker_plan = {
        "files": [
            {
                "path": TARGET,
                "content": target_source,
            }
        ],
        "commands": [
            [
                "python",
                TEST,
            ]
        ],
    }

    worker_output = json.dumps(
        worker_plan,
        ensure_ascii=False,
    )

    print(
        "[ROUND 1] REAL WORKER PLAN: VERIFIED"
    )
    print(
        "[ROUND 1] worker_output type =",
        type(worker_output).__name__,
    )
    print(
        "[ROUND 1] target source length =",
        len(target_source),
    )

    print(
        "[ROUND 1] Calling REAL RepairCandidateGenerator..."
    )

    context = await generator.generate_from_failure(
        task=TASK,
        diagnosis=DIAGNOSIS,
        worker_output=worker_output,
        previous_feedback="",
    )

    print()
    print("==============================================")
    print("REAL GENERATOR RESULT")
    print("==============================================")
    print("success =", context.get("success"))
    print("stage   =", context.get("stage"))
    print("error   =", context.get("error"))
    print("agent   =", context.get("agent"))
    print("provider=", context.get("provider"))
    print("model   =", context.get("model"))
    print("latency =", context.get("latency"))
    print("raw     =", context.get("raw"))
    print("context =", context)

    if not context.get("success"):
        raise RuntimeError(
            "RepairCandidateGenerator failed. "
            "Actual generator error is printed above."
        )

    assert context.get("target_path")
    assert context.get("old_text")
    assert context.get("test_path")
    assert context.get("candidates")

    print(
        "[ROUND 1] REAL COHERE GENERATION: VERIFIED"
    )

    print(
        "[ROUND 1] candidates =",
        len(context["candidates"]),
    )

    controller = Phase33Controller(
        ROOT,
        max_candidates=3,
    )

    print(
        "[ROUND 1] Calling REAL Phase33Controller..."
    )

    result = controller.repair(
        diagnosis=DIAGNOSIS,
        relative_path=context["target_path"],
        old_text=context["old_text"],
        candidates=context["candidates"],
        test_path=context["test_path"],
        task=TASK,
    )

    print(
        "[ROUND 1] repair success =",
        result.get("success"),
    )

    print(
        "[ROUND 1] repair stage =",
        result.get("stage"),
    )

    assert result.get("success") is True

    print(
        "[ROUND 1] REAL FILE MODIFICATION: VERIFIED"
    )

    print(
        "[ROUND 1] REAL PHASE 33 REPAIR: VERIFIED"
    )

    final_test = run_real_test()

    print(
        "[ROUND 1] independent test success =",
        final_test.get("success"),
    )

    assert final_test.get("success") is True

    print(
        "[ROUND 1] REAL INDEPENDENT TEST: VERIFIED"
    )

    assert LEARNING_DB.exists()

    data = json.loads(
        LEARNING_DB.read_text(
            encoding="utf-8"
        )
    )

    records = data.get(
        "experiences",
        [],
    )

    learned = [
        item
        for item in records
        if item.get("task") == TASK
        and item.get("success") is True
        and item.get("trusted") is True
    ]

    assert learned

    latest = learned[-1]

    print(
        "[ROUND 1] LEARNING RECORD CREATED: VERIFIED"
    )

    replay = latest.get(
        "replay_context",
        {},
    )

    assert replay.get("target_path") == TARGET
    assert replay.get("old_text")
    assert replay.get("old_text") in BROKEN_SOURCE
    assert replay.get("test_path") == TEST

    print(
        "[ROUND 1] REPLAY CONTEXT STORED: VERIFIED"
    )

    return latest


def run_round_2_without_cohere():
    print()
    print("================================================")
    print("ROUND 2 — COHERE DISABLED / MEMORY ONLY")
    print("================================================")

    # Recreate the SAME real failure.
    write_initial_workspace()

    assert_real_failure()

    bridge = LearningRepairBridge(
        ROOT,
        memory_path=LEARNING_DB,
    )

    print(
        "[ROUND 2] Searching PIKA learned memory..."
    )

    learned = bridge.find(
        task=TASK,
        error_type=DIAGNOSIS["error_type"],
        root_cause=DIAGNOSIS["root_cause"],
        error_message=DIAGNOSIS["error_message"],
    )

    assert learned is not None

    print(
        "[ROUND 2] MEMORY HIT: VERIFIED"
    )

    print(
        "[ROUND 2] learned method =",
        learned.get("method"),
    )

    print(
        "[ROUND 2] verified_count =",
        learned.get("verified_count"),
    )

    solution = learned.get(
        "solution",
        "",
    )

    replay = learned.get(
        "replay_context",
        {},
    )

    assert solution
    assert replay.get("target_path") == TARGET
    assert replay.get("old_text")
    assert replay.get("old_text") in BROKEN_SOURCE
    assert replay.get("test_path") == TEST

    # IMPORTANT:
    # No RepairCandidateGenerator is created or called here.
    # This is the actual Cohere-disabled path.
    print(
        "[ROUND 2] COHERE GENERATOR: DISABLED"
    )

    controller = Phase33Controller(
        ROOT,
        max_candidates=1,
    )

    print(
        "[ROUND 2] Applying learned candidate "
        "through REAL Phase33..."
    )

    result = controller.repair(
        diagnosis=DIAGNOSIS,
        relative_path=replay["target_path"],
        old_text=replay["old_text"],
        candidates=[solution],
        test_path=replay["test_path"],
        task=TASK,
    )

    print(
        "[ROUND 2] repair success =",
        result.get("success"),
    )

    assert result.get("success") is True

    print(
        "[ROUND 2] LEARNED REPAIR APPLIED: VERIFIED"
    )

    final_test = run_real_test()

    print(
        "[ROUND 2] REAL INDEPENDENT TEST success =",
        final_test.get("success"),
    )

    print(
        "[ROUND 2] stdout =",
        final_test.get("stdout", ""),
    )

    assert final_test.get("success") is True

    print(
        "[ROUND 2] COHERE CALLS: 0"
    )

    print(
        "[ROUND 2] COHERE-INDEPENDENT REPAIR: VERIFIED"
    )

    print(
        "[ROUND 2] REAL PHASE 33 VERIFICATION: VERIFIED"
    )


async def main():
    print()
    print("================================================")
    print("PHASE 34 — REAL CONTINUAL LEARNING E2E")
    print("================================================")

    print(
        "Learning DB:",
        LEARNING_DB,
    )

    write_initial_workspace()

    assert_real_failure()

    await run_round_1()

    run_round_2_without_cohere()

    print()
    print("================================================")
    print("PHASE 34 REAL E2E: PASS")
    print("================================================")

    print(
        "Real unknown problem: VERIFIED"
    )
    print(
        "Real Cohere generation: VERIFIED"
    )
    print(
        "Real Phase 33 repair: VERIFIED"
    )
    print(
        "Real learning record: VERIFIED"
    )
    print(
        "Replay context: VERIFIED"
    )
    print(
        "Memory retrieval: VERIFIED"
    )
    print(
        "Cohere-disabled second run: VERIFIED"
    )
    print(
        "Learned solution reused: VERIFIED"
    )
    print(
        "Real independent test: VERIFIED"
    )
    print(
        "Continual learning behavior: VERIFIED"
    )

    print()
    print(
        "TERMUX SHELL WILL REMAIN OPEN"
    )


if __name__ == "__main__":
    asyncio.run(main())
