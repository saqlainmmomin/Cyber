"""Build a rich synthetic board-report document (schema v2 + proposed v3 fields).

Synthetic only: people/firm/company/basis come from the P6-8 test fixture
(tests/golden/p6_8_board_document.json); requirements are real registry IDs.
Outcomes are seeded-random plus hand-placed findings. No DB, no LLM.
"""
import copy
import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

WT = Path("/Users/saqlainmomin/cyberassess-report-format")
sys.path.insert(0, str(WT))
from app.main import _register_frameworks  # noqa: E402

_register_frameworks()
from app.frameworks.registry import FrameworkRegistry as R  # noqa: E402

OUT = Path(__file__).parent
golden = json.loads((WT / "tests/golden/p6_8_board_document.json").read_text())
GEN = date(2026, 9, 28)
rnd = random.Random(7)

LABEL = {"compliant": "Compliant", "partially_compliant": "Partially Compliant",
         "non_compliant": "Non-Compliant", "insufficient_evidence": "Insufficient Evidence",
         "not_applicable": "Not Applicable"}
POINTS = {"compliant": 100, "partially_compliant": 50, "non_compliant": 0}
GAP = ("partially_compliant", "non_compliant")
CRIT2RISK = {"critical": "critical", "high": "high", "medium": "medium", "low": "low"}
PRIO = {"critical": 1, "high": 2, "medium": 3, "low": 4}


def rating(score):
    if score is None:
        return None
    if score >= 80: return "Compliant"
    if score >= 60: return "Partially Compliant"
    if score >= 40: return "Needs Significant Improvement"
    return "Non-Compliant"


# ISO scope: Organizational + People + Technological controls; Physical out of scope.
ISO_OUT_OF_SCOPE_DOMAINS = {"physical"}
WEIGHTS = {
    "dpdpa": [("compliant", 34), ("partially_compliant", 30), ("non_compliant", 20),
              ("insufficient_evidence", 12), ("not_applicable", 4)],
    "iso27001": [("compliant", 52), ("partially_compliant", 25), ("non_compliant", 10),
                 ("insufficient_evidence", 7), ("not_applicable", 6)],
}

