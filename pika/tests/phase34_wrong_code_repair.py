from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path

from core.repair_candidate_generator import RepairCandidateGenerator
from core.phase33_controller import Phase33Controller
from workspace.manager import WorkspaceManager

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE / "workspace" / "__phase34_wrong_code_repair__"
LEARNING_DB = BASE / "data" / "__phase34_wrong_code_repair__" / "learning_engine.json"

TARGET = "pricing.py"
TEST = "test_pricing.py"

BROKEN_SOURCE = """def discount(price, percent):
    return price - percent
"""

TEST_SOURCE = """from pricing import discount

def test_discount():
    assert discount(100, 20) == 80
    assert discount(200, 10) == 180
    assert discount(50, 0) == 50

if __name__ == "__main__":
    test_discount()
    print("INDEPENDENT TEST PASS")
"""

TASK = (
    "Fix the discount function in pricing.py. "
    "It must subtract the given percentage of the price, "
    "not subtract the percentage number directly. "
    "For example discount(100, 20) must return 80."
)

DIAGNOSIS = {
    "error_type": "test_failure",
    "root_cause": (
        "discount subtracts percent as a raw number instead "
        "of calculating the percentage of price"
    ),
    "error_message": (
        "discount(100, 20) returned 80 expected but current "
        "implementation returns 80 only accidentally for this case; "
        "additional cases expose the bug"
    ),
}


def run_test():
    return WorkspaceManager(ROOT).run_command(["python", TEST])


async def main():
    print("=" * 56)
    print("PIKA REAL WRONG-CODE SELF-HEALING TEST")
    print("=" * 56)
    print("Workspace:", ROOT)
    print("Learning DB:", LEARNING_DB)

    # Only reset this dedicated test workspace and test database.
    if ROOT.exists():
        shutil.rmtree(ROOT)
    if LEARNING_DB.exists():
        LEARNING_DB.unlink()

    ROOT.mkdir(parents=True, exist_ok=True)
    LEARNING_DB.parent.mkdir(parents=True, exist_ok=True)

    (ROOT / TARGET).write_text(BROKEN_SOURCE, encoding="utf-8")
    (ROOT / TEST).write_text(TEST_SOURCE, encoding="utf-8")

    baseline = run_test()
    print("\n[BASELINE] success =", baseline.get("success"))
    print("[BASELINE] stderr =", baseline.get("stderr", ""))

    assert baseline.get("success") is False, (
        "STOP: broken code unexpectedly passed its baseline test"
    )
    print("PASS: wrong code failure reproduced")

    generator = RepairCandidateGenerator(
        max_candidates=3,
        workspace_root=ROOT,
    )

    worker_plan = {
        "files": [
            {
                "path": TARGET,
                "content": (ROOT / TARGET).read_text(encoding="utf-8"),
            }
        ],
        "commands": [["python", TEST]],
    }

    print("\n[GENERATOR] Asking PIKA to generate repair candidates...")
    generated = await generator.generate_from_failure(
        task=TASK,
        diagnosis=DIAGNOSIS,
        worker_output=json.dumps(worker_plan),
        previous_feedback=baseline.get("stderr", ""),
    )

    print("[GENERATOR] success =", generated.get("success"))
    print("[GENERATOR] provider =", generated.get("provider"))
    print("[GENERATOR] model =", generated.get("model"))
    print("[GENERATOR] error =", generated.get("error"))
    print("[GENERATOR] target =", generated.get("target_path"))
    print("[GENERATOR] candidates =", generated.get("candidates"))

    assert generated.get("success") is True, (
        "FAIL: real candidate generation failed"
    )
    assert generated.get("target_path")
    assert generated.get("old_text")
    assert generated.get("test_path")
    assert generated.get("candidates")

    controller = Phase33Controller(
        ROOT,
        max_candidates=3,
        learning_memory_path=LEARNING_DB,
    )

    print("\n[PHASE 33] Applying generated candidates...")
    repaired = controller.repair(
        diagnosis=DIAGNOSIS,
        relative_path=generated["target_path"],
        old_text=generated["old_text"],
        candidates=generated["candidates"],
        test_path=generated["test_path"],
        task=TASK,
    )

    print("[PHASE 33] success =", repaired.get("success"))
    print("[PHASE 33] stage =", repaired.get("stage"))

    assert repaired.get("success") is True, (
        "FAIL: Phase 33 could not verify a repair"
    )

    final_test = run_test()
    print("\n[INDEPENDENT TEST] success =", final_test.get("success"))
    print("[INDEPENDENT TEST] stdout =", final_test.get("stdout", ""))
    print("[INDEPENDENT TEST] stderr =", final_test.get("stderr", ""))

    assert final_test.get("success") is True, (
        "FAIL: repaired code did not pass independent tests"
    )
    assert LEARNING_DB.exists(), (
        "FAIL: dedicated learning database was not created"
    )

    print("\n" + "=" * 56)
    print("REAL WRONG-CODE SELF-HEALING TEST: PASS")
    print("Verified: baseline failed")
    print("Verified: real candidate generation succeeded")
    print("Verified: Phase 33 accepted and tested a repair")
    print("Verified: independent tests passed")
    print("Verified: isolated learning DB created")
    print("=" * 56)


if __name__ == "__main__":
    asyncio.run(main())
