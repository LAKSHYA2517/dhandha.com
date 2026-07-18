from datetime import datetime, timezone

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


class WhatsAppSession(Document):
    # Stages: awaiting_language -> awaiting_company_name -> awaiting_country
    # -> awaiting_industry -> collecting_documents -> awaiting_product_name ->
    # awaiting_product_quantity -> awaiting_product_price ->
    # awaiting_product_description -> awaiting_product_photo -> done
    #
    # Every onboarding cycle creates a fresh Company (demo requirement: the
    # same phone number can run through onboarding repeatedly and accumulate
    # multiple company profiles). active_company_id is the one THIS
    # conversation is currently working with — document/product actions
    # always route to it, never to an ambiguous "find by phone number" lookup.
    phone_number: Indexed(str, unique=True)
    # WhatsApp's webhook delivery is at-least-once — the same message can
    # arrive more than once (network retries, redelivery). Without this, a
    # duplicate delivery mid-conversation gets processed twice, which can look
    # to the user like the conversation jumped backward or repeated itself.
    last_message_id: str | None = None
    # Counts consecutive rejected upload attempts for whichever document is
    # currently being submitted; reset to 0 once one is accepted. Lets the RCI
    # engine's Authenticity Score distinguish a vendor whose documents passed
    # verification cleanly from one who needed several retries.
    current_doc_rejection_count: int = 0
    stage: str = "awaiting_language"
    language: str | None = None
    active_company_id: PydanticObjectId | None = None
    pending_company_name: str | None = None
    pending_country: str | None = None
    pending_product_name: str | None = None
    pending_product_quantity: int | None = None
    pending_product_price: float | None = None
    pending_product_description: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "whatsapp_sessions"
