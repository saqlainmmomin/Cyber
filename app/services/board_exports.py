"""Derived DOCX and XLSX exports for stored board-report documents."""

from __future__ import annotations

import io
import re
import zipfile
from copy import copy
from datetime import date, datetime, timezone

from app.services import board_report, report_snapshots


EXPORT_FORMAT_VERSION = 1
SUPPORTED_SCHEMA_VERSIONS = (1, 2, 3)
DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
DERIVATION_LABEL = (
    "Derived from board report snapshot {snapshot_id8}, {version_label} (document SHA-256 "
    "{sha_prefix}). Edits to this file do not change the report version it was derived from."
)
UNSUPPORTED_DOCUMENT_MESSAGE = (
    "This report version's document format cannot be exported to DOCX or XLSX "
    "by this version of CyberAssess. The report version is unchanged."
)
DOCX_BODY_FONT = "Noto Sans"
DOCX_COMPLEX_SCRIPT_FONT = "Noto Sans Devanagari"
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")
XLSX_SHEETS = (
    "About",
    "Framework summary",
    "Requirement register",
    "Top risks",
    "Action tracker",
    "Evidence register",
)
XLSX_OPTIONAL_SHEETS = ("Prior-period changes", "Statement of Applicability")
XLSX_COLUMNS = {
    "Framework summary": (
        "Framework",
        "Version",
        "Pack version",
        "Score (%)",
        "Rating",
        "Headline",
        "In scope",
        "Compliant",
        "Partially compliant",
        "Non-compliant",
        "Insufficient evidence",
        "Not applicable",
    ),
    "Requirement register": (
        "Framework",
        "Requirement ID",
        "Requirement",
        "Domain",
        "Outcome",
        "Risk",
        "Priority",
        "Decision",
        "Decided by",
        "Decided on",
        "Evidence citation",
    ),
    "Top risks": (
        "Rank",
        "Finding",
        "Description",
        "Severity",
        "Priority",
        "Framework",
        "Requirement ID",
        "Requirement",
        "Outcome",
        "Cited evidence",
        "Owner",
        "Target date",
        "Action",
    ),
    "Action tracker": (
        "Action",
        "Owner",
        "Target date",
        "Status",
        "Framework",
        "Requirement ID",
        "Finding",
        "Control group",
        "Client update",
        "Evidence of closure",
    ),
    "Evidence register": ("File", "Version", "SHA-256 prefix", "Added on", "Status", "Cited"),
    "Prior-period changes": (
        "Framework",
        "Requirement ID",
        "Requirement",
        "Prior outcome",
        "Current outcome",
        "Change",
    ),
    "Statement of Applicability": (
        "Control ID",
        "Reference",
        "Control",
        "Theme",
        "Applicability",
        "Implementation",
        "Justification",
        "Justification status",
        "Justified by",
        "Justified on",
    ),
}
DOCX_TABLE_HEADERS = {
    "scores": (
        "Framework",
        "Headline",
        "In scope",
        "Compliant",
        "Partial",
        "Non-compliant",
        "Insufficient evidence",
        "Not applicable",
    ),
    "roadmap": ("Action", "Owner", "Target date", "Status", "Closes"),
    "roadmap_group": ("Action", "Owner", "Target date", "Status", "Finding"),
    "domains": ("Domain", "Score", "Rating"),
    "gaps": ("Requirement", "Outcome", "Risk", "Priority"),
    "requirement_register": (
        "Framework",
        "Requirement",
        "Outcome",
        "Risk",
        "Priority",
        "Decision",
        "Decided by",
        "Decided on",
        "Citation",
    ),
    "evidence_register": ("File", "Version", "Added", "Status", "SHA-256", "Cited"),
    "comparison": (
        "Framework",
        "Prior score",
        "Current score",
        "Change",
        "Improved",
        "Regressed",
        "Changed",
        "Newly assessed",
        "No longer assessed",
    ),
    "comparison_changes": ("Requirement", "Prior outcome", "Current outcome", "Change"),
    "soa": ("Control", "Theme", "Applicability", "Implementation", "Justification"),
}
ROADMAP_INTROS = {
    1: (
        "Actions recorded against approved findings, ordered by target date. Owners and dates are set by "
        "the consultant; nothing on this page is estimated."
    ),
    2: (
        "Actions recorded against approved findings, grouped by shared control: findings in different "
        "frameworks that cover the same control concern are listed together, so one remediation is tracked "
        "once. Groups are ordered by their earliest target date. Owners and dates are set by the consultant; "
        "nothing on this page is estimated."
    ),
}
ROADMAP_INTROS[3] = ROADMAP_INTROS[2]
JUSTIFICATION_STATUS = {True: "Recorded", False: "Missing"}
MISSING_FILL = "FFFFF2CC"


