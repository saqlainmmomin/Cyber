# UCF review triage (Saqlain's comments, 13 Oct export)

Read-only analysis. Nothing in the repo was edited. Data read: `docs/ucf/drafts/*`, the kickoff Results, `make_review_html.py`, the signed criteria modules (counts only), `iso27001.py` scope questions. Current state = after the 13 Oct role-neutral rewrite of all 195 statements.

## A. His 35 CHANGE controls

### A.0 Result

| Verdict | Count | Ids |
|---|---|---|
| RESOLVED (problem gone in current text) | 30 | all GOV, RSK and AST ids in the table A.1 |
| STILL OPEN (small wording fix) | 3 | UC-GOV-08 (real), UC-RSK-02, UC-RSK-42 (minor) |
| NEW WORK (his content ask beyond the role point) | 2 | UC-GOV-14 (scope and a new slot), UC-RSK-10 (rewrite) |

Finding: not one of the 35 statements names a role from `roles.csv` or the word CISO any more. The validator (CHECK 2) enforces this on statements. His comments were made on the page before the rewrite. One point to tell him: the **owner_role badge on each card still says CISO, Risk and Compliance Manager, Head of IT Operations**. That field is meant to hold a role. If he reads the badge as "the control is managed and signed off by a CISO" (UC-GOV-04), the answer is: it is only the default accountable function for routing, never part of the requirement. If he dislikes it, the cheapest fix is to hide `owner_role` on the sign-off cards.

### A.1 RESOLVED (30)

Proof is the current first sentence of each statement. None names a role.

| Id | Title | Current statement, first sentence (proof) | Note |
|---|---|---|---|
| UC-GOV-01 | Internal and external issues | A register of the internal and external issues that affect the organization's security outcomes is kept, including climate change where it is relevant. |  |
| UC-GOV-02 | Interested parties and their requirements | A register is kept of the parties with a stake in security, such as customers, regulators, partners and staff. |  |
| UC-GOV-03 | Scope of the security program | The scope of the security program is defined and documented, covering its boundaries and where it applies. |  |
| UC-GOV-04 | Security management system operated | A security management system is established, run and maintained, with defined processes and the way they interact. |  |
| UC-GOV-07 | Security roles and responsibilities | Security roles, responsibilities and authorities are defined and each is assigned to a named, current person. | "named person" is the subject of the control (harmless) |
| UC-GOV-09 | Specialist security forums | A record is kept of the specialist security forums and professional groups the organization joins or follows. |  |
| UC-GOV-10 | Risks and opportunities of the program | The risks and opportunities that bear on the security program are determined, actions for them are planned, and those actions are built into program processes. |  |
| UC-GOV-11 | Security objectives | Measurable security objectives are set at relevant functions, consistent with policy. |  |
| UC-GOV-12 | Planned changes to the program | Any needed change to the security management system is carried out in a planned way. |  |
| UC-GOV-13 | Resources for the program | The resources needed to establish, run, maintain and improve the security program are determined and provided, including people, budget and tools. | "Top management" appears only in good_looks_like |
| UC-GOV-15 | Documented information control | The documented information the security program needs is kept, and how it is created, approved, updated, distributed, protected, retained and disposed of is controlled. |  |
| UC-GOV-16 | Operational planning and control | The processes needed to meet security requirements and carry out treatment actions are planned, run and controlled, with set criteria for those processes. | D11 split list (see C) |
| UC-GOV-17 | Performance monitoring and measurement | What security performance to measure is decided, with methods that give valid, comparable and reproducible results, and when and by whom it is measured. |  |
| UC-GOV-19 | Continual improvement | The suitability, adequacy and effectiveness of the security program are continually improved. |  |
| UC-GOV-20 | Nonconformity and corrective action | Each nonconformity is controlled and corrected, and its consequences are dealt with. |  |
| UC-GOV-40 | Mission and business context | The organization's mission and business context, including the services it delivers, are documented and approved by leadership. | "leadership" generic, as D13 |
| UC-GOV-41 | Risk direction communicated to those who act on it | The risk direction, the risk method, security roles and planned risk responses are delivered to the people who must act on them. | D11: KEEP |
| UC-GOV-42 | Security test and exercise program | A program of security tests and exercises, such as penetration tests, tabletop exercises and recovery tests, is planned and scheduled, and includes critical suppliers and relevant third parties where it matters. |  |
| UC-GOV-70 | Personal data inside security coverage | The security policies and safeguards cover all personal data the organization holds or controls, including data that other parties process on its behalf. |  |
| UC-RSK-01 | Risk assessment method | A repeatable risk assessment method is defined, with acceptance criteria and criteria for performing assessments. | "risk owners" assigned: subject (harmless) |
| UC-RSK-03 | Statement of applicable controls | A documented statement of applicable controls is kept. |  |
| UC-RSK-04 | Risk assessments performed | Risk assessments are performed at planned intervals and when significant change is proposed or occurs. |  |
| UC-RSK-05 | Risk treatment carried out | The risk treatment plan is carried out and the results are kept. |  |
| UC-RSK-40 | Risk appetite, tolerance and response direction | Leadership approves a risk appetite statement, and it is turned into measurable tolerance limits, such as a maximum acceptable downtime or highest acceptable residual rating. | "Leadership approves" generic, as D13 |
| UC-RSK-41 | Integration with enterprise risk management | Cybersecurity and supply chain risks sit in the same enterprise risk process and register as other enterprise risks, and are assessed by a method that covers supplier risk. | D11 split list |
| UC-RSK-43 | Threat identification and register | The risk method requires internal and external threats, including insiders, to be identified. |  |
| UC-AST-01 | Asset inventory | An inventory of information and associated assets, including hardware, software, cloud services and data stores, is kept with a named owner for every entry. |  |
| UC-AST-02 | Acceptable use and handling rules | Written rules for acceptable and prohibited use of information and assets are set, and handling of information at each classification level is documented, including storage, sharing, transport and disposal. | D11 split list |
| UC-AST-03 | Return of assets | All organizational assets, such as devices, badges, tokens and documents, are returned by personnel and external parties when they leave or change role, contract or agreement. |  |
| UC-AST-04 | Information classification | An information classification scheme sets levels and criteria for assigning them, based on confidentiality, integrity, availability and stakeholder needs. |  |

Notes on the resolved ones:
- **UC-GOV-01** matches his own wording almost word for word: register of internal and external issues, reviewed "on a defined cycle" and "when the business context changes". Nothing to do.
- **UC-GOV-04**: current statement says "A security management system is established, run and maintained... Each process has an assigned owner". No CISO sign-off anywhere. (An "assigned owner" per process is a requirement of the ISO clause, and is the subject of the control, not an implementer.)
- **UC-GOV-07**: his quoted wording ("Security roles, responsibilities, and authorities are defined...") is now the opening of the statement. "named, current person" stays: assigning roles to people is what the control tests.
- **UC-AST-01**: "An inventory of information and associated assets, including hardware, software, cloud services and data stores, is kept with a named owner for every entry." The head of IT operations is gone. The "named owner" is an attribute of each inventory entry (ISO A.5.9 asks for it).
- **UC-RSK-01, 03, 04, 05, 43, 41, 40**: no implementer. RSK-40 and RSK-41 say "Leadership"; GOV-40 says "leadership" too. That is the generic management concept, same status as "top management" in D13. If he wants those generic words gone as well, see B.

