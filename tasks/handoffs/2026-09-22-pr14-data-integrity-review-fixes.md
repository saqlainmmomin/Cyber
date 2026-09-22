# PR #14 data-integrity review fixes

## Goal

Fix the data-integrity defects found in PR #14 (`pre-work-sprint`) so that both a new SQLite database and every supported pre-existing SQLite database enforce the intended relationships, repeated analysis/desk-review runs retain history without recursively duplicating it, and document deletion has an explicit, safe relationship policy. The work is done only when the implementation is migration-safe, idempotent, preserves valid customer data, proves fresh and upgraded schemas converge, and the full test suite passes.

## Current state

PR #14 adds SQLAlchemy `ForeignKey` declarations, enables `PRAGMA foreign_keys=ON`, adds a `legacy_history` TEXT column for destructive reruns, and adds an orphan-detector script. The full suite currently passes (148 tests), but the tests create only fresh schemas and therefore miss the following defects:

1. Existing SQLite databases are not upgraded with foreign-key constraints. `app/main.py:_run_migrations()` adds columns but never rebuilds the existing child tables, which SQLite requires to add a foreign key. A reproduction using a pre-PR `gap_reports` table followed by `_run_migrations()` produced `PRAGMA foreign_key_list(gap_reports) == []`.
2. Gap-analysis history recursively embeds the previous `legacy_history` in every snapshot. Each rerun serializes every `GapReport` column, including `legacy_history`, then appends it back into that column. This duplicates prior JSON as escaped nested data and grows rapidly over repeated runs.
3. `DeskReviewFinding.document_id` is actively populated and documented as a relationship to `AssessmentDocument`, but has no `ForeignKey` declaration and is omitted from `scripts/detect_orphans.py`. Deleting a document can leave stale evidence provenance.

## Required approach

Treat this as a schema-evolution task, not as a model-only change.

- Implement a dedicated, idempotent SQLite FK migration path for the affected tables. It must be safe for existing databases and result in the same effective schema as `Base.metadata.create_all()` on a fresh database.
- Before any destructive table replacement, run a read-only preflight for orphaned values for every relationship being enforced. Do not silently discard data. If pre-existing orphans cannot be safely remediated by the selected policy, fail clearly before changing the schema and point operators to `scripts/detect_orphans.py` (or an improved equivalent).
- Use a transaction where SQLite supports it; preserve valid rows, required indexes, uniqueness constraints, check constraints, defaults, and all application-used columns. Re-running the migration must be a no-op after convergence.
- Verify the final on-disk schema with `PRAGMA foreign_key_list(<table>)`, not only SQLAlchemy metadata.
- Decide and implement the `DeskReviewFinding.document_id` deletion policy deliberately. Preferred policy: make it `ForeignKey("assessment_documents.id", ondelete="SET NULL")`, ensure SQLite applies it, and test that deleting a document retains the finding while clearing its document reference. If a different policy is justified, document the user-visible behavior and make the delete route consistent with it.
- Build history snapshots from an explicit allowlist or a copied report payload that *excludes* `legacy_history`. The outer history list is already the record of prior runs. Preserve existing valid history exactly once; do not impose a retention limit or erase history unless that is separately requested.
- Keep the existing soft-delete assessment behavior. Do not change scoring, report contents, LLM behavior, public route contracts, or unrelated migrations.

## Key files

| File | Why it matters |
| --- | --- |
| `/Users/saqlainmomin/dpdpa-gap-tool/app/main.py` | DIY migrations and the current incomplete SQLite upgrade path. |
| `/Users/saqlainmomin/dpdpa-gap-tool/app/database.py` | Engine setup and SQLite connection-level FK enforcement. |
| `/Users/saqlainmomin/dpdpa-gap-tool/app/models/assessment.py` | `AssessmentDocument` parent model. |
| `/Users/saqlainmomin/dpdpa-gap-tool/app/models/desk_review.py` | `DeskReviewSummary`, `DeskReviewFinding`, and the missing document relationship. |
| `/Users/saqlainmomin/dpdpa-gap-tool/app/models/questionnaire.py` | Child table that already has a SQLite rebuild migration for its check constraint. |
| `/Users/saqlainmomin/dpdpa-gap-tool/app/models/report.py` | `GapReport`/`GapItem` relationships and stored history. |
| `/Users/saqlainmomin/dpdpa-gap-tool/app/models/initiative.py` | Report child relationship. |
| `/Users/saqlainmomin/dpdpa-gap-tool/app/models/rfi.py` | Assessment child relationship. |
| `/Users/saqlainmomin/dpdpa-gap-tool/app/routers/analysis.py` | Gap-analysis rerun snapshot creation. |
| `/Users/saqlainmomin/dpdpa-gap-tool/app/routers/web.py` | Desk-review rerun snapshot creation and web document deletion. |
| `/Users/saqlainmomin/dpdpa-gap-tool/app/routers/documents.py` | API document deletion route. |
| `/Users/saqlainmomin/dpdpa-gap-tool/scripts/detect_orphans.py` | Operational detection coverage. |
| `/Users/saqlainmomin/dpdpa-gap-tool/tests/test_foreign_keys.py` | Existing fresh-schema-only FK tests. |
| `/Users/saqlainmomin/dpdpa-gap-tool/tests/test_history_preservation.py` | Existing history tests; currently do not exercise production rerun logic repeatedly. |

