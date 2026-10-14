
import importlib.util
import json
import traceback

MODULE_PATH = '/data/data/com.termux/files/home/bee5/candidate_skills/skill_module_76.py'
TESTS = json.loads(
    '[{"function": "interval_tree_query", "args": [[[1, 3], [2, 4], [5, 6]], 2, 3], "kwargs": {}, "expected": [[1, 3], [2, 4]]}, {"function": "interval_tree_query", "args": [[[1, 3], [2, 4], [5, 6]], 0, 1], "kwargs": {}, "expected": []}, {"function": "interval_tree_query", "args": [[[1, 3], [2, 4], [5, 6]], 4, 5], "kwargs": {}, "expected": [[2, 4]]}, {"function": "interval_tree_query", "args": [[], 1, 2], "kwargs": {}, "expected": []}, {"function": "interval_tree_query", "args": [[[1, 3]], 1, 3], "kwargs": {}, "expected": [[1, 3]]}]'
)

FUNCTION_NAME = 'interval_tree_query'

spec = importlib.util.spec_from_file_location(
    "candidate_module",
    MODULE_PATH
)

if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load candidate module")

module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

if not hasattr(module, FUNCTION_NAME):
    raise RuntimeError(
        f"Missing function: {FUNCTION_NAME}"
    )

function = getattr(module, FUNCTION_NAME)

passed = 0
failed = []

for index, test in enumerate(
    TESTS,
    start=1
):
    try:
        args = test.get("args", [])
        kwargs = test.get("kwargs", {})
        expected = test.get("expected")

        actual = function(
            *args,
            **kwargs
        )

        actual_normalized = actual

        if hasattr(actual, "isoformat"):
            actual_normalized = actual.isoformat()

        if isinstance(actual, set):
            actual_normalized = sorted(actual)

        if actual_normalized != expected:
            failed.append({
                "test": index,
                "expected": expected,
                "actual": actual_normalized
            })
        else:
            passed += 1

    except Exception as exc:
        failed.append({
            "test": index,
            "error": f"{type(exc).__name__}: {exc}"
        })

print(
    json.dumps(
        {
            "passed": passed,
            "total": len(TESTS),
            "failed": failed
        },
        ensure_ascii=False
    )
)

if failed:
    raise SystemExit(2)
