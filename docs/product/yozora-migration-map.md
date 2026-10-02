# Yozora migration map

Generated 2026-10-01 from `app/templates/` and `tests/`. Every template is listed. **Must-keep** = element ids, `hx-*` targets/swaps and `data-*` attributes found in the template (a migration may restyle but not rename these), plus the test files that reference the template. Strings asserted by tests must be checked per slice with `grep -n` on the listed test files; any intended change is listed in that slice's handoff so tests are updated deliberately.

**Revised 2026-10-02 (approved flow map, `2026-10-01-app-design-mockups/flow-map.html`, and `screens/IA-SPEC.md`):** engagement tabs are Overview, Evidence, Findings and actions, Reports; assessment tabs are Overview, Scope, Questionnaire, Review, Report. One central Evidence inventory per engagement replaces the Documents tab, the AWS evidence tab and the standalone client-links page. Retention moves to firm Settings. A new firm field, contact email for clients, backs the "Email the firm" button on expired-link pages. Rows below are updated to match; must-keep ids and attributes are unchanged.

Slice key: S1 shell, S2 component layer and `/design`, S3 Home, clients, settings, S4 engagements, S5 assessment, scope, questionnaire, S6 documents, desk review, evidence, S7 analysis, report, review, S8 RFI, versions, client-facing, S9 system states, dark and mobile pass.

