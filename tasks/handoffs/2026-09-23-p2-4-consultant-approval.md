# P2-4: Consultant approval workflow: individual approve / edit / reject / reopen of Conclusions, with optimistic locking

**Plan:** `docs/plans/2026-09-21-002-revised-implementation-plan.md`, Phase 2, task P2-4 ("Consultant approval workflow": individual approval only, a Conclusion card with "Approve" / "Edit & Approve" / "Reject" per requirement, one `ConclusionRevision` per action, optimistic locking on `Conclusion.version`; files: new `app/templates/components/conclusion_card.html` plus review routes). Decisions **D3** (individual only: "Each conclusion requires consultant to view evidence + proposal before approving. No bulk-accept.") and **D6** (optimistic locking: "Version columns on Conclusions. Reject save on conflict, show diff.") in `tasks/2026-09-21-adversarial-review.md`. PRD PR-042 (the five outcomes), PR-043 (complete conclusion), PR-044 (human approval) and PR-055 (traceability). The P2-3 handoff's section "Handed forward to P2-4" (`tasks/handoffs/2026-09-23-p2-3-immutable-analysis-pipeline.md`), all four of whose items are closed below.
**Owner:** Claude designs locking logic → Codex builds UI/routes (per `tasks/agent-ownership.md`: "P2-4 Consultant approval workflow + optimistic locking | Claude designs locking logic → Codex builds UI/routes"). The locking rule, the decision state machine, the version protocol and the conflict response are fixed below; the routes, service, templates and tests are Codex's to build to that spec. Every architectural fork is closed here. **If the code forces a deviation from any decision, stop and report it in `## Results`. Do not pick an alternative.** Merge gate: the standard `[AR]` adversarial review (Phase 2 is tagged `[AR: … approvals …]` in `tasks/todo.md`).
**Depends on:** P2-3 (`app/services/analysis_pipeline.py`: `load_conclusion_state`, the lock rule, `ConclusionConflict`, the compare-and-swap; revision `4e8c1a9d2b57`). **Merged**: PR #27, merge commit `8eeccac` is the tip of `main`. (`tasks/todo.md`'s P2-3 line still says "PR #27, open, not yet merged". That line is stale; update it as part of this task, see Done criteria.) P2-2 (`app/services/citations.py`, `resolve_citations`) is merged (PR #25). P2-1 (PR #24) and P2-5 (PR #26) are merged and do not interact with this task beyond P2-1's `Evidence`/`EvidenceVersion` rows that citations resolve to.
**Blocks:** P2-6 (the workpaper shows the consultant decision and revision history this task writes) and the later reader migration (P2-3 open question 1: scoring, PDF and reports move to consultant-approved Conclusions).
**Failing contract suite: none pre-written.** Unlike P2-1 (`tests/test_evidence_service.py`) and P2-3 (`tests/test_analysis_pipeline.py`), I did **not** pre-write a red suite for this task. A grep of `tests/` for `P2-4`, `conclusion_card` and `optimistic lock` finds only one comment in `tests/test_analysis_pipeline.py` (scenario 3: `# Simulate a P2-4 "edit": human content, version bumped, no longer AI-proposed.`). **Codex writes `tests/test_conclusion_approval.py` itself**, from the scenarios in `## Test scenarios`. Follow the fixture pattern of `tests/test_analysis_pipeline.py` and the `http` fixture of `tests/test_evidence_service.py`, both described in step 8. Every scenario listed is required. You may add cases, but you may not drop or weaken one.

## Goal

A consultant can open one page per assessment, see every `Conclusion` as a card (the AI proposal, the evidence summary, resolved citations, the current outcome, the lock state, and any withheld newer AI proposal), and take exactly one decision on exactly one Conclusion per request:

- **Approve** the current content as-is.
- **Edit & Approve**: replace the content with their own and approve it in one step.
- **Reject** the current AI proposal.
- **Reopen** a previously approved or edited Conclusion so that a future analysis run can propose again.

Each decision appends one `ConclusionRevision` and increments `Conclusion.version` through the **same** compare-and-swap P2-3 uses. A decision made against a stale page is refused with HTTP 409, and the card is re-rendered from the current server state with a conflict banner and a diff of what was not saved. There is no bulk path. The legacy `GapReport`/`GapItem` review flow, and everything that reads it, is untouched.

## Current state

Grounded against `8eeccac` on `main`. Baseline `.venv/bin/pytest -q` → **392 passed** (I ran it at `8eeccac`). Re-locate everything by symbol name.

- **`app/models/conclusion.py`**:
  - `Conclusion` has `id`, `assessment_id` FK (indexed), `requirement_id`, `framework_id`, `cluster_id` (nullable), and `outcome`, `rationale`, `evidence_summary`, `gaps_identified`, `risk_level`, `recommended_action` (all NOT NULL, may be `""`). It also has `ai_proposed` (Boolean), `version` (`Integer, default=1`), `created_at`, and `updated_at` (`default=_utcnow, onupdate=_utcnow`). `__table_args__` holds the P2-3 unique index `uq_conclusions_assessment_framework_requirement` on `(assessment_id, framework_id, requirement_id)`.
  - `ConclusionRevision` has `id`, `conclusion_id` FK (indexed), `actor` (String 255), `action` (String 30, free text), `previous_outcome` / `previous_rationale` (nullable; the values **before** the action), `citations_json` (nullable Text), `analysis_run_id` (nullable FK → `analysis_runs.id`, indexed) and `created_at`.
  - No `relationship()` anywhere (house rule).
- **`app/services/analysis_pipeline.py`** (P2-3). The pieces this task reuses:
  - Constants: `HUMAN_DECISION_ACTIONS = ("approved", "edited", "rejected", "reopened")`, `LOCKING_ACTIONS = ("approved", "edited")`, `SUPPORTING_OUTCOMES = ("compliant", "partially_compliant")`, `PIPELINE_ACTOR = "system:analysis"`.
  - `class AnalysisPipelineError(Exception)` and `class ConclusionConflict(AnalysisPipelineError)`. `ConclusionConflict.__init__(self, conclusion_id)` sets the message `f"Conclusion {conclusion_id} changed while analysis was running."`.
  - `@dataclass(frozen=True) class ConclusionState: conclusion: Conclusion; locked: bool; expected_version: int`.
  - `load_conclusion_state(db, *, assessment_id, framework_id) -> dict[str, ConclusionState]` is keyed by `requirement_id` and uses two statements: the framework's Conclusions, then their revisions with `action IN HUMAN_DECISION_ACTIONS` ordered by `ConclusionRevision.created_at, literal_column("conclusion_revisions.rowid")`. The last human action per Conclusion decides `locked = latest_human_action.get(conclusion.id) in LOCKING_ACTIONS`, and `expected_version = conclusion.version`. **This function is the single definition of the lock rule** (D-P2-3-C).
  - **The compare-and-swap** is inline in `record_framework_run`, in the `else:` ("applied") branch after `elif existing.locked:`:
    ```python
    result = db.execute(
        update(Conclusion)
        .where(Conclusion.id == conclusion.id, Conclusion.version == existing.expected_version)
        .values(**content, ai_proposed=True, version=existing.expected_version + 1)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        raise ConclusionConflict(conclusion.id)
    db.expire(conclusion)
    ```
    Nothing else in the codebase writes `Conclusion.version`.
  - The module never commits, and **the word `delete` must not appear anywhere in the file**, comments and docstrings included. `tests/test_analysis_pipeline.py::test_pipeline_code_never_deletes_runs_or_conclusions` greps the raw text.
  - Pipeline revisions use actor `"system:analysis"` and action `proposed` (created/applied) or `proposal_withheld` (locked). Every one of them carries `analysis_run_id` and a non-NULL `citations_json` (`"[]"` = captured, no grounded support). The run envelope (`AnalysisRun.claims_json`) holds one claim per requirement with keys `requirement_id`, `outcome`, `item` (the analyzer item, including `current_state`), `quality`, `conclusion_id`, `revision_id` and `disposition`.
