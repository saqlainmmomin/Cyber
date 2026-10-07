# Flow rework S0a: retire the file-path guard tests (Codex)

Owner: Codex (builder). Orchestrator: Claude. Written 2026-10-07.
Plan: `docs/plans/2026-10-07-001-flow-rework-plan.md`, decision P6 ("which tests get retired") and slice S0.

## Goal
Delete every test check that runs `git diff` / `git ls-files` / `git status` to fail a branch for touching files outside a frozen allow-list, and delete `tests/yozora_paths.py`. Keep every real behaviour assertion in the same files.

## Files in scope
These files reference `git diff` or `yozora_paths` today (re-grep to confirm: `grep -ln 'git", "diff"\|"diff", "--name-only"\|yozora_paths\|ls-files' tests/*.py`):
`tests/p6_10_support.py`, `tests/test_longitudinal_demo.py`, `tests/test_p5_2_reader_migration.py`, `tests/test_p5_6_rfi_rebuild.py`, `tests/test_p5_4_adaptive_ucc_questionnaire.py`, `tests/test_p6_0c_dev_hygiene.py`, `tests/test_p5_3_framework_desk_review.py`, `tests/test_p6_1b_framework_batching.py`, `tests/test_p6_1_llm_plumbing.py`, `tests/test_p6_2b_dpdpa_criteria.py`, `tests/test_p6_3a_grounding.py`, `tests/test_p6_4_cap_upload_limit.py`, `tests/test_p6_4_whats_missing.py`, `tests/test_p6_6_report_foundations.py`, `tests/test_p6_7b_add_to_rfi.py`, `tests/test_p6_8_board_report_v2.py`, `tests/test_p6_8_b2_docx_xlsx.py`, `tests/test_p6_7_requirement_card.py`, `tests/test_p6_8_v3a_data_capture.py`, `tests/test_p6_8_v3b_file_set.py`, `tests/test_p6_9_file_set.py`, `tests/test_p6_nist_csf2_alignment.py`, `tests/test_retention.py`, `tests/test_validation_harness.py`, `tests/yozora_paths.py`.

## Rules
1. **Delete:** any assertion whose only purpose is "the branch's changed files (from `git diff main...HEAD`, `git diff HEAD`, `git ls-files --others`) are inside / outside a path list". Delete the path-list constants, `_git` helpers and imports that become unused. Delete `tests/yozora_paths.py`.
2. **Keep:** every assertion about app behaviour (routes, rendered content, scoring, no LLM call, retention/purge, file content of app modules, etc.). If one test function mixes a path check with a behaviour check (e.g. `test_scenario_1_no_llm_and_p6_9_file_set` in `test_p6_9_file_set.py`), keep the function, remove only the path part, and rename it if the name now lies.
3. A test that reads a *file's content* (e.g. "this template contains X", "this module does not import Y") is a behaviour/content check, not a path guard. Keep it.
4. If a whole test file becomes empty, delete the file. If `tests/p6_10_support.py` still has helpers used by other tests, keep those helpers.
5. **Never touch:** `tests/test_answer_key_isolation.py`, `tests/test_remaining_llm_call_sites.py`, anything under `app/`, `scripts/`, `validation/`. Do not change any non-test file except this handoff's Results section.
6. Do not add any new test.
7. Pixel-gate / design-preview tests are not path guards; leave them alone.

## Verification
- `grep -rn '"diff", "--name-only"\|git diff\|yozora_paths' tests/` returns nothing that is a path guard (docstrings/comments removed too).
- `.venv/bin/pytest -q -p no:cacheprovider` green. Baseline before this change: 1594 passed, 30 skipped. The pass count drops only by the deleted guard tests; report the before/after counts and list each deleted test function.

## Git
Commit on this branch (`codex/flow-s0a-retire-guards`) with a plain message. **No `Co-Authored-By` or any AI attribution lines.** Do not push.

## Results
Deleted files:

- `tests/yozora_paths.py`
- `tests/test_p6_8_v3b_file_set.py`

Deleted test functions:

