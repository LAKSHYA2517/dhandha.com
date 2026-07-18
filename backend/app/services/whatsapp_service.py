import logging
import os
import secrets
import uuid
from datetime import datetime, timezone

import httpx

from app.ai_services.agent import evaluate_vendor_action
from app.ai_services.localization import localize_message, translate_to_english
from app.ai_services.multimodal import parse_document_image
from app.core.config import settings
from app.core.security import hash_password
from app.models.company import Company
from app.models.document import DocumentType
from app.models.product import Product
from app.models.user import User, UserRole
from app.models.whatsapp_session import WhatsAppSession
from app.services.document_compliance import (
    REQUIRED_DOC_LABELS,
    company_names_match,
    industry_matches,
    location_matches,
    match_document_type,
    parse_flexible_date,
)

logger = logging.getLogger(__name__)

GRAPH_BASE_URL = "https://graph.facebook.com"
PRODUCT_IMAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "products")

# WhatsApp interactive List Messages cap out at 10 selectable rows total, so
# this covers the 10 most widely-spoken languages in India rather than an
# exhaustive list.
LANGUAGE_OPTIONS = [
    {"id": "lang_en", "title": "English"},
    {"id": "lang_hi", "title": "Hindi · हिन्दी"},
    {"id": "lang_bn", "title": "Bengali · বাংলা"},
    {"id": "lang_te", "title": "Telugu · తెలుగు"},
    {"id": "lang_mr", "title": "Marathi · मराठी"},
    {"id": "lang_ta", "title": "Tamil · தமிழ்"},
    {"id": "lang_gu", "title": "Gujarati · ગુજરાતી"},
    {"id": "lang_ur", "title": "Urdu · اردو"},
    {"id": "lang_kn", "title": "Kannada · ಕನ್ನಡ"},
    {"id": "lang_ml", "title": "Malayalam · മലയാളം"},
]

ASK_FOR_PHOTO_MESSAGE = "Please send a photo of your compliance certificate and I'll process it for you."

# Full onboarding entirely over WhatsApp — no website visit required.
ASK_COMPANY_NAME_MESSAGE = "Let's get your business set up. What's the name of your company?"
ASK_COUNTRY_MESSAGE = "Which city and country is your company based in?"

# A fixed catalog (like LANGUAGE_OPTIONS) instead of free text — guarantees a
# clean, consistent English label gets stored regardless of chat language, and
# gives buyers a predictable set of industry lanes on the marketplace. Row
# titles are kept short: WhatsApp list rows cap out at 24 characters even
# before translation, and translated text tends to run longer than English.
INDUSTRY_OPTIONS = [
    {"id": "ind_agriculture", "title": "Agriculture & Food"},
    {"id": "ind_textiles", "title": "Textiles & Apparel"},
    {"id": "ind_electronics", "title": "Electronics & Tech"},
    {"id": "ind_logistics", "title": "Logistics & Transport"},
    {"id": "ind_manufacturing", "title": "Manufacturing"},
    {"id": "ind_chemicals", "title": "Chemicals & Pharma"},
    {"id": "ind_handicrafts", "title": "Handicrafts & Goods"},
]
INDUSTRY_LABELS_EN = {opt["id"]: opt["title"] for opt in INDUSTRY_OPTIONS}

_CHECKLIST_LINES = "\n".join(f"{i + 1}. {label}" for i, label in enumerate(REQUIRED_DOC_LABELS.values()))
DOCUMENT_CHECKLIST_MESSAGE = (
    "As per industry compliance standards, please send photos of the following documents one by one:\n\n"
    f"{_CHECKLIST_LINES}\n\n"
    "Send them one at a time whenever you're ready — I'll confirm each one and let you know what's still needed."
)

