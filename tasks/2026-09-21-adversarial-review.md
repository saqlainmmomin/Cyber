# Adversarial Review: CyberAssess Build Plan

**Date:** 2026-09-21
**Reviewed:** PR #13 (`codex/formal-product-plan`)
**Scope:** Product requirements, implementation plan, and architecture strategy
**Verdict:** Product requirements are strong. Implementation plan is over-architected for current reality. Significant rework recommended before building.

---

## Executive Summary

The product requirements document is clear, well-bounded, and proportionate to a boutique GRC firm launch. The implementation plan is thorough but treats a pre-revenue MVP with an empty SQLite database like a production system with paying customers. The 7-unit additive migration with shadow tables, dual reads, and staged cutover gates will consume roughly double the engineering time of a clean-break approach for negligible safety benefit.

**Recommendation:** Accept the product requirements with targeted fixes (below). Rewrite the implementation plan around a clean-break migration in 4 phases instead of 7 additive units.

---

## Part 1: Critical Findings (Fix Before Building)

### C1. Questionnaire rebuild destroys columns today

**Where:** `app/main.py:82-117`
**What:** `_ensure_questionnaire_answer_constraint` drops and recreates `questionnaire_responses` with a hardcoded 8-column CREATE TABLE. The model defines additional columns (`cluster_id`, `answer_source`) added by `_run_migrations()`. On an incrementally-upgraded database, the rebuild silently drops those columns.
**Impact:** Data loss in production today — not a migration risk, a live bug.
**Action:** Hotfix as a standalone PR before any plan work begins. Add the missing columns to the CREATE TABLE statement. Test with populated rows.

### C2. Analysis and desk review hard-delete history on re-run

**Where:** `app/routers/analysis.py:257-259`, `app/routers/web.py:1754-1756`
**What:** `trigger_analysis` deletes all GapItems and the GapReport before re-running. `run_desk_review_web` deletes all DeskReviewFindings before re-running. QuestionnaireResponse rows are mutated in-place.
**Impact:** The plan's U4 backfill ("backfill legacy GapItems into immutable AnalysisRun") will find only the most recent run. All prior analysis history is already gone. Every re-run between now and U4 destroys more.
**Action:** Before starting the plan, either (a) make re-runs append-only (new rows, mark old as superseded), or (b) serialize pre-deletion state to a JSON audit column as a stopgap.

### C3. Zero foreign keys means "additive migration" is actually a full integrity retrofit

**Where:** All models in `app/models/`
**What:** Not a single `ForeignKey` or `relationship()` exists. All cross-table references are bare string columns. Every `db.delete(assessment)` leaves orphaned GapReports, DeskReviewFindings, AssessmentDocuments, and QuestionnaireResponses without error.
**Impact:** When the plan adds FKs, every delete breaks with IntegrityError. The migration from manual-join-everywhere to relationship-aware models is not "additive" — it's a query pattern rewrite across every router.
**Action:** Add FKs and ON DELETE RESTRICT in a dedicated early step. Run orphan detection first, quarantine orphans, then add constraints. This forces delete-to-archive before hierarchy work.

---

## Part 2: Strategic Findings (Rethink the Approach)

### S1. The additive migration is over-cautious — do a clean break

The plan proposes shadow tables, dual reads, backfill reconciliation, and staged cutover for a system with:
- An empty production database
- 289 lines of model code across 7 files
- 128 tests on in-memory databases
- A single developer and zero paying users

**The honest tradeoff:** Additive migration preserves backward compatibility with data that barely exists, at the cost of weeks of dual-read/write plumbing and "half-migrated" code paths that must themselves be tested and then removed. A clean-break migration — write the target schema, write a one-shot Python migration script, feature-flag the new routes, delete old ones when ready — is faster, produces cleaner code, and carries less risk because there is less code to get wrong.

If real user data appears before migration, the one-shot script handles it. The reconciliation is a 200-line Python function, not 7 units of infrastructure.

