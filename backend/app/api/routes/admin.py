from fastapi import APIRouter, Depends

from app.core.deps import CurrentUser, require_admin
from app.models.company import Company
from app.models.document import ComplianceDocument
from app.models.user import User

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats")
async def get_stats(current_user: CurrentUser = Depends(require_admin)):
    users = await User.count()
    companies = await Company.count()
    documents = await ComplianceDocument.count()

    scores = [c.rci_score async for c in Company.find(Company.rci_score != None) if c.rci_score is not None]  # noqa: E711
    avg_rci = round(sum(scores) / len(scores), 2) if scores else "N/A"

    return {
        "success": True,
        "stats": {"users": users, "companies": companies, "documents": documents, "avgRCI": avg_rci},
    }


@router.get("/users")
async def get_users(current_user: CurrentUser = Depends(require_admin)):
    users = await User.find_all().to_list()
    safe_users = [{"id": str(u.id), "name": u.name, "email": u.email, "role": u.role, "created_at": u.created_at} for u in users]
    return {"success": True, "users": safe_users}


@router.get("/companies")
async def get_companies(current_user: CurrentUser = Depends(require_admin)):
    companies = await Company.find_all().sort(-Company.rci_score).to_list()
    return {"success": True, "companies": companies}
