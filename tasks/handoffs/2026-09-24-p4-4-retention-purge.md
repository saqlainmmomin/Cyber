# P4-4: Retention plumbing: reversible engagement archive, read-only enforcement, configurable per-client retention, and a two-phase, crash-safe permanent purge

**Plan:** `docs/plans/2026-09-21-002-revised-implementation-plan.md`, Phase 4, task P4-4 ("Implement configurable retention per client (D11: `clients.retention_years`, default 7)"; "Archive = soft delete (status = "archived"). Engagement and all children become read-only."; "Permanent purge: only after `retention_years` from archive date. Checks for active dependencies. Deletes DB rows + evidence blobs together. Logs to audit_events."; "Never auto-purge as shipped default. Purge is a manual consultant action with explicit confirmation."; test: "Archive engagement, verify read-only. Attempt purge before retention period, verify rejection. Purge after period, verify DB rows and blobs removed, audit event logged."), and the Phase 4 exit criterion "Retention/archive/purge lifecycle complete". Decision **D11** in `tasks/2026-09-21-adversarial-review.md` ("Configurable per-client. Consultant sets retention period per client or engagement. Default 7 years. Retention-aware soft delete; purge only after expiry. Never auto-purge as shipped default."). PRD `docs/product/2026-09-21-cyberassess-product-requirements.md`: **PR-003** ("archived records leave default views but remain searchable and restorable; permanent deletion requires an explicit confirmation and a retention/dependency preview"), the Engagement lifecycle paragraph ("Archive removes the Engagement from normal portfolio views without destroying records. Permanent deletion requires a dependency and retention check plus explicit confirmation."), the Evidence lifecycle paragraph ("Purge is allowed only after retention, legal-hold, citation, and report-snapshot checks"), and the audit requirement listing "archive, deletion attempts" as attributable and queryable. **Binding hand-forwards** (each closed below): P2-2 (`tasks/handoffs/2026-09-23-p2-2-citation-model.md`, "P4-4 must refuse to purge an `EvidenceVersion` referenced by any `conclusion_revisions.citations_json` or `desk_review_findings.citations_json`, or mark those citations as purged-source. That task's designer must pick one." → D-P4-4-J); P2-1 (`archived` is the D11 soft delete; "P4-4 adds `archived → purged` behind the retention/dependency checks" → D-P4-4-A, D-P4-4-I); P3-2 (`tasks/handoffs/2026-09-23-p3-2-report-snapshots.md`, "A purge must remove file and row together, must honour legal hold for issued snapshots, and must not rely on `generated_at` for ordering. Recency is `rowid`. Record purges as audit events." → D-P4-4-C, D-P4-4-J, D-P4-4-L, D-P4-4-P).

**Owner:** Claude designs → Codex implements → **Claude reviews** (per `tasks/agent-ownership.md`: "P4-4 Retention/archive/purge | Claude designs → Codex implements, Claude reviews (most destructive code path in the plan)"; it meets the ownership criterion "Irreversible or destructive — permanent deletion … e.g. retention purge"). Every fork is closed below: the archive state machine, every write path that must reject, the exact pre-purge checks, the exact deletion order, and the exact failure mode for a crash between the DB step and the blob step.

> **If the code forces a deviation from this design, stop and report it in `## Results`, do not pick an alternative — this task gets a second, more skeptical review before merge specifically because a mistake here is unrecoverable data loss.**

This applies to every numbered decision, every exact constant, message, table list and ordering below, and every test scenario. "The existing code makes step N awkward" is not a licence to redesign step N. Write down what you found, what you would need to change, and stop.

