"""
DPDPA Questionnaire — one question per requirement, mapped by requirement ID.
"""

from app.dpdpa.framework import get_all_requirements

ANSWER_OPTIONS = [
    "fully_implemented",
    "partially_implemented",
    "planned",
    "not_implemented",
    "not_applicable",
]

# Backward-compatible mapping from old 4-option scale
LEGACY_ANSWER_MAP = {
    "yes": "fully_implemented",
    "partial": "partially_implemented",
    "no": "not_implemented",
    "not_applicable": "not_applicable",
}

# Question text for each requirement ID
_QUESTION_TEXT = {
    # Chapter 2 — Consent
    "CH2.CONSENT.1": "Does your organization obtain free, specific, informed, and unambiguous consent from data principals before processing their personal data?",
    "CH2.CONSENT.2": "When processing data for multiple purposes, do you obtain separate (itemised) consent for each purpose?",
    "CH2.CONSENT.3": "Can data principals withdraw their consent as easily as they gave it, and do you stop processing upon withdrawal?",
    "CH2.CONSENT.4": "If you use a Consent Manager, is it registered with the Data Protection Board and does it provide a transparent consent management platform?",
    "CH2.CONSENT.5": "Do you obtain verifiable parental or guardian consent before processing personal data of children (under 18) or persons with disabilities?",
    # Chapter 2 — Notice
    "CH2.NOTICE.1": "Do you provide a clear privacy notice to data principals at or before the time of collecting their personal data, describing what data is collected and why?",
    "CH2.NOTICE.2": "For personal data collected before the DPDPA came into effect, have you provided a retrospective notice to data principals?",
    "CH2.NOTICE.3": "Does your privacy notice include contact details of a Data Protection Officer or designated grievance officer?",
    # Chapter 2 — Purpose Limitation
    "CH2.PURPOSE.1": "Is personal data processed only for the specific purpose for which consent was obtained or a legitimate use applies?",
    "CH2.PURPOSE.2": "Have you documented all cases where you process personal data without consent under the legitimate use provisions (Section 7)?",
    # Chapter 2 — Data Minimization
    "CH2.MINIMIZE.1": "Do you limit the collection of personal data to only what is necessary for the stated purpose?",
    "CH2.MINIMIZE.2": "Is personal data erased once the purpose for which it was collected is no longer being served?",
    "CH2.MINIMIZE.3": "Do you maintain documented data retention schedules with systematic deletion procedures?",
    # Chapter 2 — Accuracy
    "CH2.ACCURACY.1": "Do you make reasonable efforts to ensure personal data remains complete, accurate, and not misleading?",
    # Chapter 2 — Security
    "CH2.SECURITY.1": "Have you implemented reasonable technical and organizational security safeguards to protect personal data from breaches?",
    "CH2.SECURITY.2": "Is personal data encrypted at rest and in transit, with access controls based on the principle of least privilege?",
    "CH2.SECURITY.3": "Do you have valid contracts with all Data Processors that include obligations for security safeguards and processing instructions?",
    # Chapter 3 — Rights
    "CH3.ACCESS.1": "Can data principals request and receive a summary of their personal data and the processing activities you undertake on it?",
    "CH3.CORRECT.1": "Can data principals request correction of inaccurate or misleading personal data and completion of incomplete data?",
    "CH3.CORRECT.2": "Can data principals request erasure of personal data that is no longer necessary for the original purpose?",
    "CH3.GRIEVANCE.1": "Do you have an accessible grievance redressal mechanism with a designated person or officer to handle data principal complaints?",
    "CH3.GRIEVANCE.2": "Do you respond to data principal grievances within a reasonable timeframe and inform them of their right to approach the Data Protection Board?",
    "CH3.NOMINATE.1": "Can data principals nominate another individual to exercise their rights in the event of death or incapacity?",
    # Chapter 4 — Children
    "CH4.CHILD.1": "Does your organization refrain from tracking, behavioural monitoring, or targeted advertising directed at children?",
    "CH4.CHILD.2": "Do you ensure that processing of children's personal data does not have a detrimental effect on their well-being?",
    "CH4.CHILD.3": "Do you have age verification mechanisms to identify children and apply appropriate data protections?",
    # Chapter 4 — SDF
    "CH4.SDF.1": "If your organization is (or may be) designated as a Significant Data Fiduciary, have you appointed a Data Protection Officer based in India?",
    "CH4.SDF.2": "Have you appointed an independent Data Auditor to evaluate your compliance with the DPDPA?",
    "CH4.SDF.3": "Do you conduct periodic Data Protection Impact Assessments (DPIAs) for your processing activities?",
    "CH4.SDF.4": "Do you conduct periodic compliance audits of your data processing activities as prescribed?",
    # Consent Management
    "CM.RECORDS.1": "Do you maintain auditable records of when, how, and for what purpose consent was obtained from each data principal?",
    "CM.RECORDS.2": "Do you have a process to refresh or re-obtain consent when processing purposes change?",
    "CM.GRANULAR.1": "Can data principals provide or withhold consent at a granular per-purpose level?",
    "CM.GRANULAR.2": "Is access to your services independent of consent to non-essential data processing (i.e., no consent bundling or dark patterns)?",
    # Cross-Border
    "CB.TRANSFER.1": "Do you transfer personal data only to countries not restricted by the Central Government, and maintain an inventory of cross-border data flows?",
    "CB.TRANSFER.2": "Do you have contractual or legal safeguards in place for data transferred outside India?",
    "CB.TRANSFER.3": "Where mandated, do you store certain categories of personal data within India (data localisation)?",
    # Breach Notification
    "BN.NOTIFY.1": "Do you have procedures to notify the Data Protection Board of India in case of a personal data breach?",
    "BN.NOTIFY.2": "Do you have procedures to notify affected data principals in case of a personal data breach?",
    "BN.NOTIFY.3": "Do you have a documented incident response plan covering detection, containment, investigation, notification, and remediation?",
    "BN.NOTIFY.4": "Do you maintain a register of all personal data breaches including facts, effects, and remedial actions?",
}

