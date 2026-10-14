from models.base import ModelProvider


class ModelRegistry:

    def __init__(self):
        self.providers: dict[str, ModelProvider] = {}

    def register(
        self,
        provider: ModelProvider,
    ) -> None:

        self.providers[provider.name] = provider

    def get(
        self,
        name: str,
    ) -> ModelProvider:

        if name not in self.providers:
            raise ValueError(
                f"Model provider '{name}' is not registered."
            )

        return self.providers[name]

    def list(self) -> list[str]:
        return list(self.providers.keys())
