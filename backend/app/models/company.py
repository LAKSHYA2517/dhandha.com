from datetime import datetime, timezone

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


class Company(Document):
    user_id: Indexed(PydanticObjectId)
    name: str
    country: str
    industry: str
    trade_category: str
    description: str = ""
    contact_email: str = ""
    website: str = ""
    rci_score: float | None = None
    compliance_status: bool = False
    current_rci_score: float | None = None
    rci_breakdown: dict = Field(default_factory=dict)
    latest_ai_explanation: str | None = None
    whatsapp_number: Indexed(str) | None = None
    rci_subcomponents: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "companies"
