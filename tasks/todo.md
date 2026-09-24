# CyberAssess implementation tracker

**Updated:** 2026-09-24 · **Source:** `2026-09-21-002-revised-implementation-plan.md` · **Current focus:** Phase 3

Mark a task complete only with its plan test/smoke evidence. `[AR]` is an adversarial-review merge gate.

## Done

- [x] **Pre-work (PW-1–PW-5)** — migration safety, preserved rerun history, template setup, HTTP test harness, and SQLite foreign keys. **Verified:** PR #14, 163 tests.
- [x] **P1-1: Alembic foundation** `[AR: migration cutover]` — **Merged:** PR #16.
- [x] **P1-2: Target schema (15 new tables + FKs)** `[AR: data integrity]` — adversarial review found a missing downgrade data-loss guard, remediated. **Merged:** PR #17.
- [x] **P1-6: Backup/restore and recovery rehearsal** `[AR: recoverability]` — adversarial review found a real rollback data-loss bug (partial safety copy could overwrite a good original) plus 3 smaller issues, all remediated. **Merged:** PR #18.
- [x] **P1-3: One-shot legacy migration** `[AR: data integrity/backfill]` — implemented against a 26-test failing suite written first; adversarial review (manual + automated) found an undocumented heuristic silently dropping genuinely-open remediation items, remediated; independent final verification pass confirmed safe. 27/27 targeted + 240/240 full suite passing. **Merged:** PR #19.

## Phase 1 — Schema & Hierarchy

- [x] **P1-4: Portfolio, hierarchy navigation, and new-engagement flow** — implemented and adversarial-review fixes applied. Verified: 17 portfolio integration cases and 257 full-suite tests pass; live ASGI smoke exercised the new page, POST, detail, and both HTMX fragments (TCP/Unix socket binds unavailable in the managed sandbox). Handoff results: `tasks/handoffs/2026-09-23-p1-4-portfolio-dashboard.md`. **Merged:** PR #21.
- [x] **P1-5: Per-framework scoring; remove blended scores** `[AR: scoring semantics]` — implemented and verified: 249 tests passed; per-framework persistence/API/UI/PDF surfaces smoke-tested with no combined percentage; adversarial review added a standing `.py`-side regression guard against the blend reappearing. Handoff Results appended in `tasks/handoffs/2026-09-23-p1-5-deprecate-blended-scoring.md`. **Merged:** PR #22.

**Phase 1 exit:** ✅ full target schema, safe legacy migration, working portfolio and legacy assessment routes, separate framework scores, tested backup/restore. Full suite: 266 passed. `docs/p1-progress-2026-09-22` → `main` integration: PR #23.

## Later phases

- [x] **Phase 2 — Evidence & conclusions** `[AR: evidence lifecycle, citations, immutable analysis, approvals, magic links]` — fully implemented and merged: P2-1 through P2-6. Full suite: 443 passed. Ownership per task: `tasks/agent-ownership.md`.
- [x] **P2-1: Evidence service** — implemented and verified: 43 contract tests and 309 full-suite tests pass; live ASGI smoke, hash verification, archive/restore, mocked desk review, and two-pass copy migration completed. Handoff Results: `tasks/handoffs/2026-09-23-p2-1-evidence-service.md`. **Merged:** PR #24.
- [x] **P2-2: Citation model** — implemented and verified: 26 citation contract tests pass; drops the dead P1-2 `citations` table in favor of `citations_json`, per D-P2-2-A. Live ASGI smoke stored a verified raw-text span citation. Handoff Results: `tasks/handoffs/2026-09-23-p2-2-citation-model.md`. **Merged:** PR #25.
- [x] **P2-5: Client evidence magic links** — implemented and verified: 29 contract tests pass; adversarial review found and this branch fixed a query-count timing oracle in `resolve_token` before merge. Handoff Results appended to `tasks/handoffs/2026-09-23-p2-5-magic-links.md`. **Merged:** PR #26.
- [x] **P2-3: Immutable analysis pipeline** `[AR: dual-write invariant, never overwrite a human decision]` — implemented and verified: 29 contract tests and 392 full-suite tests pass; dual-writes `AnalysisRun`/`Conclusion`/`ConclusionRevision` alongside the unchanged `GapReport`/`GapItem` path (zero diff on scoring/PDF/reports/remediation/review, confirmed twice independently). Also fixes a real, independently-reproduced production bug: re-running analysis crashed with a `UNIQUE constraint` error before this. Two independent reviews (personal + Sonnet adversarial) both returned MERGE AS-IS. Handoff Results: `tasks/handoffs/2026-09-23-p2-3-immutable-analysis-pipeline.md`. **Merged: PR #27.**
- [x] **P2-4: Consultant conclusion approval workflow** `[AR: individual-only approvals, optimistic locking]` — implementation and local verification complete: all 15 contract scenarios are covered by 38 new tests, and the 430-test full suite passes. Results: `tasks/handoffs/2026-09-23-p2-4-consultant-approval.md#continued-implementation-results-codex`. **Merged: PR #28.**
- [x] **P2-6: Read-only workpaper view** — implemented and verified: 13 contract/smoke tests cover the complete response → evidence → proposal → decision → revision chain, direct report/conclusion navigation, read-only guards, multi-framework scope, stale runs and edge states; 443 full-suite tests pass. Sonnet adversarial review found no blocking issues (read-only guarantee, "3 clicks" claim, and zero-diff invariant all independently re-verified). Handoff Results: `tasks/handoffs/2026-09-23-p2-6-workpaper-view.md#results`. **Merged: PR #29.**

