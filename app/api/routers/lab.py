"""NaijaPersona Labz — experiment history router."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.db.models import LabExperiment
from app.db.repositories.shared import UserRepository
from app.db.storage import DBStorage
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/lab", tags=["lab"])


# ── Dependency ────────────────────────────────────────────────────────────────

async def _ensure_user(user_data: dict = Depends(get_current_user)) -> dict:
    UserRepository().get_or_create(user_data["user_id"], user_data["email"])
    return user_data


# ── Request / response schemas ────────────────────────────────────────────────

class SaveExperimentRequest(BaseModel):
    experiment_type: str          # "review" | "recommend"
    product_title: str
    product_description: str | None = None
    persona_id: str | None = None
    rating: int | None = None
    result: Any                   # full API response stored as JSON


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/experiments")
async def save_experiment(
    req: SaveExperimentRequest,
    user: dict = Depends(_ensure_user),
) -> dict[str, str]:
    """Save a lab experiment result for the current user."""
    uid = uuid.UUID(user["user_id"])
    experiment_id = uuid.uuid4()
    db = DBStorage.get_instance()
    with db.session() as session:
        exp = LabExperiment(
            id=experiment_id,
            user_id=uid,
            experiment_type=req.experiment_type,
            product_title=req.product_title,
            product_description=req.product_description,
            persona_id=req.persona_id,
            rating=req.rating,
            result=req.result,
            created_at=datetime.utcnow(),
        )
        session.add(exp)
        session.flush()
    return {"id": str(experiment_id)}


@router.get("/experiments")
async def list_experiments(
    user: dict = Depends(_ensure_user),
) -> list[dict[str, Any]]:
    """Return the user's experiment history, newest first, up to 50."""
    uid = uuid.UUID(user["user_id"])
    db = DBStorage.get_instance()
    with db.session() as session:
        experiments = (
            session.query(LabExperiment)
            .filter(LabExperiment.user_id == uid)
            .order_by(LabExperiment.created_at.desc())
            .limit(50)
            .all()
        )
        return [
            {
                "id": str(e.id),
                "experiment_type": e.experiment_type,
                "product_title": e.product_title,
                "product_description": e.product_description,
                "persona_id": e.persona_id,
                "rating": e.rating,
                "created_at": e.created_at.isoformat(),
                "result": e.result,
            }
            for e in experiments
        ]


@router.delete("/experiments/{experiment_id}")
async def delete_experiment(
    experiment_id: str,
    user: dict = Depends(_ensure_user),
) -> dict[str, Any]:
    """Delete a single experiment, verifying ownership."""
    uid = uuid.UUID(user["user_id"])
    try:
        eid = uuid.UUID(experiment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid experiment ID")

    db = DBStorage.get_instance()
    with db.session() as session:
        exp = (
            session.query(LabExperiment)
            .filter(LabExperiment.id == eid)
            .first()
        )
        if not exp:
            raise HTTPException(status_code=404, detail="Experiment not found")
        if exp.user_id != uid:
            raise HTTPException(status_code=403, detail="Not your experiment")
        session.delete(exp)
    return {"id": experiment_id, "deleted": True}