## Constraints

- Python 3.13; use `uv run pytest` for verification.
- SQLite is the supported production database. Enable and validate FKs per connection.
- Preserve all valid data. Never use a migration that deletes orphaned rows silently.
- Existing user changes may be present in the worktree; do not revert unrelated edits.
- Keep migrations readable and narrowly scoped. Prefer a reusable, tested table-rebuild helper over eight copy-pasted rebuild implementations, but do not make a generic framework that obscures the schema contract.
- Do not use external review agents. Implement and validate locally.

## Verification

Add focused tests that prove all of the following before reporting completion:

1. Fresh schema: every intended FK exists and rejects an invalid insert; document deletion follows the chosen policy.
2. Legacy upgrade fixture: construct a representative pre-PR SQLite schema with valid data, execute the actual startup migration, assert each intended FK using `PRAGMA foreign_key_list`, confirm valid data survives, and confirm invalid future writes fail.
3. Legacy-orphan fixture: migration aborts safely and leaves the database usable/unchanged, with an actionable error or report; no implicit deletion.
4. Schema convergence: a second migration run makes no further schema/data change.
5. Analysis rerun: exercise the production code path (with the LLM mocked) at least three times and assert history contains one flat snapshot per prior run, no nested `legacy_history`, and bounded/linear serialized growth for fixed-size inputs.
6. Desk-review rerun: similarly confirm accumulated finding snapshots stay flat.
7. `python scripts/detect_orphans.py <test-db-url>` detects every implemented relationship, including `desk_review_findings.document_id` if the relationship is retained.
8. `uv run pytest -q` passes.

## Report back

Append a `## Results` section to this file. Include the migration design, tables and relationships covered, orphan policy, test commands/results, `PRAGMA foreign_key_list` evidence for both fresh and upgraded fixtures, and any residual compatibility risk. Do not claim completion without those results.

## Results

### Migration design

The FK migration uses a three-phase approach in `app/main.py:_ensure_foreign_keys()`:

1. **Detection** — For each table in `_FK_REBUILD_ORDER`, `PRAGMA foreign_key_list(table)` is compared against the expected FK spec. Tables with all FKs present are skipped (idempotent).
2. **Orphan preflight** — Before any schema change, every non-nullable FK relationship is checked for orphaned rows. If any exist, the migration raises `RuntimeError` with the count and a pointer to `scripts/detect_orphans.py`. SET NULL FKs (`desk_review_findings.document_id`) are cleaned automatically by NULLing orphaned references.
3. **Atomic rebuild** — A raw DBAPI connection with `PRAGMA foreign_keys=OFF` runs the rename → create (from SQLAlchemy model DDL via `CreateTable`) → copy → drop cycle inside a single transaction. After commit, `PRAGMA foreign_keys=ON` and `PRAGMA foreign_key_check` verify no violations. The connection pool is disposed to clear cached schema metadata.

The rebuild order (parent tables first): `assessment_documents` → `gap_reports` → `gap_items` → `initiatives` → `desk_review_summaries` → `desk_review_findings` → `rfi_documents` → `questionnaire_responses`.

### Tables and relationships covered

| Child table | FK column | Parent table | Parent column | ondelete |
|---|---|---|---|---|
| assessment_documents | assessment_id | assessments | id | NO ACTION |
| gap_reports | assessment_id | assessments | id | NO ACTION |
| gap_items | report_id | gap_reports | id | NO ACTION |
| initiatives | report_id | gap_reports | id | NO ACTION |
| desk_review_summaries | assessment_id | assessments | id | NO ACTION |
| desk_review_findings | assessment_id | assessments | id | NO ACTION |
| desk_review_findings | document_id | assessment_documents | id | SET NULL |
| rfi_documents | assessment_id | assessments | id | NO ACTION |
| questionnaire_responses | assessment_id | assessments | id | NO ACTION |

### Orphan policy

