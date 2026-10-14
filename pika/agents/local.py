from typing import Any

from .base import Agent
from models.base import ModelProvider


class LocalAgent(Agent):

    name = "local"

    capabilities = [
        "coding",
        "reasoning",
        "generation",
        "analysis",
    ]

    def __init__(
        self,
        provider: ModelProvider,
    ):
        self.provider = provider

    async def execute(
        self,
        task: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        memory = context.get("memory", {}) if context else {}
        plan = context.get("plan", []) if context else []

        system = """
You are a worker inside PIKA.

Your job is to execute the task given by PIKA.
Do not pretend that code was tested if it was not tested.
Return precise, structured results.
"""

        prompt = f"""
TASK:
{task}

PLAN:
{plan}

RELEVANT MEMORY:
{memory}

Perform the task.
"""

        result = await self.provider.generate(
            prompt=prompt,
            system=system,
        )

        return {
            "success": result.get("success", False),
            "agent": self.name,
            "provider": result.get("provider"),
            "model": result.get("model"),
            "output": result.get("text", ""),
            "raw": result,
        }
