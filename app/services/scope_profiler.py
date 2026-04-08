"""
Scope Profiler — deterministic requirement filtering and evidence checklist generation.

Given scope answers (SCP.1–SCP.5) plus industry + company_size from the Assessment,
produces:
  - applicable_requirements: list of requirement IDs to include in questionnaire + analysis
  - excluded_requirements: list of requirement IDs excluded with reason
  - evidence_checklist: list of document types the client should provide, with justification
"""

from app.dpdpa.framework import get_all_requirements

# Requirements that are only active when children's data is processed
CHILDREN_REQUIREMENT_IDS = {
    "CH2.CONSENT.5",  # Verifiable parental consent
    "CH4.CHILD.1",    # No tracking/behavioural monitoring of children
    "CH4.CHILD.2",    # No processing detrimental to child's well-being
    "CH4.CHILD.3",    # Age verification mechanism
}

# Requirements that are only active for Significant Data Fiduciaries
SDF_REQUIREMENT_IDS = {
    "CH4.SDF.1",  # DPO appointed
    "CH4.SDF.2",  # Independent Data Auditor
    "CH4.SDF.3",  # DPIA conducted
    "CH4.SDF.4",  # Periodic audit
}

# Requirements that are only active when cross-border transfers occur
CROSS_BORDER_REQUIREMENT_IDS = {
    "CB.TRANSFER.1",  # Transfers only to non-restricted jurisdictions
    "CB.TRANSFER.2",  # Contractual safeguards
    "CB.TRANSFER.3",  # Data localisation
}

# Requirement that is only relevant when third-party processors are used
PROCESSOR_REQUIREMENT_IDS = {
    "CH2.SECURITY.3",  # Data Processor contractual safeguards
}


def compute_scope(scope_answers: dict, industry: str, company_size: str) -> dict:
    """
    Compute applicable requirements and evidence checklist from scope answers.

    Args:
        scope_answers: dict mapping SCP.* question IDs to answer values
        industry: assessment industry (from creation form)
        company_size: assessment company_size (from creation form)

    Returns:
        {
          "applicable_requirements": [...],    # list of req IDs
          "excluded_requirements": [           # list of {id, reason}
              {"id": "CH4.SDF.1", "reason": "SDF designation: no"},
              ...
          ],
          "evidence_checklist": [...],         # list of {document_type, label, reason, required, maps_to}
          "flags": {...},                      # parsed boolean flags for downstream use
        }
    """
    cross_border = scope_answers.get("SCP.1", "unsure")
    children = scope_answers.get("SCP.2", "unsure")
    sdf = scope_answers.get("SCP.3", "no")
    processing_context = scope_answers.get("SCP.4", "both")
    has_processors = scope_answers.get("SCP.5", "unsure")

    # Resolve booleans (unsure → treated as possibly applicable → include)
    cross_border_active = cross_border in ("yes", "unsure")
    children_active = children in ("yes", "unsure")
    sdf_active = sdf in ("yes", "possibly")
    processors_active = has_processors in ("yes", "unsure")

    all_reqs = get_all_requirements()
    all_ids = {r["id"] for r in all_reqs}

    excluded: list[dict] = []

    def _exclude(ids: set[str], reason: str):
        for rid in ids:
            if rid in all_ids:
                excluded.append({"id": rid, "reason": reason})

    if not cross_border_active:
        _exclude(CROSS_BORDER_REQUIREMENT_IDS, "Cross-border transfers: not applicable")
    if not children_active:
        _exclude(CHILDREN_REQUIREMENT_IDS, "Children's data: not applicable")
    if not sdf_active:
        _exclude(SDF_REQUIREMENT_IDS, "SDF designation: not applicable")
    if not processors_active:
        _exclude(PROCESSOR_REQUIREMENT_IDS, "Third-party processors: not applicable")

    excluded_ids = {e["id"] for e in excluded}
    applicable = [rid for rid in [r["id"] for r in all_reqs] if rid not in excluded_ids]

    checklist = _build_evidence_checklist(
        cross_border_active=cross_border_active,
        children_active=children_active,
        sdf_active=sdf_active,
        processors_active=processors_active,
        processing_context=processing_context,
        industry=industry,
    )

    return {
        "applicable_requirements": applicable,
        "excluded_requirements": excluded,
        "evidence_checklist": checklist,
        "flags": {
            "cross_border": cross_border_active,
            "children": children_active,
            "sdf": sdf_active,
            "processors": processors_active,
            "processing_context": processing_context,
        },
    }


