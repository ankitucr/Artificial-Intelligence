import ast
import json
import re
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path("permanent_skills")
LOGS = Path("skill_execution_logs")

OUT_JSON = Path("forensic_classification_v2.json")
OUT_TXT = Path("forensic_classification_v2.txt")

PLACEHOLDERS = [
    r"\bTODO\b",
    r"\bpass\b",
    r"not implemented",
    r"implement this",
    r"to be implemented",
    r"placeholder",
]

NETWORK_IMPORTS = {
    "requests",
    "urllib",
    "httpx",
    "aiohttp",
    "bs4",
    "socket",
}

INFRA_IMPORTS = {
    "sqlite3",
    "subprocess",
    "threading",
    "asyncio",
    "pathlib",
    "os",
}

GENERATOR_SIGNALS = {
    "write",
    "write_text",
    "open",
    "create_skill",
    "add_skill",
    "create_skill_module",
    "skill_module",
    "hashlib",
}

CAPABILITY_IMPORTS = {
    "math",
    "statistics",
    "re",
    "collections",
    "datetime",
    "decimal",
}


def read_text(path):
    try:
        return path.read_text(
            encoding="utf-8",
            errors="replace"
        )
    except Exception:
        return ""


def get_runtime(name):
    path = LOGS / f"{name}.log"

    if not path.exists():
        return {
            "status": "NO_LOG",
            "runtime": None,
            "errors": [],
            "stdout": "",
        }

    text = read_text(path)

    if "Status     : COMPLETED" in text:
        status = "COMPLETED"
    elif "Status     : FAILED" in text:
        status = "FAILED"
    elif "Status     : TIMEOUT" in text:
        status = "TIMEOUT"
    else:
        status = "UNKNOWN"

    runtime = None

    m = re.search(
        r"Runtime\s*:\s*([0-9.]+)s",
        text
    )

    if m:
        runtime = float(m.group(1))

    stdout = ""

    marker = "----- STDOUT -----"

    if marker in text:
        part = text.split(
            marker,
            1
        )[1]

        if "----- STDERR -----" in part:
            stdout = part.split(
                "----- STDERR -----",
                1
            )[0]

    errors = []

    for line in text.splitlines():
        low = line.lower()

        if (
            "traceback" in low
            or "exception" in low
            or "operationalerror" in low
            or "programmingerror" in low
            or "error:" in low
            or "failed" in low
            or "no such" in low
        ):
            errors.append(line.strip())

    return {
        "status": status,
        "runtime": runtime,
        "errors": errors[-12:],
        "stdout": stdout.strip(),
    }


def parse_source(path):
    source = read_text(path)

    item = {
        "file": path.name,
        "bytes": len(source.encode("utf-8")),
        "lines": len(source.splitlines()),
        "syntax": "FAIL",
        "functions": [],
        "classes": [],
        "imports": [],
        "calls": [],
        "placeholders": [],
        "generated_files": False,
        "has_main": False,
        "has_return": False,
        "category": "UNKNOWN",
        "capability_tokens": [],
    }

    for pattern in PLACEHOLDERS:

        if re.search(
            pattern,
            source,
            re.IGNORECASE
        ):

            item["placeholders"].append(
                pattern
            )

    try:
        tree = ast.parse(
            source,
            filename=str(path)
        )
    except SyntaxError:
        return item

    item["syntax"] = "OK"

    for node in ast.walk(tree):

        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            item["functions"].append(
                node.name
            )

            if node.name == "main":
                item["has_main"] = True

        elif isinstance(
            node,
            ast.ClassDef
        ):
            item["classes"].append(
                node.name
            )

        elif isinstance(
            node,
            ast.Return
        ):
            item["has_return"] = True

        elif isinstance(
            node,
            ast.Import
        ):

            for alias in node.names:
                item["imports"].append(
                    alias.name.split(".")[0]
                )

        elif isinstance(
            node,
            ast.ImportFrom
        ):

            if node.module:
                item["imports"].append(
                    node.module.split(".")[0]
                )

        elif isinstance(
            node,
            ast.Call
        ):

            if isinstance(
                node.func,
                ast.Name
            ):
                item["calls"].append(
                    node.func.id
                )

            elif isinstance(
                node.func,
                ast.Attribute
            ):
                item["calls"].append(
                    node.func.attr
                )

    item["generated_files"] = any(
        signal in source
        for signal in GENERATOR_SIGNALS
        if signal in {
            "write",
            "write_text",
            "open",
            "hashlib",
        }
    )

    imports = set(item["imports"])
    calls = set(item["calls"])

    if imports & NETWORK_IMPORTS:
        item["category"] = "NETWORK"

    elif imports & INFRA_IMPORTS:
        item["category"] = "INFRASTRUCTURE"

    elif imports & CAPABILITY_IMPORTS:
        item["category"] = "CAPABILITY"

    elif item["classes"]:
        item["category"] = "ALGORITHM / CLASS"

    elif item["functions"]:
        item["category"] = "LOGIC"

    else:
        item["category"] = "DATA / OTHER"

    # Capability tokens for duplicate grouping
    combined = (
        " ".join(item["functions"])
        + " "
        + " ".join(item["calls"])
        + " "
        + " ".join(item["imports"])
        + " "
        + source[:5000]
    ).lower()

    item["capability_tokens"] = sorted(
        set(
            re.findall(
                r"[a-zA-Z_][a-zA-Z0-9_]{2,}",
                combined
            )
        )
    )

    return item


def similarity(a, b):

    sa = set(
        a["capability_tokens"]
    )

    sb = set(
        b["capability_tokens"]
    )

    if not sa and not sb:
        return 1.0

    union = sa | sb

    if not union:
        return 0.0

    return len(sa & sb) / len(union)


