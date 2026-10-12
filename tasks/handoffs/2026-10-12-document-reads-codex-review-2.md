# Handoff: second review of the document-reads plan, revision 3 (Codex)

## Goal
Revision 2 of the plan got **NO-GO as written** from your first review (`tasks/handoffs/2026-10-11-document-reads-codex-review.md`, 29 findings). Saqlain then approved a narrower first version and decided: **no DPDPA-only plumbing in the app.** Revision 3 is the `## Results` section of `tasks/handoffs/2026-10-10-document-budget-design.md`. Review it against the codebase. Saqlain wants no complications later from code this plan changes. Done means a `## Codex review 2` section appended to **this** file with a verdict. If the verdict is GO, implementation starts from this plan.

## Rules
- Read-only. No code changes, no prompt edits, no commits, no pushes. The only file you write is this one.
- No live LLM or API calls. Tests, if any, with `OPENROUTER_KEY=""` (never `env -u`). Writing caches or temp files outside the repo is fine.
- Never read `validation/companies/*/answer_key.json`. Reading `company.json` framework fields is fine.
- Every claim cites a file and line you actually read. Say when you could not verify something.
- Plain short sentences. No em dashes. No AI attribution anywhere.
- Read `CLAUDE.md` and `AGENTS.md` first.

## What to check
1. **Your 29 findings.** The Results has a table mapping each finding to how revision 3 handles it. For each one: resolved, partly resolved, or not resolved, and why. Do not re-raise a finding that the narrower scope has legitimately removed (for example stale-only runs), but do say if the removal itself breaks something.
2. **Stage 2, removing DPDPA-only plumbing.** This is new and is the riskiest part. Find **every** DPDPA-only branch, import and test: analysis routing, persistence, desk review, extraction, flag vocabulary, questionnaire, pre-fill, screening, scope profiling, follow-ups, scoring (`ROOT_CAUSE_CLUSTERS` in `app/services/scoring.py`), board/PDF reports, web routes and templates, seeds, scripts (for example `scripts/generate_facilitator_guide.py`), validation runner, goldens. For each, say whether it is plumbing (delete), content (keep), or unclear. In particular:
   - Can a `["dpdpa"]` assessment run end to end on the registry path today if the `is_multi` check and `is_dpdpa_only` branches are removed? What breaks?
   - Does the UCC questionnaire fully cover the 41 DPDPA controls, including scope profiling and applicability?
   - What screening removal touches (routes, templates, tabs, tests, the "adaptive tiering" claim in CLAUDE.md and product docs).
   - Can existing requirement-keyed DPDPA answers be mapped to UCC question keys cleanly (plan Q2)?
   - Is the Alembic data migration for findings with no `framework_id` enough to remove `LEGACY_FINDING_FRAMEWORK_ID`?
   - Is a stage-2 A/B on all validation companies a fair, sufficient gate?
3. **Stages 1 and 3 to 6.** Is each stage independently shippable and safe behind `evidence_reads_mode`? Any ordering problem? Any stage too big to review in one PR?
4. **Stage 5 contracts.** Can desk review keep `DeskReviewSummary` and `DeskReviewFinding` fields and shapes unchanged when its input becomes saved passages? Is `document_id` staying empty for new-mode findings safe for every consumer? Can every framework go through the batched judge builder without changing judge wording for equal inputs?
5. **Budgets and the cost model.** Check the arithmetic and the assumptions, including the 910 read calls for the 100-file case and the bulk-drop time.
6. **Anything else** that would cause a complication later.

## Report back
Append `## Codex review 2` to this file:
1. Verdict: **GO**, **GO with changes**, or **NO-GO**, in one sentence.
2. Finding status table for F1 to F29.
3. New findings table: severity (blocker, major, minor), what is wrong or missing, file and line, and the concrete change.
4. The stage-2 inventory: every DPDPA-only item, marked plumbing, content or unclear, with file and line.
5. Open questions you could not settle from the code.
