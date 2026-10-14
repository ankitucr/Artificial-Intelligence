from pathlib import Path
import shutil
import sys

root = Path.cwd()
brain = root / "core" / "brain.py"
memory = root / "core" / "semantic_code_memory.py"

if not brain.is_file() or not memory.is_file():
    print("ERROR: Required files missing; nothing changed.")
    sys.exit(1)

src = brain.read_text()
original = src

imp = "from core.semantic_code_memory import SemanticCodeMemory"
if imp not in src:
    anchor = "from core.phase34_learning_repair import Phase34LearningRepair"
    if anchor not in src:
        print("ERROR: Import anchor not found; nothing changed.")
        sys.exit(1)
    src = src.replace(anchor, anchor + "\n" + imp, 1)

if "self.semantic_code_memory" not in src:
    anchor = "self.workspace_executor = None"
    if anchor not in src:
        print("ERROR: Initialization anchor not found; nothing changed.")
        sys.exit(1)
    src = src.replace(
        anchor,
        anchor
        + "\n        project_root = Path(__file__).resolve().parents[1]"
        + "\n        self.semantic_code_memory = SemanticCodeMemory("
        + '\n            project_root / "data" / "semantic_code_memory.json"'
        + "\n        )",
        1,
    )

# Do not guess the fallback repair block's indentation or structure.
marker = "# PHASE35_SEMANTIC_CANDIDATES_INTEGRATED"
if marker not in src:
    anchor = 'if repair_context.get("success"):'
    pos = src.find(anchor)
    if pos < 0:
        print("ERROR: Repair anchor not found; nothing changed.")
        sys.exit(1)

    # Validate exact candidate argument before editing anything.
    old = 'candidates=(\n                                        repair_context["candidates"]\n                                    ),'
    if old not in src:
        print("ERROR: Candidate argument layout differs; nothing changed.")
        print("Please send: sed -n '680,760p' core/brain.py")
        sys.exit(1)

    injected = '''if repair_context.get("success"):
                            # PHASE35_SEMANTIC_CANDIDATES_INTEGRATED
                            semantic_candidates = []
                            try:
                                semantic_hits = self.semantic_code_memory.retrieve(
                                    query=(
                                        str(task) + " "
                                        + str(phase33_diagnosis.get("root_cause", "")) + " "
                                        + str(phase33_diagnosis.get("error_message", ""))
                                    ),
                                    verified_only=True,
                                    limit=3,
                                )
                                for variant in semantic_hits:
                                    code = str(variant.get("code", "")).strip()
                                    if code and code not in semantic_candidates:
                                        semantic_candidates.append(code)
                            except Exception as exc:
                                print("[PIKA PHASE 35] retrieval skipped:", exc)

                            generated_candidates = repair_context.get("candidates", [])
                            if not isinstance(generated_candidates, list):
                                generated_candidates = []
                            combined_candidates = []
                            for candidate in semantic_candidates + generated_candidates:
                                if isinstance(candidate, str):
                                    candidate = candidate.strip()
                                    if candidate and candidate not in combined_candidates:
                                        combined_candidates.append(candidate)

                            if semantic_candidates:
                                print(
                                    "[PIKA PHASE 35] verified semantic candidates "
                                    "sent to Phase 33 for validation."
                                )
'''
    src = src.replace(anchor, injected, 1)
    src = src.replace(old, "candidates=(combined_candidates),", 1)

if src == original:
    print("No changes were necessary.")
    sys.exit(0)

backup = root / "core" / "brain.py.phase35-backup"
if backup.exists():
    backup = root / "core" / "brain.py.phase35-backup-2"

shutil.copy2(brain, backup)
brain.write_text(src)
print("PATCHED:", brain)
print("BACKUP:", backup)
