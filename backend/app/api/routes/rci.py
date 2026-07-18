from fastapi import APIRouter, Depends

from app.core.deps import CurrentUser, get_current_user
from app.core.rci_engine import calculate_rci
from app.schemas.rci import RCICalculationResult, RCISubcomponents

router = APIRouter(prefix="/api/rci", tags=["rci"])


@router.post("/calculate", response_model=RCICalculationResult)
async def calculate(payload: RCISubcomponents, current_user: CurrentUser = Depends(get_current_user)):
    return calculate_rci(payload)
