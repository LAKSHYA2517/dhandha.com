import logging
from datetime import datetime, timezone

from beanie import PydanticObjectId

from app.ai_services.localization import localize_message
from app.core.config import settings
from app.core.llm import generate_content_with_retry
from app.core.rci_engine import calculate_rci
from app.models.company import Company
from app.models.document import ComplianceDocument, DocumentType
from app.schemas.rci import RCISubcomponents
from app.services.document_compliance import (
    REQUIRED_DOC_LABELS,
    REQUIRED_DOCUMENT_TYPES,
    calculate_as,
    calculate_cs,
    calculate_dc,
    calculate_dv,
    match_document_type,
    missing_required_types,
    parse_flexible_date,
)

logger = logging.getLogger(__name__)

# Neutral baseline used only the first time a company goes through the agentic
# loop without ever having run Phase 3's /run-compliance. DC gets overwritten
# immediately below; the rest stay as placeholders until a real assessment
# (manual or Gemma-scored) supplies better values.
DEFAULT_SUBCOMPONENTS = {
    "core": {"AS": 0.5, "DC": 0.5, "RF": 0.5, "CS": 0.5, "PC": 0.5},
    "external": {"CR": 0.5, "TLR": 0.5, "MSP": 1.0, "CI": 0.5},
    "operational": {"LR": 0.5, "CCP": 0.5},
    "macro": {"FH": 0.5, "FB": 0.5, "DV": 0.5},
}

AGENT_DRAFT_PROMPT = """Act as a helpful B2B compliance assistant. The vendor just sent their {received_doc}. \
They still need to send: {missing_docs}. Draft a short, friendly WhatsApp message (max 3 sentences) in English \
that confirms receipt of the {received_doc} and asks them to send the remaining documents one by one.

Respond with only the message text — no commentary, no quotation marks."""


async def _draft_missing_document_message_en(received_label: str, missing_labels: list[str]) -> str:
    """Always drafts in English — this is what gets stored for the website
    (English-only regardless of chat language). Callers localize a copy for
    the actual WhatsApp send."""
    missing_docs_str = ", ".join(missing_labels)
    fallback = (
        f"Got your {received_label}! You still need to send: {missing_docs_str}. "
        f"Please send them one by one whenever you can."
    )

    try:
        prompt = AGENT_DRAFT_PROMPT.format(received_doc=received_label, missing_docs=missing_docs_str)
        response = await generate_content_with_retry(
            model=settings.gemini_text_model,
            contents=prompt,
        )
        return response.text.strip()
    except Exception:
        logger.exception("Failed to draft missing-document message via Gemini; using fallback text")
        return fallback


SUMMARY_PROMPT = """Act as a compliance officer summarizing a vendor's trade compliance profile for a B2B buyer, \
in English, in 2-3 sentences. Vendor: {name}. RCI (Regulatory Compliance Index) score: {rci_score}/100. All \
{doc_count} required certificates are uploaded and currently valid: {doc_labels}. Historical risk factor: {rf} \
(1.0 = no flags on record, lower values indicate more risk). Write a short, professional assessment of their \
compliance standing.

Respond with only the summary text — no commentary, no quotation marks."""


async def _draft_compliance_summary_en(company_name: str, rci_score: float, doc_labels: list[str], rf: float) -> str:
    """Called once all required documents are on file. Replaces the last
    'still missing X' nudge (which otherwise stays stored as the vendor's
    explanation forever) with an actual holistic assessment."""
    fallback = (
        f"{company_name} has all {len(doc_labels)} required certificates on file and verified, with an RCI "
        f"score of {rci_score:.1f}. No outstanding compliance gaps were detected."
    )

    try:
        prompt = SUMMARY_PROMPT.format(
            name=company_name,
            rci_score=rci_score,
            doc_count=len(doc_labels),
            doc_labels=", ".join(doc_labels),
            rf=rf,
        )
        response = await generate_content_with_retry(model=settings.gemini_text_model, contents=prompt)
        return response.text.strip()
    except Exception:
        logger.exception("Failed to draft compliance summary via Gemini; using fallback text")
        return fallback


NEGATIVE_STATUS_KEYWORDS = {"expired", "revoked", "invalid", "suspended", "cancelled", "canceled", "terminated"}


