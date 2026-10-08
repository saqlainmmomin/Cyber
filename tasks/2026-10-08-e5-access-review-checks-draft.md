# E5 access-review checks: draft for Saqlain

Research date: 2026-10-08. This is a starting draft for auditor markup. It does not select a design or authorise implementation. E4 remains open. E5 concerns later demo work. Read first: `tasks/2026-10-08-ai-coherence-map.md`, item 5, and `tasks/2026-10-08-session-record.md`, decisions E4/E5.

## Source and method

Only this synthetic workbook was read:

`/Users/saqlainmomin/dpdpa-s6f1/data/uploads/demo/evidence/61b0212c-338f-4001-922a-033a569d2c71/8afb5b24-1743-4d81-81ef-f57c40d5d3f8/v1.xlsx`

SHA-256: `cc1d9915a2293a3139c62f330624b326d99a1db51257d88d21ee21adf27bc3f5`.

Scratch Python scripts under `/tmp` used the project `.venv`. The real call was `app.services.document_processor.extract_text(str(path), "xlsx")`. A separate openpyxl read inspected cells, dates, formulas and counts. No database ingestion was run. No LLM calls or network were used. No answer keys were opened. The workbook was not copied into the repo or changed. Its hash was unchanged after inspection.

Working assumptions for the examples below: Q3 2026 means 1 July through 30 September, inclusive. The observation date is 30 September 2026, not today. `Admin` means privileged access. `Approved` means a recorded approval, subject to auditor confirmation. A note does not close an exception. These are provisional interpretations, not policy decisions.

## 1. What extraction stores today

The service writes original upload bytes to versioned storage (`app/services/evidence.py:158`, `app/services/evidence.py:311`). The ingest path extracts from the released version and stores the result in `EvidenceVersion.extracted_text` (`app/services/evidence.py:699`, `app/models/evidence.py:52`). Original bytes remain available through the version's storage path.

The XLSX path loads cached values with `read_only=True`, `data_only=True` and `keep_links=False` (`app/services/document_processor.py:130`). It reads each worksheet. It stores complete rows in order until the configured word budget is reached (`app/services/document_processor.py:248`). This is the post-#127 path. It does not sample 200 rows. It can still omit trailing rows at the size limit, with explicit markers (`app/services/document_processor.py:262`, `app/services/document_processor.py:309`).

Observed run: budget 200,000 words. Output: 6,813 words, 35,551 characters and 248 lines. All 220 detail records survived. All 35 rows with notes survived. The script matched every record number and employee ID against the extracted rows.

The first 15 lines of the actual `extracted_text` were:

```text
Sheet: Access Review Summary
Quarterly Access Review List
Access review coverage summary
Review date | 2026-09-30 00:00:00 | | Coverage statement
Review owner | Security Operations | | The access review covers all 200 employees in the HR roster as of 30 Sep 2026. Each employee has been reviewed for business need, least privilege, and timely removal of access.
Review period | Q3 2026
Total employees in scope | 200
Access records expected | 200
Applications reviewed | 6
Review status | Completed
Department | Employees | Active access | Review outcome
Engineering | 82 | 82 | No exception
Sales | 38 | 38 | No exception
Operations | 31 | 31 | No exception
Finance | 24 | 24 | No exception
```

The only sheet/marker lines were:

```text
Sheet: Access Review Summary
Sheet: Access Review Detail
```

There was no truncation or unstored-sheet marker. A truncated run would use `[stored rows 1-N of M in sheet "..."; the remaining rows were not stored]` or `[sheet "..." not stored: size limit reached]` (`app/services/document_processor.py:262`).

The detail section began:

```text
Sheet: Access Review Detail
Access Review Detail
Exported records | 220 | Expected population | 200 | Review period | Q3 2026
Record # | Employee ID | Employee Name | Department | Role | Application | Access Level | Employment Status | Last Login | Review Status | Reviewer | Review Date | Exception Notes
1 | E001 | Aarav Shah | Engineering | Software Engineer | ERP | Read | Active | 2026-09-08 00:00:00 | Approved | A. Mehta | 2026-09-30 00:00:00
```

