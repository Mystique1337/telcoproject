"""Persona schema — the central abstraction shared by both agents.

See PRD v4 §5 for design rationale.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RegisterTier(str, Enum):
    """Four-tier Nigerian register classification."""

    STANDARD_ENGLISH = "standard_english"
    NIGERIAN_ENGLISH = "nigerian_english"
    NIGERIAN_PIDGIN = "nigerian_pidgin"
    CODE_MIXED = "code_mixed"  # English + Yoruba / Hausa / Igbo


class ExtractionSource(str, Enum):
    HISTORY = "history"
    ELICITATION = "elicitation"
    SYNTHETIC = "synthetic"
    MANUAL = "manual"


class ReviewAnchor(BaseModel):
    """A representative past review used for retrieval-based style anchoring."""

    review_id: str
    product_id: str
    rating: int = Field(ge=1, le=5)
    text: str
    similarity_score: float | None = None


class Persona(BaseModel):
    """Structured persona representation.

    4 cognitive dimensions + register tier + aspect priorities + history anchors.
    Trimmed from v3.1's 6-dimension schema for the 5-day build.
    """

    # Identity (never PII)
    user_id: str | None = None
    demographics: dict[str, Any] | None = None  # age range, location, gender — coarse only

    # Cognitive dimensions (4)
    hedonic_utilitarian: float = Field(
        0.5, ge=0.0, le=1.0, description="0.0 utilitarian → 1.0 hedonic"
    )
    intensity_calibration: dict[str, float] = Field(
        default_factory=dict,
        description='Per-user word-to-rating mapping, e.g. {"amazing": 4.8, "okay": 3.0}',
    )
    communal_individual: float = Field(
        0.5, ge=0.0, le=1.0, description="0.0 individualist → 1.0 communal"
    )
    aspect_priority: dict[str, float] = Field(
        default_factory=dict,
        description="Per-domain aspect weights summing to ~1.0",
    )

    # Cultural register
    register_tier: RegisterTier = RegisterTier.NIGERIAN_ENGLISH
    register_markers: list[str] = Field(default_factory=list)
    register_confidence: float = Field(0.5, ge=0.0, le=1.0)

    # History anchors for retrieval
    review_anchors: list[ReviewAnchor] = Field(default_factory=list)
    history_count: int = Field(default=0, ge=0)

    # Provenance
    extraction_source: ExtractionSource = ExtractionSource.MANUAL
    extraction_timestamp: datetime = Field(default_factory=datetime.utcnow)
    schema_version: str = "1.0"

    def primary_aspects(self, top_k: int = 3) -> list[str]:
        """Return the top-k aspects this user emphasises in reviews."""
        return [
            aspect
            for aspect, _ in sorted(
                self.aspect_priority.items(), key=lambda kv: kv[1], reverse=True
            )[:top_k]
        ]
