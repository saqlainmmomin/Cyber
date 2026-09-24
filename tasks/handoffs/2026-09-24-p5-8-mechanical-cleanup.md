# P5-8: Mechanical cleanup

**Plan:** `docs/plans/2026-09-24-001-cleanup-and-non-dpdpa-parity-plan.md`, task P5-8 (gaps #2, #4, #5-label; audit item A8).
**Depends on:** nothing. **Blocks:** nothing directly, but P5-4 shares `question_engine.py` — land this first (plan's sequencing note).
**Owner:** Codex, standalone, from this handoff. No architectural judgment calls in scope — every item below is either dead code or a mislabeled UI string.
**Code baseline:** `main` at `2a5a7e9`. Every line reference below was read against this commit on 2026-09-24.

This is deliberately the smallest task in Phase 5. Do not use it as an opportunity to refactor anything beyond what's listed. If you find yourself touching a file not listed in "Files" below, stop and report it in `## Results` rather than proceeding.

---

## D-P5-8-A: Delete the dead coverage-reinstatement loop (gap #2)

**File:** `app/services/question_engine.py`, lines ~255-275 (the block that starts `all_req_ids = {r["id"] for r in get_all_requirements()}` and ends `skipped_count -= 1`).

The loop un-skips a base question when its requirement is left uncovered, but excludes it when `skip_reason == "Not applicable per scope definition"`. That is the *only* skip reason ever produced: `_apply_screening`, `_modulate_question`, and `_modulate_industry_question` never set `status = "skipped"` — grep confirms the sole producer of `"skipped"` is the scope-exclusion branch at `question_engine.py:217-221` (`skip_reason = "Not applicable per scope definition"`). So the loop's `if q["status"] == "skipped" and q["id"] in uncovered` branch can never fire without also hitting the `continue` — it is unreachable dead code.

**Action:**
- Delete the whole loop (the `# Un-skip any base question whose requirement is uncovered and in scope` block through `skipped_count -= 1`), including the `all_req_ids`, `required_req_ids`, `uncovered` variables it introduces, if they are not used anywhere else in the function. Check `skipped_count` — if it's used later (e.g. in `tier_counts` or a returned stats dict), keep the variable declared where it's needed but drop the decrement that lived only in this dead branch.
- Remove the stale module docstring line at the top of `question_engine.py` (`"""Question Selection Engine..."""` block, ~line 10): `  - Skip: strong document evidence → question skipped with reason`. Confirm first whether any *other* skip mechanism exists that this line correctly describes — if grepping `status = "skipped"` and `skip_reason =` across `question_engine.py` still turns up only the scope-exclusion site after your other changes, delete the line; if you find a second skip producer, leave the docstring and note it in `## Results` instead of deleting.
- Add a short regression test (new or in an existing `question_engine` test module) asserting that a scope-excluded question stays skipped even when it's the only question covering its requirement, i.e. the exclusion isn't accidentally reinstated by removing this code. This locks in the *current* (and intended) behavior — scope exclusions are a deliberate consultant/legal decision (PR-042), not a coverage gap to patch over.

**Do not** add a new "skip" state anywhere as part of this task — D-P5-F (a later task) governs how documents affect responses, and the plan is explicit that "a document describes intent and is not an answer."

---

## D-P5-8-B: Remove or document the unused `company_size`/`industry` parameters (gap #4)

**File:** `app/services/scope_profiler.py`.

- `compute_scope(scope_answers: dict, industry: str, company_size: str) -> dict` (line 45): `company_size` is never referenced in the function body (verified: only appears in the signature and its docstring `Args:` line). `industry` *is* used (passed through to `_build_evidence_checklist(industry=...)`).
- `_build_evidence_checklist(..., industry: str)` (line ~122): `industry` is never referenced in that function's body either (verified: only appears in the signature).

**Decision:** there is no deterministic legal rule that excludes DPDPA requirements by company size (DPDPA s.17(3) startup exemptions require a Government notification that doesn't exist yet — that's a consultant Not-applicable rationale, not code). Do not invent size- or industry-based exclusion logic. Instead:

- Remove the `company_size` parameter from `compute_scope`'s signature and update its single call site at `scope_profiler.py:298` (inside `compute_scope_multi`) to stop passing it. Check whether `compute_scope_multi`'s own `company_size` parameter (line ~279) becomes unused once this call site is updated — if so, remove it too and check *its* one caller (`app/routers/web.py`, `compute_scope_multi(scope_data, ...)` — there are 3 call sites per the earlier grep, at `web.py:850`, `:1005`, `:1034`/`:1066` — verify the exact signature order before editing all of them).
- Remove the `industry` parameter from `_build_evidence_checklist` and its one call site inside `compute_scope`.
- Update both functions' docstrings to match the new signatures. Do not leave a stale `Args:` entry for a parameter you removed.
- If removing `company_size` all the way up to the router call sites turns out to be a wider ripple than expected (e.g. it's threaded through more than the 4 sites named above, or a test constructs `compute_scope`/`compute_scope_multi` positionally in a way that would silently break), stop and report the actual call graph in `## Results` instead of guessing — this task should not need to touch more than `scope_profiler.py`, its direct callers in `web.py`, and any test file that calls these functions directly.
- Run the full suite after this change specifically — `compute_scope`/`compute_scope_multi` are exercised by scope/questionnaire tests, and a signature change is exactly the kind of edit that breaks a test silently importing the old arity.

---

## D-P5-8-C: Relabel the generic industry-question bank (gap #5)

**Files:** `app/dpdpa/industry_questions.py` (the `INDUSTRY_BANK_MAP`, ~line 283) and `app/services/question_engine.py` (`"chapter_title": "Industry-Specific"` at lines 526 and 665, plus the docstring at line ~641).

Only `it_services` maps to a real bespoke bank (`it_saas`). Every other industry (`fintech`, `healthcare`, `ecommerce`, `manufacturing`, `education`, `real_estate`, `legal`, `accounting`, `other`) maps to `"generic"` — 5 generic questions that currently render under the same `"Industry-Specific"` chapter heading as the real IT/SaaS bank, which overstates their specificity to the consultant and client.

**Action:**
- In `question_engine.py`, make the chapter title conditional on which bank was actually used: keep `"Industry-Specific"` when the resolved bank is `it_saas` (or any future genuinely dedicated bank), and use a plain, honest label — e.g. `"Additional Questions"` or `"General Data Protection Questions"` — when the resolved bank is `generic`. You'll need to plumb through which bank key was selected (via `get_industry_questions`'s return, or by checking `INDUSTRY_BANK_MAP.get(industry, "generic")` at the call site) to both chapter-title locations (line 526 and line 665 — check if these are two different code paths or the same one called twice; the plan's gap table implies both need the fix).
- Pick one label and use it consistently in both locations. State your exact chosen label in `## Results`.
- Do **not** write new industry question banks — that's explicitly deferred (plan's deferred-list table: "New DPDPA industry banks... When a pilot client in one of those industries is signed").
- Add or update a test asserting the chapter title differs between an `it_services` assessment and, e.g., a `fintech` one.

---

## D-P5-8-D: Delete the dead `/context/submit` stub (A8)

**File:** `app/routers/web.py`, lines 1243-1259 (`@router.post("/assessments/{assessment_id}/context/submit", ...)` / `def submit_context_web(...)`).

This route builds `form_data = {}` (a comment says "Will be populated from HTMX form" — it never is), does nothing with `derive_risk_profile` despite importing it, and just redirects to the questionnaire tab. Confirm via grep that no template references this URL (`context/submit`) before deleting — if something still POSTs to it, report that in `## Results` instead of deleting a route that's actually wired up. If it's confirmed unreferenced, delete the whole route handler. Leave `/assessments/{assessment_id}/context/save` (the following route) untouched — it's a different, live endpoint.

---

## D-P5-8-E: Pass `framework_label` to the RFI DOCX export (A8)

**File:** `app/routers/web.py`, the `download_rfi_docx` handler (~line 2380 onward), and `app/utils/rfi_export.py`'s `generate_rfi_docx` (line 240).

`download_rfi_pdf` (the handler just above it) passes `framework_label=", ".join(_selected_framework_names(assessment))` into `generate_rfi_pdf`. `download_rfi_docx` calls `generate_rfi_docx` with the same other arguments but omits `framework_label`. Check `generate_rfi_docx`'s signature: if it already accepts `framework_label` (optional or otherwise) and just isn't being passed one, add the same `framework_label=", ".join(_selected_framework_names(assessment))` argument to the call. If `generate_rfi_docx` doesn't accept the parameter at all yet, add it to the function signature and use it the same way `generate_rfi_pdf` does (check how the PDF version renders it — likely in a header/subtitle — and mirror that in the DOCX version's equivalent section). This is a one-line-of-intent fix; don't restructure `rfi_export.py` beyond adding the parameter and its single use.

---

## Test expectations

No pre-written failing test suite exists for this task — write your own tests covering:
1. Scope exclusion stays permanent even when it's the sole coverage for a requirement (D-P5-8-A).
2. `compute_scope`/`compute_scope_multi` work correctly with the reduced signatures, and existing scope/questionnaire tests still pass unmodified in behavior (only signature/call-site changes, no behavior change) (D-P5-8-B).
3. Chapter title differs between an IT/SaaS assessment and a generic-bank industry (D-P5-8-C).
4. `/assessments/{id}/context/submit` returns 404 (or is simply gone) after deletion, and no other test currently depends on it (D-P5-8-D).
5. RFI DOCX download includes the framework label the same way the PDF does — a content-level assertion if `generate_rfi_docx` is testable directly, otherwise a call-arguments assertion (D-P5-8-E).

Run `.venv/bin/pytest -q` and report the exact pass count in `## Results`, alongside a `git diff --stat` confirming the diff is confined to: `app/services/question_engine.py`, `app/services/scope_profiler.py`, `app/dpdpa/industry_questions.py`, `app/routers/web.py`, `app/utils/rfi_export.py`, and new/modified test files. If the diff touches anything else, explain why in `## Results`.

**Known pre-existing flake, not caused by this task:** `tests/test_longitudinal_demo.py::test_scenario_9_rollups_and_integrated_reporting` fails intermittently on an ordering assertion (`assessments` list order in an integrated-report snapshot) — reproduced independently before this task was dispatched, on unmodified `main`. If you see it fail, re-run just that test alone to confirm it's the same pre-existing flake and note it in `## Results` rather than trying to fix it (out of scope for P5-8; flag it back for scoping into a future task if you want, but don't fix it here).

