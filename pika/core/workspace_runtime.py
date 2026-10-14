from pathlib import Path
from typing import Any

from tools.registry import Tool, ToolRegistry
from tools.workspace import WorkspaceTools


class WorkspaceRuntime:

    def __init__(
        self,
        workspace_root: str | Path,
    ):
        self.workspace = WorkspaceTools(
            workspace_root
        )

        self.tools = ToolRegistry()

        self._register_tools()

    def _register_tools(self) -> None:

        self.tools.register(
            Tool(
                name="workspace_list",
                description=(
                    "List project files."
                ),
                capabilities=[
                    "workspace",
                    "inspection",
                ],
                handler=self.workspace.list_files,
            )
        )

        self.tools.register(
            Tool(
                name="workspace_read",
                description=(
                    "Read a project text file."
                ),
                capabilities=[
                    "workspace",
                    "inspection",
                    "code_analysis",
                ],
                handler=self.workspace.read_file,
            )
        )

        self.tools.register(
            Tool(
                name="workspace_search",
                description=(
                    "Search project source code."
                ),
                capabilities=[
                    "workspace",
                    "inspection",
                    "code_analysis",
                    "debugging",
                ],
                handler=self.workspace.search,
            )
        )

        self.tools.register(
            Tool(
                name="workspace_validate_python",
                description=(
                    "Validate Python syntax."
                ),
                capabilities=[
                    "workspace",
                    "validation",
                    "debugging",
                ],
                handler=self.workspace.validate_python,
            )
        )

        self.tools.register(
            Tool(
                name="workspace_run_python_test",
                description=(
                    "Run a project pytest test."
                ),
                capabilities=[
                    "workspace",
                    "validation",
                    "debugging",
                ],
                handler=self.workspace.run_python_test,
            )
        )

    def discover(
        self,
        capabilities: list[str],
    ) -> dict[str, Any]:

        selected = self.tools.select(
            capabilities
        )

        return {
            "capabilities": capabilities,
            "tools": [
                tool.name
                for tool in selected
            ],
        }

    def execute(
        self,
        tool_name: str,
        **kwargs: Any,
    ) -> Any:

        return self.tools.execute(
            tool_name,
            **kwargs,
        )
