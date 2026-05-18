"""Request and response models for the two hackathon endpoints + supporting routes."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.api.schemas.persona import Persona, RegisterTier
from app.api.schemas.product import Product


# --------------------------------------------------------------------------- #
# Task 1 — Simulate review                                                     #
# --------------------------------------------------------------------------- #


class SimulateReviewRequest(BaseModel):
    persona: Persona
    product: Product
    stream: bool = False
    include_reasoning: bool = False
    backbone_override: str | None = Field(
        default=None,
        description=(
            "Per-request override of TASK1_BACKBONE. Format: 'provider:model'. "
            "Examples: 'lmstudio:naija-reviewer-8b', 'anthropic:claude-sonnet-4-20250514', "
            "'openai:gpt-4o', 'ollama:naija-reviewer-8b'. If unset, uses TASK1_BACKBONE from env."
        ),
    )


class SimulateReviewResponse(BaseModel):
    rating: int = Field(ge=1, le=5)
    review: str
    register_tier: RegisterTier
    rationale: str
    fallback_reason: str | None = None
    reasoning_trace: list[dict[str, Any]] | None = None
    latency_ms: int


# --------------------------------------------------------------------------- #
# Task 2 — Recommend                                                           #
# --------------------------------------------------------------------------- #


class RecommendRequest(BaseModel):
    persona: Persona
    candidate_set: list[str] | None = Field(
        default=None,
        description="If omitted, the agent retrieves candidates via Chroma over the product index.",
    )
    domain: str = Field(
        default="jumia",
        description=(
            "Single domain ('jumia'/'konga'/'nollywood'), or 'all' / comma-list for "
            "cross-domain retrieval ('jumia,konga' or 'all')."
        ),
    )
    k: int = Field(default=5, ge=1, le=20)
    include_negatives: bool = False
    include_reasoning: bool = False
    reranker_override: str | None = Field(
        default=None,
        description=(
            "Per-request override of TASK2_RERANKER. Format: 'provider:model'. "
            "Examples: 'lmstudio:naija-reviewer-8b', 'anthropic:claude-sonnet-4-20250514', "
            "'openai:gpt-4o'. If unset, uses TASK2_RERANKER from env."
        ),
    )
    conversation_history: list[dict[str, str]] | None = Field(
        default=None,
        description=(
            "Optional multi-turn context: ordered list of {role, content} chat turns. "
            "Constraints (budget, recipient, category) are extracted and folded into "
            "the re-ranking prompt. Enables conversational refinement scenarios."
        ),
    )


class RecommendItem(BaseModel):
    product_id: str
    title: str | None = None
    score: float
    rationale: str
    serendipity_score: float | None = None
    rank: int


class RecommendResponse(BaseModel):
    recommendations: list[RecommendItem]
    negatives: list[RecommendItem] | None = None
    cold_start: bool | None = None
    cross_domain: bool | None = None
    multi_turn: bool | None = None
    extracted_constraints: list[str] | None = None
    reasoning_trace: list[dict[str, Any]] | None = None
    latency_ms: int


# --------------------------------------------------------------------------- #
# Cold-start elicitation                                                       #
# --------------------------------------------------------------------------- #


class ElicitRequest(BaseModel):
    user_id: str | None = None
    seed_text: str | None = None  # any text from the user; informs register


class ElicitResponse(BaseModel):
    questions: list[str]
    session_id: str
    seeded_register_tier: RegisterTier | None = None


# --------------------------------------------------------------------------- #
# Health                                                                       #
# --------------------------------------------------------------------------- #


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    app_name: str
    components: dict[str, str]
