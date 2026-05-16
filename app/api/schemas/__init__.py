"""Pydantic schemas for the API surface."""

from app.api.schemas.persona import Persona, ReviewAnchor, RegisterTier, ExtractionSource
from app.api.schemas.product import Product
from app.api.schemas.requests import (
    SimulateReviewRequest,
    SimulateReviewResponse,
    RecommendRequest,
    RecommendResponse,
    RecommendItem,
    ElicitRequest,
    ElicitResponse,
    HealthResponse,
)

__all__ = [
    "Persona",
    "ReviewAnchor",
    "RegisterTier",
    "ExtractionSource",
    "Product",
    "SimulateReviewRequest",
    "SimulateReviewResponse",
    "RecommendRequest",
    "RecommendResponse",
    "RecommendItem",
    "ElicitRequest",
    "ElicitResponse",
    "HealthResponse",
]
