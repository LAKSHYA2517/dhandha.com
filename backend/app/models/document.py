from datetime import datetime, timezone
from enum import Enum

from beanie import Document as BeanieDocument, Indexed, PydanticObjectId
from pydantic import Field


class DocumentType(str, Enum):
    trade_license = "trade_license"
    iso_certificate = "iso_certificate"
    tax_compliance = "tax_compliance"
    export_permit = "export_permit"
    quality_cert = "quality_cert"
    other = "other"


class ComplianceDocument(BeanieDocument):
    company_id: Indexed(PydanticObjectId)
    user_id: PydanticObjectId
    type: DocumentType
    file_name: str
    original_name: str
    mime_type: str | None = None
    file_size: int | None = None
    issuing_authority: str = "Simulated Authority"
    issue_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expiry_date: datetime
    is_valid: bool = True
    # Was this document accepted on its first upload attempt, with no prior
    # seal/identity/type rejections in this cycle? Feeds the RCI engine's
    # Authenticity Score (AS) — a vendor whose paperwork sailed through
    # verification scores higher than one who needed several retries.
    uploaded_cleanly: bool = True
    extracted_data: dict = Field(default_factory=dict)
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "documents"