- **Human revisions today:** **no application code writes `approved`/`edited`/`rejected`/`reopened`.** The only writer is `scripts/migrate_legacy.py`:
  - one `proposed` revision per migrated `GapItem`, with `actor = MIGRATION_ACTOR` (`"system:migration"`), `citations_json=None` and `analysis_run_id=None`;
  - plus an `approved` revision whenever `GapItem.reviewed_at` is set, with `actor = item.reviewed_by or "unknown"` (a bare human name such as `"Manager Review"`, **not** namespaced) and `citations_json=None`.

  Because `approve_assessment` (below) stamps `reviewed_at` on every item, every bulk-approved legacy report migrated as individually "approved" Conclusions, and the P2-3 lock rule treats those as **locked**.
- **`app/routers/review.py`** (prefix `/api/assessments`, tag `review`). It operates **only on `GapReport`/`GapItem`/`Assessment`** and imports nothing from `Conclusion`, `AnalysisRun` or `analysis_pipeline`:
  - `disposition_item`: `PATCH /{assessment_id}/review/items/{item_id}`. It validates `ReviewItemUpdate`, edits one `GapItem` (`review_status` accepted/rejected + `reviewed_at`, `compliance_status`, `gap_description`, `risk_level`, `reviewer_notes`), sets `assessment.review_status = "under_review"`, commits, and returns `partials/review_finding_card.html` with an `X-Toast-Message` header via `_toast`.
  - `approve_assessment`: `POST /{assessment_id}/review/approve`. It validates `ReviewApproval(reviewer_name: str)` and refuses with 400 while any item is `draft`/NULL. Then `reviewer_name = approval.reviewer_name.strip() or "Manager Review"`, `assessment.review_status = "approved"`, and a loop stamps `reviewed_by`/`reviewed_at` on **every** `GapItem`. It returns JSON with `HX-Redirect`. **This is the bulk accept D3 forbids for Conclusions.** It writes no `ConclusionRevision` (D-P2-3-A: deliberately so).
  - `reject_assessment`: `POST /{assessment_id}/review/reject`. It validates `ReviewRejection(reviewer_name, rejection_reason)`, sets `assessment.review_status = "rejected"`, and stamps unreviewed items with `reviewed_by` (same `or "Manager Review"` fallback), `reviewer_notes` and `reviewed_at`.
  - Helpers: `_payload(request)` (JSON or form), `_validated(model_type, payload)` (blank → None except `reviewer_name`; `ValidationError` → 422), `_toast(response, message, toast_type)`. Templates come from a module-local `_templates = Jinja2Templates(...)`.
  - `assessment.review_status == "approved"` is what `app/utils/review_gate.py::require_review_approval` checks before releasing the PDF/RFI downloads in `web.py`.
- **Standing guard that constrains where P2-4 code can live:** `tests/test_analysis_pipeline.py::test_legacy_consumers_do_not_read_the_new_tables` greps `app/services/scoring.py`, **`app/routers/review.py`**, `app/routers/reports.py`, `app/routers/remediation.py` and `app/utils/pdf_export.py` for `Conclusion|AnalysisRun|analysis_pipeline`, and requires no match. **Any Conclusion route added to `review.py` breaks that test.** See D-P2-4-A.
- **`app/routers/web.py`**: `review_page` (`GET /assessments/{assessment_id}/review`) renders `pages/review.html` from `GapItem`s, with context `assessment`, `gap_items`, `draft_count`, and `reviewer_name` (the first `reviewed_by` found, else `""`). Every full page lives in `web.py` (for example `evidence_detail_page` at `GET /evidence/{evidence_id}`), rendered with the module-level `templates`. `configure_templates(templates)` (`app/template_config.py`) sets the `branding` global that `base.html` needs.
- **Templates:**
  - `app/templates/components/` holds only `engagement_status_badge.html`, `evidence_status_badge.html` and `status_badge.html`.
  - `app/templates/partials/review_finding_card.html` is the legacy per-`GapItem` card. Its root is `<div … data-review-card … id="review-card-{{ item.id }}">`, its buttons use `hx-patch` + `hx-target="#review-card-{{ item.id }}"` + `hx-swap="outerHTML"`, and it uses Tailwind classes with `dark:` variants.
  - `app/templates/pages/review.html` extends `base.html` and has the "Approve for Release" `hx-post` form.
  - `partials/report_summary.html` links "Open Review Queue →" to `/assessments/{{ assessment_id }}/review`.
- **HTMX:** `base.html` loads `htmx.org@2.0.4`. In htmx 2, 4xx/5xx responses are **not swapped** by default and fire `htmx:responseError`. `app/static/js/app.js` has:
  - a `htmx:responseError` listener that shows the generic toast `'Something went wrong. Please try again.'` (it redirects on 401);
  - a `htmx:beforeSwap` listener that handles only 401;
  - a `htmx:afterSwap` listener that shows `X-Toast-Message`/`X-Toast-Type` response headers as a toast.

  Nothing returns 409 to HTMX today.
- **`app/services/citations.py`**: `loads_citations(raw)` returns `[]` for `None`. `resolve_citations(db, raw) -> list[dict]` returns each stored citation plus `resolved`, `evidence_id`, `filename`, `version_number`, `version_status`, `evidence_status` and `is_current`. **It has no caller yet**, and it is the intended reader for the card.
- **Requirement titles**: `FrameworkRegistry.get_all_controls(framework_id)` (`app/frameworks/registry.py`) returns `Control` objects (`id`, `title`, `description`, `reference`, `criticality`, `tags`). Guard it with `FrameworkRegistry.is_registered(framework_id)`. `Assessment.frameworks` (a property) returns the selected framework ids, defaulting to `["dpdpa"]`.
- **Actor conventions in use:** `"system:analysis"`, `"system:migration"`, `"system:scan-placeholder"`, `"client_link:{prefix}"` (P2-5), and `app/services/evidence.py::CONSULTANT_ACTOR = "consultant"`. The only human-name source today is the form field `reviewer_name`, with the fallback `"Manager Review"`, in `review.py`.
- **Legacy view divergence (named by P2-3, D-P2-3-A):** a re-run resets the matching `GapItem` to `draft` with the new AI verdict even when the Conclusion is locked. `GapItem.framework_id` is nullable (NULL = legacy DPDPA).

## Decisions (made here so they are not relitigated)

### D-P2-4-A. Routes: a new Conclusion-scoped router beside the legacy review routes. `review.py` is not touched.

**Decision:** all P2-4 endpoints live in a **new** module `app/routers/conclusions.py` (`router = APIRouter(prefix="/api/assessments", tags=["conclusions"])`, the same prefix convention as `review.py`), registered in `app/main.py` with `app.include_router(conclusions.router)` directly after `app.include_router(review.router)`. The page lives in `app/routers/web.py`, beside `review_page`, because every full page lives there.

