from pathlib import Path
import shutil
import sys

def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"{label}: expected one match, found {count}. No patch applied."
        )
    return text.replace(old, new, 1)

healer = Path("core/self_healing.py")
controller = Path("core/phase33_controller.py")
brain = Path("core/brain.py")

h = healer.read_text()
c = controller.read_text()
b = brain.read_text()

# Expose evidence already produced by the existing self-healing engine.
old = '''                "final_candidate": candidate,
                "validation": validation,
                "test": test,
                "commit": commit,
'''
new = '''                "final_candidate": candidate,
                "accepted_candidate": candidate,
                "validation": validation,
                "test": test,
                "test_passed": bool(test.get("success")),
                "validation_passed": bool(validation.get("success")),
                "commit": commit,
                "commit_passed": bool(commit.get("success")),
'''
h2 = replace_once(h, old, new, "SelfHealingEngine success result")

# Surface the existing engine result through the Phase 33 boundary.
old = '''            "diagnosis": diagnosis,
            "repair": result,
'''
new = '''            "diagnosis": diagnosis,
            "repair": result,
            "accepted_candidate": result.get("final_candidate"),
            "test_passed": bool(
                result.get("test_passed") is True
                and result.get("validation_passed") is True
                and result.get("commit_passed") is True
            ),
'''
c2 = replace_once(c, old, new, "Phase33Controller result")

# Read the exact accepted candidate and evidence from the controller result.
old = '''    repair = outcome.get("repair", {})
    if not isinstance(repair, dict):
        return False

    if repair.get("test_passed") is not True:
        print("[PHASE35] No explicit test-pass evidence; save skipped.")
        return False

    accepted = repair.get("accepted_candidate")
'''
new = '''    repair = outcome.get("repair", {})
    if not isinstance(repair, dict):
        return False

    if outcome.get("test_passed") is not True:
        print("[PHASE35] Independent test/validation/commit evidence missing; save skipped.")
        return False

    accepted = outcome.get("accepted_candidate") or repair.get("final_candidate")
'''
b2 = replace_once(b, old, new, "Phase35 saver evidence")

# Ensure all files parse before touching any production file.
for name, content in (
    ("core/self_healing.py", h2),
    ("core/phase33_controller.py", c2),
    ("core/brain.py", b2),
):
    compile(content, name, "exec")

backups = [
    (healer, Path("core/self_healing.py.phase35-result-backup")),
    (controller, Path("core/phase33_controller.py.phase35-result-backup")),
    (brain, Path("core/brain.py.phase35-result-backup")),
]

for original_path, backup_path in backups:
    if backup_path.exists():
        backup_path = backup_path.with_name(
            backup_path.name + ".2"
        )
    shutil.copy2(original_path, backup_path)
    print("BACKUP:", backup_path)

try:
    healer.write_text(h2)
    controller.write_text(c2)
    brain.write_text(b2)

    for path in (healer, controller, brain):
        compile(path.read_text(), str(path), "exec")
except Exception:
    for original_path, backup_path in backups:
        candidates = [
            backup_path,
            backup_path.with_name(backup_path.name + ".2"),
        ]
        existing = next((p for p in candidates if p.exists()), None)
        if existing:
            shutil.copy2(existing, original_path)
    raise

print("PHASE 35 RESULT EVIDENCE PATCH INSTALLED")
