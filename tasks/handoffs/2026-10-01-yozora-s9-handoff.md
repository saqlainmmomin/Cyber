# Yozora S9: System states, dark mode and mobile pass

**Written:** 2026-10-01. **Owner:** Codex builds, Claude reviews every diff and screenshot before merge, Saqlain merges. **Depends on:** V3-A merged (done, PR #94); slice S8 merged.
**Specs (read first):** `docs/product/yozora-design-system.md`, `docs/product/yozora-fidelity-gate.md`, `docs/product/yozora-migration-map.md` (rows for this slice), the approved mockups in `docs/product/2026-10-01-app-design-mockups/screens/`.

## Scope
Templates: 404/500 pages, toasts, skeletons, empty states.

Needs batch 7 approved. Audit every screen in dark and at 390px against baselines; close remaining lint exceptions.

## Tests
full suite plus the gate. Must-keep ids, `hx-*` and `data-*` come from the migration map; any intended string change is listed in the PR description so tests are updated deliberately.

## File-set guard
Add a per-PR `:(exclude)` allowance for this slice's template and test files in the P6-2b file-set guard. Never delete guards.

## Screenshot gate
Baselines for this slice's screens, light and dark, at 1440 and 1024 (390 for client-facing). Thresholds from the fidelity gate: 0.4% differing pixels, no changed region over 40x40. Post candidate, baseline and diff images in the PR for Saqlain.

## Stop and ask
If a visual detail is not in the design system or the mockup, stop and ask. Do not touch `validation/companies/*/answer_key.json`. No attribution in commits.

## Results
(Codex fills in.)
