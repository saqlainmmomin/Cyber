# P6-2a: Draft DPDPA test criteria for Saqlain's sign-off

**Goal.** Produce a first draft of explicit, own-words audit test criteria for all 41 DPDPA requirements. Add the pack schema that will hold them. Export the draft as a review sheet that Saqlain can approve, edit or reject line by line.

- The criteria are the biggest quality lever in the Phase 6 plan. Today the judge has to decide on every run what "compliant" means for each requirement. Criteria make that decision explicit, versioned and reviewable.
- **This task does not wire criteria into any prompt, and it does not change v1 behaviour.** P6-4 consumes them.
- The converter that turns the signed-off sheet back into code is **P6-2b**, a separate handoff written after sign-off.

**Plan:** `docs/plans/2026-09-25-001-grounded-analysis-and-deliverables-plan.md`. See Part B.1 ("Test criteria"), D-P6-D, and "Test criteria lifecycle" under Part F.
**Owner:** Claude drafts, because the task needs regulatory judgment (`tasks/agent-ownership.md`, judgment/domain criterion). **Saqlain signs off every criterion.**
**Branch:** `claude/p6-2a-dpdpa-criteria`, from `main`.
**Depends on:** nothing.
**Runs in parallel with:** P6-1. The file sets are disjoint.
**Blocks:** P6-2b (the converter), then P6-4.

> **Independence rule (non-negotiable).** Criteria are written from the DPDP Act 2023, the DPDP Rules 2025 and the repo's own requirement definitions only. You must **not** open, grep or read any of these:
> - `validation/**`
> - `tasks/handoffs/*p5-9*`
> - `docs/plans/2026-09-24-002-p5-9-end-to-end-validation-plan.md`
> - `scripts/seed_test_companies.py`, `scripts/test_ground_truth.json`, `scripts/seed-v2-prompt.md`
> - any `answer_key.json`
>
> These describe planted gaps in the evaluation companies. Criteria shaped by them would make the P5-9 harness measure the criteria against themselves (D-P5-9-C). If a search you run happens to return content from these paths, discard it and say so in Results.

## Current state

- DPDPA requirements live in `app/dpdpa/framework.py` (41 requirements, ids like `CH2.CONSENT.1`). That file is the source of truth, and `app/frameworks/definitions/dpdpa.py` adapts it into `FrameworkDefinition`.
- `Control` in `app/frameworks/schema.py:14-23` has `id`, `title`, `description`, `reference`, `criticality` and `tags`. It has no criteria field.
- **Known currency gap (plan E-H7).** The pack has no reference to the DPDP Rules 2025. The desk-review prompt credits the 72-hour breach timeline to "Section 8(6)" of the Act (`app/dpdpa/prompts.py`), and that attribution should be checked against the Rules. Record findings like this in the sheet's `source_basis` and in Results. **Do not edit prompts or framework text in this task.**
- Evidence-request document types for DPDPA already exist (P5-5). Look for `evidence_requests` in `app/frameworks/definitions/dpdpa.py` or in the scope profiler. Use those `document_type` keys in `evidence_hint` wherever they fit.

## Deliverables

### 1. Schema (`app/frameworks/schema.py`)

```python
@dataclass(frozen=True)
class TestCriterion:
    id: str            # "<requirement_id>.TC<n>", e.g. "CH2.CONSENT.3.TC1"
    statement: str     # own words; one observable, checkable condition
    kind: str          # "design" | "operating"
    evidence_hint: str # document_type key(s) or evidence form that would show it
    source_basis: str  # "DPDPA s.6(4)" / "DPDP Rules 2025 r.X" (reference only)
```

- Add `test_criteria: tuple[TestCriterion, ...] = ()` to `Control`. The empty default keeps every other framework and every existing test unchanged.
- Add one unit test proving an unmodified `Control` has `test_criteria == ()` and that the registry still loads all frameworks.

### 2. Draft data (`app/frameworks/criteria/dpdpa_draft.py`, new)

- `DPDPA_CRITERIA_DRAFT: dict[str, tuple[TestCriterion, ...]]` with every one of the 41 requirement ids, and 2-5 criteria each.
- **It is not attached to `Control` yet.** Attaching happens in P6-2b, after sign-off, so unapproved criteria can never reach a prompt.
- Add a test that asserts:
  - the keys equal the ids of the 41 requirements
  - each requirement has 2-5 criteria
  - ids follow the `.TC<n>` pattern and are unique
  - `kind` is in `{design, operating}`
  - every field is non-empty

