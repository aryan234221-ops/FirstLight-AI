from app.engine.agents.planning_agent import PlanningAgent


class FrontendAgent(PlanningAgent):
    """Planning agent specialization for frontend engineering execution plans."""

    ROLE_NAME = "frontend"

    @property
    def agent_name(self) -> str:
        return self.ROLE_NAME
