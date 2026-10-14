from agents.base import Agent


class AgentRouter:

    def __init__(self):
        self._agents: dict[str, Agent] = {}

    def register(
        self,
        agent: Agent,
    ) -> None:

        self._agents[agent.name] = agent

    def get(
        self,
        name: str,
    ) -> Agent:

        if name not in self._agents:
            raise ValueError(
                f"Agent '{name}' is not registered."
            )

        return self._agents[name]

    def select(
        self,
        capability: str | None = None,
    ) -> Agent:

        if capability:

            for agent in self._agents.values():

                if capability in agent.capabilities:
                    return agent

        if "local" in self._agents:
            return self._agents["local"]

        raise RuntimeError(
            "No suitable agent is available."
        )
