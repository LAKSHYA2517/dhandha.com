from datetime import datetime, timezone
from enum import Enum

from beanie import Document
from pydantic import EmailStr, Field


class UserRole(str, Enum):
    buyer = "buyer"
    seller = "seller"
    admin = "admin"


class User(Document):
    name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.buyer
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"
