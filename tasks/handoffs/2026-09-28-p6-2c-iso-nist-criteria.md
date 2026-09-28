# P6-2c: ISO 27001 and NIST CSF 2.0 test criteria, from draft to pack code

This handoff takes ISO 27001 and NIST CSF 2.0 down the path DPDPA took:

- P6-2a drafted the criteria and a review CSV.
- Saqlain signed the CSV.
- P6-2b converted it into `app/frameworks/criteria/dpdpa.py` and bumped the pack version.

**Where ISO and NIST actually are (checked on `origin/main` @ `4f5309d`).** Drafting is **already done**, so this handoff does not re-draft. It covers what is left.

| Framework | Draft module | Review sheet(s) | Requirements | Criteria | Signed? |
|---|---|---|---|---|---|
| ISO 27001 | `app/frameworks/criteria/iso27001_draft.py` (PR #58) | `iso27001-criteria-v1.csv`, `iso27001-descriptions-v1.csv` | 93 Annex A + 25 clause ids (`ISO.C*`, not in the pack) | 230 Annex A + 78 clause; 118 own-words descriptions | No |
| NIST CSF 2.0 | `app/frameworks/criteria/nist_csf_draft.py` (PR #58 + P6-2d for the 13 new ids) | `nist-csf-criteria-v1.csv` | 106 (matches the pack exactly) | 348 | No |

Checked on main, no signed ISO or NIST sheet under `tasks/criteria-review/signed/`:

- No ISO or NIST control carries `test_criteria`.
- `pack_version == version` for both packs.
- `scripts/convert_criteria.py` rejects anything but `dpdpa`.

**Plan:** `docs/plans/2026-09-25-001-grounded-analysis-and-deliverables-plan.md`:

- B.1 (test criteria)
- Part C item 6 (pack depth parity)
- E-C5 (ISO pack reproduces Annex A wording)
- D-P6-D (criteria lifecycle), D-P6-J (ISO own-words descriptions), D-P6-L (fallback)

**Owner (per `tasks/agent-ownership.md`, Phase 6 row P6-2a/b/c):**

- Claude drafts and re-baselines.
- **Saqlain signs off every criterion and every ISO description.**
- The converter goes to Codex, and Claude reviews it.

**Branch:** `claude/p6-2c-iso-nist-criteria`, from `origin/main` @ `4f5309d`. Before running the suite, run `git branch -f main origin/main`: the guards diff `main...HEAD`.

> **Answer-key independence (D-P5-9-C).** Never open, grep, glob, list or read:
> - `validation/**`
> - `tasks/handoffs/*p5-9*`
> - `docs/plans/2026-09-24-002-*`
> - `scripts/seed_test_companies.py`, `scripts/test_ground_truth.json`, `scripts/seed-v2-prompt.md`
> - any `answer_key.json`
>
> Criteria come from the standard's intent and the pack definitions only, never tuned to a planted gap. Scope greps to `app/`, `tests/` and `tasks/criteria-review/`. The reviewer (Saqlain) signs without reference to answer keys.

## Goal

1. ISO Annex A controls and NIST subcategories carry Saqlain-approved `test_criteria`, and the v2 judge reports `criteria_source="approved"` for them.
2. The ISO pack's control descriptions are replaced by Saqlain-approved own-words text, which closes E-C5. `QuestionDef.guidance` is generated from the description, so it follows automatically.
3. Each framework's `pack_version` is bumped: `2022+criteria-v1` and `2.0+criteria-v1`.
4. Part C item 6: the ISO and NIST red flags are rewritten as auditor checks, after Saqlain signs the wording. The pilot is below.

## Steps and owners

| Step | What | Owner | Blocks |
|---|---|---|---|
| **1** | Re-baseline the drafts: remove stale annotations and re-rate confidence (list below) | Claude, 1 small commit | Step 2 |
| **2** | Review the sheets, one domain at a time | **Saqlain** | Step 4 |
| **3** | Generalise `scripts/convert_criteria.py` (D-P6-2c-A..H). The contract tests are already on this branch | **Codex**, Claude reviews | Step 4 |
| **4a** | NIST conversion PR: commit the signed sheet, generate `nist_csf.py`, attach, bump | Codex (mechanical) | none |
| **4b** | ISO conversion PR: commit the signed sheets, generate `iso27001.py`, attach, swap descriptions, bump | Codex (mechanical), Claude reviews E-C5 | none |
| **5** | Red flags as auditor checks (Part C6). The pilot wording is below. Saqlain signs, then a small PR | Claude drafts → Saqlain → Codex | none |

Step 3 can run now, in parallel with Step 2. Steps 4a and 4b are independent of each other; whichever sheet is signed first goes first.

## Step 1: re-baseline before Saqlain reviews (Claude)

The NIST draft was written against the 94-id pack. The CSF 2.0 alignment (`38e400b`) then fixed the titles and descriptions that the drafter flagged, and added the evidence mappings. As a result, the sheet's `source_basis` still carries notes that are **now false**.

`source_basis` is carried into `TestCriterion` and stored in the pack, so stale text would become permanent. It is not sent to the judge (`judge.criteria_for` sends only id, kind and statement).

Edit only `nist_csf_draft.py` and `iso27001_draft.py`, then regenerate the sheets with `scripts/export_criteria_review.py --framework nist_csf|iso27001`.

**NIST** (verified against the current pack, 2026-09-28):

- **Strip the bracketed `[repo title ...]` note, keep the confidence (all descriptions now match CSF 2.0):**
  - GV.OV.02.TC1, ID.AM.08.TC1, PR.AT.02.TC1, DE.AE.02.TC1, DE.AE.03.TC1, RS.MA.02.TC1, RS.CO.02.TC1
  - DE.AE.06.TC1 and DE.AE.08.TC1: the title/question mismatch is fixed, so re-rate medium → high.
- **Strip the `[minor repo wording variance ...]` note:** GV.OC.02 and GV.OC.04 rows.
- **The `[repo says ...]` lows. The pack now carries the CSF 2.0 wording, so re-rate each:**

  | Criterion | Pack now says | Action |
  |---|---|---|
  | GV.OC.05.TC4 | "understood and communicated" | Ranking dependencies is not in the outcome. Set source_basis `practice (prioritisation beyond GV.OC-05)`, **medium**, and recommend Saqlain rejects it |
  | GV.RR.01.TC3 | "risk-aware, ethical and committed to continual improvement" | The criterion now tests the pack wording: strip the note, **high** |
  | GV.OV.03.TC4 | "performance ... evaluated and reviewed to identify adjustments" | Re-read the statement against the new description. Keep it if it tests evaluation and adjustment (**high**); if it tests lessons-learned improvement, move it to **practice/medium** (ID.IM owns that) |
  | PR.PS.01.TC4 | "defined and applied across ... hardware, software and platforms" | Strip the note, **high** if the statement covers all platforms |
- **Other stale text:**
  - RS.MA.01.TC1 says ID.IM-04 "which the pack omits". The pack now has `NIST.ID.IM.04`: cite it as supporting, no omission note.
  - PR.IR.04 and DE.AE.07 evidence hints say "no pack evidence request maps ...". Both are now mapped (`business_continuity`, `logging_monitoring`): use those keys.

**ISO:** A.5.1.TC3, A.5.9.TC2 and A.6.1.TC4 are low only because the *legacy* pack description omits the element they test. The own-words descriptions do include those elements (planned review, asset owner, legal/proportionate depth), and they land in the same PR as the criteria.

- Keep the low rating in the sheet.
- Tell Saqlain in the sheet README that these three become sound if he approves the matching description.
- Only then strip the `[repo description omits ...]` note in the Step 4b PR by an **edit** decision. Do not strip it before sign-off.

After Step 1, `tests/test_p6_2c_iso_nist_criteria.py` must stay green. `test_repo_departures_are_low` only fires on `[repo says`.

## Step 2: Saqlain's review workflow and realistic volume

The sheets and columns are the same as DPDPA's (`tasks/criteria-review/README.md`): `decision` is approve, edit or reject, with `edited_statement` or `edited_description`, and `reviewer_note`. Save each signed file, unchanged in format, to `tasks/criteria-review/signed/<same filename>`. **Never modify a signed file after commit.** Change a criterion later through a new sheet version (`criteria-v2`), per D-P6-D.

| Sheet | Rows | Of which low / medium | Realistic time* |
|---|---|---|---|
| `iso27001-descriptions-v1.csv` (93 Annex A rows needed, 25 clause rows optional) | 118 | n/a | ~1.5-2 h |
| `iso27001-criteria-v1.csv`, Annex A rows | 230 | 5 / 80 | ~4-5 h |
| `iso27001-criteria-v1.csv`, clause rows `ISO.C*` | 78 | 1 / 16 | ~1.5 h (can be deferred, D-P6-2c-C) |
| `nist-csf-criteria-v1.csv` | 348 | ~4 / ~130 after Step 1 | ~6-7 h |

\* At about 50-60 rows an hour (DPDPA's 150 rows took one sitting), and faster for rows that are high and approved as-is.

**Recommended order:**

1. **ISO descriptions first.** E-C5 is a licensing exposure that blocks external use, and the fallback judge currently sends near-verbatim ISO text as the implicit criterion.
2. **ISO Annex A criteria.**
3. **NIST** by function (GV → ID → PR → DE → RS → RC).

In each sheet, review the low rows, then the medium rows, then skim the high rows.

**Quality calibration (read these first, about 15 minutes).** They span design and operating rows, high to low confidence, and 27001 vs 27002-guidance sourcing. If the style is wrong, stop and tell Claude before reviewing 700 rows.

- **ISO:** A.5.1 (policy set; includes a low row), A.5.15 (access control; a sampled operating test), A.5.24 (incident planning; mixes 27001 and 27002 guidance), A.8.8 (vulnerabilities; the pentest row is guidance/practice, medium), A.8.15 (logging).
- **NIST:** GV.OC.05 (includes the stale low to reject), GV.RM.01, PR.AA.05, DE.CM.01, RS.MA.01.

**Designer spot-check of those 10 (2026-09-28):**

- Every statement is one observable pass/fail condition, in own words.
- The confidence caps follow the rules: guidance or practice never high.
- Zero 6-word runs are shared with the legacy ISO text across all 308 ISO statements and evidence hints, and across all 118 descriptions.
- **One issue:** the stale NIST annotations that Step 1 removes.

## Step 3: generalise the converter (Codex; design pinned here)

### Decisions (not to be relitigated)

**D-P6-2c-A. One generalised converter, not one per framework.** `scripts/convert_criteria.py` gains these module-level names:

```
SUPPORTED_FRAMEWORKS = ("dpdpa", "iso27001", "nist_csf")
SIGNED_SHEETS = {fw: tasks/criteria-review/signed/{dpdpa,iso27001,nist-csf}-criteria-v1.csv}
OUTPUT_MODULES = {fw: app/frameworks/criteria/<fw>.py}
SIGNED_DESCRIPTION_SHEET = tasks/criteria-review/signed/iso27001-descriptions-v1.csv
LEGACY_ISO_6GRAMS = scripts/data/iso27001_legacy_6gram_sha256.txt
```

All paths are absolute `Path`s under the repo root. `--sheet` and `--out` default per framework, and `--framework` still defaults to `dpdpa`. `approved_criteria`, `load_sheet` and `render_module` keep their names. A new `framework` keyword on `render_module` defaults to `"dpdpa"`. **DPDPA output stays byte-identical**, and `--framework dpdpa --check` must stay green.

**D-P6-2c-B. Pack requirements.**

- DPDPA keeps `get_all_requirements()`.
- ISO and NIST use `<DEFINITION>.all_controls()` (id and criticality) and the same checks:
  - unknown id
  - criterion id pattern
  - duplicate
  - kind
  - empty statement
  - decision rules
  - criticality must equal the pack's
- Title mismatches are still ignored.

**D-P6-2c-C. ISO clause rows are deferred, not dropped silently.** Clauses 4-10 are not pack controls (P5-7 is deferred), so rows whose `requirement_id` fully matches `ISO\.C\d+(\.\d+){1,2}` are handled like this:

- They must still be fully valid and signed (decision, criterion id pattern, kind, statement, own-words guard).
- The pack-membership and criticality checks are skipped.
- They are **excluded** from `ISO27001_CRITERIA`.

The signature is kept in the signed sheet, so a later P5-7 converts them with no new review. Clause rows are *optional* for Saqlain. If he defers them, he deletes those rows from the signed copy; do not leave them blank, because blank means "not signed" and fails.

**D-P6-2c-D. The own-words guard (D4, E-C5), and how it is checked.** Rule: no ISO criterion statement, edited statement, evidence hint or description may share a run of **6 consecutive words** with the legacy pack text.

- The legacy pack's descriptions are near-verbatim ISO/IEC 27001:2022 Annex A text, so they are the best in-repo proxy for the licensed text. The repo has no copy of the standard, and must not.
- Normalisation: lowercase, tokens `[a-z0-9]+`, joined by one space.
- **Why 6:** 5-grams produce false positives on control names such as "software installation on operational systems", while 6-grams give zero hits across all 308 drafted criteria and 118 descriptions.
- The corpus is stored **as SHA-256 hashes only** in `scripts/data/iso27001_legacy_6gram_sha256.txt`, with 1117 hashes. It was generated on this branch from `origin/main` @ `4f5309d`, **before** the descriptions are replaced. Do not regenerate it: after Step 4b the source text is gone.
- API: `own_words_violations(text) -> list[str]` returns the offending normalised runs from *text*, in order of first appearance and deduplicated.
- `approved_criteria(..., "iso27001")` and `approved_descriptions` raise `ValueError` naming the criterion or requirement id. Rejected rows are not checked.
- The guard is ISO-only. NIST text is public domain.

The residual risk is stated honestly: the guard catches copying from the legacy pack, not a fresh copy out of the licensed standard. Saqlain's sign-off is the human check for that, and the README says so.

**D-P6-2c-E. The ISO descriptions sheet.**

- `load_description_sheet(path)`: the columns must equal `export_criteria_review.DESCRIPTION_COLUMNS`.
- `approved_descriptions(rows) -> dict[str, str]`:
  - Returns every Annex A pack id, in pack order.
  - approve → `own_words_description`; edit → `edited_description`, which must be non-empty.
  - **reject is an error**, because every control needs a description; use edit.
  - Blank or unknown decisions, unknown ids, duplicates, any missing Annex A id, and own-words violations are errors.
  - Clause rows are validated and excluded, as in D-P6-2c-C.

**D-P6-2c-F. Generated modules.**

- NIST: `app/frameworks/criteria/nist_csf.py` exports `NIST_CSF_CRITERIA`, `NIST_CSF_CRITERIA_VERSION = "criteria-v1"` and `NIST_CSF_CRITERIA_SHEET_SHA256`.
- ISO: `app/frameworks/criteria/iso27001.py` exports `ISO27001_CRITERIA`, `ISO27001_CRITERIA_VERSION` and `ISO27001_CRITERIA_SHEET_SHA256`, plus `ISO27001_DESCRIPTIONS` and `ISO27001_DESCRIPTIONS_SHEET_SHA256`.
- The header docstring starts `"""Generated by scripts/convert_criteria.py; do not edit by hand.` and names the signed sheet path(s) and their SHA-256.
- The modules never import `*_draft`.
- `render_module(..., framework="iso27001")` without `descriptions` and `descriptions_sha256` raises `ValueError`.
- `main --framework iso27001` takes `--descriptions-sheet`, which defaults to the signed path. Passing `--descriptions-sheet` with any other framework is `parser.error`, which exits non-zero.
- A missing file, or a sheet failing validation, makes `main` return 1.

**D-P6-2c-G. Attachment (Steps 4a/4b, one PR per framework).**

- **NIST, `app/frameworks/definitions/nist_csf.py`:**
  - Attach `test_criteria=NIST_CSF_CRITERIA.get(<id>, ())` to every control.
  - Set `criteria_version=NIST_CSF_CRITERIA_VERSION` on the definition.
- **ISO, `app/frameworks/definitions/iso27001.py`:**
  - Every `Control(...)` literal's `description="..."` string becomes `description=ISO27001_DESCRIPTIONS["<id>"]`. The legacy text must leave the **source file**, not only the runtime objects; the test parses the AST.
  - Add `test_criteria=ISO27001_CRITERIA.get("<id>", ())`.
  - Set `criteria_version=ISO27001_CRITERIA_VERSION`.
  - Do this with a one-off script, not by hand, and do not commit that script.
- `pack_version` then becomes `2022+criteria-v1` and `2.0+criteria-v1`. P6-2b already switched every stored and compared site to `.pack_version`, so no call-site change is needed. As with DPDPA, existing ISO/NIST claim sets become stale and regenerate, which is intended.

**D-P6-2c-H. Out of scope.**

- v1 (`claude_analyzer.py`) stays untouched.
- Clause 4-10 pack controls (P5-7).
- The overlap in `app/frameworks/mappings/clusters.py`: one 6-word A.5.33 phrase ("be protected from loss, destruction, falsification") appears there. Flag it for a follow-up, do not fix it here.
- GDPR, HIPAA and PCI.

### Pack version bumps (D-P6-D)

Each conversion PR is one bump. A later change to any criterion or description means a new sheet version, `criteria-v2`, and a new signed file. Never edit a signed file.

### Contract tests (already written; they are the contract)

**`tests/test_p6_2c_criteria_converter.py`: 43 tests.**

- **Scenarios 1-9** use synthetic tmp sheets and run now: **36 fail and 4 pass** on this branch. The 4 that pass cover an unknown framework exiting non-zero, the legacy corpus shape, `--descriptions-sheet` rejected for NIST (today via argparse's unknown-argument error), and DPDPA `--check` with defaults. Every failure is a missing-code failure: `ValueError: unsupported framework`, or `AttributeError` for `SUPPORTED_FRAMEWORKS`, `own_words_violations`, `approved_descriptions` and so on.
- **Scenarios 10-11** (attachment) are **skipped until the signed sheet is committed**. Once it is, they must pass, and that is the Step 4a/4b definition of done.

**How the designer checked the file.** It was run against a throwaway reference implementation, which is not committed: implement from this spec. All 40 non-skipped tests passed, together with the P6-2a/2b/2c suites. 11 of 13 targeted mutations were killed:

1. no clause deferral
2. guard removed
3. guard on all frameworks
4. guard skipping evidence hints
5. deferred rows not validated
6. no description completeness
7. pack order lost
8. ISO descriptions optional
9. `--check` always 0
10. wrong constant prefix
11. `--descriptions-sheet` accepted for NIST

The 2 survivors are equivalent mutants:

- Allowing reject still fails through the completeness check.
- Clause ids in the descriptions dict are filtered by the pack-order return.

**Sanctioned edits to existing tests, already made on this branch (do not re-edit):**

- `tests/test_p6_2b_dpdpa_criteria.py`:
  - scenario 10 now uses `gdpr` as the unsupported framework
  - scenario 5 uses a GDPR control as the fallback example
  - scenario 6 allows ISO/NIST `pack_version` to be `version` or `version+criteria-v1`
  - scenario 11 gained a `P6_2C_FILES` allow-list (per-PR, nothing removed)
- `tests/test_p6_2a_test_criteria.py::test_unmodified_control_has_no_criteria_and_registry_loads`: a framework with a generated `app/frameworks/criteria/<id>.py` must carry exactly those criteria, and others none.
- `tests/test_p6_2c_iso_nist_criteria.py`:
  - `test_drafts_are_not_attached_to_any_control` now accepts generated criteria.
  - The own-words guard compares against the hashed legacy corpus, not the live descriptions, which become the own-words text after 4b.
  - A new test applies the same guard to all draft ISO criteria.

### Stale guards

Step 3 touches only `scripts/convert_criteria.py`. P6-2b already excludes it in the guards it listed.

Steps 4a/4b also touch:

- `app/frameworks/definitions/{nist_csf,iso27001}.py`
- `app/frameworks/criteria/{nist_csf,iso27001}.py`
- `tasks/criteria-review/signed/*`

Before writing code, grep `tests/` for `main...HEAD` and add **per-path `:(exclude)` lines** for exactly those files wherever a guard would trip. Never delete or broaden a guard line. P6-2b's Results list the guards that tripped last time:

- `test_p6_nist_csf2_alignment.py`
- `test_p6_3a_grounding.py`
- `test_p6_6_report_foundations.py`
- `test_p5_4_adaptive_ucc_questionnaire.py`
- `test_p6_1b_framework_batching.py`
- `test_p5_3_framework_desk_review.py`: its `definitions/` guard fails on changed lines containing `id=`, so check it for iso27001.py

Also expect fallback-era expectations to need updating, the same way P6-2b needed them:

- ISO/NIST `criteria_source == "fallback"` assertions and `pack_version == "2022"`/`"2.0"` in the P6-4/P6-7 tests.
- NIST `nist_csf.py` alignment tests that pin control fields.

List each such edit in Results with a one-line reason. **Do not re-edit `tests/test_p6_2c_criteria_converter.py`.**

### Files touched

- **This branch (designer):**
  - `tasks/handoffs/2026-09-28-p6-2c-iso-nist-criteria.md` (this file)
  - `tests/test_p6_2c_criteria_converter.py` (new)
  - `scripts/data/iso27001_legacy_6gram_sha256.txt` (new)
  - `tests/test_p6_2a_test_criteria.py`, `tests/test_p6_2b_dpdpa_criteria.py`, `tests/test_p6_2c_iso_nist_criteria.py` (sanctioned edits above)
- **Step 1 (Claude):**
  - `app/frameworks/criteria/nist_csf_draft.py`, `iso27001_draft.py`
  - `tasks/criteria-review/{nist-csf,iso27001}-criteria-v1.csv` (regenerated)
  - `tasks/criteria-review/README.md`
- **Step 3 (Codex):** `scripts/convert_criteria.py` only.
- **Step 4a:**
  - `tasks/criteria-review/signed/nist-csf-criteria-v1.csv`
  - `app/frameworks/criteria/nist_csf.py` (generated)
  - `app/frameworks/definitions/nist_csf.py`
  - the guard excludes and expectation updates
  - `tasks/todo.md`
- **Step 4b:**
  - `tasks/criteria-review/signed/iso27001-criteria-v1.csv`, `.../iso27001-descriptions-v1.csv`
  - `app/frameworks/criteria/iso27001.py` (generated)
  - `app/frameworks/definitions/iso27001.py`
  - the guard excludes and expectation updates
  - `tasks/todo.md`
- **Step 5:** `_ISO_RED_FLAGS` in `definitions/iso27001.py`, `_NIST_CSF_RED_FLAGS` in `definitions/nist_csf.py`, and a test pinning keys.

### Codex prompt, Step 3 (paste as-is)

```
You're implementing P6-2c Step 3: generalise scripts/convert_criteria.py to
dpdpa, iso27001 and nist_csf, per
tasks/handoffs/2026-09-28-p6-2c-iso-nist-criteria.md (D-P6-2c-A..F).
No network. Do not write to .git.

1. Read the handoff's Step 3 section in full, then tests/test_p6_2c_criteria_converter.py.
2. Edit ONLY scripts/convert_criteria.py. Keep DPDPA output byte-identical:
   `.venv/bin/python scripts/convert_criteria.py --framework dpdpa --check` must exit 0.
3. Do not edit any test. Make scenarios 1-9 of
   tests/test_p6_2c_criteria_converter.py pass (10-11 stay skipped: no signed
   ISO/NIST sheet exists yet). If an assertion looks wrong, leave it failing and
   explain in the handoff's ## Results.
4. Do not regenerate scripts/data/iso27001_legacy_6gram_sha256.txt.
5. Run the full suite: .venv/bin/python -m pytest -q (after `git branch -f main origin/main`).
6. Fill in ## Results: what changed, deviations with reasons, test counts.
Never open validation/**, any answer_key.json, tasks/handoffs/*p5-9*,
docs/plans/2026-09-24-002-*, scripts/seed_test_companies.py,
scripts/test_ground_truth.json or scripts/seed-v2-prompt.md.
```

Step 4a/4b prompts follow the same shape. Only the files and D-P6-2c-G differ, and the orchestrator writes each one when its sheet is signed.

### Smoke plan (orchestrator, per conversion PR)

1. Run `convert_criteria.py --framework <fw> --check`; it must exit 0.
2. Check that all controls with approved rows return `criteria_source == "approved"`.
3. ISO: every description has `own_words_violations == []`, and the AST check passes.
4. Make one live v2 run on `tests/grounding_fixtures` for that framework and record:
   - the `criteria_source` counts
   - `finish_reason`
   - `criteria_incomplete`
5. Watch the output ceiling. NIST averages about 3.3 criteria per requirement and ISO about 2.5; DPDPA's largest batch was already at 4.7k of 8,192 tokens. If you see `finish_reason=length`, lower `v2_judge_batch_max_requirements` for that framework.

## Step 5 / pilot: red flags rewritten as auditor checks (Part C6)

**Why here and not in criteria.** The Part C6 checks are:

- SoA justification
- internal-audit cycle
- management-review inputs
- risk-treatment traceability
- NIST profile/tier claims

The ISO ones are **clause-level** (6.1.3, 9.2, 9.3, 8.3), and clauses are not pack controls (D-P6-2c-C). CSF Profiles and Tiers are not subcategories. So they cannot live in `test_criteria` without being bolted onto an unrelated control. They belong in `red_flag_patterns`, which v1 desk review and the v2 judge (`red_flag_keys`) both consume as framework-level checks.

**Key stability (decision for Saqlain, default shown).** `red_flag_key()` derives the stored `flag_type` from `pattern`. The default is:

- Keep the existing `pattern` strings where the check is the same, and rewrite only `description`.
- New checks get new patterns.
- Nothing is renamed, so stored `DeskReviewFinding.flag_type` values stay valid.

The pilot wording follows. It is in our own words and cites clauses by number only. Saqlain approves or edits it here, then Codex swaps it in.

**ISO 27001** (unlisted existing flags "Generic policy documents" and "Risk assessment staleness" are unchanged):

| `pattern` (key) | New `description` (auditor check) | Sev. | Basis |
|---|---|---|---|
| Statement of Applicability gaps *(kept)* | Check the SoA lists all 93 controls of the 2022 Annex A (not the 2013 set of 114). Each control must show an include/exclude decision, a reason, and its implementation status. An exclusion must be justified by the ISMS scope or the risk assessment; "not applicable" alone fails. A control marked implemented must have operating evidence. | high | cl.6.1.3(d) |
| Risk treatment not traceable *(new)* | Trace a sample of risks above the acceptance criteria to four things: a treatment option, an owner, selected controls that appear as included in the SoA, and a dated residual-risk acceptance by that owner. Also trace a sample of SoA inclusions back to a risk or a stated requirement. Flag any break in either direction. | high | cl.6.1.3(a)-(f), cl.8.3 |
| Internal audit cycle incomplete *(new)* | The audit programme must cover the whole ISMS scope (clauses and applicable controls) over its cycle. At least one audit must have been completed in the last 12 months by someone who did not audit their own work. Findings must carry corrective actions that are tracked to closure. Flag a programme with no plan, audits out of cycle, or self-audit. | high | cl.9.2, cl.10.2 |
| No management review evidence *(kept)* | Check the latest management review is within the planned interval. Its record must show each input the standard requires was considered: prior actions, changes in internal/external issues and interested-party needs, performance and audit results, nonconformities, objectives, risk results, and improvement opportunities. It must also record decisions on improvements or ISMS changes. Minutes that only note attendance fail. | high | cl.9.3.2, 9.3.3 |
| Certification without evidence of operational controls *(kept)* | Where a certificate is cited, check that its scope statement covers the entity, sites and services being assessed. Then check operating records exist for the review period (risk register updates, audit reports, training and access-review records). A certificate is not itself evidence that a control operates. | high | cl.4.3, cl.9.1 |

**NIST CSF 2.0** (unlisted existing flags are unchanged: "Detection without response capability", "Asset inventory gaps", "Supply chain blind spots"):

| `pattern` (key) | New `description` (auditor check) | Sev. | Basis |
|---|---|---|---|
| Tier mismatch with claims *(kept)* | Where the organisation claims an Implementation Tier or maturity level, test the claim against evidence. Tier 3 needs approved, organisation-wide risk practices with records of regular update. Tier 4 needs evidence that practices were adapted from lessons learned or metrics. A claim without dated evidence is flagged; the Tier is never taken from the claim. | high | CSWP 29 §3.2 (Tiers) |
| Profile claims unsupported by evidence *(new)* | Sample subcategories that a Current Profile marks achieved, and check each against evidence for this period. Achieved-without-evidence is flagged, and the Profile is not used to pre-fill outcomes. | high | CSWP 29 §3.1 (Profiles) |
| Profile without action *(kept)* | A Target Profile must be backed by a gap analysis against the Current Profile, and an action plan with owners, dates and priorities tied to the risk strategy (GV.RM). Progress against the plan must be recorded. A Target Profile with no plan, or a stale plan, is flagged. | medium | CSWP 29 §3.1; GV.RM-01 |
| Govern function absence *(kept)* | Look for the core Govern evidence: an approved risk strategy (GV.RM), assigned roles and authority (GV.RR), an approved policy (GV.PO), and a leadership oversight record for the period (GV.OV). Flag when two or more are missing, whatever the Protect/Detect tooling. | high | GV.RM, GV.RR, GV.PO, GV.OV |
| Recovery plan never tested *(kept)* | Check for a recovery or continuity exercise in the last 12 months, with scope, results and lessons learned fed back into the plan (a changed plan version or a tracked action). A plan with no exercise record is flagged. | medium | RC.RP-01, ID.IM-02, ID.IM-04 |

## Open questions for Saqlain (defaults in bold)

1. **Review order:** **ISO descriptions → ISO Annex A → NIST**, or NIST first (its rows are in slightly better shape)?
2. **ISO clause rows (78):** **defer**, which means deleting them from the signed copy, or sign now so P5-7 needs no review?
3. **Step 5 key stability:** **keep existing `pattern` names**, or rename freely and accept orphaned stored `flag_type` values?
4. **GV.OC.05.TC4:** reject (recommended), or keep as practice/medium?
5. **One PR or two for 4a/4b:** **one per framework**, as each sheet is signed.

## Designer verification

- Full suite on this branch (with `git branch -f main origin/main` not run; local `main` = `93d8b32`): see Results below for the counts.
- The own-words scan, 6-gram against the hashed corpus:
  - 0/308 ISO criteria and evidence hints
  - 0/118 descriptions
  - one 6-gram hit in `app/frameworks/mappings/clusters.py` (D-P6-2c-H)
- Independence held: no answer-key path was opened or grepped. One `ls scripts/` printed file *names* only, including the seed-script names; none was opened.

## Results

_(implementer fills in)_
