from pydantic import BaseModel, Field


class CoreSubcomponents(BaseModel):
    AS: float = Field(ge=0, le=1, description="Audit Score")
    DC: float = Field(ge=0, le=1, description="Documentation Completeness")
    RF: float = Field(ge=0, le=1, description="Regulatory Filing")
    CS: float = Field(ge=0, le=1, description="Compliance Standing")
    PC: float = Field(ge=0, le=1, description="Policy Conformance")


class ExternalSubcomponents(BaseModel):
    CR: float = Field(ge=0, le=1, description="Country Risk")
    TLR: float = Field(ge=0, le=1, description="Trade Law Risk")
    MSP: float = Field(ge=0, le=1, description="Market Sanctions Position (0 = sanctioned)")
    CI: float = Field(ge=0, le=1, description="Corruption Index")


class OperationalSubcomponents(BaseModel):
    LR: float = Field(ge=0, le=1, description="Litigation Risk")
    CCP: float = Field(ge=0, le=1, description="Corporate Compliance Program")


class MacroSubcomponents(BaseModel):
    FH: float = Field(ge=0, le=1, description="Financial Health")
    FB: float = Field(ge=0, le=1, description="Financial Backing")
    DV: float = Field(ge=0, le=1, description="Demand Volatility")


class RCISubcomponents(BaseModel):
    core: CoreSubcomponents
    external: ExternalSubcomponents
    operational: OperationalSubcomponents
    macro: MacroSubcomponents


class RCICalculationResult(BaseModel):
    core_score: float
    external_score: float
    operational_score: float
    macro_score: float
    base_composite: float
    missing_doc_penalty: float
    legal_block: int
    rci_score: float
