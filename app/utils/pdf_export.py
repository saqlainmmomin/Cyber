"""
Board-level compliance gap assessment PDF report.

Design philosophy: First 5 pages are for the board (visual, no walls of text).
Detailed findings go in the appendix for the compliance team.
"""

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from fpdf import FPDF

from app.config import settings
from app.frameworks.registry import FrameworkRegistry
from app.services.scoring import is_failed_framework_score, report_framework_scores

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
REPO_ROOT = Path(__file__).resolve().parents[2]

# Status colors
STATUS_COLORS = {
    "compliant": (39, 174, 96),
    "partially_compliant": (241, 196, 15),
    "non_compliant": (231, 76, 60),
    "not_assessed": (189, 195, 199),
    "insufficient_evidence": (155, 89, 182),
}

# Risk colors
RISK_COLORS = {
    "critical": (231, 76, 60),
    "high": (230, 126, 34),
    "medium": (241, 196, 15),
    "low": (39, 174, 96),
}

# Answer source display config: (label, color)
ANSWER_SOURCE_CONFIG = {
    "document": ("Doc Pre-fill", (120, 140, 180)),
    "document_confirmed": ("Doc Confirmed", (100, 160, 130)),
    "human_override": ("Doc Override", (180, 140, 100)),
    "inferred": ("Inferred", (140, 130, 170)),
    # "human" -> no indicator shown (default)
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


def brand_rgb() -> tuple[int, int, int]:
    """Convert the configured CSS-style primary color to an fpdf RGB tuple."""
    value = settings.firm_primary_hex.removeprefix("#")
    if len(value) != 6:
        raise ValueError("FIRM_PRIMARY_HEX must be a six-digit hexadecimal color")
    try:
        r, g, b = (int(value[index:index + 2], 16) for index in (0, 2, 4))
        return (r, g, b)
    except ValueError as exc:
        raise ValueError("FIRM_PRIMARY_HEX must be a six-digit hexadecimal color") from exc


def _firm_logo_path() -> Path | None:
    """Resolve an operator-provisioned logo against the repository root."""
    if not settings.firm_logo_path:
        return None
    logo_path = Path(settings.firm_logo_path).expanduser()
    if not logo_path.is_absolute():
        logo_path = REPO_ROOT / logo_path
    return logo_path if logo_path.is_file() else None


def _set_font_to_fit(
    pdf: FPDF,
    text: str,
    max_width: float,
    *,
    style: str = "B",
    start_size: int = 12,
    min_size: int = 7,
) -> None:
    """Select the largest built-in font size that fits one line."""
    for size in range(start_size, min_size - 1, -1):
        pdf.set_font("Helvetica", style, size)
        if pdf.get_string_width(S(text)) <= max_width:
            return
    pdf.set_font("Helvetica", style, min_size)


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
                     counts: dict, total: int, *, show_insufficient_evidence: bool = True):
    """Draw a stacked horizontal bar showing compliance distribution."""
    if total == 0:
        return
    cur_x = x
    order = [
        "compliant",
        "partially_compliant",
        "non_compliant",
        "not_assessed",
        "insufficient_evidence",
    ]
    labels = {
        "compliant": "Compliant",
        "partially_compliant": "Partial",
        "non_compliant": "Non-Compliant",
        "not_assessed": "N/A",
        "insufficient_evidence": "Insufficient evidence",
    }
    legend_order = order if show_insufficient_evidence else order[:-1]
    for status in legend_order:
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
    for status in legend_order:
        count = counts.get(status, 0)
        r, g, b = STATUS_COLORS[status]
        pdf.set_fill_color(r, g, b)
        pdf.rect(leg_x, legend_y, 3, 3, style="F")
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*MID_TEXT)
        pdf.text(leg_x + 4, legend_y + 2.5, S(f"{labels[status]} ({count})"))
        leg_x += 38


def _draw_timeline_block(pdf: FPDF, x: float, y: float, w: float,
                         priority: int, items: list):
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
        if item.remediation_effort and item.timeline_weeks:
            tag_text = S(f"{item.remediation_effort} | ~{item.timeline_weeks}w")
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


