"""Public share endpoint — no auth required."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/share", tags=["share"])


@router.get("/{token}")
async def get_shared_run(token: str) -> dict[str, Any]:
    """Return a shared run's summary by share token (public, no auth)."""
    from app.db.repositories.insidenaija import (
        PanelRunRepository,
        ResultRepository,
        ProjectRepository,
    )

    run_repo = PanelRunRepository()
    result_repo = ResultRepository()
    project_repo = ProjectRepository()

    run = run_repo.find_by_share_token(token)
    if not run:
        raise HTTPException(status_code=404, detail="Shared run not found")

    import uuid as _uuid
    project = project_repo.find(_uuid.UUID(str(run.project_id)))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    results = result_repo.find_by_run(str(run.id))
    meta = run.meta or {}

    return {
        "run_id": str(run.id),
        "project_name": project.name,
        "project_category": project.category,
        "created_at": run.created_at.isoformat(),
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "aggregate": meta.get("aggregate"),
        "results": [
            {
                "id": str(r.id),
                "persona_id": r.persona_id,
                "persona_name": r.persona_name,
                "review_text": r.review_text,
                "rating": r.rating,
                "register_tier": r.register_tier,
                "sentiment": r.sentiment,
            }
            for r in results
        ],
    }
