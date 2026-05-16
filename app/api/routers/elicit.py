"""Cold-start persona elicitation.

POST /elicit
Returns a 3-question flow that, combined with optional seed text, seeds a Persona.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter

from app.api.schemas import ElicitRequest, ElicitResponse
from app.api.schemas.persona import RegisterTier

logger = logging.getLogger(__name__)
router = APIRouter(tags=["task-1", "task-2"])


_QUESTIONS = [
    "When you find a product you love, do you tend to (a) write a glowing review or (b) keep it brief? "
    "(this helps us understand your expressive intensity)",
    "Are you usually shopping for yourself, or for family / community use? "
    "(this helps us understand your framing)",
    "What three things matter most to you about a product? "
    "(e.g. delivery speed, build quality, value-for-naira, customer service, seller reputation)",
]


@router.post("/elicit", response_model=ElicitResponse)
async def elicit(req: ElicitRequest) -> ElicitResponse:
    """Return a cold-start 3-question flow.

    Future iteration: the client posts answers back to `/elicit/complete` to receive
    a fully-populated Persona.
    """
    session_id = str(uuid.uuid4())
    # naive register-from-seed inference (full impl uses the LLM client)
    seeded_register: RegisterTier | None = None
    if req.seed_text:
        text = req.seed_text.lower()
        if any(m in text for m in ["abeg", "wahala", "no cap", "scatter", "e shock"]):
            seeded_register = RegisterTier.NIGERIAN_PIDGIN
        elif any(m in text for m in ["ahn ahn", "haba", "wallahi", "biko", "nna"]):
            seeded_register = RegisterTier.CODE_MIXED
        else:
            seeded_register = RegisterTier.NIGERIAN_ENGLISH

    logger.info("elicit session=%s seeded_register=%s", session_id, seeded_register)
    return ElicitResponse(
        questions=_QUESTIONS,
        session_id=session_id,
        seeded_register_tier=seeded_register,
    )
