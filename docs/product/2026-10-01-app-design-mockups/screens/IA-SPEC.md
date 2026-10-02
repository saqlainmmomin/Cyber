# Information architecture spec (approved 2026-10-02)

Approved by Saqlain from `../flow-map.html`. Every screen follows this. Sample data: client **Meridian Ledger Technologies**, engagement **FY2026 privacy readiness** (review period 1 Apr 2025 to 31 Mar 2026, evidence cut-off 15 Mar 2026), assessments **Head office** (DPDPA 2023, ISO 27001:2022) and **Payments subsidiary** (ISO 27001:2022).

## Levels and tabs
- **Side menu** (same on every staff screen, Settings at the bottom): Home (`b1-home.html`), Clients (`b1-clients.html`), Engagements (`b2-engagement_list.html`), Review (`b5-review-queue.html`, count badge), Evidence (`b4-evidence.html?state=all`), Reports (`b6-report_snapshots.html`). `aria-current="page"` on the section the page belongs to: Engagements for anything inside an engagement or assessment, except the cross-engagement views.
- **Engagement tabs** (`<nav class="tabs" aria-label="Engagement">`): Overview `b2-engagement_detail.html`, Evidence `b4-evidence.html`, Findings and actions `b2-remediation_tracker.html`, Reports `b2-integrated_reports.html`.
- **Assessment tabs** (`<nav class="tabs" aria-label="Assessment">`): Overview `b3-hub.html`, Scope `b3-scope.html`, Questionnaire `b3-questionnaire.html`, Review `b5-review-queue.html`, Report `b5-report.html`.
- There is no Documents tab, no AWS evidence tab, no Remediation tab, no Integrated reports tab any more.
- Pages below a tab (detail pages, sub-views) keep the parent tab row with that tab selected, and add the page name as the last breadcrumb.

## Breadcrumbs (always complete)
`Meridian Ledger Technologies / FY2026 privacy readiness / Head office / <page>`; links: client -> `b1-client_detail.html`, engagement -> `b2-engagement_detail.html`, assessment -> `b3-hub.html`. Engagement-level pages stop after the engagement. Add `hide-sm` to the client crumb and its slash so it fits at 390. Last crumb is `<b>`.

## Stepper (assessment Overview only, `b3-hub.html`)
Five stages, no numbers: Scope, Evidence, Questionnaire, Review, Report. Evidence stage label links to `b4-evidence.html?assessment=head-office`. The engagement Overview has **no** stepper; its assessments table has a Stage column (e.g. "Review · 3 of 6 approved") and a Next step column.

## Sub-views inside a tab
Use one `.seg` group under the tab row (buttons that navigate), never a second `.tabs` row:
- Engagement Evidence: Inventory `b4-evidence.html` | Requests `b6-magic_links.html`.
- Assessment Review: Queue `b5-review-queue.html` | Conclusions `b5-conclusions.html` | Findings `b5-findings.html` | Workpaper `b4-workpaper.html`.
- Assessment Report: Report `b5-report.html` | Versions `b6-report_snapshots.html` | Applicability `b6-soa.html` (ISO 27001 only, conditional).

## Where each screen lives
| Screen | Level / tab | Notes |
|---|---|---|
| b4-evidence (new) | Engagement / Evidence / Inventory | Every item: name, source (Upload, AWS, Client link, Reused), assessment, supports (control codes, muted), status (Scanning, Available, Rejected, Out of date), updated. Filters: source, status, assessment. Primary: Upload evidence. Secondary menu or buttons: Pull from AWS (`b4-aws_evidence`), Reuse from another assessment (`b4-evidence_reuse`), Pre-fill questionnaire (`b4-desk_review`). `?state=all` = cross-engagement view from the side menu (adds Engagement column, no engagement tabs). |
| b6-magic_links | Engagement / Evidence / Requests | Already redesigned; only re-shell it. |
| b6-rfi | Engagement / Evidence / Requests / <assessment> request | RFI items and versions for one assessment; its client links show in Requests. |
| b4-desk_review, b4-aws_evidence, b4-evidence_reuse, b4-evidence_detail, b4-evidence_span | Engagement / Evidence (sub-pages) | Evidence tab selected. |
| b4-documents_tab, b4-document_list | superseded by b4-evidence | Moved to `../superseded/`. |
| b2-engagement_detail | Engagement / Overview | Assessments table with Stage and Next step; Add assessment primary; Archive ghost. Note: an engagement with one assessment opens straight on that assessment's Overview. |
| b2-remediation_tracker | Engagement / Findings and actions | Title "Findings and actions". Export actions stays (secondary). |
| b5-finding-card | Engagement / Findings and actions / <finding> | |
| b2-integrated_reports | Engagement / Reports | |
| b3-* | Assessment / Overview, Scope, Questionnaire | b3-hub is Overview. |
| b5-analysis, b5-review-queue, b5-conclusions, b5-conclusion-card, b5-requirement-card, b5-review-finding-card, b5-findings, b4-workpaper, b4-workpaper_entry | Assessment / Review | |
| b5-report, b5-no-report, b5-basis, b5-release, b6-report_snapshots, b6-soa, b6-comparison | Assessment / Report | Open current report stays on comparison. |

## Unchanged rules
Sentence case; no uppercase; at most one visible `.btn.primary` per state and none in states with no real action; no hex; no new `<style>` blocks; period and evidence cut-off in the header meta line on engagement and assessment pages; control codes in small muted text in lists; framework copy conditional.
