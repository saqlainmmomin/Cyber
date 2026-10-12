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

## Codex review 2

**GO with changes:** the narrower design is viable, but the required changes below must be incorporated before implementation of the affected stages.

Reviewed revision 3 of `tasks/handoffs/2026-10-10-document-budget-design.md:54-242`. References to “plan” below mean that file. Resolved means resolved in the design, not implemented. Deferred work stays deferred under `plan:70` and `:195-203`.

### F1 to F29

| Finding | Status | Reason and evidence |
|---|---|---|
| F1 | Resolved | Every run judges every control. This removes the partial-report replacement problem. `plan:60`, `:80`. |
| F2 | Resolved | Stale-only scheduling is removed. All controls, including those without passages, are judged. Incomplete-read execution is a separate remaining problem, N5. `plan:80`, `:180-185`. |
| F3 | Resolved | No new stale state is cleared. Existing locks and conclusion version checks remain. `plan:80`, `:187`; `app/services/analysis_pipeline.py:405-419`. |
| F4 | Resolved | Release policy is explicitly deferred. The existing release manifest still depends on conclusion versions rather than evidence generations. That is an accepted limitation, not a new requirement. `plan:81`, `:201`; `app/services/approved_report.py:374-403`. |
| F5 | Partly resolved | All paths in the first review, startup and backfill are named. Shared read ownership still needs N4. `plan:82`, `:153`; `app/services/evidence.py:847-852`. |
| F6 | Partly resolved | Exit paths and historical retention are covered. One assessment must not deactivate another assessment's shared read. Obsolete-framework mappings still confer document scope today. `plan:153`, `:158`; `app/services/evidence.py:643-662`, `:847-852`. |
| F7 | Resolved | Legacy migration precedes reads. Skipped rows are disclosed. Current analysis still includes unmigrated documents. `plan:83`, `:155`; `app/services/evidence.py:903-913`. |
| F8 | Partly resolved | Extraction status and marker-only OCR failure are covered. Empty-text uploads are rejected and rolled back, so no version remains to display a failure status. State that the explicit upload error accounts for that outcome. `plan:84`, `:154`; `app/services/evidence.py:703-715`, `:762-774`. |
| F9 | Partly resolved | Single-framework calls and full fingerprints fix combined-call reuse. Framework-free reader identity and immutable re-read generations remain unspecified. `plan:152`, `:165-166`, `:187`. |
| F10 | Resolved | Part-local matching, offsets, duplicate-occurrence behavior, context rejection and the citation length limit are explicit. `plan:167`; `app/services/citations.py:100-111`, `:262-275`. |
| F11 | Resolved | Exact sent passages are recorded and constrain judge citation resolution. This must replace today's all-source search at persistence. `plan:135`, `:182-184`; `app/services/analysis_pipeline.py:376-377`. |
| F12 | Partly resolved | Dispatcher, claims, short sessions and restart recovery are specified. Provider-send limits and abandoned-thread accounting need clarification. `plan:162`; `app/services/llm_client.py:296-314`, `:349-373`. |
| F13 | Resolved | Reads are purged before versions. Archive pauses scope and publication checks scope. Include assessment and engagement archive state in that check. The active-version query alone does not do so. `plan:156`, `:162`; `app/services/evidence.py:843-865`; `app/services/retention.py:599-625`. |
| F14 | Resolved | Consultant-triggered desk review retains stored status, fields and completion times. No live-summary migration is required. `plan:175-178`; `app/models/desk_review.py:20-26`; `app/services/desk_review_findings.py:80-89`. |
| F15 | Resolved | Pre-fill retraction changes are explicitly deferred. `plan:70`, `:198`. |
| F16 | Resolved | Coverage judgment remains separate from passage extraction. Existing coverage and grounding requirements remain. Incomplete reads still need N5. `plan:177-178`; `app/services/question_engine.py:223-244`. |
| F17 | Resolved | Existing finding shapes, severity, flag vocabulary and grouping remain. The new reader gets an injection test. `plan:169`, `:177-178`; `app/services/desk_review.py:438-455`, `:657-686`. |
| F18 | Resolved | RFI-status absence is explicitly deferred until S4. `plan:200`. |
| F19 | Resolved | Extraction selection and judge passages have separate manifests. Quotes outside the cut are labelled. `plan:135-138`, `:182-184`. |
| F20 | Partly resolved | Whole-control runs remove targeted completeness concerns. The claimed all-empty behavior and equal-input small-framework wording need N6. `plan:90`, `:183-185`; `app/frameworks/prompts.py:599-626`. |
| F21 | Partly resolved | Setting-off goldens and a separate setting-on fixture give a sound intermediate boundary. Curated adapters are feasible. Final retirement still conflicts with retaining an off path. `plan:186`, `:193`, `:239`; `app/services/claude_analyzer.py:89-106`; N8. |
| F22 | Partly resolved | Settlement, identity, cache isolation and accounting are prerequisites. Failed-read policy and broader framework coverage remain. `plan:191-192`; N5 and N9. |
| F23 | Partly resolved | Disabling reads works in intermediate stages. Saved-read fixtures or stubs become mandatory before legacy machinery is deleted. `plan:157`, `:193`; `scripts/demo/seed_demo.py:1253-1264`; N8. |
| F24 | Resolved | Reports keep approved findings and accepted narrative inputs. Reads do not become report inputs directly. `plan:94`; `app/services/narrative.py:50-68`, `:173-174`. |
| F25 | Partly resolved | Storage and reader execution are separated. Stages 3 to 5 share one default-off setting. Stage 2 and stage 5 still need smaller review boundaries. Sequence approval remains open. `plan:132`, `:140-188`, `:240`; stage assessment below. |
| F26 | Resolved | Both corrected behavior claims are recorded accurately. `plan:100-102`; `app/services/claude_analyzer.py:324-328`, `:426-442`; `app/services/document_categories.py:31-46`. |
| F27 | Resolved | Independent settings, strict bounds, preceding headings and unknown metadata are specified. The current tail merger must be changed or bypassed to satisfy that contract. `plan:163-170`; `app/services/grounding/chunking.py:73-77`, `:120-123`. |
| F28 | Partly resolved | Limits and omitted-passage manifests are pinned. Per-control and per-batch budgets do not agree. The output allowance is not today's ceiling. `plan:181-182`, `:209-214`; `app/config.py:60-65`; N7. |
| F29 | Resolved | Service times and OCR exclusions are labelled assumptions. End-to-end measurements remain a gate. The one-file and combined-call estimates need the minor arithmetic corrections below. `plan:222`, `:231-234`, `:242`. |

