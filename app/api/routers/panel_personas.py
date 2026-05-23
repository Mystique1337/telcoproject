"""Panel personas — expose the 24 bundled Nigerian personas."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter

from app.config import PROJECT_ROOT

router = APIRouter(prefix="/api/panel-personas", tags=["panel-personas"])

_PERSONAS_DIR = PROJECT_ROOT / "data" / "sample" / "personas"


def _load_all() -> list[dict[str, Any]]:
    personas = []
    for fp in sorted(_PERSONAS_DIR.glob("*.json")):
        try:
            personas.append(json.loads(fp.read_text()))
        except Exception:
            pass
    return personas


@router.get("")
async def list_panel_personas() -> list[dict[str, Any]]:
    """Return all 24 panel personas (read from bundled JSON files)."""
    return _load_all()
