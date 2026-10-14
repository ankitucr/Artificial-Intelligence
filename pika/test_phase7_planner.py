from core.planner import Planner


def main():

    print("=" * 60)
    print("PIKA PHASE 7")
    print("MEMORY → ADAPTIVE PLANNER TEST")
    print("=" * 60)

    planner = Planner()

    task = (
        "Write a Python function named add_numbers "
        "that adds two numbers."
    )

    # ---------------------------------------------------------
    # Simulated persistent memory
    # ---------------------------------------------------------

    memories = {
        "query": task,

        "episodes": [
            {
                "task": task,
                "outcome": "success",
            }
        ],

        "failures": [
            {
                "task": task,
                "evaluation": {
                    "issues": [
                        "Python syntax validation failed"
                    ]
                }
            }
        ],

        "lessons": [
            {
                "type": "success",
                "task": task,
                "rule": (
                    "Validate Python syntax before "
                    "accepting generated code."
                ),
            }
        ],

        "skills": [],
        "knowledge": [],
    }

    plan = planner.plan(
        task,
        memories=memories,
    )

    print()
    print("TASK:")
    print(task)

    print()
    print("ADAPTIVE PLAN:")

    for index, step in enumerate(
        plan,
        start=1,
    ):
        print(
            f"{index}. {step}"
        )

    plan_text = "\n".join(plan).lower()

    required = [
        "previous successful experiences",
        "previous failures",
        "learned lessons",
        "evaluate",
        "persistent memory",
    ]

    missing = [
        item
        for item in required
        if item not in plan_text
    ]

    print()
    print("MEMORY-AWARE CHECK:")

    if not missing:
        print("Previous experience: USED")
        print("Previous failures: USED")
        print("Learned lessons: USED")
        print("Evaluation planning: USED")
        print("Persistent memory planning: USED")

        print()
        print(
            "PIKA PHASE 7 PLANNER TEST: PASSED"
        )

    else:
        print(
            "Missing planner signals:",
            missing,
        )

        print()
        print(
            "PIKA PHASE 7 PLANNER TEST: FAILED"
        )


if __name__ == "__main__":
    main()