### S2. Seven implementation units should be four

The minimum viable decomposition:

| Phase | Scope | Duration |
|-------|-------|----------|
| **1. Schema & Hierarchy** | Alembic, full target schema, Client→Engagement→Assessment, backfill script, portfolio dashboard, FK retrofit, branding fix, test harness | 2-3 weeks |
| **2. Evidence & Conclusions** | Evidence/EvidenceVersion/Citation (replaces AssessmentDocument), magic links, analysis pipeline → immutable conclusion revisions, workpaper | 2-3 weeks |
| **3. Reports & Remediation** | Versioned report snapshots, independent findings/actions, closure verification, PDF updates | 1-2 weeks |
| **4. AWS & Demo** | boto3 AssumeRole Config+SecurityHub reads, longitudinal synthetic demo | 1 week |

This cuts the "half-migrated" period from months to weeks and eliminates the compatibility-shim maintenance burden.

### S3. The audit trail is over-engineered for v1

The plan describes 11 append-only record types: EvidenceVersion, ConclusionRevision, ApprovalEvent, AnalysisRun, AnalysisClaim, CitationClaim, ActionUpdate, ClosureVerification, ReportSnapshot, WorkpaperSnapshot, AuditEvent.

**What's professionally credible for a boutique firm's first release:**

| Keep (load-bearing) | Simplify | Defer |
|---------------------|----------|-------|
| Evidence versioning with hashes | ConclusionRevision + ApprovalEvent → single `conclusion_revisions` table | CitationClaim as relational table (use JSON array on conclusion revision) |
| Report snapshots (immutable) | ActionUpdate + ClosureVerification → single `action_events` table | WorkpaperSnapshot as separate type (same table as report snapshots with a `type` column) |
| One `audit_events` table (who/what/when/entity/action/metadata) | AnalysisRun → keep table, but store claims as JSON blob not separate rows | |

This reduces new tables from ~15 to ~8 and cuts surface area roughly in half.

### S4. SQLite is fine; Alembic is warranted

SQLite handles this workload. No concurrent writes in single-user mode. The plan correctly defers Postgres. Alembic is the right migration tool — its autogenerate catches model-schema drift, which matters during a major schema change. The current DIY migrations in `main.py` are actively dangerous (see C1).

---

## Part 3: Product Requirements Fixes

### P1. Evidence lifecycle has no transition rules

Ten states (Requested → ... → Purged) with zero defined transitions. Can Evidence go from Active to Purged? From Invalidated back to Active?
**Action:** Add a state-transition table. Define which transitions require consultant confirmation vs. system-driven.

### P2. Assessment-to-pack relationship is ambiguous (PR-013)

"An Assessment may use any subset of published launch packs." But the hierarchy shows Assessment with one framework questionnaire, and Conclusions "remain bound to Assessment." If one Assessment spans DPDPA + ISO, "bound to Assessment" is less precise than "bound to Assessment + Framework + Requirement."
**Action:** Add an explicit `AssessmentPack` join entity. Clarify whether Assessment = multi-framework examination or single-framework.

### P3. AI rubber-stamping has no friction

The system produces AI-proposed conclusions that consultants can accept with one click. No mechanism prevents bulk-accept without genuine review. This undermines the entire "human judgment" thesis and creates professional liability exposure.
**Action:** Require per-requirement approval (no bulk-accept). Each approval requires the consultant to have viewed the evidence and proposal for that specific requirement.

### P4. PR-022 evidence quality analysis is unbounded

Assessing "relevance, sufficiency, currency, period, scope, contradictions, unsupported assertions, and design vs. operating effectiveness" is essentially a full evidence-analysis engine. Each dimension is a separate analytical capability.
**Action:** Tier the dimensions. V1: relevance, currency/period, gap identification. Progressive: sufficiency scoring, contradiction detection, design-vs-effectiveness.

### P5. No concurrent-editing protection

