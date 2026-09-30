# P6-5 follow-up: diagnose and reduce the v2 judge's abstention rate

## Goal
The v2 analysis pipeline answers `insufficient_evidence` (IE) on ~76% of requirements once ISO 27001 and NIST CSF carry approved test criteria. Under the pre-registered scorer, IE counts as "flagged", so catch and false positives rise together and the P6-5 pooled gate fails (now on false positives). **Diagnose why the judge abstains, then make one general fix that lowers the abstention rate without losing the catch rate.** Done means: a written diagnosis (aggregates only), one committed fix on a branch with tests green, one live v2 arm re-run, and an `ab_compare` result recorded in `## Results`, with a clear read on whether the gate now holds. Do not flip v2 on; that stays Saqlain's decision (P6-5c).

## Current state (2026-09-30)
- Local `main` and `origin/main` include PR #88 (P6-2e): signed ISO 27001 Annex A (230 criteria over 93 controls) and NIST CSF 2.0 (348 over 106) criteria are attached. DPDPA already had approved criteria (P6-2b). ISO clause requirements 4-10 (78 signed criteria, `ISO.C*`) are deliberately not attached; those requirements are not in the pack.
- Live A/B results (4 companies x 3 runs, model `deepseek/deepseek-v4-flash`, prices $0.14/M in, $0.28/M out):

