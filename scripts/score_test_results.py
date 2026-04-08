"""
Score CyberAssess analysis output against seeded ground truth.

Compares gap analysis results, follow-up trigger behavior, and RFI quality
against the expected findings in test_ground_truth.json.

Usage:
    python scripts/score_test_results.py
    python scripts/score_test_results.py --verbose   # show full evidence comparison
    python scripts/score_test_results.py --company "NovaPay"  # score one company
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models.assessment import Assessment, AssessmentDocument
from app.models.questionnaire import QuestionnaireResponse
from app.models.report import GapItem, GapReport
from app.models.rfi import RFIDocument

GROUND_TRUTH_PATH = Path(__file__).parent / "test_ground_truth.json"

# Map from ground truth actual_status to what gap analysis should output
STATUS_MAP = {
    "non_compliant": "non_compliant",
    "partially_compliant": "partially_compliant",
    "compliant": "compliant",
    "not_assessed": "not_assessed",
}

# How close the tool's status is to ground truth (0 = wrong, 1 = exact, 0.5 = adjacent)
STATUS_DISTANCE = {
    ("non_compliant", "non_compliant"): 1.0,
    ("non_compliant", "partially_compliant"): 0.3,  # Caught something but not the full gap
    ("non_compliant", "compliant"): 0.0,             # Missed entirely
    ("non_compliant", "not_assessed"): 0.0,
    ("partially_compliant", "partially_compliant"): 1.0,
    ("partially_compliant", "non_compliant"): 0.7,   # Overcalled but directionally correct
    ("partially_compliant", "compliant"): 0.0,
    ("partially_compliant", "not_assessed"): 0.0,
}


def load_ground_truth() -> dict:
    if not GROUND_TRUTH_PATH.exists():
        print(f"ERROR: Ground truth file not found at {GROUND_TRUTH_PATH}")
        print("Run seed_test_companies.py first.")
        sys.exit(1)
    with open(GROUND_TRUTH_PATH) as f:
        return json.load(f)


def score_company(company_gt: dict, db, verbose: bool = False) -> dict:
    """Score a single company's analysis results against ground truth."""
    assessment_id = company_gt["assessment_id"]
    company_name = company_gt["company_name"]

    # Check assessment exists
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        return {
            "company": company_name,
            "status": "NOT_FOUND",
            "message": f"Assessment {assessment_id} not in database",
            "scores": {},
        }

    # Check if analysis has been run
    report = (
        db.query(GapReport)
        .filter(GapReport.assessment_id == assessment_id)
        .first()
    )
    if not report:
        return {
            "company": company_name,
            "status": "NO_REPORT",
            "message": "Gap analysis has not been run yet",
            "scores": {},
        }

    # Load gap items
    gap_items = db.query(GapItem).filter(GapItem.report_id == report.id).all()
    gap_by_req = {g.requirement_id: g for g in gap_items}

    # Load RFI
    rfi = db.query(RFIDocument).filter(RFIDocument.assessment_id == assessment_id).first()

    # Score each hidden gap
    gap_scores = []
    for hidden_gap in company_gt["hidden_gaps"]:
        gap_result = _score_hidden_gap(hidden_gap, gap_by_req, rfi, verbose)
        gap_scores.append(gap_result)

    # Aggregate
    total_detection = sum(g["detection_score"] for g in gap_scores) / len(gap_scores) if gap_scores else 0
    total_severity = sum(g["severity_score"] for g in gap_scores) / len(gap_scores) if gap_scores else 0
    total_evidence = sum(g["evidence_score"] for g in gap_scores) / len(gap_scores) if gap_scores else 0
    total_rfi = sum(g["rfi_score"] for g in gap_scores) / len(gap_scores) if gap_scores else 0

    overall = (total_detection * 0.40) + (total_severity * 0.20) + (total_evidence * 0.20) + (total_rfi * 0.20)

    return {
        "company": company_name,
        "status": "SCORED",
        "assessment_id": assessment_id,
        "gap_scores": gap_scores,
        "summary": {
            "detection_accuracy": round(total_detection * 100, 1),
            "severity_accuracy": round(total_severity * 100, 1),
            "evidence_grounding": round(total_evidence * 100, 1),
            "rfi_relevance": round(total_rfi * 100, 1),
            "overall": round(overall * 100, 1),
        },
    }


