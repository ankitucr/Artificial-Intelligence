from pathlib import Path

from core.self_healing import SelfHealingEngine


ROOT = Path(__file__).resolve().parent


def main():
    print("=" * 60)
    print("PIKA PHASE 19")
    print("CRITIC-GUIDED CANDIDATE RANKING")
    print("=" * 60)

    demo = ROOT / "demo_phase19.py"
    test_file = ROOT / "test_phase19_demo.py"

    original = """def add_numbers(a, b):
    return a - b
"""

    wrong_candidate = """def wrong_function(a, b):
    return a + b
"""

    correct_candidate = """def add_numbers(a, b):
    return a + b
"""

    test_code = """from demo_phase19 import add_numbers

assert add_numbers(10, 32) == 42
print("PHASE 19 REAL TEST PASSED")
"""

    demo.write_text(original)
    test_file.write_text(test_code)

    engine = SelfHealingEngine(
        ROOT,
        max_retries=1,
    )

    task = (
        "Write a Python function named "
        "add_numbers that adds two numbers."
    )

    print()
    print("INITIAL CODE:")
    print(original)

    print("CANDIDATES:")
    print("1. wrong function")
    print("2. correct implementation")

    print()
    print("STARTING CRITIC RANKING + REPAIR...")
    
    result = engine.repair_candidates(
        relative_path="demo_phase19.py",
        old_text=original,
        candidates=[
            wrong_candidate,
            correct_candidate,
        ],
        test_path="test_phase19_demo.py",
        task=task,
    )

    print()
    print("=" * 60)
    print("PHASE 19 RESULT")
    print("=" * 60)

    print()
    print("SUCCESS:")
    print(result["success"])

    print()
    print("ATTEMPTS:")
    print(len(result["attempts"]))

    print()
    print("FINAL CANDIDATE:")
    print(
        result.get(
            "final_candidate",
            "<none>",
        )
    )

    print()
    print("ATTEMPT DETAILS:")

    for attempt in result["attempts"]:
        print(
            f"Attempt {attempt['attempt']}: "
            f"success={attempt['success']}"
        )

    final_source = demo.read_text()

    print()
    print("FINAL SOURCE:")
    print(final_source)

    passed = (
        result["success"]
        and len(result["attempts"]) == 1
        and result["attempts"][0]["success"]
        and "return a + b" in final_source
        and "def add_numbers" in final_source
    )

    print()

    if passed:
        print(
            "PIKA PHASE 19 CANDIDATE-RANKING TEST: PASSED"
        )
    else:
        print(
            "PIKA PHASE 19 CANDIDATE-RANKING TEST: FAILED"
        )

    # Cleanup test artifacts.
    if demo.exists():
        demo.unlink()

    if test_file.exists():
        test_file.unlink()

    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
