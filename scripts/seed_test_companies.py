from __future__ import annotations

import json
import math
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "scripts" / "test_ground_truth.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app.models  # noqa: E402,F401
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.dpdpa.framework import get_all_requirements  # noqa: E402
from app.models.assessment import Assessment, AssessmentDocument  # noqa: E402
from app.models.desk_review import DeskReviewFinding, DeskReviewSummary  # noqa: E402
from app.models.initiative import Initiative  # noqa: E402
from app.models.questionnaire import QuestionnaireResponse  # noqa: E402
from app.models.report import GapItem, GapReport  # noqa: E402
from app.models.rfi import RFIDocument  # noqa: E402

NOW = datetime.now(timezone.utc)
ALL_REQUIREMENTS = get_all_requirements()
ALL_REQUIREMENT_IDS = [req["id"] for req in ALL_REQUIREMENTS]
REQUIREMENTS_BY_ID = {req["id"]: req for req in ALL_REQUIREMENTS}


@dataclass(frozen=True)
class SeedDocument:
    key: str
    filename: str
    file_type: str
    document_category: str
    text: str


def json_dumps(value: object) -> str:
    return json.dumps(value, indent=2, ensure_ascii=True)


def word_count(text: str) -> int:
    return len(text.split())


def page_count(text: str) -> int:
    return max(2, math.ceil(word_count(text) / 325))


def build_document(title: str, subtitle: str, sections: list[tuple[str, list[str]]]) -> str:
    parts = [title, subtitle, ""]
    for heading, paragraphs in sections:
        parts.append(heading)
        parts.append("")
        parts.extend(paragraphs)
        parts.append("")

    text = "\n".join(parts).strip() + "\n"
    words = word_count(text)
    if words < 500:
        padding_sections = [
            (
                "Document Control and Review",
                [
                    "This document is maintained as part of the organization's controlled policy set. The owner is responsible for keeping the contents accurate, coordinating stakeholder review when operational changes occur, and ensuring that superseded versions are archived in accordance with the applicable records management process. Controlled copies may be shared with legal, compliance, security, procurement, or customer diligence teams where the content is relevant to assurance or governance discussions.",
                    "Readers should interpret this document together with any related policies, standards, implementation guides, or contractual documents that apply to the underlying business process. Where a team-specific runbook or implementation record provides more detailed instructions, that operational record should be followed so long as it remains consistent with the principles set out here and any binding legal obligations applicable to the business.",
                    "The document owner may issue clarifications, supporting guidance, or updated annexes without republishing the entire document where the change is operational in nature and does not materially alter the stated control objective. Formal review is expected at least annually, and earlier where regulation, audit observations, customer commitments, or business expansion create a reason to revisit the approach described in this document.",
                ],
            )
        ]
        for heading, paragraphs in padding_sections:
            parts.append(heading)
            parts.append("")
            parts.extend(paragraphs)
            parts.append("")
        text = "\n".join(parts).strip() + "\n"
        words = word_count(text)

    if not 500 <= words <= 2000:
        raise ValueError(f"Document '{title}' must be 500-2000 words, found {words}")
    return text


def build_novapay_documents() -> list[SeedDocument]:
    privacy_policy = build_document(
        "NovaPay Solutions Pvt. Ltd. — Privacy Policy",
        "Effective Date: 15 January 2025 | Version 4.2 | Public",
        [
            (
                "1. Scope and Agreement to Processing",
                [
                    "NovaPay Solutions Pvt. Ltd. provides digital payment orchestration, merchant onboarding, wallet services, fraud monitoring, transaction analytics, and customer support to individuals and enterprise merchants across India. This Privacy Policy explains how personal data is collected, used, shared, stored, and processed when users access the NovaPay mobile application, merchant dashboard, or customer support channels. NovaPay holds ISO 27001 certification and SOC 2 Type II attestation for its information security management system.",
                    "By using our services, you consent to the collection and processing of your data as described in this policy. This includes identity verification, fraud prevention, transaction analysis, merchant reporting, product personalization, promotional communications, and platform improvement activities. Users are presented with this Privacy Policy and Terms of Service during account creation and must indicate acceptance before creating a wallet, linking a payment instrument, or completing merchant onboarding.",
                    "This policy applies to personal data collected directly from users, received from issuing banks and payment ecosystem participants, derived from transactional behavior, or generated through fraud monitoring and customer service interactions. NovaPay may retain information for compliance, investigation, or audit purposes while continuing to safeguard it through access restrictions and encryption.",
                ],
            ),
            (
                "2. Categories of Personal Data",
                [
                    "We process identity information including name, date of birth, PAN, mobile number, email address, billing address, and account credentials; financial information including bank account metadata, transaction references, settlement information, card token identifiers, and merchant payout details; and behavioral information including payment frequency, device activity, and feature interaction metrics.",
                    "We may analyze account activity and platform usage to improve our services, detect unusual patterns, and support merchant performance programs. We use personal data to verify identity, enable regulated payment services, detect and prevent fraud, maintain ledgers and audit trails, support merchants, personalize product education, and respond to legal requests.",
                    "Where multiple service features are provided through a unified customer journey, NovaPay processes the same personal data for more than one business purpose. We maintain internal role-based access controls, but our operating model uses a single master customer profile so that fraud prevention, payment execution, support operations, analytics, and promotional preference management function from a common record.",
                ],
            ),
            (
                "3. User Controls and Communications",
                [
                    "NovaPay maintains records evidencing that a user accepted the onboarding journey, including the acceptance timestamp, device identifier, IP address, and version of the policy in force at the time of sign-up. We do not currently operate a separate consent manager. Instead, user permissions are administered through the account experience, transactional workflows, and communications preferences embedded in the product.",
                    "Questions about this policy may be addressed to privacy@novapay.in. Certain operational messages, service alerts, fraud notifications, and account security messages will continue to be sent because they are integral to use of the platform. Additional terms governing use of NovaPay services are available in the Terms of Service.",
                    "This policy is reviewed and updated periodically to reflect changes in our practices, regulatory environment, and service features. Continued use of the NovaPay platform after a policy update constitutes acknowledgement of the revised policy. Users are encouraged to review the current policy from time to time to stay informed about our data processing practices.",
                ],
            ),
            (
                "4. Data Sharing and International Processing",
                [
                    "NovaPay uses specialized service providers to host infrastructure, process payments, detect fraud, send customer communications, and support analytics. These providers may process data under contractual arrangements or platform terms designed to support confidentiality, availability, and resilience. Access is limited to information reasonably required for service delivery, troubleshooting, reconciliation, and customer engagement.",
                    "Your data may be transferred to and processed in countries other than India where our service providers operate. We use service providers based in Singapore, the United States, and other jurisdictions to host infrastructure, process payments, support customer communications, and perform analytics. When we use such providers, we expect them to maintain commercially reasonable security safeguards appropriate to the nature of the services performed.",
                    "We may also disclose information to banking partners, card networks, payment aggregators, auditors, legal advisers, and regulators where necessary to deliver our services, investigate suspicious activity, or satisfy statutory requirements. Internal teams may review aggregated and user-level datasets to assess new features, reduce payment failures, and improve lifecycle engagement under enterprise security controls.",
                ],
            ),
        ],
    )

    terms = build_document(
        "NovaPay Consumer Terms of Service",
        "Version 6.1 | Applicable to wallet users and checkout customers",
        [
            (
                "1. Account Acceptance and Eligibility",
                [
                    "These Terms of Service govern the use of NovaPay payment services including digital wallet activation, merchant checkout, saved payment methods, customer support, reward features, and promotional programs. A user must review the Privacy Policy and these Terms before opening an account. By clicking the acceptance checkbox and continuing to use the service, the user agrees to the contract framework that enables NovaPay to provide regulated payment processing and related account support.",
                    "NovaPay services are intended for individuals aged 18 and over. The service depends on identity verification, fraud screening, transaction pattern review, support logging, and platform analytics carried out as part of a unified operational model. Users who do not accept this framework should not create an account or submit payment instructions through NovaPay.",
                    "NovaPay may amend these Terms from time to time to reflect changes in regulation, service features, partner requirements, or operational processes. Users are responsible for reviewing notice banners, in-product messages, and updated legal documentation made available through the application and website.",
                ],
            ),
            (
                "2. Communications, Analytics, and Data Processing",
                [
                    "NovaPay may send transactional confirmations, service updates, fraud alerts, product education, surveys, and promotional communications through email, SMS, WhatsApp, push notifications, and in-app messages. These communications support the secure operation of the service, help users understand new features, and allow NovaPay to inform users about offers relevant to their transaction profile and usage.",
                    "You may opt out of promotional communications at any time by updating your notification settings. Opting out of promotional communications does not affect NovaPay's processing of your transaction data, fraud signals, behavioral patterns, and account activity for service delivery and improvement purposes. Use of our payment services constitutes acceptance of our data processing practices.",
                    "NovaPay may determine eligibility for cashback programs, onboarding nudges, merchant offers, and product campaigns through internal models that consider account activity, engagement history, device behavior, and transactional signals. Service functionality is not separated into distinct legal modules for each communication or analytics purpose; rather, customer data is maintained within an integrated platform environment governed by these Terms and the Privacy Policy.",
                ],
            ),
            (
                "3. Operational Matters",
                [
                    "Users are responsible for keeping account credentials secure, maintaining current contact information, and promptly reporting unauthorized transactions, suspicious notifications, device loss, or suspected compromise. NovaPay may suspend transactions, temporarily restrict accounts, or request additional verification where activity suggests fraud risk or unusual usage patterns requiring review.",
                    "Disputes, refunds, chargebacks, failed payment investigations, and settlement exceptions are managed in accordance with partner network rules, applicable law, and NovaPay internal procedures. Relevant records may be retained for audit, fraud investigation, or evidentiary purposes while such matters remain open.",
                    "Nothing in these Terms limits NovaPay's ability to take actions reasonably required to satisfy legal obligations, maintain information security, or protect the integrity of the service. NovaPay may assign or delegate operational responsibilities to affiliated entities or service providers provided appropriate safeguards are maintained for continuity, confidentiality, and service reliability.",
                ],
            ),
        ],
    )

    retention = build_document(
        "NovaPay Data Retention and Archival Standard",
        "Document Owner: CISO Office | Version 2.1 | Last Review: 31 December 2024",
        [
            (
                "1. Purpose and Scope",
                [
                    "This standard establishes the principles used by NovaPay Solutions Pvt. Ltd. to retain, archive, and eventually dispose of information assets created or received in the course of payment operations, customer support, fraud management, legal compliance, finance, and product development. The standard is intended to support consistency across systems while recognizing that regulatory and contractual obligations may require records to remain available beyond the business process that first created them.",
                    "NovaPay retains personal data for as long as necessary to fulfill the purposes described in this policy, including meeting our legal, regulatory, audit, and business obligations. Payment transaction records are retained in accordance with the Payment and Settlement Systems Act and RBI directives. Other data is retained for the duration of the customer relationship and for a reasonable period thereafter.",
                    "The standard applies to application databases, data warehouses, log repositories, support tooling, payment partner exports, analytics environments, and archived backups. It does not prescribe system-specific retention schedules. Instead, product and functional owners remain responsible for aligning their data sets to the relevant legal and business context in consultation with Compliance, Finance, and Information Security.",
                ],
            ),
            (
                "2. Retention Administration",
                [
                    "Business owners must classify data according to the process it supports and retain it for as long as the related purpose, legal basis, or regulatory expectation remains relevant. Financial transaction records, KYC artifacts, customer communications, merchant onboarding files, fraud investigation materials, and operational logs may all be retained for different reasons. In practice, retention decisions should err on the side of preservation where a future request from a regulator, banking partner, or auditor is reasonably foreseeable.",
                    "NovaPay maintains archival storage to preserve records in the event of investigations, dispute resolution, forensic review, quality assurance, or external examination. Where deletion is proposed, the requesting team must confirm that no active purpose, regulatory expectation, or legal hold continues to apply to the relevant information set.",
                    "Backups, snapshots, disaster recovery copies, and system logs may continue to contain historical records even after business users no longer actively rely on them. Such repositories remain subject to security controls and are retained according to infrastructure practices designed to support service restoration and evidentiary integrity.",
                ],
            ),
            (
                "3. Governance and Exceptions",
                [
                    "Compliance, Finance, Security, and Legal may issue interpretive guidance for specific workflows where they believe a regulatory requirement should control retention. Business units must preserve supporting justification for any deletion event undertaken in a regulated system or customer-impacting process. Exceptions to this standard require approval from the CISO and the relevant business owner.",
                    "This standard should be read together with the information classification policy, backup policy, incident response procedure, and records management guidance. Teams should avoid creating separate local deletion rules without approval because inconsistent practices can create evidentiary gaps.",
                    "The standard will be reviewed annually or earlier if there is a material regulatory development, product expansion, or audit observation affecting information lifecycle management. Operational teams are expected to comply with the intent of this standard even where a detailed retention schedule for a specific dataset has not yet been finalized by the relevant process owner.",
                ],
            ),
        ],
    )

    ir_sop = build_document(
        "NovaPay Security Incident Response Standard Operating Procedure",
        "Information Security Management System Controlled Document | Version 3.1",
        [
            (
                "1. Objective and Scope",
                [
                    "The purpose of this standard operating procedure is to define how NovaPay detects, escalates, investigates, contains, eradicates, and recovers from information security incidents affecting production systems, corporate endpoints, cloud infrastructure, or third-party service dependencies. The procedure supports the ISO 27001 control environment and aligns internal escalation practices across Security Operations, Engineering, Infrastructure, and Corporate IT.",
                    "Security incidents include malware infection, credential compromise, denial-of-service events, unauthorized administrative access, service outage, suspicious network traffic, data exfiltration indicators, cloud configuration drift, ransomware events, and third-party service disruption with operational impact. Any employee or contractor who suspects a security incident must notify the CISO or the Security Operations mailbox immediately so the response process can begin without delay.",
                    "This procedure is focused on operational security incident handling. External notifications including legal counsel, customer communications, regulator engagement, and media relations are managed under executive authority and handled separately per the Crisis Communications Plan. The CISO is authorized to engage external counsel and determine appropriate notification scope.",
                ],
            ),
            (
                "2. Response Lifecycle",
                [
                    "On receiving an alert, Security Operations classifies the incident by severity, affected systems, and likely business impact. The incident commander opens an incident record, assigns response owners, and determines whether production change freezes, partner notifications, or additional monitoring actions are needed. Initial containment priorities include isolating compromised hosts, revoking credentials, restricting suspicious network paths, and preserving volatile evidence where feasible.",
                    "Engineering and infrastructure teams investigate the root cause, identify the attack path or failure mode, validate the scope of affected systems, and develop containment and eradication plans. Recovery actions may include patch deployment, service restoration, credential resets, infrastructure rebuilds, backup recovery, or partner coordination. Throughout the incident, response teams document timeline events, technical indicators, decisions taken, and remediation steps in the central incident tracker.",
                    "If the event affects customer-facing services, the incident commander may request support from Product, Customer Success, Merchant Operations, and Communications to prepare service updates or respond to inbound queries. The primary objective remains restoration of secure operations, minimization of downtime, and capture of lessons learned for future prevention.",
                ],
            ),
            (
                "3. Escalation, Reporting, and Closure",
                [
                    "All confirmed or suspected incidents must be escalated to the CISO, Security Operations lead, and the relevant engineering owner. High-severity incidents must also be brought to the attention of the Chief Technology Officer and the head of infrastructure. Incident teams should notify the CISO and IT team as soon as practical when a material event is identified, and the CISO may convene an executive review call if sustained customer impact, media attention, or broad platform risk is anticipated.",
                    "Closure requires confirmation that the threat has been contained, affected systems have been restored, remediation tasks have been logged, and evidence has been retained for future forensic or audit review. The incident commander is responsible for ensuring that the final incident report includes a timeline, root cause summary, affected services, corrective actions, and identified preventive improvements.",
                    "This document is reviewed annually under the information security management system. Questions regarding application of the SOP should be directed to the CISO office. Exceptions to response sequencing may be approved by the incident commander where necessary to protect platform availability, preserve forensic evidence, or manage an urgent operational threat that requires prompt escalation outside normal channels.",
                ],
            ),
        ],
    )

    return [
        SeedDocument("privacy", "Privacy-Policy-NovaPay-2025.pdf", "pdf", "privacy_policy", privacy_policy),
        SeedDocument("terms", "NovaPay-Terms-of-Service-2025.pdf", "pdf", "privacy_policy", terms),
        SeedDocument("retention", "NovaPay-Data-Retention-Standard-v2.docx", "docx", "retention_policy", retention),
        SeedDocument("ir", "NovaPay-Incident-Response-SOP-v3.docx", "docx", "breach_response_plan", ir_sop),
    ]


