# P6-2c: Draft ISO 27001 (Annex A + clauses 4-10) and NIST CSF test criteria for Saqlain's sign-off

**Goal.** Same deliverable as P6-2a (`tasks/handoffs/2026-09-25-p6-2a-dpdpa-test-criteria-draft.md`, read its "Criteria-writing rules" and its Results for the house style), for ISO/IEC 27001:2022 and NIST CSF 2.0. Review sheets in `tasks/criteria-review/`, draft modules in `app/frameworks/criteria/`. Nothing is attached to a `Control` or reaches a prompt (P6-2b-style conversion happens after sign-off).
**Decisions (Saqlain, 2026-09-25):** Saqlain signs off ISO and NIST criteria. ISO clauses 4-10 (P5-7) are folded into this pass. D-P6-J: ISO control descriptions are rewritten in our own words in the same pass.
**Branch/worktree:** `claude/p6-2c-iso-nist-criteria` at `/Users/saqlainmomin/dpdpa-gap-tool-p6-2c`.

## Independence rule (non-negotiable, D-P5-9-C)
Do not open, grep, list or read: `validation/**`, `tasks/handoffs/*p5-9*`, `docs/plans/2026-09-24-002-*`, `scripts/seed_test_companies.py`, `scripts/test_ground_truth.json`, `scripts/seed-v2-prompt.md`, any `answer_key.json`. Criteria come from the standards and the repo's requirement definitions only. If a search returns such content, discard it and say so.

## Drafting phase (two dedicated drafters: one ISO, one NIST, running in parallel)

- **ISO drafter:** ISO 27001:2022 clauses 4.1-10.2 (incl. Amd 1:2024 climate text in 4.1/4.2; ~25 new ids `ISO.C4.1`, `ISO.C6.1.2`, `ISO.C9.2` etc.) plus all 93 Annex A controls. Writes `app/frameworks/criteria/iso27001_draft.py` only.
- **NIST drafter:** all 94 NIST CSF requirements in the pack. Writes `app/frameworks/criteria/nist_csf_draft.py` only.
- Work domain by domain; after each domain re-read it against the rules.

Requirement definitions: `app/frameworks/definitions/iso27001.py`, `app/frameworks/definitions/nist_csf.py` (controls, questions, `EvidenceRequest` document_type keys — use those keys in `evidence_hint` where they fit). DPDPA exemplar: `app/frameworks/criteria/dpdpa_draft.py`, `tasks/criteria-review/dpdpa-criteria-v1.csv`.

### Rules (in addition to P6-2a's rules 1-6)
- 2-5 criteria per requirement, at least one `design`; `operating` wherever the outcome is about doing something (records, logs, reviews performed, tests run).
- **ISO copyright (D4).** ISO text is licence-restricted. Never reproduce clause or control text beyond a few words needed for precision. Do not copy the repo's existing descriptions (they are near-verbatim ISO). `source_basis` cites by number only: `ISO/IEC 27001:2022 cl.6.1.3(d)`, `ISO/IEC 27001:2022 A.5.15`, `ISO/IEC 27002:2022 5.15 (guidance)`. A criterion that rests only on 27002 guidance ("should") or on practice is `drafter_confidence` medium at most; a `shall` in 27001 (clauses, or the Annex A control statement once applicable) can be high.
- **ISO own-words description.** For every ISO requirement (Annex A and clauses), write `own_words_description`: 1-2 sentences, own words, same scope as the control, no ISO phrasing.
- **ISO clauses.** Also author the requirement itself: `title` (short, own words), `own_words_description`, `criticality` (critical/high/medium/low), `section` (`context|leadership|planning|support|operation|evaluation|improvement`). Merge 6.1.1-6.1.3 only if you judge it better; default is separate ids for 6.1.1, 6.1.2, 6.1.3 and one id each for 7.5 and 9.2. Note 2022 numbering (10.1 continual improvement, 10.2 nonconformity), 6.3 planning of changes, 9.3 split into sub-clauses.
- **NIST.** CSF 2.0 (NIST CSWP 29, Feb 2024) is a voluntary outcome framework: the subcategory outcome is the basis (`NIST CSF 2.0 GV.OC-01`); implementation examples (`CSF 2.0 IE GV.OC-01 Ex2`) or SP 800-53 Rev.5 informative references (`SP 800-53r5 CP-2`) may support criteria but cap confidence at medium unless the criterion restates the outcome itself. Primary sources: nvlpubs.nist.gov / csrc.nist.gov only; record URLs. Note any CSF 2.0 subcategory in the covered categories that the repo pack omits or misnumbers (the pack has 94 of 106) — list it in findings, do not add it.
- `in_force_note`: ISO: blank unless a version/transition point matters (e.g. Amd 1:2024). NIST: blank unless there is a version point.
- `drafter_confidence` low wherever interpretation is genuinely uncertain or the repo's definition departs from the standard (note `[repo says ...]` in `source_basis`).

