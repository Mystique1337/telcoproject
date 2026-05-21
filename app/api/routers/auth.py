"""Passwordless accounts + onboarding.

A user "registers" by answering a short onboarding wizard (name, location,
age, a few preferences). We build a persona from those answers and store the
profile in SQLite. There is no password — the returned `profile_id` is the
session token (kept in the browser's localStorage). This is the spine that
makes both products personalised to a real Nigerian user.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import PROJECT_ROOT

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["accounts"])

_DB = PROJECT_ROOT / "data" / "profiles.db"


def _conn() -> sqlite3.Connection:
    _DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(_DB)
    c.execute(
        """CREATE TABLE IF NOT EXISTS profiles (
            id TEXT PRIMARY KEY,
            name TEXT,
            data TEXT,
            persona TEXT,
            created_at REAL
        )"""
    )
    return c


# Nigerian state/city -> geopolitical zone (subset; matched by substring).
_ZONE = {
    "lagos": "South-West", "ibadan": "South-West", "abeokuta": "South-West", "osun": "South-West",
    "oyo": "South-West", "ondo": "South-West", "ekiti": "South-West", "ogun": "South-West",
    "owerri": "South-East", "aba": "South-East", "onitsha": "South-East", "enugu": "South-East",
    "nnewi": "South-East", "anambra": "South-East", "imo": "South-East", "abia": "South-East",
    "port harcourt": "South-South", "warri": "South-South", "calabar": "South-South",
    "uyo": "South-South", "benin": "South-South", "delta": "South-South", "rivers": "South-South",
    "kano": "North-West", "kaduna": "North-West", "sokoto": "North-West", "katsina": "North-West",
    "zamfara": "North-West", "kebbi": "North-West", "jigawa": "North-West",
    "maiduguri": "North-East", "bauchi": "North-East", "gombe": "North-East", "yola": "North-East",
    "abuja": "North-Central", "jos": "North-Central", "makurdi": "North-Central",
    "ilorin": "North-Central", "lokoja": "North-Central", "minna": "North-Central",
}

# Default register tier per zone (a sensible starting guess the user can't see;
# drives how reviews/replies sound for them).
_ZONE_REGISTER = {
    "South-West": "code_mixed", "South-East": "code_mixed", "South-South": "nigerian_pidgin",
    "North-West": "nigerian_english", "North-East": "nigerian_english",
    "North-Central": "nigerian_english",
}

# Interest keyword -> aspect weight bumps.
_INTEREST_ASPECTS = {
    "fashion": {"design": 0.3, "value_for_money": 0.2},
    "beauty": {"quality": 0.3, "design": 0.2},
    "phones": {"quality": 0.3, "durability": 0.2},
    "electronics": {"quality": 0.3, "durability": 0.2},
    "home": {"durability": 0.3, "value_for_money": 0.2},
    "kitchen": {"durability": 0.3, "value_for_money": 0.2},
    "baby": {"safety": 0.3, "value_for_money": 0.2},
    "groceries": {"value_for_money": 0.4},
    "gaming": {"quality": 0.3, "design": 0.2},
}


def _zone_for(location: str) -> str:
    loc = (location or "").lower()
    for k, z in _ZONE.items():
        if k in loc:
            return z
    return "Unknown"


def build_persona(profile: dict[str, Any]) -> dict[str, Any]:
    """Synthesise a Persona-shaped record from onboarding answers."""
    zone = _zone_for(profile.get("location", ""))
    register = _ZONE_REGISTER.get(zone, "nigerian_english")

    # Aspect priority from interests, with a baseline.
    aspects: dict[str, float] = {"value_for_money": 0.3, "quality": 0.3, "durability": 0.2}
    for it in (profile.get("interests") or []):
        for asp, w in _INTEREST_ASPECTS.get(str(it).lower(), {}).items():
            aspects[asp] = aspects.get(asp, 0.0) + w
    total = sum(aspects.values()) or 1.0
    aspects = {k: round(v / total, 3) for k, v in aspects.items()}

    # Communal lean: family-oriented occupations / "family" interest nudge up.
    interests_l = [str(i).lower() for i in (profile.get("interests") or [])]
    communal = 0.65 if ("family" in interests_l or "baby" in interests_l) else 0.5
    hedonic = 0.6 if ("fashion" in interests_l or "beauty" in interests_l or "gaming" in interests_l) else 0.45

    return {
        "user_id": profile["name"].strip().lower().replace(" ", "_")[:40] or "shopper",
        "demographics": {
            "age_range": profile.get("age_range"),
            "location": profile.get("location"),
            "occupation": profile.get("occupation"),
        },
        "hedonic_utilitarian": hedonic,
        "communal_individual": communal,
        "intensity_calibration": {},
        "aspect_priority": aspects,
        "register_tier": register,
        "register_markers": [],
        "register_confidence": 0.5,
        "review_anchors": [],
        "history_count": 0,
        "extraction_source": "elicitation",
        "schema_version": "1.0",
    }


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    location: str = Field(..., min_length=1, max_length=80)
    age_range: str | None = None
    gender: str | None = None
    occupation: str | None = None
    interests: list[str] = Field(default_factory=list)
    language: str | None = None


@router.post("/register")
async def register(req: RegisterRequest) -> dict[str, Any]:
    profile = req.model_dump()
    persona = build_persona(profile)
    pid = uuid.uuid4().hex[:16]
    with _conn() as c:
        c.execute(
            "INSERT INTO profiles (id, name, data, persona, created_at) VALUES (?,?,?,?,?)",
            (pid, req.name, json.dumps(profile), json.dumps(persona), time.time()),
        )
        c.commit()
    return {"profile_id": pid, "profile": profile, "persona": persona, "zone": _zone_for(req.location)}


def persona_for_profile(profile_id: str) -> dict[str, Any] | None:
    """Return the stored persona dict for a profile id, or None."""
    try:
        with _conn() as c:
            row = c.execute("SELECT persona FROM profiles WHERE id=?", (profile_id,)).fetchone()
        return json.loads(row[0]) if row else None
    except Exception:  # noqa: BLE001
        return None


@router.get("/profile/{profile_id}")
async def get_profile(profile_id: str) -> dict[str, Any]:
    with _conn() as c:
        row = c.execute(
            "SELECT name, data, persona FROM profiles WHERE id=?", (profile_id,)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="profile not found")
    return {"profile_id": profile_id, "name": row[0],
            "profile": json.loads(row[1]), "persona": json.loads(row[2])}
