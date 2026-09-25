"""ISO/IEC 27001:2022 test criteria: DRAFT v1 for Saqlain's sign-off (P6-2c).

NOT attached to any `Control` and never imported by prompts or analyzers.
A P6-2b-style converter turns the *approved* review sheet
(tasks/criteria-review/) into pack code. Until then these criteria must not
reach an LLM.

Covers ISO/IEC 27001:2022 clauses 4.1-10.2 (new requirement ids `ISO.C4.1`
... `ISO.C10.2`, authored here in ISO27001_CLAUSE_REQUIREMENTS_DRAFT) and all
93 Annex A controls in the repo pack (app/frameworks/definitions/iso27001.py),
in framework order.

Sources (cited by clause/control number only; no standard text reproduced):
- ISO/IEC 27001:2022, Information security, cybersecurity and privacy
  protection - ISMS - Requirements (3rd edition, Oct 2022), clauses 4-10 and
  Annex A. Catalogue page: https://www.iso.org/standard/27001
  (licence-restricted). Clause numbering, lettered items, 'shall' status
  and the Annex A Table A.1 list were verified on 2026-09-25 against a
  licensed copy of the unamended third edition (2022-10) supplied by
  Saqlain; nothing from it is reproduced here.
- ISO/IEC 27001:2022/Amd 1:2024, Climate action changes (Feb 2024), adds a
  climate-change determination to cl.4.1 and a note to cl.4.2.
  Catalogue page: https://www.iso.org/standard/88435.html. NOT verified
  against the amendment text: the supplied copy of the standard does not
  include Amd 1, so the two climate criteria are capped below high.
- ISO/IEC 27002:2022, Information security controls (implementation
  guidance). Cited as "(guidance)" only; criteria resting on it are capped at
  medium confidence. Catalogue page: https://www.iso.org/standard/75652.html
- Repo requirement definitions: app/frameworks/definitions/iso27001.py
  (titles, questions, EvidenceRequest document_type keys).

House style (D4, P6-2a rules 1-7, P6-2c rules):
- Own words, references only. ISO text is licence-restricted: statements and
  own-words descriptions paraphrase; `source_basis` cites by number only
  ("ISO/IEC 27001:2022 cl.6.1.3(d)", "ISO/IEC 27001:2022 A.5.15",
  "ISO/IEC 27002:2022 5.15 (guidance)"). The pack's current descriptions are
  near-verbatim ISO and were deliberately not reused.
- A `shall` in 27001 (a clause, or an Annex A control statement once the
  control is applicable in the SoA) may be `high`. 27002 guidance or
  `practice` is `medium` at most. `low` where interpretation is genuinely
  uncertain or the repo definition departs from the standard
  ("[repo says ...]" in source_basis).
- Annex A criteria assume the control is included as applicable in the
  Statement of Applicability (cl.6.1.3(d)); applicability itself is tested
  under ISO.C6.1.3.
- `evidence_hint` uses the pack's EvidenceRequest document_type keys where
  they fit (isms_scope, statement_of_applicability, security_policy,
  risk_assessment, isms_audit_reports, ...), with the evidence form in
  parentheses.
"""

from __future__ import annotations

from app.frameworks.schema import TestCriterion

# ── Version notes ─────────────────────────────────────────────────────────

_AMD1 = (
    "Added by ISO/IEC 27001:2022/Amd 1:2024 (published Feb 2024); in scope for "
    "certification audits against the amended standard. Not verified against "
    "the amendment text (the supplied copy of the standard is unamended)."
)
_NEW2022 = (
    "New in the 2022 edition (no 2013 equivalent). The transition from the 2013 "
    "edition ended 31 Oct 2025, so it now applies to every certified ISMS."
)
_NEWCTRL = (
    "New Annex A control in the 2022 edition (no 2013 equivalent). The 2013 "
    "transition ended 31 Oct 2025."
)

D, O = "design", "operating"
HIGH, MED, LOW = "high", "medium", "low"

_27001 = "ISO/IEC 27001:2022"
_27002 = "ISO/IEC 27002:2022"

# criterion_id -> (drafter_confidence, in_force_note). Review-sheet metadata
# only; the converter decides whether any of it survives into pack code.
ISO27001_CRITERIA_REVIEW_META: dict[str, tuple[str, str]] = {}

# Every ISO id (clauses and Annex A) -> own-words description (D-P6-J).
ISO27001_OWN_WORDS_DRAFT: dict[str, str] = {}

# New clause requirements (P5-7 folded in): id -> title, description,
# criticality, section, reference. `description` is the own-words text.
ISO27001_CLAUSE_REQUIREMENTS_DRAFT: dict[str, dict] = {}


def _criteria(req_id: str, *rows: tuple[str, str, str, str, str, str]) -> tuple[TestCriterion, ...]:
    """rows: (kind, statement, evidence_hint, source_basis, confidence, in_force_note)."""
    out = []
    for n, (kind, statement, evidence_hint, source_basis, confidence, note) in enumerate(rows, 1):
        cid = f"{req_id}.TC{n}"
        out.append(TestCriterion(cid, statement, kind, evidence_hint, source_basis))
        ISO27001_CRITERIA_REVIEW_META[cid] = (confidence, note)
    return tuple(out)


def _clause(req_id: str, title: str, criticality: str, section: str, reference: str, description: str) -> None:
    ISO27001_CLAUSE_REQUIREMENTS_DRAFT[req_id] = {
        "title": title,
        "description": description,
        "criticality": criticality,
        "section": section,
        "reference": reference,
    }
    ISO27001_OWN_WORDS_DRAFT[req_id] = description


def _own(req_id: str, description: str) -> None:
    ISO27001_OWN_WORDS_DRAFT[req_id] = description


# ══════════════════════════════════════════════════════════════════════════
# Clauses 4-10 (management-system requirements)
# ══════════════════════════════════════════════════════════════════════════

_clause("ISO.C4.1", "Organisational context and issues", "high", "context", "Clause 4.1",
        "The organisation works out which internal and external matters affect what its ISMS can achieve, and records whether climate change is one of them.")
_clause("ISO.C4.2", "Interested parties and their requirements", "high", "context", "Clause 4.2",
        "The organisation lists the parties with a stake in its information security, what each of them requires, and which of those requirements the ISMS will meet.")
_clause("ISO.C4.3", "ISMS scope", "critical", "context", "Clause 4.3",
        "The organisation sets and documents the boundaries of its ISMS, taking account of its context, stakeholder requirements and the interfaces with activities run by others.")
_clause("ISO.C4.4", "Establishing and running the ISMS", "high", "context", "Clause 4.4",
        "The organisation sets up, operates, keeps up and keeps improving an ISMS made of defined processes and the links between them, in line with the standard.")
_clause("ISO.C5.1", "Top management leadership", "critical", "leadership", "Clause 5.1",
        "Senior management visibly drives the ISMS: it sets direction, builds it into business processes, funds it, explains why it matters and holds people to it.")
_clause("ISO.C5.2", "Information security policy", "critical", "leadership", "Clause 5.2",
        "Senior management issues a top-level security policy that fits the organisation's purpose, frames objectives, commits to meeting requirements and to improvement, and is documented and shared.")
_clause("ISO.C5.3", "ISMS roles and authorities", "high", "leadership", "Clause 5.3",
        "Senior management assigns and announces who is responsible and empowered for security roles, including someone to keep the ISMS conformant and someone to report on its performance.")
_clause("ISO.C6.1.1", "Planning for risks and opportunities", "high", "planning", "Clause 6.1.1",
        "When planning the ISMS, the organisation identifies the risks and opportunities that could help or hinder it and plans, embeds and checks actions to deal with them.")
_clause("ISO.C6.1.2", "Risk assessment process", "critical", "planning", "Clause 6.1.2",
        "The organisation defines and documents a repeatable way to find, analyse and rank information security risks against set acceptance and assessment criteria, with a named owner for each risk.")
_clause("ISO.C6.1.3", "Risk treatment and Statement of Applicability", "critical", "planning", "Clause 6.1.3",
        "The organisation decides how each assessed risk will be handled, picks the controls needed, checks them against Annex A, records the result in a Statement of Applicability and gets risk owners to sign off the plan and the residual risk.")
_clause("ISO.C6.2", "Security objectives and plans", "high", "planning", "Clause 6.2",
        "The organisation sets security objectives that follow from its policy and risk results, can be measured and tracked, and are backed by a plan saying what, who, with what and by when.")
_clause("ISO.C6.3", "Planning of ISMS changes", "medium", "planning", "Clause 6.3",
        "Changes to the ISMS itself are made deliberately and according to a plan rather than ad hoc.")
_clause("ISO.C7.1", "Resources for the ISMS", "high", "support", "Clause 7.1",
        "The organisation works out and supplies the people, budget and tools the ISMS needs to be set up, run and improved.")
_clause("ISO.C7.2", "Competence", "high", "support", "Clause 7.2",
        "People whose work affects security performance have the skills the role needs, gaps are closed through training or other action, and proof of competence is kept.")
_clause("ISO.C7.3", "Awareness", "high", "support", "Clause 7.3",
        "Everyone working under the organisation's control knows the security policy exists, how their work contributes to the ISMS, and what happens if they do not follow it.")
_clause("ISO.C7.4", "ISMS communication", "medium", "support", "Clause 7.4",
        "The organisation decides what it will say about the ISMS, to whom, when and by what means, both internally and externally.")
_clause("ISO.C7.5", "Documented information", "high", "support", "Clause 7.5",
        "The organisation keeps the records and documents the ISMS needs, and creates, approves, versions, protects, distributes, retains and disposes of them in a controlled way, including documents from outside.")
_clause("ISO.C8.1", "Operational planning and control", "high", "operation", "Clause 8.1",
        "The organisation runs the processes needed to meet its security requirements against set criteria, controls planned changes, reacts to unplanned ones and keeps outsourced ISMS-relevant processes under control.")
_clause("ISO.C8.2", "Performing risk assessments", "critical", "operation", "Clause 8.2",
        "The organisation actually carries out its risk assessment on a schedule and whenever significant change is proposed or happens, and keeps the results.")
_clause("ISO.C8.3", "Implementing risk treatment", "critical", "operation", "Clause 8.3",
        "The organisation carries out its risk treatment plan and keeps a record of what was done.")
_clause("ISO.C9.1", "Monitoring and measurement", "high", "evaluation", "Clause 9.1",
        "The organisation decides what to monitor and measure about security, how, when and by whom the results are analysed, and uses them to judge how well the ISMS works.")
_clause("ISO.C9.2", "Internal audit", "critical", "evaluation", "Clause 9.2",
        "The organisation runs a planned programme of impartial internal audits to check that the ISMS meets its own and the standard's requirements and is working, and reports the findings to management.")
_clause("ISO.C9.3", "Management review", "critical", "evaluation", "Clause 9.3",
        "Senior management reviews the ISMS on a schedule, working through a defined set of inputs, and records its decisions on improvements and changes.")
_clause("ISO.C10.1", "Continual improvement", "medium", "improvement", "Clause 10.1",
        "The organisation keeps making its ISMS more suitable, sufficient and effective over time.")
_clause("ISO.C10.2", "Nonconformity and corrective action", "high", "improvement", "Clause 10.2",
        "When something fails to meet a requirement, the organisation contains and fixes it, finds and removes the root cause so it does not recur, checks the fix worked and keeps records.")


ISO27001_CRITERIA_DRAFT: dict[str, tuple[TestCriterion, ...]] = {}

