#!/usr/bin/env python3
"""Regenerate the canonical DPDPA golden files.

The default capture is an explicitly labeled, deterministic synthetic
characterization and never contacts Claude. A genuine recording requires both
``--live`` and ``USE_LIVE_ANALYZER=1``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import struct
import sys
import zlib
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pdfplumber
from fpdf import FPDF
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app.models  # noqa: E402,F401
from app.config import settings  # noqa: E402
from app.database import Base  # noqa: E402
from app.dpdpa.prompts import SCREENING_DOMAINS  # noqa: E402
from app.dpdpa.questionnaire import build_questionnaire  # noqa: E402
from app.services.claude_analyzer import run_gap_analysis  # noqa: E402
from app.utils.pdf_export import generate_pdf  # noqa: E402
from tests.support.analyzer_mock import (  # noqa: E402
    analyzer_request_key,
    record_live_analyzer,
    with_recorded_analyzer,
)
from tests.support.canonical_dpdpa import (  # noqa: E402
    FIXED_NOW,
    analyzer_kwargs,
    extract_pdf_text,
    materialize_report,
    read_json,
    seed_assessment,
    synthetic_analyzer_response,
    write_json,
)

FIXTURE = ROOT / "tests" / "fixtures" / "canonical_dpdpa"
EXPECTED = FIXTURE / "expected"


class _FixedDatetime(datetime):
    @classmethod
    def now(cls, tz=None):
        return FIXED_NOW if tz is not None else FIXED_NOW.replace(tzinfo=None)


def _write_evidence_pdf(path: Path, title: str, paragraphs: list[str]) -> None:
    pdf = FPDF()
    pdf.set_creator("CyberAssess synthetic golden fixture")
    pdf.set_creation_date(FIXED_NOW)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.multi_cell(0, 8, title)
    pdf.ln(3)
    pdf.set_font("Helvetica", size=10)
    for paragraph in paragraphs:
        pdf.multi_cell(0, 5, paragraph)
        pdf.ln(2)
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(path)


def _write_fixture_logo(path: Path) -> None:
    """Write a tiny deterministic 3:1 PNG without adding an image dependency."""
    width, height = 120, 40
    pixel = bytes((30, 58, 95))
    raw = b"".join(b"\x00" + pixel * width for _ in range(height))

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, level=9))
        + chunk(b"IEND", b"")
    )


def bootstrap_inputs() -> None:
    FIXTURE.mkdir(parents=True, exist_ok=True)
    write_json(
        FIXTURE / "env.json",
        {
            "FIRM_LOGO_PATH": "tests/fixtures/canonical_dpdpa/firm_logo.png",
            "FIRM_NAME": "Northstar Compliance Labs",
            "FIRM_PRIMARY_HEX": "#1E3A5F",
        },
    )
    _write_fixture_logo(FIXTURE / "firm_logo.png")
    write_json(
        FIXTURE / "screening_answers.json",
        {
            domain["id"]: (
                f"Synthetic response for {domain['title']}: a documented process exists "
                "but operating evidence and review cadence are incomplete."
            )
            for domain in SCREENING_DOMAINS
        },
    )
    answer_cycle = [
        "fully_implemented",
        "partially_implemented",
        "partially_implemented",
        "planned",
        "not_implemented",
    ]
    questionnaire = {}
    for index, question in enumerate(build_questionnaire()):
        req_id = question["id"]
        answer = answer_cycle[index % len(answer_cycle)]
        questionnaire[req_id] = {
            "answer": answer,
            "confidence": "high",
            "notes": (
                f"Synthetic response for {req_id}; retained evidence is intentionally "
                "generic and contains no client information."
            ),
        }
    questionnaire["CH2.NOTICE.1"]["evidence_quote"] = (
        "Customers receive a concise privacy notice before account registration."
    )
    questionnaire["CH2.SECURITY.1"]["evidence_quote"] = (
        "Access reviews are performed quarterly and exceptions are tracked to closure."
    )
    questionnaire["BN.NOTIFY.1"]["evidence_quote"] = (
        "The incident lead records notification decisions in the breach register."
    )
    write_json(FIXTURE / "questionnaire_answers.json", questionnaire)

    evidence = {
        "privacy_policy.pdf": (
            "Synthetic Privacy Notice",
            [
                "This document belongs to Meridian Retail Systems Pvt. Ltd., a fictional organization created for automated tests.",
                "Customers receive a concise privacy notice before account registration. The notice describes purpose, contact channels, withdrawal, and data principal rights.",
            ],
        ),
        "breach_procedure.pdf": (
            "Synthetic Personal Data Breach Procedure",
            [
                "This procedure contains no real client, employee, or incident information.",
                "The incident lead records notification decisions in the breach register and coordinates notices to the Board and affected data principals.",
            ],
        ),
        "retention_policy.pdf": (
            "Synthetic Retention and Access Policy",
            [
                "Retention schedules are approved by control owners and reviewed each year.",
                "Access reviews are performed quarterly and exceptions are tracked to closure. Evidence in this file is entirely synthetic.",
            ],
        ),
    }
    for filename, (title, paragraphs) in evidence.items():
        _write_evidence_pdf(FIXTURE / "evidence" / filename, title, paragraphs)


def _write_synthetic_recording() -> None:
    response = synthetic_analyzer_response(FIXTURE)
    calls = {}

    def synthetic_call(*args, **kwargs):
        calls[analyzer_request_key(args, kwargs)] = response
        return response

    with patch("app.services.claude_analyzer._call_claude", side_effect=synthetic_call):
        run_gap_analysis(**analyzer_kwargs(FIXTURE))
    write_json(
        FIXTURE / "mocked_analyzer_response.json",
        {
            "_meta": {
                "captured_at": FIXED_NOW.isoformat(),
                "contains_real_client_data": False,
                "live_capture": False,
                "provenance": "synthetic_offline_characterization",
                "warning": "This is not a recorded Claude response.",
            },
            "calls": calls,
        },
    )


def _capture_analyzer(live: bool) -> dict:
    kwargs = analyzer_kwargs(FIXTURE)
    if live:
        if os.environ.get("USE_LIVE_ANALYZER") != "1":
            raise SystemExit("Live capture requires USE_LIVE_ANALYZER=1 as an explicit safety gate.")
        metadata = {
            "captured_at": datetime.now().astimezone().isoformat(),
            "contains_real_client_data": False,
            "live_capture": True,
            "provenance": "genuine_claude_capture",
        }
        # LIVE_CALL: this passthrough is replaced by strict replay in tests.
        with record_live_analyzer(FIXTURE, metadata):
            return run_gap_analysis(**kwargs)

    _write_synthetic_recording()
    with with_recorded_analyzer(FIXTURE):
        return run_gap_analysis(**kwargs)


def _score(assessment_id: str, session):
    from app.services import scoring

    result = scoring.score(assessment_id, ["dpdpa"], _session=session)
    return result.model_dump(mode="json") if hasattr(result, "model_dump") else result


def capture(live: bool) -> None:
    bootstrap_inputs()
    env = read_json(FIXTURE / "env.json")
    os.environ.update(env)
    settings.firm_name = env["FIRM_NAME"]
    settings.firm_logo_path = env["FIRM_LOGO_PATH"] or None
    settings.firm_primary_hex = env["FIRM_PRIMARY_HEX"]
    db_path = FIXTURE / ".capture.sqlite3"
    if db_path.exists():
        db_path.unlink()
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        assessment = seed_assessment(session, FIXTURE)
        write_json(
            EXPECTED / "screening_output.json",
            json.loads(assessment.screening_results or "{}"),
        )
        analyzer_output = _capture_analyzer(live)
        write_json(EXPECTED / "analyzer_output.json", analyzer_output)
        report, gap_items = materialize_report(session, assessment, analyzer_output)
        write_json(EXPECTED / "score.json", _score(assessment.id, session))
        with patch("app.utils.pdf_export.datetime", _FixedDatetime):
            pdf_bytes = generate_pdf(
                report,
                gap_items,
                assessment.company_name,
                initiatives=[],
                selected_frameworks=["dpdpa"],
            )
    finally:
        session.close()
        engine.dispose()
        db_path.unlink(missing_ok=True)

    rendered_path = FIXTURE / ".capture.pdf"
    rendered_path.write_bytes(pdf_bytes)
    try:
        text = extract_pdf_text(rendered_path)
        page_logger = logging.getLogger("pdfminer.pdfpage")
        previous_level = page_logger.level
        page_logger.setLevel(logging.ERROR)
        try:
            with pdfplumber.open(rendered_path) as rendered_pdf:
                page_count = len(rendered_pdf.pages)
        finally:
            page_logger.setLevel(previous_level)
    finally:
        rendered_path.unlink(missing_ok=True)
    (EXPECTED / "pdf_text.sha256").write_text(
        hashlib.sha256(text.encode("utf-8")).hexdigest() + "\n",
        encoding="utf-8",
    )
    write_json(
        EXPECTED / "pdf_meta.json",
        {
            "byte_length_lower_bound": int(len(pdf_bytes) * 0.95),
            "page_count": page_count,
        },
    )
    fixture_bytes = sum(path.stat().st_size for path in FIXTURE.rglob("*") if path.is_file())
    print(
        f"Captured {'live' if live else 'synthetic'} DPDPA golden: "
        f"{len(gap_items)} findings, {len(pdf_bytes)} PDF bytes, {fixture_bytes} fixture bytes."
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Record genuine Claude responses (requires USE_LIVE_ANALYZER=1).")
    args = parser.parse_args()
    capture(live=args.live)


if __name__ == "__main__":
    main()
