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
from app.dpdpa.framework import DPDPA_READINESS_NOTE, dpdpa_readiness_note_applies
from app.frameworks.registry import FrameworkRegistry
from app.services.report_basis import EMPTY_BASIS, ReportBasis, basis_for
from app.services.scoring import (
    RATING_THRESHOLDS,
    is_failed_framework_score,
    report_framework_scores,
)

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
    "\u00a0": " ", "₹": "Rs.",
})

GAP_STATUSES = ("non_compliant", "partially_compliant")
LEGAL_FRAMEWORK_IDS = frozenset({"dpdpa", "gdpr", "hipaa"})
COVER_AREA_ROWS = 7
HEATMAP_SQUARES_PER_LINE = 17
CONTENT_BOTTOM = 270
NOT_RECORDED = "not recorded"

# Page dimensions (A4)
PW = 210  # page width
PM = 15   # page margin
CW = PW - 2 * PM  # content width


def S(text: str) -> str:
    """Make text safe for fpdf2 built-in fonts (latin-1)."""
    if not text:
        return ""
    return text.translate(_UNICODE_MAP).encode("latin-1", errors="replace").decode("latin-1")


def heatmap_row_height(item_count: int) -> float:
    return max(14.0, math.ceil(item_count / HEATMAP_SQUARES_PER_LINE) * 5.5 + 3)


def count_gaps(gap_items) -> int:
    return sum(item.compliance_status in GAP_STATUSES for item in gap_items)


def _framework_label(framework_ids) -> str:
    names = []
    for framework_id in dict.fromkeys(framework_ids):
        framework = FrameworkRegistry.get_or_none(framework_id)
        names.append(framework.name if framework else framework_id.upper())
    return ", ".join(names) or "the assessed framework"


def _regimes(framework_ids) -> tuple[list[str], list[str]]:
    legal = []
    standards = []
    for framework_id in dict.fromkeys(framework_ids):
        framework = FrameworkRegistry.get_or_none(framework_id)
        name = framework.name if framework else framework_id.upper()
        if framework_id in LEGAL_FRAMEWORK_IDS:
            legal.append(name)
        else:
            standards.append(name)
    return legal, standards


def _basis_lines(basis: ReportBasis, generated: datetime) -> list[str]:
    return [
        f"Assessment period: {basis.period_label}",
        f"Evidence cut-off: {basis.cutoff_label}",
        f"Report generated: {generated:%d %b %Y}",
    ]


def _nature_text(framework_ids) -> str:
    legal, _standards = _regimes(framework_ids)
    status = (
        "It is not a formal compliance audit and does not constitute legal advice."
        if legal
        else "It is not a formal compliance or certification audit."
    )
    return (
        "This document constitutes an evidence-based compliance gap assessment. "
        f"{status} Findings are based on documents submitted for review and information "
        "disclosed by the organization's representatives, and every conclusion was "
        "individually approved by a consultant. These conclusions reflect the evidence considered "
        "up to the evidence cut-off stated above."
    )


def _follow_on_text(framework_ids) -> str:
    legal, standards = _regimes(framework_ids)
    lead = (
        "For requirements rated as Non-Compliant or Partially Compliant at a Critical or High "
        "risk level, independent verification by "
    )
    if legal and standards:
        return (
            f"{lead}qualified legal counsel or a certified privacy professional (for "
            f"{_framework_label(legal)} requirements), or by a qualified information security "
            f"auditor (for {_framework_label(standards)}), is strongly recommended before relying "
            "on those findings for regulatory submissions, board reporting, or contractual "
            "representations."
        )
    if legal:
        return (
            f"{lead}qualified legal counsel or a certified privacy professional is strongly "
            "recommended before relying on those findings for regulatory submissions, board "
            "reporting, or contractual representations."
        )
    return (
        f"{lead}a qualified information security auditor is strongly recommended before "
        "relying on those findings for certification, board reporting, or contractual "
        "representations."
    )


def _risk_basis(framework_ids) -> str:
    legal, standards = _regimes(framework_ids)
    legal_basis = (
        f"regulatory exposure, potential penalties under {_framework_label(legal)} and impact "
        "on affected individuals"
    )
    security_basis = (
        "likely impact on the confidentiality, integrity and availability of information"
    )
    if legal and standards:
        return (
            f"{legal_basis} (for {_framework_label(legal)}), and {security_basis} "
            f"(for {_framework_label(standards)})"
        )
    return legal_basis if legal else security_basis


