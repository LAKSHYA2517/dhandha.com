from pydantic import BaseModel

from app.schemas.rci import RCISubcomponents


class RunComplianceRequest(BaseModel):
    subcomponents: RCISubcomponents
    vendor_data: dict
    trade_route: str


class CompanyCreateRequest(BaseModel):
    name: str
    country: str
    industry: str
    trade_category: str
    description: str = ""
    contact_email: str = ""
    website: str = ""
    whatsapp_number: str | None = None


class CompanyUpdateRequest(BaseModel):
    name: str | None = None
    country: str | None = None
    industry: str | None = None
    trade_category: str | None = None
    description: str | None = None
    contact_email: str | None = None
    website: str | None = None
    whatsapp_number: str | None = None