### 3. Review sheet (`tasks/criteria-review/dpdpa-criteria-v1.csv`, new)

- Generate it with a small script: `scripts/export_criteria_review.py`, taking the draft module as input.
- UTF-8, with these columns in this order:
  `requirement_id, requirement_title, criticality, criterion_id, kind, statement, evidence_hint, source_basis, in_force_note, drafter_confidence, decision, edited_statement, reviewer_note`
- `decision`, `edited_statement` and `reviewer_note` are left blank for Saqlain. `decision` takes `approve | edit | reject`.
- Rows are grouped by chapter/domain in framework order, so the sheet can be reviewed one domain at a time.
- `drafter_confidence` is `high | medium | low`. Use `low` wherever the legal basis or its interpretation is uncertain. The reviewer's time should go there first.
- `in_force_note` records whether the obligation is in force as of 2026-09-25, or phased in under the Rules with its commencement date. Leave it blank only when it is obviously in force. **Verify commencement dates against primary sources.** Don't rely on memory.
- Also write `tasks/criteria-review/README.md`: a 10-line guide covering how to review, what each column means, and that the approved sheet is the only input to P6-2b.

## Criteria-writing rules

1. **Observable and binary.** A reviewer with the documents and the questionnaire answer can say met / not met / no evidence.
   - Avoid "adequate", "appropriate" and "robust" unless the statement says what makes it so.
   - Bad: "Consent is properly managed."
   - Good: "The consent request lets the data principal withdraw consent with ease comparable to giving it, and names how to do so."
2. **Atomic.** One condition per criterion. Split compound duties.
3. **Design vs operating.** Every requirement should have at least one `design` criterion (the policy or process exists and says X). Add an `operating` criterion where the obligation is about actually doing something: records, logs, response times, deletions performed. Operating criteria are what separate "paper moat" organisations from real ones.
4. **Own words, references only.** Paraphrase obligations and cite the section or rule in `source_basis`. Don't paste statute text beyond short phrases needed for precision. (The Act isn't licence-restricted like ISO, but the house style under D4 is reference-only.)
5. **Grounded in the law, not in best practice.** When a criterion goes beyond the statute (industry practice), put `practice` in `source_basis` and set `drafter_confidence` to `medium` at most. A consultant must be able to defend every criterion as a legal requirement or clearly see that it isn't one.
6. **Use the repo's own requirement scope.** Criteria test the requirement as `app/dpdpa/framework.py` defines it, whatever its title, description and section reference say. Where the definition and the law disagree, note it in `source_basis`, set `drafter_confidence` to `low`, and list it in Results. Don't silently re-scope.
7. **Primary sources.** Use the Act and Rules text from government sources (e.g. MeitY and the e-Gazette). Record the URLs you used in Results. Secondary commentary may help you understand the law but cannot be a `source_basis`.

## Process

1. Read `app/dpdpa/framework.py`, `app/frameworks/definitions/dpdpa.py` (tags, questions, evidence requests) and `app/dpdpa/questionnaire.py` (question text and guidance). These show what each requirement is meant to cover.
2. Fetch and read the Act and the Rules from primary sources.
3. Draft the criteria chapter by chapter. After each chapter, re-read it against rules 1-6.
4. Export the CSV. Run the tests.
5. Self-review pass: list the 10 criteria you're least sure of, with the reason for each, in Results.

## Verification

- `.venv/bin/pytest -q` passes, and the full suite is unchanged apart from the new tests.
- `git diff main --stat` touches only:
  - `app/frameworks/schema.py`
  - `app/frameworks/criteria/**`
  - `scripts/export_criteria_review.py`
  - `tasks/criteria-review/**`
  - new tests
  - this handoff's Results
- Running the export script twice produces a byte-identical CSV.
- `git grep -n "dpdpa_draft\|DPDPA_CRITERIA_DRAFT" -- app` shows no import outside `app/frameworks/criteria/` and tests. This proves nothing consumes the draft.

## Report back

Append `## Results` to this file with:
- counts: requirements, and criteria split into design / operating
- the primary-source URLs used, with retrieval date
- currency findings: DPDP Rules commencement, the "72-hour" attribution, and anything in the pack that the Rules supersede
- the 10 lowest-confidence criteria, with the reason for each
- confirmation that the independence rule held
- the PR link, with the PR description pointing Saqlain at the CSV

