# Multi-framework cleanup (from tasks/cleanup-prompt.md)

Discovery: most of the prompt is already done in the working tree — all 6 framework
definitions have `scope_questions`, web.py aggregates them per selected framework,
scope_form.html renders grouped, context questions are already framework-agnostic,
pdf_export.py body/appendix already conditional on `dpdpa_only`.

## Remaining items

- [x] 1. web.py: evidence-checklist PDF/DOCX routes still use legacy `compute_scope`
      (DPDPA-only) — switch to `compute_scope_multi` + add shared
      `_selected_framework_ids()` helper (dedupe 3 inline copies)
- [x] 2. New-assessment flow: DPDPA pre-checked in template + silent `or ["dpdpa"]`
      fallback in create route — remove default, validate ≥1 framework selected
- [x] 3. pdf_export.py cover page: hardcoded "DPDPA Compliance" title → conditional
- [x] 4. rfi_generator.py: hardcoded DPDPA title, Claude prompt, system prompt →
      framework-aware via `framework_names` param; rename internal `dpdpa_section`
- [x] 5. rfi_export.py: hardcoded "DPDPA Compliance Gap Assessment" subtitle +
      confidentiality notice → `framework_label` param, passed from web.py routes
- [x] 6. Verify: uvicorn boots, pages render, pytest passes

## Discovered during cleanup (not yet done)

- [ ] Real scope profiling for non-DPDPA frameworks — `compute_scope_multi` currently
      includes all controls for them (only DPDPA gets conditional exclusion)
- [ ] Fix or delete untracked `tests/test_phase1_prefill.py` — 4 tests error on a
      missing `session` fixture (script-style tests, pre-existing)
- [ ] CyberAssess portfolio screenshots — blocker cleared, portal is ready

## UCC content completion (2026-07-11, shipped bbf5a2b)

- [x] Content-integrity validator (`tests/test_content_integrity.py`, 10 tests) + INTENTIONAL_SINGLETONS mechanism
- [x] Hermes handoff executed: 40 duplicate cluster memberships resolved, 69 orphan controls mapped, 32 DPDPA guidance entries — verified 25/25 tests, shipped
- [ ] Review 4 flagged mapping decisions in `tasks/handoffs/2026-07-11-ucc-content-completion.md` Results (only ISO A8.11/A8.12 in crypto cluster is debatable)
- [ ] Root `cyberassess.db` + `dashboard.png` untracked junk — gitignore or delete