def build_healthbridge_documents() -> list[SeedDocument]:
    privacy_policy = build_document(
        "HealthBridge Analytics — Privacy Policy",
        "Website Policy | Version 1.0 | Last Updated: 14 March 2025",
        [
            (
                "1. Introduction and Regulatory Scope",
                [
                    "HealthBridge Analytics Private Limited provides patient engagement analytics, care pathway reporting, billing support workflows, and hospital-facing dashboards for partner healthcare institutions across India. This Privacy Policy is designed to comply with applicable data protection regulations including the General Data Protection Regulation (GDPR) for EU residents, the California Consumer Privacy Act (CCPA) for California residents, and the Digital Personal Data Protection Act (DPDPA) for Indian residents. We are committed to protecting personal information and have adopted measures intended to align with applicable privacy laws.",
                    "We collect information you provide including name, email address, phone number, date of birth, and any health information you choose to share with us. We may also collect device identifiers, browser information, and usage metrics that help us improve our websites and applications. We use this information to provide our services, communicate with users, troubleshoot issues, and manage customer relationships.",
                    "Where our hospital partners use our analytics services, information may be made available through integrated workflows so that authorized users can review reporting dashboards, billing support indicators, operational trends, and performance insights. We process such information on behalf of our partners to support service delivery, platform administration, and product maintenance. We may also use aggregated or de-identified information to analyze platform performance.",
                ],
            ),
            (
                "2. Data Minimization and Retention",
                [
                    "We are committed to data minimization and only collect personal data that is adequate, relevant, and necessary for the purposes described in this policy. We retain information for as long as necessary to provide our services, comply with legal obligations, resolve disputes, and enforce our agreements. Retention periods may vary depending on the nature of the data and the services involved.",
                    "We maintain reasonable administrative, technical, and physical safeguards designed to protect information against unauthorized access, loss, misuse, or alteration. Individuals may contact us at privacy@healthbridge.in to seek access, correction, or deletion of personal data. We will respond as appropriate and in accordance with applicable law.",
                    "This policy may be updated from time to time. When material changes are made, the updated version will be posted on our website. Continued use of our services after the effective date constitutes acknowledgement of the revised policy, to the extent permitted by law.",
                ],
            ),
            (
                "3. Children's Privacy",
                [
                    "We do not knowingly collect personal data from children under the age of 13. If we become aware that we have inadvertently collected personal data from a child under 13, we will take steps to delete such information promptly. Parents or guardians who believe that a child under 13 has provided personal information may contact us at privacy@healthbridge.in.",
                    "Some of our customers provide services to minors through hospitals, clinics, and other healthcare settings. In those cases, the customer or relevant healthcare institution is responsible for determining the legal basis for collection and use of the information and for obtaining any notices or consents required under applicable law. HealthBridge acts in accordance with contractual instructions received from such partner organizations.",
                    "We do not design our public website to target children, and we ask that children under 13 not submit information directly through the website. Questions about children's information may be directed to privacy@healthbridge.in for review by the privacy team.",
                ],
            ),
            (
                "4. Data Sharing and Contact",
                [
                    "We may share information with service providers who help us host infrastructure, deliver communications, maintain databases, process invoices, and support customer relationships. Such providers are expected to use information only for the purposes for which they have been engaged and to maintain appropriate safeguards. We may also disclose information where required by law, regulation, court order, or lawful request of a competent authority.",
                    "If you have questions regarding this Privacy Policy or wish to exercise your data rights, please contact us at privacy@healthbridge.in. Our team will review your request and respond in a reasonable timeframe. Additional identity verification may be required before we can act on certain types of requests under applicable law.",
                    "The contact details for our privacy function are privacy@healthbridge.in. Our registered office is in Bengaluru, Karnataka. We do not currently have a dedicated Data Protection Officer separate from executive management, and all data protection escalations are handled through the CEO's office as documented in our board governance records.",
                ],
            ),
        ],
    )

    board_resolution = build_document(
        "HealthBridge Analytics — Board Resolution on Data Protection Governance",
        "Extract from Board Meeting Minutes | Date: 22 January 2025",
        [
            (
                "Resolution Background",
                [
                    "The Board of Directors reviewed investor diligence requests concerning privacy governance, cybersecurity maturity, and readiness for the Digital Personal Data Protection Act. The management team noted that the company remains in an early stage of operational maturity and should adopt pragmatic oversight arrangements that leverage existing leadership roles while minimizing administrative overhead for the business.",
                    "After discussion, the Board determined that privacy oversight should remain centrally coordinated by executive leadership so that operational decisions, commercial priorities, and compliance activities can be aligned. The Board expressed the view that a separate privacy office is not currently required given the size of the company and the fact that patient data is generally made available through hospital partners rather than collected directly from individuals through a broad consumer-facing channel.",
                    "Directors noted that the company already maintains a secure engineering process, uses reputable cloud vendors, and is preparing standard documentation to support enterprise sales conversations. The Board emphasized that management should continue developing privacy documentation proportionate to the company's current stage of growth.",
                ],
            ),
            (
                "Resolved Matters",
                [
                    "RESOLVED THAT pursuant to the requirements of applicable data protection legislation, Mr. Arjun Mehta, Chief Executive Officer of the Company, be and is hereby appointed to discharge the functions of Data Protection Officer. The CEO shall ensure that the Company's data processing practices are lawful, and shall coordinate with relevant regulatory authorities as required. This appointment is effective immediately and shall remain in force until further resolution of the Board.",
                    "RESOLVED FURTHER that management is authorized to continue refining privacy policies, vendor documentation, and customer-facing notices in consultation with external counsel as needed, provided that no dedicated data protection headcount is added without prior budget approval from the Board.",
                    "RESOLVED FURTHER that investor updates concerning privacy and security readiness may be coordinated through the Chief Executive Officer together with the Chief Technology Officer and the Head of Customer Success, as appropriate for the subject matter under review. No further standing committee or reporting cadence is established by this resolution at this time.",
                ],
            ),
            (
                "Administrative Note",
                [
                    "The Company Secretary shall maintain this resolution with the corporate records and circulate relevant extracts to management teams upon request. Questions regarding implementation should be directed to the office of the Chief Executive Officer. No formal board reporting schedule for data protection matters is established by this resolution.",
                    "This extract is intended to capture the operative board decision and does not constitute a separate policy manual or role charter. Any future expansion of governance processes may be documented in follow-on board materials, investor reports, or management operating procedures as the company scales.",
                ],
            ),
        ],
    )

    partner_agreement = build_document(
        "HealthBridge Hospital Partner Agreement Template",
        "Standard Form used with hospital and clinic integration partners",
        [
            (
                "1. Scope of Integration Services",
                [
                    "This agreement governs the provision of analytics and workflow services by HealthBridge Analytics Private Limited to hospital, clinic, and healthcare network partners. The partner institution remains responsible for primary collection of patient information and for configuring the upstream systems from which records are shared for analytics and workflow support. HealthBridge may receive patient registration information, visit metadata, doctor identifiers, billing indicators, utilization events, and other operational information needed to provide dashboards, alerts, and reports.",
                    "Data Controller acknowledges and agrees that it is solely responsible for obtaining all necessary consents, authorizations, and approvals from patients, their legal representatives, and applicable institutions as required under applicable law prior to sharing any patient data with HealthBridge Analytics. The partner institution represents that it has a lawful basis to share such information with HealthBridge and that its privacy notices and patient-facing materials are sufficient for the services selected.",
                    "HealthBridge will process information in accordance with the instructions of the partner institution as reflected in the agreement and implementation documents. HealthBridge may use subcontractors or infrastructure providers to host and support the platform, provided that such arrangements are consistent with internal security practices and standard vendor management procedures.",
                ],
            ),
            (
                "2. Security and Confidentiality",
                [
                    "Both parties will maintain commercially reasonable safeguards appropriate to the nature of the services. HealthBridge maintains application logging, access controls, encryption for supported environments, and support workflows intended to preserve service continuity. Each party will notify the other of material incidents affecting the services in accordance with the main agreement.",
                    "Each party shall protect the confidential information of the other using at least the same degree of care it uses to protect its own confidential information of a similar nature, and in no event less than reasonable care. Confidential information may be used solely for the performance of this agreement and may be disclosed only to personnel who have a need to know and are bound by confidentiality obligations.",
                    "Questions regarding source data quality, notice language, and patient communication workflows should be raised by the partner institution with its internal legal and compliance teams before the production launch date. Where a patient, guardian, or third party raises a question regarding consents or notice, the partner institution will remain the primary point of contact unless otherwise agreed in writing.",
                ],
            ),
            (
                "3. Commercial and General Terms",
                [
                    "This agreement may be terminated for material breach not cured within thirty days after written notice. On termination, each party will return or destroy the other party's confidential information upon request, subject to legal retention requirements and routine backup processes. Sections that by their nature should survive termination will remain in effect after termination.",
                    "This agreement is governed by the laws of Karnataka and the courts of Bengaluru shall have exclusive jurisdiction. The template may be updated by HealthBridge from time to time to reflect commercial needs, operational experience, or legal advice. Neither party will make public statements about the other without prior written consent except as required by law.",
                    "Each party's aggregate liability under this agreement will not exceed the fees paid or payable under the relevant statement of work during the twelve months preceding the event giving rise to the claim. Neither party shall be liable for indirect, incidental, special, punitive, or consequential damages including loss of profits, revenue, or anticipated savings arising from any claim under this agreement.",
                ],
            ),
        ],
    )

    security_policy = build_document(
        "HealthBridge Analytics — Data Security Policy",
        "Internal Policy | Version 1.0 | Approved by CEO",
        [
            (
                "1. Security Commitment",
                [
                    "HealthBridge Analytics is committed to protecting the security and integrity of personal and health data. Access to systems is restricted to authorized personnel. Regular security reviews are conducted to identify and remediate vulnerabilities. Employees receive security awareness training. Data in transit is protected using TLS encryption.",
                    "The company uses reputable cloud infrastructure providers who maintain their own security certifications and controls. We rely on these managed service providers for the majority of our infrastructure security posture including network controls, physical security, and platform hardening. Our internal security practices complement the controls provided by our cloud vendors.",
                    "Security incidents and suspected unauthorized access must be reported to the technical lead immediately. The company will investigate reported incidents and take appropriate remediation action. Customers and partners will be notified of material security incidents affecting their data in accordance with contractual and legal obligations.",
                ],
            ),
            (
                "2. Data Handling and Access",
                [
                    "All employees and contractors are expected to handle personal and health data responsibly, to use such data only for authorized business purposes, and to protect it from unauthorized disclosure. Data should not be copied to personal devices, external drives, or personal cloud accounts without explicit approval from the technical lead.",
                    "The company uses TLS for data in transit across all public-facing interfaces. Data at rest encryption is provided by the cloud infrastructure provider for primary database storage. Backup media and archived exports may have varying encryption coverage depending on the storage service used.",
                    "Questions about this policy should be directed to the Chief Technology Officer. The policy will be reviewed periodically to reflect changes in the company's technology environment, regulatory requirements, and operational practices. Employees who become aware of potential security vulnerabilities or incidents should escalate promptly through internal channels.",
                ],
            ),
            (
                "3. Vendor and Third-Party Security",
                [
                    "The company engages a number of software-as-a-service vendors, infrastructure providers, and technical subcontractors who may have access to systems that process patient-linked data. Vendors are selected partly on the basis of their security reputation and the availability of standard security terms in their service agreements. We rely on standard platform terms for most vendors.",
                    "New vendor onboarding should be reviewed by the technical lead before granting access to production systems or patient-linked data environments. Vendor access should be limited to the minimum necessary for the services being performed. Access credentials and permissions should be reviewed periodically as part of routine operational security hygiene.",
                    "This policy should be read together with the company's privacy policy, partner agreement template, and any applicable employment confidentiality obligations. The company acknowledges that its security program is at an early stage and will be strengthened over time as the organization scales, adds engineering headcount, and receives guidance from its investors and external advisers on security maturity requirements.",
                ],
            ),
        ],
    )

    return [
        SeedDocument("privacy", "HealthBridge-Privacy-Policy-v1.pdf", "pdf", "privacy_policy", privacy_policy),
        SeedDocument("board", "HealthBridge-Board-Resolution-DPO.docx", "docx", "other", board_resolution),
        SeedDocument("partner", "HealthBridge-Hospital-Partner-Agreement-Template.docx", "docx", "data_processing_agreement", partner_agreement),
        SeedDocument("security", "HealthBridge-Data-Security-Policy-v1.pdf", "pdf", "security_policy", security_policy),
    ]


