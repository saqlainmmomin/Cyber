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
        "NovaPay Solutions Pvt. Ltd. Privacy Policy",
        "Effective Date: 15 January 2025 | Version 4.2 | Public Website Copy",
        [
            (
                "1. Scope and Commitment",
                [
                    "NovaPay Solutions Pvt. Ltd. provides digital payment orchestration, merchant onboarding, wallet services, transaction monitoring, and customer support services to individuals and enterprise merchants. This Privacy Policy explains how personal data is collected, used, shared, stored, and otherwise processed when users access the NovaPay mobile application, merchant dashboard, API documentation portal, and customer support channels. We maintain a strong information security program aligned to ISO 27001 and regularly review our controls to support lawful and responsible processing of personal data.",
                    "By using our services, you consent to the collection and processing of your data as described in this policy. Users are presented with this Privacy Policy and the Terms of Service during account creation and must indicate acceptance before creating a wallet, linking a payment instrument, or completing merchant onboarding. The same acceptance covers continued use of card tokenization, fraud screening, merchant analytics, loyalty offers, customer support, and service improvement activities performed through the NovaPay platform.",
                    "This policy applies to personal data that we collect directly from users, receive from issuing banks and payment ecosystem participants, derive from transactional behavior, or generate through fraud monitoring and customer service interactions. Where applicable law requires us to keep records for compliance, investigation, or audit purposes, we may retain relevant information for those purposes while continuing to safeguard it through access restrictions and encryption.",
                ],
            ),
            (
                "2. Categories of Personal Data and Processing Purposes",
                [
                    "The categories of personal data we process include identity information such as name, date of birth, PAN, Aadhaar reference details where permitted, mobile number, email address, billing address, and account credentials; financial information such as bank account metadata, transaction references, settlement information, card token identifiers, and merchant payout details; and behavioral information such as payment frequency, device activity, location approximations inferred from login patterns, fraud risk indicators, and feature interaction metrics generated through use of our applications.",
                    "We use this information to verify identity, enable regulated payment services, detect and prevent fraud, maintain ledgers and audit trails, support merchants, improve onboarding conversion, personalize product education, perform analytics, send promotional communications, respond to legal requests, and maintain service quality. Our systems are designed to apply technical controls consistently across these activities so that user data can be handled through common operational workflows while preserving confidentiality and integrity.",
                    "Where multiple service features are provided through a unified customer journey, NovaPay may process the same personal data set for more than one business purpose. We maintain internal role-based access controls to reduce unnecessary access, but our operating model uses a single master customer profile so that fraud prevention, payment execution, support operations, product analytics, and promotional preference management can function from a common record without requiring the user to repeat the onboarding journey for each separate service feature.",
                ],
            ),
            (
                "3. Consent, User Controls, and Communications",
                [
                    "We obtain consent from all users during the account registration process. Users are presented with our Privacy Policy and Terms of Service and must indicate their acceptance before proceeding. This acceptance authorizes NovaPay to collect, store, analyze, use, and share personal data for payment processing, merchant risk review, customer support, product analytics, fraud detection, service communications, and promotional outreach as described in this policy.",
                    "Where users no longer wish to receive promotional emails, they may use the unsubscribe link included in such messages or update communication preferences in the profile section of the application. Certain operational messages, service alerts, fraud notifications, and account security messages will continue to be sent because they are integral to use of the platform. Use of our services after notice updates or continued interaction with the NovaPay application constitutes acceptance of our data processing practices.",
                    "NovaPay may maintain records evidencing that a user accepted the onboarding journey, including the acceptance timestamp, device identifier, IP address, and version of the policy in force at the time of sign-up. We do not currently operate a separate consent manager. Instead, user permissions are administered through the account experience, transactional workflows, and communications preferences embedded in the product.",
                ],
            ),
            (
                "4. Data Sharing, Service Providers, and International Processing",
                [
                    "NovaPay uses specialized service providers to host infrastructure, process payments, detect fraud, send customer communications, and support analytics. These providers may process data on our behalf under contractual arrangements or platform terms designed to support confidentiality, availability, and resilience. Access is limited to the information reasonably required for service delivery, troubleshooting, reconciliation, customer engagement, and lawful request handling.",
                    "Your data may be transferred to and processed in countries other than India where our service providers operate. For example, infrastructure and disaster recovery environments may operate from regional hosting locations selected to support performance and continuity, and payment ecosystem participants may process transactional records where their operational systems are located. When we use such providers, we expect them to maintain commercially reasonable security safeguards and service continuity practices appropriate to the nature of the services performed.",
                    "We may also disclose information to banking partners, card networks, payment aggregators, auditors, legal advisers, and regulators where necessary to deliver our services, investigate suspicious activity, satisfy statutory requirements, or defend legal claims. Internal teams may review aggregated and user-level datasets to assess new features, reduce payment failures, and improve lifecycle engagement. These activities are managed under enterprise security controls and internal approval workflows.",
                ],
            ),
            (
                "5. Retention, Security, and Contact",
                [
                    "NovaPay retains personal data as required to operate our services, manage disputes, satisfy applicable regulatory requirements, support fraud monitoring, and preserve records relevant to contractual and legal obligations. Because payment operations are heavily regulated, retention decisions may vary by workflow and business context. Certain data sets may therefore remain stored for longer periods where operational, legal, investigative, or audit considerations continue to apply.",
                    "We implement technical and organizational safeguards including encryption in transit, encryption at rest for regulated environments, least-privilege access management, audit logging, secure software development practices, vendor reviews, vulnerability management, and incident response procedures. Our security team oversees these controls as part of the broader information security management system, and selected controls are subject to independent attestation as part of our external assurance program.",
                    "Questions about this policy may be addressed to privacy@novapay.in. Operational security incidents should be escalated through our customer support team or the published security reporting channel. Additional terms governing the use of NovaPay services are available in the Terms of Service and related merchant documentation.",
                ],
            ),
        ],
    )
    terms = build_document(
        "NovaPay Consumer Terms of Service",
        "Version 6.0 | Applicable to wallet users and checkout customers",
        [
            (
                "1. Account Acceptance and Eligibility",
                [
                    "These Terms of Service govern the use of NovaPay payment services, including digital wallet activation, merchant checkout, saved payment methods, customer support, reward features, and promotional programs. A user must review the Privacy Policy and these Terms before opening an account. By clicking the acceptance checkbox and continuing to use the service, the user agrees to the contract framework that enables NovaPay to provide regulated payment processing and related account support.",
                    "Use of our payment services constitutes acceptance of our data processing practices. The service depends on identity verification, fraud screening, transaction pattern review, support logging, and platform analytics carried out as part of a unified operational model. Users who do not accept this framework should not create an account or submit payment instructions through NovaPay. Once accepted, these terms remain in force until the account is closed and all outstanding regulatory, settlement, or dispute obligations have been addressed.",
                    "NovaPay may amend these Terms from time to time to reflect changes in regulation, service features, partner requirements, or operational processes. Continued use of the platform after such changes constitutes acceptance of the updated terms unless a mandatory legal right requires a different process. Users are responsible for reviewing notice banners, in-product messages, and the updated legal documentation made available through the application and website.",
                ],
            ),
            (
                "2. Communications and Promotions",
                [
                    "NovaPay may send transactional confirmations, service updates, fraud alerts, product education, surveys, and promotional communications through email, SMS, WhatsApp, push notifications, and in-app messages. These communications support the secure operation of the service, help users understand new features, and allow NovaPay to inform users about offers that may be relevant to their transaction profile and product usage.",
                    "You may opt out of promotional communications at any time by using the unsubscribe link provided in email communications or by changing the relevant communication toggle in the application settings. Opting out of promotional communications does not prevent NovaPay from processing information for analytics, fraud prevention, service measurement, or account support, because those activities are necessary to maintain and improve the payment experience delivered through the platform.",
                    "NovaPay may determine eligibility for cashback programs, onboarding nudges, merchant offers, and product campaigns through internal models that consider account activity, engagement history, device behavior, and transactional signals. The availability of such programs is discretionary and may change without notice. Service functionality is not separated into distinct legal modules for each communication or analytics purpose; rather, customer data is maintained within an integrated platform environment governed by these Terms and the Privacy Policy.",
                ],
            ),
            (
                "3. Operational Matters",
                [
                    "Users are responsible for keeping account credentials secure, maintaining current contact information, and promptly reporting unauthorized transactions, suspicious notifications, device loss, or suspected compromise. NovaPay may suspend transactions, temporarily restrict accounts, or request additional verification where activity suggests fraud risk, legal non-compliance, or unusual usage patterns that require review before services continue.",
                    "Disputes, refunds, chargebacks, failed payment investigations, and settlement exceptions are managed in accordance with partner network rules, applicable law, and NovaPay internal procedures. Relevant records may be retained for audit, fraud investigation, or evidentiary purposes while such matters remain open or where applicable requirements continue to apply. Users acknowledge that service availability depends on third-party banking, card network, and cloud infrastructure partners.",
                    "Nothing in these Terms limits NovaPay's ability to take actions reasonably required to satisfy legal obligations, maintain information security, or protect the integrity of the service. NovaPay may assign or delegate operational responsibilities to affiliated entities or service providers provided appropriate safeguards are maintained for continuity, confidentiality, and service reliability.",
                ],
            ),
        ],
    )
    retention = build_document(
        "NovaPay Data Retention and Archival Standard",
        "Document Owner: CISO Office | Last Review: 31 December 2024",
        [
            (
                "1. Purpose",
                [
                    "This standard establishes the principles used by NovaPay Solutions Pvt. Ltd. to retain, archive, and eventually dispose of information assets created or received in the course of payment operations, customer support, fraud management, legal compliance, finance, and product development. The standard is intended to support consistency across systems while recognizing that regulatory and contractual obligations may require records to remain available beyond the business process that first created them.",
                    "Personal data and business records are retained as per applicable regulatory requirements, contractual commitments, litigation hold obligations, and business continuity considerations. Control owners are expected to avoid deleting information where retention may be necessary to satisfy audit requests, regulatory inspections, dispute investigation, law enforcement requests, reconciliation processes, or internal assurance reviews. Where doubt exists, the longer retention period should be applied until Legal or Compliance provides direction.",
                    "The standard applies to application databases, data warehouses, log repositories, support tooling, payment partner exports, analytics environments, and archived backups. It does not prescribe system-specific retention schedules. Instead, product and functional owners remain responsible for aligning their data sets to the relevant legal and business context in consultation with Compliance, Finance, and Information Security.",
                ],
            ),
            (
                "2. Retention Administration",
                [
                    "Business owners must classify data according to the process it supports and retain it for as long as the related purpose, legal basis, or regulatory expectation remains relevant. Financial transaction records, KYC artifacts, customer communications, merchant onboarding files, fraud investigation materials, and operational logs may all be retained for different reasons. In practice, retention decisions should err on the side of preservation where a future request from a regulator, banking partner, or auditor is reasonably foreseeable.",
                    "NovaPay maintains archival storage to preserve records in the event of investigations, dispute resolution, forensic review, quality assurance, or external examination. Archival transfers are handled through operational runbooks maintained by the platform and infrastructure teams. Where deletion is proposed, the requesting team must confirm that no active purpose, regulatory expectation, or legal hold continues to apply to the relevant information set.",
                    "Backups, snapshots, disaster recovery copies, and system logs may continue to contain historical records even after business users no longer actively rely on them. Such repositories remain subject to security controls and are retained according to infrastructure practices designed to support service restoration and evidentiary integrity. Requests for deletion from archived environments should be escalated to the CISO office for case-by-case review.",
                ],
            ),
            (
                "3. Governance and Exceptions",
                [
                    "Compliance, Finance, Security, and Legal may issue interpretive guidance for specific workflows where they believe a regulatory requirement should control retention. Business units must preserve supporting justification for any deletion event undertaken in a regulated system or customer-impacting process. Exceptions to this standard require approval from the CISO and the relevant business owner and must be documented in the policy exception register.",
                    "This standard should be read together with the information classification policy, backup policy, incident response procedure, and records management guidance. Teams should avoid creating separate local deletion rules without approval because inconsistent practices can create evidentiary gaps. Questions regarding the application of this standard should be addressed to the CISO office or the Compliance function.",
                    "The standard will be reviewed annually or earlier if there is a material regulatory development, product expansion, or audit observation affecting information lifecycle management. Operational teams are expected to comply with the intent of this standard even where a detailed retention schedule for a specific dataset has not yet been finalized.",
                ],
            ),
        ],
    )
    incident_response = build_document(
        "NovaPay Security Incident Response Standard Operating Procedure",
        "Information Security Management System Controlled Document | Version 3.1",
        [
            (
                "1. Objective and Scope",
                [
                    "The purpose of this standard operating procedure is to define how NovaPay detects, escalates, investigates, contains, eradicates, and recovers from information security incidents affecting production systems, corporate endpoints, cloud infrastructure, or third-party service dependencies. The procedure supports the ISO 27001 control environment and aligns internal escalation practices across Security Operations, Engineering, Infrastructure, and Corporate IT.",
                    "Security incidents include malware infection, credential compromise, denial-of-service events, unauthorized administrative access, service outage, suspicious network traffic, data exfiltration indicators, cloud configuration drift, ransomware events, and third-party service disruption with operational impact. Any employee or contractor who suspects a security incident must notify the CISO or the Security Operations mailbox immediately so the response process can begin without delay.",
                    "This procedure is focused on operational incident handling. Crisis communications, external legal notifications, customer messaging, and regulator-specific obligations are handled separately as needed under executive direction. The procedure therefore emphasizes quick triage, ownership assignment, technical evidence preservation, and restoration of normal services after containment and remediation work is completed.",
                ],
            ),
            (
                "2. Response Lifecycle",
                [
                    "On receiving an alert, Security Operations classifies the incident by severity, affected systems, and likely business impact. The incident commander opens an incident record, assigns response owners, and determines whether production change freezes, partner notifications, or additional monitoring actions are needed. Initial containment priorities include isolating compromised hosts, revoking credentials, restricting suspicious network paths, and preserving volatile evidence where feasible.",
                    "Engineering and infrastructure teams investigate the root cause, identify the attack path or failure mode, validate the scope of affected systems, and develop containment and eradication plans. Recovery actions may include patch deployment, service restoration, credential resets, infrastructure rebuilds, backup recovery, or partner coordination. Throughout the incident, response teams document timeline events, technical indicators, decisions taken, and remediation steps in the central incident tracker.",
                    "If the event affects customer-facing services, the incident commander may request support from Product, Customer Success, Merchant Operations, and Communications to prepare service updates or respond to inbound queries. The primary objective remains restoration of secure operations, minimization of downtime, and capture of lessons learned for future prevention. Post-incident reviews are expected for all high-severity incidents and for any event with recurring control failures.",
                ],
            ),
            (
                "3. Escalation, Reporting, and Closure",
                [
                    "All confirmed or suspected incidents must be escalated to the CISO, Security Operations lead, and the relevant engineering owner. High-severity incidents must also be brought to the attention of the Chief Technology Officer and the head of infrastructure. Incident teams should notify the CISO and IT team as soon as practical when a material event is identified, and the CISO may convene an executive review call if sustained customer impact, media attention, or broad platform risk is anticipated.",
                    "Closure requires confirmation that the threat has been contained, affected systems have been restored, remediation tasks have been logged, and evidence has been retained for future forensic or audit review. The incident commander is responsible for ensuring that the final incident report includes a timeline, root cause summary, affected services, corrective actions, and identified preventive improvements. Lessons learned must be communicated to relevant technical stakeholders.",
                    "This document is reviewed annually under the information security management system. Questions regarding application of the SOP should be directed to the CISO office. Exceptions to response sequencing may be approved by the incident commander where necessary to protect platform availability, preserve forensic evidence, or manage an urgent operational threat.",
                ],
            ),
        ],
    )
    vendor_matrix = build_document(
        "NovaPay Third-Party Services Register",
        "Internal Governance Note | Shared with procurement and security reviewers",
        [
            (
                "1. Register Overview",
                [
                    "NovaPay maintains a central register of key vendors used to host applications, process transactions, support merchant onboarding, and deliver customer communications. The register is intended to provide an operational snapshot for procurement and security review rather than a legal inventory of every data flow. Additional implementation details may reside in technical tickets, architecture diagrams, or business owner notes for individual service integrations.",
                    "Current core providers include Amazon Web Services for primary cloud hosting, Stripe for selected payment processing and settlement support, Atlassian for issue tracking, Slack for internal communications, and several specialist tools used by product, growth, and customer support teams. Security due diligence is performed before onboarding material vendors, and renewals are coordinated through procurement workflows where applicable.",
                    "The register is reviewed quarterly for spend, availability, and security posture. Business owners are expected to notify procurement when a new service is onboarded or materially expanded. Teams may trial low-risk tools before formal register updates are completed provided those tools are used in accordance with internal security and acceptable use policies.",
                ],
            ),
            (
                "2. Contracting and Security Expectations",
                [
                    "Vendors handling customer or merchant information are expected to maintain reasonable security measures, follow lawful instructions, and support service continuity. NovaPay typically relies on vendor master terms, cloud platform terms, or standard service schedules where those documents are commercially reasonable and broadly accepted in the market. Additional contract negotiation may occur for higher-risk relationships or strategic partners.",
                    "Security review criteria include hosting architecture, identity controls, encryption posture, logging, incident history, penetration testing, business continuity, and sub-processor transparency where available. Procurement files may contain certification reports, questionnaire responses, and security summaries, but the central register itself is not intended to reproduce the full contractual record or all country-level processing details for each provider.",
                    "Questions regarding vendor ownership, contracting status, or security review history should be addressed to Procurement, Information Security, or the relevant business owner. This note is informational and may not reflect every operational integration point present in the current production environment.",
                ],
            ),
        ],
    )
    return [
        SeedDocument("privacy", "Privacy-Policy-NovaPay-2025.pdf", "pdf", "privacy_policy", privacy_policy),
        SeedDocument("terms", "NovaPay-Terms-of-Service-2025.pdf", "pdf", "consent_form", terms),
        SeedDocument("retention", "NovaPay-Data-Retention-Standard.docx", "docx", "retention_policy", retention),
        SeedDocument("ir", "NovaPay-Incident-Response-SOP.docx", "docx", "breach_response_plan", incident_response),
        SeedDocument("vendors", "NovaPay-Third-Party-Services-Register.docx", "docx", "data_processing_agreement", vendor_matrix),
    ]


