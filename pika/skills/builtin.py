from .registry import Skill, SkillRegistry
from .workspace import workspace_skill


def register_builtin_skills(
    registry: SkillRegistry,
) -> None:

    registry.register(
        Skill(
            name="calculation",
            description=(
                "Perform deterministic numerical calculations."
            ),
            capabilities=[
                "calculation",
                "reasoning",
            ],
            tool_names=[
                "calculator_sum",
                "calculator_product",
            ],
        )
    )

    registry.register(
        Skill(
            name="text_analysis",
            description=(
                "Perform basic deterministic text analysis."
            ),
            capabilities=[
                "text",
                "analysis",
            ],
            tool_names=[
                "text_length",
            ],
        )
    )

    registry.register(
        workspace_skill()
    )
