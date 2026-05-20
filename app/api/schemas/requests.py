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
    target_rating: int | None = Field(
        default=None, ge=1, le=5,
        description=(
            "Optional explicit star rating (1-5). When set, the agent will "
            "generate a review CONSISTENT with this rating instead of the "
            "Stage-A heuristic prediction. Use to test how the model writes "
            "for a given sentiment (1-star angry vs 5-star delighted)."
        ),
    )
    aspect_focus: str | None = Field(
        default=None, max_length=120,
        description=(
            "Optional aspect to emphasise (free text, ≤120 chars). "
            "Examples: 'battery life', 'value for money', 'delivery speed', "
            "'build quality after one month of use'."
        ),
    )
    length_hint: str | None = Field(
        default=None,
        description="Optional: 'short' (1-2 sentences), 'medium' (3-5), 'long' (6-8).",
    )
    tone_modifier: str | None = Field(
        default=None, max_length=80,
        description=(
            "Optional tone direction (free text). Examples: 'enthusiastic', "
            "'skeptical', 'frustrated', 'measured', 'sarcastic'."
        ),
    )
    refinement_instructions: str | None = Field(
        default=None, max_length=500,
        description=(
            "Optional natural-language refinement instruction for iterating "
            "on a prior review. Examples: 'make it shorter', 'use more Pidgin', "
            "'rewrite as 3 stars', 'mention the Owambe use case'."
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
    price_naira: float | None = None
    category: str | None = None
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
    rerank_fallback_reason: str | None = Field(
        default=None,
        description=(
            "When the re-ranker LLM did not return parseable JSON, the agent "
            "falls back to pre-rank order (similarity + popularity + aspect-match) "
            "and surfaces the reason here. Typically populated when a Task A "
            "review-generation fine-tune is incorrectly used as the Task B "
            "re-ranker."
        ),
    )
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
