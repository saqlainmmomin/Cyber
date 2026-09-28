"""Contract tests for P6-8 B2: DOCX and XLSX derived from a board report version's JSON sidecar.

Handoff: tasks/handoffs/2026-09-28-p6-8-b2-docx-xlsx.md. B1 (the board report snapshot and its
hashed sidecar) is merged; B2 renders editable DOCX and XLSX files from that stored document
only, on request, and never stores them. Written before the implementation: on `main` these fail
because `app.services.board_exports`, the two routes and the `openpyxl` pin do not exist yet.

No network, no LLM and no WeasyPrint: the board PDF renderer is faked, because B2 never renders
a PDF and must not depend on Pango being installed.
"""

from __future__ import annotations

import importlib
import io
import json
import re
import subprocess
import time
import urllib.parse
import zipfile
from datetime import date, datetime

import pytest

from app.models.assessment import Assessment
from app.models.audit_event import AuditEvent
from app.models.conclusion import Conclusion
from app.models.report_snapshot import ReportSnapshot
from app.services import report_snapshots

# Fixtures and helpers are shared with the B1 contract suite so both run on the same data.
from tests.test_p6_8_board_report_v2 import (  # noqa: F401  (pytest fixtures are used by name)
    DEVANAGARI_COMPANY,
    FIXED_GENERATED_AT,
    NON_LEGAL_FORBIDDEN,
    REPO_ROOT,
    RUPEE_TEXT,
    _decide,
    _document,
    _engagement_fixture,
    _evidence,
    _files_state,
    _generate,
    _no_llm,
    _register_frameworks,
    _seed,
    db,
    db_path,
    engine,
    gate,
    http,
    upload_root,
)

OPENPYXL_PIN = "openpyxl==3.1.5"
DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
LABEL = (
    "Derived from board report snapshot {id8}, {version} (document SHA-256 {prefix}). "
    "Edits to this file do not change the report version it was derived from."
)
XLSX_SHEETS = (
    "About",
    "Framework summary",
    "Requirement register",
    "Top risks",
    "Action tracker",
    "Evidence register",
)
XLSX_COLUMNS = {
    "Framework summary": (
        "Framework", "Version", "Score (%)", "Rating", "Headline", "In scope", "Compliant",
        "Partially compliant", "Non-compliant", "Insufficient evidence", "Not applicable",
    ),
    "Requirement register": (
        "Framework", "Requirement ID", "Requirement", "Domain", "Outcome", "Risk", "Priority",
        "Decision", "Decided by", "Decided on", "Evidence citation",
    ),
    "Top risks": (
        "Rank", "Finding", "Description", "Severity", "Priority", "Framework", "Requirement ID",
        "Requirement", "Outcome", "Cited evidence", "Owner", "Target date", "Action",
    ),
    "Action tracker": (
        "Action", "Owner", "Target date", "Status", "Framework", "Requirement ID", "Finding",
        "Client update", "Evidence of closure",
    ),
    "Evidence register": ("File", "Version", "SHA-256 prefix", "Added on", "Status", "Cited"),
}
ABOUT_KEYS = (
    "Company",
    "Engagement",
    "Frameworks",
    "Assessment period",
    "Evidence cut-off",
    "Report version",
    "Snapshot ID",
    "Report generated",
    "Document SHA-256",
    "Document schema version",
    "Export format version",
)
DOCX_TABLE_HEADERS = {
    "scores": (
        "Framework", "Headline", "In scope", "Compliant", "Partial", "Non-compliant",
        "Insufficient evidence", "Not applicable",
    ),
    "roadmap": ("Action", "Owner", "Target date", "Status", "Closes"),
    "domains": ("Domain", "Score", "Rating"),
    "gaps": ("Requirement", "Outcome", "Risk", "Priority"),
    "requirement_register": (
        "Framework", "Requirement", "Outcome", "Risk", "Priority", "Decision", "Decided by",
        "Decided on", "Citation",
    ),
    "evidence_register": ("File", "Version", "Added", "Status", "SHA-256", "Cited"),
}
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")
FAKE_RENDERER = "weasyprint 70.0"


def _exports():
    """Import lazily so each test fails on its own before implementation."""
    return importlib.import_module("app.services.board_exports")


def _board():
    return importlib.import_module("app.services.board_report")


