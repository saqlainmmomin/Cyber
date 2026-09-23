# CyberAssess implementation tracker

**Updated:** 2026-09-22 · **Source:** `2026-09-21-002-revised-implementation-plan.md` · **Current focus:** Phase 1

Mark a task complete only with its plan test/smoke evidence. `[AR]` is an adversarial-review merge gate.

## Done

- [x] **Pre-work (PW-1–PW-5)** — migration safety, preserved rerun history, template setup, HTTP test harness, and SQLite foreign keys. **Verified:** PR #14, 163 tests.
- [x] **P1-1: Alembic foundation** `[AR: migration cutover]` — **Merged:** PR #16.
- [x] **P1-2: Target schema (15 new tables + FKs)** `[AR: data integrity]` — adversarial review found a missing downgrade data-loss guard, remediated. **Merged:** PR #17.
- [x] **P1-6: Backup/restore and recovery rehearsal** `[AR: recoverability]` — adversarial review found a real rollback data-loss bug (partial safety copy could overwrite a good original) plus 3 smaller issues, all remediated. **Merged:** PR #18.
- [x] **P1-3: One-shot legacy migration** `[AR: data integrity/backfill]` — implemented against a 26-test failing suite written first; adversarial review (manual + automated) found an undocumented heuristic silently dropping genuinely-open remediation items, remediated; independent final verification pass confirmed safe. 27/27 targeted + 240/240 full suite passing. **Merged:** PR #19.

## Phase 1 — Schema & Hierarchy

- [ ] **P1-4: Portfolio, hierarchy navigation, and new-engagement flow** — unblocked (P1-3 merged). Handoff written: `tasks/handoffs/2026-09-23-p1-4-portfolio-dashboard.md`.
- [x] **P1-5: Per-framework scoring; remove blended scores** `[AR: scoring semantics]` — implemented and verified: 249 tests passed; per-framework persistence/API/UI/PDF surfaces smoke-tested with no combined percentage. Handoff Results appended in `tasks/handoffs/2026-09-23-p1-5-deprecate-blended-scoring.md`.

**Phase 1 exit:** full target schema, safe legacy migration, working portfolio and legacy assessment routes, separate framework scores, tested backup/restore.

## Later phases

- [ ] **Phase 2 — Evidence & conclusions** `[AR: evidence lifecycle, citations, immutable analysis, approvals, magic links]`
- [ ] **Phase 3 — Reports & remediation** `[AR: report immutability, provenance, closure verification]`
- [ ] **Phase 4 — AWS & validation** `[AR: IAM/external ID, retention/purge, performance]`

## Source of truth

- Implementation: `docs/plans/2026-09-21-002-revised-implementation-plan.md`.
- Product requirements: `docs/product/2026-09-21-cyberassess-product-requirements.md`.
- Decisions: `tasks/2026-09-21-adversarial-review.md` (D1–D11).