class UnsupportedDocument(report_snapshots.SnapshotError):
    status_code = 409


_ILLEGAL_XML_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _clean(value) -> str:
    """Return text safe for XML while preserving valid Unicode and whitespace."""
    if value is None:
        return ""
    return _ILLEGAL_XML_CHARS.sub("", str(value))


def _schema(document: dict) -> int:
    version = document["schema_version"]
    if version not in SUPPORTED_SCHEMA_VERSIONS:
        raise UnsupportedDocument(UNSUPPORTED_DOCUMENT_MESSAGE)
    return version


def derivation_label(document: dict, document_sha256: str) -> str:
    snapshot = document["snapshot"]
    return DERIVATION_LABEL.format(
        snapshot_id8=_clean(snapshot["id"][:8]),
        version_label=_clean(snapshot["version_label"]),
        sha_prefix=_clean(document_sha256[: board_report.SHA_PREFIX_CHARS]),
    )


def export_filename(document: dict, extension: str) -> str:
    snapshot = document["snapshot"]
    return f"{document['company_name']}_board_report_{snapshot['version_label']}_{snapshot['id'][:8]}.{extension}"


def _generated_at(document: dict) -> datetime:
    value = document["snapshot"]["generated_at"]
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(tzinfo=None)


def _display_date(value) -> str:
    if value is None:
        return ""
    return _clean(board_report.display_date(value))


def _or(value, fallback: str) -> str:
    return _clean(value) if value else fallback


def _add_docx_paragraph(document, value=""):
    return document.add_paragraph(_clean(value))


def _add_docx_heading(document, value, level: int):
    return document.add_heading(_clean(value), level=level)


def _fill_docx_cell(cell, value) -> None:
    cell.text = _clean(value)


def _docx_table(document, headers, rows):
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    for cell, header in zip(table.rows[0].cells, headers):
        _fill_docx_cell(cell, header)
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.bold = True
    for values in rows:
        cells = table.add_row().cells
        for cell, value in zip(cells, values):
            _fill_docx_cell(cell, value)
    return table


def _risk_meta(risk: dict) -> str:
    return (
        f"{risk['framework_name']} | {risk['requirement_id']}: {risk['requirement_title']} | "
        f"{risk['outcome_label']} | Severity: {risk['severity']} | Priority: {risk['priority']}"
    )


def _roadmap_closes(closes: list[dict]) -> str:
    return "; ".join(
        f"{close['framework_name']}: {close['requirement_id']} ({close['finding_title']})"
        for close in closes
    )


def _set_docx_normal_font(document, qn) -> None:
    style = document.styles["Normal"]
    style.font.name = DOCX_BODY_FONT
    rpr = style._element.get_or_add_rPr()
    rfonts = rpr.get_or_add_rFonts()
    rfonts.set(qn("w:ascii"), DOCX_BODY_FONT)
    rfonts.set(qn("w:hAnsi"), DOCX_BODY_FONT)
    rfonts.set(qn("w:eastAsia"), DOCX_BODY_FONT)
    rfonts.set(qn("w:cs"), DOCX_COMPLEX_SCRIPT_FONT)


def _render_docx_cover(word, source: dict, label: str) -> None:
    from docx.shared import Pt

    label_paragraph = _add_docx_paragraph(word, label)
    for run in label_paragraph.runs:
        run.font.size = Pt(8)
        run.font.italic = True

    _add_docx_heading(word, "Board report", 0)
    _add_docx_paragraph(word, source["company_name"])
    if source["engagement_name"]:
        _add_docx_paragraph(word, source["engagement_name"])
    frameworks = ", ".join(
        f"{framework['name']} ({framework['version']})" for framework in source["frameworks"]
    )
    _add_docx_paragraph(word, f"Frameworks: {frameworks}")
    _add_docx_paragraph(
        word,
        f"Assessment period: {source['basis']['period_label']} | "
        f"Evidence cut-off: {source['basis']['cutoff_label']}",
    )
    _add_docx_paragraph(word, f"Report generated: {source['snapshot']['generated_on']}")
    _add_docx_paragraph(
        word,
        f"Version {source['snapshot']['version_label']} | Snapshot {source['snapshot']['id'][:8]}",
    )
    if source["release"]["released_by"]:
        _add_docx_paragraph(
            word,
            f"Released for reporting by {source['release']['released_by']} "
            f"on {source['release']['released_on']}",
        )
    _add_docx_paragraph(word, source["sign_off"]["issue_status"])
    word.add_page_break()