### A.2 STILL OPEN (3)

| Id | Field(s) with the problem | Fix |
|---|---|---|
| **UC-GOV-08** Management responsibility for compliance | statement ("Top management requires every manager to make their personnel apply security"), goal ("Managers require all personnel..."), question ("require managers to ensure their personnel apply security"), why_asked, how_to_ask, good_looks_like, baseline_risk, expected_evidence ("manager guide", "manager briefing records"), test | Rewrite per his wording, see A.3 |
| **UC-RSK-02** Risk treatment plan | goal, statement, question: "Risk owners approve the plan and accept residual risk in writing"; how_to_ask "an approver"; expected_evidence "risk owner approval" | Passive form: "The treatment plan is approved, and residual risk accepted, in writing by those accountable for each risk." Question: "Does your organization have a risk treatment plan approved, with residual risk accepted in writing by those accountable for each risk?" ("Risk owner" is the ISO term, so this is minor and arguably the subject of the control. He said no named roles, so passive is safer.) |
| **UC-RSK-42** Policy exceptions | statement: "an approval from a named approver"; good_looks_like: "a documented approver, a named owner" | Statement: "Each exception needs a recorded approval and an expiry or review date." good_looks_like: "a recorded approval, an owner and an expiry or review date." |

### A.3 UC-GOV-08, proposed wording (his hint: "make the team member align with security")

The word "personnel" plus "apply" reads like a verb applied to people. The ISO control (A.5.4) is that management requires people to act in line with policy. Say it as a requirement that exists, not as management acting on personnel.

| Field | Proposed |
|---|---|
| title | Team members aligned with security policy |
| goal | The organization requires every team member to work in line with its security policies and procedures, and shows the requirement has reached each team. |
| statement | Every team member is required to work in line with the organization's security policies and procedures. The requirement is stated in documents each person receives, such as a code of conduct or onboarding pack. Teams are briefed or acknowledgements are tracked, and the records are kept. |
| question | Does your organization make sure every team member knows they must work in line with its security policies and procedures? |
| why_asked | Rules that are not reinforced inside teams are routinely ignored, and nobody is clearly responsible for lapses. |
| how_to_ask | Ask how team members learn that following security policy is expected and how that is reinforced in each team. Look for records, not statements. Example probe: "Show me the last briefing on security expectations in one team and how you know everyone was reached." |
| good_looks_like | A document each team member receives states that following security policy is required. Briefings or tracked acknowledgements cover every team, with records for the period. |
| expected_evidence | Code of conduct, onboarding pack or briefing guide stating the expectation; policy acknowledgement tracking; team briefing records; records from the current review period |
| baseline_risk | Security is treated as someone else's job, and non-compliance goes unchallenged. |
| test | Unchanged, plus: "Pass if the expectation is documented and each sampled team has a briefing or acknowledgement record in the period." (already says this) |
owner_role stays Top Management. The ISO atom A.5.4 stays mapped; atom paraphrase may keep the word "management" since atoms are source paraphrases.

### A.4 NEW WORK

#### UC-GOV-14 Security communication (his point: if it is about incidents, say so)

What it actually is: the ISO clause 7.4 atom (`ISO.C7.4-a`, "Decide what internal and external security communication is needed, when, with whom and how") is a **general communication plan for the security program** (policy changes, objectives and results, audit outcomes, awareness, requirements passed to suppliers and customers, routine contact with regulators). It is not about incidents. The standard's 7.4 asks only for what, when, with whom and how.

Why it looks like incidents: four NIST atoms were mapped to it as "req_smaller full" and the reasons on the card talk about incidents and recovery:
- `NIST.RS.CO.03-a` communications plan states who receives incident information and what may be shared (primary row)
- `NIST.RS.CO.03-c` information shared externally follows the sharing rules
- `NIST.RC.CO.03-a` recovery communication plan names stakeholders and channel (primary row)
- `NIST.RC.CO.03-b` recovery progress updates to leadership and designated stakeholders

So he is right: the control is carrying two jobs, a general plan (ISO) and incident and recovery communication (NIST). It does not duplicate UC-INC-04 (legal and contractual notification deadlines; atoms RS.CO.02-a/b/c, RC.CO.04-c). It does not duplicate UC-GOV-41 (delivery of four specific risk artifacts with proof of receipt). It sits close to a third: UC-INC-41 (approved public statements after incidents). Gap: nothing owns "who gets incident and recovery updates, and what may be shared with them".

Recommendation:
1. Narrow UC-GOV-14 to ISO 7.4 only. Title "Security communication plan". Goal: "The organization decides what security matters it communicates, when, to whom and how, inside and outside the organization, and follows that plan." Statement: "A communication plan sets which security matters are communicated, when, to whom and how, for audiences inside and outside the organization. Examples are policy changes, performance results, audit outcomes and requirements passed to suppliers. The plan is reviewed on a defined cycle, and sent messages show it is followed." Question: "Does your organization have a plan for which security matters it communicates, to whom, when and how?" Test: keep the current one. How_to_ask: add "Incident communication is covered by its own controls, so ask about everyday and program communication here."
2. New NIST slot **UC-INC-43 "Incident and recovery communication"**, owner Incident Response Lead, statement along the lines of: "A communication plan for incidents and recovery names the stakeholders who receive incident and recovery information, what may be shared with each, and the channel. Leadership and designated stakeholders receive status updates during major incidents and recovery. Information shared outside the organization follows the agreed rules." Move `RS.CO.03-a, -c`, `RC.CO.03-a, -b` there (primary of RS.CO.03 and RC.CO.03 follows). Optionally move `RS.CO.03-b` (leadership status updates, now in INC-03) too, which makes INC-03 smaller.
3. Cost: +1 control (196), 4 or 5 mapping rows re-pointed. GOV-14 then has only ISO atoms and drops out of the NIST-only subset (NIST still covered by INC-43).

#### UC-RSK-10 Compliance checks against policies (his point: unclear; it is policy drift)

What the control is today (ISO A.5.36, atoms `-a` "assign managers or control owners to check compliance at a set frequency" and `-b` "perform compliance reviews and record non-compliances with actions", plus partial NIST GV.PO.01-d): the current statement says "a named person accountable for each area", the question says "have managers check that their areas follow security policies". That reads like a management duty and hides the real point, which he states: are the teams' actual operational processes aligned with the documented policies (policy drift). It is an operational effectiveness check, done by someone checking practice (for example internal audit), and it applies only to teams where security controls are relevant.

How it differs from UC-RSK-09 (independent review): RSK-09 is the program-level audit plan and audit conduct (clause 9.2 and A.5.35). RSK-10 is the checking of day-to-day practice against policy, team by team. An internal audit program can produce the evidence for both, but the tests differ (RSK-09 samples audits and auditors; RSK-10 samples teams and what they actually do).

