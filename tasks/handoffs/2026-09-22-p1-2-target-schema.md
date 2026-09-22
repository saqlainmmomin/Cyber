# P1-2: Create target schema

**Plan:** `docs/plans/2026-09-21-002-revised-implementation-plan.md`, Phase 1, task P1-2.
**Owner:** Claude designs → Codex implements. See `tasks/agent-ownership.md` for why (schema correctness is the foundation P1-3/P1-4/P1-5 all sit on; the column spec is already fully pinned down by the plan doc, so implementation is spec-able).
**Depends on:** P1-1 (Alembic baseline) merged — this is an Alembic revision, there is no other migration mechanism after P1-1.
**Blocks:** P1-3 (migration script needs these tables to exist), P1-4 (portfolio dashboard needs `clients`/`engagements`), P1-5 (needs `assessment_packs` for per-framework score storage).

## Goal

Add all 15 new tables from the plan's Target Schema section as SQLAlchemy models + one Alembic migration, plus `engagement_id` and `version` columns on the existing `assessments` table. No data migration in this task — that's P1-3. This task only makes the empty tables exist with correct types, FKs, and constraints.

## Current state

- 7 existing model files in `app/models/`: `assessment.py`, `desk_review.py`, `initiative.py`, `questionnaire.py`, `report.py`, `rfi.py`. All follow the same pattern — see below.
- `app/models/__init__.py` imports every model class explicitly; anything not imported there is invisible to `Base.metadata` and to Alembic's autogenerate.
- Model conventions (from `app/models/assessment.py`, `report.py`, `initiative.py` — match these exactly):
  - `id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)` where `_new_id()` returns `str(uuid.uuid4())` — imported from `app.models.assessment` (`from app.models.assessment import _new_id, _utcnow`), don't redefine it per file.
  - Timestamps: `Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)`, with `onupdate=_utcnow` on `updated_at` where both exist.
  - JSON payloads are stored as `Text` columns (e.g. `chapter_scores: Mapped[str] = mapped_column(Text)`) — there is no native JSON column type in use anywhere in this codebase; don't introduce `sqlalchemy.JSON` here, stay consistent.
  - FKs: `Mapped[str] = mapped_column(String(36), ForeignKey("parent_table.id"), index=True)`. `unique=True` is added when the plan doc says "unique" (e.g. current `gap_reports.assessment_id`).
  - Nullable fields: `Mapped[str | None] = mapped_column(Text, nullable=True)`.

## Required approach