# Guidance text per question (helps the person answering)
_GUIDANCE_TEXT = {
    "CH2.CONSENT.1": "DPDPA Section 6 requires consent to be obtained through a clear affirmative action, presented in clear plain language with the purpose specified.",
    "CH2.CONSENT.2": "Section 6 requires separate consent for each distinct processing purpose. Look for itemised consent prompts that clearly distinguish purposes, evidence that bundled or combined consent is not used, and records showing which specific purposes each Data Principal consented to.",
    "CH2.CONSENT.3": "Section 6(6) mandates that withdrawal of consent must be as easy as giving consent.",
    "CH2.CONSENT.4": "Section 6(6) and the Consent Manager framework expect that where a Consent Manager is used, it is registered with the Data Protection Board. Look for evidence of registration, platform transparency, and that the Consent Manager provides mechanisms for Data Principals to give, withdraw, and manage consent.",
    "CH2.CONSENT.5": "Section 9(1) requires verifiable parental consent for processing children's data. Children are defined as under 18.",
    "CH2.NOTICE.1": "Section 5 requires a notice describing data collected, purpose, and how to exercise rights.",
    "CH2.NOTICE.2": "Section 5 expects retrospective notice for personal data collected before the DPDPA came into effect. Look for a process to identify pre-Act data, notification mechanisms, and evidence that notice was issued to affected Data Principals within the prescribed timeframe.",
    "CH2.NOTICE.3": "Section 5 requires the privacy notice to include contact details of a Data Protection Officer or designated grievance officer. Look for a named individual, published contact details, and evidence that the notice is accessible at the point of collection.",
    "CH2.PURPOSE.1": "Section 6 limits processing of personal data to the specific purpose for which consent was obtained. Look for purpose documentation, controls preventing purpose creep, and evidence that secondary processing is blocked or re-consented.",
    "CH2.PURPOSE.2": "Section 7 defines legitimate uses where processing may proceed without consent. Look for a documented register of legitimate-use cases, evidence that each case meets the Section 7 criteria, and review of the register when processing activities change.",
    "CH2.MINIMIZE.1": "Section 8(2) requires that collection of personal data is limited to what is necessary for the stated purpose. Look for data collection forms and fields justified against purpose, evidence of unnecessary fields being removed, and minimization reviews when processing scope changes.",
    "CH2.MINIMIZE.2": "Section 8(2) requires erasure of personal data once the purpose for which it was collected is no longer being served. Look for retention-to-purpose mapping, automated deletion triggers, and evidence that data is actually removed when the retention period expires.",
    "CH2.MINIMIZE.3": "Section 8(2) expects documented data retention schedules with systematic deletion procedures. Look for a retention policy defining retention periods per data category, deletion workflows, and evidence that schedules are reviewed and approved.",
    "CH2.ACCURACY.1": "Section 8(3) requires the Data Fiduciary to make reasonable efforts to ensure personal data is complete, accurate, and not misleading. Look for data quality controls, validation checks at collection, periodic reviews, and mechanisms to correct data when inaccuracies are identified.",
    "CH2.SECURITY.1": "Section 8(4) requires 'reasonable security safeguards' — this includes both technical measures (encryption, access controls) and organizational measures (policies, training).",
    "CH2.SECURITY.2": "Section 8(4) expects encryption of personal data at rest and in transit, with access controls based on least privilege. Look for encryption standards and algorithms, key management practices, role-based access enforcement, and evidence that access is reviewed periodically.",
    "CH2.SECURITY.3": "Section 8(5) requires valid contracts with Data Processors that include security safeguards and processing instructions. Look for executed processor agreements, defined security obligations, audit rights, and evidence that processor compliance is verified.",
    "CH3.ACCESS.1": "Section 11 grants Data Principals the right to request a summary of their personal data and the processing activities undertaken on it. Look for an access request workflow, identity verification, response templates, and evidence that summaries are provided within a reasonable timeframe.",
    "CH3.CORRECT.1": "Section 12 grants Data Principals the right to request correction of inaccurate or misleading personal data and completion of incomplete data. Look for a correction workflow, downstream update propagation, and evidence that corrections are applied across all affected systems.",
    "CH3.CORRECT.2": "Section 12 includes the right to erasure of personal data that is no longer necessary for the original purpose. Look for erasure request handling, technical deletion procedures, and evidence that data is removed from both primary and backup systems.",
    "CH3.GRIEVANCE.1": "Section 13 requires a grievance mechanism. This should be accessible and have a designated responsible person.",
    "CH3.GRIEVANCE.2": "Section 13 expects the Data Fiduciary to respond to grievances within a reasonable timeframe and inform the Data Principal of their right to approach the Data Protection Board if dissatisfied. Look for SLA-defined response times, escalation procedures, and evidence of Board-referral information being communicated.",
    "CH3.NOMINATE.1": "Section 12 allows Data Principals to nominate another individual to exercise their rights in the event of death or incapacity. Look for a nomination mechanism, validation of nominee identity, and evidence that nominations are recorded and honoured.",
    "CH4.CHILD.1": "Section 9(2) explicitly prohibits tracking and behavioural monitoring of children.",
    "CH4.CHILD.2": "Section 9(3) requires that processing of children's personal data does not have a detrimental effect on their well-being. Look for impact assessments specific to children's data, safeguards preventing harmful processing, and evidence that processing decisions consider the child's best interest.",
    "CH4.CHILD.3": "Section 9(1) requires age verification mechanisms to identify children before processing their data. Look for age-gate controls, verification methods, and evidence that children's data is flagged and handled with elevated protections.",
    "CH4.SDF.1": "Section 10 requires Significant Data Fiduciaries to appoint a Data Protection Officer based in India. Look for a formal appointment, DPO reporting structure, independence from processing operations, and evidence that the DPO is engaged in ongoing oversight.",
    "CH4.SDF.2": "Section 10 requires Significant Data Fiduciaries to appoint an independent Data Auditor to evaluate DPDPA compliance. Look for the auditor's appointment, scope of audit, independence from the assessed functions, and evidence of periodic audit reports reaching accountable leadership.",
    "CH4.SDF.3": "Section 10 requires Significant Data Fiduciaries to conduct periodic Data Protection Impact Assessments. Look for DPIA methodology, processing activities assessed, risk identification and treatment, and evidence that DPIA outcomes feed into control improvements.",
    "CH4.SDF.4": "Section 10 requires Significant Data Fiduciaries to conduct periodic compliance audits. Look for an audit plan, frequency defined by risk, audit findings tracking, and evidence that remediation is completed and verified.",
    "CM.GRANULAR.1": "Section 6 expects consent to be granular, allowing Data Principals to provide or withhold consent at a per-purpose level. Look for per-purpose consent toggles in the interface, evidence that purposes are clearly separated, and that partial consent does not block essential processing.",
    "CM.GRANULAR.2": "Section 6 prohibits consent bundling and dark patterns. Look for evidence that access to services is not conditioned on consent for non-essential processing, that consent interfaces are free of manipulative design, and that Data Principals can decline non-essential processing without losing core service access.",
    "CM.RECORDS.1": "Section 6 expects auditable records of consent capture including when, how, and for what purpose consent was obtained. Look for consent logs capturing timestamp, method, purpose, and version of the consent notice presented, and evidence that records are retained for the required period.",
    "CM.RECORDS.2": "Section 6 expects a process to refresh or re-obtain consent when processing purposes change. Look for triggers that detect purpose changes, re-consent workflows, and evidence that stale consent is not relied upon for new processing.",
    "CB.TRANSFER.1": "Section 16 allows transfers only to countries not blacklisted by the Central Government.",
    "CB.TRANSFER.2": "Section 16 requires contractual or legal safeguards for personal data transferred outside India. Look for data transfer agreements, standard contractual clauses, or other approved mechanisms, and evidence that safeguards are reviewed when transfer destinations change.",
    "CB.TRANSFER.3": "Section 16 empowers the Central Government to notify countries or categories of personal data that must remain in India. Look for awareness of applicable localisation requirements, data residency controls, and evidence that storage location is validated against the current negative list.",
    "BN.NOTIFY.1": "Section 8(6) mandates notification to the Board in prescribed form and manner for every personal data breach.",
    "BN.NOTIFY.2": "Section 8(6) requires the Data Fiduciary to notify affected Data Principals of a personal data breach. Look for documented notification procedures, message templates, and evidence of timely communication to affected individuals.",
    "BN.NOTIFY.3": "Section 8(5) expects the Data Fiduciary to maintain an incident response plan covering detection, containment, investigation, notification, and remediation. Look for an approved plan, defined roles, escalation paths, and evidence of periodic testing or tabletop exercises.",
    "BN.NOTIFY.4": "Section 8(5) expects a breach register documenting facts, effects, and remedial actions for every personal data breach. Look for a maintained register with entries capturing breach description, affected data categories, mitigation steps, and dates of notification to the Board and Data Principals.",
}


