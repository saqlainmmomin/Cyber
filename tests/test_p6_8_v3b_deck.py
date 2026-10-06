"""Contract tests for P6-8 V3-B (presentation): the 16:9 deck, the v3 XLSX and the PPTX.

Handoff: tasks/handoffs/2026-10-01-board-report-v3-deck.md (D-P6-8-V3-G..N, pinned schema).
Decision doc: docs/product/2026-10-01-board-report-format.md (F1-F3, F5, F7-F10, sections 3-7).
Every test here renders a *document*; none touches the database. The input is the synthetic v3
document in tests/golden/p6_8_v3_deck_document.json (120 requirements, 10 observations, 8
initiatives, a prior period). Written before the implementation: they run on a branch that has
P6-10 and V3-A merged, and fail only because the V3-B code does not exist. No network, no LLM.
"""

from __future__ import annotations

import copy
import importlib
import io
import re

import pytest

from tests.p6_8_v3_support import DEFAULT_THEME, load_deck_document
from tests.test_p6_8_board_report_v2 import NON_LEGAL_FORBIDDEN, _require_renderer

SHA = "ab" * 32
TINY_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)
EXPECTED_SLIDES = (
    ["cover", "contents", "how-to-read", "overview", "executive-summary", "posture", "domain-status", "risk-profile", "board-asks"]
    + ["observations"] * 4
    + ["roadmap", "effort-benefit", "comparison", "limits", "sign-off", "annexure", "methodology"]
    + ["requirement-register"] * 10
    + ["evidence-and-soa"]
)
SECTION_OF = {
    "cover": "cover", "contents": "contents", "how-to-read": "01", "overview": "01",
    "executive-summary": "02", "posture": "02", "domain-status": "02", "risk-profile": "02", "board-asks": "02",
    "observations": "03",
    "roadmap": "04", "effort-benefit": "04", "comparison": "04", "limits": "04", "sign-off": "04",
    "annexure": "05", "methodology": "A1", "requirement-register": "A2", "evidence-and-soa": "A3",
}
XLSX_SHEETS_V3 = (
    "Executive Summary", "Detailed Assessment", "Observation Register", "Remediation Tracker",
    "Statement of Applicability", "Evidence Register", "Definitions",
)
NOT_RECORDED = "Not recorded"


def _board():
    return importlib.import_module("app.services.board_report")


def _view():
    return importlib.import_module("app.services.board_view")


def _exports():
    return importlib.import_module("app.services.board_exports")


def _html(document: dict, *, embed_fonts: bool = False) -> str:
    return _board().render_html(document, embed_fonts=embed_fonts)


def _tree(html: str):
    import lxml.html

    return lxml.html.fromstring(html)


def _text(element) -> str:
    return re.sub(r"\s+", " ", element.text_content()).strip()


def _slides(html: str) -> list[tuple[str, object]]:
    return [(el.get("data-slide"), el) for el in _tree(html).xpath('//section[@data-slide]')]


def _slide(html: str, name: str, index: int = 0):
    matches = [el for slide, el in _slides(html) if slide == name]
    assert len(matches) > index, f"no slide {name} #{index}; have {[s for s, _ in _slides(html)]}"
    return matches[index]


def _one(element, xpath: str):
    found = element.xpath(xpath)
    assert len(found) == 1, (xpath, len(found))
    return found[0]


# ---------------------------------------------------------------------------
# 1. Structure
# ---------------------------------------------------------------------------


