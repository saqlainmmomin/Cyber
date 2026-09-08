# Multi-framework demo-usable plan (2026-09-08)

Anchor: **CyberAssess must run DPDPA, ISO 27001, and NIST CSF individually or in any combination, end-to-end, with your firm's branding, evidence citations, and a working RFI loop.** Goal is winning consulting pitches; you are the first user. Pitch weekly with whatever is ready; ship each workstream so the demo gets visibly better each week.

Derived from the grill session on 2026-09-08. See that transcript for framing decisions.

---

## 1. Development model — Codex + Claude in parallel

### 1.1 Agent split (by task nature, not by file)

| Nature | Owner | Why |
|---|---|---|
| Judgment / architecture / prompts / UCC content | **Claude** (in this chat, or `Plan` subagent) | Needs full codebase context + your voice. |
| Mechanical refactors with a written spec | **Codex** | Fast, cheap, disciplined at typing when the spec is unambiguous. |
| Test scaffolding, fixtures, golden files | **Codex** | Follow a spec, produce deterministic artefacts. |
| End-to-end verification (run app, check PDF, drive UI) | **Claude** (browser tools) | Codex can't drive the app; verification is where regressions hide. |
| Adversarial review | **Opposite agent** | Whoever built it does not review it. |

### 1.2 Handoff contract (Claude → Codex)

Every Codex handoff is a self-contained file in `tasks/handoffs/YYYY-MM-DD-<slug>.md` containing:

1. **Goal** — one paragraph, the outcome.
2. **Files in scope** — explicit list with line refs.
3. **Interfaces** — function signatures, model fields, template blocks that must exist after.
4. **Non-goals** — what NOT to touch (prevents scope creep).
5. **Test to pass** — either an existing pytest, or a new one written by Claude first.
6. **Done criteria** — pytest green + `uvicorn` boots + one manual smoke step.
7. **Rollback** — the exact `git` command to revert if adversarial review kills it.

Codex's job is to satisfy the contract, not to re-design. If the contract is wrong, Codex flags it and stops.

### 1.3 Branch strategy

