import asyncio
import json
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "workspace"
TEST_ROOT = WORKSPACE / "__phase33_real_e2e__"

sys.path.insert(0, str(ROOT))

from core.phase33_controller import Phase33Controller
from core.repair_candidate_generator import RepairCandidateGenerator


def fail(message):
    raise AssertionError(message)


def assert_true(condition, message):
    if not condition:
        fail(message)


async def main():
    print("=" * 64)
    print("PHASE 33 REAL E2E — NO FAKE SUCCESS")
    print("=" * 64)

    # ------------------------------------------------------------
    # 1. Clean isolated test workspace
    # ------------------------------------------------------------
    if TEST_ROOT.exists():
        shutil.rmtree(TEST_ROOT)

    TEST_ROOT.mkdir(parents=True)

    target = TEST_ROOT / "calculator.py"
    test_file = TEST_ROOT / "test_calculator.py"

    broken_source = """def calculate():
    return 1
"""

    expected_test = """from calculator import calculate

value = calculate()

if value != 2:
    raise RuntimeError(
        f"EXPECTED 2, GOT {value}"
    )

print("REAL_PHASE33_TEST_PASS")
"""

    target.write_text(
        broken_source,
        encoding="utf-8",
    )

    test_file.write_text(
        expected_test,
        encoding="utf-8",
    )

    # ------------------------------------------------------------
    # 2. Real syntax baseline
    # ------------------------------------------------------------
    py_compile.compile(
        str(target),
        doraise=True,
    )

    print("BASELINE: broken source is syntactically valid")

    # Confirm baseline test REALLY fails.
    import subprocess

    baseline = subprocess.run(
        [
            sys.executable,
            str(test_file),
        ],
        cwd=str(TEST_ROOT),
        text=True,
        capture_output=True,
    )

    assert_true(
        baseline.returncode != 0,
        "Baseline test unexpectedly passed; test fixture is invalid.",
    )

    print("BASELINE: real test failure confirmed")

    # ------------------------------------------------------------
    # 3. Real Cohere RepairCandidateGenerator
    # ------------------------------------------------------------
    generator = RepairCandidateGenerator(
        max_candidates=3,
        workspace_root=TEST_ROOT,
    )

    worker_output = json.dumps(
        {
            "files": [
                {
                    "path": "calculator.py",
                    "content": broken_source,
                },
                {
                    "path": "test_calculator.py",
                    "content": expected_test,
                },
            ],
            "commands": [
                [
                    "python",
                    "test_calculator.py",
                ]
            ],
        }
    )

    diagnosis = {
        "error_type": "test_failure",
        "error": (
            "EXPECTED 2, GOT 1"
        ),
        "message": (
            "The test expected calculate() to return 2 "
            "but the implementation returned 1."
        ),
    }

    print()
    print("CALLING REAL RepairCandidateGenerator...")
    print("Provider must be the configured real Cohere worker.")

    generated = await generator.generate_from_failure(
        task=(
            "Fix calculator.py so calculate() returns 2 "
            "and make the provided test pass."
        ),
        diagnosis=diagnosis,
        worker_output=worker_output,
        previous_feedback="",
    )

    assert_true(
        isinstance(generated, dict),
        "Generator did not return a dictionary.",
    )

    assert_true(
        generated.get("success") is True,
        f"Real candidate generation failed: {generated}",
    )

    target_path = generated.get("target_path")
    old_text = generated.get("old_text")
    candidates = generated.get("candidates")
    test_path = generated.get("test_path")

    assert_true(
        target_path == "calculator.py",
        f"Unexpected target_path: {target_path!r}",
    )

    assert_true(
        isinstance(old_text, str) and old_text.strip(),
        "Generator returned empty old_text.",
    )

    assert_true(
        old_text in broken_source,
        "Generator old_text does not exist in the real target source.",
    )

    assert_true(
        isinstance(candidates, list)
        and 1 <= len(candidates) <= 3,
        f"Invalid candidate list: {candidates!r}",
    )

    assert_true(
        all(
            isinstance(candidate, str)
            and candidate.strip()
            and candidate != old_text
            for candidate in candidates
        ),
        "Generator returned invalid candidates.",
    )

    assert_true(
        test_path == "test_calculator.py",
        f"Unexpected test_path: {test_path!r}",
    )

    print("REAL GENERATION: VERIFIED")
    print("Generated candidates:", len(candidates))
    print("Target:", target_path)
    print("Test:", test_path)

    # ------------------------------------------------------------
    # 4. Real Phase33Controller
    # ------------------------------------------------------------
    controller = Phase33Controller(
        TEST_ROOT,
        max_candidates=3,
    )

    # ------------------------------------------------------------
    # ROOT OWNERSHIP ASSERTION
    # ------------------------------------------------------------
    print()
    print("===== REAL E2E ROOT OWNERSHIP =====")
    print("TEST_ROOT:", TEST_ROOT.resolve())
    print("TEST_ROOT EXISTS:", TEST_ROOT.exists())
    print("TARGET EXISTS:", (TEST_ROOT / target_path).exists())
    print("TEST FILE EXISTS:", (TEST_ROOT / test_path).exists())
    print("CONTROLLER ROOT:", controller.root)
    print("HEALER ROOT:", controller.healer.root)
    print(
        "CONTROLLER ROOT MATCH:",
        controller.root == TEST_ROOT.resolve(),
    )
    print(
        "HEALER ROOT MATCH:",
        controller.healer.root == TEST_ROOT.resolve(),
    )

    assert_true(
        controller.root == TEST_ROOT.resolve(),
        "Phase33Controller root mismatch.",
    )

    assert_true(
        controller.healer.root == TEST_ROOT.resolve(),
        "SelfHealingEngine root mismatch.",
    )

    assert_true(
        (TEST_ROOT / target_path).is_file(),
        f"Target missing before repair: {target_path}",
    )

    assert_true(
        (TEST_ROOT / test_path).is_file(),
        f"Test missing before repair: {test_path}",
    )

    # Direct verification through the ACTUAL healer instance.
    direct_verify = controller.healer._verify_python(
        target_path
    )

    print("DIRECT HEALER VERIFY:", direct_verify)

    assert_true(
        direct_verify.get("success") is True,
        f"Direct healer verification failed: {direct_verify}",
    )

    print("ROOT OWNERSHIP: VERIFIED")
    print("DIRECT HEALER VERIFICATION: VERIFIED")

    print()
    print("CALLING REAL Phase33Controller.repair()...")

    repair = controller.repair(
        diagnosis=diagnosis,
        relative_path=target_path,
        old_text=old_text,
        candidates=candidates,
        test_path=test_path,
        task=(
            "Fix calculator.py so calculate() returns 2 "
            "and make the provided test pass."
        ),
    )

    assert_true(
        isinstance(repair, dict),
        "Phase33 controller returned invalid result.",
    )

    assert_true(
        repair.get("success") is True,
        f"Real Phase33 repair failed: {repair}",
    )

    # ------------------------------------------------------------
    # 5. Verify actual file state
    # ------------------------------------------------------------
    final_source = target.read_text(
        encoding="utf-8",
    )

    assert_true(
        final_source != broken_source,
        "Controller reported success but target file did not change.",
    )

    py_compile.compile(
        str(target),
        doraise=True,
    )

    print("REAL FILE MODIFICATION: VERIFIED")
    print("REAL PYTHON VALIDATION: VERIFIED")

    # ------------------------------------------------------------
    # 6. Run the real test independently
    # ------------------------------------------------------------
    final_test = subprocess.run(
        [
            sys.executable,
            str(test_file),
        ],
        cwd=str(TEST_ROOT),
        text=True,
        capture_output=True,
    )

    assert_true(
        final_test.returncode == 0,
        (
            "Controller reported success but independent real test "
            f"failed.\nSTDOUT:\n{final_test.stdout}\n"
            f"STDERR:\n{final_test.stderr}"
        ),
    )

    assert_true(
        "REAL_PHASE33_TEST_PASS" in final_test.stdout,
        "Independent test did not produce its success marker.",
    )

    print("REAL INDEPENDENT TEST: VERIFIED")

    # ------------------------------------------------------------
    # 7. Verify controller metadata
    # ------------------------------------------------------------
    repair_text = json.dumps(
        repair,
        ensure_ascii=False,
    )

    assert_true(
        "commit" in repair_text.lower()
        or "healed" in repair_text.lower(),
        "Repair result contains no evidence of successful healing.",
    )

    # ------------------------------------------------------------
    # 8. Real rollback test
    # ------------------------------------------------------------
    rollback_target = TEST_ROOT / "rollback.py"
    rollback_test = TEST_ROOT / "test_rollback.py"

    rollback_original = """def value():
    return 10
"""

    rollback_test_source = """from rollback import value

if value() != 999:
    raise RuntimeError("ROLLBACK_TEST_FAILURE")
"""

    rollback_target.write_text(
        rollback_original,
        encoding="utf-8",
    )

    rollback_test.write_text(
        rollback_test_source,
        encoding="utf-8",
    )

    rollback_controller = Phase33Controller(
        TEST_ROOT,
        max_candidates=2,
    )

    rollback_result = rollback_controller.repair(
        diagnosis={
            "error_type": "test_failure",
            "error": "intentional rollback verification",
        },
        relative_path="rollback.py",
        old_text="return 10",
        candidates=[
            "return 20",
            "return 30",
        ],
        test_path="test_rollback.py",
        task=(
            "This is an intentional rollback test. "
            "The candidates must fail the provided test."
        ),
    )

    assert_true(
        rollback_result.get("success") is False,
        "Rollback test unexpectedly succeeded.",
    )

    restored = rollback_target.read_text(
        encoding="utf-8",
    )

    assert_true(
        restored == rollback_original,
        "Rollback failed: original source was not restored.",
    )

    print("REAL ROLLBACK: VERIFIED")

    # ------------------------------------------------------------
    # 9. Clean test workspace
    # ------------------------------------------------------------
    shutil.rmtree(TEST_ROOT)

    assert_true(
        not TEST_ROOT.exists(),
        "Temporary Phase33 test workspace was not cleaned.",
    )

    # ------------------------------------------------------------
    # 10. Final machine-checked result
    # ------------------------------------------------------------
    print()
    print("=" * 64)
    print("PHASE 33 REAL E2E: VERIFIED")
    print("=" * 64)
    print("No fake workspace executor.")
    print("No fake Phase33 controller.")
    print("No fake repair result.")
    print("Real candidate generation: VERIFIED")
    print("Real file modification: VERIFIED")
    print("Real syntax validation: VERIFIED")
    print("Real independent test: VERIFIED")
    print("Real transaction success path: VERIFIED")
    print("Real rollback path: VERIFIED")
    print("Temporary workspace cleanup: VERIFIED")
    print("=" * 64)


if __name__ == "__main__":
    asyncio.run(main())
