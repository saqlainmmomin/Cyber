# Flow rework S1: build the demo company (Codex)

Builder: Codex. Written 2026-10-07 by the Claude design/spec lane. Branch: `codex/flow-s1-demo-company` (worktree already set up). Leave changes **uncommitted**; the orchestrator commits and reviews.
Plan: `docs/plans/2026-10-07-001-flow-rework-plan.md`, slice S1 and "Testing with company data". Decisions there are settled. Do not reopen them.

## Goal
A walkthrough fixture. The owner seeds a fresh SQLite file, starts the app, and clicks through screens nobody has seen with realistic data (follow-ups, analysis, review queue, conclusions, findings, report, versions, comparison). Their comments become slice S8.

It is **not an evaluation set**. Nothing is named `answer_key`. Never read `validation/companies/*/answer_key.json`. Never tune a prompt or the analyzer against anything here. `tests/test_answer_key_isolation.py` must stay green.

## Scope of changes
Create only:
- `scripts/demo/__init__.py` (empty)
- `scripts/demo/seed_demo.py` (entry point)
- `scripts/demo/files.py` (demo file generators)
- `scripts/demo/README.md` (owner walkthrough)
- `tests/test_demo_seed.py` (one lean test)
- `scripts/demo/files/` only if you decide to commit generated files. Default: generate at seed time into `<db dir>/uploads/demo_files/`, commit nothing binary (`uploads/` is gitignored at any depth; `<db dir>/demo_files/` is not and dirties git).

Do **not** edit anything in `app/`, `scripts/seed_test_companies.py`, `design/harness/*`, or any context doc (CLAUDE.md, AGENTS.md, tasks/todo.md). Import helpers from `scripts/seed_test_companies.py`; do not copy large blocks from it.

## 1. The company (fictional)
**Veldhara Logistics Pvt Ltd.** Pune-based B2B freight and warehousing company. Not a real company or brand, not a KPMG client. Check the name does not collide with an existing client name in `scripts/seed_test_companies.py` or `design/harness/seed_*.py`.

- Industry `other`, size `large` (the only valid enum values that fit: `app/schemas/assessment.py:7-24` has no logistics industry, and `large` is 500-5000 staff). About 850 staff, 11 depots, 2 data rooms.
- Systems: a cloud-hosted TMS (transport management) built by a vendor, SAP-based finance, a driver mobile app (vendor built, Android), an on-prem HR system, Microsoft 365, a managed SOC from a third-party provider.
- Personal data: employee records, driver KYC and live location, consignee names and phone numbers, small-business customer KYC for credit terms. **No children's data.** Some data goes to a parent group in Singapore.
- No in-house software development (buys and configures). This makes ISO A.8.25 and DPDPA children's controls honestly "not applicable".
- Deliberate **strengths:** information security policy (approved, reviewed yearly), grievance handling with a named officer, data classification, DR failover (tested and passed this year).
- Deliberate **weaknesses:** no consent withdrawal in the driver app, supplier security reviews are ad hoc, incident response plan exists but was never tested, awareness training lapsed this year (a regression from last year), quarterly access review still skips two systems, backup restore is untested.
- Reviewer name used everywhere: `Meera Joshi` (do not reuse `Priya Sharma`, the old demo, or `Anika Rao`, which exists in `design/harness/seed_s6.py:131`).
- Engagement: `FY2026-27 privacy and security assessment`.

## 2. Dates
Anchor = today (`date.today()`). All business dates are offsets from the anchor, like `_at(anchor, offset)` in `scripts/seed_test_companies.py`.
- Client, engagement and prior assessment created at -330 days.
- Prior assessment released at -290 days.
- Current assessment created at -45 days. Its period: start = anchor -120, end = anchor -30, evidence cut-off = anchor -20 (set through `report_basis.update_report_basis`, `app/services/report_basis.py:179`). PRIOR gets a period one year earlier (start -485, end -395, cut-off -320).
- After PRIOR's snapshots are issued, set the `assessment.released` AuditEvent `created_at` for PRIOR to -290 days, and set `ReportSnapshot.generated_at` of PRIOR's snapshots to -290 too. `report_snapshots.generated_after` (`app/services/report_snapshots.py:552-572`) compares rowids, not timestamps, so changing these timestamps afterwards is safe.
- Interim ISO 27001 check assessment created at -10 days. Its period: start = anchor -90, end = anchor -15, evidence cut-off = anchor -10. Approval is refused without a recorded period (`conclusion_review.py:234-239` calls `report_basis.approval_blocker`), so this basis is set before INTERIM's approvals.
- NIST assessment created at -14 days.

