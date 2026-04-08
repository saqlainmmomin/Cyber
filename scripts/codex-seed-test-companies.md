# Codex Task: Seed Test Companies with Hidden Compliance Gaps

## Objective

Create a Python script (`scripts/seed_test_companies.py`) that populates the CyberAssess database with 3 fictitious companies. Each company has:

- Realistic organizational context
- Uploaded "documents" with synthetic policy/procedure text (stored as `extracted_text` — no actual files)
- Questionnaire responses where the company self-assesses **optimistically**
- Desk review findings (evidence, absences, signals) derived from the documents
- A **ground truth manifest** documenting what the tool *should* find if its probing and analysis work correctly

The purpose is to test the tool's ability to:
1. **Infer real compliance state** from document text (not just keyword matching)
2. **Generate follow-up questions** that expose hidden gaps
3. **Produce actionable output** (gap reports, RFIs) that identifies the real issues

---

## Critical Design Principle: Gaps Must Be Hidden

**DO NOT create obviously non-compliant data.** Every company should look compliant on the surface. The gaps should only emerge through:

- **Cross-referencing** documents against questionnaire answers (contradictions)
- **Follow-up probing** when answers are vague or don't match evidence
- **Reading between the lines** in document text (right keywords, wrong substance)

Each gap should require 1-3 layers of probing to surface:

| Layer | What it looks like |
|---|---|
| **Surface** | Questionnaire answer says "fully_implemented" or "partially_implemented" |
| **Document text** | Policy exists and mentions the right topic, but substance is flawed |
| **Follow-up probe** | Asking "how exactly?" reveals the actual gap |

---

## Company Profiles

### Company 1: "NovaPay Solutions Pvt. Ltd." — The Overconfident Fintech

**Profile:**
- Industry: `fintech`
- Size: `sme` (200 employees)
- 2.5M data principals (payment users)
- Processes financial data, identity data, behavioral data (transaction patterns)
- Cross-border transfers to AWS Singapore + Stripe US
- Has ISO 27001 certification (security is genuinely strong)
- No dedicated DPO — CISO doubles as DPO
- Recently passed SOC 2 Type II — believes this covers DPDPA too
- Assessment driver: `customer_due_diligence` (enterprise client asked for DPDPA compliance proof)

**Gap archetype: Policy-practice divergence**

NovaPay has all the right documents. Their privacy policy mentions consent, data minimization, breach notification — all the keywords. But the implementation doesn't match:

**Hidden gaps to seed (with layered evidence):**

1. **CH2.CONSENT.1 + CH2.CONSENT.2 (Consent Management)**
   - Surface: Questionnaire says `fully_implemented`
   - Document: Privacy policy states "We obtain consent for all processing activities"
   - Hidden reality: Consent is a single checkbox during onboarding ("I agree to Privacy Policy and Terms of Service"). No separate consent per purpose. Users can't consent to payments processing while declining marketing analytics.
   - Evidence to plant: The privacy policy text should contain phrases like "By using our services, you consent to the collection and processing of your data as described in this policy" — this is bundled consent, not itemised.
   - Follow-up should reveal: No granular consent mechanism exists. The single checkbox covers 7 different processing purposes.

2. **CH2.MINIMIZE.2 + CH2.MINIMIZE.3 (Data Retention)**
   - Surface: Questionnaire says `partially_implemented`
   - Document: Data retention policy exists and says "Data is retained as per regulatory requirements"
   - Hidden reality: The retention policy is a 2-paragraph generic statement. No specific retention periods per data category. In practice, they never delete anything because "RBI might ask for it."
   - Evidence to plant: Retention policy text should reference "applicable regulatory requirements" without specifying what those requirements are or what the actual retention periods are for each data category.
   - Follow-up should reveal: No automated deletion. No retention schedule. Financial records and marketing data are both retained indefinitely.