Proposed rewrite:

| Field | Proposed |
|---|---|
| title | Practice checked against policy |
| goal | The organization checks, on a set cycle, that the day-to-day work of each team where security controls apply follows its documented security policies and standards, and acts on any gap. |
| statement | The day-to-day work of each team where security controls apply is checked on a defined cycle against the documented security policies and standards. The checks test what the team actually does, not only what is written. Each gap between practice and policy is recorded with an action, and actions are tracked to closure. Proof is the check schedule, the check reports and the action tracker. |
| question | Does your organization regularly check that day-to-day work in teams where security controls apply follows its documented security policies? |
| why_asked | Policy drift goes unseen when nobody compares practice with the written rule, and behavior slides away from what is documented. |
| how_to_ask | Ask which teams carry security controls and how the organization knows they work as the policy says (for example internal audit, a control self-assessment, or technical scans). Look at one recent check and what it found. Example probe: "Show me the last time someone checked what one team really does against the policy, and the actions that came out of it." |
| expected_evidence | List of teams where controls apply; check schedule; check reports (audit reports, self-assessments or technical scan results); gap register with actions; records from the current review period |
| good_looks_like | Every team where controls apply is on a schedule. Checks compare real practice (records, settings, observation) with policy, not only documents. Each gap has an owner and a due date and is tracked to closure. |
| test | Obtain the list of teams where security controls apply, the check schedule and the latest check reports. Sample three teams. For each, confirm a check took place in the cycle, that it compared actual practice (records, settings or observation) with the documented policy, and that every gap has an action. Pass if every listed team is on the schedule, each sampled team was checked in the cycle on real practice, and every gap is tracked to closure or has an approved exception. Fail if a check was only a self-declaration with no supporting records. |
| applicability | Teams where security controls are relevant (wording already in the question; keep the field empty because the control applies to every organization with such teams). |
| control_type, frequency | detective, quarterly stays; consider annual unless he wants a quarterly cycle (the control no longer states a number). |

Open question for him (decision D-A): must the checker be independent of the team (internal audit), or may a manager self-check? ISO A.5.36 allows managers. His comment suggests internal audit. Recommendation: do not name who checks; require only that the check compares real practice with records. Say "for example internal audit" in how_to_ask only.

#### UC-AST-01
RESOLVED (see A.1). His request ("the requirement is that a current inventory exists") is the statement's first sentence now.


## B. Sweep of all 195 controls for named roles or role-like actors

Method: every role in `roles.csv` (case-insensitive), CISO, DPO, HR, privacy team, security team, the team, incident manager, owner, Lead, Manager, Head of, plus approver, spokesperson, officer, auditor, reviewer, responder, administrator, engineer, "named person", "accountable ...", leadership, in title, goal, note, statement, why_asked, how_to_ask, question, expected_evidence, good_looks_like, test, baseline_risk, applicability. `owner_role` and the skeleton owner column were not flagged.

Headline: **no role from `roles.csv` appears in any text field** except the thing being appointed in UC-PGV-01 ("data protection officer"), and **no "CISO", "DPO", "Head of", "Lead" as a title** appears. The remaining hits are generic actors (owner, approver, named person, spokesperson, leadership) and consultant-facing phrases ("the team", "the security team").

### B.1 Fix (an implementer or approver is named in a requirement)

| Id | Field | Phrase | Suggested fix |
|---|---|---|---|
| UC-GOV-08 | statement, goal, question, why_asked, how_to_ask, good_looks_like, baseline_risk, expected_evidence | "Top management requires every manager...", "Managers", "manager guide" | rewrite, see A.3 |
| UC-RSK-02 | goal, statement, question, how_to_ask, expected_evidence | "Risk owners approve the plan", "an approver" | passive form, A.2 |
| UC-RSK-10 | goal, statement, question, expected_evidence, good_looks_like | "Managers and control owners", "a named person accountable", "reviewers named per area" | rewrite, A.4 |
| UC-RSK-42 | statement, good_looks_like | "a named approver", "documented approver" | A.2 |
| UC-RES-42 | goal, statement, good_looks_like, expected_evidence | "has owners confirm normal operation", "the owner of each system confirms", "system owner sign-offs" | "Normal operation after restoration is confirmed and recorded in priority order." Evidence: "post-restore sign-offs" |
| UC-SUP-41 | statement | "worked through with the service owner" | "worked through for the service concerned" |
| UC-SUP-40 | goal, statement, question, expected_evidence, good_looks_like | "named internal owners", "Internal roles accountable ... are named", "approved by leadership, procurement and legal" | "Accountability for supplier security is assigned and recorded. The program is formally approved and the responsibilities are communicated to the third parties." (Also a D11 split.) |
| UC-INC-41 | goal, statement, question, expected_evidence, good_looks_like, test | "named spokesperson", "approvers" | "Public statements about incidents are made only through an approved channel with an approval step and approved wording." Test: "confirms the procedure sets who may speak publicly" (defining who is the requirement, so this is borderline; at least drop the word from question and goal) |
| UC-INC-42 | statement, expected_evidence, good_looks_like, test | "An approver then declares the end of recovery" | "The end of recovery is declared against the criteria and the date recorded." |
| UC-IAM-04 | statement, good_looks_like, expected_evidence | "approved by an authorized approver" (circular) | "approved by someone with authority to grant it, before it is granted or changed" |
| UC-PSC-05 | statement | "tracked by a named person" | "tracked and kept current" |
| UC-NET-01 | good_looks_like | "reviewed by IT leadership" | "reviewed and followed up" |
| UC-PPL-40 | good_looks_like | "sign-off from HR and the access owner" | "sign-off for each step" |

### B.2 Low priority fix (consultant-facing guidance and mild actor words)

| Id | Field | Phrase |
|---|---|---|
| UC-GOV-05 | how_to_ask | "back the security team" |
| UC-GOV-09, GOV-17, OPS-07, OPS-08, SDC-02 | how_to_ask | "the team follows", "the team tracks", "how the team finds", "which sources the team follows", "how the team prevents" (use "the organization") |
| UC-OPS-10 | good_looks_like | "alerts the team when thresholds are approached" |
| UC-SUP-05 | how_to_ask | "reach the security team" |
| UC-PNC-10 | how_to_ask | "reaches the privacy team" |
| UC-INC-01 | how_to_ask | "who is the incident manager", "who would lead an incident tomorrow" |
| UC-RSK-08 | statement, expected_evidence, test | "A named person is responsible for privacy"; "the privacy lead"; "a named person is assigned". Better: "Responsibility for privacy and personal data protection is assigned and recorded." |
| UC-PHY-04 | statement | "a named point of contact to act when an alert fires" |
| UC-OPS-02 | statement | "restricted to named roles" (say "restricted to those who need it") |
| UC-OPS-41 | goal, statement, question | "accountable responder", "named owner", "accountable owner" (ticket owner is an attribute; reword to "assigned and tracked") |
| UC-PGV-03, PGV-04 | statement | "The person who carries it out gives the Board", "The auditor who carries out the audit gives the Board" |
| UC-PPL-40 | how_to_ask | "Ask HR to walk through" |
| UC-RES-41 | why_asked, good_looks_like, test | "continuity and risk owners confirm they have it" |
| UC-IAM-06 | good_looks_like | "HR triggers removal" (say "leaver notice triggers removal") |

