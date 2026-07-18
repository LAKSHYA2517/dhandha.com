import re
from datetime import datetime, timezone

from dateutil import parser as date_parser

from app.models.document import ComplianceDocument, DocumentType

# Legal-entity suffixes stripped before comparison so "Apex Dynamics India
# Pvt. Ltd." and "Apex Dynamics India" are recognized as the same company.
_LEGAL_SUFFIXES = [
    "private limited", "pvt ltd", "pvt. ltd.", "pvt", "limited", "ltd",
    "llp", "llc", "inc", "incorporated", "corporation", "corp", "co",
]

REQUIRED_DOCUMENT_TYPES = [
    DocumentType.trade_license,
    DocumentType.iso_certificate,
    DocumentType.tax_compliance,
    DocumentType.export_permit,
    DocumentType.quality_cert,
]

# Order matters: checked top-to-bottom, first match wins. More specific
# keywords go first — "iso" is broad enough to also appear inside other
# certificate types that merely *reference* an ISO/IEC standard in their body
# (e.g. a Quality Certification listing "ISO/IEC 27001" as its scope), so it's
# deliberately checked last to avoid misclassifying those as ISO certificates.
DOC_TYPE_KEYWORDS = {
    DocumentType.trade_license: ["trade license", "trade licence"],
    DocumentType.tax_compliance: ["tax"],
    DocumentType.export_permit: ["export permit", "export licence", "export license"],
    DocumentType.quality_cert: ["quality"],
    DocumentType.iso_certificate: ["iso"],
}

REQUIRED_DOC_LABELS = {
    DocumentType.trade_license: "Trade License",
    DocumentType.iso_certificate: "ISO 9001 Certificate",
    DocumentType.tax_compliance: "Tax Compliance Certificate",
    DocumentType.export_permit: "Export Permit",
    DocumentType.quality_cert: "Quality Certification",
}

# Maps each of the 7 WhatsApp-onboarding industry categories to keywords that
# might describe that business on a certificate's "Nature of Trade"/"Scope"/
# "Permitted Export Category" field. Freeform text on either side means this
# can only ever be a loose keyword match, not an exact one.
INDUSTRY_KEYWORDS = {
    "Agriculture & Food": ["agricult", "food", "farm", "organic", "seafood", "rice", "spice", "grain"],
    "Textiles & Apparel": ["textile", "apparel", "garment", "cotton", "fabric", "cloth", "silk", "yarn", "wool"],
    "Electronics & Tech": [
        "electronic", "software", "information technology", "it service", "hardware",
        "semiconductor", "circuit", "technology", "computer",
    ],
    "Logistics & Transport": ["logistics", "freight", "transport", "shipping", "cargo", "warehous"],
    "Manufacturing": ["manufactur", "industrial", "fabrication", "steel", "machin", "production"],
    "Chemicals & Pharma": ["chemical", "pharma", "drug", "medicine", "api", "pharmaceutical"],
    "Handicrafts & Goods": ["handicraft", "handmade", "craft", "artisan", "pottery", "decor"],
}


def match_document_type(certificate_type: str) -> DocumentType:
    lowered = (certificate_type or "").lower()
    for doc_type, keywords in DOC_TYPE_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return doc_type
    return DocumentType.other


def _normalize_company_name(name: str) -> str:
    normalized = re.sub(r"[^\w\s]", " ", name.lower())
    for suffix in _LEGAL_SUFFIXES:
        normalized = re.sub(rf"\b{re.escape(suffix)}\b", " ", normalized)
    return " ".join(normalized.split())


def company_names_match(registered_name: str, holder_name: str | None) -> bool:
    """Compares the vendor's registered company name against the entity name
    printed on an uploaded certificate. Tolerant of legal suffixes, punctuation,
    and minor OCR/translation variance — not an exact-string check — but a
    missing or unrelated holder name still fails, since that's exactly the
    mismatch this exists to catch (e.g. someone uploading another company's
    certificate)."""
    if not registered_name or not holder_name:
        return False

    a = _normalize_company_name(registered_name)
    b = _normalize_company_name(holder_name)
    if not a or not b:
        return False
    if a == b or a in b or b in a:
        return True

    a_tokens, b_tokens = set(a.split()), set(b.split())
    if not a_tokens or not b_tokens:
        return False
    overlap = len(a_tokens & b_tokens) / max(len(a_tokens), len(b_tokens))
    return overlap >= 0.6


def _normalize_text(text: str) -> str:
    return " ".join(re.sub(r"[^\w\s]", " ", text.lower()).split())