def _render_docx_summary(word, source: dict) -> None:
    summary = source["summary"]
    _add_docx_heading(word, "Management summary", 1)
    _add_docx_heading(word, "Basis of assessment", 2)
    _add_docx_paragraph(word, summary["basis_of_assessment"])
    _add_docx_heading(word, "Scope", 2)
    for line in summary["scope"]:
        _add_docx_paragraph(word, line)
    _add_docx_heading(word, "Limitations", 2)
    for limitation in summary["limitations"]:
        _add_docx_paragraph(word, limitation)
    _add_docx_heading(word, "Confidentiality", 2)
    _add_docx_paragraph(word, summary["confidentiality"])
    _add_docx_heading(word, "Scores and coverage", 2)
    _docx_table(
        word,
        DOCX_TABLE_HEADERS["scores"],
        [
            [
                framework["name"],
                framework["headline"],
                framework["coverage"]["in_scope"],
                framework["coverage"]["compliant"],
                framework["coverage"]["partially_compliant"],
                framework["coverage"]["non_compliant"],
                framework["coverage"]["insufficient_evidence"],
                framework["coverage"]["not_applicable"],
            ]
            for framework in summary["frameworks"]
        ],
    )
    _add_docx_paragraph(
        word,
        "Scores are computed and reported independently for each framework; no score is combined across frameworks.",
    )
    totals = summary["totals"]
    totals_paragraph = _add_docx_paragraph(
        word,
        f"{totals['requirements']} requirements assessed | {totals['gaps']} gaps identified "
        f"({totals['critical_high_gaps']} critical or high)",
    )
    for run in totals_paragraph.runs:
        run.bold = True


def _render_docx_risks(word, source: dict) -> None:
    _add_docx_heading(word, "Top risks", 1)
    if not source["top_risks"]:
        _add_docx_paragraph(word, "No approved findings are recorded.")
        return
    for risk in source["top_risks"]:
        _add_docx_heading(word, f"{risk['rank']}. {risk['title']}", 2)
        _add_docx_paragraph(word, risk["description"])
        _add_docx_paragraph(word, _risk_meta(risk))
        for citation in risk["citations"]:
            _add_docx_paragraph(
                word,
                f"{citation['filename']} v{citation['version_number']}, {citation['location_ref']} "
                f"(SHA-256 {citation['sha256_prefix']})",
            )
        _add_docx_paragraph(
            word,
            f"Owner: {_or(risk['owner'], 'Unassigned')} | "
            f"Target: {_display_date(risk['target_date']) if risk['target_date'] else 'No target date'}",
        )
        if risk["action_title"]:
            _add_docx_paragraph(word, f"Action: {risk['action_title']}")


def _render_docx_roadmap(word, source: dict, schema_version: int) -> None:
    _add_docx_heading(word, "Remediation roadmap", 1)
    _add_docx_paragraph(word, ROADMAP_INTROS[schema_version])
    roadmap = source["roadmap"]
    if schema_version == 1:
        actions = roadmap["actions"]
        if not actions:
            _add_docx_paragraph(word, "No remediation actions are recorded for the approved findings yet.")
            return
        _docx_table(
            word,
            DOCX_TABLE_HEADERS["roadmap"],
            [
                [
                    action["title"],
                    _or(action["owner"], "Unassigned"),
                    _display_date(action["target_date"]) if action["target_date"] else "No target date",
                    action["status_label"],
                    _roadmap_closes(action["closes"]),
                ]
                for action in actions
            ],
        )
        return

    groups = roadmap["groups"]
    if not groups:
        _add_docx_paragraph(word, "No remediation actions are recorded for the approved findings yet.")
        return
    for group in groups:
        _add_docx_heading(word, group["topic"], 2)
        _add_docx_paragraph(word, group["headline"])
        _docx_table(
            word,
            DOCX_TABLE_HEADERS["roadmap_group"],
            [
                [
                    action["title"],
                    _or(action["owner"], "Unassigned"),
                    _display_date(action["target_date"]) if action["target_date"] else "No target date",
                    action["status_label"],
                    f"{action['framework_name']}: {action['requirement_id']} ({action['finding_title']})",
                ]
                for action in group["actions"]
            ],
        )
        _add_docx_paragraph(word, f"Findings addressed: {_roadmap_closes(group['closes'])}")


