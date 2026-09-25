from __future__ import annotations

import builtins
import json
import shutil
import subprocess
from pathlib import Path

import pytest
from PIL import Image
from pydantic import ValidationError

from scripts.validation.export_question_pack import _member_controls, export_question_pack
from scripts.validation.lint_pack import lint_pack
from scripts.validation.models import AnswerKey, EvidenceSpec
from scripts.validation.paths import REPO_ROOT, VALIDATION_ROOT
from scripts.validation.render_evidence import render_pack
from scripts.validation.report import build_report
from scripts.validation.run_company import run_company
from scripts.validation.score import score_run

EXAMPLE = VALIDATION_ROOT / "companies" / "c0-example"


def test_export_maps_builder_control_ids_to_framework_refs():
    question = {
        "maps_to": ["ISO.A5.1", "NIST.ID.AM-1"],
        "frameworks_covered": ["iso27001", "nist_csf"],
    }
    control_ids = {
        "iso27001": {"ISO.A5.1"},
        "nist_csf": {"NIST.ID.AM-1"},
        "dpdpa": {"CH2.NOTICE.1"},
    }
    assert _member_controls(question, control_ids, ["dpdpa", "iso27001", "nist_csf"]) == [
        {"framework_id": "iso27001", "requirement_id": "ISO.A5.1"},
        {"framework_id": "nist_csf", "requirement_id": "NIST.ID.AM-1"},
    ]


def test_export_normalises_builder_member_controls_shape():
    control_ids = {"dpdpa": {"CH2.CONSENT.1"}, "iso27001": {"ISO.A5.34"}}
    question = {
        "id": "CH2.CONSENT.1",
        "maps_to": ["CH2.CONSENT.1", "ISO.A5.34"],
        "frameworks_covered": ["dpdpa", "iso27001"],
        "member_controls": [
            {"framework_id": "dpdpa", "control_id": "CH2.CONSENT.1"},
            {"framework_id": "iso27001", "control_id": "ISO.A5.34"},
            {"framework_id": "iso27001", "control_id": "ISO.A5.34"},
        ],
    }
    assert _member_controls(question, control_ids, ["dpdpa", "iso27001"]) == [
        {"framework_id": "dpdpa", "requirement_id": "CH2.CONSENT.1"},
        {"framework_id": "iso27001", "requirement_id": "ISO.A5.34"},
    ]
    assert _member_controls(
        {"id": "legacy", "member_controls": [{"framework_id": "dpdpa", "requirement_id": "CH2.CONSENT.1"}]},
        control_ids,
        ["dpdpa"],
    ) == [{"framework_id": "dpdpa", "requirement_id": "CH2.CONSENT.1"}]
    assert _member_controls(
        {"id": "controls", "controls": [{"framework_id": "iso27001", "control_id": "ISO.A5.34"}]},
        control_ids,
        ["iso27001"],
    ) == [{"framework_id": "iso27001", "requirement_id": "ISO.A5.34"}]
    with pytest.raises(ValueError, match="CH2.CONSENT.1"):
        _member_controls(
            {"id": "CH2.CONSENT.1", "member_controls": [{"framework_id": "dpdpa"}]},
            control_ids,
            ["dpdpa"],
        )


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _copy_example(validation_root: Path) -> Path:
    destination = validation_root / "companies" / "c0-example"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(EXAMPLE, destination, ignore=shutil.ignore_patterns("rendered"))
    return destination


@pytest.fixture
def rendered_example(tmp_path):
    validation_root = tmp_path / "validation"
    _copy_example(validation_root)
    render_pack("c0-example", validation_root=validation_root)
    return validation_root


def _visible_spec_text(spec: dict) -> str:
    content = spec["content"]
    kind = spec["render"]["kind"]
    if kind == "prose":
        parts = [content["title"], content["subtitle"]]
        for section in content["sections"]:
            parts.extend([section["heading"], *section["paragraphs"]])
        return "\n".join(parts)
    if kind == "table":
        return "\n".join([
            content["title"], content["subtitle"], *content["preamble"],
            *content["columns"], *(cell for row in content["rows"] for cell in row), *content["footer"],
        ])
    if kind in {"config", "console"}:
        return "\n".join([content["title"], *content["lines"]])
    return content["transcript"]