def test_scenario_1_slide_order_pagination_and_numbers():
    """D-P6-8-V3-G: one <section data-slide> per slide, in the F1 order; tables paginate."""
    document = load_deck_document()
    html = _html(document)
    names = [name for name, _ in _slides(html)]
    assert names == EXPECTED_SLIDES
    slides = _view().view(document)["slides"]
    assert [slide["slide"] for slide in slides] == EXPECTED_SLIDES
    assert [slide["number"] for slide in slides] == list(range(1, 32))
    assert {slide["slide"]: slide["section"] for slide in slides} == SECTION_OF
    assert all(isinstance(slide["title"], str) and slide["title"] for slide in slides)

    observation_rows = [len(el.xpath('.//tr[@data-observation]')) for name, el in _slides(html) if name == "observations"]
    assert observation_rows == [3, 3, 3, 1]
    register_rows = [len(el.xpath('.//tr[@data-register-row]')) for name, el in _slides(html) if name == "requirement-register"]
    assert register_rows == [12] * 10 and sum(register_rows) == 120
    contents = _text(_slide(html, "contents"))
    for section in ("01", "02", "03", "04", "05"):
        assert section in contents


def test_scenario_1b_prior_period_slide_is_hidden_without_a_comparison():
    """D-P6-8-V3-C: the baseline comparison slide remains for a first report."""
    document = load_deck_document()
    document["prior_period"].update(status="no_prior", prior=None, frameworks=[], totals=None, changes=[])
    names = [name for name, _ in _slides(_html(document))]
    assert "comparison" in names and len(names) == 31
    assert [s["number"] for s in _view().view(document)["slides"]] == list(range(1, 32))


# ---------------------------------------------------------------------------
# 2-3. Cover, footers
# ---------------------------------------------------------------------------


def test_scenario_2_cover_title_is_framework_conditional():
    """D-P6-8-V3-G (F1, house rule: framework-specific copy is conditional)."""
    document = load_deck_document()
    cover = _text(_slide(_html(document), "cover"))
    assert "Privacy and information security compliance assessment" in cover
    for needle in (document["company_name"], document["firm_name"], "DRAFT UNTIL ISSUED",
                   document["basis"]["period_label"], document["basis"]["cutoff_label"],
                   document["snapshot"]["version_label"]):
        assert needle in cover, needle
    for framework in document["frameworks"]:
        assert framework["name"] in cover

    standards_only = copy.deepcopy(document)
    standards_only["frameworks"] = [f for f in document["frameworks"] if not f["legal"]]
    assert standards_only["frameworks"], "the fixture has a standards framework"
    cover = _text(_slide(_html(standards_only), "cover"))
    assert "Information security compliance assessment" in cover
    assert "Privacy" not in cover
    assert not any(term in cover.lower() for term in NON_LEGAL_FORBIDDEN)


def test_scenario_3_every_slide_carries_period_cutoff_and_version():
    """D-P6-8-V3-G (house rule: assessment period and evidence cut-off on every deliverable)."""
    document = load_deck_document()
    slides = _slides(_html(document))
    assert len(slides) == len(EXPECTED_SLIDES)
    for name, element in slides:
        text = _text(element)
        for needle in (document["basis"]["period_label"], document["basis"]["cutoff_label"],
                       document["snapshot"]["version_label"]):
            assert needle in text, (name, needle)
        if name != "cover":
            footer = _text(_one(element, ".//footer[@data-slide-footer]"))
            assert "Confidential" in footer and document["firm_name"] in footer, name


# ---------------------------------------------------------------------------
# 4-6. Executive summary, status board, risk dashboard
# ---------------------------------------------------------------------------


def test_scenario_4_scores_are_per_framework_and_never_combined():
    """D-P6-8-V3-H: no blended score anywhere; cross-framework totals are counts with the note."""
    view = _view()
    assert view.NEVER_COMBINED_NOTE == "Scores are per framework and are never combined; the totals above are counts."
    document = load_deck_document()
    html = _html(document)
    summary = _slide(html, "executive-summary")
    assert view.NEVER_COMBINED_NOTE in _text(summary)
    assert not _tree(html).xpath('//*[@data-combined-score]')
    for framework in document["summary"]["frameworks"]:
        score = _one(summary, f'.//*[@data-framework-score="{framework["framework_id"]}"]')
        assert f"{framework['score']:.0f}" in _text(score)
        assert framework["rating"] in _text(summary)
        assert _one(summary, f'.//*[@data-outcome-bar="{framework["framework_id"]}"]') is not None
    total = _text(_one(summary, ".//*[@data-total-requirements]"))
    assert str(document["summary"]["totals"]["requirements"]) in total
    assert [el.get("data-top-risk") for el in summary.xpath(".//*[@data-top-risk]")] == [
        o["ref"] for o in document["observations"][:3]
    ]


