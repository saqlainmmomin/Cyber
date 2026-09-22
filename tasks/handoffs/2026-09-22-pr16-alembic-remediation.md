# PR #16 Alembic remediation handoff

## Goal

Rework PR #16 (`codex/p1-1-alembic-baseline`) until it is safe to merge. Preserve its intended outcome: Alembic replaces the DIY startup migration path and supports both fresh SQLite databases and the defined legacy upgrade path. Done means historical migrations are immutable, the required Alembic verification is automated, the full test suite passes, and the branch receives a fresh review with no P1 findings.

## Current state

PR #16 adds Alembic, a frozen baseline revision (`6fc718bb9f09`), and retrofit revision (`6fcd9e575309`), then invokes `alembic upgrade head` from FastAPI startup. Targeted migration tests passed locally (25 tests), and a manual fresh `upgrade head -> downgrade -1 -> upgrade head` reached revision `6fcd9e575309`.

It is **not merge-safe** due to the confirmed P1 below. An independent Claude adversarial review was attempted but did not run because the local Claude OAuth token is revoked; an in-process adversarial review independently reproduced the P1 conclusion.

## Required remediation

### P1 — freeze the retrofit revision's table DDL

`6fcd9e575309` imports helpers from `app/legacy_migrations.py`. The FK rebuild helper reads the *current* ORM metadata and compiles DDL at runtime:

- `app/legacy_migrations.py:251` — `table = Base.metadata.tables[table_name]`
- `app/legacy_migrations.py:259` — `CreateTable(table).compile(...)`
- `alembic/versions/6fcd9e575309_retrofit_legacy_columns_fks_and_.py:25-30` imports those helpers.

This makes a historical migration depend on future application models. On an unversioned legacy DB that needs an FK table rebuild, a later model column could be created by revision `6fcd9e575309` before the later revision that owns it runs. That later revision can then fail with an already-existing column/table, or the old copy logic can fail if the future column is non-nullable.

Remediate by making every DDL shape used by the retrofit revision revision-owned and frozen as of this PR. It is fine to keep independently testable helpers, but they must receive a frozen schema/DDL definition from the revision rather than look up `Base.metadata` at migration runtime. Do not simply move the live-metadata lookup into the revision file.

Add a regression test that:

1. Creates a genuine legacy fixture that lacks the FK(s), so revision `6fcd9e575309` performs a rebuild.
2. Adds a temporary representative later Alembic revision that adds a column to one rebuilt table (for example `gap_items`).
3. Runs `alembic upgrade head` against that legacy fixture.
4. Proves both revisions complete and the later column is added exactly once.

The existing `tests/test_alembic_baseline_immutable.py` only tests a fresh database plus a later *new table*. It does not exercise the legacy FK-rebuild path, so it does not cover this defect.

### P1 — automate P1-1's required Alembic verification

The plan at `docs/plans/2026-09-21-002-revised-implementation-plan.md:312-317` requires a fresh DB created by Alembic to match current schema and a `downgrade -1` then `upgrade head` round trip.

Current gaps:

- `tests/test_data_integrity.py:72-75` builds the primary fresh fixture with `Base.metadata.create_all(engine)`, not Alembic.
- `tests/test_data_integrity.py:616-643` compares legacy-upgraded FKs to a `create_all()` database, which can mask baseline migration drift.
- There is no automated `upgrade head -> downgrade -1 -> upgrade head` test.

Replace or supplement these fixtures with fresh databases created by the actual Alembic command path. Add automated assertions covering tables, columns, foreign keys, and intended indexes (not only a subset of tables). Add the exact fresh round-trip test. The test must call Alembic with an isolated SQLite URL through `Config.set_main_option("sqlalchemy.url", ...)`; never touch `data/dpdpa.db`.

## Additional findings to resolve or explicitly document

### P2 — adoption downgrade is destructive

The baseline `upgrade()` deliberately skips tables that already exist to adopt an unversioned legacy database. But `downgrade()` drops every present application table (`alembic/versions/6fc718bb9f09_baseline_schema.py:253-282`). Thus `alembic downgrade base` against an adopted DB destroys its pre-existing data.

Choose a safe, explicit policy. Preferred: document that downgrading an adopted production database is unsupported and make the migration refuse rather than silently drop data, or use an explicit adoption/stamp procedure that does not imply reversibility. Do not represent Alembic downgrade as production rollback; restore a verified SQLite backup instead. Add a focused adoption/downgrade safety test for the chosen policy.

### P2 — index parity drift

