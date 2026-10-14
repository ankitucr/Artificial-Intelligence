from __future__ import annotations

import tempfile
from pathlib import Path

from core.critic_repair import CriticRepairEngine


TASK = (
    "Write a Python function named add_numbers "
    "that adds two numbers."
)

OLD_CODE = """def add_numbers(a, b):
    return a - b
"""

WRONG_CANDIDATE = """def wrong_name(a, b):
    return a + b
"""

CORRECT_CANDIDATE = """def add_numbers(a, b):
    return a + b
"""

TEST_CODE = """from demo import add_numbers

assert add_numbers(2, 3) == 5
assert add_numbers(10, 32) == 42

print("REPAIR TEST PASSED")
"""


def main():
    print("=" * 64)
    print("PIKA PHASE 18")
    print("CRITIC -> REPAIR -> SELF-HEALING INTEGRATION TEST")
    print("=" * 64)
    print()

    with tempfile.TemporaryDirectory(
        prefix="pika_phase18_"
    ) as tmp:

        root = Path(tmp)

        demo = root / "demo.py"
        test_file = root / "test_demo.py"

        demo.write_text(OLD_CODE)
        test_file.write_text(TEST_CODE)

        engine = CriticRepairEngine(
            workspace_root=str(root),
            max_retries=2,
        )

        print("INITIAL CODE:")
        print(demo.read_text())

        print("CANDIDATES:")
        print("1. Wrong function name")
        print("2. Correct implementation")
        print()

        result = engine.repair(
            task=TASK,
            relative_path="demo.py",
            old_text=OLD_CODE,
            candidates=[
                WRONG_CANDIDATE,
                CORRECT_CANDIDATE,
            ],
            test_path="test_demo.py",
        )

        print("=" * 64)
        print("PHASE 18 RESULT")
        print("=" * 64)
        print()

        print("CRITIC REVIEW:")
        print(
            result["review"]
        )

        print()
        print("REPAIR RESULT:")
        print(
            result.get("repair")
        )

        print()
        print("FINAL CODE:")
        print(demo.read_text())

        passed = (
            result.get("success") is True
            and "return a + b"
            in demo.read_text()
        )

        print()

        if passed:
            print(
                "PIKA PHASE 18 "
                "CRITIC-REPAIR TEST: PASSED"
            )
        else:
            print(
                "PIKA PHASE 18 "
                "CRITIC-REPAIR TEST: FAILED"
            )

        raise SystemExit(
            0 if passed else 1
        )


if __name__ == "__main__":
    main()
