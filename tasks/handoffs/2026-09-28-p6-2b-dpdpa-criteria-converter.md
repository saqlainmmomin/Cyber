# P6-2b: DPDPA criteria converter (design handoff)

## Goal

Convert the signed-off DPDPA test-criteria review sheet
(`tasks/criteria-review/signed/dpdpa-criteria-v1.csv`) into pack code, so
DPDPA `Control`s carry real `test_criteria` and the v2 judge (`judge.criteria_for`)
starts returning `criteria_source="approved"` for DPDPA instead of `"fallback"`.
v1 (`claude_analyzer.py`) is untouched. Other frameworks (ISO/GDPR/HIPAA/NIST/PCI)
are not part of this PR and stay on fallback criteria.

## Decisions (D-P6-2b-A..G)

- **A.** The signed sheet is committed verbatim at
  `tasks/criteria-review/signed/dpdpa-criteria-v1.csv` — the record of
  sign-off. It is 150 rows, all `decision=approve`, no edits, sha256
  `228df4d572b42aefdd9638017a6a84210802717c2ce400ed2cb172fb2e850a75`. **Never
  modify it.** The unsigned `tasks/criteria-review/dpdpa-criteria-v1.csv`
  stays as-is (the P6-2a draft-export test still checks it).
- **B.** New `scripts/convert_criteria.py`:
  - `main(argv)`: `--framework dpdpa` (only `dpdpa` supported now; any other
    value → `SystemExit` with a clear message), `--sheet` (default the signed
    path), `--out` (default `app/frameworks/criteria/dpdpa.py`), `--check`
    (regenerate in memory, exit non-zero if it differs from the committed
    module).
  - Also expose: `load_sheet(path) -> list[dict]`,
    `approved_criteria(rows, framework) -> dict[str, tuple[TestCriterion, ...]]`,
    `render_module(criteria, *, sheet_sha256, criteria_version) -> str`.
  - Output is deterministic (byte-identical across runs), in pack control
    order, and the generated module's header says it is generated, names the
    sheet path and its sha256, and says not to edit by hand.
  - Decision rules: `approve` → `statement`; `edit` → `edited_statement`
    (empty ⇒ error); `reject` → dropped; any other/blank decision ⇒ error
    ("sheet not fully signed", naming the criterion_id). A requirement whose
    criteria are all rejected gets no dict entry (stays on fallback).
    `evidence_hint`, `source_basis`, `kind` carry into `TestCriterion`;
    `reviewer_note`, `in_force_note`, `drafter_confidence`,
    `requirement_title` do not. Validation errors (`ValueError`, `main` exits
    non-zero): unknown `requirement_id` (not a pack control id), `criterion_id`
    not `<requirement_id>.TC<n>`, duplicate `criterion_id`, `kind` not in
    `{design, operating}`, empty `statement`, missing/extra columns vs
    `export_criteria_review.COLUMNS`, `criticality` differing from the pack
    control's. **Title mismatches are ignored** — 15 requirements'
    `requirement_title` differs from the pack title; that's expected and not
    an error.
- **C.** Generated `app/frameworks/criteria/dpdpa.py` exports
  `DPDPA_CRITERIA: dict[str, tuple[TestCriterion, ...]]`,
  `DPDPA_CRITERIA_VERSION = "criteria-v1"`,
  `DPDPA_CRITERIA_SHEET_SHA256 = "<hex>"`. Must not import `dpdpa_draft`.
- **D.** `app/frameworks/definitions/dpdpa.py` attaches
  `test_criteria=DPDPA_CRITERIA.get(req["id"], ())` to every `Control`. All 41
  DPDPA controls get approved criteria (150 total, confirmed from the signed
  sheet).