def build_healthbridge_documents() -> list[SeedDocument]:
    privacy_policy = build_document(
        "HealthBridge Analytics Privacy Policy",
        "Website Policy | Last Updated: 11 February 2025",
        [
            (
                "1. Introduction",
                [
                    "HealthBridge Analytics provides patient engagement analytics, care pathway reporting, billing support workflows, and hospital-facing dashboards for partner healthcare institutions. This Privacy Policy describes how information is collected, used, disclosed, and retained when individuals interact with our websites, support channels, hospital partner interfaces, and digital tools made available through our services. We are committed to protecting personal information and have adopted measures intended to align with applicable privacy laws and industry expectations.",
                    "This Privacy Policy applies to visitors, users, customers, prospective customers, and, where applicable, EU data subjects whose information may be processed by us or by our service providers. Where required by GDPR, the California Consumer Privacy Act, or other applicable privacy laws, we will take reasonable steps to ensure that information is handled in accordance with lawful processing obligations and contractual commitments agreed with our customers and vendors.",
                    "HealthBridge may collect information directly from you, from devices you use to access our services, or from business partners who use our analytics solutions. We encourage users to review this policy carefully because it explains the categories of data collected, the reasons we use such data, and the ways in which users may contact us about privacy-related matters.",
                ],
            ),
            (
                "2. Information We Collect and Why We Use It",
                [
                    "We may collect contact information such as name, email address, mobile number, account credentials, job title, organization name, and user-submitted support requests. We may also collect information regarding device identifiers, browser information, and usage metrics that help us improve our websites and applications. We use this information to provide our services, communicate with you, troubleshoot issues, improve our services, manage customer relationships, and send updates relating to our offerings.",
                    "Where our hospital partners use our analytics services, information may be made available to us through integrated workflows so that authorized users can review reporting dashboards, billing support indicators, operational trends, and performance insights. We process such information on behalf of our partners to support service delivery, platform administration, quality improvement, and product maintenance. We may also use aggregated or de-identified information to analyze platform performance and improve our services.",
                    "We may share information with service providers who help us host infrastructure, deliver communications, maintain databases, process invoices, and support customer relationships. Such providers are expected to use information only for the purposes for which they have been engaged and to maintain appropriate safeguards. We may also disclose information where required by law, regulation, court order, or lawful request of a competent authority.",
                ],
            ),
            (
                "3. Children's Privacy",
                [
                    "We do not knowingly collect data from children under 13 through our website or general marketing channels. If we discover that we have collected data from a child under 13 without appropriate consent, we will take steps to delete that information from our records as soon as reasonably practicable. Parents or guardians who believe that a child under 13 has provided personal information to us may contact us using the contact details below.",
                    "Some of our customers may provide services to minors through hospitals, clinics, and other healthcare settings. In those cases, the customer or relevant healthcare institution is responsible for determining the legal basis for collection and use of the information and for obtaining any notices or consents required under applicable law. HealthBridge acts in accordance with contractual instructions received from such partner organizations.",
                    "We do not design our public website to target children, and we ask that children under 13 not submit information directly through the website. Questions about children's information may be directed to privacy@healthbridge.in for review by the team handling privacy requests.",
                ],
            ),
            (
                "4. Data Rights, Retention, and Contact",
                [
                    "If you would like to access, correct, update, delete, or otherwise inquire about your personal data, you may contact us at privacy@healthbridge.in and we will review your request. We will respond as appropriate and in accordance with applicable law. Additional identity verification may be required before we can act on certain requests.",
                    "We retain information for as long as necessary to provide our services, comply with legal obligations, resolve disputes, and enforce our agreements. Retention periods may vary depending on the nature of the data and the services involved. We maintain reasonable administrative, technical, and physical safeguards designed to protect information against unauthorized access, loss, misuse, or alteration.",
                    "This policy may be updated from time to time. When material changes are made, the updated version will be posted on our website. Continued use of our services after the effective date of the updated policy constitutes acknowledgement of the revised policy, to the extent permitted by law.",
                ],
            ),
        ],
    )
    board_resolution = build_document(
        "HealthBridge Board Resolution on Data Protection Governance",
        "Extract from Board Meeting Minutes dated 22 January 2025",
        [
            (
                "Resolution Background",
                [
                    "The Board of Directors reviewed investor diligence requests concerning privacy governance, cybersecurity maturity, and readiness for the Digital Personal Data Protection Act. The management team noted that the company remains in an early stage of operational maturity and should therefore adopt pragmatic oversight arrangements that leverage existing leadership roles while minimizing administrative overhead for the business.",
                    "After discussion, the Board determined that privacy oversight should remain centrally coordinated by executive leadership so that operational decisions, commercial priorities, and compliance activities can be aligned. The Board expressed the view that a separate privacy office is not currently required given the size of the company and the fact that patient data is generally made available through hospital partners rather than collected directly from individuals through a broad consumer-facing channel.",
                    "Directors also noted that the company already maintains a secure engineering process, uses reputable cloud vendors, and is preparing standard documentation to support enterprise sales conversations. The Board emphasized that management should continue developing privacy documentation proportionate to the company's current stage of growth.",
                ],
            ),
            (
                "Resolved Matters",
                [
                    "RESOLVED that Arjun Mehta, in his capacity as Chief Executive Officer, shall also discharge the functions of Data Protection Officer as required under applicable law and shall remain the point of escalation for privacy-related questions, user communications, and investor diligence requests until the Board determines that a separate appointment is necessary.",
                    "RESOLVED FURTHER that management is authorized to continue refining privacy policies, vendor documentation, and customer-facing notices in consultation with external counsel as needed, provided that no dedicated data protection headcount is added without prior budget approval from the Board.",
                    "RESOLVED FURTHER that investor updates concerning privacy and security readiness may be coordinated through the Chief Executive Officer together with the Chief Technology Officer and the Head of Customer Success, as appropriate for the subject matter under review.",
                ],
            ),
            (
                "Administrative Note",
                [
                    "The Company Secretary shall maintain this resolution with the corporate records and circulate relevant extracts to management teams upon request. Questions regarding implementation should be directed to the office of the Chief Executive Officer. No further standing committee or reporting cadence is established by this resolution at this time.",
                    "This extract is intended to capture the operative board decision and does not constitute a separate policy manual or role charter. Any future expansion of governance processes may be documented in follow-on board materials, investor reports, or management operating procedures as the company scales.",
                ],
            ),
        ],
    )
    msa = build_document(
        "HealthBridge Master Services Agreement Template",
        "Standard Form used with service providers and implementation partners",
        [
            (
                "1. Commercial Terms",
                [
                    "This Master Services Agreement governs the provision of services by the Service Provider to HealthBridge Analytics Private Limited. The parties may enter into statements of work, order forms, or schedules that reference this agreement for specific services such as software development, quality assurance, implementation support, data annotation, or technical consulting. Fees, payment milestones, acceptance terms, and service levels will be set out in the applicable ordering document.",
                    "Each party will perform its obligations in a professional and workmanlike manner. The Service Provider will ensure that personnel assigned to the services are suitably skilled and qualified, and HealthBridge will provide timely access to information, systems, and stakeholders reasonably required to enable delivery. Delays caused by dependency failures, customer unavailability, or force majeure will be handled through the change control process described in the relevant statement of work.",
                    "Intellectual property created specifically for HealthBridge under a paid statement of work will vest in HealthBridge upon full payment of undisputed fees unless otherwise stated in the statement of work. Pre-existing materials, methodologies, tools, and know-how of the Service Provider remain the property of the Service Provider, subject to any license expressly granted in the ordering document.",
                ],
            ),
            (
                "2. Confidentiality and Security",
                [
                    "Each party shall protect the confidential information of the other using at least the same degree of care it uses to protect its own confidential information of a similar nature, and in no event less than reasonable care. Confidential information may be used solely for the performance of this agreement and may be disclosed only to personnel and subcontractors who have a need to know and are bound by confidentiality obligations no less protective than those contained herein.",
                    "Service Provider shall implement reasonable security measures to protect Client data. The parties acknowledge that the nature and extent of such measures may vary based on the services being performed, the systems involved, and standard industry practices followed by the Service Provider. Upon reasonable request, the Service Provider may provide a summary of its security practices or certifications where available.",
                    "Neither party will make public statements about the other without prior written consent except as required by law. Additional confidentiality terms, if any, may be included in a statement of work or non-disclosure agreement executed between the parties.",
                ],
            ),
            (
                "3. Liability and General Terms",
                [
                    "Except for payment obligations and breaches of confidentiality, each party's aggregate liability under this agreement will not exceed the fees paid or payable under the relevant statement of work during the twelve months preceding the event giving rise to the claim. Neither party shall be liable for indirect, incidental, special, punitive, or consequential damages including loss of profits, revenue, or anticipated savings.",
                    "This agreement may be terminated for material breach not cured within thirty days after written notice. On termination, each party will return or destroy the other party's confidential information upon request, subject to legal retention requirements and routine backup processes. Sections that by their nature should survive termination will remain in effect after termination.",
                    "This agreement is governed by the laws of Karnataka and the courts of Bengaluru shall have exclusive jurisdiction. The template may be updated by HealthBridge from time to time to reflect commercial needs, operational experience, or legal advice.",
                ],
            ),
        ],
    )
    partner_addendum = build_document(
        "HealthBridge Hospital Partner Integration Addendum",
        "Operational Annex used alongside hospital master agreements",
        [
            (
                "1. Integration Scope",
                [
                    "This addendum describes the operational interfaces used when a hospital, clinic, or healthcare network enables HealthBridge analytics modules in connection with patient engagement, care coordination, billing support, or clinical operations reporting. The partner institution remains responsible for primary collection of patient information and for configuring the upstream systems from which records are shared for analytics and workflow support.",
                    "HealthBridge may receive patient registration information, visit metadata, doctor identifiers, billing indicators, utilization events, and other operational information needed to provide dashboards, alerts, and reports requested by the partner institution. The transfer method may include secure APIs, managed file transfer, cloud database synchronization, or other mutually agreed integration methods documented during implementation.",
                    "Implementation teams from both parties will coordinate test environments, field mapping, issue triage, and cutover planning. Questions regarding source data quality, notice language, and patient communication workflows should be raised by the partner institution with its internal legal and compliance teams before the production launch date.",
                ],
            ),
            (
                "2. Responsibilities",
                [
                    "Partner hospitals are responsible for obtaining all necessary consents, authorizations, notices, and approvals required for the collection, use, and disclosure of patient information made available to HealthBridge through the services. The partner institution represents that it has a lawful basis to share such information with HealthBridge and that its privacy notices and patient-facing materials are sufficient for the services selected.",
                    "HealthBridge will process information in accordance with the instructions of the partner institution as reflected in the agreement, implementation documents, and support communications. HealthBridge may use subcontractors or infrastructure providers to host and support the platform, provided that such arrangements are consistent with internal security practices and standard vendor management procedures.",
                    "Where a patient, guardian, or third party raises a question regarding consents, notice, or patient authorization, the partner institution will remain the primary point of contact unless otherwise agreed in writing. HealthBridge will reasonably assist with information needed for the partner institution to evaluate such inquiries.",
                ],
            ),
            (
                "3. Security and Support",
                [
                    "Both parties will maintain commercially reasonable safeguards appropriate to the nature of the services. HealthBridge maintains application logging, access controls, encryption for supported environments, and support workflows intended to preserve service continuity. Each party will notify the other of material incidents affecting the services in accordance with the main agreement.",
                    "This addendum is intended to supplement the commercial agreement and implementation records. It does not create a separate regulatory framework beyond the obligations already assumed in the main contract. Any conflicting terms will be resolved in accordance with the hierarchy set out in the master agreement between the parties.",
                ],
            ),
        ],
    )
    return [
        SeedDocument("privacy", "HealthBridge-Privacy-Policy-2025.pdf", "pdf", "privacy_policy", privacy_policy),
        SeedDocument("board", "HealthBridge-Board-Resolution-DPO.docx", "docx", "internal_sop", board_resolution),
        SeedDocument("msa", "HealthBridge-MSA-Template.docx", "docx", "data_processing_agreement", msa),
        SeedDocument("partner", "HealthBridge-Hospital-Partner-Addendum.docx", "docx", "internal_sop", partner_addendum),
    ]


