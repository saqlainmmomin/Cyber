# feat: Evolve CyberAssess into a Consultant Assessment Workspace

**Status:** Ready for adversarial review  
**Date:** 2026-09-21  
**Product contract:** `docs/product/2026-09-21-cyberassess-product-requirements.md`  
**Plan type:** Deep, phased migration  
**Target stack:** FastAPI, SQLAlchemy, Jinja2, HTMX, Tailwind, SQLite initially

## Summary

Evolve the working assessment application into a consultant portfolio organized as Client → Engagement → Assessment while preserving current DPDPA, ISO 27001, and NIST CSF flows during migration. The program introduces versioned assessment packs, general Evidence and Citation primitives, scoped client collection, immutable analysis and Conclusion history, independent Findings and Actions, manual AWS snapshots, versioned outputs, reassessment, and a workflow-derived portfolio.

This is an additive migration, not a rewrite. Existing Assessment IDs and URLs remain valid until compatibility reads and backfill reconciliation are complete. The current AI provider adapter, UCC mapping, questionnaire, deterministic scoring, review gate, reports, and synthetic fixtures are reused behind clearer domain boundaries.

---

## Problem frame

CyberAssess already completes a valuable single-assessment workflow, but its persistence model treats `Assessment` as the client, engagement, workflow, evidence container, report, and remediation boundary. Rerunning analysis or desk review replaces history; deletion leaves dependants and files unmanaged; company-name equality stands in for Client identity; client evidence collection and AWS snapshots do not exist; and the current multi-framework report computes a blended score forbidden by the target product.

The implementation must keep current behavior available while building an auditable system that can answer four questions reliably:

1. Which Client, Engagement, Assessment, pack version, scope, period, and cut-off does this Conclusion belong to?
2. Which immutable Evidence versions and precise Citations support it?
3. What did AI propose, what did the consultant change, and who approved the result?
4. Which Findings and Actions may roll up operationally without blending distinct compliance Conclusions?

---

## Truthful current-state map

### What is working and reusable

| Capability | Repository evidence | Reuse decision |
|---|---|---|
| Six registered framework definitions | `app/main.py` registers six definitions and checks registry/UI parity; `app/frameworks/schema.py` defines the shared pack shape. | Keep the registry boundary and add pack lifecycle/version/source metadata. |
| Three launchable web packs | `app/routers/web.py` enables `dpdpa`, `iso27001`, and `nist_csf`; GDPR, HIPAA, and PCI-DSS are roadmap. | Centralize availability so web and API enforce one policy. |
| UCC question deduplication | `app/frameworks/cluster_engine.py`, `app/frameworks/questionnaire_builder.py`, and `app/frameworks/mappings/clusters.py` map shared questions to framework controls. | Reuse UCCs for question/request mapping; never treat a UCC as a shared Conclusion. |
| Scope, upload, desk review, questionnaire, analysis, review, report | `app/routers/web.py` and `app/templates/pages/assessment.html` expose a working tabbed flow. | Evolve the shell and route through domain services rather than replace it at once. |
| Evidence-like findings | `app/models/desk_review.py` stores source quote and location, and `app/services/claude_analyzer.py` grounds newly extracted quotes. | Migrate into EvidenceVersion, Citation, AnalysisClaim, and quality dimensions. |
| Provider abstraction | Despite its filename, `app/services/claude_analyzer.py` calls the tiered adapter in `app/services/llm_client.py`; model selection is configuration-driven. | Preserve the adapter; rename the domain service after compatibility callers exist. |
| Deterministic calculation | `app/services/scoring.py` maps qualitative states through deterministic rules. | Consolidate behind one facade using approved Conclusions only. |
| Human review and release gate | `app/models/report.py` keeps `ai_*` fields; `app/routers/review.py` supports disposition/approval; `app/utils/review_gate.py` gates exports. | Replace mutable latest-state review with immutable revisions/events while preserving the gate. |
| Reports, RFI, remediation, comparison | `app/routers/reports.py`, `app/services/rfi_generator.py`, `app/routers/remediation.py`, and comparison endpoints provide usable behavior. | Convert outputs to snapshots, remediation to independent Actions, and comparisons to Client/scope ancestry. |
| Synthetic personas and golden checks | `scripts/seed_test_companies.py` and `tests/fixtures/canonical_dpdpa/` provide adversarial data and stable output fixtures. | Extend into longitudinal, multi-engagement validation. |

### Gaps and incompatible assumptions

| Gap | Current evidence | Target implication |
|---|---|---|
| Flat root model | `app/models/assessment.py` stores company identity, workflow, scope, and framework JSON on `Assessment`. | Add Client and Engagement; preserve Assessment identity. |
| Company-name lineage | `app/routers/reports.py` finds comparable records by exact `company_name`. | Replace with Client/Engagement ancestry and explicit comparability rules. |
| No referential integrity | Models use indexed string IDs without database foreign keys or relationships. | Preflight orphan/duplicate data, backfill, then add constraints. |
| Unsafe destructive behavior | Assessment and document endpoints hard-delete rows; uploaded blobs are not lifecycle-managed. | Make archive normal; route purge through retention/dependency checks and blob cleanup. |
| Evidence is assessment-bound | `AssessmentDocument` has path/type/category/text/time only. | Introduce general immutable Evidence versions, mappings, provenance, retention, and reuse. |
| History is overwritten | Desk review deletes findings; analysis deletes reports/items/initiatives; questionnaire resubmission replaces responses; review/remediation mutate in place. | Use immutable runs, revisions, events, snapshots, and updates. |
| Citation precision is incomplete | PDF extraction loses explicit page markers and desk-review reuse bypasses the fresh quote-grounding pass. | Add format-aware locations and verification state tied to EvidenceVersion. |
| Outcome mismatch | Current states include `not_assessed`; target requires `insufficient_evidence`. | Migrate deliberately and define deterministic denominator behavior. |
| Blended multi-framework score | `compute_unified_maturity()` averages framework scores and the analysis route stores it as `GapReport.overall_score`. | Remove from target semantics and UI; keep per-assessment/per-framework outputs only. |
| Two scoring paths | The router uses legacy 0–100 functions while newer cluster-first `score()` supports exactly one framework. | Build one versioned scoring facade before report cutover. |
| Launch-pack content is incomplete | DPDPA definition is Act 2023 only; ISO definition contains 93 Annex A controls but not clauses 4–10, risk treatment, or SoA workflow; NIST CSF 2.0 is present. | Gate pack publication on content completion, validation, provenance, and licensing. |
| Availability policy differs | Web rejects roadmap packs; API selection accepts every registered pack; one seed uses GDPR. | Centralize `published/selectable` policy for all channels. |
| No client collection or AWS connector | No magic-link or AWS integration exists in `app/`, dependencies, or tests. | Build only after Evidence primitives are stable. |
| Status is mutable and inconsistent | `Assessment.status` changes opportunistically; the dashboard renders it directly. | Derive portfolio state and counters from real records. |
| Migrations are not durable enough | `app/main.py::_run_migrations()` runs unversioned startup SQL; its SQLite questionnaire rebuild omits newer columns in the recreated table. | Adopt Alembic and repair the bridge before normalized schema work. |

