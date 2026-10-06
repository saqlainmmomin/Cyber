# CyberAssess

AI-powered multi-framework compliance maturity platform (DPDPA, ISO 27001, GDPR, HIPAA, NIST CSF, PCI-DSS) — Jinja2 + HTMX + Yozora design tokens. Desk-review pre-fill, adaptive tiering, tiered LLM gap analysis, deterministic scoring, board-ready PDF/RFI reports, controls de-duplicated via Unified Control Clusters.

## Current Plan (source of truth)

**Implementation plan:** `docs/plans/2026-09-21-002-revised-implementation-plan.md`
**Product requirements:** `docs/product/2026-09-21-cyberassess-product-requirements.md`
**Decisions log:** `tasks/2026-09-21-adversarial-review.md` (D1–D11)
**Task ownership (Claude vs Codex):** `tasks/agent-ownership.md` — check before scoping any handoff.

Plans dated before 2026-09-21 (incl. `2026-09-21-001-*`, `multi-framework-demo-plan.md`) are superseded.

**Current phase:** Phase 6 deliverables done (v1 pipeline live, v2 parked: `tasks/2026-09-30-p6-5c-decision-park-v2.md`). **Yozora UI redesign complete: S1-S9 merged** (PRs #100-#115). Next: Track 4 (auth, hosting). Status: `tasks/2026-10-06-status-log.md`. Local-only until Track 4.

## Running
```bash
cp .env.example .env   # add OPENROUTER_KEY
pip install -r requirements-dev.txt
uvicorn app.main:app --host 127.0.0.1 --reload   # needs Python 3.13, see gotchas
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
| `design/`, `docs/product/yozora-*.md` | Yozora tokens, design guide, fidelity gate; macros in `app/templates/components/` |

## Gotchas
- **Python 3.13 required** — system Python too old, Homebrew 3.14 breaks Jinja2's `LRUCache`.
- **Scoring is deterministic, server-side** — the LLM outputs qualitative strings only.
- **No auth** (single-user MVP); JSON stored as TEXT columns, no native JSON type.
- **v2 analysis pipeline is parked** (`ANALYSIS_PIPELINE_VERSION=v2`): don't flip it or retune the judge prompt without a new decision (see the P6-5c record).
- **Yozora UI:** edit CSS in `design/*.css`, then `python -m design.tokens_tool build` (the `app/static/css/yozora-*.css` copies are generated). Tailwind is retired. Rules in `.claude/rules/yozora-ui.md`.
- **Framework-specific copy must be conditional** (e.g. `has_dpdpa`), never a default.
- **`validation/companies/*/answer_key.json` is a held-out evaluation set** — never read it while changing prompts/analyzer/desk review, and never tune against a specific planted gap (D-P5-9-C). Code paths are enforced by `tests/test_answer_key_isolation.py`.
- Backend rules (PDF `S()`, LLM tiering and deadlines, DPDPA dicts, scoping gaps): `.claude/rules/backend.md`.