def build_dakshin_documents() -> list[SeedDocument]:
    privacy_policy = build_document(
        "Dakshin Logistics Group — Privacy Policy India",
        "Corporate Policy | Version 3.2 | Revised November 2023",
        [
            (
                "1. About This Policy",
                [
                    "Dakshin Logistics Group operates freight, warehousing, route management, fulfillment, fleet coordination, and supply chain support services across India and selected overseas markets. This Privacy Policy was updated in November 2023 to reflect the requirements of the Digital Personal Data Protection Act, 2023. We have reviewed and updated our data processing practices to align with the new framework.",
                    "The policy applies to data collected through customer contracts, warehouse operations, fleet platforms, vendor onboarding, service portals, support channels, and our corporate website. Depending on the business relationship involved, specific operational teams may collect identity, contact, payment, route, location, service performance, and compliance-related information required to provide transport and logistics services or to administer employment and contractor relationships.",
                    "We review this policy periodically to reflect changes in law, business operations, partner arrangements, and technology. Updates are posted on our website and become effective from the date listed above. Individuals are encouraged to review the policy from time to time to understand how Dakshin Logistics Group handles personal data.",
                ],
            ),
            (
                "2. Data Processing and Workforce Data",
                [
                    "We use personal data to deliver logistics services, coordinate pickups and deliveries, manage warehouse operations, verify identity, administer contracts, process payments, maintain safety and compliance controls, investigate incidents, optimize routes, respond to grievances, and monitor service-level commitments. Data may also be used for analytics, training, fraud prevention, audit support, legal compliance, and internal management reporting.",
                    "We may collect and process information about individual delivery and warehouse personnel as required for our operations, including route and location data for operational management and delivery verification purposes. Our driver operations involve the use of a mobile application that supports real-time route visibility and proof-of-delivery workflows. Location information collected through this application is used to coordinate dispatching and to support operational performance management.",
                    "Personal data may be shared with customers, transport partners, warehouse operators, payment providers, technology vendors, insurers, regulators, auditors, and affiliated entities where necessary for legitimate business operations and lawful compliance purposes. Access to personal data is governed by role-based controls and internal confidentiality requirements.",
                ],
            ),
            (
                "3. Rights and Contact",
                [
                    "Individuals may contact Dakshin Logistics Group to seek access to personal data summaries, request correction of inaccuracies, ask for erasure where applicable, or raise grievances about how information has been handled. Requests may be reviewed for identity verification, applicable exemptions, and operational feasibility before a response is provided.",
                    "Questions relating to this policy may be sent to dpo@dakshinlogistics.com. Additional guidance is available through the privacy portal referenced in our grievance procedure at privacy.dakshinlogistics.com. Where a request remains unresolved, the individual may be informed of available escalation channels in accordance with applicable law.",
                    "This policy is informational and should be read together with role-specific notices, employee communications, contractual terms, and operational procedures that apply in a particular context. Those documents may provide more specific information for the relevant business relationship or service activity.",
                ],
            ),
        ],
    )

    employee_notice = build_document(
        "Dakshin Logistics Group — Employee Data Processing Notice",
        "Version 2.0 | Applies to employees, drivers, and warehouse associates",
        [
            (
                "1. Purpose and Consent",
                [
                    "This notice explains how Dakshin Logistics Group collects and processes personal data relating to employees, contract drivers, and warehouse workers during recruitment, onboarding, employment administration, route management, safety monitoring, payroll, disciplinary processes, and performance management.",
                    "As a condition of your employment with Dakshin Logistics Group, you acknowledge and consent to the collection, processing, storage, and use of your personal data as described in this Employee Data Processing Notice. This includes your identity information, employment records, performance data, disciplinary records, and location data collected through the Driver App for operational, safety, and compliance purposes. By accepting employment, you confirm your understanding of and consent to these processing activities.",
                    "The operational needs of the business require integrated use of workforce identity information, compliance records, attendance details, route execution data, proof-of-delivery data, safety events, and related operational metrics. These processes are integral to your role and to the services Dakshin provides to its customers. By signing the onboarding documents and continuing in employment, personnel confirm that they understand the categories of information processed and the organizational purposes described.",
                ],
            ),
            (
                "2. Performance Evaluation and Location Data",
                [
                    "The company may collect identification details, contact information, government identifiers, banking information, device identifiers, route assignments, attendance records, telematics, real-time location data, incident reports, training records, customer feedback, and supervisor evaluations. We use this information to assign work, administer compensation, manage statutory obligations, maintain vehicle and route safety, respond to customer escalations, investigate incidents, and assess performance against service expectations.",
                    "Performance data collected includes delivery completion rates, route adherence metrics, customer satisfaction scores, and safety compliance records. This information is used to evaluate driver performance, determine incentive eligibility, and inform personnel decisions. Workforce performance evaluation may consider route adherence, delivery timing, proof-of-delivery quality, incident frequency, fuel usage, and related service metrics.",
                    "Location and telematics information may be reviewed by dispatch managers, fleet managers, security personnel, compliance teams, and supervisors responsible for safety and route optimization. The company may use aggregated analytics to improve route planning and resource allocation across the network. Operational records may be retained for periods necessary to support legal compliance, customer requirements, audit readiness, safety investigations, and management reporting.",
                ],
            ),
            (
                "3. Questions and Support",
                [
                    "Questions regarding this notice may be directed to Human Resources or to the Data Protection Officer through the corporate channels published on the company intranet and external website. Employees are expected to comply with related policies, mobile device requirements, and route management procedures issued by the company from time to time.",
                    "This notice does not alter the contractual nature of the employment relationship where applicable, nor does it limit the company's ability to process information necessary to administer employment, comply with law, or protect the safety and integrity of logistics operations. The company may update this notice periodically to reflect operational or legal developments and will communicate material updates through appropriate internal channels.",
                ],
            ),
        ],
    )

    transfer_framework = build_document(
        "Dakshin Logistics Group — Cross-Border Data Transfer Framework",
        "Group Legal and Compliance | Version 1.3",
        [
            (
                "1. Framework Purpose and Scope",
                [
                    "This Data Transfer Framework governs the transfer of personal data between Dakshin Logistics Group entities and to third-party processors outside the European Economic Area and India. Transfers to Dakshin Middle East FZE (UAE) are governed by Standard Contractual Clauses as approved by the European Commission pursuant to Regulation (EU) 2016/679 (GDPR). Transfers are subject to the protections afforded by the UK-EU adequacy bridge and the adequacy decisions of the European Commission.",
                    "The framework applies to inter-company transfers of customer contact data, shipment records, driver identifiers, route performance metrics, incident summaries, compliance documentation, and related operational data used in the management of cross-border services and regional support functions. The specific data elements transferred may vary depending on business need and the systems integrated between the entities.",
                    "This framework was developed in consultation with European legal counsel to support Dakshin's EU-facing logistics operations. It is intended to reflect an intra-group transfer mechanism broadly aligned with GDPR requirements. Questions about the application of this framework should be directed to the Group Legal team or the Data Protection Officer.",
                ],
            ),
            (
                "2. Safeguards and Restrictions",
                [
                    "Receiving entities shall implement appropriate technical and organizational measures to protect transferred data, including access management, network security, endpoint protection, and incident reporting processes proportionate to the nature of the systems used. Data shall be processed only for operational, customer service, compliance, audit, and internal management purposes authorized under this framework and related corporate instructions.",
                    "The receiving entity may permit access to transferred data by personnel, contractors, and service providers who have a legitimate business need and who are bound by confidentiality obligations. The parties shall cooperate on audit requests, incident investigation, and customer escalations where transferred data is relevant to the issue under review.",
                    "Where new systems or processing activities materially affect the nature of the transfer, the relevant business owners will discuss whether the framework should be updated. This framework may be supplemented by technical annexes, security schedules, or data mapping records maintained by the relevant teams.",
                ],
            ),
            (
                "3. General Terms",
                [
                    "This framework remains effective until terminated by either entity on ninety days' written notice, provided that any transferred data may continue to be retained as required for legal, contractual, or operational reasons. The framework is intended to complement broader corporate governance policies and is not a substitute for local business procedures addressing day-to-day operational handling of data.",
                    "Questions concerning this framework should be directed to the Group Legal team or the Data Protection Officer. The parties may rely on affiliated technology environments and shared enterprise systems to implement the transfers contemplated by this framework. Annual review is expected to assess whether the framework remains fit for purpose in light of any regulatory developments.",
                    "This framework covers transfers to entities and technology vendors for which a documented transfer basis has been established. The Group Legal team is responsible for maintaining an up-to-date inventory of active transfer relationships and ensuring that appropriate documentation exists for each transfer destination covered by this instrument.",
                ],
            ),
        ],
    )

    gps_policy = build_document(
        "Dakshin Logistics Group — GPS Location Data Policy",
        "Fleet Operations | Version 3.0 | Approved by DPO",
        [
            (
                "1. Purpose and Collection",
                [
                    "Dakshin Logistics Group deploys mobile and vehicle-based GPS capability to support route management, shipment visibility, driver safety, theft prevention, customer service, proof-of-service verification, and compliance with service-level commitments. This policy establishes a standardized approach for collecting location data from drivers and fleet assets so that dispatch teams and operations leaders can coordinate real-time logistics execution at scale.",
                    "Location data is collected from drivers using the Dakshin Driver App to support route optimization, delivery confirmation, driver safety monitoring, and compliance with customer service-level agreements. Data is collected continuously during active duty hours. Location records are retained for a period of 36 months for operational and legal dispute resolution purposes.",
                    "The GPS environment integrates with route planning tools, dispatch consoles, incident workflows, and customer escalation channels. Authorized operations personnel may view live location feeds, route deviations, dwell times, and event history in order to coordinate work and resolve delivery issues efficiently.",
                ],
            ),
            (
                "2. Retention and Access",
                [
                    "Location data is retained for 36 months to support post-incident review, customer dispute handling, insurance matters, service verification, and quality analysis. Dispatch supervisors, regional fleet managers, security teams, selected customer service managers, and authorized technology personnel may access location data where necessary to perform their roles. Access is governed through system permissions and internal management approvals.",
                    "Reports generated from the GPS platform may be shared with customers, insurers, internal audit, and senior management where relevant to service performance or incident review. Operational teams are expected to use location information responsibly and only for authorized business purposes.",
                    "Questions about system settings, device functionality, and regional implementation should be raised with the fleet technology team or the regional operations head. Any exceptions to the standard tracking configuration require approval from central fleet operations and documentation in the relevant change management record.",
                ],
            ),
            (
                "3. Governance and Review",
                [
                    "Fleet operations, the Data Protection Officer, Information Security, and Human Resources may review this policy periodically to ensure that it remains aligned with the needs of the business and with evolving customer, legal, and safety expectations. Additional guidance may be issued through training notes, control room instructions, or platform release documentation.",
                    "This policy should be read together with the employment data processing notice, mobile device policy, disciplinary standards, and route compliance guidance. Nothing in this policy limits Dakshin's ability to take immediate action where tracking data indicates a safety concern, operational failure, suspected misconduct, or customer-impacting service issue that requires prompt escalation.",
                    "The policy is subject to annual review by the fleet technology lead in consultation with the Data Protection Officer and Group Legal. Any material change to the GPS configuration, retention period, or access model must be reflected in an updated version of this policy before the change is implemented in production fleet systems.",
                ],
            ),
        ],
    )

    grievance_procedure = build_document(
        "Dakshin Logistics Group — Data Grievance Procedure",
        "Enterprise Privacy Procedure | Version 1.0 | Approved by General Counsel",
        [
            (
                "1. Filing a Grievance",
                [
                    "Dakshin Logistics Group provides a process for data principals to raise concerns regarding access, correction, erasure, misuse of personal data, notice concerns, or other privacy-related matters. Data principals may submit grievances or exercise their rights under the DPDPA by: (1) Submitting a request through the Data Protection Portal at privacy.dakshinlogistics.com (login required); (2) Emailing the DPO at dpo@dakshinlogistics.com; (3) Writing to the Data Protection Officer, Dakshin Logistics Group, Mumbai.",
                    "Submitted grievances should include the name of the requester, contact details, relationship to Dakshin, a description of the issue, and any supporting information necessary for the company to review the matter. The privacy team may request additional details or proof of identity before taking action. Requests received through other business channels may be redirected to the DPO portal so that they can be tracked centrally.",
                    "The procedure applies to customers, vendor contacts, website users, and other individuals whose personal data is processed by Dakshin. Business teams receiving a privacy-related complaint should direct the individual to the published privacy channels and avoid making commitments on outcome or timing before the privacy team has reviewed the matter.",
                ],
            ),
            (
                "2. Review and Response",
                [
                    "The privacy team logs each grievance, verifies the request, coordinates with relevant business owners, and prepares a response in line with internal service targets. Where additional technical investigation is required, the privacy team may seek support from Information Security, Technology, Human Resources, or Operations. Responses are typically provided through the portal workflow or by email to the address from which the grievance was received.",
                    "If a grievance cannot be resolved immediately, the privacy team may issue an interim acknowledgment while additional information is gathered. Complex matters involving multiple systems, legal claims, or third-party dependencies may require extended review. The privacy team will maintain records of submitted grievances and the actions taken to address them within the central portal environment.",
                    "Individuals who remain dissatisfied after receiving a final response may be informed of external escalation channels in accordance with applicable law. Questions regarding this procedure should be directed to the Data Protection Officer. The DPO reports through the Group Legal function and coordinates with the General Counsel on matters with legal, regulatory, or commercial implications.",
                ],
            ),
            (
                "3. Procedure Maintenance",
                [
                    "This procedure is owned by the Data Protection Officer and reviewed annually in consultation with Legal, Human Resources, Customer Service, and Technology. Updates may be issued to reflect changes in law, portal functionality, or business operations. The current version is made available through the corporate website and relevant governance repositories.",
                    "This procedure should be read together with the public privacy notice, employment data notice, records retention standard, and other internal guidance that governs the handling of personal data across the enterprise. Teams with questions about the interpretation of this procedure should consult the Data Protection Officer or Group Legal.",
                ],
            ),
        ],
    )

    return [
        SeedDocument("privacy", "Dakshin-Privacy-Policy-India-2025.pdf", "pdf", "privacy_policy", privacy_policy),
        SeedDocument("employment", "Dakshin-Employee-Data-Processing-Notice-v2.docx", "docx", "consent_form", employee_notice),
        SeedDocument("transfer", "Dakshin-Cross-Border-Data-Transfer-Framework.docx", "docx", "data_processing_agreement", transfer_framework),
        SeedDocument("gps", "Dakshin-GPS-Location-Data-Policy-v3.pdf", "pdf", "security_policy", gps_policy),
        SeedDocument("grievance", "Dakshin-Data-Grievance-Procedure-v1.docx", "docx", "internal_sop", grievance_procedure),
    ]


def default_response(answer: str, note: str, evidence_reference: str | None, *, confidence: str = "moderate",
                     na_reason: str | None = None) -> dict:
    return {
        "answer": answer,
        "notes": note,
        "evidence_reference": evidence_reference,
        "confidence": confidence,
        "na_reason": na_reason,
    }


def build_response_map(
    *,
    default_answer: str,
    default_note: str,
    doc_lookup: dict[str, str],
    overrides: dict[str, dict],
) -> dict[str, dict]:
    prefix_sources = {
        "CH2.CONSENT": doc_lookup.get("privacy"),
        "CH2.NOTICE": doc_lookup.get("privacy"),
        "CH2.PURPOSE": doc_lookup.get("privacy"),
        "CH2.MINIMIZE": doc_lookup.get("retention") or doc_lookup.get("gps") or doc_lookup.get("privacy"),
        "CH2.ACCURACY": doc_lookup.get("privacy"),
        "CH2.SECURITY": doc_lookup.get("ir") or doc_lookup.get("security") or doc_lookup.get("partner") or doc_lookup.get("transfer"),
        "CH3.ACCESS": doc_lookup.get("privacy"),
        "CH3.CORRECT": doc_lookup.get("privacy"),
        "CH3.GRIEVANCE": doc_lookup.get("grievance") or doc_lookup.get("privacy"),
        "CH3.NOMINATE": doc_lookup.get("privacy"),
        "CH4.CHILD": doc_lookup.get("privacy") or doc_lookup.get("partner"),
        "CH4.SDF": doc_lookup.get("board") or doc_lookup.get("grievance") or doc_lookup.get("employment"),
        "CM.RECORDS": doc_lookup.get("privacy") or doc_lookup.get("employment"),
        "CM.GRANULAR": doc_lookup.get("terms") or doc_lookup.get("employment") or doc_lookup.get("privacy"),
        "CB.TRANSFER": doc_lookup.get("transfer") or doc_lookup.get("privacy"),
        "BN.NOTIFY": doc_lookup.get("ir") or doc_lookup.get("security"),
    }

    response_map: dict[str, dict] = {}
    for req_id in ALL_REQUIREMENT_IDS:
        evidence_reference = None
        for prefix, filename in prefix_sources.items():
            if req_id.startswith(prefix):
                evidence_reference = filename
                break
        response_map[req_id] = default_response(
            default_answer,
            default_note,
            evidence_reference,
            confidence="moderate" if default_answer != "fully_implemented" else "strong",
        )
    response_map.update(overrides)
    return response_map


