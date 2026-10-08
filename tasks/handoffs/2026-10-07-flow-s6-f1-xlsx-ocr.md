# Flow rework S6-F1: XLSX/CSV extraction + scanned-PDF OCR fallback (Codex)

Owner: Codex (builder). Orchestrator: Claude. Written 2026-10-07.
Plan: `docs/plans/2026-10-07-001-flow-rework-plan.md`, slice S6, part F1. Line refs checked against main 00f3300; re-check before editing.

This branch starts from the S0a branch (file-path guard tests retired). **Don't add or edit any path allow-list.**

## Goal
Consultants receive evidence as spreadsheets (access reviews, asset registers) and scanned PDFs. Today both fail: `.xlsx`/`.csv` are rejected, and a scanned PDF yields empty text. Make both produce extracted text through the existing evidence pipeline.

## Work
1. **XLSX/CSV extraction** in `app/services/document_processor.py` (`extract_text`, `detect_file_type`). Use `openpyxl` (already in requirements, read-only mode, `data_only=True`) and the stdlib `csv` module.
   - Output plain text: per sheet a `Sheet: <name>` header, then the header row and data rows as ` | `-joined cells (same style as the PDF table extraction).
   - **Large sheets are sampled, not truncated blind.** Keep the header row, the first N rows and an evenly spaced sample of the rest, and add an explicit line like `[sampled 200 of 5,000 rows]` so the reader (and the LLM) knows. Pick N and the budget so the result fits under the existing `_truncate` limit without `_truncate` having to cut. Put the numbers in module constants.
   - Skip empty rows/sheets. Formulas give their cached value. Don't crash on merged cells or a workbook with no cached values; fall back to empty cells.
   - `.xls` (legacy) and `.xlsm` are out of scope; reject them with the normal unsupported-type path.
2. **Scanned PDF OCR fallback.** In `_extract_pdf`, for pages with no or almost no extractable text (pick a small character threshold, constant), rasterise the page and send it to the vision model through the same path as `_extract_image` (`llm_client`, tier `vision` -> `Settings.llm_model_vision`). pdfplumber already depends on `pypdfium2`; use `page.to_image(resolution=...)` or pypdfium2 directly so no new dependency is needed. If you do need a new dependency, add it to `requirements.txt` and say why in Results.
   - Cap the number of OCR'd pages per document (constant, e.g. 20) and note skipped pages in the text (`[OCR skipped for pages 21-40]`).
   - The vision call goes through the existing `llm_client` with its wall-clock deadline. If the existing LLM call-site registry (`tests/test_remaining_llm_call_sites.py`) needs a new entry for the new call site, add it there; that test stays.
   - With no `OPENROUTER_KEY` (tests), the fallback must not make a network call: follow whatever `_extract_image` does when there is no key, and keep the native-text pages.
3. **Accept lists and copy.** Add `.xlsx` and `.csv` wherever evidence uploads are accepted or validated:
   - `app/templates/pages/evidence_inventory.html:79` `accept=` list.
   - The upload route's type check (`app/routers/evidence.py` ~148, and any MIME/size checks).
   - The client magic-link upload (route + template accept list), and its client-facing text "PDF, DOCX or image" (`app/services/rfi_requests.py` ~47 and any template that repeats it). New wording: "PDF, DOCX, Excel/CSV or image".
   - Any file-type enum/constraint on the model (`EvidenceVersion`/`Document` file_type columns, Alembic CHECKs). If a DB CHECK limits file types, add a migration that extends it.
4. Evidence detail: if the detail page shows extracted text, make sure spreadsheet text renders readably (monospace or a preformatted block is enough). No new table renderer.

