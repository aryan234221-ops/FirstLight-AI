from app.engine.agents.planning_agent import PlanningAgent


class CEOAgent(PlanningAgent):
    """Planning agent specialization for CEO-level execution planning."""

    ROLE_NAME = "ceo"

    @property
    def agent_name(self) -> str:
        return self.ROLE_NAME