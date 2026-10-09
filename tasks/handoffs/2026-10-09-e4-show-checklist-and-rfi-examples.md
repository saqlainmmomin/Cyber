# Handoff (Codex): show signed checklist on the card, and add evidence examples to RFI requests

**Starts only after Evidence fix C (`tasks/handoffs/2026-10-09-evidence-c-kickoff.md`) has merged.** Decision: E6 in `tasks/2026-10-08-session-record.md`. Brief: `tasks/2026-10-08-e4-test-criteria-decision-brief.md`.

## Goal
Two parts, one PR each if the diff is large.
1. **Show-only checklist.** The v1 conclusion card shows the control's signed test criteria (kind, statement, evidence hint, source basis), labelled "Auditor checklist; not used by this analysis." No prompt change. No pass/fail shown.
2. **RFI examples.** Every scoped RFI document request lists the mapped controls' signed statements and hints, plus a short "example of what to send" for its document type. Period and sample size are free text for the auditor. No LLM call.

## Coherence test (path rule 1)
Loop step: findings (part 1) and request evidence (part 2). AI output: none new. Auditor sees the checklist on the card and the examples in the RFI. Check in one click: criteria carry their source basis. Downstream: none for scoring.

## Files (all exist on main)
- `app/services/requirement_card.py` (v1 branch returns `criteria=()` near line 610; `V1_SOURCE_LABEL`)
- `app/templates/components/requirement_card_body.html`
- `tests/test_p6_7_requirement_card.py`
- `app/services/rfi_requests.py` (`build_rfi_document`, around line 191)
- `app/services/rfi_evidence_requests.py` (`request_text`, `request_title`)
- `app/frameworks/schema.py` (`EvidenceRequest`, `TestCriterion`)
- `app/services/document_categories.py` (DPDPA's 15 document types)
- `tests/test_p5_6_rfi_rebuild.py`, `tests/test_p6_7b_add_to_rfi.py`

## Do
1. Part 1: in the v1 card branch, fill `criteria` from the registry for the conclusion's control (all frameworks; empty for GDPR/HIPAA/PCI, show nothing). Render each as a design or operating row with hint and basis. Add the label above. Old runs get the same label.
2. Part 2a: add one catalogue, `document_type -> {example_artifacts, good_looks_like}`, as a Python dict in one new module (version-controlled, like the criteria). Enumerate every `document_type` from all six frameworks' `evidence_requests` plus the DPDPA list and `other`. ISO + NIST alone contribute 34 distinct types; enumerate the rest in code (DPDPA, GDPR, HIPAA and PCI definitions returned none from `evidence_requests` when checked, so confirm where their types come from). Own words, no standard text. Examples: firewall review -> "export of current firewall rules with change dates"; access review -> "dated user list per system with reviewer sign-off and removals".
3. Part 2b: in `build_rfi_document`, append for each document request: the mapped controls' signed statements, the evidence hints, and the catalogue example. Keep the existing `request` text first. Free-text period and sample line left for the auditor.
4. Part 2c: allow the same text for card "add to RFI" on v1 conclusions (service guards at `requirement_card.py` 418-419 and 743-746 currently reject v1; keep idempotent recording).
5. Draft the catalogue and send the list to Saqlain in the PR body for a quick read; he signs it as he did the criteria.

## Behaviour tests
- v1 card for an ISO control shows its criteria with kind, hint, basis, and the label; for a GDPR control shows none and no error.
- No criterion is shown as met or unmet.
- Every document type in every framework's requests has a catalogue entry (test fails when a new type is added without one).
- RFI item for an access review type contains the statement, the hint and the example, and still has its original request text.
- Adding the same request twice does not duplicate it.
- Prompt fingerprint tests (`tests/test_p6_1b_framework_batching.py`) pass unchanged: the analysis prompt is untouched.

## Click-through (Saqlain, 10 minutes)
1. Open the Veldhara demo, a v1 conclusion on an ISO access control. See the checklist and the label.
2. Open a GDPR conclusion. No checklist, no crash.
3. Generate the RFI. Open the access review request: see statements, hint, example, and a free-text period/sample line.
4. Skim the firewall and one DPDPA request for sensible examples.

## Out of scope
Sending criteria to the judge, any prompt change, scoring changes, new LLM calls, criterion-level pass/fail, defaults for period or sample size, answer keys.
