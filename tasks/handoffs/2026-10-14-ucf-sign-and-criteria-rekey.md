# Handoff: sign the UCF library, lock the ids, prepare the criteria and scope re-key

For a fresh Claude Code session in the terminal. Assume no memory of earlier sessions. Work in the worktree `/Users/saqlainmomin/dpdpa-ucf` on branch `claude/ucf-part-1`. Read this file first, then the files under Key files. The two previous handoffs are `tasks/handoffs/2026-10-13-ucf-part-1-kickoff.md` and `tasks/handoffs/2026-10-14-ucf-part-1-apply-decisions.md`. Their `## Results` sections describe what was built.

## Goal

The unified control framework (UCF) library is signed. Turn that into a locked, committed version, then prepare the next two re-keys so Saqlain can decide them in one review round.

Done means all six of these:

1. **Sign-off recorded and locked.**
   - `docs/ucf/drafts/library.json` says the library is signed: `library_version` `1.0.0`, `status` `signed`, and the signer and date.
   - The sign-off tables show it.
   - `ids.lock.json` is written, and the validator enforces it.
2. **Committed and in a PR.** The signed library, plus all the uncommitted round-2 work, is committed on `claude/ucf-part-1`, pushed, and a docs-and-data PR is open. Saqlain merges; you never merge.
3. **Criteria map drafted.** A script produces a draft criteria-to-control map:
   - Every signed test criterion is attached to a unified control.
   - Where the map is unambiguous (the criterion's record maps to one control), the attachment is automatic.
   - Where the record maps to more than one control, the script lists a proposed control per criterion with a one-line reason, and leaves the choice open.
4. **ISO scope proposals re-keyed.** The scope applicability proposals are re-keyed from Annex A ids to unified control ids, as a draft data file. Nothing is wired into the app.
5. **One review page.** A single page lets Saqlain decide the ambiguous criteria and the scope proposals, plus one question: are four ISO scope questions enough? The page is smoke-tested.
6. **Results written.** A `## Results` section is appended to this file. Stop there.

Do not load anything into the app; that is WP 5.1.

## Current state

**The library.** It lives as draft CSVs in `docs/ucf/drafts/` (format in `FORMAT.md`), library version `0.0.3-draft`:
- 211 unified controls, 265 framework records (ISO 27001 clauses and Annex A, NIST CSF 2.0, DPDPA), 697 atoms (single source asks), 730 mapping rows.
- Controls per framework subset: ISO 134, NIST 112, DPDPA 54, all three 211.
- `/opt/homebrew/bin/python3.13 scripts/ucf/validate.py` exits 0 with zero warnings.

**What Saqlain approved.** On 14 Oct 2026 he approved everything on the review page (`tasks/2026-10-13-ucf-review.html`) with no comments: all 211 controls, all decision cards D01 to D20, all 25 ISO clause records, and the 16 DPDPA legal items. That approval is the sign-off of every domain table in `docs/ucf/signoff/`.

**Legal items are not legally verified.** The 16 items stay "confirmed provisionally" until he has outside information. Record this in the sign-off note; it does not block signing.

**Nothing is committed since `2d45e2b`.** All of round 2 is uncommitted in the worktree: the data, generators, sign-off tables, the review page, FORMAT.md and the smoke test. `git status` shows it.

**The signed test criteria.** There are 728, generated from signed sheets and keyed by source record id:
- 230 ISO in `app/frameworks/criteria/iso27001.py`.
- 348 NIST in `nist_csf.py`.
- 150 DPDPA in `dpdpa.py`.

Each `TestCriterion` has `id` (`<record>.TC<n>`), `stmt`, `kind` (design or operating), `hint` and `basis`. They cover 240 records. With the current mappings, **98 of those records map to more than one control, holding 345 criteria**. Those need a per-criterion choice; the other 383 attach automatically. Recompute these numbers from the data; don't trust them.

**The authority rule (decision D18).** The signed criteria are the authoritative list of tests under each control, and keep their original ids. The `test` paragraph in each control's fields is only a readable summary. ISO clauses 4 to 10 have no signed criteria; their drafted `test` text stands.

**ISO scope questions.** There are four, in `_ISO_SCOPE_QUESTIONS` in `app/frameworks/definitions/iso27001.py` (around line 1003): management system scope, cloud use, software development, physical premises.
- Answers trigger applicability proposals that name Annex A ids. For example, no cloud proposes A.5.23 as not applicable, and fully remote proposes A.7.1 to 7.6, 7.8, 7.11 and 7.12.
- Since then, splits moved Annex A asks across several controls. A.5.23 now maps to UC-SUP-06 and UC-SUP-07; A.7.2 maps to UC-PHY-02 and UC-PHY-13.
- Clauses 4 to 10 are never excludable.

## Key files

| Path | What |
|---|---|
| `/Users/saqlainmomin/dpdpa-ucf/docs/ucf/drafts/FORMAT.md` | Data contract. Read first |
| `/Users/saqlainmomin/dpdpa-ucf/docs/ucf/drafts/` | The data: `controls_*`, `fields_*` (`csv.QUOTE_ALL`), `atoms_*`, `mappings_*`, `records_*`, `library.json` |
| `/Users/saqlainmomin/dpdpa-ucf/scripts/ucf/validate.py` | The validator. `--write-lock` writes `ids.lock.json` (only if check 7 passes). Check 7 enforces the lock only when the lock's `library_version` equals `library.json`'s |
| `/Users/saqlainmomin/dpdpa-ucf/scripts/ucf/make_signoff.py` | Regenerates `docs/ucf/signoff/*.md` and its README (header says "Draft for sign-off") |
| `/Users/saqlainmomin/dpdpa-ucf/scripts/ucf/make_review_html.py`, `review_template.html` | Round 1 and 2 review page generator. Reuse its style, browser-state and export pattern for the new page |
| `/Users/saqlainmomin/dpdpa-ucf/scripts/ucf/authoring/smoke_review_page.js` | jsdom smoke test pattern. Run with `JSDOM_PATH=/Users/saqlainmomin/railPVC/frontend/node_modules/jsdom node ...` |
| `/Users/saqlainmomin/dpdpa-ucf/scripts/ucf/authoring/dump_sources.py`, `brief.py` | Dump repo records, criteria and evidence requests to JSON (`UCF_SRC_DIR`); per-domain briefs |
| `/Users/saqlainmomin/dpdpa-ucf/app/frameworks/criteria/{iso27001,nist_csf,dpdpa}.py` | Signed criteria. Generated; never edit |
| `/Users/saqlainmomin/dpdpa-ucf/app/frameworks/definitions/iso27001.py` | ISO scope questions and their Annex A proposals. Read only |
| `/Users/saqlainmomin/dpdpa-ucf/app/frameworks/ucf/` | UCF schema and loader (stdlib). Nothing outside reads it yet |
| `/Users/saqlainmomin/dpdpa-ucf/docs/plans/2026-09-21-002-revised-implementation-plan.md` | Plan. Sections 7.4 and 7.5, and WP 3.1 to 3.4, cover this work |

## Constraints (decided; do not reopen)

**Library rules.**
- One control = one requirement = one test.
- Statements are role-neutral; the owner lives only in `owner_role`.
- Statements and questions never name a framework or carry control codes.
- Own wording, American spelling, short sentences, no em dashes.

**Signing is a version event.**
- Set `library_version` to `1.0.0` and `status` to `signed`.
- Add `signed_by: "Saqlain Momin"` and `signed_on: "2026-10-14"`, the day he approved. If the loader rejects extra keys, extend the schema minimally.
- Then run `validate.py --write-lock`. After that, any id removal or title or domain change needs a version bump.
- Do not change control content while signing.

**Criteria ids are permanent.**
- Never renumber, edit or delete a signed criterion, and never edit the generated criteria modules.
- The new map is a separate data file, for example `docs/ucf/drafts/criteria_map.csv` with columns `criterion_id, record_id, unified_control_id, basis, reason`. `basis` is `auto` (single control), `proposed` (ambiguous, awaiting Saqlain) or `decided`. Document the file in FORMAT.md.
- A criterion attaches to exactly one control. If one truly tests two, flag it; don't duplicate it.

**How to propose a control for an ambiguous criterion.**
- Match the criterion text against the atoms and control statements of that record's mapped controls. A script or careful reading in this session is fine.
- No LLM API calls from code, and no live spend.
- If subagents help with the 345, use Sonnet, one per framework, each writing its own output file. Don't read their transcripts into this session.

**Scope proposals are data only.**
- Write e.g. `docs/ucf/drafts/scope_proposals.csv` (question, answer, unified_control_id, reason).
- When an Annex A id now maps to several controls, list each one whose atoms come only from that Annex A control or from other excludable ones.
- Never propose a control that carries a clause 4 to 10 atom, or one that a DPDPA or NIST record also needs. Note those cases for Saqlain.
- Do not edit `iso27001.py`; wiring is WP 5.5.

**Off limits.** Never read `validation/companies/*/answer_key.json`. Do not edit `app/routers/*`, templates, prompts, scoring, or `tasks/todo.md`.

**Git.**
- Commit on `claude/ucf-part-1`, push, and open the PR yourself. Never merge.
- No Claude or Codex attribution lines in commits or PRs (no Co-Authored-By, no "Generated with").
- Commit the signed library first, as its own commit, before the re-key work. Commit the re-key drafts separately; they can share the PR.

**Reporting.** Post a one-line status at each phase change. Report to Saqlain in plain language, outcome first.

## Plan

1. **Branch check.** `git status`; branch `claude/ucf-part-1`. Run the validator: it must exit 0.
2. **Sign.** Update `library.json`. Make `make_signoff.py` show "Signed 1.0.0 by Saqlain Momin on 14 Oct 2026" instead of "Draft for sign-off". Note in the README that the legal items are confirmed provisionally. Regenerate. Run `validate.py --write-lock`, then the validator again: check 7 must report the lock as enforced. Commit (data, generators, sign-off, review page, lock), push, and open the PR.
3. **Criteria map script.** For example `scripts/ucf/make_criteria_map.py`:
   - Read the signed criteria via the app modules or `dump_sources.py`, and the mappings.
   - Write `criteria_map.csv` with `auto` rows and `proposed` rows.
   - Print counts per framework: total, auto, proposed, and records with no control.
   - Also produce a per-control count of criteria, so controls with zero criteria are visible. For example, ISO clause controls and new split halves whose criteria all went to the partner. List them in Results as gaps.
4. **Scope proposals.** Write the re-keyed scope proposals file and the notes on any proposal that can no longer be clean.
5. **Review page.** For example `tasks/2026-10-14-ucf-rekey-review.html`, built by a generator script:
   - One card per ambiguous criterion: its text, kind, the record, the candidate controls with titles and statements, and the proposed one pre-selected. A choice of control, plus a note.
   - One card per scope proposal: Approve or Change.
   - One decision card: whether four ISO scope questions are enough.
   - Export as JSON and Markdown, like the existing page.
   - Use a new browser storage key.
6. **Verify, then append Results.** Verification below. Commit the re-key drafts and push to the same PR.

## Verification

```bash
/opt/homebrew/bin/python3.13 scripts/ucf/validate.py      # exit 0, zero WARN, check 7 says lock 1.0.0 enforced
/opt/homebrew/bin/python3.13 scripts/ucf/make_criteria_map.py   # every one of the 728 criterion ids appears exactly once in criteria_map.csv
python3 scripts/ucf/make_signoff.py                        # README says signed 1.0.0
JSDOM_PATH=/Users/saqlainmomin/railPVC/frontend/node_modules/jsdom node <new smoke test>   # loads, card counts match the proposed rows, choosing and export work
```

Also prove the lock bites. On a temporary copy of the drafts (`validate.py --data <copy>`), rename one control title and confirm check 7 fails. Then delete the copy.

The jsdom message "URL.revokeObjectURL is not a function" is a known artifact.

If the Chrome extension tools work in your session, open the new page once. In the last session they were not connected (account mismatch).

## Report back

Append `## Results` to this file. Cover:
- The commit hashes and the PR link.
- The lock summary.
- Criteria counts per framework (auto, proposed) and the controls left with zero criteria.
- The scope proposals that could not be re-keyed cleanly.
- Anything you could not do.
- The exact list of decisions Saqlain must make on the new page.

End with the next steps:
1. His re-key review.
2. Apply his choices (`basis: decided`).
3. WP 3.4 (the validator gains a criteria-coverage check).
4. The evaluation gate WP 4.6.
5. Load into the app (WP 5.1).

## Results

Run on 15 Oct 2026. All six done-items are met, except opening the page in a real browser.

### Commits and PR

- `b57ffa9`: signs the library 1.0.0 and adds the lock and all the uncommitted round-2 work (data, generators, sign-off tables, review page, FORMAT.md, smoke test).
- `2940859`: adds the re-key drafts (criteria map, scope proposals, review page, scripts, FORMAT.md sections).
- A third commit adds this Results section.
- PR: https://github.com/saqlainmmomin/Cyber/pull/157. It was already open for this branch, so I updated its title and description instead of opening a new PR. Not merged.

### Signing and lock

- `library.json` now reads: `library_version` 1.0.0, `status` signed, `signed_by` Saqlain Momin, `signed_on` 2026-10-14. The loader already accepted extra keys, so the schema did not change.
- `make_signoff.py` prints "Signed 1.0.0 by Saqlain Momin on 14 Oct 2026" on the README and every domain table, and ticks each Sign cell.
- The README says the 16 DPDPA legal items are confirmed provisionally and are not legally verified.
- `ids.lock.json` covers 211 controls (a hash of domain and title for each) and 265 records. Validator check 7 reports "lock 1.0.0 enforced: 211 controls, 265 records". The validator exits 0 with zero warnings.
- Lock test: on a temporary copy, renaming UC-CRY-01's title made check 7 fail with "domain or title changed since lock 1.0.0" and exit 1. The copy is deleted.
- No control content changed.

### Criteria map (`docs/ucf/drafts/criteria_map.csv`)

All 728 criterion ids appear exactly once. A re-run keeps `decided` rows unchanged, which I tested on a copy.

| Framework | Criteria | Auto | Proposed | Records with criteria | Records with 2+ controls |
|---|---|---|---|---|---|
| ISO 27001 | 230 | 163 | 67 | 93 | 22 |
| NIST CSF | 348 | 152 | 196 | 106 | 56 |
| DPDPA | 150 | 68 | 82 | 41 | 20 |
| Total | 728 | 383 | 345 | 240 | 98 |

- These match the handoff's numbers.
- No record with criteria lacks a control.
- How proposals were made: words weighted by rarity, matched against the record's atoms mapped to each candidate control (atoms count double) and the control's text. No LLM was used.
- 18 proposals are marked "close call": a second candidate scored within 15% of the best.
- 2 are marked "weak match": fewer than three shared words.
- In a spot check of 22 proposals, all were sensible picks.

**13 controls are left with zero criteria (gaps):**
- No mapped record has signed criteria. These are the ISO clause controls, whose drafted `test` text stands under D18: UC-GOV-01, GOV-03, GOV-12, GOV-14, GOV-15, GOV-16, GOV-20, PPL-05, RSK-03, RSK-04.
- They are candidates on a criteria record, but the proposal chose a partner control: UC-GOV-04 (Security management system operated), UC-GOV-10 (Risks and opportunities of the program), UC-PSC-06 (Cross-border flow inventory). Saqlain's choices on the page can change these.

### Scope proposals (`scope_proposals.csv`, `notes_scope_rekey.md`)

There are 11 clean proposals:
- ISO.SCP.2 = no: UC-SUP-07.
- ISO.SCP.3 = no: UC-SDC-05, SDC-07, SDC-08.
- ISO.SCP.3 = inhouse: UC-SDC-07.
- ISO.SCP.4 = fully_remote: UC-PHY-01, 03, 06, 08, 10, 11.

**Not re-keyable cleanly (9 held back):**
- **Held back because a NIST record also needs them:**
  - UC-SUP-06, via A.5.23 (NIST PR.IR-02).
  - UC-IAM-10 and UC-SDC-02, via A.8.4 and A.8.25 (NIST PR.PS-06).
  - UC-SDC-10, via A.8.33 (NIST PR.DS-02).
  - UC-PHY-02 and UC-PHY-13, via A.7.2 (NIST PR.AA-06).
  - UC-PHY-04, via A.7.4 (NIST DE.CM-02 and PR.AA-06).
  - UC-PHY-05, via A.7.5 (NIST PR.IR-02).
- **Held back for an extra reason:** UC-PPL-04 (via A.8.28) also carries A.6.3 and NIST PR.AT-02.
- **Annex A ids left with no clean control:** A.8.4, A.8.25 and A.8.33 (no development), and A.7.2, A.7.4 and A.7.5 (fully remote).
- No proposal touches a clause 4 to 10 control.

### Review page

- **Page:** `tasks/2026-10-14-ucf-rekey-review.html`.
- **Built by:** `scripts/ucf/make_rekey_review_html.py` with `rekey_review_template.html`. It uses the browser storage key `ucf-rekey-review-1.0.0`.
- **Smoke test:** `scripts/ucf/authoring/smoke_rekey_review_page.js`. All 23 checks pass. It covers loading with no errors, cards matching the 345 proposed rows across 98 records, pre-selection, choosing another control, flagging, accepting, filters, bulk accept, scope cards, and JSON and Markdown export.

### Not done

- I did not open the page in a real browser. The Chrome extension was still not connected because of the same account mismatch as last session.
- No subagents were used; the word-match script was enough.

### Decisions Saqlain makes on the page

1. For each of the 345 criteria, accept the proposed control, pick another candidate, or flag that it tests two controls. Start with the 20 marked close call or weak match; there is a filter for them. There is also a bulk accept per record or per filtered list.
2. Approve or change each of the 11 scope proposals.
3. S1: for the 9 held-back cases, either keep them out (my recommendation) or propose them only when ISO 27001 is the sole framework selected. The second option needs a framework condition in the WP 5.5 wiring.
4. S2: are four ISO scope questions enough? My recommendation is yes for 1.0, and to revisit after the first real assessments.

He exports the JSON and saves it as `tasks/2026-10-14-ucf-rekey-decisions.json`.

### Next steps

1. Saqlain's re-key review on the page.
2. Apply his choices: write them into `criteria_map.csv` as `basis: decided`, then update `scope_proposals.csv`.
3. WP 3.4: the validator gains a criteria-coverage check, which reports the 13 zero-criteria controls.
4. The evaluation gate, WP 4.6.
5. Load into the app, WP 5.1.