ISO27001_CRITERIA_DRAFT.update({
    # ── Clause 4: Context of the organisation ─────────────────────────────
    "ISO.C4.1": _criteria(
        "ISO.C4.1",
        (D, "A current record lists the external and internal issues the organisation has judged relevant to its purpose and to the intended outcomes of its ISMS.",
         "context/issues register (e.g. PESTLE/SWOT or ISMS context document); isms_scope", f"{_27001} cl.4.1", HIGH, ""),
        (D, "The context record states whether climate change was judged a relevant issue for the ISMS, and gives the conclusion either way.",
         "context/issues register",
         f"{_27001} cl.4.1 as amended by Amd 1:2024 (amendment text not verified; the supplied standard copy is unamended)",
         MED, _AMD1),
        (O, "The issues record has been revisited since the last management review, or its review date falls within the organisation's defined review cycle.",
         "context/issues register (version history); isms_audit_reports (management review minutes)",
         f"{_27001} cl.4.1, cl.9.3.2(b)", MED, ""),
    ),
    "ISO.C4.2": _criteria(
        "ISO.C4.2",
        (D, "A record names the interested parties relevant to the ISMS (e.g. customers, regulators, staff, suppliers, shareholders).",
         "interested-parties register", f"{_27001} cl.4.2(a)", HIGH, ""),
        (D, "For each listed interested party, the record states its requirements that are relevant to information security, including legal, regulatory and contractual ones.",
         "interested-parties register; legal_register", f"{_27001} cl.4.2(b)", HIGH, ""),
        (D, "The record states which of the identified requirements the organisation has decided to address through the ISMS.",
         "interested-parties register", f"{_27001} cl.4.2(c)", HIGH, _NEW2022),
        (D, "The requirements analysis shows that climate-related requirements of interested parties were considered, whether or not any were found.",
         "interested-parties register",
         f"{_27001} cl.4.2 note added by Amd 1:2024 (amendment text not verified). A note, not a 'shall': the organisation is not obliged to record climate requirements",
         LOW, _AMD1),
    ),
    "ISO.C4.3": _criteria(
        "ISO.C4.3",
        (D, "A documented ISMS scope statement exists and names the organisational units, locations, services and assets covered.",
         "isms_scope", f"{_27001} cl.4.3", HIGH, ""),
        (D, "The scope statement identifies the interfaces and dependencies between activities inside the ISMS and those performed by other organisations or outside the scope.",
         "isms_scope", f"{_27001} cl.4.3(c)", HIGH, ""),
        (D, "Any exclusion from the scope is justified by reference to the context issues (4.1) and interested-party requirements (4.2).",
         "isms_scope; context/issues register", f"{_27001} cl.4.3(a)-(b)", MED, ""),
        (O, "The scope statement matches the scope stated on the certificate or audit reports and reflects the organisation's current services and sites.",
         "isms_scope; isms_audit_reports (certificate / audit report scope)", f"{_27001} cl.4.3", MED, ""),
    ),
    "ISO.C4.4": _criteria(
        "ISO.C4.4",
        (D, "The ISMS documentation identifies the processes that make up the ISMS (e.g. risk assessment, internal audit, incident management) and how they interact.",
         "ISMS manual or process map; security_policy", f"{_27001} cl.4.4", HIGH, ""),
        (O, "Records show each identified ISMS process has been operated in the last 12 months (e.g. a risk assessment run, an audit performed, a management review held).",
         "risk_assessment; isms_audit_reports", f"{_27001} cl.4.4", MED, ""),
    ),
    # ── Clause 5: Leadership ──────────────────────────────────────────────
    "ISO.C5.1": _criteria(
        "ISO.C5.1",
        (D, "The information security policy and objectives are approved by top management and are consistent with the organisation's stated strategic direction.",
         "security_policy (approval record); objectives register", f"{_27001} cl.5.1(a)", HIGH, ""),
        (O, "Top management has allocated resources to the ISMS, shown by an approved budget, headcount or tooling decision in the last 12 months.",
         "isms_audit_reports (management review minutes); budget approval", f"{_27001} cl.5.1(c)", HIGH, ""),
        (O, "Top management attended or chaired the most recent management review and recorded decisions on the ISMS.",
         "isms_audit_reports (management review minutes with attendance)", f"{_27001} cl.5.1(e)-(h), cl.9.3", HIGH, ""),
        (O, "Top management has communicated the importance of information security to staff in the last 12 months (e.g. all-hands message, policy launch note).",
         "internal communications record", f"{_27001} cl.5.1(d)", MED, ""),
    ),
    "ISO.C5.2": _criteria(
        "ISO.C5.2",
        (D, "The top-level information security policy includes, or points to, a framework for setting information security objectives.",
         "security_policy", f"{_27001} cl.5.2(b)", HIGH, ""),
        (D, "The policy contains an explicit commitment to satisfy applicable information security requirements.",
         "security_policy", f"{_27001} cl.5.2(c)", HIGH, ""),
        (D, "The policy contains an explicit commitment to continual improvement of the ISMS.",
         "security_policy", f"{_27001} cl.5.2(d)", HIGH, ""),
        (O, "The policy is available as a controlled document, has been communicated to staff, and is available to interested parties as the organisation decided.",
         "security_policy (intranet page, distribution record, public copy if any)", f"{_27001} cl.5.2(e)-(g)", HIGH, ""),
    ),
    "ISO.C5.3": _criteria(
        "ISO.C5.3",
        (D, "A document assigns responsibility and authority for ensuring the ISMS conforms to ISO/IEC 27001.",
         "roles_responsibilities", f"{_27001} cl.5.3(a)", HIGH, ""),
        (D, "A document assigns responsibility and authority for reporting ISMS performance to top management.",
         "roles_responsibilities", f"{_27001} cl.5.3(b)", HIGH, ""),
        (O, "The assigned security roles have been communicated within the organisation (e.g. org chart or RACI published on the intranet), and the named holders are current staff.",
         "roles_responsibilities (published org chart / RACI)", f"{_27001} cl.5.3", HIGH, ""),
    ),
    # ── Clause 6: Planning ────────────────────────────────────────────────
    "ISO.C6.1.1": _criteria(
        "ISO.C6.1.1",
        (D, "A record identifies the risks and opportunities to the ISMS itself (not only information security risks), drawing on the context issues and interested-party requirements.",
         "ISMS risks-and-opportunities register; risk_assessment", f"{_27001} cl.6.1.1", HIGH, ""),
        (D, "Each identified ISMS risk or opportunity has a planned action and a stated way to evaluate whether the action worked.",
         "ISMS risks-and-opportunities register", f"{_27001} cl.6.1.1(d)-(e)", HIGH, ""),
        (O, "The planned actions have owners and status updates, and at least one has been evaluated for effectiveness.",
         "ISMS risks-and-opportunities register (status fields); isms_audit_reports",
         f"{_27001} cl.6.1.1(e)(2)", MED, ""),
    ),
    "ISO.C6.1.2": _criteria(
        "ISO.C6.1.2",
        (D, "The risk methodology defines risk acceptance criteria and criteria for performing risk assessments.",
         "risk_assessment (methodology)", f"{_27001} cl.6.1.2(a)", HIGH, ""),
        (D, "The methodology identifies risks as loss of confidentiality, integrity or availability of information within the ISMS scope.",
         "risk_assessment (methodology)", f"{_27001} cl.6.1.2(c)(1)", HIGH, ""),
        (D, "The methodology defines how consequences and likelihood are rated and how they combine into a risk level.",
         "risk_assessment (methodology; rating scales)", f"{_27001} cl.6.1.2(d)", HIGH, ""),
        (O, "Every entry in the risk register has a named risk owner.",
         "risk_assessment (risk register)", f"{_27001} cl.6.1.2(c)(2)", HIGH, ""),
        (O, "Each risk in the register has been compared with the acceptance criteria and given a treatment priority.",
         "risk_assessment (risk register)", f"{_27001} cl.6.1.2(e)", HIGH, ""),
    ),
    "ISO.C6.1.3": _criteria(
        "ISO.C6.1.3",
        (D, "For each risk requiring treatment, the register or plan records the chosen treatment option (e.g. modify, avoid, share, retain) and the controls selected.",
         "risk_assessment (risk treatment plan)", f"{_27001} cl.6.1.3(a)-(b)", HIGH, ""),
        (D, "A Statement of Applicability lists the necessary controls and, for each Annex A control, whether it is included, why, whether it is implemented, and the reason for any exclusion.",
         "statement_of_applicability", f"{_27001} cl.6.1.3(d)", HIGH, ""),
        (D, "The selected controls were compared against Annex A to confirm no necessary control was omitted (e.g. a mapping or column in the SoA).",
         "statement_of_applicability", f"{_27001} cl.6.1.3(c)", HIGH, ""),
        (O, "Risk owners have approved the risk treatment plan and formally accepted the residual risks, with dated approvals.",
         "risk_assessment (signed treatment plan / acceptance records)", f"{_27001} cl.6.1.3(f)", HIGH, ""),
        (O, "The SoA's implementation status for a sample of controls matches what the assessment observes (a control marked implemented is in fact operating).",
         "statement_of_applicability; control evidence for sampled controls", f"{_27001} cl.6.1.3(d), cl.8.3", MED, ""),
    ),
    "ISO.C6.2": _criteria(
        "ISO.C6.2",
        (D, "Documented information security objectives exist, are consistent with the policy, and are measurable where practicable.",
         "objectives register; security_policy", f"{_27001} cl.6.2(a)-(b), (g)", HIGH, ""),
        (D, "For each objective the plan states what will be done, resources needed, who is responsible, the deadline and how results will be evaluated.",
         "objectives register (action plan)", f"{_27001} cl.6.2 (planning items h-l)", HIGH, ""),
        (O, "Progress on each objective has been monitored, with recorded measurements or status against target in the last 12 months.",
         "objectives register (tracking); isms_audit_reports (management review minutes)",
         f"{_27001} cl.6.2(d)", HIGH, _NEW2022),
    ),
    "ISO.C6.3": _criteria(
        "ISO.C6.3",
        (D, "A procedure or rule states how changes to the ISMS (scope, processes, roles, policies) are planned and approved before they take effect.",
         "ISMS change procedure; security_policy", f"{_27001} cl.6.3", HIGH, _NEW2022),
        (O, "The most recent significant ISMS change (e.g. scope change, reorganisation, new site) has a record showing it was planned and approved beforehand.",
         "ISMS change record; isms_audit_reports (management review minutes)",
         f"{_27001} cl.6.3. What counts as a 'change to the ISMS' is not defined; the sample is the assessor's judgment",
         MED, _NEW2022),
    ),
    # ── Clause 7: Support ─────────────────────────────────────────────────
    "ISO.C7.1": _criteria(
        "ISO.C7.1",
        (D, "The organisation has recorded the resources the ISMS needs (people, budget, tools) in a plan, budget or management review output.",
         "isms_audit_reports (management review minutes); ISMS budget or resource plan", f"{_27001} cl.7.1", HIGH, ""),
        (O, "The resources recorded as needed were provided: named people are in post and budgeted items were funded or procured.",
         "roles_responsibilities; procurement or budget records", f"{_27001} cl.7.1", MED, ""),
    ),
    "ISO.C7.2": _criteria(
        "ISO.C7.2",
        (D, "Competence requirements (skills, qualifications or experience) are defined for roles that affect information security performance.",
         "roles_responsibilities (role descriptions); hr_security", f"{_27001} cl.7.2(a)", HIGH, ""),
        (O, "For a sample of security-relevant role holders, records show they meet the defined competence requirements (certificates, training, CV).",
         "training_records; competence records", f"{_27001} cl.7.2(b), (d)", HIGH, ""),
        (O, "Where a competence gap was identified, a recorded action (training, mentoring, hiring) was taken and its effectiveness evaluated.",
         "training_records; competence gap log", f"{_27001} cl.7.2(c)", HIGH, ""),
    ),
    "ISO.C7.3": _criteria(
        "ISO.C7.3",
        (D, "Awareness content tells staff about the security policy, their contribution to the ISMS and the consequences of not conforming.",
         "training_records (awareness material)", f"{_27001} cl.7.3(a)-(c)", HIGH, ""),
        (O, "Records show people working under the organisation's control, including contractors in scope, completed awareness activity in the last 12 months.",
         "training_records (completion report)", f"{_27001} cl.7.3", MED, ""),
    ),
    "ISO.C7.4": _criteria(
        "ISO.C7.4",
        (D, "A communication plan or matrix states, for ISMS-relevant communications, what is communicated, when, to whom and how.",
         "ISMS communication plan", f"{_27001} cl.7.4(a)-(d)", HIGH, ""),
        (O, "A sample of planned communications (e.g. to staff, customers or regulators) shows they took place as planned.",
         "ISMS communication plan; sent communications",
         f"{_27001} cl.7.4. The clause requires the organisation to determine its communication needs; checking that planned communications happened goes one step further",
         MED, ""),
    ),
    "ISO.C7.5": _criteria(
        "ISO.C7.5",
        (D, "A document-control procedure covers identification, format, review and approval of ISMS documents.",
         "document control procedure", f"{_27001} cl.7.5.2", HIGH, ""),
        (D, "The procedure covers distribution, access, storage, version control, retention and disposal of ISMS documents and records, including documents of external origin.",
         "document control procedure", f"{_27001} cl.7.5.3", HIGH, ""),
        (O, "A sample of ISMS documents each shows an owner, version, approval and review date, and the version in use is the latest approved one.",
         "security_policy; other ISMS documents (sample)", f"{_27001} cl.7.5.2, cl.7.5.3", HIGH, ""),
        (O, "The documented information the standard requires is present, including scope, policy, risk assessment and treatment process, SoA, objectives, competence evidence, monitoring results, audit programme and results, management review results and nonconformity records.",
         "isms_scope; security_policy; risk_assessment; statement_of_applicability; isms_audit_reports",
         f"{_27001} cl.7.5.1(a), cl.4.3, 5.2, 6.1.2, 6.1.3, 6.2, 7.2, 9.1, 9.2.2, 9.3.3, 10.2", HIGH, ""),
    ),
    # ── Clause 8: Operation ───────────────────────────────────────────────
    "ISO.C8.1": _criteria(
        "ISO.C8.1",
        (D, "Criteria (e.g. procedures, standards, thresholds) are defined for the processes that implement risk treatment and the objectives.",
         "security_policy (topic-specific policies and procedures)", f"{_27001} cl.8.1", HIGH, ""),
        (D, "Externally provided processes, products or services relevant to the ISMS are identified and a control over each is defined.",
         "supplier_security (supplier register with ISMS-relevance flag)", f"{_27001} cl.8.1", HIGH, ""),
        (O, "For a sample of planned operational changes, records show they were controlled, and any unintended change was reviewed with action taken on adverse effects.",
         "change_management (change records)", f"{_27001} cl.8.1", MED, ""),
    ),
    "ISO.C8.2": _criteria(
        "ISO.C8.2",
        (D, "The risk methodology or ISMS calendar sets the interval for repeating the risk assessment and names significant change as a trigger.",
         "risk_assessment (methodology)", f"{_27001} cl.8.2", HIGH, ""),
        (O, "A risk assessment was completed within the defined interval, with dated results retained.",
         "risk_assessment (dated risk register / report)", f"{_27001} cl.8.2", HIGH, ""),
        (O, "For the most recent significant change (e.g. new system, supplier, site), a risk assessment was performed and recorded.",
         "risk_assessment; change_management", f"{_27001} cl.8.2", HIGH, ""),
    ),
    "ISO.C8.3": _criteria(
        "ISO.C8.3",
        (D, "The risk treatment plan assigns each treatment action an owner and a target date.",
         "risk_assessment (risk treatment plan)", f"{_27001} cl.6.1.3(e), cl.8.3", MED, ""),
        (O, "Records show the treatment actions due in the period were completed, or overdue ones re-approved, and the results retained.",
         "risk_assessment (treatment plan status)", f"{_27001} cl.8.3", HIGH, ""),
    ),
    # ── Clause 9: Performance evaluation ──────────────────────────────────
    "ISO.C9.1": _criteria(
        "ISO.C9.1",
        (D, "A measurement plan defines what is monitored and measured (processes and controls), the methods, the frequency, and who monitors and who analyses.",
         "ISMS measurement plan / metrics catalogue", f"{_27001} cl.9.1(a)-(f)", HIGH, ""),
        (O, "Monitoring and measurement results for the last period are recorded.",
         "logging_monitoring; metrics reports", f"{_27001} cl.9.1 (documented information)", HIGH, ""),
        (O, "The results were analysed and used to evaluate ISMS performance and effectiveness, e.g. in a report to management review.",
         "isms_audit_reports (management review minutes); metrics reports", f"{_27001} cl.9.1, cl.9.3.2(d)(2)", HIGH, ""),
    ),
    "ISO.C9.2": _criteria(
        "ISO.C9.2",
        (D, "An internal audit programme sets frequency, methods, responsibilities and reporting, and covers the whole ISMS scope, including clauses 4-10 and the applicable Annex A controls, over the audit cycle.",
         "isms_audit_reports (audit programme)",
         f"{_27001} cl.9.2.1(a)-(b), cl.9.2.2. Full coverage within one cycle is the usual certification-body expectation, not express text",
         MED, ""),
        (D, "Each audit has defined criteria and scope.",
         "isms_audit_reports (audit plans)", f"{_27001} cl.9.2.2(a)", HIGH, ""),
        (O, "Audits were performed as programmed in the last 12 months by auditors who did not audit their own work.",
         "isms_audit_reports (audit reports with auditor names)", f"{_27001} cl.9.2.2(b)", HIGH, ""),
        (O, "Audit results were reported to relevant management and retained.",
         "isms_audit_reports (reports; distribution or review minutes)", f"{_27001} cl.9.2.2(c)", HIGH, ""),
    ),
    "ISO.C9.3": _criteria(
        "ISO.C9.3",
        (D, "Management review is scheduled at planned intervals (e.g. at least annually) in the ISMS calendar or policy.",
         "security_policy; ISMS calendar", f"{_27001} cl.9.3.1", HIGH, ""),
        (O, "A management review was held within the planned interval and its record shows it considered each required input: previous actions, changes in context and in interested-party needs, performance feedback, stakeholder feedback, risk results and improvement opportunities.",
         "isms_audit_reports (management review minutes)", f"{_27001} cl.9.3.2(a)-(g)", HIGH, ""),
        (O, "The management review record contains decisions on improvement opportunities and on any needed changes to the ISMS.",
         "isms_audit_reports (management review minutes)", f"{_27001} cl.9.3.3", HIGH, ""),
    ),
    # ── Clause 10: Improvement ────────────────────────────────────────────
    "ISO.C10.1": _criteria(
        "ISO.C10.1",
        (D, "The ISMS has a defined means of identifying and acting on improvement opportunities (e.g. an improvement log fed by audits, incidents and reviews).",
         "improvement log; isms_audit_reports", f"{_27001} cl.10.1", HIGH, ""),
        (O, "At least one improvement to the ISMS's suitability, adequacy or effectiveness was implemented in the last 12 months and recorded.",
         "improvement log; isms_audit_reports (management review minutes)",
         f"{_27001} cl.10.1. The clause sets no minimum rate; one recorded improvement per year is the assessor's threshold",
         MED, ""),
    ),
    "ISO.C10.2": _criteria(
        "ISO.C10.2",
        (D, "A procedure requires nonconformities to be corrected, their causes determined, and similar nonconformities looked for.",
         "corrective action procedure", f"{_27001} cl.10.2(a)-(b)", HIGH, ""),
        (O, "Each nonconformity raised in the period is logged with its nature, the action taken and the result.",
         "corrective action log; isms_audit_reports", f"{_27001} cl.10.2(f)-(g)", HIGH, ""),
        (O, "For a sample of closed nonconformities, the record shows a root-cause analysis and a review of the corrective action's effectiveness.",
         "corrective action log", f"{_27001} cl.10.2(b)(2), (d)", HIGH, ""),
    ),
})