def build_questionnaire(context_profile: dict | None = None) -> list[dict]:
    """
    Build the full questionnaire from the framework.

    If context_profile is provided (from Phase 1), questions are annotated with:
    - relevance_weight: float multiplier based on org risk profile
    - context_note: industry/org-specific guidance
    - skip_if: reason to skip this question (e.g., not SDF)
    """
    not_applicable = set(context_profile.get("likely_not_applicable", [])) if context_profile else set()

    questions = []
    for req in get_all_requirements():
        req_id = req["id"]
        if req_id not in _QUESTION_TEXT:
            continue

        q = {
            "id": req_id,
            "chapter": req["chapter"],
            "chapter_title": req["chapter_title"],
            "section": req["section"],
            "section_title": req["section_title"],
            "question": _QUESTION_TEXT[req_id],
            "guidance": _GUIDANCE_TEXT.get(req_id, ""),
            "criticality": req["criticality"],
            "section_ref": req["section_ref"],
            "answer_options": ANSWER_OPTIONS,
        }

        # Add context-aware annotations if profile exists
        if context_profile:
            q["relevance_weight"] = _compute_relevance(req, context_profile)
            q["context_note"] = _build_context_note(req, context_profile)
            q["skip_if"] = (
                f"Likely not applicable: {req_id} flagged as not relevant for this organization"
                if req_id in not_applicable
                else None
            )
        else:
            q["relevance_weight"] = 1.0
            q["context_note"] = None
            q["skip_if"] = None

        questions.append(q)
    return questions


