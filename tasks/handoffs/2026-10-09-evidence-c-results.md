# Evidence fix C results (2026-10-09)

Codex built items 1-5 and their tests, then hit its usage limit before the full suite, results and PR body were done. Claude reviewed the diff, fixed three issues, ran the suite and did the browser check.

## Files changed
- `app/services/evidence_locations.py` (new): one `location_label()` for "Page N", "Characters A–B" and "Whole document". Used by the span page, B's viewer and the conclusion card.
- `app/services/requirement_card.py`: loads every active evidence link for the assessment in one query and marks each file Cited or Not cited. Linked files replace the AI's missing-evidence suggestions. Requests already on the draft RFI stay.
- `app/templates/components/conclusion_card.html`: the citation location is a link to `/evidence-versions/{id}/span?ref=...#cited-span`. The filename links to `/evidence/{id}`.
- `app/templates/components/requirement_card_body.html`: new "Evidence on this control" block with "N files linked, M cited", each file marked "Cited" or "Not cited by the analysis", and the size-limit notice.
- `app/services/desk_review.py`: records `budget_skipped_filenames` in the existing `raw_ai_response` JSON. No migration, no prompt change.
- `app/services/evidence.py`, `app/routers/web.py`, `app/templates/partials/desk_review_findings.html`: desk-review citation names resolve from Evidence and EvidenceVersion as well as AssessmentDocument. The desk-review page shows "Not read by the analysis (size limit): ...".
- `design/yozora-patterns.css` and its generated copy: wrapping rules so long filenames don't scroll sideways.
- Tests: `tests/test_evidence_c_card.py`, `tests/test_evidence_c_desk_review.py` (13 tests).

## Review fixes (Claude)
1. The card hid the whole Missing evidence block when files were linked. That also hid requests the auditor had already added to the draft RFI, and their Remove button. Now only the unrequested suggestions drop. New test: `test_linked_files_keep_requests_already_on_the_draft_rfi`.
2. Codex edited the generated `app/static/css/yozora-patterns.css` by hand, which failed the token sync test. Moved the change to `design/yozora-patterns.css` and rebuilt.
3. New `RequirementCard` fields went after `other_rfi_requests`, which broke a P6-7b shape test. Reordered. Also fixed "1 files linked" to "1 file linked".

## Tests
- Baseline on `origin/main` (ffdacb0): 1614 passed, 29 skipped.
- This branch: 1627 passed, 29 skipped. Run with `OPENROUTER_KEY=""`.

## Browser check (Claude, demo seed on main's demo content, port 8007)
Demo-depth (`codex/demo-veldhara-depth`) had not merged, so this used the current demo.
- Current assessment, Conclusions, Access rights (ISO A.5.18): the citation reads "Characters 37–93". It opens the span page with "The quarterly review covered 9 of 11 production systems." highlighted, which matches the card's quote.
- The filename opens the evidence record for `Veldhara_Access_Review_Q2_FY26.docx`.
- "Evidence on this control": "2 files linked, 1 cited". Q2 review Cited, user access review export Not cited by the analysis. No Missing evidence box.
- 375px: no sideways scroll; long filenames wrap inside the card.

## Follow-up after Saqlain's review
- Card links (citation location, filenames) are underlined. They keep the normal text colour because `--accent-text` is unreadable in dark mode for most accents (pre-existing token bug).
- Desk review also records `budget_partial_filenames`: files the word budget cut part-way. Shown as "Partly read by the analysis (size limit): ..." on the desk-review page and on affected cards.
- Full suite: 1627 passed, 29 skipped.

## Open questions
- **Dec 2023 review is not on the list.** The spec expected three files. In the current seed the Dec 2023 review has no link to A.5.18, so it correctly isn't listed. If it should be, that is a seed change (demo-depth branch), not this PR.
- **Items 4 and 5 not visible on the demo.** The seed has no desk-review findings, so the size-limit notice and the filename fix are covered by tests only.
- Pre-existing: the conclusions page breadcrumb overflows by about 18px at desktop width. Not touched here.
