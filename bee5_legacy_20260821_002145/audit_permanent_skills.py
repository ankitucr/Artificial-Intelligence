import ast
import json
from pathlib import Path

ROOT = Path("permanent_skills")

SUSPICIOUS_IMPORTS = {
    "os",
    "sys",
    "subprocess",
    "socket",
    "requests",
    "urllib",
    "http",
    "shutil",
    "pathlib",
    "sqlite3",
    "ctypes",
    "multiprocessing",
    "threading",
    "asyncio",
    "importlib",
}

results = []

for path in sorted(ROOT.glob("*.py")):
    record = {
        "file": path.name,
        "size": 0,
        "lines": 0,
        "syntax": "UNKNOWN",
        "functions": 0,
        "classes": 0,
        "imports": [],
        "suspicious_imports": [],
        "calls": [],
        "top_level_calls": [],
        "returns": 0,
        "docstrings": 0,
        "logic_score": 0,
        "classification": "UNKNOWN",
        "error": None,
    }

    try:
        source = path.read_text(
            encoding="utf-8",
            errors="replace"
        )

        record["size"] = len(source.encode("utf-8"))
        record["lines"] = len(source.splitlines())

        tree = ast.parse(source, filename=str(path))
        record["syntax"] = "OK"

        for node in ast.walk(tree):

            if isinstance(node, ast.FunctionDef):
                record["functions"] += 1

                if ast.get_docstring(node):
                    record["docstrings"] += 1

            elif isinstance(node, ast.AsyncFunctionDef):
                record["functions"] += 1

                if ast.get_docstring(node):
                    record["docstrings"] += 1

            elif isinstance(node, ast.ClassDef):
                record["classes"] += 1

                if ast.get_docstring(node):
                    record["docstrings"] += 1

            elif isinstance(node, ast.Return):
                record["returns"] += 1

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    record["imports"].append(alias.name)

                    root = alias.name.split(".")[0]

                    if root in SUSPICIOUS_IMPORTS:
                        record["suspicious_imports"].append(
                            alias.name
                        )

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""

                record["imports"].append(module)

                root = module.split(".")[0]

                if root in SUSPICIOUS_IMPORTS:
                    record["suspicious_imports"].append(
                        module
                    )

            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    record["calls"].append(node.func.id)

                elif isinstance(node.func, ast.Attribute):
                    record["calls"].append(
                        node.func.attr
                    )

        # Top-level execution detection
        for statement in tree.body:

            if isinstance(statement, ast.Expr):
                if isinstance(statement.value, ast.Call):
                    name = "<call>"

                    if isinstance(
                        statement.value.func,
                        ast.Name
                    ):
                        name = statement.value.func.id

                    elif isinstance(
                        statement.value.func,
                        ast.Attribute
                    ):
                        name = statement.value.func.attr

                    record["top_level_calls"].append(name)

        # --------------------------------------------------
        # Logic score
        # --------------------------------------------------

        score = 0

        if record["functions"] > 0:
            score += 30

        if record["returns"] > 0:
            score += 25

        if record["lines"] >= 10:
            score += 10

        if record["lines"] >= 30:
            score += 10

        if record["docstrings"] > 0:
            score += 5

        if len(record["calls"]) > 0:
            score += 10

        if record["classes"] > 0:
            score += 5

        if record["top_level_calls"]:
            score -= 10

        if record["suspicious_imports"]:
            score -= 10

        if score < 0:
            score = 0

        if score > 100:
            score = 100

        record["logic_score"] = score

        # --------------------------------------------------
        # Classification
        # --------------------------------------------------

        if record["functions"] == 0 and record["classes"] == 0:
            record["classification"] = "LIKELY_EMPTY_OR_DATA_ONLY"

        elif record["lines"] <= 5 and record["functions"] <= 1:
            record["classification"] = "VERY_SMALL"

        elif score < 35:
            record["classification"] = "WEAK_LOGIC"

        elif score < 60:
            record["classification"] = "BASIC_LOGIC"

        elif score < 80:
            record["classification"] = "USEFUL_LOGIC"

        else:
            record["classification"] = "STRONG_LOGIC"

        if record["suspicious_imports"]:
            record["classification"] += "_CHECK_IMPORTS"

    except SyntaxError as exc:
        record["syntax"] = "FAIL"
        record["classification"] = "BROKEN_SYNTAX"
        record["error"] = (
            f"line={exc.lineno}, "
            f"message={exc.msg}"
        )

    except Exception as exc:
        record["classification"] = "AUDIT_ERROR"
        record["error"] = str(exc)

    results.append(record)


# ------------------------------------------------------
# Save full JSON report
# ------------------------------------------------------

report_path = Path("permanent_skills_audit.json")

report_path.write_text(
    json.dumps(
        results,
        indent=2,
        ensure_ascii=False
    ),
    encoding="utf-8"
)


# ------------------------------------------------------
# Summary
# ------------------------------------------------------

total = len(results)

syntax_ok = sum(
    r["syntax"] == "OK"
    for r in results
)

syntax_fail = sum(
    r["syntax"] == "FAIL"
    for r in results
)

strong = sum(
    r["classification"].startswith("STRONG_LOGIC")
    for r in results
)

useful = sum(
    r["classification"].startswith("USEFUL_LOGIC")
    for r in results
)

basic = sum(
    r["classification"].startswith("BASIC_LOGIC")
    for r in results
)

weak = sum(
    "WEAK_LOGIC" in r["classification"]
    for r in results
)

empty = sum(
    r["classification"] == "LIKELY_EMPTY_OR_DATA_ONLY"
    for r in results
)

suspicious = sum(
    bool(r["suspicious_imports"])
    for r in results
)

print()
print("=" * 70)
print("       BEE5 PERMANENT SKILLS — STATIC AUDIT")
print("=" * 70)

print(f"Total Python files       : {total}")
print(f"Syntax OK                : {syntax_ok}")
print(f"Syntax FAIL              : {syntax_fail}")
print(f"Strong logic             : {strong}")
print(f"Useful logic             : {useful}")
print(f"Basic logic              : {basic}")
print(f"Weak logic               : {weak}")
print(f"Empty/data-only          : {empty}")
print(f"Suspicious imports       : {suspicious}")

print()
print("TOP 30 STRONGEST SKILLS")
print("-" * 70)

for r in sorted(
    results,
    key=lambda x: x["logic_score"],
    reverse=True
)[:30]:
    print(
        f'{r["logic_score"]:3}/100  '
        f'{r["classification"]:<28} '
        f'{r["file"]}'
    )

print()
print("FILES NEEDING ATTENTION")
print("-" * 70)

for r in results:

    if (
        r["syntax"] == "FAIL"
        or "WEAK_LOGIC" in r["classification"]
        or r["classification"] == "LIKELY_EMPTY_OR_DATA_ONLY"
        or r["suspicious_imports"]
    ):

        print(
            f'{r["logic_score"]:3}/100  '
            f'{r["classification"]:<30} '
            f'{r["file"]}'
        )

print()
print("=" * 70)
print(
    f"Full report saved to: {report_path}"
)
print("=" * 70)
