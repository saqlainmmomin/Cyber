"""RFI DOCX renders are byte-identical regardless of wall-clock time.

Regression for the flaky P5-6 scenario 10: python-docx stamped every zip entry
with the current second, so two downloads of one frozen RFI version differed
whenever they straddled a second boundary (common under concurrent suites).
"""

import time
from datetime import datetime, timezone

from app.utils.rfi_export import generate_rfi_docx


def _render(generated_at):
    return generate_rfi_docx(
        title="RFI",
        company_name="Example",
        introduction="Intro",
        evidence_items=[],
        response_instructions="Reply",
        generated_at=generated_at,
        framework_label="DPDPA",
        version_label="v1",
    )


def test_docx_bytes_do_not_depend_on_wall_clock(monkeypatch):
    generated_at = datetime(2026, 9, 27, 10, 30, tzinfo=timezone.utc)
    real_time = time.time
    first = _render(generated_at)
    monkeypatch.setattr(time, "time", lambda: real_time() + 3600)
    second = _render(generated_at)
    assert first == second


def test_docx_without_generated_at_is_still_valid(monkeypatch):
    import io
    import zipfile

    content = _render(None)
    archive = zipfile.ZipFile(io.BytesIO(content))
    assert archive.testzip() is None
    assert all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in archive.infolist())
