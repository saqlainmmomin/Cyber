# Handoff: Formal Product and Implementation Plan

## Goal

Create a formal, repository-grounded product requirements document and a phased implementation plan for the next version of CyberAssess. The result must turn the settled product decisions below into an unambiguous build specification without relitigating the direction. Definition of done: two durable documents exist—one describing the target product and acceptance criteria, and one mapping the current application to an ordered, testable implementation program—ready for a later adversarial review by Claude.

## Current state

CyberAssess is a working FastAPI, Jinja2, HTMX, and Tailwind application for evidence-backed compliance assessments. It already contains assessment creation, framework selection, questionnaires, document upload and desk review, adaptive screening/tiering, multi-framework Unified Control Cluster mappings, deterministic scoring, consultant review, reports, RFIs, remediation tracking, and PDF output. It does not yet have the target Client → Engagement → Assessment portfolio model, client evidence-request magic links, a general evidence object and lifecycle, or an AWS connector.

The repository currently describes itself as supporting six framework definitions, but the web flow exposes DPDPA, ISO 27001, and NIST CSF while GDPR, HIPAA, and PCI-DSS remain roadmap items. Validate every current-state claim against the code rather than trusting earlier planning documents.

An older brainstorm framed the product as a DPDPA-only intelligent audit assistant. That document is useful historical context but is superseded where it conflicts with the decisions in this handoff. Existing uncommitted changes belong to the user; do not edit, discard, or reformat them.

### Settled product definition

CyberAssess is a consultant-operated assessment execution workspace that analyses client evidence to complete regulatory questionnaires and produce defensible, multi-framework compliance conclusions, reports, and remediation plans.

Evidence analysis is an input engine, not the final product. The assessment questionnaire is the consultant's primary working surface and system of record. Consultant-approved compliance assessment conclusions are the output. The product must describe these as assessed compliance posture—not independent legal compliance, certification, or attestation.

### Settled product hierarchy

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

A client may have multiple engagements. An engagement may contain multiple assessments, including a baseline gap assessment, targeted review, and remediation validation. Assessments within the same engagement may use different frameworks, versions, legal entities, business units, geographies, products, systems, cloud accounts, processes, data types, assessment periods, evidence cut-off dates, applicability decisions, and exclusions.

Operational status, evidence requests, findings, and actions may roll up to the engagement. Compliance conclusions must remain bound to the originating assessment, framework, scope, and evidence cut-off date. Do not create a blended engagement-level compliance score.

### Settled initial product scope

1. The first canonical engagement type is a regulatory gap assessment. Design the domain model so later internal audit, vendor assessment, risk assessment, and validation engagements can reuse the same assessment/evidence/conclusion primitives without pretending they are identical deliverables.
2. The initial buyer and operator is a boutique GRC consulting firm. The workflow and auditability should be credible for larger firms such as KPMG, but enterprise administration must not overwhelm the first release.
3. The consultant starts on a portfolio dashboard showing active, blocked, completed, and archived engagements; workflow-derived status; outstanding client evidence; conclusions awaiting review; deadlines; progress; high-priority gaps; and last activity. It supports starting an engagement, resuming work, filtering, viewing archived work, and duplicating prior engagements for reassessment.
4. Archive is the normal removal action. Permanent deletion belongs behind an explicit confirmation and must respect evidence retention and audit-history concerns.
5. Launch assessment packs:
   - Digital Personal Data Protection Act, 2023 plus final DPDPA Rules, 2025.
   - ISO/IEC 27001:2022, including clauses 4–10, risk treatment, Statement of Applicability, and Annex A.
   - NIST Cybersecurity Framework 2.0.
