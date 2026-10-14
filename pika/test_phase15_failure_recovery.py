from pathlib import Path
import tempfile

from core.self_healing import SelfHealingEngine


def main():

    print("=" * 60)
    print("PIKA PHASE 15")
    print("FAILURE → FEEDBACK → ROLLBACK → RETRY → PASS")
    print("=" * 60)

    with tempfile.TemporaryDirectory(
        prefix="pika_phase15_"
    ) as temp:

        root = Path(temp)

        source = root / "calculator.py"
        test = root / "test_calculator.py"

        # -----------------------------------------------------
        # INTENTIONALLY BROKEN CODE
        # -----------------------------------------------------

        source.write_text(
            "def add(a, b):\n"
            "    return a - b\n",
            encoding="utf-8",
        )

        test.write_text(
            "from calculator import add\n\n"
            "assert add(10, 32) == 42\n",
            encoding="utf-8",
        )

        engine = SelfHealingEngine(
            root,
            max_retries=2,
        )

        print()
        print("INITIAL CODE:")
        print(
            source.read_text(
                encoding="utf-8"
            )
        )

        # -----------------------------------------------------
        # FIRST CANDIDATE IS INTENTIONALLY WRONG
        # SECOND IS CORRECT
        # -----------------------------------------------------

        candidates = [
            "return a * b",
            "return a + b",
        ]

        print()
        print("CANDIDATES:")
        for index, candidate in enumerate(
            candidates,
            start=1,
        ):
            print(
                f"{index}. {candidate}"
            )

        print()
        print("STARTING FAILURE-RECOVERY LOOP...")

        result = engine.repair_candidates(
            relative_path="calculator.py",
            old_text="return a - b",
            candidates=candidates,
            test_path="test_calculator.py",
        )

        print()
        print("=" * 60)
        print("RECOVERY RESULT")
        print("=" * 60)

        print()
        print("FINAL STATUS:")
        print(result["success"])

        print()
        print("ATTEMPT COUNT:")
        print(len(result["attempts"]))

        for item in result["attempts"]:

            print()
            print(
                f"Attempt {item['attempt']}:"
            )

            print(
                "stage =",
                item["stage"],
            )

            print(
                "success =",
                item["success"],
            )

            if "candidate" in item:
                print(
                    "candidate =",
                    item["candidate"],
                )

            if "test" in item:
                test_result = item["test"]

                print(
                    "test_success =",
                    test_result["success"],
                )

                print(
                    "exit_code =",
                    test_result["returncode"],
                )

            if "rollback" in item:
                print(
                    "rollback_success =",
                    item["rollback"]["success"],
                )

        final_source = source.read_text(
            encoding="utf-8"
        )

        final_test = engine.workspace.run_python_test(
            "test_calculator.py"
        )

        print()
        print("FINAL CODE:")
        print(final_source)

        print()
        print("FINAL TEST:")
        print(final_test["success"])

        # -----------------------------------------------------
        # REQUIRED BEHAVIOR
        # -----------------------------------------------------

        first_attempt = result["attempts"][0]
        second_attempt = result["attempts"][1]

        passed = (
            result["success"]

            # First candidate must fail.
            and first_attempt["success"] is False

            # Failure must have test evidence.
            and first_attempt["test"]["success"] is False

            # Failed candidate must be rolled back.
            and first_attempt["rollback"]["success"] is True

            # Second candidate must pass.
            and second_attempt["success"] is True

            # Final project must contain correct fix.
            and "return a + b" in final_source

            # Final test must pass.
            and final_test["success"]
        )

        print()

        if passed:
            print(
                "PIKA PHASE 15 FAILURE-RECOVERY TEST: PASSED"
            )
        else:
            print(
                "PIKA PHASE 15 FAILURE-RECOVERY TEST: FAILED"
            )


if __name__ == "__main__":
    main()
