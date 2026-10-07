"""Deterministic evidence files for the Veldhara walkthrough."""

from __future__ import annotations

import io
from pathlib import Path


def _pdf(title: str, lines: list[str]) -> bytes:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(0, 9, title)
    pdf.ln(4)
    pdf.set_font("Helvetica", size=10)
    for line in lines:
        pdf.multi_cell(0, 6, line)
        pdf.ln(1)
    return bytes(pdf.output())


def _docx(
    title: str,
    paragraphs: list[str],
    *,
    headers: tuple[str, ...] = (),
    rows: tuple[tuple[str, ...], ...] = (),
) -> bytes:
    from docx import Document

    document = Document()
    document.add_heading(title, level=1)
    for paragraph in paragraphs:
        document.add_paragraph(paragraph)
    if headers:
        table = document.add_table(rows=1, cols=len(headers))
        for cell, value in zip(table.rows[0].cells, headers):
            cell.text = value
        for row in rows:
            cells = table.add_row().cells
            for cell, value in zip(cells, row):
                cell.text = value
    output = io.BytesIO()
    document.save(output)
    return output.getvalue()


def _xlsx() -> bytes:
    from openpyxl import Workbook

    workbook = Workbook()
    users = workbook.active
    users.title = "Users"
    users.append(("user", "system", "role", "last_login", "reviewer_decision"))
    for index in range(1, 41):
        users.append(
            (
                f"user{index:02d}@veldhara.example",
                ("TMS", "SAP Finance", "Microsoft 365", "HR")[(index - 1) % 4],
                ("viewer", "operator", "admin")[(index - 1) % 3],
                f"2026-09-{(index % 28) + 1:02d}",
                "retain" if index % 7 else "remove",
            )
        )
    summary = workbook.create_sheet("Summary")
    summary.append(("metric", "value"))
    summary.append(("systems reviewed", 9))
    summary.append(("systems in production", 11))
    summary.append(("accounts sampled", 40))
    output = io.BytesIO()
    workbook.save(output)
    return output.getvalue()


def _png() -> bytes | None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None

    image = Image.new("RGB", (1280, 720), "#f4f7fb")
    draw = ImageDraw.Draw(image)
    try:
        title_font = ImageFont.truetype("DejaVuSans.ttf", 34)
        body_font = ImageFont.truetype("DejaVuSans.ttf", 24)
        button_font = ImageFont.truetype("DejaVuSans.ttf", 22)
    except OSError:
        title_font = body_font = button_font = ImageFont.load_default()
    draw.rounded_rectangle((220, 75, 1060, 645), radius=28, fill="white", outline="#c5d0df", width=3)
    draw.text((290, 125), "Veldhara Driver App", fill="#16263b", font=title_font)
    draw.text((290, 230), "Location data permission", fill="#25364d", font=body_font)
    draw.text((290, 290), "I agree to location tracking", fill="#25364d", font=body_font)
    draw.rounded_rectangle((290, 390, 690, 465), radius=12, fill="#2367d1")
    draw.text((365, 412), "I agree", fill="white", font=button_font)
    draw.text((290, 535), "No withdraw option is shown on this screen.", fill="#7d3b36", font=body_font)
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def generate_demo_files(output_dir: Path) -> dict[str, Path]:
    """Write all available demo files and return them by stable key."""
    output_dir.mkdir(parents=True, exist_ok=True)
    files: dict[str, tuple[str, bytes | None]] = {
        "policy": (
            "Veldhara_Information_Security_Policy_v3.1.pdf",
            _pdf(
                "Veldhara Information Security Policy v3.1",
                [
                    "Owner: Chief Information Security Officer.",
                    "Approved by the board risk committee.",
                    "This policy is reviewed every 12 months and communicated to staff.",
                    "Multi-factor authentication is required for remote access.",
                ],
            ),
        ),
        "ropa": (
            "Veldhara_Records_of_Processing_FY26.docx",
            _docx(
                "Records of Processing Activities FY26",
                ["The privacy officer reviews this register each quarter."],
                headers=("Activity", "Purpose", "Retention"),
                rows=(
                    ("Driver KYC", "Driver onboarding and safety checks", "Contract plus 7 years"),
                    ("Consignee contacts", "Delivery coordination", "24 months after delivery"),
                    ("Payroll", "Employee administration", "7 years"),
                ),
            ),
        ),
        "access_q2": (
            "Veldhara_Access_Review_Q2_FY26.docx",
            _docx(
                "Quarterly User Access Review Q2 FY26",
                [
                    "The quarterly review covered 9 of 11 production systems.",
                    "The TMS and driver mobile app were out of scope for this review.",
                ],
            ),
        ),
        "incident_plan": (
            "Veldhara_Incident_Response_Plan_v1.pdf",
            _pdf(
                "Veldhara Incident Response Plan v1",
                [
                    "Roles: incident lead, IT operations, privacy officer, and communications lead.",
                    "Steps: detect, triage, contain, investigate, notify, recover, and learn.",
                    "The plan exists but has not yet been tested.",
                ],
            ),
        ),
        "dr_report": (
            "Veldhara_DR_Failover_Test_Report.docx",
            _docx(
                "Disaster Recovery Failover Test Report",
                [
                    "Failover completed in 3h 10m against a 4h RTO.",
                    "The test passed and the results were reviewed by IT operations.",
                ],
            ),
        ),
        "consent_screen": (
            "Veldhara_Driver_App_Consent_Screen.png",
            _png(),
        ),
        "access_export": (
            "Veldhara_User_Access_Review_Export.xlsx",
            _xlsx(),
        ),
        "stale_access": (
            "Veldhara_Access_Review_Dec_2023.docx",
            _docx(
                "User access review, 31 December 2023",
                [
                    "User access review, 31 December 2023.",
                    "This file is retained as a stale historical example.",
                ],
            ),
        ),
    }
    paths: dict[str, Path] = {}
    for key, (filename, content) in files.items():
        if content is None:
            continue
        path = output_dir / filename
        path.write_bytes(content)
        paths[key] = path
    return paths
