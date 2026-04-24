"""
DPDPA framework definition — wraps existing app.dpdpa.framework into the
generic FrameworkDefinition schema.

This is a thin adapter: the source of truth remains app/dpdpa/framework.py.
"""

from app.dpdpa.framework import (
    DPDPA_FRAMEWORK,
    REQUIREMENT_DEPENDENCIES,
    ROOT_CAUSE_CLUSTERS,
)
from app.dpdpa.questionnaire import _GUIDANCE_TEXT, _QUESTION_TEXT
from app.dpdpa.scope_questions import SCOPE_QUESTIONS
from app.frameworks.schema import (
    Control,
    Domain,
    FrameworkDefinition,
    QuestionDef,
    RedFlagPattern,
    ScopeQuestion,
    Section,
)

# ── Semantic tags per control ─────────────────────────────────────────────
# Tags enable cross-framework mapping via Unified Control Clusters.

_CONTROL_TAGS: dict[str, list[str]] = {
    "CH2.CONSENT.1": ["consent", "lawful-basis", "data-collection"],
    "CH2.CONSENT.2": ["consent", "purpose-limitation", "granular-consent"],
    "CH2.CONSENT.3": ["consent", "consent-withdrawal", "data-subject-rights"],
    "CH2.CONSENT.4": ["consent", "consent-management", "third-party"],
    "CH2.CONSENT.5": ["consent", "children-data", "parental-consent", "age-verification"],
    "CH2.NOTICE.1": ["privacy-notice", "transparency", "data-collection"],
    "CH2.NOTICE.2": ["privacy-notice", "transparency", "legacy-data"],
    "CH2.NOTICE.3": ["privacy-notice", "dpo", "contact-information"],
    "CH2.PURPOSE.1": ["purpose-limitation", "lawful-basis"],
    "CH2.PURPOSE.2": ["purpose-limitation", "lawful-basis", "legitimate-interest"],
    "CH2.MINIMIZE.1": ["data-minimization", "data-collection"],
    "CH2.MINIMIZE.2": ["data-retention", "data-deletion", "storage-limitation"],
    "CH2.MINIMIZE.3": ["data-retention", "retention-schedule", "data-deletion"],
    "CH2.ACCURACY.1": ["data-accuracy", "data-quality"],
    "CH2.SECURITY.1": ["security-safeguards", "technical-measures", "organizational-measures"],
    "CH2.SECURITY.2": ["encryption", "access-control", "least-privilege"],
    "CH2.SECURITY.3": ["processor-management", "contracts", "third-party"],
    "CH3.ACCESS.1": ["data-subject-rights", "right-of-access", "transparency"],
    "CH3.CORRECT.1": ["data-subject-rights", "right-to-rectification", "data-accuracy"],
    "CH3.CORRECT.2": ["data-subject-rights", "right-to-erasure", "data-deletion"],
    "CH3.GRIEVANCE.1": ["grievance-redressal", "complaints", "data-subject-rights"],
    "CH3.GRIEVANCE.2": ["grievance-redressal", "complaints", "response-timeline"],
    "CH3.NOMINATE.1": ["data-subject-rights", "nomination", "death-incapacity"],
    "CH4.CHILD.1": ["children-data", "tracking", "behavioral-monitoring", "advertising"],
    "CH4.CHILD.2": ["children-data", "wellbeing", "harm-prevention"],
    "CH4.CHILD.3": ["children-data", "age-verification"],
    "CH4.SDF.1": ["dpo", "governance", "significant-data-fiduciary"],
    "CH4.SDF.2": ["audit", "governance", "independent-auditor"],
    "CH4.SDF.3": ["dpia", "risk-assessment", "governance"],
    "CH4.SDF.4": ["audit", "compliance-audit", "governance"],
    "CM.RECORDS.1": ["consent", "consent-records", "audit-trail"],
    "CM.RECORDS.2": ["consent", "consent-refresh", "purpose-change"],
    "CM.GRANULAR.1": ["consent", "granular-consent", "purpose-limitation"],
    "CM.GRANULAR.2": ["consent", "consent-bundling", "dark-patterns"],
    "CB.TRANSFER.1": ["cross-border", "data-transfer", "data-flow-inventory"],
    "CB.TRANSFER.2": ["cross-border", "data-transfer", "contractual-safeguards"],
    "CB.TRANSFER.3": ["data-localization", "cross-border", "data-residency"],
    "BN.NOTIFY.1": ["breach-notification", "regulatory-notification", "incident-response"],
    "BN.NOTIFY.2": ["breach-notification", "data-subject-notification", "incident-response"],
    "BN.NOTIFY.3": ["incident-response", "incident-response-plan", "breach-management"],
    "BN.NOTIFY.4": ["breach-register", "incident-response", "record-keeping"],
}

