"""TDD ("red") contract suite for P6-5: the aggregate-only A/B comparison.

Written by the designer before the implementation. It pins
``scripts/validation/ab_compare.py`` as specified in
``tasks/handoffs/2026-09-28-p6-5-v2-ab-and-flip.md`` (section "A/B comparison
tool") and must turn green WITHOUT edits. If an assertion looks wrong, report it
in the handoff's Results; do not change it.

Every run directory here is synthetic and built in ``tmp_path``. Nothing is read
from ``validation/`` or from a real harness run (D-P5-9-C). The sentinel strings
planted in answer-key-shaped fields must never reach the comparison output: that
output is what the orchestrator and Saqlain read, so it must stay aggregate-only.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

SENTINELS = ("SENTINEL-GAP", "SENTINEL-DECOY", "SENTINEL-DESC", "SENTINEL-FACT", "SENTINEL-CLASS", "SENTINELREQ")
PACKS = {"dpdpa": "2023+criteria-v1", "iso27001": "2022"}


def ab():
    return importlib.import_module("scripts.validation.ab_compare")


def source_of(framework_id: str, requirement_id: str) -> str:
    return "approved" if framework_id == "dpdpa" else "fallback"


def req(framework_id: str, n: int) -> dict:
    return {"framework_id": framework_id, "requirement_id": f"SENTINELREQ.{framework_id}.{n}"}


def write_run(
    root: Path,
    company: str,
    run: int,
    *,
    caught: list[bool],
    decoy_fp: list[bool],
    clean_fp: list[bool],
    outcomes: dict[tuple[str, int], str],
    settings: dict | None,
    llm_mode: str = "live",
    usage: dict | None = None,
    stages_ok: bool = True,
    failed_frameworks: tuple[str, ...] = (),
    prefilled: int = 2,
    rendered: int = 10,
) -> Path:
    run_dir = root / company / f"run-{run}"
    run_dir.mkdir(parents=True)
    gap_frameworks = ["dpdpa", "iso27001", "mixed"]
    gaps = []
    for index, value in enumerate(caught):
        kind = gap_frameworks[index % 3]
        requirements = [req("dpdpa", index), req("iso27001", index)] if kind == "mixed" else [req(kind, index)]
        gaps.append({
            "gap_id": f"SENTINEL-GAP-{index}", "gap_class": "SENTINEL-CLASS", "probing_depth": 1,
            "caught": value, "gap_score": 1.0 if value else 0.0, "grounded": True, "key_fact_recall": 1.0,
            "key_facts": ["SENTINEL-FACT"], "description": "SENTINEL-DESC", "requirements": requirements,
        })
    decoys = [
        {"decoy_id": f"SENTINEL-DECOY-{index}", "false_positive": value, "requirements": [req("iso27001", 100 + index)]}
        for index, value in enumerate(decoy_fp)
    ]
    clean = [
        {**req("dpdpa", 200 + index), "false_positive": value}
        for index, value in enumerate(clean_fp)
    ]
    run_meta = {"llm_mode": llm_mode, "slug": company}
    if settings is not None:
        run_meta["settings"] = settings
    files = {
        "run.json": run_meta,
        "score.json": {
            "aggregates": {"catch_rate": 0.0},
            "gap_results": gaps,
            "decoy_results": decoys,
            "clean_control_results": clean,
            "coverage": {"failed_frameworks": list(failed_frameworks), "conclusions_count": len(outcomes)},
            "cost": {
                "llm_usage": usage if usage is not None else {
                    "judge": {"calls": 2, "input_tokens": 1000, "output_tokens": 400, "non_ok": 1, "length": 1},
                    "extract": {"calls": 3, "input_tokens": 500, "output_tokens": 100, "non_ok": 0},
                },
                "stage_seconds": {"analysis": 10.0, "desk_review": 5.0},
            },
        },
        "conclusions.json": {"conclusions": [
            {**req(fid, n), "outcome": outcome} for (fid, n), outcome in outcomes.items()
        ]},
        "questionnaire_coverage.json": {
            "rendered_ids": [f"SENTINELREQ.q{i}" for i in range(rendered)],
            "prefilled_before_save": [f"SENTINELREQ.q{i}" for i in range(prefilled)],
            "answered": [],
        },
        "stages.json": [{"stage": "analysis", "ok": stages_ok, "detail": "SENTINEL-DESC"}],
        "probes.json": [],
    }
    for name, value in files.items():
        (run_dir / name).write_text(json.dumps(value), encoding="utf-8")
    return run_dir


V1 = {"analysis_pipeline_version": "v1", "v2_missing_pass": False, "pack_versions": PACKS}
V2 = {"analysis_pipeline_version": "v2", "v2_missing_pass": False, "pack_versions": PACKS}
STABLE = {("dpdpa", 1): "compliant", ("iso27001", 1): "non_compliant"}


def make_arm(root: Path, name: str, *, settings, caught, decoy_fp=(False,), clean_fp=(False, False),
             outcomes_per_run=None, companies=("c1", "c2"), runs=3, **kwargs) -> Path:
    arm = root / name
    for company in companies:
        for run in range(1, runs + 1):
            outcomes = (outcomes_per_run or [STABLE] * runs)[run - 1]
            write_run(arm, company, run, caught=list(caught), decoy_fp=list(decoy_fp),
                      clean_fp=list(clean_fp), outcomes=outcomes, settings=settings, **kwargs)
    return arm


def compare(specs, **kwargs):
    kwargs.setdefault("criteria_source", source_of)
    kwargs.setdefault("pack_versions", PACKS)
    return ab().build_comparison(specs, **kwargs)


# --------------------------------------------------------------------------- #
# Scenario 1: pooled metrics and splits
# --------------------------------------------------------------------------- #


def test_scenario_1_pooled_metrics_and_counts(tmp_path):
    v1 = make_arm(tmp_path, "v1", settings=V1, caught=[True, False, False], decoy_fp=[True], clean_fp=[False, False])
    payload, _markdown = compare([f"v1={v1}"])
    arm = payload["arms"]["v1"]
    assert payload["schema"] == "p6-5-ab.1"
    assert arm["pipeline"] == "v1" and arm["settings_source"] == "recorded"
    assert arm["companies"] == {"c1": 3, "c2": 3} and arm["runs"] == 6
    metrics = arm["metrics"]
    assert metrics["catch_rate"] == {"value": pytest.approx(1 / 3), "numerator": 6, "denominator": 18}
    assert metrics["decoy_fp_rate"] == {"value": 1.0, "numerator": 6, "denominator": 6}
    assert metrics["clean_fp_rate"] == {"value": 0.0, "numerator": 0, "denominator": 12}
    assert metrics["stability"] == {"value": 1.0, "requirements": 4}
    assert metrics["insufficient_evidence_rate"] == {"value": 0.0, "numerator": 0, "denominator": 12}
    assert metrics["prefill_rate"] == {"value": 0.2, "numerator": 12, "denominator": 60}
    assert payload["gate"] == {}


def test_scenario_1_splits_by_framework_and_criteria_source(tmp_path):
    # Gap 0 is DPDPA (caught), gap 1 ISO (missed), gap 2 spans both (caught).
    v2 = make_arm(tmp_path, "v2", settings=V2, caught=[True, False, True])
    arm = compare([f"v2={v2}:pipeline=v2"])[0]["arms"]["v2"]
    by_framework = arm["by_framework"]
    assert set(by_framework) == {"dpdpa", "iso27001", "mixed"}
    assert by_framework["dpdpa"]["catch_rate"]["value"] == 1.0
    assert by_framework["iso27001"]["catch_rate"]["value"] == 0.0
    assert by_framework["mixed"]["catch_rate"]["denominator"] == 6
    assert by_framework["iso27001"]["decoy_fp_rate"]["denominator"] == 6
    assert by_framework["dpdpa"]["clean_fp_rate"]["denominator"] == 12
    assert by_framework["dpdpa"]["stability"]["requirements"] == 2
    by_source = arm["by_criteria_source"]
    assert set(by_source) == {"approved", "fallback", "mixed"}
    assert by_source["approved"]["catch_rate"]["value"] == 1.0
    assert by_source["fallback"]["catch_rate"]["value"] == 0.0
    assert by_source["fallback"]["decoy_fp_rate"]["denominator"] == 6
    assert set(arm["by_company"]) == {"c1", "c2"}
    assert arm["by_company"]["c1"]["catch_rate"]["denominator"] == 9


def test_scenario_1_stability_and_insufficient_evidence(tmp_path):
    flipping = [
        {("dpdpa", 1): "compliant", ("iso27001", 1): "insufficient_evidence"},
        {("dpdpa", 1): "compliant", ("iso27001", 1): "insufficient_evidence"},
        {("dpdpa", 1): "non_compliant", ("iso27001", 1): "insufficient_evidence"},
    ]
    v2 = make_arm(tmp_path, "v2", settings=V2, caught=[True], outcomes_per_run=flipping)
    metrics = compare([f"v2={v2}"])[0]["arms"]["v2"]["metrics"]
    assert metrics["stability"] == {"value": pytest.approx((2 / 3 + 1 + 2 / 3 + 1) / 4), "requirements": 4}
    assert metrics["insufficient_evidence_rate"] == {"value": 0.5, "numerator": 6, "denominator": 12}


def test_scenario_1_cost(tmp_path):
    v2 = make_arm(tmp_path, "v2", settings=V2, caught=[True])
    cost = compare([f"v2={v2}"], price_in=1.0, price_out=2.0)[0]["arms"]["v2"]["cost"]
    assert cost["calls"] == 30 and cost["input_tokens"] == 9000 and cost["output_tokens"] == 3000
    assert cost["non_ok"] == 6 and cost["length"] == 6
    assert cost["stage_seconds"] == pytest.approx(90.0)
    assert cost["usd"] == pytest.approx((9000 * 1.0 + 3000 * 2.0) / 1_000_000)
    assert cost["per_run"]["input_tokens"] == pytest.approx(1500)
    assert cost["per_run"]["usd"] == pytest.approx(cost["usd"] / 6)
    assert compare([f"v2={v2}"])[0]["arms"]["v2"]["cost"]["usd"] is None


# --------------------------------------------------------------------------- #
# Scenario 2: the D-P6-E gate
# --------------------------------------------------------------------------- #


def test_scenario_2_gate_holds_on_ties_and_improvements(tmp_path):
    v1 = make_arm(tmp_path, "v1", settings=V1, caught=[True, False], decoy_fp=[True], clean_fp=[True, False])
    v2 = make_arm(tmp_path, "v2", settings=V2, caught=[True, True], decoy_fp=[True], clean_fp=[False, False])
    payload, markdown = compare([f"v1={v1}", f"v2={v2}"], baseline="v1")
    gate = payload["gate"]["v2"]
    assert gate["comparable"] is True and gate["reasons"] == []
    assert gate["catch_rate"] == {"baseline": 0.5, "arm": 1.0, "holds": True}
    assert gate["decoy_fp_rate"] == {"baseline": 1.0, "arm": 1.0, "holds": True}
    assert gate["clean_fp_rate"] == {"baseline": 0.5, "arm": 0.0, "holds": True}
    assert gate["stability"]["holds"] is True
    assert gate["cost_reported"] is True
    assert gate["holds"] is True
    assert set(payload["gate"]) == {"v2"}
    assert "Gate" in markdown and "v2" in markdown


@pytest.mark.parametrize(
    ("field", "v2_kwargs"),
    [
        ("catch_rate", {"caught": [True, False, False]}),
        ("decoy_fp_rate", {"caught": [True, True], "decoy_fp": [True]}),
        ("clean_fp_rate", {"caught": [True, True], "clean_fp": [True, True]}),
    ],
)
def test_scenario_2_gate_fails_on_any_regression(tmp_path, field, v2_kwargs):
    v1 = make_arm(tmp_path, "v1", settings=V1, caught=[True, True], decoy_fp=[False], clean_fp=[False, False])
    v2 = make_arm(tmp_path, "v2", settings=V2, **v2_kwargs)
    gate = compare([f"v1={v1}", f"v2={v2}"], baseline="v1")[0]["gate"]["v2"]
    assert gate[field]["holds"] is False
    assert gate["holds"] is False


def test_scenario_2_stability_regression_fails(tmp_path):
    v1 = make_arm(tmp_path, "v1", settings=V1, caught=[True])
    flipping = [STABLE, {("dpdpa", 1): "non_compliant", ("iso27001", 1): "non_compliant"}, STABLE]
    v2 = make_arm(tmp_path, "v2", settings=V2, caught=[True], outcomes_per_run=flipping)
    gate = compare([f"v1={v1}", f"v2={v2}"], baseline="v1")[0]["gate"]["v2"]
    assert gate["stability"]["holds"] is False and gate["holds"] is False


def test_scenario_2_missing_cost_blocks_the_gate(tmp_path):
    v1 = make_arm(tmp_path, "v1", settings=V1, caught=[True])
    v2 = make_arm(tmp_path, "v2", settings=V2, caught=[True], usage={})
    gate = compare([f"v1={v1}", f"v2={v2}"], baseline="v1")[0]["gate"]["v2"]
    assert gate["cost_reported"] is False and gate["holds"] is False


@pytest.mark.parametrize(
    ("reason", "v2_kwargs", "companies", "runs"),
    [
        ("stage_failures", {"stages_ok": False}, ("c1", "c2"), 3),
        ("failed_frameworks", {"failed_frameworks": ("iso27001",)}, ("c1", "c2"), 3),
        ("company_mismatch", {}, ("c1",), 3),
        ("run_count_mismatch", {}, ("c1", "c2"), 2),
        ("not_live", {"llm_mode": "mock"}, ("c1", "c2"), 3),
    ],
)
def test_scenario_2_incomparable_arms_have_no_verdict(tmp_path, reason, v2_kwargs, companies, runs):
    v1 = make_arm(tmp_path, "v1", settings=V1, caught=[True])
    v2 = make_arm(tmp_path, "v2", settings=V2, caught=[True], companies=companies, runs=runs, **v2_kwargs)
    gate = compare([f"v1={v1}", f"v2={v2}"], baseline="v1")[0]["gate"]["v2"]
    assert gate["comparable"] is False
    assert reason in gate["reasons"]
    assert gate["holds"] is None


# --------------------------------------------------------------------------- #
# Scenario 3: arm identity (the env must actually have reached the app)
# --------------------------------------------------------------------------- #


def test_scenario_3_declared_pipeline_is_used_only_when_nothing_is_recorded(tmp_path):
    v1 = make_arm(tmp_path, "v1", settings=None, caught=[True])
    arm = compare([f"v1={v1}:pipeline=v1"])[0]["arms"]["v1"]
    assert arm["pipeline"] == "v1" and arm["settings_source"] == "declared"
    assert arm["v2_missing_pass"] is None
    with pytest.raises(ValueError, match="pipeline"):
        compare([f"v1={v1}"])


def test_scenario_3_declared_and_recorded_must_agree(tmp_path):
    v2 = make_arm(tmp_path, "v2", settings=V1, caught=[True])
    with pytest.raises(ValueError, match="v2"):
        compare([f"v2={v2}:pipeline=v2"])


def test_scenario_3_mixed_settings_within_an_arm_are_refused(tmp_path):
    arm = make_arm(tmp_path, "arm", settings=V2, caught=[True], companies=("c1",))
    write_run(arm, "c2", 1, caught=[True], decoy_fp=[], clean_fp=[], outcomes=STABLE,
              settings={**V2, "v2_missing_pass": True})
    with pytest.raises(ValueError, match="mixed"):
        compare([f"arm={arm}"])


def test_scenario_3_v2_pack_version_must_match_the_criteria_map(tmp_path):
    v1 = make_arm(tmp_path, "v1", settings={**V1, "pack_versions": {"dpdpa": "2023"}}, caught=[True])
    v2 = make_arm(tmp_path, "v2", settings={**V2, "pack_versions": {"dpdpa": "2023", "iso27001": "2022"}},
                  caught=[True])
    payload = compare([f"v1={v1}", f"v2={v2}"], baseline="v1")[0]
    assert payload["gate"]["v2"]["comparable"] is False
    assert "pack_version_mismatch" in payload["gate"]["v2"]["reasons"]
    assert payload["arms"]["v2"]["v2_missing_pass"] is False


def test_scenario_3_bad_specs(tmp_path):
    with pytest.raises(ValueError):
        compare(["no-equals-sign"])
    with pytest.raises(ValueError):
        compare([f"x={tmp_path / 'missing'}"])
    v1 = make_arm(tmp_path, "v1", settings=V1, caught=[True])
    with pytest.raises(ValueError):
        compare([f"v1={v1}"], baseline="v9")
    with pytest.raises(ValueError):
        compare([f"v1={v1}", f"v1={v1}"])


# --------------------------------------------------------------------------- #
# Scenario 4: aggregate-only output and the CLI
# --------------------------------------------------------------------------- #


def test_scenario_4_output_never_carries_answer_key_content(tmp_path):
    v1 = make_arm(tmp_path, "v1", settings=V1, caught=[True, False, True], decoy_fp=[True])
    v2 = make_arm(tmp_path, "v2", settings=V2, caught=[True, True, False], decoy_fp=[False],
                  stages_ok=False)
    payload, markdown = compare([f"v1={v1}", f"v2={v2}"], baseline="v1", price_in=1.0, price_out=1.0)
    text = json.dumps(payload) + markdown
    for sentinel in SENTINELS:
        assert sentinel not in text, sentinel
    assert "SENTINELREQ" not in text


def test_scenario_4_cli_writes_both_files(tmp_path, monkeypatch):
    module = ab()
    v1 = make_arm(tmp_path, "v1", settings=V1, caught=[True])
    v2 = make_arm(tmp_path, "v2", settings=V2, caught=[True])
    monkeypatch.setattr(module, "default_criteria_source", lambda: source_of)
    monkeypatch.setattr(module, "default_pack_versions", lambda: dict(PACKS))
    out = tmp_path / "out"
    code = module.main(["--arm", f"v1={v1}", "--arm", f"v2={v2}", "--baseline", "v1",
                        "--price-in", "0.5", "--price-out", "1.5", "--out", str(out)])
    assert code == 0
    payload = json.loads((out / "ab_comparison.json").read_text())
    assert payload["gate"]["v2"]["holds"] is True
    assert (out / "ab_comparison.md").read_text().startswith("# P6-5 A/B comparison")
    assert module.main(["--arm", f"v1={v1}", "--baseline", "nope", "--out", str(out)]) == 2


def test_scenario_4_default_criteria_source_reads_the_registry():
    source = ab().default_criteria_source()
    assert source("dpdpa", "CH2.CONSENT.1") == "approved"
    versions = ab().default_pack_versions()
    assert versions["dpdpa"] == "2023+criteria-v1"
