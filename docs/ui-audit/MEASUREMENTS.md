# Measurements and verification limits

Browser measurements are unavailable because Chromium was blocked. No width, unused space, line length or rendered font-size count below is inferred from CSS. Source constraints are discussed separately in ARCHITECTURE.md. This distinction is required by A5.

## Per-screen desktop measurements

N/A means not measured. The text-node count column must become a size-to-count map for both widths, restricted to visible text in main content. The longest body block is selected from paragraphs/quotes/list items, its total character count retained, and its actual maximum rendered characters per line measured using Range rectangles. Unused width is viewport minus sidebar minus the main border box, including outer gutters; internal pane waste must be considered separately.

| Screen/state | Content px 1440 / 1280 | Unused px 1440 / 1280 | Longest body block characters and line length 1440 / 1280 | Visible text nodes by font size 1440 / 1280 | Below-14px audit content |
|---|---|---|---|---|---|
| home | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| clients | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| client | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| engagements | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| portfolio-review | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| reports | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| new-engagement | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| engagement | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| new-assessment | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| remediation | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| integrated-reports | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| requests | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| aws-evidence | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| purge | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| settings | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| evidence-global | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| evidence-engagement | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| evidence-assessment | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| evidence-record | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| evidence-reuse | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| desk-review | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| overview | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| scope | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| questionnaire | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| report | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| report-summary | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| review-queue | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| conclusions | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| findings | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| workpaper | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| snapshots | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| comparison | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| narrative | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| board-inputs | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| soa | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| rfi-items | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| rfi-versions | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| rfi-links | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| report-iso | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| report-summary-iso | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| nist-overview | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| nist-questionnaire | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| interim-conclusions | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| aws_evidence-ready | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| aws_evidence-pulling | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| aws_evidence-result | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| aws_evidence-error | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| aws_evidence-notconfigured | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b3-context-complete-default | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b3-followups-loaded | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b3-hub-loading | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b3-hub-error | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b3-question-step-org | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b3-question-step-data | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b3-question-step-data-yes | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b3-question-step-last | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b3-scope-error | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b3-scope-saving | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b3-scope-complete-loading | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b3-scope-complete-error | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b3-screening-form-default | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b3-screening-form-loading | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b3-screening-form-error | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b3-screening-form-complete | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b3-screening-form-screened | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b3-section-questions-default | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b3-sections-default | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b3-sections-saved | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b3-sections-empty | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b4-desk_review-ready | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b4-desk_review-running | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b4-desk_review-findings | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b4-desk_review-rerun | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b4-desk_review-error | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-analysis-running | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-analysis-complete | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-analysis-error | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-analysis-error-all | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-analysis-gate | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-analysis-gate-no-override | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-basis-empty | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-basis-filled | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-basis-invalid | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-basis-locked | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-basis-saved | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-board-inputs-empty | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-board-inputs-partly | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-board-inputs-complete | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-board-inputs-dense | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-board-inputs-error | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-conclusion-card-pending | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-conclusion-card-edit | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-conclusion-card-approved | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-conclusion-card-edited | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-conclusion-card-rejected | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-conclusion-card-blocked | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-conclusion-card-no-citation | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-conclusion-card-superseded | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-conclusion-card-locked | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-conclusion-card-conflict | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-conclusion-card-bulk | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-conclusions-default | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-conclusions-legacy-bulk | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-conclusions-empty | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-narrative-empty | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-narrative-generating | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-narrative-drafted | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-narrative-partly-accepted | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-narrative-accepted | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-narrative-error | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-narrative-not-released | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-recommended-action-empty | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-recommended-action-drafting | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-recommended-action-drafted | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-recommended-action-edited | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-recommended-action-error | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-recommended-action-saved | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-recommended-action-gaps-required | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-recommended-action-limit | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-recommended-action-stale | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-recommended-action-not-open | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-recommended-action-not-draftable | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-release-blocked | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-release-ready | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-release-confirm | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-release-released | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-release-stale | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-report-loading-loading | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-requirement-card-v2 | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-requirement-card-v2-draft | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-requirement-card-contradiction | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-requirement-card-v1 | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-requirement-card-none | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-review-finding-card-draft | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-review-finding-card-needs-review | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-review-finding-card-notes | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-review-finding-card-accepted | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-review-finding-card-rejected | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-review-queue-default | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-review-queue-shared | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-review-queue-done | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b5-review-queue-empty | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b6-comparison-default | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b6-magic_invalid-expired | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b6-magic_invalid-revoked | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b6-magic_invalid-unknown | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b6-magic_links-default | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b6-magic_links-empty | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b6-magic_links-error | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b6-magic_links-loading | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b6-magic_links-newlink | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b6-magic_links-revoke | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b6-magic_upload-default | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b6-magic_upload-uploading | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b6-magic_upload-done | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b6-magic_upload-error | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b6-report_snapshots-default | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b6-rfi-default | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b6-rfi-error | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b6-rfi-issue | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b6-rfi-loading | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b6-rfi-noscope | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b6-rfi-versions | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b6-soa-default | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b7-404-page | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b7-404-engagement | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b7-500-error | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b7-500-down | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b7-500-upstream | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b7-empty-states-engagements | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b7-empty-states-evidence | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b7-empty-states-review | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b7-empty-states-search | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b7-empty-states-findings | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b7-empty-states-report | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b7-htmx-swaps-ok | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b7-htmx-swaps-bad | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b7-link-expired-expired | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b7-menus-popovers-default | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b7-mobile-shell-default | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b7-modals-delete | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b7-modals-purge | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b7-modals-send | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b7-modals-invite | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b7-modals-discard | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b7-modals-failed | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b7-skeleton-detail-loading | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b7-skeleton-detail-loaded | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b7-skeleton-table-loading | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b7-skeleton-table-loaded | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| b7-toasts-default | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| evidence_reuse-default | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| evidence_reuse-error | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| login-default | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| login-error | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| login-loading | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| workpaper_entry-default | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| workpaper_entry-legacy | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| workpaper_entry-excluded | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| gallery | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| questionnaire-open | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| conclusions-expanded | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| conclusions-edit | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| review-selected | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| evidence-cited | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |
| confirm-dialog | N/A / N/A | N/A / N/A | N/A / N/A | N/A / N/A | Pending DOM check |

