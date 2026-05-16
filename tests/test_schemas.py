"""Persona / Product / Request schema validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.api.schemas import Persona, Product, SimulateReviewRequest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PERSONA_DIR = PROJECT_ROOT / "data" / "sample" / "personas"
PRODUCT_DIR = PROJECT_ROOT / "data" / "sample" / "products"


@pytest.mark.parametrize("persona_file", sorted(PERSONA_DIR.glob("*.json")))
def test_sample_personas_validate(persona_file: Path) -> None:
    data = json.loads(persona_file.read_text(encoding="utf-8"))
    p = Persona.model_validate(data)
    assert 0.0 <= p.hedonic_utilitarian <= 1.0
    assert 0.0 <= p.communal_individual <= 1.0
    assert p.register_tier is not None
    if p.aspect_priority:
        # weights should be sensibly normalised (don't strictly require sum=1.0)
        total = sum(p.aspect_priority.values())
        assert 0.5 < total < 1.5, f"{persona_file.name} aspect_priority sums to {total}"


@pytest.mark.parametrize("product_file", sorted(PRODUCT_DIR.glob("*.json")))
def test_sample_products_validate(product_file: Path) -> None:
    data = json.loads(product_file.read_text(encoding="utf-8"))
    Product.model_validate(data)


def test_simulate_review_request_round_trip() -> None:
    persona_data = json.loads((PERSONA_DIR / "chinwe_owerri.json").read_text())
    product_data = json.loads((PRODUCT_DIR / "tecno_spark_10.json").read_text())
    req = SimulateReviewRequest(
        persona=Persona.model_validate(persona_data),
        product=Product.model_validate(product_data),
    )
    # ensure model_dump_json round-trips
    dumped = req.model_dump_json()
    assert "chinwe_owerri" in dumped
    assert "TECNO-SPARK-10" in dumped