### New findings and remaining design corrections

| ID | Severity | What is wrong or missing | Evidence | Concrete change |
|---|---|---|---|---|
| N1 | major | Extending a historical migration helper does not migrate a database already at head. Seeds can recreate null frameworks after backfill. | `plan:142-143`; `app/legacy_migrations.py:1-8`, `:236-244`; `alembic/versions/6fcd9e575309_retrofit_legacy_columns_fks_and_.py:25-35`, `:58`; `scripts/seed_test_companies.py:1286-1296`, `:1348-1357`. | Add a new Alembic revision. Backfill and validate assessment selections, gap-item frameworks and desk-finding frameworks. Make all seed and test writers explicit before removing readers. Do not change historical revisions to perform the new migration. |
| N2 | major | The initiative candidate identifies the wrong function as shared. Replacing it risks retained DPDPA behavior while missing the actual shared privacy wording. | `plan:124`, `:145`, `:238`; curated call `app/routers/analysis.py:494`; shared call `:808`; `app/services/scoring.py:733-756`, `:567-589`. | Keep curated grouping, prefix fallback and naming. Fix the shared initiative approach text. Retain legitimate privacy actions for DPDPA members of mixed initiatives. Remove the unnecessary new grouping-map decision. |
| N3 | major | The inventory misses shared context profiling and follow-ups. Fixing their DPDPA wording contradicts stage 2's “no prompt change” restriction. | `plan:140-146`; `app/services/context_profiler.py:57-60`, `:157-184`; shared callers `app/routers/questionnaire.py:84-88`, `app/routers/web.py:2534-2538`; `app/services/followup_engine.py:98`, `:188`; shared caller `app/routers/web.py:2825-2834`. | Add framework-aware context and follow-up branches. Preserve existing DPDPA requests and stored context IDs. Permit narrowly scoped non-DPDPA prompt changes. Keep the judge freeze. |
| N4 | major | Shared read identity is mixed with assessment-local inactivity. Unmapping or archiving one assessment can deactivate a read still needed by another. | `plan:152-153`, `:156`; `app/services/evidence.py:643-662`, `:847-852`. | Keep shared read results separate from assessment membership, or compute activity across all remaining scopes. Test two assessments sharing one version, then unmap, remove a framework and archive only one assessment. |
| N5 | major | Listing queued or failed reads does not define whether desk review or analysis can run. Reader failure is not automatically a desk-review framework error. Partial inputs could receive adequate coverage and then pre-fill. | `plan:175`, `:180-188`; `app/services/desk_review_findings.py:146-163`; `app/services/question_engine.py:223-244`. | Define readiness for queued, reading, failed and unreadable parts. The simplest initial contract waits for required reads and refuses incomplete framework execution with visible errors. If partial execution is allowed, snapshot its missing inputs and preserve failed-framework pre-fill suppression. This does not require new strength or retraction rules. |
| N6 | major | The existing no-quotes line does not cover an entirely empty framework. Forced small-framework batching also changes existing judge wording. | `plan:90`, `:183-185`; `app/frameworks/prompts.py:599-626`, `:718-726`; curated equivalent `app/dpdpa/prompts.py:548-563`. | Add an explicit saved-evidence empty state. Distinguish no relevant passages from no uploaded files. Preserve existing full-framework wording for a full-control unit, or record a narrow wording exception. Test empty and nonempty inputs for every framework. Preserve all unchanged request fingerprints. |
| N7 | major | A 2,500-token allowance per control can yield 62,500 passage tokens for 25 controls, or 135,000 for a 54-control framework. This does not fit the advertised 12k input. The 3k judge output is not today's limit. | `plan:181`, `:211-214`; `app/config.py:58-65`; `app/frameworks/batching.py:108-114`; `app/frameworks/prompts.py:391-408`; `app/services/claude_analyzer.py:570`, `:640`. | Define total request bounds including controls, answers, catalog and instructions. State whether per-control limits are maxima or expected averages. Keep existing judge output ceilings until measured. Test extraction length termination as failure, not successful empty evidence. Revise call counts and costs if smaller batches are required. |
| N8 | major | Default-on and legacy deletion are different rollout steps. Stage 6 deletes paths still required by setting-off goldens and the allowed setting-off seed strategy. | `plan:157`, `:186`, `:193`, `:239`; `tests/support/analyzer_mock.py:23-31`, `:61-69`; `scripts/demo/seed_demo.py:1262-1264`. | Flip the default after the gate while retaining rollback. Retire the setting and off branches in a distinct change only after every endpoint and loader uses saved reads. Require offline fixtures or stubs before retirement. Preserve the old golden suite while off mode exists. |
| N9 | minor | Aggregate A/B is fair for matched runs but insufficient for stage 2's whole-framework claim. Current companies cover DPDPA, ISO and NIST only. Follow-ups default off. | `plan:148`, `:192`; `validation/companies/c1-app-startup/company.json:8-10`, `c2-b2b-saas/company.json:8-11`, `c3-certified-fortress/company.json:8-12`, `c4-healthsaas/company.json:8-10`, `c0-example/company.json:6-8`; `scripts/validation/run_company.py:614-615`, `:637`; `scripts/validation/ab_compare.py:377-418`. | Keep the aggregate gate. Add offline all-six-framework checks for creation, categories, context, follow-ups and initiative copy. Check per-framework regressions in the aggregate-only outputs. Do not let gains in one framework hide losses in another. |
| N10 | minor | Keeping catalog fields unchanged does not make filename joins safe for saved version data. Two same-named files can share the wrong summary or coverage. | `plan:176-178`; `app/services/desk_review.py:570-591`; `app/services/evidence_viewer.py:116-121`. | Retain version identity in the deterministic catalog and use it when available. Keep filename matching for old summaries. Add a duplicate-name catalog/viewer case alongside stage 1's manifest test. |

