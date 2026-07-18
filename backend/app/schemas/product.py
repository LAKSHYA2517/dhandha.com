from pydantic import BaseModel, Field


class ProductCreateRequest(BaseModel):
    name: str
    description: str = ""
    category: str = ""
    price: float = Field(gt=0)
    currency: str = "INR"
    quantity_available: int = Field(ge=0)


class ProductUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    price: float | None = Field(default=None, gt=0)
    currency: str | None = None
    quantity_available: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class ShippingAddress(BaseModel):
    full_name: str
    phone: str
    address_line1: str
    address_line2: str = ""
    city: str
    state: str
    postal_code: str
    country: str


class OrderCreateRequest(BaseModel):
    quantity: int = Field(gt=0)
    shipping_address: ShippingAddress
