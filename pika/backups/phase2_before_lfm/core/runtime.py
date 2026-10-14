from core.router import AgentRouter
from agents.local import LocalAgent
from models.providers.mock import MockProvider


def create_runtime() -> AgentRouter:

    router = AgentRouter()

    provider = MockProvider()

    local_agent = LocalAgent(
        provider=provider
    )

    router.register(local_agent)

    return router
