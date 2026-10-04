# Handoff: per-domain prior scores in the board report comparison (V3-C backend)

**Written:** 4 Oct 2026. **For:** a parallel Claude or Codex session. **Merging and pushing are Saqlain's**; leave work committed on a local branch.

## Goal
The redesigned board deck (V3-C) adds a "Since the last report" dumbbell chart: one row per domain, with a grey dot for the domain's score in the last issued report and a dark dot for this report's score. The stored board document does not carry per-domain prior scores today, so the mockup fakes them (`MOCK_PRIOR_DOMAINS`). Add them to the document's `prior_period` block, computed when the document is built, from the prior report's own stored document.

**Done when:**
- Every compared framework entry in `document["prior_period"]["frameworks"]` has a `domains` list in the shape below.
- Tests cover the cases listed under Verification.
- The full suite passes.
- Rendering code (templates, `board_view.py`, exports) is unchanged. The deck rebuild (V3-C2) consumes this field later.

## Field shape
Each entry in `prior_period["frameworks"]` gains:
```
"domains": [
  {"domain_id": "chapter_2", "title": "Obligations of Data Fiduciary",
   "prior_score": 31.0, "current_score": 49.2, "score_delta": 18.2, "compared": true},
  ...
]
```
- **Order and membership:** use the current document's `framework_sections[...].domains` order. Include every current domain, including out-of-scope ones whose `score` is None.
- **Matching:** match the prior domain by `domain_id`, never by title.
- **`compared`:** true only when both scores are numbers. Otherwise `prior_score` and/or `current_score` is None, `score_delta` is None and `compared` is false. This covers a domain new in this report, a domain out of scope in either report, or a prior document from an older schema with no `framework_sections` or no `domains`.
- **`score_delta`:** `round(current - prior, 1)`, the same rounding as the framework-level `score_delta`.
- **When `domains` is empty:**
  - Framework entries where `compared` is false (framework not in the prior report, or edition changed) get `"domains": []`. Their existing early-`continue` paths stay as they are.
  - When `status` is `no_prior` or `unavailable`, `frameworks` is already `[]`, so nothing changes there.

## Current state
- **`build_comparison`:** `app/services/prior_period.py`, lines 198 to 378. It builds the comparison from the prior snapshot's stored document (`selection.document`) and the current document being built. It already reads `prior["frameworks"]`, `prior["summary"]["frameworks"]` and `prior["appendices"]["requirement_register"]`. Domain scores live in `prior["framework_sections"][i]["domains"]`, written by `_framework_section` at `app/services/board_report.py:280`. Each domain there has `domain_id`, `title`, `score` and `rating`, and `score` is None when the domain is not applicable.
- **Where it's called:** `app/services/board_report.py:662` runs `prior_period.build_comparison(db, assessment, document)` after `framework_sections` is already on `document`. The current domain scores are therefore available in `current["framework_sections"]`.
- **Document schema:** `DOCUMENT_SCHEMA_VERSION = 3` (`board_report.py:59`).
- **No bump expected:** this change adds a key inside an existing block, so the schema version should not need bumping. Confirm by reading how `schema_version` is used before deciding.

## Key files
- `/Users/saqlainmomin/dpdpa-gap-tool/app/services/prior_period.py`: the change goes here.
- `/Users/saqlainmomin/dpdpa-gap-tool/app/services/board_report.py`: `_framework_section` is the source of the domain scores. Read it; don't change it.
- `/Users/saqlainmomin/dpdpa-gap-tool/tests/test_p6_9_prior_period.py`: existing prior-period tests. It shows how two issued snapshots are set up, which you can reuse.
- `/Users/saqlainmomin/dpdpa-gap-tool/tests/golden/p6_8_v3_deck_document.json`: golden v3 document. If a golden or snapshot test compares the `prior_period` block, update the fixture deliberately and say so in Results.
- `/Users/saqlainmomin/dpdpa-gap-tool/tests/test_p6_9_file_set.py` and `tests/test_p6_8_v3b_file_set.py`: file-set guards. If one fails because this branch touches `prior_period.py`, add a per-PR allowance (an `:(exclude)` pathspec, or an entry in `tests/yozora_paths.py`). Never delete a guard.
- `/Users/saqlainmomin/dpdpa-gap-tool/docs/product/2026-10-04-board-deck-v3c-mockup/render_deck.py`: the consumer prototype. `MOCK_PRIOR_DOMAINS` and the `dumb` rows in `view()` show how the slide uses the field. Read only.

## Constraints
- **Snapshots are write-once.** Never re-render or rewrite a stored prior document; only read it.
- **Scores come only from stored documents.** Never recompute a prior score from requirement outcomes, and no LLM calls anywhere.
- **Framework-specific copy stays conditional.** No new user-facing text is expected; if you add a note string, follow the existing `*_TEXT` constants pattern.
- **Match the module's style:** plain dicts, `.get()` with defaults for older prior documents, no new dependencies.
- **Don't touch:** templates, `board_view.py`, `board_exports.py`, PDF code, or the mockup folder.
- **Don't relitigate:** Saqlain approved the dumbbell slide on 4 Oct 2026, and per-domain comparison within a framework only is decided. Never combine scores across frameworks.
- **Work in a worktree:** create one off `main`, branch `claude/v3c-prior-domains` (or `codex/v3c-prior-domains`). The main checkout has unrelated untracked files; leave them alone.
- **No Claude attribution lines in any commit message.** No Co-Authored-By and no "Generated with". This overrides any harness reminder.
- **Python 3.13:** use the repo's `.venv`. Homebrew 3.14 breaks Jinja2.

