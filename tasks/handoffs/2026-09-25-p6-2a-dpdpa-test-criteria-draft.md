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
