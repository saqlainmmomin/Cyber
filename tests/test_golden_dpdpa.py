"""Golden characterization tests for the legacy DPDPA-only pipeline."""

from __future__ import annotations

import hashlib
import io
import json
import logging
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pdfplumber
import pytest

from tests.support.analyzer_mock import with_recorded_analyzer
from tests.support.canonical_dpdpa import FIXED_NOW, materialize_report

FIXTURE = Path(__file__).parent / "fixtures" / "canonical_dpdpa"


class _FixedDatetime(datetime):
    @classmethod
    def now(cls, tz=None):
        return FIXED_NOW if tz is not None else FIXED_NOW.replace(tzinfo=None)


@pytest.fixture
def canonical_env(monkeypatch):
    from app.config import settings

    env = json.loads((FIXTURE / "env.json").read_text(encoding="utf-8"))
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(settings, "firm_name", env["FIRM_NAME"])
    monkeypatch.setattr(settings, "firm_logo_path", env["FIRM_LOGO_PATH"] or None)
    monkeypatch.setattr(settings, "firm_primary_hex", env["FIRM_PRIMARY_HEX"])
    return env


def _analyze(canonical):
    from app.services.claude_analyzer import run_gap_analysis

    with with_recorded_analyzer(FIXTURE) as metadata:
        output = run_gap_analysis(**canonical.analyzer_kwargs)
    assert metadata["contains_real_client_data"] is False
    assert metadata["provenance"] in {
        "synthetic_offline_characterization",
        "genuine_claude_capture",
    }
    return output


def _score(assessment_id, session):
    from app.services.scoring import score

    result = score(assessment_id, ["dpdpa"], _session=session)
    return result.model_dump(mode="json") if hasattr(result, "model_dump") else result


def _pdf_bytes(canonical):
    from app.utils.pdf_export import generate_pdf

    analyzer_output = _analyze(canonical)
    report, gap_items = materialize_report(
        canonical.session, canonical.assessment, analyzer_output
    )
    with patch("app.utils.pdf_export.datetime", _FixedDatetime):
        return generate_pdf(
            report,
            gap_items,
            canonical.assessment.company_name,
            initiatives=[],
            selected_frameworks=["dpdpa"],
        )


def _extract_pdf(pdf_bytes: bytes) -> tuple[str, int]:
    page_logger = logging.getLogger("pdfminer.pdfpage")
    previous_level = page_logger.level
    page_logger.setLevel(logging.ERROR)
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages), len(pdf.pages)
    finally:
        page_logger.setLevel(previous_level)


def test_scoring_matches_golden(canonical_dpdpa_assessment, canonical_env):
    analyzer_output = _analyze(canonical_dpdpa_assessment)
    materialize_report(
        canonical_dpdpa_assessment.session,
        canonical_dpdpa_assessment.assessment,
        analyzer_output,
    )
    got = _score(
        canonical_dpdpa_assessment.assessment.id,
        canonical_dpdpa_assessment.session,
    )
    expected = json.loads((FIXTURE / "expected" / "score.json").read_text())
    assert got == expected


def test_analyzer_output_matches_golden(canonical_dpdpa_assessment, canonical_env):
    expected_screening = json.loads(
        (FIXTURE / "expected" / "screening_output.json").read_text(encoding="utf-8")
    )
    assert json.loads(canonical_dpdpa_assessment.assessment.screening_results) == expected_screening
    got = _analyze(canonical_dpdpa_assessment)
    expected = json.loads(
        (FIXTURE / "expected" / "analyzer_output.json").read_text(encoding="utf-8")
    )
    assert got == expected


def test_pdf_text_matches_golden(canonical_dpdpa_assessment, canonical_env):
    pdf_bytes = _pdf_bytes(canonical_dpdpa_assessment)
    text, _ = _extract_pdf(pdf_bytes)
    got = hashlib.sha256(text.encode("utf-8")).hexdigest()
    expected = (FIXTURE / "expected" / "pdf_text.sha256").read_text().strip()
    assert got == expected


def test_pdf_meta_matches_golden(canonical_dpdpa_assessment, canonical_env):
    pdf_bytes = _pdf_bytes(canonical_dpdpa_assessment)
    _, page_count = _extract_pdf(pdf_bytes)
    meta = json.loads((FIXTURE / "expected" / "pdf_meta.json").read_text())
    assert page_count == meta["page_count"]
    assert len(pdf_bytes) >= meta["byte_length_lower_bound"]


def test_missing_analyzer_recording_fails_before_any_live_call(tmp_path):
    from app.services import claude_analyzer

    with patch.object(
        claude_analyzer.anthropic,
        "Anthropic",
        side_effect=AssertionError("live transport must not be constructed"),
    ):
        with pytest.raises(AssertionError, match="recording missing"):
            with with_recorded_analyzer(tmp_path):
                pass


def test_uncached_optional_call_is_not_swallowed(tmp_path):
    from app.services.claude_analyzer import _run_evidence_extraction

    (tmp_path / "mocked_analyzer_response.json").write_text(
        json.dumps(
            {
                "_meta": {"provenance": "test", "contains_real_client_data": False},
                "calls": {},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(AssertionError, match="Replay refused to fall back"):
        with with_recorded_analyzer(tmp_path):
            assert _run_evidence_extraction(
                [{"filename": "synthetic.txt", "category": "other", "text": "fake"}]
            ) is None


def test_analyzer_call_seam_normalizes_create_and_stream(monkeypatch):
    from app.services import claude_analyzer

    usage = SimpleNamespace(input_tokens=12, output_tokens=7)
    message = SimpleNamespace(content=[SimpleNamespace(text='{"ok":true}')], usage=usage)

    class FakeStream:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def get_final_text(self):
            return '{"streamed":true}'

        def get_final_message(self):
            return message

    messages = SimpleNamespace(
        create=lambda **_kwargs: message,
        stream=lambda **_kwargs: FakeStream(),
    )
    monkeypatch.setattr(
        claude_analyzer.anthropic,
        "Anthropic",
        lambda **_kwargs: SimpleNamespace(messages=messages),
    )
    request = {"model": "fixture", "max_tokens": 1, "messages": []}
    assert claude_analyzer._call_claude(**request) == {
        "text": '{"ok":true}',
        "usage": {
            "input_tokens": 12,
            "output_tokens": 7,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0,
        },
    }
    assert claude_analyzer._call_claude(stream=True, **request)["text"] == '{"streamed":true}'
