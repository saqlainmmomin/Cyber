"""
Generate a printable facilitator's guide from the questionnaire and context question definitions.

Usage:
    python scripts/generate_facilitator_guide.py

Output:
    docs/facilitator-guide.md
"""

import sys
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.dpdpa.context_questions import CONTEXT_BLOCKS
from app.dpdpa.questionnaire import ANSWER_OPTIONS, _GUIDANCE_TEXT, _QUESTION_TEXT
from app.dpdpa.framework import DPDPA_FRAMEWORK

OUTPUT_PATH = Path(__file__).parent.parent / "docs" / "facilitator-guide.md"

# Human-readable option labels
OPTION_LABELS = {
    # Context questions — data landscape
    "identity": "Identity data (name, DOB, address, ID numbers)",
    "financial": "Financial data (bank accounts, cards, transactions)",
    "health": "Health / medical data",
    "biometric": "Biometric data (fingerprints, face, voice)",
    "location": "Location data (GPS, IP-derived)",
    "behavioral": "Behavioral / usage data",
    "childrens": "Children's data (under 18)",
    "other": "Other",
    "web_forms": "Web forms",
    "mobile_app": "Mobile app",
    "third_party_apis": "Third-party APIs",
    "physical_forms": "Physical forms",
    "automated_tracking": "Automated tracking (cookies, pixels)",
    "yes": "Yes",
    "no": "No",
    "unsure": "Unsure",
    # Existing posture
    "full_time": "Full-time DPO / privacy function",
    "part_time_shared": "Part-time or shared responsibility",
    "iso_27001_certified": "ISO 27001 certified",
    "soc2": "SOC 2 certified",
    "internal_policy_only": "Internal policy only (no external certification)",
    "none": "None",
    "external_audit": "External audit conducted",
    "internal_only": "Internal audit only",
    "yes_recently_updated": "Yes, recently updated (within 12 months)",
    "yes_outdated": "Yes, but outdated (older than 12 months)",
    # Risk exposure
    "processes_childrens_data": "Processes children's data (under 18)",
    "healthcare_finance_critical_infra": "Healthcare, finance, or critical infrastructure sector",
    "handles_sensitive_personal_data": "Handles sensitive personal data",
    "designated_or_likely_sdf": "Designated or likely Significant Data Fiduciary (SDF)",
    "under_10k": "Under 10,000 data principals",
    "10k_to_1m": "10,000 to 1 million",
    "1m_to_10m": "1 million to 10 million",
    "over_10m": "Over 10 million",
    "yes_reported": "Yes, and it was reported to authorities",
    "yes_unreported": "Yes, but it was not reported",
    # Initiative context
    "regulatory_audit_prep": "Regulatory audit preparation",
    "investor_board_requirement": "Investor or board requirement",
    "customer_due_diligence": "Customer due diligence / vendor questionnaire",
    "proactive_compliance": "Proactive compliance initiative",
    "post_incident_review": "Post-incident review",
    "under_3_months": "Under 3 months",
    "3_to_6_months": "3 to 6 months",
    "6_to_12_months": "6 to 12 months",
    "no_hard_deadline": "No hard deadline",
    "under_5l": "Under Rs. 5 lakh",
    "5l_to_25l": "Rs. 5 lakh to Rs. 25 lakh",
    "25l_to_1cr": "Rs. 25 lakh to Rs. 1 crore",
    "above_1cr": "Above Rs. 1 crore",
    "not_yet_defined": "Not yet defined",
    # Compliance questionnaire
    "fully_implemented": "Fully implemented",
    "partially_implemented": "Partially implemented",
    "planned": "Planned (not yet in place)",
    "not_implemented": "Not implemented",
    "not_applicable": "Not applicable",
}