FINDINGS = [
    # fw, req, outcome, severity, title, description, business_impact, actions[(title, owner, target, status)], citation
    ("dpdpa", "CH2.CONSENT.1", "non_compliant", "critical",
     "Consent is collected through pre-ticked boxes",
     "The sign-up journey and the marketing preference centre both pre-select consent. No record links a consent to the notice the user saw.",
     "Consent obtained this way is unlikely to be valid, so processing that depends on it would lack a lawful basis once DPDPA obligations commence; this affects the full 2.1 million-customer marketing base.",
     [("Replace pre-ticked consent with an affirmative opt-in and log the notice version shown", "Anita Rao", "2026-11-30", "in_progress")],
     ("privacy-policy.pdf", 3, "s.4.2, p.6", "a3f19c0e7b21")),
    ("dpdpa", "BN.NOTIFY.1", "non_compliant", "critical",
     "No procedure to notify the Data Protection Board of a breach",
     "The incident response plan covers containment only. It names no owner, timeline or template for notifying the Board or affected individuals.",
     "A breach handled under the current plan would miss the statutory notification, which carries the highest penalty tier under the Act.",
     [("Adopt a breach-notification runbook with owner, 72-hour timeline and regulator templates", "Vikram Iyer", "2026-10-31", "in_progress"),
      ("Run a tabletop exercise covering Board and data-principal notification", "Vikram Iyer", "2027-01-31", "open")],
     ("incident-response-plan.docx", 2, "s.5, p.3", "77c1d02e9a40")),
    ("iso27001", "ISO.A5.18", "non_compliant", "critical",
     "Access rights are never reviewed",
     "No periodic review of user access is evidenced for production systems. 14 leaver accounts were still active at the cut-off.",
     "Former staff and over-privileged users can reach customer data, the most common root cause of insider and credential-based breaches.",
     [("Run quarterly access reviews for production and customer-data systems", "Vikram Iyer", "2026-09-15", "open")],
     ("access-review-export.xlsx", 1, "Sheet 'Leavers', rows 2-15", "4be0d6a91c33")),
    ("dpdpa", "CH2.SECURITY.2", "partially_compliant", "high",
     "Customer database access is not restricted by role",
     "Encryption at rest is in place, but 41 engineers hold read access to the customer database with no role-based restriction.",
     "Broad access raises the likelihood and scale of a personal-data breach and weakens the 'reasonable security safeguards' defence.",
     [("Introduce role-based access to the customer database", "Vikram Iyer", "2026-12-15", "open")],
     ("isms-manual.pdf", 4, "Annex B, p.22", "bb02f7a8d114")),
    ("iso27001", "ISO.A8.8", "non_compliant", "critical",
     "No defined cadence for patching technical vulnerabilities",
     "Scans run ad hoc; 23 critical CVEs older than 90 days were open on internet-facing hosts at the cut-off.",
     "Known, exploitable weaknesses on public systems are the leading entry point for ransomware.",
     [("Set patch SLAs (critical 15 days) and report monthly to the risk committee", None, "2026-11-15", "open")],
     ("vuln-scan-summary.pdf", 1, "p.2", "e81a2c44f0d9")),
    ("dpdpa", "CH2.SECURITY.3", "non_compliant", "high",
     "Data Processor contracts lack data-protection clauses",
     "Seven of nine processor contracts reviewed contain no security, breach-notice or deletion obligations.",
     "The company remains liable for its processors' failures with no contractual recourse or audit right.",
     [("Issue a data-processing addendum to all processors", "Anita Rao", "2027-02-28", "open")],
     ("vendor-contracts-index.xlsx", 2, "rows 3-11", "0cd4e5f6a7b8")),
    ("iso27001", "ISO.A5.19", "partially_compliant", "high",
     "Supplier security is not assessed before onboarding",
     "A supplier questionnaire exists but is not used; no supplier risk tiering is recorded.",
     "Third-party compromise cannot be anticipated or contracted against.",
     [("Tier suppliers by data access and assess tier-1 suppliers annually", "Anita Rao", "2027-02-28", "open")],
     None),
    ("dpdpa", "CH2.MINIMIZE.2", "partially_compliant", "high",
     "Customer data is retained indefinitely",
     "The retention policy sets periods for HR records only; customer and KYC data have no retention period or deletion job.",
     "Holding data beyond its purpose enlarges breach impact and conflicts with the storage-limitation duty.",
     [("Define retention periods for customer and KYC data and automate deletion", "Ravi Menon", "2027-03-31", "open")],
     ("data-retention-policy.pdf", 1, "s.3, p.2", "9d8e7f6a5b4c")),
    ("iso27001", "ISO.A5.30", "partially_compliant", "medium",
     "Business continuity plan has never been tested",
     "The BCP is approved but no test or exercise has been recorded since it was written in 2024.",
     "Recovery times for core platforms are unknown; an outage could exceed customer contractual commitments.",
     [("Test the BCP for the payments platform and record results", "Ravi Menon", "2027-03-31", "open")],
     ("bcp-2024.pdf", 1, "whole", "1a2b3c4d5e6f")),
    ("dpdpa", "CH3.GRIEVANCE.1", "partially_compliant", "medium",
     "Grievance channel has no response timeline",
     "Grievances are received through a shared mailbox with no tracking or response-time commitment.",
     "Unresolved complaints can be escalated to the Data Protection Board.",
     [("Publish a grievance form with tracking and a 30-day response commitment", None, None, "open")],
     None),
]
FINDING_KEYS = {(f[0], f[1]): f for f in FINDINGS}
OWNER_MAP = {"Anita Rao": "Anita Rao (DPO)", "Vikram Iyer": "Vikram Iyer (CISO)", "Ravi Menon": "Ravi Menon (COO)"}

# Unified-control groups (roadmap)
GROUPS = [
    ("Access control and privileged access", [("iso27001", "ISO.A5.18"), ("dpdpa", "CH2.SECURITY.2")]),
    ("Incident and breach response", [("dpdpa", "BN.NOTIFY.1")]),
    ("Third-party and processor security", [("dpdpa", "CH2.SECURITY.3"), ("iso27001", "ISO.A5.19")]),
    ("Consent and notice", [("dpdpa", "CH2.CONSENT.1")]),
    ("Vulnerability and patch management", [("iso27001", "ISO.A8.8")]),
    ("Data retention and deletion", [("dpdpa", "CH2.MINIMIZE.2")]),
    ("Business continuity", [("iso27001", "ISO.A5.30")]),
    ("Data-principal rights and grievances", [("dpdpa", "CH3.GRIEVANCE.1")]),
]

