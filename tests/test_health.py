"""Sanity checks for the FastAPI app — runs without external services."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.main import app


def test_health_returns_ok() -> None:
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "version" in body
    assert "components" in body


def test_root_lists_endpoints() -> None:
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    assert "tasks" in r.json()


def test_openapi_schema_loads() -> None:
    client = TestClient(app)
    r = client.get("/openapi.json")
    assert r.status_code == 200
    paths = r.json()["paths"]
    assert "/simulate-review" in paths
    assert "/recommend" in paths
    assert "/elicit" in paths
    assert "/health" in paths


def test_elicit_returns_questions() -> None:
    client = TestClient(app)
    r = client.post("/elicit", json={"seed_text": "abeg this thing dey scatter me"})
    assert r.status_code == 200
    data = r.json()
    assert len(data["questions"]) == 3
    assert data["seeded_register_tier"] == "nigerian_pidgin"
