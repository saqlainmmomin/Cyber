# Veldhara walkthrough

The primary deliverable is a fictional company evidence pack for a consultant to enter manually. The optional seed uses scripted analysis for inspecting screens. Neither validates live AI performance.

## Generate the manual upload pack

```bash
OPENROUTER_KEY="" .venv/bin/python scripts/demo/pack.py --output data/demo/veldhara-upload-pack
```

This command needs no database, network, or API key. It creates the evidence folder, upload manifest, consultant entry guide, coverage matrix, actual questionnaire entries, and `data/demo/veldhara-upload-pack.zip`. Generated artifacts are ignored by git. Read `consultant-entry-guide.md` first. Upload only files from `evidence/`; the guide and intended judgments stay outside analysis input.

The period is 1 July through 30 September 2026. Evidence cut-off is 5 October. The coverage matrix contains all 93 Annex A controls and 23 top-level clauses 4 through 10, with child obligations described in the evidence. The app currently registers only Annex A. Clauses are supplemental manual workpaper entries, so the native report cannot score the entire ISO standard. The guide makes this limit explicit.

The story is credible governance and tested DR with incomplete monthly access reviews, ad hoc supplier assurance, an unexercised incident plan, lapsed annual training, and missing backup restore tests. DR failover is separate from backup restoration. Internal integrations and occasional vendor development are in scope. July and August have initiation and chase emails, not completed review sheets. September contains 220 synthetic account rows across nine of eleven systems.

The final seed stores 22,515 current evidence words, exceeding the default 20,000-word budget. For a complete manual walkthrough, set `MAX_TOTAL_DOCUMENT_WORDS=30000` when starting the app and inspect exclusions. This uses the existing configuration setting.

Live desk review, follow-up generation, analysis, and image/scanned-PDF OCR need a configured API key. Use the actual generated questions and the guide's fact bank. The offline seed uses faithful image transcriptions and scripted conclusions. It demonstrates screen behavior only.

## Optional offline seed

If the environment is not set up yet:

```bash
python3.13 -m venv .venv && . .venv/bin/activate && pip install -r requirements-dev.txt
```

```bash
.venv/bin/python scripts/demo/seed_demo.py --db data/demo/veldhara-demo.db
OPENROUTER_KEY="" DATABASE_URL=sqlite:///data/demo/veldhara-demo.db UPLOAD_DIR=data/demo/uploads/demo .venv/bin/uvicorn app.main:app --host 127.0.0.1
```

For a clean database, choose a new filename containing `demo`. Re-running the seed replaces only Veldhara and preserves unrelated clients. It refuses `dpdpa.db`. No API key is needed. Leave live AI actions for the manual assessment with a configured key. Current approvals use 6 October 2026 and release uses 7 October. The prior assessment uses separate 2025 evidence. Its minimal baseline is not evidence of current performance. Interim remains an unreleased review queue and NIST an early questionnaire.

The seed prints the real ids. Use them in the URLs below as `<current>`, `<prior>`, `<interim>`, `<nist>`, `<eng-a>`, and `<eng-b>`.

## Walkthrough URLs

1. `/`: dashboard with Veldhara, two engagements, and each assessment status.
2. `/engagements/<eng-a>`: prior and current released, interim in review.
3. `/assessments/<current>`: overview and the next step shown.
4. `/assessments/<current>?tab=scope`: scope answers and what each did.
5. `/assessments/<current>/evidence`: full originals, including all 220 XLSX account records, screenshots, scanned approval and the unmapped historical file.
6. `/assessments/<current>?tab=questionnaire`: actual shared questions answered from authored per-control facts, with stored follow-up answers.
7. `/assessments/<current>/conclusions`: 99 approved (93 ISO plus six legacy DPDPA), one not applicable, no pending. Development is assessed.
8. `/assessments/<interim>/conclusions`: review queue with 3 approved and 3 pending. The review URL redirects here.
9. `/assessments/<current>/findings`: six findings covering consent, supplier assurance, training, monthly access reviews, incident exercises, and backup restore testing.
10. `/assessments/<current>?tab=report` and `/assessments/<current>/report-summary`: released report.
11. `/assessments/<current>/snapshots`: report versions.
12. `/assessments/<current>/compare/<prior>`: compare matched controls. The current assessment expands the minimal prior scope, so aggregate scores are not a like-for-like measure of improvement.
13. `/assessments/<prior>/snapshots`: prior release versions.
14. `/assessments/<nist>`: early NIST state and next step.
15. `/assessments/<nist>?tab=questionnaire`: partially answered questionnaire.
16. `/assessments/<current>/rfi`: current RFI screen.

After the walkthrough, write comments as a list in `tasks/2026-10-08-s1-walkthrough-comments.md`, one line per screen, using the Design pass checklist in the flow rework plan.

## Review click-through

Seed a new demo database, start the command above, and use the printed IDs.

1. `/assessments/<current>?tab=scope`: internal and vendor development included, all registered ISO controls in scope.
2. `/assessments/<current>/evidence`: full originals, September workbook, six monthly initiation/chase captures, stale December 2023 unmapped.
3. `/assessments/<current>?tab=questionnaire`: explicit responses and notes for shared controls; inspect stored follow-up answers.
4. `/assessments/<current>/conclusions`: check A.5.18 against nine-system coverage and open removals; A.8.13 against missing restores; A.8.25 and A.8.30 against development records.
5. `/assessments/<current>/findings`: review six findings, owners, dates and overdue actions.
6. `/assessments/<current>?tab=report`: reporting basis and released state. Also inspect comparison and prior versions from the complete URL list above.
