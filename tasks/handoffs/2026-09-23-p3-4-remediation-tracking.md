# P3-4: Remediation tracking: evidence-backed closure and separate consultant verification on Actions, a derived Finding status, retirement of the GapItem remediation path, and an engagement-level action rollup

**Plan:** `docs/plans/2026-09-21-002-revised-implementation-plan.md`, Phase 3, task P3-4 ("Migrate remediation fields from GapItem to standalone Actions"; "Closure verification: consultant marks action as closed, attaches closure evidence, records in history_json"; "Dashboard: engagement-level rollup of open/closed actions"; test: "Full lifecycle: finding → action → update → close → verify closure in history."), and the Phase 3 exit criterion "Findings → Actions → Closure lifecycle working". Decision **D2** in `tasks/2026-09-21-adversarial-review.md` ("JSON for claims/citations/action-history"; `history_json` "replaces ActionUpdate + ClosureVerification tables"). PRD `docs/product/2026-09-21-cyberassess-product-requirements.md`: **PR-051** ("update history is append-only; Closed requires closure Evidence plus consultant verification; client-managed actions are not exposed"), **PR-050** ("engagement rollup does not sever or obscure the origin"), **PR-052** ("a live consultant-operated action tracker"), the Action lifecycle paragraph ("`Closed` requires closure evidence and a consultant verification. Reopening creates a new update; it does not erase the prior closure event."), and the journey step "The consultant records client updates …, reviews closure evidence, and verifies Action closure." **Binding hand-forward:** P3-1's "Handed forward to P3-4" (`tasks/handoffs/2026-09-23-p3-1-findings-and-actions.md`): extend `ACTION_TRANSITIONS` rather than bypass it; `closed` requires closure evidence plus consultant verification; decide re-verification of migrated `closed` Actions; define `Finding.status`'s `resolved`/`accepted_risk` lifecycle; retire the `GapItem` remediation path; build the rollup from `findings`/`actions`, not `GapItem`. Each is closed below (D-P3-4-B, C/D, F, G, K, L).
**Owner:** Codex, from this Claude spec (per `tasks/agent-ownership.md`: "P3-4 Remediation tracking | Codex, from Claude spec"). Every architectural fork is closed below. **If the code forces a deviation from any decision, stop and report it in `## Results`. Do not pick an alternative.** Merge gate: the standard `[AR]` adversarial review (`tasks/todo.md` tags Phase 3 `[AR: report immutability, provenance, closure verification]`; closure verification is D-P3-4-C/D/F).
**Depends on:** P3-1 (merged, PR #30): `app/services/findings.py`, `app/routers/findings.py`, `app/schemas/findings.py`, `components/finding_card.html`. `main` is at `c9d0196`.
**Runs in parallel with:** P3-3 (PDF updates). P3-3 **reads** `findings.findings_page(...)` and the existing fields `FindingView.finding`, `.card`, `.source_approved`, `.actions[i].action`. **Do not rename, remove or reorder any existing field of `FindingView`, `ActionView`, `HistoryEntryView`, `EligibleConclusion` or `FindingsPage`**; add new fields only at the end, each with a default. P3-3 defines its own copy of the Action status labels (`report_content.ACTION_STATUS_LABELS`) with exactly the values in D-P3-4-A; keep them identical. Files both tasks may touch: `app/main.py`, `app/routers/web.py` (one new page route each, in different places), `app/templates/pages/engagement_detail.html` (one link each) and `tasks/todo.md`. If P3-3 lands first, keep both sides of each conflict.
**Blocks:** P4-2 (longitudinal demo: "partial remediation", "action lifecycle").
**Failing contract suite: none pre-written.** A grep of `tests/` for `P3-4`, `/close`, `/verify`, `/reopen`, `closure` and `remediation_rollup` finds nothing that tests this task. As with P2-4 onward, **Codex writes `tests/test_remediation_tracking.py` itself** from `## Test scenarios`, following the fixture pattern of `tests/test_findings.py` (step 10). Every scenario listed is required. You may add cases, but you may not drop or weaken one. **Three existing assertions must change, and only these** (D-P3-4-N): `tests/test_findings.py` scenario 4's exact `ACTION_TRANSITIONS` literal, `tests/test_findings.py` scenario 11's exact `/findings` route set, and one path in `tests/test_analysis_pipeline.py::test_legacy_consumers_do_not_read_the_new_tables`.

## Goal

1. On `/assessments/{assessment_id}/findings`, a consultant **closes** an open or in-progress Action by choosing a piece of **closure evidence** already uploaded to the assessment. The Action becomes `closed` ("Closed, awaiting verification"), and the history entry records exactly which evidence version (with its SHA-256) was attached.
2. As a **separate, later request**, a consultant **verifies** the closure. The system re-checks that the attached evidence version is still intact and active, then moves the Action to `verified` ("Closed and verified") and records the verification in history. A closed or verified Action can be **reopened** with a reason; the earlier closure and verification entries stay in the history.
3. A Finding's `status` now **follows its Actions**: `resolved` when every Action is verified, `in_progress` once any work has started, `open` otherwise.
4. The legacy `GapItem` remediation editor is **retired**: its API routes are removed, and the Report tab's per-gap editor becomes a read-only record of any legacy values. Remediation is tracked only through Findings and Actions.
5. `/engagements/{engagement_id}/remediation` shows an **engagement-level rollup** of Actions across the engagement's assessments: counts by status, overdue and unassigned counts, a severity breakdown, per-owner workload, per-assessment counts, and lists of overdue and awaiting-verification Actions. Every row keeps its assessment, framework and requirement. It shows counts, never a score.

## Current state

Grounded against `c9d0196` on `main`. Baseline `.venv/bin/pytest -q` → **477 passed, 115 warnings** (I ran it at `c9d0196`). `alembic heads` → `4e8c1a9d2b57 (head)`. Re-locate everything by symbol name.

- **`app/services/findings.py`** (P3-1). I read it in full. Module docstring: `"""Findings and Actions (P3-1): one Finding per individually approved gap Conclusion, and append-only Action history in actions.history_json. Never commits."""`.
  - Constants: `FINDING_STATUSES = ("open", "in_progress", "resolved", "accepted_risk")`, `NEW_FINDING_STATUS = "open"`, `ACTION_STATUSES = ("open", "in_progress", "closed", "verified")`, `NEW_ACTION_STATUS = "open"`, **`ACTION_TRANSITIONS = {"open": ("in_progress",), "in_progress": ("open",), "closed": (), "verified": ()}`**, `CLOSURE_STATUSES = ("closed", "verified")`, `ELIGIBLE_STATES`, `PRIORITIES`, `PRIORITY_BY_SEVERITY`, `HISTORY_KEYS = ("actor", "action", "timestamp", "notes", "changes")`, `HISTORY_ACTIONS = ("created", "status_changed", "updated")`, `LEGACY_HISTORY_ACTION = "imported"`, `TRACKED_FIELDS`, `HISTORY_LABELS` (`created`, `status_changed`, `updated`, `imported`), `MAX_TITLE`, `MAX_OWNER`, `MAX_NOTES = 2000`, `FINDING_CREATED_EVENT`, `FINDING_ENTITY`; messages including `STALE_ACTION`, **`CLOSURE_RESERVED = "Closing or verifying an action requires closure evidence and is not available yet."`**, **`TERMINAL = "This action is closed and cannot be changed here."`**, `UNREADABLE_HISTORY`, `NO_CHANGES`.
  - Exceptions: `FindingError` (`status_code`, `message`), `FindingNotFound` 404, `InvalidFindingRequest` 400, `FindingConflict` 409.
  - Frozen dataclasses: `HistoryEntryView(sequence, action, label, actor_display, timestamp, notes, changes)`, `ActionView(action, history, history_readable, history_length, allowed_statuses, editable)`, `FindingView(finding, card, origin, created_by, source_approved, workpaper_href, actions)`, `EligibleConclusion`, `FindingsPage(eligible, findings)`. None has a defaulted field. The module imports `from dataclasses import dataclass` only.
  - Helpers: `load_history(raw)` (the test seam; raises `InvalidFindingRequest(UNREADABLE_HISTORY)`), `_text`, `_notes` (≤ 2000, blank → `None`), `_title`, `_owner`, `_stored_date`, `_date_value`, `_entry(*, actor, action, notes, changes, now)` (builds the five-key entry), `_created_entry`, `_finding(db, assessment_id, finding_id)` (404 "Finding not found"), `_action(db, finding, action_id)` (404 "Action not found"), **`_append(db, action, *, expected_history_length, build_entry)`**: reads `raw`, `load_history(raw)`, raises `FindingConflict(STALE_ACTION)` on a length mismatch, calls `build_entry()` → `(entry, field_values)`, then `update(Action).where(Action.id == …, Action.history_json == raw).values(history_json=json.dumps(history + [entry]), **field_values).execution_options(synchronize_session=False)`, raises `STALE_ACTION` unless `rowcount == 1`, then `db.expire(action)`. Staleness is checked before any rule in `build_entry`.
  - Public writers: `create_finding`, `add_action`, `change_action_status` (inside `_build`: current in `CLOSURE_STATUSES` → `TERMINAL`; unknown target → "Unknown action status."; **target in `CLOSURE_STATUSES` → `CLOSURE_RESERVED`**; target not in `ACTION_TRANSITIONS.get(current, ())` → `f"An action cannot move from {current} to {status}."`), `update_action` (status not in `("open", "in_progress")` → `TERMINAL`). **No writer touches `Finding.status` after creation.**
  - Readers: `_actor_display`, `_action_view(action)` (`allowed_statuses=ACTION_TRANSITIONS.get(action.status, ())`, `editable=action.status in ("open", "in_progress")`; unreadable history → empty, not editable), `findings_page(db, assessment_id)` (four statements: `conclusion_review.conclusion_cards`, Findings, Actions, `finding_created` events), `finding_view(db, *, assessment_id, finding_id)`.
- **`app/routers/findings.py`** (P3-1): `router = APIRouter(prefix="/api/assessments", tags=["findings"])`; helpers `_payload` (JSON or form, `""` → `None`), `_validated` (422), `_toast` (URL-encoded), `_error(db, exc)` (rollback; 404 raises `HTTPException`; else JSON `{"detail"}` + toast), `_card_response(request, db, *, assessment_id, finding_id, message)` (re-renders `components/finding_card.html` with `{"assessment", "view"}`). Four `async def` POST routes: create, add action, `…/actions/{action_id}/status`, `…/actions/{action_id}/update`. Each commits once on success.
- **`app/schemas/findings.py`**: `FindingCreateIn`, `ActionCreateIn`, `ActionStatusIn` (`status: Literal["open", "in_progress", "closed", "verified"]`, `expected_history_length: int`, `notes`, `reviewer_name`), `ActionUpdateIn`.
- **`components/finding_card.html`**: per Action, `<div data-action-row id="action-{{ row.action.id }}" data-action-status="{{ row.action.status }}">`; a line "Owner: … · Target: … · Status: {{ row.action.status }}"; the history `<ol data-action-history>` with `<li data-history-action="{{ e.action }}">` rendering `changes` as `{{ name }}: {{ change['from'] or '—' }} → {{ change['to'] or '—' }}`; the status form when `row.allowed_statuses` (a `<select name="status">` of exactly those values, posting to `…/status`); the "Edit details" form when `row.editable`, **else the text "Closed and verified actions cannot be changed here."**; then "Add action". Everything uses `hx-target="#finding-{{ view.finding.id }}" hx-swap="outerHTML" hx-include="#reviewer-name"`.
- **P3-1 tests that constrain this task** (`tests/test_findings.py`):
  - scenario 4 asserts **`findings.ACTION_TRANSITIONS == {"open": ("in_progress",), "in_progress": ("open",), "closed": (), "verified": ()}`** exactly, and `CLOSURE_STATUSES == ("closed", "verified")`. Its parametrized cases post `closed`/`verified` to the **generic `…/status` route** and expect 400 `findings.CLOSURE_RESERVED` (compared through the constant), same-status 400 with the formatted message, and `open ⇄ in_progress` 200;
  - scenario 4 (terminal): an Action set to `closed` gets 400 `findings.TERMINAL` for **every** target on `…/status` and on `…/update`; the page contains "Closed and verified actions cannot be changed here."; and the page text from `id="action-{id}"` onward does **not** contain `actions/{id}/status`;
  - scenario 9: a migrated `closed` Action's page slice doesn't contain `actions/{id}/status`;
  - scenario 11: the set of routes whose path contains **`/findings`** equals exactly P3-1's five; the regex `select all|create all|all conclusions|type="checkbox"|\bmultiple\b|\|\s*safe\b` (case-insensitive) matches nothing in the service, router, schema, `pages/findings.html` or `components/finding_card.html`; `"delete"` is absent from the lower-cased service and router source; the service has no `.commit(`, `swap_conclusion` or `ConclusionRevision(`; `LEGACY_BULK` and the text "Legacy bulk approval, not individually reviewed" are still present;
  - scenario 1 asserts `finding.status == "open"` **immediately after creation** (and scenario 8 compares the workpaper's `status` with the same fresh row).
- **`scripts/migrate_legacy.py`**: for legacy (non-pipeline) assessments, each `GapItem` with `remediation_status is not None` becomes one `Finding` (`status = map_finding_status(...)`: the value if in `FINDING_STATUSES`, else `"open"` with a warning, so a legacy `"closed"` maps to Finding `"open"`) and one `Action` (`status = map_action_status(...)`: **`"closed"` iff `remediation_closed_at` is set, else `"open"`**), with one four-key `imported` history entry by `system:migration`. **A migrated `closed` Action has no closure evidence and no `closed` history entry.** Assessments with an `AnalysisRun` are skipped. A re-run skips any existing Finding.
- **The legacy remediation path:**
  - **`app/routers/remediation.py`**: `PATCH /api/assessments/{assessment_id}/gap-items/{item_id}/remediation` (writes `GapItem.remediation_status/owner/target_date/notes`, sets or clears `remediation_closed_at`) and `GET /api/assessments/{assessment_id}/remediation-summary` (counts over `GapItem.remediation_status`). Registered in `app/main.py` (`remediation,` in the router import list; `app.include_router(remediation.router)`). Its schemas are `app/schemas/remediation.py` (`RemediationUpdate`, `RemediationSummary`), imported nowhere else.
  - **No template and no test calls either route.** `partials/remediation_panel.html` (a `<details>` with an `hx-patch` form to the PATCH route, status options open/in progress/closed/accepted risk) is included per gap in `partials/report_summary.html` (`<div id="remediation-{{ item.id }}">{% include "partials/remediation_panel.html" ignore missing %}</div>`). `partials/remediation_summary.html` (a "Remediation Progress" bar over `remediation_counts.open/in_progress/closed/accepted_risk/total`) is included at `<div id="remediation-summary-area">`. **`web.report_summary` computes `remediation_counts` itself** from `GapItem.remediation_status` (the `applicable_gap_items` block) and passes it in the context; the API summary route is unused.
  - `GapItem.remediation_status` has ORM `default="open"`, so every pipeline-created `GapItem` starts `"open"`. **Every analysis re-run archives the old `GapItem` rows into `GapReport.legacy_history` and replaces them** (`app/routers/analysis.py`), so live `GapItem` remediation values only ever reflect edits made since the latest run. `GapItem` data is never shown on the Findings page.
  - `tests/test_analysis_pipeline.py::test_legacy_consumers_do_not_read_the_new_tables` greps five files, **including `app/routers/remediation.py`**, for `Conclusion|AnalysisRun|analysis_pipeline`.
- **Evidence (P2-1), `app/services/evidence.py`:**
  - `Evidence` (`id`, `engagement_id`, `assessment_id` nullable, `status` ∈ `EVIDENCE_STATUSES = ("quarantined", "active", "rejected", "invalidated", "archived")`, …) and `EvidenceVersion` (`id`, `evidence_id`, `version_number`, `storage_path`, `file_hash_sha256`, `status` ∈ `VERSION_STATUSES = ("quarantined", "active", "superseded", "rejected")`, `original_filename`, …).
  - `active_versions_in_scope(db, assessment_id) -> list[tuple[Evidence, EvidenceVersion]]`: active Evidence that belongs to the assessment or is mapped to it through `EvidenceUse`, each with its **active** version, ordered `Evidence.created_at, Evidence.id`.
  - `verify_version(db, version_id) -> bool`: the blob exists under `settings.upload_dir` and its SHA-256 equals `file_hash_sha256`.
  - `ingest_upload(db, *, assessment_id, filename, content, category, …)`: requires `assessment.engagement_id` (else `EngagementRequired`), accepts `pdf`/`docx`/`png`/`jpg`/`jpeg`/`webp`/`txt`, auto-releases from quarantine (placeholder scan), needs extractable text, and **commits**.
  - Evidence detail page: `GET /evidence/{evidence_id}` (`web.evidence_detail_page`). The assessment page is where consultants upload evidence.
- **Engagement pages** (`app/routers/web.py`): `engagement_detail` (`GET /engagements/{engagement_id}`) loads `Engagement` (404 "Engagement not found"), `Client` (404 "Client not found"), and the assessments with `Assessment.engagement_id == engagement_id` and `Assessment.status != "archived"`, and renders `pages/engagement_detail.html` (breadcrumb `Portfolio / {{ client.name }} / {{ engagement.name }}`, the header `<p class="mt-2 text-sm text-gray-500 dark:text-gray-400">{{ client.name }} · …</p>`, the assessments list, magic links). **No page shows Findings or Actions at engagement level.** `pages/findings.html` has header links "Conclusions (decide) →" and "Workpaper (read-only trace) →".
- **Route-set guards elsewhere:** `/conclusions` (P2-4 scenario 12), `/workpaper` (P2-6 scenario 9), `/snapshots` (P3-2 scenario 12). `tests/test_white_label.py` forbids `CyberAssess` in templates; `tests/test_no_blended_scoring.py` forbids `overall_score` in templates.
- **PRD vocabulary vs schema.** The PRD lists Action states "Open, In progress, Blocked, Ready for verification, Verified, Closed, or Accepted risk", where **Closed means verified closure**. The schema (P1-2) has exactly four: `open | in_progress | closed | verified`. D-P3-4-A maps them.

## Decisions (made here so they are not relitigated)

### D-P3-4-A. What the four Action statuses mean, and how they are labelled

| Stored `status` | Meaning | Label (`ACTION_STATUS_LABELS`, exact) | PRD term |
|---|---|---|---|
| `open` | Not started | `Open` | Open |
| `in_progress` | Work under way | `In progress` | In progress |
| `closed` | Closure evidence attached; **not yet verified** | `Closed, awaiting verification` | Ready for verification |
| `verified` | A consultant verified the closure evidence | `Closed and verified` | Closed (verified) |

Only `verified` counts as done anywhere (Finding status, rollup "verified"). A `closed` Action is always shown as awaiting verification. **PR-051's "Closed requires closure Evidence plus consultant verification" is therefore satisfied by `verified`**, and a `closed` row can never be presented as finished. `Blocked` and Action-level `Accepted risk` have no stored status and are **not implemented** (no schema change; open question 1).

### D-P3-4-B. The state machine: extend `ACTION_TRANSITIONS`; the generic status route keeps refusing closure targets

```python
ACTION_TRANSITIONS = {
    "open": ("in_progress", "closed"),
    "in_progress": ("open", "closed"),
    "closed": ("verified", "in_progress"),
    "verified": ("in_progress",),
}
CLOSURE_STATUSES = ("closed", "verified")          # unchanged
GENERIC_STATUS_TARGETS = ("open", "in_progress")   # the only targets the …/status route accepts
```

`ACTION_TRANSITIONS` is the **single** table of legal moves. Each route checks its move against it; no route writes a status the table doesn't allow.

| Move | Route (only this one) | Extra requirement |
|---|---|---|
| `open ⇄ in_progress` | `…/status` (P3-1, unchanged) | none |
| `open`/`in_progress` → `closed` | `…/close` (new) | closure evidence (D-P3-4-C) |
| `closed` → `verified` | `…/verify` (new) | a separate request; evidence re-checked (D-P3-4-D) |
| `closed`/`verified` → `in_progress` | `…/reopen` (new) | a reason (D-P3-4-E) |

- **`change_action_status` keeps its exact check order and messages.** A current status in `CLOSURE_STATUSES` → `TERMINAL`; a target in `CLOSURE_STATUSES` → `CLOSURE_RESERVED`; a target not in `ACTION_TRANSITIONS.get(current, ())` → the formatted `INVALID_TRANSITION`. Add one defensive check after the `CLOSURE_RESERVED` one: a target not in `GENERIC_STATUS_TARGETS` → `CLOSURE_RESERVED`. (Unreachable today, since the schema `Literal` allows only the four statuses.)
- **`CLOSURE_RESERVED`'s text changes** to `"Closing and verifying have their own steps: close with closure evidence, then verify."`, because "not available yet" is no longer true. `TERMINAL` keeps its exact text: it means "not changeable **on this route**", and the card offers the reopen and verify steps instead.
- **Why `verified` → `in_progress` is allowed:** the PRD says "Reopening creates a new update; it does not erase the prior closure event." A regression found after verification must be recordable on the same Action, with its verification still visible in history. Every reopen goes to `in_progress`, never to `open`, because work is by definition under way again.
- **Why `open` → `closed` directly is allowed:** work often happens between consultant touchpoints. The evidence requirement, not an intermediate status, is the control.

### D-P3-4-C. Close: requires one piece of closure evidence, chosen from the assessment's active, intact evidence

`close_action(...)` moves `open`/`in_progress` → `closed` and requires `evidence_version_id`.

**Eligible closure evidence (exact):** `evidence_version_id` must be the id of the **active** version of an **active** `Evidence` returned by `evidence_service.active_versions_in_scope(db, finding.assessment_id)` (so it belongs to, or is mapped to, the Finding's own assessment), **and** `evidence_service.verify_version(db, evidence_version_id)` must be `True` (its stored bytes are present and match their hash). Anything else is `CLOSURE_EVIDENCE_INVALID`.

- **No new upload path.** The consultant uploads closure evidence through the existing assessment evidence upload (P2-1) or receives it through a magic link (P2-5), then picks it on the card. This keeps hashing, quarantine and versioning in one place.
- **No `EvidenceUse` row is created.** `EvidenceUse` maps evidence to a requirement for **assessment** analysis (it feeds the workpaper's "mapped evidence" and analysis scope). Closure evidence proves remediation after the fact, and mixing it into the analysis inputs would change what the next analysis run sees. The link lives in the Action's history (below).
- **The history entry** (action `closed`) has the five `HISTORY_KEYS` **plus one documented extra key, `evidence`** (P3-1's hand-forward allowed "a documented extra key"):
  ```jsonc
  {
    "actor": "consultant:Priya", "action": "closed", "timestamp": "…", "notes": "Client sent signed policy" | null,
    "changes": {"status": {"from": "in_progress", "to": "closed"}},
    "evidence": {"evidence_id": "…", "evidence_version_id": "…", "version_number": 2,
                 "sha256": "<64 hex, the version's file_hash_sha256>", "filename": "<the version's original_filename>"}
  }
  ```
  `CLOSURE_HISTORY_KEYS = HISTORY_KEYS + ("evidence",)` and `EVIDENCE_KEYS = ("evidence_id", "evidence_version_id", "version_number", "sha256", "filename")`, both exact. The `sha256` freezes **which bytes** were attached, so a later version upload can't silently change what the closure pointed to.

### D-P3-4-D. Verify: a separate request by a consultant, which re-checks the attached evidence

`verify_action(...)` moves `closed` → `verified`. It takes no evidence input; it verifies **the closure on record**.

- **The closure on record** is the most recent history entry with `action == "closed"` that comes **after** every `reopened` entry. It must carry an `evidence` dict with exactly `EVIDENCE_KEYS`. If there is none, the Action was closed without evidence (a migrated legacy closure, D-P3-4-F) → `LEGACY_CLOSURE`.
- **Re-check (exact):** the `EvidenceVersion` with that id exists; its `file_hash_sha256` equals the recorded `sha256`; `evidence_service.verify_version(db, id)` is `True`; its `status` is `active` or `superseded` (a newer version uploaded after closure doesn't invalidate what was attached); and its `Evidence.status == "active"` (invalidated, rejected or archived evidence can't support a verification). Any failure → `CLOSURE_EVIDENCE_CHANGED`.
- **The history entry** (action `verified`) has `CLOSURE_HISTORY_KEYS`: `changes == {"status": {"from": "closed", "to": "verified"}}` and `evidence` equal to the closure-on-record's `evidence` dict (copied, so each verification states what it verified).
- **Two distinct acts, as PR-051 requires:** closing and verifying are different routes and different requests, each with its own history entry, actor and timestamp. **The same consultant may do both.** The PRD allows it ("The same consultant may prepare and approve in v1; the system still records both acts"), and there is no auth to separate duties (open question 2).
- **No `audit_events` rows.** As in P3-1, `history_json` is the Action's trail (D2: it "replaces … ClosureVerification tables").

### D-P3-4-E. Reopen: `closed`/`verified` → `in_progress`, with a required reason

`reopen_action(...)`: current status must be in `CLOSURE_STATUSES` (else `NOT_REOPENABLE`); `notes` is **required** and non-blank (else `REOPEN_REASON_REQUIRED`), ≤ 2000. The entry has `HISTORY_KEYS`, action `reopened`, `changes == {"status": {"from": <current>, "to": "in_progress"}}`. Earlier `closed`/`verified` entries are never touched. After a reopen, the only way back to `closed` is a new `close` with evidence.

### D-P3-4-F. Migrated legacy `closed` Actions are **not** grandfathered: they must be reopened, closed again with evidence, then verified

A migrated `closed` Action (status `closed`, history `[imported]`, no evidence) is shown as `Closed, awaiting verification` with the note **"Closed without closure evidence (legacy). Reopen it to close it again with evidence."** It offers **only** the reopen step. `verify` refuses it with `LEGACY_CLOSURE`.

- **Why not grandfather:** PR-051 is unconditional ("Closed requires closure Evidence plus consultant verification"). Treating an evidence-less legacy closure as verified would put exactly the unverified closure PR-051 forbids into every rollup and every future report. It would also need a special history action that a later reader would have to understand.
- **Why not "attach evidence to the existing closure":** that would make a `closed` entry that isn't the one that closed the Action, or rewrite history. Reopen → close → verify uses only the three general steps, and the history reads truthfully: imported as closed, reopened because no evidence, closed with evidence X, verified.
- **Nothing is backfilled or rewritten.** Migrated rows keep their `imported` entry byte for byte (P3-1 D-P3-1-J).

### D-P3-4-G. `Finding.status` is derived from its Actions after every Action status change; `accepted_risk` is never derived

After every successful `add_action`, `change_action_status`, `close_action`, `verify_action` and `reopen_action` (**not** `create_finding`, whose Finding and Action both start `open`, and not `update_action`, which changes no status), in the same transaction, `_sync_finding_status(db, finding)`:

1. If `finding.status == "accepted_risk"`: leave it (never derived; see below).
2. `statuses = db.execute(select(Action.status).where(Action.finding_id == finding.id)).scalars().all()` (a fresh read: `_append` updates through Core with `synchronize_session=False`).
3. Derive: `"resolved"` if `statuses` is non-empty and every status is `verified`; else `"in_progress"` if any status is not `open`; else `"open"`.
4. If it differs, set `finding.status` to it and flush.

`FINDING_STATUS_LABELS = {"open": "Open", "in_progress": "In progress", "resolved": "Resolved", "accepted_risk": "Accepted risk"}`.

- **`resolved` means every Action is verified.** A `closed`-but-unverified Action keeps its Finding `in_progress`. Adding a new Action to a `resolved` Finding moves it back to `in_progress`, and so does reopening a verified Action.
- **`accepted_risk` is a consultant judgment that the gap will not be remediated. It is not a result of Action closure, so it is never derived.** P3-4 never writes it. A migrated `accepted_risk` Finding keeps that status and is skipped by the sync. Recording a new risk acceptance needs a reason and an audit trail at Finding level, which has no history column today; it is **deferred** (open question 3). The retired legacy panel's "Accepted risk" option is therefore not replaced in this task. That is a known, stated gap.
- **Migrated Findings** keep their migrated status until one of their Actions changes, then follow the derivation.
- **Why derived, not chosen:** a stored status that a consultant picks can contradict the Actions (the PRD: "A user cannot type an arbitrary status that contradicts the underlying work"). Derivation can't drift.

### D-P3-4-H. History vocabulary additions and readers

- `HISTORY_ACTIONS = ("created", "status_changed", "updated", "closed", "verified", "reopened")`.
- `HISTORY_LABELS` gains `"closed": "Closed with evidence"`, `"verified": "Closure verified"`, `"reopened": "Reopened"`.
- `closed` and `verified` entries have exactly `CLOSURE_HISTORY_KEYS`; every other entry this code writes has exactly `HISTORY_KEYS`. Migrated `imported` entries keep their four keys.
- `HistoryEntryView` gains a last field `evidence: dict | None = None`: the entry's `evidence` when it is a dict, else `None`.
- Every append goes through `_append` (CAS on the exact prior `history_json`, D-P3-1-F) with the caller's `expected_history_length`. Nothing rewrites, reorders or removes an entry.

### D-P3-4-I. Routes and schemas (exact)

Three new routes in **`app/routers/findings.py`**, following its existing conventions exactly (`async def`, `_payload`, `_validated`, `_error`, one commit on success, `_card_response` re-render with a success toast, actor `conclusion_review.reviewer_actor(body.reviewer_name)`):

| Method + path | Handler | Success toast |
|---|---|---|
| `POST /api/assessments/{assessment_id}/findings/{finding_id}/actions/{action_id}/close` | `close_action_route` | `Action closed` |
| `POST /api/assessments/{assessment_id}/findings/{finding_id}/actions/{action_id}/verify` | `verify_action_route` | `Closure verified` |
| `POST /api/assessments/{assessment_id}/findings/{finding_id}/actions/{action_id}/reopen` | `reopen_action_route` | `Action reopened` |

One new page route in **`app/routers/web.py`**, directly after `engagement_detail`: `GET /engagements/{engagement_id}/remediation` → `remediation_tracker_page` (D-P3-4-L).

**Why nested under `/findings`:** every Action route already lives there, keyed by assessment, finding and action. That keeps the 404 scoping (`_finding`, `_action`) identical. The price is that P3-1's exact `/findings` route-set assertion must list the three new routes (D-P3-4-N).

**Schemas, new in `app/schemas/findings.py`:**
- `ActionCloseIn`: `evidence_version_id: str | None = None`, `expected_history_length: int`, `notes: str | None = None`, `reviewer_name: str | None = None`;
- `ActionVerifyIn`: `expected_history_length: int`, `notes: str | None = None`, `reviewer_name: str | None = None`;
- `ActionReopenIn`: `expected_history_length: int`, `notes: str | None = None`, `reviewer_name: str | None = None`.

A missing or non-int `expected_history_length` → 422.

### D-P3-4-J. Service API additions to `app/services/findings.py`, exact

Change the module docstring to: `"""Findings and Actions (P3-1, P3-4): one Finding per individually approved gap Conclusion, append-only Action history in actions.history_json, evidence-backed closure with separate verification, and a Finding status derived from its Actions. Never commits."""`. Change `from dataclasses import dataclass` to `from dataclasses import dataclass, field`, and add `from app.models.evidence import Evidence, EvidenceVersion` and `from app.services import evidence as evidence_service`.

```python
ACTION_TRANSITIONS = {...}                 # D-P3-4-B
GENERIC_STATUS_TARGETS = ("open", "in_progress")
ACTION_STATUS_LABELS = {"open": "Open", "in_progress": "In progress",
                        "closed": "Closed, awaiting verification", "verified": "Closed and verified"}
FINDING_STATUS_LABELS = {...}              # D-P3-4-G
CLOSURE_HISTORY_KEYS = HISTORY_KEYS + ("evidence",)
EVIDENCE_KEYS = ("evidence_id", "evidence_version_id", "version_number", "sha256", "filename")
CLOSURE_VERSION_STATUSES = ("active", "superseded")

# Messages (exact; tests compare them)
CLOSURE_RESERVED = "Closing and verifying have their own steps: close with closure evidence, then verify."
NOT_CLOSABLE = "Only an open or in-progress action can be closed."
CLOSURE_EVIDENCE_REQUIRED = "Choose the closure evidence before closing this action."
CLOSURE_EVIDENCE_INVALID = "Closure evidence must be an active, intact evidence version of this assessment."
NOT_VERIFIABLE = "Only a closed action can be verified."
LEGACY_CLOSURE = "This action was closed without closure evidence. Reopen it and close it again with evidence before verifying."
CLOSURE_EVIDENCE_CHANGED = "The closure evidence is missing, changed or no longer active. Reopen the action and close it again with current evidence."
NOT_REOPENABLE = "Only a closed or verified action can be reopened."
REOPEN_REASON_REQUIRED = "Give a reason for reopening this action."

def close_action(db, *, assessment_id: str, finding_id: str, action_id: str, evidence_version_id: str | None,
                 expected_history_length: int, notes: str | None, actor: str, now: datetime | None = None) -> Action: ...
def verify_action(db, *, assessment_id: str, finding_id: str, action_id: str,
                  expected_history_length: int, notes: str | None, actor: str, now: datetime | None = None) -> Action: ...
def reopen_action(db, *, assessment_id: str, finding_id: str, action_id: str,
                  expected_history_length: int, notes: str | None, actor: str, now: datetime | None = None) -> Action: ...
def closure_on_record(history: list[dict]) -> dict | None: ...   # D-P3-4-D: the evidence dict, or None
```

**Check order (exact).** All three: load the Finding, then the Action (404s), then `_append` (which does `load_history` + staleness **first**), then inside `build_entry`:
- **`close_action`:** `"closed" not in ACTION_TRANSITIONS.get(current, ())` → `NOT_CLOSABLE`; blank `evidence_version_id` → `CLOSURE_EVIDENCE_REQUIRED`; not eligible (D-P3-4-C) → `CLOSURE_EVIDENCE_INVALID`; `_notes`; entry and `{"status": "closed"}`.
- **`verify_action`:** `"verified" not in ACTION_TRANSITIONS.get(current, ())` → `NOT_VERIFIABLE`; `closure_on_record(history)` is `None` → `LEGACY_CLOSURE`; re-check fails → `CLOSURE_EVIDENCE_CHANGED`; `_notes`; entry and `{"status": "verified"}`.
- **`reopen_action`:** `current not in CLOSURE_STATUSES` → `NOT_REOPENABLE`; blank notes → `REOPEN_REASON_REQUIRED`; `_notes` (length); entry and `{"status": "in_progress"}` (a legal move: `"in_progress" in ACTION_TRANSITIONS[current]`).

Then `_sync_finding_status(db, finding)` (D-P3-4-G). Also call it at the end of `add_action` and `change_action_status`.

**Read-model additions** (fields appended at the end, each with a default):
- `HistoryEntryView.evidence: dict | None = None`.
- `ActionView`: `status_label: str = ""` (`ACTION_STATUS_LABELS.get(status, status)`), `closable: bool = False` (readable and status in `("open", "in_progress")`), `verifiable: bool = False` (readable, status `closed`, and `closure_evidence` is not `None`), `legacy_closure: bool = False` (readable, status `closed`, `closure_evidence is None`), `reopenable: bool = False` (readable and status in `CLOSURE_STATUSES`), `closure_evidence: dict | None = None` (`closure_on_record(history)` when readable and status in `CLOSURE_STATUSES`).
- **`ActionView.allowed_statuses`** becomes `()` when the status is in `CLOSURE_STATUSES`, else `tuple(t for t in ACTION_TRANSITIONS.get(status, ()) if t in GENERIC_STATUS_TARGETS)`. So the generic `<select>` still offers exactly `in_progress` for `open` and `open` for `in_progress`, and closed/verified rows still have no status form.
- `FindingView`: `status_label: str = ""`, and `closure_options: list[dict] = field(default_factory=list)`. `findings_page` computes the options **once** per page: one entry `{"evidence_version_id", "evidence_id", "label"}` per pair from `evidence_service.active_versions_in_scope(db, assessment_id)`, in that order, with `label = f"{version.original_filename} v{version.version_number} ({version.file_hash_sha256[:12]})"`, and attaches the same list to every `FindingView`. (It doesn't hash files; integrity is checked on close and verify.)

### D-P3-4-K. Retiring the `GapItem` remediation path (the answer to "what does retire mean")

**Decision: remove the write path and the unused API entirely, keep any legacy values visible read-only, and move the Report tab's summary onto Actions.** Exactly:

1. **Delete `app/routers/remediation.py`** and **`app/schemas/remediation.py`** (imported nowhere else). In `app/main.py`, remove `remediation,` from the router import list and the line `app.include_router(remediation.router)`. After this, no route path contains `/gap-items/` or `remediation-summary`.
2. **`partials/remediation_panel.html` becomes a read-only legacy record.** Replace its whole content with a block rendered **only** when the `GapItem` carries non-default legacy data: `item.remediation_owner or item.remediation_target_date or item.remediation_notes or item.remediation_closed_at or (item.remediation_status and item.remediation_status != 'open')`. It is a `<div data-legacy-remediation …>` showing "Legacy remediation record (read-only)", the status (`replace('_', ' ')|title`), owner, target date (`%Y-%m-%d`), closed-at date, notes, and a link `<a href="/assessments/{{ assessment_id }}/findings">Track remediation on the Findings and actions page →</a>`. **No `<form`, `<button`, `hx-*` attribute or `<select`.** Its include in `report_summary.html` is unchanged.
3. **`partials/remediation_summary.html` is rewritten over Action counts.** `web.report_summary` drops the `applicable_gap_items`/`GapItem` `remediation_counts` block and instead sets `remediation_counts = remediation_rollup.assessment_action_counts(db, assessment_id)` (D-P3-4-L; keys `ROLLUP_KEYS`), passed in the context under the same name. The partial shows, when `remediation_counts.total > 0`: the heading "Remediation Progress", the text `{{ remediation_counts.verified }} of {{ remediation_counts.total }} actions closed and verified`, a stacked bar and legend with **Verified**, **Awaiting verification**, **In progress** and **Open**, `Overdue: {{ remediation_counts.overdue }}`, and a link "Findings and actions →" to `/assessments/{{ assessment_id }}/findings`. Otherwise, the single line "No remediation actions yet." followed by the same link. No `accepted_risk` key and no `GapItem` read.
4. **`tests/test_analysis_pipeline.py`**: remove the line `"app/routers/remediation.py",` from `test_legacy_consumers_do_not_read_the_new_tables`'s `files` list (the file no longer exists, and `grep` on a missing file writes only to stderr, which would make the entry a silent no-op). Nothing else in that file changes.
5. **No data migration for pipeline-owned assessments' `GapItem` remediation values.** Legacy assessments are already migrated to Findings/Actions by `scripts/migrate_legacy.py` (P1-3, with P3-1's re-run fix), which is **unchanged**. For assessments owned by the pipeline, no automatic conversion happens, for three reasons: every re-run already archives and replaces `GapItem`s, so their live remediation values are post-run scratch data; a Finding requires an individually approved Conclusion (D-P3-1-B), and converting `GapItem` rows would bypass that; and item 2 keeps any such values visible, so the consultant can re-enter them as Actions. `GapItem` columns, values and `legacy_history` are never modified or removed (no schema change).
6. **Out of scope and unchanged:** the Report tab's `GapItem`-sourced "Critical Findings" and "Detailed Findings" blocks (that is the reader migration, P2-3 open question 1), and `scripts/migrate_legacy.py`.

**Why delete the routes rather than redirect or keep them read-only:** no template or test calls them (Current state). A live PATCH that edits `GapItem` remediation is a second source of truth that diverges from Actions, and PR-051's append-only history can't hold on it. A redirect would keep a dead URL alive for no caller. Keeping the **values** visible (item 2) removes the one real risk of deletion, which is hiding a consultant's earlier notes.

### D-P3-4-L. The engagement rollup: `app/services/remediation_rollup.py` and `/engagements/{engagement_id}/remediation`

New read-only module. Docstring: `"""Read-only remediation rollup (P3-4): Action counts and lists across an engagement's assessments, each row keeping its assessment, framework and requirement. Counts only; never a score. Never writes."""` It never writes (no `db.add(`, `.flush(`, `.commit(`) and names its Session `db`.

```python
ROLLUP_KEYS = ("open", "in_progress", "awaiting_verification", "verified", "overdue", "unassigned", "total")
ACTIVE_STATUSES = ("open", "in_progress")
UNASSIGNED_LABEL = "Unassigned"

@dataclass(frozen=True)
class TrackedAction:
    action_id: str
    title: str
    owner_display: str            # owner, or UNASSIGNED_LABEL
    target_date: date | None
    status: str
    status_label: str             # findings.ACTION_STATUS_LABELS
    overdue: bool
    finding_id: str
    finding_title: str
    severity: str
    assessment_id: str
    assessment_label: str         # f"{a.description or a.company_name} ({a.created_at:%d %b %Y})"
    framework_id: str | None      # from the Finding's Conclusion; None if missing
    requirement_id: str | None
    href: str                     # f"/assessments/{assessment_id}/findings#finding-{finding_id}"

@dataclass(frozen=True)
class AssessmentRollup:
    assessment_id: str
    label: str
    findings_href: str            # f"/assessments/{assessment_id}/findings"
    counts: dict[str, int]        # exactly ROLLUP_KEYS

@dataclass(frozen=True)
class EngagementRollup:
    counts: dict[str, int]                 # exactly ROLLUP_KEYS, over every Action in scope
    by_severity: list[dict]                # D below
    by_owner: list[dict]
    assessments: list[AssessmentRollup]    # every in-scope assessment, created_at then id; zero counts included
    overdue: list[TrackedAction]           # overdue Actions, target_date then action_id
    awaiting_verification: list[TrackedAction]   # status "closed", Action.updated_at then action_id

def assessment_action_counts(db: Session, assessment_id: str, *, today: date | None = None) -> dict[str, int]: ...
def engagement_rollup(db: Session, engagement: Engagement, *, today: date | None = None) -> EngagementRollup: ...
```

- **Scope:** the engagement's assessments with `status != "archived"` (the `engagement_detail` filter), their Findings, those Findings' Actions, and the Findings' Conclusions (`id`, `framework_id`, `requirement_id` only). Four SELECTs. `assessment_action_counts` runs the same logic for one assessment.
- **Counts (per Action):** `open`, `in_progress`, `awaiting_verification` (= `closed`) and `verified` by status; `overdue` = `target_date` is set **and** `target_date.date() < today` **and** status in `ACTIVE_STATUSES`; `unassigned` = `owner` is NULL **and** status in `ACTIVE_STATUSES`; `total` = all Actions. `today` defaults to `datetime.now(timezone.utc).date()`. (SQLite returns naive datetimes, so compare `.date()` values, never datetimes.)
- **`by_severity`:** one dict per severity in `conclusion_review.RISK_LEVELS` order, **always all four** (zeros included), then any other `Finding.severity` value found, sorted. Keys exactly `severity`, `open`, `in_progress`, `awaiting_verification`, `verified`, `total`.
- **`by_owner`:** one dict per distinct owner (`owner.strip()`, case-sensitive; NULL → `UNASSIGNED_LABEL`) with at least one Action in `ACTIVE_STATUSES`. Keys exactly `owner`, `active`, `overdue`. Sorted by `(-overdue, -active, owner)`.
- **No score, percentage of compliance, or cross-framework number** is computed. Counts are Action counts, and the page says so. Every listed Action names its assessment, framework and requirement (PR-050).

**Page `pages/remediation_tracker.html`** (extends `base.html`; context `engagement`, `client`, `rollup`, `today`):
- `{% block title %}Remediation tracker — {{ engagement.name }}{% endblock %}`; breadcrumb `Portfolio / {{ client.name }} / {{ engagement.name }} / Remediation tracker`;
- `<h1>` "Remediation tracker"; subtitle "Actions across every assessment in this engagement. These are action counts, not compliance scores. Each action keeps its assessment, framework and requirement.";
- a counts grid `<p data-rollup-count="{{ key }}">` for each of `ROLLUP_KEYS`, labelled Open, In progress, Awaiting verification, Verified, Overdue, Unassigned, Total;
- "By severity": `<tr data-severity-row="{{ row.severity }}">` per row;
- "By owner (active actions)": `<tr data-owner-row>` per row, or "No active actions.";
- "By assessment": `<tr data-assessment-row id="assessment-{{ row.assessment_id }}">` with the label, the seven counts and a "Findings and actions →" link to `row.findings_href`;
- "Overdue actions": `<li data-overdue-action>` per item (title, owner, target date `%Y-%m-%d`, status label, finding title, `framework_id|upper`, `requirement_id`, the assessment label and a link to `href`), or "No overdue actions.";
- "Awaiting verification": `<li data-awaiting-action>` per item, same fields, or "Nothing is awaiting verification.";
- when `rollup.counts.total == 0`: "No actions in this engagement yet." above the grid.

**The page is read-only**: no `<form`, no `hx-post`/`hx-put`/`hx-patch`/`hx-delete`, no `|safe`. Verification happens on the Findings page, which every row links to.

`web.remediation_tracker_page`: `db.get(Engagement, …)` → 404 "Engagement not found"; `db.get(Client, engagement.client_id)` → 404 "Client not found"; `rollup = remediation_rollup.engagement_rollup(db, engagement)`; never commits. Import `from app.services import remediation_rollup`.

**Links (additive only):**
- `pages/engagement_detail.html`: directly after the `<p class="mt-2 text-sm text-gray-500 dark:text-gray-400">{{ client.name }} · …</p>` line, add `<a href="/engagements/{{ engagement.id }}/remediation" class="mt-2 inline-block text-sm font-medium text-brand dark:text-navy-300 hover:underline">Remediation tracker →</a>`.
- `pages/findings.html`: after its "Workpaper (read-only trace) →" link, add `{% if assessment.engagement_id %}<a href="/engagements/{{ assessment.engagement_id }}/remediation" class="text-sm font-medium text-brand dark:text-navy-300 hover:underline">Engagement remediation tracker →</a>{% endif %}`.

### D-P3-4-M. `components/finding_card.html`: what changes

Per Action row (inside `data-action-row`), additively. Keep every existing attribute, form and text, including "Closed and verified actions cannot be changed here." when `not row.editable`.
- Replace `Status: {{ row.action.status }}` with `Status: {{ row.status_label }}`. The `data-action-status` attribute still holds the raw value.
- In each history `<li>`, when `e.evidence`: `Evidence: <a href="/evidence/{{ e.evidence.evidence_id }}">{{ e.evidence.filename }}</a> v{{ e.evidence.version_number }} (SHA-256 {{ e.evidence.sha256[:12] }})`.
- When `row.closable`: `<details data-close-control>` with summary "Close with evidence". Inside, when `view.closure_options`: `<form hx-post="/api/assessments/{{ assessment.id }}/findings/{{ view.finding.id }}/actions/{{ row.action.id }}/close" hx-target="#finding-{{ view.finding.id }}" hx-swap="outerHTML" hx-include="#reviewer-name">` with hidden `expected_history_length` (`row.history_length`), `<select name="evidence_version_id">` whose first option is `<option value="">Choose closure evidence</option>` followed by one option per `view.closure_options` entry (value `evidence_version_id`, text `label`), a `notes` textarea, and submit "Close action". Otherwise the text "Upload closure evidence to this assessment first." with a link to `/assessments/{{ assessment.id }}`.
- When `row.verifiable`: "Closure evidence: {{ filename }} v{{ version_number }}" linked to `/evidence/{{ evidence_id }}`, then `<form data-verify-control hx-post="…/actions/{{ row.action.id }}/verify" …>` (same `hx-*`) with hidden `expected_history_length`, `notes`, and submit "Verify closure".
- When `row.legacy_closure`: the text "Closed without closure evidence (legacy). Reopen it to close it again with evidence."
- When `row.reopenable`: `<details data-reopen-control>` with summary "Reopen", a form posting to `…/reopen` (same `hx-*`) with hidden `expected_history_length`, a `notes` textarea with the `required` attribute and placeholder "Reason for reopening", and submit "Reopen action".
- In the card header, replace `Status: {{ view.finding.status }}` with `Status: {{ view.status_label }}`.

Everything autoescaped. **Never `|safe`**. **Never the `multiple` attribute** on the `<select>` (P3-1 scenario 11's regex).

### D-P3-4-N. Consistency audit of this spec (the P2-4 lesson, done in advance)

P2-4's handoff mandated a field name its own grep forbade. Every mandated string, identifier, path and label here has been checked against every structural assertion below and in the existing suite:

1. **The three existing assertions that must change, and exactly how.** They are forced by binding decisions, not by preference:
   - `tests/test_findings.py::test_scenario_4_action_state_machine`: replace the `ACTION_TRANSITIONS` literal with the D-P3-4-B table. **Nothing else in that test changes.** Its parametrized generic-route cases still hold: `closed`/`verified` targets on `…/status` still return `CLOSURE_RESERVED` (compared through the constant, whose text changes), same-status and `open ⇄ in_progress` are unchanged. The P3-1 hand-forward requires extending this table, so the literal can't stay.
   - `tests/test_findings.py::test_scenario_11_structural_guards`: add exactly the three D-P3-4-I tuples to `expected`. **Nothing else changes.** The new paths contain `/findings` by design (D-P3-4-I).
   - `tests/test_analysis_pipeline.py::test_legacy_consumers_do_not_read_the_new_tables`: remove the one deleted path (D-P3-4-K item 4).

   **No other existing test file or assertion is modified.** If any other existing test fails, stop and report it.
2. **P3-1 terminal-state assertions still hold.** A `closed` Action gets `TERMINAL` for every target on `…/status` and on `…/update` (the check order is unchanged). The card still shows "Closed and verified actions cannot be changed here." when `not row.editable`. The page text after `id="action-{id}"` contains `/verify` and `/reopen` paths but **no** `actions/{id}/status`, because `allowed_statuses` is `()` for closure statuses. P3-1 scenario 9's migrated closed Action behaves the same way.
3. **The `delete` guard** (service and router source, lower-cased, comments included). None of the mandated messages, labels, identifiers or docstrings contains "delete". Say "reopen", "superseded" or "removed" in comments. `remediation_rollup.py` has the same rule (scenario 11).
4. **The P3-1 regex** `select all|create all|all conclusions|type="checkbox"|\bmultiple\b|\|\s*safe\b` over the service, router, schema, `pages/findings.html` and `components/finding_card.html`. Checked against every mandated string: "Choose closure evidence", "Upload closure evidence to this assessment first.", "Close with evidence", "Close action", "Verify closure", "Reopen action", "Reason for reopening", "Closed without closure evidence (legacy)…", "Engagement remediation tracker →", all messages in D-P3-4-J. **None matches.** `<select name="evidence_version_id">` doesn't match `select all`. Don't use the word "multiple" in comments or docstrings of those files.
5. **Service guards:** `.commit(`, `swap_conclusion` and `ConclusionRevision(` stay absent from `findings.py`. The new imports are `Evidence`, `EvidenceVersion` and the evidence service module, none of which matches.
6. **Route-set guards.** The three new paths contain `/findings` and none of `/conclusions`, `/workpaper`, `/snapshots`. `/engagements/{engagement_id}/remediation` contains none of `/findings`, `/conclusions`, `/workpaper`, `/snapshots`, `/integrated-reports`. This task's own guards pin the `/findings` set (eight routes) and the `/remediation` set (exactly `{("GET", "/engagements/{engagement_id}/remediation")}`).
7. **Legacy-consumer grep.** After removing the deleted path, the list still covers `scoring.py`, `review.py`, `reports.py` and `pdf_export.py`, none of which this task edits. `remediation_rollup.py` reads `Conclusion` and is intentionally not on that list.
8. **Label substrings vs text assertions.** The label "Closed and verified" is a substring of "Closed and verified actions cannot be changed here.". **Tests never count or negate "Closed and verified"**; they use `data-action-status` and `data-*` controls. "Closed, awaiting verification" contains only a comma. No mandated HTML text contains `&`, `<`, `>` or quotes.
9. **Counted attributes.** `data-close-control`, `data-verify-control`, `data-reopen-control`, `data-legacy-remediation`, `data-rollup-count`, `data-severity-row`, `data-owner-row`, `data-assessment-row`, `data-overdue-action` and `data-awaiting-action` don't contain one another, nor `data-action-row`, `data-action-history`, `data-history-action` or `data-finding-card`.
10. **Template guards.** No `overall_score` and no `CyberAssess` in any new or changed template. `remediation_panel.html` and `remediation_tracker.html` contain no `<form`, `hx-post`, `hx-patch`, `hx-put`, `hx-delete` or `|safe` (scenario 11).
11. **Actor prefix.** The raw `consultant:` prefix is never rendered (history `actor_display` strips it, as today).
12. **Workpaper.** `app/services/workpaper.py` is not modified. The workpaper's Finding links show the derived `status`, and P2-6 and P3-1's workpaper assertions compare against the fresh row, so they are unaffected.

## Required approach

### 1. `app/schemas/findings.py`: the three new schemas (D-P3-4-I)

### 2. `app/services/findings.py`: D-P3-4-B … J

### 3. `app/routers/findings.py`: the three routes (D-P3-4-I)

### 4. `app/services/remediation_rollup.py` (new): D-P3-4-L

### 5. `app/routers/web.py`

- Add `remediation_tracker_page` directly after `engagement_detail` (D-P3-4-L).
- In `report_summary`, replace the `applicable_gap_items`/`remediation_counts` block with the `assessment_action_counts` call (D-P3-4-K item 3).
- Import `from app.services import remediation_rollup`.

### 6. Retirement: D-P3-4-K items 1–4 exactly

### 7. Templates

- `components/finding_card.html` (D-P3-4-M).
- `pages/remediation_tracker.html` (new), and the links in `pages/engagement_detail.html` and `pages/findings.html` (D-P3-4-L).
- `partials/remediation_panel.html` and `partials/remediation_summary.html` (D-P3-4-K).

### 8. The three existing-test edits (D-P3-4-N item 1), and nothing else in existing tests

### 9. `tasks/todo.md`

Update the P3-4 line with its status and a link to this handoff's Results. If the P3-2 line still says "PR #31, open, not yet merged", change it to "**Merged: PR #31.**" (P3-3 may already have done so).

### 10. `tests/test_remediation_tracking.py` (new)

Copy (don't import) from `tests/test_findings.py`: the Alembic-built `db_path` / `engine` / `db` fixtures, `http`, `gate`, `_register_frameworks`, `REQS`, `_seed`, `_item`, `_stub_single`, `_run_one`, `_revisions`, `_url`, `_decide`, `_approve`, `_create`, `_history`, `_created_finding`, `_counts`, `_action_snapshot`, `_nothing_snapshot`, `_gap_item_kwargs` and `_seed_legacy_assessment`. From `tests/test_report_snapshots.py`: the autouse `upload_root` fixture (**no test may write under the real `uploads/`**). Extend `_seed` with an `engagement=` keyword so several assessments can share one engagement.

Helpers:
- `_closure_evidence(db, assessment, *, name="closure.txt", text_value="Signed closure memo")`: `evidence_service.ingest_upload(db, assessment_id=assessment.id, filename=name, content=text_value.encode(), category=None)`, returning `(evidence, version)`. Real ingestion, so the blob exists and `verify_version` is meaningful. Give every upload in a test distinct content: P2-1 refuses duplicate content (`DuplicateEvidence`) for blocking statuses.
- `_post(http, assessment, finding, action, step, **data)`: posts to `…/actions/{action.id}/{step}` with `reviewer_name="Priya"` unless overridden, and `expected_history_length` read fresh from the DB unless given.

Produce Conclusions, approvals and Findings through the real pipeline and the real P2-4/P3-1 routes. Hand-set rows are allowed only for: the migrated-closed shape (through `run_migration`), `target_date`/`owner` values used by the rollup, `Evidence.status`/`EvidenceVersion.status` changes and blob tampering in scenario 4, and `Finding.status = "accepted_risk"` in scenario 6. Every scenario is one or more test functions whose docstrings start with `Scenario N:`.

## Key files

| File | Why it matters |
|---|---|
| `app/services/findings.py` | State machine, close/verify/reopen, derived Finding status, read-model fields (D-P3-4-B … J). |
| `app/routers/findings.py`, `app/schemas/findings.py` | Three routes and schemas (D-P3-4-I). |
| `app/services/remediation_rollup.py` (new) | Rollup read model (D-P3-4-L). |
| `app/routers/web.py`, `pages/remediation_tracker.html` (new), `pages/engagement_detail.html`, `pages/findings.html` | Tracker page and links (D-P3-4-L). |
| `components/finding_card.html` | Close/verify/reopen controls and evidence display (D-P3-4-M). |
| `app/routers/remediation.py`, `app/schemas/remediation.py` | **Deleted** (D-P3-4-K). |
| `app/main.py`, `partials/remediation_panel.html`, `partials/remediation_summary.html` | Retirement (D-P3-4-K). |
| `tests/test_findings.py`, `tests/test_analysis_pipeline.py` | The three mandated assertion edits only (D-P3-4-N item 1). |
| `app/services/evidence.py`, `conclusion_review.py`, `workpaper.py`, `scripts/migrate_legacy.py`, `app/utils/pdf_export.py`, `app/routers/reports.py`, `app/static/js/app.js`, `app/models/*`, `alembic/versions/*` | **Not modified.** No schema change. |
| `tests/test_remediation_tracking.py` (new) | The contract. |

## Non-goals

- **No schema change and no Alembic revision.** No `blocked` or Action-level `accepted_risk` status, no Finding history column, no closure table (D2).
- **No new way to record `accepted_risk`** (open question 3). No Finding editing or dismissal.
- No `EvidenceUse` for closure evidence (D-P3-4-C), and no new upload route.
- No separation-of-duties enforcement between closer and verifier (open question 2).
- No PDF change (P3-3 owns `pdf_export.py`; closure evidence in the PDF is its open question 4).
- No change to the Report tab's `GapItem` findings blocks, the portfolio dashboard, `scripts/migrate_legacy.py` or `app.js`. No `relationship()`. No `audit_events` for Action changes.
- No client-facing remediation surface (PRD: "client-managed actions are not exposed").

## Test scenarios

All in `tests/test_remediation_tracking.py`. "Nothing written" means `_nothing_snapshot(db)` (counts of `findings`, `actions`, `audit_events`, `conclusion_revisions`; every Action's `(id, status, title, owner, target_date, history_json, updated_at)`; every Conclusion's `(id, version, updated_at)`) **plus** every Finding's `(id, status)` is unchanged.

1. **The plan's test: full lifecycle, finding → action → update → close → verify, closure in history.**
   - `_created_finding` (approved `non_compliant` Conclusion, Finding with its first Action). `POST …/status in_progress` (200). `POST …/update owner=Asha target_date=2026-12-31` (200). `_closure_evidence`. `POST …/close evidence_version_id=<v.id> notes="Client sent memo"` → 200; the body contains `data-action-status="closed"`, "Closed, awaiting verification" and `data-verify-control`.
   - `POST …/verify` → 200; `data-action-status="verified"`.
   - `_history` actions are `["created", "status_changed", "updated", "closed", "verified"]`. The `closed` and `verified` entries have key set `== set(CLOSURE_HISTORY_KEYS)`; every other entry `== set(HISTORY_KEYS)`. The `closed` entry's `changes == {"status": {"from": "in_progress", "to": "closed"}}`, `notes == "Client sent memo"` and `evidence == {"evidence_id": ev.id, "evidence_version_id": v.id, "version_number": 1, "sha256": v.file_hash_sha256, "filename": "closure.txt"}`. The `verified` entry's `changes == {"status": {"from": "closed", "to": "verified"}}` and its `evidence` equals the closed entry's. Both actors are `"consultant:Priya"`, and every timestamp is timezone-aware.
   - Finding status goes `open` → `in_progress` (after the first status change) → `in_progress` (after close) → `resolved` (after verify).
   - Every successful step leaves `history[:-1]` equal to the pre-request history.
   - The page shows "Closure verified", "Closed with evidence", `href="/evidence/{ev.id}"` and `"consultant:Priya" not in page`.
2. **State machine (D-P3-4-B).**
   - Constants exactly: `ACTION_TRANSITIONS`, `GENERIC_STATUS_TARGETS`, `CLOSURE_STATUSES`, `ACTION_STATUS_LABELS`, `CLOSURE_HISTORY_KEYS`, `EVIDENCE_KEYS`, `HISTORY_ACTIONS`.
   - For every `(current, step)` in `{open, in_progress, closed, verified} × {close, verify, reopen}` (set `action.status` directly and give a closed-shape history where the step needs one): `close` succeeds only from `open`/`in_progress`, `verify` only from `closed` with evidence on record, `reopen` only from `closed`/`verified` (with notes). Every refusal returns 400 with the exact D-P3-4-J message and writes nothing.
   - The generic `…/status` route with `closed` or `verified` still returns `CLOSURE_RESERVED`, and with a closed current status returns `TERMINAL`.
   - `open` → `closed` directly (no `in_progress`) → 200.
3. **Closure evidence rules (D-P3-4-C).** Each writes nothing and returns 400:
   - blank `evidence_version_id` → `CLOSURE_EVIDENCE_REQUIRED`;
   - an unknown id → `CLOSURE_EVIDENCE_INVALID`;
   - evidence uploaded to **another assessment** (another engagement) → `CLOSURE_EVIDENCE_INVALID`;
   - a superseded version (upload a new version with `ingest_new_version` first, then post the old version's id) → `CLOSURE_EVIDENCE_INVALID`;
   - a version whose blob was overwritten on disk (test-only `write_bytes`) → `CLOSURE_EVIDENCE_INVALID`;
   - evidence whose `Evidence.status` was set to `invalidated` → `CLOSURE_EVIDENCE_INVALID`.
   - Positive: `EvidenceUse`-mapped evidence from the same engagement (mapped into this assessment with `evidence_service.map_evidence`) → 200.
   - No `evidence_uses` row is created by a close (count unchanged).
4. **Verification re-checks evidence (D-P3-4-D).** After a successful close:
   - tamper with the blob → verify 400 `CLOSURE_EVIDENCE_CHANGED`, nothing written;
   - on a fresh closure, set `Evidence.status = "archived"` → `CLOSURE_EVIDENCE_CHANGED`;
   - on a fresh closure, upload a **new version** of the closure evidence (the attached one becomes `superseded`) → verify **200**, and the `verified` entry's `evidence` still names the original version.
   - The same actor closing and verifying is allowed (200), and both entries are present.
5. **Reopen (D-P3-4-E).**
   - Reopen a `verified` Action with notes "Regression found" → 200; status `in_progress`; history ends `["closed", "verified", "reopened"]`, and the earlier entries are byte-for-byte unchanged. The Finding goes `resolved` → `in_progress`.
   - Blank notes → 400 `REOPEN_REASON_REQUIRED`, nothing written.
   - After a reopen, `verify` → 400 `NOT_VERIFIABLE`. A second `close` with evidence, then `verify` → 200. `closure_on_record` returns the **newer** closed entry's evidence.
6. **Finding status derivation (D-P3-4-G).**
   - Two Actions: verify one, leave one `open` → Finding `in_progress`; verify both → `resolved`; `POST …/actions` (add a third) → `in_progress`.
   - `create_finding` → `open` (P3-1 unchanged). `update_action` doesn't change the Finding status.
   - A Finding hand-set to `accepted_risk` keeps `accepted_risk` through a status change, a close and a verify.
   - `findings_page` exposes `status_label` "Resolved" and the card header shows `Status: Resolved`.
7. **Migrated legacy closed Actions are not grandfathered (D-P3-4-F).**
   - `_seed_legacy_assessment` with one closed `GapItem` (`remediation_status="closed"`, `remediation_closed_at` set), then `run_migration(db)`. The page shows "Closed without closure evidence (legacy)", a `data-reopen-control`, and neither `data-verify-control` nor `actions/{id}/status` in that Action's slice.
   - `verify` → 400 `LEGACY_CLOSURE`, nothing written.
   - `run_migration` links the legacy assessment to its new engagement (`assessment.engagement_id` is set), so `_closure_evidence` works on it after `db.refresh(assessment)`. Reopen (notes "No evidence on file") → close with evidence → verify → 200. History is `["imported", "reopened", "closed", "verified"]`, and the `imported` entry is byte-for-byte the migrated one (four keys).
   - `run_migration(db)` again → `stats.findings == stats.actions == 0`.
8. **Concurrency (append-only, P3-1 D-P3-1-F carried forward).**
   - A stale `expected_history_length` on `close`, `verify` and `reopen` → 409 `STALE_ACTION`, nothing written.
   - CAS race on `close`: monkeypatch `app.services.findings.load_history` to append a fabricated entry to the row behind the service's back (the P3-1 scenario 5(b) pattern). `close` → 409; after the router's rollback, `history_json` equals the original raw string and the Finding status is unchanged.
   - Unreadable history (`"not json"`) → close 400 `UNREADABLE_HISTORY`, and the page renders "History could not be read." with no close, verify or reopen control for that row.
9. **Retirement of the `GapItem` remediation path (D-P3-4-K).**
   - `app/routers/remediation.py` and `app/schemas/remediation.py` don't exist. No app route path contains `/gap-items/` or `remediation-summary`. `PATCH /api/assessments/{id}/gap-items/{item_id}/remediation` → 404 or 405.
   - `partials/remediation_panel.html` doesn't match `<form|<button|<select|hx-` (case-insensitive).
   - The report summary (`GET /assessments/{id}/report-summary`) for an assessment whose `GapItem` has `remediation_owner="owner@example.com"` and `remediation_notes="Legacy note"` contains `data-legacy-remediation`, "Legacy remediation record (read-only)", "owner@example.com" and "Legacy note". A default `GapItem` (status `open`, nothing else) renders no `data-legacy-remediation`.
   - With two Actions (one verified, one open), the report summary contains "Remediation Progress" and "1 of 2 actions closed and verified", and `href="/assessments/{id}/findings"`. With no Actions it contains "No remediation actions yet.".
   - `GapItem` rows' remediation columns are unchanged by every request in this scenario.
10. **Engagement rollup (D-P3-4-L).**
    - One engagement, two assessments (A: two Findings, B: one Finding), plus an **archived** assessment with a Finding (excluded), and another engagement's assessment (excluded). Actions: A has `open` (owner "Asha", target yesterday → overdue), `in_progress` (no owner → unassigned), `closed` (with evidence), `verified`; B has `open` (owner "Asha", target tomorrow). Use `today=` for determinism.
    - `engagement_rollup(db, engagement, today=…)`: `counts == {"open": 2, "in_progress": 1, "awaiting_verification": 1, "verified": 1, "overdue": 1, "unassigned": 1, "total": 5}`; `by_severity` has all four `RISK_LEVELS` rows in order with the exact per-status numbers for the seeded severities; `by_owner == [{"owner": "Asha", "active": 2, "overdue": 1}, {"owner": "Unassigned", "active": 1, "overdue": 0}]`; `assessments` is A then B with exact counts; `overdue` is the one A Action with its `framework_id`, `requirement_id`, assessment label and `href`; `awaiting_verification` is the closed Action.
    - `assessment_action_counts(db, A.id, today=…)` equals A's `AssessmentRollup.counts`.
    - `GET /engagements/{e}/remediation` → 200: each `data-rollup-count` cell shows its number; `data-severity-row` count 4; `data-owner-row` count 2; `data-assessment-row` count 2; `data-overdue-action` count 1; `data-awaiting-action` count 1; the overdue item links to `/assessments/{A.id}/findings#finding-{fid}`; "not compliance scores" is in the page; `"consultant:"` is not.
    - An empty engagement shows "No actions in this engagement yet.". An unknown engagement → 404.
    - `GET /engagements/{e}` contains `href="/engagements/{e}/remediation"`, and the Findings page of an engaged assessment contains the same href.
    - Escaping: an owner `<script>x</script>` renders as `&lt;script&gt;x&lt;/script&gt;`.
11. **Structural guards.**
    - The `/findings` route set is exactly P3-1's five plus the three D-P3-4-I routes. The set of routes containing `/remediation` is exactly `{("GET", "/engagements/{engagement_id}/remediation")}`.
    - `"delete" not in` the lower-cased source of `app/services/findings.py`, `app/routers/findings.py` and `app/services/remediation_rollup.py`. The rollup module contains none of `db.add(`, `.flush(`, `.commit(`. `inspect.getsource(web.remediation_tracker_page)` has no `.commit(`.
    - `pages/remediation_tracker.html` and `partials/remediation_panel.html` don't match `<form|hx-post|hx-put|hx-patch|hx-delete|\|\s*safe\b|overall_score|CyberAssess`.
    - The P3-1 regex (D-P3-4-N item 4) matches nothing in its five files, **and** `CLOSURE_RESERVED`, `LEGACY_CLOSURE` and "Closed without closure evidence (legacy)" are present (the mandated strings survive the guard).
    - `inspect.signature(findings.close_action)` has `evidence_version_id`, and no parameter annotation contains `list`.
12. **Nothing else moved.** `tests/test_findings.py` (with only its two mandated edits), `tests/test_analysis_pipeline.py` (with only its one mandated edit), `tests/test_migrate_legacy.py`, `tests/test_workpaper.py`, `tests/test_conclusion_approval.py`, `tests/test_report_snapshots.py`, `tests/test_evidence_service.py`, `tests/test_white_label.py` and `tests/test_no_blended_scoring.py` pass (the full-suite run).

## Done criteria

- `tests/test_remediation_tracking.py` passes. `.venv/bin/pytest -q` passes in full: **477 + N**, where N is the number of new cases (if P3-3 merged first, its count is included in the baseline; state the baseline you measured). (In a fresh `git worktree`, expect the known one-time `_guard_dev_database_untouched` teardown error described in the P2-3 handoff; nothing else.)
- `git diff main -- tests/` shows **only** the new file plus the three D-P3-4-N item 1 edits.
- `git diff --stat main` shows changes **only** in: `app/services/findings.py`, `app/routers/findings.py`, `app/schemas/findings.py`, `app/services/remediation_rollup.py` (new), `app/routers/web.py`, `app/main.py`, `app/routers/remediation.py` (deleted), `app/schemas/remediation.py` (deleted), `app/templates/components/finding_card.html`, `app/templates/pages/findings.html`, `app/templates/pages/engagement_detail.html`, `app/templates/pages/remediation_tracker.html` (new), `app/templates/partials/remediation_panel.html`, `app/templates/partials/remediation_summary.html`, `tests/test_remediation_tracking.py` (new), `tests/test_findings.py`, `tests/test_analysis_pipeline.py`, `tasks/todo.md` and this handoff.
- `git diff --stat main -- app/services/evidence.py app/services/conclusion_review.py app/services/workpaper.py scripts/migrate_legacy.py app/utils/pdf_export.py app/routers/reports.py app/static/js/app.js app/models alembic/versions` is empty. `alembic heads` is still exactly `4e8c1a9d2b57`. `grep -rn "relationship(" app/models/` is empty.
- **Smoke test** (per the project rule; record the outputs). A fresh Alembic-built DB (or a **copy** of the dev DB) and a temporary `upload_dir`, with the in-process ASGI `TestClient` if a socket bind is refused. Patch `app.routers.analysis.run_gap_analysis` to fixed items. Then:
  1. Two assessments in one engagement. Approve gap Conclusions and create three Findings through the P3-1 route.
  2. Upload closure evidence through the real assessment evidence upload route. Take one Action through `in_progress → close → verify`, another through `close → verify → reopen → close → verify`, and leave one open with a past target date.
  3. Paste `SELECT a.title, a.status, a.history_json FROM actions a JOIN findings f ON f.id = a.finding_id` and `SELECT title, status FROM findings`.
  4. `GET /engagements/{e}/remediation` → paste the `data-rollup-count` values and the overdue list.
  5. `GET /assessments/{id}/report-summary` → confirm "Remediation Progress" reflects Actions; confirm `PATCH /api/assessments/{id}/gap-items/{item}/remediation` is gone.
  6. On a copy of a legacy DB (or a seeded legacy assessment), run `scripts/migrate_legacy.py`, then confirm a migrated closed Action shows the legacy note and can be reopened, closed with evidence and verified.
  7. **Browser check**, if a browser is available: close an Action with evidence from the card, verify it, and open the tracker. If no browser is available, say so in Results. Do not claim it.

## Rollback

- **Code:** `git revert`. No schema change. `closed`/`verified`/`reopened` history entries remain valid JSON that the reverted P3-1 reader shows with their raw action names (its readers use `.get`), and `verified`/`closed` rows become terminal again under P3-1's rules. Derived Finding statuses stay as written; the reverted app displays them and never changes them. The legacy PATCH route and summary return with the revert; `GapItem` data was never modified, so they resume where they stopped.
- **Data:** nothing deletes or rewrites. History is append-only (CAS on the exact prior content). To undo a mistaken close or verify, **reopen** it with a reason; that is itself recorded.

## Open questions (deliberately flagged, not resolved here)

1. **`Blocked` and Action-level `Accepted risk`** (PRD Action states) have no stored status. Adding them is a Claude-owned schema/vocabulary change; `migrate_legacy.ACTION_STATUSES` and P3-1's equality assertion would move with it.
2. **Separation of duties** between closer and verifier. The PRD allows one consultant to do both in v1. With real auth (post-MVP), a policy could require a different verifier; the history already records both actors.
3. **Recording risk acceptance.** `accepted_risk` is a Finding-level judgment with no history column. A design is needed for where the reason and the approver live (an `audit_events` row per acceptance, or a Finding history column), whether it requires an approved Conclusion, and how it reads in reports. Until then, P3-4 preserves migrated `accepted_risk` values and never writes new ones. This is a known capability gap versus the retired legacy panel.
4. **One Action addressing several Findings** (PRD relationship rule; P3-1 open question 1). `actions.finding_id` is singular; a join table is a schema change.
5. **Closure evidence expiry.** Verification checks that the evidence is intact and active, not that it is recent or covers the right period. Evidence currency rules (PRD "expiry/currentness") belong with the evidence-reuse work.

## Results

Implemented P3-4 on `codex/p3-4-remediation-tracking`.

- Added evidence-backed `close`, separate evidence re-checking `verify`, reasoned `reopen`, append-only closure history, derived Finding status, stable read-model fields, and the three new Action routes.
- Added the read-only engagement Action rollup and tracker page, Action-based report summary, Findings/engagement links, closure controls, and legacy GapItem read-only display.
- Removed the unused GapItem remediation API/schema and router registration without a schema migration or changes to legacy data.
- Added `tests/test_remediation_tracking.py` with all 12 required scenarios. The focused suite passes **12 passed**.
- The full suite passes **489 passed, 121 warnings**. The measured baseline was **477 passed**, so this is 477 baseline + 12 new contract cases. `alembic heads` remains exactly `4e8c1a9d2b57`.
- Fresh-DB ASGI smoke output: `SMOKE_SQL_ACTIONS [('Open action', 'open', 2), ('Reopenable action', 'verified', 6), ('Smoke action', 'verified', 3), ('Smoke action', 'open', 1)]`; `SMOKE_SQL_FINDINGS [('Finding Smoke A', 'in_progress'), ('Finding Smoke B', 'open')]`; tracker `GET` returned 200 with rollup counts `open=2`, `in_progress=0`, `awaiting_verification=0`, `verified=2`, `overdue=1`, `unassigned=2`, `total=4`, and one overdue row; report summary `GET` returned 200 and rendered `Remediation Progress`; the retired GapItem PATCH returned 404. The same smoke exercised two assessments in one engagement, real assessment evidence uploads, close/verify, reopen/close/verify, and a past target date.
- No browser tool was available in this session, so browser verification was not claimed.

Deviation forced by the current code: the handoff's fixture instructions specify `.txt` evidence, but the existing P2-1 `app/services/evidence.py` rejects `.txt` and its extractor supports only PDF/DOCX/images. The handoff also explicitly forbids changing that file. The new tests therefore use real text-bearing PDF uploads while preserving the production decision, hashing, storage, versioning and integrity checks; no production deviation or other decision change was made.

The requested commits could not be created in this sandbox: the linked worktree's Git index and object database resolve to `/Users/saqlainmomin/dpdpa-gap-tool/.git`, outside the writable workspace, so Git cannot create its lock or object files. No push or PR was attempted.