# Follow-up probes per requirement ID (high-value questions to surface evidence)
FOLLOW_UP_PROBES = {
    "CH2.CONSENT.1": "Can you show me an example of a consent screen or form a user would see?",
    "CH2.CONSENT.2": "If you process data for multiple purposes (e.g., service delivery AND marketing), do users consent to each separately?",
    "CH2.CONSENT.3": "Walk me through how a user would withdraw consent today — what steps, how long does it take?",
    "CH2.CONSENT.5": "How do you verify a user is 18 or older before collecting their data?",
    "CH2.NOTICE.1": "Can you show me the privacy notice a user sees when they first sign up?",
    "CH2.NOTICE.2": "For users who registered before DPDPA came into force — have they received any retrospective communication?",
    "CH2.NOTICE.3": "Where in your notice does a user find who to contact with a privacy question?",
    "CH2.PURPOSE.1": "Has there ever been a case where you used user data for a purpose beyond what was originally disclosed? How was it handled?",
    "CH2.MINIMIZE.2": "What happens to a user's data when they close their account?",
    "CH2.MINIMIZE.3": "Do you have a documented retention schedule? Can I see it?",
    "CH2.SECURITY.1": "What security certifications or penetration tests have you done in the last 12 months?",
    "CH2.SECURITY.2": "Is data encrypted at rest in your primary database and in backups?",
    "CH2.SECURITY.3": "Do your vendor contracts (AWS, CRM, analytics tools) include data processing agreements?",
    "CH3.ACCESS.1": "How would a user request a copy of their personal data today? Walk me through the process.",
    "CH3.CORRECT.1": "If a user says their information is wrong, what's the process to get it corrected?",
    "CH3.CORRECT.2": "If a user asks to be deleted, what systems does their data get removed from?",
    "CH3.GRIEVANCE.1": "Is there a named person responsible for privacy complaints? Is their contact published?",
    "CH3.GRIEVANCE.2": "What is your SLA for responding to a privacy complaint? Is it documented?",
    "CH4.CHILD.1": "Do any of your marketing or targeting systems use age as a signal?",
    "CH4.CHILD.3": "How do you identify if a user is under 18 at sign-up?",
    "CH4.SDF.1": "Has your organization been assessed for Significant Data Fiduciary designation?",
    "CM.RECORDS.1": "Where is consent stored? Can you pull up a record showing when a specific user gave consent?",
    "CM.GRANULAR.2": "Is consent to non-essential data (e.g., analytics, marketing) a condition for using the app?",
    "CB.TRANSFER.1": "Which countries does your data land in? AWS region, CRM vendor location?",
    "BN.NOTIFY.1": "If a breach happened tonight, who is the first person notified internally? Do you have a runbook?",
    "BN.NOTIFY.3": "Do you have a documented incident response plan? When was it last tested?",
}


def fmt_options(options: list[str], q_type: str) -> str:
    """Format answer options as a checklist."""
    prefix = "- [ ]" if q_type == "multi_select" else "- ( )"
    lines = []
    for opt in options:
        label = OPTION_LABELS.get(opt, opt.replace("_", " ").title())
        lines.append(f"  {prefix} {label}")
    return "\n".join(lines)


