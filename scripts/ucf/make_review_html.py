#!/usr/bin/env python3
"""Build the single-file review page for the UCF drafts.

    python3 scripts/ucf/make_review_html.py [--data DIR] [--out FILE]

Reads the draft library (docs/ucf/drafts by default) and writes one
self-contained HTML file: decisions, ISO clause checks, legal items, every
control for sign-off, and a record trace. Decisions are kept in the browser
and exported as JSON or Markdown. Stdlib only.
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.frameworks.ucf.loader import load_library  # noqa: E402
from app.frameworks.ucf.schema import FRAMEWORK_SUBSETS, subset_label  # noqa: E402

REVIEW_KEY = "ucf-review-0.0.1-draft"  # fixed so saved browser decisions survive library version bumps
ROUND = 2
# Controls changed or added in this round, with a one-line reason. The page gives these a fresh decision key,
# so his earlier approval of the old text does not carry over. Every other control keeps its saved decision.
ROUND2_CHANGES: dict[str, str] = {
    'UC-AST-01': 'Wording (D08): covers software, services and systems, and records location and classification for information.',
    'UC-AST-02': 'Split (D11): narrowed to acceptable use rules acknowledged, which now state that use is monitored (D09); the other half is now UC-AST-13.',
    'UC-AST-04': 'Gained a mapped ask (D09): the classification-scheme half of a NIST data classification ask. Text unchanged.',
    'UC-AST-07': 'Split (D11): narrowed to the records retention schedule; the other half is now UC-AST-14.',
    'UC-AST-13': 'New: split from UC-AST-02 (D11). Handling rules by classification level.',
    'UC-AST-14': 'New: split from UC-AST-07 (D11). Protection of records.',
    'UC-AST-43': 'Split (D11): narrowed to unsupported and unneeded software; the other half is now UC-AST-44.',
    'UC-AST-44': 'New: split from UC-AST-43 (D11). Hardware end-of-life replacement and disposal; completes UC-PHY-12.',
    'UC-CRY-40': 'Split (D11): narrowed to the data in use standard; the other half is now UC-CRY-41 and UC-CRY-42.',
    'UC-CRY-41': 'New: split from UC-CRY-40 (D11). Secrets kept out of code and logs.',
    'UC-CRY-42': 'New: split from UC-CRY-40 (D11). Tenant data isolation.',
    'UC-GOV-02': 'Soft NIST ask (D09): the register now feeds scope, policy and risk decisions.',
    'UC-GOV-06': "Wording (D08): the top-level policy reflects the organization's context.",
    'UC-GOV-14': 'Narrowed (D14) to the general communication plan; incident and recovery communication moved to UC-INC-43.',
    'UC-GOV-16': 'Split (D11, D19): narrowed to processes planned and run; change control maps to UC-SDC-09, outside processes to UC-SUP-05.',
    'UC-GOV-17': 'Soft NIST ask (D09): secure development measures map here as partial, and how_to_ask prompts for them.',
    'UC-GOV-40': "Wording (D17): 'leadership' became 'top management'.",
    'UC-IAM-03': 'Split (D11): narrowed to credential issue, reset and revocation; the other half is now UC-IAM-13.',
    'UC-IAM-13': 'New: split from UC-IAM-03 (D11). Default credentials changed on installation.',
    'UC-INC-01': 'Split (D11): narrowed to the incident procedure and roles; the other half is now UC-INC-09.',
    'UC-INC-09': 'New: split from UC-INC-01 (D11). The plan communicated and exercised; the yearly exercise setting moved here.',
    'UC-INC-43': 'New (D14): incident and recovery communication, moved out of UC-GOV-14.',
    'UC-OPS-01': 'Gained a mapped ask (D09): NIST log retention, split from a retention-and-protection ask. Text unchanged.',
    'UC-OPS-03': 'Soft NIST ask (D09): monitoring now covers unauthorized devices and wireless access points.',
    'UC-PHY-02': 'Split (D11): narrowed to entry rules and visitor control; the other half is now UC-PHY-13.',
    'UC-PHY-12': 'Split (D11): narrowed to scheduled maintenance by authorized personnel; the other half is now UC-PHY-14.',
    'UC-PHY-13': 'New: split from UC-PHY-02 (D11). Physical access rights review and leaver badge removal.',
    'UC-PHY-14': 'New: split from UC-PHY-12 (D11). Data cleared before equipment leaves for repair. Owner set to Head of IT Operations (D20).',
    'UC-RES-06': 'Split (D11): narrowed to redundancy for critical systems; the other half is now UC-RES-07.',
    'UC-RES-07': 'New: split from UC-RES-06 (D11). Failover testing; the yearly test setting moved here.',
    'UC-RES-42': 'Split (D11): narrowed to backups checked before restore; the other half is now UC-RES-43.',
    'UC-RES-43': 'New: split from UC-RES-42 (D11). Restored systems verified before return to production.',
    'UC-RSK-06': 'Gained a mapped ask (D11): identifying applicable privacy laws, moved from UC-RSK-08. Text unchanged.',
    'UC-RSK-08': 'Split (D11): narrowed to the record of personal data processing; the other half is now UC-RSK-11; the laws ask moved to UC-RSK-06.',
    'UC-RSK-10': 'The violations half of the policy-exceptions ask now maps here (D11); the text says violations are recorded and handled.',
    'UC-RSK-11': 'New: split from UC-RSK-08 (D11). Responsibility for privacy assigned.',
    'UC-RSK-40': "D09 and D17: now treats opportunities as a risk category and carries that NIST record; 'leadership' became 'top management'.",
    'UC-RSK-41': "Split (D11): narrowed to cyber and supplier risk in the enterprise risk process ('top management', D17); the other half is now UC-RSK-44.",
    'UC-RSK-42': 'Policy exceptions only (D11): the violations half of the source ask moved to UC-RSK-10.',
    'UC-RSK-44': 'New: split from UC-RSK-41 (D11). Risk escalation criteria and channels.',
    'UC-SDC-09': 'D19: change control from the operational planning clause maps here; unintended changes are now reviewed.',
    'UC-SUP-03': 'Wording (D08, D09): each agreement states the scope of access and data granted.',
    'UC-SUP-05': 'Kept (D11) on your reason and rewritten as one review with two triggers: a set interval and a change of scope. Also carries outside processes (D19).',
    'UC-SUP-06': 'Split (D11): narrowed to cloud rules, register and provider assurance; the other half is now UC-SUP-07.',
    'UC-SUP-07': 'New: split from UC-SUP-06 (D11). Cloud exit plans.',
    'UC-SUP-40': 'Split (D11): narrowed to the documented, approved supplier risk program; the other half is now UC-SUP-42.',
    'UC-SUP-42': 'New: split from UC-SUP-40 (D11). Supply chain security responsibilities assigned and communicated.',
}

FW_NAME = {"iso27001": "ISO 27001", "nist_csf": "NIST CSF", "dpdpa": "DPDPA"}

# ---------------------------------------------------------------------------
# Review items that are not controls. Written from the Results section of
# tasks/handoffs/2026-10-13-ucf-part-1-kickoff.md and the agents' notes files.
# kind: "decision" (Approve / Change / Reject), "legal" and "verify" (Verified / Needs change)
# ---------------------------------------------------------------------------

DECISIONS = [
    {
        "id": "D01", "title": "A question field on every control",
        "body": "Check 6 needs a client-facing question, and how_to_ask is direction plus an example probe. Every control now has one question: one obligation, one sentence, answerable on the five-value scale, no control code, no framework name. DPDPA questions reuse the curated text. The five compound DPDPA questions (CONSENT.2, NOTICE.1, MINIMIZE.3, TRANSFER.1, TRANSFER.2) were split across controls.",
        "rec": "Approve. It adds one field to the approved list in plan 7.4.",
    },
    {
        "id": "D02", "title": "Same-control rule is checked per atom",
        "body": "The plan says no source requirement maps to the same control twice. I read that at atom level. 236 pairs of (record, control) are reached by two or more atoms of the same record; they are allowed and shown as INFO by the validator. A record-level reading would force one row per record and lose the per-atom reasons.",
        "rec": "Approve the atom-level reading.",
    },
    {
        "id": "D03", "title": "Id ranges and stable ids",
        "body": "UC-<DOMAIN>-<NN>. ISO controls use 01 to 39, NIST slots 40 to 69, DPDPA slots 70 to 99 in the 13 base domains. The five privacy domains are created only by DPDPA and number from 01. Ids are stable once signed. Any later change makes a new library version (validator check 7, lock file written at the first signed version).",
        "rec": "Approve. The ranges let three agents work without collisions; the gaps in numbering are harmless.",
    },
    {
        "id": "D04", "title": "How numbers and timeframes are kept apart by layer",
        "body": "key_settings is written 'layer: setting | layer: setting'. Any number with a unit in shown text must appear in key_settings under base or a selected framework (check 4). Today's numbers: DPDPA 72-hour breach report, 90-day grievance cap, one-year log retention, 12-month reviews, three-year inactivity erasure with a 48-hour warning and its user thresholds, child under 18. A few base controls state a yearly cycle under base. The 'strictest among selected frameworks' rule is not scripted because no two frameworks set the same number yet.",
        "rec": "Approve.",
    },
    {
        "id": "D05", "title": "Owner roles (18) and the owner of each domain",
        "body": "A closed list: CISO, Top Management, Risk and Compliance Manager, Head of Internal Audit, Head of IT Operations, Identity and Access Lead, Security Engineering Lead, Network and Infrastructure Lead, Security Operations Lead, Head of Application Development, Head of Facilities, HR Head, Head of Procurement, Incident Response Lead, Business Continuity Manager, Data Governance Lead, Data Protection Officer, Legal Counsel. Each domain has a default owner (see the Controls tab headers). Roles are not people. The owner appears only in the owner field, never in a control statement. Owner and importance on clause-only controls are the agent's own seed.",
        "rec": "Approve the list, then adjust any control owner on its card.",
    },
    {
        "id": "D06", "title": "Two splits made after review",
        "body": "UC-INC-03 carried 18 NIST atoms and UC-OPS-03 carried 16. I moved recovery management (criteria, roles, start and end of recovery) to a new NIST slot UC-INC-42, and alert analysis, correlation and routing to a new NIST slot UC-OPS-41. UC-OPS-03's goal, statement, test and question were narrowed to monitoring and raising alerts. INC-03 still holds basic recovery for the ISO atom, so check the INC-03 and INC-42 boundary. The A.8.15 log-analysis atom still maps to OPS-03.",
        "rec": "Approve, after reading UC-INC-03, UC-INC-42, UC-OPS-03 and UC-OPS-41.",
    },
    {
        "id": "D07", "title": "Merges and splits of Annex A and clauses",
        "body": "Splits where the test differs: A.5.18 into IAM-04, 05, 06; A.5.19 into SUP-01, 02; A.5.26 into INC-03, 04; A.5.30 into RES-02, 03; A.6.3 into PPL-03, 04; A.8.8 into OPS-04, 05; A.8.13 into RES-04, 05; A.8.15 into OPS-01, 02; A.8.24 into CRY-01, 02; clause 6.1.3 into RSK-02, 03. Merges of a clause with an Annex A control: 5.2 with A.5.1 (GOV-06), 5.3 with A.5.2 (GOV-07), 7.3 with the all-staff part of A.6.3 (PPL-03), 9.2 with A.5.35 (RSK-09). No two Annex A controls were merged. A.7.1 and A.7.3 could merge and were kept separate.",
        "rec": "Approve, or note which to change.",
    },
    {
        "id": "D08", "title": "Wording suggestions for base controls (three applied in round 2)",
        "body": "The mapping agents suggested these edits to ISO base controls and I left them: RSK-06 name an owner per entry; PPL-03 add checks that awareness worked; AST-01 cover software, services and systems and record location and classification; GOV-06 policy reflects organizational context; SUP-03 name the scope of access and data granted; INC-04 add affected individuals; OPS-01 add access to sensitive data to logged events plus a review step; GOV-04 a base control for measures scaled to data risk; AST-07 and AST-08 retention triggers and erasure on request. Applying them would shrink some DPDPA and NIST remainder slots.",
        "after": "Applied in round 2, as you agreed: UC-AST-01 now covers software, services and systems and records location and classification for information; UC-GOV-06 says the top-level policy reflects the organization's context; UC-SUP-03 says each agreement states the scope of access and data granted. The others are left as they were.",
        "rec": "Applied. The three cards are in your review list.",
    },
    {
        "id": "D09", "title": "NIST asks marked full that are soft (applied in round 2)",
        "intro": [
            "Words used here. A record is one line of a source framework (a NIST subcategory such as GV.OC-02). An atom is one single ask inside it (GV.OC-02 asks three things, so it has atoms a, b and c). A mapping row says: this atom is answered by this control. Full coverage means: if the client passes the control's test, the atom is satisfied.",
            "Soft means the row says full, but a client could pass the control and still fail the NIST ask. NIST shows 295 full rows of 307 mainly because the new NIST slot controls were written to fit their atoms. The rows below are the places where no slot was written and the match was stretched. My choices: K keep as full; E keep full but edit the control text or add a mapping row so full is true (no new control); P mark partial.",
        ],
        "table": {"head": ["NIST atom", "The ask, in plain words", "Mapped to", "Why the fit is weak", "Recommendation"], "rows": [
            ["DE.CM-01-c", "Detect unauthorized devices and rogue wireless networks on the network.", "UC-OPS-03 Monitoring", "OPS-03 talks about anomalous behavior in general. Nothing mentions unknown devices or rogue wireless, so a client with no such detection would pass.", "E. Add unauthorized devices and wireless access points to OPS-03's statement and test."],
            ["DE.AE-07-b", "Analysts have asset and criticality information when they investigate an alert.", "UC-OPS-41 Alert analysis", "Already in the control's goal and test. Soft only because the control carries 8 asks.", "K. Already true."],
            ["DE.AE-06-c", "Incident responders can reach the log analysis platform.", "UC-OPS-41", "Statement and test already cover responder access.", "K."],
            ["GV.SC-06-b", "Before a supplier relationship starts, plan its scope, including the access and data the supplier gets.", "UC-SUP-03 Supplier agreements", "SUP-03 is about contract clauses. It never asks that access and data granted be scoped in advance.", "E. Say in SUP-03 that the scope of access and data granted is stated."],
            ["PR.PS-06-d", "Track and report measures of how well secure development is working.", "UC-GOV-17 Performance monitoring", "GOV-17 is generic. Nothing requires a development measure.", "P with an immaterial remainder: development measures are one kind of metric; add an example to how_to_ask. One new control for one ask is not worth it."],
            ["ID.IM-01-a", "Schedule regular evaluations of the cyber program, such as self-assessment or audit.", "UC-RSK-09 Independent review", "NIST accepts a self-assessment. RSK-09 demands an independent review, so our control is stricter. A client doing only self-assessments passes NIST but fails RSK-09.", "K, with a note that for NIST-only clients the question is stricter than NIST. Your call (see D15)."],
            ["DE.CM-03-c", "Tell personnel that their use of company systems is monitored.", "UC-AST-02 Acceptable use", "AST-02 is about rules and acknowledgement. Nothing says the rules must state that use is monitored.", "E. Add that the rules state use of systems is monitored."],
            ["ID.AM-07-c", "Keep a classification scheme for data and label data by it.", "UC-AST-05 Labeling", "The scheme itself is UC-AST-04. The atom has two asks and only one is mapped.", "E. Mapping only: also map this atom to UC-AST-04."],
            ["GV.OC-02-c", "Take stakeholder expectations into account in strategy, policy and risk decisions.", "UC-GOV-02 Interested parties", "GOV-02 records the requirements and decides which to address. It does not require that they feed strategy, policy and risk.", "E. Add one sentence: the register feeds scope, policy and risk decisions."],
            ["GV.RM-07-a, -b", "Treat opportunities (upside risk) as a category in the risk method and record them in risk discussions.", "UC-GOV-10 Risks and opportunities", "ISO clause 6.1 uses 'opportunities' for ways to improve the security program. NIST means upside in enterprise risk decisions. Same word, different idea.", "P with the remainder in UC-RSK-40 (extend risk direction to cover opportunities), or accept as nearest home. Low stakes (see D15)."],
            ["PR.PS-04-c", "Keep logs for a defined period and protect them from alteration.", "UC-OPS-02 Log protection only", "Two asks in one atom. Protection is in OPS-02, retention is in OPS-01. Only one half is mapped.", "E. Mapping only: split the atom or add a second row to OPS-01."],
        ]},
        "after": "Applied in round 2, as recommended. Text edits: OPS-03 (unauthorized devices and wireless access points), SUP-03 (scope of access and data), AST-02 (rules state that use is monitored), GOV-02 (the register feeds scope, policy and risk decisions). Mapping: ID.AM-07-c also maps to AST-04; PR.PS-04-c is split into c1 retention (OPS-01) and c2 protection (OPS-02); PR.PS-06-d is partial on GOV-17 with an immaterial remainder, and GOV-17's how_to_ask now prompts for secure development measures; GV.RM-07-a and -b are partial on GOV-10 with the remainder in RSK-40, whose text now covers opportunities, so RSK-40 is the record's primary; ID.IM-01-a stays full on RSK-09 with a stricter-than-source note on the mapping row. DE.AE-07-b and DE.AE-06-c are unchanged. No new control.",
        "rec": "Applied. Nothing to decide here; the changed cards are in your review list.",
    },
    {
        "id": "D10", "title": "DPDPA mapping judgment calls",
        "intro": [
            "A primary control is the one control marked as the home of a record. It decides where the record appears in the sign-off table and the trace, and does not limit what else the record maps to. A remainder slot is the small extra control for what a base control misses. Example: DPDPA requires erasure when the purpose ends. ISO control UC-AST-08 (deleting information) covers deletion in general (partial); the leftover for personal data sits in UC-AST-70, a remainder of AST-08. Remainder immaterial means the base control covers the ask in practice and what is left is too small for its own control; the row says so, with a reason.",
            "Three immaterial remainders exist: NIST GV.OC-03-b (each legal requirement has an owner) to UC-RSK-06, because the owner is one more column in the same register and sample. NIST PR.AT-01-d (check that awareness works) to UC-PPL-03, because it comes from the same awareness program and test. DPDPA SECURITY.1-a (reasonable technical safeguards) to UC-RES-04 backups, because personal data backups are inside normal backup scope.",
        ],
        "table": {"head": ["Item", "The ask in plain words", "What was done", "Why it is a judgment call", "Recommendation"], "rows": [
            ["SECURITY.1-a, -b", "Take reasonable technical and organizational safeguards to protect personal data and prevent breaches.", "Partial to GOV-04, OPS-01 and RES-04, with slots GOV-70 and OPS-70.", "An umbrella ask meaning 'run security properly'. No single control carries it; GOV-04 is the nearest home.", "Accept. Do not create a 'measures scaled to data risk' base control."],
            ["BN.NOTIFY.3-a, -c", "The incident response plan must cover detecting and investigating personal data breaches.", "Full to UC-INC-01.", "Marked full, but INC-01's test does not check that personal data breaches are covered. Generous.", "Accept. A plan for all incidents covers a personal data breach. No DPDPA text in a base control."],
            ["SECURITY.2-a, -b", "Encrypt personal data at rest and in transit.", "Full to UC-CRY-01.", "The Rules accept encryption, masking, obfuscation or tokens. We require encryption only. Tied to the legal item on CH2.SECURITY.2.", "Your legal call first. If the Act's options are accepted, widen to encryption or an equivalent."],
            ["PGV-04 (CH4.SDF.4)", "A significant data fiduciary has an independent audit of its compliance each period and sends significant findings to the Board.", "Own control UC-PGV-04, not RSK-09.", "Looks close to ISO internal audit (RSK-09). Kept apart because the test differs: an independent data auditor and a Board submission.", "Accept. Make sure RSK-09's question never counts for DPDPA."],
            ["PNC-05, 06, 07 (CONSENT.1)", "Consent is a clear action, given freely, and states a specific purpose.", "One record split into three controls.", "The signed criteria were written for the whole record and must be shared out among three controls later.", "Accept. Handled when criteria are re-keyed."],
            ["CONSENT.2 and CM.GRANULAR.1", "List each purpose separately and let people choose per purpose.", "Both map to PNC-08 and PNC-09.", "Two repo records say the same thing.", "Accept. Keep both records for traceability, one control carries both."],
            ["Primary calls", "SECURITY.1 to GOV-04; MINIMIZE.2 and .3 to AST-08 and AST-07; SECURITY.3 to SUP-03; CORRECT.2 to PRT-04; BN.NOTIFY.1, .2, .4 to INC-04 and INC-03; CB.TRANSFER.2 to PSC-05; ACCESS.1 to PRT-02.", "In about half of these the primary row is a partial row on a base control, while a full row exists on a slot (BN.NOTIFY.1: primary INC-04 partial, but INC-70 is full and carries the record).", "Two rules are possible. R1: primary is the base control, so ISO-only clients see the record's home. R2: primary is the control with full coverage of the record's main ask.", "Applied in round 2: R2. Seven records qualified (the other three I had named already had a full primary): MINIMIZE.2 to AST-70, MINIMIZE.3 to AST-71, SECURITY.1 to GOV-70, SECURITY.3 to SUP-70, BN.NOTIFY.1 to INC-70, BN.NOTIFY.2 to INC-71, BN.NOTIFY.4 to INC-72. Only primary flags changed. The CH2.SECURITY.2 legal question stays open; CRY-01 is not widened."],
        ]},
        "rec": "Applied as approved. Nothing to decide.",
    },
    {
        "id": "D11", "title": "Controls doing two jobs: splits applied in round 2",
        "intro": [
            "You approved the card and marked PHY-02, AST-43 and SUP-40 Split and SUP-05 Keep. The other 20 rows were blank, so they followed my recommendation. Result: 16 splits, 8 keeps. Each split has its own test now. The source asks were moved to the half that tests them, and the remainder slots were re-pointed. 15 new controls, plus UC-INC-43 from D14: the library grows from 195 to 211.",
            "Keeps: PHY-09, INC-04, PGV-03, PSC-02, GOV-41, NET-40, INC-42, and SUP-05 on your reason (a supplier review happens at a set interval or when the scope of service changes). SUP-05 is now written as one requirement with those two triggers.",
        ],
        "table": {"head": ["Control", "Now", "New control"], "rows": [
            ["UC-PHY-02", "Physical entry rules and visitor control", "UC-PHY-13 Physical access rights review and leaver badge removal"],
            ["UC-PHY-12", "Scheduled equipment maintenance (source ask A.7.13-b split into b1 and b2)", "UC-PHY-14 Data cleared before equipment leaves for repair"],
            ["UC-SUP-06", "Cloud governance and provider assurance", "UC-SUP-07 Cloud exit plans"],
            ["UC-INC-01", "Incident procedure and roles", "UC-INC-09 Incident plan communicated and exercised (the yearly exercise setting moved with it)"],
            ["UC-RES-06", "Redundancy for critical systems", "UC-RES-07 Failover testing (the yearly test setting moved with it)"],
            ["UC-IAM-03", "Credential issue, reset and revocation", "UC-IAM-13 Default credentials changed on installation"],
            ["UC-AST-02", "Acceptable use rules acknowledged", "UC-AST-13 Handling rules by classification level"],
            ["UC-AST-07", "Records retention schedule (AST-71 completes it for personal data)", "UC-AST-14 Protection of records"],
            ["UC-GOV-16", "Security processes planned and run", "None. Change control maps to SDC-09, externally provided processes to SUP-05 (see D19)"],
            ["UC-RSK-08", "Record of personal data processing", "UC-RSK-11 Responsibility for privacy assigned. The laws ask re-maps to RSK-06"],
            ["UC-RSK-41", "Cyber and supplier risk in the enterprise risk process", "UC-RSK-44 Risk escalation criteria and channels"],
            ["UC-RSK-42", "Policy exceptions only", "None. Source ask GV.PO-01-d split: d1 exceptions stay, d2 violations map to RSK-10"],
            ["UC-AST-43", "Unsupported and unneeded software removed", "UC-AST-44 Hardware end-of-life replacement and disposal (remainder of PHY-12)"],
            ["UC-CRY-40", "Data in use standard", "UC-CRY-41 Secrets kept out of code and logs; UC-CRY-42 Tenant data isolation"],
            ["UC-SUP-40", "Supplier risk program documented and approved", "UC-SUP-42 Supply chain security responsibilities assigned and communicated"],
            ["UC-RES-42", "Backups checked before restore", "UC-RES-43 Restored systems verified before return to production"],
        ]},
        "rec": "Applied. Review the changed and new cards on the Controls tab (they open first).",
    },
    {
        "id": "D12", "title": "Not done in this slice (what each item is)",
        "intro": [
            "1. ISO scope question content. At the start of an engagement the product asks a few scope questions (in the ISO definition file). There are four: scope of the management system, cloud use, software development, and physical premises. Each answer can trigger an applicability proposal, a suggestion that some controls are probably not applicable (for example no cloud proposes A.5.23 as not applicable; no development proposes A.8.4, 8.25, 8.28, 8.30, 8.31, 8.33; fully remote proposes A.7.1 to 7.6, 7.8, 7.11, 7.12). The consultant confirms each; nothing is removed automatically. Today they name Annex A ids. After the unified controls are signed, each proposal must list unified control ids instead, and a split changes which ids a proposal lists. It was left because the controls had to exist first. Your decision: whether four questions are enough for ISO. Confirm after the splits are final; the work itself is mechanical.",
            "2. Re-keying the 728 signed test criteria. These are the criteria you signed: 230 for ISO, 348 for NIST, 150 for DPDPA. Each is one checkable condition ('every inventory entry has an assigned owner'), tagged design or operating, with an evidence hint and a source reference. They are keyed to the old record ids (ISO.A5.9, CH2.CONSENT.3), so each must be attached to the unified control that now carries its record. A script can do it by record. The hard part: 87 of the 240 records map to more than one control (316 criteria), so someone decides per criterion which control it tests. Our drafted test field is one paragraph per control with a sample size and a pass rule, and it loses the one-condition-per-line structure, the design or operating tag, the evidence hint and the criterion ids, and some criteria were not carried. Clauses 4 to 10 have no signed criteria, so their tests are new text. Your decision: which is authoritative for what an auditor tests. I recommend the signed criteria stay as the list of tests under each control, with the drafted paragraph as a readable summary (see D18).",
            "3. The ids lock file. A file listing every unified control id at the moment you sign the first version. From then on the validator fails if an id disappears or changes meaning, so saved assessments cannot be orphaned. It is written only at signing, and we are still changing ids (splits). No decision needed: you sign, then it is run.",
            "4. Loading into the app. Today the library lives only as draft files; nothing in the product reads it. Loading means the questionnaire, the information request, the judge input and the review queue use unified controls instead of the 52 hand-written clusters. Plan 7.5 says only signed rows are loaded. No decision now; the order is sign domains, re-key criteria, lock, validation script, then load.",
            "Also: the fields were drafted by Sonnet agents and spot-checked only. Your reading of the 195 cards is the first full review of the statements, questions and tests. Please sample tests as well as statements.",
        ],
        "rec": "Confirm the order described in 4, and decide D18.",
    },
    {
        "id": "D13", "title": "Statements are role-neutral (applied after your first 43 reviews)",
        "body": "You pointed out that a statement cannot hinge on a named role doing the work, because compliance depends on the implementation existing. All 195 statements were rewritten as assertive requirements with no implementer named; 190 had named a role and 38 leaned on generic actors such as 'system owners' or 'the team'. Only the statement field changed; the owner stays in the owner field. 'Top management' remains where the requirement itself is about management (GOV-05, 06, 07, 08, 18, OPS-06, RSK-02, RSK-09), and PGV-01 names the officer being appointed. The validator now fails any statement that names a listed role, so it cannot drift back.",
        "rec": "Confirm the wording style on a few cards, for example UC-AST-06 and UC-IAM-05. If you already approved a control, re-skim only its statement.",
    },
    {
        "id": "D14", "title": "Security communication (UC-GOV-14) is two jobs: narrow it and add an incident slot",
        "body": "You asked: if this is about incidents, say so. The ISO clause behind it (7.4) asks only for a plan for what security matters are communicated, when, to whom and how: policy changes, results, audit outcomes, requirements passed to suppliers. It is not about incidents. But four NIST incident and recovery communication asks were mapped into it (who receives incident information and what may be shared; updates to leadership during recovery), so the card read like both. It duplicates neither INC-04 (legal notification deadlines) nor GOV-41 (delivery of risk artifacts). Proposal: narrow GOV-14 to the general communication plan, and add a new control UC-INC-43 'Incident and recovery communication' for the four NIST asks. Cost: one control (196), four mapping rows moved.",
        "after": "Applied in round 2. UC-GOV-14 is now 'Security communication plan' (clause 7.4 only) and no longer appears for NIST-only clients. New UC-INC-43 'Incident and recovery communication' carries RS.CO-03 a, b and c and RC.CO-03 a and b, and is the primary for both records. I also moved RS.CO-03-b (status updates to top management) from INC-03, as the optional step suggested.",
        "rec": "Applied. Review UC-GOV-14 and UC-INC-43.",
    },
    {
        "id": "D15", "title": "Smaller calls from D09 and D10",
        "body": "(a) NIST ID.IM-01-a (regular evaluation, self-assessment accepted) is carried by UC-RSK-09, which requires an independent review: accept it as stricter than NIST? (b) NIST GV.RM-07 opportunities: make it partial with the remainder in UC-RSK-40, or accept the nearest home? (c) Primary rule for DPDPA overlap records: R1 primary is the base control; R2 primary is the control with full coverage. I recommend R2; it changes about 10 primary flags and nothing else.",
        "rec": "Applied as approved: (a) a note on the mapping row; (b) partial, remainder in RSK-40; (c) R2 on seven records (see D10).",
    },
    {
        "id": "D16", "title": "UC-RSK-10 rewritten: who does the check is not named",
        "body": "Your comment: the control should be about whether teams' actual practice follows the documented policy (policy drift), applying only to teams where controls are relevant. Rewritten as 'Practice checked against policy': the day-to-day work of each team where security controls apply is checked on a defined cycle against documented policies; gaps are recorded with actions and tracked to closure. The checker is not named; 'for example internal audit' appears only in how_to_ask. Open: must the check be independent of the team, or may a manager self-check? ISO allows managers. I did not require independence.",
        "rec": "Approve, or tell me to require an independent check.",
    },
    {
        "id": "D17", "title": "Management words and the owner badge",
        "body": "(a) 'Top management' stays only where the requirement is itself about management (leadership, policy approval, review, risk acceptance). 'Leadership' used elsewhere (GOV-40, RSK-40, RSK-41, SUP-40) would be replaced with 'top management' for one term. (b) Each card shows an owner badge from the owner field (CISO, Head of IT Operations and so on). It is routing information, never part of the requirement. I would keep it on the sign-off tables and hide it on anything the client sees.",
        "rec": "(a) Applied in round 2 to GOV-40, RSK-40 and RSK-41; SUP-40 had no 'leadership' left. (b) No action now: the badge stays on sign-off, and hiding it client-side is a later concern.",
    },
    {
        "id": "D18", "title": "What is the authoritative test: signed criteria or the drafted paragraph?",
        "body": "You signed 728 criteria. Each control also has a drafted test paragraph. Recommendation: keep the signed criteria as the list of tests under each control (original criterion ids preserved) and treat the drafted paragraph as a readable summary. You then decide only the 316 criteria whose record maps to more than one control; a script will list them for you.",
        "rec": "Approve.",
    },
    {
        "id": "D19", "title": "GOV-16: change control and outside processes found homes (no new control)",
        "body": "The clause 8.1 control did three jobs. Planning and running processes to set criteria stays in UC-GOV-16, now 'Security processes planned and run'. Controlling planned changes and reviewing unintended ones (8.1 c) now maps to UC-SDC-09 Change management; I added one sentence to SDC-09 so unintended changes are reviewed for their effect, which makes the match full. Controlling externally provided processes, products and services (8.1 d) maps to UC-SUP-05 Supplier service review, because reviewing suppliers against the agreed terms is how that is shown. Zero new controls instead of up to two.",
        "rec": "Approve, or tell me to create the two controls instead.",
    },
    {
        "id": "D20", "title": "Other judgment calls made while applying round 2",
        "intro": [
            "Ids: ISO-origin splits took the next free number in the ISO range (PHY-13, PHY-14, SUP-07, INC-09, RES-07, IAM-13, AST-13, AST-14, RSK-11); NIST-origin splits took the next free NIST number (RSK-44, AST-44, CRY-41, CRY-42, SUP-42, RES-43). New controls inherit the original's owner and importance, except UC-PHY-14, which I gave to Head of IT Operations because clearing data from equipment is IT work.",
            "Primary moves outside R2: ISO A.5.34 now has its primary on the processing-record ask in RSK-08 (the laws ask moved to RSK-06). NIST GV.RM-07 now has its primary on RSK-40, the control that fully carries it after D09. NIST records whose primary is a partial row with a full remainder slot (for example PR.PS-03 on PHY-12, completed by AST-44) were left as they are: R2 was approved for DPDPA records only.",
            "Source asks split into numbered parts because each bundled two asks: ISO A.7.13-b (b1 maintenance by authorized people, b2 data cleared before repair), NIST GV.PO-01-d (d1 exceptions, d2 violations), NIST PR.PS-04-c (c1 retention, c2 protection). NIST ID.AM-07-c maps to two controls, both full: AST-04 for the scheme and AST-05 for the labels.",
            "Clause flags: all 70 clause asks are now marked verified, including the climate asks in 4.1 and 4.2, which your PDF could not show but you verified.",
        ],
        "rec": "Approve, or note any you want changed.",
    },
]

LEGAL = [
    ("CH2.CONSENT.3", "Stored s.6(4) and 6(6). Criteria say withdrawal is s.6(4) and the Consent Manager text is s.6(7)."),
    ("CH2.CONSENT.4", "Stored s.6(8) to (9). Consent Manager registration may start at s.6(7)."),
    ("CH2.NOTICE.3", "Stored s.6(3), s.8(9) and r.9. An earlier pack cited s.5(1). Confirm the contact duty sits in 6(3), 8(9), r.9."),
    ("CH2.MINIMIZE.1", "Stored s.6(1); the repo once cited s.4(1). The Act has no general minimization duty for s.7 uses."),
    ("CH2.SECURITY.1", "Criteria say the duty is s.8(5), not s.8(4). Check the stored reference."),
    ("CH2.SECURITY.2", "The Rules accept any of four measures; the pack requires encryption. Should the control name encryption only?"),
    ("CH3.CORRECT.2", "The pack scopes erasure to data no longer necessary. The Act allows a request at any time, with retention only for purpose or law."),
    ("CH4.CHILD.1 and CH4.CHILD.2", "The pack once swapped s.9(2) and s.9(3). Stored refs now (9(3), 9(2)) match the criteria; confirm."),
    ("CH4.CHILD.3", "Stored as a bare 'Section 9'. The age and guardian checks come from Rules r.10 to r.12."),
    ("CH4.SDF.3 and CH4.SDF.4", "Stored (c)(i) and (c)(ii) are right; the repo once cited a non-existent s.10(2)(d). The Rules r.13(3) duty has no home record: add one?"),
    ("CB.TRANSFER.2", "The Act uses a restricted-country model (s.16(1)). The pack's criteria require transfer contracts, which is practice. The sectoral-law clause is s.16(2), not stored."),
    ("CB.TRANSFER.3", "Localization is not in s.16(1) text; stored 'Section 16' is broad. Confirm the source."),
    ("BN.NOTIFY.1, .3, .4", "The 72-hour period comes from the Rules, not s.8(6). The incident response plan and the breach register are practice or Rules-derived; stored 8(4) to (6) and 8(6) may be loose."),
    ("CM.RECORDS.2", "'Refresh after a reasonable period' has no basis in the Act. It was not atomized. Keep it out, or add as practice?"),
    ("Inactivity erasure", "The signed criterion (conditional, with a warning period) has no atom; it lives in the UC-AST-70 fields with its thresholds. Add an atom to trace it?"),
    ("CH2.CONSENT.2 and CM.GRANULAR.1", "The two records duplicate each other. Keep both records, as now?"),
]


# Cross-check of the clause paraphrases against the 2022 PDF saved in Downloads (13 Oct 2026).
# "fixed" means the paraphrase or the control was changed after the check.
CLAUSE_CHECK = {
    "ISO.C4.1": ("ok", "Atom a matches the 2022 text. Atom b (climate change) comes from Amendment 1:2024, which is not in the PDF you saved, so it is still unverified."),
    "ISO.C4.2": ("fixed", "Matches a to c. Added the PDF's note that requirements can include legal, regulatory and contractual ones. The climate wording is from Amendment 1:2024 and is unverified."),
    "ISO.C4.3": ("ok", "Matches: boundaries and applicability, issues, requirements, interfaces and dependencies, documented scope."),
    "ISO.C4.4": ("ok", "Matches."),
    "ISO.C5.1": ("fixed", "The PDF has eight asks (a to h). We missed (e) the program achieves its intended outcomes and (h) supporting other managers' leadership. Added atoms e and f; UC-GOV-05 goal, statement and test updated."),
    "ISO.C5.2": ("ok", "Matches a to g, including the commitments, documented, communicated, available to interested parties."),
    "ISO.C5.3": ("ok", "Matches."),
    "ISO.C6.1.1": ("fixed", "Added that planning considers the context issues and interested-party requirements."),
    "ISO.C6.1.2": ("fixed", "Wrong before: we wrote 'criteria for when to assess'. The standard says criteria for performing assessments (timing is 8.2). Atom and UC-RSK-01 corrected."),
    "ISO.C6.1.3": ("fixed", "The statement of applicability must also say whether each control is implemented; we had left that out. Atoms b and c now name the Annex A comparison and the full contents. UC-RSK-03 updated."),
    "ISO.C6.2": ("fixed", "Matches. Added that objectives are kept as documented information."),
    "ISO.C6.3": ("ok", "Matches."),
    "ISO.C7.1": ("ok", "Matches."),
    "ISO.C7.2": ("ok", "Matches a to d."),
    "ISO.C7.3": ("ok", "Matches a to c."),
    "ISO.C7.4": ("fixed", "Wrong before: we included 'by whom'. The 2022 text lists what, when, with whom and how only (who was in the 2013 edition). Atom and UC-GOV-14 corrected."),
    "ISO.C7.5": ("ok", "Matches 7.5.1 to 7.5.3, including documents of external origin."),
    "ISO.C8.1": ("fixed", "'Outsourced' was too narrow: the text says externally provided processes, products or services. Also added that criteria are set for the processes. UC-GOV-16 updated."),
    "ISO.C8.2": ("ok", "Matches."),
    "ISO.C8.3": ("ok", "Matches."),
    "ISO.C9.1": ("fixed", "Missing: methods must give valid, comparable and reproducible results; when results are analyzed and by whom. Atoms and UC-GOV-17 updated."),
    "ISO.C9.2": ("fixed", "9.2.1: audits test conformity to the organization's own requirements and the standard, and effective implementation. 9.2.2: the program takes account of process importance and past audit results. Atoms and UC-RSK-09 updated."),
    "ISO.C9.3": ("fixed", "We missed 9.3.2 c, changes in the needs and expectations of interested parties (new in 2022), and the trends list. Atom and UC-GOV-18 updated."),
    "ISO.C10.1": ("ok", "Matches. Numbering is right for 2022: 10.1 is continual improvement, 10.2 is nonconformity."),
    "ISO.C10.2": ("ok", "Matches a to g."),
}


def build(data_dir: Path) -> dict:
    lib = load_library(data_dir)
    doms = sorted(lib.domains.values(), key=lambda d: d.sort)

    counts = []
    from collections import Counter

    for subset in FRAMEWORK_SUBSETS:
        shown = lib.shown_controls(subset) & set(lib.controls)
        recs = [r for r, rec in lib.records.items() if rec.framework in subset]
        covered = sum(1 for r in recs if lib.controls_of_record.get(r, set()) & shown)
        atoms = [a for a in lib.atoms.values() if a.framework in subset]
        counts.append({
            "label": " + ".join(FW_NAME[f] for f in ("iso27001", "nist_csf", "dpdpa") if f in subset),
            "key": subset_label(subset),
            "controls": len(shown), "records": len(recs), "covered": covered, "atoms": len(atoms),
        })

    controls = []
    for c in sorted(lib.controls.values(), key=lambda c: (lib.domains[c.domain].sort if c.domain in lib.domains else 99, c.id)):
        rows = lib.rows_by_control.get(c.id, [])
        fws = sorted({r.source_framework for r in rows})
        sources = []
        for r in rows:
            a = lib.atoms.get(r.atom_id)
            sources.append({
                "fw": r.source_framework, "rec": r.record_id, "ref": r.source_ref, "atom": r.atom_id,
                "text": a.paraphrase if a else "", "match": r.match_type, "cov": r.coverage,
                "reason": r.reason, "primary": r.primary, "rem": r.remainder_of,
                "imm": r.immaterial_reason if r.remainder_immaterial else "",
            })
        controls.append({
            "id": c.id, "title": c.title, "domain": c.domain, "theme": c.iso_theme, "goal": c.goal,
            "owner": c.owner_role, "imp": c.importance, "origin": c.origin, "note": c.note,
            "statement": c.statement, "why": c.why_asked, "how": c.how_to_ask, "q": c.question,
            "evidence": c.expected_evidence, "good": c.good_looks_like, "test": c.test,
            "risk": c.baseline_risk, "applies": c.applicability, "type": c.control_type,
            "freq": c.frequency, "ks": c.key_settings_raw, "fws": fws, "sources": sources,
            "nrec": len(lib.records_of_control.get(c.id, set())),
        })

    clauses = []
    for rid, rec in lib.records.items():
        if rec.kind != "clause":
            continue
        clauses.append({
            "id": rid, "ref": rec.reference, "title": rec.title,
            "atoms": [{"id": a.atom_id, "text": a.paraphrase} for a in lib.atoms_by_record.get(rid, [])],
            "controls": sorted({r.unified_control_id for r in lib.rows_by_record.get(rid, []) if r.unified_control_id}),
            "nv": any(a.needs_verification for a in lib.atoms_by_record.get(rid, [])),
            "check": CLAUSE_CHECK.get(rid, ("", ""))[0], "checknote": CLAUSE_CHECK.get(rid, ("", ""))[1],
        })

    trace = []
    for rid, rec in lib.records.items():
        rows = lib.rows_by_record.get(rid, [])
        prim = next((r.unified_control_id for r in rows if r.primary), "")
        others = sorted({f"{r.unified_control_id} ({r.coverage})" for r in rows if r.unified_control_id and r.unified_control_id != prim})
        trace.append({"fw": rec.framework, "id": rid, "ref": rec.reference, "title": rec.title,
                      "prim": prim, "others": others, "atoms": len(lib.atoms_by_record.get(rid, []))})

    ids = {c["id"] for c in controls}
    unknown = sorted(set(ROUND2_CHANGES) - ids)
    if unknown:
        raise SystemExit(f"ROUND2_CHANGES names unknown controls: {unknown}")
    for c in controls:
        c["r2"] = ROUND2_CHANGES.get(c["id"], "")
    return {
        "reviewKey": REVIEW_KEY,
        "round": ROUND,
        "version": lib.library_version,
        "date": datetime.date.today().isoformat(),
        "counts": counts,
        "domains": [{"code": d.code, "name": d.name, "owner": d.owner_role, "privacy": d.privacy} for d in doms],
        "controls": controls,
        "clauses": clauses,
        "trace": trace,
        "decisions": DECISIONS,
        "legal": [{"id": f"L{i + 1:02d}", "ref": r, "body": b} for i, (r, b) in enumerate(LEGAL)],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(ROOT / "docs/ucf/drafts"))
    ap.add_argument("--out", default=str(ROOT / "tasks/2026-10-13-ucf-review.html"))
    args = ap.parse_args()
    data = build(Path(args.data))
    blob = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c").replace("\u2028", "\\u2028")
    html = (ROOT / "scripts/ucf/review_template.html").read_text(encoding="utf-8").replace("/*__DATA__*/null", blob)
    Path(args.out).write_text(html, encoding="utf-8")
    print(f"wrote {args.out}: {len(data['controls'])} controls, {len(data['decisions'])} decisions, "
          f"{len(data['clauses'])} clauses, {len(data['legal'])} legal items, "
          f"{sum(1 for c in data['controls'] if c['r2'])} changed in round {ROUND}, {len(html) // 1024} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
