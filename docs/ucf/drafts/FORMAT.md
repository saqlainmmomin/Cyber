# UCF draft data format

Signed 1.0.0 by Saqlain Momin on 14 Oct 2026. All files are CSV (UTF-8, header row, standard quoting) in this folder. One table per file. No list is ever packed into one cell, except `key_settings` (see below). American spelling, sentence case, no em dashes, own wording (no copied standard text).

Framework keys: `iso27001`, `nist_csf`, `dpdpa`. Source codes in file names: `iso`, `nist`, `dpdpa`.

## Files

| File | Columns | Written by |
|---|---|---|
| `library.json` | `library_version`, `status` (`signed` or a draft label), `signed_by`, `signed_on` (ISO date, when signed), `frameworks` | fixed; changed only at a version event |
| `ids.lock.json` | `library_version`, `controls` (id to hash of domain and title), `records` | `validate.py --write-lock` at each signed version |
| `domains.csv` | `code,name,owner_role,privacy,sort` (18 rows, fixed) | fixed |
| `roles.csv` | `role` (closed list of owner roles) | fixed |
| `records_<x>.csv` | `framework,record_id,reference,title,kind,group` | script, plus ISO clauses |
| `atoms_<fw>.csv` | `framework,record_id,atom_id,source_ref,paraphrase,needs_verification` | drafting agents |
| `controls_<src>.csv` | `id,title,domain,iso_theme,goal,owner_role,importance,origin,note` | drafting agents |
| `mappings_<src>.csv` | `source_framework,record_id,source_ref,atom_id,unified_control_id,match_type,coverage,reason,primary,remainder_of,remainder_immaterial,immaterial_reason` | drafting agents |
| `fields_<DOMAINCODE>.csv` | `id,statement,why_asked,how_to_ask,question,expected_evidence,good_looks_like,test,baseline_risk,applicability,control_type,frequency,key_settings` | field writers |

A unified control is the join of its `controls_*` row and its `fields_*` row on `id`. Sign-off tables show the join.

## Records

A record is the judged unit: one ISO clause (subclause level, such as 4.1 or 6.1.2) or Annex A control, one NIST subcategory, one DPDPA requirement.

- `record_id` is the id in the repo for Annex A, NIST and DPDPA (`ISO.A5.1`, `NIST.GV.OC.01`, `CH2.CONSENT.1`). Never change these.
- ISO clause records use `ISO.C<clause>`, for example `ISO.C4.1`, `ISO.C6.1.2`. `kind` is `clause`. They go in `records_iso_clauses.csv`.
- `kind` is one of `clause`, `annex`, `subcategory`, `requirement`.

## Atoms

An atom is one single ask inside a record. Atom ids are `<record_id>-a`, `-b`, `-c`, and so on. A record with one ask has one atom, `-a`. When an atom is later found to bundle two asks, it is split into `-b1`, `-b2` (the old id is retired). `paraphrase` is one sentence in our own words, starting with a verb or "The organization...". `source_ref` is the reference, not text (`Annex A.5.18`, `GV.OC-02`, `DPDPA s.6(1)`; use the reference stored in the repo records). `needs_verification` is `true` for an atom written from knowledge that Saqlain has not yet checked against the source, otherwise `false`. All ISO clause atoms were verified by him on 14 Oct 2026.

## Unified controls (skeleton, `controls_<src>.csv`)

- `id`: `UC-<DOMAIN>-<NN>`, two digits, stable. Number ranges so parallel agents never collide: ISO 01 to 39, NIST 40 to 69, DPDPA 70 to 99. Exception: the five privacy domains (PNC, PRT, PUR, PGV, PSC) are created only by DPDPA and number from 01.
- `domain`: one code from `domains.csv`. Exactly one.
- `iso_theme`: `Organizational`, `People`, `Physical`, `Technological`, or empty (clauses 4 to 10, privacy and NIST-only controls may be empty).
- `goal`: one sentence, the single goal of the control, framework-neutral, never naming a framework.
- `owner_role`: one value from `roles.csv`.
- `importance`: `critical`, `high`, `medium`, `low`. Internal.
- `origin`: `iso`, `nist` or `dpdpa`, whichever file created the row.
- `note`: free text. Record splits, merges, "remainder of UC-xxx", NIST-only, privacy-only.

## Mapping rows (`mappings_<src>.csv`)

One row per (atom, unified control). A source atom never maps to the same control twice.

- `match_type`: `equal`, `req_smaller` (control covers all and more), `req_bigger` (control covers part), `overlap`, `none`.
- `coverage`: `full`, `partial`, `none`. Allowed pairs: `equal`+`full`, `req_smaller`+`full`, `req_bigger`+`partial`, `overlap`+`partial`, `none`+`none`.
- `reason`: one line. Mandatory on every row.
- `primary`: `true` on exactly one row per record (across all that record's atoms), `false` elsewhere. The primary row is the control that best carries the record's main goal. A record whose atoms are all `none` has no primary row.
- `remainder_of`: set on the row that maps an atom to a remainder slot. Value is the base control id the slot completes. Otherwise empty.
- Partial coverage rule: when a row has `coverage=partial`, the same atom must also have a row to a remainder slot (a control whose row has `remainder_of` equal to the partial row's control), unless the partial row sets `remainder_immaterial=true` and gives `immaterial_reason`.
- `none` rows: `unified_control_id` empty, `match_type=none`, `coverage=none`, `reason` says why there is no match.
- Every control must be reached by at least one mapping row.
- Base control from ISO: `equal` or `req_smaller` rows are the normal case. NIST and DPDPA map to ISO base controls where covered, to their own slots where not.

## Control fields (`fields_<DOMAINCODE>.csv`)

Write all of these for every control in the domain. Control statements never name a framework or contain a control code. A number or timeframe may appear only if the same text appears in `key_settings` with its layer.

| Field | Content |
|---|---|
| `statement` | Who, does what, when, how, why, proof. Active voice. One goal. Framework-neutral. |
| `why_asked` | One or two sentences: the failure this prevents. For the consultant. |
| `how_to_ask` | Plain direction for putting it to the client, with one example probe. |
| `question` | The client-facing question. One obligation, ends with a question mark, answerable on the five-value scale (fully, partially, planned, not, not applicable), no control code, no framework name. |
| `expected_evidence` | Artifact names in the client's words, and the period to cover. |
| `good_looks_like` | What a fully implemented answer contains. |
| `test` | What to sample and what a pass looks like. Seed from the signed criteria. |
| `baseline_risk` | One sentence: what happens if absent. |
| `applicability` | When the control applies, if conditional. Empty if always. |
| `control_type` | `preventive`, `detective` or `corrective`. |
| `frequency` | `continuous`, `per_event`, `monthly`, `quarterly`, `annual`, `ad_hoc`. |
| `key_settings` | Numbers and timeframes in the control, written `layer: setting` and joined with ` | `. Layer is `base`, `iso27001`, `nist_csf` or `dpdpa`. Empty if none. A setting under a framework layer applies only when that framework is selected. |

## Validator behavior this format supports

See `scripts/ucf/validate.py`. Subsets: iso27001, nist_csf, dpdpa, and every combination (seven in total). A control is shown in a subset if any selected framework has a mapping row to it. Atoms with no control (match `none`) show nothing.
