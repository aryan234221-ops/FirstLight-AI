from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import agents
from app.routers import workflows
from app.routers import knowledge

app = FastAPI(
    title="FirstLight AI Studio",
    version="0.1.0",
)

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


@app.get("/")
def root():
    return {
        "application": "FirstLight AI Studio",
        "status": "online",
        "version": "0.1.0"
    }