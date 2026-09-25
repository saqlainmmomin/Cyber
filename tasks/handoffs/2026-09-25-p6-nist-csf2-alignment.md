# P6-NIST: Align the NIST CSF pack with CSF 2.0

This task makes `app/frameworks/definitions/nist_csf.py` match the NIST CSF 2.0 Core (NIST CSWP 29, 26 Feb 2024, Appendix A).
- It removes one withdrawn subcategory and adds the 13 that are missing, so the pack goes from **94 to 106** controls. That is the full CSF 2.0 Core.
- It corrects outcome text and titles that departed from CSF 2.0.
- It brings the UCC cluster mappings, evidence requests, the batching tests and the P6-2c criteria coverage rule along with it.

DPDPA and ISO 27001 behaviour stays byte-identical.

**Plan:** `docs/plans/2026-09-25-001-grounded-analysis-and-deliverables-plan.md`. It lists NIST as the third criteria pack (D-P6-D, "NIST CSF (94)"), and its licensing rule is D4: own words, references only. The findings come from the P6-2c NIST criteria drafter's report (PR #58). The designer checked every finding used below against the CSF 2.0 PDF, Appendix A pp. 15-23.
**Owner:** Claude designs (this file) and authors all regulatory content in it → Codex implements → Claude reviews. Per `tasks/agent-ownership.md` this counts as judgment work: framework content and UCC mapping. Codex does **not** author any control text, delta text or criteria. Every string Codex needs is written out below.
**Branch / worktree:** `codex/p6-nist-csf2-alignment` in `../dpdpa-gap-tool-nist-csf2`, from `origin/main` @ `9cd3208`. That commit already has PR #57 (P6-1b batching) and PR #58 (P6-2c criteria drafts) merged.
**Depends on:** #57 and #58, both merged 2026-09-25.
**Blocks:**
- The P6-2c follow-up, where the orchestrator drafts criteria for the 13 new subcategories (D-NIST-J).
- Saqlain's sign-off on the NIST criteria sheet.
- The P5-9 NIST question-pack re-export. That re-export is **Saqlain's step** after merge, and it is out of scope here.

**Codex cannot write `.git`.** The orchestrator creates the worktree, keeps local `main` at `origin/main`, commits and opens the PR.

> **If the code forces a deviation from this design, stop and report it in `## Results`. Do not pick an alternative.** That applies to every id, title, description, criticality, cluster placement, delta string, evidence mapping, test update and rule below.

> **DPDPA and ISO 27001 must stay byte-identical. This is a hard constraint.**
> - Their prompt fingerprints must still equal the values pinned on `main` in `tests/test_p6_1b_framework_batching.py`.
> - `tests/test_golden_dpdpa.py` must pass unmodified.
> - `app/dpdpa/**`, `tests/fixtures/**`, `tests/support/**` and every other framework definition stay untouched.

> **Answer-key independence (D-P5-9-C).** Do not open, grep, list or read any of the following:
> - anything under `validation/` (answer keys and client-visible packs alike)
> - `tasks/handoffs/*p5-9*`
> - `docs/plans/2026-09-24-002-*`
> - `scripts/seed_test_companies.py`, `scripts/test_ground_truth.json`, `scripts/seed-v2-prompt.md`
> - any `answer_key.json`
>
> Also do not open `scripts/validation/**`. This task does not need it. The content below comes only from the CSF 2.0 Core. Nothing is tuned toward a planted gap. `tests/test_answer_key_isolation.py` forbids the strings `answer_key`, `validation/companies`, `scripts.validation` and `scripts/validation` anywhere under `app/`, so keep them out of comments and docstrings too.

## Why

The P6-2c drafter compared the pack with the CSF 2.0 Core. The designer re-checked each point against the PDF:

1. **`NIST.RS.CO.04` is not a CSF 2.0 subcategory.** The CSF 2.0 RS.CO category has only RS.CO-02 and RS.CO-03 (PDF p.22). The pack's RS.CO.04 text is CSF 1.1's RS.CO-05 (voluntary sharing), which CSF 2.0 folded into RS.CO-03. The pack therefore asks the same thing twice, and a withdrawn outcome is scored.
2. **13 subcategories are missing:**
   - GV.RM-05, GV.RM-06, GV.RM-07 (p.16)
   - GV.SC-06 to GV.SC-10 (p.18)
   - ID.RA-07 to ID.RA-10 (p.19)
   - ID.IM-04 (p.19)

   Three gaps matter most:
   - Nothing in the pack asks whether an incident response plan **exists** (ID.IM-04).
   - Nothing asks about change management (ID.RA-07).
   - Nothing asks about ongoing supplier risk (GV.SC-07).
3. **Outcome text drifts from CSF 2.0:**
   - GV.OC-05: the pack says "determined and prioritized". CSF 2.0 says "understood and communicated".
   - GV.OV-03: the pack says "improved from lessons learned". CSF 2.0 says "performance is evaluated and reviewed".
   - PR.PS-01: the pack narrows it to network infrastructure, in CSF 1.1 style. In CSF 2.0 it covers configuration management generally.
   - Smaller drift: GV.RR-01 drops "ethical, and continually improving". GV.OC-02 and GV.OC-04 are weakened.
4. **Titles contradict their own outcomes:**
   - DE.AE-06 and DE.AE-08 are swapped.
   - DE.AE-02 and DE.AE-03 are shifted by one.
   - The GV.OV-02 and GV.OV-03 titles are wrong.
   - Also wrong: ID.AM-08, PR.AT-02, RS.MA-02, RS.MA-05, RS.AN-07, RS.CO-02, PR.IR-02, RC.RP-03, GV.SC-02, GV.SC-04.

   This matters because every NIST questionnaire question is generated from the title (`"Has your organization implemented {title.lower()}? ({reference})"`), so a wrong title means the client is asked the wrong thing.
5. **About 20 UCC delta strings describe a different subcategory**, and they are shown to clients as follow-up questions. Examples:
   - The PR.PS-01..05 deltas are shifted.
   - The DE.AE-08 delta says "anomalies".
   - The PR.AA-06 delta says "least privilege", but PR.AA-06 is physical access.

   Four NIST controls also sit in the wrong cluster (D-NIST-F).
6. **The module docstring says 82 controls with the wrong per-function counts.** The actual count is 94 today and will be 106 after this task.

## Step 0 (before writing code)

1. **Set up (orchestrator).** Run `git fetch origin && git branch -f main origin/main`. The primary checkout is on another branch, so this is safe. Then run `git worktree add ../dpdpa-gap-tool-nist-csf2 -b codex/p6-nist-csf2-alignment origin/main`, symlink `.venv`, and copy `.env`.
2. **Baseline tests.** Run `.venv/bin/pytest -q`. Record the pass/skip/fail counts and the `main` commit in `## Results`. These failures are known and pre-existing:
   - `tests/test_remediation_tracking.py::test_scenario_10_engagement_rollup_and_tracker_page` (a hardcoded date)
   - `tests/test_p5_4_adaptive_ucc_questionnaire.py::test_scenario_13_structural_guards` (a stale two-dot guard; it also pins `app/frameworks`, and it stays failing)
   - `tests/test_longitudinal_demo.py::test_scenario_9_rollups_and_integrated_reporting` (intermittent)

   If anything else fails on unmodified `main`, stop and report.
