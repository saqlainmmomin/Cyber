# P5-2: Reader migration. Scores, the report tab, the report API, the gap-report PDF, comparison, the integrated report and every release gate read consultant-approved Conclusions only. Release becomes an explicit, attributable act bound to the exact approved Conclusion set. The legacy bulk review is retired. `GapReport` is kept as the frozen AI-proposal record and is never a source of client-visible outcomes or numbers.

**Plan:** `docs/plans/2026-09-24-001-cleanup-and-non-dpdpa-parity-plan.md`, task P5-2 ("Reader migration: approved Conclusions drive scores, reports, the PDF and release"). It closes audit finding **A1** (the reader migration that was never scheduled), the PDF half of **A7** (DPDPA-specific boilerplate on every framework), and plan-level decision **D-P5-B**. It also closes the open questions that every handoff from P2-3 through P3-4 deferred to "the reader migration (P2-3 open question 1)": P2-3 OQ1, P2-4 OQ2 ("the release gate must then move to every in-scope Conclusion individually approved or edited, excluding legacy bulk approvals"), P2-6's scores non-goal, P3-1's Report-tab `GapItem` blocks, P3-2 OQ4 ("snapshots of un-migrated readers"), P3-4's `GapItem`-sourced "Critical Findings"/"Detailed Findings", and P5-1 OQ2 (`review_status` survives a re-run).

**Product contract** (`docs/product/2026-09-21-cyberassess-product-requirements.md`):
- **PR-045** "Numeric or categorical methodology calculations shall be deterministic and operate only on eligible consultant-approved Conclusions." Acceptance: "AI cannot emit a final score; methodology version and inputs are recorded; qualitative judgment remains visible; no engagement-level blended compliance score exists."
- **PR-052** Acceptance: "exports use approved Conclusions only and remain unavailable until review gates pass."
- **PR-042** Acceptance: "Insufficient evidence is distinct from Non-compliant and from an unanswered questionnaire; deterministic methodology states how each outcome affects displayed scores and denominators."
- **PR-041** Acceptance: "incomplete Requirement coverage fails closed rather than yielding a misleading complete report."
- **PR-054** Acceptance: "regenerating output creates a new version bound to the exact approved Conclusion set and does not overwrite an issued artifact."
- **PR-056** lists "release" among the operations that must create attributable audit events.
- **Invariant 7:** "AI output is always a proposal. Only a consultant decision becomes a final Conclusion."
- **Guardrail:** "No report or downloadable client deliverable is released from unapproved Conclusions."
- **PRD open question 2** ("What deterministic denominator and presentation rule should `Insufficient evidence` use so it is neither hidden nor treated automatically as Non-compliant?") is **closed here** (D-P5-2-D).

**Decisions log:** `tasks/2026-09-21-adversarial-review.md`, **D3** ("AI conclusion approval | Individual only | Each conclusion requires consultant to view evidence + proposal before approving. No bulk-accept."), **D2** (generic `audit_events`, normalize later), **D6** (optimistic locking).

**Owner:** Claude designs (foundational, and a product invariant; `tasks/agent-ownership.md` criteria "Foundational/gating" and "A product invariant") → Codex implements → Claude reviews, **plus a second, more skeptical review pass** (as P2-3 and P4-4 had), because this task changes what a client can be shown. Every fork is closed below.

> **If the code forces a deviation from this design, stop and report it in `## Results`. Do not pick an alternative.** That applies to every numbered decision, every constant, message, key name, status value and ordering below, and every test scenario. "The existing code makes step N awkward" is not a licence to redesign step N. Write down what you found and what you would need to change, then stop.

> **P5-1's decisions are a fixed contract this task inherits, not open questions.** Specifically D-P5-1-D (`UNCONFIRMED_ANSWER_SOURCES`, `confirmed_response_clause()`), D-P5-1-E (the failed-framework sentinel and its helpers), D-P5-1-G (no release while a framework failed, with `RELEASE_BLOCKED_MESSAGE` text unchanged) and D-P5-1-H (the R1-R13 read-site table, used below as the checklist of readers to move). Where this task changes something P5-1 wrote, the decision here names the D-P5-1 decision it amends. Nothing here weakens any of them.