# ── Red flag patterns for DPDPA prompts ───────────────────────────────────

_RED_FLAG_PATTERNS = [
    RedFlagPattern(
        pattern="GDPR copy-paste language",
        description="Look for 'legitimate interest', 'right to be forgotten', 'data subject', 'DPO with EU scope' — these are GDPR terms, not DPDPA.",
        severity="high",
    ),
    RedFlagPattern(
        pattern="Template artifacts",
        description="Placeholders like '[Company Name]', generic language, or clearly template-derived text.",
        severity="medium",
    ),
    RedFlagPattern(
        pattern="CCPA artifacts",
        description="'Do Not Sell', 'California', specific CCPA categorizations in an Indian privacy policy.",
        severity="high",
    ),
    RedFlagPattern(
        pattern="Buried consent",
        description="Consent hidden in T&Cs, bundled consent, pre-checked boxes, no clear affirmative action.",
        severity="high",
    ),
    RedFlagPattern(
        pattern="Missing DPDPA timelines",
        description="No mention of 72-hour breach notification, no specific Indian regulatory references.",
        severity="medium",
    ),
    RedFlagPattern(
        pattern="Policy without implementation evidence",
        description="Policy document exists but no evidence of operational implementation (training records, audit logs, access reviews).",
        severity="high",
    ),
]


def _build_dpdpa_definition() -> FrameworkDefinition:
    """Convert existing DPDPA_FRAMEWORK dict into FrameworkDefinition."""

    domains: dict[str, Domain] = {}

    for chapter_key, chapter in DPDPA_FRAMEWORK.items():
        sections: dict[str, Section] = {}

        for section_key, section in chapter["sections"].items():
            controls = []
            for req in section["requirements"]:
                controls.append(
                    Control(
                        id=req["id"],
                        title=req["title"],
                        description=req["description"],
                        reference=req["section_ref"],
                        criticality=req["criticality"],
                        tags=_CONTROL_TAGS.get(req["id"], []),
                    )
                )
            sections[section_key] = Section(
                key=section_key,
                title=section["title"],
                weight=section["weight"],
                controls=controls,
            )

        domains[chapter_key] = Domain(
            key=chapter_key,
            title=chapter["title"],
            weight=chapter["weight"],
            sections=sections,
        )

    # Build question definitions from existing questionnaire module
    questions: dict[str, QuestionDef] = {}
    for req_id, text in _QUESTION_TEXT.items():
        questions[req_id] = QuestionDef(
            control_id=req_id,
            question=text,
            guidance=_GUIDANCE_TEXT.get(req_id, ""),
        )

    # Convert scope questions
    scope_qs = [
        ScopeQuestion(
            id=sq["id"],
            question=sq["question"],
            help_text=sq["help_text"],
            type=sq["type"],
            options=sq["options"],
        )
        for sq in SCOPE_QUESTIONS
    ]

    return FrameworkDefinition(
        id="dpdpa",
        name="India DPDPA",
        version="2023",
        description="Digital Personal Data Protection Act, 2023 (India)",
        domains=domains,
        dependencies=REQUIREMENT_DEPENDENCIES,
        root_cause_clusters=ROOT_CAUSE_CLUSTERS,
        scope_questions=scope_qs,
        questions=questions,
        red_flag_patterns=_RED_FLAG_PATTERNS,
    )


# Singleton — built once at import time
DPDPA_DEFINITION = _build_dpdpa_definition()
