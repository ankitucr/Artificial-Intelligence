from abc import ABC, abstractmethod
from typing import Any


class ModelProvider(ABC):
    """
    PIKA's model abstraction.

    Brain never talks directly to a model/provider.
    """

    name: str = "unknown"

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        context: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        pass

    async def health(self) -> bool:
        return True
