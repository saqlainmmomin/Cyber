"""
DPDPA (Digital Personal Data Protection Act, 2023) Requirements Framework.

Structured representation of all assessable requirements, organized by chapter.
Each requirement has an ID, title, description, DPDPA section reference, and criticality.
Weights determine scoring contribution.
"""

DPDPA_FRAMEWORK = {
    "chapter_2": {
        "title": "Obligations of Data Fiduciary",
        "weight": 0.30,
        "sections": {
            "consent": {
                "title": "Consent Management",
                "weight": 0.25,
                "requirements": [
                    {
                        "id": "CH2.CONSENT.1",
                        "title": "Lawful basis for processing with free, specific, informed consent",
                        "description": "Organization obtains consent that is free, specific, informed, unconditional, and unambiguous with a clear affirmative action. Consent request is presented in clear, plain language with specified purpose.",
                        "section_ref": "Section 6(1)-(2)",
                        "criticality": "critical",
                    },
                    {
                        "id": "CH2.CONSENT.2",
                        "title": "Itemised consent for multiple purposes",
                        "description": "When personal data is processed for multiple purposes, consent is obtained separately for each purpose, allowing the Data Principal to give or withhold consent for each.",
                        "section_ref": "Section 6(3)",
                        "criticality": "high",
                    },
                    {
                        "id": "CH2.CONSENT.3",
                        "title": "Consent withdrawal mechanism",
                        "description": "Data Principals can withdraw consent with the same ease as giving it. Organization ceases processing upon withdrawal unless retention is required by law.",
                        "section_ref": "Section 6(6)-(7)",
                        "criticality": "critical",
                    },
                    {
                        "id": "CH2.CONSENT.4",
                        "title": "Consent Manager registration and interoperability",
                        "description": "If a Consent Manager is used, it is registered with the Data Protection Board and provides an accessible, transparent platform for managing consent.",
                        "section_ref": "Section 6(8)-(9)",
                        "criticality": "medium",
                    },
                    {
                        "id": "CH2.CONSENT.5",
                        "title": "Verifiable parental consent for children's data",
                        "description": "Verifiable consent of a parent or lawful guardian is obtained before processing personal data of children (under 18) or persons with disabilities.",
                        "section_ref": "Section 9(1)",
                        "criticality": "critical",
                    },
                ],
            },
            "notice": {
                "title": "Notice Requirements",
                "weight": 0.15,
                "requirements": [
                    {
                        "id": "CH2.NOTICE.1",
                        "title": "Notice at or before collection of personal data",
                        "description": "A clear notice is given to the Data Principal at or before the time of collection, describing the personal data being collected and the purpose of processing.",
                        "section_ref": "Section 5(1)",
                        "criticality": "critical",
                    },
                    {
                        "id": "CH2.NOTICE.2",
                        "title": "Notice for previously collected data",
                        "description": "For personal data collected before the Act, a notice is provided as soon as reasonably practicable describing the data held and the processing purposes.",
                        "section_ref": "Section 5(2)",
                        "criticality": "high",
                    },
                    {
                        "id": "CH2.NOTICE.3",
                        "title": "Notice contains contact details of DPO or grievance officer",
                        "description": "The notice includes contact information for the Data Protection Officer or person responsible for addressing Data Principal queries.",
                        "section_ref": "Section 5(1)",
                        "criticality": "medium",
                    },
                ],
            },
            "purpose_limitation": {
                "title": "Purpose Limitation",
                "weight": 0.15,
                "requirements": [
                    {
                        "id": "CH2.PURPOSE.1",
                        "title": "Processing only for stated purpose",
                        "description": "Personal data is processed only for the purpose for which consent was given or which is deemed legitimate under the Act.",
                        "section_ref": "Section 4(1)",
                        "criticality": "critical",
                    },
                    {
                        "id": "CH2.PURPOSE.2",
                        "title": "Legitimate uses without consent properly identified",
                        "description": "Where processing occurs without consent (Section 7 — voluntary provision, state functions, employment, etc.), the legitimate use basis is documented and appropriate.",
                        "section_ref": "Section 7",
                        "criticality": "high",
                    },
                ],
            },
            "data_minimization": {
                "title": "Data Minimization & Storage Limitation",
                "weight": 0.15,
                "requirements": [
                    {
                        "id": "CH2.MINIMIZE.1",
                        "title": "Collection limited to what is necessary",
                        "description": "Only personal data that is necessary for the specified purpose is collected. No excessive or irrelevant data is gathered.",
                        "section_ref": "Section 4(1)",
                        "criticality": "high",
                    },
                    {
                        "id": "CH2.MINIMIZE.2",
                        "title": "Data retention limited to purpose fulfilment",
                        "description": "Personal data is erased when the purpose for which it was collected is no longer being served and retention is not necessary for legal purposes.",
                        "section_ref": "Section 8(7)",
                        "criticality": "high",
                    },
                    {
                        "id": "CH2.MINIMIZE.3",
                        "title": "Retention schedule and deletion procedures",
                        "description": "Organization maintains documented retention schedules and automated or systematic procedures for erasing personal data upon purpose completion or consent withdrawal.",
                        "section_ref": "Section 8(7)",
                        "criticality": "medium",
                    },
                ],
            },
            "accuracy": {
                "title": "Data Accuracy",
                "weight": 0.10,
                "requirements": [
                    {
                        "id": "CH2.ACCURACY.1",
                        "title": "Reasonable efforts to ensure data accuracy",
                        "description": "Organization makes reasonable efforts to ensure that personal data is complete, accurate, and not misleading, especially where data is used for decisions affecting the Data Principal or shared with other Fiduciaries.",
                        "section_ref": "Section 8(3)",
                        "criticality": "medium",
                    },
                ],
            },
            "security": {
                "title": "Security Safeguards",
                "weight": 0.20,
                "requirements": [
                    {
                        "id": "CH2.SECURITY.1",
                        "title": "Reasonable security safeguards implemented",
                        "description": "Organization implements reasonable security safeguards to protect personal data, including prevention of personal data breaches. This includes technical and organizational measures.",
                        "section_ref": "Section 8(4)",
                        "criticality": "critical",
                    },
                    {
                        "id": "CH2.SECURITY.2",
                        "title": "Encryption and access controls",
                        "description": "Personal data is encrypted at rest and in transit. Access controls ensure only authorized personnel can access personal data based on the principle of least privilege.",
                        "section_ref": "Section 8(4)",
                        "criticality": "critical",
                    },
                    {
                        "id": "CH2.SECURITY.3",
                        "title": "Data Processor contractual safeguards",
                        "description": "When engaging a Data Processor, the organization has a valid contract ensuring the Processor implements appropriate security safeguards and processes data only as instructed.",
                        "section_ref": "Section 8(2)",
                        "criticality": "high",
                    },
                ],
            },
        },
    },
    "chapter_3": {
        "title": "Rights of Data Principal",
        "weight": 0.20,
        "sections": {
            "right_to_access": {
                "title": "Right to Access Information",
                "weight": 0.25,
                "requirements": [
                    {
                        "id": "CH3.ACCESS.1",
                        "title": "Summary of personal data and processing activities",
                        "description": "Data Principals can obtain a summary of their personal data being processed and the processing activities undertaken, including identities of other Fiduciaries and Processors with whom data has been shared.",
                        "section_ref": "Section 11(1)",
                        "criticality": "high",
                    },
                ],
            },
            "right_to_correction": {
                "title": "Right to Correction & Erasure",
                "weight": 0.25,
                "requirements": [
                    {
                        "id": "CH3.CORRECT.1",
                        "title": "Mechanism for correction and completion of data",
                        "description": "Data Principals can request correction of inaccurate or misleading personal data and completion of incomplete data.",
                        "section_ref": "Section 12(1)",
                        "criticality": "high",
                    },
                    {
                        "id": "CH3.CORRECT.2",
                        "title": "Mechanism for erasure of personal data",
                        "description": "Data Principals can request erasure of personal data that is no longer necessary for the purpose for which it was collected.",
                        "section_ref": "Section 12(2)",
                        "criticality": "high",
                    },
                ],
            },
            "grievance_redressal": {
                "title": "Grievance Redressal",
                "weight": 0.30,
                "requirements": [
                    {
                        "id": "CH3.GRIEVANCE.1",
                        "title": "Grievance redressal mechanism available",
                        "description": "Organization provides an accessible mechanism for Data Principals to register grievances. A designated person or officer handles these grievances.",
                        "section_ref": "Section 13(1)",
                        "criticality": "critical",
                    },
                    {
                        "id": "CH3.GRIEVANCE.2",
                        "title": "Timely response to grievances",
                        "description": "Grievances are responded to within a reasonable timeframe. If unresolved, Data Principals are informed of their right to approach the Data Protection Board.",
                        "section_ref": "Section 13(2)",
                        "criticality": "high",
                    },
                ],
            },
            "nomination": {
                "title": "Right of Nomination",
                "weight": 0.20,
                "requirements": [
                    {
                        "id": "CH3.NOMINATE.1",
                        "title": "Nomination mechanism for death or incapacity",
                        "description": "Data Principals can nominate another individual to exercise their rights in the event of death or incapacity.",
                        "section_ref": "Section 14",
                        "criticality": "medium",
                    },
                ],
            },
        },
    },
    "chapter_4": {
        "title": "Special Provisions",
        "weight": 0.20,
        "sections": {
            "children_data": {
                "title": "Children's Data Protection",
                "weight": 0.40,
                "requirements": [
                    {
                        "id": "CH4.CHILD.1",
                        "title": "No tracking or behavioural monitoring of children",
                        "description": "Organization does not undertake tracking, behavioural monitoring, or targeted advertising directed at children.",
                        "section_ref": "Section 9(2)",
                        "criticality": "critical",
                    },
                    {
                        "id": "CH4.CHILD.2",
                        "title": "No processing detrimental to child's well-being",
                        "description": "Processing of children's personal data does not have a detrimental effect on their well-being.",
                        "section_ref": "Section 9(3)",
                        "criticality": "critical",
                    },
                    {
                        "id": "CH4.CHILD.3",
                        "title": "Age verification mechanism",
                        "description": "Organization has mechanisms to verify the age of users and identify children to apply appropriate protections and obtain parental consent.",
                        "section_ref": "Section 9",
                        "criticality": "high",
                    },
                ],
            },
            "significant_data_fiduciary": {
                "title": "Significant Data Fiduciary (SDF) Obligations",
                "weight": 0.60,
                "requirements": [
                    {
                        "id": "CH4.SDF.1",
                        "title": "Data Protection Officer (DPO) appointed",
                        "description": "If designated as a Significant Data Fiduciary, a Data Protection Officer based in India has been appointed who represents the organization to the Board and Data Principals.",
                        "section_ref": "Section 10(2)(a)",
                        "criticality": "critical",
                    },
                    {
                        "id": "CH4.SDF.2",
                        "title": "Independent Data Auditor appointed",
                        "description": "An independent Data Auditor has been appointed to evaluate compliance with the Act.",
                        "section_ref": "Section 10(2)(b)",
                        "criticality": "high",
                    },
                    {
                        "id": "CH4.SDF.3",
                        "title": "Data Protection Impact Assessment (DPIA) conducted",
                        "description": "Periodic Data Protection Impact Assessments are conducted to evaluate processing activities and associated risks to Data Principals.",
                        "section_ref": "Section 10(2)(c)",
                        "criticality": "high",
                    },
                    {
                        "id": "CH4.SDF.4",
                        "title": "Periodic audit completed",
                        "description": "Periodic audits of data processing activities and compliance posture are conducted as prescribed.",
                        "section_ref": "Section 10(2)(d)",
                        "criticality": "high",
                    },
                ],
            },
        },
    },
    "consent_management": {
        "title": "Consent Management (Detailed)",
        "weight": 0.10,
        "sections": {
            "consent_records": {
                "title": "Consent Records & Lifecycle",
                "weight": 0.50,
                "requirements": [
                    {
                        "id": "CM.RECORDS.1",
                        "title": "Consent records maintained",
                        "description": "Organization maintains auditable records of when, how, and for what purpose consent was obtained from each Data Principal.",
                        "section_ref": "Section 6",
                        "criticality": "high",
                    },
                    {
                        "id": "CM.RECORDS.2",
                        "title": "Consent refresh and re-validation process",
                        "description": "Organization has a process to refresh or re-obtain consent when purposes change or after a reasonable period.",
                        "section_ref": "Section 6",
                        "criticality": "medium",
                    },
                ],
            },
            "granular_consent": {
                "title": "Granular Consent Controls",
                "weight": 0.50,
                "requirements": [
                    {
                        "id": "CM.GRANULAR.1",
                        "title": "Granular consent options available",
                        "description": "Data Principals can provide or withhold consent at a granular level (per-purpose) rather than being forced into all-or-nothing consent.",
                        "section_ref": "Section 6(3)",
                        "criticality": "high",
                    },
                    {
                        "id": "CM.GRANULAR.2",
                        "title": "No consent bundling with service access",
                        "description": "Access to services is not conditional on consent to processing that is not necessary for the service. No dark patterns used in consent collection.",
                        "section_ref": "Section 6(1)",
                        "criticality": "critical",
                    },
                ],
            },
        },
    },
    "cross_border": {
        "title": "Cross-Border Data Transfer",
        "weight": 0.10,
        "sections": {
            "transfer_controls": {
                "title": "Transfer Restrictions & Controls",
                "weight": 1.0,
                "requirements": [
                    {
                        "id": "CB.TRANSFER.1",
                        "title": "Data transfers only to non-restricted jurisdictions",
                        "description": "Personal data is transferred outside India only to countries or territories not restricted by the Central Government. Organization maintains an inventory of cross-border data flows.",
                        "section_ref": "Section 16(1)",
                        "criticality": "critical",
                    },
                    {
                        "id": "CB.TRANSFER.2",
                        "title": "Contractual safeguards for cross-border transfers",
                        "description": "Appropriate contractual or legal safeguards are in place for data transferred outside India, including obligations on the receiving party.",
                        "section_ref": "Section 16",
                        "criticality": "high",
                    },
                    {
                        "id": "CB.TRANSFER.3",
                        "title": "Data localisation where required",
                        "description": "Where the Central Government mandates that certain categories of personal data must be stored in India, the organization complies with such localisation requirements.",
                        "section_ref": "Section 16",
                        "criticality": "high",
                    },
                ],
            },
        },
    },
    "breach_notification": {
        "title": "Breach Notification",
        "weight": 0.10,
        "sections": {
            "incident_management": {
                "title": "Breach Detection & Notification",
                "weight": 1.0,
                "requirements": [
                    {
                        "id": "BN.NOTIFY.1",
                        "title": "Breach notification to Data Protection Board",
                        "description": "Organization has procedures to notify the Data Protection Board of India of any personal data breach in the prescribed form and manner.",
                        "section_ref": "Section 8(6)",
                        "criticality": "critical",
                    },
                    {
                        "id": "BN.NOTIFY.2",
                        "title": "Breach notification to affected Data Principals",
                        "description": "Organization has procedures to notify affected Data Principals of a personal data breach in the prescribed form and manner.",
                        "section_ref": "Section 8(6)",
                        "criticality": "critical",
                    },
                    {
                        "id": "BN.NOTIFY.3",
                        "title": "Incident response plan documented",
                        "description": "A documented incident response plan exists covering detection, containment, investigation, notification, and remediation of personal data breaches.",
                        "section_ref": "Section 8(4)-(6)",
                        "criticality": "high",
                    },
                    {
                        "id": "BN.NOTIFY.4",
                        "title": "Breach register maintained",
                        "description": "Organization maintains a register of all personal data breaches including facts, effects, and remedial actions taken.",
                        "section_ref": "Section 8(6)",
                        "criticality": "medium",
                    },
                ],
            },
        },
    },
}