## 3. Assessments to seed
All four belong to engagements under the one new client Veldhara. Engagement A holds PRIOR, CURRENT and INTERIM (comparison matches by `company_name`, `web.py:3450`, so PRIOR and CURRENT must carry the same name). Engagement B (`NIST CSF 2.0 baseline`, same client) holds NIST. Create engagement A through `POST /engagements`, then add CURRENT and INTERIM with `_add_assessment_to_engagement` (`scripts/seed_test_companies.py:1741`; keyword args `engagement, client, description, framework_ids, created_at`). Create engagement B through `POST /engagements` with form fields `client_mode=existing` and `client_id=<veldhara id>` (`web.py:1274-1283`; `client_mode=new` with a taken name is refused).

### 3a. PRIOR (released, `dpdpa` + `iso27001`)
Description: `FY2025-26 baseline (DPDPA + ISO 27001)`.
- Scope answered (see scope table). Context set (see section 5). Status `completed`.
- 3 evidence files (policy PDF, ROPA DOCX, access review DOCX), mapped to requirements through `POST /api/evidence/{id}/uses`.
- Questionnaire fully answered by the same rule as CURRENT but shifted worse (see 4).
- Stubbed analysis with the PRIOR items table below. All conclusions approved (NA ones through the normal approve route, see 6). Findings: 2 (consent withdrawal, supplier security). Set the report basis, then released through `POST /api/assessments/{id}/release`, then a `gap_report` and a `workpaper` snapshot generated and the workpaper issued (see 8).

### 3b. CURRENT (late state, `dpdpa` + `iso27001`)
Description: `FY2026-27 reassessment (DPDPA + ISO 27001)`.
- Scope done; evidence uploaded (section 9); questionnaire **fully answered** (every non-skipped question); at least **two seeded follow-ups** (section 7, visible only if S0b renders them); analysis results present (stub); conclusions as in the CURRENT items table; 3 findings; released report version(s).
- Final state: 15 conclusions, **all approved and released** (13 approved plus 2 not applicable), 0 pending. Pending rows would block release and break Comparison (`approved_report.py:400-404,575-582`, `review_gate.py:32-33`, `web.py:3456,3182-3186`), so CURRENT stays fully released.
- Final stage shown by `assessment_stage.stage()`: the released stage. Print it.

### 3c. INTERIM (review state, `iso27001` only, engagement A)
Description: `Interim ISO 27001 check`. This is the assessment that shows the pending review queue.
- Created at -10 days. Scope: `ISO.SCP.1..4` as in the scope table. Context set. Questionnaire fully answered by the section 4 rule. No evidence upload; if approval needs captured citations, the stub item builder supplies them.
- Stub analysis with exactly 6 ISO ids: `ISO.A5.1`, `ISO.A5.18`, `ISO.A5.24`, `ISO.A5.30`, `ISO.A6.3`, `ISO.A8.13`, statuses and risk as in the CURRENT column.
- Set the report basis (section 2 dates: -90, -15, cut-off -10), then approve 3 (`ISO.A5.1`, `ISO.A5.30`, `ISO.A8.13`). Leave 3 pending (`ISO.A5.18`, `ISO.A5.24`, `ISO.A6.3`). Do not release it.
- Expected stage: Review, "3 pending" style label.

