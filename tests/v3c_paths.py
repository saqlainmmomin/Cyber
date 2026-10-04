"""File set of V3-C prior domain scores (tasks/handoffs/2026-10-04-v3c-prior-domain-scores.md).

Older file-set guards import this to allow exactly these paths for the V3-C backend PR (a scoped,
per-PR allowance; no guard is removed or loosened beyond these paths).
"""

V3C_PRIOR_DOMAINS_PATHS = (
    "app/services/prior_period.py",
    "tests/test_v3c_prior_domains.py",
    "tests/test_p6_9_prior_period.py",
    "tests/v3c_paths.py",
    "tasks/handoffs/2026-10-04-v3c-prior-domain-scores.md",
    # Guard files that gained this allowance.
    "tests/p6_10_support.py",
    "tests/test_p6_2b_dpdpa_criteria.py",
    "tests/test_p6_8_b2_docx_xlsx.py",
    "tests/test_p6_8_v3a_data_capture.py",
    "tests/test_p6_8_v3b_file_set.py",
)
V3C_PRIOR_DOMAINS_EXCLUDES = [f":(exclude){path}" for path in V3C_PRIOR_DOMAINS_PATHS]
