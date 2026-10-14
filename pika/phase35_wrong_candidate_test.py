from pathlib import Path
import tempfile

from core.phase33_controller import Phase33Controller

with tempfile.TemporaryDirectory(prefix="pika_wrong_candidate_") as tmp:
    root = Path(tmp)
    target = root / "discount.py"
    tests = root / "test_discount.py"

    target.write_text(
        "def discount(price, percent):\n"
        "    return price - percent\n",
        encoding="utf-8",
    )

    tests.write_text(
        "from discount import discount\n"
        "assert discount(100, 20) == 80\n"
        "assert discount(200, 10) == 180\n"
        "assert discount(50, 0) == 50\n"
        "print('INDEPENDENT TEST PASS')\n",
        encoding="utf-8",
    )

    controller = Phase33Controller(root, max_candidates=3)
    diagnosis = {
        "error_type": "test_failure",
        "root_cause": "Percentage must be applied to original price",
        "error_message": "discount(100, 20) must return 80",
    }

    wrong_candidate = (
        "def discount(price, percent):\n"
        "    return price + percent\n"
    )

    result = controller.repair(
        diagnosis=diagnosis,
        relative_path="discount.py",
        old_text="def discount(price, percent):\n    return price - percent\n",
        candidates=[wrong_candidate],
        test_path="test_discount.py",
        task="Fix percentage discount calculation",
    )

    print("\n========== WRONG CANDIDATE RESULT ==========")
    print("success:", result.get("success"))
    print("test_passed:", result.get("test_passed"))
    print("accepted_candidate:", repr(result.get("accepted_candidate")))
    print("result:", result)
    print("final file:\n", target.read_text(encoding="utf-8"))

    if result.get("success") is True:
        if result.get("test_passed") is not True:
            raise AssertionError("BUG: repair succeeded without passing independent tests")
        if "return price + percent" in target.read_text(encoding="utf-8"):
            raise AssertionError("BUG: wrong candidate was committed")
        print("CHECK: wrong candidate was not committed as the final repair.")
    else:
        print("CHECK: wrong candidate was rejected; repair reported failure.")

print("TERMUX SHELL WILL REMAIN OPEN")
