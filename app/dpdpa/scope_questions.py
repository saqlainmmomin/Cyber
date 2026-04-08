"""
Phase 0 Scope Questions — 5 questions to determine applicable DPDPA chapters
before evidence is requested.

Industry and company_size are captured at assessment creation, so they are NOT
repeated here. These 5 questions resolve the conditional requirements:
  - Cross-border transfers → CB.TRANSFER.*
  - Children's data       → CH4.CHILD.*, CH2.CONSENT.5
  - SDF designation       → CH4.SDF.*
  - Third-party processors → CH2.SECURITY.3 (relevant for evidence request)
  - Processing context    → informs questionnaire framing
"""

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
]


def get_scope_question_ids() -> set[str]:
    return {q["id"] for q in SCOPE_QUESTIONS}