3. **Record the prompt fingerprints on `main`, before any edit.** Use the snippet from `tasks/handoffs/2026-09-25-p6-1b-v1-framework-batching.md` Step 0.3, and paste its output into Results. Expected values:
   ```
   dpdpa system 3fc4f1c3ff6b62124716f6ca5ef29e1dd39461817d168fa4b047c2bef92e4ea6
   dpdpa user de658c512943c954425ea004165af0dd1cd88ade82f7376ac98d08aa957b3751
   iso27001 system 3c3bad7bd8818c1d5b28730e4462bbf91f2208b1eae32b89459e8e2d698116b3
   iso27001 user 6fe08745ef96857b893c623d0f468d2abca2aa6c3395affc64145807acedfd61
   iso27001 desk 9d2e926bae35b23030085da6e528b03df63c9352006cb0bb8948800a251222b2
   nist_csf system c8ddf65a8220b571733a65298503f3aff65be22ca6c21413216282f982ddf121
   nist_csf user 9fa1ded32cda08bb882873f83bb2d13e1b20a9a1b0fa84c45690569e02bb283f
   nist_csf desk 14705771d2e67febe08ab3a58e022039aea1a4360aef37a0ae0595fa25d414ec
   ```
   The six DPDPA and ISO lines must still be identical after your change. The three NIST lines will change; record the new values.
4. **Confirm these facts on `main` @ `9cd3208`. If any is false, stop and report.**
   1. `NIST_CSF_DEFINITION.control_count() == 94`. The per-domain counts are 23/16/22/11/14/8. `NIST.RS.CO.04` exists with reference `RS.CO-04`.
   2. `app/frameworks/mappings/clusters.py` maps all 94 NIST ids, each exactly once. `INTENTIONAL_SINGLETONS["nist_csf"] == set()`. `NIST.RS.CO.04` sits in `CLUSTER_017`.
   3. `_NIST_CSF_EVIDENCE_REQUESTS` has 24 entries. The only controls no request maps are `NIST.DE.AE.07`, `NIST.PR.IR.04` and `NIST.RS.CO.04`.
   4. `_generate_nist_csf_questions()` builds every NIST question from `ctrl.title`, `ctrl.reference` and `ctrl.description`. There are no hand-written NIST questions.
   5. `app/frameworks/batching.py::control_batches("nist_csf")` returns 6 batches, one per function, with `llm_batch_threshold_controls == 90` and `llm_batch_max_controls == 25`. Singleton batches are merged across domains after packing.
   6. `app/frameworks/criteria/nist_csf_draft.py` has `NIST_CSF_CRITERIA_DRAFT` keyed by all 94 pack ids in order. The `NIST.RS.CO.04` entry uses the module constant `_RSCO04` as its `in_force_note`, and no other entry uses `_RSCO04`. `NIST_CSF_CRITERIA_REVIEW_META` is filled by `_criteria(...)`.
   7. `scripts/export_criteria_review.py::build_rows` indexes `draft[req["id"]]` for every pack requirement, so a pack id with no draft entry raises `KeyError`.
   8. `tests/test_p6_2c_iso_nist_criteria.py::test_nist_covers_every_pack_requirement_in_order` asserts `len(NIST_IDS) == 94` and `list(NIST_CSF_CRITERIA_DRAFT) == NIST_IDS`. `test_committed_sheets_match_the_drafts` re-exports `tasks/criteria-review/nist-csf-criteria-v1.csv`, whose `requirement_title` column comes from the pack.
   9. `app/frameworks/compat.py` only delegates to the registry and has no id-alias mechanism. Readers of persisted rows look up controls tolerantly:
      - `conclusion_review._requirement_titles(...)` is read with `.get`, and unknown ids sort last.
      - `routers/analysis.py` falls back when `fw_ctrl_map.get(req_id)` is `None`.
      - `question_engine` skips ids that are not in the current registry.
      - `scoring._derive_framework_score` iterates the current `all_controls()`.
   10. `scope_profiler.compute_scope_multi` persists an explicit list of every NIST id as `Assessment.applicable_requirements` at scoping time (`routers/web.py` ~L1082). NIST has no exclusions and no applicability proposals.

## Goal

1. The pack is exactly the CSF 2.0 Core: 106 subcategories, correct outcomes and titles, and nothing withdrawn.
2. Every NIST control is clustered exactly once, and every NIST delta describes its own subcategory.
3. Every NIST control is mapped by at least one evidence request.
4. The NIST batch plan, prompt fingerprints and count-pinning tests are updated to the new pack. DPDPA and ISO are unchanged.
5. The P6-2c criteria draft stays a consistent draft. Codex authors no criteria. The 13 new ids are named as pending (D-NIST-J).
6. Persisted history is left as it is, and readers keep tolerating the removed id (D-NIST-I).

## Decisions (made here so they are not relitigated)

### D-NIST-A: Id scheme

New controls use the pack's existing scheme: `id="NIST.<FN>.<CAT>.<NN>"`, with `reference="<FN>.<CAT>-<NN>"` (two-digit, hyphenated like CSF). For example, `NIST.GV.RM.05` has reference `GV.RM-05`. Each new control goes into its CSF category's existing `Section`, in numeric order after the category's current last control. No new sections and no new domains are added.

### D-NIST-B: `NIST.RS.CO.04` is removed, with no alias

Delete the `Control` from `_RS_CO`, its `CLUSTER_017` member, and its criteria-draft entry (D-NIST-J). Do not add an alias, a deprecation flag or a remap. Reasons:
- **It was withdrawn in CSF 2.0.** Its content is covered by RS.CO-03 (information shared with designated stakeholders), which the pack already has. A remap would point it at a control that already exists and would double-count it.
- **An alias would be new infrastructure for a single id.** `compat.py` has no alias concept (fact 9). Scoring, questionnaire and prompts would all need to learn one, and that would change DPDPA and ISO code paths.
- **No evidence request maps it**, and its two draft criteria were both `low` "duplicates RS.CO.03".
- **Old rows stay readable** without any alias (D-NIST-I).

### D-NIST-C: The 13 new controls

The descriptions are own words (D4). They paraphrase the outcome and do not reproduce it. **Use these strings exactly.** Criticality uses the pack's existing scale. The criticality reasoning is: an outcome whose absence leaves a whole response or supplier capability unevidenced is `critical` or `high`; supporting process outcomes are `medium`; opportunity framing is `low`.

