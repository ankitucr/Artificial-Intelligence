from typing import Any

from .planner import Planner
from .router import AgentRouter
from memory.manager import MemoryManager
from evaluation.evaluator import Evaluator
from learning.experience import ExperienceEngine


class PIKABrain:

    def __init__(
        self,
        router: AgentRouter,
        memory: MemoryManager,
        planner: Planner,
        evaluator: Evaluator,
        experience: ExperienceEngine,
    ):
        self.router = router
        self.memory = memory
        self.planner = planner
        self.evaluator = evaluator
        self.experience = experience

    async def think(self, task: str) -> dict[str, Any]:

        memories = self.memory.retrieve(task)

        plan = self.planner.plan(task)

        agent = self.router.select()

        result = await agent.execute(
            task,
            context={
                "plan": plan,
                "memory": memories,
            },
        )

        evaluation = self.evaluator.evaluate(result)

        episode = self.experience.create_experience(
            task,
            result,
            evaluation,
        )

        self.memory.remember_episode(episode)

        return {
            "task": task,
            "plan": plan,
            "agent": agent.name,
            "result": result,
            "evaluation": evaluation,
        }
