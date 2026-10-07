"""Focused extraction contracts for flow-rework evidence files."""

from __future__ import annotations

from unittest.mock import Mock

from fpdf import FPDF
from openpyxl import Workbook
from PIL import Image

from app.config import settings
from app.services import document_processor


def _write_large_workbook(path):
    workbook = Workbook()
    access_reviews = workbook.active
    access_reviews.title = "Access reviews"
    access_reviews.append(["User", "Status"])
    for row_number in range(1, 5001):
        access_reviews.append([f"user-{row_number}", "Active"])

    assets = workbook.create_sheet("Asset register")
    assets.append(["Asset", "Owner"])
    assets.append(["Laptop-01", "Security"])
    workbook.save(path)


def test_xlsx_extraction_includes_sheet_headers_and_samples_large_sheets(tmp_path):
    path = tmp_path / "access-reviews.xlsx"
    _write_large_workbook(path)

    text = document_processor.extract_text(str(path), "xlsx")

    assert "Sheet: Access reviews" in text
    assert "Sheet: Asset register" in text
    assert "User | Status" in text
    assert "user-1 | Active" in text
    assert "[sampled 200 of 5,000 rows]" in text
    assert "[... truncated" not in text
    assert len(text.split()) < settings.max_document_words


def test_csv_extraction_round_trips_rows(tmp_path):
    path = tmp_path / "assets.csv"
    path.write_text("Asset,Owner\nLaptop-01,Security\n", encoding="utf-8")

    text = document_processor.extract_text(str(path), "csv")

    assert "Sheet: assets" in text
    assert "Asset | Owner" in text
    assert "Laptop-01 | Security" in text


def test_scanned_pdf_uses_vision_once_for_an_image_only_page(tmp_path, monkeypatch):
    path = tmp_path / "scanned.pdf"
    Image.new("RGB", (300, 120), "white").save(path, "PDF")
    vision = Mock(return_value="VISIBLE TEXT: signed access review")
    monkeypatch.setattr(settings, "openrouter_key", "test-key")
    monkeypatch.setattr(document_processor, "_call_claude_vision", vision)

    text = document_processor.extract_text(str(path), "pdf")

    assert "signed access review" in text
    vision.assert_called_once()


def test_text_pdf_does_not_use_vision(tmp_path, monkeypatch):
    path = tmp_path / "native.pdf"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(text="Native page text with enough characters")
    pdf.output(str(path))
    vision = Mock()
    monkeypatch.setattr(document_processor, "_call_claude_vision", vision)

    text = document_processor.extract_text(str(path), "pdf")

    assert "Native page text with enough characters" in text
    vision.assert_not_called()


def test_ocr_failure_on_one_page_keeps_the_rest_of_the_document(tmp_path, monkeypatch):
    path = tmp_path / "scan.pdf"
    Image.new("RGB", (600, 800), "white").save(path, "PDF")
    monkeypatch.setattr(settings, "openrouter_key", "test-key")
    monkeypatch.setattr(document_processor, "_call_claude_vision", Mock(side_effect=RuntimeError("upstream 503")))

    assert "[OCR failed for page 1]" in document_processor.extract_text(str(path), "pdf")


def test_csv_from_excel_on_windows_decodes_as_cp1252(tmp_path):
    path = tmp_path / "export.csv"
    path.write_bytes("name;city\nJosé;Zürich\n".encode("cp1252"))

    text = document_processor.extract_text(str(path), "csv")

    assert "José | Zürich" in text