def location_matches(registered_location: str, holder_address: str | None) -> bool:
    """Checks the vendor's registered city against the address printed on the
    certificate. Registered location is typically "City, Country" — matching
    is deliberately anchored on the city (the first, most specific part)
    rather than a blanket token-overlap ratio: a country name alone (e.g.
    "India") is common to nearly every address and would satisfy a loose
    overlap threshold even when the city is completely different."""
    if not registered_location or not holder_address:
        return False

    city_part = registered_location.split(",")[0]
    city_tokens = set(_normalize_text(city_part).split())
    if not city_tokens:
        return False

    addr_tokens = set(_normalize_text(holder_address).split())
    if not addr_tokens:
        return False

    return bool(city_tokens & addr_tokens)


def industry_matches(registered_industry: str, business_activity: str | None) -> bool:
    """Checks the vendor's registered industry category against the trade/
    business activity described on the certificate. Tries the curated
    keyword list for known categories first, then falls back to plain token
    overlap for freeform/legacy industry values (e.g. companies onboarded
    before the industry dropdown existed)."""
    if not registered_industry or not business_activity:
        return False

    activity_lower = business_activity.lower()
    keywords = INDUSTRY_KEYWORDS.get(registered_industry)
    if keywords:
        return any(keyword in activity_lower for keyword in keywords)

    reg_tokens = set(_normalize_text(registered_industry).split())
    act_tokens = set(_normalize_text(business_activity).split())
    if not reg_tokens or not act_tokens:
        return False
    overlap = len(reg_tokens & act_tokens) / max(len(reg_tokens), len(act_tokens))
    return overlap >= 0.4


def parse_flexible_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        # Indian compliance documents are printed DD-MM-YYYY. Without
        # dayfirst=True, dateutil defaults to month-first for ambiguous dates
        # (e.g. "10-09-2025" silently became October 9th instead of the
        # intended September 10th), corrupting expiry/issue dates.
        parsed = date_parser.parse(value, dayfirst=True)
    except (ValueError, OverflowError):
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def calculate_dc(documents: list[ComplianceDocument]) -> float:
    now = datetime.now(timezone.utc)
    valid_present = {
        doc.type
        for doc in documents
        if doc.is_valid and doc.type in REQUIRED_DOCUMENT_TYPES and _aware(doc.expiry_date) > now
    }
    return round(len(valid_present) / len(REQUIRED_DOCUMENT_TYPES), 4)


def missing_required_types(documents: list[ComplianceDocument]) -> list[DocumentType]:
    now = datetime.now(timezone.utc)
    valid_present = {
        doc.type for doc in documents if doc.is_valid and _aware(doc.expiry_date) > now
    }
    return [t for t in REQUIRED_DOCUMENT_TYPES if t not in valid_present]


def _valid_required_docs(documents: list[ComplianceDocument]) -> list[ComplianceDocument]:
    now = datetime.now(timezone.utc)
    return [
        doc for doc in documents
        if doc.is_valid and doc.type in REQUIRED_DOCUMENT_TYPES and _aware(doc.expiry_date) > now
    ]


def calculate_as(documents: list[ComplianceDocument]) -> float:
    """Authenticity Score: fraction of currently-valid required documents that
    were accepted on their first upload attempt, with no prior seal/identity/
    type rejections. Reflects how cleanly verifiable the vendor's paperwork
    actually was, rather than a flat 1.0 for anyone who eventually got there."""
    valid_docs = _valid_required_docs(documents)
    if not valid_docs:
        return 0.5  # neutral — nothing on file yet to judge
    clean = sum(1 for doc in valid_docs if doc.uploaded_cleanly)
    return round(clean / len(valid_docs), 4)


def calculate_cs(documents: list[ComplianceDocument]) -> float:
    """Compliance Score: fraction of currently-valid required documents that
    are NOT within 30 days of expiring. A stricter, discrete near-term
    freshness signal, distinct from DV's continuous average runway."""
    valid_docs = _valid_required_docs(documents)
    if not valid_docs:
        return 0.5
    now = datetime.now(timezone.utc)
    fresh = sum(1 for doc in valid_docs if (_aware(doc.expiry_date) - now).days > 30)
    return round(fresh / len(valid_docs), 4)


def calculate_dv(documents: list[ComplianceDocument]) -> float:
    """Documentation validity runway (macro): average remaining validity
    across currently-valid required documents, normalized so >=365 days
    remaining maps to 1.0. Two vendors who both hold 5/5 valid documents can
    still differ here if one set is about to lapse and the other isn't."""
    valid_docs = _valid_required_docs(documents)
    if not valid_docs:
        return 0.5
    now = datetime.now(timezone.utc)
    ratios = [min(1.0, (_aware(doc.expiry_date) - now).days / 365) for doc in valid_docs]
    return round(sum(ratios) / len(ratios), 4)