async def _upsert_document_from_extraction(
    company: Company, extracted_data: dict, uploaded_cleanly: bool = True
) -> DocumentType:
    matched_type = match_document_type(extracted_data.get("certificate_type") or "")
    expiry_date = parse_flexible_date(extracted_data.get("expiry_date"))
    status_text = (extracted_data.get("status") or "").lower()
    now = datetime.now(timezone.utc)

    # Real certificates rarely print a literal "Valid" stamp — they show a
    # status like "Compliant"/"Active"/"Certified", or no status at all, and
    # rely on the expiry date to convey current standing. Requiring the
    # substring "valid" here meant every genuine, currently-valid document
    # was marked invalid. Trust the expiry date as the primary signal, and
    # only override to invalid on an explicit negative status.
    has_negative_status = any(keyword in status_text for keyword in NEGATIVE_STATUS_KEYWORDS)
    is_valid = not has_negative_status and expiry_date is not None and expiry_date > now

    doc_fields = dict(
        company_id=company.id,
        user_id=company.user_id,
        type=matched_type,
        file_name=f"whatsapp_{PydanticObjectId()}.jpg",
        original_name=extracted_data.get("certificate_type") or "certificate",
        issuing_authority=extracted_data.get("issuer") or "Unknown",
        expiry_date=expiry_date or now,
        is_valid=is_valid,
        uploaded_cleanly=uploaded_cleanly,
        extracted_data=extracted_data,
    )

    if matched_type == DocumentType.other:
        # Catch-all bucket — distinct unrecognized documents shouldn't
        # overwrite each other. Only the 5 required types dedupe by type
        # (a re-uploaded trade license should replace the old one, not
        # accumulate duplicates).
        await ComplianceDocument(**doc_fields).insert()
        return matched_type

    existing = await ComplianceDocument.find_one(
        ComplianceDocument.company_id == company.id,
        ComplianceDocument.type == matched_type,
    )
    if existing:
        await existing.set(doc_fields)
    else:
        await ComplianceDocument(**doc_fields).insert()

    return matched_type


async def evaluate_vendor_action(
    company_id: str, extracted_data: dict, language: str = "English", uploaded_cleanly: bool = True
) -> dict:
    company = await Company.get(PydanticObjectId(company_id))
    if not company:
        raise ValueError(f"Company {company_id} not found")

    # 1. Update the vendor's profile with the newly received document.
    matched_type = await _upsert_document_from_extraction(company, extracted_data, uploaded_cleanly)

    # 2. Recompute the RCI subcomponents that are actually derivable from real
    # document data. DC is documentation completeness; AS/CS/DV are computed
    # here rather than left at their neutral defaults — see calculate_as/cs/dv
    # docstrings for what each measures. Every other subcomponent (RF, CR,
    # TLR, MSP, CI, LR, CCP, FH, FB) has no real data source in this app and
    # stays at its neutral placeholder rather than being fabricated.
    documents = await ComplianceDocument.find(ComplianceDocument.company_id == company.id).to_list()
    dc = calculate_dc(documents)
    as_score = calculate_as(documents)
    cs_score = calculate_cs(documents)
    dv_score = calculate_dv(documents)

    stored_subcomponents = company.rci_subcomponents or DEFAULT_SUBCOMPONENTS
    subcomponents = RCISubcomponents(**stored_subcomponents)
    subcomponents.core.DC = dc
    subcomponents.core.AS = as_score
    subcomponents.core.CS = cs_score
    subcomponents.macro.DV = dv_score

    # 3. Run the Phase 2 mathematical engine and evaluate the final score.
    result = calculate_rci(subcomponents)

    await company.set({
        "current_rci_score": result.rci_score,
        "rci_breakdown": result.model_dump(),
        "rci_subcomponents": subcomponents.model_dump(),
    })

    received_label = REQUIRED_DOC_LABELS.get(matched_type, matched_type.value.replace("_", " "))

    # 4. Agentic logic: is the missing-document penalty active?
    if result.missing_doc_penalty < 1.0:
        missing_types = missing_required_types(documents)
        missing_labels = [REQUIRED_DOC_LABELS.get(t, t.value) for t in missing_types]
        message_en = await _draft_missing_document_message_en(received_label, missing_labels)
        message_localized = await localize_message(message_en, language)

        # Website is English-only regardless of chat language — store the
        # English version; only the WhatsApp reply itself is localized.
        await company.set({"latest_ai_explanation": message_en})

        return {
            "action": "requested_document",
            "missing_documents": [t.value for t in missing_types],
            "message": message_localized,
            "rci_score": result.rci_score,
        }

    # All required documents present and valid — replace whatever nudge
    # message was last stored with an actual holistic summary.
    present_labels = [
        REQUIRED_DOC_LABELS[t] for t in REQUIRED_DOCUMENT_TYPES if t not in missing_required_types(documents)
    ]
    summary_en = await _draft_compliance_summary_en(
        company.name, result.rci_score, present_labels, subcomponents.core.RF
    )
    await company.set({"latest_ai_explanation": summary_en})

    return {"action": "none", "rci_score": result.rci_score, "received_document": received_label}
