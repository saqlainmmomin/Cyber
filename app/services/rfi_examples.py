"""Version-controlled examples of evidence a client can send with an RFI.

These describe useful artifacts and their context, not control assessment answers.
"""

DOCUMENT_EXAMPLES: dict[str, dict[str, str]] = {
    "access_control_policy": {
        "example_artifacts": "Access policy and a dated user list per system with reviewer sign-off and removals.",
        "good_looks_like": "Identify each system, reviewer and review date. Link removal decisions to completed tickets.",
    },
    "age_verification": {
        "example_artifacts": "Age check workflow, screen captures and records of completed checks.",
        "good_looks_like": "Show where the check occurs and how its result is recorded.",
    },
    "application_security_testing": {
        "example_artifacts": "Security requirements, test reports and release acceptance records.",
        "good_looks_like": "Identify the application version, test date, findings and follow-up decisions.",
    },
    "asset_inventory": {
        "example_artifacts": "Export of hardware, software and data inventories with owners and classifications.",
        "good_looks_like": "Include an export date and explain which systems and locations it covers.",
    },
    "audit_reports": {
        "example_artifacts": "Privacy audit reports and the associated action tracker.",
        "good_looks_like": "Include the audit scope, date, reviewer and status of each follow-up action.",
    },
    "backup": {
        "example_artifacts": "Backup schedule, job results and restore test records.",
        "good_looks_like": "Identify the systems tested, test dates, results and unresolved issues.",
    },
    "breach_procedure": {
        "example_artifacts": "Incident response plan, escalation contacts and notification workflow.",
        "good_looks_like": "Include the current version, owner and records of any exercises or use.",
    },
    "business_continuity": {
        "example_artifacts": "Continuity and recovery plans with exercise reports.",
        "good_looks_like": "Identify the services covered, exercise dates, outcomes and follow-up actions.",
    },
    "change_management": {
        "example_artifacts": "Change procedure and tickets showing review, approval and deployment.",
        "good_looks_like": "Keep ticket dates, approvers, affected systems and rollback details visible.",
    },
    "cloud_services": {
        "example_artifacts": "Cloud service register and provider assurance reports.",
        "good_looks_like": "Identify each provider, service owner and the period covered by each report.",
    },
    "configuration_baselines": {
        "example_artifacts": "Hardening baseline and configuration exports from managed systems.",
        "good_looks_like": "Identify baseline versions, system names, export dates and recorded exceptions.",
    },
    "consent_form": {
        "example_artifacts": "Consent form, collection screen captures and withdrawal workflow.",
        "good_looks_like": "Include the form version, purposes displayed and how consent choices are recorded.",
    },
    "consent_forms": {
        "example_artifacts": "Consent forms, collection screen captures and withdrawal workflow.",
        "good_looks_like": "Include form versions, purposes displayed and how consent choices are recorded.",
    },
    "cross_border_safeguards": {
        "example_artifacts": "Transfer register, destination list and agreements supporting overseas processing.",
        "good_looks_like": "Identify the data, recipient, destination and agreement that applies to each transfer.",
    },
    "cryptography_policy": {
        "example_artifacts": "Encryption standard, key inventory and key rotation records.",
        "good_looks_like": "Identify covered systems, key owners, dates and configuration sources.",
    },
    "csf_profiles": {
        "example_artifacts": "Current and target cybersecurity profiles with an improvement tracker.",
        "good_looks_like": "Include profile dates, scope, priorities and owners of planned actions.",
    },
    "data_flow_diagram": {
        "example_artifacts": "Data flow diagram and inventory of the data moving between systems.",
        "good_looks_like": "Label systems, data categories, recipients and the diagram revision date.",
    },
    "dpia": {
        "example_artifacts": "Impact assessment and its risk action tracker.",
        "good_looks_like": "Identify the processing activity, assessment date, reviewers and action owners.",
    },
    "dpia_reports": {
        "example_artifacts": "Impact assessment reports and their risk action trackers.",
        "good_looks_like": "Identify processing activities, assessment dates, reviewers and action owners.",
    },
    "dpo_appointment": {
        "example_artifacts": "DPO appointment letter, role description and reporting chart.",
        "good_looks_like": "Include the appointment date, work location, responsibilities and contact details.",
    },
    "exercise_records": {
        "example_artifacts": "Incident tabletop or recovery exercise report and action tracker.",
        "good_looks_like": "Identify the scenario, exercise date, participants, outcomes and action owners.",
    },
    "grievance_mechanism": {
        "example_artifacts": "Grievance procedure, contact page and case register.",
        "good_looks_like": "Show the responsible contact and dated records of intake, responses and closure.",
    },
    "hr_privacy_notices": {
        "example_artifacts": "Employee privacy notice and records of how it was shared.",
        "good_looks_like": "Include the notice version, covered employee groups and communication dates.",
    },
    "hr_security": {
        "example_artifacts": "HR security procedure and onboarding, screening and leaver checklists.",
        "good_looks_like": "Keep completion dates, responsible roles and links to asset or access actions visible.",
    },
    "incident_log": {
        "example_artifacts": "Incident register and investigation or closure reports.",
        "good_looks_like": "Include incident dates, owners, response actions and references to supporting records.",
    },
    "isms_audit_reports": {
        "example_artifacts": "Internal security audit reports and management review minutes.",
        "good_looks_like": "Include meeting or audit dates, scope, decisions and follow-up owners.",
    },
    "isms_scope": {
        "example_artifacts": "Approved scope statement with a diagram of the covered organisation and systems.",
        "good_looks_like": "Identify covered services, locations, boundaries and the document version.",
    },
    "leadership_oversight": {
        "example_artifacts": "Board or leadership cybersecurity reports and meeting minutes.",
        "good_looks_like": "Include meeting dates, attendees, decisions and assigned actions.",
    },
    "legal_register": {
        "example_artifacts": "Register of legal and contractual obligations with assigned owners.",
        "good_looks_like": "Identify each obligation, affected activities and the last review date.",
    },
    "logging_monitoring": {
        "example_artifacts": "Logging standard, alert records and dated log review tickets.",
        "good_looks_like": "Identify source systems, reviewers, timestamps and follow-up actions.",
    },
    "media_disposal": {
        "example_artifacts": "Disposal procedure, deletion records and destruction certificates.",
        "good_looks_like": "Link each record to the asset or data, disposal date and responsible person.",
    },
    "network_security": {
        "example_artifacts": "Network diagram and an export of current firewall rules with change dates.",
        "good_looks_like": "Identify firewalls, rule owners, review dates and decisions on unused or changed rules.",
    },
    "other": {
        "example_artifacts": "Relevant supporting document, system export or dated activity record.",
        "good_looks_like": "Explain which request it supports, its source and the period it covers.",
    },
    "outsourced_development": {
        "example_artifacts": "Development supplier contracts and delivery review records.",
        "good_looks_like": "Identify the supplier, project, review dates and accepted or outstanding findings.",
    },
    "parental_consent": {
        "example_artifacts": "Parental consent form, guardian check workflow and completed consent records.",
        "good_looks_like": "Show the form version, verification steps and dates of recorded decisions.",
    },
    "physical_security": {
        "example_artifacts": "Site access procedure, visitor logs and physical security inspection records.",
        "good_looks_like": "Identify the site, record dates, reviewers and follow-up actions.",
    },
    "privacy_policy": {
        "example_artifacts": "Current privacy notice and screen captures showing where people receive it.",
        "good_looks_like": "Include the notice version, covered services and publication or distribution dates.",
    },
    "processing_records": {
        "example_artifacts": "Processing activity register with data categories, purposes and recipients.",
        "good_looks_like": "Identify activity owners, systems used and the register review date.",
    },
    "remote_working_policy": {
        "example_artifacts": "Remote work and device policy with distribution or device configuration records.",
        "good_looks_like": "Identify the policy version, covered staff and dates of supporting records.",
    },
    "retention_policy": {
        "example_artifacts": "Retention schedule, deletion procedure and completed deletion records.",
        "good_looks_like": "Identify data categories, retention triggers, owners and deletion dates.",
    },
    "risk_assessment": {
        "example_artifacts": "Risk assessment method, risk register and treatment action tracker.",
        "good_looks_like": "Include assessment dates, risk owners, decisions and action status.",
    },
    "risk_management_strategy": {
        "example_artifacts": "Cybersecurity risk strategy and documented risk appetite decisions.",
        "good_looks_like": "Identify the approving body, approval date and scope of the strategy.",
    },
    "roles_responsibilities": {
        "example_artifacts": "Security organisation chart and responsibility matrix.",
        "good_looks_like": "Include named roles, assigned responsibilities and the last update date.",
    },
    "sdlc_policy": {
        "example_artifacts": "Development procedure, coding guidance and release review records.",
        "good_looks_like": "Identify repositories, release versions, reviewers and review dates.",
    },
    "security_policy": {
        "example_artifacts": "Approved security policy and records of its review and distribution.",
        "good_looks_like": "Include the policy version, owner, approval date and intended audience.",
    },
    "statement_of_applicability": {
        "example_artifacts": "Current applicability register with decisions and supporting references.",
        "good_looks_like": "Include the version, scope, decision owners and reasons for exclusions.",
    },
    "supplier_security": {
        "example_artifacts": "Supplier register, security review records and signed agreements.",
        "good_looks_like": "Link each supplier to its services, review dates, risks and follow-up actions.",
    },
    "training_records": {
        "example_artifacts": "Training materials and completion records for staff and specialist roles.",
        "good_looks_like": "Identify course versions, training dates, audiences and completion status.",
    },
    "vendor_agreement": {
        "example_artifacts": "Signed processor agreement and the associated service description.",
        "good_looks_like": "Identify parties, signing dates, data handled and the applicable service.",
    },
    "vendor_agreements": {
        "example_artifacts": "Signed processor agreements and associated service descriptions.",
        "good_looks_like": "Identify parties, signing dates, data handled and the applicable services.",
    },
    "vulnerability_management": {
        "example_artifacts": "Scan reports, patch records and vulnerability remediation tickets.",
        "good_looks_like": "Identify scanned systems, scan dates, issue owners and remediation status.",
    },
}
