"""V3-C design pass: re-render the 16:9 board-deck mockup to the research-driven changes.

Reads the approved 1 Oct mockup document (`../2026-10-01-board-report-mockup/deck_document.json`)
and renders deck.pdf plus page PNGs. `view(doc)` is the prototype of the presenter: it only
reads the stored document and derives geometry, labels and the action titles; no LLM text is
added. The one field the stored v3 document does not have is per-domain prior scores, needed
by the dumbbell; MOCK_PRIOR_DOMAINS stands in for it and the slide is tagged as mockup data.

    .venv/bin/python docs/product/2026-10-04-board-deck-v3c-mockup/render_deck.py [--sparse]
"""
import copy
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import jinja2
from markupsafe import Markup

HERE = Path(__file__).parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO))
from app.utils import html_pdf  # noqa: E402

SOURCE_DOC = HERE.parent / "2026-10-01-board-report-mockup" / "deck_document.json"
FONTS = REPO / "app" / "assets" / "fonts" / "noto"
THEME = {"p1": "#161A5C", "p2": "#2D3FD3", "p3": "#3FA9F5", "acc": "#12B3A6"}

# Status palettes, validated with the dataviz validator (light, all pairs): outcomes
# worst CVD dE 12.1 (deutan), severities 8.5. Amber is below 3:1 so it always carries a label.
OUT = [("compliant", "Compliant", "#0E8F86"), ("partially_compliant", "Partially compliant", "#E39A1F"),
       ("non_compliant", "Non-compliant", "#C0392B"), ("insufficient_evidence", "Not concluded", "#9AA3B5"),
       ("not_applicable", "Not applicable", "#D5D9E3")]
OUT_COL = {k: c for k, _, c in OUT}
SEV = ["critical", "high", "medium", "low"]
SEV_COL = {"critical": "#9B1C1C", "high": "#D9481E", "medium": "#F0A030", "low": "#3C9D6B"}
BANDS = [(0, 40, "Non-compliant", "#CDD2DE"), (40, 60, "Needs significant improvement", "#DCE0E9"),
         (60, 80, "Partially compliant", "#E9ECF2"), (80, 100, "Compliant", "#F5F6F9")]
RATING_COL = {"Compliant": "#0E8F86", "Partially Compliant": "#E39A1F",
              "Needs Significant Improvement": "#D9481E", "Non-Compliant": "#C0392B"}
LEVEL = {"high": 3, "medium": 2, "low": 1}
HORIZONS = [("short", "Short term", "within 90 days"), ("medium", "Medium term", "91 to 180 days"),
            ("long", "Long term", "after 180 days"), ("unscheduled", "Not scheduled", "no target date")]
LANES = [("client", "Client"), ("shared", "Shared"), ("consultant", "Firm")]
# Mockup-only stand-in for per-domain prior scores (a new field: the prior snapshot's domain scores).
MOCK_PRIOR_DOMAINS = {
    "dpdpa": {"Obligations of Data Fiduciary": 31.0, "Rights of Data Principal": 38.0, "Special Provisions": 52.0,
              "Consent Management (Detailed)": 62.5, "Cross-Border Data Transfer": 100.0, "Breach Notification": 12.5},
    "iso27001": {"Organizational Controls": 54.1, "People Controls": 62.0, "Technological Controls": 60.2},
}


def d(v):
    return date.fromisoformat(str(v)[:10]).strftime("%d %b %Y") if v else None


def pct(n, of):
    return round(100 * n / of) if of else 0


def plural(n, one, many=None):
    return f"{n} {one if n == 1 else (many or one + 's')}"


