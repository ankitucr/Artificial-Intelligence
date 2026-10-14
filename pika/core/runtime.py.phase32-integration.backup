from core.router import AgentRouter
from core.tool_runtime import ToolRuntime

from agents.api_load_balancer import APILoadBalancerAgent

from skills.registry import SkillRegistry
from skills.builtin import register_builtin_skills

from tools.registry import ToolRegistry
from tools.builtin import register_builtin_tools


def create_runtime() -> AgentRouter:

    router = AgentRouter()

    api_agent = APILoadBalancerAgent()

    router.register(
        api_agent
    )

    return router


def create_tool_runtime() -> ToolRuntime:

    skills = SkillRegistry()
    tools = ToolRegistry()

    register_builtin_skills(
        skills
    )

    register_builtin_tools(
        tools
    )

    return ToolRuntime(
        skills=skills,
        tools=tools,
    )