@pytest.fixture()
def fake_pdf(monkeypatch):
    """B2 never renders a PDF; fake B1's renderer so generation needs no Pango."""
    from app.utils import html_pdf

    board = _board()

    def _render_pdf(document):
        return b"%PDF-1.7\n% fake board report " + document["snapshot"]["version_label"].encode() + b"\n%%EOF\n"

    monkeypatch.setattr(board, "render_pdf", _render_pdf)
    monkeypatch.setattr(html_pdf, "renderer_label", lambda: FAKE_RENDERER)


def _version(db, http, gate, monkeypatch, **kwargs):
    """A released fixture plus one generated board report version, read back from its sidecar."""
    assessment, conclusions, dp, iso = _engagement_fixture(db, http, gate, monkeypatch, **kwargs)
    response = _generate(http, assessment)
    assert response.status_code == 200, response.text
    snapshot = db.get(ReportSnapshot, response.json()["snapshot_id"])
    document = report_snapshots.read_board_report_document(db, snapshot)
    sha = report_snapshots.generated_event(db, snapshot.id)["document_sha256"]
    return assessment, snapshot, document, sha, conclusions, dp


def _get(http, assessment_id, snapshot_id, fmt):
    return http.get(f"/api/assessments/{assessment_id}/snapshots/{snapshot_id}/{fmt}")


def _label(document, sha):
    return LABEL.format(id8=document["snapshot"]["id"][:8], version=document["snapshot"]["version_label"], prefix=sha[:12])


def _s(value) -> str:
    return "" if value is None else str(value)


def _docx(content: bytes):
    import docx

    return docx.Document(io.BytesIO(content))


def _xlsx(content: bytes):
    from openpyxl import load_workbook

    return load_workbook(io.BytesIO(content))


