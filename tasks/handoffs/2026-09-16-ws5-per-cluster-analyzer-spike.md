# WS #5 — Spike: per-cluster analyzer feasibility

**Date:** 2026-09-16
**Branch:** `spike/per-cluster-analyzer`, off `main` — **throwaway**. Nothing here merges;
only the verdict and the learnings survive.
**Owner:** Claude (this is exploratory prompt design + evaluation judgment, not a
mechanical spec — per plan §1.1, not a Codex task).
**Precondition:** WS #4 landed (needed so `scoring.py`'s cluster-verdict reduction works
for a single non-DPDPA framework too — see Method, step 4).
**Context:** `tasks/multi-framework-demo-plan.md` §3 (original WS #5) and §9.5 (2026-09-16:
folds in the contract requirements the approved screening spec named). This spike's
sole job is a **go/no-go decision for WS #7**, not a shippable feature.

---

## Goal

Prove or disprove, with real numbers: **one Claude call per UCC cluster, batching that
cluster's member controls across whichever frameworks are selected, produces
per-control assessments as good as today's per-framework two-call analyzer — at
acceptable latency and cost.**

If it holds up, WS #7 builds the real thing on this contract. If it doesn't, WS #7 gets
redesigned as a per-domain analyzer instead (plan §3, §6 risk register) before a week
gets spent on it.

---

## The design question this spike must actually answer

The approved screening spec (`tasks/handoffs/2026-09-15-multi-framework-screening-spec.md`)
already settled one important boundary: **a screening signal is cluster-level and
advisory; a final verdict stays evidence-backed, scored, and per-control.** That
principle should carry over here. So the spike tests this shape specifically, not "does
Claude give one verdict per cluster":

> One Claude call, scoped to one cluster, returns a `compliance_status` (etc.) **per
> member control** — the same per-control assessment shape the current two-call
> analyzer already produces, just narrowed to that cluster's controls across the
> assessment's selected frameworks instead of one framework's full 41-94 controls.
> The existing (WS #4-generalized) `_build_cluster_verdicts()` worst-case reduction
> then turns those per-control results into the cluster verdict — unchanged,
> reused, not reinvented.

Do not test or default to "Claude decides one collapsed status for the whole cluster
directly" — that would duplicate the deterministic-scoring invariant this codebase
already enforces (`CLAUDE.md`: "Scoring is deterministic, server-side — never Claude").
If the per-control-within-cluster shape turns out to be unworkable for some concrete
reason, that finding itself is a valid spike result — write it down and flag it,
don't quietly fall back to the other shape without saying so.

---

## Scope — 5 hand-picked clusters, chosen for real footprint variety

Picked directly from `CONTROL_CLUSTERS` and cross-checked against
`tests/fixtures/canonical_dpdpa/expected/analyzer_output.json` (so a comparison
baseline already exists for every control below — see the caveat under Method, step 3):

| Cluster | Topic | Members | DPDPA controls | Why this one |
|---|---|---|---|---|
| `CLUSTER_006` | Access Control Baseline | 13 across 6 frameworks | `CH2.SECURITY.1` (non_compliant/high), `CH2.SECURITY.2` (compliant/low) | Largest cross-framework fan-out in the DPDPA-touching set — stress-tests whether one call can hold 6 frameworks' worth of context without diluting per-control precision. |
| `CLUSTER_029` | Consent Governance, Records & Granularity | 9 across 3 frameworks | 6 DPDPA controls (`CH2.CONSENT.1/2`, `CM.RECORDS.1/2`, `CM.GRANULAR.1/2`) — mixed compliant/partial/non_compliant | Heaviest single-cluster DPDPA control count — tests whether Claude keeps 6 *different* verdicts straight within one cluster call instead of converging them toward one answer. |
| `CLUSTER_017` | Regulatory & Supervisory Breach Notification | 10 across 5 frameworks | `BN.NOTIFY.1` (partially_compliant/high) | Medium cross-framework, and the fixture's breach evidence is the kind of "policy exists, operational follow-through unclear" case the skepticism rules (`prompts.py`'s "policy ≠ implementation") are meant to catch — good test of whether cluster-scoped evidence filtering preserves that judgment. |
| `CLUSTER_022` | Privacy Contact Point & Complaint Intake | 3, DPDPA-only | `CH2.NOTICE.3` (partially_compliant), `CH3.GRIEVANCE.1` (compliant), `CH3.GRIEVANCE.2` (partially_compliant) | No cross-framework fan-out at all — isolates "does the cluster-scoped call even work" from "does it work across frameworks," a clean baseline. |
| `CLUSTER_032` | Children's Data & Age Verification | 4, DPDPA-only | `CH4.CHILD.1/2` (non_compliant), `CH4.CHILD.3` (compliant), `CH2.CONSENT.5` (non_compliant) | Smallest, sparsest evidence footprint of the five — the canonical fixture has essentially no children's-data evidence, so this tests "absence of evidence is evidence of absence" under a tightly-scoped, evidence-starved prompt rather than a full-document dump. |

