# Design brief — multi-framework domain screening

**Date:** 2026-09-15
**Type:** design/content decision, **not** a Codex handoff — read `tasks/multi-framework-demo-plan.md`
§1.1: this is "judgment / architecture / prompts / UCC content," which is Claude+Saqlain
work, the same category WS #6 (UCC clustering) was. Nothing here gets implemented until
you've picked an option below.
**Triggered by:** WS #4's handoff (`tasks/handoffs/2026-09-15-ws4-framework-agnostic-scoring.md`)
carving screening.py generalization out as an explicit Non-goal, because it isn't a
mechanical refactor — it needs new content, not just parameterization.

---

## The problem, precisely

`app/services/screening.py::run_screening_pass()` takes no `framework_ids` parameter.
It's wired to exactly one hardcoded set of content: `SCREENING_DOMAINS`
(`app/dpdpa/prompts.py:555`) — 9 broad questions, each with a `covers: [req_id, ...]`
list of **DPDPA requirement IDs only** (e.g. `SD.CONSENT` covers
`CH2.CONSENT.1-4, CM.RECORD.1-2`). One Claude call infers a status + confidence for all
41 DPDPA requirements from the 9 answers; high-confidence non-negative inferences
auto-fill the questionnaire (`_persist_inferred_answers`, `screening.py:149-203`).

Run this today against an ISO-27001-only or combined assessment and it still only
screens the 41 DPDPA requirements — silently irrelevant to whichever frameworks were
actually selected. There is no ISO or NIST equivalent of `SCREENING_DOMAINS` anywhere in
the codebase. This is why multi-framework assessments get none of the adaptive
pre-fill/tiering machinery today (traced in full in
`docs/architecture/data-flow-and-processes.md`, Part 05-06).

---

## What's already there to build on

Checked directly against the current cluster data, not the plan's abstract description:

| `domain_group` | clusters | frameworks typically involved |
|---|---|---|
| governance | 13 | ISO, NIST, GDPR, PCI, HIPAA, DPDPA |
| security | 12 | ISO, NIST, PCI, HIPAA |
| consent_rights | 9 | DPDPA, GDPR, ISO |
| incident_response | 8 | ISO, NIST, PCI, HIPAA, GDPR |
| data_protection | 8 | ISO, NIST, DPDPA, GDPR |
| cross_border | 1 | DPDPA, GDPR |
| children_vulnerable | 1 | DPDPA |

