from datetime import datetime, timezone
from enum import Enum

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


class OrderStatus(str, Enum):
    placed = "placed"
    cancelled = "cancelled"


class Order(Document):
    product_id: Indexed(PydanticObjectId)
    product_name: str
    seller_company_id: Indexed(PydanticObjectId)
    buyer_user_id: Indexed(PydanticObjectId)
    quantity: int
    unit_price: float
    total_price: float
    currency: str = "INR"
    shipping_address: dict = Field(default_factory=dict)
    status: OrderStatus = OrderStatus.placed
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "orders"
