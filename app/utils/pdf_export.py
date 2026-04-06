"""
Board-level DPDPA compliance gap assessment PDF report.

Design philosophy: First 5 pages are for the board (visual, no walls of text).
Detailed findings go in the appendix for the compliance team.
"""

import json
import math
from datetime import datetime, timezone

from fpdf import FPDF

from app.models.report import GapItem, GapReport
from app.services.scoring import get_rating

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Brand palette
NAVY = (30, 30, 80)
DARK_TEXT = (40, 40, 40)
MID_TEXT = (80, 80, 80)
LIGHT_TEXT = (140, 140, 140)
CARD_BG = (248, 248, 252)
DIVIDER = (220, 220, 220)
WHITE = (255, 255, 255)

# Status colors
STATUS_COLORS = {
    "compliant": (39, 174, 96),
    "partially_compliant": (241, 196, 15),
    "non_compliant": (231, 76, 60),
    "not_assessed": (189, 195, 199),
}

# Risk colors
RISK_COLORS = {
    "critical": (231, 76, 60),
    "high": (230, 126, 34),
    "medium": (241, 196, 15),
    "low": (39, 174, 96),
}

# Rating colors
RATING_COLORS = {
    "Non-Compliant": (231, 76, 60),
    "Needs Significant Improvement": (230, 126, 34),
    "Partially Compliant": (241, 196, 15),
    "Compliant": (39, 174, 96),
}

# Priority config
PRIORITY_CONFIG = {
    1: ("Immediate", "0-4 weeks", (231, 76, 60)),
    2: ("Short-Term", "1-3 months", (230, 126, 34)),
    3: ("Medium-Term", "3-6 months", (241, 196, 15)),
    4: ("Ongoing", "6-12 months", (39, 174, 96)),
}

# Unicode -> ASCII for latin-1 safety
_UNICODE_MAP = str.maketrans({
    "\u2014": "-", "\u2013": "-", "\u2018": "'", "\u2019": "'",
    "\u201c": '"', "\u201d": '"', "\u2026": "...", "\u2022": "*",
    "\u00a0": " ",
})

# Page dimensions (A4)
PW = 210  # page width
PM = 15   # page margin
CW = PW - 2 * PM  # content width


def S(text: str) -> str:
    """Make text safe for fpdf2 built-in fonts (latin-1)."""
    if not text:
        return ""
    return text.translate(_UNICODE_MAP).encode("latin-1", errors="replace").decode("latin-1")


def _rating_color(rating: str) -> tuple[int, int, int]:
    for key, color in RATING_COLORS.items():
        if key in rating:
            return color
    return NAVY


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

def _draw_score_ring(pdf: FPDF, cx: float, cy: float, radius: float,
                     score: float, rating: str):
    """Draw a circular score gauge — colored arc on gray track."""
    ring_width = radius * 0.22

    # Gray track (full circle via thick arc segments)
    pdf.set_draw_color(230, 230, 230)
    pdf.set_line_width(ring_width)
    pdf.arc(cx, cy, a=radius, start_angle=0, end_angle=360, style="D")

    # Colored arc for score
    if score > 0:
        r, g, b = _rating_color(rating)
        pdf.set_draw_color(r, g, b)
        arc_angle = score * 3.6  # 0-360
        # Draw from top (270) clockwise
        pdf.arc(cx, cy, a=radius, start_angle=270,
                end_angle=270 + arc_angle, style="D")

    # Reset line width
    pdf.set_line_width(0.2)

    # Score text in center
    pdf.set_font("Helvetica", "B", int(radius * 0.9))
    pdf.set_text_color(*NAVY)
    score_text = f"{score:.0f}%"
    tw = pdf.get_string_width(score_text)
    pdf.text(cx - tw / 2, cy + radius * 0.25, score_text)

    # Rating label below
    pdf.set_font("Helvetica", "B", int(radius * 0.28))
    r, g, b = _rating_color(rating)
    pdf.set_text_color(r, g, b)
    tw = pdf.get_string_width(rating)
    pdf.text(cx - tw / 2, cy + radius * 0.65, S(rating))


def _draw_kpi_card(pdf: FPDF, x: float, y: float, w: float, h: float,
                   value: str, label: str, accent: tuple[int, int, int]):
    """Draw a KPI metric card with colored top strip."""
    # Card background
    pdf.set_fill_color(*CARD_BG)
    pdf.rect(x, y, w, h, style="F", round_corners=True, corner_radius=2)
    # Accent strip at top
    pdf.set_fill_color(*accent)
    pdf.rect(x, y, w, 2.5, style="F")

    # Value
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*accent)
    tw = pdf.get_string_width(value)
    pdf.text(x + (w - tw) / 2, y + 16, value)

    # Label
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*MID_TEXT)
    tw = pdf.get_string_width(label)
    pdf.text(x + (w - tw) / 2, y + 22, S(label))


