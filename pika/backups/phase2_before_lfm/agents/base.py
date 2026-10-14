from abc import ABC, abstractmethod
from typing import Any


class Agent(ABC):
    """
    Stable interface between PIKA Brain and any worker.

    The Brain must never depend on a specific model/provider.
    """

    name: str = "unknown"
    capabilities: list[str] = []

    @abstractmethod
    async def execute(
        self,
        task: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        pass

    async def explain(self, result: dict[str, Any]) -> str:
        return str(result)

    async def propose_alternatives(
        self,
        task: str,
        result: dict[str, Any],
    ) -> list[str]:
        return []
