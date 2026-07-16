from app.engine.agents.planning_agent import PlanningAgent


class ArchitectAgent(PlanningAgent):
    """Agent responsible for converting high-level plans into software architecture plans."""

    ROLE_NAME = "architect"

    @property
    def agent_name(self) -> str:
        return self.ROLE_NAME