def _docx_text(document) -> list[str]:
    texts = [paragraph.text for paragraph in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            texts.extend(cell.text for cell in row.cells)
    for section in document.sections:
        texts.extend(paragraph.text for paragraph in section.header.paragraphs)
        texts.extend(paragraph.text for paragraph in section.footer.paragraphs)
    return texts


def _xlsx_strings(workbook) -> list[str]:
    return [
        cell.value
        for sheet in workbook.worksheets
        for row in sheet.iter_rows()
        for cell in row
        if isinstance(cell.value, str)
    ]


def _table(document, headers):
    matches = [table for table in document.tables if tuple(cell.text for cell in table.rows[0].cells) == headers]
    assert len(matches) >= 1, f"no table with headers {headers}"
    return matches


def _body_rows(table) -> list[list[str]]:
    return [[cell.text for cell in row.cells] for row in table.rows[1:]]


def _sheet_rows(sheet) -> list[list]:
    def _norm(value):
        if isinstance(value, datetime):
            return value.date().isoformat()
        if isinstance(value, date):
            return value.isoformat()
        return value

    return [[_norm(cell.value) for cell in row] for row in sheet.iter_rows(min_row=2)]


def _framework_names(document) -> dict[str, str]:
    return {framework["framework_id"]: framework["name"] for framework in document["frameworks"]}


# ---------------------------------------------------------------------------
# 1. Dependency pin and module surface
# ---------------------------------------------------------------------------


def test_scenario_1_openpyxl_is_pinned_and_the_exporters_take_only_the_document():
    """Scenario 1 (D-P6-8-B2-A/C): openpyxl pinned; renderers are pure functions of (document, sha)."""
    import inspect

    assert OPENPYXL_PIN in (REPO_ROOT / "requirements.txt").read_text().splitlines()
    import openpyxl

    assert openpyxl.__version__ == "3.1.5"

    exports = _exports()
    assert exports.EXPORT_FORMAT_VERSION == 1
    assert exports.SUPPORTED_SCHEMA_VERSIONS == (1,)
    assert exports.DOCX_MEDIA_TYPE == DOCX_MEDIA_TYPE
    assert exports.XLSX_MEDIA_TYPE == XLSX_MEDIA_TYPE
    assert exports.XLSX_SHEETS == XLSX_SHEETS
    assert exports.XLSX_COLUMNS == XLSX_COLUMNS
    assert exports.DOCX_TABLE_HEADERS == DOCX_TABLE_HEADERS
    assert exports.FORMULA_PREFIXES == FORMULA_PREFIXES
    assert issubclass(exports.UnsupportedDocument, report_snapshots.SnapshotError)
    assert exports.UnsupportedDocument.status_code == 409
    for name in ("render_docx", "render_xlsx"):
        parameters = inspect.signature(getattr(exports, name)).parameters
        assert list(parameters) == ["document", "document_sha256"], name
        assert parameters["document_sha256"].kind is inspect.Parameter.KEYWORD_ONLY, name


# ---------------------------------------------------------------------------
# 2-3. Content equals the stored document
# ---------------------------------------------------------------------------


def test_scenario_2_docx_mirrors_the_board_report_sections_and_the_document(db, http, gate, monkeypatch, fake_pdf):
    """Scenario 2 (D-P6-8-B2-D): same headings and order as the PDF, Word styles, exact Devanagari and rupee."""
    board = _board()
    assessment, snapshot, document, sha, *_ = _version(db, http, gate, monkeypatch)

    response = _get(http, assessment.id, snapshot.id, "docx")
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == DOCX_MEDIA_TYPE
    assert response.headers["X-Board-Document-Sha256"] == sha
    assert response.headers["X-Board-Export-Format-Version"] == "1"
    expected_name = f"{DEVANAGARI_COMPANY}_board_report_v1_{snapshot.id[:8]}.docx"
    disposition = response.headers["content-disposition"]
    assert disposition.startswith("attachment; ")
    assert "filename*=UTF-8''" + urllib.parse.quote(expected_name, safe="") in disposition

    word = _docx(response.content)
    paragraphs = [paragraph.text for paragraph in word.paragraphs]
    label = _label(document, sha)

    headings = [paragraph.text for paragraph in word.paragraphs if paragraph.style.name == "Heading 1"]
    assert headings == [
        "Management summary",
        "Top risks",
        "Remediation roadmap",
        "What we could not assess",
        *[f"{section['name']} ({section['version']})" for section in document["framework_sections"]],
        "Sign-off",
        "Appendix A: Methodology",
        "Appendix B: Requirement register",
        "Appendix C: Evidence register",
    ]
    assert [p.text for p in word.paragraphs if p.style.name == "Title"] == ["Board report"]
    assert paragraphs.count(label) == 1
    assert paragraphs.index(label) < paragraphs.index("Management summary")
    assert word.core_properties.comments == label
    assert word.core_properties.title == f"Board report: {DEVANAGARI_COMPANY}"
    assert word.core_properties.author == document["firm_name"]
    assert word.core_properties.identifier == snapshot.id

    # Devanagari and the rupee sign round-trip exactly (DOCX is text, not glyphs).
    assert DEVANAGARI_COMPANY in paragraphs
    assert RUPEE_TEXT in paragraphs
    everything = "\n".join(_docx_text(word))
    assert "�" not in everything and "Rs." not in everything
    assert f"Version v1 | Snapshot {snapshot.id[:8]}" in paragraphs
    assert f"Assessment period: {document['basis']['period_label']} | Evidence cut-off: {document['basis']['cutoff_label']}" in paragraphs
    assert document["sign_off"]["issue_status"] in paragraphs
    for risk in document["top_risks"]:
        assert f"{risk['rank']}. {risk['title']}" in [p.text for p in word.paragraphs if p.style.name == "Heading 2"]
        for citation in risk["citations"]:
            assert (
                f"{citation['filename']} v{citation['version_number']}, {citation['location_ref']} "
                f"(SHA-256 {citation['sha256_prefix']})"
            ) in paragraphs

    # Complex-script font for Devanagari is named on the Normal style; nothing is embedded.
    styles_xml = zipfile.ZipFile(io.BytesIO(response.content)).read("word/styles.xml").decode("utf-8")
    assert 'w:cs="Noto Sans Devanagari"' in styles_xml
    assert 'w:ascii="Noto Sans"' in styles_xml
    assert not any(name.startswith("word/fonts/") for name in zipfile.ZipFile(io.BytesIO(response.content)).namelist())

    # Tables equal the document, row for row.
    (register,) = _table(word, DOCX_TABLE_HEADERS["requirement_register"])
    assert _body_rows(register) == [
        [
            row["framework_id"],
            f"{row['requirement_id']}: {row['requirement_title']}",
            row["outcome_label"],
            _s(row["risk_level"]),
            _s(row["priority"]),
            row["decision_label"],
            _s(row["decided_by"]),
            board.display_date(row["decided_on"]) if row["decided_on"] else "Not recorded",
            row["citation"] or row["citation_note"],
        ]
        for row in document["appendices"]["requirement_register"]
    ]
    (evidence,) = _table(word, DOCX_TABLE_HEADERS["evidence_register"])
    assert _body_rows(evidence) == [
        [
            row["filename"],
            f"v{row['version_number']}",
            board.display_date(row["added_on"]) if row["added_on"] else "Not recorded",
            row["status"],
            row["sha256_prefix"],
            "Yes" if row["cited"] else "No",
        ]
        for row in document["appendices"]["evidence_register"]
    ]
    assert "rejected-scan.pdf" not in everything
    (roadmap,) = _table(word, DOCX_TABLE_HEADERS["roadmap"])
    assert _body_rows(roadmap) == [
        [
            action["title"],
            action["owner"] or "Unassigned",
            board.display_date(action["target_date"]) if action["target_date"] else "No target date",
            action["status_label"],
            "; ".join(f"{c['framework_name']}: {c['requirement_id']} ({c['finding_title']})" for c in action["closes"]),
        ]
        for action in document["roadmap"]["actions"]
    ]
    (scores,) = _table(word, DOCX_TABLE_HEADERS["scores"])
    assert [row[:3] for row in _body_rows(scores)] == [
        [framework["name"], framework["headline"], str(framework["coverage"]["in_scope"])]
        for framework in document["summary"]["frameworks"]
    ]
    assert len(_table(word, DOCX_TABLE_HEADERS["domains"])) == len(document["framework_sections"])


def test_scenario_3_xlsx_sheets_columns_and_rows_equal_the_document(db, http, gate, monkeypatch, fake_pdf):
    """Scenario 3 (D-P6-8-B2-E): six sheets, pinned columns, frozen bold filtered headers, typed cells, no formulas."""
    assessment, snapshot, document, sha, *_ = _version(db, http, gate, monkeypatch)
    response = _get(http, assessment.id, snapshot.id, "xlsx")
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == XLSX_MEDIA_TYPE
    assert response.headers["X-Board-Document-Sha256"] == sha
    expected_name = f"{DEVANAGARI_COMPANY}_board_report_v1_{snapshot.id[:8]}.xlsx"
    assert "filename*=UTF-8''" + urllib.parse.quote(expected_name, safe="") in response.headers["content-disposition"]

    book = _xlsx(response.content)
    assert tuple(book.sheetnames) == XLSX_SHEETS
    names = _framework_names(document)

    about = book["About"]
    assert about["A1"].value == _label(document, sha)
    about_rows = {row[0].value: row[1].value for row in about.iter_rows(min_row=3) if row[0].value}
    assert tuple(about_rows) == ABOUT_KEYS
    assert about_rows["Company"] == DEVANAGARI_COMPANY
    assert about_rows["Snapshot ID"] == snapshot.id
    assert about_rows["Report version"] == "v1"
    assert about_rows["Document SHA-256"] == sha
    assert about_rows["Report generated"] == document["snapshot"]["generated_at"]
    assert about_rows["Document schema version"] == 1
    assert about_rows["Export format version"] == 1
    assert about_rows["Assessment period"] == document["basis"]["period_label"]
    assert about_rows["Evidence cut-off"] == document["basis"]["cutoff_label"]
    assert book.properties.description == _label(document, sha)
    assert book.properties.identifier == snapshot.id
    assert book.properties.creator == document["firm_name"]

    for sheet_name, columns in XLSX_COLUMNS.items():
        sheet = book[sheet_name]
        assert tuple(cell.value for cell in sheet[1]) == columns, sheet_name
        assert all(cell.font.b for cell in sheet[1]), sheet_name
        assert sheet.freeze_panes == "A2", sheet_name
        assert sheet.auto_filter.ref == sheet.dimensions, sheet_name

    assert _sheet_rows(book["Requirement register"]) == [
        [
            names[row["framework_id"]], row["requirement_id"], row["requirement_title"], row["domain_title"],
            row["outcome_label"], row["risk_level"], row["priority"], row["decision_label"], row["decided_by"],
            row["decided_on"], row["citation"] or row["citation_note"],
        ]
        for row in document["appendices"]["requirement_register"]
    ]
    assert _sheet_rows(book["Top risks"]) == [
        [
            risk["rank"], risk["title"], risk["description"], risk["severity"], risk["priority"],
            risk["framework_name"], risk["requirement_id"], risk["requirement_title"], risk["outcome_label"],
            "; ".join(
                f"{c['filename']} v{c['version_number']}, {c['location_ref']} (SHA-256 {c['sha256_prefix']})"
                for c in risk["citations"]
            ) or None,
            risk["owner"], risk["target_date"], risk["action_title"],
        ]
        for risk in document["top_risks"]
    ]
    assert _sheet_rows(book["Action tracker"]) == [
        [
            action["title"], action["owner"], action["target_date"], action["status_label"],
            "; ".join(c["framework_name"] for c in action["closes"]),
            "; ".join(c["requirement_id"] for c in action["closes"]),
            "; ".join(c["finding_title"] for c in action["closes"]),
            None, None,
        ]
        for action in document["roadmap"]["actions"]
    ]
    assert _sheet_rows(book["Evidence register"]) == [
        [row["filename"], row["version_number"], row["sha256_prefix"], row["added_on"], row["status"], "Yes" if row["cited"] else "No"]
        for row in document["appendices"]["evidence_register"]
    ]
    summary = _sheet_rows(book["Framework summary"])
    assert [row[:5] for row in summary] == [
        [
            framework["name"],
            next(f["version"] for f in document["frameworks"] if f["framework_id"] == framework["framework_id"]),
            framework["score"], framework["rating"], framework["headline"],
        ]
        for framework in document["summary"]["frameworks"]
    ]
    assert [row[5:] for row in summary] == [
        [framework["coverage"][key] for key in ("in_scope", "compliant", "partially_compliant", "non_compliant", "insufficient_evidence", "not_applicable")]
        for framework in document["summary"]["frameworks"]
    ]

    # Target dates are real date cells, so the client can sort and filter the tracker.
    tracker = book["Action tracker"]
    assert isinstance(tracker.cell(row=2, column=3).value, datetime)
    assert tracker.cell(row=2, column=3).number_format == "yyyy-mm-dd"
    assert RUPEE_TEXT in _xlsx_strings(book)
    archive = zipfile.ZipFile(io.BytesIO(response.content))
    for name in archive.namelist():
        if name.startswith("xl/worksheets/"):
            xml = archive.read(name).decode("utf-8")
            assert "<f>" not in xml and "<f " not in xml, name


# ---------------------------------------------------------------------------
# 4. Only the stored document is read
# ---------------------------------------------------------------------------


def test_scenario_4_exports_read_only_the_stored_document(db, http, gate, monkeypatch, upload_root, fake_pdf):
    """Scenario 4 (D-P6-8-B2-B): live data changes and a patched builder change nothing; exports write nothing."""
    from app.services import approved_report, report_basis, report_content

    assessment, snapshot, document, sha, conclusions, dp = _version(db, http, gate, monkeypatch)
    before = {fmt: _get(http, assessment.id, snapshot.id, fmt) for fmt in ("docx", "xlsx")}
    for response in before.values():
        assert response.status_code == 200, response.text
    pdf_hash = report_snapshots.generated_event(db, snapshot.id)["sha256"]

    def _explode(*_args, **_kwargs):
        raise AssertionError("B2 read live data or re-rendered the report")

    board = _board()
    for module, name in (
        (board, "build_document"),
        (board, "render_pdf"),
        (board, "render_html"),
        (approved_report, "build_approved_report"),
        (report_content, "assessment_findings"),
        (report_basis, "current_basis"),
    ):
        monkeypatch.setattr(module, name, _explode)

    # Change live data: rename the client, reopen an approved conclusion, add evidence.
    live = db.get(Assessment, assessment.id)
    live.company_name = "Renamed Private Limited"
    _decide(db, db.get(Conclusion, conclusions[("dpdpa", dp[1])].id), "reopened")
    _evidence(db, live, "late-upload.pdf", "d")
    db.commit()

    audit_count = db.query(AuditEvent).count()
    files = _files_state(db, upload_root)
    for fmt, original in before.items():
        again = _get(http, assessment.id, snapshot.id, fmt)
        assert again.status_code == 200, (fmt, again.text)
        assert again.content == original.content, fmt
        assert again.headers["content-disposition"] == original.headers["content-disposition"], fmt
    assert db.query(AuditEvent).count() == audit_count
    assert _files_state(db, upload_root) == files
    served = http.get(f"/api/assessments/{assessment.id}/snapshots/{snapshot.id}/file")
    assert served.status_code == 200
    assert served.headers["X-Snapshot-Sha256"] == pdf_hash
    assert "Renamed Private Limited" not in "\n".join(_docx_text(_docx(before["docx"].content)))


# ---------------------------------------------------------------------------
# 5. Deterministic bytes
# ---------------------------------------------------------------------------


def test_scenario_5_bytes_are_deterministic_and_pinned_to_generated_at(db, http, gate, monkeypatch, fake_pdf):
    """Scenario 5 (D-P6-8-B2-F): same document, same bytes, whatever the wall clock; zip and core dates pinned."""
    exports = _exports()
    assessment, snapshot, *_ = _version(db, http, gate, monkeypatch)
    for fmt in ("docx", "xlsx"):
        first = _get(http, assessment.id, snapshot.id, fmt)
        second = _get(http, assessment.id, snapshot.id, fmt)
        assert first.status_code == 200 and first.content == second.content, fmt

    document = _document(db, assessment)  # generated_at = FIXED_GENERATED_AT
    sha = "ab" * 32
    stamp = FIXED_GENERATED_AT.timetuple()[:6]
    real_time = time.time
    for render in (exports.render_docx, exports.render_xlsx):
        first = render(document, document_sha256=sha)
        time.sleep(1.05)  # cross a second boundary: openpyxl stamps core.xml `modified` with now()
        monkeypatch.setattr(time, "time", lambda: real_time() + 3600)
        second = render(document, document_sha256=sha)
        monkeypatch.setattr(time, "time", real_time)
        assert first == second, render.__name__
        archive = zipfile.ZipFile(io.BytesIO(first))
        assert archive.testzip() is None
        assert all(info.date_time == stamp for info in archive.infolist()), render.__name__
        core = archive.read("docProps/core.xml").decode("utf-8")
        for element in ("created", "modified"):
            match = re.search(rf"<dcterms:{element}\b[^>]*>([^<]*)</dcterms:{element}>", core)
            assert match and match.group(1) == "2026-09-28T10:00:00Z", (render.__name__, element, core)

    word = _docx(exports.render_docx(document, document_sha256=sha)).core_properties
    assert word.created.replace(tzinfo=None) == datetime(2026, 9, 28, 10, 0)
    assert word.modified.replace(tzinfo=None) == datetime(2026, 9, 28, 10, 0)
    assert word.revision == 1
    assert word.last_modified_by == document["firm_name"]
    book = _xlsx(exports.render_xlsx(document, document_sha256=sha)).properties
    assert book.created == datetime(2026, 9, 28, 10, 0)
    assert book.modified == datetime(2026, 9, 28, 10, 0)
    assert book.lastModifiedBy == document["firm_name"]


# ---------------------------------------------------------------------------
# 6. Errors: wrong type, wrong assessment, tampered or unsupported document
# ---------------------------------------------------------------------------


def test_scenario_6_only_intact_board_report_versions_export(db, http, gate, monkeypatch, upload_root, fake_pdf):
    """Scenario 6 (D-P6-8-B2-G): 404 for other types and assessments; 500 when tampered; 409 when unsupported."""
    exports = _exports()
    assessment, snapshot, document, sha, *_ = _version(db, http, gate, monkeypatch)
    other_types = {kind: _generate(http, assessment, kind).json()["snapshot_id"] for kind in ("gap_report", "workpaper")}
    stranger = _seed(db, frameworks=["dpdpa"], applicable=[], company="Other Co")

    for fmt in ("docx", "xlsx"):
        missing_assessment = _get(http, "no-such-assessment", snapshot.id, fmt)
        assert missing_assessment.status_code == 404
        assert missing_assessment.json()["detail"] == "Assessment not found"
        for snapshot_id in ("no-such-version", *other_types.values()):
            refused = _get(http, assessment.id, snapshot_id, fmt)
            assert refused.status_code == 404, (fmt, snapshot_id)
            assert refused.json()["detail"] == "Report version not found."
            assert refused.headers["X-Toast-Type"] == "error"
        assert _get(http, stranger.id, snapshot.id, fmt).status_code == 404

    sidecar = upload_root / f"reports/assessments/{assessment.id}/{snapshot.id}.json"
    original = sidecar.read_bytes()
    sidecar.write_bytes(original.replace(b'"v1"', b'"v9"'))
    for fmt in ("docx", "xlsx"):
        tampered = _get(http, assessment.id, snapshot.id, fmt)
        assert tampered.status_code == 500, fmt
        assert tampered.json()["detail"] == report_snapshots.INTEGRITY_MESSAGE
    sidecar.unlink()
    assert _get(http, assessment.id, snapshot.id, "docx").status_code == 500
    sidecar.write_bytes(original)
    assert _get(http, assessment.id, snapshot.id, "docx").status_code == 200

    # A hash-valid document of an unknown schema is refused, never half-rendered.
    future = dict(document, schema_version=99)
    for render in (exports.render_docx, exports.render_xlsx):
        with pytest.raises(exports.UnsupportedDocument) as raised:
            render(future, document_sha256=sha)
        assert raised.value.message == exports.UNSUPPORTED_DOCUMENT_MESSAGE
    future_bytes = _board().canonical_bytes(future)
    sidecar.write_bytes(future_bytes)
    event = (
        db.query(AuditEvent)
        .filter_by(entity_id=snapshot.id, action=report_snapshots.GENERATED_ACTION)
        .one()
    )
    metadata = json.loads(event.metadata_json)
    import hashlib

    metadata["document_sha256"] = hashlib.sha256(future_bytes).hexdigest()
    event.metadata_json = json.dumps(metadata)
    db.commit()
    for fmt in ("docx", "xlsx"):
        unsupported = _get(http, assessment.id, snapshot.id, fmt)
        assert unsupported.status_code == 409, fmt
        assert unsupported.json()["detail"] == exports.UNSUPPORTED_DOCUMENT_MESSAGE


# ---------------------------------------------------------------------------
# 7. Formula injection and XML-illegal characters
# ---------------------------------------------------------------------------


def test_scenario_7_formula_prefixes_are_text_and_illegal_characters_are_dropped(db, http, gate, monkeypatch):
    """Scenario 7 (D-P6-8-B2-H): user text starting with = + - @ tab CR is stored as quoted text, never a formula."""
    exports = _exports()
    assessment, *_ = _engagement_fixture(db, http, gate, monkeypatch)
    document = _document(db, assessment)
    hostile = {
        "company": "=cmd|' /C calc'!A0",
        "title": '=HYPERLINK("http://example.invalid","click")',
        "owner": "+SUM(1,2)",
        "description": "-2+3 overdue",
        "action": "@evil",
    }
    document["company_name"] = hostile["company"]
    risk = document["top_risks"][0]
    risk.update(title=hostile["title"], owner=hostile["owner"], description=hostile["description"], action_title=hostile["action"])
    document["roadmap"]["actions"][0]["owner"] = hostile["owner"]
    register = document["appendices"]["requirement_register"]
    register[0]["requirement_title"] = "\tTabbed title"
    register[1]["requirement_title"] = "Vertical\x0btab and NUL\x00 removed"

    content = exports.render_xlsx(document, document_sha256="cd" * 32)
    archive = zipfile.ZipFile(io.BytesIO(content))
    for name in archive.namelist():
        if name.startswith("xl/worksheets/"):
            xml = archive.read(name).decode("utf-8")
            assert "<f>" not in xml and "<f " not in xml, name
    book = _xlsx(content)
    seen = set()
    for sheet in book.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                if isinstance(cell.value, str) and cell.value.startswith(FORMULA_PREFIXES):
                    assert cell.data_type == "s", (sheet.title, cell.coordinate)
                    assert cell.quotePrefix is True, (sheet.title, cell.coordinate, cell.value)
                    seen.add(cell.value)
                elif isinstance(cell.value, str):
                    assert cell.quotePrefix is not True, (sheet.title, cell.coordinate, cell.value)
    # Text is kept as written (no visible apostrophe), only typed and flagged as text.
    assert {hostile["company"], hostile["title"], hostile["owner"], hostile["description"], hostile["action"]} <= seen
    assert "Verticaltab and NUL removed" in _xlsx_strings(book)
    assert book["Requirement register"].cell(row=2, column=7).data_type == "n"  # priority stays a number

    word = _docx(exports.render_docx(document, document_sha256="cd" * 32))
    text = "\n".join(_docx_text(word))
    assert "Verticaltab and NUL removed" in text
    assert hostile["title"] in text  # DOCX has no formulas; the text is unchanged


# ---------------------------------------------------------------------------
# 8. Versions page links
# ---------------------------------------------------------------------------


def test_scenario_8_versions_page_links_exports_on_board_report_rows_only(db, http, gate, monkeypatch, fake_pdf):
    """Scenario 8 (D-P6-8-B2-G): DOCX and XLSX links on each board_report row, nowhere else."""
    assessment, first, *_ = _version(db, http, gate, monkeypatch)
    second = _generate(http, assessment).json()["snapshot_id"]
    others = [_generate(http, assessment, kind).json()["snapshot_id"] for kind in ("gap_report", "workpaper")]
    page = http.get(f"/assessments/{assessment.id}/snapshots")
    assert page.status_code == 200
    for fmt in ("docx", "xlsx"):
        assert page.text.count(f'data-board-export="{fmt}"') == 2, fmt
        for snapshot_id in (first.id, second):
            assert f"/api/assessments/{assessment.id}/snapshots/{snapshot_id}/{fmt}" in page.text
        for snapshot_id in others:
            assert f"/snapshots/{snapshot_id}/{fmt}" not in page.text


# ---------------------------------------------------------------------------
# 9. Framework-conditional copy survives the export
# ---------------------------------------------------------------------------


def test_scenario_9_exports_add_no_framework_copy_of_their_own(db, http, gate, monkeypatch, fake_pdf):
    """Scenario 9 (D-P6-8-B2-D): an ISO-only export carries no DPDPA or legal wording."""
    assessment, snapshot, *_ = _version(db, http, gate, monkeypatch, frameworks=("iso27001",))
    docx_text = "\n".join(_docx_text(_docx(_get(http, assessment.id, snapshot.id, "docx").content))).lower()
    xlsx_text = "\n".join(_xlsx_strings(_xlsx(_get(http, assessment.id, snapshot.id, "xlsx").content))).lower()
    for phrase in NON_LEGAL_FORBIDDEN:
        assert phrase not in docx_text, phrase
        assert phrase not in xlsx_text, phrase
    assert "certification" in docx_text


# ---------------------------------------------------------------------------
# 10. No LLM, no live readers, and the B2 file set
# ---------------------------------------------------------------------------

P6_8_B2_APP_ALLOWLIST = (
    "app/services/board_exports.py",
    "app/routers/snapshots.py",
    "app/templates/pages/report_snapshots.html",
)
P6_8_B2_FORBIDDEN_PATHS = (
    # B1's frozen surfaces: the document builder, snapshot storage, renderer, templates, fonts, golden.
    "app/services/board_report.py", "app/services/report_snapshots.py", "app/utils/html_pdf.py",
    "app/services/standalone_workpaper.py", "app/templates/reports", "app/assets", "tests/golden",
    # fpdf2 reports and the RFI (P6-7b owns RFI changes).
    "app/utils/pdf_export.py", "app/utils/rfi_export.py", "app/routers/reports.py",
    "app/routers/integrated_reports.py", "app/services/rfi_requests.py",
    # Live report readers: B2 must never need them.
    "app/services/approved_report.py", "app/services/report_content.py", "app/services/report_basis.py",
    "app/services/workpaper.py", "app/services/findings.py", "app/services/conclusion_review.py",
    # Analyzer, LLM, schema, app wiring, fixtures, scripts, answer keys.
    "app/services/claude_analyzer.py", "app/services/llm_client.py", "app/services/grounding",
    "app/frameworks", "app/dpdpa", "app/models", "app/schemas", "alembic", "app/config.py",
    "app/main.py", "app/routers/web.py", "app/templates/base.html", "app/templates/components",
    "app/templates/partials", "tests/fixtures", "tests/support", "scripts", "validation",
    # Stage C 2026-09-28 harness fix (#81) is on main; a stale local `main` still shows it.
    ":(exclude)scripts/validation/run_company.py",
)
LIVE_READER_TOKENS = (
    "llm_client", "claude_analyzer", "services.grounding", "call_llm", "openai",
    "build_document", "approved_report", "report_content", "report_basis", "conclusion_review",
    "workpaper", "from app.models", "Session",
)


def _git(*args) -> str:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, check=True, capture_output=True, text=True).stdout