def test_schemas_reject_bad_pack_fields():
    table = _read(EXAMPLE / "client_visible/evidence/E02.json")
    table["content"]["rows"][0].pop()
    with pytest.raises(ValidationError, match="rows"):
        EvidenceSpec.model_validate(table)

    prose_png = _read(EXAMPLE / "client_visible/evidence/E01.json")
    prose_png["render"]["format"] = "png"
    prose_png["filename"] = "quarterly-access-review.png"
    with pytest.raises(ValidationError, match="render.format"):
        EvidenceSpec.model_validate(prose_png)

    magic = _read(EXAMPLE / "client_visible/evidence/E01.json")
    magic["channel"] = "magic_link"
    magic["consultant_maps_to"] = [{"framework_id": "iso27001", "requirement_id": "ISO.A5.1"}]
    with pytest.raises(ValidationError, match="magic_item"):
        EvidenceSpec.model_validate(magic)

    key = _read(EXAMPLE / "answer_key.json")
    key["control_truth"]["iso27001"]["overrides"].pop("ISO.A8.2")
    with pytest.raises(ValidationError, match="control_truth"):
        AnswerKey.model_validate(key)

    key = _read(EXAMPLE / "answer_key.json")
    key["decoys"][0]["requirements"].append(key["planted_gaps"][0]["requirements"][0])
    with pytest.raises(ValidationError, match="both"):
        AnswerKey.model_validate(key)


@pytest.mark.parametrize("bad_id", ["CH2.CONSENT.1", "ISO.A.9.99"])
def test_lint_rejects_unknown_or_unselected_registry_ids(tmp_path, bad_id):
    base = _copy_example(tmp_path)
    key = _read(base / "answer_key.json")
    key["control_truth"]["iso27001"]["overrides"][bad_id] = "compliant"
    _write(base / "answer_key.json", key)
    result = lint_pack("c0-example", validation_root=tmp_path)
    assert any(bad_id in error and "unknown control" in error for error in result.errors)


def test_export_is_offline_and_never_touches_working_database(monkeypatch, tmp_path):
    from app.config import settings
    from app.services import llm_client

    def unexpected(*_args, **_kwargs):
        raise AssertionError("export called the LLM")

    monkeypatch.setattr(llm_client, "call_llm", unexpected)
    db_path = settings.database_url.removeprefix("sqlite:///")
    if not Path(db_path).is_absolute():
        db_path = str(REPO_ROOT / db_path)
    db_file = Path(db_path)
    before = (db_file.stat().st_mtime_ns, db_file.stat().st_size) if db_file.is_file() else None
    validation_root = tmp_path / "validation"
    _copy_example(validation_root)
    export_question_pack("c0-example", "intake", validation_root=validation_root, temp_parent=tmp_path)
    export_question_pack("c0-example", "questionnaire", validation_root=validation_root, temp_parent=tmp_path)
    after = (db_file.stat().st_mtime_ns, db_file.stat().st_size) if db_file.is_file() else None
    assert before == after
    example = validation_root / "companies" / "c0-example"
    assert (example / "question_pack.intake.json").is_file()
    assert (example / "question_pack.questionnaire.json").is_file()
    questionnaire = _read(example / "question_pack.questionnaire.json")
    mapped_questions = [
        question
        for section in questionnaire["sections"]
        for question in section["questions"]
        if question.get("member_controls")
    ]
    assert mapped_questions
    assert all(
        set(control) == {"framework_id", "requirement_id"}
        for question in mapped_questions
        for control in question["member_controls"]
    )


def test_rendering_is_deterministic_and_manifest_matches_specs(tmp_path):
    first = render_pack("c0-example", output_dir=tmp_path / "first")
    second = render_pack("c0-example", output_dir=tmp_path / "second")
    hashes_a = {
        path.relative_to(tmp_path / "first").as_posix(): __import__("hashlib").sha256(path.read_bytes()).hexdigest()
        for path in (tmp_path / "first").rglob("*") if path.is_file()
    }
    hashes_b = {
        path.relative_to(tmp_path / "second").as_posix(): __import__("hashlib").sha256(path.read_bytes()).hexdigest()
        for path in (tmp_path / "second").rglob("*") if path.is_file()
    }
    assert hashes_a == hashes_b
    for evidence_path in sorted((EXAMPLE / "client_visible/evidence").glob("*.json")):
        spec = _read(evidence_path)
        entry = first[spec["filename"]]
        assert entry["text"] == _visible_spec_text(spec)
        assert entry["sha256"] == second[spec["filename"]]["sha256"]
    assert first["privileged-access-register.png"]["sha256"] == second["privileged-access-register.png"]["sha256"]


def test_degraded_jpeg_retains_scan_quality(tmp_path):
    render_pack("c1-app-startup", output_dir=tmp_path)
    rendered_jpeg = tmp_path / "KiddieLearn-incident-channel-2026-09.jpg"
    expected_jpeg = tmp_path / "expected-quality-70.jpg"
    Image.new("RGB", (8, 8), "white").save(expected_jpeg, format="JPEG", quality=70, subsampling=0)
    with Image.open(rendered_jpeg) as actual, Image.open(expected_jpeg) as expected:
        assert actual.quantization == expected.quantization


