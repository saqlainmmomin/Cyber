# P1-4: Portfolio dashboard, hierarchy navigation, and new-engagement flow

**Plan:** `docs/plans/2026-09-21-002-revised-implementation-plan.md`, Phase 1, task P1-4.
**Owner:** Codex, from a Claude handoff (per `tasks/agent-ownership.md` — "mechanical, fully spec-able, contained": CRUD routes and templates against an already-merged column spec, with every derived value and route path pinned down below).
**Depends on:** P1-2 (`clients`, `engagements`, `assessment_packs` tables) — **merged**. P1-3 (`scripts/migrate_legacy.py`, which backfills `assessments.engagement_id`) — **PR #19, implemented, awaiting merge**. Start against fixture data; the dashboard must not require P1-3 to have been *run* (see step 2).
**Blocks:** the later (not-in-Phase-1) task of making `assessments.engagement_id` non-nullable — that task can only land once P1-4 guarantees no new code path creates a NULL-engagement Assessment (step 6 below).

## Goal

Replace the flat assessment list at `GET /` with a Client → Engagement portfolio view, add `client_detail.html` and `engagement_detail.html` pages, and add a "New Engagement" flow that creates `Client` (optionally) + `Engagement` + `Assessment` + one `AssessmentPack` per selected framework in a single POST. After this task, every Assessment created through the UI has a non-null `engagement_id`.

## Current state

Grounded against `main` at `a6d906d` (verify line numbers by symbol name, not by number — they drift).

- **`app/routers/web.py`, `def dashboard`** (currently ~line 84–90): one query — `db.query(Assessment).filter(Assessment.status != "archived").order_by(Assessment.created_at.desc()).all()` — rendered by `pages/dashboard.html` with a single `assessments` context key. This whole route is rewritten.
- **`app/templates/pages/dashboard.html`**: one `<a href="/assessments/{{ a.id }}">` card per assessment, showing `company_name`, `{% include "components/status_badge.html" %}`, industry, `created_at`, `description`; plus an empty state. Tailwind classes carry paired `dark:` variants throughout — match that.
- **`app/templates/components/status_badge.html`**: reads `{% set status = a.status if a is defined else assessment.status %}` and maps `created | documents_uploaded | context_gathered | questionnaire_done | analyzing | completed | error` to colors/labels. It does **not** know about the engagement-derived statuses this task introduces, and must not be edited — P1-4 adds a sibling `components/engagement_status_badge.html` instead.
- **`def new_assessment_page` / `def create_assessment`** (~line 96–163): `GET /assessments/new` renders `pages/new_assessment.html` with `frameworks=_framework_catalog()`; `POST /assessments` (aliased `POST /assessments/new`) reads `company_name`, `industry`, `company_size`, `description` as `Form(...)` plus a multi-valued `selected_frameworks` list pulled off `await request.form()`, validates non-empty and all-ids-in-`ENABLED_ASSESSMENT_FRAMEWORKS`, re-renders the form with `error` + `form_values` at HTTP 400 on failure, then creates a bare `Assessment` and 303-redirects to `/assessments/{id}`. It creates **no** `Client`, `Engagement` or `AssessmentPack` — so it is currently an orphan factory.
- **Models (P1-2, merged).** No SQLAlchemy `relationship()` exists anywhere in this codebase — there is no `assessment.engagement` / `engagement.client` attribute. Every cross-table read in this task is an explicit `db.query(...)` / `db.get(...)`.
  - `Client` (`app/models/client.py`): `id`, `name` (String(255), **unique**), `industry`, `size`, `retention_years` (Integer, default 7), `created_at`, `updated_at`.
  - `Engagement` (`app/models/engagement.py`): `id`, `client_id` (FK → `clients.id`, `ondelete="RESTRICT"`), `name`, `type` (default `"gap_assessment"`), `status` (**non-nullable, no default — must be passed explicitly**), `created_at`, `updated_at`.
  - `AssessmentPack` (`app/models/assessment_pack.py`): `id`, `assessment_id` (FK), `framework_id`, `pack_version`, `created_at`.
  - `Assessment` (`app/models/assessment.py`): `engagement_id` (String(36), FK → `engagements.id`, **nullable**, indexed), `version` (Integer, default 1), `status` (default `"created"`), `selected_frameworks` (Text holding a JSON list, with a `@validates` hook that rejects an empty list and unknown framework ids), plus the `frameworks` property (returns `["dpdpa"]` for NULL/garbage) and `is_multi_framework`.
