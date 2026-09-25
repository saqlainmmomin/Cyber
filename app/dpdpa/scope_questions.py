"""
Phase 0 Scope Questions — 6 questions to determine applicable DPDPA chapters
before evidence is requested.

Industry and company_size are captured at assessment creation, so they are NOT
repeated here. These 6 questions resolve the conditional requirements:
  - Cross-border transfers → CB.TRANSFER.*
  - Children's data       → CH4.CHILD.*, CH2.CONSENT.5
  - SDF designation       → CH4.SDF.*
  - Third-party processors → CH2.SECURITY.3 (relevant for evidence request)
  - Processing context    → informs questionnaire framing
  - s.17(3) notification  → applicability proposal only (never an exclusion)
"""

from app.frameworks.schema import ApplicabilityProposal

SCOPE_QUESTIONS = [
    {
        "id": "SCP.1",
        "question": "Does your organisation transfer personal data outside India?",
        "help_text": "Includes data stored on foreign cloud servers, shared with overseas subsidiaries, or processed by vendors headquartered outside India.",
        "type": "single_select",
        "options": [
            {"value": "yes", "label": "Yes"},
            {"value": "no", "label": "No"},
            {"value": "unsure", "label": "Not sure"},
        ],
    },
    {
        "id": "SCP.2",
        "question": "Does your organisation process personal data of children (under 18)?",
        "help_text": "Includes consumer apps, edtech, gaming, or any service where minors may create accounts or have their data collected.",
        "type": "single_select",
        "options": [
            {"value": "yes", "label": "Yes"},
            {"value": "no", "label": "No"},
            {"value": "unsure", "label": "Not sure"},
        ],
    },
    {
        "id": "SCP.3",
        "question": "Has your organisation been designated (or is likely to be designated) as a Significant Data Fiduciary (SDF)?",
        "help_text": "SDFs are large-scale processors of sensitive data designated by the Central Government. If unsure, select 'Possibly' — we'll assess the likelihood.",
        "type": "single_select",
        "options": [
            {"value": "yes", "label": "Yes — already designated"},
            {"value": "possibly", "label": "Possibly — we meet the likely criteria"},
            {"value": "no", "label": "No"},
        ],
    },
    {
        "id": "SCP.4",
        "question": "What is the primary context of your personal data processing?",
        "help_text": "This shapes which compliance obligations are most relevant.",
        "type": "single_select",
        "options": [
            {"value": "customer", "label": "Customer / user data (B2C or B2B product)"},
            {"value": "employee", "label": "Employee / HR data only"},
            {"value": "both", "label": "Both customer and employee data"},
            {"value": "vendor", "label": "We process data on behalf of clients (Data Processor)"},
        ],
    },
    {
        "id": "SCP.5",
        "question": "Do you use third-party vendors or cloud services that process personal data on your behalf?",
        "help_text": "Examples: CRM software, analytics platforms, payment processors, cloud infrastructure providers.",
        "type": "single_select",
        "options": [
            {"value": "yes", "label": "Yes"},
            {"value": "no", "label": "No"},
            {"value": "unsure", "label": "Not sure"},
        ],
    },
    {
        "id": "SCP.6",
        "question": "Has your organisation been notified by the Central Government under s.17(3) of the DPDP Act (for example, as a startup exempted from certain provisions)?",
        "help_text": "A s.17(3) notification can exempt named Data Fiduciaries or classes of them from s.5, s.8(3), s.8(7), s.10 and s.11. Answering yes only proposes the related requirements as likely not applicable; the consultant confirms each one against the notification. Nothing is excluded automatically.",
        "type": "single_select",
        "options": [
            {"value": "yes", "label": "Yes"},
            {"value": "no", "label": "No"},
            {"value": "unsure", "label": "Not sure"},
        ],
    },
]

# Requirements whose section_ref cites a provision s.17(3) lets the Central
# Government disapply: s.5 (notice), s.8(3) (accuracy), s.8(7) (erasure),
# s.10 (SDF) and s.11 (access). CH2.NOTICE.3 rests on s.6(3), s.8(9) and r.9,
# which s.17(3) does not name, so it is not proposed.
S17_3_REQUIREMENT_IDS = (
    "CH2.NOTICE.1", "CH2.NOTICE.2",
    "CH2.ACCURACY.1",
    "CH2.MINIMIZE.2", "CH2.MINIMIZE.3",
    "CH4.SDF.1", "CH4.SDF.2", "CH4.SDF.3", "CH4.SDF.4",
    "CH3.ACCESS.1",
)

APPLICABILITY_PROPOSALS = [
    ApplicabilityProposal(
        scope_question_id="SCP.6",
        answers=("yes",),
        control_ids=S17_3_REQUIREMENT_IDS,
        rationale=(
            "Scope answer: notified under DPDP Act s.17(3). Proposal only, for the consultant "
            "to confirm: obtain the notification and check that it covers this organisation "
            "and names the provision this requirement rests on (s.5, s.8(3), s.8(7), s.10 or "
            "s.11) before recording it as not applicable. The requirement stays in scope until "
            "then."
        ),
    ),
]


def get_scope_question_ids() -> set[str]:
    return {q["id"] for q in SCOPE_QUESTIONS}
