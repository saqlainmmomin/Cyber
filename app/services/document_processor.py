"""
Document text extraction for PDF, DOCX, spreadsheets, and image files.

Supported:
- PDF: text extraction via pdfplumber
- DOCX: text extraction via python-docx
- XLSX / CSV: tabular text extraction with row-boundary size guards
- PNG / JPG / JPEG / WEBP: content description via Claude vision API
"""

import base64
import codecs
import csv
import io
import os
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

import pdfplumber
from docx import Document
from openpyxl import load_workbook

from app.config import settings
from app.services import llm_client

# Media type map for Claude vision
_IMAGE_MEDIA_TYPES = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
}

PDF_OCR_TEXT_THRESHOLD = 20
PDF_OCR_MAX_PAGES = 10
PDF_OCR_RESOLUTION = 150
PDF_OCR_MAX_EDGE_PX = 2500
SPREADSHEET_MAX_CELL_CHARS = 2000

logger = logging.getLogger(__name__)


def extract_text(file_path: str, file_type: str) -> str:
    """Extract text from a PDF, DOCX, spreadsheet, or image file."""
    if file_type == "pdf":
        return _extract_pdf(file_path)
    elif file_type == "docx":
        return _extract_docx(file_path)
    elif file_type == "xlsx":
        return _extract_xlsx(file_path)
    elif file_type == "csv":
        return _extract_csv(file_path)
    elif file_type in _IMAGE_MEDIA_TYPES:
        return _extract_image(file_path, file_type)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def _extract_pdf(file_path: str) -> str:
    """Extract text from PDF using pdfplumber (handles tables well)."""
    pages = []
    skipped_pages = []
    ocr_enabled = bool(settings.openrouter_key.strip())
    ocr_count = 0
    with pdfplumber.open(file_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            page_parts = []
            text = page.extract_text() or ""
            if text.strip():
                page_parts.append(text)
            # Also extract tables as text
            for table in page.extract_tables():
                rows = []
                for row in table:
                    cells = [str(c) if c else "" for c in row]
                    rows.append(" | ".join(cells))
                if rows:
                    page_parts.append("\n".join(rows))
            page_text = "\n".join(page_parts).strip()
            if page_text:
                pages.append(page_text)
            if len(page_text) >= PDF_OCR_TEXT_THRESHOLD or not ocr_enabled:
                continue
            if ocr_count >= PDF_OCR_MAX_PAGES:
                skipped_pages.append(page_number)
                continue
            ocr_count += 1
            try:
                image_data = _pdf_page_png_base64(page)
                description = _call_claude_vision(image_data, "image/png")
            except Exception:
                logger.exception("OCR failed for page %s of %s", page_number, file_path)
                pages.append(f"[OCR failed for page {page_number}]")
                continue
            if description.strip():
                pages.append(f"[OCR page {page_number}]\n\n{description.strip()}")

    if skipped_pages:
        pages.append(f"[{_format_skipped_ocr_pages(skipped_pages)}]")

    full_text = "\n\n".join(pages)
    return _truncate(full_text)


def _pdf_page_png_base64(page) -> str:
    """Rasterise one PDF page for the existing vision request shape."""
    longest_edge_pt = max(float(page.width), float(page.height), 1.0)
    resolution = min(PDF_OCR_RESOLUTION, PDF_OCR_MAX_EDGE_PX * 72 / longest_edge_pt)
    rendered = page.to_image(resolution=resolution).original
    buffer = io.BytesIO()
    rendered.save(buffer, format="PNG")
    return base64.standard_b64encode(buffer.getvalue()).decode("utf-8")


def _format_skipped_ocr_pages(page_numbers: list[int]) -> str:
    ranges = []
    start = previous = page_numbers[0]
    for page_number in page_numbers[1:]:
        if page_number == previous + 1:
            previous = page_number
            continue
        ranges.append(str(start) if start == previous else f"{start}-{previous}")
        start = previous = page_number
    ranges.append(str(start) if start == previous else f"{start}-{previous}")
    return f"OCR skipped for pages {', '.join(ranges)}"


def _extract_xlsx(file_path: str) -> str:
    """Extract cached worksheet values without loading a workbook into memory."""
    workbook = load_workbook(file_path, read_only=True, data_only=True, keep_links=False)
    try:
        renderer = _SpreadsheetRenderer(settings.max_document_words)
        for worksheet in workbook.worksheets:
            _render_tabular_sheet(
                worksheet.title,
                lambda worksheet=worksheet: _worksheet_rows(worksheet),
                renderer=renderer,
            )
        return _truncate(renderer.render())
    finally:
        workbook.close()


def _extract_csv(file_path: str) -> str:
    """Extract a CSV as one named worksheet using the same tabular format."""
    renderer = _SpreadsheetRenderer(settings.max_document_words)
    _render_tabular_sheet(Path(file_path).stem, lambda: _csv_rows(file_path), renderer=renderer)
    return _truncate(renderer.render())


def _worksheet_rows(worksheet):
    return _normalized_rows(worksheet.iter_rows(values_only=True))


def _csv_rows(file_path: str):
    text = _decode_csv_bytes(Path(file_path).read_bytes())
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    previous_limit = csv.field_size_limit()
    csv.field_size_limit(max(previous_limit, len(text) + 1))
    try:
        yield from _normalized_rows(csv.reader(io.StringIO(text, newline=""), dialect))
    finally:
        csv.field_size_limit(previous_limit)


def _decode_csv_bytes(data: bytes) -> str:
    """Decode UTF-16 (BOM), UTF-8, or fall back to Windows-1252 (Excel's CSV export)."""
    if data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return data.decode("utf-16", errors="replace")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("cp1252", errors="replace")


def _normalized_rows(rows):
    for row in rows:
        values = [_cell_text(value) for value in row]
        while values and not values[-1]:
            values.pop()
        if values:
            yield values


def _cell_text(value) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r", " ").replace("\n", " ").strip()
    if len(text) > SPREADSHEET_MAX_CELL_CHARS:
        return text[:SPREADSHEET_MAX_CELL_CHARS] + " [cell truncated]"
    return text


def _word_count(text: str) -> int:
    return len(text.split())


@dataclass
class _RenderedTabularSheet:
    sheet_name: str
    title_line: str | None = None
    header_line: str | None = None
    data_lines: list[str] = field(default_factory=list)
    data_word_counts: list[int] = field(default_factory=list)
    total_data_rows: int = 0
    truncated: bool = False
    not_stored: bool = False


class _SpreadsheetRenderer:
    """Build spreadsheet text while only admitting complete rows into the budget."""

    def __init__(self, max_words: int):
        self.max_words = max_words
        self.sheets: list[_RenderedTabularSheet] = []
        self.word_count = 0
        self.size_limit_reached = False

    def add_sheet(self, sheet_name: str, rows_factory) -> None:
        rows = rows_factory()
        header = next(rows, None)
        if header is None:
            return

        sheet = _RenderedTabularSheet(sheet_name=sheet_name)
        self.sheets.append(sheet)
        if self.size_limit_reached:
            sheet.not_stored = True
            return

        title_line = f"Sheet: {sheet_name}"
        header_line = " | ".join(header)
        header_words = _word_count(title_line) + _word_count(header_line)
        if self.word_count + header_words > self.max_words:
            sheet.not_stored = True
            self.size_limit_reached = True
            return

        sheet.title_line = title_line
        sheet.header_line = header_line
        self.word_count += header_words

        for row in rows:
            sheet.total_data_rows += 1
            row_line = " | ".join(row)
            row_words = _word_count(row_line)
            if sheet.truncated:
                continue
            if self.word_count + row_words <= self.max_words:
                sheet.data_lines.append(row_line)
                sheet.data_word_counts.append(row_words)
                self.word_count += row_words
            else:
                sheet.truncated = True
                self.size_limit_reached = True

    def _partial_marker(self, sheet: _RenderedTabularSheet) -> str:
        return (
            f'[stored rows 1-{len(sheet.data_lines):,} of {sheet.total_data_rows:,} '
            f'in sheet "{sheet.sheet_name}"; the remaining rows were not stored]'
        )

    def _not_stored_marker(self, sheet: _RenderedTabularSheet) -> str:
        return f'[sheet "{sheet.sheet_name}" not stored: size limit reached]'

    def _marker_word_count(self, sheet: _RenderedTabularSheet) -> int:
        if sheet.not_stored:
            return _word_count(self._not_stored_marker(sheet))
        if sheet.truncated:
            return _word_count(self._partial_marker(sheet))
        return 0

    def _word_count_with_markers(self) -> int:
        return self.word_count + sum(self._marker_word_count(sheet) for sheet in self.sheets)

    def _trim_to_marker_budget(self) -> None:
        """Trim only trailing data rows if marker lines need additional room."""
        while self._word_count_with_markers() > self.max_words:
            target = next(
                (
                    sheet
                    for sheet in reversed(self.sheets)
                    if sheet.truncated and sheet.data_lines
                ),
                None,
            )
            if target is None:
                target = next(
                    (
                        sheet
                        for sheet in reversed(self.sheets)
                        if not sheet.not_stored and sheet.data_lines
                    ),
                    None,
                )
                if target is None:
                    return
                target.truncated = True

            target.data_lines.pop()
            row_words = target.data_word_counts.pop()
            self.word_count -= row_words

    def render(self) -> str:
        self._trim_to_marker_budget()
        parts = []
        for sheet in self.sheets:
            if sheet.not_stored:
                parts.append(self._not_stored_marker(sheet))
                continue
            lines = [sheet.title_line, sheet.header_line, *sheet.data_lines]
            if sheet.truncated:
                lines.append(self._partial_marker(sheet))
            parts.append("\n".join(line for line in lines if line is not None))
        return "\n\n".join(parts)


def _render_tabular_sheet(sheet_name: str, rows_factory, *, renderer=None) -> str:
    active_renderer = renderer or _SpreadsheetRenderer(settings.max_document_words)
    active_renderer.add_sheet(sheet_name, rows_factory)
    return "" if renderer is not None else active_renderer.render()


def _extract_docx(file_path: str) -> str:
    """Extract text from DOCX including paragraphs and tables."""
    doc = Document(file_path)
    parts = []
    for para in doc.paragraphs:
        if para.text.strip():
            parts.append(para.text)
    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            parts.append(" | ".join(cells))
    full_text = "\n".join(parts)
    return _truncate(full_text)


def _truncate(text: str) -> str:
    """Truncate text to max_document_words while preserving line breaks."""
    # Clean up whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    max_words = settings.max_document_words
    cutoff = next(
        (
            match
            for index, match in enumerate(re.finditer(r"\S+", text))
            if index == max_words
        ),
        None,
    )
    if cutoff is not None:
        return text[: cutoff.start()].rstrip() + "\n\n[... truncated to first {} words ...]".format(
            max_words
        )
    return text


def extract_relevant_sections(text: str, focus_areas: list[str], max_words: int = 5000) -> str:
    """
    Extract sections of a document most relevant to the given focus areas.

    Uses section headers as anchors instead of cutting mid-sentence.
    Falls back to word-count truncation if no headers are detected.
    """
    # Split by common section headers (lines that look like headings)
    header_pattern = re.compile(
        r"^(?:\d+[\.\)]\s*|#{1,3}\s*|[A-Z][A-Z\s]{3,}:?\s*$)",
        re.MULTILINE,
    )
    headers = list(header_pattern.finditer(text))

    if len(headers) < 2:
        # No detectable sections — fall back to word-count truncation
        return _truncate_to_words(text, max_words)

    # Build sections from header positions
    sections = []
    for i, match in enumerate(headers):
        start = match.start()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        section_text = text[start:end].strip()
        sections.append(section_text)

    # Score each section by keyword overlap with focus areas
    focus_lower = [f.lower() for f in focus_areas]
    scored = []
    for section in sections:
        section_lower = section.lower()
        score = sum(1 for kw in focus_lower if kw in section_lower)
        scored.append((score, section))

    # Sort by relevance (highest score first), then assemble up to max_words
    scored.sort(key=lambda x: x[0], reverse=True)

    result_parts = []
    total_words = 0
    for score, section in scored:
        words = section.split()
        if total_words + len(words) > max_words:
            remaining = max_words - total_words
            if remaining > 50:  # Only include if we can fit a meaningful chunk
                result_parts.append(" ".join(words[:remaining]))
                total_words += remaining
            break
        result_parts.append(section)
        total_words += len(words)

    return "\n\n".join(result_parts)


def _truncate_to_words(text: str, max_words: int) -> str:
    """Truncate text to max_words, trying to end at a sentence boundary."""
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    words = text.split()
    if len(words) <= max_words:
        return text
    truncated = " ".join(words[:max_words])
    # Try to end at last sentence boundary
    last_period = truncated.rfind(".")
    if last_period > len(truncated) * 0.8:
        truncated = truncated[: last_period + 1]
    return truncated + "\n\n[... truncated ...]"


def _extract_image(file_path: str, file_type: str) -> str:
    """
    Extract compliance-relevant content from an image using Claude vision.

    Returns a structured text description of what is visible in the screenshot
    so it can be fed into the evidence extraction pipeline.
    """
    media_type = _IMAGE_MEDIA_TYPES[file_type]
    with open(file_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    description = _call_claude_vision(image_data, media_type)
    filename = os.path.basename(file_path)
    return f"[Screenshot: {filename}]\n\n{description}"


def _call_llm(*, tier: str, stream: bool = False, **request) -> dict:
    """Seam for the OpenRouter-backed client — patched directly in tests."""
    return llm_client.call_llm(tier, stream=stream, **request)


def _call_claude_vision(image_data: str, media_type: str) -> str:
    """Call the vision model for an encoded image and return raw response text."""
    with llm_client.call_tag(stage="vision"):
        response = _call_llm(
            tier="vision",
            max_tokens=1500,
            # 0: vision feeds OCR; run-to-run stability is measured by P5-9 (P6-1).
            temperature=0,
            system=(
                "You are a compliance document analyst. When shown a screenshot or image, "
                "extract and transcribe all visible text exactly as it appears. Then add a "
                "brief structured summary of what the image shows in the context of data "
                "protection compliance (e.g. consent screen, privacy policy excerpt, cookie "
                "banner, breach log, data flow diagram). Format: first transcribe the text "
                "verbatim under 'VISIBLE TEXT:', then add 'SUMMARY:' with 2-3 sentences "
                "describing what compliance-relevant controls or gaps the image reveals."
            ),
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_data}",
                            },
                        },
                        {
                            "type": "text",
                            "text": (
                                "Please transcribe all visible text from this image and provide "
                                "a compliance-focused summary of what it shows."
                            ),
                        },
                    ],
                }
            ],
        )
    return response["text"]


def detect_file_type(filename: str) -> str | None:
    """Detect file type from extension."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "pdf":
        return "pdf"
    elif ext == "docx":
        return "docx"
    elif ext in {"xlsx", "csv"}:
        return ext
    elif ext in _IMAGE_MEDIA_TYPES:
        return ext
    return None