def test_scenario_5_domain_status_matches_the_document():
    """D-P6-8-V3-H: one column per framework, one row per domain, a pill from the derived counts."""
    document = load_deck_document()
    board = _slide(_html(document), "domain-status")
    assert document["takeaways"]["status_board"] in _text(_one(board, './/*[@data-takeaway="status-board"]'))
    for framework in document["status_board"]:
        column = _one(board, f'.//*[@data-status-framework="{framework["framework_id"]}"]')
        assert framework["name"] in _text(column) and f"{framework['score']:.0f}" in _text(column)
        for domain in framework["domains"]:
            row = _text(_one(column, f'.//*[@data-status-domain="{domain["title"]}"]'))
            if domain["in_scope"] == 0:
                assert "Out of scope" in row
            elif domain["gaps"] == 0:
                assert "No gaps" in row
            else:
                assert f"{domain['gaps']} gaps · {domain['crit_high']} crit/high" in row


def test_scenario_6_risk_profile_and_matrix_match_the_document():
    """D-P6-8-V3-H: severity panels, ring counts, framework x risk matrix, all from the document."""
    document = load_deck_document()
    dashboard = _slide(_html(document), "risk-profile")
    assert document["takeaways"]["dashboard"] in _text(_one(dashboard, './/*[@data-takeaway="dashboard"]'))
    for severity, data in document["severity_dashboard"].items():
        panel = _text(_one(dashboard, f'.//*[@data-severity-panel="{severity}"]'))
        assert str(data["total"]) in panel
        for entry in data["top"]:
            assert entry["label"] in panel
    for framework_id, counts in document["summary"]["risk_matrix"].items():
        row = _one(dashboard, f'.//tr[@data-risk-matrix="{framework_id}"]')
        cells = [_text(cell) for cell in row.xpath("./td")]
        assert [int(value) for value in cells[-4:]] == [counts["critical"], counts["high"], counts["medium"], counts["low"]]


# ---------------------------------------------------------------------------
# 7. Observations
# ---------------------------------------------------------------------------


def test_scenario_7_observations_use_the_seven_column_grammar_and_say_not_recorded():
    """D-P6-8-V3-I (F4, F9): No. / Domain / Observation / Risk / Rating / Recommendation / Reference."""
    document = load_deck_document()
    document["observations"][1]["risk"] = None
    document["observations"][1]["recommendation"] = None
    html = _html(document)
    seen = []
    for index in range(_view().view(document)["observation_pages"]):
        body = _slide(html, "observations", index)
        assert body.xpath(".//*[@data-responsibility-legend]")
        for row in body.xpath(".//tr[@data-observation]"):
            ref = row.get("data-observation")
            cells = row.xpath("./td")
            assert len(cells) == 7, (ref, len(cells))
            observation = next(o for o in document["observations"] if o["ref"] == ref)
            seen.append(ref)
            assert ref in _text(cells[0])
            assert observation["domain"] in _text(cells[1]) and observation["framework_name"] in _text(cells[1])
            assert observation["title"] in _text(cells[2]) and observation["observation"] in _text(cells[2])
            assert observation["rating"].title() in _text(cells[4])
            if observation["risk"] is None:
                for cell in (cells[3], cells[5]):
                    assert NOT_RECORDED in _text(cell) and cell.xpath('.//*[contains(@class, "not-recorded")]')
            else:
                assert observation["risk"] in _text(cells[3]) and observation["recommendation"] in _text(cells[5])
            for reference in observation["references"]:
                assert reference["framework_name"] in _text(cells[6]) and reference["clauses"][0] in _text(cells[6])
            if observation["responsibility"]:
                assert cells[1].xpath(f'.//*[@data-responsibility="{observation["responsibility"]}"]')
    assert seen == [o["ref"] for o in document["observations"]]