### Pack coverage facts

Current integrity checks cover 52 UCC clusters. Repository definitions contain 41 DPDPA controls, 93 ISO controls, 94 NIST CSF controls, 54 GDPR controls, 54 HIPAA controls, and 64 PCI-DSS controls. Mapping coverage is high, but coverage is not publication readiness: the ISO pack remains Annex-A-only, and the DPDPA Rules 2025 are not represented.

### Test baseline

The existing suite is strongest around framework/UCC integrity, picker behavior, scope invalidation, deterministic scoring, output validation, evidence prefill/tiering, and golden DPDPA outputs. It has little or no coverage for hierarchy, archive, magic links, evidence lifecycle, precise citation navigation, approval history, retention-aware purge, closure verification, AWS collection, or longitudinal reassessment.

A focused workflow run passed 37 tests. The standard full-suite run passed all 128 tests with 20 warnings. A separate isolation-oriented framework/LLM run passed 56 and failed 5 web-template tests because `branding` was undefined when templates were loaded without the normal app initialization side effect. Treat this order-dependence as a baseline test-harness issue to fix in U1 even though the normal suite is green.

---

## Requirements

The implementation is governed by PR-001 through PR-056 in the product contract. The critical slices are:

- **Hierarchy and portfolio:** PR-001–PR-005.
- **Published packs, scope, and work surface:** PR-010–PR-014.
- **Evidence, collection, reuse, and impact:** PR-020–PR-026.
- **Manual AWS snapshot:** PR-030–PR-031.
- **Analysis, Conclusions, review, and deterministic calculations:** PR-040–PR-045.
- **Findings, Actions, reporting, and auditability:** PR-050–PR-056.

### Acceptance examples

**AE1 — Deduplicated request, distinct Conclusions.** A DPDPA + ISO 27001 Assessment creates one policy evidence request mapped to applicable controls in both packs. One uploaded Evidence version supports both, but each Requirement receives its own applicability and Conclusion.

**AE2 — Evidence invalidation.** A consultant replaces an Evidence version cited by three draft and two approved Conclusions. Before confirmation the system lists all five; afterward the drafts are stale and the approved Conclusions require re-review without losing their original approvals.

**AE3 — Reassessment.** Duplicating an Engagement copies structure and request templates, offers prior Evidence with age/scope warnings, and copies no Conclusion.

**AE4 — Approval trace.** A reviewer can navigate from a Finding to the approved Conclusion revision, the AI proposal and edits, and the exact Evidence version/location.

**AE5 — No blended score.** An integrated report for DPDPA, ISO 27001, and NIST CSF shows separated framework results plus consolidated Findings/Actions and contains no averaged engagement or cross-framework compliance score.

**AE6 — Client upload boundary.** A valid magic link can submit only named request items. Expired, revoked, or cross-Engagement use is denied and reveals no existence information about other records.

**AE7 — AWS snapshot.** A manual AssumeRole run stores no credential, performs only allowed Config/Security Hub reads, and creates immutable Evidence versions with account, region, collection time, and source identifiers.

**AE8 — Closure verification.** An Action cannot become Closed until closure Evidence is linked and a consultant records a verification event.

---

## Key technical decisions

**KTD-1 — Additive shadow schema and staged cutover.** New normalized tables are added beside legacy tables. Backfills preserve IDs and record provenance. Compatibility reads/dual-writes remain until reconciliation tests pass; old columns are not removed in this program's early phases.

**KTD-2 — Adopt Alembic before hierarchy changes.** Versioned, reviewable, repeatable migrations replace new DIY startup migrations. The existing bridge remains temporarily for deployed databases but is frozen after a tested handoff migration. SQLite remains supported for the boutique release; PostgreSQL is not a prerequisite.

**KTD-3 — Import legacy identity conservatively.** Backfill one Client per exact normalized company name after producing a collision report, and one imported Engagement per legacy Assessment. Do not infer shared Engagement scope from same-name records. Consultants may consolidate later through an audited operation.

**KTD-4 — Immutable record/history primitives.** EvidenceVersion, AnalysisRun, AnalysisClaim, ConclusionRevision, ApprovalEvent, ActionUpdate, ClosureVerification, ReportSnapshot, and AuditEvent are append-only. Current-state projections may be mutable/rebuildable; historical facts are not.

**KTD-5 — Citations bind to Evidence versions.** A Citation never points only to a filename or mutable Evidence record. It includes a format-aware location and verification state. Explicit Evidence absence is a typed support record, not an empty quote.

**KTD-6 — Separate Response, claim, Conclusion, Finding, and Action.** Questionnaire responses capture facts; claims interpret Evidence; Conclusions are consultant decisions; Findings are reportable implications; Actions are remediation work. No one table carries all five responsibilities.

