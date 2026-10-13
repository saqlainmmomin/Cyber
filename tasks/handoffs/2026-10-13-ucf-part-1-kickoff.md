# Kickoff: unified control framework, part 1 (lane T, WP 3.1 and prep for 3.2, 3.3, 3.4)

For a fresh Claude Code session in the terminal (Ghostty). Assume no memory of earlier sessions. Read this file first, then the files under "Read first".

## Goal

Build the first signed slice of the unified control framework (UCF): the ISO 27001 base, plus the groundwork that lets the NIST and DPDPA layers follow. Three tracks run in parallel inside this session. You stop at "signable tables". You do not load anything into the app and you do not touch app behavior.

**Done means:**
1. Track 1: a reviewable table set for the ISO 27001 base (clauses 4 to 10 and Annex A 93): single requirements, unified controls, mappings, one table per master domain, ready for Saqlain to sign.
2. Track 2: atomized single requirements for NIST CSF 2.0 (106 subcategories) and DPDPA (41 requirements), each with a proposed mapping to the base control list once Track 1's first pass exists.
3. Track 3: the library schema and the validation script that checks the rules in plan section 7.6.
4. A Results section appended to this file.

## Read first

| Path | Why |
|---|---|
| `docs/plans/2026-10-13-001-single-track-implementation-plan.md` | The plan of record. Read sections 1, 5, 7 and 13 in full, and WP 3.1 to 3.4. |
| `tasks/2026-10-13-open-items-answers.md` | Saqlain's answers. Q1, Q3, Q8, S3 and S4 govern this work. |
| `~/job-search/applications/kpmg-control-library/interview-prep.html` | Saqlain's own control-library method. Use the method sections only: "How to map controls", "The 10 steps", "How well do two things match", "The control-writing formula", "What to record for each control", "Cleaning up a messy library", "Mistakes to avoid", and "The clauses (4 to 10)". Example numbers on that page are illustrative, not facts about any client. |
| `app/frameworks/definitions/iso27001.py` | The 93 Annex A controls as stored today (ids, titles, descriptions, references). No clauses 4 to 10. |
| `app/frameworks/definitions/nist_csf.py`, `app/frameworks/definitions/dpdpa.py`, `app/dpdpa/framework.py` | NIST subcategories and DPDPA requirements as stored today. |
| `app/frameworks/criteria/{iso27001,nist_csf,dpdpa}.py` | 728 signed test criteria. Seeds for the test and good-looks-like fields. The `*_draft.py` files are not signed; do not use them. |
| `app/frameworks/schema.py` | Existing `Control`, `QuestionDef`, `TestCriterion`. |
| `app/frameworks/mappings/clusters.py` | The 52 clusters being replaced. Read for what overlaps were already judged; do not copy its grain. |
| `docs/ui-audit/` (on branch `codex/ui-audit`) and `tasks/2026-10-13-content-audit.html` | Why the content has to change. Findings F-D1 to F-D19 are the ones this work answers. |

## Decided (do not reopen)

- Three frameworks only: ISO 27001:2022 (with Amd 1:2024), NIST CSF 2.0, DPDPA 2023 with Rules 2025. GDPR, HIPAA and PCI DSS are parked.
- ISO 27001 is the base. NIST is layered on it. DPDPA is layered on top with its own privacy slots. Common controls appear once. A control only partly covered by ISO gets its own remainder slot. Taking one framework out of scope must still work.
- Method: one master list. Every source is mapped to it once. Sources are never mapped to each other. One requirement per row. One control means one goal, one owner, one test.
- The judged unit is the framework record (an ISO control or clause, a NIST subcategory, a DPDPA requirement). The single asks inside a record are mapping atoms only. Each record has exactly one primary unified control.
- The library is static authored data, versioned. Per-assessment text (gap title, condition, impact, recommendation) is generated elsewhere; it is not part of this work.
- Expect fewer unified controls than the first estimate of 150 to 250. ISO and NIST overlap heavily. Do not aim for a number. Report the count per framework subset when each domain is ready.
- Master domains (18, approved): ISMS and governance (clauses 4 to 10); Risk and compliance; Assets and information; Identity and access; Cryptography; Network and infrastructure; Operations, logging and monitoring; Secure development and change; Physical and environmental; People; Suppliers and third parties; Incident and breach management; Resilience and continuity; Privacy: notice and consent; Privacy: principal rights and grievance; Privacy: purpose, minimization and accuracy; Privacy: fiduciary governance (nomination, significant data fiduciary, data protection officer); Privacy: special categories and transfers. Privacy domains appear only when DPDPA is in scope. ISO themes (Organizational, People, Physical, Technological) stay as an attribute.
- Own wording. Do not copy the standards' text. Store a reference and a short paraphrase for each source atom. Control statements are framework-neutral and never name a framework.
- A number or timeframe lives in the layer that sets it. A framework's number applies only when that framework is selected. Where selected frameworks differ, the strictest applies among the selected ones only.
- Match types: equal, requirement smaller (control covers all and more), requirement bigger (control covers part), overlap, none. Coverage: full, partial, none. Every mapping row has a one-line reason.
- A remainder slot is created when coverage is partial, unless the mapping row records "remainder immaterial" with a reason.

## Fields per unified control