def absence(requirement_id: str, content: str, severity: str = "medium") -> dict:
    return {
        "finding_type": "absence",
        "requirement_id": requirement_id,
        "document_key": None,
        "content": content,
        "severity": severity,
        "source_quote": None,
        "source_location": None,
    }


def evidence(requirement_id: str, document_key: str, content: str, quote: str, location: str, severity: str = "info") -> dict:
    return {
        "finding_type": "evidence",
        "requirement_id": requirement_id,
        "document_key": document_key,
        "content": content,
        "severity": severity,
        "source_quote": quote,
        "source_location": location,
    }


def signal(requirement_id: str | None, document_key: str | None, content: str, quote: str | None, location: str | None,
           severity: str = "medium") -> dict:
    return {
        "finding_type": "signal",
        "requirement_id": requirement_id,
        "document_key": document_key,
        "content": content,
        "severity": severity,
        "source_quote": quote,
        "source_location": location,
    }


def novapay_fixture() -> dict:
    docs = build_novapay_documents()
    doc_lookup = {doc.key: doc.filename for doc in docs}
    overrides = {
        # Gap requirements — surface answers
        "CH2.CONSENT.1": default_response("fully_implemented", "Single onboarding flow with clear acceptance of Privacy Policy and Terms.", doc_lookup["privacy"], confidence="strong"),
        "CH2.CONSENT.2": default_response("fully_implemented", "Product consent is captured through a unified onboarding flow that covers all platform purposes.", doc_lookup["privacy"], confidence="strong"),
        "CH2.CONSENT.3": default_response("fully_implemented", "Users can unsubscribe from marketing emails via app settings.", doc_lookup["terms"], confidence="strong"),
        "CH2.CONSENT.4": default_response("not_applicable", "We do not currently use a separate consent manager platform.", None, confidence="strong", na_reason="no_consent_manager"),
        "CH2.CONSENT.5": default_response("not_applicable", "NovaPay services are intended for adults and do not target children.", None, confidence="strong", na_reason="does_not_process_childrens_data"),
        "CH2.NOTICE.1": default_response("fully_implemented", "We maintain a comprehensive privacy policy updated quarterly.", doc_lookup["privacy"], confidence="strong"),
        "CH2.MINIMIZE.2": default_response("partially_implemented", "Retention policy documents our approach. RBI regulations require long-term storage.", doc_lookup["retention"]),
        "CH2.MINIMIZE.3": default_response("partially_implemented", "A retention standard exists and detailed schedules are being matured by system owners.", doc_lookup["retention"]),
        "CH2.SECURITY.1": default_response("fully_implemented", "ISO 27001 certified with SOC 2 Type II. Comprehensive security controls in place.", doc_lookup["ir"], confidence="strong"),
        "CH2.SECURITY.2": default_response("fully_implemented", "Encryption at rest and in transit. Least-privilege access controls enforced.", doc_lookup["ir"], confidence="strong"),
        "CH2.SECURITY.3": default_response("fully_implemented", "All vendors sign our standard MSA. AWS and Stripe have their own certified programs.", doc_lookup["privacy"], confidence="strong"),
        "CH3.GRIEVANCE.1": default_response("partially_implemented", "Customers can email privacy@novapay.in or use the in-app contact form.", doc_lookup["privacy"]),
        "CH3.GRIEVANCE.2": default_response("partially_implemented", "Privacy inquiries are handled through the shared customer support inbox.", doc_lookup["privacy"]),
        "CH3.NOMINATE.1": default_response("planned", "Nomination workflow is on the product roadmap for the next policy refresh cycle.", doc_lookup["privacy"]),
        "CH4.CHILD.1": default_response("not_applicable", "NovaPay does not offer services designed for children.", None, confidence="strong", na_reason="does_not_process_childrens_data"),
        "CH4.CHILD.2": default_response("not_applicable", "NovaPay does not intentionally process children's personal data.", None, confidence="strong", na_reason="does_not_process_childrens_data"),
        "CH4.CHILD.3": default_response("not_applicable", "Age verification controls are not used because the product is adult-oriented.", None, confidence="strong", na_reason="does_not_process_childrens_data"),
        "CH4.SDF.1": default_response("partially_implemented", "The CISO currently covers DPO responsibilities while we monitor future SDF designation.", doc_lookup["ir"]),
        "CH4.SDF.2": default_response("planned", "Independent auditor appointment will be considered if formal SDF designation occurs.", None),
        "CH4.SDF.3": default_response("planned", "Privacy impact assessments are scoped for high-risk change programs.", None),
        "CH4.SDF.4": default_response("partially_implemented", "External assurance already conducted through ISO and SOC 2 programs.", doc_lookup["ir"]),
        "CM.GRANULAR.1": default_response("fully_implemented", "Customers are informed about the purposes for which data is used during onboarding.", doc_lookup["privacy"], confidence="strong"),
        "CM.GRANULAR.2": default_response("fully_implemented", "Users can opt out of promotional communications without closing their account.", doc_lookup["terms"], confidence="strong"),
        "CB.TRANSFER.1": default_response("fully_implemented", "We use AWS Singapore with their Data Processing Addendum. Stripe has standard terms.", doc_lookup["privacy"], confidence="strong"),
        "CB.TRANSFER.2": default_response("fully_implemented", "Vendor terms and security reviews govern our international processing arrangements.", doc_lookup["privacy"], confidence="strong"),
        "CB.TRANSFER.3": default_response("partially_implemented", "We monitor localisation requirements and rely on India-based primary systems where feasible.", doc_lookup["privacy"]),
        "BN.NOTIFY.1": default_response("fully_implemented", "We have a mature ISO 27001-certified IR plan with 24/7 on-call rotation.", doc_lookup["ir"], confidence="strong"),
        "BN.NOTIFY.2": default_response("fully_implemented", "Incident response plan covers all stakeholder notifications under CISO direction.", doc_lookup["ir"], confidence="strong"),
        "BN.NOTIFY.3": default_response("fully_implemented", "NIST-framework IR plan covers full lifecycle from detection through remediation.", doc_lookup["ir"], confidence="strong"),
        "BN.NOTIFY.4": default_response("partially_implemented", "High-severity incidents are centrally logged and tracked in security tooling.", doc_lookup["ir"]),
    }
    responses = build_response_map(
        default_answer="fully_implemented",
        default_note="Control is documented and embedded in our standard operating model.",
        doc_lookup=doc_lookup,
        overrides=overrides,
    )
    coverage = {req_id: "adequate" for req_id in ALL_REQUIREMENT_IDS}
    for req_id in [
        "CH2.CONSENT.1", "CH2.CONSENT.2", "CH2.CONSENT.3",
        "CH2.MINIMIZE.2", "CH2.MINIMIZE.3",
        "CH2.NOTICE.1",
        "CH3.GRIEVANCE.1", "CH3.GRIEVANCE.2",
        "CH3.NOMINATE.1",
        "CH4.SDF.1", "CH4.SDF.2", "CH4.SDF.3", "CH4.SDF.4",
        "CM.GRANULAR.1", "CM.GRANULAR.2",
        "CB.TRANSFER.1", "CB.TRANSFER.2", "CB.TRANSFER.3",
        "BN.NOTIFY.1", "BN.NOTIFY.2", "BN.NOTIFY.3", "BN.NOTIFY.4",
    ]:
        coverage[req_id] = "partial"
    for req_id in ["CH2.CONSENT.5", "CH2.CONSENT.4", "CH4.CHILD.1", "CH4.CHILD.2", "CH4.CHILD.3"]:
        coverage[req_id] = "absent"
    findings = [
        # Evidence — surface compliance signals
        evidence("CH2.CONSENT.1", "privacy", "Privacy policy states that use of services constitutes acceptance of all processing.", "By using our services, you consent to the collection and processing of your data as described in this policy. This includes identity verification, fraud prevention, transaction analysis, merchant reporting, product personalization, promotional communications, and platform improvement activities.", "Section 1, Paragraph 2", severity="info"),
        evidence("CH2.SECURITY.1", "ir", "ISO 27001 IR procedure covers full detection-to-closure lifecycle.", "Security incidents include malware infection, credential compromise, denial-of-service events, unauthorized administrative access, service outage, suspicious network traffic, data exfiltration indicators.", "Section 1, Paragraph 1", severity="info"),
        evidence("CH2.SECURITY.2", "ir", "IR SOP references encryption and access controls as part of ISMS.", "The procedure supports the ISO 27001 control environment and aligns internal escalation practices across Security Operations, Engineering, Infrastructure, and Corporate IT.", "Section 1, Paragraph 1", severity="info"),
        evidence("BN.NOTIFY.3", "ir", "IR plan describes response lifecycle phases: containment, eradication, recovery.", "Engineering and infrastructure teams investigate the root cause, identify the attack path or failure mode, validate the scope of affected systems, and develop containment and eradication plans.", "Section 2, Paragraph 2", severity="info"),
        evidence("CB.TRANSFER.1", "privacy", "Privacy policy acknowledges data transfers to service providers in Singapore and the United States.", "Your data may be transferred to and processed in countries other than India where our service providers operate. We use service providers based in Singapore, the United States, and other jurisdictions to host infrastructure, process payments, support customer communications, and perform analytics.", "Section 4, Paragraph 2", severity="info"),
        evidence("CH2.NOTICE.1", "privacy", "Privacy policy describes analytics processing in vague terms without naming behavioral analytics or credit scoring.", "We may analyze account activity and platform usage to improve our services, detect unusual patterns, and support merchant performance programs.", "Section 2, Paragraph 1", severity="info"),
        evidence("CH2.MINIMIZE.2", "retention", "Retention standard references regulatory requirements but does not specify periods.", "NovaPay retains personal data for as long as necessary to fulfill the purposes described in this policy, including meeting our legal, regulatory, audit, and business obligations.", "Section 1, Paragraph 2", severity="low"),
        # Signal — red flags
        signal("CH2.CONSENT.2", "privacy", "Seven distinct processing purposes are bundled into a single consent statement at account creation; no granular purpose selection is offered.", "By using our services, you consent to the collection and processing of your data as described in this policy. This includes identity verification, fraud prevention, transaction analysis, merchant reporting, product personalization, promotional communications, and platform improvement activities.", "Section 1, Paragraph 2", severity="high"),
        signal("CM.GRANULAR.2", "terms", "Opt-out is limited to promotional communications while analytics, fraud signals, and behavioral data processing remain tied to service use.", "You may opt out of promotional communications at any time by updating your notification settings. Opting out of promotional communications does not affect NovaPay's processing of your transaction data, fraud signals, behavioral patterns, and account activity for service delivery and improvement purposes.", "Section 2, Paragraph 2", severity="high"),
        signal("CM.GRANULAR.2", "terms", "ToS explicitly frames continued service use as acceptance of the full data processing model, removing meaningful withdrawal choice.", "Use of our payment services constitutes acceptance of our data processing practices.", "Section 2, Paragraph 2", severity="critical"),
        signal("CH2.MINIMIZE.3", "retention", "Retention standard expressly states it does not prescribe system-specific schedules, leaving all data retention periods undefined.", "It does not prescribe system-specific retention schedules. Instead, product and functional owners remain responsible for aligning their data sets to the relevant legal and business context.", "Section 1, Paragraph 3", severity="high"),
        signal("CB.TRANSFER.1", "privacy", "Cross-border disclosure names Singapore and the United States generally but does not identify specific processors; Mixpanel, Intercom, Google Analytics, and others are absent.", "We use service providers based in Singapore, the United States, and other jurisdictions to host infrastructure, process payments, support customer communications, and perform analytics.", "Section 4, Paragraph 2", severity="high"),
        signal("BN.NOTIFY.1", "ir", "IR SOP explicitly defers external notifications to executive authority and the Crisis Communications Plan, with no reference to Data Protection Board or 72-hour clock.", "External notifications including legal counsel, customer communications, regulator engagement, and media relations are managed under executive authority and handled separately per the Crisis Communications Plan. The CISO is authorized to engage external counsel and determine appropriate notification scope.", "Section 1, Paragraph 3", severity="critical"),
        signal("CH2.NOTICE.1", "privacy", "Privacy policy never uses the terms behavioral analytics, credit scoring, or transaction profiling despite describing all three activities under vague language.", "We may analyze account activity and platform usage to improve our services, detect unusual patterns, and support merchant performance programs.", "Section 2, Paragraph 1", severity="high"),
        # Absence — required documents or controls not present
        absence("BN.NOTIFY.2", "No document establishes a process or template for notifying affected data principals following a personal data breach. The IR SOP defers all external notifications to executive authority.", severity="high"),
        absence("CH2.SECURITY.3", "No Data Processing Agreement document is present in the assessment. No contractual safeguards specific to DPDPA are in evidence for any processor handling personal data.", severity="high"),
        absence("CH3.GRIEVANCE.1", "No SOP exists for handling data principal grievances. The privacy inbox is a shared customer support address with no data protection training, SLA, or escalation path.", severity="high"),
    ]
    hidden_gaps = [
        {
            "requirement_ids": ["CH2.CONSENT.1", "CH2.CONSENT.2"],
            "surface_answer": "fully_implemented",
            "actual_status": "non_compliant",
            "gap_description": "One checkbox during account creation covers seven distinct purposes: identity verification, fraud prevention, transaction analysis, merchant reporting, product personalization, promotional communications, and platform improvement. No granular purpose selection exists. A user cannot complete a payment transaction while declining behavioral analytics.",
            "evidence_in_document": doc_lookup["privacy"],
            "evidence_quote_hint": "By using our services, you consent to the collection and processing of your data as described in this policy. This includes identity verification, fraud prevention, transaction analysis, merchant reporting, product personalization, promotional communications, and platform improvement activities.",
            "probing_depth": 3,
            "what_followup_should_ask": "Can a user complete a payment transaction while declining behavioral analytics? Show the screen where users select or decline consent for each of the seven processing purposes listed in the privacy policy.",
        },
        {
            "requirement_ids": ["CM.GRANULAR.2", "CH2.CONSENT.3"],
            "surface_answer": "fully_implemented",
            "actual_status": "non_compliant",
            "gap_description": "The only opt-out available is for promotional emails. There is no mechanism to withdraw consent for behavioral analytics, merchant reporting, or transaction pattern scoring while remaining a customer. The ToS states that use of the payment service constitutes acceptance of all data processing practices.",
            "evidence_in_document": doc_lookup["terms"],
            "evidence_quote_hint": "Use of our payment services constitutes acceptance of our data processing practices.",
            "probing_depth": 3,
            "what_followup_should_ask": "Show the screen where a user can withdraw consent for behavioral analytics without closing their account. Which processing activities can a user refuse while still using the payment service?",
        },
        {
            "requirement_ids": ["CH2.MINIMIZE.2", "CH2.MINIMIZE.3"],
            "surface_answer": "partially_implemented",
            "actual_status": "non_compliant",
            "gap_description": "The retention standard is two pages and contains no table of retention periods per data category. It explicitly states it does not prescribe system-specific schedules. In practice nothing is ever deleted because teams retain data for hypothetical future regulatory audits. Marketing analytics and KYC documents share the same undefined retention period.",
            "evidence_in_document": doc_lookup["retention"],
            "evidence_quote_hint": "NovaPay retains personal data for as long as necessary to fulfill the purposes described in this policy, including meeting our legal, regulatory, audit, and business obligations.",
            "probing_depth": 3,
            "what_followup_should_ask": "What is the specific retention period for behavioral analytics data, and what automated process deletes it once that period ends? Provide the per-category retention schedule.",
        },
        {
            "requirement_ids": ["CB.TRANSFER.1", "CB.TRANSFER.2"],
            "surface_answer": "fully_implemented",
            "actual_status": "non_compliant",
            "gap_description": "NovaPay knows about AWS Singapore and Stripe US but is unaware that Mixpanel (US), Intercom (US), Google Analytics (US), Zendesk (US), and Segment (US) also receive personal data. No DPA exists with any of these vendors. AWS and Stripe standard addenda reference GDPR SCCs, not DPDPA. The privacy policy names no specific processors and provides no transfer safeguard documents.",
            "evidence_in_document": doc_lookup["privacy"],
            "evidence_quote_hint": "We use service providers based in Singapore, the United States, and other jurisdictions to host infrastructure, process payments, support customer communications, and perform analytics.",
            "probing_depth": 4,
            "what_followup_should_ask": "Provide the complete inventory of every system that receives personal data outside India, the destination country, the legal basis for each transfer under DPDPA Section 16, and the contractual document governing each transfer.",
        },
        {
            "requirement_ids": ["BN.NOTIFY.1", "BN.NOTIFY.2", "BN.NOTIFY.3"],
            "surface_answer": "fully_implemented",
            "actual_status": "non_compliant",
            "gap_description": "The IR SOP is a strong security incident plan but does not: define what constitutes a personal data breach versus a security incident, include a Data Protection Board notification workflow, include a template for notifying affected data principals, specify the 72-hour notification clock, or name who has authority to decide notification is required. All external notifications are deferred to executive authority under the Crisis Communications Plan.",
            "evidence_in_document": doc_lookup["ir"],
            "evidence_quote_hint": "External notifications including legal counsel, customer communications, regulator engagement, and media relations are managed under executive authority and handled separately per the Crisis Communications Plan.",
            "probing_depth": 3,
            "what_followup_should_ask": "Show the section of your IR plan that covers personal data breach notification to the Data Protection Board and affected data principals, including the 72-hour clock and the notification templates.",
        },
        {
            "requirement_ids": ["CH2.SECURITY.3"],
            "surface_answer": "fully_implemented",
            "actual_status": "non_compliant",
            "gap_description": "NovaPay's standard MSA contains a single security clause: 'industry-standard security measures.' No data processing purpose limitation, no sub-processor notification rights, no audit rights, and no breach notification obligation from processor to NovaPay. AWS and Stripe standard agreements are customer ToS, not DPDPA-negotiated DPAs. No DPA document exists in the assessment.",
            "evidence_in_document": doc_lookup["privacy"],
            "evidence_quote_hint": "We use specialized service providers to host infrastructure, process payments, detect fraud, send customer communications, and support analytics. These providers may process data under contractual arrangements or platform terms.",
            "probing_depth": 2,
            "what_followup_should_ask": "Provide a copy of the Data Processing Agreement with any processor that handles personal data on your behalf, including the security obligations, processing instructions, audit rights, and breach notification clause.",
        },
        {
            "requirement_ids": ["CH3.GRIEVANCE.1"],
            "surface_answer": "partially_implemented",
            "actual_status": "partially_compliant",
            "gap_description": "privacy@novapay.in is a shared customer support inbox. The person reading it has no data protection training. There is no SLA for privacy requests, no tracking of requests received or resolved, and no escalation path to the DPO (CISO). The in-app contact form routes to the same inbox and does not distinguish data protection grievances from payment disputes.",
            "evidence_in_document": doc_lookup["privacy"],
            "evidence_quote_hint": "Questions about this policy may be addressed to privacy@novapay.in.",
            "probing_depth": 2,
            "what_followup_should_ask": "What is the SLA for responding to data principal grievances, who receives them, how are they tracked, and how many have been received and resolved in the past 12 months?",
        },
        {
            "requirement_ids": ["CH2.NOTICE.1"],
            "surface_answer": "fully_implemented",
            "actual_status": "partially_compliant",
            "gap_description": "The privacy policy describes 'payment processing, fraud detection, and service improvement' but never explicitly names behavioral analytics, transaction pattern scoring, or credit risk profiling as processing activities. 2.5M users have no idea their transaction patterns are being analyzed for credit indicators and fed into merchant risk engines. The policy uses language such as 'detect unusual patterns' and 'support merchant performance programs' without disclosure of the underlying profiling activities.",
            "evidence_in_document": doc_lookup["privacy"],
            "evidence_quote_hint": "We may analyze account activity and platform usage to improve our services, detect unusual patterns, and support merchant performance programs.",
            "probing_depth": 2,
            "what_followup_should_ask": "What are the specific analytical models applied to user transaction data, and where in the privacy notice are behavioral analytics, credit risk scoring, and transaction profiling explicitly disclosed to data principals?",
        },
    ]
    return {
        "company_name": "NovaPay Solutions Pvt. Ltd.",
        "industry": "fintech",
        "company_size": "sme",
        "description": "Payment platform with strong ISO 27001 security posture and dangerous policy-practice divergence: bundled consent, undefined retention, incomplete cross-border inventory, and an IR plan with no personal data breach workflow.",
        "context_answers": [
            {"question_id": "CTX.DATA.1", "answer": ["identity", "financial", "behavioral"]},
            {"question_id": "CTX.DATA.2", "answer": ["mobile_app", "web_forms", "third_party_apis"]},
            {"question_id": "CTX.DATA.3", "answer": "yes"},
            {"question_id": "CTX.DATA.4", "answer": "yes"},
            {"question_id": "CTX.DATA.4a", "answer": "Singapore and United States"},
            {"question_id": "CTX.POSTURE.1", "answer": "part_time_shared"},
            {"question_id": "CTX.POSTURE.2", "answer": "iso_27001_certified"},
            {"question_id": "CTX.POSTURE.3", "answer": "external_audit"},
            {"question_id": "CTX.POSTURE.4", "answer": "yes_recently_updated"},
            {"question_id": "CTX.RISK.1", "answer": ["healthcare_finance_critical_infra", "handles_sensitive_personal_data", "designated_or_likely_sdf"]},
            {"question_id": "CTX.RISK.2", "answer": "1m_to_10m"},
            {"question_id": "CTX.RISK.3", "answer": "no"},
            {"question_id": "CTX.INIT.1", "answer": "customer_due_diligence"},
            {"question_id": "CTX.INIT.2", "answer": "under_3_months"},
            {"question_id": "CTX.INIT.3", "answer": "25l_to_1cr"},
        ],
        "context_profile": {
            "risk_tier": "HIGH",
            "priority_chapters": ["chapter_2", "chapter_3", "cross_border", "breach_notification"],
            "likely_not_applicable": ["CH2.CONSENT.4", "CH2.CONSENT.5", "CH4.CHILD.1", "CH4.CHILD.2", "CH4.CHILD.3"],
            "industry_context": "Fintech processing 2.5M payment users with large-scale financial and behavioral data makes consent, breach response, and transfer controls especially material.",
            "sdf_candidate": True,
            "cross_border_transfers": True,
            "processes_children_data": False,
        },
        "documents": docs,
        "responses": responses,
        "coverage": coverage,
        "findings": findings,
        "hidden_gaps": hidden_gaps,
    }