3. **CB.TRANSFER.1 + CB.TRANSFER.2 (Cross-Border Transfers)**
   - Surface: Questionnaire says `fully_implemented`
   - Document: Privacy policy mentions "data may be stored on servers outside India"
   - Hidden reality: No inventory of cross-border flows. AWS Singapore and Stripe US are known, but they also use Mixpanel (US), Intercom (US), and Google Analytics — none documented. No contractual safeguards beyond standard cloud ToS.
   - Evidence to plant: Privacy policy should say "Your data may be transferred to and processed in countries other than India where our service providers operate" — acknowledges transfers exist but no specifics.
   - Follow-up should reveal: When asked to list all cross-border flows, they can only name AWS and Stripe. No DPA/SCCs with any processor.

4. **CM.GRANULAR.2 (No consent bundling)**
   - Surface: Questionnaire says `fully_implemented` — they believe users can opt out
   - Document: Terms of Service says users can unsubscribe from marketing emails
   - Hidden reality: Unsubscribing from emails is not the same as withdrawing consent for behavioral analytics. Users cannot use the payment service without agreeing to all data processing.
   - Evidence to plant: ToS text should include "You may opt out of promotional communications at any time" but also "Use of our payment services constitutes acceptance of our data processing practices."
   - Follow-up should reveal: There is no way to use the core service without consenting to analytics tracking.

5. **BN.NOTIFY.3 (Incident Response Plan)**
   - Surface: Questionnaire says `fully_implemented` — they have an IR plan from their ISO 27001 program
   - Document: Incident response SOP exists, references NIST framework
   - Hidden reality: The IR plan is a security incident plan, not a *personal data breach* plan. It covers system downtime and malware but has no procedures for notifying the Data Protection Board or affected data principals. No classification of what constitutes a "personal data breach" vs. a security incident.
   - Evidence to plant: IR plan text should detail containment, eradication, recovery steps but notification section should only mention "notify the CISO and IT team" — no mention of Data Protection Board, no mention of data principals, no 72-hour notification requirement.
   - Follow-up should reveal: Nobody knows what the DPB notification format is. There's no template. The IR plan doesn't distinguish between a server outage and a data breach involving personal data.

---

### Company 2: "HealthBridge Analytics" — The Checkbox Startup

**Profile:**
- Industry: `healthcare`
- Size: `startup` (35 employees)
- 180K data principals (patients via hospital partnerships)
- Processes health records, identity, financial (billing)
- Handles children's data (pediatric records through partner hospitals)
- No cross-border transfers (all India infra)
- No security certification
- DPO is "the CEO"
- Assessment driver: `investor_board_requirement` (Series A investors asked for DPDPA readiness)

**Gap archetype: Nominal compliance — everything exists in the most minimal form possible**

HealthBridge has technically done something for every requirement. But every implementation is the bare minimum checkbox version that wouldn't survive scrutiny:

**Hidden gaps to seed:**

