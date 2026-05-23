import time

from fastapi.testclient import TestClient


def test_user_lifecycle_as_admin(client: TestClient, auth_headers: dict):
  unique_email = f"user_lifecycle_{int(time.time())}@example.com"
  password = "SecurePass123!"
  name = "Lifecycle Test User"

  # 1. Create a user via Admin endpoint
  create_payload = {
    "email": unique_email,
    "name": name,
    "password": password,
    "role": "user",
  }
  response = client.post("/api/v1/users", json=create_payload, headers=auth_headers)
  assert response.status_code == 200, response.text
  assert "User created successfully" in response.json().get("data", {}).get(
    "message", ""
  )

  # 2. List all users and verify the created user is in the list
  list_response = client.get("/api/v1/users", headers=auth_headers)
  assert list_response.status_code == 200, list_response.text
  users_data = list_response.json().get("data", {}).get("items", [])
  found_user = None
  for u in users_data:
    if u.get("email") == unique_email:
      found_user = u
      break
  assert found_user is not None
  user_id = found_user.get("id")

  # 3. Clean up (delete the user)
  delete_response = client.delete(f"/api/v1/users/{user_id}", headers=auth_headers)
  assert delete_response.status_code == 204
