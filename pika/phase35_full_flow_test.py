from pathlib import Path
import tempfile

from core.phase33_controller import Phase33Controller
from core.semantic_code_memory import SemanticCodeMemory
from core.brain import _phase35_save_repair


def check(condition, message):
    if not condition:
        raise AssertionError("FAIL: " + message)
    print("PASS:", message)


def main():
    with tempfile.TemporaryDirectory(prefix="pika_full_flow_") as tmp:
        root = Path(tmp)
        target = root / "discount.py"
        test_file = root / "test_discount.py"
        db_path = root / "semantic_memory.json"

        original = (
            "def discount(price, percent):\n"
            "    return price - percent\n"
        )
        wrong = (
            "def discount(price, percent):\n"
            "    return price + percent\n"
        )
        correct = (
            "def discount(price, percent):\n"
            "    return price * (1 - percent / 100)\n"
        )
        context = {
            "target_path": "discount.py",
            "old_text": original,
            "test_path": "test_discount.py",
        }
        task = "Fix percentage discount calculation"

        target.write_text(original, encoding="utf-8")
        test_file.write_text(
            "from discount import discount\n"
            "assert discount(100, 20) == 80\n"
            "assert discount(200, 10) == 180\n"
            "assert discount(50, 0) == 50\n"
            "print('INDEPENDENT TEST PASS')\n",
            encoding="utf-8",
        )

        controller = Phase33Controller(
            root,
            max_candidates=3,
            learning_memory_path=root / "learning.json",
        )

        print("\n=== STEP 1: WRONG CANDIDATE FIRST ===")
        result = controller.repair(
            diagnosis={
                "error_type": "test_failure",
                "root_cause": "Percentage formula is incorrect",
                "error_message": "Expected discount(100, 20) == 80",
            },
            relative_path="discount.py",
            old_text=original,
            candidates=[wrong, correct],
            test_path="test_discount.py",
            task=task,
        )

        repair = result.get("repair", {})
        attempts = repair.get("attempts", [])
        print("Attempt stages:", [a.get("stage") for a in attempts])

        check(result.get("success") is True, "correct candidate recovered")
        check(result.get("test_passed") is True, "test, validation and commit passed")
        check(len(attempts) >= 2, "engine attempted more than one candidate")
        check(attempts[0].get("success") is False, "wrong first candidate rejected")
        check(
            attempts[0].get("stage") == "test"
            and attempts[0].get("rollback", {}).get("success") is True,
            "failed candidate rolled back",
        )
        check(
            repair.get("accepted_candidate") == correct
            or repair.get("final_candidate") == correct
            or result.get("accepted_candidate") == correct,
            "correct candidate is the accepted candidate",
        )
        check(target.read_text(encoding="utf-8") == correct,
              "only correct code remains committed")

        print("\n=== STEP 2: SAVE VERIFIED REPAIR ===")
        memory = SemanticCodeMemory(db_path)
        saved = _phase35_save_repair(
            memory,
            task,
            [wrong, correct],
            result,
            {"root_cause": "Percentage formula is incorrect"},
            replay_context=context,
        )
        check(saved is True, "verified repair saved to semantic memory")

        reloaded = SemanticCodeMemory(db_path)
        hits = reloaded.retrieve(task, verified_only=True, limit=5)
        match = next(
            (v for v in hits if v.get("code") == correct),
            None,
        )
        check(match is not None, "saved repair survived database reload")
        check(
            match.get("replay_context") == context,
            "replay context survived database reload",
        )

        print("\n=== STEP 3: REPLAY SAVED REPAIR ===")
        # Reset only this disposable test fixture to recreate the same failure.
        target.write_text(original, encoding="utf-8")
        replay = controller.repair(
            diagnosis={
                "error_type": "test_failure",
                "root_cause": "Percentage formula is incorrect",
                "error_message": "Expected discount(100, 20) == 80",
            },
            relative_path=match["replay_context"]["target_path"],
            old_text=match["replay_context"]["old_text"],
            candidates=[match["code"]],
            test_path=match["replay_context"]["test_path"],
            task=task,
        )
        check(replay.get("success") is True, "replayed repair passed")
        check(replay.get("test_passed") is True, "replayed repair passed test and commit")
        check(target.read_text(encoding="utf-8") == correct,
              "replay committed the correct implementation")

        print("\n=== FINAL REPORT ===")
        print("FULL FLOW: PASS")
        print("wrong candidate -> test failure -> rollback")
        print("-> next candidate -> independent test -> commit")
        print("-> persistent memory -> reload -> successful replay")
        print("Production workspace and production memory were not used.")


if __name__ == "__main__":
    main()
