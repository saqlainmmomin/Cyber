# S1 spec review, round 2 (orchestrator, 2026-10-07)

Opus re-checked the build handoff after your fix pass. All 15 round-1 items are in, and you were right on the upload categories. Apply these in `tasks/handoffs/2026-10-07-flow-s1-demo-build.md` (line refs are to that file; re-verify each against the code):

1. BLOCKER: INTERIM approvals are refused without a report basis (conclusion_review.py:234-239 -> report_basis.approval_blocker). At :224 set report basis for INTERIM (period -90 to -15, cut-off -10) before approving; add the dates to §2 (:40).
2. BLOCKER: NIST id list undefined. At :75 say narrowing applies to PRIOR, CURRENT and INTERIM only; NIST keeps the set the scope save computes. Drop "narrow" at :225.
3. INTERIM never submits answers, so stage() stays on questionnaire (assessment_stage.py:120-124). At :85 submit PRIOR, CURRENT and INTERIM, one POST /api/assessments/{id}/responses each.
4. README step 8 (:243): /review is a 303 to /conclusions (web.py:3259-3271). Point at /assessments/<interim>/conclusions (3 approved, 3 pending); drop the /review URLs or list them as documented 303s.
5. Seed output dirtied git: use <db dir>/uploads/ for UPLOAD_DIR and <db dir>/uploads/demo_files/ for generated files (:18, :204, :233); README uvicorn uses UPLOAD_DIR=data/uploads.
6. Purge: rm -rf every path in plan.blob_roots under UPLOAD_DIR (retention.py:583-587), not just two folders (:206).
7. Line refs: update_report_basis is report_basis.py:179 (:38, :145); existing-client branch is web.py:1274-1283 (:44).
8. Don't reuse _approve_conclusions (hardcoded dates/globals, seed_test_companies.py:2140-2152); write a local approve loop after setting the basis (:112).
9. NIST half-questionnaire: sort by `section`, not `domain_group` (:70; question_engine.py:303-306).
10. §13 test subprocess: add cwd=REPO_ROOT (:258).
11. Relabel 3c INTERIM / 3d NIST; §9: Q2 access review maps to ISO.A5.18, the stale file is unmapped (:198); ISO.A5.19 finding target date +60 days (:140); README step 5 (:240): "see the seed's Skipped block"; backdate PRIOR snapshot generated_at to -290 too.