---

## Method

1. **Build a spike-local `ClusterScope`** (throwaway dataclass, not the production type
   WS #7 will define) with exactly the fields the approved screening spec names for
   `ClusterScope`: `cluster_id`, `domain_group` (read from `CONTROL_CLUSTERS`, not
   re-inferred from tags), `topic`, `primary_question`, `primary_guidance`,
   `criticality`, and the member controls for the *selected* frameworks only — for this
   spike that's just `["dpdpa"]`, so `ClusterScope` degenerates to the DPDPA member(s)
   of each of the 5 clusters above. (The multi-framework case is exactly what CLUSTER_006
   and CLUSTER_017 exercise once you re-run the spike with `["dpdpa", "iso27001"]` per
   step 6 below — don't skip that re-run, it's the actual point of the spike.)
2. **Build a spike-local `ClusterContext` assembler** — organization/risk profile (from
   the canonical fixture), the cluster's member-control questionnaire answers (from
   `tests/fixtures/canonical_dpdpa/questionnaire_answers.json`), desk-review evidence
   filtered to that cluster's member requirement IDs only (not the whole document dump —
   this filtering is the efficiency claim WS #7 depends on, so test it doesn't lose
   relevant evidence by being too narrow), and the relevant excerpt of
   `tests/fixtures/canonical_dpdpa/evidence/*` documents. There is no domain-screening
   answer to include yet (screening isn't built) — that's fine, note it as a gap the real
   WS #7 build will need to backfill once cluster screening exists.
3. **Establish a real comparison baseline — do not use the canonical fixture's
   `expected/analyzer_output.json` as ground truth.** That file's provenance is
   documented (`tasks/handoffs/2026-09-09-ws1-ws2-ws3-results.md`) as
   `synthetic_offline_characterization` — a recorded/replayed response built to make the
   golden tests deterministic, not a genuine model judgment. Comparing a new prompt
   design against it would be circular (of course a well-built cluster prompt could be
   tuned to match a static recorded answer). Instead: run the **actual current
   `run_gap_analysis()`** two-call analyzer live, once, against the canonical fixture's
   real inputs (`USE_LIVE_ANALYZER=1`, per `tests/support/fixture_capture.py`'s existing
   `--live` opt-in), and use *that* live output as the baseline for all 5 clusters. This
   costs one extra live call up front but is the only non-circular comparison available.
4. For each of the 5 clusters, call Claude once with the `ClusterScope`+`ClusterContext`
   prompt, requesting structured per-control output for just that cluster's DPDPA
   member(s). Parse it the same way `_parse_json_response()` does today (reuse it,
   don't reinvent).
5. Compare each cluster's per-control verdicts against the live two-call baseline from
   step 3. Record: does `compliance_status` match, or is it defensibly different on
   manual read (not just different)?
6. **Re-run steps 1-5 with `framework_ids=["dpdpa", "iso27001"]`** for `CLUSTER_006` and
   `CLUSTER_017` specifically (the two with real ISO27001 co-members) — a spike that
   only ever tested DPDPA-alone clusters hasn't actually tested the multi-framework
   claim this whole workstream exists to de-risk.
7. Record for every call: wall-clock latency, input tokens, output tokens, whether JSON
   parsing succeeded on the first attempt.

---

## Interfaces (spike-local, not production — WS #7 formalizes these based on what works)

- `ClusterScope` — per the approved screening spec's field list (§ "Stable identity and
  scope"). Build it as a plain dataclass or dict; don't wire it into `app/frameworks/`
  yet.
- `ClusterContext` — per the approved screening spec's field list (§ "Context
  assembly"), minus the domain-screening-answer field (doesn't exist yet).
- Reuse `_parse_json_response()` from `app/services/claude_analyzer.py` for parsing —
  don't write a second JSON-fence-stripping parser.
- Reuse `_build_cluster_verdicts()` (once WS #4 lands, so it accepts any single
  `framework_id`) to reduce the spike's per-control outputs into cluster verdicts, for
  a sanity check that the shape is actually reducible the way production scoring expects.

## Non-goals

- Do not build `ClusterContext`/`ClusterScope` as real, importable modules under
  `app/frameworks/` or `app/services/` — this branch is thrown away regardless of
  verdict; only the go/no-go decision and this document's findings persist.
- Do not touch `screening.py`, `question_engine.py`, or the router layer.
- Do not attempt the cross-framework combined verdict (one number spanning DPDPA+ISO
  for a shared cluster) — that reduction logic doesn't exist yet (WS #4 explicitly
  defers it to WS #7) and isn't this spike's question.
- Do not optimize prompt cost/latency beyond what's needed to get an honest read —
  this is a feasibility measurement, not a production tuning pass.

---

## Done criteria — the go/no-go decision (unchanged from the original plan)

- **≥4 of 5 clusters** (counting the `dpdpa`-only run; the `["dpdpa","iso27001"]` re-run
  on CLUSTER_006/017 is additional evidence, not double-counted into this ratio) produce
  a `compliance_status` per control that matches the live two-call baseline, or is
  defensibly better on manual inspection (write down why, don't just assert it).
- **Median latency per cluster call < 15s.**
- **Zero JSON parse failures** across all calls (5 DPDPA-only + 2 multi-framework re-runs
  = 7 calls minimum).
- **Cost projection < $5 per full assessment.** Use the measured input/output token
  averages × **53** cluster/singleton calls (52 shared clusters + 1 intentional ISO
  singleton, `ISO.A5.32` — the correct count for a DPDPA+ISO27001+NIST-CSF assessment;
  don't reuse the plan's original rough "~80" estimate, it predates WS #6 actually
  finishing the clustering and is no longer the right number).

**If it fails:** don't try to rescue it by re-prompting inside the spike. Write down
which criterion failed and by how much, then stop — that's the trigger in plan §6 to
redesign WS #7 as a per-domain analyzer (9 calls) instead, not a signal to iterate
further on this branch.

## Adversarial pass (per plan §1.4 and §5 checkpoint α)

Before writing up the verdict, argue against your own result once: "this spike is going
to fail in production — give the three most likely reasons why," then check whether any
of those three are actually visible in the 7 calls you just made (e.g., evidence
filtering too aggressive and dropping a relevant quote, cluster-scoped context missing
information a full-framework call would have had, latency variance hidden by only
sampling 5-7 calls). Report this section honestly even if the headline numbers pass.

## Output

A short write-up (`tasks/handoffs/<date>-ws5-spike-results.md`) with: the raw
per-cluster comparison table, the four done-criteria numbers, the adversarial-pass
findings, and an explicit **GO / NO-GO / REDESIGN** verdict for WS #7. Delete the
`spike/per-cluster-analyzer` branch after the write-up is committed — the code was
never the deliverable.

## Rollback

N/A — this is a throwaway branch with no merge target. If it needs to be abandoned
mid-spike, `git branch -D spike/per-cluster-analyzer` and note why in
`tasks/todo.md`.