def _document_issues(extracted, company) -> list[str]:
    """Checks every aspect of an uploaded certificate independently (header/
    type, dates, stamp, holder identity, location, industry) and returns ALL
    problems found at once, rather than rejecting on the first mismatch — so
    the vendor gets one clear, complete list of exactly what to fix instead of
    discovering issues one round-trip at a time."""
    company_name = company.name
    issues = []

    matched_type = match_document_type(extracted.certificate_type or "")
    if matched_type == DocumentType.other:
        issues.append(
            "the certificate's title/header wasn't recognized as one of the required document types"
        )

    if not extracted.expiry_date:
        issues.append("no expiry/validity date is visible on the document")
    else:
        expiry = parse_flexible_date(extracted.expiry_date)
        if expiry is None:
            issues.append(f"the expiry date on the document (\"{extracted.expiry_date}\") isn't a readable date")
        elif expiry < datetime.now(timezone.utc):
            issues.append(f"this document expired on {extracted.expiry_date} — it's no longer valid")

    if not extracted.has_official_seal:
        issues.append("no official stamp or seal from the issuing authority is visible on the document")

    if not company_names_match(company_name, extracted.holder_name):
        holder = extracted.holder_name or "no company name"
        issues.append(f"the certificate is issued to \"{holder}\", not your registered company \"{company_name}\"")

    if not location_matches(company.country, extracted.holder_address):
        issues.append(
            f"the certificate's address doesn't appear to match your registered location \"{company.country}\""
        )

    # Not every required document states a trade/business scope (a tax
    # compliance certificate typically doesn't) — only flag this when the
    # document actually states an activity that conflicts, rather than
    # penalizing documents that simply don't carry that field.
    if extracted.business_activity and not industry_matches(company.industry, extracted.business_activity):
        issues.append(
            f"the certificate's business activity doesn't appear to match your registered industry "
            f"\"{company.industry}\""
        )

    return issues


def _document_rejection_message(issues: list[str]) -> str:
    issue_lines = "\n".join(f"- {issue}" for issue in issues)
    return (
        "❌ I couldn't accept this document for the following reason(s):\n\n"
        f"{issue_lines}\n\n"
        "Please re-upload a clear photo of a genuine, current certificate issued to your company, showing "
        "the issuing authority's official stamp/seal and a valid expiry date. Required documents:\n\n"
        f"{_CHECKLIST_LINES}"
    )


ASK_PRODUCT_NAME_MESSAGE = "🎉 Your compliance profile is complete! Let's list your first product. What's the product name?"
ASK_PRODUCT_QUANTITY_MESSAGE = "How many units do you have available? (just the number)"
ASK_PRODUCT_PRICE_MESSAGE = "What's the price per unit? (just the number, e.g. 250)"
ASK_PRODUCT_DESCRIPTION_MESSAGE = "Any description for the product? (optional — reply 'skip' if none)"
ASK_PRODUCT_PHOTO_MESSAGE = "Last step — please send a photo of the product."
PRODUCT_LISTED_MESSAGE = "✅ Your product is listed with its photo! Buyers can now find it on the Dhandha.com marketplace."

SKIP_WORDS = {"skip", "none", "n/a", "na", "no", "no thanks", "nothing"}

# WhatsApp gives no signal when a user clears their chat locally on their
# phone — that's purely client-side and never reaches our webhook. These
# explicit words always force a reset, from anywhere in the conversation.
EXPLICIT_RESET_KEYWORDS = {"restart", "reset", "start over"}

# Greeting words only reset the session when it's idle (nothing in progress) —
# otherwise a casual "hi" typed mid-conversation (very common even when
# chatting in another language) would wipe onboarding/document/product
# progress and re-ask for language, which is the exact bug this guards against.
GREETING_KEYWORDS = {"hi", "hello", "hey", "hii", "hiii"}
IDLE_STAGES = {"done"}


def _auth_headers() -> dict:
    if not settings.whatsapp_access_token or not settings.whatsapp_phone_number_id:
        raise ValueError(
            "WHATSAPP_ACCESS_TOKEN / WHATSAPP_PHONE_NUMBER_ID are not configured in backend/.env"
        )
    return {"Authorization": f"Bearer {settings.whatsapp_access_token}"}


async def download_whatsapp_media(media_id: str) -> tuple[bytes, str]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        meta_response = await client.get(
            f"{GRAPH_BASE_URL}/{settings.whatsapp_api_version}/{media_id}",
            headers=_auth_headers(),
        )
        meta_response.raise_for_status()
        media_info = meta_response.json()

        media_url = media_info["url"]
        mime_type = media_info.get("mime_type", "image/jpeg")

        media_response = await client.get(media_url, headers=_auth_headers())
        media_response.raise_for_status()

        return media_response.content, mime_type


async def send_whatsapp_message(to_number: str, text: str) -> None:
    url = f"{GRAPH_BASE_URL}/{settings.whatsapp_api_version}/{settings.whatsapp_phone_number_id}/messages"
    body = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": text},
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, headers={**_auth_headers(), "Content-Type": "application/json"}, json=body)
        response.raise_for_status()


