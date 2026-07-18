from pydantic import BaseModel


class ExtractedCertificateData(BaseModel):
    certificate_type: str | None = None
    issuer: str | None = None
    issue_date: str | None = None
    expiry_date: str | None = None
    status: str | None = None
    holder_name: str | None = None
    holder_address: str | None = None
    business_activity: str | None = None
    has_official_seal: bool = False