1. Create one model file per new table under `app/models/`, matching the plan's exact column list (reproduced below — copy the field names, don't paraphrase them, since P1-3's migration script and later phases reference these names directly):

   - `app/models/client.py` — `Client`: `id`, `name` (String, **unique**), `industry`, `size`, `retention_years` (Integer, default 7), `created_at`, `updated_at`.
   - `app/models/engagement.py` — `Engagement`: `id`, `client_id` (FK → `clients.id`, **ON DELETE RESTRICT**), `name`, `type` (default `"gap_assessment"`), `status`, `created_at`, `updated_at`.
   - `app/models/assessment_pack.py` — `AssessmentPack`: `id`, `assessment_id` (FK → `assessments.id`), `framework_id`, `pack_version`, `created_at`.
   - `app/models/evidence.py` — `Evidence`: `id`, `engagement_id` (FK → `engagements.id`), `original_filename`, `storage_path`, `file_hash_sha256`, `file_size_bytes` (Integer), `mime_type`, `status`, `uploaded_by`, `created_at`.
   - `app/models/evidence.py` (same file) — `EvidenceVersion`: `id`, `evidence_id` (FK → `evidence.id`), `version_number` (Integer), `storage_path`, `file_hash_sha256`, `file_size_bytes` (Integer), `change_reason` (nullable), `created_at`.
   - `app/models/evidence.py` (same file) — `EvidenceUse`: `id`, `evidence_id` (FK → `evidence.id`), `assessment_id` (FK → `assessments.id`), `requirement_id`, `framework_id`, `relevance` (primary|supporting|contextual), `created_at`.
   - `app/models/citation.py` — `Citation`: `id`, `evidence_version_id` (FK → `evidence_versions.id`), `location_type`, `location_ref`, `excerpt` (Text), `created_at`.
   - `app/models/analysis_run.py` — `AnalysisRun`: `id`, `assessment_id` (FK → `assessments.id`), `framework_id`, `status` (running|completed|failed), `claims_json` (Text), `model_id`, `started_at`, `completed_at` (nullable).
   - `app/models/conclusion.py` — `Conclusion`: `id`, `assessment_id` (FK → `assessments.id`), `requirement_id`, `framework_id`, `cluster_id` (nullable), `outcome` (compliant|partially_compliant|non_compliant|not_applicable|insufficient_evidence), `rationale` (Text), `evidence_summary` (Text), `gaps_identified` (Text), `risk_level`, `recommended_action` (Text), `ai_proposed` (Boolean), `version` (Integer, default 1 — this is the D6 optimistic-lock column, P2-4 depends on it existing here), `created_at`, `updated_at`.
   - `app/models/conclusion.py` (same file) — `ConclusionRevision`: `id`, `conclusion_id` (FK → `conclusions.id`), `actor`, `action` (proposed|edited|approved|rejected|reopened), `previous_outcome` (nullable), `previous_rationale` (Text, nullable), `citations_json` (Text, nullable), `created_at`.
   - `app/models/finding.py` — `Finding`: `id`, `assessment_id` (FK → `assessments.id`), `conclusion_id` (FK → `conclusions.id`), `title`, `description` (Text), `severity`, `priority` (Integer), `status` (open|in_progress|resolved|accepted_risk), `created_at`, `updated_at`.
   - `app/models/action.py` — `Action`: `id`, `finding_id` (FK → `findings.id`), `title`, `owner` (nullable), `target_date` (DateTime, nullable), `status` (open|in_progress|closed|verified), `history_json` (Text), `created_at`, `updated_at`.
   - `app/models/report_snapshot.py` — `ReportSnapshot`: `id`, `assessment_id` (FK → `assessments.id`, nullable), `engagement_id` (FK → `engagements.id`, nullable), `type` (workpaper|gap_report|integrated_report), `format` (pdf|html), `storage_path`, `generated_at`, `is_issued` (Boolean, default False).
   - `app/models/magic_link.py` — `MagicLink`: `id`, `engagement_id` (FK → `engagements.id`), `token_digest` (String — SHA-256 hex, 64 chars — **never store the raw token, this column only holds the digest**), `scope_json` (Text), `max_uploads` (Integer), `max_size_bytes` (Integer), `expires_at`, `revoked_at` (nullable), `created_at`.
   - `app/models/audit_event.py` — `AuditEvent`: `id`, `actor`, `action`, `entity_type`, `entity_id`, `metadata_json` (Text, nullable), `created_at`.

2. Add to `app/models/assessment.py`'s `Assessment` class:
   - `engagement_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("engagements.id"), nullable=True, index=True)` — **nullable in this task**. The plan's own migration-safety notes (`KTD`/"Backfill script design" section) require adding it nullable first, backfilling via P1-3, then making it required for new records in a later task. Do not make it non-nullable here — that would break every existing row before P1-3 runs.
   - `version: Mapped[int] = mapped_column(Integer, default=1)` — D6 optimistic locking, same pattern as `Conclusion.version`.
   - Do NOT add a `client_id` directly to `Assessment` — the hierarchy is `Assessment.engagement_id → Engagement.client_id`, there's no shortcut FK per the target schema.

3. Register every new class in `app/models/__init__.py`'s import list and `__all__`.

4. Generate the Alembic migration: `alembic revision --autogenerate -m "P1-2: add client/engagement/evidence/conclusion hierarchy tables"`. Hand-verify: autogenerate frequently misses `ondelete` policies and check-constrained string "enum" columns (this codebase uses plain `String`, not `sqlalchemy.Enum`, for status/outcome fields — confirm the generated migration doesn't invent a DB-level CHECK constraint that isn't in the model, since none of the existing tables use them either, e.g. `questionnaire_responses.answer`'s constraint is the one deliberate exception and is already handled by the P1-1 migration).

5. `ON DELETE RESTRICT` on `engagements.client_id` — this is explicit in the plan doc and differs from the existing tables' default `NO ACTION`/no-`ondelete` pattern. Pass `ondelete="RESTRICT"` to the `ForeignKey(...)` call and confirm it appears in `PRAGMA foreign_key_list('engagements')` after migration (SQLite needs the FK declared at table-creation time — this is a new table, so no rebuild dance is needed here, unlike P1-1's retrofit onto existing tables).

## Key files

| File | Why it matters |
|---|---|
| `app/models/assessment.py` | `_new_id`/`_utcnow` helpers other new files import; `Assessment` gets `engagement_id`/`version` added here. |
| `app/models/report.py`, `initiative.py` | Closest existing examples of the JSON-as-Text, FK, and timestamp conventions to replicate exactly. |
| `app/models/__init__.py` | Must import every new class or `Base.metadata`/Alembic autogenerate won't see it. |
| `alembic/env.py` (from P1-1) | `target_metadata` source — confirm new models are picked up. |
| `tests/test_data_integrity.py` | Pattern reference for FK assertion tests (`PRAGMA foreign_key_list`) — this task's tests should follow the same style for the 15 new tables. |