6. An assessment may use any subset of the launch packs. Multi-framework assessments use one shared scoping flow, deduplicate overlapping evidence requests and questions, and allow one evidence item to support multiple controls. They retain framework-specific applicability, rationale, and conclusions. One integrated report contains clearly separated framework sections or appendices.
7. Assessment packs are curated and versioned by the product team in v1. Client-defined methodology and spreadsheet/CSV framework imports are deferred.
8. The consultant defines assessment scope and applicability before substantive analysis. Every assessment records framework/version, in-scope domains and requirements, evidence requirements, organisational and technical boundaries, exclusions, assessment period, and evidence cut-off date.
9. Evidence inputs in v1 are consultant uploads, client uploads through scoped magic links, screenshots, written responses, and a narrow AWS integration. Clients do not need accounts.
10. The AWS integration is a manually triggered, read-only evidence snapshot using cross-account AssumeRole with an external ID. Initial sources are AWS Config and Security Hub only. Do not plan long-lived AWS credentials, a generic scan of every AWS service, remediation/write access, or continuous monitoring in v1.
11. Evidence analysis should catalogue provenance and versions; extract source-grounded claims with precise citations; map evidence to relevant questions, controls, and frameworks; assess relevance, sufficiency, currency, period, and scope; identify contradictions, gaps, and unsupported assertions; and distinguish control design from operating effectiveness where the methodology calls for it.
12. Evidence may be suggested for reuse across assessments, but conclusions must never silently carry forward. Show age and original scope and require the consultant to confirm continued applicability.
13. For each applicable requirement, the workspace combines the client's response, submitted evidence, exact citations, analysis of sufficiency and conflicts, the AI-proposed assessment, and the consultant's final decision.
14. Requirement-level outcomes are: Compliant, Partially compliant, Non-compliant, Not applicable, and Insufficient evidence. Each approved conclusion includes rationale, supporting evidence or explicit evidence absence, identified gaps, impact/risk, and recommended action.
15. Every AI-generated conclusion requires consultant review. The same consultant may prepare and approve in v1, but the complete proposal/edit/approval history must be retained. Mandatory maker-checker separation is deferred.
16. The consultant operates remediation tracking, records updates received through normal client communications, reviews closure evidence, and verifies closure. Client-managed actions are deferred.
17. Required deliverables are a reviewer-ready workpaper, a client-ready integrated gap report with prioritised remediation, and a live consultant-operated action tracker.
18. Engagement-level reporting may consolidate selected approved findings and actions but must preserve the distinct assessment scopes, dates, framework conclusions, and citations.

### Product acceptance principles

- Every final conclusion cites precise supporting evidence or explicitly records evidence absence.
- An overlapping evidence requirement is requested from the client once, while preserving its mappings to all applicable controls.
- A single evidence item may support multiple framework requirements without conflating their conclusions.
- A reviewer can trace any finding to its exact source and approval history quickly.
- Replaced, expired, rescoped, or invalidated evidence identifies all affected draft and approved conclusions.
- Workflow statuses are derived from real state—for example, Waiting for client evidence or 12 conclusions need review—not merely free-text labels.
- Deterministic calculations remain separate from qualitative AI analysis. The plan must state where human judgment and methodology rules govern the final posture.

### Explicitly deferred

- Client user accounts or a general self-service client portal.
- Continuous cloud monitoring.
- Broad cloud, identity, ticketing, and SaaS integrations.
- Client-authored framework/methodology packs or spreadsheet imports.
- Mandatory maker-checker approval.
- Client-managed remediation.
- Autonomous legal-compliance declarations, certification, or attestation.
- A single blended score across unlike frameworks and assessment scopes.

## Required deliverables

Create both documents:

1. `/Users/saqlainmomin/dpdpa-gap-tool/docs/product/2026-09-21-cyberassess-product-requirements.md`
2. `/Users/saqlainmomin/dpdpa-gap-tool/docs/plans/2026-09-21-001-feat-consultant-assessment-workspace-plan.md`

The product requirements document should cover product thesis and boundaries, target users, terminology, domain model, permissions, engagement and assessment lifecycles, end-to-end user flows, functional requirements with stable IDs and acceptance criteria, evidence and conclusion semantics, reports, auditability, data/security expectations, success measures, and deferred scope.

The implementation plan should begin with a truthful current-state map and gap analysis. Then define an incremental sequence that preserves working behaviour while evolving the data model and UI. Include migration/backward-compatibility concerns, architecture boundaries, relevant files/modules, workstreams and dependencies, acceptance tests and smoke tests per phase, risks, explicit non-goals, and later decision points. The plan must be sufficiently concrete for an implementation agent to execute, but it must not implement code during this task.

Include a product-validation/demo track using several synthetic company personas with different maturity levels and longitudinal assessment history. Treat this as a way to prove multi-engagement evidence reuse, reassessment, conclusions, and remediation—not as a substitute for real consultant discovery.