### Stage-2 inventory

“Fix” means shared code with a DPDPA assumption. “Keep” means used by DPDPA assessments or already conditional. Do not delete an import merely because its module serves several frameworks.

| Item | Classification | What changes and what could break |
|---|---|---|
| Curated single-framework analysis and persistence | Keep | Preserve the explicit DPDPA route and request path. Removing it changes retained assessment behavior. `app/routers/analysis.py:263-299`; `app/services/claude_analyzer.py:43-75`, `:78-135`. |
| Curated desk-review and extraction prompts | Keep | Preserve conditional dispatch. Stage 5 changes the input adapter, not stage 2. `app/services/desk_review.py:369-374`; `app/services/claude_analyzer.py:263-269`; `app/frameworks/prompts.py:192-195`. |
| DPDPA questionnaire, pre-fill and screening | Keep | Existing framework gates are correct. `app/services/question_engine.py:85-87`, `:402-404`; `app/services/auto_answer.py:63-65`; `app/services/screening.py:46-50`. |
| DPDPA definitions, goldens and conditional readiness copy | Keep | Preserve content and recordings. The readiness copy is conditional already. `app/frameworks/definitions/dpdpa.py:8-15`; `tests/test_golden_dpdpa.py:92-124`; `app/templates/partials/report_summary.html:73`, `:115`. |
| Gap-analysis category truncator | Fix, stage 1 | Shared selection ranks privacy categories first. The curated path also calls this helper, so preserve or deliberately characterize its request ordering. `app/services/claude_analyzer.py:89`, `:419-445`; `plan:113`, `:134-138`. |
| Upload categories | Fix | Stop prepending legacy categories to every framework. Keep historical stored category strings valid and keep the DPDPA choices when selected. `app/services/document_categories.py:31-46`; `app/schemas/assessment.py:27-36`. |
| `Assessment.frameworks` | Fix after N1 | Remove missing/invalid defaults only after data and writers are explicit. The model still permits null writes. `app/models/assessment.py:53-74`. |
| Framework compatibility helper defaults | Fix or designate legacy-only | Require an explicit framework for shared use. Preserve intentional compatibility callers. `app/frameworks/compat.py:13-42`. |
| Questionnaire framework reader | Fix | Use the validated assessment selection. A silent default can route an invalid assessment into the wrong questionnaire. `app/routers/questionnaire.py:320-327`. |
| Both analysis framework readers | Fix | Remove fallback parsing, retain the explicit DPDPA dispatch that follows. `app/routers/analysis.py:141-148`, `:256-279`. |
| Assessment framework metadata reader | Fix | Use the actual list rather than silently reporting DPDPA. `app/routers/assessments.py:144-149`. |
| PDF framework default | Fix | Require real scope or derive it from the supplied assessment. Explicit DPDPA callers remain valid. `app/utils/pdf_export.py:940-954`; `tests/test_golden_dpdpa.py:72-78`. |
| Desk-finding null reader and query | Fix after N1 | Remove both null-to-DPDPA conversion and the query's null inclusion. Backfill first or findings disappear. `app/services/desk_review_findings.py:28-45`; `app/models/desk_review.py:45`. |
| Cross-cutting signal prompt fallback | Fix after N1 | Supply explicit finding frameworks. Otherwise framework-wide flags can be assigned incorrectly. `app/frameworks/prompts.py:539-542`. |
| Gap/remediation readers and links | Fix after N1 | Fix report lookup keys, penalty attribution, PDF matching and workpaper anchors together. `app/routers/web.py:3126`, `:3274`; `app/utils/pdf_export.py:651`, `:726`; `app/templates/partials/report_summary.html:23`, `:158`. |
| Conclusion-review legacy lookup, missed by plan | Fix after N1 | Remove its null fallback too or the central card lookup still assumes DPDPA. `app/services/conclusion_review.py:420-427`. |
| Curated initiative grouping and prefix parsing | Keep | This function serves the curated DPDPA route. Its unknown-prefix fallback is `process`, not no grouping. `app/routers/analysis.py:494`; `app/services/scoring.py:465-496`, `:527-561`. |
| Shared initiative approach text, missed by plan | Fix | ISO/NIST already get neutral root groups and titles. They still get privacy counsel, DPO, consent and DPIA approaches through a shared helper. `app/routers/analysis.py:808`; `app/services/scoring.py:733-756`, `:567-589`. |
| Context interview | Fix conditional DPDPA wording; keep neutral questions | Most questions are general context. SDF and “data principals” are DPDPA-specific. Preserve IDs and existing DPDPA answers. `app/dpdpa/context_questions.py:106-125`; shared routes `app/routers/questionnaire.py:7`, `app/routers/web.py:19`. |
| Context profiler, missed by plan | Fix | It produces DPDPA applicability IDs and chapter priorities for all assessments. Changing shared calls requires N3 and regression checks. `app/services/context_profiler.py:57-60`, `:157-184`; `app/routers/web.py:2534-2538`. |
| Follow-up engine, missed by plan | Fix | Its caller accepts general questionnaire questions but the prompt names DPDPA. Use mapped frameworks; retain the DPDPA branch. `app/services/followup_engine.py:98`, `:188`; `app/routers/web.py:2825-2834`. |
| Scope profiler | Keep | The DPDPA import and ID lists belong to the gated DPDPA branch. Other frameworks already use registry controls and requests. Do not remove DPDPA scope functionality or invent automatic exclusions for other frameworks. `app/services/scope_profiler.py:14-43`, `:295-319`. |
| Legacy assessment creation API | Unclear compatibility boundary | It explicitly creates DPDPA and its schema has no framework field. Backfill does not make this endpoint framework-selectable. Preserve old clients; decide whether to add explicit selection here. `app/routers/assessments.py:47-54`; `app/schemas/assessment.py:39-43`. |
| DPDPA-shaped response IDs | Keep | Shared parsing filters direct and cluster IDs against actual framework membership. There is no demonstrated cross-framework leakage here. `app/frameworks/prompts.py:118-142`. |
| Screening template and readiness copy | Keep | The screening paragraph is gated by `screening_available`; readiness copy is conditional. `app/templates/partials/questionnaire_tab.html:41-49`; `app/templates/partials/report_summary.html:6`, `:73`. |
| Parked DPDPA missing-evidence pass | Keep parked | Its explicit DPDPA identity is not a shared reader assumption. Reusing the chunker does not authorize reopening this pass. `app/services/grounding/missing.py:25`; `tasks/2026-09-30-p6-5c-decision-park-v2.md:3`. |

