from __future__ import annotations

from conftest import login_as_admin


def test_health_and_readiness(client):
    health_response = client.get("/api/v2/observability/health")
    assert health_response.status_code == 200
    assert health_response.json()["status"] == "ok"

    readiness_response = client.get("/api/v2/observability/readiness")
    assert readiness_response.status_code == 200
    assert readiness_response.json()["status"] == "ready"


def test_metrics_requires_auth(client):
    unauthorized = client.get("/api/v2/observability/metrics")
    assert unauthorized.status_code == 401

    headers = login_as_admin(client)
    authorized = client.get("/api/v2/observability/metrics", headers=headers)
    assert authorized.status_code == 200
    assert authorized.json()["database"] == "connected"
