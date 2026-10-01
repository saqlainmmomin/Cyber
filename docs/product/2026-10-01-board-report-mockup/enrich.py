"""Add the deck-format (v3) fields to the rich synthetic document.

NEW consultant-entered data (synthetic here): Finding.recommendation,
Action.responsibility, Initiative complexity/benefit. Everything else below is
DERIVED deterministically from the document (+ the UCC cluster index).
"""
import json
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

WT = Path("/Users/saqlainmomin/cyberassess-report-format")
sys.path.insert(0, str(WT))
from app.main import _register_frameworks  # noqa: E402

_register_frameworks()
from app.frameworks.registry import FrameworkRegistry as R  # noqa: E402
from app.services.remediation_groups import cluster_index  # noqa: E402

HERE = Path(__file__).parent
doc = json.loads((HERE / "rich_document.json").read_text())
GEN = date.fromisoformat(doc["snapshot"]["generated_at"][:10])
SHORT = {"dpdpa": "DPDPA", "iso27001": "ISO 27001"}
IN_SCOPE = [f["framework_id"] for f in doc["frameworks"]]

ref_of = {}
for fid in IN_SCOPE:
    for dom in R.get(fid).as_legacy_framework_dict().values():
        secs = dom["sections"].values() if isinstance(dom["sections"], dict) else dom["sections"]
        for s in secs:
            for req in s["requirements"]:
                ref_of[(fid, req["id"])] = req.get("section_ref") or req["id"]
idx = cluster_index()
members = defaultdict(list)
for key, (cid, _topic) in idx.items():
    members[cid].append(key)


def references(fid, rid):
    """Own clause + same-cluster clauses in in-scope frameworks (UCC), grouped per framework."""
    keys = [(fid, rid)]
    c = idx.get((fid, rid))
    if c:
        keys += [k for k in members[c[0]] if k[0] in IN_SCOPE and k != (fid, rid)]
    out = defaultdict(list)
    for f, r in keys:
        out[f].append(ref_of.get((f, r), r))
    return [{"framework": SHORT[f], "clauses": list(dict.fromkeys(v))[:4]} for f, v in sorted(out.items(), key=lambda kv: IN_SCOPE.index(kv[0]))]


RECO = {
    "CH2.CONSENT.1": "Replace pre-selected consent with an unticked, purpose-specific opt-in on every channel. Log each consent with the notice version shown, timestamp and channel, and re-collect consent for the existing marketing base before relying on it.",
    "BN.NOTIFY.1": "Extend the incident response plan with a notification runbook: named decision owner, 72-hour clock, Board and data-principal templates, and an evidence log. Test it in a tabletop exercise each year.",
    "ISO.A5.18": "Run quarterly access recertification for production and customer-data systems with manager sign-off. Disable leaver accounts within 24 hours through an HR-triggered workflow and keep review evidence.",
    "ISO.A8.8": "Adopt patch SLAs by severity (critical 15 days, high 30 days), scan internet-facing assets weekly, and report open critical vulnerabilities to the risk committee monthly.",
    "CH2.SECURITY.2": "Define role-based access profiles for the customer database, remove standing engineer access, and route exceptions through time-bound, approved break-glass access with session logging.",
    "CH2.SECURITY.3": "Issue a data-processing addendum covering security, breach notice within 24 hours, sub-processing, audit rights and deletion at exit, and track signature to completion.",
    "ISO.A5.19": "Tier suppliers by data access, assess tier-1 suppliers before onboarding and annually, and record the risk decision in the supplier register.",
    "CH2.MINIMIZE.2": "Set retention periods for customer and KYC data by purpose and legal basis, and automate deletion or anonymisation at expiry with a monthly exception report.",
    "ISO.A5.30": "Test the BCP for the payments platform against target recovery times, record the results and fix gaps found before the next test cycle.",
    "CH3.GRIEVANCE.1": "Publish a grievance form with ticket tracking and a 30-day response commitment, and report volumes and ageing to the DPO monthly.",
}
RESP = {"CH2.CONSENT.1": "client", "BN.NOTIFY.1": "shared", "ISO.A5.18": "client", "ISO.A8.8": "client",
        "CH2.SECURITY.2": "client", "CH2.SECURITY.3": "shared", "ISO.A5.19": "client",
        "CH2.MINIMIZE.2": "client", "ISO.A5.30": "client", "CH3.GRIEVANCE.1": "consultant"}
INIT = {  # topic -> (initiative title, complexity, benefit) — consultant-entered
    "Access control and privileged access": ("Establish role-based access and quarterly recertification", "high", "high"),
    "Incident and breach response": ("Stand up regulator-ready breach notification", "medium", "high"),
    "Vulnerability and patch management": ("Introduce risk-based patch SLAs with board reporting", "medium", "high"),
    "Consent and notice": ("Rebuild consent capture with versioned notices", "high", "high"),
    "Third-party and processor security": ("Contract and assess processors and suppliers", "medium", "medium"),
    "Data retention and deletion": ("Automate retention and deletion for customer data", "high", "medium"),
    "Business continuity": ("Test continuity for the payments platform", "medium", "medium"),
    "Data-principal rights and grievances": ("Track grievances against a published timeline", "low", "medium"),
}
PRIO_OF_SEV = {"critical": "high", "high": "high", "medium": "medium", "low": "low"}