Two consultants on the same engagement will silently overwrite each other's work.
**Action:** Add optimistic concurrency control on Conclusions, or explicitly state v1 doesn't support concurrent editing and add a UI warning.

### P6. ISO 27001 licensing blocks stated launch scope

PR-010 promises clauses 4-10, risk treatment, SoA, and Annex A coverage. This is gated on a legal decision not yet made.
**Action:** Make PR-010 conditional. If licensing restricts text, the pack references clause numbers and assessment guidance without reproducing protected content.

### P7. Vague acceptance criteria

"Defensible" (thesis), "credible" (reviewer controls), and "quickly" (success measures) are not testable.
**Action:** Replace with specific criteria. E.g., "A reviewer can navigate from a Finding to its Conclusion's full proposal/edit/approval history in three or fewer clicks."

### P8. Magic-link security under-specified

Non-enumerable tokens without specified entropy, signing mechanism, or referrer-header protection. A leaked link gives upload access to a client's evidence request.
**Action:** Specify 128-bit token entropy, short-lived JWTs, referrer-policy headers, and configurable IP-binding.

---

## Part 4: Implementation Plan Fixes

### I1. Build HTTP integration test harness first

128 tests pass, but only 2 use TestClient for HTTP-level testing. Zero route-level integration tests for assessment CRUD, upload, desk review, analysis, or report rendering. The plan assumes test infrastructure that doesn't exist.
**Action:** Add "Build HTTP integration test harness" as a prerequisite. Create TestClient fixtures with seeded database and mocked LLM. Write one integration test per major route group before starting schema work.

### I2. URL strategy for hierarchy transition

30+ routes start with `/assessments/{assessment_id}`. The plan doesn't specify whether new URLs coexist (redirects), old URLs gain context from the database, or old URLs become redirects to `/clients/{cid}/engagements/{eid}/assessments/{id}`.
**Action:** Define the URL strategy explicitly. Recommendation: keep `/assessments/{id}` working by looking up the hierarchy from the assessment ID. Add new hierarchical URLs as the canonical paths.

### I3. Scoring cannot handle multi-framework transition

`scoring.py:209` raises `NotImplementedError("Cluster-backed scoring supports exactly one framework at a time")`. The legacy `compute_unified_maturity()` averages framework scores — the exact blended rollup the product prohibits. `GapReport.overall_score` is used in comparison page, report summary, and PDF.
**Action:** Plan explicitly: deprecate `overall_score`, add per-framework score columns, update comparison page and PDF to show per-framework scores. This is a data model + template + PDF change, not a "read boundary" toggle.

### I4. Split U3 (Evidence) — it's the critical-path bottleneck

U3 proposes ~26 new files. It builds evidence storage, citation model, magic-link upload system, and impact analysis simultaneously. U3 blocks U4 (analysis/conclusions) and U6 (AWS).
**Action:** Split into Evidence-core (Evidence/EvidenceVersion/Citation, storage) which unblocks U4, and Evidence-collection (magic links, impact analysis) which can proceed in parallel.

### I5. Fix branding import-order bug properly

`main.py:21` sets template globals as a side effect. Tests that import templates without importing `main.py` get undefined `branding`. Every new template in every phase will hit this.
**Action:** Move template environment setup into a `configure_templates()` function called by both `main.py` and test fixtures. 30-minute fix that prevents recurring failures.

### I6. Add performance benchmarks to final verification

SQLite with 36-byte string UUIDs, 6+ table joins for a workpaper view, and no query optimization. The plan defers Postgres but doesn't validate SQLite can handle realistic data.
**Action:** In the final phase, seed a database with 5 clients, 10 engagements, 30 assessments, 500 evidence versions, 3000 claims. Measure dashboard load, workpaper render, and report generation. Define a 2-second threshold.

---

## Part 5: UCC Layer Assessment

The 52-cluster UCC mapping (1041 lines in `clusters.py`) is load-bearing for question deduplication across frameworks. Keep it for that purpose.