# ══════════════════════════════════════════════════════════════════════════
# Annex A.5: Organisational controls
# ══════════════════════════════════════════════════════════════════════════

_own("ISO.A5.1", "The organisation has a top-level security policy plus subject-specific policies that management has signed off, that staff and relevant outsiders have received and confirmed, and that are revisited on a schedule and after major change.")
_own("ISO.A5.2", "Each security responsibility the organisation needs is spelled out and given to a named role or person.")
_own("ISO.A5.3", "Tasks that would let one person both commit and conceal misuse (e.g. requesting and approving access) are split between different people.")
_own("ISO.A5.4", "Managers actively require their staff and contractors to follow the organisation's security policies and procedures.")
_own("ISO.A5.5", "The organisation knows which authorities (regulators, law enforcement, CERTs) it may need to reach and keeps working contact with them.")
_own("ISO.A5.6", "The organisation keeps in touch with security forums, industry groups and professional bodies to stay informed.")
_own("ISO.A5.7", "The organisation gathers information about threats relevant to it and turns it into analysis it acts on.")
_own("ISO.A5.8", "Security requirements and risks are dealt with as a normal part of running every project, whatever its type.")
_own("ISO.A5.9", "The organisation keeps an up-to-date list of its information and the systems, devices and services that hold it, each with an accountable owner.")
_own("ISO.A5.10", "Written rules say how people may use, and must handle, the organisation's information and assets, and those rules are put into practice.")
_own("ISO.A5.11", "Staff, contractors and other parties hand back every organisational asset they hold when their role, contract or agreement ends or changes.")
_own("ISO.A5.12", "Information is sorted into sensitivity levels according to how much protection its confidentiality, integrity and availability need, including what stakeholders require.")
_own("ISO.A5.13", "Information and related assets are marked with their classification level using procedures that follow the classification scheme.")
_own("ISO.A5.14", "Every way information is sent or shared, internally or with outside parties, whether electronic, physical or verbal, is covered by rules, procedures or agreements.")
_own("ISO.A5.15", "The organisation sets and applies rules deciding who may reach which information, systems and premises, based on business and security needs.")
_own("ISO.A5.16", "Identities for people and systems are created, maintained and retired under control across their whole lifespan.")
_own("ISO.A5.17", "Passwords, keys, tokens and other secrets are issued and handled through a managed process, and users are told how to look after them.")
_own("ISO.A5.18", "Users' access rights are granted, periodically re-checked, changed and taken away according to the access-control policy.")
_own("ISO.A5.19", "The organisation has defined processes for managing the security risks that come from using suppliers' products and services.")
_own("ISO.A5.20", "Each supplier contract sets out the security obligations relevant to that kind of supplier, agreed by both sides.")
_own("ISO.A5.21", "The organisation manages security risks that travel down the supply chain of the technology products and services it buys.")
_own("ISO.A5.22", "The organisation keeps watch on how suppliers deliver and protect their services, reviews them, and handles changes in what they provide.")
_own("ISO.A5.23", "The organisation has security-driven processes for choosing, using, administering and leaving cloud services.")

