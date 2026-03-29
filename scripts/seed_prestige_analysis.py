"""
Seed script: Inject Prestige Estates gap analysis without Claude API.

Analysis performed by Claude Code based on the 41 questionnaire responses
from the original assessment (18cafa6a-...).

Run from project root:
    python scripts/seed_prestige_analysis.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.dpdpa.framework import get_all_requirements
from app.models.assessment import Assessment
from app.models.initiative import Initiative
from app.models.questionnaire import QuestionnaireResponse
from app.models.report import GapItem, GapReport
from app.services.scoring import compute_scores, generate_initiatives

# ─── Target assessment ─────────────────────────────────────────────────────
NEW_ASSESSMENT_ID = "b1f29925-bc98-41aa-823d-abc2c622ae79"
OLD_ASSESSMENT_ID = "18cafa6a-fde9-486d-9169-d7dd0d7fc422"

# ─── Gap Analysis Results ──────────────────────────────────────────────────
# Analysis: all 41 DPDPA requirements assessed against Prestige Estates
# privacy policy and self-reported questionnaire answers.
# Fields: requirement_id, compliance_status, current_state, gap_description,
#         risk_level, remediation_action, remediation_priority, remediation_effort,
#         timeline_weeks, maturity_level, root_cause_category, evidence_quote

GAP_ASSESSMENTS = [
    {
        "requirement_id": "CH2.CONSENT.1",
        "compliance_status": "partially_compliant",
        "current_state": "Checkboxes and online forms exist with stated purposes, but consent is not demonstrably free, specific, or unconditional — particularly at offline collection points (site visits, head office).",
        "gap_description": "Consent is likely bundled across purposes and collection points. No clear separate affirmative action per purpose. Offline collection uses paper forms with no structured consent capture.",
        "risk_level": "critical",
        "remediation_action": "Redesign all digital and physical consent capture forms to be purpose-specific. Implement clear affirmative action (unticked checkboxes) with plain-language purpose descriptions per Section 6(1)-(2).",
        "remediation_priority": 1,
        "remediation_effort": "high",
        "timeline_weeks": 12,
        "maturity_level": 2,
        "root_cause_category": "process",
        "evidence_quote": "Checkboxes and forms with purposes exist, but consent is not demonstrably free, specific, and unconditional per DPDPA standards.",
    },
    {
        "requirement_id": "CH2.CONSENT.2",
        "compliance_status": "partially_compliant",
        "current_state": "Purposes are listed in the privacy policy but a single bundled consent covers all purposes — lead generation, marketing campaigns, analytics, and service delivery.",
        "gap_description": "No itemised per-purpose consent mechanism exists. Data principals cannot selectively consent to, for example, marketing while declining analytics data sharing.",
        "risk_level": "high",
        "remediation_action": "Implement per-purpose consent checkboxes on all collection forms. Allow data principals to provide or withhold consent for each purpose independently.",
        "remediation_priority": 2,
        "remediation_effort": "medium",
        "timeline_weeks": 8,
        "maturity_level": 1,
        "root_cause_category": "process",
        "evidence_quote": "Purposes listed in policy but no evidence of separate itemised consent per purpose. Likely bundled consent.",
    },
    {
        "requirement_id": "CH2.CONSENT.3",
        "compliance_status": "partially_compliant",
        "current_state": "Withdrawal of consent requires contacting the organization via email or phone call. Consent was given via online checkbox or form.",
        "gap_description": "Withdrawal is significantly harder than consent giving. Section 6(6) requires withdrawal to be as easy as giving consent. A manual contact process does not satisfy this requirement.",
        "risk_level": "critical",
        "remediation_action": "Build a self-service consent dashboard or account settings page where data principals can withdraw consent for specific purposes with one click. Automate downstream processing cessation.",
        "remediation_priority": 1,
        "remediation_effort": "medium",
        "timeline_weeks": 8,
        "maturity_level": 2,
        "root_cause_category": "process",
        "evidence_quote": "Policy says contact organization to withdraw. Not as easy as giving consent (checkbox vs email/call).",
    },
    {
        "requirement_id": "CH2.CONSENT.4",
        "compliance_status": "non_compliant",
        "current_state": "No Consent Manager platform is deployed or registered with the Data Protection Board.",
        "gap_description": "While Section 6(8)-(9) is only triggered if a Consent Manager is used, the volume and complexity of consent flows at Prestige Estates (multi-channel: online, phone, site visits, head office) suggests a Consent Manager is operationally necessary to achieve compliance at scale.",
        "risk_level": "medium",
        "remediation_action": "Evaluate whether a registered Consent Manager platform is required. If implemented, ensure it is registered with the Board and provides an accessible interface for data principals to manage consents.",
        "remediation_priority": 3,
        "remediation_effort": "high",
        "timeline_weeks": 16,
        "maturity_level": 0,
        "root_cause_category": "process",
        "evidence_quote": "No registered Consent Manager platform in use.",
    },
    {
        "requirement_id": "CH2.CONSENT.5",
        "compliance_status": "partially_compliant",
        "current_state": "Privacy policy references parental consent for users under 13 years of age, but DPDPA Section 9(1) mandates this for all persons under 18.",
        "gap_description": "Incorrect age threshold (13 vs 18). No age verification mechanism to identify users under 18. No verifiable parental consent process. Website may be accessible to minors without adequate safeguards.",
        "risk_level": "critical",
        "remediation_action": "Update policy and all consent flows to apply the under-18 threshold. Implement age verification on digital platforms. Build a verifiable parental consent workflow for minor users.",
        "remediation_priority": 1,
        "remediation_effort": "high",
        "timeline_weeks": 10,
        "maturity_level": 1,
        "root_cause_category": "process",
        "evidence_quote": "Policy mentions parental consent for under 13, but DPDPA requires under 18. Age threshold is wrong.",
    },
    {
        "requirement_id": "CH2.NOTICE.1",
        "compliance_status": "compliant",
        "current_state": "Privacy policy published on website. Online forms outline intended purposes at point of collection.",
        "gap_description": "No critical gap identified. Notice exists at digital collection points. Offline collection points (site visits) may benefit from standardised notice sheets.",
        "risk_level": "low",
        "remediation_action": "Consider adding standardised printed notice cards at physical collection points (site visits, head office) to ensure parity with digital notice.",
        "remediation_priority": 4,
        "remediation_effort": "low",
        "timeline_weeks": 4,
        "maturity_level": 4,
        "root_cause_category": "policy",
        "evidence_quote": "Privacy policy exists on website. Forms outline intended purposes at collection.",
    },
    {
        "requirement_id": "CH2.NOTICE.2",
        "compliance_status": "non_compliant",
        "current_state": "No retrospective notice has been issued for personal data collected prior to DPDPA coming into force.",
        "gap_description": "Section 5(2) requires that data subjects whose data was collected pre-Act be notified as soon as reasonably practicable. Prestige Estates holds a large historical CRM database with no such notice issued.",
        "risk_level": "high",
        "remediation_action": "Conduct a data audit to identify all pre-Act data subjects. Draft a retrospective notice covering data held and processing purposes. Distribute via email/SMS/post and update the CRM with sent status.",
        "remediation_priority": 2,
        "remediation_effort": "medium",
        "timeline_weeks": 6,
        "maturity_level": 0,
        "root_cause_category": "policy",
        "evidence_quote": "No mention of retrospective notice for data collected before DPDPA.",
    },
    {
        "requirement_id": "CH2.NOTICE.3",
        "compliance_status": "partially_compliant",
        "current_state": "Corporate address and general phone/email provided in privacy policy. No specific DPO or named grievance officer listed.",
        "gap_description": "Section 5(1) requires notice to include contact details of the person responsible for addressing Data Principal queries. A generic corporate contact is insufficient — a named responsible person is required.",
        "risk_level": "medium",
        "remediation_action": "Appoint a named Privacy Contact or Grievance Officer. Update privacy policy and all notice templates to include this person's name and dedicated contact details.",
        "remediation_priority": 2,
        "remediation_effort": "low",
        "timeline_weeks": 4,
        "maturity_level": 2,
        "root_cause_category": "people",
        "evidence_quote": "Corporate address and phone given but no specific DPO or grievance officer named.",
    },
    {
        "requirement_id": "CH2.PURPOSE.1",
        "compliance_status": "partially_compliant",
        "current_state": "Purposes are listed in the privacy policy but described in generic terms: 'enhancing experience', 'lead generation', 'marketing campaigns'.",
        "gap_description": "Purpose descriptions are too broad to be 'specified' under Section 4(1). Data principals cannot meaningfully assess what they are consenting to. Financial data (Aadhaar, PAN, banking details) is especially under-specified.",
        "risk_level": "critical",
        "remediation_action": "Rewrite purpose descriptions to be granular and specific. Map each data element to specific, limited purposes. Remove catch-all purpose language. Have privacy counsel review.",
        "remediation_priority": 2,
        "remediation_effort": "medium",
        "timeline_weeks": 6,
        "maturity_level": 2,
        "root_cause_category": "policy",
        "evidence_quote": "Purposes listed but overly broad: enhancing experience, lead generation, marketing campaigns. Not specific enough.",
    },
    {
        "requirement_id": "CH2.PURPOSE.2",
        "compliance_status": "non_compliant",
        "current_state": "No documentation exists of Section 7 legitimate use cases for processing without consent.",
        "gap_description": "Processing of employee data, KYC data for property transactions, and regulatory compliance data likely occurs under Section 7 legitimate uses but has not been documented. This creates legal uncertainty.",
        "risk_level": "high",
        "remediation_action": "Conduct a processing inventory. For each processing activity that does not rely on consent, document the applicable Section 7 legitimate use basis. Have legal counsel sign off.",
        "remediation_priority": 2,
        "remediation_effort": "medium",
        "timeline_weeks": 6,
        "maturity_level": 0,
        "root_cause_category": "policy",
        "evidence_quote": "No documentation of Section 7 legitimate use cases.",
    },
    {
        "requirement_id": "CH2.MINIMIZE.1",
        "compliance_status": "partially_compliant",
        "current_state": "Organization collects Aadhaar, PAN, banking details, and detailed financial information for purposes including lead generation and marketing — categories that appear excessive for those purposes.",
        "gap_description": "No data minimization review has been conducted. Sensitive financial identifiers collected at early lead/inquiry stage likely exceed what is necessary for marketing or CRM purposes.",
        "risk_level": "high",
        "remediation_action": "Conduct a data mapping and minimization review. Remove collection of Aadhaar/PAN from lead generation flows; restrict sensitive financial data collection to transaction-stage only. Document justification for each data element.",
        "remediation_priority": 2,
        "remediation_effort": "medium",
        "timeline_weeks": 8,
        "maturity_level": 2,
        "root_cause_category": "policy",
        "evidence_quote": "No explicit minimization. Collects Aadhaar, PAN, banking details, financial data — may be more than necessary for some purposes.",
    },
    {
        "requirement_id": "CH2.MINIMIZE.2",
        "compliance_status": "partially_compliant",
        "current_state": "Privacy policy states data is retained 'as long as necessary' with no defined timeframes. Physical PII (paper documents) stored with no clear retention endpoint.",
        "gap_description": "Without defined retention periods, personal data is retained indefinitely in practice. Physical document storage especially presents risk — paper records with PAN, Aadhaar, and financial data held without systematic review.",
        "risk_level": "high",
        "remediation_action": "Define retention periods for each data category. Implement a retention schedule covering digital and physical records. Set up systematic deletion/destruction workflows triggered at retention expiry.",
        "remediation_priority": 2,
        "remediation_effort": "medium",
        "timeline_weeks": 8,
        "maturity_level": 1,
        "root_cause_category": "process",
        "evidence_quote": "Policy says retained as long as necessary but no specifics. Physical PII storage with unclear retention.",
    },
    {
        "requirement_id": "CH2.MINIMIZE.3",
        "compliance_status": "non_compliant",
        "current_state": "No documented retention schedules exist. Physical documents containing PII are stored indefinitely with no destruction procedure.",
        "gap_description": "Section 8(7) requires personal data to be erased when purpose is fulfilled. Without documented schedules and deletion procedures, systematic compliance is impossible to demonstrate or enforce.",
        "risk_level": "medium",
        "remediation_action": "Create formal data retention schedule covering all data categories. Implement secure document destruction for physical PII. Configure automated deletion in CRM/database systems. Assign retention owner.",
        "remediation_priority": 2,
        "remediation_effort": "medium",
        "timeline_weeks": 8,
        "maturity_level": 0,
        "root_cause_category": "process",
        "evidence_quote": "No documented retention schedules or systematic deletion procedures. Physical documents stored indefinitely.",
    },
    {
        "requirement_id": "CH2.ACCURACY.1",
        "compliance_status": "partially_compliant",
        "current_state": "Data principals can request corrections via contact mechanism. No proactive accuracy measures. Internal tool has permission leaks that could allow unauthorized data modifications.",
        "gap_description": "Reactive accuracy management only. Permission leaks in internal CRM/sales tool create risk of unauthorized or erroneous data changes. No systematic data quality process for decision-relevant data.",
        "risk_level": "medium",
        "remediation_action": "Fix permission leaks in internal tool (critical path). Implement role-based access for data modification. Add data quality validation rules for key personal data fields.",
        "remediation_priority": 3,
        "remediation_effort": "medium",
        "timeline_weeks": 6,
        "maturity_level": 2,
        "root_cause_category": "technology",
        "evidence_quote": "Users can request corrections but no proactive accuracy measures. Internal tool has permission leaks.",
    },
    {
        "requirement_id": "CH2.SECURITY.1",
        "compliance_status": "partially_compliant",
        "current_state": "Encryption, firewalls, IDS, and periodic security audits mentioned in policy. However, permission leaks in internal pre-sales/sales/marketing tool indicate technical controls have gaps. Physical PII storage lacks documented security controls.",
        "gap_description": "The permission leaks are a material security gap — unauthorized access to personal data is a direct Section 8(4) violation. Physical document security is inadequately controlled. Audit evidence of actual safeguards is limited.",
        "risk_level": "critical",
        "remediation_action": "Remediate permission leaks in internal tool immediately. Implement physical document security (locked storage, access log). Conduct security assessment covering both digital and physical personal data stores.",
        "remediation_priority": 1,
        "remediation_effort": "medium",
        "timeline_weeks": 8,
        "maturity_level": 2,
        "root_cause_category": "technology",
        "evidence_quote": "Internal tool has permission leaks and physical PII storage raises security concerns.",
    },
    {
        "requirement_id": "CH2.SECURITY.2",
        "compliance_status": "partially_compliant",
        "current_state": "Encryption and password-protected storage mentioned. Permission leaks in pre-sales/sales/marketing tool indicate access controls do not enforce least privilege.",
        "gap_description": "Least-privilege access control is not implemented. Sales, pre-sales, and marketing staff likely have over-broad access to personal data beyond their role requirements. No documented RBAC framework.",
        "risk_level": "critical",
        "remediation_action": "Conduct access rights review across all internal systems. Implement RBAC with least-privilege for all systems processing personal data. Fix permission leaks. Document access control policy.",
        "remediation_priority": 1,
        "remediation_effort": "medium",
        "timeline_weeks": 6,
        "maturity_level": 2,
        "root_cause_category": "technology",
        "evidence_quote": "Permission leaks in internal pre-sales/sales/marketing tool suggest access controls are insufficient. No explicit least-privilege.",
    },
    {
        "requirement_id": "CH2.SECURITY.3",
        "compliance_status": "partially_compliant",
        "current_state": "Third-party vendors are contractually obligated for confidentiality, but the scope and specificity of processor agreements relative to DPDPA obligations is unclear.",
        "gap_description": "Existing contracts may not specifically mandate DPDPA-compliant security measures, restrict processing to instructed purposes, or require breach notification to Prestige Estates. Section 8(2) requires explicit contractual obligations on processors.",
        "risk_level": "high",
        "remediation_action": "Review all data processor contracts. Add DPDPA-specific clauses covering: security obligations, processing restrictions, breach notification to data fiduciary, audit rights. Engage legal counsel to draft standard Data Processing Addendum.",
        "remediation_priority": 2,
        "remediation_effort": "medium",
        "timeline_weeks": 8,
        "maturity_level": 2,
        "root_cause_category": "governance",
        "evidence_quote": "Third parties contractually obligated for confidentiality but scope of processor agreements unclear.",
    },
    {
        "requirement_id": "CH3.ACCESS.1",
        "compliance_status": "compliant",
        "current_state": "Right to access personal data and processing activities is explicitly listed in the privacy policy.",
        "gap_description": "Formal right exists. Implementation relies on manual request processing via contact mechanism. No self-service access portal — acceptable for MVP but should be reviewed as data volumes grow.",
        "risk_level": "low",
        "remediation_action": "No immediate action required. Consider building a self-service data access portal in future to improve efficiency and demonstrate systematic compliance.",
        "remediation_priority": 4,
        "remediation_effort": "medium",
        "timeline_weeks": 12,
        "maturity_level": 3,
        "root_cause_category": "process",
        "evidence_quote": "Right to access explicitly listed in privacy policy.",
    },
    {
        "requirement_id": "CH3.CORRECT.1",
        "compliance_status": "compliant",
        "current_state": "Right to correction and completion of inaccurate data is explicitly listed in the privacy policy.",
        "gap_description": "Mechanism exists via contact. No automated correction workflow. Acceptable for current scale.",
        "risk_level": "low",
        "remediation_action": "No immediate action required. Document internal correction handling process and SLA.",
        "remediation_priority": 4,
        "remediation_effort": "low",
        "timeline_weeks": 4,
        "maturity_level": 3,
        "root_cause_category": "process",
        "evidence_quote": "Right to correction explicitly listed.",
    },
    {
        "requirement_id": "CH3.CORRECT.2",
        "compliance_status": "compliant",
        "current_state": "Right to erasure and deletion is explicitly listed in the privacy policy.",
        "gap_description": "Erasure mechanism exists in policy. Actual deletion capability depends on retention schedule implementation (see CH2.MINIMIZE.3 gap). Physical document deletion is not yet systematic.",
        "risk_level": "low",
        "remediation_action": "Align erasure procedure with retention schedule implementation. Ensure physical document destruction is included in erasure response.",
        "remediation_priority": 4,
        "remediation_effort": "low",
        "timeline_weeks": 4,
        "maturity_level": 3,
        "root_cause_category": "process",
        "evidence_quote": "Right to erasure/deletion explicitly listed.",
    },
    {
        "requirement_id": "CH3.GRIEVANCE.1",
        "compliance_status": "partially_compliant",
        "current_state": "Generic corporate contact details (address, phone, email) provided. No dedicated grievance officer or formal grievance intake mechanism.",
        "gap_description": "Section 13(1) requires a designated person or officer to handle grievances. A generic corporate contact does not satisfy this. No acknowledgment process or tracking system for grievances.",
        "risk_level": "critical",
        "remediation_action": "Appoint a designated Grievance Officer (or assign this role explicitly). Publish their contact details in the privacy policy. Create a formal grievance intake process with acknowledgment within 48 hours.",
        "remediation_priority": 2,
        "remediation_effort": "low",
        "timeline_weeks": 4,
        "maturity_level": 2,
        "root_cause_category": "people",
        "evidence_quote": "Contact details given (corporate address, phone, email) but no dedicated grievance officer or formal mechanism.",
    },
    {
        "requirement_id": "CH3.GRIEVANCE.2",
        "compliance_status": "non_compliant",
        "current_state": "No defined response timeline or SLA for grievances. Privacy policy does not mention the Data Protection Board as an escalation channel.",
        "gap_description": "Section 13(2) requires timely response and informing data principals of their right to approach the DPB if unresolved. Both elements are absent. Data principals have no visibility into resolution expectations.",
        "risk_level": "high",
        "remediation_action": "Define and publish a grievance response SLA (e.g., 30-day resolution). Add explicit reference to DPB escalation right in the privacy policy and grievance acknowledgment communications.",
        "remediation_priority": 2,
        "remediation_effort": "low",
        "timeline_weeks": 4,
        "maturity_level": 0,
        "root_cause_category": "people",
        "evidence_quote": "No response timeline or SLA mentioned for grievances. No mention of right to approach DPB.",
    },
    {
        "requirement_id": "CH3.NOMINATE.1",
        "compliance_status": "non_compliant",
        "current_state": "No nomination mechanism exists. Section 14 right to nominate a successor for data rights is not mentioned in the privacy policy.",
        "gap_description": "No mechanism for data principals to nominate another person to exercise their data rights in the event of death or incapacity. Policy is silent on this right.",
        "risk_level": "medium",
        "remediation_action": "Implement a nomination feature in account settings or via a formal written request process. Update privacy policy to describe the right and how it can be exercised.",
        "remediation_priority": 3,
        "remediation_effort": "medium",
        "timeline_weeks": 8,
        "maturity_level": 0,
        "root_cause_category": "process",
        "evidence_quote": "No nomination mechanism mentioned or known.",
    },
    {
        "requirement_id": "CH4.CHILD.1",
        "compliance_status": "non_compliant",
        "current_state": "No explicit commitment to abstaining from tracking, behavioral monitoring, or targeted advertising directed at children under 18.",
        "gap_description": "Digital marketing activity (email campaigns, lead nurturing, website analytics) may reach under-18 users without appropriate restrictions. Section 9(2) prohibition on tracking children is absolute.",
        "risk_level": "critical",
        "remediation_action": "Add explicit policy commitment to no tracking or behavioral monitoring of under-18 users. Review digital marketing suppression lists and analytics configurations. Implement child flag in CRM to suppress from marketing.",
        "remediation_priority": 1,
        "remediation_effort": "medium",
        "timeline_weeks": 6,
        "maturity_level": 0,
        "root_cause_category": "policy",
        "evidence_quote": "No explicit commitment to not tracking/monitoring children on website.",
    },
    {
        "requirement_id": "CH4.CHILD.2",
        "compliance_status": "non_compliant",
        "current_state": "Processing of children's data and its potential effects on wellbeing is not addressed in any policy or process documentation.",
        "gap_description": "Section 9(3) prohibits processing that is detrimental to children's wellbeing. No risk assessment has been conducted to identify whether any current processing could have such effects. Property inquiry data collection from minors is unaddressed.",
        "risk_level": "critical",
        "remediation_action": "Conduct a focused risk assessment on all processing activities that could involve children's data. Update policy to explicitly address this prohibition. Add wellbeing-impact review to DPIA template.",
        "remediation_priority": 1,
        "remediation_effort": "medium",
        "timeline_weeks": 6,
        "maturity_level": 0,
        "root_cause_category": "policy",
        "evidence_quote": "Not addressed in policy.",
    },
    {
        "requirement_id": "CH4.CHILD.3",
        "compliance_status": "non_compliant",
        "current_state": "No age verification mechanisms on website or app. No way to identify users under 18 at point of data collection.",
        "gap_description": "Without age verification, Prestige Estates cannot enforce the under-18 protections mandated by Section 9. All digital collection points (enquiry forms, account registration, callback requests) are accessible to minors.",
        "risk_level": "high",
        "remediation_action": "Implement age verification or age attestation on all digital registration and enquiry forms. Evaluate proportionate technical solutions (self-declaration with parental consent workflow for identified minors).",
        "remediation_priority": 2,
        "remediation_effort": "high",
        "timeline_weeks": 12,
        "maturity_level": 0,
        "root_cause_category": "technology",
        "evidence_quote": "No age verification mechanisms on website or app.",
    },
    {
        "requirement_id": "CH4.SDF.1",
        "compliance_status": "non_compliant",
        "current_state": "No Data Protection Officer appointed. Organization has not formally assessed SDF designation threshold, though scale (1000+ employees, large consumer data volumes) suggests SDF risk is high.",
        "gap_description": "If designated as an SDF (which is likely given scale and sensitivity of data including Aadhaar, PAN, financial data), a DPO based in India must be appointed under Section 10(2)(a). Current gap leaves the organization exposed to Board sanctions.",
        "risk_level": "critical",
        "remediation_action": "Formally assess SDF designation eligibility. If applicable (highly likely), appoint an India-based DPO. Register DPO with the Board. Define DPO mandate, authority, and reporting line to Board level.",
        "remediation_priority": 1,
        "remediation_effort": "high",
        "timeline_weeks": 12,
        "maturity_level": 0,
        "root_cause_category": "governance",
        "evidence_quote": "No Data Protection Officer appointed. Company likely qualifies as SDF given 1000+ employees and large customer data volumes.",
    },
    {
        "requirement_id": "CH4.SDF.2",
        "compliance_status": "non_compliant",
        "current_state": "No independent Data Auditor appointed to evaluate DPDPA compliance.",
        "gap_description": "Section 10(2)(b) requires SDFs to appoint an independent auditor. No such appointment exists. Without DPO in place (CH4.SDF.1), this cannot be effectively executed.",
        "risk_level": "high",
        "remediation_action": "After appointing DPO, initiate procurement of an independent Data Auditor (specialist firm or qualified individual). Define audit scope covering all data processing activities.",
        "remediation_priority": 2,
        "remediation_effort": "high",
        "timeline_weeks": 16,
        "maturity_level": 0,
        "root_cause_category": "governance",
        "evidence_quote": "No independent Data Auditor appointed.",
    },
    {
        "requirement_id": "CH4.SDF.3",
        "compliance_status": "non_compliant",
        "current_state": "No Data Protection Impact Assessments have been conducted for any processing activity.",
        "gap_description": "Section 10(2)(c) mandates periodic DPIAs for SDFs. High-risk processing activities (Aadhaar/PAN collection, children's data, large-scale consumer profiling for marketing) have never been assessed for privacy impact.",
        "risk_level": "high",
        "remediation_action": "Develop a DPIA methodology and template. Conduct initial DPIAs for highest-risk processing activities: sensitive data collection, marketing profiling, cross-system data sharing. Integrate DPIA into product/process change management.",
        "remediation_priority": 2,
        "remediation_effort": "medium",
        "timeline_weeks": 10,
        "maturity_level": 0,
        "root_cause_category": "governance",
        "evidence_quote": "No Data Protection Impact Assessments conducted.",
    },
    {
        "requirement_id": "CH4.SDF.4",
        "compliance_status": "non_compliant",
        "current_state": "No periodic DPDPA compliance audits have been conducted.",
        "gap_description": "Section 10(2)(d) requires periodic audits of data processing activities for SDFs. No audit program exists. Compliance gaps identified in this assessment would not have been detected through internal processes.",
        "risk_level": "high",
        "remediation_action": "Establish an annual DPDPA compliance audit calendar. Define audit scope and methodology with the appointed Data Auditor. Implement a tracking mechanism for audit findings and remediation.",
        "remediation_priority": 3,
        "remediation_effort": "medium",
        "timeline_weeks": 12,
        "maturity_level": 0,
        "root_cause_category": "governance",
        "evidence_quote": "No periodic DPDPA compliance audits conducted.",
    },
    {
        "requirement_id": "CM.RECORDS.1",
        "compliance_status": "partially_compliant",
        "current_state": "CRM system tracks some consent-related data, but there is no structured audit trail. Multiple data collection points (website, phone, site visits, head office) have inconsistent or absent consent records.",
        "gap_description": "Consent records are incomplete across channels. Physical/offline collection points (site visits, head office) have no systematic consent recording. CRM records lack timestamp, purpose scope, and withdrawal history — essential audit trail elements.",
        "risk_level": "high",
        "remediation_action": "Implement a centralized consent record system that captures: timestamp, channel, purpose, data principal identity, consent text version, and withdrawal status. Integrate across CRM, website, and offline forms. Run a backfill exercise for existing records.",
        "remediation_priority": 2,
        "remediation_effort": "high",
        "timeline_weeks": 12,
        "maturity_level": 1,
        "root_cause_category": "process",
        "evidence_quote": "Internal CRM tool tracks some consent data but no structured audit trail. Multiple data collection points (site visits, head office, online) with inconsistent tracking.",
    },
    {
        "requirement_id": "CM.RECORDS.2",
        "compliance_status": "non_compliant",
        "current_state": "No process exists to refresh or re-obtain consent when processing purposes change or after a defined period.",
        "gap_description": "Consents obtained years ago (pre-DPDPA era) are being relied upon without refresh. If Prestige Estates changes its processing purposes or launches new products/features, no consent re-validation mechanism exists.",
        "risk_level": "medium",
        "remediation_action": "Design a consent refresh workflow: define trigger conditions (purpose change, periodic review, X years elapsed). Implement automated consent renewal campaigns for aged consents. Integrate with consent records system.",
        "remediation_priority": 3,
        "remediation_effort": "medium",
        "timeline_weeks": 8,
        "maturity_level": 0,
        "root_cause_category": "process",
        "evidence_quote": "No process to refresh consent when purposes change.",
    },
    {
        "requirement_id": "CM.GRANULAR.1",
        "compliance_status": "non_compliant",
        "current_state": "All-or-nothing consent at all data collection points. No per-purpose consent options available to data principals.",
        "gap_description": "Section 6(3) requires itemised consent for multiple purposes. Prestige Estates collects consent for service delivery, lead management, marketing, analytics, and third-party sharing under a single consent. Data principals cannot accept some purposes and decline others.",
        "risk_level": "high",
        "remediation_action": "Redesign all consent interfaces to present per-purpose checkboxes. Implement logic to enforce that service-essential data processing continues even when marketing consent is declined. Separate optional from mandatory purposes clearly.",
        "remediation_priority": 1,
        "remediation_effort": "high",
        "timeline_weeks": 10,
        "maturity_level": 0,
        "root_cause_category": "process",
        "evidence_quote": "No granular per-purpose consent options. Likely all-or-nothing consent at data collection points.",
    },
    {
        "requirement_id": "CM.GRANULAR.2",
        "compliance_status": "non_compliant",
        "current_state": "Access to services and follow-up appears conditional on blanket consent including marketing. Multiple collection points (site visits, head office, online) likely bundle service consent with commercial consent.",
        "gap_description": "Section 6(1) prohibits consent bundling — service access cannot be conditioned on consent for processing not necessary for that service. Marketing/analytics consent must be freely given and declinable without loss of core service.",
        "risk_level": "critical",
        "remediation_action": "Audit all service flows to identify where service access is conditioned on optional consent. Decouple service delivery from marketing/analytics consent. Redesign physical and digital collection flows. Remove any dark patterns (pre-ticked boxes, confusing opt-out language).",
        "remediation_priority": 1,
        "remediation_effort": "high",
        "timeline_weeks": 10,
        "maturity_level": 0,
        "root_cause_category": "process",
        "evidence_quote": "Services appear bundled with marketing consent. Multiple collection points (site visits, head office) likely require blanket consent.",
    },
    {
        "requirement_id": "CB.TRANSFER.1",
        "compliance_status": "compliant",
        "current_state": "All personal data is processed and stored within India. No cross-border data transfers identified.",
        "gap_description": "No gap. Data localisation is effectively maintained. Monitor if cloud service providers or new vendor relationships introduce cross-border flows.",
        "risk_level": "low",
        "remediation_action": "Maintain a data flow inventory to ensure any future international data transfers are reviewed against Section 16 requirements before implementation.",
        "remediation_priority": 4,
        "remediation_effort": "low",
        "timeline_weeks": 4,
        "maturity_level": 5,
        "root_cause_category": "governance",
        "evidence_quote": "No cross-border transfers — data stays in India.",
    },
    {
        "requirement_id": "CB.TRANSFER.2",
        "compliance_status": "compliant",
        "current_state": "No cross-border transfers. Section 16 contractual safeguard obligations are not triggered.",
        "gap_description": "Not applicable at present. Monitor vendor onboarding for international processors.",
        "risk_level": "low",
        "remediation_action": "Include cross-border transfer check in vendor onboarding checklist.",
        "remediation_priority": 4,
        "remediation_effort": "low",
        "timeline_weeks": 2,
        "maturity_level": 5,
        "root_cause_category": "governance",
        "evidence_quote": "No cross-border transfers.",
    },
    {
        "requirement_id": "CB.TRANSFER.3",
        "compliance_status": "compliant",
        "current_state": "No cross-border transfers. Data localisation obligations are inherently met.",
        "gap_description": "Not applicable at present. Future localisation mandates should be monitored.",
        "risk_level": "low",
        "remediation_action": "Monitor Government notifications on mandatory data localisation categories.",
        "remediation_priority": 4,
        "remediation_effort": "low",
        "timeline_weeks": 2,
        "maturity_level": 5,
        "root_cause_category": "governance",
        "evidence_quote": "No cross-border transfers. Data localised in India.",
    },
    {
        "requirement_id": "BN.NOTIFY.1",
        "compliance_status": "compliant",
        "current_state": "Privacy policy explicitly commits to notifying the Data Protection Board of India within 72 hours of a personal data breach.",
        "gap_description": "Policy commitment exists. Actual drill/test of notification workflow has not been confirmed. 72-hour SLA requires pre-built notification templates and clear escalation chain.",
        "risk_level": "low",
        "remediation_action": "Conduct a tabletop exercise for breach notification. Pre-draft DPBI notification template. Define escalation chain: who authorizes notification to DPBI.",
        "remediation_priority": 4,
        "remediation_effort": "low",
        "timeline_weeks": 4,
        "maturity_level": 3,
        "root_cause_category": "process",
        "evidence_quote": "Policy commits to notifying DPBI within 72 hours of a breach.",
    },
    {
        "requirement_id": "BN.NOTIFY.2",
        "compliance_status": "compliant",
        "current_state": "Privacy policy explicitly commits to notifying affected data principals of personal data breaches.",
        "gap_description": "Policy commitment exists. Contact database quality and completeness will determine ability to execute notifications at scale. Notification templates should be pre-prepared.",
        "risk_level": "low",
        "remediation_action": "Pre-draft data principal breach notification templates. Validate that contact data (email/phone) is maintained with sufficient quality to execute mass notifications if needed.",
        "remediation_priority": 4,
        "remediation_effort": "low",
        "timeline_weeks": 4,
        "maturity_level": 3,
        "root_cause_category": "process",
        "evidence_quote": "Policy commits to notifying affected individuals.",
    },
    {
        "requirement_id": "BN.NOTIFY.3",
        "compliance_status": "compliant",
        "current_state": "A documented incident response plan (IRP) exists.",
        "gap_description": "IRP exists per user confirmation. Recommend verifying it includes DPDPA-specific breach classification, the 72-hour DPBI notification trigger, and individual notification procedures.",
        "risk_level": "low",
        "remediation_action": "Review IRP for DPDPA alignment. Ensure it covers: breach classification criteria, DPBI 72-hour notification trigger, individual notification procedure, and post-incident review.",
        "remediation_priority": 4,
        "remediation_effort": "low",
        "timeline_weeks": 3,
        "maturity_level": 4,
        "root_cause_category": "process",
        "evidence_quote": "Documented incident response plan exists per user confirmation.",
    },
    {
        "requirement_id": "BN.NOTIFY.4",
        "compliance_status": "partially_compliant",
        "current_state": "IRP exists but it is unclear whether a formal breach register is maintained as a systematic record of all incidents.",
        "gap_description": "Section 8(6) requires maintaining records of breaches including facts, effects, and remedial actions. A register distinct from IRP is needed as a durable audit trail of all breach events.",
        "risk_level": "medium",
        "remediation_action": "Create a formal breach register (spreadsheet or GRC tool). Define mandatory fields: breach date, discovery date, nature of breach, data categories affected, scope, notifications sent, remediation actions, closure date.",
        "remediation_priority": 3,
        "remediation_effort": "low",
        "timeline_weeks": 4,
        "maturity_level": 2,
        "root_cause_category": "process",
        "evidence_quote": "IRP exists but unclear if a formal breach register is maintained.",
    },
]

# ─── Executive Summary ─────────────────────────────────────────────────────
EXECUTIVE_SUMMARY = """Prestige Estates Projects Limited demonstrates foundational awareness of data privacy obligations, with a published privacy policy, incident response plan, and stated data principal rights. However, the organization faces significant structural gaps across consent management, children's data protection, and governance that represent material regulatory risk under the Digital Personal Data Protection Act, 2023.