def _build_evidence_checklist(
    cross_border_active: bool,
    children_active: bool,
    sdf_active: bool,
    processors_active: bool,
    processing_context: str,
    industry: str,
) -> list[dict]:
    """
    Build an ordered evidence checklist. Each item has:
      - document_type: machine-readable key (maps to DocumentCategory enum)
      - label: human-readable name
      - reason: why this is required
      - required: True = must have, False = recommended
      - maps_to: list of requirement IDs this document addresses
    """
    checklist = []

    def _add(document_type, label, reason, required, maps_to):
        checklist.append({
            "document_type": document_type,
            "label": label,
            "reason": reason,
            "required": required,
            "maps_to": maps_to,
        })

    # --- Always required ---
    _add(
        "privacy_policy",
        "Privacy Policy / Privacy Notice",
        "Assessed against notice obligations (Sections 5, 6)",
        True,
        ["CH2.NOTICE.1", "CH2.NOTICE.2", "CH2.NOTICE.3", "CH2.CONSENT.1"],
    )
    _add(
        "consent_forms",
        "Consent forms / consent collection screenshots",
        "Assessed for consent validity, granularity, and withdrawal mechanism",
        True,
        ["CH2.CONSENT.1", "CH2.CONSENT.2", "CH2.CONSENT.3", "CM.GRANULAR.1", "CM.GRANULAR.2"],
    )
    _add(
        "retention_policy",
        "Data retention schedule / policy",
        "Assessed for storage limitation and deletion procedures",
        True,
        ["CH2.MINIMIZE.2", "CH2.MINIMIZE.3"],
    )
    _add(
        "breach_procedure",
        "Breach notification procedure / incident response plan",
        "Assessed against breach notification obligations (Section 8(6))",
        True,
        ["BN.NOTIFY.1", "BN.NOTIFY.2", "BN.NOTIFY.3"],
    )
    _add(
        "grievance_mechanism",
        "Grievance redressal mechanism documentation",
        "Must demonstrate accessible grievance channel with named officer",
        True,
        ["CH3.GRIEVANCE.1", "CH3.GRIEVANCE.2"],
    )
    _add(
        "security_policy",
        "Information security policy / controls documentation",
        "Assessed for reasonable security safeguards (Section 8(4))",
        True,
        ["CH2.SECURITY.1", "CH2.SECURITY.2"],
    )

    # --- Recommended always ---
    _add(
        "data_flow_diagram",
        "Data flow diagram / data inventory / ROPA",
        "Helps assess data minimization and purpose limitation",
        False,
        ["CH2.MINIMIZE.1", "CH2.PURPOSE.1", "CH2.PURPOSE.2"],
    )

    # --- Conditional: processors ---
    if processors_active:
        _add(
            "vendor_agreements",
            "Vendor / Data Processor agreements (DPAs)",
            "Assessed for processor contractual safeguards (Section 8(2))",
            True,
            ["CH2.SECURITY.3"],
        )

    # --- Conditional: cross-border ---
    if cross_border_active:
        _add(
            "cross_border_safeguards",
            "Cross-border transfer safeguards / international DPAs",
            "Assessed against Section 16 transfer restrictions",
            True,
            ["CB.TRANSFER.1", "CB.TRANSFER.2", "CB.TRANSFER.3"],
        )

    # --- Conditional: children ---
    if children_active:
        _add(
            "age_verification",
            "Age verification mechanism documentation",
            "Required to verify children's data protections are implemented",
            True,
            ["CH4.CHILD.3", "CH2.CONSENT.5"],
        )
        _add(
            "parental_consent",
            "Parental consent forms / guardian verification process",
            "Assessed for verifiable parental consent (Section 9(1))",
            True,
            ["CH2.CONSENT.5", "CH4.CHILD.1", "CH4.CHILD.2"],
        )

    # --- Conditional: SDF ---
    if sdf_active:
        _add(
            "dpo_appointment",
            "Data Protection Officer (DPO) appointment documentation",
            "SDF obligation — DPO must be India-based (Section 10(2)(a))",
            True,
            ["CH4.SDF.1"],
        )
        _add(
            "dpia_reports",
            "Data Protection Impact Assessment (DPIA) reports",
            "SDF obligation — periodic DPIAs required (Section 10(2)(c))",
            True,
            ["CH4.SDF.3"],
        )
        _add(
            "audit_reports",
            "Privacy / compliance audit reports",
            "SDF obligation — periodic audits required (Section 10(2)(d))",
            False,
            ["CH4.SDF.4", "CH4.SDF.2"],
        )

    # --- Employee data context ---
    if processing_context in ("employee", "both"):
        _add(
            "hr_privacy_notices",
            "Employee privacy notices / HR data policy",
            "Employee data has legitimate use basis under Section 7 — policy evidence needed",
            False,
            ["CH2.PURPOSE.2", "CH2.NOTICE.1"],
        )

    return checklist
