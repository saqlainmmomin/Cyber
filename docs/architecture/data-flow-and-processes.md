# CyberAssess — Data Flow & Process Reference

**Purpose:** a from-the-code explanation of how every feature actually works — the real
algorithms, thresholds, and Claude-call boundaries, not a marketing description. Every
claim below is cited `file:line` against this repo as of 2026-09-12 (commit `cc0894e`).
Where the implementation has a gap, inconsistency, or dead branch, it's called out
explicitly under **Known gaps & inconsistencies** at the end — this doc is meant to be
trustworthy, not flattering.

**How to read this doc:** Part 1 covers the foundation (how one tool supports six
frameworks). Parts 2–9 walk the pipeline in the order an assessment actually moves
through it. Part 10 is the web portal's page-by-page journey. Part 11 rolls up every
subtlety worth remembering into one list.

---

## Part 1 — Multi-Framework Architecture: FrameworkRegistry + Unified Control Clusters (UCC)

Two independent layers let one tool support DPDPA, ISO 27001, GDPR, HIPAA, NIST CSF,
and PCI-DSS without duplicating scoring, UI, or questionnaire logic per framework.

### 1.1 `FrameworkRegistry` — one catalog, one shape

`app/frameworks/registry.py` holds a class-level dict `_frameworks: dict[str, FrameworkDefinition]`
(`registry.py:20`) — a process-wide singleton populated once at startup by
`_register_frameworks()` in `app/main.py:217-232`, which registers all six definitions.
`app/main.py` also runs `_assert_framework_catalog_complete()` right after registration
(`main.py:235-267`), which fails the app's boot loudly if the registered framework IDs
ever drift from the UI's `ENABLED_ASSESSMENT_FRAMEWORKS`/`ROADMAP_FRAMEWORKS` tuples —
a framework can never silently disappear from the UI.

Every framework — statute, ISO annex, or NIST function — is forced into the same
`FrameworkDefinition` dataclass shape (`app/frameworks/schema.py:13-166`):

```
FrameworkDefinition
├─ domains: dict[str, Domain]        # e.g. "governance", "technological"
│   └─ Domain(weight, sections: dict[str, Section])
│       └─ Section(weight, controls: list[Control])
│           └─ Control(id, title, description, reference, criticality, tags)
├─ questions: dict[control_id -> QuestionDef]
├─ scope_questions: list[ScopeQuestion]
├─ red_flag_patterns: list[RedFlagPattern]   # skepticism heuristics fed to Claude
├─ dependencies: dict[control_id -> prerequisite control_ids]
└─ root_cause_clusters: dict                 # groups controls for remediation initiatives
```

Two derived helpers are what let old DPDPA-only code work unmodified for every other
framework: `all_controls_enriched()` (`schema.py:101-121`) flattens the tree with
chapter/section metadata attached, and `as_legacy_framework_dict()` (`schema.py:136-166`)
converts it back into the nested `{domain: {sections: {requirements: [...]}}}` shape the
original DPDPA scoring engine expects — so `scoring.py` needed **no rewrite** when new
frameworks were added; it just consumes "a framework dict," now sourced generically via
the registry.

`app/frameworks/compat.py` is a thin legacy shim (`compat.py:16-43`) exposing
DPDPA-defaulted functions (`get_all_requirements()`, `get_framework_dict()`, etc.) that
proxy straight to the registry — the seam that let pre-multi-framework code migrate
incrementally. Note it isn't universally adopted: `app/routers/reports.py:8` still
imports directly from `app.dpdpa.framework` for one summary endpoint.

**Adding a 7th framework** is "write one `definitions/xyz.py` file that assembles a
`FrameworkDefinition`, then register it" — not "touch scoring, PDF export, and the
questionnaire builder." `app/frameworks/definitions/iso27001.py` is the reference shape:
controls carry `criticality`/`tags`, sections carry a `weight`, and per-control questions
are template-generated (`"Has your organization implemented {title}? ({reference})"`)
rather than hand-authored.

### 1.2 Unified Control Clusters — de-duplicating the questionnaire, not the scoring

`app/frameworks/mappings/clusters.py` holds `CONTROL_CLUSTERS`, a hand-curated list of
dicts, each built via a `_cluster(...)` factory (`clusters.py:30-50`):

```python
{
  "cluster_id": "CLUSTER_001",
  "topic": "Governance Framework And Policy Accountability",
  "primary_question": "Does your organization maintain a documented privacy and "
                       "information security governance framework, approved by "
                       "leadership and reviewed on a defined cadence?",
  "controls": [
      {"framework": "iso27001", "control": "ISO.A5.1"},
      {"framework": "iso27001", "control": "ISO.A5.4"},
      {"framework": "gdpr",     "control": "GDPR.ART24.1"},
      {"framework": "gdpr",     "control": "GDPR.ART24.2"},
      {"framework": "nist_csf", "control": "NIST.GV.OC.03", "delta": "NIST expects governance decisions to reflect legal and regulatory requirements."},
      {"framework": "nist_csf", "control": "NIST.GV.RM.01"},
      {"framework": "pci_dss",  "control": "PCI.12.1", "delta": "PCI DSS requires a comprehensive information security policy."},
      {"framework": "hipaa",    "control": "HIPAA.164.308a1iii", "delta": "HIPAA expects a sanction policy for workforce members who fail to comply."},
      # ... 14 controls total across 5 frameworks
  ],
  "criticality": "critical",
  "domain_group": "governance",
}
```

This single cluster maps **14 controls across 5 of the 6 frameworks** to one merged
question. A `delta` string on a member control becomes an optional per-framework
follow-up (rendered, not a second full question) rather than forcing a duplicate ask.