Critical findings: (1) Consent architecture is fundamentally non-compliant — bundled, hard to withdraw, and applied with the wrong age threshold for children. (2) No DPO has been appointed despite the organization's scale strongly suggesting SDF designation applies. (3) Internal systems have identified permission leaks creating direct unauthorized data access risk. (4) No retention schedules or systematic deletion procedures exist, resulting in indefinite PII retention.

Prestige Estates collects uniquely sensitive data — Aadhaar, PAN, banking details, and property transaction data — across a complex multi-channel operation (online, phone, site visits, head office). This data profile, combined with 1,000+ employees and large-scale consumer data volumes, places the company at high likelihood of Significant Data Fiduciary designation, triggering additional obligations that are currently unmet.

The remediation path is achievable within 12-18 months through five coordinated initiatives spanning consent platform redesign, governance structure establishment, policy documentation, technology security uplift, and process formalization. Immediate priorities are the DPO appointment, permission leak remediation, and consent architecture redesign."""


def seed():
    db = SessionLocal()
    try:
        # ── 1. Verify assessment exists ──────────────────────────────────────
        assessment = db.get(Assessment, NEW_ASSESSMENT_ID)
        if not assessment:
            print(f"ERROR: Assessment {NEW_ASSESSMENT_ID} not found.")
            return

        print(f"Target assessment: {assessment.company_name} ({NEW_ASSESSMENT_ID})")

        # ── 2. Copy responses from old assessment ────────────────────────────
        existing_responses = (
            db.query(QuestionnaireResponse)
            .filter(QuestionnaireResponse.assessment_id == NEW_ASSESSMENT_ID)
            .count()
        )
        if existing_responses == 0:
            old_responses = (
                db.query(QuestionnaireResponse)
                .filter(QuestionnaireResponse.assessment_id == OLD_ASSESSMENT_ID)
                .all()
            )
            old_answer_map = {
                "yes": "fully_implemented",
                "partial": "partially_implemented",
                "no": "not_implemented",
                "not_applicable": "not_applicable",
            }
            for r in old_responses:
                new_r = QuestionnaireResponse(
                    assessment_id=NEW_ASSESSMENT_ID,
                    question_id=r.question_id,
                    answer=old_answer_map.get(r.answer, r.answer),
                    notes=r.notes,
                    na_reason=r.na_reason,
                    confidence=r.confidence,
                )
                db.add(new_r)
            db.flush()
            print(f"Copied {len(old_responses)} responses (mapped to new GRC scale).")
        else:
            print(f"Responses already exist ({existing_responses}), skipping copy.")

        # ── 3. Delete any existing report ────────────────────────────────────
        existing_report = (
            db.query(GapReport)
            .filter(GapReport.assessment_id == NEW_ASSESSMENT_ID)
            .first()
        )
        if existing_report:
            db.query(GapItem).filter(GapItem.report_id == existing_report.id).delete()
            db.query(Initiative).filter(Initiative.report_id == existing_report.id).delete()
            db.delete(existing_report)
            db.flush()
            print("Deleted existing report + items + initiatives.")

        # ── 4. Compute scores ────────────────────────────────────────────────
        req_lookup = {r["id"]: r for r in get_all_requirements()}

        scores = compute_scores(GAP_ASSESSMENTS)
        print(f"Overall score: {scores['overall_score']} — {scores['overall_rating']}")

        # ── 5. Create report ─────────────────────────────────────────────────
        report = GapReport(
            assessment_id=NEW_ASSESSMENT_ID,
            overall_score=scores["overall_score"],
            chapter_scores=json.dumps(scores["chapter_scores"]),
            executive_summary=EXECUTIVE_SUMMARY,
            raw_ai_response="[Seeded directly by Claude Code — no API call made]",
        )
        db.add(report)
        db.flush()
        print(f"Created report: {report.id}")

        # ── 6. Create gap items ──────────────────────────────────────────────
        _REQ_TITLES = {r["id"]: r["title"] for r in get_all_requirements()}
        _REQ_CHAPTERS = {r["id"]: r["chapter"] for r in get_all_requirements()}

        for a in GAP_ASSESSMENTS:
            item = GapItem(
                report_id=report.id,
                requirement_id=a["requirement_id"],
                chapter=_REQ_CHAPTERS.get(a["requirement_id"], "unknown"),
                requirement_title=_REQ_TITLES.get(a["requirement_id"], a["requirement_id"]),
                compliance_status=a["compliance_status"],
                current_state=a.get("current_state", ""),
                gap_description=a.get("gap_description", ""),
                risk_level=a.get("risk_level", "medium"),
                remediation_action=a.get("remediation_action", ""),
                remediation_priority=a.get("remediation_priority", 3),
                remediation_effort=a.get("remediation_effort", "medium"),
                timeline_weeks=a.get("timeline_weeks", 8),
                maturity_level=a.get("maturity_level"),
                root_cause_category=a.get("root_cause_category"),
                evidence_quote=a.get("evidence_quote"),
            )
            db.add(item)
        print(f"Created {len(GAP_ASSESSMENTS)} gap items.")

        # ── 7. Generate and save initiatives ─────────────────────────────────
        initiatives_data = generate_initiatives(GAP_ASSESSMENTS)
        for init_data in initiatives_data:
            initiative = Initiative(
                report_id=report.id,
                initiative_id=init_data["initiative_id"],
                title=init_data["title"],
                root_cause=init_data["root_cause"],
                root_cause_category=init_data["root_cause_category"],
                requirements_addressed=json.dumps(init_data["requirements_addressed"]),
                combined_effort=init_data["combined_effort"],
                combined_timeline_weeks=init_data["combined_timeline_weeks"],
                priority=init_data["priority"],
                budget_estimate_band=init_data.get("budget_estimate_band"),
                suggested_approach=init_data["suggested_approach"],
            )
            db.add(initiative)
        print(f"Generated {len(initiatives_data)} initiatives.")
        for init_data in initiatives_data:
            print(f"  [{init_data['root_cause_category']}] {init_data['title']} (priority {init_data['priority']})")

        # ── 8. Update assessment status ───────────────────────────────────────
        assessment.status = "completed"
        db.commit()
        db.refresh(report)

        print(f"\nDone. Report ID: {report.id}")
        print(f"Overall: {scores['overall_score']}% — {scores['overall_rating']}")

        # Print chapter breakdown
        for ch, data in scores["chapter_scores"].items():
            print(f"  {data['title']}: {data['score']}% ({data['rating']})")

    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