def test_lint_catches_unfairness_leaks_bad_trails_and_missing_answers(tmp_path, rendered_example):
    assert lint_pack("c0-example", require_questionnaire=True, validation_root=rendered_example).errors == []

    base = _copy_example(tmp_path / "unfair")
    table_path = base / "client_visible/evidence/E02.json"
    table = _read(table_path)
    table["content"]["footer"] = ["The register was exported in September."]
    _write(table_path, table)
    render_pack("c0-example", validation_root=tmp_path / "unfair")
    result = lint_pack("c0-example", require_questionnaire=True, validation_root=tmp_path / "unfair")
    assert any("key fact is not verbatim" in error for error in result.errors)

    base = _copy_example(tmp_path / "filename")
    evidence_path = base / "client_visible/evidence/E03.json"
    spec = _read(evidence_path)
    spec["filename"] = "decoy-incident-exercise.pdf"
    _write(evidence_path, spec)
    render_pack("c0-example", validation_root=tmp_path / "filename")
    result = lint_pack("c0-example", validation_root=tmp_path / "filename")
    assert any("leak term 'decoy'" in error for error in result.errors)

    base = _copy_example(tmp_path / "shingle")
    prose_path = base / "client_visible/evidence/E01.json"
    prose = _read(prose_path)
    phrase = " ".join(_read(base / "answer_key.json")["planted_gaps"][0]["description"].split()[:8])
    prose["content"]["sections"][0]["paragraphs"].append(phrase)
    _write(prose_path, prose)
    render_pack("c0-example", validation_root=tmp_path / "shingle")
    result = lint_pack("c0-example", validation_root=tmp_path / "shingle")
    assert any("answer-key shingle leak" in error for error in result.errors)

    base = _copy_example(tmp_path / "image-trail")
    image_path = base / "client_visible/images/whiteboard.png"
    image_path.parent.mkdir(parents=True, exist_ok=True)
    image_path.write_bytes(
        (rendered_example / "companies/c0-example/rendered/privileged-access-register.png").read_bytes()
    )
    image_spec = {
        "artifact_id": "E04",
        "filename": "whiteboard.png",
        "category": "other",
        "channel": "consultant_upload",
        "magic_item": None,
        "consultant_maps_to": [],
        "render": {"kind": "external_image", "format": "png", "degrade": "none"},
        "content": {"image_path": "whiteboard.png", "transcript": "Whiteboard notes from the planning room."},
    }
    _write(base / "client_visible/evidence/E04.json", image_spec)
    key_path = base / "answer_key.json"
    key = _read(key_path)
    key["planted_gaps"][0]["evidence_trail"].append({"source": "evidence:E04", "locator": "image", "fact": "Whiteboard notes"})
    _write(key_path, key)
    render_pack("c0-example", validation_root=tmp_path / "image-trail")
    result = lint_pack("c0-example", validation_root=tmp_path / "image-trail")
    assert any("trail cannot reference external_image E04" in error for error in result.errors)

    base = _copy_example(tmp_path / "missing-answer")
    answers_path = base / "client_visible/questionnaire_answers.json"
    answers = _read(answers_path)
    answers["answers"].pop(next(iter(answers["answers"])))
    _write(answers_path, answers)
    result = lint_pack("c0-example", require_questionnaire=True, validation_root=tmp_path / "missing-answer")
    assert any("missing answer for" in error for error in result.errors)


def test_mock_runner_is_blind_and_completes_two_isolated_runs(tmp_path, monkeypatch, rendered_example):
    from scripts.validation import run_company as runner_module

    source = Path(runner_module.__file__).read_text(encoding="utf-8")
    assert "answer_key" not in source
    opened: list[str] = []
    original_open = builtins.open
    original_read_text = Path.read_text

    def tracking_open(file, *args, **kwargs):
        opened.append(str(file))
        return original_open(file, *args, **kwargs)

    def tracking_read_text(path, *args, **kwargs):
        opened.append(str(path))
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", tracking_open)
    monkeypatch.setattr(Path, "read_text", tracking_read_text)
    out = tmp_path / "runs"
    assert run_company("c0-example", llm="mock", runs=2, out=out, validation_root=rendered_example) == 0
    assert not any("answer_key.json" in path for path in opened)
    database_paths = []
    for index in (1, 2):
        run_dir = out / "c0-example" / f"run-{index}"
        database_paths.append(run_dir / "app.db")
        assert (run_dir / "transcript.jsonl").is_file()
        stages = _read(run_dir / "stages.json")
        assert all(stage["ok"] for stage in stages)
        assert "followups" not in {stage["stage"] for stage in stages}
        assert {stage["stage"] for stage in stages} >= {
            "hierarchy", "context", "scope", "evidence", "format_probes", "desk_review", "questionnaire", "analysis", "collect"
        }
        collected = _read(run_dir / "conclusions.json")
        scored = score_run(run_dir)
        assert len(collected["conclusions"]) == scored["coverage"]["conclusions_count"]
        coverage = _read(run_dir / "questionnaire_coverage.json")
        assert coverage["answer_without_render"] == []
        assert coverage["rendered_without_answer"] == []
        assert coverage["provenance_after_save"]["human"] == len(coverage["answered"])
        probes = _read(run_dir / "probes.json")
        assert len(probes) == 3
        assert all(probe.get("status_code") != 201 or probe.get("archive_status_code") == 200 for probe in probes)
    assert database_paths[0] != database_paths[1]

    payload, markdown = build_report(out)
    assert payload["stamp"] == "MOCK"
    assert "Run diagnostics" in markdown
    assert "Format probes:" in markdown
    assert "Cost:" in markdown
    key = _read(EXAMPLE / "answer_key.json")
    for gap in key["planted_gaps"]:
        assert gap["description"] not in markdown
    for decoy in key["decoys"]:
        assert decoy["why_it_looks_like_a_gap"] not in markdown
        assert decoy["why_it_is_compliant"] not in markdown
    with pytest.raises(ValueError, match="requires every run to use the live LLM"):
        build_report(out, baseline=True)


