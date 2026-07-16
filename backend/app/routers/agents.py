from fastapi import APIRouter
from app.engine.agents.ceo_agent import CEOAgent

router = APIRouter(
    prefix="/api/v1/agents",
    tags=["Agents"]
)

ceo = CEOAgent()


@router.post("/ceo/plan")
def create_plan(goal: str):
    return ceo.plan(goal)