| Method + path | Handler | Purpose |
|---|---|---|
| `GET /assessments/{assessment_id}/conclusions` (in `web.py`) | `conclusions_page` | The review page: one card per Conclusion |
| `POST /api/assessments/{assessment_id}/conclusions/{conclusion_id}/approve` | `approve_conclusion` | action `approved` |
| `POST /api/assessments/{assessment_id}/conclusions/{conclusion_id}/edit` | `edit_conclusion` | action `edited` (this is "Edit & Approve") |
| `POST /api/assessments/{assessment_id}/conclusions/{conclusion_id}/reject` | `reject_conclusion` | action `rejected` |
| `POST /api/assessments/{assessment_id}/conclusions/{conclusion_id}/reopen` | `reopen_conclusion` | action `reopened` |

These are the **only** routes this task adds. Every mutating path contains `{conclusion_id}`.

**Why not "updates to review routes" as the plan's file list says:**
1. The standing guard `test_legacy_consumers_do_not_read_the_new_tables` forbids any `Conclusion` reference in `review.py`. That guard encodes D-P2-3-A: the legacy consumers keep reading `GapItem` until the reader migration.
2. The legacy routes operate on a different model (`GapItem`) whose rows are replaced on every re-run. Mixing both models in one module invites exactly the cross-writes D-P2-4-G forbids.

The plan's intent (review routes for Conclusions) is met by a sibling router with the same prefix.

**Why `reopen` is included although the plan lists three buttons:** P2-3's lock rule makes `reopened` "the **only** way a new AI proposal can reach a locked Conclusion" (D-P2-3-C), and it is already in `HUMAN_DECISION_ACTIONS`. Without a reopen route, an approved Conclusion could never receive a new proposal. The P2-3 handoff hands it forward to P2-4.

### D-P2-4-B. Optimistic locking: the request carries the version the page was rendered with, and P2-3's compare-and-swap is extracted and reused, not copied

**Request shape:** every mutating request carries **`expected_version`** (an int, required; missing or non-int → 422), which is the `Conclusion.version` the card was rendered with. The card emits it as `<input type="hidden" name="expected_version" value="{{ card.conclusion.version }}">` inside each action form. It also carries `reviewer_name` (optional, D-P2-4-F), and for `edit` the five content fields (D-P2-4-C). Bodies are form-encoded (HTMX) or JSON. Parse them with a local `_payload` helper identical to `review.py`'s. **Do not import from `review.py`.**

**One compare-and-swap implementation.** Extract the inline CAS in `record_framework_run` into a public function in `app/services/analysis_pipeline.py`, and call it from both the pipeline and P2-4:

```python
def swap_conclusion(
    db: Session,
    conclusion: Conclusion,
    *,
    expected_version: int,
    values: dict[str, Any],
) -> None:
    """Compare-and-swap one Conclusion on its version (D6).

    Writes ``values`` plus ``version = expected_version + 1`` iff the row still
    holds ``expected_version``; otherwise raises ConclusionConflict. Never commits.
    """
    result = db.execute(
        update(Conclusion)
        .where(Conclusion.id == conclusion.id, Conclusion.version == expected_version)
        .values(**values, version=expected_version + 1)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        raise ConclusionConflict(conclusion.id)
    db.expire(conclusion)
```

In `record_framework_run`, the applied branch becomes `swap_conclusion(db, conclusion, expected_version=existing.expected_version, values={**content, "ai_proposed": True})`, followed by the existing `disposition = "applied"`. Behaviour is byte-identical. `tests/test_analysis_pipeline.py` must stay green **unmodified**, including scenario 10, which patches `load_conclusion_state` through the module global.

**Why extract rather than write a second helper:** D6's guarantee only holds if every writer of `Conclusion.version` uses the same predicate and the same `+1` rule. P2-3 already hands forward "P2-4 must increment `Conclusion.version` on **every** revision it writes … otherwise this check can't detect a concurrent human decision". Two copies of the statement are two places to get that wrong. The extraction is a pure refactor of eight lines in a module P2-3 owns. **Do not** change `ConclusionConflict`'s message: the P2-4 router never shows it to users (D-P2-4-D).

**Why reuse `load_conclusion_state` for the lock bit:** it is the single definition of "locked". P2-4 must not re-derive `locked` from its own query. The service calls it **through the module attribute** (`analysis_pipeline.load_conclusion_state(...)`, after `from app.services import analysis_pipeline`), so tests can patch it exactly as P2-3 scenario 10 does. It loads the whole framework, about 90 rows at most. That is acceptable, and keeps one definition.

**Check order inside a decision (exact):**
1. Load the `Conclusion` by id. If it is missing, or its `assessment_id` differs from the path's, raise `ConclusionNotFound` (404).
2. `state = analysis_pipeline.load_conclusion_state(db, assessment_id=conclusion.assessment_id, framework_id=conclusion.framework_id)[conclusion.requirement_id]`.
3. If `state.expected_version != expected_version`, raise `ConclusionConflict(conclusion.id)` (409). **Staleness is checked before anything else**, so a consultant looking at an out-of-date card is always shown the current state, never a validation error about content they can't see.
4. Derive the decision state (D-P2-4-C) and refuse a disallowed action with `InvalidDecision` (400).
5. For `approved`/`edited`: the PR-043 completeness guard (D-P2-4-E), which raises `InvalidDecision` (400).
6. For `edited`: validate the edits and refuse a no-op edit, raising `InvalidDecision` (400).
7. Capture `previous_outcome, previous_rationale = conclusion.outcome, conclusion.rationale`.
8. `analysis_pipeline.swap_conclusion(db, conclusion, expected_version=expected_version, values=...)`. A concurrent writer between step 2 and here gives `rowcount 0` → `ConclusionConflict` (409).
9. Append the revision (D-P2-4-C), `db.flush()`, and return it. **The service never commits.** The router commits on success, and calls `db.rollback()` on any service exception before rendering the response.

**Conflict response (exact):** HTTP **409**. The router rolls back, then re-reads and renders `components/conclusion_card.html` for the **current** server state (fresh `version`, fresh content, fresh allowed actions), with a `conflict` context. The response headers are:
- `X-Conclusion-Conflict: 1`;
- `X-Toast-Message: Conflict: this conclusion changed since you loaded it. Nothing was saved.`;
- `X-Toast-Type: error`.

The card shows a banner: "This conclusion changed since you loaded it (you had version {{ conflict.submitted_version }}, it is now {{ card.conclusion.version }}). Nothing was saved. Review the current state and decide again." For a conflicting **edit**, it also shows a diff table (field | current value | your unsaved value) for each of the five editable fields whose submitted value differs from the current value. That is D6's "show diff". The edit form is pre-filled with the **current** values, not the unsaved ones, so re-applying stale content is always a deliberate act.

**HTMX wiring for the 409 (exact change to `app/static/js/app.js`):**
- In the existing `htmx:beforeSwap` listener, add: if `event.detail.xhr.status === 409 && event.detail.xhr.getResponseHeader('X-Conclusion-Conflict')`, set `event.detail.shouldSwap = true` and `event.detail.isError = false`.
- In the existing `htmx:responseError` listener, before the generic toast, return early when that header is present. Otherwise, when an `X-Toast-Message` header is present, show `CyberToast.show(decodeURIComponent(msg), 'error')` instead of the generic text.

No other JS changes.

### D-P2-4-C. The four actions: exact state machine, mutations and revisions

**Decision state** (derived per Conclusion; `locked` comes from `load_conclusion_state`, recency is `(created_at, rowid)`, the same ordering P2-3 uses):

