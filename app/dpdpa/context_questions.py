"""
Phase 1 Context Gathering Questions — organizational intelligence before compliance assessment.

Four blocks: Data Landscape, Existing Posture, Risk Exposure, Initiative Context.
These are NOT compliance questions — they profile the organization to enable adaptive assessment.

The blocks below are the shared base. Privacy-specific blocks/questions carry a `frameworks`
tag and are shown only when a privacy framework is selected; each framework definition can add
its own blocks via `FrameworkDefinition.context_blocks`. Use `get_context_blocks()` to resolve
the wizard for an assessment.
"""

PRIVACY_FRAMEWORKS = frozenset({"dpdpa", "gdpr", "hipaa"})
_PRIVACY = {"frameworks": PRIVACY_FRAMEWORKS}

CONTEXT_BLOCKS = [
    {
        "id": "data_landscape",
        **_PRIVACY,
        "title": "Data Landscape",
        "description": "Understanding what personal data you collect and how it flows.",
        "questions": [
            {
                "id": "CTX.DATA.1",
                "question": "What categories of personal data does your organization collect?",
                "type": "multi_select",
                "options": [
                    "identity",
                    "financial",
                    "health",
                    "biometric",
                    "location",
                    "behavioral",
                    "childrens",
                    "other",
                ],
            },
            {
                "id": "CTX.DATA.2",
                "question": "What is your primary mechanism for collecting personal data?",
                "type": "multi_select",
                "options": [
                    "web_forms",
                    "mobile_app",
                    "third_party_apis",
                    "physical_forms",
                    "automated_tracking",
                ],
            },
            {
                "id": "CTX.DATA.3",
                "question": "Do you use third-party data processors or SaaS vendors who handle personal data on your behalf?",
                "type": "single_select",
                "options": ["yes", "no", "unsure"],
            },
            {
                "id": "CTX.DATA.4",
                "question": "Do you transfer personal data across international borders?",
                "type": "single_select",
                "options": ["yes", "no", "unsure"],
            },
            {
                "id": "CTX.DATA.4a",
                "question": "If yes, which regions do you transfer data to?",
                "type": "text",
                "depends_on": {"CTX.DATA.4": "yes"},
            },
        ],
    },
    {
        "id": "existing_posture",
        "title": "Existing Posture",
        "description": "Your current privacy and security maturity baseline.",
        "questions": [
            {
                "id": "CTX.POSTURE.1",
                **_PRIVACY,
                "question": "Do you have a dedicated privacy or Data Protection Officer function?",
                "type": "single_select",
                "options": ["full_time", "part_time_shared", "no"],
            },
            {
                "id": "CTX.POSTURE.2",
                "question": "Do you have an existing information security program?",
                "type": "single_select",
                "options": [
                    "iso_27001_certified",
                    "soc2",
                    "internal_policy_only",
                    "none",
                ],
            },
            {
                "id": "CTX.POSTURE.3",
                "question": "Have you undergone any privacy or security audit in the past 2 years?",
                "type": "single_select",
                "options": ["external_audit", "internal_only", "no"],
            },
            {
                "id": "CTX.POSTURE.4",
                **_PRIVACY,
                "question": "Do you have a documented privacy policy published to users?",
                "type": "single_select",
                "options": ["yes_recently_updated", "yes_outdated", "no"],
            },
        ],
    },
    {
        "id": "risk_exposure",
        "title": "Risk Exposure",
        "description": "Factors that determine your regulatory exposure and assessment depth.",
        "questions": [
            {
                "id": "CTX.RISK.1",
                **_PRIVACY,
                "question": "Which of the following apply to your organization?",
                "type": "multi_select",
                "options": [
                    "processes_childrens_data",
                    "healthcare_finance_critical_infra",
                    "handles_sensitive_personal_data",
                    "designated_or_likely_sdf",
                    "none",
                ],
            },
            {
                "id": "CTX.RISK.2",
                **_PRIVACY,
                "question": "Roughly how many data principals (individuals whose data you hold) are affected?",
                "type": "single_select",
                "options": [
                    "under_10k",
                    "10k_to_1m",
                    "1m_to_10m",
                    "over_10m",
                ],
            },
            {
                "id": "CTX.RISK.3",
                "question": "In the last 2 years, have you experienced any data breach or security incident?",
                "type": "single_select",
                "options": ["yes_reported", "yes_unreported", "no", "unsure"],
            },
        ],
    },
    {
        "id": "initiative_context",
        "title": "Initiative Context",
        "description": "Why you are doing this assessment and what outcome you need.",
        "questions": [
            {
                "id": "CTX.INIT.1",
                "question": "What is the primary driver for this assessment?",
                "type": "single_select",
                "options": [
                    "regulatory_audit_prep",
                    "investor_board_requirement",
                    "customer_due_diligence",
                    "proactive_compliance",
                    "post_incident_review",
                ],
            },
            {
                "id": "CTX.INIT.2",
                "question": "What is your target compliance timeline?",
                "type": "single_select",
                "options": [
                    "under_3_months",
                    "3_to_6_months",
                    "6_to_12_months",
                    "no_hard_deadline",
                ],
            },
            {
                "id": "CTX.INIT.3",
                "question": "What is your approximate budget band for remediation?",
                "type": "single_select",
                "options": [
                    "under_10k",
                    "10k_to_50k",
                    "50k_to_150k",
                    "above_150k",
                    "not_yet_defined",
                ],
            },
        ],
    },
]


def _applies(item: dict, selected: set[str]) -> bool:
    scope = item.get("frameworks")
    return scope is None or bool(scope & selected)


def get_context_blocks(framework_ids: list[str] | None = None) -> list[dict]:
    """Context-wizard blocks for the selected frameworks.

    Shared blocks are filtered by their `frameworks` tags, then each selected
    framework's own blocks are inserted before the closing Initiative block.
    `None` returns the full unfiltered base list.
    """
    if framework_ids is None:
        return CONTEXT_BLOCKS

    from app.frameworks.registry import FrameworkRegistry

    selected = set(framework_ids)
    blocks = []
    for block in CONTEXT_BLOCKS:
        if not _applies(block, selected):
            continue
        questions = [q for q in block["questions"] if _applies(q, selected)]
        if questions:
            blocks.append({**block, "questions": questions})

    framework_blocks = []
    for fw_id in framework_ids:
        fw = FrameworkRegistry.get_or_none(fw_id)
        if fw:
            framework_blocks.extend(fw.context_blocks)
    insert_at = next(
        (i for i, b in enumerate(blocks) if b["id"] == "initiative_context"), len(blocks)
    )
    return blocks[:insert_at] + framework_blocks + blocks[insert_at:]


def get_context_questions() -> list[dict]:
    """Return the flat list of all context questions with block metadata."""
    questions = []
    for block in CONTEXT_BLOCKS:
        for q in block["questions"]:
            questions.append(
                {
                    **q,
                    "block_id": block["id"],
                    "block_title": block["title"],
                    "block_description": block["description"],
                }
            )
    return questions


def get_context_question_ids() -> set[str]:
    """Return the set of all valid context question IDs."""
    return {q["id"] for q in get_context_questions()}
