# Revised Implementation Plan: Consultant Assessment Workspace

**Status:** Ready for implementation
**Date:** 2026-09-21
**Supersedes:** `docs/plans/2026-09-21-001-feat-consultant-assessment-workspace-plan.md`
**Product contract:** `docs/product/2026-09-21-cyberassess-product-requirements.md`
**Decisions log:** `tasks/2026-09-21-adversarial-review.md` (D1–D11)
**Strategy:** Clean-break migration in 4 phases + pre-work
**Target stack:** FastAPI, SQLAlchemy, Alembic, Jinja2, HTMX, Tailwind, SQLite

---

## Summary

Evolve CyberAssess from a flat assessment list into a consultant portfolio organized as Client → Engagement → Assessment. This is a clean-break migration — not additive shadow tables. The current database is empty (no production users); the migration script handles any rows that appear before cutover.

The program is structured as a 1-week pre-work sprint fixing live bugs and building test infrastructure, followed by 4 implementation phases that each produce a shippable, testable state.

---

## Current State (Code-Verified)

### What exists and works
- Assessment CRUD with company_name/industry/company_size baked into Assessment
- Framework selection (DPDPA, ISO 27001, NIST CSF enabled; GDPR, HIPAA, PCI-DSS registered but roadmap)
- 52 UCC clusters in `app/frameworks/mappings/clusters.py` (1041 lines) — question deduplication across frameworks
- Questionnaire engine with per-cluster questions, answer persistence, follow-up generation
- Document upload (AssessmentDocument: 7 columns, no versioning, no hashing, no lifecycle)
- Desk review pipeline (DeskReviewSummary + DeskReviewFinding — re-runs delete all findings)
- Analysis pipeline via OpenRouter (`app/services/claude_analyzer.py` + `app/services/llm_client.py`) — re-runs delete GapReport + all GapItems
- Deterministic scoring (`app/services/scoring.py`, 714 lines) — per-framework works, blended `compute_unified_maturity()` exists, multi-framework `score()` raises NotImplementedError
- Consultant review workflow (review_status, needs_review flags on GapItem)
- Remediation tracking (fields on GapItem: status, owner, target_date, notes, closed_at)
- RFI generation (RFIDocument model)
- PDF/DOCX export (`app/utils/pdf_export.py`, 1094 lines)
- 128 passing tests, 20 warnings; only 2 tests use TestClient for HTTP integration

### What's broken or missing
- **Questionnaire rebuild drops columns** — `main.py:83-117` recreates the table with 8 hardcoded columns, dropping `cluster_id` and `answer_source` on incrementally-upgraded DBs
- **Analysis/desk review destroy history** — `trigger_analysis` deletes GapItems/GapReport before re-running; `run_desk_review_web` deletes DeskReviewFindings
- **Zero foreign keys** — all cross-table references are bare string columns; deletes leave orphans
- **Branding import-order bug** — `main.py:21` sets template globals as side effect; tests that skip `main.py` get undefined `branding`
- **No HTTP integration tests** — 128 tests are unit/fixture-comparison; no route-level testing
- **Blended score on GapReport.overall_score** — used in comparison page, report summary, PDF; prohibited by product requirements

### Existing tables (7 models, 289 lines total)

| Table | PK | Parent ref | Notes |
|-------|-----|------------|-------|
| `assessments` | UUID str | — | Aggregate root. Company identity, scope, framework selection, screening, review status. 21 columns. |
| `assessment_documents` | UUID str | `assessment_id` str | 7 columns. No versioning, hashing, or lifecycle. |
| `questionnaire_responses` | UUID str | `assessment_id` str | 11 columns including `cluster_id`, `answer_source`. Check constraint on `answer`. |
| `desk_review_summaries` | int autoincrement | `assessment_id` str (unique) | JSON blobs for catalog and coverage. |
| `desk_review_findings` | int autoincrement | `assessment_id` str | Per-requirement findings with source quotes. |
| `gap_reports` | UUID str | `assessment_id` str (unique) | Overall + framework scores, executive summary. |
| `gap_items` | UUID str | `report_id` str | 28 columns. AI vs consultant fields, remediation, review status. |
| `initiatives` | UUID str | `report_id` str | Remediation initiative groupings. |
| `rfi_documents` | UUID str | `assessment_id` str (unique) | Generated RFI content. |

