"""Product schema — the unit of recommendation and review subject."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Product(BaseModel):
    product_id: str
    title: str
    category: str
    description: str = ""
    brand: str | None = None
    price_naira: float | None = None
    seller: str | None = None
    domain: str = Field(default="jumia", description="jumia | nollywood | etc.")
    metadata: dict[str, Any] = Field(default_factory=dict)
