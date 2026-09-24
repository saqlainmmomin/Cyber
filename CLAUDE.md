# CyberAssess

AI-powered multi-framework compliance maturity platform (DPDPA, ISO 27001, GDPR, HIPAA, NIST CSF, PCI-DSS) — Jinja2 + HTMX + Tailwind. Desk-review pre-fill, adaptive tiering, tiered LLM gap analysis, deterministic scoring, board-ready PDF/RFI reports, controls de-duplicated via Unified Control Clusters.

## Current Plan (source of truth)

**Implementation plan:** `docs/plans/2026-09-21-002-revised-implementation-plan.md`
**Product requirements:** `docs/product/2026-09-21-cyberassess-product-requirements.md`
**Decisions log:** `tasks/2026-09-21-adversarial-review.md` (D1–D11)
**Task ownership (Claude vs Codex):** `tasks/agent-ownership.md` — check before scoping any handoff.

All older plans in `docs/plans/` and `tasks/` are superseded. Do NOT use `2026-09-21-001-*`, `multi-framework-demo-plan.md`, or any plan dated before 2026-09-21 for implementation decisions.

**Current phase:** Phase 1 complete (PRs #16-#23). Phase 2 (Evidence & Conclusions) complete (PRs #24-#29). Phase 3 (Reports & Remediation) complete: P3-1 through P3-4 merged (PRs #30-#33). Phase 4 (AWS & Validation) complete: P4-1 through P4-4 merged (PRs #34-#37). **Phase 5 (Cleanup & non-DPDPA parity) complete:** P5-8, P5-1, P5-5, P5-3, P5-4, P5-2, P5-6 merged (PRs #38-#41, #44, #45, #46); P5-7 deliberately unscheduled — plan: `docs/plans/2026-09-24-001-cleanup-and-non-dpdpa-parity-plan.md`; kickoff: `tasks/handoffs/2026-09-24-phase-5-kickoff.md`. P5-9 (end-to-end validation, plan `docs/plans/2026-09-24-002-p5-9-end-to-end-validation-plan.md`) is separate and not part of Phase 5's completion. See `tasks/todo.md`.
**Pre-work sprint:** Completed (PW-1 through PW-5).

## Running
```bash
cp .env.example .env   # add OPENROUTER_KEY
pip install -r requirements.txt
uvicorn app.main:app --reload   # needs Python 3.13, see gotchas
pytest
```

## Key Files

| Path | Purpose |
|---|---|
| `app/main.py` | FastAPI app, routers |
| `app/frameworks/` | Registry, 6 `FrameworkDefinition`s, UCC cluster mappings |
| `app/dpdpa/` | DPDPA domain knowledge — legacy single-framework path |
| `app/services/claude_analyzer.py` | Tiered, OpenRouter-backed gap analysis pipeline |
| `app/services/llm_client.py` | Shared LLM client, model per tier via `Settings.llm_model_*` |
| `app/services/scoring.py` | Deterministic scoring engine (never an LLM) |
| `app/services/screening.py`, `tier_engine.py` | Adaptive Assessment Engine |
| `app/utils/pdf_export.py` | Board-level PDF, custom fpdf2 |
| `app/routers/web.py` | Jinja2 + HTMX portal routes |

## Gotchas
- **Python 3.13 required** — system Python too old, Homebrew 3.14 breaks Jinja2's `LRUCache`.
- **All PDF text through `S()`** (latin-1 sanitizer) — missing it crashes fpdf2.
- **Scoring is deterministic, server-side** — the LLM outputs qualitative strings only.
- **Every LLM call site is OpenRouter-tiered now** (`app/services/llm_client.py`); prompt-cache
  passthrough is unverified (`cache_read_input_tokens` was 0 on a live call). Vision (image OCR
  in `document_processor.py`) uses its own `llm_model_vision` tier — the text tiers aren't
  vision-capable.
- **DPDPA framework lives in Python dicts**, not the database — version-controlled, prompt-embeddable.
- **PDF sections are additive-only** — don't rewrite existing pages.
- **No auth** (single-user MVP); JSON stored as TEXT columns, no native JSON type.
- **Framework-specific copy must be conditional** (e.g. `has_dpdpa`), never a default.
- **`validation/companies/*/answer_key.json` is a held-out evaluation set** — never read it while changing prompts/analyzer/desk review, and never tune against a specific planted gap (D-P5-9-C).
- **Non-DPDPA scope profiling isn't implemented** — questionnaire exclusion is a no-op for ISO/GDPR/HIPAA/NIST/PCI.
