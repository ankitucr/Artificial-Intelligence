
import importlib.util
import json

MODULE_PATH = '/data/data/com.termux/files/home/bee5/candidate_skills/skill_module_131.py'
FUNCTION_NAME = 'is_prime'
TESTS = json.loads('[{"args": [25], "kwargs": {}, "expected": false}, {"args": [23], "kwargs": {}, "expected": true}, {"args": [1], "kwargs": {}, "expected": false}, {"args": [37], "kwargs": {}, "expected": true}, {"args": [48], "kwargs": {}, "expected": false}]')


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
        return sorted(
            [normalize(v) for v in value],
            key=repr
        )

    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass

    return value


spec = importlib.util.spec_from_file_location(
    "determinism_candidate",
    MODULE_PATH
)

module = importlib.util.module_from_spec(
    spec
)

spec.loader.exec_module(
    module
)

fn = getattr(
    module,
    FUNCTION_NAME
)

for index, test in enumerate(
    TESTS,
    start=1
):

    first = normalize(
        fn(
            *test.get("args", []),
            **test.get("kwargs", {})
        )
    )

    second = normalize(
        fn(
            *test.get("args", []),
            **test.get("kwargs", {})
        )
    )

    if first != second:
        print(
            json.dumps(
                {
                    "passed": False,
                    "test": index,
                    "first": first,
                    "second": second
                }
            )
        )
        raise SystemExit(2)

print(
    json.dumps(
        {
            "passed": True
        }
    )
)
