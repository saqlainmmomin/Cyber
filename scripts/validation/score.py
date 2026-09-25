"""Score a completed validation run deterministically against its held-out pack."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from scripts.validation.models import AnswerKey
from scripts.validation.paths import VALIDATION_ROOT

DISTANCE = {
    "non_compliant": {
        "non_compliant": 1.0,
        "partially_compliant": 0.5,
        "insufficient_evidence": 0.3,
        "compliant": 0.0,
        "not_applicable": 0.0,
        "missing": 0.0,
    },
    "partially_compliant": {
        "non_compliant": 0.7,
        "partially_compliant": 1.0,
        "insufficient_evidence": 0.3,
        "compliant": 0.0,
        "not_applicable": 0.0,
        "missing": 0.0,
    },
}
NEGATIVE = {"non_compliant", "partially_compliant"}


def _read(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _norm(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _outcome_map(conclusions: dict) -> dict[tuple[str, str], dict]:
    return {
        (item["framework_id"], item["requirement_id"]): item
        for item in conclusions.get("conclusions", [])
    }


def _risk_score(expected: str, actual: str) -> float:
    order = {"low": 0, "medium": 1, "high": 2}
    if actual not in order:
        return 0.0
    distance = abs(order[expected] - order[actual])
    return 1.0 if distance == 0 else 0.5 if distance == 1 else 0.0


def score_run(run_dir: Path | str, *, validation_root: Path | None = None) -> dict:
    run_dir = Path(run_dir).resolve()
    slug = run_dir.parent.name
    validation_root = validation_root or VALIDATION_ROOT
    pack = validation_root / "companies" / slug
    key = AnswerKey.model_validate_json((pack / "answer_key.json").read_text(encoding="utf-8"))
    conclusions = _read(run_dir / "conclusions.json", {})
    run_meta = _read(run_dir / "run.json", {})
    outcome_map = _outcome_map(conclusions)
    app_requirements = conclusions.get("assessment", {}).get("applicable_requirements")
    selected = run_meta.get("frameworks", [])

    all_controls: list[tuple[str, str]] = []
    if app_requirements:
        selected_set = set(app_requirements)
    else:
        selected_set = None
    if selected:
        try:
            import app.main  # noqa: F401
            from app.frameworks.registry import FrameworkRegistry

            for framework_id in selected:
                for control in FrameworkRegistry.get(framework_id).all_controls():
                    ref = (framework_id, control.id)
                    if selected_set is None or control.id in selected_set:
                        all_controls.append(ref)
        except Exception:
            all_controls = list(outcome_map)
    else:
        all_controls = list(outcome_map)

    req_to_gaps: dict[tuple[str, str], set[str]] = defaultdict(set)
    req_to_decoys: dict[tuple[str, str], set[str]] = defaultdict(set)
    req_to_clean: set[tuple[str, str]] = set()
    gap_results = []
    all_req_scores: list[float] = []
    for gap in key.planted_gaps:
        req_scores = []
        scored_refs = []
        for ref in gap.requirements:
            pair = (ref.framework_id, ref.requirement_id)
            req_to_gaps[pair].add(gap.gap_id)
            conclusion = outcome_map.get(pair)
            outcome = conclusion["outcome"] if conclusion else "missing"
            score = DISTANCE[gap.actual_status][outcome]
            req_scores.append(score)
            all_req_scores.append(score)
            scored_refs.append({"framework_id": pair[0], "requirement_id": pair[1], "outcome": outcome, "score": score})
        filename_by_artifact = {}
        evidence_dir = pack / "client_visible" / "evidence"
        for path in evidence_dir.glob("*.json"):
            try:
                item = json.loads(path.read_text(encoding="utf-8"))
                filename_by_artifact[item["artifact_id"]] = item["filename"]
            except (OSError, KeyError, json.JSONDecodeError):
                continue
        evidence_filenames = {
            filename_by_artifact[trail.source.split(":", 1)[1]]
            for trail in gap.evidence_trail
            if trail.source.startswith("evidence:") and trail.source.split(":", 1)[1] in filename_by_artifact
        }
        grounded_refs = []
        fact_texts = []
        severity_scores = []
        for ref, score in zip(gap.requirements, req_scores):
            conclusion = outcome_map.get((ref.framework_id, ref.requirement_id))
            if not conclusion:
                continue
            fact_texts.append(" ".join(str(conclusion.get(field) or "") for field in ("rationale", "gaps_identified", "evidence_summary")))
            if score >= 0.7:
                filenames = {citation.get("filename") for citation in conclusion.get("citations", [])}
                grounded_refs.append(bool(filenames & evidence_filenames))
                severity_scores.append(_risk_score(gap.severity_expected, conclusion.get("risk_level", "")))
        combined_text = _norm(" ".join(fact_texts))
        recall = sum(_norm(fact) in combined_text for fact in gap.key_facts) / len(gap.key_facts) if gap.key_facts else None
        gap_results.append({
            "gap_id": gap.gap_id,
            "gap_class": gap.gap_class,
            "probing_depth": gap.probing_depth,
            "description": gap.description,
            "requirements": scored_refs,
            "req_scores": req_scores,
            "gap_score": _mean(req_scores) or 0.0,
            "caught": max(req_scores, default=0.0) >= 0.7,
            "grounded": any(grounded_refs) if evidence_filenames and grounded_refs else (False if evidence_filenames and any(score >= 0.7 for score in req_scores) else None),
            "key_fact_recall": recall,
            "severity": _mean(severity_scores),
            "key_facts": gap.key_facts,
        })

    decoy_results = []
    for decoy in key.decoys:
        refs = []
        for ref in decoy.requirements:
            pair = (ref.framework_id, ref.requirement_id)
            req_to_decoys[pair].add(decoy.decoy_id)
            conclusion = outcome_map.get(pair)
            refs.append({"framework_id": pair[0], "requirement_id": pair[1], "outcome": conclusion["outcome"] if conclusion else "missing"})
        decoy_results.append({"decoy_id": decoy.decoy_id, "requirements": refs, "false_positive": any(ref["outcome"] in NEGATIVE for ref in refs)})
    clean_results = []
    for control in key.clean_controls:
        pair = (control.framework_id, control.requirement_id)
        req_to_clean.add(pair)
        conclusion = outcome_map.get(pair)
        outcome = conclusion["outcome"] if conclusion else "missing"
        clean_results.append({"framework_id": pair[0], "requirement_id": pair[1], "outcome": outcome, "false_positive": outcome in NEGATIVE})

    applicable = all_controls
    covered = [pair for pair in applicable if pair in outcome_map]
    missing = [f"{fw}/{req}" for fw, req in applicable if (fw, req) not in outcome_map]
    analysis_runs = conclusions.get("analysis_runs", [])
    failed_frameworks = [row.get("framework_id") for row in analysis_runs if row.get("status") != "completed"]
    excluded = set(req_to_gaps) | set(req_to_decoys) | req_to_clean
    backgrounds = []
    for fw, req in applicable:
        pair = (fw, req)
        if pair in excluded or pair not in outcome_map:
            continue
        truth = key.control_truth.get(fw)
        expected = truth.overrides.get(req, truth.default) if truth else None
        backgrounds.append(outcome_map[pair]["outcome"] == expected)

    gap_scores = [item["gap_score"] for item in gap_results]
    caught = [item["caught"] for item in gap_results]
    classes: dict[str, list[bool]] = defaultdict(list)
    depths: dict[str, list[bool]] = defaultdict(list)
    for gap in gap_results:
        classes[gap["gap_class"]].append(gap["caught"])
        depths[str(gap["probing_depth"])].append(gap["caught"])
    llm_rows = []
    usage_path = run_dir / "llm_usage.jsonl"
    if usage_path.exists():
        for line in usage_path.read_text(encoding="utf-8").splitlines():
            try:
                llm_rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    costs = defaultdict(lambda: {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0})
    for row in llm_rows:
        target = costs[f"{row.get('tier', 'unknown')} / {row.get('model', 'unknown')}"]
        target["calls"] += 1
        for field in ("input_tokens", "output_tokens", "cache_read_input_tokens"):
            target[field] += int(row.get(field) or 0)
    stages = _read(run_dir / "stages.json", [])
    score = {
        "slug": slug,
        "run_dir": str(run_dir),
        "gap_results": gap_results,
        "decoy_results": decoy_results,
        "clean_control_results": clean_results,
        "coverage": {
            "applicable_count": len(applicable),
            "conclusions_count": len(covered),
            "missing": missing,
            "failed_frameworks": failed_frameworks,
        },
        "background_agreement": _mean([1.0 if value else 0.0 for value in backgrounds]),
        "aggregates": {
            "catch_rate": _mean([1.0 if value else 0.0 for value in caught]),
            "catch_rate_by_gap_class": {name: _mean([1.0 if value else 0.0 for value in values]) for name, values in classes.items()},
            "catch_rate_by_probing_depth": {name: _mean([1.0 if value else 0.0 for value in values]) for name, values in depths.items()},
            "mean_gap_score": _mean(gap_scores),
            "grounding_rate": _mean([1.0 if item["grounded"] else 0.0 for item in gap_results if item["grounded"] is not None]),
            "mean_key_fact_recall": _mean([item["key_fact_recall"] for item in gap_results if item["key_fact_recall"] is not None]),
            "mean_severity": _mean([item["severity"] for item in gap_results if item["severity"] is not None]),
            "decoy_fp_rate": _mean([1.0 if item["false_positive"] else 0.0 for item in decoy_results]),
            "clean_fp_rate": _mean([1.0 if item["false_positive"] else 0.0 for item in clean_results]),
            "background_agreement": _mean([1.0 if value else 0.0 for value in backgrounds]),
        },
        "cost": {"llm_usage": dict(costs), "stage_seconds": {stage["stage"]: stage.get("elapsed_s", 0) for stage in stages}},
    }
    output = run_dir / "score.json"
    output.write_text(json.dumps(score, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return score


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dirs", nargs="+")
    args = parser.parse_args(argv)
    try:
        for directory in args.run_dirs:
            result = score_run(directory)
            print(f"Scored {result['slug']}: {result['aggregates']['catch_rate']}")
    except Exception as exc:
        print(f"score failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
