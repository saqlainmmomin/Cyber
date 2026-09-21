# CyberAssess Product Requirements

**Status:** Target product contract  
**Date:** 2026-09-21  
**Initial market:** Boutique GRC consulting firms  
**Canonical engagement type:** Regulatory gap assessment

## Product thesis

CyberAssess is a consultant-operated assessment execution workspace. It analyses client evidence to help consultants complete regulatory questionnaires and produce defensible, multi-framework compliance conclusions, reports, and remediation plans.

Evidence analysis is an input engine, not the product outcome. The assessment questionnaire is the consultant's primary working surface and system of record. The output is a set of consultant-approved conclusions about assessed compliance posture, bounded by a named framework and version, scope, assessment period, and evidence cut-off date.

CyberAssess does not provide independent legal advice, declare legal compliance, issue certification, or perform attestation. Its outputs must never imply otherwise.

---

## Product boundaries

### In scope for the first release

- A consultant workspace organized as Client → Engagement → Assessment.
- Regulatory gap assessments with one or more launch assessment packs. The same Assessment, Evidence, Conclusion, Finding, and Action primitives must support later internal-audit, vendor-assessment, risk-assessment, and validation Engagement types without treating their methods or deliverables as interchangeable.
- Consultant and scoped client evidence collection, including written responses and screenshots.
- A general, versioned evidence library with provenance, citations, reuse controls, and impact tracking.
- Manual, read-only AWS evidence snapshots from AWS Config and Security Hub.
- Evidence-informed questionnaires, AI-proposed assessments, consultant conclusions, findings, and actions.
- Reviewer-ready workpapers, client-ready integrated reports, and a consultant-operated action tracker.
- Portfolio visibility, reassessment, archive, and retention-aware permanent deletion.

### Deferred

- Client user accounts or a general self-service client portal.
- Continuous cloud monitoring or unattended recurring collection.
- Broad cloud, identity, ticketing, or SaaS integrations.
- Client-authored methodology packs or spreadsheet/CSV framework imports.
- Mandatory maker-checker separation.
- Client-managed remediation workflows.
- Autonomous legal-compliance declarations, certification, or attestation.
- A blended score across unlike frameworks or assessment scopes.
- Enterprise administration beyond the minimum needed to identify internal actors and enforce scoped access.

---

## Target users

### Consultant operator

Creates clients and engagements, defines scope, requests and collects evidence, completes the questionnaire, reviews AI proposals, approves conclusions, produces reports, and operates remediation tracking. The same consultant may prepare and approve conclusions in v1; the system still records both acts.

The workflow is optimized for a boutique GRC firm and must remain simple for a small team. Its traceability, review, and evidence controls should still be credible to a larger professional-services firm without importing enterprise administration into v1.

### Consulting reviewer

Uses the same internal workspace capabilities to inspect evidence, citations, judgment history, and reports. A separate reviewer is optional in v1 rather than a mandatory control.

### Client contributor

Uses an expiring, engagement-scoped magic link to answer specific evidence requests and upload requested material without creating an account. A client contributor cannot browse the engagement, questionnaire, conclusions, or other evidence.

### Product pack curator

Maintains versioned assessment packs and their provenance. Pack publication is a product-team function, not a client capability.

### Workspace administrator

Manages only the internal identities, workspace settings, and retention configuration required for a boutique-firm deployment. Complex enterprise role administration is deferred.

---

## Terminology