| State | Condition |
|---|---|
| `approved` | `locked` and the latest `HUMAN_DECISION_ACTIONS` revision is `approved` |
| `edited` | `locked` and the latest `HUMAN_DECISION_ACTIONS` revision is `edited` |
| `rejected` | not `locked`, the latest `HUMAN_DECISION_ACTIONS` revision is `rejected`, **and** no `proposed` revision is newer than it |
| `pending` | everything else: no human decision yet, latest is `reopened`, or a `rejected` that a newer `proposed` revision has superseded |

**Allowed actions (exact):**

| State | Allowed | Everything else |
|---|---|---|
| `pending` | `approved`, `edited`, `rejected` | 400 `InvalidDecision` |
| `rejected` | `approved`, `edited` | 400 (rejecting the same proposal twice is meaningless) |
| `approved`, `edited` | `reopened` | 400 (change a locked Conclusion by reopening it first) |

**Mutations and revisions (exact).** Every row increments `version` through `swap_conclusion`. The `onupdate` also refreshes `updated_at`. Every revision is appended **after** the swap, with `analysis_run_id=None` and `citations_json=None`.

| Action | `values` passed to `swap_conclusion` | Content | `ai_proposed` | Revision |
|---|---|---|---|---|
| Approve | `{}` | unchanged | unchanged | `action="approved"`, `previous_*` = content before (unchanged) |
| Edit & Approve | `{outcome, rationale, gaps_identified, risk_level, recommended_action, "ai_proposed": False}` | the five fields replaced | `False` | **one** `action="edited"` revision, `previous_*` = content before the edit |
| Reject | `{}` | unchanged | unchanged | `action="rejected"`, `previous_*` = current content |
| Reopen | `{}` | unchanged | unchanged | `action="reopened"`, `previous_*` = current content |

