from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path

from core.repair_candidate_generator import RepairCandidateGenerator
from core.phase33_controller import Phase33Controller
from workspace.manager import WorkspaceManager

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE / "workspace" / "__phase34_complex_repair__"
DB = BASE / "data" / "__phase34_complex_repair__" / "learning_engine.json"

TARGET = "checkout.py"
TEST = "test_checkout.py"

# Deliberately broken implementation with multiple interacting bugs.
BROKEN_SOURCE = '''def checkout(items, discount_percent=0, tax_rate=0.08, shipping=10):
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

TEST_SOURCE = '''from checkout import checkout

def close(a, b):
    assert abs(a - b) < 0.0001, f"expected {b}, got {a}"

def test_quantities_and_totals():
    result = checkout([
        {"price": 20, "quantity": 2},
        {"price": 10, "quantity": 3},
    ], discount_percent=10, tax_rate=0.10, shipping=5)

    close(result["subtotal"], 70)
    close(result["discount"], 7)
    close(result["tax"], 6.3)
    close(result["shipping"], 5)
    close(result["total"], 74.3)

def test_free_shipping_threshold():
    result = checkout(
        [{"price": 60, "quantity": 2}],
        discount_percent=0,
        tax_rate=0,
        shipping=8,
    )
    close(result["subtotal"], 120)
    close(result["shipping"], 0)
    close(result["total"], 120)

def test_no_discount_and_empty_cart():
    result = checkout(
        [{"price": 25, "quantity": 2}],
        discount_percent=0,
        tax_rate=0.08,
        shipping=5,
    )
    close(result["subtotal"], 50)
    close(result["discount"], 0)
    close(result["tax"], 4)
    close(result["shipping"], 5)
    close(result["total"], 59)

    empty = checkout([], discount_percent=0, tax_rate=0, shipping=5)
    close(empty["subtotal"], 0)
    close(empty["discount"], 0)
    close(empty["tax"], 0)
    close(empty["shipping"], 5)
    close(empty["total"], 5)

if __name__ == "__main__":
    test_quantities_and_totals()
    test_free_shipping_threshold()
    test_no_discount_and_empty_cart()
    print("ALL CHECKOUT TESTS PASS")
'''

TASK = """
Repair the entire checkout implementation in checkout.py.

Required contract:
- Each item has price and quantity; subtotal is sum(price * quantity).
- discount_percent is a percentage from 0 to 100, not a currency amount.
- discount = subtotal * discount_percent / 100.
- tax is calculated on subtotal minus discount.
- Shipping is free when the original subtotal is at least 100.
- Otherwise use the supplied shipping amount.
- total = subtotal - discount + tax + shipping.
- Return correct subtotal, discount, tax, shipping and total fields.
- Handle an empty cart correctly.
- Preserve the checkout(items, discount_percent=0, tax_rate=0.08, shipping=10) interface.
Pass every independent test in test_checkout.py.
"""

DIAGNOSIS = {
    "error_type": "test_failure",
    "root_cause": (
        "multiple checkout logic defects: quantities ignored, percentage "
        "discount treated as a currency amount, discount added instead "
        "of subtracted, incorrect tax base, inverted shipping threshold, "
        "and returned totals mapped to incorrect fields"
    ),
    "error_message": (
        "independent checkout tests fail across quantities, discount, tax, "
        "shipping threshold, empty cart and result fields"
    ),
}


def run_test():
    return WorkspaceManager(ROOT).run_command(["python", TEST])


async def main():
    print("=" * 60)
    print("PIKA COMPLEX WRONG-CODE REPAIR TEST")
    print("=" * 60)
    print("Workspace:", ROOT)
    print("Dedicated learning DB:", DB)

    if ROOT.exists():
        shutil.rmtree(ROOT)
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / TARGET).write_text(BROKEN_SOURCE, encoding="utf-8")
    (ROOT / TEST).write_text(TEST_SOURCE, encoding="utf-8")

    baseline = run_test()
    print("\n[BASELINE] success =", baseline.get("success"))
    print("[BASELINE] stderr =", baseline.get("stderr", ""))

    assert baseline.get("success") is False, (
        "FAIL: deliberately broken checkout unexpectedly passed"
    )
    print("[PASS] Complex baseline failure reproduced")

    generator = RepairCandidateGenerator(
        max_candidates=3,
        workspace_root=ROOT,
    )

    plan = {
        "files": [
            {
                "path": TARGET,
                "content": (ROOT / TARGET).read_text(encoding="utf-8"),
            }
        ],
        "commands": [["python", TEST]],
    }

    print("\n[COHERE] Requesting repair candidates for multiple defects...")
    generated = await generator.generate_from_failure(
        task=TASK,
        diagnosis=DIAGNOSIS,
        worker_output=json.dumps(plan),
        previous_feedback=str(baseline.get("stderr", "")),
    )

    print("[GENERATOR] success =", generated.get("success"))
    print("[GENERATOR] provider =", generated.get("provider"))
    print("[GENERATOR] error =", generated.get("error"))
    print("[GENERATOR] target =", generated.get("target_path"))
    print("[GENERATOR] candidates =", generated.get("candidates"))

    assert generated.get("success") is True, (
        "FAIL: candidate generation failed"
    )
    assert generated.get("target_path")
    assert generated.get("old_text")
    assert generated.get("test_path")
    assert generated.get("candidates")

    controller = Phase33Controller(
        ROOT,
        max_candidates=3,
        learning_memory_path=DB,
    )

    print("\n[PHASE 33] Applying candidates with independent test verification...")
    repair = controller.repair(
        diagnosis=DIAGNOSIS,
        relative_path=generated["target_path"],
        old_text=generated["old_text"],
        candidates=generated["candidates"],
        test_path=generated["test_path"],
        task=TASK,
    )

    print("[REPAIR] success =", repair.get("success"))
    print("[REPAIR] stage =", repair.get("stage"))
    print("[REPAIR] details =", repair)

    final = run_test()
    print("\n[FINAL TEST] success =", final.get("success"))
    print("[FINAL TEST] stdout =", final.get("stdout", ""))
    print("[FINAL TEST] stderr =", final.get("stderr", ""))

    assert repair.get("success") is True and final.get("success") is True, (
        "COMPLEX REPAIR FAILED: inspect logs above; no PASS will be claimed"
    )

    print("\n" + "=" * 60)
    print("PIKA COMPLEX WRONG-CODE TEST: PASS")
    print("Verified: multiple defects repaired")
    print("Verified: independent checkout tests passed")
    print("Verified: production learning DB was not selected")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