| Term | Definition |
|---|---|
| Workspace | The consulting firm's operating boundary. |
| Client | An assessed organization or contracting customer. A Client may have many Engagements. |
| Engagement | A contracted body of work with one purpose, lifecycle, deadlines, evidence library, selected findings, and actions. |
| Assessment | A conclusion-bearing examination within an Engagement, with its own type, framework versions, scope, period, evidence cut-off, applicability, questionnaire, and report. |
| Assessment pack | A curated, published, versioned methodology containing framework requirements, questions, applicability rules, evidence guidance, and deterministic scoring rules where used. |
| Requirement | A framework-specific obligation, control, outcome, or assessment point from a particular pack version. |
| Response | The client's or consultant's factual answer to a questionnaire prompt. It is not a compliance conclusion. |
| Evidence | A logical record of material that may support analysis, such as a document, screenshot, written response, or AWS snapshot. |
| Evidence version | An immutable received or collected representation of Evidence, with provenance, content hash, original scope, dates, and extraction state. |
| Citation | A precise pointer from an analysis claim or conclusion to one Evidence version and location. |
| Evidence request | A client-facing request for information. One request item may map to many requirements. |
| Analysis claim | A source-grounded statement extracted or inferred from evidence, with citations and quality dimensions. It remains machine-proposed until reviewed. |
| Conclusion | The consultant-approved outcome for one applicable Requirement in one Assessment. |
| Finding | An approved, reportable gap or observation derived from a Conclusion and bound to its Assessment origin. |
| Action | A remediation activity that may address one or more Findings and roll up to the Engagement. |
| Workpaper | The reviewer-oriented record of responses, evidence, claims, proposals, edits, decisions, and approvals. |

The product must avoid using `project` as a synonym for Client, Engagement, or Assessment.

---

## Product hierarchy and invariants

```text
Consultant workspace
└── Client
    └── Engagement
        ├── Assessment(s)
        │   ├── Scope and applicability
        │   ├── Framework questionnaire
        │   ├── Evidence and responses
        │   ├── Analysis and conclusions
        │   └── Assessment report
        ├── Shared evidence library
        ├── Consolidated findings
        ├── Remediation tracker
        └── Integrated engagement report
```

The following invariants govern all requirements:

1. A Client may have multiple Engagements; an Engagement may have multiple Assessments.
2. Assessments within one Engagement may differ in type, pack/version, legal entity, business unit, geography, product, system, cloud account, process, data type, period, cut-off date, applicability, and exclusions.
3. Evidence, evidence requests, selected Findings, Actions, deadlines, and operational status may roll up to an Engagement.
4. A Conclusion never rolls up or transfers. It remains bound to its originating Assessment, pack version, Requirement, scope, assessment period, and evidence cut-off.
5. Engagement reporting may consolidate selected approved Findings and Actions but may not create a blended compliance score.
6. Evidence reuse is explicit. Prior evidence may be suggested; prior Conclusions may not be copied or silently carried forward.
7. AI output is always a proposal. Only a consultant decision becomes a final Conclusion.
8. Deterministic calculations and methodology rules remain separate from qualitative AI analysis and human judgment.

---

## Domain model

### Core records

- `Workspace` owns internal actors, configuration, and Clients.
- `Client` owns Engagements and client-level evidence reuse eligibility.
- `Engagement` records engagement type, owner, contractual dates, deadlines, archive state, shared evidence, rollups, and report snapshots.
- `Assessment` records assessment type, lifecycle, scope, period, evidence cut-off, and pack selections.
- `AssessmentPackVersion` records pack identifier, edition/effective date, product revision, source provenance, publication state, and content/licensing approval.
- `AssessmentRequirement` records the selected Requirement, applicability decision, rationale, and framework-specific state.
- `RequirementResponse` records factual answers and revisions independently from Conclusions.
- `Evidence`, `EvidenceVersion`, `EvidenceUse`, and `Citation` provide reusable, immutable, many-to-many evidence semantics.
- `EvidenceRequest`, `EvidenceRequestItem`, and `UploadGrant` provide deduplicated collection and scoped client contribution.
- `AnalysisRun` and `AnalysisClaim` preserve provider-independent machine output and its provenance.
- `Conclusion`, `ConclusionRevision`, and `ApprovalEvent` preserve proposal, edits, decision, rationale, evidence set, and approval history.
- `Finding` preserves the reportable assessment-origin gap or observation.
- `Action`, `ActionUpdate`, and `ClosureVerification` preserve consultant-operated remediation and closure evidence.
- `ReportSnapshot` and `WorkpaperSnapshot` bind generated outputs to approved revisions and evidence cut-off.
- `AuditEvent` is append-only and records security- and judgment-relevant activity.