| id | reference | title | description | criticality | tags |
|---|---|---|---|---|---|
| `NIST.GV.RM.05` | `GV.RM-05` | Risk communication lines | Defined channels exist across the organization for raising and escalating cybersecurity risk, including risk that originates with suppliers and other third parties. | medium | `["governance", "risk-communication", "escalation", "third-party"]` |
| `NIST.GV.RM.06` | `GV.RM-06` | Standardized risk method | Cybersecurity risks are calculated, recorded, categorized and prioritized using one documented method that is shared across the organization. | high | `["governance", "risk-methodology", "risk-scoring", "prioritization"]` |
| `NIST.GV.RM.07` | `GV.RM-07` | Positive risk consideration | Opportunities (positive risks) are described and brought into the organization's cybersecurity risk discussions alongside threats. | low | `["governance", "risk-management", "opportunities"]` |
| `NIST.GV.SC.06` | `GV.SC-06` | Supplier pre-engagement due diligence | Before a formal relationship with a supplier or other third party begins, the organization plans for it and performs due diligence to reduce the associated risk. | high | `["supply-chain", "due-diligence", "onboarding", "third-party"]` |
| `NIST.GV.SC.07` | `GV.SC-07` | Supplier risk management over the relationship | Risks from each supplier, its products and services, and other third parties are identified, recorded, prioritized, assessed, treated and monitored for as long as the relationship lasts. | high | `["supply-chain", "third-party", "supplier-monitoring", "risk-assessment"]` |
| `NIST.GV.SC.08` | `GV.SC-08` | Suppliers in incident planning and recovery | Relevant suppliers and other third parties take part in the organization's incident planning, response and recovery activities. | medium | `["supply-chain", "incident-response", "recovery", "third-party"]` |
| `NIST.GV.SC.09` | `GV.SC-09` | Supply chain security across the life cycle | Supply chain security practices form part of the cybersecurity and enterprise risk programs, and how well they perform is monitored across the life cycle of technology products and services. | medium | `["supply-chain", "lifecycle-management", "performance-monitoring"]` |
| `NIST.GV.SC.10` | `GV.SC-10` | Supplier exit provisions | Supply chain risk management plans cover what must happen when a partnership or service agreement ends. | medium | `["supply-chain", "offboarding", "contracts", "termination"]` |
| `NIST.ID.RA.07` | `ID.RA-07` | Change and exception management | Changes and exceptions are controlled, evaluated for their effect on risk, recorded and tracked to closure. | high | `["risk-assessment", "change-management", "exceptions", "risk-acceptance"]` |
| `NIST.ID.RA.08` | `ID.RA-08` | Vulnerability disclosure handling | Established processes exist to receive, analyze and respond to vulnerabilities reported to the organization. | medium | `["risk-assessment", "vulnerability-disclosure", "vulnerability-management"]` |
| `NIST.ID.RA.09` | `ID.RA-09` | Hardware and software integrity verification | Hardware and software are checked for authenticity and integrity before they are acquired and put into use. | medium | `["risk-assessment", "integrity", "authenticity", "acquisition"]` |
| `NIST.ID.RA.10` | `ID.RA-10` | Critical supplier pre-acquisition assessment | Suppliers judged critical are assessed before their products or services are acquired. | high | `["risk-assessment", "supply-chain", "critical-suppliers", "acquisition"]` |
| `NIST.ID.IM.04` | `ID.IM-04` | Incident response and operational cyber plans | Incident response plans and other cybersecurity plans that affect operations exist and are communicated, kept current and improved. | critical | `["improvement", "incident-response-plan", "planning", "business-continuity"]` |

**Questions.** No explicit questions are added. `_generate_nist_csf_questions()` stays as it is and produces, for example, "Has your organization implemented supplier exit provisions? (GV.SC-10)". The titles above were chosen to read correctly in that template.

**Resulting per-section order and counts.** Scenario 1 pins these.

| Section | Count | Ids (in order) |
|---|---|---|
| gv_oc | 5 | OC.01–OC.05 |
| gv_rm | 7 | RM.01–RM.07 |
| gv_rr | 4 | RR.01–RR.04 |
| gv_po | 2 | PO.01–PO.02 |
| gv_ov | 3 | OV.01–OV.03 |
| gv_sc | 10 | SC.01–SC.10 |
| id_am | 7 | AM.01, 02, 03, 04, 05, 07, 08 |
| id_ra | 10 | RA.01–RA.10 |
| id_im | 4 | IM.01–IM.04 |
| pr_* | 22 | unchanged |
| de_* | 11 | unchanged ids |
| rs_ma, rs_an, rs_co, rs_mi | 5, 4, **2**, 2 | RS.CO.02, RS.CO.03 only |
| rc_* | 8 | unchanged |

Totals by function are GV 31, ID 21, PR 22, DE 11, RS 13, RC 8, which makes **106**. This matches CSF 2.0 Appendix A exactly.

### D-NIST-D: Corrections to existing controls

These change **only** the fields listed. Ids, references, criticality and weights stay the same. Descriptions are own words (D4).

**Description changes:**

| id | new description |
|---|---|
| `NIST.GV.OC.02` | Internal and external stakeholders are understood, and their needs and expectations about cybersecurity risk management are understood and taken into account. |
| `NIST.GV.OC.04` | Critical objectives, capabilities and services that external stakeholders rely on or expect from the organization are understood and communicated. |
| `NIST.GV.OC.05` | The outcomes, capabilities and services that the organization itself relies on are understood and communicated. |
| `NIST.GV.RR.01` | Leaders own and answer for cybersecurity risk, and build a culture that is risk-aware, ethical and committed to continual improvement. |
| `NIST.GV.OV.03` | The performance of organizational cybersecurity risk management is evaluated and reviewed to identify adjustments that are needed. |
| `NIST.PR.PS.01` | Configuration management practices are defined and applied across the organization's hardware, software and platforms. |

**Title changes.** The generated question text follows automatically.

| id | old title | new title |
|---|---|---|
| `NIST.GV.OC.05` | Outcomes and priorities | Organizational dependencies |
| `NIST.GV.OV.02` | Risk management performance | Risk strategy coverage review |
| `NIST.GV.OV.03` | Organizational risk management adjustments | Risk management performance evaluation |
| `NIST.GV.SC.02` | Supplier cybersecurity requirements | Supply chain roles and responsibilities |
| `NIST.GV.SC.04` | Supplier assessment | Supplier criticality prioritization |
| `NIST.ID.AM.08` | Systems and services in scope | Asset life-cycle management |
| `NIST.PR.AT.02` | Privileged user training | Specialized role training |
| `NIST.PR.IR.02` | Technology asset protection | Environmental threat protection |
| `NIST.DE.AE.02` | Event correlation | Adverse event analysis |
| `NIST.DE.AE.03` | Event aggregation | Event correlation |
| `NIST.DE.AE.06` | Incident declaration | Adverse event information distribution |
| `NIST.DE.AE.08` | Anomaly detection | Incident declaration |
| `NIST.RS.MA.02` | Incident triage and prioritization | Incident triage and validation |
| `NIST.RS.MA.05` | Incident criteria application | Recovery initiation criteria |
| `NIST.RS.AN.07` | Incident data collection and analysis | Incident data collection and preservation |
| `NIST.RS.CO.02` | Internal stakeholder notification | Stakeholder incident notification |
| `NIST.RC.RP.03` | Recovery verification | Restoration asset integrity verification |

