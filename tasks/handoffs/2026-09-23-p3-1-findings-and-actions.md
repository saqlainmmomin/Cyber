# P3-1: Findings and Actions: consultant-created Findings from individually approved Conclusions, with append-only Action history

**Plan:** `docs/plans/2026-09-21-002-revised-implementation-plan.md`, Phase 3, task P3-1 ("Consultant creates Findings from approved Conclusions (one Finding may reference multiple Conclusions across frameworks)"; "Each Finding gets one or more Actions with owner, target date, status"; "Action history stored as JSON array in `actions.history_json` (D2: replaces ActionUpdate + ClosureVerification tables)"; "Each status change appends `{actor, action, timestamp, notes}` to history"; test: "Create finding from conclusion, add action, update action status, verify history_json contains both entries"), and the plan's Target Schema rows `findings` (status `open | in_progress | resolved | accepted_risk`) and `actions` (status `open | in_progress | closed | verified`). Decisions **D2** ("JSON for claims/citations/action-history. One generic `audit_events` table.") and **D3** ("Individual only … No bulk-accept.") in `tasks/2026-09-21-adversarial-review.md`, and **P7** ("A reviewer can navigate from a Finding to its Conclusion's full proposal/edit/approval history in three or fewer clicks"). PRD `docs/product/2026-09-21-cyberassess-product-requirements.md`: glossary "Finding: An approved, reportable gap or observation derived from a Conclusion and bound to its Assessment origin", **PR-050** (Findings preserve their originating Assessment, framework, Requirement, Conclusion revision), **PR-051** ("update history is append-only; Closed requires closure Evidence plus consultant verification"), **PR-055** (trace any Finding to its history). The P2-6 handoff's "Handed forward" item for P3-1 (`tasks/handoffs/2026-09-23-p2-6-workpaper-view.md`) is closed by D-P3-1-K.
**Owner:** Claude designs the history pattern → Codex implements (per `tasks/agent-ownership.md`: "P3-1 Findings and Actions | Claude designs history pattern → Codex implements"). The cardinality, eligibility rule, legacy coexistence rule, history schema, state machine, locking and every route are fixed below. **If the code forces a deviation from any decision, stop and report it in `## Results`. Do not pick an alternative.** Merge gate: the standard `[AR]` adversarial review (`tasks/todo.md` tags Phase 3 `[AR: report immutability, provenance, closure verification]`; provenance is D-P3-1-C and the closure boundary is D-P3-1-E).
**Depends on:** P2-4 (`app/services/conclusion_review.py`: decision state, `legacy_bulk_approval`, `reviewer_actor`) and P2-6 (`app/services/workpaper.py`: `anchor_for`, `WorkpaperEntry`). Both **merged**; `main` is at `9bcd972` (PR #29, P2-6). (`tasks/todo.md`'s P2-6 line still says "PR #29, open, not yet merged". That line is stale; update it as part of this task, see Done criteria.)
**Blocks:** P3-4 (remediation tracking: close/verify/reopen, closure evidence, engagement rollup) builds on the history schema and state machine defined here. P3-3 (PDF "finding details") will read `Finding` rows.
**Parallel with P3-2:** the ownership doc says P3-1 and P3-2 have no file overlap. The one shared file is `app/services/workpaper.py`, which this task edits (one dataclass field and one query, D-P3-1-K). P3-2 must only **call** `build_workpaper` (its hand-forward says to serialize it), not edit that file. If P3-2 lands first and did edit it, rebase and re-apply D-P3-1-K by hand.
**Failing contract suite: none pre-written.** A grep of `tests/` for `P3-1`, `Finding(` and `history_json` finds only `tests/test_migrate_legacy.py` (it asserts the migration's own single `imported` history entry, `json.loads(action.history_json)`) and one import in `tests/test_analysis_pipeline.py` (scenario 14, asserting the migration creates **no** Finding for a pipeline-owned assessment). Neither tests anything this task builds. As with P2-4 and P2-6, **Codex writes `tests/test_findings.py` itself** from `## Test scenarios`, following the fixture pattern of `tests/test_conclusion_approval.py` and `tests/test_workpaper.py` (step 8). Every scenario listed is required. You may add cases, but you may not drop or weaken one.

## Goal

A consultant opens `/assessments/{assessment_id}/findings` and:

1. sees every **individually approved or edited** Conclusion with a gap outcome that has no Finding yet, and turns **one** of them into a Finding per request. The request also creates the Finding's first Action, so no Finding is ever created without one;
2. adds further Actions to any Finding, each with a title, an optional owner and an optional target date;
3. moves an Action between `open` and `in_progress`, and edits its title, owner or target date. Every such change **appends** one entry to `actions.history_json`, and nothing in that array is ever rewritten or removed;
4. follows each Finding to its Conclusion's full history on the workpaper in one click. From the workpaper, each Conclusion's entry links back to the Findings that cite it.

Closing and verifying an Action is **not** in this task. It needs closure evidence and a verification event (PR-051), which is P3-4's scope. This task reserves those statuses and history actions for it.

## Current state

Grounded against `9bcd972` on `main`. Baseline `.venv/bin/pytest -q` → **443 passed, 115 warnings** (I ran it at `9bcd972`). `alembic heads` → `4e8c1a9d2b57 (head)`. Re-locate everything by symbol name.

- **`app/models/finding.py`, `Finding`** (P1-2): `id`, `assessment_id` (FK → `assessments.id`, indexed), **`conclusion_id` (FK → `conclusions.id`, indexed, a single column)**, `title` (String 255), `description` (Text), `severity` (String 20), `priority` (Integer), `status` (String 30), `created_at`, `updated_at` (`onupdate=_utcnow`). **All NOT NULL. No `__table_args__`, so there is no uniqueness on `conclusion_id`.** There is no join table to Conclusions and no column for the Conclusion revision or version.
- **`app/models/action.py`, `Action`** (P1-2): `id`, `finding_id` (FK → `findings.id`, indexed), `title` (String 255, NOT NULL), `owner` (String 255, **nullable**), `target_date` (`DateTime(timezone=True)`, **nullable**), `status` (String 30, NOT NULL), **`history_json` (Text, NOT NULL, no default)**, `created_at`, `updated_at` (`onupdate`). There is no version column. Nothing in the model enforces the shape of `history_json`.
- **`app/models/audit_event.py`, `AuditEvent`**: `id`, `actor` (255), `action` (100), `entity_type` (100), `entity_id` (36), `metadata_json` (nullable Text), `created_at`. Its writers today are `app/services/evidence.py::_audit` (`metadata_json=json.dumps(metadata, sort_keys=True)`) and `app/services/magic_links.py`.
- **No `relationship()` anywhere** in `app/models/` (house rule).
- **The only writer of `findings`/`actions` today is `scripts/migrate_legacy.py::run_migration`**, and **no code in `app/` reads either table**. For each legacy `GapItem` with `remediation_status is not None`, it creates, in order:
  1. a `Finding` looked up first by `select(Finding).where(Finding.assessment_id == assessment.id, Finding.conclusion_id == conclusion.id)` with **`scalar_one_or_none()`**; if absent, `Finding(title=item.requirement_title, description=item.gap_description, severity=item.risk_level, priority=item.remediation_priority, status=map_finding_status(remediation_status))`;
  2. an `Action` looked up by `select(Action).where(Action.finding_id == finding.id)`, again with **`scalar_one_or_none()`**; if absent, `Action(title=item.remediation_action, owner=item.remediation_owner, target_date=item.remediation_target_date, status=map_action_status(...), history_json=json.dumps([{"actor": MIGRATION_ACTOR, "action": "imported", "timestamp": <now UTC isoformat>, "notes": "Migrated from legacy GapItem remediation fields"}]))`.

  Constants: `FINDING_STATUSES = frozenset({"open", "in_progress", "resolved", "accepted_risk"})` (unknown values fall back to `"open"` with a warning), `ACTION_STATUSES = frozenset({"open", "in_progress", "closed", "verified"})`, `MIGRATION_ACTOR = "system:migration"`. `map_action_status` only ever returns `"closed"` (when `remediation_closed_at` is set) or `"open"`.

  The migration is **re-runnable** and processes legacy assessments on every run. It skips (with a warning) any assessment that has an `AnalysisRun` (P2-3, D-P2-3-H), so pipeline-owned assessments never get migrated Findings. **Consequence for this task:** once a consultant adds a second Action to a migrated Finding, the next `run_migration` raises `MultipleResultsFound` on the Action lookup. D-P3-1-J closes this.
- **Legacy-migrated Conclusions** carry a `proposed` revision by `system:migration` with `citations_json = NULL`, plus an `approved` revision by the bare `reviewed_by` name when the `GapItem` was bulk-approved. In P2-4's terms (`conclusion_review.py`) that is `legacy_bulk_approval=True`. P2-4's PR-043 guard (`EVIDENCE_NOT_CAPTURED`) also refuses any individual approve or edit while the latest `proposed` revision has NULL citations. **So a migrated Conclusion cannot become individually approved until analysis is re-run on its assessment.** After a re-run the assessment is pipeline-owned, and its migrated Findings, if any, stay in place.
- **`app/services/conclusion_review.py`** (P2-4). I read it in full. What this task reuses:
  - constants `REVIEWER_ACTOR_PREFIX = "consultant:"`, `DEFAULT_REVIEWER_NAME = "Manager Review"`, `GAP_OUTCOMES = ("partially_compliant", "non_compliant", "insufficient_evidence")`, `RISK_LEVELS = ("critical", "high", "medium", "low")`;
  - `reviewer_actor(reviewer_name) -> str`, which gives `f"consultant:{name.strip()[:200] or 'Manager Review'}"`;
  - `ConclusionCard` (fields `conclusion`, `requirement_title`, `state`, `locked`, `allowed_actions`, `approval_blocker`, `citations_captured`, `citations`, `unsupported_assertion`, `last_decision`, `legacy_bulk_approval`, `withheld_proposal`, `legacy_report_status`, `previous_outcome`);
  - `conclusion_cards(db, assessment_id) -> list[ConclusionCard]` (read-only; returns `[]` for an unknown assessment or no Conclusions) and `conclusion_card(db, *, assessment_id, conclusion_id)` (calls `conclusion_cards` and raises `ConclusionNotFound` if the id is absent).
  
  **`state` is the single derived decision state.** It is `approved` or `edited` iff `load_conclusion_state` says `locked` **and** the latest `HUMAN_DECISION_ACTIONS` revision (ordered `created_at, rowid`) is `approved` or `edited` (`_decision_state`). So `state in ("approved", "edited")` is exactly "locked by a human decision", and `legacy_bulk_approval` is `True` when that latest human revision is `approved` by an actor without the `consultant:` prefix. **The lock bit alone is not the right eligibility test:** a migrated bulk approval is locked too.
- **`app/services/analysis_pipeline.py`**: `HUMAN_DECISION_ACTIONS = ("approved", "edited", "rejected", "reopened")`, `LOCKING_ACTIONS = ("approved", "edited")`.
- **`app/services/workpaper.py`** (P2-6). I read it in full.
  - It defines `anchor_for(framework_id, requirement_id) -> f"wp-{framework_id}-{requirement_id}"`, `LEGACY_BULK_LABEL = "Legacy bulk approval, not individually reviewed"`, and frozen dataclasses `RunSummary`, `ClientResponse`, `RevisionEntry`, `WorkpaperEntry` (fields `card`, `anchor`, `in_scope`, `client_response`, `mapped_evidence`, `desk_review_findings`, `ai_proposal`, `revisions`, none with defaults), `FrameworkSection` and `Workpaper`.
  - `build_workpaper(db, assessment, *, now=None)` calls `conclusion_review.conclusion_cards` once, then issues its own read statements. It never writes.
  - The desk-review findings it shows are **current state, not history**, because a desk-review re-run replaces them (P2-6 open question 3). Nothing in the workpaper reads `findings`. P2-6's non-goal said "No reading of the `findings`/`actions` tables (P3-1 designs Findings)", and its hand-forward says: "every Finding UI surface must link each of the Finding's Conclusions to `/assessments/{assessment_id}/workpaper#{anchor_for(framework_id, requirement_id)}`".
  - `components/workpaper_entry.html` root: `<article data-workpaper-entry id="{{ entry.anchor }}" …>`. Its header link row (`<div class="mt-3 flex flex-wrap items-center gap-3 text-xs">`) holds the lock text and the link "Decide on the conclusions page →".
- **Standing guards this task must not break** (all in the existing suite):
  - `tests/test_conclusion_approval.py::test_scenario_12_individual_only_structural_guards`: the set of app routes whose path contains **`/conclusions`** equals exactly P2-4's five, and `grep -niE "approve all|approve selected|select all|approve framework"` over `components/conclusion_card.html`, `pages/conclusions.html`, `app/routers/conclusions.py` and `app/services/conclusion_review.py` is empty.
  - `tests/test_workpaper.py::test_scenario_9_workpaper_is_structurally_and_behaviorally_read_only`:
    - the routes containing **`/workpaper`** are exactly `{("GET", "/assessments/{assessment_id}/workpaper")}`;
    - `pages/workpaper.html` and `components/workpaper_entry.html` must not match `<form|<button|hx-post|hx-put|hx-patch|hx-delete|expected_version|\|\s*safe\b`;
    - `app/services/workpaper.py` must not contain `delete` (any case), `db.add(`, `db.add_all(`, `db.merge(`, `.commit(`, `.flush(`, `swap_conclusion` or `decide(`;
    - the rendered workpaper page must not contain `data-conclusion-card`.
  - `tests/test_workpaper.py` scenario 11 asserts `wp.counts == expected` **as an exact dict**, and scenarios 1/3 count `data-workpaper-entry` and `id="wp-…"` occurrences.
  - `tests/test_analysis_pipeline.py::test_legacy_consumers_do_not_read_the_new_tables` greps `scoring.py`, `review.py`, `reports.py`, **`remediation.py`** and `pdf_export.py` for `Conclusion|AnalysisRun|analysis_pipeline`.
  - `tests/test_white_label.py` forbids the literal `CyberAssess` in `app/templates/`, and `tests/test_no_blended_scoring.py` forbids `overall_score` in templates.
- **Routers and pages.** Every full page lives in `app/routers/web.py` with the module-level `templates`. `conclusions_page` (`GET /assessments/{assessment_id}/conclusions`) computes `reviewer_name` inline, from the most recent `ConclusionRevision` of the assessment whose actor starts with `consultant:` (prefix removed), else `""`. `web.py` already binds a local variable named `findings` (desk review, in `desk_review_status`), and imports services as modules with aliases (`from app.services import evidence as evidence_service, workpaper`). The API routers (`conclusions.py`, `remediation.py`, `review.py`) use `prefix="/api/assessments"`, a local `_payload` (JSON or form), `_validated` (`ValidationError` → 422), module-local `_templates` + `configure_templates`, and an `X-Toast-Message`/`X-Toast-Type` header helper. **No route path in the app contains `/findings` today.**
- **Legacy remediation UI:** `app/routers/remediation.py` (`PATCH /api/assessments/{id}/gap-items/{item_id}/remediation`, `GET …/remediation-summary`) edits `GapItem.remediation_*`. It is rendered inside `partials/report_summary.html`. It knows nothing about `Finding`/`Action`. **The portfolio dashboard (`app/services/portfolio.py`, `pages/dashboard.html`, `pages/engagement_detail.html`) reads no remediation or Finding data.** Retiring the `GapItem` remediation path is P3-4 ("Migrate remediation fields from GapItem to standalone Actions").
- **HTMX error handling (`app/static/js/app.js`)**: the `htmx:responseError` listener returns early for `X-Conclusion-Conflict`. For any other 4xx/5xx it shows `decodeURIComponent(X-Toast-Message)` when that header is present, else a generic toast. Error responses are not swapped. **So a 400/409 JSON response with an encoded `X-Toast-Message` shows its own message with no JS change.**
- **Priority semantics:** `GapItem.remediation_priority` / the analyzer's `remediation_priority` is 1–4 (`app/dpdpa/prompts.py`: 1 immediate, 2 short-term, 3 medium-term, 4 long-term).

## Decisions (made here so they are not relitigated)

### D-P3-1-A. Cardinality: one Conclusion per Finding (the existing FK), and at most one Finding per Conclusion. **No join table in this task.** This is a documented deviation from the plan's parenthetical.

**Decision:** a Finding references exactly one Conclusion, through the existing `findings.conclusion_id`. A Conclusion has **at most one** Finding of any origin (consultant-created or migrated), and the service enforces that (D-P3-1-J). **No schema change and no Alembic revision.** The plan's "(one Finding may reference multiple Conclusions across frameworks)" is **not** implemented here. For a multi-framework assessment, each framework's Conclusion gets its own Finding.

**Why, in order of weight:**
1. **The plan contradicts itself, and the PRD sides with the schema.** The plan's own Target Schema declares `findings.conclusion_id: UUID str (FK → conclusions.id)`, singular, and P1-2 built exactly that. The PRD glossary defines a Finding as "derived from **a** Conclusion and bound to its Assessment origin". PR-050 requires a Finding to preserve its originating "framework, Requirement, … Conclusion revision", all singular. The PRD's relationship rules put the many-to-many on the **other** side: "An **Action** may address several Findings". A multi-Conclusion Finding would have no single framework or requirement to preserve.
2. **A join table is a schema change, and schema changes are Claude-owned and foundational.** `tasks/agent-ownership.md` lists schema migrations as the canonical "Foundational/gating" Claude-owned work. A Codex-implemented task must not add a table or an Alembic revision on its own.
3. **Cross-framework consolidation already has a home.** PR-053 consolidates approved Findings in the **integrated Engagement report** (P3-3) "while clearly separating Assessment and framework results". Consolidating at the Finding level would do exactly the blending PR-053 forbids.
4. **Nothing downstream needs it yet.** P3-3 and P3-4 can read `Finding.conclusion_id` directly.

**Deviation, stated for the reviewer:** the plan says a Finding *may* reference multiple Conclusions. This task makes it reference exactly one. If consultants need cross-framework grouping, it's a follow-up with its own Claude-designed schema change: a `finding_conclusions` join table, with `findings.conclusion_id` kept as the originating Conclusion (open question 1). Implement nothing toward it here. **Do not** store extra Conclusion ids in `description`, in `history_json` or in `audit_events` metadata as a workaround.

### D-P3-1-B. Who can create a Finding, from what, and how many per request

- **Eligible Conclusion (exact):** with `card = conclusion_review.conclusion_card(db, assessment_id=…, conclusion_id=…)`, a Conclusion is eligible iff **all** of:
  1. `card.state in ("approved", "edited")`;
  2. `not card.legacy_bulk_approval`;
  3. `card.conclusion.outcome in conclusion_review.GAP_OUTCOMES`;
  4. no `Finding` row exists with `conclusion_id == conclusion.id`.
- **Why `state`, not `locked`:** `locked` is also true for a migrated bulk approval, and P2-4 (D-P2-4-F) ruled that "It is not a D3 individual approval". The plan says "approved Conclusions", and in this system only a D3 approval counts as one. Using `card.state` also reuses P2-4's single derivation rather than re-deriving it. **Do not** import `conclusion_review`'s private helpers (`_decision_state`, `_revisions`, …).
- **Why only gap outcomes:** a Finding here exists to carry remediation Actions, and a `compliant` or `not_applicable` Conclusion has no gap to remediate. The PRD glossary also allows "observations". Findings from compliant Conclusions are deferred (open question 2).
- **Who:** any consultant. There's no auth (CLAUDE.md: "No auth (single-user MVP)"). The actor is `conclusion_review.reviewer_actor(reviewer_name)`, the same free-text name and `consultant:` namespace as P2-4.
- **One Conclusion per request, by construction.** `create_finding` takes `conclusion_id: str`, and the request schema types it `str | None` (a JSON list gives 422). No route, form or service function accepts several Conclusions. There's no "select all", no checkbox list and no loop over `create_finding` in a router.
- **D3 is not the reason, and it doesn't forbid anything here.** D3 governs **approving Conclusions** ("Each conclusion requires consultant to view evidence + proposal before approving. No bulk-accept."). Creating a Finding is a separate act, taken **after** that individual approval. It approves nothing and changes no Conclusion. The one-per-request shape follows from D-P3-1-A (one Conclusion per Finding) and from P2-4's page pattern (one form per card). It is not a D3 rule. Findings creation must not write any `ConclusionRevision` or bump `Conclusion.version` (scenario 12).
- **After creation the source can change.** A consultant may later **reopen** the source Conclusion (P2-4). The Finding stays; nothing deletes or detaches it. The Findings page flags it (D-P3-1-M: "Source conclusion is no longer approved …"). Keeping Finding and Conclusion consistent after a reopen is a P3-3/P3-4 reporting concern (open question 4).

### D-P3-1-C. A Finding is created together with its first Action, with status `open`, and its provenance is recorded as one `audit_events` row

- **Atomic pair:** `create_finding` inserts the `Finding` **and** its first `Action` (from the `action_*` request fields) in one transaction. That satisfies the plan's "Each Finding gets one or more Actions" as an invariant for consultant-created Findings. Migrated Findings already have exactly one Action. Actions are never deleted, so the invariant holds forever.
- **Finding fields:**
  - `title` = the submitted title (prefilled with `card.requirement_title`);
  - `description` = submitted (prefilled with `conclusion.gaps_identified`);
  - `severity` ∈ `RISK_LEVELS` (prefilled with `conclusion.risk_level` if it is in `RISK_LEVELS`, else `"medium"`);
  - `priority` ∈ `PRIORITIES = (1, 2, 3, 4)` (prefilled with `PRIORITY_BY_SEVERITY[severity prefill]`, where `PRIORITY_BY_SEVERITY = {"critical": 1, "high": 1, "medium": 2, "low": 3}`; the prefill is a suggestion only);
  - `status = "open"`;
  - `assessment_id` and `conclusion_id` from the Conclusion.
- **`Finding.status` is not changed by this task.** No route changes it; it is always `"open"` for consultant-created Findings. Its lifecycle (`in_progress`/`resolved`/`accepted_risk`) is tied to Action closure and verification, which is **P3-4**. Migrated Findings keep whatever status the migration gave them.
- **Provenance (PR-050: "Conclusion revision").** `Finding` has no column for the Conclusion revision or version, and adding one is a schema change (D-P3-1-A, point 2). So the binding is recorded in the one generic table D2 provides. `create_finding` adds exactly one `AuditEvent`:
  - `actor` = the actor;
  - `action = "finding_created"`;
  - `entity_type = "finding"`;
  - `entity_id = finding.id`;
  - `metadata_json = json.dumps({...}, sort_keys=True)`, with **exactly** these keys: `assessment_id`, `conclusion_id`, `conclusion_version` (the Conclusion's `version` at creation), `conclusion_revision_id` (the id of the latest `HUMAN_DECISION_ACTIONS` revision of that Conclusion, ordered `created_at, rowid`; D-P3-1-B guarantees it is an `approved` or `edited` revision), `framework_id`, `requirement_id`, `first_action_id`.

  P3-2/P3-3 can then bind a Finding to the exact approved revision. This is the only `audit_events` write in this task. **Action changes are not audited there**, because `history_json` is their trail (D2).
- **Origin.** A Finding is `origin = "consultant"` iff a `finding_created` audit event exists for it, else `"migrated"`. `migrate_legacy.py` is the only other writer, and it writes no audit event.

### D-P3-1-D. `history_json`: exact entry schema and vocabulary

`history_json` is `json.dumps(list_of_entries)`: a JSON **array**, oldest first. It is only ever **appended to**, through the compare-and-swap in D-P3-1-F. No code path rewrites, reorders or removes an entry. Every entry this task writes is an object with **exactly** these five keys (`HISTORY_KEYS`):

```jsonc
{
  "actor": "consultant:Priya",                  // conclusion_review.reviewer_actor(reviewer_name)
  "action": "created" | "status_changed" | "updated",   // HISTORY_ACTIONS
  "timestamp": "2026-09-23T10:15:02.123456+00:00",       // datetime.now(timezone.utc).isoformat() (or the injected `now`)
  "notes": "Client confirmed owner on call" | null,      // stripped; blank -> null; <= 2000 chars
  "changes": { "<field>": {"from": <old>, "to": <new>} } // see below
}
```

The plan's four keys (`actor`, `action`, `timestamp`, `notes`) come first, with the plan's meanings. **`changes` is the one addition.** Without it, "status changed" would not say from what to what. Encoding that in `notes` would put a machine fact in a free-text field the consultant also writes. It is always present on the entries this task writes; `{}` never occurs (see below).

**`changes` per action (exact):**

| `action` | Written by | `changes` keys | Values |
|---|---|---|---|
| `created` | `create_finding` (first Action), `add_action` | exactly `title`, `owner`, `target_date`, `status` | every `from` is `null`; `to` is the stored title, owner (or `null`), target date as `"YYYY-MM-DD"` (or `null`), and `"open"` |
| `status_changed` | `change_action_status` | exactly `status` | `{"from": <old status>, "to": <new status>}` |
| `updated` | `update_action` | only the fields in `TRACKED_FIELDS = ("title", "owner", "target_date")` whose value changed (≥ 1, since a no-op is refused) | old/new, with owner `null` when unset and target date as `"YYYY-MM-DD"` or `null` |

**One request appends exactly one entry.** Status changes and detail edits are separate routes, so an entry is never both.

**Vocabulary, and how it relates to the legacy migration:**
- `HISTORY_ACTIONS = ("created", "status_changed", "updated")` are the only values this task **writes**.
- `LEGACY_HISTORY_ACTION = "imported"` is written only by `scripts/migrate_legacy.py`. Its entries have exactly the four plan keys, **no `changes`**, and the notes `"Migrated from legacy GapItem remediation fields"`. **Legacy rows are left exactly as they are.** No reconciliation or backfill, and no `changes` key is added to them. Every reader uses `entry.get("changes") or {}`. A migrated Action's next change appends a normal five-key entry after the `imported` one, so its history is mixed-shape by design, and each entry is self-describing.
- **Reserved for P3-4, never written here:** `closed`, `verified`, `reopened`. P3-4 will add its own keys (for example the closure evidence version id) under `changes` or beside it; that is P3-4's decision.
- Display labels, `HISTORY_LABELS`: `created` "Action created", `status_changed` "Status changed", `updated` "Details updated", `imported` "Imported from legacy remediation". Any other value is shown verbatim.
- Actor display: a leading `consultant:` is stripped (the P2-4/P2-6 rule, so the raw prefix is never rendered). `system:migration` is shown verbatim.

**Why `status_changed` and not per-status verbs:** the transition is in `changes.status`, so one verb covers every transition, including P3-4's later ones if it chooses. Per-verb names (`started`, `paused`, …) would multiply values without adding facts.

### D-P3-1-E. Action status state machine: `open ⇄ in_progress` only. Closure is reserved for P3-4.

`ACTION_STATUSES = ("open", "in_progress", "closed", "verified")`. Its set equals `migrate_legacy.ACTION_STATUSES` (asserted). New Actions start `open`.

| Current status | Allowed targets in P3-1 | Everything else |
|---|---|---|
| `open` | `in_progress` | `closed`/`verified` → 400 `CLOSURE_RESERVED`; `open` → 400 `INVALID_TRANSITION` |
| `in_progress` | `open` | `closed`/`verified` → 400 `CLOSURE_RESERVED`; `in_progress` → 400 `INVALID_TRANSITION` |
| `closed`, `verified` (only migrated rows today) | none | any target → 400 `TERMINAL` |
| anything else (defensive) | none | 400 `INVALID_TRANSITION` |

`ACTION_TRANSITIONS = {"open": ("in_progress",), "in_progress": ("open",), "closed": (), "verified": ()}` and `CLOSURE_STATUSES = ("closed", "verified")`.

- **Why no close in P3-1:** PR-051 says "Closed requires closure Evidence plus consultant verification", and the plan gives closure verification to P3-4 ("consultant marks action as closed, attaches closure evidence, records in history_json"). A P3-1 close without evidence would create exactly the unverified closures PR-051 forbids, and P3-4 would inherit them.
- **Why no reopen in P3-1:** P2-4's reopen exists because approval **locks**. Here, `open ⇄ in_progress` is freely reversible, so no reopen is needed. Reopening a **closed** Action undoes a verification and belongs with the verification design (P3-4). Migrated `closed` Actions are therefore read-only in status and details here. The page says so (D-P3-1-M).
- **Details (`title`, `owner`, `target_date`) are editable only while the status is `open` or `in_progress`.** Otherwise the edit is refused with 400 `TERMINAL`.
- The plan's test ("update action status, verify history_json contains both entries") is `open → in_progress`: `[created, status_changed]`.

### D-P3-1-F. Concurrency: compare-and-swap on the history for every append, and a version check on the source Conclusion

`Action` has no version column, and adding one is a schema change. Without a guard, an append is read-modify-write, and two concurrent appends would lose one entry. **That silently breaks PR-051's "update history is append-only".** So:

- **Every mutating Action request** (status and details) carries **`expected_history_length`** (int, required; missing or non-int gives 422). It's the number of history entries the page was rendered with, emitted as `<input type="hidden" name="expected_history_length" value="{{ row.history_length }}">`. `add_action` creates a new row and needs no token.
- **Append protocol (exact, in `_append`):**
  1. `raw = action.history_json`;
  2. `history = load_history(raw)`, called **through the module global** (the test seam; D-P3-1-I);
  3. if `len(history) != expected_history_length`, raise `FindingConflict(STALE_ACTION)` (409);
  4. validate, and build the new entry;
  5. `result = db.execute(update(Action).where(Action.id == action.id, Action.history_json == raw).values(history_json=json.dumps(history + [entry]), **field_values).execution_options(synchronize_session=False))`;
  6. if `result.rowcount != 1`, raise `FindingConflict(STALE_ACTION)`; otherwise `db.expire(action)`.

  The `WHERE history_json = :raw` is the same compare-and-swap idea as P2-3/P2-4's `swap_conclusion`, keyed on the content being appended to. Column `onupdate` refreshes `updated_at` on a Core `update()`.
- **Finding creation** carries **`conclusion_version`** (int, required). If `conclusion.version != conclusion_version`, raise `FindingConflict(STALE_CONCLUSION)` (409). This binds the Finding to the Conclusion version the consultant looked at: if the Conclusion was reopened or re-decided since the page loaded, nothing is created.
- **Residual, accepted and named:** two simultaneous create requests for the same Conclusion can both pass the "no Finding exists" check (there is no unique index; adding one is a schema change). For a single-user local app that window is one request. A later task can add a unique index on `findings.conclusion_id` (open question 3).
- **409 response:** JSON `{"detail": message}`, status 409, with `X-Toast-Message` = the URL-encoded message and `X-Toast-Type: error`. The existing `htmx:responseError` listener shows it, and the page is not swapped. **No change to `app/static/js/app.js`.** Unlike P2-4 there is no diff to show: the consultant reloads, and nothing was saved.

### D-P3-1-G. Field validation: owner, target date, titles, notes

All text is `.strip()`ped first. The router turns every `""` form value into `None` before schema validation (the `remediation.py` pattern). The **service** enforces value rules and raises `InvalidFindingRequest` (400), so direct callers get the same checks. The **schema** enforces only types and enums (422).

| Field | Rule | Message on violation (400) |
|---|---|---|
| Finding `title`, `description` | required, non-blank; title ≤ 255 | `"A finding needs a title and a description."` / `TITLE_TOO_LONG` |
| Finding `severity` | ∈ `RISK_LEVELS` (the schema `Literal` gives 422; the service re-checks) | `"Unknown severity."` |
| Finding `priority` | int in `PRIORITIES` (1–4) | `"Priority must be between 1 and 4."` |
| Action `title` (`action_title` on create) | required, non-blank, ≤ 255 | `"An action needs a title."` / `TITLE_TOO_LONG` |
| `owner` (`action_owner` on create) | **optional free text**, ≤ 255; blank or `None` → stored `NULL` ("Unassigned"). No user directory exists (no auth), so no lookup is done | `"Owner must be 255 characters or fewer."` |
| `target_date` (`action_target_date` on create) | **optional**. The schema type is `datetime.date \| None` (the `<input type="date">` value `YYYY-MM-DD`; an invalid date gives 422). Stored as `datetime(d.year, d.month, d.day, tzinfo=timezone.utc)`; `None` → `NULL`. **Past dates are allowed** (recording an already-overdue commitment is legitimate); overdue display is P3-4's dashboard | — |
| `notes` | optional, ≤ 2000; blank → `null` in the history entry | `"Notes must be 2000 characters or fewer."` |
| `status` | the schema `Literal[ACTION_STATUSES]` gives 422 for an unknown value; the service re-checks | `"Unknown action status."` |

`TITLE_TOO_LONG = "Titles must be 255 characters or fewer."` **No-op detection for `update_action`:** compare the stripped title, the normalized owner (`None` when blank) and the target **date** (`action.target_date.date()` when set; SQLite returns naive datetimes, so compare dates, never datetimes). All equal → 400 `NO_CHANGES = "No changes to save."`.

### D-P3-1-H. Routes and modules

**New API router `app/routers/findings.py`**: `router = APIRouter(prefix="/api/assessments", tags=["findings"])`, registered in `app/main.py` with `app.include_router(findings.router)` directly after `app.include_router(conclusions.router)` (and `findings` added to the `from app.routers import (…)` list). **Page route** in `web.py`.

| Method + path | Handler | Module | Success |
|---|---|---|---|
| `GET /assessments/{assessment_id}/findings` | `findings_page` | `web.py`, directly after `workpaper_page` | 200, `pages/findings.html` |
| `POST /api/assessments/{assessment_id}/findings` | `create_finding_route` | `findings.py` | 200 JSON `{"finding_id": id}` with header `HX-Redirect: /assessments/{assessment_id}/findings#finding-{finding_id}` |
| `POST /api/assessments/{assessment_id}/findings/{finding_id}/actions` | `add_action_route` | `findings.py` | 200, re-rendered `components/finding_card.html`, toast `Action added` |
| `POST /api/assessments/{assessment_id}/findings/{finding_id}/actions/{action_id}/status` | `change_action_status_route` | `findings.py` | 200, re-rendered card, toast `Action status updated` |
| `POST /api/assessments/{assessment_id}/findings/{finding_id}/actions/{action_id}/update` | `update_action_route` | `findings.py` | 200, re-rendered card, toast `Action updated` |

These are the **only** routes this task adds. The success toasts use `X-Toast-Type: success`.

- **Why not `conclusions.py` or a `/conclusions/{id}/findings` path:** P2-4 scenario 12 pins the exact set of routes whose path contains `/conclusions`. None of the paths above contains `/conclusions` or `/workpaper`, and the Conclusion id travels in the **body**.
- **Why not `remediation.py`:** it is the legacy `GapItem` remediation surface. It stays unchanged until P3-4 retires it, and it's under the standing "legacy consumers" guard.
- **Error mapping (every handler; every error path calls `db.rollback()` first):**
  - `FindingNotFound` → `HTTPException(404, exc.message)`;
  - `InvalidFindingRequest` → `JSONResponse({"detail": exc.message}, status_code=400)` + encoded toast (`urllib.parse.quote`) + `X-Toast-Type: error`;
  - `FindingConflict` → the same shape with status **409**;
  - a schema `ValidationError` → 422.
- The router commits once on success, then renders. For the card re-render it calls `finding_service.finding_view(...)` after the commit. Module-local `_templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")` then `configure_templates(_templates)`, exactly as `conclusions.py` does. Keep local `_payload`/`_validated`/`_toast` helpers, and **do not import from `conclusions.py`, `review.py` or `remediation.py`** (the P2-4 precedent).
- **Actor:** `conclusion_review.reviewer_actor(body.reviewer_name)` for every mutating route.
- **Pydantic schemas: new `app/schemas/findings.py`.**
  - `FindingCreateIn`: `conclusion_id: str | None = None`, `conclusion_version: int`, `title: str | None = None`, `description: str | None = None`, `severity: Literal["critical", "high", "medium", "low"]`, `priority: int`, `action_title: str | None = None`, `action_owner: str | None = None`, `action_target_date: date | None = None`, `notes: str | None = None`, `reviewer_name: str | None = None`.
  - `ActionCreateIn`: `title: str | None = None`, `owner: str | None = None`, `target_date: date | None = None`, `notes: str | None = None`, `reviewer_name: str | None = None`.
  - `ActionStatusIn`: `status: Literal["open", "in_progress", "closed", "verified"]`, `expected_history_length: int`, `notes: str | None = None`, `reviewer_name: str | None = None`.
  - `ActionUpdateIn`: `title: str | None = None`, `owner: str | None = None`, `target_date: date | None = None`, `expected_history_length: int`, `notes: str | None = None`, `reviewer_name: str | None = None`.
  
  A `conclusion_id` of `None` after blank-stripping is refused by the service as `FindingNotFound("Conclusion not found")` (404).

### D-P3-1-I. `app/services/findings.py`: the service API, exact

A new module. **It never commits.** It contains no `delete` (any case, comments and docstrings included), no `swap_conclusion`, and no `ConclusionRevision(` constructor call. It writes no `Conclusion` or `ConclusionRevision`. It never logs titles, descriptions, owners or notes (ids, statuses and counts only).

```python
from app.services import conclusion_review             # module import: patch seam, single decision state
from app.services.analysis_pipeline import HUMAN_DECISION_ACTIONS
from app.services.conclusion_review import GAP_OUTCOMES, REVIEWER_ACTOR_PREFIX, RISK_LEVELS, ConclusionCard
from app.services.workpaper import anchor_for

FINDING_STATUSES = ("open", "in_progress", "resolved", "accepted_risk")   # set == migrate_legacy.FINDING_STATUSES
NEW_FINDING_STATUS = "open"
ACTION_STATUSES = ("open", "in_progress", "closed", "verified")           # set == migrate_legacy.ACTION_STATUSES
NEW_ACTION_STATUS = "open"
ACTION_TRANSITIONS = {"open": ("in_progress",), "in_progress": ("open",), "closed": (), "verified": ()}
CLOSURE_STATUSES = ("closed", "verified")
ELIGIBLE_STATES = ("approved", "edited")
PRIORITIES = (1, 2, 3, 4)
PRIORITY_BY_SEVERITY = {"critical": 1, "high": 1, "medium": 2, "low": 3}
HISTORY_KEYS = ("actor", "action", "timestamp", "notes", "changes")
HISTORY_ACTIONS = ("created", "status_changed", "updated")
LEGACY_HISTORY_ACTION = "imported"
TRACKED_FIELDS = ("title", "owner", "target_date")
HISTORY_LABELS = {"created": "Action created", "status_changed": "Status changed",
                  "updated": "Details updated", "imported": "Imported from legacy remediation"}
MAX_TITLE = 255
MAX_OWNER = 255
MAX_NOTES = 2000
FINDING_CREATED_EVENT = "finding_created"
FINDING_ENTITY = "finding"

# Messages (exact; tests compare them)
STALE_CONCLUSION = "This conclusion changed since you loaded the page. Reload before creating a finding. Nothing was saved."
NOT_APPROVED = "Only an individually approved or edited conclusion can become a finding."
LEGACY_BULK = "This conclusion has a legacy bulk approval. Reopen and approve it individually before creating a finding."
NO_GAP = "Only a conclusion with a gap (partially compliant, non-compliant or insufficient evidence) can become a finding."
DUPLICATE = "A finding already exists for this conclusion."
STALE_ACTION = "This action changed since you loaded the page. Reload and try again. Nothing was saved."
CLOSURE_RESERVED = "Closing or verifying an action requires closure evidence and is not available yet."
TERMINAL = "This action is closed and cannot be changed here."
UNREADABLE_HISTORY = "This action's history could not be read. Nothing was saved."
NO_CHANGES = "No changes to save."
TITLE_TOO_LONG = "Titles must be 255 characters or fewer."
# INVALID_TRANSITION is formatted: f"An action cannot move from {current} to {target}."

class FindingError(Exception):
    status_code = 400
    def __init__(self, message: str): self.message = message; super().__init__(message)
class FindingNotFound(FindingError): status_code = 404       # "Conclusion not found" | "Finding not found" | "Action not found"
class InvalidFindingRequest(FindingError): status_code = 400
class FindingConflict(FindingError): status_code = 409

def load_history(raw: str) -> list[dict]:
    """json.loads(raw); must be a list whose items are all dicts, else raise InvalidFindingRequest(UNREADABLE_HISTORY)."""

def create_finding(db, *, assessment_id: str, conclusion_id: str | None, conclusion_version: int,
                   title: str | None, description: str | None, severity: str, priority: int,
                   action_title: str | None, action_owner: str | None, action_target_date: date | None,
                   notes: str | None, actor: str, now: datetime | None = None) -> Finding: ...
def add_action(db, *, assessment_id: str, finding_id: str, title: str | None, owner: str | None,
               target_date: date | None, notes: str | None, actor: str, now: datetime | None = None) -> Action: ...
def change_action_status(db, *, assessment_id: str, finding_id: str, action_id: str, status: str,
                         expected_history_length: int, notes: str | None, actor: str,
                         now: datetime | None = None) -> Action: ...
def update_action(db, *, assessment_id: str, finding_id: str, action_id: str, title: str | None,
                  owner: str | None, target_date: date | None, expected_history_length: int,
                  notes: str | None, actor: str, now: datetime | None = None) -> Action: ...

@dataclass(frozen=True)
class HistoryEntryView:
    sequence: int              # 1-based, oldest first
    action: str                # raw value
    label: str                 # HISTORY_LABELS.get(action, action)
    actor_display: str         # consultant: prefix stripped
    timestamp: str             # as stored
    notes: str | None
    changes: dict              # entry.get("changes") or {}

@dataclass(frozen=True)
class ActionView:
    action: Action
    history: list[HistoryEntryView]
    history_readable: bool             # False if load_history raised; history == [] then
    history_length: int                # len(history) (the expected_history_length to render)
    allowed_statuses: tuple[str, ...]  # ACTION_TRANSITIONS.get(status, ()) (empty when not history_readable)
    editable: bool                     # status in ("open", "in_progress") and history_readable

@dataclass(frozen=True)
class FindingView:
    finding: Finding
    card: ConclusionCard | None        # the source Conclusion's card; None only if it is missing
    origin: str                        # "consultant" | "migrated" (D-P3-1-C)
    created_by: str | None             # actor display of the finding_created event, else None
    source_approved: bool              # card is not None and card.state in ELIGIBLE_STATES
    workpaper_href: str | None         # f"/assessments/{assessment_id}/workpaper#{anchor_for(fw, req)}" when card
    actions: list[ActionView]          # ordered created_at, rowid

@dataclass(frozen=True)
class EligibleConclusion:
    card: ConclusionCard
    workpaper_href: str
    prefill: dict                      # exactly: title, description, severity, priority, action_title

@dataclass(frozen=True)
class FindingsPage:
    eligible: list[EligibleConclusion]   # conclusion_cards order
    findings: list[FindingView]          # Finding.created_at, rowid order

def findings_page(db, assessment_id: str) -> FindingsPage: ...
def finding_view(db, *, assessment_id: str, finding_id: str) -> FindingView: ...   # via findings_page; FindingNotFound if absent
```

**Check order (exact):**

- **`create_finding`:**
  1. `conclusion = db.get(Conclusion, conclusion_id)` when `conclusion_id` is truthy. Missing, or `assessment_id` mismatch, raises `FindingNotFound("Conclusion not found")`.
  2. `conclusion.version != conclusion_version` → `FindingConflict(STALE_CONCLUSION)`.
  3. `card = conclusion_review.conclusion_card(...)` (map `ConclusionNotFound` to `FindingNotFound("Conclusion not found")`).
  4. `card.state not in ELIGIBLE_STATES` → `NOT_APPROVED`.
  5. `card.legacy_bulk_approval` → `LEGACY_BULK`.
  6. `conclusion.outcome not in GAP_OUTCOMES` → `NO_GAP`.
  7. `select(Finding.id).where(Finding.conclusion_id == conclusion.id).limit(1)` finds one → `DUPLICATE`.
  8. Field validation (D-P3-1-G): Finding fields first, then Action fields, then notes.
  9. Add the `Finding` and flush. Add the `Action` with `status="open"` and `history_json=json.dumps([created_entry])`, then flush.
  10. Look up the latest human-decision revision (`select(ConclusionRevision).where(conclusion_id == …, action.in_(HUMAN_DECISION_ACTIONS)).order_by(created_at.desc(), literal_column("conclusion_revisions.rowid").desc()).limit(1)`). Add the `AuditEvent` (D-P3-1-C), flush, and return the Finding.
- **`add_action`:**
  1. `finding = db.get(Finding, finding_id)`. Missing, or `finding.assessment_id != assessment_id`, raises `FindingNotFound("Finding not found")`.
  2. Validate.
  3. Insert the Action with its `created` entry, flush, and return it.
  
  Allowed on any Finding, including migrated ones, whatever the Finding's status.
- **`change_action_status`:**
  1. Load the Finding, then the Action. `action.finding_id != finding.id` → `FindingNotFound("Action not found")`.
  2. `load_history` + the staleness check (D-P3-1-F steps 1–3).
  3. Current status in `CLOSURE_STATUSES` → `TERMINAL`.
  4. `status not in ACTION_STATUSES` → `"Unknown action status."`.
  5. Target in `CLOSURE_STATUSES` → `CLOSURE_RESERVED`.
  6. Target not in `ACTION_TRANSITIONS.get(current, ())` → `INVALID_TRANSITION`.
  7. Validate notes.
  8. CAS-append a `status_changed` entry with `field_values={"status": status}`.
- **`update_action`:**
  1. The same loading and staleness steps.
  2. Status not in `("open", "in_progress")` → `TERMINAL`.
  3. Validate the fields.
  4. No-op → `NO_CHANGES`.
  5. CAS-append an `updated` entry with `field_values` = the changed tracked fields (target date stored as a UTC-midnight datetime or `None`).

**Staleness is checked before the transition and field rules**, the P2-4 order, so a consultant looking at a stale row is always told to reload rather than given a rule error about a state they can't see.

**`findings_page` (read-only; these four statements, the first of which is `conclusion_cards` with its own internal queries):**
1. `conclusion_review.conclusion_cards(db, assessment_id)`, called **once** through the module attribute.
2. The assessment's Findings, ordered `Finding.created_at, literal_column("findings.rowid")`.
3. Their Actions (`finding_id IN …`), ordered `Action.created_at, literal_column("actions.rowid")`.
4. The `AuditEvent`s with `entity_type == "finding"`, `action == "finding_created"` and `entity_id IN …`.

`eligible` = the cards that pass D-P3-1-B rules 1–4 (rule 4 uses the Finding set from statement 2). The prefill is as in D-P3-1-C, with `title` = `card.requirement_title[:255]` and `action_title` = `conclusion.recommended_action.strip()[:255]`. A malformed `history_json` gives `history_readable=False` and never raises on the page.

### D-P3-1-J. Legacy-migrated Findings: coexistence, collision, and one change to `scripts/migrate_legacy.py`

1. **Collision rule:** at most one Finding per Conclusion, whatever its origin (D-P3-1-A). `create_finding` refuses with `DUPLICATE` when **any** Finding, migrated or consultant-created, already references the Conclusion. The consultant then works on the existing Finding, which the page lists. In practice a migrated Conclusion first fails `LEGACY_BULK` or `NOT_APPROVED`, because P2-4's `EVIDENCE_NOT_CAPTURED` guard blocks individual approval until a re-run (Current state). The `DUPLICATE` path is what protects a migrated Conclusion that was re-analysed and then individually approved.
2. **Migrated Findings are first-class on the page.** They are listed with `data-finding-origin="migrated"` and the badge "Migrated from legacy remediation". A consultant can add Actions to them, and can move their `open`/`in_progress` Actions and edit those Actions' details. Their `imported` history entry is shown with its label. Their `Finding.status` values, whatever the migration wrote, are displayed and never changed (D-P3-1-C). Their `closed` Actions are terminal here (D-P3-1-E).
3. **No reconciliation of legacy rows.** Their `history_json` (the four-key `imported` entry), `Finding.status`, `severity` and `priority` stay byte-for-byte as migrated (D-P3-1-D).
4. **`scripts/migrate_legacy.py`: one change, so that re-running the migration never touches a Finding that exists.** In `run_migration`, directly after the existing `finding = session.execute(select(Finding).where(…)).scalar_one_or_none()`, replace the `if finding is None: …create…` / Action-lookup / `if action is None: …create…` sequence with:
   - `if finding is not None: continue`, with the comment `# P3-1: an existing Finding and its Actions are consultant-operated; never re-map them.`;
   - otherwise, the **unchanged** Finding-creation block, followed by the **unchanged** Action-creation block, now unconditional. Remove the `select(Action)` lookup.

   **Why this is safe for idempotency:** `run_migration` creates the Finding and its Action in the same pass and commits once (it rolls back on any exception), so "Finding exists without its Action" cannot result from the migration itself. `test_second_run_creates_zero_new_rows` and the rest of `tests/test_migrate_legacy.py` must pass **unmodified**. **Why it is needed:** without it, a consultant's second Action on a migrated Finding makes the next migration run crash with `MultipleResultsFound`. With zero Actions, which is impossible today, it would even add an `imported` Action to a consultant's Finding. Add one sentence about this to the module docstring's D-D paragraph. No other change to the script.

### D-P3-1-K. Workpaper linkage, both directions (closes the P2-6 hand-forward)

- **Finding → workpaper (P7).** Every `FindingView` and `EligibleConclusion` has a `workpaper_href` (D-P3-1-I) built with `workpaper.anchor_for`. The Findings page renders it as "Workpaper trace →" on every Finding card and every eligible row. Findings page → that entry, with the full revision history expanded, is **1 click**. From the assessment page it's findings page (1) → workpaper entry (2) → citation's `/evidence/{id}` (3), which meets P7 and PR-055 for first-class Findings.
- **Workpaper → Finding.** In `app/services/workpaper.py`:
  - change `from dataclasses import dataclass` to `from dataclasses import dataclass, field`, and add `from app.models.finding import Finding` (no other new import; `anchor_for` is already defined in this module);
  - add **one last field** to `WorkpaperEntry`: `findings: list[dict] = field(default_factory=list)`, so every existing constructor call and test stays valid;
  - add **one** statement to `build_workpaper`: `select(Finding).where(Finding.assessment_id == assessment.id).order_by(Finding.created_at, literal_column("findings.rowid"))`, grouped by `conclusion_id`;
  - set each entry's `findings` to dicts with **exactly** the keys `finding_id`, `title`, `status`, `severity`, `href` (`f"/assessments/{assessment.id}/findings#finding-{finding.id}"`).
  
  **Do not** add a key to `counts`: P2-6 scenario 11 asserts that dict exactly. Keep every P2-6 structural guard true: none of the forbidden substrings, and the word "delete" nowhere in the file.
- In `components/workpaper_entry.html`, inside the header link row (the `<div class="mt-3 flex flex-wrap items-center gap-3 text-xs">` holding "Decide on the conclusions page →"), after that link add:
  ```html
  {% for finding in entry.findings %}<a data-workpaper-finding href="{{ finding.href }}" class="font-medium text-brand dark:text-navy-300 hover:underline">Finding: {{ finding.title }} →</a>{% endfor %}
  ```
  It's a plain link, with no form or button (the P2-6 read-only regex). The attribute is `data-workpaper-finding`, which does **not** contain the substring `data-workpaper-entry` that P2-6 counts and slices on.
- **Header links (additive only):**
  - `pages/workpaper.html`: in the header link group beside "Report →", add `<a href="/assessments/{{ assessment.id }}/findings" class="text-sm font-medium text-brand dark:text-navy-300 hover:underline">Findings and actions →</a>`;
  - `pages/conclusions.html`: directly after its "Workpaper (read-only trace) →" link, add the same link.
  
  Nothing else changes in either file. `components/conclusion_card.html` and `app/services/conclusion_review.py` are **not modified**: the card does not show Finding state. That keeps P2-4's render paths and guards untouched, and the workpaper is the place where a Conclusion's full context, now including its Finding, is shown.

### D-P3-1-L. Read paths: one per-assessment Findings page. Everything else is deferred, explicitly.

- **Added:** `GET /assessments/{assessment_id}/findings` (D-P3-1-H/M), plus the workpaper link (D-P3-1-K).
- **Deferred:**
  - the **engagement-level rollup / dashboard** of open and closed Actions (plan P3-4: "Dashboard: engagement-level rollup");
  - Findings in the **PDF/report** (P3-3: "Citations in finding details");
  - replacing the Report tab's `GapItem` "Critical Findings" and the legacy remediation panel (P3-4 / the reader migration).
  
  The portfolio dashboard reads no remediation data today (Current state), so nothing regresses. None of this is in the plan's P3-1 test criterion.
- **Where the page is linked from:** `pages/conclusions.html` and `pages/workpaper.html` (D-P3-1-K). No change to the assessment page, the report tab or the dashboard.

### D-P3-1-M. Templates: what they render

**`pages/findings.html`** extends `base.html`:
- `{% block title %}Findings — {{ assessment.company_name }}{% endblock %}`;
- the breadcrumb `Assessments / {{ assessment.company_name }} / Findings` in the `pages/conclusions.html` style;
- `<h1>` "Findings and actions", and the subtitle "Create a finding from an individually approved conclusion, then track its remediation actions. Every change is appended to the action's history.";
- links "Conclusions (decide) →" and "Workpaper (read-only trace) →";
- the page-level `<input id="reviewer-name" name="reviewer_name" value="{{ reviewer_name }}" placeholder="Your name">`. The `reviewer_name` context value comes from a private helper `_latest_reviewer_name(db, assessment_id) -> str` in `web.py`: **extract** the query that `conclusions_page` already runs inline into this helper (behaviour-preserving), and call it from both pages;
- `<h2>` "Approved conclusions without a finding", then one `<div data-eligible-conclusion id="eligible-{{ row.card.conclusion.id }}">` per `page.eligible` entry. It shows the framework (upper), `requirement_id` (mono), `requirement_title`, the outcome and risk, and "Workpaper trace →" (`row.workpaper_href`), followed by a `<details>` with summary "Create finding" containing one `<form hx-post="/api/assessments/{{ assessment.id }}/findings" hx-swap="none" hx-include="#reviewer-name">`. The form has:
  - hidden `conclusion_id` and `conclusion_version` (`row.card.conclusion.version`);
  - `title` (input), `description` (textarea), `severity` (`<select>` of the four risk levels) and `priority` (`<select>` 1–4), all prefilled;
  - `action_title` (prefilled), `action_owner`, `action_target_date` (`type="date"`) and `notes` (textarea);
  - submit "Create finding".
  
  Empty state: "No approved conclusions are waiting for a finding.";
- `<h2>` "Findings", then `{% include "components/finding_card.html" %}` per `page.findings` entry (context variable `view`). Empty state: "No findings yet."

**`components/finding_card.html`**, context `view` and `assessment`. Root, **with attributes in exactly this order**:
```html
<article data-finding-card id="finding-{{ view.finding.id }}" data-finding-origin="{{ view.origin }}" data-source-approved="{{ 'true' if view.source_approved else 'false' }}" class="…">
```
It renders, in order:
1. **Header:**
   - `finding.title`, `severity`, "Priority {{ finding.priority }}" and "Status: {{ finding.status }}";
   - the source: framework (upper), `requirement_id`, `requirement_title` and `outcome` from `view.card`, plus "Workpaper trace →" (`view.workpaper_href`);
   - origin: "Migrated from legacy remediation" when `view.origin == "migrated"`, else "Created by {{ view.created_by }}";
   - when `view.card and view.card.legacy_bulk_approval`: the literal text "Legacy bulk approval, not individually reviewed" (the same wording as `workpaper.LEGACY_BULK_LABEL`, written into the template);
   - when `not view.source_approved`: "Source conclusion is no longer approved (now {{ view.card.state if view.card else 'missing' }}). Review it before relying on this finding.";
   - `finding.description`.
2. **Actions:** one `<div data-action-row id="action-{{ row.action.id }}" data-action-status="{{ row.action.status }}">` per `view.actions` entry. Each shows:
   - `title`;
   - "Owner: {{ owner }}" or "Unassigned";
   - "Target: {{ target_date.strftime('%Y-%m-%d') }}" or "No target date";
   - "Status: {{ status }}".
   
   Then:
   - **History**, always expanded (no `<details>`): `<ol data-action-history>` with one `<li data-history-action="{{ e.action }}">` per `HistoryEntryView`, oldest first, showing `#{{ sequence }}`, `timestamp`, `label`, `actor_display`, each `changes` field as `{{ name }}: {{ change['from'] or '—' }} → {{ change['to'] or '—' }}` (iterate `e.changes.items()` as `name, change`; use subscript access, because `from` is a Jinja keyword), and `notes`. When `not row.history_readable`: "History could not be read.".
   - When `row.allowed_statuses`: a `<form hx-post="/api/assessments/{{ assessment.id }}/findings/{{ view.finding.id }}/actions/{{ row.action.id }}/status" hx-target="#finding-{{ view.finding.id }}" hx-swap="outerHTML" hx-include="#reviewer-name">` with hidden `expected_history_length` (`row.history_length`), `<select name="status">` of exactly `row.allowed_statuses`, `notes`, and submit "Update status".
   - When `row.editable`: a `<details>` "Edit details" with the same `hx-*` pattern posting to `…/update`, with fields `title`, `owner`, `target_date` (`type="date"`, value `YYYY-MM-DD` or empty), `notes`, hidden `expected_history_length`, and submit "Save details".
   - When not editable: "Closed and verified actions cannot be changed here."
3. **Add action:** a `<details>` "Add action" with a form posting to `…/findings/{{ view.finding.id }}/actions` (the same `hx-target`/`hx-swap`/`hx-include`), with fields `title`, `owner`, `target_date`, `notes`, and submit "Add action".

Tailwind with `dark:` variants, styled like `components/conclusion_card.html`. Everything is autoescaped: **never `|safe`** (titles, descriptions, owners and notes are consultant or client text).

### D-P3-1-N. Consistency audit of this spec (the P2-4 lesson, done in advance)

P2-4's handoff mandated a field name that its own grep forbade (`bulk`). Every mandated string in this document has been checked against every structural assertion in it and in the existing suite:

1. **The structural grep (scenario 11) is deliberately narrow:** `select all|create all|all conclusions|type="checkbox"|\bmultiple\b|\|\s*safe\b`, case-insensitive, over the three new Python files and the two new templates. It does **not** include the word `bulk`, because the mandated service message `LEGACY_BULK` and the mandated card text "Legacy bulk approval, not individually reviewed" both contain it and must be present. I checked every mandated message and label against the regex:
   - "Approved conclusions without a finding" and "No approved conclusions are waiting for a finding." contain "conclusions" but not "all conclusions";
   - no mandated text contains "select all", "create all" or "multiple";
   - `<select name="status">` / `<select name="severity">` do not match `select all`.
   
   **Don't write "multiple" or "select all" in comments or docstrings of those files.**
2. **`delete` guard** (scenario 11: service **and** router; the existing P2-6 guard: `workpaper.py`). No mandated message, label or identifier contains "delete". Messages say "Nothing was saved", not "discarded" or "deleted". Keep the word out of comments and docstrings in all three files.
3. **P2-6 workpaper guards:**
   - `workpaper.py` gains only a `select(...)`, a dataclass `field(default_factory=list)` and dict building, and none of `db.add(`, `db.add_all(`, `db.merge(`, `.commit(`, `.flush(`, `swap_conclusion`, `decide(`. The name `field` doesn't collide with any forbidden token.
   - The template addition is an `<a>`: no `<form`, `<button`, `hx-*`, `expected_version` or `|safe`.
   - `data-workpaper-finding` does not contain `data-workpaper-entry`, so P2-6's counts and `_entry_html` slicing are unaffected.
   - `counts` is unchanged (P2-6 scenario 11 compares it exactly).
4. **Route-set guards:** none of the five new paths contains `/conclusions` (P2-4 scenario 12) or `/workpaper` (P2-6 scenario 9). This task's own guard pins the set of paths containing `/findings` to exactly the five in D-P3-1-H. No pre-existing path contains `/findings`, which I checked across `app/routers/`.
5. **P2-4 bulk-action grep** over `pages/conclusions.html`: the added link text "Findings and actions →" matches none of `approve all|approve selected|select all|approve framework`.
6. **Escaping vs exact-text assertions:** the page texts asserted in HTML contain no `&`, `<`, `>` or quotes. `"Source conclusion is no longer approved (now pending)"` uses parentheses only. The 400/409 messages are asserted from the **JSON `detail`**, not HTML. Their toast header copy is URL-encoded with `urllib.parse.quote`, so tests decode it with `urllib.parse.unquote` before comparing. The arrows `→`/`—` appear only in HTML (UTF-8), never in a header.
7. **Counted attributes:** `data-finding-card` appears only on the card root, `data-action-row` only on action rows, and `data-history-action` only on history `<li>`s. `data-action-history` (the `<ol>`) does not contain `data-history-action`, and vice versa. `data-eligible-conclusion` appears only on eligible rows.
8. **Href substrings:** the fragment link `href="/assessments/{id}/findings#finding-{fid}"` and the page link `href="/assessments/{id}/findings"` (closing quote right after `findings`) don't contain each other, and the same holds for the workpaper hrefs (the P2-6 rule).
9. **White-label and blended-score guards:** no `CyberAssess` literal and no `overall_score` in any new template. The page title uses `assessment.company_name`.
10. **Actor prefix:** the raw `consultant:` prefix is never rendered. Scenario 7 asserts `"consultant:Priya" not in page.text`, and no mandated copy contains "consultant:" followed by a name.

## Required approach

### 1. `app/schemas/findings.py` (new): D-P3-1-H

### 2. `app/services/findings.py` (new): D-P3-1-B … G, I

Module docstring (it passes every guard): `"""Findings and Actions (P3-1): one Finding per individually approved gap Conclusion, and append-only Action history in actions.history_json. Never commits."""`

### 3. `app/routers/findings.py` (new) and its registration in `app/main.py`: D-P3-1-H

### 4. `app/routers/web.py`

Add `findings_page` directly after `workpaper_page`:
- `db.get(Assessment, …)`, else 404 `"Assessment not found"`;
- `page = finding_service.findings_page(db, assessment_id)`;
- render `pages/findings.html` with context `request`, `assessment`, `page`, `reviewer_name`.

Import `from app.services import findings as finding_service`. The alias is required, because `web.py` already has a local variable `findings`. Extract `_latest_reviewer_name` (D-P3-1-M) and use it in `conclusions_page` too, with identical behaviour. `findings_page` never commits.

### 5. `app/services/workpaper.py`, `components/workpaper_entry.html`, `pages/workpaper.html`, `pages/conclusions.html`: D-P3-1-K exactly

### 6. `pages/findings.html` and `components/finding_card.html` (new): D-P3-1-M

### 7. `scripts/migrate_legacy.py`: D-P3-1-J point 4 exactly

### 8. `tests/test_findings.py` (new)

Copy (don't import) from `tests/test_workpaper.py`:
- the Alembic-built `db_path` / `engine` (`PRAGMA foreign_keys=ON`) / `db` fixtures;
- `http`, `gate`, `_seed`, `_item`, `_stub_single`, `_revisions`, `_url` and `_human_revision`;
- the module-scoped `_register_frameworks` fixture, `ALL_REQS`/`REQS`, `_add_evidence` and `_cite_revision`.

For the legacy scenario, also copy `_gap_item_kwargs` and `_seed_legacy_assessment` from `tests/test_migrate_legacy.py`, adapted to take the plain `db` session.

**Produce Conclusions and decisions through the real pipeline and the real P2-4 routes** (`gate.trigger_analysis` with `_stub_single`, then `POST /api/assessments/{id}/conclusions/{cid}/approve|edit|reopen` with `expected_version` read from the DB). An approvable Conclusion needs non-NULL citations on its proposal, which the real pipeline gives (`"[]"`), and complete gap content, which `_item`'s defaults give. Hand-built rows are allowed only for:
- the legacy-bulk shape (`_human_revision(…, "approved", actor="Manager Review")`);
- a hand-inserted Finding to simulate a migrated one;
- `history_json`/`status` corruption in scenarios 4 and 5.

Helpers:
- `_create(http, assessment, conclusion, **overrides)` posts the D-P3-1-H create form (conclusion id and version read from the DB; title "Finding title", description "Finding description", severity "high", priority 1, action_title "First action", reviewer_name "Priya"). Overrides replace keys; a value of `None` drops the key.
- `_history(db, action_id)` returns `json.loads` of the fresh row's `history_json` after `db.expire_all()`.

Every scenario is one or more test functions whose docstrings start with `Scenario N:`.

## Key files

| File | Why it matters |
|---|---|
| `app/services/findings.py` (new) | The whole contract: eligibility, history, state machine, CAS, page read model (D-P3-1-B … I). |
| `app/routers/findings.py` (new), `app/schemas/findings.py` (new), `app/main.py` | Four POST routes, validation and registration (D-P3-1-H). |
| `app/routers/web.py` | `findings_page`; the `_latest_reviewer_name` extraction. |
| `app/templates/pages/findings.html`, `app/templates/components/finding_card.html` (new) | UI (D-P3-1-M). |
| `app/services/workpaper.py`, `app/templates/components/workpaper_entry.html`, `app/templates/pages/workpaper.html`, `app/templates/pages/conclusions.html` | Workpaper linkage and header links, additive only (D-P3-1-K). |
| `scripts/migrate_legacy.py` | The existing-Finding skip (D-P3-1-J). |
| `app/services/conclusion_review.py`, `app/services/analysis_pipeline.py`, `app/routers/conclusions.py`, `components/conclusion_card.html` | Reused; **not modified**. |
| `app/routers/remediation.py`, `review.py`, `reports.py`, `analysis.py`, `app/services/scoring.py`, `app/utils/pdf_export.py`, `app/static/js/app.js`, `app/models/*`, `alembic/versions/*` | **Not modified.** No schema change. |
| `tests/test_findings.py` (new) | The contract. **No existing test file is modified.** |

## Non-goals

- **No schema change and no Alembic revision.** No join table (D-P3-1-A), no unique index (open question 3), no version, revision or `origin` column.
- **No close, verify or reopen of Actions, and no closure evidence** (P3-4). No `Finding.status` changes (P3-4).
- No Finding from compliant or not-applicable Conclusions (open question 2). No editing or dismissing of Findings, and no Finding deletion. No Action deletion, ever.
- No engagement rollup, dashboard, PDF or report change, and no change to the legacy `GapItem` remediation panel or `remediation.py` (D-P3-1-L).
- No change to `conclusion_review.py`, the conclusion card, P2-4's routes, the pipeline or `app.js`. No `relationship()`.
- No `audit_events` rows other than the one `finding_created` per Finding (D-P3-1-C).
- No reconciliation of migrated `history_json`, statuses or fields (D-P3-1-J).

## Test scenarios

All in `tests/test_findings.py`. "Nothing written" means that these are all unchanged against a pre-request snapshot:
- `COUNT(*)` of `findings`, `actions`, `audit_events` and `conclusion_revisions`;
- every Action's `(id, status, title, owner, target_date, history_json, updated_at)`;
- every Conclusion's `(id, version, updated_at)`.

1. **The plan's test: create a finding from a conclusion, add an action, update the action's status, and check the history.** Use `_seed(applicable=[REQS[0]])`, run the pipeline with `_item(REQS[0], "non_compliant")`, and `approve` as Priya. Then `_create(...)`:
   - The response is 200 with JSON `finding_id` and `HX-Redirect == f"/assessments/{a.id}/findings#finding-{fid}"`.
   - DB: one Finding (`status "open"`, the submitted fields, `conclusion_id`, `assessment_id`). One Action (`status "open"`, `owner`/`target_date` NULL). `_history` has one entry whose key set `== set(HISTORY_KEYS)`, with `action "created"`, `actor "consultant:Priya"`, `notes None`, and `changes == {"title": {"from": None, "to": "First action"}, "owner": {"from": None, "to": None}, "target_date": {"from": None, "to": None}, "status": {"from": None, "to": "open"}}`.
   - One `AuditEvent(action="finding_created", entity_type="finding", entity_id=fid)`. Its `json.loads(metadata_json)` key set is exactly the seven keys of D-P3-1-C, with `conclusion_version == 2` and `conclusion_revision_id` == the `approved` revision's id.
   - Then `POST …/actions/{aid}/status` with `status=in_progress, expected_history_length=1, notes="Kickoff"` returns 200. The body contains `id="finding-{fid}"` and `data-action-status="in_progress"`. `_history` is `[created, status_changed]`, and the second entry has `changes == {"status": {"from": "open", "to": "in_progress"}}` and `notes "Kickoff"`. `action.status == "in_progress"`.
   - Then `POST …/findings/{fid}/actions` (title "Second action", owner "Asha", target_date "2026-12-31") returns 200. There is a second Action with one `created` entry, `changes.owner.to == "Asha"` and `changes.target_date.to == "2026-12-31"`, and `target_date.date() == date(2026, 12, 31)`.
   - The `timestamp` of every entry parses with `datetime.fromisoformat` and is timezone-aware.
2. **Eligibility.** Each of these writes nothing, and the response `detail` equals the constant:
   - pending → 400 `NOT_APPROVED`;
   - rejected → 400 `NOT_APPROVED`;
   - approved then reopened (pending again) → 400 `NOT_APPROVED`;
   - an approved `compliant` Conclusion (`_item(REQS[1], "compliant", gap="", action="")`, approved) → 400 `NO_GAP`. Seed with `applicable=REQS[:2]`: `_seed`'s default scopes REQS[1] out, and the pipeline would force it to `not_applicable`;
   - legacy bulk (`_human_revision(…, "approved", actor="Manager Review")` on a gap Conclusion) → 400 `LEGACY_BULK`;
   - an unknown `conclusion_id` → 404; another assessment's Conclusion → 404; a blank `conclusion_id` → 404;
   - `conclusion_version` one less than current → 409 `STALE_CONCLUSION`, with a URL-encoded `X-Toast-Message` that decodes to it.
   
   Positive: an **edited** Conclusion (P2-4 `edit` route) → 200.
   
   `findings_page(...).eligible` contains exactly the approved or edited gap Conclusions without a Finding, and after creation that Conclusion is no longer in it.
3. **One Finding per Conclusion (D-P3-1-A/J).**
   - A second `_create` for the same Conclusion gives 400 `DUPLICATE` and writes nothing.
   - A hand-inserted `Finding` (simulating a migrated one; no audit event) on another approved Conclusion gives `_create` → 400 `DUPLICATE`, and on the page that Finding shows `data-finding-origin="migrated"`.
   - A JSON body with `conclusion_id` as a list gives 422.
4. **Action state machine (D-P3-1-E).**
   - Assert the constants exactly: `ACTION_TRANSITIONS`, `CLOSURE_STATUSES`, `set(ACTION_STATUSES) == set(migrate_legacy.ACTION_STATUSES)` and `set(FINDING_STATUSES) == set(migrate_legacy.FINDING_STATUSES)`.
   - Parametrize the current status {open, in_progress} against targets {open, in_progress, closed, verified} with the correct `expected_history_length`: `open→in_progress` and `in_progress→open` give 200 and append exactly one entry. Same-status gives 400 `f"An action cannot move from {s} to {s}."`. `closed`/`verified` give 400 `CLOSURE_RESERVED`. Every refusal writes nothing.
   - An Action whose `status` is set to `"closed"` directly gives, for every target, 400 `TERMINAL`, and `update` gives 400 `TERMINAL`. Its card shows "Closed and verified actions cannot be changed here." and no status form.
   - An unknown status `"banana"` gives 422.
5. **Append-only concurrency (D-P3-1-F).**
   - (a) A stale `expected_history_length` (0 when there is 1 entry) on `status` and on `update` gives 409 `STALE_ACTION` and writes nothing.
   - (b) CAS race: monkeypatch `app.services.findings.load_history` with a wrapper that calls the real function, then runs `db.execute(text("UPDATE actions SET history_json = :h WHERE id = :id"), {"h": <original raw with one extra fabricated entry appended>, "id": action.id})` and returns the original parsed list. `status` with the correct pre-race length gives 409. After the router's rollback, the row's `history_json` equals the original raw string.
   - (c) Across scenarios 1, 4 and 6: every successful mutation leaves `history[:-1]` equal, element for element, to the pre-request history. Nothing earlier is rewritten.
   - (d) An Action with `history_json = "not json"` gives `status` → 400 `UNREADABLE_HISTORY`, and the page renders 200 with "History could not be read.".
6. **Details update and validation (D-P3-1-G).**
   - `update` with owner "Asha" and target_date "2026-11-30" (title unchanged) appends one `updated` entry whose `changes` keys are exactly `{"owner", "target_date"}`, with the correct from/to values.
   - A second `update` with a blank owner gives `changes == {"owner": {"from": "Asha", "to": None}}`, and the owner is NULL.
   - An identical resubmit gives 400 `NO_CHANGES`.
   - Validation, each writing nothing:
     - a blank create `title` or `description` → 400;
     - a blank `action_title` → 400 "An action needs a title.";
     - a 256-character title → 400 `TITLE_TOO_LONG`;
     - an owner over 255 characters → 400;
     - notes of 2001 characters → 400;
     - `priority=5` → 400 "Priority must be between 1 and 4.";
     - `severity="severe"` → 422;
     - `target_date="2026-13-40"` → 422;
     - a missing `expected_history_length` → 422.
   - Notes of `"  "` are stored as `null`. A blank `reviewer_name` gives actor `"consultant:Manager Review"`.
7. **Page render.**
   - `GET /assessments/{id}/findings` returns 200. It has one `data-eligible-conclusion` per eligible Conclusion, with the prefilled title and action title, a hidden `conclusion_version` equal to the DB version, and `href="/assessments/{id}/workpaper#wp-dpdpa-{REQS[0]}"`.
   - After creation, it has one `data-finding-card` with "Created by Priya", "Workpaper trace →", one `data-action-row`, and `data-history-action` values in order. `"consultant:Priya" not in page.text`.
   - After P2-4 `reopen` of the source Conclusion: `data-source-approved="false"` and "Source conclusion is no longer approved (now pending)".
   - An empty assessment shows "No approved conclusions are waiting for a finding." and "No findings yet.". An unknown assessment gives 404.
   - Escaping: `<script>alert(1)</script>` as an owner and in notes renders as `&lt;script&gt;alert(1)&lt;/script&gt;`, never raw.
   - `findings_page` calls `conclusion_review.conclusion_cards` exactly once (spy through the module attribute).
8. **Workpaper linkage (D-P3-1-K, P7).** After scenario 1's creation:
   - `workpaper.build_workpaper(db, a)`: REQS[0]'s entry has `findings == [{"finding_id", "title", "status", "severity", "href"}]` with the exact values, and every other entry has `findings == []`.
   - `GET /assessments/{id}/workpaper` contains `data-workpaper-finding` and `href="/assessments/{id}/findings#finding-{fid}"`. `text.count("data-workpaper-entry")` equals the number of Conclusions.
   - The Findings page links to `id="wp-dpdpa-{REQS[0]}"`'s anchor, which appears on the workpaper exactly once.
   - `GET /assessments/{id}/conclusions` and the workpaper page both contain `href="/assessments/{id}/findings"`.
9. **Legacy coexistence (D-P3-1-J).**
   - Seed a legacy assessment with one `GapItem(remediation_status="open", remediation_owner="owner@example.com")` and one with `remediation_closed_at` set. Run `run_migration(db)`.
   - The page lists two Findings with `data-finding-origin="migrated"` and "Migrated from legacy remediation". Each history shows "Imported from legacy remediation". The closed one has no status form.
   - Add an Action to the open one (200), and move its imported Action to `in_progress` (200). Its history is now `["imported", "status_changed"]`; the first entry is byte-for-byte the migrated one (four keys, no `changes`).
   - `run_migration(db)` again: no exception, `stats.findings == stats.actions == 0`, and the Action count is unchanged.
   - `tests/test_migrate_legacy.py` passes unmodified (full suite).
10. **Provenance and no Conclusion writes.** Across a create, an add, a status change and an update, the Conclusion's `(version, updated_at, outcome, rationale)` and its revision-id set are unchanged. Exactly one `audit_events` row is added (at create).
11. **Structural guards.**
    - The set of `(method, path)` over app routes whose path contains `/findings` equals exactly the five in D-P3-1-H. The P2-4 `/conclusions` set and the P2-6 `/workpaper` set are unchanged (their own tests cover them).
    - `inspect.signature(findings.create_finding)` has `conclusion_id`, and no parameter annotation contains `list`.
    - The regex `select all|create all|all conclusions|type="checkbox"|\bmultiple\b|\|\s*safe\b` (`re.IGNORECASE`) matches nothing in `app/services/findings.py`, `app/routers/findings.py`, `app/schemas/findings.py`, `pages/findings.html` or `components/finding_card.html`. The `LEGACY_BULK` constant is **still present** in the service source, and the text "Legacy bulk approval, not individually reviewed" is still present in `components/finding_card.html` (D-P3-1-N item 1).
    - `"delete"` does not occur in the lower-cased source of the findings service or router. Neither `.commit(`, `swap_conclusion` nor `ConclusionRevision(` occurs in the service. `inspect.getsource(web.findings_page)` has no `.commit(`.
12. **Nothing else moved.** `tests/test_conclusion_approval.py`, `tests/test_workpaper.py`, `tests/test_analysis_pipeline.py`, `tests/test_migrate_legacy.py`, `tests/test_white_label.py` and `tests/test_no_blended_scoring.py` pass **unmodified** (the full-suite run). The `git diff` checks are in Done criteria.

## Done criteria

- `tests/test_findings.py` passes. `.venv/bin/pytest -q` passes in full: **443 + N**, where N is the number of new cases. **No existing test file is modified.** (In a fresh `git worktree`, expect the known one-time `_guard_dev_database_untouched` teardown error described in the P2-3 handoff; nothing else.)
- `git diff --stat main` shows changes **only** in:
  - `app/services/findings.py`, `app/routers/findings.py`, `app/schemas/findings.py` (new);
  - `app/main.py`, `app/routers/web.py`, `app/services/workpaper.py`;
  - `app/templates/pages/findings.html`, `app/templates/components/finding_card.html` (new), `app/templates/components/workpaper_entry.html`, `app/templates/pages/workpaper.html`, `app/templates/pages/conclusions.html`;
  - `scripts/migrate_legacy.py`, `tests/test_findings.py`, `tasks/todo.md`, and this handoff.
- `alembic heads` is still exactly `4e8c1a9d2b57`. `grep -rn "relationship(" app/models/` is empty. `git diff --stat main -- app/services/conclusion_review.py app/routers/conclusions.py app/templates/components/conclusion_card.html app/routers/remediation.py app/static/js/app.js app/models alembic/versions` is empty.
- `tasks/todo.md`:
  - change the P2-6 line to **Merged: PR #29**, and mark Phase 2 merged;
  - under Phase 3, add a P3-1 line with its status and a link to this handoff's Results.
- **Smoke test** (per the project rule; record the outputs). Use a fresh Alembic-built DB, or a **copy** of the dev DB, and the in-process ASGI `TestClient` if a socket bind is refused. Patch `app.routers.analysis.run_gap_analysis` to three fixed items: two `non_compliant`, one `compliant`. Then:
  1. Run the analysis (all three requirements in scope). Approve the compliant Conclusion and one `non_compliant` one, and edit the other `non_compliant` one (change its rationale). `GET /assessments/{id}/findings` → 200. Record which Conclusions are eligible: it must be the approved gap one and the edited one, not the compliant one.
  2. Create a Finding from the approved one. Add a second Action. Move the first Action `open → in_progress → open`. Edit the second Action's owner.
  3. Run `SELECT a.title, a.status, a.history_json FROM actions a JOIN findings f ON f.id = a.finding_id WHERE f.assessment_id = ?` and paste the result: three entries on the first Action, two on the second.
  4. `SELECT action, entity_type, metadata_json FROM audit_events WHERE entity_type = 'finding'` → exactly one row.
  5. Resubmit the first status change with a stale `expected_history_length` → 409.
  6. Follow Findings page → "Workpaper trace →" → the entry shows the Finding link and the full revision history; `GET /evidence/{id}` of a cited version → 200.
  7. `GET /assessments/{id}?tab=report` still renders, and the legacy remediation panel is unchanged.
  8. **Browser check**, if a browser is available: create a Finding through the UI and change an Action's status. If no browser is available, say so in Results. Do not claim it.

## Rollback

- **Code:** `git revert`. There is no schema change. `findings`/`actions`/`audit_events` rows written by this task stay as inert data. The reverted app never reads them, and they remain valid inputs for a re-apply. **Keep the `scripts/migrate_legacy.py` change if reverting only the UI:** without it, a migrated Finding that gained a second Action makes the next migration run crash.
- **Data:** nothing in this task deletes or rewrites. History is append-only by construction (CAS on the exact prior content). To undo a mistaken status change, apply the reverse transition; that is itself recorded.

## Open questions (deliberately flagged, not resolved here)

1. **Cross-framework Findings.** The plan's "(one Finding may reference multiple Conclusions across frameworks)" is deliberately not implemented (D-P3-1-A). If consultants need it, Claude should design a `finding_conclusions` join table, keep `findings.conclusion_id` as the origin, and check it against PR-053's "no blending" rule. Relatedly, the PRD's "An Action may address several Findings" has no schema support (`actions.finding_id` is singular). That belongs to P3-4 or later, with the same schema-owner rule.
2. **Observations from compliant Conclusions.** The PRD glossary allows "observations", but this task restricts Findings to `GAP_OUTCOMES`. Decide with P3-3's report design.
3. **A unique index on `findings.conclusion_id`** would close the duplicate-create race (D-P3-1-F residual). It's a schema change, so it needs a Claude-owned Alembic revision. Its upgrade must refuse if duplicates exist, as P2-3's `uq_conclusions_…` guard does.
4. **A reopened source Conclusion.** The Finding stays, flagged "Source conclusion is no longer approved". Whether reports (P3-3) exclude such Findings, and whether a re-approval should re-bind the Finding (a second `finding_created`-style audit event), is for P3-3/P3-4.
5. **Dismissing or editing a Finding, with a reason.** Out of scope. It shares its "reason" column question with P2-4 open question 1 and P2-6 open question 1.

## Handed forward to P3-4 (must be honoured there)

- **History:** append through the same CAS (`WHERE history_json = :raw`) and `load_history`. Use the five-key entry shape. Use the reserved `closed` / `verified` / `reopened` actions for closure. Any extra fact (e.g. the closure `evidence_version_id`) goes into `changes` or a documented extra key, decided there. Never rewrite existing entries, including migrated `imported` ones.
- **State machine:** extend `ACTION_TRANSITIONS` rather than bypass it. `closed` must require closure evidence plus a consultant verification (PR-051). Decide whether migrated `closed` Actions (closed without evidence) need re-verification.
- **`Finding.status`:** define its lifecycle (`resolved` / `accepted_risk`) from Action closure. It is `open` for every consultant-created Finding until then.
- **Retire the `GapItem` remediation path** (`app/routers/remediation.py`, the report-tab panel) in favour of these Actions. Build the engagement rollup from `findings`/`actions`, not `GapItem`.

## Results

**Note on provenance:** Codex's implementation and its own `tests/test_findings.py` are complete and green (see below), but Codex hit its own external usage quota twice in a row right at the finish line — after implementing and testing, and again on a follow-up asked only to write this section and commit — before it could append its own account here. This section is written by the reviewing Claude session instead, from direct inspection of the diff, not from Codex's own words. No stop-on-contradiction language, `TODO`/`FIXME` marker, or other sign of an unresolved deviation was found anywhere in the new or changed files.

Implemented on `codex/p3-1-findings-and-actions`, grounded against `main` `9bcd972`:

- **New files:** `app/routers/findings.py` (229 lines), `app/services/findings.py` (654 lines — eligibility, cardinality guard, append-only history CAS, `ACTION_TRANSITIONS` state machine), `app/schemas/findings.py` (42 lines), `app/templates/pages/findings.html`, `app/templates/components/finding_card.html`, `tests/test_findings.py` (1141 lines, 12 required scenarios, matching every scenario named in `## Test scenarios` with no scenario dropped or weakened).
- **Changed files:** `app/routers/web.py` (new findings-page route + registration), `app/main.py` (router registration), `app/services/workpaper.py` + `workpaper_entry.html` + `conclusions.html`/`workpaper.html` (the Finding↔workpaper linkage from D-P3-1's decisions), and `scripts/migrate_legacy.py` (idempotency fix: a rerun now skips a Finding entirely once it exists, rather than only skipping the Finding row and still trying to look up its Action via `scalar_one_or_none()` — which would raise `MultipleResultsFound` once a consultant-created second Action exists on a migrated Finding).
- **D-P3-1-A (cardinality)** honoured exactly: single `conclusion_id` FK, no join table, no schema change — confirmed via `git diff --stat` showing no touch to `app/models/` or `alembic/versions/`.
- **Legacy files untouched:** `git diff --stat -- app/routers/review.py app/services/scoring.py app/utils/pdf_export.py app/routers/reports.py app/routers/conclusions.py app/services/conclusion_review.py app/models/ alembic/versions/` is empty.
- **Test suite:** `.venv/bin/pytest -q` → **463 passed** (443 baseline + 20 new), independently re-run and confirmed by the reviewing Claude session in this worktree, plus the one known pre-existing, unrelated `tests/test_workpaper.py` fresh-worktree teardown artifact (documented in prior handoffs, not a regression).
- **No deviations found.** `tasks/todo.md` and the commit are being finished by the reviewing Claude session on Codex's behalf, mirroring how P2-4 and P2-6 were committed when Codex's sandbox couldn't write `.git` — here the blocker was Codex's own usage quota instead, but the resolution is the same: verify independently, then commit.
