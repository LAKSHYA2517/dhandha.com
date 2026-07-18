from app.schemas.rci import RCICalculationResult, RCISubcomponents


def calculate_core_score(core) -> float:
    return 0.25 * core.AS + 0.20 * core.DC + 0.25 * core.RF + 0.15 * core.CS + 0.15 * core.PC


def calculate_external_score(external) -> float:
    return 0.40 * external.CR + 0.30 * external.TLR + 0.10 * external.MSP + 0.20 * external.CI


def calculate_operational_score(operational) -> float:
    return 0.60 * operational.LR + 0.40 * operational.CCP


def calculate_macro_score(macro) -> float:
    return 0.50 * macro.FH + 0.30 * macro.FB + 0.20 * macro.DV


def calculate_missing_doc_penalty(dc: float) -> float:
    return 0.7 + (0.3 * dc)


def calculate_legal_block(msp: float) -> int:
    return 0 if msp == 0 else 1


def calculate_rci(data: RCISubcomponents) -> RCICalculationResult:
    core_score = calculate_core_score(data.core)
    external_score = calculate_external_score(data.external)
    operational_score = calculate_operational_score(data.operational)
    macro_score = calculate_macro_score(data.macro)

    base_composite = (
        0.50 * core_score
        + 0.25 * external_score
        + 0.15 * operational_score
        + 0.10 * macro_score
    )

    missing_doc_penalty = calculate_missing_doc_penalty(data.core.DC)
    legal_block = calculate_legal_block(data.external.MSP)

    rci_score = round(100 * legal_block * missing_doc_penalty * base_composite, 2)

    return RCICalculationResult(
        core_score=round(core_score, 4),
        external_score=round(external_score, 4),
        operational_score=round(operational_score, 4),
        macro_score=round(macro_score, 4),
        base_composite=round(base_composite, 4),
        missing_doc_penalty=round(missing_doc_penalty, 4),
        legal_block=legal_block,
        rci_score=rci_score,
    )
