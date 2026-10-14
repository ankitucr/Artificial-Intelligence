
import importlib.util
import json
import traceback

MODULE_PATH = '/data/data/com.termux/files/home/bee5/candidate_skills/skill_module_164.py'
FUNCTION_NAME = 'longest_common_subsequence'
TESTS = json.loads('[{"args": ["ABCBDAB", "BDCABA"], "kwargs": {}, "expected": "BCBA"}, {"args": ["ABCDEFG", "ABCDEFG"], "kwargs": {}, "expected": "ABCDEFG"}, {"args": ["ABCDEFG", "HIJKLMN"], "kwargs": {}, "expected": ""}, {"args": ["", "ABCDEFG"], "kwargs": {}, "expected": ""}, {"args": ["", ""], "kwargs": {}, "expected": ""}]')


def normalize(value):

    if isinstance(value, dict):
        return {
            str(k): normalize(v)
            for k, v in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            normalize(v)
            for v in value
        ]

    if isinstance(value, set):
        result = [
            normalize(v)
            for v in value
        ]

        return sorted(
            result,
            key=repr
        )

    if isinstance(
        value,
        (str, int, float, bool)
    ) or value is None:

        return value

    if hasattr(
        value,
        "isoformat"
    ):

        try:
            return value.isoformat()
        except Exception:
            pass

    return repr(value)


spec = importlib.util.spec_from_file_location(
    "bee5_candidate",
    MODULE_PATH
)

if spec is None or spec.loader is None:
    raise RuntimeError(
        "Could not load candidate module"
    )

module = importlib.util.module_from_spec(
    spec
)

spec.loader.exec_module(
    module
)

if not hasattr(
    module,
    FUNCTION_NAME
):
    raise RuntimeError(
        f"Missing function: {FUNCTION_NAME}"
    )

fn = getattr(
    module,
    FUNCTION_NAME
)

results = []
passed = 0

for index, test in enumerate(
    TESTS,
    start=1
):

    try:

        actual = fn(
            *test.get("args", []),
            **test.get("kwargs", {})
        )

        actual = normalize(
            actual
        )

        expected = test.get(
            "expected"
        )

        ok = actual == expected

        if ok:
            passed += 1

        results.append({
            "test": index,
            "passed": ok,
            "expected": expected,
            "actual": actual
        })

    except Exception as exc:

        results.append({
            "test": index,
            "passed": False,
            "error": (
                f"{type(exc).__name__}: {exc}"
            )
        })

print(
    json.dumps(
        {
            "passed": passed,
            "total": len(TESTS),
            "results": results
        },
        ensure_ascii=False
    )
)

if passed != len(TESTS):
    raise SystemExit(2)