### Relationship rules

- One Evidence version may support many Requirements, frameworks, and Assessments.
- Each Citation points to exactly one immutable Evidence version and a resolvable location or explicit whole-item reference.
- A Conclusion may cite many Evidence versions and may also record explicit evidence absence.
- Replacing, expiring, rescoring, or invalidating Evidence does not rewrite a Conclusion. It marks affected drafts and approvals for review and preserves the prior state.
- A Finding may be selected for Engagement rollup without losing its originating Assessment and Conclusion reference.
- An Action may address several Findings, but its closure requires evidence and a consultant verification event.

---

## Permissions

| Capability | Consultant | Reviewer | Client magic link | Pack curator | Admin |
|---|---:|---:|---:|---:|---:|
| View portfolio and client records | Yes | Yes | No | No | As configured |
| Create/edit Engagement and Assessment scope | Yes | Yes | No | No | No |
| Upload and link consultant evidence | Yes | Yes | Only requested scope | No | No |
| View other evidence or conclusions | Yes | Yes | No | No | No |
| Run analysis and edit proposals | Yes | Yes | No | No | No |
| Approve conclusions | Yes | Yes | No | No | No |
| Operate Findings and Actions | Yes | Yes | No | No | No |
| Publish pack versions | No | No | No | Yes | Optional |
| Configure retention/internal identities | No | No | No | No | Yes |

Magic-link authorization is capability-based: it is limited to one Engagement and one or more named Evidence request items, expires, can be revoked, and grants no browsing permission.

---

## Lifecycles

### Engagement lifecycle

The Engagement stores milestones, ownership, deadlines, and archive state. Its displayed workflow status is derived from underlying records, using states such as Draft, Scoping, Waiting for client evidence, Ready for assessment, Conclusions need review, Remediation in progress, Completed, and Archived. A user cannot type an arbitrary status that contradicts the underlying work.

Completion freezes an integrated report snapshot but does not prevent a later validation Assessment or Action update. Archive removes the Engagement from normal portfolio views without destroying records. Permanent deletion requires a dependency and retention check plus explicit confirmation.

### Assessment lifecycle

An Assessment progresses through Draft → Scope confirmed → Evidence collection → Assessment in progress → Analysis proposed → Consultant review → Finalized. It may later be Superseded or Archived. Re-analysis creates a new Analysis run and new draft revisions; it does not replace earlier proposals, Conclusions, or report snapshots.

### Evidence lifecycle

Evidence may be Requested, Received, Catalogued, Active, Superseded, Expired, Rescoped, Invalidated, Retained, or Purged. Evidence versions are immutable. A new file or response creates a new version rather than mutating the old one. Purge is allowed only after retention, legal-hold, citation, and report-snapshot checks.

### Conclusion lifecycle

A Conclusion begins as an AI Proposal or consultant Draft, may receive consultant Edits, and becomes Approved through an Approval event. It can later be Marked for re-review, Superseded, or Invalidated while its history remains queryable. The same consultant may author and approve in v1, but both events are recorded with actor and timestamp.

### Action lifecycle

Actions progress through Open, In progress, Blocked, Ready for verification, Verified, Closed, or Accepted risk. `Closed` requires closure evidence and a consultant verification. Reopening creates a new update; it does not erase the prior closure event.

---

## End-to-end user flows

### Start and scope an engagement

