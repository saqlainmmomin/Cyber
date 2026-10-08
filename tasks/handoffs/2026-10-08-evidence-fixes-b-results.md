# Evidence fixes — Part B results

Implemented Part B only. No prompt changes, new LLM calls, migrations, Part A client-link edits, or Part C conclusion-card edits. Never opened any answer key. The three provided untracked context/handoff copies and all workbook/data files remain excluded from delivery.

## Files changed

- `app/routers/web.py`: original-file endpoint and evidence-viewer context.
- `app/services/evidence_viewer.py`: full-text/table presentation, extraction notes, scoped filename catalog matching, citation links, filename sanitization.
- `app/services/requirement_card.py`: remove whole-document text preview cap; character-span context unchanged.
- `app/templates/pages/evidence_detail.html`: original previews/download, full extraction, catalog, Supports and citations, stored category label.
- `tests/test_evidence_viewer.py`: 13 behavior tests, including parametrized cases.
- `tasks/todo.md`: Part B progress, browser blocker.
- This Results file and `tasks/handoffs/2026-10-08-evidence-fixes-b-pr-body.md`.

## Verification

- Proof-first initial run: 3 failures for missing original route, category/catalog/full text and spreadsheet presentation; 4 negative cases already returned 404 before the route existed.
- Final focused command: `OPENROUTER_KEY="" .venv/bin/pytest -q tests/test_evidence_viewer.py tests/test_yozora_s6.py tests/test_p6_7_requirement_card.py tests/test_design_lint.py` — 47 passed.
- Full suite: `OPENROUTER_KEY="" .venv/bin/pytest -q` — **1605 passed, 29 skipped**, 533 warnings, 291.00 seconds. Baseline 1592 passed/29 skipped; 13 behavior cases added. An earlier run had one test-fixture failure (invalid requirement ID), corrected before this final run.
- `git diff --check`: clean.
- No stale protected-surface guard required an allowance. `tests/yozora_paths.py` is absent at this checkout's HEAD. `git diff main...HEAD` was inspected as requested; local main is older (00f3300) than the starting HEAD (9b651fb), so the three-dot diff already contains inherited mainline changes. No guard was changed to compare another range.

## Click-through evidence and limits

Seeded with `OPENROUTER_KEY="" .venv/bin/python scripts/demo/seed_demo.py --db data/evidence-b/demo.db`. The seed selected `data/evidence-b/uploads/demo` as its upload root.

Browser execution was blocked: uvicorn on 127.0.0.1:8013 could not bind (`operation not permitted`), and Playwright Chromium could not launch (`MachPortRendezvousServer … Permission denied`). No desktop/mobile click-through or screenshots are claimed. Browser verification remains outstanding.

Instead, exercised the actual demo routes with FastAPI TestClient, following the NIST inventory upload form action and evidence file links:

- NIST assessment: `a951eb6d-a2ad-4f15-9122-7053840febb8`.
- Uploaded workbook record: `55a9baa4-20b0-4a85-b6df-eb693dd03ddd`, filename `Access_Review_220.xlsx`, category Processing records.
- “Access Review Detail” has all **220 Employee-ID records**. The workbook also has title/metadata and summary rows; those are retained too.
- Record 131/E131: Aarav Iyer, Cloud Console, Admin, Terminated, Exception, “Termination record present; access still enabled”.
- Shows “Desk review hasn't read this file yet.” and Processing records; Download returns bytes identical to the supplied workbook with attachment disposition.
- `Veldhara_Driver_App_Consent_Screen.png`: image preview markup, inline image/png, 10,816 bytes.
- `Veldhara_Information_Security_Policy_v3.1.pdf`: iframe markup, inline application/pdf, 1,295 bytes.
- Saved response HTML under `data/evidence-b/` for local inspection; none is staged/committed.

## Ambiguities and delivery

The catalog is keyed only by filename. Matching is restricted to evidence's originating/mapped assessments and uses the current version's filename. Same-name files/replaced versions cannot be distinguished; matching and duplicate ambiguity are visible. Historical conclusion revision citations are intentionally included.

No authentication exists yet (Track 4). Active status/path-containment checks guard original bytes but do not add user authorization.

Staging failed: Git could not create `/Users/saqlainmomin/dpdpa-gap-tool/.git/worktrees/dpdpa-evidence-b/index.lock` (`Operation not permitted`). Changes therefore remain unstaged. The explicit path-limited commit attempt also failed because the new files could not be added to the index. Intended message: `feat(evidence): show originals, extracted text and stored analysis`. No push, PR, or merge performed.
