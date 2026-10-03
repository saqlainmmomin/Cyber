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

## Results

**Written:** 2026-10-03, by the implementing cloud session. Branch `claude/yozora-backend-features`, one commit per item plus guard and test-string commits. Everything is server-side; templates got minimal, current-style changes only.

### What was built

1. **Firm settings.** `app/models/firm_settings.py` (`FirmSettings`, singleton row id 1: `contact_email`, `archived_retention_years` 1 to 50, `accent_theme`, `accent_custom_hex`, `updated_at`; CHECK constraints for the singleton and the range). `app/services/firm_settings.py`: `get(db)` (stored values, falling back to defaults: 7 years, `midnight`, no email), `validate(...)`, `update(db, ..., actor)` (audited as `firm_settings.updated` with the changed fields), and the pure contrast helpers `relative_luminance`, `contrast_ratio`, `format_ratio`, `accent_contrast_problem`. A custom accent must give white text at least 4.5:1 on it and at least 4.5:1 as text on `#F0F1F6`; the error names the failing ratio, rounded down ("White text on this colour is 2.6:1; it needs 4.5:1."). Routes `GET /settings`, `POST /settings` (`app/routers/firm_settings.py`); page `pages/firm_settings.html` (firm name read-only from env, accent presets plus custom colour, contact email for clients, "Keep archived engagements for N years" with the handoff's help text, and the unmigrated-assessments list moved off the dashboard). Settings link in `base.html`.
2. **Retention is firm-level.** New archives record `retention_years` = the firm setting and `retention_source: "firm"` in the archive event; that snapshot alone decides eligibility. Archive events written before this change have no `retention_source` and keep the old rule exactly (max of the client's current `retention_years` and the snapshot), so purge eligibility of already-archived engagements does not change. `clients.retention_years` is kept and marked deprecated. The client retention form is gone from `client_detail.html` and **`POST /api/clients/{client_id}/retention` is removed** (404 now; tests updated deliberately, see below). `set_client_retention` and `RETENTION_CONFLICT` are removed; `RETENTION_CHANGED_EVENT` stays for the historical events. `firm_settings` is a retained table (never purged). The engagement panel reads "Retention: N years after archive (firm setting, change in Settings)".
3. **Add assessment.** `Assessment.name` (nullable) and `Assessment.display_name` (name, else `company_name`). `GET /engagements/{id}/assessments/new`, `POST /engagements/{id}/assessments` (frameworks limited to `ENABLED_ASSESSMENT_FRAMEWORKS`; the client's name, industry and size inherited as `create_engagement` does, packs recorded through a shared `engagement_factory._add_assessment`; redirect 303 to the new assessment). "Add assessment" button on the engagement page (hidden when archived); the engagement page lists assessments by display name.
4. **Export actions.** `GET /engagements/{id}/remediation/export.xlsx` (`app/services/actions_export.py`, openpyxl, reusing `board_exports`' cell writer so formulas are stored as text). Columns: Assessment, Framework, Control code, Finding, Severity, Priority, Action, Owner, Due date, Status, Verified, Verified on, Last updated (verified yes/no and its date are two columns). Priority words live in one place, `findings.PRIORITY_WORDS` (1 Do first, 2 Next, 3 Planned, 4 Backlog) with `findings.priority_word()`. Filename `<client>-<engagement>-actions-<YYYY-MM-DD>.xlsx`, slugified. "Export actions" link on the tracker.
5. **Open current report.** `comparison_page` passes `current_report_url` = `/assessments/{id}?tab=report` (the Report tab's URL); the page links "Open current report".
6. **Client contact and Email the firm.** `magic_links.contact_name` (200) and `contact_email` (254, format checked). Both creation routes accept them (optional), validated before the link is created; `create_link`'s signature is unchanged (`test_p5_6` pins it), the contact is recorded with `magic_links.set_contact`. Shown in `partials/magic_links.html` and `partials/rfi_links.html` rows; the upload page greets "Ananya, <firm> needs these items." when a contact exists. `magic/invalid.html` shows "Email <firm>" as a `mailto:` to `FirmSettings.contact_email` when set, nothing otherwise; the page is still byte-identical for every invalid token and carries no token, engagement or client.
7. **Read models (services and tests only).** `evidence_inventory.py` (`inventory_rows`, `cross_engagement_rows`, `status_counts`), `assessment_stage.py` (`stage`, rules in the module docstring), `prefill_freshness.py` (`freshness`), `request_summary.py` (`assessment_summary`, `engagement_summaries`).

### Migrations and data migration
One revision, `alembic/versions/b7d41c9e2a63_yozora_backend_features.py`, on `5e9a2c7d4b18`: creates `firm_settings` and seeds its row, adds `assessments.name`, adds `magic_links.contact_name` and `contact_email`. Downgrade drops them, and refuses (like V3-A) if consultant-entered data would be lost (a firm contact email or custom accent, an assessment name, a link contact). Legacy migrations needed nothing: like V3-A, the new columns arrive only through Alembic.

Seed rule for `archived_retention_years`: every client with one shared value -> that value; differing values -> the largest; no clients (or no valid value) -> 7. It logs one line, e.g. `Firm retention seeded at 7 years: no clients, using the default of 7 years.` (seen in CI). For the seed and demo data (`scripts/seed_test_companies.py`, the longitudinal demo) every client is created with the model default of 7, so an existing seeded database migrates to 7.

### Routes
Added: `GET /settings`, `POST /settings`, `GET /engagements/{id}/assessments/new`, `POST /engagements/{id}/assessments`, `GET /engagements/{id}/remediation/export.xlsx`. Retired: `POST /api/clients/{client_id}/retention` (removed, not redirected). The settings router is mounted behind the shared archive write guard like every other mutating route (a no-op there: no engagement in the path).

### Templates (migration-map rows updated in `docs/product/yozora-migration-map.md`)
- New: `pages/firm_settings.html` (S3), `pages/new_assessment.html` (S4).
- Changed: `base.html` (`data-settings-link`), `pages/dashboard.html` (unmigrated list removed), `pages/client_detail.html` (retention form and "N-year retention" removed; `retention-years` and `data-retention-form` now live on the settings page), `partials/engagement_retention.html` (firm value), `pages/engagement_detail.html` (`data-add-assessment-link`, display name), `pages/remediation_tracker.html` (`data-export-actions`), `pages/comparison.html` (`data-current-report-link`), `partials/magic_links.html` and `partials/rfi_links.html` (contact inputs, `data-link-contact` column), `magic/upload.html` (`data-contact-greeting`), `magic/invalid.html` (`data-firm-contact`). No existing id, `hx-*` target or `data-*` attribute was renamed.

### Test-string and existing-test changes (deliberate)
- `tests/test_retention.py`: `RETAINED_TABLES` gains `firm_settings`; the route set loses the client retention route; archive metadata gains `retention_source`; scenario 5 rewritten as the firm-retention scenario (snapshot, firm changes not applied retroactively, legacy floor unchanged, retired route 404); scenario 8's `retention_invalid` case corrupts the snapshot (and a second case covers a pre-Yozora archive with an invalid client value); scenario 3's unresolvable set gains `POST /settings`.
- `tests/integration/test_portfolio_dashboard.py`: unmigrated assessments are asserted on `/settings`, not the dashboard.
- `tests/test_remediation_tracking.py`: the `/remediation` route set includes the export.
- Alembic head pins move to `b7d41c9e2a63` in `test_alembic_baseline_immutable`, `test_correctness_bundle`, `test_data_integrity`, `test_p5_2`, `test_p5_3`, `test_p5_4`, `test_p5_6`, `test_p6_6`, `test_startup_invariants`, `test_p6_8_v3a_data_capture` (whose lossy-downgrade case now steps down to V3-A first).
- File-set guards: `tests/yozora_backend_paths.py` lists exactly this PR's files; each existing guard gained one scoped allowance line (`test_p6_2b`'s `YOZORA_BACKEND_FILES`, `test_p6_9_file_set`, `p6_10_support`, `test_p5_2`, `test_p5_4`, `test_p5_6`, `test_p6_3a`, `test_p6_4_cap`, `test_p6_4_v2_judge`, `test_p6_4_whats_missing`, `test_p6_6`, `test_p6_7`, `test_p6_7b`, `test_p6_8_b2`, `test_p6_8_board_report_v2`, `test_p6_8_v3a_data_capture`, `test_p6_nist_csf2_alignment`). No guard was removed or loosened beyond those paths.
- New tests: `test_yozora_firm_settings.py`, `test_yozora_add_assessment.py`, `test_yozora_actions_export.py`, `test_yozora_comparison_link.py`, `test_yozora_magic_link_contacts.py`, `test_yozora_read_models.py`, shared fixtures in `tests/yozora_support.py`.

### Decisions (conservative options where the handoff and the code disagreed)
- **Retention rule for new archives:** the snapshot alone, not max(current, snapshot) as before, because the approved help text says the setting "applies to engagements archived from now on". Raising the firm value therefore does not extend existing archives. Pre-change archives keep the old per-client rule unchanged.
- **Client retention route:** removed rather than redirected, because nothing posts to it any more and a silent 303 would hide stale callers.
- **Archived engagement on Add assessment:** the form page returns 400 with the archived message; the POST is refused with 409 by the shared archive write guard before the handler runs (every write to an archived engagement behaves this way; bypassing the guard to get a 400 would be less safe). The handler also checks and would return 400.
- **Export row set:** exactly the tracker's (actions on findings of the engagement's non-archived assessments). Findings can only be created from individually approved or edited conclusions, so that is the "approved conclusions" set; a conclusion reopened later keeps its finding in both the tracker and the export.
- **Accent storage:** `accent_theme` always holds a preset; a custom colour is `accent_custom_hex` on top of it (choosing a preset clears it). Only the two contrast checks the handoff names are enforced; the design system's dark-canvas check for custom accents is not, because no dark variant is stored yet.
- **Assessment name:** optional; blank stores NULL and displays the company name.
- **Request summary:** counts are for the current issued RFI version (client links can only be created from it); `latest_version` also reports a newer unissued draft.
- **Evidence source "reused":** reuse is recorded per assessment (audit event `evidence_reuse.confirmed`), so a row is "reused" for an assessment it was reused into (or, unfiltered, when it was reused anywhere in the engagement), with `reused_from`; `origin` keeps its own channel. Every source can be told apart from the stored data, so no column was added. A manual mapping without a reuse confirmation keeps its origin.
- **Stage while work runs:** a running pre-fill or analysis returns that note and no next step.

### Follow-ups
- PDF and board-report branding still read env config (`app/services/firm_theme.py`); move firm name, logo and accent to `FirmSettings` in a later PR. The accent setting is stored but not yet applied to the UI (the Yozora slices apply it).
- Tick-box item picker for client links (b6-magic_links) is a redesign UI change; requested items are still free text on the engagement route and RFI items on the RFI route.
- Dark-mode contrast check for custom accents once a dark variant is stored.
- Firm name stays read-only from env until auth (Track 4).
- Evidence inventory does not list legacy `assessment_documents` that were never migrated to Evidence (pre-fill freshness does count them, as desk review reads them).

### Verification