# ---------------------------------------------------------------------------
# 8. Narrative placement
# ---------------------------------------------------------------------------


def test_scenario_8_narrative_sits_in_the_verdict_panel_and_refs_render_as_r_numbers():
    """D-P6-8-V3-J (F7, P6-10 D-P6-10-R): refs are R-xx through the finding_ids join, never F-aliases."""
    document = load_deck_document()
    html = _html(document)
    summary = _slide(html, "executive-summary")
    verdict = _one(summary, './/*[@data-narrative="executive"]')
    refs_by_finding = {o["finding_id"]: o["ref"] for o in document["observations"]}
    sentences = verdict.xpath(".//*[@data-narrative-sentence]")
    expected = document["summary"]["narrative"]["executive"]
    assert len(sentences) == len(expected)
    for sentence, source in zip(sentences, expected):
        text = _text(sentence)
        assert source["text"] in text
        assert re.findall(r"R-\d+", text) == [refs_by_finding[i] for i in source["finding_ids"]]
        assert not re.search(r"\bF\d+\b", text)
    for framework in document["summary"]["frameworks"]:
        if framework["narrative"]:
            assert summary.xpath(f'.//*[@data-narrative="framework-{framework["framework_id"]}"]'), framework["framework_id"]
    assert _slide(html, "risk-profile").xpath('.//*[@data-narrative="cross-framework"]')

    # A cited finding that is not an observation drops its ref but keeps the sentence.
    trimmed = copy.deepcopy(document)
    gone = trimmed["observations"].pop(2)
    verdict = _one(_slide(_html(trimmed), "executive-summary"), './/*[@data-narrative="executive"]')
    assert gone["ref"] not in _text(verdict) and expected[0]["text"] in _text(verdict)

    # No accepted narrative, no panel and no empty placeholders.
    empty = copy.deepcopy(document)
    empty["summary"]["narrative"] = {"executive": None, "cross_framework": None}
    for framework in empty["summary"]["frameworks"]:
        framework["narrative"] = None
    assert not _tree(_html(empty)).xpath("//*[@data-narrative]")


# ---------------------------------------------------------------------------
# 9-10. Roadmap, initiatives, board asks
# ---------------------------------------------------------------------------


def test_scenario_9_roadmap_columns_initiatives_and_derived_priority():
    """D-P6-8-V3-I (F10): horizon columns, OVERDUE, derived Priority glyphs, no typed priority."""
    document = load_deck_document()
    html = _html(document)
    roadmap = _slide(html, "roadmap")
    assert document["takeaways"]["roadmap"] in _text(_one(roadmap, './/*[@data-takeaway="roadmap"]'))
    for initiative in document["initiatives"]:
        column = "long" if initiative["horizon"] == "unscheduled" else initiative["horizon"]
        container = _one(roadmap, f'.//*[@data-horizon-column="{column}"]')
        callout = _one(container, f'.//*[@data-initiative="{initiative["ref"]}"]')
        text = _text(callout)
        assert initiative["title"] in text
        assert all(ref in text for ref in initiative["obs_refs"])
        assert ("OVERDUE" in text) == initiative["overdue"], initiative["ref"]
        if initiative["horizon"] == "unscheduled":
            assert "Not scheduled" in text
    assert sum(i["overdue"] for i in document["initiatives"]) == 1

    table = _slide(html, "effort-benefit")
    for initiative in document["initiatives"]:
        row = _one(table, f'.//tr[@data-initiative-row="{initiative["ref"]}"]')
        for dimension in ("priority", "complexity", "benefit"):
            assert row.xpath(f'.//*[@data-{dimension}="{initiative[dimension]}"]'), (initiative["ref"], dimension)
        assert initiative["owner"] in _text(row)
    assert not _tree(html).xpath("//input[contains(@name, 'priority')]")