**Do not expand its role in v1.** The plan treats UCCs as a foundation for shared evidence requests, shared analysis, and cross-framework citation mapping. For 3 active frameworks, this is premature. Let evidence be tagged to requirements through simple mapping. Let the consultant decide which evidence supports which framework requirement. The system suggests; the consultant confirms.

When frameworks 4-6 go live, revisit whether UCC-mediated evidence routing adds enough value to justify the complexity.

---

## Recommended Plan of Attack

```
Pre-work (1 week)
├── Hotfix: questionnaire column rebuild (C1)
├── Hotfix: stop destructive re-runs (C2)
├── Build HTTP test harness (I1)
└── Fix branding import-order (I5)

Phase 1: Schema & Hierarchy (2-3 weeks)
├── Adopt Alembic, delete DIY migrations
├── Full target schema (clean break, not shadow tables)
├── One-shot backfill script + backup test
├── FK retrofit with orphan quarantine
├── Portfolio dashboard (Client → Engagement → Assessment)
├── URL strategy (keep /assessments/{id}, add hierarchical)
└── Per-framework scoring (replace blended)

Phase 2: Evidence & Conclusions (2-3 weeks)
├── Evidence/EvidenceVersion/Citation (replace AssessmentDocument)
├── Magic links (JWT, scoped, rate-limited)
├── Analysis → immutable conclusion revisions
├── Consultant approval workflow (no bulk-accept)
├── Workpaper view
└── Evidence state machine with defined transitions

Phase 3: Reports & Remediation (1-2 weeks)
├── Versioned report snapshots
├── Independent findings and actions
├── Closure verification
└── PDF updates (per-framework scores)

Phase 4: AWS & Validation (1 week)
├── boto3 AssumeRole, Config + Security Hub reads
├── Longitudinal synthetic demo (2 clients minimum)
└── Performance benchmarks on SQLite
```

**Estimated total: 7-10 weeks** (vs. 12-16+ implied by 7-unit plan)

---

## Decisions Log

All decisions made during adversarial review on 2026-09-21:

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| D1 | Migration strategy | **Clean break** | No real user data at risk. One-shot backfill script, new schema, feature-flag new routes. ~8 weeks vs ~16. |
| D2 | Audit trail granularity | **Simplified (~8 tables)** | JSON for claims/citations/action-history. One generic `audit_events` table. Normalize later if query needs emerge. |
| D3 | AI conclusion approval | **Individual only** | Each conclusion requires consultant to view evidence + proposal before approving. No bulk-accept. Professional liability protection. |
| D4 | ISO 27001 pack licensing | **Reference-only** | Ship with clause numbers and assessment guidance, no reproduced ISO text. Consultants who own the standard can work with references. |
| D5 | Implementation phasing | **4 phases** | Pre-work + 4 phases (Schema→Evidence→Reports→AWS). Less time half-migrated than 7 units. |
| D6 | Concurrent editing | **Optimistic locking** | Version columns on Conclusions. Reject save on conflict, show diff. Prevents silent data loss between consultants. |
| D7 | Accessibility (WCAG) | **Not prioritized** | Boutique firm buyer won't gate on this. Semantic HTML as baseline. Revisit if targeting enterprise. |
| D8 | UCC scope | **Questions only** | UCC deduplicates questions. Evidence-to-requirement mapping is consultant-driven with system suggestions. Keep narrow for 3 frameworks. |

| D9 | Backup RPO/RTO | **24h RPO, 4h RTO** | Daily backups, recover within half a business day. Ship a backup/restore script (DB + blobs together). Simple cron + rsync. |
| D10 | AWS collection scope | **Config rules + Security Hub findings** | Pull active Config rule evaluations (compliant/non-compliant per resource) and Security Hub findings with severity. No resource inventory in v1. |
| D11 | Evidence retention | **Configurable per-client** | Consultant sets retention period per client or engagement. Default 7 years. Retention-aware soft delete; purge only after expiry. Never auto-purge as shipped default. |

All decisions closed. No remaining open questions block implementation.