def _disclaimer_text(framework_ids) -> str:
    legal, standards = _regimes(framework_ids)
    parts = []
    if legal:
        parts.append(
            "This assessment provides guidance based on the information and evidence provided "
            "and is not legal advice. Consult qualified legal counsel for definitive compliance "
            f"determinations under {_framework_label(legal)}."
        )
    if standards:
        parts.append(
            ("For " if legal else "This assessment provides guidance based on the information "
             "and evidence provided. For ")
            + f"{_framework_label(standards)}, it is not a certification audit; certification "
            "decisions rest with an accredited certification body or qualified assessor."
        )
    return " ".join(parts)


def _framework_structure_text(framework_ids) -> str:
    lines = []
    for framework_id in dict.fromkeys(framework_ids):
        framework = FrameworkRegistry.get_or_none(framework_id)
        if framework is None:
            continue
        domains = framework.as_legacy_framework_dict()
        weights = ", ".join(
            f"{domain['title']} {round(domain['weight'] * 100)}%"
            for domain in domains.values()
        )
        lines.append(
            f"- {framework.name} ({framework.version}): {framework.control_count()} "
            f"requirements in {len(domains)} domains. Domain weights: {weights}."
        )
    return "\n".join(lines)


def methodology_text(framework_ids, requirement_count: int | None) -> str:
    """Framework-correct methodology for approved-conclusion reports (P6-6, D0 #5/#6)."""
    count_clause = (
        f", across {requirement_count} in-scope requirements"
        if requirement_count is not None
        else ""
    )
    thresholds = []
    upper = 100
    for threshold, rating in RATING_THRESHOLDS:
        thresholds.append(f"- {threshold}-{upper}%: {rating}")
        upper = threshold - 1
    return f"""This assessment evaluates compliance against the following framework(s): {_framework_label(framework_ids)}{count_clause}.

Basis of Assessment:
Each in-scope requirement receives one conclusion. The analysis engine reviews the submitted documents and questionnaire responses and proposes an outcome with cited evidence. A consultant reviews the evidence and individually approves, edits or rejects every proposal. Only individually approved conclusions appear in this report; no outcome, score or finding is produced by the AI on its own.

Outcome Definitions:
- Compliant: the requirement is met and supported by evidence
- Partially Compliant: the requirement is met in part
- Non-Compliant: the requirement is not met
- Insufficient Evidence: the evidence provided does not support a conclusion either way
- Not Applicable: the requirement does not apply within the assessed scope

Scoring Basis:
Scores are computed only from conclusions a consultant has individually approved. Each approved outcome counts as follows: Compliant 100 points, Partially Compliant 50 points, Non-Compliant 0 points. Not Applicable and Insufficient Evidence are excluded from the scoring denominator. Insufficient Evidence is not treated as Non-Compliant; the number of requirements with insufficient evidence is reported next to each framework score. Requirements excluded at scoping are not scored. A framework is scored only when every in-scope requirement has an approved conclusion. Section scores are the average of their requirement points; domain and framework scores are weighted averages using the published weights below.

Framework Structure and Weights:
{_framework_structure_text(framework_ids)}
Requirements are referenced by clause or control identifier for each selected framework; requirement descriptions are summarised for assessment purposes and do not reproduce the source standard. Scores are computed and reported independently for each framework; no score is combined across frameworks.

Rating Thresholds:
{chr(10).join(thresholds)}

Risk Classification:
Each gap carries the risk level (Critical, High, Medium, Low) approved by the consultant, reflecting {_risk_basis(framework_ids)}. Remediation priority on each gap is derived from its approved risk level.

Disclaimer:
{_disclaimer_text(framework_ids)}"""


