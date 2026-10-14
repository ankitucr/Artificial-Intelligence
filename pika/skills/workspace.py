from .registry import Skill


def workspace_skill() -> Skill:
    return Skill(
        name="workspace_engineering",
        description=(
            "Inspect and validate a software project "
            "through controlled workspace operations."
        ),
        capabilities=[
            "workspace",
            "inspection",
            "code_analysis",
            "validation",
            "debugging",
        ],
        tool_names=[
            "workspace_list",
            "workspace_read",
            "workspace_search",
            "workspace_validate_python",
            "workspace_run_pytest",
        ],
    )
