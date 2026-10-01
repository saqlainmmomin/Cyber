"""Render the 16:9 board-deck mockup (PDF via WeasyPrint) from deck_document.json.

`view(doc)` is the prototype of the implementation's pure presenter
(board_view.py): it only reads the stored document and computes geometry,
pagination and labels. Theme tokens stand in for the firm-configurable brand.
"""
import json
import math
import sys
from datetime import date
from pathlib import Path

import jinja2
from markupsafe import Markup

WT = Path("/Users/saqlainmomin/cyberassess-report-format")
sys.path.insert(0, str(WT))
from app.utils import html_pdf  # noqa: E402

HERE = Path(__file__).parent
THEME = {  # firm-configurable in the real product: primary, secondary, accent (+ logo)
    "p1": "#161A5C", "p2": "#2D3FD3", "p3": "#3FA9F5", "acc": "#12B3A6",
}
SEV = ["critical", "high", "medium", "low"]
SEV_COL = {"critical": "#9B1C1C", "high": "#D9481E", "medium": "#F0A030", "low": "#3C9D6B"}
OUT = [("compliant", "Compliant", "#2F9466"), ("partially_compliant", "Partially compliant", "#F0A030"),
       ("non_compliant", "Non-compliant", "#C0392B"), ("insufficient_evidence", "Insufficient evidence", "#9AA3B5"),
       ("not_applicable", "Not applicable", "#D5D9E3")]
RATING_COL = {"Compliant": "#2F9466", "Partially Compliant": "#E0941F", "Needs Significant Improvement": "#D9481E", "Non-Compliant": "#C0392B"}
LEVEL = {"high": 3, "medium": 2, "low": 1}


def d(v):
    return date.fromisoformat(str(v)[:10]).strftime("%d %b %Y") if v else None


def ring(values, r=17, w=5.2):
    """values: [(n, colour)] -> list of SVG arc dicts (stroke-dasharray on circles), units mm."""
    total = sum(n for n, _ in values) or 1
    c = 2 * math.pi * r
    out, off = [], 0.0
    for n, col in values:
        ln = c * n / total
        out.append({"col": col, "dash": f"{ln:.2f} {c - ln:.2f}", "off": f"{-off:.2f}"})
        off += ln
    return {"r": r, "w": w, "c": c, "arcs": out, "size": 2 * (r + w)}


def chunks(seq, n):
    return [seq[i:i + n] for i in range(0, len(seq), n)]


def view(doc):
    prior = {p["framework_id"]: p for p in doc["prior_period"]["frameworks"]}
    t = doc["summary"]["totals"]
    outcome_tot = {k: sum(f["coverage"][k] for f in doc["summary"]["frameworks"]) for k, _, _ in OUT}
    fw = []
    for f in doc["summary"]["frameworks"]:
        cov = f["coverage"]
        tot = sum(cov[k] for k, _, _ in OUT)
        p = prior.get(f["framework_id"])
        fw.append({**f, "rating_col": RATING_COL.get(f["rating"], "#9AA3B5"),
                   "delta": p["score_delta"] if p else None, "prior": p["prior_score"] if p else None,
                   "segs": [{"n": cov[k], "pct": 100 * cov[k] / tot, "col": c, "label": lbl} for k, lbl, c in OUT if cov[k]],
                   "gaps": cov["partially_compliant"] + cov["non_compliant"]})
    # roadmap placement (mm, inside a 300 x 118 area)
    cols = {"short": (22, 72), "medium": (98, 92), "long": (196, 88)}
    base = {"short": 24, "medium": 34, "long": 12}
    placed, seen = [], {"short": 0, "medium": 0, "long": 0}
    for i in doc["initiatives"]:
        h = i["horizon"] if i["horizon"] != "unscheduled" else "long"
        k = seen[h]
        seen[h] += 1
        x0, w = cols[h]
        placed.append({**i, "x": x0 + (5 if k % 2 else 0), "y": base[h] + k * 23, "w": w - 6})
    # severity dashboard
    dash = []
    for s in SEV:
        dd = doc["severity_dashboard"][s]
        mx = max([n for _, n in dd["top"]] or [1])
        dash.append({"sev": s, "total": dd["total"], "col": SEV_COL[s],
                     "ring": ring([(dd["total"], SEV_COL[s]), (max(t["gaps"] - dd["total"], 0), "#E3E6EE")], r=13, w=4),
                     "bars": [{"label": lbl, "n": n, "pct": 100 * n / mx} for lbl, n in dd["top"]]})
    sev_ring = ring([(sum(1 for o in doc["observations"] if o["rating"] == s), SEV_COL[s]) for s in SEV], r=20, w=7)
    gap_sev = {s: sum(doc["summary"]["risk_matrix"][f][s] for f in doc["summary"]["risk_matrix"]) for s in SEV}
    gap_ring = ring([(gap_sev[s], SEV_COL[s]) for s in SEV], r=22, w=8)
    soa_cols = ["Implemented", "Partially implemented", "Not implemented", "Not determined", "Not applicable", "Not assessed"]
    themes = {}
    for r in doc["soa"]["rows"]:
        themes.setdefault(r["theme"], {c: 0 for c in soa_cols})[r["implementation_label"]] += 1
    reg_pages = chunks(doc["appendices"]["requirement_register"], 21)
    obs_pages = chunks(doc["observations"], 4)
    deck_pages = 3 + 1 + 4 + len(obs_pages) + 2 + 3 + 1 + 1 + len(reg_pages) + 1
    return {
        "theme": THEME, "fw": fw, "t": t, "outcome_ring": ring([(outcome_tot[k], c) for k, _, c in OUT], r=24, w=8.5),
        "outcomes": [{"k": k, "label": lbl, "col": c, "n": outcome_tot[k]} for k, lbl, c in OUT],
        "dash": dash, "sev_ring": sev_ring, "gap_ring": gap_ring, "gap_sev": gap_sev, "sev_col": SEV_COL,
        "placed": placed, "obs_pages": obs_pages, "reg_pages": reg_pages, "level": LEVEL,
        "soa_cols": soa_cols, "soa_themes": themes, "deck_pages": deck_pages,
        "docs_reviewed": len(doc["appendices"]["evidence_register"]),
    }


def render(doc, embed_fonts=True):
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(HERE), autoescape=True)
    env.filters["d"] = d
    env.filters["cap"] = lambda s: (s or "").replace("_", " ").capitalize()
    display = (f"@font-face {{ font-family: 'Display'; src: url('file://{HERE}/fonts/BarlowCondensed-Bold.ttf'); font-weight: 700; }}"
               f"@font-face {{ font-family: 'Display'; src: url('file://{HERE}/fonts/BarlowCondensed-SemiBold.ttf'); font-weight: 600; }}")
    return env.get_template("deck_template.html").render(
        doc=doc, v=view(doc),
        font_face_css=Markup((html_pdf.font_face_css() if embed_fonts else "") + display),
        font_stack=Markup(html_pdf.FONT_STACK + ", 'Helvetica Neue', Arial, sans-serif"))


if __name__ == "__main__":
    doc = json.loads((HERE / "deck_document.json").read_text())
    html = render(doc)
    (HERE / "deck.html").write_text(html)
    from weasyprint import HTML
    HTML(string=html, base_url=str(WT / "app" / "assets" / "fonts" / "noto") + "/").write_pdf(HERE / "deck.pdf")
    print("ok")