ISO27001_CRITERIA_DRAFT.update({
    # ── Information Security Policies ─────────────────────────────────────
    "ISO.A5.1": _criteria(
        "ISO.A5.1",
        (D, "A top-level information security policy and topic-specific policies (e.g. access control, backup, cryptography) exist and each shows management approval.",
         "security_policy (approval record per policy)", f"{_27001} A.5.1", HIGH, ""),
        (O, "The policies have been published to staff and relevant external parties, and records show staff acknowledged them.",
         "security_policy (distribution list; acknowledgement records)", f"{_27001} A.5.1", HIGH, ""),
        (O, "Each policy has been reviewed within its defined review interval, or after a significant change, with the review recorded.",
         "security_policy (version history / review log)",
         f"{_27001} A.5.1 [repo description omits the planned-interval review element of the control]",
         LOW, ""),
    ),
    "ISO.A5.2": _criteria(
        "ISO.A5.2",
        (D, "A document defines the information security responsibilities of each security role (e.g. CISO, asset owners, risk owners, incident manager).",
         "roles_responsibilities", f"{_27001} A.5.2", HIGH, ""),
        (O, "Each defined security role is assigned to a named, current person.",
         "roles_responsibilities (RACI with names)", f"{_27001} A.5.2", HIGH, ""),
    ),
    "ISO.A5.3": _criteria(
        "ISO.A5.3",
        (D, "The organisation has identified which duties conflict (e.g. requesting vs approving access, developing vs deploying to production) and states they must be held by different people.",
         "roles_responsibilities; access_control_policy", f"{_27001} A.5.3", HIGH, ""),
        (O, "For a sample of the conflicting duty pairs, system roles or approval records show different individuals performed each side.",
         "access_control_policy (role assignments); change_management (approver vs implementer)", f"{_27001} A.5.3", HIGH, ""),
        (D, "Where segregation is not feasible (e.g. small team), a compensating control such as monitoring or supervisory review is documented.",
         "roles_responsibilities; risk_assessment", f"{_27002} 5.3 (guidance)", MED, ""),
    ),
    "ISO.A5.4": _criteria(
        "ISO.A5.4",
        (D, "Management expectations that staff follow security policies are stated in a document staff receive (e.g. code of conduct, onboarding pack, manager guide).",
         "security_policy; hr_security", f"{_27001} A.5.4", HIGH, ""),
        (O, "Managers have briefed or required their teams to comply, shown by records such as policy acknowledgement tracking or manager-led briefings in the period.",
         "training_records; security_policy (acknowledgement tracking)", f"{_27001} A.5.4; {_27002} 5.4 (guidance)", MED, ""),
    ),
    # ── Threat Intelligence & Asset Management ────────────────────────────
    "ISO.A5.5": _criteria(
        "ISO.A5.5",
        (D, "A current contact list names the authorities to contact (e.g. data protection regulator, CERT-In or national CERT, law enforcement, sector regulator) and when.",
         "breach_procedure (authority contact list)", f"{_27001} A.5.5", HIGH, ""),
        (D, "The incident procedure states who is authorised to contact authorities and within what timelines for reportable events.",
         "breach_procedure", f"{_27002} 5.5 (guidance)", MED, ""),
        (O, "The authority contact list has been verified or updated within the last 12 months.",
         "breach_procedure (contact list review date)", f"{_27001} A.5.5 ('maintained')", MED, ""),
    ),
    "ISO.A5.6": _criteria(
        "ISO.A5.6",
        (D, "The organisation records which security forums, industry groups, ISACs or professional bodies it participates in or subscribes to.",
         "membership or subscription list", f"{_27001} A.5.6", HIGH, ""),
        (O, "There is evidence of active participation in the period (e.g. advisories received and circulated, event attendance).",
         "advisory circulation records", f"{_27001} A.5.6 ('maintained')", MED, ""),
    ),
    "ISO.A5.7": _criteria(
        "ISO.A5.7",
        (D, "A documented process names the threat information sources used and how the information is analysed for relevance to the organisation.",
         "threat intelligence procedure", f"{_27001} A.5.7", HIGH, _NEWCTRL),
        (O, "Threat intelligence outputs (e.g. bulletins, assessments) were produced in the period.",
         "threat intelligence reports", f"{_27001} A.5.7", HIGH, _NEWCTRL),
        (O, "At least one threat intelligence output led to a recorded action (e.g. a risk register update, blocking rule, patch prioritisation).",
         "threat intelligence reports; risk_assessment; change_management", f"{_27002} 5.7 (guidance)", MED, _NEWCTRL),
    ),
    "ISO.A5.8": _criteria(
        "ISO.A5.8",
        (D, "The project management method requires security requirements and risks to be addressed at defined project stages, regardless of project type.",
         "project management methodology; sdlc_policy", f"{_27001} A.5.8", HIGH, ""),
        (O, "For a sample of projects in the period, project records show a security risk assessment or security requirements sign-off.",
         "project records (security assessments, gate sign-offs)", f"{_27001} A.5.8; {_27002} 5.8 (guidance)", MED, ""),
    ),
    "ISO.A5.9": _criteria(
        "ISO.A5.9",
        (D, "An inventory of information and associated assets (hardware, software, cloud services, data stores) exists for the ISMS scope.",
         "asset_inventory", f"{_27001} A.5.9", HIGH, ""),
        (D, "Every inventory entry has an assigned owner.",
         "asset_inventory",
         f"{_27001} A.5.9 [repo description omits the ownership element of the control]",
         LOW, ""),
        (O, "The inventory has been updated within its defined review cycle, and a sample of live assets (e.g. from cloud console or MDM) is present in it.",
         "asset_inventory; cloud console or MDM export", f"{_27001} A.5.9 ('maintained')", HIGH, ""),
    ),
    "ISO.A5.10": _criteria(
        "ISO.A5.10",
        (D, "An acceptable use policy states permitted and prohibited uses of information and assets.",
         "security_policy (acceptable use policy)", f"{_27001} A.5.10", HIGH, ""),
        (D, "Handling procedures state how information is to be handled at each classification level (storage, sharing, transport, disposal).",
         "security_policy (information handling procedure); asset_inventory (classification scheme)", f"{_27001} A.5.10", HIGH, ""),
        (O, "Users have acknowledged the acceptable use rules (e.g. at onboarding or annually).",
         "security_policy (acknowledgement records); hr_security", f"{_27001} A.5.10 ('implemented')", MED, ""),
    ),
    "ISO.A5.11": _criteria(
        "ISO.A5.11",
        (D, "The leaver and role-change procedure requires return of all organisational assets (devices, badges, tokens, documents).",
         "hr_security (leaver checklist)", f"{_27001} A.5.11", HIGH, ""),
        (O, "For a sample of leavers in the period, records show asset return checked against the asset inventory.",
         "hr_security (completed leaver checklists); asset_inventory", f"{_27001} A.5.11", HIGH, ""),
    ),
    "ISO.A5.12": _criteria(
        "ISO.A5.12",
        (D, "A classification scheme defines levels (e.g. public, internal, confidential, restricted) and the criteria for assigning them, taking account of the need to protect secrecy, accuracy and uptime, and of stakeholder requirements.",
         "asset_inventory (classification scheme)", f"{_27001} A.5.12", HIGH, ""),
        (O, "Information assets in the inventory have a classification assigned.",
         "asset_inventory", f"{_27001} A.5.12", HIGH, ""),
    ),
    "ISO.A5.13": _criteria(
        "ISO.A5.13",
        (D, "A labelling procedure states how each classification level is marked on documents, systems and media, consistent with the classification scheme.",
         "asset_inventory (classification scheme; labelling procedure)", f"{_27001} A.5.13", HIGH, ""),
        (O, "A sample of documents or records shows labels matching the procedure (e.g. headers, metadata tags, DLP labels).",
         "sample labelled documents; tool configuration (e.g. sensitivity labels)", f"{_27001} A.5.13", HIGH, ""),
    ),
    # ── Access Control & Identity Management ──────────────────────────────
    "ISO.A5.14": _criteria(
        "ISO.A5.14",
        (D, "Rules or procedures cover each transfer channel used (e.g. email, file sharing, removable media, courier, verbal), stating the protection required by classification.",
         "security_policy (information transfer policy)", f"{_27001} A.5.14", HIGH, ""),
        (D, "Transfers of information with external parties are covered by agreements that include security terms (e.g. NDAs, data-sharing agreements).",
         "supplier_security (sample agreements); data-sharing agreements", f"{_27001} A.5.14; {_27002} 5.14 (guidance)", MED, ""),
        (O, "Technical settings for the main transfer channels enforce the rules (e.g. email TLS, external sharing restrictions on file-sharing tools).",
         "network_security; tool configuration exports", f"{_27002} 5.14 (guidance)", MED, ""),
    ),
    "ISO.A5.15": _criteria(
        "ISO.A5.15",
        (D, "A topic-specific access control policy defines rules for logical and physical access, based on business and security requirements (e.g. need-to-know, least privilege).",
         "access_control_policy", f"{_27001} A.5.15", HIGH, ""),
        (O, "For a sample of systems, actual access configurations follow the policy rules (e.g. role-based groups, no shared admin accounts).",
         "access_control_policy; system access listings", f"{_27001} A.5.15 ('implemented')", HIGH, ""),
    ),
    "ISO.A5.16": _criteria(
        "ISO.A5.16",
        (D, "A procedure covers creation, change and removal of identities, requires each identity to be linked to one person (or an owned non-person account), and controls shared identities.",
         "access_control_policy (identity management procedure)", f"{_27001} A.5.16; {_27002} 5.16 (guidance)", MED, ""),
        (O, "A reconciliation of active accounts in the identity provider against the HR roster shows no active identities for departed staff.",
         "identity provider export; HR leaver list", f"{_27001} A.5.16", HIGH, ""),
        (O, "Service and other non-person accounts in scope each have a recorded owner.",
         "identity provider export; asset_inventory", f"{_27002} 5.16 (guidance)", MED, ""),
    ),
    "ISO.A5.17": _criteria(
        "ISO.A5.17",
        (D, "A procedure governs issuing, resetting and revoking authentication information (passwords, tokens, keys), including identity verification before resets.",
         "access_control_policy", f"{_27001} A.5.17; {_27002} 5.17 (guidance)", MED, ""),
        (D, "Users are given written guidance on keeping authentication information confidential (e.g. no sharing, use of a password manager, reporting compromise).",
         "security_policy; training_records", f"{_27001} A.5.17", HIGH, ""),
        (O, "Default vendor credentials are changed on installation, as shown by configuration baselines or build checklists.",
         "configuration_baselines", f"{_27002} 5.17 (guidance)", MED, ""),
    ),
    "ISO.A5.18": _criteria(
        "ISO.A5.18",
        (D, "The access policy requires access to be requested and approved before provisioning, and defines the frequency of access reviews.",
         "access_control_policy", f"{_27001} A.5.18", HIGH, ""),
        (O, "For a sample of new or changed access in the period, an approval record exists before the access was granted.",
         "access_control_policy (access request tickets)", f"{_27001} A.5.18", HIGH, ""),
        (O, "Access reviews were completed at the defined frequency for in-scope systems, with inappropriate access removed.",
         "access_control_policy (user access review records)", f"{_27001} A.5.18", HIGH, ""),
        (O, "For a sample of leavers, access was removed within the timeframe set by policy.",
         "access_control_policy; HR leaver list; identity provider logs", f"{_27001} A.5.18", HIGH, ""),
    ),
    # ── Supplier & Third-Party Management ─────────────────────────────────
    "ISO.A5.19": _criteria(
        "ISO.A5.19",
        (D, "A supplier security policy or procedure defines how suppliers are identified, risk-rated and selected based on security risk.",
         "supplier_security (supplier security policy)", f"{_27001} A.5.19", HIGH, ""),
        (O, "A supplier register lists suppliers with access to the organisation's information or systems, with a risk rating for each.",
         "supplier_security (supplier register)", f"{_27001} A.5.19; {_27002} 5.19 (guidance)", MED, ""),
        (O, "For a sample of suppliers onboarded in the period, a security due-diligence assessment was completed before contract signature or access.",
         "supplier_security (due-diligence records)", f"{_27001} A.5.19 ('implemented')", HIGH, ""),
    ),
    "ISO.A5.20": _criteria(
        "ISO.A5.20",
        (D, "A standard set of supplier security clauses exists, varied by supplier type or risk tier.",
         "supplier_security (contract templates / security schedule)", f"{_27001} A.5.20", HIGH, ""),
        (O, "A sample of contracts with high-risk suppliers contains agreed security terms (e.g. confidentiality, incident notification, audit rights, return or deletion at exit).",
         "supplier_security (sample supplier agreements)", f"{_27001} A.5.20; {_27002} 5.20 (guidance)", MED, ""),
    ),
    "ISO.A5.21": _criteria(
        "ISO.A5.21",
        (D, "The supplier process includes requirements for ICT suppliers to pass security requirements to their own sub-suppliers and to disclose critical components or subcontractors.",
         "supplier_security", f"{_27001} A.5.21; {_27002} 5.21 (guidance)", MED, ""),
        (O, "For a sample of key ICT suppliers, records show the supply chain was assessed (e.g. sub-processor lists reviewed, SBOM or component provenance obtained).",
         "supplier_security (assessment records; sub-processor lists)",
         f"{_27001} A.5.21. What evidence of supply-chain assessment is sufficient is not fixed; the control statement is process-level",
         LOW, ""),
    ),
    "ISO.A5.22": _criteria(
        "ISO.A5.22",
        (D, "The supplier procedure sets how often each risk tier of supplier is reviewed and what the review covers.",
         "supplier_security", f"{_27001} A.5.22", HIGH, ""),
        (O, "Reviews of high-risk suppliers were performed at the set frequency (e.g. assurance reports checked, SLA and incident performance reviewed).",
         "supplier_security (review records); cloud_services (assurance reports)", f"{_27001} A.5.22", HIGH, ""),
        (O, "Material changes to supplier services in the period (new features, sub-processors, locations) were assessed for security impact.",
         "supplier_security (change assessments)", f"{_27001} A.5.22", HIGH, ""),
    ),
    "ISO.A5.23": _criteria(
        "ISO.A5.23",
        (D, "A cloud services policy or procedure covers selecting, using, managing and exiting cloud services, including security requirements and the shared-responsibility split.",
         "cloud_services; security_policy", f"{_27001} A.5.23", HIGH, _NEWCTRL),
        (O, "A register of cloud services in use exists, and each has provider assurance evidence (e.g. SOC 2 report, ISO certificate) reviewed in the period.",
         "cloud_services (register; assurance reports)", f"{_27001} A.5.23; {_27002} 5.23 (guidance)", MED, _NEWCTRL),
        (D, "An exit plan exists for critical cloud services, covering data return and deletion.",
         "cloud_services (exit plan)", f"{_27001} A.5.23", HIGH, _NEWCTRL),
    ),
})

_own("ISO.A5.24", "The organisation prepares in advance for security incidents by setting up, documenting and sharing its incident-handling process and who does what in it.")
_own("ISO.A5.25", "Reported security events are looked at against set criteria to decide whether each one is an incident that needs the incident process.")
_own("ISO.A5.26", "Security incidents are handled by following the organisation's written response procedures.")
_own("ISO.A5.27", "Lessons from past incidents are fed back into strengthening the organisation's security controls.")
_own("ISO.A5.28", "The organisation has procedures for finding, gathering and preserving evidence about security events so it stays usable for disciplinary or legal action.")
_own("ISO.A5.29", "The organisation plans how it will keep information protected at an acceptable level while business is disrupted.")
_own("ISO.A5.30", "IT services are prepared, maintained and tested so they can recover in line with business continuity targets.")
_own("ISO.A5.31", "The organisation knows and records the laws, regulations and contract terms that bear on its information security and how it meets each, and keeps that record current.")
_own("ISO.A5.32", "The organisation has procedures that protect intellectual property, including respecting software licences and copyright.")
_own("ISO.A5.33", "Records are kept safe from being lost, destroyed, altered, or seen or released without authority.")
_own("ISO.A5.34", "The organisation works out which privacy and personal-data obligations apply to it and meets them.")
_own("ISO.A5.35", "Someone independent of the area checks how the organisation manages information security, on a schedule and after major change.")
_own("ISO.A5.36", "The organisation regularly checks that its own security policies, rules and standards are actually being followed.")
_own("ISO.A5.37", "Step-by-step procedures for running IT facilities are written down and available to the staff who need them.")

