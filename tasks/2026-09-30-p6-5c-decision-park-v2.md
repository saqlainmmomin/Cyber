# P6-5c: Park the v2 analysis pipeline

**Decision (2026-09-30, Saqlain):** Park v2. v1 stays the production pipeline; v2 is not flipped on. Work moves to deliverables (P6-8 B2 Word/Excel export, P6-10 narrative). No third judge-prompt-wording attempt.

## Context
P6-5 compares the v2 grounded pipeline against v1 on a pre-registered gate. After PR #88 attached signed ISO 27001 and NIST CSF criteria, v2 answered `insufficient_evidence` (IE) on about 76% of requirements. Scoring counts IE as flagged (Decision 1), so catch and false positives rose together.

## Evidence
Full A/B, 4 companies x 3 runs, pooled, model deepseek/deepseek-v4-flash.

| Arm | Catch | Decoy FP | Clean FP | Stability | IE rate |
|---|---|---|---|---|---|
| v1 | 92.9% | 58.3% | 61.5% | 81.6% | 1.1% |
| v2-criteria (prompt p6-4.1) | 98.6% | 77.8% | 96.9% | 88.9% | 75.8% |
| v2-fix (prompt p6-4.3) | 98.6% | 88.9% | 97.9% | 88.2% | 76.3% |

The gate fails on decoy FP and clean FP for both v2 arms.

## What was tried
- p6-4.2 (stricter "met only when a claim shows it"): lost catch (78.7%). Not merged.
- p6-4.3 (judge fix, PR #90): no better than p6-4.1. Closed unmerged, kept for the record.
- Diagnosis (aggregates only): the judge credits about 11% of approved criteria; 95% of IE outcomes have zero criteria met; about 28% of requirement-runs have no claims at all. The one-blocking-criterion hypothesis was wrong.

## Why park
Two prompt attempts did not move the abstention rate. The approved ISO/NIST criteria ask for operating evidence (logs, samples, dated reviews) that the synthetic desk-review packs may not contain, so IE may be the correct answer. That is a benchmark-versus-auditor question, not a prompt bug.

## What must be decided before reopening v2 (Saqlain)
a. Criterion-aware evidence for the judge: extraction currently never sees the criteria.
b. Revisit Decision 1 (score.py FLAGGED includes insufficient_evidence). Needs his written sign-off and a recorded reason.
Optional free first check: do the client-visible company documents contain operating evidence at all?

## References
- Diagnosis and results: `~/cyberassess-abstain/tasks/handoffs/2026-09-30-v2-abstention-diagnosis-and-fix.md`
- c3 re-run: `~/cyberassess-abstain/tasks/handoffs/2026-09-30-p6-5-abstention-c3-rerun.md`
- Comparison: `~/cyberassess-runs/2026-09-30-p6-5-ab-abstain/ab_comparison.md`
- Run data: `~/cyberassess-runs/2026-09-30-p6-5-v2-abstain/`
- PR #89 (merged, LLM deadline): https://github.com/saqlainmmomin/Cyber/pull/89
- PR #90 (closed, p6-4.3): https://github.com/saqlainmmomin/Cyber/pull/90
