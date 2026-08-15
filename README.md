# CyberAssess

AI-powered multi-framework compliance maturity platform with a Jinja2 + HTMX + Tailwind web portal. Desk-review pre-fill, adaptive tiering, domain screening, two-call Claude gap analysis, deterministic scoring, and board-ready PDF/RFI reports — controls de-duplicated across frameworks via Unified Control Clusters (UCC).

## Supported Frameworks

| Framework | Version | Status |
|---|---|---|
| DPDPA (India Digital Personal Data Protection Act) | 2023 | Live |
| ISO 27001 | 2022 | Live |
| GDPR | 2016/679 | Live |
| HIPAA | 2013 | Live |
| NIST CSF | 2.0 | Live |
| PCI-DSS | 4.0 | Live |

Controls that overlap across frameworks are mapped to shared **Unified Control Clusters** (`app/frameworks/mappings/clusters.py`) so an organisation answers each underlying control once, not once per framework.

## What It Does

1. **Desk review** — upload existing policy documents; Claude extracts evidence and pre-fills questionnaire answers.
2. **Adaptive tiering & domain screening** — assessment scope narrows based on organisation risk profile and applicable domains.
3. **Adaptive questionnaire** — context-aware questions across UCC-mapped controls.
4. **Two-call Claude gap analysis** — evidence extraction, then qualitative gap analysis (scoring itself is deterministic and never delegated to Claude).
5. **Report & review workflow** — HTML dashboard, gap items with risk/remediation/effort/timeline, CMMI maturity levels (0–5), root-cause clustered initiatives, prioritised roadmap.
6. **Outputs** — board-ready PDF report, RFI (Request for Information) PDF/DOCX, evidence checklist PDF/DOCX.

## Architecture

```
FastAPI · Jinja2 + HTMX + Tailwind (web portal) · SQLite via SQLAlchemy · Claude API (Anthropic) · fpdf2
```

**Assessment flow (web portal):**

```
1. Create assessment          /assessments/new
2. Scope & domain screening   /assessments/{id}/scope, /screening
3. Desk review (optional)     /assessments/{id}/upload → run-desk-review
4. Context questions          /assessments/{id}/context/block/{n}
5. Adaptive questionnaire     /assessments/{id}/questionnaire/sections
6. Run Claude gap analysis    /assessments/{id}/run-analysis
7. Review & report            /assessments/{id}/review, /report-summary
8. Generate outputs           PDF report, RFI, evidence checklist
```

A JSON API (`app/routers/assessments.py`, `questionnaire.py`, `analysis.py`, `reports.py`) exposes the same pipeline programmatically — see `/docs`.

**Design decisions:**
- Frameworks stored as versioned Python dicts (`app/frameworks/definitions/`) — embeddable in prompts, not in the DB
- Unified Control Clusters de-duplicate overlapping controls across the 6 frameworks
- Scoring is deterministic, server-side (`app/services/scoring.py`) — Claude outputs qualitative strings only
- Two-call Claude architecture: evidence extraction → gap analysis, with prompt caching on the requirements block
- Startup-time SQL migration runner — no migration tooling required
- No auth — single-user MVP; JSON stored as TEXT columns (no native JSON type)

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
| `app/routers/` | JSON API routers (assessments, questionnaire, analysis, reports, desk_review, review, remediation) |

## Running

```bash
cp .env.example .env        # add ANTHROPIC_API_KEY
pip install -r requirements.txt
uvicorn app.main:app --reload   # needs Python 3.13 — see Gotchas
pytest
# Web portal at http://localhost:8000
# API docs at http://localhost:8000/docs
```

Or with Docker:

```bash
docker-compose up
```

## Gotchas

- **Python 3.13 required** — system Python (3.9) is too old, and Homebrew 3.14 breaks Jinja2's `LRUCache`.
- **All PDF text must go through `S()`** (latin-1 sanitizer) — missing it crashes fpdf2.
- **Scoring is deterministic, server-side** — Claude never produces the numeric score, only qualitative strings.
- **DPDPA framework lives in Python dicts**, not the database — version-controlled, prompt-embeddable.
- **PDF sections are additive-only** — don't rewrite existing pages.
- **Framework-specific copy must be conditional** (e.g. `has_dpdpa`), never a default — 6 frameworks are supported, not just DPDPA.

## Extending to a New Framework

1. Add `app/frameworks/definitions/<framework>.py` — a `FrameworkDefinition` with controls tree and weights
2. Register it in `app/frameworks/registry.py`
3. Map overlapping controls into existing Unified Control Clusters in `app/frameworks/mappings/clusters.py`
4. Add framework-specific prompt guidance in `app/frameworks/prompts.py`

The scoring engine, PDF export, initiative clustering, and report endpoints are framework-agnostic.

## Stack

- Python 3.13 + FastAPI
- Jinja2 + HTMX + Tailwind — server-rendered web portal
- SQLite via SQLAlchemy (JSON stored as TEXT columns)
- [Anthropic Claude API](https://docs.anthropic.com) with prompt caching
- pdfplumber + python-docx — document text extraction
- fpdf2 — PDF generation
- Docker + docker-compose