ISO27001_CRITERIA_DRAFT.update({
    # ── Incident Management, Continuity & Compliance ──────────────────────
    "ISO.A5.24": _criteria(
        "ISO.A5.24",
        (D, "A documented incident management procedure covers detection, reporting, triage, response, communication and closure.",
         "breach_procedure", f"{_27001} A.5.24", HIGH, ""),
        (D, "Incident management roles (e.g. incident manager, response team, communications lead) are defined with named people and contact details.",
         "breach_procedure; roles_responsibilities", f"{_27001} A.5.24", HIGH, ""),
        (O, "The incident procedure and roles were communicated to those involved, and the plan was exercised (e.g. tabletop) in the last 12 months.",
         "breach_procedure (exercise records); training_records",
         f"{_27001} A.5.24 ('communicating'); exercising is {_27002} 5.24 (guidance)", MED, ""),
    ),
    "ISO.A5.25": _criteria(
        "ISO.A5.25",
        (D, "Written criteria define when a security event is classified as an incident, with severity or priority levels.",
         "breach_procedure (classification and severity matrix)", f"{_27001} A.5.25", HIGH, ""),
        (O, "For a sample of logged events, the record shows an assessment and a decision on whether each was an incident.",
         "incident_log (event triage records)", f"{_27001} A.5.25", HIGH, ""),
    ),
    "ISO.A5.26": _criteria(
        "ISO.A5.26",
        (D, "Response procedures cover containment, eradication, recovery, escalation and notification to internal and external parties.",
         "breach_procedure", f"{_27001} A.5.26; {_27002} 5.26 (guidance)", MED, ""),
        (O, "For a sample of incidents in the period, the incident record shows the documented steps were followed and the incident was closed.",
         "incident_log", f"{_27001} A.5.26", HIGH, ""),
        (O, "Where an incident triggered a legal or contractual notification duty, the record shows notification was made within the required time.",
         "incident_log; breach_procedure; legal_register", f"{_27002} 5.26 (guidance); {_27001} A.5.31", MED, ""),
    ),
    "ISO.A5.27": _criteria(
        "ISO.A5.27",
        (D, "The incident procedure requires a post-incident review for significant incidents.",
         "breach_procedure", f"{_27001} A.5.27; {_27002} 5.27 (guidance)", MED, ""),
        (O, "For significant incidents in the period, a post-incident review was recorded and at least one resulting control improvement was tracked to completion.",
         "incident_log (post-incident reviews); change_management or risk_assessment updates", f"{_27001} A.5.27", HIGH, ""),
    ),
    "ISO.A5.28": _criteria(
        "ISO.A5.28",
        (D, "A procedure covers identifying, collecting, acquiring and preserving evidence of security events, including chain of custody.",
         "breach_procedure (evidence handling section)", f"{_27001} A.5.28", HIGH, ""),
        (O, "Where evidence was collected in the period, a chain-of-custody or evidence-handling record exists.",
         "incident_log (evidence records)", f"{_27001} A.5.28; {_27002} 5.28 (guidance)", MED, ""),
    ),
    "ISO.A5.29": _criteria(
        "ISO.A5.29",
        (D, "Business continuity or crisis plans state how security controls are maintained, or which compensating controls apply, during disruption.",
         "business_continuity", f"{_27001} A.5.29", HIGH, ""),
        (O, "The last continuity test or real disruption record shows security requirements (e.g. access control, logging) were considered and kept in place.",
         "business_continuity (test reports)", f"{_27001} A.5.29; {_27002} 5.29 (guidance)", MED, ""),
    ),
    "ISO.A5.30": _criteria(
        "ISO.A5.30",
        (D, "Recovery time and recovery point objectives are defined for critical ICT services, derived from a business impact analysis.",
         "business_continuity (BIA; RTO/RPO table)", f"{_27001} A.5.30; {_27002} 5.30 (guidance)", MED, _NEWCTRL),
        (D, "ICT recovery or disaster recovery plans exist for the critical services.",
         "business_continuity (DR plans)", f"{_27001} A.5.30", HIGH, _NEWCTRL),
        (O, "The ICT recovery plans were tested in the last 12 months and test results compared against the recovery objectives, with gaps actioned.",
         "business_continuity (DR test reports)", f"{_27001} A.5.30 ('tested')", HIGH, _NEWCTRL),
    ),
    # ── Legal, Regulatory & Policy Compliance ─────────────────────────────
    "ISO.A5.31": _criteria(
        "ISO.A5.31",
        (D, "A compliance register lists every law, regulation and contract term that bears on the organisation's information security (e.g. data protection, sector rules, crypto export, customer contracts).",
         "legal_register", f"{_27001} A.5.31", HIGH, ""),
        (D, "For each listed requirement the register records how the organisation meets it (e.g. owner, control reference).",
         "legal_register", f"{_27001} A.5.31", HIGH, ""),
        (O, "The register has been reviewed and updated within the last 12 months or after a relevant legal change.",
         "legal_register (review history)", f"{_27001} A.5.31 ('kept up to date')", HIGH, ""),
    ),
    "ISO.A5.32": _criteria(
        "ISO.A5.32",
        (D, "A procedure addresses protection of intellectual property, including acquiring software only from legitimate sources and complying with licence terms.",
         "security_policy; legal_register", f"{_27001} A.5.32; {_27002} 5.32 (guidance)", MED, ""),
        (O, "A software licence reconciliation in the period shows installed or subscribed software is within licensed entitlements.",
         "software licence register; asset_inventory", f"{_27002} 5.32 (guidance)", MED, ""),
    ),
    "ISO.A5.33": _criteria(
        "ISO.A5.33",
        (D, "A records retention schedule defines record types, retention periods and storage requirements, reflecting legal and contractual needs.",
         "legal_register; records retention schedule", f"{_27001} A.5.33; {_27002} 5.33 (guidance)", MED, ""),
        (O, "For a sample of record types, storage settings protect them against deletion and tampering (e.g. access restrictions, immutability, backups) for the retention period.",
         "records retention schedule; backup; system configuration", f"{_27001} A.5.33", HIGH, ""),
    ),
    "ISO.A5.34": _criteria(
        "ISO.A5.34",
        (D, "A privacy or PII protection policy identifies the privacy laws and contractual terms that apply to the organisation's processing of personal data.",
         "privacy_policy; legal_register", f"{_27001} A.5.34", HIGH, ""),
        (D, "A person or role is responsible for privacy and PII protection (e.g. DPO or privacy lead).",
         "privacy_policy; roles_responsibilities", f"{_27002} 5.34 (guidance)", MED, ""),
        (O, "A current record of personal data processing (e.g. data inventory or processing register) exists for the ISMS scope.",
         "privacy_policy; data processing register", f"{_27001} A.5.34; {_27002} 5.34 (guidance)", MED, ""),
    ),
    "ISO.A5.35": _criteria(
        "ISO.A5.35",
        (D, "A plan sets when the approach to information security will be reviewed independently and what triggers an unscheduled review.",
         "isms_audit_reports (audit programme)", f"{_27001} A.5.35", HIGH, ""),
        (O, "An independent review (internal audit by someone outside the area, or external audit) was performed within the planned interval and its results were reported to management.",
         "isms_audit_reports", f"{_27001} A.5.35", HIGH, ""),
    ),
    "ISO.A5.36": _criteria(
        "ISO.A5.36",
        (D, "Managers or control owners are assigned to check compliance with the security policies and standards in their area, at a defined frequency.",
         "roles_responsibilities; isms_audit_reports", f"{_27001} A.5.36; {_27002} 5.36 (guidance)", MED, ""),
        (O, "Compliance reviews (e.g. control self-assessments, technical compliance scans) were performed in the period and non-compliances recorded with actions.",
         "isms_audit_reports (compliance review records); corrective action log", f"{_27001} A.5.36", HIGH, ""),
    ),
    "ISO.A5.37": _criteria(
        "ISO.A5.37",
        (D, "Operating procedures are documented for key IT activities (e.g. backups, system start-up and shutdown, user administration, monitoring).",
         "security_policy (operating procedures); backup", f"{_27001} A.5.37; {_27002} 5.37 (guidance)", MED, ""),
        (O, "The documented procedures are accessible to the personnel who need them (e.g. in a shared runbook or wiki) and are the current approved versions.",
         "operating procedures repository", f"{_27001} A.5.37", HIGH, ""),
    ),
})


# ══════════════════════════════════════════════════════════════════════════
# Annex A.6: People controls
# ══════════════════════════════════════════════════════════════════════════

_own("ISO.A6.1", "People are background-checked before they join and again later where warranted, to a depth that fits the law, the role and the sensitivity of what they will access.")
_own("ISO.A6.2", "Employment and engagement contracts spell out the security duties of both the individual and the organisation.")
_own("ISO.A6.3", "Staff and relevant outsiders receive security awareness and role-appropriate training, and are kept informed when security rules that affect their job change.")
_own("ISO.A6.4", "A formal, communicated disciplinary process exists for people who breach security policy.")
_own("ISO.A6.5", "Security duties that continue after someone leaves or changes role, such as confidentiality, are set out, communicated and enforced.")
_own("ISO.A6.6", "The organisation works out what confidentiality agreements it needs, documents them, keeps them current and gets staff and relevant outsiders to sign them.")
_own("ISO.A6.7", "Security measures protect the organisation's information when people work away from its premises.")
_own("ISO.A6.8", "People have a clear, timely route to report security events they notice or suspect.")

ISO27001_CRITERIA_DRAFT.update({
    # ── Screening & Employment ────────────────────────────────────────────
    "ISO.A6.1": _criteria(
        "ISO.A6.1",
        (D, "A screening procedure defines the background checks required before a person joins (e.g. identity, references, qualifications, criminal record where lawful).",
         "hr_security (screening procedure)", f"{_27001} A.6.1", HIGH, ""),
        (O, "For a sample of joiners in the period, records show the required checks were completed before the start date or before access was granted.",
         "hr_security (screening records)", f"{_27001} A.6.1", HIGH, ""),
        (D, "The procedure states when re-screening is performed (e.g. on promotion to a sensitive role or at a set interval).",
         "hr_security (screening procedure)",
         f"{_27001} A.6.1 (ongoing checks). The trigger and interval are not fixed by the control",
         MED, ""),
        (D, "The screening procedure scales the depth of checks to the role, the classification of information to be accessed and the perceived risk, and takes applicable law into account.",
         "hr_security (screening procedure)",
         f"{_27001} A.6.1 [repo description omits the legal and proportionality qualifiers of the control]",
         LOW, ""),
    ),
    "ISO.A6.2": _criteria(
        "ISO.A6.2",
        (D, "Employment and contractor agreement templates include information security responsibilities of the individual and the organisation.",
         "hr_security (contract templates)", f"{_27001} A.6.2", HIGH, ""),
        (O, "A sample of signed agreements for current staff and contractors contains the security terms.",
         "hr_security (signed contracts sample)", f"{_27001} A.6.2", HIGH, ""),
    ),
    "ISO.A6.3": _criteria(
        "ISO.A6.3",
        (D, "An awareness and training programme defines content, audiences (including role-specific training for technical and privileged roles) and frequency.",
         "training_records (training programme)", f"{_27001} A.6.3; {_27002} 6.3 (guidance)", MED, ""),
        (O, "Completion records show in-scope personnel completed the required awareness training within the defined period, with non-completers followed up.",
         "training_records (completion report)", f"{_27001} A.6.3", HIGH, ""),
        (O, "Personnel received updates when relevant policies or procedures changed in the period.",
         "training_records; internal communications record", f"{_27001} A.6.3", HIGH, ""),
    ),
    "ISO.A6.4": _criteria(
        "ISO.A6.4",
        (D, "A documented disciplinary process covers information security policy violations.",
         "hr_security (disciplinary procedure)", f"{_27001} A.6.4", HIGH, ""),
        (O, "The disciplinary process has been communicated to personnel (e.g. in the handbook, policy acknowledgement or training).",
         "hr_security; training_records", f"{_27001} A.6.4", HIGH, ""),
    ),
    "ISO.A6.5": _criteria(
        "ISO.A6.5",
        (D, "Contracts or leaver documents define security responsibilities that continue after termination or role change (e.g. confidentiality, return of information).",
         "hr_security (contract templates; leaver documents)", f"{_27001} A.6.5", HIGH, ""),
        (O, "For a sample of leavers, records show continuing obligations were communicated at exit (e.g. exit letter or signed acknowledgement).",
         "hr_security (leaver records)", f"{_27001} A.6.5", HIGH, ""),
    ),
    "ISO.A6.6": _criteria(
        "ISO.A6.6",
        (D, "Confidentiality or NDA templates exist for staff and for external parties, reflecting the organisation's protection needs.",
         "hr_security (NDA templates)", f"{_27001} A.6.6", HIGH, ""),
        (O, "Signed NDAs exist for a sample of staff, contractors and external parties with access to confidential information.",
         "hr_security (signed NDAs sample)", f"{_27001} A.6.6", HIGH, ""),
        (O, "The NDA templates have been reviewed within the organisation's defined review interval.",
         "hr_security (template version history)", f"{_27001} A.6.6 ('regularly reviewed')", HIGH, ""),
    ),
    # ── Remote Working & Reporting ────────────────────────────────────────
    "ISO.A6.7": _criteria(
        "ISO.A6.7",
        (D, "A remote working policy sets security requirements for work outside the premises (e.g. approved devices, secure connection, physical privacy, handling of printed material).",
         "remote_working_policy", f"{_27001} A.6.7; {_27002} 6.7 (guidance)", MED, ""),
        (O, "Technical enforcement for remote access is in place (e.g. VPN or zero-trust gateway with MFA, device compliance checks).",
         "remote_working_policy; access_control_policy; network_security", f"{_27001} A.6.7 ('implemented')", HIGH, ""),
    ),
    "ISO.A6.8": _criteria(
        "ISO.A6.8",
        (D, "A reporting channel for security events (e.g. email alias, portal, hotline) is defined and published to personnel.",
         "breach_procedure; security_policy", f"{_27001} A.6.8", HIGH, ""),
        (O, "The incident log contains events reported by personnel through the channel in the period, with timestamps showing timely reporting.",
         "incident_log", f"{_27001} A.6.8",
         MED, ""),
        (O, "Awareness material tells personnel what to report and how.",
         "training_records (awareness content)", f"{_27002} 6.8 (guidance)", MED, ""),
    ),
})