End both documents with a concise `Open questions for adversarial review` section. These questions are intended for a later Claude review; do not invent certainty where the repository or product decisions leave genuine unknowns.

## Key files

- `/Users/saqlainmomin/dpdpa-gap-tool/AGENTS.md` — repository contract, architecture summary, commands, and gotchas.
- `/Users/saqlainmomin/dpdpa-gap-tool/app/models/assessment.py` — current assessment and assessment-document persistence model.
- `/Users/saqlainmomin/dpdpa-gap-tool/app/routers/web.py` — current server-rendered assessment workflow and enabled-framework decisions.
- `/Users/saqlainmomin/dpdpa-gap-tool/app/templates/pages/dashboard.html` — current assessment-list dashboard that must evolve into the engagement portfolio.
- `/Users/saqlainmomin/dpdpa-gap-tool/app/services/desk_review.py` — current document ingestion, extraction, cataloguing, and preliminary evidence analysis.
- `/Users/saqlainmomin/dpdpa-gap-tool/app/services/question_engine.py` — current question construction and multi-framework behaviour.
- `/Users/saqlainmomin/dpdpa-gap-tool/app/services/claude_analyzer.py` — current qualitative analysis boundary; verify whether the filename still reflects the active provider abstraction.
- `/Users/saqlainmomin/dpdpa-gap-tool/app/services/scoring.py` — deterministic scoring boundary.
- `/Users/saqlainmomin/dpdpa-gap-tool/app/frameworks/registry.py` — framework registry and current definitions.
- `/Users/saqlainmomin/dpdpa-gap-tool/app/frameworks/mappings/clusters.py` — Unified Control Cluster mapping and cross-framework deduplication foundation.
- `/Users/saqlainmomin/dpdpa-gap-tool/app/models/desk_review.py` — current desk-review summary and finding persistence.
- `/Users/saqlainmomin/dpdpa-gap-tool/app/models/report.py` — current gap-report and gap-item persistence.
- `/Users/saqlainmomin/dpdpa-gap-tool/docs/brainstorms/2026-04-04-intelligent-audit-assistant-requirements.md` — superseded but useful historical requirements.
- `/Users/saqlainmomin/dpdpa-gap-tool/docs/plans/2026-04-04-001-feat-intelligent-audit-assistant-plan.md` — earlier implementation assumptions to reuse selectively, not blindly.
- `/Users/saqlainmomin/dpdpa-gap-tool/docs/plans/2026-05-03-001-feat-adaptive-assessment-engine-plan.md` — existing adaptive-assessment design context.
- `/Users/saqlainmomin/dpdpa-gap-tool/docs/architecture/data-flow-and-processes.md` — current documented data flow; check for drift against code.
- `/Users/saqlainmomin/dpdpa-gap-tool/scripts/seed_test_companies.py` — existing synthetic personas and scenarios.
- `/Users/saqlainmomin/dpdpa-gap-tool/tests/` — current behavioural contract and starting point for phased verification.

## Constraints

- Read the applicable planning skill before drafting and follow the repository's plan conventions.
- Inspect the current implementation deeply enough to identify reusable primitives, incompatible assumptions, and migration risks. Do not write a greenfield fantasy plan.
- Treat every decision in `Settled product definition`, `Settled product hierarchy`, and `Settled initial product scope` as fixed unless implementation evidence reveals a direct contradiction. Record contradictions as risks or questions; do not silently change product direction.
- Do not modify application code, tests, current schemas, existing plans, or user-owned dirty files.
- Do not use client names, credentials, or confidential evidence in either document.
- Keep the solution proportionate to a boutique-firm launch. Show how the foundations can support larger consulting teams later without pulling enterprise-only administration into v1.
- Preserve deterministic scoring and human approval boundaries.
- Prefer archive and retention-aware deletion semantics.
- Avoid overloading the word `project`; use Client, Engagement, Assessment, Evidence, Requirement, Conclusion, Finding, and Action consistently and define them.
- Flag licensing or content-availability concerns for standards such as ISO 27001 instead of assuming copyrighted standard text can be embedded or redistributed freely.
- Do not invoke Claude in this task. Produce artifacts designed for a separate Claude critique afterward.