**Tag changes** (the swapped detection tags only):

| id | new tags |
|---|---|
| `NIST.DE.AE.02` | `["detection", "event-analysis", "siem"]` |
| `NIST.DE.AE.03` | `["detection", "correlation", "log-correlation"]` |
| `NIST.DE.AE.06` | `["detection", "alerting", "information-distribution"]` |
| `NIST.DE.AE.08` | `["detection", "incident-declaration", "incident-criteria", "thresholds"]` |
| `NIST.GV.OV.03` | `["governance", "oversight", "performance-measurement"]` |
| `NIST.GV.OV.02` | `["governance", "oversight", "strategy-review"]` |

**Module docstring.** Replace it with this text:

```
NIST Cybersecurity Framework (CSF) 2.0 definition.

Covers the complete CSF 2.0 Core (NIST CSWP 29, February 2024, Appendix A):
106 subcategories across 6 functions and 22 categories.
  - Govern (31)   - Identify (21)   - Protect (22)
  - Detect (11)   - Respond (13)    - Recover (8)

Ids follow NIST.<FUNCTION>.<CATEGORY>.<NN>; `reference` carries the CSF
identifier (e.g. GV.RM-05). Gaps in numbering are CSF 2.0's own (subcategories
relocated from CSF 1.1). Titles and descriptions are the pack's own wording and
reference the CSF outcome rather than reproduce it.
```

**Why the other ~87 near-verbatim descriptions are not rewritten here.** CSF 2.0 is a US Government work, so there is no licensing exposure, unlike ISO (E-C5). A full own-words rewrite is a separate content decision (see the question for Saqlain in Results). This task only fixes wording that departs from CSF 2.0.

### D-NIST-E: Section and domain weights are unchanged

`scoring.compute_framework_scores` averages control outcomes within a section, then takes a weighted average of sections using `Section.weight`, then of domains using `Domain.weight`. The weights express how much a category matters, not how many controls it has, so all section and domain weights stay the same. Effects to state in the PR:
- GV.SC's section score now averages 10 outcomes instead of 5, at weight 0.20 within Govern.
- ID.RA averages 10 instead of 6 (0.40).
- GV.RM averages 7 instead of 4 (0.20).
- ID.IM averages 4 instead of 3 (0.25).
- RS.CO averages 2 instead of 3 (0.25).
- Per-domain weights still sum to 1.0.
- No DPDPA or ISO score changes.

### D-NIST-F: UCC cluster mapping (`app/frameworks/mappings/clusters.py`)

Match rows by **control id**. The cluster ids are there for orientation.

**1. Remove** `_control("nist_csf", "NIST.RS.CO.04", ...)` from `CLUSTER_017`.

**2. Add new members.** Append each one at the **end** of the named cluster's `controls` list, in this table's order:

| id | cluster | delta |
|---|---|---|
| `NIST.GV.RM.05` | CLUSTER_035 | NIST also expects defined lines of communication for cybersecurity risk, including risk from suppliers and other third parties. |
| `NIST.GV.RM.06` | CLUSTER_035 | NIST expects one standard method for calculating, recording, categorizing and prioritizing cybersecurity risk. |
| `NIST.GV.RM.07` | CLUSTER_035 | NIST also expects opportunities (positive risks) to be described and included in risk discussions. |
| `NIST.GV.SC.06` | CLUSTER_010 | NIST expects planning and due diligence before a supplier or third-party relationship is formalized. |
| `NIST.ID.RA.10` | CLUSTER_010 | NIST expects critical suppliers to be assessed before their products or services are acquired. |
| `NIST.GV.SC.10` | CLUSTER_011 | NIST expects supply chain plans to cover obligations that continue after an agreement ends. |
| `NIST.GV.SC.08` | CLUSTER_012 | NIST expects relevant suppliers to take part in incident planning, response and recovery. |
| `NIST.GV.SC.09` | CLUSTER_012 | NIST also expects supply chain security practices to be monitored across the product and service life cycle. |
| `NIST.ID.RA.09` | CLUSTER_012 | NIST expects hardware and software to be checked for authenticity and integrity before acquisition and use. |
| `NIST.GV.SC.07` | CLUSTER_013 | NIST expects supplier risk to be assessed, treated and monitored for the whole relationship. |
| `NIST.ID.IM.04` | CLUSTER_014 | NIST expects incident response and other operational cybersecurity plans to be established, communicated, maintained and improved. |
| `NIST.ID.RA.08` | CLUSTER_043 | NIST expects a process to receive, analyze and respond to vulnerability disclosures. |
| `NIST.ID.RA.07` | CLUSTER_044 | NIST expects changes and exceptions to be assessed for risk impact, recorded and tracked. |

**3. Move misplaced members.** Remove each from its current cluster, append it to the end of the new one, and use the new delta:

| id | from → to | delta | why |
|---|---|---|---|
| `NIST.PR.AA.06` | CLUSTER_006 → CLUSTER_045 | NIST expects physical access to assets to be managed, monitored and enforced according to risk. | PR.AA-06 is physical access, not logical least privilege |
| `NIST.PR.IR.02` | CLUSTER_014 → CLUSTER_045 | NIST expects technology assets to be protected from environmental threats. | environmental protection, not incident handling |
| `NIST.PR.IR.03` | CLUSTER_040 → CLUSTER_019 | NIST expects mechanisms that meet resilience requirements in both normal and adverse conditions. | resilience, not network topology |
| `NIST.GV.SC.02` | CLUSTER_013 → CLUSTER_011 | NIST expects cybersecurity roles and responsibilities for suppliers, customers and partners to be set, communicated and coordinated. | roles and terms with suppliers; ongoing monitoring is now GV.SC-07 |

**4. Rewrite deltas in place.** The cluster stays the same; only the third argument changes.