- **HTMX.** `app/templates/base.html` sets `hx-boost="true"` on `<body>` and loads htmx 2.0.4. **Consequence: every ordinary internal link sends `HX-Request: true` plus `HX-Boosted: true`.** The only existing route that branches on this is `assessment_report_page`, which uses the correct two-header test: `is_htmx = request.headers.get("HX-Request", "").lower() == "true"` and `is_boosted = request.headers.get("HX-Boosted", "").lower() == "true"`, returning a fragment only when `is_htmx and not is_boosted`. Reuse that exact test.
- **Partial conventions** (`app/templates/partials/*.html`): a partial never `{% extends %}` anything, opens with a `{# ... #}` comment naming its expected context (see `partials/remediation_panel.html`), and renders one swappable element. `partials/framework_tabs.html` is the reference for `hx-get` / `hx-target` / `hx-swap="innerHTML"` usage.
- **Status values in use** (grepped from `app/routers/`, `app/services/`): `created`, `scoped`, `documents_uploaded`, `context_gathered`, `questionnaire_done`, `analyzing`, `completed`, `error`, `archived`. Note `scoped` is written by `save_scope` in `web.py` but is **absent from `components/status_badge.html`'s maps** (it falls through to the title-cased default) — a pre-existing cosmetic gap, out of scope here, but the rank table below must include it.

## Required approach

### 1. Derived values — exact definitions

Put all three in a new module `app/services/portfolio.py` (pure functions over already-loaded rows, no DB access, no LLM), so the dashboard, client-detail and engagement-detail routes share one implementation and the tests can call them directly.

```python
STAGE_RANK = {
    "created": 0,
    "scoped": 1,
    "documents_uploaded": 2,
    "context_gathered": 3,
    "questionnaire_done": 4,
    "analyzing": 5,
    "completed": 6,
}
STAGE_RANK_MAX = 6
```

**`derive_status(assessments) -> str`** — `assessments` is the list of that engagement's **non-archived** Assessment rows. Evaluate in this order, first match wins:
1. empty list → `"empty"`
2. any `status == "error"` → `"error"` (a failure is the thing a consultant must see; it never gets averaged away)
3. all `status == "completed"` → `"completed"`
4. any `status == "analyzing"` → `"analyzing"`
5. otherwise → the status of the **least-advanced** assessment, i.e. `min(assessments, key=lambda a: STAGE_RANK.get(a.status, 0)).status`

Rule 5 is "least-advanced-wins", not most-advanced: an engagement is only as far along as the work still outstanding in it, and a portfolio view exists to surface what is not done. An unknown status ranks 0 (treated as least advanced) rather than raising.

**`derive_progress_pct(assessments) -> int`** — `0` for an empty list, otherwise
`round(100 * sum(STAGE_RANK.get(a.status, 0) for a in assessments) / (STAGE_RANK_MAX * len(assessments)))`.
This is a stage-weighted average so progress advances through the workflow instead of jumping 0 → 100 at completion. An `error` assessment contributes its `STAGE_RANK.get("error", 0)` = 0 — deliberate, so a broken assessment visibly drags the bar down.

**`derive_last_activity(assessments, fallback) -> datetime`** — `max(a.updated_at for a in assessments)` when the list is non-empty, else `fallback` (`Engagement.updated_at` for an engagement, `Client.updated_at` for a client-level roll-up). For a Client, roll up as `max` over its engagements' already-derived `last_activity` values, falling back to `Client.updated_at` when it has no engagements.

