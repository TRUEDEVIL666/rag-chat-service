from fastapi.testclient import TestClient


def test_get_all_tenants(client: TestClient, auth_headers: dict):
  response = client.get("/api/v1/tenants", headers=auth_headers)
  assert response.status_code == 200
  tenants = response.json()
  assert isinstance(tenants, list)
  if len(tenants) > 0:
    assert "id" in tenants[0]
    assert "name" in tenants[0]
