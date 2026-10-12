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

## Drift notes (2026-10-12, Claude): the line references above are stale
The handoff was written before #134 and #135. Scope is unchanged; use these locations instead of the numbers in "Files" and "Do":
- v1 `criteria=()` is in `app/services/requirement_card.py` at about lines 660 and 683 (two branches), next to `V1_SOURCE_LABEL` (line 25). Re-read the function; do not trust a line number.
- The guard that refuses v1 "add to RFI" is `if card.source != "v2" or match is None` inside `add_rfi_request` (about line 806). Part 2c relaxes the `source` half only; keep the `match is None` stale check and idempotent recording.
- `tests/test_p6_7b_add_to_rfi.py` (about lines 413-463, `test_scenario_3_stale_foreign_and_v1_requests_are_refused`) currently asserts that v1 cards show no add control and the route refuses. Part 2c reverses that on purpose: update that test deliberately to the new behaviour and keep its stale and foreign-request assertions.
- Budget lists on the card (`budget_skipped_filenames`, `budget_partial_filenames`, around lines 169, 210, 331, 643) are Evidence fix C and are not part of E4. Do not touch them: reads stage 1 changes them next.
- Writing rules for the catalogue: plain short sentences, no em dashes, own words, no standard text, no AI attribution anywhere (commits, code, PR body).
- Run tests with `OPENROUTER_KEY=""` and the repo `.venv` (Python 3.13). Never `env -u`.
- Do not open `validation/companies/*/answer_key.json`.

## Results

Implemented locally on `codex/e4-checklist-rfi-examples` (2026-10-12). Evidence fix C is present through merged PR #133.

### Changes

- Historical v1 cards show current signed registry criteria with design/operating kind, statement, evidence hint and source basis under “Auditor checklist; not used by this analysis”. No criterion is marked met or unmet. Empty GDPR/HIPAA/PCI packs render no checklist. Conclusions with no linked run retain their no-run display.
- v1 card requests support add, repeat-add and withdraw. Stale keys and foreign conclusions are still refused. Audit recording stays append-only and idempotent.
- Added `app/services/rfi_examples.py` with 51 explicit types. ISO has 30 registry requests and NIST has 25, giving 34 distinct registry types. DPDPA has 15 types from `scope_profiler._build_evidence_checklist`, matching `DPDPA_DOCUMENT_TYPES`. DPDPA, GDPR, HIPAA and PCI have no registry evidence requests. Four additional legacy upload aliases and `other` are covered.
- Scoped document requests and card-added requests preserve the original request first, then include mapped controls' signed statements, hints and source bases, a document example, what a useful response contains, and blank auditor period/sample fields. Existing audit request text is enriched during document assembly, so old events receive the same guidance without being rewritten.
- The existing source checksum includes this guidance. Changing signed criteria or catalogue wording makes a generated draft stale before issue. Source keys and document schema versions are unchanged.
- Removed the PDF/DOCX export's 300-character evidence-request cut-off. PDF cards use measured continuation segments; footer placement no longer creates empty pages. This extra file was necessary for the examples and auditor fields to appear in downloaded RFIs.
- Analysis prompts, scoring, LLM calls and Evidence C budget lists are unchanged. No answer-key file was opened.

### Verification

