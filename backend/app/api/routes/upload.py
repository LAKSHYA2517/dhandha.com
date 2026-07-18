import os
import random
import time
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.ai_services.multimodal import parse_document_image
from app.core.deps import CurrentUser, get_current_user
from app.models.company import Company
from app.models.document import ComplianceDocument, DocumentType
from app.schemas.multimodal import ExtractedCertificateData

router = APIRouter(prefix="/api/upload", tags=["upload"])
documents_router = APIRouter(prefix="/api/documents", tags=["documents"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE = 5 * 1024 * 1024

AUTHORITIES = {
    "trade_license": "Ministry of Commerce",
    "iso_certificate": "ISO Certifying Body International",
    "tax_compliance": "Tax Revenue Authority",
    "export_permit": "Export Control Bureau",
    "quality_cert": "Quality Standards Institute",
    "other": "General Authority",
}

CERT_PREFIXES = {
    "trade_license": "TL",
    "iso_certificate": "ISO-9001",
    "tax_compliance": "TC",
    "export_permit": "EP",
    "quality_cert": "QC",
    "other": "DOC",
}


def simulate_extraction(doc_type: str, expiry_date: datetime) -> dict:
    now = datetime.now(timezone.utc)
    expiry = expiry_date if expiry_date.tzinfo else expiry_date.replace(tzinfo=timezone.utc)
    is_expired = expiry < now
    return {
        "certificateNumber": f"{CERT_PREFIXES.get(doc_type, 'DOC')}-{random.randint(0, 99999)}",
        "issuingAuthority": AUTHORITIES.get(doc_type, "General Authority"),
        "extractedOn": now.isoformat(),
        "validity": "EXPIRED" if is_expired else "VALID",
        "confidence": f"{85 + random.randint(0, 13)}%",
        "documentType": doc_type.replace("_", " ").upper(),
    }


@router.post("", status_code=201)
async def upload_document(
    type: DocumentType = Form(...),
    expiry_date: str = Form(...),
    document: UploadFile | None = File(None),
    current_user: CurrentUser = Depends(get_current_user),
):
    company = await Company.find_one(Company.user_id == current_user.id)
    if not company:
        raise HTTPException(status_code=400, detail="Create a company profile first")

    expiry = datetime.fromisoformat(expiry_date).replace(tzinfo=timezone.utc)
    is_valid = expiry > datetime.now(timezone.utc)
    extracted_data = simulate_extraction(type.value, expiry)

    if document is not None:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        ext = os.path.splitext(document.filename or "")[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Only PDF and image files allowed")
        contents = await document.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large (max 5MB)")
        file_name = f"{int(time.time() * 1000)}_{uuid.uuid4().hex[:9]}{ext}"
        with open(os.path.join(UPLOAD_DIR, file_name), "wb") as f:
            f.write(contents)
        original_name = document.filename
        mime_type = document.content_type
        file_size = len(contents)
    else:
        file_name = f"simulated_{int(time.time() * 1000)}.pdf"
        original_name = f"{type.value}_document.pdf"
        mime_type = "application/pdf"
        file_size = 0

    doc = ComplianceDocument(
        company_id=company.id,
        user_id=current_user.id,
        type=type,
        file_name=file_name,
        original_name=original_name,
        mime_type=mime_type,
        file_size=file_size,
        issuing_authority=extracted_data["issuingAuthority"],
        expiry_date=expiry,
        is_valid=is_valid,
        extracted_data=extracted_data,
    )
    await doc.insert()

    return {"success": True, "document": doc, "extractedData": extracted_data}


@router.get("/my-documents")
async def get_my_documents(current_user: CurrentUser = Depends(get_current_user)):
    company = await Company.find_one(Company.user_id == current_user.id)
    if not company:
        return {"success": True, "documents": []}

    docs = await ComplianceDocument.find(ComplianceDocument.company_id == company.id).to_list()
    return {"success": True, "documents": docs}


@documents_router.post("/extract", response_model=ExtractedCertificateData)
async def extract_document(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
):
    image_bytes = await file.read()
    mime_type = file.content_type or "image/jpeg"
    return await parse_document_image(image_bytes, mime_type)
