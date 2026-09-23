# P2-1: Evidence service — hashing, blob storage, lifecycle state machine, legacy-document migration

**Plan:** `docs/plans/2026-09-21-002-revised-implementation-plan.md`, Phase 2, task P2-1, plus the "Evidence lifecycle states (P1 fix)" block under Target Schema and the `AssessmentDocument upload routes change | P2-1` row of "What breaks and how we handle it".
**Owner:** Claude designs + writes the failing suite → Codex implements (per `tasks/agent-ownership.md`). This is the Phase 2 gating task: P2-2 (citations point at `EvidenceVersion`), P2-3 (analysis runs record their evidence inputs), P2-5 (magic-link uploads create `Evidence`) and P2-6 (workpaper walks the evidence chain) all build on the state graph, the hashing contract and the "which evidence does an assessment see" rule pinned below. Every one of those is a decision made here, not by the implementer.
**Depends on:** P1-2 (`evidence`, `evidence_versions`, `evidence_uses`, `audit_events` tables) — **merged**. P1-4 (every UI-created Assessment has an `engagement_id`) — **merged**. P1-3 (`scripts/migrate_legacy.py`, which gives legacy assessments an engagement) — **merged**; this task must *not* require it to have been run (step 9).
**Blocks:** P2-2, P2-3, P2-4, P2-5, P2-6.
**Failing contract suite (already written, run it first):** `tests/test_evidence_service.py` — 43 collected cases, all red at `a7cd10c` for the intended reasons only: 38 on `ModuleNotFoundError: No module named 'app.services.evidence'`, 4 on the missing revision `7a3f1e2b9c80` / missing `EvidenceVersion.status` column, and 1 grep guard that finds the live `AssessmentDocument(` / `save_upload` call sites. Codex's job is to turn it green without editing its assertions. If a test looks wrong, stop and say so in `## Results` rather than changing it.

## Goal

Replace `AssessmentDocument` as the write path for uploaded material with the P1-2 `Evidence` / `EvidenceVersion` / `EvidenceUse` tables, driven by one service module, `app/services/evidence.py`, that:

- hashes every received file (SHA-256) and stores it write-once under the P1-6-backed upload tree;
- creates `Evidence` + `EvidenceVersion` rows that start in **quarantine** and are released by a malware-scan placeholder (auto-pass in v1, logged warning);
- adds new versions that **supersede** the prior version on release, never overwrite it;
- maps evidence to (assessment, framework, requirement) via `EvidenceUse`;
- enforces a lifecycle state machine for both Evidence and EvidenceVersion that rejects every transition not in an explicit table;
- writes an `audit_events` row for every creation, status change and mapping change.

The desk-review and analysis pipelines keep receiving exactly the same `documents` list shape they receive today, now sourced from Evidence (with a read-time fallback to not-yet-migrated `AssessmentDocument` rows). A human-run script migrates existing `AssessmentDocument` rows into Evidence.

## Current state

Grounded against `a7cd10c` on `docs/p1-progress-2026-09-22`. Re-locate everything by symbol name.

- **`app/models/evidence.py`** (P1-2): `Evidence` (`id`, `engagement_id` FK NOT NULL, `original_filename`, `storage_path`, `file_hash_sha256`, `file_size_bytes`, `mime_type`, `status`, `uploaded_by`, `created_at`), `EvidenceVersion` (`id`, `evidence_id` FK, `version_number`, `storage_path`, `file_hash_sha256`, `file_size_bytes`, `change_reason`, `created_at`), `EvidenceUse` (`id`, `evidence_id` FK, `assessment_id` FK, `requirement_id`, `framework_id`, `relevance`, `created_at`). All columns NOT NULL except `change_reason`. No CHECK constraints, no unique constraints beyond PKs. **Zero application code reads or writes these tables today.**
- **What those tables cannot hold yet**, and which the live pipeline needs: (a) extracted text (the only thing desk review and analysis actually consume); (b) the document category (fed to both prompts as `"category"`); (c) any link from Evidence to the Assessment it was uploaded through (the whole current UI is per-assessment); (d) a per-version status, so there is nowhere to record "v1 superseded"; (e) a per-version filename/MIME type, so a v2 in a different format than v1 is unrepresentable. Step 2 adds exactly these, and nothing else.
- **`app/models/assessment.py`, `AssessmentDocument`**: `assessment_id` FK, `filename`, `file_path` (stored as `os.path.join(settings.upload_dir, assessment_id, f"{uuid8}_{client_filename}")` — relative to the process CWD, and built from the raw client filename), `file_type`, `document_category`, `extracted_text`, `uploaded_at`. No hash, no versioning, hard-deleted on "Delete".
- **Writers of `AssessmentDocument`** (grep `AssessmentDocument(` in `app/`): `app/routers/documents.py` `upload_document` (JSON, `POST /api/assessments/{assessment_id}/documents`, 201 `DocumentResponse`; 400 unsupported type; 422 empty extraction) and `app/routers/web.py` `upload_document_web` (HTMX, `POST /assessments/{assessment_id}/upload`, returns `partials/document_list.html` + a "Document uploaded" toast; errors return `partials/upload_status.html` at **200**). Both call `document_processor.save_upload()`, `detect_file_type()`, `extract_text()`, then bump `assessment.status` `created → documents_uploaded`. Outside `app/`, `scripts/seed_test_companies.py` writes rows with fake `file_path`s and synthetic `extracted_text` (no file on disk) — relevant to step 9.
- **Deleters:** `documents.py` `delete_document` (`DELETE /api/assessments/{aid}/documents/{document_id}`, 204) and `web.py` `delete_document_web` (`DELETE /assessments/{aid}/documents/{document_id}`, re-renders the list). Both `db.delete(doc)` — a hard delete, which D11 rules out for evidence.
- **Readers of `extracted_text`** (the pipeline P2-1 must not break):
  - `app/routers/analysis.py` (inside the analysis trigger, search `db.query(AssessmentDocument)`): builds `documents = [{"filename", "category", "text"}]` → `run_gap_analysis(..., documents=...)`; `has_documents = bool(documents)` also gates the "≥80% questionnaire" check.
  - `app/services/desk_review.py` `run_desk_review`: builds `[{"id", "filename", "category", "text"}]`, raises `ValueError("No documents uploaded for this assessment")` when empty, and builds `doc_id_by_filename = {d.filename: d.id}` which `_persist_findings` writes to `DeskReviewFinding.document_id`.
  - `app/routers/desk_review.py` `trigger_desk_review`: a `.count()` of the assessment's documents, 400 `"Upload documents before running desk review."` when zero.
  - `app/routers/web.py`: `assessment_detail` (context key `documents`, used by `pages/assessment.html` for the tab pill count and by `partials/documents_tab.html` / `partials/document_list.html`) and `report_summary` (timeline step `("Documents", bool(documents))`).
