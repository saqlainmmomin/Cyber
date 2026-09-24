# P5-9 Plan: End-to-end validation with blind synthetic companies

**Status:** Planned. Handoffs written: authoring brief (Stage A) and harness build (Stage B, P5-9a). The adjudication handoff (P5-9b) is written after P5-2 merges.
**Date:** 2026-09-24
**Parent plan:** `docs/plans/2026-09-24-001-cleanup-and-non-dpdpa-parity-plan.md` (Phase 5). This adds task P5-9 to that phase. It doesn't reopen any P5 decision.
**Product contract:** `docs/product/2026-09-21-cyberassess-product-requirements.md`
**Decisions log:** `tasks/2026-09-21-adversarial-review.md` (D1-D11), plus D-P5-A to D-P5-F. This plan adds D-P5-9-A to D-P5-9-J.
**Code baseline:** `main` at `d69aa71` (P5-3 merged).
**Handoffs:**
- Stage A, company authoring (Gemini): `tasks/handoffs/2026-09-24-p5-9-authoring-brief.md`
- Stage B, harness build (Codex): `tasks/handoffs/2026-09-24-p5-9a-validation-harness.md`
- Stage D, adjudication and report invariants (Codex): P5-9b. Not yet written, because it depends on P5-2's shipped routes.

---

## Summary

Every task so far has been verified with unit, contract and ASGI smoke tests, and the LLM is mocked in all of them. Nobody has run the whole product on realistic, adversarial client material and measured whether it reaches the right conclusions. That covers intake, scoping, evidence, desk review, the adaptive questionnaire, analysis, Conclusions, review and the report.

