import json, ast, time, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
LOG = ROOT / "logs" / "pika_self_evaluation.log"
REPORT = DATA / "pika_self_evaluation_report.json"

def now():
    return datetime.now(timezone.utc).isoformat()

def record(name, status, detail=""):
    results.append({
        "check": name, "status": status, "detail": str(detail)[:1200]
    })
    print(f"[{status}] {name}: {detail}", flush=True)

results = []
started = time.time()
print("=== PIKA SELF-EVALUATION ===", flush=True)

# 1. Acquisition/evaluation artifacts
for name, path in [
    ("GitHub index", DATA / "pika_code_index.json"),
    ("GitHub evaluation report", DATA / "pika_evaluation_report.json"),
    ("GitHub registry", DATA / "pika_evolution_registry.json"),
    ("Original GitHub registry", DATA / "github_skill_registry.json"),
]:
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            size = path.stat().st_size
            record(name, "PASS", f"valid JSON, {size} bytes")
        except Exception as exc:
            record(name, "FAIL", exc)
    else:
        record(name, "WARN", "not found: " + str(path.relative_to(ROOT)))

# 2. Daemon process check
running = False
try:
    for proc in Path("/proc").iterdir():
        if not proc.name.isdigit():
            continue
        try:
            cmd = (proc / "cmdline").read_bytes().replace(b"\0", b" ").decode(errors="ignore")
            if "pika_github_evolution_loop" in cmd and "--daemon" in cmd:
                running = True
                break
        except (OSError, PermissionError):
            pass
    record("Evolution daemon", "PASS" if running else "WARN",
           "process found" if running else "process not found; Termux may have stopped it")
except Exception as exc:
    record("Evolution daemon", "WARN", exc)

# 3. Static safety/integrity checks on collected Python only.
corpus = DATA / "github_code_corpus"
py_count, parse_pass, parse_fail = 0, 0, 0
if corpus.exists():
    for path in corpus.rglob("*.py"):
        py_count += 1
        try:
            ast.parse(path.read_text(encoding="utf-8", errors="replace"))
            parse_pass += 1
        except (SyntaxError, ValueError):
            parse_fail += 1
record("Collected Python syntax", "PASS" if parse_fail == 0 else "WARN",
       f"{parse_pass}/{py_count} parsed; {parse_fail} syntax failures; no source executed")

# 4. Phase 35 semantic memory presence and structure (read-only).
memory_candidates = [
    DATA / "semantic_code_memory.json",
    DATA / "semantic_memory.json",
]
memory_file = next((p for p in memory_candidates if p.is_file()), None)
if memory_file:
    try:
        raw = json.loads(memory_file.read_text(encoding="utf-8"))
        record("Semantic memory JSON", "PASS",
               f"valid JSON at {memory_file.relative_to(ROOT)}; top-level={type(raw).__name__}")
    except Exception as exc:
        record("Semantic memory JSON", "FAIL", exc)
else:
    record("Semantic memory JSON", "WARN",
           "standard filenames not found; memory may use another path")

brain = ROOT / "core" / "brain.py"
if brain.exists():
    source = brain.read_text(encoding="utf-8", errors="replace").lower()
    found = any(term in source for term in
                ("semantic_code_memory", "semantic memory", "semantic_memory"))
    record("Brain semantic-memory reference", "PASS" if found else "WARN",
           "reference detected" if found else "reference not detected by simple scan")
else:
    record("Brain source", "FAIL", "core/brain.py missing")

# 5. Run focused existing tests; outputs are retained in logs.
test_modules = [
    "tests.test_semantic_code_memory",
    "tests.test_phase35_brain_semantic_integration",
    "tests.test_phase35_context_persistence",
]
test_results = []
for module in test_modules:
    print(f"\n--- TEST {module} ---", flush=True)
    try:
        proc = subprocess.run(
            [sys.executable, "-m", module],
            cwd=ROOT, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, timeout=90
        )
        output = proc.stdout[-5000:]
        status = "PASS" if proc.returncode == 0 else "FAIL"
        record(module, status, f"return code={proc.returncode}\n{output}")
        test_results.append({"module": module, "status": status,
                             "return_code": proc.returncode, "output": output})
    except subprocess.TimeoutExpired as exc:
        record(module, "WARN", "timed out after 90 seconds")
        test_results.append({"module": module, "status": "TIMEOUT"})
    except Exception as exc:
        record(module, "WARN", exc)
        test_results.append({"module": module, "status": "ERROR", "detail": str(exc)})

passed = sum(r["status"] == "PASS" for r in results)
failed = sum(r["status"] == "FAIL" for r in results)
report = {
    "timestamp": now(),
    "duration_seconds": round(time.time() - started, 2),
    "summary": {"checks": len(results), "passed": passed,
                "failed": failed, "warnings": len(results)-passed-failed},
    "checks": results,
    "tests": test_results,
    "limitations": [
        "A passing syntax check does not prove runtime correctness.",
        "Collected public source was not executed.",
        "A detected Brain reference does not prove runtime memory replay.",
        "This evaluator does not modify Brain or semantic memory."
    ]
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
with LOG.open("a", encoding="utf-8") as f:
    f.write("\n" + json.dumps(report, indent=2) + "\n")
print("\n=== SELF-EVALUATION SUMMARY ===")
print(json.dumps(report["summary"], indent=2))
print("Report:", REPORT)
print("Log:", LOG)
print("Next: inspect FAIL/WARN results before enabling automatic learning.")
