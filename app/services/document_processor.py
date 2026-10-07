"""
Document text extraction for PDF, DOCX, spreadsheets, and image files.

Supported:
- PDF: text extraction via pdfplumber
- DOCX: text extraction via python-docx
- XLSX / CSV: tabular text extraction with bounded row sampling
- PNG / JPG / JPEG / WEBP: content description via Claude vision API
"""

import base64
import codecs
import csv
import io
import os
import logging
import re
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

# Keep spreadsheet extraction below the document word budget while preserving
# the beginning and shape of large evidence registers.
SPREADSHEET_MAX_DATA_ROWS = 200
SPREADSHEET_INITIAL_DATA_ROWS = 100
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
        parts = []
        for worksheet in workbook.worksheets:
            rendered = _render_tabular_sheet(
                worksheet.title,
                lambda worksheet=worksheet: _worksheet_rows(worksheet),
            )
            if rendered:
                parts.append(rendered)
        return _truncate("\n\n".join(parts))
    finally:
        workbook.close()


def _extract_csv(file_path: str) -> str:
    """Extract a CSV as one named worksheet using the same tabular format."""
    return _truncate(
        _render_tabular_sheet(
            Path(file_path).stem,
            lambda: _csv_rows(file_path),
        )
    )


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


def _render_tabular_sheet(sheet_name: str, rows_factory) -> str:
    rows = rows_factory()
    try:
        header = next(rows)
    except StopIteration:
        return ""

    data_rows = sum(1 for _row in rows)
    selected_indices = _sampled_row_indices(data_rows)
    selected = []
    rows = rows_factory()
    next(rows, None)
    for index, row in enumerate(rows, start=1):
        if index in selected_indices:
            selected.append(row)

    lines = [f"Sheet: {sheet_name}", " | ".join(header)]
    lines.extend(" | ".join(row) for row in selected)
    if data_rows > SPREADSHEET_MAX_DATA_ROWS:
        lines.append(f"[sampled {len(selected)} of {data_rows:,} rows]")
    return "\n".join(lines)


def _sampled_row_indices(total_rows: int) -> set[int]:
    if total_rows <= SPREADSHEET_MAX_DATA_ROWS:
        return set(range(1, total_rows + 1))
    initial = min(SPREADSHEET_INITIAL_DATA_ROWS, SPREADSHEET_MAX_DATA_ROWS)
    sample_count = SPREADSHEET_MAX_DATA_ROWS - initial
    indices = set(range(1, initial + 1))
    start = initial + 1
    end = total_rows
    if sample_count == 1:
        indices.add(end)
    else:
        indices.update(
            start + ((end - start) * offset // (sample_count - 1))
            for offset in range(sample_count)
        )
    return indices


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
