from core.critic import Critic


def main():

    print("=" * 60)
    print("PIKA PHASE 16")
    print("ACTOR → CRITIC → FEEDBACK TEST")
    print("=" * 60)

    critic = Critic()

    task = (
        "Write a Python function named add_numbers "
        "that adds two numbers."
    )

    # --------------------------------------------------
    # Actor produces intentionally bad output.
    # --------------------------------------------------

    bad_output = """
def wrong_name(a, b):
    return a + b
"""

    print()
    print("ACTOR OUTPUT #1:")
    print(bad_output)

    review1 = critic.review(
        task,
        bad_output,
    )

    print()
    print("CRITIC REVIEW #1:")
    print(review1)

    # --------------------------------------------------
    # Actor receives Critic feedback and corrects output.
    # --------------------------------------------------

    good_output = """
def add_numbers(a, b):
    return a + b
"""

    print()
    print("ACTOR OUTPUT #2:")
    print(good_output)

    review2 = critic.review(
        task,
        good_output,
    )

    print()
    print("CRITIC REVIEW #2:")
    print(review2)

    # --------------------------------------------------
    # Required behavior
    # --------------------------------------------------

    passed = (
        review1["passed"] is False
        and len(review1["issues"]) > 0
        and review2["passed"] is True
        and review2["score"] == 1.0
        and review2["checks"]["python_syntax"] is True
        and review2["checks"]["requested_function"] is True
    )

    print()

    if passed:
        print(
            "PIKA PHASE 16 CRITIC TEST: PASSED"
        )
    else:
        print(
            "PIKA PHASE 16 CRITIC TEST: FAILED"
        )


if __name__ == "__main__":
    main()
