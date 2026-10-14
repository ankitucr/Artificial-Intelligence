from pathlib import Path
import tempfile

from core.self_healing import SelfHealingEngine


def main():

    print("=" * 60)
    print("PIKA PHASE 14")
    print("SELF-HEALING ENGINEERING LOOP")
    print("=" * 60)

    with tempfile.TemporaryDirectory(
        prefix="pika_phase14_"
    ) as temp:

        root = Path(temp)

        source = root / "calculator.py"
        test = root / "test_calculator.py"

        # -----------------------------------------------------
        # INTENTIONALLY BROKEN PROJECT
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

        print()
        print("INITIAL STATE:")
        print(
            source.read_text(
                encoding="utf-8"
            )
        )

        engine = SelfHealingEngine(
            root,
            max_retries=2,
        )

        print()
        print("STARTING SELF-HEALING...")

        result = engine.repair(
            relative_path="calculator.py",
            old_text="return a - b",
            new_text="return a + b",
            test_path="test_calculator.py",
        )

        print()
        print("=" * 60)
        print("SELF-HEALING RESULT")
        print("=" * 60)

        print()
        print("SUCCESS:")
        print(result["success"])

        print()
        print("ATTEMPTS:")
        print(len(result["attempts"]))

        for item in result["attempts"]:
            print()
            print(
                f"Attempt {item['attempt']}: "
                f"stage={item['stage']} "
                f"success={item['success']}"
            )

        print()
        print("FINAL SOURCE:")
        print(
            source.read_text(
                encoding="utf-8"
            )
        )

        # -----------------------------------------------------
        # VERIFY ACTUAL FIX
        # -----------------------------------------------------

        final_test = engine.workspace.run_python_test(
            "test_calculator.py"
        )

        fixed = (
            result["success"]
            and final_test["success"]
            and (
                "return a + b"
                in source.read_text(
                    encoding="utf-8"
                )
            )
        )

        print()
        print("FINAL TEST:")
        print(final_test["success"])

        print()

        if fixed:
            print(
                "PIKA PHASE 14 SELF-HEALING TEST: PASSED"
            )
        else:
            print(
                "PIKA PHASE 14 SELF-HEALING TEST: FAILED"
            )


if __name__ == "__main__":
    main()
