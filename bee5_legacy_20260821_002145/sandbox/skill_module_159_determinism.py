
import importlib.util
import json

MODULE_PATH = '/data/data/com.termux/files/home/bee5/candidate_skills/skill_module_159.py'
FUNCTION_NAME = 'modular_pow'
TESTS = json.loads('[{"args": [2, 10, 1000], "kwargs": {}, "expected": 24}, {"args": [5, 0, 7], "kwargs": {}, "expected": 1}, {"args": [10, 5, 1], "kwargs": {}, "expected": 0}, {"args": [3, 200, 13], "kwargs": {}, "expected": 9}]')


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
