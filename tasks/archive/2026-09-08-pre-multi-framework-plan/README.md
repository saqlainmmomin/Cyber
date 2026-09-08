# Archive — pre multi-framework demo plan (2026-09-08)

These planning artefacts were superseded on 2026-09-08 by
`tasks/multi-framework-demo-plan.md`, which is now the single source of truth
for direction on this repo.

Provenance is kept — nothing here is dead, just historical.

## Contents

- `cleanup-prompt.md` — original multi-framework UI/text cleanup prompt.
  Every item was shipped (see `todo.md` checkboxes and commit `fc7cacf`,
  `bbf5a2b`).
- `todo.md` — running punch list for the cleanup-prompt work plus the
  UCC content-completion follow-ups. All primary checkboxes shipped.
  A handful of small "discovered during cleanup" items were rolled into
  the new plan (WS #2/#4/#6) or handled directly (root-level
  `cyberassess.db` / `dashboard.png` are already gitignored).
- `2026-07-11-ucc-content-completion.md` — Hermes handoff that resolved
  40 duplicate cluster memberships + 69 orphan controls + 32 DPDPA
  guidance entries. Shipped in commit `bbf5a2b`.
- `phase3_claude_prompt.md` — prompt for the Phase 3 domain-screening
  build. That work shipped inside the Adaptive Assessment Engine
  (see project_status.md; Phase 3 marked done 2026-05-07).

## Not archived (still live)

- `tasks/handoffs/2026-07-10-v3-adversarial-seed-company.md` — v3 seed
  company work is NOT yet shipped (git log only shows v2 seed in
  commit `990b945`). Kept as live work; may inform WS #7 verification.
