"""Drive the Veldhara upload pack through the app's real HTTP routes, live.

Spends money. It needs OPENROUTER_KEY (from .env or the environment) and the
explicit flag --confirm-spend. Every LLM request and response is captured to
the output folder by scripts/live/capture.py. Nothing in the app changes.

Run from the repository root:

    .venv/bin/python -m scripts.live.drive --out ~/cyberassess-runs/<run> --confirm-spend

The driver reads only the consultant-visible files of the pack: `evidence/`,
`upload-manifest.csv` and `questionnaire-entry.json`. It never opens
`scenario.json`, `coverage-matrix.csv` or the entry guide's intended
judgments, and it never opens anything under the held-out evaluation set. This run is an
observation. Nothing is tuned to what it finds.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import mimetypes
import os
import subprocess
import sys
import threading
import time
import traceback
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DEFAULT_PACK = REPO_ROOT / "data" / "demo" / "veldhara-upload-pack"

# Intake values from the pack's consultant guide ("Company and engagement" and
# "Exact scope values").
COMPANY = {
    "company_name": "Veldhara Logistics Pvt Ltd.",
    "industry": "other",
    "company_size": "sme",
    "engagement_name": "Q2 FY2026-27 ISO 27001 assessment",
    "engagement_type": "gap_assessment",
    "description": "Q2 FY2026-27 ISO 27001 gap assessment, 1 July to 30 September 2026",
}
FRAMEWORKS = ["iso27001"]
SCOPE = {"ISO.SCP.1": "full_org", "ISO.SCP.2": "yes", "ISO.SCP.3": "both", "ISO.SCP.4": "yes_datacenter"}
# The guide's "Context" paragraph: identity, financial and location data;
# mobile app, forms and third-party APIs; foreign group reporting; sensitive
# personal data; high risk; internal policy posture; customer due diligence.
CONTEXT = {
    "CTX.DATA.1": ["identity", "financial", "location"],
    "CTX.DATA.2": ["mobile_app", "physical_forms", "third_party_apis"],
    "CTX.DATA.3": "yes",
    "CTX.DATA.4": "yes",
    "CTX.DATA.4a": "Singapore parent group",
    "CTX.POSTURE.1": "part_time_shared",
    "CTX.POSTURE.2": "internal_policy_only",
    "CTX.POSTURE.3": "internal_only",
    "CTX.POSTURE.4": "yes_recently_updated",
    "CTX.RISK.1": ["handles_sensitive_personal_data"],
    "CTX.RISK.2": "10k_to_1m",
    "CTX.RISK.3": "no",
    "CTX.INIT.1": "customer_due_diligence",
    "CTX.INIT.2": "3_to_6_months",
    "CTX.INIT.3": "50k_to_150k",
}
# The guide: "Upload only to a separate 2025 baseline assessment. Do not upload
# this file to the current assessment."
EXCLUDED_KEYS = {"prior_baseline"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def _git_sha() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True
        ).stdout.strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def _load_manifest(pack: Path) -> list[dict]:
    rows = list(csv.DictReader((pack / "upload-manifest.csv").open(encoding="utf-8")))
    for row in rows:
        path = pack / row["filename"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != row["sha256"]:
            raise SystemExit(f"pack integrity: {row['filename']} does not match its manifest hash")
    return rows


def _evidence_reference(entry: dict) -> str:
    parts = []
    for control, sources in (entry.get("sources") or {}).items():
        design = ", ".join(sources.get("design", []))
        operating = ", ".join(sources.get("operating", []))
        parts.append(f"{control}: design {design or 'none'}; operating {operating or 'none'}")
    return " | ".join(parts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pack", type=Path, default=DEFAULT_PACK)
    parser.add_argument("--out", type=Path, required=True, help="run folder, outside the repository")
    parser.add_argument("--max-words", type=int, default=30000, help="MAX_TOTAL_DOCUMENT_WORDS for this run")
    parser.add_argument("--spend-cap", type=float, default=5.0, help="hard stop on estimated USD")
    parser.add_argument("--no-followups", action="store_true")
    parser.add_argument("--stop-after", choices=["hierarchy", "context", "scope", "evidence", "desk_review", "questionnaire", "followups", "analysis"])
    parser.add_argument("--confirm-spend", action="store_true", help="required: this run spends money")
    args = parser.parse_args(argv)

    out = args.out.expanduser().resolve()
    if REPO_ROOT in (out, *out.parents):
        print("refusing: the run folder must be outside the repository", file=sys.stderr)
        return 2
    if not args.confirm_spend:
        print("refusing: pass --confirm-spend to run (this spends money)", file=sys.stderr)
        return 2
    pack = args.pack.expanduser().resolve()
    manifest = _load_manifest(pack)
    entries = json.loads((pack / "questionnaire-entry.json").read_text(encoding="utf-8"))
    out.mkdir(parents=True, exist_ok=True)

    # Settings are read at import, so the environment is set first.
    os.environ["DATABASE_URL"] = f"sqlite:///{out / 'app.db'}"
    os.environ["UPLOAD_DIR"] = str(out / "uploads")
    os.environ["MAX_TOTAL_DOCUMENT_WORDS"] = str(args.max_words)
    os.environ["ANALYSIS_PIPELINE_VERSION"] = "v1"

    from app.config import settings

    if not settings.openrouter_key:
        print("refusing: OPENROUTER_KEY is not set", file=sys.stderr)
        return 2

    from scripts.live.capture import Capture, key_usage_usd

    capture = Capture(out, spend_cap_usd=args.spend_cap)
    capture.install()
    usage_before = key_usage_usd(settings.openrouter_key)

    import app.main as application
    from app import database
    from app.models.analysis_run import AnalysisRun
    from app.models.assessment import Assessment
    from app.models.conclusion import Conclusion, ConclusionRevision
    from app.models.engagement import Engagement
    from app.models.evidence import EvidenceVersion
    from app.models.questionnaire import QuestionnaireResponse
    from app.services.question_engine import build_adaptive_questionnaire
    from fastapi.testclient import TestClient

    application._register_frameworks()

    run: dict = {
        "started_at": _utc_now(),
        "git_sha": _git_sha(),
        "pack": str(pack),
        "frameworks": FRAMEWORKS,
        "settings": {
            "max_total_document_words": settings.max_total_document_words,
            "analysis_pipeline_version": settings.analysis_pipeline_version,
            "llm_model_extract": settings.llm_model_extract,
            "llm_model_judge": settings.llm_model_judge,
            "llm_model_synthesize": settings.llm_model_synthesize,
            "llm_model_vision": settings.llm_model_vision,
            "llm_max_concurrency": settings.llm_max_concurrency,
            "llm_request_deadline_seconds": settings.llm_request_deadline_seconds,
            "llm_max_output_tokens_framework": settings.llm_max_output_tokens_framework,
        },
        "spend_cap_usd": args.spend_cap,
        "key_usage_before_usd": usage_before,
        "stages": [],
    }
    transcript = out / "http_transcript.jsonl"
    state: dict = {}
    heartbeat_stop = threading.Event()

    def heartbeat() -> None:
        while not heartbeat_stop.wait(30):
            snap = capture.snapshot()
            print(
                f"[{_utc_now()}] phase={capture.phase} sends={snap['sends_captured']} "
                f"est_spend=${snap['estimated_spend_usd']:.3f}",
                flush=True,
            )

    threading.Thread(target=heartbeat, daemon=True).start()

    def call(client, method: str, path: str, **kwargs):
        started = time.monotonic()
        response = client.request(method, path, **kwargs)
        row = {
            "ts": _utc_now(),
            "phase": capture.phase,
            "method": method.upper(),
            "path": path,
            "status": response.status_code,
            "seconds": round(time.monotonic() - started, 2),
            "body_start": response.text[:400],
        }
        with transcript.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
        return response

    # -- stages -----------------------------------------------------------

    def hierarchy(client):
        response = call(client, "POST", "/engagements", data={
            "client_mode": "new",
            **COMPANY,
            "selected_frameworks": FRAMEWORKS,
        }, follow_redirects=False)
        if response.status_code != 303:
            raise RuntimeError(f"engagement create returned {response.status_code}")
        with database.SessionLocal() as db:
            engagement = db.query(Engagement).order_by(Engagement.created_at.desc()).first()
            assessment = (
                db.query(Assessment)
                .filter(Assessment.engagement_id == engagement.id)
                .order_by(Assessment.created_at.desc())
                .first()
            )
            state["engagement_id"], state["assessment_id"] = engagement.id, assessment.id
        return {"engagement_id": state["engagement_id"], "assessment_id": state["assessment_id"]}

    def context(client):
        response = call(client, "POST", f"/assessments/{state['assessment_id']}/context/save", data=CONTEXT, follow_redirects=False)
        if response.status_code != 303:
            raise RuntimeError(f"context save returned {response.status_code}: {response.text[:300]}")
        return {"answers": len(CONTEXT)}

    def scope(client):
        response = call(client, "POST", f"/assessments/{state['assessment_id']}/scope/save", data=SCOPE, follow_redirects=False)
        if response.status_code != 303:
            raise RuntimeError(f"scope save returned {response.status_code}: {response.text[:300]}")
        return {"answers": len(SCOPE)}

    def evidence(client):
        uploaded, failures = [], []
        for row in manifest:
            if row["key"] in EXCLUDED_KEYS:
                continue
            path = pack / row["filename"]
            mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            started = time.monotonic()
            response = call(
                client, "POST", f"/api/assessments/{state['assessment_id']}/documents",
                data={"category": row["category"]},
                files={"file": (path.name, path.read_bytes(), mime)},
            )
            item = {
                "filename": path.name,
                "category": row["category"],
                "status": response.status_code,
                "seconds": round(time.monotonic() - started, 2),
            }
            if response.status_code == 201:
                item["evidence_id"] = response.json().get("id")
                uploaded.append(item)
            else:
                item["detail"] = response.text[:500]
                failures.append(item)
            print(f"  upload {path.name}: {response.status_code}", flush=True)
        with database.SessionLocal() as db:
            words = 0
            for item in uploaded:
                version = (
                    db.query(EvidenceVersion)
                    .filter(EvidenceVersion.evidence_id == item["evidence_id"])
                    .order_by(EvidenceVersion.version_number.desc())
                    .first()
                )
                item["words"] = len((version.extracted_text or "").split()) if version else 0
                words += item["words"]
        state["uploaded"] = uploaded
        _write_json(out / "uploads.json", {"uploaded": uploaded, "failures": failures, "total_words": words})
        return {"uploaded": len(uploaded), "failures": len(failures), "total_words": words}

    def desk_review(client):
        response = call(client, "POST", f"/api/assessments/{state['assessment_id']}/desk-review")
        if response.status_code != 200:
            raise RuntimeError(f"desk review returned {response.status_code}: {response.text[:400]}")
        detail = call(client, "GET", f"/api/assessments/{state['assessment_id']}/desk-review")
        _write_json(out / "desk_review.json", detail.json() if detail.status_code == 200 else {"status": detail.status_code})
        return response.json()

    def questionnaire(client):
        with database.SessionLocal() as db:
            rendered = build_adaptive_questionnaire(state["assessment_id"], db)
            before = [
                {"question_id": row.question_id, "answer": row.answer, "answer_source": row.answer_source}
                for row in db.query(QuestionnaireResponse)
                .filter(QuestionnaireResponse.assessment_id == state["assessment_id"])
                .all()
            ]
        by_id = {entry["question_id"]: entry for entry in entries}
        rendered_ids, answered, unmatched = [], [], []
        for section in rendered["sections"]:
            data = {"section_id": section["section_id"]}
            for question in section["questions"]:
                question_id = question["id"]
                rendered_ids.append(question_id)
                entry = by_id.get(question_id)
                if question.get("status") == "skipped" or entry is None:
                    unmatched.append(question_id)
                    continue
                data[f"answer_{question_id}"] = entry["answer"]
                data[f"notes_{question_id}"] = entry.get("notes", "")
                data[f"evidence_{question_id}"] = _evidence_reference(entry)
                answered.append(question_id)
            response = call(client, "POST", f"/assessments/{state['assessment_id']}/questionnaire/save", data=data)
            if response.status_code != 200:
                raise RuntimeError(f"questionnaire save returned {response.status_code} for {section['section_id']}")
        with database.SessionLocal() as db:
            after = Counter(
                row.answer_source or "unknown"
                for row in db.query(QuestionnaireResponse)
                .filter(QuestionnaireResponse.assessment_id == state["assessment_id"])
                .all()
            )
        report = {
            "rendered": len(rendered_ids),
            "answered_from_entry": len(answered),
            "rendered_without_entry_or_skipped": unmatched,
            "entry_ids_not_rendered": sorted(set(by_id) - set(rendered_ids)),
            "prefilled_before_save": before,
            "answer_source_after_save": dict(after),
        }
        _write_json(out / "questionnaire.json", report)
        return {k: (v if not isinstance(v, list) else len(v)) for k, v in report.items()}

    def followups(client):
        generated = {}
        for entry in entries:
            if entry["answer"] == "fully_implemented":
                continue
            response = call(
                client, "POST", f"/assessments/{state['assessment_id']}/questionnaire/followup",
                data={"question_id": entry["question_id"], "answer": entry["answer"]},
            )
            generated[entry["question_id"]] = {"status": response.status_code, "text": response.text[:1500]}
        _write_json(out / "followups.json", generated)
        return {"requested": len(generated)}

    def analysis(client):
        response = call(client, "POST", f"/api/assessments/{state['assessment_id']}/analyze")
        if response.status_code != 200:
            raise RuntimeError(f"analysis returned {response.status_code}: {response.text[:600]}")
        return response.json() if "json" in response.headers.get("content-type", "") else {"status": 200}

    def collect() -> dict:
        with database.SessionLocal() as db:
            rows = (
                db.query(Conclusion)
                .filter(Conclusion.assessment_id == state["assessment_id"])
                .order_by(Conclusion.framework_id, Conclusion.requirement_id)
                .all()
            )
            summary = []
            for row in rows:
                revision = (
                    db.query(ConclusionRevision)
                    .filter(ConclusionRevision.conclusion_id == row.id)
                    .order_by(ConclusionRevision.created_at.desc(), ConclusionRevision.id.desc())
                    .first()
                )
                summary.append({
                    "framework_id": row.framework_id,
                    "requirement_id": row.requirement_id,
                    "outcome": row.outcome,
                    "risk_level": row.risk_level,
                    "rationale": row.rationale,
                    "gaps_identified": row.gaps_identified,
                    "citations_json": revision.citations_json if revision else None,
                })
            runs = [
                {"framework_id": r.framework_id, "status": r.status, "model_id": r.model_id}
                for r in db.query(AnalysisRun).filter(AnalysisRun.assessment_id == state["assessment_id"]).all()
            ]
        _write_json(out / "conclusions.json", {"conclusions": summary, "analysis_runs": runs})
        return {"conclusions": len(summary), "outcomes": dict(Counter(item["outcome"] for item in summary)), "analysis_runs": runs}

    # -- run --------------------------------------------------------------

    sequence = [
        ("hierarchy", hierarchy),
        ("context", context),
        ("scope", scope),
        ("evidence", evidence),
        ("desk_review", desk_review),
        ("questionnaire", questionnaire),
    ]
    if not args.no_followups:
        sequence.append(("followups", followups))
    sequence.append(("analysis", analysis))

    exit_code = 0
    try:
        with TestClient(application.app) as client:
            for name, action in sequence:
                capture.phase = name
                started = time.monotonic()
                print(f"[{_utc_now()}] stage {name} starting", flush=True)
                row = {"stage": name, "started_at": _utc_now()}
                try:
                    row["detail"] = action(client)
                    row["ok"] = True
                except BaseException as exc:  # noqa: BLE001 - record and stop
                    row.update(ok=False, error=f"{type(exc).__name__}: {exc}", traceback=traceback.format_exc())
                    exit_code = 2
                row["seconds"] = round(time.monotonic() - started, 1)
                run["stages"].append(row)
                _write_json(out / "run.json", run)
                snap = capture.snapshot()
                print(
                    f"[{_utc_now()}] stage {name} {'ok' if row['ok'] else 'FAILED'} in {row['seconds']} s; "
                    f"sends={snap['sends_captured']} est_spend=${snap['estimated_spend_usd']:.3f}",
                    flush=True,
                )
                if not row["ok"] or capture.stop_reason or args.stop_after == name:
                    break
            capture.phase = "collect"
            try:
                run["collected"] = collect()
            except Exception as exc:  # noqa: BLE001
                run["collected"] = {"error": str(exc)}
    finally:
        heartbeat_stop.set()
        usage_after = key_usage_usd(settings.openrouter_key)
        run["finished_at"] = _utc_now()
        run["key_usage_after_usd"] = usage_after
        run["key_usage_delta_usd"] = (
            round(usage_after - usage_before, 4) if usage_before is not None and usage_after is not None else None
        )
        run["capture"] = capture.snapshot()
        run["assessment_id"] = state.get("assessment_id")
        _write_json(out / "run.json", run)
        print(json.dumps({k: run[k] for k in ("capture", "key_usage_delta_usd")}, indent=2), flush=True)
    if capture.stop_reason:
        print(f"STOPPED: {capture.stop_reason}", file=sys.stderr)
        return 3
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