def _render_docx_not_assessed(word, source: dict) -> None:
    not_assessed = source["not_assessed"]
    _add_docx_heading(word, "What we could not assess", 1)
    _add_docx_heading(word, "Insufficient evidence", 2)
    if not_assessed["insufficient_evidence"]:
        for row in not_assessed["insufficient_evidence"]:
            _add_docx_paragraph(
                word,
                f"{row['framework_id']}: {row['requirement_id']} - {row['requirement_title']}",
            )
    else:
        _add_docx_paragraph(word, "No requirement was concluded as insufficient evidence.")
    _add_docx_heading(word, "Request for information", 2)
    rfi = not_assessed["rfi"]
    if rfi["items"]:
        _add_docx_paragraph(word, f"Issued version {rfi['version_label']}")
        for item in rfi["items"]:
            _add_docx_paragraph(
                word,
                f"{item['item_id']}: {item['title']} ({'Required' if item['required'] else 'Recommended'})",
            )
    else:
        _add_docx_paragraph(word, "No request for information has been issued for this assessment.")


def _render_docx_frameworks(word, source: dict) -> None:
    for framework in source["framework_sections"]:
        _add_docx_heading(word, f"{framework['name']} ({framework['version']})", 1)
        score = framework["score"] if framework["score"] is not None else "Not scored"
        rating = f" ({framework['rating']})" if framework["rating"] else ""
        _add_docx_paragraph(word, f"Score: {score}{rating}")
        _add_docx_heading(word, "Domains", 2)
        _docx_table(
            word,
            DOCX_TABLE_HEADERS["domains"],
            [
                [
                    domain["title"],
                    domain["score"] if domain["score"] is not None else "Not applicable",
                    domain["rating"] or "Not applicable",
                ]
                for domain in framework["domains"]
            ],
        )
        _add_docx_heading(word, "Gaps", 2)
        if framework["gaps"]:
            _docx_table(
                word,
                DOCX_TABLE_HEADERS["gaps"],
                [
                    [
                        f"{gap['requirement_id']}: {gap['requirement_title']}",
                        gap["outcome_label"],
                        gap["risk_level"],
                        gap["priority"],
                    ]
                    for gap in framework["gaps"]
                ],
            )
        else:
            _add_docx_paragraph(word, "No approved gaps are recorded.")


def _render_docx_comparison(word, source: dict) -> None:
    prior_period = source["prior_period"]
    _add_docx_heading(word, "Prior-period comparison", 1)
    if prior_period["status"] != "compared":
        for note in prior_period["notes"]:
            _add_docx_paragraph(word, note)
        return

    _add_docx_paragraph(word, prior_period["intro"])
    prior = prior_period["prior"]
    _add_docx_paragraph(
        word,
        f"Compared with version {prior['version_label']} (snapshot {prior['snapshot_id'][:8]}) "
        f"for the assessment period {prior['period_label']}, evidence cut-off {prior['cutoff_label']}, "
        f"generated {prior['generated_on']}.",
    )
    for note in prior_period["notes"]:
        _add_docx_paragraph(word, note)

    table = word.add_table(rows=1, cols=len(DOCX_TABLE_HEADERS["comparison"]))
    table.style = "Table Grid"
    for cell, header in zip(table.rows[0].cells, DOCX_TABLE_HEADERS["comparison"]):
        _fill_docx_cell(cell, header)
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.bold = True
    for framework in prior_period["frameworks"]:
        cells = table.add_row().cells
        _fill_docx_cell(cells[0], framework["name"])
        if framework["compared"]:
            _fill_docx_cell(cells[1], framework["prior_score"] if framework["prior_score"] is not None else "Not scored")
            _fill_docx_cell(cells[2], framework["current_score"] if framework["current_score"] is not None else "Not scored")
            change = (
                f"{framework['score_delta']:+.1f} points"
                if framework["score_delta"] is not None
                else "Not compared"
            )
            _fill_docx_cell(cells[3], change)
            counts = framework["counts"]
            for index, key in enumerate(("improved", "regressed", "changed", "new", "no_longer_assessed"), start=4):
                _fill_docx_cell(cells[index], counts[key])
        else:
            merged = cells[1].merge(cells[-1])
            _fill_docx_cell(merged, "Not compared")

    totals = prior_period["totals"]
    _add_docx_paragraph(
        word,
        f"Gaps identified: {totals['prior']['gaps']} in the prior period, "
        f"{totals['current']['gaps']} in this period.",
    )
    if prior_period["changes"]:
        _docx_table(
            word,
            DOCX_TABLE_HEADERS["comparison_changes"],
            [
                [
                    f"{change['framework_name']}: {change['requirement_id']} - {change['requirement_title']}",
                    change["prior_outcome_label"] or "Not assessed",
                    change["current_outcome_label"] or "Not assessed",
                    change["direction_label"],
                ]
                for change in prior_period["changes"]
            ],
        )
    else:
        _add_docx_paragraph(word, "No requirement outcome changed between the two periods.")


