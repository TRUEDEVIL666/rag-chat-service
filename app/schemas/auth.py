from pydantic import BaseModel, EmailStr, Field
from uuid import UUID


class RegisterRequest(BaseModel):
	email: EmailStr
	password: str
	tenant_id: UUID


class LoginRequest(BaseModel):
	email: EmailStr = Field(default="canhphong6868@gmail.com", description="User's email address")
	password: str = Field(default="123456", description="User's password")


class AuthenticationRequest(BaseModel):
	token: str
