import ast
import shutil
from pathlib import Path

p = Path("core/brain.py")
src = p.read_text(encoding="utf-8")
tree = ast.parse(src)

helper = next((n for n in tree.body
               if isinstance(n, ast.FunctionDef)
               and n.name == "_phase35_save_repair"), None)
brain = next((n for n in tree.body
              if isinstance(n, ast.ClassDef)
              and n.name == "PIKABrain"), None)

if helper is None or brain is None:
    raise RuntimeError("Required Brain/helper not found; no changes made.")

if "from core.learning_engine import LearningEngine" in src:
    print("LearningEngine import already exists; checking integration.")
else:
    src = src.replace(
        "from core.semantic_code_memory import SemanticCodeMemory",
        "from core.semantic_code_memory import SemanticCodeMemory\n"
        "from core.learning_engine import LearningEngine",
        1,
    )

# Reparse after import change and locate helper accurately.
tree = ast.parse(src)
helper = next(n for n in tree.body
              if isinstance(n, ast.FunctionDef)
              and n.name == "_phase35_save_repair")

replacement = '''def _phase35_save_repair(
    memory, task, candidates, outcome, diagnosis,
    replay_context=None, learning_engine=None
):
    """Save only explicitly tested repairs to existing learning systems."""
    if not isinstance(outcome, dict) or outcome.get("success") is not True:
        return False
    repair = outcome.get("repair", {})
    if not isinstance(repair, dict):
        return False
    if outcome.get("test_passed") is not True:
        print("[PHASE35] Independent test evidence missing; save skipped.")
        return False

    accepted = outcome.get("accepted_candidate") or repair.get("final_candidate")
    if not isinstance(accepted, str) or accepted not in candidates:
        print("[PHASE35] Accepted candidate mismatch; save skipped.")
        return False

    context = dict(replay_context or {})
    evidence = [
        "Phase 33 repair success",
        "test_passed=True",
        "Accepted candidate matched submitted candidates",
    ]
    try:
        memory.remember(
            intent=str(task),
            code=accepted,
            language="python",
            description="Independently tested PIKA repair",
            tags=["phase33", "repair"],
            preconditions=[str(diagnosis.get("root_cause", ""))],
            verification="test_verified",
            evidence=evidence,
            replay_context=context,
        )
        if learning_engine is not None:
            record = learning_engine.learn(
                task=str(task),
                error_type=str(diagnosis.get("error_type", "")),
                root_cause=str(diagnosis.get("root_cause", "")),
                error_message=str(diagnosis.get("error_message", "")),
                method="phase33-verified-repair",
                solution=accepted,
                verification={
                    "independent_test": True,
                    "test_passed": True,
                    "evidence": evidence,
                },
                success=True,
                source="pika_phase33",
                metadata={"accepted_candidate_verified": True},
                replay_context=context,
            )
            print("[PIKA LEARNING] trusted=", record.get("trusted", False))
        print("[PHASE35] Verified repair saved.")
        return True
    except Exception as exc:
        print("[PHASE35] Learning save failed safely:", exc)
        return False
'''

lines = src.splitlines(keepends=True)
src = "".join(lines[:helper.lineno - 1]) + replacement + "\n\n" + "".join(lines[helper.end_lineno:])

marker = '''        self.semantic_code_memory = SemanticCodeMemory(
            project_root / "data" / "semantic_code_memory.json"
        )'''
init_replacement = marker + '''
        self.learning_engine = LearningEngine(
            project_root / "data" / "learning_engine.json"
        )'''

if "self.learning_engine = LearningEngine(" not in src:
    if marker not in src:
        raise RuntimeError("Semantic memory init anchor not found; no write performed.")
    src = src.replace(marker, init_replacement, 1)

# Wire Phase 34 successful repair call.
phase34_anchor = "replay_context=first_context,\n                                    )"
phase34_new = (
    "replay_context=first_context,\n"
    "                                        learning_engine=self.learning_engine,\n"
    "                                    )"
)
if "learning_engine=self.learning_engine" not in src:
    if phase34_anchor not in src:
        raise RuntimeError("Phase 34 call anchor not found; no write performed.")
    src = src.replace(phase34_anchor, phase34_new, 1)

# Wire Phase 33 generated-repair success call.
phase33_anchor = (
    "                                    phase33_diagnosis,\n"
    "                                )\n"
    '                                result["success"] = True'
)
phase33_new = (
    "                                    phase33_diagnosis,\n"
    "                                    learning_engine=self.learning_engine,\n"
    "                                )\n"
    '                                result["success"] = True'
)
if src.count("learning_engine=self.learning_engine") < 2:
    if phase33_anchor not in src:
        raise RuntimeError("Phase 33 call anchor not found; no write performed.")
    src = src.replace(phase33_anchor, phase33_new, 1)

ast.parse(src)
backup = p.with_suffix(".py.pre_learning_backup")
if not backup.exists():
    shutil.copy2(p, backup)

tmp = p.with_suffix(".py.learning_tmp")
tmp.write_text(src, encoding="utf-8")
tmp.replace(p)

print("PATCH APPLIED: existing Brain retained.")
print("Backup:", backup)
print("LearningEngine initialized and wired to Phase 34/33 success paths.")
