from pathlib import Path
import shutil
import sys

path = Path("core/brain.py")
src = path.read_text()
original = src

helper_marker = "# PHASE35_VERIFIED_LEARNING_HELPER"
helper = r'''
# PHASE35_VERIFIED_LEARNING_HELPER
def _phase35_store_verified_repair(memory, task, candidates, repair_result, diagnosis):
    """Persist only the exact candidate with explicit successful test evidence."""
    if not isinstance(repair_result, dict) or not repair_result.get("success"):
        return False

    repair = repair_result.get("repair", {})
    if not isinstance(repair, dict):
        repair = {}

    evidence_ok = (
        repair.get("test_passed") is True
        or repair_result.get("test_passed") is True
        or repair.get("tests_passed") is True
        or repair_result.get("tests_passed") is True
    )
    if not evidence_ok:
        print("[PIKA PHASE 35] save skipped: explicit test evidence missing.")
        return False

    accepted = None
    for obj in (repair, repair_result):
        for key in (
            "accepted_candidate", "candidate", "selected_candidate",
            "solution", "code",
        ):
            value = obj.get(key)
            if isinstance(value, str) and value in candidates:
                accepted = value
                break
        if accepted is not None:
            break

        for key in ("candidate_index", "selected_index"):
            index = obj.get(key)
            if isinstance(index, int) and not isinstance(index, bool):
                if 0 <= index < len(candidates):
                    accepted = candidates[index]
                    break
        if accepted is not None:
            break

    if not isinstance(accepted, str) or not accepted.strip():
        print("[PIKA PHASE 35] save skipped: exact accepted candidate unavailable.")
        return False

    root_cause = str((diagnosis or {}).get("root_cause", ""))
    try:
        memory.remember(
            intent=str(task),
            code=accepted,
            language="python",
            description="Repair retained after explicit Phase 33 test success.",
            tags=["repair", "phase33", "verified"],
            preconditions=[root_cause] if root_cause else [],
            verification="test_verified",
            evidence=[
                "Phase 33 reported success.",
                "Explicit test_passed/tests_passed evidence was true.",
                "Exact accepted candidate matched the submitted candidates.",
            ],
        )
        print("[PIKA PHASE 35] verified repair saved to semantic memory.")
        return True
    except Exception as exc:
        print("[PIKA PHASE 35] memory save failed safely:", exc)
        return False
'''

if helper_marker not in src:
    anchor = "class PIKABrain:"
    if anchor not in src:
        print("ERROR: PIKABrain class anchor missing; no changes made.")
        sys.exit(1)
    src = src.replace(anchor, helper + "\n\n" + anchor, 1)

# Add persistence calls to the existing Phase 34 learned-repair success
# and Phase 33 generated/combined-repair success branches.
call1 = (
    'if repair_result.get("success"):'
    '\n                                    result["success"] = True'
)
replacement1 = (
    'if repair_result.get("success"):'
    '\n                                    _phase35_store_verified_repair('
    '\n                                        self.semantic_code_memory, task, learned_code[:3],'
    '\n                                        repair_result, phase33_diagnosis'
    '\n                                    )'
    '\n                                    result["success"] = True'
)

if call1 in src and "_phase35_store_verified_repair(\n                                        self.semantic_code_memory, task, learned_code[:3]" not in src:
    src = src.replace(call1, replacement1, 1)

# Find the generated-repair success branch by its following result handling.
call2 = (
    'if repair_result.get("success"):'
    '\n'
)
needle = '_phase35_store_verified_repair(\n                                        self.semantic_code_memory, task, combined_candidates'
if needle not in src:
    pos = src.find('result["phase33_repair"]')
    if pos >= 0:
        success_pos = src.find('if repair_result.get("success"):', pos)
        if success_pos >= 0:
            line_end = src.find("\n", success_pos)
            indent = src[success_pos:success_pos + len(src[success_pos:]) - len(src[success_pos:].lstrip())]
            body_indent = indent + "    "
            call = (
                "\n" + body_indent + "_phase35_store_verified_repair("
                "\n" + body_indent + "    self.semantic_code_memory, task, combined_candidates,"
                "\n" + body_indent + "    repair_result, phase33_diagnosis"
                "\n" + body_indent + ")"
            )
            src = src[:line_end] + call + src[line_end:]

if src == original:
    print("No changes made. The expected repair anchors may differ.")
    print('Inspect: sed -n "710,875p" core/brain.py')
    sys.exit(1)

backup = Path("core/brain.py.phase35-loop-backup")
if backup.exists():
    backup = Path("core/brain.py.phase35-loop-backup-2")

shutil.copy2(path, backup)
path.write_text(src)
print("PATCHED:", path)
print("BACKUP:", backup)
