from fastapi import APIRouter, Depends

from app.core.deps import CurrentUser, get_current_user
from app.core.mock_sellers import MOCK_SELLERS
from app.core.rci_engine import calculate_rci
from app.schemas.match import MatchRequest, SellerMatch

router = APIRouter(prefix="/api/match", tags=["match"])


@router.post("", response_model=list[SellerMatch])
async def match_sellers(payload: MatchRequest, current_user: CurrentUser = Depends(get_current_user)):
    matches = []
    for seller in MOCK_SELLERS:
        subcomponents = seller["subcomponents"]
        result = calculate_rci(subcomponents)
        dc = subcomponents.core.DC

        if result.rci_score >= payload.min_rci and dc >= payload.min_dc:
            matches.append(SellerMatch(
                seller_id=seller["seller_id"],
                name=seller["name"],
                rci_score=result.rci_score,
                dc=dc,
            ))

    return matches