- Before implementation: v1 checklist/add tests failed as expected (4 failed, 5 passed); the strengthened scoped-request test failed because guidance was absent.
- Final focused command: `OPENROUTER_KEY="" .venv/bin/python -m pytest tests/test_p5_6_rfi_rebuild.py tests/test_p6_7_requirement_card.py tests/test_p6_7b_add_to_rfi.py tests/test_p6_1b_framework_batching.py tests/test_rfi_examples.py tests/test_rfi_export_full_requests.py -q`: **139 passed**. This includes unchanged prompt fingerprints, all catalogue coverage, v1 empty-pack handling, original request retention and idempotent add/withdraw guards.
- Full-suite rerun: `OPENROUTER_KEY="" .venv/bin/python -m pytest -q --disable-warnings`: **1702 passed, 29 skipped** in 314.22 seconds. The first full run had one obsolete source-checksum assertion collected during the test update; the settled rerun passes.
- After the review wording correction, the complete focused command above was repeated: **139 passed** in 33.25 seconds. The full run predates only that RFI heading correction, which this focused rerun covers.
- Completed local review (`status: complete`, run `e4-review-20261012`, five review lenses plus an independent validator) found one P2 wording issue: the shared RFI must not claim its checklist was unused by v2 analysis. Fixed the RFI heading to “Auditor checklist”; the mandated disclaimer remains on v1 cards. A strengthened test first failed on the old heading and passes after the correction. The original review verdict was “Ready with fixes”; its sole finding is now applied and verified, with none left unresolved. Independent external Claude review could not run in the network-disabled session. Review receipt: `/private/tmp/e4-review-20261012/review.json`.
- Five stress-test PDF pages rendered with `pdftoppm` and visually inspected. All 100 evidence lines, the final sentinel and the following request survive; cards do not overlap. QA artifact: `/private/tmp/e4-rfi-final.pdf`. DOCX full text verified structurally; no Word visual render performed.
- `git diff --check` and compilation of the changed Python modules pass. No lint/typecheck command is configured in this repository.
- Browser attempt: fixture-backed ISO/GDPR conclusions rendered through FastAPI TestClient. A local HTTP server could not bind (`PermissionError: Operation not permitted`). The in-app browser was also unavailable. Desktop/mobile screenshots and the Veldhara click-through were not performed. The four click-through steps above remain for Saqlain.

### Catalogue review list / draft PR body

V1 conclusions now expose signed auditor criteria and accept evidence requests. Scoped and card-added RFI documents include signed guidance, evidence examples and blank auditor period/sample fields. PDF and DOCX exports retain the full requests.

The following catalogue is a draft for Saqlain's wording sign-off. It does not set sample sizes, periods or criterion outcomes.

