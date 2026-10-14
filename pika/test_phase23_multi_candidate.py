from pathlib import Path

from core.multi_candidate_engine import MultiCandidateEngine


ROOT = Path(__file__).resolve().parent
DEMO = ROOT / "phase23_demo.py"
TEST = ROOT / "test_phase23_demo.py"


OLD = """def add_numbers(a, b):
    return a - b
"""


CANDIDATES = [
    """def wrong_name(a, b):
    return a + b
""",
    """def add_numbers(a, b):
    return a * b
""",
    """def add_numbers(a, b):
    return a + b
""",
]


TEST_SOURCE = """from phase23_demo import add_numbers

assert add_numbers(10, 32) == 42
"""


def main():
    print("=" * 64)
    print("PIKA PHASE 23")
    print("MULTI-CANDIDATE AUTONOMOUS REPAIR")
    print("=" * 64)

    DEMO.write_text(
        OLD,
        encoding="utf-8",
    )

    TEST.write_text(
        TEST_SOURCE,
        encoding="utf-8",
    )

    task = (
        "Write a Python function named add_numbers "
        "that adds two numbers."
    )

    engine = MultiCandidateEngine(
        ROOT,
        max_candidates=3,
    )

    print()
    print("TASK:")
    print(task)

    print()
    print("CANDIDATES:")
    for i, candidate in enumerate(
        CANDIDATES,
        start=1,
    ):
        print(f"{i}.")
        print(candidate.rstrip())

    print()
    print("STARTING MULTI-CANDIDATE LOOP...")

    result = engine.repair(
        task=task,
        relative_path="phase23_demo.py",
        old_text=OLD,
        candidates=CANDIDATES,
        test_path="test_phase23_demo.py",
    )

    print()
    print("=" * 64)
    print("PHASE 23 RESULT")
    print("=" * 64)

    print()
    print("SUCCESS:")
    print(result["success"])

    print()
    print("RANKING:")
    for item in result["ranking"]:
        print(
            f"Rank {item['rank']}: "
            f"candidate #{item['original_index']} "
            f"score={item['score']} "
            f"critic={item['critic_passed']}"
        )

    print()
    print("ATTEMPTS:")
    for attempt in result.get("attempts", []):
        print(
            f"Attempt {attempt['attempt']}: "
            f"success={attempt['success']}"
        )

    print()
    print("FINAL CANDIDATE:")
    print(
        result.get(
            "final_candidate",
            "<none>",
        )
    )

    final_code = DEMO.read_text(
        encoding="utf-8"
    )

    print()
    print("FINAL CODE:")
    print(final_code)

    passed = (
        result["success"]
        and "return a + b" in final_code
        and "return a - b" not in final_code
        and "return a * b" not in final_code
    )

    print()
    if passed:
        print(
            "PIKA PHASE 23 MULTI-CANDIDATE TEST: PASSED"
        )
    else:
        print(
            "PIKA PHASE 23 MULTI-CANDIDATE TEST: FAILED"
        )

    DEMO.unlink(missing_ok=True)
    TEST.unlink(missing_ok=True)

    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
