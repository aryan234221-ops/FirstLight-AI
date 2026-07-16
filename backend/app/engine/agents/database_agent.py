from app.engine.agents.planning_agent import PlanningAgent


class DatabaseAgent(PlanningAgent):
    """Planning agent specialization for database architecture execution plans."""

    ROLE_NAME = "database"

    @property
    def agent_name(self) -> str:
        return self.ROLE_NAME
