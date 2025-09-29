from pydantic import BaseModel, EmailStr
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    tenant_id: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthenticationRequest(BaseModel):
    token: str