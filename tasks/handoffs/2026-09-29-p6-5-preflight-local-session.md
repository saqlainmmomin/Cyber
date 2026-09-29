# P6-5 A/B: local-session handoff (mock preflight onward)

**Date:** 2026-09-29
**Why local:** the cloud session's egress policy blocks PyPI (403), so no venv could be built. Nothing was run. No spend, no code changes.

## State
- `main` @ `95a537b`. P6-5a (#85) and P6-5b (#87) are both merged, so the A/B harness is ready. #82 (design batch) is still an open draft. Don't merge it as is (141 contract tests fail by design).
- Spec: `tasks/handoffs/2026-09-28-p6-5-v2-ab-and-flip.md` (D-P6-5-B/C/D/J/K, and the run steps near line 385).

## Setup (local, Python 3.13)
```bash
git fetch origin && git worktree add ../cyberassess-p6-5 origin/main
cd ../cyberassess-p6-5
ln -s <main-checkout>/.venv .venv   # or: python3.13 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
cp <main-checkout>/.env .env
set -a && source .env && set +a
R=~/cyberassess-runs; D=$(date +%F)
BASE=$R/2026-09-28-stage-c-baseline-v1-rerun-2   # exactly this folder, not -rerun, not -rerun-2-interrupted
```

## Step 0: mock preflight (no spend)
```bash
ANALYSIS_PIPELINE_VERSION=v2 V2_MISSING_PASS=false .venv/bin/python -m scripts.validation.run_company c1-app-startup --runs 1 --llm mock --out /tmp/p6-5-preflight
.venv/bin/python -c "import glob,json; print({json.load(open(p))['settings']['analysis_pipeline_version'] for p in glob.glob('/tmp/p6-5-preflight/**/run.json', recursive=True)})"
```
- **Pass:** prints `{'v2'}`. v2 stages may fail under `--llm mock`; only the recorded setting matters.
- **Fail:** stop. The env var isn't reaching the app, and any live arm would be mislabelled.
- Also run `pytest tests/test_p6_5_ab_compare.py tests/test_p6_5_injection_pack.py -q` as a sanity check.

## Then, in order (spec has the exact commands)
1. **Pre-register Decision 1** (`insufficient_evidence` scoring) in the handoff's `## Results`, before any live run.
2. **Pilot:** one live v2 run of `c1-app-startup`. Read only the Cost section of `ab_comparison.md`, multiply by 12 per arm, and **get Saqlain's spend confirmation (D-P6-5-J)** before continuing.
3. **Arms**, 4 companies × 3 runs each, with the settings set on each command and not in `.env`:
   - `v2`: `ANALYSIS_PIPELINE_VERSION=v2 V2_MISSING_PASS=false`
   - `v2-missing`: `ANALYSIS_PIPELINE_VERSION=v2 V2_MISSING_PASS=true`
   - `v1` baseline: copy `$BASE` and re-score it with the new `score.py` (no LLM).
4. **`ab_compare`** across the three arms. The pooled gate blocks and ties pass. Framework, `criteria_source` and company splits are informational.
5. **Injection live run** (P6-5a pack), then record its `summary.json`.
6. **Present `ab_comparison.md` and the injection summary to Saqlain.** P6-5c (the flip PR) opens only after his written yes, recorded with the numbers.

## Rules to keep
- Never read `validation/companies/*/answer_key.json` while changing prompts or analyzer code (D-P5-9-C). Harness runs are aggregates only.
- Don't rewrite existing PDF sections, and keep scoring deterministic.
- Append results (preflight output, pilot cost, `ab_comparison.md` verbatim, decisions) to `## Results` in the P6-5 handoff.
- Cloud sessions can't reach PyPI, so live runs and `pytest` need the local machine.
