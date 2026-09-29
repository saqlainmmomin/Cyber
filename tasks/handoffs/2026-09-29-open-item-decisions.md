# Saqlain's answers to the open items in the Phase 6 handoffs (2026-09-29)

Recorded from an `AskUserQuestion` pass on 2026-09-29. **These answers are final for the handoffs named below; do not relitigate.** Each design handoff lives on its own branch or on the draft design PR [#82](https://github.com/saqlainmmomin/Cyber/pull/82). When an implementer picks a task up, they apply the answer here in place of the handoff's "default" or "open question", and copy it into the handoff's Results.

Where an answer matches the handoff's recommended default, it says so. Everything else is stated in full.

## P6-5: v2 A/B, injection quarantine, default flip

Handoff: `tasks/handoffs/2026-09-28-p6-5-v2-ab-and-flip.md`.

| # | Question | Answer |
|---|---|---|
| 1 | How is `insufficient_evidence` (IE) scored? | **Symmetric flag rule.** Any outcome other than `compliant` or `not_applicable` counts as flagged: a catch on a gap, a false positive on a decoy or clean control. `insufficient_evidence_rate` is shown next to it. **Fixed before any v2 number exists.** |
| 2 | Gate scope | **Pooled gate blocks**, literally per D-P6-E (ties pass). The per-framework and per-`criteria_source` splits are shown but non-blocking. A regressing bucket becomes a named watch item in the flip PR. |
| 3 | `v2_missing_pass` | **Measure both (off and on); flip with it off.** Suppressing only on red flags (option 3) stays an optional follow-up. |
| 4 | Quarantine (P6-5a) | **Ship it**, together with the pack. |
| open | Extend the quarantine to the missing pass and the v2 pre-fill adapter? | **No.** Both are non-scoring and already need confirmation. |
| open | Widen patterns beyond `p6-5.1`? | **No**, unless done with a new pack version and look-alike tests. |
| 6 | Spend | **Pilot, then confirm.** Run a one-company pilot, present the pilot-based estimate for the full arms (missing pass off and on), and get approval before the full runs. Saqlain runs every live command; agents can't launch them. |

Still open, and deliberately not decided yet: #5, the flip itself (`[AR: flip]`). It is decided after the numbers exist.

The Stage C v1 re-run has completed and its results are in a PR that Saqlain is pushing. **Record its aggregate metrics here once that PR lands**, through a separate harness agent that doesn't touch `app/`, and respect the independence rule (D-P5-9-C: never open `validation/**`, `summary.*` or any answer key).

## P6-7a follow-ups and P6-7b: add-to-RFI

Handoff: `tasks/handoffs/2026-09-28-p6-7b-add-to-rfi.md`.

| Question | Answer |
|---|---|
| Add-to-RFI control on v1 cards? | **v2 only.** |
| Editable request text before adding? | **No.** One click with the exact text previewed. `request_text_override` can come later as an additive field. |
| Merge into a matching checklist item? | **No.** Keep a separate targeted item. |
| Split consultant-requested items in the board report's open RFI list? | **No.** They are ordinary RFI items to the client. |
| Divergence acknowledgement note (P6-7a) | **Optional.** Acknowledging is still required to approve. |
| `suspected_instruction` queue chip | **Yes, in P6-7b.** |

## P6-8: board report v2

Handoffs: `tasks/handoffs/2026-09-28-p6-8-board-report-v2.md` (B1, merged) and `tasks/handoffs/2026-09-28-p6-8-b2-docx-xlsx.md`.

| Question | Answer |
|---|---|
| Should an issued PDF say "Issued"? | **No.** |
| When does the fpdf2 report retire? | **After B2, P6-9 and one real engagement.** |
| DPDPA penalty exposure line | **A small PR after P6-7b**, DPDPA-conditional, citing the Schedule (s.33). Not in P6-9. The `_framework_label` "INDIA DPDPA" bug can go in the same PR. |
| B2: freeze DOCX/XLSX at issue time? | **No.** Render on download; exports carry `EXPORT_FORMAT_VERSION`. |
| B2: formula-injection style | **`quotePrefix` flag**, not a visible apostrophe. |
| B2: Findings sheet is only the top 10; client edits coming back | **Handoff defaults:** the sheet is named "Top risks"; no XLSX import. |

## P6-9: SoA, roadmap, prior-period comparison

Handoff: `tasks/handoffs/2026-09-28-p6-9-soa-roadmap-comparison.md`. Every open question follows its handoff default:

- SoA justifications are **free text only**.
- A justification edit does **not** flag existing versions "Source data changed".
- The SoA lives **in the board report only**. B2's XLSX adds an "SoA" sheet from the same sidecar.
- **No gate** on missing ISO justifications. The report states how many are missing and the consultant decides.
- Archived prior assessments are **skipped**.
- The DPDPA penalty line is **not** in P6-9 (see P6-8).

## P6-10: remediation drafts and narrative

Handoff: `tasks/handoffs/2026-09-28-p6-10-remediation-and-narrative.md`. Every open question follows its handoff default:

- The gap approval rule is **kept**: a recommended action is still required, so Stage 3 lives in Edit & Approve.
- The measured-value filter is **kept**; the consultant types statutory deadlines.
- **Strict citation:** every accepted narrative line ends with `[F…]`.
- A draft or stale narrative **blocks** generation with a 409.
- PDF references use **requirement IDs**.
- Narrative edits do **not** mark older versions "Source data changed".
- Caps stay at **3** Stage 3 attempts per Conclusion version and **3** Stage 4 attempts per section per findings state.

## P6-2c: ISO and NIST criteria sign-off

Handoff: `tasks/handoffs/2026-09-28-p6-2c-iso-nist-criteria.md`.

| Question | Answer |
|---|---|
| Review order | **ISO descriptions → ISO Annex A → NIST.** Each sheet converts and merges as soon as it is signed. |
| The 78 ISO clause rows (`ISO.C*`) | **Defer.** Saqlain deletes those rows from the signed copy. P5-7 will need its own review of them. Do not leave them blank; blank means unsigned and fails. |
| Existing `pattern` keys | **Keep them**, so no stored `flag_type` is orphaned. |
| `GV.OC.05.TC4` | **Reject.** |
| PR granularity | **One PR per framework**, as each sheet is signed. |

The review itself is Saqlain's work (roughly 2 h, 5 h and 7 h for the three sheets). The converter (Step 3) can run in parallel.

## Process

- **#79's widened scope-guard allowed set: confirmed.** The 10 stale-guard and expectation test files it updated were needed and are accepted.

## Model workflow (new rules, 2026-09-29)

- **Sonnet 5.5 (`claude-sonnet-5-5`) is the default for every subagent** the orchestrator spawns: the harness agent, reviewers, test writers and mechanical work. Earlier handoffs say just "Sonnet"; read that as Sonnet 5.5.
- **Opus only when necessary:** the genuinely hard design work, meaning scoring and grounding boundaries or `[AR]` items where a wrong call is expensive. It is not the default for designers or reviewers. Justify each use in the handoff's Results.
- The app's runtime `llm_model_vision` tier (`anthropic/claude-sonnet-4` in `app/config.py`) is a product setting and is **unchanged**. Ask Saqlain before changing it.

## Still needs Saqlain

- **Push the Stage C re-run PR**, then record its aggregate metrics (see P6-5 above).
- **Review the ISO descriptions sheet** (the first of the P6-2c sheets).
- **Approve pilot spend** for P6-5 once the pilot estimate exists.
- **Decision #5, the flip**, after `ab_comparison.md` and the injection summary exist.
- **Carried over:** a `main`-only branch ruleset, the ISO clause titles (P5-7), and Track 4 security before real client data.
