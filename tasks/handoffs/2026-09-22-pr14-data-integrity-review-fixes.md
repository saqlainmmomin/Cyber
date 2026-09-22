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
