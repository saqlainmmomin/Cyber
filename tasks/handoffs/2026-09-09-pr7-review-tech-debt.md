# PR #7 Review Tech Debt — Codex Rework

**Date:** 2026-09-09
**Context:** Adversarial review of PR #7 (`codex/ws1-ws2-ws3`) surfaced 9 findings. Findings 1–4 were fixed in-session. This handoff covers the remaining 5 items for Codex to address and push as an update to the same PR.

**Branch:** `codex/ws1-ws2-ws3`
**PR:** #7

---

## Tasks

### 1. Add startup assertion for framework registry ↔ UI tuple drift

**File:** `app/routers/web.py` (near lines 31–32) or `app/main.py` (in lifespan)

`ENABLED_ASSESSMENT_FRAMEWORKS` and `ROADMAP_FRAMEWORKS` are manually maintained tuples. If a framework is added to `FrameworkRegistry` but not to these tuples, it silently disappears from the UI.

**Action:** Add an assertion during app startup that:
```
set(ENABLED_ASSESSMENT_FRAMEWORKS) | set(ROADMAP_FRAMEWORKS) == set(FrameworkRegistry.all_ids())
```
Place it in the lifespan function in `app/main.py` after `_register_frameworks()` is called, or at module level in `web.py` after the registry is populated. Fail loud at boot, not silently at runtime.

### 2. Backfill legacy `framework_id=NULL` gap items to `"dpdpa"`

**Files:** `app/main.py` (migration dict), `app/routers/web.py:184–186, 343`

Legacy `GapItem` rows predate multi-framework and have `framework_id IS NULL`. The code currently special-cases DPDPA with `OR framework_id IS NULL` in queries and list comprehensions. This should be a one-time data migration, not permanent presentation logic.

**Action:**
1. Add a migration entry in `_run_migrations()` in `app/main.py`:
   ```sql
   UPDATE gap_items SET framework_id = 'dpdpa' WHERE framework_id IS NULL
   ```
2. After the migration is in place, remove the DPDPA NULL fallback branches:
   - `web.py:184–186` — the `if framework_id == "dpdpa"` branch with the `OR framework_id.is_(None)` filter
   - `web.py:343` — the `or (active_framework == "dpdpa" and item.framework_id is None)` condition
   - Any similar pattern in the codebase (grep for `framework_id is None` or `framework_id.is_(None)`)

### 3. Rename `_brand_rgb` to `brand_rgb` (public API)

**Files:** `app/utils/pdf_export.py:95`, `app/utils/rfi_export.py`, `app/utils/evidence_checklist_export.py`

`_brand_rgb()` has a leading underscore (private convention) but is imported by two other modules. Either:
- Rename to `brand_rgb()` and update all import sites, OR
- Have each consumer parse `settings.firm_primary_hex` independently

Prefer the rename — it's one function, three files.

### 4. Fix `_brand_rgb` return type annotation

**File:** `app/utils/pdf_export.py:95–101`

The annotation says `-> tuple[int, int, int]` but `tuple()` with a generator returns `tuple[int, ...]`. Fix:
```python
r, g, b = (int(value[i:i+2], 16) for i in (0, 2, 4))
return (r, g, b)
```

### 5. Harden default credentials (pre-existing, low priority)

**File:** `app/config.py:11–12`

`session_secret` defaults to `"change-me-in-production"` and `auditor_password` to `"admin"`. For MVP this is acceptable, but consider:
- Generating a random `session_secret` at startup if the default is detected (log a warning)
- Or adding a Pydantic validator that warns when the shipped defaults are active

This is lowest priority — address only if the other 4 tasks are done cleanly.

---

## Constraints

- All existing tests must continue to pass (`pytest` — currently 24/24 green).
- Do not touch the fixes already applied in this session (branding dict in `main.py`, hex validator in `config.py`, `StopIteration` guard in `web.py:336`, `assessment.frameworks` in `web.py:1318`).
- Keep changes minimal — these are targeted fixes, not a refactor.
