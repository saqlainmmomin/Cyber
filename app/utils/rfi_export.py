"""
RFI (Request for Information) export - PDF and DOCX formats.

PDF: Professional letterhead style using fpdf2.
DOCX: Editable format using python-docx.
"""

import json
import re
import zipfile
from datetime import datetime, timezone
from io import BytesIO

from fpdf import FPDF
from fpdf.enums import MethodReturnValue

from app.config import settings
# Reuse palette and helpers from main PDF export
from app.utils.pdf_export import (
    NAVY, DARK_TEXT, MID_TEXT, LIGHT_TEXT, WHITE, CARD_BG, DIVIDER,
    PW, PM, CW, S, brand_rgb,
)

# Priority colors for RFI
RFI_PRIORITY_COLORS = {
    "Critical": (231, 76, 60),
    "High": (230, 126, 34),
    "Medium": (241, 196, 15),
    "Low": (39, 174, 96),
    "Required": (230, 126, 34),
    "Recommended": (39, 174, 96),
}

WHY_WE_ASK_INTRO = (
    "This appendix lists the checks behind each request. Send the items listed "
    "under each request. You do not need to answer each check separately."
)


# ---------------------------------------------------------------------------
# PDF Export
# ---------------------------------------------------------------------------

def generate_rfi_pdf(
    title: str,
    company_name: str,
    introduction: str,
    evidence_items: list[dict],
    response_instructions: str,
    generated_at: datetime | None = None,
    framework_label: str = "",
    *,
    version_label: str = "",
) -> bytes:
    """Generate a professional RFI PDF document."""
    subtitle = f"{framework_label} Compliance Gap Assessment" if framework_label else "Compliance Gap Assessment"
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.alias_nb_pages()

    date_str = (generated_at or datetime.now(timezone.utc)).strftime("%d %B %Y")

    # --- Cover Page ---
    pdf.add_page()
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, PW, 60, style="F")
    pdf.set_draw_color(*brand_rgb())
    pdf.set_line_width(1)
    pdf.line(0, 61, PW, 61)
    pdf.set_line_width(0.2)

    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*WHITE)
    pdf.set_y(18)
    pdf.set_x(PM)
    pdf.multi_cell(CW, 8, text=S(f"{settings.firm_name} Request for Information"), align="C")
    pdf.set_font("Helvetica", "", 12)
    pdf.set_x(PM)
    pdf.cell(0, 8, text=S(subtitle), align="C")

    pdf.set_y(70)
    pdf.set_text_color(*DARK_TEXT)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, text=S(company_name), align="C")
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*MID_TEXT)
    pdf.cell(0, 6, text=S(f"Date: {date_str}"), align="C")
    pdf.ln(6)
    pdf.cell(0, 6, text=S(f"Reference: RFI-{company_name[:20].upper().replace(' ', '-')}"), align="C")
    if version_label:
        pdf.ln(6)
        pdf.cell(0, 6, text=S(f"Version: {version_label}"), align="C")

    # Summary box
    pdf.ln(15)
    critical = sum(1 for i in evidence_items if i.get("priority") == "Critical")
    high = sum(1 for i in evidence_items if i.get("priority") == "High")
    medium = sum(1 for i in evidence_items if i.get("priority") == "Medium")
    required = sum(1 for i in evidence_items if i.get("priority") == "Required")
    recommended = sum(1 for i in evidence_items if i.get("priority") == "Recommended")

    pdf.set_fill_color(*CARD_BG)
    pdf.rect(PM, pdf.get_y(), CW, 30, style="F")
    y = pdf.get_y() + 5
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*NAVY)
    pdf.set_xy(PM + 5, y)
    pdf.cell(0, 6, text=S(f"Total Evidence Items: {len(evidence_items)}"))
    pdf.set_xy(PM + 5, y + 8)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*MID_TEXT)

    summary_parts = []
    if critical:
        summary_parts.append(f"{critical} Critical")
    if high:
        summary_parts.append(f"{high} High")
    if medium:
        summary_parts.append(f"{medium} Medium")
    if required:
        summary_parts.append(f"{required} Required")
    if recommended:
        summary_parts.append(f"{recommended} Recommended")
    pdf.cell(0, 6, text=S(" | ".join(summary_parts) if summary_parts else "No priority items"))
    pdf.set_y(pdf.get_y() + 25)

    # Confidentiality notice
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*LIGHT_TEXT)
    pdf.multi_cell(CW, 4, text=S(
        f"CONFIDENTIAL: This document contains findings from a {framework_label + ' ' if framework_label else ''}compliance assessment. "
        "Distribution should be limited to authorized personnel."
    ), align="C")

    _rfi_footer(pdf, company_name)

    # --- Introduction Page ---
    pdf.add_page()
    _rfi_header(pdf, "Introduction")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*DARK_TEXT)
    pdf.multi_cell(CW, 5, text=S(introduction))
    _rfi_footer(pdf, company_name)

    # --- Evidence Items Pages ---
    # Group by chapter
    chapters = {}
    for item in evidence_items:
        ch = item.get("chapter", "General")
        chapters.setdefault(ch, []).append(item)

    for chapter_name, items in chapters.items():
        pdf.add_page()
        _rfi_header(pdf, f"Evidence Items - {chapter_name}")

        for item in items:
            _render_evidence_item(pdf, item, company_name)

        _rfi_footer(pdf, company_name)

    if any(item.get("why_we_ask") or [] for item in evidence_items):
        pdf.add_page()
        _rfi_header(pdf, "Why We Ask")
        _render_why_we_ask(pdf, evidence_items, company_name)
        _rfi_footer(pdf, company_name)

    # --- Response Instructions Page ---
    pdf.add_page()
    _rfi_header(pdf, "Response Instructions")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*DARK_TEXT)
    pdf.multi_cell(CW, 5, text=S(response_instructions))
    _rfi_footer(pdf, company_name)

    return pdf.output()