def healthbridge_fixture() -> dict:
    docs = build_healthbridge_documents()
    doc_lookup = {doc.key: doc.filename for doc in docs}
    overrides = {
        "CH2.CONSENT.1": default_response("partially_implemented", "Consent is gathered through hospital onboarding workflows and our website privacy notice.", doc_lookup["privacy"]),
        "CH2.CONSENT.2": default_response("partially_implemented", "Consent for specific data categories is managed by partner hospitals during patient intake.", doc_lookup["partner"]),
        "CH2.CONSENT.3": default_response("not_implemented", "Consent withdrawal will be part of the Q3 rights portal build.", None),
        "CH2.CONSENT.4": default_response("not_applicable", "We do not use a consent manager platform.", None, confidence="strong", na_reason="no_consent_manager"),
        "CH2.CONSENT.5": default_response("partially_implemented", "We have a children's privacy section in our policy and rely on hospitals to verify age.", doc_lookup["partner"]),
        "CH2.NOTICE.1": default_response("fully_implemented", "We have a published privacy policy.", doc_lookup["privacy"], confidence="strong"),
        "CH2.NOTICE.2": default_response("planned", "Legacy notices are being reviewed as we mature our privacy program.", doc_lookup["privacy"]),
        "CH2.NOTICE.3": default_response("partially_implemented", "Privacy inbox details are published on our website.", doc_lookup["privacy"]),
        "CH2.PURPOSE.1": default_response("partially_implemented", "Data is used for analytics and service delivery as described in our policy.", doc_lookup["privacy"]),
        "CH2.PURPOSE.2": default_response("not_implemented", "Legitimate use documentation has not been formalized.", None),
        "CH2.MINIMIZE.1": default_response("partially_implemented", "We only collect data necessary for our analytics service.", doc_lookup["privacy"]),
        "CH2.MINIMIZE.2": default_response("partially_implemented", "Retention is managed per service requirements.", doc_lookup["privacy"]),
        "CH2.MINIMIZE.3": default_response("not_implemented", "Formal retention schedules and automated deletion procedures are planned.", None),
        "CH2.ACCURACY.1": default_response("partially_implemented", "Data accuracy is primarily the responsibility of the hospital partner providing the records.", doc_lookup["partner"]),
        "CH2.SECURITY.1": default_response("partially_implemented", "Core engineering safeguards are in place; formal certification has not been pursued.", doc_lookup["security"]),
        "CH2.SECURITY.2": default_response("partially_implemented", "We rely on managed cloud infrastructure controls and internal access management.", doc_lookup["security"]),
        "CH2.SECURITY.3": default_response("fully_implemented", "All sub-processors sign our partner agreement.", doc_lookup["partner"], confidence="strong"),
        "CH3.ACCESS.1": default_response("partially_implemented", "Data subjects can contact us at privacy@healthbridge.in for any requests.", doc_lookup["privacy"]),
        "CH3.CORRECT.1": default_response("partially_implemented", "Corrections are supported through the privacy inbox and coordination with engineering.", doc_lookup["privacy"]),
        "CH3.CORRECT.2": default_response("partially_implemented", "Deletion requests are reviewed case by case through the privacy inbox.", doc_lookup["privacy"]),
        "CH3.GRIEVANCE.1": default_response("not_implemented", "We are planning to implement a formal grievance mechanism in Q3.", None),
        "CH3.GRIEVANCE.2": default_response("not_implemented", "Grievance response process will be part of the Q3 rights portal.", None),
        "CH3.NOMINATE.1": default_response("not_implemented", "A nomination process has not yet been established.", None),
        "CH4.CHILD.1": default_response("partially_implemented", "We do not intentionally target children through our website. Hospitals manage patient-facing obligations.", doc_lookup["privacy"]),
        "CH4.CHILD.2": default_response("partially_implemented", "Customer contracts require hospitals to use the service lawfully and responsibly.", doc_lookup["partner"]),
        "CH4.CHILD.3": default_response("partially_implemented", "Age screening is handled by partner hospitals within their intake workflows.", doc_lookup["partner"]),
        "CH4.SDF.1": default_response("fully_implemented", "Our CEO takes personal responsibility for data protection and reports to the Board.", doc_lookup["board"], confidence="strong"),
        "CH4.SDF.2": default_response("not_applicable", "HealthBridge is not currently designated as an SDF.", None, confidence="strong", na_reason="not_designated_sdf"),
        "CH4.SDF.3": default_response("not_applicable", "Formal DPIA obligations are not presently applicable.", None, confidence="strong", na_reason="not_designated_sdf"),
        "CH4.SDF.4": default_response("not_applicable", "Periodic SDF audit obligations are not presently applicable.", None, confidence="strong", na_reason="not_designated_sdf"),
        "CM.RECORDS.1": default_response("partially_implemented", "Consent records are maintained informally through hospital partner records.", doc_lookup["partner"]),
        "CM.RECORDS.2": default_response("not_implemented", "Consent refresh process is not yet formalized.", None),
        "CM.GRANULAR.1": default_response("partially_implemented", "Patients provide consent through hospital intake forms.", doc_lookup["partner"]),
        "CM.GRANULAR.2": default_response("not_implemented", "Granular consent controls are not yet implemented.", None),
        "CB.TRANSFER.1": default_response("not_applicable", "All current infrastructure and processing remain within India.", None, confidence="strong", na_reason="no_cross_border_transfers"),
        "CB.TRANSFER.2": default_response("not_applicable", "No international transfers occur today.", None, confidence="strong", na_reason="no_cross_border_transfers"),
        "CB.TRANSFER.3": default_response("not_applicable", "All current systems are India-based.", None, confidence="strong", na_reason="no_cross_border_transfers"),
        "BN.NOTIFY.1": default_response("planned", "Breach notification playbooks are part of the next compliance sprint.", None),
        "BN.NOTIFY.2": default_response("planned", "Affected-user communication templates are being drafted.", None),
        "BN.NOTIFY.3": default_response("partially_implemented", "Security incident handling exists informally within engineering operations.", doc_lookup["security"]),
        "BN.NOTIFY.4": default_response("not_implemented", "A formal breach register has not yet been introduced.", None),
    }
    responses = build_response_map(
        default_answer="partially_implemented",
        default_note="A lightweight control exists today and will be formalized further as the company scales.",
        doc_lookup=doc_lookup,
        overrides=overrides,
    )
    coverage = {req_id: "partial" for req_id in ALL_REQUIREMENT_IDS}
    for req_id in ["CB.TRANSFER.1", "CB.TRANSFER.2", "CB.TRANSFER.3", "CH4.SDF.2", "CH4.SDF.3", "CH4.SDF.4", "CH2.CONSENT.4"]:
        coverage[req_id] = "absent"
    for req_id in ["CH3.GRIEVANCE.1", "CH3.GRIEVANCE.2", "CH2.CONSENT.3", "CH3.NOMINATE.1", "BN.NOTIFY.1", "BN.NOTIFY.2", "BN.NOTIFY.4"]:
        coverage[req_id] = "absent"
    findings = [
        # Evidence — surface compliance signals
        evidence("CH4.SDF.1", "board", "Board resolution formally appoints CEO as DPO.", "RESOLVED THAT pursuant to the requirements of applicable data protection legislation, Mr. Arjun Mehta, Chief Executive Officer of the Company, be and is hereby appointed to discharge the functions of Data Protection Officer.", "Resolved Matters, Paragraph 1", severity="info"),
        evidence("CH2.NOTICE.1", "privacy", "Privacy policy is published and states DPDPA compliance intent alongside GDPR and CCPA.", "This Privacy Policy is designed to comply with applicable data protection regulations including the General Data Protection Regulation (GDPR) for EU residents, the California Consumer Privacy Act (CCPA) for California residents, and the Digital Personal Data Protection Act (DPDPA) for Indian residents.", "Section 1, Paragraph 1", severity="info"),
        evidence("CH3.ACCESS.1", "privacy", "Privacy policy publishes an email address for data rights requests.", "If you have questions regarding this Privacy Policy or wish to exercise your data rights, please contact us at privacy@healthbridge.in.", "Section 4, Paragraph 2", severity="info"),
        evidence("CH2.MINIMIZE.1", "privacy", "Privacy policy states a data minimization principle.", "We are committed to data minimization and only collect personal data that is adequate, relevant, and necessary for the purposes described in this policy.", "Section 2, Paragraph 1", severity="info"),
        evidence("CH2.CONSENT.5", "privacy", "Privacy policy contains a children's section but uses a US COPPA age threshold.", "We do not knowingly collect personal data from children under the age of 13.", "Section 3, Paragraph 1", severity="info"),
        evidence("CH2.SECURITY.1", "security", "Security policy states commitment to protecting health data and restricting access.", "HealthBridge Analytics is committed to protecting the security and integrity of personal and health data. Access to systems is restricted to authorized personnel.", "Section 1, Paragraph 1", severity="info"),
        # Signal — red flags
        signal("CH2.NOTICE.1", "privacy", "Privacy policy prominently references GDPR and CCPA — template artifact signals the policy was not drafted for Indian data principals.", "This Privacy Policy is designed to comply with applicable data protection regulations including the General Data Protection Regulation (GDPR) for EU residents, the California Consumer Privacy Act (CCPA) for California residents.", "Section 1, Paragraph 1", severity="high"),
        signal("CH2.NOTICE.1", "privacy", "Policy lists only name, email, phone, and date of birth as collected data types — health records, diagnostic data, and lab results are entirely absent despite being a health analytics company.", "We collect information you provide including name, email address, phone number, date of birth, and any health information you choose to share with us.", "Section 1, Paragraph 2", severity="critical"),
        signal("CH2.CONSENT.5", "privacy", "DPDPA defines a child as under 18. HealthBridge uses an under-13 threshold copied from a US COPPA template — leaving patients aged 13-17 without the required parental consent protections.", "We do not knowingly collect personal data from children under the age of 13.", "Section 3, Paragraph 1", severity="critical"),
        signal("CH4.CHILD.3", "partner", "Partner agreement delegates all age verification and parental consent obligations to hospitals with a single sentence, without specifying DPDPA's under-18 threshold or parental consent verification mechanism.", "Data Controller acknowledges and agrees that it is solely responsible for obtaining all necessary consents, authorizations, and approvals from patients, their legal representatives, and applicable institutions as required under applicable law prior to sharing any patient data with HealthBridge Analytics.", "Section 1, Paragraph 2", severity="high"),
        signal("CH4.SDF.1", "board", "Board resolution combines CEO commercial decision-making and DPO oversight with no independence, no time allocation, no DPO training requirement, and no board reporting cadence.", "No further standing committee or reporting cadence is established by this resolution at this time.", "Administrative Note, Paragraph 1", severity="high"),
        signal("CH2.SECURITY.3", "partner", "Partner agreement contains a single-sentence security obligation for all processors; no processing instructions, no audit rights, no breach notification obligation, no sub-processor restriction.", "Both parties will maintain commercially reasonable safeguards appropriate to the nature of the services.", "Section 2, Paragraph 1", severity="high"),
        signal("CH2.MINIMIZE.1", "privacy", "Data minimization is stated as a principle but the policy contains no description of which data fields are collected or why each is necessary for analytics.", "We are committed to data minimization and only collect personal data that is adequate, relevant, and necessary for the purposes described in this policy.", "Section 2, Paragraph 1", severity="medium"),
        # Absence — required controls not present
        absence("CH3.ACCESS.1", "No internal rights-handling SOP or request tracking system exists. The privacy inbox is a shared developer mailbox with no SLA, no defined process, and no technical mechanism to export patient data without manual database queries.", severity="high"),
        absence("CH3.CORRECT.2", "No documented deletion workflow or engineering runbook exists for erasing patient data on request. Deletion would require manual developer intervention in production MongoDB collections.", severity="high"),
        absence("CH2.SECURITY.3", "No dedicated Data Processing Agreement or processor annex exists for AWS, MongoDB Atlas, Razorpay, SendGrid, Twilio, or Segment — all of which handle patient-linked data.", severity="high"),
        absence("CH2.SECURITY.2", "No access control matrix, role-based access control policy, or audit logging procedure is documented. Developers have read access to the production database by default.", severity="high"),
        absence("CH3.GRIEVANCE.1", "No grievance mechanism exists for data principals. The Q3 rights portal has not been built. Patients who interact only with hospitals do not know HealthBridge exists as a processor.", severity="critical"),
    ]
    hidden_gaps = [
        {
            "requirement_ids": ["CH4.CHILD.1", "CH4.CHILD.2", "CH4.CHILD.3", "CH2.CONSENT.5"],
            "surface_answer": "partially_implemented",
            "actual_status": "non_compliant",
            "gap_description": "DPDPA defines a child as under 18. HealthBridge's policy uses under-13 (copied from a US COPPA template). Pediatric records ages 0-17 flow through hospital integrations. No direct age verification exists. Parental consent is delegated to hospitals via one sentence in the partner agreement that does not reference DPDPA's under-18 threshold.",
            "evidence_in_document": doc_lookup["privacy"],
            "evidence_quote_hint": "We do not knowingly collect personal data from children under the age of 13.",
            "probing_depth": 3,
            "what_followup_should_ask": "DPDPA defines a child as under 18, not under 13. How do you obtain verifiable parental consent for patients aged 13-17 whose records you process through hospital integrations?",
        },
        {
            "requirement_ids": ["CH4.SDF.1"],
            "surface_answer": "fully_implemented",
            "actual_status": "non_compliant",
            "gap_description": "The CEO has zero data protection training, zero hours per week allocated to DPO functions, and decides what data to collect AND oversees compliance — a structural conflict of interest. No DPO contact details are published to data principals. No board reporting cadence exists. The resolution is a template with the CEO name filled in.",
            "evidence_in_document": doc_lookup["board"],
            "evidence_quote_hint": "RESOLVED THAT pursuant to the requirements of applicable data protection legislation, Mr. Arjun Mehta, Chief Executive Officer of the Company, be and is hereby appointed to discharge the functions of Data Protection Officer.",
            "probing_depth": 3,
            "what_followup_should_ask": "What data protection training has the DPO completed, how many hours per week are allocated to DPO duties, and can you share the last data protection report presented to the Board?",
        },
        {
            "requirement_ids": ["CH2.NOTICE.1"],
            "surface_answer": "fully_implemented",
            "actual_status": "non_compliant",
            "gap_description": "The privacy policy was generated from a legal template website and contains explicit GDPR and CCPA references. The data types section lists only name, email, phone, and date of birth — never mentions health records, diagnostic data, lab results, treatment histories, or medication information. The hospital partnership data flow (99% of their data) is not described. Patients whose data flows through hospital integrations never see this policy.",
            "evidence_in_document": doc_lookup["privacy"],
            "evidence_quote_hint": "This Privacy Policy is designed to comply with applicable data protection regulations including the General Data Protection Regulation (GDPR) for EU residents, the California Consumer Privacy Act (CCPA) for California residents.",
            "probing_depth": 2,
            "what_followup_should_ask": "Where do hospital patients actually receive notice about HealthBridge processing their health records, and why does the published notice omit health records and partner-hospital data flows entirely?",
        },
        {
            "requirement_ids": ["CH3.ACCESS.1", "CH3.CORRECT.1", "CH3.CORRECT.2"],
            "surface_answer": "partially_implemented",
            "actual_status": "non_compliant",
            "gap_description": "privacy@healthbridge.in is a shared developer inbox. No SLA exists. 3 requests received in 12 months; 1 responded to after 47 days. No technical mechanism to export patient data from MongoDB without a developer manually querying the production database. Patients whose data came via hospital integration cannot identify HealthBridge as a processor.",
            "evidence_in_document": doc_lookup["privacy"],
            "evidence_quote_hint": "If you have questions regarding this Privacy Policy or wish to exercise your data rights, please contact us at privacy@healthbridge.in.",
            "probing_depth": 3,
            "what_followup_should_ask": "Walk me through exactly what happens when a data principal submits an access request — who receives it, what system do you query, what format is the export, and what is your SLA?",
        },
        {
            "requirement_ids": ["CH2.SECURITY.3"],
            "surface_answer": "fully_implemented",
            "actual_status": "non_compliant",
            "gap_description": "The hospital partner agreement contains a single-sentence security commitment ('commercially reasonable safeguards'). No data processing purpose limitation, no sub-processor notification rights, no audit rights, no breach notification obligation from processor to HealthBridge. AWS, MongoDB Atlas, Razorpay, SendGrid, and Twilio all handle patient-linked data with no DPDPA-compliant DPA.",
            "evidence_in_document": doc_lookup["partner"],
            "evidence_quote_hint": "Both parties will maintain commercially reasonable safeguards appropriate to the nature of the services.",
            "probing_depth": 2,
            "what_followup_should_ask": "Provide the Data Processing Agreement with AWS, MongoDB Atlas, and your other sub-processors that includes security obligations, processing instructions, breach notification duties, and audit rights.",
        },
        {
            "requirement_ids": ["CH2.SECURITY.1", "CH2.SECURITY.2"],
            "surface_answer": "partially_implemented",
            "actual_status": "non_compliant",
            "gap_description": "The security policy is 3 pages written by the CEO in a day. No role-based access control system exists. Developers have read access to production database containing patient records by default. No audit log of who accessed what patient record. No penetration test ever conducted. 'Security awareness training' is one 30-minute video at onboarding.",
            "evidence_in_document": doc_lookup["security"],
            "evidence_quote_hint": "HealthBridge Analytics is committed to protecting the security and integrity of personal and health data. Access to systems is restricted to authorized personnel.",
            "probing_depth": 2,
            "what_followup_should_ask": "Provide the access control matrix for your production database, the audit log showing who accessed patient records in the past 90 days, and the most recent penetration test report.",
        },
        {
            "requirement_ids": ["CH2.MINIMIZE.1"],
            "surface_answer": "partially_implemented",
            "actual_status": "non_compliant",
            "gap_description": "HealthBridge requests full patient records (diagnosis codes, medication lists, lab values, imaging reports) from hospital APIs. Their analytics product only needs aggregate trends, not individual patient-level clinical detail. They ingest the full record 'to ensure we have everything if the algorithms need it later.' No data minimization review has ever been conducted.",
            "evidence_in_document": doc_lookup["privacy"],
            "evidence_quote_hint": "We are committed to data minimization and only collect personal data that is adequate, relevant, and necessary for the purposes described in this policy.",
            "probing_depth": 3,
            "what_followup_should_ask": "Provide the list of every data field ingested from hospital APIs and the specific analytics purpose that requires each field. Which fields could be excluded or aggregated without affecting your product?",
        },
        {
            "requirement_ids": ["CH3.GRIEVANCE.1", "CH3.GRIEVANCE.2"],
            "surface_answer": "not_implemented",
            "actual_status": "non_compliant",
            "gap_description": "No grievance mechanism exists even in nominal form. The acknowledged Q3 timeline gap is worse than it appears: patients do not know HealthBridge exists as a processor and interact only with hospitals, so even if a portal were built, patients have no way to find it. No communication identifies HealthBridge as a processor to data principals.",
            "evidence_in_document": doc_lookup["privacy"],
            "evidence_quote_hint": "The contact details for our privacy function are privacy@healthbridge.in.",
            "probing_depth": 2,
            "what_followup_should_ask": "How would a patient whose records HealthBridge received from a hospital know that HealthBridge exists as a processor? What communication informs them of this, and where is the grievance portal accessible to them?",
        },
        {
            "requirement_ids": ["CH2.CONSENT.3"],
            "surface_answer": "not_implemented",
            "actual_status": "non_compliant",
            "gap_description": "Since all data comes via hospital integrations, patients cannot identify HealthBridge as the processor to contact for consent withdrawal. Even if they did, there is no mechanism to withdraw consent for specific processing activities without withdrawing from the hospital's own system. Deletion requires manual developer intervention in production databases.",
            "evidence_in_document": doc_lookup["partner"],
            "evidence_quote_hint": "Data Controller acknowledges and agrees that it is solely responsible for obtaining all necessary consents, authorizations, and approvals from patients.",
            "probing_depth": 2,
            "what_followup_should_ask": "If a patient wants to withdraw consent for HealthBridge's processing of their health records, what is the exact mechanism they use, who do they contact, and how is the withdrawal technically implemented?",
        },
    ]
    return {
        "company_name": "HealthBridge Analytics",
        "industry": "healthcare",
        "company_size": "startup",
        "description": "Healthcare SaaS startup with nominal compliance: GDPR/CCPA template policy, CEO-as-DPO with zero training, wrong children threshold, no access controls, and no real grievance mechanism.",
        "context_answers": [
            {"question_id": "CTX.DATA.1", "answer": ["identity", "health", "financial", "childrens"]},
            {"question_id": "CTX.DATA.2", "answer": ["third_party_apis", "web_forms"]},
            {"question_id": "CTX.DATA.3", "answer": "yes"},
            {"question_id": "CTX.DATA.4", "answer": "no"},
            {"question_id": "CTX.POSTURE.1", "answer": "part_time_shared"},
            {"question_id": "CTX.POSTURE.2", "answer": "none"},
            {"question_id": "CTX.POSTURE.3", "answer": "no"},
            {"question_id": "CTX.POSTURE.4", "answer": "yes_recently_updated"},
            {"question_id": "CTX.RISK.1", "answer": ["processes_childrens_data", "healthcare_finance_critical_infra", "handles_sensitive_personal_data"]},
            {"question_id": "CTX.RISK.2", "answer": "10k_to_1m"},
            {"question_id": "CTX.RISK.3", "answer": "no"},
            {"question_id": "CTX.INIT.1", "answer": "investor_board_requirement"},
            {"question_id": "CTX.INIT.2", "answer": "3_to_6_months"},
            {"question_id": "CTX.INIT.3", "answer": "under_5l"},
        ],
        "context_profile": {
            "risk_tier": "HIGH",
            "priority_chapters": ["chapter_2", "chapter_4", "chapter_3"],
            "likely_not_applicable": ["CB.TRANSFER.1", "CB.TRANSFER.2", "CB.TRANSFER.3", "CH4.SDF.2", "CH4.SDF.3", "CH4.SDF.4", "CH2.CONSENT.4"],
            "industry_context": "Healthcare processing, pediatric records, and partner-hospital data flows make notice, children's protections, and rights handling especially sensitive.",
            "sdf_candidate": False,
            "cross_border_transfers": False,
            "processes_children_data": True,
        },
        "documents": docs,
        "responses": responses,
        "coverage": coverage,
        "findings": findings,
        "hidden_gaps": hidden_gaps,
    }