STATUS_LABEL = {"open": "Open", "in_progress": "In progress", "done": "Done"}


def build():
    doc = copy.deepcopy(golden)
    doc["schema_version"] = 3
    doc["snapshot"] = {"id": "5f2c9e1a-4d7b-4e2a-9c3f-0b1d2e3f4a5b", "version_label": "v2",
                       "generated_at": "2026-09-28T10:00:00+00:00", "generated_on": "28 Sep 2026"}
    doc["release"] = {"released_by": "Priya Sharma", "released_on": "27 Sep 2026"}
    doc["assessment_id"] = "a7c41e2d-0000-4000-8000-000000000042"
    fw_meta = {f["framework_id"]: f for f in doc["frameworks"]}

    register, summaries, sections = [], [], []
    soa_rows = []
    totals = dict(requirements=0, gaps=0, critical_high_gaps=0, insufficient_evidence=0, not_applicable=0)
    risk_matrix = {}
    for fid in ("dpdpa", "iso27001"):
        fw = R.get(fid)
        legacy = fw.as_legacy_framework_dict()
        cov = dict(awaiting=0, compliant=0, eligible=0, in_scope=0, insufficient_evidence=0, missing=0,
                   non_compliant=0, not_applicable=0, out_of_scope=0, partially_compliant=0, scored=0)
        dom_scores, gaps = [], []
        matrix = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        weighted, wsum = 0.0, 0.0
        for did, dom in legacy.items():
            secs = dom["sections"].values() if isinstance(dom["sections"], dict) else dom["sections"]
            sec_scores = []
            for sec in secs:
                pts = []
                for req in sec["requirements"]:
                    rid = req["id"]
                    in_scope = not (fid == "iso27001" and did in ISO_OUT_OF_SCOPE_DOMAINS)
                    if not in_scope:
                        cov["out_of_scope"] += 1
                        soa_rows.append(_soa_row(req, dom["title"], None))
                        continue
                    if (fid, rid) in FINDING_KEYS:
                        outcome = FINDING_KEYS[(fid, rid)][2]
                    else:
                        outcome = rnd.choices([w[0] for w in WEIGHTS[fid]], [w[1] for w in WEIGHTS[fid]])[0]
                        if outcome == "non_compliant" and req.get("criticality") == "critical":
                            outcome = "partially_compliant"
                    risk = CRIT2RISK.get(req.get("criticality"), "medium")
                    if (fid, rid) in FINDING_KEYS:
                        risk = FINDING_KEYS[(fid, rid)][3]
                    elif outcome == "compliant":
                        risk = "low"
                    elif outcome == "partially_compliant":
                        risk = {"critical": "high", "high": "medium"}.get(risk, "low")
                    elif outcome == "non_compliant":
                        risk = {"critical": "high"}.get(risk, risk)
                    cov["in_scope"] += 1
                    cov["eligible"] += 1
                    cov[outcome] += 1
                    if outcome in POINTS:
                        cov["scored"] += 1
                        pts.append(POINTS[outcome])
                    if outcome in GAP:
                        matrix[risk] += 1
                        gaps.append({"requirement_id": rid, "requirement_title": req["title"], "outcome": outcome,
                                     "outcome_label": LABEL[outcome], "risk_level": risk, "priority": PRIO[risk],
                                     "domain_title": dom["title"]})
                    f = FINDING_KEYS.get((fid, rid))
                    cit = f[8] if f else None
                    register.append({
                        "framework_id": fid, "requirement_id": rid, "requirement_title": req["title"],
                        "domain_title": f"{fw.name} — {dom['title']}", "outcome": outcome,
                        "outcome_label": LABEL[outcome], "risk_level": risk, "priority": PRIO[risk],
                        "decision_label": "Edited" if rnd.random() < 0.12 else "Approved",
                        "decided_by": "Priya Sharma", "decided_on": "2026-09-24",
                        "citation": f"{cit[0]} v{cit[1]}, {cit[2]}" if cit else (
                            f"{rnd.choice(['isms-manual.pdf v4', 'privacy-policy.pdf v3', 'questionnaire-response.pdf v1', 'access-control-policy.pdf v2'])}, p.{rnd.randint(2, 30)}"
                            if outcome != "insufficient_evidence" else None),
                        "citation_note": "No supporting citation" if outcome == "insufficient_evidence" else None,
                    })
                    if fid == "iso27001":
                        soa_rows.append(_soa_row(req, dom["title"], outcome))
                if pts:
                    sec_scores.append((sum(pts) / len(pts), sec.get("weight", 1)))
            if sec_scores:
                ds = sum(s * w for s, w in sec_scores) / sum(w for _, w in sec_scores)
                weighted += ds * dom["weight"]
                wsum += dom["weight"]
                dom_scores.append({"domain_id": did, "title": dom["title"], "score": round(ds, 1), "rating": rating(ds)})
            else:
                dom_scores.append({"domain_id": did, "title": dom["title"], "score": None, "rating": None,
                                   "scope_note": "Out of scope"})
        score = round(weighted / wsum, 1)
        ie = cov["insufficient_evidence"]
        summaries.append({
            "framework_id": fid, "name": fw.name, "status": "scored", "score": score, "rating": rating(score),
            "coverage": cov,
            "headline": f"{score:.0f}% ({rating(score)}); {ie} requirement(s) insufficient evidence",
            "narrative": None,
        })
        sections.append({"framework_id": fid, "name": fw.name, "version": fw.version, "status": "scored",
                         "score": score, "rating": rating(score), "domains": dom_scores,
                         "gaps": sorted(gaps, key=lambda g: (PRIO[g["risk_level"]], g["requirement_id"]))})
        risk_matrix[fid] = matrix
        totals["requirements"] += cov["in_scope"]
        totals["gaps"] += len(gaps)
        totals["critical_high_gaps"] += matrix["critical"] + matrix["high"]
        totals["insufficient_evidence"] += ie
        totals["not_applicable"] += cov["not_applicable"]

    doc["summary"]["frameworks"] = summaries
    doc["summary"]["totals"] = totals
    doc["summary"]["scope"] = [
        f"{s['name']}: {s['coverage']['in_scope']} requirements in scope" for s in summaries]
    doc["summary"]["scope"][1] += " (Physical Controls excluded: single cloud-hosted office)"
    doc["framework_sections"] = sections
    doc["appendices"]["requirement_register"] = register
    doc["appendices"]["methodology"] = golden["appendices"]["methodology"].replace(
        "across 5 in-scope requirements", f"across {totals['requirements']} in-scope requirements")

    # Findings -> top risks, roadmap
    fw_name = {"dpdpa": "India DPDPA", "iso27001": "ISO 27001"}
    reqtitle = {(r["framework_id"], r["requirement_id"]): r["requirement_title"] for r in register}
    sev_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    ordered = sorted(enumerate(FINDINGS), key=lambda p: (sev_rank[p[1][3]], PRIO[p[1][3]], p[0]))
    top, alias = [], {}
    for rank, (_, f) in enumerate(ordered, 1):
        fid, rid, outcome, sev, title, desc, impact, actions, cit = f
        alias[(fid, rid)] = f"F{rank}"
        a0 = actions[0]
        top.append({
            "rank": rank, "finding_id": f"fnd-{rank:03d}", "title": title, "description": desc,
            "business_impact": impact,  # NEW (v3)
            "severity": sev, "priority": PRIO[sev], "framework_id": fid, "framework_name": fw_name[fid],
            "requirement_id": rid, "requirement_title": reqtitle[(fid, rid)], "outcome_label": LABEL[outcome],
            "citations": ([{"filename": cit[0], "version_number": cit[1], "location_ref": cit[2],
                            "sha256_prefix": cit[3], "is_current": True}] if cit else []),
            "owner": OWNER_MAP.get(a0[1]) if a0[1] else None, "target_date": a0[2], "action_title": a0[0],
            "action_status_label": STATUS_LABEL[a0[3]],  # NEW (v3)
        })
    doc["top_risks"] = top
    for sec in sections:
        for g in sec["gaps"]:
            g["finding_ref"] = alias.get((sec["framework_id"], g["requirement_id"]))  # NEW (v3)

    actions_flat = []
    for f in FINDINGS:
        for a in f[7]:
            actions_flat.append({"title": a[0], "owner": OWNER_MAP.get(a[1]) if a[1] else None,
                                 "target_date": a[2], "status_label": STATUS_LABEL[a[3]],
                                 "closes": [{"framework_name": fw_name[f[0]], "requirement_id": f[1], "finding_title": f[4]}],
                                 "_sev": f[3], "_key": (f[0], f[1])})
    actions_flat.sort(key=lambda a: (a["target_date"] is None, a["target_date"] or "", sev_rank[a["_sev"]]))
    groups = []
    for i, (topic, keys) in enumerate(GROUPS, 1):
        g_actions = [a for a in actions_flat if a["_key"] in keys]
        fws = sorted({fw_name[k[0]] for k in keys})
        closes = [{"finding_title": FINDING_KEYS[k][4], "framework_id": k[0], "framework_name": fw_name[k[0]],
                   "requirement_id": k[1], "requirement_title": reqtitle[k], "severity": FINDING_KEYS[k][3],
                   "finding_ref": alias[k]} for k in keys]
        dates = [a["target_date"] for a in g_actions if a["target_date"]]
        groups.append({
            "group_id": f"CLUSTER_{i:03d}", "topic": topic, "cross_framework": len(fws) > 1,
            "frameworks": fws, "finding_count": len(keys),
            "headline": (f"Fix once, closes {len(keys)} findings across {' and '.join(fws)}" if len(fws) > 1
                         else f"Addresses {len(keys)} finding in {fws[0]}"),
            "target_date": min(dates) if dates else None,
            "actions": [{"title": a["title"], "owner": a["owner"], "target_date": a["target_date"],
                         "status_label": a["status_label"], "framework_name": a["closes"][0]["framework_name"],
                         "requirement_id": a["closes"][0]["requirement_id"],
                         "finding_title": a["closes"][0]["finding_title"]} for a in g_actions],
            "closes": closes,
            "top_severity": min((c["severity"] for c in closes), key=lambda s: sev_rank[s]),
        })
    groups.sort(key=lambda g: (g["target_date"] is None, g["target_date"] or ""))
    for a in actions_flat:
        del a["_sev"], a["_key"]
    # NEW (v3): deterministic horizon bucket per group, relative to generated date
    for g in groups:
        g["horizon"] = horizon(g["target_date"], g["actions"])
    doc["roadmap"] = {"actions": actions_flat, "unplanned_gap_count": totals["gaps"] - len(FINDINGS), "groups": groups}

    status_counts = {"Open": 0, "In progress": 0, "Done": 0}
    overdue = unassigned = undated = 0
    for a in actions_flat:
        status_counts[a["status_label"]] += 1
        if a["target_date"] and date.fromisoformat(a["target_date"]) < GEN and a["status_label"] != "Done":
            overdue += 1
        if not a["owner"]:
            unassigned += 1
        if not a["target_date"]:
            undated += 1
    doc["roadmap"]["status_counts"] = status_counts  # NEW (v3)
    doc["roadmap"]["overdue_count"] = overdue  # NEW (v3)

    # NEW (v3): deterministic risk matrix and board asks
    doc["summary"]["risk_matrix"] = risk_matrix
    derived = []
    crit_unassigned = sum(1 for g in groups for a in g["actions"] if not a["owner"] and g["top_severity"] in ("critical", "high"))
    if overdue:
        derived.append(f"{overdue} remediation action is past its target date (access reviews, due 15 Sep 2026).")
    if crit_unassigned:
        derived.append(f"{crit_unassigned} action(s) on critical or high findings have no owner.")
    if undated:
        derived.append(f"{undated} action has no target date.")
    if totals["insufficient_evidence"]:
        derived.append(f"{totals['insufficient_evidence']} requirements could not be concluded; 4 evidence requests are open.")
    doc["board_asks"] = {
        "derived": derived,
        "consultant": [
            "Approve funding for a consent-management platform before the May 2027 DPDPA commencement.",
            "Confirm the CISO as accountable owner for vulnerability management and set the patch SLA as a board-tracked KPI.",
        ],
        "consultant_by": "Priya Sharma",
    }

    # NEW (P6-10, folded into v3): accepted narrative
    doc["summary"]["narrative"] = {
        "executive": [
            {"text": "The organisation has a sound policy base, but several controls that protect customer data exist on paper only and are not operated.", "finding_refs": ["F3", "F5", "F7"]},
            {"text": "The most serious exposures are consent that is unlikely to be valid, no procedure for notifying the regulator of a breach, and access rights that are never reviewed.", "finding_refs": ["F1", "F2", "F3"]},
            {"text": "Most gaps are process gaps with clear owners, and closing access control and supplier security once addresses findings under both frameworks.", "finding_refs": ["F3", "F4", "F6", "F7"]},
        ],
        "cross_framework": [
            {"text": "Weak access governance appears under both DPDPA security safeguards and ISO 27001 access-rights controls.", "finding_refs": ["F3", "F4"]},
        ],
    }
    for s in summaries:
        s["narrative"] = (
            [{"text": "Consent, breach notification and processor contracts are the weakest areas; rights handling and notices are largely in place.", "finding_refs": ["F1", "F2", "F6"]}]
            if s["framework_id"] == "dpdpa" else
            [{"text": "Policies and organisational controls are mostly implemented; access reviews and vulnerability management are the material gaps.", "finding_refs": ["F3", "F5"]}]
        )

    # Not assessed + RFI
    doc["not_assessed"] = {
        "insufficient_evidence": [{"framework_id": r["framework_id"], "requirement_id": r["requirement_id"],
                                   "requirement_title": r["requirement_title"]}
                                  for r in register if r["outcome"] == "insufficient_evidence"],
        "rfi": {"version_label": "v2", "items": [
            {"item_id": "RFI-01", "title": "Consent records export for July 2026", "required": True},
            {"item_id": "RFI-02", "title": "Cross-border transfer register and destination list", "required": True},
            {"item_id": "RFI-03", "title": "DPIA for the loan-underwriting model", "required": True},
            {"item_id": "RFI-04", "title": "Last two backup-restore test reports", "required": False},
        ]},
    }

    # Evidence register
    files = [("access-control-policy.pdf", 2), ("access-review-export.xlsx", 1), ("bcp-2024.pdf", 1),
             ("data-retention-policy.pdf", 1), ("incident-response-plan.docx", 2), ("isms-manual.pdf", 4),
             ("privacy-policy.pdf", 3), ("questionnaire-response.pdf", 1), ("vendor-contracts-index.xlsx", 2),
             ("vuln-scan-summary.pdf", 1), ("board-minutes-q1.pdf", 1)]
    doc["appendices"]["evidence_register"] = [
        {"filename": n, "version_number": v, "sha256_prefix": f"{abs(hash(n)) % 16**12:012x}",
         "added_on": "2026-07-0" + str(1 + i % 9), "status": "active", "cited": n != "board-minutes-q1.pdf"}
        for i, (n, v) in enumerate(files)]

    # SoA
    soa = copy.deepcopy(golden["soa"])
    soa["rows"] = soa_rows
    t = dict(applicable=0, controls=len(soa_rows), excluded=0, implemented=0, justification_missing=0,
             not_assessed=0, not_determined=0, not_implemented=0, partially_implemented=0, pending=0)
    for r in soa_rows:
        t["applicable" if r["applicability"] == "applicable" else
          "excluded" if r["applicability"] == "excluded" else "not_assessed"] += 1
        impl = {"Implemented": "implemented", "Partially implemented": "partially_implemented",
                "Not implemented": "not_implemented", "Not determined": "not_determined"}.get(r["implementation_label"])
        if impl:
            t[impl] += 1
        if not r["justification"]:
            t["justification_missing"] += 1
    soa["totals"] = t
    soa["notes"] = [f"{t['not_assessed']} Annex A control(s) were outside the scope of this assessment. Their applicability has not been determined; the organization must decide it before relying on this statement.",
                    f"{t['justification_missing']} control(s) have no recorded justification."]
    doc["soa"] = soa

    # Prior period
    prior = {"dpdpa": 41.0, "iso27001": 58.5}
    doc["prior_period"] = {
        "status": "compared", "intro": golden["prior_period"]["intro"], "notes": [],
        "prior": {"version_label": "v3", "snapshot_id": "c0ffee12-aaaa-4bbb-8ccc-000000000001",
                  "period_label": "01 Oct 2025 to 31 Dec 2025", "cutoff_label": "15 Jan 2026", "generated_on": "02 Feb 2026"},
        "frameworks": [{"framework_id": s["framework_id"], "name": s["name"], "compared": True,
                        "prior_score": prior[s["framework_id"]], "current_score": s["score"],
                        "score_delta": round(s["score"] - prior[s["framework_id"]], 1),
                        "counts": ({"improved": 9, "regressed": 2, "unchanged": 26, "changed": 1, "new": 3, "no_longer_assessed": 0}
                                   if s["framework_id"] == "dpdpa" else
                                   {"improved": 6, "regressed": 3, "unchanged": 52, "changed": 0, "new": 0, "no_longer_assessed": 0})}
                       for s in summaries],
        "totals": {"prior": {"gaps": totals["gaps"] + 6}, "current": {"gaps": totals["gaps"]}},
        "changes": _changes(register),
    }
    return doc