### Output (each drafter writes these files only)
1. The draft module, in the style of `dpdpa_draft.py` (a `_criteria(...)` helper filling a `*_REVIEW_META` dict of `criterion_id -> (confidence, in_force_note)`):
   - ISO: `ISO27001_CRITERIA_DRAFT: dict[str, tuple[TestCriterion, ...]]` (clause ids first, then Annex A in framework order), `ISO27001_CRITERIA_REVIEW_META`, `ISO27001_CLAUSE_REQUIREMENTS_DRAFT: dict[str, dict]` (title, description, criticality, section, reference) and `ISO27001_OWN_WORDS_DRAFT: dict[str, str]` (every ISO id -> own-words description).
   - NIST: `NIST_CSF_CRITERIA_DRAFT`, `NIST_CSF_CRITERIA_REVIEW_META`.
   - Module docstring lists sources (URL + retrieval date) and the house-style notes. It must import cleanly: `.venv/bin/python -c "import app.frameworks.criteria.<module>"`.
2. A report at `/private/tmp/claude-501/-Users-saqlainmomin-dpdpa-gap-tool/3fbbda88-d5f4-48e7-89dc-b9c7d17b532e/scratchpad/criteria/<iso27001|nist_csf>-report.md`: counts (requirements, design/operating, high/medium/low), sources, findings (repo mismatches, omissions, numbering issues), 15 lowest-confidence criteria with reasons, independence confirmation.

Do not edit any other repo file, do not commit, do not touch the other framework's module.

## Assembly phase (after both drafts land)
- Generalise `scripts/export_criteria_review.py` to `--framework dpdpa|iso27001|nist_csf` (DPDPA output byte-identical to the current CSV). Outputs: `tasks/criteria-review/iso27001-criteria-v1.csv` (clauses first, then Annex A in framework order), `tasks/criteria-review/iso27001-descriptions-v1.csv` (`requirement_id, requirement_title, source, current_reference, own_words_description, decision, edited_description, reviewer_note`), `tasks/criteria-review/nist-csf-criteria-v1.csv`. Update `tasks/criteria-review/README.md`.
- Tests `tests/test_p6_2c_iso_nist_criteria.py`: same checks as P6-2a (coverage of every pack id + clause ids, 2-5 per req, ≥1 design, id pattern/uniqueness, kind, non-empty fields, meta complete, `practice`/guidance-only never `high`, byte-identical export twice, no `app/` import of the draft modules outside `app/frameworks/criteria/`), plus a verbatim-copy guard: no ISO own-words description equals or contains the repo's current description.
- Verify: full `.venv/bin/pytest -q` (known failures only: `test_scenario_10_engagement_rollup_and_tracker_page`, `test_scenario_13_structural_guards`, flaky `test_longitudinal_demo` scenario 9 and `test_workpaper` smoke), `git diff main...HEAD --stat` limited to the files above + this handoff.

## Results
Assembled 2026-09-25. Sheets: `tasks/criteria-review/iso27001-criteria-v1.csv`, `iso27001-descriptions-v1.csv`, `nist-csf-criteria-v1.csv` (README updated). Exporter: `python scripts/export_criteria_review.py --framework dpdpa|iso27001|nist_csf`. Tests: `tests/test_p6_2c_iso_nist_criteria.py`. No criteria content was changed at assembly.

### Counts