### B.3 Harmless (subject of the control, a thing appointed, or a statutory term)

| Id | Field | Phrase | Why harmless |
|---|---|---|---|
| UC-PGV-01 | title, goal, statement, question, evidence | "data protection officer", "the officer" | the thing being appointed (DPDPA names the role) |
| UC-PGV-02 | title, goal, statement | "independent data auditor" | the thing appointed |
| UC-PRT-05 | title, statement | "Grievance channel and owner", "owner appointment" | appointment is the subject |
| UC-PNC-13 | title, statement, question | "consent manager" | statutory entity, not a company role |
| UC-INC-70, INC-72, PNC-01, PRT-06, PGV-03/04, PNC-13 | statement | "the Board" | the regulator |
| UC-PGV-01, PGV-02, PGV-04 | statement | "governing body" | whom a report goes to |
| UC-GOV-05, 06, 07, 08(rewritten), 13, 18; UC-OPS-06; UC-RSK-02 | various | "top management" | D13 accepted: the requirement is about management itself (ISO terms). Leave unless he rules otherwise |
| UC-GOV-40, RSK-40, RSK-41, SUP-40 | various | "leadership" | generic management concept; replace with "top management" for consistency if he wants one term |
| UC-GOV-07 | goal, statement, question | "named people", "named person" | the control tests that roles have holders |
| UC-AST-01, IAM-02, IAM-40, GOV-04, GOV-10, GOV-12, GOV-15, GOV-42, RSK-05, RSK-06, RSK-40 | various | "owner" of an entry, process, document, action | attribute of a recorded item, not an implementer |
| UC-INC-01 | goal, statement, question | "named people", "named person with contact details" | assigning incident roles to people is the requirement |
| UC-IAM-02, IAM-06, IAM-41 | statement, evidence | "HR roster", "HR process", "HR record" | data source or process, not an actor |
| UC-PPL-40 | goal, statement | "HR procedures" | the process |
| UC-IAM-10 | statement | "authorized developers" | who may have access (the requirement is that access is limited) |
| UC-OPS-05 | statement | "qualified testers" | competence requirement |
| UC-PHY-12 | goal, statement | "authorized personnel" | who may do the work |
| UC-OPS-09, RES-02, RES-03 | statement | "IT activities", "IT service" | scope, not an actor |
| UC-PSC-02 | statement | "designated authority" | the legal body that appoints a guardian |
| UC-GOV-41 | statement, test | "role holders", "risk owners" | recipients of the artifacts (subject) |
| UC-OPS-02 | statement, goal | "administrators of the systems being logged" | the threat the control protects against |
| UC-CRY-40 | evidence | "secrets manager" | a tool |

### B.4 Recommended guard

Extend validator CHECK 2 beyond `roles.csv` so it cannot drift: fail (statement, goal, question) on these generic implementers: `approver`, `spokesperson`, `named person`, `named owner`, `service owner`, `system owner`, `manager(s)`, `leadership`, `reviewer(s)`. Warn on the same in how_to_ask and good_looks_like. Keep a small allow-list for the "thing appointed" cases (PGV-01, PGV-02, PRT-05) and for "top management".

## C. Plain-language elaboration for D09 to D12

### C.0 Vocabulary used in D09 and D10 (put this at the top of the explanation)

- **Record**: one line of a source framework. For NIST, one subcategory such as GV.OC-02. For DPDPA, one requirement such as CH2.CONSENT.2. For ISO, one clause or one Annex A control.
- **Atom**: one single ask inside a record. NIST GV.OC-02 asks three things, so it has atoms a, b and c.
- **Unified control**: one of our 195 controls. One control, one requirement, one test.
- **Mapping row**: one line that says "this atom is answered by this control". 725 rows in all.
- **Full coverage**: if the client passes the control's test, the atom is satisfied. **Partial**: the control covers some of the ask. The rest must go into a **remainder slot** (a small extra control for what is left), or be called **immaterial** with a reason.
- **"Soft" (D09)**: the row says full, but when you read the control's statement and test, a client could fail the NIST ask and still pass the control. The mapping is polite, not exact. NIST rows are 295 full of 307 mainly because the agent wrote the new slot controls to fit the atoms. Soft rows are the places where no slot was written and the match was stretched.

### C.1 D09 NIST atoms marked full that are soft (12 atoms in 11 NIST subcategories)

For each: the NIST ask, the control it sits in, why the fit is weak, what I recommend. Choices are: **K** keep as full, **E** keep full but edit the control text so full is true (no new control), **P** mark partial and add a remainder slot, **N** add a new control.

