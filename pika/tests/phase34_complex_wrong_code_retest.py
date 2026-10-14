from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path

from core.phase34_learning_repair import Phase34LearningRepair
from core.repair_candidate_generator import RepairCandidateGenerator
from core.phase33_controller import Phase33Controller
from workspace.manager import WorkspaceManager

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE / "workspace" / "__phase34_complex_retest__"
DB = BASE / "data" / "__phase34_complex_repair__" / "learning_engine.json"

TARGET = "checkout_retest.py"
TEST = "test_checkout_retest.py"

BROKEN = '''def checkout(items, discount_percent=0, tax_rate=0.08, shipping=10):
    subtotal = 0
    for item in items:
        subtotal += item.get("price", 0)

    discount = discount_percent
    taxable = subtotal + discount
    tax = taxable * tax_rate

    if subtotal > 100:
        shipping = 10
    else:
        shipping = 0

    total = subtotal + discount + tax - shipping

    return {
        "subtotal": total,
        "discount": discount,
        "tax": tax,
        "shipping": shipping,
        "total": subtotal,
    }
'''

TEST_CODE = '''from checkout_retest import checkout

def close(a, b):
    assert abs(a - b) < 0.0001, f"expected {b}, got {a}"

def test_quantities_and_totals():
    r = checkout([
        {"price": 20, "quantity": 2},
        {"price": 10, "quantity": 3},
    ], discount_percent=10, tax_rate=0.10, shipping=5)
    close(r["subtotal"], 70)
    close(r["discount"], 7)
    close(r["tax"], 6.3)
    close(r["shipping"], 5)
    close(r["total"], 74.3)

def test_free_shipping():
    r = checkout(
        [{"price": 60, "quantity": 2}],
        discount_percent=0, tax_rate=0, shipping=8
    )
    close(r["subtotal"], 120)
    close(r["shipping"], 0)
    close(r["total"], 120)

def test_empty_and_regular_cart():
    r = checkout(
        [{"price": 25, "quantity": 2}],
        discount_percent=0, tax_rate=0.08, shipping=5
    )
    close(r["subtotal"], 50)
    close(r["discount"], 0)
    close(r["tax"], 4)
    close(r["shipping"], 5)
    close(r["total"], 59)

    e = checkout([], discount_percent=0, tax_rate=0, shipping=5)
    close(e["subtotal"], 0)
    close(e["discount"], 0)
    close(e["tax"], 0)
    close(e["shipping"], 5)
    close(e["total"], 5)

if __name__ == "__main__":
    test_quantities_and_totals()
    test_free_shipping()
    test_empty_and_regular_cart()
    print("COMPLEX RETEST PASS")
'''

TASK = (
    "Repair the checkout function: calculate subtotal using price times "
    "quantity, apply percentage discount, calculate tax after discount, "
    "make shipping free at original subtotal >= 100, calculate final total, "
    "return correct fields, and handle empty carts."
)

DIAGNOSIS = {
    "error_type": "test_failure",
    "root_cause": (
        "checkout has multiple interacting defects in quantity handling, "
        "percentage discount, tax base, shipping threshold and returned totals"
    ),
    "error_message": (
        "independent checkout tests fail for quantities, discount, tax, "
        "shipping, empty cart and output fields"
    ),
}


def run_test():
    return WorkspaceManager(ROOT).run_command(["python", TEST])


async def main():
    print("=" * 60)
    print("PIKA COMPLEX RE-TEST — NEW FILENAMES")
    print("Learning DB:", DB)
    print("Workspace:", ROOT)
    print("=" * 60)

    if ROOT.exists():
        shutil.rmtree(ROOT)
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / TARGET).write_text(BROKEN, encoding="utf-8")
    (ROOT / TEST).write_text(TEST_CODE, encoding="utf-8")

    baseline = run_test()
    print("[BASELINE] success =", baseline.get("success"))
    assert baseline.get("success") is False, "Broken baseline should fail"
    print("[PASS] Same class of complex bug reproduced")

    controller = Phase33Controller(
        ROOT, max_candidates=3, learning_memory_path=DB
    )

    learned = []
    if DB.exists():
        learner = Phase34LearningRepair(ROOT, memory_path=DB)
        learned = learner.lookup_candidates(
            task=TASK,
            error_type="test_failure",
            root_cause=DIAGNOSIS["root_cause"],
            error_message=DIAGNOSIS["error_message"],
            limit=3,
        )

    print("[MEMORY] compatible learned records =", len(learned))
    repair = {"success": False, "stage": "memory_miss"}

    if learned:
        candidates = [
            str(x.get("solution", "")).strip()
            for x in learned
            if str(x.get("solution", "")).strip()
        ]
        print("[MEMORY] candidate methods =", [
            x.get("method") for x in learned
        ])

        if candidates:
            print("[MEMORY] trying learned solutions first")
            repair = controller.repair(
                diagnosis=DIAGNOSIS,
                relative_path=TARGET,
                old_text=BROKEN,
                candidates=candidates,
                test_path=TEST,
                task=TASK,
            )
            print("[MEMORY REPAIR] success =", repair.get("success"))

    if repair.get("success") is True:
        print("[RESULT] learned repair succeeded; Cohere not needed")
    else:
        print("[FALLBACK] memory missed or repair failed; asking Cohere")
        generator = RepairCandidateGenerator(
            max_candidates=3, workspace_root=ROOT
        )
        plan = {
            "files": [{
                "path": TARGET,
                "content": (ROOT / TARGET).read_text(encoding="utf-8"),
            }],
            "commands": [["python", TEST]],
        }
        generated = await generator.generate_from_failure(
            task=TASK,
            diagnosis=DIAGNOSIS,
            worker_output=json.dumps(plan),
            previous_feedback=str(baseline.get("stderr", "")),
        )
        print("[COHERE] success =", generated.get("success"))
        print("[COHERE] provider =", generated.get("provider"))
        print("[COHERE] candidates =", generated.get("candidates"))
        assert generated.get("success") is True, "Candidate generation failed"

        repair = controller.repair(
            diagnosis=DIAGNOSIS,
            relative_path=generated["target_path"],
            old_text=generated["old_text"],
            candidates=generated["candidates"],
            test_path=generated["test_path"],
            task=TASK,
        )
        print("[FALLBACK REPAIR] success =", repair.get("success"))

    final = run_test()
    print("[INDEPENDENT TEST] success =", final.get("success"))
    print("[INDEPENDENT TEST] stdout =", final.get("stdout", ""))
    print("[INDEPENDENT TEST] stderr =", final.get("stderr", ""))

    assert repair.get("success") is True, "Repair did not succeed"
    assert final.get("success") is True, "Independent tests failed"

    print("=" * 60)
    print("PIKA COMPLEX RE-TEST: PASS")
    print("Repair route:", repair.get("stage"))
    print("Independent tests passed on new filenames")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