async def send_language_selector(to_number: str) -> None:
    url = f"{GRAPH_BASE_URL}/{settings.whatsapp_api_version}/{settings.whatsapp_phone_number_id}/messages"
    body = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "Welcome to Dhandha.com"},
            "body": {"text": "I'm your compliance assistant. Please choose the language you'd like to chat in:"},
            "footer": {"text": "We'll keep using this language for the rest of our chat"},
            "action": {
                "button": "Select Language",
                "sections": [{"title": "Languages", "rows": LANGUAGE_OPTIONS}],
            },
        },
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, headers={**_auth_headers(), "Content-Type": "application/json"}, json=body)
        response.raise_for_status()


async def send_industry_selector(to_number: str, language: str) -> None:
    url = f"{GRAPH_BASE_URL}/{settings.whatsapp_api_version}/{settings.whatsapp_phone_number_id}/messages"
    rows = [
        {"id": opt["id"], "title": (await localize_message(opt["title"], language))[:24]}
        for opt in INDUSTRY_OPTIONS
    ]
    body = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "Business Industry"},
            "body": {"text": await localize_message("Which industry best describes your business?", language)},
            "footer": {"text": "Choose one to continue"},
            "action": {
                "button": (await localize_message("Select Industry", language))[:20],
                "sections": [{"title": "Industries", "rows": rows}],
            },
        },
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, headers={**_auth_headers(), "Content-Type": "application/json"}, json=body)
        response.raise_for_status()


def _extract_message(payload: dict) -> dict | None:
    try:
        value = payload["entry"][0]["changes"][0]["value"]
        messages = value.get("messages")
        return messages[0] if messages else None
    except (KeyError, IndexError, TypeError):
        return None


def _extract_list_reply_title(message: dict) -> str | None:
    interactive = message.get("interactive")
    if interactive and interactive.get("type") == "list_reply":
        return interactive.get("list_reply", {}).get("title")
    return None


def _extract_list_reply_id(message: dict) -> str | None:
    interactive = message.get("interactive")
    if interactive and interactive.get("type") == "list_reply":
        return interactive.get("list_reply", {}).get("id")
    return None


def _text_body(message: dict) -> str:
    return (message.get("text", {}).get("body") or "").strip()


async def _get_or_create_session(phone_number: str) -> tuple[WhatsAppSession, bool]:
    session = await WhatsAppSession.find_one(WhatsAppSession.phone_number == phone_number)
    if session:
        return session, False

    session = WhatsAppSession(phone_number=phone_number)
    await session.insert()
    return session, True


async def _create_vendor_account(phone_number: str, company_name: str, country: str, industry: str) -> Company:
    """Creates a shadow User (reused across cycles) + a fresh Company (one per
    onboarding cycle) entirely from WhatsApp chat answers — no website visit
    or password needed. Demo requirement: the same phone number can run
    through onboarding repeatedly and accumulate multiple company profiles."""
    email = f"whatsapp-{phone_number}@vendors.dhandha.com"

    user = await User.find_one(User.email == email)
    if not user:
        user = User(
            name=company_name,
            email=email,
            password=hash_password(secrets.token_urlsafe(24)),
            role=UserRole.seller,
        )
        await user.insert()

    company = Company(
        user_id=user.id,
        name=company_name,
        country=country,
        industry=industry,
        trade_category=industry,
        whatsapp_number=phone_number,
    )
    await company.insert()

    return company


