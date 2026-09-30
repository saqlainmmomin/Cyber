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
