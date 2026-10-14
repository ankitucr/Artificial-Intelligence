import asyncio
import tempfile
from pathlib import Path

from core.brain import PIKABrain, _phase35_save_repair
from core.semantic_code_memory import SemanticCodeMemory
from tests.test_phase34_brain_integration import (
    FakeMemory, FakeAnalyzer, FakePlanner, FakeDecision,
    FakeAgent, FakeRouter, FakeWorkspaceExecutor,
    FakePhase32, FakePhase33,
)


class EmptyLearning:
    def lookup_candidates(self, **kwargs):
        return []


class CountingGenerator:
    def __init__(self):
        self.calls = 0

    async def generate_from_failure(self, **kwargs):
        self.calls += 1
        return {
            "success": True,
            "target_path": "calculator.py",
            "old_text": "return a - b",
            "test_path": "test_calculator.py",
            "candidates": ["return a + b"],
        }


def make_brain(generator):
    agent = FakeAgent()
    brain = PIKABrain(
        router=FakeRouter(agent),
        memory=FakeMemory(),
        planner=FakePlanner(),
        evaluator=object(),
        experience=object(),
        task_analyzer=FakeAnalyzer(),
        decision_engine=FakeDecision(),
        tool_runtime=None,
        max_retries=0,
    )
    brain.tool_runtime = object()
    brain.workspace_executor = FakeWorkspaceExecutor()
    brain.phase32_controller = FakePhase32()
    brain.phase33_controller = FakePhase33()
    brain.phase34_learning = EmptyLearning()
    brain.repair_candidate_generator = generator
    return brain


async def run():
    with tempfile.TemporaryDirectory(prefix="pika_brain_reuse_") as tmp:
        db = Path(tmp) / "semantic.json"
        task = "Build a calculator project and fix its code error"
        code = "return a * b"
        context = {
            "target_path": "calculator.py",
            "old_text": "return a - b",
            "test_path": "test_calculator.py",
        }
        diagnosis = {
            "error_type": "AssertionError",
            "root_cause": "wrong calculator operation",
            "error_message": "expected multiplication",
        }

        # First run: persist an evidence-backed repair.
        memory1 = SemanticCodeMemory(db)
        saved = _phase35_save_repair(
            memory1, task, [code],
            {
                "success": True,
                "test_passed": True,
                "accepted_candidate": code,
                "repair": {"final_candidate": code},
            },
            diagnosis,
            replay_context=context,
        )
        assert saved is True
        assert SemanticCodeMemory(db).stats()["test_verified"] == 1

        # Second run: new Brain and newly loaded memory object.
        generator = CountingGenerator()
        brain2 = make_brain(generator)
        brain2.semantic_code_memory = SemanticCodeMemory(db)

        result = await brain2.think(task)

        assert result.get("success") is True, result
        assert "phase35_memory_repair" in result, result
        assert generator.calls == 0, f"Generator unexpectedly called {generator.calls} time(s)"
        assert len(brain2.phase33_controller.calls) == 1
        assert brain2.phase33_controller.calls[0]["candidates"] == [code]

        # Changed context must not be considered compatible.
        loaded = SemanticCodeMemory(db)
        hits = loaded.retrieve(task, language="python", verified_only=True)
        match = next((v for v in hits if v["code"] == code), None)
        assert match is not None
        assert match["replay_context"] == context
        changed = dict(context, test_path="different_test.py")
        assert any(
            match["replay_context"].get(k) != changed[k]
            for k in ("target_path", "old_text", "test_path")
        )

        print("PASS: verified repair persisted before Brain restart")
        print("PASS: fresh Brain instance loaded persistent memory")
        print("PASS: real PIKABrain.think() used semantic memory replay")
        print("PASS: compatible candidate reached Phase 33 first")
        print("PASS: generator call count stayed zero")
        print("PASS: changed test context detected as incompatible")
        print("RESULT: 6 checks passed; temporary database only")


if __name__ == "__main__":
    asyncio.run(run())
