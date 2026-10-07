# Veldhara walkthrough

This is a fictional company fixture for walking through the CyberAssess flow. It uses a scripted analysis and does not need an API key.

## Run it

If the environment is not set up yet:

```bash
python3.13 -m venv .venv && . .venv/bin/activate && pip install -r requirements-dev.txt
```

```bash
python scripts/demo/seed_demo.py --db data/demo.db
OPENROUTER_KEY="" DATABASE_URL=sqlite:///data/demo.db UPLOAD_DIR=data/uploads/demo uvicorn app.main:app --host 127.0.0.1
```

Re-running the seed replaces only Veldhara. Use `rm data/demo.db` for a full reset. No API key is needed. AI buttons for desk review, follow-up generation, the context wizard, and drafting error in this demo. That is expected, so do not click them.

The seed prints the real ids. Use them in the URLs below as `<current>`, `<prior>`, `<interim>`, `<nist>`, `<eng-a>`, and `<eng-b>`.

## Walkthrough URLs

1. `/`: dashboard with Veldhara, two engagements, and each assessment status.
2. `/engagements/<eng-a>`: prior and current released, interim in review.
3. `/assessments/<current>`: overview and the next step shown.
4. `/assessments/<current>?tab=scope`: scope answers and what each did.
5. `/assessments/<current>/evidence`: uploads, including the stale file and PNG. See the seed `Skipped` block for the XLSX result.
6. `/assessments/<current>?tab=questionnaire`: all answered. Follow-ups are stored but visible only if S0b also renders stored follow-ups; otherwise use the seed note.
7. `/assessments/<current>/conclusions`: 13 approved, 2 not applicable, 0 pending.
8. `/assessments/<interim>/conclusions`: review queue with 3 approved and 3 pending. The review URL redirects here.
9. `/assessments/<current>/findings`: three findings, including one overdue item.
10. `/assessments/<current>?tab=report` and `/assessments/<current>/report-summary`: released report.
11. `/assessments/<current>/snapshots`: report versions.
12. `/assessments/<current>/compare/<prior>`: year-over-year delta.
13. `/assessments/<prior>/snapshots`: prior release versions.
14. `/assessments/<nist>`: early NIST state and next step.
15. `/assessments/<nist>?tab=questionnaire`: partially answered questionnaire.
16. `/assessments/<current>/rfi`: current RFI screen.

After the walkthrough, write comments as a list in `tasks/2026-10-08-s1-walkthrough-comments.md`, one line per screen, using the Design pass checklist in the flow rework plan.
