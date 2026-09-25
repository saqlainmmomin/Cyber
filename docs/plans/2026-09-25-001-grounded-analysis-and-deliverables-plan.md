# Phase 6 Plan: Grounded Analysis, Multi-Framework Review, and Deliverables

**Status:** Decisions taken 2026-09-25 (see Part F). Handoffs written: P6-1 (`tasks/handoffs/2026-09-25-p6-1-llm-plumbing.md`) and P6-2a (`tasks/handoffs/2026-09-25-p6-2a-dpdpa-test-criteria-draft.md`).
**Date:** 2026-09-25
**Builds on:** Phase 5 (complete on `main` at `e0fbb52`, PRs #38-#46). Every file:line reference below was read against `origin/main` at that commit.
**Product contract:** `docs/product/2026-09-21-cyberassess-product-requirements.md`
**Decisions log:** `tasks/2026-09-21-adversarial-review.md` (D1-D11). This plan adds D-P6-A to D-P6-K. It amends D8 (D-P6-C, approved by Saqlain 2026-09-25) and otherwise reopens nothing.
**Ownership rules:** `tasks/agent-ownership.md`
**Measurement:** P5-9 harness (`docs/plans/2026-09-24-002-p5-9-end-to-end-validation-plan.md`). The Stage C baseline on today's pipeline is the gate for this whole plan.

---

## Summary

Phases 1-5 made the *data layer* correct. Every final number and report now reads consultant-approved Conclusions. They cite immutable evidence versions and carry append-only history. The *LLM layer* feeding that data layer was never rebuilt. It is still the original DPDPA gap-report generator, generalised by string templating:

- One huge call per framework. It must emit 12 fields for 90+ controls in one response. It cannot say "insufficient evidence". It invents numbers nobody can verify (maturity 0-5, timeline weeks, effort). Its quotes are free text, checked only after the fact.
- A DPDPA + ISO + NIST assessment is three single-framework reviews run side by side. Each reads the same documents, is told "assess against X only", and does not know the others exist.
- DPDPA gets a hand-curated prompt. ISO and NIST, the two launch packs with the most at stake, get a generic template.

The *deliverables* mostly re-render the proposal format. They are not built for the three people who read them: the consultant, the client's leadership, and a reviewer.

This plan does four things:

1. **Grounded analysis pipeline:** the LLM proposes, code verifies, the consultant decides. The judge can only cite claims that already passed a deterministic citation check.
2. **Genuine multi-framework review:** read documents once, judge per framework with awareness of what else is in scope, and surface cross-framework divergence.
3. **Deliverables rebuilt for their readers:** a consultant requirement card, a board report, a reviewer workpaper, and an editable output.
4. **CTO audit items:** what the pivot overlooked outside the LLM and report layers, triaged.

---

## Principles (apply to every task)

1. **LLM proposes, code verifies, human decides.** No LLM output reaches a consultant without a deterministic check, or a visible "unverified" marker where no check is possible.
2. **Closed-set citation.** The judging model can only reference claim IDs from a verified set. It cannot author quotes, facts or document locations.
3. **"Insufficient evidence" is a first-class answer.** A model forced to choose between compliant and non-compliant without evidence will hallucinate one of them.
4. **No LLM-invented numbers.** Scores, risk levels, priorities and dates are deterministic (pack criticality × outcome) or consultant-entered. The LLM writes words, never numbers that look measured.
5. **Read once, judge per framework.** The cost and consistency of documents do not scale with the framework count.
6. **Content beats prompting.** Explicit per-requirement test criteria in the pack matter more than any prompt wording.
7. **Every change is measured.** P5-9 catch rate, false-positive rate, grounding, stability and cost, plus the production consultant-override rate. A change stays only if it holds or improves the metrics.
8. **Answer-key isolation (D-P5-9-C).** Nothing in this plan reads `validation/companies/*/answer_key.json` or tunes toward a planted gap.

---

## Part A: What is wrong today (evidence)

### A1. Analysis call shape

- **One judge call per framework**, streaming, `max_tokens=16384` (`app/services/claude_analyzer.py:436-444`). The ISO (93 controls) and NIST (94) outputs of 12 fields each run close to that ceiling.
- **A missing control fails the whole framework.** `validate_and_filter` raises when any control ID is missing (`app/schemas/llm_output.py` ~L183-190). P5-1 made scoring fail closed, so one truncated response loses every verdict for that framework.
- **Frameworks run sequentially** in analysis (`claude_analyzer.py:417`) and in desk review (`app/services/desk_review.py:115`).
- **No structured-output mode.** The code relies on "Respond ONLY with valid JSON" plus regex fence-stripping (`claude_analyzer.py:_parse_json_response`). There is no retry.
- **Analysis runs synchronously inside the HTTP request** (`app/routers/analysis.py:93`, a sync `def` route) for multi-minute LLM work. Desk review uses `BackgroundTasks` (`app/routers/web.py:~2531`). Neither survives a process restart.

### A2. Output vocabulary and invented fields

- **The model cannot answer "insufficient evidence".** `KNOWN_STATUSES` is compliant / partial / non-compliant / not_assessed / not_applicable (`app/services/scoring.py:31`). The Conclusion schema already supports `insufficient_evidence` (`app/schemas/conclusions.py:17`), and PR-042 requires it.
- **The judge invents fields with no evidence behind them** for every control, including compliant ones: `maturity_level` (0-5 CMMI), `timeline_weeks`, `remediation_effort`, `remediation_priority`, `root_cause_category` and `risk_level` (`app/frameworks/prompts.py` `build_framework_system_prompt`, and `app/dpdpa/prompts.py:60-100`).
- **The evidence quote comes last in the schema.** The model writes its verdict first, then justifies it, even though the prompt tells it to "quote first".
- **The judge's `evidence_quote` is never grounded.** Only extraction-path quotes pass `_ground_evidence_quotes` (`claude_analyzer.py:~160`). A "compliant" verdict with no quote is flagged, but a *fabricated or irrelevant* quote passes.
- **Synthesis asks the LLM for `estimated_score: 0-100` per framework** (`app/frameworks/prompts.py`, `build_synthesis_prompt`). Nothing reads it (verified by `git grep`), but it breaks the deterministic-scoring rule and is a trap for the next person.

### A3. Evidence visibility caps recall

- **The judge never sees documents once desk review found any quote.** If desk review found *any* quote for the framework, the judge sees only those quotes, never the documents (`app/frameworks/prompts.py` `build_framework_user_prompt`, the evidence/`_documents_section` branch). Anything desk review missed is judged on questionnaire answers alone. The judge's recall can never exceed desk review's. The "paper moat" profile (P5-9 C3) is exactly this failure.
- **Truncation is DPDPA-biased.** Documents are cut to 20,000 words total. The analyzer ranks them by a DPDPA-only category list (`claude_analyzer.py:~335-350`). Desk review truncates in upload order (`desk_review.py:514-531`).
- **Upload categories are DPDPA-only.** `DocumentCategory` (`app/schemas/assessment.py:27-37`) has no ISMS policy, Statement of Applicability, risk register, access review, incident response plan or BCP. ISO and NIST evidence all lands in `other` and is truncated first.

### A4. Multi-framework blindness

- **Each desk review runs as if its framework were the only one.** Desk review is one full call per framework over the same documents, each told "Assess against {fw.name} only" (`app/frameworks/prompts.py`, `build_framework_desk_review_system_prompt`). The user prompt carries company, industry and documents, but not the other in-scope frameworks (`app/dpdpa/prompts.py:392-406`).
- **DPDPA red flags misfire on multi-framework clients.** "data subject", "legitimate interest" and "references to compliance frameworks the organization is unlikely to follow" are flagged as copy-paste or template problems (`app/dpdpa/prompts.py:~255-275`). A unified GDPR + DPDPA + ISO policy uses that language legitimately. The real DPDPA finding ("does not address the Data Protection Board, data principal rights or consent managers") is a different check.
- **The same evidence is judged independently per framework**, so one access-control policy can get three different verdicts under ISO A.5.15, NIST PR.AA and DPDPA safeguards. UCC deduplicates questions and requests only (D8). Nothing checks cross-framework consistency. The only cross-framework view is a post-hoc synthesis over counts and the top 5 critical IDs.

### A5. Pack depth asymmetry

- **DPDPA has a hand-curated desk-review prompt** with section-specific absence examples, 7 flag types and a data-minimisation focus (`app/dpdpa/prompts.py:213-390`).
- **ISO and NIST get a generic template** filled with the persona line, the control list and 5-7 one-line red flags (`app/frameworks/definitions/iso27001.py:1155-1180`).
- **No pack has per-control test criteria.** "What does compliant mean for ISO A.8.2" is left to the model on every run. That is the main source of run-to-run inconsistency.

---

## Part B: Grounded analysis pipeline (v2)

v2 runs behind a setting (`analysis_pipeline_version: "v1" | "v2"`, default `v1` until the gate in Part G passes). v1 is untouched so the harness can A/B them.

### Stage 0: Document preparation (deterministic)

- **Chunking.** Chunk each Evidence version's extracted text by heading/section, ~800-1,500 words per chunk. Each chunk keeps an offset map into the immutable extracted text so `citations.locate_excerpt` (`app/services/citations.py:89`) resolves spans exactly.
- **Metadata.** Extract the document date, version and approver where present. This uses deterministic regex plus a cheap LLM fallback whose output is verified against the text. Currency, period and cut-off checks (PR-022) then happen in code, not in the model.
- **No global word cap.** Every chunk gets read. Cost is bounded by chunk count × batch count, and is reported.
- **Untrusted input.** Wrap all document text in explicit untrusted-content delimiters. See Part E, prompt injection.

### Stage 1: Claim extraction (cheap tier, parallel)

- **Inputs.** One call per (chunk × control batch). Batches are the pack's `Section`s (`app/frameworks/schema.py:27`) or UCC clusters, ~10-20 requirements each.
- **Output schema** (JSON schema enforced via `response_format`):
  `{claims: [{requirement_ids[], statement, quote, kind: design|operating|context, stated_period?, stated_owner?}]}`
- **Code check (hard gate).** `quote` must resolve via `locate_excerpt` inside that chunk. Otherwise the claim is **dropped** and counted as a grounding failure in run metrics.
- **Support check (cheap tier, yes/no/partial).** "Does this quote support this statement?" `no` drops the claim. `partial` keeps it with the statement rewritten to the supported part, or flagged for review. This catches the real-quote-overstated-claim case that substring grounding misses.
- **Framework neutrality.** Claims are framework-neutral facts. The same claim may carry requirement IDs from several frameworks. Stored as `AnalysisClaim` rows in `AnalysisRun.claims_json` (D2: JSON, not new tables).

### Stage 2: Requirement judgment (judge tier, parallel by batch)

- **Inputs per requirement batch:**
  - requirement references and **test criteria** (Part B.1)
  - verified claims tagged to those requirements, by claim ID
  - the confirmed questionnaire response and its provenance (human, document pre-fill or inferred)
  - relevant desk-review absence signals
  - scope context: the other in-scope frameworks, and the assessment period and cut-off
- **Output schema** (enforced), one entry per requirement, ordered so the model reasons before it concludes:
  ```
  requirement_id
  criteria: [{criterion_id, result: met|not_met|no_evidence, claim_ids[]}]
  contradictions: [{claim_id, response_ref, note}]
  outcome: compliant|partially_compliant|non_compliant|insufficient_evidence|not_applicable_proposed
  gap_statement (≤ 2 sentences, empty if compliant)
  missing_evidence: [{document_type, what_it_would_show}]
  ```
- **Code checks (deterministic, post-judgment):**
  - Every `claim_id` must exist in the verified set for that requirement. An unknown ID is dropped, and the item is flagged.
  - `compliant` requires every criterion `met` with ≥1 claim. Otherwise the outcome is downgraded to `insufficient_evidence` and flagged "model/criteria inconsistency".
  - A response-only "yes" with no supporting claim sets `unsupported_assertion=true` (PR-041).
  - `not_applicable_proposed` never becomes N/A without the consultant (existing ApplicabilityProposal semantics).
  - Missing requirement IDs in a batch trigger **one retry for only the missing IDs**. A second failure marks those requirements `insufficient_evidence` + `analysis_incomplete`. The rest of the framework survives.
- **Deterministic fields** (never from the LLM): `risk_level` = f(pack criticality, outcome); `priority` = f(risk_level); score = existing `scoring.py` over approved Conclusions only.

### Stage 3: Remediation drafting (cheap tier, gaps only, on demand)

- **Scope.** Only for `partially_compliant` / `non_compliant`. Preferably generated when the consultant approves the Conclusion, or when a Finding is created, so no text is spent on verdicts the consultant overturns.
- **Output.** `recommended_action` (≤ 3 sentences) and optional `suggested_owner_role`. There is no effort, timeline or maturity; those are consultant-entered on the Action.

### Stage 4: Engagement narrative (synthesize tier, after approval)

- **Executive and cross-framework narrative** are generated from **approved** Conclusions and Findings only, at report-draft time, not at analysis time.
- **Grounding.** Every sentence must cite Finding IDs, and code checks those IDs exist. No scores are requested. The consultant edits the narrative before the snapshot is issued.

### B.1 Test criteria (pack content)

- **Schema.** Add `test_criteria: tuple[TestCriterion, ...]` to `Control` (`app/frameworks/schema.py:14`). Each criterion is `{id, statement, kind: design|operating, evidence_hint}`, with 2-5 per requirement.
- **Licensing (D4).** Criteria are *assessment guidance in our own words*, referencing clause numbers, never reproduced standard text. This is the same rule as `EvidenceRequest.reason`.
- **Authoring.** An LLM drafts from public guidance and our existing descriptions and red flags. A human curates. Criteria are versioned in the pack and live in Python like the existing definitions.
- **Order:** DPDPA (41) → ISO Annex A (93) → NIST CSF (94). GDPR, HIPAA and PCI stay disabled.
- **Side benefits.** Criteria give PR-022's design vs operating-effectiveness split for free. They also give consultants a reusable audit programme, and they become the consultant card's checklist.

### B.2 Reliability and plumbing

- **Structured output, provider-agnostic.** `llm_client.call_llm` gains `response_schema`. Callers pass a JSON schema built from Pydantic models. The client maps it to the provider's mechanism: OpenRouter `response_format: {type: json_schema}` + `provider.require_parameters: true` today, and Bedrock Converse tool-use with a forced tool and `inputSchema` after the D-P6-K migration. Nothing outside `llm_client.py` may depend on an OpenRouter-specific feature, so the Bedrock swap stays a client change. The existing ZDR preference (`app/services/llm_client.py:52-55`) remains until then.
- **Concurrency.** A bounded thread pool, ~6 workers, per assessment, with per-call timeout and one retry with backoff on 429/5xx.
- **Temperatures.** Set the screening (`app/services/screening.py:117`) and vision (`document_processor.py:~188`) temperatures to 0.
- **Provenance (PR-040).** Every call records tier, model, prompt-template hash, pack version, tokens, latency and outcome in the `AnalysisRun` envelope. The P5-9 harness reads cost from there.
- **Background jobs.** Analysis moves to a persisted job (the `AnalysisRun` row is already the state). At startup, any `running` run older than N minutes is marked `failed(interrupted)`, so the UI never shows a permanent spinner.
- **Cleanup.** Remove `estimated_score` from synthesis.

### B.3 Desk review under v2

- **Desk review becomes a view over Stage 0-1 output.** It is no longer a separate LLM pass:
  - the document catalog comes from Stage 0 metadata plus claim coverage
  - the evidence map is the verified claims
  - absences come from Stage 2's `no_evidence` criteria, or from a cheap "what is missing" pass per batch
  - red flags become per-framework *checks over claims*
- **Pre-fill (P5-4) keeps working.** It reads the same `DeskReviewFinding` rows, and the adapter writes them from claims.
- **Cost.** Desk review and analysis share one document read instead of N+N.

---

## Part C: Multi-framework review

1. **Shared claims, per-framework judgment.** Stage 1 runs once per document set. Stage 2 runs per framework over the same verified claims. Consistency comes from the design, and cost grows with document volume.
2. **Scope-aware prompts.** Each framework judge is told the other in-scope frameworks and what language is therefore expected. DPDPA "copy-paste" flags are replaced by substantive checks: "the policy never names the Data Protection Board", "no data principal grievance route", "no consent-manager provision where applicable". GDPR vocabulary is a problem only when DPDPA-specific obligations are absent, not in itself.
3. **Deterministic divergence check.** For each UCC cluster, if the same claim set produces `compliant` under one framework and `non_compliant` under another, the requirement card shows a "framework divergence" note that the consultant must acknowledge. It is not blocked: requirements can legitimately differ.
4. **Cross-framework remediation view** (for deliverables). One Action can address Findings across frameworks (already allowed by the PRD relationship rules). The report shows "fixing X closes N Findings across ISO, NIST and DPDPA".
5. **Framework-aware document categories.** Replace the DPDPA-only `DocumentCategory` enum with pack-contributed categories, unified with `EvidenceRequest.document_type`. There is one vocabulary for requests, uploads and truncation priority.
6. **Pack depth parity.** ISO and NIST red flags are rewritten as auditor checks: SoA justification, internal audit cycle, management review inputs, risk-treatment traceability, and NIST profile/tier claims vs evidence. This is done alongside the test criteria.

---


## Part D: Deliverables

The reports audit was run against `origin/main` on 2026-09-25.

**Already right:**
- Every client output reads approved Conclusions (`app/services/approved_report.py:264-299`).
- There is no blended score.
- Snapshots are write-once and hash-verified.
- The web Workpaper meets PR-055.

**Not built for the people who read it:**
- **Consultant:** reviews a proposal format, not the evidence-first card from Part B.
- **Client leadership:** gets a PDF that mixes deterministic counts with leftovers from the old questionnaire era.
- **Reviewer:** gets a Workpaper HTML snapshot that depends on `/static` and a CDN (`base.html:12-14`), so it does not render standalone.

**No editable output exists.** DOCX is available only for the RFI and the evidence checklist. No XLSX exists anywhere.

### D0. Defects to fix regardless

| # | Defect | Evidence |
|---|---|---|
| 1 | **Assessment period and evidence cut-off are not modelled at all**, although PRD invariant 4 and PR-012/PR-050/PR-053 require them. The integrated PDF prints "not recorded" | `git grep` finds no field. `pdf_export.py:~1528` |
| 2 | The report prints the *render* date as the assessment date | `pdf_export.py:1263` |
| 3 | Everything goes through Latin-1 via `S()`, so Devanagari names and ₹ render as `?` | `pdf_export.py:89-93` |
| 4 | Two different "gaps identified" counts (cover vs appendix) | `pdf_export.py:843` vs `:1179` |
| 5 | Methodology still describes CMMI maturity and "questionnaire response scale" scoring, which is not how approved scoring works | `pdf_export.py:1420-1448` |
| 6 | Disclaimer says "qualified legal counsel" and M5 says "privacy practice" for ISO/NIST-only reports, breaking the framework-conditional copy rule | `pdf_export.py:1447-1452` |
| 7 | "Remediation Timeline (not estimated) n/a" KPI card; permanently empty "Why These Gaps Exist"; roadmap uses fixed P1-P4 windows instead of real Actions | `pdf_export.py:69-74,1004-1049`; `web.py:2034` |
| 8 | **The DPDPA penalty table looks wrong.** It has `BN.NOTIFY` at ₹250 Cr and `CH4.SDF` at ₹50 Cr. The Schedule reads ₹200 Cr (breach notice) and ₹150 Cr (SDF obligations), and unmatched IDs fall back to ₹50 Cr. **Verify against the statute before fixing.** | `web.py:1856-1870` |
| 9 | Integrated PDF has no Scope & Limitations, methodology or disclaimer pages | `pdf_export.py:1461+` |
| 10 | Cover domain bars and heatmap overflow with auto page break off once DPDPA+NIST exceed ~8 domains (inferred) | `pdf_export.py:760-878` |
| 11 | Unescaped company name in `Content-Disposition` | `reports.py:222-227`, `web.py:1121,1153` |

### D1. Consultant requirement card (the working surface, PR-014)

One card per applicable requirement, in this order:

1. **Proposed outcome**, the one-line reason, and a status chip (AI proposal / edited / approved).
2. **Criteria checklist.** Each criterion shows ✓ / ✗ / ?, and each ✓ or ✗ links to the highlighted span in the evidence viewer (existing citation spans).
3. **What the client said vs what the evidence shows**, with contradictions highlighted and unsupported assertions labelled.
4. **Evidence quality**, as separate chips (current, in period, in scope, design vs operating). Never one confidence number (PR-022).
5. **Missing evidence**, with a one-click "add to RFI" into the P5-6 RFI.
6. **Framework divergence note** when it applies (Part C.3).
7. **Decision controls.** Approve, edit or reject individually, as D3 requires.

**A review queue, because D3 has a cost.** A DPDPA + ISO + NIST assessment has ~228 requirements to approve one by one. The queue:
- sorts by deterministic risk, then by flags (inconsistency, unsupported assertion, divergence)
- supports keyboard navigation
- groups UCC-shared requirements so the consultant reads one evidence set once, while still approving each Conclusion separately

D3 stays intact. We are removing friction around it, not the control itself.

### D2. Client board report (redesigned, new report type)

Target length: 10-15 pages plus appendices, one template per engagement.

1. **Cover:** client, engagement, frameworks and versions, **assessment period, evidence cut-off**, issue date, snapshot ID and version, draft or issued watermark.
2. **Management summary:**
   - basis of assessment
   - scope, exclusions and limitations
   - a per-framework posture paragraph (Stage 4 narrative, grounded in Findings, consultant-edited)
   - per-framework score **with coverage** ("62%, 11 requirements insufficient evidence")
3. **Top risks:** 5-10 Findings ranked by deterministic risk. Each shows what is wrong, why it matters in business terms, the cited evidence (file, version, location), owner and target date.
4. **Remediation roadmap built from real Actions**, each listing the Findings it closes across frameworks, for example "fix once, closes 4 Findings across ISO, NIST and DPDPA". Owners and dates come from Actions, not from priority buckets.
5. **What we could not assess:** insufficient-evidence requirements and open RFI items. This honest boundary is what makes the rest credible.
6. **Per-framework sections:** score, domain view, findings table.
7. **Prior-period comparison**, when a previous assessment exists (web-only today).
8. **Sign-off:** prepared by, reviewed by, issued by, with real identities (needs E-C1/C3).
9. **Appendices:**
   - methodology (framework-correct)
   - full requirement register (outcome plus citation on every row, not only on Finding rows)
   - evidence register (documents reviewed, version, hash prefix, date)
   - **ISO Statement of Applicability**, when ISO is in scope. Annex A applicability, justification and implementation status are mostly derivable from existing applicability and Conclusions.

### D3. Formats

- **DOCX of the board report.** Consultants always edit before sending. `python-docx` is already a dependency. The issued snapshot stays the immutable record. The DOCX is labelled "derived from snapshot X, vN", and edits do not flow back.
- **XLSX** requirement register and action tracker (new dependency `openpyxl`). Client teams work from spreadsheets.
- **Standalone Workpaper:** self-contained HTML with inline CSS and no CDN, or a PDF, so a reviewer can open it offline.

### D4. Rendering stack

`fpdf2` hand layout with `auto_page_break=False` is the root cause of D0 #3 and #10, and it makes every new section expensive. Proposal (D-P6-H):
- Build the new board report as **Jinja2 HTML → PDF via WeasyPrint**. It gets Unicode fonts (Noto Sans + Noto Sans Devanagari), real pagination, and one template shared by the web preview and the PDF.
- The existing fpdf2 PDFs stay frozen, which satisfies "PDF sections are additive-only", and are retired once the new type reaches parity.
- WeasyPrint needs Pango system libraries, so the Docker image must include them.

---

## Part E: CTO audit (what the pivot overlooked)

The platform audit was run against `origin/main` on 2026-09-25. **[V]** marks items spot-checked by hand in this session.

The evidence, approval and snapshot engine is well built. There is **no perimeter around it**, and the audit trail cannot attribute actions to people. **None of this can go to a real client network until the Critical items land.**

### Critical (block any external exposure)

- **E-C1 No authentication [V].**
  - `auditor_username`, `auditor_password` and `session_secret` are read only by a startup warning (`config.py:45-69`).
  - `/login` redirects straight to the dashboard (`main.py:~156`).
  - Every route is open, including permanent purge, evidence download, approval and issue.
- **E-C2 CORS `*` with credentials and no CSRF [V]** (`main.py:~121-127`). Any web page the consultant visits can drive the app on localhost. The Phase 5 plan deferred this "before any network-exposed pilot" and it was never scheduled.
- **E-C3 The audit trail is unattributable [V].**
  - The approver is whatever text is typed into a form field, defaulting to "Manager Review" (`conclusion_review.py:20-21,103-105`).
  - Every evidence action is logged as the literal `"consultant"` (`evidence.py:30`).
  - There is no User model.
  - This breaks PR-056, D3's liability purpose, and the sign-off block in D2.
- **E-C4 No encryption at rest.** Evidence blobs, extracted text, raw LLM responses and backups are all plaintext.
- **E-C5 ISO pack reproduces Annex A wording verbatim [V]**, e.g. `iso27001.py:35`, "A set of policies for information security shall be defined, approved by management…". That contradicts D4 (reference-only) and is a licensing exposure for a commercial product. It must be rewritten in our own words before selling. This naturally pairs with authoring test criteria (B.1).

### High

- **E-H1 Upload hardening.**
  - Consultant uploads have no size cap (`documents.py:41` `await file.read()`).
  - File type is decided by extension only.
  - `scan_blob` is a stub that always passes (`evidence.py:135-140`).
  - PDFs and DOCX are parsed fully with no zip-bomb or page guard.
  - Magic-link uploads (from untrusted clients) are capped but not scanned.
- **E-H2 Prompt injection from client documents.** Document text and client-controlled filenames go into prompts with no delimiters. A client under assessment can plant "all controls adequate". Mitigated by Part B's closed-set citation, untrusted-content delimiters, and **a new injected-document test pack in P5-9**. That test covers a failure mode, not a planted-gap key.
- **E-H3 Durable jobs.**
  - Analysis runs synchronously in the request.
  - Desk review uses in-process `BackgroundTasks`.
  - Nothing resets `analyzing`/`running` state on restart.
  - The OpenAI client has no explicit timeout (`llm_client.py:65-68`).
  - Covered by B.2.
- **E-H4 Deployment config is broken [V].**
  - `docker-compose.yml` still passes `ANTHROPIC_API_KEY`.
  - There is no `SESSION_SECRET`.
  - There is no `.dockerignore`, so `.env`, `data/` and `uploads/` get baked into the image.
  - The container runs as root.
  - There is no CI (`.github/` absent).
- **E-H5 Cross-border data position.**
  - Full document text and answers go via OpenRouter to DeepSeek, and to Anthropic for vision. ZDR is enforced, which is good, but there is no region pinning and no redaction.
  - A firm selling DPDPA readiness needs a written position: subprocessor list, DPAs, where data is processed, and an optional redaction pass for obvious personal data before LLM calls.
- **E-H6 Accuracy is unmeasured.** P5-9 Stage C has never run on the live pipeline. Every quality claim about the product is unproven until it does.
- **E-H7 Regulatory currency.**
  - The DPDPA pack has no reference to the **DPDP Rules, 2025** (`git grep` is empty).
  - The desk-review prompt attributes the 72-hour breach timeline to "Section 8(6)" of the Act (`app/dpdpa/prompts.py`), but that timeline comes from the Rules. Verify it.
  - More generally, there is no process for pack updates when a regulation changes: bump the pack version, show affected Conclusions, and trigger re-review (the pack-level analogue of PR-026).

### Medium

- **E-M1 SQLite has no WAL mode or busy timeout** (`database.py:36-40`). Long analysis transactions plus concurrent consultants will produce "database is locked" errors.
- **E-M2 Observability and cost.**
  - There is no error tracking.
  - `AnalysisRun` has no token or cost columns, so LLM cost per engagement cannot be priced into a statement of work.
  - Covered by B.2 provenance.
- **E-M3 Retention.**
  - Purge does not scrub backups, so restoring an old backup brings purged data back.
  - The retention floor is 1 year.
  - There is no legal hold.
- **E-M4 Test hygiene.**
  - `pytest` is not declared in any requirements file.
  - There is no lockfile or `.python-version`, despite the 3.13 pin.
  - There are no browser tests.
  - A known ordering flake recurs.
- **E-M5 Legacy writes.** `GapReport`/`GapItem` are still written on every analysis (`analysis.py:395,439,691,737`), and there are two prompt stacks. Retire both after v2.
- **E-M6 Incremental re-analysis.** When RFI evidence arrives, the whole analysis re-runs. v2 claims make "re-judge only requirements whose claim set changed" cheap, and that closes the RFI loop.

### Low

- **E-L1** `web.py` is 2,536 lines and contains business logic.
- **E-L2** The README is stale: it says GDPR/HIPAA/PCI are "Live" and that calls go to the Anthropic API.
- **E-L3** There is no whole-client export (JSON/zip of evidence and records) for offboarding or portability.

### Strategic (not code)

- **No real user has used this yet.** Phases 1-5 were built and validated on synthetic data. After Track 4 (security and residency) and the P5-9 baseline, one real consultant running one real engagement will produce override-rate data worth more than any synthetic pack. Recommend booking that pilot now, so it is waiting when Track 4 lands.
- **Consultant-override rate** (AI proposal vs approved, per framework, requirement and prompt version) is the production quality metric. It is a query over `ConclusionRevision` plus a small internal report.

---

## Part F: Decisions

Saqlain confirmed these on 2026-09-25. Entries marked *proposed, not objected to* were not challenged, and they are treated as accepted unless someone reopens them.

| # | Decision | Choice | Rationale |
|---|---|---|---|
| D-P6-A | AI outcome vocabulary | The PRD's five outcomes, including `insufficient_evidence`. Maturity, timeline, effort and root cause are removed from AI output. *(Proposed, not objected to)* | Principles 3 and 4; PR-042 |
| D-P6-B | Citation model | Closed-set: the judge references verified claim IDs only, and every claim passes locate + support check. *(Proposed, not objected to)* | Principle 2; PR-021/041 |
| D-P6-C | **Amend D8. APPROVED** | Verified claims are extracted once and tagged to requirements across all in-scope frameworks as *system suggestions*. The consultant still confirms each Conclusion's evidence set. Conclusions stay per framework. UCC stays questions-only for the questionnaire | Read once, judge consistently. Accepted cost: a mis-tagged claim can repeat across frameworks. Each framework's judge applying its own test criteria, plus per-Conclusion consultant review, is the mitigation. |
| D-P6-D | Test criteria | Added to packs, own words, reference-only (D4), versioned. **Saqlain signs off every criterion.** An LLM drafts them for review | Principle 6 |
| D-P6-E | Rollout | v2 behind `analysis_pipeline_version`. The default flips only after P5-9 shows catch rate ≥ baseline, FP ≤ baseline, stability ≥ baseline, cost reported. *(Proposed, not objected to)* | Principle 7 |
| D-P6-F | Narrative | Executive and cross-framework narrative is generated only from approved Findings at report-draft time, cites Finding IDs, and is consultant-edited. *(Proposed, not objected to)* | No unreviewed LLM text in a client document |
| D-P6-G | Period and cut-off | Assessment period and evidence cut-off are required before any Conclusion can be approved, and are printed on every deliverable. *(Proposed, not objected to)* | PRD invariant 4; PR-012/050/053 |
| D-P6-H | Report rendering. **APPROVED** | The new board report is HTML → PDF (WeasyPrint). fpdf2 reports are frozen, then retired at parity | Unicode (₹, Devanagari), real pagination, one template for the web preview and the PDF |
| D-P6-I | **Security sequencing. APPROVED** | The tool runs locally only. Auth, encryption in transit and at rest, CSRF/CORS and upload hardening move to **Track 4, after the v2 pipeline is implemented and validated**. The gate is unchanged: no non-localhost use and no real client data before Track 4 merges | Saqlain, 2026-09-25 |
| D-P6-J | ISO content | Rewrite ISO control descriptions in our own words, with references only, done together with the ISO test criteria (P6-2). *(Proposed, not objected to)* | E-C5, D4 |
| D-P6-K | **LLM provider. APPROVED** | Move from OpenRouter to **AWS Bedrock in `ap-south-1` (Mumbai)** so client data stays in India. This replaces the redaction question (E-H5). Done in Track 4 | Data residency for a DPDPA-selling firm |

### Test criteria lifecycle (D-P6-D)

- **Defined once per pack version, not per assessment or client.** Every engagement reuses them. The work is heavy the first time and light afterwards.
- **They are revisited only in three cases:**
  1. The regulation or standard changes. The DPDP Rules 2025 check (E-H7) is the first such review.
  2. Consultant-override data shows a criterion is systematically wrong. For example, consultants keep overturning ISO.A8.2 "met" proposals.
  3. P5-9 exposes a miscalibration at the *criterion* level, never at a planted-gap level (D-P5-9-C).
- **Changing any criterion bumps the pack version.** Approved Conclusions keep the pack version they were judged against. New analysis runs use the new version. A PR-026-style impact list shows affected drafts.
- **Size.** About 228 requirements across DPDPA (41), ISO Annex A (93) and NIST CSF (94), at 2-5 criteria each, is roughly 700-900 criteria.
- **Review process.** An LLM drafts them from public guidance and our existing descriptions. Saqlain reviews one domain at a time in a sheet (approve / edit / reject per criterion). The approved sheet is converted into pack code.
- **Order.** DPDPA first, so v2 can be built and tested on it. ISO and NIST follow while Stage 2 is in development.
- **Independence rule.** Criteria are written from the standards and regulations only. **The drafting agent never sees `validation/companies/`.** The reviewer should sign off without reference to the P5-9 answer keys, or the harness measures the criteria against themselves.

---

## Part G: Tasks, sequencing, and gates

Owners are assigned per `tasks/agent-ownership.md` when handoffs are written. `[AR]` marks an adversarial-review merge gate.

### Track 0: Now (no dependency on the redesign)

- **P5-9 Stage C: baseline run on v1, after P6-1 merges.** Running it after P6-1 means the v1 baseline already has timeouts, temperature 0 and cost records, so the later v1 → v2 comparison measures only the pipeline redesign. Before that: merge the P5-9a harness (`codex/p5-9a-validation-harness`) and the packs (`codex/p5-9-stage-a-packs`) to `main`, clean up the stray `fix_*.py` scripts and `*_backup/` pack directories, and finish the pack fairness audit. **Gate for the Track 1 default flip.**
- **P6-0c Dev hygiene (only the parts the pipeline work needs)**
  - GitHub Actions running pytest
  - dev requirements, `.python-version`
  - SQLite WAL mode and busy timeout, since parallel LLM batches will write concurrently
- **P6-0d Content checks**
  - verify and fix the DPDPA penalty table (D0 #8)
  - check DPDP Rules 2025 currency (E-H7)
- **Localhost guard (≈10 lines, not the security track).** Bind to `127.0.0.1` and replace CORS `*`-with-credentials by the local origin. Even fully local, any web page open in the consultant's browser can POST to `localhost:8000` today (E-C2). This is the one exposure that local-only use does not remove, so it is patched now. Real CSRF protection comes with Track 4.

### Track 1: Analysis pipeline

- **P6-1 LLM plumbing (behaviour-neutral, benefits v1 immediately)**
  - provider-agnostic structured output
  - timeouts and retry
  - bounded concurrency across frameworks
  - temperature fixes
  - per-call provenance and cost in `AnalysisRun`
  - durable jobs with restart recovery
  - remove `estimated_score`
  - untrusted-content delimiters (a quality concern: prompt injection distorts proposals even locally)
- **P6-2 Test criteria content.** DPDPA first (41), then ISO (93, with the own-words rewrite), then NIST (94). Saqlain signs off each domain sheet. This is the critical path.
- **P6-3 v2 Stages 0-1** `[AR: grounding]`
  - chunking with offset maps
  - document metadata
  - claim extraction
  - locate + support verification
  - cross-framework claim tagging (D-P6-C)
  - desk-review adapter so P5-4 pre-fill keeps working
- **P6-4 v2 Stage 2** `[AR: scoring boundary]`
  - batched judge
  - closed-set citation
  - deterministic consistency checks
  - `insufficient_evidence` end to end
  - scope-aware multi-framework prompts
  - divergence check
  - framework-aware document categories
- **P6-5 A/B and flip.** Run the P5-9 harness on v2 against the baseline. Flip the default only if D-P6-E holds. Add the injected-document test pack.

### Track 2: Deliverables (runs alongside Track 1)

- **P6-6 Report foundations**
  - period and cut-off model with the approval gate (D-P6-G)
  - fix every D0 defect
  - the sign-off block ships with a free-text preparer/reviewer until Track 4 identity lands, then switches to real users
- **P6-7 Consultant requirement card and review queue.** Needs P6-4 output; can prototype on v1 fields.
- **P6-8 Board report v2**
  - WeasyPrint with Noto fonts
  - DOCX derived from the snapshot
  - XLSX register and tracker
  - standalone Workpaper
- **P6-9 Statement of Applicability, cross-framework roadmap, prior-period comparison in the PDF**
- **P6-10 Stages 3-4**
  - remediation drafting on approval
  - Finding-grounded narrative at report draft

### Track 3: After v2 flips

- Incremental re-analysis on evidence change (E-M6).
- Consultant-override-rate report.
- Retire `GapReport`/`GapItem` writes and the `app/dpdpa/prompts.py` stack (E-M5).
- `web.py` split.
- Whole-client export.

### Track 4: Security and residency (after Track 1 is validated; gate for any real client data, D-P6-I)

- **P6-11 Identity and perimeter** `[AR: security]`
  - User model and login
  - session-derived actor on every audit write, replacing `reviewer_name` and `CONSULTANT_ACTOR` (E-C3)
  - CSRF on all state-changing routes, including HTMX
  - strict CORS
  - `/docs` disabled
  - TLS for any non-localhost deployment
- **P6-12 Data at rest and uploads** `[AR: security]`
  - encrypted database and blobs (SQLCipher or an encrypted volume)
  - encrypted backups, with purge-aware rotation (E-M3)
  - size caps on every upload route
  - magic-byte type checks
  - a real malware scanner behind `scan_blob`
  - parser page and size limits
- **P6-13 Bedrock migration (D-P6-K)**
  - implement the Bedrock Converse backend in `llm_client.py`
  - map each tier to a model **available in `ap-south-1`**, including one vision-capable model
  - **do not use cross-region inference profiles**, which can route requests outside India
  - model availability in Mumbai must be verified at implementation time
  - **rerun P5-9 on the new models before switching**, because a model change is a quality change
- **P6-14 Deploy**
  - fix the compose environment
  - add `.dockerignore`
  - run as non-root
  - WeasyPrint system libraries in the image

### Dependency sketch

```
P5-9 baseline ──────────────────────────────────┐
P6-1 ──► P6-3 ──► P6-4 ──► P6-5 (flip) ◄────────┘ ──► Track 3
P6-2 (DPDPA) ──► P6-4 ;  P6-2 (ISO, NIST) ──► P6-5
P6-4 ──► P6-7 ;  P6-6 ──► P6-8 ──► P6-9 ;  P6-4 + P6-6 ──► P6-10
P6-5 ──► Track 4 (P6-11..14) ──► first real client data
```

### Out of scope / deferred

- ISO clauses 4-10 full pack (P5-7): still deferred. The SoA in P6-9 covers the most-requested ISO artefact.
- GDPR, HIPAA and PCI enablement.
- Postgres: revisit when there is more than one concurrent consultant.
- Mandatory maker-checker (PRD deferred).
- WCAG (D7).

## Resolved questions (2026-09-25)

1. D8 amendment: **approved** (D-P6-C).
2. Security timing: **after pipeline implementation and validation** (D-P6-I, Track 4). The localhost guard is patched now.
3. Test criteria sign-off: **Saqlain.** Defined once per pack version (see "Test criteria lifecycle").
4. Report rendering: **WeasyPrint approved** (D-P6-H).
5. Data residency: **Bedrock `ap-south-1`** instead of redaction (D-P6-K).