def _render_docx_signoff_and_appendices(word, source: dict) -> None:
    sign_off = source["sign_off"]
    _add_docx_heading(word, "Sign-off", 1)
    _add_docx_paragraph(word, f"Prepared by: {_or(sign_off['prepared_by'], 'not recorded')}")
    _add_docx_paragraph(word, f"Reviewed by: {_or(sign_off['reviewed_by'], 'not recorded')}")
    _add_docx_paragraph(word, f"Assessment period: {source['basis']['period_label']}")
    _add_docx_paragraph(word, f"Evidence cut-off: {source['basis']['cutoff_label']}")
    _add_docx_paragraph(word, f"Report generated: {source['snapshot']['generated_on']}")
    _add_docx_paragraph(word, sign_off["issue_status"])
    _add_docx_paragraph(word, sign_off["names_note"])

    _add_docx_heading(word, "Appendix A: Methodology", 1)
    _add_docx_paragraph(word, source["appendices"]["methodology"])

    _add_docx_heading(word, "Appendix B: Requirement register", 1)
    _docx_table(
        word,
        DOCX_TABLE_HEADERS["requirement_register"],
        [
            [
                row["framework_id"],
                f"{row['requirement_id']}: {row['requirement_title']}",
                row["outcome_label"],
                row["risk_level"],
                row["priority"],
                row["decision_label"],
                row["decided_by"],
                _display_date(row["decided_on"]) if row["decided_on"] else "Not recorded",
                row["citation"] or row["citation_note"],
            ]
            for row in source["appendices"]["requirement_register"]
        ],
    )

    _add_docx_heading(word, "Appendix C: Evidence register", 1)
    evidence = source["appendices"]["evidence_register"]
    if evidence:
        _docx_table(
            word,
            DOCX_TABLE_HEADERS["evidence_register"],
            [
                [
                    row["filename"],
                    f"v{row['version_number']}",
                    _display_date(row["added_on"]) if row["added_on"] else "Not recorded",
                    row["status"],
                    row["sha256_prefix"],
                    "Yes" if row["cited"] else "No",
                ]
                for row in evidence
            ],
        )
    else:
        _add_docx_paragraph(word, "No evidence documents are recorded for this assessment.")


def _render_docx_soa(word, source: dict, schema_version: int) -> None:
    if schema_version < 2 or not source["soa"]:
        return
    soa = source["soa"]
    _add_docx_heading(word, "Appendix D: Statement of Applicability", 1)
    _add_docx_paragraph(word, soa["intro"])
    _add_docx_paragraph(word, soa["reliance"])
    for note in soa["notes"]:
        _add_docx_paragraph(word, note)
    _docx_table(
        word,
        DOCX_TABLE_HEADERS["soa"],
        [
            [
                f"{row['reference']} {row['title']}",
                row["theme"],
                row["applicability_label"],
                row["implementation_label"],
                row["justification"] or "Justification not recorded",
            ]
            for row in soa["rows"]
        ],
    )


