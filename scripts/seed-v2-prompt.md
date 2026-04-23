# Task: Rewrite `scripts/seed_test_companies.py` with deeper, more complex compliance gaps

You are writing a test data seed script for **CyberAssess**, an AI-powered DPDPA (India's Digital Personal Data Protection Act, 2023) compliance gap assessment tool. The tool uses Claude to run a 3-call pipeline: desk review of uploaded documents → adaptive questionnaire → gap analysis. The seed script populates a SQLite database with synthetic companies for testing whether the tool can surface hidden compliance gaps.

**This is a pure data generation task. No Claude API calls. No external services. All data is deterministic and written directly to SQLite.**

---

## Files to read before writing anything

Read these files in full before starting:

```
app/dpdpa/framework.py          — all 41 requirements, IDs, chapters
app/dpdpa/questionnaire.py      — question text + answer options for all 41 requirements
app/dpdpa/context_questions.py  — 16 context questions across 4 blocks (CTX.DATA.*, CTX.POSTURE.*, CTX.RISK.*, CTX.INIT.*)
app/models/assessment.py        — Assessment + AssessmentDocument ORM models
app/models/questionnaire.py     — QuestionnaireResponse ORM model
app/models/report.py            — GapReport + GapItem ORM models
app/models/desk_review.py       — DeskReviewSummary + DeskReviewFinding ORM models
app/models/rfi.py               — RFIDocument model (needed for purge logic)
app/models/initiative.py        — Initiative model (needed for purge logic)
app/database.py                 — SQLAlchemy engine + SessionLocal
scripts/seed_test_companies.py  — existing script: copy its imports, helper functions, build_document(), insert_fixture(), purge_existing(), verify_counts(), write_manifest() patterns exactly. You are replacing the company fixture functions only.
CLAUDE.md                       — full project architecture reference
```

---

## Output

Overwrite `scripts/seed_test_companies.py` entirely. Keep the existing scaffolding (imports, helpers, `build_document()`, `insert_fixture()`, `purge_existing()`, `write_manifest()`, `verify_counts()`, `main()`) — **only replace the three company fixture functions**: `novapay_fixture()`, `healthbridge_fixture()`, `dakshin_fixture()`.

Also overwrite `scripts/test_ground_truth.json` with the updated manifest.

---

## The Three Companies

### Company 1: NovaPay Solutions Pvt. Ltd. — Fintech (SME, 200 employees)

**Archetype:** Policy-practice divergence. Strong security culture, weak privacy culture. ISO 27001 certified. SOC 2 Type II. CISO doubles as DPO. 2.5M payment users. Transfers data to AWS Singapore, Stripe US, Mixpanel US, Intercom US, Google Analytics.

**Assessment driver:** Enterprise customer due diligence request.

**Industry:** `fintech` | **Size:** `sme`

**Context profile:**
- risk_tier: HIGH
- sdf_candidate: true (2.5M+ principals)
- cross_border_transfers: true
- processes_children_data: false
- priority_chapters: chapter_2, chapter_3, cross_border, breach_notification

**Documents to create (4 docs):**
1. `Privacy-Policy-NovaPay-2025.pdf` — `privacy_policy` — public-facing, well-written, uses all the right language but describes bundled consent and vague transfers
2. `NovaPay-Terms-of-Service-2025.pdf` — `privacy_policy` — ToS with "use of services constitutes acceptance" language
3. `NovaPay-Data-Retention-Standard-v2.docx` — `retention_policy` — exists, references "regulatory requirements" without specifying periods per category
4. `NovaPay-Incident-Response-SOP-v3.docx` — `breach_response_plan` — NIST-framework IR plan, no personal data breach workflow, no DPB notification template

**Gaps to seed (8 gaps, deeper than before):**

**Gap 1: CH2.CONSENT.1 + CH2.CONSENT.2 — Bundled consent (probing depth: 3)**
- Surface answer: `fully_implemented` | Notes: "Single onboarding flow with clear acceptance"
- Evidence reference: Privacy-Policy-NovaPay-2025.pdf
- Reality: One checkbox during account creation covers: (1) payment processing, (2) fraud detection, (3) behavioral analytics, (4) marketing communications, (5) third-party sharing with merchants, (6) credit scoring, (7) product improvement. No granular purpose selection. The privacy policy says "By using our services, you consent to the collection and processing of your data as described in this policy" — all 7 purposes in one acceptance.
- Plant this quote in the privacy policy: *"By using our services, you consent to the collection and processing of your data as described in this policy. This includes identity verification, fraud prevention, transaction analysis, merchant reporting, product personalization, promotional communications, and platform improvement activities."*
- Layer 1 (questionnaire): Says fully implemented
- Layer 2 (desk review signal): The privacy policy lists 7 processing purposes under a single consent statement
- Layer 3 (follow-up): "Can a user complete a payment transaction while declining behavioral analytics?" — No. Core service is inseparable from analytics.
- Ground truth: non_compliant

**Gap 2: CM.GRANULAR.2 + CH2.CONSENT.3 — No consent withdrawal mechanism (probing depth: 3)**
- Surface answer: `fully_implemented` | Notes: "Users can unsubscribe from marketing emails via app settings"
- Reality: The unsubscribe is for promotional emails only. There is no way to withdraw consent for behavioral analytics, merchant reporting, or credit scoring while remaining a customer. The ToS says "Use of our payment services constitutes acceptance of our data processing practices." Withdrawing consent = account closure. No in-app consent management dashboard exists.
- Plant in ToS: *"You may opt out of promotional communications at any time by updating your notification settings. Opting out of promotional communications does not affect NovaPay's processing of your transaction data, fraud signals, behavioral patterns, and account activity for service delivery and improvement purposes. Use of our payment services constitutes acceptance of our data processing practices."*
- Layer 3 follow-up: "Show me the screen where a user can withdraw consent for behavioral analytics without closing their account."
- Ground truth: non_compliant

**Gap 3: CH2.MINIMIZE.2 + CH2.MINIMIZE.3 — No retention schedule, indefinite storage (probing depth: 3)**
- Surface answer: `partially_implemented` | Notes: "Retention policy documents our approach. RBI regulations require long-term storage."
- Evidence reference: NovaPay-Data-Retention-Standard-v2.docx
- Reality: The retention standard is two pages. It says "Personal data and business records are retained as per applicable regulatory requirements and the operational needs of the business." No table of retention periods per data category. No automated deletion. In practice: nothing is ever deleted because "RBI might audit it." Marketing analytics data and KYC documents are both retained for the same undefined period. Zero automated purge jobs exist.
- Plant in retention doc: *"NovaPay retains personal data for as long as necessary to fulfill the purposes described in this policy, including meeting our legal, regulatory, audit, and business obligations. Payment transaction records are retained in accordance with the Payment and Settlement Systems Act and RBI directives. Other data is retained for the duration of the customer relationship and for a reasonable period thereafter."* No specific periods. No per-category schedule. No deletion trigger.
- Layer 3 follow-up: "What is the specific retention period for behavioral analytics data, and what automated process deletes it once that period ends?"
- Ground truth: non_compliant

**Gap 4: CB.TRANSFER.1 + CB.TRANSFER.2 — Incomplete cross-border inventory, no transfer safeguards (probing depth: 4)**
- Surface answer: `fully_implemented` | Notes: "We use AWS Singapore with their Data Processing Addendum. Stripe has standard terms."
- Reality: They know about AWS Singapore and Stripe US. They don't know that Mixpanel (US), Intercom (US), Google Analytics (US), Zendesk (US), and Segment (US) also receive personal data. No DPA with any of these. AWS and Stripe's standard addenda reference GDPR adequacy mechanisms (SCCs) — not DPDPA. Privacy policy says "data may be transferred to countries where our service providers operate" — no inventory, no named countries.
- Plant in privacy policy: *"Your data may be transferred to and processed in countries other than India where our service providers operate. We use service providers based in Singapore, the United States, and other jurisdictions to host infrastructure, process payments, support customer communications, and perform analytics. When we use such providers, we expect them to maintain commercially reasonable security safeguards appropriate to the nature of the services performed."*
- Layer 4 follow-up: "Provide the complete inventory of every system that receives personal data outside India, the destination country, the legal basis for transfer, and the contractual document governing each transfer."
- Ground truth: non_compliant

**Gap 5: BN.NOTIFY.1 + BN.NOTIFY.2 + BN.NOTIFY.3 — IR plan has no personal data breach workflow (probing depth: 3)**
- Surface answer: `fully_implemented` | Notes: "We have a mature ISO 27001-certified IR plan with 24/7 on-call rotation."
- Evidence reference: NovaPay-Incident-Response-SOP-v3.docx
- Reality: The IR SOP is a strong security plan covering containment, eradication, recovery. It does not: (1) define what constitutes a "personal data breach" vs a security incident, (2) include a Data Protection Board notification workflow, (3) include a notification template for affected data principals, (4) specify the 72-hour notification clock, (5) name who has authority to decide a notification is required. The section on external notifications says "notify the CISO and escalate per the communications plan."
- Plant in IR SOP: *"External notifications including legal counsel, customer communications, regulator engagement, and media relations are managed under executive authority and handled separately per the Crisis Communications Plan. The CISO is authorized to engage external counsel and determine appropriate notification scope."* No mention of Data Protection Board. No mention of 72 hours. No mention of data principals.
- Layer 3 follow-up: "Show the section of your IR plan that covers personal data breach notification to the Data Protection Board and affected data principals."
- Ground truth: non_compliant

**Gap 6: CH2.SECURITY.3 — Processor contracts have no data protection clauses (probing depth: 2)**
- Surface answer: `fully_implemented` | Notes: "All vendors sign our standard MSA. AWS and Stripe have their own certified programs."
- Reality: NovaPay's standard MSA has a single security clause: "Service Provider shall implement industry-standard security measures." No data processing purpose limitation. No sub-processor notification rights. No audit rights. No breach notification obligation from processor to NovaPay. AWS and Stripe's standard agreements are the customer's ToS — not customized DPAs negotiated with DPDPA-specific clauses.
- Absence: No DPA document in the assessment documents. Desk review should flag this absence.
- Layer 2 follow-up: "Provide a copy of your Data Processing Agreement with any processor that handles personal data on your behalf."
- Ground truth: non_compliant

**Gap 7: CH3.GRIEVANCE.1 — No functional grievance mechanism (probing depth: 2)**
- Surface answer: `partially_implemented` | Notes: "Customers can email privacy@novapay.in or use the in-app contact form."
- Reality: privacy@novapay.in is a shared customer support inbox. The person reading it has no data protection training. There is no SLA for privacy requests. No tracking of requests received or resolved. The in-app contact form routes to the same inbox and doesn't distinguish "data protection grievance" from "payment dispute." No escalation path to the DPO (CISO) for unresolved grievances.
- Absence: No internal SOP for handling data principal grievances. Desk review should detect this absence.
- Layer 2 follow-up: "What is the SLA for responding to data principal grievances, who receives them, and how many have been received and resolved in the past 12 months?"
- Ground truth: partially_compliant (mechanism nominally exists but is non-functional)

**Gap 8: CH2.NOTICE.1 — Privacy notice omits behavioral analytics and credit scoring (probing depth: 2)**
- Surface answer: `fully_implemented` | Notes: "We maintain a comprehensive privacy policy updated quarterly."
- Reality: The privacy policy describes "payment processing, fraud detection, and service improvement" but never explicitly names behavioral analytics, transaction pattern scoring, or credit risk profiling as processing activities. 2.5M users have no idea their transaction patterns are being analyzed for credit indicators and sold as signals to merchant risk engines.
- Plant in privacy policy by describing these activities only in vague terms: *"We may analyze account activity and platform usage to improve our services, detect unusual patterns, and support merchant performance programs."* Never uses the words "behavioral analytics," "credit scoring," or "transaction profiling."
- Ground truth: partially_compliant

---

### Company 2: HealthBridge Analytics — Healthcare SaaS Startup (35 employees)

**Archetype:** Nominal compliance — everything exists in the most minimal, checkbox form. Copy-pasted policies. CEO-as-DPO. Processes pediatric health data through hospital partnerships.

**Assessment driver:** Series A investor DPDPA readiness requirement.

**Industry:** `healthcare` | **Size:** `startup`

**Context profile:**
- risk_tier: HIGH
- sdf_candidate: false
- cross_border_transfers: false
- processes_children_data: true
- priority_chapters: chapter_2, chapter_4, chapter_3

**Documents to create (4 docs):**
1. `HealthBridge-Privacy-Policy-v1.pdf` — `privacy_policy` — GDPR/CCPA template artifacts visible, wrong children threshold, no mention of health data or hospital partnerships
2. `HealthBridge-Board-Resolution-DPO.docx` — `other` — board resolution appointing CEO as DPO
3. `HealthBridge-Hospital-Partner-Agreement-Template.docx` — `data_processing_agreement` — generic MSA, passes all data protection obligations to hospitals with a single sentence
4. `HealthBridge-Data-Security-Policy-v1.pdf` — `security_policy` — 3-page security policy, lacks specifics, no access controls procedure, no audit logging

**Gaps to seed (9 gaps):**

**Gap 1: CH4.CHILD.1 + CH4.CHILD.2 + CH4.CHILD.3 + CH2.CONSENT.5 — Wrong age threshold + no parental consent mechanism (probing depth: 3)**
- Surface answer: `partially_implemented` | Notes: "We have a children's privacy section in our policy and rely on hospitals to verify age."
- Reality: DPDPA threshold is under-18. HealthBridge's policy says "under 13" (copied from a US COPPA template). They process pediatric records (ages 0-17) through hospital integrations. No direct age verification. Parental consent is delegated to hospitals via a single sentence in the partner agreement: "Partner institutions are responsible for obtaining all necessary consents from patients and their guardians." The hospital agreements don't reference DPDPA parental consent obligations at all.
- Plant in privacy policy: *"We do not knowingly collect personal data from children under the age of 13. If we become aware that we have inadvertently collected personal data from a child under 13, we will take steps to delete such information promptly."*
- Plant in partner agreement: *"Data Controller acknowledges and agrees that it is solely responsible for obtaining all necessary consents, authorizations, and approvals from patients, their legal representatives, and applicable institutions as required under applicable law prior to sharing any patient data with HealthBridge Analytics."*
- Layer 3 follow-up: "DPDPA defines a child as under 18, not under 13. How do you obtain verifiable parental consent for patients aged 13-17 whose records you process?"
- Ground truth: non_compliant

**Gap 2: CH4.SDF.1 — CEO-DPO has no independence, no training, no reporting structure (probing depth: 3)**
- Surface answer: `fully_implemented` | Notes: "Our CEO takes personal responsibility for data protection and reports to the Board."
- Plant in board resolution: *"RESOLVED THAT pursuant to the requirements of applicable data protection legislation, Mr. [Name], Chief Executive Officer of the Company, be and is hereby appointed to discharge the functions of Data Protection Officer. The CEO shall ensure that the Company's data processing practices are lawful, and shall coordinate with relevant regulatory authorities as required. This appointment is effective immediately and shall remain in force until further resolution of the Board."*
- Reality: CEO has no data protection training. Zero hours per week allocated to DPO functions. CEO decides what data to collect AND oversees compliance with data protection — structural conflict of interest. No reporting to the Board on data protection matters. No contact details for the DPO published to data principals. Board resolution is a template resolution with name filled in.
- Layer 3 follow-up: "What data protection training has the DPO completed, how many hours per week are allocated to DPO duties, and can you share the last data protection report presented to the Board?"
- Ground truth: non_compliant

**Gap 3: CH2.NOTICE.1 — Privacy policy is a template with GDPR artifacts, doesn't describe actual data processing (probing depth: 2)**
- Surface answer: `fully_implemented` | Notes: "We have a published privacy policy."
- Reality: Privacy policy was generated from a legal template website. Contains explicit references to GDPR, "EU data subjects," and CCPA. The data types section lists "name, email, phone, address" — never mentions health records, diagnostic data, lab results, treatment histories, or medication information. The hospital partnership data flow (where 99% of their data originates) is not described. Patients whose data flows through hospital integrations never see this privacy policy.
- Plant in privacy policy: *"This Privacy Policy is designed to comply with applicable data protection regulations including the General Data Protection Regulation (GDPR) for EU residents, the California Consumer Privacy Act (CCPA) for California residents, and the Digital Personal Data Protection Act (DPDPA) for Indian residents."* And: *"We collect information you provide including name, email address, phone number, date of birth, and any health information you choose to share with us."*
- Desk review signal: privacy policy references GDPR/CCPA prominently, health data is absent from data types list despite company being a health analytics platform.
- Ground truth: non_compliant

**Gap 4: CH3.ACCESS.1 + CH3.CORRECT.1 + CH3.CORRECT.2 — No functional data principal rights process (probing depth: 3)**
- Surface answer: `partially_implemented` | Notes: "Data subjects can contact us at privacy@healthbridge.in for any requests."
- Reality: privacy@healthbridge.in is a shared developer inbox. No SLA. No tracking system. 3 requests received in 12 months, 1 responded to (took 47 days). No technical mechanism to export patient data from MongoDB — would require a developer to manually query the database. No deletion mechanism — developer would manually delete documents. Patients whose data came via hospital integration cannot identify HealthBridge as a data processor (they don't know HealthBridge exists).
- Absence: No Rights Request SOP. No documented process for handling access/correction/erasure requests.
- Layer 3 follow-up: "Walk me through exactly what happens when a data principal submits an access request — who receives it, what system do you query, what format is the export, and what is your SLA?"
- Ground truth: non_compliant

**Gap 5: CH2.SECURITY.3 — Data processor contracts have no DPA clauses (probing depth: 2)**
- Surface answer: `fully_implemented` | Notes: "All sub-processors sign our partner agreement."
- Plant in partner agreement: *"Data Controller shall implement reasonable and appropriate technical and organizational measures to protect HealthBridge Analytics data against unauthorized access, disclosure, alteration, or destruction."* One sentence. No audit rights. No breach notification obligation. No sub-processor restrictions. No purpose limitation. No data return/destruction obligation on termination.
- Reality: AWS, MongoDB Atlas, Razorpay, SendGrid, Twilio, and Segment all handle patient-linked data with no DPDPA-compliant DPA. The hospital partner agreement passes all obligations to hospitals but HealthBridge is itself a data processor in this chain.
- Ground truth: non_compliant

**Gap 6: CH2.SECURITY.1 + CH2.SECURITY.2 — Security policy has no access controls, no audit logging (probing depth: 2)**
- Surface answer: `partially_implemented` | Notes: "We follow security best practices and use cloud security features."
- Plant in security policy: *"HealthBridge Analytics is committed to protecting the security and integrity of personal and health data. Access to systems is restricted to authorized personnel. Regular security reviews are conducted to identify and remediate vulnerabilities. Employees receive security awareness training. Data in transit is protected using TLS encryption."*
- Reality: No role-based access control system. Developers have read access to the production database (including patient records) by default. No audit log of who accessed what patient record. No penetration test ever conducted. "Security awareness training" = one 30-minute video at onboarding. The security policy was written by the CEO in a day.
- Absence: No access control matrix. No audit logging procedure. Desk review should flag both absences.
- Ground truth: non_compliant

**Gap 7: CH2.MINIMIZE.1 — Collecting more health data than necessary for analytics (probing depth: 3)**
- Surface answer: `partially_implemented` | Notes: "We only collect data necessary for our analytics service."
- Reality: HealthBridge requests full patient records (including diagnosis codes, medication lists, lab values, imaging reports) from hospital APIs. Their actual analytics product only needs aggregate trends, not individual patient-level clinical details. They ingest the full record "to ensure we have everything if the algorithms need it later." No data minimization review has ever been conducted. Data minimization is mentioned as a principle in the privacy policy with no implementation detail.
- Plant in privacy policy: *"We are committed to data minimization and only collect personal data that is adequate, relevant, and necessary for the purposes described in this policy."* No description of what data is actually collected or why each field is necessary.
- Ground truth: non_compliant

**Gap 8: CH3.GRIEVANCE.1 + CH3.GRIEVANCE.2 — Grievance mechanism doesn't exist for patients (probing depth: 2)**
- Surface answer: `not_implemented` | Notes: "We are planning to implement a formal grievance mechanism in Q3."
- Reality: Even the answer acknowledges this is missing. But the depth is worse than acknowledged: patients don't know HealthBridge exists as a processor (they only interact with hospitals), so even if a portal existed, patients have no way to find it. There is no communication to data principals identifying HealthBridge as a processor.
- Ground truth: non_compliant

**Gap 9: CM.WITHDRAW.1 — No consent withdrawal process for any data category (probing depth: 2)**
- Surface answer: `not_implemented` | Notes: "Consent withdrawal will be part of the Q3 rights portal."
- Reality: Since all data comes via hospital integrations, patients cannot identify HealthBridge as the processor they need to contact. Even if they did, there is no mechanism to withdraw consent for specific processing activities without withdrawing from the hospital's system. Deletion would require manual developer intervention in production databases.
- Ground truth: non_compliant

---

### Company 3: Dakshin Logistics Group — Large Manufacturing/Logistics Enterprise (2,800 employees)

**Archetype:** Competence in adjacent areas creating dangerous blind spots. Strong on GDPR (done GDPR work for EU operations), weak on DPDPA-specific requirements. Full-time DPO. ISO 27001. But their operational practices don't reach blue-collar workers, and their GDPR compliance creates false confidence for India.

**Assessment driver:** Anticipating DPB enforcement action (proactive regulatory audit prep).

**Industry:** `manufacturing` | **Size:** `large`

**Context profile:**
- risk_tier: HIGH
- sdf_candidate: true (4.2M principals)
- cross_border_transfers: true
- processes_children_data: false
- priority_chapters: chapter_2, chapter_3, cross_border, chapter_4

**Documents to create (5 docs):**
1. `Dakshin-Privacy-Policy-India-2025.pdf` — `privacy_policy` — professional, references DPDPA correctly, but worker-specific processing (GPS, performance scoring) described only at a high level
2. `Dakshin-Employee-Data-Processing-Notice-v2.docx` — `consent_form` — employment consent framed as mandatory condition; GPS tracking notice bundled with performance evaluation notice
3. `Dakshin-Cross-Border-Data-Transfer-Framework.docx` — `data_processing_agreement` — references EU SCCs and GDPR adequacy mechanisms, no DPDPA framework, Saudi Arabia not covered
4. `Dakshin-GPS-Location-Data-Policy-v3.pdf` — `security_policy` — describes operational necessity for GPS, states "during active duty hours," but implementation tracks 24/7
5. `Dakshin-Data-Grievance-Procedure-v1.docx` — `internal_sop` — describes web portal and email, no offline or phone channel

**Gaps to seed (9 gaps):**

**Gap 1: CH2.CONSENT.1 + CM.GRANULAR.1 — Employment consent is coerced, not freely given (probing depth: 4)**
- Surface answer: `fully_implemented` | Notes: "We have documented consent from all employees and drivers. Consent forms are signed during onboarding."
- Plant in employee notice: *"As a condition of your employment with Dakshin Logistics Group, you acknowledge and consent to the collection, processing, storage, and use of your personal data as described in this Employee Data Processing Notice. This includes your identity information, employment records, performance data, disciplinary records, and location data collected through the Driver App for operational, safety, and compliance purposes. By accepting employment, you confirm your understanding of and consent to these processing activities."*
- Reality: Sign this or don't get the job. Drivers cannot consent to route tracking but decline performance scoring. They cannot decline GPS tracking and remain employed. "Consent" obtained as a condition of employment is not freely given under DPDPA.
- Layer 4 follow-up: "Can a driver at Dakshin decline GPS tracking while remaining employed? Can they consent to identity processing but decline performance evaluation scoring? What happens to employment if they refuse the data processing consent form?"
- Ground truth: non_compliant

**Gap 2: CH2.MINIMIZE.1 + CH2.MINIMIZE.2 — GPS tracking is 24/7 and retention far exceeds purpose (probing depth: 4)**
- Surface answer: `fully_implemented` | Notes: "Our GPS policy describes data minimization. We retain location data for dispute resolution."
- Plant in GPS policy: *"Location data is collected from drivers using the Dakshin Driver App to support route optimization, delivery confirmation, driver safety monitoring, and compliance with customer service-level agreements. Data is collected continuously during active duty hours. Location records are retained for a period of 36 months for operational and legal dispute resolution purposes."*
- Cross-document contradiction: The GPS policy says "active duty hours" but the employee notice says "continuous" collection — the two documents contradict each other, and the technical implementation matches the employee notice (24/7).
- Reality: The app tracks every 15 seconds, 24 hours a day, 7 days a week — including nights, weekends, and leave days. 36-month retention for data whose stated purpose (dispute resolution) is satisfied in 30 days. 180,000 drivers × 3 years of 15-second GPS pings = massive unminimized dataset.
- Layer 4 follow-up: "What is the exact GPS ping interval? Do you collect location data outside work hours? Can you show me the technical configuration that stops tracking when a driver clocks out?"
- Ground truth: non_compliant

**Gap 3: CH2.NOTICE.2 — No retrospective notice to 4.2M pre-DPDPA data principals (probing depth: 3)**
- Surface answer: `planned` | Notes: "We updated our website privacy policy when DPDPA was enacted. Retrospective notice plan is under review."
- Reality: Dakshin has been collecting data for 8 years. When DPDPA came into force, they updated the website privacy policy. They sent no communication to existing employees, drivers, customers, or vendors. 4.2M data principals have never been informed of their rights under DPDPA.
- Absence: No document evidencing any retrospective notification campaign.
- Plant in privacy policy a "Revised November 2023" datestamp: *"This Privacy Policy was updated in November 2023 to reflect the requirements of the Digital Personal Data Protection Act, 2023. We have reviewed and updated our data processing practices to align with the new framework."* No mention of direct communication to existing data principals.
- Layer 3 follow-up: "How did you notify the 4.2M data principals whose data was collected before DPDPA came into force that they now have rights under the Act? What was the channel, timeline, and evidence of delivery?"
- Ground truth: non_compliant

**Gap 4: CB.TRANSFER.1 + CB.TRANSFER.2 + CB.TRANSFER.3 — GDPR SCCs used for DPDPA cross-border, Saudi Arabia completely undocumented (probing depth: 4)**
- Surface answer: `partially_implemented` | Notes: "We have an inter-company data transfer agreement with our UAE subsidiary. GDPR-compliant SCCs are in place."
- Plant in cross-border framework: *"This Data Transfer Framework governs the transfer of personal data between Dakshin Logistics Group entities and to third-party processors outside the European Economic Area and India. Transfers to Dakshin Middle East FZE (UAE) are governed by Standard Contractual Clauses as approved by the European Commission pursuant to Regulation (EU) 2016/679 (GDPR). Transfers are subject to the protections afforded by the UK-EU adequacy bridge and the adequacy decisions of the European Commission."*
- Reality: EU SCCs are an EU legal mechanism — not recognized under DPDPA Section 16. Saudi Arabia receives driver data via a shared ERP system with zero documentation. Framework has never been reviewed by Indian counsel. No DPDPA-compliant transfer mechanism exists for any jurisdiction.
- Layer 4 follow-up: "Your cross-border framework references EU SCCs. DPDPA's Section 16 cross-border transfer framework is independent of GDPR. What DPDPA-compliant mechanism do you rely on for transfers to UAE and Saudi Arabia?"
- Ground truth: non_compliant

**Gap 5: CH3.GRIEVANCE.1 + CH3.GRIEVANCE.2 — Grievance portal is inaccessible to blue-collar workers (probing depth: 3)**
- Surface answer: `fully_implemented` | Notes: "We have a dedicated DPO portal and email channel. The DPO is accessible."
- Plant in grievance procedure: *"Data principals may submit grievances or exercise their rights under the DPDPA by: (1) Submitting a request through the Data Protection Portal at privacy.dakshinlogistics.com (login required); (2) Emailing the DPO at dpo@dakshinlogistics.com; (3) Writing to the Data Protection Officer, Dakshin Logistics Group, [address]."*
- Reality: The portal requires a Dakshin corporate email login. Drivers and warehouse workers don't have corporate email. No WhatsApp, phone, QR code on delivery vests, physical form, or any accessible channel for ~180,000 blue-collar workers. Zero grievances received from drivers or warehouse workers in 2 years.
- Layer 3 follow-up: "A driver who doesn't have a corporate email wants to submit a data grievance. Walk me through exactly how they do that."
- Ground truth: non_compliant

**Gap 6: CH2.SECURITY.3 — Third-party logistics partner contracts have no data protection clauses (probing depth: 2)**
- Surface answer: `partially_implemented` | Notes: "We have data processing agreements with key technology vendors."
- Reality: ~40 third-party logistics subcontractors receive driver, customer, and delivery data via EDI/API integrations. None have DPAs — only commercial logistics agreements. DPO focused on technology vendors (AWS, SAP) but not the logistics partner ecosystem, which is the highest-risk category.
- Absence: No DPA template for logistics partners. Cross-border framework covers only technology vendors and subsidiaries.
- Layer 2 follow-up: "Do the 40+ third-party logistics subcontractors who receive driver and customer data via your EDI integrations have signed Data Processing Agreements?"
- Ground truth: non_compliant

**Gap 7: CH2.MINIMIZE.1 — Performance scoring algorithm uses undisclosed personal data (probing depth: 3)**
- Surface answer: `fully_implemented` | Notes: "Our performance scoring uses delivery metrics as described in the employee notice."
- Plant in employee notice: *"Performance data collected includes delivery completion rates, route adherence metrics, customer satisfaction scores, and safety compliance records. This information is used to evaluate driver performance, determine incentive eligibility, and inform personnel decisions."*
- Reality: The scoring algorithm also ingests: time-of-day patterns (implying lifestyle inferences), social network data from the app (which drivers interact with), personal device type and app version (used as a proxy for "tech savvy" in promotion decisions), and location data during rest periods (to infer whether drivers are moonlighting). None of this is disclosed.
- Layer 3 follow-up: "Provide the complete list of data inputs to your driver performance scoring algorithm and map each input to the disclosure in the employee data processing notice."
- Ground truth: non_compliant

**Gap 8: CH4.SDF.1 — DPO reports to General Counsel, not independent (probing depth: 2)**
- Surface answer: `fully_implemented` | Notes: "We have a full-time, qualified DPO who has been in role for 18 months."
- Reality: The DPO reports to the General Counsel, who is also the legal head for business transactions the DPO may need to scrutinize. The GC has pressured the DPO to approve data sharing arrangements the DPO flagged as non-compliant. No direct Board access. Structural independence issue.
- Absence: No board charter establishing DPO independence or direct Board reporting access.
- Layer 2 follow-up: "If the DPO raises a compliance concern about a processing activity the General Counsel has approved commercially, what is the escalation path and who makes the final decision?"
- Ground truth: partially_compliant

**Gap 9: CH2.NOTICE.1 — Driver privacy notice uses inaccessible technical language (probing depth: 2)**
- Surface answer: `fully_implemented` | Notes: "All employees and drivers receive our data processing notice at onboarding."
- Plant in employee notice: a document written in formal corporate English with legal terminology — "data principal," "data fiduciary," "legitimate interest," "processing activities," "retention schedule" — approximately Grade 12 reading level. Drivers typically complete education to Grade 8-10 level. The notice is 8 pages, A4 format, in 10pt Times New Roman.
- Reality: DPDPA requires notice in "clear and plain language." A technically present but practically incomprehensible notice is not effective notice.
- Layer 2 follow-up: "Has the driver data processing notice been tested for readability with the actual audience? What steps have you taken to ensure it is understandable to employees with lower literacy levels?"
- Ground truth: partially_compliant

---

## Technical Requirements

### Script structure

Keep the existing scaffolding exactly. The script must:
1. Import from the same modules as the existing script
2. Use `build_document()` for all synthetic document text — documents must be 500-2000 words and pass word count validation
3. Have `novapay_fixture()`, `healthbridge_fixture()`, `dakshin_fixture()` functions returning a dict with keys: `company_name`, `industry`, `company_size`, `description`, `context_answers`, `context_profile`, `documents`, `responses`, `coverage`, `findings`, `hidden_gaps`
4. `responses` must be a dict mapping every requirement_id from `get_all_requirements()` to a response dict with `answer`, optionally `notes`, `evidence_reference`, `na_reason`, `confidence`
5. `findings` must be 10-20 DeskReviewFinding dicts with keys: `finding_type`, `requirement_id`, `document_key`, `content`, `severity`, `source_quote`, `source_location`
6. Script must be idempotent (purge and re-create by company name)
7. Run with: `cd ~/dpdpa-gap-tool && python scripts/seed_test_companies.py`

### Finding type distribution per company

Each company should have a mix:
- **evidence** findings (10-15): quotes from documents that appear compliant — the "surface" layer
- **absence** findings (5-8): requirements with zero document coverage (these should trigger "absence detection" in the tool)
- **signal** findings (3-5): red flags like template artifacts (GDPR references in Indian policy), internal contradictions between documents, language that sounds compliant but isn't

### Questionnaire response strategy

For each of the 41 requirements:
- **Gap requirements**: Use the surface answer specified above (usually `fully_implemented` or `partially_implemented`) with optimistic notes
- **Non-gap requirements**: Assign realistic answers reflecting the company's archetype
  - NovaPay: strong on security requirements (CH2.SECURITY.*), average on consent/notice/rights
  - HealthBridge: weak across the board, some `not_implemented` for requirements they haven't touched
  - Dakshin: strong on governance (CH4.*) and security, weak on operational practices for workers

### Ground truth manifest

Write `scripts/test_ground_truth.json` after seeding. Format:

```json
{
  "companies": [
    {
      "company_name": "...",
      "assessment_id": "<uuid assigned during seed>",
      "hidden_gaps": [
        {
          "requirement_ids": ["CH2.CONSENT.1", "CH2.CONSENT.2"],
          "surface_answer": "fully_implemented",
          "actual_status": "non_compliant",
          "gap_description": "...",
          "evidence_in_document": "filename.pdf",
          "evidence_quote_hint": "the planted quote that reveals the gap",
          "probing_depth": 3,
          "what_followup_should_ask": "..."
        }
      ]
    }
  ]
}
```

### Validation

`verify_counts()` checks: 3-5 documents per company, 10-20 findings per company, all 41 requirement IDs covered in responses. Ensure these pass.

**Note:** NovaPay and HealthBridge have 4 documents each. Dakshin has 5. All are within the 3-5 range enforced by validation. If you want to add a 5th document to NovaPay or HealthBridge to add more cross-document contradictions, that is allowed — do not exceed 5.

---

## What makes this different from the existing script

The existing script has ~5 gaps per company at probing depth 2-3. This new version must have **8-9 gaps per company at probing depth 2-4**, with:
- **Cross-document contradictions**: A document says X, another doc implies not-X (e.g., GPS policy says "active duty hours" but employment notice says "continuous")
- **Layered absences**: Some gaps surface only because a required document is completely absent (no DPA with processors) — not because an existing document is flawed
- **DPDPA-specific traps**: Gaps that a GDPR-compliant company would miss because DPDPA differs (under-18 vs under-13, SCCs not recognized under DPDPA, employment consent coercion)
- **Operational reality gaps**: Gaps between what the policy says and how the technical system actually works (24/7 vs "active duty" GPS, manual deletion vs "automated" rights process)
- **Audience accessibility gaps**: Technically compliant in form, non-compliant in substance (notices inaccessible to intended audience, grievance channels that workers can't use)
