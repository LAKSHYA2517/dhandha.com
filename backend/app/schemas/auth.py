from beanie import PydanticObjectId
from pydantic import BaseModel, EmailStr

from app.models.user import UserRole


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.buyer


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: PydanticObjectId
    name: str
    email: EmailStr
    role: UserRole


class AuthResponse(BaseModel):
    success: bool = True
    message: str | None = None
    token: str
    user: UserOut
