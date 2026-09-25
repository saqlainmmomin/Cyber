# P6-0e: DPDPA pack correctness pass

This task makes the DPDPA pack, its prompts and its client-facing copy agree with the DPDP Act 2023 and the DPDP Rules 2025. The work covers:

- section references
- the breach-timeline attribution
- the penalty table
- three requirement descriptions that misstate the law
- a readiness notice, needed because almost nothing binds a Data Fiduciary before mid-May 2027

No requirement is added, removed or renamed. Nothing in scoring changes.

**Plan:** `docs/plans/2026-09-25-001-grounded-analysis-and-deliverables-plan.md`, Track 0. This task absorbs P6-0d (penalty table and DPDP Rules currency) and plan item E-H7.
**Source of the findings:** the P6-2a criteria drafting pass (PR #49, branch `claude/p6-2a-dpdpa-criteria`). It read the Act and Rules from primary sources on 2026-09-25. Its findings are copied into this file, so you do not need PR #49.
**Owner:** Claude implements. This is regulatory copy, and wording is a legal-accuracy judgment (`tasks/agent-ownership.md`, judgment criterion). An independent reviewer checks it before merge.
**Branch / worktree:** `claude/p6-0e-dpdpa-pack-correctness` at `/Users/saqlainmomin/dpdpa-gap-tool-p6-0e`, from `main` @ `dc64829`. `.venv` is symlinked and `.env` copied.
**Runs in parallel with:**
- **P6-1** (Codex, `../dpdpa-gap-tool-p6-1`). Its only overlap is `app/frameworks/prompts.py`, which this task does **not** touch.
- **P6-2a** (PR #49). Both branches edit `tests/test_p5_3_framework_desk_review.py::test_scenario_12`. Whichever merges second rebases and keeps both edits.
**Baseline on `main` @ `dc64829`:** 642 passed, 9 skipped, 2 failed. Both failures are pre-existing and out of scope, so do not fix them:
- `tests/test_remediation_tracking.py::test_scenario_10_engagement_rollup_and_tracker_page` (a date bomb)
- `tests/test_p5_4_adaptive_ucc_questionnaire.py::test_scenario_13_structural_guards` (a stale post-merge guard)

Known intermittents: `test_longitudinal_demo` ordering, and occasionally `test_p5_6_rfi_rebuild::test_scenario_10` and `test_workpaper::test_smoke_full_assessment_traceability`. All pass in isolation.

> **Independence rule (P5-9, D-P5-9-C).** Never open, grep, list or read any of these:
> - `validation/**`
> - any `*p5-9*` handoff
> - `docs/plans/2026-09-24-002-*`
> - `scripts/seed_test_companies.py`, `scripts/test_ground_truth.json`, `scripts/seed-v2-prompt.md`
> - any `answer_key.json`
>
> Exclude them explicitly from every grep, for example with `--exclude-dir=validation`.

> **Verify before you write.** Every legal statement you put in code or copy must be checked against the primary texts:
> - Act: https://www.meity.gov.in/static/uploads/2024/06/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf
> - Rules G.S.R. 846(E): https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf
> - Commencement G.S.R. 843(E): https://www.meity.gov.in/static/uploads/2025/11/c56ceae6c383460ca69577428d36828b.pdf
>
> The findings below are a prior agent's reading. **If a primary text disagrees with a finding here, follow the text, stop on that item, and report the disagreement in Results.** Don't invent a section number you cannot see in the text.

## Decisions (made here so they are not relitigated)

### D-P6-0e-A: Requirement IDs, titles, criticality and weights do not change

- Conclusions, questions and UCC mappings are keyed by requirement ID, and scoring uses section weights. This task edits only `section_ref` strings, three `description` strings, guidance text, prompt text, the penalty table and report copy.
- A `title` changes only where the title itself states the wrong law. That applies to CH2.ACCURACY.1 (D-P6-0e-C). Record any title change in Results.

### D-P6-0e-B: `section_ref` corrections in `app/dpdpa/framework.py`

| Requirement | Now | Change to |
|---|---|---|
| CH2.CONSENT.1 | Section 6(1)-(2) | Section 6(1), 6(3) |
| CH2.CONSENT.2 | Section 6(3) | Section 6(1) |
| CM.GRANULAR.1 | Section 6(3) | Section 6(1) |
| CH2.CONSENT.3 | Section 6(6)-(7) | Section 6(4) |
| CH2.NOTICE.3 | Section 5(1) | Section 5(1), 8(9); Rules r.3, r.9 |
| CH2.MINIMIZE.1 | Section 4(1) | Section 6(1) |
| CH2.SECURITY.1 | Section 8(4) | Section 8(5) |
| CH3.CORRECT.2 | Section 12(2) | Section 12(3) |
| CH4.CHILD.1 | Section 9(2) | Section 9(3) |
| CH4.CHILD.2 | Section 9(3) | Section 9(2) |
| CH4.SDF.4 | Section 10(2)(d) | Section 10(2)(c)(ii) |
| BN.NOTIFY.* currently `Section 8(6)` | — | Leave as `Section 8(6)`, and add `; Rules r.7` where the requirement is about the content or timing of the intimation |

- **Formatting.** Match the file's existing style ("Section X(y)"). If the style uses "Section" for Act references and has no convention for Rules, write "DPDP Rules 2025 r.N".
- **Check CM.GRANULAR.1 and CH2.CONSENT.2 against the text.** Granularity is read into s.6(1)'s "specific ... for the specified purpose". If you conclude no reference fits better, keep the new value and note it in Results as an interpretive mapping.

### D-P6-0e-C: Three descriptions that misstate the law

Rewrite each in the file's existing own-words style, one or two sentences, with no statute text beyond short phrases:

- **CH2.ACCURACY.1.**
  - Now: "reasonable efforts … complete, accurate …".
  - The Act s.8(3) says the fiduciary shall **ensure** completeness, accuracy and consistency where the data is **likely to be used to make a decision that affects the data principal, or disclosed to another Data Fiduciary**.
  - Title becomes: "Data accuracy ensured for decision-making and onward disclosure".
- **CH3.CORRECT.2.**
  - Now: "erasure of personal data that is no longer necessary".
  - s.12(3): the data principal may request erasure (of data she gave consent for), and the fiduciary shall erase it unless retention is necessary for the specified purpose or for compliance with law.
- **CH2.NOTICE.1.**
  - Now: "at or before collection".
  - s.5(1): the notice accompanies or precedes the **request for consent**, and states the personal data and purpose, how to withdraw consent and exercise rights, and how to complain to the Board. Rules r.3 sets the content and form.
  - The title "Notice at or before collection of personal data" becomes "Notice accompanying the consent request".

**Not in scope (Saqlain decides; list them under Open questions in Results):**
- CB.TRANSFER.2 (contract requirement has no statutory basis)
- CM.RECORDS.2 (periodic consent refresh has no statutory basis)
- merging CH2.CONSENT.2 and CM.GRANULAR.1
- IT Act s.43A / SPDI Rules 2011 coverage until May 2027
- the s.17(3) startup exemption missing from scope questions
- Rules r.3(a) (standalone notice)
- r.8(3) (one-year minimum log retention)

### D-P6-0e-D: Breach-timeline attribution

The correct statement, checked against Rules r.7:
- Act s.8(6) sets **no** timeline.
- The initial intimation to the Board (r.7(2)(a)) and to each affected data principal (r.7(1)) is due **without delay**.
- A **detailed report to the Board is due within 72 hours** of becoming aware (r.7(2)(b)), or longer if the Board allows it on request.
- There is **no harm or materiality threshold**.

Fix every place that says otherwise:

1. `app/dpdpa/prompts.py:259`. In the absence-specificity example, replace the quoted example with one that tests the real obligation. For example: "no 'without delay' intimation to the Board and affected Data Principals, or no 72-hour detailed report to the Board per DPDP Rules 2025 r.7(2)(b)".
2. `app/dpdpa/prompts.py:296`. Replace the `missing_timeline` bullet with two bullets:
   - no "without delay" intimation to the Board and to affected Data Principals (s.8(6), r.7(1)–(2)(a))
   - no 72-hour detailed follow-up report to the Board (r.7(2)(b))

   Keep the flag_type `missing_timeline` exactly as it is.
3. `app/frameworks/definitions/dpdpa.py` ~L95-98, `RedFlagPattern("Missing DPDPA timelines")`. Change **only `description`**, for example: "No 'without delay' breach intimation to the Board and affected Data Principals, no 72-hour detailed report to the Board (DPDP Rules 2025 r.7), or no specific Indian regulatory references."
   - **Do not change `pattern`.** `red_flag_key(pattern)` is a stored `flag_type`.
4. `app/services/scope_profiler.py:173`. Change the reason to "Assessed against breach intimation obligations (Section 8(6); DPDP Rules 2025 r.7)".
5. `app/dpdpa/questionnaire.py:119-120`. BN.NOTIFY.1/2 guidance: keep s.8(6), and add the r.7 content and timing in one sentence each.
6. Search the rest of the codebase for other occurrences: `git grep -n -i "72.hour\|72 hour\|8(6)" -- app tests ':!validation'`. Fix any in `app/`. **In `tests/`, change only expectations that assert the old wording**, and list them.

### D-P6-0e-E: Questionnaire guidance references (`app/dpdpa/questionnaire.py`)

- MINIMIZE.* "s.8(2)" becomes s.6(1) for collection and s.8(7) for erasure/retention, whichever the guidance is about.
- SECURITY.3 "s.8(5)" becomes s.8(2) (processors under a valid contract) and Rules r.6(1)(f).
- NOMINATE.1 "Section 12" becomes Section 14.
- BN.NOTIFY.3/4 "s.8(5)" becomes s.8(5) (safeguards) and r.7 where the guidance is about intimation. Read each sentence and cite what it actually describes.
- CONSENT.4 "s.6(6)" becomes s.6(7)–(9) (Consent Managers) if the guidance is about Consent Managers. Otherwise cite what it describes.
- CHILD.3 "s.9(1) requires age verification":
  - s.9(1) requires **verifiable consent of the parent**.
  - Rules r.10 requires due diligence that the person identifying as parent is an identifiable adult.
  - Neither mandates a specific age check of the child.
  - Rewrite the claim accordingly.

Fix any other wrong reference you find in `questionnaire.py` or `framework.py` while reading, and list each one in Results.

### D-P6-0e-F: Penalty table (`app/routers/web.py:1856-1870`)

1. Read the Act's **Schedule** and **s.33** in the primary text. The expected values are:
   - breach of security safeguards: up to ₹250 Cr
   - failure to intimate a breach to the Board or data principals: up to ₹200 Cr
   - children's obligations (s.9): up to ₹200 Cr
   - SDF additional obligations (s.10): up to ₹150 Cr
   - data principal duties (s.15): up to ₹10,000
   - breach of voluntary undertaking: up to the amount applicable to the underlying breach
   - residual: up to ₹50 Cr

   **If the text differs, follow the text.**
2. Correct `_PENALTY_MAP`: `BN.NOTIFY` becomes 200 and `CH4.SDF` becomes 150. Leave the others as the Schedule states. Update the table's comment to cite "DPDPA 2023 Schedule (s.33)".
3. In `app/templates/partials/report_summary.html:124-125,152-154`, replace "per incident" / "Per-incident penalty" with wording that matches s.33 and the Schedule, for example: "Maximum penalty under the DPDPA 2023 Schedule for the highest-severity category identified. Penalty provisions apply from mid-May 2027."
   - Use the Act's own framing of per-breach imposition if s.33 states it. Don't claim "per incident" unless the text says so.
4. Show the tile only where it is already shown (`has_dpdpa_exposure`).

### D-P6-0e-G: Readiness notice (DPDPA in scope, before commencement)

**Verified commencement (G.S.R. 843(E) and Rules r.1):**
- Consent Manager registration (s.6(9), r.4) starts mid-November 2026.
- Every other Data Fiduciary obligation and the penalty provisions start **mid-May 2027**: 18 months after the Rules' publication on 13 Nov 2025, with the Gazette digitally signed 14 Nov.
- **Confirm this in the commencement notification.**

**Constant.** In `app/dpdpa/framework.py`, add `DPDPA_FIDUCIARY_OBLIGATIONS_COMMENCE = date(2027, 5, 14)`. Use the date you confirm; if the texts support 13 May, use 13 May and record why. Add one comment line citing G.S.R. 843(E) and Rules r.1.

**Also add** `DPDPA_READINESS_NOTE`, one sentence of report copy:

> "Most DPDPA 2023 obligations on Data Fiduciaries, and its penalty provisions, commence in mid-May 2027 (DPDP Rules 2025, G.S.R. 846(E)); findings against those obligations are a readiness assessment, not a determination of current non-compliance."

**Where it shows.** Only when DPDPA is in the assessment's frameworks, **and** the report's as-of date is before the commencement constant:

1. **Board gap PDF, Scope & Limitations** (`app/utils/pdf_export.py` ~L1260-1320). Append one paragraph after the existing scope text in both `dpdpa_only` and mixed branches, through `S()`.
   - This is **additive**. Don't rewrite the existing paragraphs (the "PDF sections are additive-only" rule).
   - Use the PDF's own render timestamp as "as of". That is how the page already dates itself.
2. **Integrated PDF.** Add the same paragraph in the assessment block for any assessment with DPDPA in scope, if that block has a natural text slot. If it doesn't, record it in Results and skip it. Don't build a new page.
3. **Web report summary** (`report_summary.html`). Add a one-line note under the executive summary area, gated the same way.

**Leave these alone:**
- Analysis prompts. The judge's semantics don't change in this task.
- Questionnaire copy.

## Golden fixtures

- **What breaks.** Changing `section_ref`, `description`, prompt text or PDF copy changes the DPDPA system prompt (which the golden recording keys on) and the PDF text hash. `tests/test_golden_dpdpa.py` will fail.
- **Regenerate** with the **offline deterministic** capture: `.venv/bin/python tests/support/fixture_capture.py`. **Never use `--live`.**
- **Then check the diff with `git diff --stat tests/fixtures` and a content diff:**
  - `expected/score.json` is **unchanged**.
  - `expected/analyzer_output.json` differs at most in text fields you changed. Statuses and IDs are identical.
  - `mocked_analyzer_response.json` differs only in request keys and hashes.
  - `pdf_text.sha256` / `pdf_meta.json` change is expected.
- **Where to report.** Paste the list of changed fixture files and a one-line reason for each into Results. `FIXED_NOW` is 2026-09-08, so the readiness paragraph **appears** in the golden PDF. That is expected.
- **If the score changes, stop.**

## Allowed test changes

- `tests/test_p5_3_framework_desk_review.py::test_scenario_12_standing_guards_and_public_signatures`.
  - Its `git diff --stat main -- ... app/frameworks/definitions` guard will trip on the one `description` edit in `definitions/dpdpa.py`.
  - Exempt exactly that file from the "empty diff" assertion.
  - Add an assertion that `git diff -U0 main -- app/frameworks/definitions/dpdpa.py` touches no line containing `pattern=`, `id=`, `Control(` or `weight`. That keeps the guard's intent: identifiers and weights frozen.
  - PR #49 also edits this test (the `schema.py` part). On rebase, keep both edits.
- Tests asserting old wording or old penalty values: update the expectation and list each one.
- New tests go in `tests/test_p6_0e_dpdpa_pack_correctness.py`:
  1. Each D-P6-0e-B requirement has its new `section_ref`.
  2. No string in `app/` pairs "72" with "8(6)". Use grep in a test via `subprocess`, or read the files.
  3. `_PENALTY_MAP` values for `BN.NOTIFY`, `CH4.SDF` and `CH2.SECURITY` match D-P6-0e-F.
  4. The readiness note appears in the rendered board PDF text for a DPDPA assessment dated before commencement, and is absent:
     - for an ISO-only assessment
     - for a DPDPA assessment when the as-of date is monkeypatched to after commencement
  5. The web report summary shows the note under the same gating.
  6. The requirement ID set, titles (except CH2.ACCURACY.1 and CH2.NOTICE.1), criticality and weights are unchanged against a snapshot taken from `main` at test-write time. Hardcode the expected set in the test.
  7. The `red_flag_key` values for the DPDPA registry are unchanged.

## Verification (before reporting done)

1. `.venv/bin/pytest -q` shows no new failures beyond the baseline, and the new tests pass.
2. **Run the app and check** (`.venv/bin/uvicorn app.main:app --port 8765` in the worktree). Open an existing or seeded DPDPA assessment's report page and confirm:
   - the penalty tile's wording and value
   - the readiness note
   - a generated board PDF shows the note in Scope & Limitations

   Describe what you saw in Results, or explain why you couldn't.
3. `git diff main --stat` shows only the files named in this handoff, plus the fixture regeneration and the test files.

## Git

- Commit on the branch in the worktree with plain messages.
- **No `Co-Authored-By` or "Generated with" lines (repo rule).**
- Do not push or open a PR. The orchestrator reviews, then does both.

## Report back

Append `## Results` with:
- every edit made (file, requirement or line, old → new)
- any primary-text disagreement with this handoff
- the confirmed commencement date and its basis
- the Schedule values as read
- the fixture diff summary
- test counts
- the smoke observations
- Open questions for Saqlain (the not-in-scope list in D-P6-0e-C, plus anything new)
- commit hashes

## Results

Executed 2026-09-25 by Claude in `/Users/saqlainmomin/dpdpa-gap-tool-p6-0e`. Primary texts were downloaded from the three MeitY URLs above and read with `pdftotext`. The independence rule was kept: nothing under `validation/`, no p5-9 handoff, no forbidden script or answer key was opened.

### Edits

**`app/dpdpa/framework.py`: `section_ref`**

| Requirement | Old | New | Note |
|---|---|---|---|
| CH2.CONSENT.1 | Section 6(1)-(2) | Section 6(1), 6(3) | as handoff |
| CH2.CONSENT.2 | Section 6(3) | Section 6(1) | interpretive: granularity read into "specific ... for the specified purpose" |
| CM.GRANULAR.1 | Section 6(3) | Section 6(1) | interpretive, same reading |
| CH2.CONSENT.3 | Section 6(6)-(7) | **Section 6(4), 6(6)** | **departs from the handoff's `Section 6(4)`**, see Disagreements |
| CH2.NOTICE.3 | Section 5(1) | Section 5(1), 8(9); DPDP Rules 2025 r.3, r.9 | as handoff; see Open questions |
| CH2.MINIMIZE.1 | Section 4(1) | Section 6(1) | as handoff |
| CH2.SECURITY.1 | Section 8(4) | Section 8(5) | as handoff |
| CH2.SECURITY.2 | Section 8(4) | Section 8(5); DPDP Rules 2025 r.6(1)(a)-(b) | **extra**: same error as SECURITY.1 |
| CH3.CORRECT.2 | Section 12(2) | Section 12(3) | as handoff |
| CH4.CHILD.1 | Section 9(2) | Section 9(3) | as handoff |
| CH4.CHILD.2 | Section 9(3) | Section 9(2) | as handoff |
| CH4.SDF.3 | Section 10(2)(c) | Section 10(2)(c)(i) | **extra**: DPIA is (c)(i), a sibling of SDF.4's (c)(ii) |
| CH4.SDF.4 | Section 10(2)(d) | Section 10(2)(c)(ii) | as handoff; s.10(2) has no clause (d) |
| BN.NOTIFY.1 | Section 8(6) | Section 8(6); DPDP Rules 2025 r.7(2) | the sub-rule for Board intimation |
| BN.NOTIFY.2 | Section 8(6) | Section 8(6); DPDP Rules 2025 r.7(1) | the sub-rule for Data Principal intimation |
| BN.NOTIFY.3 / .4 | unchanged | unchanged | IR plan / register are not about intimation content or timing |

**`app/dpdpa/framework.py`: titles and descriptions**
- CH2.NOTICE.1:
  - title "Notice at or before collection of personal data" → "Notice accompanying the consent request"
  - description rewritten: the notice accompanies or precedes every consent request; it states the data and purpose, how to withdraw consent and exercise rights, and how to complain to the Board; r.3 sets content and form.
- CH2.ACCURACY.1:
  - title "Reasonable efforts to ensure data accuracy" → "Data accuracy ensured for decision-making and onward disclosure"
  - description rewritten: ensure the data is complete, accurate and consistent where it is likely to be used for a decision affecting the Data Principal or disclosed to another Data Fiduciary.
- CH3.CORRECT.2: description rewritten: erasure on request of consented data, unless retention is necessary for the specified purpose or for compliance with law.

**`app/dpdpa/framework.py`: new definitions**
- `DPDPA_FIDUCIARY_OBLIGATIONS_COMMENCE = date(2027, 5, 13)`, with a comment citing G.S.R. 843(E) cl.(c) and r.1(4).
- `DPDPA_READINESS_NOTE`, using the handoff's text verbatim.
- `dpdpa_readiness_note_applies(frameworks, as_of)`: one gate helper that the board PDF, the integrated PDF and the web summary all use.

**`app/dpdpa/questionnaire.py`: guidance only.** Question text was not changed.
- CONSENT.2: "Section 6 requires separate consent" → s.6(1), consent specific to the purpose.
- CONSENT.3: s.6(6) → s.6(4) (ease of withdrawal) plus s.6(6) (cessation).
- CONSENT.4: s.6(6) → s.6(7)-(9) plus r.4.
- NOTICE.1: → s.5(1), accompanying or preceding the consent request, plus r.3.
- NOTICE.3: "Section 5 requires the notice to include DPO contact" → s.6(3) (contact details in the consent request) plus s.8(9) and r.9 (published contact).
- MINIMIZE.1: s.8(2) → s.6(1).
- MINIMIZE.2 and MINIMIZE.3: s.8(2) → s.8(7).
- ACCURACY.1: "reasonable efforts ... not misleading" → the s.8(3) "ensure ... complete, accurate and consistent" test, with its two triggers.
- SECURITY.1: s.8(4) → s.8(5) plus r.6.
- SECURITY.2: s.8(4) → s.8(5) plus r.6(1)(a)-(b).
- SECURITY.3: s.8(5) → s.8(2) plus r.6(1)(f).
- CORRECT.2: → s.12(3) with the correct exception.
- NOMINATE.1: Section 12 → Section 14.
- CHILD.1: s.9(2) → s.9(3), now including targeted advertising.
- CHILD.2: s.9(3) → s.9(2).
- CHILD.3: "s.9(1) requires age verification" → s.9(1) verifiable parental consent plus r.10 due diligence that the parent is an identifiable adult. Neither mandates an age check of the child.
- BN.NOTIFY.1: kept s.8(6), plus one sentence on r.7(2): without delay, and a detailed report within 72 hours.
- BN.NOTIFY.2: kept s.8(6), plus one sentence on r.7(1): without delay, and the content list.
- BN.NOTIFY.3: s.8(5) → s.8(5) with r.6(1)(c) (detection and remediation), plus s.8(6) and r.7 for intimation.
- BN.NOTIFY.4: s.8(5) → s.8(6) plus r.7(2)(b). The register is framed as the practical means, not a statutory duty.

**`app/dpdpa/prompts.py`**
- L258: example "consent withdrawal process per Section 6(6)" → Section 6(4). **Extra.**
- L259: absence example → "no 'without delay' intimation to the Board and affected Data Principals, or no 72-hour detailed report to the Board per DPDP Rules 2025 r.7(2)(b)".
- L296: the `missing_timeline` bullet is now two bullets: s.8(6) with r.7(1)-(2)(a) "without delay", and r.7(2)(b) 72-hour report. The flag_type is unchanged.
- L354 (JSON example): "Section 6(6) requires..." → "Section 6(4) requires...". **Extra**, same error as L258.

**Other app files**
- `app/frameworks/definitions/dpdpa.py`: only the `description` of "Missing DPDPA timelines" changed, to the handoff's text. The `pattern` is unchanged.
- `app/services/scope_profiler.py:173`: the reason now reads "Assessed against breach intimation obligations (Section 8(6); DPDP Rules 2025 r.7)".
- `app/routers/web.py`:
  - `_PENALTY_MAP`:
    - BN.NOTIFY 250 → 200.
    - CH4.SDF 50 → 150.
    - **Added `("CH2.CONSENT.5", 200)`.** Verifiable parental consent is s.9(1), which is Schedule item 3. Before this it fell under `CH2.CONSENT` at 50.
    - The comment now cites "DPDPA 2023 Schedule (s.33)" and lists the items.
  - The report-summary route passes `show_dpdpa_readiness_note` and `dpdpa_readiness_note`. The as-of date is the render time, `datetime.now(timezone.utc).date()`.
- `app/templates/partials/report_summary.html`:
  - Hero tile: "per incident under DPDPA" → "maximum under the DPDPA 2023 Schedule".
  - Business-impact copy: "Per-incident penalty ..." → "Maximum penalty the Board may impose for a significant breach under the DPDPA 2023 Schedule (s.33), for the highest-severity category identified. Penalty provisions apply from mid-May 2027."
  - A gated `<p data-dpdpa-readiness-note>` sits directly under the Executive Summary block.
  - The tile is still shown only under `has_dpdpa_exposure`.
- `app/utils/pdf_export.py`:
  - **Board PDF, Scope & Limitations:** additive. When the gate passes, a "Regulatory Commencement:" paragraph is appended after Confidentiality, through `S()`. It covers the `dpdpa_only` and mixed branches, and the as-of date is the same render timestamp as "Assessment Date". The existing paragraphs are untouched.
  - **Integrated PDF:** the natural slot is the per-assessment scope-lines block, and the note is added there. Detection matches the assessment's framework names against the registry's DPDPA name. `IntegratedSection` carries names, not ids, and I did not want to touch `report_content.py`.

**Tests**
- `tests/test_p6_0e_dpdpa_pack_correctness.py` (new, 9 tests):
  - the section refs
  - no sentence in `app/` pairs "72" with "8(6)"
  - penalty map values plus `_compute_business_impact`
  - the board PDF note gate: DPDPA, mixed, ISO-only, after commencement
  - the integrated PDF note gate
  - the web summary note gate
  - no "per incident" in the template
  - IDs, titles, criticality and chapter/section weights against a hardcoded snapshot of main
  - `red_flag_key` values
- `tests/test_p5_3_framework_desk_review.py`:
  - scenario 12: `definitions/dpdpa.py` is exempted from the empty-diff guard. A `-U0` diff assertion was added: no changed line contains `pattern=`, `id=`, `Control(` or `weight`.
  - scenario 3: the pinned `SYSTEM_SHA256` (`bf3dd3…` → `29d363…`) and `REQUEST_KEY` (`4794fa…` → `cb7d28…`) were updated. The curated DPDPA desk-review system prompt contains the L258/L259/L296 lines. This is an "old wording" assertion.
- `tests/test_p5_6_rfi_rebuild.py::test_scenario_22`: **not in the handoff's allowed list.** Its `git diff --stat main` guard protects `app/utils/pdf_export.py` and `app/services/scope_profiler.py`, and both files are ones this handoff requires editing. I excluded those two paths with `:!` pathspecs and left a comment. **Reviewer: confirm this is acceptable, or say how you'd rather narrow it.**
- `tests/test_longitudinal_demo.py::test_scenario_13` and `tests/test_retention.py::test_scenario_13` guard the uncommitted working tree only. They fail before a commit and pass after it, so they were not changed.

### Primary-text disagreements with this handoff
1. **CH2.CONSENT.3 → `Section 6(4)` only.** The description has two sentences:
   - withdrawal "with the same ease as giving it" is s.6(4);
   - "ceases processing upon withdrawal unless retention is required by law" is s.6(6): "cease and cause its Data Processors to cease processing ... within a reasonable time".

   Dropping 6(6) loses the correct basis for the second sentence. Following the text, I used `Section 6(4), 6(6)`.
2. **Commencement date: 14 May → 13 May 2027.** Both G.S.R. 843(E) and G.S.R. 846(E) state their Gazette date as "NEW DELHI, THURSDAY, NOVEMBER 13, 2025" (Extraordinary Nos. 757 and 760). The 14 Nov 2025 date is only the digital-signature and upload stamp (eGazette ID `CG-DL-E-14112025-…`). G.S.R. 843(E) cl.(c) says the provisions commence "eighteen months from the date of publication of this gazette". Rules r.1(4) says "eighteen months after the date of publication". Eighteen months from 13 Nov 2025 is **13 May 2027**, so the constant is `date(2027, 5, 13)`. The copy says "mid-May 2027" either way. See Open question 8.
3. The expected Schedule values all match. There is no disagreement there.
4. **s.33 does not say "per incident".** s.33(1): if the Board determines that "breach of the provisions ... by a person is significant", it may impose "such monetary penalty specified in the Schedule". The new copy says "maximum penalty the Board may impose for a significant breach" and makes no per-incident claim.

### Commencement: confirmed
- **G.S.R. 843(E)**, dated 13 Nov 2025:
  - (a) on publication: s.1(2), s.2, ss.18-26, 35, 38-43, 44(1) and (3).
  - (b) one year later: s.6(9) and s.27(1)(d). This is Consent Manager registration, **~13 Nov 2026**.
  - (c) eighteen months later: ss.3-5, 6(1)-(8) and (10), 7-17, 27 (except (1)(d)), 28-34, 36, 37 and 44(2). This covers every Data Fiduciary obligation and the penalty provisions (s.33), **13 May 2027**.
- **Rules r.1**:
  - (2) rr.1, 2 and 17-21 on publication;
  - (3) r.4 one year after;
  - (4) rr.3, 5-16, 22 and 23 eighteen months after.

### Schedule values, as read (Act, The Schedule, "[See section 33 (1)]")

| Item | Breach | Maximum penalty |
|---|---|---|
| 1 | s.8(5) reasonable security safeguards | ₹250 crore |
| 2 | s.8(6) notice of breach to Board or affected Data Principal | ₹200 crore |
| 3 | s.9 children | ₹200 crore |
| 4 | s.10 SDF additional obligations | ₹150 crore |
| 5 | s.15 duties of Data Principal | ₹10,000 |
| 6 | voluntary undertaking (s.32) | up to the amount applicable to the breach for which s.28 proceedings were instituted |
| 7 | any other provision of the Act or rules | ₹50 crore |

### Fixture diff (offline `fixture_capture.py`, no `--live`)
- `expected/score.json`: **unchanged**.
- `expected/analyzer_output.json`: **unchanged**.
- `mocked_analyzer_response.json`: only the call key changed (`df0370…` → `b23036…`), because the DPDPA system prompt changed. The response body is identical.
- `expected/pdf_text.sha256`: changed. The Scope & Limitations page now carries the readiness paragraph, since FIXED_NOW is 2026-09-08.
- `expected/pdf_meta.json`: `byte_length_lower_bound` went from 43868 to 44062. `page_count` stays at 16, so the paragraph fits on the existing page. I checked this visually.

### Test counts
- After the commit: `.venv/bin/pytest -q` gives **651 passed, 9 skipped, 2 failed**. That is the 642 baseline plus 9 new tests.
- Both failures are the known pre-existing ones: `test_remediation_tracking::test_scenario_10` and `test_p5_4::test_scenario_13`.
- `test_longitudinal_demo::test_scenario_9` failed once in isolation and passed on 3 of 4 reruns. This is the known ordering intermittent: the source list is sorted by random UUIDs.

### Smoke test (`uvicorn app.main:app --port 8765`, worktree `data/dpdpa.db`, which is gitignored)
- **Setup.** The worktree DB was empty. A scratch script seeded one DPDPA-only assessment through `trigger_analysis`, with a stubbed analyzer, then approved and released it:
  - BN.NOTIFY.1 non_compliant/critical
  - CH4.SDF.1 partial/high
  - CH2.CONSENT.1 compliant
- **Report page** (`/assessments/{id}/report`):
  - The hero tile reads "₹200Cr / maximum under the DPDPA 2023 Schedule". On main this assessment would have shown ₹250Cr.
  - Business Impact reads "Up to ₹200 Crore", followed by the new s.33 wording and "Penalty provisions apply from mid-May 2027."
  - The readiness note renders directly under the Executive Summary.
  - Tailwind styling did not load in the browser pane: the page rendered unstyled, and `style.css` is a 1.2 KB stub. This has nothing to do with this change, but I could only verify content and placement, not visual styling.
- **Board PDF** (`/api/assessments/{id}/report/pdf`, 200 application/pdf): Scope & Limitations shows "Assessment Date: September 25, 2026" and, after Confidentiality, "Regulatory Commencement:" with the note.
- **Mixed DPDPA+ISO board PDF**, rendered directly: the note appears in the mixed branch and fits on the page, which I checked from a screenshot.

### Open questions for Saqlain
1. CB.TRANSFER.2: the contractual-safeguards requirement has no statutory basis. s.16 is a negative-list power only. Its guidance still says "Section 16 requires contractual or legal safeguards".
2. CM.RECORDS.2: periodic consent refresh has no statutory basis. Its guidance still says "Section 6 expects".
3. Should CH2.CONSENT.2 and CM.GRANULAR.1 be merged? Both now cite s.6(1).
4. IT Act s.43A / SPDI Rules 2011 are the law actually in force until May 2027 and are not covered.
5. The s.17(3) startup exemption is missing from the scope questions.
6. Rules r.3(a) (notice understandable independently of other information) is not assessed.
7. Rules r.8(3) (minimum one-year retention of personal data, traffic data and logs) is not assessed, and nor is r.6(1)(e) (one-year log retention). Both pull against the "erase" framing of MINIMIZE.2/3.
8. **New: 13 vs 14 May 2027.** I used 13 May, the printed Gazette date plus 18 months. If you prefer the conservative reading that keeps the note on the ambiguous day, use 14 May, which is a one-line change.
9. **New: CH2.NOTICE.3 cites s.5(1).** s.5(1) does not require DPO contact details. s.6(3) (consent request) plus s.8(9) and r.9 are the provisions that do. I kept the handoff's value `Section 5(1), 8(9); DPDP Rules 2025 r.3, r.9` and corrected only the guidance. Consider `Section 6(3), 8(9); DPDP Rules 2025 r.9`.
10. **New: question text is untouched.** It still restates three of the old misstatements, because the handoff scoped question text out:
    - NOTICE.1: "at or before the time of collecting"
    - ACCURACY.1: "reasonable efforts ... not misleading"
    - CORRECT.2: "no longer necessary for the original purpose"

    They should be aligned in a follow-up.
11. **New: the `missing_timeline` prompt bullet** "Vague language like ... 'without undue delay' without specific timeframes" is still in the prompt. r.7 itself uses "without delay" for the initial intimation, so a policy that mirrors the Rules could be flagged. Decide whether that bullet should exempt the r.7 "without delay" standard.
12. **New: `_PENALTY_MAP` maps CH2.SECURITY.3 (processor contracts, s.8(2)) to 250.** The mapping is defensible, because r.6(1)(f) makes the processor-contract safeguard part of s.8(5) reasonable security safeguards. On a strict reading, s.8(2) alone is residual (₹50 Cr).
13. **New: test guard change.** `test_p5_6_rfi_rebuild::test_scenario_22` now exempts `pdf_export.py` and `scope_profiler.py` (see Tests above).