# ─── Requirement Dependency DAG ──────────────────────────────────────────────
# Maps requirement_id → list of prerequisite requirement_ids.
# Remediation items should be sequenced: prerequisites first.

REQUIREMENT_DEPENDENCIES: dict[str, list[str]] = {
    # Can't do data subject access without knowing what data you hold
    "CH3.ACCESS.1": ["CH2.MINIMIZE.2", "CH2.MINIMIZE.3"],
    # Can't do correction/erasure without retention schedules
    "CH3.CORRECT.1": ["CH2.MINIMIZE.2"],
    "CH3.CORRECT.2": ["CH2.MINIMIZE.2", "CH2.MINIMIZE.3"],
    # Consent records depend on having a consent mechanism
    "CM.RECORDS.1": ["CH2.CONSENT.1"],
    "CM.RECORDS.2": ["CH2.CONSENT.1", "CM.RECORDS.1"],
    # Granular consent depends on having any consent mechanism
    "CM.GRANULAR.1": ["CH2.CONSENT.1"],
    "CM.GRANULAR.2": ["CH2.CONSENT.1", "CM.GRANULAR.1"],
    # Consent withdrawal depends on consent capture
    "CH2.CONSENT.3": ["CH2.CONSENT.1"],
    # Itemised consent depends on basic consent
    "CH2.CONSENT.2": ["CH2.CONSENT.1"],
    # Parental consent depends on basic consent + age verification
    "CH2.CONSENT.5": ["CH2.CONSENT.1", "CH4.CHILD.3"],
    # SDF obligations — DPO before audit
    "CH4.SDF.2": ["CH4.SDF.1"],
    "CH4.SDF.3": ["CH4.SDF.1"],
    "CH4.SDF.4": ["CH4.SDF.1", "CH4.SDF.2"],
    # Breach notification depends on incident response plan
    "BN.NOTIFY.1": ["BN.NOTIFY.3"],
    "BN.NOTIFY.2": ["BN.NOTIFY.3"],
    "BN.NOTIFY.4": ["BN.NOTIFY.3"],
    # Cross-border contractual safeguards depend on knowing your flows
    "CB.TRANSFER.2": ["CB.TRANSFER.1"],
    "CB.TRANSFER.3": ["CB.TRANSFER.1"],
    # Notice for pre-existing data depends on having a notice template
    "CH2.NOTICE.2": ["CH2.NOTICE.1"],
    "CH2.NOTICE.3": ["CH2.NOTICE.1"],
}