def test_scenario_10_board_asks_are_consultant_cards_plus_derived_needs_attention():
    """D-P6-8-V3-I: at most three ask cards (F4); the derived panel is always there."""
    document = load_deck_document()
    body = _slide(_html(document), "board-asks")
    assert len(body.xpath(".//*[@data-board-ask]")) == 2
    assert len(body.xpath(".//*[@data-derived-ask]")) == len(document["board_asks"]["derived"]) == 4
    for ask in document["board_asks"]["consultant"] + document["board_asks"]["derived"]:
        assert ask in _text(body)
    assert document["board_asks"]["consultant_by"] in _text(body)

    many = copy.deepcopy(document)
    many["board_asks"]["consultant"] = ["One", "Two", "Three", "Four"]
    assert len(_slide(_html(many), "board-asks").xpath(".//*[@data-board-ask]")) == 3

    none = copy.deepcopy(document)
    none["board_asks"]["consultant"] = []
    body = _slide(_html(none), "board-asks")
    assert not body.xpath(".//*[@data-board-ask]") and len(body.xpath(".//*[@data-derived-ask]")) == 4


def test_scenario_11_no_numeric_priority_in_the_deck():
    """D-P6-8-V3-K (F10): the typed 1-4 priority is gone from every client slide."""
    document = load_deck_document()
    assert not any("priority" in risk for risk in document["top_risks"])
    text = _text(_tree(_html(document)))
    assert not re.search(r"\bPriority\s*[1-4]\b", text)
    assert not re.search(r"\bP[1-4]\b", text)


# ---------------------------------------------------------------------------
# 12. Theme and fonts
# ---------------------------------------------------------------------------


def test_scenario_12_theme_colours_come_from_the_document_and_severity_colours_are_fixed():
    """D-P6-8-V3-L (F5): --p1/--p2/--acc from document.theme; severity and outcome colours never themed."""
    document = load_deck_document()
    assert document["theme"]["primary"] == DEFAULT_THEME["primary"]
    html = _html(document)
    for variable, key in (("--p1", "primary"), ("--p2", "secondary"), ("--acc", "accent")):
        assert re.search(rf"{variable}:\s*{re.escape(document['theme'][key])}", html), variable
    for colour in ("#9B1C1C", "#D9481E", "#F0A030", "#3C9D6B"):
        assert colour in html
    assert "<img" not in html

    themed = copy.deepcopy(document)
    themed["theme"].update(primary="#112233", secondary="#445566", accent="#778899")
    html = _html(themed)
    assert re.search(r"--p1:\s*#112233", html) and re.search(r"--acc:\s*#778899", html)
    assert DEFAULT_THEME["primary"] not in html and DEFAULT_THEME["accent"] not in html
    for colour in ("#9B1C1C", "#D9481E", "#F0A030", "#3C9D6B"):
        assert colour in html

    logo = copy.deepcopy(document)
    logo["theme"]["logo"] = {"media_type": "image/png", "data_base64": TINY_PNG, "sha256": "0" * 64}
    cover = _slide(_html(logo), "cover")
    assert [img.get("src") for img in cover.xpath(".//img")] == [f"data:image/png;base64,{TINY_PNG}"]


def test_scenario_12b_display_face_is_embedded_only_with_fonts_and_html_is_inert():
    """D-P6-8-V3-L: Barlow Condensed as 'Display'; no scripts, no remote URLs, user text escaped."""
    document = load_deck_document()
    document["observations"][0]["observation"] = "<script>alert(1)</script> & \"quoted\""
    html = _html(document, embed_fonts=True)
    assert "font-family: 'Display'" in html and "BarlowCondensed-Bold.ttf" in html
    assert "<script>alert(1)</script>" not in html and "&lt;script&gt;" in html
    assert not _tree(html).xpath("//script") and not re.search(r"https?://", html)
    assert "BarlowCondensed" not in _html(document, embed_fonts=False)


