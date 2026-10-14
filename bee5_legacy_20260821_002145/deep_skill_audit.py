import os
import ast
import json
import re
from pathlib import Path
from collections import Counter

ROOT = Path("permanent_skills")
LOG_DIR = Path("skill_execution_logs")
REPORT = Path("deep_skill_audit.json")

PLACEHOLDER_PATTERNS = [
    r"\bTODO\b",
    r"\bpass\s*(#.*)?$",
    r"not implemented",
    r"implement this",
    r"to be implemented",
    r"placeholder",
    r"dummy",
]

INFRA_IMPORTS = {
    "sqlite3", "os", "json", "pathlib", "threading",
    "subprocess", "socket", "asyncio"
}

NETWORK_IMPORTS = {
    "requests", "urllib", "httpx", "aiohttp",
    "bs4", "socket"
}

CAPABILITY_IMPORTS = {
    "math", "statistics", "re", "collections",
    "numpy", "pandas", "sklearn"
}


def safe_read(path):
    try:
        return path.read_text(errors="replace")
    except Exception:
        return ""


def analyse_source(path):
    source = safe_read(path)

    result = {
        "file": path.name,
        "size": len(source),
        "lines": len(source.splitlines()),
        "syntax": "FAIL",
        "functions": [],
        "classes": [],
        "imports": [],
        "calls": [],
        "placeholders": [],
        "has_real_logic": False,
        "category": "UNKNOWN",
        "signals": [],
    }

    for pattern in PLACEHOLDER_PATTERNS:
        for match in re.finditer(pattern, source, re.I | re.M):
            line = source[:match.start()].count("\n") + 1
            result["placeholders"].append({
                "line": line,
                "pattern": pattern
            })

    try:
        tree = ast.parse(source)
        result["syntax"] = "OK"

        for node in ast.walk(tree):

            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                result["functions"].append(node.name)

            elif isinstance(node, ast.ClassDef):
                result["classes"].append(node.name)

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    result["imports"].append(alias.name.split(".")[0])

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    result["imports"].append(node.module.split(".")[0])

            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    result["calls"].append(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    result["calls"].append(node.func.attr)

    except SyntaxError:
        return result

    imports = set(result["imports"])
    calls = set(result["calls"])

    # Real computational / operational signals
    logic_signals = {
        "if", "for", "while", "return", "try",
        "sqlite3", "requests", "BeautifulSoup",
        "open", "execute", "fetchall", "json"
    }

    for signal in logic_signals:
        if signal in source or signal in calls:
            result["signals"].append(signal)

    result["has_real_logic"] = (
        len(result["functions"]) > 0
        and (
            len(result["calls"]) >= 2
            or len(result["signals"]) >= 2
            or len(source.splitlines()) >= 20
        )
    )

    if imports & INFRA_IMPORTS:
        result["category"] = "INFRASTRUCTURE"

    if imports & NETWORK_IMPORTS:
        if result["category"] == "UNKNOWN":
            result["category"] = "NETWORK"
        else:
            result["category"] += "+NETWORK"

    if imports & CAPABILITY_IMPORTS:
        if result["category"] == "UNKNOWN":
            result["category"] = "CAPABILITY"

    if result["category"] == "UNKNOWN":
        if len(result["functions"]) >= 2:
            result["category"] = "LOGIC"
        elif result["functions"]:
            result["category"] = "SMALL_LOGIC"
        else:
            result["category"] = "DATA_ONLY"

    return result


def read_runtime_log(filename):
    log = LOG_DIR / (filename + ".log")

    if not log.exists():
        return {
            "status": "NO_LOG",
            "runtime": None,
            "errors": []
        }

    text = safe_read(log)

    status = "UNKNOWN"

    if "Status     : COMPLETED" in text:
        status = "COMPLETED"
    elif "Status     : FAILED" in text:
        status = "FAILED"
    elif "Status     : TIMEOUT" in text:
        status = "TIMEOUT"

    runtime = None

    m = re.search(r"Runtime\s*:\s*([0-9.]+)s", text)
    if m:
        runtime = float(m.group(1))

    errors = []

    for line in text.splitlines():
        if (
            "Error" in line
            or "Exception" in line
            or "Traceback" in line
            or "no such table" in line
            or "no such column" in line
        ):
            errors.append(line.strip())

    return {
        "status": status,
        "runtime": runtime,
        "errors": errors[-10:]
    }


def classify(item):
    source = item["source"]
    runtime = item["runtime"]

    if source["syntax"] != "OK":
        return "REPAIR"

    if source["placeholders"]:
        if not source["has_real_logic"]:
            return "JUNK_CANDIDATE"
        return "REPAIR"

    if runtime["status"] == "FAILED":
        if source["category"] == "INFRASTRUCTURE":
            return "REPAIR"
        return "REVIEW"

    if runtime["status"] == "TIMEOUT":
        return "REVIEW"

    if (
        runtime["status"] == "COMPLETED"
        and source["has_real_logic"]
    ):
        return "KEEP_CANDIDATE"

    if not source["has_real_logic"]:
        return "JUNK_CANDIDATE"

    return "REVIEW"


def main():
    print("=" * 72)
    print("        BEE5 DEEP PERMANENT SKILL AUDITOR")
    print("=" * 72)

    files = sorted(ROOT.glob("*.py"))

    print(f"\nSkills found : {len(files)}")
    print("Mode         : READ ONLY")
    print("Deleting     : NO")
    print("Modifying    : NO\n")

    results = []

    for path in files:
        source = analyse_source(path)
        runtime = read_runtime_log(path.name)

        item = {
            "source": source,
            "runtime": runtime,
        }

        item["decision"] = classify(item)
        results.append(item)

        print(
            f"{item['decision']:<16} "
            f"{path.name:<55} "
            f"{runtime['status']}"
        )

    summary = Counter(x["decision"] for x in results)

    output = {
        "total": len(results),
        "summary": dict(summary),
        "skills": results
    }

    REPORT.write_text(
        json.dumps(output, indent=2, ensure_ascii=False)
    )

    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)

    for key in [
        "KEEP_CANDIDATE",
        "REPAIR",
        "REVIEW",
        "JUNK_CANDIDATE"
    ]:
        print(f"{key:<18}: {summary.get(key, 0)}")

    print("\nReport:")
    print(REPORT.resolve())

    print("\nIMPORTANT:")
    print("No permanent skill was modified or deleted.")


if __name__ == "__main__":
    main()
