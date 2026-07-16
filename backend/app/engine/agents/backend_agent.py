from app.engine.agents.planning_agent import PlanningAgent


class BackendAgent(PlanningAgent):
    """Planning agent specialization for backend engineering execution plans."""

    ROLE_NAME = "backend"

    @property
    def agent_name(self) -> str:
        return self.ROLE_NAME