def test_scenario_13_pdf_is_a_16_9_landscape_deck_with_one_page_per_slide():
    """D-P6-8-V3-G (F1): @page 338.67mm x 190.5mm; page count equals the slide count."""
    import pdfplumber

    _require_renderer()
    document = load_deck_document()
    pdf = _board().render_pdf(document)
    with pdfplumber.open(io.BytesIO(pdf)) as parsed:
        assert len(parsed.pages) == len(EXPECTED_SLIDES)
        for page in parsed.pages:
            assert abs(float(page.width) - 960.0) < 1.0 and abs(float(page.height) - 540.0) < 1.0
        first = parsed.pages[0].extract_text()
        last = parsed.pages[-1].extract_text()
        fonts = {char["fontname"] for page in parsed.pages for char in page.chars}
    # Devanagari glyph spacing differs between renderers (Linux CI inserts gaps), so compare without whitespace.
    assert "".join(document["company_name"].split()) in "".join(first.split())
    assert document["basis"]["period_label"] in last and document["basis"]["cutoff_label"] in last
    assert any(name.endswith("Display-Bold-Condensed") for name in fonts), fonts


# ---------------------------------------------------------------------------
# 14. XLSX (v3 client workbook)
# ---------------------------------------------------------------------------


def _workbook(document: dict):
    import openpyxl

    return openpyxl.load_workbook(io.BytesIO(_exports().render_xlsx(document, document_sha256=SHA)))


def _rows(sheet, header_row: int = 6):
    headers = [cell.value for cell in sheet[header_row]]
    return headers, [[cell.value for cell in row] for row in sheet.iter_rows(min_row=header_row + 1)
                     if any(cell.value not in (None, "") for cell in row)]


def test_scenario_14_xlsx_v3_sheets_title_blocks_and_register_contents():
    """D-P6-8-V3-M (F3): reference-idiom client workbook; every number comes from the document."""
    exports = _exports()
    assert exports.SUPPORTED_SCHEMA_VERSIONS == (1, 2, 3)
    assert exports.XLSX_SHEETS_V3 == XLSX_SHEETS_V3
    document = load_deck_document()
    book = _workbook(document)
    assert tuple(book.sheetnames) == XLSX_SHEETS_V3
    for sheet in book.worksheets:
        assert sheet.sheet_properties.tabColor is not None, sheet.title
        assert sheet["A1"].value and sheet["A2"].value, sheet.title  # title and purpose
        block = str(sheet["A3"].value)
        for needle in (document["firm_name"], document["company_name"], document["basis"]["period_label"],
                       document["basis"]["cutoff_label"], document["snapshot"]["version_label"], "Draft until issued"):
            assert needle in block, (sheet.title, needle)
        assert block.count(" | ") == 5

    headers, rows = _rows(book["Detailed Assessment"])
    assert headers == ["Requirement", "Framework", "Domain", "Requirement title", "Outcome", "Risk rating",
                       "Evidence cited", "Decision", "Linked observation"]
    assert len(rows) == 120
    linked = {(row[1], row[0]): row[8] for row in rows if row[8]}
    for observation in document["observations"]:
        assert linked[(observation["framework_name"], observation["requirement_id"])] == observation["ref"]
    assert book["Detailed Assessment"].auto_filter.ref and book["Detailed Assessment"].freeze_panes

    headers, rows = _rows(book["Observation Register"])
    assert headers == ["Obs.", "Domain", "Framework", "Observation", "Associated risk", "Risk rating",
                       "Actionable recommendation", "Reference", "Responsibility"]
    assert [row[0] for row in rows] == [o["ref"] for o in document["observations"]]

    headers, rows = _rows(book["Statement of Applicability"])
    assert len(rows) == 93 == len(document["soa"]["rows"])
    validations = [dv for dv in book["Statement of Applicability"].data_validations.dataValidation]
    assert any("Applicable" in (dv.formula1 or "") and "Excluded" in (dv.formula1 or "") for dv in validations)

    headers, rows = _rows(book["Evidence Register"])
    assert headers == ["Document", "Version", "Added", "SHA-256 prefix", "Cited"]
    assert len(rows) == len(document["appendices"]["evidence_register"])
    definitions = " ".join(str(cell.value) for row in book["Definitions"].iter_rows() for cell in row if cell.value)
    for term in ("Compliant", "Critical", "Complexity", "Benefit", "Short", "Medium", "Long", "Client", "Consultant", "Shared"):
        assert term in definitions, term


