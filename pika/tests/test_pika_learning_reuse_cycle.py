import tempfile
from pathlib import Path

from core.brain import _phase35_save_repair
from core.learning_engine import LearningEngine
from core.semantic_code_memory import SemanticCodeMemory


def run():
    with tempfile.TemporaryDirectory(prefix="pika_reuse_cycle_") as tmp:
        root = Path(tmp)
        sem_path = root / "semantic.json"
        learn_path = root / "learning.json"

        task = "repair calculator to return forty two"
        code = "def calculate():\n    return 42\n"
        context = {
            "target_path": "fixture.py",
            "old_text": "def calculate():\n    return 0\n",
            "test_path": "test_fixture.py",
        }
        diagnosis = {
            "error_type": "AssertionError",
            "root_cause": "wrong return value",
            "error_message": "expected 42",
        }
        outcome = {
            "success": True,
            "test_passed": True,
            "accepted_candidate": code,
            "repair": {"final_candidate": code},
        }

        # First task: save evidence-backed repair.
        semantic = SemanticCodeMemory(sem_path)
        learner = LearningEngine(learn_path)
        saved = _phase35_save_repair(
            semantic, task, [code], outcome, diagnosis,
            replay_context=context, learning_engine=learner,
        )
        assert saved is True

        # Simulate a later run by reopening both persistent stores.
        semantic2 = SemanticCodeMemory(sem_path)
        learner2 = LearningEngine(learn_path)

        hits = semantic2.retrieve(task, language="python", verified_only=True)
        match = next((v for v in hits if v["code"] == code), None)
        assert match is not None, "Saved verified code not retrieved after reload"
        assert match["verification"] == "test_verified"
        assert match["replay_context"] == context

        # Only reuse when all replay-context fields match exactly.
        required = ("target_path", "old_text", "test_path")
        compatible = all(match["replay_context"].get(k) == context[k] for k in required)
        incompatible_context = dict(context, test_path="different_test.py")
        incompatible = all(
            match["replay_context"].get(k) == incompatible_context[k]
            for k in required
        )
        assert compatible is True
        assert incompatible is False

        experience = learner2.best_solution(task=task, error_type="AssertionError",
                                             root_cause="wrong return value")
        assert experience is not None, "LearningEngine did not return saved experience"
        assert experience.get("solution") == code

        # Unverified variants must never be returned by default.
        semantic2.remember(
            intent="unverified dangerous alternative",
            code="def calculate():\n    return -1\n",
            verification="unverified",
            evidence=[],
        )
        safe_hits = semantic2.retrieve("unverified dangerous alternative", verified_only=True)
        assert all("return -1" not in item["code"] for item in safe_hits)

        print("PASS: repair saved with explicit test evidence")
        print("PASS: semantic memory survived reload")
        print("PASS: verified code and replay context retrieved")
        print("PASS: matching context accepted; changed test context rejected")
        print("PASS: LearningEngine experience survived reload and retrieval")
        print("PASS: unverified code excluded from default retrieval")
        print("RESULT: 6 checks passed; temporary files only")


if __name__ == "__main__":
    run()