def test_scorer_arithmetic_grounding_recall_and_false_positives(tmp_path):
    validation_root = tmp_path / "validation"
    base = _copy_example(validation_root)
    key_path = base / "answer_key.json"
    key = _read(key_path)
    key["control_truth"]["iso27001"]["overrides"]["ISO.A5.2"] = "partially_compliant"
    key["planted_gaps"][1]["requirements"].append({"framework_id": "iso27001", "requirement_id": "ISO.A5.2"})
    _write(key_path, key)
    run_dir = tmp_path / "out" / "c0-example" / "run-1"
    run_dir.mkdir(parents=True)
    (run_dir / "run.json").write_text(json.dumps({"frameworks": ["iso27001"], "llm_mode": "mock"}), encoding="utf-8")
    payload = {
        "assessment": {"applicable_requirements": ["ISO.A8.2", "ISO.A5.15", "ISO.A5.2", "ISO.A5.24"]},
        "analysis_runs": [{"framework_id": "iso27001", "status": "completed"}],
        "conclusions": [
            {"framework_id": "iso27001", "requirement_id": "ISO.A8.2", "outcome": "partially_compliant", "rationale": "Review incomplete.", "gaps_identified": "", "evidence_summary": "", "risk_level": "high", "citations": []},
            {"framework_id": "iso27001", "requirement_id": "ISO.A5.15", "outcome": "insufficient_evidence", "rationale": "The REGISTER lists 20 administrator accounts.", "gaps_identified": " TEN   temporary accounts were excluded from that review. ", "evidence_summary": "", "risk_level": "medium", "citations": []},
            {"framework_id": "iso27001", "requirement_id": "ISO.A5.2", "outcome": "partially_compliant", "rationale": "Roles need additional review.", "gaps_identified": "", "evidence_summary": "", "risk_level": "medium", "citations": [{"filename": "quarterly-access-review.docx"}]},
            {"framework_id": "iso27001", "requirement_id": "ISO.A5.24", "outcome": "partially_compliant", "rationale": "", "gaps_identified": "", "evidence_summary": "", "risk_level": "low", "citations": []},
        ],
    }
    _write(run_dir / "conclusions.json", payload)
    result = score_run(run_dir, validation_root=validation_root)
    by_id = {gap["gap_id"]: gap for gap in result["gap_results"]}
    assert by_id["G01"]["req_scores"] == [0.5]
    assert by_id["G01"]["caught"] is False
    assert by_id["G02"]["req_scores"] == [0.3, 1.0]
    assert by_id["G02"]["gap_score"] == pytest.approx(0.65)
    assert by_id["G02"]["caught"] is True
    assert by_id["G02"]["grounded"] is True
    assert by_id["G02"]["key_fact_recall"] == 1.0
    assert result["decoy_results"][0]["false_positive"] is True

    payload["conclusions"][0]["outcome"] = "non_compliant"
    _write(run_dir / "conclusions.json", payload)
    result = score_run(run_dir, validation_root=validation_root)
    assert result["gap_results"][0]["req_scores"] == [1.0]
    assert result["gap_results"][0]["caught"] is True


def test_app_files_are_untouched_by_harness():
    if not (REPO_ROOT / ".git").exists():
        pytest.skip("not a git checkout")
    comparison_ref = "origin/main"
    if subprocess.run(
        ["git", "rev-parse", "--verify", comparison_ref],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    ).returncode != 0:
        comparison_ref = "main"
    merge_base = subprocess.run(
        ["git", "merge-base", "HEAD", comparison_ref],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    result = subprocess.run(
        [
            "git", "diff", "--name-only", merge_base, "--",
            "app", "alembic", "app/templates", "requirements.txt",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == ""
