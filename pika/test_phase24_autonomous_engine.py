from __future__ import annotations

from pathlib import Path

from core.autonomous_engine import (
    AutonomousEngineeringEngine,
)


ROOT = Path(__file__).resolve().parent

DEMO = ROOT / "phase24_demo.py"
TEST = ROOT / "test_phase24_demo.py"


OLD_SOURCE = """def add_numbers(a, b):
    return a - b
"""


TEST_SOURCE = """from phase24_demo import add_numbers

assert add_numbers(10, 32) == 42
"""


def actor(task: str) -> list[str]:
    print("[TEST ACTOR] Generating candidate set")

    return [
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


def main():
    print("=" * 68)
    print("PIKA PHASE 24")
    print("END-TO-END AUTONOMOUS ENGINEERING LOOP")
    print("=" * 68)

    DEMO.write_text(
        OLD_SOURCE,
        encoding="utf-8",
    )

    TEST.write_text(
        TEST_SOURCE,
        encoding="utf-8",
    )

    task = (
        "Write a Python function named "
        "add_numbers that adds two numbers."
    )

    print()
    print("TASK:")
    print(task)

    print()
    print("INITIAL SOURCE:")
    print(DEMO.read_text())

    print()
    print("STARTING AUTONOMOUS ENGINEERING...")

    engine = AutonomousEngineeringEngine(
        workspace_root=str(ROOT),
        actor=actor,
        max_candidates=3,
    )

    result = engine.run(
        task=task,
        relative_path="phase24_demo.py",
        old_text=OLD_SOURCE,
        test_path="test_phase24_demo.py",
    )

    final_source = DEMO.read_text(
        encoding="utf-8"
    )

    print()
    print("=" * 68)
    print("PHASE 24 RESULT")
    print("=" * 68)

    print()
    print("SUCCESS:")
    print(result["success"])

    print()
    print("CANDIDATE COUNT:")
    print(result["candidate_count"])

    print()
    print("CRITIC RANKING:")

    for item in result["ranking"]:
        print(
            f"Rank {item['rank']}: "
            f"candidate #{item['original_index']} "
            f"score={item['score']} "
            f"critic={item['critic_passed']}"
        )

    print()
    print("EXECUTION ATTEMPTS:")

    for attempt in result["attempts"]:
        print(
            f"Attempt {attempt['attempt']}: "
            f"stage={attempt['stage']} "
            f"success={attempt['success']}"
        )

    print()
    print("FINAL SOURCE:")
    print(final_source)

    print()
    print("FINAL VALIDATION:")
    print(result["validation"])

    print()
    print("FINAL TEST:")
    print(result["test"])

    passed = (
        result["success"]
        and result["candidate_count"] == 3
        and len(result["attempts"]) >= 2
        and "return a + b" in final_source
        and "return a - b" not in final_source
        and "return a * b" not in final_source
        and result["validation"]["success"]
        and result["test"]["success"]
    )

    print()

    if passed:
        print(
            "PIKA PHASE 24 AUTONOMOUS ENGINEERING TEST: PASSED"
        )
    else:
        print(
            "PIKA PHASE 24 AUTONOMOUS ENGINEERING TEST: FAILED"
        )

    DEMO.unlink(missing_ok=True)
    TEST.unlink(missing_ok=True)

    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
