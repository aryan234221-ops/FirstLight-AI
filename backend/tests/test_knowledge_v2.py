from __future__ import annotations

from conftest import login_as_admin


def test_knowledge_upload_list_search_delete_reindex(client):
    headers = login_as_admin(client)
    project_id = "fl-knowledge-test"

    upload_response = client.post(
        f"/api/v2/projects/{project_id}/knowledge/upload",
        headers={"Authorization": headers["Authorization"]},
        files={"file": ("notes.md", b"launch readiness and architecture", "text/markdown")},
    )
    assert upload_response.status_code == 201
    payload = upload_response.json()
    assert payload["version"] >= 1
    document_id = payload["id"]

    list_response = client.get(
        f"/api/v2/projects/{project_id}/knowledge",
        headers={"Authorization": headers["Authorization"]},
    )
    assert list_response.status_code == 200
    listed = list_response.json()
    assert len(listed) >= 1

    search_response = client.post(
        f"/api/v2/projects/{project_id}/knowledge/search",
        headers=headers,
        json={"query": "architecture", "top_k": 5},
    )
    assert search_response.status_code == 200
    assert search_response.json()["count"] >= 1

    reindex_response = client.post(
        f"/api/v2/projects/{project_id}/knowledge/{document_id}/reindex",
        headers=headers,
    )
    assert reindex_response.status_code == 200
    assert reindex_response.json()["status"] == "indexed"

    delete_response = client.delete(
        f"/api/v2/projects/{project_id}/knowledge/{document_id}",
        headers={"Authorization": headers["Authorization"]},
    )
    assert delete_response.status_code == 204