def _draw_h_bar(pdf: FPDF, x: float, y: float, w: float, h: float,
                score: float, label: str, rating: str):
    """Draw a labeled horizontal bar chart row."""
    bar_x = x + 75  # label area
    bar_w = w - 75 - 30  # leave room for percentage

    # Label
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*DARK_TEXT)
    pdf.text(x, y + h * 0.65, S(label[:38]))

    # Background track
    pdf.set_fill_color(235, 235, 240)
    pdf.rect(bar_x, y + 1, bar_w, h - 2, style="F", round_corners=True, corner_radius=2)

    # Filled portion
    if score > 0:
        r, g, b = _rating_color(rating)
        pdf.set_fill_color(r, g, b)
        filled_w = max(bar_w * score / 100, 3)
        pdf.rect(bar_x, y + 1, filled_w, h - 2, style="F", round_corners=True, corner_radius=2)

    # Score text
    pdf.set_font("Helvetica", "B", 9)
    r, g, b = _rating_color(rating)
    pdf.set_text_color(r, g, b)
    score_text = f"{score:.0f}%"
    pdf.text(bar_x + bar_w + 3, y + h * 0.65, score_text)


def _draw_status_bar(pdf: FPDF, x: float, y: float, w: float, h: float,
                     counts: dict, total: int):
    """Draw a stacked horizontal bar showing compliance distribution."""
    if total == 0:
        return
    cur_x = x
    order = ["compliant", "partially_compliant", "non_compliant", "not_assessed"]
    labels = {
        "compliant": "Compliant",
        "partially_compliant": "Partial",
        "non_compliant": "Non-Compliant",
        "not_assessed": "N/A",
    }
    for status in order:
        count = counts.get(status, 0)
        if count == 0:
            continue
        seg_w = (count / total) * w
        r, g, b = STATUS_COLORS[status]
        pdf.set_fill_color(r, g, b)
        pdf.rect(cur_x, y, seg_w, h, style="F")
        # Count label inside if wide enough
        if seg_w > 12:
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(*WHITE)
            tw = pdf.get_string_width(str(count))
            pdf.text(cur_x + (seg_w - tw) / 2, y + h * 0.68, str(count))
        cur_x += seg_w

    # Legend below
    legend_y = y + h + 3
    leg_x = x
    for status in order:
        count = counts.get(status, 0)
        r, g, b = STATUS_COLORS[status]
        pdf.set_fill_color(r, g, b)
        pdf.rect(leg_x, legend_y, 3, 3, style="F")
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*MID_TEXT)
        pdf.text(leg_x + 4, legend_y + 2.5, f"{labels[status]} ({count})")
        leg_x += 38


def _draw_timeline_block(pdf: FPDF, x: float, y: float, w: float,
                         priority: int, items: list[GapItem]):
    """Draw a single priority block in the remediation timeline."""
    config = PRIORITY_CONFIG.get(priority, ("Other", "", NAVY))
    label, timeframe, color = config
    r, g, b = color

    # Block header
    pdf.set_fill_color(r, g, b)
    pdf.rect(x, y, w, 8, style="F")
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*WHITE)
    pdf.text(x + 3, y + 5.5, S(f"{label}  |  {timeframe}  |  {len(items)} items"))

    # Items
    item_y = y + 10
    pdf.set_font("Helvetica", "", 8)
    for item in items[:8]:  # cap at 8 per block to avoid overflow
        if item_y > 270:
            break
        pdf.set_fill_color(r, g, b)
        pdf.rect(x, item_y, 2, 4, style="F")  # accent dot
        pdf.set_text_color(*DARK_TEXT)
        text = f"{item.requirement_id}: {item.requirement_title[:55]}"
        pdf.text(x + 4, item_y + 3, S(text))

        # Effort + timeline tag
        tag_text = f"{item.remediation_effort} | ~{item.timeline_weeks}w"
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*LIGHT_TEXT)
        pdf.text(x + w - pdf.get_string_width(tag_text) - 2, item_y + 3, tag_text)
        pdf.set_font("Helvetica", "", 8)
        item_y += 6

    if len(items) > 8:
        pdf.set_text_color(*LIGHT_TEXT)
        pdf.set_font("Helvetica", "I", 7)
        pdf.text(x + 4, item_y + 3, f"+{len(items) - 8} more items (see appendix)")

    return item_y + 4