## Results

**Status:** drafted, exported and tested on `claude/p6-2a-dpdpa-criteria`. Not pushed and no PR opened: the orchestrator reviews and opens it. The PR description should point Saqlain at `tasks/criteria-review/dpdpa-criteria-v1.csv` and ask him to start with the `low` rows.

### Counts
- **41 requirements, 150 criteria** (2-5 each; every requirement has at least one `design` criterion).
- By kind: **110 design / 40 operating**.
- By drafter confidence: **87 high / 55 medium / 8 low**.
- 16 criteria are marked `practice` in `source_basis`. None of them is rated `high`, and a test enforces that.

### Primary sources (all retrieved 2026-09-25)
- DPDP Act 2023 (No. 22 of 2023), MeitY copy: https://www.meity.gov.in/static/uploads/2024/06/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf. It is byte-identical to the e-Gazette copy at https://egazette.gov.in/WriteReadData/2023/248045.pdf.
- DPDP Rules 2025, G.S.R. 846(E), 13 Nov 2025: https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf
- Act commencement notification, G.S.R. 843(E), 13 Nov 2025: https://www.meity.gov.in/static/uploads/2025/11/c56ceae6c383460ca69577428d36828b.pdf
- Corrigendum, G.S.R. 892(E), 10 Dec 2025: https://www.meity.gov.in/static/uploads/2025/12/3c7ebbae0e5456f493f486e6845df86b.pdf. It is typographical only and changes no substance.
- MeitY's DPDP Rules 2025 listing page (checked for amendments): https://www.meity.gov.in/documents/act-and-policies/digital-personal-data-protection-rules-2025-gDOxUjMtQWa
- Secondary sources were used only to find these documents. None is cited as a `source_basis`.

### Currency findings

**Commencement (verified against G.S.R. 843(E) and Rules r.1)**
- **In force from 13 Nov 2025:** Act s.1(2), s.2, ss.18-26 (the Board), 35, 38-43 and 44(1),(3). Rules r.1, 2 and 17-21.
- **Mid-Nov 2026 (one year after publication):** Act s.6(9), which requires Consent Managers to register, and s.27(1)(d). Rules r.4.
- **Mid-May 2027 (18 months after publication):** everything else that matters to a fiduciary. That covers Act ss.3-5, s.6(1)-(8) and (10), ss.7-17, the penalty sections and s.44(2). Rules r.3, 5-16, 22 and 23 also start then.
- **Consequence:** at 2026-09-25, **none of the 41 requirements is legally in force for a Data Fiduciary**. Every row's `in_force_note` says so, and DPDPA assessments are readiness assessments until mid-May 2027.
- **Counting the date:** the Gazette is dated 13 Nov 2025 but was digitally signed on 14 Nov. That is why secondary sources give 13 or 14 Nov 2026 and 13 or 14 May 2027. The notes say "mid-Nov 2026" and "mid-May 2027".
- **Old IT Act regime still applies:** s.44(2), which removes IT Act s.43A, also starts in May 2027. Until then the IT Act s.43A regime and the SPDI Rules 2011 still apply. The pack does not cover them. This is not in scope for this task and is flagged for Saqlain.
- **Reported SDF acceleration:** secondary sources report a January 2026 MeitY proposal to shorten the SDF window from 18 to 12 months. MeitY's DPDP Rules page lists no such amendment; it holds only the Rules, the three 13 Nov notifications and the corrigendum. Neither does the Gazette-notifications list. I could not search the e-Gazette directly, so treat this as "not found", not "confirmed absent".

**The "72-hour / Section 8(6)" attribution is wrong**
- Act s.8(6) sets no timeline. It requires intimation to the Board and to each affected data principal "in such form and manner as may be prescribed".
- The 72 hours comes from **Rules r.7(2)(b)**, and it is the deadline for the *detailed follow-up report to the Board*. The Board can extend it on a written request.
- The initial intimation to the Board (r.7(2)(a)) and to data principals (r.7(1)) must be made **"without delay"**. There is no fixed hour count and no harm threshold.
- **Where the wrong attribution appears:**
  - `app/dpdpa/prompts.py:259` and `:296`
  - the "Missing DPDPA timelines" red flag in `app/frameworks/definitions/dpdpa.py`
  - the reason `Section 8(6)` for `breach_procedure` in `app/services/scope_profiler.py`