def test_scenario_10_no_llm_no_live_readers_and_b2_file_set():
    """Scenario 10 (D-P6-8-B2-I): renderers import nothing live; B2 touches only its own files."""
    exports_path = REPO_ROOT / "app" / "services" / "board_exports.py"
    assert exports_path.exists(), "app/services/board_exports.py is not implemented yet"
    source = exports_path.read_text(encoding="utf-8")
    for token in LIVE_READER_TOKENS:
        assert token not in source, token
    assert re.search(r"^import openpyxl|^from openpyxl", source, re.M) is None, "import openpyxl lazily inside render_xlsx"

    committed = _git("diff", "--name-only", "main...HEAD", "--", *P6_8_B2_FORBIDDEN_PATHS).split()
    working = _git("diff", "--name-only", "HEAD", "--", *P6_8_B2_FORBIDDEN_PATHS).split()
    assert committed == [] and working == [], committed + working

    changed_app = set(_git("diff", "--name-only", "main...HEAD", "--", "app").split())
    changed_app |= set(_git("diff", "--name-only", "HEAD", "--", "app").split())
    changed_app |= set(_git("ls-files", "--others", "--exclude-standard", "app").split())
    outside = sorted(path for path in changed_app if not path.startswith(P6_8_B2_APP_ALLOWLIST))
    assert outside == [], outside

    requirements = _git("diff", "main...HEAD", "--", "requirements.txt")
    added = [line[1:] for line in requirements.splitlines() if line.startswith("+") and not line.startswith("+++")]
    removed = [line[1:] for line in requirements.splitlines() if line.startswith("-") and not line.startswith("---")]
    assert added in ([], [OPENPYXL_PIN]) and removed == [], (added, removed)