P5-9 does that. It builds **four fictional client companies** at different maturity levels. Each has a hidden answer key of planted gaps, decoys (things that look like gaps but aren't) and genuinely clean controls, plus the evidence and answers a real client would hand over. Each company goes through the real HTTP routes with the live LLM tiers. A deterministic scorer then measures what the tool found against what was planted.

The output is a measured baseline: detection rate per gap class, false-positive rate, grounding, run-to-run stability and cost. It also produces a list of product defects found in the process, and a screenshot set and friction log that become the brief for the UI redesign.

## Why now, and why not the UI first

- Phase 5 changes where the numbers come from. P5-2 moves scores and reports onto approved Conclusions. P5-4 gives the cluster path adaptive treatment. A validation run before those land measures code that's about to be replaced. **Building** the harness and authoring the companies doesn't depend on them, so that work starts now. **Running** it for the baseline waits for P5-2 and P5-4 (D-P5-9-H).
- The UI redesign waits for the validation run. P5-4 and P5-6 rebuild the questionnaire and RFI surfaces. A redesign now would conflict with them and would be done without evidence. The run produces screenshots of every page at every stage for four realistic companies, plus a friction log. That's the redesign brief.

## The company matrix (D-P5-9-A)

Only the launch packs are used. GDPR, HIPAA and PCI-DSS are disabled in the picker (`ENABLED_ASSESSMENT_FRAMEWORKS`, `app/routers/web.py:60`), and D-P5-A limits acceptance to DPDPA, ISO 27001 and NIST CSF.

| # | Working name | Maturity | Frameworks | Path it exercises | Gaps | Decoys | Clean controls | Artifacts |
|---|---|---|---|---|---|---|---|---|
| C1 | Indian consumer startup, ~40 staff, handles children's data | Low | DPDPA | Legacy DPDPA path, screening, adaptive tiering, scope exclusion, completion gate | 10-14, mostly depth 1-3 | 2 | ≥ 6 | 5-7 |
| C2 | Indian B2B SaaS, ~250 staff, pursuing ISO certification | Medium | DPDPA + ISO 27001 | Mixed cluster (UCC) path, P5-4 adaptive treatment, cross-framework dedup, evidence requests | 12-16, depth 2-4 | 3 | ≥ 8 | 9-12 |
| C3 | "Certified fortress, paper moat": ISO-certified Indian enterprise, DPDPA on paper only | High on paper | DPDPA + ISO 27001 + NIST CSF | Three-framework clusters and cross-framework divergence. It takes over the unexecuted v3 spec. | 12-16, depth 3-5 | 4 | ≥ 10 | 10-15 |
| C4 | US-headquartered health-data SaaS with an Indian engineering centre | Medium-high, security-native | NIST CSF | Non-DPDPA-only path, security artifact evidence, no DPDPA copy leaking into outputs | 10-14, depth 2-4 | 3 | ≥ 8 | 10-14 |

C3 absorbs `tasks/handoffs/2026-07-10-v3-adversarial-seed-company.md`, which was never executed (it has no `## Results`, and `scripts/test_ground_truth.json` still holds only the three v2 companies). That spec's gap classes and decoy rules carry over into the authoring brief. A C2 longitudinal re-assessment (year two, evidence reuse, remediation closure) is deferred to P5-9b.

## Plan-level decisions

- **D-P5-9-A. Launch packs only, four companies, per the matrix above.** Every company must include at least one DPDPA-free or DPDPA-mixed path. Between them, the four cover every enabled framework combination class: DPDPA only, mixed, three-way and non-DPDPA.
- **D-P5-9-B. The answer key is written first, and the tool never sees it.** The truth sheet, planted gaps, decoys and clean controls are written before any evidence. The evidence is then built to hide them. The answer key lives in files the runner **never opens**. Only the scorer reads it. The runner uploads only what's under `client_visible/`. A leak lint fails the pack if client-visible text contains answer-key vocabulary, gap ids, or any 8-word run copied from an answer-key description.
- **D-P5-9-C. Held-out set.** The answer keys are a held-out evaluation set. No task that changes prompts, the analyzer or the desk review may read `validation/companies/*/answer_key.json` or tune against a specific planted gap. Tuning against the set turns it into a training set and makes the numbers meaningless. If prompt work needs examples, author a separate dev company.
- **D-P5-9-D. Gap-carrying evidence is rendered deterministically, not image-generated.** Every artifact that carries a planted gap, a decoy or a key fact is written as structured data: prose sections, table rows, config lines or console lines. It's rendered by code (python-docx, fpdf2, Pillow; no new app dependencies), so the discrepancy in the file is exactly the one in the spec. Image models garble dense text like rule tables, user lists and dates. That would contaminate the answer key with unplanned errors. Image generation is allowed only for **realism-only** artifacts (a photographed whiteboard, a letterhead scan) that carry no gap, decoy or key fact. The lint enforces this. OCR robustness is tested with deterministic degradation (skew, noise, JPEG quality) of rendered images, not with image-model output.
- **D-P5-9-E. Real routes, live LLM, isolated database.** The runner drives the app in-process through `fastapi.testclient.TestClient` and the real HTTP routes. It follows the P4-2 pattern in `scripts/seed_test_companies.py`, with the LLM **not** mocked. Each run gets its own SQLite file and upload directory, set through `DATABASE_URL` / `UPLOAD_DIR` before the app is imported, so the working database is never touched. The runner never calls a service function to *write*. It may call read-only services, for example `build_adaptive_questionnaire`, to learn which questions are rendered.
- **D-P5-9-F. Authoring and assessing use different model families.** The tool's text tiers are `deepseek/deepseek-v4-flash` and its vision tier is `anthropic/claude-sonnet-4` (`app/config.py:41-44`). Companies are authored with Gemini. A different model (Codex or Claude) runs the fairness audit of each pack. The same model shouldn't write the puzzle and grade its own solution.
- **D-P5-9-G. Precision counts as much as recall.** Headline metrics are reported in pairs: planted-gap detection alongside false-positive rate on decoys and clean controls. A tool that flags everything isn't useful to a consultant, so neither number is reported without the other.
- **D-P5-9-H. The build starts now, the baseline run waits.** Stages A and B start immediately. The **baseline** run (Stage C) happens once P5-2 and P5-4 are on `main`. Earlier runs are allowed as smoke runs and are labeled as such in their summary. Their numbers are not the baseline.
- **D-P5-9-I. The harness is not a gate, and it never changes app code.** P5-9a adds scripts, fixtures, docs and tests only. Defects the run finds become new tasks in `tasks/todo.md`. They are not fixed inside P5-9. Unsupported evidence formats are measured by probes and not fixed here (see Known product findings).
- **D-P5-9-J. Stochastic runs are repeated.** Stage C runs each company **3 times** from scratch (fresh database). The scorer reports per-gap catch counts out of 3, per-requirement outcome agreement, and the list of requirements whose outcome changed between runs. A gap is "reliably caught" only if it's caught 3 out of 3 times.

## Stages

```
Stage A  authoring (Gemini)   intake pack → answer key → evidence specs → answers → fairness audit (Codex/Claude)
Stage B  harness (Codex, P5-9a)  schemas, question-pack export, renderer, lint, runner, scorer, report   ← can start now, parallel to A
Stage C  baseline run            4 companies × 3 runs, live LLM                                             ← after P5-2 + P5-4 merge
Stage D  adjudication (P5-9b)    consultant oracle approves/edits Conclusions → release → snapshot → PDF invariants, oracle-score check, screenshots
Stage E  triage                  results doc, new todo entries per defect, redesign brief from the friction log
```

Stage A has one dependency on Stage B. The authoring model answers questionnaire questions **by the tool's own question ids**, so it needs the question-pack export from P5-9a Part 1. The brief is split to fit this. The answer key and evidence can be authored before the export exists. The questionnaire answers are authored after it.

## Metrics (deterministic; the P5-9a scorer)

Per company, per run, then aggregated across runs:

| Metric | Definition |
|---|---|
| Gap catch rate | Share of planted gaps where at least one listed requirement's Conclusion scores ≥ 0.7 against its true status (outcome distance table in the P5-9a handoff). Also broken down by `gap_class` and by `probing_depth`. |
| Gap score | Mean outcome-distance score over each gap's listed requirements |
| Decoy false-positive rate | Share of decoys where any listed requirement is proposed `non_compliant` or `partially_compliant` |
| Clean-control false-positive rate | Same, over `clean_controls` |
| Grounding | For caught requirements, the share whose Conclusion citations point to an artifact named in that gap's evidence trail |
| Key-fact recall | Share of a gap's `key_facts` that appear in the Conclusion's rationale, gaps or evidence summary text |
| Severity agreement | `risk_level` against `severity_expected`: exact match 1, adjacent 0.5 |
| Coverage | Applicable requirements with a Conclusion, and frameworks that failed |
| Stability | Per-requirement modal agreement across runs; gaps caught k/3 |
| Cost and time | LLM calls, tokens by tier and model, and wall time per stage, from a passive tap on `app.services.llm_client.call_llm` |
| Background agreement | Agreement on all other applicable requirements against the truth sheet's defaults. Reported, not a headline number, because defaults are lower-confidence truth. |

P5-9b adds an **oracle-score check**. The consultant oracle edits every Conclusion to its true outcome, and then the released per-framework scores must equal the deterministic score of the truth sheet exactly. That's a direct end-to-end test of P5-2's reader migration.

## Known product findings the plan already expects

These come from reading code for this plan. The run confirms them and they get filed as tasks. P5-9 doesn't fix them.

1. **Evidence formats.** Upload accepts PDF, DOCX, PNG, JPG and WEBP. `detect_file_type` never returns `txt`, although `FILE_TYPE_TO_MIME` lists it (`app/services/document_processor.py:222-231`, `app/services/evidence.py:35-43`). Real security evidence often comes as `.xlsx`/`.csv` (access reviews, asset registers) and `.txt`/`.conf` (firewall and router configs). The runner probes each format and records the rejection.
2. **Document categories are DPDPA-shaped.** `DocumentCategory` (`app/schemas/assessment.py:27-36`) has no category for security-native evidence (configs, access reviews, scan reports), so these all land in `other`.
3. **Follow-up answers.** The follow-up route generates questions (`app/routers/web.py:1524`). The runner records the questions but doesn't answer them in P5-9a. Whether follow-up answers reach analysis is checked and reported.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Planted gaps are unfair: not discoverable, or a matter of opinion | Medium | High | The answer key comes first (D-P5-9-B). Structural lint requires every key fact to appear verbatim in client-visible material. A second model runs an independent fairness audit. |
| The answer key leaks into client material through filenames, titles or phrasing | Medium | High | Leak lint on all rendered text, answers and filenames. Filenames are reviewed in the fairness audit. |
| Overfitting: later prompt work tunes against the set | Medium | High | D-P5-9-C. The rule is stated in `validation/README.md` and in `CLAUDE.md`'s gotchas. |
| Live runs are slow or costly | Low | Medium | Cheap tiers. `--stop-after` stages. Per-stage cost is reported so a regression shows up. |
| Adaptive questions change between authoring and runtime (P5-4) | High | Low | The runner answers rendered questions by id. It records sheet ids that weren't rendered and rendered ids that had no answer. Re-export and top up the answers when that list isn't empty. |
| C3's three-framework assessment exceeds the desk-review token budget | Medium | Medium | The per-framework failure isolation from P5-3 already exists. The runner records failed frameworks as a finding. |

## Explicitly out of scope / deferred

| Item | Why | Revisit when |
|---|---|---|
| Fixing any defect the run finds | D-P5-9-I | Filed as tasks in Stage E |
| LLM-judge semantic scoring of rationales | Deterministic metrics first. A judge model adds its own noise. | If key-fact recall proves too blunt |
| GDPR, HIPAA and PCI companies | Disabled packs (D-P5-A) | When a roadmap pack is promoted |
| Answering follow-up questions with a persona model | Nondeterministic and needs its own blinding design | After P5-9a reports whether follow-up answers reach analysis |
| C2 year-two longitudinal run | Needs P5-2's approval flow | P5-9b |
| UI redesign | Waits for the Stage C/D screenshots and friction log | After Stage E |
