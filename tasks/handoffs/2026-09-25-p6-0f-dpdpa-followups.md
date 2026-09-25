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

## Results

Claude ran this on 2026-09-25 in `/Users/saqlainmomin/dpdpa-gap-tool-p6-0f`. The primary texts are the same three MeitY PDFs used in P6-0e (Act, G.S.R. 846(E) Rules, G.S.R. 843(E)), read with `pdftotext`. I kept the independence rule: I opened nothing under `validation/`, no p5-9 handoff, and none of the forbidden scripts or answer keys.

No decision's legal premise was contradicted by the primary text, so I stopped on nothing. One verification changed an expected set (see decision 5).

### Edits by decision (old → new)

1. **CB.TRANSFER.2** (`framework.py`, `questionnaire.py`)
   - Title: "Contractual safeguards for cross-border transfers" → "Transfers comply with s.16 restrictions and stricter sectoral law".
   - Description: "contractual or legal safeguards ... obligations on the receiving party" → it now tests:
     - no transfer to a country or territory restricted by notification under s.16(1), with those notifications tracked;
     - compliance with any stricter law in force in India (s.16(2)).
   - `section_ref`: stays `Section 16`.
   - Question: "contractual or legal safeguards" → the s.16(1) and s.16(2) test.
   - Guidance: "Section 16 requires contractual or legal safeguards" → s.16(1) is a negative-list power and s.16(2) preserves stricter law. Transfer agreements are "supporting evidence only; the Act does not require them".
   - Note: the rewritten requirement now overlaps with CB.TRANSFER.1 (also s.16(1), plus the flow inventory). That follows from the decision, so I did not change it.
2. **CM.RECORDS.2**
   - Title: "Consent refresh and re-validation process" → "Fresh consent for a new or changed purpose".
   - Description: "...when purposes change or after a reasonable period" → fresh consent before processing for a new or changed purpose, because consent is purpose-specific. Existing consent is not relied on.
   - `section_ref`: `Section 6` → `Section 6(1)`.
   - Question and guidance were rewritten to match. "Refresh" and "reasonable period" are removed.
3. **CH2.CONSENT.2 / CM.GRANULAR.1**
   - Titles unchanged.
   - CONSENT.2 description now covers the consent request itemising each purpose and consent being recorded per purpose. It points to GRANULAR.1 for the controls.
   - GRANULAR.1 description now covers working per-purpose controls (toggles) and partial consent actually being possible. It points to CONSENT.2 for the request and the record.
   - The questions and guidance were split the same way, and each guidance names the other ID.
   - GRANULAR.1 guidance: "Section 6 expects" → "Section 6(1)".
4. **`DPDPA_READINESS_NOTE`**: appended the suggested wording verbatim: "Until then, obligations under the Information Technology Act, 2000, s.43A and the SPDI Rules, 2011 continue to apply and were not assessed."
   - Checked against Act s.44(2)(a) ("section 43A shall be omitted") and s.44(2)(c), which omits IT Act s.87(2)(ob), the SPDI Rules' rule-making head.
   - G.S.R. 843(E) cl.(c) brings s.44(2) into force on the same 18-month date, so "until then" is accurate.
   - Gating is unchanged (`dpdpa_readiness_note_applies`). No existing test asserted the exact note text: the P6-0e tests use the constant.
5. **SCP.6** (`scope_questions.py`)
   - Added with the handoff's question text and yes / no / unsure options. The help text says it is a proposal the consultant confirms and that nothing is excluded automatically.
   - Docstring: "5 questions" → "6 questions", and an SCP.6 bullet was added.
   - Proposal path: the DPDPA definition had none, so I reused the P5-5 mechanism with no new UI or schema:
     - `APPLICABILITY_PROPOSALS` (one `ApplicabilityProposal`: SCP.6 answered `yes` → `S17_3_REQUIREMENT_IDS`) is defined in `scope_questions.py`.
     - `app/frameworks/definitions/dpdpa.py` passes `applicability_proposals=APPLICABILITY_PROPOSALS`. That is 2 lines, and the P5-3 dpdpa.py token guard still passes.
     - `app/services/scope_profiler.py`'s `compute_scope_multi` DPDPA branch now calls `propose_not_applicable` and drops any requirement that is already excluded. For example, SDF requirements are not re-proposed when SCP.3 is `no`.
     - `scope_complete.html` already renders `proposed_not_applicable` generically.
6. **CH2.NOTICE.1**
   - Description: added that the notice is understandable on its own, independently of other information the organisation makes available (r.3(a)).
   - `section_ref`: `Section 5(1)` → `Section 5(1); DPDP Rules 2025 r.3`.
   - Guidance: added r.3(a).