def _draw_gap_card(pdf: FPDF, item, x: float, y: float, w: float,
                   show_evidence: bool = False,
                   answer_source: str | None = None) -> float:
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

    # Answer source indicator (subtle, muted pill below badges)
    source_cfg = ANSWER_SOURCE_CONFIG.get(answer_source or "") if answer_source else None
    if source_cfg:
        src_label, (src_r, src_g, src_b) = source_cfg
        # Position below the badges row
        src_y = y + 6.5
        pdf.set_fill_color(src_r, src_g, src_b)
        src_w = pdf.get_string_width(src_label) + 4
        pdf.rect(badge_x, src_y, src_w, 4, style="F", round_corners=True, corner_radius=1)
        pdf.set_font("Helvetica", "", 5.5)
        pdf.set_text_color(*WHITE)
        pdf.text(badge_x + 2, src_y + 3, src_label)

    # Gap description (truncated)
    cur_y = y + 9 + (4.5 if source_cfg else 0)
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
                      score: float, rating: str, items: list):
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
    pdf.cell(0, 5, text=S(f"{settings.firm_name}  |  CONFIDENTIAL  |  {company_name}"), align="L")
    pdf.cell(0, 5, text=f"Page {pdf.page_no()}/{{nb}}", align="R")


def _page_header(pdf: FPDF, section_title: str):
    """Draw header bar on non-cover pages."""
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, PW, 12, style="F")
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_text_color(*WHITE)
    pdf.text(PM, 8, S(f"{settings.firm_name}  |  {section_title}"))
    pdf.set_y(16)


def _section_title(pdf: FPDF, title: str):
    """Draw a section heading."""
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 8, text=S(title))
    pdf.ln(10)


# Findings and evidence chain (P3-3)

def _draw_finding_detail(pdf: FPDF, finding, index: int, y: float) -> float:
    """Draw one approved finding and its evidence chain."""
    risk_color = RISK_COLORS.get(finding.severity, NAVY)
    pdf.set_fill_color(*risk_color)
    pdf.rect(PM, y, 2.5, 8, style="F")
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*DARK_TEXT)
    pdf.set_xy(PM + 5, y)
    pdf.multi_cell(
        CW - 5,
        4,
        text=S(f"F{index}. {finding.title}"),
        new_x="LMARGIN",
    )
    y = pdf.get_y() + 2

    def paragraph(text: str, *, style: str = "", size: float = 7.5, color=MID_TEXT):
        pdf.set_font("Helvetica", style, size)
        pdf.set_text_color(*color)
        pdf.set_xy(PM + 5, y)
        pdf.multi_cell(CW - 5, 3.7, text=S(text), new_x="LMARGIN")
        return pdf.get_y()

    y = paragraph(
        f"{finding.framework_name} {finding.requirement_id}: "
        f"{finding.requirement_title}"
    ) + 1
    y = paragraph(
        f"Severity: {finding.severity.title()} | Priority P{finding.priority} | "
        f"Finding status: {finding.status_label}"
    ) + 1
    decided_date = (
        finding.decided_at.strftime("%d %b %Y")
        if finding.decided_at is not None
        else "unknown date"
    )
    y = paragraph(
        f"Decision: {finding.outcome_label}, {finding.decision_label} by "
        f"{finding.decided_by or 'unknown'} on {decided_date}, "
        f"record v{finding.decision_version} | Workpaper ref: {finding.workpaper_ref}"
    ) + 1
    description = finding.description or ""
    if len(description) > 600:
        description = f"{description[:600]}..."
    if description:
        y = paragraph(description) + 1

    y = paragraph("Evidence chain:", style="B", color=DARK_TEXT) + 1
    if finding.citations:
        for citation_index, citation in enumerate(finding.citations, start=1):
            excerpt = citation.excerpt or ""
            if len(excerpt) > 300:
                excerpt = f"{excerpt[:300]}..."
            y = paragraph(f'[{citation_index}] "{excerpt}"', style="I") + 0.5
            if not citation.resolved:
                y = paragraph("Unresolved evidence") + 0.5
            else:
                version = citation.version_number or "unknown"
                filename = citation.filename or "unknown file"
                location = citation.location_ref or "unknown location"
                sha256 = citation.sha256[:16] if citation.sha256 else "unknown"
                suffix = " | superseded version" if not citation.is_current else ""
                y = paragraph(
                    f"{filename} v{version} | {location} | SHA-256 {sha256}{suffix}"
                ) + 0.5
    elif finding.citations_captured:
        y = paragraph("No supporting citation (explicit evidence absence)") + 0.5
    else:
        y = paragraph("Evidence support not captured (legacy)") + 0.5

    y = paragraph("Actions:", style="B", color=DARK_TEXT) + 1
    if finding.actions:
        for action in finding.actions:
            target = (
                action.target_date.strftime("%Y-%m-%d")
                if action.target_date is not None
                else "No target date"
            )
            y = paragraph(
                f"- {action.title} | Owner: {action.owner or 'Unassigned'} | "
                f"Target: {target} | {action.status_label}"
            ) + 0.5
    else:
        y = paragraph("No actions recorded.") + 0.5
    return y + 4


