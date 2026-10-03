# Yozora backend: implement the server-side work the approved redesign needs

**Written:** 2026-10-03. **For:** a cloud Claude session, working fully autonomously.
**Repo:** https://github.com/saqlainmmomin/Cyber, branch `claude/yozora-backend-features` (based on `main` at `eb3f5de`).
**PR:** opened alongside this file, carrying only the handoff. You push your implementation to the same branch.
**Merging:** Saqlain merges; you never merge.
**Commits:** end each commit message with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` and add no other attribution.

## Goal
Saqlain approved a redesign of the CyberAssess web app, code name Yozora. A separate track (Codex, slices S1 to S9) will rebuild the templates to the approved mockups. That track must not also have to invent backend behaviour, so you implement every server-side change the approved design needs first: models, migrations, services, routes and tests.

Template changes stay minimal and functional, in the current Tailwind style. The redesign restyles them later.

**Definition of done:**
- Every item in "Work" is implemented with tests.
- The full test suite passes.
- The CI file-set guard allows your files.
- The PR description lists every user-visible change and every test-string change.
- The Results section of this file is filled in.

## Background (decided; do not relitigate)
- The approved information architecture is in `docs/product/2026-10-01-app-design-mockups/screens/IA-SPEC.md` and `docs/product/2026-10-01-app-design-mockups/flow-map.html`.
  - Engagement tabs: Overview, Evidence, Findings and actions, Reports.
  - Assessment tabs: Overview, Scope, Questionnaire, Review, Report.
  - One five-stage stepper (Scope, Evidence, Questionnaire, Review, Report).
- Approved mockups are in `docs/product/2026-10-01-app-design-mockups/screens/`, notably:
  - `b1-firm_settings.html`, `b1-client_detail.html`
  - `b2-engagement_detail.html`, `b2-remediation_tracker.html`
  - `b4-evidence.html`
  - `b6-magic_links.html`, `b6-magic_upload.html`, `b6-magic_invalid.html`
  - `b6-comparison.html`, `b3-hub.html`, `b3-questionnaire.html`

  They are static HTML. Read them for fields and wording, not for markup to copy.
- Template-to-test map: `docs/product/yozora-migration-map.md`.
- Saqlain kept four features the app does not have yet:
  - Add assessment
  - Export actions
  - Open current report
  - Email the firm, which needs a firm contact email
- Retention moves to a firm-level setting.
- Client links carry a client contact.
- Evidence reuse is between assessments of the same engagement (`app/services/evidence_reuse.py`). Leave it as it is.
- Evidence status words shown to users map from the real states:
  - quarantined → Scanning
  - active → Available
  - rejected → Rejected
  - invalidated → Out of date
  - archived is not shown in lists
- There is no auth (single-user MVP). Keep the existing temporary reviewer/consultant name inputs wherever a route needs a name; they go away with Track 4 auth.
- Scoring is deterministic and never LLM-driven. Scores are never combined across frameworks. Framework-specific copy is conditional (see `CLAUDE.md`).

## Work
Implement in this order. Commit per item.

### 1. Firm settings (new persistence)
**Today:** firm branding is env config only (`app/config.py`: `firm_name`, `firm_logo_path`, `firm_color_*`). There is no settings page or table.

**Build:**
- **Model:** a singleton `FirmSettings` model and table with:
  - `contact_email` (nullable)
  - `archived_retention_years` (int, 1 to 50)
  - `accent_theme` (one of the preset names used in `design/yozora-tokens.css`)
  - `accent_custom_hex` (nullable)
  - `updated_at`
- **Service:** `app/services/firm_settings.py` with `get(db)` and `update(db, ...)`. `get` returns stored values, falling back to defaults. The retention default is decided in item 2.
- **Routes:** `GET /settings` and `POST /settings`. The new template `app/templates/pages/firm_settings.html` is minimal, current style. It shows:
  - firm name (read-only from env for now)
  - accent theme
  - contact email for clients
  - "Keep archived engagements for N years", with help text: archived engagements become eligible for permanent deletion after this period, and it applies to engagements archived from now on
  - the existing list of unmigrated assessments (no engagement), which today shows on the dashboard. Move it here; the mockups put it in Settings under data housekeeping.
- **Validation:**
  - Contact email: a basic format check.
  - Retention years: 1 to 50.
  - Custom accent hex: reject unless white text on the accent is at least 4.5:1, and the accent used as text on the light panel `#F0F1F6` is at least 4.5:1. The error shows the failing ratio, for example "White text on this colour is 3.1:1; it needs 4.5:1."
  - Put the contrast maths in a pure function with unit tests.
- **Branding:** do not rewire PDF or board-report branding to the DB in this PR. Record it as a follow-up in Results.
- **Navigation:** add a Settings link in `base.html` (current style).

### 2. Retention becomes firm-level
**Today:** `Client.retention_years` (default 7) is edited on client detail. The handler is `app/routers/retention.py`, around line 256, and the form is in `pages/client_detail.html`. The years are snapshotted into archive metadata (`retention_years_at_archive` in `app/services/retention.py`).

