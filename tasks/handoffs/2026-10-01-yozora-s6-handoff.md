# Yozora S6: Documents, desk review and evidence

**Written:** 2026-10-01. **Owner:** Codex builds, Claude reviews every diff and screenshot before merge, Saqlain merges. **Depends on:** V3-A merged (done, PR #94); slice S5 merged.
**Specs (read first):** `docs/product/yozora-design-system.md`, `docs/product/yozora-fidelity-gate.md`, `docs/product/yozora-migration-map.md` (rows for this slice), the approved mockups in `docs/product/2026-10-01-app-design-mockups/screens/`.

## Scope
Templates: documents_tab, document_list, upload_status, desk_review_*, evidence_*, aws_evidence*, workpaper*.

Needs batch 4 approved. Evidence span keeps its highlighted citation markup.

## Tests
existing documents, desk review, evidence and workpaper tests. Must-keep ids, `hx-*` and `data-*` come from the migration map; any intended string change is listed in the PR description so tests are updated deliberately.

## File-set guard
Add a per-PR `:(exclude)` allowance for this slice's template and test files in the P6-2b file-set guard. Never delete guards.

## Screenshot gate
Baselines for this slice's screens, light and dark, at 1440 and 1024 (390 for client-facing). Thresholds from the fidelity gate: 0.4% differing pixels, no changed region over 40x40. Post candidate, baseline and diff images in the PR for Saqlain.

## Stop and ask
If a visual detail is not in the design system or the mockup, stop and ask. Do not touch `validation/companies/*/answer_key.json`. No attribution in commits.

## Results
(Codex fills in.)
