import tempfile
from pathlib import Path

from core.brain import _phase35_save_repair
from core.learning_engine import LearningEngine
from core.semantic_code_memory import SemanticCodeMemory


def run():
    with tempfile.TemporaryDirectory(prefix="pika_brain_learning_") as tmp:
        root = Path(tmp)
        semantic = SemanticCodeMemory(root / "semantic.json")
        learner = LearningEngine(root / "learning.json")

        task = "repair test fixture calculation"
        code = "def calculate():\n    return 42\n"
        diagnosis = {
            "error_type": "AssertionError",
            "root_cause": "incorrect return value",
            "error_message": "expected 42",
        }
        context = {
            "target_path": "fixture.py",
            "old_text": "def calculate():\n    return 0\n",
            "test_path": "test_fixture.py",
        }

        failed = _phase35_save_repair(
            semantic, task, [code],
            {"success": True, "test_passed": False,
             "accepted_candidate": code, "repair": {"final_candidate": code}},
            diagnosis, context, learner,
        )
        assert failed is False
        assert semantic.stats()["total_variants"] == 0
        assert len(learner.data.get("experiences", [])) == 0

        repair_details = {
            "success": True,
            "stage": "healed",
            "final_candidate": code,
            "test_passed": True,
            "validation_passed": True,
            "commit_passed": True,
            "test": {"success": True},
            "validation": {"success": True},
            "commit": {"success": True},
            "attempts": [{
                "success": True,
                "stage": "committed",
                "candidate": code,
                "test": {"success": True},
                "validation": {"success": True},
                "commit": {"success": True},
            }],
        }
        passed = _phase35_save_repair(
            semantic, task, [code],
            {"success": True, "test_passed": True,
             "accepted_candidate": code, "repair": repair_details},
            diagnosis, context, learner,
        )
        assert passed is True
        assert semantic.stats()["test_verified"] == 1

        records = learner.retrieve(task=task, error_type="AssertionError",
                                   root_cause="incorrect return value")
        assert records["known"] is True
        assert any(
            s.get("solution") == code
            for match in records["matches"]
            for s in match.get("solutions", [])
        ), "LearningEngine did not retrieve the saved solution"

        print("PASS: missing test evidence rejected")
        print("PASS: no unverified record persisted")
        print("PASS: evidence-backed repair saved to semantic memory")
        print("PASS: learning experience persisted and is retrievable")
        print("PASS: temporary databases only")
        print("RESULT: 5 checks passed")


if __name__ == "__main__":
    run()