| Framework | Requirements | Criteria | Design / operating | High / medium / low | `in_force_note` set |
|---|---|---|---|---|---|
| ISO 27001 clauses 4-10 (new `ISO.C*`) | 25 | 78 | 43 / 35 | 61 / 16 / 1 | |
| ISO 27001 Annex A | 93 | 230 | 109 / 121 | 145 / 80 / 5 | |
| **ISO 27001 total** | **118** | **308** | **152 / 156** | **206 / 96 / 6** | 34 |
| **NIST CSF 2.0** | **94** | **312** | **165 / 147** | **172 / 132 / 8** | 3 |

ISO clause requirements: 25 (9 critical, 13 high, 3 medium); separate ids for 6.1.1/6.1.2/6.1.3, one id each for 7.5, 9.2 and 9.3; 2022 numbering (6.3 changes, 10.1 improvement, 10.2 nonconformity). Own-words descriptions: all 118 ISO ids.

### Sources

- ISO/IEC 27001:2022 (3rd ed., 2022-10), clauses 4-10 and Annex A, cited by number only (https://www.iso.org/standard/27001). The ISO drafter reports checking numbering, lettered items, `shall` status and the Table A.1 list against a licensed copy Saqlain supplied; nothing reproduced.
- ISO/IEC 27001:2022/Amd 1:2024 (https://www.iso.org/standard/88435.html): **not verified** against the amendment text (the supplied copy is unamended). The two climate criteria are capped: C4.1.TC2 medium, C4.2.TC4 low.
- ISO/IEC 27002:2022 (https://www.iso.org/standard/75652.html), cited as "(guidance)", capped at medium.
- NIST CSWP 29, CSF 2.0, 26 Feb 2024: https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf
- CSF 2.0 Core with Implementation Examples (NIST CPRT JSON export): https://csrc.nist.gov/extensions/nudp/services/json/nudp/framework/version/csf_2_0_0/export/json?element=all . CPRT maps to SP 800-53r5 at family level only; the few 800-53 control numbers cited are the drafter's reading and are support only (medium).
- Repo definitions: `app/frameworks/definitions/iso27001.py`, `app/frameworks/definitions/nist_csf.py` (ids, titles, `EvidenceRequest` document_type keys).

### Key findings

**NIST pack vs CSF 2.0**
1. **RS.CO.04 is not a CSF 2.0 subcategory** (withdrawn; CPRT: incorporated into RS.MA-01/RS.MA-04). The pack text resembles CSF 1.1 RS.CO-05, now in RS.CO-03, so it duplicates RS.CO.03. Both criteria low.
2. **13 CSF 2.0 subcategories in the covered categories are missing** (93 real + RS.CO.04 = 94; 93 + 13 = 106): GV.RM-05, GV.RM-06, GV.RM-07, GV.SC-06, GV.SC-07, GV.SC-08, GV.SC-09, GV.SC-10, ID.RA-07, ID.RA-08, ID.RA-09, ID.RA-10, ID.IM-04. Most consequential: ID.IM-04 (nothing asks whether an IR plan exists), ID.RA-07 (no change management) and GV.SC-07 (no supplier monitoring). Listed, not added.
3. **Outcome text departs from CSF 2.0** (criteria testing the CSF 2.0 outcome are low): GV.OC.05 ("prioritized" vs "understood and communicated"), GV.OV.03 (lessons-learned vs performance evaluated), PR.PS.01 (narrowed to network infrastructure, CSF 1.1-style), GV.RR.01 (drops "ethical, and continually improving"). Minor drift in GV.OC.02 and GV.OC.04.
4. **Titles contradict their outcome** (and the questionnaire question is generated from the title): DE.AE.06, DE.AE.08 (swapped declaration/anomaly), DE.AE.02, DE.AE.03 (correlation/aggregation shifted), GV.OV.02, ID.AM.08, PR.AT.02, RS.MA.02, RS.CO.02. These rows carry `[repo title ...]` in `source_basis` but are rated high/medium because the criterion follows the pack description, which matches CSF 2.0; DE.AE.06.TC1 and DE.AE.08.TC1 are medium.
5. `definitions/nist_csf.py` docstring is stale ("82 subcategory controls", 20/13/21/9/12/7; actual 94, 23/16/22/11/14/8).

**ISO pack omissions**
6. Pack descriptions drop parts of the 2022 controls: A.5.1 (planned review, topic-specific policies; A.5.1.TC3 low), A.5.9 (asset owners; A.5.9.TC2 low), A.6.1 (legal/ethical and proportionality qualifiers; A.6.1.TC4 low). Narrower scope in A.5.14, A.5.34, A.5.35, A.6.3, A.6.4, A.6.5; 2013-style phrasing in A.5.2, A.5.4-A.5.6; A.8.5 adds "established". Small title differences in A.5.21, A.5.34, A.8.1. All 93 ids match Table A.1.
7. Pack descriptions (and `QuestionDef.guidance`) are near-verbatim ISO text (D4 risk; e.g. A.5.12, A.5.13, A.5.33, A.8.9, A.8.34). The own-words sheet replaces them at conversion.
8. The pack had no clause 4-10 requirements (P5-7); the 25 `ISO.C*` ids are new.

**Missing evidence keys**
9. ISO clause criteria need evidence with no `document_type` key: context/issues register, interested-parties register, objectives register, measurement plan, corrective action log, document control procedure, communication plan (named in free text; adding keys is a P6-2b decision).
10. NIST: no `EvidenceRequest` maps DE.AE.07, PR.IR.04 or RS.CO.04; their hints name an evidence form.

**Amd 1:2024 not verified** against the amendment text (see Sources).

### Lowest-confidence rows (review first)

**ISO 27001**, all 6 low: C4.2.TC4 (Amd 1 climate note is a NOTE and unverified), A.5.1.TC3, A.5.9.TC2, A.6.1.TC4 (test parts the pack description omits), A.5.21.TC2 (what evidences an ICT supply-chain assessment is open), A.7.1.TC3 (provider assurance vs own perimeter for remote/cloud-only orgs). Report top 15 adds (medium): C4.1.TC2 (Amd 1 unverified), C9.2.TC1 (full-scope audit cycle is a CB norm), C6.3.TC2 ("change" undefined), C10.1.TC2 (improvement-rate threshold), C7.4.TC2 (goes beyond "determine"), A.7.4.TC2 (small office without CCTV), A.6.1.TC3 (re-screening interval), A.8.8.TC4 (annual pentest is guidance/practice), C4.3.TC3 (justifying exclusions against 4.1/4.2 is a reading).

**NIST CSF 2.0**, all 8 low: RS.CO.04.TC1, RS.CO.04.TC2 (withdrawn subcategory), GV.OC.05.TC4, GV.OV.03.TC4, PR.PS.01.TC4 (pack wording not CSF 2.0), GV.RR.01.TC3 (tests CSF 2.0 wording the pack omits), PR.DS.10.TC3 (evidence of data-in-use isolation unsettled), RC.RP.04.TC2 ("post-incident operational norms" undefined). Report top 15 adds (medium): DE.AE.06.TC1, DE.AE.08.TC1 (title/question mismatch), PR.DS.10.TC1 (abstract outcome), PR.IR.04.TC1 (IE-derived, no evidence request), GV.RR.03.TC2 (allocation vs adequacy), GV.OC.01.TC1 ("understood" not observable), PR.AA.04.TC3 (token lifetime/rotation is practice).

### Assembly notes

- `dpdpa-criteria-v1.csv` was **not** regenerated. The generalised exporter's default DPDPA output is byte-identical to main's exporter, but both differ from the committed CSV at one requirement title: P6-0f (7bddbe9) retitled CH2.NOTICE.1 to "Notice accompanying the consent request" after the sheet was exported. Pre-existing drift; left for Saqlain to decide (regenerating overwrites nothing yet, the review columns are blank).
- Exporter runs twice give byte-identical files (tested). `git grep "iso27001_draft\|nist_csf_draft" -- app` finds nothing outside `app/frameworks/criteria/` (tested).

### Independence

Held. Both drafters and the assembler did not open, grep, list or read `validation/**`, `tasks/handoffs/*p5-9*`, `docs/plans/2026-09-24-002-*`, `scripts/seed_test_companies.py`, `scripts/test_ground_truth.json`, `scripts/seed-v2-prompt.md` or any `answer_key.json`; no search returned such content. Criteria rest on the standards and the repo requirement definitions only.

PR: _see below_