| id | new delta |
|---|---|
| `NIST.GV.SC.04` | NIST also expects suppliers to be known and prioritized by criticality. |
| `NIST.RS.MA.02` | NIST expects incident reports to be triaged and validated. |
| `NIST.RS.MA.05` | NIST expects defined criteria for starting incident recovery to be applied. |
| `NIST.DE.AE.06` | NIST expects information on adverse events to reach authorized staff and tools. |
| `NIST.ID.IM.01` | NIST expects improvements to be identified from evaluations such as assessments and audits. |
| `NIST.ID.IM.03` | NIST expects improvements to be identified from running day-to-day processes and activities. |
| `NIST.RS.CO.02` | NIST expects internal and external stakeholders to be notified of incidents. |
| `NIST.RS.CO.03` | NIST also expects information to be shared with designated internal and external stakeholders. |
| `NIST.RC.RP.03` | NIST expects backups and other restoration assets to be checked for integrity before they are used. |
| `NIST.RC.CO.03` | NIST expects recovery progress to be communicated to designated internal and external stakeholders. |
| `NIST.ID.AM.07` | NIST expects inventories of data and related metadata to be maintained for designated data types. |
| `NIST.ID.RA.04` | NIST expects potential impacts and likelihoods of threats exploiting vulnerabilities to be identified and recorded. |
| `NIST.GV.RM.03` | NIST expects cybersecurity risk management to be part of enterprise risk management. |
| `NIST.PR.PS.01` | NIST expects configuration management practices to be established and applied. |
| `NIST.PR.PS.02` | NIST expects software to be maintained, replaced and removed according to risk. |
| `NIST.PR.PS.03` | NIST expects hardware to be maintained, replaced and removed according to risk. |
| `NIST.PR.PS.05` | NIST expects installation and execution of unauthorized software to be prevented. |
| `NIST.DE.AE.08` | NIST expects incidents to be declared when adverse events meet defined incident criteria. |
| `NIST.GV.OC.05` | NIST expects the outcomes, capabilities and services the organization depends on to be understood and communicated. |
| `NIST.GV.OV.02` | NIST expects the risk strategy to be reviewed and adjusted so it covers organizational requirements and risks. |
| `NIST.GV.OV.03` | NIST expects risk management performance to be evaluated and reviewed for needed adjustments. |

**What stays unchanged:**
- No other cluster's primary question, guidance, tags, criticality or `domain_group`.
- No non-NIST member.
- `INTENTIONAL_SINGLETONS["nist_csf"]` stays `set()`.
- `CLUSTER_001`'s NIST membership stays at 6, which `tests/test_picker_and_scoring_contract.py` pins.

After this, NIST coverage is 106/106, so `scoring._validated_cluster_mapping` needs no warning.

### D-NIST-G: Evidence requests (`_NIST_CSF_EVIDENCE_REQUESTS`)

Every NIST control ends up mapped by at least one request, and scenario 5 pins that. The `required` flags stay as they are. Changes:

| document_type | change to `maps_to` (order as written) | new `reason` (own words, references only) |
|---|---|---|
| `risk_management_strategy` | append `NIST.GV.RM.05`, `NIST.GV.RM.07` | Evidence for organisational context (GV.OC-01, GV.OC-04, GV.OC-05) and risk management strategy, risk communication and opportunity handling (GV.RM-01 to GV.RM-05, GV.RM-07). |
| `supplier_security` | insert `NIST.GV.SC.06` … `NIST.GV.SC.10` after `NIST.GV.SC.05`, then append `NIST.ID.RA.10` | Evidence for supply chain risk management across the supplier life cycle (GV.SC-01 to GV.SC-10), critical-supplier assessment before acquisition (ID.RA-10), external service inventory (ID.AM-04) and provider monitoring (DE.CM-06). |
| `risk_assessment` | append `NIST.GV.RM.06` | Evidence for threat identification, impact and likelihood, risk determination and response (ID.RA-03 to ID.RA-06) and the organisation's standard risk method (GV.RM-06). |
| `vulnerability_management` | append `NIST.ID.RA.08` | Evidence for vulnerability identification (ID.RA-01), threat intelligence (ID.RA-02), vulnerability disclosure handling (ID.RA-08) and software maintenance (PR.PS-02). |
| `configuration_baselines` | append `NIST.ID.RA.09`; **label** → `Secure configuration / hardening baselines, software execution controls and integrity checks for acquired hardware and software` | Evidence for configuration management, hardware maintenance and execution prevention (PR.PS-01, PR.PS-03, PR.PS-05) and authenticity and integrity checks before hardware and software are used (ID.RA-09). |
| `logging_monitoring` | replace `NIST.DE.AE.08` with `NIST.DE.AE.06`, then append `NIST.DE.AE.07` | Evidence for log generation (PR.PS-04), continuous monitoring (DE.CM-01, DE.CM-03, DE.CM-09) and adverse event analysis, correlation, distribution and threat context (DE.AE-02, DE.AE-03, DE.AE-06, DE.AE-07). |
| `breach_procedure` | new tuple: `("NIST.ID.IM.04", "NIST.RS.MA.01", "NIST.RS.MA.02", "NIST.RS.MA.03", "NIST.RS.MA.04", "NIST.RS.MA.05", "NIST.RS.MI.01", "NIST.RS.MI.02", "NIST.RS.CO.02", "NIST.RS.CO.03", "NIST.DE.AE.04", "NIST.DE.AE.08")` | Evidence for the incident response plan (ID.IM-04), incident management, containment, eradication and stakeholder communication (RS.MA-01 to RS.MA-05, RS.MI-01, RS.MI-02, RS.CO-02, RS.CO-03) and incident impact and declaration (DE.AE-04, DE.AE-08). |
| `business_continuity` | append `NIST.PR.IR.04` | Evidence for recovery plan execution and communication (RC.RP-01, RC.RP-02, RC.RP-04 to RC.RP-06, RC.CO-03, RC.CO-04) and resilience mechanisms and capacity (PR.IR-03, PR.IR-04). |
| **new** `change_management` | `("NIST.ID.RA.07",)`; label `Change management procedure, sample change records and the exception (risk acceptance) register`; `required=False` | Evidence for change and exception management (ID.RA-07). |

**Placement and merging.**
- Insert the new `change_management` request **immediately after `configuration_baselines`**.
- The NIST list becomes 25 entries. Its `document_type` order is the current `NIST_DOCUMENT_TYPES` with `"change_management"` inserted after `"configuration_baselines"`.
- ISO already has a `change_management` request, so `compute_scope_multi` merges the two into one RFI line for ISO + NIST assessments. That merge is the point of reusing the key.

### D-NIST-H: Dependencies and root-cause hints

In `_NIST_CSF_DEPENDENCIES`:
- **Add:**
  - `"NIST.GV.RM.06": ["NIST.GV.RM.01"]`
  - `"NIST.GV.SC.06": ["NIST.GV.SC.01"]`
  - `"NIST.GV.SC.07": ["NIST.GV.SC.04"]`
  - `"NIST.GV.SC.10": ["NIST.GV.SC.05"]`
  - `"NIST.ID.RA.10": ["NIST.GV.SC.04"]`
- **Change:** `"NIST.RS.MA.01"` becomes `["NIST.DE.AE.08", "NIST.ID.IM.04"]`.
- **Comments only:**
  - `DE.AE.04`'s comment becomes "Impact estimation needs event analysis".
  - `DE.AE.08`'s comment becomes "Incident declaration needs event analysis".
  - Each new line gets a one-phrase comment in the existing style.

