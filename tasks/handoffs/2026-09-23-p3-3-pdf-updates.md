# P3-3: PDF updates: approved Findings with citations and evidence chain in the gap report, and an engagement-level integrated report generated only as a write-once snapshot

**Plan:** `docs/plans/2026-09-21-002-revised-implementation-plan.md`, Phase 3, task P3-3 ("Per-framework scores (no blended) in executive summary"; "Citations in finding details"; "Evidence chain rendering"; "Engagement-level integrated report option (consolidates approved findings across assessments, preserves distinct scopes/dates per the product requirements)"; files: `app/utils/pdf_export.py`, "additive changes only, per CLAUDE.md: 'PDF sections are additive-only'"; test: "Generate PDF for multi-framework assessment. Verify per-framework scores, citations present, no blended score."), and the Phase 3 exit criteria "PDF shows per-framework scores with citations" and "Engagement-level reporting consolidates without blending". Decisions **D1/D5** in `tasks/2026-09-21-adversarial-review.md` (no blended cross-framework score) and **D2** (JSON and one generic `audit_events` table). PRD `docs/product/2026-09-21-cyberassess-product-requirements.md`: **PR-050** (Findings preserve their origin; "engagement rollup does not sever or obscure the origin"), **PR-052** ("exports use approved Conclusions only and remain unavailable until review gates pass"), **PR-053** ("One integrated Engagement report may consolidate selected approved Findings and Actions while clearly separating Assessment and framework results. Acceptance: each section states pack/version, scope, period, cut-off, exclusions, and Citations; no blended score across Assessments/frameworks is displayed."), **PR-054** (versioned snapshots), **PR-055** (traceability). Hand-forwards closed here: P3-2's "Handed forward … P3-3" (`tasks/handoffs/2026-09-23-p3-2-report-snapshots.md`), P3-1's open question 4 (whether reports exclude Findings whose source Conclusion was reopened).
**Owner:** Codex, from this Claude spec; Claude reviews the rendered output (per `tasks/agent-ownership.md`: "P3-3 PDF updates | Codex, from Claude spec, Claude reviews rendered output"). Every architectural fork is closed below. **If the code forces a deviation from any decision, stop and report it in `## Results`. Do not pick an alternative.** Merge gate: the standard `[AR]` adversarial review (`tasks/todo.md` tags Phase 3 `[AR: report immutability, provenance, closure verification]`), plus a Claude review of real rendered PDFs from the smoke test.
**Depends on:** P3-1 (`app/services/findings.py::findings_page`, merged PR #30) and P3-2 (`app/services/report_snapshots.py`, `app/routers/snapshots.py`, merged PR #31). `main` is at `c9d0196`. (`tasks/todo.md`'s P3-2 line still says "PR #31, open, not yet merged". That line is stale; fix it, see Done criteria.)
**Runs in parallel with:** P3-4 (remediation tracking). P3-4 changes `app/services/findings.py` (it extends `ACTION_TRANSITIONS`, adds fields **with defaults** to `ActionView`/`FindingView`, and derives `Finding.status`). This task only **reads** `findings.findings_page(...)` and the existing fields `view.finding`, `view.card`, `view.source_approved`, `view.actions[i].action`. Do not edit `app/services/findings.py`. Files both tasks may touch: `app/main.py` (one `include_router` line each), `app/routers/web.py` (one new page route each, in different places), `app/templates/pages/engagement_detail.html` (one link each) and `tasks/todo.md` (one line each). If P3-4 lands first, keep both sides of each conflict.
**Blocks:** nothing in Phase 3. P4-2 (longitudinal demo) will generate integrated reports.
**Failing contract suite: none pre-written.** A grep of `tests/` for `P3-3`, `integrated_report`, `report_findings` and `generate_integrated_pdf` finds only P3-2's scenario 9 and 11 in `tests/test_report_snapshots.py` (the assessment route refusing `type=integrated_report`, and hand-inserted integrated rows pinning the issue statement). Neither tests anything this task builds. As with P2-4 onward, **Codex writes `tests/test_pdf_updates.py` itself** from `## Test scenarios`, following the fixture pattern of `tests/test_findings.py` and `tests/test_report_snapshots.py` (step 9). Every scenario listed is required. You may add cases, but you may not drop or weaken one.

## Goal

1. The **gap report PDF** (`GET /api/assessments/{id}/report/pdf`, and therefore every new `gap_report` snapshot, which P3-2 renders by calling that route) gains one new section, **"Approved Findings"**. It lists every Finding whose source Conclusion is currently individually approved, grouped by framework. Each Finding shows its requirement, the consultant decision that backs it, its **citations** (excerpt, file, version, location, SHA-256 prefix) and its Actions. That is the evidence chain Finding → decision → citation → evidence version. Nothing else in the existing PDF changes.
2. The **per-framework scores** the executive summary already shows (P1-5) stay exactly as they are. There is still no blended or overall score anywhere.
3. A consultant opens `/engagements/{engagement_id}/integrated-reports` and generates an **integrated engagement report**: one PDF that consolidates every release-approved assessment of the engagement, **one section per assessment**. Each section states the assessment's own dates, frameworks and pack versions, scope, its own per-framework scores, and its own approved Findings with citations. Scores are never added, averaged or compared across assessments or frameworks. The report exists only as a P3-2-style write-once snapshot: generate a draft, view it, issue it.

## Current state

Grounded against `c9d0196` on `main`. Baseline `.venv/bin/pytest -q` → **477 passed, 115 warnings** (I ran it at `c9d0196`). `alembic heads` → `4e8c1a9d2b57 (head)`. Re-locate everything by symbol name.

- **`app/utils/pdf_export.py`** (1133 lines). One public entry point: `generate_pdf(report, gap_items, company_name, initiatives=None, answer_source_map=None, selected_frameworks=None, assessment=None) -> bytes`. It draws with module helpers `S()` (latin-1 sanitizer with `_UNICODE_MAP`), `_set_font_to_fit`, `_rating_color`, `_draw_score_ring`, `_draw_kpi_card`, `_draw_h_bar(pdf, x, y, w, h, score, label, rating)` (prints `f"{score:.0f}%"`), `_draw_status_bar`, `_draw_timeline_block`, `_draw_gap_card`, `_draw_heatmap_row`, `_page_footer(pdf, company_name)`, `_page_header(pdf, section_title)` and `_section_title(pdf, title)`, and constants `NAVY`, `DARK_TEXT`, `MID_TEXT`, `LIGHT_TEXT`, `CARD_BG`, `DIVIDER`, `WHITE`, `RISK_COLORS`, `STATUS_COLORS`, `PW`/`PM`/`CW`. `pdf.set_auto_page_break(auto=False)`, so every section breaks pages by hand (`if y > 245: _page_footer(...); pdf.add_page(); _page_header(...)`).
  - Page order in `generate_pdf`: cover (one `_draw_score_ring` per framework, comment "One score ring per framework; no cross-framework ring exists."), Executive Dashboard (KPI cards, **`_section_title(pdf, "Framework Scores")` with one `_draw_h_bar` per framework**, Compliance Distribution, Assessment Areas, Key Findings), Critical & High Risk Gaps, Remediation Roadmap, Strategic Initiatives (if any), the Appendix divider ("Detailed Gap Findings"), one appendix page per chapter (`for chapter_key, items in chapters_grouped.items():`), **Scope & Limitations** (`pdf.add_page(); _page_header(pdf, "Scope & Limitations")`), then Methodology, then `return bytes(pdf.output())`.
  - **Per-framework scores already exist (P1-5).** `framework_score_rows` is built from `report_framework_scores(report, score_assessment)` with a subscript read `scores["overall_score"]` and skips frameworks with no score. There is no blended ring, bar or number. `tests/test_no_blended_scoring.py::test_pdf_has_one_score_section_per_framework_and_no_total` asserts "Overall Score" is absent and each framework's score is present. **This task adds nothing to the score pages.**
  - **No citation, Finding or evidence-chain rendering exists.** The only "evidence" is `_draw_gap_card(..., show_evidence=True)`, which prints `GapItem.evidence_quote` in the appendix. Everything is `GapItem`-sourced.
  - The Methodology text says "The overall score is the weighted average of chapter scores" (per framework, lower-case). It is not changed (additive-only).
- **`app/routers/reports.py`**: `download_pdf(assessment_id, db)` calls `require_review_approval` (403 unless `review_status == "approved"`), `_get_report` (404 "No report found. Run analysis first."), loads items, initiatives and `answer_source_map`, parses `selected_frameworks`, then calls the module-global `generate_pdf(report, items, company_name, initiatives=…, answer_source_map=…, selected_frameworks=…, assessment=assessment)` and returns `Response(… media_type="application/pdf", Content-Disposition attachment …)`. It imports `generate_pdf` by name (`from app.utils.pdf_export import generate_pdf`), which is the seam P3-2's tests monkeypatch (`monkeypatch.setattr(reports, "generate_pdf", _fake)` with `def _fake(*_args, **_kwargs)`).
- **Standing guard that shapes this whole design:** `tests/test_analysis_pipeline.py::test_legacy_consumers_do_not_read_the_new_tables` runs `grep -nE "Conclusion|AnalysisRun|analysis_pipeline"` over `app/services/scoring.py`, `app/routers/review.py`, **`app/routers/reports.py`**, `app/routers/remediation.py` and **`app/utils/pdf_export.py`**, and requires empty output. The grep is **case-sensitive**: `conclusion` in lower case does not match; `Conclusion` anywhere (code, strings, comments, docstrings, identifiers such as `ConclusionCard`) does.
- **Blended-score guards** (`tests/test_no_blended_scoring.py`): `test_no_template_reads_retired_score` fails on the literal `overall_score` anywhere under `app/templates`, and on any `ast.Attribute` named `overall_score` or `ast.keyword` with `arg == "overall_score"` in `app/**/*.py` outside an allow-list (`app/models/report.py`, `app/services/scoring.py`, `app/schemas/scoring.py`, `app/legacy_migrations.py`, `app/legacy_migrations_schema.py`, `app/routers/analysis.py`). A **subscript** `scores["overall_score"]` is not flagged (it is how `pdf_export.py` reads it today).
- **`app/services/scoring.py::report_framework_scores(report, assessment) -> dict[str, dict]`**: parses `GapReport.framework_scores` JSON (`{framework_id: {"overall_score", "overall_rating", "domain_scores", …}}`); falls back to the legacy `overall_score` only for a single-framework assessment; returns `{}` otherwise.
- **`app/services/findings.py`** (P3-1). I read it in full. What this task reuses: `findings_page(db, assessment_id) -> FindingsPage` (`eligible`, `findings: list[FindingView]`, Findings in `created_at, rowid` order; it calls `conclusion_review.conclusion_cards` once) and `FindingView` fields `finding` (ORM `Finding`), `card` (`ConclusionCard | None`), `origin`, `created_by`, `source_approved` (`card is not None and card.state in ELIGIBLE_STATES`, where `ELIGIBLE_STATES = ("approved", "edited")`), `workpaper_href`, `actions: list[ActionView]` (`ActionView.action` is the ORM `Action`, ordered `created_at, rowid`). `findings_page` never writes.
- **`app/services/conclusion_review.py`** (P2-4): `ConclusionCard` has `conclusion` (ORM), `requirement_title`, `state`, `citations_captured`, `citations` (resolved from the **latest `proposed`** revision via `citations.resolve_citations`), `last_decision` (`{"action", "actor_display", "created_at"}` or `None`; `actor_display` has the `consultant:` prefix already stripped), `legacy_bulk_approval`.
- **`app/services/citations.py::resolve_citations(db, raw)`** returns each stored citation (`evidence_version_id`, `location_type`, `location_ref`, `excerpt`) plus `resolved`, `evidence_id`, `filename`, `version_number`, `version_status`, `evidence_status`, `is_current`. **It does not return the version's SHA-256**; that is `EvidenceVersion.file_hash_sha256` (String 64).
- **`app/services/workpaper.py`**: `anchor_for(framework_id, requirement_id) -> f"wp-{framework_id}-{requirement_id}"`. `build_workpaper` is the full per-requirement read model (client response, desk review, every revision). It is **not** used here (D-P3-3-C).
- **`app/services/report_snapshots.py`** (P3-2). I read it in full.
  - Constants `SNAPSHOT_TYPES = ("gap_report", "workpaper", "integrated_report")`, `ASSESSMENT_SNAPSHOT_TYPES = ("gap_report", "workpaper")`, `FORMAT_BY_TYPE` (`integrated_report` → `pdf`), `MEDIA_TYPES`, `TYPE_LABELS`, `AUDIT_ENTITY_TYPE = "report_snapshot"`, `GENERATED_ACTION`, `ISSUED_ACTION`, `MANIFEST_SCHEMA_VERSION = 1`, `ISSUE_SQL` (already scope-aware for `assessment_id IS NULL` + `engagement_id`), `INTEGRITY_MESSAGE`; exceptions `SnapshotError` (with `status_code`, `message`), `InvalidSnapshot` 400, `SnapshotNotFound` 404, `SnapshotNotIssuable` 409, `SnapshotIntegrityError` 500.
  - Functions: `storage_path_for(*, snapshot_id, fmt, assessment_id=None, engagement_id=None)` (engagement form `reports/engagements/{engagement_id}/{snapshot_id}.{fmt}`), `snapshot_path(snapshot)`, `source_manifest(db, assessment) -> {"gap_report_id", "conclusion_versions"}`, `_write_file(storage_path, content)` (the module's only `.open("xb")`), `_record_event(db, *, actor, action, snapshot_id, metadata)`, `create_snapshot(db, *, assessment, snapshot_type, content, actor)` (refuses any type outside `ASSESSMENT_SNAPSHOT_TYPES`; writes the file, then inside `try:` adds the row and the generated event and flushes; `except Exception:` `path.unlink(missing_ok=True)` and re-raises; that is the module's only `.unlink(`), `load_snapshot(db, *, assessment_id, snapshot_id)` (filters by `assessment_id`, so it can never load an integrated row), `generated_event`, `read_snapshot_bytes`, `verify_snapshot_file`, `issue_snapshot(db, snapshot, *, actor)` (scope-agnostic: verify, `ISSUE_SQL`, issued event), `_actor_display`, `SnapshotRow` (frozen: `snapshot`, `sequence`, `state`, `is_current_issue`, `issuable`, `sha256`, `size_bytes`, `generated_by`, `issued_by`, `issued_at`, `source_changed`) and `snapshot_rows(db, assessment)` (assessment-only).
  - Its generated-event metadata has exactly the keys `schema_version`, `type`, `format`, `storage_path`, `sha256`, `size_bytes`, `assessment_id`, `engagement_id`, `review_status`, `source`.
- **`app/routers/snapshots.py`** (P3-2): assessment-scoped generate/issue/file routes. For `type == "integrated_report"` it returns 400 "Integrated engagement reports are not available yet." (asserted verbatim by P3-2 scenario 9). Its `_render` gets gap-report bytes by calling `reports.download_pdf(assessment_id=…, db=db)` and taking `bytes(response.body)`.
- **P3-2 standing guards** (`tests/test_report_snapshots.py`):
  - scenario 3 over `app/services/report_snapshots.py` + `app/routers/snapshots.py`: no match for `\.is_issued\s*=(?!=)` or `SET\s+is_issued\s*=\s*0`; the service has **exactly one** `.open(` (and it is `.open("xb")`), no `write_bytes(`/`write_text(`/`"wb"`/`'wb'`/`"ab"`/`'ab'`, **exactly one `.unlink(`**; the router exactly one `.unlink(`; `"delete"` absent from both (lower-cased, comments included);
  - scenario 12: the set of app routes whose path contains **`/snapshots`** is exactly P3-2's four.
- **Other route-set guards:** paths containing `/conclusions` (P2-4 scenario 12, five routes), `/workpaper` (P2-6 scenario 9, one route), `/findings` (P3-1 scenario 11, five routes). `tests/test_white_label.py` forbids `CyberAssess` in `app/templates/` and in PDF text.
- **Engagement pages** (`app/routers/web.py`): `engagement_detail` (`GET /engagements/{engagement_id}`) loads the `Engagement` (404 "Engagement not found"), its `Client` (404 "Client not found") and its assessments with `Assessment.engagement_id == engagement_id` and `Assessment.status != "archived"`, and renders `pages/engagement_detail.html`. The only existing `/engagements/...` routes are that page, `/engagements/new`, `/engagements/new/client-fields`, and P2-5's `POST /engagements/{engagement_id}/magic-links` and `…/magic-links/{link_id}/revoke` (`app/routers/magic.py`, `APIRouter(include_in_schema=False)`, no prefix). **No route path starts with `/api/engagements` today.** `Engagement` has `id`, `client_id`, `name`, `type`, `status`, `created_at`, `updated_at`; `Client` has `name`.
- **Scope metadata that exists:** `Assessment.created_at`, `Assessment.description`, `Assessment.applicable_requirements` (JSON list or NULL), `Assessment.frameworks` (property), `Assessment.review_status`; `GapReport.generated_at` (the analysis date); `AssessmentPack(assessment_id, framework_id, pack_version)` rows, written by `engagement_factory.create_engagement_with_assessment` (`framework.version`) and by `scripts/migrate_legacy.py` (`"unknown"`). **There is no assessment-period, evidence cut-off or exclusions-rationale column anywhere** (D-P3-3-G).

## Decisions (made here so they are not relitigated)

### D-P3-3-A. Per-framework scores: already correct; this task changes nothing on the score pages and adds no score anywhere else in the gap report

The plan's "Per-framework scores (no blended) in executive summary" is **already implemented by P1-5** (Current state): one cover ring and one "Framework Scores" bar per framework, no overall. This task:
- does **not** touch the cover, the Executive Dashboard, or any existing page;
- adds no score to the new Findings section;
- adds a regression assertion in its own suite (scenario 1) that the multi-framework PDF still shows each framework's score and no "Overall Score".

The integrated report shows scores only **inside each assessment's section, per framework** (D-P3-3-F).

### D-P3-3-B. Where the Finding, citation and evidence-chain data comes from: a new read-only module, `app/services/report_content.py`, which hands `pdf_export.py` plain frozen dataclasses

`pdf_export.py` and `reports.py` must not contain the token `Conclusion` (Current state, case-sensitive guard). Findings, cards and citations are Conclusion-derived. So:

- **A new module `app/services/report_content.py`** does all the reading (it is not under the guard). It returns plain frozen dataclasses (below) that carry only strings, numbers, dates and lists. **No ORM object crosses into `pdf_export.py`** from this module.
- `pdf_export.py` reads those objects by **attribute** (duck-typed). It does **not** import `report_content`. New code in `pdf_export.py` uses the words "finding", "decision", "requirement", "citation" and "evidence", never `Conclusion`, `AnalysisRun` or `analysis_pipeline`, in code, strings, comments or docstrings.
- `reports.py` gains exactly one import, `from app.services import report_content`, and one call (D-P3-3-D). The legacy-consumer guard stays **unmodified and green**. Do not edit that test.

**Why not relax the guard:** the guard exists so the `GapItem`-sourced report pages can't silently start reading pipeline tables. This task adds a new, clearly bounded section from a separate module. The guard's intent ("Moving them to Conclusions is a later, separate task") still holds for every existing page.

### D-P3-3-C. Reuse `findings.findings_page`, not `workpaper.build_workpaper` or a new derivation

`report_content.assessment_findings` calls **`findings.findings_page(db, assessment.id)` exactly once**, through the module attribute (`from app.services import findings as finding_service`), and builds each `ReportFinding` from a `FindingView`.

**Why this read path, checked against the code:**
1. `FindingView.card` is the P2-4 `ConclusionCard`. It already carries the single derived decision `state`, `legacy_bulk_approval`, `last_decision` (actor already stripped, timestamp), and **`citations` resolved from the latest `proposed` revision**. That is the same revision the workpaper labels "AI proposal" (P2-6: `ai_proposal` is "the same revision `card.citations` comes from"). So the PDF's citations are, by construction, the ones the reviewer sees on the conclusions page and the workpaper.
2. `findings_page` also returns each Finding's Actions in order, which the PDF lists (D-P3-3-E).
3. `build_workpaper` adds client responses, desk-review rows, every revision and run claims. None of that belongs in a board PDF, and it would issue far more queries per render. The PDF instead prints each Finding's **workpaper anchor** (`anchor_for(framework_id, requirement_id)`) as a reference, so a reader can find the full trail (PR-055) without the PDF duplicating it.
4. No second citation resolver: the one extra query is the SHA-256 lookup (D-P3-3-E), which `resolve_citations` doesn't return.

Do not import private helpers from `findings.py`, `conclusion_review.py` or `workpaper.py`.

### D-P3-3-D. Which Findings appear: only those whose source is a current individual consultant approval

For an assessment, `assessment_findings(db, assessment)` includes a `FindingView` **iff** `view.source_approved and not view.card.legacy_bulk_approval`. Every other Finding (source reopened/pending/rejected, source missing, or source a legacy bulk approval) is **omitted and counted** in `omitted_count`, and the section prints one line saying how many were omitted and why.

- **Why:** PR-052 ("exports use approved Conclusions only") and D3 / D-P3-1-B (only an individual approval counts as approved). This closes **P3-1 open question 4** for reports: a Finding whose source was reopened is not reported until its source is re-approved. It is not deleted or altered; it simply doesn't render.
- Migrated Findings on legacy bulk-approved Conclusions are therefore omitted. The legacy `GapItem` appendix of the same PDF still shows those requirements, as it does today.
- **Finding status is not a filter.** A `resolved` or `accepted_risk` Finding is still an approved gap and is still reported, with its status printed.

**Ordering:** group by framework, frameworks in `assessment.frameworks` order and then any other `framework_id` sorted; within a framework, sort by `(SEVERITY_RANK[severity], priority, original index in findings_page order)` with `SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}` (unknown severities rank 4).

### D-P3-3-E. `app/services/report_content.py`: public API, exact

Module docstring (it passes every guard): `"""Read-only report content (P3-3): approved Findings with citations and evidence chain for the gap report, and per-assessment sections for the integrated engagement report. Never writes."""`

It never writes (no `db.add(`, `db.add_all(`, `db.merge(`, `.flush(`, `.commit(`), never logs finding text, excerpts or filenames (ids and counts only), and names its Session parameter `db`.

```python
from app.services import findings as finding_service    # module import: spy seam (scenario 2)
from app.services.scoring import report_framework_scores
from app.services.workpaper import anchor_for

SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
DECISION_LABELS = {"approved": "Approved", "edited": "Edited and approved"}
ACTION_STATUS_LABELS = {"open": "Open", "in_progress": "In progress",
                        "closed": "Closed, awaiting verification", "verified": "Closed and verified"}
FINDING_STATUS_LABELS = {"open": "Open", "in_progress": "In progress",
                         "resolved": "Resolved", "accepted_risk": "Accepted risk"}
NOT_RELEASED = "Not approved for release"
NO_REPORT = "No analysis report yet"
PERIOD_NOT_RECORDED = "not recorded"

@dataclass(frozen=True)
class ReportCitation:
    excerpt: str
    location_ref: str | None
    filename: str | None        # the cited version's original_filename; None when unresolved
    version_number: int | None
    sha256: str | None          # EvidenceVersion.file_hash_sha256 of the cited version
    resolved: bool
    is_current: bool

@dataclass(frozen=True)
class ReportAction:
    title: str
    owner: str | None
    target_date: date | None    # action.target_date.date() when set
    status: str
    status_label: str           # ACTION_STATUS_LABELS.get(status, status)

@dataclass(frozen=True)
class ReportFinding:
    finding_id: str
    title: str
    description: str
    severity: str
    priority: int
    status_label: str           # FINDING_STATUS_LABELS.get(finding.status, finding.status)
    framework_id: str
    framework_name: str         # FrameworkRegistry.get_or_none(fw).name, else fw.upper()
    requirement_id: str
    requirement_title: str      # card.requirement_title
    outcome_label: str          # card.conclusion.outcome.replace("_", " ").title()
    decision_label: str         # DECISION_LABELS[card.state]
    decided_by: str | None      # card.last_decision["actor_display"] when last_decision
    decided_at: datetime | None # card.last_decision["created_at"] when last_decision
    decision_version: int       # card.conclusion.version
    workpaper_ref: str          # anchor_for(framework_id, requirement_id)
    citations_captured: bool    # card.citations_captured
    citations: list[ReportCitation]
    actions: list[ReportAction]

@dataclass(frozen=True)
class AssessmentFindings:
    findings: list[ReportFinding]   # D-P3-3-D order
    omitted_count: int

@dataclass(frozen=True)
class ScoreLine:
    framework_name: str
    score: float                # NEVER name this field overall_score (D-P3-3-K item 2)
    rating: str

@dataclass(frozen=True)
class IntegratedSection:
    assessment_id: str
    label: str                  # f"{assessment.description or assessment.company_name} ({created:%d %b %Y})"
    created_at: datetime
    analysed_at: datetime | None    # GapReport.generated_at
    frameworks: list[tuple[str, str]]   # (framework_name, pack_version or "not recorded"), assessment.frameworks order
    scope_label: str            # D-P3-3-G
    scores: list[ScoreLine]     # this assessment only, assessment.frameworks order
    findings: AssessmentFindings

@dataclass(frozen=True)
class ExcludedAssessment:
    assessment_id: str
    label: str
    reason: str                 # NOT_RELEASED | NO_REPORT

@dataclass(frozen=True)
class IntegratedReport:
    engagement_name: str
    client_name: str
    sections: list[IntegratedSection]    # included assessments, created_at ascending, then id
    excluded: list[ExcludedAssessment]   # same order
    source: dict                         # D-P3-3-H manifest

def assessment_findings(db: Session, assessment: Assessment) -> AssessmentFindings: ...
def integrated_report(db: Session, engagement: Engagement) -> IntegratedReport: ...
```

- **`assessment_findings`**: one `findings_page` call; then **one** `select(EvidenceVersion.id, EvidenceVersion.file_hash_sha256).where(EvidenceVersion.id.in_(…))` over every cited `evidence_version_id` of the included Findings (skip when there are none). `excerpt` is the citation's `excerpt` (or `""`). Unresolved citations get `filename=None`, `version_number=None`, `sha256=None`.
- **`integrated_report`**: see D-P3-3-F/G/H. It raises nothing for an engagement with no assessments; the router decides (D-P3-3-I).
- The word `overall_score` appears in this module **only** as a string subscript key (`scores["overall_score"]`, `scores.get("overall_score")`), exactly as `pdf_export.py` reads it today.

### D-P3-3-F. The gap report's new section, and the integrated PDF: exact, additive-only rendering in `pdf_export.py`

**Additive only means, and is checked as:** `git diff main -- app/utils/pdf_export.py` has **zero removed lines** (no line starting with `-` other than the `---` header). Existing functions, pages and strings are untouched. You add:

1. **`generate_pdf` gets one new keyword parameter, last:** `report_findings=None`, inserted as a new line `    report_findings=None,` directly after `    assessment=None,`. Its docstring is unchanged.
2. **One new call**, inserted between the end of the appendix chapter loop (`for chapter_key, items in chapters_grouped.items(): …` ending with `_page_footer(pdf, company_name)`) and the `# APPENDIX: SCOPE & LIMITATIONS` block:
   ```python
   if report_findings is not None and (report_findings.findings or report_findings.omitted_count):
       _render_findings_section(pdf, company_name, report_findings)
   ```
   With `None` or an empty result, the output is exactly what it is today (the golden and white-label tests call `generate_pdf` without it).
3. **New private helpers**, appended in a new block `# Findings and evidence chain (P3-3)` placed after `_section_title` and before `# Main PDF generation`:
   - `_render_findings_section(pdf, company_name, report_findings, *, header="Findings and Evidence Chain")`: `pdf.add_page()`, `_page_header(pdf, header)`, `_section_title(pdf, "Approved Findings")`, then the intro line `Each finding below is bound to an individually approved requirement decision and lists the evidence it cites.`, then, when `omitted_count > 0`, the line `f"{n} finding(s) not shown: their source decision is not a current individual consultant approval."`, then the Findings. Print a framework sub-heading (bold, `framework_name`) each time `framework_id` changes. Findings are numbered `F1`, `F2`, … across the section. Page-break by hand before any block that would pass `y > 250`, continuing with `_page_header(pdf, f"{header} (continued)")`. Call `_page_footer` on every page it ends.
   - `_draw_finding_detail(pdf, finding, index, y) -> float` (returns the new y). It prints, in order, each through `S()`, using `multi_cell` for anything that can wrap:
     - `f"F{index}. {finding.title}"` (bold) with a severity colour bar from `RISK_COLORS`;
     - `f"{finding.framework_name} {finding.requirement_id}: {finding.requirement_title}"`;
     - `f"Severity: {finding.severity.title()} | Priority P{finding.priority} | Finding status: {finding.status_label}"`;
     - `f"Decision: {finding.outcome_label}, {finding.decision_label} by {finding.decided_by or 'unknown'} on {date or 'unknown date'}, record v{finding.decision_version} | Workpaper ref: {finding.workpaper_ref}"` (date as `%d %b %Y`);
     - `finding.description` (truncate to 600 characters plus `...`);
     - `Evidence chain:` then, per citation, numbered from 1: `f'[{n}] "{excerpt}"'` (excerpt truncated to 300 characters plus `...`) and on the next line `f"{filename} v{version_number} | {location_ref} | SHA-256 {sha256[:16]}"`, plus `" | superseded version"` when `not is_current`. An unresolved citation prints `Unresolved evidence` instead of the filename line. When `citations_captured` and there are none: `No supporting citation (explicit evidence absence)`. When not captured: `Evidence support not captured (legacy)`;
     - `Actions:` then per action `f"- {title} | Owner: {owner or 'Unassigned'} | Target: {target_date:%Y-%m-%d or 'No target date'} | {status_label}"`; `No actions recorded.` when empty.
   - `generate_integrated_pdf(report_data) -> bytes`: a **new public function**, appended at the end of the module. It builds its own `FPDF()` (same `alias_nb_pages`, `set_auto_page_break(auto=False)` settings) and draws:
     - **Cover:** `settings.firm_name` (via `_set_font_to_fit`), `Integrated Engagement Report`, `report_data.engagement_name`, `report_data.client_name`, today's date, `f"Assessments included: {len(report_data.sections)}"`, one line per section label, and the sentence `Results are reported separately for each assessment and framework. Scores are never combined across assessments or frameworks.`
     - **One block per section, each starting on a new page** with `_page_header(pdf, f"Assessment: {section.label}")` and `_section_title(pdf, section.label)`, then the lines `f"Assessment created: {created:%d %b %Y}"`, `f"Analysis date: {analysed_at:%d %b %Y or 'not recorded'}"`, `f"Frameworks and pack versions: {', '.join(f'{name} ({version})' …)}"`, `f"Scope: {section.scope_label}"`, `f"Assessment period and evidence cut-off: {PERIOD_NOT_RECORDED}"` (the literal `not recorded`); then `_section_title(pdf, "Framework Scores (this assessment only)")` and one `_draw_h_bar(pdf, PM, y, CW, 8, line.score, line.framework_name, line.rating)` per `ScoreLine` (or the line `Scores unavailable for this assessment.` when there are none); then, when the section has findings or omissions, `_render_findings_section(pdf, report_data.client_name, section.findings, header=f"Assessment: {section.label}")`.
     - **When `report_data.excluded` is non-empty**, a final page `_page_header(pdf, "Assessments Not Included")`, `_section_title(pdf, "Assessments Not Included")`, and one line `f"{label}: {reason}"` per excluded assessment.
     - `_page_footer(pdf, report_data.client_name)` on every page. `return bytes(pdf.output())`.

   **No arithmetic across `ScoreLine`s or sections anywhere.** No sum, mean, min/max, count-weighted value or comparison of scores is computed or printed. `_draw_h_bar` is the only thing that prints a score.

All new strings are plain ASCII. Everything user- or client-derived goes through `S()` (CLAUDE.md: missing it crashes fpdf2).

### D-P3-3-G. Integrated report scope: which assessments, and what each section states

- **Candidates:** the engagement's assessments with `status != "archived"` (the `engagement_detail` filter), ordered `created_at, id`.
- **Included** iff `assessment.review_status == "approved"` (the release gate, PR-052) **and** it has a `GapReport`. Otherwise **excluded** with reason `NOT_RELEASED` (checked first) or `NO_REPORT`.
- **Each included section states** (PR-053): its label and creation date; the analysis date (`GapReport.generated_at`); each framework with its `AssessmentPack.pack_version` (or `not recorded` when no pack row exists); scope; its own per-framework scores via `report_framework_scores(report, assessment)`, in `assessment.frameworks` order, skipping frameworks with no score (the `generate_pdf` rule); and its approved Findings (`assessment_findings`).
- **`scope_label`:** when `json.loads(assessment.applicable_requirements)` is a non-empty list, `f"{len(list)} applicable requirements in scope"`; otherwise `No scope restriction recorded` (NULL, unparseable, non-list, or empty; the P2-6 `applicable` rule).
- **Period, cut-off and exclusions rationale are not recorded anywhere in the schema** (Current state). The PDF prints `Assessment period and evidence cut-off: not recorded` rather than inventing values. Adding those fields is a schema change (open question 1).
- **Never blended:** no engagement-level score, count-weighted score or "average across assessments" exists in the data model or the PDF. The same framework appearing in two assessments gets two separate bars, each under its own assessment heading.

### D-P3-3-H. Snapshot integration: the gap report needs no wiring; the integrated report is snapshot-only and reuses P3-2's storage, event schema and `ISSUE_SQL`

**Gap report (answers "does Generate call `create_snapshot` with the richer PDF?"):** no change to P3-2. `reports.download_pdf` passes `report_findings=report_content.assessment_findings(db, assessment)` to `generate_pdf`. P3-2's `snapshots._render` already obtains gap-report bytes by calling `reports.download_pdf`, so **every new `gap_report` snapshot contains the Findings section automatically**, and every earlier snapshot keeps its old bytes forever (D-P3-2-A). `app/routers/snapshots.py` and `pages/report_snapshots.html` are **not modified**.

**Integrated report:** there is **no live, unversioned integrated route**. The consultant generates a draft snapshot, views it through the file route and issues it. *Why:* it is a new client deliverable with no legacy link to keep working; a draft snapshot is the preview; and a GET that renders from live data would be a second, unversioned client-facing document (the exact ambiguity P3-2 kept out of the assessment routes). Generation is a POST (the D-P3-2-D reasoning).

**Additions to `app/services/report_snapshots.py`** (the P3-2 hand-forward: "a sibling of `create_snapshot` reusing the same private write-and-record helper"):
- `ENGAGEMENT_SNAPSHOT_TYPES = ("integrated_report",)`.
- **Extract** the write-then-record body of `create_snapshot` into one private helper, `_store(db, *, snapshot_id, snapshot_type, fmt, storage_path, content, actor, assessment_id, engagement_id, review_status, source) -> ReportSnapshot`. It computes the digest, calls `_write_file`, then inside `try:` adds `ReportSnapshot(id=…, assessment_id=…, engagement_id=…, type=…, format=…, storage_path=…, is_issued=False)` and the generated event (the same ten metadata keys, `schema_version=MANIFEST_SCHEMA_VERSION`), flushes and returns; `except Exception:` `path.unlink(missing_ok=True)` and re-raises. `create_snapshot` keeps its validation, id minting, path and `source_manifest` call (before the write) and then calls `_store`. **Its behaviour, messages and event metadata are unchanged** (P3-2's suite must pass unmodified). After the refactor the module still has exactly one `.open(` and exactly one `.unlink(`.
- No new path helper: integrated files use the existing `storage_path_for(snapshot_id=…, fmt="pdf", engagement_id=engagement.id)`.
- `create_engagement_snapshot(db, *, engagement, content, actor, source) -> ReportSnapshot`: non-empty `content` (else `InvalidSnapshot("Rendered report was empty; nothing was saved.")`), mint the id, build the engagement path, then `_store(..., snapshot_type="integrated_report", fmt="pdf", assessment_id=None, engagement_id=engagement.id, review_status=None, source=source)`.
- `load_engagement_snapshot(db, *, engagement_id, snapshot_id) -> ReportSnapshot`: `ReportSnapshot.id == snapshot_id`, `engagement_id == engagement_id`, `assessment_id IS NULL`, `type == "integrated_report"`; else `SnapshotNotFound("Report version not found.")`. An assessment snapshot's id can never be loaded here, and vice versa.
- `engagement_snapshot_rows(db, engagement, *, current_source: dict | None) -> list[SnapshotRow]`: the engagement's `integrated_report` rows with `assessment_id IS NULL`, ordered by `rowid`, returned **newest first**, with the same `state` / `sequence` / `is_current_issue` / `issuable` / `generated_by` / `issued_by` / `issued_at` rules as `snapshot_rows`. `source_changed = current_source is not None and metadata.get("source") != current_source`. Share the per-row building with `snapshot_rows` by extracting one private helper, `_build_rows(snapshots, generated_by_id, issued_by_id, current_source) -> list[SnapshotRow]` (oldest-first in, newest-first out); `snapshot_rows` must return exactly what it returns today.
- `issue_snapshot` is **reused unchanged** for integrated rows (`ISSUE_SQL` already scopes by engagement when `assessment_id IS NULL`; P3-2 scenario 11 pins it).

**The integrated `source` manifest** (built by `report_content.integrated_report` as `IntegratedReport.source`; it is the only builder):
```jsonc
{
  "assessments": [                         // included, sorted by assessment_id
    {"assessment_id": "<id>", "gap_report_id": "<id>", "conclusion_versions": [["<cid>", 3], ...]}
  ],                                       // each entry = {"assessment_id": id, **report_snapshots.source_manifest(db, a)}
  "excluded_assessment_ids": ["<id>", ...],   // sorted
  "finding_ids": ["<id>", ...]                // every included ReportFinding id across sections, sorted
}
```

### D-P3-3-I. Routes (exact)

| Method + path | Handler | Module | Purpose |
|---|---|---|---|
| `GET /engagements/{engagement_id}/integrated-reports` | `integrated_reports_page` | `app/routers/web.py`, directly after `engagement_detail` | The integrated-report versions page |
| `POST /api/engagements/{engagement_id}/integrated-reports` | `generate_integrated_report` | `app/routers/integrated_reports.py` (new) | Generate a draft. Form field `reviewer_name` |
| `POST /api/engagements/{engagement_id}/integrated-reports/{snapshot_id}/issue` | `issue_integrated_report` | `app/routers/integrated_reports.py` | Issue. Form field `reviewer_name` |
| `GET /api/engagements/{engagement_id}/integrated-reports/{snapshot_id}/file` | `integrated_report_file` | `app/routers/integrated_reports.py` | Stream the stored, hash-checked bytes |

These are the **only** routes this task adds. `router = APIRouter(prefix="/api/engagements", tags=["integrated-reports"])`, registered in `app/main.py` with `app.include_router(integrated_reports.router)` directly after `app.include_router(snapshots.router)`, and `integrated_reports` added to the `from app.routers import (…)` list in alphabetical position. **No path contains `/snapshots`, `/findings`, `/conclusions` or `/workpaper`**, so every existing route-set guard stays exact. The P3-2 assessment route's refusal of `type=integrated_report` ("Integrated engagement reports are not available yet.") is **left unchanged**; that route is assessment-scoped by design, and P3-2 scenario 9 asserts the message (open question 3).

Handler shape copies P3-2 exactly: **sync `def`**, `reviewer_name: str = Form("")`, a local `_error(status_code, message)` (JSON `{"detail": …}`, URL-encoded `X-Toast-Message`, `X-Toast-Type: error`), every error path calls `db.rollback()` first, success is `JSONResponse({"snapshot_id", "type", "is_issued"})` with `HX-Redirect: /engagements/{engagement_id}/integrated-reports`, `X-Toast-Message` ("Draft version generated" / "Version issued") and `X-Toast-Type: success`. Actor: `conclusion_review.reviewer_actor(reviewer_name)`. Import modules, not functions: `from app.utils import pdf_export`, `from app.services import report_content, report_snapshots`.

**Generate (exact order):**
1. `engagement = db.get(Engagement, engagement_id)`, else 404 `"Engagement not found"`.
2. `data = report_content.integrated_report(db, engagement)`. If `data.sections == []`: 400 `NO_INCLUDED = "No assessment in this engagement is approved for release with a report. Nothing was generated."`.
3. `content = pdf_export.generate_integrated_pdf(data)`.
4. `snapshot = report_snapshots.create_engagement_snapshot(db, engagement=engagement, content=content, actor=…, source=data.source)`; a `SnapshotError` maps to its status and message.
5. `db.commit()`. If it raises: `db.rollback()`, `report_snapshots.snapshot_path(snapshot).unlink(missing_ok=True)`, and 500 `"The report version could not be saved. Try again."` (the P3-2 rule). That is this router's **only** `.unlink(`.

**Issue (exact order):**
1. Engagement 404. `snapshot = load_engagement_snapshot(...)` (404).
2. **Release gate:** read the snapshot's generated event (`report_snapshots.generated_event`). Every `assessment_id` in `source["assessments"]` must still exist and have `review_status == "approved"`; otherwise 403 `INTEGRATED_NOT_RELEASABLE = "Every assessment in this version must still be approved for release before it can be issued."`. Nothing is written.
3. `report_snapshots.issue_snapshot(db, snapshot, actor=…)` (integrity, `ISSUE_SQL`, issued event; 409/500 as in P3-2).
4. `db.commit()`.

**File:** engagement 404; `load_engagement_snapshot` 404; `read_snapshot_bytes` (500 on integrity failure); `Response(content, media_type="application/pdf")` with `X-Snapshot-Sha256` and `Content-Disposition: attachment; filename="{safe_client}_integrated_report_v{sequence}_{snapshot.id[:8]}.pdf"`, where `safe_client = re.sub(r"[^A-Za-z0-9._-]+", "_", client.name).strip("_") or "report"` and `sequence` comes from `engagement_snapshot_rows(..., current_source=None)`. No release gate on reading (the D-P3-2-G reasoning). Never re-render.

### D-P3-3-J. The page: `pages/integrated_reports.html`

Extends `base.html`. Context: `engagement`, `client`, `data` (the `IntegratedReport` from `report_content.integrated_report`, used both for the preview lists and for `current_source`), `rows` (`engagement_snapshot_rows(db, engagement, current_source=data.source)`), `reviewer_name` (`rows[0].generated_by` when rows exist and it is not `None`, else `""`).
- `{% block title %}Integrated reports — {{ engagement.name }}{% endblock %}`; breadcrumb `Portfolio / {{ client.name }} / {{ engagement.name }} / Integrated reports` in the `engagement_detail.html` style.
- `<h1>` "Integrated engagement report". Subtitle: "One report with a separate section for each assessment approved for release. Scores are shown per assessment and framework and are never combined. Generating creates a new draft version; issuing makes it permanent."
- The page-level `<input id="reviewer-name" name="reviewer_name" placeholder="Your name" value="{{ reviewer_name }}">`.
- `<h2>` "Included assessments", one `<li data-included-assessment>{{ section.label }}</li>` per `data.sections`, or "No assessment is approved for release yet."; `<h2>` "Not included", one `<li data-excluded-assessment>{{ row.label }}: {{ row.reason }}</li>` per `data.excluded` (omit the block when empty).
- A generate form `<form hx-post="/api/engagements/{{ engagement.id }}/integrated-reports" hx-include="#reviewer-name">` with submit "Generate new version".
- "No versions generated yet." when `rows` is empty; otherwise a table, newest first, one `<tr data-integrated-row data-snapshot-id="{{ row.snapshot.id }}" data-snapshot-state="{{ row.state }}">` per row, with the P3-2 columns: `v{{ row.sequence }}`, the state label (`Draft`, `Draft (superseded)`, `Issued`, `Issued (current)`), generated at/by, issued at/by, SHA-256 first 12 characters (full hash in `title`), size in KB, "Source data changed since generation" when `row.source_changed`, a "Download" link to `…/integrated-reports/{{ row.snapshot.id }}/file`, and for issuable rows only `<form data-issue-control hx-post="/api/engagements/{{ engagement.id }}/integrated-reports/{{ row.snapshot.id }}/issue" hx-include="#reviewer-name" hx-confirm="Issue this version? Issued versions are permanent and cannot be changed or withdrawn.">` with submit "Issue".
- Everything autoescaped. **Never `|safe`.** No `overall_score`, no `CyberAssess`.

`web.integrated_reports_page`: `db.get(Engagement, …)` → 404 `"Engagement not found"`; `db.get(Client, engagement.client_id)` → 404 `"Client not found"`; never commits. Import `from app.services import report_content` (and reuse the existing `report_snapshots` import).

**`pages/engagement_detail.html`:** directly after the `<p class="mt-2 text-sm text-gray-500 dark:text-gray-400">{{ client.name }} · …</p>` line, add `<a href="/engagements/{{ engagement.id }}/integrated-reports" class="mt-2 inline-block text-sm font-medium text-brand dark:text-navy-300 hover:underline">Integrated reports →</a>`. Nothing else changes.

### D-P3-3-K. Consistency audit of this spec (the P2-4 lesson, done in advance)

P2-4's handoff mandated a field name its own grep forbade. Every mandated string, identifier and path here has been checked against every structural assertion in this document and in the existing suite:

1. **Legacy-consumer grep** (`Conclusion|AnalysisRun|analysis_pipeline`, case-sensitive) over `pdf_export.py` and `reports.py`. Every mandated identifier and string that lands in those two files is checked: `report_findings`, `_render_findings_section`, `_draw_finding_detail`, `generate_integrated_pdf`, `report_data`, `report_content`, `decision_label`, `decided_by`, `decided_at`, `decision_version`, `outcome_label`, `workpaper_ref`, `citations_captured`; and the strings "Approved Findings", "Findings and Evidence Chain", "Each finding below is bound to an individually approved requirement decision…", "finding(s) not shown: their source decision is not a current individual consultant approval.", "Decision: … record v…", "Evidence chain:", "Evidence support not captured (legacy)", "Integrated Engagement Report", "Framework Scores (this assessment only)", "Assessments Not Included". **None contains `Conclusion`.** The data classes live in `report_content.py`, which the grep doesn't cover. Do not write the word with a capital C in either file, including comments ("source decision", never "source Conclusion").
2. **Blended-score AST guard.** It flags `.overall_score` attributes and `overall_score=` keywords in `app/**/*.py`. The mandated field is `ScoreLine.score`, and `report_content` reads the JSON with subscripts only. **Never** write `ScoreLine(overall_score=…)`, `line.overall_score` or `SomeDataclass(overall_score=…)` in any new or changed app file. The integrated template must not contain the literal `overall_score` (the template grep).
3. **"Overall Score" text.** Neither PDF prints "Overall" in any new string. The mandated cover sentence says "Scores are never combined", not "overall".
4. **P3-2 service guards** on `report_snapshots.py` after the D-P3-3-H additions: `.open(` count stays 1 (only `_write_file`), `.unlink(` count stays 1 (only `_store`), no `write_bytes(` etc., no `delete` in any case (comments and docstrings included; say "superseded"), no `.is_issued =` assignment (`ReportSnapshot(..., is_issued=False)` is a keyword argument and is allowed), no `update(ReportSnapshot`, no `.commit(`.
5. **P3-2 router guard** covers `app/routers/snapshots.py` only, which is not modified. The new router gets the same checks in this task's scenario 10: exactly one `.unlink(`, no `delete`, no `.is_issued =`, no `SET is_issued = 0`.
6. **Route-set guards.** `/integrated-reports` doesn't contain `/snapshots`, `/findings`, `/conclusions` or `/workpaper`, so P3-2 scenario 12, P3-1 scenario 11, P2-4 scenario 12 and P2-6 scenario 9 stay exact. This task's own guard pins the `/integrated-reports` set to the four in D-P3-3-I.
7. **P3-2 scenario 9** still gets "Integrated engagement reports are not available yet." from the unmodified assessment route.
8. **Golden/white-label PDFs.** `generate_pdf` called without `report_findings` (as `tests/test_golden_dpdpa.py`, `tests/test_white_label.py`, `tests/test_no_blended_scoring.py` and `tests/support/fixture_capture.py` do) takes no new branch. The integrated cover uses `settings.firm_name`, never a product name.
9. **PDF text vs assertions.** Extracted PDF text wraps lines and may collapse spaces. Tests normalise with `" ".join(text.split())` and assert only **short** tokens (ids, titles, the 16-character hash prefix, short excerpts, section titles). All mandated PDF strings are ASCII, so `S()` passes them through unchanged. `Closed and verified` (an action label) doesn't collide with any asserted section title.
10. **HTML exact-text assertions.** The page's mandated texts contain no `&`, `<`, `>` or quotes. `data-included-assessment` and `data-excluded-assessment` don't contain each other; `data-integrated-row` appears only on version rows; `data-issue-control` only on issuable rows.
11. **Actor prefix.** The raw `consultant:` prefix is never rendered on the page or in the PDF (`decided_by` comes from `last_decision["actor_display"]`; page actors from `SnapshotRow`).

## Required approach

### 1. `app/services/report_content.py` (new): D-P3-3-B … H

### 2. `app/utils/pdf_export.py`: D-P3-3-F, additions only

### 3. `app/routers/reports.py`

In `download_pdf`, after `answer_source_map` is built and before `generate_pdf`, add `report_findings = report_content.assessment_findings(db, assessment)` and pass `report_findings=report_findings` as the last keyword argument. Add the import. Nothing else in the file changes.

### 4. `app/services/report_snapshots.py`: D-P3-3-H (the `_store` and `_build_rows` extractions, and the three engagement functions)

### 5. `app/routers/integrated_reports.py` (new) and `app/main.py`: D-P3-3-I

### 6. `app/routers/web.py` and templates: D-P3-3-J (`integrated_reports_page`, `pages/integrated_reports.html`, the `engagement_detail.html` link)

### 7. `tasks/todo.md`

Change the P3-2 line's "**PR #31, open, not yet merged.**" to "**Merged: PR #31.**", and update the P3-3 line with its status and a link to this handoff's Results.

### 8. If a circular import appears

`report_content` imports `findings` → `conclusion_review`/`workpaper`/`analysis_pipeline`, and `reports.py` imports `report_content`. If that creates an import cycle, **stop and report it** in Results with the traceback. Do not move the import inside the function or restructure modules without a decision.

### 9. `tests/test_pdf_updates.py` (new)

Copy (don't import) from `tests/test_findings.py`: the Alembic-built `db_path` / `engine` / `db` fixtures, `http`, `gate`, `_register_frameworks`, `REQS`, `_seed`, `_item`, `_stub_single`, `_run_one`, `_revisions`, `_url`, `_decide`, `_approve`, `_create`. From `tests/test_workpaper.py`: `_stub_multi`, `_add_evidence`, `_cite_revision`. From `tests/test_report_snapshots.py`: the autouse `upload_root` fixture (**no test may write under the real `uploads/`**). Extend `_seed` with `frameworks=` and an `engagement=` keyword so several assessments can share one engagement.

Helpers:
- `_pdf_text(content: bytes) -> str`: pdfplumber over all pages, joined, then `" ".join(text.split())`.
- `_approved_finding(db, http, gate, monkeypatch, assessment, conclusion, *, excerpt="Grounded quote")`: `_add_evidence` + `_cite_revision` on the proposal, `approve` through the P2-4 route, `_create` through the P3-1 route; returns the Finding.
- `_set_scores(db, assessment, {framework_id: score})`: overwrite the assessment's `GapReport.framework_scores` with `json.dumps({fw: {"overall_score": s, "overall_rating": "Partially Compliant", "domain_scores": {}}})` (the dict literal key is a string in a test file; the AST guard only scans `app/`).

Use the **real** `generate_pdf` / `generate_integrated_pdf` everywhere except where a scenario says otherwise. Every scenario is one or more test functions whose docstrings start with `Scenario N:`.

## Key files

| File | Why it matters |
|---|---|
| `app/services/report_content.py` (new) | All Finding/citation/scope reading; plain dataclasses (D-P3-3-B … H). |
| `app/utils/pdf_export.py` | One new keyword, one new call, three new functions. **Zero removed lines** (D-P3-3-F). |
| `app/routers/reports.py` | One import, one call (D-P3-3-H). |
| `app/services/report_snapshots.py` | `_store`/`_build_rows` extraction plus engagement generator, loader and rows (D-P3-3-H). |
| `app/routers/integrated_reports.py` (new), `app/main.py` | Three engagement API routes (D-P3-3-I). |
| `app/routers/web.py`, `pages/integrated_reports.html` (new), `pages/engagement_detail.html` | Page and link (D-P3-3-J). |
| `app/services/findings.py`, `conclusion_review.py`, `workpaper.py`, `citations.py`, `app/routers/snapshots.py`, `pages/report_snapshots.html` | Reused; **not modified**. |
| `app/models/*`, `alembic/versions/*` | **Not modified.** No schema change. |
| `tests/test_pdf_updates.py` (new) | The contract. **No existing test file is modified.** |

## Non-goals

- **No change to any existing PDF page**, string or helper, and no removal of the `GapItem` appendix. The Methodology wording is not edited.
- No score of any kind in the Findings section; no engagement-level score, average or comparison (D-P3-3-G).
- **No live integrated route**, no HTML integrated report, no RFI snapshot (P3-2 open question 2).
- No closure-evidence rendering for Actions (P3-4 adds closure evidence to `history_json`; rendering it in the PDF is a follow-up, open question 4). Actions show title, owner, target and status only.
- No schema change: no period, cut-off or exclusions columns (open question 1), no hash or issued columns.
- No change to `findings.py`, P2-4/P2-6 services, `snapshots.py`, the Report tab, the portfolio dashboard, or `app.js`. No `relationship()`.
- No reading of `audit_events` for Findings' `finding_created` binding (the card's current version is printed; open question 2).

## Test scenarios

All in `tests/test_pdf_updates.py`. "Nothing written" means these are unchanged against a pre-request snapshot: `COUNT(*)` of `report_snapshots` and `audit_events`; every snapshot's `(id, is_issued, storage_path)`; the set of files under `upload_root / "reports"`.

1. **The plan's test: multi-framework assessment PDF with per-framework scores, citations and no blended score.**
   - `_seed(frameworks=["dpdpa", "iso27001"], applicable=[REQS[0], iso_req])` where `iso_req` is the first `iso27001` control id from the registry. `_stub_multi` gives `_item(REQS[0], "non_compliant", risk="high")` for `dpdpa` and `_item(iso_req, "partially_compliant", risk="medium")` for `iso27001`. Run `gate.trigger_analysis`.
   - `_approved_finding` on both Conclusions, with excerpts "Grounded quote" and "Second quote" (two `_add_evidence` rows; `_add_evidence`'s hash is `"a" * 64`, so give the second `EvidenceVersion` `file_hash_sha256 = "b" * 64`). Set `review_status = "approved"`.
   - `GET /api/assessments/{id}/report/pdf` → 200, `application/pdf`. `_pdf_text` contains: "Framework Scores"; both framework display names; for each framework in `report_framework_scores(report, assessment)`, `f"{score:.0f}%"`; "Approved Findings"; both Finding titles; both requirement ids; "Grounded quote" and "Second quote"; "a" * 16 and "b" * 16; "policy.pdf v1"; `f"Workpaper ref: wp-dpdpa-{REQS[0]}"`; "Approved by Priya". It does **not** contain "Overall Score".
   - Ordering: the index of "Approved Findings" is after "Detailed Gap Findings" and before "Scope & Limitations"; the DPDPA Finding's title comes before the ISO Finding's title.
2. **Inclusion rules (D-P3-3-D)** through `report_content.assessment_findings` and the PDF.
   - An approved Finding, then P2-4 `reopen` of its source: `assessment_findings(...).findings == []`, `omitted_count == 1`, and the PDF contains "1 finding(s) not shown" and not the Finding's title.
   - A hand-inserted migrated-shape Finding whose Conclusion has a legacy bulk approval (`_human_revision(…, "approved", actor="Manager Review")`) is omitted and counted.
   - An **edited** source (`_decide(..., "edit")`) is included with "Edited and approved".
   - `assessment_findings` calls `findings.findings_page` exactly once (spy through the module attribute).
   - Two Findings in one framework, severities `low` then `critical` by creation order: the critical one is `F1`.
3. **No Findings, no section; byte-level additivity of existing pages.**
   - `generate_pdf(report, items, name, …)` with `report_findings=None` and with `AssessmentFindings([], 0)`: neither text contains "Approved Findings", and both have the same page count as a call without the keyword.
   - The page count with one included Finding is strictly greater.
   - `inspect.signature(pdf_export.generate_pdf)`: parameter names in order are exactly `report, gap_items, company_name, initiatives, answer_source_map, selected_frameworks, assessment, report_findings`, and `report_findings` defaults to `None`.
4. **Gap-report snapshots pick up the new section automatically; old snapshots don't change (D-P3-3-H).**
   - With the real renderer and `review_status = "approved"`: `POST /api/assessments/{id}/snapshots type=gap_report` **before** any Finding exists → v1; its file text has no "Approved Findings".
   - Create an approved Finding; generate v2 → v2's text contains the Finding title and its citation excerpt.
   - v1's bytes and `X-Snapshot-Sha256` from `GET …/file` are unchanged; the two sha256 values differ.
5. **Integrated report, happy path.**
   - One engagement with three assessments: **A** (`["dpdpa"]`), **B** (`["dpdpa", "iso27001"]`) and **C** (`["dpdpa"]`, `review_status = "pending"`). Run the pipeline on all three, give A and B one approved Finding each (distinct titles), and set A and B `review_status = "approved"`. `_set_scores`: A `{"dpdpa": 100.0}`, B `{"dpdpa": 40.0, "iso27001": 60.0}`.
   - `POST /api/engagements/{e}/integrated-reports reviewer_name=Priya` → 200, `HX-Redirect == f"/engagements/{e}/integrated-reports"`, body `type == "integrated_report"`, `is_issued` false.
   - One `ReportSnapshot` row: `assessment_id is None`, `engagement_id == e`, `format == "pdf"`, `storage_path == f"reports/engagements/{e}/{sid}.pdf"`; the file exists.
   - The generated event's metadata key set equals P3-2's ten keys exactly; `assessment_id is None`, `review_status is None`, `actor == "consultant:Priya"`; `source["assessments"]` lists exactly A and B (sorted by id), each equal to `{"assessment_id": id, **report_snapshots.source_manifest(db, x)}`; `source["excluded_assessment_ids"] == [C.id]`; `source["finding_ids"]` is the two Finding ids, sorted.
   - `GET …/{sid}/file` → 200, `application/pdf`, `X-Snapshot-Sha256` equal to the file's hash. Its text contains "Integrated Engagement Report", both A's and B's labels, "Framework Scores (this assessment only)", "100%", "40%", "60%", both Finding titles, "Assessments Not Included", C's label and "Not approved for release", and "Assessment period and evidence cut-off: not recorded". **No blending:** the text contains none of "67%", "50%", "70%" or "Overall". A's Finding title appears after A's label and before B's label.
6. **Integrated lifecycle and release gate.**
   - Generate twice: two rows, states newest-first `["draft", "superseded_draft"]`. Issuing the older → 409 with the P3-2 "newer version" message, nothing written. Issuing the newer → 200.
   - Generate v3, set A `review_status = "pending"`, issue v3 → 403 `INTEGRATED_NOT_RELEASABLE` (via `unquote` of the toast too), nothing written. Set A back to `"approved"` → issue v3 → 200, and only v3 has `is_current_issue`.
   - A later Finding creation marks v3 `source_changed` on the page's rows, and v3's file bytes are unchanged.
7. **Validation and scoping.** Each writes nothing:
   - an unknown engagement → 404 on the page and all three API routes;
   - an engagement whose only assessment is not approved → generate 400 `NO_INCLUDED`;
   - an engagement with an approved assessment that has no `GapReport` → generate 400 `NO_INCLUDED`, and the page lists it under "Not included" with "No analysis report yet";
   - another engagement's integrated snapshot id → 404 on `issue` and `file`; an **assessment** snapshot's id (from P3-2's route) → 404 on the engagement `file` route.
8. **Page render.**
   - Empty: 200, "No versions generated yet.", the included and excluded lists (`data-included-assessment` count 2, `data-excluded-assessment` count 1 for scenario 5's setup).
   - After scenario 6's sequence: `data-integrated-row` count 3; labels `Issued (current)`, `Issued` or `Draft (superseded)` as applicable; one file link per row; `data-issue-control` count 0 while the newest is issued, and 1 after another generate.
   - `"consultant:Priya" not in page` and `"Priya" in page`.
   - An engagement named `<script>x</script>` renders escaped.
   - `GET /engagements/{e}` contains `href="/engagements/{e}/integrated-reports"`.
9. **Failure cleanup.**
   - Monkeypatch `app.services.report_snapshots._record_event` to raise `RuntimeError("boom")`: the generate POST raises (wrap in `pytest.raises(RuntimeError)`); after `db.rollback()` there is no row and no file under `reports/engagements/`.
   - Monkeypatch the test `db`'s `commit` to raise once: generate → 500 "The report version could not be saved. Try again."; after `db.rollback()`, no row and no file.
   - `create_engagement_snapshot` with `content=b""` raises `InvalidSnapshot`.
10. **Structural guards.**
    - The set of `(method, path)` over app routes whose path contains `/integrated-reports` equals exactly the four in D-P3-3-I.
    - `app/routers/integrated_reports.py`: `.unlink(` count 1; `"delete" not in source.lower()`; no match for `\.is_issued\s*=(?!=)` or `SET\s+is_issued\s*=\s*0` (case-insensitive); `.commit(` present. `app/services/report_content.py`: none of `db.add(`, `db.add_all(`, `db.merge(`, `.flush(`, `.commit(`, and no `delete`. `inspect.getsource(web.integrated_reports_page)` has no `.commit(`.
    - `app/services/report_snapshots.py`: `.open(` count 1, `.unlink(` count 1 (re-asserted here because this task edits the file).
    - `grep -nE "Conclusion|AnalysisRun|analysis_pipeline"` over `app/utils/pdf_export.py` and `app/routers/reports.py` is empty (re-asserted; the standing guard also covers it).
    - `pages/integrated_reports.html` doesn't match `overall_score|CyberAssess|\|\s*safe\b`.
    - `git diff` additivity is in Done criteria, not in pytest.
11. **Sanitiser and wrapping.** A Finding titled `Policy “review” – owner’s sign-off…` and a 2,500-character description and excerpt render without an exception; the text contains `Policy "review"` and the truncated excerpt ends with `...`.
12. **Nothing else moved.** `tests/test_report_snapshots.py`, `tests/test_findings.py`, `tests/test_no_blended_scoring.py`, `tests/test_analysis_pipeline.py`, `tests/test_golden_dpdpa.py`, `tests/test_white_label.py` and `tests/test_workpaper.py` pass **unmodified** (the full-suite run).

## Done criteria

- `tests/test_pdf_updates.py` passes. `.venv/bin/pytest -q` passes in full: **477 + N**, where N is the number of new cases. **No existing test file is modified.** (In a fresh `git worktree`, expect the known one-time `_guard_dev_database_untouched` teardown error described in the P2-3 handoff; nothing else.)
- `git diff main -- app/utils/pdf_export.py | grep -E '^-[^-]'` prints **nothing** (additive only).
- `git diff --stat main` shows changes **only** in: `app/services/report_content.py` (new), `app/utils/pdf_export.py`, `app/routers/reports.py`, `app/services/report_snapshots.py`, `app/routers/integrated_reports.py` (new), `app/main.py`, `app/routers/web.py`, `app/templates/pages/integrated_reports.html` (new), `app/templates/pages/engagement_detail.html`, `tests/test_pdf_updates.py` (new), `tasks/todo.md` and this handoff.
- `git diff --stat main -- app/services/findings.py app/services/conclusion_review.py app/services/workpaper.py app/services/citations.py app/routers/snapshots.py app/templates/pages/report_snapshots.html app/models alembic/versions` is empty. `alembic heads` is still exactly `4e8c1a9d2b57`. `grep -rn "relationship(" app/models/` is empty.
- **Smoke test** (per the project rule; record the outputs). A fresh Alembic-built DB and a temporary `upload_dir`, with the in-process ASGI `TestClient` if a socket bind is refused. Patch `app.routers.analysis.run_multi_framework_analysis` (and `run_gap_analysis` for single-framework assessments) to fixed items. Use the **real** renderers. Then:
  1. One engagement with two assessments (one `dpdpa + iso27001`, one `nist_csf`), each with two approved gap Conclusions with citations and a Finding each (via the P3-1 route), both `review_status = "approved"`.
  2. `GET /api/assessments/{id}/report/pdf` for the multi-framework one: save it, record the page count and paste the extracted text of the "Approved Findings" pages.
  3. Generate a `gap_report` snapshot (P3-2 route) and confirm its file text contains the same Findings section.
  4. Generate and issue an integrated report; paste `SELECT type, format, is_issued, assessment_id, engagement_id, storage_path FROM report_snapshots WHERE engagement_id = ? ORDER BY rowid` and the extracted text of its first two sections. Confirm by eye that no score appears outside its assessment's section.
  5. **Leave the two PDFs** (the live gap report and the issued integrated report) in a path you name in Results, so Claude can review the rendered output (the ownership row's "Claude reviews rendered output").
  6. **Browser check**, if a browser is available: engagement page → "Integrated reports →" → generate → Download → issue (confirm dialog shown). If no browser is available, say so in Results. Do not claim it.

## Rollback

- **Code:** `git revert`. No schema change. Integrated `report_snapshots` rows, their `audit_events` and their files under `upload_dir/reports/engagements/` remain as inert history that the reverted app never lists; backups keep covering them. The gap report reverts to its pre-P3-3 content for new renders; existing snapshots keep whatever bytes they were generated with.
- **Data:** nothing deletes or rewrites. The only in-place write is P3-2's `is_issued` 0 → 1 through `ISSUE_SQL`. Do not "undo" an issue by editing the row; generate and issue a corrected newer version.

## Open questions (deliberately flagged, not resolved here)

1. **Assessment period, evidence cut-off and exclusions rationale** (PR-053) have no columns. The integrated report prints "not recorded". Adding them is a Claude-owned schema change, with capture UI at scoping time.
2. **Finding-to-revision binding in the PDF.** The PDF prints the source's **current** version (`record vN`) and last decision. P3-1's `finding_created` audit event records the version and revision the Finding was created from. If they differ (reopened and re-approved since), the PDF shows the current approval, which is what PR-052 requires, but not the original binding. Printing both is a small follow-up.
3. **Stale wording on the assessment snapshot route.** `POST /api/assessments/{id}/snapshots type=integrated_report` still answers "Integrated engagement reports are not available yet." (P3-2 scenario 9 asserts it). A follow-up could reword it to point to the engagement page, updating that assertion in the same PR.
4. **Closure evidence in the PDF.** After P3-4, `closed`/`verified` history entries carry an `evidence` object. Showing "closed with evidence X, verified by Y" per Action in the Findings section is a natural follow-up once P3-4 merges.
5. **Findings from compliant Conclusions** (P3-1 open question 2) remain out; the section is gaps only because Findings are.

## Results

_To be completed by the implementer: what was built, the full-suite count, the smoke-test outputs and the path of the two PDFs left for review, and any deviation (there should be none; if the code forced one, describe it and stop)._
