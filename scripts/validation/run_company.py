"""Drive a blinded company pack through the product's actual HTTP routes."""

from __future__ import annotations

import argparse
import csv
import html
import importlib.util
import io
import json
import mimetypes
import os
import re
import subprocess
import sys
import time
import traceback
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from scripts.validation.models import CompanyMeta, EvidenceSpec, IntakeAnswers, QuestionnaireAnswers
from scripts.validation.paths import REPO_ROOT, VALIDATION_ROOT, client_visible_files, load_client_visible, run_root


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class MockLLM:
    """Small deterministic responses for route-level harness smoke runs."""

    def __init__(self, frameworks: list[str]):
        self.frameworks = frameworks

    def __call__(self, tier: str, **request) -> dict:
        system = request.get("system", "")
        if isinstance(system, list):
            system_text = " ".join(str(block) for block in system)
        else:
            system_text = str(system)
        prompt = " ".join(str(message.get("content", "")) for message in request.get("messages", []))
        combined = (system_text + " " + prompt).casefold()
        if "risk profile" in combined and "risk_tier" in combined:
            data = {
                "risk_tier": "MEDIUM",
                "priority_chapters": ["chapter_2"],
                "likely_not_applicable": [],
                "industry_context": "Synthetic organization.",
                "timeline_pressure": "MEDIUM",
                "framing_notes": "Synthetic route test.",
            }
        elif "inferences" in combined and tier == "judge":
            data = {"inferences": {}}
        elif "evidence extraction" in combined or "extract exact quotes" in combined:
            data = {"evidence": {}}
        elif "follow-up" in combined or "follow up" in combined:
            data = {"followups": []}
        elif "synthesis" in combined or tier == "synthesize":
            data = {"executive_summary": "Synthetic analysis."}
        elif tier == "judge" and self.frameworks:
            import app.main  # noqa: F401
            from app.frameworks.registry import FrameworkRegistry

            ids = []
            for framework_id in self.frameworks:
                controls = FrameworkRegistry.get(framework_id).all_controls()
                if all(control.id in prompt for control in controls[:1]):
                    ids = [control.id for control in controls]
                    break
            if not ids:
                # The active framework name appears in the framework prompt. Use
                # its registry definition and preserve a complete control set.
                for framework_id in self.frameworks:
                    framework = FrameworkRegistry.get(framework_id)
                    if framework.name.casefold() in combined:
                        ids = [control.id for control in framework.all_controls()]
                        break
            if not ids:
                ids = [control.id for control in FrameworkRegistry.get(self.frameworks[0]).all_controls()]
            data = {
                "executive_summary": "Synthetic offline analysis.",
                "assessments": [
                    {
                        "requirement_id": requirement_id,
                        "compliance_status": "not_assessed",
                        "current_state": "Not assessed by the deterministic mock.",
                        "gap_description": "",
                        "risk_level": "low",
                        "remediation_action": "",
                        "evidence_quote": "",
                    }
                    for requirement_id in ids
                ],
            }
        else:
            data = {}
        return {
            "text": json.dumps(data),
            "usage": {
                "input_tokens": 0,
                "output_tokens": 0,
                "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 0,
            },
        }


def _mime(filename: str) -> str:
    return mimetypes.guess_type(filename)[0] or "application/octet-stream"


def _evidence_specs(allowed: dict[str, Path]) -> list[tuple[EvidenceSpec, Path]]:
    items = []
    for relative, path in sorted(allowed.items()):
        if relative.startswith("client_visible/evidence/") and path.suffix == ".json":
            spec = EvidenceSpec.model_validate_json(path.read_text(encoding="utf-8"))
            rendered = allowed.get(f"rendered/{spec.filename}")
            if rendered is None or not rendered.is_file():
                raise FileNotFoundError(f"Rendered artifact is missing: {spec.filename}")
            items.append((spec, rendered))
    return items


def _probe_bytes(filename: str) -> tuple[bytes, str] | None:
    if filename.endswith(".xlsx"):
        if importlib.util.find_spec("openpyxl") is None:
            return None
        from openpyxl import Workbook

        book = Workbook()
        sheet = book.active
        sheet.append(["User", "Last reviewed"])
        sheet.append(["synthetic-user", "2026-09-01"])
        buffer = io.BytesIO()
        book.save(buffer)
        return buffer.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    if filename.endswith(".csv"):
        return b"user,last_reviewed\nsynthetic-user,2026-09-01\n", "text/csv"
    return b"hostname synthetic-router\nlogin block-for 60 attempts 5 within 60\n", "text/plain"