1. The consultant opens the portfolio and creates or selects a Client.
2. The consultant starts a regulatory gap Engagement, records owner and deadlines, and creates at least one Assessment.
3. The consultant selects one or more published launch packs and defines the Assessment scope before substantive analysis.
4. The scope records legal entities, business units, geographies, products, systems and cloud accounts, processes, data types, assessment period, evidence cut-off, exclusions, and applicability rationale.
5. CyberAssess creates a deduplicated evidence-request set while preserving every Requirement mapping.

### Collect and catalogue evidence

1. The consultant uploads evidence or sends an expiring scoped link.
2. The client contributor sees only requested items and may upload a file, screenshot, or written response.
3. CyberAssess records provenance, immutable version metadata, original scope, and receipt time, then extracts content and precise source locations.
4. The consultant resolves duplicates, confirms scope, and decides whether prior Evidence remains applicable.
5. Changed Evidence shows every affected draft and approved Conclusion before the consultant confirms the lifecycle change.

### Complete the assessment workpaper

1. The consultant uses the questionnaire as the primary working surface.
2. For each applicable Requirement, the workspace shows the factual response, linked Evidence, exact Citations, claim quality, contradictions, missing material, AI proposal, and consultant decision.
3. Shared UCC questions and evidence requests reduce duplication, but the workspace retains framework-specific applicability and Conclusions.
4. The consultant edits or accepts each proposal and approves all final Conclusions.

### Report and remediate

1. CyberAssess produces a reviewer-ready Workpaper and a client-ready integrated report from approved Conclusions.
2. The integrated report separates framework sections or appendices and preserves each Assessment's scope, version, period, cut-off, and Citations.
3. Selected Findings and Actions roll up to the Engagement without blending Conclusions or scores.
4. The consultant records client updates from normal communications, reviews closure evidence, and verifies Action closure.

### Reassess

1. The consultant duplicates an Engagement or creates a validation Assessment.
2. Structure, scope, request templates, and selected prior Evidence may be proposed for reuse.
3. The system shows prior Evidence age and original scope; the consultant confirms continued applicability.
4. No prior Conclusion is copied. New Conclusions are produced against the new Assessment scope, period, cut-off, and evidence set.

---

## Functional requirements

### Portfolio, hierarchy, and lifecycle

**PR-001 — Client and Engagement hierarchy.** The system shall persist and navigate Workspace → Client → Engagement → Assessment without using company-name matching as identity.  
Acceptance: one Client can own multiple Engagements; one Engagement can own multiple Assessments; moving or merging imported records is explicit and audited.

**PR-002 — Portfolio dashboard.** The landing page shall show active, blocked, completed, and archived Engagements with workflow-derived status, outstanding client evidence, Conclusions awaiting review, deadlines, progress, high-priority gaps, and last activity.  
Acceptance: the consultant can filter, resume, open archived work, start an Engagement, and duplicate prior work; no displayed status relies only on free text.

**PR-003 — Archive-first removal.** Archive shall be the normal removal action.  
Acceptance: archived records leave default views but remain searchable and restorable; permanent deletion requires an explicit confirmation and a retention/dependency preview.

**PR-004 — Reassessment duplication.** The system shall duplicate reusable Engagement structure without copying Conclusions.  
Acceptance: the copy has new IDs and may inherit scope/request templates; prior Evidence is only suggested; the new Assessment contains no approved or draft Conclusion copied from the source.

**PR-005 — Reusable engagement primitives.** Regulatory gap assessment shall be the first canonical Engagement type, while the domain model remains capable of later internal-audit, vendor-assessment, risk-assessment, and validation types.  
Acceptance: shared identity, Evidence, Citation, Conclusion-history, Finding, and Action primitives are reusable, while type-specific scope, lifecycle rules, methodology, and deliverables remain explicit.

### Assessment packs, scope, and questionnaire

**PR-010 — Versioned launch packs.** V1 shall publish DPDPA 2023 plus final DPDPA Rules 2025, ISO/IEC 27001:2022 including clauses 4–10, risk treatment, Statement of Applicability, and Annex A, and NIST CSF 2.0.  
Acceptance: every Assessment records immutable pack/version references; unpublished or incomplete packs cannot be selected; pack source, effective date, product revision, and content/licensing approval are recorded.