def _changes(register):
    pick = [r for r in register if r["framework_id"] == "dpdpa" and r["outcome"] == "compliant"][:3]
    out = [{"framework_name": "India DPDPA", "requirement_id": r["requirement_id"], "requirement_title": r["requirement_title"],
            "prior_outcome_label": "Non-Compliant" if i % 2 == 0 else "Partially Compliant",
            "current_outcome_label": "Compliant", "direction_label": "Improved"} for i, r in enumerate(pick)]
    for rid in ("ISO.A5.18", "ISO.A8.8"):
        r = next(x for x in register if x["requirement_id"] == rid)
        out.append({"framework_name": "ISO 27001", "requirement_id": rid, "requirement_title": r["requirement_title"],
                    "prior_outcome_label": "Partially Compliant", "current_outcome_label": r["outcome_label"],
                    "direction_label": "Regressed"})
    return out


def horizon(target, actions):
    if any(a["target_date"] and date.fromisoformat(a["target_date"]) < GEN and a["status_label"] != "Done" for a in actions):
        return "overdue"
    if not target:
        return "unscheduled"
    days = (date.fromisoformat(target) - GEN).days
    if days <= 30: return "30"
    if days <= 90: return "90"
    if days <= 180: return "180"
    return "later"


def _soa_row(req, theme, outcome):
    if outcome is None:
        app_, impl = "not_assessed", "Not assessed"
        app_label = "Not determined"
    elif outcome == "not_applicable":
        app_, app_label, impl = "excluded", "Excluded", "Not applicable"
    else:
        app_, app_label = "applicable", "Applicable"
        impl = {"compliant": "Implemented", "partially_compliant": "Partially implemented",
                "non_compliant": "Not implemented", "insufficient_evidence": "Not determined"}[outcome]
    just = None
    if outcome == "not_applicable":
        just = "No on-premises development; all development is outsourced under contract." if "development" in req["title"].lower() else "Not relevant to the cloud-only operating model."
    return {"applicability": app_, "applicability_label": app_label, "control_id": req["id"],
            "implementation_label": impl, "justification": just,
            "justification_by": "Priya Sharma" if just else None, "justification_on": "2026-09-24" if just else None,
            "outcome": outcome, "reference": req.get("section_ref") or req["id"], "theme": theme, "title": req["title"]}


if __name__ == "__main__":
    d = build()
    (OUT / "rich_document.json").write_text(json.dumps(d, indent=1, ensure_ascii=False))
    print("requirements", d["summary"]["totals"], [ (s["name"], s["score"]) for s in d["summary"]["frameworks"]])
    print("matrix", d["summary"]["risk_matrix"], "groups", [(g["topic"], g["horizon"]) for g in d["roadmap"]["groups"]])
    print("soa", d["soa"]["totals"])
