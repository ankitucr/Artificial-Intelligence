from typing import Any

from .base import Agent
from models.base import ModelProvider


class APIAgent(Agent):

    name = "api"

    capabilities = [
        "coding",
        "reasoning",
        "generation",
        "analysis",
    ]

    def __init__(self, provider: ModelProvider):
        self.provider = provider

    async def execute(
        self,
        task: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        memory = context.get("memory", {}) if context else {}
        plan = context.get("plan", []) if context else {}

        system = """
You are an external worker inside PIKA.

PIKA Brain decides what needs to be done.
You execute the assigned task.

Rules:
- Do not claim that code was tested unless it was actually tested.
- Be precise.
- Prefer working solutions over explanations.
- Return useful structured output.
"""

        prompt = f"""
TASK:
{task}

PLAN:
{plan}

RELEVANT MEMORY:
{memory}

Execute the task.
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
            "error": result.get("error"),
            "raw": result,
        }
