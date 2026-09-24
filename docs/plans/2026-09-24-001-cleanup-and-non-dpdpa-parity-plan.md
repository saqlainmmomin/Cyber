# Phase 5 Plan: Cleanup and Non-DPDPA Parity

**Status:** Planning. Per-task handoffs not written yet.
**Date:** 2026-09-24
**Builds on:** `docs/plans/2026-09-21-002-revised-implementation-plan.md`. That plan stays the source of truth for Phases 1-4, which are all complete (PRs #16-#37).
**Product contract:** `docs/product/2026-09-21-cyberassess-product-requirements.md`
**Decisions log:** `tasks/2026-09-21-adversarial-review.md` (D1-D11). This plan adds plan-level decisions D-P5-A to D-P5-F. It does not reopen D1-D11.
**Ownership rules:** `tasks/agent-ownership.md`
**Process model:** `tasks/handoffs/2026-09-24-phase-4-kickoff.md`
**Code baseline:** `main` at `377b211`. Every file:line reference below was read against this commit.

---

## Summary

Phases 1-4 built the multi-framework, engagement-level platform: Client → Engagement → Assessment, Evidence/Conclusion lifecycles, snapshots, AWS evidence, and retention. They built it around an original single-assessment core that only understood DPDPA. Where the old core and the new platform meet, the joins are incomplete. A consultant on an ISO 27001 or NIST CSF engagement, or on a mixed DPDPA + ISO assessment, gets a worse and sometimes misleading product. A few of the joins are also outright bugs, and none of them depend on the framework.

This plan scopes that work as **Phase 5**, with 8 tasks (P5-1 to P5-8). It rests on two things:

1. The 9 known gaps: 8 still open from `docs/architecture/data-flow-and-processes.md#known-gaps--inconsistencies`, plus the evidence-checklist gap found on 2026-09-24. Each one is judged below against the current product framing, not the 2026-09-08 demo framing.
2. A bounded audit of the same seam. It found **one unscheduled product-invariant violation** that matters more than any known gap: the "reader migration." Scores, the gap report, the PDF, the RFI and the release gate still read AI-proposed `GapItem`s rather than consultant-approved Conclusions. It also found **five correctness bugs** that no one was tracking.

---

## Why this plan exists

The 2026-09-08 plan (`tasks/multi-framework-demo-plan.md` §9.2) kept a list of open gaps. The 2026-09-21 clean-break pivot superseded that plan, and its list was dropped without being carried forward. Several of those gaps were fixed as side effects of Phase 1-4 work. The rest stayed open quietly. The architecture trace in `docs/architecture/` listed 11. A live check against current code confirms 8 are still open. Gaps #2, #3 and #10 in that doc were fixed by later phase work:

- Scope exclusion now reaches the UCC path through `compute_excluded_controls`, in `app/services/question_engine.py:64-67`.
- Cluster-first scoring no longer blocks the router.
- P3-4 retired legacy remediation.

The product framing also changed. The PRD describes a consultant-operated assessment workspace for paying boutique-GRC engagements. It has three **launch packs** (PR-010): DPDPA, ISO/IEC 27001:2022 and NIST CSF 2.0. GDPR, HIPAA and PCI-DSS are registered but disabled in the picker (`app/routers/web.py:60-61`). Under this framing, ISO and NIST parity is part of the v1 contract, not a nice-to-have. The PRD's own fourth demo persona is "a growing B2B SaaS company running a DPDPA + ISO 27001 + NIST CSF Assessment." That persona is exactly the case this plan fixes.

This plan also exists to stop a repeat of the silent loss. Every gap considered here is either scoped into a P5 task or listed under **Explicitly out of scope / deferred**, with its reason.

---

## Verdicts on the 9 known gaps

| # | Gap | Still open? | Verdict under current framing | Goes to |
|---|---|---|---|---|
| 1 | UCC/multi-framework path gets no desk-review pre-fill, screening pre-fill or tiering | Yes: `question_engine.py:182-184` routes every non-`["dpdpa"]` selection away; `_build_multi_framework_questionnaire` hard-codes `status="active"`, `tier="standard"` and null pre-fill (`:91-104`) | **Matters more. Reframed:** the machinery is missing on the multi path, and its input is DPDPA-only. Desk review itself is DPDPA-only (see A3), so on this path there are no ISO/NIST findings to pre-fill from. Fix the input first (P5-3), then the questionnaire (P5-4). This also hurts DPDPA users: any DPDPA + ISO assessment loses the DPDPA adaptive machinery as well. | P5-3 → P5-4 |
| 2 | Coverage-reinstatement loop targets dead code | Yes: `question_engine.py:264-274` un-skips only questions whose `skip_reason` is not the scope reason. The only producer of `"skipped"` is scope exclusion (`:217-221`). `_modulate_question` (`:370-443`), `_apply_screening` (`:446-492`) and `_modulate_industry_question` (`:505-595`) never return `"skipped"`. | **Still worth fixing, low stakes.** Delete it, along with the stale module docstring claim "Skip: strong document evidence → question skipped" (`:10`). P5-4 must not reintroduce a desk-review "skip" state: a document describes intent and is not an answer (auto_answer's own rationale). | P5-8 |
| 3 | Multi-requirement signal stored against only the first requirement | Yes: `desk_review.py:249` `requirement_id=req_ids[0] if req_ids else None`. `flag_type` is not stored either. The compensating mechanism is keyword matching on signal text in `question_engine.py:345-358`, and it feeds industry-question `deepen_if` only. | **Matters more than the doc says.** The loss is not cosmetic. `auto_answer.py:69-72` suppresses a document pre-fill only for requirements with a signal row, so a red flag spanning `CH2.NOTICE.1` and `CH2.CONSENT.1` still lets `CONSENT.1` be auto-pre-filled `fully_implemented`. That breaks auto_answer's own rule that signals always override pre-fill. The same truncation drops the flag from `_modulate_question` deepening (`:401-409`) and from the per-framework red-flag filter (`app/frameworks/prompts.py:280-283`). Fix it inside the desk-review generalization, because the schema is being touched there anyway. | P5-3 |
| 4 | `compute_scope()` accepts `company_size` but never reads it | Yes: `scope_profiler.py:45`. `_build_evidence_checklist(industry=…)` (`:128`) is also unused. | **Doesn't matter as a feature. Cleanup only.** No deterministic legal rule excludes DPDPA requirements by headcount. The s.17(3) startup exemptions depend on a Government notification, so they belong in a consultant's Not-applicable rationale (PR-042), not an automatic filter. Remove the dead parameters or document them as reserved. Do not invent size-based exclusion. | P5-8 |
| 5 | Only IT/SaaS has a bespoke industry bank | Yes: `app/dpdpa/industry_questions.py:284-295`. Everything except `it_services` maps to `generic`. | **Matters less. Reframed.** Industry banks are DPDPA-only and feed only the DPDPA-only path. Writing four more banks is consulting-content work, not engineering, and it ranks below ISO/NIST parity. The real defect is honesty: the 5 generic questions render under an "Industry-Specific" chapter heading (`question_engine.py:526,665`). Label them honestly now and defer new banks. | P5-8 (label); new banks deferred |
| 6 | One document upload bypasses the 80% completion gate | Yes: `app/routers/analysis.py:112-128`. | **Reframed: the bypass hides a real bug.** On the DPDPA path, `expected_question_ids` is all 41 base IDs, with scope exclusions ignored (`:99-102`). But scope-excluded questions can't be saved: the web save drops `status == "skipped"` questions (`web.py:1432`). A domestic, no-children, non-SDF client with processors can answer at most 30/41 (73%), so without a document it is **blocked from analysis**. That was verified by running `compute_scope`. The document bypass is what hides this. The gate also counts unconfirmed `answer_source="document"`/`"inferred"` rows as answered (`:103-107`). Fix the denominator. Then replace the silent bypass with an explicit, audited consultant override, because analysis is now only a proposal (PR-044). | P5-1 |
| 7 | RFI regeneration has no version history | Yes: `app/models/rfi.py:16` has `unique=True`, and `web.py:2322-2326` deletes before insert. | **Still matters (PR-054 names RFIs explicitly). Reframed.** The RFI is legacy-adjacent. It is sourced from AI `GapItem`s rather than approved Conclusions (`web.py:2276-2291`). Its download sits behind the full report release gate (`web.py:2354,2385`), which is backwards for a request that precedes conclusions. It does not connect to magic links, the actual collection channel. Versioning alone would preserve the wrong artifact. Rebuild it as a versioned snapshot sourced from approved Conclusions that can be issued as magic-link request items. | P5-6 |
| 8 | `reports.py` imports `app.dpdpa.framework` directly | Yes: `app/routers/reports.py:8`. | **Worse than a seam: a wrong value.** `/report/summary` returns `total_requirements=get_requirement_count()` (`:143`), which is always 41, including for an ISO-only (93-control) or NIST-only (94-control) assessment. `ROOT_CAUSE_CLUSTERS` is imported but unused. Fix the value with a per-framework count and drop the import. | P5-1 |
| 9 | Evidence checklist is DPDPA-only | Yes: `compute_scope_multi` builds a checklist only on its `fw_id == "dpdpa"` branch (`scope_profiler.py:297-303`). `_build_evidence_checklist` hard-codes DPDPA IDs (`:150-271`). | **Matters more.** An ISO- or NIST-only engagement gets an empty "Evidence Request" (`scope_complete.html:58`). The client-facing PDF/DOCX export also prints DPDPA-only flags, "Cross-border / Children's data / **SDF obligations** / Third-party processors … [N/A]", for an ISO engagement (`evidence_checklist_export.py:84-89,233-238`; `scope_complete.html:17-30`). That breaks CLAUDE.md's "framework-specific copy must be conditional" rule in a document the client receives. | P5-5 |

**Tally:** 8 scoped in (1, 2, 3, 4, 6, 7, 8, 9). Gap #5 is scoped in only as a labeling fix, and its substance (new banks) is deferred. None is dropped outright.

---

## Broader audit findings

These come from a bounded read of the seams between the old DPDPA core and the Phase 1-4 infrastructure. They are ordered by priority.

### A1. Reader migration was never scheduled. Scores, reports, the PDF and the release gate still read AI output. (Product invariant, highest priority)

- `app/services/scoring.py` has no reference to `Conclusion`. Per-framework scores are computed from raw LLM `assessments` at analysis time (`app/routers/analysis.py:290-293,594`) and frozen into `GapReport.framework_scores`.
- The release gate `require_review_approval` (`app/utils/review_gate.py:7-17`) checks `Assessment.review_status`. Only the legacy `approve_assessment` sets that field (`app/routers/review.py:107-142`). That route bulk-stamps every `GapItem`. P2-4's own handoff calls it "the bulk accept D3 forbids" (`tasks/handoffs/2026-09-23-p2-4-consultant-approval.md:55`).
- The effect is that a consultant can release a client PDF whose per-framework scores are 100% AI-proposed, without approving a single Conclusion. The P3-3 findings section shows only approved-Conclusion findings, but the score pages, gap cards and the RFI all come from `GapItem`.
- This contradicts PR-045 ("deterministic calculations … operate only on eligible consultant-approved Conclusions"), PR-052 ("exports use approved Conclusions only"), invariant 7, and D3.
- It is not an oversight in any one task. Every handoff from P2-3 through P3-4 deferred it by name to "the reader migration (P2-3 open question 1)". That covers P2-3:64, P2-4:307/427, P2-6:451, P3-1:428, P3-2:78/551 and P3-4:236. **No plan or tracker ever scheduled it.** The Phase 4 kickoff doesn't mention it.
- This is the single most important thing this audit surfaced.

### A2. A failed framework is reported as "0% Non-Compliant". (Correctness bug)

- `_persist_multi_framework_analysis` (`app/routers/analysis.py:575-580`) writes `compute_framework_scores([], fw_id)` for a framework whose LLM call failed. That returns `{'overall_score': 0.0, 'overall_rating': 'Non-Compliant'}` (verified). The code then sets `assessment.status = "completed"` (`:716`).
- `AnalysisRun` correctly records `failed` (`tests/test_analysis_pipeline.py:935-960`), but the report, the PDF and the integrated report read `GapReport`. They print a real-looking 0% score for a framework that was never analyzed.
- This breaks PR-041 ("incomplete Requirement coverage fails closed rather than yielding a misleading complete report").

### A3. Desk review and the multi path's evidence extraction are DPDPA-only whatever the framework selection. (Root cause of gap #1)

- `run_desk_review` always uses `app.dpdpa.prompts.build_desk_review_system_prompt()` (`app/services/desk_review.py:20,160`). The prompt is "…specializing in India's DPDPA" with the 41 DPDPA requirements (`app/dpdpa/prompts.py:213-246`). No route gates desk review by framework (`web.py:2477-2552`). The UI offers it whenever documents exist (`documents_tab.html:63-87`).
- On an ISO-only assessment it produces DPDPA findings. `persist_document_answers` then writes `QuestionnaireResponse` rows keyed by DPDPA requirement IDs (`auto_answer.py:124-132`) into an assessment that has no DPDPA questions. Screening does the same with `answer_source="inferred"` (`app/services/screening.py:164-210`). Screening is offered on every assessment, with copy promising "high-confidence controls are pre-filled in the questionnaire below" (`questionnaire_tab.html:37-72`), and that is false on the multi path.
- In the multi-framework analyzer, a completed desk review short-circuits evidence extraction (`app/services/claude_analyzer.py:303-312`). Otherwise the extraction prompt is also DPDPA-only ("For each DPDPA requirement below", `app/dpdpa/prompts.py:187`). The per-framework prompt then filters evidence to that framework's control IDs (`app/frameworks/prompts.py:303-315`). ISO and NIST therefore **never** get grounded extracted quotes. They silently fall back to raw document text, and on the extraction path the extraction call is wasted.

### A4. Unconfirmed pre-fills are sent to analysis as answers. On mixed assessments they are invisible to the consultant. (Contract violation)

- `auto_answer.py`'s docstring promises that document pre-fills are "never auto-submitted to analysis." But `trigger_analysis` loads every `QuestionnaireResponse` with no filter on `answer_source` (`analysis.py:49-63`) and counts them toward the completion gate (`:103-107`).
- On a DPDPA + ISO assessment the questionnaire is keyed by cluster ID, so DPDPA-keyed `document`/`inferred` rows never render. `_expand_cluster_responses` then passes raw DPDPA IDs straight into the DPDPA prompt (`app/frameworks/prompts.py:93-96`). They can sit beside a contradicting human cluster answer for the same control.
- The analysis therefore uses answers no human saw. This is a judgment call (exclude them, or label them "unconfirmed" in the prompt), so P5-1 owns the decision.

### A5. The report summary attributes non-DPDPA gaps to DPDPA penalties. (Correctness bug, client-visible)

- `_compute_business_impact` (`web.py:1795-1823`) falls through to `max_penalty = 50` for **any** gap whose ID matches no DPDPA prefix (`:1809-1810`). On a DPDPA + ISO assessment where DPDPA is clean but ISO has gaps, `report_summary.html:89-92,116-121` shows "Up to ₹50 Crore … under the DPDPA 2023 Schedule."
- The same block says "Repeat violations attract up to ₹500 Crore" (`report_summary.html:122`). That figure appears to come from the 2022 draft Bill, not the 2023 Act's Schedule. It needs verifying before any client sees it.

### A6. ISO and NIST scope questions promise effects they don't have. (Misleading UI)

- ISO scope help text says the cloud answer "activates cloud-specific controls (A.5.23)". The development answer "determines applicability of secure development lifecycle controls (A.8.25-A.8.34)". The premises answer "determines applicability of physical security controls" (`app/frameworks/definitions/iso27001.py:1012-1045`).
- The answers are stored (`web.py:986-1001`). But `compute_scope_multi` marks every non-DPDPA control applicable (`scope_profiler.py:304-310`), and `build_framework_user_prompt` never receives scope answers (`app/frameworks/prompts.py:208-320`). NIST's four scope questions (`nist_csf.py:1125-1170`) are equally inert.
- A consultant who answers "fully remote" still gets every A.7 physical control. The same finding surfaces under PR-012 (scope before analysis): for ISO/NIST, scoping is a form that does nothing.

### A7. Smaller DPDPA-copy leaks on non-DPDPA paths (fold into the owning tasks)

- The scope summary card shows the four DPDPA flags for every framework (`scope_complete.html:17-30`). That belongs in P5-5.
- The PDF "What Is Not Covered" boilerplate excludes "physical security review" and recommends a "certified privacy professional" for every framework (`pdf_export.py:1185-1192`). That is wrong for an ISO assessment that includes Annex A.7. The non-DPDPA methodology says requirements are "drawn directly from the source standard" (`:1245`), which is in tension with D4's reference-only ISO pack. PDF sections are additive-only, so these need conditional copy, not rewrites. That belongs in P5-2's PDF work.

### A8. Dead code found in passing (P5-8)

- `POST /assessments/{id}/context/submit` is an unused stub with an empty `form_data` (`web.py:1243-1259`).
- `rfi/docx` omits `framework_label` where `rfi/pdf` passes it (`web.py:2392-2399` vs `:2361-2369`).

### Checked and found sound (no action)

- **P4-2 evidence reuse vs non-DPDPA.** `map_evidence` validates `(framework_id, requirement_id)` against the registry for any selected framework (`app/services/evidence.py:585-596`). `reuse_candidates` filters by the target's own frameworks (`app/services/evidence_reuse.py:103-190`). Reuse works for ISO and NIST. Suggestions for ISO/NIST mappings are manual only, which is consistent with D8.
- **Evidence panel and analysis inputs.** `analysis_documents` includes engagement evidence only once it is mapped to the assessment (`evidence.py:875-911`). This is framework-neutral.
- **Main PDF body.** `generate_pdf` branches correctly on `dpdpa_only` (`pdf_export.py:672-683,1163-1250`) apart from the boilerplate in A7.
- **Magic links** are framework-neutral by design (free-text request items, `app/services/magic_links.py:146-211`). Their gap is PR-023 deduplication/mapping, which P5-5/P5-6 cover.
- **`tasks/todo.md`** has no open, TBD or "not yet implemented" items. Every task line is checked, and Phases 1-4 are marked complete.

---

## Plan-level decisions

These are scoping calls for the phase as a whole. Per-task decisions (`D-P5-1-A`, `D-P5-2-A`, …) with exact code and policy text belong in each task's handoff, not here.

- **D-P5-A. Parity target is the launch packs.** "Parity" means DPDPA, ISO 27001 and NIST CSF (PR-010, `ENABLED_ASSESSMENT_FRAMEWORKS`). All new logic must be registry-driven, so GDPR/HIPAA/PCI work later with content only and no code. Acceptance tests, however, cover only the three launch packs.
- **D-P5-B. The reader migration (A1) is in Phase 5 and is its most important task.** Parity work that polishes a questionnaire whose final numbers still come from unapproved AI output would be building on a violated invariant.
- **D-P5-C. Generalize the input before the questionnaire.** Adaptive machinery on the UCC path (P5-4) consumes framework-aware desk-review output (P5-3). No task may pre-fill ISO/NIST questions from DPDPA-keyed findings.
- **D-P5-D. Evidence requests stay suggestions, not routing (D8 holds).** Framework evidence-request lists and cross-framework deduplication by document type satisfy PR-023's "request once, map to many". They must not become automatic evidence-to-requirement mapping. A consultant still confirms every `EvidenceUse`.
- **D-P5-E. The RFI is rebuilt, not just versioned.** Adding version history to today's `GapItem`-sourced RFI is out of scope. The RFI becomes a versioned snapshot of a request derived from approved Conclusions (P5-6).
- **D-P5-F. Unconfirmed machine answers are never silent inputs.** Every task that touches responses must keep `document`/`inferred` rows either excluded from analysis and gates, or explicitly labeled as unconfirmed. P5-1 picks which one, and later tasks inherit it.

---

## Task breakdown

Each task gets its own Claude-written handoff before dispatch, following the Phase 4 kickoff model. Owners follow `tasks/agent-ownership.md`. Every task gets the standard `[AR]` adversarial review before merge.

### P5-1. Correctness bundle: analysis gate, fail-closed scores, wrong counts

**Goal:** fix the framework-independent bugs that currently produce wrong numbers or wrongly blocked or allowed analysis.
**Scope:**
- Make the DPDPA completion-gate denominator honor `applicable_requirements` (gap #6, `analysis.py:99-102`). Add a regression test for the 30/41 case.
- Replace the silent "≥1 document" bypass with an explicit consultant override, recorded as an `AuditEvent` with a reason. Decide whether it stays available at all (gap #6).
- Decide D-P5-F: exclude unconfirmed `document`/`inferred` rows from the gate numerator and from analysis input, or label them in both prompt builders (A4).
- Fail closed for a failed framework: store no score, surface "analysis failed for {framework}", and don't mark the assessment `completed` as if whole (A2). The fix must be one that P5-2 can carry forward.
- Return a per-framework requirement count from `/report/summary` and drop the dead import (gap #8, `reports.py:8,143`).
- Scope DPDPA penalty exposure to DPDPA gaps only, and verify or remove the ₹500 Crore claim (A5, `web.py:1801-1810`, `report_summary.html:122`).

**Owner:** Claude designs the gate and override policy and the fail-closed semantics (product invariants) → Codex implements.
**Depends on:** nothing. **Blocks:** P5-2 (shared lines in `analysis.py`, `reports.py` and the `web.py` report helpers).
**Files (expected):** `app/routers/analysis.py`, `app/routers/reports.py`, `app/routers/web.py` (report helpers), `app/templates/partials/report_summary.html`, and a new test module.

### P5-2. Reader migration: approved Conclusions drive scores, reports, the PDF and release

**Goal:** close A1. Deterministic scores come only from consultant-approved Conclusions (PR-045). The release gate requires individual Conclusion approval, not the legacy bulk stamp (D3, PR-052). The gap-report PDF and the report tab render from Conclusions.
**Scope (for the handoff to close, not decided here):**
- The scoring input contract from `Conclusion.outcome`, including the unresolved PRD open question 2: the `insufficient_evidence` denominator rule.
- What counts as "releasable": all applicable Conclusions approved? What about proposals that were never generated?
- The fate of `approve_assessment` / `disposition_item` / `GapItem` review. Retire them, or make them read-only views.
- How `GapReport` survives: frozen legacy history, or a thin cache.
- Snapshot manifest continuity (P3-2 already binds `conclusion_versions`).
- The legacy-data path for pre-P2-3 assessments.
- A7's conditional PDF boilerplate. Additive-only.
- Removing the gap-card and summary reliance on `GapItem`. The existing blended-score AST guard (`tests/test_no_blended_scoring.py`) must stay green.

**Owner:** Claude designs (foundational, and a product invariant) → Codex implements → Claude reviews. It needs **a second, more skeptical review pass**, as P2-3 and P4-4 had, because it changes what a client can be shown.
**Depends on:** P5-1. **Blocks:** P5-6.

### P5-3. Framework-aware desk review, evidence extraction and signal persistence

**Goal:** make document analysis produce findings keyed to the selected frameworks' own control IDs (the root cause of gap #1, per A3), and store signals losslessly (gap #3).
**Scope:**
- A registry-driven desk-review prompt, using each framework's controls and `red_flag_patterns`.
- A decision on one call vs. one per framework, under the existing token budgets in `app/config.py`.
- `DeskReviewFinding` gains `framework_id` and `flag_type`. A multi-requirement signal is stored so that every mapped requirement sees it (one row per requirement, or a JSON column). This needs an Alembic revision.
- Retire the keyword re-derivation in `question_engine.py:345-358` in favor of the stored `flag_type`.
- Registry-driven multi-path evidence extraction (`claude_analyzer.py:303-312`).
- Gate or scope screening so it never writes DPDPA-keyed rows into an assessment without DPDPA.
- Migrate or quarantine existing DPDPA-keyed `document`/`inferred` rows on non-DPDPA assessments.

**Owner:** Claude designs (LLM output contract, schema change, citation interplay with P2-2's `citations_json`) → Codex implements.
**Depends on:** P5-1 (D-P5-F). **Blocks:** P5-4.

### P5-4. Adaptive questionnaire on the UCC path

**Goal:** give cluster questions the same deepen, pre-fill and tier treatment the DPDPA-only path has (gap #1), from P5-3's framework-keyed findings.
**Scope:**
- The cluster status derivation rule. For example: any member control with an absence or signal deepens the question, and pre-fill happens only when every member control is adequate and has cited evidence. This is judgment work for the handoff.
- Where pre-fill rows are keyed, since the cluster questionnaire answers by cluster ID and `auto_answer` writes control IDs.
- `assign_tiers` on cluster questions.
- Whether screening applies to the DPDPA members of a mixed assessment, or is hidden outside DPDPA-only. Correct the screening copy either way (A3).
- The questionnaire stats block becomes real.

**Owner:** Claude designs the cluster-status rule → Codex implements.
**Depends on:** P5-3. **Coordinates with:** P5-8 (both touch `question_engine.py`, so P5-8 should land first).

### P5-5. Framework-aware scoping and evidence requests

**Goal:** give ISO and NIST engagements a real evidence request and scoping that does what it says (gap #9, A6, and the scope half of A7).
**Scope:**
- Curated per-framework evidence-request definitions: document type, label, reason, required/recommended, and `maps_to` control IDs. These live in the framework definitions (a `FrameworkDefinition` field), not in `scope_profiler`.
- `compute_scope_multi` merges requests across frameworks by document type, with the union of mappings (PR-023 "request once").
- Conditional scope flags in `scope_complete.html` and the checklist export.
- ISO/NIST scope answers either drive applicability *proposals* or have their help text corrected. An ISO exclusion is an SoA decision that needs a rationale, so the handoff must decide between "propose N/A with rationale" and "exclude."
- Optionally, a "create magic link from these items" action that pre-fills the existing free-text titles, with no change to magic-link security.

**Owner:** Claude owns the content and applicability design (consulting-domain judgment; D4 reference-only rule for ISO text) → Codex implements the plumbing and templates.
**Depends on:** nothing. It can run in parallel with P5-1 through P5-4. **Blocks:** P5-6.

### P5-6. RFI rebuilt as a versioned, Conclusion-sourced evidence request

**Goal:** close gap #7 as reframed (D-P5-E).
**Scope:**
- The RFI is generated from approved Conclusions and Findings (after P5-2) plus open evidence requests (P5-5).
- It is stored through `report_snapshots` as a new snapshot type, so regeneration creates versions and issued RFIs are immutable (PR-054). `rfi_documents` / `RFIDocument` retire or freeze.
- The download no longer sits behind the full report release gate.
- RFI items can be issued as magic-link request items with their requirement mappings, which makes PR-023's mappings visible.
- Decide whether this extends `magic_links.scope_json` (a security boundary) or stays a consultant-side template.

**Owner:** Claude designs (it touches the magic-link capability scope and snapshot immutability) → Codex implements.
**Depends on:** P5-2, P5-5.

### P5-7. (Reserved) ISO clauses 4-10 / SoA content pack

Deliberately not scheduled. See the deferred list. The number is reserved so that if Saqlain pulls this in, it keeps its place in ordering without renumbering.

### P5-8. Mechanical cleanup

**Goal:** remove the dead code and dishonest labels this audit found, before the larger tasks touch the same files.
**Scope:**
- Delete the dead reinstatement loop and the stale docstring (gap #2).
- Remove the unused `company_size` and `industry` parameters, or document them as reserved (gap #4).
- Relabel the generic industry bank so it isn't presented as "Industry-Specific" (gap #5).
- Delete the dead `/context/submit` stub.
- Pass `framework_label` to the RFI DOCX (A8).

**Owner:** Codex, standalone, from a short Claude handoff.
**Depends on:** nothing. Land it first.

### Sequencing

```
Lane 1:  P5-8 ─┐
               ├─ P5-1 ── P5-2 ──┐
Lane 2:        └─ (P5-1) ─ P5-3 ── P5-4
Lane 3:  P5-5 ───────────────────┴── P5-6
```

- P5-8 and P5-5 can start immediately.
- P5-1 gates P5-2 and P5-3, because D-P5-F must be decided before either touches responses.
- P5-2 and P5-3 share `analysis.py`. Run them in parallel only with a pre-declared coordination rule in both handoffs, as Phase 2 and 3 pairs did.
- P5-6 comes last.

---

## Process

Follow `tasks/handoffs/2026-09-24-phase-4-kickoff.md` without restating it here:

- Claude writes each task's handoff, grounded in exact current code, with numbered `D-P5-N-X` decisions and every fork closed.
- Claude spot-checks the handoff.
- Codex runs in an isolated worktree on `gpt-5.6-luna` at `xhigh`.
- Claude verifies the diff scope and re-runs the suite independently.
- Claude commits on Codex's behalf, with no attribution trailer, per that doc.
- An independent Sonnet adversarial review runs before the PR. P5-2 gets the extra skeptical pass.
- After each merge, update `tasks/todo.md`, `CLAUDE.md` and auto-memory.

Before dispatching P5-1, re-verify the suite baseline yourself rather than trusting a stated number.

---

## Explicitly out of scope / deferred

Each item is listed so it can't be lost the way the 2026-09-08 list was.

| Item | Why deferred | Revisit when |
|---|---|---|
| **ISO 27001 clauses 4-10, risk treatment, SoA** (PR-010). The registered ISO pack is Annex A only: 93 controls across `organizational/people/physical/technological` (verified from the registry). | This is content curation under D4's reference-only licensing rule, not engineering. It also needs consulting-domain authorship. **This is the highest-priority deferral:** an ISO-led paid engagement without the mandatory clauses is not credible. The number P5-7 is reserved for it. | Before any ISO-led pilot. |
| **New DPDPA industry banks** (fintech, healthcare, e-commerce; gap #5) | DPDPA-only path, consulting-content work, and it ranks below launch-pack parity. P5-8 fixes the labeling honesty. | When a pilot client in one of those industries is signed. |
| **Size-driven scope exclusion** (gap #4) | There is no deterministic legal basis. DPDPA s.17(3) exemptions depend on a notification and are a consultant N/A rationale. | If the Government notifies startup exemptions. |
| **Screening for ISO/NIST** (new domain-screening banks) | A new LLM screening design per framework. P5-4 only makes screening honest about where it applies. | After P5-4 ships and pilot feedback shows questionnaire length hurts. |
| **Assessment period and evidence cut-off** (PR-012, PR-053) | Not modeled on `Assessment`. Every integrated report prints "not recorded" (`app/services/report_content.py:40`, `pdf_export.py:1365`). This is scoping-flow and schema work outside the non-DPDPA seam. | Next plan, alongside PR-026. It is pilot-relevant. |
| **Evidence change impact / re-review** (PR-026), persisted reuse dismissal (P4-2 OQ1), a UI to create a validation assessment (P4-2 OQ3) | Separate evidence-lifecycle feature work, already handed forward by P4-2. | Next plan. |
| **Legal hold, per-engagement retention override, audit-metadata scrubbing, backup rotation** (P4-4 OQ1-5) | Retention policy extensions, not parity. | Before the first real purge. |
| **App-wide CSRF / CORS.** `allow_origins=["*"]` with `allow_credentials=True` and no auth (`app/main.py:121-124`); P4-1 OQ6 | A security track, not a parity task. It matters once the app is reachable beyond localhost, because magic links already imply an external surface. | **Before any network-exposed pilot.** Recommend its own Claude-owned security task. |
| **Automatic AWS-evidence mapping to ISO/NIST controls** (P4-1 OQ4) | D8: evidence mapping is consultant-driven. | If frameworks 4-6 go live (D8's own revisit trigger). |
| **GDPR / HIPAA / PCI-DSS acceptance** | Roadmap packs, disabled in the picker. D-P5-A keeps the P5 code registry-generic so they need content only. | When a roadmap pack is promoted to launch. |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| P5-2 changes client-visible numbers for existing assessments | High | High | The handoff defines legacy behavior explicitly. Issued snapshots are immutable (P3-2), so past deliverables don't change. Extra review pass. |
| Framework-aware desk review blows the token budget on 3-framework assessments | Medium | Medium | P5-3 decides between one call and one per framework against `max_total_document_words`. The per-framework failure isolation already exists in the analyzer and is the model. |
| The ISO applicability design (P5-5) drifts into reproducing standard text | Low | High | D4. The handoff restricts ISO content to references and guidance. |
| P5-2 and P5-3 conflict in `analysis.py` | Medium | Low | Pre-declared coordination rule, or run them in sequence. |
