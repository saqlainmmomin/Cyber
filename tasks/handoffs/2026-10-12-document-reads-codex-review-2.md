# Handoff: second review of the document-reads plan, revision 3 (Codex)

## Goal
Revision 2 of the plan got **NO-GO as written** from your first review (`tasks/handoffs/2026-10-11-document-reads-codex-review.md`, 29 findings). Saqlain then approved a narrower first version and decided: **shared code that is meant to serve every framework must stop assuming DPDPA, but nothing DPDPA assessments use may be deleted.** Revision 3 is the `## Results` section of `tasks/handoffs/2026-10-10-document-budget-design.md`. Review it against the codebase. Saqlain wants no complications later from code this plan changes. Done means a `## Codex review 2` section appended to **this** file with a verdict. If the verdict is GO, implementation starts from this plan.

## Rules
- Read-only. No code changes, no prompt edits, no commits, no pushes. The only file you write is this one.
- No live LLM or API calls. Tests, if any, with `OPENROUTER_KEY=""` (never `env -u`). Writing caches or temp files outside the repo is fine.
- Never read `validation/companies/*/answer_key.json`. Reading `company.json` framework fields is fine.
- Every claim cites a file and line you actually read. Say when you could not verify something.
- Plain short sentences. No em dashes. No AI attribution anywhere.
- Read `CLAUDE.md` and `AGENTS.md` first.

## What to check
1. **Your 29 findings.** The Results has a table mapping each finding to how revision 3 handles it. For each one: resolved, partly resolved, or not resolved, and why. Do not re-raise a finding that the narrower scope has legitimately removed (for example stale-only runs), but do say if the removal itself breaks something.
2. **Stage 2, shared code that assumes DPDPA.** Saqlain's rule: "I don't want you to delete code that is being used by DPDPA assessment. I only want you to delete things or remove things that are supposed to be framework agnostic, but are using DPDPA-specific plumbing." The plan's DPDPA section has a "Kept" list (must not change) and a "Candidates" list (shared code to fix). For each candidate: is it really shared code with a DPDPA assumption, what does the fix touch, and what could break? Then search for any shared code with a DPDPA assumption the list missed: hardcoded `"dpdpa"` fallbacks, `app.dpdpa` imports into shared services, DPDPA vocabulary in generic prompts, templates or copy that is not conditional, DPDPA category lists, DPDPA-prefixed id parsing. In particular:
   - Are the "null framework_id means DPDPA" readers safe to remove after a backfill? Which tables need it, and does `app/legacy_migrations.py` already cover them?
   - Can `Assessment.frameworks` stop defaulting to `["dpdpa"]` without breaking creation flows, seeds or the API?
   - Initiative grouping in `app/services/scoring.py`: what do ISO and NIST gaps get today, and what do reports and initiatives tests assert?
   - Context interview (`app/dpdpa/context_questions.py`) and scope profiler: is the shared use DPDPA-specific or neutral?
   - Confirm that nothing in the "Kept" list changes in stage 2, and that the DPDPA goldens stay byte-identical.
   - Is a stage-2 A/B on all validation companies a fair, sufficient gate?
3. **Stages 1 and 3 to 6.** Is each stage independently shippable and safe behind `evidence_reads_mode`? Any ordering problem? Any stage too big to review in one PR?
4. **Stage 5 contracts.** Can desk review keep `DeskReviewSummary` and `DeskReviewFinding` fields and shapes unchanged when its input becomes saved passages? Is `document_id` staying empty for new-mode findings safe for every consumer? Can every registry framework go through the batched judge builder without changing judge wording for equal inputs? Can the curated DPDPA desk review and judge take saved passages through their existing quote inputs, with the DPDPA goldens still byte-identical when the setting is off?
5. **Budgets and the cost model.** Check the arithmetic and the assumptions, including the 910 read calls for the 100-file case and the bulk-drop time.
6. **Anything else** that would cause a complication later.

## Report back
Append `## Codex review 2` to this file:
1. Verdict: **GO**, **GO with changes**, or **NO-GO**, in one sentence.
2. Finding status table for F1 to F29.
3. New findings table: severity (blocker, major, minor), what is wrong or missing, file and line, and the concrete change.
4. The stage-2 inventory: every item, marked shared code with a DPDPA assumption (fix), used by DPDPA assessments (keep), or unclear, with file and line.
5. Open questions you could not settle from the code.