def _hint_label(criterion: dict) -> str:
    """Readable evidence hint. The signed source basis carries auditor notes and
    is not printed in client documents."""
    return criterion.get("evidence_hint_label") or criterion.get("evidence_hint", "")


def _render_why_we_ask(pdf: FPDF, evidence_items: list[dict], company_name: str):
    """Measure appendix lines before drawing and keep headings with content."""
    blocks = [("", 9, WHY_WE_ASK_INTRO, False)]
    for item in evidence_items:
        controls = item.get("why_we_ask") or []
        if not controls:
            continue
        blocks.append(("", 7, "", False))
        blocks.append(("B", 9,
                       f"{item.get('item_id', '')} {item.get('requirement_title', '')}", True))
        for control in controls:
            blocks.append(("B", 8,
                           f"{control['requirement_id']} {control['title']}", True))
            for criterion in control["criteria"]:
                label = "Design" if criterion["kind"] == "design" else "Operating"
                blocks.extend([
                    ("", 7, f"[{label}] {criterion['statement']}", True),
                    ("", 7, f"Evidence hint: {_hint_label(criterion)}", False),
                    ("", 7, "", False),
                ])

    lines = []
    for style, size, text, heading in blocks:
        pdf.set_font("Helvetica", style, size)
        pdf.set_x(PM)
        wrapped = pdf.multi_cell(
            CW, 4, text=S(text), dry_run=True, output=MethodReturnValue.LINES,
        ) if text else [""]
        lines.extend((style, size, line,
                      heading or (bool(text) and index < len(wrapped) - 1),
                      4 if text else 2)
                     for index, line in enumerate(wrapped))

    for index, (style, size, line, heading, height) in enumerate(lines):
        # Keep headings, including any intervening spacing, with the first
        # complete criterion. Wrapped source bases stay in that same group.
        minimum_lines = 1
        if heading:
            following = index + 1
            while following < len(lines) and (lines[following][3] or not lines[following][2]):
                following += 1
            minimum_lines = following - index + (following < len(lines))
        minimum_height = sum(row[4] for row in lines[index:index + minimum_lines])
        if not line and (pdf.get_y() <= 16 or
                         pdf.page_break_trigger - pdf.get_y() < height):
            continue
        if pdf.page_break_trigger - pdf.get_y() < minimum_height:
            _rfi_footer(pdf, company_name)
            pdf.add_page()
            _rfi_header(pdf, "Why We Ask (continued)")
        pdf.set_x(PM)
        pdf.set_font("Helvetica", style, size)
        pdf.set_text_color(*DARK_TEXT)
        pdf.cell(CW, height, text=S(line), new_x="LMARGIN", new_y="NEXT")