# ══════════════════════════════════════════════════════════════════════════
# Annex A.7: Physical controls
# ══════════════════════════════════════════════════════════════════════════

_own("ISO.A7.1", "The organisation marks out physical boundaries around places holding information and equipment and uses them to keep those places protected.")
_own("ISO.A7.2", "Entry to secure areas goes only through controlled access points that let authorised people in.")
_own("ISO.A7.3", "Offices, rooms and facilities are physically secured by design and in practice.")
_own("ISO.A7.4", "Premises are watched at all times for anyone getting in without permission.")
_own("ISO.A7.5", "Facilities are designed and fitted to withstand physical and environmental hazards such as fire, flood, storms and deliberate attack.")
_own("ISO.A7.6", "Extra rules govern how people behave and work inside secure areas.")
_own("ISO.A7.7", "Rules require papers and removable media to be cleared from desks and screens to be locked when unattended, and those rules are enforced.")
_own("ISO.A7.8", "Equipment is placed and protected so that it is shielded from environmental risk and unauthorised access.")
_own("ISO.A7.9", "Organisational assets taken off site are kept protected.")
_own("ISO.A7.10", "Storage media are controlled from purchase through use and transport to disposal, according to the classification of the data on them.")
_own("ISO.A7.11", "IT facilities keep running, or fail safely, when mains power, cooling or other supporting services break down.")
_own("ISO.A7.12", "Power and data cabling is protected against tapping, interference and damage.")
_own("ISO.A7.13", "Equipment is serviced properly so the information it handles stays available, accurate and confidential.")
_own("ISO.A7.14", "Devices with built-in storage are checked before being scrapped or reissued, to confirm that confidential data and licensed programs have been wiped or destroyed.")

ISO27001_CRITERIA_DRAFT.update({
    # ── Physical Perimeter & Access ───────────────────────────────────────
    "ISO.A7.1": _criteria(
        "ISO.A7.1",
        (D, "Physical security perimeters are defined for each in-scope site (e.g. building, floor, server room), with the protection required for each.",
         "physical_security (site plans; perimeter definitions)", f"{_27001} A.7.1", HIGH, ""),
        (O, "A site walkthrough or photo evidence confirms the defined perimeters exist as described (e.g. doors lock, no unprotected openings).",
         "physical_security (inspection records)", f"{_27001} A.7.1 ('used')", HIGH, ""),
        (D, "Where the organisation has no own premises in scope (fully remote or cloud-hosted), the SoA records this and relies on provider assurance for hosting facilities.",
         "statement_of_applicability; cloud_services (provider assurance reports)",
         f"{_27001} cl.6.1.3(d), A.7.1. How far provider reports can stand in for own perimeter controls is a judgment",
         LOW, ""),
    ),
    "ISO.A7.2": _criteria(
        "ISO.A7.2",
        (D, "Entry controls (e.g. badge readers, locks, reception) are defined for secure areas, with authorisation rules for who may enter.",
         "physical_security", f"{_27001} A.7.2", HIGH, ""),
        (O, "Visitor logs or access-control system records exist for the period, and visitors are recorded and escorted where required.",
         "physical_security (visitor logs; access system reports)", f"{_27001} A.7.2; {_27002} 7.2 (guidance)", MED, ""),
        (O, "Physical access rights to secure areas were reviewed in the period and leavers' badges deactivated.",
         "physical_security (access review records)", f"{_27002} 7.2 (guidance)", MED, ""),
    ),
    "ISO.A7.3": _criteria(
        "ISO.A7.3",
        (D, "Physical security measures for offices, rooms and facilities are specified (e.g. locks, restricted signage, no public indication of sensitive rooms).",
         "physical_security", f"{_27001} A.7.3; {_27002} 7.3 (guidance)", MED, ""),
        (O, "Inspection shows the specified measures are in place for sampled rooms holding sensitive information or equipment.",
         "physical_security (inspection records)", f"{_27001} A.7.3 ('implemented')", HIGH, ""),
    ),
    "ISO.A7.4": _criteria(
        "ISO.A7.4",
        (D, "Monitoring arrangements for unauthorised physical access are defined for premises (e.g. CCTV, intruder alarms, guards) with responsibility for responding.",
         "physical_security", f"{_27001} A.7.4", HIGH, _NEWCTRL),
        (O, "Monitoring systems were operational throughout the period (e.g. CCTV retention available, alarm test records, guard logs).",
         "physical_security (CCTV/alarm test records)",
         f"{_27001} A.7.4 ('continuously'). Whether small offices without CCTV can meet 'continuous' monitoring is a judgment",
         MED, _NEWCTRL),
    ),
    "ISO.A7.5": _criteria(
        "ISO.A7.5",
        (D, "A documented assessment of physical and environmental threats (e.g. fire, flood, power surge, civil unrest) exists for each in-scope site.",
         "physical_security; risk_assessment", f"{_27001} A.7.5; {_27002} 7.5 (guidance)", MED, ""),
        (O, "Protective measures identified by that assessment (e.g. fire suppression, water detection) are installed and have current maintenance or test records.",
         "physical_security (maintenance/test certificates)", f"{_27001} A.7.5", HIGH, ""),
    ),
    "ISO.A7.6": _criteria(
        "ISO.A7.6",
        (D, "Rules for working in secure areas are documented (e.g. no unsupervised third parties, no recording devices, areas locked when vacant).",
         "physical_security", f"{_27001} A.7.6; {_27002} 7.6 (guidance)", MED, ""),
        (O, "Personnel authorised for secure areas have been made aware of the rules (e.g. briefing record or signed acknowledgement).",
         "physical_security; training_records", f"{_27001} A.7.6 ('implemented')", MED, ""),
    ),
    "ISO.A7.7": _criteria(
        "ISO.A7.7",
        (D, "A clear desk and clear screen policy defines the rules for papers, removable media and unattended screens.",
         "remote_working_policy (clear desk / clear screen)", f"{_27001} A.7.7", HIGH, ""),
        (O, "Automatic screen lock after inactivity is enforced by configuration on endpoints.",
         "configuration_baselines; MDM policy export", f"{_27002} 7.7 (guidance)", MED, ""),
        (O, "Clear desk compliance was checked in the period (e.g. spot-check records) with findings followed up.",
         "physical_security (spot-check records)", f"{_27001} A.7.7 ('enforced')", HIGH, ""),
    ),
    # ── Equipment Security ────────────────────────────────────────────────
    "ISO.A7.8": _criteria(
        "ISO.A7.8",
        (D, "Siting requirements for equipment are defined (e.g. servers in locked racks or rooms, screens not overlooked, protection from environmental hazards).",
         "physical_security", f"{_27001} A.7.8; {_27002} 7.8 (guidance)", MED, ""),
        (O, "Inspection of sampled equipment locations confirms the siting requirements are met.",
         "physical_security (inspection records)", f"{_27001} A.7.8", HIGH, ""),
    ),
    "ISO.A7.9": _criteria(
        "ISO.A7.9",
        (D, "Rules for protecting assets off-premises are documented (e.g. not left unattended, carried as hand luggage, authorisation to remove).",
         "remote_working_policy", f"{_27001} A.7.9; {_27002} 7.9 (guidance)", MED, ""),
        (O, "Portable devices used off-site have full-disk encryption and remote wipe enabled, per MDM or endpoint reports.",
         "remote_working_policy; MDM compliance report", f"{_27001} A.7.9; {_27002} 7.9 (guidance)", MED, ""),
    ),
    "ISO.A7.10": _criteria(
        "ISO.A7.10",
        (D, "A media handling procedure covers acquisition, use, transport, storage and disposal of removable and other storage media according to classification.",
         "media_disposal", f"{_27001} A.7.10", HIGH, ""),
        (O, "Technical controls restrict or encrypt removable media on endpoints in line with the procedure.",
         "configuration_baselines; endpoint policy export", f"{_27002} 7.10 (guidance)", MED, ""),
        (O, "Media disposals in the period are recorded (e.g. destruction certificates or disposal log).",
         "media_disposal (disposal log / certificates)", f"{_27001} A.7.10", HIGH, ""),
    ),
    "ISO.A7.11": _criteria(
        "ISO.A7.11",
        (D, "Supporting utilities for critical facilities (power, cooling, telecoms) have protection defined (e.g. UPS, generator, redundant feeds).",
         "physical_security; business_continuity", f"{_27001} A.7.11", HIGH, ""),
        (O, "UPS, generator or equivalent equipment has current maintenance and test records.",
         "physical_security (maintenance/test records)", f"{_27002} 7.11 (guidance)", MED, ""),
    ),
    "ISO.A7.12": _criteria(
        "ISO.A7.12",
        (D, "Cabling protection requirements are defined (e.g. cabling in conduits or locked cabinets, separation of power and data, patch panels in secured rooms).",
         "physical_security", f"{_27001} A.7.12; {_27002} 7.12 (guidance)", MED, ""),
        (O, "Inspection of sampled cabling and comms rooms confirms the requirements are met.",
         "physical_security (inspection records)", f"{_27001} A.7.12", HIGH, ""),
    ),
    "ISO.A7.13": _criteria(
        "ISO.A7.13",
        (D, "Maintenance requirements and schedules are defined for in-scope equipment, following supplier recommendations.",
         "maintenance schedule; asset_inventory", f"{_27001} A.7.13; {_27002} 7.13 (guidance)", MED, ""),
        (O, "Maintenance records show scheduled maintenance was performed by authorised personnel, and equipment sent off-site for repair was cleared of sensitive data or protected.",
         "maintenance records", f"{_27001} A.7.13; {_27002} 7.13 (guidance)", MED, ""),
    ),
    "ISO.A7.14": _criteria(
        "ISO.A7.14",
        (D, "A procedure requires equipment containing storage media to be checked, and data and licensed software removed or securely overwritten, before disposal or reuse.",
         "media_disposal", f"{_27001} A.7.14", HIGH, ""),
        (O, "For a sample of disposed or reissued devices, records show verified wiping or destruction (e.g. wipe report, destruction certificate).",
         "media_disposal (wipe reports; destruction certificates); asset_inventory", f"{_27001} A.7.14", HIGH, ""),
    ),
})


