from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def _test_env() -> None:
    os.environ.setdefault("FIRSTLIGHT_JWT_SECRET", "test-secret")


@pytest.fixture
def client() -> TestClient:
    from app.main import app

    return TestClient(app)


def login_as_admin(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v2/auth/login",
        json={"username": "admin", "password": "ChangeMeNow123!"},
    )
    assert response.status_code == 200
    payload = response.json()
    return {
        "Authorization": f"Bearer {payload['access_token']}",
        "Content-Type": "application/json",
    }
