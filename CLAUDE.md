# DPDPA Gap Assessment Tool

## Project Overview
AI-powered DPDPA (Digital Personal Data Protection Act, 2023) compliance gap assessment backend.
API-first — frontend is built separately.

## Tech Stack
- Python 3.13 + FastAPI
- SQLite via SQLAlchemy
- Claude API (Anthropic SDK) for gap analysis
- pdfplumber / python-docx for document extraction
- fpdf2 for PDF report generation

## Key Architecture Decisions
- DPDPA framework stored as Python dicts in `app/dpdpa/framework.py` (not DB) — version-controlled, embeddable in prompts
- Scoring is deterministic server-side (not Claude) — reproducible results
- Analysis is synchronous (blocks for 15-30s while Claude responds)
- No auth — MVP single-user demo tool
- All text in PDFs must go through `S()` (latin-1 sanitizer) in `pdf_export.py`

## Running
```
cp .env.example .env  # add your ANTHROPIC_API_KEY
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## API Base URL
http://localhost:8000

## Key Files
- `app/dpdpa/framework.py` — DPDPA requirements tree (41 requirements)
- `app/dpdpa/prompts.py` — Claude system/user prompt templates
- `app/services/claude_analyzer.py` — Claude API integration
- `app/services/scoring.py` — Weighted compliance scoring
- `app/utils/pdf_export.py` — PDF report generation
