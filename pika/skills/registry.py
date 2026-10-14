from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Skill:
    name: str
    description: str
    capabilities: list[str] = field(default_factory=list)
    tool_names: list[str] = field(default_factory=list)


class SkillRegistry:
    """
    Registry of reusable PIKA skills.

    Skills describe WHAT PIKA can do.
    Tools provide the concrete operations.
    """

    def __init__(self):
        self.skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        if skill.name in self.skills:
            raise ValueError(
                f"Skill '{skill.name}' is already registered."
            )

        self.skills[skill.name] = skill

    def get(self, name: str) -> Skill:
        if name not in self.skills:
            raise ValueError(
                f"Skill '{name}' is not registered."
            )

        return self.skills[name]

    def find_by_capability(
        self,
        capability: str,
    ) -> list[Skill]:

        return [
            skill
            for skill in self.skills.values()
            if capability in skill.capabilities
        ]

    def find_for_capabilities(
        self,
        capabilities: list[str],
    ) -> list[Skill]:

        requested = set(capabilities)

        scored = []

        for skill in self.skills.values():

            score = len(
                requested.intersection(
                    skill.capabilities
                )
            )

            if score:
                scored.append(
                    (score, skill)
                )

        scored.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return [
            skill
            for _, skill in scored
        ]

    def list(self) -> list[str]:
        return list(self.skills.keys())

    def describe(self) -> dict[str, dict[str, Any]]:

        return {
            name: {
                "description": skill.description,
                "capabilities": skill.capabilities,
                "tools": skill.tool_names,
            }
            for name, skill in self.skills.items()
        }
