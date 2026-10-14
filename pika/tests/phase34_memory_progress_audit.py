from __future__ import annotations

import asyncio
import json
from pathlib import Path

from core.phase34_learning_repair import Phase34LearningRepair
from core.repair_candidate_generator import RepairCandidateGenerator
from core.phase33_controller import Phase33Controller
from workspace.manager import WorkspaceManager

BASE = Path(__file__).resolve().parents[1]
DBS = [
    BASE / "data" / "learning_engine.json",
    BASE / "data" / "__phase34_wrong_code_repair__" / "learning_engine.json",
    BASE / "data" / "__phase34_complex_repair__" / "learning_engine.json",
]

ROOT = BASE / "workspace" / "__phase34_new_learning_tests__"

TASKS = [
    {
        "name": "inventory",
        "target": "inventory_value_new.py",
        "test": "test_inventory_value_new.py",
        "task": (
            "Fix inventory valuation: stock value must account for quantity "
            "and unit price; reorder flag must be true when quantity is below "
            "the reorder threshold."
        ),
        "diagnosis": {
            "error_type": "test_failure",
            "root_cause": (
                "inventory calculation ignores quantity and uses an incorrect "
                "reorder threshold comparison"
            ),
            "error_message": "inventory valuation and reorder tests fail",
        },
        "broken": '''def inventory_value(items, reorder_at=5):
    total = 0
    reorder = []
    for item in items:
        total += item.get("price", 0)
        if item.get("quantity", 0) > reorder_at:
            reorder.append(item.get("sku"))
    return {"total_value": total, "reorder": reorder}
''',
        "tests": '''from inventory_value_new import inventory_value

def test_inventory():
    r = inventory_value([
        {"sku": "A", "price": 12, "quantity": 3},
        {"sku": "B", "price": 5, "quantity": 10},
    ], reorder_at=5)
    assert r["total_value"] == 86, r
    assert r["reorder"] == ["A"], r

if __name__ == "__main__":
    test_inventory()
    print("INVENTORY TEST PASS")
''',
    },
    {
        "name": "commission",
        "target": "commission_payout_new.py",
        "test": "test_commission_payout_new.py",
        "task": (
            "Fix salesperson payout calculation: commission is a percentage "
            "of sales, and payout equals base pay plus commission."
        ),
        "diagnosis": {
            "error_type": "test_failure",
            "root_cause": (
                "commission percentage is treated as a flat amount and "
                "payout combines base pay and commission incorrectly"
            ),
            "error_message": "commission and payout tests fail",
        },
        "broken": '''def payout(sales, commission_percent, base_pay):
    commission = commission_percent
    total = sales - commission
    return {"commission": commission, "payout": total - base_pay}
''',
        "tests": '''from commission_payout_new import payout

def test_payout():
    r = payout(2000, 5, 300)
    assert r["commission"] == 100, r
    assert r["payout"] == 400, r

if __name__ == "__main__":
    test_payout()
    print("COMMISSION TEST PASS")
''',
    },
]


def audit_memory():
    print("\\n" + "=" * 60)
    print("READ-ONLY PIKA MEMORY AUDIT")
    print("=" * 60)

    for path in DBS:
        print("\\nDATABASE:", path)
        if not path.exists():
            print("STATUS: NOT FOUND")
            continue

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print("STATUS: READ ERROR:", exc)
            continue

        records = data.get("experiences", [])
        print("Experiences:", len(records))
        print("Patterns:", len(data.get("patterns", [])) if isinstance(data.get("patterns"), list) else len(data.get("patterns", {})))

        trusted = [
            x for x in records
            if x.get("trusted") is True and x.get("success") is True
        ]
        failed = [
            x for x in records
            if x.get("success") is False or x.get("trusted") is False
        ]
        print("Trusted successful records:", len(trusted))
        print("Failed/untrusted records:", len(failed))

        for item in records[-3:]:
            print("RECENT:", json.dumps({
                "task": item.get("task"),
                "method": item.get("method"),
                "solution": item.get("solution"),
                "success": item.get("success"),
                "trusted": item.get("trusted"),
                "verification": item.get("verification"),
            }, ensure_ascii=False)[:900])