**KTD-7 — One published-pack policy.** Registry presence does not imply selectability. A pack version becomes selectable only when content completeness, source provenance, automated integrity checks, product approval, and licensing approval pass. All web and API entry points use the same policy.

**KTD-8 — One scoring facade, no blended rollup.** Deterministic calculations run per Assessment and framework against approved Conclusions under a recorded methodology version. `Insufficient evidence` behavior must be explicitly decided before cutover. Engagement views aggregate counts, Findings, and Actions—not framework scores.

**KTD-9 — Capability-scoped client links.** Magic links authorize one set of request items, not a client session. Store a token digest, expire and revoke grants, minimize error disclosure, and reuse the same ingestion service as consultant uploads.

**KTD-10 — AWS is an Evidence source adapter.** Manual collectors produce raw and normalized Evidence versions. Temporary AssumeRole credentials live only for the run. The first adapter supports Config and Security Hub only and has no write or scheduling path.

**KTD-11 — Derived workflow projection.** Portfolio status, progress, blockers, review counts, outstanding Evidence, deadlines, and last activity are computed from domain state and Audit events. Archive remains explicit metadata; it is not inferred.

**KTD-12 — Preserve provider abstraction.** Retain `llm_client.py` and its privacy/validation posture. Introduce provider-neutral analysis modules and leave compatibility imports for `claude_analyzer.py` until callers and tests migrate.

---

## High-level technical design

```text
HTTP / HTMX / API
        │
        ▼
Application services
  portfolio · scope · evidence · requests · analysis · review · actions · reports
        │
        ├───────────────┬───────────────────┬────────────────────┐
        ▼               ▼                   ▼                    ▼
Domain records     Provider adapter    AWS source adapter   Storage adapter
Client             llm_client          AssumeRole           local blob store
Engagement         validation          Config               future object store
Assessment         provenance          Security Hub
Evidence/Citation
Conclusion history
Finding/Action
        │
        ▼
Versioned migrations + SQLAlchemy persistence + audit events
```

The write path uses domain services even while legacy routes remain. Read models serve the portfolio and Workpaper so templates do not reconstruct business state. Background job infrastructure may be introduced when analysis/AWS execution needs durability, but the domain record and idempotency contract must not depend on a specific queue.

### Target data flow

```text
scope → deduplicated request items → Evidence versions → extraction/claims
      → Requirement workpaper → AI proposal → consultant revisions/approval
      → framework calculation → Findings → Actions → versioned outputs
```

Evidence reuse branches at `EvidenceUse`: it reuses a version and records confirmation, while analysis and Conclusion creation continue normally for the new Assessment.

---

## Architecture boundaries

### Domain layer

SQLAlchemy models define identity and durable state, but cross-aggregate mutations go through services. Models should not call LLMs, AWS, storage, or template code.

### Pack layer

`app/frameworks/` owns published methodology content, pack metadata, applicability definitions, UCC mapping, and deterministic calculation inputs. It does not own client Evidence or Conclusions.

### Evidence layer

The Evidence service owns versions, hashes, provenance, extraction state, lifecycle transitions, mappings, Citations, reuse confirmation, impact analysis, retention, and blob coordination. Existing `AssessmentDocument` becomes a compatibility adapter.

### Analysis layer

Provider-neutral orchestration creates Analysis runs and claims, validates structure/completeness, performs citation grounding, and proposes Conclusion revisions. It cannot approve a Conclusion or emit a final score.

### Decision and review layer

Conclusion services validate outcome/rationale/support, append revisions, record approvals, and emit impact/review state. Deterministic scoring consumes only eligible approved revisions.

### Reporting and remediation layer

Findings and Actions are independent durable records. Report services snapshot approved inputs. Engagement rollups select Findings/Actions while preserving their Assessment origin.

### Integration layer

Magic links and AWS collectors are scoped adapters that call Evidence application services. They do not bypass validation, provenance, audit, or retention behavior.

---

## Migration and backward compatibility

### Preflight and safety

1. Back up the SQLite database and upload tree together and record hashes/counts.
2. Inventory orphan rows, duplicate assumed-unique records, invalid JSON, missing files, and legacy answer values. Quarantine rather than delete anything audit-relevant.
3. Repair and regression-test the questionnaire table rebuild so it preserves `cluster_id`, `answer_source`, and every populated column.
4. Add an Alembic baseline representing the current schema and a migration ledger. Startup must refuse an unknown schema rather than improvising destructive repair.

### Hierarchy backfill

- Preserve every `Assessment.id`.
- Create a Client candidate per trimmed/case-folded company name and emit a collision report for variants; do not merge ambiguous records silently.
- Create one imported regulatory-gap Engagement per legacy Assessment, linked to its Client. This preserves unknown historical scopes.
- Add `engagement_id` nullable first, backfill and reconcile, then make it required for new records. Keep `company_name`, industry, and size as compatibility projections during dual-read.
- Replace company-name comparison with Client ID plus explicit checks for pack/version, scope, and cut-off comparability.

### Pack and scope backfill

- Create pack/version rows for the exact legacy definitions. Treat null/malformed `selected_frameworks` as an inferred DPDPA legacy selection and record that provenance.
- Convert selected frameworks and applicable-requirement JSON into normalized AssessmentPack and RequirementApplicability rows while retaining the snapshots for comparison.
- Preserve existing scope/context JSON as immutable legacy source data even after structured scope fields exist.

### Evidence backfill

- Create one Evidence and one EvidenceVersion for each `AssessmentDocument`; retain the original blob path initially and calculate a hash when the file exists.
- Flag missing blobs rather than fabricating content or dropping the record.
- Convert desk-review evidence findings into imported Analysis claims/Citations when the source can be resolved. Mark unresolved free-text references as legacy-unverified.
- Do not automatically share imported Evidence across Assessments; reuse begins only after Client ancestry and consultant confirmation are available.

### Conclusion/report/action backfill

