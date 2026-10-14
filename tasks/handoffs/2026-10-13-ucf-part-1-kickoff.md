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

## Results

Run date 13 Oct 2026, branch `claude/ucf-part-1`. Nothing is committed or loaded into the app. Drafting subagents ran on Sonnet, as the session instruction said (this file says Opus). All three tracks reached "signable tables plus validator". `python3.13 scripts/ucf/validate.py` exits 0 and passes checks 0 to 7 on everything that exists.

### What exists and where

| Path | What |
|---|---|
| `docs/ucf/drafts/FORMAT.md` | The data contract the agents wrote to. Read this first |
| `docs/ucf/drafts/` | 18 domains, roles, 265 records, 692 atoms, 195 control skeletons, 723 mapping rows, 195 field rows (CSV) |
| `docs/ucf/drafts/notes_*.md` | Agent notes: DPDPA atom flags, NIST and DPDPA mapping judgment calls |
| `docs/ucf/signoff/` | One table per domain (GOV is two files), plus `README.md` with counts. Regenerate with `python3 scripts/ucf/make_signoff.py` |
| `app/frameworks/ucf/` | Schema and loader (stdlib only). Nothing outside it reads it |
| `scripts/ucf/validate.py`, `make_signoff.py` | The validator and the sign-off generator |

Rows: ISO 125 controls (297 atoms over 93 Annex A records and 25 clause records); NIST 297 atoms over 106 subcategories, 307 rows, 25 new controls plus 2 added after review (27 in all); DPDPA 98 atoms over 41 requirements, 119 rows, 43 new controls (8 remainder slots, 35 privacy-only). Mapping coverage: ISO 297 full; NIST 295 full, 12 partial; DPDPA 100 full, 19 partial. No `none` rows: every record found a home.

### Counts per framework subset (validator output)

| Subset | Controls shown | Records covered | Atoms mapped |
|---|---|---|---|
| ISO 27001 | 125 | 118 of 118 | 297 of 297 |
| NIST CSF | 103 | 106 of 106 | 297 of 297 |
| DPDPA | 54 | 41 of 41 | 98 of 98 |
| ISO + NIST | 152 | 224 of 224 | 594 of 594 |
| ISO + DPDPA | 168 | 159 of 159 | 395 of 395 |
| NIST + DPDPA | 149 | 147 of 147 | 395 of 395 |
| All three | 195 | 265 of 265 | 692 of 692 |

These are controls, not questions to ask in the questionnaire (depth tiers still apply). They answer Q8. The all-three total (195) is inside the first estimate of 150 to 250, not below it. ISO plus NIST is 152, and NIST adds 27 controls on top of ISO, which fits your overlap point. Per-domain counts are in `docs/ucf/signoff/README.md`.

### ISO clause paraphrases marked `needs_verification`

All 25 clause records (68 atoms) in `records_iso_clauses.csv` and `atoms_iso.csv`, written from knowledge, none checked against the standard: 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 6.1.1, 6.1.2, 6.1.3, 6.2, 6.3, 7.1, 7.2, 7.3, 7.4, 7.5 (one record for 7.5.1 to 7.5.3), 8.1, 8.2, 8.3, 9.1, 9.2, 9.3, 10.1, 10.2. 4.1 and 4.2 include the 2024 climate wording. 9.2 and 9.3 are single records, not split by sub-clause. The `needs_verification` flag lives on atoms, not on control fields. Controls that are clause-derived are marked "Clause only" in their `note`.

### Merges and splits to Annex A and clauses

Splits (test differs): A.5.18 into IAM-04 provision, IAM-05 review, IAM-06 removal; A.5.19 into SUP-01 register and tiering and SUP-02 due diligence; A.5.26 into INC-03 response and INC-04 notification; A.5.30 into RES-02 objectives and plans and RES-03 testing; A.6.3 into PPL-03 awareness and PPL-04 role-based training; A.8.8 into OPS-04 vulnerabilities and OPS-05 penetration testing; A.8.13 into RES-04 backup and RES-05 restore testing; A.8.15 into OPS-01 log production and OPS-02 log protection; A.8.24 into CRY-01 use and CRY-02 key management; clause 6.1.3 into RSK-02 treatment plan and RSK-03 applicable-controls statement.

