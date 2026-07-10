# CyberAssess

AI-powered multi-framework compliance maturity platform (DPDPA, ISO 27001, GDPR, HIPAA, NIST CSF, PCI-DSS) with a Jinja2 + HTMX + Tailwind web portal. Desk-review pre-fill, adaptive tiering, domain screening, two-call Claude gap analysis, deterministic scoring, board-ready PDF/RFI reports — controls de-duplicated across frameworks via Unified Control Clusters.

## Running
```bash
cp .env.example .env   # add ANTHROPIC_API_KEY
pip install -r requirements.txt
uvicorn app.main:app --reload   # needs Python 3.13, see gotchas
pytest
```

## Key Files

| Path | Purpose |
|---|---|
| `app/main.py` | FastAPI app, DIY migrations, routers |
| `app/frameworks/` | Registry, 6 `FrameworkDefinition`s, UCC cluster mappings (`mappings/clusters.py`) |
| `app/dpdpa/` | DPDPA domain knowledge — legacy single-framework path, still used |
| `app/services/claude_analyzer.py` | Evidence extraction + gap analysis Claude calls |
| `app/services/scoring.py` | Deterministic scoring engine (never Claude) |
| `app/services/screening.py`, `tier_engine.py` | Adaptive Assessment Engine |
| `app/utils/pdf_export.py` | Board-level PDF, custom fpdf2 |
| `app/routers/web.py` | Jinja2 + HTMX web portal routes |

## Gotchas
- **Python 3.13 required** — system Python (3.9) too old, Homebrew 3.14 breaks Jinja2's `LRUCache`.
- **All PDF text through `S()`** (latin-1 sanitizer) — missing it crashes fpdf2.
- **Scoring is deterministic, server-side** — Claude outputs qualitative strings only.
- **DPDPA framework lives in Python dicts**, not the database — version-controlled, prompt-embeddable.
- **PDF sections are additive-only** — don't rewrite existing pages.
- **No auth** (single-user MVP); **JSON stored as TEXT columns**, no native JSON type.
- **Framework-specific copy must be conditional** (e.g. `has_dpdpa`), never a default — 6 frameworks supported, not just DPDPA.