def _draw_gap_card(pdf: FPDF, item: GapItem, x: float, y: float, w: float,
                   show_evidence: bool = False) -> float:
    """Draw a compact card for a gap item. Returns height consumed."""
    r, g, b = RISK_COLORS.get(item.risk_level, NAVY)

    # Estimate height needed
    gap_text = S(item.gap_description or "")
    fix_text = S(item.remediation_action or "")

    # Left color bar
    card_h = 28  # will adjust below
    pdf.set_fill_color(r, g, b)
    pdf.rect(x, y, 2.5, card_h, style="F")

    # Card background
    pdf.set_fill_color(*CARD_BG)
    pdf.rect(x + 2.5, y, w - 2.5, card_h, style="F")

    # Title line
    inner_x = x + 5
    inner_w = w - 8
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*DARK_TEXT)
    title = f"{item.requirement_id}: {item.requirement_title[:60]}"
    pdf.text(inner_x, y + 5, S(title))

    # Status + risk badges
    status_label = item.compliance_status.replace("_", " ").title()
    sr, sg, sb = STATUS_COLORS.get(item.compliance_status, NAVY)
    badge_x = inner_x + inner_w - 50
    pdf.set_fill_color(sr, sg, sb)
    pdf.rect(badge_x, y + 1.5, 22, 4.5, style="F", round_corners=True, corner_radius=1)
    pdf.set_font("Helvetica", "B", 6)
    pdf.set_text_color(*WHITE)
    bw = pdf.get_string_width(status_label)
    pdf.text(badge_x + (22 - bw) / 2, y + 4.8, status_label)

    pdf.set_fill_color(r, g, b)
    pdf.rect(badge_x + 24, y + 1.5, 18, 4.5, style="F", round_corners=True, corner_radius=1)
    risk_label = item.risk_level.upper()
    bw = pdf.get_string_width(risk_label)
    pdf.text(badge_x + 24 + (18 - bw) / 2, y + 4.8, risk_label)

    # Maturity badge (if available)
    maturity_level = getattr(item, "maturity_level", None)
    if maturity_level is not None:
        maturity_colors = {
            0: (231, 76, 60), 1: (231, 76, 60),   # red
            2: (230, 126, 34),                      # orange
            3: (241, 196, 15),                      # yellow
            4: (39, 174, 96), 5: (39, 174, 96),    # green
        }
        mr, mg, mb = maturity_colors.get(maturity_level, NAVY)
        pdf.set_fill_color(mr, mg, mb)
        pdf.rect(badge_x + 44, y + 1.5, 18, 4.5, style="F", round_corners=True, corner_radius=1)
        maturity_label = f"M{maturity_level}"
        bw = pdf.get_string_width(maturity_label)
        pdf.text(badge_x + 44 + (18 - bw) / 2, y + 4.8, maturity_label)

    # Gap description (truncated)
    cur_y = y + 9
    if gap_text:
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(*MID_TEXT)
        pdf.set_xy(inner_x, cur_y)
        pdf.multi_cell(inner_w, 3.5, text=gap_text[:200], new_x="LMARGIN")
        cur_y = pdf.get_y()

    # Remediation (truncated)
    if fix_text:
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.set_text_color(39, 174, 96)
        pdf.text(inner_x, cur_y + 3.5, "FIX:")
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(*MID_TEXT)
        pdf.set_xy(inner_x + 8, cur_y + 0.5)
        pdf.multi_cell(inner_w - 8, 3.5, text=fix_text[:180], new_x="LMARGIN")
        cur_y = pdf.get_y()

    # Evidence quote (appendix only)
    if show_evidence:
        evidence = S(item.evidence_quote or "No relevant language found")
        is_verbatim = item.evidence_quote and item.evidence_quote != "No relevant language found"
        label = "EVIDENCE:" if is_verbatim else "EVIDENCE:"
        label_color = (52, 152, 219) if is_verbatim else LIGHT_TEXT
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(*label_color)
        pdf.text(inner_x, cur_y + 3.5, label)
        pdf.set_font("Helvetica", "I" if is_verbatim else "", 7)
        pdf.set_text_color(*MID_TEXT if is_verbatim else LIGHT_TEXT)
        pdf.set_xy(inner_x + 18, cur_y + 0.5)
        pdf.multi_cell(inner_w - 18, 3.5, text=evidence[:240], new_x="LMARGIN")
        cur_y = pdf.get_y()

    # Adjust card height to actual content
    actual_h = max(cur_y - y + 2, 14)
    # Redraw the left bar at correct height
    pdf.set_fill_color(r, g, b)
    pdf.rect(x, y, 2.5, actual_h, style="F")

    return actual_h


