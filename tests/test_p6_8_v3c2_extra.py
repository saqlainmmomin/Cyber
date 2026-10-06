"""V3-C2 deck invariants that are easy to lose during visual iteration."""

from __future__ import annotations

import copy
import io
import json
import re
import shutil
import subprocess
from pathlib import Path

import pdfplumber
import pytest

from app.services import board_report, board_view
from tests.p6_8_v3_support import load_deck_document


FRAMEWORK_IDS = ("dpdpa", "gdpr", "hipaa", "iso27001", "nist_csf", "pci_dss")
REPO_ROOT = Path(__file__).resolve().parents[1]


def _pdf(document: dict) -> bytes:
    return board_report.render_pdf(document)


def _thin_document() -> dict:
    document = copy.deepcopy(load_deck_document())
    framework_id = "iso27001"
    framework = next(item for item in document["frameworks"] if item["framework_id"] == framework_id)
    summary_framework = next(item for item in document["summary"]["frameworks"] if item["framework_id"] == framework_id)
    observations = [item for item in document["observations"] if item.get("framework_id") == framework_id][:3]
    if len(observations) < 3:
        observations = document["observations"][:3]
    refs = {item["ref"] for item in observations}

    document["frameworks"] = [framework]
    document["summary"]["frameworks"] = [summary_framework]
    document["summary"]["scope"] = [document["summary"]["scope"][1]]
    document["summary"]["risk_matrix"] = {framework_id: document["summary"]["risk_matrix"][framework_id]}
    document["framework_sections"] = [item for item in document["framework_sections"] if item["framework_id"] == framework_id]
    document["status_board"] = [item for item in document["status_board"] if item["framework_id"] == framework_id]
    document["observations"] = observations
    document["initiatives"] = [item for item in document["initiatives"] if refs.intersection(item.get("obs_refs", []))]
    document["register"] = [item for item in document.get("register", []) if item.get("framework_id") == framework_id]
    document["appendices"]["requirement_register"] = [
        item for item in document["appendices"].get("requirement_register", []) if item.get("framework_id") == framework_id
    ]
    document["prior_period"] = {
        "status": "no_prior",
        "prior": None,
        "frameworks": [],
        "totals": None,
        "changes": [],
    }
    document["board_asks"]["consultant"] = document["board_asks"]["consultant"][:1]
    return document


def _walk_boxes(box):
    yield box
    for child in getattr(box, "children", ()):
        yield from _walk_boxes(child)


