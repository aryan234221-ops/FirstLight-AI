from fastapi import FastAPI
from app.routers import agents
from app.routers import workflows
from app.routers import knowledge

app = FastAPI(
    title="FirstLight AI Studio",
    version="0.1.0",
)

app.include_router(agents.router)
app.include_router(workflows.router)
app.include_router(knowledge.router)


@app.get("/")
def root():
    return {
        "application": "FirstLight AI Studio",
        "status": "online",
        "version": "0.1.0"
    }