52 clusters total, averaging 3 frameworks each; 92/93 ISO 27001 controls and 94/94 NIST
CSF controls are already cluster-members (WS #6 is essentially done — see plan §9.1).
**Every control in every enabled framework already belongs to one of these 7
domain_groups.** That's the raw material for a cross-framework screening design: 7
coarse buckets that already span every selected framework's controls, versus DPDPA's
own 9 domains which only ever meant anything for DPDPA.

---

## Three options

### A — Native domain set per framework

Write a separate ~8-12 question `SCREENING_DOMAINS`-equivalent for ISO 27001 (probably
along its 4 Annex A themes: organizational/people/physical/technological) and one for
NIST CSF (its 6 functions: Govern/Identify/Protect/Detect/Respond/Recover), each with a
`covers` list of that framework's own control IDs. Run one screening pass per selected
framework.

- **Pro:** mirrors the existing, working DPDPA pattern almost exactly — least
  conceptually new, `_parse_inferences`/`_persist_inferred_answers` barely change.
- **Con:** for a combined DPDPA+ISO+NIST assessment (the actual demo pitch), the user
  answers 9 + ~10 + 6 = ~25 broad domain questions, several of which are asking about
  the same underlying reality in different words (DPDPA's governance/SDF domain, ISO's
  organizational domain, and NIST's Govern function are the same conversation with a
  CISO, three times). That's the exact duplication problem UCC clustering exists to kill
  at the detailed-question level — reintroducing it at the screening level cuts against
  the pitch narrative ("answer once, cover every framework").

### B — Cluster/domain-group-based screening (cross-framework by construction)

Replace `covers: [req_id...]` with `covers: [cluster_id...]` (or `domain_group`, which
resolves to a set of clusters). ~7-9 domain-level questions, one per `domain_group`
(governance, security, consent_rights, incident_response, data_protection,
cross_border, children_vulnerable), asked **once regardless of how many frameworks are
selected**. The screening Claude call receives the assessment's `framework_ids` and
infers a status per **cluster**, not per raw requirement; auto-fill then writes
`QuestionnaireResponse` rows keyed by `cluster_id` — the same key the adaptive
questionnaire already uses for cluster-based questions (`question_engine.py`'s
`_build_multi_framework_questionnaire` already sets `"id": ucc_q["cluster_id"]`), so no
new persistence shape is needed.

- **Pro:** one screening pass, any combination of frameworks, by construction — no
  duplicated domain questions across frameworks. Keeps the whole pipeline's mental model
  consistent: clusters are the unit of analysis everywhere except the legacy DPDPA-only
  path (matches where WS #7's per-cluster analyzer is already heading).
- **Con:** real design work, not a rename. The 9 existing DPDPA domain questions and
  their `covers` lists were purpose-written around DPDPA's own chapter structure; they'd
  need to be rewritten (not just relabeled) against the 7 domain_groups, which risks
  changing DPDPA-only screening's behavior unless it's kept on a separate, frozen path
  (see the recommendation below).

### C — Do nothing yet; route multi-framework assessments around screening

Leave screening as a DPDPA-only optional step; for multi-framework assessments, simply
don't show the screening tab (hide it in the UI when `is_multi_framework`). No new
content, no new code path.

- **Pro:** zero design/content cost.
- **Con:** doesn't fix anything — multi-framework assessments still get no
  domain-level pre-fill, and now can't even fake it. This punts the actual gap
  indefinitely rather than closing it; not recommended given the pitch depends on the
  multi-framework story feeling as smart as the DPDPA-only one.

---

## Recommendation

**Build Option B, but ship it as a second, independent code path — leave the existing
DPDPA `SCREENING_DOMAINS` / `run_screening_pass()` completely untouched.**

This is the same discipline WS #4 and the original picker work (WS #2) already used:
DPDPA-only behavior stays byte-identical and golden-tested; new behavior is additive.
Concretely:

- Existing `run_screening_pass(assessment_id, domain_answers, db)` keeps working exactly
  as today for `assessment.frameworks == ["dpdpa"]`. No golden-test risk.
- A new function — e.g. `run_cluster_screening_pass(assessment_id, framework_ids, domain_answers, db)` —
  handles everything else (any non-DPDPA-only selection), built against the
  `domain_group` clusters above.
- The screening route (`web.py:998-1009`) branches on `assessment.is_multi_framework`
  (the property already exists, from WS #2) to call one or the other. This mirrors how
  `question_engine.py` already branches on framework selection to route to
  `_build_multi_framework_questionnaire()`.

This keeps the risky, novel content work isolated from the shipped, tested DPDPA path,
and gives WS #4's Codex handoff nothing to worry about — screening genuinely doesn't
need to change for WS #4 to land.

---

## What a content-design session needs to produce

Sized like WS #6 (Saqlain's judgment, Claude assisting) — **not** a Codex task, at least
for the first pass:

1. **7-9 domain-level screening questions**, one per `domain_group` (or split
   `governance`/`security` — they're the two largest at 13 and 12 clusters — into two
   questions each if a single question can't reasonably span that much ground). Each
   question needs: the question text (broad, CISO-interview-style, matching the existing
   `SD.*` tone), and a `covers: [cluster_id, ...]` list pulled directly from
   `CONTROL_CLUSTERS` filtered to that `domain_group`.
2. **A revised screening system prompt** (`build_screening_system_prompt()`-equivalent)
   that asks Claude to infer a status per *cluster* rather than per raw requirement, and
   to only infer clusters relevant to the assessment's actual `framework_ids` (a cluster
   spanning ISO+NIST+DPDPA, for a DPDPA-only assessment, should only get evaluated
   against its DPDPA member — reuse the same "expand cluster to member controls" logic
   `_expand_cluster_responses()` already does at analysis time,
   `app/frameworks/prompts.py:56-98`, rather than inventing a second version of it).
3. **A decision on how a cluster-level screening inference propagates to member
   controls** — mirrors the exact question WS #4's `_build_cluster_verdicts` answers for
   scoring (worst-case status across cluster members), so reuse that logic/vocabulary
   rather than inventing new semantics for screening specifically.
4. **A spot-check pass**, same spirit as WS #6's adversarial review ("would a DPDPA
   specialist and an ISO auditor both agree this domain question's `covers` list is
   complete and correctly scoped?") — pick 10 random clusters across the 7 domain
   groups and verify they're reachable by exactly one of the new domain questions, no
   orphans.

## Open questions only you can settle

- Do `governance` (13 clusters) and `security` (12 clusters) each need to be split into
  two screening questions rather than one, to keep each question answerable in a
  reasonable paragraph? (Compare: DPDPA's 9 domains average ~4.5 requirements each;
  a single governance question spanning 13 clusters is a much bigger ask of the
  screener answering it.)
- Should `cross_border` and `children_vulnerable` (1 cluster each) get their own
  screening question at all, or fold into a general "special categories" question — as
  single-cluster domains they're arguably too narrow to be a "broad domain question" in
  the spirit of the original 9.
- Is a from-scratch cluster-based screening prompt worth writing now, or does it make
  more sense to fold this into WS #7 (per-cluster analyzer) directly, since that
  workstream is already redesigning how clusters get evaluated by Claude end-to-end and
  a screening pass built on the *old* per-cluster-question shape might need rework once
  WS #7 lands anyway? (My lean: do it after WS #7's spike (WS #5) reports back — building
  a second cluster-facing Claude interface before knowing what WS #7's actual cluster
  evaluation contract looks like risks writing it twice.)

## Suggested sequencing

Given the last open question above, my recommendation is **don't schedule this
immediately** — let WS #4 land, then WS #5's spike (per plan §9.3), and revisit this
brief once WS #5's verdict is in. If the spike confirms the per-cluster analyzer
direction, this screening redesign should probably be designed *together* with WS #7's
Claude-call contract rather than as a separate, earlier piece of work that WS #7 might
then have to adapt to.
