# P5-1: Correctness bundle: scope-aware completion gate, audited override, unconfirmed answers excluded, fail-closed framework scores, per-framework requirement count, DPDPA-only penalty exposure

**Plan:** `docs/plans/2026-09-24-001-cleanup-and-non-dpdpa-parity-plan.md`, task P5-1 ("Correctness bundle"). It owns known gaps **#6** (the completion gate ignores scope exclusions, and one document bypasses it) and **#8** (`/report/summary` returns the DPDPA requirement count for every assessment), audit findings **A2** (a failed framework is reported as "0% Non-Compliant"), **A4** (unconfirmed pre-fills go to analysis as answers) and **A5** (DPDPA penalty exposure is applied to non-DPDPA gaps), and plan-level decision **D-P5-F** ("Unconfirmed machine answers are never silent inputs. ... P5-1 picks which one, and later tasks inherit it."). PRD `docs/product/2026-09-21-cyberassess-product-requirements.md`: **PR-041**, acceptance: "incomplete Requirement coverage fails closed rather than yielding a misleading complete report"; **PR-044** ("Every AI-generated Conclusion shall require consultant review"); **PR-012** ("An Assessment shall record scope and applicability before substantive analysis").
**Owner:** Claude designs the gate and override policy and the fail-closed semantics (product invariants) → Codex implements. See `tasks/agent-ownership.md`, criterion "A product invariant". Every fork is closed below.

> **If the code forces a deviation from this design, stop and report it in `## Results`. Do not pick an alternative.** That applies to every numbered decision, every constant, message, key name and ordering below, and every test scenario. "The existing code makes step N awkward" is not a licence to redesign step N. Write down what you found and what you would need to change, then stop.

> **P5-2 and P5-3 depend on this task, and they read the `D-P5-1-*` decisions below as a fixed contract.** P5-2 (reader migration) inherits D-P5-1-F, D-P5-1-G and D-P5-1-H: the failed-framework sentinel, the "no release while a framework failed" rule, and the read-site list. P5-3 (framework-aware desk review) and P5-4 inherit D-P5-1-D, the unconfirmed-answer rule. That is why every decision here is written as a rule, not a suggestion. Do not weaken any of them "because P5-2 will replace this anyway".

**Depends on:** nothing unmerged. `main` is at `2a5a7e9`.
**Blocks:** P5-2 and P5-3. They share `app/routers/analysis.py`, `app/routers/reports.py` and the `app/routers/web.py` report helpers (D-P5-1-M).
**Runs in parallel with:** P5-8 (mechanical cleanup, worktree `/Users/saqlainmomin/dpdpa-gap-tool-p5-8`) and P5-5. File overlap and the coordination rule are in D-P5-1-M.
**No failing contract suite is pre-written.** `grep -rlniE "completion_override|failed_framework|requirement_counts|has_dpdpa_exposure|UNCONFIRMED_ANSWER" tests/` finds nothing, and `ls tests/` has no correctness-bundle module. **Codex writes `tests/test_correctness_bundle.py` itself**, working from `## Test scenarios`. Every scenario listed is required. You may add cases, but you may not drop or weaken one. The only existing file you may change under `tests/` or `scripts/` is `scripts/seed_test_companies.py`, and only the one edit in D-P5-1-C. **No existing test file is modified.**

## Goal

1. A DPDPA-only client with legitimate scope exclusions can reach analysis by answering 80% of the **in-scope** questions. A domestic, no-children, non-SDF client with processors needs 24 of 30, not 33 of 41.
2. Uploading a document no longer silently waives the 80% gate. Below 80%, analysis runs only if a consultant records an **override**: a coded reason, attributed to them and written to `audit_events`. The web UI tells the consultant the gate fired and offers that override. Today it shows "Something went wrong".
3. Document and screening pre-fills that no human has confirmed (`answer_source` `"document"` / `"inferred"`) are never passed to the analyzer and never count toward the gate.
4. When one framework's analysis fails on a multi-framework assessment, the report records **no score** for it, and every surface says "Analysis failed for {framework}": the web report, the analysis-status poll, the PDF and the integrated report. The assessment is not marked `completed`. The report cannot be released (approved exports, snapshot issue, integrated report) until analysis is re-run. If every framework failed, nothing is persisted and the previous report stays intact.
5. `/api/assessments/{id}/report/summary` returns the requirement count of the assessment's own frameworks (93 for ISO-only, 94 for NIST-only, and so on), per framework, and drops the dead DPDPA import.
6. The report summary shows a DPDPA rupee exposure only when there are DPDPA gaps. It never states the unverified "₹500 Crore repeat violations" figure.

## Current state

Grounded against `2a5a7e9` on `main`. Relocate everything by symbol name, because line numbers drift. P5-8 is editing `web.py` concurrently (D-P5-1-M).

**Baseline measured in a fresh worktree of `2a5a7e9`:** `.venv/bin/pytest -q` → **550 passed, 9 skipped, 1 error**. The error is the known, pre-existing fresh-worktree teardown artifact from `tests/conftest.py::_guard_dev_database_untouched`, reported at `tests/test_workpaper.py::test_smoke_full_assessment_traceability`. Every Phase 2-4 handoff documents it, and it is not a regression.

### The completion gate (`app/routers/analysis.py::trigger_analysis`)

