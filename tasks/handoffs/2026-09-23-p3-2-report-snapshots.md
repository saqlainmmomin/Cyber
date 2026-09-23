# P3-2: Report snapshots: write-once rendered versions with a draft → issued lifecycle, added beside the live report

**Plan:** `docs/plans/2026-09-21-002-revised-implementation-plan.md`, Phase 3, task P3-2 ("Generate report → create ReportSnapshot row with `is_issued=false` (draft)"; "Consultant reviews, issues → set `is_issued=true`, snapshot becomes immutable and client-visible"; "Regenerating creates a new ReportSnapshot, not an overwrite (PR-054 fix)"; "One `report_snapshots` table for workpapers, gap reports, and integrated reports (D2: `type` column discriminator)"; test: "Generate report, issue it, regenerate, verify two snapshots exist. Issued snapshot unchanged."). The plan's Target Schema block for `report_snapshots` (`type: workpaper | gap_report | integrated_report`, `format: pdf | html`, `is_issued` "only issued snapshots are client-visible") and the Phase 3 exit criterion "Reports generated as immutable snapshots". Decision **D2** in `tasks/2026-09-21-adversarial-review.md` ("One generic `audit_events` table. Normalize later if query needs emerge."). PRD `docs/product/2026-09-21-cyberassess-product-requirements.md`: **PR-054** ("Generated reports and RFIs shall be versioned snapshots. Acceptance: regenerating output creates a new version bound to the exact approved Conclusion set and does not overwrite an issued artifact."), **PR-052** ("exports … remain unavailable until review gates pass"), **PR-056** ("release" is an audited operation). The P2-6 hand-forward to this task (`tasks/handoffs/2026-09-23-p2-6-workpaper-view.md`, "Handed forward"): a `type = "workpaper"` snapshot must come from `build_workpaper`'s output, not a re-derivation.
**Owner:** Claude designs → Codex implements (per `tasks/agent-ownership.md`: "P3-2 Report snapshots (immutability) | Claude designs → Codex implements"; the ownership criteria name "issued-report immutability" as an irreversible concern). Every architectural fork is closed below. **If the code forces a deviation from any decision, stop and report it in `## Results`. Do not pick an alternative.** Merge gate: the standard `[AR]` adversarial review (`tasks/todo.md` tags Phase 3 `[AR: report immutability, provenance, closure verification]`), plus a Claude review of the diff.
**Depends on:** P2-6 (`app/services/workpaper.py::build_workpaper`, `pages/workpaper.html`) and P2-4 (`conclusion_review.reviewer_actor`). Both are **merged**: P2-6 is PR #29, merge commit `9bcd972`, the tip of `main`. (`tasks/todo.md`'s P2-6 line still says "PR #29, open, not yet merged". That line is stale; see Done criteria.)
**Runs in parallel with:** P3-1 (Findings and Actions). Per `tasks/agent-ownership.md`, "P3-1 and P3-2 have no file overlap". This task does **not** touch `app/models/finding.py`, `app/models/action.py`, or anything to do with Findings or Actions. The only files both tasks may edit are `app/main.py` (one `include_router` line each) and `tasks/todo.md` (one line each). If P3-1 merges first, the conflict is trivial: keep both lines.
**Blocks:** P3-3 ("P3-3 depends on P3-2's snapshot plumbing for final wiring"). P3-3's PDF content changes reach new gap-report snapshots with no extra work (D-P3-2-A). Its engagement-level integrated report uses the reserved type and storage path defined here (D-P3-2-I).
**Failing contract suite: none pre-written.** A grep of `tests/` for `P3-2`, `ReportSnapshot`, `report_snapshot` and `is_issued` finds only the P1-2 schema checks in `tests/test_target_schema.py` (the table name in the expected-tables list, and its two FK tuples). As with P2-4 and P2-6, **Codex writes `tests/test_report_snapshots.py` itself** from `## Test scenarios`, following the fixture pattern of `tests/test_workpaper.py` (step 7). Every scenario listed is required. You may add cases, but you may not drop or weaken one.

## Goal

A consultant can freeze a report as an exact, permanent file, review it, and release it, and nothing in the system can later change what was released.

- **Generate** renders the report as it would be served right now and writes those bytes once to a new file. It adds one new `ReportSnapshot` row (`is_issued = false`, a draft) and one `audit_events` row that records the file's SHA-256 and the exact source state it was built from. Generating again always adds a new row and a new file. It never updates or replaces an earlier one.
- **Issue** flips a draft to `is_issued = true` in one atomic, one-way statement, and only for the newest version of its report. It then writes an audit event recording who issued it. There is no un-issue, no edit and no delete.
- **Download/view** of any snapshot, draft or issued, streams the stored bytes after checking them against the recorded hash. It never re-renders.
- The existing live routes (`GET /api/assessments/{id}/report/pdf` and the workpaper page) keep working exactly as they do today, as the unversioned working view. Snapshots are added beside them. This is the P2-3 dual-write pattern (D-P2-3-A) applied to output.

## Current state

Grounded against `9bcd972` on `main`. Baseline `.venv/bin/pytest -q` → **443 passed, 115 warnings** (I ran it at `9bcd972`). Re-locate everything by symbol name.

- **`app/models/report_snapshot.py`, `ReportSnapshot`** (P1-2): `id` (String 36 PK, `default=_new_id`), `assessment_id` (nullable FK → `assessments.id`, indexed), `engagement_id` (nullable FK → `engagements.id`, indexed), `type` (String 30), `format` (String 10), `storage_path` (String 500), `generated_at` (`DateTime(timezone=True)`, `default=_utcnow`), `is_issued` (Boolean, `default=False`; NOT NULL in the migration). **There is no content column, no hash column, and no issued-at/issued-by column.** It is exported from `app/models/__init__.py`. The table was created by `alembic/versions/5c7c75960f43_p1_2_add_client_engagement_evidence_.py`. **Zero application code reads or writes it.** A grep of `app/` for `ReportSnapshot|report_snapshot|is_issued` finds only the model and `app/models/__init__.py`. Alembic head is `4e8c1a9d2b57`.
- **`app/models/audit_event.py`, `AuditEvent`**: `id`, `actor` (String 255), `action` (String 100), `entity_type` (String 100), `entity_id` (String 36), `metadata_json` (nullable Text), `created_at`. The only writer today is the private `_audit(db, *, actor, action, entity_type, entity_id, metadata)` helper in `app/services/evidence.py`. It writes `metadata_json=json.dumps(metadata, sort_keys=True)` and uses dotted actions such as `evidence.created` and `evidence_version.status_changed`.
- **Blob storage precedent (`app/services/evidence.py`)**:
  - Files live under `settings.upload_dir` (`app/config.py`, default `"uploads"`). `blob_path(storage_path) = Path(settings.upload_dir) / storage_path`.
  - `storage_path` is a **relative** path built only from ids: `f"evidence/{engagement_id}/{evidence_id}/v{n}.{type}"`.
  - `_write_blob` opens the file with mode **`"xb"`** (exclusive create), so an existing file can never be overwritten.
  - On any exception after the write, the service unlinks the file it just wrote (`written_path.unlink(missing_ok=True)`) and re-raises.
  - `verify_version` re-hashes the file against the stored `file_hash_sha256`.
  - **`scripts/backup.py::create_backup(db_path, upload_dir, out_dir)` copies the whole `upload_dir` tree**, so anything stored under it is backed up with the database (D9).
- **`app/routers/reports.py`** (prefix `/api/assessments/{assessment_id}/report`). Read in full. **Every route renders live from the current `GapReport`/`GapItem`/`Initiative` rows on every request, and none writes anything.**
  - `get_report` (`GET ""`, JSON `ReportOut`), `get_report_summary` (`GET /summary`) and `get_full_report` (`GET /full`) all call `require_review_approval` first.
  - **`download_pdf` (`GET /pdf`)** is a plain sync function `download_pdf(assessment_id: str, db: Session = Depends(get_db))`. It:
    1. calls `require_review_approval(assessment_id, db)` (404 "Assessment not found"; **403** "Report not yet approved for release. Complete the review process first." unless `assessment.review_status == "approved"`);
    2. calls `_get_report` (404 "No report found. Run analysis first."), then loads items, initiatives and an `answer_source_map` from `QuestionnaireResponse`, and parses `selected_frameworks`;
    3. calls the module-global **`generate_pdf`** (imported `from app.utils.pdf_export import generate_pdf`);
    4. returns `Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="Compliance_Assessment_{fw_label}_{company}.pdf"'})`.
  - `comparison_router` holds `get_comparable_assessments` and `compare_assessments`.
  - The file imports nothing from `Conclusion`, `AnalysisRun` or `analysis_pipeline`. The standing guard `tests/test_analysis_pipeline.py::test_legacy_consumers_do_not_read_the_new_tables` greps it, together with `app/utils/pdf_export.py`, `scoring.py`, `review.py` and `remediation.py`, for those names.
  - **No test calls the `/report/pdf` route.** Tests call `generate_pdf` directly (`tests/test_golden_dpdpa.py`, `tests/test_white_label.py`, `tests/test_no_blended_scoring.py`, `tests/support/fixture_capture.py`).
