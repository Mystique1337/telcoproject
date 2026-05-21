"""InsideNaija panel endpoint — run a product across the persona panel.

POST /panel
Input:  { product, persona_ids?, backbone_override?, target_language? }
Output: { product_title, reactions[], aggregate{}, latency_ms }
"""

from __future__ import annotations

import logging
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agents.panel_agent import run_panel
from app.api.schemas.product import Product

logger = logging.getLogger(__name__)
router = APIRouter(tags=["insidenaija"])


class PanelRequest(BaseModel):
    product: Product
    persona_ids: list[str] | None = Field(
        default=None,
        description="Subset of persona ids to run. Omit to run the full 24-persona panel.",
    )
    backbone_override: str | None = None
    target_language: Literal["yoruba", "hausa", "igbo"] | None = None


@router.post("/panel")
async def panel(req: PanelRequest) -> dict[str, Any]:
    """Fan a product out across the persona panel and aggregate insights."""
    try:
        result = await run_panel(
            product=req.product,
            persona_ids=req.persona_ids,
            backbone_override=req.backbone_override,
            target_language=req.target_language,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("panel run failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result