- `main` — never broken.
- `feat/web-portal` — current working branch, only merges of green workstreams.
- `ws/<n>-<slug>` — one branch per workstream (Codex or Claude commits here).
- `spike/<slug>` — throwaway branches for de-risking (WS #5 analyzer spike). Never merged; discoveries flow into the plan.

Merge into `feat/web-portal` only after adversarial review passes.

### 1.4 Adversarial review protocol (used at every checkpoint)

**Trigger:** any workstream in this plan is marked "done" by its builder.

**Reviewer:** the opposite agent (Claude if Codex built; Codex if Claude built) — or `compound-engineering:review:code-simplicity-reviewer` / `security-sentinel` / `kieran-python-reviewer` subagent where matched.

**Review prompt shape:**
```
You are adversarial. The builder claims workstream #N is complete. Your job is to
break the claim.

Scope: <files>
Done criteria the builder claims to meet: <list>

Find:
1. Any done-criterion that is not actually met (run the test, boot the app, open the PDF).
2. Silent regressions in files outside the stated scope.
3. Assumptions the builder made that are unstated in the handoff.
4. The single most likely production failure mode.

Output: PASS / FAIL with numbered failures. No hedging.
```

**Resolution:** FAIL → builder addresses each numbered failure → re-review. Two FAILs on the same workstream = escalate to Saqlain for design change.

**Cadence:** every workstream gets one adversarial review. Additionally, three **major checkpoints** get a deeper multi-agent review (see §5).

---

## 2. Workstream matrix

| # | Workstream | Owner | Depends on | Effort | Track |
|---|---|---|---|---|---|
| 1 | Static white-label config | Codex | — | 1 d | A |
| 2 | Framework picker + individual/combined UX | Claude → Codex | — | 2 d | A |
| 3 | Golden-output tests on current DPDPA path | Claude → Codex | — | 2 d | B |
| 4 | Framework-agnostic refactor of `screening.py` + `scoring.py` | Codex | #3 | 3–4 d | B |
| 5 | **Spike:** per-cluster analyzer on 5 DPDPA clusters | Claude | #3 | 2 d | C |
| 6 | UCC clustering for ISO 27001 + NIST CSF | Claude (you) | — | 1–2 wk | D |
| 7 | Per-cluster analyzer full build | Claude → Codex | #4, #5, #6 | 1 wk | C |
| 8 | Evidence citations in analyzer output + PDF | Claude → Codex | #7 | 3–4 d | E |
| 9 | RFI magic-link port from `ai_audit_copilot` | Claude (validate) → Codex (port) | client signed | 2 d validate + ~1 wk port | F |

Tracks A–F run **in parallel** where dependencies allow. See §4 timeline.

---

## 3. Per-workstream detail

### WS #1 — Static white-label config

- **Goal:** Every screenshot and PDF page shows your firm's name and logo instead of "CyberAssess."
- **Owner:** Codex.
- **Inputs Claude produces first:** handoff spec listing every hardcoded "CyberAssess" / "DPDPA Gap Tool" string in `app/utils/pdf_export.py`, `app/templates/base.html`, `app/config.py`.
- **Deliverables:**
  - `app/config.py`: `firm_name`, `firm_logo_path`, `firm_primary_hex` env vars.
  - `pdf_export.py`: header/footer/cover use config, not literals.
  - `base.html` navbar shows firm name.
  - `.env.example` updated.
- **Done criteria:** Boot the app with `FIRM_NAME="Momin & Co"`, `FIRM_LOGO_PATH=static/img/momin.png` — navbar and PDF cover both show it. `pytest -q` green.
- **Adversarial review:** Claude grep for any remaining hardcoded product name string. FAIL if any client-visible surface still says "CyberAssess."

### WS #2 — Framework picker + individual/combined UX

- **Goal:** On new-assessment screen, user picks any subset of {DPDPA, ISO 27001, NIST CSF} (GDPR/HIPAA/PCI stay visible but marked "roadmap — DPDPA-anchored"). Assessment page shows per-framework tabs when >1 selected, single view when 1.
- **Owner:** Claude designs data model + template; Codex implements.
- **Key decision to nail before coding:** per-framework scoring is stored per-framework; combined view is a *derived* aggregation, not a stored artifact. Document this in the handoff — it's the invariant that WS #7 and #8 rely on.
- **Deliverables:**
  - `Assessment` model gains `frameworks: list[str]` (already exists — audit) and validation ≥1.
  - Scope page groups controls by framework with "select all in framework" chips.
  - Assessment page: tabs component (`<div hx-target>` swaps).
  - Report route: `?view=combined|per_framework` query param.
- **Done criteria:** Create 3 assessments: DPDPA-only, ISO+NIST, all three. Each renders scope, questionnaire, and report correctly.
- **Adversarial review:** Codex-built → Claude drives the app in browser, screenshots each path, flags visual/logic breaks.

### WS #3 — Golden-output tests

- **Goal:** Freeze the current DPDPA behaviour so #4/#5/#7 refactors can't silently regress it.
- **Precondition:** WS #1 (white-label) merged first — branding text is captured in the PDF golden; if #1 lands after #3, the golden invalidates immediately.
- **Comparison contract:** exact dict equality on score + analyzer output; SHA-256 of *extracted PDF text* (not byte hash) plus exact page count plus byte-length floor. Full spec in `tasks/handoffs/2026-09-08-ws3-golden-dpdpa.md`.
- **Analyzer:** mocked in golden runs via a recorded response file. Live-analyzer testing is separate.
- **Owner:** Claude writes fixtures + assertions; Codex parameterises.
- **Deliverables:**
  - `tests/fixtures/canonical_dpdpa_assessment/` — one fully-populated assessment (evidence files, screening answers, questionnaire answers).
  - `tests/test_golden_dpdpa.py`:
    - Score JSON: dict equality against `expected_score.json`.
    - PDF: SHA-256 of the byte stream against `expected_pdf.sha256` (or byte-length + page-count for tolerance).
    - Analyzer output: canonical string keys present, cluster IDs match.
  - `tests/conftest.py` fixture to spin up an ephemeral SQLite + seed the canonical assessment.
- **Done criteria:** `pytest tests/test_golden_dpdpa.py` green on a clean checkout. Deliberately break one status string in `scoring.py` locally and confirm the test fails loudly.
- **Adversarial review:** Codex — try to make a "harmless" change (rename a variable in `scoring.py`) that should not affect output; test must not fire. If it does, the golden is too tight.

### WS #4 — Framework-agnostic `screening.py` + `scoring.py`

- **Goal:** Both services accept `framework_ids: list[str]` and read from `app.frameworks.registry` instead of `from app.dpdpa.framework import ...`.
- **Owner:** Codex, from a Claude-authored handoff.
- **Handoff must specify:**
  - Every call site of `DPDPA_FRAMEWORK`, `ROOT_CAUSE_CLUSTERS`, `SCREENING_DOMAINS` — replaced with registry lookups keyed by the framework(s) in scope.
  - Backwards compatibility shim: if a caller passes no `framework_ids`, default to `["dpdpa"]` and log a deprecation warning.
  - No behavioural change for a DPDPA-only assessment (WS #3 tests protect this).
- **Deliverables:** two refactored files, all `from app.dpdpa.*` imports removed from `services/`, WS #3 tests still green.
- **Done criteria:** WS #3 green + a new test `tests/test_iso_scoring_smoke.py` runs `score()` on an ISO-only assessment and gets non-crashing output.
- **Adversarial review:** Claude — inspect every diff for hidden DPDPA assumption (magic domain names, hardcoded control ID prefixes like `DPDPA-`).

### WS #5 — Spike: per-cluster analyzer

- **Goal:** De-risk WS #7 before you commit a week to it. Prove that one Claude call per UCC cluster produces coherent status + reasoning, at acceptable cost/latency.
- **Owner:** Claude, throwaway branch `spike/per-cluster-analyzer`.
- **Scope:** 5 hand-picked DPDPA clusters that vary in size (small/medium/large evidence footprint).
- **Method:**
  1. Take the canonical fixture from WS #3.
  2. For each of 5 clusters: build a prompt with (a) cluster definition, (b) mapped controls across selected frameworks, (c) filtered evidence excerpts (only files touching those control keywords), (d) relevant questionnaire answers.
  3. Call Claude Sonnet, structured output.
  4. Compare status verdicts against the current two-call analyzer's output for those clusters.
  5. Record latency, input tokens, output tokens per call.
- **Done criteria — the go/no-go decision:**
  - ≥4/5 clusters produce a status that matches the two-call output OR is defensibly better on inspection.
  - Median latency per cluster < 15s.
  - Cost per full 3-framework assessment (est. ~80 clusters) projects to < $5.
  - Zero JSON parse failures.
- **If it fails:** fall back to per-domain analyzer (9 calls), rewrite WS #7 spec, re-spike.
- **Adversarial review:** Claude — hostile prompt: "the spike is going to fail in production, tell me the three reasons why." Then run those failure modes.

### WS #6 — UCC clustering for ISO 27001 + NIST CSF

- **Goal:** Every ISO 27001 and NIST CSF control belongs to a UCC cluster (or is an intentional singleton). Existing 53 clusters get expanded; new clusters created only where a genuinely new control theme appears.
- **Owner:** **You.** This is judgment work. Claude assists by:
  - Pre-suggesting candidate cluster matches per control (subagent pass).
  - Flagging orphans and singletons.
  - Running the content-integrity validator after each batch.
- **Deliverables:**
  - `app/frameworks/mappings/clusters.py` updated.
  - `INTENTIONAL_SINGLETONS` extended where warranted (documented reason per entry).
  - `tests/test_content_integrity.py` green.
- **Workflow:** batch by NIST function (Identify, Protect, Detect, Respond, Recover) then ISO by Annex A section. ~20 controls per sitting.
- **Done criteria:** validator green, 0 unexplained orphans, spot-check 10 random controls with adversarial reviewer.
- **Adversarial review:** Claude subagent — pick 10 random cluster memberships and ask "would a DPDPA specialist and an ISO auditor both agree this control belongs in this cluster? Justify or flag."

### WS #7 — Per-cluster analyzer full build

- **Precondition:** WS #5 spike passed. If it failed, this workstream is redesigned first.
- **Owner:** Claude designs the module; Codex implements from the spec that emerged from the spike.
- **Deliverables:**
  - `app/services/cluster_analyzer.py` — public API `analyze_clusters(assessment_id, framework_ids) -> ClusterAnalysisResult`.
  - Batched concurrent calls (asyncio + semaphore) with per-cluster retry.
  - Structured output schema (Pydantic) so JSON parse failures are impossible in principle.
  - Progress state persisted to DB so mid-run failure resumes on the next call.
- **Wire-up:** existing analyzer route calls the new module behind a feature flag `USE_CLUSTER_ANALYZER=1`.
- **Done criteria:** flag off → WS #3 golden green (byte-identical output). Flag on → produces per-framework scores for a DPDPA+ISO fixture. Mid-run kill of the process + restart resumes.
- **Adversarial review:** `compound-engineering:review:performance-oracle` + Claude — attack async/error paths, force API failures, verify resume actually resumes.

### WS #8 — Evidence citations in analyzer output + PDF

- **Precondition:** WS #7 shipped (analyzer shape settled).
- **Owner:** Claude drafts the schema and PDF layout; Codex implements.
- **Deliverables:**
  - Analyzer output per control gains `evidence_citations: list[{doc_id, filename, excerpt, page_or_para, why_it_supports}]`.
  - PDF gains a per-control block or appendix section rendering these citations.
  - Web assessment page shows the same citations under each control in an expander.
- **Done criteria:** open the demo PDF for the canonical assessment — every non-"not implemented" control has ≥1 citation. Click any control in the web view — same citations render.
- **Adversarial review:** you role-play a client CISO: pick 5 controls at random and ask "why this score?" — the PDF must answer without you speaking.

### WS #9 — RFI magic-link port

- **Precondition:** a live client signs, OR a pitch explicitly demands live evidence intake.
- **Owner:** Claude reads `ai_audit_copilot` and produces a **portability report** first, before any code lands.
- **Portability report contents:**
  - Which files/modules in `ai_audit_copilot` implement the magic-link intake + re-ingestion loop.
  - Their dependencies (auth model, DB schema, framework versions).
  - What has to be adapted for CyberAssess (session model, tenancy, models file).
  - Honest effort estimate: "port" vs "reference and rewrite."
- **Only after Saqlain reads the report:** Codex ports/adapts.
- **Deliverables:** magic-link generation route, public intake route, evidence re-ingestion into the existing desk-review pipeline, RFI status tracking.
- **Done criteria:** generate an RFI → open the link in a private window → submit evidence → assessment shows the new evidence in the desk review.
- **Adversarial review:** `security-sentinel` — magic links are auth. Attack: link enumeration, expiry, re-use, evidence spoofing, unbounded upload.

---

## 4. Timeline (parallel tracks, 5–7 week envelope)

**Guideline:** each week produces at least one visibly-better pitch demo. If a week ends without that, the plan has broken and we re-sequence.

| Week | Track A (visible polish) | Track B (foundation) | Track C (analyzer) | Track D (content) | Notes |
|---|---|---|---|---|---|
| 1 | WS #1 Days 1–2, WS #2 Days 1–5 | WS #3 Days 3–5 (after #1 lands — branding is part of the golden) | WS #5 spike Days 4–5 | WS #6 starts (Identify + Annex A.5) | End of week: pitch-ready white-label demo. Spike verdict decides Track C shape. |
| 2 | WS #2 polish per adversarial review | WS #4 refactor scoring + screening | (paused if spike failed → redesign) | WS #6 continues (Protect + A.6/7/8) | Refactor lands under golden test coverage. |
| 3 | — | WS #4 finish + smoke-test ISO run | WS #7 build starts | WS #6 continues (Detect + A.9/10/11) | First ISO-only assessment runs end-to-end (may be ugly). |
| 4 | — | — | WS #7 finish + feature flag on | WS #6 finishes | Combined DPDPA+ISO assessment demo-worthy. |
| 5 | — | — | WS #7 hardening (resume, retries) | WS #6 NIST wrap + integrity validator green | First combined DPDPA+ISO+NIST demo. |
| 6 | — | — | WS #8 citations | — | Board-defensible PDF ships. |
| 7 (only if client signed) | — | — | — | WS #9 RFI port | Otherwise: rest / pitch / iterate. |

Slippage rule: if any workstream slips >2 days past its week, **stop** and re-plan rather than compress the next week.

---

## 5. Major-checkpoint deep reviews (multi-agent, not per-workstream)

At three points, run a beefier adversarial pass beyond the per-workstream review:

**Checkpoint α — end of Week 1 (post-spike).**
- Question: does the spike verdict hold up? Would per-domain be safer?
- Agents: `code-simplicity-reviewer` + `performance-oracle` + you.
- Output: go/no-go/redesign for WS #7.

**Checkpoint β — end of Week 4 (first combined DPDPA+ISO+NIST assessment).**
- Question: does the tool actually deliver on the multi-framework pitch?
- Agents: `architecture-strategist` + `security-sentinel` + you role-playing a client CISO.
- Output: gap list against pitch narrative; anything critical becomes Week 5 work before WS #8.

**Checkpoint γ — end of Week 6 (before you first pitch it as "done").**
- Question: would you stake your consulting reputation on the PDF this produces?
- Agents: `dhh-rails-reviewer` (yes, on Python — the taste bar transfers) + you + one friendly external GRC reviewer if you can find one.
- Output: final polish list, or ship.

---

## 6. Risk register + kill criteria

| Risk | Signal | Kill / redesign trigger |
|---|---|---|
| Per-cluster analyzer hallucinates or costs too much | WS #5 spike done criteria not met | Redesign WS #7 as per-domain (9 calls). |
| NIST clustering takes 3+ weeks of your time | End of Week 3, <50% of NIST done | Ship demo with DPDPA+ISO only, NIST marked "in progress." |
| WS #4 refactor breaks the golden | WS #3 tests red for >1 day | Revert to `main`, redo refactor with smaller commits. |
| RFI port turns out to be a rewrite | Portability report from WS #9 says "reference and rewrite" | Cut RFI from demo bar, use email + PDF loop instead. |
| You aren't actually pitching weekly | Two weeks pass with no external conversation | Grill said this is the whole point. Stop building; go pitch. |

---

## 7. Rollback and merge discipline

- Every workstream branch has a documented `git revert <sha>` in its handoff. Adversarial review failure that can't be fixed same-day → revert, re-plan, don't compound the mess.
- Never merge a workstream branch into `feat/web-portal` without: (a) `pytest -q` green, (b) `uvicorn app.main:app` boots, (c) adversarial review PASS documented in the branch commit message.
- Never touch a file that's currently checked out on another workstream branch. If two workstreams need the same file, sequence them, don't parallel.

---

## 8. Immediate next actions (Day 1 of Week 1)

1. Claude writes the WS #1 handoff → `tasks/handoffs/2026-09-08-white-label-config.md`.
2. Claude writes the WS #3 golden-test handoff and generates the canonical fixture → `tasks/handoffs/2026-09-08-golden-dpdpa.md`.
3. You hand both to Codex in parallel; two branches open: `ws/1-white-label`, `ws/3-golden-dpdpa`.
4. In this chat: Claude drafts the WS #2 data-model decision doc (per-framework storage, combined-as-derived) → `tasks/handoffs/2026-09-08-picker-data-model.md` for your sign-off before Codex touches it.
5. End of Day 1: WS #1 in review, WS #3 in build, WS #2 spec awaiting your OK.

---

Update this file as reality diverges from the plan. Keep the diffs — they're the record of what the grill missed.