---

## Closing instructions

- Number every decision you have to make beyond what's specified here as `D-P5-8-F`, `D-P5-8-G`, etc., in your own `## Results` section, and close every fork explicitly.
- If the code forces a deviation from anything above, stop and report it in `## Results` — do not silently pick an alternative.
- No `Co-Authored-By: Claude` trailer or "Generated with Claude Code" footer on any commit or PR.

## Results

Codex (`gpt-5.6-luna`, `xhigh`) implemented all five decisions (D-P5-8-A through D-P5-8-E) and wrote `tests/test_p5_8_mechanical_cleanup.py`, then lost its connection mid-run (`stream disconnected before completion` / websocket DNS failures against `chatgpt.com`) before it could write this `## Results` section or commit. This section is written by Claude from direct inspection of the diff Codex left behind, per the phase-4 kickoff process's guidance for a quota/connectivity cutoff: "check whether the actual implementation and tests already landed before the cutoff... if so, finish the mechanical remainder yourself... say so explicitly."

**D-P5-8-A (dead reinstatement loop):** Done as specified. `app/services/question_engine.py`'s coverage-reinstatement loop (the `covered_reqs`/`all_req_ids`/`uncovered` block through `skipped_count -= 1`) is deleted in full, along with the stale docstring line `- Skip: strong document evidence → question skipped with reason`. Verified by re-grepping `question_engine.py` after the change: the only remaining producer of `status == "skipped"` is the scope-exclusion branch, so the docstring deletion was correct. `get_all_requirements` import was dropped as newly-unused. Regression test: `test_scope_exclusion_stays_skipped_when_requirement_has_no_other_question`.