# ══════════════════════════════════════════════════════════════════════════
# Annex A.8: Technological controls
# ══════════════════════════════════════════════════════════════════════════

_own("ISO.A8.1", "Laptops, phones and other user devices, and the information on or reachable through them, are kept protected.")
_own("ISO.A8.2", "Administrator and other high-power access is handed out sparingly and its use is controlled.")
_own("ISO.A8.3", "Systems enforce the access-control policy so people reach only the information and functions they are allowed.")
_own("ISO.A8.4", "Permission to view or modify source code, developer tooling and software libraries is granted and controlled on a need basis.")
_own("ISO.A8.5", "Log-in methods and technologies are strong enough for the sensitivity of what they protect, as the access policy requires.")
_own("ISO.A8.6", "The organisation tracks how much of its computing, storage and network capacity is used and adjusts it to meet present and forecast demand.")
_own("ISO.A8.7", "Defences against malicious software are in place and backed up by making users aware of the threat.")
_own("ISO.A8.8", "The organisation learns about weaknesses in the technology it runs, judges how exposed it is, and acts on them.")
_own("ISO.A8.9", "The organisation defines, records, applies and keeps checking the approved settings of its hardware, software, services and networks, security settings included.")
_own("ISO.A8.10", "Information held in systems, devices or media is erased once it is no longer needed.")
_own("ISO.A8.11", "Sensitive data is hidden or obscured, for example by masking or pseudonymisation, where access policy, business need and the law call for it.")
_own("ISO.A8.12", "Measures are in place on systems, networks and devices to detect and stop sensitive information leaving without authority.")
_own("ISO.A8.13", "The organisation keeps spare copies of its data, software and systems as its backup policy requires, and proves at regular intervals that they can be restored.")
_own("ISO.A8.14", "Enough duplicate capacity is built into IT facilities to meet the organisation's uptime needs.")
_own("ISO.A8.15", "Systems record activities, errors, faults and other significant events, and those records are kept, protected and reviewed.")
_own("ISO.A8.16", "Networks, systems and applications are watched for unusual behaviour and suspicious findings are followed up as possible incidents.")
_own("ISO.A8.17", "System clocks are set from agreed reference time sources so that timestamps line up.")
_own("ISO.A8.18", "Tools that can bypass system and application safeguards are available only to a few people and their use is closely controlled.")
_own("ISO.A8.19", "Installing software on live systems is done securely through defined procedures and measures.")
_own("ISO.A8.20", "The organisation hardens, administers and governs its networks and network equipment so that the data carried over them stays safe.")
_own("ISO.A8.21", "For each network service, the security features, service levels and requirements are defined, put in place and monitored.")
_own("ISO.A8.22", "The network is divided so that different groups of services, users and systems are kept apart.")
_own("ISO.A8.23", "The organisation controls which external websites people can reach, to reduce the risk of picking up malicious content.")
_own("ISO.A8.24", "The organisation defines and follows rules for using encryption effectively, including how cryptographic keys are managed.")
_own("ISO.A8.25", "The organisation sets and follows rules for building software and systems securely.")
_own("ISO.A8.26", "Security needs are worked out, written down and approved whenever an application is built or bought.")
_own("ISO.A8.27", "The organisation has documented, maintained principles for designing systems securely and applies them to all system development.")
_own("ISO.A8.28", "Developers follow secure coding principles when writing software.")
_own("ISO.A8.29", "Security testing is defined and carried out as part of the development life cycle, including before acceptance.")
_own("ISO.A8.30", "When system development is outsourced, the organisation steers, monitors and reviews the supplier's work.")
_own("ISO.A8.31", "Separate environments are kept for building, testing and running systems, each with its own safeguards.")
_own("ISO.A8.32", "Every change to IT facilities and systems follows the organisation's controlled change process.")
_own("ISO.A8.33", "Data used for testing is chosen with care, protected and managed.")
_own("ISO.A8.34", "Before anyone audits or tests live systems, the scope and timing are worked out and signed off with the managers responsible, so the testing does not disrupt the business.")