def _render_findings_section(
    pdf: FPDF,
    company_name: str,
    report_findings,
    *,
    header: str = "Findings and Evidence Chain",
):
    """Render the additive approved-findings section."""
    pdf.add_page()
    _page_header(pdf, header)
    _section_title(pdf, "Approved Findings")
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*MID_TEXT)
    pdf.set_x(PM)
    pdf.multi_cell(
        CW,
        3.8,
        text=S(
            "Each finding below is bound to an individually approved requirement "
            "decision and lists the evidence it cites."
        ),
        new_x="LMARGIN",
    )
    if report_findings.omitted_count > 0:
        pdf.set_x(PM)
        pdf.multi_cell(
            CW,
            3.8,
            text=S(
                f"{report_findings.omitted_count} finding(s) not shown: their source "
                "decision is not a current individual consultant approval."
            ),
            new_x="LMARGIN",
        )
    pdf.ln(2)

    current_framework = None
    finding_index = 0
    for finding in report_findings.findings:
        if finding.framework_id != current_framework:
            if pdf.get_y() > 245:
                _page_footer(pdf, company_name)
                pdf.add_page()
                _page_header(pdf, f"{header} (continued)")
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*NAVY)
            pdf.set_xy(PM, pdf.get_y())
            pdf.multi_cell(CW, 5, text=S(finding.framework_name), new_x="LMARGIN")
            current_framework = finding.framework_id
            pdf.ln(1)

        if pdf.get_y() > 250:
            _page_footer(pdf, company_name)
            pdf.add_page()
            _page_header(pdf, f"{header} (continued)")
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*NAVY)
            pdf.set_xy(PM, pdf.get_y())
            pdf.multi_cell(CW, 5, text=S(finding.framework_name), new_x="LMARGIN")
            pdf.ln(1)

        finding_index += 1
        pdf.set_y(pdf.get_y())
        new_y = _draw_finding_detail(pdf, finding, finding_index, pdf.get_y())
        pdf.set_y(new_y)

    _page_footer(pdf, company_name)


# ---------------------------------------------------------------------------
# Main PDF generation
# ---------------------------------------------------------------------------