What is lost:

- All cell values become strings. Integers and Excel dates lose their native types. Dates retain readable values here, but lose the Excel date format. Formulas would yield cached values rather than formula logic. This workbook has zero formula cells (`app/services/document_processor.py:132`, `app/services/document_processor.py:190`).
- Blank rows disappear. Trailing blank cells disappear. Internal blanks survive as empty fields. E001 therefore has no final delimiter for its blank note (`app/services/document_processor.py:181`).
- Header text survives. Header semantics do not. The renderer treats the first nonempty row as its header. That is a title on both sheets. The real detail header is Excel row 4 (`app/services/document_processor.py:224`).
- Cell coordinates, merged layout and formatting are absent. Embedded line breaks become spaces. Literal pipe characters have no escaping. Cells longer than 2,000 characters are shortened (`app/services/document_processor.py:190`, `app/services/document_processor.py:237`).

Draft recommendation: run checks on the stored original bytes of an explicitly selected `EvidenceVersion`. Retain extracted text for quotations and narrative. Re-read the version path and verify its hash. Do not read the frozen v1 path on `Evidence` when a later version exists (`app/models/evidence.py:21`, `app/services/evidence.py:819`, `app/services/evidence.py:831`). Bind the result to the selected version so later uploads cannot silently change the tested population.

## 2. Workbook profile

### Sheets and layout

| Sheet | Occupied extent | Structure |
| --- | --- | --- |
| Access Review Summary | A1:H27 | Titles, metadata, department summary and legends. Not a single record table. |
| Access Review Detail | A1:M224 | Title on row 1. Export metadata on row 2. Headers on row 4. Records on rows 5-224. |

Summary cells B4 and B6 give the review date and quarter. B7/B8 state 200 employees and 200 expected access records. B9 states six applications. B10 says Completed. Department rows 14-19 report 82 Engineering, 38 Sales, 31 Operations, 24 Finance, 15 People and 10 Legal and Compliance. All six say No exception. There is no independent HR roster or system register in this workbook.

### Detail columns

Counts below are records, not distinct people. Blank means an empty cell, not the literal access-level label `None`.

| Column | Native values and profile |
| --- | --- |
| Record # | 220 integers, unique, 1-220. Format `#,##0`. |
| Employee ID | 220 strings. 212 distinct IDs, E001-E212. Eight IDs occur twice. |
| Employee Name | 220 strings. 101 distinct names. Names are not unique identifiers. |
| Department | Engineering 38; Sales 38; Operations 36; Finance 37; People 36; Legal and Compliance 35. |
| Role | Software Engineer 38; Account Executive 38; Operations Analyst 36; Data Analyst 37; People Partner 36; Compliance Counsel 35. This is a job role, not an application permission. |
| Application | ERP 37; CRM 37; HRIS 36; Data Warehouse 36; Cloud Console 38; Support Desk 36. |
| Access Level | Read 110; Write 72; Admin 38. The summary legend defines `None` as no access, but no detail row has that value. |
| Employment Status | Active 215; Terminated 5. No termination dates. |
| Last Login | 219 Excel dates and one blank. Range 2026-09-01 to 2026-09-22. Sep 1: 54; Sep 8: 56; Sep 15: 54; Sep 22: 55. Format `yyyy-mm-dd`. |
| Review Status | Approved 210; Pending 4; Exception 6. |
| Reviewer | A. Mehta on all 220 rows. No blanks. No reviewer ID or approval authority. |
| Review Date | 219 Excel dates, all 2026-09-30. One blank, E154. Format `yyyy-mm-dd`. |
| Exception Notes | 35 nonblank strings and 185 empty cells. Ten distinct note patterns, listed below. |

All populated non-date columns other than Record # contain strings. Both date columns contain native datetime values on read. There are no formula cells. The summary mixes strings, integers and one Excel date.

### All 35 rows with notes