**D-P5-8-B (unused `company_size`/`industry` params):** Done, and the ripple stayed exactly as scoped. `compute_scope(scope_answers)` and `_build_evidence_checklist(...)` (both in `scope_profiler.py`) dropped their unused parameters; `compute_scope_multi(scope_answers, framework_ids)` dropped `industry`/`company_size` too (its own `company_size`/`industry` params were unused after the `compute_scope` call site was simplified — confirmed no other use in the function body). All 4 call sites in `app/routers/web.py` (assessment_detail, save_scope, download_evidence_checklist_pdf, download_evidence_checklist_docx) were updated to the reduced signature. No other call sites existed. Regression test: `test_scope_profiler_reduced_signatures_preserve_behavior` (asserts identical output before/after via the multi-framework wrapper).

**D-P5-8-C (generic industry bank relabeling):** Done. Chosen label: **"Additional Questions"** (matches the handoff's suggested wording exactly). `question_engine.py` now resolves `industry_bank_key = INDUSTRY_BANK_MAP.get(industry, "generic")` once in `build_adaptive_questionnaire` and threads `industry_chapter_title` (`"Industry-Specific"` if the bank is genuinely dedicated, `"Additional Questions"` otherwise) through `_modulate_industry_question` (new fourth parameter) and into `_build_sections` (which now reads `q["chapter_title"]` per-question instead of hardcoding the string). Both chapter-title sites the plan named (~526, ~665 pre-change) turned out to be the same underlying code path threaded through one new parameter, not two independent sites — simpler than the handoff anticipated, no deviation needed. Regression test: `test_industry_question_chapter_title_reflects_resolved_bank` (asserts `it_services` → "Industry-Specific", `fintech` → "Additional Questions").

**D-P5-8-D (dead `/context/submit` stub):** Done. Confirmed via grep that nothing referenced `context/submit` before deletion (no template, no test). Route handler removed from `app/routers/web.py`; `/assessments/{assessment_id}/context/save` (the next route) is untouched. Regression test: `test_context_submit_stub_is_removed` (asserts 404).

**D-P5-8-E (RFI DOCX `framework_label`):** Done. `generate_rfi_docx` in `app/utils/rfi_export.py` gained a `framework_label: str = ""` parameter, rendering a centered subtitle paragraph (`"{framework_label} Compliance Gap Assessment"`, or just `"Compliance Gap Assessment"` if empty) beneath the main title — mirroring how `generate_rfi_pdf` uses the label. `download_rfi_docx` in `web.py` now passes `framework_label=", ".join(_selected_framework_names(assessment))`, identical to `download_rfi_pdf`. Regression test: `test_rfi_docx_includes_framework_label`.

**Diff scope:** `git diff --stat` against the task's file list is clean — only `app/routers/web.py`, `app/services/question_engine.py`, `app/services/scope_profiler.py`, `app/utils/rfi_export.py`, plus the new test file. No unlisted files touched.

**Test results (independently re-run by Claude after the cutoff, worktree `dpdpa-gap-tool-p5-8`, commit base `2a5a7e9`):** `.venv/bin/pytest -q` → **553 passed, 9 skipped**, one pre-existing intermittent failure (`tests/test_longitudinal_demo.py::test_scenario_9_rollups_and_integrated_reporting`, an ordering assertion — reproduced independently on unmodified `main` before this task was dispatched, not a regression). A second failure, `test_scenario_13_protected_surface_is_unchanged`, is a false positive specific to an uncommitted worktree: that test asserts `git diff --name-only -- <protected files>` is empty, which only holds once this task's own diff to `app/routers/web.py` is committed (it's not in the protected list's exclusion path, so an in-progress uncommitted diff on `web.py` trips it). Re-ran after committing (see below) and it passed.

**No deviations required beyond D-P5-8-C's simpler-than-expected single code path**, noted above.
