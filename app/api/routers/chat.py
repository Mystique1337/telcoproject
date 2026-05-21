"""Conversational shopping agent endpoint.

POST /chat — one turn of a multi-turn conversation. The agent decides each
turn whether to ASK a clarifying question or RECOMMEND products. Constraints
(budget, category, recipient) are extracted from the running conversation
and applied as HARD filters to retrieval.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agents.chat_agent import chat_step
from app.api.schemas import RecommendItem
from app.api.schemas.persona import Persona

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str


class ChatRequest(BaseModel):
    history: list[ChatMessage] = Field(
        default_factory=list,
        description="Ordered conversation so far. Most-recent turn last.",
    )
    persona: Persona | None = Field(
        default=None,
        description=(
            "Optional Persona — if provided, used for register / aspect "
            "personalisation. If omitted, the agent operates anonymously."
        ),
    )
    orchestrator_override: str | None = Field(
        default=None,
        description=(
            "Per-request override for the orchestrator LLM that decides "
            "ask-vs-recommend each turn. Format 'provider:model'. Defaults "
            "to settings.task2_reranker."
        ),
    )
    reranker_override: str | None = Field(
        default=None,
        description="Per-request override for the LLM that ranks candidates.",
    )
    k: int = Field(default=5, ge=1, le=20)
    include_reasoning: bool = False
    language: Literal["yoruba", "hausa", "igbo"] | None = Field(
        default=None,
        description=(
            "Optional: have the assistant reply directly in a Nigerian language "
            "(Yoruba / Hausa / Igbo). If unset, replies in English/Pidgin."
        ),
    )


class ChatResponse(BaseModel):
    action: str = Field(..., description="ask | recommend | refine")
    message: str
    recommendations: list[RecommendItem] = Field(default_factory=list)
    extracted_constraints: dict[str, Any] = Field(default_factory=dict)
    filters_applied: dict[str, Any] = Field(default_factory=dict)
    rerank_fallback_reason: str | None = None
    reasoning_trace: list[dict[str, Any]] | None = None
    latency_ms: int


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    started = time.perf_counter()
    try:
        out = await chat_step(
            history=[t.model_dump() for t in req.history],
            persona=req.persona,
            orchestrator_spec=req.orchestrator_override,
            reranker_spec=req.reranker_override,
            include_reasoning=req.include_reasoning,
            k=req.k,
            language=req.language,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("chat step failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    recs = [RecommendItem(**r) for r in out.get("recommendations", [])]
    return ChatResponse(
        action=out["action"],
        message=out["message"],
        recommendations=recs,
        extracted_constraints=out.get("extracted_constraints", {}),
        filters_applied=out.get("filters_applied", {}),
        rerank_fallback_reason=out.get("rerank_fallback_reason"),
        reasoning_trace=out.get("reasoning_trace"),
        latency_ms=out.get("latency_ms") or int((time.perf_counter() - started) * 1000),
    )
