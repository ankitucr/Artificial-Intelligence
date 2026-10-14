import asyncio
from core.brain import PIKABrain


class FakeExperience:
    def create_experience(self, task, result, evaluation, decision):
        return {"lesson": "isolated phase34 fallback test"}

class FakeMemory:
    def __init__(self):
        self.failures = []
        self.lessons = []

    def retrieve(self, task):
        return {}

    def remember_failure(self, record):
        self.failures.append(record)
    def remember_lesson(self, lesson):
        self.lessons.append(lesson)


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
            "task_signature": "phase34-fallback-test",
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
    def __init__(self, candidates):
        self.candidates = candidates
        self.lookups = 0

    def lookup_candidates(self, **kwargs):
        self.lookups += 1
        return self.candidates


class FakePhase33:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def repair(self, **kwargs):
        self.calls.append(kwargs)
        return self.outcomes.pop(0)


class FakeGenerator:
    def __init__(self):
        self.calls = 0

    async def generate_from_failure(self, **kwargs):
        self.calls += 1
        return {
            "success": True,
            "target_path": "calculator.py",
            "old_text": "return a - b",
            "test_path": "test_calculator.py",
            "candidates": ["return a + b", "return sum([a, b])"],
            "count": 2,
        }


def make_brain(candidates, repair_outcomes):
    agent = FakeAgent()
    memory = FakeMemory()
    learning = FakeLearning(candidates)
    phase33 = FakePhase33(repair_outcomes)
    generator = FakeGenerator()

    brain = PIKABrain(
        router=FakeRouter(agent),
        memory=memory,
        planner=FakePlanner(),
        evaluator=object(),
        experience=FakeExperience(),
        task_analyzer=FakeAnalyzer(),
        decision_engine=FakeDecision(),
        tool_runtime=None,
        max_retries=0,
    )

    brain.tool_runtime = object()
    brain.workspace_executor = FakeWorkspaceExecutor()
    brain.phase32_controller = FakePhase32()
    brain.phase34_learning = learning
    brain.phase33_controller = phase33
    brain.repair_candidate_generator = generator

    return brain, agent, memory, learning, phase33, generator


def make_candidate():
    return {
        "solution": "return a + b",
        "replay_context": {
            "target_path": "calculator.py",
            "old_text": "return a - b",
            "test_path": "test_calculator.py",
        },
    }


async def test_memory_miss():
    brain, agent, memory, learning, phase33, generator = make_brain(
        candidates=[],
        repair_outcomes=[
            {"success": True, "stage": "healed",
             "repair": {"verified": True, "test_passed": True}}
        ],
    )

    result = await brain.think(
        "Build a small calculator project and fix its code error"
    )

    assert learning.lookups == 1, "Memory lookup was not performed"
    assert generator.calls == 1, "Fallback generator did not run on memory miss"
    assert len(phase33.calls) == 1, "Generated candidates did not reach Phase 33"
    assert phase33.calls[0]["candidates"] == [
        "return a + b", "return sum([a, b])"
    ]
    assert result.get("success") is True, result
    assert agent.calls == 1
    print("PASS: memory miss -> candidate generation -> successful repair")


async def test_learned_repair_failure_falls_back():
    brain, agent, memory, learning, phase33, generator = make_brain(
        candidates=[make_candidate()],
        repair_outcomes=[
            {"success": False, "stage": "repair_failed"},
            {"success": True, "stage": "healed",
             "repair": {"verified": True, "test_passed": True}},
        ],
    )

    result = await brain.think(
        "Build a small calculator project and fix its code error"
    )

    assert learning.lookups == 1
    assert len(phase33.calls) == 2, (
        f"Expected learned attempt and fallback attempt; got {len(phase33.calls)}"
    )
    assert phase33.calls[0]["candidates"] == ["return a + b"]
    assert generator.calls == 1, "Fallback generator did not run after repair failure"
    assert phase33.calls[1]["candidates"] == [
        "return a + b", "return sum([a, b])"
    ]
    assert result.get("success") is True, result
    assert agent.calls == 1
    print("PASS: learned repair failure -> fallback generation -> successful repair")


async def main():
    await test_memory_miss()
    await test_learned_repair_failure_falls_back()
    print("\nPHASE 34 BRAIN FALLBACK TESTS: PASS")


if __name__ == "__main__":
    asyncio.run(main())