### Route structure

45+ routes in `app/routers/web.py` (1781 lines), all under `/assessments/{assessment_id}/...`. Additional API routes in `analysis.py`, `assessments.py`, `desk_review.py`, `documents.py`, `questionnaire.py`, `remediation.py`, `reports.py`, `review.py`.

---

## Target Schema

Clean-break design. New tables replace the flat model; a one-shot migration script maps existing rows.

### New tables

```
clients
├── id: UUID str (PK)
├── name: str (unique)
├── industry: str
├── size: str
├── retention_years: int (default 7)  ← D11
├── created_at, updated_at: datetime

engagements
├── id: UUID str (PK)
├── client_id: UUID str (FK → clients.id, ON DELETE RESTRICT)
├── name: str
├── type: str (default "gap_assessment")
├── status: str (derived; see lifecycle)
├── created_at, updated_at: datetime

assessments  (evolved — new columns, FKs added)
├── id: UUID str (PK)  ← stable, no change
├── engagement_id: UUID str (FK → engagements.id, ON DELETE RESTRICT)
├── company_name: str  ← frozen after migration, read from client for display
├── [all existing columns preserved]
├── version: int (default 1)  ← D6 optimistic locking

assessment_packs  (join entity — D3/P2 fix)
├── id: UUID str (PK)
├── assessment_id: UUID str (FK → assessments.id)
├── framework_id: str
├── pack_version: str
├── created_at: datetime

evidence
├── id: UUID str (PK)
├── engagement_id: UUID str (FK → engagements.id)
├── original_filename: str
├── storage_path: str
├── file_hash_sha256: str
├── file_size_bytes: int
├── mime_type: str
├── status: str  ← lifecycle states (see below)
├── uploaded_by: str (consultant | client_link:{token_prefix})
├── created_at: datetime

evidence_versions
├── id: UUID str (PK)
├── evidence_id: UUID str (FK → evidence.id)
├── version_number: int
├── storage_path: str
├── file_hash_sha256: str
├── file_size_bytes: int
├── change_reason: str | null
├── created_at: datetime

evidence_uses  (maps evidence to requirements across frameworks)
├── id: UUID str (PK)
├── evidence_id: UUID str (FK → evidence.id)
├── assessment_id: UUID str (FK → assessments.id)
├── requirement_id: str
├── framework_id: str
├── relevance: str (primary | supporting | contextual)
├── created_at: datetime

citations
├── id: UUID str (PK)
├── evidence_version_id: UUID str (FK → evidence_versions.id)
├── location_type: str (page | section | table_cell | config_item | finding_id)
├── location_ref: str
├── excerpt: text
├── created_at: datetime

analysis_runs  (replaces destructive re-run pattern)
├── id: UUID str (PK)
├── assessment_id: UUID str (FK → assessments.id)
├── framework_id: str
├── status: str (running | completed | failed)
├── claims_json: text  ← JSON array of per-requirement claims (D2: simplified)
├── model_id: str
├── started_at, completed_at: datetime

conclusions  (replaces GapItem for the target model)
├── id: UUID str (PK)
├── assessment_id: UUID str (FK → assessments.id)
├── requirement_id: str
├── framework_id: str
├── cluster_id: str | null
├── outcome: str  ← compliant | partially_compliant | non_compliant | not_applicable | insufficient_evidence
├── rationale: text
├── evidence_summary: text
├── gaps_identified: text
├── risk_level: str
├── recommended_action: text
├── ai_proposed: bool
├── version: int  ← D6 optimistic locking
├── created_at, updated_at: datetime

conclusion_revisions  (D2: single table replaces Conclusion+ConclusionRevision+ApprovalEvent)
├── id: UUID str (PK)
├── conclusion_id: UUID str (FK → conclusions.id)
├── actor: str
├── action: str (proposed | edited | approved | rejected | reopened)
├── previous_outcome: str | null
├── previous_rationale: text | null
├── citations_json: text | null  ← D2: JSON array, not relational CitationClaim table
├── created_at: datetime

findings
├── id: UUID str (PK)
├── assessment_id: UUID str (FK → assessments.id)
├── conclusion_id: UUID str (FK → conclusions.id)
├── title: str
├── description: text
├── severity: str
├── priority: int
├── status: str (open | in_progress | resolved | accepted_risk)
├── created_at, updated_at: datetime

actions
├── id: UUID str (PK)
├── finding_id: UUID str (FK → findings.id)
├── title: str
├── owner: str | null
├── target_date: datetime | null
├── status: str (open | in_progress | closed | verified)
├── history_json: text  ← D2: JSON array replaces ActionUpdate+ClosureVerification tables
├── created_at, updated_at: datetime

report_snapshots  (D2: one table for workpapers and reports)
├── id: UUID str (PK)
├── assessment_id: UUID str (FK → assessments.id) | null
├── engagement_id: UUID str (FK → engagements.id) | null
├── type: str (workpaper | gap_report | integrated_report)
├── format: str (pdf | html)
├── storage_path: str
├── generated_at: datetime
├── is_issued: bool (default false)  ← only issued snapshots are client-visible

magic_links
├── id: UUID str (PK)
├── engagement_id: UUID str (FK → engagements.id)
├── token_digest: str (SHA-256 of 128-bit token)  ← P8: never store raw token
├── scope_json: text  ← which evidence requests this link covers
├── max_uploads: int
├── max_size_bytes: int
├── expires_at: datetime
├── revoked_at: datetime | null
├── created_at: datetime

audit_events  (D2: one generic table replaces multiple event types)
├── id: UUID str (PK)
├── actor: str
├── action: str
├── entity_type: str
├── entity_id: str
├── metadata_json: text | null
├── created_at: datetime
```