- **Non-nullable FKs**: Migration aborts before any schema change. Operator must resolve orphans via `scripts/detect_orphans.py` (which now covers all 9 relationships including `document_id`).
- **SET NULL FKs** (`desk_review_findings.document_id`): Orphaned references are automatically NULLed before rebuild. Document deletion retains findings with `document_id = NULL`.
- **No silent data deletion** — the migration never drops orphaned rows.

### History snapshot fix

- **Gap analysis** (`app/routers/analysis.py`): Snapshots now exclude `legacy_history` from the report dict (`if c.name != "legacy_history"`). The outer history list is the record of prior runs; no nesting occurs.
- **Multi-framework path**: Added history preservation (was missing entirely — existing report was deleted with no snapshot).
- **Desk review** (`app/routers/web.py`): Already flat — finding snapshots serialize `DeskReviewFinding` columns, which have no `legacy_history` field. No change needed.

### Test commands and results

```
$ uv run pytest -q
162 passed, 30 warnings in 3.92s

$ uv run python -m scripts.detect_orphans
  OK: assessment_documents.assessment_id -> assessments.id
  OK: questionnaire_responses.assessment_id -> assessments.id
  OK: desk_review_summaries.assessment_id -> assessments.id
  OK: desk_review_findings.assessment_id -> assessments.id
  OK: gap_reports.assessment_id -> assessments.id
  OK: rfi_documents.assessment_id -> assessments.id
  OK: gap_items.report_id -> gap_reports.id
  OK: initiatives.report_id -> gap_reports.id
  OK: desk_review_findings.document_id -> assessment_documents.id
  No orphans found.
```

14 new tests in `tests/test_data_integrity.py`:

| # | Verification item | Test |
|---|---|---|
| 1 | Fresh schema FKs | `TestFreshSchemaFKs::test_every_intended_fk_exists` |
| 1 | Document FK SET NULL | `TestFreshSchemaFKs::test_desk_review_finding_document_id_fk_exists` |
| 1 | FK rejects invalid insert | `TestFreshSchemaFKs::test_gap_report_rejects_invalid_assessment` |
| 1 | Document deletion policy | `TestFreshSchemaFKs::test_document_deletion_sets_finding_null` |
| 2 | Legacy upgrade + PRAGMA | `TestLegacyUpgrade::test_migration_adds_fks_and_preserves_data` |
| 2 | Post-upgrade rejection | `TestLegacyUpgrade::test_invalid_insert_fails_after_upgrade` |
| 3 | Orphan abort | `TestLegacyOrphanAbort::test_migration_aborts_on_orphaned_rows` |
| 3 | SET NULL orphan cleanup | `TestLegacyOrphanAbort::test_set_null_fk_orphans_are_cleaned` |
| 4 | Second migration no-op | `TestSchemaConvergence::test_second_migration_is_noop` |
| 4 | Fresh ≡ upgraded schema | `TestSchemaConvergence::test_fresh_schema_matches_upgraded` |
| 5 | Analysis rerun ×3 | `TestAnalysisRerunHistory::test_three_reruns_flat_history` |
| 6 | Desk review rerun ×3 | `TestDeskReviewRerunHistory::test_three_desk_reruns_flat_history` |
| 7 | detect_orphans clean | `TestDetectOrphans::test_detect_orphans_clean_db` |
| 7 | detect_orphans document_id | `TestDetectOrphans::test_detect_orphans_finds_document_orphan` |

### PRAGMA foreign_key_list evidence

**Fresh schema** (via `create_all`): All 8 child tables have their FKs, verified by `TestFreshSchemaFKs::test_every_intended_fk_exists`.

**Upgraded legacy fixture**: `TestLegacyUpgrade::test_migration_adds_fks_and_preserves_data` constructs a pre-PR schema (no FKs), inserts valid data, runs `_run_migrations` + `_ensure_foreign_keys`, then asserts every expected FK column appears in `PRAGMA foreign_key_list` output. `TestSchemaConvergence::test_fresh_schema_matches_upgraded` asserts the FK sets are identical between fresh and upgraded schemas.

### Residual compatibility risk

- **Python sqlite3 module**: The migration uses `engine.raw_connection()` and explicit `PRAGMA foreign_keys=OFF` to bypass the application-level FK enforcement during schema changes. This is the SQLite-recommended approach. The `engine.dispose()` after migration ensures the connection pool clears stale schema cache.
- **Concurrent access during migration**: The rename-create-copy-drop cycle holds a write lock. If another process writes during migration, it will block until commit. This is acceptable for a single-user SQLite deployment.
- **Existing production databases**: Any database with orphaned rows (broken parent references) will cause startup to fail with a clear error message. The dev database had 1 orphaned `questionnaire_responses` row which was cleaned as part of this work.
