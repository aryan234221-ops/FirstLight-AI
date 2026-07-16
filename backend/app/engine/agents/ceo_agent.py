from app.engine.core.base_agent import BaseAgent
from app.engine.core.task import Task, Plan

class CEOAgent(BaseAgent):

    def __init__(self):
        super().__init__("CEO AI")

    def plan(self, goal: str) -> Plan:

        tasks = [
            Task(
                title="Analyze Requirements",
                description=f"Understand: {goal}"
            ),
            Task(
                title="Design Architecture",
                description="Prepare system architecture"
            ),
            Task(
                title="Assign Backend",
                description="Backend implementation"
            ),
            Task(
                title="Assign Frontend",
                description="Frontend implementation"
            ),
            Task(
                title="QA",
                description="Testing and review"
            ),
        ]

        return Plan(
            goal=goal,
            tasks=tasks
        )