- **`DeskReviewFinding.document_id`** is `ForeignKey("assessment_documents.id", ondelete="SET NULL")`, and SQLite foreign keys are enforced (`app/database.py` sets `PRAGMA foreign_keys=ON`). **An Evidence id written into that column for a file that has no `AssessmentDocument` row is an FK violation.** Its only consumer is the JSON output of `GET /api/assessments/{aid}/desk-review`. Step 8 handles this.
- **Storage/backup:** `settings.upload_dir` (default `"uploads"`). `scripts/backup.py` / `scripts/restore.py` (P1-6) back up and restore the whole `upload_dir` tree together with the DB. Anything stored under `upload_dir` is covered by D9's RPO/RTO; anything outside it is not.
- **`audit_events`** (`actor`, `action`, `entity_type`, `entity_id`, `metadata_json`, `created_at`) exists and has **no writer** anywhere. Product requirement §Auditability (line ~351 of the PRD) requires Evidence lifecycle changes to be attributable and queryable.
- **Framework requirement ids** come from `FrameworkRegistry.get_all_controls(fw_id)` → `Control.id` (e.g. `CH2.CONSENT.1`, `ISO.A5.1`, `NIST.GV.OC.01`). The registry is populated by `app.main._register_frameworks()` at startup.
- **Baseline suite:** `pytest -q` → 265 passed, 1 failed. The one failure (`tests/test_no_blended_scoring.py::test_blended_function_and_topic_maturity_are_gone`) is environmental: its `grep -rn` matches stale `__pycache__/*.cpython-311.pyc` / `-314.pyc` files from other interpreters. `find app scripts -name __pycache__ -prune -exec rm -rf {} +` makes it pass. Not in scope to fix here (it is flagged in Claude's report), but do not count it as a P2-1 regression.

## Decisions (made here so they are not relitigated)

### D-P2-1-A. Evidence ↔ Assessment scoping: engagement-owned evidence + a nullable *originating assessment*, and one membership rule

**Decision:** `Evidence` stays owned by its Engagement (`engagement_id` NOT NULL, as P1-2 has it — the Engagement is the product's "shared evidence library"). Add **`evidence.assessment_id`: nullable FK → `assessments.id`**, meaning *"the assessment through whose upload surface this evidence was received"*. It is written once at creation and never changed. It is NULL for engagement-level intake (P2-5 magic links, P4-1 AWS snapshots).

**The membership rule — the single definition of "the evidence an assessment sees"** (implemented once, in `analysis_documents()` and `evidence_panel_rows()`, step 7):

> Evidence *E* is in scope for Assessment *A* iff `E.assessment_id == A.id` **or** an `EvidenceUse` row exists with `evidence_id == E.id and assessment_id == A.id`.
> It is **fed to analysis/desk review** iff it is in scope **and** `E.status == "active"`.

**Why not the alternative (engagement-level evidence connected to assessments only through per-requirement `EvidenceUse`):** an upload through the Documents tab is not mapped to any requirement at upload time — desk review is what *discovers* which requirements a document speaks to. If per-requirement `EvidenceUse` were the only connection, a freshly uploaded policy would be invisible to the desk review that is supposed to map it: a silent chicken-and-egg failure. Relaxing `evidence_uses.requirement_id` to nullable to fake an "assessment-level use" would overload the mapping table with a sentinel row that every later consumer (P2-6 workpaper, PR-023 request dedup) must remember to filter out — exactly the easy-to-violate trap the ownership contract says Claude must close.
**Why not "all engagement evidence feeds every assessment in it":** PRD rule 6 / PR-025 — evidence reuse across assessments is explicit and consultant-confirmed. An engagement with a baseline and a validation assessment must not silently analyse one assessment's evidence in the other.
**Why the OR-clause now:** P2-1 already builds `EvidenceUse` mapping, and a consultant mapping evidence to assessment B's requirement *is* the explicit, audited reuse act PR-025 describes. Defining membership as the union today means P2-5/PR-025 never has to change the reader — they only create rows.

Constraints that fall out: mapping is **same-engagement only** (cross-engagement/client-level reuse is later work), and only the originating assessment may archive or re-version an Evidence (a mapped-in row is read-only in assessment B's panel; archiving is an engagement-wide effect).

**Orphans:** an Assessment with `engagement_id IS NULL` (legitimate per P1-4 §2 until `migrate_legacy.py` runs) cannot receive new Evidence — `evidence.engagement_id` is NOT NULL and inventing an engagement is P1-3's job. Upload is refused with an explicit error (409 JSON / error partial HTML). Its legacy `AssessmentDocument` rows keep feeding analysis through the fallback in step 7.

### D-P2-1-B. Lifecycle: two state machines — the logical Evidence record and its immutable byte-versions

The plan's single graph (`Requested → Uploaded → Quarantined → Active → Superseded → Archived → Purged`, with `Invalidated`/`Rescoped` branches) conflates two things: *quarantine is a property of bytes* (a scan result for one received file), while *active/invalidated/archived is a property of the logical record*. With one status column on `Evidence`, uploading v2 would either put the whole Evidence back into quarantine (making v1 unusable while v2 is scanned) or leave v2's scan state unrecorded. So:

**`EvidenceVersion.status`** (new column): `quarantined`, `active`, `superseded`, `rejected`. All transitions are system-driven:

| From | To | When |
|---|---|---|
| `quarantined` | `active` | scan passes (`release_from_quarantine`) |
| `quarantined` | `rejected` | scan fails |
| `active` | `superseded` | a *newer* version of the same Evidence is released to `active` |

`superseded` and `rejected` are terminal. Invariant: **at most one `active` version per Evidence**, and supersession happens **at release, not at upload** — so a v2 that is still in (or fails) quarantine never displaces a good v1. (In v1 release is synchronous, so the plan's "upload new version → old is Superseded" test holds; the precise point is pinned for when a real, asynchronous scanner lands.)

**`Evidence.status`** (existing column; lowercase snake values, matching every other status in the codebase): `quarantined`, `active`, `rejected`, `invalidated`, `archived`.

| From | To | Actor | Reason required | Meaning |
|---|---|---|---|---|
| `quarantined` | `active` | system | no | first version released |
| `quarantined` | `rejected` | system | no | first version failed the scan |
| `active` | `invalidated` | consultant | **yes** | content judged invalid (wrong doc, forged, out of scope) |
| `invalidated` | `active` | consultant | **yes** | re-validation (plan: "requires consultant confirmation") |
| `active` | `archived` | consultant | no | soft delete (D11) — replaces the old hard delete |
| `invalidated` | `archived` | consultant | no | soft delete |
| `rejected` | `archived` | consultant | no | tidy a rejected upload out of the panel |
| `archived` | `active` | consultant | **yes** | restore (PRD PR-003 "restorable"); guarded: requires the Evidence to have an `active` version |

Every pair not in this table — including self-transitions — is rejected with `InvalidTransition`. A consultant request for a `system` edge is rejected with `TransitionNotPermitted` (403): **nobody can manually release a file from quarantine**, which is what makes the placeholder a real gate once a scanner is plugged in.

New versions do **not** change `Evidence.status`. They may be added only while the Evidence is `active` or `invalidated`, and only when no version is currently `quarantined`. An `invalidated` Evidence that receives a corrected, released v2 stays `invalidated` until a consultant re-validates it — an upload is not a confirmation.

**Deliberately excluded from P2-1, with owner:**
- `requested` — an evidence *request* is not received material; it belongs to the EvidenceRequest/magic-link model (**P2-5**). The P1-2 schema has no request table, so a `requested` Evidence row would have no file, hash or blob to satisfy its NOT NULL columns.
- `uploaded` / `received` — transient inside one atomic `ingest_upload` call; never persisted, so not a state.
- Evidence-level `superseded` — modelled at version level (above).
- `rescoped`, `expired` — reuse suggestions and currency (PR-025/PR-026, later Phase 2/3 work that also needs Conclusions to exist to compute impact).
- `purged`, `retained`, legal hold — **P4-4** (the plan's own "most destructive code path"). `archived` is the D11 "retention-aware soft delete"; P4-4 adds `archived → purged` behind the retention/dependency checks. P2-1 contains **no** code path that deletes an `Evidence`/`EvidenceVersion` row or a blob.

### D-P2-1-C. Duplicate uploads: refuse, scoped, never silent

**Upload:** refuse with `DuplicateEvidence` (409) when an Evidence in the **same engagement** with the **same originating `assessment_id`** (NULL matches NULL) and `status` in `{"quarantined", "active", "invalidated"}` has **any** version whose `file_hash_sha256` equals the new file's. The message names the existing file.
- *Different assessment in the same engagement:* allowed (separate receipt for a separate scope; linking it instead is the PR-025 reuse workflow, not a silent dedupe).
- *Existing copy is `archived` or `rejected`:* allowed ("archive and re-upload" must not be a dead end).
- **Not** silently deduplicated (returning the existing row): a consultant who uploads a file and is told "uploaded" must be looking at a row that records *that* receipt, with *that* timestamp and actor — chain of custody.

**New version:** refuse with `DuplicateEvidence` (409) when the new bytes equal the **current active** version's hash. Equal to an older, superseded version is **allowed** (a revert is a legitimate new version with its own reason).

**Hash equality means identical content.** A real SHA-256 collision is not a design consideration.
**Race:** the check is check-then-insert with no conditional unique index (SQLite cannot express "unique among non-archived rows of the same scope" cheaply). Acceptable for the single-user MVP; named in Rollback/Report back so it is not forgotten.
**Legacy migration bypasses dedupe** (`allow_duplicate=True`): every `AssessmentDocument` must map 1:1 to an Evidence or the read-time fallback would keep serving it (step 9).

### D-P2-1-D. Legacy `AssessmentDocument` migration is **in scope**, as a human-run script, backed by a read-time fallback

In scope because the moment readers switch to Evidence, un-migrated documents must still reach analysis, and they cannot be versioned, archived or mapped until they are Evidence. As a **script** (`scripts/migrate_documents_to_evidence.py`), not an Alembic data migration, because: it must read and copy files from `upload_dir` (not a schema concern, and `lifespan()` runs `alembic upgrade head` at every startup); it must skip orphan assessments until `migrate_legacy.py` has run, and be re-runnable after; and P1-3 set the precedent (idempotent, backup-first, human-invoked).

**Read-time fallback** (the P1-5 `report_framework_scores` pattern): the one reader returns un-migrated `AssessmentDocument` rows alongside Evidence, so there is no window in which deploying P2-1 before running the script makes documents vanish from analysis. The migration **reuses the `AssessmentDocument.id` as the `Evidence.id`**, which makes "is this legacy row migrated?" a primary-key lookup and keeps existing `DeskReviewFinding.document_id` values meaningful. `AssessmentDocument` rows are never modified or deleted (they remain FK targets for desk-review findings, and the rollback path).

### D-P2-1-E. Extracted text lives on the version; extraction happens only after release

Text is derived from specific bytes, so `extracted_text` goes on `EvidenceVersion`. Extraction (which for images sends the file to the vision LLM) runs **after** the version is released from quarantine — never on quarantined or rejected bytes. The legacy rule "an upload whose extraction is empty is refused" is preserved: the whole ingest (rows, audit events, blob) is rolled back. P2-1 is a storage swap, not a UX change, and an unparseable file silently contributing nothing to analysis is the failure mode to avoid.

## Required approach

### 1. Model changes (`app/models/evidence.py`)

No `relationship()` (house rule; `grep -rn "relationship(" app/models/` must stay empty).

```python
class Evidence(Base):
    # existing columns unchanged, plus:
    assessment_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("assessments.id"), nullable=True, index=True
    )  # originating assessment; written once; NULL for engagement-level intake
    document_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
```
Add this comment above `original_filename`: `# original_filename, storage_path, file_hash_sha256, file_size_bytes and mime_type record the FIRST receipt (v1) and are frozen at creation. Never read them to get current content: use app.services.evidence.current_version().`

```python
class EvidenceVersion(Base):
    __table_args__ = (
        UniqueConstraint("evidence_id", "version_number",
                         name="uq_evidence_versions_evidence_id_version_number"),
    )
    # existing columns unchanged; file_hash_sha256 gains index=True
    # (index name ix_evidence_versions_file_hash_sha256), plus:
    status: Mapped[str] = mapped_column(String(20), server_default="quarantined")
    original_filename: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(100))
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)

class EvidenceUse(Base):
    __table_args__ = (
        UniqueConstraint("evidence_id", "assessment_id", "framework_id", "requirement_id",
                         name="uq_evidence_uses_mapping"),
    )
```

### 2. Alembic revision — pinned id `7a3f1e2b9c80`

File `alembic/versions/7a3f1e2b9c80_p2_1_evidence_service_columns.py`, `revision = "7a3f1e2b9c80"`, `down_revision = "5c7c75960f43"`. The id is pinned because the contract suite and three existing tests reference it. Hand-written (do not autogenerate against live metadata — `tests/test_alembic_baseline_immutable.py` guards that pattern for older revisions; follow the same discipline). All ALTERs through `op.batch_alter_table` (SQLite).

`upgrade()`, in this order:
1. `evidence`: add `assessment_id` (String(36), nullable) and `document_category` (String(50), nullable); `create_foreign_key("fk_evidence_assessment_id_assessments", "assessments", ["assessment_id"], ["id"])`; `create_index("ix_evidence_assessment_id", ["assessment_id"])`.
2. `evidence_versions`: add `status` (String(20), `nullable=False`, `server_default="quarantined"` — any pre-existing row comes up fail-closed, excluded from analysis), `original_filename` (String(255), nullable **for now**), `mime_type` (String(100), nullable for now), `extracted_text` (Text, nullable); `create_index("ix_evidence_versions_file_hash_sha256", ["file_hash_sha256"])`; `create_unique_constraint("uq_evidence_versions_evidence_id_version_number", ["evidence_id", "version_number"])`.
3. Backfill: `UPDATE evidence_versions SET original_filename = (SELECT original_filename FROM evidence WHERE evidence.id = evidence_versions.evidence_id), mime_type = (SELECT mime_type FROM evidence WHERE evidence.id = evidence_versions.evidence_id)`. (No writer exists, so this is expected to touch zero rows — it is there so the NOT NULL step can never fail on a hand-edited DB.)
4. `evidence_versions`: `alter_column("original_filename", nullable=False)`, `alter_column("mime_type", nullable=False)`.
5. `evidence_uses`: `create_unique_constraint("uq_evidence_uses_mapping", ["evidence_id", "assessment_id", "framework_id", "requirement_id"])`.

`downgrade()`: first a guard mirroring P1-2's — if `evidence`, `evidence_versions` or `evidence_uses` has any row, raise `RuntimeError("Refusing to downgrade past P2-1 revision 7a3f1e2b9c80: these tables still hold data: <table (n rows), ...>. Downgrading would permanently drop evidence columns -- restore a verified backup instead.")`. Then drop, in reverse: the evidence_uses constraint; the evidence_versions constraint, index and four columns; the evidence FK, index and two columns.

**Existing tests that must be updated in lockstep** (they hard-code the current head):
- `tests/test_target_schema.py` — `test_downgrade_removes_only_p1_2_schema_and_upgrade_restores_it` and `test_downgrade_refuses_when_p1_2_data_is_present` call `command.downgrade(config, "-1")` expecting to undo P1-2. Change both to `command.downgrade(config, "6fcd9e575309")`. No assertion changes.
- `tests/test_data_integrity.py` `TestAlembicRoundTrip.test_fresh_upgrade_downgrade_upgrade_round_trip` — `assert current == "5c7c75960f43"` becomes `"7a3f1e2b9c80"` (its `downgrade -1` now round-trips P2-1, which is what a round-trip test of the newest revision should do).
- `tests/test_alembic_baseline_immutable.py` — both probe templates' `down_revision = "5c7c75960f43"` become `"7a3f1e2b9c80"` (otherwise the probe forks a second head and `upgrade head` fails).

### 3. Storage layout and hashing

- **Path**, relative to `settings.upload_dir`: `evidence/{engagement_id}/{evidence_id}/v{version_number}.{file_type}` — e.g. `evidence/3f2c…/9a1b…/v2.pdf`. `storage_path` stores this **relative** string (forward slashes). Deliberate divergence from `AssessmentDocument.file_path` (CWD-relative, `upload_dir`-prefixed): a relative-to-`upload_dir` path survives a P1-6 restore into a different `upload_dir`.
- **No part of the client filename appears in the path.** The client filename is metadata only (`original_filename`), normalised by `_display_filename(name) = (name or "").replace("\\", "/").rsplit("/", 1)[-1].strip()[:255] or "document"`. (The legacy `save_upload` joins the raw client filename into the path; that function is deleted in step 6.)
- **Write-once:** `path.parent.mkdir(parents=True, exist_ok=True)`, then `open(path, "xb")` — an existing blob is never overwritten; a `FileExistsError` propagates (it indicates a bug, and must not be swallowed).
- **Resolution:** `blob_path(storage_path) -> Path(settings.upload_dir) / storage_path`. Read `settings.upload_dir` **at call time** (tests and the migration script redirect it); never cache it at import.
- **Hash:** `sha256_hex(content) = hashlib.sha256(content).hexdigest()` — 64 lowercase hex chars, computed over the exact bytes written. `file_size_bytes = len(content)`.
- **MIME type** from the *detected* file type, never the client's `Content-Type`:
  ```python
  FILE_TYPE_TO_MIME = {
      "pdf": "application/pdf",
      "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp",
      "txt": "text/plain",   # legacy migration only — never accepted from an upload
  }
  ```
  Uploads use `document_processor.detect_file_type(filename)` (pdf/docx/png/jpg/jpeg/webp only). The displayed `file_type` of a version is the suffix of its `storage_path` (`Path(storage_path).suffix[1:]`), so it is always exact.
- **`Evidence`'s own file columns = v1's values, frozen** (see the model comment in step 1).

### 4. `app/services/evidence.py` — public API, exact

Module-level imports that tests patch: `from app.services.document_processor import detect_file_type, extract_text` (patch target: `app.services.evidence.extract_text`). `scan_blob` must be looked up as a module global at call time (patch target: `app.services.evidence.scan_blob`).

```python
EVIDENCE_STATUSES = ("quarantined", "active", "rejected", "invalidated", "archived")
VERSION_STATUSES = ("quarantined", "active", "superseded", "rejected")
BLOCKING_DUPLICATE_STATUSES = ("quarantined", "active", "invalidated")
RELEVANCE_VALUES = ("primary", "supporting", "contextual")
CONSULTANT_ACTOR = "consultant"          # no auth yet; every UI/API action
SYSTEM_ACTOR = "system"
SCAN_ACTOR = "system:scan-placeholder"
SCAN_REJECTED_MESSAGE = "File failed the malware scan and was not released from quarantine."
FILE_TYPE_TO_MIME = {...}                # step 3

class TransitionRule(NamedTuple):
    actor_kind: str        # "system" | "consultant"
    requires_reason: bool

EVIDENCE_TRANSITIONS: dict[tuple[str, str], TransitionRule]   # exactly the D-P2-1-B table
VERSION_TRANSITIONS: frozenset[tuple[str, str]]               # exactly the three version edges

@dataclass(frozen=True)
class IngestResult:
    evidence: Evidence
    version: EvidenceVersion
    released: bool          # False => the scan rejected this version
```

**Errors.** One hierarchy; routers translate with `except EvidenceError as exc: raise HTTPException(exc.status_code, exc.message)` (JSON) or render `exc.message` (HTML).

| Class | Base | `status_code` |
|---|---|---|
| `EvidenceError(Exception)` — `__init__(self, message)`, sets `self.message` | — | 400 |
| `EvidenceNotFound` | `EvidenceError` | 404 |
| `EvidenceValidationError` | `EvidenceError` | 422 |
| `UnsupportedFileType` | `EvidenceValidationError` | **400** (legacy JSON contract) |
| `EvidenceConflict` | `EvidenceError` | 409 |
| `InvalidTransition`, `DuplicateMapping`, `EngagementRequired` | `EvidenceConflict` | 409 |
| `DuplicateEvidence` — extra attr `existing_evidence_id: str` | `EvidenceConflict` | 409 |
| `TransitionNotPermitted` | `EvidenceError` | 403 |

**Exact messages** (the suite asserts these verbatim):

| Condition | Class | Message |
|---|---|---|
| no such evidence / version / assessment / use | `EvidenceNotFound` | `Evidence not found` / `Evidence version not found` / `Assessment not found` / `Evidence use not found` |
| unsupported type | `UnsupportedFileType` | `Unsupported file type. Upload PDF, DOCX, PNG, JPG, JPEG, or WEBP files.` |
| zero-byte file | `EvidenceValidationError` | `The uploaded file is empty.` |
| extraction empty | `EvidenceValidationError` | `Could not extract text from this document. If it is a scanned PDF, try uploading it as a PNG or JPEG screenshot instead.` |
| assessment has no engagement | `EngagementRequired` | `This assessment is not linked to an engagement. Run scripts/migrate_legacy.py before uploading evidence.` |
| duplicate upload | `DuplicateEvidence` | `This file is identical to '{existing.original_filename}' already in this engagement's evidence.` |
| duplicate of current version | `DuplicateEvidence` | `This file is identical to the current version (v{n}).` |
| version on wrong evidence status | `InvalidTransition` | `Cannot add a version to evidence in status '{status}'.` |
| a version already quarantined | `InvalidTransition` | `A new version is already awaiting release from quarantine.` |
| blank change reason | `EvidenceValidationError` | `A change reason is required when uploading a new version.` |
| unknown target status | `EvidenceValidationError` | `Unknown evidence status '{to}'.` |
| edge not in table | `InvalidTransition` | `Invalid evidence transition: {from} -> {to}.` |
| version edge not in table | `InvalidTransition` | `Invalid evidence version transition: {from} -> {to}.` |
| consultant requests a system edge | `TransitionNotPermitted` | `Transition {from} -> {to} is system-driven and cannot be requested directly.` |
| system code requests a consultant edge | `TransitionNotPermitted` | `Transition {from} -> {to} requires a consultant.` |
| reason missing where required | `EvidenceValidationError` | `A reason is required for this transition.` |
| restore/re-validate with no active version | `InvalidTransition` | `Evidence has no active version to restore.` |
| mapping across engagements | `EvidenceValidationError` | `Evidence and assessment belong to different engagements.` |
| mapping non-active evidence | `EvidenceConflict` | `Only active evidence can be mapped to a requirement.` |
| framework not on assessment | `EvidenceValidationError` | `Framework '{fw}' is not selected for this assessment.` |
| unknown requirement | `EvidenceValidationError` | `Unknown requirement '{req}' for framework '{fw}'.` |
| bad relevance | `EvidenceValidationError` | `Relevance must be one of: primary, supporting, contextual.` |
| duplicate mapping | `DuplicateMapping` | `This evidence is already mapped to that requirement.` |

**Transaction rule.** Only the two `ingest_*` orchestrators commit — because they own a filesystem side effect that must be undone if the DB work fails. On any exception they `db.rollback()`, unlink every blob they wrote in this call (`unlink(missing_ok=True)`; leave directories), and re-raise. Every other mutating function `db.flush()`es and leaves `commit()` to the caller (router or script). `receive_evidence` / `receive_version` write their blob *after* all validation and dedupe checks and unlink it themselves if their own `flush()` raises.

**Functions** (all keyword-only after `db`):

- `sha256_hex(content: bytes) -> str`, `evidence_root() -> Path` (`Path(settings.upload_dir) / "evidence"`), `blob_path(storage_path: str) -> Path`.
- `scan_blob(path: Path) -> bool` — the placeholder. Body: `logger.warning("Malware scanning is not configured; auto-releasing %s from quarantine (P2-1 placeholder).", path.name)`; `return True`. `logger = logging.getLogger(__name__)`.
- `check_evidence_transition(from_status, to_status, *, actor_kind) -> TransitionRule` — pure. Order: `to_status in EVIDENCE_STATUSES` (else `EvidenceValidationError`) → `(from, to) in EVIDENCE_TRANSITIONS` (else `InvalidTransition`) → `rule.actor_kind == actor_kind` (else `TransitionNotPermitted`, message by direction). Returns the rule.
- `check_version_transition(from_status, to_status) -> None` — pure; `InvalidTransition` unless the pair is in `VERSION_TRANSITIONS`.
- `receive_evidence(db, *, engagement_id, assessment_id, filename, content, category, uploaded_by, actor, file_type=None, evidence_id=None, created_at=None, change_reason=None, allow_duplicate=False) -> tuple[Evidence, EvidenceVersion]` — no scan, no extraction, no commit. Order: resolve `file_type` (`detect_file_type(filename)` when `None`; must be a key of `FILE_TYPE_TO_MIME` → else `UnsupportedFileType`) → `len(content) == 0` → `EvidenceValidationError` → dedupe (D-P2-1-C) unless `allow_duplicate` → generate ids in Python (`evidence_id or _new_id()`, version id `_new_id()`) → write blob `v1.{file_type}` → add `Evidence(status="quarantined", assessment_id=..., document_category=category or None, ...frozen v1 fields)` and `EvidenceVersion(version_number=1, status="quarantined", original_filename=..., mime_type=..., change_reason=change_reason)`; when `created_at` is given set it on both → audit `evidence.created` then `evidence_version.created` → flush.
- `receive_version(db, *, evidence_id, filename, content, change_reason, actor) -> EvidenceVersion` — no scan/extraction/commit. Order: evidence exists → `evidence.status in ("active", "invalidated")` → no `quarantined` version exists → `change_reason.strip()` non-empty → file type → non-empty content → not identical to current active version → `version_number = max + 1` → write blob → add version (`quarantined`) → audit `evidence_version.created` → flush.
- `release_from_quarantine(db, *, version_id, actor=SCAN_ACTOR) -> EvidenceVersion` — no commit. Order: version exists → `version.status == "quarantined"` (via `check_version_transition`) → `passed = scan_blob(blob_path(version.storage_path))` →
  - pass: for each other `active` version of that evidence → `superseded` (audit) **first**; then this version → `active` (audit); if `evidence.status == "quarantined"` → evidence `active` (system edge, audit).
  - fail: version → `rejected` (audit); if `evidence.status == "quarantined"` → evidence `rejected` (system edge, audit).
- `transition_evidence(db, *, evidence_id, to_status, actor, reason=None) -> Evidence` — the **consultant** entry point (`actor_kind="consultant"` always). Order: evidence exists → `check_evidence_transition(...)` → `rule.requires_reason` and blank `reason` → `EvidenceValidationError` → for `to_status == "active"` from `invalidated`/`archived`: an `active` version must exist, else `InvalidTransition("Evidence has no active version to restore.")` → set status → audit `evidence.status_changed` → flush.
- `map_evidence(db, *, evidence_id, assessment_id, framework_id, requirement_id, relevance, actor) -> EvidenceUse` — order: evidence exists → assessment exists → same engagement → `evidence.status == "active"` → `framework_id in assessment.frameworks` → `requirement_id in {c.id for c in FrameworkRegistry.get_all_controls(framework_id)}` → `relevance in RELEVANCE_VALUES` → no existing identical (evidence, assessment, framework, requirement) row → add → audit `evidence_use.created` → flush. (The unique constraint is the race backstop.)
- `unmap_evidence(db, *, evidence_id, use_id, actor) -> None` — use exists **and** `use.evidence_id == evidence_id` (else `EvidenceNotFound("Evidence use not found")`) → audit `evidence_use.deleted` (metadata = the row's fields) → `db.delete(use)` → flush. This is the only `db.delete` in the module; it deletes a *mapping*, never evidence.
- `ingest_upload(db, *, assessment_id, filename, content, category, uploaded_by=CONSULTANT_ACTOR) -> IngestResult` — **commits**. Order: assessment exists (`EvidenceNotFound("Assessment not found")`) → `assessment.engagement_id` not None (`EngagementRequired`) → `receive_evidence(..., engagement_id=assessment.engagement_id, assessment_id=assessment.id, actor=uploaded_by)` → `release_from_quarantine` → if released: `text = extract_text(blob_path(version.storage_path), file_type)`; `not text.strip()` → `EvidenceValidationError` (whole call rolled back, blob unlinked); else `version.extracted_text = text`; and `if assessment.status == "created": assessment.status = "documents_uploaded"` → commit → `IngestResult(evidence, version, released)`. When **not** released: no extraction, no status bump, **commit** (the rejected receipt is kept for the audit trail) and return `released=False`.
- `ingest_new_version(db, *, evidence_id, filename, content, change_reason, actor=CONSULTANT_ACTOR) -> IngestResult` — **commits**; same shape: `receive_version` → `release_from_quarantine` → extract only if released (empty → rollback) → commit.
- `current_version(db, evidence_id) -> EvidenceVersion | None` — the `active` version, else `None`.
- `verify_version(db, version_id) -> bool` — re-hashes the blob; `False` when missing or different. The chain-of-custody check; no route in P2-1.
- `analysis_documents(db, assessment_id) -> list[dict]` and `evidence_panel_rows(db, assessment_id) -> list[dict]` — step 7.
- `evidence_detail(db, evidence_id) -> dict` — step 5's `EvidenceOut` shape; `EvidenceNotFound` if missing.

**Audit events** — exact `action` / `entity_type` / `entity_id` / `metadata_json` (`json.dumps(..., sort_keys=True)`); `actor` is the function's `actor` argument (`SCAN_ACTOR` for scan-driven changes):

| action | entity_type | entity_id | metadata keys |
|---|---|---|---|
| `evidence.created` | `evidence` | evidence id | `assessment_id`, `sha256`, `size_bytes`, `uploaded_by`, `version_id` |
| `evidence_version.created` | `evidence_version` | version id | `change_reason`, `evidence_id`, `sha256`, `size_bytes`, `version_number` |
| `evidence_version.status_changed` | `evidence_version` | version id | `evidence_id`, `from`, `to` |
| `evidence.status_changed` | `evidence` | evidence id | `from`, `reason`, `to` |
| `evidence_use.created` / `evidence_use.deleted` | `evidence_use` | use id | `assessment_id`, `evidence_id`, `framework_id`, `relevance`, `requirement_id` |

A successful first upload therefore writes exactly, in insertion (`rowid`) order: `evidence.created`, `evidence_version.created`, `evidence_version.status_changed` (quarantined→active), `evidence.status_changed` (quarantined→active). A released v2 writes: `evidence_version.created`, `evidence_version.status_changed` (v1 active→superseded), `evidence_version.status_changed` (v2 quarantined→active).

### 5. Routes — exact table

New JSON router `app/routers/evidence.py`, `APIRouter(prefix="/api/evidence", tags=["evidence"])`, registered in `app/main.py` with the other API routers (before `web.router`). New schemas in `app/schemas/evidence.py`.

| Method | Path | Request | Success | Errors |
|---|---|---|---|---|
| GET | `/api/evidence/{evidence_id}` | — | 200 `EvidenceOut` | 404 |
| POST | `/api/evidence/{evidence_id}/versions` | multipart `file`, `change_reason` (Form, default `""`) | 201 `EvidenceOut` | 404, 400, 409, 422; scan rejected → 422 `SCAN_REJECTED_MESSAGE` (rows committed) |
| POST | `/api/evidence/{evidence_id}/transitions` | JSON `{"to_status": str, "reason": str \| null}` | 200 `EvidenceOut` | 404, 409, 403, 422 |
| POST | `/api/evidence/{evidence_id}/uses` | JSON `{"assessment_id", "framework_id", "requirement_id", "relevance"}` | 201 `EvidenceUseOut` | 404, 409, 422 |
| DELETE | `/api/evidence/{evidence_id}/uses/{use_id}` | — | 204 | 404 |

Existing JSON router `app/routers/documents.py` — **same paths and status codes**, reimplemented on the service (compatibility, like P1-4's `POST /assessments` shim; no redirects — a 307 on a multipart POST buys nothing):

| Method | Path | Now does | Success | Errors |
|---|---|---|---|---|
| POST | `/api/assessments/{aid}/documents` | `ingest_upload`; `category: DocumentCategory` enum validation kept | 201 `DocumentResponse` | 404, 400 unsupported, 409 duplicate / no engagement, 422 empty / extraction / scan rejected |
| GET | `/api/assessments/{aid}/documents` | `evidence_panel_rows` | 200 `list[DocumentResponse]` | 404 |
| DELETE | `/api/assessments/{aid}/documents/{document_id}` | `transition_evidence(to_status="archived")` | 204 | 404 `Document not found` (unknown id, or evidence whose `assessment_id != aid`); 409 legacy row: `Legacy document: run scripts/migrate_documents_to_evidence.py before archiving it.`; 409 invalid transition |

`DocumentResponse` gains one field, `status: str` (evidence status, or `"legacy"`). Mapping from a panel row: `id`, `assessment_id` (= the path `aid`), `filename`, `file_type`, `document_category` (= row `category`), `text_length`, `uploaded_at`, `status`.

HTML routes in `app/routers/web.py`:

| Method | Path | Returns | Notes |
|---|---|---|---|
| POST | `/assessments/{aid}/upload` | `partials/document_list.html` + toast `Document uploaded` | Reimplemented on `ingest_upload`. Every `EvidenceError`, and `released=False` (`SCAN_REJECTED_MESSAGE`), renders `partials/upload_status.html` with `error=message` at **200** (existing pattern). |
| DELETE | `/assessments/{aid}/documents/{evidence_id}` | `partials/document_list.html` | Archive. 404 unknown / not originating here; 409 legacy row. |
| POST | `/assessments/{aid}/evidence/{evidence_id}/versions` | `partials/document_list.html` + toast `New version uploaded` | **New.** Form: `file`, `change_reason`. 404 unless `evidence.assessment_id == aid`. Errors → `upload_status.html` at 200. |
| GET | `/evidence/{evidence_id}` | `pages/evidence_detail.html` | **New** (the plan's URL-strategy path). 404 if missing. |

Declare the new `/evidence/...` page route next to the P1-4 `/clients` / `/engagements` routes.

**`EvidenceOut`** (`app/schemas/evidence.py`):
```
EvidenceVersionOut: id, version_number, status, original_filename, mime_type,
                    file_hash_sha256, file_size_bytes, change_reason: str|None,
                    text_length: int, created_at
EvidenceUseOut:     id, evidence_id, assessment_id, framework_id, requirement_id, relevance, created_at
EvidenceOut:        id, engagement_id, assessment_id: str|None, original_filename, mime_type,
                    document_category: str|None, status, uploaded_by, file_hash_sha256,
                    file_size_bytes, created_at,
                    current_version: EvidenceVersionOut|None,   # the active version
                    versions: list[EvidenceVersionOut],         # ascending version_number
                    uses: list[EvidenceUseOut]                  # ascending (created_at, id)
```
`extracted_text` is **never** returned by the API (size; `text_length` only).

### 6. Pipeline glue — minimal, shape-preserving

The prompt builders must receive **byte-identical dict shapes**. Each call site builds its existing dict from the reader, key for key:

- `app/routers/analysis.py`: `documents = [{"filename": d["filename"], "category": d["category"], "text": d["text"]} for d in analysis_documents(db, assessment_id)]`.
- `app/services/desk_review.py` `run_desk_review`: `docs = analysis_documents(db, assessment_id)`; empty → the existing `ValueError`; `documents = [{"id": d["id"], "filename": d["filename"], "category": d["category"], "text": d["text"]} for d in docs]`; **`doc_id_by_filename = {d["filename"]: d["legacy_document_id"] for d in docs}`** — the FK-safe value (step 8).
- `app/routers/desk_review.py` `trigger_desk_review`: `if not analysis_documents(db, assessment_id): 400` (same message).
- `app/routers/web.py`: `assessment_detail` context `documents` = `evidence_panel_rows(...)` and new key `analysable_document_count = len(analysis_documents(...))`; `partials/documents_tab.html`'s desk-review gate `{% if documents %}` becomes `{% if analysable_document_count %}`. `report_summary`'s timeline step becomes `("Documents", bool(analysis_documents(db, assessment_id)))`.
- Delete `document_processor.save_upload` (no caller remains; it built paths from raw client filenames). Remove now-unused `AssessmentDocument` imports from `web.py`, `documents.py`, `analysis.py`, `desk_review.py` (router and service).

After this step, `app/` contains **no** `AssessmentDocument(` constructor call and no `save_upload` reference (grep-guarded by the suite). Known, accepted side effect: `document_processor._extract_image` embeds `os.path.basename(file_path)` in its output, so a screenshot's extracted text now begins `[Screenshot: v1.png]` instead of `[Screenshot: 1a2b3c4d_original.png]`. The real filename still reaches the prompt via the `filename` key. Do not change `document_processor` to compensate.

### 7. The two readers — exact shapes, order and query budget

**`analysis_documents(db, assessment_id) -> list[dict]`** — what the pipeline sees. Each dict has exactly the keys `{"id", "filename", "category", "text", "legacy_document_id", "source"}`:
- Evidence part: in-scope (D-P2-1-A) evidence with `status == "active"`, ordered `(Evidence.created_at, Evidence.id)` ascending. `id` = evidence id; `filename` = the active version's `original_filename`; `category` = `evidence.document_category or "other"`; `text` = the active version's `extracted_text or ""`; `source = "evidence"`; `legacy_document_id` = the evidence id if it is also the id of one of **this assessment's** `AssessmentDocument` rows (i.e. a migrated document), else `None`.
- Legacy part, appended after: this assessment's `AssessmentDocument` rows whose id is **not** an `Evidence.id` in any status (a migrated-then-archived document must not resurrect through the fallback), ordered `(uploaded_at, id)`. `id` = `legacy_document_id` = doc id; `filename`, `category` = `document_category`, `text` = `extracted_text or ""`; `source = "legacy"`.
- **Query budget: ≤ 4 statements**, independent of row count:
  ```python
  used = select(EvidenceUse.evidence_id).where(EvidenceUse.assessment_id == assessment_id)
  evs = (db.query(Evidence)
           .filter(Evidence.status == "active",
                   or_(Evidence.assessment_id == assessment_id, Evidence.id.in_(used)))
           .order_by(Evidence.created_at, Evidence.id).all())                       # 1
  vers = (db.query(EvidenceVersion)
            .filter(EvidenceVersion.evidence_id.in_([e.id for e in evs]),
                    EvidenceVersion.status == "active").all()) if evs else []         # 2
  legacy = (db.query(AssessmentDocument)
              .filter(AssessmentDocument.assessment_id == assessment_id)
              .order_by(AssessmentDocument.uploaded_at, AssessmentDocument.id).all())  # 3
  migrated = {i for (i,) in db.query(Evidence.id)
                                .filter(Evidence.id.in_([d.id for d in legacy]))} if legacy else set()  # 4
  ```

**`evidence_panel_rows(db, assessment_id) -> list[dict]`** — what the Documents tab and the compat JSON list show. In-scope evidence with `status != "archived"` plus un-migrated legacy rows, **newest first** (`created_at`/`uploaded_at` descending — matching today's list order). Same ≤ 4-query shape (query 2 loads **all** versions of the listed evidence). Each row:
```
{"id": str, "source": "evidence" | "legacy", "filename": str, "category": str,
 "file_type": str, "status": str,               # evidence status, or "legacy"
 "version_count": int, "current_version_number": int | None,
 "sha256_prefix": str | None,                   # first 12 hex chars of the displayed version
 "text_length": int, "uploaded_at": datetime,   # Evidence.created_at / uploaded_at
 "mapped_in": bool,                             # in scope only via EvidenceUse
 "can_archive": bool, "can_add_version": bool}
```
The *displayed version* is the `active` one, else the highest `version_number`. `filename`/`file_type`/`sha256_prefix`/`text_length` come from it. `current_version_number` is the active version's number or `None`. `can_archive` = evidence row, not `mapped_in`, status in `{"active", "invalidated", "rejected"}`. `can_add_version` = evidence row, not `mapped_in`, status in `{"active", "invalidated"}`, no `quarantined` version. Legacy rows: `version_count = 1`, `current_version_number = None`, `sha256_prefix = None`, `mapped_in`/`can_*` all `False`.

`evidence_detail` / `GET /evidence/{id}`: evidence (1) + versions (1) + uses (1); the HTML page adds engagement, client and originating assessment by `db.get` — **6** statements, fixed.

### 8. `DeskReviewFinding.document_id` — keep the FK valid, don't widen scope

The column's FK targets `assessment_documents.id`. The reader's `legacy_document_id` is non-NULL only for ids that exist in `assessment_documents` (legacy rows and migrated evidence, whose id was reused), so new desk-review findings stay FK-valid. For evidence uploaded after P2-1 it is `None`: those findings lose the per-document link in the desk-review JSON output until **P2-2** replaces the link with citations to `EvidenceVersion`. Do **not** retarget the FK or add a column to `desk_review_findings` in this task.

### 9. `scripts/migrate_documents_to_evidence.py` — exact behaviour

Mirror `scripts/migrate_legacy.py`'s structure.

```python
MIGRATION_ACTOR = "system:migration"
MIGRATION_UPLOADED_BY = "migration:assessment_documents"

@dataclass
class DocumentMigrationStats:
    migrated: int = 0          # Evidence rows created by this call
    text_only: int = 0         # subset of migrated whose original file was missing
    skipped_existing: int = 0  # already migrated (Evidence with the same id exists)
    skipped_orphan: int = 0    # assessment has no engagement
    skipped_empty: int = 0     # file missing AND no extracted text: nothing to preserve
    warnings: list[str] = field(default_factory=list)

def run_document_migration(session: Session) -> DocumentMigrationStats
def main(argv: list[str] | None = None) -> int
```

`run_document_migration`, for every `AssessmentDocument` ordered `(uploaded_at, id)`:
1. `db.get(Evidence, doc.id)` exists → `skipped_existing += 1`, continue.
2. Assessment's `engagement_id is None` → `skipped_orphan += 1`, warning `f"AssessmentDocument {doc.id}: assessment {doc.assessment_id} has no engagement; run scripts/migrate_legacy.py first."` (also `logger.warning`), continue.
3. Resolve the original file: first existing of `Path(doc.file_path)` and `Path(settings.upload_dir) / doc.assessment_id / Path(doc.file_path).name`.
   - Found → `content = file.read_bytes()`, `file_type = doc.file_type`, `change_reason = f"Migrated from assessment_documents (original file copied from {doc.file_path})."` The legacy file is **copied**, never moved or deleted.
   - Missing, `doc.extracted_text` non-blank → `content = doc.extracted_text.encode("utf-8")`, `file_type = "txt"`, `change_reason = f"Migrated from assessment_documents: original file missing at {doc.file_path}; blob is the previously extracted text."`, `text_only += 1`, warning.
   - Missing and no text → `skipped_empty += 1`, warning, continue.
4. `receive_evidence(session, evidence_id=doc.id, engagement_id=..., assessment_id=doc.assessment_id, filename=doc.filename, content=content, file_type=file_type, category=doc.document_category, uploaded_by=MIGRATION_UPLOADED_BY, actor=MIGRATION_ACTOR, created_at=doc.uploaded_at, change_reason=change_reason, allow_duplicate=True)` → `release_from_quarantine(session, version_id=..., actor=MIGRATION_ACTOR)` → `version.extracted_text = doc.extracted_text` (**verbatim; never re-extract** — re-extraction would re-call the vision LLM and change what earlier analyses saw) → `session.commit()`; on exception `session.rollback()`, unlink that document's blob, re-raise. `migrated += 1`.

The `AssessmentDocument` row is not modified. Seeded demo data (fake `file_path`, text only) therefore migrates as text-only evidence and keeps working.

`main`: flags `--db-url`, `--upload-dir` (assigned to `settings.upload_dir` before any work), `--backup-out-dir` (default `backups`), `--skip-backup` (hidden). Calls module-level `create_backup(db_path, upload_dir, out_dir)` (imported as `from scripts.backup import create_backup`) **before opening a write transaction** unless `--skip-backup`; if it raises, print to stderr and return 1 without writing. Prints the backup dir and `Document migration complete: {migrated} migrated ({text_only} text-only), {skipped_existing} already migrated, {skipped_orphan} orphaned, {skipped_empty} empty` and returns 0. It is never run by the app.

### 10. Templates

- `partials/document_list.html` — **rewrite** over panel rows (context: `documents`, `assessment_id`). Columns: File (link to `/evidence/{{ row.id }}` for evidence rows), Category, Type, Status (badge), Version (`v{{ row.current_version_number }}` of `{{ row.version_count }}`), SHA-256 (`{{ row.sha256_prefix }}…` in `font-mono`), Actions. Actions only when the flag allows: **Archive** (`hx-delete="/assessments/{{ assessment_id }}/documents/{{ row.id }}"`, `hx-target="#document-list"`, `hx-swap="innerHTML"`, `hx-confirm="Archive {{ row.filename }}? It will be excluded from analysis but retained."`) and a `<details>` "New version" form (`hx-post="/assessments/{{ assessment_id }}/evidence/{{ row.id }}/versions"`, `hx-encoding="multipart/form-data"`, same target/swap; required `file` input and required `change_reason` text input). Legacy rows show the `legacy` badge and the text *"Uploaded before evidence versioning. Run `scripts/migrate_documents_to_evidence.py` to enable versioning and archiving."*; `mapped_in` rows show *"Mapped from another assessment"*. Keep the existing empty state. Add `dark:` variants throughout (the current file has none).
- `components/evidence_status_badge.html` — **new**, expects `status`. `quarantined` amber "Quarantined", `active` green "Active", `superseded` gray "Superseded", `rejected` red "Rejected", `invalidated` red "Invalidated", `archived` gray "Archived", `legacy` gray "Legacy (not migrated)"; unknown → title-cased gray.
- `pages/evidence_detail.html` — **new**. Breadcrumb `Portfolio / {{ client.name }} / {{ engagement.name }} / {{ evidence.original_filename }}` (link the first three to `/`, `/clients/{id}`, `/engagements/{id}`); link back to the originating assessment when present. Metadata block (status badge, category, uploaded_by, received at, full v1 SHA-256). Versions table (number, status badge, filename, type, size, full SHA-256 in `font-mono break-all`, received at, change reason). Uses table (assessment link, framework, requirement, relevance) with an empty state. Read-only — no action buttons.
- `partials/documents_tab.html` — only the desk-review gate change from step 6.

## Key files

| File | Why it matters |
|---|---|
| `app/services/evidence.py` (new) | The whole contract: constants, transition tables, errors, primitives, orchestrators, readers. |
| `app/models/evidence.py` | Step 1 columns/constraints; the "frozen v1 fields" comment. |
| `alembic/versions/7a3f1e2b9c80_p2_1_evidence_service_columns.py` (new) | Step 2; pinned revision id; downgrade guard. |
| `app/routers/evidence.py`, `app/schemas/evidence.py` (new) | New JSON API (step 5). |
| `app/routers/documents.py`, `app/schemas/assessment.py` | Compat JSON routes; `DocumentResponse.status`. |
| `app/routers/web.py` | `upload_document_web`, `delete_document_web`, new version route, `/evidence/{id}` page, `assessment_detail` + `report_summary` reader swap. |
| `app/routers/analysis.py`, `app/services/desk_review.py`, `app/routers/desk_review.py` | Reader swap only — shape-preserving (step 6); `legacy_document_id` for the FK (step 8). |
| `app/services/document_processor.py` | `detect_file_type`/`extract_text` reused unchanged; `save_upload` deleted. |
| `app/models/desk_review.py` | `DeskReviewFinding.document_id` FK → `assessment_documents` — why step 8 exists. Not modified. |
| `app/models/audit_event.py` | First writer of this table. |
| `scripts/migrate_documents_to_evidence.py` (new) | Step 9. `scripts/migrate_legacy.py` is the structural template. |
| `scripts/backup.py` | `create_backup` — called by the migration's `main`; also why blobs must live under `upload_dir`. |
| `app/templates/partials/document_list.html`, `documents_tab.html`, `components/evidence_status_badge.html`, `pages/evidence_detail.html` | Step 10. |
| `tests/test_evidence_service.py` | The contract. Also update `tests/integration/test_document_upload.py` (it asserts `AssessmentDocument` rows and patches `app.routers.web.save_upload`; rewrite it against Evidence and redirect `settings.upload_dir` to `tmp_path`), plus the three Alembic-head tests listed in step 2. `tests/integration/test_desk_review.py` seeds `AssessmentDocument` directly and must keep passing unchanged (it now exercises the legacy fallback). |

## Non-goals

- Do **not** build real malware scanning (ClamAV, a cloud AV API, async scan queues). `scan_blob` is a logged auto-pass placeholder; PRD open question 5 decides the real control.
- Do **not** build citations or change `DeskReviewFinding`'s schema/FK (**P2-2**), record analysis inputs or touch `AnalysisRun` (**P2-3**), or change prompt construction. The `documents` dicts handed to `run_gap_analysis` / `_call_claude_desk_review` keep their current keys exactly.
- Do **not** add `requested`, `rescoped`, `expired`, `purged`, legal hold, retention enforcement or any purge path. No code in `app/` may delete an `Evidence` or `EvidenceVersion` row or a blob. (**P2-5**, PR-025/026, **P4-4**.)
- Do **not** add an engagement-level upload route, magic-link intake, cross-engagement mapping or reuse suggestions. `receive_evidence` supports `assessment_id=None` for P2-5; nothing calls it that way yet.
- Do **not** add HTML UI for mapping, invalidation or restore. Those are JSON-only in P2-1; the evidence page is read-only. (UI lands with P2-4/P2-6.)
- Do **not** add blob download/preview routes, or a file-size limit (none exists today; P2-5 introduces per-link limits).
- Do **not** drop, modify or stop migrating-from the `AssessmentDocument` model/table, and do **not** run `migrate_documents_to_evidence.py` from the app or at startup.
- Do **not** modify `scripts/seed_test_companies.py` (it keeps writing `AssessmentDocument`, which the fallback serves; **P4-2** rewrites it). Note: its reset path hard-deletes `Assessment` rows and will hit FK errors on assessments that have Evidence/engagements — pre-existing class of issue since P1-3, out of scope.
- Do **not** tighten the HTMX upload's free-text `category` (the JSON route's enum validation stays; the HTMX form posts from a fixed `<select>`).
- Do **not** add `relationship()` anywhere.
- Do **not** fix pre-existing cosmetic issues: the HTMX error partial replacing `#document-list`, and the tab-pill count not refreshing after an upload.

## Test scenarios

All in `tests/test_evidence_service.py` (already written — FK-enforcing Alembic-built SQLite per test, `settings.upload_dir` redirected to `tmp_path`, `extract_text` patched on the service module; numbering below matches the test docstrings).

1. **Upload creates Evidence + v1 with the correct hash.** One `Evidence` (engagement, originating assessment, `original_filename`, `mime_type == "application/pdf"`, `file_hash_sha256 == sha256(bytes)`, size, `status == "active"`, `uploaded_by == "consultant"`, `document_category`) and one `EvidenceVersion` (`version_number == 1`, `status == "active"`, same hash, `storage_path == f"evidence/{eng}/{ev}/v1.pdf"`, blob bytes equal the upload, `extracted_text` = the extractor's output). Evidence's frozen fields equal v1's. The storage path contains no part of the client filename. Assessment status bumped to `documents_uploaded`.
2. **Quarantine placeholder + audit trail.** The warning `Malware scanning is not configured` is logged; `audit_events` holds exactly the four actions of step 4, in order, with `from`/`to` metadata `quarantined → active`.
3. **Scan rejection.** With `scan_blob` patched to `False`: `released is False`, evidence and version `rejected`, rows committed, `extract_text` never called, assessment status unchanged; the JSON compat upload returns 422 with `SCAN_REJECTED_MESSAGE`.
4. **New version supersedes on release.** v1 `superseded`, v2 `active` at `v2.pdf` with its own hash and `change_reason`; Evidence's frozen fields still v1's; `analysis_documents` serves only v2's text and filename; audit contains v1 `active → superseded`.
5. **A rejected new version leaves v1 active.**
6. **State machine is exactly the designed graph; everything else is refused.** `EVIDENCE_TRANSITIONS` / `VERSION_TRANSITIONS` equal the D-P2-1-B tables; every other ordered pair of statuses raises `InvalidTransition` (exhaustive); consultant requests for system edges raise `TransitionNotPermitted`; unknown status → `EvidenceValidationError`; the service refuses `active → quarantined` and a reason-less invalidation, leaving status unchanged and writing no audit row; HTTP maps these to 409 / 403 / 422.
7. **Consultant transitions and analysis visibility.** invalidate (excluded) → re-validate (included) → archive (excluded from reader and panel; rows and blob retained) → restore (included). `rejected → archived → active` is refused with `Evidence has no active version to restore.`
8. **Duplicates.** Same bytes, same assessment → 409 naming the existing file, no new rows or blobs; after archiving the original → allowed; same bytes to a second assessment in the engagement → allowed. New version identical to current → 409; identical to superseded v1 → allowed as v3.
9. **EvidenceUse mapping.** Valid mapping creates the row and an `evidence_use.created` audit event; duplicate → `DuplicateMapping`; framework not on assessment, unknown requirement, bad relevance, cross-engagement → the exact 422 messages; non-active evidence → 409. Mapping assessment A's evidence to assessment B's requirement makes it appear in B's `analysis_documents` (as `mapped_in` in B's panel, read-only); unmapping removes it and writes `evidence_use.deleted`.
10. **Reader contract.** Exact key set, evidence-then-legacy order, `source`/`legacy_document_id` values; a migrated-then-archived legacy document is **not** resurrected; ≤ 4 SQL statements with 3 evidence + 2 legacy rows.
11. **Desk review reads evidence and stays FK-valid.** With `_call_claude_desk_review` stubbed to return one evidence-map item per document, `run_desk_review` receives both an Evidence-sourced and a legacy document with the historical dict keys, and the persisted findings carry `document_id == None` for the new evidence and the legacy id for the legacy row, under enforced foreign keys.
12. **Unmigrated assessment.** Upload to an assessment with `engagement_id=None` → `EngagementRequired` / HTTP 409; no rows, blobs or audit events.
13. **Validation failures write nothing.** Unsupported type (400), empty file, empty extraction (422, legacy message) — each leaves zero Evidence/EvidenceVersion/AuditEvent rows and no blob. New-version validation order: blank reason, then type, then duplicate.
14. **Compat routes.** JSON POST 201 with `id` == the Evidence id and `status == "active"`; GET lists evidence and legacy (`status == "legacy"`); DELETE archives (204; row and blob kept; drops out of GET); DELETE of a legacy id → 409 and the `AssessmentDocument` survives; unknown → 404. HTMX upload 200 creates Evidence and **no** `AssessmentDocument`; HTMX archive and new-version routes re-render the list; `GET /evidence/{id}` shows both versions' full SHA-256, the `Superseded` badge, and the client and engagement names; missing → 404. Only the originating assessment can archive (mapped-in DELETE → 404). HTMX upload errors render `upload_status.html` at 200 with the service message.
15. **New JSON API.** `GET /api/evidence/{id}` returns the `EvidenceOut` key set with no `extracted_text`; versions POST 201; transitions 200/409/403/422; uses POST 201 / DELETE 204.
16. **Alembic.** Head is `7a3f1e2b9c80`; the new columns, FK, indexes and both unique constraints exist and are enforced; downgrade to `5c7c75960f43` refuses while evidence rows exist and succeeds (columns gone) when empty.
17. **Legacy migration script.** Real file → hash of the file bytes, legacy file still present; missing file with text → text-only `.txt` blob hashing the UTF-8 text, `change_reason` prefix, `text_only` counted; missing and empty → skipped; orphan → skipped with warning; `Evidence.id == doc.id`, `created_at == uploaded_at`, `extracted_text` verbatim, `extract_text` never called, `AssessmentDocument` rows unchanged; second run is a no-op; `main` backs up first and aborts without writing if the backup raises.
18. **Standing guards.** No `AssessmentDocument(` constructor and no `save_upload` in `app/**/*.py` (source files only — `.pyc` excluded, see baseline note).
19. **Chain of custody.** `verify_version` is `True` for an intact blob and `False` after the blob is altered or removed.

## Done criteria

- `tests/test_evidence_service.py` passes unmodified; `pytest -q` passes in full (modulo the pre-existing stale-`.pyc` failure if `__pycache__` isn't cleared), including the updated `test_document_upload.py`, `test_target_schema.py`, `test_data_integrity.py`, `test_alembic_baseline_immutable.py`.
- `alembic upgrade head` → `7a3f1e2b9c80`; downgrade guard refuses with data present.
- `grep -rn "AssessmentDocument(" app/ --include=*.py` and `grep -rn "save_upload" app/ --include=*.py` are empty; `grep -rn "relationship(" app/models/` is empty; the only `db.delete(` in `app/services/evidence.py` is on an `EvidenceUse`.
- Every `EvidenceError` message in the step 4 table is emitted verbatim.
- Smoke-tested live per the project's smoke-test rule: run the app (`uvicorn app.main:app --reload`, or the in-process ASGI fallback P1-4/P1-5 used if the sandbox refuses a socket bind), then on a real engagement's assessment: upload a PDF through the Documents tab → see it `Active` with a hash prefix; upload a new version with a reason → `v2 of 2`; open `/evidence/{id}` → v1 `Superseded`, v2 `Active`, full hashes match `shasum -a 256` of the two files; archive it → it leaves the panel, and its blobs are still on disk; trigger desk review with the LLM mocked → it receives the evidence text. Then run `scripts/migrate_documents_to_evidence.py` against a **copy** of the dev DB and uploads tree, and run it a second time.

## Rollback

- **Code:** `git revert`. `AssessmentDocument` rows are never modified by P2-1, so the reverted app sees every pre-P2-1 document exactly as before. Documents uploaded *while P2-1 was live* exist only as Evidence and become invisible to the reverted app — re-upload them, or restore the P1-6 backup taken before deploy.
- **Schema:** `alembic downgrade 5c7c75960f43` succeeds only while the three evidence tables are empty (guarded). With evidence present, restore the P1-6 backup (`scripts/restore.py`) — the supported rollback for this project.
- **Migration script:** idempotent and additive (it copies files, never moves them). Undo = restore the backup `main()` took before writing (its path is printed), exactly as for P1-3.
- **Blobs:** everything P2-1 writes is under `{upload_dir}/evidence/`; after a revert + restore it can be removed as a whole.
- **Known residual risk:** duplicate detection is check-then-insert (D-P2-1-C); two truly concurrent identical uploads can both succeed. Single-user MVP; revisit when auth/multi-user lands.

## Results

### Routes

| Method | Path | Success | Template or response model |
|---|---|---:|---|
| GET | `/api/evidence/{evidence_id}` | 200 | `EvidenceOut` |
| POST | `/api/evidence/{evidence_id}/versions` | 201 | `EvidenceOut` |
| POST | `/api/evidence/{evidence_id}/transitions` | 200 | `EvidenceOut` |
| POST | `/api/evidence/{evidence_id}/uses` | 201 | `EvidenceUseOut` |
| DELETE | `/api/evidence/{evidence_id}/uses/{use_id}` | 204 | — |
| POST | `/api/assessments/{assessment_id}/documents` | 201 | `DocumentResponse` |
| GET | `/api/assessments/{assessment_id}/documents` | 200 | `list[DocumentResponse]` |
| DELETE | `/api/assessments/{assessment_id}/documents/{document_id}` | 204 | — |
| POST | `/assessments/{assessment_id}/upload` | 200 | `partials/document_list.html` + `Document uploaded` toast |
| DELETE | `/assessments/{assessment_id}/documents/{evidence_id}` | 200 | `partials/document_list.html` |
| POST | `/assessments/{assessment_id}/evidence/{evidence_id}/versions` | 200 | `partials/document_list.html` + `New version uploaded` toast |
| GET | `/evidence/{evidence_id}` | 200 | `pages/evidence_detail.html` |

No route-table deviation from Required approach step 5. The TCP Uvicorn bind was refused by the managed sandbox, so the smoke used the specified in-process ASGI fallback.

### Lifecycle tables shipped

`EVIDENCE_TRANSITIONS`:

| From | To | Actor | Reason |
|---|---|---|---|
| quarantined | active | system | no |
| quarantined | rejected | system | no |
| active | invalidated | consultant | yes |
| invalidated | active | consultant | yes |
| active | archived | consultant | no |
| invalidated | archived | consultant | no |
| rejected | archived | consultant | no |
| archived | active | consultant | yes |

`VERSION_TRANSITIONS`:

| From | To |
|---|---|
| quarantined | active |
| quarantined | rejected |
| active | superseded |

### Schema and tests

Alembic revision shipped: `7a3f1e2b9c80`, down revision `5c7c75960f43`. The four specified existing test files were updated for the P2-1 head/model contract: `test_document_upload.py`, `test_target_schema.py`, `test_data_integrity.py`, and `test_alembic_baseline_immutable.py`. The integration upload test now asserts Evidence and redirects storage to its temporary upload tree; the three Alembic updates follow step 2. During full-suite verification, four additional stale `5c7c75960f43` head assertions were found in `test_data_integrity.py` and `test_startup_invariants.py`; those were updated to `7a3f1e2b9c80` so the suite can reflect the pinned head. This is handoff drift, not a contract change.

### Legacy migration copy run

The source dev DB and `uploads/` tree were copied to `/private/tmp/p2-1-migration.TLrgUI`. A legacy text-only AssessmentDocument was seeded in the copy only to exercise the migration path; the live DB was not used as a migration target.

| Run | migrated | text-only | already migrated | orphaned | empty | AssessmentDocument rows |
|---|---:|---:|---:|---:|---:|---:|
| First | 1 | 1 | 0 | 0 | 0 | 1 before / 1 after |
| Immediate second | 0 | 0 | 1 | 0 | 0 | 1 |

The first run printed `Document migration complete: 1 migrated (1 text-only), 0 already migrated, 0 orphaned, 0 empty`; the second printed `0 migrated (0 text-only), 1 already migrated, 0 orphaned, 0 empty`. Both runs took the backup-first path.

### Live smoke counts

The live dev DB was schema-empty before startup; the app startup migrated it to the P2-1 head. Counts below are immediately before and after the upload/version/restore-for-desk-review/final-archive smoke sequence.

| Resource | Before | After |
|---|---:|---:|
| `evidence` | 0 | 1 |
| `evidence_versions` | 0 | 2 |
| `evidence_uses` | 0 | 0 |
| `audit_events` | 0 | 10 |
| blob files under `uploads/evidence/` | 0 | 2 |

Stored hashes matched the two `shasum -a 256` outputs:

```text
v1: 7a92ece634429b7ba2fd151e7520619e63faa89e6b777f0d7bab89d5e081707a  uploads/evidence/acd7d731-16f4-4823-9d26-c63328e5e29e/b6eba50f-8267-4e4d-8780-8b133663923c/v1.pdf
v2: e662e3137749233348ec8788fb835e689b8e66935d3e642e35ad19ede423f472  uploads/evidence/acd7d731-16f4-4823-9d26-c63328e5e29e/b6eba50f-8267-4e4d-8780-8b133663923c/v2.pdf
```

Desk review completed with the LLM seam mocked and received the active v2 evidence text. Because archived evidence is intentionally excluded from analysis, the smoke archived the evidence, restored it through the JSON lifecycle route for desk review, then archived it again; the final status was `archived` and both blobs remained on disk.

### Verification

- `tests/test_evidence_service.py`: **43 passed**.
- Full `.venv/bin/pytest -q`: **309 passed, 58 warnings in 26.14s**.
- Source guards: no `AssessmentDocument(` constructor or `save_upload` reference in `app/**/*.py`; no `relationship(` in `app/models/`; the only `db.delete(` in `app/services/evidence.py` deletes an `EvidenceUse` mapping.

### Current-state drift found

- The dev DB was empty rather than containing a ready real engagement, so the smoke created a dedicated smoke client, engagement, and assessment through the normal model hierarchy.
- The handoff did not mention four stale P2-1 head assertions outside its three listed Alembic edits; they contradicted the pinned `7a3f1e2b9c80` contract and were updated as described above.
- The handoff’s smoke wording places desk review after archive, but D-P2-1-A makes archived evidence invisible to analysis. The smoke therefore restored the archived evidence for the mocked desk-review check and archived it again as its final state.
- No missed live writer caller remained after the route swap; the source guard found only the `AssessmentDocument` class declaration itself, which is intentionally preserved.

## Report back

Append a `## Results` section containing:
- The final route table as implemented (method, path, success code, template or response model), flagging any deviation from step 5 and why.
- The shipped `EVIDENCE_TRANSITIONS` and `VERSION_TRANSITIONS` tables (copy them from the code, not from this document) — they must match D-P2-1-B.
- The Alembic revision as shipped, and confirmation the four existing tests were updated only in the ways step 2 lists.
- Migration decision as shipped: the script's stats from a run against a **copy** of the dev DB (migrated / text-only / skipped counts) and from the immediate second run (must be all-skipped), plus the count of `AssessmentDocument` rows before/after (must be equal).
- A count table from the live smoke test: `evidence`, `evidence_versions`, `evidence_uses`, `audit_events`, and blob files under `uploads/evidence/` before and after the smoke sequence, plus the two `shasum -a 256` outputs next to the stored hashes.
- `pytest -q` output and the pass count of `tests/test_evidence_service.py`.
- Anything this document got wrong about the current code (a drifted symbol, a caller the greps missed, a test that contradicts the spec) — name it explicitly rather than silently working around it.
