from pydantic import BaseModel, Field


class MatchRequest(BaseModel):
    min_rci: float = Field(ge=0, le=100, description="Buyer's minimum required RCI score")
    min_dc: float = Field(ge=0, le=1, description="Buyer's minimum required Documentation Completeness")


class SellerMatch(BaseModel):
    seller_id: str
    name: str
    rci_score: float
    dc: float