| Exact note pattern | Count | Employee IDs and record references |
| --- | ---: | --- |
| Termination record present; access still enabled | 5 | E017, E042, E088, E131, E188. |
| Manager attestation missing | 4 | E025, E061, E120, E167. |
| Department differs from HR roster | 1 | E031. |
| Elevated access requires validation | 1 | E074. |
| Last login not recorded | 1 | E116. |
| Review date missing | 1 | E154. |
| Name spelling differs from HR roster | 1 | E199, record 199. |
| Application differs from HR roster | 1 | E200. |
| Not included in summary population | 12 | E201-E212, records 201-212. |
| Duplicate employee row | 8 | E014, E037, E052, E081, E109, E143, E176, E199, records 213-220 respectively. |

These groups sum to 35 and do not overlap as note groups. Check flags can overlap. Only six rows have Review Status = Exception. Notes appear on Approved rows too. Do not equate 35 noted rows with 35 failed access controls.

Repeated employee IDs affect 16 rows in eight groups. Only two employee/application pairs repeat: E081/HRIS and E109/ERP. Only E081/HRIS/Read repeats the same employee/application/access-level combination. E109 has Read and Write. The remaining repeated IDs have different applications. There is no account ID to establish whether these are duplicate accounts or legitimate multiple entitlements.

## 3. Candidate deterministic checks

### Control references checked against this repo

These are candidate evidence links, not claims that one spreadsheet proves a whole control.

| Local requirement ID | Framework reference and meaning | Code source |
| --- | --- | --- |
| `ISO.A5.18` | ISO 27001 A.5.18, access rights. Main review, modification and removal link. | `app/frameworks/definitions/iso27001.py:187` |
| `ISO.A8.2` | ISO 27001 A.8.2, privileged access rights. | `app/frameworks/definitions/iso27001.py:601` |
| `ISO.A5.3` | ISO 27001 A.5.3, segregation of duties. | `app/frameworks/definitions/iso27001.py:51` |
| `ISO.A5.16` | ISO 27001 A.5.16, identity management. Supporting lifecycle link. | `app/frameworks/definitions/iso27001.py:171` |
| `NIST.PR.AA.05` | NIST CSF 2.0 PR.AA-05, permissions reviewed, least privilege and segregation of duties. | `app/frameworks/definitions/nist_csf.py:562` |
| `NIST.PR.AA.01` | NIST CSF 2.0 PR.AA-01, identity and credential management. Supporting lifecycle link. | `app/frameworks/definitions/nist_csf.py:530` |

No external standards were fetched. Thresholds and frequencies below are proposed auditor inputs. They are not asserted framework requirements.

### C1. Systems and population covered

**Auditor test:** Did the review include every in-scope system and the required account population?

**Inputs:** Application, stable account/employee ID, Review Status, Reviewer, Review Date. Also an approved system list, account inventory and review period. Those independent lists are absent.

**Exact proposed rule:** For each system in the approved scope list, require at least one record with Approved status, nonblank reviewer and valid date inside the period. Flag `scope systems minus reviewed systems`. Then reconcile account keys against the independent inventory. A system with one reviewed row is present, but its full account population is not proved covered.

**This file:** Six systems have qualifying rows: ERP 35, CRM 35, HRIS 36, Data Warehouse 34, Cloud Console 35 and Support Desk 34. Actual missing-system count is unavailable. It is not zero. If Saqlain confirms these six as the complete scope, the system-presence rule flags zero systems. E001, E002 and E003 are qualifying examples, not failures.

**Additional exact reconciliation rule:** Flag a mismatch between the declared expected count and the measured count at the auditor-approved grain. Here 200 expected access records versus 220 detail records is a difference of 20. If employee grain is intended, 200 stated employees versus 212 distinct IDs is a difference of 12. The notes identify E201, E202 and E203 as outside the summary population. A real HR join is still needed to establish out-of-scope people and missing people.

**False positives:** System aliases, service accounts, contractors and multiple accounts per person. A headcount must not be used as an entitlement-row denominator without agreement.