## Non-goals

- Do NOT write `scripts/migrate_legacy.py` or populate any new table with data — that's P1-3.
- Do NOT make `assessments.engagement_id` non-nullable — P1-3 backfills it first.
- Do NOT touch `app/routers/`, `app/templates/`, or `app/services/` — this task is models + migration only. Routes/UI land in P1-4/P1-5.
- Do NOT implement the evidence lifecycle state machine (Quarantined→Active transitions etc.) — that's P2-1's service-layer logic; this task only creates the `status` column to hold those values.

## Test to pass

Add `tests/test_target_schema.py`:
1. `alembic upgrade head` on an empty DB creates all 15 new tables plus the 2 new `assessments` columns.
2. Every FK in the model list above appears in `PRAGMA foreign_key_list(<table>)` for its table, including `engagements.client_id` showing `RESTRICT` as the on-delete action.
3. Inserting an `Engagement` with a non-existent `client_id` raises `IntegrityError`.
4. Inserting a `Client` with a duplicate `name` raises `IntegrityError` (unique constraint).
5. `assessments.engagement_id` accepts `NULL` (existing rows / a fresh row created without one don't error).
6. `Conclusion.version` and `assessments.version` both default to `1` on insert without specifying them.
7. Round-trip: `alembic downgrade -1` removes exactly the tables/columns this migration added and nothing else; `alembic upgrade head` restores them.

## Done criteria

- All 15 new model classes exist, are imported in `app/models/__init__.py`, and match the plan doc's column list exactly (names, types, nullability, FK targets).
- `assessments` gains nullable `engagement_id` and `version` (default 1).
- `alembic upgrade head` on a fresh DB produces a schema where `sqlalchemy.inspect(engine)` matches `Base.metadata` for every new table.
- `pytest -q` passes in full, including the new `tests/test_target_schema.py`.
- No existing test in `tests/test_data_integrity.py` or elsewhere regresses (the 15 new tables must not interfere with the existing FK-retrofit migration from P1-1).

## Rollback

`alembic downgrade -1` reverts this migration cleanly since no data has been written to the new tables yet (P1-3 hasn't run). `git revert` the commit if adversarial review fails.

## Report back

Append a `## Results` section: the final list of model files added, the migration file's table-creation summary, `pytest -q` output, and `PRAGMA foreign_key_list` evidence for at least `engagements` (to confirm the `RESTRICT` policy landed) and one join table (e.g. `evidence_uses`).

## Results

### Model files added

- `app/models/action.py`
- `app/models/analysis_run.py`
- `app/models/assessment_pack.py`
- `app/models/audit_event.py`
- `app/models/citation.py`
- `app/models/client.py`
- `app/models/conclusion.py`
- `app/models/engagement.py`
- `app/models/evidence.py` (`Evidence`, `EvidenceVersion`, `EvidenceUse`)
- `app/models/finding.py`
- `app/models/magic_link.py`
- `app/models/report_snapshot.py`
- Updated `app/models/assessment.py` and `app/models/__init__.py`.

### Migration

`alembic/versions/5c7c75960f43_p1_2_add_client_engagement_evidence_.py` creates all 15 target tables and adds nullable `assessments.engagement_id` plus `assessments.version`. The migration preserves the existing legacy partial index/type behavior, adds a temporary server default of `1` so existing assessment rows can upgrade safely, and uses a named SQLite batch FK for the assessment linkage.

### Verification

- `pytest -q`: **206 passed, 30 warnings**.
- Focused target-schema contract: **22 passed**.
- Fresh upgrade, Alembic/ORM parity, round-trip, and startup smoke checks: **26 passed**.
- `alembic upgrade head` on an empty SQLite database created all 15 target tables and both assessment columns.
- `PRAGMA foreign_key_list(engagements)`:
  `[(0, 0, 'clients', 'client_id', 'id', 'NO ACTION', 'RESTRICT', 'NONE')]`
- `PRAGMA foreign_key_list(evidence_uses)`:
  `[(0, 0, 'evidence', 'evidence_id', 'id', 'NO ACTION', 'NO ACTION', 'NONE'), (1, 0, 'assessments', 'assessment_id', 'id', 'NO ACTION', 'NO ACTION', 'NONE')]`

The standalone `alembic check` also reports the pre-existing legacy-only `gap_items.ix_gap_items_null_framework_id` index, which is intentionally preserved by the P1-1 migration and documented in the existing parity test; it is unrelated to P1-2.