**Resolution algorithm** — `app/frameworks/cluster_engine.py::resolve_clusters()`
(`cluster_engine.py:113-195`):
- **Single framework selected** → clustering is skipped entirely; every control becomes
  its own `SINGLE.{control_id}` singleton (`cluster_engine.py:87-110,136-142`). No
  merge overhead — a single-framework assessment behaves exactly like the
  pre-multi-framework tool.
- **2+ frameworks selected** → for each `CONTROL_CLUSTERS` entry, keep only member
  controls belonging to the selected frameworks and not scope-excluded
  (`cluster_engine.py:149-171`). If ≥1 control survives, build a live cluster and mark
  those controls "claimed." Any control from a selected framework that no cluster
  claims becomes its own singleton (`cluster_engine.py:190-193`) — the mapping table
  doesn't need 100% coverage; uncovered areas degrade gracefully to per-framework
  questions.

**Where the fan-out happens** (the actual "one answer, many frameworks" mechanism):
1. The questionnaire persists one `QuestionnaireResponse` keyed by `cluster_id`
   (e.g. `CLUSTER_001`), not by per-framework control ID.
2. At analysis time, `_expand_cluster_responses()` (`app/frameworks/prompts.py:56-98`)
   translates that one cluster-keyed answer back into every member framework's native
   control IDs before building each framework's own Claude prompt — the user answered
   once, but each framework's per-framework Claude call still receives its own
   correctly-labeled control assessment.
3. At scoring time, `app/services/scoring.py::_build_cluster_verdicts()` (`scoring.py:54-110`)
   independently re-groups legacy per-control `GapItem` rows by `cluster_id` and takes
   the **worst-case status** across the cluster's members
   (rank order `unknown < not_implemented < partial < implemented < not_applicable`,
   `scoring.py:58-64,84-97`) — so a DPDPA control's score can be driven by an answer
   that was nominally asked as an ISO/NIST/GDPR question, if they landed in the same
   cluster. This scoring-time dedup is currently gated to `framework_ids == ["dpdpa"]`
   only (`scoring.py:174-177`) — see Known gaps.

---

## Part 2 — Scope & Applicability (Phase 0)

**Trigger:** `POST /assessments/{id}/scope/save` (`app/routers/web.py:379-423`), driven
by `SCP.1`–`SCP.5` questions (`app/dpdpa/scope_questions.py`) plus each selected
framework's own `scope_questions` (`web.py:396-402`).

**Algorithm** — `compute_scope()` (`app/services/scope_profiler.py:45-119`), pure
deterministic Python, no Claude call:

| Scope answer | Excludes requirement IDs (if answer is "no") |
|---|---|
| `SCP.1` cross-border transfers | `CB.TRANSFER.1/2/3` |
| `SCP.2` processes children's data | `CH2.CONSENT.5`, `CH4.CHILD.1/2/3` |
| `SCP.3` Significant Data Fiduciary status | `CH4.SDF.1/2/3/4` (kept if answer is `"possibly"`) |
| `SCP.5` uses third-party processors | `CH2.SECURITY.3` |

**Deliberate bias toward inclusion:** an `"unsure"` answer is treated as "possibly
applicable" and the requirement is **kept in scope** — only an explicit "no" excludes it
(`scope_profiler.py:72-75`). This directly sets `assessment.applicable_requirements`,
which forces excluded questions to `status="skipped"` before any desk-review or
screening logic runs (`app/services/question_engine.py:217-221`).

Note: `compute_scope()` accepts a `company_size` parameter but never reads it in the
function body — scope exclusion is driven solely by the 5 SCP answers
(`scope_profiler.py:45-68`).

**Multi-framework caveat:** scope-based exclusion is currently a no-op for
multi-framework assessments — `_build_multi_framework_questionnaire()` explicitly
passes `excluded=None` with the comment "UCC engine uses include-list differently — pass
None for now" (`app/services/question_engine.py:65`). Every control from every selected
framework appears regardless of scope answers.

---

## Part 3 — Desk Review & Document Processing

### 3.1 Upload → text extraction

**Entry points:** `POST /api/assessments/{id}/documents` (`app/routers/documents.py:12-64`)
or the HTMX form (`app/routers/web.py:496-551`).

1. File type is derived purely from the filename extension
   (`detect_file_type`, `app/services/document_processor.py:223-232`). Accepted:
   `pdf, docx, png, jpg, jpeg, webp`; anything else → HTTP 400.
2. Saved to `uploads/{assessment_id}/{uuid8}_{filename}`.
3. Text extraction dispatches by type (`extract_text`, `document_processor.py:41-50`):
   - **PDF** (`_extract_pdf`, lines 53-70) — `pdfplumber`; extracts page text and
     converts every table's rows into `"cell1 | cell2 | ..."` blocks so tabular data
     (e.g. retention schedules) survives as text.
   - **DOCX** (`_extract_docx`, lines 73-85) — `python-docx`; paragraphs + tables
     (`" | "`-joined cells).
   - **Images** (`_extract_image`, lines 170-220) — **no OCR library**; a live Claude
     vision call transcribes visible text verbatim and adds a 2–3 sentence compliance
     summary. This is the only extraction path that calls an LLM, and the only one with
     no word-limit truncation applied (naturally short, capped by `max_tokens=1500`).
