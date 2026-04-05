# CyberAssess — DPDPA Gap Assessment Tool

## Project Overview
AI-powered DPDPA (Digital Personal Data Protection Act, 2023) compliance gap assessment tool. Currently API-only backend; evolving to include a Jinja2 + HTMX + Tailwind web portal (see `docs/plans/2026-04-04-001-feat-intelligent-audit-assistant-plan.md`).

## Running
```bash
cp .env.example .env  # add ANTHROPIC_API_KEY
pip install -r requirements.txt
uvicorn app.main:app --reload
# API at http://localhost:8000
```

## Tech Stack
- **Python 3.13 + FastAPI** — ASGI web framework
- **SQLite via SQLAlchemy 2.0** — synchronous, `check_same_thread=False`
- **Anthropic SDK** — Claude `claude-sonnet-4-6` with prompt caching
- **pdfplumber / python-docx** — document text extraction
- **fpdf2** — PDF report generation
- **No auth** — MVP single-user (session auth planned for web portal)
- **No test framework** — no pytest, no test files yet
- **No migration tool** — DIY migrations in `app/main.py:_run_migrations()`

## Architecture

### Module Layout
```
app/
  main.py                   # FastAPI app, lifespan, CORS, router includes
  config.py                 # Pydantic Settings (env vars)
  database.py               # SQLAlchemy engine, session, Base
  dpdpa/                    # Domain knowledge (DPDPA-specific)
    framework.py            # 41 requirements as nested Python dicts + dependency DAG + root cause clusters
    prompts.py              # Claude prompt builders (system + user, with prompt caching)
    questionnaire.py        # Compliance questions (1 per requirement), GRC 5-option scale, relevance weighting
    context_questions.py    # 16 context-gathering questions across 4 blocks
  models/                   # SQLAlchemy ORM models
    assessment.py           # Assessment + AssessmentDocument
    questionnaire.py        # QuestionnaireResponse
    report.py               # GapReport + GapItem
    initiative.py           # Initiative
  schemas/                  # Pydantic request/response schemas
    assessment.py
    context.py
    questionnaire.py
    report.py
    initiative.py
  routers/                  # FastAPI route handlers (REST API)
    assessments.py          # CRUD for assessments
    questionnaire.py        # Context questions, compliance questionnaire, responses
    documents.py            # Document upload/list/delete
    analysis.py             # Trigger Claude gap analysis
    reports.py              # Gap report retrieval + PDF download
  services/                 # Business logic
    claude_analyzer.py      # Two-call Claude pipeline (evidence extraction + gap analysis)
    context_profiler.py     # Derives risk profile from context answers (deterministic signals + Claude)
    document_processor.py   # PDF/DOCX text extraction + Claude vision for images
    scoring.py              # Weighted compliance scoring + initiative generation
  utils/
    pdf_export.py           # Board-level PDF report (942 lines, custom fpdf2 drawing)
```

### Assessment Pipeline (Current)
```
1. POST /api/assessments                           → Create assessment
2. POST /api/assessments/{id}/context              → Submit 16 context questions → derive risk profile
3. GET  /api/assessments/{id}/questionnaire/sections → Get adaptive compliance questionnaire
4. POST /api/assessments/{id}/responses            → Submit questionnaire responses (GRC 5-option scale)
5. POST /api/assessments/{id}/documents            → Upload documents (PDF/DOCX/images)
6. POST /api/assessments/{id}/analyze              → Run Claude analysis (2 calls)
7. GET  /api/assessments/{id}/report               → JSON report
8. GET  /api/assessments/{id}/report/pdf           → PDF download
```

### Claude Analysis Pipeline (Two-Call Architecture)
**Call 1 — Evidence Extraction** (`claude_analyzer.py:_run_evidence_extraction`):
- Only runs when documents are present
- Extracts exact quotes from documents mapped to requirement IDs
- Output: `{"evidence": {"CH2.CONSENT.1": ["quote1", ...], ...}}`

**Call 2 — Gap Analysis** (`claude_analyzer.py:run_gap_analysis`):
- System prompt uses prompt caching (`cache_control: {"type": "ephemeral"}`) on requirements block
- Receives: org profile, risk profile, questionnaire responses, evidence (from Call 1 or raw docs)
- Returns: `executive_summary` + 41 `assessments` (each with 11 fields: compliance_status, current_state, gap_description, risk_level, remediation_action, etc.)

**Context Profiling** (`context_profiler.py`):
- Deterministic signal extraction from context answers (sdf_candidate, children_data, cross_border, etc.)
- One Claude call to derive: risk_tier, priority_chapters, likely_not_applicable, industry_context
- Deterministic signals override Claude's output

