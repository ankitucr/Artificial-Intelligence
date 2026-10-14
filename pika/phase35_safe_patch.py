import ast
import shutil
from pathlib import Path

path = Path("core/brain.py")
original = path.read_text()
tree = ast.parse(original)
lines = original.splitlines(keepends=True)

marker = "PHASE35_VERIFIED_LOOP_V2"

if marker in original:
    print("Phase 35 verified loop already installed.")
    raise SystemExit(0)

helper = '''
# PHASE35_VERIFIED_LOOP_V2
def _phase35_save_repair(memory, task, candidates, outcome, diagnosis):
    """Store an accepted candidate only with explicit test evidence."""
    if not isinstance(outcome, dict) or outcome.get("success") is not True:
        return False

    repair = outcome.get("repair", {})
    if not isinstance(repair, dict):
        return False

    if repair.get("test_passed") is not True:
        print("[PHASE35] No explicit test-pass evidence; save skipped.")
        return False

    accepted = repair.get("accepted_candidate")
    if not isinstance(accepted, str) or accepted not in candidates:
        print("[PHASE35] Exact accepted candidate unknown; save skipped.")
        return False

    try:
        memory.remember(
            intent=str(task),
            code=accepted,
            language="python",
            description="Phase 33 independently tested repair",
            tags=["phase33", "repair"],
            preconditions=[
                str(diagnosis.get("root_cause", ""))
            ],
            verification="test_verified",
            evidence=[
                "Phase 33 success",
                "Phase 33 test_passed=True",
                "Accepted candidate matched submitted code",
            ],
        )
        print("[PHASE35] Verified repair saved.")
        return True
    except Exception as exc:
        print("[PHASE35] Save failed safely:", exc)
        return False
'''

# Find the two repair-success branches inside the real Brain class.
matches = []

for node in ast.walk(tree):
    if not isinstance(node, ast.If):
        continue

    condition = ast.get_source_segment(original, node.test)
    if condition != 'repair_result.get("success")':
        continue

    if not node.body:
        continue

    body_text = ast.get_source_segment(original, node)
    if "result[" not in body_text:
        continue

    matches.append(node)

if len(matches) < 2:
    print("ERROR: Expected two repair-success branches; found", len(matches))
    print("No changes made.")
    raise SystemExit(1)

# The first branch is Phase34 learned repair; second is generated repair.
matches.sort(key=lambda node: node.lineno)
selected = matches[:2]

for index, node in reversed(list(enumerate(selected))):
    first_statement = node.body[0]
    indent = " " * first_statement.col_offset
    candidates = "learned_code[:3]" if index == 0 else "combined_candidates"

    addition = (
        indent + "_phase35_save_repair(\n"
        + indent + "    self.semantic_code_memory,\n"
        + indent + "    task,\n"
        + indent + "    " + candidates + ",\n"
        + indent + "    repair_result,\n"
        + indent + "    phase33_diagnosis,\n"
        + indent + ")\n"
    )
    lines.insert(first_statement.lineno - 1, addition)

updated = "".join(lines)

# Insert helper before PIKABrain class.
class_anchor = "class PIKABrain:"
if class_anchor not in updated:
    print("ERROR: PIKABrain class not found; no changes made.")
    raise SystemExit(1)

updated = updated.replace(
    class_anchor,
    helper + "\n\n" + class_anchor,
    1,
)

# Compile before writing to production file.
compile(updated, str(path), "exec")

backup = Path("core/brain.py.phase35-safe-backup")
shutil.copy2(path, backup)

try:
    path.write_text(updated)
    compile(path.read_text(), str(path), "exec")
except Exception:
    shutil.copy2(backup, path)
    print("ERROR: Patch rolled back automatically.")
    raise

print("PHASE 35 PATCH INSTALLED")
print("BACKUP:", backup)
