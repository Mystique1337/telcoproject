"""FastAPI application entry point.

Run locally: `make serve`
Run in Docker: `make demo`
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import simulate_review, recommend, elicit, health
from app.config import get_settings

settings = get_settings()
logging.basicConfig(level=settings.log_level.upper())
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("starting %s v%s", settings.app_name, settings.app_version)
    yield
    logger.info("shutting down %s", settings.app_name)


app = FastAPI(
    title="Naija Persona Agent",
    description=(
        "Nigerian-context LLM agent system for review simulation (Task 1) and "
        "personalised product recommendation (Task 2). Submission to the Nigerian "
        "AI Agents Hackathon, May 2026."
    ),
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS — open during hackathon evaluation
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router)
app.include_router(simulate_review.router)
app.include_router(recommend.router)
app.include_router(elicit.router)


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "tasks": "POST /simulate-review (Task 1), POST /recommend (Task 2)",
    }