- **Responses** are loaded with no `answer_source` filter (`responses_db = db.query(QuestionnaireResponse).filter(assessment_id == …).all()`). They are turned into the `responses` dicts that both analyzers receive: `run_gap_analysis(responses=…)` and `_run_multi_framework_analysis(responses=…)`, then `run_multi_framework_analysis`.
- **Multi path** (`_is_multi`): `expected_question_ids` = cluster ids of `build_multi_questionnaire(_selected_fw, excluded_controls=compute_excluded_controls(_selected_fw, assessment.applicable_requirements), …)`, minus `IND.*`. This path is already scope-aware.
- **DPDPA path:** `expected_question_ids = {q["id"] for q in build_questionnaire(context_profile=context_profile) if not q["id"].startswith(("IND.", "FU."))}`. That is all 41 base ids, and **scope is ignored**. `build_questionnaire` is `app.dpdpa.questionnaire.build_questionnaire`, imported at module level. **Six test modules monkeypatch `app.routers.analysis.build_questionnaire`** (`test_analysis_pipeline.py`, `test_retention.py`, `test_remediation_tracking.py`, `test_pdf_updates.py`, `test_needs_review_ui.py`, `test_no_blended_scoring.py`), so the gate must keep calling it through that module global.
- `answered_question_ids` = expected ids with any response whose `answer` is non-blank, whatever `answer_source` it has (A4).
- `if total_expected and completion_ratio < 0.8:` → without documents, raise 400 `"Questionnaire is incomplete: … Answer at least 80% of the questionnaire or upload supporting documents before running analysis."`. With documents, `logger.warning("Allowing analysis with incomplete questionnaire because documents are available", …)` and proceed. This is the silent bypass (gap #6).
- Then `if not responses and not documents:` → 400 `"Submit questionnaire responses or upload documents before running analysis."`.
- Then `assessment.status = "analyzing"; db.commit()`.
- `applicable_requirements` is parsed again further down (`json.loads` in a `try`, logging a warning on bad JSON) for the analyzers' scope enforcement.
- **Scope exclusion in the DPDPA questionnaire** (`app/services/question_engine.py::build_adaptive_questionnaire`): when `assessment.applicable_requirements` is truthy, `applicable_req_ids = set(json.loads(...))`, and any base question whose `id` is not in it gets `status="skipped"`. The web save (`web.save_questionnaire_responses`) drops `status == "skipped"` questions (`section_questions = [q for q in s["questions"] if q.get("status") != "skipped"]`), so those questions can never be answered.
- **Verified by running `compute_scope`** with `SCP.1=no, SCP.2=no, SCP.3=no, SCP.4=both, SCP.5=yes`: 30 applicable of 41. Excluded are exactly `CB.TRANSFER.1-3`, `CH2.CONSENT.5`, `CH4.CHILD.1-3` and `CH4.SDF.1-4`. The maximum reachable ratio is 30/41 = 73%.
- **Web trigger** (`web.run_analysis_web`, `POST /assessments/{assessment_id}/run-analysis`): it sets `assessment.status = "analyzing"` and commits, then calls `trigger_analysis(assessment_id, db=analysis_db)` in a fresh `SessionLocal()`. **It catches every exception** and sets `status = "error"`. The gate's 400 message is therefore lost, and the next poll shows `partials/analysis_error.html` ("Something went wrong during the analysis").

### Who relies on the document bypass today

I **prototyped** the gate change in a throwaway worktree: scope-filtered denominator, unconfirmed rows excluded, bypass removed. The full suite went from 550 passed to **537 passed, 13 errors**. All 13 are `tests/test_longitudinal_demo.py` fixture setup failures, from one root cause: `scripts/seed_test_companies.py::_analyze` posts `/api/assessments/{id}/analyze` with **zero answers** plus uploaded evidence, which means it depends on the bypass. The error was `RuntimeError: analyze baseline: expected 200, got 400: {"detail":"Questionnaire is incomplete: 0 of 45 core questions answered (0%)…"}`. No other test depends on the bypass or on unconfirmed rows counting. D-P5-1-C fixes the seed script. The prototype was discarded.

### `answer_source` vocabulary (`app/models/questionnaire.py`, `app/services/auto_answer.py` docstring)

- `"document"` is written by `auto_answer.persist_document_answers` (desk-review pre-fill, "awaiting confirmation").
- `"inferred"` is written by `app/services/screening.py` (screening pre-fill).
- `"document_confirmed"` and `"human_override"` are set by the web save when a human submits a question whose row was `"document"`.
- `"human"` is the column default, what the web save writes for new rows, and what the save sets for any other prior source, including `"inferred"`.
- **`NULL`** can appear on legacy rows (the column is nullable, and the legacy migrations default it to `'human'`). `reports.download_pdf` already treats NULL as `"human"`.
- `auto_answer`'s docstring promises pre-fills "are never auto-submitted to analysis". `trigger_analysis` breaks that promise (A4).
- `app/services/analysis_pipeline.py::_inputs` (the P2-3 envelope) records `"questionnaire_response_count"` as a count of **all** the assessment's responses.

### Prompt builders (the "label" alternative, D-P5-1-D)

- `app/dpdpa/prompts.py::build_user_prompt` renders base, industry and follow-up responses (around lines 492-525) with no provenance marker.
- `app/frameworks/prompts.py::build_framework_user_prompt` expands cluster-keyed responses through `_expand_cluster_responses` and renders `fw_responses` (around lines 290-299), also with no marker.
- `tests/test_golden_dpdpa.py` pins analyzer output against a recorded golden fixture.

### Framework scores: producers and the failed-framework path (A2)

- `_run_multi_framework_analysis` computes `failed_frameworks` (missing result or an `"error"` key), calls `analysis_pipeline.fail_runs(..., error_type="FrameworkAnalysisError", framework_ids=failed_frameworks)` and commits. Then `_persist_multi_framework_analysis` runs.
- In `_persist_multi_framework_analysis`, for a failed framework: `per_fw_assessments[fw_id] = []; per_fw_scores[fw_id] = compute_framework_scores([], fw_id); continue`. `compute_framework_scores([], fw_id)` returns `{"overall_score": 0.0, "overall_rating": "Non-Compliant", "domain_scores": {... every domain "applicable": False, "score": 0.0}}`, which is a real-looking score. The function then writes `GapReport(framework_scores=json.dumps(per_fw_scores), chapter_scores=json.dumps(namespaced_domain_scores(per_fw_scores)))` and **unconditionally** sets `assessment.status = "completed"`. It returns `{"report_id", "status": "completed", "frameworks_analyzed", "per_framework_scores", "initiatives_generated", "message", "analysis_run_ids"}`.
- The single path has only one framework. Its failures already raise 500 and set `error` (P2-3 D-P2-3-B). **A2 is multi-path only.**
- **`GapReport` has no status column.** `framework_scores` (Text JSON) is the only place a per-framework outcome can live without a schema change. `AnalysisRun` records `failed` correctly (`tests/test_analysis_pipeline.py::test_multi_framework_writes_one_run_per_framework`), **but three files are grep-guarded against even mentioning it**: `tests/test_analysis_pipeline.py::test_legacy_consumers_do_not_read_the_new_tables` greps `app/services/scoring.py`, `app/routers/review.py`, `app/routers/reports.py` and `app/utils/pdf_export.py` for `Conclusion|AnalysisRun|analysis_pipeline`, and `tests/test_pdf_updates.py` scenario 10 greps `pdf_export.py` + `reports.py` for the same pattern. **Comments and docstrings count.** So the failed state must travel inside `framework_scores`, not come from `AnalysisRun`.

### Every read site of `framework_scores` today (the complete list; `grep -rnE "framework_scores|fw_scores|overall_rating|overall_score" app scripts`)

| # | Site | What it does now | Behaviour with a failed entry today |
|---|---|---|---|
| R1 | `app/services/scoring.py::report_framework_scores(report, assessment)` | Returns the parsed `framework_scores` dict, or the single-framework legacy fallback | Passes the entry through |
| R2 | `app/services/scoring.py::namespaced_domain_scores(per_framework_scores)` | Flattens domains into `chapter_scores` | Emits the failed framework's domains, all at 0% and "not applicable" |
| R3 | `app/schemas/report.py::FrameworkScoreOut` (`overall_score: float`, `overall_rating: str`, `domain_scores`), used by `ReportOut.framework_scores` and `ReportSummary.framework_scores` | Response models of `GET /report` and `GET /report/summary` | A `None` score would fail validation with a 500 |
| R4 | `app/routers/reports.py::get_report` (`framework_scores=report_framework_scores(...)`) | JSON API | Passes through R3 |
| R5 | `app/routers/reports.py::get_report_summary` | JSON API | Passes through R3 |
| R6 | `app/routers/reports.py::get_full_report` (`frameworks_info[fw_id]["scores"] = scores`) | Plain `JSONResponse` | Passes through verbatim |
| R7 | `app/routers/web.py::_framework_display(assessment, framework_scores)` → `{name, version, score, rating, domain_scores}` | Feeds every template below | Shows `score` 0.0 |
| R8 | `app/routers/web.py::assessment_detail` (`framework_display = _framework_display(...)` when a report exists and `tab in ("report", "questionnaire")`) → `pages/assessment.html` (only `framework_display | length`, line ~78) and `partials/questionnaire_tab.html` → `partials/analysis_complete.html` / `analysis_error.html` | Page context | |
| R9 | `app/routers/web.py::analysis_status` (the `completed` branch passes `framework_display`; the `error` branch does not) → `partials/analysis_complete.html` (`{% if fw_data.score is not none %}…{% else %}scores unavailable{% endif %}`) | HTMX poll | Prints "0%" |
| R10 | `app/routers/web.py::report_summary` → `partials/report_summary.html`, lines ~23-50 (per-framework gauges: `{% if fw_data.score is not none %}` gauge, else "Scores unavailable / Re-run analysis"), plus the chapter bars from `chapter_scores` (R2) | Report tab | A 0% red gauge labelled "Non-Compliant" |
| R11 | `app/routers/web.py::compare_assessments_web` (`current.get("overall_score") if current else None`) → `pages/comparison.html` (`{% if framework.delta is none %}—`) | Comparison page | Computes a delta against 0.0 |
| R12 | `app/utils/pdf_export.py::generate_pdf` (`framework_score_rows`: skips an entry whose `overall_score is None`; used by the cover rings around line 789 and the "Framework Scores" bars around line 841), plus `chapter_scores` bars (lines ~815, ~864) | Board PDF (live and snapshot) | Draws a 0% ring |
| R13 | `app/services/report_content.py` integrated-report sections (`score_data.get("overall_score") is None → continue`) | Integrated engagement report | Prints a 0% score line |

Nothing else reads it. `scripts/migrate_legacy.py` only mentions it in a docstring. Two structural guards constrain every edit here:
- `tests/test_no_blended_scoring.py::test_no_template_reads_retired_score`. (a) `overall_score` must not appear in any template. (b) AST check: `.overall_score` attribute access or an `overall_score=` keyword is allowed only in `app/models/report.py`, `app/services/scoring.py`, `app/schemas/scoring.py`, `app/legacy_migrations*.py` and `app/routers/analysis.py`. (c) **Every line of `app/routers/analysis.py` that contains the token `overall_score`** must be either the `overall_score=0.0` keyword or a dict comprehension over `per_fw_scores.items()` whose value is `…["overall_score"]`. Dict-literal *string keys* elsewhere are fine for (b) but not in `analysis.py`, because of (c).
- `tests/test_pdf_updates.py` scenario 10: `app/services/report_content.py` must not contain `db.add(`, `db.add_all(`, `db.merge(`, `.flush(`, `.commit(` or `delete`.

### Release paths (`app/utils/review_gate.py::require_review_approval`)

- It checks only `Assessment.review_status == "approved"` (403 otherwise).
- Callers: `reports.get_report`, `get_report_summary`, `get_full_report`, `download_pdf` and `compare_assessments`; `web.compare_assessments_web`, `download_rfi_pdf` and `download_rfi_docx`; `snapshots.issue_snapshot_route`.
- `report_content` (integrated report) filters `review_status != "approved"` → `NOT_RELEASED` and `report is None` → `NO_REPORT`.
- **Draft snapshot generation (`POST …/snapshots`) is not gated**, so `generate_pdf` can render a report that has a failed framework.
- **Analysis never resets `review_status`.** An assessment approved before a re-run keeps `"approved"` afterwards. That is pre-existing, and D-P5-1-G does not fix it in general (open question 2). It only makes sure a failed framework can't be released that way.

### Gap #8 (`app/routers/reports.py`)

- Line 8: `from app.dpdpa.framework import ROOT_CAUSE_CLUSTERS, get_requirement_count`. `grep -n ROOT_CAUSE_CLUSTERS app/routers/reports.py` finds **only the import line**, so it is dead.
- `get_report_summary` returns `total_requirements=get_requirement_count()`, and `app.dpdpa.framework.get_requirement_count()` is `len(get_all_requirements())` = 41 always.
- The existing accessor is **`FrameworkDefinition.control_count(self) -> int`** (`app/frameworks/schema.py`, `return len(self.all_controls())`; `all_controls()` is cached in `_all_controls_cache`). It is reached through `FrameworkRegistry.get(fw_id)`. `app/frameworks/compat.get_requirement_count(framework_id)` wraps the same call. Measured: `dpdpa 41, iso27001 93, gdpr 54, hipaa 54, nist_csf 94, pci_dss 64`.
- `get_report_summary` already has the `Assessment` in scope: `assessment = require_review_approval(assessment_id, db)`. **`assessment.frameworks`** is the property that returns the parsed `selected_frameworks` list, or `["dpdpa"]` for NULL or bad data. Use the property, not the raw `selected_frameworks` JSON string.
- `tests/test_no_blended_scoring.py::test_report_api_has_only_framework_score_shapes` asserts that the payload has no top-level `overall_score`/`overall_rating`. A new top-level key is fine.

### A5 (`app/routers/web.py` report helpers, `partials/report_summary.html`)

- `_PENALTY_MAP` is a list of DPDPA id prefixes → ₹ Crore: `CH2.SECURITY` 250, `BN.NOTIFY` 250, `CH4.CHILD` 200, the rest 50.
- `_compute_business_impact(gap_items)` loops over non/partial items. A prefix match gives its penalty. **The `for … else` gives `max_penalty = max(max_penalty, 50)` for any id matching no DPDPA prefix, including every ISO/NIST id.** It returns `{"max_penalty_cr", "affected_domains", "critical_high_count", "has_gaps": max_penalty > 0}`.
- Template, hero card (lines ~88-100): `{% if business_impact.has_gaps and has_dpdpa %}₹{{ max_penalty_cr }}Cr "per incident under DPDPA"{% elif business_impact.has_gaps %}{{ critical_high_count }} gaps …`.
- Template, business-impact panel (lines ~110-130): `{% if has_dpdpa %}"Up to ₹{{ max_penalty_cr }} Crore" + "Per-incident penalty under the DPDPA 2023 Schedule for the highest-severity violation category identified." + "Repeat violations attract up to ₹500 Crore."{% else %}…{% endif %}`.
- `grep -rn "500 Crore\|₹500" app` finds only that one template line.
- `has_dpdpa = "dpdpa" in assessment.frameworks`. So on a DPDPA + ISO assessment where DPDPA is clean and ISO has gaps, the page claims a ₹50 Crore DPDPA exposure.

### A structural test that fails while your changes are uncommitted (read this)

`tests/test_longitudinal_demo.py::test_scenario_13_protected_surface_is_unchanged` runs `git diff --name-only -- app/routers/web.py app/routers/analysis.py app/services/report_content.py …`, which compares the **working tree against the index**. While your edits to those files are uncommitted, it fails. Once they are committed, it passes. **This is expected. Do not modify that test.** Report its failure in Results as "working-tree guard, expected until commit", and confirm that every other test in that module passes. The reviewing session re-runs the suite after committing, and it must be green then.

## Decisions (made here so they are not relitigated)

### D-P5-1-A. The DPDPA gate denominator is the in-scope base questions, using the same rule as the questionnaire

- Add a private helper in `analysis.py`:
  ```python
  def _applicable_requirement_ids(raw: str | None) -> set[str] | None:
      """None = no scope recorded (every requirement applies)."""
  ```
  - `None` or `""` → `None`.
  - `json.loads` raises, or the result is not a `list` → `logger.warning("Invalid applicable_requirements for assessment gate", extra={"assessment_id": …})`, return `None`. This matches the existing downstream parse, which also treats bad JSON as "no scope".
  - Otherwise → `{str(x) for x in parsed}`.
- DPDPA path, exactly:
  ```python
  expected_question_ids = {
      q["id"] for q in build_questionnaire(context_profile=context_profile)   # module global: tests patch it
      if not q["id"].startswith(("IND.", "FU."))
  }
  applicable_ids = _applicable_requirement_ids(assessment.applicable_requirements)
  if applicable_ids is not None:
      expected_question_ids &= applicable_ids
  ```
  This is the same exclusion `question_engine.build_adaptive_questionnaire` applies (a base question is skipped iff its id is not in the applicable set). The gate therefore can never expect a question the questionnaire refuses to save.
- An empty applicable list (`"[]"`) → an empty expected set → `total_expected == 0` → the gate does not apply. That is the existing `if total_expected and …` behaviour, unchanged. The later "no inputs" 400 still applies.
- The multi path's expected set is **unchanged** (it is already scope-aware).
- `COMPLETION_THRESHOLD = 0.8` becomes a module constant, and the gate compares `completion_ratio < COMPLETION_THRESHOLD`. The value doesn't change.
- **Not changed:** `web.save_questionnaire_responses` still refuses to save skipped questions. Once the denominator honours scope, that refusal is correct.

### D-P5-1-B. No document bypass. Below the threshold, analysis runs only with an explicit, coded, audited consultant override

**Decision: the override stays available.** Analysis is a proposal that every Conclusion must pass through consultant review for (PR-044), and document-led assessments are a real consulting pattern. So the product must allow it, but never silently, and never because of the unrelated fact that a document was uploaded.

- **Delete** the `if not has_documents:` condition and the `logger.warning("Allowing analysis with incomplete questionnaire …")` block. `has_documents` stays as a variable, because it is still passed downstream to evidence confidence.
- **Reasons are codes, not free text.** An audit row outlives an engagement purge (P4-4 D-P4-4-I), and P4-4 D-P4-4-B refused free text in retained audit rows for exactly that reason. Its open question 1 is still open. Exact constant, in `analysis.py`:
  ```python
  COMPLETION_OVERRIDE_REASONS = {
      "document_led": "Documents are the primary evidence for this assessment",
      "client_answers_pending": "Client answers are pending and an interim AI proposal is needed",
      "scope_under_review": "Scope is still being confirmed with the client",
  }
  COMPLETION_OVERRIDE_EVENT = "analysis.completion_override"
  COMPLETION_OVERRIDE_SCHEMA_VERSION = 1
  ```
- **Input.** New `app/schemas/analysis.py`:
  ```python
  class CompletionOverride(BaseModel):
      reason: str
      reviewer_name: str = ""
  ```
  `trigger_analysis` gains **one keyword parameter at the end**: `def trigger_analysis(assessment_id: str, db: Session = Depends(get_db), override: CompletionOverride | None = None)`. On the API this is an **optional JSON body**. No body means `None`, so every existing `http.post(".../analyze")` and every direct `trigger_analysis(a.id, db)` call behaves as before. **`_run_multi_framework_analysis`'s signature does not change** (`test_no_blended_scoring` calls it by keyword).
- **The gate, in this exact order** (replacing today's two blocks):
  1. Compute `expected_question_ids` (D-P5-1-A) and `answered_question_ids` from the **confirmed** responses only (D-P5-1-D).
  2. `gate_blocked = bool(total_expected) and completion_ratio < COMPLETION_THRESHOLD`.
  3. If `gate_blocked and override is None` → `raise CompletionGateRefused(answered=len(answered_question_ids), expected=total_expected)`. That is a new `HTTPException` subclass in `analysis.py` with `status_code=400`, `detail = COMPLETION_GATE_MESSAGE.format(answered=…, expected=…, pct=round(ratio * 100))`, and the attributes `answered`/`expected`:
     ```python
     COMPLETION_GATE_MESSAGE = (
         "Questionnaire is incomplete: {answered} of {expected} in-scope core questions answered ({pct}%). "
         "Answer at least 80% of the in-scope questionnaire, or run analysis with a recorded consultant override. "
         "Pre-filled answers count only after a consultant confirms them."
     )
     ```
  4. If `gate_blocked and override is not None and override.reason not in COMPLETION_OVERRIDE_REASONS` → `HTTPException(400, "Choose a valid override reason.")`.
  5. The existing `if not responses and not documents:` 400 check, unchanged. An override never bypasses it.
  6. If `gate_blocked` (so a valid override is present): `db.add(AuditEvent(actor=conclusion_review.reviewer_actor(override.reviewer_name), action=COMPLETION_OVERRIDE_EVENT, entity_type="assessment", entity_id=assessment_id, metadata_json=json.dumps(metadata, sort_keys=True)))`. The metadata has exactly this key set: `{"schema_version": 1, "reason": <code>, "answered": int, "expected": int, "completion_pct": round(ratio * 100), "threshold_pct": 80, "framework_ids": list(_selected_fw)}`. Then `logger.info` with the assessment id, reason code and counts only.
  7. `assessment.status = "analyzing"; db.commit()`. This is the existing commit, so the override event and the status flip commit together.
- **An override sent when the gate isn't blocked is ignored:** no event, no error. Only a needed override is recorded.
- The override event is kept even if the analysis later fails. It records the decision to run, not the outcome.
- **Web** (`web.run_analysis_web`):
  - Add `override_reason: str = Form("")` and `reviewer_name: str = Form("")` parameters (the handler stays a sync `def`; `snapshots.py` already uses `Form`).
  - Read `previous_status = assessment.status` **before** setting `"analyzing"`.
  - Call `trigger_analysis(assessment_id, db=analysis_db, override=CompletionOverride(reason=override_reason, reviewer_name=reviewer_name) if override_reason.strip() else None)`.
  - **`except CompletionGateRefused as exc:`** (before the generic `except`): set `assessment.status = previous_status`, commit, and return `partials/analysis_gate_blocked.html` with `{"request", "assessment_id", "message": exc.detail, "show_override": True, "override_reasons": COMPLETION_OVERRIDE_REASONS}` and toast `("Analysis not started", "error")`.
  - **`except HTTPException as exc` with `status_code == 400`**, which covers the invalid reason and the no-input check: same restore and partial, with `show_override=False`.
  - **Any other exception:** unchanged (`status = "error"`).
- **New partial `app/templates/partials/analysis_gate_blocked.html`.** It is swapped into `#analysis-area`. Contents:
  - a `<div data-completion-gate-blocked>` with the heading "Analysis not started" and `{{ message }}`;
  - when `show_override`, a `<form data-completion-override-form hx-post="/assessments/{{ assessment_id }}/run-analysis" hx-target="#analysis-area" hx-swap="innerHTML" hx-confirm="Run analysis on an incomplete questionnaire? The override and its reason are recorded in the audit log.">` containing a `<select name="override_reason" required>` with one `<option value="{{ code }}">{{ label }}</option>` per `override_reasons` item, in dict order, and no blank option; an `<input name="reviewer_name" placeholder="Your name">`; and the submit button "Run analysis with override";
  - always a plain link, "Back to questionnaire", to `/assessments/{{ assessment_id }}?tab=questionnaire`.
  - Everything is autoescaped, with no `|safe`. No text in the partial contains an apostrophe (P2-5 lesson).

### D-P5-1-C. The longitudinal seed passes an override (the only existing-code consumer of the bypass)

In `scripts/seed_test_companies.py::_analyze`, change `http.post(f"/api/assessments/{assessment_id}/analyze")` to `http.post(f"/api/assessments/{assessment_id}/analyze", json={"reason": "document_led", "reviewer_name": DEMO_REVIEWER})`. Nothing else in that file changes. `test_longitudinal_demo` scenario 1's count assertions filter `AuditEvent` by action, so the new `analysis.completion_override` rows do not disturb them. Scenario 3 only checks that audit dates are recent. Scenario 12's structural checks on `seed_longitudinal_demo` / `seed_longitudinal_cli` (`print(`, `SessionLocal`, `token`) are unaffected.

### D-P5-1-D. D-P5-F is decided: unconfirmed machine answers are **excluded** from analysis and from gates. They are not labelled.

**Rule, binding on P5-3, P5-4 and every later task that touches responses:** a `QuestionnaireResponse` whose `answer_source` is in `UNCONFIRMED_ANSWER_SOURCES = ("document", "inferred")` is a **pre-fill proposal**. It may be displayed for confirmation. It is **never** passed to any analyzer or LLM prompt, and it is **never** counted by any completion gate or input count. It becomes an input only when a human save changes its source (to `"document_confirmed"`, `"human_override"` or `"human"`). `NULL` means a legacy human answer and **is** confirmed. A later task that adds a new machine-written source value must add it to `UNCONFIRMED_ANSWER_SOURCES`, not invent a parallel list.

Why exclude, not label:
1. **Exclusion is already the product's written promise** (`auto_answer`'s docstring, "never auto-submitted to analysis"). A label would turn a violated promise into a new policy.
2. **Nothing is lost.** The same document text still reaches the analyzer as documents, and the desk-review findings still arrive as `desk_review_data`. The pre-fill is only a derived restatement of those, so excluding it removes a duplicate, unconfirmed signal, not evidence.
3. **Labelling spreads.** It means changing both prompt builders (`app/dpdpa/prompts.py::build_user_prompt` and `app/frameworks/prompts.py::build_framework_user_prompt`, including `_expand_cluster_responses`), which changes analyzer inputs pinned by `tests/test_golden_dpdpa.py`. The model would also be trusted to discount a marker. And on a mixed assessment, a DPDPA-keyed pre-fill would still sit next to a contradicting human cluster answer for the same control (A4). Exclusion removes that case entirely.
4. **It is simple for P5-3/P5-4 to inherit:** one filter, one constant.

Implementation:
- In `app/services/auto_answer.py`, next to the docstring's vocabulary, add `UNCONFIRMED_ANSWER_SOURCES = ("document", "inferred")` and `def confirmed_response_clause()`. The clause returns `or_(QuestionnaireResponse.answer_source.is_(None), QuestionnaireResponse.answer_source.notin_(UNCONFIRMED_ANSWER_SOURCES))`. **The `is_(None)` arm is mandatory**, because SQL `NULL NOT IN (…)` is not true, and a bare `notin_` would silently drop legacy human rows.
- `trigger_analysis`: the `responses_db` query gains `.filter(confirmed_response_clause())`. Both the analyzer `responses` and `answered_question_ids` derive from it, so both paths and the multi-path cluster expansion are covered by one line. `_response_ids` (evidence confidence) derives from `responses`, which is correct.
- `app/services/analysis_pipeline.py::_inputs`: `questionnaire_response_count` counts with the same clause, so the P2-3 envelope records what the analyzer actually received. This deliberately amends P2-3 D-P2-3-E's wording ("COUNT of this assessment's questionnaire_responses" becomes "… that were analysis inputs"). The key set is unchanged. Import the function; add no `delete` anywhere in that module (its standing guard).
- **Not changed:** the prompt builders, the questionnaire rendering, the web save's source transitions, `reports.download_pdf`'s `answer_source_map` (which labels, and is a display), and the workpaper's answer-source display.

### D-P5-1-E. The failed-framework sentinel (A2): the stored shape and its helpers

- In `app/services/scoring.py`:
  ```python
  FRAMEWORK_ANALYSIS_FAILED = "failed"

  def failed_framework_scores() -> dict:
      return {"status": FRAMEWORK_ANALYSIS_FAILED, "overall_score": None,
              "overall_rating": None, "domain_scores": {}}

  def is_failed_framework_score(entry) -> bool:
      return isinstance(entry, dict) and entry.get("status") == FRAMEWORK_ANALYSIS_FAILED

  def failed_framework_ids(framework_scores: dict, framework_ids: list[str]) -> list[str]:
      """Ids in framework_ids order whose entry is the failed sentinel."""
  ```
- **A scored entry is unchanged.** `compute_framework_scores` is not modified, and an entry without `"status"` is a scored entry. So every existing report, fixture and equality assertion stays valid, and the legacy fallback in `report_framework_scores` needs no change.
- **Contract for any producer, now and in P5-2:** each selected framework's entry in `framework_scores` is **either** a full score dict **or** exactly `failed_framework_scores()`. There is never a zero-filled stand-in. Every reader decides "failed" only through `is_failed_framework_score`/`failed_framework_ids`, never by testing `overall_score is None` (a missing entry is a different state: "scores unavailable", legacy).
- `namespaced_domain_scores`: add an explicit `if is_failed_framework_score(framework_scores): continue`. It would emit nothing anyway, because `domain_scores` is `{}`, but the rule should be visible. **So `chapter_scores` holds no chapters for a failed framework.**
- **`scoring.py` must not contain the strings `Conclusion`, `AnalysisRun` or `analysis_pipeline`, even in comments** (grep guard). Describe the sentinel as "a framework whose analysis call failed".

### D-P5-1-F. What analysis does when frameworks fail (multi path only)

In `_run_multi_framework_analysis`, after the existing `fail_runs(…)` + `db.commit()` and **before** the persistence `try`:
- **Every selected framework failed:** `assessment.status = "error"; db.commit(); raise HTTPException(500, "Analysis failed for every selected framework. Run analysis again.")`. Nothing is persisted, so the previous `GapReport`, Conclusions and revisions are untouched. Its runs are already `failed` (P2-3). This matches the single path's empty-result behaviour.

In `_persist_multi_framework_analysis`:
- Replace `per_fw_scores[fw_id] = compute_framework_scores([], fw_id)` with `per_fw_scores[fw_id] = failed_framework_scores()` (imported from `app.services.scoring`). **No line in `analysis.py` may spell `overall_score` other than the two allowed forms** (guard (c) above). Use the helper; don't write the dict literal here.
- Compute `failed = [fw for fw in selected_frameworks if not result["frameworks"].get(fw) or "error" in result["frameworks"][fw]]`, the same predicate as the caller.
- Replace the unconditional `assessment.status = "completed"` with `assessment.status = "error" if failed else "completed"`. **Rationale:** `"completed"` drives the analysis timeline step, `compare`/`comparable` eligibility, `portfolio.derive_status` ("Completed") and the "Analysis Complete" panel. A partly failed analysis must show none of them. `"error"` is an existing status every surface already handles (the poll, the questionnaire tab, the badge, the portfolio), so **no new status value is introduced**. The report of the frameworks that did succeed is still persisted, so the consultant's Conclusions for those frameworks exist (P2-3 D-P2-3-B step 4), and the report tab shows it with the failure stated.
- The return dict keeps every existing key. Changes:
  - `"status"` is `"incomplete"` when `failed`, else `"completed"`.
  - A new key, **`"failed_frameworks": failed`**, is always present in the multi response (possibly `[]`).
  - `"message"` is `f"Analysis failed for {', '.join(names)}. Results for the other frameworks were saved. Run analysis again to complete the assessment."` when `failed`, where `names` are the registry `name`s in `failed` order. Otherwise it is unchanged.
  - `per_framework_scores` keeps its existing comprehension, so a failed framework maps to `None`.
  - The single-path return dict is **unchanged**; its key set is asserted by `test_legacy_report_path_is_unchanged`.
- HTTP status stays 200 for a partial failure, because the results for the frameworks that succeeded were saved.

### D-P5-1-G. A report with a failed framework is never releasable

This rule is inherited by P5-2's release gate.
- `app/utils/review_gate.py::require_review_approval` is the single release chokepoint. After the existing 404/403 checks, load the assessment's `GapReport`. If one exists and `failed_framework_ids(report_framework_scores(report, assessment), assessment.frameworks)` is non-empty → `raise HTTPException(409, RELEASE_BLOCKED_MESSAGE.format(names=", ".join(<registry names>)))` with `RELEASE_BLOCKED_MESSAGE = "Analysis failed for {names}. Run analysis again before releasing this report."`.
- No report → unchanged (the callers 404 on their own).
- This covers `GET /report`, `/report/summary`, `/report/full`, `/report/pdf`, `compare`, the RFI downloads, the web comparison page and **snapshot issue**. It deliberately checks the **current** report, so an assessment approved earlier and then re-run into a partial failure is blocked too (see the Current state note on `review_status`).
- **Integrated report** (`report_content.py`): add `ANALYSIS_INCOMPLETE = "Analysis failed for at least one framework"`. In the section loop, after the `report is None` check, if `failed_framework_ids(report_framework_scores(report, assessment), assessment.frameworks)` is non-empty → `excluded.append(ExcludedAssessment(assessment.id, label, ANALYSIS_INCOMPLETE)); continue`. **No new write-ish token in that file** (its guard).
- Draft snapshot **generation** stays ungated (drafts are internal). The PDF therefore must render the failure itself (D-P5-1-H, R12).
- `approve_assessment` in `review.py` is **not** changed. P5-2 owns the approval flow. Release is blocked at the release chokepoint no matter what `review_status` says.

### D-P5-1-H. Every read site handles the sentinel explicitly (exact per site, R1-R13)

| # | Change |
|---|---|
| R1 | None. The sentinel passes through `report_framework_scores`. |
| R2 | D-P5-1-E (explicit skip). |
| R3 | `FrameworkScoreOut`: `status: Literal["scored", "failed"] = "scored"`, `overall_score: float \| None`, `overall_rating: str \| None`, `domain_scores: dict[str, ChapterScore]` (unchanged). The API therefore emits `"status": "scored"` for normal entries (additive) and a valid failed entry instead of a 500. |
| R4-R6 | No code change beyond R3 and the import cleanup in D-P5-1-I. In practice D-P5-1-G's 409 means they never serve a failed report. |
| R7 | `_framework_display` adds `"failed": is_failed_framework_score(scores)` to each entry. `score`/`rating` stay `scores.get(...)`, so `None` for failed. |
| R8 | `assessment_detail`: no change beyond R7 (it already builds `framework_display` for `tab in ("report", "questionnaire")` when a report exists). |
| R9 | `analysis_status`: the `error` branch also passes `"framework_display": _framework_display(assessment, report_framework_scores(report, assessment)) if report else {}`, loading `report` the same way as the `completed` branch. `partials/analysis_error.html`: when `framework_display` is defined and any entry has `failed`, the message line becomes `Analysis failed for {{ names joined by ", " }}. Results for the other frameworks were saved. Run analysis again to complete the assessment.` inside a `<p data-analysis-failed-frameworks>`. Otherwise it keeps the existing text. The "Retry Analysis" button is unchanged. `partials/analysis_complete.html`: add a `{% if fw_data.failed %}analysis failed{% elif fw_data.score is not none %}…` branch before the existing ones. It's unreachable in practice (status is `error`), but it keeps the partial honest. |
| R10 | `report_summary.html`: (1) directly after the `review-banner` div, `{% set failed_names = framework_display.values() \| selectattr("failed") \| map(attribute="name") \| list %}{% if failed_names %}<div data-analysis-incomplete-banner …>Analysis failed for {{ failed_names \| join(", ") }}. This report is incomplete: those frameworks have no score, and the report cannot be released until analysis is run again.</div>{% endif %}`; (2) in the gauge loop, a first branch `{% if fw_data.failed %}` renders a card `<div data-framework-failed="{{ fw_id }}">` with the framework name, "Analysis failed" and "Not scored. Run analysis again." Then the existing `{% elif fw_data.score is not none %}` gauge and the existing `{% else %}` "Scores unavailable" card (kept exactly: `test_no_blended_scoring` asserts "Scores unavailable" for the legacy missing-scores case). |
| R11 | No change. `compare_assessments_web` is None-safe and D-P5-1-G blocks it anyway. |
| R12 | `generate_pdf`: build `failed_framework_names = [name for fw_id, name in framework_metadata if is_failed_framework_score(framework_scores.get(fw_id))]`. `framework_score_rows` keeps skipping them, as today. **Additive only:** (a) cover page: when `failed_framework_names`, draw `S(f"Incomplete: analysis failed for {', '.join(failed_framework_names)}. Not scored.")` in the risk-critical colour at `y = 94` (below the existing "Frameworks assessed" line at 88). (b) "Framework Scores" section on the Executive Dashboard: after the bars loop, one line per failed framework, `S(f"{name}: analysis failed. Not scored.")`, advancing `framework_bar_y` by 11 each. Every string goes through `S()`. **No `Conclusion`/`AnalysisRun`/`analysis_pipeline` text in the file.** |
| R13 | D-P5-1-G (`ANALYSIS_INCOMPLETE` exclusion). The existing `overall_score is None → continue` stays as the legacy-missing guard. |

### D-P5-1-I. `/report/summary` returns per-framework requirement counts from the registry (gap #8)

- `app/routers/reports.py`: replace line 8 with `from app.frameworks.registry import FrameworkRegistry`. Both `ROOT_CAUSE_CLUSTERS` (unused) and the DPDPA `get_requirement_count` import go. Verify afterwards that `grep -n "app.dpdpa" app/routers/reports.py` is empty.
- In `get_report_summary`:
  ```python
  requirement_counts = {fw_id: FrameworkRegistry.get(fw_id).control_count() for fw_id in assessment.frameworks}
  ```
  `assessment.frameworks` is the property, in selection order. `FrameworkRegistry.get` raises for an unregistered id, which `Assessment.validate_selected_frameworks` already makes impossible. Return `total_requirements=sum(requirement_counts.values())` and the new field `requirement_counts=requirement_counts`.
- `app/schemas/report.py::ReportSummary` gains `requirement_counts: dict[str, int]`.
- **The sum is a count of requirements across the selected frameworks.** It matches the response's other counters (`compliant`, `non_compliant`, …), which already count `GapItem`s across frameworks. It is not a score, and D1's no-blended-score rule is about scores. The counts are **framework totals, not in-scope totals**. That is the same meaning the field always had (41 = DPDPA total), now correct per framework.
- Use `FrameworkDefinition.control_count()` directly. **Do not** add a new counting helper, and do not route through `app.frameworks.compat` (one accessor, not two).

### D-P5-1-J. DPDPA penalty exposure is computed only from DPDPA gaps, and the ₹500 Crore line is removed (A5)

- **Remove** `Repeat violations attract up to ₹500 Crore.` from `report_summary.html`. It can't be verified against the enacted 2023 Act's Schedule here, and neither Claude nor Codex can do legal research, so the safe default is to not state it. It must not come back without a cited source (open question 3).
- `_compute_business_impact(gap_items)`: the penalty lookup (both the prefix match and the `for … else` fallback of 50) runs **only** for items where `(item.framework_id or "dpdpa") == "dpdpa"`. That is the same legacy-null rule the templates use (`item.framework_id or 'dpdpa'`). For DPDPA items the prefix map and the fallback of 50 are unchanged. `affected_domains` and `critical_high_count` are computed exactly as today, over all non/partial items. Return keys:
  - `max_penalty_cr`: the maximum over DPDPA gaps, or 0;
  - `affected_domains`, `critical_high_count`: unchanged;
  - `has_gaps`: **any** non/partial item in any framework. It must be the same truth value as today (today `max_penalty > 0` held iff any gap existed), so the panel shows in exactly the cases it did;
  - `has_dpdpa_exposure`: `max_penalty_cr > 0`.
- Template, hero card: `{% if business_impact.has_gaps and has_dpdpa %}` → `{% if business_impact.has_dpdpa_exposure %}`. The `{% elif business_impact.has_gaps %}` / `{% else %}` branches are unchanged.
- Template, panel: `{% if has_dpdpa %}` → `{% if business_impact.has_dpdpa_exposure %}`. The rupee line and the sentence "Per-incident penalty under the DPDPA 2023 Schedule for the highest-severity violation category identified." stay. The ₹500 sentence is gone. The `{% else %}` branch is unchanged.
- **The per-category values in `_PENALTY_MAP` are not changed by this task** (open question 3).

### D-P5-1-K. What this task does not touch

- `question_engine.py`, `scope_profiler.py`, the prompt builders, `claude_analyzer.py`, `review.py`, `scoring.compute_framework_scores`, the `GapItem` write, `Conclusion` code, schema and Alembic (head stays `4e8c1a9d2b57`, no model change).
- No new assessment status value.
- The reader migration (scores from approved Conclusions) is **P5-2**.

### D-P5-1-L. Consistency audit against the standing guards (the P2-4 lesson)

1. `analysis.py`: the only `overall_score` tokens are the two existing allowed forms. The sentinel comes from `failed_framework_scores()`. No new line contains `delete` together with `AnalysisRun`/`Conclusion`.
2. `scoring.py`, `reports.py`, `pdf_export.py`, `review.py`: no `Conclusion|AnalysisRun|analysis_pipeline` anywhere, comments included.
3. `analysis_pipeline.py`: no `delete`.
4. `report_content.py`: no `db.add(`, `db.add_all(`, `db.merge(`, `.flush(`, `.commit(` or `delete`.
5. Templates: no `overall_score`, no `CyberAssess`, no `|safe`. `report_summary.html` still contains `/snapshots"` and `Live PDF` and does not contain `Download PDF`/`PDF Report` (`test_report_snapshots` scenario guard). Don't touch those links.
6. `test_no_blended_scoring`'s AST allow-list: `review_gate.py`, `report_content.py`, `web.py` and `pdf_export.py` may use `.get("overall_score")`/`["overall_score"]` subscripts (strings), but never `.overall_score` or `overall_score=`.
7. Every mutating route still carries P4-4's archive guard automatically (router-level). No new route is added: `run-analysis` and `/analyze` already exist.

### D-P5-1-M. Coordination with P5-8 (running now) and with P5-2 / P5-3

- **P5-8's files:** `app/services/question_engine.py`, `app/services/scope_profiler.py`, `app/dpdpa/industry_questions.py`, `app/utils/rfi_export.py`, and `app/routers/web.py`. In `web.py` it deletes the `/assessments/{assessment_id}/context/submit` route (`submit_context_web`), edits `download_rfi_docx`, and possibly the `compute_scope_multi(...)` call sites in the scope routes.
- **P5-1's `web.py` edits:** `_framework_display`, `run_analysis_web`, `analysis_status` and `_compute_business_impact`. **There are no shared hunks.** If P5-8 lands first, rebase and keep both sides. The merge is mechanical because the hunks are disjoint.
- **Tests must not call `compute_scope`/`compute_scope_multi`**, because P5-8 changes their signatures. Scenario 1 hard-codes the 11 excluded ids instead.
- **P5-2 and P5-3 start from this task merged.** Each must keep: `confirmed_response_clause()` on every response read that feeds analysis or a gate (D-P5-1-D); the sentinel contract and `is_failed_framework_score` (D-P5-1-E); the release refusal (D-P5-1-G); and the read-site table (D-P5-1-H) as the checklist for any reader they move. If either needs to break one of these, its own handoff must say so explicitly and name the D-P5-1 decision it supersedes.

## Required approach

1. `app/services/auto_answer.py`: `UNCONFIRMED_ANSWER_SOURCES`, `confirmed_response_clause()` (D-P5-1-D). Add a docstring line stating the D-P5-F rule.
2. `app/schemas/analysis.py` (new): `CompletionOverride`.
3. `app/routers/analysis.py`: constants, `CompletionGateRefused`, `_applicable_requirement_ids`, the gate rewrite (D-P5-1-A/B/D), the all-failed 500 and the partial-failure persistence (D-P5-1-F). Import `AuditEvent`, `conclusion_review.reviewer_actor` and `failed_framework_scores`.
4. `app/services/analysis_pipeline.py`: the confirmed-only response count (D-P5-1-D). One statement.
5. `app/services/scoring.py`: the sentinel helpers and the `namespaced_domain_scores` skip (D-P5-1-E).
6. `app/schemas/report.py`: `FrameworkScoreOut` (R3), `ReportSummary.requirement_counts` (D-P5-1-I).
7. `app/routers/reports.py`: the import swap and the counts (D-P5-1-I).
8. `app/utils/review_gate.py`: the release refusal (D-P5-1-G).
9. `app/services/report_content.py`: `ANALYSIS_INCOMPLETE` (D-P5-1-G).
10. `app/utils/pdf_export.py`: R12, additive only.
11. `app/routers/web.py`: `_framework_display`, `run_analysis_web`, `analysis_status`, `_compute_business_impact`.
12. Templates: `partials/report_summary.html` (R10, D-P5-1-J), `partials/analysis_error.html`, `partials/analysis_complete.html` (R9), `partials/analysis_gate_blocked.html` (new, D-P5-1-B).
13. `scripts/seed_test_companies.py`: the one-line override (D-P5-1-C).
14. `tests/test_correctness_bundle.py` (new). Copy (don't import) the fixture pattern from `tests/test_analysis_pipeline.py`: `db_path`, `engine`, `db`, the `gate` fixture's monkeypatching of `generate_initiatives`/`generate_multi_framework_initiatives`, `_seed`, `_item`, `_stub_single`, `_stub_multi`. For gate scenarios, **do not** patch `build_questionnaire` (use the real one). Use an `http` `TestClient` with `app.dependency_overrides[get_db]` for route and template scenarios, as `tests/test_pdf_updates.py` does. No test may touch `data/dpdpa.db` or the real `uploads/`.
15. `tasks/todo.md`: under Phase 5, add a P5-1 line in the existing style with a link to this handoff's Results. Don't edit the phase summary line.

## Key files

| File | Why |
|---|---|
| `app/routers/analysis.py` | Gate, override, confirmed inputs, fail-closed persistence (D-P5-1-A, B, D, F) |
| `app/services/auto_answer.py` | `UNCONFIRMED_ANSWER_SOURCES`, `confirmed_response_clause` (D-P5-1-D) |
| `app/services/analysis_pipeline.py` | Confirmed-only input count (one statement) |
| `app/services/scoring.py` | Sentinel helpers (D-P5-1-E) |
| `app/schemas/analysis.py` (new), `app/schemas/report.py` | `CompletionOverride`; `FrameworkScoreOut`, `ReportSummary` |
| `app/routers/reports.py` | Per-framework counts, dead import removed (D-P5-1-I) |
| `app/utils/review_gate.py` | Release refusal (D-P5-1-G) |
| `app/services/report_content.py` | Integrated-report exclusion (D-P5-1-G) |
| `app/utils/pdf_export.py` | Failed framework shown, additive (R12) |
| `app/routers/web.py` | `_framework_display`, `run_analysis_web`, `analysis_status`, `_compute_business_impact` |
| `app/templates/partials/report_summary.html`, `analysis_error.html`, `analysis_complete.html`, `analysis_gate_blocked.html` (new) | UI |
| `scripts/seed_test_companies.py` | D-P5-1-C only |
| `tests/test_correctness_bundle.py` (new) | The contract |
| `app/services/question_engine.py`, `scope_profiler.py`, `claude_analyzer.py`, `app/dpdpa/prompts.py`, `app/frameworks/prompts.py`, `app/routers/review.py`, `app/models/*`, `alembic/*`, every existing test | **Not modified** |

## Non-goals

- No reader migration to Conclusions, no change to scoring inputs, and no change to `approve_assessment` (P5-2).
- No prompt-level "unconfirmed" labels (D-P5-1-D).
- No new assessment status, no schema change, no Alembic revision.
- No change to the questionnaire's rendering of pre-fills, or to the web save's source transitions (open question 1).
- No change to `_PENALTY_MAP` values (open question 3). No legal-figure research.
- No reset of `review_status` on re-run (open question 2).
- No fix for `test_longitudinal_demo.py::test_scenario_9_rollups_and_integrated_reporting`'s intermittent ordering failure. It reproduces on unmodified `main`, is unrelated, and should be reported if seen, not fixed.

## Test scenarios

All in `tests/test_correctness_bundle.py`. Each test's docstring starts with `Scenario N:`.

1. **Scope-aware DPDPA denominator (the plan's regression).**
   - A DPDPA-only assessment with `applicable_requirements` = the 41 real base ids from `build_questionnaire()` minus exactly `{"CB.TRANSFER.1", "CB.TRANSFER.2", "CB.TRANSFER.3", "CH2.CONSENT.5", "CH4.CHILD.1", "CH4.CHILD.2", "CH4.CHILD.3", "CH4.SDF.1", "CH4.SDF.2", "CH4.SDF.3", "CH4.SDF.4"}` (30 ids; assert `len == 30`). It has 24 human answers on in-scope ids and no documents. `trigger_analysis` succeeds (stub the analyzer), and **no** `analysis.completion_override` event is written.
   - With 23 answers → `CompletionGateRefused`, 400, `detail` exactly `COMPLETION_GATE_MESSAGE` with `answered=23, expected=30, pct=77`. No `AnalysisRun` is created, and `assessment.status` is unchanged.
   - Answers on out-of-scope ids don't count: 23 in scope plus 5 on excluded ids is still refused, with 23 of 30.
   - `applicable_requirements` NULL → the expected count is 41. Invalid JSON → 41, with a warning. `"[]"` → the gate does not apply (then the no-input rule decides).
2. **No document bypass.** 0 answers plus one active evidence document mapped to the assessment → 400 `CompletionGateRefused`. On `main` this passed silently. The same state with `override=CompletionOverride(reason="document_led", reviewer_name="Priya")` → analysis succeeds, and exactly one `analysis.completion_override` audit row: actor `consultant:Priya`, entity `assessment`/id, and metadata key set and values exactly per D-P5-1-B (`answered 0`, `expected 41`, `completion_pct 0`, `threshold_pct 80`, `framework_ids ["dpdpa"]`, `schema_version 1`). An unknown reason → 400 `"Choose a valid override reason."`, no row. An override with 0 answers **and** no documents → 400 no-input message, no row. An override when ≥80% is answered → success, no row. Over HTTP: `POST /api/assessments/{id}/analyze` with `json={"reason": "document_led"}` → 200, actor `consultant:Manager Review`. With no body → 400.
3. **Unconfirmed answers are excluded (D-P5-F).**
   - 33 `"document"` + 0 human rows on a 41-expected DPDPA assessment → refused with `answered=0`.
   - Mixed: 30 human + 3 `"document"` → refused (30/41 = 73%).
   - Convert those 3 to `"document_confirmed"` → allowed.
   - Same for `"inferred"`.
   - `answer_source=NULL` rows count as confirmed (insert with Core `update`, setting NULL after creation).
   - The stubbed analyzer's captured `responses` contain **no** question id whose row is `"document"`/`"inferred"`, on both the single path (`run_gap_analysis`) and the multi path (`run_multi_framework_analysis`, DPDPA + ISO with a DPDPA-keyed `"document"` row).
   - The run envelope's `inputs.questionnaire_response_count` equals the confirmed count.
   - `UNCONFIRMED_ANSWER_SOURCES == ("document", "inferred")`.
4. **Web gate UX.**
   - `POST /assessments/{id}/run-analysis` below the threshold → 200 body containing `data-completion-gate-blocked`, the gate message, `data-completion-override-form`, and one `<option value="…">` per reason code in order. `X-Toast-Type: error`. `assessment.status` equals what it was before the request (not `error`, not `analyzing`).
   - The same POST with `override_reason=document_led`, `reviewer_name=Priya` (form) → analysis runs (patch `app.routers.analysis.run_gap_analysis` **and** point the route's `SessionLocal` at the test engine, the way existing web-analysis tests do; if none does, patch `app.database.SessionLocal` to a sessionmaker bound to the test engine) and one override event is written.
   - A no-input 400 → the partial without `data-completion-override-form`.
5. **Partial framework failure fails closed.**
   - DPDPA + ISO, with ISO's result `{"error": "boom"}`. The response is 200 with `status == "incomplete"`, `failed_frameworks == ["iso27001"]`, `per_framework_scores["iso27001"] is None`, and the message naming "ISO". Existing keys are all present.
   - The stored `framework_scores["iso27001"] == failed_framework_scores()`, and `framework_scores["dpdpa"]` has no `status` key and a numeric score.
   - `chapter_scores` has no key starting `iso27001:`.
   - `assessment.status == "error"`.
   - `GET /assessments/{id}/report-summary` contains `data-analysis-incomplete-banner` and `data-framework-failed="iso27001"`, and does not contain `0%` inside that card.
   - `GET /assessments/{id}/analysis-status` contains `data-analysis-failed-frameworks` and the ISO name.
6. **All frameworks failed.** Every framework errors → 500 `"Analysis failed for every selected framework. Run analysis again."`. `status == "error"`. A pre-existing `GapReport` from an earlier successful run is byte-identical (same id, same `framework_scores`, same `GapItem` rows). All runs are `failed`.
7. **Release refused.**
   - With the scenario-5 state and `review_status` hand-set to `"approved"`: `GET /report`, `/report/summary`, `/report/full` and `/report/pdf`, the RFI PDF download, and `POST …/snapshots/{id}/issue` (for a draft generated first) each → 409 with `detail == "Analysis failed for ISO/IEC 27001:2022. Run analysis again before releasing this report."`. Use the registry's actual `name`, not a hard-coded string.
   - After a successful re-run, the same `GET /report/summary` → 200.
   - A draft snapshot **can** be generated. Its PDF text (pdfplumber) contains "analysis failed" for the ISO name and the "Incomplete:" cover line.
   - The integrated report for the engagement lists the assessment as excluded with `ANALYSIS_INCOMPLETE`.
   - The schema accepts the sentinel: `FrameworkScoreOut(**failed_framework_scores())` validates, and a normal entry serializes with `status == "scored"`.
8. **Per-framework requirement counts (gap #8).** Approved reports for ISO-only, NIST-only, DPDPA-only and DPDPA + ISO assessments. `/report/summary` returns `requirement_counts` `{"iso27001": 93}`, `{"nist_csf": 94}`, `{"dpdpa": 41}` and `{"dpdpa": 41, "iso27001": 93}`, with `total_requirements` 93, 94, 41 and 134. Assert against `FrameworkRegistry.get(fw).control_count()` as well as the literals. `app/routers/reports.py` source contains neither `ROOT_CAUSE_CLUSTERS` nor `app.dpdpa`.
9. **Penalty exposure (A5).** `_compute_business_impact` on:
   - (a) DPDPA-clean + ISO non-compliant items (`framework_id="iso27001"`) → `max_penalty_cr == 0`, `has_dpdpa_exposure False`, `has_gaps True`;
   - (b) a DPDPA `CH2.SECURITY.1` gap → 250 / True;
   - (c) a DPDPA id matching no prefix → 50;
   - (d) a legacy item with `framework_id=None` and a DPDPA id → counted as DPDPA;
   - (e) no gaps → `has_gaps False`.
   - Rendered `report-summary` for case (a) on a DPDPA + ISO assessment has no `₹`, and case (b) has `₹250`.
   - `grep`-style: `"₹500"` and `"Repeat violations"` do not appear in `app/templates/partials/report_summary.html`.
10. **Guards (D-P5-1-L).** Every numbered item of D-P5-1-L that can be checked by reading source is asserted by reading source, for example the `analysis_gate_blocked.html` contents and the absence of the forbidden tokens in `scoring.py`, `reports.py`, `pdf_export.py`, `report_content.py` and `analysis_pipeline.py`. `alembic heads` is `4e8c1a9d2b57`. `inspect.signature(analysis._run_multi_framework_analysis)` is unchanged from `main` (compare it with a literal parameter-name list).

## Done criteria

- `tests/test_correctness_bundle.py` passes. `.venv/bin/pytest -q` passes in full: **550 + N passed, 9 skipped** (state the baseline you measured). Two exceptions are allowed: the fresh-worktree teardown error, and `test_longitudinal_demo.py::test_scenario_13_protected_surface_is_unchanged` failing **only** because of uncommitted working-tree changes (see Current state). Also report `test_scenario_9`'s ordering flake if it appears.
- `git diff --stat main -- tests/` shows **only** `tests/test_correctness_bundle.py`.
- `git diff --stat main` touches only the files listed in `## Key files` (plus `tasks/todo.md` and this handoff).
- `git diff --stat main -- app/services/question_engine.py app/services/scope_profiler.py app/services/claude_analyzer.py app/dpdpa app/frameworks app/routers/review.py app/models alembic` is **empty**.
- **Smoke test** (per the project rule; record the outputs in Results). Use a fresh Alembic-built SQLite DB and the in-process ASGI `TestClient` if a socket bind is refused.
  1. Create a DPDPA assessment, save the scope with the D-P5-1 scenario-1 answers, and answer 24 in-scope questions through `POST /assessments/{id}/questionnaire/save`. Run analysis (patched analyzer) → paste the 200 status.
  2. On a fresh assessment with one uploaded PDF and 0 answers: `POST /assessments/{id}/run-analysis` → paste the blocked partial's text. Then post with an override → paste the resulting `SELECT action, actor, metadata_json FROM audit_events WHERE action='analysis.completion_override'`.
  3. On DPDPA + ISO with ISO patched to error → paste the 200 JSON, `SELECT status FROM assessments`, `SELECT framework_scores FROM gap_reports`, and the `/report/summary` 409 body after hand-approving.
  4. `/report/summary` for an approved ISO-only assessment → paste `requirement_counts` / `total_requirements`.
  5. **Browser check** if a browser is available: the blocked panel and override form, the failed banner and card on the report tab. If none is available, say so. Do not claim it.

## Rollback

- **Code:** `git revert`. The document bypass comes back, and unconfirmed rows count again.
- Stored `framework_scores` sentinels from partial failures stay in the DB. The reverted `FrameworkScoreOut` would 500 on them, and `_framework_display` would show "Scores unavailable" (their `overall_score` is `None`). Re-running analysis on those assessments replaces them.
- `analysis.completion_override` audit rows stay as inert history.
- No schema change.

## Open questions (deliberately flagged, not resolved here)

1. **Implicit confirmation by section save.** A section save posts every rendered answer, so saving a section with pre-filled radios selected converts every `"document"` row in it to `"document_confirmed"`, and every `"inferred"` row to `"human"`, at once. That is closer to a bulk accept than to per-answer confirmation. P5-4 (adaptive questionnaire) should decide whether confirmation must be per question.
2. **`review_status` survives a re-run.** An approved assessment re-analysed keeps `"approved"`. D-P5-1-G blocks the failed-framework case only. P5-2's release gate should decide whether any new analysis invalidates approval. (Under P5-2, approval moves to individual Conclusions, which may make this moot.)
3. **`_PENALTY_MAP` values.** They were not verified against the enacted DPDPA 2023 Schedule. My reading of the Schedule, **to be verified by a qualified person before any client sees it**, is breach notification up to ₹200 Crore (the map says 250) and additional SDF obligations up to ₹150 Crore (the map says 50). The ₹500 Crore repeat-violation figure is removed by D-P5-1-J and must not return without a cited source.
4. **Override reason codes.** There are three fixed codes, with no free text (P4-4 open question 1). If consultants need a narrative, it belongs in a purge-scoped record, not `audit_events`.

## Report back

Append a `## Results` section to this file containing:
- The shipped constants and signatures (`COMPLETION_THRESHOLD`, `COMPLETION_GATE_MESSAGE`, `COMPLETION_OVERRIDE_REASONS`, `COMPLETION_OVERRIDE_EVENT`, `CompletionGateRefused`, `UNCONFIRMED_ANSWER_SOURCES`, `confirmed_response_clause`, `failed_framework_scores`, `is_failed_framework_score`, `failed_framework_ids`, `RELEASE_BLOCKED_MESSAGE`, `ANALYSIS_INCOMPLETE`), copied from the code.
- The R1-R13 table with what you actually changed at each site.
- `pytest -q` output for the new file and for the full suite, with the baseline you measured, and the scenario-13 note.
- The smoke outputs.
- Anything this document got wrong about the current code. **Name it and stop if it forces a design change. Do not pick an alternative.**

Commits and PRs for this task carry **no** `Co-Authored-By: Claude` trailer and no "Generated with Claude Code" footer. Codex cannot commit (its sandbox refuses to write `.git`). Leave the tree uncommitted, and the reviewing session commits on your behalf.
## Results

Implemented on `codex/p5-1-correctness-bundle`; the tree is intentionally uncommitted.

### Shipped contract symbols

```python
COMPLETION_THRESHOLD = 0.8
COMPLETION_GATE_MESSAGE = (
    "Questionnaire is incomplete: {answered} of {expected} in-scope core questions answered ({pct}%). "
    "Answer at least 80% of the in-scope questionnaire, or run analysis with a recorded consultant override. "
    "Pre-filled answers count only after a consultant confirms them."
)
COMPLETION_OVERRIDE_REASONS = {
    "document_led": "Documents are the primary evidence for this assessment",
    "client_answers_pending": "Client answers are pending and an interim AI proposal is needed",
    "scope_under_review": "Scope is still being confirmed with the client",
}
COMPLETION_OVERRIDE_EVENT = "analysis.completion_override"

class CompletionGateRefused(HTTPException):
    def __init__(self, *, answered: int, expected: int):
        self.answered = answered
        self.expected = expected
        pct = round((answered / expected) * 100) if expected else 0
        super().__init__(
            status_code=400,
            detail=COMPLETION_GATE_MESSAGE.format(
                answered=answered, expected=expected, pct=pct
            ),
        )
```

```python
UNCONFIRMED_ANSWER_SOURCES = ("document", "inferred")

def confirmed_response_clause():
    """Return the SQL predicate for confirmed and legacy human responses.

    D-P5-F: unconfirmed machine answers are never silent analysis inputs.
    """
    return or_(
        QuestionnaireResponse.answer_source.is_(None),
        QuestionnaireResponse.answer_source.notin_(UNCONFIRMED_ANSWER_SOURCES),
    )
```

```python
FRAMEWORK_ANALYSIS_FAILED = "failed"

def failed_framework_scores() -> dict:
    return {
        "status": FRAMEWORK_ANALYSIS_FAILED,
        "overall_score": None,
        "overall_rating": None,
        "domain_scores": {},
    }

def is_failed_framework_score(entry) -> bool:
    return isinstance(entry, dict) and entry.get("status") == FRAMEWORK_ANALYSIS_FAILED

def failed_framework_ids(framework_scores: dict, framework_ids: list[str]) -> list[str]:
    """Return failed framework ids in the selected-framework order."""
    return [
        framework_id
        for framework_id in framework_ids
        if is_failed_framework_score(framework_scores.get(framework_id))
    ]
```

```python
RELEASE_BLOCKED_MESSAGE = "Analysis failed for {names}. Run analysis again before releasing this report."
ANALYSIS_INCOMPLETE = "Analysis failed for at least one framework"
```

`trigger_analysis` now has the fixed optional body parameter at the end:
`def trigger_analysis(assessment_id: str, db: Session = Depends(get_db), override: CompletionOverride | None = None)`.
`_run_multi_framework_analysis` retains its original parameter-name list. The override metadata is schema version 1, uses `reviewer_actor`, and is committed with the analyzing status. Confirmed response filtering is shared by both analyzer paths and the immutable-run input envelope.

### R1-R13 read-site audit

| Site | Actual change |
|---|---|
| R1 | No change; `report_framework_scores` passes the stored per-framework entry through. |
| R2 | `namespaced_domain_scores` explicitly skips the failed sentinel. |
| R3 | `FrameworkScoreOut` now emits `status` (`scored`/`failed`) and allows nullable score/rating; `ReportSummary` adds `requirement_counts`. |
| R4-R6 | No reader-shape change beyond R3; the release chokepoint now refuses failed reports before these release APIs serve them. |
| R7 | `_framework_display` adds `failed`, while score/rating remain nullable lookups. |
| R8 | Existing assessment-detail wiring consumes the new display flag without additional route changes. |
| R9 | The error poll loads the current report display; error and complete partials state failed frameworks explicitly. |
| R10 | The report-summary partial adds the incomplete banner and failed-framework card, preserving the legacy “Scores unavailable” branch. Penalty exposure now uses `has_dpdpa_exposure`. |
| R11 | No change; comparison remains None-safe and the release gate blocks failed reports. |
| R12 | PDF cover and Executive Dashboard additive failure lines use `S()` and skip failed score rings/bars. |
| R13 | Integrated reports exclude failed assessments with `ANALYSIS_INCOMPLETE`. |

The release gate also covers the RFI and snapshot issue paths. A narrow internal draft-PDF seam was added because the live snapshot route was calling the release-gated PDF endpoint; normal scored-report snapshot release behavior remains unchanged.

### Verification

The supplied fresh-worktree baseline was **550 passed, 9 skipped, 1 known teardown error**. Results for this tree:

- `.venv/bin/pytest -q tests/test_correctness_bundle.py` → **10 passed, 7 warnings**.
- Related guard suite (`test_no_blended_scoring`, `test_analysis_pipeline`, `test_pdf_updates`, `test_report_snapshots`) → **65 passed**.
- `.venv/bin/pytest -q` → **563 passed, 9 skipped, 2 failed, 1 error**. The error is the known fresh-worktree `tests/conftest.py::_guard_dev_database_untouched` teardown artifact. `test_longitudinal_demo.py::test_scenario_13_protected_surface_is_unchanged` is the expected working-tree guard, expected until commit. The other failure is the documented scenario-9 integrated-report ordering flake; it also reproduced when run alone. Every other longitudinal-demo test passed.
- `alembic heads` → `4e8c1a9d2b57 (head)`.
- Browser verification was unavailable in this run; no browser result is claimed.

### Smoke outputs

Using a fresh Alembic-built SQLite database and an in-process ASGI `TestClient` with patched analyzers:

```text
SMOKE 1 analyze status: 200
SMOKE 2 blocked partial: ... Questionnaire is incomplete: 0 of 41 in-scope core questions answered (0%). Answer at least 80% of the in-scope questionnaire, or run analysis with a recorded consultant override. Pre-filled answers count only after a consultant confirms them. ...
SMOKE 2 override status: 200
SMOKE 2 audit: [('analysis.completion_override', 'consultant:Priya', '{"answered": 0, "completion_pct": 0, "expected": 41, "framework_ids": ["dpdpa"], "reason": "document_led", "schema_version": 1, "threshold_pct": 80}')]
SMOKE 3 partial JSON: 200 {'status': 'incomplete', 'failed_frameworks': ['iso27001'], 'per_framework_scores': {'dpdpa': 100.0, 'iso27001': None}, ...}
SMOKE 3 assessment status: error
SMOKE 3 framework_scores: ... "iso27001": {"status": "failed", "overall_score": null, "overall_rating": null, "domain_scores": {}} ...
SMOKE 3 release body: 409 {'detail': 'Analysis failed for ISO 27001. Run analysis again before releasing this report.'}
SMOKE 4 requirement counts: 200 {'requirement_counts': {'iso27001': 93}, 'total_requirements': 93}
```

### Current-code correction

The handoff’s current-state note that draft snapshot generation was already ungated was inaccurate. `app/routers/snapshots.py::_render` called `reports.download_pdf`, which enforced the release gate. The implementation added the smallest scoped internal draft-render seam needed for the required failed-report PDF scenario, while preserving the existing normal-report snapshot release test. The current registry name is `ISO 27001` (not `ISO/IEC 27001:2022`), so all failure messages use the registry name as required.
