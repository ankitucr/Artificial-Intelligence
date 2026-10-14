import ast, json, importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = [
    "core/brain.py",
    "core/phase33_controller.py",
    "core/self_healing.py",
    "core/semantic_code_memory.py",
    "core/learning_engine.py",
    "core/learning_repair_bridge.py",
    "core/phase34_learning_repair.py",
    "core/pika_self_evaluator.py",
    "core/pika_github_evolution_loop.py",
]
TESTS = [
    "tests.test_semantic_code_memory",
    "tests.test_phase34_brain_integration",
    "tests.test_phase34_brain_fallback",
    "tests.test_phase35_brain_semantic_integration",
    "tests.test_phase35_context_persistence",
]
result = {"files": [], "tests": [], "integration_gaps": []}

for rel in FILES:
    path = ROOT / rel
    item = {"path": rel, "exists": path.is_file(), "classes": [], "functions": [], "imports": []}
    if path.is_file():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.col_offset <= 4:
                        item["functions"].append({
                            "name": node.name,
                            "args": [a.arg for a in node.args.args],
                        })
                elif isinstance(node, ast.ClassDef):
                    item["classes"].append({
                        "name": node.name,
                        "methods": [
                            {"name": n.name,
                             "args": [a.arg for a in n.args.args]}
                            for n in node.body
                            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                        ],
                    })
                elif isinstance(node, ast.ImportFrom):
                    item["imports"].append({
                        "module": node.module,
                        "names": [n.name for n in node.names],
                    })
        except Exception as exc:
            item["parse_error"] = str(exc)
    result["files"].append(item)
    print(f"{'FOUND' if item['exists'] else 'MISSING'} {rel}")
    for cls in item["classes"]:
        print("  CLASS", cls["name"], "METHODS:",
              ", ".join(m["name"] for m in cls["methods"][:15]))
    for fn in item["functions"]:
        print("  FUNCTION", fn["name"] + "(" + ", ".join(fn["args"]) + ")")

for module in TESTS:
    try:
        spec = importlib.util.find_spec(module)
        found = spec is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        found = False
    result["tests"].append({"module": module, "available": found})
    print(("TEST FOUND " if found else "TEST MISSING ") + module)

brain = next((f for f in result["files"] if f["path"] == "core/brain.py"), {})
memory = next((f for f in result["files"] if f["path"] == "core/semantic_code_memory.py"), {})
controller = next((f for f in result["files"] if f["path"] == "core/phase33_controller.py"), {})
if not brain.get("exists"):
    result["integration_gaps"].append("PIKABrain source missing")
if not memory.get("exists"):
    result["integration_gaps"].append("Semantic memory source missing")
if not controller.get("exists"):
    result["integration_gaps"].append("Phase 33 controller source missing")

out = ROOT / "data" / "pika_learning_integration_map.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, indent=2), encoding="utf-8")
print("\nIntegration map saved:", out)
print("This scan did not modify Brain, memory, or downloaded code.")