| Document type | Example of what to send | Good looks like |
|---|---|---|
| `access_control_policy` | Access policy and a dated user list per system with reviewer sign-off and removals. | Identify each system, reviewer and review date. Link removal decisions to completed tickets. |
| `age_verification` | Age check workflow, screen captures and records of completed checks. | Show where the check occurs and how its result is recorded. |
| `application_security_testing` | Security requirements, test reports and release acceptance records. | Identify the application version, test date, findings and follow-up decisions. |
| `asset_inventory` | Export of hardware, software and data inventories with owners and classifications. | Include an export date and explain which systems and locations it covers. |
| `audit_reports` | Privacy audit reports and the associated action tracker. | Include the audit scope, date, reviewer and status of each follow-up action. |
| `backup` | Backup schedule, job results and restore test records. | Identify the systems tested, test dates, results and unresolved issues. |
| `breach_procedure` | Incident response plan, escalation contacts and notification workflow. | Include the current version, owner and records of any exercises or use. |
| `business_continuity` | Continuity and recovery plans with exercise reports. | Identify the services covered, exercise dates, outcomes and follow-up actions. |
| `change_management` | Change procedure and tickets showing review, approval and deployment. | Keep ticket dates, approvers, affected systems and rollback details visible. |
| `cloud_services` | Cloud service register and provider assurance reports. | Identify each provider, service owner and the period covered by each report. |
| `configuration_baselines` | Hardening baseline and configuration exports from managed systems. | Identify baseline versions, system names, export dates and recorded exceptions. |
| `consent_form` | Consent form, collection screen captures and withdrawal workflow. | Include the form version, purposes displayed and how consent choices are recorded. |
| `consent_forms` | Consent forms, collection screen captures and withdrawal workflow. | Include form versions, purposes displayed and how consent choices are recorded. |
| `cross_border_safeguards` | Transfer register, destination list and agreements supporting overseas processing. | Identify the data, recipient, destination and agreement that applies to each transfer. |
| `cryptography_policy` | Encryption standard, key inventory and key rotation records. | Identify covered systems, key owners, dates and configuration sources. |
| `csf_profiles` | Current and target cybersecurity profiles with an improvement tracker. | Include profile dates, scope, priorities and owners of planned actions. |
| `data_flow_diagram` | Data flow diagram and inventory of the data moving between systems. | Label systems, data categories, recipients and the diagram revision date. |
| `dpia` | Impact assessment and its risk action tracker. | Identify the processing activity, assessment date, reviewers and action owners. |
| `dpia_reports` | Impact assessment reports and their risk action trackers. | Identify processing activities, assessment dates, reviewers and action owners. |
| `dpo_appointment` | DPO appointment letter, role description and reporting chart. | Include the appointment date, work location, responsibilities and contact details. |
| `exercise_records` | Incident tabletop or recovery exercise report and action tracker. | Identify the scenario, exercise date, participants, outcomes and action owners. |
| `grievance_mechanism` | Grievance procedure, contact page and case register. | Show the responsible contact and dated records of intake, responses and closure. |
| `hr_privacy_notices` | Employee privacy notice and records of how it was shared. | Include the notice version, covered employee groups and communication dates. |
| `hr_security` | HR security procedure and onboarding, screening and leaver checklists. | Keep completion dates, responsible roles and links to asset or access actions visible. |
| `incident_log` | Incident register and investigation or closure reports. | Include incident dates, owners, response actions and references to supporting records. |
| `isms_audit_reports` | Internal security audit reports and management review minutes. | Include meeting or audit dates, scope, decisions and follow-up owners. |
| `isms_scope` | Approved scope statement with a diagram of the covered organisation and systems. | Identify covered services, locations, boundaries and the document version. |
| `leadership_oversight` | Board or leadership cybersecurity reports and meeting minutes. | Include meeting dates, attendees, decisions and assigned actions. |
| `legal_register` | Register of legal and contractual obligations with assigned owners. | Identify each obligation, affected activities and the last review date. |
| `logging_monitoring` | Logging standard, alert records and dated log review tickets. | Identify source systems, reviewers, timestamps and follow-up actions. |
| `media_disposal` | Disposal procedure, deletion records and destruction certificates. | Link each record to the asset or data, disposal date and responsible person. |
| `network_security` | Network diagram and an export of current firewall rules with change dates. | Identify firewalls, rule owners, review dates and decisions on unused or changed rules. |
| `other` | Relevant supporting document, system export or dated activity record. | Explain which request it supports, its source and the period it covers. |
| `outsourced_development` | Development supplier contracts and delivery review records. | Identify the supplier, project, review dates and accepted or outstanding findings. |
| `parental_consent` | Parental consent form, guardian check workflow and completed consent records. | Show the form version, verification steps and dates of recorded decisions. |
| `physical_security` | Site access procedure, visitor logs and physical security inspection records. | Identify the site, record dates, reviewers and follow-up actions. |
| `privacy_policy` | Current privacy notice and screen captures showing where people receive it. | Include the notice version, covered services and publication or distribution dates. |
| `processing_records` | Processing activity register with data categories, purposes and recipients. | Identify activity owners, systems used and the register review date. |
| `remote_working_policy` | Remote work and device policy with distribution or device configuration records. | Identify the policy version, covered staff and dates of supporting records. |
| `retention_policy` | Retention schedule, deletion procedure and completed deletion records. | Identify data categories, retention triggers, owners and deletion dates. |
| `risk_assessment` | Risk assessment method, risk register and treatment action tracker. | Include assessment dates, risk owners, decisions and action status. |
| `risk_management_strategy` | Cybersecurity risk strategy and documented risk appetite decisions. | Identify the approving body, approval date and scope of the strategy. |
| `roles_responsibilities` | Security organisation chart and responsibility matrix. | Include named roles, assigned responsibilities and the last update date. |
| `sdlc_policy` | Development procedure, coding guidance and release review records. | Identify repositories, release versions, reviewers and review dates. |
| `security_policy` | Approved security policy and records of its review and distribution. | Include the policy version, owner, approval date and intended audience. |
| `statement_of_applicability` | Current applicability register with decisions and supporting references. | Include the version, scope, decision owners and reasons for exclusions. |
| `supplier_security` | Supplier register, security review records and signed agreements. | Link each supplier to its services, review dates, risks and follow-up actions. |
| `training_records` | Training materials and completion records for staff and specialist roles. | Identify course versions, training dates, audiences and completion status. |
| `vendor_agreement` | Signed processor agreement and the associated service description. | Identify parties, signing dates, data handled and the applicable service. |
| `vendor_agreements` | Signed processor agreements and associated service descriptions. | Identify parties, signing dates, data handled and the applicable services. |
| `vulnerability_management` | Scan reports, patch records and vulnerability remediation tickets. | Identify scanned systems, scan dates, issue owners and remediation status. |

