# Session record and path rules (2026-10-08)

## What happened

1. **Saqlain questioned the project.** Uploading an access review showed a consultant can't see evidence the client sends through a magic link. He asked whether to keep building on the app or start over smaller. Claude first misread this as "shrink the product to evidence extraction". **Corrected:** the product stays a full gap-assessment tool for the whole consultant loop; the problem is that the AI steps inside the loop don't reach the auditor.
2. **Decision: no rebuild.** The data model already carries what an auditor needs (evidence versions, evidence-to-control links, citations to the exact passage, signed design/operating test criteria per control). What's missing is wiring and surfacing, plus one new capability. Agreed rebuild trigger, not hit: most AI steps invisible *and* the data model unable to carry samples/criteria.
3. **Coherence walkthrough** on the Veldhara demo plus a code trace of every LLM call site → `tasks/2026-10-08-ai-coherence-map.md`. Worst findings: client-link uploads never reach analysis; the per-document AI summary is stored but never shown; desk review silently drops documents past 20,000 words; the conclusion card can't be checked against its source; nothing tests tabular evidence.
4. **PRs:** #125 (flow rules) and #128 (Veldhara demo) merged; #116 (stale context update) closed; #127 (XLSX/OCR) sent back because its row sampling dropped 6 of 35 exception rows in Saqlain's 220-row test file, including a terminated admin with access still enabled. Fixed by Codex to store every row (`tasks/handoffs/2026-10-08-flow-s6-f1-keep-every-row.md`), verified 220/220 and 35/35, merged.
5. **Next work:** evidence fixes A-C, handoff `tasks/handoffs/2026-10-08-evidence-fixes.md`.

## Decisions

| # | Decision |
|---|---|
| E1 | No rebuild. Fix in place, guided by the coherence map. |
| E2 | Spreadsheets are stored whole; no sampling at extraction (reverses the flow plan's S6-F1 "sampled" line). |
| E3 | Evidence fixes A (client-link scope), B (evidence viewer), C (checkable conclusion card) come before flow-plan S3. |
| E4 | Open for Saqlain: (4) send signed test criteria to the analysis and show them (touches the P6-5c-parked prompt); (5) deterministic access-review checks (needs his auditor design). |
| E5 | Later: flesh out the Veldhara demo company; fresh context update once A-C land. |

## Path rules (how not to stray)

1. **The AI-coherence test gates every PR.** The PR body names the loop step it changes (request evidence → receive → read → pre-fill → judge → findings → report) and answers: what does the AI produce, where does the auditor see it, can they check it against the original in one click, what does it change downstream. A PR that adds AI output nobody sees, or a screen unrelated to the loop, doesn't get built.
2. **One thing in flight.** At most one handoff being implemented (two only if their files are disjoint). Nothing new starts until the current PR is clicked through and merged.
3. **Saqlain clicks through every PR before merging** using the PR's Click-through section (10 minutes). No click-through, no merge. This is the step that was skipped before.
4. **New ideas go to the parking lot, not a handoff.** Add a line under "Parking lot" below with the date. They get scoped only when the current sequence is done, and only if they pass rule 1.
5. **The sequence is fixed until Saqlain changes it here:** A + B → C → decide E4 → flow-plan S3, S4, S5, S7, S8, S9 → Track 4. Changing the order means editing this file, on purpose.

## Parking lot
- 2026-10-08: Veldhara demo needs realistic documents (stubs are 130-300 characters).
- 2026-10-08: NIST questions all read "Has your organization implemented …?"; NIST assessment shows DPDPA-sounding section names.
- 2026-10-08: RFI items are one line per document type, with no period, cycles or samples (overlaps E4/5 and flow-plan S9).