**Controls:** `ISO.A5.18`, `NIST.PR.AA.05`. Identity reconciliation can also support `ISO.A5.16`, `NIST.PR.AA.01`.

### C2. Removal decisions actioned

**Auditor test:** Was access actually withdrawn when a review required removal?

**Inputs:** Account ID, system, review decision, decision date, action status, action date and a dated account-state export. Also the agreed action deadline. None of the decision/action columns exists here.

**Exact proposed rule:** For each Remove decision due by the observation date, flag an account still enabled, a missing completion date, or completion after the agreed deadline. Report those reasons separately. If a required input is absent, report Not testable rather than Pass.

**This file:** Removal-decision denominator and failed-removal count are unavailable. Five termination notes are follow-up candidates, including E017, E131 and E188. They are not five proven failures of a recorded Remove decision. Review Status is not a retain/remove decision.

**False positives:** Export captured before the deadline, disabling versus deleting accounts, approved delayed removal, and unlinked ticket evidence.

**Controls:** `ISO.A5.18`, `NIST.PR.AA.05`. Lifecycle support: `ISO.A5.16`, `NIST.PR.AA.01`.

### C3. Terminated users with access assigned

**Auditor test:** Do leavers retain access that should have ended?

**Inputs:** Employment Status and Access Level for a screening rule. For a conclusive enabled-account test, also termination date, enabled/disabled status, snapshot date and permitted removal delay.

**Exact rule runnable here:** Flag Employment Status = Terminated and Access Level in {Read, Write, Admin}. Label the result “terminated with access assigned”. The notes corroborate “still enabled”, but a level value alone does not prove live login capability.

**This file:** Five of five terminated records flag: E017, E042, E088, E131 and E188. E017 and E131 are Admin. Examples: E017 at sheet row 21, E131 at row 135 and E188 at row 192. The five exact notes say access is still enabled. A conclusive timeliness test is unavailable.

**False positives:** Stale employment status, disabled accounts that retain a role label, retained audit records and approved transition periods. No termination date means no elapsed-time calculation.

**Controls:** `ISO.A5.18`, `ISO.A5.16`, `NIST.PR.AA.05`, `NIST.PR.AA.01`. The two admin rows also support `ISO.A8.2`.

### C4. Privileged accounts reviewed

**Auditor test:** Was privileged access explicitly reviewed and resolved?

**Inputs:** Access Level, Review Status, Reviewer, Review Date, system and account identifier. Confirm which levels mean privileged and what proves completion.

**Exact proposed rule:** For every Admin row, require Approved status, nonblank reviewer and a valid review date within the period. Flag any missing condition. Independently retain notes for auditor review. Do not infer privileged appropriateness from job title alone.

**This file:** 38 Admin records. 34 meet the completion rule. Four flag: E017, E074, E131 and E167. The first three have Exception status. E167 is Pending. Examples: E074 at row 78, E131 at row 135 and E167 at row 171. All 38 have a reviewer and date. A simpler presence-only rule would flag zero and miss the unresolved statuses.

**False positives:** Exception might mean an approved risk acceptance. A single Approved value may lack manager sign-off. Admin labels and break-glass accounts may need separate treatment. The source does not prove all privileged accounts were exported.

**Controls:** `ISO.A8.2`, `ISO.A5.18`, `NIST.PR.AA.05`.

### C5. Reviewer and review date present

**Auditor test:** Can each review be attributed to a person and a date?

**Inputs:** Reviewer and Review Date. Review Status is needed for a separate completion check.

**Exact rule:** Flag blank or whitespace-only Reviewer. Flag blank or unparseable Review Date. Keep separate counts and a union count. A summary-level owner/date does not fill missing row evidence.

**This file:** Zero missing reviewers. One missing date and one row in the union: E154, row 158, despite Approved status. No other failure examples exist. E001 and E002 meet the presence rule.

