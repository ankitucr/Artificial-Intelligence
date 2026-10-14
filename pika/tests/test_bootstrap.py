import asyncio

from core.brain import PIKABrain
from core.planner import Planner
from core.router import AgentRouter
from memory.manager import MemoryManager
from evaluation.evaluator import Evaluator
from learning.experience import ExperienceEngine


class FakeAgent:
    name = "test-worker"
    capabilities = ["coding", "reasoning", "generation"]

    async def execute(self, task, context=None):
        return {
            "success": True,
            "agent": self.name,
            "provider": "test",
            "model": "fake-agent",
            "output": "Test task completed successfully.",
            "error": None,
            "raw": {},
        }


def test_brain_bootstrap():
    async def run():
        router = AgentRouter()
        router.register(FakeAgent())

        brain = PIKABrain(
            router=router,
            memory=MemoryManager(),
            planner=Planner(),
            evaluator=Evaluator(),
            experience=ExperienceEngine(),
        )

        episodes_before = len(brain.memory.episodes)
        result = await brain.think("test task")

        assert isinstance(result, dict), (
            f"Expected dict result, got {type(result).__name__}"
        )
        assert "evaluation" in result, (
            f"Missing evaluation field. Keys: {list(result.keys())}"
        )
        assert len(brain.memory.episodes) > episodes_before, (
            f"Expected a new memory episode; before={episodes_before}, "
            f"after={len(brain.memory.episodes)}"
        )

    asyncio.run(run())


if __name__ == "__main__":
    test_brain_bootstrap()
    print("BRAIN BOOTSTRAP TEST: PASS")
