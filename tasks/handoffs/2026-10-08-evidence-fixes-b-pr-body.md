## Summary

Part B only: make the evidence record show original files, full extracted text (including spreadsheet tables and extraction notes), the stored desk-review document catalog, and Supports/citation links. Whole-document span views now show the complete text. Category labels preserve stored categories, including Access control policy.

AI-coherence loop steps: **read → pre-fill → judge**. The existing AI produces document summaries, types, coverage areas and citations; the auditor sees them beside the stored extraction and original download/preview. Citation links open highlighted source passages. This is read-only visibility: it does not change downstream scoring or analysis, introduce LLM calls, or modify prompts.

Catalog entries are matched by the current version's filename within originating/mapped assessments. The catalog has no version identity, so same-name files and replaced versions remain ambiguous; the page labels filename matching and multiple matches explicitly. All conclusion revisions and desk-review findings citing any version of this evidence are listed.

**No-auth note:** there is no authentication yet; Track 4 adds it. File delivery checks active evidence/version status, resolved storage containment under UPLOAD_DIR, file presence, safe disposition filenames, the stored MIME, and nosniff. Only PDF/PNG/JPEG/WEBP may render inline; other types download.

## Click-through

upload Saqlain's access-review workbook to the demo NIST assessment → its record shows a Download button, the "What the AI read" table has 220 detail rows including record 131 (E131, terminated, Admin, "access still enabled"), section 3 says desk review hasn't run, category shows the chosen category. Open the demo's consent PNG and a PDF → both render inline.

## Verification

- Focused viewer/inventory/span/design-lint checks: 47 passed.
- Full suite: **1605 passed, 29 skipped** (baseline 1592 passed, 29 skipped); command `OPENROUTER_KEY="" .venv/bin/pytest -q`.
- Isolated demo: `data/evidence-b/demo.db`, upload root `data/evidence-b/uploads/demo`. In-process HTTP uploaded the supplied workbook to NIST, counted 220 Employee-ID detail records, verified E131, Processing records category, no desk-review catalog message, and byte-identical download. Demo consent PNG/PDF returned inline dispositions and preview markup.
- Browser click-through (done by Claude after Codex's sandbox blocked it, :8005 on the same isolated demo): workbook record shows Download, category "Processing records", "Desk review hasn't read this file yet", two sheet tables with every row, E131 row present (Aarav Iyer, Cloud Console, Admin, Terminated, "Termination record present; access still enabled"). Consent PNG renders inline (1280px loaded). Policy PDF served `inline`, `application/pdf`, `nosniff`.
- Review fix: citation lookup narrowed in SQL to rows that mention this evidence's version ids (was a full scan of every conclusion revision and desk-review finding on each page load).

## Fix pass after Saqlain's browser review

1. **Sheet header.** Rows above the real column names (title, metadata) now show as a small table above the main one. The header is the first early row that is as wide as the widest row, with no empty or numeric cells. Your workbook's detail sheet now has "Record # | Employee ID | ..." as its header and exactly 220 rows. Mixed-layout sheets (the summary sheet) show without a header rather than with a wrong one.
2. **Stray `|` in cells.** Empty cells (`a | | b`) now split into empty cells instead of a leading "| ".
3. **Sideways scroll at phone width.** The Format value, the page title and the Download button now wrap long names. Checked at 375px: the workbook, PDF and PNG records have no sideways scroll. The Q2 record still overflows by about 50px because of the shared breadcrumb bar (long engagement name plus filename). That is app chrome on every page, not this PR, so it is left as-is.
4. **Citation label.** "Conclusion: ISO.A5.18" now reads "Conclusion: Access rights (ISO.A5.18)".

## Design pass — evidence record

- [x] Orientation: evidence filename/status precede the four sections; existing Upload new version remains the primary action.
- [x] Priority: status and metadata come first; extraction is in a scrollable region.
- [x] Scannable: spreadsheet tables, catalog summaries, and smaller assessment/location metadata.
- [x] Done states: existing upload/archive behavior preserved; this viewer adds no save operation.
- [x] Wording: framework names in Supports come from the evidence mappings.
- [x] Desktop browser inspection (Claude). Mobile not inspected; Supports table no longer hides columns below 768px.
