from app.engine.agents.planning_agent import PlanningAgent


class QAAgent(PlanningAgent):
    """Planning agent specialization for quality assurance execution plans."""

    ROLE_NAME = "qa"

    @property
    def agent_name(self) -> str:
        return self.ROLE_NAME
