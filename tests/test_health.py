"""Health endpoint tests."""

from __future__ import annotations

import sys
sys.path.insert(0, "/Users/Franca/Library/Python/3.9/lib/python/site-packages")

from fastapi.testclient import TestClient

from app.api.main import app


def test_health_ok():
    """GET /health returns 200 with a status field."""
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert "status" in body
    assert body["status"] == "ok"
