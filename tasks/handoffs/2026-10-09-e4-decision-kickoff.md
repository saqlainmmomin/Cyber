# Kickoff: E4 decision session (signed test criteria on the card and in the analysis)

## Goal
Help Saqlain make decision E4 in about 20 minutes and record it. Done means: his answers to the brief's three questions are written into `tasks/2026-10-08-session-record.md` as a dated decision row, the sequence line (path rule 5) is updated if the decision changes the order, and if he chooses to build something, a scoped build handoff exists at `tasks/handoffs/2026-10-09-e4-<slug>.md` ready for Codex. Do not build anything in this session.

## Current state (2026-10-09)
- Every DPDPA, ISO 27001 and NIST CSF control has signed test criteria (design and operating, each with an evidence hint). GDPR, HIPAA and PCI have none. The v1 analysis never sends them to the judge, and the conclusion card hides them.
- A Codex research run produced the decision brief: `tasks/2026-10-08-e4-test-criteria-decision-brief.md`. Recommendation: (a) show the signed checklist on the card with no prompt change, then deterministic RFI drafting from the evidence hints; send criteria to the judge (b/c) only after a validation experiment passes. Cost of (b): about 38,500 extra input tokens per full three-framework assessment.
- The analysis prompt is frozen by `tasks/2026-09-30-p6-5c-decision-park-v2.md`; option (b) or (c) is an exception to that and needs Saqlain's explicit written decision.
- Parallel work you must not touch: Evidence fix C (being built by Codex, handoff `tasks/handoffs/2026-10-09-evidence-c-kickoff.md`) and the Veldhara demo build (`codex/demo-veldhara-depth`). Any E4 build waits until C merges (path rule 2: at most two things in flight).

## Key files
- `/Users/saqlainmomin/dpdpa-next/tasks/2026-10-08-e4-test-criteria-decision-brief.md`: the brief. Verify any claim you lean on against the code it cites before presenting it.
- `/Users/saqlainmomin/dpdpa-next/tasks/2026-10-08-session-record.md`: decisions E1-E5, path rules, parking lot. Record the outcome here.
- `/Users/saqlainmomin/dpdpa-next/tasks/2026-10-08-ai-coherence-map.md`: item 4 is this decision.
- `tasks/2026-09-30-p6-5c-decision-park-v2.md`: what the freeze protects and what must be decided before reopening.
- `app/frameworks/criteria/iso27001.py` (e.g. `ISO.A5.18.TC3`): a real criterion to show him.

## How to run the session
1. Read the brief, the session record and the P6-5c record. Spot-check 3-4 of the brief's code citations.
2. Give Saqlain a one-screen summary: what exists, the three options as a table (what the auditor sees, size, risk), the recommendation, and ISO A.5.18's real criteria as the concrete example.
3. Ask the brief's three questions one at a time, each with 2-3 options and your suggested default:
   1. Show-only first, or authorise a v1 prompt experiment now as an E4 exception?
   2. Should missing operating evidence lower compliance, or stay an evidence request until the auditor reviews it?
   3. Should evidence hints enrich every scoped RFI request, or only ones the auditor selects? What default period and sample size?
   Push back where an answer conflicts with the coherence rule (every AI step visible, checkable in one click, actionable) or with P6-5c.
4. Record the decision as a new row (E6 or "E4 decided") in the session record, dated, with the why. Update path rule 5's sequence if needed.
5. If he chooses a build, write a Codex-ready handoff (Goal, files, Do list, behaviour tests, Click-through, Out of scope) at `tasks/handoffs/2026-10-09-e4-<slug>.md`. Mark it as starting only after C merges.
6. Commit on branch `claude/c-and-e4-kickoffs` (worktree `/Users/saqlainmomin/dpdpa-next`), push, and open or update a docs-only PR. Never merge.

## Constraints
- No code changes, no LLM calls, never open `validation/companies/*/answer_key.json`.
- No attribution trailers on commits or PRs. Push and PR creation are approved; merging is Saqlain's.
- Plain, short sentences; no em dashes.

## Verification
Before reporting done: the session record's new row quotes his actual answers (not your defaults); the handoff (if any) names files that exist on `main` and contains a Click-through; `git diff origin/main` shows docs only.

## Report back
Append a `## Results` section to this file: the decision in two lines, files changed, PR link.