ISO27001_CRITERIA_DRAFT.update({
    # ── Technical Access Control & Authentication ─────────────────────────
    "ISO.A8.1": _criteria(
        "ISO.A8.1",
        (D, "An endpoint device policy sets security requirements for user devices (e.g. registration, encryption, screen lock, patching, anti-malware, remote wipe), including personally owned devices if allowed.",
         "remote_working_policy (endpoint / BYOD policy)", f"{_27001} A.8.1; {_27002} 8.1 (guidance)", MED, ""),
        (O, "Device management or endpoint reports show in-scope devices meet the required settings (e.g. disk encryption on, OS within support).",
         "MDM / endpoint compliance report", f"{_27001} A.8.1", HIGH, ""),
    ),
    "ISO.A8.2": _criteria(
        "ISO.A8.2",
        (D, "The access policy requires privileged access to be authorised separately, limited to those who need it, and held in accounts separate from everyday user accounts.",
         "access_control_policy", f"{_27001} A.8.2; {_27002} 8.2 (guidance)", MED, ""),
        (O, "A current list of privileged accounts exists for in-scope systems and each holder has a recorded authorisation.",
         "access_control_policy (privileged account list; approvals)", f"{_27001} A.8.2", HIGH, ""),
        (O, "Privileged access was reviewed in the period, more often than standard access if the policy says so, with unneeded rights removed.",
         "access_control_policy (privileged access review records)", f"{_27001} A.8.2 ('managed'); {_27002} 8.2 (guidance)", MED, ""),
    ),
    "ISO.A8.3": _criteria(
        "ISO.A8.3",
        (D, "Applications and systems in scope have access controls configured by role or group in line with the access-control policy.",
         "access_control_policy; system role matrices", f"{_27001} A.8.3", HIGH, ""),
        (O, "Testing a sample of users shows they cannot reach information or functions outside their authorised role.",
         "system access listings; assessor test results", f"{_27001} A.8.3", HIGH, ""),
    ),
    "ISO.A8.4": _criteria(
        "ISO.A8.4",
        (D, "Rules define who may read and write source code repositories, build tools and software libraries.",
         "sdlc_policy; access_control_policy", f"{_27001} A.8.4", HIGH, ""),
        (O, "Repository permissions show write access is limited to authorised developers and protected branches require review before merge.",
         "sdlc_policy; repository permission export", f"{_27001} A.8.4; {_27002} 8.4 (guidance)", MED, ""),
    ),
    "ISO.A8.5": _criteria(
        "ISO.A8.5",
        (D, "The access policy sets authentication strength by system sensitivity (e.g. multi-factor authentication for remote, privileged and sensitive-data access).",
         "access_control_policy", f"{_27001} A.8.5; {_27002} 8.5 (guidance)", MED, ""),
        (O, "Identity provider or system configuration shows the required authentication methods are enforced for the sampled systems.",
         "access_control_policy; identity provider configuration export", f"{_27001} A.8.5", HIGH, ""),
        (O, "Log-on protections are configured, such as lockout or throttling after failed attempts and no display of passwords.",
         "configuration_baselines; identity provider configuration export", f"{_27002} 8.5 (guidance)", MED, ""),
    ),
    # ── Operational & Network Security ────────────────────────────────────
    "ISO.A8.6": _criteria(
        "ISO.A8.6",
        (D, "Capacity requirements and utilisation thresholds are defined for critical systems.",
         "capacity plan; logging_monitoring", f"{_27001} A.8.6; {_27002} 8.6 (guidance)", MED, ""),
        (O, "Resource use is monitored and alerts or reviews in the period led to capacity adjustments where thresholds were approached.",
         "logging_monitoring (capacity dashboards / alerts); change_management", f"{_27001} A.8.6", HIGH, ""),
    ),
    "ISO.A8.7": _criteria(
        "ISO.A8.7",
        (D, "A malware protection standard defines the required protection (e.g. endpoint detection, email and download scanning) for each system type.",
         "configuration_baselines (malware protection standard)", f"{_27001} A.8.7", HIGH, ""),
        (O, "Endpoint and server reports show protection installed, active and up to date on in-scope systems, with exceptions justified.",
         "configuration_baselines; EDR / anti-malware console report", f"{_27001} A.8.7", HIGH, ""),
        (O, "Awareness material covers malware risks (e.g. phishing, suspicious attachments) and was delivered in the period.",
         "training_records", f"{_27001} A.8.7", HIGH, ""),
    ),
    "ISO.A8.8": _criteria(
        "ISO.A8.8",
        (D, "A vulnerability management procedure names the sources of vulnerability information, how exposure is assessed and the remediation deadlines by severity.",
         "vulnerability_management", f"{_27001} A.8.8", HIGH, ""),
        (O, "Vulnerability scans or equivalent assessments of in-scope systems were run in the period at the frequency the procedure sets.",
         "vulnerability_management (scan reports)", f"{_27001} A.8.8; {_27002} 8.8 (guidance)", MED, ""),
        (O, "A sample of critical and high findings was remediated within the defined deadlines, or has a recorded risk acceptance.",
         "vulnerability_management (remediation tracking); risk_assessment", f"{_27001} A.8.8", HIGH, ""),
        (O, "Penetration testing of internet-facing systems was performed in the last 12 months and findings tracked to closure.",
         "vulnerability_management; application_security_testing (pentest reports)",
         f"{_27002} 8.8 (guidance). Not an express requirement; frequency is practice",
         MED, ""),
    ),
    "ISO.A8.9": _criteria(
        "ISO.A8.9",
        (D, "Documented secure configuration baselines exist for each in-scope technology type (e.g. OS, database, cloud account, network device).",
         "configuration_baselines", f"{_27001} A.8.9", HIGH, _NEWCTRL),
        (O, "Configuration monitoring (e.g. CSPM, compliance scans) shows in-scope systems are checked against the baselines and drift is remediated.",
         "configuration_baselines; compliance scan report", f"{_27001} A.8.9 ('monitored')", HIGH, _NEWCTRL),
        (O, "The baselines have been reviewed within their defined review interval.",
         "configuration_baselines (version history)", f"{_27001} A.8.9 ('reviewed')", HIGH, _NEWCTRL),
    ),
    "ISO.A8.10": _criteria(
        "ISO.A8.10",
        (D, "A retention and deletion procedure states when information in systems, devices and media must be deleted and the deletion method.",
         "media_disposal; records retention schedule", f"{_27001} A.8.10", HIGH, _NEWCTRL),
        (O, "Records show deletions were performed in the period in line with the schedule (e.g. automated deletion jobs, deletion logs, supplier deletion confirmations).",
         "media_disposal (deletion logs); supplier_security (deletion confirmations)", f"{_27001} A.8.10", HIGH, _NEWCTRL),
    ),
    "ISO.A8.11": _criteria(
        "ISO.A8.11",
        (D, "A policy or standard states which data must be masked, pseudonymised or anonymised, in which contexts (e.g. non-production, support screens, reports), and the technique to use.",
         "access_control_policy; privacy_policy; sdlc_policy", f"{_27001} A.8.11", HIGH, _NEWCTRL),
        (O, "A sample of non-production datasets or user interfaces shows masking applied as the standard requires.",
         "test data samples; application screenshots", f"{_27001} A.8.11", HIGH, _NEWCTRL),
    ),
    "ISO.A8.12": _criteria(
        "ISO.A8.12",
        (D, "The organisation has identified the sensitive information to protect from leakage and the channels through which it could leak (e.g. email, uploads, removable media, printing).",
         "asset_inventory (classification scheme); security_policy", f"{_27001} A.8.12; {_27002} 8.12 (guidance)", MED, _NEWCTRL),
        (O, "Data leakage prevention measures (e.g. DLP rules, upload and USB blocking, sharing restrictions) are configured on the identified channels.",
         "DLP / endpoint configuration export", f"{_27001} A.8.12", HIGH, _NEWCTRL),
        (O, "DLP alerts in the period were reviewed and acted on.",
         "DLP alert log; incident_log", f"{_27002} 8.12 (guidance)", MED, _NEWCTRL),
    ),
    "ISO.A8.13": _criteria(
        "ISO.A8.13",
        (D, "A topic-specific backup policy sets scope, frequency, retention, storage location (including offsite or isolated copies) and protection of backups.",
         "backup", f"{_27001} A.8.13; {_27002} 8.13 (guidance)", MED, ""),
        (O, "Backup job logs for the period show backups ran as the policy requires, with failures investigated.",
         "backup (job logs)", f"{_27001} A.8.13 ('maintained')", HIGH, ""),
        (O, "Restore tests were performed at the frequency the policy sets and results recorded.",
         "backup (restore test records)", f"{_27001} A.8.13 ('regularly tested')", HIGH, ""),
    ),
    "ISO.A8.14": _criteria(
        "ISO.A8.14",
        (D, "Availability requirements are defined for critical systems and the redundancy design meeting them is documented (e.g. multi-zone deployment, failover links).",
         "business_continuity; network_security (architecture diagram)", f"{_27001} A.8.14", HIGH, ""),
        (O, "Failover of redundant components was tested in the last 12 months, or observed in a real event, and worked.",
         "business_continuity (failover test records)", f"{_27002} 8.14 (guidance)", MED, ""),
    ),
    # ── Logging, Monitoring & Cryptography ────────────────────────────────
    "ISO.A8.15": _criteria(
        "ISO.A8.15",
        (D, "A logging standard defines which events are logged for each system type (e.g. authentication, privileged actions, errors, security events) and how long logs are kept.",
         "logging_monitoring", f"{_27001} A.8.15; {_27002} 8.15 (guidance)", MED, ""),
        (O, "Sampled in-scope systems produce the defined logs and forward them to central storage.",
         "logging_monitoring (SIEM source list; sample logs)", f"{_27001} A.8.15 ('produced, stored')", HIGH, ""),
        (O, "Logs are protected from tampering and unauthorised access (e.g. restricted access, write-once storage), including from administrators of the logged systems.",
         "logging_monitoring; storage configuration", f"{_27001} A.8.15 ('protected'); {_27002} 8.15 (guidance)", MED, ""),
        (O, "Logs were analysed in the period (e.g. alert rules, periodic log reviews) with records of the review.",
         "logging_monitoring (review records)", f"{_27001} A.8.15 ('analysed')", HIGH, ""),
    ),
    "ISO.A8.16": _criteria(
        "ISO.A8.16",
        (D, "Monitoring covers networks, systems and applications in scope and defines what is anomalous (e.g. baselines, alert rules) and who responds.",
         "logging_monitoring", f"{_27001} A.8.16", HIGH, _NEWCTRL),
        (O, "Alerts raised in the period were triaged and, where warranted, passed to the incident process.",
         "logging_monitoring (alert records); incident_log", f"{_27001} A.8.16", HIGH, _NEWCTRL),
    ),
    "ISO.A8.17": _criteria(
        "ISO.A8.17",
        (D, "A standard names the approved reference time source(s) for in-scope systems.",
         "logging_monitoring; configuration_baselines", f"{_27001} A.8.17", HIGH, ""),
        (O, "A sample of systems is configured to synchronise with the approved source (e.g. NTP settings or cloud-provider time service).",
         "configuration_baselines; system configuration export", f"{_27001} A.8.17", HIGH, ""),
    ),
    "ISO.A8.18": _criteria(
        "ISO.A8.18",
        (D, "Utility programs able to override system or application controls are identified and their use is limited to named, authorised people.",
         "access_control_policy; configuration_baselines", f"{_27001} A.8.18", HIGH, ""),
        (O, "Use of such utilities is logged, and the logs or authorisations for a sample of uses exist.",
         "logging_monitoring; access_control_policy", f"{_27002} 8.18 (guidance)", MED, ""),
    ),
    "ISO.A8.19": _criteria(
        "ISO.A8.19",
        (D, "A procedure controls software installation on operational systems (who may install, from which approved sources, with what testing and approval).",
         "change_management", f"{_27001} A.8.19", HIGH, ""),
        (O, "Technical restrictions prevent unauthorised software installation on servers and endpoints (e.g. no local admin, application allow-listing, deployment only via pipeline).",
         "configuration_baselines; MDM / endpoint policy export", f"{_27001} A.8.19; {_27002} 8.19 (guidance)", MED, ""),
    ),
    "ISO.A8.20": _criteria(
        "ISO.A8.20",
        (D, "A network security standard defines how networks and network devices are secured and managed (e.g. firewall rules, device hardening, admin access, encryption in transit).",
         "network_security", f"{_27001} A.8.20", HIGH, ""),
        (D, "An up-to-date network diagram covers the in-scope environment, including cloud networks and connections to third parties.",
         "network_security (architecture diagram)", f"{_27002} 8.20 (guidance)", MED, ""),
        (O, "Firewall and security group rules were reviewed in the period, with unneeded or overly permissive rules removed.",
         "network_security (rule review records)", f"{_27001} A.8.20 ('managed and controlled')", HIGH, ""),
    ),
    "ISO.A8.21": _criteria(
        "ISO.A8.21",
        (D, "For each network service used (e.g. ISP links, CDN, DNS, VPN, SD-WAN), the security features, service levels and requirements are documented, in contracts where provided externally.",
         "network_security; supplier_security (network service agreements)", f"{_27001} A.8.21", HIGH, ""),
        (O, "Network service performance and security are monitored against the agreed levels (e.g. SLA reports reviewed).",
         "network_security; supplier_security (SLA reports)", f"{_27001} A.8.21 ('monitored')", HIGH, ""),
    ),
    "ISO.A8.22": _criteria(
        "ISO.A8.22",
        (D, "The network design defines segments by trust level or function (e.g. production, development, corporate, guest, management) and the traffic allowed between them.",
         "network_security (segmentation standard; diagram)", f"{_27001} A.8.22", HIGH, ""),
        (O, "Firewall, VLAN or security group configuration enforces the defined segmentation for sampled segments.",
         "network_security (configuration export)", f"{_27001} A.8.22", HIGH, ""),
    ),
    "ISO.A8.23": _criteria(
        "ISO.A8.23",
        (D, "A policy defines which categories of external website are blocked and how access to them is managed.",
         "network_security; security_policy", f"{_27001} A.8.23; {_27002} 8.23 (guidance)", MED, _NEWCTRL),
        (O, "A web filtering control (e.g. secure web gateway, DNS filtering, endpoint agent) is active for in-scope users, including remote users.",
         "network_security (filtering configuration / report)", f"{_27001} A.8.23", HIGH, _NEWCTRL),
    ),
    "ISO.A8.24": _criteria(
        "ISO.A8.24",
        (D, "A cryptography policy defines where encryption is required (at rest and in transit, by classification) and which algorithms and key lengths are approved.",
         "cryptography_policy", f"{_27001} A.8.24", HIGH, ""),
        (D, "Key management rules cover generation, storage, distribution, rotation, revocation and destruction of keys, and who may access them.",
         "cryptography_policy", f"{_27001} A.8.24", HIGH, ""),
        (O, "Configuration of sampled data stores and endpoints shows encryption enabled as the policy requires (e.g. storage encryption, TLS versions).",
         "cryptography_policy; system configuration export", f"{_27001} A.8.24 ('implemented')", HIGH, ""),
        (O, "Key management records show keys are held in a controlled store (e.g. KMS, HSM) and rotated as the policy requires.",
         "cryptography_policy; KMS configuration export", f"{_27001} A.8.24", HIGH, ""),
    ),
    # ── Secure Development & Testing ──────────────────────────────────────
    "ISO.A8.25": _criteria(
        "ISO.A8.25",
        (D, "A secure development policy sets security rules for each life-cycle phase (requirements, design, coding, testing, release).",
         "sdlc_policy", f"{_27001} A.8.25", HIGH, ""),
        (O, "A sample of releases in the period shows the required security steps were completed (e.g. security review, SAST scan, approval gate).",
         "sdlc_policy; change_management (release records)", f"{_27001} A.8.25 ('applied')", HIGH, ""),
    ),
    "ISO.A8.26": _criteria(
        "ISO.A8.26",
        (D, "The development and procurement processes require security requirements to be identified and approved for new or changed applications, including acquired and SaaS applications.",
         "application_security_testing; sdlc_policy", f"{_27001} A.8.26", HIGH, ""),
        (O, "For a sample of applications built or acquired in the period, a documented and approved set of security requirements exists.",
         "application_security_testing (requirements records)", f"{_27001} A.8.26", HIGH, ""),
    ),
    "ISO.A8.27": _criteria(
        "ISO.A8.27",
        (D, "Secure engineering principles (e.g. defence in depth, least privilege, secure defaults, zero trust) are documented and kept current.",
         "application_security_testing; sdlc_policy (architecture principles)", f"{_27001} A.8.27", HIGH, ""),
        (O, "Design or architecture reviews for a sample of development activities in the period record that the principles were applied.",
         "application_security_testing (architecture review records)", f"{_27001} A.8.27 ('applied')", HIGH, ""),
    ),
    "ISO.A8.28": _criteria(
        "ISO.A8.28",
        (D, "A secure coding standard exists (e.g. covering input validation, output encoding, secrets handling, dependency management) and applies to in-house and outsourced code.",
         "sdlc_policy (secure coding standard)", f"{_27001} A.8.28; {_27002} 8.28 (guidance)", MED, _NEWCTRL),
        (O, "Code review or automated scanning (e.g. SAST, dependency or secret scanning) runs on code changes and findings are addressed before release.",
         "sdlc_policy; CI pipeline configuration and scan results", f"{_27001} A.8.28 ('applied')", HIGH, _NEWCTRL),
        (O, "Developers received secure coding training in the last 12 months.",
         "training_records", f"{_27002} 8.28 (guidance)", MED, _NEWCTRL),
    ),
    "ISO.A8.29": _criteria(
        "ISO.A8.29",
        (D, "A security testing process defines the tests required at each life-cycle stage and the acceptance criteria before go-live.",
         "application_security_testing; sdlc_policy", f"{_27001} A.8.29", HIGH, ""),
        (O, "For a sample of new or significantly changed systems, security test results and an acceptance sign-off exist before production release.",
         "application_security_testing (test reports; acceptance records)", f"{_27001} A.8.29 ('implemented')", HIGH, ""),
    ),
    "ISO.A8.30": _criteria(
        "ISO.A8.30",
        (D, "Contracts for outsourced development set security requirements (e.g. secure coding, testing evidence, IP and code ownership, right to audit).",
         "outsourced_development (contracts)", f"{_27001} A.8.30; {_27002} 8.30 (guidance)", MED, ""),
        (O, "Records show the organisation monitored and reviewed the outsourced work in the period (e.g. code reviews, test evidence received, progress meetings).",
         "outsourced_development (oversight records)", f"{_27001} A.8.30", HIGH, ""),
    ),
    "ISO.A8.31": _criteria(
        "ISO.A8.31",
        (D, "Development, test and production environments are defined as separate (e.g. separate accounts, subscriptions or networks) with rules for promoting changes between them.",
         "sdlc_policy (environment separation)", f"{_27001} A.8.31", HIGH, ""),
        (O, "Access configuration shows developers do not have standing write access to production, or such access is approved and logged.",
         "access_control_policy; cloud IAM export", f"{_27002} 8.31 (guidance)", MED, ""),
        (O, "Non-production environments are secured to the level of the data they hold (e.g. access control, no unmasked production data without approval).",
         "sdlc_policy; configuration_baselines", f"{_27001} A.8.31 ('secured')", HIGH, ""),
    ),
    "ISO.A8.32": _criteria(
        "ISO.A8.32",
        (D, "A change management procedure covers recording, impact and risk assessment, authorisation, testing, rollback planning and communication of changes.",
         "change_management", f"{_27001} A.8.32; {_27002} 8.32 (guidance)", MED, ""),
        (O, "For a sample of production changes in the period, records show authorisation before implementation and testing evidence.",
         "change_management (change records)", f"{_27001} A.8.32", HIGH, ""),
        (O, "Emergency changes in the period were recorded and retrospectively reviewed and approved.",
         "change_management (emergency change records)", f"{_27002} 8.32 (guidance)", MED, ""),
    ),
    "ISO.A8.33": _criteria(
        "ISO.A8.33",
        (D, "Rules govern selection and use of test data, requiring production or personal data to be masked or explicitly authorised before use in testing.",
         "sdlc_policy (test data rules)", f"{_27001} A.8.33; {_27002} 8.33 (guidance)", MED, ""),
        (O, "For any production data copied to test environments in the period, an authorisation record exists and the copy was deleted after testing.",
         "sdlc_policy; test data authorisation and deletion records", f"{_27002} 8.33 (guidance)", MED, ""),
    ),
    "ISO.A8.34": _criteria(
        "ISO.A8.34",
        (D, "A procedure requires audit and assurance tests on operational systems (e.g. penetration tests, audit queries) to be planned and approved by responsible management before they start.",
         "isms_audit_reports; application_security_testing (test authorisation procedure)", f"{_27001} A.8.34", HIGH, ""),
        (O, "For tests performed on live systems in the period, a signed rules-of-engagement or authorisation record exists.",
         "application_security_testing (rules of engagement); isms_audit_reports", f"{_27001} A.8.34", HIGH, ""),
    ),
})