Notes:
- **Edit & Approve writes one `edited` revision, not `edited` + `approved`.** `edited` is already in `LOCKING_ACTIONS`: human-authored content is vouched for by its author. Two rows would double-count one decision.
- **Not editable:** `evidence_summary` (it is the grounded quote, PR-041, and must never be human-typed text posing as evidence), `cluster_id`, `requirement_id` and `framework_id`.
- **Human revisions carry `citations_json = NULL`.** Citations belong to proposals (P2-2's one-representation rule). Every reader takes a Conclusion's citations from its latest `proposed` revision (D-P2-4-H), never from a human revision.
- **The sequence reject → re-run → proposal applied is intended**: `rejected` doesn't lock (D-P2-3-C).
- `ACTION_BY_ROUTE = {"approve": "approved", "edit": "edited", "reject": "rejected", "reopen": "reopened"}`. `set(ACTION_BY_ROUTE.values()) == set(analysis_pipeline.HUMAN_DECISION_ACTIONS)`, and a test asserts it.

### D-P2-4-D. `app/services/conclusion_review.py`: the service API, exact

A new module. It never commits, contains **no** `delete` (a test greps it, as P2-3 does), and never logs Conclusion content or citation excerpts (requirement ids and actions only).

```python
from app.services import analysis_pipeline            # module import: patch seam
from app.services.analysis_pipeline import ConclusionConflict   # re-exported for the router

REVIEWER_ACTOR_PREFIX = "consultant:"
DEFAULT_REVIEWER_NAME = "Manager Review"               # same fallback as review.py
CONCLUSION_OUTCOMES = ("compliant", "partially_compliant", "non_compliant",
                       "not_applicable", "insufficient_evidence")        # PR-042
GAP_OUTCOMES = ("partially_compliant", "non_compliant", "insufficient_evidence")
RISK_LEVELS = ("critical", "high", "medium", "low")
EDITABLE_FIELDS = ("outcome", "rationale", "gaps_identified", "risk_level", "recommended_action")
ACTION_BY_ROUTE = {"approve": "approved", "edit": "edited", "reject": "rejected", "reopen": "reopened"}
ALLOWED_ACTIONS = {
    "pending": ("approved", "edited", "rejected"),
    "rejected": ("approved", "edited"),
    "approved": ("reopened",),
    "edited": ("reopened",),
}

class ConclusionReviewError(Exception):
    status_code = 400
    def __init__(self, message: str): self.message = message; super().__init__(message)
class ConclusionNotFound(ConclusionReviewError): status_code = 404
class InvalidDecision(ConclusionReviewError): status_code = 400

def reviewer_actor(reviewer_name: str | None) -> str:
    """f"consultant:{(reviewer_name or '').strip()[:200] or DEFAULT_REVIEWER_NAME}" """

def decide(
    db: Session,
    *,
    assessment_id: str,
    conclusion_id: str,
    action: str,                     # one of ACTION_BY_ROUTE.values()
    expected_version: int,
    actor: str,
    edits: dict[str, str] | None = None,   # required iff action == "edited"; keys == EDITABLE_FIELDS
) -> ConclusionRevision: ...        # check order exactly as D-P2-4-B

@dataclass(frozen=True)
class ConclusionCard:
    conclusion: Conclusion
    requirement_title: str               # Control.title, else requirement_id
    state: str                           # pending | rejected | approved | edited
    locked: bool                         # from load_conclusion_state
    allowed_actions: tuple[str, ...]     # ALLOWED_ACTIONS[state]
    approval_blocker: str | None         # D-P2-4-E message if approve/edit would be refused, else None
    citations_captured: bool             # latest `proposed` revision exists and its citations_json is not NULL
    citations: list[dict]                # resolve_citations(db, latest proposed revision's citations_json)
    unsupported_assertion: bool          # outcome in SUPPORTING_OUTCOMES and citations_captured and not citations
    last_decision: dict | None           # {"action", "actor_display", "created_at"} of the latest HUMAN_DECISION_ACTIONS revision
    legacy_bulk_approval: bool           # D-P2-4-F
    withheld_proposal: dict | None       # D-P2-4-H: {"outcome", "rationale", "revision_id", "run_id", "created_at", "citation_count"}
    legacy_report_status: str | None     # D-P2-4-G: mapped GapItem outcome iff it differs from conclusion.outcome

def conclusion_cards(db: Session, assessment_id: str) -> list[ConclusionCard]: ...
def conclusion_card(db: Session, *, assessment_id: str, conclusion_id: str) -> ConclusionCard: ...
```

- `decide` is the **only** writer. Its signature takes one `conclusion_id: str`. There is no list-taking variant (D-P2-4-G).
- **Edit validation** (step 6 of D-P2-4-B). Strip every value. The keys must be exactly `EDITABLE_FIELDS`. `outcome ∈ CONCLUSION_OUTCOMES` and `risk_level ∈ RISK_LEVELS`: the router's Pydantic `Literal`s give 422 for a bad value from HTTP, and the service re-checks for direct callers with a 400. After stripping, the PR-043 guard (D-P2-4-E) applies to the **submitted** content. If all five stripped values equal the current ones, raise `InvalidDecision("No changes to save. Use Approve to approve the current content.")`.
- **Ordering of `conclusion_cards`**: frameworks in `Assessment.frameworks` order, with Conclusions for any other `framework_id` after them, sorted by id. Within a framework, the registry's `get_all_controls` order, with ids unknown to the registry last, sorted.
- **Query shape**: one statement for the Conclusions, one for all their revisions (`conclusion_id IN (...)`, ordered by `created_at, rowid`), one `load_conclusion_state` per framework, one for the `AnalysisRun`s referenced by withheld revisions, and one for the assessment's `GapReport` + `GapItem`s. `resolve_citations` runs once per card, which is two small queries per card. That is accepted for a single-user local SQLite app, and there is no hard budget.
- **Router error mapping:**
  - `ConclusionNotFound` → `HTTPException(404, message)`.
  - `InvalidDecision` → a `JSONResponse({"detail": message}, status_code=400)` with `X-Toast-Message` = the URL-encoded message (use `urllib.parse.quote`, because `app.js` calls `decodeURIComponent`) and `X-Toast-Type: error`.
  - `ConclusionConflict` → the 409 card (D-P2-4-B).
  - Success → 200: the re-rendered card with `X-Toast-Message` `Conclusion approved` / `Conclusion edited and approved` / `Conclusion rejected` / `Conclusion reopened` and `X-Toast-Type: success`.

  Every error path calls `db.rollback()` first.
- **Router templates**: a module-local `_templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")` followed by `configure_templates(_templates)` (from `app.template_config`), so the card renders identically from the page and from the API.
- **Pydantic schemas** go in a new `app/schemas/conclusions.py`:
  - `ConclusionDecisionIn(expected_version: int, reviewer_name: str = "")`;
  - `ConclusionEditIn(ConclusionDecisionIn)`, adding `outcome: Literal[<CONCLUSION_OUTCOMES>]`, `rationale: str`, `gaps_identified: str`, `risk_level: Literal["critical", "high", "medium", "low"]` and `recommended_action: str`.

  A validation failure is a 422, the same as `review.py::_validated`.

### D-P2-4-E. PR-043 approval guard: approve and edit refuse incomplete Conclusions

A Conclusion may be `approved` or `edited` only if the resulting content satisfies all of the following. Otherwise `InvalidDecision`, and `approval_blocker` holds the same message so the card can show why the button is disabled:

1. **Evidence support was captured**: the Conclusion has a `proposed` revision, and the latest one has `citations_json IS NOT NULL`. `"[]"` passes: it is explicit evidence absence (D-P2-2-D), which PR-043 allows. `NULL` means "not captured", which occurs only on `migrate_legacy` rows. Message: `"Evidence support was not captured for this conclusion (migrated legacy data). Re-run analysis before approving."`
2. `outcome ∈ CONCLUSION_OUTCOMES`, `rationale.strip()` is non-empty, and `risk_level.strip()` is non-empty. Message: `"A conclusion needs an outcome, a rationale and a risk level before it can be approved."`
3. If `outcome ∈ GAP_OUTCOMES`, then `gaps_identified.strip()` and `recommended_action.strip()` are non-empty. Message: `"A conclusion with gaps needs the identified gaps and a recommended action before it can be approved."`

Reject and reopen are never blocked by this guard. An `unsupported_assertion` (a compliant or partially compliant outcome with `"[]"` citations) is **allowed** to be approved, because that is a consultant judgement, but the card shows a visible warning next to the Approve button.

### D-P2-4-F. Actor identity: `reviewer_actor(reviewer_name)`, and migrated bulk approvals are flagged, not trusted

- **Actor string**: `ConclusionRevision.actor = "consultant:" + (reviewer_name.strip()[:200] or "Manager Review")`. This is the `review.py` convention (a free-text `reviewer_name`, falling back to `"Manager Review"`, because there is no auth; CLAUDE.md: "No auth (single-user MVP)"), namespaced like every other actor in the system (`system:analysis`, `system:migration`, `client_link:…`). The namespace is what makes D3 approvals distinguishable from migrated ones (below). `actor_display` strips the prefix.
- **Where the name comes from**: `pages/conclusions.html` has one page-level `<input id="reviewer-name" name="reviewer_name" placeholder="Your name">`, pre-filled with the context value `reviewer_name`. That value is the prefix-stripped actor of the assessment's most recent revision whose actor starts with `"consultant:"`, else `""`. That's one extra query, mirroring `review_page`'s "first `reviewed_by` found". Every action form carries `hx-include="#reviewer-name"`.
- **Migrated bulk approvals (closes the P2-3 hand-forward):** an `approved` revision whose `actor` does **not** start with `"consultant:"` came from `migrate_legacy.py` mirroring a legacy bulk stamp (its actor is the bare `reviewed_by`). **It is not a D3 individual approval.** Consequences:
  - The lock rule is **unchanged**. Such a Conclusion stays locked, so the pipeline keeps withholding proposals: the conservative reading P2-3 chose, and changing it would edit P2-3's rule.
  - The card sets `legacy_bulk_approval=True` when the latest `HUMAN_DECISION_ACTIONS` revision is such an `approved` row. It then shows the badge "Legacy bulk approval, not individually reviewed" in place of "Approved", and offers **Reopen** (its state is `approved`). After reopening, the consultant can approve individually.
  - The page's summary counts show legacy bulk approvals **separately** from approvals, so they are never counted as D3 approvals.
  - No data is rewritten.

### D-P2-4-G. Individual-only (D3), and the legacy bulk route is left alone

- **Forbidden in this task and in the new modules:**
  - any route, service function or template control that decides more than one Conclusion per request;
  - "approve all", "approve selected", "approve framework", or a select-all checkbox;
  - any `decide` loop in a router.

  Each mutating route takes one `{conclusion_id}` and requires that card's `expected_version`, which only rendering that card supplies. Structural tests pin this (scenario 12).
- **Legacy `approve_assessment` / `reject_assessment` / `disposition_item`: left untouched.** No code change, no deprecation banner, no gating. Reasons:
  1. They stamp `GapItem`s only and write no `ConclusionRevision` (D-P2-3-A), so they are not Conclusion approvals and cannot violate D3 in the new model.
  2. `approve_assessment` sets `assessment.review_status = "approved"`, which `require_review_approval` uses to release the PDF/RFI. Gating or removing it would break report release before scoring and the PDF read Conclusions.
  3. The standing guard forbids Conclusion references in `review.py`.

  Retiring the bulk route belongs to the reader-migration task (P2-3 open question 1).
- **No cross-writes in either direction.** P2-4 actions do not touch `GapItem` (`review_status`, `reviewed_by`, `reviewed_at`, `compliance_status`, …), `GapReport`, or `Assessment.review_status`. The legacy routes do not touch Conclusions.
- **What the report shows in the meantime (closes D-P2-3-A's "P2-4's designer must decide"):** the report, the PDF, scoring and remediation keep showing the `GapItem` view, unchanged. The conclusions page is the individual-approval record. Where the two disagree, the card shows "Report view differs: {{ legacy_report_status }}". `legacy_report_status` is `OUTCOME_BY_STATUS.get(gap_item.compliance_status, UNKNOWN_STATUS_OUTCOME)` for the `GapItem` of the assessment's `GapReport` with the same `(framework_id or "dpdpa", requirement_id)`, and it is set only when it differs from `conclusion.outcome`. Otherwise it is `None`, and it is also `None` when there is no report or no item. It is display only.

### D-P2-4-H. `components/conclusion_card.html`: what it renders (plan: "Conclusion card shows AI proposal, evidence summary, citations")

Context: `card` (a `ConclusionCard`), `assessment`, and optionally `conflict` (`{"submitted_version": int, "submitted_action": str, "diff": list[{"field", "current", "submitted"}]}`). Root element: `<div id="conclusion-card-{{ card.conclusion.id }}" data-conclusion-card data-state="{{ card.state }}" data-version="{{ card.conclusion.version }}" class="…">`. The Tailwind styling follows `partials/review_finding_card.html`, including its `dark:` variants.

It renders, in order:

1. **Header**:
   - the framework id (upper-cased), the `requirement_id` (mono) and `requirement_title`;
   - a state badge: Pending / Rejected / Approved / Edited & approved, or the legacy-bulk badge (D-P2-4-F);
   - "v{{ version }}";
   - a lock indicator when `locked`: "Locked: re-analysis will not overwrite this".
2. **Conflict banner + diff** when `conflict` is set (D-P2-4-B).
3. **Current conclusion**:
   - `outcome` (the PR-042 label), `risk_level`, `rationale`, `gaps_identified` and `recommended_action`;
   - labelled "AI proposal" when `ai_proposed`, else "Consultant-edited";
   - for an edited Conclusion, "AI proposed before edit: {{ previous_outcome }}", taken from the latest `edited` revision.
4. **Evidence summary**: `evidence_summary`, or the text "No grounded supporting quote" when it is `""`.
5. **Citations**, from the latest `proposed` revision via `resolve_citations`:
   - each shows the excerpt, the filename + "v{{ version_number }}", and `location_ref`;
   - a "(superseded version)" note when `not is_current`;
   - the filename links to `/evidence/{{ evidence_id }}` when `resolved`;
   - `[]` renders "No supporting citation (explicit evidence absence)";
   - not captured renders "Evidence support not captured (legacy)";
   - the unsupported-assertion warning when set.
6. **Withheld newer AI proposal**, shown iff the latest `proposal_withheld` revision is newer than **both** the latest `LOCKING_ACTIONS` revision and the latest `proposed` revision. Its outcome and rationale come from that revision's run envelope: in `json.loads(run.claims_json)["claims"]`, the claim whose `revision_id` equals the revision id, taking its `outcome` and `item["current_state"]`. `citation_count` is `len(loads_citations(revision.citations_json))`. Text: "A newer AI proposal was withheld because this conclusion is locked: {{ outcome }}. Reopen to let the next analysis apply it." If the claim can't be found (a malformed envelope), show the banner without the proposal fields and never raise.
7. **Last decision**: "{{ action }} by {{ actor_display }} at {{ created_at }}", when present.
8. **Report view differs** note (D-P2-4-G).
9. **Actions**: exactly `card.allowed_actions`. Each is a `<form hx-post="/api/assessments/{{ assessment.id }}/conclusions/{{ card.conclusion.id }}/<route>" hx-target="#conclusion-card-{{ card.conclusion.id }}" hx-swap="outerHTML" hx-include="#reviewer-name">` with the hidden `expected_version`.
   - Approve is rendered `disabled`, with `approval_blocker` as visible text, when a blocker exists.
   - Edit & Approve is a `<details>` form with a `<select name="outcome">` (the 5 outcomes), `<select name="risk_level">` (the 4 levels) and textareas `rationale`, `gaps_identified` and `recommended_action`, pre-filled with the current values. Its submit button is disabled with the same blocker text when it's blocked for reason 1.
   - Reject and Reopen are single buttons.

Everything is autoescaped. **Never use `|safe`** on Conclusion content, citation excerpts or actor names, because they are client and LLM text.

`pages/conclusions.html` extends `base.html`:
- a breadcrumb in the `pages/review.html` style (`Assessments / {{ company_name }} / Conclusions`);
- a title "Conclusions: individual approval";
- the page-level reviewer-name input;
- summary counts: pending, rejected, approved (individual), edited, and legacy bulk approvals;
- the cards grouped under a framework heading, in `conclusion_cards` order;
- the empty state "No conclusions yet. Run the gap analysis first." when there are none.

Add one link, "Individual conclusion approval →" to `/assessments/{{ assessment.id }}/conclusions`, in the header of `pages/review.html`, and change nothing else in that template.

## Required approach

### 1. `app/services/analysis_pipeline.py`: extract `swap_conclusion` (D-P2-4-B)

- Add `swap_conclusion` exactly as specified, after `load_conclusion_state`.
- Replace the inline CAS in `record_framework_run`'s applied branch with a call to it.
- Add one sentence to the module docstring: the compare-and-swap is shared with the consultant decision service.
- Nothing else changes. Keep the word `delete` out of the file.
- Run `tests/test_analysis_pipeline.py` and confirm 29 passed before continuing.

### 2. `app/schemas/conclusions.py` (new): `ConclusionDecisionIn`, `ConclusionEditIn` (D-P2-4-D)

### 3. `app/services/conclusion_review.py` (new): the API in D-P2-4-D, the check order in D-P2-4-B, the state machine in D-P2-4-C, the guard in D-P2-4-E, and the card view in D-P2-4-F/G/H

### 4. `app/routers/conclusions.py` (new), plus registration in `app/main.py`

Add the four POST routes in D-P2-4-A. Each route:
- validates the matching schema (422);
- calls `conclusion_review.decide(...)` with `actor=reviewer_actor(body.reviewer_name)` and, for edit, `edits={field: getattr(body, field) for field in EDITABLE_FIELDS}`;
- on success, calls `db.commit()` and then renders the card via `conclusion_card(...)`;
- on error, maps it as in D-P2-4-D.

Import the `app.routers` module list in `main.py` alongside the others, and add `app.include_router(conclusions.router)` right after `review.router`.

### 5. `app/routers/web.py`: `conclusions_page`

Add `GET /assessments/{assessment_id}/conclusions`, placed right after `review_page`:
- 404 `"Assessment not found"`;
- context: `assessment`, `cards = conclusion_cards(db, assessment_id)`, `counts`, `reviewer_name` (D-P2-4-F);
- renders `pages/conclusions.html`.

**No 400 when there's no report.** Unlike `review_page`, the page renders its empty state, because Conclusions don't depend on `GapReport`.

### 6. Templates

- `app/templates/components/conclusion_card.html` (new, D-P2-4-H).
- `app/templates/pages/conclusions.html` (new).
- The one-link addition to `app/templates/pages/review.html`.

### 7. `app/static/js/app.js`: the two listener changes in D-P2-4-B, nothing else

### 8. `tests/test_conclusion_approval.py` (new)

Reuse the P2-3 test infrastructure by copying, not importing, because the test modules are not a package API:
- the Alembic-built `db_path` / `engine` (`PRAGMA foreign_keys=ON`) / `db` fixtures, `_seed`, `_item`, `_stub_single`, `gate`, `_conclusions`, `_revisions` and `_human_revision` from `tests/test_analysis_pipeline.py`;
- the `http` `TestClient` fixture from `tests/test_evidence_service.py`, which overrides `get_db` with the shared `db`, points `settings.database_url` at the per-test DB so the lifespan never touches `data/dpdpa.db`, and calls `configure_templates(templates)`.

Produce Conclusions by running the real pipeline (`gate.trigger_analysis(a.id, db)` with `_stub_single`), not by inserting rows, except in scenarios 8 and 9, which need hand-built legacy-shaped revisions. Every scenario in `## Test scenarios` is one or more test functions whose docstrings start with `Scenario N:`.

## Key files

| File | Why it matters |
|---|---|
| `app/services/analysis_pipeline.py` | Extract `swap_conclusion` (step 1). The single CAS and the single lock rule. |
| `app/services/conclusion_review.py` (new) | The only writer of human decisions (D-P2-4-C/D/E/F). |
| `app/routers/conclusions.py` (new) | Four per-Conclusion POST routes and the 409 card (D-P2-4-A/B). |
| `app/schemas/conclusions.py` (new) | Request validation. |
| `app/routers/web.py` | `conclusions_page`. |
| `app/main.py` | Router registration. |
| `app/templates/components/conclusion_card.html` (new), `app/templates/pages/conclusions.html` (new), `app/templates/pages/review.html` (one link) | UI (D-P2-4-H). |
| `app/static/js/app.js` | 409 swap + error toast text. |
| `app/routers/review.py`, `app/services/scoring.py`, `app/utils/pdf_export.py`, `app/routers/reports.py`, `app/routers/remediation.py`, `app/routers/analysis.py`, `scripts/migrate_legacy.py`, `app/models/*`, `alembic/versions/*` | **Not modified.** No schema change, no migration. |
| `tests/test_conclusion_approval.py` (new) | The contract. `tests/test_analysis_pipeline.py` must pass **unmodified**. |

## Non-goals

- **No schema change and no Alembic revision.** Everything fits the existing columns. `action` is free text, and the four values are already P2-3's vocabulary.
- No rejection reason or reviewer notes on Conclusions. `ConclusionRevision` has no note column, and adding one is a schema change (open question 1).
- No bulk action of any kind (D-P2-4-G). No change to `review.py` or the legacy review page's behaviour.
- No move of scoring, the PDF, reports or remediation onto Conclusions, and no change to `Assessment.review_status` or `require_review_approval` (the reader migration, P2-3 open question 1).
- No full revision-history view or run browser. That's **P2-6**, and the card shows only the last decision.
- No `audit_events` rows. Revision rows are this domain's append-only trail (D2, as in P2-3).
- No auth or real user identity (D-P2-4-F). No `relationship()`.

## Test scenarios

All in `tests/test_conclusion_approval.py`. "Nothing written" always means: the revision-id set is unchanged, and `version`, content, `ai_proposed` and `updated_at` all equal a pre-request snapshot.

1. **Approve (the plan's test).** After one pipeline run, `POST …/approve` with `expected_version=1, reviewer_name="Priya"` returns 200.
   - The body contains `id="conclusion-card-{id}"` and `data-state="approved"`, and the `X-Toast-Message` header is set.
   - DB: `version == 2`; content and `ai_proposed` unchanged; `updated_at` advanced.
   - Exactly one new revision: `action="approved"`, `actor="consultant:Priya"`, `previous_outcome`/`previous_rationale` equal to the content, `citations_json IS NULL`, `analysis_run_id IS NULL`.
   - `analysis_pipeline.load_conclusion_state(...)[req].locked is True`.
   - A blank `reviewer_name` gives actor `"consultant:Manager Review"`.
2. **Concurrent approval (the plan's test).** Two `approve` requests, both with `expected_version=1`: the first returns 200 and the second 409.
   - The 409 response has the header `X-Conclusion-Conflict: 1`, and a body with the conflict banner, `data-version="2"` and a hidden `expected_version` value of `2`.
   - Exactly one `approved` revision exists, and `version == 2`.
3. **CAS race between read and write.** Patch `app.services.analysis_pipeline.load_conclusion_state` with a wrapper that calls the real function, then runs `session.execute(text("UPDATE conclusions SET version = version + 1 WHERE id = :id"), …)` and returns the stale state. This is the scenario 10 pattern from `tests/test_analysis_pipeline.py`.
   - `approve` with the correct pre-race version returns 409.
   - No revision is written, and after the rollback the Conclusion's version and content equal the snapshot.
4. **Edit & Approve.** `POST …/edit` with all five fields changed returns 200.
   - The five fields are updated; `evidence_summary` and `cluster_id` are unchanged; `ai_proposed is False`; `version == 2`.
   - Exactly **one** new revision, `action="edited"`, with `previous_*` equal to the AI content. It is locked.
   - Then re-run the analysis with a different stub verdict: the Conclusion is byte-for-byte unchanged, and the newest revision is `proposal_withheld`.
   - `GET /assessments/{id}/conclusions` shows the withheld-proposal banner with the new outcome.
   - Then `reopen` (200), re-run again, and the proposal is applied (`ai_proposed True`, newest revision `proposed`), with the banner gone.
5. **Edit validation.** Each of these writes nothing:
   - an invalid `outcome` or `risk_level` gives 422;
   - a missing `expected_version` gives 422;
   - a whitespace-only `rationale` gives 400;
   - `outcome="non_compliant"` with a blank `gaps_identified` gives 400;
   - five fields identical to the current ones give 400 ("No changes to save…"), with the header `X-Toast-Message` present.
6. **Reject.**
   - `reject` returns 200: content unchanged, `version == 2`, one `rejected` revision, not locked, card state `rejected`.
   - A second `reject` (correct version) gives 400.
   - `approve` after reject gives 200.
   - A separate Conclusion: reject, then a re-run applies the new proposal (`disposition == "applied"` in the run's claims); card state is `pending`, and `reject` is allowed again.
7. **Reopen.**
   - `reopen` on a `pending` Conclusion gives 400.
   - On an `approved` one it returns 200: a `reopened` revision, `version` incremented, content unchanged, not locked, state `pending`.
8. **State machine matrix.** Parametrize the states {pending, rejected, approved, edited}, built with `_human_revision` plus a matching `version` bump, against the four routes. Allowed pairs (D-P2-4-C) give 200, and every other pair gives 400 with nothing written. Also assert:
   - `set(ACTION_BY_ROUTE.values()) == set(HUMAN_DECISION_ACTIONS)`;
   - `ALLOWED_ACTIONS` exactly as specified;
   - every successful action increments `version` by exactly 1 (the P2-3 hand-forward).
9. **PR-043 guard.** Each blocked case writes nothing.
   - Build a Conclusion whose only `proposed` revision has `citations_json=None` and `actor="system:migration"` (the `migrate_legacy` shape). `approve` and `edit` give 400 with the "not captured" message; `reject` gives 200. Its card shows `approval_blocker` and a disabled Approve.
   - A `compliant` Conclusion whose proposal cited nothing (`"[]"`): its card shows the unsupported-assertion warning, and `approve` gives 200.
   - A `non_compliant` Conclusion with `recommended_action=""`: `approve` gives 400.
10. **Legacy bulk approval flag.** A Conclusion with an `approved` revision whose actor is `"Manager Review"`, i.e. no prefix.
    - Its card shows `legacy_bulk_approval` (the badge text), state `approved`, and only Reopen.
    - The page counts it under legacy bulk, not approved.
    - After `reopen` and then `approve` as `"Priya"`, it counts as approved.
11. **Stale, foreign and unknown ids.**
    - For each of the four routes, a stale `expected_version` gives 409 and nothing written.
    - A Conclusion id belonging to another assessment gives 404; an unknown id gives 404.
12. **Individual-only (D3) structural guards.**
    - The set of app routes whose path contains `/conclusions` equals exactly the five in D-P2-4-A. Every POST among them contains `{conclusion_id}`.
    - `inspect.signature(conclusion_review.decide)` has `conclusion_id` and no parameter annotated as a list.
    - `grep -niE "approve all|approve selected|select all|approve framework"` over `components/conclusion_card.html`, `pages/conclusions.html`, `app/routers/conclusions.py` and `app/services/conclusion_review.py` is empty. This checks for a bulk-*action* path, not the word "bulk" itself — D-P2-4-F's `legacy_bulk_approval` field and its "Legacy bulk approval, not individually reviewed" badge text are the one legitimate, read-only use of that word (it labels a fact about history, not an action a consultant can take) and must still be present.
    - `"delete"` does not appear in `conclusion_review.py`, and neither does `.commit(`.
13. **Legacy path untouched (the P2-3 zero-diff invariant).**
    - After approve, edit and reject on Conclusions, the assessment's `GapItem` rows (`review_status`, `reviewed_by`, `reviewed_at`, `compliance_status`, `reviewer_notes`) and `Assessment.review_status` equal a pre-snapshot.
    - Conversely, `POST /api/assessments/{id}/review/approve` (after accepting all items through `disposition_item`) still returns 200 with the `HX-Redirect` header and writes **no** `ConclusionRevision`.
    - `git diff --stat main -- app/routers/review.py app/services/scoring.py app/utils/pdf_export.py app/routers/reports.py app/routers/remediation.py app/routers/analysis.py` is empty. Assert this in the Done criteria, not in pytest.
    - `tests/test_analysis_pipeline.py::test_legacy_consumers_do_not_read_the_new_tables` still passes.
14. **Page render.**
    - `GET /assessments/{id}/conclusions` returns 200, with one card per Conclusion, each with its hidden `expected_version`.
    - A grounded citation's excerpt and filename appear, linked to `/evidence/{evidence_id}`.
    - The "Report view differs" note appears for a locked Conclusion after a re-run changed the `GapItem` verdict.
    - The reviewer-name input is pre-filled with the last `consultant:` actor.
    - An assessment with no Conclusions renders the empty state with 200. An unknown assessment gives 404.
    - Client text containing `<script>` in `rationale` is rendered escaped.
15. **CAS extraction is behaviour-preserving.** `analysis_pipeline.swap_conclusion` exists and raises `ConclusionConflict` on a version mismatch, leaving the row untouched. `tests/test_analysis_pipeline.py` passes unmodified (covered by the full-suite run).

## Done criteria

- `tests/test_conclusion_approval.py` passes. `.venv/bin/pytest -q` passes in full: **392 + N**, where N is the number of new cases. **No existing test file is modified**, `tests/test_analysis_pipeline.py` included. (In a fresh `git worktree`, expect the known one-time `_guard_dev_database_untouched` teardown error described in the P2-3 handoff's Current state; nothing else.)
- `git diff --stat main` shows **no** change to:
  - `app/routers/review.py`, `app/services/scoring.py`, `app/utils/pdf_export.py`, `app/routers/reports.py`, `app/routers/remediation.py`, `app/routers/analysis.py`;
  - `scripts/migrate_legacy.py`, `app/models/`, `alembic/versions/`;
  - any golden fixture.
- `alembic heads` is still exactly `4e8c1a9d2b57`. `grep -rn "relationship(" app/models/` is empty.
- `tasks/todo.md`: correct the P2-3 line to **Merged: PR #27**, and add a P2-4 line with the status and a link to this handoff's Results.
- **Smoke test** (per the project rule; record the outputs). Use a **copy** of the dev DB, or a fresh Alembic-built DB if none is usable, as P2-3's Results did. Use the in-process ASGI `TestClient` if the sandbox refuses a socket bind. Patch `app.routers.analysis.run_gap_analysis` to two fixed items, then:
  1. Run the analysis once. `GET /assessments/{id}/conclusions` returns 200 with two cards.
  2. `POST …/approve` on card A with `expected_version=1` gives 200. Repeat the identical request: 409, with the header `X-Conclusion-Conflict: 1`.
  3. `POST …/edit` on card B gives 200.
  4. Run: `SELECT c.requirement_id, c.version, c.ai_proposed, r.action, r.actor FROM conclusions c JOIN conclusion_revisions r ON r.conclusion_id = c.id WHERE c.assessment_id = ? ORDER BY c.requirement_id, r.created_at, r.rowid` → A: `proposed`, `approved` (v2). B: `proposed`, `edited` (v2, `ai_proposed` 0).
  5. Re-run the analysis. Both Conclusions are unchanged, and each has a newest `proposal_withheld` revision. The page shows the withheld banner on both.
  6. `GET /assessments/{id}?tab=report` still renders, and the legacy `/review` page still renders its `GapItem` cards.
  7. **Browser check**, if a browser is available: load the page, open two tabs, approve in one and then approve in the other. The second tab's card is swapped for the conflict version, with no generic "Something went wrong" toast. If no browser is available, say so in Results. Do not claim it.

## Rollback

- **Code:** `git revert`. No schema changed. Human revisions already written stay as inert rows that the reverted app never reads except through the P2-3 lock rule, which still honours them: approved and edited Conclusions stay locked. The `swap_conclusion` extraction reverts cleanly, because the inline CAS it replaced is behaviourally identical.
- **Data:** nothing in this task deletes or rewrites history. Every content change (`edited`) is preceded by the swap and followed by a revision holding the prior outcome and rationale. To undo a mistaken approval, **reopen** it. Never delete the revision.

## Open questions (deliberately flagged, not resolved here)

1. **Rejection reasons and reviewer notes on Conclusions.** They need a column on `conclusion_revisions`, which means a migration. The legacy `ReviewRejection.rejection_reason` has no Conclusion equivalent yet. Decide with P2-6, which is the first reader.
2. **Retiring the legacy bulk `approve_assessment`.** This belongs to the reader-migration task (P2-3 open question 1). The release gate (`require_review_approval`) must then move to "every in-scope Conclusion individually approved or edited, excluding legacy bulk approvals".
3. **Edit-then-citation mismatch.** An `edited` Conclusion keeps showing the citations of the AI proposal it replaced. Whether consultants should attach their own citations to an edit is a P2-6/Phase 3 question. P2-2's `attach_citations` refuses a second write to a revision, so it would need a new revision type.
4. **The ConclusionConflict message** still says "changed while analysis was running". It is never shown to users by P2-4. Rename it when P2-3's module is next touched for another reason.

## Results

Implementation stopped before completion because the handoff contains two mutually
exclusive requirements:

- D-P2-4-F and D-P2-4-H require the `ConclusionCard.legacy_bulk_approval`
  field and the visible badge text "Legacy bulk approval, not individually
  reviewed". The page must also count legacy bulk approvals separately.
- Test scenario 12 requires
  `grep -niE "approve all|approve selected|select all|bulk"` over
  `app/services/conclusion_review.py`, `components/conclusion_card.html`, and
  `pages/conclusions.html` (plus the router) to return no matches.

The mandated field and user-visible copy necessarily match the mandated `bulk`
pattern, so both contracts cannot pass literally. No alternate spelling,
dynamic source construction, or weakened structural assertion was chosen.

Partial work present when the contradiction was confirmed:

- Extracted `analysis_pipeline.swap_conclusion(...)` exactly as specified and
  rewired the pipeline's applied branch to use it.
- Added the initial schemas and decision/card service implementation, including
  the required `legacy_bulk_approval` field whose name demonstrates the conflict.
- Updated the stale P2-3 tracker status and marked P2-4 in progress.

Verification completed before stopping:

- `.venv/bin/pytest -q tests/test_analysis_pipeline.py` — 29 passed.

The routes, templates, contract suite, smoke test, full-suite run, and commits
were not completed. No decision D-P2-4-A through H was intentionally deviated
from; implementation awaits clarification of scenario 12's structural grep.

### Resolution (Claude)

Codex's own recommendation was correct and is applied: Scenario 12's grep (line
486, live version) is narrowed from the bare word `bulk` to bulk-*action*
phrases (`approve all|approve selected|select all|approve framework`). The
invariant D3 actually protects is "no bulk-approve action route or control,"
not "the string 'bulk' may never appear" — `legacy_bulk_approval` and its badge
text are a read-only label describing history, not an action, so they survive
the narrowed grep unmodified. D-P2-4-F/H are unchanged. Re-dispatched to
continue from the same branch.
