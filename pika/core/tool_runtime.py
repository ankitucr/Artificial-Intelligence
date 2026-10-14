import re
from typing import Any

from skills.registry import SkillRegistry
from tools.registry import ToolRegistry


class ToolRuntime:

    def __init__(
        self,
        skills: SkillRegistry,
        tools: ToolRegistry,
    ):
        self.skills = skills
        self.tools = tools

    def discover(
        self,
        capabilities: list[str],
    ) -> dict[str, Any]:

        skills = self.skills.find_for_capabilities(
            capabilities
        )

        tools = self.tools.select(
            capabilities
        )

        return {
            "capabilities": capabilities,
            "skills": [
                skill.name
                for skill in skills
            ],
            "tools": [
                tool.name
                for tool in tools
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

    def execute_for_task(
        self,
        task: str,
        capabilities: list[str],
    ) -> dict[str, Any]:

        discovered = self.discover(
            capabilities
        )

        tools = discovered["tools"]

        if not tools:
            return {
                "success": False,
                "tool_used": None,
                "output": "",
                "error": (
                    "No registered tool matches "
                    "the requested capabilities."
                ),
                "discovery": discovered,
            }

        task_lower = task.lower()

        # ---------------------------------------------------------
        # CALCULATION
        # ---------------------------------------------------------

        if "calculation" in capabilities:

            numbers = self._numbers(task)

            if len(numbers) >= 2:

                a = numbers[0]
                b = numbers[1]

                # Explicit operation detection.
                if (
                    "multiply" in task_lower
                    or "product" in task_lower
                    or "*" in task_lower
                ):
                    tool_name = "calculator_product"

                elif (
                    "add" in task_lower
                    or "sum" in task_lower
                    or "plus" in task_lower
                    or "+" in task_lower
                ):
                    tool_name = "calculator_sum"

                else:
                    # Do NOT guess.
                    #
                    # Subtraction/division and other operations
                    # are not implemented by the current registry.
                    return {
                        "success": False,
                        "tool_used": None,
                        "output": "",
                        "error": (
                            "The calculation operation is not "
                            "supported by the registered tools."
                        ),
                        "discovery": discovered,
                    }

                if tool_name not in tools:
                    return {
                        "success": False,
                        "tool_used": None,
                        "output": "",
                        "error": (
                            f"Required tool '{tool_name}' "
                            "was not discovered."
                        ),
                        "discovery": discovered,
                    }

                value = self.execute(
                    tool_name,
                    a=a,
                    b=b,
                )

                return {
                    "success": True,
                    "tool_used": tool_name,
                    "output": str(value),
                    "value": value,
                    "discovery": discovered,
                }

        # ---------------------------------------------------------
        # TEXT LENGTH
        # ---------------------------------------------------------

        if "text" in capabilities:

            match = re.search(
                r"text\s*[:=]\s*[\"'](.*?)[\"']",
                task,
                flags=re.IGNORECASE,
            )

            if match:

                text = match.group(1)

                tool_name = "text_length"

                if tool_name in tools:

                    value = self.execute(
                        tool_name,
                        text=text,
                    )

                    return {
                        "success": True,
                        "tool_used": tool_name,
                        "output": str(value),
                        "value": value,
                        "discovery": discovered,
                    }

        return {
            "success": False,
            "tool_used": None,
            "output": "",
            "error": (
                "A matching tool was discovered, "
                "but the task input could not be "
                "mapped to a supported operation."
            ),
            "discovery": discovered,
        }

    @staticmethod
    def _numbers(
        task: str,
    ) -> list[int | float]:

        values = re.findall(
            r"(?<![A-Za-z_])-?\d+(?:\.\d+)?",
            task,
        )

        numbers: list[int | float] = []

        for value in values:
            if "." in value:
                numbers.append(float(value))
            else:
                numbers.append(int(value))

        return numbers