def render_docx(document: dict, *, document_sha256: str) -> bytes:
    schema_version = _schema(document)
    from docx import Document
    from docx.oxml.ns import qn

    word = Document()
    _set_docx_normal_font(word, qn)
    label = derivation_label(document, document_sha256)
    _render_docx_cover(word, document, label)
    _render_docx_summary(word, document)
    _render_docx_risks(word, document)
    _render_docx_roadmap(word, document, schema_version)
    _render_docx_not_assessed(word, document)
    _render_docx_frameworks(word, document)
    if schema_version >= 2:
        _render_docx_comparison(word, document)
    _render_docx_signoff_and_appendices(word, document)
    _render_docx_soa(word, document, schema_version)

    section = word.sections[0]
    section.header.paragraphs[0].text = _clean(f"{document['firm_name']} | Board report")
    section.footer.paragraphs[0].text = _clean(
        f"{document['company_name']} | {document['snapshot']['version_label']}"
    )
    generated_at = _generated_at(document)
    properties = word.core_properties
    properties.title = _clean(f"Board report: {document['company_name']}")
    properties.author = _clean(document["firm_name"])
    properties.last_modified_by = _clean(document["firm_name"])
    properties.comments = _clean(label)
    properties.identifier = _clean(document["snapshot"]["id"])
    properties.subject = _clean(f"Board report {document['snapshot']['version_label']}")
    properties.revision = 1
    properties.created = generated_at
    properties.modified = generated_at

    buffer = io.BytesIO()
    word.save(buffer)
    return _pin_package(buffer.getvalue(), generated_at)