## Verification

Before reporting completion:

1. Confirm both target documents exist and contain no placeholders, unresolved drafting notes, credentials, or real client names.
2. Cross-check every material current-state statement against code, tests, or an existing authoritative repository document and cite paths in the plan.
3. Check that every settled decision above appears in either the product requirements or implementation plan and that no deferred feature is accidentally placed in the v1 critical path.
4. Verify the implementation phases each have observable acceptance criteria and a smoke-test strategy.
5. Verify the working tree shows only the two new planning documents plus this handoff and pre-existing user changes.
6. Run relevant non-mutating repository checks needed to validate plan assumptions. If the full test suite is run, report the exact command and result; do not imply code was tested if it was not.

## Report back

Append a `## Results` section to this same handoff file summarising the documents created, key architectural conclusions, repository checks performed, remaining risks, and the best questions for the subsequent Claude review.

## Results

### Documents created

1. `docs/product/2026-09-21-cyberassess-product-requirements.md`
   - Defines the product thesis, boundaries, users, terminology, hierarchy, permissions, lifecycles, flows, stable requirements (`PR-001`–`PR-056`), acceptance criteria, Evidence and Conclusion semantics, reports, auditability, security expectations, success measures, longitudinal synthetic validation, deferred scope, and adversarial-review questions.
2. `docs/plans/2026-09-21-001-feat-consultant-assessment-workspace-plan.md`
   - Maps the current repository to seven ordered implementation units covering migration/pack foundations, hierarchy/portfolio, Evidence/client collection, immutable analysis/Conclusions, Findings/Actions/reporting, AWS snapshots, and longitudinal hardening.
   - Includes architecture boundaries, additive migration/backward-compatibility rules, file-level scope, dependencies, phase gates, acceptance and smoke tests per unit, risks, non-goals, later decision points, and definition of done.

No application code, schema, tests, existing plans, or pre-existing user-owned changes were modified.

### Key architectural conclusions

- `Assessment` is currently the aggregate root and embeds company identity, workflow, scope, and framework selection. The target must add Client and Engagement without renaming or replacing Assessment in place.
- A real versioned migration system is a prerequisite. The current startup migration code is insufficient for the normalized model, and its SQLite questionnaire rebuild can omit populated newer columns. The plan adopts Alembic, repairs the bridge first, and uses additive shadow tables, backfill, reconciliation, dual-read/write, then constraints.
- Legacy import should create Clients conservatively and one imported Engagement per legacy Assessment. Same-name records must not be assumed to share one historical Engagement or scope.
- Current document, desk-review, report, review, RFI, and remediation records contain useful seeds, but reruns and edits overwrite history. The target separates immutable EvidenceVersion/Citation, AnalysisRun/Claim, ConclusionRevision/ApprovalEvent, Finding, ActionUpdate/ClosureVerification, and ReportSnapshot records.
- UCC mappings remain the foundation for shared questions and deduplicated Evidence requests. They must not produce shared Conclusions: each framework Requirement retains its own applicability, rationale, and Conclusion.
- The existing provider boundary in `app/services/llm_client.py` is reusable; `claude_analyzer.py` is a misleading compatibility filename rather than an active provider lock-in.
- Deterministic scoring remains separate from qualitative AI/human judgment, but the two current scoring paths need one per-framework facade based on approved Conclusions. The current equal-weight unified multi-framework score conflicts with the settled product and must leave target UI/API/report semantics.
- Pack registration is not the same as readiness. The current DPDPA pack does not cover the final Rules 2025, the ISO pack covers Annex A but not clauses 4–10/risk treatment/SoA, and ISO content requires a licensing decision. NIST CSF 2.0 is present. Publication must be gated by content, source, integrity, product, and licensing approval.
- Client magic links and AWS are Evidence source adapters. They should reuse the same validation, provenance, lifecycle, audit, and retention services as consultant uploads; AWS remains manual, AssumeRole/external-ID based, Config/Security Hub only, and read-only.
- Portfolio status must be derived from Evidence, review, deadline, Finding, Action, and activity state. Archive is normal; permanent purge is retention- and dependency-aware and coordinates database and blob state.

### Repository checks performed