4. Empty/whitespace-only extraction (e.g. a scanned, non-OCR'd PDF) → HTTP 422 asking
   the user to re-upload as an image so the vision path can run instead — there's no
   automatic OCR fallback.
5. **Per-document word cap**: `_truncate()` (lines 88-99) keeps only the first
   `settings.max_document_words` words (default **5000**, `app/config.py:18`), applied
   to PDF/DOCX only.
6. First upload flips `assessment.status` from `"created"` to `"documents_uploaded"`
   (`documents.py:51-52`).

### 3.2 Running desk review — `run_desk_review()` (`app/services/desk_review.py:28-140`)

Synchronous, blocking, in-request (no queue/background task):

1. Requires ≥1 uploaded document (else HTTP 400).
2. Creates or **destructively resets** the assessment's `DeskReviewSummary` — any prior
   `DeskReviewFinding` rows are deleted before re-running (full wipe-and-replace, not
   incremental). Status → `"analyzing"`, committed immediately (visible to a polling UI
   before the Claude call even starts).
3. **Cross-document word budget**: `_truncate_documents()` (`desk_review.py:229-246`)
   enforces `settings.max_total_document_words` (default **20000**,
   `app/config.py:19`) across *all* documents combined, in upload order. Once the
   budget is exhausted, any remaining documents are **dropped entirely**, not just
   trimmed — upload order determines which documents make it into the analysis.
4. **Single Claude call** (`_call_claude_desk_review`, `desk_review.py:143-174`):
   `model=settings.claude_model`, `max_tokens=16000`, `temperature=0`. The system
   prompt (`app/dpdpa/prompts.py:213-378`) is cached (`cache_control: ephemeral`) since
   it's static per-DPDPA content, and instructs the model to perform four analysis
   levels for every document:
   - **Document Catalog** — type, DPDPA chapters covered, 1–2 sentence summary.
   - **Evidence Mapping** — exact verbatim quotes per requirement ID, with filename +
     location.
   - **Absence Detection** — explicitly what's missing per requirement (the prompt
     forbids vague absence text; it demands citation of the specific missing clause).
   - **Signal Detection** — an enumerated red-flag taxonomy the model must aggressively
     apply: `gdpr_copy_paste` (EU-law language like "data subject", "legitimate
     interest"), `template_artifact` (`[Company Name]` placeholders, mismatched
     boilerplate), `ccpa_copy_paste` ("Do Not Sell...", "CCPA/CPRA"), `buried_consent`
     (consent hidden in T&Cs, pre-checked boxes), `missing_timeline` (no 72-hour breach
     notice per Section 8(6)), `scope_gap` (industry-relevant or children's data not
     addressed).

   Two governing skepticism rules baked into the prompt: **"policy ≠ implementation"**
   (a written policy alone can't score above `partially_compliant` without evidence of
   operational follow-through) and **"absence of evidence is evidence of absence"**
   (silence on a requirement → `non_compliant`/`absent`, never assumed compliant).

   `coverage_summary` output has exactly four levels per requirement:
   `adequate` (well-addressed) / `partial` (mentioned, has gaps) / `absent` (explicitly
   missing despite a relevant document existing) / `not_covered` (no relevant document
   at all). **This is entirely the model's judgment** — CyberAssess does not
   independently compute coverage from the finding counts.

