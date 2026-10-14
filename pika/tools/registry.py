from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Tool:
    name: str
    description: str
    capabilities: list[str]
    handler: Callable[..., Any]
    input_schema: dict[str, Any] = field(
        default_factory=dict
    )


class ToolRegistry:
    """
    Explicit registry for executable PIKA tools.

    Only registered tools can be executed.
    """

    def __init__(self):
        self.tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:

        if tool.name in self.tools:
            raise ValueError(
                f"Tool '{tool.name}' is already registered."
            )

        self.tools[tool.name] = tool

    def get(self, name: str) -> Tool:

        if name not in self.tools:
            raise ValueError(
                f"Tool '{name}' is not registered."
            )

        return self.tools[name]

    def select(
        self,
        capabilities: list[str],
    ) -> list[Tool]:

        requested = set(capabilities)

        scored = []

        for tool in self.tools.values():

            score = len(
                requested.intersection(
                    tool.capabilities
                )
            )

            if score:
                scored.append(
                    (score, tool)
                )

        scored.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return [
            tool
            for _, tool in scored
        ]

    def execute(
        self,
        name: str,
        **kwargs: Any,
    ) -> Any:

        tool = self.get(name)

        return tool.handler(
            **kwargs
        )

    def list(self) -> list[str]:
        return list(
            self.tools.keys()
        )

    def describe(self) -> dict[str, dict[str, Any]]:

        return {
            name: {
                "description": tool.description,
                "capabilities": tool.capabilities,
                "input_schema": tool.input_schema,
            }
            for name, tool in self.tools.items()
        }
