import sys
import json
import subprocess
from pathlib import Path

from core.phase33_controller import Phase33Controller
from core.semantic_code_memory import SemanticCodeMemory
from core.brain import _phase35_save_repair

root = Path("workspace/__phase35_live_repair__").resolve()
root.mkdir(parents=True, exist_ok=True)

(root / "discount.py").write_text(
    "def discount(price, percent):\n"
    "    return price - percent\n",
    encoding="utf-8",
)
(root / "test_discount.py").write_text(
    "from discount import discount\n"
    "assert discount(100, 20) == 80\n"
    "assert discount(200, 10) == 180\n"
    "assert discount(50, 0) == 50\n"
    "print('INDEPENDENT DISCOUNT TEST PASS')\n",
    encoding="utf-8",
)

baseline = subprocess.run(
    [sys.executable, "test_discount.py"],
    cwd=root, capture_output=True, text=True,
)
print("BROKEN CODE TEST RETURN:", baseline.returncode)
if baseline.returncode == 0:
    raise SystemExit("ERROR: deliberately broken code unexpectedly passed")

candidate = "    return price * (1 - percent / 100)"
controller = Phase33Controller(root, max_candidates=3)
result = controller.repair(
    diagnosis={
        "error_type": "test_failure",
        "root_cause": "discount percentage calculation is incorrect",
        "error_message": "independent discount assertions failed",
    },
    relative_path="discount.py",
    old_text="    return price - percent",
    candidates=[candidate],
    test_path="test_discount.py",
    task="Fix percentage discount calculation",
)

print("\nPHASE 33 RESULT:")
print(json.dumps(result, indent=2, ensure_ascii=False))
if result.get("success") is not True:
    raise SystemExit("REPAIR FAILED; memory save skipped")

check = subprocess.run(
    [sys.executable, "test_discount.py"],
    cwd=root, capture_output=True, text=True,
)
print("\nFINAL TEST:", check.stdout, check.stderr)
if check.returncode != 0:
    raise SystemExit("INDEPENDENT TEST FAILED; memory save skipped")

memory = SemanticCodeMemory(Path("data/semantic_code_memory.json"))
saved = _phase35_save_repair(
    memory,
    "Fix percentage discount calculation",
    [candidate],
    result,
    {"root_cause": "discount percentage calculation is incorrect"},
)
if not saved:
    raise SystemExit("REPAIR PASSED BUT MEMORY SAVE FAILED")

reloaded = SemanticCodeMemory(Path("data/semantic_code_memory.json"))
hits = reloaded.retrieve("Fix percentage discount calculation", verified_only=True)
match = next((v for v in hits if v.get("code") == candidate), None)
if match is None:
    raise SystemExit("SAVE RELOAD CHECK FAILED")

print("\nVERIFIED SAVED MEMORY:")
print(json.dumps({
    "intent": match["intent"],
    "code": match["code"],
    "verification": match["verification"],
    "evidence": match["evidence"],
}, indent=2, ensure_ascii=False))
print("\nLIVE REPAIR + MEMORY SAVE + RELOAD: PASS")