def dakshin_fixture() -> dict:
    docs = build_dakshin_documents()
    doc_lookup = {doc.key: doc.filename for doc in docs}
    overrides = {
        "CH2.CONSENT.1": default_response("fully_implemented", "We have documented consent from all employees and drivers. Consent forms are signed during onboarding.", doc_lookup["employment"], confidence="strong"),
        "CH2.CONSENT.2": default_response("partially_implemented", "Multi-purpose processing is disclosed in relevant notices and forms.", doc_lookup["employment"]),
        "CH2.CONSENT.3": default_response("partially_implemented", "Employees can raise concerns through the DPO portal.", doc_lookup["grievance"]),
        "CH2.CONSENT.4": default_response("not_applicable", "No consent manager is used.", None, confidence="strong", na_reason="no_consent_manager"),
        "CH2.CONSENT.5": default_response("not_applicable", "Dakshin does not intentionally process children's data.", None, confidence="strong", na_reason="does_not_process_childrens_data"),
        "CH2.NOTICE.2": default_response("planned", "We updated our website privacy policy when DPDPA was enacted. Retrospective notice plan is under review.", doc_lookup["privacy"]),
        "CH2.MINIMIZE.1": default_response("fully_implemented", "Our GPS policy describes data minimization. We retain location data for dispute resolution.", doc_lookup["gps"], confidence="strong"),
        "CH2.MINIMIZE.2": default_response("fully_implemented", "Retention periods are documented for operational needs and dispute resolution.", doc_lookup["gps"], confidence="strong"),
        "CH2.MINIMIZE.3": default_response("partially_implemented", "Deletion controls are managed through operational systems and records policies.", doc_lookup["gps"]),
        "CH3.GRIEVANCE.1": default_response("fully_implemented", "We have a dedicated DPO portal and email channel. The DPO is accessible.", doc_lookup["grievance"], confidence="strong"),
        "CH3.GRIEVANCE.2": default_response("fully_implemented", "Privacy grievances are centrally logged and responded to through the privacy workflow.", doc_lookup["grievance"], confidence="strong"),
        "CH4.CHILD.1": default_response("not_applicable", "Children's data is not part of the normal logistics business model.", None, confidence="strong", na_reason="does_not_process_childrens_data"),
        "CH4.CHILD.2": default_response("not_applicable", "Children's data is not intentionally processed.", None, confidence="strong", na_reason="does_not_process_childrens_data"),
        "CH4.CHILD.3": default_response("not_applicable", "Age verification is not used in the current operating model.", None, confidence="strong", na_reason="does_not_process_childrens_data"),
        "CH4.SDF.1": default_response("fully_implemented", "We have a full-time, qualified DPO who has been in role for 18 months.", doc_lookup["grievance"], confidence="strong"),
        "CH4.SDF.2": default_response("partially_implemented", "External audit support is being aligned to the broader compliance roadmap.", doc_lookup["transfer"]),
        "CH4.SDF.3": default_response("partially_implemented", "Privacy impact assessments are conducted in selected high-risk programs.", doc_lookup["transfer"]),
        "CH4.SDF.4": default_response("fully_implemented", "Governance and assurance activities are integrated with the enterprise compliance function.", doc_lookup["transfer"], confidence="strong"),
        "CM.GRANULAR.1": default_response("fully_implemented", "Our performance scoring uses delivery metrics as described in the employee notice.", doc_lookup["employment"], confidence="strong"),
        "CM.GRANULAR.2": default_response("partially_implemented", "Where processing is necessary for operations, the notice explains the data uses tied to the role.", doc_lookup["employment"]),
        "CB.TRANSFER.1": default_response("partially_implemented", "We have an inter-company data transfer agreement with our UAE subsidiary. GDPR-compliant SCCs are in place.", doc_lookup["transfer"]),
        "CB.TRANSFER.2": default_response("partially_implemented", "Inter-company transfer terms exist for the UAE affiliate.", doc_lookup["transfer"]),
        "CB.TRANSFER.3": default_response("partially_implemented", "Localisation obligations are monitored through the central privacy office.", doc_lookup["transfer"]),
        "BN.NOTIFY.1": default_response("partially_implemented", "Incident and regulatory escalation are managed through central governance channels.", doc_lookup["grievance"]),
        "BN.NOTIFY.2": default_response("partially_implemented", "Affected-party communications are coordinated through the privacy and communications teams.", doc_lookup["grievance"]),
        "BN.NOTIFY.3": default_response("fully_implemented", "Incident management is formalized as part of the enterprise governance program.", doc_lookup["grievance"], confidence="strong"),
        "BN.NOTIFY.4": default_response("partially_implemented", "Material incidents are logged centrally with follow-up actions.", doc_lookup["grievance"]),
    }
    responses = build_response_map(
        default_answer="fully_implemented",
        default_note="Control is operating across the enterprise and is supported by documented governance.",
        doc_lookup=doc_lookup,
        overrides=overrides,
    )
    coverage = {req_id: "adequate" for req_id in ALL_REQUIREMENT_IDS}
    for req_id in [
        "CH2.CONSENT.1", "CH2.CONSENT.2", "CH2.CONSENT.3",
        "CH2.NOTICE.2",
        "CH2.MINIMIZE.1", "CH2.MINIMIZE.2", "CH2.MINIMIZE.3",
        "CH3.GRIEVANCE.1", "CH3.GRIEVANCE.2",
        "CM.GRANULAR.1", "CM.GRANULAR.2",
        "CB.TRANSFER.1", "CB.TRANSFER.2", "CB.TRANSFER.3",
        "BN.NOTIFY.1", "BN.NOTIFY.2", "BN.NOTIFY.4",
    ]:
        coverage[req_id] = "partial"
    coverage["CH2.NOTICE.2"] = "absent"
    for req_id in ["CH2.CONSENT.4", "CH2.CONSENT.5", "CH4.CHILD.1", "CH4.CHILD.2", "CH4.CHILD.3"]:
        coverage[req_id] = "absent"
    findings = [
        # Evidence — surface compliance signals
        evidence("CH2.CONSENT.1", "employment", "Employment notice contains consent clause as a condition of employment.", "As a condition of your employment with Dakshin Logistics Group, you acknowledge and consent to the collection, processing, storage, and use of your personal data as described in this Employee Data Processing Notice.", "Section 1, Paragraph 2", severity="info"),
        evidence("CH2.MINIMIZE.1", "gps", "GPS policy describes operational purposes for location collection.", "Location data is collected from drivers using the Dakshin Driver App to support route optimization, delivery confirmation, driver safety monitoring, and compliance with customer service-level agreements.", "Section 1, Paragraph 2", severity="info"),
        evidence("CH3.GRIEVANCE.1", "grievance", "Grievance procedure describes portal, email, and written submission channels.", "Data principals may submit grievances or exercise their rights under the DPDPA by: (1) Submitting a request through the Data Protection Portal at privacy.dakshinlogistics.com (login required); (2) Emailing the DPO at dpo@dakshinlogistics.com; (3) Writing to the Data Protection Officer, Dakshin Logistics Group, Mumbai.", "Section 1, Paragraph 1", severity="info"),
        evidence("CH4.SDF.1", "grievance", "DPO ownership documented in grievance procedure.", "This procedure is owned by the Data Protection Officer and reviewed annually in consultation with Legal, Human Resources, Customer Service, and Technology.", "Section 3, Paragraph 1", severity="info"),
        evidence("CB.TRANSFER.2", "transfer", "Cross-border transfer framework documents UAE transfer under GDPR SCCs.", "Transfers to Dakshin Middle East FZE (UAE) are governed by Standard Contractual Clauses as approved by the European Commission pursuant to Regulation (EU) 2016/679 (GDPR).", "Section 1, Paragraph 2", severity="info"),
        evidence("CH2.NOTICE.1", "privacy", "Privacy policy updated November 2023 with DPDPA reference.", "This Privacy Policy was updated in November 2023 to reflect the requirements of the Digital Personal Data Protection Act, 2023. We have reviewed and updated our data processing practices to align with the new framework.", "Section 1, Paragraph 1", severity="info"),
        evidence("CM.GRANULAR.1", "employment", "Employee notice lists performance data categories.", "Performance data collected includes delivery completion rates, route adherence metrics, customer satisfaction scores, and safety compliance records. This information is used to evaluate driver performance, determine incentive eligibility, and inform personnel decisions.", "Section 2, Paragraph 2", severity="info"),
        # Signal — red flags
        signal("CH2.CONSENT.1", "employment", "Consent is framed as a condition of employment — sign or don't get the job. Freely given consent under DPDPA cannot be coerced through a take-it-or-leave-it employment contract.", "As a condition of your employment with Dakshin Logistics Group, you acknowledge and consent to the collection, processing, storage, and use of your personal data as described in this Employee Data Processing Notice.", "Section 1, Paragraph 2", severity="critical"),
        signal("CM.GRANULAR.1", "employment", "GPS location tracking and performance scoring are bundled in a single consent clause with no option to accept one and decline the other.", "These processes are integral to your role and to the services Dakshin provides to its customers. By signing the onboarding documents and continuing in employment, personnel confirm that they understand the categories of information processed.", "Section 1, Paragraph 3", severity="high"),
        signal("CH2.MINIMIZE.2", "gps", "GPS policy states collection is during 'active duty hours' but the employment notice describes continuous collection — a direct cross-document contradiction. Technical implementation aligns with 24/7 collection.", "Data is collected continuously during active duty hours.", "Section 1, Paragraph 2", severity="critical"),
        signal("CH2.MINIMIZE.2", "gps", "36-month retention for location data far exceeds any dispute resolution purpose. The stated justification covers only the first 30 days of post-delivery disputes.", "Location records are retained for a period of 36 months for operational and legal dispute resolution purposes.", "Section 1, Paragraph 2", severity="high"),
        signal("CB.TRANSFER.2", "transfer", "Cross-border framework uses EU Standard Contractual Clauses — an EU legal mechanism not recognized under DPDPA Section 16. No DPDPA-specific transfer mechanism documented.", "This Data Transfer Framework governs the transfer of personal data between Dakshin Logistics Group entities and to third-party processors outside the European Economic Area and India. Transfers to Dakshin Middle East FZE (UAE) are governed by Standard Contractual Clauses as approved by the European Commission pursuant to Regulation (EU) 2016/679 (GDPR).", "Section 1, Paragraph 2", severity="critical"),
        signal("CH3.GRIEVANCE.1", "grievance", "DPO portal requires a Dakshin corporate email login. Drivers and warehouse workers do not have corporate email. No WhatsApp, phone, QR code, or physical form channel is provided for the 180,000 blue-collar workforce.", "Submitting a request through the Data Protection Portal at privacy.dakshinlogistics.com (login required)", "Section 1, Paragraph 1", severity="high"),
        signal("CH4.SDF.1", "grievance", "DPO reports through the General Counsel who also approves commercial data sharing arrangements the DPO may need to scrutinize — a structural independence conflict.", "The DPO reports through the Group Legal function and coordinates with the General Counsel on matters with legal, regulatory, or commercial implications.", "Section 2, Paragraph 3", severity="high"),
        signal("CM.GRANULAR.1", "employment", "Performance scoring algorithm inputs are limited to listed delivery metrics in the notice, but undisclosed inputs include time-of-day patterns, social network data from the app, device type, and off-duty location data.", "Performance data collected includes delivery completion rates, route adherence metrics, customer satisfaction scores, and safety compliance records.", "Section 2, Paragraph 2", severity="high"),
        # Absence — required controls not present
        absence("CH2.NOTICE.2", "No document evidences retrospective notice to the 4.2M data principals whose data was collected before DPDPA came into force. The website was updated; no direct communication was sent to existing employees, drivers, customers, or vendors.", severity="high"),
        absence("CB.TRANSFER.1", "Saudi Arabia receives driver data via a shared ERP system but is completely undocumented in the cross-border transfer framework. No transfer documentation, no legal basis, no security assessment.", severity="critical"),
        absence("CH2.SECURITY.3", "No Data Processing Agreement exists for the 40+ third-party logistics subcontractors who receive driver and customer data via EDI and API integrations. Only technology vendors are covered; the logistics partner ecosystem is unaddressed.", severity="high"),
    ]
    hidden_gaps = [
        {
            "requirement_ids": ["CH2.CONSENT.1", "CM.GRANULAR.1"],
            "surface_answer": "fully_implemented",
            "actual_status": "non_compliant",
            "gap_description": "Employment consent is obtained as a condition of the job offer — sign or don't get hired. Drivers cannot consent to route tracking and decline performance scoring. They cannot decline GPS tracking and remain employed. Consent obtained as a condition of employment is not freely given under DPDPA.",
            "evidence_in_document": doc_lookup["employment"],
            "evidence_quote_hint": "As a condition of your employment with Dakshin Logistics Group, you acknowledge and consent to the collection, processing, storage, and use of your personal data as described in this Employee Data Processing Notice.",
            "probing_depth": 4,
            "what_followup_should_ask": "Can a driver at Dakshin decline GPS tracking while remaining employed? Can they consent to identity processing but decline performance evaluation scoring? What happens to employment if they refuse the data processing consent form?",
        },
        {
            "requirement_ids": ["CH2.MINIMIZE.1", "CH2.MINIMIZE.2"],
            "surface_answer": "fully_implemented",
            "actual_status": "non_compliant",
            "gap_description": "The GPS policy says collection is 'during active duty hours' but the employment notice describes continuous collection — a direct cross-document contradiction. Technical implementation is 24/7, every 15 seconds. 180,000 drivers tracked continuously for 36 months equals a massive unminimized dataset. The stated retention purpose (dispute resolution) is satisfied in 30 days.",
            "evidence_in_document": doc_lookup["gps"],
            "evidence_quote_hint": "Data is collected continuously during active duty hours. Location records are retained for a period of 36 months for operational and legal dispute resolution purposes.",
            "probing_depth": 4,
            "what_followup_should_ask": "What is the exact GPS ping interval? Do you collect location data outside work hours? Can you show me the technical configuration that stops tracking when a driver clocks out? What specific dispute requires 36 months of location history?",
        },
        {
            "requirement_ids": ["CH2.NOTICE.2"],
            "surface_answer": "planned",
            "actual_status": "non_compliant",
            "gap_description": "Dakshin updated its website privacy policy when DPDPA came into force but sent no communication to existing employees, drivers, customers, or vendors. 4.2M data principals have never been informed of their rights under DPDPA. A website update that existing data principals have no reason to check does not constitute effective retrospective notice.",
            "evidence_in_document": doc_lookup["privacy"],
            "evidence_quote_hint": "This Privacy Policy was updated in November 2023 to reflect the requirements of the Digital Personal Data Protection Act, 2023.",
            "probing_depth": 3,
            "what_followup_should_ask": "How did you notify the 4.2M data principals whose data was collected before DPDPA came into force that they now have rights under the Act? What was the communication channel, timeline, and evidence of delivery?",
        },
        {
            "requirement_ids": ["CB.TRANSFER.1", "CB.TRANSFER.2", "CB.TRANSFER.3"],
            "surface_answer": "partially_implemented",
            "actual_status": "non_compliant",
            "gap_description": "The cross-border framework uses EU Standard Contractual Clauses — a GDPR mechanism not recognized under DPDPA Section 16. Saudi Arabia receives driver data via a shared ERP with zero documentation. The framework has never been reviewed by Indian counsel. No DPDPA-compliant transfer mechanism exists for any jurisdiction.",
            "evidence_in_document": doc_lookup["transfer"],
            "evidence_quote_hint": "Transfers to Dakshin Middle East FZE (UAE) are governed by Standard Contractual Clauses as approved by the European Commission pursuant to Regulation (EU) 2016/679 (GDPR).",
            "probing_depth": 4,
            "what_followup_should_ask": "Your cross-border framework references EU SCCs. DPDPA's Section 16 transfer framework is independent of GDPR. What DPDPA-compliant mechanism do you rely on for transfers to UAE and Saudi Arabia?",
        },
        {
            "requirement_ids": ["CH3.GRIEVANCE.1", "CH3.GRIEVANCE.2"],
            "surface_answer": "fully_implemented",
            "actual_status": "non_compliant",
            "gap_description": "The DPO portal requires a Dakshin corporate email login. Drivers and warehouse workers — approximately 180,000 people — do not have corporate email. No WhatsApp, phone, QR code, or physical form channel exists. Zero grievances have been received from the driver or warehouse population in two years.",
            "evidence_in_document": doc_lookup["grievance"],
            "evidence_quote_hint": "Submitting a request through the Data Protection Portal at privacy.dakshinlogistics.com (login required)",
            "probing_depth": 3,
            "what_followup_should_ask": "A driver who doesn't have a corporate email wants to submit a data grievance. Walk me through exactly how they do that. How many grievances have you received from drivers or warehouse workers in the past 24 months?",
        },
        {
            "requirement_ids": ["CH2.SECURITY.3"],
            "surface_answer": "partially_implemented",
            "actual_status": "non_compliant",
            "gap_description": "Approximately 40 third-party logistics subcontractors receive driver, customer, and delivery data via EDI and API integrations. None have Data Processing Agreements — only commercial logistics contracts. The DPO focused on technology vendors (AWS, SAP) but not the logistics partner ecosystem, which is the highest-risk category for data leakage.",
            "evidence_in_document": doc_lookup["transfer"],
            "evidence_quote_hint": "This Data Transfer Framework governs the transfer of personal data between Dakshin Logistics Group entities and to third-party processors.",
            "probing_depth": 2,
            "what_followup_should_ask": "Do the 40+ third-party logistics subcontractors who receive driver and customer data via your EDI integrations have signed Data Processing Agreements? Provide the list.",
        },
        {
            "requirement_ids": ["CM.GRANULAR.1"],
            "surface_answer": "fully_implemented",
            "actual_status": "non_compliant",
            "gap_description": "The performance scoring algorithm ingests undisclosed inputs: time-of-day patterns (implying lifestyle inferences), social network data from the app (which drivers interact with), personal device type and app version (used as proxy for 'tech savvy' in promotion decisions), and location data during rest periods (to infer moonlighting). None of these inputs are disclosed in the employee notice.",
            "evidence_in_document": doc_lookup["employment"],
            "evidence_quote_hint": "Performance data collected includes delivery completion rates, route adherence metrics, customer satisfaction scores, and safety compliance records.",
            "probing_depth": 3,
            "what_followup_should_ask": "Provide the complete list of data inputs to your driver performance scoring algorithm and map each input to the disclosure in the employee data processing notice.",
        },
        {
            "requirement_ids": ["CH4.SDF.1"],
            "surface_answer": "fully_implemented",
            "actual_status": "partially_compliant",
            "gap_description": "The DPO reports to the General Counsel who is also the legal head for commercial business transactions the DPO may need to scrutinize. The GC has pressured the DPO to approve data sharing arrangements the DPO flagged as non-compliant. No direct Board access. No board charter establishing DPO independence.",
            "evidence_in_document": doc_lookup["grievance"],
            "evidence_quote_hint": "The DPO reports through the Group Legal function and coordinates with the General Counsel on matters with legal, regulatory, or commercial implications.",
            "probing_depth": 2,
            "what_followup_should_ask": "If the DPO raises a compliance concern about a processing activity the General Counsel has approved commercially, what is the escalation path and who makes the final decision?",
        },
        {
            "requirement_ids": ["CH2.NOTICE.1"],
            "surface_answer": "fully_implemented",
            "actual_status": "partially_compliant",
            "gap_description": "The driver data processing notice is written in formal corporate English with legal terminology — 'data principal,' 'data fiduciary,' 'legitimate interest,' 'processing activities,' 'retention schedule.' Approximately Grade 12 reading level in 10pt font over 8 pages. Drivers typically complete education to Grade 8-10. DPDPA requires notice in 'clear and plain language.' A technically present but practically incomprehensible notice is not effective notice.",
            "evidence_in_document": doc_lookup["employment"],
            "evidence_quote_hint": "As a condition of your employment with Dakshin Logistics Group, you acknowledge and consent to the collection, processing, storage, and use of your personal data as described in this Employee Data Processing Notice.",
            "probing_depth": 2,
            "what_followup_should_ask": "Has the driver data processing notice been tested for readability with the actual audience? What steps have you taken to ensure it is understandable to employees with lower literacy levels?",
        },
    ]
    return {
        "company_name": "Dakshin Logistics Group",
        "industry": "manufacturing",
        "company_size": "large",
        "description": "Large logistics enterprise with GDPR competence creating dangerous blind spots: coerced employment consent, 24/7 GPS tracking disguised as active-duty-only, GDPR SCCs passed off as DPDPA compliance, and a DPO portal inaccessible to 180,000 blue-collar workers.",
        "context_answers": [
            {"question_id": "CTX.DATA.1", "answer": ["identity", "financial", "location", "behavioral"]},
            {"question_id": "CTX.DATA.2", "answer": ["web_forms", "mobile_app", "automated_tracking"]},
            {"question_id": "CTX.DATA.3", "answer": "yes"},
            {"question_id": "CTX.DATA.4", "answer": "yes"},
            {"question_id": "CTX.DATA.4a", "answer": "United Arab Emirates and Saudi Arabia"},
            {"question_id": "CTX.POSTURE.1", "answer": "full_time"},
            {"question_id": "CTX.POSTURE.2", "answer": "iso_27001_certified"},
            {"question_id": "CTX.POSTURE.3", "answer": "external_audit"},
            {"question_id": "CTX.POSTURE.4", "answer": "yes_recently_updated"},
            {"question_id": "CTX.RISK.1", "answer": ["handles_sensitive_personal_data", "designated_or_likely_sdf"]},
            {"question_id": "CTX.RISK.2", "answer": "1m_to_10m"},
            {"question_id": "CTX.RISK.3", "answer": "yes_reported"},
            {"question_id": "CTX.INIT.1", "answer": "regulatory_audit_prep"},
            {"question_id": "CTX.INIT.2", "answer": "under_3_months"},
            {"question_id": "CTX.INIT.3", "answer": "above_1cr"},
        ],
        "context_profile": {
            "risk_tier": "HIGH",
            "priority_chapters": ["chapter_2", "chapter_3", "cross_border", "chapter_4"],
            "likely_not_applicable": ["CH2.CONSENT.4", "CH2.CONSENT.5", "CH4.CHILD.1", "CH4.CHILD.2", "CH4.CHILD.3"],
            "industry_context": "Large-scale logistics operations with 180,000 drivers, GPS tracking, overseas affiliates, and 4.2M data principals create elevated risk for consent, minimization, notice, and transfer controls.",
            "sdf_candidate": True,
            "cross_border_transfers": True,
            "processes_children_data": False,
        },
        "documents": docs,
        "responses": responses,
        "coverage": coverage,
        "findings": findings,
        "hidden_gaps": hidden_gaps,
    }