def _score_hidden_gap(hidden_gap: dict, gap_by_req: dict, rfi, verbose: bool) -> dict:
    """Score the tool's detection of a single hidden gap."""
    req_ids = hidden_gap["requirement_ids"]
    expected_status = hidden_gap["actual_status"]
    surface_answer = hidden_gap["surface_answer"]
    gap_desc = hidden_gap["gap_description"]
    evidence_hint = hidden_gap.get("evidence_quote_hint", "")

    # --- 1. Detection Score: Did the tool downgrade the status from surface answer? ---
    detection_scores = []
    for req_id in req_ids:
        gap_item = gap_by_req.get(req_id)
        if not gap_item:
            detection_scores.append(0.0)
            continue

        actual_tool_status = gap_item.compliance_status
        pair = (expected_status, actual_tool_status)
        score = STATUS_DISTANCE.get(pair, 0.0)

        # Bonus: if the tool correctly downgraded from the surface answer
        if actual_tool_status != surface_answer and actual_tool_status == expected_status:
            score = min(score + 0.1, 1.0)  # Small bonus for exact match after downgrade

        detection_scores.append(score)

    detection_score = sum(detection_scores) / len(detection_scores) if detection_scores else 0

    # --- 2. Severity Score: Did the tool correctly assess risk level? ---
    severity_scores = []
    for req_id in req_ids:
        gap_item = gap_by_req.get(req_id)
        if not gap_item:
            severity_scores.append(0.0)
            continue

        # If the gap was detected (status != compliant), check if risk level makes sense
        if gap_item.compliance_status in ("non_compliant", "partially_compliant"):
            if gap_item.risk_level in ("high", "critical"):
                severity_scores.append(1.0)
            elif gap_item.risk_level == "medium":
                severity_scores.append(0.5)
            else:
                severity_scores.append(0.2)
        else:
            severity_scores.append(0.0)

    severity_score = sum(severity_scores) / len(severity_scores) if severity_scores else 0

    # --- 3. Evidence Score: Did the tool cite relevant evidence? ---
    evidence_scores = []
    for req_id in req_ids:
        gap_item = gap_by_req.get(req_id)
        if not gap_item:
            evidence_scores.append(0.0)
            continue

        ev_score = 0.0

        # Check if gap_description references the core issue
        if gap_item.gap_description:
            # Check for key phrases from the ground truth gap description
            key_phrases = _extract_key_phrases(gap_desc)
            matches = sum(1 for phrase in key_phrases if phrase.lower() in gap_item.gap_description.lower())
            ev_score = min(matches / max(len(key_phrases), 1), 1.0)

        # Check if evidence_quote references document text
        if gap_item.evidence_quote and evidence_hint:
            hint_words = set(evidence_hint.lower().split())
            quote_words = set(gap_item.evidence_quote.lower().split())
            overlap = len(hint_words & quote_words) / max(len(hint_words), 1)
            ev_score = max(ev_score, overlap)

        evidence_scores.append(ev_score)

    evidence_score = sum(evidence_scores) / len(evidence_scores) if evidence_scores else 0

    # --- 4. RFI Score: Did the RFI ask for the right thing? ---
    rfi_score = 0.0
    if rfi:
        try:
            evidence_items = json.loads(rfi.evidence_items)
        except (json.JSONDecodeError, TypeError):
            evidence_items = []

        # Check if any RFI item targets the gap's requirements
        relevant_rfi_items = [
            item for item in evidence_items
            if item.get("requirement_id") in req_ids
               or any(rid in str(item) for rid in req_ids)
        ]

        if relevant_rfi_items:
            rfi_score = 0.5  # Found relevant RFI item

            # Check if the RFI item asks for something specific (not generic)
            for item in relevant_rfi_items:
                item_text = json.dumps(item).lower()
                key_phrases = _extract_key_phrases(gap_desc)
                if any(phrase.lower() in item_text for phrase in key_phrases):
                    rfi_score = 1.0
                    break

    result = {
        "requirement_ids": req_ids,
        "expected_status": expected_status,
        "surface_answer": surface_answer,
        "gap_description": gap_desc,
        "detection_score": round(detection_score, 3),
        "severity_score": round(severity_score, 3),
        "evidence_score": round(evidence_score, 3),
        "rfi_score": round(rfi_score, 3),
    }

    if verbose:
        result["details"] = {}
        for req_id in req_ids:
            gap_item = gap_by_req.get(req_id)
            if gap_item:
                result["details"][req_id] = {
                    "tool_status": gap_item.compliance_status,
                    "tool_risk_level": gap_item.risk_level,
                    "tool_gap_description": gap_item.gap_description[:200] if gap_item.gap_description else None,
                    "tool_evidence_quote": gap_item.evidence_quote[:200] if gap_item.evidence_quote else None,
                }
            else:
                result["details"][req_id] = {"tool_status": "NOT_ASSESSED"}

    return result