`Engagement.status` (the DB column, `"active"` / `"closed"`) is a separate lifecycle field and is **never** used as the card badge. It only filters: the dashboard hides engagements with `status == "closed"`; the engagement-detail page renders them regardless (a direct link always resolves).

### 2. Orphaned (`engagement_id IS NULL`) assessments — decision

**Decision: render them, do not require P1-3 to have run, do not crash, do not hide them.** The dashboard groups them into a distinct "Unmigrated assessments" section rendered *below* the client list, each linking straight to `/assessments/{id}`, with a one-line note: *"These assessments predate the Client/Engagement hierarchy. Run `scripts/migrate_legacy.py` to file them under a client."* The section is omitted entirely when the list is empty.

Rationale, stated so it isn't relitigated: P1-3 is a script a human runs, not a startup hook — a developer DB, a restored backup, or a DB restored from before PR #19 can legitimately contain NULL-engagement rows. Hard-requiring P1-3 would make the app's front page 500 on a valid DB; silently filtering them would make real assessments vanish with no signal. The synthetic section is the only option that is both safe and honest. It costs one extra query and ~15 lines of template.

### 3. Routes — exact paths and methods

| Method | Path | Returns | Notes |
|---|---|---|---|
| GET | `/` | `pages/dashboard.html` | Rewritten `dashboard()`. |
| GET | `/clients/{client_id}` | `pages/client_detail.html` | 404 if no such Client. |
| GET | `/clients/{client_id}/engagements-list` | `partials/engagement_list.html` | HTMX fragment only (step 5). |
| GET | `/engagements/{engagement_id}` | `pages/engagement_detail.html` | 404 if no such Engagement. |
| GET | `/engagements/new` | `pages/new_engagement.html` | Optional `?client_id=` preselects a client. |
| GET | `/engagements/new/client-fields` | `partials/client_picker.html` | HTMX fragment only. Query param `mode=existing\|new` (400 on anything else), optional `client_id=`. |
| POST | `/engagements` | 303 → `/engagements/{id}` | Single-page form submit; 400 + re-render on validation failure. |