**Phase 2 exit:** ✅ evidence lifecycle, citations, immutable analysis runs, individual consultant approval with optimistic locking, magic links, and a read-only workpaper trace all working. Full suite: 443 passed.

## Phase 3 — Reports & remediation `[AR: report immutability, provenance, closure verification]`

- [x] **P3-1: Findings and Actions** — implemented and verified: 12 contract scenarios covered by 20 new tests (append-only history via compare-and-swap, `ACTION_TRANSITIONS` state machine, one-Finding-per-Conclusion cardinality, legacy-migration coexistence, workpaper linkage); 463 full-suite tests pass. Sonnet adversarial review found no blocking issues (append-only CAS race, eligibility rule, and migration idempotency all independently re-verified). Handoff Results: `tasks/handoffs/2026-09-23-p3-1-findings-and-actions.md#results`. **Merged: PR #30.**
- [x] **P3-2: Write-once report snapshots** — implemented and verified: 14 contract tests cover immutable PDF/HTML artifacts, draft → issued lifecycle, newest-only atomic issue, provenance, integrity failures, cleanup, integrated-report scope and UI guards; 457 full-suite tests pass. Sonnet adversarial review found no blocking issues (true immutability, atomic issue SQL, and hash verification all independently re-verified). Handoff Results: `tasks/handoffs/2026-09-23-p3-2-report-snapshots.md#results`. **Merged: PR #31.**
- [x] **P3-3: PDF updates** — implemented and verified: 13 new contract tests cover approved Findings with citations/evidence chains, additive gap PDFs, integrated report sections, write-once lifecycle/release gates, validation, cleanup, structural guards, and sanitization. Full suite: 490 passed. Sonnet adversarial review found no blocking issues (additive-only pdf_export.py diff and no-blended-score invariant both independently re-verified). Handoff Results: `tasks/handoffs/2026-09-23-p3-3-pdf-updates.md#results`. **Merged: PR #32.**
- [x] **P3-4: Remediation tracking** — implemented and verified: 12 contract scenarios cover evidence-backed close, separate verification, re-open, derived Finding status, legacy retirement, report Action counts, engagement rollup and structural guards; 489 full-suite tests pass (477 baseline + 12 new). ASGI smoke covered the full Action lifecycle, SQL history/status output, tracker/report routes and removal of the legacy PATCH. Sonnet adversarial review found no blocking issues (closure/verification separation and legacy non-grandfathering both independently re-verified). Handoff Results: `tasks/handoffs/2026-09-23-p3-4-remediation-tracking.md#results`. **Merged: PR #33.**

**Phase 3 exit:** ✅ append-only Findings/Actions with evidence-backed closure and verification, write-once immutable report snapshots, per-framework PDF scores with citations and no blend, an engagement-level integrated report, and a fully retired legacy remediation path. Full suite: 502 passed.

- [ ] **Phase 4 — AWS & validation** `[AR: IAM/external ID, retention/purge, performance]` — not started. P4-1/P4-2/P4-4 need a Claude-written handoff each (P4-1 is a security-boundary task, P4-4 is the most destructive code path in the plan); P4-3 is standalone Codex. All four are independent and can run concurrently. Kickoff process doc: `tasks/handoffs/2026-09-24-phase-4-kickoff.md`.

## Source of truth

- Implementation: `docs/plans/2026-09-21-002-revised-implementation-plan.md`.
- Product requirements: `docs/product/2026-09-21-cyberassess-product-requirements.md`.
- Decisions: `tasks/2026-09-21-adversarial-review.md` (D1–D11).
