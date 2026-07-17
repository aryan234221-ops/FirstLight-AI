from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth.middleware import AuthContextMiddleware
from app.core.application import ApplicationContext
from app.core.logging import RequestContextMiddleware, configure_logging
from app.routers import agents
from app.routers import auth
from app.routers import chat
from app.routers import dashboard
from app.routers import enterprise_workflows
from app.routers import knowledge_v2
from app.routers import observability
from app.routers import projects
from app.routers import workflows
from app.routers import knowledge
from app.routers import workflow_history

configure_logging()
context = ApplicationContext()

app = FastAPI(
    title="FirstLight AI Studio",
    version="2.0.0-enterprise",
)

app.add_middleware(RequestContextMiddleware)
app.add_middleware(AuthContextMiddleware, auth_service=context.auth_service)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://127.0.0.1:3001",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents.router)
app.include_router(workflows.router)
app.include_router(knowledge.router)
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(dashboard.router)
app.include_router(enterprise_workflows.router)
app.include_router(knowledge_v2.router)
app.include_router(chat.router)
app.include_router(workflow_history.router)
app.include_router(observability.router)


@app.get("/")
def root():
    return {
        "application": "FirstLight AI Studio",
        "status": "online",
        "version": "2.0.0-enterprise"
    }