- These files were not edited, per the task rules.

**Section references in the pack that don't match the law.** These are recorded in `source_basis` as `[repo cites ...]`.

| Requirement | Pack cites | Where the obligation actually sits |
|---|---|---|
| CH2.CONSENT.1 | s.6(1)-(2) | Plain language and the language option are in s.6(3) |
| CH2.CONSENT.3 | s.6(6)-(7) | The withdrawal right is s.6(4); s.6(7) is about Consent Managers |
| CH2.CONSENT.2, CM.GRANULAR.1 | s.6(3) | s.6(3) covers language and contact details, not granularity |
| CH2.NOTICE.3 | s.5(1) | s.6(3), s.8(9) and r.9 |
| CH2.MINIMIZE.1 | s.4(1) | The necessity limit is in s.6(1) |
| CH2.SECURITY.1 | s.8(4) | The safeguards duty is s.8(5); s.8(4) is general technical and organisational measures |
| CH3.CORRECT.2 | s.12(2) | Erasure is s.12(3) |
| CH4.CHILD.1 / CH4.CHILD.2 | s.9(2) / s.9(3) | **Swapped:** the tracking and advertising ban is s.9(3); the well-being duty is s.9(2) |
| CH4.SDF.4 | s.10(2)(d) | **s.10(2)(d) does not exist;** periodic audit is s.10(2)(c)(ii) |

**Wrong references in the questionnaire guidance** (`app/dpdpa/questionnaire.py`, not edited):
- MINIMIZE.* cite "s.8(2)"; the correct provisions are s.6(1) and s.8(7).
- SECURITY.3 cites "s.8(5)"; the correct provisions are s.8(2) and r.6(1)(f).
- NOMINATE.1 cites "Section 12"; the correct provision is s.14.
- BN.NOTIFY.3/4 cite "s.8(5)".
- CONSENT.4 cites "s.6(6)".
- CHILD.3 claims "s.9(1) requires age verification". Neither the Act nor the Rules requires a specific age check of the child. r.10 verifies that the *parent* is an identifiable adult.

**Where the repo's scope departs from the law in substance.** These criteria are rated `low`, as rule 6 requires, and listed below.
- **ACCURACY.1:** the pack says "reasonable efforts". The Act says the fiduciary "shall ensure", and only for data used in decisions about the data principal or disclosed to another fiduciary.
- **CORRECT.2:** the pack limits erasure to data "no longer necessary". Under s.12(3) the data principal can ask at any time, and retention is allowed only for the specified purpose or legal compliance.
- **CB.TRANSFER.2:** the pack requires contractual safeguards for all transfers. The Act uses a restricted-country model instead.
- **CM.RECORDS.2:** the pack's periodic consent refresh has no statutory basis.
- **CH2.NOTICE.1 (disclosed re-scope):** the pack describes the notice as given "at or before collection". The Act ties the notice to consent requests. The pack also omits the statutory minimum content (how to withdraw, exercise rights and complain to the Board). I added that content as TC3-TC5, rated `medium` and labelled in `source_basis`.