# ─── Root Cause Clusters ────────────────────────────────────────────────────
# Maps root_cause_category → default initiative template.
# Claude assigns one root_cause_category per gap; these drive initiative clustering.

ROOT_CAUSE_CLUSTERS: dict[str, dict] = {
    "policy": {
        "title": "Policy Development & Documentation Sprint",
        "description": "Develop, formalize, and publish foundational privacy and data protection policies.",
        "typical_requirements": [
            "CH2.NOTICE.1", "CH2.NOTICE.2", "CH2.NOTICE.3",
            "CH2.PURPOSE.1", "CH2.PURPOSE.2",
            "CH2.MINIMIZE.3",
        ],
    },
    "people": {
        "title": "Privacy Awareness & Capability Building Program",
        "description": "Train staff, assign roles, and build internal privacy expertise.",
        "typical_requirements": [
            "CH4.SDF.1", "CH3.GRIEVANCE.1", "CH3.GRIEVANCE.2",
        ],
    },
    "process": {
        "title": "Process Formalization & Rights Enablement",
        "description": "Establish repeatable processes for consent, rights, retention, and breach response.",
        "typical_requirements": [
            "CH2.CONSENT.1", "CH2.CONSENT.2", "CH2.CONSENT.3",
            "CM.RECORDS.1", "CM.RECORDS.2", "CM.GRANULAR.1", "CM.GRANULAR.2",
            "CH3.ACCESS.1", "CH3.CORRECT.1", "CH3.CORRECT.2",
            "CH2.MINIMIZE.2", "BN.NOTIFY.1", "BN.NOTIFY.2", "BN.NOTIFY.3",
        ],
    },
    "technology": {
        "title": "Technology Investment & Security Uplift",
        "description": "Implement or upgrade security controls, consent platforms, and monitoring tools.",
        "typical_requirements": [
            "CH2.SECURITY.1", "CH2.SECURITY.2", "CH2.SECURITY.3",
            "CH4.CHILD.3", "BN.NOTIFY.4",
        ],
    },
    "governance": {
        "title": "Governance Structure & Oversight Framework",
        "description": "Establish board reporting, DPO function, audit program, and DPIA processes.",
        "typical_requirements": [
            "CH4.SDF.1", "CH4.SDF.2", "CH4.SDF.3", "CH4.SDF.4",
            "CB.TRANSFER.1", "CB.TRANSFER.2", "CB.TRANSFER.3",
        ],
    },
}


def get_all_requirements() -> list[dict]:
    """Flatten the framework into a list of all requirements."""
    requirements = []
    for chapter_key, chapter in DPDPA_FRAMEWORK.items():
        for section_key, section in chapter["sections"].items():
            for req in section["requirements"]:
                requirements.append(
                    {
                        **req,
                        "chapter": chapter_key,
                        "chapter_title": chapter["title"],
                        "section": section_key,
                        "section_title": section["title"],
                    }
                )
    return requirements


def get_requirement_count() -> int:
    return len(get_all_requirements())