def _compute_relevance(req: dict, profile: dict) -> float:
    """Compute relevance weight for a requirement based on org profile."""
    weight = 1.0

    priority_chapters = profile.get("priority_chapters", [])
    if req["chapter"] in priority_chapters[:2]:
        weight *= 1.3

    if req["criticality"] == "critical" and profile.get("risk_tier") == "HIGH":
        weight *= 1.2

    if req["id"] in profile.get("likely_not_applicable", []):
        weight *= 0.3

    return round(weight, 2)


def _build_context_note(req: dict, profile: dict) -> str | None:
    """Build a context-specific note for this requirement based on org profile."""
    notes = []

    if profile.get("industry_context") and req["criticality"] == "critical":
        notes.append(profile["industry_context"])

    if profile.get("sdf_candidate") and req["chapter"] == "chapter_4" and "SDF" in req["id"]:
        notes.append(
            "Your organization is identified as a likely Significant Data Fiduciary — "
            "these requirements are mandatory for you."
        )

    if profile.get("cross_border_transfers") and req["chapter"] == "cross_border":
        notes.append("You indicated cross-border data transfers — these requirements are directly applicable.")

    if profile.get("processes_children_data") and "CHILD" in req["id"]:
        notes.append("You process children's data — heightened requirements apply under Section 9.")

    return " ".join(notes) if notes else None
