from fastapi import APIRouter
from app.core.application import ApplicationContext
from app.engine.agents.ceo_agent import CEOAgent

router = APIRouter(
    prefix="/api/v1/agents",
    tags=["Agents"]
)

context = ApplicationContext()
dispatcher = context.agent_dispatcher


@router.post("/ceo/plan")
def create_plan(goal: str):
    return dispatcher.dispatch(CEOAgent.ROLE_NAME, goal)