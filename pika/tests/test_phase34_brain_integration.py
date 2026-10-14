import asyncio

from core.brain import PIKABrain


class FakeMemory:
    def __init__(self):
        self.failures = []

    def retrieve(self, task):
        return {}

    def remember_failure(self, record):
        self.failures.append(record)


class FakeAnalyzer:
    def analyze(self, task):
        return {
            "task_type": "engineering",
            "capabilities": ["coding"],
            "tool_capabilities": [],
        }


class FakePlanner:
    def plan(self, task, memories=None):
        return {
            "goal": task,
            "task_type": "engineering",
            "complexity": "low",
            "subtask_count": 1,
            "subtasks": [],
            "dependencies": [],
            "execution_order": [],
            "validation": {},
            "strategy": {},
            "memory_hints": [],
        }


class FakeDecision:
    def decide(self, **kwargs):
        return {
            "mode": "agent",
            "confidence": 1.0,
            "task_signature": "phase34-brain-integration",
            "history": {},
        }


class FakeAgent:
    name = "isolated-test-worker"

    def __init__(self):
        self.calls = 0

    async def execute(self, task, context=None):
        self.calls += 1
        return {
            "success": True,
            "output": '{"files": [], "commands": []}',
            "agent": self.name,
            "provider": "test",
            "model": "stub",
        }


class FakeRouter:
    def __init__(self, agent):
        self.agent = agent

    def select(self, required_capabilities=None):
        return self.agent


class FakeWorkspaceExecutor:
    def inspect(self):
        return {"success": True, "files": []}

    def build_context(self, **kwargs):
        return {"workspace_execution": True}


class FakePhase32:
    def execute(self, worker_output, attempt=1, worker_result=None):
        return {
            "success": False,
            "stage": "execution",
            "error": "intentional isolated test failure",
            "diagnosis": {
                "error_type": "code_error",
                "root_cause": "known test problem",
                "error_message": "intentional isolated test failure",
            },
            "recovery": {"action": "stop"},
            "recovery_feedback": "isolated test failure",
            "transaction": {"rollback": {"success": True}},
        }


class FakeLearning:
    def __init__(self):
        self.lookups = 0

    def lookup_candidates(self, **kwargs):
        self.lookups += 1
        return [{
            "solution": "return a + b",
            "replay_context": {
                "target_path": "calculator.py",
                "old_text": "return a - b",
                "test_path": "test_calculator.py",
            },
        }]


class FakePhase33:
    def __init__(self):
        self.calls = []

    def repair(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "success": True,
            "stage": "healed",
            "repair": {
                "verified": True,
                "test_passed": True,
            },
        }


class GeneratorMustNotRun:
    async def generate_from_failure(self, **kwargs):
        raise AssertionError(
            "Cohere fallback ran despite a verified memory candidate"
        )


async def run_test():
    agent = FakeAgent()
    memory = FakeMemory()

    brain = PIKABrain(
        router=FakeRouter(agent),
        memory=memory,
        planner=FakePlanner(),
        evaluator=object(),
        experience=object(),
        task_analyzer=FakeAnalyzer(),
        decision_engine=FakeDecision(),
        tool_runtime=None,
        max_retries=0,
    )

    # Inject isolated fakes into the REAL PIKABrain.think() flow.
    # No production workspace, learning DB, or API is accessed.
    brain.tool_runtime = object()
    brain.workspace_executor = FakeWorkspaceExecutor()
    brain.phase32_controller = FakePhase32()
    brain.phase34_learning = FakeLearning()
    brain.phase33_controller = FakePhase33()
    brain.repair_candidate_generator = GeneratorMustNotRun()

    result = await brain.think(
        "Build a small calculator project and fix its code error"
    )

    assert result.get("success") is True, result
    assert "phase34_repair" in result, result
    assert result["phase34_repair"].get("success") is True
    assert brain.phase34_learning.lookups == 1
    assert len(brain.phase33_controller.calls) == 1
    assert brain.phase33_controller.calls[0]["candidates"] == [
        "return a + b"
    ]
    assert brain.phase33_controller.calls[0]["relative_path"] == (
        "calculator.py"
    )
    assert agent.calls == 1
    assert len(memory.failures) == 1

    print("\nPHASE 34 BRAIN INTEGRATION: PASS")
    print("Verified: actual PIKABrain.think() used the memory-first path.")
    print("Verified: compatible learned candidate reached Phase 33.")
    print("Verified: successful repair returned from Brain.")
    print("Verified: Cohere candidate generator was not called.")
    print("Verified: production workspace and learning DB were untouched.")


if __name__ == "__main__":
    asyncio.run(run_test())