def classify(source, runtime):

    # Broken syntax
    if source["syntax"] != "OK":
        return "BROKEN_SYNTAX"

    # Explicit placeholder with almost no implementation
    if (
        source["placeholders"]
        and len(source["functions"]) <= 1
        and not source["has_return"]
        and source["lines"] <= 15
    ):
        return "PLACEHOLDER"

    # Skill generator / file creator
    text_flags = (
        source["generated_files"]
        or any(
            x in source["calls"]
            for x in [
                "create_skill",
                "add_skill",
                "create_skill_module",
            ]
        )
    )

    if text_flags:
        return "INFRASTRUCTURE_GENERATOR"

    # Network capability
    if source["category"] == "NETWORK":
        if runtime["status"] == "FAILED":
            return "NETWORK_BROKEN"
        return "NETWORK"

    # Database infrastructure
    if source["category"] == "INFRASTRUCTURE":
        if runtime["status"] == "FAILED":
            return "INFRASTRUCTURE_BROKEN"
        return "INFRASTRUCTURE"

    # Actual runtime failure
    if runtime["status"] == "FAILED":
        return "BROKEN_RUNTIME"

    # No runtime log
    if runtime["status"] == "NO_LOG":
        if source["functions"] or source["classes"]:
            return "UNTESTED"
        return "UNKNOWN"

    # Completed but no real implementation
    if (
        runtime["status"] == "COMPLETED"
        and not source["functions"]
        and not source["classes"]
    ):
        return "DATA_OR_SCRIPT"

    # Completed with implementation
    if (
        runtime["status"] == "COMPLETED"
        and source["functions"]
    ):
        return "REAL_CAPABILITY"

    return "REVIEW"


def main():

    files = sorted(
        ROOT.glob("*.py")
    )

    print()
    print("=" * 78)
    print("         BEE5 FORENSIC CLASSIFIER v2")
    print("=" * 78)
    print()
    print(f"Files found : {len(files)}")
    print("Mode        : READ ONLY")
    print("Delete      : NO")
    print("Modify      : NO")
    print()

    records = []

    for path in files:

        source = parse_source(path)

        runtime = get_runtime(
            path.name
        )

        decision = classify(
            source,
            runtime
        )

        records.append({
            "file": path.name,
            "source": source,
            "runtime": runtime,
            "decision": decision,
        })

    # --------------------------------------------------------
    # Duplicate grouping
    # --------------------------------------------------------

    groups = []

    used = set()

    real_like = [
        r for r in records
        if r["decision"]
        in {
            "REAL_CAPABILITY",
            "NETWORK",
            "INFRASTRUCTURE",
            "UNTESTED",
        }
    ]

    for i, current in enumerate(real_like):

        if current["file"] in used:
            continue

        group = [
            current["file"]
        ]

        for other in real_like[i + 1:]:

            score = similarity(
                current["source"],
                other["source"]
            )

            if score >= 0.65:

                group.append(
                    other["file"]
                )

        if len(group) >= 2:

            for name in group:
                used.add(name)

            groups.append({
                "representative": group[0],
                "members": group,
                "size": len(group),
            })

    # --------------------------------------------------------
    # Duplicate annotations
    # --------------------------------------------------------

    duplicate_map = {}

    for group in groups:

        for name in group["members"]:

            duplicate_map[name] = group

    for record in records:

        name = record["file"]

        if name in duplicate_map:

            record["duplicate_group"] = (
                duplicate_map[name]
            )

            if (
                record["decision"]
                == "REAL_CAPABILITY"
            ):

                record["decision"] = (
                    "REAL_DUPLICATE_CANDIDATE"
                )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    summary = Counter(
        r["decision"]
        for r in records
    )

    output = {
        "total": len(records),
        "summary": dict(summary),
        "duplicate_groups": groups,
        "skills": records,
    }

    OUT_JSON.write_text(
        json.dumps(
            output,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    # --------------------------------------------------------
    # Human-readable report
    # --------------------------------------------------------

    with OUT_TXT.open(
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            "=" * 78 + "\n"
        )

        f.write(
            "BEE5 FORENSIC CLASSIFICATION v2\n"
        )

        f.write(
            "=" * 78 + "\n\n"
        )

        for key, value in sorted(
            summary.items()
        ):

            f.write(
                f"{key:<30} {value}\n"
            )

        f.write(
            "\n\n"
        )

        f.write(
            "DUPLICATE GROUPS\n"
        )

        f.write(
            "-" * 78 + "\n"
        )

        for i, group in enumerate(
            groups,
            1
        ):

            f.write(
                f"\nGROUP {i} "
                f"({group['size']} files)\n"
            )

            for name in group["members"]:
                f.write(
                    f"  - {name}\n"
                )

        f.write(
            "\n\n"
        )

        f.write(
            "INDIVIDUAL CLASSIFICATION\n"
        )

        f.write(
            "-" * 78 + "\n"
        )

        for record in records:

            f.write(
                f"{record['decision']:<30} "
                f"{record['file']}\n"
            )

            if record["runtime"]["errors"]:

                f.write(
                    "    ERROR: "
                    + " | ".join(
                        record["runtime"]["errors"][:3]
                    )
                    + "\n"
                )

    print(
        "=" * 78
    )

    print(
        "CLASSIFICATION COMPLETE"
    )

    print(
        "=" * 78
    )

    for key, value in sorted(
        summary.items()
    ):

        print(
            f"{key:<30}: {value}"
        )

    print()
    print(
        f"JSON report : {OUT_JSON}"
    )

    print(
        f"Text report : {OUT_TXT}"
    )

    print()
    print(
        "NO FILES WERE MODIFIED."
    )


if __name__ == "__main__":
    main()