**Related completion rule:** Flag Review Status in {Pending, Exception}. Ten records flag: four Pending and six Exception. Examples: E025, E074 and E167. Combined with missing-date evidence, 11 records need attention. Their notes cannot automatically be treated as approved exceptions.

**False positives:** Valid batch sign-off held elsewhere, reviewer initials requiring identity resolution, approved exceptions, or status values that describe a different workflow.

**Controls:** `ISO.A5.18`, `NIST.PR.AA.05`. Apply `ISO.A8.2` to the privileged subset.

### C6. Review cycles within the period

**Auditor test:** Were the required review cycles completed at the agreed frequency?

**Inputs:** Review Date, cycle ID or batch reference, period boundaries, required frequency and in-scope system list. A date alone is not a reliable cycle identifier.

**Exact proposed rule:** Assign each dated row to an auditor-defined cycle window. For each system/window, require a completed review batch and reconcile its account population. Flag missing expected cycles. Separately flag dates outside the period and missing dates. Do not count distinct row dates as independent completed reviews.

**This file:** All 219 dated rows fall on 30 September, inside Q3. Zero dates are outside Q3. E154 has the one missing date. There is one observed date and one stated quarter, but no cycle ID. The count of proven complete cycles is unavailable. Under a provisional quarterly, date-presence-only screen, all six applications have Q3 evidence. Under monthly date-presence screening, July and August have no dates for any application: 12 system/month gaps. These are missing evidence windows, not proven missed reviews. E001 and E002 illustrate September evidence.

**False positives:** A September signature covers earlier work, consolidated exports, differing system schedules and an incomplete evidence pack.

**Controls:** `ISO.A5.18`, `NIST.PR.AA.05`, plus `ISO.A8.2` for privileged review cycles. The auditor supplies frequency.

### C7. Dormant accounts

**Auditor test:** Are unused accounts still assigned access without an agreed reason?

**Inputs:** Last Login, account state, snapshot date, account type and dormant-day threshold. This file has no account state or account type.

**Exact provisional rule:** For rows with assigned access, flag `(2026-09-30 minus Last Login).days > 90`. Missing dates go into Unknown, not Dormant. In a full test, restrict to enabled accounts and apply agreed service-account exceptions. Reject future or unparseable dates as data-quality issues.

**This file:** Zero known dates exceed 90 days. Known inactivity ranges from 8 to 29 days. E116, row 120, is the one Unknown due to a missing login date. There are no dormant failure examples. E001 and E004 illustrate 22 and 29 days. Strict thresholds of 30 and 60 days also flag zero known dates.

**False positives:** Service accounts, newly created accounts, leave, SSO activity missing from local logs and unreliable last-login exports. Unknown must not inflate a clean denominator.

**Controls:** `ISO.A5.18`, `NIST.PR.AA.05`. Apply `ISO.A8.2` to privileged dormant accounts.

### C8. Segregation of duties

**Auditor test:** Does one identity hold a prohibited combination of permissions?

**Inputs:** Stable identity/account ID, detailed entitlements, system, effective dates and an auditor-approved conflict matrix. Job Role and Read/Write/Admin are insufficient to identify transaction conflicts.

**Exact proposed rule:** Join entitlements by identity and overlapping effective period. Flag each pair found in the approved conflict matrix. Compare reviewer identity to subject identity only if a separate self-review prohibition is confirmed and both identities can be resolved.

**This file:** Not testable. No matrix or granular entitlements exists. No reviewer ID exists. There is no confirmed conflict count. E052, E176 and E199 each have multiple application rows and could be joined later. Multiple applications are not themselves a SoD breach. E074's elevated access note is a validation request, not proof of a conflicting permission pair.

**False positives:** Different people with the same name, disjoint effective dates, approved compensating controls and ambiguous role labels.

**Controls:** `ISO.A5.3`, `NIST.PR.AA.05`. Privilege management may also support `ISO.A8.2`.

### C9. Population integrity before interpreting results

**Auditor test:** Does the detail reconcile to the summary, and is the test population reliable?