- Convert each `GapItem` AI field set into an imported proposal revision and the current field set into an imported consultant revision; preserve reviewer metadata as an imported Approval event when the Assessment is approved.
- Do not map every `not_assessed` to `Insufficient evidence` blindly. Produce a review queue for ambiguous records.
- Preserve existing GapReport/RFI bytes or data as legacy Report snapshots. Never regenerate history to make it look current.
- Convert remediation fields into an initial Action and ActionUpdate only where the GapItem represents a reportable gap. Preserve closure timestamps as imported events; require new closure verification rules prospectively.

### Cutover gates

Each table family needs row-count, ID, relationship, hash, and semantic reconciliation. Add foreign keys, uniqueness, and check constraints only after diagnostics are clean. Keep old URLs through redirects/adapters until browser and golden-report parity is demonstrated.

---

## Implementation units and phased delivery

### U1. Establish migration, pack, and contract foundations

**Goal:** Make schema evolution safe, centralize pack publication, repair baseline test isolation, and freeze target vocabulary before new domain records appear.

**Requirements:** PR-010, PR-011, PR-042, PR-045, PR-056  
**Dependencies:** None

**Files:**

- `requirements.txt`
- `alembic.ini`
- `alembic/`
- `app/main.py`
- `app/frameworks/schema.py`
- `app/frameworks/registry.py`
- `app/frameworks/definitions/dpdpa.py`
- `app/frameworks/definitions/iso27001.py`
- `app/frameworks/definitions/nist_csf.py`
- `app/routers/assessments.py`
- `app/routers/web.py`
- `app/templates/base.html`
- `tests/test_startup_invariants.py`
- `tests/test_content_integrity.py`
- `tests/test_picker_and_scoring_contract.py`
- `tests/test_template_environment.py`
- `docs/architecture/data-flow-and-processes.md`

**Approach:**

1. Baseline the current schema in Alembic and define the temporary relationship with `_run_migrations`; stop adding new domain migrations to startup code.
2. Fix the SQLite questionnaire rebuild and add a populated legacy-table regression fixture.
3. Extend pack metadata with product revision, effective/source dates, publication state, source provenance, content validation, and licensing approval.
4. Complete the DPDPA 2023 + final Rules 2025 and ISO 27001 clauses 4–10/risk treatment/SoA content only after source/licensing review. Keep NIST CSF 2.0 under the same publication gate.
5. Centralize selectability so web and API reject unpublished/roadmap versions identically.
6. Define the five target Conclusion outcomes and scoring-methodology version contract without changing production report behavior yet.
7. Make template globals deterministic in tests instead of depending on import order.

**Patterns to follow:** Existing framework integrity tests, startup invariant tests, registry schema, and legacy DPDPA golden fixtures.

**Test scenarios:**

- A populated legacy questionnaire table migrates without losing answer source, cluster, notes, or identifiers.
- Running migrations twice is idempotent and preserves all rows.
- Web and API expose exactly the published DPDPA, ISO 27001, and NIST CSF versions.
- A registered but unpublished GDPR version cannot be selected through either channel.
- Each published pack has required provenance/effective/licensing metadata and complete question/control integrity.
- Templates render in isolation and through the application with identical branding defaults.

**Verification:** A copied populated database migrates twice without drift; framework integrity and picker contracts pass; a reviewer confirms pack content/licensing evidence before publish state is enabled.

**Smoke test:** Start the app against a copied legacy database, create one Assessment with each launch pack through the web and API, and reopen an existing Assessment URL.

### U2. Add Client, Engagement, scope, archive, and portfolio projections

**Goal:** Introduce the target hierarchy and workflow-derived portfolio without breaking legacy Assessment routes.

**Requirements:** PR-001–PR-005, PR-012, PR-013, PR-056  
**Dependencies:** U1

**Files:**

- `app/models/client.py`
- `app/models/engagement.py`
- `app/models/assessment.py`
- `app/models/audit.py`
- `app/models/__init__.py`
- `app/services/portfolio.py`
- `app/services/workflow_status.py`
- `app/services/archive.py`
- `app/services/assessment_scope.py`
- `app/routers/clients.py`
- `app/routers/engagements.py`
- `app/routers/web.py`
- `app/templates/pages/dashboard.html`
- `app/templates/pages/client.html`
- `app/templates/pages/engagement.html`
- `app/templates/pages/new_engagement.html`
- `tests/test_hierarchy_migration.py`
- `tests/test_portfolio.py`
- `tests/test_archive_and_purge.py`
- `tests/test_scope_contract.py`

**Approach:**

1. Add Client, Engagement, AssessmentPack selection, structured Assessment scope, and append-only AuditEvent tables.
2. Backfill conservatively using KTD-3 and produce a collision/reconciliation report.
3. Keep `/assessments/{id}` operational while adding Client and Engagement navigation.
4. Build a portfolio read model for derived status, evidence/review counts, deadlines, progress, high-priority gaps, and last activity.
5. Add archive/restore. Replace direct delete UI with dependency preview and retention-aware purge service; keep permanent deletion disabled until its policy passes review.
6. Duplicate structure and request templates only; never duplicate Conclusion state.

**Patterns to follow:** Server-rendered routes/templates in `app/routers/web.py`, assessment cards, current scope flow, and UTC/UUID model conventions.

**Test scenarios:**

- Legacy Assessments retain IDs and URLs and receive one imported Engagement each.
- Name variants produce a collision report rather than silent Client merge.
- One Client owns several Engagements and each Engagement owns different Assessment types/scopes.
- Derived status changes when Evidence or review state changes and cannot be overwritten by a label.
- Archive hides an Engagement by default, archive filters reveal it, and restore returns it.
- Purge refuses cited/retained Evidence and previews every dependent record/blob.
- Covers AE3. Duplication creates new identities, copies allowed structure, and contains no Conclusions.

**Verification:** Reconciliation reports show no lost Assessment; portfolio counters equal direct database calculations; old links, new hierarchy navigation, archive, and duplication work in browser tests.

**Smoke test:** Open the portfolio with seeded active, waiting, review, completed, and archived Engagements; resume each; archive/restore one; duplicate one and verify the new Assessment has no Conclusions.

