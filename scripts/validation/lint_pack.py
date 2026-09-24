"""Validate pack schemas, registry references, fairness, and client-visible text."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from scripts.validation.models import (
    AnswerKey,
    CompanyMeta,
    EvidenceSpec,
    IntakeAnswers,
    QuestionnaireAnswers,
    validate_pack_relations,
)
from scripts.validation.paths import VALIDATION_ROOT, pack_dir

DENYLIST = (
    "answer key",
    "ground truth",
    "planted",
    "decoy",
    "hidden gap",
    "test company",
    "validation pack",
    "seeded gap",
)


@dataclass
class LintResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalized(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value)).strip().casefold()


def _tokens(value: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", value.casefold())


def _shingles(value: str, size: int = 8) -> set[tuple[str, ...]]:
    words = _tokens(value)
    return {tuple(words[index:index + size]) for index in range(max(0, len(words) - size + 1))}


def _framework_registry():
    import app.main  # noqa: F401
    from app.frameworks.registry import FrameworkRegistry

    app.main._register_frameworks()
    return FrameworkRegistry


def _coverage_warnings(slug: str, key: AnswerKey, result: LintResult) -> None:
    ranges = {
        "c1-": (10, 14, 2, 6),
        "c2-": (12, 16, 3, 8),
        "c3-": (12, 16, 4, 10),
        "c4-": (10, 14, 3, 8),
    }
    prefix = next((p for p in ranges if slug.startswith(p)), None)
    if prefix is None:
        return
    gap_min, gap_max, decoys, clean_min = ranges[prefix]
    if not gap_min <= len(key.planted_gaps) <= gap_max:
        result.warnings.append(f"gap count {len(key.planted_gaps)} outside expected range {gap_min}-{gap_max}")
    if len(key.decoys) != decoys:
        result.warnings.append(f"decoy count {len(key.decoys)} expected {decoys}")
    if len(key.clean_controls) < clean_min:
        result.warnings.append(f"clean-control count {len(key.clean_controls)} below {clean_min}")
    if prefix in {"c2-", "c3-", "c4-"}:
        classes = {gap.gap_class for gap in key.planted_gaps}
        if len(classes) < 5:
            result.warnings.append(f"only {len(classes)} distinct gap classes; at least 5 expected")


def lint_pack(
    slug: str,
    *,
    require_questionnaire: bool = False,
    validation_root: Path | None = None,
) -> LintResult:
    base = pack_dir(slug, validation_root)
    result = LintResult()
    parsed: dict[str, Any] = {}

    def parse(path: Path, model, label: str):
        try:
            value = model.model_validate(_read_json(path))
            parsed[label] = value
            return value
        except FileNotFoundError:
            result.errors.append(f"{path.relative_to(base)}: required file is missing")
        except (json.JSONDecodeError, ValidationError, ValueError) as exc:
            result.errors.append(f"{path.relative_to(base)}: {exc}")
        return None

    company = parse(base / "company.json", CompanyMeta, "company")
    intake_path = base / "client_visible" / "intake_answers.json"
    intake = parse(intake_path, IntakeAnswers, "intake")
    answers_path = base / "client_visible" / "questionnaire_answers.json"
    questionnaire = None
    if answers_path.exists():
        questionnaire = parse(answers_path, QuestionnaireAnswers, "questionnaire")
    elif require_questionnaire:
        result.errors.append("client_visible/questionnaire_answers.json: required by --require-questionnaire")

    evidence_specs: list[EvidenceSpec] = []
    evidence_dir = base / "client_visible" / "evidence"
    for path in sorted(evidence_dir.glob("*.json")):
        spec = parse(path, EvidenceSpec, f"evidence:{path.stem}")
        if spec is not None:
            evidence_specs.append(spec)
    try:
        answer_key = AnswerKey.model_validate(_read_json(base / "answer_key.json"))
        parsed["answer_key"] = answer_key
    except FileNotFoundError:
        answer_key = None
        result.errors.append("answer_key.json: required file is missing")
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        answer_key = None
        result.errors.append(f"answer_key.json: {exc}")

    if company and intake:
        try:
            validate_pack_relations(company, intake, evidence_specs, answer_key)
        except ValueError as exc:
            result.errors.append(f"cross-file schema: {exc}")
        if company.slug != slug:
            result.errors.append(f"company.json: slug {company.slug!r} does not match directory {slug!r}")
    if not answer_key:
        return result
    if answer_key.company_slug != slug:
        result.errors.append(f"answer_key.json: company_slug does not match directory {slug!r}")

    selected_frameworks = set(company.frameworks) if company else set()
    framework_ids = set(answer_key.control_truth)
    if framework_ids - selected_frameworks:
        result.errors.append(f"answer_key.json: control_truth includes unselected frameworks {sorted(framework_ids - selected_frameworks)}")

    try:
        registry = _framework_registry()
        valid_controls = {
            fw_id: {control.id for control in registry.get(fw_id).all_controls()}
            for fw_id in selected_frameworks
        }
    except Exception as exc:
        result.errors.append(f"framework registry unavailable: {exc}")
        valid_controls = {}

    def check_ref(framework_id: str, requirement_id: str, origin: str) -> None:
        known = valid_controls.get(framework_id)
        if known is None or requirement_id not in known:
            result.errors.append(f"{origin}: unknown control {framework_id}/{requirement_id}")

    for framework_id, truth in answer_key.control_truth.items():
        for requirement_id in truth.overrides:
            check_ref(framework_id, requirement_id, "answer_key.json control_truth")
    for gap in answer_key.planted_gaps:
        for ref in gap.requirements:
            check_ref(ref.framework_id, ref.requirement_id, f"answer_key.json {gap.gap_id}")
    for decoy in answer_key.decoys:
        for ref in decoy.requirements:
            check_ref(ref.framework_id, ref.requirement_id, f"answer_key.json {decoy.decoy_id}")
    for clean in answer_key.clean_controls:
        check_ref(clean.framework_id, clean.requirement_id, "answer_key.json clean_controls")
    for spec in evidence_specs:
        for ref in spec.consultant_maps_to:
            if company and ref.framework_id not in company.frameworks:
                result.errors.append(f"client_visible/evidence/{spec.artifact_id}.json: framework {ref.framework_id} is not selected")
            check_ref(ref.framework_id, ref.requirement_id, f"client_visible/evidence/{spec.artifact_id}.json consultant_maps_to")

    spec_by_id = {spec.artifact_id: spec for spec in evidence_specs}
    intake_pack_path = base / "question_pack.intake.json"
    qpack_path = base / "question_pack.questionnaire.json"
    intake_pack = _read_json(intake_pack_path) if intake_pack_path.exists() else {}
    qpack = _read_json(qpack_path) if qpack_path.exists() else {}
    if require_questionnaire and not qpack_path.is_file():
        result.errors.append("question_pack.questionnaire.json: required by --require-questionnaire")
    rendered_path = base / "rendered" / "manifest.json"
    manifest: dict = {}
    if rendered_path.is_file():
        try:
            manifest = _read_json(rendered_path)
        except (json.JSONDecodeError, OSError) as exc:
            result.errors.append(f"rendered/manifest.json: unreadable ({exc})")
    elif evidence_specs:
        result.errors.append("rendered/manifest.json: render_evidence must run before lint")
    for spec in evidence_specs:
        entry = manifest.get(spec.filename)
        rendered_file = base / "rendered" / spec.filename
        if not entry or not rendered_file.is_file():
            if evidence_specs:
                result.errors.append(f"rendered/{spec.filename}: missing from manifest or disk")
            continue
        current_sha = hashlib.sha256(rendered_file.read_bytes()).hexdigest()
        if entry.get("sha256") != current_sha:
            result.errors.append(f"rendered/{spec.filename}: manifest is stale; rerun render_evidence")

    questions = {
        question.get("id"): question
        for section in qpack.get("sections", [])
        for question in section.get("questions", [])
        if isinstance(question, dict) and question.get("id")
    }
    answer_map = questionnaire.answers if questionnaire else {}
    if require_questionnaire:
        for question_id, question in questions.items():
            if question.get("status") != "skipped" and question_id not in answer_map:
                result.errors.append(f"client_visible/questionnaire_answers.json: missing answer for {question_id}")
        for question_id in answer_map:
            if question_id not in questions:
                result.errors.append(f"client_visible/questionnaire_answers.json: answer_without_render {question_id}")
            elif questions[question_id].get("status") == "skipped":
                result.errors.append(f"client_visible/questionnaire_answers.json: skipped question has answer {question_id}")

    context_ids = {q.get("id") for q in intake_pack.get("context", [])}
    scope_ids = {q.get("id") for values in intake_pack.get("scope", {}).values() for q in values}
    if intake and intake_pack:
        unknown_context = set(intake.context) - context_ids
        if unknown_context:
            result.errors.append(f"client_visible/intake_answers.json: unknown context ids {sorted(unknown_context)}")
        selected_scope = set(company.frameworks if company else [])
        selected_scope_ids = {
            question.get("id")
            for framework_id, values in intake_pack.get("scope", {}).items()
            if framework_id in selected_scope
            for question in values
        }
        unknown_scope = set(intake.scope) - selected_scope_ids
        if unknown_scope:
            result.errors.append(f"client_visible/intake_answers.json: unknown or unselected scope ids {sorted(unknown_scope)}")
    for gap in answer_key.planted_gaps:
        for trail in gap.evidence_trail:
            try:
                source_type, source_id = trail.source.split(":", 1)
            except ValueError:
                result.errors.append(f"answer_key.json {gap.gap_id}: invalid trail source {trail.source!r}")
                continue
            client_text = ""
            if source_type == "evidence":
                spec = spec_by_id.get(source_id)
                if spec is None:
                    result.errors.append(f"answer_key.json {gap.gap_id}: missing trail artifact {source_id}")
                elif spec.render.kind == "external_image":
                    result.errors.append(f"answer_key.json {gap.gap_id}: trail cannot reference external_image {source_id}")
                else:
                    client_text = str(manifest.get(spec.filename, {}).get("text", ""))
            elif source_type == "answer":
                if source_id not in questions:
                    result.errors.append(f"answer_key.json {gap.gap_id}: unknown questionnaire question {source_id}")
                entry = answer_map.get(source_id)
                client_text = f"{entry.notes} {entry.evidence_reference}" if entry else ""
            elif source_type == "context":
                if source_id not in context_ids:
                    result.errors.append(f"answer_key.json {gap.gap_id}: unknown context question {source_id}")
                client_text = str((intake.context if intake else {}).get(source_id, ""))
            elif source_type == "scope":
                if source_id not in scope_ids:
                    result.errors.append(f"answer_key.json {gap.gap_id}: unknown scope question {source_id}")
                client_text = str((intake.scope if intake else {}).get(source_id, ""))
            else:
                result.errors.append(f"answer_key.json {gap.gap_id}: unsupported trail source type {source_type}")
            if require_questionnaire and source_type == "answer" and not entry:
                result.errors.append(f"answer_key.json {gap.gap_id}: missing answer trail source {source_id}")
        trail_texts = []
        for trail in gap.evidence_trail:
            if trail.source.startswith("evidence:"):
                artifact = spec_by_id.get(trail.source.split(":", 1)[1])
                if artifact:
                    trail_texts.append(str(manifest.get(artifact.filename, {}).get("text", "")))
            elif trail.source.startswith("answer:"):
                entry = answer_map.get(trail.source.split(":", 1)[1])
                if entry:
                    trail_texts.append(f"{entry.notes} {entry.evidence_reference}")
            elif trail.source.startswith("context:") and intake:
                trail_texts.append(str(intake.context.get(trail.source.split(":", 1)[1], "")))
            elif trail.source.startswith("scope:") and intake:
                trail_texts.append(str(intake.scope.get(trail.source.split(":", 1)[1], "")))
        for fact in gap.key_facts:
            normalized_fact = _normalized(fact)
            if not any(normalized_fact in _normalized(text) for text in trail_texts):
                result.errors.append(f"answer_key.json {gap.gap_id}: key fact is not verbatim in any trail source: {fact!r}")
    for decoy in answer_key.decoys:
        for trail in decoy.evidence_trail:
            if trail.source.startswith("evidence:"):
                artifact_id = trail.source.split(":", 1)[1]
                spec = spec_by_id.get(artifact_id)
                if spec is None:
                    result.errors.append(f"answer_key.json {decoy.decoy_id}: missing trail artifact {artifact_id}")
                elif spec.render.kind == "external_image":
                    result.errors.append(f"answer_key.json {decoy.decoy_id}: trail cannot reference external_image {artifact_id}")
            elif trail.source.startswith("answer:"):
                question_id = trail.source.split(":", 1)[1]
                if question_id not in questions:
                    result.errors.append(f"answer_key.json {decoy.decoy_id}: unknown questionnaire question {question_id}")
            elif trail.source.startswith("context:"):
                question_id = trail.source.split(":", 1)[1]
                if question_id not in context_ids:
                    result.errors.append(f"answer_key.json {decoy.decoy_id}: unknown context question {question_id}")
            elif trail.source.startswith("scope:"):
                question_id = trail.source.split(":", 1)[1]
                if question_id not in scope_ids:
                    result.errors.append(f"answer_key.json {decoy.decoy_id}: unknown scope question {question_id}")
    for control in answer_key.clean_controls:
        for artifact_id in control.supporting_artifacts:
            if artifact_id not in spec_by_id:
                result.errors.append(f"answer_key.json clean_controls: missing supporting artifact {artifact_id}")

    client_files: list[tuple[str, str]] = []
    for spec in evidence_specs:
        if spec.filename:
            client_files.append((f"client_visible/evidence/{spec.artifact_id}.json", spec.filename))
    for name, value in (("company.json", company.model_dump(mode="json") if company else {}),
                        ("client_visible/intake_answers.json", intake.model_dump(mode="json") if intake else {}),
                        ("client_visible/questionnaire_answers.json", questionnaire.model_dump(mode="json") if questionnaire else {})):
        if value:
            client_files.append((name, json.dumps(value, ensure_ascii=False)))
    for filename, entry in manifest.items():
        client_files.append((f"rendered/{filename}", str(entry.get("text", ""))))
    for spec in evidence_specs:
        if spec.render.kind == "external_image":
            client_files.append((f"client_visible/evidence/{spec.artifact_id}.json", spec.content.transcript))
    if intake:
        client_files.extend(("client_visible/intake_answers.json", item) for item in intake.magic_link_items)

    answer_key_texts = []
    for gap in answer_key.planted_gaps:
        answer_key_texts.append(gap.description)
    for decoy in answer_key.decoys:
        answer_key_texts.extend([decoy.why_it_looks_like_a_gap, decoy.why_it_is_compliant])
    answer_key_texts.append(answer_key.authoring_notes)
    key_shingles: set[tuple[str, ...]] = set()
    for text in answer_key_texts:
        key_shingles |= _shingles(text)

    for filename, text in client_files:
        norm = _normalized(text)
        for denied in DENYLIST:
            if denied in norm:
                result.errors.append(f"{filename}: leak term {denied!r} in {text[:160]!r}")
        match = re.search(r"\b[GD]\d{2}\b", text)
        if match:
            result.errors.append(f"{filename}: id leak {match.group(0)!r}")
        shared = _shingles(text) & key_shingles
        if shared:
            phrase = " ".join(sorted(shared)[0])
            result.errors.append(f"{filename}: answer-key shingle leak {phrase!r}")

    _coverage_warnings(slug, answer_key, result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug")
    parser.add_argument("--require-questionnaire", action="store_true")
    args = parser.parse_args(argv)
    try:
        root = Path(os.environ["CYBERASSESS_VALIDATION_ROOT"]) if os.environ.get("CYBERASSESS_VALIDATION_ROOT") else VALIDATION_ROOT
        result = lint_pack(args.slug, require_questionnaire=args.require_questionnaire, validation_root=root)
    except Exception as exc:
        print(f"lint failed: {exc}", file=sys.stderr)
        return 1
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    for error in result.errors:
        print(f"ERROR: {error}")
    print(f"{args.slug}: {len(result.errors)} error(s), {len(result.warnings)} warning(s)")
    return 1 if result.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