**Build:**
- New archives snapshot `FirmSettings.archived_retention_years`. Existing archive snapshots stay untouched.
- Purge eligibility for already-archived engagements must not change.
- **Initial firm value (data migration):**
  - If all clients share one value, use it.
  - Otherwise use the largest; the safer choice keeps data longer.
  - With no clients, use 7.
  - Record what the migration did in a log line, and in Results for the seed and demo data.
- Keep the `clients.retention_years` column. Do not drop it, but stop reading it for new archives. Mark it deprecated in the model with a comment.
- Remove the client-level retention form from `client_detail.html` and retire its POST route. Either remove the route and update its tests deliberately, or have it redirect to `/settings` with 303. Choose one and state it in the PR.
- Engagement pages keep archive/unarchive (`partials/engagement_retention.html`). The retention text there must now read the firm value.
- Grep `tests/` for `retention` and update the tests deliberately.

### 3. Add assessment to an existing engagement
**Today:** assessments are only created through the new-engagement flow (`POST /engagements` and `POST /assessments/new` in `app/routers/web.py`). The `Assessment` model has no display-name field. The redesign lists assessments by name (for example "Head office", with a scope line).

**Build:**
- **Model:** add `Assessment.name`, nullable. Display falls back to the current behaviour (`company_name`) when it is null. Backfill nothing.
- **Routes:**
  - `GET /engagements/{id}/assessments/new`: a minimal form with name, scope description (`description`) and framework checkboxes limited to `ENABLED_ASSESSMENT_FRAMEWORKS`.
  - `POST /engagements/{id}/assessments`.
  - The new assessment inherits `company_name`, `industry` and `company_size` from the engagement's client or its existing assessments. Copy what `create_engagement` does.
  - Reject archived engagements (400, reusing the archived checks in `app/services/retention.py`).
  - Redirect to the new assessment.
- **Engagement page:** add an "Add assessment" button on `pages/engagement_detail.html` (current style).
- **Tests:** create, validation (no framework, unknown framework, archived engagement), and name fallback.

### 4. Export actions (Findings and actions)
**Today:** the engagement remediation tracker is `GET /engagements/{id}/remediation` (`app/routers/web.py`, around line 438). Actions and findings live in `app/models/action.py` and `finding.py`; see `app/services/findings.py` and `app/services/remediation*`.

**Build:**
- **Route:** `GET /engagements/{id}/remediation/export.xlsx`, using openpyxl, which is already used by the board exports (see `app/services/board_exports.py` for style).
- **Columns:**
  - assessment
  - framework
  - control code
  - finding
  - severity
  - priority, as words: Do first, Next, Planned, Backlog. Never numeric, because this file may go to clients. Find the existing 1–4 priority mapping and add one word map in one place.
  - action
  - owner
  - due date
  - status
  - verified (yes/no and date)
  - last updated
- **Scoping:** only include actions on findings from approved conclusions, the same set the tracker shows. Include archived engagements read-only.
- **Filename:** `<client>-<engagement>-actions-<YYYY-MM-DD>.xlsx`, slugified.
- **Tracker:** add an "Export actions" link on `pages/remediation_tracker.html`.
- **Tests:** headers, one row per action, priority words, empty engagement (headers only), and the 404 path.

### 5. Open current report from the comparison page
`comparison_page` is in `app/routers/web.py`, around line 2277; its template is `pages/comparison.html`. Add the current assessment's report URL to the context (the same URL the assessment's Report tab uses today), and add an "Open current report" link. Add a test that the link is present.

### 6. Client contact on magic links, and "Email the firm" on invalid links
**Today:** `MagicLink` (`app/models/magic_link.py`) has no contact. Creation routes are in `app/routers/magic.py`: `POST /engagements/{id}/magic-links` and `POST /assessments/{id}/rfi/versions/{snapshot_id}/magic-links`. The invalid or expired page is `magic/invalid.html`, rendered by `_render_invalid`.

**Build:**
- **Model:** add nullable `contact_name` (max 200) and `contact_email` (max 254, format-checked).
- **Creation:** accept both on both creation routes. They are optional, so existing callers and tests keep working.
- **Display:** show them in `partials/magic_links.html` and `partials/rfi_links.html` rows.
- **Upload page:** use the contact's first name in the upload page greeting when present (`magic/upload.html`, for example "Ananya, <firm> needs these items"). The page is otherwise unchanged.
- **Invalid page:** when `FirmSettings.contact_email` is set, show an "Email <firm name>" mailto link. When it is not set, show nothing extra.
- **Security:** never put the token in the mailto. Never reveal the engagement or client name on the invalid page beyond what it shows today. Keep the existing behaviour that the token is shown once, at creation.
- **Out of scope:** do not change how requested items are chosen (free text on the engagement route, RFI items on the RFI route). The mockup's tick-box picker is a UI change for the redesign; note it in Results.
- **Tests:** creation with and without a contact, email validation, rendering, and the invalid-page mailto present and absent.

### 7. Read models the redesigned screens need (services and tests only, no templates)
Pure functions with unit tests. The redesign templates will call them.