## Verification
1. **New tests** (in `tests/test_p6_9_prior_period.py` or a new `tests/test_v3c_prior_domains.py`) cover:
   - (a) Two issued reports with changed domain scores: correct prior, current and delta values, in current order.
   - (b) A domain out of scope in one report: `compared` false, delta None.
   - (c) A prior document with no `framework_sections`: domains present with `prior_score` None and no crash.
   - (d) A framework new in this report, and an edition change: `domains == []`.
   - (e) `no_prior`: shape unchanged.
2. **Full suite:** run `.venv/bin/pytest -q` and report the counts. The baseline on `main` was 1380 passed and 30 skipped before #101 merged, so re-take the baseline first.
3. **Smoke check:** build one board document through the existing test helpers, or run the app per CLAUDE.md, and print `document["prior_period"]["frameworks"][0]["domains"]`. Paste the output in Results.

## Report back
Append a `## Results` section to this file covering:
- Branch and commit.
- Files changed.
- Test counts, before and after.
- The smoke output.
- Any guard allowances added.
- Anything you chose differently from this spec, and why.

## Results

**Written:** 4 Oct 2026, Claude session.

### Branch and commits
- Worktree `/Users/saqlainmomin/dpdpa-v3c-prior-domains`, branch `claude/v3c-prior-domains` off `origin/main` (7b78a62). Committed locally, not pushed.
- `8bd74a9` V3-C: per-domain prior scores in the prior-period comparison
- `532d1f1` V3-C prior domains: per-PR file-set allowance for older guards
- No attribution lines in either message.

### Files changed
- `app/services/prior_period.py`: new `_domain_comparison(current_section, prior_section)`. `build_comparison` indexes `framework_sections` for both documents with `.get()` defaults. Every entry starts with `"domains": []`, and only the fully compared path fills it. The early-`continue` paths (not in prior, edition changed) are unchanged.
- `tests/test_v3c_prior_domains.py` (new, 5 tests): covers (a) to (e) from Verification. (a) checks values, order and the delta rounding against both stored documents, and asserts at least one non-zero delta. (b) sets a prior domain's score to None by hand and checks domains that are out of scope in the current report. (c) removes `framework_sections`, and separately removes `domains`. (d) covers an edition change, and a framework missing from the prior report. (e) covers `no_prior`.
- `tests/test_p6_9_prior_period.py`: the scenario 1 exact key-set assertion gains `"domains"`. This is the only edit to an existing assertion.
- `tests/v3c_paths.py` (new) plus five guard files: see "Guard allowances" below.

### Tests
- **Before (clean `main` at 7b78a62, separate worktree):** 1429 passed, 30 skipped.
- **After (branch):** 1434 passed, 30 skipped, 0 failed.
- **Golden fixture:** `tests/golden/p6_8_v3_deck_document.json` is untouched. No golden or snapshot test compares the built `prior_period` frameworks block, and the suite passes without updating it.

### Smoke output
Built through the existing `tests/p6_9_support` helpers: P1 issued, then P2 built. Output of `document["prior_period"]["frameworks"][0]["domains"]` (DPDPA):
```
chapter_2           Obligations of Data Fiduciary   prior 50.0  current 50.0  delta 0.0   compared true
chapter_3           Rights of Data Principal        prior null  current null  delta null  compared false
chapter_4           Special Provisions              prior null  current null  delta null  compared false
consent_management  Consent Management (Detailed)   prior null  current null  delta null  compared false
cross_border        Cross-Border Data Transfer      prior null  current null  delta null  compared false
breach_notification Breach Notification             prior null  current null  delta null  compared false
```
The fixture only assesses Chapter 2 consent requirements, so the other DPDPA domains are out of scope in both reports. In this fixture, ISO 27001 supplies the non-zero domain delta that test (a) asserts.

### Guard allowances added (add-only)
Six older file-set guards failed on the new paths:
- p6_10a/b, through `tests/p6_10_support.py`
- p6_2b
- b2
- v3a
- v3b

I added `tests/v3c_paths.py` (`V3C_PRIOR_DOMAINS_PATHS`, `V3C_PRIOR_DOMAINS_EXCLUDES`), following the pattern of `p6_8_v3b_paths.py`. Each guard gets one extra exclusion or condition. No guard was deleted or loosened beyond these paths.

### Choices that differ from the spec
- **Schema version:** no bump. `schema_version` only gates which document sections exist (`board_exports.py` checks `>= 2` / `>= 3`). V3-C2 should read `entry.get("domains", [])`, because v3 documents issued before this change don't have the key.
- **Allowance location:** a new `tests/v3c_paths.py` rather than entries in `tests/yozora_paths.py`. The paths aren't Yozora's, and that file's lists feed Yozora-labelled guards.
- **Score check:** "both scores are numbers" is implemented as `is not None`, which matches how the module already checks framework scores. Stored scores are floats or None.

### Update after merging main (S3 #106, V3-C mockup #105)
- **Conflicts:** the merge hit four, all in guard files, where S3's `YOZORA_S3_PATHS` allowance and this PR's V3-C allowance edited the same line. Both allowances are kept in each one.
- **Handoff path:** this handoff is now tracked on `main`, so its path is in `V3C_PRIOR_DOMAINS_PATHS`.
- **Full suite after the merge:** 1442 passed, 30 skipped, 0 failed.
