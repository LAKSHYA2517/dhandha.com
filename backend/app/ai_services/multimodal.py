from google.genai import types

from app.ai_services.json_utils import parse_json_response
from app.core.config import settings
from app.core.llm import generate_content_with_retry
from app.schemas.multimodal import ExtractedCertificateData

EXTRACTION_PROMPT = """Analyze this image of a compliance certificate closely. It may contain regional languages.

Extract the compliance certificate details from this image. Output only raw valid JSON matching this schema:
{"certificate_type": string, "issuer": string, "issue_date": string, "expiry_date": string, "status": string,
 "holder_name": string, "holder_address": string, "business_activity": string, "has_official_seal": boolean}

Field guidance:
- certificate_type: Use the document's own main heading/title (the largest, most prominent text near the
  top — e.g. "Trade License", "Certificate of Tax Compliance", "Export Permit Certification", "Quality
  Certification"). Prefer one of these five categories when the document reasonably matches one: Trade
  License, ISO 9001 Certificate, Tax Compliance Certificate, Export Permit, Quality Certification. Do NOT
  use a standard or code merely *referenced inside* the document's body or tables (e.g. a "Quality
  Certification" that lists "ISO/IEC 27001" as its scope is still a Quality Certification, not an ISO
  certificate) — only the document's own title determines certificate_type.
- issuer: The issuing authority or certifying body named on the document. If not present, use null.
- issue_date / expiry_date: Format as DD-MM-YYYY (Indian date convention used on these documents). Read
  every date field carefully — check labels like "Date of Issue", "First Certified", "Date of
  Certification", "Date of Expiry", "Valid Until", "Certificate Expiry" individually rather than assuming
  which is which from position alone. If a field is not printed on the document, use null rather than
  guessing.
- status: A short validity indicator if the document states one (e.g. "Valid", "Compliant", "Active",
  "Expired", "Revoked"). If the document doesn't print an explicit status, use null — do not invent one.
- holder_name: The exact name of the company/entity the certificate is issued to, as printed on the
  document (often labeled "Enterprise Name", "Certified Enterprise", "Issued To", or appearing directly
  after "This is to certify that"). Transcribe it exactly as printed, including suffixes like "Pvt. Ltd."
  If no holder/entity name is printed anywhere, use null.
- holder_address: The full address printed for the holder company (street, area, city, state, PIN/postal
  code, country) — transcribe it as printed. If no address is printed, use null.
- business_activity: The trade/industry activity or scope described on the document — check labels like
  "Nature of Trade", "Scope", "Permitted Export Category", "Description of Goods/Services", or similar
  (e.g. "Information Technology", "Software Products & Services", "Frozen Seafood Export"). If none is
  printed, use null.
- has_official_seal: true ONLY if the mark clearly shows genuine printed/embossed authority markings — it
  must contain readable text (an organization name, "certified"/"approved"/"registered" wording, or a
  registration number) arranged as part of a stamp, AND look like it was produced by a real stamp/seal/
  official printing process (crisp circular or ornate border, consistent ink/emboss texture), not a
  freehand drawing. Explicitly set false for: a plain hand-drawn circle, oval, or doodle with no text
  inside or around it; a signature by itself; a decorative border or letterhead logo with no stamp-like
  mark; any circular shape that looks sketched/uneven rather than printed. If you cannot clearly read
  authority-identifying text within the mark, set false — when genuinely unsure, false is the safe default,
  since treating an unverifiable mark as a real seal defeats the point of checking for one at all.

Respond with a single JSON object only — not a list/array, even if the image shows multiple certificates
or sections. If there are multiple, describe the single most prominent one.
Do not include markdown formatting or any text outside the JSON object."""


async def parse_document_image(image_bytes: bytes, mime_type: str) -> ExtractedCertificateData:
    response = await generate_content_with_retry(
        model=settings.gemini_vision_model,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            EXTRACTION_PROMPT,
        ],
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )

    data = parse_json_response(response.text)
    if isinstance(data, list):
        data = data[0] if data else {}
    return ExtractedCertificateData(**data)