**Depends on:** P5-1 (merged, PR #40) and P5-3 (merged, PR #41). `main` is at `d69aa71` (`d69aa71d12823d9939e0eea69a01a7c05429fb31`).
**Blocks:** P5-6 (RFI rebuilt from approved Conclusions; it reuses this task's approved view and release gate).
**Runs in parallel with:** P5-4 (adaptive UCC questionnaire). File overlap is limited to `app/routers/web.py`, in disjoint functions (D-P5-2-T).
**No failing contract suite is pre-written.** `grep -rlnE "approved_report|record_release|assessment\.released|approved_framework_scores|pending_review|RELEASE_EVENT" tests/` finds nothing, `ls tests/ | grep p5_2` finds nothing, and no existing test scores from `Conclusion.outcome` (the only `Conclusion`-plus-scoring references in `tests/` are the two grep guards that forbid it, D-P5-2-R). **Codex writes `tests/test_p5_2_reader_migration.py` itself**, working from `## Test scenarios`. Every scenario listed is required. You may add cases, but you may not drop or weaken one. Existing test files and scripts may be changed **only** under the rule in D-P5-2-S.

## Step 0 (dispatching Claude session, before Codex starts)

**The suite baseline was not measured by the author of this handoff.** This handoff was written in a cloud container where PyPI is blocked by the network policy (`pypi.org` → 403 `host_not_allowed`), there is no `.venv`, and system Python is 3.11, so `pytest` could not run. The last independently re-verified number is the P5-3 merge record in `tasks/todo.md` and P5-3's Results: **593 passed, 9 skipped, 0 failed** (after commit). **Before dispatch, create the worktree (`git worktree add ../dpdpa-gap-tool-p5-2 -b codex/p5-2-reader-migration main`, symlink `.venv`, copy `.env`), run `.venv/bin/pytest -q` there, and write the measured baseline into this section.** Do not trust 593 without re-running it.

**Codex, your first action:** run

```bash
grep -n "^UNCONFIRMED_ANSWER_SOURCES\|^def confirmed_response_clause" app/services/auto_answer.py
grep -n "^FRAMEWORK_ANALYSIS_FAILED\|^def failed_framework_scores\|^def is_failed_framework_score\|^def failed_framework_ids" app/services/scoring.py
grep -n "^RELEASE_BLOCKED_MESSAGE" app/utils/review_gate.py
grep -n "^def load_desk_review_data\|^def scoped_findings" app/services/desk_review_findings.py
.venv/bin/alembic heads
```

and confirm: all four P5-1 scoring symbols and both P5-1 answer symbols exist with those names; `RELEASE_BLOCKED_MESSAGE` is defined in `review_gate.py`; P5-3's `load_desk_review_data` and `scoped_findings` exist; and the single Alembic head is `8b2d5f7e1c34`. **If any of this is not true, stop and report in `## Results`.**

## Goal

1. Every client-visible outcome and every number (per-framework score, chapter score, requirement counts, gap cards, roadmap, comparison deltas, integrated-report score lines) is computed deterministically from **eligible consultant-approved Conclusions only** (D-P5-2-B). No release surface reads `GapItem`, `GapReport.framework_scores` numbers, `GapReport.chapter_scores`, `Initiative` or the AI executive summary.
2. `Insufficient evidence` has a published deterministic rule: excluded from the score denominator, never treated as Non-compliant, and **always shown next to the score** as a count and coverage fraction (D-P5-2-D). The PDF methodology states the rule.
3. A report is **releasable** only when every in-scope requirement of every selected framework has an eligible approved Conclusion, no framework failed analysis, and analysis is not running (D-P5-2-F). Release is an explicit consultant action that writes one attributable `assessment.released` audit event bound to a manifest of the exact approved Conclusion versions and scope (D-P5-2-G). Any later change to an in-scope approved Conclusion or to scope makes the release **stale**, and every export closes until the consultant releases again.
4. `approve_assessment`, `disposition_item` and `reject_assessment` (the bulk accept D3 forbids) are retired with an explicit 410, and write nothing (D-P5-2-I). Hand-setting `assessments.review_status = "approved"` releases nothing: no code path reads that column for any decision.
5. The report tab, the report JSON API, the live and snapshot gap-report PDF, the analysis poll, comparison and the integrated report render from the approved view. Frameworks awaiting review show progress, not a number.
6. Issued snapshots never change (PR-054). A draft can only be issued if it was generated after, and under, the current release (D-P5-2-O).
7. Pre-P2-3 assessments (no Conclusions), migrated legacy assessments (legacy bulk approvals, no captured citations) and assessments released under the retired bulk route all fail closed, with a documented path back to release (D-P5-2-Q).
8. The PDF "What Is Not Covered", "Recommended Follow-On Actions" and non-DPDPA "Framework Overview" copy is conditional on the selected frameworks (A7), additively.

## Current state

Grounded against `d69aa71` on `main` (P5-1, P5-3, P5-5, P5-8 merged). Line numbers below were read at that commit. Relocate everything by symbol name.

### The Conclusion model and decision workflow

- `app/models/conclusion.py`: `Conclusion(id, assessment_id, requirement_id, framework_id, cluster_id, outcome, rationale, evidence_summary, gaps_identified, risk_level, recommended_action, ai_proposed, version, created_at, updated_at)`, unique on `(assessment_id, framework_id, requirement_id)` (lines 10-40). `ConclusionRevision(id, conclusion_id, actor, action, previous_outcome, previous_rationale, citations_json, analysis_run_id, created_at)` (lines 43-58). **No relationship(), no status column**: a Conclusion's decision state is derived from its revisions.
- `app/services/conclusion_review.py`:
  - `CONCLUSION_OUTCOMES = ("compliant", "partially_compliant", "non_compliant", "not_applicable", "insufficient_evidence")` (lines 22-28). **`insufficient_evidence` is one of them.** `GAP_OUTCOMES = ("partially_compliant", "non_compliant", "insufficient_evidence")` (29-33). `RISK_LEVELS = ("critical", "high", "medium", "low")`.
  - `REVIEWER_ACTOR_PREFIX = "consultant:"`, `reviewer_actor(name)` → `"consultant:<name or Manager Review>"` (20, 103-105).
  - `ALLOWED_ACTIONS` (48-53): `pending → approved/edited/rejected`, `rejected → approved/edited`, `approved/edited → reopened`.
  - `_decision_state` (121-144): the latest human revision (action in `analysis_pipeline.HUMAN_DECISION_ACTIONS = ("approved", "edited", "rejected", "reopened")`) decides the state; `approved`/`edited` lock (`LOCKING_ACTIONS`).
  - `_approval_blocker` (156-173): approval is refused with `EVIDENCE_NOT_CAPTURED` when the latest `proposed` revision has `citations_json is None` (every migrated legacy Conclusion), `INCOMPLETE_CONCLUSION` or `INCOMPLETE_GAPS`.
  - `decide(...)` (204-264) swaps the Conclusion through `analysis_pipeline.swap_conclusion` (compare-and-swap on `version`, D6) and writes one revision. **Every human decision increments `Conclusion.version`.**
  - `conclusion_cards` (361-500) computes each card's `state`, `locked`, `legacy_bulk_approval` (**an `approved` latest human revision whose actor does not start with `consultant:`**, lines 444-448) and `legacy_report_status` (the GapItem outcome when it differs).
- `app/services/analysis_pipeline.py`: `OUTCOME_BY_STATUS` maps `not_assessed` → `insufficient_evidence` and any unknown status → `UNKNOWN_STATUS_OUTCOME = "insufficient_evidence"` (53-60). `record_framework_run` (297-423) creates or applies a proposal to every requirement the analyzer returned; a **locked** Conclusion is left untouched and gets a `proposal_withheld` revision (**its version does not change**). `load_conclusion_state` (209-246). The module docstring promises no row removal and never commits.
- `app/services/findings.py`: `ELIGIBLE_STATES = ("approved", "edited")` (line 52); Findings come only from eligible, non-legacy-bulk cards. `report_content.assessment_findings` (147-264) already filters `source_approved and not card.legacy_bulk_approval`. **The PDF "Approved Findings" section is already Conclusion-sourced (P3-3). Everything else in the report is not.**
- The analyzer rejects incomplete responses: `app/schemas/llm_output.py::validate_and_filter` raises `IncompleteAssessmentError` unless every known requirement id is covered. A **successful** framework run therefore yields a Conclusion for every control of that framework, including out-of-scope ones (the server forces them to `not_applicable`, `app/routers/analysis.py` lines 344-349 single path, 651-656 multi path, before `record_framework_run`). A requirement can still lack a Conclusion when: the framework failed (P5-1 sentinel); the assessment predates P2-3 and was never migrated; the legacy migration only had some `GapItem`s; or a test/seed stub bypasses `validate_and_filter`.

### Scoring (`app/services/scoring.py`)

- `STATUS_SCORES = {"compliant": 100, "partially_compliant": 50, "non_compliant": 0}`, `KNOWN_STATUSES = STATUS_SCORES | {"not_assessed", "not_applicable"}` (17-24).
- `compute_framework_scores(assessments, framework_id)` (572-632): a requirement absent from `assessments`, or with a status outside `KNOWN_STATUSES`, is treated as `not_assessed`; `not_assessed` and `not_applicable` are **excluded** from the section averages; a domain with no scored requirement gets `applicable: False, score: 0.0`; an assessment with nothing scored returns `overall_score: 0.0, overall_rating: "Non-Compliant"` (the A2-style fake zero). **Today's de facto rule for `insufficient_evidence` (via `not_assessed`) is already "excluded from the denominator", but it is displayed nowhere.**
- P5-1 sentinel (52-74): `FRAMEWORK_ANALYSIS_FAILED = "failed"`, `failed_framework_scores()`, `is_failed_framework_score(entry)`, `failed_framework_ids(framework_scores, framework_ids)`.
- `namespaced_domain_scores` (635-656) keys chapters `f"{framework_id}:{domain_key}"`, titles `f"{framework.name} — {domain title}"`, skips failed entries.
- `report_framework_scores(report, assessment)` (659-682) parses `report.framework_scores` via `getattr`, with a single-framework legacy fallback from `chapter_scores`/`overall_score`.
- `score()` (222-284) is the P1 cluster-first scorer. It reads `GapItem`. **No app surface calls it** (`grep -rn "scoring import" app scripts` shows only the helpers above, `KNOWN_STATUSES` and `compute_delta`). Out of scope (open question 5).
- `compute_delta(current_items, previous_items)` (287-367) is duck-typed on `.requirement_id`, `.requirement_title`, `.compliance_status`.

### The release chokepoint and every release path

- `app/utils/review_gate.py::require_review_approval(assessment_id, db) -> Assessment` (lines 11-36): 404 "Assessment not found" → **403 unless `assessment.review_status == "approved"`** ("Report not yet approved for release. Complete the review process first.") → if a `GapReport` exists and `failed_framework_ids(...)` is non-empty, **409** `RELEASE_BLOCKED_MESSAGE = "Analysis failed for {names}. Run analysis again before releasing this report."` (line 8).
- Callers: `reports.get_report` (84), `get_report_summary` (122), `get_full_report` (168), `_download_pdf_response` (249/251; with P5-1's `allow_failed_draft` seam at 245-249), `compare_assessments` (336-337); `web.comparison_page` (2250-2251), `download_rfi_pdf` (2415), `download_rfi_docx` (2441+); `snapshots.issue_snapshot_route` (131). Draft gap-report generation goes through `snapshots._render` (50-63) → `reports._download_pdf_response(..., allow_failed_draft=True)`, so **gap-report draft generation is release-gated except when a framework failed**; workpaper generation is not gated.
- Other `review_status == "approved"` readers: `reports.get_comparable_assessments` SQL filter (313), `web.report_summary` comparable SQL filter (2007), `report_content.integrated_report` (284, `NOT_RELEASED`), `integrated_reports.issue_integrated_report` (110, `INTEGRATED_NOT_RELEASABLE`), templates `partials/report_summary.html` (3, 11 review banner), `pages/report_snapshots.html` (35), `pages/review.html` (23, 34).
- **The only writer of `review_status = "approved"`** is `review.approve_assessment` (`app/routers/review.py` 106-142), which refuses while any `GapItem` is `draft` and then stamps `reviewed_by`/`reviewed_at` on every `GapItem` — "the bulk accept D3 forbids" (P2-4 handoff line 55). `disposition_item` (58-103) edits one `GapItem` and sets `review_status = "under_review"`; `reject_assessment` (145-177) sets `"rejected"`. **None of them looks at a Conclusion.** Analysis never resets `review_status` (P5-1 OQ2).
- **So today a consultant can release a PDF whose scores are 100% AI-proposed without approving one Conclusion**, and a hand-set `review_status` releases everything.

### Every reader to move (the P5-1 R1-R13 table, extended)

| # | Reader | Reads today |
|---|---|---|
| X1 | `reports.get_report` (82-117) | `GapItem`s → `gap_items`, roadmap by `remediation_priority`; `Initiative`s; `report.executive_summary`; `report_framework_scores`; `report.chapter_scores` |
| X2 | `reports.get_report_summary` (120-157) | `GapItem` status counts and critical/high counts; framework scores; chapter scores |
| X3 | `reports.get_full_report` (160-231) | same, grouped by framework, plus `evidence_confidence`, initiatives |
| X4 | `reports._download_pdf_response` (239-295) → `pdf_export.generate_pdf(report, items, company_name, initiatives=, answer_source_map=, selected_frameworks=, assessment=, report_findings=)` | the `GapReport` and its `GapItem`s |
| X5 | `pdf_export.generate_pdf` (660-1314) | `report.chapter_scores`, `report_framework_scores(report, …)`, `report.executive_summary`, `GapItem` attributes (`requirement_id`, `requirement_title`, `chapter`, `compliance_status`, `risk_level`, `gap_description`, `remediation_action`, `remediation_priority`, `remediation_effort`, `timeline_weeks`, `maturity_level`, `evidence_quote`) — **duck-typed; it never queries the DB** |
| X6 | `reports.compare_assessments` (328-347), `web.comparison_page` (2238-2313) | `compute_delta` over `GapItem`s; framework deltas from `report_framework_scores` |
| X7 | `reports.get_comparable_assessments` (298-325), `web.report_summary` comparable list (2001-2012) | SQL `review_status == "approved"` |
| X8 | `web._framework_display` (91-110) via `assessment_detail` (890-895), `analysis_status` (1758-1784) | `report_framework_scores` |
| X9 | `web.report_summary` (1932-2058) → `partials/report_summary.html` | `GapItem`s for status counts, chapter bars, business impact, root causes, critical findings, quick wins, detailed findings, legacy remediation panel, reviewer name; `report.executive_summary`; review banner |
| X10 | `web.framework_tab` (713-748), `assessment_detail` `active_framework_finding_count` (934-937) | `GapItem` counts per framework |
| X11 | `report_content.integrated_report` (267-367) | `review_status`; `report_framework_scores` score lines |
| X12 | `integrated_reports.issue_integrated_report` (~90-128) | `review_status` per source assessment |
| X13 | `web.review_page` (2061-2095) → `pages/review.html` | `GapItem` review queue with the bulk-approve form |
| — | `web.generate_rfi_web` (2319-2406), `download_rfi_pdf`/`docx` | `GapItem`s → RFI. **P5-6 owns the RFI** (D-P5-E); only its download gate changes here |

`app/routers/analysis.py` writes `GapReport`/`GapItem`/`Initiative` and the P2-3 records; it reads no report data. **This task does not change it** (D-P5-2-T).

### Snapshots (`app/services/report_snapshots.py`, `app/routers/snapshots.py`)

- `source_manifest(db, assessment)` (101-115) = `{"gap_report_id", "conclusion_versions": [[id, version], …] sorted by id}` over **every** Conclusion of the assessment. It is recorded in the `report_snapshot.generated` event's `source` (key set of the event metadata pinned by `test_report_snapshots`/`test_pdf_updates`: `schema_version, type, format, storage_path, sha256, size_bytes, assessment_id, engagement_id, review_status, source`). `snapshot_rows` shows "Source data changed" when `metadata["source"] != source_manifest(...)`.
- `issue_snapshot` (342-373) flips `is_issued` through `ISSUE_SQL` (newest-only). Issue is gated by `require_review_approval` in the route. **There is no check that the draft being issued was rendered from the currently approved state.**
- Issued bytes are never re-rendered (P3-2 D-P3-2-A); P3-2's accepted limitation was that gap-report bytes were rendered from `GapItem` (its OQ4).

### PDF boilerplate (A7) — `app/utils/pdf_export.py`

- "What Is Not Covered" (line 1205): "…source code review, network security assessment, physical security review, or any form of independent technical verification…" for every framework.
- "Recommended Follow-On Actions" (1211): "…independent verification by a qualified legal counsel or certified privacy professional is strongly recommended…" for every framework.
- Non-DPDPA "Framework Overview" (1262-1267): "Requirements are drawn directly from the source standard for each selected framework…" — in tension with D4 (reference-only ISO pack).
- Methodology "Scoring Formula" (1281-1282) describes questionnaire-response scoring only; it states nothing about approved Conclusions or `insufficient_evidence`.
- Cover summary (818): `f"{total} requirements assessed  |  {critical_count + high_count} gaps identified  |  ~{max_weeks} weeks to full remediation"`; KPI card "Remediation Timeline" `f"~{max_weeks}w"` (847-848); timeline tag `f"{item.remediation_effort} | ~{item.timeline_weeks}w"` (306); `_draw_status_bar` order/labels (236-276) know only `compliant/partially_compliant/non_compliant/not_assessed`; `STATUS_COLORS` (36-41) likewise.
- `generate_pdf`'s parameter list is pinned by `tests/test_pdf_updates.py::test_scenario_3_empty_findings_preserve_existing_pdf_pages` (`["report", "gap_items", "company_name", "initiatives", "answer_source_map", "selected_frameworks", "assessment", "report_findings"]`) and called directly with a real `GapReport` + `GapItem`s by `test_golden_dpdpa.py`, `test_white_label.py`, `test_no_blended_scoring.py` and `test_pdf_updates.py`.

### Scope rule already used by the workpaper

`app/services/workpaper.py::_scope(raw)` (116-127): `None`, `""`, invalid JSON, a non-list, an **empty list**, or a list containing a non-string → `None` ("no restriction"); otherwise `frozenset(values)`. `build_workpaper` marks a Conclusion `in_scope` iff `applicable is None or requirement_id in applicable` (399-401) and lists `unconcluded` in-scope registry controls with no Conclusion (448-462). **This differs from P5-1's gate helper** (`analysis._applicable_requirement_ids`, where `"[]"` means "nothing expected"). D-P5-2-C picks the workpaper rule so the reviewer's trace and the release gate agree.

### Standing guards (read before editing)

- `tests/test_no_blended_scoring.py::test_no_template_reads_retired_score`: no `overall_score` in any template; `.overall_score` attribute access or `overall_score=` keyword only in `app/models/report.py`, `app/services/scoring.py`, `app/schemas/scoring.py`, `app/legacy_migrations*.py`, `app/routers/analysis.py`; and the `analysis.py` line rule. **Unchanged and must stay green unmodified.** Dict string keys `"overall_score"` are fine outside `analysis.py`.
- `tests/test_no_blended_scoring.py::test_report_api_has_only_framework_score_shapes`: no top-level `overall_score`/`overall_rating` in `/report`, `/report/summary`, `/report/full`.
- **The Conclusion-mention guard** (D-P2-3-A, "legacy consumers keep reading GapItem"): `tests/test_analysis_pipeline.py::test_legacy_consumers_do_not_read_the_new_tables` (lines 1112-1128, greps `scoring.py`, `review.py`, `reports.py`, `pdf_export.py` for `Conclusion|AnalysisRun|analysis_pipeline`, comments included), `tests/test_pdf_updates.py::test_scenario_10_structural_guards` (line 1044, `pdf_export.py` + `reports.py`), and `tests/test_correctness_bundle.py::test_p5_1_structural_guards_and_signatures` (lines 811-818, the same four files). **This guard makes P5-2 impossible as written; D-P5-2-R replaces it.**
- `report_content.py` must not contain `db.add(`, `db.add_all(`, `db.merge(`, `.flush(`, `.commit(` or `delete` (`test_pdf_updates` scenario 10, `test_correctness_bundle` scenario 10).
- `analysis_pipeline.py` must not contain `delete`. `grep -rn "relationship(" app/models/` must stay empty.
- `report_summary.html` must still contain `/snapshots"` and `Live PDF` and must not contain `Download PDF`/`PDF Report` (`test_report_snapshots`, `test_correctness_bundle` scenario 10). No template may contain `overall_score`, `CyberAssess` or `|safe`.
- `tests/test_retention.py` exercises every mutating route under an archived engagement and requires `PATCH /api/assessments/{assessment_id}/review/items/{item_id}` to exist and answer 409 from the router-level archive guard (lines ~818-832).
- `tests/test_needs_review_ui.py` renders `partials/review_finding_card.html` directly (line 44). That template must stay on disk.
- `tests/test_longitudinal_demo.py::test_scenario_13_protected_surface_is_unchanged` and `tests/test_retention.py::test_scenario_13_only_new_retention_test_file_changes` run `git diff --name-only` against the working tree. **They fail while your edits are uncommitted and pass once committed.** Do not modify them. Report them as "working-tree guard, expected until commit".
- `tests/test_longitudinal_demo.py::test_scenario_9_rollups_and_integrated_reporting` has a known intermittent ordering flake on unmodified `main`. Report it if seen; don't fix it.

## Decisions (made here so they are not relitigated)

### D-P5-2-A. One read-only service computes the approved view. Every release surface uses it.

- New module **`app/services/approved_report.py`**. It is the only place that turns Conclusions into client-visible rows, scores and release state. `reports.py`, `review_gate.py`, `report_content.py`, `integrated_reports.py`, `snapshots.py` and the `web.py` report functions call it; none of them re-derives eligibility or scope.
- It **never commits and never deletes**. Its only write is `record_release` (D-P5-2-G), which does `db.add` + `db.flush` and leaves the commit to the route. It imports no LLM client.
- It is computed **on read, every time** (no cache table, no cached JSON; D-P5-2-J). Inputs: the `Assessment`, its `GapReport` (existence, the P5-1 failed sentinel, `generated_at`, `id`), its Conclusions and their human-decision revisions, the registry, and `assessment.applicable_requirements`.
- Public API (exact names):
  ```python
  RELEASE_EVENT = "assessment.released"
  RELEASE_SCHEMA_VERSION = 1
  FRAMEWORK_VIEW_STATUSES = ("scored", "not_scored", "pending_review", "unavailable", "failed")
  PRIORITY_BY_RISK = {"critical": 1, "high": 2, "medium": 3, "low": 4}

  def in_scope_requirement_ids(raw: str | None) -> frozenset[str] | None: ...
  def build_approved_report(db: Session, assessment: Assessment) -> ApprovedReport: ...
  def release_state(db: Session, assessment: Assessment) -> ReleaseState: ...   # == build_approved_report(...).release
  def is_released(db: Session, assessment: Assessment) -> bool: ...
  def record_release(db: Session, assessment: Assessment, *, actor: str) -> AuditEvent: ...
  def latest_release_event(db: Session, assessment_id: str) -> AuditEvent | None: ...

  class ReleaseRefused(Exception):
      status_code = 409
      def __init__(self, message: str, blockers: tuple[str, ...] = ()): ...
  ```
  and the frozen dataclasses `ApprovedRow`, `FrameworkReview`, `ReleaseState`, `ApprovedReport`, `RenderReport` defined in D-P5-2-B/E/F/K/M.

### D-P5-2-B. Which Conclusions count ("eligible")

A Conclusion is **eligible** iff its **latest human-decision revision** (the latest `ConclusionRevision` with `action in analysis_pipeline.HUMAN_DECISION_ACTIONS`, ordered by `created_at` then `rowid`, exactly as `load_conclusion_state` orders them) has `action in analysis_pipeline.LOCKING_ACTIONS` (`approved`, `edited`) **and** `actor.startswith(conclusion_review.REVIEWER_ACTOR_PREFIX)`.

- Not eligible: no human decision (pending), `rejected`, `reopened`, and any locking decision whose actor lacks the `consultant:` prefix (the migrated `reviewed_by` stamps: `legacy_bulk_approval`, D3).
- Load it the lean way (one Conclusion query + one revision query with `ConclusionRevision.action.in_(HUMAN_DECISION_ACTIONS)` for the assessment), **not** through `conclusion_cards`, which resolves citations for every card. Scenario 3 proves parity with `conclusion_cards`' `state` and `legacy_bulk_approval` for every Conclusion.
- The eligible row records `decision` (`"approved"`/`"edited"`), `decided_by` (actor minus the prefix) and `decided_at` (that revision's `created_at`).
- `proposal_withheld` revisions never change eligibility. A consultant's locked decision stands across re-runs (D-P2-3-C); the withheld proposal remains visible on the Conclusions page as today.

### D-P5-2-C. The in-scope set

- `in_scope_requirement_ids(raw)` has **exactly** `workpaper._scope`'s semantics (Current state). Do not import the private `_scope`; re-implement it and prove parity in scenario 4 on `None`, `""`, `"[]"`, `"not json"`, `"{}"`, `'["a", 1]'`, `'["CH2.NOTICE.1"]'`.
- For each selected framework `fw` (in `assessment.frameworks` order): `in_scope_ids(fw)` = the registry controls of `fw` in registry order (`FrameworkRegistry.get(fw).all_controls()`), filtered to `applicable` when `applicable is not None`.
- **Out-of-scope Conclusions are never rows and never scored**, whatever their outcome or state, and never block release. Coverage reports them as `out_of_scope` (D-P5-2-E). Scoping is the consultant-recorded decision for them (DPDPA statutory exclusions, PR-012); it is not re-litigated per Conclusion.
- `missing_ids(fw)` = in-scope ids with no Conclusion row for `(assessment, fw, id)`. Scenario 4 proves it equals `build_workpaper`'s `unconcluded` for the same framework.

### D-P5-2-D. The scoring input contract. PRD open question 2 is closed.

**Rule (published in the PDF methodology, D-P5-2-M):** among eligible in-scope Conclusions, `compliant` = 100, `partially_compliant` = 50, `non_compliant` = 0 and all three are in the denominator; `not_applicable` and `insufficient_evidence` are **excluded from the denominator**. `insufficient_evidence` is never converted to `non_compliant`. The count of `insufficient_evidence` requirements, and the fraction of in-scope requirements actually scored, are **always displayed next to every framework score**, on every surface that shows a score (report tab gauge, PDF dashboard, API `coverage`). A framework with no scoring outcome at all is **not scored** (no number), never "0% Non-Compliant".

Why this rule:
1. **It neither hides nor punishes.** Counting it as 0 would be exactly "treated automatically as Non-compliant", which PR-042 forbids; the consultant chose `insufficient_evidence` precisely because they could not conclude `non_compliant`. Dropping it silently would hide it. Excluding it from the arithmetic while forcing its count next to the number is the only option that satisfies both halves of the PRD sentence.
2. **It is the rule the engine already applies.** `compute_framework_scores` already excludes `not_assessed` (which `OUTCOME_BY_STATUS` maps to `insufficient_evidence`). Keeping it means an unchanged approval reproduces the AI-proposed number exactly (scenario 2), so no existing assessment's numbers move merely because of the migration, only because a consultant decided differently.
3. **A threshold was considered and rejected for now.** Suppressing the score below, say, 50% coverage is defensible but arbitrary without consultant input; it is open question 1. The mandatory coverage line is the fail-safe in the meantime, and "not scored" covers the 0% case.

Implementation, in `app/services/scoring.py` (pure; no DB, no ORM import):
```python
APPROVED_OUTCOME_POINTS = {"compliant": 100, "partially_compliant": 50, "non_compliant": 0}
DENOMINATOR_EXCLUDED_OUTCOMES = ("not_applicable", "insufficient_evidence")

def approved_framework_scores(outcomes: dict[str, str], framework_id: str) -> dict:
    """Deterministic per-framework score from approved outcomes (requirement id -> outcome).

    Callers pass eligible in-scope outcomes only. Unknown outcome -> ValueError.
    """
```
- Raise `ValueError(f"Unknown approved outcome {outcome!r} for {requirement_id}")` for any outcome outside the five.
- If no outcome is in `APPROVED_OUTCOME_POINTS`: return `{"status": "not_scored", "overall_score": None, "overall_rating": None, "domain_scores": {}}`.
- Else: `base = compute_framework_scores([{"requirement_id": r, "compliance_status": o} for r, o in outcomes.items() if o in APPROVED_OUTCOME_POINTS], framework_id)` and return `{"status": "scored", **base}`. `compute_framework_scores` is **not modified**.
- `scoring.py` may now mention Conclusions in comments/docstrings (D-P5-2-R lifts that guard) but **must not import** `app.models.conclusion`, `app.services.analysis_pipeline` or `app.services.approved_report`. The scoring engine stays DB-free for this function.

### D-P5-2-E. Per-framework view status and exact entry shapes (composes with the P5-1 sentinel)

`ApprovedReport.framework_scores` has one entry per selected framework, in selection order. Exactly one of:

| Status | When (first match wins) | Entry |
|---|---|---|
| `failed` | `is_failed_framework_score(report_framework_scores(gap_report, assessment).get(fw))` | exactly `failed_framework_scores()` (P5-1 D-P5-1-E; no `coverage` key) |
| `unavailable` | the framework has **zero** Conclusion rows for this assessment and at least one in-scope id | `{"status": "unavailable", "overall_score": None, "overall_rating": None, "domain_scores": {}, "coverage": C}` |
| `pending_review` | any in-scope id is missing or not eligible | same shape, `"status": "pending_review"` |
| `not_scored` | all in-scope ids eligible (or none in scope) and no scoring outcome | `approved_framework_scores(...)` result + `"coverage": C` |
| `scored` | all in-scope ids eligible and at least one scoring outcome | `approved_framework_scores(...)` result + `"coverage": C` |

- **The failed sentinel wins even if older approved Conclusions exist for that framework.** A partial re-run failure means the current analysis state is unknown; P5-1 D-P5-1-G's "never releasable while a framework failed" is kept verbatim.
- **A number is shown only for a fully reviewed framework.** A partial score over the approved subset is exactly the "misleading complete report" PR-041 forbids.
- `C` (coverage), exact key set and order: `{"in_scope", "out_of_scope", "eligible", "missing", "awaiting", "scored", "compliant", "partially_compliant", "non_compliant", "not_applicable", "insufficient_evidence"}`, all ints. Outcome counts count **eligible in-scope** Conclusions only. `scored` = compliant + partially_compliant + non_compliant. `out_of_scope` = Conclusion rows of this framework whose id is not in scope. `awaiting` = in-scope Conclusions that exist but are not eligible.
- `ApprovedReport.chapter_scores = namespaced_domain_scores({fw: entry for fw, entry in framework_scores.items() if entry["status"] == "scored"})`.
- `app/schemas/report.py::FrameworkScoreOut` (P5-1 R3, amended): `status: Literal["scored", "not_scored", "pending_review", "unavailable", "failed"] = "scored"`, and a new optional `coverage: dict[str, int] | None = None`. A P5-1 stored entry without `status` still validates as `"scored"` (scenario 16 re-asserts P5-1's two schema checks).
- **`GapReport.framework_scores` keeps P5-1's stored contract unchanged** (full AI-derived dict or the sentinel). It is the analysis record; the approved view is a separate, computed dict with its own documented shapes.

### D-P5-2-F. What "releasable" means. Blockers, order, messages.

`ReleaseState.blockers` is a tuple of strings, built in exactly this order; `releasable = not blockers`:

1. No `GapReport` → `NO_ANALYSIS_MESSAGE = "Run analysis before releasing this report."` Stop (no further blockers).
2. `assessment.status == "analyzing"` → `ANALYSIS_RUNNING_MESSAGE = "Analysis is running. Wait for it to finish before releasing this report."`
3. Failed frameworks (selection order) → `RELEASE_BLOCKED_MESSAGE.format(names=", ".join(registry names))`. **Text unchanged from P5-1.** Failed frameworks get no blocker 4 or 5.
4. For each other framework with missing ids → `MISSING_CONCLUSIONS_MESSAGE = "{name}: no conclusion was proposed for {count} in-scope requirement(s). Run analysis again."`
5. For each other framework with awaiting ids → `AWAITING_DECISION_MESSAGE = "{name}: {count} of {total} in-scope conclusions still need an individual consultant decision."` (`total` = in-scope count).
6. If the in-scope count summed over all selected frameworks is 0 → `NOTHING_IN_SCOPE_MESSAGE = "No requirement is in scope for this assessment. Record the scope before releasing."`

- **"Proposals that were never generated" block release** (blocker 4). There is no manual way to create a Conclusion, so the remedy is to re-run analysis, which the analyzer's completeness check (`validate_and_filter`) guarantees will propose every requirement. If a requirement can never be proposed, that is a bug to fix, not a release to allow (fail closed, PR-041). Open question 3 records the manual-conclusion idea.
- `insufficient_evidence` and `not_applicable` are legitimate final outcomes and **do not block** release. (Approval already requires a rationale for them: `_approval_blocker`, and `INCOMPLETE_GAPS` for `insufficient_evidence`.)
- `RELEASE_BLOCKED_MESSAGE` moves **definition** into `approved_report.py`; `app/utils/review_gate.py` re-exports it with `from app.services.approved_report import RELEASE_BLOCKED_MESSAGE` so `review_gate.RELEASE_BLOCKED_MESSAGE` is still importable and identical (P5-1 contract; this avoids a circular import).

### D-P5-2-G. Release is an explicit, attributable act bound to a manifest

- **Route:** `POST /api/assessments/{assessment_id}/release` in `app/routers/review.py` (sync `def`, `reviewer_name: str = Form("")`). The review router is already mounted with the P4-4 archive guard, so the route is archive-guarded automatically (no `main.py` change).
  - 404 JSON "Assessment not found".
  - `record_release(db, assessment, actor=conclusion_review.reviewer_actor(reviewer_name))`; on `ReleaseRefused` → `db.rollback()`, 409 JSON `{"detail": message, "blockers": list(blockers)}` with `X-Toast-Message: quote(message)` and `X-Toast-Type: error` (the `snapshots._error` pattern).
  - Success → `db.commit()`, 200 JSON `{"status": "released", "release_event_id": event.id}` with `HX-Redirect: /assessments/{id}?tab=report`, `X-Toast-Message: Report released`, `X-Toast-Type: success`.
- **`record_release`**, in order: compute the state; if `blockers` → `ReleaseRefused(" ".join(blockers), blockers)`; if `state.released` → `ReleaseRefused(ALREADY_RELEASED_MESSAGE)` with `ALREADY_RELEASED_MESSAGE = "This report is already released for the current approved conclusions."` (no duplicate event); else `db.add(AuditEvent(actor=actor, action=RELEASE_EVENT, entity_type="assessment", entity_id=assessment.id, metadata_json=json.dumps(metadata, sort_keys=True)))`, set `assessment.review_status = "approved"`, `db.flush()`, return the event.
- **Metadata, exact key set:** `{"schema_version": 1, "manifest": M, "gap_report_id": <id>, "coverage": {fw: C for scored/not_scored frameworks}}`. Identifiers and counts only, no free text (P4-4 D-P4-4-B: audit rows outlive a purge).
- **Manifest `M`, exact:** `{"framework_ids": list(assessment.frameworks), "in_scope": {fw: [ids in registry order] for each selected fw}, "conclusion_versions": [[conclusion_id, version], …] for every eligible in-scope Conclusion, sorted by conclusion_id}`.
- **`released`** iff `releasable` **and** the latest `assessment.released` event for the assessment (ordered by `created_at`, then `audit_events.rowid`) exists **and** its `metadata["manifest"] == M` computed now. **`stale`** iff such an event exists and `released` is false. `ReleaseState` carries `release_event_id`, `released_by` (actor minus prefix) and `released_at` of that latest event, whether or not it is still current.
- **Why the manifest excludes `gap_report_id`:** a re-run in which every in-scope Conclusion is locked produces only `proposal_withheld` revisions and no version change; the released content is identical, so the release survives. Any re-run that proposes new content for an in-scope unlocked Conclusion (impossible once all are eligible, since eligible = locked), any reopen or re-decision (version bump), any scope change, and any partial failure (blocker 3) invalidates it. **This closes P5-1 OQ2** without a cross-write from analysis or `decide` into `Assessment`.
- **`review_status` becomes a display-only denormalisation.** The release route is its only writer (`"approved"`). **No code reads it for a decision** (D-P5-2-H). A stale or legacy `"approved"` is harmless. It is kept because `tests/test_longitudinal_demo.py` (lines 471-473), `tests/test_performance_benchmarks.py` (line ~109) and the snapshot generated-event `review_status` key already record it.
- There is no "unrelease" route. Reopening any in-scope Conclusion is the way to withdraw (it stales the release immediately).

### D-P5-2-H. The release chokepoint is rewritten. Order and messages are exact.

`require_review_approval(assessment_id, db) -> Assessment` keeps its name, signature and every caller. New body, in this order:
1. `db.get(Assessment, …)` is `None` → 404 "Assessment not found" (unchanged).
2. No `GapReport` → **404 "No report found. Run analysis first."** (same text as `reports._get_report`; moved into the gate so the no-report case never reports "not approved").
3. Failed frameworks → **409** `RELEASE_BLOCKED_MESSAGE` (P5-1 D-P5-1-G). **Moved before the approval check**, so a failed framework is reported as such regardless of release state, as P5-1 scenario 7 already expects.
4. `not release_state(db, assessment).released` → **403** `NOT_RELEASED_MESSAGE = "Report not yet approved for release. Complete the review process first."` (text unchanged from today; defined in `approved_report.py`, used by `review_gate.py`).
5. Return the assessment.

Steps 2-4 use one `approved_report.build_approved_report(db, assessment)` call (failed frameworks = entries with `status == "failed"`; the message is formatted from registry names in selection order, as P5-1 does). `review_gate.py` no longer contains the tokens `review_status`, `GapReport` query code or `report_framework_scores`. Every caller listed in Current state keeps calling it. The P5-1 `allow_failed_draft` seam in `reports._download_pdf_response` is kept with its semantics: when a framework failed, draft rendering skips the gate; otherwise the gate applies.

**No code reads `review_status` for a decision.** Replace: `reports.get_comparable_assessments` and `web.report_summary`'s comparable query drop the SQL `review_status` filter and keep candidates `c` (same company, other id, `status == "completed"`, newest first) only where `approved_report.is_released(db, c)`; `web.report_summary` keeps its `.limit(5)` **after** that filter. `report_content.integrated_report` excludes with `NOT_RELEASED` iff `not is_released(db, assessment)`. `integrated_reports.issue_integrated_report` per D-P5-2-P. Templates per D-P5-2-N.

### D-P5-2-I. The legacy review is retired: routes answer 410, the page redirects

- `app/routers/review.py`: `disposition_item` (`PATCH /{assessment_id}/review/items/{item_id}`), `approve_assessment` (`POST /{assessment_id}/review/approve`) and `reject_assessment` (`POST /{assessment_id}/review/reject`) stay **registered with the same paths and methods** (so the archive guard and `test_retention`'s route inventory still cover them), but each body is only `raise HTTPException(410, LEGACY_REVIEW_RETIRED)` with `LEGACY_REVIEW_RETIRED = "Assessment-level review has been retired. Approve each conclusion individually on the Conclusions page, then release the report."` No request parsing, no DB access, no writes. Remove `_payload`, `_validated`, `_get_report`, `_toast` and `_templates` from `review.py` if nothing else uses them.
- `app/schemas/review.py` is **deleted** (only `review.py` imported it; verify with grep first, and stop if anything else does).
- `web.review_page` (`GET /assessments/{assessment_id}/review`) becomes `RedirectResponse(f"/assessments/{assessment_id}/conclusions", status_code=303)` after the 404 check. `app/templates/pages/review.html` and `app/templates/partials/review_filter_bar.html` are **deleted** (verify no other template includes `review_filter_bar`). `app/templates/partials/review_finding_card.html` **stays unchanged** (rendered by `test_needs_review_ui.py`; unreachable from the app; open question 6).
- **Why retire rather than keep read-only:** a read-only `GapItem` queue would present AI proposals next to the real decision surface with a different vocabulary (`accepted`/`rejected`) and invite the belief that it matters. The Conclusions page already shows each Conclusion's AI proposal, citations, the withheld proposal and `legacy_report_status`. The Workpaper already shows the full trace. There is nothing left for the queue to do. 410 (not 404) makes the retirement explicit to any automation still posting.
- `GapItem.review_status`, `reviewed_by`, `reviewed_at`, `reviewer_notes` are frozen: analysis still writes `review_status="draft"` on new rows (analysis.py unchanged); nothing else writes or reads them.

### D-P5-2-J. `GapReport` survives as the frozen AI-proposal record, not a cache

- The analyzer keeps writing `GapReport` + `GapItem` + `Initiative` exactly as today (analysis.py zero diff), including `legacy_history` on re-run and P5-1's sentinel in `framework_scores`.
- Release-path code reads the `GapReport` only for: its existence (blocker 1 / 404), the failed sentinel (via `report_framework_scores` + `failed_framework_ids`, inside `approved_report.py` only), `id` (release metadata, `RenderReport.id`) and `generated_at` ("analysed at"). Never for outcomes, numbers, text or initiatives.
- **Why not a thin cache of approved results:** a cache is a second, mutable copy of what the consultant decided. It would need invalidation on every `decide`, every re-run and every scope edit, and a missed invalidation is exactly a client seeing numbers nobody approved. Computing on read from append-only-revisioned, versioned Conclusions is deterministic and cheap (≤ ~230 Conclusions and their decision revisions per assessment). Immutability of what a client *received* is already guaranteed where PR-054 requires it: issued snapshot **bytes** (P3-2), plus the release manifest in the audit log that pins the exact `(id, version)` set. A cache would add a third copy with none of those guarantees.
- **Why not "frozen legacy history" only:** new analyses still need a run-level container for the failed sentinel (P5-1's contract lives in `framework_scores`), `raw_ai_response` and `legacy_history`. Keeping the writer unchanged also keeps P2-3/P5-1/P5-3 untouched.

### D-P5-2-K. Row shape, and what AI-only content is withheld from release

`ApprovedRow` (frozen dataclass), built for every **eligible in-scope** Conclusion, ordered by framework selection order then registry control order:

| Field | Value |
|---|---|
| `id`, `conclusion_id` | `Conclusion.id` (`id` exists for template anchors like `remediation-{{ item.id }}`) |
| `conclusion_version` | `Conclusion.version` |
| `framework_id`, `requirement_id` | from the Conclusion |
| `requirement_title` | registry `control.title` (fallback `requirement_id`) |
| `chapter` | `f"{framework_id}:{domain_key}"`, the same key as `chapter_scores` (the domain containing the control, from `as_legacy_framework_dict()`) |
| `chapter_title` | `f"{framework.name} — {domain title}"` (identical to `namespaced_domain_scores`' title) |
| `control_reference` | registry `control.reference` or `None` |
| `compliance_status` | `Conclusion.outcome` (**the five-value vocabulary; `insufficient_evidence` stays itself**) |
| `current_state` | `Conclusion.rationale` |
| `gap_description` | `Conclusion.gaps_identified` |
| `risk_level` | `Conclusion.risk_level` |
| `remediation_action` | `Conclusion.recommended_action` |
| `remediation_priority` | `PRIORITY_BY_RISK.get(risk_level, 3)` |
| `evidence_quote` | `Conclusion.evidence_summary or None` |
| `decision`, `decided_by`, `decided_at` | D-P5-2-B |
| `remediation_effort`, `timeline_weeks`, `maturity_level`, `root_cause_category`, `evidence_confidence` | always `None` |

**Withheld from every release surface because no consultant approved it:** remediation effort, timeline weeks, maturity level, root-cause category, evidence confidence (all AI or heuristic `GapItem` fields), `Initiative`s (AI root-cause clustering over unapproved statuses), and the AI executive summary. Priority is derived deterministically from the consultant-approved risk level, which is allowed (PR-045: a deterministic calculation over approved input).

**Deterministic summary text** (`ApprovedReport.summary_text`), replacing the AI executive summary on the report tab, in the API `executive_summary` field and in the PDF "Key Findings" block. First line exactly `"This summary is generated from consultant-approved conclusions only."`, then one line per selected framework, joined with `"\n"`:
- scored: `f"{name}: {score:.0f}% ({rating}), {scored} of {in_scope} in-scope requirements scored; {compliant} compliant, {partially_compliant} partially compliant, {non_compliant} non-compliant, {insufficient_evidence} insufficient evidence, {not_applicable} not applicable."`
- not_scored: `f"{name}: not scored; no in-scope requirement has a scoring outcome ({insufficient_evidence} insufficient evidence, {not_applicable} not applicable)."`
- pending_review: `f"{name}: review in progress; {eligible} of {in_scope} in-scope conclusions approved."`
- unavailable: `f"{name}: no conclusions recorded. Run analysis."`
- failed: `f"{name}: analysis failed. Not scored."`

The AI executive summary stays stored (`GapReport.executive_summary`, run envelopes) and is not shown anywhere in the report (open question 2 proposes a consultant-authored summary).

### D-P5-2-L. The report JSON API (`app/routers/reports.py`, `app/schemas/report.py`)

- `reports.py` builds everything from `approved = approved_report.build_approved_report(db, assessment)` after `require_review_approval`. It no longer imports `GapItem`, `Initiative`, `InitiativeOut`-building helpers it no longer needs, `report_framework_scores`, or `failed_framework_ids` except where the P5-1 `allow_failed_draft` seam needs them (move that check to `approved.release` / `approved.framework_scores` statuses: `any(e["status"] == "failed" for e in approved.framework_scores.values())`).
- `GapItemOut`: `remediation_effort: str | None = None`, `timeline_weeks: int | None = None` (were required); new optional `framework_id: str | None = None`, `conclusion_id: str | None = None`, `conclusion_version: int | None = None`. `_item_to_schema` maps an `ApprovedRow`.
- `get_report` (X1): `id=gap_report.id`, `framework_scores=approved.framework_scores`, `chapter_scores=approved.chapter_scores`, `executive_summary=approved.summary_text`, `gap_items` = rows, `remediation_roadmap` = rows whose `compliance_status != "compliant"` bucketed by `remediation_priority` exactly as today (so `not_applicable` and `insufficient_evidence` rows land in buckets as today's non-compliant-filter would), `initiatives=[]`, `generated_at=gap_report.generated_at`.
- `get_report_summary` (X2): counts over rows; `ReportSummary` gains `insufficient_evidence: int = 0` and `not_applicable: int = 0`; `not_assessed` is kept and **equals the `insufficient_evidence` count** (documented alias, one release). `requirement_counts`/`total_requirements` unchanged (P5-1 D-P5-1-I). `critical_gaps`/`high_gaps` over rows with gap outcomes `non_compliant`/`partially_compliant` as today.
- `get_full_report` (X3): `frameworks[fw]["scores"]` = approved entries; `gap_items_by_framework` from rows (same keys; the withheld fields are `null`); `initiatives: []`; `executive_summary` = summary text.
- No new top-level `overall_score`/`overall_rating` (guard).

### D-P5-2-M. The PDF: same renderer, approved input, additive copy only

- **`generate_pdf`'s signature is unchanged** (pinned). `_download_pdf_response` passes `report=approved.render_report()`, `gap_items=approved.rows`, `initiatives=None`, and the existing `answer_source_map`, `selected_frameworks`, `assessment`, `report_findings`. `RenderReport` is a frozen dataclass with exactly `id`, `assessment_id`, `chapter_scores` (JSON string of `approved.chapter_scores`), `framework_scores` (JSON string of `approved.framework_scores`), `executive_summary` (`approved.summary_text`), `generated_at`. `pdf_export` keeps reading `report.chapter_scores`, `report_framework_scores(report, …)` and `report.executive_summary`, so it renders the approved view without knowing its source. Direct callers passing a real `GapReport` (tests) keep working.
- `pdf_export.py` must not import `GapItem`/`GapReport` anymore: replace the type hints `list[GapItem]`/`GapReport` with unannotated or `list`/`object` hints. It must not access the DB. It may now mention Conclusions in comments (D-P5-2-R).
- **Additive edits, exact** (all strings through `S()`):
  1. `STATUS_COLORS` gains `"insufficient_evidence": (155, 89, 182)`. `_draw_status_bar`'s `order` appends `"insufficient_evidence"` with label `"Insufficient evidence"`.
  2. `_draw_timeline_block`: draw the effort/timeline tag only when `item.remediation_effort and item.timeline_weeks`.
  3. Cover summary: when `max_weeks` is 0, the text is `f"{total} requirements assessed  |  {critical_count + high_count} gaps identified"` (no "~0 weeks"). Otherwise unchanged.
  4. KPI card 3: when `max_weeks` is 0, value `"n/a"`, label `"Remediation Timeline (not estimated)"`. Otherwise unchanged.
  5. Coverage lines on the Executive Dashboard, after the failed-framework lines (P5-1 R12) and before "Compliance Distribution": for each framework whose entry has a `coverage` dict and `status == "scored"`: `S(f"{name}: {scored} of {in_scope} in-scope requirements scored; {insufficient_evidence} insufficient evidence (excluded from the score, not counted as non-compliant); {not_applicable} not applicable.")`; for `status == "not_scored"`: `S(f"{name}: not scored. No in-scope requirement has a scoring outcome.")`. 9pt, `MID_TEXT`, advancing `framework_bar_y` by 7 each. Entries without `coverage` (a real `GapReport`) draw nothing.
  6. Methodology: insert a **"Scoring Basis"** paragraph immediately after the "Scoring Formula" paragraph (before `{chapter_weights_block}`), exact text:
     `"Scoring Basis:\nScores are computed only from conclusions a consultant has individually approved. Each approved outcome counts as follows: Compliant 100 points, Partially Compliant 50 points, Non-Compliant 0 points. Not Applicable and Insufficient Evidence are excluded from the scoring denominator. Insufficient Evidence is not treated as Non-Compliant; the number of requirements with insufficient evidence is reported next to each framework score. Requirements excluded at scoping are not scored. A framework is scored only when every in-scope requirement has an approved conclusion.\n\n"`
- **A7 conditional copy** (existing DPDPA-only text stays byte-identical; new variants apply only when not DPDPA-only):
  - "What Is Not Covered": `dpdpa_only` → unchanged. Otherwise: `"This assessment does not include technical penetration testing, source code review, network security assessment, or any form of independent technical verification. Where the selected framework(s) include physical or environmental controls, findings on those controls are based on disclosed information and submitted documents, not an on-site inspection. Findings in areas where the organization provided limited or no evidence are based on stated intent and disclosed posture only."`
  - "Recommended Follow-On Actions": `dpdpa_only` → unchanged. `has_dpdpa` and not `dpdpa_only` → `f"For requirements rated as Non-Compliant or Partially Compliant at a Critical or High risk level, independent verification by qualified legal counsel or a certified privacy professional (for DPDPA requirements), or by a qualified information security auditor (for {other_names}), is strongly recommended before relying on those findings for regulatory submissions, board reporting, or contractual representations."` where `other_names` = the non-DPDPA framework names joined with ", ". No DPDPA → `"For requirements rated as Non-Compliant or Partially Compliant at a Critical or High risk level, independent verification by a qualified information security auditor is strongly recommended before relying on those findings for certification, board reporting, or contractual representations."`
  - Non-DPDPA "Framework Overview" first sentence: `"Requirements are drawn directly from the source standard for each selected framework ({frameworks_label})."` → `"Requirements are referenced by clause or control identifier for each selected framework ({frameworks_label}); requirement descriptions are summarised for assessment purposes and do not reproduce the source standard."` The rest of that paragraph is unchanged.
  - These replace a sentence only on the non-DPDPA branch; no page, heading, section or layout changes. That is the additive-only rule's intent (no rewrite of existing pages), and the plan's instruction for A7 ("conditional copy, not rewrites").
- The Strategic Initiatives section simply does not render (it is already `if initiatives:`). The "Approved Findings" section (P3-3) is unchanged.

### D-P5-2-N. The web surfaces

- **`_framework_display(assessment, framework_scores)`**: add `"status": scores.get("status", "scored")` and `"coverage": scores.get("coverage")` to each entry; everything else unchanged. Callers pass `approved.framework_scores`: `assessment_detail` (when a `GapReport` exists and `tab in ("report", "questionnaire")`), `analysis_status` (both branches), `report_summary`.
- **`partials/analysis_complete.html`**: branch order `failed` → `status == "pending_review"` → `score is not none` → else. New branch text `awaiting consultant review`. Add one link after "View Report": `<a href="/assessments/{{ assessment_id }}/conclusions" data-review-conclusions-link …>Review conclusions</a>`.
- **`web.report_summary`** (X9): keep the no-`GapReport` → `partials/no_report.html` branch. Otherwise build `approved`, then pass: `report` (the `GapReport`, unchanged key so the template's other uses keep working), `gap_items = approved.rows`, `chapter_scores = approved.chapter_scores`, `status_counts` from rows, `chapter_status_counts`, `business_impact`, `root_cause_counts` (always `{}` now), `critical_findings` (same filter/sort, on rows), `quick_wins = []` and `quick_wins_available = False`, `summary_text`, `release` (`approved.release`), `release_status` (`"released"`/`"stale"`/`"not_released"`), `gap_items_by_chapter` keyed by **`row.chapter_title`** in row order, `legacy_remediation` = `{(item.framework_id or "dpdpa", item.requirement_id): item}` for the `GapReport`'s `GapItem`s whose P3-4 legacy remediation fields are set (the one allowed `GapItem` read on this page: historical consultant-entered remediation, not an AI outcome), plus the existing keys. Drop `reviewed_by`/`reviewed_at`/`review_status`.
- **`partials/report_summary.html`**, exact changes:
  1. Replace the `review-banner` block (lines 1-17) with `<div id="review-banner" data-release-state="{{ release_status }}">`: `released` → green "Released" + `by {{ release.released_by }} · {{ release.released_at.strftime('%d %b %Y') }}`; `stale` → amber "The released version is out of date: an in-scope conclusion or the scope changed after release. Release again to reopen exports." + link "Open conclusions →" to `/assessments/{{ assessment_id }}/conclusions`; `not_released` → amber "Not released: exports stay closed until every in-scope conclusion is individually approved and the report is released." + `<ul data-release-blockers>` with one `<li>` per blocker + the same link. No apostrophes in new text.
  2. Keep P5-1's `data-analysis-incomplete-banner` block unchanged.
  3. Gauge loop: `failed` (unchanged) → **new** `{% elif fw_data.status == "pending_review" %}` card `<div data-framework-pending="{{ fw_id }}">` with the name, "Awaiting consultant review", `{{ fw_data.coverage.eligible }} of {{ fw_data.coverage.in_scope }} conclusions approved` → **new** `{% elif fw_data.status == "not_scored" %}` card `data-framework-not-scored` with "Not scored" and "No in-scope requirement has a scoring outcome" → existing `score is not none` gauge, **plus** below the SVG `<p data-framework-coverage="{{ fw_id }}">{{ c.scored }} of {{ c.in_scope }} scored · {{ c.insufficient_evidence }} insufficient evidence · {{ c.not_applicable }} not applicable</p>` when `fw_data.coverage` → existing `else` "Scores unavailable / Re-run analysis" card, **unchanged text** (it now means `unavailable`; `test_no_blended_scoring` asserts it).
  4. Requirements card: add a line "Insufficient evidence" with `status_counts.get("insufficient_evidence", 0)` after "Non-Compliant".
  5. Section C: `{% if report.executive_summary %}` → `{% if summary_text %}` and the body `{{ report.executive_summary }}` → `{{ summary_text }}`. Heading unchanged.
  6. Chapter bars: `na_pct` adds `ch_counts.get("insufficient_evidence", 0)`.
  7. Quick Wins empty state: `{% if quick_wins_available is defined and not quick_wins_available %}` → "Effort is not estimated in approved conclusions, so quick wins are not shown." else the existing text.
  8. Detailed Findings grouped view: `{{ chapter_key | replace("_", " ") | title }}` → `{{ chapter_key }}`; wrap the remediation include as `{% set legacy = legacy_remediation.get((item.framework_id, item.requirement_id)) %}{% if legacy %}{% with item = legacy %}{% include "partials/remediation_panel.html" ignore missing %}{% endwith %}{% endif %}` inside the existing `remediation-{{ item.id }}` div.
  9. Keep `Live PDF`, `/snapshots"`, "Report versions", "Workpaper", RFI links and the RFI section unchanged.
- **Conclusions page** (`web.conclusions_page`): pass `release = approved_report.release_state(db, assessment)`. New partial **`partials/release_panel.html`**, included in `pages/conclusions.html` directly after the counts grid: `<section data-release-panel data-release-state="…">`. When `release.released`: "Released by … on …". Else, when blockers: heading "Not ready to release" and `<ul data-release-blockers>`. Else (releasable, or stale and releasable): `<form data-release-form hx-post="/api/assessments/{{ assessment.id }}/release" hx-include="#reviewer-name" hx-swap="none" hx-confirm="Release this report? Exports will use the approved conclusions exactly as they are now.">` with the button "Release report". Autoescaped, no `|safe`, no apostrophes.
- **`pages/report_snapshots.html`** line 35: the note condition becomes `{% if type == 'gap_report' and not release.released %}` and the text "Generating a gap report requires the report to be released." `web.snapshots_page` passes `release`.
- **`web.framework_tab`** and `assessment_detail`'s `active_framework_finding_count`: count rows of `approved.rows` with that `framework_id` and `compliance_status in conclusion_review.GAP_OUTCOMES` (0 when there is no `GapReport`). `assessment_detail` stops loading `GapItem`s and drops the `gap_items` context key (first `grep -rn "gap_items" app/templates`; if any template in `pages/assessment.html`'s include tree reads it, stop and report).
- **`web.comparison_page`**: see D-P5-2-P.

### D-P5-2-O. Snapshot continuity

- **`source_manifest` is unchanged** (same keys, same content). Every existing snapshot's `source_changed` comparison stays meaningful, and `MANIFEST_SCHEMA_VERSION` stays 1.
- **Generation:** gap-report drafts keep going through `reports._download_pdf_response(..., allow_failed_draft=True)`, so they now render the approved view and require `released` (or a failed framework, P5-1 seam). Workpaper generation stays ungated.
- **Issue** (both types): in `snapshots.issue_snapshot_route`, after `require_review_approval` (released now), refuse with **409** `SNAPSHOT_STALE_MESSAGE = "This version was generated before the current release. Generate a new version, then issue it."` unless the snapshot's `report_snapshot.generated` event is **newer** than the assessment's latest `assessment.released` event (compare `audit_events.rowid`). Implement as `report_snapshots.generated_after(db, snapshot_id, event_id) -> bool` (read-only helper; no `delete`). Rationale: `released now` + `generated after the release event` means nothing in the manifest changed between release and render (versions only increase), so the bytes are bound to the exact released Conclusion set (PR-054). The only uncaught case is a scope edit that is reverted between release and a workpaper render; that is accepted and named (open question 4).
- **Issued bytes never change.** Reopening, re-deciding, re-running or re-releasing never touches an issued file or its `is_issued` (scenario 14 proves byte identity across all four).

### D-P5-2-P. Integrated report and comparison

- `report_content.integrated_report`: exclusion order `not is_released` → `NOT_RELEASED` (checked first, as today), no `GapReport` → `NO_REPORT`, failed → `ANALYSIS_INCOMPLETE` (P5-1; unreachable for a released assessment but kept). Score lines come from `build_approved_report(...).framework_scores` entries with `status == "scored"`. `report_content.py` gains no write token (guard). `source["assessments"]` stays `{"assessment_id", **source_manifest}`.
- `integrated_reports.issue_integrated_report`: for each source assessment, refuse with the existing 403 `INTEGRATED_NOT_RELEASABLE` unless it is `is_released` **and** the integrated snapshot's generated event is newer than that assessment's latest `assessment.released` event.
- Comparison (X6/X7): both assessments pass `require_review_approval`; `compute_delta(current.rows, previous.rows)`; framework deltas use approved entries' `overall_score` only when `status == "scored"`, else `None` (renders "—"). `status == "completed"` checks stay. Comparable lists use `is_released` (D-P5-2-H).

### D-P5-2-Q. The legacy-data path (three cases, all fail closed)

1. **Pre-P2-3, never migrated** (a `GapReport` + `GapItem`s, zero Conclusions, maybe `review_status == "approved"` from the old bulk route): every framework is `unavailable`, blocker 4 fires for every framework, every export returns 403, the report tab shows "Scores unavailable / Re-run analysis" and the not-released banner. **Path back:** run analysis (creates Conclusions), approve individually, release. Already-issued snapshots stay downloadable, byte-identical.
2. **Migrated by `scripts/migrate_legacy.py`** (Conclusions whose proposal revision has `citations_json = NULL`, and `approved` revisions whose actor is the old `reviewed_by`, not `consultant:`): the legacy approvals are **not eligible** (D-P5-2-B), so blocker 5 fires. **Path back:** reopen each legacy-approved Conclusion (allowed from `approved`), re-run analysis (the reopened and pending ones get a fresh `proposed` revision with captured citations; locked ones stay withheld), approve individually, release. Until the re-run, `EVIDENCE_NOT_CAPTURED` blocks approval, as P2-4 designed.
3. **Post-P2-3 but released through the retired bulk route** (Conclusions pending, `review_status == "approved"`): not released. Path back: approve individually, release.

No data migration, no notification, no schema change. Legacy `review_status` values are inert. The behaviour change for existing assessments is the point of the task (plan risk table: "P5-2 changes client-visible numbers for existing assessments … Issued snapshots are immutable, so past deliverables don't change").

### D-P5-2-R. The Conclusion-mention guard is retired and inverted. The blended-score guard is untouched.

- **Retired:** `tests/test_analysis_pipeline.py::test_legacy_consumers_do_not_read_the_new_tables`, the regex assertion at `tests/test_pdf_updates.py` line 1044, and the four-file loop at `tests/test_correctness_bundle.py` lines 811-818. They encoded D-P2-3-A ("legacy consumers keep reading GapItem until the reader migration"). This task **is** the reader migration, so the rule now points the other way.
- **Replacement (same test functions, bodies rewritten; rename the first to `test_release_readers_do_not_read_ai_outcomes`):**
  - `grep -nE "\bGapItem\b" app/routers/reports.py app/utils/pdf_export.py app/utils/review_gate.py app/services/report_content.py app/services/approved_report.py app/routers/integrated_reports.py` → empty.
  - `grep -nE "\bInitiative\b|report_framework_scores|chapter_scores\)|\.executive_summary" app/routers/reports.py app/utils/review_gate.py app/services/report_content.py` → empty (`approved_report.py` is the only release-path file allowed to call `report_framework_scores`, for the sentinel).
  - `grep -rnE "review_status\s*(==|!=)" app/` → only `app/templates/partials/review_finding_card.html` (the frozen `GapItem` card).
  - `grep -n "llm_client\|\.commit(\|delete" app/services/approved_report.py` → empty.
  - `app/services/scoring.py` imports none of `app.models.conclusion`, `app.services.analysis_pipeline`, `app.services.approved_report` (AST import check).
  - `inspect.getsource` of `web.report_summary`, `web.comparison_page`, `web.analysis_status`, `web.framework_tab` contains neither `GapItem` nor `report_framework_scores`, except `web.report_summary` may contain `GapItem` exactly for the `legacy_remediation` lookup (assert the substring `legacy_remediation` is in the source whenever `GapItem` is).
  - `test_correctness_bundle` scenario 10 keeps every other assertion (analysis.py `overall_score` rule, `analysis_pipeline` no `delete`, `report_content` write tokens, templates, `analysis_gate_blocked.html`, alembic head, `_run_multi_framework_analysis` signature).
- **`tests/test_no_blended_scoring.py::test_no_template_reads_retired_score` stays byte-identical and green.** No new `.overall_score` attribute access and no `overall_score=` keyword anywhere outside its allow-list.

### D-P5-2-S. Existing tests and scripts: the only permitted changes

An existing test may be changed **only** if it fails for one of these reasons, and **only** in the stated way. Every changed test function is listed in Results with its reason code.

- **(a) Hand-set release.** It sets `x.review_status = "approved"` (or `"pending"` to un-release) to open a release path. Replace with the release helper below (or, to un-release, reopen one in-scope Conclusion through `conclusion_review.decide(..., action="reopened", …)`). Keep every other assertion.
- **(b) Hand-built report served on a release surface or the report tab.** It builds a `GapReport`/`GapItem` by hand and expects release-path output. Replace the setup with real Conclusions (through the file's existing pipeline stubs and `gate.trigger_analysis`, or `decide`) plus the helper, restricting `applicable_requirements` where the test only cares about a few requirements. **Assertions about shapes, guards, counts or text stay;** numeric literals may change only to the approved-derived value, and the Results entry must show old → new.
- **(c) Retired legacy route.** It calls `review/items`, `review/approve` or `review/reject` expecting success. Change the expectation to 410 with `LEGACY_REVIEW_RETIRED` and keep its "no cross-writes" assertions.
- **(d) Retired guard** (D-P5-2-R).
- **(e) Stale draft.** It issues a draft generated before the current release and expects 200. Generate a fresh draft after the release and issue that; additionally assert the old draft now gets 409 `SNAPSHOT_STALE_MESSAGE` (or 403 `INTEGRATED_NOT_RELEASABLE` for integrated).

Release helper (copy it into each test module that needs it; do not create a shared module):
```python
def _approve_all_and_release(db, assessment, reviewer="Priya"):
    actor = conclusion_review.reviewer_actor(reviewer)
    for row in db.query(Conclusion).filter_by(assessment_id=assessment.id).order_by(Conclusion.id).all():
        card = conclusion_review.conclusion_card(db, assessment_id=assessment.id, conclusion_id=row.id)
        if card.state in ("approved", "edited") and not card.legacy_bulk_approval:
            continue
        if card.state in ("approved", "edited"):
            conclusion_review.decide(db, assessment_id=assessment.id, conclusion_id=row.id,
                                     action="reopened", expected_version=row.version, actor=actor)
            db.refresh(row)
        conclusion_review.decide(db, assessment_id=assessment.id, conclusion_id=row.id,
                                 action="approved", expected_version=row.version, actor=actor)
    approved_report.record_release(db, assessment, actor=actor)
    db.commit()
```

Known affected tests (from reading; the list may be incomplete, and anything outside (a)-(e) is a stop-and-report):
- `test_analysis_pipeline.py::test_legacy_consumers_do_not_read_the_new_tables` (d).
- `test_pdf_updates.py`: scenario 10 line 1044 (d); `_run_one` line 420, `_setup_integrated` lines 511/544/556 and `_set_scores` expectations, scenarios 1 (614), 2 (648), 6 (878/887 → reopen + re-approve + re-release, then (e)), 7 (926), 11 (1067) (a/b/e).
- `test_report_snapshots.py`: `_run_one` (221), scenario 4 (402), scenario 6 (460/465: the workpaper drafted before release → (e)), line 552 (a/e).
- `test_correctness_bundle.py`: scenario 7's final `/report/summary == 200` after re-run (a); scenario 8 `test_requirement_counts_are_registry_driven` (b; one in-scope requirement per framework is enough); scenario 9's report-summary ₹ cases (b; an approved `CH2.SECURITY.1` non-compliant Conclusion instead of a `GapItem`); scenario 10 lines 811-818 (d).
- `test_no_blended_scoring.py`: `test_comparison_renders_framework_deltas_and_missing_scores` and `test_report_api_has_only_framework_score_shapes` (b). `test_pdf_has_one_score_section_per_framework_and_no_total` and `test_legacy_reader_falls_back_only_for_single_framework` should pass unchanged.
- `test_conclusion_approval.py::test_scenario_13_legacy_path_and_status_are_untouched` lines 713-722 (c).
- `test_performance_benchmarks.py` line ~100 (`== 1083` a0 revision count) and `scripts/benchmark_performance.py::seed_benchmark_dataset`: replace `a0.review_status = "approved"` (line 718) with approving every non-eligible a0 Conclusion (pending and rejected ones, via `decide`, **after** the existing findings loop so finding counts don't move) and `record_release`. Update only the a0 revision literal; report old → new. `PLAN_COUNTS` is unchanged (fillers absorb the difference). If any a0 Conclusion cannot be approved (`_approval_blocker`), stop and report.
- `scripts/seed_test_companies.py` (the longitudinal demo): (1) before each `_analyze`, set that assessment's `applicable_requirements` to `json.dumps(sorted(every requirement id in ITEMS[assessment_key] across its frameworks))` through the seed's existing DB session, so the synthetic assessments are honestly scoped to the requirements they script (their fake analyzer returns only those); (2) `_release_assessment` becomes one `http.post(f"/api/assessments/{assessment_id}/release", data={"reviewer_name": DEMO_REVIEWER})` expecting 200. `tests/test_longitudinal_demo.py` itself must pass **unmodified** (Conclusion count 12, `review_status` assertions at 471-473, integrated sources).
- Expected to pass unchanged (report if not): `test_remediation_tracking.py` scenario 9, `test_workpaper.py`, `test_picker_and_scoring_contract.py::test_report_view_mode_defaults_and_validation`, `test_golden_dpdpa.py`, `test_white_label.py`, `test_retention.py` (the new `POST /release` is exercised by its archive loop automatically), `test_needs_review_ui.py`, `test_migrate_legacy.py`, `test_p5_3_framework_desk_review.py`, `test_p5_5_scoping_evidence.py`.

### D-P5-2-T. Coordination and what this task does not touch

- **P5-3's pre-declared rule (D-P5-3-P) is honoured:** `app/routers/analysis.py` has **zero diff** (so the `trigger_analysis` desk-review block stays P5-3's one-line `load_desk_review_data`, and no `DeskReviewFinding` query is reintroduced anywhere). In `web.py` this task does not touch `desk_review_status_web` or `generate_rfi_web`. No Alembic revision; the head stays `8b2d5f7e1c34`.
- **P5-4 (may run in parallel):** it owns `question_engine.py`, the questionnaire routes/templates and `assessment_detail`'s questionnaire-tab data. This task's `assessment_detail` edits are limited to `framework_display`, `gap_items` removal and `active_framework_finding_count`. If P5-4 lands first, rebase and keep both sides.
- **P5-6 (blocked by this):** the RFI (`generate_rfi_web`, `rfi_generator`, `RFIDocument`, `rfi_export`) is untouched except that its downloads now pass the new gate. P5-6 must source from `build_approved_report(...).rows` and gate on `release_state`.
- **Not touched:** `analysis.py`, `analysis_pipeline.py`, `conclusion_review.py`, `findings.py`, `workpaper.py`, `desk_review*.py`, `claude_analyzer.py`, prompts, `question_engine.py`, `scope_profiler.py`, `auto_answer.py`, `app/models/*`, `alembic/*`, `scoring.compute_framework_scores`, `scoring.score`, `report_snapshots.source_manifest`/`issue_snapshot`/`ISSUE_SQL`.

### D-P5-2-U. Consistency audit against the standing guards

1. `analysis.py`: zero diff. `analysis_pipeline.py`: zero diff (no `delete`).
2. `report_content.py`: no `db.add(`, `db.add_all(`, `db.merge(`, `.flush(`, `.commit(`, `delete`.
3. Templates: no `overall_score`, `CyberAssess`, `|safe`; `report_summary.html` keeps `/snapshots"` and `Live PDF` and gains no `Download PDF`/`PDF Report`; new text has no apostrophes.
4. The AST `overall_score` guard: no new attribute access or keyword outside the allow-list (dict keys only).
5. No `relationship(` in `app/models/`.
6. `generate_pdf` parameter list unchanged; every new PDF string through `S()`.
7. The new `POST /release` sits on the archive-guarded review router; no route is added to `main.py`.
8. `RELEASE_BLOCKED_MESSAGE`, `failed_framework_scores`, `is_failed_framework_score`, `failed_framework_ids`, `UNCONFIRMED_ANSWER_SOURCES`, `confirmed_response_clause` unchanged in value and importable from their P5-1 modules.

## Required approach

1. **Step 0** checks.
2. `app/services/scoring.py`: `APPROVED_OUTCOME_POINTS`, `DENOMINATOR_EXCLUDED_OUTCOMES`, `approved_framework_scores` (D-P5-2-D).
3. `app/services/approved_report.py` (new): constants and messages (D-P5-2-A/F/G/H/O), `in_scope_requirement_ids`, eligibility loading, `ApprovedRow`/`FrameworkReview`/`ReleaseState`/`ApprovedReport`/`RenderReport`, `build_approved_report`, `release_state`, `is_released`, `latest_release_event`, `record_release`, `ReleaseRefused`, `summary_text`.
4. `app/utils/review_gate.py`: re-export `RELEASE_BLOCKED_MESSAGE`; rewrite `require_review_approval` (D-P5-2-H).
5. `app/schemas/report.py`: `FrameworkScoreOut`, `GapItemOut`, `ReportSummary` (D-P5-2-E/L).
6. `app/routers/reports.py` (D-P5-2-L, P): all four report endpoints, `_download_pdf_response`, comparable and compare.
7. `app/utils/pdf_export.py` (D-P5-2-M): type hints, the six additive edits, the A7 copy.
8. `app/routers/review.py`: 410 stubs, `POST /release` (D-P5-2-G/I). Delete `app/schemas/review.py`.
9. `app/services/report_snapshots.py`: `generated_after` only. `app/routers/snapshots.py`: the stale check (D-P5-2-O).
10. `app/services/report_content.py`, `app/routers/integrated_reports.py` (D-P5-2-P).
11. `app/routers/web.py`: `_framework_display`, `framework_tab`, `assessment_detail`, `analysis_status`, `report_summary`, `review_page`, `conclusions_page`, `snapshots_page`, `comparison_page` (D-P5-2-N/P).
12. Templates: `partials/report_summary.html`, `partials/analysis_complete.html`, `partials/release_panel.html` (new), `pages/conclusions.html`, `pages/report_snapshots.html`; delete `pages/review.html`, `partials/review_filter_bar.html`.
13. `scripts/seed_test_companies.py`, `scripts/benchmark_performance.py` (D-P5-2-S).
14. Existing tests under D-P5-2-S, then `tests/test_p5_2_reader_migration.py` (new). Copy (don't import) the fixture pattern from `tests/test_pdf_updates.py` (`db_path`/`engine`/`db` on an Alembic-built, FK-enforcing SQLite, `http` with `app.dependency_overrides[get_db]`, `upload_root`, `gate`, `_seed`, `_item`, `_stub_single`, `_stub_multi`, `_add_evidence`, `_cite_revision`, `_pdf_text`). Use the real `generate_pdf` (pdfplumber) where text is asserted. No test may touch `data/dpdpa.db`, the real `uploads/` or the network.
15. `tasks/todo.md`: tick P5-2 in the existing Phase 5 style with a link to this handoff's Results. Don't edit the phase summary line.

## Key files

| File | Why |
|---|---|
| `app/services/approved_report.py` (new) | The approved view, eligibility, scope, release state, release record (D-P5-2-A…H, K) |
| `app/services/scoring.py` | `approved_framework_scores` (D-P5-2-D) |
| `app/utils/review_gate.py` | The chokepoint (D-P5-2-H) |
| `app/routers/review.py`; `app/schemas/review.py` (deleted) | 410 stubs, `POST /release` (D-P5-2-G/I) |
| `app/routers/reports.py`, `app/schemas/report.py` | Report API (D-P5-2-L) |
| `app/utils/pdf_export.py` | Additive PDF edits, A7 (D-P5-2-M) |
| `app/services/report_snapshots.py` (`generated_after` only), `app/routers/snapshots.py` | Issue binding (D-P5-2-O) |
| `app/services/report_content.py`, `app/routers/integrated_reports.py` | Integrated report (D-P5-2-P) |
| `app/routers/web.py` | Report tab, poll, detail, framework tab, conclusions page, snapshots page, comparison, review redirect |
| `app/templates/partials/report_summary.html`, `analysis_complete.html`, `release_panel.html` (new); `pages/conclusions.html`, `report_snapshots.html`; `pages/review.html`, `partials/review_filter_bar.html` (deleted) | UI |
| `scripts/seed_test_companies.py`, `scripts/benchmark_performance.py` | D-P5-2-S only |
| `tests/test_p5_2_reader_migration.py` (new) | The contract |
| Existing tests named in D-P5-2-S | Only the permitted changes |
| `app/routers/analysis.py`, `app/services/analysis_pipeline.py`, `conclusion_review.py`, `findings.py`, `workpaper.py`, `desk_review*.py`, `app/models/*`, `alembic/*`, RFI code, `partials/review_finding_card.html` | **Not modified** |

## Non-goals

- No schema change and no Alembic revision (release lives in `audit_events`, D2).
- No consultant-authored executive summary, no manual Conclusion creation, no coverage threshold (open questions 1-3).
- No RFI change beyond its gate (P5-6).
- No change to how analysis writes `GapReport`/`GapItem`/`Initiative`, and no removal of those tables.
- No change to the Conclusion decision workflow, its routes or `ALLOWED_ACTIONS`.
- No "unrelease" route (reopen stales a release).
- No change to `scoring.score()` (open question 5) or to the `per_framework_scores` numbers in the analyze API response (open question 7).
- No fix for the `test_scenario_9` ordering flake.

## Test scenarios

All in `tests/test_p5_2_reader_migration.py`. Each test's docstring starts with `Scenario N:`.

1. **Scoring contract (pure).** `approved_framework_scores` on DPDPA: (a) all compliant → 100.0 `scored`; (b) adding one `insufficient_evidence` requirement leaves `overall_score` and every domain score unchanged, while adding one `non_compliant` lowers it; (c) `not_applicable` likewise unchanged; (d) only `not_applicable`/`insufficient_evidence` → exactly `{"status": "not_scored", "overall_score": None, "overall_rating": None, "domain_scores": {}}` (never 0.0); (e) an unknown outcome → `ValueError`; (f) for a random-but-seeded mix, the result minus `status` equals `compute_framework_scores` fed the same ids with `insufficient_evidence` mapped to `not_assessed`. `inspect.getsource(scoring)` imports none of the three forbidden modules.
2. **Unchanged approval reproduces the proposal's numbers.** Single DPDPA and multi DPDPA + ISO pipeline runs (stubs), approve every Conclusion unchanged, release: for each framework, the approved entry minus `status`/`coverage` equals `json.loads(GapReport.framework_scores)[fw]`, and `approved.chapter_scores == json.loads(GapReport.chapter_scores)`.
3. **Eligibility and parity.** On one assessment create: pending, approved (consultant), edited (consultant), rejected, approved-then-reopened, and a legacy-bulk approved revision (actor `"Legacy Reviewer"`, written directly as a `ConclusionRevision`). Only the consultant approved/edited are rows. For every Conclusion, `eligible == (card.state in ("approved", "edited") and not card.legacy_bulk_approval)` against `conclusion_review.conclusion_cards`. Rows carry `decision`, `decided_by` (no prefix), `decided_at`.
4. **Scope and missing proposals.** `in_scope_requirement_ids` parity with `workpaper._scope` on the seven inputs listed in D-P5-2-C. With `applicable_requirements` = 3 DPDPA ids and a stubbed analyzer that returns 2 of them plus 2 out-of-scope ids: rows hold only in-scope eligible ones; out-of-scope Conclusions are never rows or scored and `coverage["out_of_scope"] == 2`; `missing_ids` equals `build_workpaper`'s `unconcluded` ids for DPDPA; blocker 4 text is exact.
5. **Blockers, order and messages.** Separate assessments for: no report (only blocker 1); `status == "analyzing"`; a failed ISO on DPDPA + ISO with DPDPA pending (blockers exactly `[RELEASE_BLOCKED_MESSAGE…, AWAITING…DPDPA]` in that order, no ISO missing/awaiting); awaiting counts `"{n} of {total}"`; `applicable_requirements` excluding every control → only blocker 6. `insufficient_evidence` and `not_applicable` approved outcomes do not block.
6. **Release route.** Not releasable → 409 JSON with `detail` = the joined blockers and `blockers` list, toast header, **no** `assessment.released` event, `review_status` unchanged. Releasable → 200, `HX-Redirect` to `?tab=report`, exactly one event: actor `consultant:Priya`, `entity_type "assessment"`, metadata key set exactly `{"schema_version", "manifest", "gap_report_id", "coverage"}`, `manifest` key set exactly `{"framework_ids", "in_scope", "conclusion_versions"}` and equal to the D-P5-2-G formula; `review_status == "approved"`. A second POST → 409 `ALREADY_RELEASED_MESSAGE`, no second event.
7. **Release invalidation and P5-1 OQ2.** After release: (a) reopen one in-scope Conclusion → `stale`, every gate 403; re-approve → still `stale` until a new release; (b) change `applicable_requirements` → `stale`; (c) re-run analysis with every in-scope Conclusion locked (withheld proposals only) → still `released`, the gate passes; (d) re-run with ISO failing → 409 `RELEASE_BLOCKED_MESSAGE`; (e) changing an **out-of-scope** Conclusion (re-run proposal) does not stale the release.
8. **Hand-set approval releases nothing.** `review_status = "approved"` with pending Conclusions → 403 `NOT_RELEASED_MESSAGE` on `GET /report`, `/report/summary`, `/report/full`, `/report/pdf`, `/compare/{other}`, the web comparison page, `/rfi/pdf`, `/rfi/docx`, gap-report snapshot generation, snapshot issue. Gate order: unknown assessment 404; no report 404 "No report found. Run analysis first."; failed 409; then 403. `review_gate.RELEASE_BLOCKED_MESSAGE is approved_report.RELEASE_BLOCKED_MESSAGE` and its text equals P5-1's.
9. **The API reflects the consultant, not the AI.** AI proposes `CH2.SECURITY.1` `non_compliant`/critical with gap "AI gap"; the consultant edits it to `partially_compliant`/medium with gap "Consultant gap"; release. `/report` has that row with `compliance_status "partially_compliant"`, `gap_description "Consultant gap"`, `risk_level "medium"`, `remediation_priority 3`, `remediation_effort None`, `conclusion_version` = the Conclusion's; the DPDPA score equals `approved_framework_scores` of the approved outcomes and differs from `GapReport.framework_scores`; the `GapItem` still says `non_compliant` (unchanged); `initiatives == []`; `executive_summary` starts with the D-P5-2-K first line and contains no text from the stub's AI summary. `/report/summary` counts include `insufficient_evidence`, `not_applicable` and `not_assessed == insufficient_evidence`. `/report/full` groups the rows; no top-level `overall_score`.
10. **The PDF.** For the scenario-9 assessment, `GET /report/pdf` text (pdfplumber) contains "Consultant gap", not "AI gap"; contains "Scoring Basis:"; contains the coverage line; contains no "~0 weeks"; contains "Remediation Timeline (not estimated)"; has no "Strategic Initiatives". A7: a released ISO-only PDF does not contain "physical security review," nor "certified privacy professional" nor "drawn directly from the source standard", and contains "qualified information security auditor" and "referenced by clause or control identifier"; a released DPDPA-only PDF still contains the original "physical security review" and "certified privacy professional" sentences; a DPDPA + ISO PDF contains "(for DPDPA requirements)". `list(inspect.signature(generate_pdf).parameters)` is unchanged.
11. **Report tab.** Before approval: `data-framework-pending="dpdpa"` with "0 of N conclusions approved", no gauge percentage for it, `data-release-state="not_released"` and `data-release-blockers`. After approve-all and release: the gauge shows the approved score, `data-framework-coverage`, `data-release-state="released"`, the deterministic summary, and no AI summary text. After a reopen: `stale`. A no-Conclusion framework shows "Scores unavailable". A failed framework keeps P5-1's banner and card. The Requirements card shows "Insufficient evidence". Quick Wins shows the not-estimated text. Chapter headings render the chapter title verbatim ("India DPDPA — …"). A `GapItem` with legacy remediation fields for an approved requirement still renders `data-legacy-remediation`.
12. **Conclusions page release panel.** Pending → `data-release-panel` with blockers and no `data-release-form`. All approved → `data-release-form` posting to `/api/assessments/{id}/release`. Released → "Released by Priya". No apostrophe in `release_panel.html`.
13. **Retired legacy review.** `PATCH review/items/{id}`, `POST review/approve`, `POST review/reject` → 410 `LEGACY_REVIEW_RETIRED`; afterwards every `GapItem`'s `(review_status, reviewed_by, reviewed_at, compliance_status, reviewer_notes)`, `assessment.review_status`, the revision count and the audit-event count are unchanged. `GET /assessments/{id}/review` → 303 to `/assessments/{id}/conclusions`. `app/schemas/review.py`, `pages/review.html`, `partials/review_filter_bar.html` do not exist; `partials/review_finding_card.html` does.
14. **Snapshots.** Not released → gap-report generation 403. Released → generate v1, issue v1 → 200. Generate v2, reopen + re-approve + re-release, issue v2 → 409 `SNAPSHOT_STALE_MESSAGE`; generate v3, issue v3 → 200. v1's stored bytes and sha256 are identical before and after all of that (and after one more re-run). A workpaper generated before release cannot be issued after release (409 stale). `source_manifest` key set unchanged.
15. **Integrated report.** Engagement with A (released), B (`review_status = "approved"` by hand, Conclusions pending) and C (released, then an in-scope reopen → stale): the report includes only A, excludes B and C with `NOT_RELEASED`; A's score line equals A's approved score (edit one outcome so it differs from `GapReport.framework_scores`). Generate, re-release A (reopen + re-approve + release), issue → 403 `INTEGRATED_NOT_RELEASABLE`; generate again, issue → 200.
16. **Comparison and schema.** Two released assessments of one company: `/compare` deltas come from rows (a consultant edit changes the delta); framework delta uses approved scores; a comparable list omits an assessment whose release is stale. `FrameworkScoreOut(**failed_framework_scores()).status == "failed"`, `FrameworkScoreOut(overall_score=80.0, overall_rating="Compliant", domain_scores={}).status == "scored"`, and a `pending_review` entry with `coverage` validates.
17. **Analysis poll and detail.** After a successful analysis, `GET /analysis-status` shows "awaiting consultant review" for every framework, no percentage, and `data-review-conclusions-link`. A partial failure still shows `data-analysis-failed-frameworks`. The framework tab count equals the eligible gap-outcome rows for that framework.
18. **Legacy data path.** (a) A hand-built pre-P2-3 assessment (GapReport + GapItems, zero Conclusions, `review_status = "approved"`, plus one previously issued snapshot file written through `report_snapshots.create_snapshot` + `issue_snapshot`): every release path 403; the report tab says "Scores unavailable"; the issued snapshot downloads byte-identically. (b) A `migrate_legacy`-shaped assessment (proposal revision with `citations_json=None`, an `approved` revision by actor `"Legacy Reviewer"`): not releasable (blocker 5); approve is refused with `EVIDENCE_NOT_CAPTURED` after reopen; after reopen → re-run (stub) → approve → release, the release succeeds.
19. **Guards (D-P5-2-R, D-P5-2-U).** Every grep/AST/`inspect` assertion listed in D-P5-2-R and each checkable item of D-P5-2-U, by reading source. `git diff --stat main -- app/routers/analysis.py app/services/analysis_pipeline.py app/models alembic` is empty (via `subprocess`, with `grep`, not `rg`). `alembic heads` is `8b2d5f7e1c34 (head)`.

## Done criteria

- `tests/test_p5_2_reader_migration.py` passes. `.venv/bin/pytest -q` passes in full: **baseline (measured in Step 0) + N passed, 9 skipped**, with only the documented exceptions: the fresh-worktree teardown error from `tests/conftest.py::_guard_dev_database_untouched` if it appears, the two working-tree guards (`test_longitudinal_demo.py::test_scenario_13_protected_surface_is_unchanged`, `test_retention.py::test_scenario_13_only_new_retention_test_file_changes`) failing **only** while uncommitted, and `test_scenario_9`'s flake if it appears.
- `tests/test_no_blended_scoring.py::test_no_template_reads_retired_score` and `tests/test_longitudinal_demo.py` pass **unmodified**.
- `git diff --stat main -- tests/` shows only the new file and the D-P5-2-S files; every changed test function appears in Results with its reason code (a)-(e) and any old → new literal.
- `git diff --stat main` touches only `## Key files` (plus `tasks/todo.md` and this handoff). `git diff --stat main -- app/routers/analysis.py app/services/analysis_pipeline.py app/services/conclusion_review.py app/services/findings.py app/services/workpaper.py app/models alembic` is empty.
- **Smoke test** (record outputs in Results). Fresh Alembic-built SQLite DB and the in-process ASGI `TestClient` if a socket bind is refused; analyzers patched.
  1. DPDPA + ISO assessment (scope restricted to 3 + 3 requirements), run analysis, `GET /api/assessments/{id}/report/summary` → paste the 403 body. `POST /release` → paste the 409 JSON.
  2. Approve all but edit one outcome through `POST …/conclusions/{id}/edit`; `POST /release` → paste the 200 JSON and `SELECT action, actor, metadata_json FROM audit_events WHERE action='assessment.released'`.
  3. Paste `/report/summary` (`framework_scores` with `coverage`) and the first 30 lines of the PDF text.
  4. Reopen one Conclusion → paste the 403 body and the report-tab banner text.
  5. **Browser check** if a browser is available: the release panel, the pending card, the released banner. If none, say so. Do not claim it.

## Rollback

- **Code:** `git revert`. The old gate (`review_status == "approved"`) returns. Every assessment the release route set to `"approved"` stays approved under the old gate, which is safe (they were individually approved when released) but would ignore later reopens. **Also, every assessment still carrying a legacy bulk `"approved"` becomes releasable again**; say so in the revert PR.
- `assessment.released` audit events stay as inert history. No schema change, nothing to downgrade.
- The deleted `app/schemas/review.py` and templates come back with the revert.
- Issued snapshots are untouched either way.

## Open questions (deliberately flagged, not resolved here)

1. **A minimum coverage for showing a score.** Today a framework with 2 scored and 40 `insufficient_evidence` requirements shows a number (with "2 of 42 scored" beside it). A threshold (for example, no number below 50% scored) needs consultant input on what a client should see.
2. **A consultant-authored executive summary.** The AI narrative is no longer shown anywhere in the report. A consultant-edited summary needs a stored, versioned, release-bound field (a schema change) and would join the release manifest.
3. **Manual Conclusions.** A requirement the analyzer can never propose blocks release forever (blocker 4). A consultant-created Conclusion path (with its own evidence basis and revision) would close that, and needs P2-3/P2-4 design.
4. **Scope flip-flop between release and a workpaper render** is not detected by the issue binding (D-P5-2-O). Adding a release id to the snapshot manifest would close it, at the cost of flagging every existing snapshot "source changed".
5. **`scoring.score()`** (the P1 cluster-first scorer) still reads `GapItem`. No surface calls it. Retire it, or port it to approved outcomes, when cluster scoring is surfaced.
6. **Dead `GapItem` review artefacts.** `partials/review_finding_card.html` (rendered only by `test_needs_review_ui.py`), `GapItem.review_status`/`reviewed_by`/`reviewer_notes`/`needs_review` and the `ai_*` columns are now write-only history. A later cleanup can drop the template and the test together.
7. **The analyze API response** still returns AI-derived `per_framework_scores` numbers (P5-1 contract, internal automation only, no surface shows them). Consider renaming to `proposed_scores` or removing once no caller needs it.
8. **Release attribution.** "Release" and "approve" can be the same actor in v1 (PR-044 allows it). A later four-eyes rule (release actor ≠ last approver) would be a one-line blocker here.

## Report back

Append a `## Results` section to this file containing:
- Step 0's outputs (the symbol checks and the head) and the baseline you measured.
- The shipped constants, messages and signatures (`RELEASE_EVENT`, `RELEASE_SCHEMA_VERSION`, `FRAMEWORK_VIEW_STATUSES`, `PRIORITY_BY_RISK`, `NO_ANALYSIS_MESSAGE`, `ANALYSIS_RUNNING_MESSAGE`, `RELEASE_BLOCKED_MESSAGE`, `MISSING_CONCLUSIONS_MESSAGE`, `AWAITING_DECISION_MESSAGE`, `NOTHING_IN_SCOPE_MESSAGE`, `ALREADY_RELEASED_MESSAGE`, `NOT_RELEASED_MESSAGE`, `LEGACY_REVIEW_RETIRED`, `SNAPSHOT_STALE_MESSAGE`, `APPROVED_OUTCOME_POINTS`, `DENOMINATOR_EXCLUDED_OUTCOMES`, `approved_framework_scores`, `in_scope_requirement_ids`, `build_approved_report`, `release_state`, `is_released`, `record_release`, `latest_release_event`, `generated_after`, the dataclass field lists), copied from the code.
- The X1-X13 reader table with what you actually changed at each site.
- The D-P5-2-S list of every existing test and script you changed, with reason code and old → new literals.
- `pytest -q` output for the new file and for the full suite, with the baseline and the working-tree-guard note.
- The smoke outputs.
- Anything this document got wrong about the current code. **Name it and stop if it forces a design change. Do not pick an alternative.**

Commits and PRs for this task carry **no** `Co-Authored-By: Claude` trailer and no "Generated with Claude Code" footer. Codex cannot commit (its sandbox refuses to write `.git`). Leave the tree uncommitted, and the reviewing session commits on your behalf.

## Results

### Step 0 and baseline

The required Step 0 checks passed:

```text
32:UNCONFIRMED_ANSWER_SOURCES = ("document", "inferred")
35:def confirmed_response_clause()
52:FRAMEWORK_ANALYSIS_FAILED = "failed"
55:def failed_framework_scores() -> dict
64:def is_failed_framework_score(entry) -> bool
68:def failed_framework_ids(framework_scores: dict, framework_ids: list[str]) -> list[str]
8:RELEASE_BLOCKED_MESSAGE = "Analysis failed for {names}. Run analysis again before releasing this report."
17:def scoped_findings(db, assessment, *, framework_ids: list[str] | None = None)
64:def load_desk_review_data(db, assessment)
8b2d5f7e1c34 (head)
```

Baseline before implementation: `1 failed, 592 passed, 9 skipped, 211 warnings in 109.89s`; the only failure was the known `tests/test_longitudinal_demo.py::test_scenario_9_rollups_and_integrated_reporting` ordering flake.

### Shipped contract

`app/services/approved_report.py` is the read-only approved view and release-state reader. It exports:

```text
RELEASE_EVENT = "assessment.released"
RELEASE_SCHEMA_VERSION = 1
FRAMEWORK_VIEW_STATUSES = ("scored", "not_scored", "pending_review", "unavailable", "failed")
PRIORITY_BY_RISK = {"critical": 1, "high": 2, "medium": 3, "low": 4}
NO_ANALYSIS_MESSAGE = "Run analysis before releasing this report."
ANALYSIS_RUNNING_MESSAGE = "Analysis is running. Wait for it to finish before releasing this report."
RELEASE_BLOCKED_MESSAGE = "Analysis failed for {names}. Run analysis again before releasing this report."
MISSING_CONCLUSIONS_MESSAGE = "{name}: no conclusion was proposed for {count} in-scope requirement(s). Run analysis again."
AWAITING_DECISION_MESSAGE = "{name}: {count} of {total} in-scope conclusions still need an individual consultant decision."
NOTHING_IN_SCOPE_MESSAGE = "No requirement is in scope for this assessment. Record the scope before releasing."
ALREADY_RELEASED_MESSAGE = "This report is already released for the current approved conclusions."
NOT_RELEASED_MESSAGE = "Report not yet approved for release. Complete the review process first."
LEGACY_REVIEW_RETIRED = "Assessment-level review has been retired. Approve each conclusion individually on the Conclusions page, then release the report."
SNAPSHOT_STALE_MESSAGE = "This version was generated before the current release. Generate a new version, then issue it."
APPROVED_OUTCOME_POINTS = {"compliant": 100, "partially_compliant": 50, "non_compliant": 0}
DENOMINATOR_EXCLUDED_OUTCOMES = ("not_applicable", "insufficient_evidence")
```

Signatures shipped: `approved_framework_scores(outcomes: dict[str, str], framework_id: str) -> dict`, `in_scope_requirement_ids(raw: str | None) -> frozenset[str] | None`, `build_approved_report(db: Session, assessment: Assessment) -> ApprovedReport`, `release_state(db: Session, assessment: Assessment) -> ReleaseState`, `is_released(db: Session, assessment: Assessment) -> bool`, `record_release(db: Session, assessment: Assessment, *, actor: str) -> AuditEvent`, `latest_release_event(db: Session, assessment_id: str) -> AuditEvent | None`, and `generated_after(db: Session, snapshot_id: str, event_id: str) -> bool`. `generate_pdf` retains the exact parameter list `report, gap_items, company_name, initiatives, answer_source_map, selected_frameworks, assessment, report_findings`.

Dataclass field lists:

```text
ApprovedRow: id, conclusion_id, conclusion_version, framework_id, requirement_id,
requirement_title, chapter, chapter_title, control_reference, compliance_status,
current_state, gap_description, risk_level, remediation_action, remediation_priority,
evidence_quote, decision, decided_by, decided_at, remediation_effort, timeline_weeks,
maturity_level, root_cause_category, evidence_confidence
FrameworkReview: framework_id, name, in_scope_ids, out_of_scope_ids, missing_ids,
awaiting_ids, rows, coverage, status, score
ReleaseState: blockers, releasable, released, stale, release_event_id, released_by, released_at
RenderReport: id, assessment_id, chapter_scores, framework_scores, executive_summary, generated_at
ApprovedReport: assessment_id, report_id, generated_at, rows, framework_reviews,
framework_scores, chapter_scores, summary_text, release
```

### X1-X13 reader migration

| Reader | What changed |
|---|---|
| X1 `reports.get_report` | Uses `ApprovedReport` rows/scores/summary and an approved-only roadmap; initiatives are empty. |
| X2 `reports.get_report_summary` | Counts approved rows, includes coverage and excluded-outcome counts, and is release-gated. |
| X3 `reports.get_full_report` | Groups approved rows and returns approved scores and deterministic summary only. |
| X4 `_download_pdf_response` | Renders `ApprovedReport.render_report()` and approved rows through the unchanged PDF signature. |
| X5 `pdf_export.generate_pdf` | Removed model imports; added approved coverage, insufficient-evidence, no-estimate timeline, methodology, and conditional A7 copy. Legacy direct `GapReport` golden callers remain compatible. |
| X6 comparison | Uses approved rows for deltas and approved scored framework entries for framework deltas. |
| X7 comparable assessments | Uses `is_released`, excluding stale and legacy bulk-approved assessments. |
| X8 framework display/poll | Shows approved status and coverage; pending review shows progress rather than a percentage. |
| X9 report tab | Uses approved rows, deterministic summary, release state/banner, coverage, pending/not-scored cards, and only the permitted historical remediation lookup. |
| X10 framework tab | Counts approved gap-outcome rows per framework. |
| X11 integrated report | Includes released assessments only and scores from approved framework entries. |
| X12 integrated issue | Requires every source to be currently released and generated after its release event. |
| X13 legacy review | Bulk review routes return 410 without writes; the old page redirects to Conclusions; obsolete review schema/filter/page templates are deleted and the frozen finding-card partial remains. |

### Permitted existing tests and scripts

- `tests/test_analysis_pipeline.py` — (d): retired and renamed the old legacy-reader guard to check release readers.
- `tests/test_conclusion_approval.py` — (c): legacy review success expectations `200 → 410`, with no-cross-write checks retained.
- `tests/test_correctness_bundle.py` — (a), (b), (d): hand-set release became individual approval/release; release-path `200 → 403` where appropriate; old ₹250 output assertion became no ₹ output; the reader guard was inverted.
- `tests/test_no_blended_scoring.py` — (b): synthetic report setup now creates consultant-approved Conclusions and records release.
- `tests/test_pdf_updates.py` — (a), (b), (d), (e): direct decisions/release replaced hand-set approval; approved-derived score literals changed `100%/40%/60% → 0%/50%`; stale issue expectations changed `200 → 403/409` and fresh regeneration is asserted.
- `tests/test_report_snapshots.py` — (a), (e): direct decisions/release replaced hand-set approval; stale workpaper issue changed `200 → 409` with `SNAPSHOT_STALE_MESSAGE`; release wording changed to “released”.
- `scripts/seed_test_companies.py` — (a): scope is set through the existing seed session and bulk review is replaced by `POST /release`.
- `scripts/benchmark_performance.py` — (a): all synthetic a0 requirements remain in scope, pending/rejected Conclusions are approved after findings, and `record_release` replaces hand-set approval.
- `tests/test_performance_benchmarks.py` — (a): only the permitted a0 revision literal changed `1083 → 1197`.
- `tests/test_p5_2_reader_migration.py` — new 19-scenario contract suite.

### Verification

New contract suite: `19 passed, 7 warnings in 4.99s`.

Focused migration/regression set: `103 passed, 22 warnings in 20.11s`.

Full `.venv/bin/pytest -q` run: `3 failed, 609 passed, 9 skipped, 218 warnings in 67.75s`. The failures were the documented longitudinal scenario-9 ordering flake and the two expected uncommitted working-tree guards (`test_longitudinal_demo.py::test_scenario_13_protected_surface_is_unchanged` and `test_retention.py::test_scenario_13_only_new_retention_test_file_changes`). The fresh workpaper teardown issue did not appear. `git diff --check`, compilation, the Alembic head, protected-file diff, relationship guard, reader grep/AST guards, and PDF signature checks passed.

The opt-in benchmark run was `8 passed, 1 failed`; its single failure is the handoff inconsistency recorded below.

### Smoke output

Fresh Alembic SQLite + in-process `TestClient`, with DPDPA + ISO scope restricted to 3 + 3:

```text
PENDING_SUMMARY 403 Report not yet approved for release. Complete the review process first.
PENDING_RELEASE 409 ["India DPDPA: 3 of 3 in-scope conclusions still need an individual consultant decision.", "ISO 27001: 3 of 3 in-scope conclusions still need an individual consultant decision."]
RELEASE 200 consultant:Smoke ['coverage', 'gap_report_id', 'manifest', 'schema_version'] ['dpdpa', 'iso27001']
COVERAGE dpdpa={in_scope: 3, eligible: 3, scored: 3, compliant: 3} iso27001={in_scope: 3, eligible: 3, scored: 3, compliant: 2, partially_compliant: 1}
PDF_STATUS 200
PDF_FIRST_30
CyberAssess
Multi-Framework Compliance
Gap Assessment Report
September 24, 2026
Smoke Reader
Frameworks assessed: India DPDPA, ISO 27001
100% 83%
Compliant Compliant
India DPDPA ISO 27001
6 requirements assessed | 0 gaps identified
Assessment Areas
India DPDPA - Breach Notification 0%
India DPDPA - Obligations of Data Fidu 100%
India DPDPA - Rights of Data Principal 0%
India DPDPA - Special Provisions 0%
India DPDPA - Consent Management (Deta 0%
India DPDPA - Cross-Border Data Transf 0%
ISO 27001 - Organizational Controls 83%
ISO 27001 - People Controls 0%
CyberAssess | CONFIDENTIAL | Smoke Reader Page 1/9
ISO 27001 - Physical Controls 0%
CyberAssess | Executive Dashboard
0 0 n/a
Critical Gaps High Risk Gaps Remediation Timeline (not estimated)
Framework Scores
India DPDPA 100%
ISO 27001 83%
India DPDPA: 3 of 3 in-scope requirements scored; 0 insufficient evidence (excluded from the score, not counted as non-compliant); 0 not applicable.
ISO 27001: 3 of 3 in-scope requirements scored; 0 insufficient evidence (excluded from the score, not counted as non-compliant); 0 not applicable.
REOPEN 200 403 Report not yet approved for release. Complete the review process first. True
```

The release JSON was `{"status":"released","release_event_id":"<uuid>"}`. The recorded event was `assessment.released`, actor `consultant:Smoke`, with metadata keys `coverage`, `gap_report_id`, `manifest`, and `schema_version`. Browser automation was unavailable, so no browser check is claimed.

### Discrepancies and flags

1. The literal D-P5-2-R command `grep -rnE "review_status\\s*(==|!=)" app/` also matches unrelated pre-existing `desk_review_status` comparisons in `web.py` and `retention.py`. The permitted guard tests use `\\breview_status\\b` to express the intended field boundary; no desk-review behavior was changed.
2. The benchmark instructions require approving pending/rejected a0 Conclusions after the existing finding loop so findings do not change, while unchanged `test_a0_product_shapes` requires persisted findings to equal every approved gap outcome. Following the handoff produces 95 persisted findings versus 171 approved gap outcomes. I did not invent a workaround or change that assertion beyond the explicitly permitted `1083 → 1197` literal; the opt-in failure is left flagged for review.

The repository remains uncommitted as requested. No schema migration, protected analysis/pipeline/model/Alembic change, or commit was made.
