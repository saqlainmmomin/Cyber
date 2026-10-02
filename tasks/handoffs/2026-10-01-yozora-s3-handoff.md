# Yozora S3: Home, clients, firm settings

**Written:** 2026-10-01. **Owner:** Codex builds, Claude reviews every diff and screenshot before merge, Saqlain merges. **Depends on:** V3-A merged (done, PR #94); slice S2 merged.
**Specs (read first):** `docs/product/yozora-design-system.md`, `docs/product/yozora-fidelity-gate.md`, `docs/product/yozora-migration-map.md` (rows for this slice), the approved mockups in `docs/product/2026-10-01-app-design-mockups/screens/`.

## Scope
Templates: dashboard, client_detail, client_picker, login.

Needs mockup batch 1 approved. Home shows attention rows plus the engagement table; legacy unmigrated assessments move to firm settings, data housekeeping. Login is a placeholder card wired in Track 4.

## Tests
existing dashboard/client tests plus a new test that the legacy list is absent from Home. Must-keep ids, `hx-*` and `data-*` come from the migration map; any intended string change is listed in the PR description so tests are updated deliberately.

## File-set guard
Add a per-PR `:(exclude)` allowance for this slice's template and test files in the P6-2b file-set guard. Never delete guards.

## Screenshot gate
Baselines for this slice's screens, light and dark, at 1440 and 1024 (390 for client-facing). Thresholds from the fidelity gate: 0.4% differing pixels, no changed region over 40x40. Post candidate, baseline and diff images in the PR for Saqlain.

## Stop and ask
If a visual detail is not in the design system or the mockup, stop and ask. Do not touch `validation/companies/*/answer_key.json`. No attribution in commits.

## Results
(Codex fills in.)
