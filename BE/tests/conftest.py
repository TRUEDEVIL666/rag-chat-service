import asyncio
import csv
import os
import sys

if sys.platform == "win32":
  asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import pytest
from fastapi.testclient import TestClient

from app.services import AuthService
from main import app


@pytest.fixture(scope="session")
def client():
  with TestClient(app) as c:
    yield c


@pytest.fixture(scope="session")
def auth_headers():
  try:
    loop = asyncio.get_event_loop()
  except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
  return loop.run_until_complete(get_or_create_auth_headers())


async def get_or_create_auth_headers():
  csv_path = os.path.join(os.path.dirname(__file__), "..", "..", "test_users.csv")
  email = "batch_tester_08@example.com"
  password = "SecurePass123!"
  name = "Batch Tester Eight"
  tenant_id = "4d8cd271-a065-4c9d-bde0-1a2d210a7187"
  role = "admin"

  if os.path.exists(csv_path):
    with open(csv_path, mode="r", encoding="utf-8") as f:
      reader = csv.DictReader(f)
      for row in reader:
        if row.get("role") == "admin":
          email = row.get("email")
          password = row.get("password")
          name = row.get("name")
          tenant_id = row.get("tenant_id")
          break

  from sqlalchemy import text

  from app.core.database import postgres_engine

  engine = await postgres_engine.get_engine()
  async with engine._pool.begin() as conn:
    # Check if tenant exists
    res = await conn.execute(
      text("SELECT id FROM tenants WHERE id = :tenant_id"), {"tenant_id": tenant_id}
    )
    row = res.fetchone()
    if not row:
      # Check if any tenant exists to reuse
      res_any = await conn.execute(text("SELECT id FROM tenants LIMIT 1"))
      row_any = res_any.fetchone()
      if row_any:
        tenant_id = str(row_any[0])
      else:
        # Create a new tenant directly in the database to bypass RLS policies
        await conn.execute(
          text("INSERT INTO tenants (id, name) VALUES (:tenant_id, :name)"),
          {"tenant_id": tenant_id, "name": "Test Tenant"},
        )

  auth_service = AuthService.get_instance()
  try:
    result = await auth_service.sign_in_with_password(email=email, password=password)
    token = result.get("token")
  except Exception:
    try:
      await auth_service.sign_up(
        email=email, password=password, name=name, tenant_id=tenant_id, role=role
      )
    except Exception:
      pass

    result = await auth_service.sign_in_with_password(email=email, password=password)
    token = result.get("token")

  return {"Authorization": f"Bearer {token}"}
