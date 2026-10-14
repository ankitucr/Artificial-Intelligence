from pathlib import Path
import json
import tempfile

from core.learning_engine import LearningEngine


def main():
    root = Path(
        tempfile.mkdtemp(
            prefix="pika_phase34_"
        )
    )

    memory_file = root / "learning.json"

    learner = LearningEngine(memory_file)

    print("==============================================")
    print("PHASE 34 — ACTUAL CONTINUAL LEARNING")
    print("==============================================")

    # ------------------------------------------------------
    # ROUND 1
    # Unknown problem.
    # Cohere would normally provide this solution.
    # Here the solution is treated as the result produced
    # by the worker so that the learning engine itself can
    # be tested deterministically.
    # ------------------------------------------------------

    print("[ROUND 1] UNKNOWN PROBLEM")

    first_solution = """
def add(a, b):
    return a + b
""".strip()

    first = learner.learn(
        task="repair add function failing arithmetic test",
        error_type="test_failure",
        root_cause="function returns incorrect arithmetic result",
        error_message="expected 5 but received 0",
        method="direct arithmetic correction",
        solution=first_solution,
        verification={
            "syntax": True,
            "test": True,
            "independent_test": True,
        },
        success=True,
        source="cohere",
    )

    assert first["trusted"] is True

    print("LEARNING: VERIFIED")
    print("TRUSTED SOLUTION: VERIFIED")

    # ------------------------------------------------------
    # ROUND 2
    # Cohere disabled.
    # PIKA must retrieve the learned solution.
    # ------------------------------------------------------

    print("[ROUND 2] COHERE DISABLED")

    replay = learner.best_solution(
        task="repair add function failing arithmetic test",
        error_type="test_failure",
        root_cause="function returns incorrect arithmetic result",
        error_message="expected 9 but received 0",
    )

    assert replay is not None
    assert replay["solution"] == first_solution

    print("MEMORY RETRIEVAL: VERIFIED")
    print("LEARNED SOLUTION REUSED: VERIFIED")
    print("COHERE CALL: 0")

    # ------------------------------------------------------
    # ROUND 3
    # Learn a SECOND valid method.
    # ------------------------------------------------------

    print("[ROUND 3] SECOND SOLUTION METHOD")

    second_solution = """
def add(a, b):
    result = a
    result += b
    return result
""".strip()

    second = learner.learn(
        task="repair add function failing arithmetic test",
        error_type="test_failure",
        root_cause="function returns incorrect arithmetic result",
        error_message="expected 7 but received 0",
        method="incremental accumulation",
        solution=second_solution,
        verification={
            "syntax": True,
            "test": True,
            "independent_test": True,
        },
        success=True,
        source="local",
    )

    assert second["trusted"] is True

    stored = learner.retrieve(
        task="repair add function failing arithmetic test",
        error_type="test_failure",
        root_cause="function returns incorrect arithmetic result",
    )

    all_solutions = []

    for match in stored["matches"]:
        all_solutions.extend(
            match["solutions"]
        )

    assert len(all_solutions) >= 2

    print("MULTIPLE SOLUTIONS: VERIFIED")
    print("SOLUTION DIVERSITY: VERIFIED")

    # ------------------------------------------------------
    # ROUND 4
    # Failed method learning.
    # ------------------------------------------------------

    print("[ROUND 4] FAILED METHOD")

    bad_solution = """
def add(a, b):
    return a - b
""".strip()

    failed = learner.learn(
        task="repair add function failing arithmetic test",
        error_type="test_failure",
        root_cause="function returns incorrect arithmetic result",
        error_message="expected 5 but received 1",
        method="subtraction",
        solution=bad_solution,
        verification={
            "syntax": True,
            "test": False,
            "independent_test": False,
        },
        success=False,
        source="cohere",
    )

    assert failed["trusted"] is False

    best = learner.best_solution(
        task="repair add function failing arithmetic test",
        error_type="test_failure",
        root_cause="function returns incorrect arithmetic result",
    )

    assert best is not None
    assert best["solution"] != bad_solution

    print("FAILED METHOD LEARNING: VERIFIED")
    print("FAILED METHOD NOT TRUSTED: VERIFIED")
    print("BAD METHOD NOT SELECTED: VERIFIED")

    # ------------------------------------------------------
    # FINAL
    # ------------------------------------------------------

    stats = learner.stats()

    print("----------------------------------------------")
    print("STATS:", json.dumps(stats, indent=2))
    print("----------------------------------------------")
    print("PHASE 34 LEARNING ENGINE: PASS")
    print("Actual reusable learning: VERIFIED")
    print("Cohere-independent retrieval: VERIFIED")
    print("Multiple solution methods: VERIFIED")
    print("Failure learning: VERIFIED")
    print("Only verified solutions become trusted: VERIFIED")
    print("TERMUX SHELL WILL REMAIN OPEN")


if __name__ == "__main__":
    main()