def _assert_no_empty_bottom_third(pdf: bytes, tmp_path: Path, label: str) -> None:
    if shutil.which("pdftoppm") is None:
        pytest.skip("pdftoppm is not installed; the pixel smoke check runs where poppler is available")
    source = tmp_path / label
    source.write_bytes(pdf)
    subprocess.run(
        ["pdftoppm", "-png", "-r", "24", str(source), str(source)],
        check=True,
        capture_output=True,
    )
    from PIL import Image

    pages = sorted(tmp_path.glob(f"{label}-*.png"))
    assert pages
    for page in pages:
        image = Image.open(page).convert("RGB")
        bottom = image.crop((0, image.height * 2 // 3, image.width, image.height))
        non_white = sum(1 for pixel in bottom.getdata() if min(pixel) < 245)
        assert non_white > 100, f"{label} has an empty bottom third on {page.name}"


def test_v3c2_pdf_page_count_and_vertical_rhythm_for_dense_and_thin_documents(tmp_path):
    for label, document in (("golden", load_deck_document()), ("thin", _thin_document())):
        pdf = _pdf(document)
        assert len(pdf) > 1000
        with pdfplumber.open(io.BytesIO(pdf)) as parsed:
            assert len(parsed.pages) == len(board_view.view(document)["slides"])
        _assert_no_empty_bottom_third(pdf, tmp_path, label)


def test_v3c2_computed_body_and_table_font_sizes_meet_the_deck_floor():
    from weasyprint import HTML

    html = board_report.render_html(load_deck_document(), embed_fonts=False)
    rendered = HTML(string=html, base_url=str(REPO_ROOT)).render()
    page_boxes = [page._page_box for page in rendered.pages]
    html_boxes = [box for root in page_boxes for box in _walk_boxes(root) if box.element_tag == "html"]
    assert html_boxes and html_boxes[0].style["font_size"] >= 11 * 96 / 72
    table_cells = [
        box for root in page_boxes for box in _walk_boxes(root)
        if box.element_tag in {"td", "th"}
    ]
    assert table_cells
    assert min(box.style["font_size"] for box in table_cells) >= 9 * 96 / 72


def test_v3c2_dumbbell_only_uses_compared_prior_domains_and_has_no_mock_values():
    document = load_deck_document()
    for framework in document["prior_period"]["frameworks"]:
        domain_ids = [
            domain["domain_id"]
            for section in document["framework_sections"]
            if section["framework_id"] == framework["framework_id"]
            for domain in section["domains"]
        ]
        framework["domains"] = [
            {"domain_id": domain_ids[0], "compared": True, "prior_score": 31.0},
            {"domain_id": domain_ids[1], "compared": False, "prior_score": 99.0},
        ]
    presentation = board_view.view(document)
    rows = [row for group in presentation["dumb"] for row in group["rows"]]
    assert any(row["was"] == 31.0 for row in rows)
    assert any(row["was"] is None for row in rows)
    html = board_report.render_html(document, embed_fonts=False)
    assert "MOCK_PRIOR_DOMAINS" not in html
    assert "31.0" in html


def test_v3c2_all_six_registered_frameworks_render_without_keyerror():
    base = load_deck_document()
    source_summary = next(item for item in base["summary"]["frameworks"] if item["framework_id"] == "iso27001")
    source_status = next(item for item in base["status_board"] if item["framework_id"] == "iso27001")
    source_sections = next(item for item in base["framework_sections"] if item["framework_id"] == "iso27001")
    source_matrix = base["summary"]["risk_matrix"]["iso27001"]
    for framework_id in FRAMEWORK_IDS:
        document = copy.deepcopy(base)
        summary = copy.deepcopy(source_summary)
        summary.update({"framework_id": framework_id, "name": framework_id.upper(), "framework_short": framework_id.upper()})
        document["summary"]["frameworks"] = [summary]
        document["summary"]["scope"] = [f"Scope for {framework_id}"]
        document["summary"]["risk_matrix"] = {framework_id: copy.deepcopy(source_matrix)}
        framework = next((item for item in document["frameworks"] if item["framework_id"] == framework_id), None)
        if framework is None:
            framework = {"framework_id": framework_id, "name": framework_id.upper(), "version": "current", "legal": framework_id == "dpdpa"}
        else:
            framework = copy.deepcopy(framework)
        framework.update({"name": framework_id.upper(), "framework_short": framework_id.upper()})
        document["frameworks"] = [framework]
        status = copy.deepcopy(source_status)
        status["framework_id"] = framework_id
        status["name"] = framework_id.upper()
        document["status_board"] = [status]
        sections = copy.deepcopy(source_sections)
        sections["framework_id"] = framework_id
        document["framework_sections"] = [sections]
        board_report.render_html(document, embed_fonts=False)


def test_v3c2_devanagari_company_name_survives_the_html_and_pdf_cover_path():
    document = load_deck_document()
    document["company_name"] = "भारत डेटा प्राइवेट लिमिटेड"
    html = board_report.render_html(document, embed_fonts=True)
    assert document["company_name"] in html
    assert "NotoSansDevanagari" in html
    with pdfplumber.open(io.BytesIO(_pdf(document))) as parsed:
        cover = parsed.pages[0].extract_text() or ""
    assert all(character in cover for character in "भारत डेटा प्राइवेट लिमिटेड" if not character.isspace())


def test_v3c2_action_titles_only_use_numbers_present_in_the_document():
    document = load_deck_document()
    document_text = json.dumps(document, ensure_ascii=False)
    derived_numbers = {
        str(sum(
            sum(int(framework.get("coverage", {}).get(key, 0) or 0) for key in ("compliant", "partially_compliant", "non_compliant"))
            for framework in document["summary"]["frameworks"]
        )),
        str(sum(int(framework.get("coverage", {}).get("partially_compliant", 0) or 0) + int(framework.get("coverage", {}).get("non_compliant", 0) or 0) for framework in document["summary"]["frameworks"])),
    }
    for slide in board_view.view(document)["slides"]:
        for number in re.findall(r"\b\d+(?:\.\d+)?\b", slide["title"]):
            assert number in document_text or number in derived_numbers, (slide["slide"], slide["title"], number)
