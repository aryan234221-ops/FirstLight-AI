from fastapi import FastAPI
from app.routers import agents

app = FastAPI(
    title="FirstLight AI Studio",
    version="0.1.0",
)

app.include_router(agents.router)


@app.get("/")
def root():
    return {
        "application": "FirstLight AI Studio",
        "status": "online",
        "version": "0.1.0"
    }