### 3d. NIST (early state, `nist_csf` only)
Description: `NIST CSF 2.0 baseline`.
- Scope done (`NIST.SCP.1..4`). Context set.
- 2 evidence files uploaded: the policy PDF and the consent screen PNG (section 9). No desk review run, so no document-sourced rows (they are hidden without a completed DeskReviewSummary with grounded findings, `web.py:2530,2585`, `question_engine.py:90-100,225-245`).
- Questionnaire about **half answered**: answer every question in the first half of the sections (sorted by the question dict's `section` key, which holds the domain group; there is no `domain_group` key, `question_engine.py:303-306`) and none in the rest. Use the web save route (`POST /assessments/{id}/questionnaire/save`, form fields `section_id`, `answer_<qid>`, `notes_<qid>`; `web.py:2621-2645`), one section per call, so the rows get realistic `answer_source`.
- Status `questionnaire_done` is not required. Leave it where the routes put it. No analysis, no conclusions.
- Expected stage: Questionnaire, "N of M answered".

## 4. Questionnaire answers: a rule, not a list
Read the questions the UI shows, not a static list. Order: save scope, then narrow `assessment.applicable_requirements` to the section 6 ids (PRIOR, CURRENT and INTERIM only; INTERIM uses its 6 ISO ids from 3c). NIST is not narrowed: it keeps the set the scope save computes. Then call `build_adaptive_questionnaire(assessment_id, db)` (`app/services/question_engine.py:381`). Excluded controls are removed from the questionnaire (`question_engine.py:283-290`), not marked, so no extra not-applicable rule is needed. Take every question whose `status != "skipped"`. Sort by `(section, id)` (the `section` key holds the domain group, `question_engine.py:303-306`).

Assign answers by this rule, and print the final table (domain, counts per answer) when seeding:
1. Domain match by case-insensitive substring of the domain group, topic or question text:
   - **Strong** (`policy`, `governance`, `grievance`, `classification`, `continuity`, `disaster`, `physical`): 70% `fully_implemented`, 30% `partially_implemented`.
   - **Weak** (`incident`, `breach`, `supplier`, `vendor`, `third`, `processor`, `consent`, `awareness`, `training`, `backup`): 15% `fully_implemented`, 35% `partially_implemented`, 25% `planned`, 25% `not_implemented`.
   - **Everything else**: repeat the cycle `fully, fully, partially, fully, partially, not_implemented, fully, planned`.
2. Position within a domain decides the bucket (index modulo 20, or the cycle above). No randomness. Re-running gives identical answers.
3. For PRIOR, downgrade every `fully_implemented` at an index divisible by 3 to `partially_implemented`, and every `partially_implemented` at an index divisible by 4 to `not_implemented`.
4. For every answer that is not `fully_implemented`, set `notes` to one plain sentence from a small pool of 6 to 8 realistic notes (for example "Process exists but is not documented.", "Owner identified, rollout planned next quarter."). Cycle through them deterministically.
5. Submit PRIOR, CURRENT and INTERIM in one `POST /api/assessments/{id}/responses` call each (it replaces all rows; do it before inserting follow-ups). Without it INTERIM's `stage()` stays on Questionnaire (`assessment_stage.py:120-124`). NIST uses the web save route instead (3d). Set `confidence` to `medium`.

## 5. Scope and context
Scope through `POST /assessments/{id}/scope/save` (form fields = question ids; INTERIM uses only the `ISO.SCP.*` rows). Partial saves are allowed without the `scope_form` field.

| Question | CURRENT and PRIOR | NIST |
|---|---|---|
| `SCP.1` | `yes` | |
| `SCP.2` | `no` (no children's data) | |
| `SCP.3` | `possibly` | |
| `SCP.4` | `both` | |
| `SCP.5` | `yes` | |
| `SCP.6` | `no` | |
| `ISO.SCP.1` | `full_org` | |
| `ISO.SCP.2` | `yes` (cloud) | |
| `ISO.SCP.3` | `no` (no development) | |
| `ISO.SCP.4` | `yes_datacenter` | |
| `NIST.SCP.1` | | `no` |
| `NIST.SCP.2` | | `tier2` |
| `NIST.SCP.3` | | `no` |
| `NIST.SCP.4` | | `current_only` |

Verify every option value exists in the framework definitions (`app/frameworks/definitions/*.py`, `app/dpdpa/scope_questions.py`). The values above come from `design/harness/seed_s5.py` and the definitions. If a value is invalid, pick the nearest valid one and note it in the seed output. Do not change the definitions.

The context gate (`questionnaire_tab.html:27-40,69`, `context_done`) needs `assessment.context_answers` or `context_profile` set. Set both directly on the model as dead data, as `design/harness/seed_s5.py::_context` does, with values that describe Veldhara. Do not call the context wizard routes (they call an LLM). Slice S3 deletes the gate later; this is harmless.

## 6. Stubbed conclusions
`applicable_requirements` is set to exactly the ids below (as `_analyze` in `scripts/seed_test_companies.py:2099` does) right after the scope save and before the questionnaire is built (section 4), so the conclusion set is small and complete. Reuse `_scripted_item`, `_analyze`, `_create_finding`, `_release_assessment`, `_upload_assessment_document`, `_map`, `_expect`, `_at`, `_create_hierarchy` where their signatures fit. They currently read module-level `ITEMS`, `FINDING_SPECS`, `DEMO_REVIEWER`. If reuse needs a different table, write thin local wrappers in `seed_demo.py` that patch `analysis.run_multi_framework_analysis` the same way. Do not edit the originals. Do not reuse `_approve_conclusions`: it hardcodes 2026 period dates and reads the module globals (`scripts/seed_test_companies.py:2140-2152`). Write a local approve loop that runs after the report basis is set and approves the requested ids through the normal approve route.

Verify every id exists in `FrameworkRegistry` at startup; abort with a clear message if not. Ids below were checked against the definitions on 2026-10-07. The registry is only populated at app startup (`app/main.py:123`), so run the check after entering `TestClient`, not at import.

| Id | PRIOR | CURRENT |
|---|---|---|
| `CH2.CONSENT.1` | partially_compliant, medium | compliant, low |
| `CH2.CONSENT.3` | non_compliant, high | non_compliant, high |
| `CH2.NOTICE.1` | partially_compliant, medium | partially_compliant, medium |
| `CH2.SECURITY.1` | non_compliant, high | partially_compliant, medium |
| `CH3.GRIEVANCE.1` | partially_compliant, medium | compliant, low |
| `CH4.CHILD.1` | not_applicable | not_applicable |
| `ISO.A5.1` | compliant, low | compliant, low |
| `ISO.A5.18` | non_compliant, high | partially_compliant, medium |
| `ISO.A5.19` | non_compliant, high | non_compliant, high |
| `ISO.A5.24` | non_compliant, high | partially_compliant, medium |
| `ISO.A5.30` | partially_compliant, medium | compliant, low |
| `ISO.A6.3` | compliant, low | partially_compliant, medium (regression) |
| `ISO.A8.5` | partially_compliant, medium | compliant, low |
| `ISO.A8.13` | partially_compliant, medium | partially_compliant, medium |
| `ISO.A8.25` | not_applicable | not_applicable |

That is 15 rows. PRIOR and CURRENT both have 15 conclusions.

Status values are `compliant`, `partially_compliant`, `non_compliant`, `not_applicable` (map at `app/services/analysis_pipeline.py:54-59`; `partial` is not valid). `_scripted_item` only maps three statuses for `maturity_level`, so add a local item builder for NA rows with `compliance_status="not_applicable"`, `risk_level="low"`, `maturity_level=0` and a rationale that cites the scope answer (for children's: "Scope answer SCP.2 = No: the company does not process children's data." For A.8.25: "Scope answer ISO.SCP.3 = No software development."). NA rows are approved through the normal approve route like any other (`conclusion_review.py:157-174`: not a gap outcome, so no gaps or action text is needed). Do not use the `edit` route.

Findings (through `POST /api/assessments/{id}/findings`):
- PRIOR: `CH2.CONSENT.3` (high, owner Rhea Kapoor), `ISO.A5.19` (high, owner Arjun Mehta).
- CURRENT: `CH2.CONSENT.3` (high, owner Rhea Kapoor, target -20 days, so overdue), `ISO.A5.19` (high, owner none, target +60 days), `ISO.A6.3` (medium, owner Arjun Mehta, target +30 days).
Use fresh finding and action titles. Do not reuse text from the old demo.

### Order of operations for CURRENT
Release is refused while any in-scope conclusion awaits a decision (`app/services/approved_report.py:553-585`). Pending rows live on INTERIM (3c), so CURRENT never reopens anything:
1. Set the report basis (period and cut-off) through `report_basis.update_report_basis` (`app/services/report_basis.py:179`).
2. Approve all 15 (NA ones included).
3. Create the 3 findings.
4. Release.
5. Generate and issue snapshots (section 8).

## 7. Follow-ups (depends on S0b)
Saving follow-up answers is broken on this branch: `POST /assessments/{id}/questionnaire/save` writes follow-up text into `QuestionnaireResponse.answer`, which has a CHECK constraint (`app/models/questionnaire.py:13-16`, `web.py:2670-2695`). S0b fixes it in a separate PR. **Do not fix it here.**

Even when saving works, follow-ups are **not visible in the UI today**: the panel only fills on an answer change through the LLM route (`web.py:2712-2775`, `section_questions.html:100-109`), and `FU.` rows are excluded from the answered count (`web.py:1924`). Print the note `follow-ups are stored but visible only if S0b also renders stored follow-ups`. The README says the same.

Seed 2 follow-ups on CURRENT, on two different weak-domain questions from the narrowed question set (section 4) whose parent answer is `partially_implemented` or `not_implemented` (one DPDPA-covered cluster, one ISO-covered cluster). Use the real route: `POST /assessments/{id}/questionnaire/save` with form fields `section_id`, the parent answers, and `followup_FU.<question_id>.1` set to a two-sentence realistic answer (for example about the driver app's consent screen and the vendor roadmap).

Detect whether S0b is merged by trying it:
- Wrap the call in `try/except Exception`; roll back the session on failure.
- Success = a `QuestionnaireResponse` row with `question_id` starting `FU.` exists afterwards and the free text is readable from the row (in `notes` or the new column, whichever S0b chose; do not assume).
- On failure, print `follow-ups skipped: needs S0b (follow-up storage fix)` and continue. The seed still succeeds.
Do not seed follow-ups by writing rows directly. The point is to prove the real route works.

## 8. Report versions and comparison
After release, per released assessment (PRIOR and CURRENT only):
- `POST /api/assessments/{id}/snapshots` with `type=workpaper` (HTML, no renderer needed), then `.../snapshots/{snapshot_id}/issue`.
- Also try `type=gap_report`. If it raises or returns 503 (`RendererUnavailable`), print a note and continue.
Do not call `board_report` (needs report inputs); skip it.
Expected: `/assessments/{id}/snapshots` lists versions for both; `/assessments/{current}/compare/{prior}` renders a delta (needs both `status == "completed"`, same `company_name`, both released).

## 9. Demo evidence files (`scripts/demo/files.py`)
Plain Python, no network. Content is deterministic; byte-identical output is not promised (fpdf2, docx and openpyxl embed timestamps). Use `python-docx` (already used), `fpdf2` (requirements.txt), `openpyxl` (requirements.txt), `Pillow` (`requirements-dev.txt`; if import fails, skip the PNG with a printed note).
All PDF text goes through the repo's `S()` latin-1 sanitizer (`app/utils/pdf_export.py`) or stays ASCII. Plain ASCII is simplest.

| File | Used on | Upload `category` | Content |
|---|---|---|---|
| `Veldhara_Information_Security_Policy_v3.1.pdf` | PRIOR, CURRENT, NIST | `security_policy` | One page. Owner CISO, approved by the board risk committee, reviewed every 12 months, MFA for remote access. |
| `Veldhara_Records_of_Processing_FY26.docx` | PRIOR, CURRENT | `processing_records` | Table of processing activities (driver KYC, consignee contacts, payroll), purposes, retention. |
| `Veldhara_Access_Review_Q2_FY26.docx` | PRIOR, CURRENT | `access_control_policy` | Quarterly review covering 9 of 11 production systems; says two systems were out of scope. |
| `Veldhara_Incident_Response_Plan_v1.pdf` | CURRENT | `breach_procedure` | Roles and steps. A line says "not yet tested". |
| `Veldhara_DR_Failover_Test_Report.docx` | CURRENT | `business_continuity` | Failover completed in 3h 10m against a 4h RTO. |
| `Veldhara_Driver_App_Consent_Screen.png` | CURRENT, NIST | `consent_form` | Screenshot-like image, 1280x720: a mock app screen with text "I agree to location tracking" and one button, no withdraw option. Drawn with Pillow text. |
| `Veldhara_User_Access_Review_Export.xlsx` | CURRENT | `access_control_policy` | Sheet "Users": 40 rows, columns user, system, role, last_login, reviewer_decision. A second sheet "Summary". |
| `Veldhara_Access_Review_Dec_2023.docx` | CURRENT | `access_control_policy` | **Stale file.** Filename and first line: "User access review, 31 December 2023". Period start is nearly 3 years later, so the staleness is obvious to a reader. |

`category` is required on upload (`app/routers/documents.py:40-41`) and must be in `document_categories(assessment.frameworks)` (`app/services/document_categories.py`), else 422. Checked against the live vocabulary: `security_policy`, `access_control_policy`, `breach_procedure`, `business_continuity` come from the ISO and NIST evidence requests; `processing_records` and `consent_form` are legacy categories valid for every framework. Do not use `consent_forms` (plural): it is DPDPA-only and invalid on the NIST assessment.

**Upload helper.** `_upload_assessment_document` builds DOCX bytes itself, so it cannot upload PDF, PNG or XLSX. Write a small local helper in `seed_demo.py` that posts arbitrary bytes, filename, content type and `category` to `POST /api/assessments/{id}/documents`, then backdates `Evidence.created_at` and `EvidenceVersion.created_at` the same way.

The image goes through the vision path on upload (`app/services/document_processor.py:165`, `_call_claude_vision`). The stub in section 10 must return canned text for it, shaped like the real output (`[Screenshot: <file>]` is added by the caller; the stub returns `VISIBLE TEXT: ... SUMMARY: ...`).

**xlsx handling.** `detect_file_type` (`document_processor.py:227`) accepts only pdf, docx and images today, so the xlsx upload is rejected until S6-F1. Implementation: always attempt the upload through `POST /api/assessments/{id}/documents`. If the response is 201, keep going and map it. If it is 4xx, print `xlsx skipped: not accepted by this build (S6-F1 not merged); this gap is intentional` and continue. Do not extend the accept list. The same attempt-then-skip applies to nothing else.

**Stale file.** Backdate `Evidence.created_at` and `EvidenceVersion.created_at` as `_upload_assessment_document` does with `received`, but for the stale file leave `received` at the normal upload date. The staleness comes from the document's own date. There is no as-of field until S6-F2, so do not invent one.

Backdating for the rest: PRIOR files at -325; CURRENT files at -40 (policy and ROPA reused via the evidence-reuse route are optional; skip reuse, upload fresh copies); NIST files at -12.

Map evidence to requirements (`POST /api/evidence/{id}/uses`) for CURRENT: policy to `ISO.A5.1` (primary) and `CH2.SECURITY.1` (supporting); ROPA to `CH2.NOTICE.1`; Q2 access review DOCX (`Veldhara_Access_Review_Q2_FY26.docx`) to `ISO.A5.18`; the stale Dec 2023 file stays unmapped; IR plan to `ISO.A5.24`; DR report to `ISO.A5.30`; PNG to `CH2.CONSENT.3`. Mirror similar mappings for PRIOR. NIST gets exactly two files, the policy PDF and the PNG, and only the policy is mapped (`NIST.GV.PO.01`). INTERIM has no evidence.

## 10. How it runs (`scripts/demo/seed_demo.py`)
CLI: `python scripts/demo/seed_demo.py [--db PATH]` and env var `DEMO_DB` as the fallback for `--db`. Default DB: `data/demo.db` (never `data/dpdpa.db`).

0. **Paths and pipeline.** Put the repo root on `sys.path` before any repo import (running `python scripts/demo/seed_demo.py` puts `scripts/demo` there, not the root). Set `os.environ["ANALYSIS_PIPELINE_VERSION"] = "v1"` too.
1. **Set settings before any `app` import.** `app.database` builds its engine from `settings.database_url` at import time and `ensure_sqlite_parent_dir` creates the directory. Parse args first, then set `os.environ["DATABASE_URL"] = f"sqlite:///{abs_path}"` and `os.environ["UPLOAD_DIR"] = str(<db dir>/uploads)`, then import. Generated demo files go to `<db dir>/uploads/demo_files/`. Refuse to run if the resolved DB path equals the developer DB (`data/dpdpa.db`).
2. **Clean DB:** run Alembic to head against that file the way tests do (`command.upgrade` with `alembic.ini`, see `_alembic_config` in `tests/test_longitudinal_demo.py:60`). Entering `TestClient(app)` as a context manager also runs the lifespan upgrade; either is fine. It must work from a missing file.
3. **Idempotent:** if the Veldhara client exists, delete only its rows. `purge_existing` (`scripts/seed_test_companies.py:1260`) covers legacy tables only, so do not rely on it. Per Veldhara engagement: set `status` to `archived` (`retention.ARCHIVED_STATUS`), build `plan = retention.build_purge_plan(db, engagement)` (`app/services/retention.py:690`) and run the deletes from `retention._purge_scopes(plan)` (line 590; same loop as `purge_engagement`, lines 1056-1110, but skip its eligibility and confirm checks, which would refuse a fresh demo). Then delete the Engagement and Client rows, commit, and `rm -rf` every path in `plan.blob_roots` under `UPLOAD_DIR` (built by `_blob_roots`, `retention.py:583-587`: `evidence/<eng_id>`, `reports/engagements/<eng_id>`, and per assessment `reports/assessments/<assessment_id>` and `<assessment_id>`). An explicit ordered table-delete list is acceptable if this proves brittle. Other data is never touched. Test with a second, unrelated client present.
4. **No-LLM guard (stub must be active):**
   - Patch `app.services.llm_client._get_client` to raise `AssertionError("The demo must never call the LLM.")` (as `no_llm` in `tests/test_longitudinal_demo.py:131`).
   - Patch `app.services.document_processor._call_claude_vision` to return canned text for the PNG.
   - Patch `app.routers.analysis.run_multi_framework_analysis` with the scripted item function, as `_analyze` does.
   - Set `settings.openrouter_key = ""` in-process. The `.env` file may still load a real key, so after imports blank it if it is not empty and print a note. The seed must not need a key and must never use one.
   - Before seeding, assert the three patches are installed (`llm_client._get_client is not original`). If not, print `refusing to run: LLM stub not active` and exit 2.
   - Use `unittest.mock.patch` contexts around the whole seed. No network anywhere.
5. Use `TestClient(app)` as a context manager with `app.dependency_overrides[get_db]` bound to one `SessionLocal` session (the pattern in `seed_longitudinal_cli`, `scripts/seed_test_companies.py:2445`). Importing `scripts.seed_test_companies` is allowed after step 1; it imports `app.main`.
6. Seed order: client and engagement A with PRIOR; CURRENT; INTERIM; engagement B with NIST. Then print a manifest.
7. Output: one line per major step, then the manifest (ids of client, engagements, assessments, a count of conclusions by state per assessment) and the URL list from section 12 with real ids filled in. Print every skip note again in a final "Skipped" block. Exit 0 even if only skippable parts were skipped.

Do not read `validation/`. Do not write any file named `answer_key`.

## 11. Order of the whole seed
1. Guard, DB, purge.
2. PRIOR: create (engagement A), backdate, scope, narrow applicable requirements, context, upload and map 3 files, questionnaire, stub analysis, set report basis, approve all, findings (2), release, snapshots, then backdate the release AuditEvent and the snapshots' `generated_at` to -290.
3. CURRENT: add to engagement A, scope, narrow, context, upload and map files (including the stale file and the xlsx attempt), questionnaire, follow-ups (or skip note), stub analysis, set report basis, approve all, findings (3), release, snapshots.
4. INTERIM: add to engagement A, scope, narrow, context, questionnaire, stub analysis, set report basis, approve 3.
5. NIST: create (engagement B), scope, context, upload 2 files, map the policy, half questionnaire.
6. Manifest and URLs.

## 12. Walkthrough README (`scripts/demo/README.md`)
Write it for the owner, plain and short. Contents:
1. Commands (exact):
   - `python3.13 -m venv .venv && . .venv/bin/activate && pip install -r requirements-dev.txt` (only if not already set up)
   - `python scripts/demo/seed_demo.py --db data/demo.db`
   - `OPENROUTER_KEY="" DATABASE_URL=sqlite:///data/demo.db UPLOAD_DIR=data/uploads uvicorn app.main:app --host 127.0.0.1` (the empty key stops `.env` loading a real one)
   - A note: re-running the seed replaces only Veldhara; `rm data/demo.db` for a full reset; no API key needed. AI buttons (desk review, follow-up generation, context wizard, drafting) error in the demo; that is expected, do not click them.
2. The list of URLs in this order, one line each on what to look at. Use the ids the seed prints (describe them as `<current>`, `<prior>`, `<interim>`, `<nist>`, `<eng-a>`, `<eng-b>`):
   1. `/` dashboard: Veldhara, two engagements, status of each assessment.
   2. `/engagements/<eng-a>`: prior and current released, interim in review.
   3. `/assessments/<current>`: overview; note the next step shown.
   4. `/assessments/<current>?tab=scope`: scope answers and what each did.
   5. `/assessments/<current>/evidence`: uploads, including the stale-dated file and the png. For the xlsx, see the seed's Skipped block.
   6. `/assessments/<current>?tab=questionnaire`: all answered. Follow-ups are stored but visible only if S0b also renders stored follow-ups; otherwise the seed's printed note applies.
   7. `/assessments/<current>/conclusions`: 13 approved, 2 not applicable, 0 pending.
   8. `/assessments/<interim>/conclusions`: the review queue, 3 approved, 3 pending. (`/assessments/{id}/review` is a documented 303 to `/conclusions`, `web.py:3259-3271`; there is no separate review screen to compare.)
   9. `/assessments/<current>/findings`: 3 findings, one overdue.
   10. `/assessments/<current>?tab=report` and `/assessments/<current>/report-summary`: released report.
   11. `/assessments/<current>/snapshots`: versions list.
   12. `/assessments/<current>/compare/<prior>`: delta against last year.
   13. `/assessments/<prior>/snapshots`: the prior release.
   14. `/assessments/<nist>`: early state; next step shown.
   15. `/assessments/<nist>?tab=questionnaire`: half done.
   16. `/assessments/<current>/rfi`: the RFI screen as it is today.
3. "Leave comments" section: ask the owner to write comments as a list in `tasks/2026-10-08-s1-walkthrough-comments.md` (create it themselves), one line per screen, using the Design pass checklist wording from the plan. No action needed from Codex beyond mentioning this.
Verify every URL pattern in the README against `app/routers/web.py` before writing it; drop any that 404 and say so in the final report.

## 13. Test (`tests/test_demo_seed.py`)
One file, lean, no snapshots, no pixel checks.
- Run `scripts/demo/seed_demo.py` logic against a `tmp_path` SQLite file through its importable `main(argv)` or `seed(db_path)` function (make the entry point importable; keep the `if __name__ == "__main__"` guard).
- Because `app.database` reads settings at import, either run the seed in a subprocess (`subprocess.run([sys.executable, "scripts/demo/seed_demo.py", "--db", str(db)], cwd=REPO_ROOT)`) and then open the file with SQLAlchemy to assert, or follow how existing tests redirect settings. A subprocess is the simplest and also proves the clean-DB path. Set `OPENROUTER_KEY=""` in the subprocess env (do not unset it; `.env` would still load and a real key would then spend money).
- Assert: client Veldhara exists; 4 assessments exist with the expected frameworks (PRIOR and CURRENT `["dpdpa","iso27001"]`, INTERIM `["iso27001"]`, NIST `["nist_csf"]`); PRIOR has 15 conclusions all locked and a release event; CURRENT has 15 conclusions, 0 pending, 2 NA and a release event, 3 findings, at least one issued snapshot; INTERIM has 6 conclusions, 3 pending, no release event; NIST has no conclusions, a partial questionnaire (answered between 20% and 80% of total), 2 evidence rows; no row with `answer_source` outside the known values; every uploaded `EvidenceVersion` has non-empty `extracted_text`.
- Assert the seed is idempotent: run it twice, the Veldhara client count is 1 and the assessment count is 4. In the same test add an unrelated `Client` row after the first run and assert it survives the second.
- Assert the dev DB path (`data/dpdpa.db`) was not created or modified (the `conftest.py` session guard already covers this).
- Skip, do not fail, follow-up assertions when the seed printed the S0b skip note. Assert follow-ups exist only if S0b is merged.

## 14. Acceptance checks (run all and report the evidence)
1. `python scripts/demo/seed_demo.py --db <tmp>/demo.db` from a missing file exits 0 and prints the manifest, URLs and a Skipped block.
2. Run it a second time: exits 0, same counts, other data untouched.
3. Start the app on that DB (with `OPENROUTER_KEY=""`) and `curl -s -o /dev/null -w "%{http_code}"` every README URL: each is 200 (or a documented 303 to a 200 page). Paste the table of URL and status. Do not use a browser; do not call any network host besides 127.0.0.1.
4. For each of the four assessments, print stage via `assessment_stage.stage()` and the conclusion state counts, and compare with the targets in section 3.
5. `pytest tests/test_demo_seed.py -q` passes. Then run the full suite once (`pytest -q`) and report pass/fail counts. Any failure not caused by this change is reported, not fixed.
6. `git status` shows only the files under "Scope of changes". `git diff --stat` for `app/` is empty.
7. `/assessments/<current>/compare/<prior>` returns 200 with a delta, and both Versions pages return 200.
8. Grep proves no `answer_key` string and no `validation/` read in the new files: `grep -rn "answer_key\|validation/" scripts/demo tests/test_demo_seed.py` returns nothing.

## 15. Judgment left to you
- Exact wording of notes, follow-up answers and document text, as long as it is short, realistic and plain.
- Whether to import helpers from `scripts/seed_test_companies.py` or write thin wrappers where signatures do not fit. Do not modify that file.
- How to implement the purge for idempotence (service helper vs ordered deletes), as long as only Veldhara rows go.
- Whether to also seed desk-review summaries for CURRENT (optional; skip if it needs more than a few lines or any LLM path).
- Using `gap_report` snapshots only if the renderer works offline in your environment.

## 16. Rules
Never write the literal string `answer_key` anywhere under `scripts/` or in tests, not even in a comment or a "we never read this" note: `tests/test_answer_key_isolation.py` scans `.md` and `.py` files for it. No em dashes in anything you write (code comments, README, handoff results). Plain short sentences. No network. Do not install packages (Pillow is in `requirements-dev.txt`; if missing, skip the PNG with a note). Do not commit or push. No Claude or Codex attribution anywhere.

## Results

Files created:

- `scripts/demo/__init__.py`
- `scripts/demo/seed_demo.py`
- `scripts/demo/files.py`
- `scripts/demo/README.md`
- `tests/test_demo_seed.py`

Acceptance evidence:

- Fresh seed completed with exit 0 and printed the database line, manifest, URL list, stages, and Skipped block.
- Second seed completed with exit 0. It purged only the Veldhara client and engagements. An unrelated client survived and Veldhara still had one client and four assessments.
- Prior: 15 conclusions, 1 release event, and issued workpaper plus gap-report snapshots.
- Current: 15 conclusions, 2 not applicable outcomes, 3 findings, 1 release event, and issued workpaper plus gap-report snapshots.
- Interim: 6 conclusions, 3 approved and 3 pending, with no release event. Its printed stage was `review` with `3 of 6 approved`.
- NIST: 0 conclusions and 23 of 106 questionnaire responses, which is within the required partial range. It has 2 evidence rows.
- Every Veldhara evidence version had non-empty extracted text. Answer sources were within the known values.
- `assessment_stage.stage()` printed prior and current as report, interim as review, and NIST as questionnaire.
- Comparison returned 200. Both versions pages returned 200.
- All 17 README URL patterns returned 200 through an in-process TestClient smoke check. A live uvicorn bind on 127.0.0.1 was blocked by the sandbox with operation not permitted, so curl could not be run.
- `pytest tests/test_demo_seed.py tests/test_answer_key_isolation.py -q` passed: 3 passed.
- The full `pytest -q` run reached collection but was blocked by missing environment dependencies: `boto3` for the AWS test module and `python-pptx` for the PowerPoint test module. No new-test failure was reported.
- The forbidden-string scan and em-dash scan were clean. `git diff -- app` was empty. Git status showed the five new files above plus this required Results edit.

Skips:

- XLSX upload was rejected as expected by the pre-S6-F1 build. The exact intentional skip note was printed.
- Follow-up storage was rejected by the current CHECK constraint as expected before S0b. The exact S0b skip note was printed, followed by the stored-follow-up visibility note.
- Pillow was available, so the consent PNG was generated and uploaded.
- The gap-report renderer worked offline, so no gap-report skip ran.

Deviation:

- The current UCC questionnaire had no non-full DPDPA weak-domain parent under the generic deterministic answer cycle. To preserve the requested two follow-up walkthrough states, the seed makes the first eligible DPDPA weak parent partially implemented before using the real follow-up route. This is deterministic and is reported in the implementation rather than changing application code.

No files were committed or pushed.

### Orchestrator verification and fix pass
- Seed from a clean DB: exit 0 in ~4 s. Stages: prior report (released), current report (released), interim review (3 of 6 approved), NIST questionnaire (23 of 106). Comparison 200.
- Live server on the demo DB: all 17 walkthrough URLs return 200 with seeded content; no errors in the server log; repo tree stays clean.
- Review fixes: the DB guard now refuses any file named `dpdpa.db` or without "demo" in its name (the old guard only covered this worktree's `data/dpdpa.db`); `OPENROUTER_KEY` is blanked in the environment before any `app` import, and the stub check now fails closed (key empty and the three stubs active); the purge refuses to remove the upload root itself; demo uploads move to `<db dir>/uploads/demo` (README updated) so they never mix with other uploads.
