from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import CurrentUser, get_current_user
from app.models.company import Company
from app.services.explanation import generate_explanation

router = APIRouter(prefix="/api/explanation", tags=["explanation"])


@router.get("/{company_id}")
async def get_explanation(company_id: PydanticObjectId, current_user: CurrentUser = Depends(get_current_user)):
    my_company = await Company.find_one(Company.user_id == current_user.id)
    target_company = await Company.get(company_id)

    if not target_company:
        raise HTTPException(status_code=404, detail="Company not found")

    target_rci = target_company.rci_score or 0
    my_rci = my_company.rci_score if my_company else 0

    explanation = generate_explanation(my_company, target_company, target_rci, my_rci or 0)

    return {
        "success": True,
        "explanation": explanation,
        "targetCompany": {
            "name": target_company.name,
            "country": target_company.country,
            "industry": target_company.industry,
            "rciScore": target_rci,
        },
    }