Backfill covers three stored locations: `assessments.selected_frameworks`, `desk_review_findings.framework_id` and `gap_items.framework_id`. The named remediation rows are `GapItem` fields, not another table (`app/models/report.py:33`, `:50-54`). The historical helper covers only gap items (`app/legacy_migrations.py:236-244`). Desk findings have a separate historical backfill (`alembic/versions/8b2d5f7e1c34_p5_3_framework_keyed_desk_review_findings.py:25-26`). Neither repairs later seed writes. Missing historical selections can preserve known legacy DPDPA provenance. Invalid or ambiguous selections need validation, not an unconditional DPDPA assignment (`app/models/assessment.py:57-74`).

The hierarchy factory and existing assessment API write explicit frameworks (`app/services/engagement_factory.py:58-75`; `app/routers/assessments.py:53`). Direct seed creation does not (`scripts/seed_test_companies.py:1286-1296`). A legacy regression test also depends on absent selections (`tests/test_legacy_dpdpa_framework_id.py:17-21`). Convert that case into migration characterization. “Every live row already has a list” is not verified here.

ISO and NIST currently use neutral root categories, with invalid or absent values falling back to `process` (`app/services/scoring.py:733-736`). The report API asserts no legacy initiatives (`tests/test_p5_2_reader_migration.py:513-534`). Roadmap tests assert UCC grouping and neutral topic names (`tests/test_p6_9_roadmap.py:72-80`, `:87-110`). Do not replace those report groups as part of N2. The DPDPA PDF golden passes `initiatives=[]`, so passing it alone does not protect curated initiatives (`tests/test_golden_dpdpa.py:72-78`).

