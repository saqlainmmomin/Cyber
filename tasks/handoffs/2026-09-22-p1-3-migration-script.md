# P1-3: One-shot migration script

**Plan:** `docs/plans/2026-09-21-002-revised-implementation-plan.md`, Phase 1, task P1-3, plus the "Migration Safety → Backfill script design" section.
**Owner:** Claude designs + writes the failing tests first → Codex implements against them. See `tasks/agent-ownership.md` — the mapping decisions here (outcome mapping, one-Engagement-per-Assessment conservatism) are judgment calls with data-integrity consequences; the test scenarios are enumerated below so implementation itself is spec-able.
**Depends on:** P1-2 (target schema) merged — every table this script writes to must exist first.
**Blocks:** P1-4 (portfolio dashboard needs real `Client`/`Engagement` rows to render), and the later step (not in this task) of making `assessments.engagement_id` non-nullable.

## Goal

`scripts/migrate_legacy.py` — an idempotent script that, run against any current-schema SQLite DB (empty, or with legacy `Assessment`/`GapItem`/`GapReport` rows), creates the `Client`/`Engagement` hierarchy and migrates `GapItem` → `Conclusion`/`Finding`/`Action` without losing or duplicating data. Per the plan: **the current database is empty (no production users)** — this script's main job is correctness and idempotency, not handling a large messy legacy dataset. Test it against constructed fixtures that exercise the real shapes, not just the empty case.

## Current state

- `Assessment` rows have `company_name`, `industry`, `company_size`, `selected_frameworks` (JSON list, e.g. `["dpdpa", "iso27001"]` — see `Assessment.frameworks` property in `app/models/assessment.py`), and now (from P1-2) a nullable `engagement_id`.
- `GapReport` (one per Assessment, unique FK) has `overall_score`, `framework_scores` (JSON: `{framework_id: {...}}` — see `compute_framework_scores()` / `compute_unified_maturity()` in `app/services/scoring.py`), `legacy_history` (from PW-2, a JSON array of prior-run snapshots — must be preserved as-is, not touched by this migration).
- `GapItem` (many per `GapReport`) has: `compliance_status` (one of `compliant`, `partially_compliant`, `non_compliant`, `not_assessed`, `not_applicable` — see `app/services/scoring.py:18-24`), `framework_id`, `cluster_id`, `requirement_id`, plus AI fields (`ai_compliance_status`, `ai_gap_description`, `ai_risk_level`), consultant review fields (`review_status`, `reviewed_by`, `reviewed_at`, `reviewer_notes`), and remediation fields (`remediation_status`, `remediation_owner`, `remediation_target_date`, `remediation_notes`, `remediation_closed_at`, `remediation_priority`, `remediation_effort`, `timeline_weeks`).
- `Initiative` groups multiple `GapItem`s by root cause — out of scope for this migration (no target-schema equivalent named in the plan; leave `initiatives` as a retired/preserved-for-reference table, don't migrate it into `Finding`/`Action`).
- Target tables from P1-2: `clients`, `engagements`, `assessment_packs`, `conclusions`, `conclusion_revisions`, `findings`, `actions` are what this script populates. It does NOT touch `evidence`, `evidence_versions`, `citations`, `magic_links` — those are empty until Phase 2.

## Required approach

Follow the plan's "Backfill script design" section exactly:

1. **Idempotent.** Before creating a `Client`, check if one already exists with that exact `company_name` (case-sensitive exact match — no fuzzy matching). Before creating an `Engagement` for an `Assessment`, check `assessment.engagement_id is not None` and skip if already set. Running the script twice on the same DB must produce zero additional rows the second time.

2. **Conservative Client creation.** One `Client` per distinct `company_name` string. **One `Engagement` per `Assessment`, always** — even if two Assessments share the same `company_name`, do NOT assume they belong to the same Engagement. This is explicit in the plan: "Same-name assessments are NOT assumed to share one Engagement (one Engagement per Assessment for safety)." Set `Engagement.name` to something derivable and stable, e.g. the Assessment's `description` if present, else a synthesized name like `f"Imported: {assessment.company_name} ({assessment.created_at.date()})"`. Set `Engagement.type = "gap_assessment"`.

3. **Freeze `company_name`.** After migration, `Assessment.company_name` is never updated again by application code — this script only reads it to derive the `Client`. Write a test asserting `assessment.engagement.client.name == assessment.company_name` for every migrated row, and note in the script's docstring that this equality is a migration-time invariant, not an ongoing constraint (a consultant could rename a `Client` later without `Assessment.company_name` following it — that's expected).