### Evidence lifecycle states (P1 fix)

```
Requested → Uploaded → Quarantined → Active → Superseded → Archived → Purged
                                   ↘ Invalidated → Archived → Purged
                                   ↘ Rescoped → Active (requires consultant confirmation)
```

Transitions requiring consultant confirmation: Invalidated→Active (re-validation), Rescoped→Active, Active→Purged, Archived→Purged.
System-driven transitions: Uploaded→Quarantined (on upload), Quarantined→Active (scan pass), Active→Superseded (new version uploaded).

### Table count

**New: 15 tables** (clients, engagements, assessment_packs, evidence, evidence_versions, evidence_uses, citations, analysis_runs, conclusions, conclusion_revisions, findings, actions, report_snapshots, magic_links, audit_events)
**Preserved: 5 tables** (assessments with new columns + FKs, questionnaire_responses, desk_review_summaries, desk_review_findings, rfi_documents)
**Retired after migration verification: 3 tables** (gap_reports, gap_items, initiatives — data migrated to conclusions/findings/actions)
**Total active: 20 tables** (vs. current 9)

This is 8 net-new domain tables (D2 target) plus 7 supporting tables (packs, versions, uses, citations, links, snapshots, audit) that each serve a distinct, testable purpose.

---

## URL Strategy (I2)

Keep `/assessments/{assessment_id}/...` working by resolving the hierarchy from the assessment ID. Add new canonical paths:

```
/                                              → portfolio dashboard
/clients/{client_id}                           → client detail
/clients/{client_id}/engagements/{eid}         → engagement detail
/assessments/{assessment_id}/...               → all existing routes (unchanged URLs)
/evidence/{evidence_id}                        → evidence detail/versions
/magic/{token}                                 → client upload page (no auth)
```

No redirects needed. The assessment routes look up `engagement_id` and `client_id` from the assessment row. New navigation (breadcrumbs, portfolio) uses the hierarchical paths. Old bookmarks keep working.

---

## Pre-Work Sprint (Week 0)

**Goal:** Fix live bugs and build the test infrastructure that all phases depend on. Shippable independently — no schema changes.