### Stage safety and stage-5 contracts

Stage 1 is a viable independent change. Keep stage-specific manifests and old-summary rendering. Its version IDs need a legacy-source representation until document migration finishes; current analysis still returns legacy rows (`plan:135-138`, `:155`; `app/services/evidence.py:891-913`). Do not claim a uniform evidence-version key already exists.

Stage 2 is too broad for one comfortable review. Split its new migration and explicit writers from conditional context/follow-up fixes and the small category/initiative fixes. Preserve the kept list in every change. This follows the distinct affected surfaces at `plan:140-149` and N1 to N3. The stage-2 A/B establishes analysis quality, not migration safety or initiative preservation. N9 supplements it.

Stage 3 can ship default-off as storage and reconciliation after N4. Stage 4 can ship default-off as execution and per-file display. Queued stage-3 rows need not be consumed until stage 4 exists (`plan:132`, `:151-171`). Ensure claims and publication check archived assessments and engagements, not merely active evidence. Keep read purge before version purge (`app/services/evidence.py:843-865`; `app/services/retention.py:599-625`).

Stage 5 combines two substantial consumer changes. Split the shared passage adapter and desk-review persistence from judge integration, with both default-off. Resolve N5 to N7 first. Stage 6 should first flip the default, then retire legacy paths separately under N8. Do not change the fixed sequence until its recorded decision is updated (`plan:240`; `tasks/2026-10-08-session-record.md:29`).

