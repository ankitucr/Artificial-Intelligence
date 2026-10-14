from pathlib import Path

from core.critic import Critic
from core.candidate_ranker import CandidateRanker
from core.experience_learner import ExperienceLearner


ROOT = Path(__file__).resolve().parent
STORE = (
    ROOT
    / "data"
    / "phase21"
    / "experience.json"
)


def main():
    print("=" * 60)
    print("PIKA PHASE 21")
    print("LEARNING-AWARE DECISION MAKING")
    print("=" * 60)

    STORE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if STORE.exists():
        STORE.unlink()

    learner = ExperienceLearner(
        STORE
    )

    critic = Critic()

    ranker = CandidateRanker(
        critic,
        learner=learner,
    )

    task = (
        "Write a Python function named "
        "add_numbers that adds two numbers."
    )

    successful_candidate = """def add_numbers(a, b):
    return a + b
"""

    failed_candidate = """def wrong_function(a, b):
    return a + b
"""

    print()
    print("SEEDING PREVIOUS EXPERIENCE...")

    learner.learn(
        task,
        [
            {
                "candidate": successful_candidate,
                "rank": 1,
                "quality_score": 1100.0,
                "passed_critic": True,
                "success": True,
            },
            {
                "candidate": failed_candidate,
                "rank": 2,
                "quality_score": -10.0,
                "passed_critic": False,
                "success": False,
            },
        ],
        {
            "success": True,
        },
    )

    print()
    print("PREVIOUS EXPERIENCE:")
    print(
        learner.get_candidate_signal(
            successful_candidate
        )
    )

    print(
        learner.get_candidate_signal(
            failed_candidate
        )
    )

    # Deliberately reverse the order.
    candidates = [
        failed_candidate,
        successful_candidate,
    ]

    print()
    print(
        "NEW CANDIDATE ORDER: "
        "previously failed candidate FIRST"
    )

    ranked = ranker.rank(
        task,
        candidates,
    )

    print()
    print("NEW RANKING:")

    for item in ranked:
        print(
            f"Rank {item['rank']}: "
            f"original #{item['original_index'] + 1} "
            f"critic={item['critic_score']:.1f} "
            f"learning={item['learning_bonus']:.1f} "
            f"final={item['quality_score']:.1f}"
        )

    best = ranked[0]

    print()
    print("BEST CANDIDATE:")
    print(best["candidate"])

    passed = (
        best["candidate"].strip()
        == successful_candidate.strip()
        and best["rank"] == 1
        and best["learning"]["known"] is True
        and best["learning_bonus"] > 0
    )

    print()

    if passed:
        print(
            "PIKA PHASE 21 LEARNING-DECISION TEST: PASSED"
        )
    else:
        print(
            "PIKA PHASE 21 LEARNING-DECISION TEST: FAILED"
        )

    if STORE.exists():
        STORE.unlink()

    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