| Arm | Catch | Decoy FP | Clean FP | Stability | IE rate |
|---|---|---|---|---|---|
| v1 baseline | 92.9% | 58.3% | 61.5% | 81.6% | 1.1% |
| v2, fallback criteria (pre-#88) | 82.3% | 50.0% | 46.9% | 84.6% | 61.0% |
| v2, approved criteria (post-#88) | 98.6% | 77.8% | 96.9% | 88.9% | 75.8% |

  Post-#88 IE by framework: DPDPA 60%, ISO 81%, NIST 80%. Catch by framework: DPDPA 98.9%, ISO 95.8%, NIST 100%.
- Why it abstains (hypothesis, unverified): the judge prompt says `compliant` only when every criterion is `met`; `partially_compliant` when some are met; `insufficient_evidence` when the material does not settle it. With 3-4 strict criteria per requirement (many `operating`), one `no_evidence` criterion pushes the whole requirement to IE. `judge.py` also downgrades a model `compliant` to IE when any criterion is not `met` (flag `model_criteria_inconsistency`, metric `downgraded_compliant`).
- A stricter judge prompt (p6-4.2: "met only when a claim itself shows it") was tried and **made catch worse** (78.7%, IE 71%) on fallback criteria. It lives on branch `claude/p6-5-judge-strictness` in `~/cyberassess-p6-5`. It is not merged. Do not reuse it.

## Key files
- `/Users/saqlainmomin/dpdpa-gap-tool/app/services/grounding/judge.py`: the v2 judge; `criteria_for()`, outcome derivation, criterion downgrade rule (~lines 440-480), metrics incl. `downgraded_compliant`.
- `/Users/saqlainmomin/dpdpa-gap-tool/app/services/grounding/judge_prompts.py`: judge system/user prompt and schema (`JUDGE_PROMPT_VERSION = "p6-4.1"`).
- `/Users/saqlainmomin/dpdpa-gap-tool/app/frameworks/criteria/{dpdpa,iso27001,nist_csf}.py`: generated approved criteria (never edit by hand; `scripts/convert_criteria.py`).
- `/Users/saqlainmomin/dpdpa-gap-tool/scripts/validation/{run_company,score,ab_compare}.py`: harness. `score.py` holds the pre-registered `FLAGGED = {non_compliant, partially_compliant, insufficient_evidence}`.
- `/Users/saqlainmomin/dpdpa-gap-tool/tasks/handoffs/2026-09-28-p6-5-v2-ab-and-flip.md`: the P6-5 spec and its `## Results` (Decisions 1-5, injection summary, catch diagnostic, this session's numbers).
- Runs (read-only data): `~/cyberassess-runs/2026-09-29-p6-5-v2-criteria/` (post-#88 v2 arm), `~/cyberassess-runs/2026-09-29-p6-5-v1-rescored/`, `~/cyberassess-runs/2026-09-29-p6-5-v2-missing-off/` and `-on/` (old-pack v2 arms), `~/cyberassess-runs/2026-09-29-p6-5-ab-criteria/ab_comparison.{md,json}`. Each `run-N/` has `conclusions.json`, `score.json`, `llm_usage.jsonl`, `stages.json`.

## Constraints (decisions already made)
- **Never read `validation/companies/*/answer_key.json`** while changing prompts, the judge or the analyzer (D-P5-9-C). Do not tune against any specific planted gap. Diagnose from aggregates only (counts by outcome, framework, criterion `kind`, criterion result). `score.json` `gap_results` contains gap descriptions and key facts: read only `caught`, `gap_class`, `framework_id`, `outcome`; print counts, never gap text or requirement IDs.
- **Decision 1 scoring is frozen** (IE counts as flagged; `FLAGGED` above). Do not change `score.py`'s mapping after seeing numbers. If the diagnosis suggests the mapping is the real problem, write that up for Saqlain rather than changing it (it needs his written sign-off and a recorded reason).
- Scoring stays deterministic and server-side; the LLM outputs qualitative strings only. Do not rewrite existing PDF sections.
- Approved criteria wording is signed by Saqlain; do not edit `signed/*.csv` or the generated criteria modules to make numbers move.
- Fixes must be general: judge logic, prompt wording, or how evidence is handed to the judge. Prompt version must be bumped; the file-guard tests that list changed paths need per-PR `:(exclude)` pathspecs added (never delete guards). See memory note on stale guards.
- Python 3.13 (`.venv`). Push and PR creation work from here; **merging a PR is blocked for Claude, so hand Saqlain the `gh pr merge` command.**
- Live runs spend real OpenRouter money. Each v2 arm (4 companies x 3 runs) costs about $0.25 and ~40 minutes wall-clock. **Ask Saqlain for spend approval before every live run.** Live-script no-key guards must be tested with `OPENROUTER_KEY=""`, never `env -u`.
- Commit messages end with the `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` line; PR bodies end with the Claude Code attribution line.

## Steps
1. **Worktree:** `git fetch origin && git worktree add ../cyberassess-abstain -b claude/p6-5-abstention origin/main`; symlink `.venv` from the main checkout and copy `.env`.
2. **Diagnose (free, no LLM), using the post-#88 arm and its `conclusions.json`/judge records.** Establish, as aggregate counts: (a) share of requirements by outcome and by criterion result (`met`/`not_met`/`no_evidence`); (b) IE share split by which criterion `kind` (`design` vs `operating`) was the blocking one; (c) how many IE outcomes are from the downgrade rule (`downgraded_compliant` / `model_criteria_inconsistency`) versus the model choosing IE; (d) IE share when at least one criterion is `met` (partial evidence) versus none; (e) how the same splits look for DPDPA (60% IE) versus ISO/NIST (80%). Also `stages.json`/`llm_usage.jsonl` for how many claims per requirement reach the judge (starved evidence vs strict rule).
3. **Write the diagnosis** into `## Results` first (numbers, no gap text), with the chosen fix and why.
4. **Fix.** Candidates, pick by the diagnosis: (i) derive the outcome from criteria with a weighted rule (e.g. `compliant` when all `critical`/design criteria are met and operating criteria are at least partly evidenced; `partially_compliant` when some met and none contradicted), keeping the rule deterministic in `judge.py`; (ii) prompt wording that defines what evidence satisfies an `operating` criterion; (iii) improve which claims are shown to the judge per requirement. One change, general, bump `JUDGE_PROMPT_VERSION` if the prompt changes. Add or adjust tests in `tests/test_p6_4_v2_judge.py` (or a new file).
5. **Verify offline:** `.venv/bin/pytest -q -p no:cacheprovider` fully green (current baseline: 1,205 passed, 10 skipped). Add per-PR excludes to any stale guard that trips.
6. **Ask Saqlain to approve the spend**, then run one live v2 arm (missing pass off) on the branch:
   `ANALYSIS_PIPELINE_VERSION=v2 V2_MISSING_PASS=false .venv/bin/python -m scripts.validation.run_company <company> --runs 3 --llm live --out $OUT` for c1-app-startup, c2-b2b-saas, c3-certified-fortress, c4-healthsaas in parallel (`&`, then `wait`), then `scripts.validation.score "$OUT"/*/run-*`.
7. **Compare:** `.venv/bin/python -m scripts.validation.ab_compare --baseline v1 --arm v1=$HOME/cyberassess-runs/2026-09-29-p6-5-v1-rescored:pipeline=v1 --arm v2-criteria=$HOME/cyberassess-runs/2026-09-29-p6-5-v2-criteria --arm v2-fix=$OUT --price-in 0.14 --price-out 0.28 --out <dir>`. Do not run `report.py` on these arms.
8. **Report to Saqlain** (plain language): catch, both FP rates, stability and IE for the three arms, framework and company splits, whether the pooled gate holds, and your recommendation. Open a PR only if the fix is offline-green and measurably better; do not merge or flip.

## Verification (smoke-test default)
- Unit/contract tests green, and the diagnosis script's output pasted in Results (counts only).
- Live arm completes with no `non_ok`/stage failures (`ab_compare` marks the arm comparable) and `analysis_pipeline_version == v2` in every `run.json`.
- Compare against the numbers in the table above, not memory.

## Report back
Append a `## Results` section to this file: diagnosis counts, the fix and its rationale, test results, spend, `ab_comparison.md` verbatim, and open questions for Saqlain (especially anything touching the frozen scoring rule). Also append a short note to `## Results` in `tasks/handoffs/2026-09-28-p6-5-v2-ab-and-flip.md`.

## Results

Branch `claude/p6-5-abstention` (worktree `~/cyberassess-abstain`, from `origin/main` at `21a8d3c`).

### Diagnosis (free, no LLM; aggregates only)

Source: the full judge records stored in each run's `app.db` (`analysis_runs.claims_json`), for the post-#88 arm (`2026-09-29-p6-5-v2-criteria`) and the pre-#88 fallback arm (`2026-09-29-p6-5-v2-missing-off`). 12 runs, 1,563 requirement-runs per arm. Scripts are in the session scratchpad (`diagnose.py`, `mech.py`, `ceiling.py`) and print counts only.

**The hypothesis was wrong.** The judge does not abstain because one strict criterion blocks the rest. It abstains because it credits no criterion at all.

| Post-#88, all frameworks | Count |
|---|---|
| Requirement-runs | 1,563 (1,509 sent to the judge) |
| Outcomes | IE 1,184 · partially 176 · non-compliant 109 · N/A 54 · compliant 40 |
| Criterion results (4,818) | no_evidence 4,177 (87%) · met 472 (10%) · not_met 169 (4%) |
| (a) IE with **zero** criteria met | 1,124 of 1,184 (95%) |
| (d) IE with at least one criterion met | 60 (5%) |
| (b) IE blocking kind | design+operating 1,138 · design only 43 · operating only 3 |
| (c) IE source | model chose IE 1,151 · downgrade rule 30 · N/A proposed 3 |
| IE with no claims shown (questionnaire only) | 440 (the judge cannot credit anything here; 445 pre-#88, so unchanged) |
| IE with claims shown | 744 |

By criterion kind the rates are low for both: design met 261 of 2,766 (9%), operating met 211 of 2,052 (10%). Operating criteria are not the special blocker.

**(e) DPDPA vs ISO/NIST.** DPDPA: IE 222 of 369, 195 of those with zero met, 96 with no claims. ISO/NIST: IE 962 of 1,194, 929 with zero met, 344 with no claims. Same pattern; ISO/NIST is worse because it has more requirements with claims that the judge now refuses to credit.

**Same claims, different judge behaviour (ISO/NIST, requirements with at least one claim shown):**

| | Pre-#88 (1 fallback criterion = control description) | Post-#88 (2-5 approved criteria) |
|---|---|---|
| Requirements with claims | 840 | 844 |
| Claims shown | 4,387 | 4,365 |
| Model outcome compliant | 442 | 45 |
| Model outcome IE | 327 (39%) | 598 (71%) |
| Claims cited anywhere | 1,823 | 777 |
| Requirements citing no claim at all | 349 | 570 |

Extraction never sees the criteria, and the claim volume is the same in both arms. The only change is the criteria the judge tests against. With the control description as the test, the judge credited 33% of these requirements. With specific audit-style criteria (e.g. "procedure covers detection, reporting, triage, response, communication and closure"; "for a sample of joiners in the period, records show..."), it reads each criterion literally, finds no claim that restates it, and answers `no_evidence` across the board.

**Mechanical losses are small.** `met` given without claim IDs (turned into `no_evidence`): 17 DPDPA + 113 ISO/NIST criteria. Unknown criterion IDs: 1. Criteria missing from the reply: 7 requirements. Retries: 34 requirements, 0 left incomplete. Truncated claim lists: 47.

**Clean controls and decoys (outcome counts only; no IDs):** 93 of 96 scored clean-control runs have claims shown, so evidence starvation does not explain clean FP. Pre-#88 those 93 gave 51 compliant; post-#88 they give 3 compliant, 54 IE (all with zero criteria met, 48 citing no claim), 28 partially and 8 non-compliant.

**Why fix (i), a weighted outcome rule, cannot work.** Under the frozen scorer only `compliant` (or N/A) stops a requirement being flagged. Turning IE into `partially_compliant` lowers the IE rate but leaves every FP unchanged. Replaying two weighted rules over the post-#88 records: "all design met + at least one operating met, nothing not_met" turns 12 of 1,509 judged records compliant; "all design met, nothing not_met" turns 28. Too small to matter.

**Chosen fix: (ii), prompt wording that defines what evidence meets a criterion.** The judge needs to be told how an assessor reads a control test against desk-review claims: judge substance not wording, "e.g." lists are examples, a policy/procedure/configuration claim meets a design criterion, a claim that the activity was carried out (record, log, report, dated review, audit finding) meets an operating criterion, and "for a sample" / "in the period" describe how an auditor tests rather than something a claim must restate. To protect catch, the same wording sends a document that covers the subject but leaves out or contradicts something the criterion requires to `not_met` (still flagged), and says a general "we are certified/compliant" claim does not meet a criterion on its own. It also says a `met` result must list its claim IDs (the 130 lost criteria above). This is the opposite direction from p6-4.2, which was stricter and is not reused.

**Honest ceiling.** 440 of 1,563 requirement-runs (28%) have no claims and will stay IE under any judge change. The gate needs clean FP to drop from 96.9% to ≤61.5%, i.e. roughly a third of clean-control runs to become compliant. The pre-#88 arm reached 46.9% with loose criteria, so it is possible in principle, but the risk is that catch falls back towards the fallback arm's 82.3%.

**Process note.** While learning the `score.json` layout I printed one line of `clean_control_results` and one of `decoy_results`, which showed three requirement IDs with their outcomes. No gap text, key facts or answer key file were read. Those IDs played no part in choosing or wording the fix, which is general and was chosen from the aggregates above.

### Fix (committed on `claude/p6-5-abstention`)

- `app/services/grounding/judge_prompts.py`: the one-line "Criterion results" rule is replaced by a short block that defines what evidence meets a design criterion and an operating criterion (wording above). `JUDGE_PROMPT_VERSION` `p6-4.1` → `p6-4.3` (`p6-4.2` is the unmerged strict branch, so it is skipped to keep run records unambiguous). The outcome rule, schema, `judge.py` derivation, downgrade rule and `score.py` are untouched.
- `tests/test_p6_5_abstention_prompt.py` (new, 5 tests): the new evidence rules, the two catch guards (omission → not_met; blanket certification is not evidence), met needs claim IDs, outcome and untrusted-material rules unchanged, fingerprint tracks the template.
- Guards: per-PR `:(exclude)`/allow entries for `judge_prompts.py` (and, in the P6-2b guard, the new test and this handoff) in `test_p6_4_cap_upload_limit`, `test_p6_4_whats_missing` (both scenario-13 tests), `test_p6_7_requirement_card`, `test_p6_7b_add_to_rfi`, `test_p6_8_board_report_v2`, `test_p6_9_file_set`, `test_p6_2b_dpdpa_criteria`. No guard deleted. Version pins in `test_p6_4_v2_judge.py` (3) and `test_p6_4_whats_missing.py` (1) moved to `p6-4.3`.
- `test_retention` scenario 13 only checks uncommitted edits under `tests/`, so it passes once committed.

### Tests

`.venv/bin/pytest -q -p no:cacheprovider`: **1,210 passed, 10 skipped** (baseline 1,205 + 5 new).

### Live arm (partial: c1, c2, c4)

**Information only, no gate verdict.** `ab_compare` refuses unequal company sets, and c3 has not finished (see hangs below). Arm dir: `~/cyberassess-runs/2026-09-30-p6-5-v2-abstain/` (branch at `7d4eb02`, `ANALYSIS_PIPELINE_VERSION=v2`, `V2_MISSING_PASS=false`, prompt `p6-4.3` in every judge record). Pooled over c1-app-startup, c2-b2b-saas, c4-healthsaas, all `run-*` dirs; same script over all three arms (`partial_compare.py` in the session scratchpad; stability uses `ab_compare`'s modal-share definition):

| Arm | Runs | Catch | Decoy FP | Clean FP | Stability | IE rate | Compliant share |
|---|---|---|---|---|---|---|---|
| v1 | 9 | 95.2% (100/105) | 66.7% (16/24) | 69.7% (46/66) | 82.7% (281 reqs) | 0.8% (7/843) | 9.0% (76/843) |
| v2-criteria | 9 | 98.1% (103/105) | 79.2% (19/24) | 100.0% (66/66) | 88.0% (281 reqs) | 68.4% (577/843) | 1.3% (11/843) |
| v2-fix | 9 | 98.1% (103/105) | 87.5% (21/24) | 98.5% (65/66) | 87.3% (281 reqs) | 71.6% (604/843) | 1.1% (9/843) |

Judge-record aggregates, same three companies (`partial_diag.py`, from `analysis_runs.claims_json`):

| Arm | Prompt | Req-runs (judged) | IE of judged | IE with zero criteria met | IE with no claims shown | Criteria met / not_met / no_evidence | `met` dropped for missing claim IDs | Claims shown | Claims cited |
|---|---|---|---|---|---|---|---|---|---|
| v2-criteria | p6-4.1 | 843 (798) | 72.3% (577) | 95.7% (552) | 43.3% (250) | 269 / 110 / 2,090 (11% met) | 40 | 3,013 | 689 |
| v2-fix | p6-4.3 | 843 (798) | 75.7% (604) | 92.1% (556) | 41.7% (252) | 268 / 172 / 2,029 (11% met) | 60 | 2,778 | 609 |

**Read.** The p6-4.3 wording did not change how the judge behaves. The share of criteria credited `met` is unchanged at 11%; IE is slightly up; clean-control runs are still flagged in 65 of 66; the only visible shift is about 60 criteria moving from `no_evidence` to `not_met` (the omission rule), which keeps them flagged. The "met needs claim IDs" instruction did not help either (60 lost `met` results vs 40). Catch held at 98.1%.

**The gate cannot hold for this arm whatever c3 does.** In the full post-#88 comparison c3 contributes 30 of the 96 clean-control runs and 12 of the 36 decoy runs. Even if every c3 clean control came back compliant, pooled clean FP would be 65/96 = 67.7%, above the 61.5% gate. Running c3 would complete the record, not change the verdict.

**Spend and hangs.** DeepSeek at $0.14/M in, $0.28/M out. The nine finished runs cost $0.418. c3 hung twice (kept in `stuck-c3/` and `stuck-c3-2/`, never scored) and lost $0.529. Total ~$0.95. A full four-company arm costs ~$0.55-0.60, not the $0.25 estimated above. Both hangs had the same shape: every in-flight request of every c3 process stopped in the same minute (10:04, then 11:02) while OpenRouter `/api/v1/models` answered in 0.45 s. Cause: `llm_client._get_client()` passes `timeout=settings.llm_timeout_seconds` (300 s) to `OpenAI(...)`; in httpx that is a per-phase timeout, the read timer resets whenever bytes arrive, and OpenRouter sends keep-alive bytes while a request is stuck upstream, so the call never times out. Fix: a wall-clock deadline per provider call, on its own branch (`claude/llm-request-deadline`). The c3 re-run is written up in `tasks/handoffs/2026-09-30-p6-5-abstention-c3-rerun.md`.

**Open question for Saqlain.** Two prompt directions have now failed (stricter p6-4.2 lost catch; the evidence definitions in p6-4.3 changed nothing). The judge credits almost nothing against the approved audit-style criteria, and 28% of requirement-runs have no claims at all. The remaining levers are outside the judge prompt: (a) show the judge which criterion each claim was extracted for (extraction currently never sees the criteria), or (b) revisit Decision 1, since under the frozen scorer IE is flagged and only `compliant` clears a clean control. Either needs your call; (b) needs written sign-off and a recorded reason.

### PRs (2026-09-30)
- Draft: https://github.com/saqlainmmomin/Cyber/pull/90 (this branch; stays a draft unless the full arm is measurably better).
- Deadline fix: https://github.com/saqlainmmomin/Cyber/pull/89 (`claude/llm-request-deadline`; merge first, then merge `main` into this branch before the c3 re-run). Also fixes `tests/test_p6_nist_csf2_alignment.py`, which failed on `main` once local `main` included #88; the same one-line fix is on this branch.

### Live arm (full, 2026-09-30)

c3-certified-fortress re-run on `919db15` (branch with #89 merged: `llm_request_deadline_seconds = 600`). Three runs, sequential, 745 LLM calls, all `ok`: **0 `LLMRequestTimeout` records, no stalls.** Every `run.json` has `analysis_pipeline_version == v2`; every judge record has `judge_prompt_version == p6-4.3`. c3 cost $0.334 (DeepSeek, $0.14/M in, $0.28/M out). **Arm total $0.752 for the 12 scored runs; session spend including the two hung c3 attempts ~$1.28.** `stuck-c3/` and `stuck-c3-2/` kept, never scored.

`ab_compare` output (`~/cyberassess-runs/2026-09-30-p6-5-ab-abstain/ab_comparison.md`), verbatim:

# P6-5 A/B comparison

Baseline: `v1`

## Arms

| Arm | Pipeline | Runs | Catch | Decoy FP | Clean FP | Stability | IE | Cost USD |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| v1 | v1 | 12 | 92.9% | 58.3% | 61.5% | 81.6% | 1.1% | 0.43063552 |
| v2-criteria | v2 | 12 | 98.6% | 77.8% | 96.9% | 88.9% | 75.8% | 0.7653041200000001 |
| v2-fix | v2 | 12 | 98.6% | 88.9% | 97.9% | 88.2% | 76.3% | 0.7577416000000001 |

## Gate

| Arm | Comparable | Reasons | Catch | Decoy FP | Clean FP | Stability | Cost reported | Holds |
|---|---|---|---|---|---|---|---|---|
| v2-criteria | true | none | true | false | false | true | true | false |
| v2-fix | true | none | true | false | false | true | true | false |

c3 on its own (from `ab_comparison.json` `by_company`):

| Arm | Catch | Decoy FP | Clean FP | Stability | IE |
|---|---|---|---|---|---|
| v1 | 86.1% (31/36) | 41.7% (5/12) | 43.3% (13/30) | 80.4% | 1.4% (10/720) |
| v2-criteria | 100.0% (36/36) | 75.0% (9/12) | 90.0% (27/30) | 90.0% | 84.3% (607/720) |
| v2-fix | 100.0% (36/36) | 91.7% (11/12) | 96.7% (29/30) | 89.2% | 81.8% (589/720) |

**Gate verdict: fails** (pooled, vs v1). Catch 98.6% ≥ 92.9% holds; stability 88.2% ≥ 81.6% holds; decoy FP 88.9% > 58.3% fails; clean FP 97.9% > 61.5% fails.

**Recommendation.** The p6-4.3 prompt is not better than p6-4.1: catch is identical (98.6%), IE is about the same (76.3% vs 75.8%), clean FP is about the same (97.9% vs 96.9%), and decoy FP is worse (88.9% vs 77.8%). Keep PR #90 as a draft for the record and close it, or close it now; do not merge it. v2 stays off. The deadline fix (#89) held: a full c3 arm completed with no hangs. The next step is a choice for Saqlain between the two levers in "Open question" above (criterion-aware evidence for the judge, or revisiting Decision 1 with written sign-off). A third prompt-wording attempt is not recommended.