def build_dakshin_documents() -> list[SeedDocument]:
    public_notice = build_document(
        "Dakshin Logistics Group Privacy Notice",
        "Corporate Website Notice | Last Updated: 19 December 2024",
        [
            (
                "1. About This Notice",
                [
                    "Dakshin Logistics Group operates freight, warehousing, route management, fulfillment, fleet coordination, and supply chain support services across India and selected overseas markets. This Privacy Notice explains how we process personal data relating to customers, vendor contacts, website users, job applicants, and other individuals who interact with our business. We are committed to handling personal data responsibly and have developed governance processes informed by industry standards and prior international privacy workstreams.",
                    "The notice applies to data collected through customer contracts, warehouse operations, fleet platforms, vendor onboarding, service portals, support channels, and our corporate website. Depending on the business relationship involved, specific operational teams may collect identity, contact, payment, route, location, service performance, and compliance-related information required to provide transport and logistics services or to administer employment and contractor relationships.",
                    "We review this notice periodically to reflect changes in law, business operations, partner arrangements, and technology. Updates are posted on our website and become effective from the date listed above. Individuals are encouraged to review the notice from time to time to understand how Dakshin Logistics Group handles personal data across its operations.",
                ],
            ),
            (
                "2. How We Use Personal Data",
                [
                    "We use personal data to deliver logistics services, coordinate pickups and deliveries, manage warehouse operations, verify identity, administer contracts, process payments, maintain safety and compliance controls, investigate incidents, optimize routes, respond to grievances, and monitor service-level commitments. Depending on the context, data may also be used for analytics, training, fraud prevention, audit support, legal compliance, and internal management reporting.",
                    "Personal data may be shared with customers, transport partners, warehouse operators, payment providers, technology vendors, insurers, regulators, auditors, and affiliated entities where necessary for legitimate business operations and lawful compliance purposes. Access to personal data is governed by role-based controls and internal confidentiality requirements. Where cross-border operations are involved, relevant corporate teams coordinate the applicable transfer controls and documentation.",
                    "Certain operational records are retained for periods necessary to satisfy contractual, legal, safety, evidentiary, and audit requirements. Retention periods vary depending on the nature of the data and the processing activity involved. We maintain reasonable technical and organizational safeguards designed to protect information and to support accountability across our processing environment.",
                ],
            ),
            (
                "3. Rights and Contact Details",
                [
                    "Individuals may contact Dakshin Logistics Group to seek access to personal data summaries, request correction of inaccuracies, ask for erasure where applicable, or raise grievances about the way information has been handled. Requests may be reviewed for identity verification, applicable exemptions, and operational feasibility before a response is provided. We may need to retain some data where continued processing is required by law or for ongoing contractual and dispute management purposes.",
                    "Questions relating to this notice may be sent to dpo@dakshinlogistics.com. Additional guidance may also be available through the privacy portal referenced in our grievance procedure. Where a request remains unresolved, the individual may be informed of available escalation channels in accordance with applicable law and internal policy.",
                    "This notice is informational and should be read together with role-specific notices, employee communications, contractual terms, and operational procedures that apply in a particular context. Those documents may provide more specific information for the relevant business relationship or service activity.",
                ],
            ),
        ],
    )
    employee_notice = build_document(
        "Dakshin Logistics Group Employment Data Processing Notice",
        "Applies to employees, drivers, and warehouse associates",
        [
            (
                "1. Purpose of This Notice",
                [
                    "This notice explains how Dakshin Logistics Group collects and processes personal data relating to employees, contract drivers, and warehouse workers during recruitment, onboarding, employment administration, route management, safety monitoring, payroll, disciplinary processes, and performance management. The notice is intended to support transparency while ensuring that the business can maintain secure, efficient, and accountable logistics operations across a distributed workforce.",
                    "As a condition of your employment, you acknowledge and consent to the collection and processing of your personal data as described herein, including real-time location tracking for route optimization and performance evaluation. The operational needs of the business require integrated use of workforce identity information, compliance records, attendance details, route execution data, proof-of-delivery data, safety events, and related operational metrics. These processes are integral to your role and to the services Dakshin provides to its customers.",
                    "By signing the onboarding documents and continuing in employment, personnel confirm that they understand the categories of information processed, the organizational purposes described, and the expectation that such data may be used across workforce administration, route oversight, customer service, safety, and performance management processes. Where the company uses affiliated entities or service providers to support these processes, such parties may receive relevant information for authorized business purposes.",
                ],
            ),
            (
                "2. Categories of Data and Uses",
                [
                    "The company may collect identification details, contact information, government identifiers, banking information, device identifiers, route assignments, attendance records, telematics, real-time location data, incident reports, training records, customer feedback, and supervisor evaluations. We use this information to assign work, administer compensation, manage statutory obligations, maintain vehicle and route safety, respond to customer escalations, investigate incidents, and assess performance against service expectations.",
                    "Location and telematics information may be reviewed by dispatch managers, fleet managers, security personnel, compliance teams, and supervisors responsible for safety and route optimization. Workforce performance evaluation may consider route adherence, delivery timing, proof-of-delivery quality, incident frequency, fuel usage, and related service metrics. The company may also use aggregated analytics to improve route planning and resource allocation across the network.",
                    "Operational records may be retained for periods necessary to support legal compliance, customer requirements, audit readiness, safety investigations, insurance claims, dispute resolution, and management reporting. Additional details may be available in related policies, platform guidance, and training materials communicated separately to relevant personnel.",
                ],
            ),
            (
                "3. Questions and Support",
                [
                    "Questions regarding this notice may be directed to Human Resources or to the Data Protection Officer through the corporate channels published on the company intranet and external website. Employees are expected to comply with related policies, mobile device requirements, and route management procedures issued by the company from time to time.",
                    "This notice does not alter the at-will or contractual nature of the employment relationship where applicable, nor does it limit the company's ability to process information necessary to administer employment, comply with law, or protect the safety and integrity of logistics operations. The company may update this notice periodically to reflect operational or legal developments.",
                ],
            ),
        ],
    )
    gps_policy = build_document(
        "Dakshin Fleet GPS Tracking and Route Assurance Policy",
        "Fleet Operations Manual | Version 2.7",
        [
            (
                "1. Policy Objective",
                [
                    "Dakshin Logistics Group deploys mobile and vehicle-based GPS capability to support route management, shipment visibility, driver safety, theft prevention, customer service, proof-of-service verification, and compliance with service-level commitments. The policy establishes a standardized approach for collecting location data from drivers and fleet assets so that dispatch teams and operations leaders can coordinate real-time logistics execution at scale.",
                    "Location data is collected to ensure delivery efficiency, driver safety, and compliance with service-level agreements. The GPS environment integrates with route planning tools, dispatch consoles, incident workflows, and customer escalation channels. Authorized operations personnel may view live location feeds, route deviations, dwell times, and event history in order to coordinate work and resolve delivery issues efficiently.",
                    "Continuous tracking during active duty hours is expected as part of routine fleet operations, and location telemetry is preserved in operational systems to support post-incident review, customer dispute handling, insurance matters, and quality analysis. The business uses a common tracking configuration across most mobile devices to reduce administrative complexity and to maintain a uniform operational standard across regions and business units.",
                ],
            ),
            (
                "2. Collection and Retention",
                [
                    "The fleet application may collect GPS coordinates, timestamped route events, device identifiers, mileage, idle time, driving events, and related telematics records at intervals configured by the fleet technology team. Location data is retained for a period of 36 months for operational and legal purposes, including service verification, dispute resolution, insurance handling, safety inquiries, and trend analysis intended to improve route planning and workforce performance.",
                    "Dispatch supervisors, regional fleet managers, security teams, selected customer service managers, and authorized technology personnel may access location data where necessary to perform their roles. Access is governed through system permissions and internal management approvals. Reports generated from the GPS platform may be shared with customers, insurers, internal audit, and senior management where relevant to service performance or incident review.",
                    "Operational teams are expected to use location information responsibly and only for authorized business purposes. Questions about system settings, device functionality, and regional implementation should be raised with the fleet technology team or the regional operations head. Any exceptions to the standard tracking configuration require approval from central fleet operations.",
                ],
            ),
            (
                "3. Governance",
                [
                    "Fleet operations, the Data Protection Officer, Information Security, and Human Resources may review this policy periodically to ensure that it remains aligned with the needs of the business and with evolving customer, legal, and safety expectations. Additional guidance may be issued through training notes, control room instructions, or platform release documentation.",
                    "This policy should be read together with the employment data processing notice, mobile device policy, disciplinary standards, and route compliance guidance. Nothing in this policy limits Dakshin's ability to take immediate action where tracking data indicates a safety concern, operational failure, suspected misconduct, or customer-impacting service issue that requires prompt escalation.",
                ],
            ),
        ],
    )
    grievance = build_document(
        "Dakshin Data Protection Grievance Procedure",
        "Enterprise Privacy Procedure | Approved by General Counsel",
        [
            (
                "1. Filing a Grievance",
                [
                    "Dakshin Logistics Group provides a process for data principals to raise concerns regarding access, correction, erasure, misuse of personal data, notice concerns, or other privacy-related matters. Data principals may submit grievances through the DPO portal at privacy.dakshinlogistics.com or by emailing dpo@dakshinlogistics.com. The portal is the preferred channel because it captures structured information needed for validation, routing, and timely response.",
                    "Submitted grievances should include the name of the requester, contact details, relationship to Dakshin, a description of the issue, and any supporting information necessary for the company to review the matter. The privacy team may request additional details or proof of identity before taking action. Requests received through other business channels may be redirected to the DPO portal so that they can be tracked centrally and handled consistently.",
                    "The procedure applies to customers, vendor contacts, website users, and other individuals whose personal data is processed by Dakshin. Business teams receiving a privacy-related complaint should direct the individual to the published privacy channels and avoid making commitments on outcome or timing before the privacy team has reviewed the matter.",
                ],
            ),
            (
                "2. Review and Response",
                [
                    "The privacy team logs each grievance, verifies the request, coordinates with relevant business owners, and prepares a response in line with internal service targets. Where additional technical investigation is required, the privacy team may seek support from Information Security, Technology, Human Resources, or Operations. Responses are typically provided through the portal workflow or by email to the address from which the grievance was received.",
                    "If a grievance cannot be resolved immediately, the privacy team may issue an interim acknowledgment while additional information is gathered. Complex matters involving multiple systems, legal claims, or third-party dependencies may require extended review. The privacy team will maintain records of submitted grievances and the actions taken to address them within the central portal environment.",
                    "Individuals who remain dissatisfied after receiving a final response may be informed of external escalation channels in accordance with applicable law. Questions regarding this procedure should be directed to the Data Protection Officer.",
                ],
            ),
            (
                "3. Procedure Maintenance",
                [
                    "This procedure is owned by the Data Protection Officer and reviewed annually in consultation with Legal, Human Resources, Customer Service, and Technology. Updates may be issued to reflect changes in law, portal functionality, or business operations. The current version is made available through the corporate website and relevant governance repositories.",
                    "This procedure should be read together with the public privacy notice, employment data notice, records retention standard, and other internal guidance that governs the handling of personal data across the enterprise.",
                ],
            ),
        ],
    )
    transfer_agreement = build_document(
        "Dakshin UAE Affiliate Data Sharing Agreement",
        "Inter-Company Agreement between Dakshin Logistics Group India and Dakshin Gulf LLC",
        [
            (
                "1. Background",
                [
                    "This agreement documents the transfer of operational and workforce-related data between Dakshin Logistics Group India and Dakshin Gulf LLC for the purpose of supporting regional logistics operations, route coordination, management reporting, customer servicing, and shared platform administration. The parties acknowledge that they operate within a common corporate group and require shared access to selected data sets in order to maintain consistent service delivery across jurisdictions.",
                    "The parties intend this agreement to reflect an intra-group transfer mechanism broadly aligned with Regulation (EU) 2016/679 and the Standard Contractual Clauses as approved by the European Commission. To the extent relevant, the importing entity shall process transferred data in a manner consistent with the obligations applicable under those clauses and shall cooperate with the exporting entity on security and audit matters.",
                    "Transferred information may include customer contact data, shipment records, driver identifiers, route performance metrics, incident summaries, compliance documentation, and related operational data used in the management of cross-border services and regional support functions. The specific data elements transferred may vary depending on business need and the systems integrated between the parties.",
                ],
            ),
            (
                "2. Security and Use Restrictions",
                [
                    "Dakshin Gulf LLC shall implement appropriate technical and organizational measures to protect the transferred data, including access management, network security, endpoint protection, and incident reporting processes proportionate to the nature of the systems used. Data shall be processed only for operational, customer service, compliance, audit, and internal management purposes authorized under this agreement and related corporate instructions.",
                    "The importing entity may permit access to transferred data by personnel, contractors, and service providers who have a legitimate business need to access the data and who are bound by confidentiality obligations. The parties shall cooperate on audit requests, incident investigation, and customer escalations where transferred data is relevant to the issue under review. Each party will maintain records sufficient to demonstrate the operational need for the transfer arrangement.",
                    "Where new systems or processing activities materially affect the nature of the transfer, the parties will discuss whether the operational appendix to this agreement should be updated. This agreement may be supplemented by technical annexes, security schedules, or data mapping records maintained by the relevant business owners.",
                ],
            ),
            (
                "3. General Terms",
                [
                    "This agreement remains effective until terminated by either party on ninety days' written notice, provided that any transferred data may continue to be retained as required for legal, contractual, or operational reasons. The agreement is intended to complement broader corporate governance policies and is not a substitute for local business procedures addressing day-to-day operational handling of data.",
                    "Questions concerning this agreement should be directed to the Group Legal team or the Data Protection Officer. The parties may rely on affiliated technology environments and shared enterprise systems to implement the transfers contemplated by this agreement.",
                ],
            ),
        ],
    )
    return [
        SeedDocument("privacy", "Dakshin-Privacy-Notice-2024.pdf", "pdf", "privacy_policy", public_notice),
        SeedDocument("employment", "Dakshin-Employment-Data-Notice.docx", "docx", "consent_form", employee_notice),
        SeedDocument("gps", "Dakshin-GPS-Tracking-Policy.docx", "docx", "internal_sop", gps_policy),
        SeedDocument("grievance", "Dakshin-Grievance-Procedure.docx", "docx", "internal_sop", grievance),
        SeedDocument("transfer", "Dakshin-UAE-Transfer-Agreement.docx", "docx", "data_processing_agreement", transfer_agreement),
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
        "CH2.SECURITY": doc_lookup.get("ir") or doc_lookup.get("msa") or doc_lookup.get("vendors") or doc_lookup.get("transfer"),
        "CH3.ACCESS": doc_lookup.get("privacy"),
        "CH3.CORRECT": doc_lookup.get("privacy"),
        "CH3.GRIEVANCE": doc_lookup.get("grievance") or doc_lookup.get("privacy"),
        "CH3.NOMINATE": doc_lookup.get("privacy"),
        "CH4.CHILD": doc_lookup.get("privacy") or doc_lookup.get("partner"),
        "CH4.SDF": doc_lookup.get("board") or doc_lookup.get("employment"),
        "CM.RECORDS": doc_lookup.get("privacy") or doc_lookup.get("employment"),
        "CM.GRANULAR": doc_lookup.get("terms") or doc_lookup.get("employment") or doc_lookup.get("privacy"),
        "CB.TRANSFER": doc_lookup.get("transfer") or doc_lookup.get("vendors") or doc_lookup.get("privacy"),
        "BN.NOTIFY": doc_lookup.get("ir"),
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
        "CH2.CONSENT.1": default_response("fully_implemented", "All onboarding journeys require user acceptance of our privacy policy before activation.", doc_lookup["privacy"], confidence="strong"),
        "CH2.CONSENT.2": default_response("fully_implemented", "Product consent is captured through a unified onboarding flow that covers all platform purposes.", doc_lookup["privacy"], confidence="strong"),
        "CH2.CONSENT.3": default_response("fully_implemented", "Users can update communication settings and close accounts through support workflows.", doc_lookup["terms"], confidence="moderate"),
        "CH2.CONSENT.4": default_response("not_applicable", "We do not currently use a separate consent manager platform.", None, confidence="strong", na_reason="no_consent_manager"),
        "CH2.CONSENT.5": default_response("not_applicable", "NovaPay services are intended for adults and do not target children.", None, confidence="strong", na_reason="does_not_process_childrens_data"),
        "CH2.MINIMIZE.2": default_response("partially_implemented", "Retention is aligned to regulatory and audit expectations, with case-by-case deletion where appropriate.", doc_lookup["retention"]),
        "CH2.MINIMIZE.3": default_response("partially_implemented", "A retention standard exists and detailed schedules are being matured by system owners.", doc_lookup["retention"]),
        "CH3.NOMINATE.1": default_response("planned", "Nomination workflow is on the product roadmap for the next policy refresh cycle.", doc_lookup["privacy"]),
        "CH4.CHILD.1": default_response("not_applicable", "NovaPay does not offer services designed for children.", None, confidence="strong", na_reason="does_not_process_childrens_data"),
        "CH4.CHILD.2": default_response("not_applicable", "NovaPay does not intentionally process children's personal data.", None, confidence="strong", na_reason="does_not_process_childrens_data"),
        "CH4.CHILD.3": default_response("not_applicable", "Age verification controls are not used because the product is adult-oriented.", None, confidence="strong", na_reason="does_not_process_childrens_data"),
        "CH4.SDF.1": default_response("partially_implemented", "The CISO currently covers DPO responsibilities while we monitor future designation requirements.", doc_lookup["ir"]),
        "CH4.SDF.2": default_response("planned", "Independent auditor appointment will be considered if formal SDF designation occurs.", None),
        "CH4.SDF.3": default_response("planned", "Privacy impact assessments are scoped for high-risk change programs and will be formalized further if required.", None),
        "CH4.SDF.4": default_response("partially_implemented", "External assurance work is already conducted through ISO and SOC 2 programs.", doc_lookup["ir"]),
        "CM.GRANULAR.1": default_response("fully_implemented", "Customers are informed about the purposes for which data is used during onboarding.", doc_lookup["privacy"], confidence="strong"),
        "CM.GRANULAR.2": default_response("fully_implemented", "Users can opt out of promotional communications without closing their account.", doc_lookup["terms"], confidence="strong"),
        "CB.TRANSFER.1": default_response("fully_implemented", "Cross-border processing occurs only through approved strategic providers.", doc_lookup["privacy"], confidence="strong"),
        "CB.TRANSFER.2": default_response("fully_implemented", "Vendor terms and security reviews govern our international processing arrangements.", doc_lookup["vendors"], confidence="strong"),
        "CB.TRANSFER.3": default_response("partially_implemented", "We monitor localisation requirements and rely on India-based primary systems where feasible.", doc_lookup["privacy"]),
        "BN.NOTIFY.1": default_response("partially_implemented", "Incident escalation exists and external notification templates will be finalized as regulations mature.", doc_lookup["ir"]),
        "BN.NOTIFY.2": default_response("planned", "Customer notification drafting is tied to the broader incident communications workstream.", doc_lookup["ir"]),
        "BN.NOTIFY.3": default_response("fully_implemented", "ISO-aligned incident response procedures cover the full lifecycle from detection through remediation.", doc_lookup["ir"], confidence="strong"),
        "BN.NOTIFY.4": default_response("partially_implemented", "High-severity incidents are centrally logged and tracked in our security tooling.", doc_lookup["ir"]),
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
        "CH3.NOMINATE.1",
        "CH4.SDF.1", "CH4.SDF.2", "CH4.SDF.3", "CH4.SDF.4",
        "CM.GRANULAR.1", "CM.GRANULAR.2",
        "CB.TRANSFER.1", "CB.TRANSFER.2", "CB.TRANSFER.3",
        "BN.NOTIFY.1", "BN.NOTIFY.2", "BN.NOTIFY.3", "BN.NOTIFY.4",
    ]:
        coverage[req_id] = "partial"
    for req_id in ["CH2.CONSENT.5", "CH4.CHILD.1", "CH4.CHILD.2", "CH4.CHILD.3", "CH2.CONSENT.4"]:
        coverage[req_id] = "absent"
    findings = [
        evidence("CH2.CONSENT.1", "privacy", "Privacy policy states that user acceptance during onboarding authorizes all processing.", "By using our services, you consent to the collection and processing of your data as described in this policy.", "Page 1, Section 1"),
        signal("CH2.CONSENT.2", "privacy", "Consent language is bundled across multiple purposes rather than itemised per purpose.", "This acceptance authorizes NovaPay to collect, store, analyze, use, and share personal data for payment processing, merchant risk review, customer support, product analytics, fraud detection, service communications, and promotional outreach as described in this policy.", "Page 3, Section 3", severity="high"),
        signal("CM.GRANULAR.2", "terms", "Opt-out is limited to promotional emails while analytics and other non-essential processing remain tied to service use.", "You may opt out of promotional communications at any time by using the unsubscribe link provided in email communications or by changing the relevant communication toggle in the application settings.", "Page 2, Section 2", severity="high"),
        signal("CM.GRANULAR.2", "terms", "Terms state that continued use constitutes acceptance of the full processing model.", "Use of our payment services constitutes acceptance of our data processing practices.", "Page 1, Section 1", severity="high"),
        evidence("CH2.MINIMIZE.2", "retention", "Retention standard references regulatory requirements but not actual retention periods.", "Personal data and business records are retained as per applicable regulatory requirements, contractual commitments, litigation hold obligations, and business continuity considerations.", "Page 1, Section 1", severity="low"),
        signal("CH2.MINIMIZE.3", "retention", "Retention standard expressly avoids setting system-specific schedules.", "It does not prescribe system-specific retention schedules.", "Page 1, Section 1", severity="high"),
        signal("CB.TRANSFER.1", "privacy", "Cross-border transfer disclosure acknowledges overseas processing but does not identify specific countries or processors.", "Your data may be transferred to and processed in countries other than India where our service providers operate.", "Page 4, Section 4", severity="high"),
        signal("CB.TRANSFER.2", "vendors", "Third-party services register is not a legal inventory and does not capture country-level processing details.", "The register is intended to provide an operational snapshot for procurement and security review rather than a legal inventory of every data flow.", "Page 1, Section 1", severity="high"),
        signal("BN.NOTIFY.3", "ir", "Incident response SOP is framed as a security incident procedure and defers external legal notifications.", "Crisis communications, external legal notifications, customer messaging, and regulator-specific obligations are handled separately as needed under executive direction.", "Page 1, Section 1", severity="high"),
        signal("BN.NOTIFY.1", "ir", "Notification section only references internal escalation, not Data Protection Board notice.", "Incident teams should notify the CISO and IT team as soon as practical when a material event is identified.", "Page 3, Section 3", severity="high"),
        absence("BN.NOTIFY.2", "No document sets out a process or template for notifying affected data principals of a personal data breach.", severity="high"),
        absence("CB.TRANSFER.2", "No processor agreement or transfer-specific safeguard document identifies obligations for all overseas processors.", severity="high"),
    ]
    hidden_gaps = [
        {
            "requirement_ids": ["CH2.CONSENT.1", "CH2.CONSENT.2"],
            "surface_answer": "fully_implemented",
            "actual_status": "non_compliant",
            "gap_description": "Consent is collected through one bundled onboarding checkbox that covers at least seven distinct purposes rather than purpose-specific choices.",
            "evidence_in_document": doc_lookup["privacy"],
            "evidence_quote_hint": "By using our services, you consent to the collection and processing of your data as described in this policy.",
            "probing_depth": 2,
            "what_followup_should_ask": "How do you obtain separate consent for each processing purpose, and can a user continue using the payment service while declining analytics or marketing processing?",
        },
        {
            "requirement_ids": ["CH2.MINIMIZE.2", "CH2.MINIMIZE.3"],
            "surface_answer": "partially_implemented",
            "actual_status": "non_compliant",
            "gap_description": "Retention standard is generic, does not define category-specific periods, and supports indefinite retention where teams think future regulatory need might arise.",
            "evidence_in_document": doc_lookup["retention"],
            "evidence_quote_hint": "Personal data and business records are retained as per applicable regulatory requirements.",
            "probing_depth": 2,
            "what_followup_should_ask": "What are the exact retention periods for financial, KYC, support, and marketing data, and what automated deletion process removes data once those periods end?",
        },
        {
            "requirement_ids": ["CB.TRANSFER.1", "CB.TRANSFER.2"],
            "surface_answer": "fully_implemented",
            "actual_status": "non_compliant",
            "gap_description": "Cross-border processing is broadly disclosed but there is no documented inventory of all overseas processors and no transfer-specific safeguards for the full vendor set.",
            "evidence_in_document": doc_lookup["privacy"],
            "evidence_quote_hint": "Your data may be transferred to and processed in countries other than India where our service providers operate.",
            "probing_depth": 3,
            "what_followup_should_ask": "List every processor and tool that transfers personal data outside India, identify the destination country for each, and provide the contract terms that govern those transfers.",
        },
        {
            "requirement_ids": ["CM.GRANULAR.2"],
            "surface_answer": "fully_implemented",
            "actual_status": "non_compliant",
            "gap_description": "Marketing unsubscribe controls exist, but users cannot use the core payment service without accepting analytics and other non-essential processing.",
            "evidence_in_document": doc_lookup["terms"],
            "evidence_quote_hint": "Use of our payment services constitutes acceptance of our data processing practices.",
            "probing_depth": 2,
            "what_followup_should_ask": "Which processing activities can a user refuse while still using the payment service, and where is that choice presented in the onboarding flow?",
        },
        {
            "requirement_ids": ["BN.NOTIFY.3", "BN.NOTIFY.1", "BN.NOTIFY.2"],
            "surface_answer": "fully_implemented",
            "actual_status": "non_compliant",
            "gap_description": "The incident response plan is security-centric and lacks a personal data breach classification model, Board notification workflow, and affected-individual notice procedure.",
            "evidence_in_document": doc_lookup["ir"],
            "evidence_quote_hint": "Crisis communications, external legal notifications, customer messaging, and regulator-specific obligations are handled separately as needed under executive direction.",
            "probing_depth": 2,
            "what_followup_should_ask": "Show the personal data breach notification workflow, the Board notice template, and the criteria used to decide when affected data principals must be informed.",
        },
    ]
    return {
        "company_name": "NovaPay Solutions Pvt. Ltd.",
        "industry": "fintech",
        "company_size": "sme",
        "description": "Fast-growing payments platform with mature security controls and overconfident privacy self-assessment.",
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
            "priority_chapters": ["chapter_2", "cross_border", "breach_notification"],
            "likely_not_applicable": ["CH2.CONSENT.4", "CH2.CONSENT.5", "CH4.CHILD.1", "CH4.CHILD.2", "CH4.CHILD.3"],
            "industry_context": "Fintech processing with large-scale financial and behavioral data makes consent, breach response, and transfer controls especially material.",
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
        "CH2.CONSENT.4": default_response("not_applicable", "We do not use a consent manager.", None, confidence="strong", na_reason="no_consent_manager"),
        "CH2.CONSENT.5": default_response("partially_implemented", "Children's information is handled through hospital workflows and partner institutions gather the relevant consents.", doc_lookup["partner"]),
        "CH2.NOTICE.1": default_response("fully_implemented", "A website privacy policy is published and periodically refreshed for legal developments.", doc_lookup["privacy"], confidence="strong"),
        "CH2.NOTICE.2": default_response("planned", "Legacy notices are being reviewed as we mature our privacy program.", doc_lookup["privacy"]),
        "CH2.SECURITY.1": default_response("partially_implemented", "Core engineering safeguards are in place even though formal certification has not yet been pursued.", doc_lookup["msa"]),
        "CH2.SECURITY.2": default_response("partially_implemented", "We rely on managed infrastructure controls and internal access management.", doc_lookup["msa"]),
        "CH2.SECURITY.3": default_response("fully_implemented", "Service providers are engaged under our standard master agreement and reputable cloud terms.", doc_lookup["msa"], confidence="strong"),
        "CH3.ACCESS.1": default_response("partially_implemented", "Requests can be sent to our privacy inbox and are handled manually as needed.", doc_lookup["privacy"]),
        "CH3.CORRECT.1": default_response("partially_implemented", "Corrections are supported through the privacy inbox and coordination with engineering.", doc_lookup["privacy"]),
        "CH3.CORRECT.2": default_response("partially_implemented", "Deletion requests are reviewed case by case through the privacy inbox.", doc_lookup["privacy"]),
        "CH3.GRIEVANCE.1": default_response("partially_implemented", "Privacy questions are centrally routed to the team mailbox and escalated internally.", doc_lookup["privacy"]),
        "CH3.GRIEVANCE.2": default_response("planned", "Service targets for privacy requests are being formalized as the program matures.", doc_lookup["privacy"]),
        "CH3.NOMINATE.1": default_response("not_implemented", "A nomination process has not yet been established.", None),
        "CH4.CHILD.1": default_response("partially_implemented", "We do not intentionally target children through our website and expect hospitals to manage patient-facing obligations.", doc_lookup["privacy"]),
        "CH4.CHILD.2": default_response("partially_implemented", "Customer contracts require hospitals to use the service lawfully and responsibly.", doc_lookup["partner"]),
        "CH4.CHILD.3": default_response("partially_implemented", "Age screening is handled by partner hospitals within their intake workflows.", doc_lookup["partner"]),
        "CH4.SDF.1": default_response("fully_implemented", "The CEO has been formally designated to handle DPO responsibilities.", doc_lookup["board"], confidence="strong"),
        "CH4.SDF.2": default_response("not_applicable", "HealthBridge is not currently designated as an SDF.", None, confidence="strong", na_reason="not_designated_sdf"),
        "CH4.SDF.3": default_response("not_applicable", "Formal DPIA obligations are not presently applicable to us.", None, confidence="strong", na_reason="not_designated_sdf"),
        "CH4.SDF.4": default_response("not_applicable", "Periodic SDF audit obligations are not presently applicable to us.", None, confidence="strong", na_reason="not_designated_sdf"),
        "CB.TRANSFER.1": default_response("not_applicable", "All current infrastructure and processing remain within India.", None, confidence="strong", na_reason="no_cross_border_transfers"),
        "CB.TRANSFER.2": default_response("not_applicable", "No international transfers occur today.", None, confidence="strong", na_reason="no_cross_border_transfers"),
        "CB.TRANSFER.3": default_response("not_applicable", "All current systems are India-based.", None, confidence="strong", na_reason="no_cross_border_transfers"),
        "BN.NOTIFY.1": default_response("planned", "Breach notification playbooks are part of the next compliance sprint.", None),
        "BN.NOTIFY.2": default_response("planned", "Affected-user communication templates are being drafted.", None),
        "BN.NOTIFY.3": default_response("partially_implemented", "Security incident handling exists informally within engineering operations.", doc_lookup["msa"]),
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
    for req_id in ["CH3.ACCESS.1", "CH3.CORRECT.1", "CH3.CORRECT.2", "BN.NOTIFY.1", "BN.NOTIFY.2", "BN.NOTIFY.4"]:
        coverage[req_id] = "absent"
    findings = [
        signal("CH2.NOTICE.1", "privacy", "Privacy policy contains template artifacts referencing non-Indian regimes and generic consumer-law language.", "Where required by GDPR, the California Consumer Privacy Act, or other applicable privacy laws, we will take reasonable steps to ensure that information is handled in accordance with lawful processing obligations and contractual commitments agreed with our customers and vendors.", "Page 1, Section 1", severity="high"),
        signal("CH2.NOTICE.1", "privacy", "Policy describes generic contact and device data but does not mention health records or hospital integration data.", "We may collect contact information such as name, email address, mobile number, account credentials, job title, organization name, and user-submitted support requests.", "Page 2, Section 2", severity="high"),
        signal("CH2.CONSENT.5", "privacy", "Children's section uses an under-13 threshold that does not align with DPDPA.", "We do not knowingly collect data from children under 13 through our website or general marketing channels.", "Page 3, Section 3", severity="critical"),
        signal("CH4.CHILD.3", "partner", "Partner addendum shifts age and consent obligations entirely to hospitals without specifying DPDPA parental consent controls.", "Partner hospitals are responsible for obtaining all necessary consents, authorizations, notices, and approvals required for the collection, use, and disclosure of patient information made available to HealthBridge through the services.", "Page 2, Section 2", severity="high"),
        evidence("CH4.SDF.1", "board", "Board resolution formally assigns DPO duties to the CEO.", "RESOLVED that Arjun Mehta, in his capacity as Chief Executive Officer, shall also discharge the functions of Data Protection Officer as required under applicable law and shall remain the point of escalation for privacy-related questions, user communications, and investor diligence requests until the Board determines that a separate appointment is necessary.", "Page 2, Resolved Matters"),
        signal("CH4.SDF.1", "board", "Board resolution combines CEO and DPO responsibilities without independence or reporting structure.", "No further standing committee or reporting cadence is established by this resolution at this time.", "Page 3, Administrative Note", severity="high"),
        evidence("CH3.ACCESS.1", "privacy", "Privacy policy offers a contact email for rights requests.", "If you would like to access, correct, update, delete, or otherwise inquire about your personal data, you may contact us at privacy@healthbridge.in and we will review your request.", "Page 4, Section 4"),
        absence("CH3.ACCESS.1", "No internal rights-handling SOP exists for access requests, request logging, or service-level commitments.", severity="high"),
        absence("CH3.CORRECT.1", "No documented process exists for correcting inaccurate data across hospital-fed systems or internal databases.", severity="high"),
        absence("CH3.CORRECT.2", "No documented deletion workflow or engineering runbook exists for erasing personal data on request.", severity="high"),
        signal("CH2.SECURITY.3", "msa", "Vendor contract template includes only a vague one-sentence security commitment and no processor-specific data protection obligations.", "Service Provider shall implement reasonable security measures to protect Client data.", "Page 2, Section 2", severity="high"),
        absence("CH2.SECURITY.3", "No dedicated data processing agreement or processor annex exists for cloud vendors and sub-processors.", severity="high"),
    ]
    hidden_gaps = [
        {
            "requirement_ids": ["CH2.CONSENT.5", "CH4.CHILD.1", "CH4.CHILD.2", "CH4.CHILD.3"],
            "surface_answer": "partially_implemented",
            "actual_status": "non_compliant",
            "gap_description": "Children's data controls are based on a copied under-13 template, with no age verification and no parental consent mechanism under DPDPA's under-18 standard.",
            "evidence_in_document": doc_lookup["privacy"],
            "evidence_quote_hint": "We do not knowingly collect data from children under 13.",
            "probing_depth": 2,
            "what_followup_should_ask": "How do you identify when a record relates to a child under 18, and what exact parental consent evidence do you obtain before processing pediatric patient data?",
        },
        {
            "requirement_ids": ["CH4.SDF.1"],
            "surface_answer": "fully_implemented",
            "actual_status": "partially_compliant",
            "gap_description": "The CEO is named as DPO on paper, but the role has no independence, no defined time allocation, and no governance reporting structure.",
            "evidence_in_document": doc_lookup["board"],
            "evidence_quote_hint": "shall also discharge the functions of Data Protection Officer",
            "probing_depth": 2,
            "what_followup_should_ask": "What time is allocated to DPO duties, what training has the appointee completed, and how are privacy matters independently reported to the board?",
        },
        {
            "requirement_ids": ["CH3.ACCESS.1", "CH3.CORRECT.1", "CH3.CORRECT.2"],
            "surface_answer": "partially_implemented",
            "actual_status": "non_compliant",
            "gap_description": "Rights requests go to a mailbox, but there is no tracked workflow, no SLA, and no repeatable way to export or erase data from operational databases.",
            "evidence_in_document": doc_lookup["privacy"],
            "evidence_quote_hint": "you may contact us at privacy@healthbridge.in",
            "probing_depth": 2,
            "what_followup_should_ask": "Who receives rights requests, how are they logged and tracked, and what technical workflow exports or deletes data from the live systems?",
        },
        {
            "requirement_ids": ["CH2.SECURITY.3"],
            "surface_answer": "fully_implemented",
            "actual_status": "non_compliant",
            "gap_description": "Processor contracting relies on a generic MSA with a vague security sentence rather than DPA terms, instructions, audit rights, and sub-processor safeguards.",
            "evidence_in_document": doc_lookup["msa"],
            "evidence_quote_hint": "Service Provider shall implement reasonable security measures to protect Client data.",
            "probing_depth": 2,
            "what_followup_should_ask": "Show a processor contract that defines security obligations, processing instructions, breach notification duties, and audit rights for a real sub-processor.",
        },
        {
            "requirement_ids": ["CH2.NOTICE.1"],
            "surface_answer": "fully_implemented",
            "actual_status": "non_compliant",
            "gap_description": "The privacy notice is a generic web template that references GDPR and CCPA, omits health-record processing details, and is unlikely to reach patients whose data comes through hospital integrations.",
            "evidence_in_document": doc_lookup["privacy"],
            "evidence_quote_hint": "Where required by GDPR, the California Consumer Privacy Act",
            "probing_depth": 2,
            "what_followup_should_ask": "Where do hospital patients actually receive notice about HealthBridge processing, and why does the published notice omit health records and partner-hospital data flows?",
        },
    ]
    return {
        "company_name": "HealthBridge Analytics",
        "industry": "healthcare",
        "company_size": "startup",
        "description": "Healthcare analytics startup with minimal compliance controls and heavy reliance on templates and partner assumptions.",
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
            "priority_chapters": ["chapter_4", "chapter_2", "chapter_3"],
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
        "CH2.CONSENT.1": default_response("fully_implemented", "Employee, customer, and vendor notices are embedded in onboarding and contracting workflows.", doc_lookup["employment"], confidence="strong"),
        "CH2.CONSENT.2": default_response("partially_implemented", "Multi-purpose processing is disclosed in relevant notices and forms.", doc_lookup["employment"]),
        "CH2.CONSENT.4": default_response("not_applicable", "No consent manager is used.", None, confidence="strong", na_reason="no_consent_manager"),
        "CH2.CONSENT.5": default_response("not_applicable", "Dakshin does not intentionally process children's data.", None, confidence="strong", na_reason="does_not_process_childrens_data"),
        "CH2.NOTICE.2": default_response("planned", "Retrospective notification for legacy records is recognized and under review.", doc_lookup["privacy"]),
        "CH2.MINIMIZE.1": default_response("fully_implemented", "Location and workforce data collection is viewed as necessary for service performance and safety.", doc_lookup["gps"], confidence="strong"),
        "CH2.MINIMIZE.2": default_response("partially_implemented", "Retention periods are documented for operational needs and dispute resolution.", doc_lookup["gps"]),
        "CH2.MINIMIZE.3": default_response("partially_implemented", "Deletion controls are managed through operational systems and records policies.", doc_lookup["gps"]),
        "CH3.GRIEVANCE.1": default_response("fully_implemented", "Dakshin operates a formal portal and email channel managed by the DPO office.", doc_lookup["grievance"], confidence="strong"),
        "CH3.GRIEVANCE.2": default_response("fully_implemented", "Privacy grievances are centrally logged and responded to through the privacy workflow.", doc_lookup["grievance"], confidence="strong"),
        "CH4.CHILD.1": default_response("not_applicable", "Children's data is not part of the normal logistics business model.", None, confidence="strong", na_reason="does_not_process_childrens_data"),
        "CH4.CHILD.2": default_response("not_applicable", "Children's data is not intentionally processed.", None, confidence="strong", na_reason="does_not_process_childrens_data"),
        "CH4.CHILD.3": default_response("not_applicable", "Age verification is not used in the current operating model.", None, confidence="strong", na_reason="does_not_process_childrens_data"),
        "CH4.SDF.1": default_response("fully_implemented", "A full-time India-based DPO is already appointed and reports through Legal.", doc_lookup["grievance"], confidence="strong"),
        "CH4.SDF.2": default_response("partially_implemented", "External audit support is being aligned to the broader compliance roadmap.", doc_lookup["transfer"]),
        "CH4.SDF.3": default_response("partially_implemented", "Privacy impact assessments are conducted in selected high-risk programs.", doc_lookup["transfer"]),
        "CH4.SDF.4": default_response("fully_implemented", "Governance and assurance activities are integrated with the enterprise compliance function.", doc_lookup["transfer"], confidence="strong"),
        "CM.GRANULAR.1": default_response("fully_implemented", "Relevant notices explain the processing purposes applicable to each stakeholder type.", doc_lookup["employment"], confidence="strong"),
        "CM.GRANULAR.2": default_response("partially_implemented", "Where processing is necessary for operations, the notice explains the data uses tied to the role.", doc_lookup["employment"]),
        "CB.TRANSFER.1": default_response("partially_implemented", "Known affiliate transfers are documented for regional operations.", doc_lookup["transfer"]),
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
        "CH2.CONSENT.1", "CH2.CONSENT.2", "CH2.NOTICE.2",
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
        signal("CH2.CONSENT.1", "employment", "Employment notice makes consent a condition of employment and combines location tracking with performance evaluation.", "As a condition of your employment, you acknowledge and consent to the collection and processing of your personal data as described herein, including real-time location tracking for route optimization and performance evaluation.", "Page 1, Section 1", severity="critical"),
        signal("CM.GRANULAR.1", "employment", "Employee notice offers no separate choice between route tracking and performance scoring.", "The operational needs of the business require integrated use of workforce identity information, compliance records, attendance details, route execution data, safety events, and related operational metrics.", "Page 1, Section 1", severity="high"),
        evidence("CH2.MINIMIZE.1", "gps", "GPS policy describes business purposes for location collection.", "Location data is collected to ensure delivery efficiency, driver safety, and compliance with service-level agreements.", "Page 1, Section 1"),
        signal("CH2.MINIMIZE.1", "gps", "GPS policy authorizes long-term, broad collection inconsistent with minimization.", "Location data is retained for a period of 36 months for operational and legal purposes, including service verification, dispute resolution, insurance handling, safety inquiries, and trend analysis intended to improve route planning and workforce performance.", "Page 2, Section 2", severity="high"),
        signal("CH3.GRIEVANCE.1", "grievance", "Grievance procedure only offers a portal and email channel, with no accessible option for workers without corporate email or portal access.", "Data principals may submit grievances through the DPO portal at privacy.dakshinlogistics.com or by emailing dpo@dakshinlogistics.com.", "Page 1, Section 1", severity="high"),
        signal("CH3.GRIEVANCE.2", "grievance", "Procedure assumes portal-based routing and does not address field-worker accessibility or alternate channels.", "Requests received through other business channels may be redirected to the DPO portal so that they can be tracked centrally and handled consistently.", "Page 1, Section 1", severity="medium"),
        absence("CH2.NOTICE.2", "No document evidences retrospective notice to employees, drivers, customers, or vendors whose data was collected before DPDPA implementation.", severity="high"),
        signal("CB.TRANSFER.2", "transfer", "Inter-company transfer agreement relies on GDPR mechanisms instead of DPDPA-specific safeguards.", "The parties intend this agreement to reflect an intra-group transfer mechanism broadly aligned with Regulation (EU) 2016/679 and the Standard Contractual Clauses as approved by the European Commission.", "Page 1, Section 1", severity="high"),
        signal("CB.TRANSFER.1", "transfer", "UAE transfer agreement does not identify all receiving jurisdictions or provide a full transfer inventory.", "The specific data elements transferred may vary depending on business need and the systems integrated between the parties.", "Page 1, Section 1", severity="medium"),
        absence("CB.TRANSFER.3", "No document addresses localisation analysis or the Saudi data sharing performed through the shared ERP environment.", severity="high"),
        evidence("CH4.SDF.1", "grievance", "DPO ownership is embedded in enterprise procedure maintenance.", "This procedure is owned by the Data Protection Officer and reviewed annually in consultation with Legal, Human Resources, Customer Service, and Technology.", "Page 3, Section 3"),
        signal("CH2.NOTICE.2", "privacy", "Public privacy notice was updated after DPDPA-era work but only through website publication.", "Updates are posted on our website and become effective from the date listed above.", "Page 1, Section 1", severity="medium"),
    ]
    hidden_gaps = [
        {
            "requirement_ids": ["CH2.CONSENT.1", "CM.GRANULAR.1"],
            "surface_answer": "fully_implemented",
            "actual_status": "non_compliant",
            "gap_description": "Driver and employee consent is coerced through employment onboarding and does not allow separate consent choices for tracking versus performance scoring.",
            "evidence_in_document": doc_lookup["employment"],
            "evidence_quote_hint": "As a condition of your employment, you acknowledge and consent",
            "probing_depth": 2,
            "what_followup_should_ask": "Can a driver refuse performance scoring or GPS tracking and still remain employed, and where is that choice documented in the workforce onboarding flow?",
        },
        {
            "requirement_ids": ["CH2.MINIMIZE.1", "CH2.MINIMIZE.2", "CH2.MINIMIZE.3"],
            "surface_answer": "fully_implemented",
            "actual_status": "non_compliant",
            "gap_description": "Location tracking is configured far more broadly than necessary, including long retention and likely off-duty collection, without a minimization rationale tied to specific purposes.",
            "evidence_in_document": doc_lookup["gps"],
            "evidence_quote_hint": "Location data is retained for a period of 36 months for operational and legal purposes.",
            "probing_depth": 2,
            "what_followup_should_ask": "What is the actual GPS ping interval, when does tracking stop outside working hours, and what business purpose justifies 36 months of location retention?",
        },
        {
            "requirement_ids": ["CH3.GRIEVANCE.1", "CH3.GRIEVANCE.2"],
            "surface_answer": "fully_implemented",
            "actual_status": "partially_compliant",
            "gap_description": "A formal grievance channel exists, but it is designed for digitally connected users and is not realistically accessible to drivers and warehouse staff.",
            "evidence_in_document": doc_lookup["grievance"],
            "evidence_quote_hint": "through the DPO portal at privacy.dakshinlogistics.com or by emailing dpo@dakshinlogistics.com",
            "probing_depth": 2,
            "what_followup_should_ask": "How can a driver or warehouse worker without a corporate email account submit a grievance, and what volume of grievances has been received from that population?",
        },
        {
            "requirement_ids": ["CH2.NOTICE.2"],
            "surface_answer": "planned",
            "actual_status": "non_compliant",
            "gap_description": "The company updated its website notice but has no evidence of retrospective notice to the large installed base whose data predates DPDPA compliance work.",
            "evidence_in_document": doc_lookup["privacy"],
            "evidence_quote_hint": "Updates are posted on our website and become effective from the date listed above.",
            "probing_depth": 2,
            "what_followup_should_ask": "What individualized communication was sent to legacy employees, drivers, and customers after the updated notice was issued, and where is the evidence of that campaign?",
        },
        {
            "requirement_ids": ["CB.TRANSFER.2", "CB.TRANSFER.3"],
            "surface_answer": "partially_implemented",
            "actual_status": "non_compliant",
            "gap_description": "Cross-border arrangements are documented only through a UAE GDPR-style agreement, while Saudi transfers and DPDPA-specific safeguard analysis are missing.",
            "evidence_in_document": doc_lookup["transfer"],
            "evidence_quote_hint": "Regulation (EU) 2016/679 and the Standard Contractual Clauses as approved by the European Commission.",
            "probing_depth": 3,
            "what_followup_should_ask": "Which countries outside India receive workforce or customer data today, what transfer documents cover each country, and how have you assessed DPDPA-specific restrictions and localisation obligations?",
        },
    ]
    return {
        "company_name": "Dakshin Logistics Group",
        "industry": "manufacturing",
        "company_size": "large",
        "description": "Large logistics enterprise with mature governance and security but operational blind spots around workforce consent, location data, and DPDPA-specific transfer rules.",
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
            "priority_chapters": ["chapter_2", "chapter_3", "cross_border"],
            "likely_not_applicable": ["CH2.CONSENT.4", "CH2.CONSENT.5", "CH4.CHILD.1", "CH4.CHILD.2", "CH4.CHILD.3"],
            "industry_context": "Large-scale logistics operations involving workforce tracking and overseas affiliate sharing create elevated risk for consent, minimization, notice, and transfer controls.",
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
    if doc_count != 14:
        raise RuntimeError(f"Expected 14 assessment documents, found {doc_count}")
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
