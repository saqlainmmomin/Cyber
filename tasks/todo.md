# WS1–WS3 execution — 2026-09-08

User requested three dedicated `gpt-5.6-sol` / medium subagents, one combined results handoff, and push/PR only after approval.

Working baseline: clean `docs/2026-09-08-handoffs`, commit `635291e`. Preserve the supplied handoffs; integrate on the existing feature branch. Native subagents explicitly requested; parent owns integrated verification and delivery. No publishing before approval.

- [x] WS1: configurable firm branding and isolated tests.
- [x] WS2: framework picker, tabs/report views, validated scoring contract and isolated tests.
- [x] WS3: canonical DPDPA fixtures, strict replay/capture harness, golden checks; finalize after WS1/WS2 stabilize. Report live-capture prerequisite honestly.
- [x] Inspect combined diff and resolve integration issues.
- [x] Run full tests, boot/browser smoke checks and applicable adversarial checks.
- [x] Write one results handoff with evidence and outstanding constraints.
- [x] Obtain user approval before commit/push/opening PR. User approved with "yes" on 2026-09-09.

Results: `tasks/handoffs/2026-09-09-ws1-ws2-ws3-results.md`. Final suite 53 passed; browser verified boosted report navigation. Additional full review interrupted by usage limit; bounded findings fixed and parent checked. Publication approved; feature branch `codex/ws1-ws2-ws3` was fast-forwarded to current main (1696a2e) before the implementation commit.

## PR #7 review tech debt — 2026-09-09

Source: `tasks/handoffs/2026-09-09-pr7-review-tech-debt.md`. Continue on `codex/ws1-ws2-ws3`; keep the fixes targeted and verify the integrated branch before handoff.

- [x] Assert the registered framework set matches the enabled and roadmap UI tuples.
- [x] Backfill legacy NULL gap-item framework IDs and remove presentation fallbacks.
- [x] Promote the PDF brand-color helper to a correctly typed public API.
- [x] Warn when shipped session or auditor credential defaults are active, if cleanly testable.
- [x] Run focused regression tests, the full suite, and a startup smoke check.
- [x] Complete the standalone simplify/review/handoff gates.

Verification: 62 tests passed after applying all three validated review findings. CyberAssess started against an isolated SQLite database with the final startup order, emitted both credential warnings, completed startup assertions/migrations, and returned HTTP 200 for `/assessments/new`.

## Plan status audit + reprioritization — 2026-09-15

Full write-up: `tasks/multi-framework-demo-plan.md` §9. Short version: WS #1-3 shipped
(PR #7), WS #6 (UCC clustering for ISO 27001 + NIST CSF) turned out to be ~99% done and
was never marked done in the plan. WS #4/#5/#7/#8/#9 have not started. WS #4
(framework-agnostic `screening.py`/`scoring.py`) is now the top-priority workstream —
it's the direct unblock for multi-framework assessments getting desk-review pre-fill,
screening pre-fill, and adaptive tiering, none of which they get today. 11 new gaps
found via a full data-flow trace (`docs/architecture/data-flow-and-processes.md`) are
folded into WS #4/#10 or flagged for a product decision — see plan §9.2.

- [x] Write the WS #4 handoff — `tasks/handoffs/2026-09-15-ws4-framework-agnostic-scoring.md`.
      Scope narrowed from the todo-audit description above after reading the actual code:
      `scoring.py`'s cluster-verdict engine (`score()`) generalizes cleanly to any single
      framework (mechanical, Codex-ready), and the multi-framework scope-exclusion no-op
      in `question_engine.py` is bundled in. `screening.py` staying DPDPA-only is now an
      explicit Non-goal in the handoff — generalizing it needs new per-framework
      domain-question content designed first (Claude/Saqlain judgment work, WS #6-shaped),
      not a mechanical refactor Codex can do from a spec alone.
- [ ] Get sign-off on the WS #4 handoff, then hand to Codex on `ws/4-framework-agnostic-scoring`.
- [x] Sketch the screening.py multi-framework design brief — `tasks/handoffs/2026-09-15-multi-framework-screening-design-brief.md`.
      Recommendation: build it as a second, independent code path (cluster/domain_group-based,
      ~7-9 questions covering all frameworks at once), leave DPDPA's existing screening
      untouched. Sequencing recommendation: don't schedule this until after WS #5's spike
      reports back — it should be designed together with WS #7's per-cluster analyzer
      contract, not before it, to avoid building the cluster-facing Claude interface twice.
- [ ] WS #10 cleanup sweep (dead code, remediation validation) — cheap, can run in parallel, no dependencies.

## Multi-framework screening spec review — 2026-09-16

Codex produced `tasks/handoffs/2026-09-15-multi-framework-screening-spec.md` from the
design brief; Saqlain approved Option B with Codex directly. Verified against the actual
code (not just read): 52/52 cluster coverage in the 9-question catalog is exact, the
governance/security splits match the real `domain_group` field, and the spec correctly
catches that `assessment.is_multi_framework` is false for ISO-only/NIST-only assessments
— routing must use `assessment.frameworks == ["dpdpa"]` instead. Full record: plan §9.5.

**Not implementing cluster screening yet** — the spec's own sequencing says to wait for
WS #5's spike + WS #7's contract first, to avoid building a throwaway Claude interface.
Next actual step in the build order is still WS #4.

- [x] Adversarially verify the screening spec's factual claims before treating it as settled.
- [ ] When WS #5 starts, build `ClusterScope`/`ClusterContext` to the shapes this spec already named.
