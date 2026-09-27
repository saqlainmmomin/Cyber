# P6-4-cap: lift the 5,000-word upload cap `[AR: extraction]`

This task turns the per-document upload cap into a safety bound:

- **`max_document_words`** default goes from `5000` to `200000`. It becomes a guard against pathological files, not an analysis cap.
- **`document_processor._truncate`** keeps its whitespace normalisation. Above the bound it now cuts at the character offset where word `N+1` starts, so line breaks survive. Today it re-joins the kept words with single spaces.
- **v1's 20,000-word total (`max_total_document_words`) stays.** v1 remains the frozen baseline. Its prompt input is still bounded, but a single long document can now fill that budget.

**This PR deliberately changes v1 behaviour for new uploads** (see "What changes in v1"). It cannot share P6-4's "flag off is byte-identical" gate, which is why D-P6-4-R split it out.

**Spec:** D-P6-4-R in `tasks/handoffs/2026-09-28-p6-4-v2-stage-2-judge.md` (mini-spec items 1-5, and Step 0 fact 11). `tasks/todo.md:94`.
**Owner:** Claude designs (this file + contract tests) → Codex implements → Claude runs an adversarial review (`[AR: extraction]`) → PR. Per `tasks/agent-ownership.md`, Phase 6.
**Branch:** `claude/p6-4-cap-upload-limit` from `origin/main` @ `9b0dbea` (worktree `/Users/saqlainmomin/dpdpa-gap-tool-p6-4-cap`). Designer commit: the one that adds this file.
**Depends on:** P6-4 (merged, PR #74). **Runs in parallel with:** the P6-4 "what's missing" pass (`claude/p6-4-whats-missing`). **Blocks:** the P5-9 v1 baseline re-run, and through it P6-5.

> **The contract tests are already written. They are the contract.** `tests/test_p6_4_cap_upload_limit.py` has 16 tests, written by the designer before implementation. Before implementation **11 fail and 5 pass**. The 11 fail only for missing-code reasons: the default is still `5000`, `_truncate` still cuts at 5,000 words and joins with spaces, so the 30k-word documents come back as 5,000 words plus the marker. The 5 that pass are pins that must stay green: 1b (the 20k total), 2's exactly-at-the-bound case, 3's marker on single-line text, 7b (the image path) and 9 (the file-set guard). Make all 16 pass **without editing the file**. Do not weaken, skip, `xfail`, re-parametrize or delete any test. If you believe a test is wrong, leave it failing and explain in `## Results`. You may add tests in `tests/test_p6_4_cap_extra.py`.
>
> The designer checked the file against a throwaway reference implementation (not in the repo; implement from this spec). With it: all 16 pass. The full suite was **1030 passed, 10 skipped, 0 failed**: the 1014 pre-existing tests plus the 16 new ones, with the guard edits in D-P6-4-cap-F committed. Without those guard edits exactly three guards fail, each only on `app/services/document_processor.py`. No golden recording, prompt fingerprint or PDF hash moved. Six targeted mutations each failed at least one contract test: no `rstrip`, no normalisation, space-join, off-by-one cut, a 100k default, and a raised 20k total.

> **If the code forces a deviation from this design, stop and report it in `## Results`. Do not pick an alternative.**

> **Answer-key independence (D-P5-9-C).** Do not open, grep, glob, list or read: anything under `validation/`; `tasks/handoffs/*p5-9*`; `docs/plans/2026-09-24-002-*`; `scripts/seed_test_companies.py`, `scripts/test_ground_truth.json`, `scripts/seed-v2-prompt.md`; `scripts/validation/**`; `tests/test_validation_harness.py`; any `answer_key.json`. Scope every search to `app/`, `tests/test_p6_4_cap_*.py` and this file.

> **Codex cannot write `.git`.** No `git add/commit/branch/stash`. Read-only git is fine; the guards use it. The orchestrator commits.

## Goal

1. New uploads and new versions store up to 200,000 words of extracted text per document, with line structure intact. Stage 0 chunking needs the line structure.
2. Above 200,000 words the text is cut at a word boundary, keeps its line breaks, and ends with the existing marker.
3. v1 prompts stay bounded by the 20,000-word total, unchanged.
4. v2 (`load_source_documents`) receives the full stored text. It already does, with no code change.

## Step 0 (before writing code)

1. `main` == `origin/main` == `9b0dbea`. Run `.venv/bin/pytest -q -p no:cacheprovider` and record the counts in `## Results`. Designer baseline before any edit: **1014 passed, 10 skipped, 0 failed**. With this commit's files in place: the 5 pins pass and the 11 contract tests fail as described. `tests/test_retention.py::test_scenario_13_*` fails whenever files under `tests/` are uncommitted and passes once committed; ignore it.
2. Confirm these facts. **If any is false, stop and report.** Line numbers are from `9b0dbea`.
   1. `app/config.py:17` `max_document_words: int = 5000`; `:18` `max_total_document_words: int = 20000`. `.env.example` mentions neither.
   2. `app/services/document_processor.py:29-38` `extract_text(file_path, file_type)` dispatches to `_extract_pdf` (`:41-58`, pages joined with `"\n\n"`, then `_truncate` at `:58`), `_extract_docx` (`:61-73`, paragraphs and table rows joined with `"\n"`, then `_truncate` at `:73`) and `_extract_image` (`:158-171`, vision text, **no** `_truncate`).
   3. `document_processor.py:76-87` `_truncate` collapses `\n{3,}` → `\n\n` and ` {2,}` → ` `, then above the cap returns `" ".join(words[:N]) + "\n\n[... truncated to first N words ...]"`. That join is where line structure is lost. `extract_relevant_sections` / `_truncate_to_words` (`:90-155`) have no caller in `app/` and are out of scope.
   4. The only writers of stored text are the three `extract_text` calls in `app/services/evidence.py`: `ingest_upload` (`:697`, stored `:705`), `ingest_engagement_upload` (`:755`/`:764`) and `ingest_new_version` (`:799`/`:807`). Routes reach them from `app/routers/documents.py:44` (API upload), `app/routers/web.py:1175` and `:1256` (web upload and new version), `app/routers/evidence.py:35` and `app/services/magic_links.py:469`. None of them truncate.
   5. `app/services/evidence.py:875-910` `analysis_documents` returns `version.extracted_text` / legacy `extracted_text` untruncated. It feeds v1 desk review (`app/services/desk_review.py:67`), v1 analysis (`app/services/analysis_pipeline.py:140`, `app/routers/analysis.py:138`) and v2 sources.
   6. `app/services/desk_review.py:111-114` branches to `run_desk_review_v2` **before** `:117` `_truncate_documents`. That function (`:678-695`) caps the total at `max_total_document_words` in upload order and appends `"\n\n[... truncated ...]"`. It flattens the cut document with spaces; that is v1 and stays.
   7. `app/services/claude_analyzer.py:419-455` `_truncate_documents` does the same with a DPDPA category priority order. It is called at `:89` (DPDPA path) and `:521` (multi-framework path). Desk-review evidence is grounded against the **untruncated** documents (`:209` `_ground_evidence_quotes`, `:528` `grounding_documents=documents`).
   8. `app/services/grounding/sources.py:38-75` `load_source_documents` copies `version.extracted_text` (`:57`) or the legacy row's text (`:73`) with no cap. `desk_review_v2.py:203` and `analysis_v2.py:471` are its only callers. No `grounding/` module reads `max_document_words` or `max_total_document_words`. **v2 therefore already gets the full stored text**; it has been getting a 5,000-word, space-joined text for long documents.
   9. v1 desk-review citations re-locate quotes in stored text via `app/services/citations.py` `cite_quotes` (sources built from `version.extracted_text`, `:130`).

## Decisions (made here so they are not relitigated)

### D-P6-4-cap-A: The setting

`app/config.py`: `max_document_words: int = 200000`, with a comment directly above it (within 4 lines) containing the word "safety". It should say this is a safety bound for pathological files at extraction, not an analysis cap, and that v1 prompts stay bounded by `max_total_document_words`. `max_total_document_words` keeps `20000`. No other setting. No `.env.example` line (P6-4 and P6-6 both edit that file; the default is enough).

### D-P6-4-cap-B: `_truncate`

Keep the two normalisation substitutions, in their current order. Words are `str.split()` words; `re.finditer(r"\S+", text)` gives the same boundaries. With `N = settings.max_document_words`, read at call time:
- **At or below `N` words:** return the normalised text, unchanged from today.
- **Above `N`:** return `text[:start_of_word_N+1].rstrip() + "\n\n[... truncated to first {N} words ...]"`. The body is exactly the first `N` words with their original separators. The `rstrip` drops the separator before word `N+1`, so the marker always follows `"\n\n"` and never produces `"\n\n\n"`. The marker string is unchanged. P6-3a's grounding already treats it as a non-quotable line (`tests/test_p6_3a_grounding.py:824`, `:1551`).
- Don't materialise the whole word list for a 200k-word text if you can avoid it (for example, `itertools.islice` over `finditer` up to `N + 1`). This is a style note; no test measures it.

Keep the function name, signature and docstring intent. Update the docstring to say it keeps line breaks.

### D-P6-4-cap-C: v1's total stays; v1 files are not edited

`desk_review.py` and `claude_analyzer.py` are **not touched**. Their `_truncate_documents` still enforce 20,000 words in total (scenario 6 and 1b pin it).

### D-P6-4-cap-D: Scope of "new uploads"

Only text extracted after merge changes. Stored `EvidenceVersion.extracted_text` rows are immutable evidence records: no re-extraction, no backfill, no migration. A consultant who wants full text for an old document uploads a new version (`ingest_new_version`), which extracts afresh. Legacy `AssessmentDocument` rows are untouched.

### D-P6-4-cap-E: Images

`_extract_image` does not go through `_truncate` today and still doesn't. Its length is bounded by the vision call's `max_tokens=1500`. Scenario 7b pins this.

### D-P6-4-cap-F: Guard updates (designer-owned; already applied, Codex must not edit)

Following the stale-guard convention (targeted `:(exclude)` entries naming the PR, never deleting a guard), each of these gains `":(exclude)app/services/document_processor.py"` with a P6-4-cap comment. `app/config.py` was already excluded in the two guards that list it.
- `tests/test_p6_3a_grounding.py` `PROTECTED_PATHS` (scenario 17).
- `tests/test_p6_6_report_foundations.py` `P6_4_AND_PROTECTED_PATHS` (scenario 17).
- `tests/test_p6_nist_csf2_alignment.py::test_protected_surface_guard_uses_three_dot_diff`.

Every other protected path still fails those guards. The P6-4-cap suite adds its own file-set guard (scenario 9).

### D-P6-4-cap-G: File set and overlap with the "what's missing" PR

P6-4-cap changes exactly: `app/config.py`, `app/services/document_processor.py`, this handoff (`## Results` only), and `tasks/todo.md` (tick line 94). The designer commit adds `tests/test_p6_4_cap_upload_limit.py` and the three guard edits in F. Codex may add `tests/test_p6_4_cap_extra.py`.

The "what's missing" PR (`claude/p6-4-whats-missing`) touches `app/services/desk_review_v2.py`, `app/services/grounding/**` and possibly the desk-review prompts. **None of those is in this set, so there is no application-file overlap.** Possible textual overlaps are all resolvable by keeping both sides:
- `app/config.py`, only if that PR adds a setting. It would be a different line.
- The guard exclusion lists in F, if that PR also edits them.
- `tasks/todo.md`.

Merge `origin/main` into whichever branch lands second (never rebase), then run `git branch -f main origin/main` before the suite.

## What changes in v1 (state this in the PR body)

For documents uploaded or re-versioned after merge:
1. **Stored extracted text length.** Previously PDFs and DOCX files were cut at 5,000 words, space-joined, plus the marker. Now the full text is stored, up to 200,000 words, with line breaks. Visible as `text_length` in the documents API and evidence panel. Smoke: a 30,000-word DOCX went from 58,540 stored characters (5,007 words, 2 newlines) to 378,499 characters (30,000 words, 599 newlines).
2. **v1 prompt input.** When any document exceeds 5,000 words, v1 desk review and v1 analysis see more of it, up to the unchanged 20,000-word total across documents. A single 30k-word policy now fills the whole 20k budget, so later documents in upload order (desk review) or priority order (analysis) can drop out of the prompt where before they fitted.
3. **v1 quote grounding and citations.** `_ground_evidence_quotes` and `cite_quotes` search the stored text, so quotes from beyond word 5,000 can now be kept and cited. Before, they were dropped as ungrounded.
4. Short documents (≤ 5,000 words) are byte-identical to today.

**Re-recorded tests or fingerprints: none.** The v1 prompt fingerprints (`tests/test_p6_1b_framework_batching.py`), golden DPDPA recordings and PDF hashes do not pass through `_truncate`, and the full suite stayed green against the reference. The only existing-test edits are the three guard exclusions in F, already applied.

**The P5-9 v1 baseline must be re-run after this PR merges and before P6-5.** The v1-vs-v2 A/B has to compare against v1 as it now behaves on long documents.

**v2:** `load_source_documents` already passes the stored text through unchanged (Step 0 fact 8). After this PR, v2 Stage 0 sees the whole document, up to 200k words, with its lines. Before, it saw a 5,000-word single line. Scenario 5b confirms both readers get exactly the stored text. v2 cost grows with document length; it stays bounded by `v2_max_extraction_calls` (600).

## Key files

| Path | Change |
|---|---|
| `app/config.py` | D-P6-4-cap-A: one default and its comment |
| `app/services/document_processor.py` | D-P6-4-cap-B: `_truncate` body and docstring only (plus an import if needed) |
| `tests/test_p6_4_cap_upload_limit.py` (**already written; read-only for you**) | The contract |
| `tests/test_p6_4_cap_extra.py` (optional, new) | Any extra tests you add |
| `tasks/todo.md` | Tick line 94, noting that the P5-9 v1 baseline re-run is still pending |
| this file | Append `## Results` only |

## Do not touch

- The contract and guard edits: `tests/test_p6_4_cap_upload_limit.py`, `tests/test_p6_3a_grounding.py`, `tests/test_p6_6_report_foundations.py`, `tests/test_p6_nist_csf2_alignment.py`.
- v1 paths: `app/services/desk_review.py`, `app/services/claude_analyzer.py`, `app/services/analysis_pipeline.py`, `app/dpdpa/**`, `app/frameworks/**`, `tests/fixtures/**`, `tests/support/**`.
- The parallel PR's surface: `app/services/desk_review_v2.py`, `app/services/grounding/**`, `app/services/analysis_v2.py`, all prompt modules.
- In `document_processor.py`: everything except `_truncate` (extraction functions, `extract_relevant_sections`, `_truncate_to_words`, the vision seam).
- `app/services/evidence.py`, `app/services/citations.py`, `app/routers/**`, `app/models/**`, `app/schemas/**`, `alembic/**`, `.env.example`, every other existing test file.
- Everything in the independence list.

## Non-goals

Re-extracting stored evidence, or any migration. Changing the 20k total or v1's truncation order. Truncation for images. Removing the dead `extract_relevant_sections`. Surfacing a "truncated" flag in the UI. v2 cost controls.

## Test scenarios (implemented in `tests/test_p6_4_cap_upload_limit.py`)

Documents are built in-process (python-docx, fpdf2). No network: the one LLM seam involved (vision) is stubbed.

1. **Default** (`test_scenario_1_max_document_words_default_is_the_safety_bound`): the `Settings` field default and live value are `200000`, and the comment contains "safety". Red on clean.
   1b. (`test_scenario_1b_v1_total_document_cap_is_unchanged`): `max_total_document_words` is `20000`. Pin.
2. **Below the bound** (`test_scenario_2_six_thousand_words_pass_unchanged_apart_from_whitespace`): a 6,000-word text with messy whitespace equals today's normalisation exactly. Red on clean. `test_scenario_2_exactly_at_the_bound_is_not_truncated`: `N` words with `N` set to 40 come back unchanged, with no marker. Pin.
3. **Above the bound** (`test_scenario_3_over_bound_keeps_exactly_n_words_and_its_newlines`): the output equals `normalised[:start of word N+1].rstrip() + marker(N)`. The body's words are the first `N`, its newlines are kept, and there is no `\n\n\n` or double space. Red on clean. `test_scenario_3_cut_after_a_line_end_leaves_no_trailing_whitespace`: when word `N+1` opens a paragraph, the result is the first two paragraphs plus the marker. Red on clean. `test_scenario_3_marker_uses_the_configured_bound`: the marker names `N`. Pin.
4. **Real extraction** (`test_scenario_4_docx_thirty_thousand_words_extract_in_full`): a 600-paragraph, 30,000-word DOCX extracts to exactly its paragraphs joined by `\n`. `test_scenario_4_pdf_over_five_thousand_words_keeps_lines`: a 6,000-word, 600-line PDF has no marker, all its words, and at least 590 newlines. `test_scenario_4_docx_over_the_bound_keeps_lines`: with `N=125`, two whole paragraphs, a newline, 25 words, then the marker. All red on clean.
5. **Route and readers** (`test_scenario_5_upload_route_stores_thirty_thousand_words_with_line_breaks`): `routers.documents.upload_document` with a 30k-word DOCX stores `EvidenceVersion.extracted_text` equal to the full text (599 newlines), and `text_length` equals its length. `test_scenario_5_v1_and_v2_readers_get_the_full_stored_text`: `analysis_documents` and `grounding.sources.load_source_documents` return exactly that text. Both red on clean.
6. **v1 prompt input** (`test_scenario_6_v1_sees_up_to_twenty_thousand_words_of_one_long_document[desk_review|claude_analyzer]`): a 30k-word extracted DOCX through each `_truncate_documents` yields exactly its first 20,000 words plus `"\n\n[... truncated ...]"`. Red on clean, where only about 5,000 words reach it.
7b. **Images** (`test_scenario_7b_image_extraction_is_not_truncated_or_reformatted`): the stubbed vision text passes through verbatim. Pin.
9. **File set** (`test_scenario_9_only_config_and_document_processor_change_under_app`): `git diff --name-only` (`main...HEAD` and the working tree) under `app`, `alembic` and `.env.example` is a subset of `{app/config.py, app/services/document_processor.py}`. Pin.

## Verification (before reporting done)

1. `.venv/bin/pytest -q -p no:cacheprovider tests/test_p6_4_cap_upload_limit.py`: 16 passed, three runs.
2. Full suite: expect **1030 passed, 10 skipped** (plus any extra tests you add). The only acceptable failure is `test_retention.py::test_scenario_13_*` while files are uncommitted.
3. `git diff --name-only main...HEAD; git status --porcelain`: only the files in D-P6-4-cap-G.
4. **Smoke (report the printed lines in `## Results`):** push a synthetic 30,000-word, 600-paragraph DOCX through the real HTTP route `POST /api/assessments/{id}/documents` and print the stored length, word count, newline count, whether the marker is present, and whether `analysis_documents` and `load_source_documents` return exactly the stored text. Use a `TestClient` with `get_db` overridden to a temp SQLite built by `Base.metadata.create_all`, `settings.upload_dir` in a temp dir, `_register_frameworks()`, and a Client, Engagement and Assessment seeded as in the test file. Run it with `PYTHONPATH=.` from the repo root. Designer's reference run:
   `status 201 text_length 378499` / `stored_words 30000 stored_chars 378499 newlines 599 marker False` / `v1_reader_equal True v2_reader_equal True`. On clean `main` the same script printed `text_length 58540`, `stored_words 5007`, `newlines 2`, `marker True`.
   Also run once with `settings.max_document_words = 1000` and confirm the stored text is 1,000 words, keeps its newlines and ends with `[... truncated to first 1000 words ...]`.

## Adversarial review checkpoints `[AR: extraction]` (after Codex, before the PR)

- The below-bound output is byte-identical to `9b0dbea` for a sample of messy inputs (compare against `git show main:app/services/document_processor.py`).
- There is no off-by-one at the cut: the body has exactly `N` words.
- No file outside D-P6-4-cap-G is changed. `desk_review.py` and `claude_analyzer.py` diffs are empty.
- The PR body carries "What changes in v1", including the P5-9 re-run requirement.

## Open questions for Saqlain

None blocking. Defaults taken:
1. Old evidence stays at 5k. Fresh text comes via a new version, not a backfill (D).
2. No `.env.example` line (A).

Say if you want either changed.

## Results