**Inputs:** Record #, Employee ID, Application, Access Level, summary counts and an approved account-grain definition. A real HR roster is needed for attribute discrepancies.

**Exact rules runnable here:** Compare detail count 220 with declared 200. Compare distinct employee count 212 with declared 200 only under employee grain. Flag repeated Employee ID groups for review, retaining all rows. Report employee/application and employee/application/level repetitions separately. Flag the summary's Completed/No exception claims when any row is Pending, Exception or missing its date.

**This file:** Two count mismatches under the two stated grains. Eight repeated employee groups affect 16 rows. Examples: E014 records 14/213, E081 records 81/216 and E199 records 199/220. Two repeated employee/application groups affect four rows. One repeated employee/application/level group affects two rows. The summary completion claim has 11 contrary detail records, including E025, E131 and E154. The department totals also differ from the detail counts in section 2.

The four note patterns about population and HR attributes need external corroboration. Twelve records say they are outside the summary. E031, E199 record 199 and E200 assert department, name and application mismatches. Those notes do not supply the HR values required for a deterministic comparison.

**False positives:** Employees with multiple entitlements, valid additional scope and a summary built at a different date or grain. Do not deduplicate employee IDs automatically. Do not infer an authoritative HR roster from ID numbering.

**Controls:** Supports the reliability of testing `ISO.A5.18` and `NIST.PR.AA.05`. It is not a separate access violation by itself.

## 4. Column mapping and auditor confirmation

| Source column or cell | Proposed role |
| --- | --- |
| Detail row 4 | Header row. Record region A5:M224. |
| Record # | Source record reference. Pair with sheet and Excel row. |
| Employee ID | Employee join key. Not proven to be an account ID. |
| Employee Name | Display name. Optional HR comparison. Never primary key. |
| Department | Organisational unit. Optional HR comparison. |
| Role | Job role. Not application entitlement. |
| Application | System identifier, subject to approved aliases. |
| Access Level | Coarse access class. Admin maps to privileged provisionally. |
| Employment Status | HR lifecycle status. Not enabled-account status. |
| Last Login | Last recorded activity date. |
| Review Status | Review workflow status. Not removal decision or action status. |
| Reviewer | Reviewer display name. Not yet a verified identity or authority. |
| Review Date | Row review date. Not removal date or snapshot date. |
| Exception Notes | Source explanation. Not accepted risk, closure or rule override. |
| Summary B4/B6/B7/B8/B9/B10 | Stated date, quarter, employees, expected records, application count and completion claim. |

Missing roles must remain Unmapped: account ID, enabled state, snapshot date, termination date, retain/remove decision, action date/status, cycle ID, account type, granular entitlement and exception approval/expiry.

Proposed confirmation step: show the original table with sheet/cell addresses beside each proposed mapping. Include normal examples and E131, E154 and a repeated-ID pair. Let Saqlain change the table boundary, key grain, aliases, status meanings and date roles. Show the external lists and thresholds each selected check needs. He explicitly confirms the mapping and parameters for that evidence version before execution. Save who confirmed it and when. A replacement version or changed mapping should require revalidation.

An LLM could propose sheet/table selection and semantic column roles for unfamiliar uploads. It could suggest synonyms and explain ambiguities. No step inherently requires an LLM. This workbook can be mapped manually. The LLM must not invent absent columns, choose thresholds, approve exceptions or decide findings.

Pure code can read cells, profile types, detect blanks, validate dates and keys, apply confirmed mappings, join approved registers, execute rules, compute counts and preserve row references. Auditor judgement selects the scope, grain, rules and thresholds. It also resolves note meanings and confirms conclusions. If later narrative summarisation uses an LLM, it should consume measured results without changing them.

## 5. Where the auditor would see results

Proposed landing point: the relevant conclusion card, initially A.5.18 and A.8.2. Show the tested filename/version, approved mapping, period, rule and denominator. Each check shows Flagged, No flags or Not testable, with Unknown shown separately. These are check results, not automatic control outcomes.