| NIST atom | The ask in plain words | Mapped to | Why the fit is weak | Recommendation |
|---|---|---|---|---|
| DE.CM-01-c | Detect unauthorized devices and rogue wireless networks connecting to the network. | UC-OPS-03 Monitoring for anomalous activity | OPS-03 talks about anomalous behavior in general. Neither its statement nor test mentions unknown devices or rogue wireless, so a client with no such detection would still pass. | **E**. Add "unauthorized devices and wireless access points" to what monitoring covers in OPS-03's statement and test. No new control. |
| DE.AE-07-b | Analysts have asset and criticality information in front of them when they investigate an alert. | UC-OPS-41 Alert analysis | It is in the slot's goal and test ("asset context was available"). Soft only because the slot carries 8 atoms. | **K**. Already true. |
| DE.AE-06-c | Incident responders have access to the log analysis platform. | UC-OPS-41 | Same: statement says access is given to the people who respond, and the test checks a responder access list. | **K**. |
| GV.SC-06-b | Before a supplier relationship starts, plan its scope, including what access and data the supplier will get. | UC-SUP-03 Supplier security agreements | SUP-03 is about clauses in the contract. It never asks that the access and data granted be scoped in advance. | **E**. Apply the D08 suggestion: SUP-03 says the scope of access and data granted is stated. |
| PR.PS-06-d | Track and report measures of how well secure development is working. | UC-GOV-17 Performance monitoring | GOV-17 is generic. Nothing in its text or test requires a development measure. | **P with immaterial remainder** (reason: development measures are one kind of metric in the program's measurement; add "for example secure development" to how_to_ask). A new slot for one atom is not worth it. |
| ID.IM-01-a | Schedule regular evaluations of the cyber program, such as self-assessment or audit. | UC-RSK-09 Independent review | NIST accepts a self-assessment. RSK-09 demands an independent review, so it is stricter than the ask. A client doing only self-assessments passes NIST but fails RSK-09. | **K**, with a note: in a NIST-only engagement the question is stricter than NIST. Alternatively add a second row to the revised UC-RSK-10 (practice checks, which includes self-assessments). Saqlain's call. |
| DE.CM-03-c | Tell personnel that their use of company systems is monitored. | UC-AST-02 Acceptable use | AST-02 is about rules and acknowledgement. Nothing says the rules must state that use is monitored. | **E**. Add "and state that use of systems is monitored" to the acceptable-use rules in AST-02 (after the D11 split: to the "acceptable use rules acknowledged" control). |
| ID.AM-07-c | Keep a classification scheme for data and label data according to it. | UC-AST-05 Information labeling | The scheme itself is UC-AST-04, not AST-05. The atom has two asks and only one is mapped. | **E** (mapping only). Add a second row: this atom also maps to UC-AST-04 (equal, full). |
| GV.OC-02-c | Take stakeholder expectations into account in strategy, policy and risk decisions. | UC-GOV-02 Interested parties | GOV-02 records the requirements and decides which to address. It does not require that they feed strategy, policy and risk. | **E**. Add one sentence to GOV-02: the register feeds scope, policy and risk decisions (its good_looks_like already says so for scope). |
| GV.RM-07-a, -b (two atoms) | Treat opportunities (positive risks, upside) as a category in the risk method and record them in risk discussions. | UC-GOV-10 Risks and opportunities of the program | ISO clause 6.1 "opportunities" means ways to improve the security program. NIST means upside in enterprise risk decisions. Same word, different idea. GOV-10 is the nearest home, not a match. | **P with remainder in UC-RSK-40** (extend its risk direction to include opportunities), or accept as nearest home. Low stakes. |
| PR.PS-04-c | Keep logs for a defined period and protect them from alteration. | UC-OPS-02 Log protection only | Two asks in one atom. Protection is in OPS-02; retention is in OPS-01 (statement: "how long logs are kept"). Only one half is mapped. | **E** (mapping only). Split the atom into -c1 retention and -c2 protection, or add a second row to UC-OPS-01. |

Summary for him: 2 are fine as they are (DE.AE-07-b, DE.AE-06-c), 6 become honest by a text edit or one extra mapping row and need no new control (DE.CM-01-c, GV.SC-06-b, DE.CM-03-c, ID.AM-07-c, GV.OC-02-c, PR.PS-04-c), 1 is a stricter-than-NIST note (ID.IM-01-a), 2 are partial (PR.PS-06-d, GV.RM-07). Zero new controls are required.

### C.2 D10 DPDPA mapping judgment calls

Extra vocabulary:
- **Primary control**: for every source record, exactly one control is marked "the home of this record". It is the control that best carries the record's main goal. It decides where the record appears in the sign-off table and the record trace. It does not change what else the record maps to.
- **Remainder slot**: the control that holds what the base control misses. Example: DPDPA requires erasure when the purpose ends. The ISO control UC-AST-08 (deleting information) covers deletion in general (partial). The leftover (personal data, purpose ends, processors must erase too) sits in the slot UC-AST-70, which is "remainder of AST-08".
- **Remainder immaterial**: the base control covers the ask in practice, and what is left over is too small to deserve its own control. The row says so with a reason. Three exist:
  1. NIST GV.OC-03-b (each legal requirement has an owner) to UC-RSK-06: the owner is just one more column in the same register, tested in the same sample.
  2. NIST PR.AT-01-d (check awareness works, by quiz or phishing test) to UC-PPL-03: produced by the same awareness program and sampled in the same test. Suggested: add it to PPL-03's goal.
  3. DPDPA CH2.SECURITY.1-a (reasonable technical safeguards) to UC-RES-04 backups: personal data backups are inside normal backup scope, nothing specific is left.

| Item | The DPDPA ask in plain words | What was done | Why it is a judgment call | Recommendation |
|---|---|---|---|---|
| SECURITY.1-a, -b | Take reasonable technical and organizational safeguards to protect personal data and prevent breaches. | Partial to GOV-04 (the management system) and OPS-01 (logging) and RES-04 (backups), with slots GOV-70 (personal data inside security coverage) and OPS-70 (access logging and review). | The ask is an umbrella: it means "run security properly". No single control carries it. GOV-04 is the nearest home. | Accept. Do not create a base control "measures scaled to data risk". The specific safeguards are carried by SECURITY.2 and .3 and by GOV-70. |
| BN.NOTIFY.3-a, -c | The incident response plan must cover detecting and investigating personal data breaches. | Full to UC-INC-01 (incident management planning). | Marked full, but INC-01's test does not check that personal data breaches are covered. "Generous". | Accept. A plan covering all incidents covers a personal data breach. Do not put DPDPA text in the base control (framework-neutral rule). |
| SECURITY.2-a, -b | Encrypt personal data at rest and in transit. | Full to UC-CRY-01 (use of encryption). | The Rules accept encryption, masking, obfuscation or tokens. We require encryption only. A client using tokenization is partly compliant under the Act but fails our control. Linked to the legal item on CH2.SECURITY.2. | His legal decision first. If the Act's options are accepted, reword atoms to "encryption or an equivalent such as masking or tokens" and reflect in CRY-01's key note. |
| PGV-04 (CH4.SDF.4) | A significant data fiduciary must have an independent audit of its compliance each period and send significant findings to the Board. | Own privacy control UC-PGV-04, not RSK-09. | Looks close to ISO internal audit (UC-RSK-09). Kept apart because the test differs: a named independent data auditor, a Board submission. | Accept. Make sure RSK-09's question never counts for DPDPA. |
| PNC-05, 06, 07 (CONSENT.1) | Consent must be a clear action, free of conditions, and state a specific purpose in plain language. | One record split into three controls. | The signed criteria for CONSENT.1 were written for the whole record, so the same criteria will have to be shared out among three controls (re-keying work). | Accept. Handle during criteria re-keying. |
| CONSENT.2 and CM.GRANULAR.1 | List each purpose separately and let people choose per purpose. | Both records map to PNC-08 and PNC-09. | Two repo records say the same thing. | Accept. Keep both records for traceability, one control carries both. |
| Primary calls | See below | See below | See below | See below |

Primary calls made (record, control chosen as primary):
SECURITY.1 to GOV-04 (not the slot OPS-70), MINIMIZE.2 and MINIMIZE.3 to the base controls AST-08 and AST-07 (not the slots AST-70, AST-71), SECURITY.3 to SUP-03, CORRECT.2 to PRT-04 (erasure on request, not AST-08), BN.NOTIFY.1, .2, .4 to the base INC-04 and INC-03 (not the slots INC-70, 71, 72), CB.TRANSFER.2 to PSC-05, ACCESS.1 to PRT-02 (not PRT-01).

Honest observation to tell him: in about half of these, the primary row is a **partial** row on a base control while a **full** row exists on a slot (for example BN.NOTIFY.1 primary INC-04 partial, while INC-70 "Breach intimation to the regulator" is full and is the control that really carries the record). Two rules are possible: (R1) primary = the base control, so ISO-only clients see the record's home; (R2) primary = the control with full coverage of the record's main atom. I recommend **R2 for DPDPA overlap records** because the trace then reads truthfully ("this record is carried by INC-70"). It changes about 10 primary flags and nothing else. If he prefers R1, accept as is. His call; low risk either way.

### C.3 D11 Controls their writers flagged as doing two jobs (24 listed)

Principle applied: one control = one requirement = one test. Test I used: can a client pass one half and fail the other half? If yes, the halves need different tests, so SPLIT. If the second half is just the same duty applied to several items, or the design and operation of one thing sampled in one pass, KEEP.

**Common pattern across the 24** (what to tell him):
1. **A rule or plan plus its test or exercise** (INC-01 plan and exercise, RES-06 redundancy and failover test). Same split he already accepted for A.5.30 and A.8.13 (plans vs testing, backup vs restore test).
2. **A thing plus the periodic or event-driven review of it** (SUP-05 periodic review and change review, PHY-02 entry rules and access review).
3. **One ISO Annex A control that is really three sub-requirements** (A.7.2, A.7.13, A.5.17, A.5.10, A.5.23, A.5.34). The agents kept the ISO control whole, as the kickoff said to split only where the test differs, and under-applied it.
4. **NIST slots built as buckets**: several NIST subcategories were poured into one new slot for the same theme (RSK-41 carries 10 atoms, CRY-40, AST-43, SUP-40, RES-42).
5. **A policy plus a register or a person** (RSK-08 laws, a responsible person and a processing record).

| # | Control | The two (or three) jobs | Verdict | If SPLIT: resulting controls and atoms |
|---|---|---|---|---|
| 1 | UC-PHY-02 Physical entry controls | Entry rules and visitor control; review of access rights and removal of leavers' badges | **SPLIT** | PHY-02 "Physical entry rules and visitor control": I.A7.2-a, -b, N.PR.AA.06-a. New "Physical access rights review and leaver badge removal": I.A7.2-c, N.PR.AA.06-c. Different samples: visitors vs leavers. |
| 2 | UC-PHY-09 Assets off premises | Rules for assets off site; encryption and remote wipe on portable devices | **KEEP** | Rule and technical enforcement of one duty, tested in one pass (sample devices against the rules and the compliance report). |
| 3 | UC-PHY-12 Equipment maintenance | Maintenance on a schedule by authorized staff; clearing data before equipment leaves for repair | **SPLIT** (borderline) | PHY-12 "Scheduled equipment maintenance": I.A7.13-a, -b (first half), N.PR.PS.03-a. New "Data cleared before equipment leaves for repair": I.A7.13-b (second half). Atom -b itself bundles both and must be split into -b1, -b2. Samples already differ (equipment vs repairs). |
| 4 | UC-SUP-05 Supplier monitoring and change review | Periodic review of suppliers by tier; assessment of changes to supplier services | **SPLIT** | SUP-05 "Periodic supplier review": I.A5.22-a, -b, N.GV.SC.07-c, N.GV.SC.09-b. New "Supplier service change assessment": I.A5.22-c. |
| 5 | UC-SUP-06 Cloud service security | Cloud rules, register and provider assurance; exit plan for critical services | **SPLIT** (borderline) | SUP-06 "Cloud service governance and provider assurance": I.A5.23-a, -b, N.PR.IR.02-b. New "Cloud exit plans": I.A5.23-c. |
| 6 | UC-INC-01 Incident management planning | Procedure and named roles; communicating and exercising the plan | **SPLIT** | INC-01 "Incident management procedure and roles": I.A5.24-a, -b, N.ID.IM.04-a, N.RS.MA.01-a, -b, BN.NOTIFY.3-a, -c, N.GV.SC.08-a. New "Incident plan communicated and exercised": I.A5.24-c, N.ID.IM.04-c, N.GV.SC.08-b (suppliers in exercises; INC-40 stays the remainder). |
| 7 | UC-INC-04 Incident notification duties | Who may notify and the timelines; notifying in time when a duty applies | **KEEP** | One requirement: notify in time. The procedure is the design, the incident sample is the operation. Normal for one test. |
| 8 | UC-RES-06 Redundancy of processing facilities | Redundancy design; failover testing | **SPLIT** | RES-06 "Redundancy for critical systems": I.A8.14-a, N.PR.IR.03-b. New "Failover testing": I.A8.14-b, N.PR.IR.03-c. Mirrors RES-02/03 and RES-04/05. |
| 9 | UC-IAM-03 Authentication credentials management | Issue, reset, revoke with identity check; user guidance on keeping credentials secret; default vendor credentials changed | **SPLIT** (borderline) | IAM-03 "Credential issue, reset and revocation": I.A5.17-a, -b, N.PR.AA.02-a. New "Default credentials changed on installation": I.A5.17-c. (Guidance -b could move to PPL-03 instead.) Different samples: resets vs new builds. |
| 10 | UC-AST-02 Acceptable use and handling rules | Acceptable-use rules acknowledged by users; handling rules per classification level | **SPLIT** | AST-02 "Acceptable use rules acknowledged": I.A5.10-a, -c, N.DE.CM.03-c. New "Handling rules by classification level": I.A5.10-b. |
| 11 | UC-AST-07 Protection of records | Retention schedule; protection of stored records for the period | **SPLIT** | AST-07 "Records retention schedule": I.A5.33-a, CH2.MINIMIZE.3-a, -d, CH2.MINIMIZE.2-b. New "Protection of records": I.A5.33-b. Bonus: the DPDPA remainder UC-AST-71 then completes the schedule control directly. |
| 12 | UC-GOV-16 Operational planning and control | Processes planned and run to criteria; changes controlled; outsourced processes controlled | **SPLIT** (borderline) | GOV-16 "Security processes planned and run": C8.1-a, -b. Change control (C8.1-c) and outsourced process control (C8.1-d): check first whether they can map to existing SDC-09 (change management) and SUP-01 to SUP-04 instead of creating two new controls. Test already samples three different things. |
| 13 | UC-RSK-08 Privacy and personal data protection | Applicable privacy laws identified; a person responsible for privacy; a record of processing | **SPLIT** | RSK-08 keeps "Record of personal data processing": I.A5.34-c. New "Responsibility for privacy assigned": I.A5.34-b. I.A5.34-a (laws and contract terms) re-maps to UC-RSK-06 legal register (no new control). |
| 14 | UC-PGV-03 Data protection impact assessment | Assess risks; repeat every 12 months | **KEEP** | Assess-and-repeat is one requirement with a frequency. (Statement also says the report goes to the Board and mentions algorithmic software: no atom backs these. Verify against the Act, not a split.) |
| 15 | UC-PSC-02 Verifiable guardian consent | Parent consent for a child; guardian consent for a person with a disability; verify the person is an adult/valid guardian | **KEEP** | One requirement (verifiable consent from the responsible adult before processing), one sample of accounts. |
| 16 | UC-GOV-41 Risk direction communicated | Deliver four items (risk direction, method, roles, planned responses) to those who act on them | **KEEP** | Same duty applied to four items, one test (sample recipients, check receipts). |
| 17 | UC-RSK-41 Integration with enterprise risk management | Cyber and supplier risk sits in the enterprise register and reports; escalation criteria and channels | **SPLIT** | RSK-41 "Cyber and supplier risk in the enterprise risk process": N.GV.RM.03-a, -c, N.GV.SC.03-a, -b, N.GV.SC.09-a. New "Risk escalation criteria and channels": N.GV.RM.03-b, N.GV.RM.05-a, -b, -c, N.GV.SC.03-c. (10 atoms in one control today.) |
| 18 | UC-RSK-42 Policy exceptions and time-limited risk acceptance | Exceptions approved with expiry and register; policy violations recorded and handled | **SPLIT the atom, no new control** | Atom N.GV.PO.01-d bundles exceptions and violations. Split into -d1 (exceptions: stays with RSK-42, with ID.RA.07-b, -c) and -d2 (violations recorded and handled: map to UC-RSK-10, which already records non-compliances with actions, and optionally UC-PPL-06 disciplinary). RSK-42 becomes pure exceptions. |
| 19 | UC-AST-43 End-of-life replacement and removal | Unsupported or unneeded software removed; hardware replacement and disposal at end of life | **SPLIT** | AST-43 "Unsupported and unneeded software removed": N.PR.PS.02-b, -c. New "Hardware end-of-life replacement and disposal": N.PR.PS.03-a, -b (this half is the remainder of PHY-12). |
| 20 | UC-CRY-40 Protection of data in use | Standard sets requirements for data in use; secrets kept out of code and logs; tenant isolation | **SPLIT** | CRY-40 keeps N.PR.DS.10-a. New "Secrets kept out of code and logs": N.PR.DS.10-b. New "Tenant data isolation": N.PR.DS.10-c. Three different tests: read the standard, scan code and logs, run an isolation test. |
| 21 | UC-NET-40 Authenticity and integrity of acquired items | Hardware genuine before acquisition; software integrity before install | **KEEP** | One duty (acquired items are genuine and unaltered), one sample of acquisitions, one procedure. |
| 22 | UC-INC-42 Incident recovery and its closure | Criteria for starting recovery; recording the actions; declaring recovery over | **KEEP** | One lifecycle (start, do, end) tested on the same sample of incidents. Remove one sentence from its test: "Confirm a recovery test carried out planned actions" belongs to the recovery testing controls. |
| 23 | UC-SUP-40 Supplier risk management program | A documented, approved program; accountability and shared responsibilities assigned and communicated | **SPLIT** | SUP-40 "Supplier risk program documented and approved": N.GV.SC.01-a, -b, -c. New "Supply chain security responsibilities assigned and communicated": N.GV.SC.02-a, -b. |
| 24 | UC-RES-42 Integrity of backups and restored assets | Backups checked before restoring; restored systems verified before return to production | **SPLIT** | RES-42 "Backups checked before restore": N.RC.RP.03-a, -b. New "Restored systems verified before return to production": N.RC.RP.04-c, N.RC.RP.05-a, -b. |

**Count: 17 SPLIT, 7 KEEP.** Firm splits (12): PHY-02, SUP-05, INC-01, RES-06, AST-02, AST-07, RSK-08, RSK-41, AST-43, CRY-40, SUP-40, RES-42. Borderline splits (5; recommend confirm with him): PHY-12, SUP-06, IAM-03, GOV-16, RSK-42 (atom split, zero new controls). KEEP (7): PHY-09, INC-04, PGV-03, PSC-02, GOV-41, NET-40, INC-42.
New controls if all splits go ahead: about 19 (PHY-02 1, PHY-12 1, SUP-05 1, SUP-06 1, INC-01 1, RES-06 1, IAM-03 1, AST-02 1, AST-07 1, GOV-16 up to 2, RSK-08 1, RSK-41 1, AST-43 1, CRY-40 2, SUP-40 1, RES-42 1), plus UC-INC-43 from A.4: library goes from 195 to about 215. Every split needs: new skeleton row, new fields row, atom re-pointing in the mapping files, remainder slots re-pointed (AST-71, INC-40, AST-43 vs PHY-12), then a validator run.

### C.4 D12 Not done in this slice (four items, in plain words)

**1. ISO scope question content.**
- *What it is.* At the start of an engagement the product asks a few "scope questions" (in `app/frameworks/definitions/iso27001.py`, `_ISO_SCOPE_QUESTIONS`). There are four: ISMS scope (whole organization, units, services, undefined), cloud use, software development, and physical premises. Each answer can trigger an "applicability proposal": a suggestion that some controls are probably not applicable (for example "no cloud" proposes A.5.23 as not applicable; "no development" proposes A.8.4, 8.25, 8.28, 8.30, 8.31, 8.33; "fully remote" proposes A.7.1 to 7.6, 7.8, 7.11, 7.12). The consultant confirms each. Nothing is removed automatically. Today they name Annex A ids.
- *Why left.* The kickoff tracks did not list it, and the controls had to exist first. After the unified controls are signed, each proposal must be re-written to list unified control ids instead of Annex A ids. A split (for example SUP-06, PHY-02) changes which control ids a proposal lists.
- *Work package.* WP 3.1 (content, files owned by the UCF lane), wiring in WP 5.5 (scope screen) and WP 5.4 (statement of applicability, clauses 4 to 10 never excludable).
- *Saqlain must decide:* whether four questions are enough for ISO (the old content was sized for DPDPA-first). He should confirm after the splits are final; the work itself is mechanical.

**2. Re-keying the 728 signed test criteria.**
- *What they are.* You signed 728 test criteria: 230 for ISO, 348 for NIST, 150 for DPDPA, held in `app/frameworks/criteria/iso27001.py`, `nist_csf.py`, `dpdpa.py` (generated from signed sheets, do not edit). Each is one checkable condition ("Every inventory entry has an assigned owner"), tagged design or operating, with an evidence hint and a source reference. They cover 240 records (93 Annex A, 106 NIST, 41 DPDPA). There are none for ISO clauses 4 to 10.
- *Why keyed to old ids.* The dictionary is keyed by source record id (`ISO.A5.9`, `CH2.CONSENT.3`) and each criterion id is `<record>.TC<n>`. The analysis reads criteria per record.
- *What must happen.* Each criterion must attach to the unified control(s) that now carry its record. A script can do this by record. The hard part: **87 of the 240 records map to more than one control (316 of the 728 criteria are in those records)**. For those, someone decides per criterion which control it tests (for example the three CONSENT.1 criteria spread over PNC-05, 06, 07). Splits from D11 add more. Criteria for NIST and DPDPA that share a control must be merged next to the ISO ones without losing the original ids.
- *How our drafted `test` fields differ.* Ours is one paragraph per control ("Sample five..., pass if..."), written by agents seeded from the signed criteria. It loses: the one-condition-per-line structure; the design versus operating tag; the evidence hint; the per-criterion ids; and some criteria were not carried at all (for example PNC-10 re-confirmation at an interval). It adds: sample sizes and a pass rule. For clauses 4 to 10 there are no signed criteria; the drafted tests are new text.
- *Work package.* Part of WP 3.1 to 3.3 (the plan counts it inside the 150 to 250 controls effort, section 7.5), and the library's test text reaches the workpaper in WP 3.5. Nothing is loaded before WP 5.1.
- *Saqlain must decide:* which is authoritative for what an auditor tests: the signed criteria list or the drafted paragraph. Recommendation: keep the signed criteria as the list of tests under each control (a table keyed to the control id, original criterion ids preserved) and treat the drafted `test` paragraph as a readable summary. He resolves the per-criterion choice only for the ambiguous 316 (a script lists them for him).

**3. ids.lock.json.**
- *What it is.* A file listing every unified control id (and mapping key) at the moment you sign the first version. From then on the validator (CHECK 7) fails if an id disappears or changes meaning, so saved assessments and criteria cannot be orphaned.
- *Why left.* It is only written at the first signed version, and we are still changing ids (splits, INC-43). Writing it now would freeze drafts.
- *Work package.* WP 3.4 (validator and library version), run `python3 scripts/ucf/validate.py --write-lock` after sign-off.
- *Decision:* none. He signs, then it is run.

**4. Loading into the app.**
- *What it is.* Today the library lives only as draft files and `app/frameworks/ucf/`; nothing in the product reads it. Loading means the questionnaire, RFI, judge input and review queue use unified controls instead of the 52 hand-written clusters.
- *Why left.* "Only signed rows are loaded into the app" (plan 7.5). Sign-off comes first. Also WP 5.1 is blocked by WP 3.2, 3.3, 3.4, 4.6 (an evaluation gate) and 1.1.
- *Work package.* WP 5.1 (XL, one owner, Opus review), then gate 5.1g, then WP 5.2 to 5.7. RFI from the expected evidence is WP 5.3. Scope content is WP 5.5.
- *Decision:* none now. Confirm the order: sign domains, criteria re-key, lock, 3.4, then 5.1.

Also in D12: "Fields were drafted by Sonnet agents and spot-checked only." That is a real quality risk: his reading of the 195 cards is the first full review of the statements, questions and tests. Suggest he checks a sample of tests as well as statements.

## D. Next steps, in order

### D.1 Change in the data now (no decision needed)

| # | Change | Ids and counts |
|---|---|---|
| 1 | Rewrite GOV-08 (A.3) | 1 control, all fields |
| 2 | Passive wording for approver or owner phrases in statements, goals, questions | RSK-02, RSK-42, RES-42, SUP-41, SUP-40, INC-41, INC-42, IAM-04, PSC-05, NET-01, PPL-40 (B.1: 11 controls, plus GOV-08 and RSK-10) |
| 3 | Low-priority consultant text ("the team", "security team", "privacy team", "incident manager") | B.2: about 16 controls, mostly how_to_ask |
| 4 | Soft-atom fixes that need only text or a mapping row (C.1) | Text: OPS-03, SUP-03, AST-02, GOV-02, GOV-17 (note). Mapping rows: ID.AM-07-c also to AST-04; PR.PS-04-c split to OPS-01 and OPS-02; GV.RM-07 and PR.PS-06-d partial rows |
| 5 | Validator CHECK 2 guard on generic implementers (B.4) | `scripts/ucf/validate.py` |
| 6 | Bump `library_version` to 0.0.2-draft and mark changed cards "changed since reviewed" so his earlier approvals do not hide edits | review page generator |
| 7 | Rewrite RSK-10 (A.4) and narrow GOV-14 (A.4) | 2 controls. The RSK-10 wording is ready except decision Q3 |

### D.2 Needs Saqlain's decision (give him these with the recommendation)

| # | Question | Recommendation |
|---|---|---|
| Q1 | D11: confirm the 17 splits, especially the 5 borderline (PHY-12, SUP-06, IAM-03, GOV-16, RSK-42) | Approve the 12 firm splits; approve the borderline ones; keep the 7 |
| Q2 | UC-GOV-14: narrow to the general communication plan and create UC-INC-43 for incident and recovery communication | Yes |
| Q3 | UC-RSK-10 (A.4): may a manager self-check, or must an independent function check? | Do not name who checks; require checks on real practice with records |
| Q4 | D09: accept RSK-09 as the home for NIST ID.IM-01-a (stricter than NIST)? Accept GV.RM-07 as partial with remainder in RSK-40? | Yes to both |
| Q5 | D10: the legal item on CH2.SECURITY.2 (encryption only versus the Rules' four measures), and the primary rule R1 versus R2 | Follow the Rules (widen); use R2 for DPDPA overlap records |
| Q6 | Generic management words: allow "top management" only and replace "leadership"? | Yes |
| Q7 | Show or hide `owner_role` on sign-off cards (it still says CISO etc.) | Keep on the sign-off table, hide on any client-facing view |
| Q8 | D12: confirm the order, and that signed criteria stay as the list of tests under each control with the drafted `test` as a summary | Yes |

### D.3 What can be regenerated (no thinking)

- `python3 scripts/ucf/make_signoff.py` (sign-off tables, counts per domain).
- `python3 scripts/ucf/make_review_html.py` (review page). Replace the D09 to D12 text with the plain-language versions in section C, and add a new decision for the changes above.
- `python3.13 scripts/ucf/validate.py` (checks 0 to 7 and counts per subset; expect about 215 controls for all three frameworks after the splits and UC-INC-43).

### D.4 Work after the data edits (mechanics, by subagents)

1. Splits: one Sonnet subagent per domain group (PHY, SUP, INC and RES, AST, CRY and IAM, RSK and GOV), each owning disjoint files. Every split: skeleton row, fields row, atom paraphrase split where an atom is bundled (I.A7.13-b, N.GV.PO.01-d, N.PR.PS.04-c), mapping rows re-pointed, remainder slots re-pointed. New ids use the next free number in the ISO range (01 to 39) for ISO-origin splits and 40 to 69 for NIST-origin splits (the validator enforces ranges).
2. Validator run and fix loop. Regenerate sign-off and review pages.
3. A fresh agent (not the author) reviews only the changed controls against the principle "role-neutral, one requirement, one test".

### D.5 What remains afterward to reach "signable domain tables"

1. He reviews the changed and new cards (about 55: the 35 comment items, the splits and new slots, less overlaps).
2. He clears the 25 ISO clause records marked `needs_verification` (68 atoms); 11 were already adjusted against the PDF, and the 2024 climate wording in 4.1 and 4.2 is unverified.
3. He decides the 15 undecided legal items (pack against Act flags).
4. Spot check of the Sonnet-drafted fields beyond statements (tests and questions): the largest unreviewed risk.
5. Per-domain sign-off (18 domains; AST and GOV tables exceed the 15-row target and can be split by sub-theme).
6. At the first signed version: write `ids.lock.json`, set `library_version`, then WP 3.4, the criteria re-key (316 criteria need a per-control choice), ISO scope proposals re-keyed to control ids, then WP 5.1.

## Scratch note

Helper files I made in the scratchpad: `load.py`, `hits.json`, `A_resolved.md`, `part_*.md`. If `load.py` or `triage.md` existed before, they were overwritten.