def generate_guide() -> str:
    lines = []

    lines.append("# DPDPA Assessment — Facilitator's Guide")
    lines.append("")
    lines.append("> **Facilitator instructions:** Work through each section in order.")
    lines.append("> Mark answers as you go. For multi-select questions, tick all that apply.")
    lines.append("> For single-select, circle or tick one. Use the Notes fields to capture")
    lines.append("> verbatim quotes, document references, and follow-up items.")
    lines.append("> Never fill in answers on behalf of the client — capture what they say.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── PHASE 1: CONTEXT QUESTIONS ──────────────────────────────────────────
    lines.append("## Phase 1 — Organizational Context")
    lines.append("")
    lines.append(
        "_Purpose: Build the risk profile used to weight the compliance assessment._"
    )
    lines.append("_Time estimate: 15–20 minutes_")
    lines.append("")

    for block in CONTEXT_BLOCKS:
        lines.append(f"### {block['title']}")
        lines.append(f"_{block['description']}_")
        lines.append("")

        for q in block["questions"]:
            lines.append(f"**{q['id']}** — {q['question']}")
            lines.append("")
            if q.get("depends_on"):
                dep_id, dep_val = next(iter(q["depends_on"].items()))
                dep_label = OPTION_LABELS.get(dep_val, dep_val)
                lines.append(f"> _Only ask if {dep_id} = \"{dep_label}\"_")
                lines.append("")
            if q["type"] in ("single_select", "multi_select"):
                lines.append(fmt_options(q["options"], q["type"]))
                lines.append("")
            else:
                lines.append("  Answer: ___________________________________________")
                lines.append("")
            lines.append("  **Notes / verbatim:** _________________________________")
            lines.append("")
            lines.append("  **Evidence seen:** ____________________________________")
            lines.append("")

        lines.append("---")
        lines.append("")

    # ── PHASE 2: COMPLIANCE QUESTIONNAIRE ───────────────────────────────────
    lines.append("## Phase 2 — DPDPA Compliance Assessment")
    lines.append("")
    lines.append("_Purpose: Assess compliance against all 41 DPDPA requirements._")
    lines.append("_Time estimate: 45–60 minutes_")
    lines.append("")
    lines.append("**Answer options for all questions below:**")
    lines.append("")
    for opt in ANSWER_OPTIONS:
        label = OPTION_LABELS.get(opt, opt)
        lines.append(f"- **{label}**")
    lines.append("")
    lines.append("---")
    lines.append("")

    for chapter_key, chapter in DPDPA_FRAMEWORK.items():
        lines.append(f"## {chapter['title']}")
        lines.append(f"_Chapter weight: {int(chapter['weight'] * 100)}%_")
        lines.append("")

        for section_key, section in chapter["sections"].items():
            lines.append(f"### {section['title']}")
            lines.append("")

            for req in section["requirements"]:
                req_id = req["id"]
                question_text = _QUESTION_TEXT.get(req_id)
                if not question_text:
                    continue

                criticality_badge = {
                    "critical": "🔴 CRITICAL",
                    "high": "🟠 HIGH",
                    "medium": "🟡 MEDIUM",
                    "low": "🟢 LOW",
                }.get(req["criticality"], req["criticality"].upper())

                lines.append(f"**{req_id}** `{criticality_badge}` — {req['section_ref']}")
                lines.append("")
                lines.append(f"> {question_text}")
                lines.append("")

                guidance = _GUIDANCE_TEXT.get(req_id)
                if guidance:
                    lines.append(f"_Guidance: {guidance}_")
                    lines.append("")

                lines.append("  - ( ) Fully implemented")
                lines.append("  - ( ) Partially implemented")
                lines.append("  - ( ) Planned")
                lines.append("  - ( ) Not implemented")
                lines.append("  - ( ) Not applicable")
                lines.append("")

                probe = FOLLOW_UP_PROBES.get(req_id)
                if probe:
                    lines.append(f"  _Probe: {probe}_")
                    lines.append("")

                lines.append("  **Notes / verbatim:** _________________________________")
                lines.append("")
                lines.append("  **Evidence seen:** ____________________________________")
                lines.append("")

        lines.append("---")
        lines.append("")

    lines.append("## Session Close")
    lines.append("")
    lines.append("- Confirm report delivery timeline with client: **48 hours from today**")
    lines.append("- Confirm who should receive the report (name, email):")
    lines.append("  - Name: ___________________________")
    lines.append("  - Email: ___________________________")
    lines.append("- Confirm follow-up call to be booked upon report delivery")
    lines.append("- Thank client and set expectations:")
    lines.append('  _"You will receive a PDF gap report within 48 hours. It will include')
    lines.append("  a compliance score, risk-prioritized gap list, and a remediation roadmap")
    lines.append('  with effort and budget estimates. We will schedule a 30-minute call')
    lines.append('  to walk through findings and discuss next steps."_')
    lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    guide = generate_guide()
    OUTPUT_PATH.write_text(guide, encoding="utf-8")
    print(f"Facilitator guide written to {OUTPUT_PATH}")
    q_count = sum(
        len(b["questions"]) for b in CONTEXT_BLOCKS
    ) + len(_QUESTION_TEXT)
    print(f"  Context questions: {sum(len(b['questions']) for b in CONTEXT_BLOCKS)}")
    print(f"  Compliance questions: {len(_QUESTION_TEXT)}")
    print(f"  Total: {q_count}")