| Template | Slice | Target pattern | Must-keep: ids | hx-target | hx-swap | data-* | Tests referencing it |
|---|---|---|---|---|---|---|---|
| `base.html` | S1 | App shell, nav, canvas | - | - | - | - | test_p6_7_requirement_card.py, test_p6_7b_add_to_rfi.py, test_p6_8_b2_docx_xlsx.py, test_p6_8_board_report_v2.py, test_p6_9_file_set.py |
| `components/conclusion_card.html` | S7 | Review detail | - | `#conclusion-card-{{ card.conclusion.id }}` | `outerHTML` | `data-conclusion-card`, `data-state`, `data-version` | test_conclusion_approval.py, test_p6_3a_grounding.py, test_p6_4_cap_upload_limit.py, test_p6_4_whats_missing.py, test_p6_7_requirement_card.py, test_p6_7b_add_to_rfi.py |
| `components/engagement_status_badge.html` | S2 | Pill/status | - | - | - | - | - |
| `components/evidence_status_badge.html` | S2 | Pill/status | - | - | - | - | - |
| `components/finding_card.html` | S7 | Card | - | `#finding-{{ view.finding.id }}` | `outerHTML` | `data-action-history`, `data-action-row`, `data-action-status`, `data-close-control`, `data-finding-card`, `data-finding-origin`, `data-history-action`, `data-reopen-control`, `data-source-approved`, `data-verify-control` | test_correctness_bundle.py, test_findings.py, test_needs_review_ui.py, test_p5_2_reader_migration.py, test_remediation_tracking.py |
| `components/requirement_card_body.html` | S7 | Review detail | - | `#conclusion-card-{{ card.conclusion.id }}` | `outerHTML` | `data-acknowledged`, `data-claim`, `data-claim-link`, `data-client-said`, `data-contradiction`, `data-criteria-source`, `data-criterion`, `data-criterion-result`, `data-divergence-ack-form`, `data-divergence-note`, `data-evidence-shared`, `data-evidence-shows`, `data-missing-evidence`, `data-proposal-reason`, `data-quality-chip`, `data-requirement-card`, `data-requirement-source`, `data-rfi-add-form`, `data-rfi-request`, `data-rfi-request-key`, `data-rfi-request-preview`, `data-rfi-request-status`, `data-rfi-state`, `data-rfi-withdraw-form`, `data-tone`, `data-unsupported-assertion` | test_p6_2b_dpdpa_criteria.py, test_p6_3a_grounding.py, test_p6_4_cap_upload_limit.py, test_p6_4_whats_missing.py, test_p6_7_requirement_card.py, test_p6_7b_add_to_rfi.py, test_p6_8_board_report_v2.py |
| `components/status_badge.html` | S2 | Pill/status | - | - | - | - | - |
| `components/workpaper_entry.html` | S6 | Row card | - | - | - | `data-decision-state`, `data-in-scope`, `data-revision-action`, `data-revision-history`, `data-workpaper-entry`, `data-workpaper-finding` | test_p6_7_requirement_card.py, test_workpaper.py |
| `magic/invalid.html` | S8 | Client page (mobile-first) | - | - | - | - | - |
| `magic/upload.html` | S8 | Client page (mobile-first): request checklist per item | `file-upload`, `item-key` | - | - | - | - |
| `pages/assessment.html` | S5 | Assessment shell: tabs Overview, Scope, Questionnaire, Review, Report; stepper on Overview only (b3-hub) | - | - | - | `data-archived-banner` | test_report_snapshots.py |
| `pages/aws_evidence.html` | S6 | Evidence sub-page "Pull from AWS" under engagement Evidence tab (no own tab) | `aws-external-id` | - | - | `data-aws-not-configured`, `data-consultant-policy`, `data-external-id`, `data-permissions-policy`, `data-trust-policy` | test_aws_evidence.py |
| `pages/client_detail.html` | S3 | Page header + engagement table; retention form removed (moved to firm Settings), `retention-years` and `data-retention-form` move with it | `retention-years`, `reviewer-name` | - | - | `data-archived-engagement`, `data-purge-complete-control`, `data-purge-record`, `data-retention-form` | - |
| `pages/comparison.html` | S8 | Table | - | - | - | - | - |
| `pages/conclusions.html` | S7 | List | `reviewer-name` | - | - | `data-count` | test_conclusion_approval.py, test_p6_3a_grounding.py, test_p6_4_cap_upload_limit.py, test_p6_4_whats_missing.py, test_p6_7_requirement_card.py |
| `pages/dashboard.html` | S3 | Home: attention rows + engagement table | - | `#client-{{ c.id }}-engagements` | `innerHTML` | `data-shortcut-scope` | - |
| `pages/engagement_detail.html` | S4 | Engagement Overview tab: assessments table with Stage and Next step, no stepper; single-assessment engagements open on the assessment | - | - | - | - | - |
| `pages/engagement_purge.html` | S4 | Destructive confirm | `confirm-name`, `reviewer-name` | - | - | `data-purge-count`, `data-purge-dependency`, `data-purge-files`, `data-purge-form`, `data-purge-reason`, `data-purge-reasons` | - |
| `pages/evidence_detail.html` | S6 | Detail page | - | - | - | - | - |
| `pages/evidence_reuse.html` | S6 | Table | - | - | - | `data-reuse-candidate`, `data-reuse-confirm`, `data-reuse-error`, `data-reuse-warning`, `data-warnings` | test_longitudinal_demo.py |
| `pages/evidence_span.html` | S6 | Citation block | `cited-span` | - | - | `data-cited-span`, `data-evidence-span-text`, `data-span-unavailable` | test_p6_3a_grounding.py, test_p6_4_cap_upload_limit.py, test_p6_4_whats_missing.py, test_p6_7_requirement_card.py |
| `pages/findings.html` | S7 | Table | `reviewer-name` | - | `none` | `data-eligible-conclusion` | test_findings.py, test_remediation_tracking.py |
| `pages/integrated_reports.html` | S4 | Engagement Reports tab | `reviewer-name` | - | - | `data-excluded-assessment`, `data-included-assessment`, `data-integrated-row`, `data-issue-control`, `data-snapshot-id`, `data-snapshot-state` | test_pdf_updates.py |
| `pages/login.html` | S3 | Auth placeholder card | `password`, `username` | - | - | - | - |
| `pages/new_engagement.html` | S4 | Form page | `client-fields`, `create-engagement`, `description`, `engagement_name`, `engagement_type`, `new-engagement-form` | `#client-fields` | `innerHTML` | - | - |
| `pages/remediation_tracker.html` | S4 | Engagement Findings and actions tab | - | - | - | `data-assessment-row`, `data-awaiting-action`, `data-overdue-action`, `data-owner-row`, `data-rollup-count`, `data-severity-row` | test_remediation_tracking.py |
| `pages/report_snapshots.html` | S8 | Table | `reviewer-name` | - | - | `data-board-export`, `data-board-report-preview`, `data-issue-control`, `data-snapshot-id`, `data-snapshot-row`, `data-snapshot-state`, `data-snapshot-type`, `data-soa-link` | test_p6_2b_dpdpa_criteria.py, test_p6_3a_grounding.py, test_p6_4_cap_upload_limit.py, test_p6_4_whats_missing.py, test_p6_7_requirement_card.py, test_p6_7b_add_to_rfi.py, test_p6_8_b2_docx_xlsx.py, test_p6_8_board_report_v2.py, test_p6_9_file_set.py |
| `pages/review_queue.html` | S7 | Review queue (v3) | `reviewer-name` | - | - | `data-conclusion-id`, `data-flags`, `data-queue-group`, `data-queue-index`, `data-queue-item`, `data-queue-keys`, `data-queue-nav`, `data-risk`, `data-shared`, `data-shared-claim`, `data-state` | test_p6_3a_grounding.py, test_p6_4_cap_upload_limit.py, test_p6_4_whats_missing.py, test_p6_7_requirement_card.py |
| `pages/rfi.html` | S8 | Engagement Evidence tab, Requests view: one assessment request | `reviewer-name` | - | `none` | `data-conclusion-id`, `data-rfi-generate-form`, `data-rfi-issue-control`, `data-rfi-item`, `data-rfi-kind`, `data-rfi-mapped`, `data-rfi-omit`, `data-rfi-preview`, `data-rfi-request`, `data-rfi-requests`, `data-rfi-requests-note`, `data-rfi-scope-required`, `data-rfi-version-row`, `data-rfi-versions`, `data-rfi-withdraw-form`, `data-snapshot-id`, `data-snapshot-state` | test_p5_6_rfi_rebuild.py, test_p6_2b_dpdpa_criteria.py, test_p6_3a_grounding.py, test_p6_4_cap_upload_limit.py, test_p6_4_whats_missing.py, test_p6_7_requirement_card.py, test_p6_7b_add_to_rfi.py, test_p6_8_board_report_v2.py |
| `pages/soa.html` | S8 | Table | `reviewer-name` | - | `none` | `data-applicability`, `data-approved-rationale`, `data-soa-justification-form`, `data-soa-row` | test_p6_2b_dpdpa_criteria.py, test_p6_3a_grounding.py, test_p6_4_cap_upload_limit.py, test_p6_4_whats_missing.py, test_p6_7_requirement_card.py, test_p6_7b_add_to_rfi.py, test_p6_8_board_report_v2.py, test_p6_9_file_set.py |
| `pages/workpaper.html` | S6 | Table page | - | - | - | `data-count`, `data-report-basis`, `data-run-stale`, `data-run-status`, `data-workpaper-section`, `data-workpaper-unconcluded` | test_p6_3a_grounding.py, test_p6_7_requirement_card.py, test_workpaper.py |
| `partials/analysis_complete.html` | S7 | Alert/CTA | - | - | - | `data-review-conclusions-link` | test_report_snapshots.py |
| `partials/analysis_error.html` | S7 | Alert | - | `#analysis-area` | `innerHTML` | `data-analysis-failed-frameworks` | - |
| `partials/analysis_gate_blocked.html` | S7 | Alert | `override_reason` | `#analysis-area` | `innerHTML` | `data-completion-gate-blocked`, `data-completion-override-form` | test_correctness_bundle.py |
| `partials/analysis_running.html` | S7 | Loading | - | - | `outerHTML` | - | - |
| `partials/aws_evidence_panel.html` | S6 | Panel | `aws-evidence-panel` | `#aws-evidence-panel` | `outerHTML` | `data-aws-error`, `data-aws-evidence-row`, `data-aws-pull-form`, `data-aws-result`, `data-aws-source-row` | test_aws_evidence.py |
| `partials/client_picker.html` | S3 | Menu/popover list | `client_id`, `company_name`, `company_size`, `industry` | - | - | - | - |
| `partials/context_complete.html` | S5 | Alert/empty | - | - | - | - | - |
| `partials/desk_review_error.html` | S6 | Alert | - | `#desk-review-area` | `innerHTML` | - | - |
| `partials/desk_review_findings.html` | S6 | Table/cards | - | `#desk-review-area` | `innerHTML` | `data-desk-review-failed-frameworks` | - |
| `partials/desk_review_ready.html` | S6 | Empty/CTA | `dr-spinner` | `#desk-review-area` | `innerHTML` | - | - |
| `partials/desk_review_running.html` | S6 | Loading | - | - | `outerHTML` | - | - |
| `partials/document_list.html` | S6 | Folded into the engagement Evidence inventory table (`b4-evidence`) | - | `#document-list` | `innerHTML` | - | - |
| `partials/documents_tab.html` | S6 | Folded into the engagement Evidence inventory (`b4-evidence`): upload panel | `desk-review-area`, `document-list`, `drop-zone`, `file-input`, `file-name-display`, `upload-progress`, `upload-progress-bar` | `#document-list` | `innerHTML` | `data-evidence-reuse-link` | - |
| `partials/engagement_list.html` | S4 | Table | - | - | - | - | - |
| `partials/engagement_retention.html` | S3 | Split: retention period moves to firm Settings (data housekeeping); engagement keeps only the archive/unarchive action and archived banner | `reviewer-name` | - | - | `data-archive-control`, `data-archived-banner`, `data-purge-preview-link`, `data-retention-panel`, `data-unarchive-control` | - |
| `partials/followup_questions.html` | S5 | Form | - | - | - | - | - |
| `partials/framework_panel.html` | S7 | Framework card | - | - | - | - | - |
| `partials/framework_tabs.html` | S5 | Tabs | `framework-panel` | `#framework-panel` | `innerHTML` | - | - |
| `partials/magic_links.html` | S8 | Engagement Evidence tab, Requests view: request cards with requested items, received count, expiry | `magic-links`, `requested-items` | `#magic-links` | `outerHTML` | - | - |
| `partials/no_report.html` | S7 | Empty state | - | - | - | - | - |
| `partials/question_step.html` | S5 | Form step | `previous-answers` | `#context-wizard` | `innerHTML` | `data-depends-on`, `data-depends-value` | - |
| `partials/questionnaire_sections.html` | S5 | Rows | `section-content` | `#section-content` | `innerHTML` | `data-collapsible-section`, `data-section`, `data-stat-answered`, `data-stat-awaiting-confirmation` | test_p5_4_adaptive_ucc_questionnaire.py |
| `partials/questionnaire_tab.html` | S5 | Panel list | `analysis-area`, `context-wizard`, `questionnaire-content`, `screening-body`, `screening-section` | `#analysis-area`, `#screening-body` | `innerHTML` | `data-screening-unavailable`, `data-shortcut-scope` | test_p5_4_adaptive_ucc_questionnaire.py |
| `partials/release_panel.html` | S7 | Panel + confirm | - | - | `none` | `data-release-blockers`, `data-release-form`, `data-release-panel`, `data-release-state` | test_p5_2_reader_migration.py |
| `partials/remediation_panel.html` | S4 | Table | - | - | - | `data-legacy-remediation` | test_remediation_tracking.py |
| `partials/remediation_summary.html` | S4 | Stat row | - | - | - | - | - |
| `partials/report_basis_panel.html` | S7 | Panel | - | - | `none` | `data-period-locked`, `data-period-recorded`, `data-report-basis-form`, `data-report-basis-panel` | test_p6_3a_grounding.py |
| `partials/report_summary.html` | S7 | Framework cards | `remediation-summary-area`, `review-banner`, `rfi-section` | - | - | `data-analysis-incomplete-banner`, `data-copy-target`, `data-copy-trigger`, `data-dpdpa-readiness-note`, `data-framework-coverage`, `data-framework-failed`, `data-framework-not-scored`, `data-framework-pending`, `data-legacy-remediation`, `data-release-blockers`, `data-release-state`, `data-rfi-link`, `data-view-mode` | test_correctness_bundle.py, test_p6_0e_dpdpa_pack_correctness.py, test_p6_3a_grounding.py, test_p6_6_report_foundations.py, test_report_snapshots.py |
| `partials/report_tab.html` | S7 | Tabs + panels | `report-content` | - | `innerHTML` | - | - |
| `partials/review_finding_card.html` | S7 | Review detail | - | `#review-card-{{ item.id }}` | `outerHTML` | `data-review-card`, `data-review-status`, `data-risk-level` | test_correctness_bundle.py, test_needs_review_ui.py, test_p5_2_reader_migration.py |
| `partials/rfi_links.html` | S8 | Table | `rfi-links` | `#rfi-links` | `outerHTML` | `data-rfi-coverage`, `data-rfi-link-error`, `data-rfi-link-form`, `data-rfi-link-row`, `data-rfi-links`, `data-rfi-new-link`, `data-rfi-received`, `data-rfi-unsent` | test_p5_6_rfi_rebuild.py, test_p6_7b_add_to_rfi.py |
| `partials/scope_complete.html` | S5 | Alert/empty | - | - | - | `data-rfi-link` | test_p6_0f_dpdpa_followups.py |
| `partials/scope_form.html` | S5 | Form | - | - | - | `data-scope-group` | - |
| `partials/scope_tab.html` | S5 | Form panel | - | - | - | - | - |
| `partials/screening_form.html` | S5 | Form | `screening-indicator` | `#screening-section` | `innerHTML` | - | test_p5_4_adaptive_ucc_questionnaire.py |
| `partials/section_questions.html` | S5 | Form | - | `#followup-{{ q.id }}`, `#section-content` | `innerHTML` | `data-pre-filled`, `data-prefill-badge`, `data-progress-counter`, `data-question-card`, `data-question-index`, `data-question-name`, `data-questionnaire-form`, `data-required-question`, `data-save-indicator`, `data-section-header`, `data-section-questionnaire`, `data-validation-summary` | - |
| `partials/section_saved.html` | S5 | Toast/alert | - | - | - | - | - |
| `partials/status_timeline.html` | S4 | Stepper | - | - | - | - | - |
| `partials/upload_status.html` | S6 | Status rows | - | - | - | - | - |
| `reports/board_report.html` | out of scope | Print template: tokens only | - | - | - | `data-comparison-framework`, `data-framework`, `data-preview`, `data-roadmap-group`, `data-section`, `data-soa-control` | test_p6_7b_add_to_rfi.py, test_p6_8_b2_docx_xlsx.py, test_p6_9_file_set.py |
| `reports/workpaper_standalone.html` | out of scope | Print template | - | - | - | `data-count`, `data-decision-state`, `data-in-scope`, `data-report-basis`, `data-revision-action`, `data-run-stale`, `data-run-status`, `data-workpaper-entry`, `data-workpaper-finding`, `data-workpaper-section`, `data-workpaper-unconcluded` | test_p6_9_file_set.py |

72 templates accounted for.