Example card text: “220 access records tested. Five terminated employees have access assigned. Two are Admin. Removal completion could not be tested because decision and action fields are absent.” Row links should open the selected original version at E131, Excel row 135, with the relevant cells visible. Distinguish the source note from the computed count.

Existing models offer useful homes:

| Existing model or surface | Reuse and limit |
| --- | --- |
| `EvidenceVersion` and `EvidenceUse` | Version identity, hash, original bytes and evidence-to-assessment/control links. `app/models/evidence.py:32`, `app/models/evidence.py:56`. |
| `TestCriterion` | Signed design/operating statements and evidence hints. It is not an executable rule or result schema. `app/frameworks/schema.py:14`. |
| `Conclusion` | Control outcome, rationale, evidence summary, gaps, risk and action. `app/models/conclusion.py:29`. Auditor outcome remains separate from row flags. |
| `ConclusionRevision` | Actor, revision action, citations JSON and analysis-run reference. `app/models/conclusion.py:43`. |
| `Finding` | Grouped title, description, impact, recommendation, severity and status linked to a conclusion. `app/models/finding.py:10`. |
| `Action` | Owner, target date, status and history attached to a finding. `app/models/action.py:10`. |
| `AnalysisRun` | Existing model/claims payload. It requires model_id and is not a dedicated deterministic execution record. `app/models/analysis_run.py:10`. |
| `VerifiedClaim` | Source/version references, exact text offsets and quotes. No typed sheet/cell locator fields. A computed aggregate must not be passed off as a verified source quote. `app/services/grounding/claims.py:36`. |

The card already has criteria/result and evidence-link surfaces (`app/templates/components/requirement_card_body.html:15`, `app/templates/components/requirement_card_body.html:34`). These are integration points, not existing spreadsheet checks. The default analysis pipeline is still v1 (`app/config.py:78`).

The current finding service requires an approved or edited gap conclusion. It rejects a second finding for the same conclusion (`app/services/findings.py:530`). Reuse would therefore group access-review issues under the approved conclusion, with row detail and actions. One finding per flagged row would change that workflow.

No inspected model defines a complete deterministic run record. A design must decide where to persist rule version, original version/hash, approved mapping, parameters, external-register versions, counts, unknowns, row/cell locators and auditor dispositions. Prose fields alone do not make results reproducible. No schema decision is made in this draft.

## 6. Questions Saqlain must answer

1. Which checks belong in v1? A small option is C3-C5 plus C9. C1/C2/C6 need more scope or action evidence. C7 needs a threshold. C8 needs entitlements and a matrix.
2. What does one record represent: employee, account, employee/system or entitlement? Which key is authoritative? How should repeated IDs and the 200/212/220 mismatch affect testing?
3. Which system list, HR roster and account inventory are authoritative? What dates and service-account populations must they cover?
4. Does Approved prove completion? Who may approve? Can a batch signature replace a missing row date or reviewer? What does Exception mean?
5. What proves removal: disabled state, deletion, ticket completion or a follow-up export? What delay is allowed after review decisions and termination?
6. Which review frequency applies to each system and privileged account population? What proves a completed cycle beyond a dated row?
7. Is dormancy measured at review date or export date? Is the threshold 30, 60, 90 or another number? Is the boundary strictly greater than the threshold? How do unknown logins and service accounts count?
8. Which permission conflicts and self-review rules should be tested? Can the evidence supply stable identities and effective dates?
9. Do notes remain open until independent proof, or can an auditor approve a documented exception? What approval, expiry and compensating-control fields are required? Should approved exceptions remain in the flagged count with a separate disposition?
10. When inputs are missing, should the app request further evidence and show Not testable? Can other checks continue? What prevents a partial test from appearing to cover the whole control?
11. Should issues stay grouped under one conclusion/finding? How should one source row linked to ISO and NIST avoid duplicate follow-up actions?
12. What minimum run record and source viewer does Saqlain need to reproduce a result? Who confirms mappings, and when must they be reconfirmed?
