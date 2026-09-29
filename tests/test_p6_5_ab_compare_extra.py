"""Additional P6-5b harness invariants from orchestration review."""

from __future__ import annotations

import json
from pathlib import Path

from tests.test_p6_5_ab_compare import V1, V2, compare, make_arm, write_run
from scripts.validation import score as score_module
from scripts.validation.score import DISTANCE, score_run


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


def _write_score_fixture(root: Path) -> tuple[Path, Path]:
    validation_root = root / "validation"
    pack = validation_root / "companies" / "synthetic"
    run_dir = pack / "run-1"
    run_dir.mkdir(parents=True)

    gap_specs = [
        ("G01", "G.PARTIAL.IE", "partially_compliant", "insufficient_evidence"),
        ("G02", "G.NON.PARTIAL", "non_compliant", "partially_compliant"),
        ("G03", "G.COMPLIANT", "partially_compliant", "compliant"),
        ("G04", "G.NA", "partially_compliant", "not_applicable"),
        ("G05", "G.MISSING", "partially_compliant", None),
    ]
    decoy_specs = [
        ("D01", "D.IE", "insufficient_evidence"),
        ("D02", "D.NA", "not_applicable"),
    ]
    clean_specs = [
        ("C.IE", "insufficient_evidence"),
        ("C.NA", "not_applicable"),
    ]
    overrides = {
        requirement_id: actual_status
        for _gap_id, requirement_id, actual_status, _outcome in gap_specs
    }
    overrides.update({requirement_id: "compliant" for _decoy_id, requirement_id, _outcome in decoy_specs})
    overrides.update({requirement_id: "compliant" for requirement_id, _outcome in clean_specs})
    answer_key = {
        "schema_version": 1,
        "company_slug": "synthetic",
        "control_truth": {"dpdpa": {"default": "compliant", "overrides": overrides}},
        "planted_gaps": [
            {
                "gap_id": gap_id,
                "requirements": [{"framework_id": "dpdpa", "requirement_id": requirement_id}],
                "gap_class": "honest_gap",
                "actual_status": actual_status,
                "surface_answer": "not_implemented",
                "probing_depth": 1,
                "severity_expected": "medium",
                "description": "Synthetic gap",
                "evidence_trail": [{"source": "answer:synthetic", "locator": "answer", "fact": "fact"}],
                "key_facts": ["fact"],
                "what_followup_should_ask": "Follow up",
            }
            for gap_id, requirement_id, actual_status, _outcome in gap_specs
        ],
        "decoys": [
            {
                "decoy_id": decoy_id,
                "requirements": [{"framework_id": "dpdpa", "requirement_id": requirement_id}],
                "why_it_looks_like_a_gap": "Synthetic decoy",
                "why_it_is_compliant": "Synthetic control",
                "evidence_trail": [{"source": "answer:synthetic", "locator": "answer", "fact": "fact"}],
            }
            for decoy_id, requirement_id, _outcome in decoy_specs
        ],
        "clean_controls": [
            {"framework_id": "dpdpa", "requirement_id": requirement_id, "supporting_artifacts": []}
            for requirement_id, _outcome in clean_specs
        ],
        "authoring_notes": "Synthetic fixture",
    }
    conclusions = {
        "conclusions": [
            {"framework_id": "dpdpa", "requirement_id": requirement_id, "outcome": outcome}
            for _gap_id, requirement_id, _actual_status, outcome in gap_specs
            if outcome is not None
        ]
        + [
            {"framework_id": "dpdpa", "requirement_id": requirement_id, "outcome": outcome}
            for _decoy_id, requirement_id, outcome in decoy_specs
        ]
        + [
            {"framework_id": "dpdpa", "requirement_id": requirement_id, "outcome": outcome}
            for requirement_id, outcome in clean_specs
        ]
    }
    (pack / "answer_key.json").write_text(json.dumps(answer_key), encoding="utf-8")
    (run_dir / "run.json").write_text(json.dumps({"frameworks": []}), encoding="utf-8")
    (run_dir / "conclusions.json").write_text(json.dumps(conclusions), encoding="utf-8")
    return run_dir, validation_root


def test_score_uses_flagged_membership_for_gaps_decoys_and_clean_controls(tmp_path):
    run_dir, validation_root = _write_score_fixture(tmp_path)

    result = score_run(run_dir, validation_root=validation_root)
    gaps = {item["gap_id"]: item for item in result["gap_results"]}
    decoys = {item["decoy_id"]: item for item in result["decoy_results"]}
    clean = {item["requirement_id"]: item for item in result["clean_control_results"]}

    assert score_module.FLAGGED == {"non_compliant", "partially_compliant", "insufficient_evidence"}
    assert DISTANCE["partially_compliant"]["insufficient_evidence"] == 0.3
    assert DISTANCE["non_compliant"]["insufficient_evidence"] == 0.3
    assert gaps["G01"]["caught"] is True
    assert gaps["G02"]["caught"] is True
    assert all(gaps[gap_id]["caught"] is False for gap_id in ("G03", "G04", "G05"))
    assert decoys["D01"]["false_positive"] is True
    assert decoys["D02"]["false_positive"] is False
    assert clean["C.IE"]["false_positive"] is True
    assert clean["C.NA"]["false_positive"] is False


def test_partially_covered_run_is_incomparable(tmp_path):
    baseline = make_arm(tmp_path, "baseline", settings=V1, caught=[True])
    arm = make_arm(tmp_path, "v2", settings=V2, caught=[True])
    score_path = arm / "c1" / "run-1" / "score.json"
    score = json.loads(score_path.read_text(encoding="utf-8"))
    score["gap_results"][0]["requirements"][0]["outcome"] = "missing"
    score_path.write_text(json.dumps(score), encoding="utf-8")

    payload, _ = compare([f"v1={baseline}", f"v2={arm}"], baseline="v1")
    gate = payload["gate"]["v2"]
    assert gate["comparable"] is False
    assert "missing_conclusions" in gate["reasons"]
    assert gate["holds"] is None


def test_declared_v2_without_settings_is_incomparable_for_pack_verification(tmp_path):
    baseline = make_arm(tmp_path, "baseline", settings=V1, caught=[True])
    arm = make_arm(tmp_path, "v2", settings=None, caught=[True])

    payload, _ = compare([f"v1={baseline}", f"v2={arm}:pipeline=v2"], baseline="v1")
    gate = payload["gate"]["v2"]
    assert payload["arms"]["v2"]["settings_source"] == "declared"
    assert gate["comparable"] is False
    assert "pack_version_mismatch" in gate["reasons"]
    assert gate["holds"] is None


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
