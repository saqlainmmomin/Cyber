# CyberAssess

AI-powered compliance gap assessment platform. Structured questionnaires, document analysis via Claude, deterministic scoring, and board-ready reports — PDF and HTML dashboard.

**Current module: DPDPA** (India's Digital Personal Data Protection Act, 2023). Built to extend to ISO 27001, SOC 2, GDPR, and other frameworks.

## What It Does

Organisations answer a structured questionnaire, optionally upload supporting documents (privacy policies, DPIAs, breach procedures), and receive a board-ready compliance gap report with:

- Overall compliance score (weighted, deterministic)
- Chapter-level breakdown with scores and ratings
- Gap items with current state, gap description, risk level, remediation action, effort, and timeline
- CMMI maturity levels (0–5) per requirement
- Root-cause clustered strategic initiatives with budget bands
- Prioritised remediation roadmap
- HTML dashboard (editorial design, print-ready) + PDF report

## Modules

| Module | Framework | Requirements | Status |
|--------|-----------|-------------|--------|
| DPDPA | Digital Personal Data Protection Act 2023 (India) | 41 | Live |
| ISO 27001 | Information Security Management | — | Planned |
| SOC 2 | Trust Services Criteria | — | Planned |

## Architecture

```
FastAPI  ·  SQLite via SQLAlchemy  ·  Claude API (Anthropic)  ·  fpdf2
```

**Assessment pipeline:**

```
1. Create Assessment        POST /api/assessments
2. Context Gathering        POST /api/assessments/{id}/context       (risk profiling)
3. Adaptive Questionnaire   GET  /api/assessments/{id}/questionnaire/sections
4. Submit Responses         POST /api/assessments/{id}/responses
5. Upload Documents         POST /api/assessments/{id}/documents     (optional)
6. Run Analysis             POST /api/assessments/{id}/analyze       (Claude)
7. Get Report               GET  /api/assessments/{id}/report
8. Download PDF             GET  /api/assessments/{id}/report/pdf
```

**Design decisions:**
- Framework stored as versioned Python dicts — embeddable in prompts, not in DB
- Scoring is deterministic server-side — Claude does qualitative analysis only
- Two-call Claude architecture: evidence extraction → gap analysis
- Prompt caching on the requirements block — consistent cache hits across assessments
- Startup-time SQL migration runner — no migration tooling required
- No auth — single-user demo tool (MVP)

## Key Files

```
app/
  dpdpa/
    framework.py          DPDPA 41 requirements, dependency DAG, root cause clusters
    questionnaire.py      Context-aware questions with GRC 5-option scale
    prompts.py            Claude system/user prompt builders (cached)
    context_questions.py  15 context questions across 4 blocks
  services/
    claude_analyzer.py    Two-call Claude pipeline
    scoring.py            Weighted scoring + initiative generation
    context_profiler.py   Risk profile derivation from context answers
    document_processor.py Section-aware document text extraction
  models/                 SQLAlchemy models (Assessment, Report, GapItem, Initiative)
  routers/                FastAPI routers (assessments, questionnaire, analysis, reports)
  utils/
    pdf_export.py         Board-level PDF with maturity badges + initiatives section
data/
  prestige_estates_dashboard_v2.html   Live example output — Prestige Estates DPDPA assessment
scripts/
  seed_prestige_analysis.py            Seeder to inject analysis without API call (demo/dev)
```

## Running

```bash
cp .env.example .env        # add ANTHROPIC_API_KEY
pip install -r requirements.txt
uvicorn app.main:app --reload
# API at http://localhost:8000
# Docs at http://localhost:8000/docs
```

Or with Docker:

```bash
docker-compose up
```

## Example Output

Live assessment: **Prestige Estates Projects Limited** — DPDPA gap assessment using real privacy policy.

- Overall score: **43.9% — Needs Significant Improvement**
- 10 compliant / 15 partially compliant / 16 non-compliant
- 11 critical gaps · 13 high gaps
- Average maturity: **M1.8** across 41 requirements
- 5 strategic initiatives generated with budget bands (₹5L to >₹1Cr)

Dashboard: `data/prestige_estates_dashboard_v2.html`

## Extending to a New Framework

1. Add `app/<framework>/framework.py` — requirements tree with weights
2. Add `app/<framework>/questionnaire.py` — one question per requirement
3. Add `app/<framework>/prompts.py` — system/user prompt builders
4. Wire a new router prefix in `app/main.py`

The scoring engine, PDF export, initiative clustering, and report endpoints are framework-agnostic.

## API Reference

Full interactive docs at `/docs` when running locally. Key endpoints:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/assessments` | Create assessment |
| GET | `/api/context-questions` | Get 4-block context questionnaire |
| POST | `/api/assessments/{id}/context` | Submit context answers + derive risk profile |
| GET | `/api/assessments/{id}/questionnaire/sections` | Get adaptive questionnaire sections |
| POST | `/api/assessments/{id}/responses` | Submit questionnaire responses |
| POST | `/api/assessments/{id}/documents` | Upload supporting documents |
| POST | `/api/assessments/{id}/analyze` | Run Claude gap analysis |
| GET | `/api/assessments/{id}/report` | Full JSON report |
| GET | `/api/assessments/{id}/report/summary` | Summary stats |
| GET | `/api/assessments/{id}/report/pdf` | Download PDF |

## Stack

- Python 3.13 + FastAPI
- SQLite via SQLAlchemy (swap for Postgres in production)
- [Anthropic Claude API](https://docs.anthropic.com) — `claude-sonnet-4-6` with prompt caching
- pdfplumber + python-docx — document text extraction
- fpdf2 — PDF generation
- Docker + docker-compose