**Rules obligations the pack does not cover at all** (not added, since criteria follow the repo's scope):
- r.13(3), algorithmic due diligence for SDFs. This one was placed under CH4.SDF.3.TC4 and labelled.
- r.8(3), minimum one-year retention of processing logs. Placed under CH2.MINIMIZE.3.TC3.
- r.3(a), the notice must be understandable on its own.
- Act s.17(3): startups and other notified fiduciaries can be exempted from s.5, s.8(3), s.8(7), s.10 and s.11. The scope profiler has no question for this.

**Duplicate requirements.** CH2.CONSENT.2 and CM.GRANULAR.1 test largely the same obligation. The criteria are split (the request lists purposes / the record keeps per-purpose status, versus the UI toggles / mixed states actually occur), but Saqlain may want to merge the two requirements.

### The 10 lowest-confidence criteria (review these first)
1. **CH2.CONSENT.4.TC2** (low): must the organisation accept consent routed through Consent Managers? s.6(7) gives the data principal the *option* to use one. Whether that obliges every fiduciary to integrate with Consent Managers is unsettled.
2. **CH2.ACCURACY.1.TC2** (low): the repo says "reasonable efforts" but the Act says "ensure" (s.8(3)), and only for decision-making or onward disclosure. The criterion tests the Act's standard.
3. **CH3.CORRECT.2.TC2** (low): the repo scopes erasure to "no longer necessary" data. s.12(3) is broader, and the criterion tests the Act.
4. **CH4.CHILD.2.TC2** (low): "detrimental effect on well-being" (s.9(2)) is undefined, so what counts as "harmful processing" is a judgment call.
5. **CM.RECORDS.2.TC3** (low): periodic consent refresh is practice with no statutory hook. The item is kept only because the repo's description includes it.
6. **CB.TRANSFER.2.TC2** (low): a contract term for r.15 orders. No r.15 order exists yet, and a contract is only one way to comply.
7. **CB.TRANSFER.2.TC3** (low): transfer contracts with overseas fiduciaries are not required by the Act. The repo's scope exceeds the law.
8. **CB.TRANSFER.3.TC3** (low): SDF localisation under r.13(4). No data category has been specified yet, and no SDF has been notified.
9. **CH4.CHILD.3.TC1** (medium): no provision mandates checking the *child's* age. It is inferred from s.9(1) and the Fourth Schedule Part B item 6 exemption.
10. **CH2.NOTICE.2.TC1** (medium): "consent given before the commencement of this Act" is read per provision under s.1(2), meaning consents given before mid-May 2027. That reading is reasonable but untested.
- **Honourable mentions:**
  - CH2.CONSENT.1.TC3 and CH2.NOTICE.1.TC5: how many of the 22 Eighth Schedule languages must be offered is not settled.
  - CH2.CONSENT.2.TC1: per-purpose consent is a reading of "specific", not express text.

### Independence rule
- **Held.** I did not open, grep, list or read `validation/**`, any `*p5-9*` handoff, the P5-9 plan, `scripts/seed_test_companies.py`, `scripts/test_ground_truth.json`, `scripts/seed-v2-prompt.md` or any `answer_key.json`.
- **One disclosure:** a plain `ls scripts` printed the *filenames* of the seed and ground-truth scripts in a directory listing. I did not open or read their contents.
- Repo greps were limited to `app/` (with `--exclude-dir=validation`), `tests/` and specific files. No content from the restricted paths appeared.
- Web searches returned only public legal sources.

### Tests and verification
- New tests are in `tests/test_p6_2a_test_criteria.py` (5 tests, all passing). They check:
  - `Control.test_criteria` defaults to `()`, and all 6 frameworks load with no criteria attached
  - the draft has exactly the 41 requirement ids
  - each requirement has 2-5 criteria, with at least one `design`
  - ids follow the `.TC<n>` pattern and are unique
  - `kind` is valid and every field is non-empty
  - review metadata is complete
  - `practice` criteria are never rated `high`
  - running the export twice gives a byte-identical CSV
- **One existing test had to change:** `tests/test_p5_3_framework_desk_review.py::test_scenario_12_standing_guards_and_public_signatures`.
  - The P5-3 guard asserted `git diff main -- app/frameworks/schema.py` is empty. Any schema change, including the one this handoff requires, trips it.
  - `app/frameworks/definitions` is still fully protected. For `schema.py` the guard now asserts additive-only: no line removed or changed.
  - This is the only file outside the handoff's allowed diff list.
- **Full suite after commit:** 646 passed, 9 skipped, 3 failed. The failures are the two known pre-existing ones (`test_scenario_10_engagement_rollup_and_tracker_page`, `test_scenario_13_structural_guards`) plus the known `test_longitudinal_demo` flake.
- **Other intermittent failures seen before the commit, each once:**
  - `test_p5_6_rfi_rebuild::test_scenario_10_rendered_artifacts_are_frozen_and_complete`
  - a setup error in `test_workpaper::test_smoke_full_assessment_traceability`
  - Both pass in isolation, on main as well as on this branch.
- **Expected before commit:** `test_retention::test_scenario_13` fails while any test file has uncommitted edits. It clears after commit.
- Running `scripts/export_criteria_review.py` twice gives a byte-identical CSV (same md5).
- Outside `app/frameworks/criteria/`, `dpdpa_draft` is imported only by `scripts/export_criteria_review.py` and the new test. Nothing in `app/` consumes it.
