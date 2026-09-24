# P4-3: Performance benchmarks: a deterministic 5/10/30/500/3000 SQLite dataset, four timed operations against a 2-second threshold, and a bounded miss protocol

**Plan:** `docs/plans/2026-09-21-002-revised-implementation-plan.md`, Phase 4, task P4-3 ("Seed a database with: 5 clients, 10 engagements, 30 assessments, 500 evidence versions, 3000 conclusion revisions"; "Measure (all must complete in < 2 seconds on SQLite): Portfolio dashboard load, Workpaper render for a 3-framework assessment, Report generation, Evidence search across an engagement"; "If any exceeds threshold: add indexes, denormalize hot paths, or document Postgres gate"; test: "Benchmark script runs, all queries under threshold, results logged."), and the Phase 4 exit criterion "Performance within thresholds on SQLite". Origin: **I6** in `tasks/2026-09-21-adversarial-review.md` ("SQLite with 36-byte string UUIDs, 6+ table joins for a workpaper view, and no query optimization … Define a 2-second threshold.").
**Owner:** Codex, standalone (per `tasks/agent-ownership.md`: "P4-3 Performance benchmarks | Codex, standalone"). This handoff pins down the seed and the measurement. It doesn't reopen any architecture. **If the code forces a deviation from this design, stop and report it in `## Results`. Do not pick an alternative.** Merge gate: the standard `[AR]` review (`tasks/todo.md` tags Phase 4 `[AR: IAM/external ID, retention/purge, performance]`).
**Depends on:** Phases 1–3 (merged, PRs #16–#33). `main` is at `a4ac3d9`.
**Runs in parallel with:** P4-1 (AWS adapter), P4-2 (longitudinal demo, which **extends `scripts/seed_test_companies.py`**, so this task must not touch that file), and P4-4 (retention/purge). By default the only file shared with them is `tasks/todo.md`. **Conditional overlap:** a new index needs an Alembic revision plus head-literal edits in four test files (D-P4-3-K), and P4-1/P4-4 may add revisions to the same files. D-P4-3-K gives the rebase rule.
**Blocks:** nothing.
**Failing contract suite: none pre-written.** I grepped `tests/` and `scripts/` for `benchmark`, `perf_counter`, `P4-3` and `performance`. The only hits are the one-off smoke timing inside `tests/test_workpaper.py::test_smoke_full_assessment_traceability` (lines ~1119–1121) and unrelated prose in `scripts/seed_test_companies.py`. No benchmark test or script exists. **Codex writes `tests/test_performance_benchmarks.py` itself** from `## Test scenarios`.

## Goal

1. One command seeds a fresh, isolated SQLite database with exactly the plan's volumes, in the shapes the product itself writes. It then times the four operations and logs the results as a table and a JSON file.
2. The same code runs as an opt-in pytest module that asserts each operation's median is under 2.0 s.
3. For any miss, the task either adds a targeted index or stops with a precise attribution. It does not become an open-ended optimisation project.

## Current state

Grounded against `a4ac3d9`. I ran the baseline myself: `.venv/bin/pytest -q` → **502 passed, 126 warnings, 1 error in 41.55s**. The error is the known fresh-worktree `_guard_dev_database_untouched` teardown artefact on `tests/test_workpaper.py::test_smoke_full_assessment_traceability`, documented in every Phase 2/3 handoff. `alembic/versions/` head is **`4e8c1a9d2b57`**. There is no `pytest.ini`, `setup.cfg` or `pyproject.toml`, so no custom markers are registered. `grep -rn "relationship(" app/models/` is empty, so every read is an explicit query.

### What earlier handoffs deferred to this task (quoted exactly; check these first)

- **P2-4** (`tasks/handoffs/2026-09-23-p2-4-consultant-approval.md`, the `conclusion_cards` query shape): *"one statement for the Conclusions, one for all their revisions (`conclusion_id IN (...)`, ordered by `created_at, rowid`), one `load_conclusion_state` per framework, one for the `AnalysisRun`s referenced by withheld revisions, and one for the assessment's `GapReport` + `GapItem`s. `resolve_citations` runs once per card, which is two small queries per card. That is accepted for a single-user local SQLite app, and there is no hard budget."*
- **P2-6** (`tasks/handoffs/2026-09-23-p2-6-workpaper-view.md`, D-P2-6-L): *"`build_workpaper` runs `conclusion_cards`' full per-assessment load … plus `resolve_citations` per revision/finding with non-empty citations (two small queries each; NULL and `"[]"` cost nothing). The revision list is queried twice (once inside `conclusion_cards`, once here) … **There is no hard query or latency budget in this task.** The adversarial review's performance item (a 2-second threshold for "workpaper render" on a seeded large dataset) is explicitly a final-phase (Phase 4) measurement. … If batching ever becomes necessary, it belongs in `app/services/citations.py` as a batched resolver, not as a second resolver in this module."* Its hand-forward reads: *"Phase 4 (performance): measure workpaper render against the adversarial review's 2-second threshold on the seeded dataset. This task's smoke timing is the baseline (D-P2-6-L)."*
- **P2-6 Results** (the baseline): *"Three workpaper GETs returned 200 with median render time `0.010783s`"* for **41 Conclusions, 3 runs, 126 revisions**, one framework. This task's workpaper case has about 5.6× the conclusions and about 8.6× the revisions.
- **P3-4** (`tasks/handoffs/2026-09-23-p3-4-remediation-tracking.md`, D-P3-4-L): the rollup is *"Four SELECTs."* P3-4 gave it **no** perf deferral and no budget. The engagement remediation rollup is **not** one of the plan's four measured operations, so this task doesn't time it (Non-goals). The P3-4 surface that *is* on a measured path is `findings.findings_page`, which P3-1 describes as *"four statements: `conclusion_review.conclusion_cards`, Findings, Actions, `finding_created` events"*. The report PDF reaches it through `report_content.assessment_findings`.

### The four operations: exact code paths (read, not assumed)

1. **Portfolio dashboard:** `app/routers/web.py::dashboard` (`GET /`). Four flat queries: all `Client` ordered by name; `Engagement` with `status != "closed"`; linked `Assessment` with `status != "archived"` and `engagement_id IS NOT NULL`; unmigrated `Assessment`. Then pure grouping in `app/services/portfolio.py` (`build_engagement_card`, `build_client_card`). It never reads conclusions, revisions or evidence. **Expected to be trivially fast.**
2. **Workpaper render:** `web.workpaper_page` (`GET /assessments/{assessment_id}/workpaper`) → `app/services/workpaper.py::build_workpaper` → template `pages/workpaper.html` + `components/workpaper_entry.html`. `build_workpaper` calls `conclusion_review.conclusion_cards(db, assessment.id)` (`app/services/conclusion_review.py`). That runs: Conclusions; `_revisions` (all revisions `IN (...)`); `analysis_pipeline.load_conclusion_state` **once per framework** (Conclusions again + human revisions again); withheld runs; legacy `GapItem`s; then **`resolve_citations` once per card** and **`_withheld_proposal` once per card**. `_withheld_proposal` runs `json.loads(run.claims_json)` on the *whole* run envelope for every card with a live withheld proposal. `build_workpaper` then adds Findings, **all revisions again**, all runs, responses, `_mapped_evidence` (2 queries) and `_desk_findings`. `_revision_entries` calls **`resolve_citations` once per revision**. `resolve_citations` (`app/services/citations.py`) issues **2 queries** (`EvidenceVersion IN`, `Evidence IN`) whenever the stored list is non-empty, and it loads full `EvidenceVersion` rows, `extracted_text` included.
3. **Report generation:** `app/routers/reports.py::download_pdf` (`GET /api/assessments/{assessment_id}/report/pdf`). It calls `require_review_approval` (`app/utils/review_gate.py`: 403 unless `assessment.review_status == "approved"`), then `GapReport`, `GapItem`s, `Initiative`s and `QuestionnaireResponse`s. Next, `app/services/report_content.py::assessment_findings` → `findings.findings_page` (`app/services/findings.py`) runs `conclusion_cards` again, `evidence.active_versions_in_scope`, Findings, Actions and the `AuditEvent` `finding_created` lookup, then one `EvidenceVersion` hash query. Finally it calls `app/utils/pdf_export.py::generate_pdf(...)`, which renders a gap card per `GapItem` plus the Approved Findings section.
4. **Evidence search across an engagement:** **no such feature exists in the product.** I grepped `app/` for `search`, `ilike` and `.like(`: the only hits are a client-side dashboard filter in `app/static/js/app.js`, a regex in `screening.py`, and `Evidence.uploaded_by.like("client_link:%")` in `magic_links.py`. There is no route, service or template that searches evidence. D-P4-3-G item 4 decides what gets measured.

### Index inventory on the grown tables (from `app/models/`)

- `conclusion_revisions`: `conclusion_id` (indexed), `analysis_run_id` (indexed). No index on `action` or `created_at`.
- `conclusions`: `assessment_id` (indexed); unique `uq_conclusions_assessment_framework_requirement` on `(assessment_id, framework_id, requirement_id)`.
- `evidence_versions`: `evidence_id` (indexed), `file_hash_sha256` (indexed), unique `(evidence_id, version_number)`.
- `evidence`: `engagement_id`, `assessment_id` (indexed). `evidence_uses`: `evidence_id`, `assessment_id` (indexed).
- **`audit_events`: no index at all** (not `entity_type`, `entity_id`, `action` or `created_at`). Readers on measured paths: `findings.findings_page` (`entity_type == "finding" AND action == "finding_created" AND entity_id IN (...)`), so every report PDF does a full scan of `audit_events`. Off the measured paths: `report_snapshots.py:309`, `:453` and `web.snapshots_page`.
- `analysis_runs`: `assessment_id` (indexed). `findings`: `assessment_id`, `conclusion_id` (indexed). `actions`: `finding_id` (indexed).

### Framework sizes (registered via `app.main._register_frameworks()`)

`dpdpa` 41 controls (first `CH2.CONSENT.1`), `iso27001` 93 (`ISO.A5.1`), `nist_csf` 94 (`NIST.GV.OC.01`). A 3-framework assessment over `ENABLED_ASSESSMENT_FRAMEWORKS = ("dpdpa", "iso27001", "nist_csf")` therefore has **228** requirements.

## Decisions (made here so they are not relitigated)

### D-P4-3-A. Deliverable shape: one importable script plus one opt-in pytest module

- **`scripts/benchmark_performance.py`** (new) holds all seeding and measurement logic and a CLI. It follows the `scripts/backup.py` convention: add `ROOT` to `sys.path` and stay importable as `scripts.benchmark_performance` (tests already import `scripts.backup` this way; `scripts/` has no `__init__.py`).
- **`tests/test_performance_benchmarks.py`** (new) imports the script's functions and asserts. It is **opt-in**: `pytestmark = pytest.mark.skipif(os.environ.get("CYBERASSESS_RUN_BENCHMARKS") != "1", reason="set CYBERASSESS_RUN_BENCHMARKS=1 to run the P4-3 benchmarks")`.
- **Why both:** the plan's test line says "Benchmark script runs … results logged", so a script is the deliverable, and its clean table and JSON are the logged results. The pytest module turns "all under threshold" into a pass/fail assertion.
- **Why opt-in:** the seed drives the real analysis pipeline four times over 228 items, among other work (D-P4-3-E). Running it on every `pytest -q` would add seconds to the 41.6 s suite for no correctness value, and wall-clock asserts on a shared CI box are the classic flake source. Skipped tests are green, so "Full test suite green" still holds. The Done criteria run the opt-in module explicitly.
- **No marker registration and no new config file.** An env-var `skipif` needs neither. Creating `pytest.ini`/`pyproject.toml` would change collection for the whole repo.

### D-P4-3-B. A new seeder, not `scripts/seed_test_companies.py`

`seed_test_companies.py` is the wrong base:
- it writes legacy `Assessment`/`GapReport`/`AssessmentDocument` rows directly;
- it binds to the dev DB via `SessionLocal`;
- it imports `app.main` at module top;
- it has no Client/Engagement/Evidence/Conclusion model;
- **P4-2 is editing it concurrently.**

The benchmark seeder lives entirely in `scripts/benchmark_performance.py` and shares no code with it.

### D-P4-3-C. The database: fresh, file-backed, Alembic-built, never the dev DB

- The DB is built by `alembic upgrade head` on a new file. Use the `_alembic_config(db_path)` pattern from `tests/test_workpaper.py`: `Config(REPO_ROOT/"alembic.ini")`, `script_location`, `sqlalchemy.url`.
- The engine has `check_same_thread=False` and a `connect` listener that sets `PRAGMA foreign_keys=ON`, same as the app and the tests.
- It is **file-backed, not `:memory:`**, because production is a file and the plan says "on SQLite".
- The script's `--db PATH` defaults to `<tempfile.mkdtemp(prefix="cyberassess-bench-")>/benchmark.sqlite3`. It **refuses to run if `PATH` already exists** (exit 2, message `refusing to reuse existing database: <path>`), so it can never touch `data/dpdpa.db` or a reused file.
- `settings.upload_dir` is pointed at a fresh temp dir for the whole run. Nothing should write there (D-P4-3-E writes no blobs); this is only a guard.
- The pytest module does the same inside `tmp_path_factory`. It uses `pytest.MonkeyPatch.context()` in a **module-scoped** fixture for `settings.database_url` and `settings.upload_dir`, because function-scoped `monkeypatch` can't serve a module fixture.

### D-P4-3-D. The dataset: exact counts and distribution

Names, statuses and text come from index arithmetic. Let `c` = client number 1–5, `e` = engagement number within the client (1–2), and `n` = assessment number within the engagement (1–3). Iterate in that nested order everywhere.

| Entity | Count | Distribution |
|---|---:|---|
| `clients` | **5** | `name=f"Benchmark Client {c}"` (unique), `industry="Technology"`, `size="medium"` |
| `engagements` | **10** | 2 per client. `name=f"Benchmark Client {c} engagement {e}"`, `status="active"`, `type="gap_assessment"` |
| `assessments` | **30** | 3 per engagement. **A0** = client 1 / engagement 1 / assessment 1. A0 has `selected_frameworks=["dpdpa","iso27001","nist_csf"]`, `description="Benchmark 3-framework assessment"`, `applicable_requirements=None`, and `review_status="approved"` once seeding finishes. The other **29 fillers** have `selected_frameworks=["dpdpa"]`, `applicable_requirements=None` and `status` cycling `("completed", "questionnaire_done", "documents_uploaded")` by filler index. `company_name`/`industry`/`company_size` come from the client. |
| `assessment_packs` | 30 + 2 | One per (assessment, framework). `pack_version = FrameworkRegistry.get(fw).version`, as `engagement_factory` writes it. |
| `evidence` | 250 | **E0** (client 1 / engagement 1) has **70**: 40 with `assessment_id=A0` (A0 docs `k=0..39`), 15 with E0's assessment 2 and 15 with E0's assessment 3. **Each of the other 9 engagements has 20**, with `assessment_id` round-robin over its 3 assessments (`k % 3`). |
| `evidence_versions` | **500** | 2 per Evidence: v1 `status="superseded"` and v2 `status="active"`. `Evidence.status="active"`. |
| `conclusions` | 808 | A0 **228** (all 3 frameworks, created by the pipeline). Each filler has **20** (the first 20 `dpdpa` controls in registry order), 580 in total. |
| `conclusion_revisions` | **3000** | A0 about **1083** from real code paths (D-P4-3-E). The fillers get `3000 − actual_A0_count`: 3 each, plus a 4th for the first `remainder` filler conclusions in iteration order. |
| `analysis_runs` | 41 | A0 12 (4 triggers × 3 frameworks). One per filler. |
| `findings` / `actions` | 95 / 95 | A0 only (D-P4-3-E step 5). One Action per Finding. |
| `evidence_uses` | 114 | A0 only (D-P4-3-E step 2). |
| `questionnaire_responses` | 808 | A0 228 (one per requirement, `question_id=requirement_id`). 20 per filler. |
| `audit_events` | ~1,800 | 6 per Evidence (1,500, D-P4-3-E step 1), plus 114 `evidence_use.created`, plus 95 `finding_created`, plus whatever the pipeline writes. The exact count is recorded, not asserted. |
| `gap_reports` / `gap_items` | 1 / 228 | A0 only, written by the pipeline. |

**The skew is deliberate.** Two of the four operations (workpaper and report) run on a single assessment, so A0 holds a third of all revisions and the fillers supply table volume. E0 holds 140 of the 500 versions, so "across an engagement" searches a realistically large engagement rather than 50 versions.

### D-P4-3-E. How each part is seeded: real services for A0, direct ORM inserts for filler

A0 is what the workpaper and report read, so its rows must have exactly the shapes the product writes. That means real `claims_json` envelopes, real text-span citations, a real `GapReport` with scores and `legacy_history`, and real Finding/Action history and audit events. Hand-building those would benchmark a shape the product never produces. Filler rows only have to exist, so they are bulk-inserted directly.

**Evidence text (all 500 versions): `evidence_text(global_index, version_number, markers)`.**
- Line 1 is `f"Benchmark policy document {global_index:03d}, version {version_number}."`.
- Then `BODY_PARAGRAPH` 20 times, each prefixed `f"Section {s}. "` (`s = 1..20`). `BODY_PARAGRAPH` is one fixed ASCII paragraph of 380–420 characters of neutral policy prose written by Codex, and it **must contain the phrase `"retention schedule"`**. That gives about 8 KB per version.
- Last come the `markers`: for A0 doc `k`, one sentence `f"Requirement marker {control_id} is implemented under this policy."` for every A0 requirement `g` with `g % 40 == k` (`g` is defined in step 3). Other docs get no markers. Both versions of a doc carry the same markers.
- `original_filename=f"benchmark-e{engagement_index:02d}-doc{k:03d}-v{version_number}.pdf"`. The `Evidence` frozen fields copy v1.
- `storage_path=f"benchmark/{evidence_id}/v{version_number}.pdf"`. **No file is written**: none of the four operations reads a blob (`verify_version` isn't on any measured path).
- `file_hash_sha256 = sha256(f"{global_index}:{version_number}".encode()).hexdigest()`, `file_size_bytes = len(text)`, `mime_type="application/pdf"`, `uploaded_by="consultant:Bench Reviewer"`.

**Step 1: clients, engagements, assessments, packs, evidence and filler, as direct ORM inserts.**
- Timestamps are `BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)` plus a monotonically increasing `timedelta(seconds=i)` counter. Set `created_at` and `updated_at` explicitly.
- For each Evidence, write the **6 audit events the real ingest path writes**, via `AuditEvent(...)` directly (the action/entity strings are copied from `app/services/evidence.py`):
  - `evidence.created` (entity_type `"evidence"`);
  - per version, `evidence_version.created` and `evidence_version.status_changed` quarantined→active (entity_type `"evidence_version"`);
  - for v1, `evidence_version.status_changed` active→superseded.
  - `metadata_json = json.dumps({"evidence_id": ...}, sort_keys=True)`.
- **Filler assessments**, each:
  - 20 `QuestionnaireResponse` (`answer` cycling the five values allowed by `ck_questionnaire_responses_answer_valid`).
  - One `AnalysisRun(framework_id="dpdpa", status="completed", model_id="benchmark", started_at, completed_at)`. Its `claims_json` is the minimal valid envelope `{"schema_version": 1, "trigger_id": "benchmark-filler", "framework_id": "dpdpa", "model_tiers": {}, "inputs": {"evidence_versions": [], "legacy_document_ids": [], "questionnaire_response_count": 20, "applicable_requirements": null}, "gap_report_id": null, "desk_review_used": false, "claims": [], "error": null}`.
  - 20 `Conclusion`s: `outcome="partially_compliant"`, `rationale="Benchmark filler rationale"`, `evidence_summary=""`, `gaps_identified="Benchmark gap"`, `risk_level="medium"`, `recommended_action="Benchmark action"`, `ai_proposed=True`, `version=2`, `cluster_id=None`.
  - **Revisions are inserted after A0 is seeded** (the count depends on A0). Actions follow `["proposed", "approved", "proposal_withheld", "proposal_withheld"][:n]` with `n` = 3 or 4. AI actions set `actor="system:analysis"`, `analysis_run_id` = that assessment's run and `citations_json="[]"`. `approved` sets `actor="consultant:Bench Reviewer"`, `analysis_run_id=None` and `citations_json=None`. The first revision has `previous_outcome`/`previous_rationale` of `None`; later ones use the Conclusion's values. `created_at` comes from the counter.
- Commit.

**Step 2: A0 inputs.** Add 228 `QuestionnaireResponse`s (`question_id` = requirement id, `answer` cycling the five valid values, `notes=f"Benchmark response {g}"`). Map evidence through the **real** `app.services.evidence.map_evidence(db, evidence_id=A0 doc (g // 2) % 40, assessment_id=A0, framework_id, requirement_id, relevance="primary", actor="consultant:Bench Reviewer")` for every `g % 2 == 0`, which gives 114 uses plus their audit events. Commit.

**Step 3: A0 analysis run 1, through the real router function.** Call `app.routers.analysis.trigger_analysis(a0.id, db)` directly (a plain function call with an explicit `db`, as `tests/test_pdf_updates.py::_run_one` does via `gate.trigger_analysis`). Patch exactly what `tests/test_pdf_updates.py`'s `gate` fixture and `_stub_multi` patch, using `unittest.mock.patch.object` in the script:
- `app.routers.analysis.run_multi_framework_analysis` → `{"frameworks": {fw: {"parsed": {"executive_summary": f"{fw} benchmark summary", "assessments": deepcopy(items[fw])}, "raw": "{}"}}, "synthesis": None, "total_usage": {}}`
- `app.routers.analysis.generate_multi_framework_initiatives` → `[]`
- `app.routers.analysis.generate_initiatives` → `[]`
- `app.routers.analysis.build_questionnaire` → `[{"id": "Q1"}]`
- `app.frameworks.questionnaire_builder.build_multi_questionnaire` → `[]`

No LLM or network call can happen. If any code path tries one, that is a deviation: stop.

`items[fw]` has one dict per control, in registry order. Let **`g`** be the A0-global index over dpdpa, then iso27001, then nist_csf (0–227). Keys are exactly those of `tests/test_pdf_updates.py::_item`:
- `requirement_id`
- `compliance_status = ("non_compliant", "partially_compliant", "compliant")[g % 3]`
- `current_state=f"Benchmark current state for {id}."`
- `gap_description=f"Benchmark gap for {id}."`
- `risk_level = ("critical", "high", "medium", "low")[g % 4]`
- `remediation_action=f"Benchmark remediation for {id}."`
- `remediation_priority=(g % 4) + 1`
- `remediation_effort="medium"`
- `timeline_weeks=6`
- `maturity_level=2`
- `root_cause_category="process"`
- `needs_review=False`
- `evidence_quote = f"Requirement marker {id} is implemented under this policy." if g % 2 == 0 else ""`

The quote text is present verbatim in A0 doc `g % 40` (step 1), so the pipeline's `cite_quotes` produces real `text_span` citations for half the requirements and `"[]"` for the other half.

**Step 4: human decisions, through the real service.** For each A0 Conclusion in `g` order, call `app.services.conclusion_review.decide(db, assessment_id=A0, conclusion_id=..., action=..., expected_version=conclusion.version, actor=conclusion_review.reviewer_actor("Bench Reviewer"), edits=...)`:
- `g % 4 == 0` → `"approved"`;
- `g % 4 == 1` → `"edited"` with `edits={"outcome": "non_compliant", "rationale": f"Consultant rationale for {id}.", "gaps_identified": "Consultant-identified gap", "risk_level": "high", "recommended_action": "Consultant action"}`;
- `g % 4 == 2` → `"rejected"`;
- `g % 4 == 3` → no decision.

`decide` never commits, so commit once after the loop. That gives 171 human revisions.

**Step 5: Findings, through the real service.** For every A0 Conclusion whose card state is `approved`/`edited` and whose `outcome` is in `conclusion_review.GAP_OUTCOMES`, call `app.services.findings.create_finding(db, assessment_id=A0, conclusion_id, conclusion_version=conclusion.version, title=f"Finding for {id}", description=f"Benchmark finding description for {id}.", severity=conclusion.risk_level, priority=findings.PRIORITY_BY_SEVERITY[conclusion.risk_level], action_title=f"Remediate {id}", action_owner=("Owner A", "Owner B", None)[g % 3], action_target_date=date(2026, 12, 31), notes=None, actor=reviewer_actor("Bench Reviewer"), now=BASE)`. Expected: **95** (38 approved gap Conclusions plus 57 edited). Commit.

**Step 6: A0 runs 2, 3 and 4.** Call `trigger_analysis(a0.id, db)` three more times with the same patches and items. Locked Conclusions (`g % 4 ∈ {0, 1}`) get `proposal_withheld`; the rest get `proposed`. The expected A0 total is **228 × 4 + 171 = 1083** revisions, with 12 runs, 1 `GapReport` (its `legacy_history` holds 3 snapshots) and 228 `GapItem`s.

**Step 7: filler revisions** (step 1's deferred insert), totalling `3000 − actual_A0_count`. Commit. Then set `A0.review_status = "approved"` and commit.

**Step 8: `seed_counts(db) -> dict`** returns row counts for every table in the table above. `seed_benchmark_dataset` then **asserts exactly** `clients == 5`, `engagements == 10`, `assessments == 30`, `evidence_versions == 500` and `conclusion_revisions == 3000`. If `actual_A0_count != 1083` or `findings != 95`, keep the total at 3000 (the filler absorbs the difference) and record the actual value and the reason in Results. That is not a stop.

### D-P4-3-F. Determinism: what "reproducible" means here

- There is **no randomness** anywhere; every value is index arithmetic. Do not import `random`.
- Primary keys are `uuid4` from the model defaults. Pipeline-written timestamps (`AnalysisRun.started_at`, revision `created_at` inside `trigger_analysis`/`decide`) come from the real clock, and D-P4-3-E doesn't override them.
- Two runs therefore produce **identical row counts, identical per-row shapes, identical text and the same citation set**, but different ids and pipeline timestamps. None of the four operations' cost depends on id values or clock values.
- The seeder is idempotent only in the sense that it refuses a pre-existing DB (D-P4-3-C). It never updates or deletes an existing DB.

### D-P4-3-G. The four operations: exactly what is timed

Each operation is one in-process HTTP request through the real ASGI app, except item 4.

| # | `name` | Target | Expected status |
|---|---|---|---|
| 1 | `portfolio_dashboard` | `GET /` | 200 |
| 2 | `workpaper_3_framework` | `GET /assessments/{A0}/workpaper` | 200 |
| 3 | `gap_report_pdf_3_framework` | `GET /api/assessments/{A0}/report/pdf` | 200, `application/pdf`, body starts with `%PDF` |
| 4 | `evidence_search_engagement` | `search_engagement_evidence(db, E0.id, "retention schedule")` | returns 70 rows |

- **Item 3 is the assessment gap-report PDF.** It is "report generation" for the plan's 3-framework case. It is also read-only, so it can be repeated. The engagement integrated report (`POST /engagements/{id}/integrated-reports`) **writes** a snapshot file and audit events on every call, which would grow the DB across timed runs. It is not timed here (Open question 2).
- **Item 4 is a benchmark-local reference query**, because the product has no evidence search (Current state). It is defined in `scripts/benchmark_performance.py` only. It is **not** added to `app/` and gets no route or template:

  ```python
  def search_engagement_evidence(db, engagement_id: str, term: str) -> list[tuple[Evidence, EvidenceVersion]]:
      """P4-3 reference query: the minimum work any engagement-wide evidence search must do.
      Not product code -- no search feature exists yet."""
      pattern = f"%{term}%"
      return db.execute(
          select(Evidence, EvidenceVersion)
          .join(EvidenceVersion, EvidenceVersion.evidence_id == Evidence.id)
          .where(
              Evidence.engagement_id == engagement_id,
              Evidence.status != "archived",
              EvidenceVersion.status == "active",
              or_(EvidenceVersion.original_filename.ilike(pattern),
                  EvidenceVersion.extracted_text.ilike(pattern)),
          )
          .order_by(Evidence.created_at, Evidence.id)
      ).all()
  ```

  It is timed as a direct call on a fresh Session (no HTTP), including materialising the rows. It measures whether a `LIKE '%…%'` scan over an engagement's extracted text is viable on SQLite. That scan is the inherent cost of any future search, and it is the only one of the four where the "Postgres gate" alternative (full-text search) is a meaningful answer.

### D-P4-3-H. Measurement mechanics

- **Client:** `fastapi.testclient.TestClient(app.main.app, raise_server_exceptions=False)`, set up exactly like `tests/test_workpaper.py::http`:
  - `configure_templates(web.templates)`;
  - `settings.database_url` patched to the benchmark URL, so the lifespan's `_run_alembic_upgrade` is a no-op on an at-head DB;
  - `app.dependency_overrides[get_db]` set, then cleared in `finally`.
- **Session per request.** The override yields a **new** Session from a `sessionmaker(bind=bench_engine)` per request and closes it afterwards, which mirrors `app.database.get_db`. Do **not** reuse one Session across timed runs: its identity map would make runs 2–5 look faster than production. Item 4 likewise opens a fresh Session per run.
- **Timing:** `time.perf_counter()` around the full `client.get(...)`, which includes routing, the service, template/PDF rendering and reading `response.content`. Do **one untimed warm-up** per operation (Jinja template compilation, fpdf font load and the SQLite page cache are one-time process costs, not per-request costs), then **5 timed runs**. Record all five, the median and the max.
- **Pass rule:** `median < THRESHOLD_SECONDS = 2.0`. The max is recorded, not asserted, to avoid one-off scheduler noise. Record it in Results so a reviewer can see the spread.
- **SQL statement count:** attach `event.listen(bench_engine, "before_cursor_execute", counter)` for the warm-up run only, and record `statements` per operation. This is the N+1 signal for D-P4-3-J.
- **Attribution breakdown** (untimed against the threshold; one extra run each after the 5 timed runs, on a fresh Session):
  - workpaper: `build_workpaper_seconds` (a direct `workpaper.build_workpaper(db, a0)`);
  - report: `assessment_findings_seconds` (a direct `report_content.assessment_findings(db, a0)`) and `generate_pdf_seconds` (a direct `pdf_export.generate_pdf(...)` with the same arguments `download_pdf` builds). Keep the argument construction in the script and copy it from `reports.py::download_pdf`; don't import a private helper.
- **Environment:** record `sys.version`, `sqlite3.sqlite_version`, `platform.platform()` and `seed_seconds` (wall time of `seed_benchmark_dataset`).

### D-P4-3-I. Results logging: the exact output

`run_benchmarks(db_url, engine) -> dict` returns the JSON structure below. The CLI prints a fixed-width table (`name | median_s | max_s | statements | status | PASS/FAIL`) and writes the dict to `--json PATH` (default `<db dir>/benchmark-results.json`).

```json
{"threshold_seconds": 2.0, "environment": {"python": "...", "sqlite": "...", "platform": "..."},
 "seed_seconds": 0.0, "counts": {"clients": 5, "...": 0},
 "operations": [{"name": "portfolio_dashboard", "target": "GET /", "status_code": 200,
   "bytes": 0, "runs_seconds": [0.0, 0.0, 0.0, 0.0, 0.0], "median_seconds": 0.0,
   "max_seconds": 0.0, "statements": 0, "breakdown": {}, "passed": true}]}
```

- Exit code: `0` if every operation passed, `1` if any failed, `2` on refusal (D-P4-3-C).
- The pytest module writes the same JSON to its tmp dir and `print`s the table, which is visible with `-s`.

CLI: `.venv/bin/python scripts/benchmark_performance.py [--db PATH] [--json PATH]`.

### D-P4-3-J. What to do on a threshold miss: a bounded ladder, then stop

Work through this **only** for an operation whose median is ≥ 2.0 s, in this order.

1. **Attribute first.** Use the `statements` count and the D-P4-3-H breakdown. Re-run the offending statements under `EXPLAIN QUERY PLAN` (in the script, not in a test) and record any `SCAN <table>` on a grown table.
2. **A targeted index is the only fix this task may apply,** and only when step 1 shows a specific statement doing a `SCAN` on a large table that an index turns into a `SEARCH`. Pre-identified candidates:
   - **`audit_events (entity_type, entity_id)`**, named `ix_audit_events_entity_type_entity_id`. `findings.findings_page` (on the report path) full-scans `audit_events` today because the table has no index. At about 1,800 rows this is unlikely to matter, so **add it only if measurement shows it matters**.
   - No other missing index is evident from the code. Every FK on the measured paths is already indexed (Current state). Don't add speculative indexes.
3. **If the cost is statement count or Python time, stop: no index fixes it.** Signs: hundreds of `resolve_citations` pairs, the per-card `_withheld_proposal` `json.loads` of the full run envelope, the duplicate revision loads flagged in D-P2-6-L, Jinja rendering of about 1,083 revision entries, or fpdf2 rendering of 228 gap cards. **Do not refactor** `conclusion_review.py`, `workpaper.py`, `citations.py`, `findings.py`, `report_content.py` or `pdf_export.py`, and do not denormalise. Record the attribution in Results as a **threshold miss requiring a follow-up**: name the function, the statement count and the time split. Leave the failing assertion in place. D-P2-6-L already names the eventual fix location ("a batched resolver" in `app/services/citations.py`), but scoping it is Claude's call, not this task's.
4. **Postgres gate, documentation only.** Use it only when the time is inside a single SQL statement that SQLite cannot make fast with an index. The only plausible case is item 4's `LIKE '%…%'` scan over `extracted_text`. Write a "Postgres gate" paragraph in Results: the measured time, the row and byte volume scanned, and that the options are SQLite FTS5 or Postgres `pg_trgm`/`tsvector`. Build neither.
5. PDF render time is CPU-bound in fpdf2 and is **not** a database or Postgres question. If `generate_pdf_seconds` alone is ≥ 2.0 s, report it under step 3.

### D-P4-3-K. If (and only if) an index is added: the migration protocol and its file overlap

- **New Alembic revision** `alembic/versions/<rev>_p4_3_performance_indexes.py` with `down_revision` = the current head (`4e8c1a9d2b57` unless another Phase 4 revision has merged). Use `op.create_index(...)` in `upgrade()` and `op.drop_index(...)` in `downgrade()`. An index-only revision needs no data guard.
- **Declare the same index on the ORM model** (`index=True` on the column, or `Index(...)` in `__table_args__`) with the **same name**. `tests/test_data_integrity.py::TestAlembicContractParity` diffs Alembic-built against `create_all()`-built indexes and fails on any mismatch. `TestAlembicRoundTrip` diffs the full schema across `downgrade -1` → `upgrade head`.
- **Head literal edits (only these, only the literal):** `tests/test_alembic_baseline_immutable.py` (the two probe templates' `down_revision = "4e8c1a9d2b57"`, lines ~30 and ~91), `tests/test_startup_invariants.py` (two `assert version == "4e8c1a9d2b57"`, ~171 and ~209), `tests/test_data_integrity.py` (three head asserts, ~1040, ~1103, ~1434), and `tests/test_analysis_pipeline.py::test_p2_3_revision_is_head_and_adds_link_and_uniqueness` (`script.get_current_head() == P2_3_REVISION`; change only the head comparison to the new revision, and keep the `down_revision` check). `tests/test_citations.py:762/779` check `4e8c1a9d2b57`'s *down*-revision and stay unchanged. Re-grep `4e8c1a9d2b57` before editing; if other head assertions exist, list them in Results.
- **Coordination with P4-1/P4-4:** both may add revisions off the same head. Whichever merges **second** re-points its `down_revision` to the new head and updates the same head literals to its own revision id. P4-3's revision contains only indexes, so the rebase is mechanical.
- **No index is added** → none of the files above change, `alembic heads` stays `4e8c1a9d2b57`, and P4-3 has no overlap beyond `tasks/todo.md`.

### D-P4-3-L. Files this task must not change

Unless D-P4-3-K applies, `git diff --stat main` touches only the two new files, `tasks/todo.md` and this handoff. **Never changed, in any branch of this task:** `app/services/*.py`, `app/routers/*.py`, `app/utils/pdf_export.py`, `app/templates/**`, `scripts/seed_test_companies.py` (P4-2), and `app/database.py`/`app/config.py`/`app/main.py`.

## Required approach

1. `scripts/benchmark_performance.py`:
   - constants `THRESHOLD_SECONDS = 2.0`, `TIMED_RUNS = 5`, `SEARCH_TERM = "retention schedule"`, `BASE`, `BODY_PARAGRAPH`, and the plan counts as `PLAN_COUNTS = {"clients": 5, "engagements": 10, "assessments": 30, "evidence_versions": 500, "conclusion_revisions": 3000}`;
   - functions `build_database(db_path) -> (url, engine)` (D-P4-3-C), `evidence_text(...)`, `seed_benchmark_dataset(engine) -> SeedHandle` (a frozen dataclass with `a0_id`, `e0_id`, `seed_seconds` and `counts`; D-P4-3-D/E, including the step 8 assertions), `seed_counts(db)`, `search_engagement_evidence(...)` (D-P4-3-G), `benchmark_client(url, engine)` (a context manager, D-P4-3-H), `run_benchmarks(url, engine, handle) -> dict` (D-P4-3-G/H/I), `format_table(results) -> str`, and `main(argv=None) -> int` (CLI, D-P4-3-I);
   - `_register_frameworks()` from `app.main` is called before seeding.
2. `tests/test_performance_benchmarks.py`, per `## Test scenarios`.
3. Run the CLI once, then the opt-in module, then the normal suite (Done criteria).
4. Apply D-P4-3-J only if something missed.
5. `tasks/todo.md`: under the Phase 4 line, add a P4-3 sub-bullet in the existing style: `- [x] **P4-3 Performance benchmarks** — scripts/benchmark_performance.py + opt-in tests/test_performance_benchmarks.py (CYBERASSESS_RUN_BENCHMARKS=1); medians: dashboard Xs, workpaper Xs, report Xs, search Xs (threshold 2.0s)`. If any operation missed, mark it `[ ]` and write "threshold miss, see handoff Results" instead of the medians.

## Key files

| Path | Why |
|---|---|
| `scripts/benchmark_performance.py` | **New.** Seeder, reference search query, measurement, CLI. |
| `tests/test_performance_benchmarks.py` | **New.** Opt-in assertions. |
| `app/routers/web.py` (`dashboard`, `workpaper_page`) | Operations 1–2 (read only). |
| `app/services/workpaper.py`, `app/services/conclusion_review.py`, `app/services/citations.py` | Workpaper query pattern (read only; P2-4/P2-6 deferrals quoted above). |
| `app/routers/reports.py::download_pdf`, `app/services/report_content.py`, `app/services/findings.py::findings_page`, `app/utils/pdf_export.py::generate_pdf` | Operation 3 (read only). |
| `app/routers/analysis.py::trigger_analysis`, `app/services/analysis_pipeline.py` | A0 seeding path. |
| `app/services/evidence.py::map_evidence`, `app/services/findings.py::create_finding` | A0 seeding path. |
| `tests/test_workpaper.py` (`_alembic_config`, `engine`, `http`), `tests/test_pdf_updates.py` (`gate`, `_stub_multi`, `_item`, `_run_one`) | Fixture and stub patterns to copy. |
| `scripts/backup.py`, `tests/test_backup_restore.py` | Importable-script convention. |
| `tests/test_data_integrity.py::TestAlembicContractParity` | Only relevant under D-P4-3-K. |

## Non-goals

- Timing the engagement remediation rollup (`remediation_rollup.engagement_rollup`), the integrated report, the Findings page or the conclusions page. None of them is one of the plan's four.
- Building a product evidence-search feature, FTS5, or any Postgres support.
- Refactoring or batching any service (D-P4-3-J step 3), denormalising any table, or caching.
- Load or concurrency testing. The app is single-user; one request at a time is the realistic case.
- Registering pytest markers or adding any pytest/CI configuration.
- Touching `scripts/seed_test_companies.py` or the dev DB.

## Test scenarios

`tests/test_performance_benchmarks.py`, with the module-level opt-in `skipif` (D-P4-3-A). One **module-scoped** fixture `bench` builds the DB in `tmp_path_factory`, patches settings with `pytest.MonkeyPatch.context()`, runs `seed_benchmark_dataset` once, runs `run_benchmarks` once, writes the JSON, prints `format_table`, and yields `(handle, results)`. It also calls `app.main._register_frameworks()` first, the way `test_workpaper.py`'s autouse fixture does.

1. **Seed counts are exactly the plan's**: `handle.counts[k] == v` for every `PLAN_COUNTS` item. Also check that A0 has 228 Conclusions across exactly `{"dpdpa", "iso27001", "nist_csf"}`, 12 `AnalysisRun`s, exactly one `GapReport` and `review_status == "approved"`.
2. **A0's data has product shapes**: at least one A0 `proposed` revision whose `citations_json` parses to a non-empty list of `text_span` citations resolving (via `citations.resolve_citations`) to an active E0 version, and at least one A0 `proposal_withheld` revision. `findings` count equals the number of A0 approved/edited gap Conclusions. `evidence_versions` has exactly 250 `active` and 250 `superseded`.
3. **Dashboard** (`portfolio_dashboard`): status 200, `passed`, and the body contains all five `Benchmark Client {c}` names.
4. **Workpaper** (`workpaper_3_framework`): status 200, `passed`, and the body contains `anchor_for` ids from each of the three frameworks (e.g. `wp-dpdpa-CH2.CONSENT.1`, `wp-iso27001-ISO.A5.1`, `wp-nist_csf-NIST.GV.OC.01`).
5. **Report** (`gap_report_pdf_3_framework`): status 200, the content type starts with `application/pdf`, the body starts with `b"%PDF"`, and `passed`.
6. **Evidence search** (`evidence_search_engagement`): returns exactly 70 rows, all with `Evidence.engagement_id == E0` and an `active` version, and `passed`. A second call with a term found in no document (`"zz-no-such-term"`) returns 0 rows. That call is untimed.
7. **Results JSON contract**: keys exactly as in D-P4-3-I; four operations in D-P4-3-G order; each has 5 `runs_seconds`; `median_seconds` equals `statistics.median(runs_seconds)`; `threshold_seconds == 2.0`.
8. **The benchmark never touches the dev DB.** `settings.database_url` inside the fixture points into `tmp_path_factory`. The existing session guard `_guard_dev_database_untouched` covers the rest; don't weaken it.
9. **CLI refusal** (under the same module `skipif` as everything else): `main(["--db", str(existing_file)])` returns 2 and leaves the file unchanged.

Scenarios 3–6 assert `passed`. Under D-P4-3-J step 3 a miss stays a failing assertion; don't `xfail` or skip it.

## Done criteria

- `CYBERASSESS_RUN_BENCHMARKS=1 .venv/bin/pytest -q -s tests/test_performance_benchmarks.py` passes. Paste the printed table.
- `.venv/bin/python scripts/benchmark_performance.py` exits 0. Paste its table and the JSON file's `counts` and `environment`.
- `.venv/bin/pytest -q` (no env var) → **502 passed** plus the new module's cases **skipped**, same runtime ± noise. (Expect the known fresh-worktree teardown error; nothing else.)
- `git diff --stat main` is limited to D-P4-3-L's list, plus D-P4-3-K's files only if an index was added. `git diff --stat main -- app/services app/routers app/utils app/templates scripts/seed_test_companies.py app/main.py app/database.py app/config.py` is empty.
- `alembic heads` is still exactly `4e8c1a9d2b57`, unless D-P4-3-K applied, in which case it is the new revision and `TestAlembicContractParity` plus `TestAlembicRoundTrip` pass.
- No `data/dpdpa.db` was created or modified by the benchmark (the session guard passes, and the CLI's default path is under the system temp dir).
- `tasks/todo.md` updated (Required approach step 5).

## Rollback

- **Code:** `git revert`. With no index added, this task adds two new files and changes no product code, so there is nothing to undo in data.
- **With an index (D-P4-3-K):** `alembic downgrade -1` drops it. It is index-only, so no data is lost, and the revert restores the head literals.
- **Data:** the benchmark only ever writes to its own temp DB.

## Open questions (deliberately flagged, not resolved here)

1. **Evidence search doesn't exist as a product feature.** This task measures a reference query (D-P4-3-G item 4). The PRD (line 254: archived records "remain searchable") implies a search surface nobody owns yet. When one is built, re-point operation 4 at it.
2. **The integrated engagement report isn't timed** because generating it is a write path (a snapshot file plus audit events per call). If it matters, time it once per fresh seed in a follow-up.
3. **CI:** the opt-in module doesn't run by default anywhere. Whether a scheduled or nightly job should set `CYBERASSESS_RUN_BENCHMARKS=1` is a process decision outside this task.

## Report back

Append a `## Results` section containing:
- the printed benchmark table (medians, maxes, statement counts) from both the CLI run and the opt-in pytest run, plus `seed_seconds` and the JSON `environment` block;
- the full `counts` dict, and the actual A0 revision and Finding counts versus the expected 1083 and 95 (with the reason for any difference);
- the workpaper and report `breakdown` numbers, and the workpaper median next to P2-6's `0.010783s` 41-conclusion baseline;
- for any miss, the D-P4-3-J attribution (the function, the statement count, the time split, `EXPLAIN QUERY PLAN` output for any index candidate), what was done (an index, per D-P4-3-K), or the "threshold miss requiring a follow-up" / "Postgres gate" paragraph;
- `.venv/bin/pytest -q` output without the env var, and `alembic heads`;
- anything this document got wrong about the current code (a drifted symbol, a stub that no longer matches `trigger_analysis`, a seed step the real services rejected). Name it rather than working around it.

## Results

Implemented `scripts/benchmark_performance.py` and `tests/test_performance_benchmarks.py`. The seeder uses a fresh Alembic-built file-backed SQLite database, real A0 analysis/decision/finding paths with patched deterministic analysis results, direct ORM filler rows, fresh sessions per measured request, five timed runs after one warm-up, statement counters, breakdown timings, CLI JSON logging, and the required opt-in pytest guard. No numbered D-P4-3 decision was changed, and no index was required.

CLI run (`.venv/bin/python scripts/benchmark_performance.py`, fresh explicit temp database):

```text
name                       | median_s | max_s    | statements | status | PASS/FAIL
---------------------------+----------+----------+------------+--------+----------
portfolio_dashboard        | 0.002585 | 0.002896 | 4          | 200    | PASS
workpaper_3_framework      | 0.235780 | 0.312872 | 1158       | 200    | PASS
gap_report_pdf_3_framework | 0.494659 | 0.512616 | 250        | 200    | PASS
evidence_search_engagement | 0.001429 | 0.001535 | 1          | None   | PASS
```

Opt-in pytest run (`CYBERASSESS_RUN_BENCHMARKS=1 .venv/bin/pytest -q -s tests/test_performance_benchmarks.py`):

```text
name                       | median_s | max_s    | statements | status | PASS/FAIL
---------------------------+----------+----------+------------+--------+----------
portfolio_dashboard        | 0.003184 | 0.005135 | 4          | 200    | PASS
workpaper_3_framework      | 0.224453 | 0.331271 | 1158       | 200    | PASS
gap_report_pdf_3_framework | 0.518870 | 0.524752 | 250        | 200    | PASS
evidence_search_engagement | 0.001429 | 0.001593 | 1          | None   | PASS
```

Both runs used Python `3.13.13`, SQLite `3.53.2`, and platform `macOS-26.3.1-arm64-arm-64bit-Mach-O`. `seed_seconds` was `34.51195833273232` for the CLI run and `35.79861733317375` for the pytest run. The pytest JSON recorded the same operation order and threshold `2.0` seconds.

The full counts dict from the CLI JSON was:

```json
{"a0_conclusion_revisions": 1083, "a0_findings": 95, "actions": 95, "analysis_runs": 41, "assessment_packs": 32, "assessments": 30, "audit_events": 1709, "clients": 5, "conclusion_revisions": 3000, "conclusions": 808, "engagements": 10, "evidence": 250, "evidence_uses": 114, "evidence_versions": 500, "findings": 95, "gap_items": 228, "gap_reports": 1, "questionnaire_responses": 808}
```

A0 produced the expected `1083` conclusion revisions and `95` findings. The workpaper breakdown was `build_workpaper_seconds=0.208192` in the CLI run and `0.236377` in the pytest run; its pytest median `0.224453s` is recorded next to the P2-6 baseline of `0.010783s` for 41 conclusions. The report breakdown was `assessment_findings_seconds=0.098320` and `generate_pdf_seconds=0.414557` in the CLI run, and `0.095756` and `0.434039` in the pytest run.

`.venv/bin/pytest -q` completed with `502 passed, 9 skipped, 126 warnings in 43.70s`. The benchmark dataset seed did not run in normal mode. The known unrelated teardown artifact did not reproduce in this run; there were no test errors. The benchmark module itself passed `9 passed, 7 warnings in 44.27s`. `alembic heads` remained `4e8c1a9d2b57 (head)`.

No operation missed the 2-second median threshold, so the D-P4-3-J bounded miss ladder was not entered. No files outside `scripts/benchmark_performance.py`, `tests/test_performance_benchmarks.py`, `tasks/todo.md`, and this handoff were changed; `.venv` was pre-existing untracked worktree state and was left untouched.