**PR-011 — Curated methodology only.** Only product-curated pack versions are selectable in v1.  
Acceptance: no client-defined pack or spreadsheet import appears in the workflow.

**PR-012 — Scope before analysis.** An Assessment shall record scope and applicability before substantive analysis.  
Acceptance: pack versions, in-scope domains/requirements, evidence requirements, organizational and technical boundaries, exclusions with rationale, assessment period, and evidence cut-off are present before final Conclusions can be approved.

**PR-013 — Multi-framework assessment.** An Assessment may use any subset of published launch packs through one shared scoping flow.  
Acceptance: shared questions and evidence requests are deduplicated; framework-specific applicability, rationale, Requirement identity, and Conclusion remain distinct.

**PR-014 — Questionnaire as system of record.** The Requirement workspace shall be the authoritative consultant working surface.  
Acceptance: each applicable Requirement shows response, Evidence, exact Citations, sufficiency and conflicts, AI proposal, final decision, rationale, gaps, impact/risk, and recommended action.

### Evidence and collection

**PR-020 — General evidence record.** The system shall represent consultant uploads, client uploads, screenshots, written responses, and AWS snapshots through one Evidence model.  
Acceptance: source type, contributor, received/collected time, immutable version, content hash, original scope, relevant period, expiry/currentness, retention state, and extraction status are queryable.

**PR-021 — Precise citations.** Every source-grounded claim and supporting Conclusion shall cite an immutable Evidence version precisely.  
Acceptance: citations resolve to a page, section, cell, finding identifier, or other format-appropriate location plus the quoted content; whole-item citation is allowed only when granularity is impossible and is identified as such.

**PR-022 — Evidence quality analysis.** The system shall assess relevance, sufficiency, currency, period, and scope, identify contradictions and unsupported assertions, and distinguish control design from operating effectiveness where the pack methodology requires it.  
Acceptance: these dimensions are visible separately and are not collapsed into a single unexplained confidence score.

**PR-023 — Deduplicated requests.** Overlapping Evidence requirements shall be requested once.  
Acceptance: one request item may map to several Requirements across several frameworks, and each mapping is visible in the Workpaper.

**PR-024 — Scoped client magic links.** A client contributor shall submit requested evidence without an account.  
Acceptance: tokens are expiring, revocable, non-enumerable, restricted to named request items, rate-limited, and prevented from reading other Engagement data.

**PR-025 — Controlled evidence reuse.** The system may suggest Evidence reuse across Assessments but shall require consultant confirmation.  
Acceptance: the prompt shows Evidence age, original scope, version, period, and current lifecycle; declining reuse has no side effect; confirming reuse creates an audited Evidence-use link.

**PR-026 — Evidence change impact.** Replacing, expiring, rescoping, or invalidating Evidence shall identify affected drafts, approved Conclusions, Findings, and snapshots.  
Acceptance: the consultant sees the full impact list before confirmation; affected final Conclusions enter re-review without losing their original approval history.

### AWS evidence snapshot

**PR-030 — Manual AWS snapshot.** The consultant shall manually trigger a read-only evidence snapshot using cross-account AssumeRole with an external ID.  
Acceptance: v1 collects only AWS Config and Security Hub data; each run records account/scope, requestor, time, status, and immutable raw and normalized outputs.

**PR-031 — AWS security boundary.** The connector shall not store long-lived AWS credentials or perform write/remediation actions.  
Acceptance: permissions are least-privilege, temporary credentials are not persisted, failed assumptions are audited, and there is no schedule or continuous-monitoring promise.

### Analysis, conclusions, and review

**PR-040 — Provider-independent analysis runs.** Analysis shall preserve input references, pack/prompt/model configuration, outputs, validation results, and run status without naming a single provider in the domain.  
Acceptance: rerunning analysis creates a new run and leaves earlier runs queryable.

