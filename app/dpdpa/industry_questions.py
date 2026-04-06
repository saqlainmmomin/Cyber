"""
Industry-specific question banks for adaptive assessment.

These are NOT the base 41 DPDPA requirement questions (those are in questionnaire.py).
Industry questions probe deeper into how the organization's specific operations
interact with DPDPA requirements. They map to requirement IDs for scoring/reporting.

Each question has:
  - skip_if: conditions under which the question is skipped (desk review found adequate coverage)
  - deepen_if: conditions under which additional context is shown (desk review found signals/absences)
  - follow_up_triggers: conditions that trigger Claude-generated follow-up questions
"""

INDUSTRY_QUESTIONS = {
    "it_saas": {
        "name": "IT / SaaS",
        "description": "Questions for IT services and SaaS companies processing personal data across multi-tenant environments.",
        "questions": [
            # --- Multi-tenant data isolation ---
            {
                "id": "IND.SAAS.1",
                "text": "How do you isolate personal data between tenants in your SaaS platform? Describe the technical mechanism (row-level, schema-level, DB-per-tenant).",
                "maps_to": ["CH2.SECURITY.1", "CH2.SECURITY.2"],
                "category": "data_isolation",
                "criticality": "critical",
                "guidance": "DPDPA Section 8(4) requires reasonable security safeguards. For SaaS platforms, tenant data isolation is a foundational control.",
                "skip_if": {"desk_review_coverage": {"CH2.SECURITY.1": "adequate", "CH2.SECURITY.2": "adequate"}},
                "deepen_if": {"signal_flags": ["template_artifacts", "scope_gaps"]},
                "follow_up_triggers": {
                    "weak_answers": ["not_implemented", "planned"],
                    "inconsistency_check": True,
                },
            },
            {
                "id": "IND.SAAS.2",
                "text": "When a customer (tenant) requests data deletion, how do you ensure their data is purged from all systems including backups, caches, and derived datasets?",
                "maps_to": ["CH2.MINIMIZE.2", "CH2.MINIMIZE.3", "CH3.CORRECT.2"],
                "category": "data_lifecycle",
                "criticality": "high",
                "guidance": "SaaS platforms often retain data in multiple layers (primary DB, search indices, analytics, backups). DPDPA Section 8(7) requires erasure when purpose is no longer served.",
                "skip_if": {"desk_review_coverage": {"CH2.MINIMIZE.2": "adequate", "CH3.CORRECT.2": "adequate"}},
                "deepen_if": {"absence_findings": ["CH2.MINIMIZE.2", "CH2.MINIMIZE.3"]},
                "follow_up_triggers": {
                    "weak_answers": ["partially_implemented", "not_implemented"],
                    "inconsistency_check": True,
                },
            },
            # --- API data sharing ---
            {
                "id": "IND.SAAS.3",
                "text": "Does your platform expose APIs that allow third parties to access personal data? If so, how is consent propagated through the API chain?",
                "maps_to": ["CH2.CONSENT.1", "CH2.PURPOSE.1", "CH2.SECURITY.3"],
                "category": "api_data_sharing",
                "criticality": "high",
                "guidance": "API-based data sharing creates consent propagation challenges. Each API consumer may be a separate data processor under DPDPA.",
                "skip_if": {},
                "deepen_if": {"signal_flags": ["gdpr_copy_paste", "scope_gaps"]},
                "follow_up_triggers": {
                    "weak_answers": ["partially_implemented", "not_implemented", "planned"],
                    "inconsistency_check": True,
                },
            },
            {
                "id": "IND.SAAS.4",
                "text": "How do you handle personal data in webhook payloads, event streams, or message queues? Is there consent validation before data enters these pipelines?",
                "maps_to": ["CH2.CONSENT.1", "CH2.PURPOSE.1"],
                "category": "api_data_sharing",
                "criticality": "medium",
                "guidance": "Asynchronous data flows (webhooks, Kafka, etc.) often bypass the consent checks that exist in synchronous API paths.",
                "skip_if": {},
                "deepen_if": {},
                "follow_up_triggers": {
                    "weak_answers": ["not_implemented", "planned"],
                },
            },
            # --- Cloud infrastructure ---
            {
                "id": "IND.SAAS.5",
                "text": "Which cloud providers and regions host personal data? Do you have contractual agreements with each provider covering DPDPA obligations?",
                "maps_to": ["CB.TRANSFER.1", "CB.TRANSFER.2", "CH2.SECURITY.3"],
                "category": "cloud_infra",
                "criticality": "high",
                "guidance": "Cloud providers are data processors under DPDPA. Section 8(2) requires valid contracts with processing instructions. Cross-border hosting triggers Section 16.",
                "skip_if": {"desk_review_coverage": {"CB.TRANSFER.1": "adequate", "CB.TRANSFER.2": "adequate"}},
                "deepen_if": {"absence_findings": ["CB.TRANSFER.1", "CB.TRANSFER.2"]},
                "follow_up_triggers": {
                    "weak_answers": ["partially_implemented", "not_implemented"],
                    "inconsistency_check": True,
                },
            },
            {
                "id": "IND.SAAS.6",
                "text": "Do you use any third-party SaaS tools (analytics, monitoring, CRM, support) that process your customers' personal data? How do you ensure DPDPA compliance across this vendor chain?",
                "maps_to": ["CH2.SECURITY.3", "CB.TRANSFER.1"],
                "category": "cloud_infra",
                "criticality": "high",
                "guidance": "Sub-processors handling personal data must meet the same DPDPA obligations. Many SaaS vendors unknowingly create a processor chain.",
                "skip_if": {},
                "deepen_if": {"signal_flags": ["scope_gaps"]},
                "follow_up_triggers": {
                    "weak_answers": ["partially_implemented", "not_implemented", "planned"],
                    "inconsistency_check": True,
                },
            },
            # --- SLA-based deletion ---
            {
                "id": "IND.SAAS.7",
                "text": "What is your data retention policy for customer data after contract termination? Is there an SLA-defined deletion window, and how is it enforced?",
                "maps_to": ["CH2.MINIMIZE.2", "CH2.MINIMIZE.3"],
                "category": "data_lifecycle",
                "criticality": "high",
                "guidance": "DPDPA Section 8(7) requires deletion when purpose is fulfilled. For SaaS, contract termination is a clear 'purpose fulfilled' event.",
                "skip_if": {"desk_review_coverage": {"CH2.MINIMIZE.2": "adequate", "CH2.MINIMIZE.3": "adequate"}},
                "deepen_if": {"absence_findings": ["CH2.MINIMIZE.2"]},
                "follow_up_triggers": {
                    "weak_answers": ["not_implemented", "planned"],
                },
            },
            # --- Consent in product flows ---
            {
                "id": "IND.SAAS.8",
                "text": "How does your application collect consent within the product experience? Is consent captured in-app, or do you rely on terms of service acceptance?",
                "maps_to": ["CH2.CONSENT.1", "CH2.CONSENT.2", "CM.GRANULAR.2"],
                "category": "consent_ux",
                "criticality": "critical",
                "guidance": "DPDPA requires clear, specific consent — not buried in T&C. SaaS products should have in-product consent flows separate from ToS.",
                "skip_if": {"desk_review_coverage": {"CH2.CONSENT.1": "adequate"}},
                "deepen_if": {"signal_flags": ["buried_consent", "gdpr_copy_paste"]},
                "follow_up_triggers": {
                    "weak_answers": ["partially_implemented", "not_implemented"],
                    "inconsistency_check": True,
                },
            },
            {
                "id": "IND.SAAS.9",
                "text": "When you add new features that process personal data in new ways, how do you obtain fresh consent from existing users?",
                "maps_to": ["CH2.CONSENT.2", "CM.RECORDS.2"],
                "category": "consent_ux",
                "criticality": "high",
                "guidance": "Purpose creep is common in SaaS — each new feature that processes data differently requires separate consent under Section 6(3).",
                "skip_if": {},
                "deepen_if": {},
                "follow_up_triggers": {
                    "weak_answers": ["not_implemented", "planned"],
                },
            },
            # --- Breach response ---
            {
                "id": "IND.SAAS.10",
                "text": "Describe your incident response process for a data breach affecting multiple tenants. How do you determine which tenants are affected and notify them?",
                "maps_to": ["BN.NOTIFY.1", "BN.NOTIFY.2", "BN.NOTIFY.3"],
                "category": "breach_response",
                "criticality": "critical",
                "guidance": "Multi-tenant breaches require per-tenant impact analysis. DPDPA Section 8(6) requires notification to both the Board and affected data principals.",
                "skip_if": {"desk_review_coverage": {"BN.NOTIFY.1": "adequate", "BN.NOTIFY.3": "adequate"}},
                "deepen_if": {"absence_findings": ["BN.NOTIFY.1", "BN.NOTIFY.2"]},
                "follow_up_triggers": {
                    "weak_answers": ["partially_implemented", "not_implemented", "planned"],
                    "inconsistency_check": True,
                },
            },
            # --- Data subject rights at scale ---
            {
                "id": "IND.SAAS.11",
                "text": "How do you handle data access and portability requests from end-users (data principals) of your customers' tenants? Who is responsible — you or the tenant?",
                "maps_to": ["CH3.ACCESS.1", "CH3.CORRECT.1"],
                "category": "rights_management",
                "criticality": "high",
                "guidance": "In B2B SaaS, the tenant is typically the data fiduciary and you are the processor. But if you have a direct relationship with end-users, you may also be a fiduciary.",
                "skip_if": {},
                "deepen_if": {"signal_flags": ["scope_gaps"]},
                "follow_up_triggers": {
                    "weak_answers": ["partially_implemented", "not_implemented"],
                    "inconsistency_check": True,
                },
            },
            {
                "id": "IND.SAAS.12",
                "text": "Do you provide automated tools (self-service dashboard, API) for data principals to access, correct, or delete their data, or is it handled manually?",
                "maps_to": ["CH3.ACCESS.1", "CH3.CORRECT.1", "CH3.CORRECT.2"],
                "category": "rights_management",
                "criticality": "medium",
                "guidance": "At SaaS scale, manual rights handling creates compliance bottlenecks. Automated self-service is a strong compliance signal.",
                "skip_if": {},
                "deepen_if": {},
                "follow_up_triggers": {
                    "weak_answers": ["not_implemented"],
                },
            },
            # --- Analytics & tracking ---
            {
                "id": "IND.SAAS.13",
                "text": "What analytics, telemetry, or user tracking do you perform on product usage data? Is consent obtained separately for analytics processing?",
                "maps_to": ["CH2.CONSENT.2", "CH2.PURPOSE.1", "CM.GRANULAR.1"],
                "category": "analytics",
                "criticality": "high",
                "guidance": "Product analytics often processes personal data (user behavior, session data, device info). DPDPA requires separate consent for each processing purpose.",
                "skip_if": {},
                "deepen_if": {"signal_flags": ["buried_consent"]},
                "follow_up_triggers": {
                    "weak_answers": ["partially_implemented", "not_implemented"],
                    "inconsistency_check": True,
                },
            },
        ],
    },
    "generic": {
        "name": "Generic",
        "description": "Standard DPDPA compliance questions for organizations without a specific industry vertical.",
        "questions": [
            {
                "id": "IND.GEN.1",
                "text": "Do you maintain a data inventory or register of processing activities that maps personal data flows across your organization?",
                "maps_to": ["CH2.PURPOSE.1", "CH2.MINIMIZE.1"],
                "category": "data_governance",
                "criticality": "high",
                "guidance": "A data inventory is the foundation of DPDPA compliance — you can't protect what you don't know you have.",
                "skip_if": {},
                "deepen_if": {},
                "follow_up_triggers": {
                    "weak_answers": ["not_implemented", "planned"],
                },
            },
            {
                "id": "IND.GEN.2",
                "text": "How do you ensure third-party vendors who process personal data on your behalf comply with DPDPA requirements?",
                "maps_to": ["CH2.SECURITY.3"],
                "category": "vendor_management",
                "criticality": "high",
                "guidance": "Section 8(2) holds the data fiduciary responsible for processor compliance.",
                "skip_if": {"desk_review_coverage": {"CH2.SECURITY.3": "adequate"}},
                "deepen_if": {"absence_findings": ["CH2.SECURITY.3"]},
                "follow_up_triggers": {
                    "weak_answers": ["partially_implemented", "not_implemented"],
                    "inconsistency_check": True,
                },
            },
            {
                "id": "IND.GEN.3",
                "text": "Have you trained your staff on DPDPA requirements and their responsibilities when handling personal data?",
                "maps_to": ["CH2.SECURITY.1"],
                "category": "people",
                "criticality": "medium",
                "guidance": "Organizational security measures under Section 8(4) include staff awareness and training.",
                "skip_if": {},
                "deepen_if": {},
                "follow_up_triggers": {
                    "weak_answers": ["not_implemented"],
                },
            },
            {
                "id": "IND.GEN.4",
                "text": "Do you have a documented process for responding to data principal rights requests (access, correction, erasure) within a defined timeframe?",
                "maps_to": ["CH3.ACCESS.1", "CH3.CORRECT.1", "CH3.CORRECT.2", "CH3.GRIEVANCE.1"],
                "category": "rights_management",
                "criticality": "high",
                "guidance": "Chapter III rights must be exercisable in practice, not just in policy.",
                "skip_if": {"desk_review_coverage": {"CH3.ACCESS.1": "adequate", "CH3.GRIEVANCE.1": "adequate"}},
                "deepen_if": {"absence_findings": ["CH3.ACCESS.1", "CH3.GRIEVANCE.1"]},
                "follow_up_triggers": {
                    "weak_answers": ["partially_implemented", "not_implemented"],
                    "inconsistency_check": True,
                },
            },
            {
                "id": "IND.GEN.5",
                "text": "How do you ensure that personal data collected for one purpose is not repurposed without obtaining fresh consent?",
                "maps_to": ["CH2.PURPOSE.1", "CH2.CONSENT.2"],
                "category": "purpose_limitation",
                "criticality": "high",
                "guidance": "Purpose limitation is a core DPDPA principle. Data originally collected for billing should not be used for marketing without separate consent.",
                "skip_if": {},
                "deepen_if": {"signal_flags": ["buried_consent"]},
                "follow_up_triggers": {
                    "weak_answers": ["partially_implemented", "not_implemented"],
                },
            },
        ],
    },
}


# Map industry enum values to question bank keys
INDUSTRY_BANK_MAP = {
    "it_services": "it_saas",
    "fintech": "generic",  # Future: dedicated fintech bank
    "healthcare": "generic",  # Future: dedicated healthcare bank
    "ecommerce": "generic",  # Future: dedicated ecommerce bank
    "manufacturing": "generic",
    "education": "generic",
    "real_estate": "generic",
    "legal": "generic",
    "accounting": "generic",
    "other": "generic",
}


def get_industry_questions(industry: str) -> dict:
    """Get the question bank for a given industry."""
    bank_key = INDUSTRY_BANK_MAP.get(industry, "generic")
    return INDUSTRY_QUESTIONS.get(bank_key, INDUSTRY_QUESTIONS["generic"])
