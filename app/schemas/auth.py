from pydantic import BaseModel, EmailStr
from uuid import UUID

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    tenant_id: UUID


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthenticationRequest(BaseModel):
    token: str