In `_NIST_CSF_ROOT_CAUSE_CLUSTERS["process"]["typical_requirements"]`, append `"NIST.ID.IM.04"` and `"NIST.ID.RA.07"`.

Red flags and scope questions are unchanged. They are pinned in `tests/test_p5_3_framework_desk_review.py` and `tests/test_p5_5_scoping_evidence.py`.

### D-NIST-I: Persisted data: no migration, no alias, and history stays as it is

- **Issued report snapshots** are write-once (P3-2 and P5-6) and are not touched.
- **Existing rows that reference `NIST.RS.CO.04` stay as they are:** `GapItem`, `Conclusion`/`ConclusionRevision`, `DeskReviewFinding`, `Finding` and `AnalysisRun` envelopes. They record what was assessed at the time. Readers already tolerate an id that is no longer in the registry (fact 9):
  - Conclusion review shows it without a title and sorts it last.
  - Scoring ignores it because it iterates current controls.
  - The questionnaire engine skips it.

  Scenario 10 pins this tolerance.
- **Existing scoped NIST assessments.** `Assessment.applicable_requirements` holds the old 94-id list (fact 10). If such an assessment is re-analysed, the 13 new ids fall outside its scope list and would be treated as out of scope. **Operator step, in the PR description:** re-save the Scope tab of any existing NIST assessment before re-running analysis. That recomputes the list from the registry.
  - No code change is made for this. A read-time "treat missing NIST ids as applicable" rule would change the shared scope-enforcement path for every framework. An Alembic data migration is not worth it for a single-user MVP whose NIST assessments are demo and validation data.
  - Saqlain confirms this in Results (see the question below).
- **No change** to `app/frameworks/compat.py`, `app/models/**`, `alembic/**`, `app/routers/**` or `app/services/**`.

### D-NIST-J: P6-2c criteria rule. Codex authors no criteria

The draft keeps its meaning. The only changes are removing the RS.CO.04 criteria and naming the new ids as pending. The orchestrator (Claude) drafts their criteria afterwards as a separate follow-up.

1. **`app/frameworks/criteria/nist_csf_draft.py`:**
   - Delete the whole `"NIST.RS.CO.04": _criteria(...)` entry.
   - Delete the `_RSCO04` constant. It is orphaned by the deletion (fact 6).
   - Add the following module-level constant directly after the `NIST_CSF_CRITERIA_REVIEW_META` declaration:
     ```python
     # Pack ids added by the CSF 2.0 alignment (P6-NIST) whose criteria are not drafted yet.
     # The orchestrator drafts them in the P6-2c follow-up and empties this set; nothing else
     # may be added to it (tests/test_p6_2c_iso_nist_criteria.py pins it exactly).
     CRITERIA_PENDING_IDS: frozenset[str] = frozenset({
         "NIST.GV.RM.05", "NIST.GV.RM.06", "NIST.GV.RM.07",
         "NIST.GV.SC.06", "NIST.GV.SC.07", "NIST.GV.SC.08", "NIST.GV.SC.09", "NIST.GV.SC.10",
         "NIST.ID.RA.07", "NIST.ID.RA.08", "NIST.ID.RA.09", "NIST.ID.RA.10",
         "NIST.ID.IM.04",
     })
     ```
   - Change nothing else in the file. Every other criterion's `statement`, `evidence_hint`, `source_basis`, `kind`, confidence and `in_force_note` stays byte-identical, and scenario 9 checks this against `main`.
   - Some rows now carry stale `[repo says ...]` notes because the pack was corrected: GV.OC.05.TC4, GV.OV.03.TC4, PR.PS.01.TC4, GV.RR.01.TC3, and the DE.AE.06/08 TC1 notes. **Leave them.** Re-drafting them is the orchestrator's follow-up, and they remain `low`/`medium`, so `test_repo_departures_are_low` still holds.
2. **`scripts/export_criteria_review.py::build_rows`:**
   - Read `pending = getattr(module, "CRITERIA_PENDING_IDS", frozenset())`.
   - **Skip** any requirement whose id is in `pending`.
   - Any other id missing from the draft must still raise `KeyError`, as today.
   - DPDPA and ISO output stays byte-identical, because their modules define no such constant.
3. **Regenerate** the committed sheet with `.venv/bin/python scripts/export_criteria_review.py --framework nist_csf`. The expected diff is:
   - the RS.CO.04 rows disappear
   - `requirement_title` changes on the D-NIST-D rows
   - no other change

   Do not touch the ISO or DPDPA sheets.
4. **`tests/test_p6_2c_iso_nist_criteria.py::test_nist_covers_every_pack_requirement_in_order`** becomes:
   ```python
   from app.frameworks.criteria.nist_csf_draft import CRITERIA_PENDING_IDS
   assert len(NIST_IDS) == 106
   assert CRITERIA_PENDING_IDS == frozenset({...the 13 ids above...})   # exact, so it cannot grow
   assert CRITERIA_PENDING_IDS <= set(NIST_IDS)
   assert list(NIST_CSF_CRITERIA_DRAFT) == [i for i in NIST_IDS if i not in CRITERIA_PENDING_IDS]
   ```
   No other assertion in that file changes.

The orchestrator's follow-up is not Codex's work. It will:
- draft 2-5 criteria for each pending id
- revise the stale rows listed above
- empty `CRITERIA_PENDING_IDS`
- restore the strict equality in the coverage test
- regenerate the sheet

Saqlain's NIST sign-off waits for that follow-up.

### D-NIST-K: Batching: no code change; the expected table becomes 7 batches

`app/frameworks/batching.py` and the settings are unchanged. With 106 controls, threshold 90 and M = 25, the algorithm produces this table:

| Batch | Domain | Sections | Controls | Range |
|---|---|---|---|---|
| 1/7 | govern | gv_oc, gv_rm, gv_rr, gv_po, gv_ov | 21 | NIST.GV.OC.01 .. NIST.GV.OV.03 |
| 2/7 | govern | gv_sc | 10 | NIST.GV.SC.01 .. NIST.GV.SC.10 |
| 3/7 | identify | id_am, id_ra, id_im | 21 | NIST.ID.AM.01 .. NIST.ID.IM.04 |
| 4/7 | protect | pr_aa, pr_at, pr_ds, pr_ps, pr_ir | 22 | NIST.PR.AA.01 .. NIST.PR.IR.04 |
| 5/7 | detect | de_cm, de_ae | 11 | NIST.DE.CM.01 .. NIST.DE.AE.08 |
| 6/7 | respond | rs_ma, rs_an, rs_co, rs_mi | 13 | NIST.RS.MA.01 .. NIST.RS.MI.02 |
| 7/7 | recover | rc_rp, rc_co | 8 | NIST.RC.RP.01 .. NIST.RC.CO.04 |