async def process_whatsapp_message(payload: dict) -> None:
    try:
        message = _extract_message(payload)
        if not message:
            return  # status callback or other non-message event — nothing to do

        sender_number = message.get("from")
        message_type = message.get("type")
        message_id = message.get("id")

        session, is_new = await _get_or_create_session(sender_number)

        if is_new:
            # Brand-new number's very first message — always start with language selection.
            await send_language_selector(sender_number)
            return

        if message_id and message_id == session.last_message_id:
            # Exact redelivery of the message we just handled — skip it
            # rather than reprocess (see last_message_id's docstring).
            return
        if message_id:
            await session.set({"last_message_id": message_id})

        text_lower = _text_body(message).lower() if message_type == "text" else ""
        is_explicit_reset = text_lower in EXPLICIT_RESET_KEYWORDS
        is_idle_greeting = text_lower in GREETING_KEYWORDS and session.stage in IDLE_STAGES

        if is_explicit_reset or is_idle_greeting:
            await session.delete()
            await WhatsAppSession(phone_number=sender_number).insert()
            await send_language_selector(sender_number)
            return

        if session.stage == "awaiting_language":
            chosen_language = _extract_list_reply_title(message)
            if not chosen_language:
                # They typed instead of picking from the list — re-send the
                # selector rather than accept arbitrary free-text input.
                await send_language_selector(sender_number)
                return

            await session.set({
                "language": chosen_language,
                "stage": "awaiting_company_name",
                "updated_at": datetime.now(timezone.utc),
            })
            greeting = (
                f"👋 Hello! I'll be chatting with you in {chosen_language} from here on. "
                f"{ASK_COMPANY_NAME_MESSAGE}"
            )
            await send_whatsapp_message(sender_number, await localize_message(greeting, chosen_language))
            return

        language = session.language or "English"

        if session.stage == "awaiting_company_name":
            company_name = _text_body(message)
            if not company_name:
                await send_whatsapp_message(sender_number, await localize_message(ASK_COMPANY_NAME_MESSAGE, language))
                return

            # The website is English-only regardless of chat language, so
            # anything persisted for display there gets translated on the way in.
            company_name_en = await translate_to_english(company_name, language)

            await session.set({
                "pending_company_name": company_name_en,
                "stage": "awaiting_country",
                "updated_at": datetime.now(timezone.utc),
            })
            await send_whatsapp_message(sender_number, await localize_message(ASK_COUNTRY_MESSAGE, language))
            return

        if session.stage == "awaiting_country":
            country = _text_body(message)
            if not country:
                await send_whatsapp_message(sender_number, await localize_message(ASK_COUNTRY_MESSAGE, language))
                return

            country_en = await translate_to_english(country, language)

            await session.set({
                "pending_country": country_en,
                "stage": "awaiting_industry",
                "updated_at": datetime.now(timezone.utc),
            })
            await send_industry_selector(sender_number, language)
            return

        if session.stage == "awaiting_industry":
            selected_id = _extract_list_reply_id(message)
            if not selected_id or selected_id not in INDUSTRY_LABELS_EN:
                # They typed instead of picking from the list — re-send the
                # selector rather than accept arbitrary free-text input.
                await send_industry_selector(sender_number, language)
                return

            industry = INDUSTRY_LABELS_EN[selected_id]

            company = await _create_vendor_account(
                sender_number, session.pending_company_name, session.pending_country, industry
            )
            await session.set({
                "stage": "collecting_documents",
                "active_company_id": company.id,
                "updated_at": datetime.now(timezone.utc),
            })

            done_message = f"✅ You're all set up, {session.pending_company_name}!\n\n{DOCUMENT_CHECKLIST_MESSAGE}"
            await send_whatsapp_message(sender_number, await localize_message(done_message, language))
            return

        if session.stage == "collecting_documents":
            if message_type == "image":
                media_id = message["image"]["id"]
                image_bytes, mime_type = await download_whatsapp_media(media_id)
                extracted = await parse_document_image(image_bytes, mime_type)

                if not session.active_company_id:
                    # Shouldn't normally happen — onboarding guarantees a
                    # linked company before this stage. Defensive fallback for
                    # a corrupted/manually-edited session record.
                    await WhatsAppSession.find(WhatsAppSession.phone_number == sender_number).delete()
                    await send_language_selector(sender_number)
                    return

                company = await Company.get(session.active_company_id)
                if not company:
                    # The linked company was deleted/corrupted — same
                    # defensive fallback as a missing active_company_id.
                    await WhatsAppSession.find(WhatsAppSession.phone_number == sender_number).delete()
                    await send_language_selector(sender_number)
                    return

                issues = _document_issues(extracted, company)
                if issues:
                    # Report every problem found at once (wrong type, missing/
                    # expired date, no stamp, wrong company) instead of
                    # rejecting on the first mismatch — one clear round-trip
                    # instead of several. Tracked so the RCI engine's
                    # Authenticity Score can tell a clean first-try upload
                    # apart from one that needed several attempts.
                    await session.set({"current_doc_rejection_count": session.current_doc_rejection_count + 1})
                    await send_whatsapp_message(
                        sender_number, await localize_message(_document_rejection_message(issues), language)
                    )
                    return

                uploaded_cleanly = session.current_doc_rejection_count == 0
                await session.set({"current_doc_rejection_count": 0})

                action = await evaluate_vendor_action(
                    str(session.active_company_id), extracted.model_dump(), language, uploaded_cleanly
                )
                if action["action"] == "requested_document":
                    await send_whatsapp_message(sender_number, action["message"])
                else:
                    await session.set({"stage": "awaiting_product_name", "updated_at": datetime.now(timezone.utc)})
                    await send_whatsapp_message(
                        sender_number, await localize_message(ASK_PRODUCT_NAME_MESSAGE, language)
                    )
            elif message_type == "text":
                await send_whatsapp_message(sender_number, await localize_message(ASK_FOR_PHOTO_MESSAGE, language))
            return

        if session.stage == "awaiting_product_name":
            product_name = _text_body(message)
            if not product_name:
                await send_whatsapp_message(sender_number, await localize_message(ASK_PRODUCT_NAME_MESSAGE, language))
                return

            product_name = await translate_to_english(product_name, language)

            await session.set({
                "pending_product_name": product_name,
                "stage": "awaiting_product_quantity",
                "updated_at": datetime.now(timezone.utc),
            })
            await send_whatsapp_message(sender_number, await localize_message(ASK_PRODUCT_QUANTITY_MESSAGE, language))
            return

        if session.stage == "awaiting_product_quantity":
            try:
                quantity = int(_text_body(message))
                if quantity < 0:
                    raise ValueError
            except ValueError:
                await send_whatsapp_message(
                    sender_number, await localize_message(ASK_PRODUCT_QUANTITY_MESSAGE, language)
                )
                return

            await session.set({
                "pending_product_quantity": quantity,
                "stage": "awaiting_product_price",
                "updated_at": datetime.now(timezone.utc),
            })
            await send_whatsapp_message(sender_number, await localize_message(ASK_PRODUCT_PRICE_MESSAGE, language))
            return

        if session.stage == "awaiting_product_price":
            try:
                price = float(_text_body(message))
                if price <= 0:
                    raise ValueError
            except ValueError:
                await send_whatsapp_message(sender_number, await localize_message(ASK_PRODUCT_PRICE_MESSAGE, language))
                return

            await session.set({
                "pending_product_price": price,
                "stage": "awaiting_product_description",
                "updated_at": datetime.now(timezone.utc),
            })
            await send_whatsapp_message(
                sender_number, await localize_message(ASK_PRODUCT_DESCRIPTION_MESSAGE, language)
            )
            return

        if session.stage == "awaiting_product_description":
            raw_description = _text_body(message)
            if raw_description.lower() in SKIP_WORDS:
                description = ""
            else:
                description = await translate_to_english(raw_description, language)

            await session.set({
                "pending_product_description": description,
                "stage": "awaiting_product_photo",
                "updated_at": datetime.now(timezone.utc),
            })
            await send_whatsapp_message(sender_number, await localize_message(ASK_PRODUCT_PHOTO_MESSAGE, language))
            return

        if session.stage == "awaiting_product_photo":
            if message_type != "image":
                await send_whatsapp_message(sender_number, await localize_message(ASK_PRODUCT_PHOTO_MESSAGE, language))
                return

            media_id = message["image"]["id"]
            image_bytes, mime_type = await download_whatsapp_media(media_id)
            ext = ".jpg" if "jpeg" in mime_type or "jpg" in mime_type else ".png"
            os.makedirs(PRODUCT_IMAGE_DIR, exist_ok=True)
            file_name = f"{uuid.uuid4().hex}{ext}"
            with open(os.path.join(PRODUCT_IMAGE_DIR, file_name), "wb") as f:
                f.write(image_bytes)

            company = await Company.get(session.active_company_id)
            product = Product(
                company_id=session.active_company_id,
                user_id=company.user_id,
                name=session.pending_product_name,
                description=session.pending_product_description or "",
                price=session.pending_product_price,
                quantity_available=session.pending_product_quantity,
                image_path=f"products/{file_name}",
            )
            await product.insert()

            await session.set({
                "stage": "done",
                "pending_product_name": None,
                "pending_product_quantity": None,
                "pending_product_price": None,
                "pending_product_description": None,
                "updated_at": datetime.now(timezone.utc),
            })
            await send_whatsapp_message(sender_number, await localize_message(PRODUCT_LISTED_MESSAGE, language))
            return

        # stage == "done" — everything set up; nudge toward the reset keyword.
        if message_type == "text":
            done_reply = "You're all set! Type 'restart' anytime to set up another company."
            await send_whatsapp_message(sender_number, await localize_message(done_reply, language))

    except Exception:
        logger.exception("Failed to process incoming WhatsApp message")