### PW-1. Hotfix: questionnaire column rebuild
**File:** `app/main.py:83-117`
**What:** Add `cluster_id` and `answer_source` to the hardcoded CREATE TABLE in `_ensure_questionnaire_answer_constraint`. Add them to the INSERT...SELECT.
**Test:** Insert rows with `cluster_id` and `answer_source` populated, trigger the rebuild, assert values survive.
**Smoke:** `pytest tests/test_picker_and_scoring_contract.py -q` still passes.

### PW-2. Hotfix: stop destructive re-runs
**Files:** `app/routers/analysis.py:257-259`, `app/routers/web.py:1754-1756`
**What:** Before deleting GapItems/GapReport/DeskReviewFindings, serialize the about-to-be-deleted rows to a `_legacy_history` JSON column on GapReport / DeskReviewSummary. This preserves prior analysis for future backfill without changing the re-run behavior.
**Test:** Run analysis, re-run, assert `_legacy_history` contains the first run's data.

### PW-3. Fix branding import-order
**Files:** `app/main.py:21-25`, new `app/templates/config.py`
**What:** Extract template environment setup into `configure_templates()` called by both `main.py` and test `conftest.py`. Expose `get_templates()` that guarantees branding is set.
**Test:** The 5 previously-failing isolated template tests now pass.

### PW-4. Build HTTP integration test harness
**Files:** `tests/conftest.py`, new `tests/integration/`
**What:** Create a `conftest.py` fixture that yields a `TestClient` with a seeded SQLite database and mocked LLM client. Write one integration test per major route group:
- Assessment CRUD (create, read, delete)
- Document upload
- Questionnaire save
- Desk review trigger
- Analysis trigger
- Report rendering

**Acceptance:** At least 6 new integration tests passing. These become the regression baseline for all phases.

