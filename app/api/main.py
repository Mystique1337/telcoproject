"""FastAPI application entry point.

Run locally: `make serve`
Run in Docker: `make demo`
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

# Load .env at import time so os.getenv("OLLAMA_API_KEY") etc. work in the
# LLM client. (pydantic-settings only loads fields declared in app/config.py,
# but the LLM client reads provider keys directly via os.getenv.)
try:
    from dotenv import load_dotenv
    _ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
    if _ENV_PATH.exists():
        load_dotenv(_ENV_PATH, override=False)
except ImportError:
    pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import simulate_review, recommend, elicit, health, catalog, chat, tts, panel, shop, auth, b2b, projects, runs, debug_auth, panel_personas, analytics, share, compare, shopeasy_profile
from app.config import get_settings

settings = get_settings()
logging.basicConfig(level=settings.log_level.upper())
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("starting %s v%s", settings.app_name, settings.app_version)
    # Lightweight schema migration — adds columns that don't exist yet
    try:
        from sqlalchemy import text
        from app.db.storage import DBStorage
        db = DBStorage.get_instance()
        with db.session() as session:
            session.execute(text("ALTER TABLE panel_runs ADD COLUMN IF NOT EXISTS meta JSONB"))
            session.execute(text("ALTER TABLE panel_runs ADD COLUMN IF NOT EXISTS share_token TEXT"))
            session.execute(text("ALTER TABLE personas ADD COLUMN IF NOT EXISTS location TEXT"))
            session.execute(text("ALTER TABLE personas ADD COLUMN IF NOT EXISTS display_name TEXT"))
            session.execute(text(
                "CREATE TABLE IF NOT EXISTS shop_orders ("
                "id UUID PRIMARY KEY, "
                "user_id UUID REFERENCES users(id), "
                "status TEXT NOT NULL DEFAULT 'placed', "
                "total_naira FLOAT NOT NULL, "
                "created_at TIMESTAMP NOT NULL"
                ")"
            ))
            session.execute(text(
                "CREATE TABLE IF NOT EXISTS shop_order_items ("
                "id UUID PRIMARY KEY, "
                "order_id UUID REFERENCES shop_orders(id), "
                "product_id TEXT NOT NULL, "
                "product_title TEXT NOT NULL, "
                "quantity INTEGER NOT NULL DEFAULT 1, "
                "unit_price_naira FLOAT NOT NULL"
                ")"
            ))
            session.execute(text(
                "CREATE TABLE IF NOT EXISTS shop_wishlist ("
                "id UUID PRIMARY KEY, "
                "user_id UUID REFERENCES users(id), "
                "product_id TEXT NOT NULL, "
                "product_title TEXT NOT NULL, "
                "product_price FLOAT, "
                "product_category TEXT, "
                "added_at TIMESTAMP NOT NULL"
                ")"
            ))
        logger.info("schema migration OK")
    except Exception:
        logger.warning("schema migration skipped (DB not reachable or already applied)")
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

# CORS
_ALLOWED_ORIGINS = [o.strip() for o in os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:8765,http://localhost:5173,http://localhost:3000,http://127.0.0.1:8765",
).split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin",
                   "X-Requested-With", "Cache-Control"],
    expose_headers=["Content-Length"],
    max_age=600,
)

# Routers
app.include_router(health.router)
app.include_router(simulate_review.router)
app.include_router(recommend.router)
app.include_router(elicit.router)
app.include_router(catalog.router)
app.include_router(chat.router)
app.include_router(tts.router)
app.include_router(panel.router)
app.include_router(shop.router)
app.include_router(auth.router)
app.include_router(b2b.router)
app.include_router(projects.router)
app.include_router(runs.router)
app.include_router(panel_personas.router)
app.include_router(analytics.router)
app.include_router(share.router)
app.include_router(compare.router)
app.include_router(shopeasy_profile.router)
app.include_router(debug_auth.router)


# ── Static frontend (React build) ─────────────────────────────────────────
# In production we serve the built React SPA from frontend/dist/.
# In dev, run `npm run dev` in frontend/ — Vite proxies API calls back here.
from pathlib import Path as _Path
from fastapi.staticfiles import StaticFiles as _StaticFiles
from fastapi.responses import FileResponse as _FileResponse

_FRONTEND_DIST = _Path(__file__).resolve().parents[2] / "frontend_v2" / "dist"

if _FRONTEND_DIST.exists() and (_FRONTEND_DIST / "index.html").exists():
    # Serve hashed asset files (/assets/*) directly.
    app.mount(
        "/assets",
        _StaticFiles(directory=str(_FRONTEND_DIST / "assets")),
        name="frontend-assets",
    )

    # Root + any other non-API path → React index.html (SPA routing).
    @app.get("/", include_in_schema=False)
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str = "") -> _FileResponse:
        # Don't intercept API routes — let them 404 normally if missed.
        # FastAPI's path matching already prefers more-specific routes, so
        # /simulate-review, /recommend, /catalog/*, /docs, /openapi.json are
        # all handled before this catch-all fires.
        return _FileResponse(_FRONTEND_DIST / "index.html")
else:
    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "tasks": "POST /simulate-review (Task 1), POST /recommend (Task 2)",
            "frontend_status": "not built — run `cd frontend && npm install && npm run build`",
        }