### Delivery and review status

Implementation and catalogue review material are in the working tree. No commit or PR was created: this checkout has a pre-existing unpushed handoff commit (`71950e3`), and the session permits read-only access to `.git` with no approval escalation. The catalogue list above is ready to copy into the PR body. Saqlain's catalogue sign-off and the project-required Claude review remain external gates.


### Review fixes (2026-10-12)

- Applied all nine findings locally. RFI requests use a block-level `cc-pre` element; the page loads the stylesheet defining `white-space: pre-line`. Unknown and empty stored document types use the `other` example. Added ISO/DPDPA rendered-guidance checks, stronger show-only checklist assertions, original-reason retention and a no-linked-run add refusal (409).
- PDF checks now require sentinel ordering across pages, first-page `Page n/N` numbering and safe non-latin-1 text. Cards require space for the header and five body lines (or all remaining lines if fewer); one/two-line carry-overs become at least three. Regression cases cover both orphans and metadata-only widows. DOCX retains full status and strips XML-illegal request controls, including null and vertical tab.
- Focused command: `OPENROUTER_KEY="" .venv/bin/python -m pytest tests/test_p5_6_rfi_rebuild.py tests/test_p6_7_requirement_card.py tests/test_p6_7b_add_to_rfi.py tests/test_rfi_examples.py tests/test_rfi_export_full_requests.py tests/test_rfi_docx_determinism.py tests/test_p6_1b_framework_batching.py -q`: **155 passed** in 37.76 seconds.
- Full command: `OPENROUTER_KEY="" .venv/bin/python -m pytest -q --disable-warnings`: **1716 passed, 29 skipped** in 326.05 seconds. `git diff --check` passes. Changes remain uncommitted.

PR-body notes:

- Existing generated RFI drafts show "source changed" once and need regenerating because the source fingerprint now includes guidance.
- RFI PDFs now have about half the pages because blank footer-only pages are gone.
- v1 "add to RFI" suggestions can duplicate a scoped document item under "Additional evidence requested", same as v2 today.
- Design preview strings in `app/routers/design_s7_cards.py` still show the old v1 label. That file remains untouched.


### Option A (2026-10-12)

- Readability revision: document and card-added requests keep every existing item key and add `summary`, `what_to_send`, `example` and `good_looks_like`. Grouping retains 12 artifacts for ISO access control, with five nested specifics under Access control policy. Its seven controls and 20 signed criteria remain in `why_we_ask`. Plain-text `request` uses section breaks, supports lines and nested bullets, with no access-request line longer than 100 characters.
- HTML uses real artifact and specific lists, separate Example and Good looks like rows limited to 70ch, short auditor fields, and a closed checks fold. Criterion statements appear only inside the fold. Existing classes and spacing tokens are reused. Stored snapshots lacking summary and artifacts keep their pre-line request text; PDF and DOCX also retain their legacy paths.
- PDF uses measured hanging bullets at 4 mm and 8 mm text indents. The optional appendix remains before Response Instructions. DOCX uses List Bullet and List Bullet 2, with smaller grey control ids. Fingerprints still include catalogue wording, request text and signed checks. No prompt, analyzer, scoring, LLM or protected card-router edits were made; changes remain uncommitted.
- Export inspection: generated a real ISO RFI from `tests.test_p5_6_rfi_rebuild._seed`, with scope answers `{}` and all applicable ISO controls. Files are `/private/tmp/e4-optionA/iso-rfi.pdf` and `iso-rfi.docx`. Ran `pdftoppm -png -r 80` into that directory, opened the page images and contact sheets, and inspected the access block plus every appendix page individually. Final PDF: **33 pages**, access request **page 5**, appendix **pages 18-32**, Response Instructions **page 33**. It has no blank pages and a footer on every page. The access request is one complete scannable card, with no overlapping text.
- Visual fixes: added space between appendix criterion groups; kept statements, hints and complete source bases together; prevented metadata-only request continuations; kept section labels with their values and whole requests together when they fit a page. Wrapped bullets hang beneath their text. Widened the structured DOCX request column so nested bullets have a usable measure. XML/style inspection confirms **12 List Bullet** paragraphs and **5 List Bullet 2** paragraphs in the access request, and **118/108** across the ISO document. Two DOCX generations are byte identical.
- Mobile inspection limitation: generated the real HTML with an isolated fixture database and attempted Chromium at **375px**. The sandbox denied Chromium's Mach port registration (`bootstrap_check_in ... Permission denied`); the computer-use connector has no available browser. DOM checks pass, and the template uses a shrinking value column, wrapping auditor row and overflow wrapping, but actual 375px visual/overflow verification remains pending.
- Focused command: `OPENROUTER_KEY="" .venv/bin/python -m pytest tests/test_p5_6_rfi_rebuild.py tests/test_p6_7_requirement_card.py tests/test_p6_7b_add_to_rfi.py tests/test_rfi_examples.py tests/test_rfi_export_full_requests.py tests/test_rfi_docx_determinism.py tests/test_rfi_artifact_guidance.py tests/test_rfi_why_html.py tests/test_rfi_why_exports.py tests/test_p6_1b_framework_batching.py -q --disable-warnings`: **175 passed** in **40.06 seconds**.
- Final full command: `OPENROUTER_KEY="" .venv/bin/python -m pytest -q --disable-warnings`: **1,736 passed, 29 skipped** in **340.75 seconds**. This final run includes the additional appendix boundary regression. `git diff --check` passes.
- Character counts across all **30 ISO document requests**: access **5,833 before Option A, 1,366 final**; ISO median **2,174.5 before, 659 final**. The interrupted dense attempt was 1,203 for access and 618.5 median. The small increase adds readable hierarchy and line breaks while keeping signed criteria outside the main request.

