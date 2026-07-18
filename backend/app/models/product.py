from datetime import datetime, timezone

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


class Product(Document):
    company_id: Indexed(PydanticObjectId)
    user_id: PydanticObjectId
    name: str
    description: str = ""
    category: str = ""
    price: float
    currency: str = "INR"
    quantity_available: int
    image_path: str | None = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "products"
