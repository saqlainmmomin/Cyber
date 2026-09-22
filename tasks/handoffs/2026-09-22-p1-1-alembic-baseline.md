# P1-1: Adopt Alembic

**Plan:** `docs/plans/2026-09-21-002-revised-implementation-plan.md`, Phase 1, task P1-1.
**Owner:** Claude (drives directly — this replaces the app's only migration path on the one real database, so it is not a Codex handoff).
**Depends on:** nothing. Can start immediately, in parallel with [2026-09-22-p1-6-backup-restore.md](2026-09-22-p1-6-backup-restore.md).
**Blocks:** P1-2 (target schema migration) — every later Phase 1 task assumes Alembic is the only migration mechanism.

## Goal

Replace the DIY startup migration path in `app/main.py` with Alembic, without losing any behavior the current path provides (FK enforcement, questionnaire constraint repair) and without breaking `pytest` or a fresh `uvicorn app.main:app --reload` boot.

## Current state

- `app/main.py::lifespan()` runs, in order: `Base.metadata.create_all(bind=engine)` → `_register_frameworks()` → `_assert_framework_catalog_complete()` → `_run_migrations(engine)` → `_ensure_foreign_keys(engine)`.
- `_run_migrations()` (`app/main.py:133`) handles the questionnaire `answer` check-constraint rebuild and legacy answer-value backfill.
- `_ensure_foreign_keys()` (`app/main.py:275`) does a three-phase idempotent SQLite table-rebuild (detect → orphan preflight → atomic rebuild) to retrofit FKs onto 8 child tables. This is recent, well-tested work (`tests/test_data_integrity.py`, 14 tests) from PR #14 — see `tasks/handoffs/2026-09-22-pr14-data-integrity-review-fixes.md` for the design rationale.
- `app/database.py` defines `Base`, `engine`, `SessionLocal`, and sets `PRAGMA foreign_keys=ON` on every connection.
- `app/models/__init__.py` imports all 7 current model classes so `Base.metadata` sees them before `create_all`.
- `requirements.txt` has no `alembic` dependency yet.
- No `alembic/` directory or `alembic.ini` exists.

## Required approach

1. Add `alembic==1.13.*` (pin an exact compatible version) to `requirements.txt`.
2. Run `alembic init alembic` at the repo root, then configure `alembic/env.py` to:
   - Import `app.database.Base` and `app.models` (for `target_metadata`).
   - Read `sqlalchemy.url` from `app.config.settings.database_url`, not a hardcoded value in `alembic.ini` — `alembic.ini`'s `sqlalchemy.url` line should stay a placeholder/commented, with `env.py` overriding it from `settings` so dev/test DBs resolve correctly.
   - Support `render_as_batch=True` for SQLite (required for any future `ALTER` operations in Alembic-generated migrations, since SQLite can't do most in-place `ALTER TABLE`).
3. Generate the baseline migration with `alembic revision --autogenerate -m "baseline: current schema as of PR #14"` against a DB created via the *existing* `Base.metadata.create_all()` path (i.e., autogenerate should produce an empty or near-empty diff, since the models already match the real schema). Hand-verify the generated migration file — autogenerate can miss SQLite-specific constructs (check constraints, some index forms); add anything missing by hand.
4. Fold `_ensure_foreign_keys()`'s FK-retrofit logic and `_run_migrations()`'s questionnaire-constraint repair into this same baseline migration (or a second migration immediately after it) so that running `alembic upgrade head` against a **pre-PR-14 legacy database** produces an identical end state to what `_run_migrations()` + `_ensure_foreign_keys()` currently produce. Do not weaken the orphan-preflight safety behavior (migration must still abort loudly on orphaned rows rather than silently dropping them) — port that check into the Alembic migration's `upgrade()` function.
5. Delete `_run_migrations()`, `_ensure_questionnaire_answer_constraint()`, `_ensure_foreign_keys()`, and `_rebuild_table_for_fks()` from `app/main.py` once their behavior is fully represented in Alembic migrations.
6. Update `lifespan()` in `app/main.py`:
   - Remove `Base.metadata.create_all(bind=engine)`, `_run_migrations(engine)`, `_ensure_foreign_keys(engine)`.
   - Replace with a call that runs `alembic upgrade head` programmatically (via `alembic.config.Config` + `alembic.command.upgrade`, not a subprocess) before `_register_frameworks()`.
   - Keep `_register_frameworks()` and `_assert_framework_catalog_complete()` as-is — they are framework-registry checks, not schema migrations, and are out of scope.
7. Confirm `alembic upgrade head` works from a clean checkout with `data/` absent (creates DB + all tables) and from the current dev `data/dpdpa.db` (upgrades in place).

## Key files

| File | Why it matters |
|---|---|
| `app/main.py` | Where `lifespan()`, `_run_migrations`, `_ensure_foreign_keys` currently live — most of this gets deleted or replaced. |
| `app/database.py` | `Base`, `engine`, `SessionLocal` — `env.py` needs these. |
| `app/models/__init__.py` | Import list `env.py`'s `target_metadata` depends on. |
| `app/config.py` | `settings.database_url` — the single source of truth for the DB URL, must not be duplicated in `alembic.ini`. |
| `requirements.txt` | Add `alembic`. |
| `tests/test_data_integrity.py` | 14 existing tests exercise the exact upgrade paths this task must preserve (legacy-upgrade, orphan-abort, convergence, `PRAGMA foreign_key_list` checks). These are the regression baseline — do not weaken or delete them; adapt their setup (they currently call `_run_migrations`/`_ensure_foreign_keys` directly) to call `alembic upgrade head` instead, keeping the same assertions. |
| `tests/conftest.py` | Test DB fixture setup — likely needs to run `alembic upgrade head` instead of `create_all` for consistency with production. |

## Non-goals

- Do NOT write the P1-2 migration (new tables: clients, engagements, evidence, etc.) in this task — that's a separate, subsequent Alembic revision.
- Do NOT change FK `ondelete` policies, the questionnaire answer constraint values, or any other behavioral decision already made in PR #14 — this is a mechanism swap (DIY → Alembic), not a redesign.
- Do NOT touch `scripts/detect_orphans.py`, scoring, routes, or templates.

## Test to pass

Adapt (don't discard) `tests/test_data_integrity.py`'s scenarios to run through `alembic upgrade head`:
1. Fresh DB via `alembic upgrade head` has every FK `PRAGMA foreign_key_list` currently asserts.
2. A constructed pre-PR-14 legacy fixture, migrated via `alembic upgrade head`, ends with the same FK set and preserves valid data (byte-for-byte same assertions as today's `TestLegacyUpgrade`).
3. A legacy fixture with orphaned rows aborts the migration with a clear error and leaves the DB unchanged (`TestLegacyOrphanAbort`).
4. Running `alembic upgrade head` twice is a no-op (`TestSchemaConvergence`) — this is Alembic's native behavior (it tracks the current revision) but verify the FK-retrofit logic inside the migration is also idempotent if `alembic upgrade head` is somehow invoked against a partially-upgraded state.
5. `alembic downgrade -1` followed by `alembic upgrade head` round-trips cleanly on an empty/fresh DB (does not need to preserve data through a downgrade — SQLite table-rebuild downgrades are allowed to be lossy-safe, i.e., they may just drop what was added, as long as they don't error).

## Done criteria

- `alembic upgrade head` on a fresh checkout (no `data/` dir) creates the full current schema, verified by comparing `sqlalchemy.inspect(engine)` table/column/FK output against `Base.metadata` — they must match.
- `alembic upgrade head` on the current dev `data/dpdpa.db` (or an equivalent legacy fixture) succeeds and produces the same `PRAGMA foreign_key_list` output as today's `_ensure_foreign_keys()`.
- `uvicorn app.main:app --reload` boots cleanly against both a fresh and an existing DB.
- `pytest -q` passes in full (163+ tests, no regressions).
- `_run_migrations`, `_ensure_questionnaire_answer_constraint`, `_ensure_foreign_keys`, `_rebuild_table_for_fks` are deleted from `app/main.py` — `git grep` for their names returns nothing outside `tasks/handoffs/` history docs.

## Rollback

`git revert` the merge commit. Because this task deletes the DIY migration functions, a partial rollback (keep Alembic, restore DIY functions) is not meaningful — treat this as an atomic all-or-nothing change and revert the whole PR if it fails adversarial review.

## Report back

Append a `## Results` section to this file: the final `alembic/` directory layout, the exact baseline migration content (or a diff summary if long), `pytest -q` output, and `PRAGMA foreign_key_list` evidence for both fresh and upgraded fixtures — same evidence shape as `tasks/handoffs/2026-09-22-pr14-data-integrity-review-fixes.md`'s Results section.

## Results

### Design deviation from the plan above

The ORM models (`app/models/*.py`) already declare every FK and the questionnaire check constraint (confirmed before writing any code: `git grep ForeignKey|CheckConstraint app/models`). So `Base.metadata.create_all()` already produces a fully correct fresh schema — `_run_migrations`/`_ensure_foreign_keys` only ever did real work against a genuinely pre-PR-14 database. This shaped the two-revision design below, and it's why autogenerate (run once as a sanity check) produced an **empty diff** against a `create_all()`'d DB.

The retrofit logic (formerly `_run_migrations`, `_ensure_questionnaire_answer_constraint`, `_ensure_foreign_keys`, `_rebuild_table_for_fks`) was moved into a new plain module, `app/legacy_migrations.py`, rather than inlined in the Alembic revision file. Three existing test files (`tests/test_needs_review_ui.py`, `tests/test_questionnaire_rebuild.py`, `tests/test_startup_invariants.py`, not listed in the original handoff's file table) unit-test these functions directly against isolated in-memory/partial-schema engines — that only works if the logic is a normal importable module, not something buried in `alembic/versions/`. The Alembic revision now just calls into it.

### Final `alembic/` layout

```
alembic.ini                                  # sqlalchemy.url left commented; env.py overrides from settings
alembic/
  env.py                                     # target_metadata = Base.metadata, render_as_batch for sqlite,
                                              # disable_existing_loggers=False (see bug #2 below)
  script.py.mako
  README
  versions/
    6fc718bb9f09_baseline_schema.py          # Revision 1: Base.metadata.create_all(bind=op.get_bind())
    6fcd9e575309_retrofit_legacy_columns_fks_and_.py   # Revision 2: calls app.legacy_migrations
app/legacy_migrations.py                     # ported retrofit logic, importable + unit-testable
```

Revision 1 (`upgrade`): `Base.metadata.create_all(bind=op.get_bind())` — not hand-copied autogenerate DDL, so it can never drift from the models. `checkfirst=True` (the default) makes it a no-op against a DB that already has these tables, which is what lets Revision 2 run against genuinely legacy data.

Revision 2 (`upgrade`): `run_column_migrations(engine)` then `run_fk_retrofit(engine)` from `app.legacy_migrations` — same column-add logic, same questionnaire check-constraint rebuild, same `_FK_SPEC`/orphan-preflight/`_rebuild_table_for_fks` table-rebuild dance as the deleted `app/main.py` functions, byte-for-byte. Both `downgrade()`s are lossy-safe no-ops per the plan (Revision 1's downgrade drops all tables; Revision 2 adds nothing that needs undoing separately).

### Two bugs found and fixed during verification (both would have shipped silently broken)

1. **`env.py` unconditionally overwrote `sqlalchemy.url` from `settings.database_url`**, clobbering any URL a caller (e.g. a test) had already set on the `Config` object before invoking a command. Fixed: only default from settings `if not config.get_main_option("sqlalchemy.url")`.
2. **Dropped `engine.dispose()`** when porting `_ensure_foreign_keys` → `run_fk_retrofit` — the original relies on it to invalidate any pooled connection that predates the raw table-rebuild (SQLite serves stale reads from an old pooled connection object otherwise). Restored it in the `finally` block. Separately, `alembic/env.py`'s `fileConfig()` call defaults to `disable_existing_loggers=True`, which silently killed the app's own loggers (e.g. `app.config`) partway through the test run the first time Alembic ran — fixed with `disable_existing_loggers=False`.

### `pytest -q` output

```
167 passed, 30 warnings in 3.86s
```

167 passed both before and after this change (same count) — no tests lost, no regressions. All of `test_data_integrity.py`'s legacy-upgrade/orphan-abort/convergence/drift tests now run through `alembic upgrade head` (via a `_alembic_upgrade(engine)` test helper) instead of calling the deleted functions directly.

### `PRAGMA foreign_key_list` evidence

Fresh DB (`alembic upgrade head` against an empty file) — identical FK set to a copy of the real dev `data/dpdpa.db` upgraded the same way:

```
assessment_documents:     [(0,0,'assessments','assessment_id','id','NO ACTION','NO ACTION','NONE')]
gap_reports:               [(0,0,'assessments','assessment_id','id','NO ACTION','NO ACTION','NONE')]
gap_items:                 [(0,0,'gap_reports','report_id','id','NO ACTION','NO ACTION','NONE')]
initiatives:                [(0,0,'gap_reports','report_id','id','NO ACTION','NO ACTION','NONE')]
desk_review_summaries:     [(0,0,'assessments','assessment_id','id','NO ACTION','NO ACTION','NONE')]
desk_review_findings:      [(0,0,'assessment_documents','document_id','id','NO ACTION','SET NULL','NONE'),
                             (1,0,'assessments','assessment_id','id','NO ACTION','NO ACTION','NONE')]
rfi_documents:              [(0,0,'assessments','assessment_id','id','NO ACTION','NO ACTION','NONE')]
questionnaire_responses:   [(0,0,'assessments','assessment_id','id','NO ACTION','NO ACTION','NONE')]
```

Also verified: `sqlalchemy.inspect(engine)` table/column output on the fresh DB matches `Base.metadata` exactly (same tables, same columns per table). The real dev `data/dpdpa.db` was never touched directly — all upgrade tests ran against scratch copies; the live file only had FKs read from it once (baseline snapshot) for comparison.

### Boot smoke test

`uvicorn app.main:app` (via `.venv`, Python 3.13) booted cleanly and returned `{"status":"ok"}` from `/health` against both a fresh DB and a copy of the real dev DB, in both cases logging:
```
INFO  [alembic.runtime.migration] Running upgrade  -> 6fc718bb9f09, baseline schema: current schema as of PR #14
INFO  [alembic.runtime.migration] Running upgrade 6fc718bb9f09 -> 6fcd9e575309, retrofit legacy columns, questionnaire answer constraint, and foreign keys
```

### Done criteria check

- `git grep` for `_run_migrations`, `_ensure_foreign_keys`, `_ensure_questionnaire_answer_constraint`, `_rebuild_table_for_fks` outside `tasks/handoffs/`: only historical mentions in `docs/plans/`, `docs/sessions/`, `tasks/2026-09-21-adversarial-review.md`, and one explanatory code comment in `tests/test_data_integrity.py` referencing the old function name — no live references. ✅
- All other done criteria (fresh boot, legacy boot matching FK output, `pytest -q` full pass) confirmed above. ✅