- **`app/services/evidence_inventory.py`:** `inventory_rows(db, engagement_id, *, assessment_id=None, source=None, status=None, search=None)` and `cross_engagement_rows(db, ...)`. Each row has:
  - evidence id, filename, mime/type label, size
  - source: `upload`, `aws`, `client_link` (with the link's contact name when known) or `reused` (with the source assessment name)
  - assessments it is used by
  - supported requirement/control codes, through `EvidenceUse` or the equivalent
  - status label, using the mapping above
  - updated date

  Also `status_counts(...)`. Work out the source from the real data: how AWS pulls, magic-link uploads and reuse confirmations record provenance. Read `app/services/evidence.py`, `aws_evidence.py`, `magic*.py` and `evidence_reuse.py`. If a source cannot be told apart from the stored data, say so in Results rather than adding a column speculatively.
- **`app/services/assessment_stage.py`:** `stage(db, assessment)` returns:
  - the stage, one of scope, evidence, questionnaire, review, report
  - a short progress note, for example "3 of 6 approved" or "18 of 42 answered"
  - the next-step label and target, from: Set scope, Upload evidence, Pre-fill questionnaire, Continue questionnaire, Run analysis, Review N conclusions, Release report, Generate board report

  Derive it only from existing fields: scope answers, evidence, `desk_review_status`, questionnaire responses, analysis runs, conclusion review states, release state and snapshots. Document the rules in the module docstring and test each transition.
- **`app/services/prefill_freshness.py`:** given an assessment, the count of available documents and the count added since the last completed desk review. These feed "5 documents ready to pre-fill" and "3 new documents since the last pre-fill".
- **`app/services/request_summary.py`:** per assessment in an engagement, the latest RFI version number, its item count, and how many items have been received through magic links.

## Constraints
- **Do not read** `validation/companies/*/answer_key.json`. It is a held-out evaluation set, enforced by `tests/test_answer_key_isolation.py`.
- **Never call live LLMs.** Tests must not need `OPENROUTER_KEY`. If you run anything that could reach a live LLM script, set `OPENROUTER_KEY=""`; do not unset it, because `.env` would still load. Do not change prompts, the analyzer, desk review logic or scoring.
- **Pipeline and PDFs:** do not flip `ANALYSIS_PIPELINE_VERSION`. Add new PDF sections only; never rewrite pages. All PDF text goes through `S()`.
- **Migrations:** add an Alembic revision in `alembic/versions/`, following the latest revision's style (the app runs `alembic upgrade` at startup, `app/main.py`). Keep `app/legacy_migrations*.py` consistent if new columns must also exist on legacy databases; check how the most recent columns were added and match that. SQLite: JSON is stored as TEXT columns. Every migration must be reversible where practical.
- **CI file-set guard:** `tests/test_p6_2b_dpdpa_criteria.py`, `test_scenario_11_only_p6_2b_files_change`. Add a `YOZORA_BACKEND_FILES` tuple (this handoff is already listed there) holding every file you add or change, and include it in the offenders filter. Never delete or weaken existing guards. Also check `tests/test_p6_9_file_set.py` and any other file-set test for the same need.
- **Templates:** keep template changes minimal and in the current style. Do not restyle; the Yozora slices do that. Do not rename existing element ids, `hx-*` targets or `data-*` attributes (listed per template in `docs/product/yozora-migration-map.md`). If you add a template, add its row to the migration map, with slice S3 for settings.
- **Style:** match the surrounding code. Sentence case in user-facing copy. No exclamation marks. Dates like "15 Oct 2026".
- **Scope:** if a requirement here contradicts the code in a way that needs a product decision, implement the conservative option and list the decision in Results and the PR description. Do not stop the whole task for it.

## Verification (before reporting done)
- **Environment:** Python 3.13 (`python3.13 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt`). Homebrew 3.14 breaks Jinja2.
- **Full suite:** `.venv/bin/python -m pytest -q` passes. Paste the summary line into Results. If some tests were already failing on `main` before your change, show that with `git stash` or a clean checkout and list them.
- **Migrations:** `alembic upgrade head` on a fresh SQLite database, then on a copy of a database created at `main`, then `alembic downgrade -1` and `upgrade` again.
- **Smoke test:** start `uvicorn app.main:app --host 127.0.0.1` with `OPENROUTER_KEY=""`. With a seeded or demo engagement, use curl or the test client to:
  - open `/settings`, save a contact email, then try a failing accent and confirm the ratio message;
  - add an assessment to an engagement;
  - download the actions export and open it with openpyxl to print the headers and first row;
  - create a magic link with a contact;
  - load an expired magic link and see the mailto.

  Record the commands and outputs in Results.

## Report back
- Append `## Results` to this file. Cover:
  - what was built per item;
  - migrations and data-migration behaviour;
  - routes added or retired;
  - template changes, each with its migration-map row;
  - test-string changes;
  - decisions you made and why;
  - follow-ups (DB-backed branding, tick-box item picker, anything deferred);
  - the verification outputs.
- Update the PR description to match.
- Push to `claude/yozora-backend-features`.