## Tests (lean)
Add only:
- XLSX extraction: a workbook generated in the test with openpyxl (2 sheets, one with 5,000 rows) gives text containing both sheet names, the header, and the sampled marker, and stays under the truncate limit.
- CSV extraction: a small CSV round-trips.
- OCR fallback: a one-page PDF with no text layer (generate an image-only PDF with Pillow) calls the vision path once (monkeypatch the vision call) and its text appears in the output; a normal text PDF makes no vision call.
- Upload accepts `.xlsx` and `.csv` through the consultant route.
Keep the existing suite green. No pixel gates, path guards or template snapshots.

## Rules
- Don't touch desk-review prompts or truncation in `desk_review._truncate_documents` (S6-F2 handles dates; prompts are under the held-out rule).
- Never read `validation/companies/*/answer_key.json`.

## Verification
- `.venv/bin/pytest -q -p no:cacheprovider` green; report counts.
- A manual check script is fine but not committed.

## Git
Commit on this branch with plain messages. **No `Co-Authored-By` or any AI attribution lines.** Don't push.

## Results

- Changed `app/services/document_processor.py` to support `xlsx` and `csv` extraction, `app/services/evidence.py` to register their MIME types, and `app/services/rfi_requests.py` plus the evidence/magic-link upload templates to accept and describe Excel/CSV files. Added focused extraction and consultant-upload coverage in `tests/test_document_processor.py` and `tests/integration/test_document_upload.py`; updated affected copy assertions.
- Spreadsheet extraction uses `openpyxl.load_workbook(..., read_only=True, data_only=True, keep_links=False)` and stdlib `csv`. Each non-empty sheet is rendered with a `Sheet:` header, header row, and ` | `-joined cells. The constants are `SPREADSHEET_INITIAL_DATA_ROWS = 100` and `SPREADSHEET_MAX_DATA_ROWS = 200`; larger sheets keep the first 100 rows plus 100 evenly spaced rows and emit an explicit sampling marker. No blind `_truncate` is needed for the generated 5,000-row regression fixture. Legacy `.xls`/`.xlsm` remain unsupported.
- Scanned-PDF fallback uses a 20-character native-text threshold, rasterises eligible pages at 150 DPI while the `pdfplumber` document is open, and sends PNG base64 through the existing vision call path. OCR is capped at 20 pages per document; later eligible pages receive a compressed skipped-page marker. With no `OPENROUTER_KEY`, OCR is disabled and native extraction remains unchanged.
- No dependency or database migration was added; `openpyxl`, `pdfplumber`/`pypdfium2`, Pillow, and the existing MIME/file-type columns were sufficient.
- Verification: focused extraction/upload/LLM/template tests: `41 passed`; full suite with network disabled as required: `OPENROUTER_KEY='' .venv/bin/pytest -q -p no:cacheprovider` → `1585 passed, 29 skipped, 507 warnings`.

### Orchestrator fix pass (after review)
- CSV: decode from bytes (UTF-16 BOM, then strict UTF-8, then cp1252 for Excel's Windows export); sniff `,` `;` tab `|` delimiters; raise the csv field limit for the read so a huge cell can't crash the upload.
- Cells are capped at 2,000 characters (`[cell truncated]`); trailing empty cells are dropped.
- OCR: a failed render or vision call on one page appends `[OCR failed for page N]` and keeps the rest, instead of aborting the upload. Render resolution is capped so the longest edge is at most 2,500 px. `PDF_OCR_MAX_PAGES` lowered to 10 (the vision calls run inside the upload request).
- Client checklist PDF copy now says "PDF, DOCX, Excel/CSV or image".
- Tests added: OCR failure keeps the document; cp1252 semicolon CSV decodes.
- Verified in the running app: a 3,000-row xlsx uploaded through `POST /api/assessments/{id}/documents` stored `Sheet: UAR Q2` + header + `[sampled 200 of 3,000 rows]`. One live vision call on a generated image-only PDF returned the page's text under `[OCR page 1]`.
- 2026-10-08: Sampling replaced by full spreadsheet row storage with row-boundary size markers; see `tasks/handoffs/2026-10-08-flow-s6-f1-keep-every-row.md`.