def generate_pdf(
    report: object,
    gap_items: list,
    company_name: str,
    initiatives: list | None = None,
    answer_source_map: dict[str, str] | None = None,
    selected_frameworks: list[str] | None = None,
    assessment=None,
    report_findings=None,
) -> bytes:
    """Generate a board-level PDF report."""
    selected_frameworks = selected_frameworks or ["dpdpa"]
    dpdpa_only = selected_frameworks == ["dpdpa"]
    has_dpdpa = "dpdpa" in selected_frameworks

    framework_metadata = []
    for fw_id in selected_frameworks:
        fw_def = FrameworkRegistry.get_or_none(fw_id)
        framework_metadata.append((fw_id, fw_def.name if fw_def else fw_id.upper()))
    framework_names = [name for _framework_id, name in framework_metadata]
    frameworks_label = ", ".join(framework_names) if framework_names else "the assessed framework"

    if dpdpa_only:
        cover_title = "DPDPA Compliance"
    elif len(framework_names) == 1:
        cover_title = f"{framework_names[0]} Compliance"
    else:
        cover_title = "Multi-Framework Compliance"
    chapter_scores = json.loads(report.chapter_scores or "{}")
    score_assessment = assessment or SimpleNamespace(frameworks=selected_frameworks)
    framework_scores = report_framework_scores(report, score_assessment)
    approved_input = any(
        isinstance(scores, dict) and "status" in scores
        for scores in framework_scores.values()
    )
    framework_score_rows = []
    for framework_id, framework_name in framework_metadata:
        scores = framework_scores.get(framework_id)
        if not scores or scores.get("overall_score") is None:
            continue
        framework_score_rows.append((
            framework_id,
            framework_name,
            scores["overall_score"],
            scores.get("overall_rating", "N/A"),
        ))
    failed_framework_names = [
        framework_name
        for framework_id, framework_name in framework_metadata
        if is_failed_framework_score(framework_scores.get(framework_id))
    ]

    # Compute summary stats
    counts = {
        "compliant": 0,
        "partially_compliant": 0,
        "non_compliant": 0,
        "not_assessed": 0,
        "insufficient_evidence": 0,
    }
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
    chapters_grouped: dict[str, list] = {}
    for item in gap_items:
        chapters_grouped.setdefault(item.chapter, []).append(item)

    priority_grouped: dict[int, list] = {}
    for item in gap_items:
        if item.compliance_status not in (
            "compliant",
            "not_assessed",
            "insufficient_evidence",
        ):
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

    logo_path = _firm_logo_path()
    if logo_path:
        pdf.image(
            logo_path,
            x=PW - PM - 40,
            y=7,
            w=40,
            h=20,
            keep_aspect_ratio=True,
        )

    # Title
    firm_title_width = CW - 50 if logo_path else CW
    _set_font_to_fit(pdf, settings.firm_name, firm_title_width)
    pdf.set_text_color(*WHITE)
    pdf.text(PM, 15, S(settings.firm_name))
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(*WHITE)
    pdf.text(PM, 28, S(cover_title))
    pdf.set_font("Helvetica", "", 24)
    pdf.text(PM, 40, "Gap Assessment Report")

    # Date
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(180, 180, 210)
    date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
    pdf.text(PM, 50, date_str)

    # Company name
    pdf.set_font("Helvetica", "", 18)
    pdf.set_text_color(*DARK_TEXT)
    pdf.text(PM, 75, S(company_name))

    # Divider line
    pdf.set_draw_color(*brand_rgb())
    pdf.set_line_width(0.8)
    pdf.line(PM, 80, PW - PM, 80)
    pdf.set_line_width(0.2)

    # Frameworks assessed (only worth spelling out beyond the title for multi-framework)
    if not dpdpa_only:
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*MID_TEXT)
        pdf.text(PM, 88, S(f"Frameworks assessed: {frameworks_label}"))
    if failed_framework_names:
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*RISK_COLORS["critical"])
        pdf.text(
            PM,
            94,
            S(f"Incomplete: analysis failed for {', '.join(failed_framework_names)}. Not scored."),
        )

    # One score ring per framework; no cross-framework ring exists.
    cy = 130
    ring_count = len(framework_score_rows)
    ring_radius = 30 if ring_count == 1 else (22 if ring_count in (2, 3) else 18)
    for index, (_framework_id, framework_name, framework_score, framework_rating) in enumerate(
        framework_score_rows
    ):
        cx = PM + CW * (index + 0.5) / ring_count
        _draw_score_ring(pdf, cx, cy, ring_radius, framework_score, framework_rating)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*MID_TEXT)
        framework_label = S(framework_name)
        label_width = pdf.get_string_width(framework_label)
        pdf.text(cx - label_width / 2, cy + ring_radius + 10, framework_label)

    # Summary stats below ring
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*MID_TEXT)
    summary_text = (
        f"{total} requirements assessed  |  {critical_count + high_count} gaps identified"
        if max_weeks == 0
        else f"{total} requirements assessed  |  {critical_count + high_count} gaps identified  |  ~{max_weeks} weeks to full remediation"
    )
    tw = pdf.get_string_width(summary_text)
    pdf.text((PW - tw) / 2, 182, S(summary_text))

    # Bottom section: chapter score preview bars
    bar_y = 202
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
    card_w = (CW - 6) / 3  # 3 cards with 3px gaps
    card_y = pdf.get_y() + 2
    _draw_kpi_card(pdf, PM, card_y, card_w, 27,
                   str(critical_count), "Critical Gaps", RISK_COLORS["critical"])
    _draw_kpi_card(pdf, PM + card_w + 3, card_y, card_w, 27,
                   str(high_count), "High Risk Gaps", RISK_COLORS["high"])
    _draw_kpi_card(
        pdf,
        PM + 2 * (card_w + 3),
        card_y,
        card_w,
        27,
        "n/a" if max_weeks == 0 else f"~{max_weeks}w",
        "Remediation Timeline (not estimated)" if max_weeks == 0 else "Remediation Timeline",
        NAVY,
    )

    # Per-framework scores
    pdf.set_y(card_y + 35)
    _section_title(pdf, "Framework Scores")
    framework_bar_y = pdf.get_y()
    for _framework_id, framework_name, framework_score, framework_rating in framework_score_rows:
        _draw_h_bar(
            pdf,
            PM,
            framework_bar_y,
            CW,
            8,
            framework_score,
            S(framework_name),
            framework_rating,
        )
        framework_bar_y += 11
    if failed_framework_names:
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*RISK_COLORS["critical"])
        for framework_name in failed_framework_names:
            pdf.text(PM, framework_bar_y, S(f"{framework_name}: analysis failed. Not scored."))
            framework_bar_y += 11

    for framework_id, framework_name in framework_metadata:
        scores = framework_scores.get(framework_id) or {}
        coverage = scores.get("coverage")
        if not coverage:
            continue
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*MID_TEXT)
        if scores.get("status") == "scored":
            coverage_text = (
                f"{framework_name}: {coverage['scored']} of {coverage['in_scope']} "
                "in-scope requirements scored; "
                f"{coverage['insufficient_evidence']} insufficient evidence "
                "(excluded from the score, not counted as non-compliant); "
                f"{coverage['not_applicable']} not applicable."
            )
            pdf.text(PM, framework_bar_y, S(coverage_text))
            framework_bar_y += 7
        elif scores.get("status") == "not_scored":
            pdf.text(
                PM,
                framework_bar_y,
                S(f"{framework_name}: not scored. No in-scope requirement has a scoring outcome."),
            )
            framework_bar_y += 7

    # Compliance distribution bar
    pdf.set_y(framework_bar_y + 5)
    _section_title(pdf, "Compliance Distribution")
    _draw_status_bar(
        pdf,
        PM,
        pdf.get_y(),
        CW,
        10,
        counts,
        total,
        show_insufficient_evidence=approved_input,
    )

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

        src = (answer_source_map or {}).get(item.requirement_id)
        h = _draw_gap_card(pdf, item, PM, card_y, CW, answer_source=src)
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
            elif item.compliance_status in ("not_assessed", "insufficient_evidence"):
                status_color = (
                    "insufficient_evidence"
                    if item.compliance_status == "insufficient_evidence"
                    else "not_assessed"
                )
                pdf.set_fill_color(*STATUS_COLORS[status_color])
                pdf.rect(PM, cur_y, 2, 5, style="F")
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(*LIGHT_TEXT)
                label = (
                    "Insufficient evidence"
                    if item.compliance_status == "insufficient_evidence"
                    else "N/A"
                )
                pdf.text(
                    PM + 4,
                    cur_y + 3.8,
                    S(f"{label}  {item.requirement_id}: {item.requirement_title[:70]}"),
                )
                pdf.set_y(cur_y + 7)
            else:
                # Full card for gaps (with evidence in appendix)
                src = (answer_source_map or {}).get(item.requirement_id)
                h = _draw_gap_card(pdf, item, PM, cur_y, CW, show_evidence=True, answer_source=src)
                pdf.set_y(cur_y + h + 4)

        _page_footer(pdf, company_name)

    if report_findings is not None and (report_findings.findings or report_findings.omitted_count):
        _render_findings_section(pdf, company_name, report_findings)

    # ===================================================================
    # APPENDIX: SCOPE & LIMITATIONS
    # ===================================================================
    pdf.add_page()
    _page_header(pdf, "Scope & Limitations")
    _section_title(pdf, "Scope & Limitations")

    assessment_date = datetime.now(timezone.utc).strftime("%B %d, %Y")

    if dpdpa_only:
        scope_of_coverage = (
            "The assessment evaluates the organization's compliance posture against 41 requirements "
            "derived from the Digital Personal Data Protection Act, 2023 (DPDPA). These requirements span "
            "six domains: (1) Obligations of Data Fiduciary, (2) Rights of Data Principal, (3) Special "
            "Provisions for Children and Significant Data Fiduciaries, (4) Consent Management, (5) "
            "Cross-Border Data Transfer, and (6) Breach Notification."
        )
    else:
        scope_of_coverage = (
            f"The assessment evaluates the organization's compliance posture against {len(gap_items)} "
            f"requirements across the following framework(s): {frameworks_label}."
        )

    if dpdpa_only:
        not_covered_text = (
            "This assessment does not include technical penetration testing, source code review, "
            "network security assessment, physical security review, or any form of independent "
            "technical verification. Findings in areas where the organization provided limited "
            "or no evidence are based on stated intent and disclosed posture only."
        )
    else:
        not_covered_text = (
            "This assessment does not include technical penetration testing, source code review, "
            "network security assessment, or any form of independent technical verification. "
            "Where the selected framework(s) include physical or environmental controls, findings "
            "on those controls are based on disclosed information and submitted documents, not on "
            "an on-site inspection. Findings in areas where the organization provided limited or no "
            "evidence are based on stated intent and disclosed posture only."
        )

    if dpdpa_only:
        follow_on_text = (
            "For requirements rated as Non-Compliant or Partially Compliant at a Critical or High "
            "risk level, independent verification by a qualified legal counsel or certified privacy "
            "professional is strongly recommended before relying on those findings for regulatory "
            "submissions, board reporting, or contractual representations."
        )
    elif has_dpdpa:
        other_names = ", ".join(
            name for framework_id, name in framework_metadata if framework_id != "dpdpa"
        )
        follow_on_text = (
            "For requirements rated as Non-Compliant or Partially Compliant at a Critical or High "
            "risk level, independent verification by qualified legal counsel or a certified privacy "
            f"professional (for DPDPA requirements), or by a qualified information security auditor "
            f"(for {other_names}), is strongly recommended before relying on those findings for "
            "regulatory submissions, board reporting, or contractual representations."
        )
    else:
        follow_on_text = (
            "For requirements rated as Non-Compliant or Partially Compliant at a Critical or High "
            "risk level, independent verification by a qualified information security auditor is "
            "strongly recommended before relying on those findings for certification, board reporting, "
            "or contractual representations."
        )

    scope_text = f"""Assessment Date: {assessment_date}

Nature of Assessment:
This document constitutes a questionnaire-based compliance gap assessment. It is not a formal compliance audit and does not constitute legal advice. Findings are based solely on information disclosed by the organization's representatives during the structured assessment interview and from documents voluntarily submitted for review.

Scope of Coverage:
{scope_of_coverage}

What Is Not Covered:
{not_covered_text}

Reliance on Disclosed Information:
All findings reflect the information provided to the assessor at the time of the assessment. The assessor has not independently verified the accuracy or completeness of information provided. Material omissions or inaccuracies in disclosed information would affect the reliability of findings.

Recommended Follow-On Actions:
{follow_on_text}

Confidentiality:
This report is prepared solely for the use of the named organization. It should not be shared with third parties without the organization's explicit consent. {settings.firm_name} and the named organization are the intended recipients of this report."""

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

    if dpdpa_only:
        methodology_intro = (
            "This assessment evaluates compliance against India's Digital Personal Data Protection "
            "Act, 2023 (DPDPA) across 41 requirements organized in 6 chapters. The assessment combines "
            "questionnaire responses from organizational stakeholders with analysis of uploaded policy "
            "documents."
        )
        framework_overview = (
            "Framework Overview:\n"
            "The 41 requirements are derived directly from DPDPA statutory text and cover all "
            "obligations applicable to a Data Fiduciary operating in India. Requirements are organized "
            "into chapters aligned with the Act's chapter structure, with each chapter weighted to "
            "reflect regulatory emphasis and penalty exposure.\n\n"
        )
        chapter_weights_block = (
            "Chapter Weights:\n"
            "- Obligations of Data Fiduciary (Ch. 2): 30%\n"
            "- Rights of Data Principal (Ch. 3): 20%\n"
            "- Special Provisions - Children & SDF (Ch. 4): 20%\n"
            "- Consent Management (detailed): 10%\n"
            "- Cross-Border Data Transfer: 10%\n"
            "- Breach Notification: 10%\n\n"
        )
        risk_basis = "regulatory exposure, potential penalties under the Schedule to the DPDPA, and impact on data principals"
    else:
        methodology_intro = (
            f"This assessment evaluates compliance against the following framework(s): {frameworks_label}, "
            f"across {len(gap_items)} requirements. The assessment combines questionnaire responses from "
            "organizational stakeholders with analysis of uploaded policy documents."
        )
        framework_overview = (
            "Framework Overview:\n"
            f"Requirements are referenced by clause or control identifier for each selected framework "
            f"({frameworks_label}); requirement descriptions are summarised for assessment purposes "
            "and do not reproduce the source standard. Each framework retains its own internal chapter/domain structure and "
            "weighting; scores are computed and reported independently for each framework.\n\n"
        )
        chapter_weights_block = ""
        risk_basis = "regulatory exposure, potential penalties under the applicable framework(s), and impact on affected individuals"

    strategic_initiatives_block = (
        "Strategic Initiatives:\n"
        "Gaps are clustered by root cause (Policy, People, Process, Technology, Governance) into named remediation initiatives. Each initiative groups related requirements that share a common fix pattern, enabling efficient resource and budget allocation. Initiatives are sequenced considering prerequisite dependencies between requirements.\n\n"
        if initiatives or not approved_input
        else ""
    )
    approved_scoring_basis = (
        "Scoring Basis:\n"
        "Scores are computed only from conclusions a consultant has individually approved. "
        "Each approved outcome counts as follows: Compliant 100 points, Partially Compliant "
        "50 points, Non-Compliant 0 points. Not Applicable and Insufficient Evidence are "
        "excluded from the scoring denominator. Insufficient Evidence is not treated as "
        "Non-Compliant; the number of requirements with insufficient evidence is reported "
        "next to each framework score. Requirements excluded at scoping are not scored. "
        "A framework is scored only when every in-scope requirement has an approved "
        "conclusion.\n\n"
        if approved_input
        else ""
    )

    methodology = f"""{methodology_intro}

{framework_overview}GRC Response Scale:
Questionnaire responses use a five-option scale:
- Fully Implemented: Control exists, is documented, consistently applied, and evidence is available (maps to Compliant - 100 points)
- Partially Implemented: Control exists in some form but is inconsistent, undocumented, or not fully operational (maps to Partially Compliant - 50 points)
- Planned: Control is not yet in place but there is a documented plan or budget commitment (maps to Non-Compliant - 0 points; recognized in remediation priority)
- Not Implemented: No control exists and none is planned (maps to Non-Compliant - 0 points)
- Not Applicable: Requirement does not apply to this organization's processing activities (excluded from scoring denominator)

Scoring Formula:
Each requirement is scored based on its GRC response. Section scores are the unweighted average of constituent requirement scores. Chapter scores are weighted averages of section scores using published section weights. The overall score is the weighted average of chapter scores using the published chapter/domain weights. Not Applicable responses are excluded from the denominator, so scores reflect the applicable compliance universe only.

{approved_scoring_basis}{chapter_weights_block}Rating Thresholds:
- 80-100%: Compliant
- 60-79%: Partially Compliant
- 40-59%: Needs Significant Improvement
- 0-39%: Non-Compliant

Risk Classification:
Gaps are classified by risk level (Critical, High, Medium, Low) based on {risk_basis}. Remediation priorities (P1-P4) are assigned based on risk severity and implementation dependencies between requirements.

Maturity Model (CMMI-Aligned):
Each gap is assigned a current maturity rating on a 0-5 scale:
M0 - Non-existent: No awareness or capability; requirement is entirely unaddressed
M1 - Initial: Ad-hoc or reactive; no repeatable process; relies on individual knowledge
M2 - Managed: Some process exists but applied inconsistently; not documented or auditable
M3 - Defined: Consistent, documented, and auditable process; meets minimum regulatory bar
M4 - Quantitative: Process is measured with KPIs; performance tracked and reported
M5 - Optimizing: Continuous improvement cycle in place; best-in-class privacy practice
The minimum remediation target for regulatory compliance is M3 (Defined). The gap between current maturity and M3 drives the remediation effort estimate.

{strategic_initiatives_block}Disclaimer:
This assessment provides guidance based on the information provided and should not be considered legal advice. Organizations should consult qualified legal counsel for definitive compliance determinations."""

    pdf.set_x(PM)
    pdf.multi_cell(CW, 4.5, text=S(methodology), new_x="LMARGIN")

    _page_footer(pdf, company_name)

    return bytes(pdf.output())