**PR-041 — Source-grounded claims.** AI analysis shall produce claims with Citations, contradictions, explicit gaps, and unsupported-assertion flags.  
Acceptance: an ungrounded quote cannot be treated as supporting Evidence; incomplete Requirement coverage fails closed rather than yielding a misleading complete report.

**PR-042 — Conclusion outcomes.** Final Requirement outcomes shall be Compliant, Partially compliant, Non-compliant, Not applicable, or Insufficient evidence.  
Acceptance: Not applicable requires rationale; Insufficient evidence is distinct from Non-compliant and from an unanswered questionnaire; deterministic methodology states how each outcome affects displayed scores and denominators.

**PR-043 — Complete conclusion.** Every approved Conclusion shall include outcome, rationale, supporting Evidence or explicit Evidence absence, identified gaps, impact/risk, and recommended action.  
Acceptance: approval is blocked when a required field or evidence/absence basis is missing.

**PR-044 — Human approval.** Every AI-generated Conclusion shall require consultant review.  
Acceptance: the Workpaper preserves proposal, every edit, actor, timestamp, decision, and approval; the same actor may prepare and approve in v1, but both events remain visible.

**PR-045 — Deterministic scoring boundary.** Numeric or categorical methodology calculations shall be deterministic and operate only on eligible consultant-approved Conclusions.  
Acceptance: AI cannot emit a final score; methodology version and inputs are recorded; qualitative judgment remains visible; no engagement-level blended compliance score exists.

### Findings, actions, reports, and auditability

**PR-050 — Assessment-bound Findings.** Findings shall preserve their originating Assessment, framework, Requirement, scope, cut-off, Conclusion revision, and Citations.  
Acceptance: engagement rollup does not sever or obscure the origin.

**PR-051 — Consultant-operated Actions.** Consultants shall create and update Actions, capture updates received through normal client communications, and verify closure evidence.  
Acceptance: update history is append-only; Closed requires closure Evidence plus consultant verification; client-managed actions are not exposed.

**PR-052 — Required deliverables.** The system shall produce a reviewer-ready Workpaper, a client-ready integrated gap report with prioritized remediation, and a live consultant-operated action tracker.  
Acceptance: exports use approved Conclusions only and remain unavailable until review gates pass.

**PR-053 — Integrated report boundaries.** One integrated Engagement report may consolidate selected approved Findings and Actions while clearly separating Assessment and framework results.  
Acceptance: each section states pack/version, scope, period, cut-off, exclusions, and Citations; no blended score across Assessments/frameworks is displayed.

**PR-054 — Immutable output snapshots.** Generated reports and RFIs shall be versioned snapshots.  
Acceptance: regenerating output creates a new version bound to the exact approved Conclusion set and does not overwrite an issued artifact.

**PR-055 — Traceability.** A reviewer shall trace any Finding to exact source material and its proposal/edit/approval history quickly.  
Acceptance: the Workpaper provides direct navigation Finding → Conclusion revision → claim/Citation → Evidence version and shows all actors/timestamps.

**PR-056 — Audit events.** Security- and judgment-relevant operations shall create append-only Audit events.  
Acceptance: scope changes, Evidence lifecycle changes, magic-link actions, analysis runs, edits, approvals, release, archive, deletion attempts, AWS runs, and closure verification are attributable and queryable.

---

## Data and security expectations