**Depends on:** nothing unmerged. `main` is at `a4ac3d9` (Phases 1–3 merged, PRs #16–#33).
**Blocks:** nothing in Phase 4 (P4-2's demo does not need archive or purge).
**Runs in parallel with:** P4-1 (AWS evidence adapter), P4-2 (longitudinal demo), P4-3 (performance benchmarks). Shared files and the coordination rule are in D-P4-4-U.
**Failing contract suite: none pre-written.** `ls tests/` has no retention/archive/purge suite, and `grep -rniE "retention|purge|archive_engagement|unarchive" tests/` finds only the pre-existing evidence-level archive tests in `tests/test_evidence_service.py` (Evidence `archived` status, unrelated to engagements) and the `retention_years` column assertions in `tests/test_target_schema.py`. **Codex writes `tests/test_retention.py` itself** from `## Test scenarios`, following the fixture pattern of `tests/test_remediation_tracking.py` (step 11). Every scenario listed is required. You may add cases, but you may not drop or weaken one. **No existing test file is modified.** If any existing test fails after your change, stop and report it.

## Review gate (read this before dispatch, and again before any PR is opened)

This task requires an **extra adversarial review pass beyond the standard `[AR]` gate**, per `tasks/agent-ownership.md`'s callout that P4-4 is the most destructive code path in the plan, and per `tasks/handoffs/2026-09-24-phase-4-kickoff.md` step 6 ("P4-4 (retention/purge) needs an extra pass beyond the standard gate … Don't settle for one clean review on this task alone"). Concretely, before `gh pr create`:

1. The standard independent adversarial review of the committed diff (every invariant traced in code, suite re-run independently, active attempts to break it).
2. **A second, separate, more skeptical review** whose brief is only: "find a way to lose data that should not be lost, or to keep data that should have been removed." It must, at minimum, (a) re-derive the purge set from `Base.metadata` and the FK graph and compare it with `PURGE_ORDER`; (b) try to make `_remove_tree` delete anything outside the purge roots (symlinks, `..`, tampered ledger rows, ids with separators); (c) kill the process between phase 1 and phase 2 and confirm recovery; (d) find any mutating route an archived engagement still accepts.
3. Whoever reviews this handoff **before dispatch** should spot-check at least D-P4-4-E's route enumeration and D-P4-4-I's table list against the live code, the way every prior handoff's claims were spot-checked.

Do not merge on one clean review.

## Goal

1. A consultant **archives** an engagement from its page. The engagement leaves the dashboard and the client's engagement list, shows on the client page under "Archived engagements", and it and **everything under it become read-only**: every mutating request that touches the engagement, one of its assessments or one of its evidence items is refused with 409. Reads keep working.
2. A consultant **unarchives** it. It returns to exactly the status it had before archive and is writable again. The retention clock restarts the next time it is archived.
3. A consultant sets a **retention period per client** (1–50 years, default 7).
4. After the retention period has elapsed since the archive date, a consultant opens a **purge preview** that lists exactly what will be deleted and any reason it cannot be, types the engagement name, and **permanently purges** it. The DB rows go in one transaction; then the engagement's stored files go. The act is recorded in `audit_events`, and so is every refused attempt.
5. If the process fails or dies between deleting the rows and removing the files, the system is left in one documented, detectable, resumable state ("records purged, files pending"), never in a state where a row points at a missing file or a file is referenced by nothing at all.
6. Nothing is ever purged automatically.

## Current state

Grounded against `a4ac3d9` on `main`. Baseline in this worktree: `.venv/bin/pytest -q` → **502 passed, 126 warnings, 1 error** (the error is the known, pre-existing fresh-worktree teardown artifact from `tests/conftest.py::_guard_dev_database_untouched`, reported at `tests/test_workpaper.py::test_smoke_full_assessment_traceability`; documented in every Phase 2/3 handoff, not a regression). `alembic heads` → `4e8c1a9d2b57 (head)`. Re-locate everything by symbol name; line numbers drift.

### Hierarchy and statuses

- **`app/models/client.py`, `Client`**: `id`, `name` (unique), `industry`, `size`, **`retention_years: Mapped[int] = mapped_column(Integer, default=7)`** (the P1-2 migration `5c7c75960f43` declares it `nullable=False`), `created_at`, `updated_at` (`onupdate`). `pages/client_detail.html` already renders `{{ client.retention_years }}-year retention`. **No code path writes `retention_years` after creation**, and no UI sets it.
- **`app/models/engagement.py`, `Engagement`**: `id`, `client_id` (FK `clients.id`, `ondelete="RESTRICT"`), `name`, `type`, **`status: Mapped[str] = mapped_column(String(50))`** (no default, no enum, no check constraint), `created_at`, `updated_at` (`onupdate`). There is **no archive-date column** and none is added (D-P4-4-C).
- **Engagement status values in use today** (full grep of `Engagement(` and `.status` across `app/`, `scripts/`, `tests/`):
  - `"active"`: the only value the app writes (`app/services/engagement_factory.py::create_engagement_with_assessment`; `scripts/migrate_legacy.py` also writes `"active"`). Every test fixture uses `"active"`.
  - `"closed"`: **never written** by the app, but read: `web.dashboard` filters `Engagement.status != "closed"`, and so does `web._engagement_cards_for_client` (P1-4 decision: closed engagements are hidden from the dashboard and client list; the engagement page still renders one addressed directly).
  - `app/services/magic_links.py`: `create_link` raises `MagicLinkConflict("Magic links can only be created for active engagements.")` when `engagement.status != "active"`, and `resolve_token` returns `None` (the non-enumerable 404) when `engagement is None or engagement.status != "active"`. **So an archived engagement's magic links are already inert on both GET and POST** with no change.
  - Nothing else branches on `Engagement.status`. The engagement badge (`components/engagement_status_badge.html`) renders `card.derived_status`, which `app/services/portfolio.py::derive_status` computes from assessments, not from `Engagement.status`.
- **Assessment-level soft delete already exists and is separate:** `Assessment.status = "archived"` is set by `web.delete_assessment_web` (`DELETE /assessments/{assessment_id}`) and `assessments.delete_assessment` (`DELETE /api/assessments/{assessment_id}`). It is filtered out by `web.dashboard`, `web._engagement_cards_for_client`, `web.engagement_detail`, `report_content` (integrated report) and `remediation_rollup.engagement_rollup`, and by `portfolio.build_engagement_card`. It has no unarchive route. **This task does not change assessment-level archive** (D-P4-4-A).
- **Evidence-level archive already exists and is separate:** `app/services/evidence.py` `EVIDENCE_STATUSES = ("quarantined", "active", "rejected", "invalidated", "archived")` with `EVIDENCE_TRANSITIONS` including `("active", "archived")` and `("archived", "active")`, each audited as `evidence.status_changed`. Evidence `archived` means "excluded from analysis, blob retained". **This task does not propagate engagement archive into Evidence status** (D-P4-4-D).

### Audit events (the write pattern to match)

- `app/models/audit_event.py`, `AuditEvent`: `id`, `actor` (String 255), `action` (String 100), `entity_type` (String 100), `entity_id` (String 36), `metadata_json` (Text, nullable), `created_at` (default `_utcnow`). No index beyond the PK. It is a rowid table (String PK), so `rowid` strictly increases with insertion.
- **Live writers and their exact shape** (every one uses `db.add(AuditEvent(actor=…, action=…, entity_type=…, entity_id=…, metadata_json=json.dumps(metadata, sort_keys=True)))` and never sets `created_at`):
  - `app/services/evidence.py::_audit`: actions `evidence.created`, `evidence_version.created`, `evidence.status_changed`, `evidence_version.status_changed`, `evidence_use.created`, `evidence_use.deleted`; entity types `evidence`, `evidence_version`, `evidence_use`.
  - `app/services/magic_links.py::_audit`: `magic_link.created`, `magic_link.revoked`, `magic_link.upload_received`; entity type `magic_link`.
  - `app/services/report_snapshots.py::_record_event`: `report_snapshot.generated`, `report_snapshot.issued` (`GENERATED_ACTION`, `ISSUED_ACTION`); entity type `AUDIT_ENTITY_TYPE = "report_snapshot"`.
  - `app/services/findings.py::create_finding`: `FINDING_CREATED_EVENT = "finding_created"`, `FINDING_ENTITY = "finding"` (the one undotted legacy name).
  - **P3-4 writes no audit events** (its D-P3-4-D: "No `audit_events` rows. As in P3-1, `history_json` is the Action's trail"). The kickoff doc's "P3-4's closure/verification events" is inaccurate; the P3-2 and P2-1 writers above are the pattern.
- **Actor convention:** human actors are `conclusion_review.reviewer_actor(reviewer_name)` → `f"{REVIEWER_ACTOR_PREFIX}{name}"` with `REVIEWER_ACTOR_PREFIX = "consultant:"`, blank → `DEFAULT_REVIEWER_NAME = "Manager Review"`, truncated to 200 characters. System actors are `system:<purpose>` (`system:analysis`, `system:scan-placeholder`, `system:migration`). Readers strip the `consultant:` prefix for display.
- **Recency rule:** P3-2 D-P3-2-F: recency is insertion order (`rowid`), "one definition everywhere"; `created_at` is display only. `findings.findings_page` and `report_snapshots` read audit events back as the source of truth for "who created/issued this", so **reading a fact back from `audit_events` is established precedent** in this codebase.

### Blob storage on disk (all under `settings.upload_dir`, default `uploads/`)

- **Evidence** (`app/services/evidence.py`): `blob_path(storage_path) = Path(settings.upload_dir) / storage_path`. `receive_evidence` writes `storage_path = f"evidence/{engagement_id}/{evidence_id}/v1.{ext}"`; `receive_version` writes `f"evidence/{evidence.engagement_id}/{evidence.id}/v{n}.{ext}"`. `Evidence.storage_path` records v1 and is frozen; every `EvidenceVersion.storage_path` records its own file. `Evidence.engagement_id` is NOT NULL. **So every Evidence blob of engagement E lives under `evidence/{E}/`.**
- **Report snapshots** (`app/services/report_snapshots.py::storage_path_for`): assessment snapshots at `reports/assessments/{assessment_id}/{snapshot_id}.{fmt}`, engagement (integrated) snapshots at `reports/engagements/{engagement_id}/{snapshot_id}.{fmt}`; `snapshot_path(snapshot) = Path(settings.upload_dir) / snapshot.storage_path`. Assessment snapshots also store `engagement_id`.
- **Legacy `AssessmentDocument`** (`app/models/assessment.py`): `file_path` (String 500) as written by the retired `save_upload`, i.e. `os.path.join(settings.upload_dir, assessment_id, filename)` (see `tasks/handoffs/2026-09-22-p1-6-backup-restore.md` and `scripts/migrate_documents_to_evidence.py`, which reads `Path(document.file_path)` and `Path(settings.upload_dir) / document.assessment_id / Path(document.file_path).name`). **No code in `app/` constructs `AssessmentDocument` any more** (`tests/test_evidence_service.py::test_no_assessment_document_writers_or_save_upload_in_app`). The legacy per-assessment directory is `upload_dir/{assessment_id}/`. The file name part is client-supplied text.
- **No code in `app/` deletes an Evidence/EvidenceVersion row or a blob** (P2-1 non-goal: "No code in `app/` may delete an `Evidence` or `EvidenceVersion` row or a blob. (… **P4-4**.)"). The only `.unlink(` calls are rollback cleanups of a just-written file (evidence ingestion, `report_snapshots._store`, `integrated_reports.generate_integrated_report`). `shutil.rmtree` appears nowhere in `app/`.

### FK graph (SQLite `PRAGMA foreign_keys=ON` via `app/database.py::set_sqlite_pragma`; test fixtures enable it too)

Every table in `Base.metadata` (23): `clients`, `engagements` (→ clients, RESTRICT), `assessments` (→ engagements, nullable), `assessment_documents`, `questionnaire_responses`, `desk_review_summaries`, `desk_review_findings` (→ assessments; `document_id` → assessment_documents `ON DELETE SET NULL`), `gap_reports`, `rfi_documents`, `analysis_runs`, `assessment_packs`, `conclusions`, `findings` (all → assessments), `gap_items`, `initiatives` (→ gap_reports), `conclusion_revisions` (→ conclusions; `analysis_run_id` → analysis_runs, nullable), `actions` (→ findings), `evidence` (→ engagements; `assessment_id` → assessments, nullable), `evidence_versions` (→ evidence), `evidence_uses` (→ evidence, → assessments), `magic_links` (→ engagements), `report_snapshots` (→ assessments nullable, → engagements nullable), `audit_events` (no FKs). FKs other than the two noted are `NO ACTION` (an out-of-order delete fails the statement). There is no `relationship()` anywhere in `app/models/`.

### JSON references that are not FK-protected

- `conclusion_revisions.citations_json` and `desk_review_findings.citations_json`: arrays of `{"evidence_version_id", "location_type", "location_ref", "excerpt"}` (P2-2).
- `actions.history_json`: P3-4 `closed`/`verified` entries carry `"evidence": {"evidence_id", "evidence_version_id", …}`.
- `audit_events.metadata_json`: ids of all kinds (retained by design, D-P4-4-I).

### Write paths (the enumeration D-P4-4-E is built on)

`app/main.py` includes these routers in this order: `assessments`, `questionnaire`, `documents`, `evidence`, `analysis`, `reports` (+ `reports.comparison_router`), `desk_review`, `review`, `conclusions`, `findings`, `snapshots`, `integrated_reports`, `magic`, `web`. Every mutating route today (method, path, router), grepped from `@router.(post|put|patch|delete)`:

| Resolves to engagement via | Routes |
|---|---|
| `{assessment_id}` | `POST /api/assessments/{assessment_id}/frameworks`, `DELETE /api/assessments/{assessment_id}` (assessments); `POST /api/assessments/{assessment_id}/context`, `POST /api/assessments/{assessment_id}/responses` (questionnaire); `POST /api/assessments/{assessment_id}/documents`, `DELETE /api/assessments/{assessment_id}/documents/{document_id}` (documents); `POST /api/assessments/{assessment_id}/analyze` (analysis); `POST /api/assessments/{assessment_id}/desk-review` (desk_review); `PATCH …/review/items/{item_id}`, `POST …/review/approve`, `POST …/review/reject` (review); `POST …/conclusions/{conclusion_id}/approve|edit|reject|reopen` (conclusions); `POST …/findings`, `…/findings/{finding_id}/actions`, `…/actions/{action_id}/status|update|close|verify|reopen` (findings); `POST …/snapshots`, `POST …/snapshots/{snapshot_id}/issue` (snapshots); and in `web`: `DELETE /assessments/{assessment_id}`, `POST /assessments/{assessment_id}/scope/save`, `…/upload`, `DELETE …/documents/{document_id}`, `POST …/evidence/{evidence_id}/versions`, `…/context/submit`, `…/context/save`, `…/questionnaire/save`, `…/questionnaire/followup`, `…/screening/submit`, `…/run-analysis`, `…/generate-rfi`, `…/run-desk-review` |
| `{engagement_id}` | `POST /api/engagements/{engagement_id}/integrated-reports`, `…/integrated-reports/{snapshot_id}/issue` (integrated_reports); `POST /engagements/{engagement_id}/magic-links`, `…/magic-links/{link_id}/revoke` (magic) |
| `{evidence_id}` | `POST /api/evidence/{evidence_id}/versions`, `…/transitions`, `…/uses`, `DELETE …/uses/{use_id}` (evidence) |
| none (creates a new hierarchy, or is token-scoped) | `POST /engagements`, `POST /assessments`, `POST /assessments/new` (web); `POST /api/assessments` (assessments); `POST /magic/{token}` (magic) |

No GET handler commits, flushes or adds (checked by scanning every router function body). `run_analysis_web` runs analysis **synchronously** after committing `assessment.status = "analyzing"`; `run_desk_review_web` commits `assessment.desk_review_status = "analyzing"` and then runs the LLM call in a `BackgroundTasks` task with its own session.

### Existing structural guards that constrain this task (the P2-4/P3-4 lesson, checked in advance)

- `"delete" not in` the lower-cased source of: `app/services/analysis_pipeline.py`, `app/services/conclusion_review.py`, `app/services/findings.py`, `app/routers/findings.py`, `app/services/remediation_rollup.py`, `app/routers/integrated_reports.py`, `app/services/report_content.py`, `app/services/report_snapshots.py` + `app/routers/snapshots.py`, `app/services/workpaper.py`. **This task edits none of those files.**
- Exact route sets for paths containing `/findings`, `/conclusions`, `/workpaper`, `/snapshots`, `/remediation`, `/integrated-reports`. **None of this task's paths contains any of those substrings** (D-P4-4-O).
- `.unlink(` counts in `report_snapshots.py`, `snapshots.py`, `integrated_reports.py`. Not touched.
- No `CyberAssess` in templates (`tests/test_white_label.py`); no `overall_score` in templates; no `AssessmentDocument(` or `save_upload` in `app/**/*.py`; no `relationship(` in `app/models/`.

### HTMX/response conventions to reuse

- `app/routers/integrated_reports.py::_error(status_code, message)` returns `JSONResponse({"detail": message})` with `X-Toast-Message: quote(message)` and `X-Toast-Type: error`; `_success` returns JSON with `HX-Redirect` and a success toast. `app/static/js/app.js` shows `decodeURIComponent(X-Toast-Message)` on `htmx:responseError` and after swaps, and follows `HX-Redirect`. **The toast is rendered with `innerHTML`**, so a toast message must never contain user-controlled text (D-P4-4-O).
- **Existing destructive-action confirmation pattern is `hx-confirm` only** (`integrated_reports.html` issue, `report_snapshots.html` issue, `document_list.html` archive, `desk_review_findings.html` re-run, `magic_links.html` revoke). There is **no** type-to-confirm pattern anywhere (`grep -rn "hx-confirm\|confirm(" app/templates app/static`). D-P4-4-N adds one, for purge only, on top of `hx-confirm`.
- Reviewer name: forms include `hx-include="#reviewer-name"` pointing at `<input id="reviewer-name" name="reviewer_name">` (conclusions, findings, integrated reports pages).
- **Jinja autoescapes `'` as `&#39;`** (P2-5 lesson): no message that is rendered into HTML contains an apostrophe.

### Compare-and-swap precedent

- `app/services/analysis_pipeline.py::swap_conclusion` (P2-3/P2-4): `update(Conclusion).where(Conclusion.id == …, Conclusion.version == expected_version).values(...).execution_options(synchronize_session=False)`; `rowcount != 1` → `ConclusionConflict`; then `db.expire(conclusion)`.
- `app/services/findings.py::_append` (P3-1/P3-4): the same shape on `Action.history_json == raw`.
- `app/services/report_snapshots.py::issue_snapshot` (P3-2): raw `ISSUE_SQL` with `WHERE … is_issued = 0 AND NOT EXISTS (…)`, `rowcount != 1` → `SnapshotNotIssuable`.

Archive, unarchive, retention changes and the purge's final engagement delete all use this exact shape: a single conditional statement, `rowcount != 1` → conflict (D-P4-4-B, D-P4-4-G, D-P4-4-L).

## Decisions (made here so they are not relitigated)

### D-P4-4-A. The unit of archive and purge is the Engagement. Clients are never archived or purged; assessment- and evidence-level archive are unchanged.

- **Archive and purge act on one Engagement and everything that hangs off it** (its assessments and all of their children, its evidence, its magic links, its report snapshots). This is what the plan says ("Engagement and all children become read-only") and what the PRD models (`Engagement` "records … archive state").
- **The Client row is never archived or purged by this task.** A client can have several engagements, and it is the firm's own relationship record, which also holds the retention setting. Deleting a client is not in scope (open question 4).
- **`Assessment.status = "archived"` (assessment-level soft delete) is not changed, not extended, and not reinterpreted.** It stays "hidden from views". An archived assessment inside an archived engagement is simply part of the engagement's purge set.
- **Evidence `archived` (P2-1) is not changed.** It stays "excluded from analysis, blob retained".

### D-P4-4-B. The Engagement status machine (exact)

```python
ARCHIVED_STATUS = "archived"
ARCHIVABLE_STATUSES = ("active", "closed")
```

| From | To | Operation | Preconditions | CAS statement |
|---|---|---|---|---|
| `active` or `closed` | `archived` | `archive_engagement` | no in-flight work (below) | `UPDATE engagements SET status='archived', updated_at=:now WHERE id=:id AND status=:status_read` |
| `archived` | the `previous_status` recorded by the current archive record, or `active` when there is no valid record | `unarchive_engagement` | none | `UPDATE engagements SET status=:restored, updated_at=:now WHERE id=:id AND status='archived'` |
| `archived` | (row deleted) | `purge_engagement` | D-P4-4-J | `DELETE FROM engagements WHERE id=:id AND status='archived'` (D-P4-4-L) |

- Any other current status (for example a hand-set `"draft"`) cannot be archived: `NOT_ARCHIVABLE`.
- **In-flight work blocks archive:** `COUNT(*)` of assessments with `engagement_id = :id AND (status = 'analyzing' OR desk_review_status = 'analyzing')` must be 0, else `ARCHIVE_IN_FLIGHT`. Both markers are committed before the long-running LLM call starts (`run_analysis_web` sets `status`; `run_desk_review_web` sets `desk_review_status` before scheduling its background task), so a request that is mid-analysis always shows one of them. `AnalysisRun.status == "running"` is **not** used: P2-3 documents that a crashed process leaves runs `running` forever with no sweeper, which would make such an engagement impossible to archive. A stale `analyzing` marker is cleared by re-running analysis or desk review, which the consultant can do before archiving.
- **Unarchive restores the exact prior status** (`active` or `closed`). It is recorded in the archive event's metadata (`previous_status`) and validated against `ARCHIVABLE_STATUSES`; any other or missing value restores `active`.
- **No free-text reason is taken for archive or unarchive.** Audit rows outlive a purge (D-P4-4-I), so anything typed into them would survive the deletion of the engagement it describes. The actor and timestamp are recorded; that is enough.
- **Unarchive is allowed at any time**, including after the retention period has elapsed. Re-archiving creates a new archive record and **restarts the retention clock** (D-P4-4-C). That is intended: an engagement that was made live again has live data again.

### D-P4-4-C. The archive date is the archive audit event. No schema change.

- **The archive record** of engagement E is the most recent (by `rowid`) `audit_events` row with `entity_type = "engagement"`, `entity_id = E` and `action IN ("engagement.archived", "engagement.unarchived")`, **if and only if** that row's action is `engagement.archived` **and** `Engagement.status == "archived"` **and** its `metadata_json` parses to a dict. Its `created_at` is the **archive date**. Recency is `rowid` (`literal_column("audit_events.rowid")`), per P3-2 D-P3-2-F, never `created_at`.
- **Why not an `archived_at` column:** it would need an Alembic revision, move the head off `4e8c1a9d2b57`, and force lockstep edits to the head assertions in `test_alembic_baseline_immutable.py`, `test_data_integrity.py`, `test_startup_invariants.py` and `test_citations.py` (the P2-3 list), while P4-1/P4-2/P4-3 run in parallel. The archive event is written in the same transaction as the status flip, so it is exactly as reliable as a column, and reading a fact back from `audit_events` is existing practice (P3-1's creator display, P3-2's issue metadata).
- **It fails closed.** An engagement whose status is `archived` but which has no valid archive record (for example one hand-set in the DB) **cannot be purged** (`archive_record_missing`). The fix is visible and safe: unarchive and archive again, which starts a fresh retention period.
- `created_at` values read back from SQLite are naive. Treat a naive value as UTC (`_as_utc(dt)`: `dt.replace(tzinfo=timezone.utc)` if naive, else `dt.astimezone(timezone.utc)`, the `magic_links._as_utc` convention).

### D-P4-4-D. Archive is inferred from the parent engagement, never propagated to children

**Decision: no child row is written when an engagement is archived or unarchived.** Assessment, Evidence, Finding, Action, Conclusion, snapshot and magic-link rows keep their own statuses untouched. "Is this archived?" is answered by resolving the request to its engagement and reading `Engagement.status`.

Why inference, against this codebase's actual patterns:
1. **The children already have their own `status` vocabularies with different meanings.** `Assessment.status` is a workflow stage (`created` … `completed`, plus assessment-level `archived`); `Evidence.status` has P2-1's audited transition table where `archived` means "excluded from analysis"; `Action.status` is P3-4's closure state machine; `Finding.status` is derived from Actions. Propagating would overwrite those values and require storing every child's prior status to restore it on unarchive, and it would make "this evidence was archived by a consultant" indistinguishable from "this evidence was archived because its engagement was".
2. **Propagation would add N audited transitions per archive** (P2-1 audits every Evidence status change) and N more per unarchive, with partial-failure states in between.
3. **The cost usually cited for inference, "every read and write path must join up to the parent", is paid once**, in a single router-level dependency (D-P4-4-E), not in each service. Reads need no check at all, because archive does not hide anything that is addressed directly.
4. It is the same shape the codebase already uses for derived state: P3-4 derives `Finding.status` from Actions rather than letting two stored values drift, and `portfolio.derive_status` derives the engagement badge from assessments.

### D-P4-4-E. Read-only enforcement: one router-level dependency, on every router except the retention router

- New dependency `archive_write_guard(request: Request, db: Session = Depends(get_db)) -> None` in `app/routers/retention.py`.
  1. If `request.method in READ_ONLY_METHODS` (`("GET", "HEAD", "OPTIONS")`): return.
  2. `ids = retention.engagement_ids_for_path(db, request.path_params)`.
  3. If `retention.archived_engagement_ids(db, ids)` is non-empty: `raise HTTPException(409, ARCHIVED_READ_ONLY, headers={"X-Toast-Message": quote(ARCHIVED_READ_ONLY), "X-Toast-Type": "error"})`.
- **`engagement_ids_for_path(db, path_params) -> set[str]`**, exact resolution:
  - `engagement_id` present → that value (whether or not the row exists).
  - `assessment_id` present → `Assessment.engagement_id` of that row, if the row exists and the value is not NULL.
  - `evidence_id` present → `Evidence.engagement_id` of that row, if the row exists.
  - Every other parameter is ignored. Unknown ids resolve to nothing; the handler returns its own 404 as today.
  - At most one `SELECT` per resolvable parameter (the `db.get` calls), plus one `SELECT` for `archived_engagement_ids` when `ids` is non-empty: `select(Engagement.id).where(Engagement.id.in_(ids), Engagement.status == ARCHIVED_STATUS)`.
- **Wiring, in `app/main.py`:** define `_ARCHIVE_GUARD = [Depends(retention_router.archive_write_guard)]` and pass `dependencies=_ARCHIVE_GUARD` to **every** existing `app.include_router(...)` call (all fifteen, including `reports.comparison_router`, `magic.router` and `web.router`). Include the new `retention.router` **without** it, because unarchive and purge must act on archived engagements; those routes enforce their own rules. Import the new router module as `from app.routers import retention as retention_router` inside the existing router import block (keep alphabetical order in the block: it goes after `review,`).
- **Why here and not in each handler or service:** it covers all 50 mutating `(method, path)` pairs registered today (the table in Current state; counted from `app.routes`, 45 of them resolvable to an engagement and the 5 listed below by design) with one code path, it needs **no edit to any router file**, so none of the per-file `"delete" not in source` and route-set guards is touched, and a structural test (scenario 3) proves every present and future mutating route carries it. FastAPI resolves router-level dependencies before the endpoint's own body and form parameters, so the guard refuses before any handler code runs. It shares the handler's cached `get_db` session, and `app.dependency_overrides[get_db]` applies to it as well.
- **The five mutating routes with no resolvable parameter are allowed by design:** `POST /engagements`, `POST /assessments`, `POST /assessments/new`, `POST /api/assessments` each create a **new** engagement hierarchy (the JSON and form creation paths always call `create_engagement_with_assessment`, never attach to an existing engagement), and `POST /magic/{token}` is already refused for a non-active engagement by `magic_links.resolve_token` (Current state), with the byte-identical non-enumerable 404. Scenario 3 pins this set exactly, so a new unguardable route fails the suite.
- **Reads are not blocked.** Every GET page (engagement, assessment, findings, conclusions, workpaper, remediation tracker, integrated reports, report snapshots and their file downloads, evidence detail) keeps working on an archived engagement. That is what makes archive "read-only" rather than "hidden".
- **Known residual, accepted and documented:** a write request that passes the guard and then runs for a long time (synchronous analysis) could still be writing after an archive that commits in the gap between the guard check and the handler's first commit. The gap is the few statements between the guard and `run_analysis_web`'s `analyzing` commit; after that commit, archive refuses (`ARCHIVE_IN_FLIGHT`). In a single-user local app this is accepted, exactly as P2-5 accepted its check-then-insert race. It cannot cause data loss: purge re-checks everything inside its own locked transaction years later (D-P4-4-L).
- **Out of scope for enforcement:** operator scripts (`scripts/seed_test_companies.py`, `scripts/migrate_legacy.py`, `scripts/migrate_documents_to_evidence.py`) write through their own sessions and are not guarded. They are human-invoked maintenance tools.

### D-P4-4-F. What the consultant sees

- **Portfolio visibility:** in `app/routers/web.py`, `dashboard` and `_engagement_cards_for_client` change their filter from `Engagement.status != "closed"` to `Engagement.status.notin_(("closed", "archived"))`. Nothing else in those functions changes.
- **Client page** (`web.client_detail` → `pages/client_detail.html`): gains three blocks from `retention.client_retention_view(db, client)` (D-P4-4-S): a retention form (D-P4-4-G), "Archived engagements" (one `<li data-archived-engagement id="archived-{{ row.engagement_id }}">` per archived engagement of this client: name linked to `/engagements/{id}`, "Archived {{ archived_at:%d %b %Y }}", and either "Eligible for purge from {{ eligible_at:%d %b %Y }}" or "Eligible for purge now"; or the text "No archived engagements."), and "Purge history" (one `<li data-purge-record>` per purged engagement of this client: the engagement name as recorded, "Purged {{ purged_at:%d %b %Y }} by {{ purged_by_display }}", and either "Files removed" or "Files pending removal" plus a `<form data-purge-complete-control hx-post="/api/engagements/{{ row.engagement_id }}/purge/complete" hx-include="#reviewer-name">` with submit "Finish removing files"; or the text "No engagements have been purged."). The page gets a `<input id="reviewer-name" name="reviewer_name" placeholder="Your name">` field above these blocks.
- **Engagement page** (`web.engagement_detail` → `pages/engagement_detail.html`): gains `{% include "partials/engagement_retention.html" %}` directly after the header `<div class="flex flex-col gap-5 …">…</div>` block and before `<section>` "Assessments". Context key `retention` = `retention.retention_state(db, engagement)` plus `client` (already present). The partial contains its own `<input id="reviewer-name" name="reviewer_name" placeholder="Your name">` and:
  - when `not retention.archived`: a `<div data-retention-panel>` with "Retention: {{ retention.client_retention_years }} years after archive (client setting)" and `<form data-archive-control hx-post="/api/engagements/{{ engagement.id }}/archive" hx-include="#reviewer-name" hx-confirm="Archive this engagement? It becomes read-only and leaves the portfolio views. You can unarchive it later.">` with submit "Archive engagement";
  - when `retention.archived`: a `<div data-archived-banner>` "This engagement is archived and read-only." then, if `retention.record`, "Archived on {{ archived_at:%d %b %Y }} by {{ archived_by_display }}." and "Eligible for permanent purge on or after {{ eligible_at:%d %b %Y }}." (or "Retention setting is not valid." when `retention_years_applied is none`), else "No archive record was found."; then `<form data-unarchive-control hx-post="/api/engagements/{{ engagement.id }}/unarchive" hx-include="#reviewer-name" hx-confirm="Unarchive this engagement? It becomes editable again, and its retention period restarts the next time it is archived.">` with submit "Unarchive engagement", and a link `<a data-purge-preview-link href="/engagements/{{ engagement.id }}/purge">Review permanent purge →</a>`.
- **Assessment page** (`web.assessment_detail` → `pages/assessment.html`): add context key `engagement_archived` (`bool`, from `retention.archived_engagement_ids(db, {assessment.engagement_id})` when `engagement_id` is set, else `False`). In the template, as the first child of `{% block content %}`, `{% if engagement_archived %}<div data-archived-banner …>This assessment belongs to an archived engagement and is read-only. Changes are refused until the engagement is unarchived.</div>{% endif %}`.
- **Write controls are not hidden per control.** The server refuses every write (D-P4-4-E) and the error toast says why. Hiding dozens of controls across a dozen templates is a large, error-prone diff whose failure mode is cosmetic, not data loss; the banners state the read-only state up front (open question 6).

### D-P4-4-G. Retention configuration: per client, 1–50 years, CAS, and archive-time floor

```python
RETENTION_YEARS_RANGE = (1, 50)
```

- New route `POST /api/clients/{client_id}/retention` (form fields `retention_years`, `reviewer_name`) → `retention.set_client_retention(db, client_id=…, retention_years=…, actor=…)`.
- **Validation:** the form value, stripped, must match `^[0-9]{1,3}$` and its `int` must be within `RETENTION_YEARS_RANGE` inclusive; anything else (blank, `0`, `51`, `7.5`, `-1`, `abc`, missing) → 400 `RETENTION_YEARS_INVALID`, nothing written.
- **Unchanged value:** nothing written, 200 with toast `Retention unchanged`.
- **Write:** `UPDATE clients SET retention_years=:new, updated_at=:now WHERE id=:id AND retention_years=:old` (`:old` as read); `rowcount != 1` → 409 `RETENTION_CONFLICT`. Then one `client.retention_changed` event (D-P4-4-P).
- **Which retention applies to an archived engagement (exact):** `retention_years_applied = max(current_client_years, years_at_archive)`, where `years_at_archive` is the archive event's `metadata["retention_years"]` when it is an `int` (not `bool`) within range, else it is ignored (the current value alone applies). If `current_client_years` is not an `int` within range, `retention_years_applied = None` and purge is refused with `retention_invalid`.
  - **Why the floor:** lowering a client's retention must never make an already-archived engagement purgeable sooner than the period it was archived under. This is the conservative reading of D11 for an irreversible operation. Raising retention does extend already-archived engagements (the `max`).
- **Per-engagement override is not implemented.** D11 says "per client or engagement", but the schema has only `clients.retention_years`, and a column is a schema change this task does not make (open question 2).
- The client page form: `<form data-retention-form hx-post="/api/clients/{{ client.id }}/retention" hx-include="#reviewer-name">` with `<input type="number" name="retention_years" min="1" max="50" value="{{ client.retention_years }}">`, submit "Save retention", and the help text "Applies from archive. An engagement that is already archived keeps at least the retention it was archived with."

### D-P4-4-H. Retention arithmetic (exact)

```python
def add_years(moment: datetime, years: int) -> datetime:
    try:
        return moment.replace(year=moment.year + years)
    except ValueError:                      # 29 February into a non-leap year
        return moment.replace(year=moment.year + years, day=28)
```

- `eligible_at = add_years(_as_utc(archived_at), retention_years_applied)`.
- **Elapsed iff `now >= eligible_at`** (inclusive), with `now = datetime.now(timezone.utc)` unless the caller passes `now=` (tests only). Everything is compared as timezone-aware UTC.
- Dates shown to people use `%d %b %Y` of the UTC value.

### D-P4-4-I. The purge set: exactly what is deleted, and exactly what is kept

For engagement **E**, with **A** = the ids of every assessment whose `engagement_id = E` (including assessment-level archived ones), **Ev** = ids of every Evidence with `engagement_id = E`, **V** = ids of every EvidenceVersion whose `evidence_id ∈ Ev`, **F** = Finding ids with `assessment_id ∈ A`, **C** = Conclusion ids with `assessment_id ∈ A`, **R** = GapReport ids with `assessment_id ∈ A`:

```python
PURGE_ORDER = (                      # delete order: children before parents (FKs are enforced)
    "evidence_uses",                 # evidence_id IN Ev OR assessment_id IN A
    "actions",                       # finding_id IN F
    "findings",                      # assessment_id IN A
    "conclusion_revisions",          # conclusion_id IN C
    "conclusions",                   # assessment_id IN A
    "analysis_runs",                 # assessment_id IN A
    "initiatives",                   # report_id IN R
    "gap_items",                     # report_id IN R
    "gap_reports",                   # assessment_id IN A
    "desk_review_findings",          # assessment_id IN A
    "desk_review_summaries",         # assessment_id IN A
    "questionnaire_responses",       # assessment_id IN A
    "rfi_documents",                 # assessment_id IN A
    "assessment_packs",              # assessment_id IN A
    "report_snapshots",              # assessment_id IN A OR engagement_id = E
    "evidence_versions",             # evidence_id IN Ev
    "evidence",                      # engagement_id = E
    "assessment_documents",          # assessment_id IN A
    "magic_links",                   # engagement_id = E
    "assessments",                   # engagement_id = E
    "engagements",                   # id = E AND status = 'archived'   (the CAS, D-P4-4-L)
)
RETAINED_TABLES = ("clients", "audit_events")
```

- **The scope of each table is defined once**, in a private `_purge_scopes(plan) -> list[tuple[str, type[Base], ColumnElement[bool]]]` (table name, ORM model, where-clause) in `PURGE_ORDER` order. `build_purge_plan` counts with `select(func.count()).select_from(Model).where(clause)` and the purge deletes with `delete(Model).where(clause).execution_options(synchronize_session=False)`, from the same list. There is no second definition to drift.
- **Coverage is enforced:** `set(Base.metadata.tables) == set(PURGE_ORDER) | set(RETAINED_TABLES)`, and the two are disjoint (scenario 1). Any table added later fails the suite until someone decides whether it is purged or retained.
- **Kept, deliberately:**
  - **`clients`**: D-P4-4-A.
  - **`audit_events`: never deleted and never rewritten, not even rows about purged entities.** The audit trail is what proves the purge was lawful and when it happened (PRD: "deletion attempts … attributable and queryable"), and P3-2's issue metadata, P2-1's hash history and P2-5's upload records are append-only by design. The residual is named: a few retained metadata keys can hold consultant- or client-authored text about purged items (`evidence_version.created.change_reason`, which P2-5 fills with the magic-link item title, and `evidence.status_changed.reason`). Everything else in audit metadata is ids, hashes, sizes and statuses. Open question 1 asks whether those two keys must be scrubbed; this task neither scrubs nor rewrites.
  - **Backups** under `backups/` (P1-6): not touched. They keep purged data until they are rotated, and restoring a pre-purge backup brings the data back (and also removes the purge's own audit rows). The operations doc says so (step 10); backup rotation is open question 3.
- **Issued report snapshots are purged with their engagement.** P3-2's "never un-issues, never deletes" is a property of the snapshot lifecycle while the record is retained; retention is what ends the record. Blocking purge on issued snapshots would make every completed engagement unpurgeable, which defeats D11. P3-2's hand-forward asked P4-4 to "honour legal hold for issued snapshots": **there is no legal-hold state in the schema or the product today**, so there is nothing to honour. Adding one is a product and schema decision (open question 5). Removing a whole scope's snapshot rows never reorders any remaining scope's `rowid`s, so P3-2's newest-only `ISSUE_SQL` is unaffected for every other engagement.
- **`assessment_documents` and `desk_review_findings.document_id`:** desk review findings of A are deleted before `assessment_documents` (the `SET NULL` FK would otherwise fire on our own rows first; the order makes that moot). A `desk_review_findings` row of **another** engagement pointing at one of our documents gets `NULL` from the FK, which is the existing documented document-deletion policy (PR-14).

### D-P4-4-J. The pre-purge checks (exact reasons, dependency codes and non-dependencies)

`evaluate_purge(db, engagement, plan, *, now=None) -> Eligibility` returns `reasons`, a tuple in exactly this order, containing each reason that applies:

```python
REFUSAL_REASONS = (
    "not_archived",            # Engagement.status != "archived". When present, it is the ONLY reason (nothing else is evaluated).
    "archive_record_missing",  # archived, but no valid archive record (D-P4-4-C). Retention is then not evaluated.
    "retention_invalid",       # retention_years_applied is None (D-P4-4-G). Elapsed is then not evaluated.
    "retention_not_elapsed",   # now < eligible_at (D-P4-4-H)
    "active_dependencies",     # any Dependency below has count > 0
    "storage_layout_invalid",  # plan.layout_violations > 0 (D-P4-4-K)
)
DEPENDENCY_CODES = (
    "evidence_used_elsewhere",
    "evidence_cited_elsewhere",
    "evidence_linked_elsewhere",
    "blob_shared_elsewhere",
)
```

Dependencies and layout are evaluated whenever `not_archived` is absent, so a refusal reports **every** blocker at once (the plan's "both" case). Each dependency is a `Dependency(code, count)`; all four are always present in `Eligibility.dependencies`, in `DEPENDENCY_CODES` order, zero counts included.

| Code | Exact count |
|---|---|
| `evidence_used_elsewhere` | `evidence_uses` rows with `evidence_id ∈ Ev` and `assessment_id ∉ A` |
| `evidence_cited_elsewhere` | rows **outside the purge set** whose raw JSON text contains any id in **V** as a substring: `conclusion_revisions` joined to `conclusions` with `conclusions.assessment_id ∉ A` and `citations_json IS NOT NULL`; `desk_review_findings` with `assessment_id ∉ A` and `citations_json IS NOT NULL`; `actions` joined to `findings` with `findings.assessment_id ∉ A`. Skip the three queries when **V** is empty. |
| `evidence_linked_elsewhere` | `evidence` rows with `assessment_id ∈ A` and `engagement_id != E`, plus `evidence` rows with `engagement_id = E` and `assessment_id IS NOT NULL` and `assessment_id ∉ A` |
| `blob_shared_elsewhere` | rows **outside the purge set** whose stored path lies under one of this plan's blob roots (D-P4-4-K): `evidence` (`id ∉ Ev`) and `evidence_versions` (`evidence_id ∉ Ev`) and `report_snapshots` (not in the purge scope) with `substr(storage_path, 1, length(:prefix)) = :prefix` for each `prefix = root + "/"`; and `assessment_documents` with `assessment_id ∉ A` whose resolved `file_path` is inside a resolved root |

- **P2-2's hand-forward is resolved by refusal, not by marking citations "purged-source".** A citation outside the engagement that points at our evidence means another engagement's record depends on these bytes; silently turning its support into a dangling reference would change a retained record's meaning. Refusing is the fail-closed choice. Citations **inside** the purge set are deleted with their rows. (With today's code, cross-engagement citations are not reachable: `citable_sources` is assessment-scoped and `map_evidence` refuses cross-engagement mappings. The checks exist because JSON references are not FK-protected and hand-set or future rows could create them.)
- **Substring matching on raw text is deliberate:** version ids are UUIDs, so a substring hit is an exact reference, and it also fails closed on malformed JSON that could not be parsed.
- **What is deliberately NOT an active dependency:**
  - issued report snapshots (D-P4-4-I);
  - open or in-progress Actions, unapproved Conclusions, or incomplete assessments. After the retention period these are history, and the consultant chose to archive;
  - magic links, active or not. They are inert once the engagement is archived and are purged with it;
  - `AnalysisRun.status == "running"` and assessment `analyzing` markers. Archive already refused in-flight work, the guard stops new work, and purge runs inside a write-locked transaction (D-P4-4-L). A stale marker must not make an engagement unpurgeable forever;
  - legal hold: there is none to check (open question 5).
- **Any FK reference the checks do not model is still caught:** SQLite enforces every FK, so a row outside the plan that references a row inside it (for example a Finding of another engagement whose `conclusion_id` points at one of our Conclusions) makes its DELETE fail. The whole phase-1 transaction rolls back and nothing is deleted (scenario 10b).

### D-P4-4-K. Blob roots and storage-layout validation

```python
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
```

- **The blob roots of E**, in this exact order, as POSIX paths relative to `settings.upload_dir`: `f"evidence/{E}"`, `f"reports/engagements/{E}"`, then for each A in `sorted(A)`: `f"reports/assessments/{A}"`, `f"{A}"` (the legacy per-assessment upload directory). Every root is listed whether or not it exists on disk.
- **Phase 2 removes these directories whole** (`shutil.rmtree`), rather than unlinking a list of file paths. Reasons: (1) the ledger then holds only ids, never client-supplied file names (legacy `file_path` values contain them, and the ledger is an audit row that outlives the purge); (2) orphan files inside an engagement's own directories (for example left by an interrupted upload) are removed too, which is the point of a purge; (3) the ledger stays small and can be validated exactly (D-P4-4-M). Completeness is guaranteed by the layout checks below: every blob a purged row references must be inside a root, or the purge is refused.
- **`plan.layout_violations`** counts each of:
  - E, or any A, not matching `SAFE_ID` (such an id can't be turned into a safe path);
  - a root whose path `upload_root / root` exists and `is_symlink()`, or whose `resolve()` is not strictly inside `Path(settings.upload_dir).resolve()`;
  - an in-set `evidence`/`evidence_versions`/`report_snapshots` row whose `storage_path` is absolute, contains a `..` or `.` part or a backslash, or does not start with one of the plan's roots + `"/"`, **and** whose file (`upload_root / storage_path`, resolved) exists;
  - an in-set `assessment_documents` row whose `Path(file_path).resolve()` (relative paths resolve against the process CWD, as the legacy writer's did) is not inside any resolved root, **and** that file exists.

  A referenced file that does not exist is not a violation (there is nothing to remove). An existing file outside the roots is a violation: deleting its row would leave client data behind with nothing pointing at it. Such a purge is refused with `storage_layout_invalid`, and nothing is deleted.
- `plan.blob_file_count` = the number of regular files under the existing, non-symlink roots (`rglob("*")`, `is_file()`), for the preview and the ledger.

### D-P4-4-L. Deletion ordering and crash safety: DB rows first in one locked transaction, blob directories second, with the audit event as the ledger

**Decision: phase 1 deletes every DB row and writes the `engagement.purged` event in one transaction and commits. Phase 2 then removes the blob roots and writes `engagement.purge_blobs_removed`. A committed `engagement.purged` event without a matching `engagement.purge_blobs_removed` event is the definition of "files pending", and it is always resumable.**

`purge_engagement(db, *, engagement_id, confirm_name, actor, now=None) -> PurgeResult`, exact sequence:

1. `engagement = db.get(Engagement, engagement_id)`. If `None`: raise `RetentionNotFound(ALREADY_PURGED)` when an `engagement.purged` event exists for that id, else `RetentionNotFound(ENGAGEMENT_NOT_FOUND)`.
2. If `(confirm_name or "").strip() != engagement.name.strip()`: raise `InvalidRetentionRequest(CONFIRM_MISMATCH)`. Nothing is written, no audit row. (The service checks this itself, so the script and any future caller can't skip it.)
3. Capture `name`, `client_id`. `db.rollback()` (ends the read transaction). `db.execute(text("PRAGMA secure_delete = ON"))` (D-P4-4-Q).
4. **Take the write lock first:** `locked = db.execute(update(Engagement).where(Engagement.id == engagement_id, Engagement.status == ARCHIVED_STATUS).values(updated_at=now).execution_options(synchronize_session=False)).rowcount == 1`. This is the first DML of the transaction, so SQLite takes the RESERVED lock here, and **no other connection can commit a write until this transaction ends**. Everything checked after this point is exactly the state that is deleted.
5. `db.expire_all()`; `engagement = db.get(Engagement, engagement_id)`. If `None`: `db.rollback()`, raise `RetentionNotFound(ALREADY_PURGED)`.
6. If `locked`: `plan = build_purge_plan(db, engagement)` and `eligibility = evaluate_purge(db, engagement, plan, now=now)`, both called **through the module globals** (scenario 10c patches `build_purge_plan`). If not `locked`: `eligibility` has `reasons == ("not_archived",)`.
7. **Refusal:** if `eligibility.reasons`: `db.rollback()`; add the `engagement.purge_refused` event (D-P4-4-P); `db.commit()`; raise `PurgeRefused(eligibility)`.
8. **Phase 1:** inside `try`: for each `(table, Model, clause)` of `_purge_scopes(plan)`, execute the delete; if `rowcount != plan.row_counts[table]`, raise `PurgeIntegrityError(table)`. The final `engagements` delete additionally carries `Engagement.status == ARCHIVED_STATUS` and must have `rowcount == 1`. Then `_write_purged_event(db, …)` (module global; scenario 10a patches it), then `db.commit()`. On **any** `Exception`: `db.rollback()`, log `"Purge of engagement %s failed before commit (%s); nothing was deleted"` with the id and `type(exc).__name__` only, and raise `PurgeFailed(PURGE_FAILED)` from it.
9. **Phase 2:** `outcome = _finish_blob_removal(db, engagement_id=…, purge_event_id=…, roots=plan.blob_roots, actor=actor)`. It removes each root (D-P4-4-M), writes `engagement.purge_blobs_removed`, and commits. On any `Exception` it does `db.rollback()`, logs the engagement id and exception class, and the result is `blobs_removed=False` with the root that failed. `BaseException` (a real crash, `KeyboardInterrupt`) is **not** caught.
10. Return `PurgeResult`.

**The failure-mode table (the contract; scenario 10 tests every row):**

| Failure point | State afterwards | Recovery |
|---|---|---|
| Before step 8's commit (exception, FK violation, rowcount mismatch, disk full, crash) | **Nothing deleted.** All rows and files intact, engagement still `archived`, no `engagement.purged` event. (A crash leaves an uncommitted SQLite transaction, which SQLite rolls back.) | Retry the purge. |
| Commit succeeded, phase 2 raises (`OSError`, permission, DB error writing the completion event) | Rows gone. `engagement.purged` committed. Some roots still on disk; no `engagement.purge_blobs_removed`. **"Files pending."** HTTP 500 `PURGE_BLOBS_PENDING`. | `POST /api/engagements/{E}/purge/complete`, the client page button, or `python scripts/complete_purges.py`. |
| Commit succeeded, process dies during phase 2 | Same as the row above (the route never answers). | Same. |
| Phase 2 removed everything, dies before the completion event commits | Rows gone; roots gone; no completion event. **"Files pending"** with nothing left to remove. | Completion finds every root missing (`missing_roots`), writes the event. Idempotent. |

Why this order and mechanism:
- **It makes both forbidden states impossible by construction.** (a) *A DB row pointing at a deleted file:* files are touched only after the rows referencing them are committed as deleted, and the layout checks (D-P4-4-K) plus `blob_shared_elsewhere` guarantee no surviving row references anything under a root. (b) *An orphaned blob referenced by nothing:* from the moment the rows are gone, the leftover roots **are** referenced, by the committed `engagement.purged` event's `blob_roots`, until the completion event says they are gone. "Pending" is detectable (`pending_purges`) and shown on the client page.
- **Why not blobs first:** a crash after removing files and before committing the rows leaves live rows pointing at missing files, forbidden state (a), on an engagement that looks intact. Recovering that needs a compensating restore from backup.
- **Why not a new ledger table:** it would be a schema change (D-P4-4-C's reasons), and the audit event must be written anyway. Using it as the ledger gives one record, not two that could disagree.
- **Why lock first and re-check inside the lock:** the preview and any earlier read are advisory. The authoritative checks run in the same write-locked transaction as the deletes, so no concurrent unarchive, upload, citation or mapping can slip between check and delete. A second concurrent purge blocks on the lock, then finds the engagement gone and returns `ALREADY_PURGED`.
- **Why this is enough for this app:** single process, single SQLite file, local disk. No distributed-transaction machinery is needed, only a strict order, a durable marker and an idempotent second step.

### D-P4-4-M. Completing a pending purge (resume), exact

- `pending_purges(db) -> list[PendingPurge]`: every `engagement.purged` event (by `rowid`) whose `entity_id` has no `engagement.purge_blobs_removed` event. `PendingPurge(engagement_id, purge_event_id, purged_at, blob_roots: tuple[str, ...])`, with `blob_roots` read from the event metadata (an empty tuple when unreadable, which completion then refuses).
- `complete_pending_purge(db, *, engagement_id, actor) -> CompletionOutcome` (commits):
  1. The latest `engagement.purged` event for the id; none → `RetentionNotFound(NO_PENDING_PURGE)`.
  2. A `engagement.purge_blobs_removed` event already exists for the id → return `CompletionOutcome(already_complete=True, removed_roots=(), missing_roots=())`, write nothing.
  3. An `Engagement` row with that id exists → `RetentionConflict(PURGE_LEDGER_INCONSISTENT)`, remove nothing. (Can't happen through this code; guards against a hand-written or restored ledger row.)
  4. **Validate the ledger exactly:** `metadata["blob_roots"]` must be a list of strings with no duplicates, and `set(blob_roots)` must **equal** the root set rebuilt from `entity_id` and `metadata["assessment_ids"]` by D-P4-4-K's templates, with every id matching `SAFE_ID`. Otherwise → `RetentionConflict(PURGE_LEDGER_INVALID)`, remove nothing.
  5. `_finish_blob_removal(...)`; on exception → `db.rollback()` and raise `PurgeFailed(PURGE_BLOBS_PENDING)`.
- `_finish_blob_removal(db, *, engagement_id, purge_event_id, roots, actor) -> CompletionOutcome`: for each root in order, `path = Path(settings.upload_dir) / root`; re-validate (no symlink at `path`, and `path.resolve()` strictly inside `Path(settings.upload_dir).resolve()`; else raise `BlobRootError(root)`); if `not path.exists()`: record in `missing_roots`; else `_remove_tree(path)` and record in `removed_roots`. Then add the `engagement.purge_blobs_removed` event and `db.commit()`.
- `_remove_tree(path: Path) -> None` is exactly `shutil.rmtree(path)`. It is a module-global seam (scenario 10d/e patch it). `shutil.rmtree` refuses a symlinked top directory and does not follow symlinks inside the tree.
- **`scripts/complete_purges.py`** (new), in the style of `scripts/backup.py`/`scripts/detect_orphans.py` (plain functions, stdlib `argparse`, `if __name__ == "__main__":`): `run(db: Session, *, list_only: bool = False, out=sys.stdout) -> int` prints `PENDING <engagement_id> <purged_at iso> roots=<n>` for each pending purge; unless `list_only`, calls `complete_pending_purge(db, engagement_id=…, actor=COMPLETION_SCRIPT_ACTOR)` for each and prints `COMPLETED <engagement_id> removed=<n> missing=<m>` or `FAILED <engagement_id> <message>`; returns `1` if any failed, else `0`. `main(argv=None) -> int` parses `--list`, opens `app.database.SessionLocal()`, calls `run`, closes the session. It never runs Alembic and never purges anything that is not already committed as purged.

### D-P4-4-N. The confirmation flow: preview page, typed engagement name, `hx-confirm`, server re-check

1. From the archived engagement's page, "Review permanent purge →" opens **`GET /engagements/{engagement_id}/purge`** (`pages/engagement_purge.html`). It renders for any existing engagement (unknown id → 404 `ENGAGEMENT_NOT_FOUND`; purged id → 404 `ALREADY_PURGED`). It calls `build_purge_plan` and `evaluate_purge` and **never writes** (no audit row, no commit). It shows:
   - breadcrumb `Portfolio / {{ client.name }} / {{ engagement.name }} / Permanent purge`; `<h1>` "Permanent purge";
   - archive facts (when a record exists): archived date and by whom, `retention_years_applied`, eligible date;
   - when refused: one `<li data-purge-reason="{{ code }}">` per reason with its message (D-P4-4-O), and under `active_dependencies` one `<li data-purge-dependency="{{ code }}">` per non-zero dependency with its label and count;
   - "What will be permanently deleted": one `<tr data-purge-count="{{ table }}">` per `PURGE_ORDER` table with its count, and `<p data-purge-files>` "{{ plan.blob_file_count }} stored files in {{ plan.blob_roots|length }} storage folders";
   - "What is kept": "The client record. The audit log, including the record of this purge. Backups made before the purge still contain this engagement until they are rotated, and restoring one would bring it back.";
   - **only when `eligibility.reasons` is empty**: `<form data-purge-form hx-post="/api/engagements/{{ engagement.id }}/purge" hx-confirm="Permanently delete this engagement and all of its stored files? This cannot be undone.">` containing `<label for="confirm-name">Type the engagement name to confirm: {{ engagement.name }}</label>`, `<input id="confirm-name" name="confirm_name" autocomplete="off" required>`, `<input id="reviewer-name" name="reviewer_name" placeholder="Your name">`, and submit "Permanently delete engagement". Otherwise the text "Permanent deletion is not available for this engagement." and no form.
2. `POST /api/engagements/{engagement_id}/purge` re-checks everything server-side (D-P4-4-L). The typed name is compared exactly after stripping (case-sensitive). The preview's eligibility is never trusted.

- **Why a typed name on top of `hx-confirm`:** `hx-confirm` is this codebase's existing pattern for every destructive action, and it is kept. It is one click on a browser dialog, so for the one irreversible delete in the product a second, deliberate act is added: typing the name is the standard pattern for irreversible deletes, and it is checked on the server, so it also protects the JSON API and the script path.
- **Why no confirmation token:** a GET-issued token adds state (storage, expiry) for no gain here. There is no auth and no multi-user race. The typed name is already a per-engagement secret-free proof of intent, and every eligibility fact is re-derived under the lock at POST time.

### D-P4-4-O. Routes, HTTP contract and messages (exact)

New router `app/routers/retention.py`, `router = APIRouter(tags=["retention"])`, registered in `app/main.py` **without** `_ARCHIVE_GUARD`, directly before `app.include_router(magic.router, …)` (after `integrated_reports`). Handlers are sync `def`, take `Form` fields like `integrated_reports.py`, and reuse its `_error`/`_success` shapes (copy the two helpers; don't import them). Actor is always `conclusion_review.reviewer_actor(reviewer_name)`.

| Method + path | Handler | Success |
|---|---|---|
| `POST /api/engagements/{engagement_id}/archive` | `archive_engagement_route` | 200 JSON `{"engagement_id", "status": "archived"}`, `HX-Redirect: /engagements/{id}`, toast `Engagement archived` |
| `POST /api/engagements/{engagement_id}/unarchive` | `unarchive_engagement_route` | 200 JSON `{"engagement_id", "status": <restored>}`, `HX-Redirect: /engagements/{id}`, toast `Engagement restored` |
| `GET /engagements/{engagement_id}/purge` | `purge_preview_page` | 200 HTML (D-P4-4-N) |
| `POST /api/engagements/{engagement_id}/purge` | `purge_engagement_route` | 200 JSON `{"engagement_id", "purge_event_id", "row_counts", "blobs_removed": true}`, `HX-Redirect: /clients/{client_id}`, toast `Engagement permanently purged` |
| `POST /api/engagements/{engagement_id}/purge/complete` | `complete_purge_route` | 200 JSON `{"engagement_id", "already_complete", "removed_roots", "missing_roots"}`, toast `Stored files removed` (or `Nothing left to remove` when already complete), `HX-Refresh: true` |
| `POST /api/clients/{client_id}/retention` | `set_client_retention_route` | 200 JSON `{"client_id", "retention_years"}`, `HX-Redirect: /clients/{id}`, toast `Retention updated` / `Retention unchanged` |

Each route commits at most once on success (archive, unarchive, retention: the router commits after the service returns; purge and completion: the service commits, D-P4-4-S). Every error path calls `db.rollback()` before returning.

**Error mapping:** `RetentionNotFound` → 404; `InvalidRetentionRequest` → 400; `RetentionConflict` → 409; `PurgeRefused` → 409 with JSON `{"detail": <message>, "reasons": [...], "eligible_at": <iso or null>, "dependencies": [{"code", "count"}, … only non-zero], "layout_violations": <int>}`; `PurgeFailed` → 500; the phase-2 pending case → 500 JSON `{"detail": PURGE_BLOBS_PENDING, "records_purged": true, "blobs_pending": true, "engagement_id": …}`. All errors carry the error toast headers.

```python
READ_ONLY_METHODS = ("GET", "HEAD", "OPTIONS")

# Messages (exact; tests compare them; no apostrophes, no user-controlled text)
ENGAGEMENT_NOT_FOUND = "Engagement not found"
CLIENT_NOT_FOUND = "Client not found"
ARCHIVED_READ_ONLY = "This engagement is archived and read-only. Unarchive it to make changes."
ALREADY_ARCHIVED = "This engagement is already archived."
NOT_ARCHIVABLE = "Only an active or closed engagement can be archived."
ARCHIVE_IN_FLIGHT = "An analysis or desk review is still running in this engagement. Wait for it to finish, then archive."
ARCHIVE_CONFLICT = "This engagement changed while you were archiving it. Reload and try again."
NOT_ARCHIVED = "This engagement is not archived."
UNARCHIVE_CONFLICT = "This engagement changed while you were restoring it. Reload and try again."
RETENTION_YEARS_INVALID = "Retention must be a whole number of years from 1 to 50."
RETENTION_CONFLICT = "The retention of this client changed while you were editing it. Reload and try again."
CONFIRM_MISMATCH = "Type the engagement name exactly as shown to confirm permanent deletion."
ALREADY_PURGED = "This engagement has already been purged."
PURGE_FAILED = "The purge could not be completed. Nothing was deleted."
PURGE_BLOBS_PENDING = "The records of this engagement were permanently deleted, but some stored files could not be removed yet. Finish the purge from the client page or run scripts/complete_purges.py."
NO_PENDING_PURGE = "There is no unfinished purge for this engagement."
PURGE_LEDGER_INCONSISTENT = "The purge record for this engagement does not match the database. Nothing was removed."
PURGE_LEDGER_INVALID = "The purge record for this engagement is not valid. Nothing was removed."
REASON_MESSAGES = {
    "not_archived": "Only an archived engagement can be purged.",
    "archive_record_missing": "No archive record was found for this engagement. Unarchive it and archive it again to start its retention period.",
    "retention_invalid": "The retention setting of this client is not valid. Set a retention period from 1 to 50 years first.",
    "retention_not_elapsed": "The retention period has not elapsed. This engagement can be purged on or after {eligible_at:%d %b %Y}.",
    "active_dependencies": "Other records still depend on the evidence of this engagement: {dependencies}.",
    "storage_layout_invalid": "Some stored files of this engagement are outside its storage folders. Nothing can be purged until this is resolved.",
}
DEPENDENCY_LABELS = {
    "evidence_used_elsewhere": "evidence mapped into an assessment of another engagement",
    "evidence_cited_elsewhere": "evidence cited by records of another engagement",
    "evidence_linked_elsewhere": "evidence filed under another engagement",
    "blob_shared_elsewhere": "stored files shared with another engagement",
}
```

- `{dependencies}` is `"; ".join(f"{DEPENDENCY_LABELS[d.code]} ({d.count})" for d in eligibility.dependencies if d.count)`.
- **The refusal `detail` is `" ".join(REASON_MESSAGES[r].format(...) for r in reasons)`**, in `REFUSAL_REASONS` order. For the plan's "both" case this is the `retention_not_elapsed` message, one space, then the `active_dependencies` message.
- **No engagement or client name, file name or other stored text ever appears in a message, a toast or a log line.** Toasts are rendered with `innerHTML` (Current state), and log lines outlive the data. Ids, dates, counts and codes only.
- **Route-set consistency (checked):** none of the six paths contains `/findings`, `/conclusions`, `/workpaper`, `/snapshots`, `/remediation` or `/integrated-reports`, so every existing exact route-set guard is unaffected. This task's own guard (scenario 1) pins exactly these six routes as the set of paths containing `/archive`, `/unarchive`, `/purge` or `/retention`. (`/archive` is not a substring of `/unarchive`.)

### D-P4-4-P. Audit events (exact; the P2-1/P3-2 write pattern)

Every event is `db.add(AuditEvent(actor=…, action=…, entity_type=…, entity_id=…, metadata_json=json.dumps(metadata, sort_keys=True)))`, `created_at` left to its default, and is written in the same transaction as the change it records. Metadata key sets are exact (tests assert set equality). Timestamps in metadata are `.isoformat()` of timezone-aware UTC values.

```python
ENGAGEMENT_ENTITY = "engagement"
CLIENT_ENTITY = "client"
ARCHIVED_EVENT = "engagement.archived"
UNARCHIVED_EVENT = "engagement.unarchived"
PURGE_REFUSED_EVENT = "engagement.purge_refused"
PURGED_EVENT = "engagement.purged"
PURGE_BLOBS_REMOVED_EVENT = "engagement.purge_blobs_removed"
RETENTION_CHANGED_EVENT = "client.retention_changed"
EVENT_SCHEMA_VERSION = 1
COMPLETION_SCRIPT_ACTOR = "system:purge-completion"
```

| Action | entity | Metadata keys (exact) |
|---|---|---|
| `engagement.archived` | engagement, E | `schema_version`, `client_id`, `previous_status`, `retention_years` (the client value at archive time) |
| `engagement.unarchived` | engagement, E | `schema_version`, `archive_event_id` (id of the archive record, or `null`), `restored_status` |
| `engagement.purge_refused` | engagement, E | `schema_version`, `reasons` (list), `dependencies` (list of `{"code", "count"}`, all four), `layout_violations`, `archived_at` (iso or `null`), `retention_years_applied` (int or `null`), `eligible_at` (iso or `null`) |
| `engagement.purged` | engagement, E | `schema_version`, `client_id`, `engagement_name`, `archive_event_id`, `archived_at`, `retention_years_applied`, `eligible_at`, `assessment_ids` (sorted list), `row_counts` (object: every `PURGE_ORDER` table → int), `blob_roots` (list, D-P4-4-K order), `blob_file_count` |
| `engagement.purge_blobs_removed` | engagement, E | `schema_version`, `purge_event_id`, `removed_roots` (list), `missing_roots` (list) |
| `client.retention_changed` | client, client id | `schema_version`, `from`, `to` |

- **Refusals are audited only once the confirmation name matched** (a mistyped name is input validation, not a deletion attempt). `CONFIRM_MISMATCH` and 404s write nothing. Archive/unarchive refusals (409) write nothing: they change nothing and are not deletion attempts.
- `engagement_name` is recorded on `engagement.purged` so a person reading the audit log years later can tell what was purged. It is a consultant-authored label, not client-supplied content (the client name is retained in `clients` anyway). It is shown on the client page's purge history and never placed in a toast or log line.
- The purged event is written **after** the deletes and **before** the commit, so it exists if and only if the rows are gone.

### D-P4-4-Q. `PRAGMA secure_delete = ON` for the purge connection

Deleted SQLite rows stay readable in free pages until overwritten. The purge's point is removal, so step 3 of D-P4-4-L enables `secure_delete` on the connection before the transaction, which makes SQLite zero deleted content. It is a connection-level flag and is left on (its only cost is extra writes on later deletes over the same pooled connection, which are rare in this app). Scenario 9 proves a sentinel string from a purged row no longer appears in the raw DB file bytes while a control sentinel of another engagement does. **Not covered, and named in the operations doc:** the rollback journal file's freed disk blocks, filesystem-level remnants of removed blobs, and backups.

### D-P4-4-R. Never auto-purge, as a structural property

- `purge_engagement(` is called from exactly one place in `app/`: `app/routers/retention.py::purge_engagement_route`. `complete_pending_purge(` is called only from `complete_purge_route` and `scripts/complete_purges.py`. Neither is called from `app/main.py` (including `lifespan`), from any `BackgroundTasks`, scheduler, startup hook or other service.
- No shipped setting enables automatic purge, and none is added.
- Scenario 12 greps for this and also boots the app (lifespan) with an eligible archived engagement present, then shows it is still intact.

### D-P4-4-S. Service API and commit boundaries (exact)

New module **`app/services/retention.py`** (not an extension of `evidence.py`: purge spans every table and the report-snapshot store, and `evidence.py`, `report_snapshots.py` and `findings.py` are protected by the delete guards and non-goals above). Module docstring: `"""Engagement retention (P4-4): reversible archive as an engagement status flip inferred by every child, per-client retention, and a manual two-phase permanent purge that commits the DB deletion first and removes the engagement's storage folders second, with audit events as the ledger. Never purges automatically."""` `logger = logging.getLogger(__name__)`.

Constants: everything in D-P4-4-B, G, I, J, K, O and P above.

Exceptions: `RetentionError(Exception)` with `status_code` and `message` (the `findings.FindingError` shape); `RetentionNotFound` 404; `InvalidRetentionRequest` 400; `RetentionConflict` 409; `PurgeRefused(RetentionConflict)` carrying `.eligibility`; `PurgeFailed` 500; `PurgeIntegrityError(Exception)` (internal, always converted to `PurgeFailed`); `BlobRootError(Exception)` (internal).

Frozen dataclasses:

```python
@dataclass(frozen=True)
class ArchiveRecord:
    event_id: str
    archived_at: datetime               # timezone-aware UTC
    actor: str
    previous_status: str | None
    retention_years_at_archive: int | None

@dataclass(frozen=True)
class RetentionState:
    engagement_id: str
    status: str
    archived: bool
    record: ArchiveRecord | None
    client_retention_years: int | None  # None when the stored value is out of range
    retention_years_applied: int | None
    eligible_at: datetime | None
    elapsed: bool
    archived_by_display: str            # actor without "consultant:", "" when no record

@dataclass(frozen=True)
class Dependency:
    code: str
    count: int

@dataclass(frozen=True)
class PurgePlan:
    engagement_id: str
    client_id: str
    assessment_ids: tuple[str, ...]      # sorted
    evidence_ids: tuple[str, ...]        # sorted
    version_ids: tuple[str, ...]         # sorted
    row_counts: dict[str, int]           # every PURGE_ORDER table, in order
    blob_roots: tuple[str, ...]
    blob_file_count: int
    layout_violations: int

@dataclass(frozen=True)
class Eligibility:
    reasons: tuple[str, ...]
    dependencies: tuple[Dependency, ...] # all four, DEPENDENCY_CODES order; () when not_archived
    layout_violations: int
    state: RetentionState

@dataclass(frozen=True)
class PurgeResult:
    engagement_id: str
    client_id: str
    purge_event_id: str
    row_counts: dict[str, int]
    blob_roots: tuple[str, ...]
    blobs_removed: bool
    failed_root: str | None

@dataclass(frozen=True)
class PendingPurge:
    engagement_id: str
    purge_event_id: str
    purged_at: datetime
    blob_roots: tuple[str, ...]

@dataclass(frozen=True)
class CompletionOutcome:
    already_complete: bool
    removed_roots: tuple[str, ...]
    missing_roots: tuple[str, ...]
```

Functions (the only public API):

```python
def add_years(moment: datetime, years: int) -> datetime: ...
def archive_record(db: Session, engagement_id: str) -> ArchiveRecord | None: ...
def retention_state(db: Session, engagement: Engagement, *, now: datetime | None = None) -> RetentionState: ...
def engagement_ids_for_path(db: Session, path_params: Mapping[str, str]) -> set[str]: ...
def archived_engagement_ids(db: Session, engagement_ids: set[str]) -> set[str]: ...
def archive_engagement(db: Session, *, engagement_id: str, actor: str, now: datetime | None = None) -> Engagement: ...
def unarchive_engagement(db: Session, *, engagement_id: str, actor: str, now: datetime | None = None) -> Engagement: ...
def set_client_retention(db: Session, *, client_id: str, retention_years: str | int | None, actor: str) -> tuple[Client, bool]: ...   # (client, changed)
def build_purge_plan(db: Session, engagement: Engagement) -> PurgePlan: ...
def evaluate_purge(db: Session, engagement: Engagement, plan: PurgePlan, *, now: datetime | None = None) -> Eligibility: ...
def refusal_message(eligibility: Eligibility) -> str: ...
def purge_engagement(db: Session, *, engagement_id: str, confirm_name: str | None, actor: str, now: datetime | None = None) -> PurgeResult: ...
def pending_purges(db: Session) -> list[PendingPurge]: ...
def complete_pending_purge(db: Session, *, engagement_id: str, actor: str) -> CompletionOutcome: ...
def client_retention_view(db: Session, client: Client) -> ClientRetentionView: ...
```

`ClientRetentionView(archived: list[ArchivedEngagementRow], purges: list[PurgeRecordRow])`, with `ArchivedEngagementRow(engagement_id, name, archived_at: datetime | None, eligible_at: datetime | None, elapsed: bool)` (archived engagements of the client, `created_at` then `id`) and `PurgeRecordRow(engagement_id, engagement_name, purged_at, purged_by_display, blobs_removed: bool)` (every `engagement.purged` event whose metadata `client_id` is this client, newest `rowid` first).

**Commit boundaries:** `archive_engagement`, `unarchive_engagement` and `set_client_retention` **never commit** (they flush; the router commits once, the P2-1/P3-1 rule). **`purge_engagement` and `complete_pending_purge` commit**, because the two-phase contract needs a commit between the DB step and the blob step, and a router can't own a boundary in the middle of a service call. The precedent is `evidence.ingest_upload`, which commits for exactly the same reason (blob and row ordering). Every read function (`archive_record`, `retention_state`, `engagement_ids_for_path`, `archived_engagement_ids`, `build_purge_plan`, `evaluate_purge`, `pending_purges`, `client_retention_view`) never writes.

Archive/unarchive/retention CAS details: after the `update(...)` with `rowcount != 1` → the conflict error; on success, `db.expire(row)`, add the audit event, `db.flush()`, return the refreshed row. `archive_engagement` reads, in order: engagement (404), status checks, then `_in_flight_count(db, engagement_id)` (a module-global seam; scenario 2 patches it to simulate a concurrent status change), then the client, then the CAS.

### D-P4-4-T. Consistency audit of this spec against the existing structural guards (the P2-4 lesson)

1. **No file under a `"delete" not in source` guard is edited** (the list in Current state). The words "delete", "purge" and "rmtree" live only in new files and in `app/main.py` (which has no such guard; `main.py` gains only the router import, `_ARCHIVE_GUARD` and the `dependencies=` arguments).
2. **No route-set guard moves** (D-P4-4-O).
3. **`.unlink(` counts are unchanged** in `report_snapshots.py`, `snapshots.py`, `integrated_reports.py` (not edited). `retention.py` uses no `.unlink(` at all (roots are removed with `shutil.rmtree`).
4. **Templates:** no `CyberAssess`, no `overall_score`, no `|safe` in any new or changed template. New `data-*` attributes (`data-retention-panel`, `data-archive-control`, `data-archived-banner`, `data-unarchive-control`, `data-purge-preview-link`, `data-retention-form`, `data-archived-engagement`, `data-purge-record`, `data-purge-complete-control`, `data-purge-reason`, `data-purge-dependency`, `data-purge-count`, `data-purge-files`, `data-purge-form`) don't contain one another except `data-purge-*` prefixes, which tests always match with the full attribute name and `=` (for example `data-purge-reason="`).
5. **Messages in HTML** contain no apostrophe and no `&`, `<`, `>` or quote characters (D-P4-4-O), so autoescaping can't change them.
6. **`AssessmentDocument(`** never appears in the new code (the P2-1 guard). Query it with `select(AssessmentDocument…)` only.
7. **No `relationship(`**, no model change, no Alembic revision: `alembic heads` stays `4e8c1a9d2b57`.
8. The `get_db` override used by every test's `http` fixture also reaches the guard, so existing tests that write to **active** engagements are unaffected. No existing test creates an `archived` engagement.

### D-P4-4-U. Coordination with the parallel Phase 4 tasks

- **Files this task shares with others:** `app/main.py` (P4-1 is likely to register an AWS router), `app/routers/web.py` and `app/templates/pages/engagement_detail.html` (P4-1 may add an AWS panel or link), and `tasks/todo.md` (all). Each change here is additive and local (an include, a filter, a context key, one include line). **If another task lands first, keep both sides of each conflict.**
- **Binding on whichever of P4-1/P4-4 lands second:** P4-1's router (it writes Evidence into an engagement) **must** be included with `dependencies=_ARCHIVE_GUARD`. Scenario 3's structural test fails if any mutating route lacks the guard, so the rebase is mechanical: add the argument. If P4-1 adds a mutating route with none of `assessment_id`/`engagement_id`/`evidence_id` in its path, scenario 3's exact "unresolvable" set fails. That route must then be redesigned to take one of them, which is P4-1's call, not a reason to widen the set here.
- **P4-2 (seed script)** writes through its own session and is not guarded (D-P4-4-E). P4-2 does not need archive or purge.
- **P4-3 (benchmarks)** may measure the guard's extra `SELECT`s. They are bounded (≤ 4 per mutating request, D-P4-4-E).

## Required approach

### 1. `app/services/retention.py` (new): D-P4-4-B … S exactly

Implementation notes that are part of the contract:
- Import models directly (`Action`, `AnalysisRun`, `Assessment`, `AssessmentDocument`, `AssessmentPack`, `AuditEvent`, `Client`, `Conclusion`, `ConclusionRevision`, `DeskReviewFinding`, `DeskReviewSummary`, `Engagement`, `Evidence`, `EvidenceUse`, `EvidenceVersion`, `Finding`, `GapItem`, `GapReport`, `Initiative`, `MagicLink`, `QuestionnaireResponse`, `ReportSnapshot`, `RFIDocument`) and `Base` from `app.database`. Use `settings.upload_dir` read at call time (tests monkeypatch it). Use `conclusion_review.REVIEWER_ACTOR_PREFIX` for display stripping.
- `_purge_scopes(plan)` is the single scope definition (D-P4-4-I). Build `A`, `Ev`, `V`, `F`, `C`, `R` with one `SELECT` each. Empty `in_()` lists are fine.
- `rowid` ordering: `literal_column("audit_events.rowid")`.
- Never log stored text: ids, counts, codes and exception class names only.

### 2. `app/routers/retention.py` (new): `archive_write_guard` and the six routes (D-P4-4-E, N, O)

`purge_preview_page` renders `pages/engagement_purge.html` with `Jinja2Templates` configured by `app.template_config.configure_templates`, the same way `app/routers/findings.py` sets up `_templates`. Context: `request`, `engagement`, `client`, `plan`, `eligibility`, `reason_messages` (a list of `(code, message)` in order), `REASON_MESSAGES`-derived text only.

### 3. `app/main.py`

Import `retention as retention_router` in the router import block; define `_ARCHIVE_GUARD = [Depends(retention_router.archive_write_guard)]` (import `Depends` from `fastapi`); add `dependencies=_ARCHIVE_GUARD` to all fifteen existing `include_router` calls; add `app.include_router(retention_router.router)` (no guard) directly before `app.include_router(magic.router, …)`. Nothing else changes.

### 4. `app/routers/web.py`

- `dashboard` and `_engagement_cards_for_client`: the filter change in D-P4-4-F, nothing else.
- `engagement_detail`: add `"retention": retention.retention_state(db, engagement)` to the context.
- `client_detail`: add `"retention_view": retention.client_retention_view(db, client)` to the context.
- `assessment_detail`: add `"engagement_archived": …` (D-P4-4-F).
- Import `from app.services import retention` (add it to the existing `from app.services import (...)` block, alphabetically after `report_snapshots,`).

### 5. Templates

- `partials/engagement_retention.html` (new), included from `pages/engagement_detail.html` (D-P4-4-F).
- `pages/engagement_purge.html` (new; extends `base.html`; `{% block title %}Permanent purge — {{ engagement.name }}{% endblock %}`) (D-P4-4-N).
- `pages/client_detail.html`: the reviewer input, retention form, archived engagements and purge history (D-P4-4-F, G).
- `pages/assessment.html`: the archived banner (D-P4-4-F).

Everything autoescaped. Never `|safe`.

### 6. `scripts/complete_purges.py` (new): D-P4-4-M

### 7. Nothing else in `app/`

No model, migration, or other router or service file changes (see Done criteria for the exact list).

### 8. `docs/operations/retention-purge.md` (new, short)

Cover: D11 in one line; archive/unarchive and what read-only means; how retention is set and the archive-time floor; the purge preview and confirmation; the two-phase contract and the failure-mode table in plain words; how to find and finish a pending purge (client page, route, `python scripts/complete_purges.py --list` then without `--list`); what is kept (client row, audit log and the two free-text keys, backups; restoring a pre-purge backup resurrects the data and drops the purge audit rows); `secure_delete` and what it does not cover; "Never runs automatically." Link it from `docs/operations/backup-restore.md` with one added line under a "See also" heading at the end of that file. Do not touch `CLAUDE.md` or `AGENTS.md` (the reviewing session updates context files after merge).

### 9. `tasks/todo.md`

Under the Phase 4 line, add a P4-4 line in the existing style with its status and a link to this handoff's Results. Don't change the Phase 4 summary line's other content (the reviewing session does that after merge).

### 10. Smoke test script

None is committed. The smoke in Done criteria is run ad hoc (scratch only), as in every prior task.

### 11. `tests/test_retention.py` (new)

Copy (don't import) from `tests/test_remediation_tracking.py`: `_register_frameworks`, `_alembic_config`, `db_path`, `engine` (with the FK `connect` listener), `db`, `http`, the autouse `upload_root`, `gate`, `_seed` (with its `engagement=` keyword), and whatever helpers you need to create real Conclusions, approvals, Findings, Actions, closure evidence and snapshots through the real pipeline and routes (`_item`, `_stub_single`, `_run_one`, `_decide`/`_approve`, `_create`, `_closure_evidence` using real PDF uploads, as P3-4's Results found `.txt` is rejected). **No test may write under the real `uploads/` or touch `data/dpdpa.db`.**

Helpers to add:
- `_snapshot(db, upload_root)`: for every table in `sorted(Base.metadata.tables)`, the full ordered content `db.execute(text(f"SELECT * FROM {t} ORDER BY rowid")).all()`, plus `sorted((str(p.relative_to(upload_root)), sha256(p.read_bytes())) for p in upload_root.rglob("*") if p.is_file())`. "Nothing written" means `_snapshot` is equal before and after. "Nothing written except one audit row" means equal after removing `audit_events` from both and the audit table grew by exactly the stated rows.
- `_backdate_archive(db, engagement_id, *, years, days=1)`: sets the archive record's `created_at` to `add_years(now, -years) - timedelta(days=days)` with a direct `UPDATE audit_events` (the only way to simulate elapsed time over HTTP; allowed hand-set).
- `_full_engagement(db, http, gate, upload_root, *, client=None, sentinel)`: builds the realistic engagement of scenario 9 through real routes and services, returns ids.

Hand-set rows are allowed **only** for: engagement `status` values other than through the routes in scenario 2's refusal cases and scenario 8's `archive_record_missing`; `clients.retention_years` out of range (scenario 8); the audit `created_at` backdating; the cross-engagement dependency rows of scenario 7 (they can't be created through the app by design); legacy `assessment_documents` rows via Core `insert()` (the P2-1 guard forbids `AssessmentDocument(` in `app/`, not in tests, but use `insert()` for consistency with P1-3's fixture lesson); tampered ledger rows in scenario 10f; storage-path and symlink tampering in scenarios 8 and 10g. Every scenario is one or more test functions whose docstrings start with `Scenario N:`.

## Key files

| File | Why it matters |
|---|---|
| `app/services/retention.py` (new) | The whole contract (D-P4-4-B … S). |
| `app/routers/retention.py` (new) | `archive_write_guard` and the six routes (D-P4-4-E, N, O). |
| `app/main.py` | Guard on every existing router; retention router without it (D-P4-4-E). |
| `app/routers/web.py` | Two portfolio filters; three context keys (D-P4-4-F). |
| `app/templates/partials/engagement_retention.html`, `pages/engagement_purge.html` (new); `pages/engagement_detail.html`, `pages/client_detail.html`, `pages/assessment.html` | UI (D-P4-4-F, G, N). |
| `scripts/complete_purges.py` (new) | Resume tool (D-P4-4-M). |
| `docs/operations/retention-purge.md` (new), `docs/operations/backup-restore.md` (one "See also" line) | Operator guidance. |
| `tests/test_retention.py` (new) | The contract. |
| `app/models/*`, `alembic/versions/*` | **Not modified.** No schema change (D-P4-4-C). |
| `app/services/evidence.py`, `report_snapshots.py`, `findings.py`, `magic_links.py`, `conclusion_review.py`, `analysis_pipeline.py`, `workpaper.py`, `remediation_rollup.py`, `report_content.py`, `portfolio.py`, `engagement_factory.py`, every router file other than `web.py` and the new `retention.py`, `scripts/backup.py`, `scripts/restore.py`, `scripts/migrate_legacy.py`, `app/static/js/app.js`, every existing test | **Not modified.** |

## Non-goals

- **No schema change and no Alembic revision.** No `archived_at`, no per-engagement retention column, no ledger table, no legal-hold column (D-P4-4-C, G, L; open questions 2 and 5).
- **No automatic purge, scheduler, reminder, or startup completion** (D-P4-4-R). Completion of a pending purge is explicit too.
- **No client deletion**, no assessment-level unarchive, no change to assessment-level or evidence-level archive semantics (D-P4-4-A).
- **No audit-row deletion or scrubbing** (D-P4-4-I; open question 1).
- **No backup rotation or backup scrubbing**, and no `VACUUM` (D-P4-4-I, Q; open question 3).
- **No per-control hiding of write buttons** on archived pages (D-P4-4-F; open question 6).
- **No change to the dashboard beyond the filter**: no archived filter or archived section on the dashboard itself (PR-002's "archived" view is open question 7).
- No guard on operator scripts (D-P4-4-E).
- No `relationship()`.

## Test scenarios

All in `tests/test_retention.py`.

1. **Constants and structure.**
   - `PURGE_ORDER`, `RETAINED_TABLES`, `REFUSAL_REASONS`, `DEPENDENCY_CODES`, `ARCHIVABLE_STATUSES`, `RETENTION_YEARS_RANGE`, every event name, `EVENT_SCHEMA_VERSION`, `COMPLETION_SCRIPT_ACTOR`, `REASON_MESSAGES`, `DEPENDENCY_LABELS` and every message constant equal the exact values in this document.
   - `set(Base.metadata.tables) == set(PURGE_ORDER) | set(RETAINED_TABLES)`, the two are disjoint, and `PURGE_ORDER` is a valid delete order: for every FK in `Base.metadata` from child table X to parent table Y where both are in `PURGE_ORDER` and the FK is not `ON DELETE SET NULL`, `PURGE_ORDER.index(X) < PURGE_ORDER.index(Y)`.
   - The set of `(method, path)` for app routes whose path contains `/archive`, `/unarchive`, `/purge` or `/retention` is exactly the six routes of D-P4-4-O.
   - `inspect.getsource` of `archive_engagement`, `unarchive_engagement`, `set_client_retention`, `build_purge_plan`, `evaluate_purge`, `retention_state`, `archive_record`, `pending_purges`, `client_retention_view`, `engagement_ids_for_path`, `archived_engagement_ids` contains no `.commit(`; `purge_engagement` and `complete_pending_purge` (or `_finish_blob_removal`) do.
   - `alembic heads` is exactly `4e8c1a9d2b57`; `grep -rn "relationship(" app/models/` is empty.
   - Across `app/**/*.py`: `rmtree` appears only in `app/services/retention.py`; no file contains `delete(AuditEvent` or `delete(Client`; no file other than `retention.py` contains `delete(Evidence`, `delete(EvidenceVersion` or `delete(ReportSnapshot`.
2. **Archive (the plan's test, part 1).**
   - `POST /api/engagements/{E}/archive` with `reviewer_name=Priya` → 200, `HX-Redirect: /engagements/{E}`; `Engagement.status == "archived"`; exactly one new audit row, `engagement.archived`, actor `consultant:Priya`, entity `engagement`/E, metadata key set exact with `previous_status == "active"` and `retention_years == 7`; `archive_record(db, E)` returns it with an aware `archived_at`.
   - The dashboard and `GET /clients/{c}/engagements-list` (HTMX) no longer show E; `GET /clients/{c}` shows `data-archived-engagement` for E with its eligible date; `GET /engagements/{E}` → 200 with `data-archived-banner`, "Eligible for permanent purge on or after" and the formatted date `add_years(archived_at, 7)`, `data-unarchive-control`, `data-purge-preview-link`, and no `data-archive-control`; `GET /assessments/{A}` → 200 with `data-archived-banner`.
   - Refusals, each writing nothing (`_snapshot` equal): unknown id → 404 `ENGAGEMENT_NOT_FOUND`; already archived → 409 `ALREADY_ARCHIVED`; hand-set status `"draft"` → 409 `NOT_ARCHIVABLE`; an assessment with `status="analyzing"` → 409 `ARCHIVE_IN_FLIGHT`; an assessment with `desk_review_status="analyzing"` → 409 `ARCHIVE_IN_FLIGHT`; CAS race (patch `retention._in_flight_count` to set the engagement to `closed` through a second connection, then return 0) → 409 `ARCHIVE_CONFLICT`, status stays `closed`, no audit row.
   - A `closed` engagement archives with `previous_status == "closed"`.
3. **Read-only enforcement.**
   - **Structural:** every `APIRoute` in `app.routes` with a method in `{POST, PUT, PATCH, DELETE}`, other than the retention router's five non-GET routes, has `retention_router.archive_write_guard` among `[d.call for d in route.dependant.dependencies]`.
   - **The unresolvable set is exact:** the mutating routes (excluding the retention router) whose path has none of `{assessment_id}`, `{engagement_id}`, `{evidence_id}` are exactly `{("POST", "/engagements"), ("POST", "/assessments"), ("POST", "/assessments/new"), ("POST", "/api/assessments"), ("POST", "/magic/{token}")}`.
   - **Behavioural, every route:** build an archived engagement E with one assessment A (with a GapReport, a Conclusion, a Finding with an Action, a snapshot) and one Evidence Ev. Take `_snapshot`. For **every** mutating route whose path has at least one of the three parameters, substitute `assessment_id → A`, `engagement_id → E`, `evidence_id → Ev`, every other parameter → the id of a real row of the right type where one exists, else `"x"`, and send the method with an empty form body. Each response is **409** with `detail == ARCHIVED_READ_ONLY` and `X-Toast-Type: error`. After all of them, `_snapshot` is unchanged. The test asserts that the exercised set includes at least `POST /api/assessments/{assessment_id}/analyze`, `POST /assessments/{assessment_id}/run-analysis`, `POST /assessments/{assessment_id}/upload`, `DELETE /assessments/{assessment_id}`, `POST /api/evidence/{evidence_id}/transitions`, `DELETE /api/evidence/{evidence_id}/uses/{use_id}`, `POST /engagements/{engagement_id}/magic-links`, `POST /api/engagements/{engagement_id}/integrated-reports`, `POST /api/assessments/{assessment_id}/findings`, `POST /api/assessments/{assessment_id}/conclusions/{conclusion_id}/approve`, `POST /api/assessments/{assessment_id}/snapshots` and `PATCH /api/assessments/{assessment_id}/review/items/{item_id}`.
   - **Magic links:** a link created while E was active: `GET` and `POST /magic/{token}` after archive → 404 with a body byte-identical to a random-token 404; nothing written.
   - **Reads still work** on the archived engagement (each 200): `/engagements/{E}`, `/engagements/{E}/remediation`, `/engagements/{E}/integrated-reports`, `/assessments/{A}`, `/assessments/{A}/findings`, `/assessments/{A}/conclusions`, `/assessments/{A}/workpaper`, `/assessments/{A}/snapshots`, the snapshot file route, `/evidence/{Ev}`.
   - **Isolation:** a second, active engagement of the same client accepts a write while E is archived (for example `POST /engagements/{E2}/magic-links` → 200), and `engagement_ids_for_path`/`archived_engagement_ids` return the expected sets for `engagement_id`, `assessment_id`, `evidence_id`, an unknown id, and an assessment with `engagement_id = NULL`.
4. **Unarchive.**
   - Archive an `active` engagement, unarchive → 200, status `active`, one `engagement.unarchived` event with `archive_event_id` = the archive event and `restored_status == "active"`; a write that was refused in scenario 3 (for example creating a magic link) now succeeds. Same for a `closed` engagement → restored to `closed`.
   - Hand-set an engagement to `archived` with no archive event, unarchive → restored `active`, `archive_event_id` null.
   - Re-archive: a new archive event; `archive_record` returns the newer one (by `rowid`), and `retention_state.eligible_at` moves accordingly (the clock restarts).
   - Unarchive a non-archived engagement → 409 `NOT_ARCHIVED`; CAS race (status changed to `active` by a second connection between read and write, via patching `retention.archive_record`) → 409 `UNARCHIVE_CONFLICT`; each writes nothing.
5. **Retention setting.**
   - `POST /api/clients/{c}/retention retention_years=10` → 200, `Client.retention_years == 10`, one `client.retention_changed` event `{"from": 7, "to": 10, "schema_version": 1}`, entity `client`.
   - Each of `""`, `"0"`, `"51"`, `"7.5"`, `"-1"`, `"abc"`, missing → 400 `RETENTION_YEARS_INVALID`, nothing written. `"10"` again → 200, toast `Retention unchanged`, nothing written. Unknown client → 404 `CLIENT_NOT_FOUND`. CAS race → 409 `RETENTION_CONFLICT`.
   - Floor: archive at 7, lower the client to 2 → `retention_years_applied == 7`; raise to 10 → `10`.
   - The client page shows `data-retention-form` with the current value.
6. **Purge refused: retention not elapsed (the plan's test, part 2).**
   - Archive E now. `GET /engagements/{E}/purge` → 200 with `data-purge-reason="retention_not_elapsed"`, the formatted message, the `data-purge-count` rows equal to `build_purge_plan(...).row_counts`, and **no** `data-purge-form`; nothing written.
   - `POST /api/engagements/{E}/purge confirm_name=<exact name>` → 409; JSON `reasons == ["retention_not_elapsed"]`, `detail ==` the formatted message with `add_years(archived_at, 7)`, `eligible_at` its ISO string, `dependencies == []`, `layout_violations == 0`. `_snapshot` unchanged except exactly one new `engagement.purge_refused` audit row with the exact metadata.
   - Boundary, service-level with `now=`: `eligible_at - timedelta(microseconds=1)` → refused; `eligible_at` → no `retention_not_elapsed`. Archive on 29 Feb 2028 with 1-year retention → `eligible_at` is 28 Feb 2029.
7. **Purge refused: active dependencies.** Backdate the archive by 8 years. For each case separately (fresh engagements), the purge → 409 with `reasons == ["active_dependencies"]`, the exact `dependencies` entry, the exact `detail`, `_snapshot` unchanged except one `engagement.purge_refused` row:
   - (a) an `evidence_uses` row mapping E's evidence into another engagement's assessment → `evidence_used_elsewhere` 1;
   - (b) another engagement's `ConclusionRevision.citations_json` containing E's version id → `evidence_cited_elsewhere` 1;
   - (c) another engagement's `DeskReviewFinding.citations_json` containing it → `evidence_cited_elsewhere` 1;
   - (d) another engagement's `Action.history_json` containing it → `evidence_cited_elsewhere` 1;
   - (e) an Evidence row of another engagement with `assessment_id` in A → `evidence_linked_elsewhere` 1;
   - (f) another engagement's `EvidenceVersion.storage_path` under `evidence/{E}/` → `blob_shared_elsewhere` 1.
   - Citations **inside** E (E's own revisions citing E's evidence, created through the real pipeline) are not dependencies (covered by scenario 9 succeeding).
8. **Purge refused: every other reason, and "both".**
   - Archived yesterday **and** dependency (a) → `reasons == ["retention_not_elapsed", "active_dependencies"]`, `detail` = the two messages joined by one space.
   - Not archived → 409 `["not_archived"]` (`detail == "Only an archived engagement can be purged."`), one refusal row with `dependencies == []`.
   - Hand-set `status="archived"` with no archive event → `["archive_record_missing"]` (plus nothing else for a clean engagement).
   - Backdated archive with `clients.retention_years` hand-set to 0 → `["retention_invalid"]`.
   - Backdated archive with one in-set `EvidenceVersion.storage_path` hand-set to `elsewhere/x.pdf` and that file created → `["storage_layout_invalid"]`, `layout_violations == 1`, and `elsewhere/x.pdf` still exists afterwards; the same path **without** the file → eligible.
   - Wrong `confirm_name` (and blank, and different case) → 400 `CONFIRM_MISMATCH`, **nothing written, no audit row**. Unknown engagement → 404 `ENGAGEMENT_NOT_FOUND`.
   - The preview page lists every reason of the "both" case and each non-zero dependency (`data-purge-dependency=`), and shows no form.
9. **Successful purge (the plan's test, part 3).**
   - Build E with `_full_engagement(..., sentinel="PURGE-SENTINEL-7Q")` through real routes: two assessments (A1 analysed through the patched pipeline with Conclusions, one approved, a Finding with two Actions, one closed and verified with real closure evidence; A2 with questionnaire responses whose `notes` contain the sentinel, then assessment-level archived via `DELETE /assessments/{A2}`), evidence with two versions and an `EvidenceUse`, a desk review summary and findings with citations, an RFI document, a gap-report snapshot (issued) and a workpaper snapshot (draft), an integrated report snapshot (issued), a magic link with one client upload, and one legacy `assessment_documents` row inserted with Core `insert()` whose file is written under `upload_root/{A1}/legacy.pdf`. Build a **control** engagement E2 of the same client the same way with sentinel `"CONTROL-SENTINEL-3K"`.
   - Archive E, backdate 7 years + 1 day. `GET /engagements/{E}/purge` → 200 with `data-purge-form` and counts. Take the control's `_snapshot` restricted to E2's rows and files, and the pre-purge `row_counts`.
   - `POST /api/engagements/{E}/purge confirm_name=<name> reviewer_name=Priya` → 200, `HX-Redirect: /clients/{c}`, JSON `row_counts` equal to the preview counts and every value > 0 for the tables the fixture populated.
   - **Every** `PURGE_ORDER` table has zero rows for E's ids (query each table by the ids captured before the purge). The `clients` row is unchanged. E2's rows and files are byte-identical to before. None of E's blob roots exists on disk; `upload_root/evidence`, `upload_root/reports/assessments` and `upload_root/reports/engagements` still exist with E2's files in them.
   - Audit: every pre-existing `audit_events` row is unchanged (same ids, same content), plus exactly `engagement.purged` then `engagement.purge_blobs_removed`, both actor `consultant:Priya`, with exact metadata key sets; `row_counts` equals the pre-purge counts; `blob_roots` equals the D-P4-4-K list; `removed_roots` lists the roots that existed and `missing_roots` the rest.
   - `pending_purges(db) == []`. `GET /engagements/{E}` → 404. `GET /clients/{c}` shows a `data-purge-record` with "Files removed" and the engagement name. A second purge POST → 404 `ALREADY_PURGED`; `GET /engagements/{E}/purge` → 404.
   - `PRAGMA foreign_key_check` returns no rows; `PRAGMA integrity_check` is `ok`.
   - **secure_delete:** after `db.close()` and `engine.dispose()`, the raw bytes of the SQLite file do not contain `PURGE-SENTINEL-7Q` and do contain `CONTROL-SENTINEL-3K`.
10. **Crash safety and the failure-mode table (D-P4-4-L).** Each on a fresh, eligible engagement with blobs on disk.
    - (a) **Failure before commit:** patch `retention._write_purged_event` to raise `RuntimeError` → 500 `PURGE_FAILED`; `_snapshot` unchanged (every row, every file); no `engagement.purged` row; status still `archived`; a retry without the patch succeeds.
    - (b) **FK backstop:** a Finding in E2's assessment whose `conclusion_id` is one of E's Conclusions (hand-set) → 500 `PURGE_FAILED`, `_snapshot` unchanged.
    - (c) **Rowcount mismatch:** patch `retention.build_purge_plan` to return the real plan with `row_counts["gap_items"] + 1` → 500 `PURGE_FAILED`, `_snapshot` unchanged.
    - (d) **Blob removal fails after commit:** patch `retention._remove_tree` to call the real `shutil.rmtree` for the first root that exists and raise `OSError` for the next → 500, JSON `{"detail": PURGE_BLOBS_PENDING, "records_purged": true, "blobs_pending": true, …}`. Every E row is gone; `engagement.purged` exists; no `engagement.purge_blobs_removed`; the first root is gone and the later roots still exist; `pending_purges(db)` lists E with the ledger's roots; the client page shows "Files pending removal" and `data-purge-complete-control`. Remove the patch. `POST /api/engagements/{E}/purge/complete` → 200, `already_complete` false, every root gone, one completion event whose `missing_roots` includes the first root. A second call → 200 `already_complete` true, **no** new audit row. `POST …/purge/complete` for an engagement never purged → 404 `NO_PENDING_PURGE`.
    - (e) **Process death between phases:** patch `retention._remove_tree` to raise `SimulatedCrash(BaseException)`; call `retention.purge_engagement(...)` directly → it propagates. In a **new session** on the same engine: every E row is gone, `engagement.purged` is committed, every root still exists, `pending_purges` lists E. Then `scripts.complete_purges.run(new_db)` → returns 0, prints `PENDING …` and `COMPLETED <E> removed=<n> missing=<m>`; roots gone; completion event written; `run(new_db, list_only=True)` then prints nothing and returns 0.
    - (f) **Tampered ledger:** a hand-written `engagement.purged` event for an engagement that still exists → completion 409 `PURGE_LEDGER_INCONSISTENT`, nothing removed. A hand-written `engagement.purged` event (for a non-existent id) whose `blob_roots` contains `"../outside"`, or a root for an assessment id not in its `assessment_ids`, or is missing a root → 409 `PURGE_LEDGER_INVALID`; a directory `upload_root/../outside` created for the test still exists with its file.
    - (g) **Symlinked root:** replace `upload_root/evidence/{E}` with a symlink to a directory outside `upload_root` containing a file → the purge is refused with `storage_layout_invalid`, and the target file still exists.
11. **Concurrency.**
    - Purge with a stale preview: open the preview while archived, unarchive through the route, then POST the purge → 409 `["not_archived"]`, nothing deleted.
    - Double purge: after a successful purge, the same POST → 404 `ALREADY_PURGED` (the step-5 re-read path; also test step 1's path by calling the service with an id whose `engagement.purged` event exists and whose row is gone).
12. **Never auto-purge (D-P4-4-R).**
    - Grep of `app/**/*.py`: `purge_engagement(` appears only in `app/services/retention.py` (definition) and `app/routers/retention.py`; `complete_pending_purge(` only in `retention.py` (definition), `app/routers/retention.py` and `scripts/complete_purges.py`. `app/main.py` contains neither. `app/routers/retention.py` contains no `BackgroundTasks`.
    - An eligible archived engagement survives a full app start and stop (`with TestClient(app):` running the lifespan against the test DB via `settings.database_url`) and 3 GET requests: `_snapshot` unchanged.
13. **Nothing else moved.** The full suite passes with **no existing test file modified**.

## Done criteria

- `tests/test_retention.py` passes. `.venv/bin/pytest -q` passes in full: **502 + N**, N being the new cases (state the baseline you measured; if P4-1/P4-2/P4-3 merged first, their counts are in your baseline). In a fresh `git worktree`, expect the known one-time `_guard_dev_database_untouched` teardown error described in Current state; nothing else.
- `git diff main --stat -- tests/` shows **only** `tests/test_retention.py`.
- `git diff --stat main` shows changes **only** in: `app/services/retention.py` (new), `app/routers/retention.py` (new), `app/main.py`, `app/routers/web.py`, `app/templates/partials/engagement_retention.html` (new), `app/templates/pages/engagement_purge.html` (new), `app/templates/pages/engagement_detail.html`, `app/templates/pages/client_detail.html`, `app/templates/pages/assessment.html`, `scripts/complete_purges.py` (new), `docs/operations/retention-purge.md` (new), `docs/operations/backup-restore.md`, `tests/test_retention.py` (new), `tasks/todo.md` and this handoff.
- `git diff --stat main -- app/models alembic/versions app/services/evidence.py app/services/report_snapshots.py app/services/findings.py app/services/magic_links.py app/services/conclusion_review.py app/services/analysis_pipeline.py app/services/workpaper.py app/services/remediation_rollup.py app/services/report_content.py app/services/portfolio.py app/routers/analysis.py app/routers/assessments.py app/routers/conclusions.py app/routers/desk_review.py app/routers/documents.py app/routers/evidence.py app/routers/findings.py app/routers/integrated_reports.py app/routers/magic.py app/routers/questionnaire.py app/routers/reports.py app/routers/review.py app/routers/snapshots.py app/static scripts/backup.py scripts/restore.py scripts/migrate_legacy.py` is **empty**. `alembic heads` is exactly `4e8c1a9d2b57`. `grep -rn "relationship(" app/models/` is empty.
- **Smoke test** (per the project rule; record the outputs in Results). A fresh Alembic-built SQLite DB and a temporary `upload_dir`, with the in-process ASGI `TestClient` if a socket bind is refused (it has been refused in every prior Codex sandbox). Patch `app.routers.analysis.run_gap_analysis` to fixed items. Then:
  1. `POST /engagements` (new client) → engagement E; upload one PDF through `POST /assessments/{A}/upload`; run analysis once; generate a gap-report snapshot.
  2. Paste `find <upload_dir> -type f | sort` and `SELECT COUNT(*)` for `engagements, assessments, evidence, evidence_versions, conclusions, conclusion_revisions, report_snapshots, audit_events`.
  3. `POST /api/engagements/{E}/archive` → paste status and the audit row. `POST /assessments/{A}/upload` → paste the 409 and its toast header.
  4. `POST /api/engagements/{E}/unarchive`, then archive again. `POST /api/engagements/{E}/purge` with the right name → paste the 409 JSON (retention not elapsed).
  5. Backdate the archive event 7 years + 1 day by SQL. `GET /engagements/{E}/purge` → paste the `data-purge-count` values. `POST` the purge → paste the 200 JSON.
  6. Re-paste step 2's `find` and counts, and `SELECT action, entity_type, entity_id, metadata_json FROM audit_events ORDER BY rowid DESC LIMIT 2`.
  7. Repeat 1–5 on a second engagement with `retention._remove_tree` patched to raise `OSError` on its second call; paste the 500 JSON, `python scripts/complete_purges.py --list` output (pointing `DATABASE_URL`/`UPLOAD_DIR` at the smoke DB and directory), then the run without `--list`, and the final `find`.
  8. **Browser check** if a browser is available: archive from the engagement page, confirm the banner and the refused write toast, then walk the preview → typed name → confirm dialog → purge. If no browser is available, say so in Results. Do not claim it.

## Rollback

- **Code:** `git revert` removes the guard, routes, service and UI. Nothing in the schema changed. Engagements left in status `archived` then show again on the dashboard (the old filter only hides `closed`) and become writable, because nothing else in the reverted code reads `archived`. `engagement.*` and `client.retention_changed` audit rows remain as inert history. Retention values set through the new route stay in `clients.retention_years`, which the reverted app only displays.
- **Data:** **a purge cannot be rolled back by code.** The only way back is `scripts/restore.py` from a P1-6 backup taken before the purge, which also discards every write made after that backup, including the purge's own audit rows. Take a backup (`python scripts/backup.py`) before the first real purge on any environment that matters, and state this in the operations doc (step 8).
- **A pending purge after a revert:** its rows are already gone. Finish it before reverting (`python scripts/complete_purges.py`), or remove the listed directories by hand using the ledger's `blob_roots`.

## Open questions (deliberately flagged, not resolved here)

1. **Free text in retained audit rows about purged items.** `evidence_version.created.change_reason` (which P2-5 fills with the magic-link item title) and `evidence.status_changed.reason` survive a purge. Whether they must be scrubbed, and how that squares with an append-only audit log, is a product and legal call.
2. **Per-engagement retention override** (D11 "per client or engagement"). Needs a column and a rule for how it combines with the client value and the archive-time floor.
3. **Backups hold purged data.** P1-6 backups are never rotated. A backup retention policy (for example "no backup older than N days"), or an explicit "purged since backup" warning on restore, is needed before a real client pilot. Restoring a pre-purge backup today silently resurrects purged engagements and drops their purge records.
4. **Client deletion.** A client with no engagements left can't be removed.
5. **Legal hold** (PRD Evidence lifecycle; P3-2's hand-forward for issued snapshots). There is no legal-hold state. When one exists, it becomes a seventh refusal reason, checked in the same locked transaction.
6. **Hiding write controls on archived pages.** The server refuses them and the banners explain why, but buttons still render. A shared template flag could hide them later.
7. **PR-002's archived view on the dashboard.** Archived engagements are reachable from the client page only.
8. **Filesystem-level and journal remnants.** `secure_delete` covers the DB file only (D-P4-4-Q). Encrypted storage or secure file erasure is out of scope for a local single-user app.

## Report back

Append a `## Results` section to this file containing:
- The shipped constants and public signatures of `app/services/retention.py`, copied from the code (they must match D-P4-4-S).
- The `PURGE_ORDER` tuple as shipped, and the output of scenario 1's FK-order check.
- The exact list of mutating routes scenario 3 exercised, with their count, and the unresolvable set.
- `pytest -q` output for the new file and for the full suite, with the baseline you measured.
- The smoke outputs listed in Done criteria.
- Anything this document got wrong about the current code (a drifted symbol, a route the enumeration missed, a test that contradicts the spec, a guard that fires). **Name it explicitly and stop if it forces a design change. Do not pick an alternative.**