def _draw_heatmap_row(pdf: FPDF, x: float, y: float, label: str,
                      score: float, rating: str, items: list[GapItem]):
    """Draw a chapter heatmap row — label, mini squares, score."""
    # Label
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*DARK_TEXT)
    pdf.text(x, y + 4, S(label[:30]))

    # Mini squares
    sq_x = x + 62
    sq_size = 4.5
    gap = 1
    for item in items:
        r, g, b = STATUS_COLORS.get(item.compliance_status, (189, 195, 199))
        pdf.set_fill_color(r, g, b)
        pdf.rect(sq_x, y, sq_size, sq_size, style="F")
        sq_x += sq_size + gap

    # Score
    pdf.set_font("Helvetica", "B", 9)
    r, g, b = _rating_color(rating)
    pdf.set_text_color(r, g, b)
    pdf.text(x + CW - 22, y + 4, f"{score:.0f}%")

    # Rating text
    pdf.set_font("Helvetica", "", 7)
    pdf.text(x + CW - 22, y + 8, S(rating[:25]))


# ---------------------------------------------------------------------------
# Page sections
# ---------------------------------------------------------------------------

def _page_footer(pdf: FPDF, company_name: str):
    """Draw footer on current page."""
    pdf.set_y(-15)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(*LIGHT_TEXT)
    pdf.cell(0, 5, text=S(f"CONFIDENTIAL  |  {company_name}  |  DPDPA Gap Assessment"), align="L")
    pdf.cell(0, 5, text=f"Page {pdf.page_no()}/{{nb}}", align="R")


def _page_header(pdf: FPDF, section_title: str):
    """Draw header bar on non-cover pages."""
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, PW, 12, style="F")
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_text_color(*WHITE)
    pdf.text(PM, 8, S(section_title))
    pdf.set_y(16)


def _section_title(pdf: FPDF, title: str):
    """Draw a section heading."""
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 8, text=S(title))
    pdf.ln(10)


# ---------------------------------------------------------------------------
# Main PDF generation
# ---------------------------------------------------------------------------

