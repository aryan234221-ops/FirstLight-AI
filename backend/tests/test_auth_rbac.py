from __future__ import annotations

from conftest import login_as_admin


def test_auth_login_refresh_logout_flow(client):
    login_response = client.post(
        "/api/v2/auth/login",
        json={"username": "admin", "password": "ChangeMeNow123!"},
    )
    assert login_response.status_code == 200
    payload = login_response.json()
    assert payload["access_token"]
    assert payload["refresh_token"]

    refresh_response = client.post(
        "/api/v2/auth/refresh",
        json={"refresh_token": payload["refresh_token"]},
    )
    assert refresh_response.status_code == 200
    refreshed = refresh_response.json()
    assert refreshed["access_token"]
    assert refreshed["refresh_token"]

    me_response = client.get(
        "/api/v2/auth/me",
        headers={"Authorization": f"Bearer {refreshed['access_token']}"},
    )
    assert me_response.status_code == 200
    me_payload = me_response.json()
    assert me_payload["username"] == "admin"

    logout_response = client.post(
        "/api/v2/auth/logout",
        json={"refresh_token": refreshed["refresh_token"]},
    )
    assert logout_response.status_code == 204


def test_rbac_dashboard_requires_auth(client):
    response = client.get("/api/v2/dashboard/overview")
    assert response.status_code == 401

    headers = login_as_admin(client)
    authorized = client.get("/api/v2/dashboard/overview", headers=headers)
    assert authorized.status_code == 200
