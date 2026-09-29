"""Additional P6-5b harness invariants from orchestration review."""

from __future__ import annotations

import json
from pathlib import Path

from tests.test_p6_5_ab_compare import V1, V2, compare, make_arm, write_run


def _add_run(arm: Path, company: str, run: int, settings: dict) -> None:
    write_run(
        arm,
        company,
        run,
        caught=[True],
        decoy_fp=[False],
        clean_fp=[False],
        outcomes={("dpdpa", 1): "compliant", ("iso27001", 1): "non_compliant"},
        settings=settings,
    )


def _mark_child_style_baseline(arm: Path) -> None:
    for run_json in arm.glob("*/run-*/run.json"):
        meta = json.loads(run_json.read_text(encoding="utf-8"))
        meta["dirty"] = True
        meta["entrypoint"] = "scripts.validation.run_company --_child"
        run_json.write_text(json.dumps(meta), encoding="utf-8")


def test_sibling_folder_trap_is_incomparable_against_baseline_counts(tmp_path):
    baseline = make_arm(tmp_path, "baseline", settings=V1, caught=[True])
    arm = make_arm(tmp_path, "v2", settings=V2, caught=[True])
    _add_run(arm, "c1", 4, V2)

    payload, _ = compare([f"v1={baseline}", f"v2={arm}"], baseline="v1")
    gate = payload["gate"]["v2"]
    assert gate["comparable"] is False
    assert "run_count_mismatch" in gate["reasons"]
    assert gate["holds"] is None


def test_unequal_company_run_counts_use_existing_mismatch_reason(tmp_path):
    baseline = make_arm(tmp_path, "baseline", settings=V1, caught=[True], runs=4)
    arm = make_arm(tmp_path, "v2", settings=V2, caught=[True], runs=3)
    _add_run(arm, "c1", 4, V2)

    payload, _ = compare([f"v1={baseline}", f"v2={arm}"], baseline="v1")
    gate = payload["gate"]["v2"]
    assert gate["comparable"] is False
    assert gate["reasons"] == ["run_count_mismatch"]
    assert gate["holds"] is None


def test_dirty_child_style_baseline_without_settings_is_accepted(tmp_path):
    baseline = make_arm(tmp_path, "baseline", settings=None, caught=[True])
    _mark_child_style_baseline(baseline)
    arm = make_arm(tmp_path, "v2", settings=V2, caught=[True])

    payload, _ = compare([f"v1={baseline}:pipeline=v1", f"v2={arm}"], baseline="v1")
    assert payload["arms"]["v1"]["settings_source"] == "declared"
    assert payload["arms"]["v1"]["pipeline"] == "v1"
    assert payload["gate"]["v2"]["comparable"] is True
    assert payload["gate"]["v2"]["holds"] is True
