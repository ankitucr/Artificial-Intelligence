from pathlib import Path
from core.experience_learner import ExperienceLearner


ROOT = Path(__file__).resolve().parent
STORE = ROOT / "data" / "phase20" / "experience_test.json"


def main():
    print("=" * 60)
    print("PIKA PHASE 20")
    print("EXPERIENCE LEARNING LOOP")
    print("=" * 60)

    if STORE.exists():
        STORE.unlink()

    learner = ExperienceLearner(STORE)

    task = (
        "Write a Python function named "
        "add_numbers that adds two numbers."
    )

    candidates = [
        {
            "candidate": (
                "def wrong_function(a, b):\n"
                "    return a + b"
            ),
            "rank": 2,
            "quality_score": -10.0,
            "passed_critic": False,
            "success": False,
        },
        {
            "candidate": (
                "def add_numbers(a, b):\n"
                "    return a + b"
            ),
            "rank": 1,
            "quality_score": 1100.0,
            "passed_critic": True,
            "success": True,
        },
    ]

    final_result = {
        "success": True,
    }

    print()
    print("LEARNING FROM PHASE 19 RESULT...")

    experience = learner.learn(
        task,
        candidates,
        final_result,
    )

    print()
    print("EXPERIENCE:")
    print(experience)

    print()
    print("RANKING SIGNAL:")

    signal = learner.get_ranking_signal(
        task
    )

    print(signal)

    print()
    print("STATS:")

    stats = learner.stats()

    print(stats)

    stored = STORE.exists()

    passed = (
        experience["success"] is True
        and experience["lesson"]["type"]
        == "success"
        and signal["known"] is True
        and signal["relevant_experiences"] >= 1
        and stats["experiences"] == 1
        and stats["successes"] == 1
        and stats["failures"] == 0
        and stored
    )

    print()

    if passed:
        print(
            "PIKA PHASE 20 EXPERIENCE-LEARNING TEST: PASSED"
        )
    else:
        print(
            "PIKA PHASE 20 EXPERIENCE-LEARNING TEST: FAILED"
        )

    if STORE.exists():
        STORE.unlink()

    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