def _date_value(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed.date()


def _set_xlsx_cell(cell, value, *, date_cell: bool = False) -> None:
    if date_cell and value is not None:
        value = _date_value(value)
    if isinstance(value, str):
        value = _clean(value)
        cell.value = value
        cell.data_type = "s"
        if value.startswith(FORMULA_PREFIXES):
            cell.quotePrefix = True
    else:
        cell.value = value
    if date_cell and value is not None:
        cell.number_format = "yyyy-mm-dd"


def _write_xlsx_row(sheet, row_number: int, values, *, date_columns=()) -> None:
    for index, value in enumerate(values, start=1):
        _set_xlsx_cell(sheet.cell(row=row_number, column=index), value, date_cell=index in date_columns)


def _style_xlsx_table(sheet, header_row: int, column_count: int) -> None:
    from openpyxl.utils import get_column_letter

    for cell in sheet[header_row]:
        font = copy(cell.font)
        font.bold = True
        cell.font = font
    sheet.freeze_panes = f"A{header_row + 1}"
    last_column = get_column_letter(column_count)
    sheet.auto_filter.ref = f"A{header_row}:{last_column}{sheet.max_row}"


def _framework_name_map(document: dict) -> dict[str, str]:
    return {framework["framework_id"]: framework["name"] for framework in document["frameworks"]}


def _render_xlsx_about(book, document: dict, label: str, document_sha256: str, schema_version: int) -> None:
    sheet = book["About"]
    _set_xlsx_cell(sheet["A1"], label)
    prior_value = None
    if schema_version >= 2:
        prior_period = document["prior_period"]
        if prior_period["status"] == "compared":
            prior = prior_period["prior"]
            prior_value = f"Compared with version {prior['version_label']} (snapshot {prior['snapshot_id'][:8]})"
        else:
            prior_value = " ".join(prior_period["notes"])
    values = (
        ("Company", document["company_name"]),
        ("Engagement", document["engagement_name"]),
        (
            "Frameworks",
            "; ".join(
                f"{framework['name']} ({framework['version']})" for framework in document["frameworks"]
            ),
        ),
        ("Assessment period", document["basis"]["period_label"]),
        ("Evidence cut-off", document["basis"]["cutoff_label"]),
        ("Report version", document["snapshot"]["version_label"]),
        ("Snapshot ID", document["snapshot"]["id"]),
        ("Report generated", document["snapshot"]["generated_at"]),
        ("Prior-period comparison", prior_value),
        ("Document SHA-256", document_sha256),
        ("Document schema version", schema_version),
        ("Export format version", EXPORT_FORMAT_VERSION),
    )
    for row, (key, value) in enumerate(values, start=3):
        _set_xlsx_cell(sheet.cell(row=row, column=1), key)
        _set_xlsx_cell(sheet.cell(row=row, column=2), value)


def _render_xlsx_framework_summary(book, document: dict) -> None:
    sheet = book["Framework summary"]
    _write_xlsx_row(sheet, 1, XLSX_COLUMNS[sheet.title])
    by_id = _framework_name_map(document)
    versions = {framework["framework_id"]: framework for framework in document["frameworks"]}
    for row_number, framework in enumerate(document["summary"]["frameworks"], start=2):
        recorded = versions[framework["framework_id"]]
        pack_version = recorded["pack_version"] if document["schema_version"] >= 2 else None
        _write_xlsx_row(
            sheet,
            row_number,
            [
                framework["name"],
                recorded["version"],
                pack_version,
                framework["score"],
                framework["rating"],
                framework["headline"],
                *[framework["coverage"][key] for key in (
                    "in_scope",
                    "compliant",
                    "partially_compliant",
                    "non_compliant",
                    "insufficient_evidence",
                    "not_applicable",
                )],
            ],
        )
    _style_xlsx_table(sheet, 1, len(XLSX_COLUMNS[sheet.title]))


def _render_xlsx_requirement_register(book, document: dict) -> None:
    sheet = book["Requirement register"]
    _write_xlsx_row(sheet, 1, XLSX_COLUMNS[sheet.title])
    names = _framework_name_map(document)
    for row_number, row in enumerate(document["appendices"]["requirement_register"], start=2):
        _write_xlsx_row(
            sheet,
            row_number,
            [
                names[row["framework_id"]],
                row["requirement_id"],
                row["requirement_title"],
                row["domain_title"],
                row["outcome_label"],
                row["risk_level"],
                row["priority"],
                row["decision_label"],
                row["decided_by"],
                row["decided_on"],
                row["citation"] or row["citation_note"],
            ],
            date_columns=(10,),
        )
    _style_xlsx_table(sheet, 1, len(XLSX_COLUMNS[sheet.title]))


def _render_xlsx_top_risks(book, document: dict) -> None:
    sheet = book["Top risks"]
    _write_xlsx_row(sheet, 1, XLSX_COLUMNS[sheet.title])
    for row_number, risk in enumerate(document["top_risks"], start=2):
        citations = "; ".join(
            f"{citation['filename']} v{citation['version_number']}, {citation['location_ref']} "
            f"(SHA-256 {citation['sha256_prefix']})"
            for citation in risk["citations"]
        ) or None
        _write_xlsx_row(
            sheet,
            row_number,
            [
                risk["rank"],
                risk["title"],
                risk["description"],
                risk["severity"],
                risk["priority"],
                risk["framework_name"],
                risk["requirement_id"],
                risk["requirement_title"],
                risk["outcome_label"],
                citations,
                risk["owner"],
                risk["target_date"],
                risk["action_title"],
            ],
            date_columns=(12,),
        )
    _style_xlsx_table(sheet, 1, len(XLSX_COLUMNS[sheet.title]))


def _action_group_topics(document: dict, schema_version: int) -> dict[tuple[str, str], list[str]]:
    if schema_version == 1:
        return {}
    topics: dict[tuple[str, str], list[str]] = {}
    for group in document["roadmap"]["groups"]:
        for close in group["closes"]:
            key = (close["framework_name"], close["requirement_id"])
            topics.setdefault(key, []).append(group["topic"])
    return topics


def _render_xlsx_action_tracker(book, document, schema_version: int) -> None:
    sheet = book["Action tracker"]
    _write_xlsx_row(sheet, 1, XLSX_COLUMNS[sheet.title])
    topics = _action_group_topics(document, schema_version)
    for row_number, action in enumerate(document["roadmap"]["actions"], start=2):
        group_names = []
        for close in action["closes"]:
            for topic in topics.get((close["framework_name"], close["requirement_id"]), []):
                if topic not in group_names:
                    group_names.append(topic)
        _write_xlsx_row(
            sheet,
            row_number,
            [
                action["title"],
                action["owner"],
                action["target_date"],
                action["status_label"],
                "; ".join(close["framework_name"] for close in action["closes"]),
                "; ".join(close["requirement_id"] for close in action["closes"]),
                "; ".join(close["finding_title"] for close in action["closes"]),
                "; ".join(group_names) or None,
                None,
                None,
            ],
            date_columns=(3,),
        )
    _style_xlsx_table(sheet, 1, len(XLSX_COLUMNS[sheet.title]))


def _render_xlsx_evidence_register(book, document: dict) -> None:
    sheet = book["Evidence register"]
    _write_xlsx_row(sheet, 1, XLSX_COLUMNS[sheet.title])
    for row_number, row in enumerate(document["appendices"]["evidence_register"], start=2):
        _write_xlsx_row(
            sheet,
            row_number,
            [
                row["filename"],
                row["version_number"],
                row["sha256_prefix"],
                row["added_on"],
                row["status"],
                "Yes" if row["cited"] else "No",
            ],
            date_columns=(4,),
        )
    _style_xlsx_table(sheet, 1, len(XLSX_COLUMNS[sheet.title]))


def _render_xlsx_comparison(book, document) -> None:
    sheet = book.create_sheet("Prior-period changes")
    _write_xlsx_row(sheet, 1, XLSX_COLUMNS[sheet.title])
    for row_number, change in enumerate(document["prior_period"]["changes"], start=2):
        _write_xlsx_row(
            sheet,
            row_number,
            [
                change["framework_name"],
                change["requirement_id"],
                change["requirement_title"],
                change["prior_outcome_label"] or "Not assessed",
                change["current_outcome_label"] or "Not assessed",
                change["direction_label"],
            ],
        )
    _style_xlsx_table(sheet, 1, len(XLSX_COLUMNS[sheet.title]))


def _render_xlsx_soa(book, document) -> None:
    from openpyxl.styles import PatternFill

    sheet = book.create_sheet("Statement of Applicability")
    soa = document["soa"]
    notes = soa["notes"]
    for row_number, note in enumerate(notes, start=1):
        _set_xlsx_cell(sheet.cell(row=row_number, column=1), note)
    header_row = len(notes) + 2 if notes else 1
    _write_xlsx_row(sheet, header_row, XLSX_COLUMNS[sheet.title])
    for row_number, row in enumerate(soa["rows"], start=header_row + 1):
        _write_xlsx_row(
            sheet,
            row_number,
            [
                row["control_id"],
                row["reference"],
                row["title"],
                row["theme"],
                row["applicability_label"],
                row["implementation_label"],
                row["justification"],
                JUSTIFICATION_STATUS[bool(row["justification"])],
                row["justification_by"],
                row["justification_on"],
            ],
            date_columns=(10,),
        )
        status_cell = sheet.cell(row=row_number, column=8)
        if status_cell.value == JUSTIFICATION_STATUS[False]:
            status_cell.fill = PatternFill(fill_type="solid", fgColor=MISSING_FILL)
    _style_xlsx_table(sheet, header_row, len(XLSX_COLUMNS[sheet.title]))


def render_xlsx(document: dict, *, document_sha256: str) -> bytes:
    schema_version = _schema(document)
    from openpyxl import Workbook

    label = derivation_label(document, document_sha256)
    book = Workbook()
    book.active.title = "About"
    for name in XLSX_SHEETS[1:]:
        book.create_sheet(name)
    _render_xlsx_about(book, document, label, document_sha256, schema_version)
    _render_xlsx_framework_summary(book, document)
    _render_xlsx_requirement_register(book, document)
    _render_xlsx_top_risks(book, document)
    _render_xlsx_action_tracker(book, document, schema_version)
    _render_xlsx_evidence_register(book, document)
    if schema_version >= 2 and document["prior_period"]["status"] == "compared":
        _render_xlsx_comparison(book, document)
    if schema_version >= 2 and document["soa"]:
        _render_xlsx_soa(book, document)

    generated_at = _generated_at(document)
    properties = book.properties
    properties.creator = _clean(document["firm_name"])
    properties.lastModifiedBy = _clean(document["firm_name"])
    properties.title = _clean(f"Board report: {document['company_name']}")
    properties.description = _clean(label)
    properties.identifier = _clean(document["snapshot"]["id"])
    properties.created = generated_at
    properties.modified = generated_at

    buffer = io.BytesIO()
    book.save(buffer)
    return _pin_package(buffer.getvalue(), generated_at)


def _pin_package(content: bytes, generated_at: datetime) -> bytes:
    stamp = generated_at.timetuple()[:6]
    iso_stamp = generated_at.strftime("%Y-%m-%dT%H:%M:%SZ").encode("ascii")
    output = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(content), "r") as source, zipfile.ZipFile(
        output, "w", compression=zipfile.ZIP_DEFLATED
    ) as target:
        for entry in source.infolist():
            data = source.read(entry.filename)
            if entry.filename == "docProps/core.xml":
                data = re.sub(
                    rb"(<dcterms:created\b[^>]*>)[^<]*(</dcterms:created>)",
                    rb"\g<1>" + iso_stamp + rb"\g<2>",
                    data,
                )
                data = re.sub(
                    rb"(<dcterms:modified\b[^>]*>)[^<]*(</dcterms:modified>)",
                    rb"\g<1>" + iso_stamp + rb"\g<2>",
                    data,
                )
            pinned = zipfile.ZipInfo(entry.filename, date_time=stamp)
            pinned.compress_type = zipfile.ZIP_DEFLATED
            pinned.external_attr = entry.external_attr
            pinned.internal_attr = entry.internal_attr
            pinned.create_system = entry.create_system
            pinned.flag_bits = entry.flag_bits
            target.writestr(pinned, data)
    return output.getvalue()