7. **CH2.MINIMIZE.3**
   - Description: added that personal data, associated traffic data and other processing logs are retained for at least one year from processing, for the Seventh Schedule purposes, before erasure (r.8(3)).
   - `section_ref`: `Section 8(7)` → `Section 8(7); DPDP Rules 2025 r.8(3)`.
   - **Beyond the handoff:** I also aligned its question and guidance with the r.8(3) element. Otherwise the questionnaire would never ask about it. Reviewer: revert if unwanted.
8. **CH2.NOTICE.3** `section_ref`: `Section 5(1), 8(9); DPDP Rules 2025 r.3, r.9` → `Section 6(3), 8(9); DPDP Rules 2025 r.9`. Each provision checked:
   - s.6(3): the consent request provides DPO or authorised-person contact details.
   - s.8(9): publish the business contact information.
   - r.9: publish it prominently on the website or app, and in every rights response.

   The title and description still say "the notice", but s.6(3) attaches the contact details to the consent request. The decision didn't ask for a change, so I made none. **Open item.**
9. **Question text** (IDs unchanged):
   - NOTICE.1: "at or before the time of collecting" → every consent request is accompanied or preceded by a notice, understandable on its own, with the s.5(1) content.
   - ACCURACY.1: "reasonable efforts ... not misleading" → "do you ensure it is complete, accurate, and consistent" where the data is used for a decision or disclosed to another Data Fiduciary.
   - CORRECT.2: "no longer necessary for the original purpose" → erasure of consented data requestable at any time, and erased unless retention is necessary for the specified purpose or for law.

   Fixtures: `tests/fixtures` holds no question text. The P5-9 packs under `validation/` were not checked, per the independence rule. **Whoever owns P5-9 needs to re-export the question packs:** question text changed for CONSENT.2, NOTICE.1, MINIMIZE.3, ACCURACY.1, CORRECT.2, RECORDS.2, GRANULAR.1 and TRANSFER.2, and SCP.6 is new.
10. **`prompts.py` L299**: `Vague language like "as soon as possible" or "without undue delay" without specific timeframes` → `Vague language like "as soon as possible" without specific timeframes (do not flag "without delay": DPDP Rules 2025 r.7 itself sets that standard for the initial intimation)`.
    - The "without delay" intimation bullet, the 72-hour bullet and the `missing_timeline` flag_type are kept.
    - `test_p5_3` scenario 3 pins updated:
      - `SYSTEM_SHA256` `29d363…` → `21b365d6eac8d3ad2171ac86773567dcee0306b3968a6da993ee67a8bd4e1d93`
      - `REQUEST_KEY` `cb7d28…` → `3e7f8d2a1c9ce76110f25d26e4c7ae86e52b633b441746d5d4d16b82438f1c86`
11. **`_PENALTY_MAP`**: added `("CH2.SECURITY.3", 50)` before `("CH2.SECURITY", 250)`, with a comment. The consumer (`_compute_business_impact`) takes the **first** matching prefix and `break`s, so no restructuring was needed.
    - SECURITY.3 → 50.
    - SECURITY.1 and .2 stay at 250.
12. Commencement: no change (13 May 2027).

### Verification findings
- **s.16(1) notifications:** none found. Secondary sources (legal500, DSCI FAQ, practitioner guides, Sept 2026) report that no restricted-country list has been notified. Note also that s.16 is in G.S.R. 843(E)'s 18-month bucket, so it only commences on 13 May 2027. I could not query egazette.gov.in directly, so this is based on secondary sources.
- **s.17(3) notifications:** none found. Secondary sources report that none has been issued, and s.17 likewise commences only on 13 May 2027. Same caveat about egazette.
- **r.8(3) reading: confirmed.**
  - What it says: "Without prejudice to sub-rules (1) and (2)", retain "such personal data, associated traffic data and other logs of the processing for a minimum period of one year from the date of such processing, for the purposes as specified in the Seventh Schedule", then erase unless other law requires longer.
  - Seventh Schedule purposes: State use for sovereignty or security, State functions under law, and SDF assessment. It is referenced from r.23(1) and r.8(3).
  - r.8(3) is distinct from r.6(1)(e): the one-year retention of logs and personal data for detecting unauthorised access, a security safeguard under s.8(5). r.6(1)(e) is still not assessed separately and would sit under SECURITY/NOTIFY.3.