### DPDPA Framework (`dpdpa/framework.py`)
- **6 chapters** with weights: Chapter 2 (0.30), Chapter 3 (0.20), Chapter 4 (0.20), Consent Mgmt (0.10), Cross-Border (0.10), Breach Notification (0.10)
- **41 requirements** total, each with: id (e.g., "CH2.CONSENT.1"), title, description, section_ref, criticality
- **Dependency DAG** (`REQUIREMENT_DEPENDENCIES`): 20 requirement dependencies for remediation sequencing
- **Root Cause Clusters** (`ROOT_CAUSE_CLUSTERS`): 5 types (policy, people, process, technology, governance) → initiative templates
- Helper: `get_all_requirements()` flattens the tree into a list of 41 dicts enriched with chapter/section metadata

### Scoring Engine (`services/scoring.py`)
- **Deterministic** — Claude does qualitative analysis only, scoring is server-side
- Status scores: compliant=100, partially_compliant=50, non_compliant=0, not_assessed=excluded
- Formula: requirement → section (avg) → chapter (weighted avg) → overall (weighted avg by chapter weights)
- Thresholds: >=80 Compliant, >=60 Partially Compliant, >=40 Needs Significant Improvement, <40 Non-Compliant
- Initiative generation: groups gaps by root cause category → named initiatives with budget bands

### Database Models
| Model | Table | Key Fields |
|---|---|---|
| Assessment | assessments | id (UUID), company_name, industry, company_size, status, context_answers (JSON text), context_profile (JSON text) |
| AssessmentDocument | assessment_documents | assessment_id (FK), filename, file_path, document_category, extracted_text |
| QuestionnaireResponse | questionnaire_responses | assessment_id (FK), question_id, answer, notes, evidence_reference, confidence |
| GapReport | gap_reports | assessment_id (unique FK), overall_score, chapter_scores (JSON), executive_summary, raw_ai_response |
| GapItem | gap_items | report_id (FK), requirement_id, compliance_status, gap_description, risk_level, maturity_level, evidence_quote |
| Initiative | initiatives | report_id (FK), root_cause_category, requirements_addressed (JSON), budget_estimate_band |

**Note:** No SQLAlchemy `relationship()` declarations. All links via `.filter()` on FK columns.
**Note:** JSON stored as TEXT columns (no JSON column type).
**Assessment status flow:** created → context_gathered / documents_uploaded → questionnaire_done → analyzing → completed / error

### PDF Report (`utils/pdf_export.py`)
- 942 lines of custom fpdf2 drawing
- **All text must go through `S()`** (latin-1 sanitizer, line 75) — translates unicode to ASCII. Missing this crashes fpdf2.
- Pages: Cover → Executive Dashboard → Critical/High Gaps → Remediation Roadmap → Strategic Initiatives → Appendix (detailed findings, scope & limitations, methodology)
- Brand palette: Navy (30,30,80), status colors (green/yellow/red/gray)
- PDF sections are additive-only — don't rewrite existing pages, add new content in appendix

### Document Processing (`services/document_processor.py`)
- PDF: pdfplumber extracts text + tables
- DOCX: python-docx extracts paragraphs + tables
- Images (PNG/JPG/WEBP): sent to Claude vision → text transcription + compliance summary
- Per-doc word limit: 5,000 words. Cross-doc limit: 20,000 words (`claude_analyzer.py:_truncate_documents`)
- `extract_relevant_sections()` exists but is unused (smart section extraction by keyword scoring)

## Hard Rules
1. **All PDF text through `S()`** — no exceptions. Every `pdf.text()`, `pdf.cell()`, `pdf.multi_cell()`.
2. **Scoring is deterministic and server-side** — Claude outputs qualitative strings, `scoring.py` converts to numbers. Never let Claude compute scores.
3. **DPDPA framework stays in Python dicts** (`framework.py`), not in the database. Version-controlled, embeddable in prompts.
4. **PDF sections are additive-only** — existing pages are visually tuned. New content goes in appendix or as new pages. Reuse `_section_title()`, `_page_header()`, `_page_footer()` helpers.
5. **Dummy company for demos**: "Meridian Retail Ltd"

## Current Plans
- **Intelligent Audit Assistant**: `docs/plans/2026-04-04-001-feat-intelligent-audit-assistant-plan.md`
  - Phase 1: Web portal (Jinja2 + HTMX + Tailwind)
  - Phase 2: Desk review pipeline (document-first analysis, Call 0)
  - Phase 3: Adaptive assessment engine (industry questions, conversational follow-ups)
  - Phase 4: Output generation (RFI document, policy generation, enhanced reports)