### U3. Build the general Evidence, Citation, request, and magic-link foundation

**Goal:** Make all evidence inputs versioned, reusable, precisely citable, and collectible through scoped client links.

**Requirements:** PR-020–PR-026, PR-055, PR-056  
**Dependencies:** U2

**Files:**

- `app/models/evidence.py`
- `app/models/evidence_request.py`
- `app/models/assessment.py`
- `app/services/evidence.py`
- `app/services/evidence_ingestion.py`
- `app/services/evidence_impact.py`
- `app/services/evidence_requests.py`
- `app/services/document_processor.py`
- `app/services/storage.py`
- `app/services/upload_grants.py`
- `app/routers/evidence.py`
- `app/routers/evidence_requests.py`
- `app/routers/client_upload.py`
- `app/templates/pages/evidence_library.html`
- `app/templates/pages/evidence_request.html`
- `app/templates/pages/client_upload.html`
- `app/templates/partials/documents_tab.html`
- `tests/test_evidence_migration.py`
- `tests/test_evidence_lifecycle.py`
- `tests/test_citations.py`
- `tests/test_evidence_requests.py`
- `tests/test_client_upload_grants.py`
- `tests/test_storage_lifecycle.py`

**Approach:**

1. Add Evidence, immutable EvidenceVersion, EvidenceUse, Requirement mapping, Citation, explicit EvidenceAbsence, request/item, and token-digest records.
2. Put consultant and client uploads through one validation/storage/extraction service with source-specific provenance.
3. Add page/section/table/image/AWS-ready location types and deterministic quote verification where applicable.
4. Migrate `AssessmentDocument` without moving blobs first; reconcile file existence and hashes.
5. Generate deduplicated request items from scope/UCC mappings and preserve all requirement links.
6. Implement expiring/revocable capability links with generic denial responses and no client account.
7. Add reuse suggestions showing age/original scope and explicit confirmation.
8. Implement preview-first lifecycle impact for supersede, expire, rescope, invalidate, and purge.

**Patterns to follow:** Current document-type detection/extraction, desk-review source fields, UCC control mappings, and review-release deny behavior.

**Test scenarios:**

- Covers AE1. One request item maps to multiple framework Requirements and is shown once to the client.
- One EvidenceVersion supports multiple Requirements and Assessments without sharing a Conclusion.
- A citation resolves to immutable version, quote, and format-appropriate location; a fabricated quote fails verification.
- Covers AE2. Evidence replacement previews and marks every affected draft and approved Conclusion.
- Reuse requires confirmation and records age/scope/version in its audit event.
- Covers AE6. Valid, expired, revoked, replayed, and wrong-item magic-link operations enforce the capability boundary.
- Oversized, mismatched MIME, malware-quarantined, empty extraction, and failed storage cases leave no active EvidenceVersion or orphan blob.
- Legacy documents with missing files remain visible as flagged records.

**Verification:** Evidence/reference counts reconcile with legacy documents; request mapping has no duplicates; security tests prove scoped denial; citations navigate from questionnaire to source.

**Smoke test:** Create one multi-framework request, upload one document as a consultant and one response through a client link, reuse the consultant Evidence in a second Assessment, then replace it and inspect the impact preview.

### U4. Introduce immutable analysis, claims, Conclusion history, and the authoritative workpaper

**Goal:** Turn the questionnaire into a traceable Requirement workpaper and separate AI proposals from consultant-approved Conclusions.

**Requirements:** PR-014, PR-022, PR-040–PR-045, PR-055–PR-056  
**Dependencies:** U1, U3

**Files:**

- `app/models/analysis.py`
- `app/models/conclusion.py`
- `app/models/questionnaire.py`
- `app/services/assessment_analyzer.py`
- `app/services/claim_validation.py`
- `app/services/conclusions.py`
- `app/services/scoring.py`
- `app/services/claude_analyzer.py`
- `app/services/question_engine.py`
- `app/routers/analysis.py`
- `app/routers/questionnaire.py`
- `app/routers/review.py`
- `app/routers/web.py`
- `app/templates/pages/assessment.html`
- `app/templates/pages/review.html`
- `app/templates/partials/questionnaire_tab.html`
- `app/templates/partials/review_finding_card.html`
- `tests/test_analysis_runs.py`
- `tests/test_claim_validation.py`
- `tests/test_conclusion_history.py`
- `tests/test_workpaper.py`
- `tests/test_scoring_contract.py`
- `tests/test_incomplete_assessment_e2e.py`
- `tests/test_golden_dpdpa.py`

**Approach:**

1. Add immutable AnalysisRun/Claim and Conclusion/Revision/ApprovalEvent records with pack, prompt, provider/model, evidence-set, validation, actor, and timestamp provenance.
2. Move orchestration to provider-neutral services while keeping compatibility exports from `claude_analyzer.py`.
3. Ground every Evidence-derived claim, assess relevance/sufficiency/currency/period/scope, represent contradictions, and separate design from operating effectiveness.
4. Render each applicable Requirement as response + Evidence/Citations + claims/quality + proposal + editable final decision.
5. Require one of the five target outcomes and complete rationale/support/gap/risk/action fields before approval.
6. Preserve every edit and approval. Allow same-person approval but make it explicit.
7. Consolidate deterministic calculation behind one per-framework facade using approved revisions only. Disable blended multi-framework output at the new read boundary.
8. Backfill legacy GapItems and ambiguous `not_assessed` records using the migration rules above.

**Patterns to follow:** Existing `validate_and_filter`, quote grounding, `needs_review`, review gate, UCC expansion, and golden DPDPA tests.

**Test scenarios:**

- An incomplete or unknown-control model response fails closed and creates no proposed complete report.
- Unsupported Compliant proposals require review and cannot be approved without evidence or typed absence.
- Each quality dimension is independently visible; contradictory Evidence remains visible beside the proposal.
- All five outcomes validate; Not applicable needs rationale; Insufficient evidence remains distinct from Non-compliant and unanswered.
- Covers AE4. Proposal, multiple edits, approval, and later re-review remain queryable in order.
- Multi-framework UCC response fans out to pack controls while final Conclusions remain separate.
- Deterministic output is reproducible for the same approved revisions and records methodology version.
- Covers AE5. No new API, Workpaper, or calculation response emits a blended cross-framework score.

