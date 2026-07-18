from app.schemas.rci import (
    CoreSubcomponents,
    ExternalSubcomponents,
    MacroSubcomponents,
    OperationalSubcomponents,
    RCISubcomponents,
)

MOCK_SELLERS = [
    {
        "seller_id": "S001",
        "name": "Alpha Trading Co",
        "subcomponents": RCISubcomponents(
            core=CoreSubcomponents(AS=0.9, DC=0.95, RF=0.9, CS=0.85, PC=0.9),
            external=ExternalSubcomponents(CR=0.85, TLR=0.8, MSP=1.0, CI=0.8),
            operational=OperationalSubcomponents(LR=0.9, CCP=0.85),
            macro=MacroSubcomponents(FH=0.85, FB=0.8, DV=0.9),
        ),
    },
    {
        "seller_id": "S002",
        "name": "Beta Exports Ltd",
        "subcomponents": RCISubcomponents(
            core=CoreSubcomponents(AS=0.7, DC=0.6, RF=0.65, CS=0.7, PC=0.6),
            external=ExternalSubcomponents(CR=0.6, TLR=0.55, MSP=1.0, CI=0.6),
            operational=OperationalSubcomponents(LR=0.65, CCP=0.6),
            macro=MacroSubcomponents(FH=0.6, FB=0.55, DV=0.6),
        ),
    },
    {
        "seller_id": "S003",
        "name": "Continental Metals Inc",
        "subcomponents": RCISubcomponents(
            core=CoreSubcomponents(AS=0.5, DC=0.3, RF=0.4, CS=0.45, PC=0.4),
            external=ExternalSubcomponents(CR=0.45, TLR=0.4, MSP=1.0, CI=0.4),
            operational=OperationalSubcomponents(LR=0.4, CCP=0.35),
            macro=MacroSubcomponents(FH=0.4, FB=0.35, DV=0.4),
        ),
    },
    {
        "seller_id": "S004",
        "name": "Sanctioned Global Holdings",
        "subcomponents": RCISubcomponents(
            core=CoreSubcomponents(AS=0.8, DC=0.9, RF=0.8, CS=0.8, PC=0.8),
            external=ExternalSubcomponents(CR=0.7, TLR=0.7, MSP=0.0, CI=0.7),
            operational=OperationalSubcomponents(LR=0.8, CCP=0.8),
            macro=MacroSubcomponents(FH=0.8, FB=0.8, DV=0.8),
        ),
    },
    {
        "seller_id": "S005",
        "name": "Delta Precision Manufacturing",
        "subcomponents": RCISubcomponents(
            core=CoreSubcomponents(AS=0.95, DC=0.4, RF=0.9, CS=0.9, PC=0.85),
            external=ExternalSubcomponents(CR=0.9, TLR=0.85, MSP=1.0, CI=0.85),
            operational=OperationalSubcomponents(LR=0.9, CCP=0.9),
            macro=MacroSubcomponents(FH=0.9, FB=0.85, DV=0.85),
        ),
    },
]