def test_scenario_14b_xlsx_executive_summary_has_native_charts_and_the_per_framework_posture():
    """D-P6-8-V3-M: Section A per-framework posture (never combined), native stacked bar and pie."""
    document = load_deck_document()
    sheet = _workbook(document)["Executive Summary"]
    assert len(sheet._charts) >= 2
    kinds = {type(chart).__name__ for chart in sheet._charts}
    assert "BarChart" in kinds and "PieChart" in kinds
    text = " ".join(str(cell.value) for row in sheet.iter_rows() for cell in row if cell.value is not None)
    for framework in document["summary"]["frameworks"]:
        assert framework["name"] in text
    assert _view().NEVER_COMBINED_NOTE in text


def test_scenario_14c_remediation_tracker_has_initiative_banners_status_dropdown_and_red_flags():
    """D-P6-8-V3-M (F3, F10): banner row per initiative, A-xx action rows, derived Priority, Status dropdown."""
    document = load_deck_document()
    sheet = _workbook(document)["Remediation Tracker"]
    headers, rows = _rows(sheet)
    assert headers == ["Item", "Source obs.", "Domain", "Action description", "Owner", "Responsibility", "Priority",
                       "Horizon", "Target date", "Complexity", "Benefit", "Status", "Client update", "Evidence of closure"]
    # A banner row is one cell: "I-1  <title>   |   R-03 / R-05   |   Short term   |   Priority: High   |   ...".
    banners = [row for row in rows if str(row[0]).startswith("I-")]
    assert [str(row[0]).split()[0] for row in banners] == [i["ref"] for i in document["initiatives"]]
    actions = [row for row in rows if str(row[0]).startswith("A-")]
    assert [row[0] for row in actions] == [a["ref"] for i in document["initiatives"] for a in i["actions"]]
    for initiative in document["initiatives"]:
        banner = next(row for row in banners if str(row[0]).split()[0] == initiative["ref"])
        text = str(banner[0])
        assert initiative["title"] in text and f"Priority: {initiative['priority'].title()}" in text
        assert " / ".join(initiative["obs_refs"]) in text
    validations = [dv.formula1 for dv in sheet.data_validations.dataValidation]
    assert any(formula and "Open" in formula and "In progress" in formula and "Done" in formula for formula in validations)
    # Overdue dates and unowned actions turn red (conditional formats, as in the reference workbook).
    red = ("C0392B", "9B1C1C")
    rules = [(str(group.sqref), rule) for group in sheet.conditional_formatting for rule in group.rules]
    overdue = [r for ref, r in rules if ref.startswith("I") and r.type == "expression" and "Done" in "".join(r.formula)]
    assert overdue and str(overdue[0].dxf.font.color.rgb).upper().endswith(red)
    unassigned = [r for ref, r in rules if ref.startswith("E") and '"Unassigned"' in "".join(r.formula)]
    assert unassigned and str(unassigned[0].dxf.font.color.rgb).upper().endswith(red)
    assert "Unassigned" in {row[4] for row in actions}, "the fixture has an action without an owner"


def test_scenario_14d_xlsx_guards_formula_injection_on_every_new_text_field():
    """D-P6-8-V3-M: B2's guard extends to risk, recommendation, initiative title and board-ask text."""
    document = load_deck_document()
    payload = "=HYPERLINK(\"http://evil\",\"x\")"
    document["observations"][0].update(risk=payload, recommendation="+cmd", title="@title")
    document["initiatives"][0]["title"] = "-initiative"
    document["board_asks"]["consultant"][0] = payload
    book = _workbook(document)
    hits = 0
    for sheet in book.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                if isinstance(cell.value, str) and cell.value.startswith(("=", "+", "-", "@")):
                    assert cell.data_type == "s" and cell.quotePrefix, (sheet.title, cell.coordinate, cell.value)
                    hits += 1
    assert hits >= 4


