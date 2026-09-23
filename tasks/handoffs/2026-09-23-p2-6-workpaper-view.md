# P2-6: Workpaper view: a read-only, per-requirement traceability page from response to evidence to proposal to decision

**Plan:** `docs/plans/2026-09-21-002-revised-implementation-plan.md`, Phase 2, task P2-6 ("New route: `/assessments/{assessment_id}/workpaper`"; "For each applicable requirement: shows client response, evidence, citations, AI proposal, consultant decision, revision history"; "Read-only traceability view"; test: "Assessment with approved conclusions renders workpaper. '3 clicks from Finding to full history' acceptance criterion (P7 fix)"), and the Phase 2 exit criterion "Workpaper view renders complete evidence → conclusion → revision chain". **P7** in `tasks/2026-09-21-adversarial-review.md` gives the exact criterion: "A reviewer can navigate from a Finding to its Conclusion's full proposal/edit/approval history in three or fewer clicks." PRD `docs/product/2026-09-21-cyberassess-product-requirements.md`: **PR-055** ("the Workpaper provides direct navigation Finding → Conclusion revision → claim/Citation → Evidence version and shows all actors/timestamps"), **PR-044** ("the Workpaper preserves proposal, every edit, actor, timestamp, decision, and approval"), **PR-022** (quality dimensions "visible separately"), and the "Complete the assessment workpaper" journey step 2. Open questions handed to this task: P2-3 open question 5 (stale `running` runs) and P2-4 open questions 1 and 3 (rejection notes; edit-then-citation display). All are closed or explicitly deferred below.
**Owner:** Codex, from this Claude spec (per `tasks/agent-ownership.md`: "P2-6 Workpaper view | Codex, from Claude spec"). Every architectural fork is closed below. **If the code forces a deviation from any decision, stop and report it in `## Results`. Do not pick an alternative.** Merge gate: a Claude review of the diff. `tasks/todo.md` tags Phase 2 `[AR: evidence lifecycle, citations, immutable analysis, approvals, magic links]`; the workpaper is not one of the named concerns *provided* it stays read-only and does not modify the P2-3/P2-4 services, which D-P2-6-H and the Done criteria pin.
**Depends on:** all of P2-1 … P2-5, **all merged**: P2-1 PR #24, P2-2 PR #25, P2-5 PR #26, P2-3 PR #27, P2-4 PR #28 (merge commit `6d21242`, the tip of `main`). (`tasks/todo.md`'s P2-4 line still says "Awaiting Claude adversarial review before merge". That line is stale; update it as part of this task, see Done criteria.)
**Blocks:** Phase 3. P3-1 (Findings UI must link each Finding to the workpaper entry of its Conclusion, see "Handed forward") and P3-2 (the `report_snapshots` `type = "workpaper"` snapshot should serialize this task's read model).
**Failing contract suite: none pre-written.** A grep of `tests/` and `app/` for `P2-6` and `workpaper` (case-insensitive) finds **nothing**. As with P2-4, **Codex writes `tests/test_workpaper.py` itself** from the scenarios in `## Test scenarios`, following the fixture pattern of `tests/test_conclusion_approval.py` (step 7). Every scenario listed is required. You may add cases, but you may not drop or weaken one.

## Goal

A reviewer opens one page per assessment, `/assessments/{assessment_id}/workpaper`, and sees, for every requirement the assessment concluded on, grouped by framework, in one place and without clicking further:

1. the **client's questionnaire response** for that requirement;
2. the **evidence**: documents explicitly mapped to the requirement, and the desk-review findings about it, each with resolved citations;
3. the **AI proposal**: what the model claimed, with its quality flags and the exact citations to immutable evidence versions, and which run and model produced it;
4. the **consultant decision**: the current content of the Conclusion, its decision state, lock state and last decision;
5. the **full revision history**: every `ConclusionRevision`, oldest first, with actor, timestamp, action, the outcome before and after, and, for proposals, the run, the claim and its citations.

Every citation links to `/evidence/{evidence_id}`, which already shows each version's full SHA-256. A finding in the report links straight to its requirement's entry. The page writes nothing, and has no controls that write anything.

## Current state

Grounded against `6d21242` on `main`. Baseline `.venv/bin/pytest -q` → **430 passed, 111 warnings** (I ran it at `6d21242`). Re-locate everything by symbol name.

- **`app/models/conclusion.py`** (unchanged since P2-3):
  - `Conclusion`: `id`, `assessment_id` (FK, indexed), `requirement_id`, `framework_id`, `cluster_id` (nullable), `outcome`, `rationale`, `evidence_summary`, `gaps_identified`, `risk_level`, `recommended_action` (all NOT NULL), `ai_proposed`, `version` (default 1), `created_at`, `updated_at` (`onupdate`). Unique index `uq_conclusions_assessment_framework_requirement` on `(assessment_id, framework_id, requirement_id)`.
  - `ConclusionRevision`: `id`, `conclusion_id` (FK, indexed), `actor`, `action` (free text), `previous_outcome` / `previous_rationale` (nullable; the values **before** the action), `citations_json` (nullable Text), `analysis_run_id` (nullable FK → `analysis_runs.id`, indexed), `created_at`. **A revision stores the "before" values, never the result.**
  - No `relationship()` anywhere.
- **`app/models/analysis_run.py`, `AnalysisRun`**: `id`, `assessment_id` (FK, indexed), `framework_id`, `status`, `claims_json` (Text, NOT NULL), `model_id` (NOT NULL; the pipeline writes `settings.llm_model_judge`), `started_at` (NOT NULL), `completed_at` (nullable). `claims_json` is the P2-3 envelope (D-P2-3-E): keys `schema_version`, `trigger_id`, `framework_id`, `model_tiers`, `inputs` (`evidence_versions`, `legacy_document_ids`, `questionnaire_response_count`, `applicable_requirements`), `gap_report_id`, `desk_review_used`, `claims`, `error`. Each claim has `requirement_id`, `cluster_id`, `outcome`, `scope_enforced`, `item` (the analyzer item verbatim: `current_state`, `gap_description`, `risk_level`, `remediation_action`, `evidence_quote`, …), `quality` (`citation_count`, `evidence_quote_grounded` (`true`/`false`/`null`), `unsupported_assertion`, `needs_review`, `desk_review_red_flags`, `desk_review_absence`, `contradictions` (always `null`)), `conclusion_id`, `revision_id`, `disposition` (`created`/`applied`/`withheld`). **Navigation is revision → `analysis_run_id` → run → the claim whose `revision_id` equals the revision's id** (P2-3 D-P2-3-E).
- **Which revisions have a run.** Pipeline revisions (`actor = "system:analysis"`, action `proposed` or `proposal_withheld`) always carry `analysis_run_id` and a non-NULL `citations_json`. They are written in the persistence phase in the same transaction that sets the run `completed`; on any failure the phase rolls back (D-P2-3-B), so **a revision never links to a `running` or `failed` run**. Human revisions (P2-4, `actor = "consultant:…"`) and `scripts/migrate_legacy.py` revisions (`actor = "system:migration"` for `proposed`; the bare legacy `reviewed_by` name, e.g. `"Manager Review"`, for `approved`) have `analysis_run_id = NULL` and `citations_json = NULL`. **No request timeout is configured anywhere in `app/`** (`grep -rn timeout app --include="*.py"` finds only a HIPAA control tag), and P2-3 added no sweeper, so a process crash mid-LLM-call leaves a run `running` forever (P2-3 open question 5).
- **`app/services/conclusion_review.py`** (P2-4) — read in full:
  - Constants used here: `REVIEWER_ACTOR_PREFIX = "consultant:"`, `CONCLUSION_OUTCOMES`, `ALLOWED_ACTIONS`.
  - `@dataclass(frozen=True) class ConclusionCard` with fields `conclusion`, `requirement_title`, `state` (`pending`/`rejected`/`approved`/`edited`), `locked`, `allowed_actions`, `approval_blocker`, `citations_captured`, `citations` (resolved, from the **latest `proposed`** revision), `unsupported_assertion`, `last_decision` (`{"action", "actor_display", "created_at"}` or `None`), `legacy_bulk_approval`, `withheld_proposal` (`{"outcome", "rationale", "revision_id", "run_id", "created_at", "citation_count"}` or `None`), `legacy_report_status`, and `previous_outcome: str | None = None` (from the latest `edited` revision).
  - `conclusion_cards(db, assessment_id) -> list[ConclusionCard]`. It returns `[]` when the assessment or its Conclusions don't exist. It takes **no request object**, and it only reads: `db.get`, `db.execute(select(...))` for the Conclusions, their revisions (private `_revisions`, ordered `created_at, rowid`), the `AnalysisRun`s of withheld revisions and the `GapItem`s of the assessment's `GapReport`, plus `analysis_pipeline.load_conclusion_state` per framework (two SELECTs) and `resolve_citations` per card. No `add`, `flush` or `commit`. Order: frameworks in `Assessment.frameworks` order, then any other `framework_id` sorted; within a framework, registry `get_all_controls` order, unknown ids last (`_ordered_conclusions`).
  - `conclusion_card(db, *, assessment_id, conclusion_id)` calls `conclusion_cards` and picks one. `decide(...)` is the only writer of human decisions.
- **`app/routers/conclusions.py`** (P2-4): `router = APIRouter(prefix="/api/assessments", tags=["conclusions"])` with exactly four POSTs, `…/{conclusion_id}/approve|edit|reject|reopen`. **`tests/test_conclusion_approval.py::test_scenario_12_individual_only_structural_guards` asserts that the set of app routes whose path contains `/conclusions` is exactly those four plus `GET /assessments/{assessment_id}/conclusions`.** Any new route whose path contains `/conclusions` breaks it.
- **`app/routers/web.py`**: every full page lives here, rendered with the module-level `templates` (configured by `configure_templates`). `conclusions_page` (`GET /assessments/{assessment_id}/conclusions`) does `db.get(Assessment, …)` → 404 `"Assessment not found"`, then `cards = conclusion_cards(db, assessment_id)` (imported by name: `from app.services.conclusion_review import conclusion_cards`), computes `counts` (`pending`, `rejected`, `approved` = approved and not `legacy_bulk_approval`, `edited`, `legacy_bulk`) and `reviewer_name`, and renders `pages/conclusions.html` with `templates.TemplateResponse(request=request, name=…, context=…)`. `evidence_detail_page` (`GET /evidence/{evidence_id}`) renders `pages/evidence_detail.html`: metadata, a versions table with each version's full SHA-256, and the uses table (P2-1).
- **Templates:**
  - `pages/conclusions.html` groups cards under a framework heading (`{{ card.conclusion.framework_id|upper }}`) by comparing each card's `framework_id` with the previous one, and has the breadcrumb `Assessments / {{ company_name }} / Conclusions` and the empty state "No conclusions yet. Run the gap analysis first."
  - `components/conclusion_card.html`: root `<div id="conclusion-card-{{ card.conclusion.id }}" data-conclusion-card data-state=… data-version=…>`. It contains `<form hx-post=…>` action controls and hidden `expected_version` inputs. Its only outbound link is the citation filename → `/evidence/{{ citation.evidence_id }}`.
  - `partials/report_summary.html` (loaded into the Report tab by `partials/report_tab.html` via `hx-get="/assessments/{{ assessment.id }}/report-summary…"` with `hx-trigger="load"`): a **"Critical Findings"** block (`{% for item in critical_findings %}`, showing `item.requirement_title`, `gap_description`, `item.requirement_id`) and a **"Detailed Findings"** `<details>` whose `<summary>` holds "PDF Report" / "RFI" links, then a grouped branch (`{% if gap_items_by_chapter is defined %}` … `{% for item in chapter_items %}`) and a flat-table fallback (`{% for item in gap_items %}`). `web.report_summary` always passes `gap_items_by_chapter`, so the grouped branch is the live one. **No finding row links anywhere today.** Every "finding" row is a legacy `GapItem` (`item.framework_id` is nullable; NULL means DPDPA).
  - `base.html` contains one `<button>` (the theme toggle) and no `<form>` or `hx-post`.
- **"Finding" in the app today.** A `findings` table and `app/models/finding.py::Finding` (with `conclusion_id` FK) exist from P1-2, but **the only writer is `scripts/migrate_legacy.py`** and **no code in `app/` reads it** (grep for `Finding` in `app/` outside the model and `DeskReviewFinding` finds only UI strings). Findings as a product object are **P3-1**. So the only thing a reviewer sees labelled "finding" today is a `GapItem` row in the Report tab ("Critical Findings", "Detailed Findings") and the legacy review queue's cards.
- **Client responses** (`app/models/questionnaire.py::QuestionnaireResponse`): `assessment_id`, `question_id` (String 50), `answer` (CHECK: `fully_implemented`/`partially_implemented`/`planned`/`not_implemented`/`not_applicable`), `notes`, `evidence_reference`, `na_reason`, `confidence`, `cluster_id`, `answer_source` (`human`/`document`/`document_confirmed`/`human_override`/`inferred`), `submitted_at`. **No unique constraint** on `(assessment_id, question_id)`; `web.save_questionnaire_responses` updates the first match. What `question_id` holds depends on the path:
  - DPDPA-only assessments: the **requirement id** (`app/dpdpa/questionnaire.py::build_questionnaire` sets `"id": req_id`, and `save_questionnaire_responses` stores `q["id"]` from `build_adaptive_questionnaire`).
  - Every other selection: the **cluster id** (`app/services/question_engine.py::_build_multi_framework_questionnaire` sets `"id": ucc_q["cluster_id"]`). A cluster id is either a `CONTROL_CLUSTERS` id or, for an unclustered control, `f"SINGLE.{control_id}"` (`app/frameworks/cluster_engine.py::_build_singleton_cluster`).
  - `Conclusion.cluster_id` is the `CONTROL_CLUSTERS` lookup for `(framework_id, requirement_id)` (`analysis_pipeline._cluster_id`), `None` when unclustered. Today every DPDPA (41) and NIST CSF (94) control is clustered; one ISO 27001 control (`ISO.A5.32`) is not.
  - Follow-up answers are stored as `FU.{parent_id}.{n}`.
- **Scope** (`Assessment.applicable_requirements`): a JSON list of requirement ids, flat across all selected frameworks (`web.save_scope` → `compute_scope_multi`). The analysis router forces any out-of-scope item to `not_applicable` before persistence, and the pipeline records `scope_enforced = bool(applicable) and requirement_id not in applicable` on each claim. So out-of-scope requirements **do** get Conclusions (outcome `not_applicable`). NULL, unparseable or empty means "no scope restriction" to the pipeline.
- **Desk review** (`app/models/desk_review.py::DeskReviewFinding`): `id` (int), `assessment_id`, `finding_type` (`evidence`/`absence`/`signal`), `requirement_id` (nullable; NULL for cross-cutting signals), `document_id`, `content`, `severity`, `source_quote`, `source_location`, `citations_json` (NULL = not captured, pre-P2-2), `created_at`. **A desk-review re-run deletes and replaces the assessment's findings** (`app/services/desk_review.py`, the `.delete()` at line 75), so they are current-state, not history.
- **Evidence mapping** (`app/models/evidence.py::EvidenceUse`): `id`, `evidence_id`, `assessment_id`, `framework_id`, `requirement_id`, `relevance` (`primary`/`supporting`/`contextual`), `created_at`, unique on `(evidence_id, assessment_id, framework_id, requirement_id)`. P2-1 says: never read `Evidence.original_filename` etc. for current content; they are frozen v1 values.
- **`app/services/citations.py`**: `loads_citations(raw)` (`None` → `[]`; non-list → `CitationError`). `resolve_citations(db, raw)` returns `[]` **without querying** when the stored list is empty; otherwise ≤ 2 statements, and each output is the stored citation plus `resolved`, `evidence_id`, `filename` (the cited version's `original_filename`), `version_number`, `version_status`, `evidence_status`, `is_current`.
- **Standing guards that constrain this task:**
  - `tests/test_analysis_pipeline.py::test_legacy_consumers_do_not_read_the_new_tables` greps `app/services/scoring.py`, `app/routers/review.py`, `app/routers/reports.py`, `app/routers/remediation.py`, `app/utils/pdf_export.py` for `Conclusion|AnalysisRun|analysis_pipeline`.
  - `tests/test_no_blended_scoring.py::test_no_template_reads_retired_score` fails on any `overall_score` in `app/templates`, and an AST scan rejects `overall_score` attribute access in `app/**/*.py` outside an allowlist.
  - `tests/test_white_label.py::test_no_hardcoded_product_name_in_client_surfaces` fails on the literal `CyberAssess` anywhere in `app/templates/`.
  - `tests/test_conclusion_approval.py` scenario 12 (above) and its bulk-action grep (`approve all|approve selected|select all|approve framework`) over `components/conclusion_card.html`, `pages/conclusions.html`, `app/routers/conclusions.py` and `app/services/conclusion_review.py`.

## Decisions (made here so they are not relitigated)

### D-P2-6-A. One GET route in `web.py`, one read-only service module, no JSON API

| Method + path | Handler | Module |
|---|---|---|
| `GET /assessments/{assessment_id}/workpaper` | `workpaper_page` | `app/routers/web.py`, placed directly after `conclusions_page` |

This is the **only** route this task adds. There is no JSON endpoint, no HTMX partial route, and no per-requirement sub-route (the per-requirement "page" is a fragment anchor on this one page, D-P2-6-G).

- The page lives in `web.py` because every full page does (the P2-4 precedent for `conclusions_page`).
- The read model lives in a new **`app/services/workpaper.py`** (D-P2-6-B). The route: `assessment = db.get(Assessment, assessment_id)`; if `None`, `HTTPException(404, "Assessment not found")`; else `wp = workpaper.build_workpaper(db, assessment)` and render `pages/workpaper.html` with context `{"request": request, "assessment": assessment, "wp": wp}`, using `templates.TemplateResponse(request=request, name="pages/workpaper.html", context=…)` exactly as `conclusions_page` does. Import the module (`from app.services import workpaper`), not the function, so tests can spy on it.
- **Why the path must not contain `/conclusions`:** P2-4 scenario 12 pins the exact set of routes containing `/conclusions` (Current state). `/assessments/{assessment_id}/workpaper` does not contain it. Do not add, for example, `/assessments/{id}/conclusions/{cid}/history`.

### D-P2-6-B. Read model: reuse `conclusion_cards()` for the current state, add a workpaper-only read path for history and context

**Decision:** `build_workpaper` calls **`conclusion_review.conclusion_cards(db, assessment.id)` exactly once**, through the module attribute (`from app.services import conclusion_review`), and wraps each returned `ConclusionCard` in a `WorkpaperEntry`. Everything the card doesn't carry (the full revision list, runs and claims, client responses, mapped evidence, desk-review findings, scope) comes from the workpaper's own queries in `app/services/workpaper.py`.

**Why reuse is correct here, checked against the code:**
1. `conclusion_cards` needs no request context, takes only `(db, assessment_id)`, and is read-only (Current state lists every statement it issues). Nothing in it is decision-route-specific except two fields, `allowed_actions` and `approval_blocker`, which the workpaper simply **does not render** (they describe what a consultant may do next, not what happened).
2. It is the single place that derives `state`, `locked` (via `load_conclusion_state`, the single lock rule), `legacy_bulk_approval`, `withheld_proposal`, `legacy_report_status`, the ordering, and the latest proposal's resolved citations. A second derivation in the workpaper would drift from the conclusions page. The workpaper must show the **same** decision state the consultant acted on.

**Why not extend `ConclusionCard` with a revision list instead:** that would modify the P2-4 service and every card render (the 200 and 409 responses of four POST routes) for a need only the workpaper has. **`app/services/conclusion_review.py` is not modified by this task.** Do not import its private helpers (`_revisions`, `_decision_state`, …): write the workpaper's own revision query with the same ordering.

**`app/services/workpaper.py`: public API, exact.**

```python
from app.services import conclusion_review          # module import: spy seam (scenario 10)
from app.services.conclusion_review import REVIEWER_ACTOR_PREFIX, ConclusionCard

STALE_RUNNING_AFTER = timedelta(hours=1)
CONTENT_CHANGING_ACTIONS = ("proposed", "edited")
ACTION_LABELS = {
    "proposed": "AI proposal",
    "proposal_withheld": "AI proposal withheld (conclusion locked)",
    "approved": "Approved",
    "edited": "Edited and approved",
    "rejected": "Rejected",
    "reopened": "Reopened",
}
LEGACY_BULK_LABEL = "Legacy bulk approval, not individually reviewed"

def anchor_for(framework_id: str, requirement_id: str) -> str:
    """f"wp-{framework_id}-{requirement_id}" -- the fragment id of a requirement's entry."""

@dataclass(frozen=True)
class RunSummary:
    id: str
    framework_id: str
    status: str
    stale: bool                        # D-P2-6-K
    model_id: str
    started_at: datetime
    completed_at: datetime | None
    trigger_id: str | None             # envelope["trigger_id"]
    claim_count: int                   # len(envelope["claims"]) when a list, else 0
    error_type: str | None             # envelope["error"]["type"] when a dict, else None
    evidence_version_count: int | None # len(envelope["inputs"]["evidence_versions"]) when a list, else None
    desk_review_used: bool | None      # envelope["desk_review_used"]

@dataclass(frozen=True)
class ClientResponse:
    question_id: str
    matched_on: str                    # "requirement" | "cluster" | "singleton" (D-P2-6-F)
    answer: str
    notes: str | None
    evidence_reference: str | None
    na_reason: str | None
    confidence: str | None
    answer_source: str | None
    submitted_at: datetime

@dataclass(frozen=True)
class RevisionEntry:
    sequence: int                      # 1-based, oldest first
    revision: ConclusionRevision
    action_label: str                  # LEGACY_BULK_LABEL if legacy_bulk_approval else ACTION_LABELS.get(action, action)
    actor_display: str                 # actor with a leading "consultant:" removed; other actors verbatim
    is_human: bool                     # action in analysis_pipeline.HUMAN_DECISION_ACTIONS
    legacy_bulk_approval: bool         # action == "approved" and not actor.startswith(REVIEWER_ACTOR_PREFIX)
    outcome_after: str | None          # D-P2-6-E; None unless action in CONTENT_CHANGING_ACTIONS
    rationale_after: str | None        # D-P2-6-E; None unless action in CONTENT_CHANGING_ACTIONS
    run: RunSummary | None             # the run analysis_run_id points at, else None
    claim: dict | None                 # that run's claim whose revision_id == revision.id, else None
    citations_captured: bool           # revision.citations_json is not None
    citations: list[dict]              # resolve_citations(db, revision.citations_json)

@dataclass(frozen=True)
class WorkpaperEntry:
    card: ConclusionCard               # from conclusion_review.conclusion_cards, unmodified
    anchor: str                        # anchor_for(conclusion.framework_id, conclusion.requirement_id)
    in_scope: bool                     # D-P2-6-C
    client_response: ClientResponse | None
    mapped_evidence: list[dict]        # D-P2-6-D item 2a
    desk_review_findings: list[dict]   # D-P2-6-D item 2b
    ai_proposal: RevisionEntry | None  # the LAST RevisionEntry whose action == "proposed", else None
    revisions: list[RevisionEntry]     # every revision of this Conclusion, oldest first

@dataclass(frozen=True)
class FrameworkSection:
    framework_id: str
    entries: list[WorkpaperEntry]           # in scope, in conclusion_cards order
    excluded_entries: list[WorkpaperEntry]  # not in scope, in conclusion_cards order
    unconcluded: list[dict]                 # {"requirement_id", "title", "anchor"}; D-P2-6-C

@dataclass(frozen=True)
class Workpaper:
    sections: list[FrameworkSection]
    runs: list[RunSummary]                  # every AnalysisRun of the assessment; D-P2-6-K
    counts: dict[str, int]                  # D-P2-6-D "Page header"
    applicable: frozenset[str] | None       # D-P2-6-C

def build_workpaper(db: Session, assessment: Assessment, *, now: datetime | None = None) -> Workpaper: ...
```

- `now` defaults to `datetime.now(timezone.utc)`; it exists so the stale-run test is deterministic.
- The Session parameter is named **`db`** everywhere in the module (the structural guard in D-P2-6-H depends on it).
- The module never logs response text, notes, quotes, rationale or citation excerpts (client content); ids and counts only.

**Statements `build_workpaper` issues** (in addition to whatever `conclusion_cards` issues):
1. every `ConclusionRevision` whose `conclusion_id` is in the cards' Conclusion ids, ordered `ConclusionRevision.created_at, literal_column("conclusion_revisions.rowid")` (skip when there are no cards);
2. every `AnalysisRun` of the assessment, ordered `AnalysisRun.started_at, literal_column("analysis_runs.rowid")`;
3. every `QuestionnaireResponse` of the assessment, ordered `submitted_at, id`;
4. every `EvidenceUse` of the assessment joined to its `Evidence`, then one query for the `active` `EvidenceVersion`s of those evidence ids (skip when there are no uses);
5. every `DeskReviewFinding` of the assessment with `requirement_id IS NOT NULL`, ordered by `id`;
6. `resolve_citations` once per revision and once per desk-review finding (it returns without querying for `NULL` or `"[]"`).

Parse each run's `claims_json` once. A run whose envelope doesn't parse as a JSON object, or whose `claims` isn't a list, contributes no claims and `trigger_id`/`error_type`/counts of `None`/`0`; **never raise** on a malformed envelope (the P2-4 `_withheld_proposal` precedent). Index claims by `revision_id` across all runs, skipping non-dict claims and claims without a `revision_id`.

### D-P2-6-C. Which requirements appear: every Conclusion, split by the current scope, plus the applicable requirements with no Conclusion

"For each applicable requirement" is implemented as three disjoint lists per framework section.

**The scope set** (`Workpaper.applicable`), mirroring the pipeline exactly: `json.loads(assessment.applicable_requirements)` when it is a non-empty list of strings, as a `frozenset`; otherwise `None`. NULL, unparseable JSON, a non-list and an empty list all give `None`, meaning no restriction. `in_scope(requirement_id) = applicable is None or requirement_id in applicable`.

1. **`entries`**: Conclusions with `in_scope` true. These are the workpaper proper.
2. **`excluded_entries`**: Conclusions with `in_scope` false. Scope enforcement forced them to `not_applicable`, but they are part of the record, and a report finding can link to them. So they are **rendered with the same full entry**, under the heading "Excluded by scope enforcement" at the end of their framework section, with `data-in-scope="false"`. The claim's recorded `scope_enforced` (what the run saw) is shown separately in the AI-proposal block. The section split uses the scope **now**; the claim flag shows the scope **at run time**. They can differ, and both are shown.
3. **`unconcluded`**: for each framework in `assessment.frameworks` that `FrameworkRegistry.is_registered`, the registry controls (in `get_all_controls` order) that are `in_scope` and have **no** Conclusion for `(framework_id, control.id)`. Each is `{"requirement_id": control.id, "title": control.title, "anchor": anchor_for(framework_id, control.id)}`. These are the requirements the workpaper cannot yet trace, which is exactly what a reviewer needs to see. **Computed only when the assessment has at least one Conclusion**; with zero Conclusions, `sections == []` and the page shows the empty state (D-P2-6-J), not a list of every control.

**Section order:** the frameworks of `assessment.frameworks`, in order, then any other `framework_id` found on a Conclusion, sorted. This matches `conclusion_cards`' ordering. A selected framework with no Conclusions still gets a section when the assessment has Conclusions in another framework, holding only its `unconcluded` list. Entries within a section keep the `conclusion_cards` order.

### D-P2-6-D. What an entry shows (this is "full history"), exact

Template `app/templates/components/workpaper_entry.html`, context `entry` (a `WorkpaperEntry`) and `assessment`. The root element, **with attributes in exactly this order**:

```html
<article data-workpaper-entry id="{{ entry.anchor }}" data-in-scope="{{ 'true' if entry.in_scope else 'false' }}" data-decision-state="{{ entry.card.state }}" class="…">
```

The test helper in step 7 relies on `data-workpaper-entry` coming **before** `id`. Sections render in this order, each with a small uppercase heading (Tailwind, `dark:` variants, styled like `components/conclusion_card.html`). Every "exact text" below is asserted by a test, so copy it verbatim.

**Header.**
- `framework_id|upper`, `requirement_id` (mono), `card.requirement_title`.
- The decision badge with the card's labels: Pending / Rejected / Approved / "Edited and approved" / `LEGACY_BULK_LABEL` when `card.legacy_bulk_approval`.
- `v{{ card.conclusion.version }}`, the Conclusion id (small, mono), and "Locked: re-analysis will not overwrite this" when `card.locked`.
- The badge "Excluded by scope enforcement" when `not entry.in_scope`.
- A link `href="/assessments/{{ assessment.id }}/conclusions#conclusion-card-{{ card.conclusion.id }}"` with text "Decide on the conclusions page →". This is the only route to a decision; the workpaper itself has none (D-P2-6-H).
- When `card.legacy_report_status`: "Report view differs: {{ card.legacy_report_status|replace('_', ' ')|title }}". The reviewer arrived from a report row that shows the `GapItem` verdict, so the divergence must be explicit.

**1. Client response.**
- When `entry.client_response`: the answer (`replace('_',' ')|title`), `answer_source`, `confidence`, `na_reason`, `notes`, `evidence_reference`, `submitted_at`, and `question_id` (mono).
- When `matched_on == "cluster"`, also the text "Shared cluster question {{ question_id }}: one answer informs every framework requirement in this cluster."
- Otherwise: "No questionnaire response recorded for this requirement."

**2. Evidence.**
- **(a) Mapped evidence**: `entry.mapped_evidence`, the `EvidenceUse` rows with `(framework_id, requirement_id)` equal to the Conclusion's, ordered `(created_at, id)`. Each dict is `{"use_id", "evidence_id", "filename", "evidence_status", "relevance", "created_at"}`, where `filename` is the **active version's** `original_filename`, else `Evidence.original_filename`. Render the filename as a link to `/evidence/{{ evidence_id }}`, plus relevance and status. Empty: "No evidence mapped to this requirement."
- **(b) Desk-review findings**: `entry.desk_review_findings`, the `DeskReviewFinding`s with `requirement_id` equal to the Conclusion's `requirement_id` (desk-review rows carry no framework id), ordered by `id`. Each dict is `{"finding_type", "severity", "content", "source_quote", "source_location", "citations_captured", "citations"}` (`citations_captured = citations_json is not None`, `citations = resolve_citations(db, citations_json)`). Label the block "Current desk review (replaced when desk review is re-run)". Empty: "No desk-review findings for this requirement."

**3. AI proposal**, from `entry.ai_proposal` (the latest `proposed` revision, the same revision `card.citations` comes from):
- `None` → "No AI proposal recorded."
- `claim is None` → "No run record for this proposal (migrated from the legacy report)." followed by the citation list macro (it will say not captured).
- Otherwise:
  - the claim's `outcome`, and from `claim["item"]` (use `.get`): `current_state` (as Rationale), `gap_description`, `risk_level`, `remediation_action`;
  - the run (`run.model_id`, `run.started_at`, `run.trigger_id`) and `claim["disposition"]`;
  - "Scope-enforced to not applicable at analysis time" when `claim["scope_enforced"]`;
  - a **quality list with each dimension separate** (PR-022): citations `quality.citation_count`; evidence quote "grounded" / "not grounded" / "no quote offered" for `true` / `false` / `null`; unsupported assertion yes/no; model flagged for review yes/no; desk-review red flags (count); desk-review absence yes/no; contradictions "Not assessed" when `null`;
  - when `quality.evidence_quote_grounded is false`: "Ungrounded quote offered by the model (not found in any evidence; not treated as support):" followed by `item.evidence_quote`. It is shown for audit, never in the Evidence section (PR-041);
  - the citation list for `entry.ai_proposal`;
  - the text "This supporting outcome has no grounded citation." when `card.unsupported_assertion`.
- When `card.withheld_proposal`: "A newer AI proposal was withheld because this conclusion is locked" plus its outcome and rationale when present (the card's own wording, **without** a Reopen control).

**4. Consultant decision.**
- The current Conclusion: `outcome`, `risk_level`, `rationale`, `gaps_identified`, `recommended_action`, `evidence_summary` (or "No grounded supporting quote" when `""`), labelled "AI proposal" when `ai_proposed`, else "Consultant-edited".
- "AI proposed before edit: …" when `not ai_proposed and card.previous_outcome`.
- The last decision line: "{{ action }} by {{ actor_display }} at {{ created_at }}".
- For a `card.state == "edited"` entry, the note: "Consultant edits carry no citations; the citations above belong to the AI proposal this edit replaced." This closes P2-4 open question 3 **for display**; whether edits get their own citations stays open.

**5. Revision history.** `<ol data-revision-history>` with one `<li data-revision-action="{{ rev.revision.action }}">` per `RevisionEntry`, oldest first (D-P2-6-E). Each item shows:
- `#{{ sequence }}`, `created_at`, `action_label` and `actor_display`;
- "Before: {{ previous_outcome }}", with `previous_rationale`, when not NULL;
- "After: {{ outcome_after }}", with `rationale_after`, when not `None`;
- for a revision with a `run`: the run's short id (first 8 chars), framework, `model_id` and status; with a `claim`, also its `outcome` and `disposition`, and the citation list for this revision;
- for a `proposed` revision with no run: "No run record for this proposal (migrated from the legacy report).";
- for human revisions: no citation list (they carry none by design, D-P2-4-C).

The history is **always expanded**. `workpaper_entry.html` contains **no `<details>` element at all**, so landing on the anchor shows the full history without another click.

**Citation list** (a Jinja macro defined at the top of `workpaper_entry.html`, taking `(citations, captured)`), with wording identical to the conclusion card:
- not `captured` → "Evidence support not captured (legacy)";
- `captured` and empty → "No supporting citation (explicit evidence absence)";
- otherwise each citation shows the `excerpt`, then the filename linked to `/evidence/{{ evidence_id }}` when `resolved` (else the filename or "Unresolved evidence"), `v{{ version_number }}`, `location_ref`, and "(superseded version)" when `not is_current`.

**Page** `app/templates/pages/workpaper.html` extends `base.html`:
- `{% block title %}Workpaper — {{ assessment.company_name }}{% endblock %}`;
- the breadcrumb `Assessments / {{ assessment.company_name }} / Workpaper`, in the `pages/conclusions.html` style;
- `<h1>` "Workpaper: requirement traceability" and the subtitle "Read-only. Client response, evidence, AI proposal, consultant decision and every revision for each requirement, oldest event first.";
- links "Conclusions (decide) →" (`/assessments/{{ assessment.id }}/conclusions`) and "Report →" (`/assessments/{{ assessment.id }}?tab=report`);
- a counts grid, `<p data-count="{{ key }}">`, over `wp.counts` with keys `conclusions`, `in_scope`, `excluded`, `unconcluded`, `pending`, `rejected`, `approved` (approved and not legacy bulk), `edited`, `legacy_bulk`, `runs`. The state counts use exactly `conclusions_page`'s rules, over all entries.
- **Analysis runs** (D-P2-6-K);
- then either the empty state, or one `<section data-workpaper-section="{{ section.framework_id }}">` per section:
  - an `<h2>` with `framework_id|upper`;
  - the in-scope entries (`{% include "components/workpaper_entry.html" %}` per entry);
  - when there are excluded entries, an `<h3>` "Excluded by scope enforcement" followed by those entries;
  - when `unconcluded` is non-empty, an `<h3>` "Applicable requirements with no conclusion" and a plain `<ul>` of `<li data-workpaper-unconcluded id="{{ row.anchor }}">{{ row.requirement_id }} — {{ row.title }}</li>`. This is not inside a `<details>`, so a fragment link lands on a visible row.

Everything is autoescaped. **Never use `|safe`**, because response notes, desk-review content, rationale, quotes and excerpts are client and LLM text.

### D-P2-6-E. Revision history semantics

- **Order:** `(created_at, rowid)` ascending, the P2-3/P2-4 recency order. `sequence` is 1-based in that order.
- **Before/after.** A revision stores only the values *before* it (Current state). For each revision at index *i* whose action is in `CONTENT_CHANGING_ACTIONS` (`proposed`, which covers both created and applied proposals, and `edited`), `outcome_after`/`rationale_after` are the `previous_outcome`/`previous_rationale` of the **next** content-changing revision *j > i*, or the Conclusion's current `outcome`/`rationale` if there is none. For every other action (`approved`, `rejected`, `reopened`, `proposal_withheld`), they are `None`: those actions never change content (D-P2-3-C, D-P2-4-C). Only outcome and rationale can be reconstructed. The other fields are not stored per revision, and the page must not imply they are.
- **Labels and actors:** `action_label` and `actor_display` as defined in D-P2-6-B. System actors (`system:analysis`, `system:migration`) are shown verbatim. **The raw `consultant:` prefix is never rendered** (the same rule as `ConclusionCard.last_decision.actor_display`).
- **Legacy bulk approvals** are labelled with `LEGACY_BULK_LABEL` per revision, using the same rule as D-P2-4-F. They are never presented as individual approvals.
- **Run and claim linking:** `run` = the `RunSummary` for `revision.analysis_run_id` (from statement 2; `None` when NULL). `claim` = the claim whose `revision_id == revision.id` (`None` when not found; never raise).
- **Why not `audit_events`:** revision rows are this domain's append-only trail (D2, and P2-3/P2-4 non-goals). Evidence lifecycle `audit_events` are reachable one click away on `/evidence/{id}`; the workpaper does not read `audit_events`.

### D-P2-6-F. Client response matching

Load the assessment's responses once, into a dict keyed by `question_id`, iterating in `(submitted_at, id)` order so that the **last** one wins for a duplicated `question_id` (there is no unique constraint). For a Conclusion, try these keys in order; the first hit wins, and records `matched_on`:

| Order | Key | `matched_on` | When it hits |
|---|---|---|---|
| 1 | `conclusion.requirement_id` | `requirement` | DPDPA-only assessments (`question_id` = requirement id) |
| 2 | `conclusion.cluster_id` (skipped when `None`) | `cluster` | multi-framework, clustered control |
| 3 | `f"SINGLE.{conclusion.requirement_id}"` | `singleton` | multi-framework, unclustered control (e.g. `ISO.A5.32`) |

No hit → `None`. **Follow-up answers (`FU.*`) are not shown** (open question 2). The rule is a read of existing keys and needs no schema change.

### D-P2-6-G. "3 clicks from Finding to full history": the exact path, and the links this task adds

Today "Finding" means a `GapItem` row labelled as a finding in the Report tab (Current state). `Finding` rows exist only for migrated legacy data and have no UI (P3-1). The acceptance criterion is therefore met on the report, and P3-1 must honour it for its own Findings (Handed forward).

**The path (every step is a plain `<a href>`; nothing is collapsed):**

| Step | Where the reviewer is | Clicks | Lands on |
|---|---|---|---|
| start | Assessment page (`/assessments/{id}`) | — | — |
| 1 | the Report tab link (existing) | 1 | Report tab; `report_summary.html` loads, showing "Critical Findings" and "Detailed Findings" |
| 2 | "Workpaper trace →" on a finding row (**new**) | 2 | `/assessments/{id}/workpaper#wp-{framework}-{requirement}`: that requirement's entry, with the client response, evidence, citations, AI proposal + claim quality + run/model, consultant decision and the **complete** revision history (actors, timestamps), all expanded |
| 3 | a citation filename in that entry (existing pattern) | 3 | `/evidence/{evidence_id}`: every version with its full SHA-256, status and change reason (the PR-055 "Evidence version" end of the chain) |

So from a finding, the full history is **1** click away, and the evidence-version record is **2** clicks away. From the assessment page, the whole Finding → Conclusion revision → claim/Citation → Evidence version chain takes **3** clicks. That is P7's "three or fewer clicks" and PR-055's navigation, literally.

**Links added (template-only; no route or Python change outside `web.py`'s new route):**

1. `app/templates/partials/report_summary.html`:
   - **(a)** In the "Critical Findings" loop, in the `<p>` that shows `{{ item.requirement_id }}`, append `<a href="/assessments/{{ assessment_id }}/workpaper#wp-{{ item.framework_id or 'dpdpa' }}-{{ item.requirement_id }}" class="ml-2 text-brand dark:text-navy-300 hover:underline">Workpaper trace →</a>`.
   - **(b)** In the grouped "Detailed Findings" branch (`{% for item in chapter_items %}`), and **(c)** in the flat-table fallback (`{% for item in gap_items %}`), put the same anchor directly after the `<p … data-copy-target="requirement-id">` line.
   - **(d)** In the "Detailed Findings" `<summary>`, beside "PDF Report", add `<a href="/assessments/{{ assessment_id }}/workpaper" onclick="event.stopPropagation()" class="text-xs text-brand dark:text-navy-300 hover:text-brand-light font-medium">Workpaper</a>`, matching the existing links' markup.
   - Change nothing else in the file.
2. `app/templates/components/conclusion_card.html`: in the header metadata row (after `<span>v{{ card.conclusion.version }}</span>`), add `<a href="/assessments/{{ assessment.id }}/workpaper#wp-{{ card.conclusion.framework_id }}-{{ card.conclusion.requirement_id }}" class="text-brand dark:text-navy-300 hover:underline">Workpaper trace →</a>`. Nothing else changes, and both render paths (the page, and the 200/409 API responses) already pass `assessment`.
3. `app/templates/pages/conclusions.html`: in the header block, add `<a href="/assessments/{{ assessment.id }}/workpaper" class="text-sm font-medium text-brand dark:text-navy-300 hover:underline">Workpaper (read-only trace) →</a>`. Nothing else changes.

**Anchor consistency:** the report uses `item.framework_id or 'dpdpa'` (legacy NULL means DPDPA, the same normalisation `conclusion_cards` uses for `legacy_report_status`), and the workpaper uses `anchor_for(conclusion.framework_id, requirement_id)`. The unique index on `(assessment_id, framework_id, requirement_id)` makes anchors unique across entries, and `unconcluded` rows by construction have no Conclusion, so no id repeats. A report finding with neither a Conclusion nor an in-scope unconcluded row (e.g. an out-of-scope `GapItem` from an assessment analysed before P2-3) has no anchor; the browser then lands at the top of the page. That is accepted, not an error.

### D-P2-6-H. Read-only guarantee

- **No mutation of any kind in this task.** No POST/PUT/PATCH/DELETE route, no HTMX action, no form, no button, no hidden `expected_version`. Every decision about a Conclusion belongs to P2-4's four routes (already built). The workpaper only **links** to `/assessments/{id}/conclusions#conclusion-card-{id}`. Adding any mutating control or route here is a spec violation, not a convenience.
- `app/services/workpaper.py` never commits, flushes, adds, merges or swaps, and contains no delete. `workpaper_page` never commits.
- **Structural guards** (scenario 9 pins them, the same way P2-4 scenario 12 pinned individual-only):
  1. The set of app routes whose path contains `/workpaper` is exactly `{("GET", "/assessments/{assessment_id}/workpaper")}`.
  2. Neither `app/templates/pages/workpaper.html` nor `app/templates/components/workpaper_entry.html` matches the Python regex `<form|<button|hx-post|hx-put|hx-patch|hx-delete|expected_version|\|\s*safe\b` (`re.IGNORECASE`).
  3. `app/services/workpaper.py`: `"delete" not in source.lower()`, and none of the substrings `db.add(`, `db.add_all(`, `db.merge(`, `.commit(`, `.flush(`, `swap_conclusion`, `decide(` occurs.
  4. `inspect.getsource(web.workpaper_page)` contains no `.commit(`.
  5. `POST`, `PUT`, `PATCH` and `DELETE` to `/assessments/{id}/workpaper` each return **405**.
  6. A GET changes nothing in the DB (scenario 9's snapshot).

### D-P2-6-I. Multi-framework handling

One page per assessment, with one section per framework (D-P2-6-C order), reusing the `pages/conclusions.html` grouping idea (a framework heading, then that framework's entries). **Requirements are never merged across frameworks.** A shared UCC question is shown on each framework's entry with the "Shared cluster question" text (D-P2-6-F), keeping framework-specific applicability and Conclusions distinct (PRD journey step 3). No scores are shown anywhere on the page (P1-5: no blended score; the workpaper is not a scoring surface).

### D-P2-6-J. Empty and edge states (exact behaviour)

| Case | Behaviour |
|---|---|
| Unknown assessment id | 404 `"Assessment not found"` |
| Assessment with no Conclusions | 200. The runs section still renders (so failed runs are visible), then "No conclusions yet. Run the gap analysis first." `sections == []`, and no `data-workpaper-entry` appears. |
| No runs | "No analysis runs recorded." |
| Proposal with `citations_json = "[]"` | "No supporting citation (explicit evidence absence)" and, for a supporting outcome, the unsupported-assertion warning |
| Proposal with an ungrounded quote | `evidence_summary` is `""` → "No grounded supporting quote"; the AI-proposal block shows the ungrounded-quote text and the quote |
| Migrated legacy Conclusion (`proposed` by `system:migration`, NULL citations, no run; optionally `approved` by a bare name) | "No run record for this proposal (migrated from the legacy report).", "Evidence support not captured (legacy)", `LEGACY_BULK_LABEL` on the approval revision and the header badge. Never raises. |
| No client response / no mapped evidence / no desk findings | The three exact texts in D-P2-6-D |
| Requirement excluded by scope | Full entry under "Excluded by scope enforcement", `data-in-scope="false"` |
| Applicable requirement with no Conclusion | Listed in "Applicable requirements with no conclusion", with its anchor |
| Malformed run envelope | That run shows with `None`/`0` fields; its revisions have `claim = None`; never raises |
| Framework not in the registry | Titles fall back to the requirement id (the card already does this); no `unconcluded` list for it |

`resolve_citations`/`loads_citations` are **not** wrapped in try/except, consistent with `conclusion_cards`, which already calls them unguarded. Every writer stores a JSON array or NULL (P2-2), and a corrupt row should surface, not be hidden on an audit page.

### D-P2-6-K. Run log and stale runs (closes P2-3 open question 5 for display)

The "Analysis runs" section, placed before the framework sections, is a table with one `<tr data-run-status="{{ run.status }}" data-run-stale="{{ 'true' if run.stale else 'false' }}">` per `RunSummary`, in `(started_at, rowid)` order. Columns: framework (upper), status, model id, started, completed, trigger id (first 8 chars), claims, evidence versions offered, desk review used, and error type.

`stale = run.status == "running" and started_at < now - STALE_RUNNING_AFTER`. Treat a naive `started_at` (SQLite returns naive datetimes) as UTC before comparing. A stale run's status cell reads "Running (stale: started more than 1 hour ago; likely interrupted)". **Display only:** nothing is written and no sweeper is added. The one-hour threshold is a fixed constant because no request timeout exists to derive it from (Current state).

### D-P2-6-L. Performance: P2-4's accepted budget carried forward, not re-litigated

`build_workpaper` runs `conclusion_cards`' full per-assessment load (as `conclusions_page` does, and as P2-4's reviewer accepted as a non-blocking inefficiency for a single-user local SQLite app), plus the fixed statements in D-P2-6-B, plus `resolve_citations` per revision/finding with non-empty citations (two small queries each; NULL and `"[]"` cost nothing). The revision list is queried twice (once inside `conclusion_cards`, once here); that duplication is accepted in exchange for not modifying the P2-4 service. **There is no hard query or latency budget in this task.** The adversarial review's performance item (a 2-second threshold for "workpaper render" on a seeded large dataset) is explicitly a final-phase (Phase 4) measurement. Record this task's timing in the smoke test (Done criteria) so Phase 4 has a baseline. If batching ever becomes necessary, it belongs in `app/services/citations.py` as a batched resolver, not as a second resolver in this module.

### D-P2-6-M. Consistency audit of this spec (the P2-4 lesson, done in advance)

P2-4's handoff mandated a field name that its own grep forbade. Every mandated string in this document has been checked against every structural assertion in this document and in the existing suite:

1. **Read-only regex vs mandated template content.** The two workpaper templates must contain none of `<form`, `<button`, `hx-post|put|patch|delete`, `expected_version`, `|safe`. Nothing mandated in D-P2-6-D/G/K needs any of them: every navigation is an `<a href>`, and the history uses no `<details>` (and `<details>` isn't forbidden anyway). The **rendered** page includes `base.html`, which has a `<button>` (the theme toggle), so the rendered-page assertions in scenario 9 check only `<form`, `hx-post`, `hx-put`, `hx-patch`, `hx-delete`, `name="expected_version"` and `data-conclusion-card`, **never** `<button`.
2. **Service substring guard vs mandated code.** Forbidden: `delete` (any case), `db.add(`, `db.add_all(`, `db.merge(`, `.commit(`, `.flush(`, `swap_conclusion`, `decide(`. The mandated API contains none. `dict.update(...)` and `set.add(...)` are **deliberately not forbidden**, so ordinary Python stays legal. **Keep the word "delete" out of comments and docstrings too.** The desk-review block's label says "replaced", not "deleted", for this reason. The Session parameter must be called `db` so the `db.add(` guard means what it says.
3. **P2-4 scenario 12 route set.** The new path does not contain `/conclusions`. The links added to `conclusion_card.html`/`conclusions.html` contain none of `approve all|approve selected|select all|approve framework`.
4. **Escaping vs exact-text assertions.** No mandated label contains `&`, `<`, `>` or quotes. That's why the edited label is "Edited and approved", not the card's "Edited &amp; approved". Tests compare any DB- or LLM-sourced string (model id, notes, excerpts) as `html.escape(value)`, and use only plain alphanumeric test data except in the dedicated escaping scenario.
5. **Counted attributes.** `data-workpaper-entry` appears **only** on the entry root, so its count equals the number of Conclusions, excluded ones included. `unconcluded` rows use `data-workpaper-unconcluded`, which does not contain the substring `data-workpaper-entry`. `data-revision-action=` appears only on history `<li>`s. The workpaper never includes `components/conclusion_card.html`, so `data-conclusion-card` never appears on it.
6. **Entry-slicing helper vs attribute order.** Step 7's `_entry_html` slices from `id="{anchor}"` to the next `data-workpaper-entry`. That only isolates one entry because the root is `<article data-workpaper-entry id=…>` (attribute before id). Do not reorder.
7. **Anchor hrefs vs page-link href.** Tests look for the fragment link `href="/assessments/{id}/workpaper#wp-…"` and the page link `href="/assessments/{id}/workpaper"` (closing quote right after `workpaper`). Neither substring contains the other.
8. **Existing template guards.** No `CyberAssess` literal in any template (white-label guard), and no `overall_score` anywhere (blended-score guards). The page title uses `assessment.company_name`, like the other pages.
9. **Actor prefix.** The raw `consultant:` prefix is never rendered (D-P2-6-E). Scenario 2 asserts `"consultant:Priya" not in page.text`. No mandated copy contains the lowercase `consultant:` followed by a name.

## Required approach

### 1. `app/services/workpaper.py` (new): the API in D-P2-6-B, the row set in D-P2-6-C, the entry data in D-P2-6-D, history in D-P2-6-E, responses in D-P2-6-F, and runs in D-P2-6-K

Module docstring (use this text, which passes the D-P2-6-H guard): `"""Read-only workpaper read model (P2-6): per-requirement traceability from client response and evidence to AI proposal, consultant decision and every revision. Never writes."""`

### 2. `app/routers/web.py`: `workpaper_page` (D-P2-6-A), directly after `conclusions_page`, and `from app.services import workpaper`

### 3. Templates

- `app/templates/pages/workpaper.html` (new, D-P2-6-D "Page").
- `app/templates/components/workpaper_entry.html` (new, D-P2-6-D, including the citation macro).
- The link additions in D-P2-6-G to `partials/report_summary.html`, `components/conclusion_card.html` and `pages/conclusions.html`. Additive only.

### 4. No change anywhere else

`app/services/conclusion_review.py`, `app/services/analysis_pipeline.py`, `app/services/citations.py`, `app/routers/conclusions.py`, `app/routers/review.py`, `app/routers/reports.py`, `app/routers/remediation.py`, `app/routers/analysis.py`, `app/services/scoring.py`, `app/utils/pdf_export.py`, `app/static/js/app.js`, `app/models/*`, `alembic/versions/*` and `scripts/*` are **not modified**. There is no schema change and no Alembic revision.

### 5. `tasks/todo.md`

Change the P2-4 line to **Merged: PR #28**, add a P2-6 line with its status and a link to this handoff's Results, and update the Phase 2 summary line.

### 6. Smoke test (Done criteria)

### 7. `tests/test_workpaper.py` (new)

Copy (don't import) from `tests/test_conclusion_approval.py`:
- the Alembic-built `db_path` / `engine` (`PRAGMA foreign_keys=ON`) / `db` fixtures;
- the `http` `TestClient` fixture;
- `gate`, `_seed`, `_item`, `_stub_single`, `_run_one`, `_revisions`, `_url`, `_edit_payload` and `_human_revision`;
- `REQS = [row["id"] for row in get_all_requirements()][:3]` and the module-scoped `_register_frameworks` fixture.

Extend `_seed` with a `frameworks=["dpdpa"]` keyword, and let `applicable` accept an explicit list. **Its `applicable or [REQS[0]]` default means an unspecified `applicable` scopes every other requirement out**, so pass the exact list each scenario needs. Copy `_stub_multi` from `tests/test_analysis_pipeline.py` for scenario 5.

Produce Conclusions and decisions through the **real** pipeline (`gate.trigger_analysis(a.id, db)` with a stub) and the **real** P2-4 POST routes (`/api/assessments/{id}/conclusions/{cid}/approve|edit|reject|reopen` with `expected_version` read from the DB). Hand-built rows are allowed only for:
- the legacy-migrated shape (scenario 7);
- citation JSON on a proposal revision (set `citations_json` directly after the run, exactly as P2-4 scenario 14 does);
- `EvidenceUse`, `DeskReviewFinding`, `QuestionnaireResponse` and stale `AnalysisRun` rows.

Helper, exactly:

```python
def _entry_html(page_text: str, anchor: str) -> str:
    start = page_text.index(f'id="{anchor}"')
    end = page_text.find("data-workpaper-entry", start)
    return page_text[start:] if end == -1 else page_text[start:end]
```

Use it only for **positive** assertions and for ordering within an entry. The last entry of a section can run on into the section's trailing lists, so make negative assertions on the whole page or through `build_workpaper`. Prefer `workpaper.build_workpaper(db, assessment)` for semantic assertions and the HTML for wiring. Every scenario is one or more test functions whose docstrings start with `Scenario N:`.

## Key files

| File | Why it matters |
|---|---|
| `app/services/workpaper.py` (new) | The read model (D-P2-6-B … F, K). |
| `app/routers/web.py` | `workpaper_page`, the only new route. |
| `app/templates/pages/workpaper.html`, `app/templates/components/workpaper_entry.html` (new) | The page and one entry (D-P2-6-D). |
| `app/templates/partials/report_summary.html`, `components/conclusion_card.html`, `pages/conclusions.html` | Link additions only (D-P2-6-G). |
| `app/services/conclusion_review.py` | Reused via `conclusion_cards`; **not modified**. |
| `app/services/citations.py` | `resolve_citations`; **not modified**. |
| `tests/test_workpaper.py` (new) | The contract. **No existing test file is modified.** |
| `tasks/todo.md` | P2-4 → merged; the P2-6 line. |

## Non-goals

- **No mutation of any kind** (D-P2-6-H). No approve/edit/reject/reopen, no evidence mapping, invalidation or archive, no response editing, and no "mark reviewed" from the workpaper.
- **No `report_snapshots` workpaper snapshot, PDF or export.** Immutable snapshots are P3-2, and the PDF is P3-3. This is a live view.
- **No change to `ConclusionRevision`**: no rejection-reason or reviewer-note column (P2-4 open question 1 stays open; see open question 1), and no consultant citations on edits (P2-4 open question 3 stays open for data; display is closed in D-P2-6-D).
- **No reading of the `findings`/`actions` tables** (P3-1 designs Findings; today's rows are migration artefacts). No reading of `audit_events` (D-P2-6-E).
- **No scores**, and no move of scoring, reports, PDF or remediation onto Conclusions (the reader migration, P2-3 open question 1).
- **No follow-up (`FU.*`) answers, no screening results, no desk-review coverage summary** (open question 2).
- No JSON API, no HTMX partials, no pagination or filtering, no new JS, no `relationship()`, no schema change.

## Test scenarios

All in `tests/test_workpaper.py`. "Nothing written" means the D-P2-6-H snapshot is unchanged: `COUNT(*)` of `conclusions`, `conclusion_revisions`, `analysis_runs`, `audit_events`, `evidence_uses`, `questionnaire_responses` and `desk_review_findings`; every Conclusion's `(id, version, updated_at, outcome, rationale, ai_proposed)`; and the assessment's `(status, review_status, updated_at)`.

1. **Assessment with approved conclusions renders the workpaper (the plan's test).** `_seed(applicable=REQS[:2])`, then add a `QuestionnaireResponse(question_id=REQS[0], answer="partially_implemented", notes="Client note text")`. Run the pipeline with `_item(REQS[0], "partially_compliant")` and `_item(REQS[1], "compliant", gap="", risk="low", action="")`. Give REQS[0]'s `proposed` revision a `text_span` citation to an active `EvidenceVersion` (P2-4 scenario 14's construction, `file_hash_sha256 = "a" * 64`). `approve` REQS[0] as `reviewer_name="Priya"`. `GET /assessments/{id}/workpaper` → 200, and:
   - `page.text.count("data-workpaper-entry") == 2`;
   - `_entry_html(page, "wp-dpdpa-" + REQS[0])` contains `data-decision-state="approved"`;
   - its `data-revision-action` values in order are `["proposed", "approved"]`;
   - it contains "Priya", `html.escape(run.model_id)`, "Client note text", "Partially Implemented", the excerpt, and `href="/evidence/{evidence.id}"`;
   - it contains "no quote offered" (the stub's `evidence_quote` is `""`, so the claim's `evidence_quote_grounded` is `null`; do not assert on the bare word "grounded", which is a substring of other mandated texts);
   - REQS[1]'s entry is `data-decision-state="pending"` and shows "No questionnaire response recorded for this requirement.".
2. **Full history, before/after and actors.** One Conclusion (REQS[0], `applicable=[REQS[0]]`), taken through: run 1 (`partially_compliant`) → `approve` (Priya) → `reopen` (Priya) → run 2 (`non_compliant`, applied) → `edit` (reviewer "Asha", outcome `compliant`) → run 3 (`partially_compliant`, withheld).
   - `build_workpaper` entry `revisions` actions == `["proposed", "approved", "reopened", "proposed", "edited", "proposal_withheld"]`, with `sequence` 1–6.
   - `outcome_after` is `partially_compliant` for #1, `non_compliant` for #4 and `compliant` for #5, and `None` for #2, #3 and #6.
   - `#4.previous_outcome == "partially_compliant"` and `#5.previous_outcome == "non_compliant"`.
   - `ai_proposal` is revision #4, and its `claim["outcome"] == "non_compliant"`.
   - `#6.claim["disposition"] == "withheld"`. `#1.run`, `#4.run` and `#6.run` are three distinct completed runs, and `#2.run is None`.
   - `actor_display` values: "Priya", "Asha" and "system:analysis".
   - HTML: the entry contains "Edited and approved", "A newer AI proposal was withheld because this conclusion is locked", "AI proposed before edit" and the edited-citations note ("Consultant edits carry no citations"), and `"consultant:Priya" not in page.text`.
3. **Three clicks from Finding to full history (P7).** Run the pipeline with `_item(REQS[0], "non_compliant", risk="high")` (`applicable=[REQS[0]]`), set its citation as in scenario 1, and `approve` it.
   - `GET /assessments/{id}/report-summary`: the text contains `href="/assessments/{id}/workpaper#wp-dpdpa-{REQS[0]}"` **at least twice** (Critical Findings and Detailed Findings) and `href="/assessments/{id}/workpaper"` at least once.
   - `GET /assessments/{id}/conclusions` contains the same fragment href.
   - `GET /assessments/{id}/workpaper` contains `id="wp-dpdpa-{REQS[0]}"` exactly once, and that entry has two `data-revision-action` items and `href="/evidence/{evidence.id}"`.
   - `GET /evidence/{evidence.id}` returns 200 and contains `"a" * 64`.
   - Assert the markup-level guarantee: `components/workpaper_entry.html` source contains no `<details`.
4. **Scope and the applicable set.**
   - (a) `_seed(applicable=[REQS[0]])` with items REQS[0] and REQS[1]: REQS[1]'s entry is `data-in-scope="false"`, appears after the "Excluded by scope enforcement" heading and after REQS[0]'s entry, and shows "Scope-enforced to not applicable at analysis time". Both entries count in `data-workpaper-entry`.
   - (b) `_seed(applicable=REQS[:3])` with only REQS[0] analysed: `unconcluded` requirement ids == `[REQS[1], REQS[2]]` (registry order); the page has `data-workpaper-unconcluded` twice, `id="wp-dpdpa-{REQS[1]}"`, and the heading "Applicable requirements with no conclusion".
   - (c) Through `build_workpaper`, after setting `applicable_requirements` directly: `None`, `"not json"` and `"[]"` each give `wp.applicable is None`, and 40 DPDPA `unconcluded` rows (41 − 1).
5. **Multi-framework grouping and response matching.**
   - Setup: `_seed(frameworks=["dpdpa", "iso27001"], applicable=[REQS[0], iso_clustered, iso_single])`. `iso_clustered` is the first `iso27001` control present in `CONTROL_CLUSTERS`, and `iso_single` is the first not present; assert both exist. `_stub_multi` gives one item per control. Add responses keyed `REQS[0]`, the ISO Conclusion's `cluster_id` (read from the DB after the run), and `f"SINGLE.{iso_single}"`.
   - `matched_on` is `requirement`, `cluster` and `singleton` respectively.
   - `data-workpaper-section="dpdpa"` comes before `data-workpaper-section="iso27001"` in the HTML, and each entry's anchor lies inside its own framework's section. The ISO clustered entry shows "Shared cluster question".
   - Before the three responses are added, all three entries have `client_response is None` (the seed's `"Q1"` response matches no key).
   - Two responses with the same `question_id` and explicit `submitted_at` values one minute apart: the later one wins.
6. **Evidence block.**
   - An `EvidenceUse(evidence_id=…, assessment_id=…, framework_id="dpdpa", requirement_id=REQS[0], relevance="primary")` appears in `mapped_evidence` with the active version's filename, and the entry links to `/evidence/{id}` and shows "primary".
   - A use for REQS[1] is not in REQS[0]'s `mapped_evidence`.
   - A `DeskReviewFinding(requirement_id=REQS[0], finding_type="evidence", content="Desk finding text", citations_json=None)` appears with `citations_captured False` (HTML: "Evidence support not captured (legacy)"); one with `citations_json="[]"` shows "No supporting citation (explicit evidence absence)"; a finding with `requirement_id=None` appears in no entry.
   - Empty cases show "No evidence mapped to this requirement." and "No desk-review findings for this requirement.".
7. **Edge states.**
   - Unknown assessment → 404.
   - An assessment with no Conclusions → 200, "No conclusions yet. Run the gap analysis first.", "No analysis runs recorded.", and no `data-workpaper-entry`.
   - Patch `run_gap_analysis` to raise `RuntimeError("boom")` and call `gate.trigger_analysis` inside `pytest.raises(HTTPException)` (the P2-3 scenario 8 pattern). The run log then has `data-run-status="failed"` and the text "RuntimeError", still with no entries, and "boom" is not on the page.
   - A hand-inserted `AnalysisRun(status="running", started_at=now - 2h, claims_json="{}")` gives `stale True` (via `build_workpaper(…, now=now)`) and `data-run-stale="true"`; one started 5 minutes ago gives `stale False`.
   - `claims_json="not json"` on a completed run doesn't raise.
   - **Legacy-migrated shape**, on its own assessment:
     - Hand-build a Conclusion with one `proposed` revision (`actor="system:migration"`, `citations_json=None`, `analysis_run_id=None`) and an `approved` revision by `"Manager Review"`.
     - The entry shows "No run record for this proposal (migrated from the legacy report).", "Evidence support not captured (legacy)" and `LEGACY_BULK_LABEL`.
     - The approved `RevisionEntry` has `legacy_bulk_approval True`.
     - `counts["legacy_bulk"] == 1` and `counts["approved"] == 0`.
   - **Ungrounded quote:** `_item(REQS[0], "compliant", quote="fabricated words not in evidence")`, with no evidence uploaded, shows "No grounded supporting quote", "Ungrounded quote offered by the model", the quote, and "This supporting outcome has no grounded citation.".
8. **Escaping.** `<script>alert(1)</script>` in the stub's `current_state`, in response `notes`, and in a desk finding's `content`: the page contains `&lt;script&gt;alert(1)&lt;/script&gt;` and never `<script>alert(1)</script>`.
9. **Read-only guarantee (D-P2-6-H).**
   - The `/workpaper` route set is exactly the one GET.
   - The template regex check on both files passes, as does the service substring check.
   - `workpaper_page` source has no `.commit(`.
   - POST, PUT, PATCH and DELETE to the page URL each return 405.
   - For the scenario 1 setup, snapshot → GET the workpaper twice → snapshot: nothing written.
   - The rendered page contains none of `<form`, `hx-post`, `hx-put`, `hx-patch`, `hx-delete`, `name="expected_version"`, `data-conclusion-card`. **Do not assert on `<button`**, because `base.html` has one (D-P2-6-M item 1).
10. **Reuse of `conclusion_cards` (D-P2-6-B).** Monkeypatch `app.services.conclusion_review.conclusion_cards` with a spy that calls the real function. One `GET /assessments/{id}/workpaper` calls it **exactly once**, with the assessment id. Every entry's `data-decision-state` equals the `state` of the same Conclusion's card on `/assessments/{id}/conclusions` (check the `data-state` attribute there).
11. **Counts.** For a fixture with one pending, one rejected, one approved (Priya), one edited, one legacy bulk, one excluded Conclusion and one unconcluded requirement, `wp.counts` equals the exact expected dict, and each value appears in the matching `data-count` cell.
12. **Nothing else moved.**
    - `tests/test_conclusion_approval.py`, `tests/test_analysis_pipeline.py`, `tests/test_no_blended_scoring.py` and `tests/test_white_label.py` pass **unmodified** (covered by the full-suite run).
    - `git diff --stat main --` over the non-modified files in step 4 is empty. Assert that in the Done criteria, not in pytest.

## Done criteria

- `tests/test_workpaper.py` passes. `.venv/bin/pytest -q` passes in full: **430 + N**, where N is the number of new cases. **No existing test file is modified.** (In a fresh `git worktree`, expect the known one-time `_guard_dev_database_untouched` teardown error described in the P2-3 handoff; nothing else.)
- `git diff --stat main` shows changes **only** in:
  - `app/services/workpaper.py`, `app/routers/web.py`;
  - `app/templates/pages/workpaper.html`, `app/templates/components/workpaper_entry.html`, `app/templates/partials/report_summary.html`, `app/templates/components/conclusion_card.html`, `app/templates/pages/conclusions.html`;
  - `tests/test_workpaper.py`, `tasks/todo.md` and this handoff.
- `alembic heads` is still exactly `4e8c1a9d2b57`. `grep -rn "relationship(" app/models/` is empty.
- **Smoke test** (per the project rule; record the outputs). Use a fresh Alembic-built DB (or a **copy** of the dev DB) and the in-process ASGI `TestClient` if a socket bind is refused. Patch `app.routers.analysis.run_gap_analysis` to return **all 41 DPDPA requirements**, one with a quote grounded in an uploaded evidence file. Then:
  1. Run the analysis; `approve` one Conclusion, `edit` another, `reject` a third; run the analysis twice more.
  2. `GET /assessments/{id}/workpaper` → 200. Record the response time (three GETs; report the median) and the counts grid values.
  3. Follow the D-P2-6-G path literally:
     - `GET /assessments/{id}/report-summary` contains the fragment link;
     - the workpaper contains the matching `id`, whose entry shows the full history (paste the `data-revision-action` sequence for the edited requirement);
     - the citation link's `/evidence/{id}` returns 200 with the SHA-256.
  4. Run: `SELECT COUNT(*) FROM conclusion_revisions` before and after the GETs; it must be equal.
  5. **Browser check**, if a browser is available: open the report tab, click "Workpaper trace →" on a critical finding, confirm the page scrolls to that entry with the history visible, click the citation filename, and confirm the evidence page. If no browser is available, say so in Results. Do not claim it.
- `tasks/todo.md` updated (step 5).

## Rollback

- **Code:** `git revert`. This task adds one GET route, one read-only service, two templates and four additive links. There is no schema change and no data written, so a revert leaves no residue.
- **Data:** nothing to roll back. The page never writes.

## Handed forward (must be honoured there)

- **P3-1 (Findings and Actions):** every Finding UI surface must link each of the Finding's Conclusions to `/assessments/{assessment_id}/workpaper#{anchor_for(framework_id, requirement_id)}` (the public helper in `app/services/workpaper.py`), so that P7's "three or fewer clicks" holds for first-class Findings as it does for report rows today. If P3-1 replaces the report's `GapItem` rows, the D-P2-6-G links move with them.
- **P3-2 (report snapshots):** a `report_snapshots` row with `type = "workpaper"` should serialize `build_workpaper`'s output (entries, revisions, claims, resolved citations), not re-derive it, so the live view and the snapshot cannot disagree.
- **Phase 4 (performance):** measure workpaper render against the adversarial review's 2-second threshold on the seeded dataset. This task's smoke timing is the baseline (D-P2-6-L).

## Open questions (deliberately flagged, not resolved here)

1. **Rejection reasons and reviewer notes** (P2-4 open question 1). The workpaper is their first reader and would show them in the history, but they need a `conclusion_revisions` column, and so a migration and a change to P2-4's routes. Decide before P3-1, which will want a reason when a Finding is dismissed.
2. **Follow-up answers, screening results and desk-review coverage** per requirement. They're omitted here (the core response, mapped evidence and desk findings cover the plan's list). Add them if reviewers ask. `FU.{requirement_id}.{n}` keys make follow-ups straightforward for DPDPA; multi-framework follow-ups are keyed by cluster.
3. **Desk-review findings are current-state, not history.** A desk-review re-run replaces them, so the workpaper can't show what analysis saw at the time. The run envelope records only counts (`desk_review_red_flags`, `desk_review_absence`), by P2-3's design. Making desk review append-only is a separate task.
4. **Stale-run threshold.** One hour is a display constant. Revisit if a real request timeout or a sweeper is introduced (P2-3 open question 5 remains open for *data*).

## Results
