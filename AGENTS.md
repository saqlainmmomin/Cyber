# CyberAssess

CyberAssess is a multi-framework compliance maturity platform. Its FastAPI, Jinja2, HTMX, and Tailwind portal supports desk-review pre-fill, deterministic scoring, reports, RFIs, and UCC de-duplication.

## Current Plan (source of truth)

**Implementation plan:** `docs/plans/2026-09-21-002-revised-implementation-plan.md`
**Product requirements:** `docs/product/2026-09-21-cyberassess-product-requirements.md`
**Decisions log:** `tasks/2026-09-21-adversarial-review.md` (D1–D11)
**Task ownership (Claude vs Codex):** `tasks/agent-ownership.md` — check before scoping any handoff.

Older plans are historical only; do not use them for implementation decisions.

**Current:** Phase 1 — Schema & Hierarchy. P1-1/P1-2/P1-6 merged; P1-3 implemented, PR #19 open; P1-4/P1-5 not started.
**Pre-work:** Complete.
**Progress tracking:** Update `tasks/todo.md` in the same change as each completed task.

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
| `app/main.py` | App, routers |
| `app/frameworks/` | Registry, definitions, UCC mappings |
| `app/dpdpa/` | Legacy DPDPA knowledge |
| `app/services/claude_analyzer.py` | Tiered, OpenRouter-backed gap analysis pipeline |
| `app/services/llm_client.py` | Shared LLM client, model per tier |
| `app/services/scoring.py` | Deterministic scoring |
| `app/services/screening.py`, `tier_engine.py` | Adaptive Assessment Engine |
| `app/utils/pdf_export.py` | Board-level PDF export |
| `app/routers/web.py` | Jinja2/HTMX portal routes |

## Gotchas
- Python 3.13 required; 3.9 is too old and Homebrew 3.14 breaks Jinja2 `LRUCache`.
- All PDF text goes through `S()`; otherwise fpdf2 crashes.
- Scoring is server-side and deterministic; LLMs are qualitative only.
- DPDPA knowledge uses version-controlled Python dictionaries, not the DB.
- PDF sections are additive only.
- Single-user MVP: no auth; JSON columns use TEXT.
- Framework copy must be conditional.
- All LLM calls are OpenRouter-tiered (`app/services/llm_client.py`).
