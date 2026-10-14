from typing import Any

from .registry import Tool, ToolRegistry
from .workspace import (
    workspace_list,
    workspace_read,
    workspace_write,
    workspace_replace,
    workspace_delete,
    workspace_run,
    workspace_run_python,
    workspace_check_python,
)


def calculate_sum(
    a: float,
    b: float,
) -> float:
    return a + b


def calculate_product(
    a: float,
    b: float,
) -> float:
    return a * b


def text_length(
    text: str,
) -> int:
    return len(text)


def register_builtin_tools(
    registry: ToolRegistry,
) -> None:

    # ---------------------------------------------------------
    # EXISTING TOOLS
    # ---------------------------------------------------------

    registry.register(
        Tool(
            name="calculator_sum",
            description="Add two numbers.",
            capabilities=[
                "calculation",
                "reasoning",
            ],
            handler=calculate_sum,
            input_schema={
                "a": "number",
                "b": "number",
            },
        )
    )

    registry.register(
        Tool(
            name="calculator_product",
            description="Multiply two numbers.",
            capabilities=[
                "calculation",
                "reasoning",
            ],
            handler=calculate_product,
            input_schema={
                "a": "number",
                "b": "number",
            },
        )
    )

    registry.register(
        Tool(
            name="text_length",
            description="Return the length of text.",
            capabilities=[
                "text",
                "analysis",
            ],
            handler=text_length,
            input_schema={
                "text": "string",
            },
        )
    )

    # ---------------------------------------------------------
    # PHASE 31 — WORKSPACE TOOLS
    # ---------------------------------------------------------

    registry.register(
        Tool(
            name="workspace_list",
            description="List files and directories inside the controlled PIKA workspace.",
            capabilities=[
                "workspace",
                "filesystem",
                "engineering",
                "coding",
            ],
            handler=workspace_list,
            input_schema={
                "path": "string",
            },
        )
    )

    registry.register(
        Tool(
            name="workspace_read",
            description="Read a UTF-8 text file from the controlled PIKA workspace.",
            capabilities=[
                "workspace",
                "filesystem",
                "engineering",
                "coding",
            ],
            handler=workspace_read,
            input_schema={
                "path": "string",
            },
        )
    )

    registry.register(
        Tool(
            name="workspace_write",
            description="Create or overwrite a text file inside the controlled PIKA workspace.",
            capabilities=[
                "workspace",
                "filesystem",
                "engineering",
                "coding",
            ],
            handler=workspace_write,
            input_schema={
                "path": "string",
                "content": "string",
            },
        )
    )

    registry.register(
        Tool(
            name="workspace_replace",
            description="Replace text inside an existing workspace file.",
            capabilities=[
                "workspace",
                "filesystem",
                "engineering",
                "coding",
            ],
            handler=workspace_replace,
            input_schema={
                "path": "string",
                "old": "string",
                "new": "string",
                "replace_all": "boolean",
            },
        )
    )

    registry.register(
        Tool(
            name="workspace_delete",
            description="Delete a file from the controlled PIKA workspace.",
            capabilities=[
                "workspace",
                "filesystem",
                "engineering",
                "coding",
            ],
            handler=workspace_delete,
            input_schema={
                "path": "string",
            },
        )
    )

    registry.register(
        Tool(
            name="workspace_run",
            description="Run an allowlisted command inside the controlled PIKA workspace.",
            capabilities=[
                "workspace",
                "execution",
                "engineering",
                "testing",
            ],
            handler=workspace_run,
            input_schema={
                "command": "list[string]",
            },
        )
    )

    registry.register(
        Tool(
            name="workspace_run_python",
            description="Run a Python file inside the controlled PIKA workspace.",
            capabilities=[
                "workspace",
                "execution",
                "python",
                "engineering",
                "testing",
            ],
            handler=workspace_run_python,
            input_schema={
                "path": "string",
                "args": "list[string]",
            },
        )
    )

    registry.register(
        Tool(
            name="workspace_check_python",
            description="Compile-check a Python file inside the controlled PIKA workspace.",
            capabilities=[
                "workspace",
                "execution",
                "python",
                "engineering",
                "testing",
            ],
            handler=workspace_check_python,
            input_schema={
                "path": "string",
            },
        )
    )