# --- observations (R-xx), ordered as top risks ---
fw_of_name = {"India DPDPA": "dpdpa", "ISO 27001": "iso27001"}
domain_of = {(r["framework_id"], r["requirement_id"]): r["domain_title"].split(" — ")[-1] for r in doc["appendices"]["requirement_register"]}
obs = []
for r in doc["top_risks"]:
    rid = r["requirement_id"]
    obs.append({
        "ref": f"R-{r['rank']:02d}", "finding_id": r["finding_id"], "framework_name": r["framework_name"],
        "framework_short": SHORT[r["framework_id"]], "domain": domain_of[(r["framework_id"], rid)],
        "title": r["title"], "observation": r["description"], "risk": r["business_impact"],
        "rating": r["severity"], "recommendation": RECO[rid], "responsibility": RESP[rid],
        "requirement_id": rid, "references": references(r["framework_id"], rid),
    })
obs_ref = {(o["framework_short"], o["requirement_id"]): o["ref"] for o in obs}
doc["observations"] = obs


# --- initiatives (I-n) with actions (A-xx) ---
def horizon3(target):
    if not target:
        return "unscheduled"
    days = (date.fromisoformat(target) - GEN).days
    return "short" if days <= 90 else "medium" if days <= 180 else "long"


inits, a_no = [], 0
for i, g in enumerate(doc["roadmap"]["groups"], 1):
    title, cx, bn = INIT[g["topic"]]
    acts = []
    for a in g["actions"]:
        a_no += 1
        key = (SHORT[fw_of_name[a["framework_name"]]], a["requirement_id"])
        overdue = bool(a["target_date"] and date.fromisoformat(a["target_date"]) < GEN and a["status_label"] != "Done")
        acts.append({**a, "ref": f"A-{a_no:02d}", "obs_ref": obs_ref[key], "responsibility": RESP[a["requirement_id"]],
                     "overdue": overdue})
    resp = {a["responsibility"] for a in acts}
    inits.append({
        "ref": f"I-{i}", "title": title, "topic": g["topic"], "obs_refs": sorted({a["obs_ref"] for a in acts}),
        "frameworks": g["frameworks"], "cross_framework": g["cross_framework"],
        "horizon": horizon3(g["target_date"]), "target_date": g["target_date"],
        "overdue": any(a["overdue"] for a in acts),
        "priority": PRIO_OF_SEV[g["top_severity"]],  # derived from approved severity
        "complexity": cx, "benefit": bn,  # consultant-entered
        "responsibility": resp.pop() if len(resp) == 1 else "shared",
        "owner": next((a["owner"] for a in acts if a["owner"]), None), "actions": acts,
    })
doc["initiatives"] = inits

# --- domain status board (derived from the register) ---
board = []
for s in doc["framework_sections"]:
    fid = s["framework_id"]
    rows = []
    reg = [r for r in doc["appendices"]["requirement_register"] if r["framework_id"] == fid]
    for d in s["domains"]:
        dr = [r for r in reg if r["domain_title"].endswith(d["title"])]
        gaps = [r for r in dr if r["outcome"] in ("partially_compliant", "non_compliant")]
        sev = Counter(r["risk_level"] for r in gaps)
        rows.append({"title": d["title"], "in_scope": len(dr), "gaps": len(gaps),
                     "crit_high": sev["critical"] + sev["high"],
                     "ie": sum(r["outcome"] == "insufficient_evidence" for r in dr),
                     "score": d["score"], "rating": d["rating"]})
    board.append({"framework_id": fid, "name": s["name"], "version": s["version"], "score": s["score"],
                  "rating": s["rating"], "in_scope": len(reg), "domains": rows})
doc["status_board"] = board

# --- severity dashboard by domain (derived) ---
dash = {}
for sev in ("critical", "high", "medium", "low"):
    c = Counter()
    for s in doc["framework_sections"]:
        for g in s["gaps"]:
            if g["risk_level"] == sev:
                c[f"{SHORT[s['framework_id']]} · {g['domain_title']}"] += 1
    dash[sev] = {"total": sum(c.values()), "top": c.most_common(4)}
doc["severity_dashboard"] = dash

# --- deterministic slide takeaways ---
t = doc["summary"]["totals"]
clean = sum(1 for b in board for d in b["domains"] if d["in_scope"] and d["gaps"] == 0)
scoped = sum(1 for b in board for d in b["domains"] if d["in_scope"])
doc["takeaways"] = {
    "status_board": f"{clean} of {scoped} in-scope domains have no approved gaps; the weakest are "
                    + " and ".join(f"{d['title']} ({d['score']:.0f}%)" for d in sorted((d for b in board for d in b["domains"] if d["score"] is not None), key=lambda d: d["score"])[:2]) + ".",
    "dashboard": f"{t['gaps']} approved gaps, {t['critical_high_gaps']} of them critical or high; "
                 f"{dash['critical']['total']} critical gaps sit in {len(dash['critical']['top'])} domains.",
    "roadmap": f"{len(inits)} initiatives close all {len(obs)} key observations; "
               f"{sum(i['cross_framework'] for i in inits)} of them fix a weakness once across both frameworks.",
}
def _r(ref):
    return f"R-{int(ref[1:]):02d}"
for sec in ("executive", "cross_framework"):
    for snt in doc["summary"]["narrative"][sec]:
        snt["finding_refs"] = [_r(x) for x in snt["finding_refs"]]
for f in doc["summary"]["frameworks"]:
    for snt in f["narrative"] or []:
        snt["finding_refs"] = [_r(x) for x in snt["finding_refs"]]
(HERE / "deck_document.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False))
print(doc["takeaways"])
print(obs[0]["references"], obs[3]["references"])
print([(i["ref"], i["horizon"], i["priority"], i["obs_refs"]) for i in inits])