def _render_evidence_item(pdf: FPDF, item: dict, company_name: str):
    """Render a single evidence request item as a card."""
    requirements = item.get("requirements") or []
    priority = item.get("priority", "Medium")
    color = RFI_PRIORITY_COLORS.get(priority, (150, 150, 150))
    # "dpdpa_section" is the pre-multi-framework key still present in stored RFIs.
    section_ref = item.get("section_ref") or item.get("dpdpa_section", "")
    reference = " | ".join(
        part for part in (item.get("requirement_id", ""), section_ref) if part
    )
    blocks = [
        ("B", 9, DARK_TEXT, item.get("requirement_title", "")),
        ("I", 8, MID_TEXT, f"Status: {item.get('current_status', '')}"),
    ]
    structured = bool(item.get("what_to_send") or item.get("summary"))
    if structured:
        # Indents locate the text; the bullet occupies the preceding 4 mm.
        blocks.append(("", 8, DARK_TEXT, item.get("summary") or "", 0, False))
        artifacts = item.get("what_to_send") or []
        if artifacts:
            blocks.extend([("", 8, DARK_TEXT, "", 0, False),
                           ("B", 8, DARK_TEXT, "What to send", 0, False)])
        for artifact in artifacts:
            ids = ", ".join(artifact.get("controls") or [])
            text = artifact.get("name", "") + (f" ({ids})" if ids else "")
            blocks.append(("", 8, DARK_TEXT, text, 4, True))
            for specific in artifact.get("specifics") or []:
                ids = ", ".join(specific.get("controls") or [])
                text = specific.get("text", "") + (f" ({ids})" if ids else "")
                blocks.append(("", 8, DARK_TEXT, text, 8, True))
        blocks.append(("", 8, DARK_TEXT, "", 0, False))
        for label, key in (("Example of what to send:", "example"),
                           ("Good looks like:", "good_looks_like")):
            blocks.append(("B", 8, MID_TEXT, label, 0, False))
            blocks.append(("", 8, DARK_TEXT, item.get(key) or "", 0, False))
        blocks.extend([
            ("", 8, DARK_TEXT, "", 0, False),
            ("", 8, DARK_TEXT,
             "Period (auditor): ________    Sample size (auditor): ________", 0, False),
        ])
    else:
        blocks.append(("", 8, DARK_TEXT,
                       f"Evidence Requested: {item.get('evidence_requested', '')}"))
    if requirements:
        blocks.append(("", 7, MID_TEXT, f"Requested for: {_requested_for(requirements)}"))
    blocks.append(("", 7, LIGHT_TEXT,
                   f"Suggested deadline: {item.get('deadline_weeks', 3)} weeks"))

    # Wrap before drawing so each card segment has the exact height needed.
    # A request can span pages; fixed-height cards would overlap the next item.
    lines = []
    for block in blocks:
        style, size, text_color, text = block[:4]
        indent, bullet = block[4:] if len(block) > 4 else (0, False)
        pdf.set_font("Helvetica", style, size)
        pdf.set_x(PM + 6)
        wrapped = pdf.multi_cell(
            CW - 12 - indent, 4, text=S(text), dry_run=True, output=MethodReturnValue.LINES,
        ) if text else [""]
        lines.extend((style, size, text_color, line, indent, bullet and index == 0,
                      index == 0, len(wrapped) - index)
                     for index, line in enumerate(wrapped))

    if structured:
        card_height = 10 + 4 * len(lines)
        fresh_capacity = pdf.page_break_trigger - 16
        if card_height <= fresh_capacity and card_height > pdf.page_break_trigger - pdf.get_y():
            _rfi_footer(pdf, company_name)
            pdf.add_page()
            _rfi_header(pdf, "Evidence Items (continued)")

    while lines:
        # Keep the header with at least five body lines when available.
        minimum_height = 10 + 4 * min(5, len(lines))
        if pdf.page_break_trigger - pdf.get_y() < minimum_height:
            _rfi_footer(pdf, company_name)
            pdf.add_page()
            _rfi_header(pdf, "Evidence Items (continued)")

        y_start = pdf.get_y()
        capacity = int((pdf.page_break_trigger - y_start - 10) // 4)
        # Avoid a continuation containing only the final one or two lines.
        remaining = len(lines) - capacity
        if 0 < remaining < 3:
            capacity -= 3 - remaining
        if structured and capacity < len(lines):
            tail_start = next((index for index, row in enumerate(lines)
                               if row[0] == "B" and row[3] == "Good looks like:"), None)
            if tail_start is not None and 0 < tail_start < capacity:
                capacity = tail_start
            # Keep a paragraph's first two and last two lines together.
            next_line = lines[capacity]
            if not next_line[6] and next_line[7] == 1:
                capacity -= 1
            elif capacity and lines[capacity - 1][6] and lines[capacity - 1][7] > 1:
                capacity -= 1
            # A section label always stays with its first value line.
            while capacity and lines[capacity - 1][0] == "B":
                capacity -= 1
        segment, lines = lines[:capacity], lines[capacity:]
        card_height = 10 + 4 * len(segment)
        pdf.set_fill_color(*color)
        pdf.rect(PM, y_start, 3, card_height, style="F")
        pdf.set_fill_color(*CARD_BG)
        pdf.rect(PM + 3, y_start, CW - 3, card_height, style="F")

        pdf.set_xy(PM + 6, y_start + 2)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*NAVY)
        pdf.cell(30, 5, text=S(item.get("item_id", "")))
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*color)
        pdf.cell(20, 5, text=S(priority))
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*LIGHT_TEXT)
        pdf.cell(0, 5, text=S(reference))

        pdf.set_y(y_start + 8)
        for style, size, text_color, line, indent, bullet, _, _ in segment:
            pdf.set_x(PM + 6 + indent)
            pdf.set_font("Helvetica", style, size)
            pdf.set_text_color(*text_color)
            if bullet:
                pdf.set_x(PM + 6 + indent - 4)
                pdf.cell(4, 4, text=S("-"))
            pdf.cell(CW - 12 - indent, 4, text=S(line), new_x="LMARGIN", new_y="NEXT")
        pdf.set_y(y_start + card_height + 4)