Govern splits because 21 + 10 > 25. The ISO table (6 batches) is unchanged. NIST judge and desk-review calls go from 6 to 7 per run. Expect roughly 1/6 more NIST desk-review input tokens, because documents are re-sent per batch (D-P6-1b-H). State this in the PR.

### D-NIST-L: Existing tests: the only authorised edits

For each file, make exactly the edits listed and nothing else:

| File | Authorised edit |
|---|---|
| `tests/test_correctness_bundle.py::test_requirement_counts_are_registry_driven` | `"nist_csf": 94` → `106` |
| `tests/test_p5_5_scoping_evidence.py` | `NIST_DOCUMENT_TYPES` gains `"change_management"` after `"configuration_baselines"`; `len(... NIST ...evidence_requests) == 24` → `25`; the `breach_procedure` `EvidenceRequest` pin → the D-NIST-G reason and tuple |
| `tests/test_p6_1b_framework_batching.py` | (a) the `nist_csf` rows of the batch-table expectation → the D-NIST-K table; (b) the label assertion becomes per framework (`len(expected[framework_id])`) instead of the literal `/6` for both; (c) `count("nist_csf") == 6` → `7`; (d) the three `("nist_csf", ...)` fingerprint values → the new values from Verification 2; (e) `test_protected_surface_guard_uses_three_dot_diff` adds the pathspec `":(exclude)app/frameworks/definitions/nist_csf.py"` after `"app/frameworks/definitions"`, with the comment `# P6-NIST: CSF 2.0 alignment edits the NIST pack.` |
| `tests/test_p5_3_framework_desk_review.py::test_scenario_12_standing_guards_and_public_signatures` | Add `":!app/frameworks/definitions/nist_csf.py"` to the `protected` pathspec, next to the dpdpa exclusion, with the same comment |
| `tests/test_p6_2c_iso_nist_criteria.py` | D-NIST-J step 4 only |
| `tasks/criteria-review/nist-csf-criteria-v1.csv` | Regenerated only (D-NIST-J step 3) |

Rules for any other failure:
- If another existing test fails **only** because it pins a NIST count, a NIST id, a NIST title or delta string, or a NIST cluster membership that this design changes, stop and report it with the exact assertion. Do not edit it.
- Any other failure: stop and report.
- `test_p5_4_adaptive_ucc_questionnaire.py::test_scenario_13_structural_guards` stays failing (pre-existing). Do not touch it.

## Key files

| Path | Change |
|---|---|
| `app/frameworks/definitions/nist_csf.py` | D-NIST-B, C, D, G, H; docstring |
| `app/frameworks/mappings/clusters.py` | NIST members only (D-NIST-F) |
| `app/frameworks/criteria/nist_csf_draft.py` | RS.CO.04 entry and `_RSCO04` removed; `CRITERIA_PENDING_IDS` added (D-NIST-J) |
| `scripts/export_criteria_review.py` | Skip pending ids (D-NIST-J) |
| `tasks/criteria-review/nist-csf-criteria-v1.csv` | Regenerated |
| `tests/test_p6_nist_csf2_alignment.py` (new) | Scenarios below |
| Tests in D-NIST-L | Only the listed edits |

**Do not touch:**
- `app/dpdpa/**`, `app/frameworks/schema.py`, `app/frameworks/batching.py`, `app/frameworks/prompts.py`, `app/frameworks/compat.py`, `app/frameworks/registry.py`
- every other file in `app/frameworks/definitions/`, and `app/frameworks/criteria/{dpdpa,iso27001}_draft.py`
- `app/services/**`, `app/routers/**`, `app/models/**`, `app/templates/**`, `alembic/**`, `app/config.py`
- `tests/fixtures/**`, `tests/support/**`
- `validation/**`, `scripts/validation/**`
- the DPDPA and ISO criteria sheets
- any non-NIST cluster member or cluster-level field

## Non-goals

- Rewriting the other near-verbatim NIST descriptions in own words (see the question in Results).
- Drafting or editing any test criterion beyond the RS.CO.04 removal.
- A data migration, id aliasing or a scope read-time fallback (D-NIST-I).
- Re-exporting the P5-9 NIST question packs. That is Saqlain's step after merge.
- Changing section or domain weights, red flags, scope questions or the batching algorithm.
- Updating the plan doc's "NIST CSF (94)" count, `tasks/todo.md` or memory. The orchestrator does these.

## Test scenarios (all required; you may add cases, not drop or weaken them)

New file `tests/test_p6_nist_csf2_alignment.py`. Expected content is written into the test as literals copied from this handoff.

1. **Pack shape.**
   - `control_count() == 106`.
   - Per-section ordered id lists equal D-NIST-C's table, spelled out in full as literals.
   - Per-domain counts are 31/21/22/11/13/8.
   - `get_control("NIST.RS.CO.04") is None`.
   - Ids are unique.
   - Every `reference` equals the id-derived `"{FN}.{CAT}-{NN}"`.
   - The module docstring contains "106" and does not contain "82 subcategory".
2. **Content.**
   - For all 13 new ids: `(title, description, criticality, tags, reference)` equal D-NIST-C.
   - For every D-NIST-D row: the changed fields equal the new values, and every unchanged field (id, reference, criticality, and the fields not listed) equals `main`. To get the `main` values, load `git show main:app/frameworks/definitions/nist_csf.py` into a namespace with `exec`.
   - Every NIST control **not** named in D-NIST-C or D-NIST-D is `==` its `main` counterpart (full `Control` equality).
   - Section and domain weights equal `main`.
3. **Questions.**
   - Every NIST control has a `QuestionDef`.
   - `questions["NIST.DE.AE.08"].question == "Has your organization implemented incident declaration? (DE.AE-08)"`.
   - `questions["NIST.GV.SC.10"].question == "Has your organization implemented supplier exit provisions? (GV.SC-10)"`.
   - No question or guidance mentions `RS.CO-04`.
4. **Clusters.**
   - `tests/test_content_integrity.py` passes.
   - Each new id and each moved id is in exactly the D-NIST-F cluster with exactly the D-NIST-F delta.
   - Every D-NIST-F step-4 delta matches.
   - `NIST.RS.CO.04` appears in no cluster.
   - The NIST member set equals all 106 ids.
   - `CLUSTER_001` still has 6 NIST members.
   - Every non-NIST member of every cluster, and every cluster's non-`controls` fields, equal `main`. Load `main:app/frameworks/mappings/clusters.py` via `git show` and `exec`.
5. **Evidence requests.**
   - The document-type order has 25 entries, as in D-NIST-G.
   - Each changed request's `maps_to`, `reason` and `label` equal D-NIST-G.
   - Unchanged requests equal `main`.
   - The union of `maps_to` equals all 106 ids, so every control is mapped.
   - `compute_scope_multi({}, ["iso27001", "nist_csf"])` yields **one** `change_management` item with `frameworks == ["iso27001", "nist_csf"]` and `maps_to` = ISO's then NIST's.
