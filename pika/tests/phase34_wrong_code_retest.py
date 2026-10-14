from pathlib import Path
import asyncio
import json
import shutil

from core.repair_candidate_generator import RepairCandidateGenerator
from core.phase33_controller import Phase33Controller
from workspace.manager import WorkspaceManager

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE / "workspace" / "__phase34_wrong_code_retest__"
DB = BASE / "data" / "__phase34_wrong_code_repair__" / "learning_engine.json"

TARGET = "discount_retest.py"
TEST = "test_discount_retest.py"

BROKEN = """def discount(price, percent):
    return price - percent
"""

TEST_CODE = """from discount_retest import discount

def test_discount():
    assert discount(100, 20) == 80
    assert discount(200, 10) == 180
    assert discount(50, 0) == 50

if __name__ == "__main__":
    test_discount()
    print("RETEST PASS")
"""

TASK = (
    "Fix discount calculation: subtract the given percentage of the price, "
    "not the percentage number directly."
)
DIAGNOSIS = {
    "error_type": "test_failure",
    "root_cause": "discount subtracts percent directly instead of calculating percentage",
    "error_message": "independent discount tests fail",
}


def run_test():
    return WorkspaceManager(ROOT).run_command(["python", TEST])


async def main():
    print("=== PIKA WRONG-CODE RETEST: NEW FILENAME ===")
    print("Target:", TARGET)
    print("Learning DB:", DB)

    if ROOT.exists():
        shutil.rmtree(ROOT)
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / TARGET).write_text(BROKEN, encoding="utf-8")
    (ROOT / TEST).write_text(TEST_CODE, encoding="utf-8")

    baseline = run_test()
    print("[BASELINE] success =", baseline.get("success"))
    assert baseline.get("success") is False, "Expected wrong code to fail"
    print("[PASS] Wrong-code failure reproduced")

    # First try the solution learned during the previous real repair.
    learned = []
    if DB.exists():
        try:
            data = json.loads(DB.read_text(encoding="utf-8"))
            for exp in data.get("experiences", []):
                if exp.get("trusted") and exp.get("success"):
                    solution = str(exp.get("solution", "")).strip()
                    if solution and solution not in learned:
                        learned.append(solution)
        except Exception as exc:
            print("[MEMORY] read error:", exc)

    print("[MEMORY] trusted solutions available =", len(learned))

    controller = Phase33Controller(
        ROOT, max_candidates=3, learning_memory_path=DB
    )

    if learned:
        print("[MEMORY] Trying previously learned solution(s) first")
        result = controller.repair(
            diagnosis=DIAGNOSIS,
            relative_path=TARGET,
            old_text="return price - percent",
            candidates=learned[:3],
            test_path=TEST,
            task=TASK,
        )
    else:
        result = {"success": False, "stage": "memory_miss"}

    if result.get("success") is True:
        print("[RESULT] MEMORY REPAIR SUCCEEDED; Cohere not needed")
    else:
        print("[RESULT] Memory repair unavailable/failed; trying Cohere fallback")
        generator = RepairCandidateGenerator(
            max_candidates=3, workspace_root=ROOT
        )
        worker_plan = {
            "files": [{"path": TARGET, "content": (ROOT / TARGET).read_text(encoding="utf-8")}],
            "commands": [["python", TEST]],
        }
        generated = await generator.generate_from_failure(
            task=TASK,
            diagnosis=DIAGNOSIS,
            worker_output=json.dumps(worker_plan),
            previous_feedback=str(baseline.get("stderr", "")),
        )
        print("[COHERE FALLBACK] success =", generated.get("success"))
        print("[COHERE FALLBACK] provider =", generated.get("provider"))
        print("[COHERE FALLBACK] candidates =", generated.get("candidates"))
        assert generated.get("success") is True, "Cohere fallback generation failed"

        result = controller.repair(
            diagnosis=DIAGNOSIS,
            relative_path=generated["target_path"],
            old_text=generated["old_text"],
            candidates=generated["candidates"],
            test_path=generated["test_path"],
            task=TASK,
        )

    print("[REPAIR] success =", result.get("success"))
    print("[REPAIR] stage =", result.get("stage"))
    assert result.get("success") is True, "Repair failed"

    final = run_test()
    print("[INDEPENDENT TEST] success =", final.get("success"))
    print("[INDEPENDENT TEST] stdout =", final.get("stdout", ""))
    print("[INDEPENDENT TEST] stderr =", final.get("stderr", ""))
    assert final.get("success") is True, "Repaired code failed independent tests"

    print("PIKA WRONG-CODE RETEST: PASS")


if __name__ == "__main__":
    asyncio.run(main())