def _requested_for(requirements: list[str]) -> str:
    if len(requirements) <= 12:
        return ", ".join(requirements)
    return ", ".join(requirements[:12]) + f" and {len(requirements) - 12} more"


def _rfi_header(pdf: FPDF, section_title: str):
    """Draw RFI header bar."""
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, PW, 12, style="F")
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_text_color(*WHITE)
    pdf.text(PM, 8, S(f"{settings.firm_name} | RFI | {section_title}"))
    pdf.set_y(16)


def _rfi_footer(pdf: FPDF, company_name: str):
    """Draw RFI footer."""
    x, y = pdf.get_x(), pdf.get_y()
    auto_page_break, margin = pdf.auto_page_break, pdf.b_margin
    pdf.set_auto_page_break(False)
    pdf.set_xy(PM, pdf.h - 15)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(*LIGHT_TEXT)
    pdf.cell(0, 5, text=S(f"{settings.firm_name}  |  CONFIDENTIAL  |  RFI  |  {company_name}"), align="L")
    pdf.cell(0, 5, text=S(f"Page {pdf.page_no()}/{{nb}}"), align="R")
    pdf.set_auto_page_break(auto_page_break, margin)
    pdf.set_xy(x, y)


# ---------------------------------------------------------------------------
# DOCX Export
# ---------------------------------------------------------------------------

