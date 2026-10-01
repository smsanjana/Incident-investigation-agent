import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.db import create_db_and_tables
from app.routers import actions, evidence, incidents, investigation, report


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title="Incident Investigation Agent",
    description="""An AI-assisted incident investigation agent that inspects logs, runbooks, 
    service metadata, and deployment events to produce evidence-based investigation reports.
    
    **Safety**: This agent is read-only. High-risk actions are identified but never executed.
    Approval endpoints record decisions only — execution requires manual engineer action.""",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(incidents.router)
app.include_router(investigation.router)
app.include_router(evidence.router)
app.include_router(report.router)
app.include_router(actions.router)

# Mount static and artefact files
static_dir = os.path.join(os.path.dirname(__file__), "static")
artefacts_dir = os.path.join(os.path.dirname(__file__), "..", "artefacts")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

if os.path.exists(artefacts_dir):
    app.mount("/artefacts", StaticFiles(directory=artefacts_dir), name="artefacts")


@app.get("/", tags=["UI"])
def root():
    """Serve the modern interactive UI dashboard."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "service": "Incident Investigation Agent",
        "version": "1.0.0",
        "status": "healthy",
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
def health():
    return {"status": "healthy"}