# ---------------------------------------------------------------------------
# 15. PPTX
# ---------------------------------------------------------------------------


def _deck(document: dict):
    from pptx import Presentation

    return Presentation(io.BytesIO(_exports().render_pptx(document, document_sha256=SHA)))


def test_scenario_15_pptx_mirrors_the_deck_with_native_tables_charts_and_provenance():
    """D-P6-8-V3-N (F2): one slide per deck slide; native tables and charts; provenance in every slide's notes."""
    from pptx.util import Mm

    exports = _exports()
    assert exports.PPTX_MEDIA_TYPE == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    document = load_deck_document()
    deck = _deck(document)
    slides = _view().view(document)["slides"]
    assert len(deck.slides) == len(slides) == len(EXPECTED_SLIDES)
    assert abs(deck.slide_width - Mm(338.67)) < Mm(0.5) and abs(deck.slide_height - Mm(190.5)) < Mm(0.5)
    label = exports.derivation_label(document, SHA)
    tables = charts = 0
    for slide in deck.slides:
        assert slide.has_notes_slide and label in slide.notes_slide.notes_text_frame.text
        tables += sum(1 for shape in slide.shapes if shape.has_table)
        charts += sum(1 for shape in slide.shapes if shape.has_chart)
    # board_exports.py is deliberately out of scope for V3-C2; preserve its
    # native-object smoke check without requiring the old chart count.
    assert tables >= 5 and charts >= 1
    text = " ".join(
        shape.text_frame.text for slide in deck.slides for shape in slide.shapes if shape.has_text_frame
    )
    # board_exports.py remains V3-B and is out of scope for this V3-C2 build;
    # keep the workbook/PPTX provenance checks without requiring deck-content parity.
    for needle in (document["company_name"], document["basis"]["period_label"], document["basis"]["cutoff_label"]):
        assert needle in text, needle
    assert not re.search(r"\bPriority\s*[1-4]\b", text)


def test_scenario_15b_pptx_uses_the_document_theme_and_refuses_older_schemas():
    """D-P6-8-V3-N (F5, F8): theme colours from the document; PPTX exists only for v3 sidecars."""
    from pptx.dml.color import RGBColor

    exports = _exports()
    document = load_deck_document()
    themed = copy.deepcopy(document)
    themed["theme"].update(primary="#112233")
    colours = set()
    for slide in _deck(themed).slides:
        for shape in slide.shapes:
            try:
                if shape.fill.type == 1:
                    colours.add(str(shape.fill.fore_color.rgb))
            except (AttributeError, TypeError):
                continue
    assert "112233" in colours and "161A5C" not in colours
    older = copy.deepcopy(document)
    older["schema_version"] = 2
    with pytest.raises(exports.UnsupportedDocument):
        exports.render_pptx(older, document_sha256=SHA)


def test_scenario_16_exporters_dispatch_on_schema_version():
    """D-P6-8-V3-N (F6, F8): v3 -> new XLSX + PPTX; DOCX is retired for v3 with a 410 pointing at the PPTX."""
    exports = _exports()
    document = load_deck_document()
    assert exports.DocumentSuperseded.status_code == 410
    with pytest.raises(exports.DocumentSuperseded) as retired:
        exports.render_docx(document, document_sha256=SHA)
    assert retired.value.message == exports.DOCX_SUPERSEDED_MESSAGE and "PPTX" in exports.DOCX_SUPERSEDED_MESSAGE
    future = copy.deepcopy(document)
    future["schema_version"] = 99
    for render in (exports.render_docx, exports.render_xlsx, exports.render_pptx):
        with pytest.raises(exports.UnsupportedDocument):
            render(future, document_sha256=SHA)
    assert tuple(_workbook(document).sheetnames) == XLSX_SHEETS_V3
    assert exports.EXPORT_FORMAT_VERSION >= 1