- Data minimization applies to client evidence, logs, prompts, temporary files, and report artifacts.
- Secrets, raw credentials, and signed magic-link tokens must not be logged.
- Stored evidence and generated artifacts require encryption in transit and at rest appropriate to the deployment.
- Uploads require size and type enforcement, content/MIME validation, filename sanitization, malware-scanning integration, and quarantine/failure states.
- Authorization checks must be object-scoped and enforced server-side; opaque IDs are not authorization.
- LLM processing must preserve the existing zero-data-retention/data-collection-deny posture where supported, expose provider/model provenance, and fail closed on missing or structurally invalid output.
- Audit logs must avoid duplicating confidential evidence content; they record identifiers and before/after metadata sufficient for review.
- Retention and legal-hold rules apply independently to database records, uploaded blobs, extracted text, generated outputs, and connector snapshots.
- Backups and migration rehearsals must cover the database and evidence blobs together.
- Pack content must record source and licensing approval. ISO 27001 and other copyrighted standards must not be embedded or redistributed beyond licensed rights.

---

## Success measures

### Product outcomes

- At least 95% of applicable approved Conclusions in a pilot can be traced to one or more precise Citations or an explicit Evidence-absence record without opening raw database records.
- Overlapping request items are sent once while retaining all Requirement mappings in every tested multi-framework Assessment.
- A consultant can resume any active Engagement from the portfolio and understand the next blocker within one screen.
- A reassessment reuses eligible Evidence with explicit confirmation while creating no copied Conclusions.
- A reviewer can reconstruct proposal → edits → approval for a sampled Conclusion in under two minutes.
- No released integrated report contains a blended score across unlike frameworks or scopes.
- Longitudinal synthetic demos prove baseline, remediation, and validation workflows for multiple maturity profiles before external pilot use.

### Guardrails

- Evidence replacement, expiry, rescoping, or invalidation never silently leaves an affected approved Conclusion presented as current.
- No report or downloadable client deliverable is released from unapproved Conclusions.
- No client magic link exposes a questionnaire, Conclusion, other request, or unrelated Evidence.
- No AWS connector operation uses long-lived credentials, performs writes, or implies continuous monitoring.

---

## Product-validation and demo track

Synthetic data proves the product mechanics; it does not replace discovery with practising consultants.

Use at least four fictional Clients with contrasting conditions:

1. A high-maturity fintech with strong technical operations but policy/practice contradictions.
2. A low-maturity health-data platform with missing processor governance and weak children's-data controls.
3. A large logistics organization with global scope, mature governance artifacts, and hidden operating-effectiveness gaps.
4. A growing B2B SaaS company running a DPDPA + ISO 27001 + NIST CSF Assessment.

Each Client must have longitudinal history: a baseline Engagement, at least one targeted or remediation-validation Assessment, and a later reassessment. The dataset must include valid and stale Evidence reuse, a rejected reuse suggestion, Evidence replacement that triggers re-review, deduplicated cross-framework requests, distinct framework Conclusions, Action updates, closure Evidence, and an archived Engagement.

Demo acceptance is automated where practical and includes a browser walkthrough. The track must prove hierarchy, reuse, reassessment, Conclusions, and remediation; it must not tune the product only to synthetic expected answers.

---

## Open questions for adversarial review

1. What licensed content strategy permits the ISO/IEC 27001:2022 pack to cover clauses 4–10, risk treatment, Statement of Applicability, and Annex A without redistributing protected text?
2. What deterministic denominator and presentation rule should `Insufficient evidence` use so it is neither hidden nor treated automatically as Non-compliant?
3. Which Evidence lifecycle changes require mandatory re-approval of an approved Conclusion, and when is a visible warning sufficient?
4. What citation granularity is achievable and defensible for PDFs, DOCX tables, screenshots, written responses, AWS Config items, and Security Hub findings?
5. What default magic-link lifetime, upload limit, malware-scanning control, Evidence retention period, and legal-hold behavior are required for the first consulting pilot?
6. Should a completed Engagement permit new Actions and validation Assessments without reopening, or should completion be a report-only milestone?
7. What minimum AWS Config resource types and Security Hub finding fields provide useful evidence without implying full-cloud coverage?
8. Which legacy `not_assessed` records can be migrated to `Insufficient evidence`, and which must remain explicitly unknown pending consultant review?