async def run_one(spec):
    root = ROOT / spec["name"]
    root.mkdir(parents=True, exist_ok=True)

    target = spec["target"]
    test = spec["test"]
    source_path = root / target
    test_path = root / test
    source_path.write_text(spec["broken"], encoding="utf-8")
    test_path.write_text(spec["tests"], encoding="utf-8")

    manager = WorkspaceManager(root)

    def run_test():
        return manager.run_command(["python", test])

    baseline = run_test()
    print("\\n" + "-" * 60)
    print("NEW PROBLEM:", spec["name"].upper())
    print("Baseline success:", baseline.get("success"))
    assert baseline.get("success") is False, "Broken baseline unexpectedly passed"

    # Search saved memory before invoking the external generator.
    learner = Phase34LearningRepair(
        root,
        memory_path=DBS[0],
    )
    learned = learner.lookup_candidates(
        task=spec["task"],
        error_type=spec["diagnosis"]["error_type"],
        root_cause=spec["diagnosis"]["root_cause"],
        error_message=spec["diagnosis"]["error_message"],
        limit=3,
    )

    print("[MEMORY] compatible records:", len(learned))
    candidates = [
        str(x.get("solution", "")).strip()
        for x in learned
        if str(x.get("solution", "")).strip()
    ]

    controller = Phase33Controller(root, max_candidates=3)
    repair = {"success": False}

    if candidates:
        print("[MEMORY] trying saved solution first")
        repair = controller.repair(
            diagnosis=spec["diagnosis"],
            relative_path=target,
            old_text=spec["broken"].strip(),
            candidates=candidates,
            test_path=test,
            task=spec["task"],
        )
        print("[MEMORY REPAIR] success:", repair.get("success"))
    else:
        print("[MEMORY] miss; will use Cohere fallback")

    if repair.get("success") is not True:
        generator = RepairCandidateGenerator(
            max_candidates=3,
            workspace_root=root,
        )
        plan = {
            "files": [{
                "path": target,
                "content": source_path.read_text(encoding="utf-8"),
            }],
            "commands": [["python", test]],
        }
        generated = await generator.generate_from_failure(
            task=spec["task"],
            diagnosis=spec["diagnosis"],
            worker_output=json.dumps(plan),
            previous_feedback=str(baseline.get("stderr", "")),
        )
        print("[COHERE] success:", generated.get("success"))
        print("[COHERE] provider:", generated.get("provider"))
        assert generated.get("success") is True, "Fallback generation failed"

        repair = controller.repair(
            diagnosis=spec["diagnosis"],
            relative_path=generated["target_path"],
            old_text=generated["old_text"],
            candidates=generated["candidates"],
            test_path=generated["test_path"],
            task=spec["task"],
        )
        print("[FALLBACK REPAIR] success:", repair.get("success"))

    final = run_test()
    print("[FINAL TEST] success:", final.get("success"))
    print("[FINAL TEST] stdout:", final.get("stdout", ""))
    print("[FINAL TEST] stderr:", final.get("stderr", ""))

    if repair.get("success") is True and final.get("success") is True:
        print("RESULT:", spec["name"], "PASS")
        return True

    print("RESULT:", spec["name"], "FAIL")
    return False


async def main():
    audit_memory()

    if ROOT.exists():
        import shutil
        shutil.rmtree(ROOT)
    ROOT.mkdir(parents=True, exist_ok=True)

    results = []
    for spec in TASKS:
        try:
            results.append((spec["name"], await run_one(spec)))
        except Exception as exc:
            print("[TEST ERROR]", spec["name"], repr(exc))
            results.append((spec["name"], False))

    print("\\n" + "=" * 60)
    print("NEW PROBLEM RESULTS")
    for name, passed in results:
        print(name, "PASS" if passed else "FAIL")
    print("Passed:", sum(ok for _, ok in results), "/", len(results))
    print("Note: this audit reads saved DBs; new repairs use a separate workspace.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
