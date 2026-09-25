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
    "CH2.CONSENT.2": "When processing data for multiple purposes, does your consent request itemise each purpose separately, and do you record consent against each specific purpose?",
    "CH2.CONSENT.3": "Can data principals withdraw their consent as easily as they gave it, and do you stop processing upon withdrawal?",
    "CH2.CONSENT.4": "If you use a Consent Manager, is it registered with the Data Protection Board and does it provide a transparent consent management platform?",
    "CH2.CONSENT.5": "Do you obtain verifiable parental or guardian consent before processing personal data of children (under 18) or persons with disabilities?",
    # Chapter 2 — Notice
    "CH2.NOTICE.1": "Is every consent request accompanied or preceded by a notice, understandable on its own, that describes the personal data and purpose, how to withdraw consent and exercise rights, and how to complain to the Data Protection Board?",
    "CH2.NOTICE.2": "For personal data collected before the DPDPA came into effect, have you provided a retrospective notice to data principals?",
    "CH2.NOTICE.3": "Does your privacy notice include contact details of a Data Protection Officer or designated grievance officer?",
    # Chapter 2 — Purpose Limitation
    "CH2.PURPOSE.1": "Is personal data processed only for the specific purpose for which consent was obtained or a legitimate use applies?",
    "CH2.PURPOSE.2": "Have you documented all cases where you process personal data without consent under the legitimate use provisions (Section 7)?",
    # Chapter 2 — Data Minimization
    "CH2.MINIMIZE.1": "Do you limit the collection of personal data to only what is necessary for the stated purpose?",
    "CH2.MINIMIZE.2": "Is personal data erased once the purpose for which it was collected is no longer being served?",
    "CH2.MINIMIZE.3": "Do you maintain documented data retention schedules with systematic deletion procedures, including retention of personal data, traffic data and processing logs for at least one year where the DPDP Rules require it?",
    # Chapter 2 — Accuracy
    "CH2.ACCURACY.1": "Where personal data is likely to be used to make a decision affecting the data principal, or disclosed to another Data Fiduciary, do you ensure it is complete, accurate, and consistent?",
    # Chapter 2 — Security
    "CH2.SECURITY.1": "Have you implemented reasonable technical and organizational security safeguards to protect personal data from breaches?",
    "CH2.SECURITY.2": "Is personal data encrypted at rest and in transit, with access controls based on the principle of least privilege?",
    "CH2.SECURITY.3": "Do you have valid contracts with all Data Processors that include obligations for security safeguards and processing instructions?",
    # Chapter 3 — Rights
    "CH3.ACCESS.1": "Can data principals request and receive a summary of their personal data and the processing activities you undertake on it?",
    "CH3.CORRECT.1": "Can data principals request correction of inaccurate or misleading personal data and completion of incomplete data?",
    "CH3.CORRECT.2": "Can data principals request erasure of the personal data they consented to at any time, and do you erase it unless retention is necessary for the specified purpose or for compliance with law?",
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
    "CM.RECORDS.2": "Before processing personal data for a new or changed purpose, do you obtain fresh consent for that purpose?",
    "CM.GRANULAR.1": "Do data principals have working controls (for example, per-purpose toggles) to give or withhold consent for each purpose, so that partial consent is actually possible?",
    "CM.GRANULAR.2": "Is access to your services independent of consent to non-essential data processing (i.e., no consent bundling or dark patterns)?",
    # Cross-Border
    "CB.TRANSFER.1": "Do you transfer personal data only to countries not restricted by the Central Government, and maintain an inventory of cross-border data flows?",
    "CB.TRANSFER.2": "Do you ensure that no personal data is transferred to a country or territory restricted by Central Government notification under Section 16(1), and that any stricter sectoral law on transfers outside India is complied with?",
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
    "CH2.CONSENT.2": "Section 6(1) requires consent to be specific to the specified purpose and limited to the personal data necessary for it. This question covers the consent request and the consent record: look for consent requests that itemise and clearly distinguish each purpose, evidence that one blanket consent is not used for several purposes, and records showing which specific purposes each Data Principal consented to. The per-purpose controls themselves are covered by CM.GRANULAR.1.",
    "CH2.CONSENT.3": "Section 6(4) requires that withdrawing consent is comparable in ease to giving it, and Section 6(6) requires processing (including by Data Processors) to cease within a reasonable time after withdrawal unless the law requires or authorises it.",
    "CH2.CONSENT.4": "Sections 6(7)-(9) let a Data Principal give, manage, review or withdraw consent through a Consent Manager, which must be registered with the Data Protection Board (DPDP Rules 2025 r.4). Look for evidence of registration, platform transparency, and that the Consent Manager provides mechanisms for Data Principals to give, withdraw, and manage consent.",
    "CH2.CONSENT.5": "Section 9(1) requires verifiable parental consent for processing children's data. Children are defined as under 18.",
    "CH2.NOTICE.1": "Section 5(1) requires every consent request to be accompanied or preceded by a notice stating the personal data and purpose, how to withdraw consent and exercise rights, and how to complain to the Board. DPDP Rules 2025 r.3 sets its content and form; r.3(a) requires the notice to be presented and understandable independently of any other information the Data Fiduciary makes available, so a notice that only works by cross-reference to a general privacy policy or terms does not meet it.",
    "CH2.NOTICE.2": "Section 5 expects retrospective notice for personal data collected before the DPDPA came into effect. Look for a process to identify pre-Act data, notification mechanisms, and evidence that notice was issued to affected Data Principals within the prescribed timeframe.",
    "CH2.NOTICE.3": "Section 6(3) requires the consent request to give contact details of the Data Protection Officer, where applicable, or another authorised person, and Section 8(9) with DPDP Rules 2025 r.9 requires those business contact details to be published prominently on the website or app. Look for a named individual, published contact details, and evidence that they appear alongside the notice and consent request.",
    "CH2.PURPOSE.1": "Section 6 limits processing of personal data to the specific purpose for which consent was obtained. Look for purpose documentation, controls preventing purpose creep, and evidence that secondary processing is blocked or re-consented.",
    "CH2.PURPOSE.2": "Section 7 defines legitimate uses where processing may proceed without consent. Look for a documented register of legitimate-use cases, evidence that each case meets the Section 7 criteria, and review of the register when processing activities change.",
    "CH2.MINIMIZE.1": "Section 6(1) limits consent to the personal data necessary for the specified purpose. Look for data collection forms and fields justified against purpose, evidence of unnecessary fields being removed, and minimization reviews when processing scope changes.",
    "CH2.MINIMIZE.2": "Section 8(7) requires erasure of personal data on withdrawal of consent or once the specified purpose is no longer being served, unless the law requires retention. Look for retention-to-purpose mapping, automated deletion triggers, and evidence that data is actually removed when the retention period expires.",
    "CH2.MINIMIZE.3": "Section 8(7) requires erasure once the purpose is served; documented retention schedules with systematic deletion procedures are how that is met. DPDP Rules 2025 r.8(3) also requires personal data, associated traffic data and other processing logs to be retained for at least one year from the date of processing, for the purposes in the Rules' Seventh Schedule, before they are erased. Look for a retention policy defining retention periods per data category that reflects the one-year minimum, deletion workflows, and evidence that schedules are reviewed and approved.",
    "CH2.ACCURACY.1": "Section 8(3) requires the Data Fiduciary to ensure personal data is complete, accurate and consistent where it is likely to be used to make a decision affecting the Data Principal or disclosed to another Data Fiduciary. Look for data quality controls, validation checks at collection, periodic reviews, and mechanisms to correct data when inaccuracies are identified.",
    "CH2.SECURITY.1": "Section 8(5) and DPDP Rules 2025 r.6 require 'reasonable security safeguards' to prevent personal data breach — this includes both technical measures (encryption, access controls) and organizational measures (policies, training).",
    "CH2.SECURITY.2": "Section 8(5) and DPDP Rules 2025 r.6(1)(a)-(b) expect data security measures such as encryption and controls on access to computer resources; encryption at rest and in transit with least-privilege access is the usual way to meet them. Look for encryption standards and algorithms, key management practices, role-based access enforcement, and evidence that access is reviewed periodically.",
    "CH2.SECURITY.3": "Section 8(2) allows a Data Processor to be engaged only under a valid contract, and DPDP Rules 2025 r.6(1)(f) requires that contract to provide for reasonable security safeguards. Look for executed processor agreements, defined security obligations, audit rights, and evidence that processor compliance is verified.",
    "CH3.ACCESS.1": "Section 11 grants Data Principals the right to request a summary of their personal data and the processing activities undertaken on it. Look for an access request workflow, identity verification, response templates, and evidence that summaries are provided within a reasonable timeframe.",
    "CH3.CORRECT.1": "Section 12 grants Data Principals the right to request correction of inaccurate or misleading personal data and completion of incomplete data. Look for a correction workflow, downstream update propagation, and evidence that corrections are applied across all affected systems.",
    "CH3.CORRECT.2": "Section 12(3) lets a Data Principal request erasure of her personal data, and the Data Fiduciary must erase it unless retention is necessary for the specified purpose or for compliance with law. Look for erasure request handling, technical deletion procedures, and evidence that data is removed from both primary and backup systems.",
    "CH3.GRIEVANCE.1": "Section 13 requires a grievance mechanism. This should be accessible and have a designated responsible person.",
    "CH3.GRIEVANCE.2": "Section 13 expects the Data Fiduciary to respond to grievances within a reasonable timeframe and inform the Data Principal of their right to approach the Data Protection Board if dissatisfied. Look for SLA-defined response times, escalation procedures, and evidence of Board-referral information being communicated.",
    "CH3.NOMINATE.1": "Section 14 allows Data Principals to nominate another individual to exercise their rights in the event of death or incapacity. Look for a nomination mechanism, validation of nominee identity, and evidence that nominations are recorded and honoured.",
    "CH4.CHILD.1": "Section 9(3) prohibits tracking or behavioural monitoring of children and targeted advertising directed at children.",
    "CH4.CHILD.2": "Section 9(2) requires that processing of children's personal data does not have a detrimental effect on their well-being. Look for impact assessments specific to children's data, safeguards preventing harmful processing, and evidence that processing decisions consider the child's best interest.",
    "CH4.CHILD.3": "Section 9(1) requires verifiable consent of the parent before processing a child's personal data, and DPDP Rules 2025 r.10 requires due diligence that the person identifying as the parent is an identifiable adult. Neither prescribes a specific age check of the child, so look for how the organisation identifies that a user is a child, how it verifies the parent, and evidence that children's data is flagged and handled with elevated protections.",
    "CH4.SDF.1": "Section 10 requires Significant Data Fiduciaries to appoint a Data Protection Officer based in India. Look for a formal appointment, DPO reporting structure, independence from processing operations, and evidence that the DPO is engaged in ongoing oversight.",
    "CH4.SDF.2": "Section 10 requires Significant Data Fiduciaries to appoint an independent Data Auditor to evaluate DPDPA compliance. Look for the auditor's appointment, scope of audit, independence from the assessed functions, and evidence of periodic audit reports reaching accountable leadership.",
    "CH4.SDF.3": "Section 10 requires Significant Data Fiduciaries to conduct periodic Data Protection Impact Assessments. Look for DPIA methodology, processing activities assessed, risk identification and treatment, and evidence that DPIA outcomes feed into control improvements.",
    "CH4.SDF.4": "Section 10 requires Significant Data Fiduciaries to conduct periodic compliance audits. Look for an audit plan, frequency defined by risk, audit findings tracking, and evidence that remediation is completed and verified.",
    "CM.GRANULAR.1": "Section 6(1) requires consent to be specific to each specified purpose. This question covers the controls the Data Principal uses: look for per-purpose consent toggles or equivalent choices in the interface, evidence that a Data Principal can consent to some purposes and decline others, and that partial consent does not block the processing she did consent to. How the consent request itemises purposes and how consent is recorded are covered by CH2.CONSENT.2.",
    "CM.GRANULAR.2": "Section 6 prohibits consent bundling and dark patterns. Look for evidence that access to services is not conditioned on consent for non-essential processing, that consent interfaces are free of manipulative design, and that Data Principals can decline non-essential processing without losing core service access.",
    "CM.RECORDS.1": "Section 6 expects auditable records of consent capture including when, how, and for what purpose consent was obtained. Look for consent logs capturing timestamp, method, purpose, and version of the consent notice presented, and evidence that records are retained for the required period.",
    "CM.RECORDS.2": "Section 6(1) makes consent specific to the specified purpose, so processing for a new or changed purpose needs fresh consent for that purpose. Look for triggers that detect new or changed purposes, re-consent workflows that run before the new processing starts, and evidence that existing consent is not relied upon for the new purpose.",
    "CB.TRANSFER.1": "Section 16 allows transfers only to countries not blacklisted by the Central Government.",
    "CB.TRANSFER.2": "Section 16(1) lets the Central Government restrict, by notification, transfers of personal data to a country or territory outside India, and Section 16(2) preserves any law in force in India that gives a higher degree of protection for, or restriction on, such transfers (for example, sectoral rules from a financial or other regulator). Look for a process to track s.16(1) notifications against the inventory of transfer destinations, identification of the sectoral laws that apply to the organisation, and evidence that transfers are checked against both. Data transfer agreements are supporting evidence only; the Act does not require them.",
    "CB.TRANSFER.3": "Section 16 empowers the Central Government to notify countries or categories of personal data that must remain in India. Look for awareness of applicable localisation requirements, data residency controls, and evidence that storage location is validated against the current negative list.",
    "BN.NOTIFY.1": "Section 8(6) requires intimation of every personal data breach to the Board. DPDP Rules 2025 r.7(2) requires an initial intimation without delay and a detailed report within 72 hours of becoming aware (or longer if the Board allows).",
    "BN.NOTIFY.2": "Section 8(6) requires the Data Fiduciary to intimate each affected Data Principal of a personal data breach. DPDP Rules 2025 r.7(1) requires this without delay, in clear and plain language, covering the breach, its likely consequences, mitigation, protective steps and a contact person. Look for documented notification procedures, message templates, and evidence of timely communication to affected individuals.",
    "BN.NOTIFY.3": "Section 8(5) (reasonable security safeguards, including detection, investigation and remediation under DPDP Rules 2025 r.6(1)(c)) and the intimation duties in Section 8(6) and r.7 are met through an incident response plan covering detection, containment, investigation, notification, and remediation. Look for an approved plan, defined roles, escalation paths, and evidence of periodic testing or tabletop exercises.",
    "BN.NOTIFY.4": "Section 8(6) and DPDP Rules 2025 r.7(2)(b) require the Board to receive the facts, circumstances, mitigation and remedial measures for each personal data breach; a breach register is how those are kept ready. Look for a maintained register with entries capturing breach description, affected data categories, mitigation steps, and dates of notification to the Board and Data Principals.",
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