def build_company_fixtures() -> list[dict]:
    return [novapay_fixture(), healthbridge_fixture(), dakshin_fixture()]


def validate_fixture(fixture: dict) -> None:
    if set(fixture["responses"]) != set(ALL_REQUIREMENT_IDS):
        missing = sorted(set(ALL_REQUIREMENT_IDS) - set(fixture["responses"]))
        extra = sorted(set(fixture["responses"]) - set(ALL_REQUIREMENT_IDS))
        raise ValueError(f"{fixture['company_name']} response map mismatch. Missing={missing} Extra={extra}")
    if not 3 <= len(fixture["documents"]) <= 5:
        raise ValueError(f"{fixture['company_name']} must have 3-5 documents")
    if not 10 <= len(fixture["findings"]) <= 20:
        raise ValueError(f"{fixture['company_name']} must have 10-20 findings")


def purge_existing(session, company_names: list[str]) -> None:
    existing = session.query(Assessment).filter(Assessment.company_name.in_(company_names)).all()
    if not existing:
        return

    assessment_ids = [assessment.id for assessment in existing]
    report_ids = [
        report.id
        for report in session.query(GapReport.id).filter(GapReport.assessment_id.in_(assessment_ids)).all()
    ]

    if report_ids:
        session.query(GapItem).filter(GapItem.report_id.in_(report_ids)).delete(synchronize_session=False)
        session.query(Initiative).filter(Initiative.report_id.in_(report_ids)).delete(synchronize_session=False)
        session.query(GapReport).filter(GapReport.id.in_(report_ids)).delete(synchronize_session=False)

    session.query(RFIDocument).filter(RFIDocument.assessment_id.in_(assessment_ids)).delete(synchronize_session=False)
    session.query(DeskReviewFinding).filter(DeskReviewFinding.assessment_id.in_(assessment_ids)).delete(synchronize_session=False)
    session.query(DeskReviewSummary).filter(DeskReviewSummary.assessment_id.in_(assessment_ids)).delete(synchronize_session=False)
    session.query(QuestionnaireResponse).filter(QuestionnaireResponse.assessment_id.in_(assessment_ids)).delete(synchronize_session=False)
    session.query(AssessmentDocument).filter(AssessmentDocument.assessment_id.in_(assessment_ids)).delete(synchronize_session=False)
    session.query(Assessment).filter(Assessment.id.in_(assessment_ids)).delete(synchronize_session=False)


