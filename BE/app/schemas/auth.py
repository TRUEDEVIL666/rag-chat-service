from datetime import datetime
from pydantic import BaseModel, EmailStr
from uuid import UUID
from fastapi import Path, Query


class RegisterRequest(BaseModel):
  email: EmailStr
  name: str
  password: str
  tenant_id: UUID | None = None
  role: str | None = None


class LoginRequest(BaseModel):
  email: EmailStr
  password: str


class User(BaseModel):
  id: UUID
  tenant_id: UUID | None = None
  email: EmailStr
  name: str | None = None
  role: str
  created_at: datetime
  updated_at: datetime | None = None

  class Config:
    from_attributes = True


class AuthenticationRequest(BaseModel):
  token: str


class UserIdRequest(BaseModel):
  user_id: UUID = Path(..., description="User ID")
