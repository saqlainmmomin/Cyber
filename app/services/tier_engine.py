"""
Tier Engine — assigns assessment depth tier to each question.

Tiers control how much time and attention each question receives in the UI:
  - DEEP:     Full question + follow-ups + evidence panel (critical/flagged controls, ~5 min)
  - STANDARD: Single question with notes (default, ~2 min)
  - LIGHT:    Compact confirmation card (pre-filled non-critical, ~30 sec)
  - SKIP:     Hidden / auto-marked N/A (scope exclusion, 0 min)

Rules are evaluated in priority order — first match wins.
"""

TIERS = ("skip", "light", "standard", "deep")


def assign_tier(question: dict, risk_tier: str = "MEDIUM") -> str:
    """Assign an assessment depth tier to a single question.

    Args:
        question: Question dict with at least 'status' and 'criticality' keys.
        risk_tier: Organization risk tier from context profile ("HIGH", "MEDIUM", "LOW").

    Returns:
        One of: "deep", "standard", "light", "skip"
    """
    status = question.get("status", "active")
    criticality = question.get("criticality", "medium")

    # Rule 1: Scope exclusions → SKIP
    if status == "skipped":
        return "skip"

    # Rule 2: Pre-filled + non-critical → LIGHT (compact confirmation)
    if status == "pre_filled" and criticality != "critical":
        return "light"

    # Rule 3: Pre-filled + critical → STANDARD (critical controls always need attention)
    if status == "pre_filled" and criticality == "critical":
        return "standard"

    # Rule 4: Deepened by desk review (signals/absences) → DEEP
    if status == "deepened":
        return "deep"

    # Rule 5: Critical controls with HIGH org risk → DEEP
    if criticality == "critical" and risk_tier == "HIGH":
        return "deep"

    # Rule 6: High criticality with HIGH org risk → DEEP
    if criticality == "high" and risk_tier == "HIGH":
        return "deep"

    # Rule 7: Default → STANDARD
    return "standard"


def assign_tiers(questions: list[dict], risk_tier: str = "MEDIUM") -> list[dict]:
    """Assign tiers to a list of questions, mutating each dict in place.

    Args:
        questions: List of question dicts from modulation.
        risk_tier: Organization risk tier from context profile.

    Returns:
        The same list with 'tier' key added to each question.
    """
    for q in questions:
        q["tier"] = assign_tier(q, risk_tier)
    return questions


def compute_tier_stats(questions: list[dict]) -> dict:
    """Count questions per tier.

    Returns:
        {"deep": int, "standard": int, "light": int, "skip": int}
    """
    counts = {"deep": 0, "standard": 0, "light": 0, "skip": 0}
    for q in questions:
        tier = q.get("tier", "standard")
        if tier in counts:
            counts[tier] += 1
    return counts