## Static type risks, not rendered counts

`yozora-components.css` makes `.help` 12px. `partials/section_questions.html` applies it to question guidance, skip reasons, confidence and desk-review notes. That violates the project reason-role target of 14px independently of whether contrast passes. Citation quotes inherit body type and `.concl` is 16px, so the report does not claim that all audit content is tiny. At capture time classify each below-14 node as metadata or decision-bearing content, using the text samples and selector in rendered-measurements.json.

## Contrast method and complete matrix

The complete [contrast appendix](CONTRAST_APPENDIX.md) contains every source-discovered foreground-token candidate against declared surface families in light and dark, with each accent where needed. It is a conservative superset, not a list of verified DOM pairings. [contrast-data.json](contrast-data.json) retains declaration locations and all ratios; [contrast.py](tools/contrast.py) reproduces them. Source-computed values are rounded to three decimals. WCAG normal text requires 4.5:1; large text and non-text markers can use 3:1 when the applicable conditions hold.

The calculation linearizes sRGB channels, uses relative luminance and `(Llighter + .05)/(Ldarker + .05)`, samples 101 positions on each gradient segment, then composites declared alpha surfaces. Glass includes the CSS saturation approximation on a flat canvas. The min/max ratios cover lightest and darkest gradient contributions and intermediate samples. Nested surfaces are enumerated in the appendix. Blur, content behind overlays, custom firm colors, hover oklab mixing and disabled opacity are not certified. Print reports have a separate palette and are outside this portal audit.

The Playwright measurement tool also records computed foreground and ancestor background/opacity/image layers. Associate these with source tokens before calling a candidate failure an actual usage failure. Validate glass bounds by inspecting real backdrop pixels in the capture follow-up.

### Base body tokens against canvas and reading surfaces

| Theme | Text token | Surface | Minimum | Maximum | AA normal |
|---|---|---|---:|---:|---|
| light | muted | canvas | 4.720 | 5.314 | Pass |
| light | muted | glass | 5.823 | 6.087 | Pass |
| light | muted | solid | 6.429 | 6.498 | Pass |
| light | text | canvas | 12.385 | 13.942 | Pass |
| light | text | glass | 15.278 | 15.971 | Pass |
| light | text | solid | 16.868 | 17.051 | Pass |
| light | text-2 | canvas | 6.953 | 7.827 | Pass |
| light | text-2 | glass | 8.577 | 8.967 | Pass |
| light | text-2 | solid | 9.470 | 9.573 | Pass |
| dark | muted | canvas | 6.035 | 6.393 | Pass |
| dark | muted | glass | 5.133 | 5.476 | Pass |
| dark | muted | solid | 6.877 | 6.913 | Pass |
| dark | text | canvas | 13.199 | 13.982 | Pass |
| dark | text | glass | 11.226 | 11.976 | Pass |
| dark | text | solid | 15.042 | 15.119 | Pass |
| dark | text-2 | canvas | 8.349 | 8.844 | Pass |
| dark | text-2 | glass | 7.101 | 7.575 | Pass |
| dark | text-2 | solid | 9.514 | 9.563 | Pass |

### Interpretation

Base text, secondary and muted tokens pass AA normal against the modeled canvas, glass and solid surfaces. Preserve this evidence when deciding whether a reading problem is size, hierarchy, repetition or contrast. Seven non-graphite presets retain light accent-text in dark theme and need pair-specific correction. Some primary gradient endpoint pairings fall below 4.5:1, but endpoint bounds are not proof that the text sits over that endpoint. Semantic amber/orange marker colors must not be used indiscriminately as small text.

The status inventory records where color is a fill, marker or foreground: [STATUS_INVENTORY.md](STATUS_INVENTORY.md). A badge can use a readable text token with a low-contrast colored marker without failing text contrast; inspect its actual anatomy.

## Required follow-up

Run the retained capture/measurement tool on the already running app from an unrestricted browser host. Review screenshots by eye, check keyboard focus/history, resolve seed-dependent fixtures, replace pending geometry tables and associate every issue with an existing capture. This dispatch stops after source/HTTP Phase 12 under A2; it does not claim visual sign-off.
