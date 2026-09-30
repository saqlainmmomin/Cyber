"""Compare validation arms using aggregate-only, answer-key-independent data."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Callable


SCHEMA = "p6-5-ab.1"
_PIPELINES = {"v1", "v2"}


def default_criteria_source() -> Callable[[str, str], str]:
    """Return the comparison-commit criteria source classifier."""
    import app.main as application
    from app.frameworks.registry import FrameworkRegistry
    from app.services.grounding.judge import criteria_for

    application._register_frameworks()

    def source(framework_id: str, requirement_id: str) -> str:
        control = FrameworkRegistry.get(framework_id).get_control(requirement_id)
        return criteria_for(control)[0]

    return source


def default_pack_versions() -> dict[str, str]:
    """Return the pack versions registered by the comparison commit."""
    import app.main as application
    from app.frameworks.registry import FrameworkRegistry

    application._register_frameworks()
    return {framework_id: FrameworkRegistry.get(framework_id).pack_version for framework_id in FrameworkRegistry.all_ids()}


def _read(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _discover_runs(root: Path) -> list[Path]:
    return sorted(path.parent for path in root.glob("**/score.json") if (path.parent / "run.json").is_file())


def _parse_arm_spec(spec: str) -> tuple[str, Path, str | None]:
    name, separator, remainder = spec.partition("=")
    if not separator or not name.strip() or not remainder:
        raise ValueError(f"Invalid arm spec: {spec!r}")
    name = name.strip()
    declared = None
    marker = ":pipeline="
    if marker in remainder:
        path_text, declared = remainder.rsplit(marker, 1)
        if declared not in _PIPELINES or not path_text:
            raise ValueError(f"Invalid pipeline declaration for arm {name!r}")
    else:
        path_text = remainder
    root = Path(path_text).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"Arm directory does not exist: {root}")
    return name, root, declared


def _canonical_core_settings(settings: dict) -> tuple[str, bool]:
    pipeline = settings.get("analysis_pipeline_version")
    if pipeline not in _PIPELINES:
        raise ValueError("Recorded settings have an invalid analysis pipeline")
    missing_pass = settings.get("v2_missing_pass")
    if not isinstance(missing_pass, bool):
        raise ValueError("Recorded settings have an invalid v2_missing_pass")
    return pipeline, missing_pass


def _resolve_identity(records: list[dict], declared: str | None) -> tuple[str, str, bool | None, dict | None]:
    recorded = [record["meta"].get("settings") for record in records]
    has_settings = [settings is not None for settings in recorded]
    if any(has_settings) and not all(has_settings):
        raise ValueError("mixed settings within an arm")
    if not any(has_settings):
        if declared is None:
            raise ValueError("arm without recorded settings requires a declared pipeline")
        return declared, "declared", None, None

    cores = []
    for settings in recorded:
        if not isinstance(settings, dict):
            raise ValueError("mixed settings within an arm")
        cores.append(_canonical_core_settings(settings))
    if len(set(cores)) != 1:
        raise ValueError("mixed settings within an arm")
    pipeline, missing_pass = cores[0]
    if declared is not None and declared != pipeline:
        raise ValueError(f"declared pipeline {declared} disagrees with recorded {pipeline}")
    return pipeline, "recorded", missing_pass, recorded[0]


def _rate(numerator: int, denominator: int) -> dict:
    return {
        "value": numerator / denominator if denominator else None,
        "numerator": numerator,
        "denominator": denominator,
    }


def _count(value) -> int:
    if isinstance(value, (list, tuple, set, dict)):
        return len(value)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return int(value)
    return 0


def _has_missing_conclusions(score: dict) -> bool:
    return (
        any(
            requirement.get("outcome") == "missing"
            for gap in score.get("gap_results", [])
            for requirement in gap.get("requirements", [])
        )
        or any(
            requirement.get("outcome") == "missing"
            for decoy in score.get("decoy_results", [])
            for requirement in decoy.get("requirements", [])
        )
        or any(
            clean.get("outcome") == "missing"
            for clean in score.get("clean_control_results", [])
        )
    )


def _framework_bucket(requirements: list[dict]) -> str | None:
    framework_ids = {item.get("framework_id") for item in requirements if item.get("framework_id")}
    if not framework_ids:
        return None
    return next(iter(framework_ids)) if len(framework_ids) == 1 else "mixed"


def _source_bucket(requirements: list[dict], source_for: Callable[[str, str], str]) -> str | None:
    sources = {
        source_for(item["framework_id"], item["requirement_id"])
        for item in requirements
        if item.get("framework_id") and item.get("requirement_id")
    }
    if not sources:
        return None
    return next(iter(sources)) if len(sources) == 1 else "mixed"


def _new_bucket() -> dict:
    return {
        "gaps": [],
        "decoys": [],
        "clean": [],
        "conclusions": [],
        "prefilled": 0,
        "rendered": 0,
    }


def _add_item(bucket: dict, field: str, value) -> None:
    if field in bucket:
        bucket[field].append(value)


def _stability(entries: list[tuple[str, tuple[str, str], str]], company_counts: dict[str, int]) -> tuple[float | None, int]:
    grouped: dict[tuple[str, tuple[str, str]], list[str]] = defaultdict(list)
    for company, requirement, outcome in entries:
        grouped[(company, requirement)].append(outcome)
    shares = []
    for (company, _requirement), outcomes in grouped.items():
        if not outcomes:
            continue
        modal = Counter(outcomes).most_common(1)[0][1]
        denominator = company_counts.get(company, len(outcomes))
        shares.append(modal / denominator if denominator else 0.0)
    return (sum(shares) / len(shares) if shares else None, len(grouped))


def _bucket_metrics(bucket: dict, company_counts: dict[str, int], *, include_prefill: bool = False) -> dict:
    stability, requirement_count = _stability(bucket["conclusions"], company_counts)
    metrics = {
        "catch_rate": _rate(sum(bucket["gaps"]), len(bucket["gaps"])),
        "decoy_fp_rate": _rate(sum(bucket["decoys"]), len(bucket["decoys"])),
        "clean_fp_rate": _rate(sum(bucket["clean"]), len(bucket["clean"])),
        "stability": {"value": stability, "requirements": requirement_count},
    }
    outcomes = [outcome for _company, _requirement, outcome in bucket["conclusions"]]
    metrics["insufficient_evidence_rate"] = _rate(outcomes.count("insufficient_evidence"), len(outcomes))
    if include_prefill:
        metrics["prefill_rate"] = _rate(bucket["prefilled"], bucket["rendered"])
    return metrics


def _cost(records: list[dict], price_in: float | None, price_out: float | None) -> tuple[dict, bool]:
    totals = {"calls": 0, "input_tokens": 0, "output_tokens": 0, "non_ok": 0, "length": 0}
    stage_seconds = 0.0
    reported = True
    for record in records:
        cost = record["score"].get("cost")
        usage = cost.get("llm_usage") if isinstance(cost, dict) else None
        seconds = cost.get("stage_seconds") if isinstance(cost, dict) else None
        if not isinstance(usage, dict) or not usage or not isinstance(seconds, dict):
            reported = False
        if isinstance(usage, dict):
            for values in usage.values():
                if not isinstance(values, dict):
                    reported = False
                    continue
                for field in totals:
                    totals[field] += int(values.get(field) or 0)
        if isinstance(seconds, dict):
            stage_seconds += sum(float(value or 0) for value in seconds.values())
    usd = None
    if price_in is not None and price_out is not None:
        usd = (totals["input_tokens"] * price_in + totals["output_tokens"] * price_out) / 1_000_000
    run_count = len(records)
    per_run = {
        field: value / run_count if run_count else None
        for field, value in totals.items()
    }
    per_run["stage_seconds"] = stage_seconds / run_count if run_count else None
    per_run["usd"] = usd / run_count if usd is not None and run_count else None
    return {
        **totals,
        "stage_seconds": stage_seconds,
        "usd": usd,
        "per_run": per_run,
    }, reported


def _arm_record(name: str, root: Path, declared: str | None, source_for, expected_packs, price_in, price_out) -> dict:
    run_dirs = _discover_runs(root)
    if not run_dirs:
        raise ValueError(f"No scored runs found under {root}")
    records = []
    for run_dir in run_dirs:
        records.append({
            "dir": run_dir,
            "company": run_dir.parent.name,
            "meta": _read(run_dir / "run.json", {}),
            "score": _read(run_dir / "score.json", {}),
            "conclusions": _read(run_dir / "conclusions.json", {}),
            "questionnaire": _read(run_dir / "questionnaire_coverage.json", {}),
            "stages": _read(run_dir / "stages.json", []),
        })
    pipeline, settings_source, missing_pass, first_settings = _resolve_identity(records, declared)
    companies = Counter(record["company"] for record in records)
    company_counts = dict(companies)
    all_bucket = _new_bucket()
    framework_buckets: dict[str, dict] = {}
    source_buckets: dict[str, dict] = {}
    company_buckets: dict[str, dict] = {company: _new_bucket() for company in sorted(companies)}
    source_cache: dict[tuple[str, str], str] = {}

    def source_for_cached(framework_id: str, requirement_id: str) -> str:
        key = (framework_id, requirement_id)
        if key not in source_cache:
            source_cache[key] = source_for(framework_id, requirement_id)
        return source_cache[key]

    for record in records:
        company = record["company"]
        score = record["score"]
        for gap in score.get("gap_results", []):
            requirements = gap.get("requirements", [])
            caught = bool(gap.get("caught"))
            for bucket in (all_bucket, company_buckets[company]):
                bucket["gaps"].append(caught)
            for mapping, key_for in ((framework_buckets, _framework_bucket), (source_buckets, lambda refs: _source_bucket(refs, source_for_cached))):
                key = key_for(requirements)
                if key is not None:
                    mapping.setdefault(key, _new_bucket())["gaps"].append(caught)
        for decoy in score.get("decoy_results", []):
            requirements = decoy.get("requirements", [])
            false_positive = bool(decoy.get("false_positive"))
            for bucket in (all_bucket, company_buckets[company]):
                bucket["decoys"].append(false_positive)
            for mapping, key_for in ((framework_buckets, _framework_bucket), (source_buckets, lambda refs: _source_bucket(refs, source_for_cached))):
                key = key_for(requirements)
                if key is not None:
                    mapping.setdefault(key, _new_bucket())["decoys"].append(false_positive)
        for clean in score.get("clean_control_results", []):
            requirements = [{"framework_id": clean.get("framework_id"), "requirement_id": clean.get("requirement_id")}]
            false_positive = bool(clean.get("false_positive"))
            for bucket in (all_bucket, company_buckets[company]):
                bucket["clean"].append(false_positive)
            for mapping, key_for in ((framework_buckets, _framework_bucket), (source_buckets, lambda refs: _source_bucket(refs, source_for_cached))):
                key = key_for(requirements)
                if key is not None:
                    mapping.setdefault(key, _new_bucket())["clean"].append(false_positive)

        coverage = record["questionnaire"]
        prefilled = _count(coverage.get("prefilled_before_save"))
        rendered = _count(coverage.get("rendered_ids"))
        all_bucket["prefilled"] += prefilled
        all_bucket["rendered"] += rendered
        company_buckets[company]["prefilled"] += prefilled
        company_buckets[company]["rendered"] += rendered
        for item in record["conclusions"].get("conclusions", []):
            framework_id = item.get("framework_id")
            requirement_id = item.get("requirement_id")
            if not framework_id or not requirement_id:
                continue
            entry = (company, (framework_id, requirement_id), item.get("outcome", "missing"))
            all_bucket["conclusions"].append(entry)
            company_buckets[company]["conclusions"].append(entry)
            framework_buckets.setdefault(framework_id, _new_bucket())["conclusions"].append(entry)
            source_bucket = source_for_cached(framework_id, requirement_id)
            source_buckets.setdefault(source_bucket, _new_bucket())["conclusions"].append(entry)

    metrics = _bucket_metrics(all_bucket, company_counts, include_prefill=True)
    by_framework = {key: _bucket_metrics(bucket, company_counts) for key, bucket in sorted(framework_buckets.items())}
    by_source = {key: _bucket_metrics(bucket, company_counts) for key, bucket in sorted(source_buckets.items())}
    by_company = {key: _bucket_metrics(bucket, {key: company_counts[key]}, include_prefill=True) for key, bucket in sorted(company_buckets.items())}
    cost, cost_reported = _cost(records, price_in, price_out)

    stage_failures = sum(any(not bool(stage.get("ok")) for stage in record["stages"]) for record in records)
    failed_frameworks = sum(len(record["score"].get("coverage", {}).get("failed_frameworks", [])) for record in records)
    missing_conclusions = sum(
        not (record["dir"] / "conclusions.json").is_file()
        or not record["score"].get("coverage", {}).get("conclusions_count", 0)
        or _has_missing_conclusions(record["score"])
        for record in records
    )
    defects = {
        "stage_failures": stage_failures,
        "failed_frameworks": failed_frameworks,
        "missing_conclusions": missing_conclusions,
    }
    pack_mismatch = False
    if pipeline == "v2":
        if first_settings is None:
            pack_mismatch = True
        else:
            for record in records:
                settings = record["meta"].get("settings", {})
                packs = settings.get("pack_versions")
                if not isinstance(packs, dict) or not packs or any(expected_packs.get(fid) != version for fid, version in packs.items()):
                    pack_mismatch = True
                    break
    return {
        "path": str(root),
        "pipeline": pipeline,
        "settings_source": settings_source,
        "v2_missing_pass": missing_pass,
        "companies": dict(sorted(companies.items())),
        "runs": len(records),
        "llm_modes": sorted({record["meta"].get("llm_mode", "unknown") for record in records}),
        "defects": defects,
        "metrics": metrics,
        "by_framework": by_framework,
        "by_criteria_source": by_source,
        "by_company": by_company,
        "cost": cost,
        "_records": records,
        "_cost_reported": cost_reported,
        "_pack_mismatch": pack_mismatch,
    }


def _gate(baseline: dict, arm: dict) -> dict:
    reasons = []
    if baseline["defects"]["stage_failures"] or arm["defects"]["stage_failures"]:
        reasons.append("stage_failures")
    if baseline["defects"]["failed_frameworks"] or arm["defects"]["failed_frameworks"]:
        reasons.append("failed_frameworks")
    if baseline["defects"]["missing_conclusions"] or arm["defects"]["missing_conclusions"]:
        reasons.append("missing_conclusions")
    if set(baseline["companies"]) != set(arm["companies"]):
        reasons.append("company_mismatch")
    if (
        len(set(baseline["companies"].values())) > 1
        or len(set(arm["companies"].values())) > 1
        or any(baseline["companies"].get(company) != count for company, count in arm["companies"].items())
    ):
        reasons.append("run_count_mismatch")
    if any(mode != "live" for mode in baseline["llm_modes"] + arm["llm_modes"]):
        reasons.append("not_live")
    if arm["pipeline"] == "v2" and arm["_pack_mismatch"]:
        reasons.append("pack_version_mismatch")
    reasons = list(dict.fromkeys(reasons))

    def comparison(metric: str, *, higher_is_better: bool) -> dict:
        baseline_value = baseline["metrics"][metric]["value"]
        arm_value = arm["metrics"][metric]["value"]
        if baseline_value is None or arm_value is None:
            holds = None
        elif higher_is_better:
            holds = arm_value >= baseline_value
        else:
            holds = arm_value <= baseline_value
        return {"baseline": baseline_value, "arm": arm_value, "holds": holds}

    catch = comparison("catch_rate", higher_is_better=True)
    decoy = comparison("decoy_fp_rate", higher_is_better=False)
    clean = comparison("clean_fp_rate", higher_is_better=False)
    stability = comparison("stability", higher_is_better=True)
    cost_reported = bool(baseline["_cost_reported"] and arm["_cost_reported"])
    comparable = not reasons
    gated = [catch["holds"], decoy["holds"], clean["holds"], stability["holds"]]
    holds = None if not comparable else bool(cost_reported and catch["holds"] is not None and all(value is not False for value in gated))
    return {
        "comparable": comparable,
        "reasons": reasons,
        "catch_rate": catch,
        "decoy_fp_rate": decoy,
        "clean_fp_rate": clean,
        "stability": stability,
        "cost_reported": cost_reported,
        "holds": holds,
    }


def build_comparison(
    arm_specs: list[str],
    *,
    baseline: str | None = None,
    price_in: float | None = None,
    price_out: float | None = None,
    criteria_source=None,
    pack_versions=None,
) -> tuple[dict, str]:
    if not arm_specs:
        raise ValueError("At least one arm is required")
    if price_in is not None and price_in < 0 or price_out is not None and price_out < 0:
        raise ValueError("Prices must not be negative")
    source_for = criteria_source if criteria_source is not None else default_criteria_source()
    expected_packs = dict(pack_versions if pack_versions is not None else default_pack_versions())
    arms = {}
    for spec in arm_specs:
        name, root, declared = _parse_arm_spec(spec)
        if name in arms:
            raise ValueError(f"Duplicate arm name: {name}")
        arms[name] = _arm_record(name, root, declared, source_for, expected_packs, price_in, price_out)
    if baseline is not None and baseline not in arms:
        raise ValueError(f"Unknown baseline arm: {baseline}")
    gate = {}
    if baseline is not None:
        for name, arm in arms.items():
            if name != baseline:
                gate[name] = _gate(arms[baseline], arm)
    payload_arms = {}
    for name, arm in arms.items():
        payload_arms[name] = {key: value for key, value in arm.items() if not key.startswith("_")}
    payload = {"schema": SCHEMA, "baseline": baseline, "arms": payload_arms, "gate": gate}
    return payload, render_markdown(payload)


def _fmt_rate(value) -> str:
    return "n/a" if value is None else f"{value:.1%}"


def render_markdown(payload: dict) -> str:
    lines = ["# P6-5 A/B comparison", "", f"Baseline: `{payload.get('baseline') or 'none'}`", "", "## Arms", "", "| Arm | Pipeline | Runs | Catch | Decoy FP | Clean FP | Stability | IE | Cost USD |", "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for name, arm in payload["arms"].items():
        metrics = arm["metrics"]
        lines.append(
            f"| {name} | {arm['pipeline']} | {arm['runs']} | {_fmt_rate(metrics['catch_rate']['value'])} | "
            f"{_fmt_rate(metrics['decoy_fp_rate']['value'])} | {_fmt_rate(metrics['clean_fp_rate']['value'])} | "
            f"{_fmt_rate(metrics['stability']['value'])} | {_fmt_rate(metrics['insufficient_evidence_rate']['value'])} | "
            f"{arm['cost']['usd'] if arm['cost']['usd'] is not None else 'n/a'} |"
        )
    lines.extend(["", "## Gate", ""])
    if not payload["gate"]:
        lines.append("No baseline gate requested.")
    else:
        lines.extend(["| Arm | Comparable | Reasons | Catch | Decoy FP | Clean FP | Stability | Cost reported | Holds |", "|---|---|---|---|---|---|---|---|---|"])
        for name, gate in payload["gate"].items():
            lines.append(
                f"| {name} | {str(gate['comparable']).lower()} | {', '.join(gate['reasons']) or 'none'} | "
                f"{str(gate['catch_rate']['holds']).lower()} | {str(gate['decoy_fp_rate']['holds']).lower()} | "
                f"{str(gate['clean_fp_rate']['holds']).lower()} | {str(gate['stability']['holds']).lower()} | "
                f"{str(gate['cost_reported']).lower()} | {str(gate['holds']).lower()} |"
            )
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", action="append", required=True)
    parser.add_argument("--baseline")
    parser.add_argument("--price-in", type=float)
    parser.add_argument("--price-out", type=float)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        payload, markdown = build_comparison(
            args.arm,
            baseline=args.baseline,
            price_in=args.price_in,
            price_out=args.price_out,
        )
    except ValueError as exc:
        print(f"ab_compare failed: {exc}", file=sys.stderr)
        return 2
    root = args.out.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    (root / "ab_comparison.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (root / "ab_comparison.md").write_text(markdown, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