1. **CH2.CONSENT.5 + CH4.CHILD.1 + CH4.CHILD.2 + CH4.CHILD.3 (Children's Data)**
   - Surface: Questionnaire says `partially_implemented` — they know children's data is sensitive
   - Document: Privacy policy has a section titled "Children's Privacy" that says "We do not knowingly collect data from children under 13"
   - Hidden reality: The threshold is wrong (DPDPA says under 18, not 13 — they copied this from a US COPPA-compliant template). They process pediatric records which inherently involve children. No age verification mechanism exists. No parental consent mechanism — they rely on hospitals to obtain consent.
   - Evidence to plant: The privacy policy children's section should reference "under 13" and say "if we discover we have collected data from a child under 13, we will delete it." Also include a partner agreement template that says "Partner hospitals are responsible for obtaining all necessary consents."
   - Follow-up should reveal: They have no mechanism to verify age. They have no mechanism to obtain parental consent directly. They rely entirely on hospital partners, but the hospital agreements don't specifically mention DPDPA parental consent requirements.

2. **CH4.SDF.1 (Data Protection Officer)**
   - Surface: Questionnaire says `fully_implemented` — "Our CEO handles data protection matters"
   - Document: Board resolution mentions "The CEO shall serve as the Data Protection Officer"
   - Hidden reality: The CEO has no training in data protection. No dedicated time allocated to DPO functions. The CEO also decides what data to collect (conflict of interest — DPO should be independent). No reporting mechanism to the Board of Directors on data protection matters.
   - Evidence to plant: Board resolution should say "RESOLVED that [CEO Name], in his capacity as Chief Executive Officer, shall also discharge the functions of Data Protection Officer as required under applicable law."
   - Follow-up should reveal: The CEO spends zero hours per week on DPO duties. There's no data protection reporting to the board. The CEO decides both what data to collect AND serves as the oversight function.

3. **CH3.ACCESS.1 + CH3.CORRECT.1 + CH3.CORRECT.2 (Data Principal Rights)**
   - Surface: Questionnaire says `partially_implemented` — "We respond to requests via email"
   - Document: Privacy policy says "You may contact us at privacy@healthbridge.in for any data-related requests"
   - Hidden reality: There's no structured process. The email goes to a shared inbox checked by a junior developer. No SLA. No tracking. They've received 3 requests in the past year and responded to 1. No mechanism to actually export or delete data from their MongoDB collections.
   - Evidence to plant: Privacy policy should have the standard "contact us" language. Internal SOP (if any) should be absent — this is an absence the tool should detect.
   - Follow-up should reveal: Average response time to the 3 requests received was "we never tracked it." They have no automated data export function. Deletion requires a developer to manually run database queries.

4. **CH2.SECURITY.3 (Data Processor Contracts)**
   - Surface: Questionnaire says `fully_implemented`
   - Document: Master services agreement template exists
   - Hidden reality: The MSA template is a generic business agreement with no data protection clauses. No DPA (Data Processing Agreement) with any of their 8 sub-processors (AWS, MongoDB Atlas, Razorpay, SendGrid, etc.). They treat cloud ToS as sufficient.
   - Evidence to plant: MSA template text should cover payment terms, SLAs, IP ownership — but the data protection section should be a single sentence: "Service Provider shall implement reasonable security measures to protect Client data."
   - Follow-up should reveal: When asked for a Data Processing Agreement with any processor, they have none. "Reasonable security measures" is undefined. No audit rights over processors.

5. **CH2.NOTICE.1 (Privacy Notice)**
   - Surface: Questionnaire says `fully_implemented` — they have a privacy policy on their website
   - Document: Privacy policy exists, 4 pages long, mentions DPDPA
   - Hidden reality: The privacy policy is a copy-pasted template from a legal template website. It references "GDPR" and "EU Data Subjects" in two places (they forgot to remove these). The purposes listed are generic ("to improve our services, to communicate with you"). The policy doesn't describe the specific types of health data they process or mention hospital partnerships.
   - Evidence to plant: The policy text should contain tell-tale template artifacts: references to "GDPR", "EU data subjects", "California Consumer Privacy Act", generic purpose descriptions. The data types section should list "name, email, phone number" but not mention health records, diagnostic data, or treatment histories.
   - Follow-up should reveal: The privacy policy doesn't mention health data at all. It doesn't describe the hospital partnership data flow. Patients whose data is processed through hospital integrations never see this privacy policy.

---

### Company 3: "Dakshin Logistics Group" — The Sophisticated-but-Incomplete Enterprise

**Profile:**
- Industry: `manufacturing` (logistics/supply chain)
- Size: `large` (2,800 employees)
- 4.2M data principals (drivers, warehouse workers, customers, vendors)
- Processes identity, financial, location (real-time GPS tracking of drivers), behavioral (delivery performance scoring)
- Cross-border: shares driver data with Middle East operations (UAE, Saudi Arabia)
- ISO 27001 certified, SOC 2 Type I in progress
- Full-time DPO appointed (reports to General Counsel)
- Has been through a GDPR assessment for EU-facing operations
- Assessment driver: `regulatory_audit_prep` (anticipating DPB enforcement)

**Gap archetype: Competence in adjacent areas creating blind spots**

Dakshin is genuinely strong on governance (Chapter 4) and security (Chapter 2 security section). They've done GDPR work and know compliance. But they have blind spots in areas where DPDPA differs from GDPR, and in operational practices that their governance frameworks don't reach:

**Hidden gaps to seed:**

1. **CH2.CONSENT.1 + CM.GRANULAR.1 (Employee/Driver Consent)**
   - Surface: Questionnaire says `fully_implemented` — they have consent forms for customers and vendors
   - Document: Customer consent form is well-drafted. Employee data processing notice exists.
   - Hidden reality: Consent from employees (especially drivers) is obtained as a condition of employment — sign this or don't get the job. This isn't "free" consent under DPDPA. GPS tracking consent is bundled with employment consent. Drivers can't consent to route tracking while declining performance scoring.
   - Evidence to plant: Employment data processing notice should say "As a condition of your employment, you acknowledge and consent to the collection and processing of your personal data as described herein, including real-time location tracking for route optimization and performance evaluation."
   - Follow-up should reveal: Drivers cannot opt out of performance scoring while remaining employed. There's no alternative to GPS tracking. Consent is effectively coerced.

2. **CH2.MINIMIZE.1 (Data Minimization — Location Data)**
   - Surface: Questionnaire says `fully_implemented` — they believe GPS tracking is necessary
   - Document: GPS tracking policy exists, references operational necessity
   - Hidden reality: GPS tracking continues when drivers are off-duty (the app doesn't distinguish between work hours and personal time). Location data is retained for 3 years ("for dispute resolution") even though delivery disputes are resolved within 30 days. The tracking granularity (every 15 seconds) far exceeds what's needed for route optimization.
   - Evidence to plant: GPS policy should state "Location data is collected to ensure delivery efficiency, driver safety, and compliance with service-level agreements." It should mention "continuous tracking during active duty hours" but the actual app configuration tracks 24/7. The retention clause should say "Location data is retained for a period of 36 months for operational and legal purposes."
   - Follow-up should reveal: 15-second GPS ping interval. 24/7 tracking including off-duty hours. 3-year retention for data that has no purpose after 30 days. None of this is mentioned in the consent form drivers sign.

3. **CH3.GRIEVANCE.1 + CH3.GRIEVANCE.2 (Grievance Mechanism for Blue-Collar Workers)**
   - Surface: Questionnaire says `fully_implemented` — they have a grievance portal
   - Document: Data protection grievance procedure references an online portal and email
   - Hidden reality: The grievance portal is a web application that requires a corporate email login. Warehouse workers and drivers don't have corporate email accounts. The email address (dpo@dakshinlogistics.com) is on the website but not on any communication drivers receive. In practice, blue-collar workers have no accessible channel.
   - Evidence to plant: Grievance procedure should describe "Data principals may submit grievances through the DPO portal at privacy.dakshinlogistics.com or by emailing dpo@dakshinlogistics.com." No mention of phone, physical form, WhatsApp, or any channel accessible to workers without internet/email.
   - Follow-up should reveal: Of 4.2M data principals, ~180K are drivers and warehouse workers. None of them have access to the grievance portal. Zero grievances have been received from this population. The grievance procedure was designed for B2B customers, not blue-collar workers.

4. **CH2.NOTICE.2 (Notice for Previously Collected Data)**
   - Surface: Questionnaire says `planned` — they're aware of the requirement
   - Document: No document exists for this (desk review should flag absence)
   - Hidden reality: Dakshin has been collecting driver location data and employee data for 8 years. When DPDPA came into effect, they updated their website privacy policy but never informed existing employees, drivers, or customers whose data was collected under the old regime. They believe updating the website is sufficient.
   - Evidence to plant: NO document for retrospective notice. The updated privacy policy on the website should have a "Last Updated" date after DPDPA enactment. But there should be no evidence of any communication to existing data principals about the change.
   - Follow-up should reveal: 4.2M data principals whose data was collected pre-DPDPA have never been notified. Website update is not equivalent to individual notice. No plan to send retrospective notices.

5. **CB.TRANSFER.2 + CB.TRANSFER.3 (Cross-Border — Middle East)**
   - Surface: Questionnaire says `partially_implemented` — they know they transfer data
   - Document: Inter-company data sharing agreement with UAE subsidiary exists
   - Hidden reality: The agreement was drafted for GDPR adequacy (references "Standard Contractual Clauses" and "EU Commission adequacy decisions") but doesn't reference DPDPA or Indian law at all. The Central Government's restricted countries list hasn't been checked. Saudi operations receive driver data via a shared ERP system with no specific data transfer agreement.
   - Evidence to plant: The inter-company agreement should explicitly reference "Regulation (EU) 2016/679" and "Standard Contractual Clauses as approved by the European Commission." It should cover UAE transfers but not mention Saudi Arabia at all. No reference to DPDPA or Section 16.
   - Follow-up should reveal: The DPDPA cross-border framework is different from GDPR. SCCs are an EU mechanism, not recognized under DPDPA. Saudi transfers are completely undocumented. They assumed GDPR compliance implies DPDPA compliance for cross-border.

---

## Technical Specification

### Database Connection

```python
from app.database import SessionLocal, engine, Base
from app.models.assessment import Assessment, AssessmentDocument
from app.models.questionnaire import QuestionnaireResponse
from app.models.report import GapReport, GapItem
from app.models.desk_review import DeskReviewSummary, DeskReviewFinding
```

Database is SQLite at `data/dpdpa.db`. Use `SessionLocal()` to get a session.

### Assessment Model Fields

```python
Assessment(
    id=str,              # UUID string, use uuid.uuid4()
    company_name=str,
    industry=str,        # Enum: it_services, fintech, healthcare, ecommerce, manufacturing, education, other
    company_size=str,    # Enum: startup, sme, large, enterprise
    description=str,     # Optional
    status=str,          # "context_gathered" — these have gone through context phase
    context_answers=str, # JSON string — list of {"question_id": "CTX.xxx", "answer": "value"} dicts
    context_profile=str, # JSON string — risk profile dict with keys: risk_tier, priority_chapters, likely_not_applicable, industry_context, sdf_candidate, cross_border_transfers, processes_children_data
)
```

### Context Questions

The context answers must use IDs from `app/dpdpa/context_questions.py`. The 16 questions span 4 blocks:
- `CTX.DATA.1` through `CTX.DATA.4a` — data landscape
- `CTX.POSTURE.1` through `CTX.POSTURE.4` — existing posture
- `CTX.RISK.1` through `CTX.RISK.3` — risk exposure
- `CTX.INIT.1` through `CTX.INIT.3` — initiative context

### AssessmentDocument Model Fields

```python
AssessmentDocument(
    id=str,                # UUID
    assessment_id=str,     # FK to Assessment
    filename=str,          # e.g., "Privacy-Policy-NovaPay-2025.pdf"
    file_path=str,         # Use "seeded/{assessment_id}/{filename}" — no actual file needed
    file_type=str,         # "pdf" or "docx"
    document_category=str, # Enum: privacy_policy, consent_form, data_flow_diagram, security_policy, internal_sop, data_processing_agreement, retention_policy, breach_response_plan, other
    extracted_text=str,    # THE KEY FIELD — full synthetic document text with planted evidence
)
```

**Important:** The `extracted_text` is what the tool actually analyzes. Write realistic, multi-paragraph document text — not bullet points. Include the right compliance keywords but with subtly flawed substance as specified in each company's gap descriptions.

### QuestionnaireResponse Model Fields

```python
QuestionnaireResponse(
    id=str,
    assessment_id=str,
    question_id=str,       # e.g., "CH2.CONSENT.1"
    answer=str,            # One of: fully_implemented, partially_implemented, planned, not_implemented, not_applicable
    notes=str,             # Optional — company's self-assessment notes (write these optimistically)
    evidence_reference=str,# Optional — what the company cites as evidence
    na_reason=str,         # Optional — only if answer is not_applicable
    confidence=str,        # Optional — strong, moderate, weak
)
```

The 41 requirement IDs are listed in `app/dpdpa/questionnaire.py`. Every company should have a response for each requirement. Answers should be **optimistic** — the company believes they're more compliant than they are.

### DeskReviewSummary Model Fields

```python
DeskReviewSummary(
    assessment_id=str,
    document_catalog=str,  # JSON string — list of {"filename": "...", "type": "...", "pages": N} dicts
    coverage_summary=str,  # JSON string — dict mapping requirement_id to "adequate"|"partial"|"absent"
    status="completed",
    started_at=datetime,
    completed_at=datetime,
)
```

### DeskReviewFinding Model Fields

```python
DeskReviewFinding(
    assessment_id=str,
    finding_type=str,      # "evidence" | "absence" | "signal"
    requirement_id=str,    # Which DPDPA requirement this relates to (nullable for cross-cutting signals)
    document_id=str,       # FK to AssessmentDocument (nullable)
    content=str,           # Human-readable finding description
    severity=str,          # "info" | "low" | "medium" | "high" | "critical"
    source_quote=str,      # Exact quote from document (for evidence type)
    source_location=str,   # "Page 3, Section 2.1" or similar
)
```

**Finding types:**
- `evidence`: Document text that supports compliance with a requirement
- `absence`: A requirement has NO supporting evidence in any document
- `signal`: A red flag or concern found in document text (template artifacts, GDPR references in Indian context, etc.)

### Ground Truth Manifest

At the end of the script, write a JSON file `scripts/test_ground_truth.json` with the expected findings:

```json
{
  "companies": [
    {
      "company_name": "NovaPay Solutions Pvt. Ltd.",
      "assessment_id": "<uuid>",
      "hidden_gaps": [
        {
          "requirement_ids": ["CH2.CONSENT.1", "CH2.CONSENT.2"],
          "surface_answer": "fully_implemented",
          "actual_status": "non_compliant",
          "gap_description": "Consent is a single bundled checkbox covering 7 purposes. No itemised consent.",
          "evidence_in_document": "Privacy-Policy-NovaPay-2025.pdf",
          "evidence_quote_hint": "By using our services, you consent to...",
          "probing_depth": 2,
          "what_followup_should_ask": "How do you obtain separate consent for each processing purpose? Can users consent to payments but decline marketing analytics?"
        }
      ]
    }
  ]
}
```

### Script Requirements

1. **Idempotent:** The script should check if seeded companies already exist (by company name) and skip or overwrite them
2. **Self-contained:** No Claude API calls. All data is deterministic.
3. **Runnable:** `python scripts/seed_test_companies.py` from the project root
4. **Verbose:** Print what's being created as it runs
5. **Complete:** Each company needs:
   - 1 Assessment record
   - 3-5 AssessmentDocument records with full synthetic document text
   - 41 QuestionnaireResponse records (one per requirement)
   - 1 DeskReviewSummary record
   - 10-20 DeskReviewFinding records (mix of evidence, absence, signal)
   - Ground truth entry in the manifest

### Synthetic Document Text Guidelines

Each document should be 500-2000 words of realistic corporate text. Key principles:

- **Privacy policies** should read like real privacy policies — formal language, section headings, legal disclaimers
- **Internal SOPs** should read like real procedures — numbered steps, responsible parties, approval workflows
- **Template artifacts are intentional** — for HealthBridge specifically, leave in GDPR/CCPA references that signal copy-paste
- **The gap should be in what's missing or subtly wrong, not in what's obviously broken**

Example of GOOD planted evidence (subtle):
> "We obtain consent from all users during the account registration process. Users are presented with our Privacy Policy and Terms of Service and must indicate their acceptance before proceeding."

(This sounds compliant but describes bundled consent — the gap is in the structure, not the intent.)

Example of BAD planted evidence (too obvious):
> "We do not obtain consent from users."

(This defeats the purpose — the tool doesn't need to probe if the gap is this obvious.)

---

## File Locations

- Script: `scripts/seed_test_companies.py`
- Ground truth: `scripts/test_ground_truth.json`
- Both files should be committed to git

## Reference Files

Read these files for complete schema and logic understanding:

- `app/dpdpa/framework.py` — all 41 requirements, dependency DAG, root cause clusters
- `app/dpdpa/questionnaire.py` — question text for all 41 requirements, answer options
- `app/dpdpa/context_questions.py` — 16 context questions across 4 blocks
- `app/models/assessment.py` — Assessment + AssessmentDocument models
- `app/models/questionnaire.py` — QuestionnaireResponse model
- `app/models/report.py` — GapReport + GapItem models
- `app/models/desk_review.py` — DeskReviewSummary + DeskReviewFinding models
- `app/database.py` — database connection setup
- `app/services/followup_engine.py` — how follow-up questions are triggered (the probing logic you're testing)
- `app/services/question_engine.py` — how desk review findings modulate the questionnaire
- `CLAUDE.md` — project overview and architecture