- **`app/utils/pdf_export.py`** (1133 lines) has one public entry point: `generate_pdf(report, gap_items, company_name, initiatives=None, answer_source_map=None, selected_frameworks=None, assessment=None) -> bytes`. It takes ORM objects (`GapReport`, `GapItem`s) and draws with custom fpdf2 helpers (`_draw_gap_card`, `_page_header`, …). Every string goes through `S()`. It sets no fixed creation date, so **two renders of identical data are not guaranteed to be byte-identical**. Its only caller in `app/` is `reports.download_pdf`.
- **Live UI links to the PDF:** `pages/assessment.html` ("Download PDF", shown when `assessment.status == 'completed'`), `partials/analysis_complete.html` ("Download PDF") and `partials/report_summary.html` ("PDF Report", in the "Detailed Findings" `<summary>`, next to the P2-6 "Workpaper" link). All three point to `/api/assessments/{{ … }}/report/pdf`. No test asserts these link texts. A grep of `tests/` for "Download PDF" and "PDF Report" finds nothing.
- **`app/utils/review_gate.py::require_review_approval(assessment_id, db) -> Assessment`** is the release gate for the PDF, the report JSON and the RFI downloads. `review_status` is set to `"approved"` only by the legacy bulk `review.approve_assessment`.
- **Workpaper (P2-6):**
  - `app/services/workpaper.py::build_workpaper(db, assessment, *, now=None) -> Workpaper` is read-only. Its result holds ORM objects (`ConclusionCard.conclusion`, `RevisionEntry.revision`) and datetimes, so it is not JSON-serializable as is.
  - `web.workpaper_page` (`GET /assessments/{assessment_id}/workpaper`) renders `pages/workpaper.html` with context `{"request", "assessment", "wp"}`.
  - **Neither `pages/workpaper.html`, `components/workpaper_entry.html` nor `base.html` references `request` or `url_for`.** `base.html` loads `/static/css/tailwind.css`, `/static/css/style.css`, `https://unpkg.com/htmx.org@2.0.4` and `/static/js/app.js`. The only global it needs is `branding`, set by `app/template_config.py::configure_templates`.
  - Standing guards (`tests/test_workpaper.py` scenario 9): the set of app routes whose path contains `/workpaper` is exactly `{("GET", "/assessments/{assessment_id}/workpaper")}`, and the two workpaper templates may contain no `<form`, `<button`, `hx-post`, … .
- **"Integrated report" today:** nothing produces one. `web.engagement_detail` (`GET /engagements/{engagement_id}`) renders assessment cards, magic links and client uploads, and no report. The plan puts the "Engagement-level integrated report option" under **P3-3**.
- **Client-facing surfaces today:** only `app/routers/magic.py`'s unauthenticated `GET/POST /magic/{token}`. That is a client **upload** page (P2-5), and it shows no report. There is **no client report portal**. The app has no auth ("No auth (single-user MVP)", CLAUDE.md). The consultant downloads a PDF and sends it.
- **Actor convention:** `conclusion_review.reviewer_actor(reviewer_name)` returns `"consultant:" + (name.strip()[:200] or "Manager Review")`, and `REVIEWER_ACTOR_PREFIX = "consultant:"`. `pages/conclusions.html` has a page-level `<input id="reviewer-name" name="reviewer_name">` that action forms pull in with `hx-include="#reviewer-name"`.
- **HTMX error handling** (`app/static/js/app.js`, after P2-4): `htmx:responseError` shows `decodeURIComponent(X-Toast-Message)` as an error toast when the header is present. `app/routers/conclusions.py` has `_toast(response, message, toast_type, *, encoded=False)`, which URL-encodes with `urllib.parse.quote` when `encoded=True`. The legacy `review.approve_assessment` returns JSON with an `HX-Redirect` header on success.
- **Other standing guards this task must not trip:**
  - `tests/test_conclusion_approval.py` scenario 12: the set of routes whose path contains `/conclusions` is exactly five;
  - `tests/test_white_label.py`: no `CyberAssess` literal in `app/templates/`;
  - `tests/test_no_blended_scoring.py`: no `overall_score` in templates or `app/**/*.py` attribute access;
  - `tests/conftest.py::_guard_dev_database_untouched`.

## Decisions (made here so they are not relitigated)

### D-P3-2-A. What a snapshot captures: the exact rendered bytes, written once to a file. Its hash and source manifest go in an audit event.

**Decision:** a snapshot **is the rendered artifact**, meaning the exact PDF or HTML bytes that the live route would have returned at generation time. They are written once to `Path(settings.upload_dir) / snapshot.storage_path` with mode `"xb"`, and **never opened for writing again**. Every later view or download streams those bytes. Nothing re-renders a snapshot, ever.