6. **Batches.**
   - `control_batches("nist_csf")` equals the D-NIST-K table (domains, section keys, counts, first and last ids, labels `1/7` … `7/7`).
   - `control_batches("iso27001")` is unchanged.
   - `control_batches("dpdpa") == ()`.
7. **Prompts.**
   - The six DPDPA and ISO fingerprints equal the Step 0 values.
   - `build_framework_system_prompt("nist_csf")` contains `(106 total)`, contains `**NIST.ID.IM.04**`, and does not contain `NIST.RS.CO.04`.
   - `build_framework_desk_review_system_prompt("nist_csf")` contains `Include ALL 106 control IDs`.
8. **Dependencies.**
   - Every key and value in `NIST_CSF_DEFINITION.dependencies` is a real NIST control.
   - The D-NIST-H additions and the `RS.MA.01` change are present.
   - `"NIST.ID.IM.04"` and `"NIST.ID.RA.07"` are in `root_cause_clusters["process"]["typical_requirements"]`.
9. **Criteria rule (D-NIST-J).**
   - `CRITERIA_PENDING_IDS` equals the 13 ids.
   - `set(main_draft) - set(draft) == {"NIST.RS.CO.04"}` and `set(draft) - set(main_draft) == set()`. Load the main draft via `git show` and `exec`.
   - For every remaining criterion, `(statement, evidence_hint, source_basis, kind)` and its `REVIEW_META` entry equal `main`.
   - `export_criteria_review.build_rows(framework="nist_csf")` emits no row for a pending id and none for RS.CO.04.
   - With `CRITERIA_PENDING_IDS` monkeypatched to `frozenset()`, `build_rows` raises `KeyError`.
   - The DPDPA and ISO exports are byte-identical to their committed sheets (the existing test).
10. **Legacy data tolerance (D-NIST-I).** Seed a `nist_csf` assessment with the existing seed helpers, for example the `_seed` / `_make_report` pattern in `tests/test_correctness_bundle.py` or the conclusion helpers in the P2-4/P5-2 tests. Give it a `GapItem`, and a `Conclusion` with its revision, for `NIST.RS.CO.04`, plus one for `NIST.GV.PO.01`. Then:
    - The conclusion-review page and the workpaper page for that assessment return 200.
    - The review data includes the `NIST.RS.CO.04` row, with no crash and a missing title allowed.
    - `scoring.score(assessment.id, ["nist_csf"], _session=db)` succeeds, and its `control_count` is 106.

    Pin only "no exception and the row is present", not layout.
11. **Guards.**
    - `git diff --stat main...HEAD -- app/dpdpa tests/fixtures tests/support app/frameworks/schema.py app/frameworks/prompts.py app/frameworks/batching.py app/frameworks/compat.py app/frameworks/registry.py app/services app/routers app/models alembic app/config.py app/frameworks/definitions ':(exclude)app/frameworks/definitions/nist_csf.py' app/frameworks/criteria/dpdpa_draft.py app/frameworks/criteria/iso27001_draft.py tasks/criteria-review/dpdpa-criteria-v1.csv tasks/criteria-review/iso27001-criteria-v1.csv tasks/criteria-review/iso27001-descriptions-v1.csv` is empty. It uses the **three-dot** form.
    - `tests/test_golden_dpdpa.py` and `tests/test_answer_key_isolation.py` pass unmodified.

## Verification (before reporting done)

1. Run `.venv/bin/pytest -q` **after the orchestrator commits** (the guards compare `main...HEAD`). Expect the Step 0 baseline plus the new tests, with no new failures. List every D-NIST-L edit you made.
2. Re-run the Step 0.3 fingerprint snippet.
   - The DPDPA and ISO lines must be identical to Step 0.
   - Paste the three new NIST values. These are the values written into `tests/test_p6_1b_framework_batching.py` (D-NIST-L d).
3. Run the focused set and record the counts:
   ```
   .venv/bin/pytest -q tests/test_p6_nist_csf2_alignment.py tests/test_p6_1b_framework_batching.py tests/test_p6_2c_iso_nist_criteria.py tests/test_content_integrity.py tests/test_p5_5_scoping_evidence.py tests/test_p5_3_framework_desk_review.py tests/test_correctness_bundle.py tests/test_picker_and_scoring_contract.py tests/test_golden_dpdpa.py tests/test_answer_key_isolation.py
   ```
4. Paste `git diff --stat main...HEAD` and the diff of `tasks/criteria-review/nist-csf-criteria-v1.csv`, summarised as rows removed and titles changed.
5. **No live LLM smoke is required.** Prompts change only through pack content, and the batching code is unchanged. The orchestrator may optionally run one NIST desk review plus analysis on a synthetic assessment and confirm 7 batch-tagged judge records, all `finish_reason == "stop"`.
6. When the orchestrator launches Codex in the background with `codex exec`, it must redirect stdin: `codex exec ... < /dev/null`.

## Results

_To be filled in by the implementer:_
- Step 0 baseline counts and `main` commit
- fingerprints before and after
- fact-check outcomes
- files changed
- test counts
- every D-NIST-L edit
- the CSV diff summary
- any deviation stopped on
- PR link (added by the orchestrator)

**Open question for Saqlain (orchestrator carries it to the PR):**
1. Are there any **non-demo** NIST assessments in your database that will be re-analysed? If so, re-save their Scope tab first (D-NIST-I).
2. Have you started annotating `tasks/criteria-review/nist-csf-criteria-v1.csv`? This task regenerates it: RS.CO.04 rows go and some titles change. The recommendation is to hold NIST sign-off until the P6-2c follow-up (D-NIST-J).
3. Should the remaining NIST descriptions also be rewritten in own words, as D-P6-J does for ISO? CSF is public domain, so this is house style only.

## Done criteria

- Every scenario passes.
- The full suite has no new failures against the baseline.
- The DPDPA and ISO fingerprints are unchanged.
- Results is filled in.
- The orchestrator commits and opens a PR against `main` from `codex/p6-nist-csf2-alignment`. The PR description includes:
  - the D-NIST-E scoring effects
  - the D-NIST-K cost note
  - the D-NIST-I operator step
  - the note that the P5-9 NIST question packs need re-export (Saqlain)
- **Claude reviews before merge.** After merge, the orchestrator starts the P6-2c follow-up (D-NIST-J).

## Saqlain's answers (2026-09-25, before dispatch)
1. **Existing NIST data:** demo only. No migration and no scope-refresh step.
2. **`nist-csf-criteria-v1.csv`:** no review decisions entered yet. Regenerating the sheet is safe.
3. **Own-words rewrite:** limited to the new and corrected controls named in this handoff. Leave all other NIST descriptions unchanged.