def generate_pdf(
    report: GapReport,
    gap_items: list[GapItem],
    company_name: str,
    initiatives: list | None = None,
) -> bytes:
    """Generate a board-level PDF report."""
    chapter_scores = json.loads(report.chapter_scores)
    overall_rating = get_rating(report.overall_score)

    # Compute summary stats
    counts = {"compliant": 0, "partially_compliant": 0, "non_compliant": 0, "not_assessed": 0}
    critical_count = 0
    high_count = 0
    for item in gap_items:
        counts[item.compliance_status] = counts.get(item.compliance_status, 0) + 1
        if item.compliance_status in ("non_compliant", "partially_compliant"):
            if item.risk_level == "critical":
                critical_count += 1
            elif item.risk_level == "high":
                high_count += 1
    total = sum(counts.values())

    # Group items
    chapters_grouped: dict[str, list[GapItem]] = {}
    for item in gap_items:
        chapters_grouped.setdefault(item.chapter, []).append(item)

    priority_grouped: dict[int, list[GapItem]] = {}
    for item in gap_items:
        if item.compliance_status not in ("compliant", "not_assessed"):
            priority_grouped.setdefault(item.remediation_priority, []).append(item)

    # Max remediation timeline
    max_weeks = max((i.timeline_weeks for i in gap_items if i.timeline_weeks), default=0)

    pdf = FPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=False)

    # ===================================================================
    # PAGE 1: COVER
    # ===================================================================
    pdf.add_page()

    # Navy header band
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, PW, 55, style="F")

    # Title
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(*WHITE)
    pdf.text(PM, 22, "DPDPA Compliance")
    pdf.set_font("Helvetica", "", 24)
    pdf.text(PM, 34, "Gap Assessment Report")

    # Date
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(180, 180, 210)
    date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
    pdf.text(PM, 48, date_str)

    # Company name
    pdf.set_font("Helvetica", "", 18)
    pdf.set_text_color(*DARK_TEXT)
    pdf.text(PM, 75, S(company_name))

    # Divider line
    pdf.set_draw_color(*DIVIDER)
    pdf.line(PM, 80, PW - PM, 80)

    # Score ring (centered)
    cx = PW / 2
    cy = 130
    _draw_score_ring(pdf, cx, cy, 30, report.overall_score, overall_rating)

    # Summary stats below ring
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*MID_TEXT)
    summary_text = f"{total} requirements assessed  |  {critical_count + high_count} gaps identified  |  ~{max_weeks} weeks to full remediation"
    tw = pdf.get_string_width(summary_text)
    pdf.text((PW - tw) / 2, 175, S(summary_text))

    # Bottom section: chapter score preview bars
    bar_y = 195
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*NAVY)
    pdf.text(PM, bar_y - 5, "Assessment Areas")

    for chapter_key, scores in chapter_scores.items():
        _draw_h_bar(pdf, PM, bar_y, CW, 8, scores["score"], scores["title"], scores["rating"])
        bar_y += 11

    _page_footer(pdf, company_name)

    # ===================================================================
    # PAGE 2: EXECUTIVE DASHBOARD
    # ===================================================================
    pdf.add_page()
    _page_header(pdf, "Executive Dashboard")

    # KPI cards row
    card_w = (CW - 9) / 4  # 4 cards with 3px gaps
    card_y = pdf.get_y() + 2
    _draw_kpi_card(pdf, PM, card_y, card_w, 27,
                   f"{report.overall_score:.0f}%", "Overall Score", _rating_color(overall_rating))
    _draw_kpi_card(pdf, PM + card_w + 3, card_y, card_w, 27,
                   str(critical_count), "Critical Gaps", RISK_COLORS["critical"])
    _draw_kpi_card(pdf, PM + 2 * (card_w + 3), card_y, card_w, 27,
                   str(high_count), "High Risk Gaps", RISK_COLORS["high"])
    _draw_kpi_card(pdf, PM + 3 * (card_w + 3), card_y, card_w, 27,
                   f"~{max_weeks}w", "Remediation Timeline", NAVY)

    # Compliance distribution bar
    pdf.set_y(card_y + 35)
    _section_title(pdf, "Compliance Distribution")
    _draw_status_bar(pdf, PM, pdf.get_y(), CW, 10, counts, total)

    # Chapter scores with heatmap
    pdf.set_y(pdf.get_y() + 22)
    _section_title(pdf, "Assessment Areas")

    hm_y = pdf.get_y()
    for chapter_key, scores in chapter_scores.items():
        items = chapters_grouped.get(chapter_key, [])
        _draw_heatmap_row(pdf, PM, hm_y, scores["title"], scores["score"], scores["rating"], items)
        hm_y += 14

    # Executive summary (condensed)
    pdf.set_y(hm_y + 8)
    _section_title(pdf, "Key Findings")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*DARK_TEXT)
    # Take first 600 chars of executive summary
    summary = S(report.executive_summary[:600])
    if len(report.executive_summary) > 600:
        summary += "..."
    pdf.set_x(PM)
    pdf.multi_cell(CW, 4.5, text=summary, new_x="LMARGIN")

    _page_footer(pdf, company_name)

    # ===================================================================
    # PAGE 3: CRITICAL & HIGH RISK GAPS
    # ===================================================================
    pdf.add_page()
    _page_header(pdf, "Critical & High Risk Gaps")
    _section_title(pdf, "Requires Immediate Attention")

    critical_high = [
        i for i in gap_items
        if i.risk_level in ("critical", "high")
        and i.compliance_status != "compliant"
    ]
    critical_high.sort(key=lambda x: (
        0 if x.risk_level == "critical" else 1,
        x.remediation_priority,
    ))

    card_y = pdf.get_y()
    for item in critical_high:
        if card_y > 255:
            _page_footer(pdf, company_name)
            pdf.add_page()
            _page_header(pdf, "Critical & High Risk Gaps (continued)")
            card_y = pdf.get_y()

        h = _draw_gap_card(pdf, item, PM, card_y, CW)
        card_y += h + 3

    _page_footer(pdf, company_name)

    # ===================================================================
    # PAGE 4-5: REMEDIATION ROADMAP
    # ===================================================================
    pdf.add_page()
    _page_header(pdf, "Remediation Roadmap")
    _section_title(pdf, "Implementation Timeline")

    # Visual timeline — 4 priority blocks across the page
    # First draw a horizontal timeline axis
    axis_y = pdf.get_y() + 2
    axis_x = PM
    axis_w = CW

    # Timeline segments
    seg_count = len(priority_grouped)
    if seg_count > 0:
        seg_w = axis_w / 4
        for pri in range(1, 5):
            config = PRIORITY_CONFIG.get(pri, ("", "", NAVY))
            _, timeframe, color = config
            sx = axis_x + (pri - 1) * seg_w
            r, g, b = color
            pdf.set_fill_color(r, g, b)
            pdf.rect(sx, axis_y, seg_w - 1, 5, style="F")
            pdf.set_font("Helvetica", "B", 7)
            pdf.set_text_color(*WHITE)
            pdf.text(sx + 2, axis_y + 3.8, S(timeframe))

        # Arrow at end
        end_x = axis_x + axis_w - 1
        pdf.set_fill_color(*NAVY)

    # Priority blocks below
    block_y = axis_y + 12
    for pri in sorted(priority_grouped.keys()):
        items = priority_grouped[pri]
        items.sort(key=lambda x: (
            -{"critical": 4, "high": 3, "medium": 2, "low": 1}.get(x.risk_level, 0),
        ))
        if block_y > 240:
            _page_footer(pdf, company_name)
            pdf.add_page()
            _page_header(pdf, "Remediation Roadmap (continued)")
            block_y = pdf.get_y()
        block_y = _draw_timeline_block(pdf, PM, block_y, CW, pri, items)
        block_y += 5

    _page_footer(pdf, company_name)

    # ===================================================================
    # STRATEGIC INITIATIVES (if any)
    # ===================================================================
    if initiatives:
        # Root cause cluster color map
        cluster_colors = {
            "policy": (52, 152, 219),      # blue
            "people": (155, 89, 182),      # purple
            "process": (230, 126, 34),     # orange
            "technology": (39, 174, 96),   # green
            "governance": (30, 30, 80),    # navy
        }

        pdf.add_page()
        _page_header(pdf, "Strategic Initiatives")
        _section_title(pdf, "Remediation Initiative Plan")

        # Subtitle
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*MID_TEXT)
        pdf.set_x(PM)
        pdf.multi_cell(
            CW, 4,
            text=S(
                f"Gaps clustered by root cause into {len(initiatives)} initiatives. "
                "Initiatives ordered by priority. Address prerequisite initiatives first."
            ),
            new_x="LMARGIN",
        )
        pdf.ln(4)

        init_y = pdf.get_y()
        for init in initiatives:
            if init_y > 250:
                _page_footer(pdf, company_name)
                pdf.add_page()
                _page_header(pdf, "Strategic Initiatives (continued)")
                init_y = pdf.get_y()

            cluster = getattr(init, "root_cause_category", "process")
            cr, cg, cb = cluster_colors.get(cluster, NAVY)
            title = getattr(init, "title", "")
            approach = getattr(init, "suggested_approach", "")
            req_ids = getattr(init, "requirements_addressed", "[]")
            if isinstance(req_ids, str):
                try:
                    req_ids = json.loads(req_ids)
                except Exception:
                    req_ids = []
            effort = getattr(init, "combined_effort", "")
            timeline = getattr(init, "combined_timeline_weeks", 0)
            priority = getattr(init, "priority", 3)
            budget = getattr(init, "budget_estimate_band", "") or ""
            init_id = getattr(init, "initiative_id", "")

            # Card left color bar
            pdf.set_fill_color(cr, cg, cb)
            pdf.rect(PM, init_y, 3, 24, style="F")

            # Card background
            pdf.set_fill_color(*CARD_BG)
            pdf.rect(PM + 3, init_y, CW - 3, 24, style="F")

            inner_x = PM + 6
            inner_w = CW - 9

            # Initiative ID + title
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*DARK_TEXT)
            pdf.text(inner_x, init_y + 5, S(f"{init_id}: {title[:65]}"))

            # Cluster + effort + timeline badges
            badge_x = inner_x + inner_w - 80
            cluster_label = cluster.upper()
            pdf.set_fill_color(cr, cg, cb)
            pdf.rect(badge_x, init_y + 1, 22, 4.5, style="F", round_corners=True, corner_radius=1)
            pdf.set_font("Helvetica", "B", 6)
            pdf.set_text_color(*WHITE)
            bw = pdf.get_string_width(cluster_label)
            pdf.text(badge_x + (22 - bw) / 2, init_y + 4.2, cluster_label)

            priority_label = f"P{priority}"
            pri_color = PRIORITY_CONFIG.get(priority, (1, "", NAVY))[2]
            pdf.set_fill_color(*pri_color)
            pdf.rect(badge_x + 24, init_y + 1, 12, 4.5, style="F", round_corners=True, corner_radius=1)
            bw = pdf.get_string_width(priority_label)
            pdf.text(badge_x + 24 + (12 - bw) / 2, init_y + 4.2, priority_label)

            meta_str = f"{effort} effort  |  ~{timeline}w  |  {budget.replace('_', ' ')}"
            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(*LIGHT_TEXT)
            pdf.text(inner_x, init_y + 10, S(meta_str))

            # Approach text
            pdf.set_font("Helvetica", "", 7.5)
            pdf.set_text_color(*MID_TEXT)
            pdf.set_xy(inner_x, init_y + 13)
            pdf.multi_cell(inner_w, 3.5, text=S(approach[:160]), new_x="LMARGIN")
            content_bottom = max(pdf.get_y(), init_y + 22)

            # Requirement count tag
            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(*LIGHT_TEXT)
            pdf.text(inner_x, content_bottom + 2, S(f"{len(req_ids)} requirements addressed"))

            card_h = content_bottom - init_y + 5
            # Redraw left bar at correct height
            pdf.set_fill_color(cr, cg, cb)
            pdf.rect(PM, init_y, 3, card_h, style="F")

            init_y = content_bottom + 7

        _page_footer(pdf, company_name)

    # ===================================================================
    # DIVIDER PAGE: APPENDIX
    # ===================================================================
    pdf.add_page()
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, PW, 297, style="F")

    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(*WHITE)
    pdf.text(PM, 130, "Appendix")
    pdf.set_font("Helvetica", "", 16)
    pdf.set_text_color(180, 180, 210)
    pdf.text(PM, 145, "Detailed Gap Findings")
    pdf.set_font("Helvetica", "", 11)
    pdf.text(PM, 160, S(f"{total} requirements  |  {len(gap_items) - counts.get('compliant', 0)} gaps identified"))

    # ===================================================================
    # APPENDIX: DETAILED FINDINGS BY CHAPTER
    # ===================================================================
    for chapter_key, items in chapters_grouped.items():
        chapter_title = chapter_scores.get(chapter_key, {}).get("title", chapter_key)
        chapter_score = chapter_scores.get(chapter_key, {}).get("score", 0)
        chapter_rating = chapter_scores.get(chapter_key, {}).get("rating", "")

        pdf.add_page()
        _page_header(pdf, f"Appendix: {S(chapter_title)}")

        # Chapter header with score
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(*NAVY)
        pdf.text(PM, pdf.get_y() + 5, S(chapter_title))

        r, g, b = _rating_color(chapter_rating)
        score_text = f"{chapter_score:.0f}% - {chapter_rating}"
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(r, g, b)
        pdf.text(PW - PM - pdf.get_string_width(S(score_text)), pdf.get_y() + 5, S(score_text))

        pdf.set_y(pdf.get_y() + 10)
        pdf.set_draw_color(*DIVIDER)
        pdf.line(PM, pdf.get_y(), PW - PM, pdf.get_y())
        pdf.set_y(pdf.get_y() + 5)

        for item in items:
            cur_y = pdf.get_y()
            if cur_y > 245:
                _page_footer(pdf, company_name)
                pdf.add_page()
                _page_header(pdf, f"Appendix: {S(chapter_title)}")
                cur_y = pdf.get_y()

            if item.compliance_status == "compliant":
                # Compact single-line for compliant items
                pdf.set_fill_color(*STATUS_COLORS["compliant"])
                pdf.rect(PM, cur_y, 2, 5, style="F")
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(39, 174, 96)
                pdf.text(PM + 4, cur_y + 3.8, S(f"COMPLIANT  {item.requirement_id}: {item.requirement_title[:70]}"))
                pdf.set_y(cur_y + 7)
            elif item.compliance_status == "not_assessed":
                pdf.set_fill_color(*STATUS_COLORS["not_assessed"])
                pdf.rect(PM, cur_y, 2, 5, style="F")
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(*LIGHT_TEXT)
                pdf.text(PM + 4, cur_y + 3.8, S(f"N/A  {item.requirement_id}: {item.requirement_title[:70]}"))
                pdf.set_y(cur_y + 7)
            else:
                # Full card for gaps (with evidence in appendix)
                h = _draw_gap_card(pdf, item, PM, cur_y, CW, show_evidence=True)
                pdf.set_y(cur_y + h + 4)

        _page_footer(pdf, company_name)

    # ===================================================================
    # APPENDIX: SCOPE & LIMITATIONS
    # ===================================================================
    pdf.add_page()
    _page_header(pdf, "Scope & Limitations")
    _section_title(pdf, "Scope & Limitations")

    assessment_date = datetime.now(timezone.utc).strftime("%B %d, %Y")
    scope_text = f"""Assessment Date: {assessment_date}

Nature of Assessment:
This document constitutes a questionnaire-based DPDPA gap assessment. It is not a formal compliance audit and does not constitute legal advice. Findings are based solely on information disclosed by the organization's representatives during the structured assessment interview and from documents voluntarily submitted for review.

Scope of Coverage:
The assessment evaluates the organization's compliance posture against 41 requirements derived from the Digital Personal Data Protection Act, 2023 (DPDPA). These requirements span six domains: (1) Obligations of Data Fiduciary, (2) Rights of Data Principal, (3) Special Provisions for Children and Significant Data Fiduciaries, (4) Consent Management, (5) Cross-Border Data Transfer, and (6) Breach Notification.

What Is Not Covered:
This assessment does not include technical penetration testing, source code review, network security assessment, physical security review, or any form of independent technical verification. Findings in areas where the organization provided limited or no evidence are based on stated intent and disclosed posture only.

Reliance on Disclosed Information:
All findings reflect the information provided to the assessor at the time of the assessment. The assessor has not independently verified the accuracy or completeness of information provided. Material omissions or inaccuracies in disclosed information would affect the reliability of findings.

Recommended Follow-On Actions:
For requirements rated as Non-Compliant or Partially Compliant at a Critical or High risk level, independent verification by a qualified legal counsel or certified privacy professional is strongly recommended before relying on those findings for regulatory submissions, board reporting, or contractual representations.

Confidentiality:
This report is prepared solely for the use of the named organization. It should not be shared with third parties without the organization's explicit consent. CyberAssess and the named organization are the intended recipients of this report."""

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*DARK_TEXT)
    pdf.set_x(PM)
    pdf.multi_cell(CW, 4.5, text=S(scope_text), new_x="LMARGIN")
    _page_footer(pdf, company_name)

    # ===================================================================
    # FINAL PAGE: METHODOLOGY
    # ===================================================================
    pdf.add_page()
    _page_header(pdf, "Methodology")
    _section_title(pdf, "Assessment Methodology")

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*DARK_TEXT)

    methodology = """This assessment evaluates compliance against India's Digital Personal Data Protection Act, 2023 (DPDPA) across 41 requirements organized in 6 chapters. The assessment combines questionnaire responses from organizational stakeholders with analysis of uploaded policy documents.

Framework Overview:
The 41 requirements are derived directly from DPDPA statutory text and cover all obligations applicable to a Data Fiduciary operating in India. Requirements are organized into chapters aligned with the Act's chapter structure, with each chapter weighted to reflect regulatory emphasis and penalty exposure.

GRC Response Scale:
Questionnaire responses use a five-option scale:
- Fully Implemented: Control exists, is documented, consistently applied, and evidence is available (maps to Compliant - 100 points)
- Partially Implemented: Control exists in some form but is inconsistent, undocumented, or not fully operational (maps to Partially Compliant - 50 points)
- Planned: Control is not yet in place but there is a documented plan or budget commitment (maps to Non-Compliant - 0 points; recognized in remediation priority)
- Not Implemented: No control exists and none is planned (maps to Non-Compliant - 0 points)
- Not Applicable: Requirement does not apply to this organization's processing activities (excluded from scoring denominator)

Scoring Formula:
Each requirement is scored based on its GRC response. Section scores are the unweighted average of constituent requirement scores. Chapter scores are weighted averages of section scores using published section weights. The overall score is the weighted average of chapter scores using the chapter weights below. Not Applicable responses are excluded from the denominator, so scores reflect the applicable compliance universe only.

Chapter Weights:
- Obligations of Data Fiduciary (Ch. 2): 30%
- Rights of Data Principal (Ch. 3): 20%
- Special Provisions - Children & SDF (Ch. 4): 20%
- Consent Management (detailed): 10%
- Cross-Border Data Transfer: 10%
- Breach Notification: 10%

Rating Thresholds:
- 80-100%: Compliant
- 60-79%: Partially Compliant
- 40-59%: Needs Significant Improvement
- 0-39%: Non-Compliant

Risk Classification:
Gaps are classified by risk level (Critical, High, Medium, Low) based on regulatory exposure, potential penalties under Schedule to the DPDPA, and impact on data principals. Remediation priorities (P1-P4) are assigned based on risk severity and implementation dependencies between requirements.

Maturity Model (CMMI-Aligned):
Each gap is assigned a current maturity rating on a 0-5 scale:
M0 - Non-existent: No awareness or capability; requirement is entirely unaddressed
M1 - Initial: Ad-hoc or reactive; no repeatable process; relies on individual knowledge
M2 - Managed: Some process exists but applied inconsistently; not documented or auditable
M3 - Defined: Consistent, documented, and auditable process; meets minimum regulatory bar
M4 - Quantitative: Process is measured with KPIs; performance tracked and reported
M5 - Optimizing: Continuous improvement cycle in place; best-in-class privacy practice
The minimum remediation target for regulatory compliance is M3 (Defined). The gap between current maturity and M3 drives the remediation effort estimate.

Strategic Initiatives:
Gaps are clustered by root cause (Policy, People, Process, Technology, Governance) into named remediation initiatives. Each initiative groups related requirements that share a common fix pattern, enabling efficient resource and budget allocation. Initiatives are sequenced considering prerequisite dependencies between requirements.

Disclaimer:
This assessment provides guidance based on the information provided and should not be considered legal advice. Organizations should consult qualified legal counsel for definitive compliance determinations."""

    pdf.set_x(PM)
    pdf.multi_cell(CW, 4.5, text=S(methodology), new_x="LMARGIN")

    _page_footer(pdf, company_name)

    return bytes(pdf.output())
