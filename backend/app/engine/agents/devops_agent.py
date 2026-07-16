from app.engine.agents.planning_agent import PlanningAgent


class DevOpsAgent(PlanningAgent):
    """Planning agent specialization for DevOps execution plans."""

    ROLE_NAME = "devops"

    @property
    def agent_name(self) -> str:
        return self.ROLE_NAME