- **Verified s.17(3) requirement set.** s.17(3) names s.5, s.8(3), s.8(7), s.10 and s.11. Mapped by `section_ref`:
  - s.5: CH2.NOTICE.1, CH2.NOTICE.2
  - s.8(3): CH2.ACCURACY.1
  - s.8(7): CH2.MINIMIZE.2 and CH2.MINIMIZE.3
  - s.10: CH4.SDF.1-4
  - s.11: CH3.ACCESS.1

  Two differences from the handoff's expected set:
  - **CH2.NOTICE.3 is excluded.** After decision 8 it rests on s.6(3), s.8(9) and r.9, none of which s.17(3) names.
  - **CH2.MINIMIZE.3 is included**, because its ref cites s.8(7). Caveat: r.8(3)'s one-year minimum retention supports State access under the Seventh Schedule and r.23, and may survive an s.8(7) exemption. The proposal rationale tells the consultant to check the notification per provision.

  A test derives this set from the `section_ref`s and asserts that it equals the hardcoded tuple.

### Fixture changes (offline `fixture_capture.py`, no `--live`)
- `expected/score.json`: **unchanged**. `expected/analyzer_output.json`: unchanged.
- `mocked_analyzer_response.json`: the call key changed (`b23036…` → `a14835…`) because requirement descriptions are in the analyzer prompt. The response body is identical.
- `expected/pdf_text.sha256`: changed. The PDF carries the new titles, section refs and the SPDI sentence.
- `expected/pdf_meta.json`: `byte_length_lower_bound` 44062 → 44153. `page_count` stays at 16.

### Test changes
- New: `tests/test_p6_0f_dpdpa_followups.py`, with 12 tests covering decisions 1-11 (decision 5 has two tests).
- `tests/test_p6_0e_dpdpa_pack_correctness.py`:
  - `TITLE_CHANGES` extended with CB.TRANSFER.2 and CM.RECORDS.2;
  - the NOTICE.3 expected ref updated.
  - The ID, criticality and weight guard is otherwise intact and passes.
- `tests/test_p5_3_framework_desk_review.py`: scenario 3 hash and key pins (decision 10).
- `tests/test_p5_5_scoping_evidence.py::test_registered_framework_content_is_valid_and_control_ids_are_global`: **not in the allowed list.** It asserted `DPDPA_DEFINITION.applicability_proposals == []`, which decision 5 makes stale. It now asserts that the only DPDPA proposal is `("SCP.6", ("yes",))`. **Reviewer: confirm.**

### Test counts
- After the commit, `.venv/bin/pytest -q` gives **681 passed, 10 skipped, 2 failed**. Both failures are the baseline ones: `test_remediation_tracking::test_scenario_10` and `test_p5_4::test_scenario_13`.
- Before the commit there were also the known uncommitted-tree guards (`test_longitudinal_demo::test_scenario_13`, `test_retention::test_scenario_13`). There was also one transient setup ERROR in `test_workpaper::test_smoke_full_assessment_traceability`. It passed in isolation and on the post-commit full run.
- Note: the local `main` ref in this worktree is stale (`dc64829`, while `origin/main` is `d1c086e`). The `git diff main` guards passed regardless. The diff below is against the branch base `d1c086e`.

### Smoke (`uvicorn app.main:app --port 8766`, worktree `data/dpdpa.db`)
- **Scope form.** I created a DPDPA-only assessment "P6-0f-Smoke" with `POST /assessments/new`. `?tab=scope` renders SCP.6 with the s.17(3) question and the "consultant confirms ... Nothing is excluded automatically" help text.
- **Scope result.** I saved scope with SCP.1 yes, SCP.2 no, SCP.3 possibly, SCP.4 customer, SCP.5 yes, SCP.6 yes. The scope-complete view shows:
  - "37 of 41 requirements apply": only the 4 children's requirements are excluded, and the proposals do not reduce the count;
  - "10 control(s) proposed as likely not applicable — consultant to confirm", listing NOTICE.1, NOTICE.2, ACCURACY.1, MINIMIZE.2, MINIMIZE.3, SDF.1-4 and ACCESS.1, each with the s.17(3) rationale.
  - The generic explainer line under that heading still mentions ISO 27001 SoA. That wording is the existing P5-5 template, which I did not change.
- **Report summary.** I seeded a GapReport with a scratch script. `/report-summary`, which the report page loads by HTMX, renders `data-dpdpa-readiness-note` with the full note, ending in the SPDI sentence.
- **Not exercised:** the penalty tile. The summary uses only approved conclusions, and the seeded item was not approved. SECURITY.3 → ₹50 Cr is covered by `test_11` instead.

### Stopped on
Nothing.

### Open items
- NOTICE.3 title and description still say "notice", while the ref is now the consent request (s.6(3)) plus publication (s.8(9), r.9).
- CB.TRANSFER.1 and .2 now overlap on s.16(1).
- r.6(1)(e) one-year log retention is not assessed as its own element.
- Re-export of the P5-9 question packs is needed (decision 9).