def generate_integrated_pdf(report_data) -> bytes:
    """Generate a write-once integrated report with separate assessment sections."""
    pdf = FPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=False)

    pdf.add_page()
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, PW, 55, style="F")
    _set_font_to_fit(pdf, settings.firm_name, CW)
    pdf.set_text_color(*WHITE)
    pdf.text(PM, 15, S(settings.firm_name))
    pdf.set_font("Helvetica", "B", 22)
    pdf.text(PM, 29, "Integrated Engagement Report")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(180, 180, 210)
    pdf.text(PM, 42, datetime.now(timezone.utc).strftime("%B %d, %Y"))

    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*DARK_TEXT)
    pdf.text(PM, 78, S(report_data.engagement_name))
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*MID_TEXT)
    pdf.text(PM, 88, S(report_data.client_name))
    pdf.set_draw_color(*brand_rgb())
    pdf.set_line_width(0.8)
    pdf.line(PM, 96, PW - PM, 96)
    pdf.set_line_width(0.2)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*DARK_TEXT)
    pdf.text(PM, 108, S(f"Assessments included: {len(report_data.sections)}"))
    cover_y = 119
    for section in report_data.sections:
        pdf.set_xy(PM, cover_y)
        pdf.multi_cell(CW, 4.5, text=S(section.label), new_x="LMARGIN")
        cover_y = pdf.get_y() + 2
    pdf.set_xy(PM, max(cover_y + 8, 145))
    pdf.multi_cell(
        CW,
        4.5,
        text=S(
            "Results are reported separately for each assessment and framework. "
            "Scores are never combined across assessments or frameworks."
        ),
        new_x="LMARGIN",
    )
    _page_footer(pdf, report_data.client_name)

    for section in report_data.sections:
        pdf.add_page()
        _page_header(pdf, f"Assessment: {section.label}")
        _section_title(pdf, section.label)
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(*DARK_TEXT)
        scope_lines = [
            f"Assessment created: {section.created_at:%d %b %Y}",
            "Analysis date: "
            + (
                section.analysed_at.strftime("%d %b %Y")
                if section.analysed_at is not None
                else "not recorded"
            ),
            "Frameworks and pack versions: "
            + ", ".join(
                f"{name} ({version})" for name, version in section.frameworks
            ),
            f"Scope: {section.scope_label}",
            "Assessment period and evidence cut-off: not recorded",
        ]
        for line in scope_lines:
            pdf.set_x(PM)
            pdf.multi_cell(CW, 4, text=S(line), new_x="LMARGIN")
        pdf.ln(3)
        _section_title(pdf, "Framework Scores (this assessment only)")
        if section.scores:
            score_y = pdf.get_y()
            for line in section.scores:
                _draw_h_bar(
                    pdf,
                    PM,
                    score_y,
                    CW,
                    8,
                    line.score,
                    line.framework_name,
                    line.rating,
                )
                score_y += 11
            pdf.set_y(score_y + 3)
        else:
            pdf.set_font("Helvetica", "", 8.5)
            pdf.set_text_color(*MID_TEXT)
            pdf.set_x(PM)
            pdf.multi_cell(
                CW,
                4,
                text="Scores unavailable for this assessment.",
                new_x="LMARGIN",
            )
        _page_footer(pdf, report_data.client_name)
        if section.findings.findings or section.findings.omitted_count:
            _render_findings_section(
                pdf,
                report_data.client_name,
                section.findings,
                header=f"Assessment: {section.label}",
            )

    if report_data.excluded:
        pdf.add_page()
        _page_header(pdf, "Assessments Not Included")
        _section_title(pdf, "Assessments Not Included")
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(*DARK_TEXT)
        for excluded in report_data.excluded:
            pdf.set_x(PM)
            pdf.multi_cell(
                CW,
                4,
                text=S(f"{excluded.label}: {excluded.reason}"),
                new_x="LMARGIN",
            )
            pdf.ln(1)
        _page_footer(pdf, report_data.client_name)

    return bytes(pdf.output())