5. **Persisting findings** (`_persist_findings`, `desk_review.py:177-226`) — one flat
   `DeskReviewFinding` table, discriminated by `finding_type`:
   - `evidence` — one row per quote in `evidence_map`; `severity` hard-coded `"info"`.
   - `absence` — one row per item in `absence_findings`; `severity` is model-assigned
     (default `"medium"`); no source quote (there's nothing to cite for an absence).
   - `signal` — one row per flag in `signal_flags`; `severity` model-assigned. **A
     signal that logically applies to multiple requirements is linked to only the
     first** requirement ID in the model's list (`req_ids[0]`, `desk_review.py:218`) —
     a lossy simplification the questionnaire engine has to work around (see §5.2).
     The model's `flag_type` (e.g. `gdpr_copy_paste`) is **not stored as its own
     column** — it only survives if mentioned inside the free-text `content`.
6. On success: status → `"completed"`, then `persist_document_answers()` (auto-fill,
   §3.3) runs as a best-effort side effect — its failure is logged but does **not**
   flip the desk review itself to `"error"`.
7. Any exception from the Claude call or from persistence sets status → `"error"` with
   `error_message` captured; no findings are left partially written.

### 3.3 Auto-fill from desk review — `persist_document_answers()` (`app/services/auto_answer.py:28-141`)

For every `(requirement_id, coverage_level)` pair in the desk review's coverage summary:

1. **Skip** unless `coverage_level in ("adequate", "partial")` — `absent`/`not_covered`
   are never auto-answered.
2. **Suppress absolutely** if that requirement has any `signal` or `absence` finding —
   checked *before* anything else. Signals/absences always override a positive
   coverage label; "documents describe intent, not operational reality."
3. **Never overwrite** a response with `answer_source` in
   `("human", "human_override", "document_confirmed")` — anything a human has touched
   is permanently protected from a later desk-review re-run.
4. Map: `adequate → fully_implemented` (confidence `high`); `partial →
   partially_implemented` (confidence `medium`) — the entire mapping is a two-branch
   ternary, nothing more sophisticated.
5. Notes are built from up to 3 evidence quotes (200 chars each); if a prior
   `answer_source == "document"` row exists it's updated in place (handles re-runs),
   otherwise a new row is inserted with `answer_source="document"`.

Every pre-filled answer is worded in the UI as needing confirmation
("Evidence found in your documents. Please review and confirm.") — nothing is ever
auto-submitted as final. The save handler transitions `answer_source` to
`document_confirmed` (re-submitted unchanged) or `human_override` (changed) once a
human interacts with it.

### 3.4 Evidence checklist export — *not* fed by desk review

Worth flagging explicitly: the "evidence checklist" PDF/DOCX
(`app/utils/evidence_checklist_export.py`) is a **pre-assessment document request
list** derived purely from the scope answers (`compute_scope`'s `_build_evidence_checklist`,
`scope_profiler.py:99-106,122+`) — required/recommended documents by scope flag
(cross-border, children's data, SDF, processors). It is meant to be sent to the client
*before* any documents exist, and does not read from desk-review findings at all.

---

## Part 4 — Context Profiling (Phase 1)

**Trigger:** a 14-question, 4-block wizard (`app/dpdpa/context_questions.py`), saved via
`POST /assessments/{id}/context/save` (`app/routers/web.py:634-682`).

`derive_risk_profile()` (`app/services/context_profiler.py`) is a **Claude call** that
turns the raw context answers into a structured `context_profile`: `risk_tier`
(`HIGH`/`MEDIUM`/`LOW`), `priority_chapters` (ordered list), `likely_not_applicable`
(requirement IDs), plus flags (`sdf_candidate`, `cross_border_transfers`,
`processes_children_data`, `industry_context`, `timeline_pressure`, `framing_notes`).
This profile is stored on `assessment.context_profile` and consumed downstream by:

- **The base questionnaire** (`app/dpdpa/questionnaire.py::_compute_relevance()`,
  lines 174-188) — a `relevance_weight` multiplier (`×1.3` if in the top-2 priority
  chapters, `×1.2` if critical+HIGH risk, `×0.3` if flagged not-applicable) and a
  `context_note`. **Both are currently display-only metadata** — nothing in
  `question_engine.py` filters or reorders questions by `relevance_weight`.
- **Adaptive tiering** (Part 5) — `risk_tier` is the sole driver of whether a
  non-deepened critical/high question gets escalated to the `"deep"` tier.
- **Gap analysis prompts** — injected as a "risk profile" block in Call 2's user prompt
  (Part 6).

---

## Part 5 — Domain Screening (Phase 3, optional)

**Purpose:** infer likely answers for all 41 DPDPA requirements from just 9 broad
domain-level questions (Consent Management, Notice & Transparency, Purpose Limitation,
Accuracy, Security, Breach Notification, Data Subject Rights, Governance/SDF/Children,
Cross-Border — `app/dpdpa/prompts.py:555-670`), each domain declaring which requirement
IDs it `covers`.

**Algorithm** — `run_screening_pass()` (`app/services/screening.py:31-86`):

1. One Claude call (`model="claude-sonnet-4-6"`, `max_tokens=4096`) with explicit
   inference rules in the system prompt: "not started"/"no process" answers → infer
   `non_compliant` at `high` confidence; vague answers → `medium`/`low` confidence;
   requirements not covered by any of the 9 domains → `not_assessed` at `low`
   confidence.
2. `_parse_inferences()` (`screening.py:89-138`) validates every requirement ID is
   real, normalizes invalid status/confidence values to safe defaults, and **backfills
   any requirement missing from the response** to `not_assessed`/`low` — all 41 IDs are
   always present in the output.
3. Two independent consumers of the same result:
   - **DB persistence** (`_persist_inferred_answers`, lines 149-203) — creates
     `QuestionnaireResponse` rows with `answer_source="inferred"`, but **only** when
     `confidence == "high"` AND status is `compliant` or `partially_compliant`.
     `non_compliant` findings are **deliberately never auto-persisted**, even at high
     confidence — a human must confirm every negative finding.
   - **Live re-modulation** at render time (`_apply_screening`,
     `app/services/question_engine.py:446-492`) — re-applies the same rules to
     whatever's still `"active"` after desk-review modulation (desk review always takes
     priority): `high` confidence compliant/partial → pre-fill (tagged
     `pre_fill_source="inferred"`, a distinct "purple badge" from document-sourced
     pre-fills); `low` confidence (any status) → force `"deepened"`; `medium` confidence
     → stays active with a hint note attached.

---

## Part 6 — Adaptive Questionnaire & Tiering

### 6.1 Assembly — `build_adaptive_questionnaire()` (`app/services/question_engine.py:152-296`)

Recomputed fresh on **every page load** — nothing about the questionnaire's *shape* is
persisted; only the underlying answer/finding rows are. Order of operations:

1. **Framework routing**: if `selected_frameworks != ["dpdpa"]`, delegate entirely to
   the UCC cluster-based multi-framework builder (§6.3) and return early —
   **desk-review modulation, screening modulation, and adaptive tiering do not run at
   all on the multi-framework path.**
2. Build base DPDPA questions (`app/dpdpa/questionnaire.py::build_questionnaire()`) and
   industry questions (`app/dpdpa/industry_questions.py`) — the industry bank is keyed
   by `INDUSTRY_BANK_MAP`, and only `it_services→it_saas` (13 questions) has a bespoke
   bank; every other industry falls back to the same 5-question `generic` bank.
3. **Scope exclusion first** — any question whose requirement ID isn't in
   `applicable_requirements` is force-skipped before desk-review/screening logic ever
   runs.
4. **Desk-review modulation** (`_modulate_question`, lines 370-443) — evaluated in this
   priority order, **signals and absences always override a positive pre-fill**:
   1. Absence finding for this requirement → `status="deepened"`, follow-ups enabled.
   2. Signal finding for this requirement → `status="deepened"`, follow-ups enabled.
   3. (Only if neither fired) coverage `adequate`/`partial` **and** ≥1 evidence
      citation exists → pre-fill (`fully_implemented`/`high` or
      `partially_implemented`/`medium` respectively). A coverage label alone, with zero
      supporting evidence quotes, does **not** pre-fill.
   5. Otherwise → stays `active` (evidence attached as context if any exists).
5. **Screening modulation** applies only to questions still `active` after step 4
   (§5, "Two independent consumers").
6. **Coverage-guarantee pass** (lines 249-274) reinstates any skipped-but-uncovered
   requirement — except this logic targets a code path (`_modulate_question` setting
   `status="skipped"`) that no longer exists in the current implementation, since only
   scope exclusion sets `"skipped"` now, and scope-skips are explicitly excluded from
   reinstatement. **This is effectively dead code** (flagged in Known gaps).
7. **Tiering** (§6.2) is assigned to every question.
8. Grouped into sections (base questions by `chapter.section`, industry questions by
   `industry.category`) for rendering.

### 6.2 Adaptive Tiering — `app/services/tier_engine.py::assign_tier()` (lines 16-54)

First-match-wins rule table — this governs how much UI attention a question gets, **not**
whether it's shown:

| Order | Condition | Tier | UI treatment |
|---|---|---|---|
| 1 | `status == "skipped"` | `skip` | hidden / N-A |
| 2 | `status == "pre_filled"` and not critical | `light` | compact confirm card (~30s) |
| 3 | `status == "pre_filled"` and critical | `standard` | still gets full attention (~2 min) |
| 4 | `status == "deepened"` | `deep` | full question + evidence panel (~5 min), **regardless of criticality/risk_tier** |
| 5 | `criticality=="critical"` and `risk_tier=="HIGH"` | `deep` | |
| 6 | `criticality=="high"` and `risk_tier=="HIGH"` | `deep` | |
| — | default | `standard` | |

For `MEDIUM`/`LOW`-risk organizations, criticality alone never escalates a question to
`deep` — only a desk-review/screening-driven `"deepened"` status does. This is the
concrete mechanism by which an org's risk profile changes question *depth* (attention),
while scope/desk-review/screening control question *presence and status*.

### 6.3 Multi-framework questionnaire (`app/frameworks/questionnaire_builder.py`)

`build_multi_questionnaire()` resolves UCC clusters (Part 1.2) and converts each into one
merged question via `_cluster_to_question()` (`questionnaire_builder.py:108-176`):
`criticality` = the highest-ranked criticality among member controls;
`relevance_weight` gets a `×1.2`/`×1.3` bump for critical+HIGH-risk clusters or
cross-border/children's-data clusters matching the org's context profile; per-framework
`delta` strings become optional follow-up sub-questions. **Every question on this path
is hardcoded** `status="active"`, `tier="standard"`, pre-fill fields `None` — confirming
there is no desk-review pre-fill, no screening pre-fill, and no adaptive tiering for
multi-framework assessments today.

### 6.4 Completion gate before analysis is allowed

`app/routers/analysis.py:99-129`: `completion_ratio = answered / expected` (expected =
base DPDPA IDs, or UCC cluster IDs for multi-framework, excluding follow-up/industry
prefixes). If `< 80%` **and no documents were uploaded** → HTTP 400, blocked. If
`< 80%` but **at least one document exists** → merely logged as a warning, analysis
proceeds anyway. So the real gate is **"≥80% answered OR ≥1 document uploaded"** —
uploading any document bypasses the questionnaire-completion requirement entirely,
independent of how good that document's desk-review coverage actually was.

---

## Part 7 — Gap Analysis: the Claude Engine

Entry point: `POST /api/assessments/{id}/analyze` → `trigger_analysis()`
(`app/routers/analysis.py:31-219`), which branches on
`is_multi = len(selected_frameworks) > 1 or selected_frameworks != ["dpdpa"]`.

### 7.1 Legacy single-framework (DPDPA) path — the true "two-call" architecture

`run_gap_analysis()` (`app/services/claude_analyzer.py:55-140`):

- **Call 1 — Evidence extraction** (grounding). Only runs if there are documents *and*
  desk review hasn't already produced evidence for these requirements — if
  `_evidence_from_desk_review()` finds prior evidence, **Call 1 is skipped entirely**
  and that evidence is reused (a real cost-saving branch, not just a doc claim).
  When it does run: system prompt "extract exact quotes...be precise, quote verbatim,"
  `max_tokens=8192`, `temperature=0`, output `{"evidence": {req_id: [quotes...]}}`
  covering every requirement. On any failure it fails soft — logs a warning and returns
  `None`, so Call 2 falls back to raw document text instead of extracted quotes.
- **Call 2 — Gap analysis**. System prompt uses **Anthropic prompt caching**: the
  persona is uncached, but the full DPDPA requirements text + instructions block is
  marked `cache_control: ephemeral` — this is the ~90% cost reduction referenced in the
  module docstring, since that block is identical across every analysis run. User
  prompt assembles, in order: org profile → scope exclusions (forces `not_applicable`
  for out-of-scope IDs) → risk profile (from context profiling) → desk-review findings
  → questionnaire responses → **either** Call 1's evidence quotes **or** raw document
  text if no evidence exists. `max_tokens=16384`, `temperature=0`. Output: one
  assessment object per requirement — `compliance_status, current_state,
  gap_description, risk_level, remediation_action/priority/effort, timeline_weeks,
  maturity_level (0-5), root_cause_category, evidence_quote`.
- **Why two calls, not one**: Call 1's sole purpose is evidence grounding — pulling
  verbatim quotes so Call 2's assessment is anchored in cited text rather than
  paraphrase, and so Call 2's (cached) prompt doesn't need to re-embed raw document text
  every time evidence already exists. It's a genuine producer→consumer pipeline, not two
  independent purposes.
- JSON parsing (`_parse_json_response`) strips markdown fences then `json.loads`s; a
  parse failure raises with a 500-char snippet, propagating to the router as an HTTP 500
  with `assessment.status="error"`.

### 7.2 Multi-framework path — actually N+2 calls, not two

`run_multi_framework_analysis()` (`claude_analyzer.py:237-393`) is a 3-stage pipeline:

1. **Evidence extraction** — identical logic to Call 1 above, run **once**, shared
   across every selected framework (not once per framework) — itself a Claude-call
   dedup.
2. **Per-framework gap analysis** — one Claude call **per selected framework**, each
   with its own persona (`_FRAMEWORK_PERSONAS`), its own controls reference block
   (cached independently), and its own red-flag/skepticism guidance derived from that
   framework's `red_flag_patterns`. Before building each framework's prompt,
   `_expand_cluster_responses()` translates the user's cluster-keyed questionnaire
   answers back into that framework's native control IDs (Part 1.2, step 2) — this is
   where UCC dedup at collection time gets reconciled with per-framework, per-control
   scoring at analysis time. Calls are **streamed** (unlike Call 2 above) specifically
   to avoid server disconnects on large (~50KB) responses. A failure in one framework's
   call is isolated — it doesn't abort the others; that framework just gets a stub
   "Analysis failed" result.
3. **Cross-framework synthesis** — only if 2+ frameworks were selected and at least one
   succeeded: one lightweight call combining each framework's executive summary + gap
   counts + top-5 critical gaps into a `unified_executive_summary`,
   `cross_framework_themes`, `prioritized_recommendations`. Non-fatal on failure — the
   report falls back to concatenating each framework's own summary.

### 7.3 Legacy vs. multi-framework: the concrete divergences

| | Legacy (DPDPA-only) | Multi-framework |
|---|---|---|
| Claude calls | 1–2 (evidence + gap analysis) | 1 (shared evidence) + N (per framework) + 1 (synthesis) |
| Scoring | `compute_scores()` — hardcoded DPDPA framework dict | `compute_framework_scores()` per framework + `compute_unified_maturity()` |
| Overall score stored | DPDPA's own weighted-chapter score | **Equal-weight mean** of each framework's own overall score (not re-derived from raw items) |
| `GapItem.framework_id` | Hardcoded literal `"dpdpa"` | Threaded through from the per-framework loop variable |
| `chapter`/`requirement_title` | Static lookup dicts built once at module load | Live lookup via `FrameworkRegistry.get(fw_id).all_controls()` each time |
| Initiatives | `generate_initiatives()` — DPDPA-only root-cause rules | `generate_multi_framework_initiatives()` — merges gaps across frameworks, tags `frameworks_addressed` |
| Failure isolation | One exception aborts the whole request | Per-framework try/except; one framework failing doesn't kill the others |

`evidence_confidence` (stored per `GapItem`) is computed identically on both paths by a
small deterministic closure (duplicated, not shared, between the two code paths):
`strong` = desk-review evidence **and** a questionnaire response both exist; `moderate`
= desk-review evidence **or** (a response **and** documents were uploaded); `weak` =
otherwise. This is code-side heuristic, entirely separate from anything Claude outputs.

---

## Part 8 — Deterministic Scoring (`app/services/scoring.py`)

Scoring is intentionally **never done by Claude** — it's plain arithmetic over the
`compliance_status` field Claude assigned per requirement.

### 8.1 The formula

```
STATUS_SCORES = {"compliant": 100, "partially_compliant": 50, "non_compliant": 0}
# not_assessed / not_applicable: excluded from scoring entirely (not averaged in)
```

Aggregation chain, exactly as coded (`compute_scores()`, `scoring.py:308-385`):

1. **Requirement** → its raw status score (0/50/100), or excluded if
   not_assessed/not_applicable.
2. **Section** → plain (unweighted) average of its scoreable requirements. A section
   with zero scoreable requirements is dropped entirely from the chapter calculation.
3. **Chapter** → **weighted** average of its section averages, weight = each section's
   configured `weight` in the framework definition.
4. **Overall** → **weighted** average of *applicable* chapters only (a chapter with zero
   scoreable sections is marked `applicable=False` and excluded), weight = each
   chapter's configured `weight`.
5. **Rating labels** — first threshold met, checked descending:
   `80 → Compliant`, `60 → Partially Compliant`, `40 → Needs Significant Improvement`,
   `0 → Non-Compliant`.

`compute_framework_scores()` is the generic multi-framework analog, identical formula,
sourcing the framework tree from the registry instead of a hardcoded DPDPA constant.

### 8.2 What does *not* affect the score

- **`risk_level`** (critical/high/medium/low) plays **no role** in the numeric formula
  anywhere. Its only use is a display aggregate — counting critical/high gaps for
  dashboard tiles — and indirectly through `remediation_priority` (a separate field)
  for initiative ordering.
- **`maturity_level`** (Claude's 0–5 CMMI-style self-rating) is also **not** an input to
  `compute_scores()`. It feeds a *separate* cross-framework view,
  `compute_unified_maturity()`, which averages `maturity_level` per `root_cause_category`
  across frameworks — a distinct concept from the 0–100 compliance score.

There is a **second, independent 0–5 maturity vocabulary** used by a newer cluster-first
scoring path (`_build_cluster_verdicts`/`score()`, `scoring.py:33-51,54-215`), derived
purely from `compliance_status` (not from Claude's own `maturity_level` field) via
`MATURITY_STATUS_SCORES` and an `M0`–`M5` rating. This path is explicitly restricted to
`framework_ids == ["dpdpa"]` — it raises `NotImplementedError` for any other framework
selection, "until their analyzer output is cluster-backed" (`scoring.py:165-177`). It is
not currently what the multi-framework router path uses.

---

## Part 9 — Review Gate, RFI Generation, Follow-up Questions, and Remediation

### 9.1 Review gate — the mandatory human-in-the-loop checkpoint

Two independent state machines exist on the same data:

- **`GapItem.review_status`** (default `"draft"`): can be set to `"accepted"` or
  `"rejected"` via `PATCH /api/assessments/{id}/review/items/{item_id}`
  (`app/routers/review.py:58-103`), which also lets a reviewer directly overwrite
  `compliance_status`/`gap_description`/`risk_level` in place — the original AI output
  is preserved separately in parallel `ai_*` columns for audit/diff.
- **`Assessment.review_status`**: `None → "under_review"` (set the moment any item is
  first dispositioned) → `"approved"` (`POST .../review/approve`) or `"rejected"`
  (`POST .../review/reject`, no precondition). **Approval is blocked** with HTTP 400 if
  *any* gap item is still `NULL`/`"draft"` — every finding must be explicitly
  dispositioned (accepted **or** rejected; not required to all be accepted) before
  approval succeeds.

**`require_review_approval()`** (`app/utils/review_gate.py:7-17`) is the single guard
enforced at every download/release endpoint: 403 unless
`assessment.review_status == "approved"` (`"under_review"` and `"rejected"` are both
blocked identically). It gates: the report JSON API, report summary, board PDF export,
RFI PDF/DOCX download, and cross-assessment comparison (**both** assessments in a
comparison must be approved). It does **not** gate viewing/dispositioning findings
themselves or running analysis — only releasing a finished artifact.

### 9.2 RFI (Request for Information) generation

`generate_rfi()` (`app/services/rfi_generator.py:35-91`), triggered by
`POST /assessments/{id}/generate-rfi`.

**Eligibility** — two sources, deduplicated by `requirement_id` only:
- Gap items where `compliance_status` is **not** `compliant` or `not_assessed`
  (effectively: non-compliant and partially-compliant items qualify).
- Desk-review **absence** findings not already covered by a gap item.

**Priority** — a deterministic rule table (`_compute_priority`, lines 156-167),
evaluated top-down: `Critical` if `risk_level=="critical"` or (non-compliant **and**
`remediation_priority<=1`); `High` if `risk_level=="high"` or non-compliant; `Medium` if
partially-compliant; else `Low`. Desk-review-absence items bypass this and are
hardcoded `Medium` priority regardless of actual severity. Suggested response deadline
follows priority: Critical=1wk, High=2wk, Medium=3wk, Low=4wk (absence items hardcoded
to 4wk).

**Claude enrichment** — one call, `temperature=0.2`, asks only for the human-facing
`evidence_requested` text, an `introduction`, and `response_instructions` per item
(the priority/deadline/eligibility logic above is *not* delegated to Claude). On JSON
parse failure it degrades gracefully to templated fallback text rather than failing the
whole RFI.

**Persistence & export**: one `RFIDocument` row per assessment (unique constraint) —
regenerating **deletes and replaces** the prior RFI; there's no version history. Export
(`app/utils/rfi_export.py`) groups items by chapter and color-codes priority
(Critical=red, High=orange, Medium=yellow, Low=green) in the PDF; the DOCX groups
identically but renders priority as plain text.

### 9.3 Follow-up questions — deterministic trigger, Claude-generated text

Fired live as the user answers the questionnaire
(`POST /assessments/{id}/questionnaire/followup`, `app/routers/web.py:894-958`).

**Whether to trigger** is pure deterministic logic (`_assess_trigger`,
`app/services/followup_engine.py:101-151`), evaluated in this order:

1. `"fully_implemented"` **and** desk review has both evidence *and* a contradicting
   note → contradiction, 2 follow-ups.
2. `"not_applicable"` → **never** followed up, regardless of any contradicting evidence.
3. Desk-review evidence exists **but** the answer claims no implementation
   (`not_implemented`/`planned`) → strongest trigger, 3 follow-ups (checked before the
   plain "weak answer" rule below).
4. `not_implemented`/`planned` without contradicting evidence → 2 follow-ups if
   critical/high criticality, else 1.
5. `partially_implemented` → 2 follow-ups if critical, or if desk review flagged a
   signal note; else 1.
6. Everything else → none.

Once triggered, the actual question **text** is Claude-generated (`temperature=0.3`,
`max_tokens=512`), fed the original question, the trigger's reason, up to 3 desk-review
evidence excerpts, and asked for exactly `max_count` follow-ups as JSON. Any failure —
network, parse — degrades to an empty list; follow-up generation never blocks
questionnaire completion (the router itself also swallows exceptions and returns an
empty fragment).

### 9.4 Remediation tracking

`GapItem.remediation_status ∈ {open, in_progress, closed, accepted_risk}`, default
`"open"`. `PATCH /api/assessments/{id}/gap-items/{item_id}/remediation`
(`app/routers/remediation.py:46-115`) applies a **partial update with no transition
validation** — any status can be set from any other status; there's no state-machine
guard.

- Setting `"closed"` stamps `remediation_closed_at` **only if not already set** —
  re-closing doesn't reset the original close date.
- Setting **any other status** unconditionally **clears** `remediation_closed_at` —
  there's no separate "reopen" action; moving out of `"closed"` is just a normal PATCH.
- `"accepted_risk"` is a parallel terminal state to `"closed"` but does **not** stamp a
  close date — risk-accepted items are excluded from close-date tracking even though
  they're functionally resolved.
- No cross-check exists between `remediation_status` and `review_status` or
  `compliance_status` — nothing stops closing remediation on an item still in
  `review_status="draft"`. These are entirely independent state machines on the same
  row.

---

## Part 10 — Report Generation & the Full Web Portal Journey

### 10.1 Board-ready PDF (`app/utils/pdf_export.py::generate_pdf`)

Sections, in order, and their data source:

1. **Cover page** — dynamic title (DPDPA-only / single named framework / "Multi-
   Framework Compliance"), score ring, summary stats, per-chapter score bars.
2. **Executive Dashboard** — 4 KPI cards, compliance distribution bar, an "Assessment
   Areas" heatmap per chapter, first 600 chars of the executive summary.
3. **Critical & High Risk Gaps** — filtered to `risk_level in (critical, high)` and not
   compliant, sorted by risk then remediation priority.
4. **Remediation Roadmap** — a 4-segment priority timeline, gap items grouped by
   `remediation_priority`.
5. **Strategic Initiatives** *(only rendered if any initiatives exist)* — root-cause
   category, suggested approach, combined effort/timeline/budget band.
6–7. **Appendix: Detailed Findings by Chapter** — compliant items get a one-liner;
   everything else gets a full card with evidence quotes.
8. **Appendix: Scope & Limitations** — wording branches on DPDPA-only vs. multi
   ("41 requirements across six chapters" vs. a generic "{N} requirements across
   {frameworks}").
9. **Methodology** — DPDPA-only path hardcodes the six chapter weights (30/20/20/10/10/10%);
   multi-framework path states each framework "retains its own internal weighting."

The generator branches on exactly two flags computed up front —
`dpdpa_only = selected_frameworks == ["dpdpa"]` and `has_dpdpa` — everywhere else it
operates generically over `gap_items`/`chapter_scores`, which is why one PDF generator
serves all six frameworks without per-framework branching in the bulk of the code.

**Report API surface** (`app/routers/reports.py`): `/report` (legacy shape),
`/report/summary` (condensed), `/report/full` (per-framework breakdown, resolves each
framework's name via the registry, groups gap items by `framework_id`), `/report/pdf`
(the export above), `/compare/{other_id}` (cross-assessment delta, requires both
assessments `completed` **and** `approved`). Every one of these except the raw
comparability check is gated by `require_review_approval`.

### 10.2 The full assessment lifecycle, as pages/routes

The portal is effectively a single-page-per-assessment HTMX app — most "steps" below are
`?tab=` query params or HTMX partials fetched into `GET /assessments/{id}`, not separate
page navigations.

1. **Dashboard** (`GET /`) → **New assessment** (`GET /assessments/new`) — framework
   picker shows all 6 registered frameworks, but only `dpdpa, iso27001, nist_csf`
   (`ENABLED_ASSESSMENT_FRAMEWORKS`) are selectable; `gdpr, hipaa, pci_dss`
   (`ROADMAP_FRAMEWORKS`) are shown disabled. Submitting with a disabled framework
   selected is rejected server-side too, not just hidden in the UI.
2. **Create** (`POST /assessments`) — requires ≥1 framework; redirects to the hub.
3. **Scope tab** — saves scope answers, computes `applicable_requirements`, advances
   status `created → scoped`. Evidence checklist export is available here (optional).
4. **Document upload** *(optional)* — accepts files, advances status to
   `documents_uploaded` on first upload; deletable individually.
5. **Desk review** *(optional, needs step 4)* — polled via a status endpoint
   (`not_started → analyzing → completed/error`); feeds the questionnaire's pre-fill.
6. **Context questions** — 4-block wizard; saves `context_profile`, advances status to
   `context_gathered`.
7. **Domain screening** *(optional)* — 9-question pass; feeds pre-fill/deepening.
8. **Adaptive questionnaire** — assembled fresh per Part 6; supports resume (loads
   existing answers), inline follow-ups (Part 9.3), and cluster-based multi-framework
   rendering.
9. **Run analysis** — synchronous call to `trigger_analysis()` (Part 7); status →
   `analyzing` → `completed`/`error`, polled by the frontend.
10. **Gap report** — `view=combined` vs `view=per_framework`, defaulting by whether the
    assessment is multi-framework; surfaces critical findings, quick wins, remediation
    counts, and whether an RFI already exists.
11. **Review / approval** — shows draft items pending sign-off; this is the enforcement
    point behind every gated download.
12. **RFI / remediation** *(optional)* — generate and download the RFI; track
    remediation status per gap item.
13. **PDF export** — requires `review_status == "approved"`.
14. **Comparison** *(optional)* — cross-assessment delta, both sides must be approved.

**Gating summary:** framework availability (enabled vs. roadmap) is a hard server-side
check, not just a UI hint; scope and context are the only optional-looking steps that
actually flip `assessment.status` and feed scoring/questionnaire logic; document upload,
desk review, screening, and RFI generation are all skippable without blocking progress
to analysis and reporting; the review-approval gate is the single mandatory checkpoint
between AI-drafted findings and any client-facing deliverable.

---

## Known gaps & inconsistencies (surfaced during this trace, not hidden)

Flagging these explicitly since understanding the *actual* algorithm means understanding
where it's incomplete or inconsistent, not just where it works cleanly:

1. **Multi-framework assessments get none of the adaptive machinery.** Desk-review
   pre-fill, screening pre-fill, and adaptive tiering are entirely DPDPA-only-path
   features today (Part 6.1, 6.3). A multi-framework assessment's questionnaire is
   uniformly `active`/`standard` regardless of uploaded documents or screening answers.
2. **Scope exclusion doesn't apply to multi-framework questionnaires** — the exclusion
   list is passed as `None` with a "for now" comment (Part 2).
3. **The cluster-first `score()`/maturity-verdict path is DPDPA-only** and raises
   `NotImplementedError` for any other framework selection — it exists in parallel with,
   but isn't wired into, the multi-framework router path (Part 8.2).
4. **The coverage-guarantee reinstatement logic in `question_engine.py` targets a dead
   code path** — it was written to un-skip desk-review-skipped questions, but
   `_modulate_question` no longer ever produces `status="skipped"` (only scope exclusion
   does now, and that's explicitly excluded from reinstatement) (Part 6.1, step 6).
5. **A desk-review signal tied to multiple requirements is persisted against only the
   first one** (`req_ids[0]`) — the questionnaire engine has to separately re-derive
   signal coverage via keyword matching on finding text to compensate for industry
   questions (Part 3.2, step 5).
6. **`compute_scope()` accepts `company_size` but never uses it** — scope exclusion is
   driven solely by the 5 scope answers (Part 2).
7. **Only the IT/SaaS industry has a bespoke question bank** — every other industry
   (fintech, healthcare, e-commerce, etc.) currently uses the same 5-question generic
   bank (Part 6.1, step 2).
8. **A document upload can bypass the 80% questionnaire-completion gate entirely** —
   the real analysis gate is "≥80% answered OR ≥1 document uploaded," independent of
   how much that document actually covers (Part 6.4).
9. **RFI regeneration has no version history** — it deletes and replaces the prior RFI
   document outright (Part 9.2).
10. **Remediation tracking has no transition validation and no cross-check against
    review status** — any status can follow any other, and closing remediation doesn't
    require the underlying finding to be reviewed/approved first (Part 9.4).
11. **`app/routers/reports.py` still imports directly from `app.dpdpa.framework`** for
    one summary endpoint rather than going through the `compat.py` shim or the registry
    — a residual pre-multi-framework seam (Part 1.1).
