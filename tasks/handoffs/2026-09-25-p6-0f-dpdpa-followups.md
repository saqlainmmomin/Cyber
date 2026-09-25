# P6-0f: DPDPA pack follow-ups (Saqlain's decisions on the P6-0e open questions)

**What this is.** A second DPDPA correctness pass. It applies the decisions Saqlain made on 2026-09-25 about the open questions P6-0e (PR #52) raised. Every decision below is final. Implement them; don't reopen them.

**Plan:** `docs/plans/2026-09-25-001-grounded-analysis-and-deliverables-plan.md`, Track 0.
**Predecessor:** `tasks/handoffs/2026-09-25-p6-0e-dpdpa-pack-correctness.md`. Its Results section lists the open questions, the primary-source URLs, and the edits already made.
**Owner:** Claude implements, because this is regulatory copy. An independent reviewer checks the work before merge.
**Branch / worktree:** `claude/p6-0f-dpdpa-followups` at `/Users/saqlainmomin/dpdpa-gap-tool-p6-0f`, created from `main` @ `d1c086e`. `.venv` is symlinked and `.env` copied.
**Runs in parallel with:** P6-1 (Codex, `../dpdpa-gap-tool-p6-1`). There is no file overlap, except that P6-1 edits `app/frameworks/prompts.py` (synthesis only), which this task must not touch. P6-1 does not touch `app/dpdpa/`, `app/routers/web.py` or the scope questions.
**Baseline on `main` @ `d1c086e`:**
- Two failures already exist before this task. Don't fix them:
  - `tests/test_remediation_tracking.py::test_scenario_10_engagement_rollup_and_tracker_page` (date bomb)
  - `tests/test_p5_4_adaptive_ucc_questionnaire.py::test_scenario_13_structural_guards` (stale guard)
- Known intermittent: `test_longitudinal_demo` scenario 9.

> **Independence rule (D-P5-9-C).** Never open, grep, list or read:
> - `validation/**`
> - any `*p5-9*` handoff
> - `docs/plans/2026-09-24-002-*`
> - `scripts/seed_test_companies.py`, `scripts/test_ground_truth.json`, `scripts/seed-v2-prompt.md`
> - any `answer_key.json`
>
> `tests/test_answer_key_isolation.py` enforces part of this.

> **Verify against primary texts** (URLs are in the P6-0e Results). If the text contradicts a decision's legal premise, stop on that item and report it in Results. Don't change the decision.

> **IDs, criticality and weights stay the same.** No requirement is added or removed. The only structural addition is one new scope question (decision 5).

## Decisions and what to implement

1. **CB.TRANSFER.2 is rewritten around s.16.** The requirement now tests that transfers outside India do not go to any country or territory the Central Government has restricted by notification under s.16(1). It also tests that a stricter sectoral law is respected (s.16(2)).
   - Update the title, description and `section_ref` (`Section 16`) in `app/dpdpa/framework.py`.
   - Contracts are no longer the test. At most, they appear in questionnaire guidance as supporting evidence.
   - Update the question text and guidance in `app/dpdpa/questionnaire.py` to match.
   - Check whether any s.16(1) restriction notification exists. Record what you find in Results.

2. **CM.RECORDS.2 tests only a change of purpose.** The requirement now tests that fresh consent is obtained before personal data is processed for a new or changed purpose. Consent is purpose-specific under s.6(1).
   - Drop "after a reasonable period".
   - Update the title, description, `section_ref` (`Section 6(1)`), question text and guidance.

3. **CH2.CONSENT.2 and CM.GRANULAR.1 both stay, with separate scopes.**
   - CONSENT.2 covers the consent request and the per-purpose consent record.
   - GRANULAR.1 covers the controls the data principal uses (per-purpose toggles, and partial consent actually possible).
   - Rewrite both descriptions, and their question text and guidance, so the split is explicit and the two don't overlap.

4. **Add an SPDI note to the readiness note.** Extend `DPDPA_READINESS_NOTE` in `app/dpdpa/framework.py` with one sentence. Suggested wording: "Until then, obligations under the Information Technology Act, 2000, s.43A and the SPDI Rules, 2011 continue to apply and were not assessed."
   - Check the wording against Act s.44(2), which omits s.43A with effect from the same commencement.
   - The note is shown wherever P6-0e shows it: board PDF, integrated PDF and web summary. Update any test that asserts the exact note text.

5. **New s.17(3) scope question, as a proposal only.**
   - Add `SCP.6` to `app/dpdpa/scope_questions.py`: "Has your organisation been notified by the Central Government under s.17(3) of the DPDP Act (for example, as a startup exempted from certain provisions)?" The options are yes / no / not sure.
   - When the answer is `yes`, **propose (never auto-apply)** these requirements as likely not applicable: those implementing s.5, s.8(3), s.8(7), s.10 and s.11.
     - Map them from `app/dpdpa/framework.py`'s `section_ref`s. The expected set is the NOTICE.*, ACCURACY.1, MINIMIZE.2, CH4.SDF.* and CH3.ACCESS.1 requirements, but verify against the Act's s.17(3) text.
   - Use the existing DPDPA scope and applicability mechanism, and follow how the P5-5 `ApplicabilityProposal` pattern works for ISO. If DPDPA has no proposal path yet, add the smallest equivalent that the scope UI already renders. If that would need new UI or a schema change, **stop and report**.
   - The help text must say this is a proposal the consultant confirms.
   - Record in Results whether any s.17(3) notification has actually been issued yet.
   - Update the module docstring's count ("5 questions").

6. **Fold r.3(a) into CH2.NOTICE.1.** Add to the description that the notice must be understandable on its own, independent of other information (DPDP Rules 2025 r.3(a)). Add `; DPDP Rules 2025 r.3` to the `section_ref` if it isn't already there.

7. **Fold r.8(3) into CH2.MINIMIZE.3.** Add to the description that personal data, traffic data and processing logs are retained for at least one year for the purposes the Rules specify (r.8(3)). Check this reading against the Rules text; the P6-0e Results also mention r.6(1)(e). Update the `section_ref`.

8. **Correct the CH2.NOTICE.3 reference.** Change the `section_ref` from `Section 5(1)` to the provisions that actually require the contact details: s.6(3), s.8(9) and Rules r.9. Verify each one.

9. **Align question text with the corrected descriptions.** The question text (not only the guidance) for CH2.NOTICE.1, CH2.ACCURACY.1 and CH3.CORRECT.2 still repeats the old misstatements. Rewrite it to match the P6-0e descriptions:
   - the notice accompanies the consent request
   - accuracy is *ensured* for decision-making and onward disclosure
   - erasure can be requested at any time
   - **Question IDs don't change.** Check whether `tests/fixtures` or the P5-9 exported question packs contain question text. If the golden fixtures change, regenerate them **offline only** with `.venv/bin/python tests/support/fixture_capture.py`, and stop if `expected/score.json` changes. The P5-9 packs under `validation/` are off-limits (see the independence rule). Note in Results that they need re-exporting by whoever owns P5-9.

10. **Stop flagging the "without delay" wording.** In `app/dpdpa/prompts.py` (~L299, the `missing_timeline` signal list), stop listing "without undue delay" as vague. Rules r.7 itself uses "without delay".
    - Keep flagging "as soon as possible", and keep flagging a missing 72-hour detailed Board report or a missing Board intimation.
    - Keep the `missing_timeline` flag_type.
    - This changes the DPDPA desk-review prompt. Update any pinned hash or request key in tests the way P6-0e did for `test_p5_3` scenario 3, and list the change.

11. **Lower the SECURITY.3 penalty to ₹50 Cr.** Processor contracts are read strictly under s.8(2), which falls under the residual Schedule item 7 (₹50 Cr).
    - In `app/routers/web.py` `_PENALTY_MAP`, add a `("CH2.SECURITY.3", 50)` entry **before** the `("CH2.SECURITY", 250)` prefix, so it wins the match. Add a comment.
    - Check how the map is consumed: first match or max over matches. The entry must actually produce 50 for SECURITY.3. If the consumer takes the max, restructure the lookup minimally, keeping the behaviour for every other prefix identical.

12. **Commencement date stays 13 May 2027.** No change.

## Tests

- Add `tests/test_p6_0f_dpdpa_followups.py`. It covers one assertion per decision (1-11) where the result is observable in code:
  - new `section_ref`s
  - key phrases present in or absent from descriptions and questions
  - the SPDI sentence in the note, shown under the same gating as before
  - `SCP.6` exists and its `yes` answer produces a proposal (not an exclusion) for the verified requirement set
  - the prompt no longer contains "without undue delay" in the vague-language list
  - SECURITY.3's penalty is 50 while `CH2.SECURITY.1` stays at 250
- Keep the P6-0e guard that asserts the requirement ID set, criticality and weights are unchanged. Extend it if titles change (CB.TRANSFER.2, CM.RECORDS.2, and CONSENT.2/GRANULAR.1 if their titles change).
- You may update existing tests only where they assert old wording, old penalty values, old prompt hashes or the scope-question count. List each change.

## Verification

1. `.venv/bin/pytest -q`: no new failures compared with the baseline.
2. Run the app on port 8766. Check the report page's readiness note (it should show the SPDI sentence) and a DPDPA scope page (it should show `SCP.6`; answering "yes" should show the proposal). Describe what you saw.
3. `git diff main --stat` lists only files this handoff names, plus tests and any regenerated fixtures.

## Git

- Commit on the branch with plain messages.
- **Do not add `Co-Authored-By` or "Generated with" lines.**
- Do not push or open a PR. The orchestrator reviews first.

## Report back

Append `## Results` to this file with:
- each decision and its edits (old → new)
- the verification findings (s.16 notifications, s.17(3) notifications, r.8(3) reading)
- the verified s.17(3) requirement set
- any fixture changes
- test counts
- smoke observations
- anything you stopped on
- commit hashes