def waffle(cov):
    """One cell per in-scope requirement, column-major, 10 per column, ordered by outcome."""
    cells = [c for k, _, c in OUT for _ in range(cov[k])]
    return [{"col": c, "x": i // 10, "y": i % 10} for i, c in enumerate(cells)], (len(cells) + 9) // 10


def view(doc, sparse=False):
    t = doc["summary"]["totals"]
    prior = {p["framework_id"]: p for p in doc["prior_period"].get("frameworks", []) if p.get("compared")}
    board = {b["framework_id"]: b for b in doc["status_board"]}
    short = {"dpdpa": "DPDPA", "iso27001": "ISO 27001"}

    fw = []
    for f in doc["summary"]["frameworks"]:
        cov = f["coverage"]
        cells, ncols = waffle(cov)
        p = prior.get(f["framework_id"])
        concluded = cov["compliant"] + cov["partially_compliant"] + cov["non_compliant"]
        doms = [dm for dm in board[f["framework_id"]]["domains"]]
        live = sorted([dm for dm in doms if dm["in_scope"]], key=lambda dm: dm["score"])
        fw.append({**f, "short": short.get(f["framework_id"], f["name"]), "cells": cells, "ncols": ncols,
                   "rating_col": RATING_COL.get(f["rating"], "#9AA3B5"), "concluded": concluded,
                   "prior": p, "delta": p["score_delta"] if p else None,
                   "outcomes": [{"k": k, "label": lbl, "col": c, "n": cov[k], "pct": pct(cov[k], cov["in_scope"])}
                                for k, lbl, c in OUT],
                   "gaps": cov["partially_compliant"] + cov["non_compliant"],
                   "domains": live, "out_domains": [dm for dm in doms if not dm["in_scope"]],
                   "sev": doc["summary"]["risk_matrix"][f["framework_id"]]})

    # ---- action titles: deterministic sentences computed from the document only ----
    below = [f for f in fw if f["rating"] != "Compliant"]
    exec_title = (f"{t['critical_high_gaps']} of {t['gaps']} gaps are critical or high, and "
                  + ("neither framework is yet rated Compliant" if len(below) == len(fw) == 2
                     else "no framework is yet rated Compliant" if len(below) == len(fw)
                     else f"{', '.join(f['short'] for f in below) or 'no framework'} is below Compliant"))
    met = sum(f["coverage"]["compliant"] for f in fw)
    concluded = sum(f["concluded"] for f in fw)
    posture_title = f"{met} of {concluded} concluded requirements are met; {t['gaps']} have gaps to close"
    all_doms = [(f["short"], dm) for f in fw for dm in f["domains"]]
    weakest = sorted(all_doms, key=lambda x: x[1]["score"])[:2]
    domain_title = " and ".join(f"{dm['title']} ({dm['score']:.0f}%)" for _, dm in weakest) + \
        (" are the weakest areas" if len(weakest) > 1 else " is the weakest area")
    by_ch = sorted(all_doms, key=lambda x: -x[1]["crit_high"])
    top_ch = by_ch[0] if by_ch and by_ch[0][1]["crit_high"] else None
    risk_title = (f"{top_ch[1]['title']} holds {top_ch[1]['crit_high']} of the {t['critical_high_gaps']} critical or high gaps"
                  if top_ch else f"No critical or high gaps; {plural(t['gaps'], 'gap')} remain")
    asks = doc["board_asks"]
    decision_title = (f"The board is asked to make {plural(len(asks['consultant']), 'decision')}; "
                      f"{plural(len(asks['derived']), 'item')} need management attention")

    inits = doc["initiatives"]
    n_short = sum(1 for i in inits if i["horizon"] == "short")
    n_over = sum(1 for i in inits if i["overdue"])
    roadmap_title = (f"{n_short} of {len(inits)} initiatives fall in the next 90 days"
                     + (f"; {n_over} {'is' if n_over == 1 else 'are'} already overdue" if n_over else ""))
    # effort-benefit matrix
    grid = {f"{c}-{b}": [] for c in ("low", "medium", "high") for b in ("low", "medium", "high")}
    for i in inits:
        grid[f'{i["complexity"]}-{i["benefit"]}'].append(i)
    hi_bn = [i for i in inits if i["benefit"] == "high"]
    hi_bn_low_cx = [i for i in hi_bn if i["complexity"] == "low"]
    matrix_title = (f"{plural(len(hi_bn_low_cx), 'quick win')} among {len(hi_bn)} high-benefit initiatives"
                    if hi_bn_low_cx else
                    f"No quick wins: all {len(hi_bn)} high-benefit initiatives need medium or high effort")
    lanes = [(k, lbl) for k, lbl in LANES if any(i["responsibility"] == k for i in inits)]
    horizons = [h for h in HORIZONS if h[0] != "unscheduled" or any(i["horizon"] == "unscheduled" for i in inits)]

    # dumbbell (per domain, prior vs current)
    dumb = []
    for f in fw:
        mock = MOCK_PRIOR_DOMAINS.get(f["framework_id"], {}) if f["prior"] else {}
        rows = [{"title": dm["title"], "now": dm["score"], "was": mock.get(dm["title"])} for dm in f["domains"]]
        dumb.append({"name": f["name"], "rows": sorted(rows, key=lambda r: r["now"])})
    since_title = (" and ".join(f"{f['short']} {'rose' if f['delta'] >= 0 else 'fell'} {abs(f['delta']):.0f} points"
                                for f in fw if f["prior"]) + " since the last report"
                   if prior else "No earlier report to compare with")

    nobs = {s: sum(1 for o in doc["observations"] if o["rating"] == s) for s in SEV}
    obs_title = (f"{len(doc['observations'])} key observations: "
                 + ", ".join(f"{n} {s}" for s, n in nobs.items() if n))
    sev_tot = {s: sum(f["sev"][s] for f in fw) for s in SEV}
    ch_doms = sorted([(f["short"], dm) for f in fw for dm in f["domains"] if dm["crit_high"]], key=lambda x: -x[1]["crit_high"])

    # Vertical rhythm: rows grow to use the body height when data is thin (body is ~133 mm tall).
    max_dom = max([len(f["domains"]) + len(f["out_domains"]) for f in fw] or [1])
    n_dumb = sum(len(g["rows"]) + 1 for g in dumb) or 1
    lay = {"dom_row": round(min(28.0, max(15.5, 108 / max_dom)), 1),
           "dumb_row": round(min(14.0 if prior else 28.0, max(9.6, 112 / n_dumb)), 1),
           "ch_row": round(min(15.0, max(11.0, 70 / max(len(ch_doms[:6]), 1))), 1),
           "ask_h": round(min(124.0, (128 - 4 * (len(asks["consultant"]) - 1)) / max(len(asks["consultant"]), 1)), 1),
           "fwcard": 27 if len(fw) > 1 else 40, "dom_bar": 70 if len(fw) > 1 else 200}
    obs = doc["observations"]
    n_obs_pages = max(1, -(-len(obs) // 3))  # at most 3 per page, spread evenly
    cuts = [round(k * len(obs) / n_obs_pages) for k in range(n_obs_pages + 1)]
    obs_pages = [obs[cuts[k]:cuts[k + 1]] for k in range(n_obs_pages)]
    reg_pages = [doc["appendices"]["requirement_register"][i:i + 14]
                 for i in range(0, len(doc["appendices"]["requirement_register"]), 14)]
    # page map (cover = 1)
    pg = {"read": 3, "overview": 4, "exec": 5, "obs": 10}
    pg["roadmap"] = pg["obs"] + len(obs_pages)
    pg["annex"] = pg["roadmap"] + 5
    return {
        "theme": THEME, "fw": fw, "t": t, "sev": SEV, "sev_col": SEV_COL, "sev_tot": sev_tot, "out": OUT,
        "out_col": OUT_COL, "bands": BANDS, "level": LEVEL, "ch_doms": ch_doms[:6],
        "titles": {"exec": exec_title, "posture": posture_title, "domain": domain_title, "risk": risk_title,
                   "decision": decision_title, "obs": obs_title, "roadmap": roadmap_title, "matrix": matrix_title, "since": since_title},
        "grid": grid, "lanes": lanes, "horizons": horizons, "dumb": dumb, "has_prior": bool(prior),
        "lay": lay, "obs_pages": obs_pages, "reg_pages": reg_pages, "pg": pg, "sparse": sparse,
        "met": met, "concluded": concluded, "docs_reviewed": len(doc["appendices"]["evidence_register"]),
        "source": f"Source: approved outcomes in report {doc['snapshot']['version_label']} "
                  f"(snapshot {doc['snapshot']['id'][:8]}), evidence cut-off {doc['basis']['cutoff_label']}.",
    }


def sparse_doc(doc):
    """A thin engagement: one framework, three findings, no prior period, nothing overdue."""
    s = copy.deepcopy(doc)
    keep = "iso27001"
    s["frameworks"] = [f for f in s["frameworks"] if f["framework_id"] == keep]
    s["framework_sections"] = [f for f in s["framework_sections"] if f["framework_id"] == keep]
    s["summary"]["frameworks"] = [f for f in s["summary"]["frameworks"] if f["framework_id"] == keep]
    s["summary"]["scope"] = [x for x in s["summary"]["scope"] if x.startswith("ISO")]
    s["summary"]["risk_matrix"] = {keep: s["summary"]["risk_matrix"][keep]}
    s["status_board"] = [b for b in s["status_board"] if b["framework_id"] == keep]
    cov = s["summary"]["frameworks"][0]["coverage"]
    s["summary"]["totals"] = {"requirements": cov["in_scope"], "gaps": cov["partially_compliant"] + cov["non_compliant"],
                              "critical_high_gaps": sum(s["summary"]["risk_matrix"][keep][k] for k in ("critical", "high")),
                              "insufficient_evidence": cov["insufficient_evidence"], "not_applicable": cov["not_applicable"]}
    s["observations"] = [o for o in s["observations"] if o["framework_short"] != "DPDPA"][:3]
    refs = {o["ref"] for o in s["observations"]}
    s["initiatives"] = [{**i, "overdue": False, "cross_framework": False, "frameworks": ["ISO 27001"],
                         "obs_refs": [r for r in i["obs_refs"] if r in refs]}
                        for i in s["initiatives"] if any(r in refs for r in i["obs_refs"])]
    s["roadmap"]["overdue_count"] = 0
    s["prior_period"] = {"status": "first_report", "frameworks": [], "changes": [], "prior": None}
    s["not_assessed"]["insufficient_evidence"] = [x for x in s["not_assessed"]["insufficient_evidence"] if x["framework_id"] == keep]
    s["appendices"]["requirement_register"] = [r for r in s["appendices"]["requirement_register"] if r["framework_id"] == keep]
    s["board_asks"]["derived"] = s["board_asks"]["derived"][2:]
    s["board_asks"]["consultant"] = s["board_asks"]["consultant"][1:]
    s["summary"]["narrative"]["executive"] = [{"text": "Access governance and vulnerability management are the two areas that need attention; most other controls operate as described.", "finding_refs": sorted(refs)}]
    return s


def render(doc, sparse=False):
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(HERE), autoescape=True)
    env.filters["d"] = d
    env.filters["cap"] = lambda s: (s or "").replace("_", " ").capitalize()
    display = "".join(f"@font-face {{ font-family: 'Display'; src: url('file://{FONTS}/BarlowCondensed-{w}.ttf'); font-weight: {n}; }}"
                      for w, n in (("Bold", 700), ("SemiBold", 600)))
    return env.get_template("deck_template.html").render(
        doc=doc, v=view(doc, sparse),
        font_face_css=Markup(html_pdf.font_face_css() + display),
        font_stack=Markup(html_pdf.FONT_STACK + ", 'Helvetica Neue', Arial, sans-serif"))


if __name__ == "__main__":
    from weasyprint import HTML
    sparse = "--sparse" in sys.argv
    doc = json.loads(SOURCE_DOC.read_text())
    if sparse:
        doc = sparse_doc(doc)
    name = "deck-sparse" if sparse else "deck"
    html = render(doc, sparse)
    (HERE / f"{name}.html").write_text(html)
    HTML(string=html, base_url=str(FONTS) + "/").write_pdf(HERE / f"{name}.pdf")
    png = HERE / "pages" / name
    png.mkdir(parents=True, exist_ok=True)
    for old in png.glob("*.png"):
        old.unlink()
    subprocess.run(["pdftoppm", "-png", "-r", "80", str(HERE / f"{name}.pdf"), str(png / "p")], check=True)
    print(name, "ok", len(list(png.glob("*.png"))), "pages")
