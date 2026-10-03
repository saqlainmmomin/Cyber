"""File set of the Yozora backend features PR (tasks/handoffs/2026-10-03-yozora-backend-features.md).

Older file-set guards import this to allow exactly these paths for this PR (a scoped, per-PR
allowance, as tests/p6_8_v3a_paths.py does for P6-8 V3-A; no guard is removed or loosened beyond
these paths). Nothing in the set calls a model; tests/test_yozora_read_models.py checks that.
"""

YOZORA_BACKEND_APP_PATHS = (
    "alembic/versions/b7d41c9e2a63_yozora_backend_features.py",
    # Models
    "app/models/__init__.py", "app/models/firm_settings.py", "app/models/client.py",
    "app/models/assessment.py", "app/models/magic_link.py",
    # Services
    "app/services/firm_settings.py", "app/services/retention.py", "app/services/engagement_factory.py", "app/services/actions_export.py",
    "app/services/magic_links.py", "app/services/rfi_requests.py", "app/services/findings.py",
    "app/services/evidence_inventory.py", "app/services/assessment_stage.py",
    "app/services/prefill_freshness.py", "app/services/request_summary.py",
    # Routers
    "app/main.py", "app/routers/firm_settings.py", "app/routers/retention.py", "app/routers/web.py",
    "app/routers/magic.py",
    # Templates
    "app/templates/base.html", "app/templates/pages/dashboard.html", "app/templates/pages/firm_settings.html",
    "app/templates/pages/client_detail.html", "app/templates/partials/engagement_retention.html",
    "app/templates/pages/engagement_detail.html", "app/templates/pages/new_assessment.html",
    "app/templates/pages/remediation_tracker.html", "app/templates/pages/comparison.html",
    "app/templates/partials/magic_links.html", "app/templates/partials/rfi_links.html",
    "app/templates/magic/upload.html", "app/templates/magic/invalid.html",
)
YOZORA_BACKEND_EXCLUDES = [f":(exclude){path}" for path in YOZORA_BACKEND_APP_PATHS]

# New tests, docs and the existing tests this PR edits deliberately (Alembic head pins, retention
# scenarios, and one scoped allowance line per file-set guard).
YOZORA_BACKEND_OTHER_PATHS = (
    "tasks/handoffs/2026-10-03-yozora-backend-features.md", "docs/product/yozora-migration-map.md",
    "tests/yozora_backend_paths.py", "tests/yozora_support.py",
    "tests/test_yozora_firm_settings.py", "tests/test_yozora_add_assessment.py",
    "tests/test_yozora_actions_export.py", "tests/test_yozora_comparison_link.py",
    "tests/test_yozora_magic_link_contacts.py", "tests/test_yozora_read_models.py",
    # Alembic head pins and retention behaviour
    "tests/test_alembic_baseline_immutable.py", "tests/test_correctness_bundle.py", "tests/test_data_integrity.py",
    "tests/test_p5_2_reader_migration.py", "tests/test_p5_3_framework_desk_review.py",
    "tests/test_p5_4_adaptive_ucc_questionnaire.py", "tests/test_p5_6_rfi_rebuild.py",
    "tests/test_p6_6_report_foundations.py", "tests/test_p6_8_v3a_data_capture.py",
    "tests/test_startup_invariants.py", "tests/test_retention.py",
    # File-set guards: one scoped allowance each
    "tests/p6_10_support.py", "tests/test_p6_2b_dpdpa_criteria.py", "tests/test_p6_3a_grounding.py", "tests/test_p6_4_cap_upload_limit.py", "tests/test_p6_4_v2_judge.py", "tests/test_p6_4_whats_missing.py",
    "tests/test_p6_7_requirement_card.py", "tests/test_p6_7b_add_to_rfi.py", "tests/test_p6_8_b2_docx_xlsx.py",
    "tests/test_p6_8_board_report_v2.py", "tests/test_p6_9_file_set.py", "tests/test_p6_nist_csf2_alignment.py",
    "tests/test_validation_harness.py",
)
YOZORA_BACKEND_FILES = YOZORA_BACKEND_APP_PATHS + YOZORA_BACKEND_OTHER_PATHS