- Inspected all named key files plus related models, routers, templates, schemas, framework definitions, UCC/questionnaire code, report/export paths, migrations, tests, architecture documentation, older plans, and synthetic seeds.
- Read-only framework/UCC diagnostic found 52 UCC clusters and current control totals of 41 DPDPA, 93 ISO 27001, 94 NIST CSF, 54 GDPR, 54 HIPAA, and 64 PCI-DSS controls. Integrity tests already enforce valid IDs, unique cluster membership, and explicit singleton coverage.
- Focused workflow verification:
  - `uv run pytest -q tests/test_picker_and_scoring_contract.py tests/test_needs_review_ui.py tests/test_incomplete_assessment_e2e.py`
  - Result: 37 passed; warnings only.
- Isolation-oriented verification:
  - `.venv/bin/pytest -q tests/test_content_integrity.py tests/test_picker_and_scoring_contract.py tests/test_llm_output_validation.py tests/test_incomplete_assessment_e2e.py`
  - Result: 56 passed, 5 failed because templates loaded without the normal app initialization had no `branding` global. This reveals test-order/environment coupling and is captured in U1.
- Authoritative standard full-suite verification:
  - `PYTHONDONTWRITEBYTECODE=1 uv run pytest -p no:cacheprovider -q`
  - Result: 128 passed, 20 warnings in 3.07 seconds. Warnings are one collection warning, two tests returning non-`None`, 16 Starlette `TemplateResponse` deprecations, and one fpdf2 `ln` deprecation.
- `git diff --check` passed.
- Placeholder/drafting-note/credential scans found no unresolved drafting markers or credentials in either document.
- Fixed-decision coverage was checked explicitly for hierarchy, engagement types, buyer/operator, portfolio fields, archive/deletion, all three launch packs, multi-framework deduplication and separation, scope, all v1 Evidence sources, AWS limits, Evidence analysis quality, reuse, five outcomes, human approval history, remediation, outputs, auditability, deterministic scoring, deferred features, and the prohibition on blended scores.
- Final working-tree audit shows only the two new documents and this handoff in addition to pre-existing user changes/untracked files.

### Remaining risks and decision gates

1. ISO/IEC 27001 content and redistribution rights must be resolved before the ISO pack can meet the stated launch scope; PCI-DSS requires a similar review before future publication.
2. The methodology must decide how `Insufficient evidence` affects deterministic score denominators and whether low evidence coverage suppresses score presentation.
3. Legacy `not_assessed` records cannot all be converted safely to `Insufficient evidence`; ambiguous rows require review.
4. Evidence lifecycle changes need a policy defining when approved Conclusions and issued snapshots require mandatory re-review, supersession, or only a warning.
5. Client link lifetime, rate limits, file limits, malware scanning, retention, and legal-hold defaults remain pilot decisions.
6. Citation precision varies by PDF, DOCX tables, images, written responses, Config items, and Security Hub findings; the location contract needs adversarial validation.
7. The minimum useful AWS Config/Security Hub collection set and least-privilege policy are not yet fixed.
8. The current standard suite passes, but isolated template tests expose initialization-order coupling that should be removed before schema work.

### Best questions for the subsequent Claude review

1. Is the additive migration/backfill/cutover sequence safe enough for the current SQLite and unversioned migration history, and which failure modes or reconciliation gates are missing?
2. Do the proposed boundaries among Response, AnalysisClaim, ConclusionRevision, Finding, and Action preserve complete auditability without excessive duplication or ambiguous ownership?
3. Does the pack publication model adequately address DPDPA Rules 2025 completeness and ISO clauses 4–10/risk treatment/SoA plus licensing constraints?
4. What is the most defensible deterministic treatment and presentation of `Insufficient evidence`, including minimum coverage needed before showing a framework score?
5. Are Evidence invalidation, reuse confirmation, Citation precision, and issued-report impact rules strong enough for professional-services review?
6. Does any planned portfolio, integrated-report, or comparison behavior still imply a prohibited blended compliance posture?
7. Are the magic-link and AWS capability boundaries proportionate to a boutique launch while sufficiently safe for confidential evidence?
8. Are the seven implementation units ordered and scoped so each can ship behind compatibility gates without creating a half-migrated system that consultants can misuse?
