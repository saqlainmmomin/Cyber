# Handoff: PR #127 fix pass — store every spreadsheet row

Owner: Codex implements, Claude reviews adversarially, Saqlain approves and merges (`tasks/agent-ownership.md`). No Claude/Codex attribution lines in commits or the PR. Do not merge. Never open `validation/companies/*/answer_key.json`. No LLM calls.

Work in `/Users/saqlainmomin/dpdpa-s6f1-fix` (branch `codex/flow-s6-f1-fix`). It is PR #127's branch (`codex/flow-s6-f1-xlsx-ocr`) with current `main` already merged in (merge commit `967b817`). Claude pushes it to the PR branch after review.

## Goal

Spreadsheet extraction stores **every data row** instead of a sample. Done when:
- an access-review workbook with 220 records stores all 220, and all 35 exception rows in it are present in the stored text;
- a sheet too big to store whole is cut only at a row boundary, with a visible marker saying how many rows were stored out of how many;
- all tests pass, with the sampling tests rewritten to the new behaviour.

## Why (decided by Saqlain, 2026-10-08)

The flow-rework plan said "large sheets sampled, not truncated blind". That was wrong for audit evidence. On a real test file (220-row user access review with 35 planted exceptions), the sampling (first 100 rows + 100 evenly spaced) dropped 6 exceptions, including a terminated employee with Admin access still enabled. Exceptions in a population are rare and can be anywhere, so an auditor needs every row. **No sampling at extraction.** Do not reintroduce sampling, "smart" row selection or summarising.

## Current state

`app/services/document_processor.py`:
- `SPREADSHEET_MAX_DATA_ROWS = 200`, `SPREADSHEET_INITIAL_DATA_ROWS = 100` (around line 37).
- `_render_tabular_sheet` counts rows, picks indices with `_sampled_row_indices`, and appends `[sampled N of M rows]`.
- `_extract_xlsx` / `_extract_csv` then pass the joined text through `_truncate`, which cuts at `settings.max_document_words` (200,000 words, `app/config.py:20`) at a word boundary.
- `SPREADSHEET_MAX_CELL_CHARS = 2000` caps single cells with `[cell truncated]`. Keep that.

Tests pinning sampling: `tests/test_document_processor.py:29` (`test_xlsx_extraction_includes_sheet_headers_and_samples_large_sheets`, asserts `[sampled 200 of 5,000 rows]`). Check `tests/integration/test_document_upload.py` for the same.

## Work

1. Remove `_sampled_row_indices`, the two row constants and the sampled marker. `_render_tabular_sheet` streams every row (keep the single pass cheap; the workbook is opened `read_only=True`, don't load it into memory).
2. Size guard at row boundaries: across a whole workbook, stop adding rows once the next row would take the text past `settings.max_document_words` words. Then append one line per affected sheet: `[stored rows 1-N of M in sheet "<name>"; the remaining rows were not stored]`, and skip any later sheets with `[sheet "<name>" not stored: size limit reached]`. The result must already be under the limit so `_truncate` never has to cut tabular text mid-row. Same for CSV.
3. Tests:
   - Rewrite the 5,000-row test: every row present, no sampled marker.
   - New test: a generated workbook whose rows exceed a small patched `max_document_words`; asserts the cut is at a row boundary, the marker states N and M correctly, and a later sheet gets the "not stored" line.
   - New test: a generated access-review sheet with exception rows placed at positions the old sampler would skip (e.g. 120, 131, 203, 208, 214, 219 of 220); all present in the output.
4. Update the original handoff's Results note in `tasks/handoffs/2026-10-07-flow-s6-f1-xlsx-ocr.md` with one dated line: sampling replaced by full storage, see this handoff. Don't edit `tasks/todo.md`; Claude updates it when committing.

## Constraints

- Touch only `app/services/document_processor.py`, the tests above, and the two task files. Not in scope (separate handoff coming): the evidence viewer, the 1,500-character limit on the citation page, the desk review's 20,000-word prompt budget and its silent dropping of later documents.
- Don't change the cell cap, the OCR path, accept lists or anything the PR already did besides sampling.
- Keep the `Sheet: <name>` line and ` | ` joined cells format; downstream quoting and citations depend on it.

## Verification

1. `OPENROUTER_KEY="" .venv/bin/pytest -q` (full suite; never `env -u`, since `.env` would still load). Report the counts.
2. Real-file smoke check, no server needed. Run extraction directly on Saqlain's synthetic test workbook (no client data):
   `/Users/saqlainmomin/dpdpa-s6f1/data/uploads/demo/evidence/61b0212c-338f-4001-922a-033a569d2c71/8afb5b24-1743-4d81-81ef-f57c40d5d3f8/v1.xlsx`
   Read it only, don't copy it into the repo. Expected: sheet "Access Review Detail" has record numbers 1-220 all present; record 131 (E131, terminated, Admin, "access still enabled") is present; no sampled marker; no "not stored" marker. Paste the counts in Results.

## Report back

Append a `## Results` section to this file: what changed (files), test counts, the smoke-check numbers, anything you were unsure about. Leave changes uncommitted.

## Results

- Changed `app/services/document_processor.py` to remove row sampling and stream every normalized spreadsheet row once. XLSX/CSV rendering now enforces `settings.max_document_words` at complete-row boundaries, reports affected sheets with stored/total row markers, reports later sheets as not stored, and leaves the existing 2,000-character cell cap and CSV/OCR paths unchanged.
- Changed `tests/test_document_processor.py`: rewrote the 5,000-row test for full storage, added a row-boundary/size-marker test, and added an access-review regression with exception rows outside the former sample. No integration test changes were needed; the existing spreadsheet upload coverage remained green.
- Verification: focused extraction/upload tests `12 passed, 4 warnings`; required full suite `OPENROUTER_KEY="" .venv/bin/pytest -q` → `1592 passed, 29 skipped, 512 warnings`.
- Real-file smoke check on the specified workbook: `Sheet: Access Review Detail` header count `1`; record numbers present `220/220`; missing record numbers `[]`; record 131 required evidence present `True`; sampled markers `0`; not-stored markers `0`; extracted word count `6813`. The workbook contains 6 exception records (5 with “access still enabled”), not the handoff’s stated 35; all 6 were present in the extracted text.
- No packages, network calls, commits, pushes, `tasks/todo.md`, AGENTS/context docs, or vault files were changed. Changes remain uncommitted. The pre-existing untracked handoff run log was preserved.