4. **AssessmentPack creation.** For each `Assessment`, for each framework id in `assessment.frameworks` (the property, not the raw `selected_frameworks` string), create one `AssessmentPack` row (`framework_id`, `pack_version` — use a placeholder like `"unknown"` if no version metadata exists yet at this point in the plan; P1's pack-version-metadata work landed in the superseded `001` plan's U1, not in `002` — check `app/frameworks/registry.py` for whether a version field already exists on `FrameworkDefinition` before inventing one; if it doesn't, `"unknown"` is correct and expected here).

5. **GapItem → Conclusion mapping:**
   - `outcome = compliance_status`, with `not_assessed → insufficient_evidence` and **log a warning per row** (`logger.warning(...)`, include `assessment_id` and `requirement_id`) so these are flagged for manual review, per the plan's explicit instruction. All other statuses map 1:1 (`compliant→compliant`, `partially_compliant→partially_compliant`, `non_compliant→non_compliant`, `not_applicable→not_applicable`).
   - `Conclusion.assessment_id`, `requirement_id`, `framework_id`, `cluster_id`, `risk_level` copy directly.
   - `rationale` ← `gap_description`, `evidence_summary` ← `evidence_quote` (nullable — carry `None` through if absent), `gaps_identified` ← `gap_description` (yes, same source as `rationale`; the plan doesn't distinguish these two target fields from any distinct GapItem source — do not fabricate a second field), `recommended_action` ← `remediation_action`.
   - `ai_proposed = True` always (every migrated GapItem originated from an AI-produced analysis run in the old flow).
   - `version = 1`.
   - Create exactly one `ConclusionRevision` with `action="proposed"`, `actor="system:migration"`, `citations_json=None` (no structured citations exist pre-Phase-2 — do not synthesize any from `evidence_quote`, that's P2-2's job on new data, not a backfill concern).
   - **If `reviewed_at` is set** on the GapItem, create a **second** `ConclusionRevision` with `action="approved"`, `actor=item.reviewed_by or "unknown"`, `created_at=item.reviewed_at`, capturing `previous_outcome`/`previous_rationale` as the pre-review AI values (`ai_compliance_status`/`ai_gap_description` if present, else the same as the proposed values).

6. **Remediation fields → Finding + Action.** Only create a `Finding`+`Action` pair when the GapItem has non-default remediation state — use `remediation_status is not None` as the trigger (the column defaults to `"open"` on new rows per `app/models/report.py`, so `None` genuinely means "never touched," not "open with no action taken"; treat an explicit `"open"` value the same as any other status — it's still a real Finding).
   - `Finding.assessment_id` = the GapItem's Assessment (via `report.assessment_id`), `conclusion_id` = the just-created `Conclusion`'s id, `title` = derived from `requirement_title` on the parent... **`requirement_title` lives on `GapItem` directly** (confirm via `app/models/report.py`), `description` ← `gap_description`, `severity` ← `risk_level`, `priority` ← `remediation_priority`, `status`: map `remediation_status` (`open`→`open`, anything else pass through if it matches the target enum, else default to `"open"` and log a warning).
   - `Action.finding_id` = the just-created Finding, `title` ← `remediation_action`, `owner` ← `remediation_owner`, `target_date` ← `remediation_target_date`, `status`: derive from `remediation_closed_at` (`is not None` → `"closed"`, else map from `remediation_status` the same way as Finding.status, but Action's enum is `open|in_progress|closed|verified` — there is no `in_progress` source field, so only `open`/`closed` are ever produced by migration; `in_progress`/`verified` only arise from post-migration application use).
   - `Action.history_json` = a JSON array with one entry: `{"actor": "system:migration", "action": "imported", "timestamp": <assessment's or item's most recent relevant timestamp, ISO8601>, "notes": "Migrated from legacy GapItem remediation fields"}`.

7. **`GapReport.framework_scores` → per-`AssessmentPack` score storage.** The plan's target schema doesn't define a scores table on `AssessmentPack` itself (re-read P1-2's `AssessmentPack` column list — it doesn't have a score column). Flag this ambiguity rather than guessing: **do not silently drop the score data**. For this task, copy `GapReport.framework_scores` verbatim into a new `Conclusion`-adjacent location is out of scope (no such column exists) — instead, leave `GapReport`/`GapItem` tables **untouched and preserved** (per the plan's table-retirement note: "Retired after migration verification: 3 tables... data migrated to conclusions/findings/actions" — retired means kept-but-unused, not deleted) and have P1-5 (deprecate blended scoring) read historical per-framework scores from the still-present `GapReport.framework_scores` column until a later phase adds proper per-pack score storage. State this explicitly in the script's docstring and in the `## Results` section so it isn't silently forgotten.

8. **`legacy_history` preserved as-is** — do not read, transform, or migrate it. It stays on `GapReport` for audit reference only.

9. **Backup is mandatory before running.** The script's `__main__` entry point must call (or shell out to) `scripts/backup.py` (from P1-6 — confirm it exists and its function signature before wiring this in) before making any write, and abort if the backup step fails. Accept a `--skip-backup` flag only for use inside the test suite (never document it as a normal flag in the script's `--help`).

10. **`scripts/rollback_legacy.py`** — a thin script that calls `scripts/restore.py` (from P1-6) pointed at the backup directory `migrate_legacy.py` just created. Print the backup path from `migrate_legacy.py`'s run so a human can pass it to `rollback_legacy.py` if needed.

## Key files

| File | Why it matters |
|---|---|
| `app/models/assessment.py` | `Assessment.frameworks` property — use this, not raw `selected_frameworks` JSON parsing, to get the framework id list. |
| `app/models/report.py` | Exact `GapItem`/`GapReport` column names and defaults for every field referenced above. |
| `app/services/scoring.py:16-24` | Canonical `compliance_status` value set — confirms there are exactly 5 values, no others to handle. |
| `app/models/client.py`, `engagement.py`, `assessment_pack.py`, `conclusion.py`, `finding.py`, `action.py` (from P1-2) | Target model definitions this script writes into. |
| `scripts/backup.py`, `scripts/restore.py` (from P1-6) | Mandatory pre-migration backup and the rollback path. |
| `scripts/seed_test_companies.py` | Existing pattern for constructing multi-assessment test fixtures — useful reference for building this task's test fixtures (single-framework, multi-framework, empty-DB cases the plan's Test scenarios ask for). |

## Non-goals

- Do NOT make `assessments.engagement_id` non-nullable — that's a follow-up task after this script has run successfully against the real DB, not part of this task.
- Do NOT migrate `Initiative` rows — no target-schema equivalent exists in this plan.
- Do NOT delete `GapReport`/`GapItem`/`Initiative` rows or tables — they stay, per the plan's "retired" (not deleted) language.
- Do NOT invent a score-storage column on `AssessmentPack` to solve the framework_scores gap (item 7 above) — flag it, don't silently extend P1-2's already-merged schema.
- Do NOT touch `evidence`/`citations`/`magic_links` tables — empty until Phase 2.

## Test to pass

Per the plan's exact scenario list, seed a DB with 3 assessments (single-framework, multi-framework, empty/no-GapReport) and assert after running `migrate_legacy.py`:
1. `assessment.engagement.client.name == assessment.company_name` for all rows.
2. `Conclusion` count == `GapItem` count for migrated assessments.
3. No orphaned rows in any table (reuse the `scripts/detect_orphans.py` pattern, extended to cover the new FK relationships, or add equivalent assertions inline).
4. Round-trip: scores match pre-migration values — i.e., `GapReport.framework_scores` for each assessment is byte-identical before and after migration (this task doesn't move scores anywhere, per item 7, so this should be true almost trivially — the test still matters as a regression guard against an implementation that touches `GapReport` by mistake).
5. Running the script a second time against the already-migrated DB creates zero new `Client`/`Engagement`/`Conclusion`/`Finding`/`Action` rows.
6. A `not_assessed` GapItem produces a `Conclusion` with `outcome="insufficient_evidence"` and a logged warning (assert via `caplog` or equivalent).
7. A GapItem with `reviewed_at` set produces two `ConclusionRevision` rows (`proposed` then `approved`); one without `reviewed_at` produces exactly one.
8. A GapItem with `remediation_status is None` produces no `Finding`/`Action`; one with `remediation_status` set (any value) produces exactly one `Finding` and one `Action`.
9. The empty-DB case (no assessments) runs without error and creates zero rows.
10. Script refuses to run (non-zero exit, no writes) if the mandatory backup step fails, verified with a mocked/broken backup call.

## Done criteria

- `python scripts/migrate_legacy.py` runs cleanly against the 3-assessment fixture and against an empty DB.
- All 10 test scenarios above pass in `tests/test_migrate_legacy.py`.
- `scripts/rollback_legacy.py` exists and successfully restores a pre-migration state when pointed at the backup `migrate_legacy.py` produced.
- `pytest -q` passes in full, no regressions.
- The framework_scores gap (item 7) is documented in the script's module docstring and in this file's `## Results` section, not silently resolved by inventing schema.

## Rollback

`scripts/rollback_legacy.py` (built as part of this task) restores from the mandatory pre-run backup. For the code itself (not the data it migrates), `git revert` the commit if adversarial review fails.

## Report back

Append a `## Results` section: the exact mapping table implemented (compliance_status → outcome), counts from a real run against the current dev DB (or the 3-assessment fixture if the dev DB is empty), `pytest -q` output, and explicit confirmation of how the framework_scores gap (item 7) was left for a later phase to resolve.

## Results (2026-09-22)

**Status:** Implemented and merged (PR #19).

**Process:** Claude wrote `tests/test_migrate_legacy.py` (26 scenarios) plus `NotImplementedError` interface stubs for `scripts/migrate_legacy.py`/`scripts/rollback_legacy.py`, verified a clean TDD red state (25 failed/1 passed, no collection errors), then handed off to Codex to implement.

**Mapping table implemented** (`compliance_status` → `Conclusion.outcome`, in `OUTCOME_MAP`):
| compliance_status | outcome |
|---|---|
| compliant | compliant |
| partially_compliant | partially_compliant |
| non_compliant | non_compliant |
| not_applicable | not_applicable |
| not_assessed | insufficient_evidence (+ `logger.warning` with assessment_id/requirement_id) |

**Open decisions (D-A..D-D), resolved as documented in `scripts/migrate_legacy.py`'s module docstring:**
- D-A: `GapReport.framework_scores` stays authoritative; no score column added to `AssessmentPack` — deferred to a later phase.
- D-B: `Conclusion.evidence_summary` coerces a `None` `evidence_quote` to `""`.
- D-C: `Engagement.status="active"`; `Client.industry`/`size` copied from the first-seen assessment (by `created_at`) for a given `company_name`.
- D-D: `Finding.status` falls back to `"open"` + warning for unrecognized values; `Action.status` is `closed` when `remediation_closed_at is not None`, else `open` (migration never produces `in_progress`/`verified`).

**Adversarial review finding (real bug, fixed before merge):** an undocumented heuristic in the first implementation pass silently treated a genuinely-open, not-yet-triaged `GapItem` (`remediation_status="open"` with no owner/date/notes/closed_at) as untouched (`None`), skipping `Finding`/`Action` creation with no warning — contradicting this doc's explicit instruction (item 6) that an explicit `"open"` value is still a real Finding. Root cause: `GapItem.remediation_status`'s Python-side `default="open"` fires even when `None` is passed explicitly to the ORM constructor, so the original test fixture could never seed a genuine `NULL`. Fixed by seeding `GapItem` rows via a SQLAlchemy Core `insert()` (bypasses the default) instead of the ORM constructor, adding a regression test for the bare-`"open"` case, and removing the heuristic from `run_migration`.

**Test results:** `tests/test_migrate_legacy.py`: 27 passed (26 original scenarios + 1 regression test for the finding above). Full suite: 240 passed, no regressions.

**Real-run counts:** not yet run against the dev DB (currently empty, no legacy rows to migrate per-plan assumption); verified instead against the 3-assessment fixture (single-framework, multi-framework, empty/no-GapReport) as the test scenarios specify.