All of these live in `app/routers/web.py` on the existing `router` (no new router module — the ownership contract's "contained" criterion). Declare the `/clients/...` and `/engagements/...` routes **above** the existing `/assessments/{assessment_id}` block so path ordering is obvious on read; FastAPI matching is unaffected either way since the prefixes are disjoint.

### 4. Template variable contracts

Build two plain-dict shapes once, in `app/services/portfolio.py`, and pass them everywhere. Nothing in a template may reach through an ORM attribute that doesn't exist.

`engagement_card` dict:
```
{"id": str, "name": str, "type": str, "status": str,          # Engagement columns, verbatim
 "derived_status": str, "derived_status_label": str,           # step 1; label from the badge map
 "progress_pct": int, "assessment_count": int,
 "framework_ids": list[str],                                   # union over its assessments' .frameworks, first-seen order
 "framework_badges": list[{"id": str, "name": str, "version": str}],
 "last_activity": datetime}
```

`client_card` dict:
```
{"id": str, "name": str, "industry": str, "size": str, "retention_years": int,
 "engagement_count": int, "last_activity": datetime,
 "engagements": list[engagement_card]}
```

`framework_badges` resolves each id via `FrameworkRegistry.get_or_none(fw_id)`, falling back to `{"id": fw_id, "name": fw_id.upper(), "version": ""}` — the same defensive pattern `_selected_framework_names` already uses in `web.py`.

Route contexts, exactly:

- **`GET /`** → `{"request", "clients": list[client_card], "unmigrated_assessments": list[Assessment], "total_client_count": int, "total_engagement_count": int}`
- **`GET /clients/{id}`** → `{"request", "client": Client, "engagements": list[engagement_card], "assessment_count": int, "last_activity": datetime}`
- **`GET /engagements/{id}`** → `{"request", "engagement": Engagement, "client": Client, "card": engagement_card, "assessments": list[{"id", "company_name", "description", "status", "created_at", "updated_at", "framework_badges": list[...]}]}`
- **`GET /clients/{id}/engagements-list`** → `{"request", "engagements": list[engagement_card]}`
- **`GET /engagements/new`** → `{"request", "frameworks": _framework_catalog(), "clients": list[Client] (ordered by name), "mode": "existing"|"new", "preselected_client_id": str|None, "error": str|None, "form_values": dict|None}`
- **`GET /engagements/new/client-fields`** → `{"request", "mode", "clients", "preselected_client_id", "form_values"}`

### 5. Query plan (no `relationship()`, no N+1)

`dashboard()` issues exactly **four** queries regardless of row count:
```python
clients = db.query(Client).order_by(Client.name).all()
engagements = (db.query(Engagement)
                 .filter(Engagement.status != "closed")
                 .order_by(Engagement.created_at.desc()).all())
linked = (db.query(Assessment)
            .filter(Assessment.status != "archived", Assessment.engagement_id.isnot(None)).all())
unmigrated = (db.query(Assessment)
                .filter(Assessment.engagement_id.is_(None), Assessment.status != "archived")
                .order_by(Assessment.created_at.desc()).all())
```
then group `engagements` by `client_id` and `linked` by `engagement_id` in Python (`collections.defaultdict`, already imported in `web.py`). Clients sort by `name`; engagements within a client sort by `last_activity` descending.

A Client with zero engagements still appears, with `engagements == []` — the template renders an inline empty state and a `New engagement` link to `/engagements/new?client_id={{ client.id }}`. An Engagement with zero assessments renders with `derived_status == "empty"` and `progress_pct == 0`.

`client_detail` / `engagement_detail` use the same helpers scoped to one row (`db.get(Client, client_id)` etc.), never `.all()` over the whole table.

### 6. "New Engagement" replaces "New Assessment" as the entry point — decision

**Decision: "New Engagement" is the only UI entry point; `POST /assessments` survives as a compatibility shim that now also creates the hierarchy.** Concretely:

- Extract the row-creation into one helper in `web.py`:
  `_create_engagement_with_assessment(db, *, client, engagement_name, engagement_type, description, framework_ids) -> Engagement` which creates, in one transaction: `Engagement(client_id=client.id, name=..., type=..., status="active")`, `Assessment(company_name=client.name, industry=client.industry, company_size=client.size, description=..., selected_frameworks=json.dumps(framework_ids), engagement_id=engagement.id)`, and one `AssessmentPack(assessment_id=..., framework_id=fw_id, pack_version=<see below>)` per framework id. One `db.commit()` at the end; on any exception, `db.rollback()` and re-render with an error — never a partially-created hierarchy.
- `pack_version` = `FrameworkRegistry.get_or_none(fw_id).version` when resolvable, else `"unknown"`. (Note the deliberate divergence from P1-3, which writes `"unknown"` for every backfilled pack because no version metadata existed at migration time. New packs are versioned; migrated ones are not. Do not retro-fix P1-3's rows here.)
- `GET /assessments/new` becomes `RedirectResponse("/engagements/new", status_code=307)`; delete `pages/new_assessment.html` only after confirming no other template links to it (`grep -rn "assessments/new" app/templates/`).
- `POST /assessments` (and its `POST /assessments/new` alias) keeps its existing form contract and status codes, but its body now: looks up `Client` by exact `company_name` (`db.query(Client).filter(Client.name == company_name).first()`), creates one if absent using the posted `industry`/`company_size`, then calls the same helper. It 303-redirects to `/assessments/{assessment.id}` as it does today (not to the engagement) so existing callers and tests keep working.

This is the invariant the later non-nullable-`engagement_id` task depends on: **after P1-4 there is no code path in `app/` that creates an `Assessment` without an `engagement_id`.**

### 7. `POST /engagements` — form fields and validation

Form fields (single-page form, not a wizard — a three-step wizard would need server-side partial state with no model to hold it, and every field fits on one screen):

| Field | Required | Notes |
|---|---|---|
| `client_mode` | yes | `existing` or `new`; anything else → 400 |
| `client_id` | when `client_mode == "existing"` | must resolve via `db.get(Client, client_id)` |
| `company_name` | when `client_mode == "new"` | becomes `Client.name`; unique |
| `industry` | when `client_mode == "new"` | same `<option>` list as `pages/new_assessment.html` |
| `company_size` | when `client_mode == "new"` | same `<option>` list |
| `engagement_name` | yes | non-empty after `.strip()` |
| `engagement_type` | no | default `"gap_assessment"`; allowed set `{"gap_assessment", "audit", "readiness"}` |
| `description` | no | copied to `Assessment.description`, `None` when blank |
| `selected_frameworks` | yes, ≥1 | multi-valued; read with `form.getlist("selected_frameworks")` exactly as `create_assessment` does |

Validation order and failure behaviour (mirror `create_assessment`'s existing pattern — re-render `pages/new_engagement.html` with `error` and `form_values`, **HTTP 400**, never a redirect):
1. `client_mode` valid.
2. Frameworks non-empty → `"Select at least one framework to assess against."` De-duplicate with `list(dict.fromkeys(...))`, preserving order.
3. Every framework id in `ENABLED_ASSESSMENT_FRAMEWORKS` → `"One or more selected frameworks are not available for assessment yet."` (verbatim reuse of the existing string).
4. `engagement_name.strip()` non-empty → `"Engagement name is required."`
5. `client_mode == "existing"`: `client_id` resolves, else `"Select an existing client or create a new one."`
6. `client_mode == "new"`: `company_name`/`industry`/`company_size` all present, and no `Client` already has that `name` → `"A client named '<name>' already exists — select it instead."` Also wrap the insert in `try/except IntegrityError` → `db.rollback()` and the same message, since `clients.name` is uniquely constrained and a check-then-insert races.

On success: create rows via the step-6 helper, then `RedirectResponse(f"/engagements/{engagement.id}", status_code=303)`.

### 8. HTMX interaction points — exactly two

Both endpoints return a **fragment** (a partial that does not extend `base.html`) and both guard with the `is_htmx and not is_boosted` test from `assessment_report_page`. A non-HTMX (or boosted) request to either → `RedirectResponse` to the corresponding full page (`/clients/{id}` and `/engagements/new` respectively), so a hard refresh or a crawler never gets a naked fragment.

**(a) Lazy engagement list on a dashboard client card.** In `pages/dashboard.html`, each client card's engagement list is a `<div id="client-{{ c.id }}-engagements">` inside a `<details>`. The `<summary>` carries:
```
hx-get="/clients/{{ c.id }}/engagements-list"
hx-target="#client-{{ c.id }}-engagements"
hx-swap="innerHTML"
hx-trigger="click once"
```
`click once` so a re-collapse doesn't refetch. The div is pre-rendered server-side with the same `partials/engagement_list.html` include so the dashboard is fully useful with JS disabled; the swap is a refresh, not a reveal.

**(b) Client-mode toggle on the new-engagement form.** Two radios named `client_mode`, each with:
```
hx-get="/engagements/new/client-fields?mode=existing"   (resp. mode=new)
hx-target="#client-fields"
hx-swap="innerHTML"
hx-trigger="change"
```
`#client-fields` is the wrapper div holding either the `<select name="client_id">` or the three new-client inputs.

The submit-button-disabled-until-a-framework-is-checked script in `pages/new_assessment.html` moves to `pages/new_engagement.html` unchanged (same ids: `#new-engagement-form`, `#create-engagement`, `.framework-choice`) — rename the ids to match, and re-run the listener binding after an HTMX swap is **not** needed, since the framework checkboxes live outside `#client-fields`.

### 9. Templates to add

- `app/templates/pages/dashboard.html` — **rewrite.** Header becomes "Portfolio" with a "New Engagement" button → `/engagements/new`. Client cards → nested engagement rows → "Unmigrated assessments" section → global empty state ("No clients yet").
- `app/templates/pages/client_detail.html` — **new.** Breadcrumb `Portfolio / {{ client.name }}`, client meta (industry, size, retention years), engagement list, "New engagement for this client" button.
- `app/templates/pages/engagement_detail.html` — **new.** Breadcrumb `Portfolio / {{ client.name }} / {{ engagement.name }}`, derived status badge + progress bar + last activity, then one row per Assessment linking to `/assessments/{{ a.id }}` with its `components/status_badge.html` and its framework badges.
- `app/templates/partials/engagement_list.html` — **new.** Expects `engagements` (list of `engagement_card`). One row per engagement; empty state when the list is empty.
- `app/templates/partials/client_picker.html` — **new.** Expects `mode`, `clients`, `preselected_client_id`, `form_values`.
- `app/templates/components/engagement_status_badge.html` — **new.** Expects `derived_status`. Maps the step-1 outputs: `empty` → "No assessments" (gray), `error` → "Error" (red), `completed` → "Completed" (green), `analyzing` → "Analyzing…" (purple, with the same spinner SVG `status_badge.html` uses), and the remaining stage names reusing `status_badge.html`'s colors/labels. Do **not** edit `components/status_badge.html`; it stays the per-assessment badge.
- `app/templates/pages/new_engagement.html` — **new.** Structurally a copy of `pages/new_assessment.html` (same card, same `<option>` lists, same framework checkbox grid, same error banner) with the client-mode radios and `#client-fields` wrapper added. Add the `dark:` class variants that `new_assessment.html` is missing, since `dashboard.html` and `base.html` both carry them.

## Key files

| File | Why it matters |
|---|---|
| `app/routers/web.py` | `dashboard()` (rewrite), `new_assessment_page`/`create_assessment` (redirect + hierarchy-creating shim), and all six new routes. `assessment_report_page` holds the canonical `HX-Request`/`HX-Boosted` test to copy. |
| `app/services/portfolio.py` (new) | `STAGE_RANK`, `derive_status`, `derive_progress_pct`, `derive_last_activity`, and the `client_card`/`engagement_card` builders — one implementation, three routes, directly unit-testable. |
| `app/models/client.py`, `engagement.py`, `assessment_pack.py` | Exact columns. `Engagement.status` has **no** default — pass `"active"` explicitly or the insert fails. |
| `app/models/assessment.py` | `engagement_id` (nullable), the `frameworks` property, and the `@validates("selected_frameworks")` hook that rejects an empty list — validate framework selection *before* constructing the `Assessment`, so the user gets a 400 page and not a `ValueError` traceback. |
| `app/templates/base.html` | `hx-boost="true"` on `<body>` — the reason every fragment route needs the `HX-Boosted` guard. |
| `app/templates/partials/framework_tabs.html` | Reference for `hx-get`/`hx-target`/`hx-swap` markup style. |
| `app/templates/components/status_badge.html` | Per-assessment badge, reused on engagement detail; the color/label maps to mirror in `engagement_status_badge.html`. |
| `app/frameworks/registry.py` | `FrameworkRegistry.get_or_none(...)` and `FrameworkDefinition.version` (already consumed by `_framework_catalog`) — the source for `framework_badges` and `AssessmentPack.pack_version`. |
| `scripts/migrate_legacy.py` (P1-3) | Writes `pack_version="unknown"`; the deliberate divergence from step 6's versioned packs. |

## Non-goals

- Do **not** add SQLAlchemy `relationship()` to any model. This codebase has none; introducing one here would change lazy-loading behaviour for every existing query.
- Do **not** make `assessments.engagement_id` non-nullable, and do **not** write an Alembic migration in this task. P1-4 is routes and templates only.
- Do **not** run `scripts/migrate_legacy.py` as part of the app, at startup or on first dashboard render. It stays a human-invoked script.
- Do **not** touch the scoring, report, PDF or comparison surfaces — per-framework score display is P1-5's job and lands in parallel. The only overlap is `app/routers/web.py`; keep P1-4's edits confined to the routes named above so the two branches merge cleanly.
- Do **not** add Client or Engagement *editing*/deletion (rename, archive, close). Create + read only; `Engagement.status` is written once as `"active"`.
- Do **not** add pagination, search or filtering to the dashboard. The expected row count is tens.
- Do **not** repair `components/status_badge.html`'s missing `scoped` entry — pre-existing, cosmetic, unrelated.

## Test scenarios

Add `tests/integration/test_portfolio_dashboard.py` (the HTTP harness from PW-4 already lives in `tests/integration/`). Unit-test the `app/services/portfolio.py` helpers directly where the scenario is purely computational.

1. **Dashboard renders the hierarchy.** Seed 2 Clients; Client A has 2 Engagements (one with 2 Assessments, one with 1), Client B has 1 Engagement with 1 Assessment. `GET /` is 200 and the HTML contains both client names, all three engagement names, and links to `/clients/{id}` and `/engagements/{id}` for every seeded row. Assert the response contains no `/assessments/` link for an assessment that *is* linked to an engagement (those are reached via the engagement page).
2. **Derived status — least-advanced-wins.** An Engagement whose Assessments are `completed` and `context_gathered` derives `"context_gathered"`, not `"completed"`. An Engagement whose Assessments are `completed` and `error` derives `"error"`. An Engagement whose Assessments are all `completed` derives `"completed"`. An Engagement with one `analyzing` and one `created` derives `"analyzing"` (rule 4 beats rule 5). Assert on `derive_status` directly *and* that the rendered dashboard shows the matching badge label.
3. **Derived progress.** Two Assessments at `created` (rank 0) and `completed` (rank 6) → `progress_pct == 50`. A single `questionnaire_done` (rank 4) → `67`. Zero assessments → `0` and `derived_status == "empty"`. An archived Assessment is excluded from both the count and the average.
4. **Last activity.** An Engagement's `last_activity` equals the max `updated_at` across its non-archived Assessments, not its own `updated_at`, when it has assessments; equals `Engagement.updated_at` when it has none. A Client's equals the max over its engagements.
5. **Orphaned assessment is surfaced, not hidden or fatal.** Seed one Assessment with `engagement_id=None` alongside a normal hierarchy. `GET /` is 200, the response contains the orphan's `company_name` and a link to `/assessments/{orphan.id}`, and contains the string `Unmigrated`. With zero orphans, the response does **not** contain `Unmigrated`.
6. **New Engagement, existing client, end-to-end.** Seed a Client. `POST /engagements` with `client_mode=existing`, that `client_id`, an `engagement_name`, and `selected_frameworks=["dpdpa","iso27001"]` → 303 to `/engagements/{new_id}`. Assert exactly: `Client` count unchanged, +1 `Engagement` (`client_id` correct, `status == "active"`, `type == "gap_assessment"`), +1 `Assessment` with `engagement_id` set and `frameworks == ["dpdpa","iso27001"]` and `company_name == client.name`, and **+2** `AssessmentPack` rows with the right `framework_id`s and a non-empty `pack_version`.
7. **New Engagement, new client.** Same POST with `client_mode=new` and a fresh `company_name`/`industry`/`company_size` → +1 `Client` (industry/size copied from the form) plus everything in scenario 6. Re-posting the same `company_name` → HTTP 400, the re-rendered form contains the "already exists" message, and **no** new `Client`/`Engagement`/`Assessment`/`AssessmentPack` rows are created (assert all four counts).
8. **Validation failures re-render at 400 with no partial writes.** (a) no `selected_frameworks`; (b) a roadmap framework id (e.g. `gdpr`, which is in `ROADMAP_FRAMEWORKS` not `ENABLED_ASSESSMENT_FRAMEWORKS`); (c) blank `engagement_name`; (d) `client_mode=existing` with a non-existent `client_id`. Each returns 400, contains the specified error string, and leaves all four table counts unchanged.
9. **Engagement detail shows its assessments with framework badges.** Seed an Engagement with one single-framework (`dpdpa`) and one multi-framework (`dpdpa`+`nist_csf`) Assessment. `GET /engagements/{id}` is 200, shows the client name and engagement name, lists both assessments with links to `/assessments/{id}`, and renders the resolved framework display names (`FrameworkRegistry.get("dpdpa").name`, `...get("nist_csf").name`) — not the raw ids. `GET /engagements/does-not-exist` → 404. Same for `GET /clients/does-not-exist` → 404.
10. **HTMX fragments are fragments.** `GET /clients/{id}/engagements-list` with `HX-Request: true` (and no `HX-Boosted`) returns 200 whose body does **not** contain `<!DOCTYPE`, `<html`, or `<nav` — i.e. it is a bare fragment — and does contain each engagement name. The same URL with `HX-Request: true, HX-Boosted: true`, and with no HTMX headers at all, both return a redirect to `/clients/{id}`. Repeat all three cases for `GET /engagements/new/client-fields?mode=new` (fragment contains a `name="company_name"` input; `?mode=existing` contains a `name="client_id"` select; `?mode=bogus` → 400).
11. **Zero-row edge cases.** A Client with no Engagements appears on the dashboard with an empty-state string and a `/engagements/new?client_id=...` link. An Engagement with no Assessments appears with the "No assessments" badge and a `0%` progress bar, and its detail page renders 200. A DB with zero Clients and zero Assessments renders the global empty state at 200.
12. **Legacy entry point still works and no longer orphans.** `GET /assessments/new` → 307 to `/engagements/new`. `POST /assessments` with the old form body (`company_name`/`industry`/`company_size`/`selected_frameworks`) still 303s to `/assessments/{id}`, and now also creates exactly one `Client` (or reuses the matching one), one `Engagement`, and one `AssessmentPack` per framework. Assert `Assessment.engagement_id is not None`. Then assert the portfolio invariant globally: after running the whole integration module, `db.query(Assessment).filter(Assessment.engagement_id.is_(None)).count()` equals only the orphans the tests seeded deliberately.

## Done criteria

- `GET /` renders Client → Engagement → (count of) Assessment with derived status, progress and last activity computed exactly as step 1 specifies, in four queries.
- `pages/client_detail.html`, `pages/engagement_detail.html`, `pages/new_engagement.html`, `partials/engagement_list.html`, `partials/client_picker.html`, `components/engagement_status_badge.html` all exist and render at phone and desktop widths with `dark:` variants throughout.
- `POST /engagements` creates `Client?` + `Engagement` + `Assessment` + N `AssessmentPack`s atomically, and every validation failure returns 400 with zero rows written.
- No code path in `app/` creates an `Assessment` with a NULL `engagement_id`; `grep -rn "Assessment(" app/` shows every construction site passing `engagement_id`.
- No `relationship()` added; `grep -rn "relationship(" app/models/` is still empty.
- All scenarios in `tests/integration/test_portfolio_dashboard.py` pass, and `pytest -q` passes in full with no regressions to the existing 240-test suite.
- Smoke-tested live per the project's smoke-test rule: `uvicorn app.main:app --reload`, create an engagement through the form, confirm it appears on `/` and its detail page, and confirm the two HTMX swaps update in place without a full-page flash.

## Rollback

Pure application code — no migration, no data written to a table that didn't already exist. `git revert` the commit. The only irreversible artifact is the `Client`/`Engagement`/`AssessmentPack` rows created through the new form during testing; those are removable with a targeted delete, or by restoring the P1-6 backup taken before the smoke test.

## Report back

Append a `## Results` section containing:
- The final route table as implemented (path, method, template, HTMX-or-page), flagging any path that had to differ from step 3 and why.
- The final `STAGE_RANK` table and the `derive_status` rule order, if either changed.
- A count table from the live smoke test: clients / engagements / assessments / assessment_packs before and after creating one engagement through the form.
- Confirmation of the orphan decision as shipped (section rendered, count of orphans present in the dev DB at the time).
- `pytest -q` output, plus the count of new tests in `tests/integration/test_portfolio_dashboard.py`.
- Any open question you hit that this document did not answer — name it rather than resolving it silently, so it can be folded back into the next handoff.