- **E (pack version, D-P6-D).** Add `criteria_version: str = ""` to
  `FrameworkDefinition` (`app/frameworks/schema.py`) and a `pack_version`
  property = `version` if no `criteria_version` else
  `f"{version}+{criteria_version}"`. DPDPA sets
  `criteria_version=DPDPA_CRITERIA_VERSION` → `pack_version` =
  `"2023+criteria-v1"`; `version` stays `"2023"` (display sites unchanged).
  Switch these three call sites to `.pack_version`:
  - `app/services/engagement_factory.py:49` (`AssessmentPack(... pack_version=framework.version ...)`)
  - `app/services/grounding/pipeline.py:755` (`empty_claim_set()`'s `pack_versions={...: .version}`)
  - `app/services/grounding/pipeline.py:928` (the normal-path `pack_versions={...}`)

  Consequence (intended): an existing DPDPA claim set built under `"2023"` is
  now stale and gets refused/regenerated. Other frameworks' `pack_version ==
  version`, unchanged.

  **`claims.py` too (orchestrator decision):** `claim_set_is_current` in
  `app/services/grounding/claims.py` (~line 213) builds its comparison dict
  from `.version`. Switch it to `.pack_version` as well, or every DPDPA
  claim set built after this change would compare as stale forever.
  `claims.py` is in the allowed-file set; scenario 7b checks that a fresh
  claim set is current and a `"2023"` one is stale.
- **F.** v1 untouched: `app/services/claude_analyzer.py` must not reference
  `test_criteria` (contract test asserts this).
- **G.** `tests/test_p6_2a_test_criteria.py::test_unmodified_control_has_no_criteria_and_registry_loads`
  is already updated in this handoff's tests (the one legitimate edit to an
  existing test): DPDPA controls must carry exactly `DPDPA_CRITERIA`; the
  other five frameworks still carry no criteria. Do not re-edit it.
  `app/frameworks/criteria/__init__.py`'s docstring is stale after this PR
  ("criteria reach a `Control` only via the P6-2b converter, after Saqlain
  signs off") — leaving it as-is is fine; it's still true, just no longer
  forward-looking. Not required to touch.

## Touched files (only these; scope guard enforces it)

- `tasks/criteria-review/signed/dpdpa-criteria-v1.csv` (already committed to
  the working tree, untracked — just don't modify it)
- `scripts/convert_criteria.py` (new)
- `app/frameworks/criteria/dpdpa.py` (new, generated — run the script, don't
  hand-write it)
- `app/frameworks/criteria/__init__.py` (only if you choose to touch the
  docstring; not required)
- `app/frameworks/definitions/dpdpa.py`
- `app/frameworks/schema.py`
- `app/services/engagement_factory.py`
- `app/services/grounding/pipeline.py`
- `app/services/grounding/claims.py`
- `tests/test_p6_2a_test_criteria.py` (already edited — don't re-edit)
- `tests/test_p6_2b_dpdpa_criteria.py` (already written — don't edit)
- `tasks/handoffs/2026-09-28-p6-2b-dpdpa-criteria-converter.md` (this file —
  fill in `## Results`)
- `tasks/todo.md` (update status when done)

## Stale guards needing `:(exclude)` lines for P6-2b's files

Found by grepping `tests/` for `main...HEAD` and checking each guard's path
list against the files above. **Do not delete any existing guard line — only
add new `:(exclude)` entries for the specific P6-2b paths that would
otherwise trip it.** Verified against the current tree (all pass today,
before P6-2b's app changes land):

1. `tests/test_p6_nist_csf2_alignment.py::test_protected_surface_guard_uses_three_dot_diff`
   (includes `app/services` broadly, `app/frameworks/schema.py` directly,
   `app/frameworks/definitions` excluding only `nist_csf.py`) — needs:
   - `:(exclude)app/services/engagement_factory.py`
   - `:(exclude)app/frameworks/schema.py`
   - `:(exclude)app/frameworks/definitions/dpdpa.py`
   (`app/services/grounding` is already wholesale excluded, so
   `pipeline.py` is fine.)
2. `tests/test_p6_3a_grounding.py::test_scenario_17_protected_files_unchanged`
   (`PROTECTED_PATHS` includes all of `app/frameworks`) — needs:
   - `:(exclude)app/frameworks/schema.py`
   - `:(exclude)app/frameworks/definitions/dpdpa.py`
   - `:(exclude)app/frameworks/criteria/dpdpa.py`
   - `:(exclude)app/frameworks/criteria/__init__.py` (only if you touch it)
3. `tests/test_p6_6_report_foundations.py::test_scenario_17_p6_6_shares_no_files_with_p6_4`
   (`P6_4_AND_PROTECTED_PATHS` includes all of `app/frameworks` and all of
   `scripts`) — needs:
   - `:(exclude)app/frameworks/schema.py`
   - `:(exclude)app/frameworks/definitions/dpdpa.py`
   - `:(exclude)app/frameworks/criteria/dpdpa.py`
   - `:(exclude)app/frameworks/criteria/__init__.py` (only if you touch it)
   - `:(exclude)scripts/convert_criteria.py`
4. `tests/test_p5_4_adaptive_ucc_questionnaire.py::test_scenario_13_structural_guards`
   (includes `app/frameworks` broadly) — needs:
   - `:(exclude)app/frameworks/schema.py`
   - `:(exclude)app/frameworks/definitions/dpdpa.py`
   - `:(exclude)app/frameworks/criteria/dpdpa.py`
   - `:(exclude)app/frameworks/criteria/__init__.py` (only if you touch it)
5. `tests/test_p6_1b_framework_batching.py::test_protected_surface_guard_uses_three_dot_diff`
   (includes `app/frameworks/schema.py` directly, `app/frameworks/definitions`
   excluding only `nist_csf.py`; does not include `app/frameworks/criteria`) — needs:
   - `:(exclude)app/frameworks/schema.py`
   - `:(exclude)app/frameworks/definitions/dpdpa.py`

Checked and **should not** need an exclude (verify anyway; assertions are
about additive-only diffs / specific tokens, not presence of any diff at all):
- `tests/test_p5_3_framework_desk_review.py::test_scenario_12_standing_guards_and_public_signatures`
  — the `app/frameworks/definitions` guard already excludes `dpdpa.py`. The
  `schema.py` guard only fails on *removed* lines (`git diff -U0`), and
  `schema.py`'s change here (new field + new property) is purely additive.
  The `dpdpa.py` guard only fails if a changed line contains `pattern=`,
  `id=`, `Control(`, or `weight` — adding
  `test_criteria=DPDPA_CRITERIA.get(req["id"], ())` and
  `criteria_version=DPDPA_CRITERIA_VERSION` as new lines doesn't contain any
  of those substrings, but double check after writing the actual diff.

Every other `main...HEAD` guard in `tests/` (test_p5_2, test_p5_6, test_p6_1)
was checked and doesn't touch any P6-2b path.

## Codex prompt (paste as-is)

```
You're implementing P6-2b: the DPDPA test-criteria converter, per
tasks/handoffs/2026-09-28-p6-2b-dpdpa-criteria-converter.md in this repo.
You have no network access and cannot write to .git.

Read the handoff in full first (decisions D-P6-2b-A through G), then:

1. Write scripts/convert_criteria.py per D-P6-2b-B: main(argv), load_sheet,
   approved_criteria, render_module. Read tasks/criteria-review/signed/
   dpdpa-criteria-v1.csv (never modify it) and app/dpdpa/framework.py's
   get_all_requirements() (or the DPDPA_DEFINITION) for the pack's
   requirement ids/titles/criticality to validate against.
2. Run it to generate app/frameworks/criteria/dpdpa.py (D-P6-2b-C). Don't
   hand-write this file — always regenerate it by running the script, and
   re-run after any script change.
3. Edit app/frameworks/definitions/dpdpa.py per D-P6-2b-D (attach
   test_criteria to each Control).
4. Edit app/frameworks/schema.py per D-P6-2b-E (criteria_version field +
   pack_version property on FrameworkDefinition), and switch the three call
   sites listed there, plus the comparison in
   app/services/grounding/claims.py claim_set_is_current, to .pack_version.
5. Do NOT edit tests/test_p6_2a_test_criteria.py or
   tests/test_p6_2b_dpdpa_criteria.py. Make them pass by writing the
   implementation, not the tests. If a test assertion looks wrong, stop and
   report it in this handoff's Results section instead of changing it.
6. Add exactly the :(exclude) lines listed under "Stale guards needing
   :(exclude) lines" above to the named test files — do not remove or edit
   any other line in those guards.
7. Run the full suite: .venv/bin/python -m pytest -q
   Fix anything that fails. Report the final pass/fail counts.
8. Fill in this handoff's `## Results` section: files written, any
   deviations from the design (with reasoning), and the final test run summary.

Do not touch validation/**, any answer_key.json, or anything under
tasks/handoffs/*p5-9*.
```

## Smoke plan (orchestrator runs this after Codex reports green)

1. `.venv/bin/python scripts/convert_criteria.py --framework dpdpa --check`
   → exit 0.
2. Stub-free check: import `DPDPA_DEFINITION` and
   `app.services.grounding.judge.criteria_for`; assert all 41 DPDPA controls
   return `criteria_source == "approved"`.
3. One live v2 DPDPA fixture run via `scripts/grounding_smoke.py` (check its
   `--help` for the right flags/fixture) showing per-requirement
   `criteria_source` counts — confirm DPDPA requirements show `approved`, not
   `fallback`, in the judge stage output.

## Hard rules (reminder)

- No git commits, no pushes — leave files in the working tree.
- Never modify `tasks/criteria-review/signed/dpdpa-criteria-v1.csv`.
- Don't touch `validation/**`, `answer_key.json` files, or `tasks/handoffs/*p5-9*`.

## Results

(fill in after implementation)
