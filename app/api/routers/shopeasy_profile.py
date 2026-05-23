"""ShopEasy persona — DB-backed profile (language, location, cognitive dims)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.db.models import Persona
from app.db.repositories.shared import UserRepository
from app.db.storage import DBStorage
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/shopeasy", tags=["shopeasy-profile"])

# ── Zone / register helpers (mirrors auth.py logic) ──────────────────────────

_ZONE_BY_KW: dict[str, str] = {
    "lagos": "South-West", "ibadan": "South-West", "abeokuta": "South-West",
    "ogun": "South-West", "ondo": "South-West", "ekiti": "South-West", "osun": "South-West", "oyo": "South-West",
    "owerri": "South-East", "aba": "South-East", "enugu": "South-East", "anambra": "South-East",
    "onitsha": "South-East", "nnewi": "South-East", "imo": "South-East", "abia": "South-East",
    "port harcourt": "South-South", "warri": "South-South", "calabar": "South-South",
    "delta": "South-South", "rivers": "South-South", "bayelsa": "South-South", "uyo": "South-South",
    "kano": "North-West", "kaduna": "North-West", "sokoto": "North-West",
    "katsina": "North-West", "zamfara": "North-West", "kebbi": "North-West", "jigawa": "North-West",
    "maiduguri": "North-East", "bauchi": "North-East", "gombe": "North-East",
    "abuja": "North-Central", "jos": "North-Central", "makurdi": "North-Central", "ilorin": "North-Central",
}

_ZONE_REGISTER: dict[str, str] = {
    "South-West": "code_mixed",
    "South-East": "code_mixed",
    "South-South": "nigerian_pidgin",
    "North-West": "nigerian_english",
    "North-East": "nigerian_english",
    "North-Central": "nigerian_english",
}

_LANG_REGISTER: dict[str, str] = {
    "pidgin": "nigerian_pidgin",
    "yoruba": "code_mixed",
    "igbo": "code_mixed",
    "hausa": "nigerian_english",
    "english": "nigerian_english",
}


def _zone_for(location: str) -> str:
    loc = location.lower()
    for kw, zone in _ZONE_BY_KW.items():
        if kw in loc:
            return zone
    return "Unknown"


def _register_for(location: str, language: str) -> str:
    lang_reg = _LANG_REGISTER.get(language.lower(), "nigerian_english")
    zone = _zone_for(location)
    zone_reg = _ZONE_REGISTER.get(zone, "nigerian_english")
    # Language preference takes precedence for non-English speakers
    if language.lower() in ("pidgin", "yoruba", "igbo", "hausa"):
        return lang_reg
    return zone_reg


# ── Dependency ────────────────────────────────────────────────────────────────

async def _ensure_user(user_data: dict = Depends(get_current_user)) -> dict:
    UserRepository().get_or_create(user_data["user_id"], user_data["email"])
    return user_data


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/profile")
async def get_profile(user: dict = Depends(_ensure_user)) -> dict[str, Any]:
    """Return the user's ShopEasy persona, or 404 if not set up yet."""
    uid = uuid.UUID(user["user_id"])
    db = DBStorage.get_instance()
    with db.session() as session:
        persona = session.query(Persona).filter(Persona.user_id == uid).first()
        if not persona:
            raise HTTPException(status_code=404, detail="ShopEasy profile not found")
        session.expunge(persona)

    return {
        "user_id": str(persona.user_id),
        "display_name": persona.display_name or user["email"].split("@")[0],
        "language": persona.language_preference,
        "location": persona.location or "",
        "register_tier": persona.register_tier,
        "hedonic_utilitarian": persona.hedonic_utilitarian,
        "communal_individual": persona.communal_individual,
        "aspect_priority": persona.aspect_priority,
    }


class SetupRequest(BaseModel):
    display_name: str
    language: str = "english"
    location: str


@router.post("/profile")
async def setup_profile(
    req: SetupRequest,
    user: dict = Depends(_ensure_user),
) -> dict[str, Any]:
    """Create or update the user's ShopEasy persona in the DB."""
    uid = uuid.UUID(user["user_id"])
    register = _register_for(req.location, req.language)

    db = DBStorage.get_instance()
    with db.session() as session:
        persona = session.query(Persona).filter(Persona.user_id == uid).first()

        if persona:
            persona.display_name = req.display_name
            persona.language_preference = req.language
            persona.location = req.location
            persona.register_tier = register
            persona.updated_at = datetime.utcnow()
        else:
            persona = Persona(
                user_id=uid,
                display_name=req.display_name,
                language_preference=req.language,
                location=req.location,
                register_tier=register,
                hedonic_utilitarian=0.5,
                communal_individual=0.5,
                aspect_priority={"value_for_money": 0.3, "quality": 0.3, "durability": 0.2},
            )
            session.add(persona)
        session.flush()
        session.expunge(persona)

    return {
        "user_id": str(persona.user_id),
        "display_name": persona.display_name,
        "language": persona.language_preference,
        "location": persona.location,
        "register_tier": persona.register_tier,
    }