def insert_fixture(session, fixture: dict) -> dict:
    assessment_id = str(uuid.uuid4())
    assessment = Assessment(
        id=assessment_id,
        company_name=fixture["company_name"],
        industry=fixture["industry"],
        company_size=fixture["company_size"],
        description=fixture["description"],
        status="context_gathered",
        context_answers=json_dumps(fixture["context_answers"]),
        context_profile=json_dumps(fixture["context_profile"]),
        desk_review_status="completed",
    )
    session.add(assessment)
    session.flush()

    print(f"Creating assessment for {fixture['company_name']} ({assessment_id})")

    doc_id_by_key: dict[str, str] = {}
    catalog = []
    for doc in fixture["documents"]:
        document_id = str(uuid.uuid4())
        record = AssessmentDocument(
            id=document_id,
            assessment_id=assessment_id,
            filename=doc.filename,
            file_path=f"seeded/{assessment_id}/{doc.filename}",
            file_type=doc.file_type,
            document_category=doc.document_category,
            extracted_text=doc.text,
        )
        session.add(record)
        doc_id_by_key[doc.key] = document_id
        catalog.append({"filename": doc.filename, "type": doc.file_type, "pages": page_count(doc.text)})
        print(f"  Added document: {doc.filename} ({word_count(doc.text)} words)")

    for req_id in ALL_REQUIREMENT_IDS:
        response = fixture["responses"][req_id]
        session.add(
            QuestionnaireResponse(
                id=str(uuid.uuid4()),
                assessment_id=assessment_id,
                question_id=req_id,
                answer=response["answer"],
                notes=response.get("notes"),
                evidence_reference=response.get("evidence_reference"),
                na_reason=response.get("na_reason"),
                confidence=response.get("confidence"),
            )
        )

    session.add(
        DeskReviewSummary(
            assessment_id=assessment_id,
            document_catalog=json_dumps(catalog),
            coverage_summary=json_dumps(fixture["coverage"]),
            status="completed",
            started_at=NOW,
            completed_at=NOW,
        )
    )

    for finding in fixture["findings"]:
        session.add(
            DeskReviewFinding(
                assessment_id=assessment_id,
                finding_type=finding["finding_type"],
                requirement_id=finding["requirement_id"],
                document_id=doc_id_by_key.get(finding["document_key"]) if finding["document_key"] else None,
                content=finding["content"],
                severity=finding["severity"],
                source_quote=finding["source_quote"],
                source_location=finding["source_location"],
            )
        )
    print(f"  Added {len(ALL_REQUIREMENT_IDS)} questionnaire responses and {len(fixture['findings'])} desk review findings")

    return {
        "company_name": fixture["company_name"],
        "assessment_id": assessment_id,
        "hidden_gaps": fixture["hidden_gaps"],
    }


def write_manifest(entries: list[dict]) -> None:
    MANIFEST_PATH.write_text(json_dumps({"companies": entries}) + "\n", encoding="utf-8")
    print(f"Wrote manifest: {MANIFEST_PATH}")


def verify_counts(session, company_names: list[str]) -> None:
    assessments = session.query(Assessment).filter(Assessment.company_name.in_(company_names)).all()
    if len(assessments) != len(company_names):
        raise RuntimeError(f"Expected {len(company_names)} seeded assessments, found {len(assessments)}")

    assessment_ids = [assessment.id for assessment in assessments]
    response_count = session.query(QuestionnaireResponse).filter(QuestionnaireResponse.assessment_id.in_(assessment_ids)).count()
    summary_count = session.query(DeskReviewSummary).filter(DeskReviewSummary.assessment_id.in_(assessment_ids)).count()
    finding_count = session.query(DeskReviewFinding).filter(DeskReviewFinding.assessment_id.in_(assessment_ids)).count()
    doc_count = session.query(AssessmentDocument).filter(AssessmentDocument.assessment_id.in_(assessment_ids)).count()

    expected_responses = len(company_names) * len(ALL_REQUIREMENT_IDS)
    if response_count != expected_responses:
        raise RuntimeError(f"Expected {expected_responses} questionnaire responses, found {response_count}")
    if summary_count != len(company_names):
        raise RuntimeError(f"Expected {len(company_names)} desk review summaries, found {summary_count}")
    if doc_count != 13:
        raise RuntimeError(f"Expected 13 assessment documents, found {doc_count}")
    if finding_count < 30:
        raise RuntimeError(f"Expected at least 30 desk review findings, found {finding_count}")
    print(f"Verified counts: {len(assessments)} assessments, {doc_count} documents, {response_count} responses, {finding_count} findings")


def main() -> None:
    Base.metadata.create_all(bind=engine)
    fixtures = build_company_fixtures()
    for fixture in fixtures:
        validate_fixture(fixture)

    company_names = [fixture["company_name"] for fixture in fixtures]
    session = SessionLocal()
    try:
        print("Removing any existing seeded companies with matching names")
        purge_existing(session, company_names)
        session.flush()

        manifest_entries = []
        for fixture in fixtures:
            manifest_entries.append(insert_fixture(session, fixture))

        session.commit()
        write_manifest(manifest_entries)
        verify_counts(session, company_names)
        print("Seeding completed successfully.")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