Merges (clause with Annex A): 5.2 with A.5.1 into GOV-06; 5.3 with A.5.2 into GOV-07; 7.3 with the all-staff part of A.6.3 into PPL-03; 9.2 with A.5.35 into RSK-09. No two Annex A controls were merged.

Changes I made after review: UC-OPS-03 narrowed to monitoring and raising alerts (its goal, statement, test and question rewritten); alert analysis, correlation and routing moved to the new NIST slot UC-OPS-41 (8 NIST atoms). Recovery management (criteria, roles, start and end of recovery) moved from UC-INC-03 to the new NIST slot UC-INC-42 (8 atoms), because INC-03 carried 18 NIST atoms and OPS-03 carried 16. After the moves INC-03 carries 10 NIST atoms and OPS-03 carries 8. INC-03 still holds basic recovery for the ISO atom, so check the INC-03 and INC-42 boundary when you sign. Importance of OPS-05 and PPL-04 set to high (they inherited critical from the parent record).

### Records and atoms that could not be placed cleanly

No record is unplaced. Judgment-heavy rows (all marked full or partial, listed in `notes_nist_mapping.md` and `notes_dpdpa_mapping.md`):
- About ten NIST atoms are marked full but are soft: DE.CM-01-c, DE.AE-07-b, DE.AE-06-c, GV.SC-06-b, PR.PS-06-d, ID.IM-01-a, DE.CM-03-c and similar. NIST coverage of 295 full of 307 rows is high because the slots were written for the atoms; treat the soft ones as the places to challenge.
- DPDPA SECURITY.1-a and -b are umbrella asks, mapped partial to GOV-04 and OPS-01. BN.NOTIFY.3-a and -c map full to INC-01, which is generous.
- Three immaterial remainders: NIST GV.OC-03-b (RSK-06), NIST PR.AT-01-d (PPL-03), DPDPA SECURITY.1-a to RES-04.
- The signed inactivity-erasure criterion (conditional, with a warning period) has no atom. It sits in UC-AST-70 fields. Add an atom if you want it traceable.
- Soft overlaps to decide: UC-PGV-04 and UC-RSK-09; PNC-05, 06, 07 share source criteria; DPDPA CONSENT.2 and CM.GRANULAR.1 duplicate each other.
- Most base-control change suggestions in the notes files were not applied (RSK-06 owner, PPL-03 effectiveness checks, AST-01 scope, GOV-06 context, SUP-03 access scope, INC-04 affected individuals, OPS-01 sensitive-data events). Decide at sign-off.

### Pack against Act: your legal items (no id would change, so the stop condition did not trigger)

Flags from the DPDPA agent, for you to verify (references only): CONSENT.3 and CONSENT.4 stored as s.6(6) and 6(8) to (9) while the consent manager text may sit at s.6(7); NOTICE.3, MINIMIZE.1, SECURITY.1 and CHILD.1/2 references the signed criteria already call earlier errors; CHILD.3 stored as a bare "Section 9" though the age and guardian checks come from Rules r.10 to r.12; SECURITY.2 requires encryption though the Rules accept any of four measures; CORRECT.2 scopes erasure narrowly; CB.TRANSFER.2 and .3 require transfer contracts and localization that are practice, not s.16(1) text; the 72-hour breach period, incident plan and breach register come from the Rules and practice; CM.RECORDS.2 "refresh after a reasonable period" has no basis in the Act and was not atomized. Full list in `notes_dpdpa_atoms.md`.

### Schema choices you did not specify (confirm or change)

1. A `question` field was added to each control. Check 6 needs a client-facing question and `how_to_ask` is direction plus a probe. The curated DPDPA text seeds most privacy questions; the five compound questions (CONSENT.2, NOTICE.1, MINIMIZE.3, TRANSFER.1, TRANSFER.2) were split across controls.
2. Mapping rows gained `record_id`, `remainder_immaterial` and `immaterial_reason`.
3. "No source requirement maps to the same control twice" is enforced per atom. 236 (record, control) pairs are reached by two or more atoms of one record; that is allowed and reported as INFO.
4. `key_settings` is `layer: setting | layer: setting`. Check 4 requires any number with a unit in shown text to appear there under `base` or a selected framework. Existing numbers: DPDPA 72-hour intimation, 90-day grievance cap, one-year logs, 12-month review, three-year inactivity erasure, child under 18, plus a few 12-month cycles in base controls.
5. Id ranges: ISO 01 to 39, NIST 40 to 69, DPDPA 70 to 99 in base domains; privacy domains number from 01.
6. A control's source reference is derived from its mapping rows.