def _strip_html(value: str) -> str:
    text = re.sub(r"<[^>]*>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def _child_run(slug: str, out_dir: Path, validation_root: Path, llm_mode: str, stop_after: str | None, followups: bool) -> int:
    allowed = load_client_visible(slug, validation_root)
    company = CompanyMeta.model_validate_json(allowed["company.json"].read_text(encoding="utf-8"))
    intake = IntakeAnswers.model_validate_json(allowed["client_visible/intake_answers.json"].read_text(encoding="utf-8"))
    questionnaire = QuestionnaireAnswers.model_validate_json(allowed["client_visible/questionnaire_answers.json"].read_text(encoding="utf-8"))
    specs = _evidence_specs(allowed)
    out_dir.mkdir(parents=True, exist_ok=True)
    transcript_path = out_dir / "transcript.jsonl"
    stages_path = out_dir / "stages.json"
    stages: list[dict] = []
    run_meta = {
        "slug": slug,
        "frameworks": company.frameworks,
        "llm_mode": llm_mode,
        "started_at": _utc_now(),
        "mock": llm_mode == "mock",
    }
    _json_write(out_dir / "run.json", run_meta)

    import app.main as application  # noqa: PLC0415
    from app import database  # noqa: PLC0415
    from app.config import settings  # noqa: PLC0415
    from app.models.analysis_run import AnalysisRun  # noqa: PLC0415
    from app.models.assessment import Assessment  # noqa: PLC0415
    from app.models.conclusion import Conclusion, ConclusionRevision  # noqa: PLC0415
    from app.models.evidence import Evidence  # noqa: PLC0415
    from app.models.engagement import Engagement  # noqa: PLC0415
    from app.models.questionnaire import QuestionnaireResponse  # noqa: PLC0415
    from app.models.report import GapReport  # noqa: PLC0415
    from app.services import llm_client  # noqa: PLC0415
    from app.services.citations import resolve_citations  # noqa: PLC0415
    from app.services.question_engine import build_adaptive_questionnaire  # noqa: PLC0415
    from fastapi.testclient import TestClient  # noqa: PLC0415
    from sqlalchemy import select  # noqa: PLC0415

    if llm_mode == "mock":
        llm_client.call_llm = MockLLM(company.frameworks)
    else:
        original_call = llm_client.call_llm
        tier_setting = {
            "extract": "llm_model_extract",
            "judge": "llm_model_judge",
            "synthesize": "llm_model_synthesize",
            "vision": "llm_model_vision",
        }

        def recorded_call(tier, *args, **kwargs):
            started = time.perf_counter()
            try:
                result = original_call(tier, *args, **kwargs)
            except Exception:
                elapsed = round((time.perf_counter() - started) * 1000, 2)
                row = {
                    "ts": _utc_now(),
                    "tier": str(tier),
                    "model": getattr(settings, tier_setting.get(str(tier), "llm_model_judge")),
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cache_read_input_tokens": 0,
                    "elapsed_ms": elapsed,
                    "ok": False,
                }
                with (out_dir / "llm_usage.jsonl").open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(row, sort_keys=True) + "\n")
                raise
            usage = result.get("usage", {})
            row = {
                "ts": _utc_now(),
                "tier": str(tier),
                "model": getattr(settings, tier_setting.get(str(tier), "llm_model_judge")),
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
                "cache_read_input_tokens": usage.get("cache_read_input_tokens", 0),
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
                "ok": True,
            }
            with (out_dir / "llm_usage.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(row, sort_keys=True) + "\n")
            return result

        llm_client.call_llm = recorded_call

    context: dict[str, str] = {}
    engagement_id = None
    assessment_id = None
    response_log: list[dict] = []
    current_stage = ""

    def request(client, stage: str, method: str, path: str, **kwargs):
        started = time.perf_counter()
        response = client.request(method, path, **kwargs)
        body = response.text[:2048]
        row = {
            "ts": _utc_now(),
            "stage": stage,
            "method": method.upper(),
            "path": path,
            "status": response.status_code,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
            "note": body,
        }
        response_log.append(row)
        with transcript_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        return response

    def save_stage(stage: str, ok: bool, started: float, detail) -> None:
        stages.append({"stage": stage, "ok": ok, "elapsed_s": round(time.perf_counter() - started, 4), "detail": detail})
        _json_write(stages_path, stages)

    def perform(stage: str, action, *, continue_on_error: bool = False) -> bool:
        nonlocal current_stage
        current_stage = stage
        started = time.perf_counter()
        before_logs = len(response_log)
        try:
            detail = action()
            new_responses = response_log[before_logs:]
            non_success = [
                row for row in new_responses
                if not 200 <= row["status"] < 300
                and not (stage in {"hierarchy", "context", "scope"} and row["status"] == 303)
            ]
            ok = not non_success or stage == "format_probes"
            if non_success:
                detail = {"detail": detail, "non_success": [{"path": row["path"], "status": row["status"]} for row in non_success]}
            save_stage(stage, ok, started, detail)
            return True
        except Exception as exc:
            save_stage(stage, False, started, {"error": str(exc), "traceback": traceback.format_exc()})
            return continue_on_error

    def hierarchy(client):
        nonlocal engagement_id, assessment_id
        response = request(client, "hierarchy", "POST", "/engagements", data={
            "client_mode": "new",
            "company_name": company.company_name,
            "industry": company.industry.value,
            "company_size": company.company_size.value,
            "engagement_name": company.engagement_name,
            "engagement_type": "gap_assessment",
            "description": company.description,
            "selected_frameworks": company.frameworks,
        }, follow_redirects=False)
        if response.status_code != 303:
            raise RuntimeError(f"hierarchy route returned {response.status_code}")
        with database.SessionLocal() as db:
            engagement = db.query(Engagement).filter(Engagement.name == company.engagement_name).order_by(Engagement.created_at.desc()).first()
            assessment = db.query(Assessment).filter(Assessment.engagement_id == engagement.id).order_by(Assessment.created_at.desc()).first() if engagement else None
            if engagement is None or assessment is None:
                raise RuntimeError("hierarchy route did not create engagement and assessment")
            engagement_id, assessment_id = engagement.id, assessment.id
        return {"engagement_id": engagement_id, "assessment_id": assessment_id}

    def context_stage(client):
        nonlocal context
        context = intake.context
        response = request(client, "context", "POST", f"/assessments/{assessment_id}/context/save", data=context, follow_redirects=False)
        if response.status_code != 303:
            raise RuntimeError(f"context route returned {response.status_code}")
        return {"answers": len(context)}

    def scope_stage(client):
        response = request(client, "scope", "POST", f"/assessments/{assessment_id}/scope/save", data=intake.scope, follow_redirects=False)
        if response.status_code != 303:
            raise RuntimeError(f"scope route returned {response.status_code}")
        return {"answers": len(intake.scope)}

    def evidence_stage(client):
        uploaded = []
        failures = []
        for spec, path in specs:
            if spec.channel != "consultant_upload":
                continue
            response = request(client, "evidence", "POST", f"/api/assessments/{assessment_id}/documents", data={"category": spec.category.value}, files={"file": (spec.filename, path.read_bytes(), _mime(spec.filename))})
            if response.status_code == 201:
                uploaded.append(response.json().get("id"))
            else:
                failures.append({"filename": spec.filename, "status": response.status_code, "detail": response.text[:2048]})
        if intake.magic_link_items:
            link_response = request(client, "evidence", "POST", f"/engagements/{engagement_id}/magic-links", data={
                "items": "\n".join(intake.magic_link_items),
                "expires_in_days": 7,
                "max_uploads": 20,
                "max_total_mb": 100,
            })
            link_match = re.search(r"/magic/([A-Za-z0-9_-]+)", link_response.text)
            if not link_match:
                raise RuntimeError("magic-link creation response did not contain its URL")
            token = link_match.group(1)
            page = request(client, "evidence", "GET", f"/magic/{token}")
            item_keys = {
                html.unescape(title).strip(): html.unescape(key)
                for key, title in re.findall(r'<option value="([^"]+)">([^<]+)</option>', page.text)
            }
            for spec, path in specs:
                if spec.channel != "magic_link":
                    continue
                item_key = item_keys.get(spec.magic_item or "")
                if not item_key:
                    failures.append({"filename": spec.filename, "status": 422, "detail": f"No item key for {spec.magic_item!r}"})
                    continue
                response = request(client, "evidence", "POST", f"/magic/{token}", data={"item_key": item_key}, files={"file": (spec.filename, path.read_bytes(), _mime(spec.filename))})
                if not 200 <= response.status_code < 300:
                    failures.append({"filename": spec.filename, "status": response.status_code, "detail": response.text[:2048]})
                    continue
                with database.SessionLocal() as db:
                    row = db.query(Evidence).filter(Evidence.assessment_id == assessment_id, Evidence.original_filename == spec.filename).order_by(Evidence.created_at.desc()).first()
                    evidence_id = row.id if row else None
                if evidence_id is None:
                    failures.append({"filename": spec.filename, "status": 500, "detail": "uploaded file has no evidence row"})
                    continue
                for ref in spec.consultant_maps_to:
                    map_response = request(client, "evidence", "POST", f"/api/evidence/{evidence_id}/uses", json={
                        "assessment_id": assessment_id,
                        "framework_id": ref.framework_id,
                        "requirement_id": ref.requirement_id,
                        "relevance": "primary",
                    })
                    if map_response.status_code != 201:
                        failures.append({"filename": spec.filename, "status": map_response.status_code, "detail": map_response.text[:2048]})
        return {"uploaded": uploaded, "failures": failures, "magic_link_maps_relevance": "primary"}

    def format_probes(client):
        probes = []
        for filename in ("probe-access-review.xlsx", "probe-users.csv", "probe-router.conf"):
            built = _probe_bytes(filename)
            if built is None:
                probes.append({"format": Path(filename).suffix.lstrip("."), "filename": filename, "status_code": None, "detail": "skipped: openpyxl is not installed"})
                continue
            content, mime = built
            response = request(client, "format_probes", "POST", f"/api/assessments/{assessment_id}/documents", data={"category": "other"}, files={"file": (filename, content, mime)})
            entry = {"format": Path(filename).suffix.lstrip("."), "filename": filename, "status_code": response.status_code, "detail": response.text[:2048]}
            if response.status_code == 201:
                evidence_id = response.json().get("id")
                archived = request(client, "format_probes", "POST", f"/api/evidence/{evidence_id}/transitions", json={"to_status": "archived"})
                entry["archive_status_code"] = archived.status_code
                if archived.status_code >= 300:
                    entry["archive_detail"] = archived.text[:2048]
            probes.append(entry)
        _json_write(out_dir / "probes.json", probes)
        return probes

    def desk_review(client):
        response = request(client, "desk_review", "POST", f"/api/assessments/{assessment_id}/desk-review")
        if response.status_code != 200:
            raise RuntimeError(f"desk review returned {response.status_code}")
        detail = request(client, "desk_review", "GET", f"/api/assessments/{assessment_id}/desk-review")
        if detail.status_code != 200:
            raise RuntimeError(f"desk-review result returned {detail.status_code}")
        _json_write(out_dir / "desk_review.json", detail.json())
        return response.json()

    def screening(client):
        response = request(client, "screening", "POST", f"/assessments/{assessment_id}/screening/submit", data=intake.screening or {}, follow_redirects=False)
        if response.status_code not in {200, 303}:
            raise RuntimeError(f"screening route returned {response.status_code}")
        return {"answers": len(intake.screening or {})}

    def questionnaire_stage(client):
        with database.SessionLocal() as db:
            assessment = db.get(Assessment, assessment_id)
            rendered = build_adaptive_questionnaire(assessment_id, db)
            rendered_questions = [
                (section, question)
                for section in rendered["sections"]
                for question in section["questions"]
            ]
            rendered_ids = [question["id"] for _, question in rendered_questions]
            eligible = {question["id"] for _, question in rendered_questions if question.get("status") != "skipped"}
            answer_map = questionnaire.answers
            answer_without_render = sorted(set(answer_map) - set(rendered_ids))
            rendered_without_answer = sorted(eligible - set(answer_map))
            prefilled = [
                {"question_id": row.question_id, "answer_source": row.answer_source}
                for row in db.query(QuestionnaireResponse).filter(QuestionnaireResponse.assessment_id == assessment_id).all()
                if row.answer_source in {"document", "inferred"}
            ]
        for section in rendered["sections"]:
            data = {"section_id": section["section_id"]}
            for question in section["questions"]:
                qid = question["id"]
                if question.get("status") == "skipped" or qid not in questionnaire.answers:
                    continue
                entry = questionnaire.answers[qid]
                data.update({
                    f"answer_{qid}": entry.answer,
                    f"notes_{qid}": entry.notes,
                    f"evidence_{qid}": entry.evidence_reference,
                })
            response = request(client, "questionnaire", "POST", f"/assessments/{assessment_id}/questionnaire/save", data=data)
            if response.status_code != 200:
                raise RuntimeError(f"questionnaire save returned {response.status_code} for {section['section_id']}")
        with database.SessionLocal() as db:
            rows = db.query(QuestionnaireResponse).filter(QuestionnaireResponse.assessment_id == assessment_id).all()
            provenance = dict(Counter(row.answer_source or "unknown" for row in rows))
        payload = {
            "rendered_ids": rendered_ids,
            "answered": sorted(set(answer_map) & eligible),
            "rendered_without_answer": rendered_without_answer,
            "answer_without_render": answer_without_render,
            "prefilled_before_save": prefilled,
            "provenance_after_save": provenance,
        }
        _json_write(out_dir / "questionnaire_coverage.json", payload)
        return payload

    def followup_stage(client):
        generated = {}
        for question_id, entry in questionnaire.answers.items():
            if entry.answer == "fully_implemented":
                continue
            response = request(client, "followups", "POST", f"/assessments/{assessment_id}/questionnaire/followup", data={"question_id": question_id, "answer": entry.answer})
            if response.status_code >= 300:
                generated[question_id] = {"status": response.status_code, "text": ""}
            else:
                generated[question_id] = {"status": response.status_code, "text": _strip_html(response.text)}
        _json_write(out_dir / "followups.json", generated)
        return {"generated": len(generated), "persisted_or_sent_to_analysis": False}

    def analyze(client):
        response = request(client, "analysis", "POST", f"/api/assessments/{assessment_id}/analyze")
        if response.status_code != 200:
            raise RuntimeError(f"analysis returned {response.status_code}: {response.text[:2048]}")
        return response.json() if "application/json" in response.headers.get("content-type", "") else {"status": response.status_code}

    def collect(_client):
        with database.SessionLocal() as db:
            assessment = db.get(Assessment, assessment_id)
            conclusions = db.query(Conclusion).filter(Conclusion.assessment_id == assessment_id).order_by(Conclusion.framework_id, Conclusion.requirement_id).all()
            collected = []
            for conclusion in conclusions:
                revision = db.query(ConclusionRevision).filter(ConclusionRevision.conclusion_id == conclusion.id).order_by(ConclusionRevision.created_at.desc(), ConclusionRevision.id.desc()).first()
                citations = resolve_citations(db, revision.citations_json) if revision else []
                collected.append({
                    "framework_id": conclusion.framework_id,
                    "requirement_id": conclusion.requirement_id,
                    "outcome": conclusion.outcome,
                    "rationale": conclusion.rationale,
                    "evidence_summary": conclusion.evidence_summary,
                    "gaps_identified": conclusion.gaps_identified,
                    "risk_level": conclusion.risk_level,
                    "recommended_action": conclusion.recommended_action,
                    "ai_proposed": conclusion.ai_proposed,
                    "version": conclusion.version,
                    "analysis_run_id": revision.analysis_run_id if revision else None,
                    "citations": citations,
                })
            analysis_runs = db.query(AnalysisRun).filter(AnalysisRun.assessment_id == assessment_id).order_by(AnalysisRun.started_at, AnalysisRun.framework_id).all()
            report = db.query(GapReport).filter(GapReport.assessment_id == assessment_id).first()
            applicable = None
            if assessment and assessment.applicable_requirements:
                try:
                    applicable = json.loads(assessment.applicable_requirements)
                except (TypeError, json.JSONDecodeError):
                    applicable = None
            payload = {
                "assessment": {
                    "id": assessment_id,
                    "applicable_requirements": applicable,
                    "selected_frameworks": company.frameworks,
                },
                "conclusions": collected,
                "analysis_runs": [
                    {"framework_id": row.framework_id, "status": row.status, "model_id": row.model_id, "started_at": row.started_at.isoformat(), "completed_at": row.completed_at.isoformat() if row.completed_at else None}
                    for row in analysis_runs
                ],
                "framework_scores": json.loads(report.framework_scores) if report and report.framework_scores else None,
            }
        _json_write(out_dir / "conclusions.json", payload)
        return {"conclusions": len(payload["conclusions"]), "analysis_runs": len(payload["analysis_runs"])}

    with TestClient(application.app) as client:
        operations = [
            ("hierarchy", lambda: hierarchy(client)),
            ("context", lambda: context_stage(client)),
            ("scope", lambda: scope_stage(client)),
            ("evidence", lambda: evidence_stage(client)),
            ("format_probes", lambda: format_probes(client)),
            ("desk_review", lambda: desk_review(client)),
        ]
        if company.frameworks == ["dpdpa"]:
            operations.append(("screening", lambda: screening(client)))
        operations.append(("questionnaire", lambda: questionnaire_stage(client)))
        if followups:
            operations.append(("followups", lambda: followup_stage(client)))
        operations.extend([("analysis", lambda: analyze(client)), ("collect", lambda: collect(client))])
        for stage, action in operations:
            success = perform(stage, action, continue_on_error=False)
            if not success:
                run_meta["finished_at"] = _utc_now()
                run_meta["reached_collect"] = any(item["stage"] == "collect" for item in stages)
                _json_write(out_dir / "run.json", run_meta)
                return 2
            if stop_after == stage:
                break
    run_meta["finished_at"] = _utc_now()
    run_meta["reached_collect"] = any(item["stage"] == "collect" for item in stages)
    _json_write(out_dir / "run.json", run_meta)
    return 0 if run_meta["reached_collect"] or stop_after else 2


def run_company(
    slug: str,
    *,
    runs: int = 1,
    stop_after: str | None = None,
    followups: bool = False,
    llm: str = "live",
    out: Path | str | None = None,
    validation_root: Path | None = None,
) -> int:
    if runs < 1:
        raise ValueError("--runs must be at least 1")
    if llm not in {"live", "mock"}:
        raise ValueError("--llm must be live or mock")
    validation_root = (validation_root or VALIDATION_ROOT).resolve()
    # Load only paths from the explicit client-visible allow-list.
    client_visible_files(slug, validation_root)
    if llm == "live" and not os.environ.get("OPENROUTER_KEY"):
        raise ValueError("OPENROUTER_KEY must be set for --llm live")
    lint = subprocess.run(
        [sys.executable, "-m", "scripts.validation.lint_pack", slug, "--require-questionnaire"],
        cwd=REPO_ROOT,
        env={**os.environ, "CYBERASSESS_VALIDATION_ROOT": str(validation_root)},
        capture_output=True,
        text=True,
    )
    if lint.returncode:
        raise ValueError(f"pack lint failed:\n{lint.stdout}\n{lint.stderr}")
    target_root = run_root(out or (VALIDATION_ROOT / "runs" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")))
    overall = 0
    for run_index in range(1, runs + 1):
        run_dir = target_root / slug / f"run-{run_index}"
        run_dir.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env["DATABASE_URL"] = f"sqlite:///{run_dir / 'app.db'}"
        env["UPLOAD_DIR"] = str(run_dir / "uploads")
        env["CYBERASSESS_VALIDATION_ROOT"] = str(validation_root)
        command = [
            sys.executable,
            "-m",
            "scripts.validation.run_company",
            "--_child",
            slug,
            str(run_dir),
            str(validation_root),
            llm,
            stop_after or "",
            "1" if followups else "0",
        ]
        result = subprocess.run(command, cwd=REPO_ROOT, env=env, text=True)
        if result.returncode:
            overall = 2
    return overall


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug", nargs="?")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--stop-after")
    parser.add_argument("--followups", action="store_true")
    parser.add_argument("--llm", choices=("live", "mock"), default="live")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--_child", nargs=6, metavar=("SLUG", "RUN_DIR", "ROOT", "LLM", "STOP", "FOLLOWUPS"), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args._child:
        slug, run_dir, root, llm_mode, stop, follow = args._child
        target = Path(run_dir)
        os.environ["DATABASE_URL"] = f"sqlite:///{target / 'app.db'}"
        os.environ["UPLOAD_DIR"] = str(target / "uploads")
        try:
            return _child_run(slug, target, Path(root), llm_mode, stop or None, follow == "1")
        except Exception:
            target.mkdir(parents=True, exist_ok=True)
            _json_write(target / "run.json", {"slug": slug, "llm_mode": llm_mode, "reached_collect": False, "fatal_error": traceback.format_exc()})
            print(traceback.format_exc(), file=sys.stderr)
            return 2
    if not args.slug:
        parser.error("slug is required")
    try:
        return run_company(args.slug, runs=args.runs, stop_after=args.stop_after, followups=args.followups, llm=args.llm, out=args.out)
    except Exception as exc:
        print(f"run_company failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
