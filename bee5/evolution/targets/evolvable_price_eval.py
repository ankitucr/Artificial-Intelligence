#!/usr/bin/env python3

import importlib.util
import json
import sys
from pathlib import Path


def load_target(path: Path):
    spec = importlib.util.spec_from_file_location("evolvable_target", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load candidate module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "format_price"):
        raise RuntimeError("Candidate must provide format_price(value)")
    return module


TESTS = [
    (12, "$12.00"),
    (1234, "$1,234.00"),
    (1234567.5, "$1,234,567.50"),
    (0, "$0.00"),
]


def evaluate(path: Path):
    module = load_target(path)
    passed = 0
    failures = []

    for index, (source, expected) in enumerate(TESTS, start=1):
        try:
            actual = module.format_price(source)
        except Exception as exc:
            actual = None
            failures.append({"test": index, "error": repr(exc)})
            continue

        if actual == expected:
            passed += 1
        else:
            failures.append({
                "test": index,
                "input": source,
                "expected": expected,
                "actual": actual,
            })

    return {"passed": passed, "total": len(TESTS), "score": passed, "failures": failures}


def main():
    if len(sys.argv) != 2:
        print("Usage: python evolvable_price_eval.py <candidate.py>")
        return 1
    path = Path(sys.argv[1])
    if not path.exists():
        print(json.dumps({"ok": False, "error": f"File not found: {path}"}, indent=2))
        return 2
    try:
        result = evaluate(path)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": repr(exc)}, indent=2))
        return 3
    result["ok"] = True
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
