"""
AgentMail AI - FastAPI Application Server
Initializes database, checks RAG index, and serves REST API & static dashboard.
"""

from pathlib import Path
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import BASE_DIR, API_HOST, API_PORT
from backend.database.db import init_db
from backend.rag.vector_store import LocalVectorStore
from backend.api.routes import router as api_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("agentmail.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database and RAG Index
    logger.info("Initializing AgentMail AI SQLite database...")
    init_db()
    logger.info("Ensuring RAG Knowledge Base is indexed...")
    vs = LocalVectorStore()
    vs.index_knowledge_base(force_reindex=False)
    yield
    # Shutdown
    logger.info("AgentMail AI server shutting down.")


app = FastAPI(
    title="AgentMail AI",
    description="An Agentic AI-Based Intelligent Email Management System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for local frontend dashboard communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router, prefix="/api")

# Mount Static Dashboard Files
DASHBOARD_DIR = BASE_DIR / "dashboard"
if DASHBOARD_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(DASHBOARD_DIR)), name="static")
    app.mount("/", StaticFiles(directory=str(DASHBOARD_DIR), html=True), name="dashboard")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=API_HOST, port=API_PORT, reload=True)