`DeskReviewSummary` and `DeskReviewFinding` can retain their stored fields and shapes. Their existing catalog, coverage, raw response, status, timestamps, signals and citations support the proposed adapter (`app/models/desk_review.py:20-47`; `app/services/desk_review.py:615-686`). Preserve failed-framework metadata as well as the visible JSON fields. N5 identifies why fields alone do not guarantee unchanged behavior.

Leaving `document_id` null is safe for the audited consumers when versioned citations are supplied. The FK is nullable (`app/models/desk_review.py:37-39`). The API returns citations beside the nullable ID (`app/routers/desk_review.py:97-98`, `:121-122`). Names prefer cited versions (`app/services/evidence.py:1089-1102`). Workpapers and the evidence viewer use citation JSON (`app/services/workpaper.py:289-309`; `app/services/evidence_viewer.py:132-140`). Keep supplied citations for signals too; current signal persistence searches the whole source set (`app/services/desk_review.py:662-669`).

The curated adapter is feasible. Its desk builder accepts document dictionaries with text (`app/dpdpa/prompts.py:394-408`); its judge accepts quote maps (`:548-554`). Add an explicit saved-read branch. Passing `documents=[]` into today's runner does not load saved evidence because extraction and reuse sit inside `if truncated_docs` (`app/services/claude_analyzer.py:89-106`). Test zero passages as well as populated passages. Characterize global red flags in the setting-on fixture, while retaining setting-off requests.

The same controls, responses and evidence do not currently produce identical small-framework user prompts when changing from `control_ids=None` to all control IDs. The final instruction changes (`app/frameworks/prompts.py:623-626`). An offline GDPR builder check confirmed this. Another check confirmed that `evidence={}` and `documents=[]` produce “No supporting documents uploaded,” not the claimed no-quotes line (`:599-621`, `:718-726`). N6 must address both registry and curated empty paths.

### Budget and timing check

The read arithmetic is correct under the stated assumptions at `plan:209-222`. Let W be words, P parts, F frameworks and C total controls. Estimated read input is `1.6*W*(1+F) + P*(1000 + 1500*F + 30*C)`. Estimated output is `P*(500 + 1000*F)`. This repeats part text once for the reader and once per framework.

| Case | Calls | Estimated input | Estimated output | Estimated read cost | Ideal bulk time at 6 / 4 |
|---|---:|---:|---:|---:|---:|
| 22,500 words, 61 parts, ISO, 93 controls | 122 | 394,690 | 91,500 | $0.0808766 | 5.08 / 7.63 minutes |
| 100,000 words, 130 parts, six frameworks, 412 controls | 910 | 4,026,800 | 845,000 | $0.800352 | 37.92 / 56.88 minutes |

