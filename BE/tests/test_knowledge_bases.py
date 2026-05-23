import time

from fastapi.testclient import TestClient


def test_knowledge_base_lifecycle(client: TestClient, auth_headers: dict):
  # 1. Create a knowledge base
  kb_payload = {
    "name": f"KB Test {int(time.time())}",
    "description": "Integration testing knowledge base description",
    "permission": "only_me",
    "indexing_technique": "high_quality",
  }
  response = client.post(
    "/api/v1/knowledge_bases", json=kb_payload, headers=auth_headers
  )
  assert response.status_code == 201, response.text
  created = response.json()
  assert "data" in created
  kb_data = created["data"]
  kb_id = kb_data["id"]
  assert kb_data["name"] == kb_payload["name"]

  # 2. Get knowledge base details
  get_res = client.get(f"/api/v1/knowledge_bases/{kb_id}", headers=auth_headers)
  assert get_res.status_code == 200, get_res.text
  details = get_res.json()["data"]
  assert details["id"] == kb_id

  # 3. Update knowledge base
  update_payload = {
    "name": f"KB Updated {int(time.time())}",
    "description": "Updated description",
  }
  update_res = client.patch(
    f"/api/v1/knowledge_bases/{kb_id}", json=update_payload, headers=auth_headers
  )
  assert update_res.status_code == 200, update_res.text
  updated_data = update_res.json()["data"]
  assert updated_data["name"] == update_payload["name"]

  # 4. List knowledge bases
  list_res = client.get("/api/v1/knowledge_bases", headers=auth_headers)
  assert list_res.status_code == 200, list_res.text
  kbs = list_res.json()["data"]["data"]
  assert any(k["id"] == kb_id for k in kbs)

  # 5. List documents in knowledge base (should be empty initially)
  docs_res = client.get(
    f"/api/v1/knowledge_bases/{kb_id}/documents", headers=auth_headers
  )
  assert docs_res.status_code == 200, docs_res.text
  docs_data = docs_res.json()["data"]
  assert docs_data["total"] == 0

  # 6. Delete knowledge base
  del_res = client.delete(f"/api/v1/knowledge_bases/{kb_id}", headers=auth_headers)
  assert del_res.status_code == 200, del_res.text
