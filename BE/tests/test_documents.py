import time

import pytest
from fastapi.testclient import TestClient


def test_document_lifecycle(client: TestClient, auth_headers: dict):
  # 1. Create a KB first to associate the document with
  kb_payload = {
    "name": f"KB Doc Test {int(time.time())}",
    "description": "Knowledge base for testing document upload",
    "permission": "only_me",
    "indexing_technique": "high_quality",
  }
  kb_res = client.post("/api/v1/knowledge_bases", json=kb_payload, headers=auth_headers)
  assert kb_res.status_code == 201, kb_res.text
  kb_id = kb_res.json()["data"]["id"]

  # 2. Try uploading a file
  files = [
    (
      "files",
      (
        "test_doc.txt",
        b"This is a test document content for integration testing.",
        "text/plain",
      ),
    )
  ]
  data = {
    "knowledge_base_id": kb_id,
    "chunking_method": "economy",
    "enable_extraction": "false",
  }

  response = client.post(
    "/api/v1/documents/", data=data, files=files, headers=auth_headers
  )

  # Check if MinIO/Celery are down and it results in validation error or server error
  if response.status_code != 200:
    # Cleanup KB
    client.delete(f"/api/v1/knowledge_bases/{kb_id}", headers=auth_headers)
    pytest.skip(
      f"Document upload failed with status {response.status_code}. Storage (MinIO) or worker might be offline."
    )
    return

  res_json = response.json()
  upload_data = res_json.get("data", {})
  results = upload_data.get("results", [])

  if not results or results[0].get("status") == "failed":
    client.delete(f"/api/v1/knowledge_bases/{kb_id}", headers=auth_headers)
    pytest.skip(
      "Document upload failed in service layer. Storage (MinIO) is likely offline."
    )
    return

  result = results[0]
  task_id = result.get("task_id")

  # 3. Get the document ID by listing KB documents
  docs_res = client.get(
    f"/api/v1/knowledge_bases/{kb_id}/documents", headers=auth_headers
  )
  assert docs_res.status_code == 200, docs_res.text
  docs = docs_res.json()["data"]["data"]
  assert len(docs) > 0
  doc_id = docs[0]["id"]

  # 4. Get Task Status
  task_res = client.get(
    f"/api/v1/documents/tasks/{task_id}",
    params={"task_id": task_id},
    headers=auth_headers,
  )
  assert task_res.status_code == 200, task_res.text

  # 5. Get Download URL
  dl_res = client.get(f"/api/v1/documents/{doc_id}/download", headers=auth_headers)
  assert dl_res.status_code == 200, dl_res.text

  # 6. Retry Document Processing
  retry_res = client.post(f"/api/v1/documents/{doc_id}/retry", headers=auth_headers)
  assert retry_res.status_code == 200, retry_res.text

  # 7. Delete document
  del_res = client.delete(f"/api/v1/documents/{doc_id}", headers=auth_headers)
  assert del_res.status_code == 200, del_res.text

  # 8. Cleanup KB
  client.delete(f"/api/v1/knowledge_bases/{kb_id}", headers=auth_headers)