`app/legacy_migrations.py:230-236` creates `ix_gap_items_null_framework_id` whenever `gap_items` exists. This happens on fresh Alembic installs too, but the index is not declared in model metadata or the frozen baseline. Decide whether it belongs in the durable target schema:

- If yes, declare it consistently in frozen migration/model schema and assert index parity.
- If legacy-only, avoid creating it on fresh installations and document the compatibility rationale.

## Key files

| File | Responsibility |
|---|---|
| `/Users/saqlainmomin/dpdpa-gap-tool/alembic/versions/6fc718bb9f09_baseline_schema.py` | Frozen baseline and adoption/downgrade policy. |
| `/Users/saqlainmomin/dpdpa-gap-tool/alembic/versions/6fcd9e575309_retrofit_legacy_columns_fks_and_.py` | Historical retrofit revision; must not derive DDL from live models. |
| `/Users/saqlainmomin/dpdpa-gap-tool/app/legacy_migrations.py` | Legacy upgrade helpers; isolate live-model dependencies from migration execution. |
| `/Users/saqlainmomin/dpdpa-gap-tool/tests/test_data_integrity.py` | Fresh/legacy upgrade and round-trip coverage. |
| `/Users/saqlainmomin/dpdpa-gap-tool/tests/test_alembic_baseline_immutable.py` | Add the legacy-rebuild plus later-revision regression. |
| `/Users/saqlainmomin/dpdpa-gap-tool/docs/plans/2026-09-21-002-revised-implementation-plan.md` | P1-1 acceptance requirements. |

## Constraints

- Do not alter scoring, routes, templates, framework registration, or P1-2 target-schema work.
- Keep the orphan preflight behavior: non-SET-NULL orphaned foreign keys must abort before writes; `desk_review_findings.document_id` orphans may be set to `NULL` as today.
- Keep the configured `settings.database_url` as the default source in `alembic/env.py`, while preserving explicit Alembic config URL overrides for isolated tests.
- Treat SQLite deployment as single-writer maintenance work. Take a verified backup and do not run a manual upgrade concurrently with app startup.
- Preserve existing user changes; make minimal, root-cause changes only.

## Verification

Run and report all of the following before claiming completion:

1. `pytest -q` using the repository's supported Python 3.13 environment.
2. Fresh isolated SQLite DB: Alembic `upgrade head`; compare tables, columns, FKs, and intended indexes to the frozen target contract.
3. Fresh isolated SQLite DB: `upgrade head -> downgrade -1 -> upgrade head`; assert revision is `6fcd9e575309` and schema is valid.
4. Legacy fixture requiring FK rebuild plus a temporary later migration adding a column; assert the historical retrofit does not pre-create/collide with that future column.
5. Legacy orphan fixture: assert no retrofit writes occur before the orphan abort.
6. Chosen adopted-database downgrade policy test.
7. Startup smoke test against fresh and legacy-copy DBs; verify `/health` after a single Alembic upgrade.

## Report back

Append a `## Results` section to this file with changed files, the exact tests/commands and outputs, the adopted downgrade policy, and any remaining risk. Request a fresh adversarial review after the P1 remediation is complete.

## Results

All remediation items were completed and verified locally (Python 3.13, repo venv). No fresh adversarial review was requested — no OAuth token is available in this environment; **request one before merging.**

### Changed files

