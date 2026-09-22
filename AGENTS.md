# CyberAssess

CyberAssess is a multi-framework compliance maturity platform for DPDPA, ISO 27001, GDPR, HIPAA, NIST CSF, and PCI-DSS. Its FastAPI, Jinja2, HTMX, and Tailwind portal supports desk-review pre-fill, adaptive tiering, deterministic scoring, reports, RFIs, and UCC-based control de-duplication.

## Current Plan (source of truth)

**Implementation plan:** `docs/plans/2026-09-21-002-revised-implementation-plan.md`
**Product requirements:** `docs/product/2026-09-21-cyberassess-product-requirements.md`
**Decisions log:** `tasks/2026-09-21-adversarial-review.md` (D1–D11)

All older plans in `docs/plans/` and `tasks/` are superseded. Do NOT reference `2026-09-21-001-*`, `multi-framework-demo-plan.md`, or any plan dated before 2026-09-21 for implementation decisions. Those are historical context only.

**Current phase:** Phase 1 — Schema & Hierarchy.
**Pre-work sprint:** Completed.

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
- Python 3.13 is required; system 3.9 is too old and Homebrew 3.14 breaks Jinja2 `LRUCache`.
- All PDF text passes through `S()`; otherwise fpdf2 can crash.
- Scoring is deterministic and server-side; LLMs provide qualitative output only.
- DPDPA knowledge is version-controlled Python dictionaries, not database content.
- Add PDF sections; do not rewrite existing pages.
- No auth (single-user MVP); JSON columns are stored as TEXT.
- Framework-specific copy must be conditional, never a default.
- Every LLM call site is OpenRouter-tiered (`app/services/llm_client.py`).