### Not done, or only partly

- ISO scope question content (WP 3.1 mentions it) was not touched. Kickoff Track 1 did not list it.
- Re-keying the 728 signed criteria was not done. They seeded `test` and `expected_evidence` by hand per control. Some signed criteria are not carried (for example PNC-10 re-confirmation at an interval).
- `ids.lock.json` is not written. Run `validate.py --write-lock` at first signed version.
- Not verified by the validator: the "strictest among selected frameworks" rule (no number conflicts exist yet because base controls carry no framework numbers), numbers written as words, and compound questions beyond the heuristics. Eleven earlier compound-question warnings were fixed; none remain.
- Control fields were drafted by Sonnet agents and spot-checked only. Several controls were flagged by their writers as doing two jobs: PHY-02, PHY-09, PHY-12, SUP-05, SUP-06, INC-01, INC-04, RES-06, IAM-03, AST-02, AST-07, GOV-16, RSK-08, PGV-03, PSC-02, GOV-41, RSK-41, RSK-42, AST-43, CRY-40, NET-40, INC-42, SUP-40, RES-42. Consider these at sign-off.
- Sign-off tables run up to 18 controls (AST, 18; GOV has 24 and is split in two files). The "about 15" target is exceeded in AST and GOV.

### Addendum, 13 Oct 2026 (after your first review pass)

- **Clauses checked against the ISO PDF** (`~/Downloads/ISO IEC 27001 2022.pdf`, the 2022 edition without Amendment 1:2024): 14 of 25 clause records matched; 11 were adjusted, 8 for real errors or gaps (5.1, 6.1.2, 6.1.3, 7.4, 8.1, 9.1, 9.2, 9.3). Atoms, mappings and the affected controls (GOV-05, 14, 16, 17, 18; RSK-01, 03, 09) were corrected. Annex A numbering matches (93 of 93). The climate wording in 4.1 and 4.2 is still unverified. `needs_verification` flags are unchanged: they are yours to clear.
- **Statements are role-neutral.** All 195 statements were rewritten after your feedback that compliance cannot depend on a named role doing the work. The owner lives only in `owner_role`. "Top management" stays where the requirement itself is about management. The validator now fails any statement that names a listed role (CHECK 2) and warns on generic implementers. Only the `statement` column changed, apart from one `good_looks_like` line in UC-IAM-05.
- Totals are unchanged (195 controls, 725 mapping rows, 694 atoms). The review page and sign-off tables were regenerated; `library_version` is unchanged so saved review decisions in the browser still apply.

### Addendum, 14 Oct 2026 (after your exported review comments)

- Your 35 Change comments: 30 were already resolved by the 13 Oct role-neutral rewrite (your page predated it); 3 needed small wording (GOV-08, RSK-02, RSK-42), 2 were content asks (RSK-10 rewritten as "Practice checked against policy"; GOV-14 is two jobs and waits for your call, see D14). 33 controls were edited in all, including a sweep of consultant-facing text. `library_version` is now 0.0.2-draft; the review page keeps its old browser key so saved decisions survive.
- The 16 DPDPA legal items default to "Confirmed (provisional)" until you have outside information. This is a placeholder, not a legal verification; ids and pack text are unchanged.
- D09 to D12 now carry plain-language explanations on the review page. D11 has a Split or Keep choice per control. New decisions D14 to D18 (GOV-14 and a new INC-43, small calls, RSK-10 independence, management words and the owner badge, authority of signed criteria versus the drafted test).
- Not applied, waiting for you: the 17 proposed splits (library would grow from 195 to about 215), GOV-14 narrowing plus UC-INC-43, the D09 text and mapping fixes, the primary rule R2, the validator guard on generic implementers.
