from pydantic import BaseModel, EmailStr, Field
from uuid import UUID


class RegisterRequest(BaseModel):
	email: EmailStr
	password: str
	tenant_id: UUID | None = None
	role: str = Field(default="user", description="User role in system")


class LoginRequest(BaseModel):
	email: EmailStr = Field(default="canhphong6868@gmail.com", description="User's email address")
	password: str = Field(default="123456", description="User's password")


from datetime import datetime

class User(BaseModel):
  id: UUID
  email: EmailStr
  role: str
  created_at: datetime
  updated_at: datetime | None = None

  class Config:
    from_attributes = True

class AuthenticationRequest(BaseModel):
  token: str
