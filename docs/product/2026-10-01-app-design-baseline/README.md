# App design baseline screenshots (2026-10-01)

Captured from the local dev DB (`data/dpdpa.db`) at 1440 px wide, light mode, with headless Chromium against `uvicorn` on port 8001. They are the "before" for the app redesign (`tasks/handoffs/2026-10-01-app-design-kickoff.md`).

| File | Screen | Route |
|---|---|---|
| 01-dashboard | Portfolio dashboard | `/` |
| 02-client-detail | Client | `/clients/{id}` |
| 03-engagement-detail | Engagement | `/engagements/{id}` |
| 04-new-engagement | New engagement form | `/engagements/new` |
| 05-integrated-reports | Integrated reports | `/engagements/{id}/integrated-reports` |
| 06-remediation | Remediation tracker | `/engagements/{id}/remediation` |
| 07-assessment-hub-helix | Assessment hub, 2 frameworks, completed | `/assessments/{id}` |
| 08-hub-tab-dpdpa | Framework tab partial (HTMX) | `/assessments/{id}/tab/dpdpa` |
| 09-hub-scoped-prestige | Assessment hub, engagement-linked, scoped | `/assessments/{id}` |
| 10-conclusions | Conclusions approval | `/assessments/{id}/conclusions` |
| 11-findings | Findings and actions | `/assessments/{id}/findings` |
| 12-rfi | RFI | `/assessments/{id}/rfi` |
| 13-snapshots | Report versions | `/assessments/{id}/snapshots` |
| 14-workpaper | Workpaper | `/assessments/{id}/workpaper` |

## Gaps in this baseline

- **Dev DB is thin.** It has no findings, conclusions, evidence, report snapshots or magic links, so 10 to 14 show empty states. The populated review queue, requirement card, evidence detail and board-report-linked screens still need a seeded assessment (`scripts/seed_test_companies.py`) to capture.
- **Not captured:** review queue (`/assessments/{id}/review` redirects with 303 until the assessment is in review), SoA, comparison, the client-facing magic-link upload page (needs a generated link), login (redirects), and dark mode.

## Observations for the design pass

- Dashboard: the "Unmigrated assessments" list (17 legacy rows, amber cards) outweighs the one real client.
- Assessment hub: two stacked tab rows (framework tabs, then Scope/Documents/Questionnaire/Report) and a pipeline stepper that uses dots only.
- Conclusions: the breadcrumb renders twice, and the stat tiles are plain white cards with no severity or outcome colour.
- The nav bar has no firm logo (a hard-coded shield glyph) and no role or user indicator.