def _extract_key_phrases(description: str) -> list[str]:
    """Extract key phrases from a gap description for fuzzy matching."""
    # Split on common delimiters and filter short/generic words
    words = description.replace(",", " ").replace(".", " ").replace("—", " ").split()
    stop_words = {"the", "a", "an", "is", "are", "was", "were", "no", "not", "and", "or", "but",
                  "in", "on", "at", "to", "for", "of", "with", "from", "by", "as", "it", "its",
                  "this", "that", "they", "their", "has", "have", "had", "do", "does", "did"}

    # Return meaningful 2-3 word phrases
    phrases = []
    meaningful_words = [w for w in words if w.lower() not in stop_words and len(w) > 2]

    # Individual meaningful words
    for w in meaningful_words:
        if len(w) > 4:  # Only words with some substance
            phrases.append(w)

    # Bigrams from meaningful words
    for i in range(len(meaningful_words) - 1):
        phrases.append(f"{meaningful_words[i]} {meaningful_words[i+1]}")

    return phrases[:10]  # Cap at 10 to avoid over-matching


def print_report(results: list[dict]):
    """Print a formatted scoring report."""
    print("\n" + "=" * 70)
    print("  CYBERASSESS TEST SCORING REPORT")
    print("=" * 70)

    all_scored = [r for r in results if r["status"] == "SCORED"]
    not_ready = [r for r in results if r["status"] != "SCORED"]

    if not_ready:
        print("\n--- Not Ready ---")
        for r in not_ready:
            print(f"  {r['company']}: {r['status']} — {r['message']}")

    for r in all_scored:
        print(f"\n--- {r['company']} ---")
        s = r["summary"]
        print(f"  Detection Accuracy:  {s['detection_accuracy']:5.1f}%  (Did the tool find the hidden gaps?)")
        print(f"  Severity Accuracy:   {s['severity_accuracy']:5.1f}%  (Did it rate risk correctly?)")
        print(f"  Evidence Grounding:  {s['evidence_grounding']:5.1f}%  (Did it cite the right evidence?)")
        print(f"  RFI Relevance:       {s['rfi_relevance']:5.1f}%  (Did the RFI ask for the right things?)")
        print(f"  Overall:             {s['overall']:5.1f}%")
        print()

        for gap in r["gap_scores"]:
            reqs = ", ".join(gap["requirement_ids"])
            det = "CAUGHT" if gap["detection_score"] >= 0.7 else "PARTIAL" if gap["detection_score"] >= 0.3 else "MISSED"
            icon = {"CAUGHT": "+", "PARTIAL": "~", "MISSED": "x"}[det]
            print(f"  [{icon}] {reqs}")
            print(f"      Expected: {gap['expected_status']} (surface: {gap['surface_answer']})")
            print(f"      Detection: {gap['detection_score']:.0%}  Severity: {gap['severity_score']:.0%}  Evidence: {gap['evidence_score']:.0%}  RFI: {gap['rfi_score']:.0%}")

            if "details" in gap:
                for req_id, detail in gap["details"].items():
                    print(f"      {req_id}: tool said {detail['tool_status']}, risk={detail.get('tool_risk_level', 'n/a')}")
                    if detail.get("tool_gap_description"):
                        print(f"        desc: {detail['tool_gap_description']}")
            print()

    # Overall summary
    if all_scored:
        avg_overall = sum(r["summary"]["overall"] for r in all_scored) / len(all_scored)
        total_gaps = sum(len(r["gap_scores"]) for r in all_scored)
        caught = sum(1 for r in all_scored for g in r["gap_scores"] if g["detection_score"] >= 0.7)
        partial = sum(1 for r in all_scored for g in r["gap_scores"] if 0.3 <= g["detection_score"] < 0.7)
        missed = sum(1 for r in all_scored for g in r["gap_scores"] if g["detection_score"] < 0.3)

        print("=" * 70)
        print(f"  OVERALL: {avg_overall:.1f}%")
        print(f"  Gaps: {total_gaps} total — {caught} caught, {partial} partial, {missed} missed")
        print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Score CyberAssess test results against ground truth")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed per-requirement results")
    parser.add_argument("--company", "-c", type=str, help="Score only one company (substring match)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of formatted report")
    args = parser.parse_args()

    ground_truth = load_ground_truth()
    companies = ground_truth["companies"]

    if args.company:
        companies = [c for c in companies if args.company.lower() in c["company_name"].lower()]
        if not companies:
            print(f"No company matching '{args.company}' found in ground truth")
            sys.exit(1)

    db = SessionLocal()
    try:
        results = []
        for company_gt in companies:
            result = score_company(company_gt, db, verbose=args.verbose)
            results.append(result)

        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print_report(results)
    finally:
        db.close()


if __name__ == "__main__":
    main()