def _render_sign_off_page(pdf: FPDF, company_name: str, basis: ReportBasis, generated: datetime):
    pdf.add_page()
    _page_header(pdf, "Report Sign-off")
    _section_title(pdf, "Report Sign-off")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*DARK_TEXT)
    lines = [
        f"Prepared by: {basis.prepared_by or NOT_RECORDED}",
        f"Reviewed by: {basis.reviewed_by or NOT_RECORDED}",
        *_basis_lines(basis, generated),
        "",
        "This version is a draft until it is issued. The issued version, and who issued it, are recorded in the report version history.",
        "Names are recorded as entered by the consultant; they are not verified sign-ins.",
    ]
    for line in lines:
        pdf.set_x(PM)
        pdf.multi_cell(CW, 5, text=S(line), new_x="LMARGIN")
    _page_footer(pdf, company_name)


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
    sq_size = 4.5
    gap = 1
    for index, item in enumerate(items):
        r, g, b = STATUS_COLORS.get(item.compliance_status, (189, 195, 199))
        pdf.set_fill_color(r, g, b)
        pdf.rect(
            x + 62 + (index % HEATMAP_SQUARES_PER_LINE) * (sq_size + gap),
            y + (index // HEATMAP_SQUARES_PER_LINE) * (sq_size + gap),
            sq_size,
            sq_size,
            style="F",
        )

    # Score
    pdf.set_font("Helvetica", "B", 9)
    r, g, b = _rating_color(rating)
    pdf.set_text_color(r, g, b)
    pdf.text(x + CW - 22, y + 4, S(f"{score:.0f}%"))

    # Rating text
    pdf.set_font("Helvetica", "", 7)
    pdf.text(x + CW - 22, y + 8, S(rating[:25]))
    return heatmap_row_height(len(items))


def _render_remediation_actions(pdf: FPDF, company_name: str, report_findings, gap_items):
    actions = []
    finding_keys = set()
    if report_findings is not None:
        for finding in report_findings.findings:
            finding_keys.add((finding.framework_id or "dpdpa", finding.requirement_id))
            for action in finding.actions:
                actions.append((finding, action))
    severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    actions.sort(
        key=lambda pair: (
            pair[1].target_date is None,
            pair[1].target_date,
            severity_rank.get(pair[0].severity, 3),
        )
    )

    _section_title(pdf, "Remediation Actions")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*MID_TEXT)
    pdf.set_x(PM)
    pdf.multi_cell(
        CW,
        4,
        text=S(
            "Actions recorded against approved findings, ordered by target date. "
            "Owners and dates are set by the consultant; nothing on this page is estimated."
        ),
        new_x="LMARGIN",
    )
    pdf.ln(2)

    if not actions:
        pdf.set_x(PM)
        pdf.multi_cell(
            CW,
            4,
            text=S("No remediation actions are recorded for the approved findings yet."),
            new_x="LMARGIN",
        )
    else:
        for finding, action in actions:
            if pdf.get_y() > CONTENT_BOTTOM - 16:
                _page_footer(pdf, company_name)
                pdf.add_page()
                _page_header(pdf, "Remediation Roadmap (continued)")
            pdf.set_font("Helvetica", "B", 8.5)
            pdf.set_text_color(*DARK_TEXT)
            pdf.set_x(PM)
            pdf.multi_cell(CW, 4, text=S(action.title), new_x="LMARGIN")
            target = (
                action.target_date.strftime("%d %b %Y")
                if action.target_date is not None
                else "No target date"
            )
            pdf.set_font("Helvetica", "", 8.5)
            pdf.set_text_color(*MID_TEXT)
            pdf.set_x(PM)
            pdf.multi_cell(
                CW,
                4,
                text=S(
                    f"Owner: {action.owner or 'Unassigned'}  |  Target: {target}  |  "
                    f"{action.status_label}"
                ),
                new_x="LMARGIN",
            )
            pdf.set_x(PM)
            pdf.multi_cell(
                CW,
                4,
                text=S(
                    f"Closes: {finding.framework_name} {finding.requirement_id} - {finding.title}"
                ),
                new_x="LMARGIN",
            )
            pdf.ln(2)

    unplanned = sum(
        item.compliance_status in GAP_STATUSES
        and (item.framework_id or "dpdpa", item.requirement_id) not in finding_keys
        for item in gap_items
    )
    if unplanned:
        if pdf.get_y() > CONTENT_BOTTOM - 10:
            _page_footer(pdf, company_name)
            pdf.add_page()
            _page_header(pdf, "Remediation Roadmap (continued)")
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(*MID_TEXT)
        pdf.set_x(PM)
        pdf.multi_cell(
            CW,
            4,
            text=S(
                f"{unplanned} identified gap(s) have no approved finding with an action yet."
            ),
            new_x="LMARGIN",
        )


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
    basis = basis_for(assessment)
    generated = datetime.now(timezone.utc)
    dpdpa_only = selected_frameworks == ["dpdpa"]

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

    gap_count = count_gaps(gap_items)

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

    # Report basis and render date
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(180, 180, 210)
    pdf.text(
        PM,
        46.5,
        S(f"Assessment period: {basis.period_label}  |  Evidence cut-off: {basis.cutoff_label}"),
    )
    pdf.set_font("Helvetica", "", 8)
    pdf.text(PM, 52, S(f"Report generated: {generated:%d %b %Y}"))

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
        f"{total} requirements assessed  |  {gap_count} gaps identified "
        f"({critical_count + high_count} critical or high)"
    )
    tw = pdf.get_string_width(summary_text)
    pdf.text((PW - tw) / 2, 182, S(summary_text))

    # Bottom section: chapter score preview bars
    bar_y = 202
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*NAVY)
    pdf.text(PM, bar_y - 5, "Assessment Areas")

    area_rows = list(chapter_scores.items())
    for chapter_key, scores in area_rows[:COVER_AREA_ROWS - 1 if len(area_rows) > COVER_AREA_ROWS else COVER_AREA_ROWS]:
        _draw_h_bar(pdf, PM, bar_y, CW, 8, scores["score"], scores["title"], scores["rating"])
        bar_y += 11
    if len(area_rows) > COVER_AREA_ROWS:
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(*MID_TEXT)
        pdf.text(
            PM,
            bar_y + 4,
            S(
                f"+{len(area_rows) - (COVER_AREA_ROWS - 1)} more assessment areas "
                "on the Executive Dashboard"
            ),
        )

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
        str(counts.get("insufficient_evidence", 0)),
        "Insufficient Evidence",
        STATUS_COLORS["insufficient_evidence"],
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
            pdf.set_xy(PM, framework_bar_y - 3)
            pdf.multi_cell(CW, 4, text=S(coverage_text), new_x="LMARGIN")
            framework_bar_y = pdf.get_y() + 4
        elif scores.get("status") == "not_scored":
            pdf.set_xy(PM, framework_bar_y - 3)
            pdf.multi_cell(
                CW,
                4,
                text=S(
                    f"{framework_name}: not scored. No in-scope requirement has a scoring outcome."
                ),
                new_x="LMARGIN",
            )
            framework_bar_y = pdf.get_y() + 4

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
        row_height = heatmap_row_height(len(items))
        if hm_y + row_height > CONTENT_BOTTOM:
            _page_footer(pdf, company_name)
            pdf.add_page()
            _page_header(pdf, "Executive Dashboard (continued)")
            hm_y = pdf.get_y()
        hm_y += _draw_heatmap_row(
            pdf, PM, hm_y, scores["title"], scores["score"], scores["rating"], items
        )

    # Executive summary (condensed)
    if hm_y + 8 > CONTENT_BOTTOM - 45:
        _page_footer(pdf, company_name)
        pdf.add_page()
        _page_header(pdf, "Executive Dashboard (continued)")
        hm_y = pdf.get_y()
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
    _render_remediation_actions(pdf, company_name, report_findings, gap_items)

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
    pdf.text(PM, 160, S(f"{total} requirements  |  {gap_count} gaps identified"))

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

    scope_as_of = generated

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

    scope_text = f"""{chr(10).join(_basis_lines(basis, generated))}

Nature of Assessment:
{_nature_text(selected_frameworks)}

Scope of Coverage:
{scope_of_coverage}

What Is Not Covered:
{not_covered_text}

Reliance on Disclosed Information:
All findings reflect the information provided to the assessor at the time of the assessment. The assessor has not independently verified the accuracy or completeness of information provided. Material omissions or inaccuracies in disclosed information would affect the reliability of findings.

Recommended Follow-On Actions:
{_follow_on_text(selected_frameworks)}

Confidentiality:
This report is prepared solely for the use of the named organization. It should not be shared with third parties without the organization's explicit consent. {settings.firm_name} and the named organization are the intended recipients of this report."""

    if dpdpa_readiness_note_applies(selected_frameworks, scope_as_of.date()):
        scope_text += f"\n\nRegulatory Commencement:\n{DPDPA_READINESS_NOTE}"

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
    pdf.set_x(PM)
    pdf.multi_cell(
        CW,
        4.5,
        text=S(methodology_text(selected_frameworks, len(gap_items))),
        new_x="LMARGIN",
    )

    _page_footer(pdf, company_name)

    _render_sign_off_page(pdf, company_name, basis, generated)

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
    pdf.text(PM, 29, S("Integrated Engagement Report"))
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(180, 180, 210)
    report_as_of = datetime.now(timezone.utc)
    pdf.text(PM, 42, S(f"Report generated: {report_as_of:%d %b %Y}"))
    dpdpa_framework = FrameworkRegistry.get_or_none("dpdpa")
    dpdpa_name = dpdpa_framework.name if dpdpa_framework else "DPDPA"
    integrated_ids = []
    for section in report_data.sections:
        for framework_id in getattr(section, "framework_ids", ()):
            if framework_id not in integrated_ids:
                integrated_ids.append(framework_id)

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

    # ===================================================================
    # SCOPE & LIMITATIONS
    # ===================================================================
    pdf.add_page()
    _page_header(pdf, "Scope & Limitations")
    _section_title(pdf, "Scope & Limitations")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*DARK_TEXT)
    for section in report_data.sections:
        section_basis = getattr(section, "basis", None) or EMPTY_BASIS
        framework_names = ", ".join(name for name, _version in section.frameworks)
        pdf.set_x(PM)
        pdf.multi_cell(
            CW,
            4,
            text=S(
                f"{section.label}: {framework_names}; assessment period "
                f"{section_basis.period_label}; evidence cut-off {section_basis.cutoff_label}; "
                f"{section.scope_label}."
            ),
            new_x="LMARGIN",
        )
    pdf.ln(2)
    integrated_scope = "\n".join(
        [
            f"Report generated: {report_as_of:%d %b %Y}",
            "",
            "Nature of Assessment:",
            _nature_text(integrated_ids),
            "",
            "What Is Not Covered:",
            "This assessment does not include technical penetration testing, source code review, network security assessment, or any form of independent technical verification. Findings in areas where the organization provided limited or no evidence are based on stated intent and disclosed posture only.",
            "",
            "Recommended Follow-On Actions:",
            _follow_on_text(integrated_ids),
            "",
            "Confidentiality:",
            f"This report is prepared solely for the use of the named organization. It should not be shared with third parties without the organization's explicit consent. {settings.firm_name} and the named organization are the intended recipients of this report.",
        ]
    )
    pdf.set_x(PM)
    pdf.multi_cell(CW, 4.5, text=S(integrated_scope), new_x="LMARGIN")
    _page_footer(pdf, report_data.client_name)

    for section in report_data.sections:
        pdf.add_page()
        _page_header(pdf, f"Assessment: {section.label}")
        _section_title(pdf, section.label)
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(*DARK_TEXT)
        section_basis = getattr(section, "basis", None) or EMPTY_BASIS
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
        ]
        if section_basis.period_recorded:
            scope_lines.extend(
                [
                    f"Assessment period: {section_basis.period_label}",
                    f"Evidence cut-off: {section_basis.cutoff_label}",
                ]
            )
        else:
            scope_lines.append("Assessment period and evidence cut-off: not recorded")
        scope_lines.append(
            f"Prepared by: {section_basis.prepared_by or 'not recorded'}  |  "
            f"Reviewed by: {section_basis.reviewed_by or 'not recorded'}"
        )
        for line in scope_lines:
            pdf.set_x(PM)
            pdf.multi_cell(CW, 4, text=S(line), new_x="LMARGIN")
        if dpdpa_name in {name for name, _version in section.frameworks} and (
            dpdpa_readiness_note_applies(["dpdpa"], report_as_of.date())
        ):
            pdf.ln(1)
            pdf.set_x(PM)
            pdf.multi_cell(CW, 4, text=S(DPDPA_READINESS_NOTE), new_x="LMARGIN")
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
                text=S("Scores unavailable for this assessment."),
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

    # ===================================================================
    # FINAL PAGE: METHODOLOGY
    # ===================================================================
    pdf.add_page()
    _page_header(pdf, "Methodology")
    _section_title(pdf, "Assessment Methodology")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*DARK_TEXT)
    pdf.set_x(PM)
    pdf.multi_cell(CW, 4.5, text=S(methodology_text(integrated_ids, None)), new_x="LMARGIN")
    _page_footer(pdf, report_data.client_name)

    return bytes(pdf.output())