- `tests/test_longitudinal_demo.py::test_scenario_13_protected_surface_is_unchanged`
- `tests/test_p6_10a_remediation_draft.py::test_scenario_9_p6_10_file_set_and_llm_call_sites`
- `tests/test_p6_10b_narrative.py::test_scenario_10_p6_10_file_set_and_llm_call_sites`
- `tests/test_p6_1b_framework_batching.py::test_protected_surface_guard_uses_three_dot_diff`
- `tests/test_p6_2b_dpdpa_criteria.py::test_scenario_11_only_p6_2b_files_change`
- `tests/test_p6_3a_grounding.py::test_scenario_17_protected_files_unchanged`
- `tests/test_p6_4_cap_upload_limit.py::test_scenario_9_only_config_and_document_processor_change_under_app`
- `tests/test_p6_4_whats_missing.py::test_scenario_13_application_files_are_limited_and_disjoint_from_p6_4_cap`
- `tests/test_p6_6_report_foundations.py::test_scenario_17_p6_6_shares_no_files_with_p6_4`
- `tests/test_p6_7_requirement_card.py::test_scenario_14_p6_7_touches_only_its_files`
- `tests/test_p6_7b_add_to_rfi.py::test_scenario_12_p6_7b_touches_only_its_files`
- `tests/test_p6_nist_csf2_alignment.py::test_protected_surface_guard_uses_three_dot_diff`
- `tests/test_p6_8_v3b_file_set.py::test_v3b_changes_stay_in_the_v3b_file_set`
- `tests/test_retention.py::test_scenario_13_only_new_retention_test_file_changes`
- `tests/test_validation_harness.py::test_app_files_are_untouched_by_harness`

Kept and trimmed:

- `test_scenario_19_source_and_migration_guards`, `test_scenario_12_public_signatures_and_model_constraints`, `test_scenario_7_tiering_matches_engine`, `test_scenario_13_structure_and_provenance_guards`, `test_scenario_22_source_schema_signature_and_migration_guards`, `test_llm_client_collects_calls_and_preserves_signature`, `test_scenario_13_grounding_prompt_versions_remain_pinned`, `test_scenario_14_no_llm_imports`, `test_scenario_10_no_llm_no_live_readers`, `test_scenario_12_v3a_is_offline_and_preserves_schema`, and `test_scenario_1_new_modules_have_no_llm_imports` remain with their path assertions removed.
- The shared P6-10 fixtures remain; only the two P6-10 file-set caller tests and their path-list helper were removed.
- The P6-0c meta-test remains, renamed to `test_guard_meta_test_rejects_stale_venv_and_baseline_invocations`.

Verification:

- Before: 1,594 passed, 30 skipped.
- After: 1,580 passed, 29 skipped, 505 warnings.
- `.venv/bin/pytest -q -p no:cacheprovider` passed.
- `python -m compileall -q tests` passed.
- The remaining `git diff` references are source-content comparisons or the P6-0c planted-pattern meta-test; no path allow-list guard remains.

### Orchestrator fix pass (after review)
- Restored the source-content check that every `app/` module calling `call_llm` is registered, as `tests/test_p6_10a_remediation_draft.py::test_every_module_calling_the_llm_is_registered` (it was lost with the P6-10 file-set tests).
- Retired three frozen-file guards the first grep missed (spelled `"git", "diff"` / `_git("diff"...)`): the `dpdpa.py`/`schema.py` diff blocks in `test_p5_3_framework_desk_review.py::test_scenario_12_*`, `test_p6_3b_v2_flag.py::test_scenario_2_desk_review_v1_lines_are_only_added_to` plus the diff part of its scenario 11, and both `test_p6_4_v2_judge.py::test_scenario_16_*` guards (the `PROMPT_VERSION` pin stays as `test_scenario_16_grounding_prompt_version_pinned`). They would block S0b (`scoring.py`) and S3.
- Removed orphans: the unused `subprocess` imports and `_git`/`git` helpers, and the dead allowance modules `tests/p6_8_v3a_paths.py`, `p6_8_v3b_paths.py`, `v3c_paths.py`, `v3c3_paths.py`, `yozora_backend_paths.py`.
- Left on purpose: `tests/test_p6_nist_csf2_alignment.py` compares NIST definitions/clusters with the merge-base copy. That is tangled with real content checks. S3/S9 must update it when they change NIST scope or definitions.