def generate_rfi_docx(
    title: str,
    company_name: str,
    introduction: str,
    evidence_items: list[dict],
    response_instructions: str,
    generated_at: datetime | None = None,
    framework_label: str = "",
    *,
    version_label: str = "",
) -> bytes:
    """Generate a professional RFI DOCX document."""
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT

    doc = Document()
    date_str = (generated_at or datetime.now(timezone.utc)).strftime("%d %B %Y")
    subtitle = f"{framework_label} Compliance Gap Assessment" if framework_label else "Compliance Gap Assessment"

    # Style defaults
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10)

    # Title
    title_p = doc.add_heading(f"{settings.firm_name} - {title}", level=0)
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle_p = doc.add_paragraph(subtitle)
    subtitle_p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Metadata
    meta_p = doc.add_paragraph()
    meta_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    metadata_text = f"Date: {date_str}\nOrganization: {company_name}"
    if version_label:
        metadata_text += f"\nVersion: {version_label}"
    meta_run = meta_p.add_run(metadata_text)
    meta_run.font.size = Pt(10)
    meta_run.font.color.rgb = RGBColor(100, 100, 100)

    doc.add_paragraph()  # spacer

    # Confidentiality
    conf_p = doc.add_paragraph()
    conf_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    conf_run = conf_p.add_run("CONFIDENTIAL - Distribution limited to authorized personnel")
    conf_run.font.size = Pt(8)
    conf_run.font.italic = True
    conf_run.font.color.rgb = RGBColor(150, 150, 150)

    # Summary
    critical = sum(1 for i in evidence_items if i.get("priority") == "Critical")
    high = sum(1 for i in evidence_items if i.get("priority") == "High")
    summary_p = doc.add_paragraph()
    summary_p.add_run(f"Total Evidence Items: {len(evidence_items)}").bold = True
    if critical:
        summary_p.add_run(f"  |  {critical} Critical").font.color.rgb = RGBColor(231, 76, 60)
    if high:
        summary_p.add_run(f"  |  {high} High").font.color.rgb = RGBColor(230, 126, 34)
    if required := sum(1 for i in evidence_items if i.get("priority") == "Required"):
        summary_p.add_run(f"  |  {required} Required").font.color.rgb = RGBColor(230, 126, 34)

    doc.add_page_break()

    # Introduction
    doc.add_heading("Introduction", level=1)
    doc.add_paragraph(introduction)

    doc.add_page_break()

    # Evidence Items Table
    doc.add_heading("Evidence Items", level=1)

    # Group by chapter
    chapters = {}
    for item in evidence_items:
        ch = item.get("chapter", "General")
        chapters.setdefault(ch, []).append(item)

    for chapter_name, items in chapters.items():
        doc.add_heading(chapter_name, level=2)

        table = doc.add_table(rows=1, cols=5)
        table.style = "Light Grid Accent 1"
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        structured_table = any(item.get("what_to_send") or item.get("summary") for item in items)
        if structured_table:
            table.autofit = False
            for column, width in zip(table.columns, (0.6, 1.35, 0.65, 0.9, 3.0)):
                column.width = Inches(width)
            for cell, width in zip(table.rows[0].cells, (0.6, 1.35, 0.65, 0.9, 3.0)):
                cell.width = Inches(width)

        # Header row
        headers = ["Item ID", "Requirement", "Priority", "Current Status", "Evidence Requested"]
        for i, header in enumerate(headers):
            cell = table.rows[0].cells[i]
            cell.text = header
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.bold = True
                    run.font.size = Pt(8)

        # Data rows
        for item in items:
            row = table.add_row()
            if structured_table:
                for cell, width in zip(row.cells, (0.6, 1.35, 0.65, 0.9, 3.0)):
                    cell.width = Inches(width)
            row.cells[0].text = item.get("item_id", "")
            requirements = item.get("requirements") or []
            if requirements:
                row.cells[1].text = (
                    f"{item.get('requirement_title', '')}\n"
                    f"Requested for: {', '.join(requirements)}"
                )
            else:
                row.cells[1].text = (
                    f"{item.get('requirement_title', '')}\n"
                    f"({item.get('requirement_id', '')})"
                )
            row.cells[2].text = item.get("priority", "Medium")
            row.cells[3].text = item.get("current_status", "")
            if item.get("what_to_send") or item.get("summary"):
                cell = row.cells[4]
                cell.paragraphs[0].add_run(_xml_text(item.get("summary") or ""))
                if item.get("what_to_send"):
                    cell.add_paragraph().add_run("What to send").bold = True
                for artifact in item.get("what_to_send") or []:
                    paragraph = cell.add_paragraph(style="List Bullet")
                    paragraph.add_run(_xml_text(artifact.get("name", "")))
                    _docx_control_ids(paragraph, artifact.get("controls") or [])
                    for specific in artifact.get("specifics") or []:
                        paragraph = cell.add_paragraph(style="List Bullet 2")
                        paragraph.add_run(_xml_text(specific.get("text", "")))
                        _docx_control_ids(paragraph, specific.get("controls") or [])
                for label, key in (("Example of what to send:", "example"),
                                   ("Good looks like:", "good_looks_like")):
                    paragraph = cell.add_paragraph()
                    paragraph.add_run(label).bold = True
                    paragraph.add_run(_xml_text(" " + (item.get(key) or "")))
                cell.add_paragraph(
                    "Period (auditor): ________    Sample size (auditor): ________"
                )
            else:
                row.cells[4].text = _xml_text(item.get("evidence_requested", ""))

            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        if run.font.size is None:
                            run.font.size = Pt(8)

        doc.add_paragraph()  # spacer

    if any(item.get("why_we_ask") or [] for item in evidence_items):
        doc.add_page_break()
        doc.add_heading("Why We Ask", level=1)
        doc.add_paragraph(WHY_WE_ASK_INTRO)
        for item in evidence_items:
            controls = item.get("why_we_ask") or []
            if not controls:
                continue
            doc.add_heading(_xml_text(
                f"{item.get('item_id', '')} {item.get('requirement_title', '')}"
            ), level=3)
            for control in controls:
                doc.add_paragraph().add_run(_xml_text(
                    f"{control['requirement_id']} {control['title']}"
                )).bold = True
                for criterion in control["criteria"]:
                    label = "Design" if criterion["kind"] == "design" else "Operating"
                    doc.add_paragraph(_xml_text(
                        f"[{label}] {criterion['statement']}\n"
                        f"Evidence hint: {_hint_label(criterion)}"
                    ))

    doc.add_page_break()

    # Response Instructions
    doc.add_heading("Response Instructions", level=1)
    doc.add_paragraph(response_instructions)

    # Save to bytes
    for section in doc.sections:
        footer = section.footer.paragraphs[0]
        footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        footer.add_run(f"{settings.firm_name}  |  CONFIDENTIAL  |  {company_name}")

    buffer = BytesIO()
    doc.save(buffer)
    return _stamp_zip_entries(buffer.getvalue(), generated_at)


def _docx_control_ids(paragraph, controls: list[str]):
    """Keep citations distinct from the artifact a reader needs to send."""
    from docx.shared import Pt, RGBColor

    if controls:
        run = paragraph.add_run(_xml_text(f" ({', '.join(controls)})"))
        run.font.size = Pt(7)
        run.font.color.rgb = RGBColor(100, 100, 100)


def _xml_text(text: str) -> str:
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)


def _stamp_zip_entries(content: bytes, generated_at: datetime | None) -> bytes:
    """Pin every zip entry's timestamp so re-rendering a DOCX is byte-identical.

    python-docx stamps each member with the wall-clock second of the save, so two
    downloads of the same frozen RFI version differed whenever they straddled a
    second boundary.
    """
    stamp = (generated_at or datetime(1980, 1, 1)).timetuple()[:6]
    stamp = max(stamp, (1980, 1, 1, 0, 0, 0))
    source = zipfile.ZipFile(BytesIO(content))
    output = BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as target:
        for info in source.infolist():
            pinned = zipfile.ZipInfo(info.filename, date_time=stamp)
            pinned.compress_type = info.compress_type
            pinned.external_attr = info.external_attr
            target.writestr(pinned, source.read(info))
    return output.getvalue()