Final access-request "What to send" structure:

```text
What to send
- Access control policy
    supports: ISO.A5.15, ISO.A5.17, ISO.A5.18, ISO.A8.2, ISO.A8.3, ISO.A8.5
    - identity management procedure (ISO.A5.16)
    - access request tickets (ISO.A5.18)
    - user access review records (ISO.A5.18)
    - privileged account list, approvals (ISO.A8.2)
    - privileged access review records (ISO.A8.2)
- System access listings
    supports: ISO.A5.15, ISO.A8.3
- Identity provider export
    supports: ISO.A5.16
- HR leaver list
    supports: ISO.A5.16, ISO.A5.18
- Asset inventory
    supports: ISO.A5.16
- Security policy
    supports: ISO.A5.17
- Training records
    supports: ISO.A5.17
- Configuration baselines
    supports: ISO.A5.17, ISO.A8.5
- Identity provider logs
    supports: ISO.A5.18
- System role matrices
    supports: ISO.A8.3
- Assessor test results
    supports: ISO.A8.3
- Identity provider configuration export
    supports: ISO.A8.5
```

### Option A review round (2026-10-12, Claude)

Checked on the generated RFI for the live Veldhara run (93 v1 ISO conclusions): HTML page at desktop and 375 px, the PDF (rendered to images) and the DOCX (paragraph styles).

- **Source basis is off client documents.** Signed `source_basis` strings carry auditor notes (for example "repo description omits the ownership element of the control", 40 such strings across ISO, NIST and DPDPA). The PDF and DOCX appendix now print statement and evidence hint only. The consultant's HTML fold and the cards still show source basis.
- **Readable hints.** Nearly every signed hint uses internal ids (`asset_inventory`). The rows carry `evidence_hint_label` (ids become plain names, details kept) and the appendix and fold show it. The signed hint itself is unchanged.
- **Plain names for 51 document types** (`DOCUMENT_NAMES`, `artifact_name`) with an acronym rule, replacing auto-humanised ids ("Hr security" is now "HR security procedures", "Roles responsibilities" is now "Roles and responsibilities").
- **RFI page:** the framework pill shows once per request, not once per control (seven identical "ISO 27001" pills before). At 375 px the checkbox column wrapped below the text instead of squeezing it to half width.
- **Result for the ISO access request:** 12 "What to send" lines (down from about 60 lines of criteria); the PDF is 29 pages (34 before this round, 33 in the first Option A pass); no source basis, no internal ids and no repo notes anywhere in the PDF or DOCX; DOCX uses List Bullet and List Bullet 2.
- **Verified:** focused set 182 passed. Full suite with `OPENROUTER_KEY=""`: 1743 passed, 29 skipped.