### PW-5. Add foreign keys to existing tables
**What:** Run orphan detection across all 9 tables. Quarantine orphaned rows (move to `_orphans` tables or delete if assessment_id doesn't exist). Add ForeignKey declarations to all model files. Add ON DELETE RESTRICT. Replace `db.delete(assessment)` with soft-delete (status = "archived").
**Test:** Attempting to delete an assessment with child rows raises IntegrityError. Orphan detection script finds zero orphans after cleanup.

**Pre-work exit criteria:** All existing 128 tests pass + new integration tests pass + no column-loss on questionnaire rebuild + no history destruction on re-run.

---

## Phase 1: Schema & Hierarchy (Weeks 1-3)

**Goal:** Target schema deployed. Client → Engagement → Assessment hierarchy working. Portfolio dashboard live. One-shot migration handles any legacy rows.

### P1-1. Adopt Alembic
- Add `alembic.ini`, `alembic/env.py`, `alembic/versions/`
- Generate initial migration from current models (baseline)
- Delete DIY `_run_migrations()` and `_ensure_questionnaire_answer_constraint()` from `main.py`
- Update `lifespan()` to run `alembic upgrade head` instead of `create_all` + `_run_migrations`
- **Test:** Fresh DB created by `alembic upgrade head` matches current schema. `alembic downgrade -1` + `upgrade head` is idempotent.

### P1-2. Create target schema
- Write Alembic migration for all new tables (clients, engagements, assessment_packs, evidence, evidence_versions, evidence_uses, citations, analysis_runs, conclusions, conclusion_revisions, findings, actions, report_snapshots, magic_links, audit_events)
- Add `engagement_id` FK and `version` column to assessments
- Add FKs to all existing child tables (if not done in PW-5)
- **Test:** `alembic upgrade head` on empty DB creates all tables with correct FKs. SQLite `.schema` output matches model definitions.

### P1-3. One-shot migration script
- `scripts/migrate_legacy.py` — idempotent, runs against any DB state:
  - For each distinct `company_name` in assessments: create a Client
  - For each Assessment: create an Engagement under its Client, link Assessment
  - For each Assessment's `selected_frameworks`: create AssessmentPack rows
  - Freeze `company_name` on Assessment (keep the column, never update it after migration)
  - Migrate GapItems → Conclusions (map compliance_status to outcome, carry AI vs consultant fields to conclusion_revisions)
  - Migrate GapItems with remediation fields → Findings + Actions
  - Migrate GapReport.framework_scores → per-assessment-pack score storage
- **Test:** Seed a DB with 3 assessments (single-framework, multi-framework, empty), run migration, assert:
  - `assessment.engagement.client.name == assessment.company_name` for all rows
  - Conclusion count == GapItem count for migrated assessments
  - No orphaned rows in any table
  - Round-trip: scores match pre-migration values

### P1-4. Portfolio dashboard
- **Files:** `app/templates/pages/dashboard.html` (rewrite), new `app/templates/pages/client_detail.html`, `engagement_detail.html`
- Dashboard shows Client → Engagement cards with derived status, progress, last activity
- Engagement detail shows its Assessments with framework badges
- "New Engagement" flow: select or create Client → name Engagement → select frameworks → creates Assessment + AssessmentPacks
- **Test:** Integration test: create client, create engagement, see it on dashboard. HTMX partial responses render correctly.

### P1-5. Deprecate blended scoring
- Remove `compute_unified_maturity()` from `app/services/scoring.py`
- Remove `GapReport.overall_score` usage from comparison page (`web.py:1449-1510`), report summary, and PDF export
- Replace with per-framework score display using existing `framework_scores` JSON column on GapReport (or new per-AssessmentPack score storage)
- Fix `score()` NotImplementedError for multi-framework — route through per-framework scoring
- **Test:** Multi-framework assessment shows separate scores per framework. No blended score in UI, PDF, or API responses.

### P1-6. Backup/restore script
- `scripts/backup.py` — copies SQLite DB + evidence blob directory to a timestamped backup folder
- `scripts/restore.py` — restores from a backup, verifying DB integrity and blob presence
- Documents the 24h RPO / 4h RTO target (D9) and cron setup instructions
- **Test:** Backup, mutate DB, restore, assert DB matches pre-mutation state.

**Phase 1 exit criteria:**
- `alembic upgrade head` creates full schema
- Migration script handles legacy data correctly
- Portfolio dashboard shows Client → Engagement → Assessment hierarchy
- All routes under `/assessments/{id}/...` still work (hierarchy resolved from assessment row)
- Per-framework scoring, no blended score
- Backup/restore tested
- All pre-work + new integration tests pass

---

## Phase 2: Evidence & Conclusions (Weeks 4-6)

**Goal:** Evidence model replaces AssessmentDocument. Analysis produces immutable conclusions. Consultant approval workflow enforces individual review (D3). Workpaper view.

### P2-1. Evidence service
- New `app/services/evidence.py`:
  - Upload: hash file (SHA-256), store blob, create Evidence + EvidenceVersion row, set status=Quarantined
  - Quarantine→Active transition (placeholder for malware scan integration; auto-approve in v1 with logged warning)
  - Version: upload new version of existing Evidence, create EvidenceVersion, set old to Superseded
  - Map: create EvidenceUse linking evidence to requirement+framework
  - Lifecycle state machine with transition validation (P1 fix)
- Migrate AssessmentDocument rows to Evidence + EvidenceVersion on upgrade
- **Files touched:** `app/routers/web.py` (upload route), `app/routers/documents.py`, `app/templates/` (evidence panel)
- **Test:** Upload a file, verify Evidence + EvidenceVersion created with correct hash. Upload new version, verify old version is Superseded. Attempt invalid transition, verify rejection.

### P2-2. Citation model
- When analysis or desk review produces findings, store Citations pointing to EvidenceVersion + location
- Citations stored as JSON array on `conclusion_revisions.citations_json` (D2 simplification) with structured objects: `{evidence_version_id, location_type, location_ref, excerpt}`
- **Test:** Analysis run produces conclusion revisions with citation JSON. Each citation resolves to a valid EvidenceVersion.

### P2-3. Immutable analysis pipeline
- Rewrite `app/routers/analysis.py:trigger_analysis` to:
  - Create a new AnalysisRun row (status=running)
  - Store per-requirement claims as JSON in `claims_json` (D2: no separate AnalysisClaim table)
  - Create/update Conclusion rows with `ai_proposed=True`
  - Create ConclusionRevision with action=proposed
  - Never delete previous AnalysisRun or Conclusion rows
- **Files:** `app/routers/analysis.py`, `app/services/claude_analyzer.py`
- **Test:** Run analysis twice. Both AnalysisRuns exist. Conclusion has revision history showing both proposals.

### P2-4. Consultant approval workflow
- Individual approval only (D3): consultant must view evidence + proposal before approving each Conclusion
- UI: Conclusion card shows AI proposal, evidence summary, citations. "Approve" / "Edit & Approve" / "Reject" buttons per requirement.
- Each action creates a ConclusionRevision row (action=approved/edited/rejected)
- Optimistic locking on Conclusion.version (D6): if version changed since page load, reject save, show conflict
- **Files:** New `app/templates/components/conclusion_card.html`, updates to review routes
- **Test:** Approve a conclusion, verify revision created. Attempt concurrent approval, verify conflict detected.

### P2-5. Magic links (client evidence upload)
- New `app/routers/magic.py`:
  - Consultant creates link: generates 128-bit token, stores SHA-256 digest in `magic_links` table, sets scope/expiry/limits
  - Client accesses `/magic/{token}`: validate digest, check expiry, show scoped upload form
  - Upload creates Evidence with `uploaded_by=client_link:{token_prefix}`
  - Rate limiting: max N uploads per token per hour, max total size per token (P8 security)
  - Referrer-Policy: no-referrer header on magic link pages
- **Test:** Create link, upload file via token, verify evidence created. Attempt upload with expired token, verify rejection. Attempt upload exceeding rate limit, verify rejection.

### P2-6. Workpaper view
- New route: `/assessments/{assessment_id}/workpaper`
- For each applicable requirement: shows client response, evidence, citations, AI proposal, consultant decision, revision history
- Read-only traceability view — reviewer can navigate from any finding to its evidence chain
- **Test:** Assessment with approved conclusions renders workpaper. "3 clicks from Finding to full history" acceptance criterion (P7 fix).

**Phase 2 exit criteria:**
- Evidence upload, versioning, and lifecycle working
- Analysis produces immutable AnalysisRuns and Conclusions (no destructive re-runs)
- Per-conclusion consultant approval with optimistic locking
- Magic links functional with security controls
- Workpaper view renders complete evidence → conclusion → revision chain
- All previous tests pass

---

## Phase 3: Reports & Remediation (Weeks 7-8)

**Goal:** Versioned report snapshots. Independent findings and actions. Closure verification. Updated PDF.

### P3-1. Findings and Actions
- Consultant creates Findings from approved Conclusions (one Finding may reference multiple Conclusions across frameworks)
- Each Finding gets one or more Actions with owner, target date, status
- Action history stored as JSON array in `actions.history_json` (D2: replaces ActionUpdate + ClosureVerification tables)
- Each status change appends `{actor, action, timestamp, notes}` to history
- **Test:** Create finding from conclusion, add action, update action status, verify history_json contains both entries.

### P3-2. Report snapshots
- Generate report → create ReportSnapshot row with `is_issued=false` (draft)
- Consultant reviews, issues → set `is_issued=true`, snapshot becomes immutable and client-visible
- Regenerating creates a new ReportSnapshot, not an overwrite (PR-054 fix)
- One `report_snapshots` table for workpapers, gap reports, and integrated reports (D2: `type` column discriminator)
- **Test:** Generate report, issue it, regenerate, verify two snapshots exist. Issued snapshot unchanged.

### P3-3. PDF updates
- Per-framework scores (no blended) in executive summary
- Citations in finding details
- Evidence chain rendering
- Engagement-level integrated report option (consolidates approved findings across assessments, preserves distinct scopes/dates per the product requirements)
- **Files:** `app/utils/pdf_export.py` (1094 lines — additive changes only, per CLAUDE.md: "PDF sections are additive-only")
- **Test:** Generate PDF for multi-framework assessment. Verify per-framework scores, citations present, no blended score.

### P3-4. Remediation tracking
- Migrate remediation fields from GapItem to standalone Actions
- Closure verification: consultant marks action as closed, attaches closure evidence, records in history_json
- Dashboard: engagement-level rollup of open/closed actions
- **Test:** Full lifecycle: finding → action → update → close → verify closure in history.

**Phase 3 exit criteria:**
- Reports generated as immutable snapshots
- PDF shows per-framework scores with citations
- Findings → Actions → Closure lifecycle working
- Engagement-level reporting consolidates without blending
- All previous tests pass

---

## Phase 4: AWS & Validation (Weeks 9-10)

**Goal:** AWS evidence adapter. Longitudinal demo. Performance validation.

### P4-1. AWS evidence adapter
- New `app/services/aws_evidence.py`:
  - Input: AWS account ID, role ARN, external ID, region(s)
  - AssumeRole with external ID (no long-lived credentials)
  - Pull Config rule evaluations: compliant/non-compliant per resource (D10)
  - Pull Security Hub findings with severity (D10)
  - Each result becomes an Evidence item with `uploaded_by=aws_config:{account_id}` or `aws_securityhub:{account_id}`
  - Manual trigger only. Read-only. No write access, no continuous monitoring.
- **Test:** Mock boto3 responses. Verify Evidence + EvidenceVersion created with correct provenance. Verify least-privilege policy documented.

### P4-2. Longitudinal synthetic demo
- Expand `scripts/seed_test_companies.py` with 2 synthetic clients (minimal per review recommendation):
  - **Client A (mature):** Baseline gap assessment (DPDPA + ISO 27001), 6 months later a remediation validation with evidence reuse
  - **Client B (startup):** NIST CSF gap assessment, evidence uploaded via magic link, partial remediation
- Demonstrates: multi-engagement, evidence reuse with age/scope warnings, reassessment, conclusion independence, action lifecycle, engagement-level reporting
- **Test:** Seed script runs without error. Dashboard shows both clients with correct engagement hierarchy. Evidence reuse prompts for re-confirmation.

### P4-3. Performance benchmarks
- Seed a database with: 5 clients, 10 engagements, 30 assessments, 500 evidence versions, 3000 conclusion revisions
- Measure (all must complete in < 2 seconds on SQLite):
  - Portfolio dashboard load
  - Workpaper render for a 3-framework assessment
  - Report generation
  - Evidence search across an engagement
- If any exceeds threshold: add indexes, denormalize hot paths, or document Postgres gate
- **Test:** Benchmark script runs, all queries under threshold, results logged.

### P4-4. Retention plumbing
- Implement configurable retention per client (D11: `clients.retention_years`, default 7)
- Archive = soft delete (status = "archived"). Engagement and all children become read-only.
- Permanent purge: only after `retention_years` from archive date. Checks for active dependencies. Deletes DB rows + evidence blobs together. Logs to audit_events.
- Never auto-purge as shipped default. Purge is a manual consultant action with explicit confirmation.
- **Test:** Archive engagement, verify read-only. Attempt purge before retention period, verify rejection. Purge after period, verify DB rows and blobs removed, audit event logged.

**Phase 4 exit criteria:**
- AWS evidence adapter working with mocked and (optionally) real AWS account
- Synthetic demo covers multi-engagement, reuse, reassessment, remediation lifecycle
- Performance within thresholds on SQLite
- Retention/archive/purge lifecycle complete
- Full test suite green

---

## Architecture Boundaries

### UCC scope (D8)
UCCs deduplicate questions only. Evidence-to-requirement mapping is consultant-driven with system suggestions based on keyword/requirement matching. UCC-mediated evidence routing is deferred until frameworks 4-6 go live.

### Scoring boundary
Deterministic scoring (`app/services/scoring.py`) computes quantitative scores from approved Conclusion outcomes. LLM produces qualitative analysis only. Scores are per-framework per-assessment — never blended across frameworks.

### LLM boundary
`app/services/llm_client.py` is the sole LLM interface. OpenRouter-tiered. All LLM calls produce `AnalysisRun` records. Failed/incomplete runs produce no draft Conclusions (P3: error recovery). Vision tier for document OCR is separate.

### ISO pack (D4)
Reference-only. Clause numbers, control objective descriptions, and assessment guidance. No reproduced ISO standard text. Pack metadata includes a content-source disclaimer. Consultants who own the standard can map references to their copy.

---

## Migration Safety

### Backfill script design (`scripts/migrate_legacy.py`)
1. **Idempotent** — safe to run multiple times. Checks for existing Client/Engagement before creating.
2. **Conservative Client creation** — each distinct `company_name` creates one Client. Same-name assessments are NOT assumed to share one Engagement (one Engagement per Assessment for safety).
3. **Assessment.company_name frozen** — column preserved but never updated. Display reads from `engagement.client.name`. Migration test asserts equality.
4. **GapItem → Conclusion mapping:**
   - `compliance_status` → `outcome` (map `not_assessed` → `insufficient_evidence` with logged warning for review)
   - AI fields → ConclusionRevision with action=proposed
   - Consultant review fields → ConclusionRevision with action=approved (if reviewed_at is set)
   - Remediation fields → Finding + Action
5. **`_legacy_history` JSON** (from PW-2) preserved as-is for audit reference
6. **Rollback** — `scripts/rollback_legacy.py` restores from backup (backup is mandatory before migration)

### What breaks and how we handle it

| Breakage | When | Fix |
|----------|------|-----|
| `db.delete(assessment)` raises IntegrityError | PW-5 (FK addition) | Replace with soft-delete (status=archived) |
| `compute_unified_maturity()` removed | P1-5 | Replace all callers with per-framework display |
| `GapReport.overall_score` removed from templates | P1-5 | Templates show per-framework scores |
| AssessmentDocument upload routes change | P2-1 | Evidence service replaces; old routes redirect |
| Analysis re-run creates new rows instead of replacing | P2-3 | UI shows latest run, history accessible |

---

## Test Strategy

### Test infrastructure (built in PW-4)
- `TestClient` fixture with seeded DB and mocked LLM
- One integration test per major route group
- Separate `tests/integration/` directory

### Per-phase testing

| Phase | Unit tests | Integration tests | Smoke tests |
|-------|-----------|-------------------|-------------|
| Pre-work | Column survival, history preservation, branding, FK constraints | 6 route-level tests | `pytest -q` full suite |
| Phase 1 | Alembic up/down, migration script, per-framework scoring | Dashboard, create engagement, assessment CRUD | Server starts, dashboard loads, create→view→archive cycle |
| Phase 2 | Evidence lifecycle transitions, citation validation, token security | Upload, magic link, analysis, approval, workpaper | Upload→analyze→approve→workpaper end-to-end |
| Phase 3 | Snapshot immutability, action history, PDF content | Report generation, finding lifecycle | Generate→issue→regenerate, PDF download |
| Phase 4 | AWS mock responses, retention rules, benchmark thresholds | AWS ingest, seed script, purge lifecycle | Full synthetic demo run, performance benchmarks |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| ISO licensing blocks clause content | High | Medium | D4: reference-only pack, no text reproduction |
| SQLite performance degrades with normalized schema | Low | High | P4-3: benchmark with realistic data, Postgres gate documented |
| Evidence lifecycle complexity exceeds estimate | Medium | Medium | P1 fix: state machine defined upfront, transitions validated |
| `not_assessed` → `insufficient_evidence` mapping loses intent | Medium | Low | Log warnings during migration, flag for manual review |
| Magic link token leakage | Low | High | P8: 128-bit entropy, digest-only storage, referrer-policy, expiry |
| Single-developer velocity risk across 10 weeks | Medium | High | 4 phases each produce shippable state; can pause between phases |

---

## Explicitly Not In This Plan

- Client user accounts or self-service portal
- Continuous cloud monitoring
- Broad cloud/identity/SaaS integrations beyond AWS Config + Security Hub
- Client-authored framework packs or CSV imports
- Mandatory maker-checker approval (deferred; individual approval in v1)
- Client-managed remediation
- Autonomous compliance declarations, certification, or attestation
- Blended cross-framework score
- PostgreSQL migration (gate documented, not planned)
- WCAG 2.1 AA compliance (D7: not prioritized for v1)
- UCC-mediated evidence routing (D8: questions only)
- Bulk conclusion approval (D3: individual only)