**Verification:** Golden single-framework output remains explainable; new history and Workpaper tests pass; a reviewer traces a sample Conclusion to exact source; deterministic calculations match fixed fixtures.

**Smoke test:** Run a DPDPA + ISO 27001 + NIST CSF Assessment from shared responses/Evidence, edit and approve one Conclusion per pack, and confirm distinct calculations and complete history.

### U5. Separate Findings and Actions and produce versioned workpapers/reports

**Goal:** Deliver approved, versioned outputs and consultant-operated remediation without tying Action history to regenerated report rows.

**Requirements:** PR-050–PR-056  
**Dependencies:** U4

**Files:**

- `app/models/finding.py`
- `app/models/action.py`
- `app/models/report.py`
- `app/models/rfi.py`
- `app/services/findings.py`
- `app/services/actions.py`
- `app/services/report_snapshots.py`
- `app/services/rfi_generator.py`
- `app/routers/remediation.py`
- `app/routers/reports.py`
- `app/routers/review.py`
- `app/utils/pdf_export.py`
- `app/utils/rfi_export.py`
- `app/templates/partials/report_summary.html`
- `app/templates/partials/remediation_panel.html`
- `app/templates/pages/engagement.html`
- `tests/test_findings_and_actions.py`
- `tests/test_closure_verification.py`
- `tests/test_report_snapshots.py`
- `tests/test_release_gate.py`
- `tests/test_integrated_report.py`
- `tests/test_golden_dpdpa.py`

**Approach:**

1. Create durable Finding origin links and independent Action/Update/ClosureVerification records.
2. Convert selected approved Conclusions into Findings without losing revision or Citation references.
3. Roll selected Findings and Actions to the Engagement; keep Conclusion data at Assessment/framework scope.
4. Require closure Evidence and consultant verification before Closed.
5. Create immutable Workpaper, Assessment report, integrated Engagement report, and RFI snapshots bound to approved revisions and evidence cut-off.
6. Separate framework sections/appendices and remove combined-score copy and visuals from multi-framework outputs.
7. Gate both endpoint and UI affordances until release criteria pass.

**Patterns to follow:** Existing report/RFI exporters, `S()` PDF sanitization, remediation partials, report view modes, and review approval guard.

**Test scenarios:**

- A Finding always resolves to Assessment, pack version, scope, cut-off, Conclusion revision, and Citations.
- An Action addresses Findings from several Assessments while each origin remains visible.
- Covers AE8. Closing without Evidence/verification is rejected; verify/close/reopen history remains intact.
- Regenerating a report or RFI creates a new snapshot and preserves prior issued output.
- Covers AE5. Integrated output separates framework/Assessment results and contains no blended score.
- Unapproved exports are hidden/disabled in UI and denied server-side.
- PDF text and metadata snapshots retain current DPDPA behavior where the product contract has not changed.

**Verification:** Workpaper traceability is complete; report snapshots are byte-addressable and versioned; closure state is reconstructable; PDF smoke and golden checks pass.

**Smoke test:** Approve Conclusions, create Findings/Actions, export Workpaper and integrated report, attach closure Evidence, verify/close/reopen an Action, and download both report versions.

### U6. Add the manual AWS Config and Security Hub evidence adapter

**Goal:** Collect narrow, read-only cloud evidence through the same Evidence lifecycle.

**Requirements:** PR-030–PR-031, PR-020–PR-022, PR-056  
**Dependencies:** U3

**Files:**

- `requirements.txt`
- `app/models/cloud.py`
- `app/integrations/aws/client.py`
- `app/integrations/aws/config_collector.py`
- `app/integrations/aws/security_hub_collector.py`
- `app/services/aws_snapshots.py`
- `app/routers/integrations.py`
- `app/templates/pages/aws_connection.html`
- `app/templates/partials/aws_snapshot_status.html`
- `tests/integrations/aws/test_assume_role.py`
- `tests/integrations/aws/test_config_collector.py`
- `tests/integrations/aws/test_security_hub_collector.py`
- `tests/test_aws_snapshot_evidence.py`

**Approach:**

1. Store connection configuration without credentials: role ARN, external-ID secret reference/digest strategy, allowed accounts/regions, and audit metadata.
2. Assume the role only for a consultant-triggered run and use temporary credentials in memory.
3. Collect a reviewed minimum set from AWS Config and Security Hub with paginated, bounded reads.
4. Preserve raw responses and normalized items as immutable Evidence versions with source identifiers, account, region, collection time, and collector version.
5. Map items through ordinary Evidence/Citation services; expose failure, partial, and stale states without implying full-cloud assurance.
6. Provide no write API, scheduled trigger, or broad service scan.

**Patterns to follow:** LLM provider adapter isolation, Analysis run status/provenance, and Evidence ingestion idempotency.

**Test scenarios:**

- Covers AE7. Successful AssumeRole/Config/Security Hub reads create immutable Evidence and persist no credential.
- Incorrect external ID, access denial, timeout, throttling, pagination, partial-region failure, and empty result are auditable and retry-safe.
- Collector methods cannot invoke write APIs and reject services outside Config/Security Hub.
- Repeating an identical snapshot is idempotent at run/request level while preserving separate collection history when intentionally rerun.

**Verification:** Mocked AWS contract tests prove exact allowed calls and denial behavior; security review validates least-privilege policy; Evidence traceability matches upload sources.

**Smoke test:** Assume a sandbox role manually, collect one Config resource and one Security Hub finding, map them to a Requirement, and inspect provenance and Citations; disable the role and verify a safe failed run.

### U7. Complete the portfolio, reassessment, retention, and longitudinal demo track

