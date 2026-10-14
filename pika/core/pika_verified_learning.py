"""Evidence-gated learning bridge. Self-test uses temporary databases only."""
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone

from core.learning_engine import LearningEngine
from core.semantic_code_memory import SemanticCodeMemory


def record_verified_experiment(
    *,
    learning_engine,
    semantic_memory,
    task,
    code,
    language="python",
    test_passed=False,
    test_evidence="",
    method="controlled-experiment",
    replay_context=None,
    source="pika_experiment",
):
    # Fail closed: no evidence means no promotion to verified.
    if test_passed is not True or not str(test_evidence).strip():
        return {
            "saved": False,
            "reason": "Independent test pass and evidence are required.",
        }

    if not str(task).strip() or not str(code).strip():
        return {"saved": False, "reason": "Task and code are required."}

    timestamp = datetime.now(timezone.utc).isoformat()
    evidence = str(test_evidence).strip()

    semantic = semantic_memory.remember(
        intent=task,
        code=code,
        language=language,
        description="Saved after an explicitly passing experiment test.",
        tags=["pika-learning", "test-verified"],
        verification="test_verified",
        evidence=[evidence, "independent_test_passed=True"],
        replay_context=replay_context or {},
    )

    # LearningEngine accepts only a successful verification record.
    learned = learning_engine.learn(
        task=task,
        method=method,
        solution=code,
        verification={
            "independent_test": True,
            "test_passed": True,
            "evidence": evidence,
            "timestamp": timestamp,
        },
        success=True,
        source=source,
        metadata={"evidence": evidence, "semantic_variant_id": semantic["id"]},
        replay_context=replay_context or {},
    )

    return {
        "saved": True,
        "semantic_variant_id": semantic["id"],
        "semantic_verification": semantic["verification"],
        "learning_trusted": learned["trusted"],
        "timestamp": timestamp,
    }


def self_test():
    with tempfile.TemporaryDirectory(prefix="pika_learn_test_") as tmp:
        root = Path(tmp)
        semantic = SemanticCodeMemory(root / "semantic.json")
        learner = LearningEngine(root / "learning.json")

        # Negative case: an untested candidate must not be saved.
        rejected = record_verified_experiment(
            learning_engine=learner,
            semantic_memory=semantic,
            task="test-only example",
            code="def example():\n    return 7\n",
            test_passed=False,
            test_evidence="",
        )
        assert rejected["saved"] is False
        assert semantic.stats()["total_variants"] == 0

        # Positive case uses a real independent assertion.
        namespace = {}
        code = "def example():\n    return 7\n"
        exec(compile(code, "<isolated-self-test>", "exec"), namespace)
        assert namespace["example"]() == 7

        saved = record_verified_experiment(
            learning_engine=learner,
            semantic_memory=semantic,
            task="return the integer seven",
            code=code,
            test_passed=True,
            test_evidence="Independent assertion passed: example() == 7",
        )
        assert saved["saved"] is True
        assert saved["semantic_verification"] == "test_verified"
        assert saved["learning_trusted"] is True
        assert semantic.stats()["test_verified"] == 1

        retrieved = semantic.retrieve("return integer seven", verified_only=True)
        assert any(x["id"] == saved["semantic_variant_id"] for x in retrieved)

        print("PASS: untested candidate rejected")
        print("PASS: independent test evidence required")
        print("PASS: semantic memory saved test_verified variant")
        print("PASS: LearningEngine marked evidence-backed record trusted")
        print("PASS: verified semantic retrieval succeeded")
        print("PASS: temporary databases only; production memory unchanged")
        print("RESULT: 6 checks passed")


if __name__ == "__main__":
    self_test()
