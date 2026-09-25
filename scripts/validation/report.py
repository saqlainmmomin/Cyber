"""Create a shareable cross-company summary from scored run directories."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from scripts.validation.paths import REPO_ROOT


def _read(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _mean(values):
    return sum(values) / len(values) if values else None


def _fmt(value):
    return "n/a" if value is None else f"{value:.1%}"


def _git_info() -> tuple[str, bool]:
    try:
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.strip())
        return sha, dirty
    except (OSError, subprocess.CalledProcessError):
        return "unknown", True


def _discover_runs(out_dir: Path) -> list[Path]:
    return sorted(path.parent for path in out_dir.glob("**/score.json") if (path.parent / "run.json").exists())


def _summary_for_company(slug: str, run_dirs: list[Path]) -> dict:
    run_rows = []
    for run_dir in run_dirs:
        run_rows.append({
            "run_dir": str(run_dir),
            "meta": _read(run_dir / "run.json", {}),
            "score": _read(run_dir / "score.json", {}),
            "questionnaire_coverage": _read(run_dir / "questionnaire_coverage.json", {}),
            "probes": _read(run_dir / "probes.json", []),
            "stages": _read(run_dir / "stages.json", []),
            "conclusions": _read(run_dir / "conclusions.json", {}),
        })
    scores = [row["score"] for row in run_rows]
    gaps_by_id: dict[str, list[dict]] = defaultdict(list)
    outcomes_by_req: dict[str, list[str]] = defaultdict(list)
    for row in run_rows:
        for gap in row["score"].get("gap_results", []):
            gaps_by_id[gap["gap_id"]].append(gap)
        for item in row["conclusions"].get("conclusions", []):
            key = f"{item.get('framework_id')}/{item.get('requirement_id')}"
            outcomes_by_req[key].append(item.get("outcome", "missing"))
    gap_rows = []
    for gap_id, values in sorted(gaps_by_id.items()):
        first = values[0]
        grounding = [value["grounded"] for value in values if value.get("grounded") is not None]
        recalls = [value["key_fact_recall"] for value in values if value.get("key_fact_recall") is not None]
        gap_rows.append({
            "gap_id": gap_id,
            "gap_class": first.get("gap_class"),
            "probing_depth": first.get("probing_depth"),
            "caught_runs": sum(bool(value.get("caught")) for value in values),
            "run_count": len(values),
            "mean_gap_score": _mean([value.get("gap_score", 0) for value in values]),
            "grounded_rate": _mean([1.0 if value else 0.0 for value in grounding]),
            "key_facts": first.get("key_facts", []),
            "description": first.get("description", ""),
        })
    changed = sorted(key for key, outcomes in outcomes_by_req.items() if len(set(outcomes)) > 1)
    modal_agreement = [Counter(outcomes).most_common(1)[0][1] / len(outcomes) for outcomes in outcomes_by_req.values() if outcomes]
    class_values: dict[str, list[bool]] = defaultdict(list)
    for gap in gap_rows:
        class_values[gap["gap_class"]].append(gap["caught_runs"] == gap["run_count"])
    coverage = [score.get("coverage", {}) for score in scores]
    result = {
        "slug": slug,
        "run_count": len(run_rows),
        "runs": run_rows,
        "headline": {
            "catch_rate": _mean([score.get("aggregates", {}).get("catch_rate") for score in scores if score.get("aggregates", {}).get("catch_rate") is not None]),
            "decoy_fp_rate": _mean([score.get("aggregates", {}).get("decoy_fp_rate") for score in scores if score.get("aggregates", {}).get("decoy_fp_rate") is not None]),
            "clean_fp_rate": _mean([score.get("aggregates", {}).get("clean_fp_rate") for score in scores if score.get("aggregates", {}).get("clean_fp_rate") is not None]),
        },
        "gap_class_catch_rate": {
            name: _mean([score.get("aggregates", {}).get("catch_rate_by_gap_class", {}).get(name) for score in scores if score.get("aggregates", {}).get("catch_rate_by_gap_class", {}).get(name) is not None])
            for name in sorted({gap.get("gap_class") for score in scores for gap in score.get("gap_results", [])})
        },
        "gaps": gap_rows,
        "decoys": [item for score in scores for item in score.get("decoy_results", [])],
        "stability": {
            "per_requirement_modal_agreement": _mean(modal_agreement),
            "changed_requirements": changed,
        },
        "coverage": coverage,
        "questionnaire_coverage": [row["questionnaire_coverage"] for row in run_rows],
        "format_probes": [probe for row in run_rows for probe in row["probes"]],
        "cost": [score.get("cost", {}) for score in scores],
    }
    return result


def build_report(out_dir: Path | str, *, baseline: bool = False) -> tuple[dict, str]:
    out_dir = Path(out_dir).expanduser().resolve()
    run_dirs = _discover_runs(out_dir)
    if not run_dirs:
        raise ValueError(f"No scored runs found under {out_dir}")
    run_meta = [_read(path / "run.json", {}) for path in run_dirs]
    modes = {meta.get("llm_mode", "unknown") for meta in run_meta}
    if baseline and modes != {"live"}:
        raise ValueError("--baseline requires every run to use the live LLM")
    stamp = "BASELINE" if baseline else "MOCK" if modes == {"mock"} else "SMOKE"
    sha, dirty = _git_info()
    try:
        from app.config import settings

        model_ids = {
            "extract": settings.llm_model_extract,
            "judge": settings.llm_model_judge,
            "synthesize": settings.llm_model_synthesize,
            "vision": settings.llm_model_vision,
        }
    except Exception:
        model_ids = {}
    grouped: dict[str, list[Path]] = defaultdict(list)
    for path in run_dirs:
        grouped[path.parent.name].append(path)
    companies = [_summary_for_company(slug, grouped[slug]) for slug in sorted(grouped)]
    all_gaps = [gap for company in companies for gap in company["gaps"]]
    all_decoys = [decoy for company in companies for decoy in company["decoys"]]
    all_clean = [item for company in companies for row in company["runs"] for item in row["score"].get("clean_control_results", [])]
    total_caught = sum(gap["caught_runs"] for gap in all_gaps)
    total_attempts = sum(gap["run_count"] for gap in all_gaps)
    defects = []
    for company in companies:
        for row in company["runs"]:
            run_label = f"{company['slug']}/{Path(row['run_dir']).name}"
            for stage in row["stages"]:
                if not stage.get("ok"):
                    defects.append({"run": run_label, "type": "stage_failure", "stage": stage.get("stage"), "detail": stage.get("detail")})
            for framework_id in row["score"].get("coverage", {}).get("failed_frameworks", []):
                defects.append({"run": run_label, "type": "failed_framework", "framework_id": framework_id})
            qcoverage = row["questionnaire_coverage"]
            if qcoverage.get("rendered_without_answer"):
                defects.append({"run": run_label, "type": "rendered_without_answer", "ids": qcoverage["rendered_without_answer"]})
            if qcoverage.get("answer_without_render"):
                defects.append({"run": run_label, "type": "answer_without_render", "ids": qcoverage["answer_without_render"]})
            for probe in row["probes"]:
                status = probe.get("status_code")
                if status is not None and not 200 <= status < 300:
                    defects.append({"run": run_label, "type": "rejected_probe", "format": probe.get("format"), "status": status})
            if not (Path(row["run_dir"]) / "conclusions.json").is_file() or not row["score"].get("coverage", {}).get("conclusions_count"):
                defects.append({"run": run_label, "type": "missing_conclusions"})

    payload = {
        "stamp": stamp,
        "git_sha": sha,
        "dirty": dirty,
        "date": datetime.now(timezone.utc).date().isoformat(),
        "model_ids": model_ids,
        "companies": companies,
        "cross_company": {
            "gap_catch_rate": total_caught / total_attempts if total_attempts else None,
            "decoy_fp_rate": _mean([1.0 if item.get("false_positive") else 0.0 for item in all_decoys]),
            "clean_fp_rate": _mean([1.0 if item.get("false_positive") else 0.0 for item in all_clean]),
            "gaps_caught": total_caught,
            "gap_run_attempts": total_attempts,
            "decoys": len(all_decoys),
            "clean_controls": len(all_clean),
        },
        "defects_to_file": defects,
    }

    lines = [
        f"# Validation summary — {stamp}",
        "",
        f"Date: {payload['date']}  ",
        f"Git: `{sha}` (dirty: `{str(dirty).lower()}`)  ",
        f"Models: `{json.dumps(model_ids, sort_keys=True)}`",
        "",
        "## Headline by company",
        "",
        "| Company | Catch rate | Decoy false positives | Clean-control false positives |",
        "|---|---:|---:|---:|",
    ]
    for company in companies:
        head = company["headline"]
        lines.append(f"| {company['slug']} | {_fmt(head['catch_rate'])} | {_fmt(head['decoy_fp_rate'])} | {_fmt(head['clean_fp_rate'])} |")
    totals = payload["cross_company"]
    lines.extend([
        f"| **All companies** | {_fmt(totals['gap_catch_rate'])} | {_fmt(totals['decoy_fp_rate'])} | {_fmt(totals['clean_fp_rate'])} |",
        "",
        "## Gap classes",
        "",
    ])
    for company in companies:
        lines.extend([f"### {company['slug']}", "", "| Gap class | Catch rate |", "|---|---:|"])
        for gap_class, rate in company["gap_class_catch_rate"].items():
            lines.append(f"| {gap_class} | {_fmt(rate)} |")
        lines.extend(["", "| Gap | Class | Depth | Caught | Mean score | Grounded | Key facts |", "|---|---|---:|---:|---:|---:|---|"])
        for gap in company["gaps"]:
            lines.append(f"| {gap['gap_id']} | {gap['gap_class']} | {gap['probing_depth']} | {gap['caught_runs']}/{gap['run_count']} | {_fmt(gap['mean_gap_score'])} | {_fmt(gap['grounded_rate'])} | {'; '.join(gap['key_facts'])} |")
        lines.extend(["", "Decoys: " + (", ".join(f"{d['decoy_id']} false_positive={d['false_positive']}" for d in company["decoys"]) or "none"), ""])
        lines.append(f"Stability: modal agreement {_fmt(company['stability']['per_requirement_modal_agreement'])}; changed requirements: {', '.join(company['stability']['changed_requirements']) or 'none'}.")
        lines.append("")
        lines.extend(["Run diagnostics", ""])
        for run in company["runs"]:
            run_name = Path(run["run_dir"]).name
            qcoverage = run["questionnaire_coverage"]
            rendered = qcoverage.get("rendered_ids", [])
            answered = qcoverage.get("answered", [])
            prefilled = qcoverage.get("prefilled_before_save", [])
            provenance = qcoverage.get("provenance_after_save", {})
            lines.append(
                f"- `{run_name}` questionnaire: {len(answered)}/{len(rendered)} answered; "
                f"rendered without answer: {', '.join(qcoverage.get('rendered_without_answer', [])) or 'none'}; "
                f"answer without render: {', '.join(qcoverage.get('answer_without_render', [])) or 'none'}; "
                f"prefilled before save: {len(prefilled)}; provenance after save: `{json.dumps(provenance, sort_keys=True)}`."
            )
            probe_text = []
            for probe in run["probes"]:
                status = probe.get("status_code")
                result = f"{probe.get('format')}: {'skipped' if status is None else status}"
                if probe.get("archive_status_code") is not None:
                    result += f", archive {probe['archive_status_code']}"
                probe_text.append(result)
            lines.append(f"  Format probes: {'; '.join(probe_text) or 'none'}.")
            usage = run["score"].get("cost", {}).get("llm_usage", {})
            if usage:
                usage_text = "; ".join(
                    f"{name}: {values.get('calls', 0)} calls, {values.get('input_tokens', 0)} input / {values.get('output_tokens', 0)} output tokens"
                    for name, values in sorted(usage.items())
                )
            else:
                usage_text = "no recorded LLM calls"
            stage_seconds = sum(run["score"].get("cost", {}).get("stage_seconds", {}).values())
            lines.append(f"  Cost: {usage_text}; total stage time {stage_seconds:.2f}s.")
        lines.append("")
    lines.extend(["## Defects to file", ""])
    if defects:
        for defect in defects:
            compact = {key: value for key, value in defect.items() if key != "detail"}
            lines.append(f"- {json.dumps(compact, sort_keys=True)}")
    else:
        lines.append("- None mechanically detected.")
    lines.append("")
    markdown = "\n".join(lines)
    return payload, markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out_dir", type=Path)
    parser.add_argument("--baseline", action="store_true")
    args = parser.parse_args(argv)
    try:
        payload, markdown = build_report(args.out_dir, baseline=args.baseline)
    except Exception as exc:
        print(f"report failed: {exc}", file=sys.stderr)
        return 1
    root = args.out_dir.expanduser().resolve()
    (root / "summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (root / "summary.md").write_text(markdown, encoding="utf-8")
    print(f"Wrote {root / 'summary.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
