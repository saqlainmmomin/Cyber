# Claude Code Prompt: Phase 3 Implementation

You are continuing the work on the Adaptive Assessment Engine for the DPDPA Gap Assessment Tool. Phase 1 (Document Pre-fill) and Phase 2 (Tiered Assessment Depth) are complete.

Your objective is to execute **Phase 3: Domain-Level Screening Pass**.

## 1. Context to Read
Before making any changes, please read the following files to understand the system architecture, the current state of the codebase, and the specific requirements for Phase 3:

1. **`docs/sessions/2026-05-03-adaptive-assessment-engine.md`** 
   - *Why:* Understands the recent decisions, work completed in Phase 1 & 2, and current data flow.
2. **`docs/plans/2026-05-03-001-feat-adaptive-assessment-engine-plan.md`**
   - *Why:* The overarching plan for the adaptive engine.
3. **`.gemini/antigravity/brain/e122e685-d231-4190-8042-eb42a852493c/artifacts/phase3_implementation_plan.md`**
   - *Why:* This is your **detailed execution plan** for Phase 3. It outlines the 7 specific files you need to create or modify.

## 2. Technical Stack Reminders
- **Backend:** FastAPI, SQLAlchemy (SQLite/PostgreSQL compatible). Use the existing session management and dependency injection patterns (see `app/database.py` and existing routers like `app/routers/web.py`).
- **Migrations:** We use a custom migration runner in `app/main.py` (`_run_migrations`). Add your new columns to the `migrations` dictionary there. Do not use Alembic.
- **Frontend:** Jinja2 templates with HTMX and TailwindCSS. Follow existing patterns in `app/templates/partials/`.
- **LLM Integration:** The project uses Claude via Anthropic's API. Check `app/services/claude_analyzer.py` or existing prompt patterns in `app/dpdpa/prompts.py` for how to structure the screening call.

## 3. Your Tasks
Follow the 7 steps in `phase3_implementation_plan.md`:
1. Update `app/models/assessment.py` with `screening_status` and `screening_results` columns.
2. Update `app/main.py` to run migrations for these columns.
3. Create `app/dpdpa/prompts.py` additions for the screening prompts.
4. Create `app/services/screening.py` to orchestrate the Claude inference.
5. Update `app/routers/web.py` with endpoints for the screening UI.
6. Update `app/services/question_engine.py` to integrate screening results (`inferred` source, `high/medium/low` confidence).
7. Create `screening_form.html` and update existing templates to handle the `inferred` badge.

## 4. Acceptance Criteria
- Make sure all database migrations run cleanly.
- Verify that the 9-question domain screening UI is accessible and submittable.
- Ensure the inference properly updates the `screening_results` in the DB.
- Ensure the questionnaire UI shows `inferred` pre-fills distinctly from `document` pre-fills (e.g., a purple "✨ Inferred" badge).
- Run the existing tests (`python tests/test_phase1_prefill.py` and `pytest tests/test_phase2_tiers.py`) to ensure no regressions.

Please review the context files first, then begin implementing the steps in order. Update the session log (`docs/sessions/2026-05-03-adaptive-assessment-engine.md`) with a new session entry when you are done.