**Goal:** Prove the end-to-end product with realistic longitudinal histories and harden operational lifecycle behavior.

**Requirements:** PR-002–PR-004, PR-025–PR-026, PR-051–PR-056  
**Dependencies:** U2–U6

**Files:**

- `app/services/portfolio.py`
- `app/services/engagement_duplication.py`
- `app/services/retention.py`
- `app/services/workflow_status.py`
- `app/routers/engagements.py`
- `app/routers/web.py`
- `app/templates/pages/dashboard.html`
- `app/templates/pages/engagement.html`
- `scripts/seed_test_companies.py`
- `tests/fixtures/longitudinal/`
- `tests/test_engagement_duplication.py`
- `tests/test_retention_and_purge.py`
- `tests/test_longitudinal_demo.py`
- `tests/test_portfolio.py`
- `tests/browser/test_consultant_workspace.py`

**Approach:**

1. Finalize portfolio filters, resume actions, derived blockers/counters, deadlines, archived views, and last activity.
2. Add reassessment/validation creation using Client/Engagement ancestry and scope-aware comparability.
3. Finalize retention, legal hold, dependency previews, coordinated database/blob purge, and tombstone/audit policy.
4. Extend existing fictional personas into baseline, targeted review/remediation validation, and later reassessment histories.
5. Include valid/stale/rejected Evidence reuse, replacement impact, deduplicated cross-framework requests, distinct Conclusions, Action closure, and archive cases.
6. Run supervised browser journeys and consultant review sessions; record product gaps separately from fixture tuning.

**Patterns to follow:** Existing synthetic fixture builders, canonical DPDPA golden fixture, dashboard cards, and comparison view.

**Test scenarios:**

- Every portfolio status/count is derived from seeded domain records and changes when those records change.
- Covers AE3. Reassessment copies permitted structure and offers Evidence reuse without copying Conclusions.
- Scope/version/cut-off mismatch prevents misleading comparison or requires an explicit caveat.
- Retention/legal hold blocks purge; eligible purge removes database/blob data as one recoverable operation and retains the approved tombstone/audit record.
- Longitudinal personas prove baseline → remediation → validation, Evidence change impact, and distinct framework results.
- Archived Engagements disappear from default views and remain available through the archive filter.

**Verification:** The full migration and behavioral suite passes from a populated legacy fixture; browser journeys complete; product demo assertions pass independently of live LLM calls; a consultant can explain next action and trace a sampled Finding.

**Smoke test:** Run the complete demo for four fictional Clients, including one multi-framework reassessment, one client magic-link submission, one AWS snapshot, one Evidence invalidation, one closure verification, one integrated report, and one archive/restore cycle.

---

## Phase dependencies and rollout gates

```text
U1 migration + pack contract
 ├─→ U2 hierarchy/portfolio ─→ U3 evidence/client collection ─→ U4 workpaper/conclusions ─→ U5 reports/actions
 │                                └─→ U6 AWS adapter ───────────────────────────────┐
 └──────────────────────────────────────────────────────────────────────────────────┴─→ U7 hardening/demo
```

| Gate | Required evidence |
|---|---|
| U1 → U2 | Versioned migration baseline; no column loss; launch-pack publication policy and licensing/content sign-off. |
| U2 → U3 | Legacy hierarchy reconciliation; stable old URLs; archive/read models operational. |
| U3 → U4 | Evidence migration reconciled; Citation and impact tests; magic-link security tests. |
| U4 → U5 | Conclusion history and approval complete; scoring decision for Insufficient evidence; no blended output in new path. |
| U3 → U6 | Evidence source adapter contract stable; secrets and storage design reviewed. |
| U5/U6 → U7 | Versioned reports, independent Actions, AWS evidence, and retention behavior available behind rollout flags. |

Use feature flags or configuration gates for hierarchy reads, client links, new Workpaper, report snapshots, and AWS. Deploy migrations and backfills before switching reads. Keep rollback as a read-path rollback; do not attempt to delete newly created history during rollback.

---

## Verification strategy

### Automated layers

- Schema migration tests against empty, current, populated legacy, duplicate/orphan, malformed JSON, and missing-blob fixtures.
- Domain tests for lifecycles, invariants, authorization, impact propagation, history, calculation, retention, and idempotency.
- Integration tests crossing route → service → database → storage, plus mocked LLM and AWS adapters.
- Golden tests for DPDPA analysis/calculation and PDF text/metadata.
- Browser tests for portfolio, scope, request, magic-link upload, Workpaper review, report release, Action closure, reassessment, and archive.
- Content integrity checks for pack versions, UCC mappings, questions, provenance, publication state, and licensing approval.

### Migration proof

For each migration phase, record before/after row counts, IDs, orphan counts, relationship coverage, hashes, and semantic samples. Rehearse forward migration twice and restore from backup. Preserve the exact legacy fixture that exposed the questionnaire column-loss risk.

### Security proof

Test object-level authorization, generic token failures, expiry/revocation, upload validation/quarantine, log redaction, secret absence, AWS allowed-call lists, retention holds, and audit attribution. Review threat boundaries before exposing client links or AWS to a pilot.

### Human validation

Run the four-persona longitudinal demo with at least two practising consultant reviewers. Validate navigation, terminology, the distinction between response/proposal/Conclusion, report disclaimers, Evidence reuse judgment, and whether portfolio blockers match real working practice. Synthetic accuracy is not a substitute for these sessions.

---

## Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Legacy orphans/duplicates break new constraints | Migration failure or silent loss | Preflight inventory, quarantine, additive nullable links, reconciliation, constraints last. |
| DIY migration and SQLite rebuild lose columns | Audit/provenance loss | Repair first, adopt Alembic, migrate populated fixture, back up database + blobs together. |
| Same-name Clients are merged incorrectly | Cross-client data exposure | Collision report, conservative import, explicit audited merge only. |
| Pack content is incomplete or unlicensed | Invalid methodology or redistribution exposure | Publish gate, legal/content review, product-authored questions, source/reference provenance. |
| `Insufficient evidence` distorts scores | Misleading posture | Settle denominator rule with methodology review; show coverage separately; record version. |
| Evidence invalidation floods review queues | Operational overload | Impact preview, severity/materiality rules, batched review, never silent auto-approval. |
| Magic links expose client data | Confidentiality breach | Token digest, narrow capability, short expiry, revocation, generic errors, rate limits, audit. |
| Uploads or extracted content are unsafe | Malware/data leakage | Quarantine, MIME/content checks, scanning hook, storage isolation, log minimization. |
| Long analysis/AWS calls block requests | Timeouts/duplicate runs | Durable run records and idempotency now; introduce queue/worker when measured need crosses threshold. |
| Old/new read paths disagree | Consultant confusion | Dual-read parity instrumentation, feature flags, sample comparison, one-way staged cutover. |
| Report snapshots grow storage | Cost/retention risk | Content addressing, retention policy, explicit issued-artifact preservation, measured cleanup. |
| Current terminology overclaims compliance | Legal/reputational risk | Replace certification/legal-compliance language with assessed-posture disclaimers in UI and outputs. |

---

## Explicit non-goals

- Do not build client accounts or a general client portal.
- Do not schedule AWS collection or market it as continuous monitoring.
- Do not add broad integrations beyond AWS Config and Security Hub.
- Do not add client-defined packs or spreadsheet/CSV pack imports.
- Do not require maker-checker separation in v1.
- Do not let clients operate Actions.
- Do not produce autonomous legal declarations, certification, or attestation.
- Do not calculate an Engagement or cross-framework blended compliance score.
- Do not migrate to PostgreSQL merely to complete this program.
- Do not introduce enterprise organization/role administration beyond the minimum internal actor and capability model.
- Do not rewrite the Jinja2/HTMX application as a client-side SPA.

---

## Later decision points

These decisions are required at the named gate; they are not invitations to revisit the settled product direction.

1. **Before publishing pack updates (U1):** licensed content strategy for ISO 27001 and any other copyrighted standards.
2. **Before scoring cutover (U4):** deterministic denominator/presentation behavior for Insufficient evidence and legacy `not_assessed` migration.
3. **Before client-link pilot (U3):** token lifetime, rate limits, upload size, scanning service, and default retention/legal-hold policy.
4. **Before automatic re-review behavior (U3/U4):** which Evidence lifecycle events mandate re-approval versus warnings.
5. **Before AWS pilot (U6):** minimum Config resource types, Security Hub fields, regions, and least-privilege reference policy.
6. **Before worker infrastructure:** measured request duration, duplicate-run rate, and deployment topology that justify a queue; do not choose a queue preemptively.
7. **Before legacy-column removal:** two successful releases with read parity, complete reconciliation, rollback rehearsal, and no consumers of compatibility fields.

---

## Documentation and operational updates

- Rewrite `docs/architecture/data-flow-and-processes.md` after each cutover so it describes provider-neutral analysis, normalized Evidence, Conclusion history, and current pack behavior.
- Add an operator migration/backup/restore runbook and a retention/purge runbook.
- Document the client magic-link threat model and AWS least-privilege setup.
- Version assessment methodology and report disclaimers with pack releases.
- Keep demo data explicitly fictional and free of credentials or confidential client material.

---

## Definition of done

- Client → Engagement → Assessment is the canonical navigable model, with legacy Assessment IDs preserved.
- Portfolio status and counters derive from real Evidence, Conclusion, deadline, Finding, Action, and activity state.
- All three launch packs are complete for the stated scope, versioned, source-traceable, validated, and legally approved for intended use.
- Shared questions and Evidence requests are deduplicated without sharing framework-specific Conclusions.
- All Evidence inputs use immutable versions, provenance, precise Citations, lifecycle, reuse confirmation, and impact tracking.
- Client magic links are scoped, expiring, revocable, audited, and require no client account.
- AWS collection is manual, read-only, AssumeRole/external-ID based, and limited to Config and Security Hub.
- Every AI proposal receives consultant review; complete proposal/edit/approval history is retained.
- Final outcomes use the five settled labels and deterministic calculations are separate, versioned, and based on approved Conclusions.
- Findings and Actions roll up operationally while Conclusions remain bound to Assessment scope/version/cut-off.
- Workpapers, integrated reports, and RFIs are versioned snapshots; no unapproved output releases.
- No Engagement or cross-framework blended compliance score remains in target UI/API/report semantics.
- Archive is normal; permanent deletion is explicit, retention-aware, dependency-checked, and coordinates database and blob state.
- Migration, unit, integration, golden, security, browser, and longitudinal demo checks pass from a populated legacy fixture.
- Existing unrelated user changes remain untouched.

---

## Open questions for adversarial review

1. Is the additive schema/cutover sequence conservative enough for the current unversioned SQLite database, or should any legacy record family remain read-only indefinitely?
2. Does one imported Engagement per legacy Assessment preserve enough reassessment utility, or is there a safe evidence-based grouping rule beyond exact Client-name normalization?
3. Are ConclusionRevision, ApprovalEvent, Finding, and Action boundaries sufficient to reconstruct all judgment and remediation history without duplicating too much state?
4. What licensed/approved source strategy should replace or constrain the current ISO Annex A descriptions and support clauses 4–10, risk treatment, and SoA?
5. Should Insufficient evidence be excluded from a score denominator, counted separately with a coverage threshold, or prevent a score from being presented at all?
6. Which Evidence changes should automatically mark issued report snapshots as superseded, and which should only create a visible post-issuance warning?
7. What citation location model is precise enough across PDF, DOCX tables, images, written responses, Config resources, and Security Hub findings without becoming brittle?
8. Is the AWS v1 slice narrow enough, and which exact read permissions/resource types prove value while avoiding a monitoring or attestation implication?
9. What rollout metric should trigger background workers for analysis and AWS collection rather than the initial durable-run/in-request approach?
10. Which existing report score displays can remain as per-framework methodology outputs, and which copy or visuals still imply a prohibited blended posture?
