from memory.manager import MemoryManager


def main():

    print("=" * 60)
    print("PIKA PHASE 6")
    print("PERSISTENT MEMORY + LEARNING TEST")
    print("=" * 60)

    memory = MemoryManager()

    before = memory.stats()

    print()
    print("MEMORY BEFORE:")
    print(before)

    test_episode = {
        "timestamp": "phase6-test",
        "task": "create python add_numbers function",
        "outcome": "success",
        "evaluation": {
            "passed": True,
            "score": 1.0,
        },
    }

    test_failure = {
        "task": "create python add_numbers function",
        "attempt": 1,
        "evaluation": {
            "passed": False,
            "issues": [
                "syntax validation failed"
            ],
        },
    }

    test_lesson = {
        "type": "success",
        "task": "create python add_numbers function",
        "rule": (
            "Validate Python syntax before accepting "
            "generated code."
        ),
    }

    memory.remember_episode(
        test_episode
    )

    memory.remember_failure(
        test_failure
    )

    memory.remember_lesson(
        test_lesson
    )

    print()
    print("MEMORY AFTER WRITE:")
    print(memory.stats())

    # New MemoryManager = simulated PIKA restart.
    reloaded = MemoryManager()

    print()
    print("MEMORY AFTER RELOAD:")
    print(reloaded.stats())

    retrieved = reloaded.retrieve(
        "python add_numbers function",
        limit=10,
    )

    print()
    print("RETRIEVED MEMORY:")
    print(
        "episodes:",
        len(retrieved["episodes"]),
    )

    print(
        "failures:",
        len(retrieved["failures"]),
    )

    print(
        "lessons:",
        len(retrieved["lessons"]),
    )

    passed = (
        len(reloaded.episodes) >= 1
        and len(reloaded.failures) >= 1
        and len(reloaded.lessons) >= 1
        and len(retrieved["episodes"]) >= 1
        and len(retrieved["failures"]) >= 1
        and len(retrieved["lessons"]) >= 1
    )

    print()

    if passed:
        print(
            "PIKA PHASE 6 MEMORY TEST: PASSED"
        )
    else:
        print(
            "PIKA PHASE 6 MEMORY TEST: FAILED"
        )


if __name__ == "__main__":
    main()
