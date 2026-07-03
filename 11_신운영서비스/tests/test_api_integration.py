from __future__ import annotations

import pytest


def test_health_endpoint_without_database() -> None:
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    from heatgrid_ops.api.app import app

    response = TestClient(app).get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "heatgrid-ops"
