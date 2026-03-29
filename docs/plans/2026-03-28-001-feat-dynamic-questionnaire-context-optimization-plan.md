---
title: Dynamic Questionnaire with Context-Gathering Phase & Context Optimization
type: feat
status: active
date: 2026-03-28
---

# Dynamic Questionnaire with Context-Gathering Phase & Context Optimization

## Overview

Transform the current static 41-question DPDPA assessment into a two-phase adaptive system:

1. **Context Gathering Phase** — understand the organization's data landscape, tech stack, exposure profile, and existing posture before any compliance questions are asked
2. **Adaptive Assessment Sections** — serve requirement questions that are scoped, pre-weighted, and contextually relevant based on what was gathered in Phase 1

Additionally, optimize how context is assembled and sent to Claude — shifting from a single monolithic prompt to a structured, token-efficient, layered context strategy that produces more reliable, initiative-planning-grade output.

---

## Problem Statement

### Current Questionnaire Limitations

The current questionnaire is a flat, static 41-question checklist:
- Every organization gets the same questions regardless of industry, size, or data exposure
- Questions map 1:1 to DPDPA requirements — they test knowledge of compliance obligations, not operational reality
- No intake context means Claude has to infer industry-specific risk from generic answers
- `not_applicable` is a single answer option with no structured reason — Claude can't distinguish "we don't process children's data" from "we haven't checked"
- No follow-up depth: a "partial" answer on `CH2.SECURITY.1` triggers the same remediation advice for a 5-person startup as for a 2000-person fintech

### Current Context Management Limitations

- System prompt embeds the full 41-requirement framework on every call — ~3,000+ tokens that don't change
- User prompt dumps all responses + documents in flat text — no structure signals to Claude which areas deserve deeper analysis
- No caching of the static system prompt (Anthropic prompt caching saves ~90% of system prompt tokens on repeated calls)
- Document truncation is crude (word count cutoff) — important policy clauses may be cut mid-sentence
- Single synchronous call means no opportunity for targeted follow-up on ambiguous responses
- Analysis output is dense JSON — no intermediate reasoning layer, so the executive summary is often generic

### Gap in Report Value for Planning