| File | Change |
|---|---|
| `app/legacy_migrations_schema.py` (new) | Hand-written, revision-owned frozen `sqlalchemy.Table` definitions (`FROZEN_TABLES`) for every table the retrofit revision may need to rebuild for FK enforcement — a private `MetaData()`, never `Base.metadata`. Mirrors the frozen baseline's DDL, including the `questionnaire_responses` CHECK constraint. |
| `app/legacy_migrations.py` | Removed `from app.database import Base`. `_rebuild_table_for_fks` and `apply_fk_rebuild` now take a `table` / `frozen_tables` parameter instead of resolving `Base.metadata.tables[...]` themselves. `run_fk_retrofit` defaults to `app.legacy_migrations_schema.FROZEN_TABLES` (lazy import) when no frozen tables are supplied, so existing direct callers keep working. |
| `alembic/versions/6fcd9e575309_retrofit_legacy_columns_fks_and_.py` | Imports `FROZEN_TABLES` from the new schema module and passes it into `apply_fk_rebuild`. No more dependency on live ORM state. |
| `alembic/versions/6fc718bb9f09_baseline_schema.py` | (a) Declares `ix_gap_items_null_framework_id` as part of the frozen `gap_items` DDL (it was already being created unconditionally by `run_column_migrations` on every install, fresh included — this just makes that existing behavior visible in the declared contract instead of leaving it as drift) and drops it symmetrically in `downgrade()`. (b) `downgrade()` now calls `_refuse_downgrade_if_any_data()` first: raises `RuntimeError` and aborts before dropping anything if any application table still has rows (covers both a genuinely adopted legacy production DB and any DB that's actually been used) — only an **empty** database (e.g. a throwaway test fixture) can still be downgraded past this revision. |
| `tests/test_alembic_baseline_immutable.py` | Added `test_legacy_fk_rebuild_plus_later_revision_does_not_collide` (the required P1 regression: legacy fixture forcing a `gap_items` FK rebuild + a temporary later revision adding a column to `gap_items`; asserts both revisions complete, the FK rebuild actually happened, and the later column exists exactly once) and `test_retrofit_fk_rebuild_source_has_no_live_metadata_dependency` (source-text guard against `Base.metadata` creeping back into `app/legacy_migrations.py`, the retrofit revision, or the new schema module). |
| `tests/test_data_integrity.py` | `fresh_db` fixture now builds via the real `alembic upgrade head` command path (`_alembic_upgrade`, already present in this file) instead of `Base.metadata.create_all()`. Added `TestAlembicContractParity` (fresh-vs-ORM diff over tables/columns/FKs/indexes, with the one documented exception), `TestAlembicRoundTrip` (`upgrade head -> downgrade -1 -> upgrade head` on an isolated SQLite URL, asserting final revision `6fcd9e575309`), and `TestAdoptedDatabaseDowngradePolicy` (refuses with data present, still allowed when empty). |

### Verification run and output

1. **`pytest -q`** (repo venv, Python 3.13.x via `.venv`): `173 passed, 30 warnings in ~5s` (was 167 before this change; +6 new tests, 0 removed, 0 skipped).
2. **Fresh isolated SQLite DB vs. frozen target contract**: `TestAlembicContractParity::test_tables_columns_fks_indexes_match_orm_metadata` — builds one DB via `alembic upgrade head` and one via `Base.metadata.create_all()`, diffs table set, columns, FKs, and indexes per table. Passes with exactly one documented, intentional difference: `gap_items.ix_gap_items_null_framework_id` (Alembic/legacy-compat only, not represented in the ORM models). Manually re-confirmed via a throwaway script: `sorted(insp.get_table_names())` on a fresh DB = `['alembic_version', 'assessment_documents', 'assessments', 'desk_review_findings', 'desk_review_summaries', 'gap_items', 'gap_reports', 'initiatives', 'questionnaire_responses', 'rfi_documents']`; `gap_items` indexes = `['ix_gap_items_null_framework_id', 'ix_gap_items_report_id']`.
3. **Round trip**: `TestAlembicRoundTrip::test_fresh_upgrade_downgrade_upgrade_round_trip` — isolated SQLite URL via `Config.set_main_option("sqlalchemy.url", ...)`, `upgrade head -> downgrade -1 -> upgrade head`; asserts final `alembic_version.version_num == "6fcd9e575309"` and spot-checks schema validity (`gap_items.framework_id` column, `assessment_documents` FK to `assessments.id`). Passes.
4. **Legacy fixture + later revision (P1 regression)**: `test_legacy_fk_rebuild_plus_later_revision_does_not_collide` — genuine legacy fixture with no FK constraints (forces `6fcd9e575309` to rebuild `gap_items`), plus a temporary `zzzz_later_column_probe` revision (`down_revision = "6fcd9e575309"`) adding `gap_items.later_revision_marker`. Asserts: final revision is the later one, the marker column exists **exactly once**, `gap_items` does have its FK to `gap_reports` (proving the historical rebuild actually ran), and the legacy row survived both steps. Passes — this reproduces and closes the exact defect the handoff described (previously, this scenario risked the retrofit revision pre-creating or colliding with a column owned by a later revision because it read live `Base.metadata`).
5. **Orphan preflight**: pre-existing `TestLegacyOrphanAbort::test_orphan_blocks_before_any_destructive_write` still passes unmodified — confirms the FK orphan check still runs, and still aborts, before any write (no `gap_items` backfill, retrofit revision not recorded as applied).
6. **Adopted-database downgrade policy**: `TestAdoptedDatabaseDowngradePolicy::test_downgrade_refuses_when_data_present` (seeds one row, `alembic downgrade base` raises `RuntimeError` matching `"Refusing to downgrade"`, data and schema survive — Alembic may legitimately record the no-op retrofit-revision downgrade step before the baseline step raises, so the version lands on either `6fcd9e575309` or `6fc718bb9f09`, never with tables dropped; a follow-up `upgrade head` cleanly recovers to `6fcd9e575309`) and `test_downgrade_allowed_when_empty` (`alembic downgrade base` succeeds against a table-less DB, used by the round-trip style tests). Both pass. Manually re-confirmed the refusal message against a live seeded DB via a throwaway script (see below).
7. **Startup smoke test**: ad hoc script (not committed — scratch only) that runs the actual FastAPI `lifespan()` (via `TestClient`) against (a) a fresh temp SQLite file and (b) a temp file pre-seeded with the same legacy, FK-less schema/data used elsewhere in the suite. Output:
   ```
   [fresh] GET /health -> 200 {'status': 'ok'}
   [fresh] alembic_version after startup: 6fcd9e575309
   [legacy-copy] GET /health -> 200 {'status': 'ok'}
   [legacy-copy] alembic_version after startup: 6fcd9e575309
   SMOKE TEST OK
   ```
   Neither run touched `data/dpdpa.db`.

### Adopted downgrade policy (chosen)

**Refuse rather than silently drop.** `downgrade()` in the baseline revision (`6fc718bb9f09`) now checks every application table for rows before doing anything else, and raises `RuntimeError` (aborting before any `DROP TABLE`) if any table is non-empty — this covers both a genuinely adopted pre-Alembic production database (whose tables `upgrade()` deliberately left untouched) and any database that has simply been used since. Only a table-less database (fresh test fixtures, the round-trip test) can still be downgraded past this revision. The error message states that Alembic downgrade is not a production rollback path here and to restore a verified backup instead, matching CLAUDE.md's existing SQLite single-writer/backup guidance. No separate `alembic stamp`-based adoption procedure was introduced — the existing "skip tables that already exist" `upgrade()` behavior is unchanged; only `downgrade()` gained the guard.

### Index parity (chosen)

**Declared, not legacy-only.** `ix_gap_items_null_framework_id` was already being created unconditionally by `run_column_migrations` on every install (fresh databases included), just never declared anywhere as part of the target schema. Rather than changing behavior to skip it on fresh installs (a bigger, riskier change for a purely cosmetic drift issue), it's now declared directly in the frozen baseline's `gap_items` DDL (and dropped symmetrically in `downgrade()`), so the actual schema and the declared contract agree. `TestAlembicContractParity` encodes this as the one documented, intentional exception between the Alembic-built schema and the ORM's own `create_all()` schema (the index isn't represented in the SQLAlchemy models).

### Remaining risk

- **No fresh adversarial review has been run against this remediation** (no local Claude OAuth token in this environment). Request one before merging PR #16.
- The multi-step downgrade chain means `alembic downgrade base` against a non-empty adopted database still advances `alembic_version` one step (to `6fc718bb9f09`, since the retrofit revision's own `downgrade()` is a genuine no-op with nothing to protect) before the baseline step refuses. No table is ever dropped in this sequence, and `alembic upgrade head` cleanly recovers to `6fcd9e575309` afterward, but the `alembic_version` row briefly reflects an intermediate step rather than staying pinned exactly at `6fcd9e575309`. Documented in the test and this section rather than special-cased further, since it doesn't touch data.
- `app/legacy_migrations_schema.py`'s `FROZEN_TABLES` is a hand-maintained snapshot, parallel to the hand-maintained baseline revision DDL it mirrors. Any future change to a table that `FK_REBUILD_ORDER` covers (`assessment_documents`, `gap_reports`, `gap_items`, `initiatives`, `desk_review_summaries`, `desk_review_findings`, `rfi_documents`, `questionnaire_responses`) must go into a **new** revision only — never edit `6fc718bb9f09`, `6fcd9e575309`, or `app/legacy_migrations_schema.py` after this PR merges. This is the same discipline the pre-existing baseline-immutability test already enforces for the baseline revision; there is no automated guard preventing someone from editing the frozen schema module itself, beyond the source-text checks added in this PR and code review.
- The startup smoke test (Verification item 7) was run manually from a scratch script, not added as a committed test — item 7 is a one-time environment-level check (real `lifespan()` + `TestClient` + `/health`), and the repo already has `tests/test_startup_invariants.py` covering `lifespan()` invariants at the unit level.
