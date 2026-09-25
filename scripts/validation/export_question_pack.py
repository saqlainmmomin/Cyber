"""Export intake and adaptive-questionnaire packs from an isolated SQLite app."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from scripts.validation.models import CompanyMeta, IntakeAnswers
from scripts.validation.paths import REPO_ROOT, VALIDATION_ROOT, pack_dir


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _member_controls(
    question: dict,
    control_ids_by_framework: dict[str, set[str]],
    framework_ids: list[str],
) -> list | None:
    for key in ("member_controls", "controls"):
        if key in question:
            return question[key]
    if "maps_to" not in question:
        return None

    covered = question.get("frameworks_covered") or framework_ids
    return [
        {"framework_id": framework_id, "requirement_id": requirement_id}
        for requirement_id in question["maps_to"]
        for framework_id in framework_ids
        if framework_id in covered and requirement_id in control_ids_by_framework.get(framework_id, set())
    ]


def _form_scope_answers(http, assessment_id: str, company: CompanyMeta, answers: dict[str, str]) -> None:
    response = http.post(
        f"/assessments/{assessment_id}/scope/save",
        data=answers,
        follow_redirects=False,
    )
    if response.status_code != 303:
        raise RuntimeError(f"scope save failed: {response.status_code} {response.text[:500]}")


def _make_assessment(http, db, company: CompanyMeta):
    from app.models.assessment import Assessment
    from app.models.engagement import Engagement

    response = http.post(
        "/engagements",
        data={
            "client_mode": "new",
            "company_name": company.company_name,
            "industry": company.industry.value,
            "company_size": company.company_size.value,
            "engagement_name": company.engagement_name,
            "engagement_type": "gap_assessment",
            "description": company.description,
            "selected_frameworks": company.frameworks,
        },
        follow_redirects=False,
    )
    if response.status_code != 303:
        raise RuntimeError(f"engagement creation failed: {response.status_code} {response.text[:500]}")
    db.expire_all()
    engagement = db.query(Engagement).filter(Engagement.name == company.engagement_name).first()
    if engagement is None:
        raise RuntimeError("engagement route did not create the requested engagement")
    assessment = (
        db.query(Assessment)
        .filter(Assessment.engagement_id == engagement.id)
        .order_by(Assessment.created_at.desc(), Assessment.id.desc())
        .first()
    )
    if assessment is None:
        raise RuntimeError("engagement route did not create an assessment")
    return engagement, assessment


def _run_child(slug: str, stage: str, validation_root: Path, temp_root: Path) -> None:
    """Runs after DATABASE_URL and UPLOAD_DIR are set, before app imports."""
    base = pack_dir(slug, validation_root)
    company = CompanyMeta.model_validate_json((base / "company.json").read_text(encoding="utf-8"))
    import app.main  # noqa: PLC0415
    from app.services import llm_client  # noqa: PLC0415
    from app.database import SessionLocal  # noqa: PLC0415
    from app.dpdpa.context_questions import CONTEXT_BLOCKS  # noqa: PLC0415
    from app.frameworks.registry import FrameworkRegistry  # noqa: PLC0415
    from app.schemas.assessment import DocumentCategory  # noqa: PLC0415
    from app.services.question_engine import build_adaptive_questionnaire  # noqa: PLC0415
    from fastapi.testclient import TestClient  # noqa: PLC0415

    def no_llm(*_args, **_kwargs):
        raise AssertionError("question-pack export must not call the LLM")

    llm_client.call_llm = no_llm

    client_visible = base / "client_visible"
    with TestClient(app.main.app) as http:
        with SessionLocal() as db:
            _engagement, assessment = _make_assessment(http, db, company)
            if stage == "questionnaire":
                intake = IntakeAnswers.model_validate_json((client_visible / "intake_answers.json").read_text(encoding="utf-8"))
                _form_scope_answers(http, assessment.id, company, intake.scope)
                # Context is assigned directly only in this throwaway export database;
                # the real context route calls an LLM and export must remain offline.
                assessment.context_answers = json.dumps(
                    [
                        {"question_id": question_id, "answer": value}
                        for question_id, value in intake.context.items()
                    ]
                )
                db.commit()
                questionnaire = build_adaptive_questionnaire(assessment.id, db)
                control_ids_by_framework = {
                    framework_id: {
                        control["id"]
                        for control in FrameworkRegistry.get_all_controls_enriched(framework_id)
                    }
                    for framework_id in company.frameworks
                }

        if stage == "intake":
            context = [
                {
                    "id": question["id"],
                    "text": question["question"],
                    "type": question["type"],
                    "options": question.get("options", []),
                }
                for block in CONTEXT_BLOCKS
                for question in block["questions"]
            ]
            scope = {}
            controls = {}
            for framework_id in company.frameworks:
                framework = FrameworkRegistry.get(framework_id)
                scope[framework_id] = [
                    {
                        "id": question.id,
                        "text": question.question,
                        "options": question.options,
                        "help_text": question.help_text,
                    }
                    for question in framework.scope_questions
                ]
                controls[framework_id] = [
                    {
                        "requirement_id": control["id"],
                        "title": control["title"],
                        "description": control["description"],
                        "domain": control["chapter"],
                        "section": control["section"],
                        "reference": control["section_ref"],
                    }
                    for control in FrameworkRegistry.get_all_controls_enriched(framework_id)
                ]
            from app.services.screening import get_domain_coverage

            payload = {
                "context": context,
                "scope": scope,
                "screening": get_domain_coverage() if company.frameworks == ["dpdpa"] else None,
                "document_categories": [category.value for category in DocumentCategory],
                "controls": controls,
                "magic_link_limits": {"expires_in_days": 7, "max_uploads": 20, "max_total_mb": 100},
            }
            _write_json(base / "question_pack.intake.json", payload)
            return

    sections = []
    for section in questionnaire["sections"]:
        questions = []
        for question in section["questions"]:
            item = {
                "id": question["id"],
                "text": question.get("question", question.get("text", "")),
                "status": question.get("status", "active"),
            }
            for key in ("cluster_id", "guidance"):
                if key in question:
                    item[key] = question[key]
            member_controls = _member_controls(question, control_ids_by_framework, company.frameworks)
            if member_controls is not None:
                item["member_controls"] = member_controls
            questions.append(item)
        sections.append(
            {
                "section_id": section["section_id"],
                "title": section.get("section_title", section.get("chapter_title", section["section_id"])),
                "questions": questions,
            }
        )
    _write_json(base / "question_pack.questionnaire.json", {"sections": sections})


def export_question_pack(
    slug: str,
    stage: str,
    *,
    validation_root: Path | None = None,
    temp_parent: Path | None = None,
) -> None:
    if stage not in {"intake", "questionnaire"}:
        raise ValueError("stage must be intake or questionnaire")
    root = (validation_root or VALIDATION_ROOT).resolve()
    pack_dir(slug, root)
    with tempfile.TemporaryDirectory(prefix="cyberassess-export-", dir=temp_parent) as temp_name:
        temp = Path(temp_name)
        env = os.environ.copy()
        env["DATABASE_URL"] = f"sqlite:///{temp / 'export.db'}"
        env["UPLOAD_DIR"] = str(temp / "uploads")
        command = [
            sys.executable,
            "-m",
            "scripts.validation.export_question_pack",
            "--_child",
            slug,
            stage,
            str(root),
            str(temp),
        ]
        result = subprocess.run(command, cwd=REPO_ROOT, env=env, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "question-pack export failed")
        if result.stdout.strip():
            print(result.stdout.strip())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug", nargs="?")
    parser.add_argument("--stage", choices=("intake", "questionnaire"))
    parser.add_argument("--_child", nargs=4, metavar=("SLUG", "STAGE", "ROOT", "TEMP"), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args._child:
        slug, stage, root, temp = args._child
        os.environ["DATABASE_URL"] = f"sqlite:///{Path(temp) / 'export.db'}"
        os.environ["UPLOAD_DIR"] = str(Path(temp) / "uploads")
        _run_child(slug, stage, Path(root), Path(temp))
        print(f"Exported {stage} questions for {slug}")
        return 0
    if not args.slug or not args.stage:
        parser.error("slug and --stage are required")
    try:
        export_question_pack(args.slug, args.stage)
    except Exception as exc:
        print(f"export failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