The current output tells clients *what* is non-compliant but not reliably *how* to plan remediation as a cyber initiative:
- No dependency mapping between requirements (e.g., you can't do `CH3.ACCESS.1` well without fixing `CH2.MINIMIZE.2` first)
- No maturity framing — binary compliant/non-compliant per requirement misses the "partially compliant with a plan" scenario
- Remediation roadmap is sorted by priority score but not by logical implementation sequence
- No effort bundling — 8 medium-effort items that share the same root cause (e.g., missing ISMS) should surface as one initiative

---

## Proposed Solution

### Phase 1: Context Gathering (New)

A structured intake questionnaire served *before* the DPDPA compliance sections. ~12-15 questions grouped into 4 blocks. This is **not** compliance assessment — it's organizational intelligence gathering.

#### Block A: Data Landscape
- What categories of personal data do you collect? (multi-select: identity, financial, health, biometric, location, behavioral, children's, other)
- What is your primary mechanism for collecting data? (web forms, mobile app, third-party APIs, physical forms, automated tracking, combinations)
- Do you use third-party data processors / SaaS vendors who handle personal data on your behalf? (yes / no / unsure)
- Do you transfer personal data outside India? (yes / no / unsure — if yes: which regions?)

#### Block B: Existing Posture
- Do you have a dedicated privacy / DPO function? (yes, full-time / yes, part-time/shared / no)
- Do you have an existing information security program? (ISO 27001 certified / SOC 2 / internal policy only / none)
- Have you undergone any privacy or security audit in the past 2 years? (yes — external / yes — internal only / no)
- Do you have a documented privacy policy published to users? (yes, recently updated / yes, outdated / no)

#### Block C: Risk Exposure
- Do any of the following apply to your organization? (multi-select: processes children's data, operates in healthcare/finance/critical infra, handles sensitive personal data, designated or likely SDF, none)
- Roughly how many data principals (individuals whose data you hold) are affected? (<10K / 10K–1M / 1M–10M / >10M)
- In the last 2 years, have you experienced any data breach or security incident? (yes, reported / yes, unreported / no / unsure)

#### Block D: Initiative Context
- What is the primary driver for this assessment? (regulatory audit prep / investor/board requirement / customer due diligence / proactive compliance / post-incident review)
- What is your target compliance timeline? (<3 months / 3-6 months / 6-12 months / no hard deadline)
- What is your approximate budget band for remediation? (under ₹5L / ₹5L–25L / ₹25L–1Cr / above ₹1Cr / not yet defined)

#### How Context Is Used

After Phase 1 is submitted, the backend:
1. Runs a lightweight Claude call (~1,000 tokens) to compute an **org risk profile**: which DPDPA chapters are highest priority, which sections are likely not applicable, and what contextual framing should be applied to ambiguous answers
2. Stores the risk profile in the `Assessment` model as a `context_profile` JSON field
3. Uses this profile to **filter, re-order, and annotate** the Phase 2 questionnaire before serving it

### Phase 2: Adaptive Assessment Sections (Enhanced)

Replace the flat 41-question list with a **sectioned, contextually annotated** questionnaire:

#### Section Structure

Instead of a single GET endpoint returning 41 questions, sections are served progressively:

```
GET /api/assessments/{id}/questionnaire/sections
→ Returns section index with estimated question count and relevance score per section

GET /api/assessments/{id}/questionnaire/sections/{section_id}
→ Returns questions for that section, with context-aware annotations
```

#### Per-Question Enhancements

Each question now carries context-aware metadata derived from the org's risk profile:

```json
{
  "id": "CH2.CONSENT.1",
  "question": "...",
  "guidance": "...",
  "criticality": "critical",
  "relevance_weight": 1.4,        // boosted because org processes sensitive data
  "context_note": "Your industry (fintech) is subject to heightened consent standards under RBI guidelines in addition to DPDPA Section 6.",
  "suggested_evidence": ["privacy_policy", "consent_form", "mobile_app_screenshots"],
  "follow_up_triggers": {
    "partial": "Please describe which consent mechanisms are in place and what gaps you're aware of.",
    "no": "Is this because you rely on legitimate use (Section 7), or consent mechanisms haven't been implemented yet?"
  },
  "skip_if": null   // populated for SDF questions if org indicated they're unlikely SDF
}
```

#### Answer Schema Enhancement

Extend the `ResponseSubmit` schema:

```python
class ResponseSubmit(BaseModel):
    question_id: str
    answer: Literal["yes", "no", "partial", "not_applicable"]
    notes: str | None = None
    evidence_reference: str | None = None
    na_reason: Literal["not_applicable_confirmed", "not_applicable_assumed", "deferred"] | None = None  # NEW
    confidence: Literal["high", "medium", "low"] | None = None  # NEW — how sure is the respondent?
```

---

## Context Optimization Strategy

### 1. Prompt Caching for System Prompt

The system prompt (DPDPA requirements framework + assessment instructions) is static and ~3,000+ tokens. Implement Anthropic prompt caching:

```python
# In claude_analyzer.py
message = client.messages.create(
    model=settings.claude_model,
    max_tokens=8192,
    temperature=0,
    system=[
        {
            "type": "text",
            "text": system_prompt,
            "cache_control": {"type": "ephemeral"}  # Cache for 5 minutes
        }
    ],
    messages=[{"role": "user", "content": user_prompt}]
)
```

**Impact**: ~90% token cost reduction for the system prompt on repeated assessments within 5 minutes. For demos (repeated runs), this is significant.

### 2. Structured Context Assembly

Replace the flat text user prompt with a **structured context object** that signals importance to Claude:

```
## Context Profile (Generated from Phase 1)
- Risk tier: HIGH — processes sensitive financial data + >1M data principals
- Primary exposure: Chapter 2 (Consent, Security), Cross-Border Transfers
- Likely not applicable: SDF provisions (not yet designated)
- Compliance driver: Customer due diligence — output will be shared with enterprise clients
- Target timeline: 3-6 months — prioritize quick wins that address audit-visible gaps

## Questionnaire Responses (41 items)
[responses grouped by section, not flat list]

## Document Evidence
[only include sections relevant to specific gap areas — not full document dumps]
```

### 3. Section-Based Claude Analysis (Multi-Call Architecture)

Split the single monolithic Claude call into **2 targeted calls**:

**Call 1 — Risk Profiling** (fast, ~500 tokens, cached system prompt)
- Input: Phase 1 context + org profile
- Output: Risk tier, priority sections, contextual framing notes
- Stored in `Assessment.context_profile`

**Call 2 — Full Gap Analysis** (existing, enhanced with context profile)
- Input: Context profile + Phase 2 responses + documents
- System prompt uses cache from Call 1
- Output: 41-item assessment, same JSON schema

This gives Claude a "thinking step" — the risk profile primes the analysis frame before diving into 41 requirements.

### 4. Document Context Optimization

Replace the word-count truncation with **semantic section extraction**:

- For privacy policies: extract the sections most relevant to current gap analysis focus areas (consent, cross-border, retention, children)
- For breach procedures: extract notification timelines and escalation paths specifically
- Use section headers as anchors — don't cut mid-section

```python
def extract_relevant_sections(text: str, focus_areas: list[str], max_words: int) -> str:
    """Extract sections of a document most relevant to focus_areas."""
    # Split by common section headers, score each section by keyword overlap with focus_areas
    # Return highest-scoring sections up to max_words
```

### 5. Caching Assessment Context

For long-running assessments (client spends multiple sessions answering), cache the assembled context between calls:

- Store `assembled_context_hash` in `GapReport` — if responses + documents haven't changed, reuse cached context
- Avoid re-assembling 20,000 words of document text on every analysis trigger

---

## Initiative-Planning Grade Output

The report output needs to be reliable enough for a client to take to their CISO or board. Enhancements:

### Requirement Dependency Mapping

Add a `dependencies` field to gap items:

```json
{
  "requirement_id": "CH3.ACCESS.1",
  "...": "...",
  "dependencies": ["CH2.MINIMIZE.2", "CH2.MINIMIZE.3"],
  "dependency_note": "Data subject access requests require knowing what data you hold — depends on retention and minimization practices being in place first."
}
```

Static dependency map defined in `framework.py` — no extra Claude call needed.

### Root Cause Clustering

After gap analysis, group non-compliant/partially compliant items by root cause:

- **Missing ISMS/Security Program** → bundles `CH2.SECURITY.1`, `CH2.SECURITY.2`, `BN.NOTIFY.3`, `CH4.SDF.4`
- **No Documented Consent Lifecycle** → bundles `CH2.CONSENT.1`, `CH2.CONSENT.2`, `CM.RECORDS.1`, `CM.RECORDS.2`, `CM.GRANULAR.1`
- **No Privacy Notice/Policy** → bundles `CH2.NOTICE.1`, `CH2.NOTICE.2`, `CH2.NOTICE.3`

Each cluster becomes a **named initiative** in the roadmap:

```json
{
  "initiative_id": "INIT-001",
  "title": "Establish Consent Lifecycle Management",
  "root_cause": "No documented consent capture, storage, or withdrawal mechanism",
  "requirements_addressed": ["CH2.CONSENT.1", "CH2.CONSENT.2", "CM.RECORDS.1", "CM.RECORDS.2", "CM.GRANULAR.1"],
  "combined_effort": "high",
  "combined_timeline_weeks": 12,
  "priority": 1,
  "budget_estimate_band": "₹5L–15L",
  "suggested_approach": "Implement a consent management platform (CMP) or build consent flows into your product with audit logging."
}
```

### Maturity Framing

Add a maturity level (1-5) alongside the compliance status:

| Level | Label | Meaning |
|-------|-------|---------|
| 1 | Ad Hoc | No formal process; relies on individuals |
| 2 | Documented | Process exists but not consistently followed |
| 3 | Defined | Consistent process; some monitoring |
| 4 | Managed | Measured and actively managed |
| 5 | Optimized | Continuously improving |

This frames "partially compliant" more precisely — a client at maturity 2 vs 3 has very different remediation paths.

---

## Implementation Phases

### Phase 1: Context Gathering Infrastructure
- Add `context_profile` JSON field to `Assessment` model + migration
- Define Phase 1 question set in `app/dpdpa/context_questions.py`
- New endpoint: `POST /api/assessments/{id}/context` — submit Phase 1 answers
- New service: `app/services/context_profiler.py` — lightweight Claude call to derive risk profile
- Update `GET /api/questionnaire` to accept optional `assessment_id` — returns context-annotated questions if profile exists

**Files**:
- `app/dpdpa/context_questions.py` — Phase 1 question definitions
- `app/services/context_profiler.py` — risk profiling service
- `app/routers/questionnaire.py` — add context endpoint
- `app/models/assessment.py` — add `context_profile` field
- `app/schemas/assessment.py` — add `ContextSubmit` schema

### Phase 2: Adaptive Question Annotations
- Add `relevance_weight`, `context_note`, `follow_up_triggers`, `skip_if` fields to question schema
- `build_questionnaire(context_profile)` becomes context-aware — applies weights and annotations
- Add section-based questionnaire endpoints
- Extend `ResponseSubmit` with `na_reason` and `confidence` fields

**Files**:
- `app/dpdpa/questionnaire.py` — extend `build_questionnaire()`, add section grouping
- `app/schemas/questionnaire.py` — extend `ResponseSubmit`, add `QuestionnaireSection` schema
- `app/routers/questionnaire.py` — add `/sections` endpoints

### Phase 3: Context Optimization
- Implement prompt caching in `claude_analyzer.py`
- Restructure `build_user_prompt()` to use structured context object
- Add semantic section extraction to `document_processor.py`
- Split analysis into Call 1 (risk profiling) + Call 2 (gap analysis)

**Files**:
- `app/services/claude_analyzer.py` — prompt caching, restructured prompts, 2-call architecture
- `app/dpdpa/prompts.py` — new context profile prompt, restructured user prompt
- `app/services/document_processor.py` — add `extract_relevant_sections()`

### Phase 4: Initiative-Planning Output
- Add static dependency map to `framework.py`
- Add root cause clustering logic to `scoring.py`
- Add initiative generation to `analysis.py` (post-Claude step, deterministic)
- Add maturity level to `GapItem` model and Claude output schema
- Update report schemas and PDF export

**Files**:
- `app/dpdpa/framework.py` — add `dependencies` and `root_cause_cluster` to requirements
- `app/services/scoring.py` — add `cluster_by_root_cause()`, `generate_initiatives()`
- `app/models/report.py` — add `maturity_level` to `GapItem`, add `Initiative` model
- `app/schemas/report.py` — add `InitiativeOut`, `MaturityLevel`
- `app/utils/pdf_export.py` — add initiatives section, maturity badges

---

## Data Model Changes

### Assessment Model (add field)
```python
context_profile: str | None = None  # JSON string — risk profile from Phase 1
```

### QuestionnaireResponse Model (add fields)
```python
na_reason: str | None = None      # "confirmed" | "assumed" | "deferred"
confidence: str | None = None      # "high" | "medium" | "low"
```

### GapItem Model (add field)
```python
maturity_level: int | None = None  # 1-5 maturity scale
```

### Initiative Model (new)
```python
class Initiative(Base):
    id: str (UUID)
    report_id: str (FK → GapReport)
    initiative_id: str  # e.g., "INIT-001"
    title: str
    root_cause: str
    requirements_addressed: str  # JSON list
    combined_effort: str
    combined_timeline_weeks: int
    priority: int
    budget_estimate_band: str | None
    suggested_approach: str
```

---

## Acceptance Criteria

### Context Gathering
- [ ] Phase 1 endpoint accepts and stores org context answers
- [ ] Risk profile is generated (Claude call) and stored on Assessment
- [ ] Phase 2 questionnaire returns context-annotated questions when assessment_id provided
- [ ] SDF questions are marked `skip_if` for orgs that indicated they're not SDF candidates

### Adaptive Questionnaire
- [ ] Questions carry `relevance_weight`, `context_note`, `follow_up_triggers`
- [ ] Section-based endpoints return grouped questions with section metadata
- [ ] `ResponseSubmit` accepts `na_reason` and `confidence`

### Context Optimization
- [ ] Prompt caching is implemented — verified via `usage.cache_read_input_tokens` in API response
- [ ] User prompt is structured with context profile header
- [ ] Document extraction uses section-aware logic (not word-count cutoff mid-sentence)

### Initiative-Planning Output
- [ ] Non-compliant items are grouped into named initiatives
- [ ] Each initiative has effort, timeline, budget band, and suggested approach
- [ ] Dependency relationships are surfaced in gap items
- [ ] Maturity level (1-5) is included per gap item
- [ ] PDF report includes initiatives section

### Quality
- [ ] Existing Prestige Estates assessment re-run produces richer output with initiatives
- [ ] System prompt token cost reduced measurably via caching on second run
- [ ] All 14 existing API endpoints continue to work (no breaking changes to existing response shapes)

---

## System-Wide Impact

### API Surface
- All existing endpoints remain backward-compatible
- New endpoints added: `POST /context`, `GET /questionnaire/sections`, `GET /questionnaire/sections/{id}`
- Existing `GET /api/questionnaire` becomes context-aware but backward-compatible (returns unannotated questions without assessment_id)

### Claude API Costs
- Phase 1 profiling call: ~1,000 input tokens, ~300 output tokens (minimal cost)
- Phase 2 analysis call: Same as current, but system prompt cached after first call = ~90% reduction on system prompt tokens
- Net effect: Slightly more calls per assessment, but lower total token cost

### Database
- 3 model changes (additive only, no schema breaking changes)
- 1 new model (`Initiative`)
- SQLite `ALTER TABLE` migrations needed for new nullable fields

---

## Dependencies & Risks

| Risk | Mitigation |
|------|-----------|
| Context profiling call adds latency to Phase 1 submission | Run it async / background task after Phase 1 submit returns 200 |
| Dynamic question annotation increases questionnaire endpoint complexity | Keep annotation logic purely additive — unannotated fields remain valid |
| Root cause clustering may mis-bundle requirements | Start with manually curated static clusters; Claude-assisted clustering in v2 |
| Maturity level requires additional Claude output field | Validate Claude returns maturity_level; fall back to `null` if absent |
| Prompt caching requires specific API version | Verify `anthropic` SDK version supports `cache_control`; update if needed |

---

## Research-Validated Design Decisions

### Prompt Caching — Confirmed Approach

Use `cache_control: {"type": "ephemeral"}` on the last stable content block in the system prompt. Key rules from Anthropic docs:
- Sonnet 4.6 minimum: **2,048 tokens** to activate caching (framework requirements at ~3,000 tokens qualifies)
- Cache reads cost **0.1x** base input tokens — 90% saving
- Max **4 breakpoints** per request
- Place breakpoint on the **last stable block** (after it, only dynamic org content)
- Concurrent requests: cache only becomes available after first response **begins** — don't fan out parallel calls before first response

**Confirmed caching pattern**:
```python
system=[
    {"type": "text", "text": analyst_persona},
    {"type": "text", "text": dpdpa_requirements_text, "cache_control": {"type": "ephemeral"}},
]
```

Monitor with `response.usage.cache_read_input_tokens` — should be non-zero on repeat calls.

### Response Scale Enhancement — Confirmed

Replace 4-option `[yes, no, partial, not_applicable]` with 5-option scale used by all production GRC tools:
- `fully_implemented`
- `partially_implemented`
- `planned` ← critical addition: "we have a roadmap for this"
- `not_applicable` (with `na_reason` required)
- `not_implemented`

The `planned` state enables maturity scoring and distinguishes "working on it" from "never considered it."

### Maturity Model — CMMI 0-5 Scale (Not NIST 4-Tier)

Use **0-5 CMMI-aligned scale** — aligns with ISO 27001 which Indian enterprise clients (BFSI, IT/ITES) already know:

| Level | Name | Description |
|-------|------|-------------|
| 0 | Non-existent | Control entirely absent |
| 1 | Initial | Ad-hoc, depends on individuals |
| 2 | Managed | Documented but inconsistently applied |
| 3 | Defined | Standardized, consistent, auditable |
| 4 | Quantitative | KPIs tracked, deviations alerted |
| 5 | Optimizing | Continuous improvement embedded |

Map response answers to maturity: `not_implemented` → 1, `planned` → 1.5, `partially_implemented` → 2.5, `fully_implemented` → 4.

### Multi-Call Architecture — Quote-First Pattern

Two-call chain confirmed as best practice for document-heavy compliance analysis:

**Call 1 (evidence extraction)**: Instruct Claude to quote specific policy text per requirement before assessment. "Before assessing each requirement, quote the exact policy language or state 'No relevant language found'." This grounds the analysis, reduces hallucination, and the output is cacheable/reusable.

**Call 2 (gap analysis)**: Use Call 1 quoted evidence as input. Claude can now assess against concrete text, not inferences.

### Structured Output — Use json_schema Constrained Decoding

Use `output_config.format.type = "json_schema"` with a full schema definition. This uses constrained decoding — Claude **cannot** produce tokens that violate the schema. Eliminates JSON parse errors entirely. Preferable to "output valid JSON" instructions.

### Phase 1 Context Gathering — Key Branching Triggers

Research confirmed these as the critical decision points:
- `data_principals > 100,000` or `sensitive_data = True` → SDF branch → DPO/DPIA questions
- `cross_border_transfers = True` → adequacy questions
- `processes_children_data = True` → parental consent deep-dive
- `has_breach_response_plan = False` → skip 72h notification detail, flag as Critical immediately

### Professional DPDPA Questions (Beyond Statutory)

Phase 1 context gathering should probe:
- **Data lineage**: Is legacy data (pre-DPDPA) covered with retroactive notice?
- **Derived data**: What happens to inferred/derived data when consent is withdrawn?
- **DPbD gate**: Is "Data Protection by Design" a gate in your SDLC?
- **Rights SLA**: What is your actual SLA for erasure requests?
- **Vendor audit rights**: Do your DPAs include audit rights and sub-processor restrictions?
- **Non-prod masking**: Is PII masked in dev/staging environments?

These distinguish a board-ready assessment from a statutory checklist.

---

## Sources & References

### Internal
- `app/dpdpa/questionnaire.py` — current 41 questions
- `app/dpdpa/prompts.py` — current prompt architecture
- `app/services/claude_analyzer.py` — current single-call implementation
- `app/dpdpa/framework.py` — requirements with criticality and section refs
- `app/services/scoring.py` — current scoring weights

### External
- [Anthropic Prompt Caching](https://platform.claude.com/docs/en/docs/build-with-claude/prompt-caching) — cache_control, TTL, token minimums, gotchas
- [Anthropic Structured Outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) — json_schema constrained decoding
- [Anthropic Prompting Best Practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) — long docs at top, XML tags, quote-first
- [DPDPA Compliance Checklist 2026](https://www.dpdpa.com/blogs/dpdpa_compliance_checklist_2026_business_assessment.html) — 50-point professional checklist
- [DPDPA Gap Assessment Methodology](https://www.dpdpconsultants.com/blog.php?id=49) — professional assessor questions
- [NIST CSF 2.0 Maturity Guide](https://allaboutgrc.com/nist-csf-2-0-maturity-assessment/) — intake phase structure
- [CMMI Maturity Levels for ISO 27001](https://www.linkedin.com/pulse/using-maturity-model-iso-27001-soa-27002-control-das-cisa-cissp) — 0-5 scale definition
- [SOC 2 Gap Analysis Patterns](https://www.thoropass.com/blog/soc-2-gap-analysis) — multi-phase assessment structure
- DPDPA Section 6-16 — statutory requirements basis
