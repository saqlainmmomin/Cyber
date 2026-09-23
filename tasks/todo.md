# CyberAssess implementation tracker

**Updated:** 2026-09-23 · **Source:** `2026-09-21-002-revised-implementation-plan.md` · **Current focus:** Phase 2

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

- [ ] **Phase 2 — Evidence & conclusions** `[AR: evidence lifecycle, citations, immutable analysis, approvals, magic links]` — P2-1, P2-2 and P2-5 complete; P2-3/P2-4/P2-6 remain. Ownership per task: `tasks/agent-ownership.md`. Gating task is P2-1 (evidence service); {P2-2→P2-3→P2-4} and {P2-5} are independent lanes after that; P2-6 depends on all of them.
- [x] **P2-1: Evidence service** — implemented and verified: 43 contract tests and 309 full-suite tests pass; live ASGI smoke, hash verification, archive/restore, mocked desk review, and two-pass copy migration completed. Handoff Results: `tasks/handoffs/2026-09-23-p2-1-evidence-service.md`. **Merged:** PR #24.
- [x] **P2-2: Citation model** — implemented and verified: 26 citation contract tests pass; drops the dead P1-2 `citations` table in favor of `citations_json`, per D-P2-2-A. Live ASGI smoke stored a verified raw-text span citation. Handoff Results: `tasks/handoffs/2026-09-23-p2-2-citation-model.md`. **Merged:** PR #25.
- [x] **P2-5: Client evidence magic links** — implemented and verified: 29 contract tests pass; adversarial review found and this branch fixed a query-count timing oracle in `resolve_token` before merge. Handoff Results appended to `tasks/handoffs/2026-09-23-p2-5-magic-links.md`. **Merged:** PR #26.
- [ ] **Phase 3 — Reports & remediation** `[AR: report immutability, provenance, closure verification]`
- [ ] **Phase 4 — AWS & validation** `[AR: IAM/external ID, retention/purge, performance]`

## Source of truth

- Implementation: `docs/plans/2026-09-21-002-revised-implementation-plan.md`.
- Product requirements: `docs/product/2026-09-21-cyberassess-product-requirements.md`.
- Decisions: `tasks/2026-09-21-adversarial-review.md` (D1–D11).
