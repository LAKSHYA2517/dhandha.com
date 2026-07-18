from datetime import datetime, timezone

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException
from google.genai import errors as genai_errors

from app.ai_services.rag_policy import evaluate_compliance
from app.core.deps import CurrentUser, get_current_user
from app.core.rci_engine import calculate_rci
from app.models.company import Company
from app.models.document import ComplianceDocument
from app.schemas.company import CompanyCreateRequest, CompanyUpdateRequest, RunComplianceRequest
from app.services.document_compliance import REQUIRED_DOC_LABELS

router = APIRouter(prefix="/api/company", tags=["company"])


@router.post("", status_code=201)
async def create_company(payload: CompanyCreateRequest, current_user: CurrentUser = Depends(get_current_user)):
    existing = await Company.find_one(Company.user_id == current_user.id)
    if existing:
        raise HTTPException(status_code=400, detail="Company profile already exists")

    company = Company(user_id=current_user.id, **payload.model_dump())
    await company.insert()
    return {"success": True, "company": company}


@router.get("/me")
async def get_my_company(current_user: CurrentUser = Depends(get_current_user)):
    company = await Company.find_one(Company.user_id == current_user.id)
    if not company:
        raise HTTPException(status_code=404, detail="No company profile found")
    return {"success": True, "company": company}


@router.put("/me")
async def update_my_company(payload: CompanyUpdateRequest, current_user: CurrentUser = Depends(get_current_user)):
    company = await Company.find_one(Company.user_id == current_user.id)
    if not company:
        raise HTTPException(status_code=404, detail="No company profile found")

    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    updates["updated_at"] = datetime.now(timezone.utc)
    await company.set(updates)
    return {"success": True, "company": company}


@router.get("/all")
async def get_all_companies(current_user: CurrentUser = Depends(get_current_user)):
    companies = await Company.find_all().to_list()
    return {"success": True, "companies": companies}


@router.get("/{company_id}/documents")
async def get_company_documents(company_id: PydanticObjectId, current_user: CurrentUser = Depends(get_current_user)):
    """Buyer-facing document summary. Deliberately never returns the raw uploaded
    file (file_name/original_name/user_id) — only the certificate type, validity,
    and the non-sensitive fields Gemma extracted — so other companies can verify
    compliance without ever seeing the actual document."""
    company = await Company.get(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    documents = await ComplianceDocument.find(ComplianceDocument.company_id == company_id).to_list()

    results = []
    for doc in documents:
        extracted = doc.extracted_data or {}
        results.append({
            "type": doc.type.value,
            "label": REQUIRED_DOC_LABELS.get(doc.type, doc.type.value.replace("_", " ").title()),
            "issuing_authority": doc.issuing_authority,
            "expiry_date": doc.expiry_date,
            "is_valid": doc.is_valid,
            "extracted_metadata": {
                "certificate_type": extracted.get("certificate_type"),
                "issue_date": extracted.get("issue_date"),
                "expiry_date": extracted.get("expiry_date"),
                "status": extracted.get("status"),
            },
        })

    return {"success": True, "documents": results}


@router.post("/{company_id}/run-compliance")
async def run_compliance(
    company_id: PydanticObjectId,
    payload: RunComplianceRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    company = await Company.get(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    try:
        evaluation = await evaluate_compliance(payload.vendor_data, payload.trade_route)
    except genai_errors.ServerError:
        raise HTTPException(
            status_code=502,
            detail="The AI evaluation service is temporarily unavailable. Please try again in a moment.",
        )

    subcomponents = payload.subcomponents
    subcomponents.core.RF = evaluation["regulatory_fit_score"]

    result = calculate_rci(subcomponents)
    breakdown = result.model_dump()

    await company.set({
        "current_rci_score": result.rci_score,
        "rci_breakdown": breakdown,
        "latest_ai_explanation": evaluation["explanation"],
        "updated_at": datetime.now(timezone.utc),
    })

    return {
        "success": True,
        "rci_score": result.rci_score,
        "breakdown": breakdown,
        "explanation": evaluation["explanation"],
    }
