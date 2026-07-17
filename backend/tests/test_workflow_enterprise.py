from __future__ import annotations

from conftest import login_as_admin


def test_workflow_run_approval_and_history(client):
    headers = login_as_admin(client)
    create_response = client.post(
        "/api/v2/workflows/runs",
        headers=headers,
        json={"project_id": "fl-wf-test", "goal": "Build release checklist"},
    )
    assert create_response.status_code == 201
    payload = create_response.json()
    run_id = payload["run"]["run_id"]

    approval_response = client.post(
        f"/api/v2/workflows/runs/{run_id}/approval",
        headers=headers,
        json={"action": "reject", "comment": "Need updates"},
    )
    assert approval_response.status_code == 200
    assert approval_response.json()["status"] == "rejected"

    detail_response = client.get(f"/api/v2/workflows/runs/{run_id}", headers=headers)
    assert detail_response.status_code == 200

    history_response = client.get("/api/v2/workflow-history", headers=headers)
    assert history_response.status_code == 200
