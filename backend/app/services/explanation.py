from datetime import datetime, timezone

LOW_RISK_COUNTRIES = [
    "Germany", "Japan", "United States", "United Kingdom", "Singapore",
    "Canada", "Australia", "Netherlands", "Switzerland",
]


def generate_explanation(my_company, target_company, target_rci: float, my_rci: float) -> dict:
    reasons = []
    warnings = []

    if target_rci >= 75:
        reasons.append(f"{target_company.name} has an excellent RCI score of {target_rci:.1f}, placing it in the top compliance tier.")
    elif target_rci >= 55:
        reasons.append(f"{target_company.name} holds a strong RCI score of {target_rci:.1f}, indicating solid regulatory adherence.")
    elif target_rci >= 35:
        reasons.append(f"{target_company.name} has a moderate RCI score of {target_rci:.1f}.")
        warnings.append("Recommend additional due diligence before proceeding.")
    else:
        warnings.append(f"{target_company.name} has a low RCI score ({target_rci:.1f}). High compliance risk detected.")

    if target_company.country in LOW_RISK_COUNTRIES:
        reasons.append(f"Registered in {target_company.country}, a low-risk jurisdiction with strong regulatory frameworks.")
    else:
        reasons.append(f"Based in {target_company.country} — review country-specific trade regulations before finalizing.")

    if target_company.compliance_status:
        reasons.append("All submitted documents have been verified as current and compliant.")
    else:
        warnings.append("Compliance status is not fully confirmed — request updated documentation.")

    if my_company and my_company.industry == target_company.industry:
        reasons.append(f"Operates in the same industry ({target_company.industry}), enabling smoother regulatory alignment.")
    if my_company and my_company.trade_category == target_company.trade_category:
        reasons.append(f"Shared trade category ({target_company.trade_category}) suggests compatible operational standards.")

    if my_rci and abs(target_rci - my_rci) < 10:
        reasons.append(f"RCI scores are closely matched (difference: {abs(target_rci - my_rci):.1f} points), indicating mutual compliance compatibility.")

    if target_rci >= 65 and target_company.compliance_status:
        recommendation = "HIGHLY RECOMMENDED — This partner demonstrates outstanding compliance credentials."
    elif target_rci >= 45:
        recommendation = "RECOMMENDED — This partner meets core compliance requirements. Proceed with standard verification."
    elif target_rci >= 30:
        recommendation = "PROCEED WITH CAUTION — Compliance gaps detected. Enhanced due diligence advised."
    else:
        recommendation = "NOT RECOMMENDED — Significant compliance deficiencies. High trading risk."

    return {
        "reasons": reasons,
        "warnings": warnings,
        "recommendation": recommendation,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }
