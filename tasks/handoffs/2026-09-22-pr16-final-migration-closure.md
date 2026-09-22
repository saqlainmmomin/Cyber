# PR #16 final migration-state closure

## Goal

Finish PR #16 (`codex/p1-1-alembic-baseline`) so Alembic safely replaces the
legacy startup migrations for both fresh SQLite databases and every supported
legacy upgrade state. This is the final remediation pass: fix the two
confirmed blockers below, add the complete state-transition coverage they
expose, run the full suite, and request a fresh report-only adversarial review
before merge. Do not stop at a narrow regression test for either individual
bug; the definition of done is that no supported failure/retry or
legacy-rebuild route can stamp an invalid database as Alembic head.

## Current state

The working tree already replaced live ORM metadata use during the historical
FK retrofit with revision-owned `FROZEN_TABLES`. It also added fresh Alembic
schema parity, a fresh downgrade/upgrade round trip, a later-revision collision
test, and a data-bearing downgrade refusal. `pytest -q` currently passes
(`173 passed`), but a fresh adversarial review reproduced two blockers that
the current tests miss.

### P1: orphan preflight is incomplete and retries can stamp an invalid DB

`compute_fk_tables_to_rebuild()` returns only tables whose FK definition is
missing. `preflight_fk_orphans()` scans only that returned list. Therefore an
already-constrained table can contain a non-SET-NULL orphan (for example,
`gap_reports.assessment_id`) while another table (for example, `gap_items`)
needs rebuilding. The orphan bypasses preflight; the other table rebuild
commits; `PRAGMA foreign_key_check` then raises. On retry, no table needs
rebuilding, so no integrity check runs and Alembic records head while the
original orphan remains.

This was reproduced through real `alembic command.upgrade()` calls: the first
upgrade raised after committing a `gap_items` rebuild; the second reached
`6fcd9e575309`; `PRAGMA foreign_key_check` still reported the orphan.

### P1: legacy `gap_items` rebuild loses the declared partial index

`run_column_migrations()` creates `ix_gap_items_null_framework_id` before the
FK rebuild. `_rebuild_table_for_fks()` then renames and drops the old table and
recreates only indexes declared in `FROZEN_TABLES`. The frozen `gap_items`
definition contains `ix_gap_items_report_id` but omits the partial index, so a
genuine legacy `upgrade head` finishes with only `ix_gap_items_report_id`.

This also breaks the chosen empty-adopted-database downgrade policy: baseline
`downgrade()` tries to drop the missing partial index and fails with `no such
index`, after the no-op retrofit downgrade has already moved the Alembic
version to the baseline revision.

## Required implementation

1. Make the frozen rebuild contract complete. `gap_items` must recreate
   `ix_gap_items_null_framework_id` with its exact intended definition:
   `gap_items (id)` and `WHERE framework_id IS NULL`. Do not solve this by
   making the historical retrofit read live ORM metadata or by adding a
   post-rebuild ad-hoc index that can drift separately from the frozen shape.
2. Preserve the read-only-before-write invariant. Before
   `run_column_migrations()`, inspect every existing table covered by `FK_SPEC`
   for non-SET-NULL orphans, not only tables selected for rebuilding. A
   non-SET-NULL orphan must abort before any column backfill, cleanup, table
   rename, data copy, or Alembic version update.
3. Treat every retry as an integrity boundary. Ensure the retrofit verifies
   FK integrity before it can be recorded as head even when no table needs a
   rebuild. Retain the existing policy that `desk_review_findings.document_id`
   orphans may be set to `NULL`; ensure that cleanup/verification remains safe
   for mixed legacy states too.
4. Keep the adopted-database policy: a data-bearing database must refuse to
   downgrade past the baseline without dropping tables; an empty supported
   database may downgrade to base. Fix the legacy rebuild route so it satisfies
   this contract instead of failing on a missing index.
5. Do not modify unrelated scoring, routes, templates, framework registration,
   or P1-2 target-schema work. Preserve current uncommitted user changes and
   make minimal root-cause changes only. Historical revisions and their frozen
   companion schema must remain independent of `Base.metadata`.

## Key files

| File | Responsibility |
|---|---|
| `/Users/saqlainmomin/dpdpa-gap-tool/app/legacy_migrations.py` | FK-state discovery, orphan preflight, SET-NULL cleanup, rebuild and integrity verification. |
| `/Users/saqlainmomin/dpdpa-gap-tool/app/legacy_migrations_schema.py` | Revision-owned frozen tables and indexes used by the retrofit rebuild. |
| `/Users/saqlainmomin/dpdpa-gap-tool/alembic/versions/6fcd9e575309_retrofit_legacy_columns_fks_and_.py` | Retrofit ordering; preserve preflight-before-write semantics. |
| `/Users/saqlainmomin/dpdpa-gap-tool/alembic/versions/6fc718bb9f09_baseline_schema.py` | Frozen baseline and adopted-database downgrade guard. |
| `/Users/saqlainmomin/dpdpa-gap-tool/tests/test_data_integrity.py` | Fresh/legacy migration contracts, downgrade safety, orphan scenarios. |
| `/Users/saqlainmomin/dpdpa-gap-tool/tests/test_alembic_baseline_immutable.py` | Historical immutability and later-revision collision coverage. |
| `/Users/saqlainmomin/dpdpa-gap-tool/tests/test_startup_invariants.py` | Lifespan and SQLite startup invariants. |

## Required verification matrix

All DBs must be isolated temporary SQLite URLs passed with
`Config.set_main_option("sqlalchemy.url", ...)`; never use `data/dpdpa.db`.

1. Fresh: `upgrade head`; compare complete tables, columns, FK definitions,
   index name/columns/uniqueness/predicate, and constraints with the intended
   target contract.
2. Fresh: `upgrade head -> downgrade -1 -> upgrade head`; compare the full
   schema contract before and after, not spot checks only.
3. Legacy/no FKs: `upgrade head`; assert each rebuilt table preserves rows,
   FKs, constraints, and every intended index, including the partial
   `gap_items` index predicate.
4. Legacy/no FKs plus a temporary later revision adding a `gap_items` column:
   assert the later column is added once and the retrofit did rebuild
   `gap_items`.
5. Mixed legacy state: one table has its expected FK but contains a
   non-SET-NULL orphan, while a different table requires rebuilding. Assert
   the first upgrade aborts before **any** writes/version update; a retry after
   no repair must also fail and never stamp head.
6. SET-NULL legacy orphan: preserve the existing allowed cleanup behavior and
   assert the final database passes `PRAGMA foreign_key_check`.
7. Empty adopted legacy database requiring a `gap_items` rebuild: `upgrade
   head -> downgrade base` succeeds and leaves no application tables. A
   data-bearing adopted database still refuses before any table drop and
   recovers to head cleanly.
8. Startup smoke: actual FastAPI lifespan plus `/health` against a fresh DB
   and a valid legacy-copy DB. Also assert the invalid mixed-orphan DB cannot
   start successfully or report health after the failed migration.

Run `pytest -q` with the repository Python 3.13 virtual environment after the
focused matrix passes.

## Report back

Append a `## Results` section to this file. List changed files, exact commands
and outputs, the chosen implementation shape, every verification-matrix result,
and remaining risks. Then request a fresh report-only adversarial review of the
working tree; do not merge, commit, push, or open a PR as part of this handoff.

## Results

### Changed files

| File | Change |
|---|---|
| `app/legacy_migrations_schema.py` | `FROZEN_TABLES["gap_items"]` now declares `Index("ix_gap_items_null_framework_id", "id", unique=False, sqlite_where=text("framework_id IS NULL"))`, so the legacy rebuild recreates it. |
| `app/legacy_migrations.py` | `preflight_fk_orphans(engine)` dropped the `tables_to_rebuild` param and now scans every `FK_REBUILD_ORDER` table that exists in the DB (not just tables slated for rebuild). `apply_fk_rebuild` now runs `PRAGMA foreign_key_check` unconditionally — the rebuild loop is skipped when `tables_to_rebuild` is empty, but the integrity check always runs — and gained an explicit `if engine.dialect.name != "sqlite": return` guard (previously implicit via the early `tables_to_rebuild` return) so non-sqlite dialects stay a no-op. `run_fk_retrofit` updated to match the new `preflight_fk_orphans` signature. |
| `alembic/versions/6fcd9e575309_retrofit_legacy_columns_fks_and_.py` | `upgrade()` now calls `preflight_fk_orphans(engine)` (no `tables_to_rebuild` arg); comments updated to explain the ordering guarantee. |
| `tests/test_data_integrity.py` | Enhanced `TestAlembicRoundTrip` to do a full before/after `_schema_snapshot` comparison instead of spot checks. Enhanced `test_set_null_fk_orphans_are_cleaned` with a `PRAGMA foreign_key_check` assertion. Added `TestLegacyGapItemsPartialIndexPreserved`, `TestMixedLegacyOrphanState` (+ shared `_make_fk_declared_gap_reports` helper), `TestApplyFkRebuildAlwaysVerifiesIntegrity`, `TestEmptyAdoptedLegacyDowngrade`. |
| `tests/test_startup_invariants.py` | Added `test_lifespan_and_health_against_fresh_database`, `test_lifespan_and_health_against_valid_legacy_copy_database`, `test_lifespan_fails_startup_on_invalid_mixed_orphan_database`. |
| `tests/test_alembic_baseline_immutable.py` | No new edits this pass (already covered matrix item 4 — later-revision-on-rebuilt-`gap_items` collision — from the prior session; re-verified it still passes against the fixed code). |

Note: the working tree already contained an uncommitted refactor from the
prior session (revision-owned `FROZEN_TABLES` replacing live `Base.metadata`
lookups, plus earlier test coverage) before this pass started — see the
handoff's "Current state" section. `git diff` against HEAD therefore includes
that earlier work along with this pass's changes; the table above lists only
what this pass changed.

### Implementation shape

**P1 (orphan preflight incomplete + retry gap):**
- `preflight_fk_orphans` no longer takes a table list; it iterates
  `FK_REBUILD_ORDER`, skips tables that don't exist yet, and checks every
  `FK_SPEC` entry with `on_delete != "SET NULL"` for orphans — regardless of
  whether `compute_fk_tables_to_rebuild` selected that table for a rebuild
  this run. This is the root-cause fix: an already-FK'd table's orphan is
  now caught before any write, even when a different table is the one being
  rebuilt.
- `apply_fk_rebuild` restructured so the `BEGIN`/rebuild/`COMMIT` block is
  conditional on `tables_to_rebuild`, but the final
  `PRAGMA foreign_key_check` always runs. This is defense in depth: with the
  preflight fix above, a genuine retry after fixing an orphan can no longer
  reach `apply_fk_rebuild` while any orphan remains, but the unconditional
  check also protects any future caller that skips the preflight.
- `run_fk_retrofit` (the convenience wrapper used by direct callers/tests)
  and the retrofit revision's `upgrade()` both updated to the new call
  shape; ordering is unchanged (`compute` → `preflight` → `run_column_migrations`
  → `apply`), preserving the "read-only-before-any-write" guarantee.

**P2 (gap_items partial index lost on legacy rebuild):**
- Added the missing `Index(..., sqlite_where=text("framework_id IS NULL"))`
  to `FROZEN_TABLES["gap_items"]`, mirroring the already-correct declaration
  in the frozen baseline revision (`6fc718bb9f09`). `_rebuild_table_for_fks`
  recreates every index declared on the frozen `Table` it's given, so this
  alone fixes both the lost-index bug and the downstream empty-adopted-
  database downgrade failure (baseline `downgrade()`'s `op.drop_index(...,
  'ix_gap_items_null_framework_id')` now always has something to drop).
- No change was made to the historical retrofit reading live ORM metadata,
  and no post-rebuild ad-hoc index was added — both explicitly ruled out by
  the handoff.

### Verification matrix results

All 8 items pass; new tests listed per item are in `tests/test_data_integrity.py`
unless noted.

1. **Fresh upgrade head, full contract** — `TestAlembicContractParity` (pre-existing, re-verified) diffs tables/columns/FKs/indexes against `Base.metadata.create_all()`. PASS.
2. **Fresh upgrade → downgrade -1 → upgrade head, full contract** — `TestAlembicRoundTrip.test_fresh_upgrade_downgrade_upgrade_round_trip`, now asserting `schema_after == schema_before` via `_schema_snapshot` (was spot checks only). PASS.
3. **Legacy/no-FK upgrade preserves rows, FKs, and every index incl. the partial `gap_items` predicate** — `TestLegacyUpgrade` (pre-existing) + new `TestLegacyGapItemsPartialIndexPreserved.test_partial_index_survives_legacy_rebuild`, which asserts both index presence *and* the `framework_id IS NULL` predicate string in `sqlite_master.sql`. PASS.
4. **Legacy/no-FK + later revision adding a `gap_items` column** — `tests/test_alembic_baseline_immutable.py::test_legacy_fk_rebuild_plus_later_revision_does_not_collide` (pre-existing from prior session), re-run against the fixed code: later column added exactly once, retrofit still rebuilt `gap_items`. PASS.
5. **Mixed legacy state (one table already FK'd but orphaned, a different table needs rebuild)** — new `TestMixedLegacyOrphanState`: `test_first_upgrade_aborts_before_any_write` asserts no FK/backfill write happened and `alembic_version` wasn't stamped; `test_retry_without_repair_still_fails_and_never_stamps_head` asserts a second attempt (no repair) also raises and never stamps head. PASS.
6. **SET-NULL legacy orphan cleanup + full integrity check** — `TestLegacyOrphanAbort.test_set_null_fk_orphans_are_cleaned`, now also asserting `PRAGMA foreign_key_check` returns no violations. PASS.
7. **Empty adopted legacy DB requiring `gap_items` rebuild: upgrade → downgrade base leaves no tables; data-bearing equivalent refuses then recovers** — new `TestEmptyAdoptedLegacyDowngrade`: `test_upgrade_then_downgrade_base_leaves_no_tables` and `test_data_bearing_adopted_db_refuses_then_recovers_to_head`. PASS.
8. **Startup smoke: real lifespan + `/health` for fresh and valid-legacy DBs; invalid mixed-orphan DB cannot start** — new tests in `tests/test_startup_invariants.py`: `test_lifespan_and_health_against_fresh_database`, `test_lifespan_and_health_against_valid_legacy_copy_database`, `test_lifespan_fails_startup_on_invalid_mixed_orphan_database` (asserts `TestClient(main.app)` startup itself raises `RuntimeError: FK migration blocked`, and `/health` is never reachable). PASS.

Additional targeted unit coverage: `TestApplyFkRebuildAlwaysVerifiesIntegrity.test_empty_rebuild_list_still_raises_on_existing_violation` calls `apply_fk_rebuild(engine, [], FROZEN_TABLES)` directly (bypassing the preflight) to prove the `PRAGMA foreign_key_check` layer is unconditional on its own, not only effective because the preflight now happens to catch this case first.

### Exact commands and output

```
$ .venv/bin/python -m pytest -q tests/test_data_integrity.py tests/test_alembic_baseline_immutable.py tests/test_startup_invariants.py
........................................                                 [100%]
40 passed in 2.14s

$ .venv/bin/python -m pytest -q
........................................................................ [ 39%]
........................................................................ [ 79%]
......................................                                   [100%]
182 passed, 30 warnings in 4.52s
```

(182 passed vs. the 173 reported in "Current state" — 9 net new tests: 3
startup-smoke tests, and 6 in `test_data_integrity.py`
(`TestLegacyGapItemsPartialIndexPreserved` x1,
`TestMixedLegacyOrphanState` x2, `TestApplyFkRebuildAlwaysVerifiesIntegrity`
x1, `TestEmptyAdoptedLegacyDowngrade` x2); the round-trip and SET-NULL tests
were strengthened in place rather than added as new test functions.)

The 30 warnings are pre-existing (Starlette `TemplateResponse` deprecation,
fpdf2 `ln=` deprecation, two `pytest.ReturnNotNoneWarning` in
`test_phase1_prefill.py`, one `PytestCollectionWarning` for a helper class
named `TestResults`) — unrelated to this change, not touched.

### Remaining risks

- **Non-sqlite dialects are still untested for this path.** `apply_fk_rebuild`
  and `preflight_fk_orphans` both gate on `engine.dialect.name == "sqlite"`
  and no-op otherwise, matching `compute_fk_tables_to_rebuild`'s existing
  guard — but there is no test exercising a non-sqlite engine, because the
  project is sqlite-only in practice (per `CLAUDE.md`: "No auth (single-user
  MVP)... Treat SQLite deployment as single-writer maintenance work").
  Low risk, pre-existing scope, not touched by this pass.
- **The mixed-orphan fixture is synthetic.** `_make_fk_declared_gap_reports`
  hand-builds a `gap_reports` table with its FK already declared to simulate
  "a table that already has its FK but still has an orphan." This is a
  plausible real state (e.g. FK added before enforcement was consistently
  on, or a row inserted via `PRAGMA foreign_keys=OFF`) but has not been
  observed as an actual field incident — it's a defensive fix for a category
  of bug the adversarial review identified, not a reported outage.
  Reasonable to explain in the review request.
- **`PRAGMA foreign_key_check` cost on very large legacy databases** is
  unchanged by this pass (it already ran when any table needed rebuilding);
  making it unconditional adds one extra full-database check only on the
  (previously silent) empty-rebuild-list path, which is O(rows) but no worse
  than the existing check.
- No changes were made outside `app/legacy_migrations.py`,
  `app/legacy_migrations_schema.py`, the retrofit revision, and test files,
  per the handoff's scope constraint (P1-2 target-schema work, routes,
  templates, and framework registration are untouched).

### Next step

Working tree is intentionally left uncommitted, unpushed, with no PR opened,
per this handoff's instructions. Requesting a fresh **report-only adversarial
review** of the current working tree (not a prior commit) before any merge
decision — specifically asking it to re-attempt reproducing both original P1
findings against the fixed code, and to probe the mixed-orphan and
empty-adopted-downgrade paths for any remaining gap the matrix above didn't
cover.

### Adversarial review results (report-only, this pass)

Ran a fresh multi-angle review (8 finder angles, high effort) against the
full working-tree diff (`git diff HEAD`, since HEAD == the tracked upstream
branch and all changes are uncommitted) plus the untracked
`app/legacy_migrations_schema.py`. Both original P1 findings from the
"Current state" section above were re-attempted against the fixed code and
did **not** reproduce (see the verification matrix above, items 5–7 and the
`TestApplyFkRebuildAlwaysVerifiesIntegrity`/`TestMixedLegacyOrphanState`
coverage). 7 findings survived verification, none of which contradict or
undermine the two required fixes — they're either **pre-existing** gaps this
review's wider net happened to catch, or **cleanup opportunities in the new
test code**:

1. **CONFIRMED, correctness, pre-existing** — `alembic/versions/6fc718bb9f09_baseline_schema.py:316`: baseline `downgrade()` unconditionally drops `ix_gap_items_null_framework_id`, but `upgrade()` only creates it for a *fresh* `gap_items` table, not an adopted one. Reproduced: `alembic upgrade 6fc718bb9f09` (skipping the retrofit revision) on an adopted legacy `gap_items`, then `alembic downgrade base`, raises `no such index`. Not reachable via the app (`_run_alembic_upgrade` always targets `head`) or the required matrix (always upgrades to head first); this file wasn't touched by this pass. Same bug class as P1b, one revision earlier — worth a follow-up but out of this handoff's scope.
2. **CONFIRMED, correctness, pre-existing** — `alembic/versions/6fcd9e575309_retrofit_legacy_columns_fks_and_.py:53`: `tables_to_rebuild` is computed before `run_column_migrations` and reused unchanged afterward. On a genuinely old `questionnaire_responses` (missing both the CHECK constraint and the FK), `run_column_migrations`'s own `ensure_questionnaire_answer_constraint` rebuild already adds the FK, so `apply_fk_rebuild` redundantly rebuilds the same table again. Verified directly (`compute_fk_tables_to_rebuild` returns `['questionnaire_responses']` before, `[]` after). Not data-lossy, wastes one full table copy on affected legacy installs. Pre-existing ordering, not changed by this pass.
3. **PLAUSIBLE, altitude** — `app/legacy_migrations.py:231`: the P1b fix declared the one missing index in `FROZEN_TABLES`, but the underlying pattern (ad hoc `CREATE INDEX` in `run_column_migrations`, with no enforced pairing to a `FROZEN_TABLES` declaration) is still there — a future ad hoc index on any `FK_REBUILD_ORDER` table could go missing the same way, undetected.
4. **PLAUSIBLE, altitude** — `app/legacy_migrations.py:363`: `apply_fk_rebuild`'s shape (rebuild conditional, verify unconditional, logging conditional again) could be a cleaner two-function split (`rebuild_fk_tables` / `verify_fk_integrity`) for future reuse/testability.
5. **CONFIRMED, simplification, new code** — `tests/test_data_integrity.py:1258`: the mixed-orphan DB builder is copy-pasted 3x (`TestMixedLegacyOrphanState`, `TestApplyFkRebuildAlwaysVerifiesIntegrity`, and the new startup-smoke test) instead of one shared helper.
6. **PLAUSIBLE, efficiency, new code** — `tests/test_startup_invariants.py:156`: 2 of the 3 new startup-smoke tests spin up a full `TestClient` where a direct `_alembic_upgrade` call would prove the same fact more cheaply; only the abort case needs the real lifespan.
7. **PLAUSIBLE, reuse, new code** — `tests/test_data_integrity.py:1181`: `_make_fk_declared_gap_reports` hand-writes `gap_reports` DDL instead of compiling it from `FROZEN_TABLES['gap_reports']`.

None of these were fixed in this pass — per this handoff's instructions, the
working tree stays as-is for a human merge decision. #1–#2 are candidates for
a small separate follow-up (not blocking, not introduced by this work); #3–#7
are optional polish a reviewer may want addressed before merge or left for
later.

### Third P1, found by an independent review (Codex), fixed in this pass

My own 8-angle review above missed a real bug that a separate Codex
adversarial review caught: **rebuilding a parent table corrupts an
already-FK'd child table's FK metadata.**

`_rebuild_table_for_fks` renames the table being rebuilt to
`_{table_name}_pre_fk`, recreates it under its original name, then drops the
temp table. SQLite's default `ALTER TABLE ... RENAME` behavior
(`legacy_alter_table=OFF`, the default) rewrites the FK clause of every
*other* table that references the renamed table to point at its new
(temporary) name. So when a parent needs an FK rebuild (e.g.
`assessment_documents`) but a child already has its correct FK to that
parent (e.g. `desk_review_findings.document_id`, excluded from
`tables_to_rebuild` because it's already correct), the child's FK got
silently rewritten to reference `_assessment_documents_pre_fk` — and once
that temp table was dropped, the child was left with a dangling FK the
moment the transaction committed (SQLite DDL is non-transactional, so this
wasn't rolled back).

Reproduced directly against the code from the "Results" section above
(before this fix): `alembic upgrade head` on a legacy DB with a correctly-FK'd
`desk_review_findings` and an FK-less `assessment_documents` raised
`Foreign key violations detected after migration:
[('desk_review_findings', 1, '_assessment_documents_pre_fk', 0)]`, and
`PRAGMA foreign_key_list(desk_review_findings)` showed the dangling
reference. `alembic_version` was correctly NOT stamped past the baseline (so
this class of failure can't record a false head), and a second
`alembic upgrade head` self-healed (the broken FK made
`compute_fk_tables_to_rebuild` pick `desk_review_findings` up for rebuild
too) — but the first attempt still corrupted FK metadata on disk and failed
for no legitimate reason. Same class of bug reproduced for
`gap_reports` → `gap_items`/`initiatives`.

**Fix:** `apply_fk_rebuild` now runs `PRAGMA legacy_alter_table=ON` around
the rebuild transaction (`app/legacy_migrations.py`), which disables
SQLite's cross-table FK-clause rewrite on rename — a sibling's FK clause
keeps referencing the table by its original (soon to be restored) name
throughout the rebuild, instead of being rewritten to the temp name.

**Regression coverage:** `tests/test_data_integrity.py::TestParentRebuildDoesNotCorruptSiblingFks`,
two tests (`assessment_documents`→`desk_review_findings` and
`gap_reports`→`gap_items`/`initiatives`), each asserting the sibling's FK
target and `ON DELETE` action are unchanged, `PRAGMA foreign_key_check`
passes, and the upgrade succeeds on the *first* attempt (not just after a
self-healing retry). Verified these tests fail (reproducing the exact
`_{table}_pre_fk` dangling-FK violation) with the `legacy_alter_table`
pragma removed, and pass with it restored.

**Final verification after this fix:**

```
$ .venv/bin/python -m pytest -q
184 passed, 30 warnings in 5.57s
```

(184 = the 182 from the first pass + 2 new `TestParentRebuildDoesNotCorruptSiblingFks` tests.)

This bug predates this handoff — `_rebuild_table_for_fks`'s rename/recreate/drop
mechanism is unchanged by either P1 fix above, and the working tree already
had it before this session started. It surfaced only because the required
verification matrix's fixtures didn't happen to include a sibling table that
was already correctly FK'd while its parent needed a rebuild. The working
tree is still uncommitted, unpushed, with no PR opened. This finding and fix
should be included in whatever re-review happens next before merge.