| Field | Notes |
|---|---|
| `id` | `UC-<DOMAIN>-<NN>`, stable. A change makes a new library version. |
| `statement` | Who, does what, when, how, why, proof. One goal. Framework-neutral. Active voice. |
| `why_asked` | One or two sentences: what failure this prevents. For the consultant. |
| `how_to_ask` | Plain-language direction for putting it to the client, with one example probe. |
| `expected_evidence` | Artifact names in the client's words, and the period to cover. |
| `good_looks_like` | What a fully implemented answer contains. |
| `test` | What to sample and what a pass looks like. Seed from the signed criteria. |
| `baseline_risk` | One sentence: what happens if absent. Static. |
| `importance` | Internal. critical, high, medium, low. Never shown as "Critical" to a user. |
| `domain` | One of the 18. Exactly one. |
| `iso_theme` | Organizational, People, Physical or Technological, where applicable. |
| `owner_role` | Domain owner role from the library, for example "Head of IT Operations". Not a person. |
| `applicability` | When the control applies, if conditional (children, significant data fiduciary, cloud). |
| `control_type`, `frequency`, `key_settings` | Recorded now, shown later. |

Mapping rows (separate table, never comma-separated cells): `source_framework`, `source_ref`, `atom_id`, `unified_control_id`, `match_type`, `coverage`, `reason`, `primary` (true for exactly one row per framework record), `remainder_of` (the base control id for a remainder slot).

## Tracks

### Track 1: ISO base (primary)

1. Atomize ISO clauses 4 to 10 and Annex A 93 controls into single requirements. Clauses 4 to 10 are not in the repo; write them as short paraphrases from your knowledge of the standard and mark each `needs_verification`. Saqlain is an ISO 27001 Lead Auditor and will check them.
2. Draft unified controls. Most Annex A controls map 1:1. Split a control where the test differs. Merge only where two ISO controls have the same goal, owner and test.
3. Assign each control to one master domain and write the fields above. Seed `test` from the signed ISO criteria and `expected_evidence` from the existing ISO evidence requests in `iso27001.py`.
4. Produce one sign-off table per domain, at most about 15 rows each, sorted by id.

### Track 2: NIST and DPDPA atoms (parallel, no dependency on Track 1 for step 1)

1. Atomize the 106 NIST subcategories (expect 3 to 6 asks in some) and the 41 DPDPA requirements. Keep the exact id and reference. Paraphrase.
2. Once Track 1 has a first pass of base controls, propose a mapping row for every atom: to a base control (full, partial) or a remainder slot or a new slot in the matching domain. Flag NIST-only atoms and DPDPA privacy-only atoms.
3. DPDPA overlap that the plan expects: security safeguards, breach notification and intimation, processors, retention and erasure. Privacy-only: notice, consent, principal rights and grievance, purpose, minimization and accuracy, nomination, significant data fiduciary, children, cross-border. Check each against the repo's DPDPA pack; the audit found purpose, minimization, accuracy and nomination had no home in the draft plan, which is why the two new privacy domains exist.
4. Reuse the curated DPDPA question text and guidance in `app/dpdpa/questionnaire.py` as source text for `how_to_ask` where it is good (the audit rates it good on substance). Split the five compound questions.

### Track 3: schema and validator (parallel)

1. Write the library schema as plain data files. Keep it simple: one file per table (JSON or CSV), a loader, and a single validation script `scripts/ucf/validate.py`.
2. The script enforces plan section 7.6: (1) every framework record maps to at least one unified control with full coverage, or base plus remainder slot, or a recorded "remainder immaterial" reason, or "no match" with a reason, and has exactly one primary control; (2) every unified control has a source reference, a statement, a test and an owner role; (3) no control is in two domains and no record maps to the same control twice; (4) for each of the seven framework subsets, no shown text or number names an out-of-scope framework and no out-of-scope remainder slot appears; (5) both directions answer: controls covering a record, and records losing coverage if a control is retired; (6) every question-style field is a single obligation without a control code; (7) ids are stable.
3. Print counts per framework subset: controls shown, records covered. This is how the questionnaire size is reported.
4. One run, one exit code. No test framework, no fixtures beyond the data itself.

## Where things go

| Path | Purpose |
|---|---|
| `docs/ucf/drafts/` | Atoms, mapping rows and control drafts as CSV or Markdown tables for review |
| `docs/ucf/signoff/<domain>.md` | One sign-off table per domain |
| `app/frameworks/ucf/` | The data package (schema, loader). Nothing outside it reads it yet |
| `scripts/ucf/validate.py` | The validation script |

You may also touch the specific framework definition files WP 3.1 names (ISO scope question content) only if you need to record a finding; do not change them yet. Do not edit `app/routers/*`, templates, prompts, scoring or `tasks/todo.md`.

## Rules

- Never read `validation/companies/*/answer_key.json`.
- No LLM calls from the app and no live API spend. Your own subagents are fine.
- American spelling. Plain language, short sentences. No em dashes in files you write. Sentence case.
- Do not tune anything to a specific planted gap.
- No Claude or Codex attribution in commits or PRs. Push your branch and open a docs-or-data PR yourself if asked; never merge.
- Work in your own worktree and branch. Do not use the main checkout.
- Model use: decide and review in this session. One Opus drafting subagent per framework for atomization and first-pass mapping, each owning a disjoint output file, each returning a summary of 250 words or fewer. Sonnet subagents for the validation script and mechanical table generation. Do not read subagent transcripts into this session.
- Post a one-line status at each phase change and every few minutes while waiting on subagents.

## Verification

```bash
python scripts/ucf/validate.py
```

It must print per-subset counts and pass checks 1 to 7 on everything that exists so far (ISO base at minimum). Report any record the library cannot place.

## Stop conditions

- Stop after the ISO base domain tables and the validator are done and NIST and DPDPA atoms plus proposed mappings exist. Do not start the signed-data load into the app (WP 5.1) or any questionnaire change.
- Stop and ask if you find a conflict between the repo's DPDPA pack and the Act that would change an id. Ids are persisted and Saqlain verifies legal items himself.

## Report back

Append `## Results` to this file: what exists and where, counts per subset from the validator, the list of ISO clause paraphrases marked `needs_verification`, records that could not be placed cleanly, merges and splits you made to Annex A controls, and anything you could not do.