The row's `storage_path` points at that file. The things the table has no column for go into the `report_snapshot.generated` audit event (D-P3-2-J, exact schema below): the file's `sha256`, its `size_bytes`, and the **source manifest** (the `GapReport` id and every Conclusion's `(id, version)` at generation time).

**How the bytes are obtained (no new rendering code):**
- `gap_report`: call **`reports.download_pdf(assessment_id=assessment.id, db=db)`** as a plain function and take `bytes(response.body)`. The snapshot is therefore, by construction, exactly what the live download returns. It inherits the live route's release gate (403) and "no report" 404 without restating them. And whatever P3-3 changes inside `generate_pdf` flows into every **new** snapshot automatically.
- `workpaper`: `wp = workpaper.build_workpaper(db, assessment)`, then `_templates.get_template("pages/workpaper.html").render(assessment=assessment, wp=wp).encode("utf-8")`. This uses a router-local `Jinja2Templates` configured with `configure_templates`, the same template and the same globals as `web.workpaper_page`, so the bytes equal the live page's body (scenario 7 asserts it). This is the P2-6 hand-forward, "serialize `build_workpaper`'s output, not re-derive it": the template **is** the serialization the reviewer already sees.

**Why rendered bytes and not "a JSON data snapshot, re-rendered on each view":**
1. **Immutability against code changes.** P3-3 is about to rewrite parts of `pdf_export.py`: per-framework executive summary, citations, evidence chain. With render-on-demand, every one of those changes would silently change the PDF of every already-issued report, meaning the document the client received. That is precisely the "does not overwrite an issued artifact" failure PR-054 names. Frozen bytes are immune to renderer changes.
2. **Verifiability.** fpdf2 output isn't byte-deterministic (no fixed creation date; see Current state). Re-rendering even the same data can't be checked against a hash. Stored bytes can, on every read (D-P3-2-E).
3. **No reconstruction layer.** `generate_pdf` takes live ORM objects (`GapReport`, `GapItem`, `Initiative`). Rebuilding those from JSON would be a second data model that must track every field P3-3 adds. `build_workpaper`'s result holds ORM objects too.
4. **No schema change.** Storing content in the DB would need a new column. The model already says "a file at `storage_path`".

**What the manifest is for (PR-054 "bound to the exact approved Conclusion set"):** the audit event records `source.gap_report_id` (the `GapReport` the bytes were rendered from) and `source.conclusion_versions` (every Conclusion of the assessment as `[id, version]`, sorted by id). `Conclusion.version` increments on every proposal and every human decision (P2-3/P2-4), so `(id, version)` pins each Conclusion's exact state, approved or not. The list page shows "Source data changed since generation" when the current manifest differs (D-P3-2-F). **Accepted limitation, named:** the gap-report PDF body is still rendered from `GapItem`, not from Conclusions. That's the reader migration, P2-3 open question 1. So the manifest binds the snapshot to the Conclusion state that existed alongside it, not to a Conclusion-sourced rendering. It is recorded now so that no issued snapshot ever lacks its binding.

**Accepted consequence for `html` snapshots:** the stored workpaper HTML links `/static/css/*.css`, `/static/js/app.js` and the unpkg htmx script. A later stylesheet change can alter how an old snapshot **looks**. It can never alter a word of what it **says**. Inlining assets is out of scope (open question 3).

### D-P3-2-B. Storage convention, write-once, and cleanup on failure

- **Path (exact):** `storage_path_for(snapshot_id=, fmt=, assessment_id=None, engagement_id=None)` returns
  - `f"reports/assessments/{assessment_id}/{snapshot_id}.{fmt}"` when `assessment_id` is given (`gap_report`, `workpaper`);
  - `f"reports/engagements/{engagement_id}/{snapshot_id}.{fmt}"` when only `engagement_id` is given (reserved for P3-3's `integrated_report`);
  - `ValueError` otherwise.

  It is relative to `settings.upload_dir`, like evidence, and built **only from server-generated UUIDs** and the fixed format. No user input reaches the path. The whole tree is inside `upload_dir`, so `scripts/backup.py` already backs it up with the database. No backup change is needed, and the smoke test demonstrates it.
- **Write:** `path.parent.mkdir(parents=True, exist_ok=True)`, then `with path.open("xb") as handle: handle.write(content)`. `"xb"` makes a second write to an existing path raise `FileExistsError`. That is the file-level half of "never overwrite". It's the P2-1 `_write_blob` pattern. Write it locally in the new service, and do **not** import the private `evidence._write_blob`.
- **The snapshot id is minted before the write** (`snapshot_id = _new_id()` from `app.models.assessment`), so that the path and the row agree.
- **The write lives in one private helper**, `_write_file(storage_path: str, content: bytes) -> Path`, in the service. It is the only `.open(` in the module.
- **Failure cleanup:** in `create_snapshot`, any exception after the file is written unlinks that file (`path.unlink(missing_ok=True)`) and re-raises. The router doesn't catch that exception, so it surfaces as a server error, and the request's session is discarded uncommitted. If the router's `db.commit()` itself raises, the router calls `db.rollback()`, unlinks the file via `report_snapshots.snapshot_path(snapshot).unlink(missing_ok=True)`, and returns the D-P3-2-D error response with status 500 and the message `"The report version could not be saved. Try again."`. A failed generation therefore leaves neither a row without a file nor a file without a row (scenario 10). These two `unlink` calls are the **only** file removals in this task, and each removes only a file written earlier in the same request, before its row was committed.
- **Empty content** (`len(content) == 0`) raises `InvalidSnapshot("Rendered report was empty; nothing was saved.")` **before** any write.

### D-P3-2-C. The `type` discriminator: three values, two generatable now

```python
SNAPSHOT_TYPES = ("gap_report", "workpaper", "integrated_report")   # plan schema, verbatim
ASSESSMENT_SNAPSHOT_TYPES = ("gap_report", "workpaper")             # generatable in P3-2
FORMAT_BY_TYPE = {"gap_report": "pdf", "workpaper": "html", "integrated_report": "pdf"}
MEDIA_TYPES = {"pdf": "application/pdf", "html": "text/html; charset=utf-8"}
TYPE_LABELS = {"gap_report": "Gap report (PDF)", "workpaper": "Workpaper (HTML)",
               "integrated_report": "Integrated engagement report (PDF)"}
```

| `type` | `format` | Scope columns | Source today | Live counterpart (unchanged) |
|---|---|---|---|---|
| `gap_report` | `pdf` | `assessment_id` = the assessment; `engagement_id` = `assessment.engagement_id` (may be NULL) | `reports.download_pdf` → `pdf_export.generate_pdf` | `GET /api/assessments/{id}/report/pdf` |
| `workpaper` | `html` | as above | `workpaper.build_workpaper` → `pages/workpaper.html` | `GET /assessments/{id}/workpaper` |
| `integrated_report` | `pdf` | `assessment_id` NULL, `engagement_id` = the engagement | **none: P3-3 builds it** | none |

- The values are the plan's `integrated_report`, not "integrated".
- **P3-2 generates only `ASSESSMENT_SNAPSHOT_TYPES`.** A generate request for `integrated_report` or any other value is refused with 400 `InvalidSnapshot`. The issue statement, the file route logic and the storage-path helper are already scope-aware for `integrated_report`, so P3-3 only adds its generator and an engagement-scoped route (D-P3-2-I).
- The **scope** of a snapshot, which is the set of snapshots it is "a version of", is `(type, assessment_id)` when `assessment_id` is set, and `(type, engagement_id)` with `assessment_id IS NULL` otherwise. `engagement_id` is stored on assessment snapshots for P4-4 retention and rollups, but it is **not** part of their scope key: an assessment's versions stay one sequence even if its engagement link changes.

### D-P3-2-D. Lifecycle and routes (exact)

`draft` → `issued`. Nothing else, and nothing reverses.

| Method + path | Handler | Module | Purpose |
|---|---|---|---|
| `GET /assessments/{assessment_id}/snapshots` | `snapshots_page` | `app/routers/web.py`, directly after `workpaper_page` | The "Report versions" page |
| `POST /api/assessments/{assessment_id}/snapshots` | `generate_snapshot` | `app/routers/snapshots.py` (new) | Generate a draft. Form fields `type`, `reviewer_name` |
| `POST /api/assessments/{assessment_id}/snapshots/{snapshot_id}/issue` | `issue_snapshot_route` | `app/routers/snapshots.py` | Issue. Form field `reviewer_name` |
| `GET /api/assessments/{assessment_id}/snapshots/{snapshot_id}/file` | `snapshot_file_route` | `app/routers/snapshots.py` | Stream the stored bytes |

These are the **only** routes this task adds. There is no PUT, PATCH or DELETE, no un-issue, no rename, no "replace file". `app/routers/snapshots.py` defines `router = APIRouter(prefix="/api/assessments", tags=["snapshots"])` and is registered in `app/main.py` with `app.include_router(snapshots.router)` directly after `app.include_router(conclusions.router)`, adding `snapshots` to the `from app.routers import (…)` list in alphabetical position.

**Handler shape.** The two POST handlers are **sync `def`**, with FastAPI `Form` parameters (`type: str = Form("")`, `reviewer_name: str = Form("")`), not `async def` + `_payload`. PDF rendering is CPU-bound and must run in the threadpool, not on the event loop. HTMX sends form-encoded bodies. Blank or missing `type` is a 400 `InvalidSnapshot("Choose a report type to generate.")`, not a 422, so the toast shows.

**Responses (exact):**
- **Success** of generate or issue: `JSONResponse({"snapshot_id": id, "type": type, "is_issued": bool}, status_code=200)` with headers `HX-Redirect: /assessments/{assessment_id}/snapshots`, `X-Toast-Message` ("Draft version generated" or "Version issued") and `X-Toast-Type: success`.
- **Errors:** every error path calls `db.rollback()` first, then returns `JSONResponse({"detail": message}, status_code=code)` with `X-Toast-Message` = `urllib.parse.quote(message)` and `X-Toast-Type: error`.
  - An `HTTPException` raised by `reports.download_pdf` (403 gate, 404 no report) maps to its own `status_code` and `detail`.
  - A `SnapshotError` subclass maps to its `status_code` and `message`.
  - An unknown assessment is `HTTPException(404, "Assessment not found")`, checked first in every handler.
- **File route:** see D-P3-2-G.

**Generate (exact order):**
1. Load the `Assessment`, or 404.
2. Validate that `type in ASSESSMENT_SNAPSHOT_TYPES`, else 400 (`"Unknown report type."` for anything not in `SNAPSHOT_TYPES`, `"Integrated engagement reports are not available yet."` for `integrated_report`).
3. Render (D-P3-2-A). For `gap_report` this is where the release gate applies (inherited 403). `workpaper` has **no** gate at generation, because the live workpaper page has none and a draft is a review aid.
4. `snapshot = report_snapshots.create_snapshot(db, assessment=assessment, snapshot_type=type, content=content, actor=reviewer_actor(reviewer_name))`.
5. `db.commit()`, with the D-P3-2-B commit-failure cleanup.

**Why generation is an explicit POST and `download_pdf` is not turned into the trigger:** a GET that writes rows and files turns every link prefetch, reload or crawler hit into a new "version" and floods the version list. Generation is a deliberate consultant act, so it's a POST.

### D-P3-2-E. Issue: atomic, one-way, newest-only, integrity-checked, release-gated, audited

**Exact order in `issue_snapshot_route`:**
1. Load the `Assessment`, or 404. `snapshot = report_snapshots.load_snapshot(db, assessment_id=, snapshot_id=)`, which raises `SnapshotNotFound` (404, "Report version not found.") when the id is unknown or belongs to another assessment.
2. `require_review_approval(assessment_id, db)`. **Issuing is releasing** (PR-052: exports "remain unavailable until review gates pass"; PR-056: "release"), so both types need it. A 403 maps as in D-P3-2-D.
3. `report_snapshots.issue_snapshot(db, snapshot, actor=reviewer_actor(reviewer_name))`, which does:
   1. **Integrity:** `verify_snapshot_file(db, snapshot)`. The file must exist, and its SHA-256 must equal the `sha256` recorded in the snapshot's `report_snapshot.generated` event. Otherwise it raises `SnapshotIntegrityError` (500, "The stored file for this version is missing or does not match its recorded hash. Nothing was issued."). You never issue bytes that differ from the ones generated.
   2. **The one state change**, a single statement through `db.execute(text(ISSUE_SQL), {"id": snapshot.id})`:
      ```sql
      UPDATE report_snapshots SET is_issued = 1
      WHERE id = :id AND is_issued = 0
        AND NOT EXISTS (
          SELECT 1 FROM report_snapshots AS newer
          WHERE newer.type = report_snapshots.type
            AND newer.rowid > report_snapshots.rowid
            AND (
              (report_snapshots.assessment_id IS NOT NULL AND newer.assessment_id = report_snapshots.assessment_id)
              OR (report_snapshots.assessment_id IS NULL AND newer.assessment_id IS NULL
                  AND newer.engagement_id = report_snapshots.engagement_id)
            )
        )
      ```
      Keep this text exactly as written: it is checked by the structural guards (D-P3-2-K item 2). I verified it against SQLite at `9bcd972`: on two drafts of one scope, it returns rowcount 0 for the older and 1 for the newer; a second issue of the same row returns 0; and other types and the integrated scope are independent. SQLite serializes writers, so the check "is newest and is draft" and the write happen as one statement. There is no read-then-write window for a concurrent generate or issue.
   3. `rowcount != 1` → `db.expire(snapshot)`, re-read, and raise `SnapshotNotIssuable` (409). The message is `"This version is already issued."` if `snapshot.is_issued`, else `"A newer version of this report exists. Issue the newest version, or generate a new one."`.
   4. `db.expire(snapshot)`. Append the `report_snapshot.issued` audit event (D-P3-2-J). `db.flush()`. Return the snapshot.
4. `db.commit()`.

**What issuing locks:** the row's `is_issued` (one-way: no code path in this task ever sets it back, D-P3-2-K) and, through the list page and the file route, the row's standing as the released version. **The content was already frozen at generation**: the bytes are write-once from the moment the draft exists (D-P3-2-A/B). Issuing doesn't freeze anything new. It records that these exact, already-immutable bytes were released. So a later Conclusion change, re-run, approval or P3-3 renderer change **cannot** alter an issued snapshot. It can only make the page show "Source data changed since generation" and invite a new version.

**Why newest-only:** issuing an older draft while a newer one exists almost always means releasing a report the consultant has already superseded. If the older content is truly wanted, the consultant generates again. After an issue, the issued row is the newest in its scope, and generating again creates a newer draft that can be issued in turn. **Several issued versions per scope over time is expected**: each one is a historical release, and the newest issued is the "current" one.

### D-P3-2-F. Regeneration and superseded drafts: derived, no new column

- **Generate always inserts.** `create_snapshot` never queries for or updates an existing row, not even the same assessment's unissued draft. That is the PR-054 fix, and scenario 1 is the plan's test.
- **Prior unissued drafts are kept**, never deleted and never mutated. Their state is **derived**, not stored:

| Derived `state` | Condition | Label on the page (exact) | Issuable |
|---|---|---|---|
| `draft` | not issued, and newest in its scope | `Draft` | yes |
| `superseded_draft` | not issued, and a newer snapshot exists in its scope | `Draft (superseded)` | no |
| `issued` | issued | `Issued`, or `Issued (current)` when it is the newest **issued** row in its scope | no |

- **Recency is insertion order, `rowid`, one definition everywhere** (the issue statement, the list ordering and `sequence`). `generated_at` is display only. `report_snapshots` has a String primary key, so it is a rowid table. Rows are never deleted by this task, so rowid strictly increases with insertion, and there is no clock-skew ambiguity. (Handed forward to P4-4: a purge must not break this. Removing rows never reorders the remaining ones.)
- **Why no `status`/`superseded` column:** "superseded" is a pure function of rowid order and `is_issued`. Storing it would be a second source of truth that must be updated on every generate, which is a mutation of older rows that the append-only model forbids. It would also be a schema change (Alembic revision, head bump, and the four lockstep test files P2-3 had to edit), which `tasks/agent-ownership.md` treats as foundational. It isn't needed.
- **`sequence`**: each row's 1-based position within its scope, oldest first, rendered as `v{{ sequence }}`.
- **`source_changed`**: `True` iff the snapshot's recorded `source` differs from `source_manifest(db, assessment)` now. Display only. It never blocks an issue, because the consultant is releasing the exact bytes they reviewed, and the page makes the drift explicit.
- **Clutter:** drafts accumulate. That is accepted: they are small, and they are the audit trail of what was generated. Removing them is P4-4's retention concern, not this task's.

### D-P3-2-G. Read paths: the live routes stay live; snapshots are served only from stored bytes

- **`GET /api/assessments/{id}/report/pdf` (`download_pdf`) is unchanged, byte for byte**, and `app/routers/reports.py` is **not modified**. It stays the consultant's live, unversioned working view. It still requires the release gate, still renders from current data, and **writes no snapshot**.
  - *Why not make it serve the latest issued snapshot:* that would silently change a route's meaning. It would 404 or show a stale report for every assessment with no issued version, break the working flow the three UI links rely on, and mix the "current data" and "released document" meanings in one URL. The two views are kept apart, as in D-P2-3-A.
  - *Why not make it generate:* D-P3-2-D.
- **The UI makes the distinction visible** (template-only):
  - in `pages/assessment.html` and `partials/analysis_complete.html`, change the link text `Download PDF` to `Live PDF`;
  - in `partials/report_summary.html`, change `PDF Report` to `Live PDF`;
  - next to each of the three links, add `<a href="/assessments/{{ <that template's existing assessment-id expression> }}/snapshots" …>Report versions</a>`, styled like its neighbour. Use `assessment.id` in `assessment.html`, and `assessment_id` in the two partials, exactly as each template's existing PDF link does. In `report_summary.html` the link also needs `onclick="event.stopPropagation()"`, like its neighbours inside `<summary>`.

  Change nothing else in those files.
- **`snapshot_file_route`** is the only way to read a snapshot's content:
  1. Assessment 404. Then `load_snapshot` → 404.
  2. `content = report_snapshots.read_snapshot_bytes(db, snapshot)`. It reads the file **once**, hashes those bytes, and raises `SnapshotIntegrityError` (500) when the file is missing or the hash differs from the generated event. Only the verified bytes are returned, so there is no second read that could differ.
  3. Return `Response(content=content, media_type=MEDIA_TYPES[snapshot.format])` with header `X-Snapshot-Sha256: <hex>`.
     - For `pdf`, also `Content-Disposition: attachment; filename="{safe_company}_{type}_v{sequence}_{snapshot.id[:8]}.pdf"`, where `safe_company = re.sub(r"[^A-Za-z0-9._-]+", "_", assessment.company_name).strip("_") or "report"`. `sequence` is computed the same way as on the page (D-P3-2-F).
     - For `html`, no `Content-Disposition`, so it renders inline.
  - **No release gate on reading.** Drafts must be readable for review, and they exist only because generation was allowed. An **issued** snapshot must stay retrievable even if `review_status` later changes (for example after a legacy reject), because it was released and is the record of what the client received. Anyone who can reach the app can already read everything (no auth).
  - A snapshot is **never re-rendered**. If its file is gone, the answer is a 500 integrity error, not a quiet regeneration.

### D-P3-2-H. "Client-visible" is a status today, not a surface

The plan says an issued snapshot "becomes … client-visible". **There is no client report surface today**, and this task does not build one:
- The only client-facing route is P2-5's magic-link **upload** page (`/magic/{token}`, `app/routers/magic.py`), which shows no reports.
- There is no auth. The consultant delivers reports out of band.

So in P3-2, "client-visible" means **"released for delivery to the client"**. `is_issued = true` is the flag, and `Issued (current)` on the page tells the consultant which file to send. **Handed forward, binding on any future client surface** (a portal, an email share, a magic-link report view): it must list only rows with `is_issued = true`, and must serve content only through `report_snapshots.read_snapshot_bytes` (the hash-checked stored bytes), never through a live route.

### D-P3-2-I. Boundary with P3-3, and engagement scope

- **`app/utils/pdf_export.py` is out of scope and is not modified.** That includes its rendering internals, `generate_pdf`'s signature, and any new section (CLAUDE.md: "PDF sections are additive-only"; `tasks/agent-ownership.md`: PDF content is P3-3). P3-2 only wraps the snapshot lifecycle around whatever `download_pdf` returns. **`app/routers/reports.py` is not modified either.**
- **P3-3 content changes need no P3-2 rework**: new gap-report snapshots call `download_pdf`, so they pick up P3-3's PDF automatically. Snapshots generated before P3-3 keep their old bytes forever, which is the point.
- **Engagement-level integrated reports are P3-3's to generate.** P3-2 reserves the `integrated_report` type, its `pdf` format, its scope (`assessment_id NULL`, `engagement_id` set), its storage path (`storage_path_for(engagement_id=…)`), and makes the issue statement handle that scope. P3-2 adds **no** engagement route, no engagement page link and no integrated renderer. P3-3 adds an engagement-scoped generator (a sibling of `create_snapshot` reusing the same private write-and-record helper), an engagement-scoped loader, and routes that don't contain `/snapshots` under `/api/assessments`, **or** it extends this task's route-set guard in the same PR.

### D-P3-2-J. Audit events hold the hash, the manifest and the release record (D2). No schema change.

The row has no hash or issued-at/by columns. Rather than adding them (a migration, a head bump, and lockstep edits to four test files), this task uses the generic append-only `audit_events` table exactly as D2 intends: "Normalize later if query needs emerge" (open question 1).

**`report_snapshot.generated`**, written by `create_snapshot` in the same transaction as the row: `actor` = `reviewer_actor(reviewer_name)`, `entity_type="report_snapshot"`, `entity_id=snapshot.id`, and `metadata_json = json.dumps(meta, sort_keys=True)` with **exactly** these keys:

```jsonc
{
  "schema_version": 1,
  "type": "gap_report",
  "format": "pdf",
  "storage_path": "reports/assessments/<assessment_id>/<snapshot_id>.pdf",
  "sha256": "<64 lowercase hex of the stored bytes>",
  "size_bytes": 13068,
  "assessment_id": "<id>",
  "engagement_id": "<id>" | null,
  "review_status": "approved" | "<other>" | null,    // assessment.review_status at generation
  "source": {
    "gap_report_id": "<GapReport.id>" | null,         // the assessment's GapReport now, or null
    "conclusion_versions": [["<conclusion_id>", 3], ...]   // every Conclusion of the assessment, sorted by id
  }
}
```

**`report_snapshot.issued`**, written by `issue_snapshot` after the successful UPDATE: same actor convention, same entity, and metadata with exactly `{"assessment_id", "engagement_id", "sha256", "type"}`. `sha256` is the verified hash.

- One generated event per snapshot, one issued event per issued snapshot. Scenario 3 asserts that a refused second issue writes no second event.
- Metadata holds identifiers, hashes and versions only. It never holds report text (PRD: "Audit logs must avoid duplicating confidential evidence content").
- `source_manifest(db, assessment) -> dict` returns `{"gap_report_id": …, "conclusion_versions": […]}` and is the only function that builds `source`. It is used both at generation and for `source_changed`, so the two can't drift.
- The "generated by", "issued by" and "issued at" shown on the page come from these events. `actor_display` strips the `consultant:` prefix, the same rule as P2-4/P2-6, and the raw prefix is never rendered.

### D-P3-2-K. Consistency audit of this spec (the P2-4 lesson, done in advance)

P2-4's handoff mandated a field whose name its own grep forbade. Every mandated string, statement and label in this document has been checked against every structural assertion below and against the existing standing guards:

1. **Route-set guards.** No new path contains `/workpaper` (P2-6 scenario 9) or `/conclusions` (P2-4 scenario 12). The value `workpaper` travels only in the POST **body** (`type=workpaper`), never in a path. The new guard (scenario 12) expects exactly the four `/snapshots` routes in D-P3-2-D, including the `web.py` page, whose path also contains `/snapshots`.
2. **`is_issued` one-way guard vs mandated code.** The guard forbids, in `app/services/report_snapshots.py` and `app/routers/snapshots.py`:
   - the regex `\.is_issued\s*=(?!=)` (any attribute assignment);
   - the regex `SET\s+is_issued\s*=\s*0` (case-insensitive);
   - the literal `update(ReportSnapshot` (no ORM bulk update).

   Checked against what is mandated:
   - `ISSUE_SQL` contains `SET is_issued = 1`, which is not forbidden, and `AND is_issued = 0` in its `WHERE`, which has no preceding `SET` and no preceding `.`. Its column references `report_snapshots.type`, `.rowid`, `.assessment_id` and `.engagement_id` never qualify `is_issued`. **Do not write `report_snapshots.is_issued` anywhere.**
   - `create_snapshot` constructs `ReportSnapshot(..., is_issued=False)`. That's a keyword argument with no preceding `.`, so it doesn't match.
   - Reads such as `snapshot.is_issued` or `if row.snapshot.is_issued:` have no `=`, and comparisons `.is_issued ==` are excluded by `(?!=)`.
   - No dataclass field may be named `is_issued` (the page row uses `is_current_issue`, which the regex doesn't match, because `is_issued` is not a prefix of it).
3. **Write-once guard.** In the service: `source.count(".open(") == 1`, and that one call is `.open("xb")`. There is no `write_bytes(`, `write_text(`, `"wb"`, `'wb'`, `"ab"` or `'ab'`. Reads use `path.read_bytes()`, which isn't forbidden.
4. **Removal guard.** Neither new module contains the word `delete` (case-insensitive), **comments and docstrings included**. The page's wording is "superseded", never "deleted". `.unlink(` occurs exactly **once** in the service (the `create_snapshot` failure path) and exactly **once** in the router (the commit-failure path). Nothing else may call it, so an issued file can never be unlinked by this task's code.
5. **Commit guard.** `.commit(` does not occur in the service (the router owns transactions, the P2-1/P2-4 rule). It does occur in the router.
6. **Untouched files.** `git diff --stat main -- app/routers/reports.py app/utils/pdf_export.py app/services/workpaper.py app/services/conclusion_review.py app/models alembic/versions` is empty (Done criteria). So `test_legacy_consumers_do_not_read_the_new_tables` is unaffected: the snapshot router imports `reports`, but no new text is added to `reports.py`.
7. **Exact-text assertions vs escaping.** No mandated label or message contains `&`, `<`, `>`, `"` or `'`. That covers the state labels, the toasts, the error messages, the confirm text in D-P3-2-L and `TYPE_LABELS`. `Draft (superseded)` and `Issued (current)` contain only parentheses. Test data uses plain alphanumerics except in the escaping scenario.
8. **Counted attributes.** `data-snapshot-row` appears only on each row's `<tr>`, so its count equals the number of snapshots. The "Issue" control carries `data-issue-control` and appears only on issuable rows, so its count is the number of issuable rows: at most one per type.
9. **Existing template guards.** No `CyberAssess` literal (white-label). No `overall_score`. The page title uses `assessment.company_name`. The workpaper templates are **not modified**, so P2-6's no-form regex is untouched. The snapshot **page** has forms and buttons, and it is a different file that no guard covers.
10. **Toast encoding.** Error toasts are URL-encoded (`quote`), because `app.js` decodes them. Tests compare `unquote(response.headers["X-Toast-Message"])` with the message.
11. **Actor prefix.** `"consultant:Priya"` never appears in the rendered page (scenario 13). No mandated copy contains the lowercase `consultant:`.

### D-P3-2-L. The page: `pages/report_snapshots.html`

It extends `base.html`. Context: `assessment`, `groups` (from `snapshot_rows`), and `reviewer_name` (the prefix-stripped actor of the assessment's most recent `report_snapshot.*` audit event whose actor starts with `consultant:`, else `""`).
- `{% block title %}Report versions — {{ assessment.company_name }}{% endblock %}`, and the breadcrumb `Assessments / {{ assessment.company_name }} / Report versions` in the `pages/workpaper.html` style.
- `<h1>` "Report versions". Subtitle: "Generating creates a new draft version and never overwrites an earlier one. Issuing releases the newest draft for delivery to the client and makes it permanent."
- Links: "Live report →" (`/assessments/{{ assessment.id }}?tab=report`) and "Workpaper (live) →" (`/assessments/{{ assessment.id }}/workpaper`).
- The page-level `<input id="reviewer-name" name="reviewer_name" placeholder="Your name" value="{{ reviewer_name }}">`.
- One `<section data-snapshot-type="{{ type }}">` per `ASSESSMENT_SNAPSHOT_TYPES` entry, in that order. Each has:
  - `<h2>` `{{ type_labels[type] }}`. `snapshots_page` passes `type_labels=report_snapshots.TYPE_LABELS` in the context.
  - A generate form: `<form hx-post="/api/assessments/{{ assessment.id }}/snapshots" hx-include="#reviewer-name">` with `<input type="hidden" name="type" value="{{ type }}">` and a submit button "Generate new version".
  - For `gap_report` only, when `assessment.review_status != "approved"`, the note "Generating a gap report requires the report to be approved for release." The button stays enabled, because the server enforces the gate and the toast explains it.
  - The empty state "No versions generated yet." when the group is empty.
  - Otherwise a table, **newest first**, one `<tr data-snapshot-row data-snapshot-id="{{ row.snapshot.id }}" data-snapshot-state="{{ row.state }}">` per row. The columns are:
    - `v{{ row.sequence }}`;
    - the state label (D-P3-2-F);
    - generated at, and generated by;
    - issued at, and issued by (blank for drafts);
    - the SHA-256 as its first 12 characters, with the full hash in a `title` attribute;
    - the size in KB;
    - the text "Source data changed since generation" when `row.source_changed`;
    - a link to `/api/assessments/{{ assessment.id }}/snapshots/{{ row.snapshot.id }}/file`, labelled "Download" for `pdf` and "View" for `html`;
    - for issuable rows only, `<form data-issue-control hx-post="/api/assessments/{{ assessment.id }}/snapshots/{{ row.snapshot.id }}/issue" hx-include="#reviewer-name" hx-confirm="Issue this version? Issued versions are permanent and cannot be changed or withdrawn.">` with a submit button "Issue".
- Everything is autoescaped. **Never use `|safe`.**

## Required approach

### 1. `app/services/report_snapshots.py` (new): public API, exact

Module docstring (it passes the D-P3-2-K guards): `"""Report snapshots (P3-2): write-once rendered report versions with a one-way draft-to-issued lifecycle. Never re-renders, never overwrites, never un-issues."""`

It never commits, never logs report content (ids, types, sizes and hashes only), and names its Session parameter `db`.

```python
SNAPSHOT_TYPES, ASSESSMENT_SNAPSHOT_TYPES, FORMAT_BY_TYPE, MEDIA_TYPES, TYPE_LABELS   # D-P3-2-C
AUDIT_ENTITY_TYPE = "report_snapshot"
GENERATED_ACTION = "report_snapshot.generated"
ISSUED_ACTION = "report_snapshot.issued"
MANIFEST_SCHEMA_VERSION = 1
ISSUE_SQL = """…"""                     # D-P3-2-E, verbatim

class SnapshotError(Exception):
    status_code = 400
    def __init__(self, message: str): self.message = message; super().__init__(message)
class InvalidSnapshot(SnapshotError): status_code = 400
class SnapshotNotFound(SnapshotError): status_code = 404
class SnapshotNotIssuable(SnapshotError): status_code = 409
class SnapshotIntegrityError(SnapshotError): status_code = 500

def storage_path_for(*, snapshot_id: str, fmt: str, assessment_id: str | None = None,
                     engagement_id: str | None = None) -> str: ...                  # D-P3-2-B
def snapshot_path(snapshot: ReportSnapshot) -> Path: ...     # Path(settings.upload_dir) / snapshot.storage_path
def source_manifest(db: Session, assessment: Assessment) -> dict: ...               # D-P3-2-J
def create_snapshot(db: Session, *, assessment: Assessment, snapshot_type: str,
                    content: bytes, actor: str) -> ReportSnapshot: ...
def load_snapshot(db: Session, *, assessment_id: str, snapshot_id: str) -> ReportSnapshot: ...
def generated_event(db: Session, snapshot_id: str) -> dict: ...   # parsed metadata; SnapshotIntegrityError if absent
def read_snapshot_bytes(db: Session, snapshot: ReportSnapshot) -> bytes: ...        # D-P3-2-G
def verify_snapshot_file(db: Session, snapshot: ReportSnapshot) -> None: ...        # = read_snapshot_bytes, discarding the bytes
def issue_snapshot(db: Session, snapshot: ReportSnapshot, *, actor: str) -> ReportSnapshot: ...

@dataclass(frozen=True)
class SnapshotRow:
    snapshot: ReportSnapshot
    sequence: int                  # 1-based within its scope, by rowid
    state: str                     # "draft" | "superseded_draft" | "issued"
    is_current_issue: bool         # issued, and the newest issued row in its scope
    issuable: bool                 # state == "draft"
    sha256: str | None             # from the generated event
    size_bytes: int | None
    generated_by: str | None       # actor_display
    issued_by: str | None
    issued_at: datetime | None     # the issued event's created_at
    source_changed: bool

def snapshot_rows(db: Session, assessment: Assessment) -> dict[str, list[SnapshotRow]]: ...
    # keys: ASSESSMENT_SNAPSHOT_TYPES, in order; each list newest first
```

- **`create_snapshot`** does this in order:
  1. Validate `snapshot_type in ASSESSMENT_SNAPSHOT_TYPES` (`InvalidSnapshot`) and non-empty `content`.
  2. `snapshot_id = _new_id()`, `fmt = FORMAT_BY_TYPE[snapshot_type]`, `storage_path = storage_path_for(snapshot_id=…, fmt=…, assessment_id=assessment.id)`.
  3. `digest = hashlib.sha256(content).hexdigest()`, and `manifest = source_manifest(db, assessment)`. Build the manifest **before** the write, so a query failure writes nothing.
  4. Write the file (D-P3-2-B).
  5. Then, inside `try:`, add `ReportSnapshot(id=snapshot_id, assessment_id=assessment.id, engagement_id=assessment.engagement_id, type=snapshot_type, format=fmt, storage_path=storage_path, is_issued=False)` and the generated event via a private `_record_event(db, *, actor, action, snapshot_id, metadata)`, then `db.flush()`.
  6. `except Exception:` unlink the file and re-raise.
- **`source_manifest`** runs two SELECTs: the assessment's `GapReport.id` (`.first()`, or `None`), and `select(Conclusion.id, Conclusion.version).where(Conclusion.assessment_id == assessment.id).order_by(Conclusion.id)` as a list of `[id, version]` lists.
- **`snapshot_rows`** runs one SELECT for the assessment's snapshots ordered by `literal_column("report_snapshots.rowid")`, one SELECT for their `audit_events` (`entity_type == AUDIT_ENTITY_TYPE`, `entity_id IN …`), and one `source_manifest`. It **does not hash files**. The list page stays cheap, and hashing happens on read and issue.
- `_record_event` is the only writer of `AuditEvent` in this module, and it is the test seam for scenario 10.

### 2. `app/routers/snapshots.py` (new)

- The router and the three API routes (D-P3-2-D/E/G).
- A module-local `_templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")` followed by `configure_templates(_templates)`, as `app/routers/conclusions.py` does.
- `_render(db, assessment, snapshot_type) -> bytes` (D-P3-2-A). Import the modules, not the functions (`from app.routers import reports`, `from app.services import workpaper, report_snapshots`), so that tests' monkeypatches of `app.routers.reports.generate_pdf` and of the service are seen.
- `from app.services.conclusion_review import reviewer_actor`, and `from app.utils.review_gate import require_review_approval`.
- A local `_error(status_code, message)` builds the D-P3-2-D error response.

### 3. `app/routers/web.py`: `snapshots_page` (D-P3-2-L), directly after `workpaper_page`

It uses `db.get(Assessment, …)` → 404 `"Assessment not found"`, `groups = report_snapshots.snapshot_rows(db, assessment)` and `reviewer_name`, and renders with `templates.TemplateResponse(request=request, name="pages/report_snapshots.html", context={…})`. It never commits. Import the module: `from app.services import report_snapshots`.

### 4. `app/main.py`

Add `snapshots` to the router import list, and add `app.include_router(snapshots.router)` after `conclusions.router`.

### 5. Templates

- `app/templates/pages/report_snapshots.html` (new).
- The three link edits in D-P3-2-G. Nothing else.

### 6. `tasks/todo.md`

- If the P2-6 line still says "PR #29, open, not yet merged", change it to **Merged: PR #29** and update the Phase 2 summary line to match.
- Add a P3-2 line under Phase 3 with its status and a link to this handoff's Results.

If P3-1's session has already made the P2-6 edit, leave it.

### 7. `tests/test_report_snapshots.py` (new)

Copy (don't import) from `tests/test_workpaper.py`:
- the Alembic-built `db_path` / `engine` / `db` fixtures and the `http` `TestClient` fixture;
- `_register_frameworks`, `gate`, `_seed`, `_item`, `_stub_single` and `_run_one`;
- `REQS`, and the helpers needed to call the P2-4 approve route.

Add an **autouse** `upload_root` fixture exactly like `tests/test_evidence_service.py`'s: `monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))`. **No test may write under the real `uploads/`.**

Add a `fake_pdf` fixture that monkeypatches `app.routers.reports.generate_pdf` with a counter-based fake returning `f"%PDF-1.4\n% fake gap report {n}\n".encode()` for call n = 1, 2, …. This makes bytes deterministic and distinct per render, and avoids fpdf2's non-deterministic output. Produce a `GapReport` and Conclusions through the real pipeline (`gate.trigger_analysis`), then set `assessment.review_status = "approved"` and commit, unless the scenario tests the gate.

Every scenario below is one or more test functions whose docstrings start with `Scenario N:`.

## Key files

| File | Why it matters |
|---|---|
| `app/services/report_snapshots.py` (new) | Storage, manifest, lifecycle and integrity (D-P3-2-A…F, J). |
| `app/routers/snapshots.py` (new) | Generate, issue and file routes; rendering by reuse (D-P3-2-A, D, E, G). |
| `app/routers/web.py` | `snapshots_page`. |
| `app/main.py` | Router registration. |
| `app/templates/pages/report_snapshots.html` (new) | The Report versions page (D-P3-2-L). |
| `app/templates/pages/assessment.html`, `partials/analysis_complete.html`, `partials/report_summary.html` | Link text and "Report versions" links only (D-P3-2-G). |
| `app/routers/reports.py`, `app/utils/pdf_export.py` | **Not modified** (D-P3-2-G/I). |
| `app/services/workpaper.py`, `app/services/conclusion_review.py`, `pages/workpaper.html`, `components/workpaper_entry.html` | Reused; **not modified**. |
| `app/models/*`, `alembic/versions/*` | **Not modified.** No schema change (D-P3-2-F/J). |
| `tests/test_report_snapshots.py` (new) | The contract. **No existing test file is modified.** |

## Non-goals

- **No change to `pdf_export.py` or `reports.py`** (P3-3; D-P3-2-I). No PDF content, section, score, citation or evidence-chain change.
- **No integrated/engagement report generation**, and no engagement route or link (P3-3; D-P3-2-I).
- **No schema change and no Alembic revision.** No hash, status, issued-at or issued-by column (D-P3-2-F/J; open question 1).
- **No un-issue, withdraw, delete, archive, rename or replace** of any snapshot or file. No retention or purge (P4-4).
- **No client portal or client link to reports** (D-P3-2-H).
- **No RFI snapshots.** PR-054 names RFIs, but the plan's P3-2 lists only workpapers, gap reports and integrated reports (open question 2).
- **No change to the live workpaper page or the P2-4/P2-6 services.** No Findings or Actions (P3-1), no `relationship()`.
- No inlining of CSS or JS into HTML snapshots (open question 3). No auto-generation on approve or on analysis.

## Test scenarios

All in `tests/test_report_snapshots.py`. **"Nothing written"** means all of these are unchanged: `COUNT(*)` of `report_snapshots` and of `audit_events`; every snapshot's `(id, is_issued, storage_path, generated_at)`; and the set of files under `upload_root / "reports"`.

1. **Generate, issue, regenerate (the plan's test).**
   - `POST /api/assessments/{id}/snapshots` with `type=gap_report, reviewer_name=Priya` returns 200, with `HX-Redirect` equal to `/assessments/{id}/snapshots` and body `is_issued` false.
   - One row: `type == "gap_report"`, `format == "pdf"`, `is_issued` false, `engagement_id == assessment.engagement_id`, and `storage_path == f"reports/assessments/{id}/{snapshot.id}.pdf"`.
   - The file exists under `upload_root` with the bytes of fake render 1.
   - `POST …/{sid}/issue` returns 200, and `is_issued` is true.
   - Generating again returns 200. There are **two** rows and two distinct files. The first is still issued, and its file bytes and `sha256` are still render 1's. The second is a draft with render 2's bytes.
   - `GET …/{first}/file` returns render 1's bytes, `application/pdf`, and `X-Snapshot-Sha256` equal to `sha256(render 1)`.
2. **Regeneration never overwrites a draft, and only the newest draft is issuable.**
   - Generate three times without issuing: three rows. Their `snapshot_rows` states newest-first are `["draft", "superseded_draft", "superseded_draft"]`, with sequences `[3, 2, 1]`.
   - Issuing v1 returns 409 with the "newer version" message (compare with `unquote` on the toast), and nothing is written.
   - Issuing v3 returns 200.
   - Then generate v4 and issue it. v3 and v4 are both issued, and only v4 has `is_current_issue`.
3. **Issue is one-way and single.**
   - Issuing an already-issued row returns 409 "This version is already issued.", `is_issued` stays true, and there is still exactly one `report_snapshot.issued` event for it.
   - Calling `report_snapshots.issue_snapshot` directly on it raises `SnapshotNotIssuable`.
   - The D-P3-2-K items 2–5 source guards pass on both new modules.
4. **Issued snapshot unchanged by later data changes.** After issuing v1:
   - approve a Conclusion through the P2-4 route, and re-run the analysis with a different stub verdict;
   - `GET …/{v1}/file` still returns render 1's bytes, and the file's `sha256` equals the generated event's;
   - `snapshot_rows` marks v1 `source_changed` True;
   - a freshly generated v2 has a different `source.conclusion_versions` and `source.gap_report_id` from v1's event.
5. **Integrity check.**
   - Overwrite a draft's file bytes on disk (test-only `write_bytes`). `GET …/file` returns 500 with the integrity message, and `issue` returns 500 with nothing written (the row stays a draft).
   - Remove another draft's file. `GET …/file` returns 500.
6. **Release gate.** With `review_status` `"pending"` (or NULL):
   - `generate type=gap_report` returns **403** with the `require_review_approval` message in `unquote(X-Toast-Message)`, and nothing is written;
   - `generate type=workpaper` returns 200 (no gate);
   - issuing that workpaper draft returns 403, and nothing is written.
   - After setting `review_status = "approved"`, the issue returns 200.
   - With no `GapReport` at all (a seeded, unanalysed assessment, approved), `generate type=gap_report` returns 404 "No report found. Run analysis first.", and nothing is written.
7. **Workpaper snapshot equals the live page, then stays frozen.**
   - `generate type=workpaper` gives `format == "html"` and path `…/{sid}.html`.
   - The file's bytes, decoded as UTF-8, **equal** `http.get(f"/assessments/{id}/workpaper").text` taken right after, with no data change in between.
   - `GET …/file` returns `text/html; charset=utf-8` and no `Content-Disposition`.
   - Then `approve` a Conclusion. The live workpaper page now shows `data-decision-state="approved"`, while the snapshot bytes are unchanged and don't contain it.
8. **Audit records.**
   - The generated event's `json.loads(metadata_json)` key set equals the D-P3-2-J set exactly. Its `sha256`, `size_bytes` and `storage_path` match the file and the row. `source.conclusion_versions` equals `[[c.id, c.version] …]` sorted by id from the DB. `source.gap_report_id` equals the assessment's `GapReport.id`. Its `actor` is `"consultant:Priya"`.
   - The issued event's metadata key set is exactly `{"assessment_id", "engagement_id", "sha256", "type"}`.
   - A blank `reviewer_name` gives the actor `"consultant:Manager Review"`.
9. **Validation and scoping.** Each of these writes nothing:
   - `type` missing, `type=bogus` and `type=integrated_report` each return 400, with their exact messages;
   - an unknown assessment id returns 404 on all three API routes and on the page;
   - a snapshot id belonging to another assessment returns 404 for `issue` and `file`;
   - an unknown snapshot id returns 404.
10. **Failure cleanup.**
    - Monkeypatch `app.services.report_snapshots._record_event` to raise `RuntimeError("boom")`. The generate POST, made through the default `http` client, raises: wrap it in `pytest.raises(RuntimeError)`. Then call `db.rollback()`. There is no row, **and no file left under `reports/`**.
    - Separately, monkeypatch the test `db`'s `commit` to raise `RuntimeError` once. The generate POST returns 500 with the message `"The report version could not be saved. Try again."`. After `db.rollback()`, there is no row and no file.
    - `storage_path_for` with neither id raises `ValueError`. Calling `report_snapshots._write_file` twice for the same path raises `FileExistsError` on the second call, and the file keeps the first call's bytes.
11. **Integrated scope in the issue statement.** Hand-insert two `integrated_report` rows (`assessment_id` NULL, the same `engagement_id`) plus one for another engagement, with files and generated events built through the same helpers. Then:
    - `issue_snapshot` on the older one raises `SnapshotNotIssuable`;
    - the newer one issues;
    - the other engagement's row issues independently;
    - `storage_path_for(engagement_id=e, …)` is `f"reports/engagements/{e}/{sid}.pdf"`.

    This pins the scope rule P3-3 inherits.
12. **Structural guards.**
    - The set of `(method, path)` app routes whose path contains `/snapshots` equals exactly the four in D-P3-2-D.
    - No route path contains `/snapshots` together with any of `delete`, `unissue`, `withdraw` or `replace`.
    - The D-P3-2-K items 2–5 checks run on the source of `app/services/report_snapshots.py` and `app/routers/snapshots.py`.
    - `inspect.getsource(web.snapshots_page)` contains no `.commit(`.
13. **Page render.**
    - `GET /assessments/{id}/snapshots` with no snapshots returns 200, two `data-snapshot-type` sections, and "No versions generated yet." twice.
    - After scenario 2's sequence (four gap-report versions, two issued):
      - `data-snapshot-row` count 4;
      - `data-issue-control` count 0 (the newest is issued);
      - the labels `Issued (current)`, `Issued` and `Draft (superseded)` all present;
      - each row's file link present;
      - `"consultant:Priya" not in page` and `"Priya" in page`.
    - After one more generate, `data-issue-control` count is 1, on the newest row.
    - The gap-report gate note appears when `review_status != "approved"`.
    - A `company_name` of `<script>x</script>` is rendered escaped.
14. **Live routes unchanged.**
    - With `fake_pdf`, `GET /api/assessments/{id}/report/pdf` returns 200, `application/pdf`, and the next fake render. It creates **no** `report_snapshots` row and no file.
    - `GET /assessments/{id}/workpaper` still returns 200.
    - `pages/assessment.html`, `partials/analysis_complete.html` and `partials/report_summary.html` each contain `/snapshots"` and `Live PDF`, and none contains `Download PDF` or `PDF Report`. Check these as source-text checks on the three files.

## Done criteria

- `tests/test_report_snapshots.py` passes. `.venv/bin/pytest -q` passes in full: **443 + N**, where N is the number of new cases. **No existing test file is modified.** (In a fresh `git worktree`, expect the known one-time `_guard_dev_database_untouched` teardown error described in the P2-3 handoff; nothing else.)
- `git diff --stat main` shows changes **only** in:
  - `app/services/report_snapshots.py`, `app/routers/snapshots.py`, `app/routers/web.py`, `app/main.py`;
  - `app/templates/pages/report_snapshots.html`, `app/templates/pages/assessment.html`, `app/templates/partials/analysis_complete.html`, `app/templates/partials/report_summary.html`;
  - `tests/test_report_snapshots.py`, `tasks/todo.md` and this handoff.
- In particular, `git diff --stat main -- app/routers/reports.py app/utils/pdf_export.py app/services/workpaper.py app/services/conclusion_review.py app/models alembic/versions app/templates/pages/workpaper.html app/templates/components/workpaper_entry.html` is **empty**.
- `alembic heads` is still exactly `4e8c1a9d2b57`. `grep -rn "relationship(" app/models/` is empty.
- **Smoke test** (per the project rule; record the outputs). Use a fresh Alembic-built DB and a temporary `upload_dir`, with the in-process ASGI `TestClient` if a socket bind is refused. Patch `app.routers.analysis.run_gap_analysis` to two fixed items, and use the **real** `generate_pdf`, not the fake. Then:
  1. Run the analysis and set `review_status = "approved"`. `POST …/snapshots type=gap_report`. `GET …/file` returns 200 `application/pdf` and starts with `%PDF`. Record its size and `X-Snapshot-Sha256`.
  2. Issue it. Generate again. Paste `SELECT type, format, is_issued, storage_path FROM report_snapshots WHERE assessment_id = ? ORDER BY rowid` (two rows, the first issued) and `SELECT action, entity_id, actor FROM audit_events WHERE entity_type = 'report_snapshot' ORDER BY rowid` (generated, issued, generated).
  3. `sha256sum` of the first file equals its recorded hash. Re-run the analysis, then re-download v1: identical hash.
  4. `POST …/snapshots type=workpaper`. `GET …/file` returns 200 `text/html` and contains `data-workpaper-entry`.
  5. `GET /assessments/{id}/snapshots` returns 200. Paste the `data-snapshot-state` values.
  6. **Backup coverage:** `scripts.backup.create_backup(db_path, upload_dir, out_dir)` into a temp directory. Show that the backup's `uploads/reports/assessments/{id}/` holds all three snapshot files.
  7. **Browser check**, if a browser is available: generate, issue (confirm dialog shown), and confirm the page shows `Issued (current)`. If no browser is available, say so in Results. Do not claim it.

## Rollback

- **Code:** `git revert`. There's no schema change. Existing `report_snapshots` rows and `audit_events` rows stay as inert history that the reverted app never reads, and snapshot files stay under `upload_dir/reports/`, where backups keep covering them. The live PDF and workpaper routes are unchanged throughout, so nothing depends on this task to keep working.
- **Data:** nothing in this task deletes or rewrites anything. The only in-place write is `is_issued` 0 → 1 through `ISSUE_SQL`, recorded by an `issued` event. **Do not "undo" an issue by editing the row.** An issued report was released, and the record of that release must stay. If an issued version was wrong, generate and issue a corrected newer version. It becomes `Issued (current)`, and the older one remains as history.

## Open questions (deliberately flagged, not resolved here)

1. **Promote hash and issue metadata to columns.** `sha256`, `issued_at` and `issued_by` live in `audit_events` (D-P3-2-J, D2 "normalize later"). If P3-3, P4-4 or a client surface needs to filter on them in SQL, add columns in a dedicated migration, backfilled from the events.
2. **RFI snapshots.** PR-054 says "Generated reports **and RFIs**". The plan's P3-2 names only three types. An `rfi` type would reuse this lifecycle unchanged (source: `web.download_rfi_pdf`). Decide whether it belongs in Phase 3.
3. **Self-contained HTML snapshots.** Workpaper snapshots reference `/static` CSS/JS and the unpkg htmx script (D-P3-2-A). Their content is frozen, but their appearance can drift, and they don't render offline. Inlining the CSS would make them standalone.
4. **Snapshots of un-migrated readers.** Until the reader migration (P2-3 open question 1), gap-report snapshots render from `GapItem`, and are bound to the Conclusion state only by the manifest (D-P3-2-A).

## Handed forward (must be honoured there)

- **P3-3 (PDF updates):**
  - Change `pdf_export.py` freely. New gap-report snapshots pick it up through `reports.download_pdf`, and issued ones never change.
  - Build the integrated report as `type="integrated_report"`, `format="pdf"`, `assessment_id=None`, `engagement_id=<engagement>`, stored at `storage_path_for(engagement_id=…)`, recorded with the same generated-event schema (with `source` extended to list each included assessment's manifest), and issued through `ISSUE_SQL` unchanged.
  - Keep its routes consistent with scenario 12's route-set guard, or extend that guard in the same PR.
  - Never re-render an issued snapshot.
- **Any client-facing surface:** D-P3-2-H. Only `is_issued = true` rows, and only through `read_snapshot_bytes`.
- **P4-4 (retention/purge):** snapshot files live under `upload_dir/reports/`, and rows reference them by `storage_path`. A purge must remove file and row together, must honour legal hold for issued snapshots, and must not rely on `generated_at` for ordering. Recency is `rowid` (D-P3-2-F). Record purges as audit events.

## Results

Implemented P3-2 in full with no deviations from D-P3-2-A through D-P3-2-L.

- Added `app/services/report_snapshots.py`: exclusive-create storage under `upload_dir/reports`, exact source manifests and audit metadata, hash-checked reads, atomic newest-only `ISSUE_SQL`, derived version states and display rows, and reserved engagement scope for P3-3.
- Added the three assessment snapshot API routes and the Report versions page route. Gap snapshots reuse the unchanged live PDF route; workpaper snapshots render the unchanged live workpaper read model/template. Draft and issued files are always served from stored, verified bytes.
- Added `pages/report_snapshots.html` and distinguished the existing live report links from Report versions. No model, migration, live report renderer, PDF renderer, workpaper service or workpaper template changed.
- Added `tests/test_report_snapshots.py` with 14 tests, one for every numbered scenario in this handoff.

Verification:

- `.venv/bin/pytest -q tests/test_report_snapshots.py` → **14 passed**.
- Focused compatibility run (`test_workpaper`, `test_conclusion_approval`, `test_analysis_pipeline`, `test_white_label`, `test_no_blended_scoring`, and the new suite) → **107 passed, 11 warnings**.
- `.venv/bin/pytest -q` → **457 passed, 115 warnings** (443-test baseline + 14 new tests). The documented workpaper teardown artifact did not occur.
- `git diff --check` passed. Alembic head remains exactly `4e8c1a9d2b57`; `app/models/` still contains no `relationship(`; all mandated untouched-file diffs are empty.
- Fresh migrated-DB ASGI smoke with the real PDF renderer: v1 was **12,395 bytes**, started with `%PDF`, and had SHA-256 `40515b0e9fe8b4625d0b8d0e31916cc942064cfa80b2fb54eb4cf218284a54ef`. The same hash was returned after a changed analysis rerun. Snapshot rows were `(gap_report, pdf, issued)` then `(gap_report, pdf, draft)`; audit actions were `generated`, `issued`, `generated`. The workpaper snapshot was **18,740 bytes**, returned `text/html`, and contained `data-workpaper-entry`. The page states were `draft`, `issued`, `draft`. Backup copied both PDFs and the HTML snapshot under the assessment report directory.
- No browser automation was available in this session, so the optional confirm-dialog browser check was not claimed. Page behavior is covered by the ASGI and source-level contract tests.

Deviations: **none**.

Commit status: implementation commits could not be created in this session because the managed sandbox exposes the linked worktree Git directory (`/Users/saqlainmomin/dpdpa-gap-tool/.git/worktrees/dpdpa-gap-tool-p3-2`) as read-only. `git add` failed while creating `index.lock` with `Operation not permitted`. All requested working-tree changes are preserved on `codex/p3-2-report-snapshots`; no push or PR was attempted.