The 910 calls are `130*(1+6)`, so that count is correct. Part counts remain file-mix assumptions (`plan:221`). An offline registry check confirmed 41/93/54/54/106/64 controls and 1/6/1/1/7/1 default execution units. The batching rule returns no subdivisions for small frameworks (`app/frameworks/batching.py:108-114`).

At 12k input and 3k output, each desk/judge unit costs $0.00252. Twelve units cost $0.03024. Thirty-four units cost $0.08568 before synthesis. The six-framework $0.09 end cost requires a stated synthesis token allowance; that allowance is missing from revision 3's budget table (`plan:213-229`). Cross-framework synthesis exists only for multiple frameworks; batch summaries are deterministic (`app/services/claude_analyzer.py:866-875`, `:893-895`). Report narrative is a separate workload (`app/services/narrative.py:62`).

The advertised end waits match ideal serial desk/judge waves: ISO is 90 seconds at six workers or 180 at four. Six frameworks need about 315 or 495 seconds if synthesis also takes 45 seconds (`plan:222`, `:232`). These estimates exclude retries and other workload. The default shared concurrency is four (`app/config.py:57`).

Two minor time corrections: a one-part, six-framework file needs seven calls, so six or four slots require at least two waves, not one. Combining the six extraction calls while retaining the framework-free reader reduces 910 calls to 260, a factor of 3.5, not six (`plan:164-166`, `:231-233`).

The budgets are estimates, not verified model limits. The unchanged extraction builder embeds complete control text, not a fixed 30-token control representation (`app/frameworks/prompts.py:309-320`, `:343-363`). Offline character counts for an empty ISO extraction prompt imply about 5,167 tokens at four characters per token, before document text or system instructions. That is only a rough check. N7 prevents the 12k and 3k estimates from being treated as safe request ceilings. Current provider price, context window, OCR time, actual output sizes and latency were not verified.

### Verification and open questions

Ran `OPENROUTER_KEY="" PYTHONDONTWRITEBYTECODE=1 DATABASE_URL="sqlite:///:memory:" .venv/bin/python -m pytest tests/test_golden_dpdpa.py tests/test_answer_key_isolation.py -q -p no:cacheprovider --basetemp=/private/tmp/document-review2-pytest`: **10 passed**. The tests replay complete analyzer requests and compare output, score and PDF text (`tests/support/analyzer_mock.py:23-31`, `:61-75`; `tests/test_golden_dpdpa.py:92-124`). This proves the current baseline only. Future stage-2 byte identity requires running these unchanged tests after implementation, plus separate initiative/context/screening checks.

Offline checks also reproduced read costs, registry batch counts and the two judge-builder failures. No live calls or answer keys were used. Review coverage included coherence, feasibility, scope, source navigation and failure paths. External comparison was excluded by the handoff's no-live-call rule. No Compound Packs were declared.

1. No live database was present at the configured default path. The actual null/invalid row counts and provenance of invalid selections remain unknown. Require migration preflight rather than assuming every row is populated (`app/config.py:16`; `plan:142`).
2. Where is the framework-free reader result stored and fingerprinted? The only named identity is version/framework/part, but cost and execution count one extra reader per part (`plan:152`, `:165`, `:229`).
3. Does “read set” include immutable result generations or content fingerprints? Comparing row IDs would miss changed content after Re-read. Preserve old run inputs when settings or results change (`plan:152`, `:168`, `:187`).
4. Does “at most 2 attempts” mean queue attempts or provider sends? The client retries internally and leaves timed-out provider threads alive. Define how the shared budget counts those threads and shuts down the dispatcher (`plan:162`; `app/services/llm_client.py:296-314`, `:349-373`).
5. Is rejected empty-text upload handling the existing visible validation error, or a persistent failed receipt? The former is already safe from silent success. A status on a rolled-back version cannot provide the latter (`app/services/evidence.py:703-715`; `plan:154`).
6. Is the legacy creation API intentionally DPDPA-only, and when is off mode retired? These compatibility boundaries affect N1, N3 and N8 (`app/routers/assessments.py:47-54`; `plan:193`, `:239`). The sequence slot also remains a recorded user decision (`plan:240`).
