"""Fictional Veldhara Logistics evidence and control scenario.

The scenario covers the 93 ISO 27001 Annex A controls registered by the app and
23 supplemental top-level clauses 4-10 for the consultant's manual walkthrough.
All dates are fixed to the 1 July-30 September 2026 assessment period. This
module contains only synthetic company records and deterministic data.
"""

from __future__ import annotations

from datetime import date, timedelta


def _document(
    filename: str,
    title: str,
    category: str,
    issued: str,
    owner: str,
    approved_by: str,
    version: str,
    sections: list[tuple[str, list[str]]],
    *,
    headers: tuple[str, ...] = (),
    rows: tuple[tuple[object, ...], ...] | list[tuple[object, ...]] = (),
    render_as_scan: bool = False,
) -> dict:
    return {
        "filename": filename,
        "title": title,
        "category": category,
        "date": issued,
        "owner": owner,
        "approved_by": approved_by,
        "version": version,
        "sections": sections,
        **({"headers": headers, "rows": rows} if headers else {}),
        **({"render_as_scan": True} if render_as_scan else {}),
    }


_ACCESS_SYSTEMS = (
    "Dispatch Portal",
    "Warehouse WMS",
    "Finance ERP",
    "Workplace Mail",
    "Fleet Maintenance",
    "Payroll Desk",
    "Analytics Lake",
    "Yard Check-in",
    "Customer Claims",
)
_ACCESS_TEAMS = (
    "Linehaul Operations",
    "Depot Operations",
    "Finance",
    "People Services",
    "Fleet Engineering",
    "Information Technology",
    "Customer Care",
    "Risk and Safety",
    "Network Planning",
)
_ACCESS_ROLES = ("read_only", "operator", "approver", "administrator", "report_user")
_TERMINATED_ROWS = {19, 87, 143, 201}
_OPEN_REMOVAL_ROWS = {19, 51, 87, 122, 143, 169, 201, 214}
_UNCONFIRMED_ROWS = {34, 178}


def _access_rows() -> tuple[tuple[object, ...], ...]:
    """Return 220 distinct access records with the exceptions described in Q2."""
    rows: list[tuple[object, ...]] = []
    for number in range(1, 221):
        system_index = (number - 1) % len(_ACCESS_SYSTEMS)
        system = _ACCESS_SYSTEMS[system_index]
        status = "terminated" if number in _TERMINATED_ROWS else (
            "vendor" if number in {13, 76, 155, 207} else "active"
        )
        enabled = "yes" if number in _TERMINATED_ROWS or number not in {28, 106} else "no"
        privileged = "yes" if number % 17 == 0 or number in {19, 34, 87, 143, 178, 201} else "no"
        role = "administrator" if number in {19, 34, 87, 143, 178, 201} else _ACCESS_ROLES[(number * 3) % len(_ACCESS_ROLES)]
        if role == "administrator":
            privileged = "yes"
        decision = (
            "remove approved" if number in _OPEN_REMOVAL_ROWS else
            "review pending" if number in _UNCONFIRMED_ROWS else
            "retain" if number % 9 not in {0, 1} else
            "reduce role"
        )
        reviewer = "" if number in _UNCONFIRMED_ROWS else "Asha Menon"
        reviewed_on = "" if number in _UNCONFIRMED_ROWS else "2026-09-18"
        ticket = f"IAM-26-{number:04d}" if number in _OPEN_REMOVAL_ROWS else ""
        closure = "Overdue; enabled at 2026-09-30" if number in _OPEN_REMOVAL_ROWS else (
            "Awaiting manager response" if number in _UNCONFIRMED_ROWS else "Closed"
        )
        due_date = date(2026, 9, 10) + timedelta(days=(number * 3) % 10) if number in _OPEN_REMOVAL_ROWS else (
            date(2026, 9, 18) if number in _UNCONFIRMED_ROWS else None
        )
        last_login = date(2026, 9, 1) + timedelta(days=(number * 7) % 18)
        rows.append(
            (
                f"VH-{number:04d}",
                f"acct-{number:04d}@veldhara.example",
                system,
                _ACCESS_TEAMS[system_index],
                status,
                enabled,
                role,
                privileged,
                last_login.isoformat(),
                decision,
                reviewer,
                reviewed_on,
                ticket,
                due_date.isoformat() if due_date else "",
                closure,
            )
        )
    return tuple(rows)


_ACCESS_EXPORT_ROWS = _access_rows()
_ACCESS_SYSTEM_COUNTS = tuple(
    (system, sum(1 for row in _ACCESS_EXPORT_ROWS if row[2] == system))
    for system in _ACCESS_SYSTEMS
)


DOCUMENTS: dict[str, dict] = {
    "policy": _document(
        "Veldhara_Information_Security_Policy_v3.1.pdf",
        "Information Security Policy",
        "security_policy",
        "2026-07-01",
        "Information Security Lead",
        "Board Risk Committee",
        "3.1",
        [
            ("Document control", [
                "Owner: Information Security Lead. Approved by the Board Risk Committee on 1 July 2026.",
                "This policy applies to employees, depot contractors, systems, information and services operated for Veldhara Logistics.",
                "The Information Security Lead reviews this policy every twelve months and after a material change; the next scheduled review is 1 July 2027.",
                "Version 3.1 replaced version 3.0 after the driver integration team and two new SaaS services entered scope.",
                "Staff receive the policy through the People Services portal and acknowledge it during induction and the annual policy refresh.",
            ]),
            ("Management and responsibilities", [
                "The Managing Director owns the ISMS outcome. The Information Security Lead maintains the framework and reports material risks to the Board Risk Committee.",
                "System owners approve access to their service. People Services sends joiner, mover and leaver notices. The platform team implements approved changes.",
                "Managers must review security exceptions for their teams and close assigned actions by the date recorded in the risk register.",
            ]),
            ("Use of information and services", [
                "Information is classified as Public, Internal, Confidential or Restricted using the impact on drivers, customers, staff and operations.",
                "Personal identity, payroll and live location data are Restricted. Dispatch instructions and customer contact details are Confidential.",
                "Staff may use approved services for company work. Personal email and unapproved file sharing are not approved transfer routes.",
                "Information owners set retention periods and authorize disposal. Restricted information must not be copied into test accounts without masking.",
            ]),
            ("Asset ownership and information handling", [
                "Each production service has a business owner who approves its purpose, access groups, information class, supplier dependency and recovery priority.",
                "The Asset Coordinator keeps the service inventory with the owner and asks owners to attest changes each quarter.",
                "System owners approve data exports before release. The recipient, purpose, fields, transfer route and deletion date are recorded in the service ticket.",
                "Confidential and Restricted records are stored in managed repositories with named groups. Local copies are removed after the owner confirms the required business record is retained.",
                "Removable storage requires a named custodian and an approved task. Personal storage accounts and removable media are not approved storage locations.",
                "Where a service provider operates infrastructure, the service owner records the provider boundary and the security responsibilities retained by Veldhara.",
            ]),
            ("Access and authentication", [
                "Access is granted for a recorded role and business need, approved by the line manager and service owner, and removed when that need ends.",
                "Multi-factor authentication is required for remote access and administrator accounts. Shared administrator credentials are prohibited.",
                "The Identity Administrator maintains the central identity directory. Service owners review access monthly and record exceptions and removal tickets.",
                "An access review does not count as complete until every production service owner has returned a decision or an exception has been escalated.",
                "Joiner access requires a personnel event, manager approval and service owner approval. Mover access is adjusted to the new role before old permissions are retained.",
                "Leaver disable requests are due on the employment end date. The Identity Administrator records each system confirmation and escalates any account that remains enabled.",
                "Administrator access is separate from ordinary user access, time-bound where the service permits and reviewed by a manager other than the account holder.",
                "Service accounts have a named technical owner, a documented purpose, restricted permissions and a rotation or replacement date.",
                "The monthly service owner review is scheduled for the first two weeks of each month. The coordinator tracks returned exports, signed decisions and removal closure separately.",
            ]),
            ("Suppliers and development", [
                "The service owner records security requirements before a supplier receives company information or system access.",
                "The integration team uses peer review and a separate test environment before release. Emergency production changes require next-day review.",
                "Critical provider assurance is intended to be reviewed each year, but the owners did not use a shared review calendar during this period.",
                "Before onboarding, the owner records service purpose, data categories, hosting location, support access, subprocessors, assurance evidence and exit requirements.",
                "Contract security terms address confidentiality, access controls, incident contact, service continuity, information return or deletion and notice of material changes.",
                "New supplier evidence is reviewed by the Supplier Manager and the business service owner. Open requests remain visible in the quarterly risk register.",
                "Developers use private repositories, protected branches, approved libraries and peer review. Security and privacy requirements are added to the ticket before work starts.",
                "Production releases require a second approver, test results, rollback instructions and a post-deployment check. Emergency changes receive next-business-day review.",
            ]),
            ("Technical operations", [
                "Platform owners maintain approved build baselines, endpoint protection, vulnerability targets and named exception records.",
                "Critical security events and administrator activity are forwarded to the managed log workspace. The monitoring desk routes priority alerts to the on-call role.",
                "Production network rules have an owner, reason and review date. Guest and office routes are separated from production service paths.",
                "Cryptographic keys remain in the managed key service. Key owners review access and rotation dates each quarter.",
                "Nightly backup jobs are monitored by IT Operations. A successful job is not treated as a restore test; a separate sample restore must record integrity and elapsed time.",
                "Service recovery exercises use the recovery runbook and record actual time, recovery point, access issues, communications and corrective actions.",
            ]),
            ("Incident and continuity", [
                "Personnel report suspected events to the service desk or duty manager as soon as practical; the incident lead records triage and decisions.",
                "The incident plan assigns an incident lead, technical responder, privacy contact and communications approver.",
                "Business continuity exercises are scheduled and recorded separately from backup restore tests.",
                "Personnel report suspected events to the service desk or duty manager. The incident record keeps detection time, severity, owner, affected service and decisions.",
                "The incident lead controls external statements with the Managing Director and records recipients and approved wording in the event file.",
                "Lessons from an event or exercise are assigned to an owner and remain open until evidence of correction is reviewed.",
            ]),
            ("Measurement, assurance and exceptions", [
                "The Information Security Lead reports access review completion, supplier assurance, training, vulnerability status, backup jobs, restore tests and recovery exercises each quarter.",
                "Internal Audit selects samples independently and reports observations to the Audit Committee Chair. Control owners provide source records but do not approve audit conclusions.",
                "A policy exception states the affected service, business reason, risk, compensating measure, approving role and expiry date. Expired exceptions are escalated.",
                "Failure to meet a target is recorded as an open action or risk. A planned task is not closed until the owner supplies a record and the reviewer confirms the result.",
            ]),
            ("Review and approval history", [
                "Version 3.0 was approved on 15 June 2025. Version 3.1 was approved on 1 July 2026 after scope and service changes were reviewed.",
            ]),
            ("Cutoff addendum, 5 October 2026", [
                "The Information Security Lead added this note on 5 October after the quarter close; it does not change policy version 3.1 or its 1 July effective date.",
                "The committee reviewed the open access review, supplier assurance and backup test actions at its 24 September 2026 meeting.",
                "The policy remains in force. The September discussion assigned owners and dates but did not record closure of the open actions.",
            ]),
        ],
    ),
    "ropa": _document(
        "Veldhara_Records_of_Processing_FY26.docx",
        "Records of Processing Activities, FY 2026-27",
        "processing_records",
        "2026-09-29",
        "Privacy Coordinator",
        "Operations Director",
        "2.2",
        [
            ("Register notes", [
                "The Privacy Coordinator updated the service owners and retention notes on 29 September 2026.",
                "The register covers the processing activities reported by Operations, People Services, Finance and Customer Care as at 30 September 2026.",
                "A quarterly owner review is scheduled for the first working week after each quarter close; the Q2 review was completed on 29 September.",
            ]),
            ("Purpose and access", [
                "Dispatch and proof-of-delivery data is used to plan routes, confirm delivery and resolve claims; access is limited to dispatch, depot and customer care roles.",
                "Driver identity and onboarding records are used to verify eligibility, assign routes and respond to safety events; People Services and Safety hold access.",
                "Live location data is used during an assigned route and is not exposed to customer users after delivery confirmation.",
                "Payroll data is used for salary, tax and benefits administration; Finance and People Services use separate role groups.",
            ]),
            ("Processing activity register", [
                "Driver onboarding includes identity details, licence checks, emergency contact and employment status. People Services owns the record.",
                "Route operations include assigned driver, vehicle, dispatch events and live location during an active route. Network Planning owns the purpose.",
                "Customer delivery coordination includes consignee name, phone number, delivery address and proof-of-delivery record. Customer Care owns the purpose.",
                "Payroll administration includes employee identifier, bank details, pay components and tax declarations. Finance owns the purpose.",
                "Supplier support tickets can include limited account identifiers and service logs. The service owner reviews each disclosure before sharing.",
            ]),
            ("Retention and disposal", [
                "Completed delivery contact records are retained for 24 months after delivery unless an open claim requires a hold.",
                "Driver identity and safety records are retained for the employment period plus seven years under the internal records schedule.",
                "Route location samples are deleted after 90 days; aggregated route performance records are retained for 24 months.",
                "Payroll and statutory finance records are retained for seven years. Deletion exceptions are recorded in the legal hold register.",
                "Service desk attachments are retained for 180 days unless linked to an incident or open legal hold.",
            ]),
            ("Transfers and review", [
                "The route platform, payroll service and company email use hosted services listed in the cloud register.",
                "The Privacy Coordinator checks a sample of service descriptions with their owners each quarter and records changes for risk review.",
                "The 29 September review added the Fleet Route Insights export and corrected the contact-data retention owner.",
                "The driver onboarding notice describes identity checks and route assignment; the driver app permission screen separately asks for location access.",
                "The company did not supply a versioned withdrawal flow or a consent receipt export for the sampled driver app build.",
            ]),
            ("Recipients and access", [
                "People Services can view driver onboarding information; Network Planning can view assigned route data; Customer Care can view delivery contacts and claims.",
                "Finance and People Services have separate payroll groups. Depot supervisors receive only the route and delivery details needed for their location.",
                "Hosted service support access is approved by the service owner, limited to a recorded ticket and checked against the supplier agreement.",
                "Supplier support attachments are checked by the service owner before transfer so unrelated personnel or customer records are not included.",
            ]),
            ("Notice, request and correction records", [
                "The driver onboarding portal presents the current notice before account activation; the mobile location permission appears separately when a route feature is enabled.",
                "A user can send a question or correction request to the privacy mailbox. Customer Care routes privacy items to the Privacy Coordinator and retains the response in the grievance queue.",
                "The September record set did not include an export of driver app consent receipts or a tested in-app withdrawal flow.",
                "Service owners correct inaccurate fields through a recorded request and retain the source, verification and completion date.",
            ]),
            ("Review log", [
                "On 29 September 2026 the Privacy Coordinator checked activity owners, purposes, retention fields and hosted service references with five service owners.",
                "That review added the Fleet Route Insights export and corrected the contact-data retention owner; it did not establish a mobile consent receipt for prior users.",
                "The next register review is due in the first working week of January 2027, or earlier if a new purpose or supplier is added.",
            ]),
        ],
        headers=("Activity ID", "Processing activity", "Data subjects and fields", "Purpose", "Owner", "Retention"),
        rows=(
            ("ROP-01", "Driver onboarding", "Drivers; identity, licence, emergency contact, employment status", "Eligibility and safety", "People Services", "Employment plus 7 years"),
            ("ROP-02", "Route operations", "Drivers; route assignment, location events, vehicle", "Dispatch and delivery confirmation", "Network Planning", "Location 90 days; route 24 months"),
            ("ROP-03", "Consignee coordination", "Customers; name, phone, address, proof of delivery", "Delivery coordination and claims", "Customer Care", "24 months after delivery"),
            ("ROP-04", "Payroll", "Employees; bank details, pay, tax declarations", "Salary and benefits administration", "Finance", "7 years"),
            ("ROP-05", "Supplier support", "Named business users; account ID and service logs", "Troubleshooting contracted service", "Service owner", "180 days unless held"),
        ),
    ),
    "access_q2": _document(
        "Veldhara_Access_Review_Q2_FY26.docx",
        "Monthly Access Review Summary, Q2 FY 2026-27",
        "access_control_policy",
        "2026-09-30",
        "Identity Administrator",
        "Information Security Lead",
        "2.0",
        [
            ("Review basis", [
                "The review period is 1 July through 30 September 2026; service owners are expected to review access monthly.",
                "The completed review covered 9 of 11 production systems.",
                "The TMS and driver mobile app were excluded because their service owners had not returned an export by the review deadline.",
                "The September workbook contains 220 account records from the nine systems that supplied data; it does not represent the two omitted systems.",
            ]),
            ("Review timeline", [
                "The July request was sent on 2 July and chased on 16 July; no complete owner decision set was returned by month end.",
                "The August request was sent on 3 August and chased on 18 August; the warehouse and finance exports were received, but the cycle was not closed.",
                "The September cycle was opened on 2 September. Nine system owners returned decisions by 18 September, and the summary was signed on 22 September.",
                "No signed review sheet was created for July or August. The September workbook must not be treated as evidence for either earlier month.",
            ]),
            ("Exceptions and actions", [
                "Eight approved removal actions remained open at 30 September; four were for terminated accounts that were still enabled in the directory.",
                "Two administrator accounts had no reviewer decision because the responsible manager did not respond before the cutoff.",
                "The Identity Administrator reconciled the eight open removal tickets on 30 September and confirmed they were past their target dates.",
                "The Identity Administrator escalated the outstanding decisions to the Information Security Lead on 24 September.",
                "The next monthly cycle is due to open on 1 October; the TMS and driver app owners remain named escalation recipients.",
            ]),
            ("Decision fields", [
                "A completed decision includes the account identity, production service, account state, business role, privilege level, last activity, reviewer and review date.",
                "For a removal, the service owner records approval and the Identity Administrator records the disable ticket, due date and directory closure check.",
                "A reviewer may record retain or reduce role, but a pending manager response is not a retain approval.",
                "The nine returned service owner files were checked for duplicate rows and obvious account identifier errors before consolidating the workbook.",
            ]),
            ("Closeout limitation", [
                "The summary is an exception report for one completed cycle, not evidence that the monthly process operated in July and August.",
                "The two absent production systems remain in the asset inventory and in the October request list.",
                "The eight approved removals have individual target dates before 30 September; their open status means the accounts were not verified disabled.",
                "The owner response for two administrator accounts is absent. The Identity Administrator did not classify these accounts as reviewed or retained.",
                "The Information Security Lead accepted the summary for tracking but did not accept the open exceptions as closed risk treatment.",
            ]),
            ("Approval", [
                "Asha Menon prepared the 9-system summary on 22 September 2026; the Information Security Lead accepted it with the listed exceptions still open.",
                "A review is considered complete only for the systems with returned decisions; omitted systems and open removals remain follow-up work.",
            ]),
            ("Method and control totals", [
                "Owners received a service-specific account extract and were asked to confirm account status, business role, manager, privilege level, last login and removal decision.",
                "The Identity Administrator reconciled returned rows to the current production inventory and removed duplicate account lines before preparing the workbook.",
                "The returned population contained 220 records across nine systems. System counts are shown in the table and should not be projected onto the omitted TMS or driver app.",
                "A remove-approved decision was accepted from the service owner; the identity remained open until the disable event appeared in the directory and was checked.",
                "Rows marked review pending have no signed owner decision and are excluded from a clean retain conclusion, even when the account had recent activity.",
            ]),
            ("Removal action register", [
                "IAM-26-0019, IAM-26-0051, IAM-26-0087 and IAM-26-0122 were due between 10 and 19 September and remained open at quarter close.",
                "IAM-26-0143, IAM-26-0169, IAM-26-0201 and IAM-26-0214 were also past their due dates on 30 September.",
                "The terminated identities in the population are VH-0019, VH-0087, VH-0143 and VH-0201; each was still enabled at cutoff.",
                "VH-0034 and VH-0178 are administrator accounts with no reviewer response. They remain an open decision rather than an approved retain.",
                "The follow-up request was assigned to the Identity Administrator and the Information Security Lead; no removal closure was asserted without a directory check.",
            ]),
        ],
        headers=("System", "In completed review", "Records supplied", "Review status"),
        rows=tuple((system, "Yes", count, "Decisions received") for system, count in _ACCESS_SYSTEM_COUNTS)
        + (("Transport Management System (TMS)", "No", 0, "Owner export not returned"), ("Driver mobile app", "No", 0, "Owner export not returned")),
    ),
    "incident_plan": _document(
        "Veldhara_Incident_Response_Plan_v1.pdf",
        "Information Security Incident Response Plan",
        "breach_procedure",
        "2026-03-15",
        "Information Security Lead",
        "Managing Director",
        "1.0",
        [
            ("Purpose and activation", [
                "This plan covers suspected loss, unauthorized access, malware, service compromise, personal information exposure and material availability events.",
                "The duty manager opens an incident record and pages the Information Security Lead for a suspected security event affecting a production service.",
                "The incident lead sets severity, assigns technical investigation and records the basis for escalation or closure.",
            ]),
            ("Roles", [
                "The incident lead coordinates decisions; IT Operations contains the technical issue; the Privacy Coordinator assesses personal information impact.",
                "The Managing Director approves external communications. The service owner preserves business records and identifies affected customers or depots.",
                "The Information Security Lead maintains the call tree and records any contact with authorities or contracted providers.",
            ]),
            ("Response sequence", [
                "Record detection time and source, preserve original alerts, scope affected services and keep a time-stamped decision log.",
                "Contain access or network paths under incident lead direction; retain relevant logs and obtain a second person to witness volatile evidence collection.",
                "The Privacy Coordinator records the data categories and affected groups before the Managing Director approves any external communication.",
                "Recover from a known-good service state, monitor for recurrence and assign a post-incident review owner.",
            ]),
            ("Triage and decision record", [
                "The incident lead records source, detection time, affected service, business impact, information types, current containment and the next decision time.",
                "A suspected security event remains open until the lead records an incident decision or the reason it was returned to routine service support.",
                "Potential personal information exposure is referred to the Privacy Coordinator for a fact-based impact assessment and internal escalation.",
                "The incident lead records who was consulted, which evidence was preserved and why an external communication was approved or deferred.",
                "The assigned technical responder records systems examined, queries run, timestamps and any changes made during containment.",
            ]),
            ("Service restoration and follow-up", [
                "The service owner confirms business data and user access before declaring a service restored.",
                "IT Operations compares the recovered service with the known-good state and records the recovery point and elapsed time.",
                "The incident lead arranges a review with affected owners after stabilization and records what went well, what failed and who owns each action.",
                "Corrective actions remain open in the risk register until an independent reviewer checks the evidence and the owner confirms the residual risk.",
            ]),
            ("Contacts and communications", [
                "The call tree lists the hosting provider support desk, local emergency contact, national incident contact and the company's contracted legal adviser.",
                "The Information Security Lead verified the hosting provider number on 10 February 2026; the other contact entries were copied forward from the prior revision.",
                "Only the incident lead or Managing Director may send an external status message; the duty manager records approved wording and recipients.",
            ]),
            ("Exercise expectation at issue", [
                "The plan exists but has not yet been tested.",
                "The plan owner must assign a tabletop or call-tree test and retain the attendance, decisions and action list with the incident register.",
            ]),
            ("Version history", [
                "Version 1.0 was approved on 15 March 2026. The next formal review is due 15 March 2027 or after a material incident.",
            ]),
            ("Quarter-end addendum, 5 October 2026", [
                "The Information Security Lead added this cutoff note on 5 October; the approved plan remains version 1.0 dated 15 March 2026.",
                "No tabletop exercise, call-tree test or technical incident simulation was completed between 1 July and 30 September 2026.",
                "The plan owner scheduled a tabletop for 20 October 2026; it was future work at the 5 October evidence cutoff.",
                "The hosting provider number was verified on 10 February 2026; the other contact entries were not reconfirmed during the September quarter close.",
            ]),
        ],
    ),
    "dr_report": _document(
        "Veldhara_DR_Failover_Test_Report.docx",
        "Core Dispatch Failover Exercise Report",
        "business_continuity",
        "2026-08-19",
        "IT Operations Manager",
        "Operations Director",
        "1.0",
        [
            ("Exercise record", [
                "The exercise was conducted on 18 August 2026 against the Core Dispatch recovery runbook.",
                "Failover completed in 3h 10m against a 4h RTO.",
                "The test passed and the results were reviewed by IT Operations.",
                "The exercise used the secondary hosted region and a controlled dispatch queue; no live driver route was interrupted.",
            ]),
            ("Observed results", [
                "Dispatch staff authenticated to the recovery service and confirmed a sample of 12 route assignments and delivery acknowledgements.",
                "The recovered queue lagged by 4 minutes at first login and reached the recorded recovery point within the agreed 15 minute objective.",
                "The platform team restored service to the primary region after 52 minutes of stable monitoring.",
                "Two operator contact numbers were out of date; People Services corrected the call sheet on 21 August.",
            ]),
            ("Limits and actions", [
                "The exercise tested regional service failover and did not perform a backup restore from retained copies.",
                "The report does not establish the recovery time of a deleted database or a single corrupted record.",
                "Action DR-26-08-04 assigns a separate database restore exercise to IT Operations by 31 October 2026.",
            ]),
        ],
        headers=("Checkpoint", "Target", "Observed", "Result"),
        rows=(
            ("Dispatch service available", "4 hours", "3 hours 10 minutes", "Met"),
            ("Route assignment sample", "12 records", "12 records confirmed", "Met"),
            ("Recovery point", "15 minutes", "4 minutes of queue lag", "Met"),
            ("Database restore from backup", "Separate test", "Not performed", "Open action DR-26-08-04"),
        ),
    ),
    "consent_screen": _document(
        "Veldhara_Driver_App_Consent_Screen.png",
        "Driver App Location Permission Screen",
        "consent_form",
        "2026-08-29",
        "Driver Experience Product Owner",
        "Privacy Coordinator",
        "Build 2.8.4",
        [("Visible screen text", [
            "Veldhara Driver App",
            "Location data permission",
            "I agree to location tracking",
            "I agree",
            "No withdraw option is shown on this screen.",
            "The screen was captured from the production mobile build on 29 August 2026 for an internal privacy review.",
        ])],
    ),
    "access_export": _document(
        "Veldhara_User_Access_Review_Export.xlsx",
        "September Access Review Export",
        "access_control_policy",
        "2026-09-30",
        "Identity Administrator",
        "Information Security Lead",
        "Extract 2026-09-30; signed review 2026-09-22",
        [
            ("Workbook scope", [
                "The workbook lists 220 account records returned by nine production system owners for the September 2026 monthly review.",
                "The Transport Management System and driver mobile app are omitted because their owners did not return exports by 18 September.",
                "Eight removal approvals were still open at 30 September. Four affected accounts belonged to people recorded as terminated.",
                "Administrator accounts VH-0034 and VH-0178 have no reviewer decision because their manager response was outstanding.",
            ]),
            ("Reviewer notes", [
                "A decision of remove approved records the owner's decision; an open closure status means the identity was not confirmed disabled by the cutoff.",
                "The Identity Administrator reconciled ticket references on 24 September and did not alter source owner decisions.",
            ]),
        ],
        headers=("Record ID", "Account", "System", "Team", "Account status", "Enabled", "Role", "Privileged", "Last login", "Reviewer decision", "Reviewer", "Review date", "Remediation ticket", "Remediation due date", "Closure status"),
        rows=_ACCESS_EXPORT_ROWS,
    ),
    "stale_access": _document(
        "Veldhara_Access_Review_Dec_2023.docx",
        "User Access Review, 31 December 2023",
        "access_control_policy",
        "2023-12-31",
        "Former IT Administrator",
        "Operations Director",
        "Archive copy",
        [
            ("Archive note", [
                "User access review, 31 December 2023.",
                "This file records a historical sample prepared before the current identity directory and service inventory were established.",
                "The document is retained in the archive and does not describe the July through September 2026 review period.",
            ]),
        ],
    ),
    "prior_baseline": _document(
        "Veldhara_ISMS_Baseline_Operating_Log_2025.docx",
        "Prior-Year ISMS Operating Log",
        "isms_audit_reports",
        "2025-09-30",
        "Information Security Lead",
        "Managing Director",
        "1.0",
        [
            ("Period and source", [
                "This record covers 1 July through 30 September 2025 and was assembled from the prior-year service desk and committee register.",
                "The log is limited to the records retained in the 2025 archive; it does not establish performance in the 2026 assessment period.",
            ]),
            ("Prior-year activity", [
                "The July 2025 policy sample showed a management-approved security policy distributed to office staff; two depot acknowledgements were still outstanding.",
                "The 2025 identity sample found the access request and approval steps documented, but quarterly review evidence was missing for two services and one removal ticket was overdue.",
                "The supplier file contained signed confidentiality clauses for the payroll host and email service, but no consolidated supplier risk review or complete subprocessor check.",
                "The incident procedure assigned an incident lead and escalation contacts, but no incident exercise or response record was supplied for the prior period.",
                "A dispatch failover exercise completed in 5 hours 20 minutes against the stated 4 hour recovery objective; the service owner opened corrective action BC-25-09.",
                "A security refresher was delivered in August 2025 to 31 depot supervisors; the annual completion list for all personnel was not available.",
                "The secure authentication sample showed multifactor access for remote administrators, while the review of two service accounts was incomplete.",
                "The backup console showed successful scheduled copies in September 2025, but no restore test result was retained for the period.",
                "The backup archive contained no provider attestation for encryption of retained backup copies.",
                "During July-September 2025, Veldhara did not employ a team or commission a supplier to build or modify company software; the scope record applied only to that period.",
                "The driver notice described identity and delivery coordination purposes but the 2025 archive did not contain a mobile location permission receipt.",
                "The prior driver permission screen had an allow action but no recorded withdrawal route in the sampled mobile build.",
                "The consignee notice listed delivery coordination and claim handling, but its retention summary did not distinguish route location records.",
                "The 2025 security policy required access restriction and event reporting; the evidence sample did not include service owner review records for every system.",
                "The prior grievance register contained routine delivery complaints and one privacy question; response details were not retained for two sampled cases.",
                "The prior consent sample consisted of a driver onboarding paper form; no receipt export for the mobile location permission flow was retained.",
                "The 2025 onboarding and route inventory showed no child profile or service channel for children, and no child-related records were identified in the period.",
            ]),
            ("Archive limitation", [
                "The evidence index was created on 5 October 2025. Current-period records are stored in separate folders and are not cited here.",
            ]),
        ],
    ),
    "isms_scope": _document(
        "Veldhara_ISMS_Scope_and_Context_v2.docx",
        "ISMS Scope and Context",
        "isms_scope",
        "2026-07-01",
        "Information Security Lead",
        "Managing Director",
        "2.0",
        [
            ("Organizational context", [
                "Veldhara coordinates road freight through regional depots, a central dispatch function, a small technology team and contracted transport partners.",
                "The ISMS addresses confidentiality, integrity and availability of driver, customer, employee and dispatch information used to provide logistics services.",
                "The largest operating dependencies are the dispatch platform, identity provider, route data feed, payroll service and depot connectivity.",
            ]),
            ("Interested parties and needs", [
                "Drivers expect correct route assignments, limited use of personal information and prompt handling of account problems.",
                "Customers expect delivery records to be available to authorized contacts and protected from unrelated access.",
                "Employees expect payroll and personnel records to be available only to authorized People Services and Finance roles.",
                "Contracted service providers receive documented service and security requirements from their Veldhara owner.",
            ]),
            ("Scope and boundary", [
                "The ISMS covers all Veldhara offices, depots, employees, contractors, logistics services, supporting technology and information handled for those services.",
                "The boundary includes two staffed depots, the Pune operations office, cloud services and internal development of dispatch and driver integrations.",
                "The boundary excludes customer-owned networks and independent carrier systems after the contracted handoff; exchange points and responsibilities are recorded in the supplier register.",
                "The ISMS includes occasional vendor development support where a supplier builds, tests or changes a company integration.",
            ]),
            ("Review", [
                "The Managing Director approved scope version 2.0 on 1 July 2026 after the route integration and mobile product team were added.",
                "The Information Security Lead reviews context annually and after a material service, location or ownership change.",
            ]),
        ],
    ),
    "risk_methodology": _document(
        "Veldhara_Information_Risk_Method_v2.docx",
        "Information Security Risk Method",
        "risk_assessment",
        "2026-07-04",
        "Risk Coordinator",
        "Board Risk Committee",
        "2.0",
        [
            ("Method", [
                "Owners identify information assets, threat events, existing safeguards and business impact with the service owner and risk coordinator.",
                "Likelihood and impact are rated from 1 to 5; the product sets the inherent score and the owner records the residual view after current safeguards.",
                "Risks scoring 15 or higher require a named treatment owner, target date and committee visibility; lower scores may be accepted by the service owner with rationale.",
                "Treatment options are reduce, avoid, transfer or accept. Acceptance above the delegated threshold requires Board Risk Committee approval.",
            ]),
            ("Review triggers", [
                "The register is reviewed each quarter and after an incident, major supplier change, new processing purpose or material vulnerability.",
                "The Risk Coordinator checks that treatment decisions have an owner, due date, planned safeguards and evidence of closure.",
                "A late action remains open until the owner supplies evidence and the risk approver records acceptance or closure.",
            ]),
            ("Version record", [
                "The Board Risk Committee approved version 2.0 on 4 July 2026. The previous annual review was recorded on 19 June 2025.",
            ]),
        ],
    ),
    "risk_register": _document(
        "Veldhara_Information_Risk_Register_Q2_2026.xlsx",
        "Information Risk Register, Q2 FY 2026-27",
        "risk_assessment",
        "2026-09-25",
        "Risk Coordinator",
        "Board Risk Committee",
        "Q2-2026",
        [
            ("Register notes", [
                "The quarterly register review was held on 24 September 2026 and the action owners confirmed dates on 25 September.",
                "Four treatments remain open: incomplete monthly access coverage, supplier assurance backlog, an incident exercise and a database restore test.",
                "The open risks are visible in the Board Risk Committee pack; no risk was marked closed solely because a policy had been approved.",
            ]),
        ],
        headers=("Risk ID", "Scenario", "Inherent", "Current safeguards", "Residual", "Treatment", "Owner", "Due date", "Status"),
        rows=(
            ("R-014", "Leaver identity remains enabled in an unreviewed service", "20", "Joiner/leaver ticket and September review for 9 services", "15", "Complete monthly owner reviews and close removals", "Identity Administrator", "2026-10-16", "Open"),
            ("R-021", "Critical SaaS assurance evidence is not current", "16", "Contracts include security schedule; two reports on file", "12", "Obtain current assurance for Route Insights and Payroll Host", "Supplier Manager", "2026-10-30", "Open"),
            ("R-028", "A restore failure extends a data loss event", "15", "Nightly backup jobs and regional dispatch failover", "10", "Run database restore test and capture record", "IT Operations Manager", "2026-10-31", "Open"),
            ("R-031", "Unexercised incident call tree slows coordinated response", "15", "Approved incident plan and on-call roster", "10", "Run tabletop and update stale contact entries", "Information Security Lead", "2026-10-20", "Open"),
            ("R-036", "Integration change introduces unauthorized data exposure", "12", "Peer review, tests, deployment approval and logging", "6", "Continue monthly sample review", "Engineering Lead", "2026-12-15", "Monitoring"),
        ),
    ),
    "soa": _document(
        "Veldhara_Statement_of_Applicability_v3.xlsx",
        "Statement of Applicability and Treatment Plan",
        "statement_of_applicability",
        "2026-09-26",
        "Information Security Lead",
        "Board Risk Committee",
        "3.0",
        [
            ("Decision basis", [
                "This Statement of Applicability records all 93 Annex A controls as applicable to the Veldhara ISMS scope.",
                "No control is excluded because its operation is inconvenient or evidence was unavailable; deficiencies remain in the treatment plan.",
                "The Board Risk Committee reviewed the applicability decisions on 24 September 2026 and requested owners and dates for open treatments.",
                "The treatment plan carries access review, supplier assurance, incident exercise, training refresh and backup restore actions as open work.",
            ]),
            ("Treatment status", [
                "The access review statement is supported by one completed monthly cycle in the quarter, covering nine of eleven production systems.",
                "The incident plan is approved but not exercised. The scheduled October tabletop is future work and is not reported as completed.",
                "The August failover exercise met its recovery objective; it does not close the separate backup restore action.",
            ]),
        ],
        headers=("Control family", "Applicability", "Basis", "Treatment reference", "Owner"),
        rows=(
            ("Organizational A.5", "Applicable", "Information, suppliers and service operations are in scope", "Risk register R-014/R-021/R-031", "Control owners"),
            ("People A.6", "Applicable", "Employees and contractors handle scoped information", "Training refresh and HR evidence schedule", "People Services"),
            ("Physical A.7", "Applicable", "Two depots and a staffed operations office are in scope", "Facilities review calendar", "Facilities Manager"),
            ("Technological A.8", "Applicable", "Hosted platforms and internal/vendor-assisted development are in scope", "R-014/R-028/R-036", "Technology owners"),
        ),
    ),
    "objectives": _document(
        "Veldhara_ISMS_Objectives_and_Metrics_Q2.xlsx",
        "ISMS Objectives and Monitoring, Q2 FY 2026-27",
        "isms_audit_reports",
        "2026-09-27",
        "Information Security Lead",
        "Board Risk Committee",
        "Q2-2026",
        [
            ("Measurement notes", [
                "The Information Security Lead consolidated July through September measures on 30 September 2026.",
                "Monthly access review completion was one of three scheduled cycles; the single completed September review covered nine of eleven services.",
                "Supplier assurance refresh was incomplete for two critical providers at the reporting cutoff.",
                "All scheduled backup jobs reported success, but no sampled restore test was recorded during the quarter.",
                "The dispatch failover objective was met in August; this measure is reported separately from backup restore readiness.",
            ]),
        ],
        headers=("Objective", "Measure", "Target", "Q2 result", "Owner", "Management response"),
        rows=(
            ("Review access monthly", "Completed cycles", "3 of 3", "1 of 3; September covered 9 of 11 services", "Information Security Lead", "Open R-014; escalate omitted owners"),
            ("Maintain critical supplier assurance", "Current reviews", "All critical providers", "4 of 6 current", "Supplier Manager", "Complete two outstanding evidence requests"),
            ("Recover dispatch service", "Annual failover RTO", "4 hours", "3 hours 10 minutes", "IT Operations Manager", "Target met"),
            ("Prove backup recovery", "Sampled restore tests", "At least one per quarter", "0 recorded", "IT Operations Manager", "Open R-028; test due 31 October"),
            ("Refresh workforce awareness", "Current completion", "At least 95%", "81% at 30 September", "People Services", "Two depot sessions and online refresh planned"),
        ),
    ),
    "internal_audit": _document(
        "Veldhara_Internal_Audit_ISMS_2026.docx",
        "Internal ISMS Audit Report",
        "isms_audit_reports",
        "2026-09-16",
        "Internal Audit Manager",
        "Audit Committee Chair",
        "1.0",
        [
            ("Audit programme", [
                "The annual audit schedule gives priority to high-risk access, supplier, incident, backup and development processes and names a lead auditor for each review.",
                "The 2026 audit plan covered policy and governance, personnel, facility safeguards, supplier records, technical operations and recovery evidence.",
                "The audit objective was to compare defined procedures with a sample of current-period operating records and report whether actions had been effective.",
                "The Audit Committee Chair approved the 2026 schedule on 6 January; scope changes and follow-up dates are retained in the audit plan register.",
            ]),
            ("Mandate and independence", [
                "The Internal Audit Manager reports administratively to Finance and functionally to the Audit Committee Chair for this engagement.",
                "The Information Security Lead did not select samples, perform tests or approve the audit conclusions.",
                "The audit sampled access tickets, supplier files, training records, incident preparation and continuity evidence between 8 and 15 September.",
                "The audit account was read-only and the team recorded no production data changes during testing.",
            ]),
            ("Results", [
                "The reviewer found that July and August access review cycles had no signed decision records and September covered only nine of eleven services.",
                "Four enabled accounts belonged to terminated users and eight approved removals remained open at quarter end.",
                "Supplier files were available for four of six critical services; two owners had not completed their evidence refresh.",
                "The incident procedure had no recorded exercise, and no backup restore result was supplied for the audit sample.",
                "The August dispatch failover report met its four-hour target; it did not test restoration of a retained backup.",
            ]),
            ("Follow-up", [
                "The audit assigned one consolidated access finding and requested owner evidence by 16 October 2026.",
                "Open supplier and recovery actions will be rechecked in the November audit committee meeting.",
            ]),
        ],
    ),
    "management_review": _document(
        "Veldhara_Management_Review_2026-09-24.docx",
        "ISMS Management Review Minutes",
        "isms_audit_reports",
        "2026-09-24",
        "Company Secretary",
        "Managing Director",
        "Approved 2026-09-28",
        [
            ("Meeting record", [
                "The Board Risk Committee and senior service owners met on 24 September 2026 to review ISMS performance and changes in context.",
                "Attendees were the Managing Director, Operations Director, Information Security Lead, Risk Coordinator, People Services Manager and Internal Audit Manager.",
                "The committee reviewed the July-September objective measures, internal audit observations, supplier changes, risks and open corrective actions.",
            ]),
            ("Decisions", [
                "The committee retained the current scope and confirmed all 93 Annex A controls remain applicable.",
                "The Information Security Lead will escalate missing TMS and driver-app review decisions at the 16 October operations meeting.",
                "The Supplier Manager will obtain the two outstanding critical provider assurance packages by 30 October.",
                "The IT Operations Manager will run a database restore test by 31 October and retain the job, sample and recovery result.",
                "People Services will schedule the missed depot awareness refresh before 15 November and report completion at the next quarterly review.",
                "The incident plan tabletop remains scheduled for 20 October; the committee asked that the contact tree be verified before the exercise.",
            ]),
            ("Approval", [
                "The Managing Director approved these minutes on 28 September 2026; action owners accepted the dates shown in the committee register.",
            ]),
        ],
    ),
    "policy_acknowledgements": _document(
        "Veldhara_Policy_Acknowledgement_Export_Q2.xlsx",
        "Policy Receipt and Acknowledgement Export",
        "security_policy",
        "2026-09-28",
        "People Services Manager",
        "Information Security Lead",
        "Q2-2026",
        [
            ("Export notes", [
                "The portal issued the current policy to all 280 employees and active depot contractors on 1 July 2026.",
                "The 28 September export shows 274 acknowledgements and six overdue reminders; one reminder was assigned to a manager for follow-up.",
                "The policy portal stores version, recipient, delivery time and acknowledgement time for each record.",
            ]),
        ],
        headers=("Personnel ID", "Group", "Policy version", "Delivered", "Acknowledged", "Status"),
        rows=(
            ("EMP-014", "Pune office", "3.1", "2026-07-01", "2026-07-01", "Acknowledged"),
            ("EMP-108", "East depot", "3.1", "2026-07-01", "2026-07-02", "Acknowledged"),
            ("CTR-033", "West depot contractor", "3.1", "2026-07-01", "2026-07-03", "Acknowledged"),
            ("EMP-219", "West depot", "3.1", "2026-07-01", "", "Reminder sent 2026-09-26"),
        ),
    ),
    "legal_ip_register": _document(
        "Veldhara_Legal_Contract_and_IP_Register_Q2.xlsx",
        "Legal, Contract and Intellectual Property Register",
        "legal_register",
        "2026-09-24",
        "Legal and Commercial Lead",
        "Operations Director",
        "Q2-2026",
        [
            ("Register notes", [
                "The Legal and Commercial Lead reviewed the register with service owners on 24 September 2026.",
                "The register identifies requirements by service owner, source, review date and evidence location; the owner checks changes at renewal or when scope changes.",
                "The code inventory records repository, licence family, owner and approval source for third-party components used by production integrations.",
                "The September code sample had source attribution and approved licences for 18 of 18 sampled packages.",
            ]),
        ],
        headers=("Entry", "Requirement or right", "Applies to", "Owner", "Evidence", "Last reviewed"),
        rows=(
            ("LEG-01", "Customer and driver record retention", "Route and claims services", "Privacy Coordinator", "Processing register and retention schedule", "2026-09-29"),
            ("LEG-02", "Customer delivery confidentiality", "Customer delivery contracts", "Legal and Commercial Lead", "Contract template clauses", "2026-08-14"),
            ("LEG-03", "Third-party software licences", "Integration repositories", "Engineering Lead", "Dependency inventory and licence files", "2026-09-24"),
            ("LEG-04", "Records preservation and legal hold", "Claims and personnel records", "Company Secretary", "Records schedule and hold register", "2026-09-19"),
            ("LEG-05", "Personal information notice and request handling", "Driver and consignee records", "Privacy Coordinator", "Notice register and request log", "2026-09-29"),
        ),
    ),
    "records_protection": _document(
        "Veldhara_Records_Retention_and_Protection_Schedule_v2.docx",
        "Business Records Retention and Protection Schedule",
        "legal_register",
        "2026-07-05",
        "Company Secretary",
        "Operations Director",
        "2.0",
        [
            ("Record ownership", [
                "Every record series has a business owner, storage location, access group, retention trigger and disposal method.",
                "Payroll, personnel, customer claims and delivery records are stored in managed services with named owner groups and audit history.",
                "Legal holds suspend routine deletion; the Company Secretary logs the matter, affected record series and release approval.",
            ]),
            ("Operating review", [
                "The Company Secretary sampled six record series on 19 September and confirmed the owner and retention trigger were recorded for each.",
                "A claims mailbox export was corrected after a departed coordinator retained an owner role; the role was removed on 20 September.",
                "The September sample did not include a restoration test from a retained record copy.",
            ]),
        ],
    ),
    "privacy_notice": _document(
        "Veldhara_Driver_and_Consignee_Privacy_Notice_v2.docx",
        "Driver and Consignee Privacy Notice",
        "privacy_policy",
        "2026-07-18",
        "Privacy Coordinator",
        "Operations Director",
        "2.0",
        [
            ("Notice content", [
                "The notice identifies Veldhara as the service operator and gives a privacy mailbox for questions and requests.",
                "Drivers are told that identity and licence details are used for onboarding and safety checks, and route location is used while a job is assigned.",
                "Consignees are told that contact details and proof of delivery are used to coordinate delivery and respond to a claim.",
                "The notice links to the retention summary and explains that service providers may process information to provide hosted systems.",
                "The July review found that the driver app location prompt does not link back to the full notice or present a withdrawal route.",
            ]),
            ("Distribution and requests", [
                "The notice is displayed in the driver onboarding portal and linked from the customer delivery tracking page.",
                "The Privacy Coordinator records received questions in the request log and assigns an owner and response date.",
                "The current mobile build screenshot was captured on 29 August; no consent receipt export was provided for the sampled account.",
            ]),
        ],
    ),
    "grievance_register": _document(
        "Veldhara_Privacy_and_Service_Grievance_Log_Q2.xlsx",
        "Privacy and Service Grievance Register",
        "privacy_policy",
        "2026-09-30",
        "Customer Care Manager",
        "Operations Director",
        "Q2-2026",
        [
            ("Handling notes", [
                "Customer Care records complaints and privacy questions in the service grievance queue, then assigns a named responder and due date.",
                "Privacy questions are forwarded to the Privacy Coordinator; the Customer Care Manager checks overdue items each Friday.",
                "The current quarter had one privacy-related request and two routine delivery complaints; none involved a confirmed information security incident.",
                "The privacy request was answered within the internal target and its customer callback was recorded.",
            ]),
        ],
        headers=("Case ID", "Opened", "Type", "Assigned owner", "Response date", "Outcome", "Status"),
        rows=(
            ("GR-26-0719", "2026-07-19", "Delivery complaint", "Customer Care Lead", "2026-07-20", "Address corrected and customer called", "Closed"),
            ("GR-26-0822", "2026-08-22", "Privacy question: route location", "Privacy Coordinator", "2026-08-24", "Purpose and retention explained; customer callback logged", "Closed"),
            ("GR-26-0907", "2026-09-07", "Missed delivery window", "Depot Operations", "2026-09-08", "Updated delivery estimate sent", "Closed"),
        ),
    ),
    "capacity_report": _document(
        "Veldhara_Service_Capacity_and_Utilization_Q2.xlsx",
        "Service Capacity and Utilization Review",
        "configuration_baselines",
        "2026-09-25",
        "Platform Lead",
        "IT Operations Manager",
        "Q2-2026",
        [
            ("Capacity process", [
                "Platform monitoring records processor, memory, storage and queue utilization for the dispatch and claims services.",
                "The Platform Lead reviews weekly trends and raises a capacity ticket when forecast headroom falls below the approved operating threshold.",
                "The quarter review found no production service above 78 percent sustained capacity and no dispatch queue older than the operating target.",
                "A seasonal route-volume forecast was reviewed with Network Planning on 25 September before the festival delivery period.",
            ]),
        ],
        headers=("Service", "Peak CPU", "Peak storage", "Queue measure", "Forecast action", "Review date"),
        rows=(
            ("Core Dispatch", "71%", "63%", "4 minutes maximum", "No scale change required", "2026-09-25"),
            ("Customer Claims", "54%", "58%", "Within 8 minute target", "Watch October volume", "2026-09-25"),
            ("Route Integration", "42%", "39%", "No backlog", "No action", "2026-09-25"),
        ),
    ),
    "approval_scan": _document(
        "Veldhara_Board_Risk_Minutes_Approval_2026-07-01.pdf",
        "Board Risk Committee Approval Extract",
        "isms_audit_reports",
        "2026-07-01",
        "Company Secretary",
        "Board Risk Committee Chair",
        "Signed extract",
        [
            ("Meeting extract", [
                "The Board Risk Committee met on 1 July 2026 and approved Information Security Policy version 3.1.",
                "The committee confirmed the ISMS covers Veldhara offices, depots, cloud services and internal integration development.",
                "The committee asked management to bring unresolved access coverage and supplier assurance actions to the September review.",
                "Signed for the committee by the Chair on 1 July 2026.",
            ]),
        ],
        render_as_scan=True,
    ),
    "board_minutes": _document(
        "Veldhara_Board_Risk_Committee_Minutes_Q2_2026.docx",
        "Board Risk Committee Minutes, Q2 FY 2026-27",
        "isms_audit_reports",
        "2026-09-24",
        "Company Secretary",
        "Managing Director",
        "Approved 2026-09-28",
        [
            ("Agenda and attendance", [
                "The Board Risk Committee reviewed changes in the logistics operating context, customer and driver expectations, key suppliers and ISMS performance.",
                "The committee noted the route integration team now maintains two internal services and receives occasional supplier development support.",
                "The committee reviewed five open information risks and confirmed each has an owner, target and treatment decision.",
            ]),
            ("Governance decisions", [
                "Management approved the July 2026 scope statement and the annual policy review before the current quarter began.",
                "The committee confirmed the risk acceptance threshold remains unchanged and no high residual risk was accepted without a named approver.",
                "Internal Audit will independently verify closure evidence rather than rely on owner status alone.",
                "The committee requested a separate restore test because the August failover exercise did not read data back from a backup copy.",
            ]),
        ],
    ),
    "board_email_chain": _document(
        "Veldhara_Board_Risk_Email_Chain_2026-09.png",
        "Board Risk Committee Email Chain",
        "isms_audit_reports",
        "2026-09-25",
        "Company Secretary",
        "Board Risk Committee Chair",
        "Email capture",
        [
            ("Email chain", [
                "From: Company Secretary <secretary@veldhara.example> | 24 Sep 2026 16:42",
                "Subject: Q2 ISMS actions and minutes",
                "Attached are the approved minutes and the five actions accepted at today's review. The access review remains limited to nine services and the restore test is still open.",
                "From: Operations Director <operations@veldhara.example> | 25 Sep 2026 09:08",
                "I have confirmed the October dates with IT Operations and the supplier owners. Please keep the monthly access follow-up on the October agenda.",
                "From: Committee Chair <chair@veldhara.example> | 25 Sep 2026 10:16",
                "Received. The minutes should preserve the open status until evidence is checked.",
            ]),
        ],
    ),
    "roles": _document(
        "Veldhara_Security_Roles_and_RACI_v2.docx",
        "Information Security Roles and Responsibility Matrix",
        "roles_responsibilities",
        "2026-07-02",
        "Information Security Lead",
        "Managing Director",
        "2.0",
        [
            ("Role ownership", [
                "The Managing Director is accountable for ISMS direction and approves high residual risk acceptance.",
                "The Information Security Lead maintains policies, coordinates response and reports security performance to management.",
                "The Risk Coordinator records risk owners, treatment dates and committee decisions.",
                "System owners approve access, classify their information and confirm service changes before release.",
                "The Identity Administrator provisions directory access, reconciles monthly review results and records removal closure.",
                "The Internal Audit Manager independently samples control records and reports results to the Audit Committee Chair.",
            ]),
            ("Segregation and small-team safeguards", [
                "Access requesters cannot approve their own production access; a system owner or line manager must approve each grant.",
                "The integration developer cannot approve their own production deployment; the platform release manager checks the ticket and deployment log.",
                "Where a small depot team cannot separate a local task, the Operations Director reviews the activity log monthly.",
                "The Identity Administrator can process removals but cannot certify their own monthly review sample.",
            ]),
            ("Assignment and review", [
                "The Company Secretary records the current role holder and delegated cover in the access-controlled governance directory.",
                "The Managing Director reviewed role assignments on 2 July 2026; changes are raised through the personnel change process.",
            ]),
        ],
    ),
    "asset_inventory": _document(
        "Veldhara_Information_Asset_Inventory_Q2.xlsx",
        "Information and Technology Asset Inventory",
        "asset_inventory",
        "2026-09-23",
        "Asset Coordinator",
        "Information Security Lead",
        "Q2-2026",
        [
            ("Inventory notes", [
                "Service owners confirmed the production inventory on 23 September 2026; the next owner attestation is due in December.",
                "Restricted information includes driver identity records, precise route location, payroll bank details and credentials used for service administration.",
                "The inventory records system owner, hosting boundary, information class, recovery dependency and approved supplier for each production service.",
                "The TMS and driver mobile app are listed as production assets even though their September access export was not returned.",
            ]),
        ],
        headers=("Asset ID", "Service or information set", "Owner", "Classification", "Hosting", "Dependency", "Review date"),
        rows=(
            ("AS-001", "Core Dispatch", "Network Planning", "Confidential", "Hosted service", "Identity provider; route feed", "2026-09-23"),
            ("AS-002", "Transport Management System", "Linehaul Operations", "Restricted", "Hosted service", "Identity provider; carrier link", "2026-09-23"),
            ("AS-003", "Driver mobile app", "Driver Experience", "Restricted", "Hosted service", "Identity provider; location API", "2026-09-23"),
            ("AS-004", "Payroll records", "Finance", "Restricted", "Supplier SaaS", "Payroll Host", "2026-09-23"),
            ("AS-005", "Customer delivery contacts", "Customer Care", "Confidential", "Hosted service", "Customer Claims", "2026-09-23"),
            ("AS-006", "Integration source repositories", "Engineering Lead", "Confidential", "Managed code service", "Cloud Code Host", "2026-09-23"),
            ("AS-007", "Backups and recovery copies", "IT Operations", "Restricted", "Hosted service and immutable store", "Cloud Region B", "2026-09-23"),
            ("AS-008", "Pune operations office", "Facilities Manager", "Internal", "Company premises", "Badge and visitor systems", "2026-09-23"),
        ),
    ),
    "classification_guide": _document(
        "Veldhara_Information_Classification_and_Labelling_v1.docx",
        "Information Classification and Labelling Guide",
        "asset_inventory",
        "2026-07-07",
        "Asset Coordinator",
        "Information Security Lead",
        "1.0",
        [
            ("Classification", [
                "Public information may be shared without access controls after owner approval.",
                "Internal information is for personnel and contracted workers with a business need.",
                "Confidential information includes customer delivery details, route plans and non-public operating measures.",
                "Restricted information includes driver identity, live location, payroll bank details, authentication material and investigation records.",
            ]),
            ("Labels and handling", [
                "Owners apply a visible label to exported files and set the repository classification for records that remain in a managed service.",
                "Email containing Restricted information must use an approved encrypted transfer route and a separately managed recipient list.",
                "Printed Restricted records remain in a locked cabinet when unattended and are destroyed through the confidential waste service.",
                "The Asset Coordinator sampled eight active repositories on 20 September; seven carried the expected label and one old route workbook was corrected on 21 September.",
            ]),
        ],
    ),
    "supplier_register": _document(
        "Veldhara_Critical_Supplier_Register_Q2.xlsx",
        "Critical Supplier and Cloud Service Register",
        "supplier_security",
        "2026-09-26",
        "Supplier Manager",
        "Risk Coordinator",
        "Q2-2026",
        [
            ("Register notes", [
                "The Supplier Manager reconciled critical services and business owners on 26 September 2026.",
                "Six services are rated critical because they handle identity, payroll, routes, customer records or production source code.",
                "Four current assurance packages were reviewed in the quarter; Route Insights and Payroll Host remain pending refresh.",
                "The Supplier Manager did not maintain a common review calendar; assurance requests were raised when a contract owner asked or a renewal approached.",
                "Contracts are available for all six listed services, but contract presence does not establish current operational assurance.",
            ]),
        ],
        headers=("Supplier ID", "Service", "Business owner", "Data or access", "Criticality", "Agreement", "Latest assurance", "Next action"),
        rows=(
            ("SUP-01", "Cloud Identity Service", "IT Operations", "Identity metadata", "Critical", "2026-03-12", "2026-05-10", "Review next cycle"),
            ("SUP-02", "Core Dispatch Host", "Network Planning", "Route and delivery records", "Critical", "2026-01-18", "2026-06-21", "Review next cycle"),
            ("SUP-03", "Payroll Host", "Finance", "Payroll and bank details", "Critical", "2025-11-02", "2025-08-14", "Assurance request overdue"),
            ("SUP-04", "Route Insights", "Network Planning", "Aggregated route data", "Critical", "2026-02-08", "2025-07-30", "Assurance request overdue"),
            ("SUP-05", "Cloud Code Host", "Engineering Lead", "Source repositories", "Critical", "2026-04-09", "2026-07-02", "Review next cycle"),
            ("SUP-06", "Service Desk", "IT Operations", "Business account IDs and logs", "High", "2026-04-20", "2026-08-11", "Review next cycle"),
        ),
    ),
    "supplier_contracts": _document(
        "Veldhara_Supplier_Security_Schedules_Extract.docx",
        "Supplier Security Schedule Extracts",
        "supplier_security",
        "2026-09-20",
        "Supplier Manager",
        "Legal and Commercial Lead",
        "Sample set 1.2",
        [
            ("Agreement terms", [
                "The Core Dispatch Host agreement requires access logging, annual assurance delivery, incident contact and return or deletion of company information at exit.",
                "The Payroll Host schedule requires named support access, confidentiality, incident escalation and approved subprocessors.",
                "The Cloud Code Host schedule requires private repositories, named contractor accounts, multifactor authentication and return of source material at exit.",
                "The Route Insights contract names the service and data return terms but has no attached current assurance package in the supplier file.",
                "The Supplier Manager checks agreement renewal and subprocessors when the service owner reports a change; a consolidated change review was not completed this quarter.",
            ]),
            ("Operational follow-up", [
                "An assurance request was sent to the Payroll Host on 5 September and remains unanswered at 30 September.",
                "The Route Insights owner requested a refreshed report on 8 September; the supplier provided a delivery estimate but no report by cutoff.",
                "No evidence package is recorded for an annual review of each critical supplier's security performance.",
            ]),
        ],
    ),
    "cloud_review": _document(
        "Veldhara_Cloud_Service_Review_Q2_2026.docx",
        "Cloud Service Use and Exit Review",
        "cloud_services",
        "2026-09-19",
        "Cloud Service Owner",
        "Information Security Lead",
        "1.0",
        [
            ("Service lifecycle", [
                "The cloud register identifies the service owner, information class, account administrator, renewal date and documented export path for six hosted services.",
                "New cloud services require owner approval, privacy review, security requirements and an exit plan before production information is uploaded.",
                "The Cloud Identity Service and Core Dispatch Host were reviewed on 19 September; the Payroll Host and Route Insights assurance refresh remain open.",
                "A service exit must disable accounts, export business records, confirm supplier deletion and transfer any required records to the named owner.",
            ]),
            ("Operational checks", [
                "The Cloud Identity owner exported administrator activity on 12 September and confirmed no unapproved admin grant in the sample.",
                "The Core Dispatch owner reviewed the provider's June assurance report and logged one monitoring question for the October meeting.",
                "The supplier register lists all six critical hosted services; two assurance updates were not complete at quarter end.",
            ]),
        ],
    ),
    "threat_digest": _document(
        "Veldhara_Threat_Advisory_Digest_Q2_2026.docx",
        "Security Advisory Digest and Circulation Log",
        "vulnerability_management",
        "2026-09-30",
        "Security Analyst",
        "Information Security Lead",
        "Q2-2026",
        [
            ("Sources and assessment", [
                "The Security Analyst checks advisories from the national incident response bulletin, the cloud identity provider, the code-host provider and the endpoint protection service.",
                "Each item is rated for affected service, exposure, available fix and owner; relevant items are entered in the vulnerability queue.",
                "The analyst circulated three relevant advisories to IT Operations and Engineering on 11 July, 6 August and 12 September.",
                "No membership or active subscription to a logistics-sector security forum was recorded in the quarter.",
            ]),
            ("Quarter activity", [
                "Advisory TA-26-071 identified an exposed library version in the test image; the Engineering Lead updated the base image on 15 July.",
                "Advisory TA-26-144 prompted an identity provider configuration check on 8 August; no affected tenant setting was found.",
                "Advisory TA-26-201 is assigned for review at the October operations meeting because the provider notice did not identify a Veldhara account.",
            ]),
        ],
    ),
    "incident_log": _document(
        "Veldhara_Information_Security_Incident_Log_Q2.xlsx",
        "Security Event and Incident Register",
        "incident_log",
        "2026-09-30",
        "Incident Coordinator",
        "Information Security Lead",
        "Q2-2026",
        [
            ("Register note", [
                "The register includes reported events triaged from 1 July through 30 September 2026.",
                "The quarter had no event classified as a confirmed information security incident; two service desk events were reviewed and closed as routine operational errors.",
                "No incident-response exercise or simulated escalation was recorded during the quarter.",
                "The plan owner will retain exercise actions in a separate record after the scheduled October tabletop.",
            ]),
        ],
        headers=("Event ID", "Reported", "Summary", "Initial classification", "Decision", "Reviewer", "Record status"),
        rows=(
            ("EV-26-0712", "2026-07-12", "Depot user reported a route screen loading slowly", "Service issue", "No security indicators found after log check", "Incident Coordinator", "Closed 2026-07-13"),
            ("EV-26-0826", "2026-08-26", "Two failed sign-ins after a handset replacement", "Access support", "User verified; no unauthorized session found", "IT Operations", "Closed 2026-08-27"),
        ),
    ),
    "training_records": _document(
        "Veldhara_Security_Awareness_Completion_Q2.xlsx",
        "Security Awareness and Training Completion",
        "training_records",
        "2026-09-30",
        "People Services Manager",
        "Operations Director",
        "Q2-2026",
        [
            ("Training programme", [
                "New starters receive a security induction covering account safety, route information, reporting channels and restricted records.",
                "The annual refresher is assigned to employees and depot contractors through the People Services learning portal.",
                "The expected annual refresh date passed on 31 August 2026; two depot groups did not complete the refresher before quarter end.",
                "Completion was 81 percent at 30 September; the remaining staff were assigned catch-up sessions for October and November.",
                "Managers received a weekly overdue list, but no manager sign-off was retained for the two incomplete depot groups.",
            ]),
        ],
        headers=("Group", "Assigned", "Complete by 2026-09-30", "Completion", "Overdue", "Follow-up"),
        rows=(
            ("Pune office", 84, 78, "93%", 6, "Portal reminder"),
            ("East depot", 96, 78, "81%", 18, "Session booked 2026-10-22"),
            ("West depot", 72, 44, "61%", 28, "Session booked 2026-11-05"),
            ("Technology and support", 28, 28, "100%", 0, "Complete"),
            ("Total", 280, 228, "81%", 52, "52 overdue at cutoff"),
        ),
    ),
    "hr_records": _document(
        "Veldhara_People_Security_Procedures_v2.docx",
        "People Security and Employment Procedure",
        "hr_security",
        "2026-07-03",
        "People Services Manager",
        "Operations Director",
        "2.0",
        [
            ("Screening and terms", [
                "People Services verifies identity and role-relevant references before a staff member receives production access.",
                "Employment terms describe acceptable use, confidentiality, incident reporting and return of company property.",
                "Contractors sign confidentiality terms and receive a named sponsor, expiry date and restricted account profile.",
                "Screening records are retained in the personnel system with access limited to People Services.",
            ]),
            ("Quarter sample", [
                "People Services sampled three July through September joiner files on 22 September; identity and role checks preceded the first production access grant in each file.",
                "The same sample showed signed employment or contractor terms and confidentiality acknowledgements before service access was approved.",
                "Contractor CTR-041 had a named sponsor, an expiry date of 30 September and a private repository account closed on that date.",
                "The sample did not include every depot contractor file; the People Services Manager scheduled a wider check for October.",
            ]),
            ("Joiner, mover and leaver events", [
                "People Services sends a role-change notice to the Identity Administrator and affected system owners within one business day.",
                "The Identity Administrator records each leaver disable request against the personnel event and confirms closure to the manager.",
                "Exit checklists include return of badge, device, keys and issued storage media; the manager records any missing property.",
                "The September access workbook shows four terminated identities that remained enabled at quarter end despite approved removal actions.",
            ]),
            ("Conduct and ongoing duties", [
                "The conduct procedure describes investigation, employee response and proportionate disciplinary review for repeated security breaches.",
                "Confidentiality obligations continue after employment or contract end and are recorded with the signed agreement.",
                "People Services changes access when an employee transfers between depot, finance and technology roles.",
            ]),
        ],
        headers=("Personnel ID", "Event", "Screening verified", "Terms signed", "Confidentiality", "Production access", "Owner check"),
        rows=(
            ("EMP-213", "Joiner 2026-07-11", "2026-07-09", "2026-07-10", "2026-07-10", "2026-07-12", "Sampled 2026-09-22"),
            ("CTR-041", "Contractor 2026-08-16", "2026-08-14", "2026-08-15", "2026-08-15", "2026-08-18", "Sponsor and expiry checked"),
            ("EMP-244", "Joiner 2026-09-03", "2026-09-01", "2026-09-02", "2026-09-02", "2026-09-04", "Sampled 2026-09-22"),
        ),
    ),
    "remote_work": _document(
        "Veldhara_Remote_Work_and_Endpoint_Standard_v2.docx",
        "Remote Work and Endpoint Standard",
        "remote_working_policy",
        "2026-07-08",
        "IT Operations Manager",
        "Information Security Lead",
        "2.0",
        [
            ("Remote access", [
                "Remote staff connect through the managed identity gateway with multifactor authentication and a company-managed endpoint.",
                "Personnel protect screens from public view, lock devices when unattended and avoid discussing route or driver details in public areas.",
                "Remote work outside approved locations requires manager approval and a check that Restricted records remain in managed services.",
            ]),
            ("Endpoint maintenance", [
                "Company laptops use full-disk encryption, endpoint protection, centrally managed updates and screen lock after ten minutes.",
                "Lost or stolen equipment is reported to the service desk immediately so the device can be isolated and its credentials reviewed.",
                "IT Operations sampled 26 active laptops on 16 September; two had updates pending and both were patched by 19 September.",
                "The clear desk and clear screen reminder was included in the July staff bulletin and depot supervisor briefing.",
            ]),
        ],
    ),
    "physical_security": _document(
        "Veldhara_Facilities_Security_Inspection_Q2.docx",
        "Facilities Security Inspection Record",
        "physical_security",
        "2026-09-17",
        "Facilities Manager",
        "Operations Director",
        "Q2-2026",
        [
            ("Premises and entry", [
                "The Pune operations office and two staffed depots use badge-controlled staff entry and a visitor sign-in register.",
                "Visitors receive a temporary badge, remain with a host in controlled work areas and return the badge before departure.",
                "The Facilities Manager compared active badge holders with the staff list on 17 September and disabled three badges for departed contractors.",
            ]),
            ("Rooms, monitoring and environment", [
                "The network closet at the Pune office remains locked; access is limited to IT Operations and the facilities duty manager.",
                "Door alarms and camera coverage are checked at the start of each facilities shift; recorded exceptions are sent to the Facilities Manager.",
                "Smoke detection, fire suppression and temperature alarms were inspected by the building service provider on 12 August.",
                "The depot generator was load-tested on 21 August; the office UPS battery warning was replaced on 22 August.",
            ]),
            ("Equipment and maintenance", [
                "Network equipment is kept in locked cabinets above floor level and away from the loading bay and water line.",
                "A facilities work order records the technician, maintenance window and escort for equipment repairs in secure rooms.",
                "A cable tray inspection on 17 September found one loose patch-cord label, corrected before the inspector left.",
            ]),
        ],
        headers=("Check", "Pune office", "East depot", "West depot", "Date"),
        rows=(
            ("Badge comparison", "Complete; 3 old badges disabled", "Complete", "Complete", "2026-09-17"),
            ("Visitor log sample", "No unescorted visitors found", "One missing host close time corrected", "No exception", "2026-09-17"),
            ("Environmental equipment", "UPS battery replaced", "Generator test passed", "Alarm test passed", "2026-08-22"),
            ("Secure-room access", "One maintenance visit escorted", "Not applicable to site", "Not applicable to site", "2026-09-17"),
        ),
    ),
    "media_register": _document(
        "Veldhara_Media_Handling_and_Disposal_Log_Q2.xlsx",
        "Storage Media, Deletion and Disposal Log",
        "media_disposal",
        "2026-09-28",
        "Asset Coordinator",
        "Information Security Lead",
        "Q2-2026",
        [
            ("Handling rules", [
                "Removable media is issued only for an approved operational need and recorded to a named custodian.",
                "Restricted information must be deleted from a service using the approved owner request and deletion confirmation process.",
                "Equipment scheduled for reuse is reset and checked by IT Operations; failed storage media is destroyed through the contracted secure disposal service.",
            ]),
            ("Quarter records", [
                "Four retired storage devices were collected on 12 August; the disposal provider issued serial-linked destruction receipts on 19 August.",
                "Two user deletion requests were completed on 6 and 22 September, with owner confirmation attached to the service desk ticket.",
                "A test database copy was masked before use in the integration test environment on 14 September.",
            ]),
        ],
        headers=("Record", "Asset or request", "Action", "Completed", "Verification", "Status"),
        rows=(
            ("MED-2612", "Storage devices D-301 to D-304", "Secure destruction", "2026-08-19", "Provider receipt SD-884", "Closed"),
            ("DEL-2606", "Former consignee contact", "Service deletion", "2026-09-06", "Owner checked export", "Closed"),
            ("DEL-2622", "Duplicate test profile", "Service deletion", "2026-09-22", "Test owner verified", "Closed"),
            ("TST-2614", "Route integration test copy", "Mask before test", "2026-09-14", "Engineering peer review", "Closed"),
        ),
    ),
    "vulnerability_report": _document(
        "Veldhara_Vulnerability_and_Patch_Report_Q2.xlsx",
        "Vulnerability and Patch Management Report",
        "vulnerability_management",
        "2026-09-27",
        "Security Analyst",
        "IT Operations Manager",
        "Q2-2026",
        [
            ("Process and results", [
                "Production images are scanned weekly and externally reachable services are scanned after material configuration changes.",
                "Critical vulnerabilities are assigned a four-day target, high vulnerabilities a 14-day target and lower items are risk-ranked by the service owner.",
                "The September scan found one high issue in a test image and three medium library updates; production services had no overdue critical issue at cutoff.",
                "The Engineering Lead patched the test image on 15 July and attached the scan result to the change record.",
                "A third-party penetration test was completed on 6 August; one medium finding remains scheduled for the next release window.",
            ]),
        ],
        headers=("Finding", "Asset", "Severity", "Detected", "Target", "Closed or status", "Reference"),
        rows=(
            ("VUL-071", "Integration test image", "High", "2026-07-11", "2026-07-15", "Closed 2026-07-15", "CHG-26-0715"),
            ("VUL-144", "Route Insights connector library", "Medium", "2026-08-06", "2026-09-05", "Fix in next release", "CHG-26-0918"),
            ("VUL-201", "Public claims endpoint", "Low", "2026-09-12", "2026-10-12", "Open within target", "SEC-26-201"),
        ),
    ),
    "configuration_baseline": _document(
        "Veldhara_Secure_Configuration_Baseline_v3.docx",
        "Secure Configuration and Malware Protection Baseline",
        "configuration_baselines",
        "2026-07-10",
        "Platform Lead",
        "Information Security Lead",
        "3.0",
        [
            ("Build standards", [
                "Production images use approved base versions, encrypted storage, restricted administration and endpoint malware protection.",
                "Privileged command-line utilities are limited to the platform administrator group and activity is forwarded to the managed log workspace.",
                "Platform engineers record deviations in a baseline exception ticket with owner, risk and expiry date.",
                "Endpoint signatures update automatically; the Security Analyst reviews failed update alerts each business day.",
                "Configuration changes are compared with the approved baseline during the monthly platform review.",
            ]),
            ("Operating sample", [
                "The 12 September configuration report sampled 38 production hosts; 36 matched the approved baseline and two were corrected by 16 September.",
                "The 19 September malware console export showed all 280 enrolled endpoints reporting current signatures.",
                "No production baseline exception had passed its recorded expiry date at the quarter cutoff.",
            ]),
        ],
    ),
    "logging_review": _document(
        "Veldhara_Logging_and_Monitoring_Review_Q2.xlsx",
        "Logging, Monitoring and Time Review",
        "logging_monitoring",
        "2026-09-29",
        "Security Analyst",
        "Information Security Lead",
        "Q2-2026",
        [
            ("Standards", [
                "Identity, administrator, network gateway and dispatch application events are forwarded to the managed log workspace.",
                "The monitoring desk reviews priority alerts during staffed hours and pages the on-call engineer for a critical service alert.",
                "Production services synchronize to the approved time source; the platform checks drift during its weekly health report.",
                "Privileged activity logs are retained for 365 days and routine service logs for 180 days unless an incident hold applies.",
            ]),
            ("Period operation", [
                "The analyst reviewed 15 sampled alert cases from July through September; one dispatch burst was escalated to the service owner and closed as expected batch activity.",
                "A 21 August time-drift alert on the test image was corrected before the next release.",
                "The 28 September retention check found the sampled privileged events available for the required period.",
            ]),
        ],
        headers=("Check ID", "Evidence", "Reviewer", "Result", "Date"),
        rows=(
            ("LOG-072", "Identity alert sample", "Security Analyst", "No unexplained administrator sign-in", "2026-07-29"),
            ("LOG-151", "Dispatch service alert", "Monitoring Desk", "Escalated and closed after owner confirmation", "2026-08-28"),
            ("LOG-228", "Privileged log retention sample", "Security Analyst", "Events available for 365 days", "2026-09-28"),
            ("CLK-221", "Test image time drift", "Platform Lead", "Corrected and rechecked", "2026-08-22"),
        ),
    ),
    "network_review": _document(
        "Veldhara_Network_Security_Review_Q2.docx",
        "Network Security and Segmentation Review",
        "network_security",
        "2026-09-21",
        "Network Operations Lead",
        "IT Operations Manager",
        "Q2-2026",
        [
            ("Network design", [
                "Depot office, guest wireless, corporate endpoints and hosted production services use separate network zones and documented service paths.",
                "Network rules require an owner, business reason and review date; default inbound routes are denied at the managed gateway.",
                "The corporate web gateway blocks known malicious and unapproved categories and records exceptions for manager approval.",
                "The September rule review sampled 34 production paths and removed two expired vendor rules on 21 September.",
            ]),
            ("Service and connection operation", [
                "The managed network provider's August service review recorded no unresolved critical outage or unapproved route change.",
                "The Network Operations Lead compared the depot guest network and corporate route on 18 September and confirmed guest clients could not reach the dispatch segment.",
                "The claims web gateway blocked three test categories on 19 September; the result was recorded in the change log.",
            ]),
        ],
    ),
    "crypto_key_log": _document(
        "Veldhara_Cryptography_and_Key_Review_Q2.docx",
        "Cryptography and Key Management Review",
        "cryptography_policy",
        "2026-09-12",
        "Platform Lead",
        "Information Security Lead",
        "1.1",
        [
            ("Cryptographic requirements", [
                "Restricted information is encrypted in transit over approved service connections and at rest in managed production storage.",
                "Keys are held in the managed key service, separated from encrypted data and limited to named platform administrators.",
                "Key rotation uses the provider schedule or a documented event trigger; emergency rotation requires a second administrator check.",
                "The platform owner records algorithm, key owner, rotation date and dependent service in the cryptographic inventory.",
            ]),
            ("Quarter operation", [
                "The 12 September review confirmed two production keys rotated within their scheduled period and one development key retired after a contractor change.",
                "A quarterly access sample found no standing key export permission outside the platform administrator group.",
                "The key recovery procedure was reviewed but not exercised during this quarter.",
            ]),
        ],
    ),
    "change_management": _document(
        "Veldhara_Change_and_Release_Procedure_v2.docx",
        "Change and Release Procedure",
        "change_management",
        "2026-07-06",
        "Platform Lead",
        "IT Operations Manager",
        "2.0",
        [
            ("Change approval", [
                "A production change requires a ticket with business purpose, affected service, test evidence, security impact, rollback steps and named approver.",
                "The requester cannot approve their own deployment; the release manager checks the approved build identifier against the deployment record.",
                "Emergency changes are contained to the minimum needed and receive a documented next-business-day review.",
                "Software installation on production systems is limited to the platform release group and approved automation account.",
            ]),
            ("Quarter sample", [
                "Internal Audit sampled twelve production changes from July through September; all twelve had an approval and post-deployment record.",
                "Change CHG-26-0918 includes reviewer, test output, approval timestamp and production deployment log for the route integration.",
                "The 12 September sampling found one emergency change reviewed the next business day within the procedure.",
            ]),
        ],
        headers=("Change ID", "Service", "Requester", "Reviewer", "Test reference", "Deployment", "Post-check"),
        rows=(
            ("CHG-26-0715", "Integration test image", "Engineering Lead", "Platform Lead", "VUL-071", "2026-07-15 16:12", "Passed 16:30"),
            ("CHG-26-0818", "Dispatch failover configuration", "IT Operations", "Network Operations Lead", "DR exercise record", "2026-08-18 09:05", "Passed 12:15"),
            ("CHG-26-0918", "Route integration", "Integration Engineer", "Platform Lead", "APP-TEST-0926", "2026-09-26 17:40", "Passed 18:05"),
        ),
    ),
    "sdlc_standard": _document(
        "Veldhara_Secure_Development_Standard_v1.docx",
        "Secure Development and Engineering Standard",
        "sdlc_policy",
        "2026-07-12",
        "Engineering Lead",
        "Information Security Lead",
        "1.0",
        [
            ("Scope and roles", [
                "The standard applies to the four-person integration team and supplier engineers who build or change Veldhara software connections.",
                "Internal development includes the dispatch connector, driver status service and data exchange jobs; vendor support is limited to approved integration tasks.",
                "The Engineering Lead owns design review. A separate platform reviewer approves production release and source repository membership.",
            ]),
            ("Source and coding", [
                "Repositories are private, protected branches require peer review and production secrets are stored outside source code.",
                "Engineers follow input validation, safe error handling, dependency review and logging rules for route and driver information.",
                "The reviewer checks changed data fields against the processing register before accepting a feature that changes personal information use.",
                "A supplier engineer uses a named account with an expiry date and may not deploy directly to production.",
            ]),
            ("Testing and environments", [
                "Development, test and production accounts are separated; production data is masked before use in test.",
                "A release requires unit tests, integration tests, security checks, business acceptance and an approved change ticket.",
                "Security tests run on each material change and after a dependency update that changes an exposed service path.",
                "The September sample included a peer-reviewed change, automated checks and a production post-check for the route integration.",
            ]),
            ("Review and records", [
                "The Engineering Lead reviews the standard each year and after a new development supplier or production service is added.",
                "Version 1.0 was approved on 12 July 2026; the next review is due 12 July 2027.",
            ]),
        ],
    ),
    "app_test_report": _document(
        "Veldhara_Application_Security_Test_Report_Q2.docx",
        "Application Security and Acceptance Test Record",
        "application_security_testing",
        "2026-09-26",
        "Engineering Lead",
        "Product Owner",
        "APP-TEST-0926",
        [
            ("Requirements and design", [
                "The route integration ticket records authentication, data minimization, error handling and audit logging requirements before development began.",
                "The design review traced the driver identifier and route location fields to the processing register and limited the service response to the assigned route.",
                "The engineering review included an abuse case for an expired driver session and a replayed delivery event.",
            ]),
            ("Test evidence", [
                "The 26 September test run passed 42 unit checks, 11 integration checks and six security cases before release approval.",
                "The test environment used masked driver identifiers and synthetic route records; no live payroll or location export was copied into the test service.",
                "The product owner accepted the delivery status workflow on 26 September and recorded one non-security display issue for the next sprint.",
                "A supplier developer reviewed the connector library change under account EXT-042; the internal Engineering Lead approved the merge.",
            ]),
        ],
        headers=("Test ID", "Scenario", "Expected result", "Observed result", "Status"),
        rows=(
            ("SEC-01", "Expired driver session", "Reject request and record event", "Rejected; event in audit log", "Pass"),
            ("SEC-02", "Replay delivery event", "Reject duplicate event ID", "Duplicate rejected", "Pass"),
            ("SEC-03", "Unauthorized route lookup", "Return no route details", "No data returned", "Pass"),
            ("ACC-04", "Role boundary for customer user", "Show assigned delivery only", "Assigned delivery shown", "Pass"),
        ),
    ),
    "change_ticket_shot": _document(
        "Veldhara_Change_Ticket_CHG-26-0918.png",
        "Route Integration Change Ticket Capture",
        "change_management",
        "2026-09-26",
        "Engineering Lead",
        "Platform Lead",
        "CHG-26-0918",
        [
            ("Ticket view", [
                "Change CHG-26-0918 | Route integration response filter",
                "Requested by: Integration Engineer | 24 Sep 2026 10:14",
                "Peer review: Platform Lead | 25 Sep 2026 15:52 | Approved",
                "Security test: APP-TEST-0926 | 42 unit, 11 integration, 6 security checks passed",
                "Production approval: Release Manager | 26 Sep 2026 16:20",
                "Deployment: build INT-4.12.8 | 26 Sep 2026 17:40 | Post-check passed 18:05",
            ]),
        ],
    ),
    "deployment_shot": _document(
        "Veldhara_Production_Deployment_INT-4.12.8.png",
        "Production Deployment Record",
        "change_management",
        "2026-09-26",
        "Release Manager",
        "IT Operations Manager",
        "INT-4.12.8",
        [
            ("Deployment console", [
                "Service: Route Integration | Environment: Production",
                "Change reference: CHG-26-0918 | Approved build: INT-4.12.8",
                "Started: 26 Sep 2026 17:40 | Completed: 17:52",
                "Deployment identity: svc-release-prod | Approval checked by Release Manager",
                "Health check: Passed 18:05 | Route sample: 12 of 12 confirmed",
                "Rollback: Not required | Log event: DEP-2026-0926-44",
            ]),
        ],
    ),
    "outsourced_dev_review": _document(
        "Veldhara_Outsourced_Development_Oversight_Q2.docx",
        "Supplier Development Access and Oversight Review",
        "outsourced_development",
        "2026-09-30",
        "Engineering Lead",
        "Information Security Lead",
        "Q2-2026",
        [
            ("Vendor scope and terms", [
                "Occasional supplier engineers support connector maintenance under a named work order and the Cloud Code Host agreement.",
                "The agreement requires confidentiality, named accounts, private repository access, return of source material and Veldhara approval before release.",
                "Supplier developers cannot use production deployment credentials or approve their own merge.",
            ]),
            ("Quarter operation", [
                "External account EXT-042 was approved for the route integration ticket, reviewed by the Engineering Lead and expired on 30 September.",
                "The sampled supplier change was peer reviewed internally, security tested and deployed by the release manager.",
                "The Supplier Manager did not complete a broader security performance review of development support during the quarter.",
                "No evidence package was received for the supplier's current secure development training or subcontractor screening.",
            ]),
        ],
    ),
    "backup_log": _document(
        "Veldhara_Backup_Operations_and_Restore_Log_Q2.xlsx",
        "Backup Operations and Restore Test Log",
        "backup",
        "2026-09-30",
        "IT Operations Manager",
        "Information Security Lead",
        "Q2-2026",
        [
            ("Schedule and execution", [
                "Core dispatch data is backed up nightly and the completion monitor pages IT Operations for a failed job.",
                "Backup copies use a separate administrative group and an immutable retention window for production datasets.",
                "The daily job console reported successful scheduled copies for all 92 nights in the quarter.",
                "No restore test was recorded between 1 July and 30 September 2026.",
                "The August failover report tested the secondary service path and did not restore data from a backup copy.",
                "The IT Operations Manager accepted action DR-26-08-04 for a database restore test by 31 October 2026.",
            ]),
        ],
        headers=("Period", "Scheduled jobs", "Successful", "Failed", "Restore test", "Reviewer note"),
        rows=(
            ("2026-07", 31, 31, 0, "None recorded", "Daily copies completed"),
            ("2026-08", 31, 31, 0, "None recorded", "Failover test was not a restore"),
            ("2026-09", 30, 30, 0, "None recorded", "Restore action remains open"),
            ("Quarter total", 92, 92, 0, "0 restore tests", "Action DR-26-08-04 due 2026-10-31"),
        ),
    ),
    "objectives_email": _document(
        "Veldhara_ISMS_Objective_Review_Email_2026-09.png",
        "Q2 ISMS Objective Review Email",
        "isms_audit_reports",
        "2026-09-27",
        "Information Security Lead",
        "Operations Director",
        "Email capture",
        [
            ("Email", [
                "From: Information Security Lead <security@veldhara.example> | 27 Sep 2026 14:12",
                "Subject: Q2 objective measures for review",
                "Access coverage is one completed cycle out of three. The completed September file includes nine of eleven systems. The backup job monitor is green, but no restore sample was run.",
                "From: Operations Director <operations@veldhara.example> | 27 Sep 2026 15:06",
                "Please keep the restore action separate from the dispatch failover result and include both owners in the October follow-up.",
            ]),
        ],
    ),
    "access_jul_start": _document(
        "Veldhara_Access_Review_July_Request.png",
        "July Access Review Request Email",
        "access_control_policy",
        "2026-07-02",
        "Identity Administrator",
        "Information Security Lead",
        "Email capture",
        [("Email", [
            "From: Identity Administrator <identity@veldhara.example> | 02 Jul 2026 09:05",
            "To: Production service owners | Subject: July monthly access decisions due 10 July",
            "Please review active users, service roles and administrator accounts in your service export. Return a decision for each account and list any removals by 10 July.",
            "The TMS and driver app owners should send their own exports because both are in the production inventory.",
        ])],
    ),
    "access_jul_followup": _document(
        "Veldhara_Access_Review_July_Followup.png",
        "July Access Review Follow-up Email Chain",
        "access_control_policy",
        "2026-07-20",
        "Identity Administrator",
        "Information Security Lead",
        "Email capture",
        [("Email chain", [
            "From: Identity Administrator <identity@veldhara.example> | 16 Jul 2026 11:22",
            "Subject: Follow-up: July access decisions still outstanding",
            "I have received two partial exports. The TMS, driver app and Finance owner decisions are still missing. Please send the remaining records today so removals can be raised.",
            "From: TMS Owner <tms-owner@veldhara.example> | 17 Jul 2026 08:40",
            "We have not reconciled the contractor account list. I cannot sign the review this week.",
            "From: Information Security Lead <security@veldhara.example> | 20 Jul 2026 09:13",
            "Leave July open in the tracker. Do not treat an export without owner decisions as a completed review.",
        ])],
    ),
    "access_aug_start": _document(
        "Veldhara_Access_Review_August_Request.png",
        "August Access Review Request Email",
        "access_control_policy",
        "2026-08-03",
        "Identity Administrator",
        "Information Security Lead",
        "Email capture",
        [("Email", [
            "From: Identity Administrator <identity@veldhara.example> | 03 Aug 2026 09:18",
            "To: Production service owners | Subject: August access review due 12 August",
            "Please use the August export and confirm manager, role, enabled status and administrator membership for every account by 12 August.",
            "If there is no role change, reply with a retain decision; if access should end, raise a removal request with the account identifier.",
        ])],
    ),
    "access_aug_followup": _document(
        "Veldhara_Access_Review_August_Followup.png",
        "August Access Review Follow-up Email Chain",
        "access_control_policy",
        "2026-08-19",
        "Identity Administrator",
        "Information Security Lead",
        "Email capture",
        [("Email chain", [
            "From: Identity Administrator <identity@veldhara.example> | 18 Aug 2026 10:04",
            "Subject: August review not closed",
            "The warehouse and finance files arrived, but owner decisions for TMS, the driver app and two administrator accounts are still missing. No complete August sign-off is available.",
            "From: Warehouse Owner <warehouse-owner@veldhara.example> | 18 Aug 2026 11:41",
            "I have signed the accounts in my file. The driver app team is waiting for its vendor account export.",
            "From: Information Security Lead <security@veldhara.example> | 19 Aug 2026 08:55",
            "Record August as incomplete and carry the omitted services into the September escalation.",
        ])],
    ),
    "access_sep_start": _document(
        "Veldhara_Access_Review_September_Request.png",
        "September Access Review Request Email",
        "access_control_policy",
        "2026-09-02",
        "Identity Administrator",
        "Information Security Lead",
        "Email capture",
        [("Email", [
            "From: Identity Administrator <identity@veldhara.example> | 02 Sep 2026 08:48",
            "To: Production service owners | Subject: September review; return decisions by 18 September",
            "This is the quarter-close access review. Include enabled accounts, leavers, administrator roles, last login and removal closure evidence.",
            "I will escalate any service without a complete export on 10 September. TMS and driver app owners must confirm a named reviewer.",
        ])],
    ),
    "access_sep_followup": _document(
        "Veldhara_Access_Review_September_Followup.png",
        "September Access Review Follow-up Email Chain",
        "access_control_policy",
        "2026-09-22",
        "Identity Administrator",
        "Information Security Lead",
        "Email capture",
        [("Email chain", [
            "From: Identity Administrator <identity@veldhara.example> | 10 Sep 2026 15:10",
            "Subject: Escalation: September access exports due",
            "Two production owners have not returned their files. Please send TMS and driver app exports by 14 September so we can finish the monthly review.",
            "From: Driver Experience Owner <driver-owner@veldhara.example> | 14 Sep 2026 13:30",
            "The vendor export is still being reconciled. We cannot confirm the accounts by the deadline.",
            "From: Identity Administrator <identity@veldhara.example> | 22 Sep 2026 16:05",
            "The September summary is signed for nine systems. TMS and the driver app are recorded as omitted; eight removal actions remain open, including four terminated users still enabled.",
        ])],
    ),
    "controls_drill": _document(
        "Veldhara_Control_Operations_Sample_Q2.xlsx",
        "Control Operations Sample Register",
        "other",
        "2026-09-30",
        "Information Security Lead",
        "Internal Audit Manager",
        "Q2-2026",
        [
            ("Sample notes", [
                "The sample register indexes operating records from July through September and links each sample to its original service ticket or owner record.",
                "The table records the observed action and date; it is not a certification statement and does not replace source records.",
            ]),
        ],
        headers=("Sample ID", "Activity", "Date", "Source record", "Observed result", "Reviewer"),
        rows=(
            ("OPS-0715", "Test image patch", "2026-07-15", "CHG-26-0715", "Updated and rescanned", "Security Analyst"),
            ("OPS-0818", "Dispatch failover", "2026-08-18", "DR exercise report", "3h 10m; within 4h RTO", "IT Operations Manager"),
            ("OPS-0917", "Facilities inspection", "2026-09-17", "Q2 inspection record", "Badge and alarm sample complete", "Operations Director"),
            ("OPS-0924", "Management review", "2026-09-24", "Approved minutes", "Five actions assigned", "Company Secretary"),
            ("OPS-0926", "Integration release", "2026-09-26", "CHG-26-0918", "Tested, approved, deployed", "Release Manager"),
            ("OPS-0928", "Policy acknowledgement sample", "2026-09-28", "Acknowledgement export", "One overdue employee reminder", "People Services"),
        ),
    ),
}


CONTROL_OUTCOME_TO_ANSWER = {
    "compliant": "fully_implemented",
    "partially_compliant": "partially_implemented",
    "non_compliant": "not_implemented",
    "not_applicable": "not_applicable",
}


def _control(
    outcome: str,
    risk: str,
    rationale: str,
    design: tuple[str, ...],
    operating: tuple[str, ...],
    primary: str,
    quote: str,
    gap: str,
    action: str,
) -> dict:
    return {
        "applicability": "applicable",
        "rationale": rationale,
        "answer": CONTROL_OUTCOME_TO_ANSWER[outcome],
        "notes": " ".join(part for part in (rationale, gap) if part),
        "outcome": outcome,
        "risk": risk,
        "design": list(design),
        "operating": list(operating),
        "quote": quote,
        "primary": primary,
        "gap": gap,
        "action": action,
    }


CONTROLS: dict[str, dict] = {
    # Clause records are supplemental manual-workpaper items. The app registry
    # currently registers Annex A only, so these 23 entries do not alter scope.
    "ISO.C4.1": _control("compliant", "low", "Context applies to a national logistics operator with depots, hosted services and contracted carriers.", ("isms_scope", "risk_methodology"), ("risk_register", "board_minutes"), "isms_scope", "Veldhara coordinates road freight through regional depots, a central dispatch function, a small technology team and contracted transport partners.", "", "Keep the context review on the annual management calendar and revisit it after a material service change."),
    "ISO.C4.2": _control("compliant", "low", "Drivers, customers, employees and service providers have distinct security and privacy expectations recorded by the company.", ("isms_scope", "ropa"), ("management_review", "grievance_register"), "isms_scope", "Drivers expect correct route assignments, limited use of personal information and prompt handling of account problems.", "", "Continue checking interested-party needs during quarter reviews and record new expectations with the owner."),
    "ISO.C4.3": _control("compliant", "low", "The scope includes all offices, depots, hosted services and internal integration work with explicit external boundaries.", ("isms_scope", "approval_scan"), ("board_minutes", "asset_inventory"), "isms_scope", "The ISMS covers all Veldhara offices, depots, employees, contractors, logistics services, supporting technology and information handled for those services.", "", "Reconfirm boundaries when a new depot, carrier interface or hosted service enters operation."),
    "ISO.C4.4": _control("compliant", "low", "The ISMS spans the services and supporting processes that deliver the scoped logistics operation.", ("isms_scope", "roles"), ("management_review", "objectives"), "isms_scope", "The ISMS includes occasional vendor development support where a supplier builds, tests or changes a company integration.", "", "Maintain the process and ownership map when teams or service boundaries change."),
    "ISO.C5.1": _control("compliant", "low", "Management reviews risk and performance, assigns action owners and approves the information security direction.", ("policy", "roles", "risk_methodology"), ("board_minutes", "management_review"), "management_review", "The Managing Director approved these minutes on 28 September 2026; action owners accepted the dates shown in the committee register.", "", "Keep committee decisions and owner acceptance with each quarterly review pack."),
    "ISO.C5.2": _control("partially_compliant", "low", "The approved policy is suitable to the scope and distributed through a tracked staff portal, but six acknowledgements remain overdue.", ("policy",), ("policy_acknowledgements", "approval_scan"), "policy_acknowledgements", "The 28 September export shows 274 acknowledgements and six overdue reminders; one reminder was assigned to a manager for follow-up.", "Six acknowledgements were not complete at the evidence cutoff.", "Close the remaining acknowledgements and preserve manager follow-up."),
    "ISO.C5.3": _control("compliant", "low", "The role matrix assigns approval, operation, risk and independent assurance duties to accountable role holders.", ("roles",), ("policy_acknowledgements", "board_minutes"), "roles", "The Managing Director is accountable for ISMS direction and approves high residual risk acceptance.", "", "Review delegated cover with People Services after personnel changes."),
    "ISO.C6.1": _control("compliant", "medium", "Risk assessment and treatment criteria are defined, reviewed quarterly and applied to current information risks.", ("risk_methodology",), ("risk_register", "board_minutes"), "risk_methodology", "Risks scoring 15 or higher require a named treatment owner, target date and committee visibility; lower scores may be accepted by the service owner with rationale.", "Four treatments remain open, with owners and dates assigned; their open status is visible to management.", "Reassess the open access, supplier and restore risks after their October actions are tested."),
    "ISO.C6.2": _control("partially_compliant", "medium", "Objectives are measurable and reviewed, but several quarterly targets were missed and corrective work remains open.", ("objectives",), ("objectives_email", "management_review"), "objectives", "Monthly access review completion was one of three scheduled cycles; the single completed September review covered nine of eleven services.", "Access review, supplier assurance, training and restore objectives missed their stated quarterly targets.", "Set recovery dates for missed objectives and report their measured status at the next committee meeting."),
    "ISO.C6.3": _control("partially_compliant", "medium", "Changes are planned through change tickets, but the scope and operating model changed during the year and the quarter review identified open dependencies.", ("change_management", "risk_methodology"), ("change_ticket_shot", "risk_register"), "change_ticket_shot", "Security test: APP-TEST-0926 | 42 unit, 11 integration, 6 security checks passed", "The September change sample is strong, but no single change register links every ISMS-level change to the updated risk and resource assessment.", "Add the ISMS change impact check to the quarterly change register before the next scope revision."),
    "ISO.C7.1": _control("compliant", "low", "Named owners and service resources support operation of the defined ISMS processes.", ("roles", "isms_scope"), ("management_review", "physical_security"), "roles", "The Information Security Lead maintains policies, coordinates response and reports security performance to management.", "", "Confirm backup coverage for key security roles during the next annual resource review."),
    "ISO.C7.2": _control("partially_compliant", "medium", "Role expectations are defined, but annual awareness completion is below target and competency refresh is overdue for some depot staff.", ("hr_records", "roles"), ("training_records", "management_review"), "training_records", "The expected annual refresh date passed on 31 August 2026; two depot groups did not complete the refresher before quarter end.", "52 people were overdue at cutoff and two depot groups lacked manager completion sign-off.", "Complete the scheduled depot sessions and retain competency and attendance evidence by 15 November."),
    "ISO.C7.3": _control("partially_compliant", "medium", "Security responsibilities are communicated in induction and policy material, while the annual refresher is incomplete.", ("policy", "hr_records"), ("training_records", "policy_acknowledgements"), "training_records", "Completion was 81 percent at 30 September; the remaining staff were assigned catch-up sessions for October and November.", "The annual refresh did not reach all staff before the stated deadline.", "Track catch-up completion by group and require manager follow-up for overdue personnel."),
    "ISO.C7.4": _control("partially_compliant", "medium", "Internal security communications use tracked email and portal channels, but six policy acknowledgements and two access-owner responses remained open.", ("policy", "roles"), ("policy_acknowledgements", "access_sep_followup"), "access_sep_followup", "The September summary is signed for nine systems. TMS and the driver app are recorded as omitted; eight removal actions remain open, including four terminated users still enabled.", "The access escalation reached management but did not obtain all service-owner decisions by the cutoff.", "Keep escalation recipients and acknowledgement overdue items visible in the October management follow-up."),
    "ISO.C7.5": _control("compliant", "low", "Current controlled documents have named owners, versions, approval dates and review intervals.", ("policy", "risk_methodology", "sdlc_standard"), ("policy_acknowledgements", "management_review"), "policy", "The Information Security Lead reviews this policy every twelve months and after a material change; the next scheduled review is 1 July 2027.", "", "Keep prior versions and approval records in the controlled repository and remove superseded copies from staff portals."),
    "ISO.C8.1": _control("partially_compliant", "high", "Operational procedures govern access, suppliers, development and backup, but operating coverage was incomplete in the quarter.", ("policy", "change_management", "backup_log"), ("access_q2", "supplier_register", "backup_log"), "access_q2", "The completed review covered 9 of 11 production systems.", "July and August reviews were not completed, supplier assurance was incomplete and no backup restore test was recorded.", "Track the three open operating processes against the assigned October dates and verify evidence before closing."),
    "ISO.C8.2": _control("compliant", "low", "The risk method and register show a scheduled assessment and a quarterly review using current service context.", ("risk_methodology",), ("risk_register", "management_review"), "risk_register", "The quarterly register review was held on 24 September 2026 and the action owners confirmed dates on 25 September.", "", "Preserve the risk review record after each quarterly assessment and trigger review after a material incident or supplier change."),
    "ISO.C8.3": _control("partially_compliant", "medium", "Treatments are assigned and monitored, but access, supplier and restore risks remain open beyond the assessment cutoff.", ("risk_methodology", "soa"), ("risk_register", "management_review"), "risk_register", "Four treatments remain open: incomplete monthly access coverage, supplier assurance backlog, an incident exercise and a database restore test.", "Open treatment actions were not completed by quarter end.", "Complete the planned treatments, then retain owner evidence and residual risk approval in the register."),
    "ISO.C9.1": _control("compliant", "medium", "Objectives have owners, metrics, targets and a dated analysis, with period-to-date measures reviewed at the September meeting and final quarter measures retained at cutoff.", ("objectives",), ("objectives_email", "management_review"), "objectives", "The Information Security Lead consolidated July through September measures on 30 September 2026.", "", "Retain trend comparisons and record the management response where results fall below target."),
    "ISO.C9.2": _control("compliant", "low", "An independent internal audit sampled operating evidence and reported findings to an oversight role outside the control owners.", ("roles",), ("internal_audit", "management_review"), "internal_audit", "The Information Security Lead did not select samples, perform tests or approve the audit conclusions.", "", "Track each audit action to evidence-based closure and preserve the next audit programme schedule."),
    "ISO.C9.3": _control("compliant", "low", "Management review considered the required performance inputs and produced decisions, owners and due dates.", ("risk_methodology", "objectives"), ("management_review", "board_minutes"), "management_review", "The committee reviewed the July-September objective measures, internal audit observations, supplier changes, risks and open corrective actions.", "", "Carry forward open decisions without changing their status until owners provide closure evidence."),
    "ISO.C10.1": _control("partially_compliant", "medium", "Management has assigned improvements, while recurring access and assurance gaps show that action effectiveness is not yet established.", ("policy", "risk_methodology"), ("management_review", "internal_audit"), "management_review", "The IT Operations Manager will run a database restore test by 31 October and retain the job, sample and recovery result.", "The corrective actions are planned but not yet completed or retested.", "Verify the completed work and compare the next quarter's measures with the current baseline."),
    "ISO.C10.2": _control("partially_compliant", "high", "Nonconformities are recorded with owners and dates, but the relevant corrective actions remain open at cutoff.", ("risk_methodology", "internal_audit"), ("risk_register", "management_review"), "internal_audit", "The audit assigned one consolidated access finding and requested owner evidence by 16 October 2026.", "Access, supplier and backup findings were not closed or effectiveness-tested by 30 September.", "Record correction, cause, action, verification and residual risk before closing each finding."),

    # Annex A.5 Organizational controls.
    "ISO.A5.1": _control("partially_compliant", "low", "The policy is approved, versioned and distributed to relevant personnel, but six current acknowledgements were outstanding at cutoff.", ("policy",), ("policy_acknowledgements", "approval_scan"), "policy_acknowledgements", "The 28 September export shows 274 acknowledgements and six overdue reminders; one reminder was assigned to a manager for follow-up.", "Acknowledgement is not complete for six recipients.", "Obtain the six acknowledgements and retain the updated portal export."),
    "ISO.A5.2": _control("compliant", "low", "Security duties are assigned to current roles and reviewed by management.", ("roles",), ("board_minutes", "management_review"), "roles", "The Risk Coordinator records risk owners, treatment dates and committee decisions.", "", "Update the role register when a role holder or delegate changes."),
    "ISO.A5.3": _control("compliant", "medium", "Approval, implementation and independent review duties are separated with documented compensating checks for small teams.", ("roles",), ("change_management", "change_ticket_shot"), "roles", "The integration developer cannot approve their own production deployment; the platform release manager checks the ticket and deployment log.", "", "Continue sampling requester, approver and deployer identities on production changes."),
    "ISO.A5.4": _control("compliant", "low", "Management requires personnel to follow security procedures and uses tracked briefings and policy acknowledgements.", ("policy", "roles"), ("policy_acknowledgements", "management_review"), "policy", "Managers must review security exceptions for their teams and close assigned actions by the date recorded in the risk register.", "", "Close overdue policy acknowledgements and retain manager reminders."),
    "ISO.A5.5": _control("partially_compliant", "medium", "Authority and emergency contacts are identified, but only the provider number has a current verification record.", ("incident_plan",), ("incident_plan", "management_review"), "incident_plan", "The Information Security Lead verified the hosting provider number on 10 February 2026; the other contact entries were copied forward from the prior revision.", "The authority and emergency entries were not all reconfirmed within the current review period.", "Verify each contact and record the date, source and responsible role before the October tabletop."),
    "ISO.A5.6": _control("partially_compliant", "low", "Threat sources are listed and advisories are circulated, but no specialist group membership or active participation is recorded.", ("threat_digest",), ("threat_digest",), "threat_digest", "No membership or active subscription to a logistics-sector security forum was recorded in the quarter.", "No maintained record shows participation in a specialist security forum.", "Decide whether a suitable forum is needed and record the membership or documented decision."),
    "ISO.A5.7": _control("compliant", "low", "Security advisories are collected, assessed for service relevance and assigned to owners.", ("threat_digest", "vulnerability_report"), ("threat_digest", "vulnerability_report"), "threat_digest", "The analyst circulated three relevant advisories to IT Operations and Engineering on 11 July, 6 August and 12 September.", "", "Continue recording relevance decisions and closure evidence for each advisory."),
    "ISO.A5.8": _control("compliant", "low", "Security impact, ownership and tests are built into project and change approval for new or changed services.", ("change_management", "sdlc_standard"), ("change_ticket_shot", "app_test_report"), "app_test_report", "The design review traced the driver identifier and route location fields to the processing register and limited the service response to the assigned route.", "", "Retain the security review and acceptance record for each material release."),
    "ISO.A5.9": _control("compliant", "low", "An owner-maintained inventory identifies production services, information classes, suppliers and dependencies.", ("asset_inventory",), ("asset_inventory", "management_review"), "asset_inventory", "Service owners confirmed the production inventory on 23 September 2026; the next owner attestation is due in December.", "", "Resolve inventory changes through owner attestation each quarter."),
    "ISO.A5.10": _control("compliant", "low", "Acceptable use and handling rules are communicated for company information and devices.", ("policy", "remote_work"), ("policy_acknowledgements", "training_records"), "policy", "Staff may use approved services for company work. Personal email and unapproved file sharing are not approved transfer routes.", "", "Complete reminders for staff who have not acknowledged the current policy."),
    "ISO.A5.11": _control("partially_compliant", "medium", "The leaver procedure calls for asset return and tracking, but current access exceptions show incomplete closure across the service estate.", ("hr_records",), ("hr_records", "access_export"), "hr_records", "Exit checklists include return of badge, device, keys and issued storage media; the manager records any missing property.", "Four terminated identities remained enabled and asset-return evidence was not attached to all sampled leaver records.", "Reconcile leaver checklists to the identity and asset inventories and escalate missing returns."),
    "ISO.A5.12": _control("compliant", "low", "The asset inventory and classification guide identify sensitivity according to the data and operating impact.", ("classification_guide", "asset_inventory"), ("asset_inventory", "ropa"), "classification_guide", "Restricted information includes driver identity, live location, payroll bank details, authentication material and investigation records.", "", "Continue checking classifications when processing purposes or data fields change."),
    "ISO.A5.13": _control("partially_compliant", "low", "Labels and repository classes are defined, but one stale route workbook required correction during the quarter sample.", ("classification_guide",), ("classification_guide", "controls_drill"), "classification_guide", "The Asset Coordinator sampled eight active repositories on 20 September; seven carried the expected label and one old route workbook was corrected on 21 September.", "One sampled route workbook lacked the expected label until the review found it.", "Repeat the label sample next quarter and confirm old exports are retired."),
    "ISO.A5.14": _control("compliant", "medium", "Approved transfer routes and owner checks apply to customer, driver and supplier information.", ("policy", "ropa", "supplier_contracts"), ("supplier_contracts", "media_register"), "policy", "Restricted information must not be copied into test accounts without masking.", "", "Retain owner approval for any new supplier transfer path or export."),
    "ISO.A5.15": _control("partially_compliant", "high", "Access rules require business approval and monthly review, but only one quarter cycle was closed and two production systems were omitted.", ("policy", "roles"), ("access_q2", "access_export"), "access_q2", "The completed review covered 9 of 11 production systems.", "July and August cycles were incomplete; the September cycle omitted the TMS and driver app.", "Complete the October cycle for all production services and track reviewer decisions to closure."),
    "ISO.A5.16": _control("partially_compliant", "high", "Identity lifecycle steps are defined, but four terminated accounts were still enabled at quarter end.", ("policy", "hr_records"), ("access_export", "access_q2"), "access_export", "Four affected accounts belonged to people recorded as terminated.", "Approved leaver removals were not confirmed disabled by the quarter cutoff.", "Disable the four accounts, reconcile all open removal tickets and verify the identity source against HR."),
    "ISO.A5.17": _control("compliant", "medium", "Authentication material is managed through named identities, multifactor requirements and restricted key access.", ("policy", "crypto_key_log"), ("logging_review", "crypto_key_log"), "policy", "Multi-factor authentication is required for remote access and administrator accounts.", "", "Continue quarterly sampling of administrator factors and service account secrets."),
    "ISO.A5.18": _control("partially_compliant", "high", "Access rights are provisioned and reviewed by policy, but the quarter contains two incomplete cycles, two omitted systems and open removals.", ("policy", "roles"), ("access_q2", "access_export", "access_sep_followup"), "access_q2", "The completed review covered 9 of 11 production systems.", "Eight approved removal actions remained open at 30 September, including four enabled terminated users; July and August lack signed reviews.", "Finish all removal tickets and obtain signed decisions for TMS and the driver app in every monthly cycle."),
    "ISO.A5.19": _control("non_compliant", "high", "Supplier use is in scope, but no repeatable risk-based review calendar was defined or implemented for the six critical services.", ("supplier_register", "supplier_contracts"), ("supplier_register", "management_review"), "supplier_register", "The Supplier Manager did not maintain a common review calendar; assurance requests were raised when a contract owner asked or a renewal approached.", "The absence of a recurring risk-based process left two critical providers without current assurance and the remaining reviews dependent on ad hoc requests.", "Establish a risk-based supplier review calendar, assign owners and track current assurance for each critical service."),
    "ISO.A5.20": _control("partially_compliant", "high", "Security clauses are present in sampled agreements, but one supplier schedule and current assurance evidence are incomplete.", ("supplier_contracts",), ("supplier_register", "management_review"), "supplier_contracts", "The Route Insights contract names the service and data return terms but has no attached current assurance package in the supplier file.", "The agreement does not establish current evidence that the supplier meets the stated security requirements.", "Refresh the supplier schedule and record review of its security obligations before renewal."),
    "ISO.A5.21": _control("partially_compliant", "high", "Critical ICT dependencies are inventoried, but two provider assurance files and a consolidated supply-chain change review remain open.", ("supplier_register", "supplier_contracts"), ("cloud_review", "management_review"), "cloud_review", "The supplier register lists all six critical hosted services; two assurance updates were not complete at quarter end.", "Subprocessor and service changes were not consolidated into a completed quarter supply-chain review.", "Obtain outstanding assurance and verify provider and subprocessor changes against the service inventory."),
    "ISO.A5.22": _control("partially_compliant", "medium", "Provider services have owners and sampled checks, but the annual monitoring process did not cover every critical service this quarter.", ("supplier_register", "cloud_review"), ("cloud_review", "supplier_contracts"), "cloud_review", "The Cloud Identity owner exported administrator activity on 12 September and confirmed no unapproved admin grant in the sample.", "Two critical services await assurance refresh and there is no complete recurring service review for all six.", "Schedule reviews for each critical supplier and record performance, incidents, changes and open concerns."),
    "ISO.A5.23": _control("partially_compliant", "high", "Cloud service onboarding, ownership and exit steps are documented, but assurance review is incomplete for two critical hosted providers.", ("cloud_review", "supplier_register"), ("cloud_review", "supplier_contracts"), "cloud_review", "The cloud register identifies the service owner, information class, account administrator, renewal date and documented export path for six hosted services.", "Current provider assurance and change review evidence is missing for two critical services.", "Complete the assurance refresh and verify exit and data deletion terms for each cloud service."),
    "ISO.A5.24": _control("partially_compliant", "high", "The response plan assigns roles and steps, but no tabletop or incident simulation was performed in the assessment period.", ("incident_plan", "roles"), ("incident_log", "management_review"), "incident_plan", "The plan exists but has not yet been tested.", "No exercise showed whether owners can use the plan and call tree under incident conditions.", "Run the scheduled tabletop, record decisions and close assigned plan updates."),
    "ISO.A5.25": _control("partially_compliant", "medium", "Triage roles and event records exist, but the unexercised plan has not demonstrated consistent event classification and escalation.", ("incident_plan",), ("incident_log", "management_review"), "incident_log", "No incident-response exercise or simulated escalation was recorded during the quarter.", "Routine service events were logged, but no exercise tested event decision thresholds.", "Use the October tabletop to test classification, escalation and decision records."),
    "ISO.A5.26": _control("partially_compliant", "high", "Response tasks and containment authority are documented, while no response exercise or confirmed incident tested execution.", ("incident_plan", "roles"), ("incident_log",), "incident_plan", "Contain access or network paths under incident lead direction; retain relevant logs and obtain a second person to witness volatile evidence collection.", "Response execution has not been demonstrated in an incident or exercise during the period.", "Exercise containment and recovery steps with technical and business responders and retain the event log."),
    "ISO.A5.27": _control("partially_compliant", "medium", "The plan calls for post-incident review, but no incident or exercise produced a completed lessons record this quarter.", ("incident_plan",), ("incident_log", "management_review"), "incident_log", "The quarter had no event classified as a confirmed information security incident; two service desk events were reviewed and closed as routine operational errors.", "No lessons-learned record was available because the response process has not been exercised.", "Record lessons and action owners after the October tabletop, even if the scenario is simulated."),
    "ISO.A5.28": _control("partially_compliant", "medium", "Evidence preservation steps and witness roles are defined, but no collection exercise was performed.", ("incident_plan",), ("incident_log", "internal_audit"), "incident_plan", "The incident lead sets severity, assigns technical investigation and records the basis for escalation or closure.", "No current-period record demonstrates collection, integrity or custody of incident evidence.", "Include a mock evidence capture and custody log in the incident tabletop."),
    "ISO.A5.29": _control("compliant", "medium", "Continuity procedures include security responsibilities and a successful controlled failover exercise.", ("dr_report", "isms_scope"), ("dr_report", "management_review"), "dr_report", "The exercise used the secondary hosted region and a controlled dispatch queue; no live driver route was interrupted.", "", "Keep the security checks and access restrictions in the annual continuity exercise."),
    "ISO.A5.30": _control("compliant", "low", "The dispatch recovery capability was exercised within its target and reviewed by the responsible operator.", ("dr_report", "asset_inventory"), ("dr_report", "change_management"), "dr_report", "Failover completed in 3h 10m against a 4h RTO.", "", "Retest after material platform changes and keep database restore testing as a separate action."),
    "ISO.A5.31": _control("compliant", "medium", "A current owner-managed register identifies applicable legal, contract and privacy requirements and review dates.", ("legal_ip_register", "ropa"), ("legal_ip_register", "management_review"), "legal_ip_register", "The Legal and Commercial Lead reviewed the register with service owners on 24 September 2026.", "", "Review the register when a contract, processing purpose or applicable requirement changes."),
    "ISO.A5.32": _control("compliant", "low", "Software rights and third-party licences are tracked with repository ownership and approval records.", ("legal_ip_register", "sdlc_standard"), ("legal_ip_register", "app_test_report"), "legal_ip_register", "The September code sample had source attribution and approved licences for 18 of 18 sampled packages.", "", "Keep licence checks in the release checklist and investigate new dependencies before approval."),
    "ISO.A5.33": _control("partially_compliant", "medium", "A retention schedule and access owners are defined, but restoration and deletion evidence is not complete for every record type.", ("records_protection", "ropa"), ("records_protection", "media_register"), "records_protection", "The Company Secretary sampled six record series on 19 September and confirmed the owner and retention trigger were recorded for each.", "The sample did not test restoration and not all service deletion receipts were retained in the record index.", "Complete the restore sample and reconcile deletion confirmations to each record-series owner."),
    "ISO.A5.34": _control("partially_compliant", "high", "Personal information purposes and retention are recorded, but the driver location screen lacks a withdrawal route and receipt evidence.", ("privacy_notice", "ropa", "policy"), ("consent_screen", "grievance_register"), "consent_screen", "No withdraw option is shown on this screen.", "The sampled mobile permission flow does not show withdrawal and the company did not supply a consent receipt export.", "Add a withdrawal route and retain a versioned notice and consent receipt for the production build."),
    "ISO.A5.35": _control("compliant", "low", "An independent internal audit was completed by a reviewer outside the information security control roles.", ("roles", "internal_audit"), ("internal_audit", "management_review"), "internal_audit", "The Internal Audit Manager reports administratively to Finance and functionally to the Audit Committee Chair for this engagement.", "", "Maintain auditor independence and the approved annual audit schedule."),
    "ISO.A5.36": _control("partially_compliant", "medium", "Policy and compliance checks are defined and independently sampled, but open access and supplier exceptions remain unresolved.", ("policy", "internal_audit"), ("internal_audit", "management_review"), "internal_audit", "The reviewer found that July and August access review cycles had no signed decision records and September covered only nine of eleven services.", "Known deviations were escalated but not closed by quarter end.", "Track each policy exception to correction or a recorded risk decision."),
    "ISO.A5.37": _control("compliant", "low", "Current operating procedures assign roles, steps, records and approval points for common security tasks.", ("policy", "change_management", "incident_plan"), ("controls_drill", "change_ticket_shot"), "change_management", "A production change requires a ticket with business purpose, affected service, test evidence, security impact, rollback steps and named approver.", "", "Review operating procedures on the annual cycle and after service ownership changes."),

    # Annex A.6 People controls.
    "ISO.A6.1": _control("compliant", "medium", "Employees with access to scoped information are screened before access is granted and screening records have restricted ownership.", ("hr_records",), ("hr_records", "policy_acknowledgements"), "hr_records", "People Services verifies identity and role-relevant references before a staff member receives production access.", "", "Keep screening completion linked to the joiner ticket before provisioning."),
    "ISO.A6.2": _control("compliant", "low", "Employment terms define security responsibilities and confidentiality obligations for personnel.", ("hr_records", "policy"), ("policy_acknowledgements", "supplier_contracts"), "hr_records", "Employment terms describe acceptable use, confidentiality, incident reporting and return of company property.", "", "Retain signed terms and verify changes for role transfers and contractors."),
    "ISO.A6.3": _control("partially_compliant", "high", "An annual security programme exists, but the 2026 refresher lapsed and completion was 81 percent at cutoff.", ("training_records", "policy"), ("training_records", "management_review"), "training_records", "The expected annual refresh date passed on 31 August 2026; two depot groups did not complete the refresher before quarter end.", "Fifty-two personnel were overdue at cutoff and manager sign-off was missing for two depot groups.", "Run the scheduled depot sessions, close the overdue list and report verified completion."),
    "ISO.A6.4": _control("partially_compliant", "low", "A disciplinary process covers security breaches, but no current-period case sample demonstrated its operation.", ("hr_records",), ("internal_audit", "incident_log"), "hr_records", "The conduct procedure describes investigation, employee response and proportionate disciplinary review for repeated security breaches.", "No security disciplinary case or manager acknowledgement of the process was supplied for this period.", "Include process awareness in the next manager briefing and retain a case record if the process is invoked."),
    "ISO.A6.5": _control("partially_compliant", "high", "Post-termination duties and disable steps are documented, but four terminated users remained enabled at quarter end.", ("hr_records", "policy"), ("access_export", "access_q2"), "access_export", "Four affected accounts belonged to people recorded as terminated.", "Leaver responsibilities and access removal were not completed for four sampled identities by cutoff.", "Disable the accounts, confirm asset return and reconcile the leaver checklist with every service owner."),
    "ISO.A6.6": _control("compliant", "medium", "Confidentiality obligations are included in employee terms and supplier developer agreements.", ("hr_records", "supplier_contracts"), ("outsourced_dev_review", "legal_ip_register"), "supplier_contracts", "The Cloud Code Host schedule requires private repositories, named contractor accounts, multifactor authentication and return of source material at exit.", "", "Check signed confidentiality terms and expiry dates before each external engineer receives repository access."),
    "ISO.A6.7": _control("compliant", "medium", "Remote work rules require managed endpoints, multifactor access and protection of sensitive screens and records.", ("remote_work", "policy"), ("remote_work", "logging_review"), "remote_work", "Remote staff connect through the managed identity gateway with multifactor authentication and a company-managed endpoint.", "", "Review endpoint and remote-access exceptions each quarter."),
    "ISO.A6.8": _control("compliant", "low", "Personnel have defined event reporting routes and reported events are recorded with triage decisions.", ("incident_plan", "policy"), ("incident_log", "grievance_register"), "incident_log", "The quarter had no event classified as a confirmed information security incident; two service desk events were reviewed and closed as routine operational errors.", "", "Continue recording report source, triage owner and closure basis for every reported event."),

    # Annex A.7 Physical controls.
    "ISO.A7.1": _control("compliant", "low", "Staffed offices and depots use defined facility boundaries and badge-controlled entry.", ("physical_security",), ("physical_security", "controls_drill"), "physical_security", "The Pune operations office and two staffed depots use badge-controlled staff entry and a visitor sign-in register.", "", "Retain periodic checks of doors, fencing and access records at all scoped premises."),
    "ISO.A7.2": _control("compliant", "low", "Physical entry is managed through staff badges, visitor registration and host escort.", ("physical_security",), ("physical_security",), "physical_security", "Visitors receive a temporary badge, remain with a host in controlled work areas and return the badge before departure.", "", "Review visitor logs and close missing host or badge return fields promptly."),
    "ISO.A7.3": _control("compliant", "low", "Office, depot and network spaces use locked rooms and assigned facility owners.", ("physical_security", "asset_inventory"), ("physical_security",), "physical_security", "The network closet at the Pune office remains locked; access is limited to IT Operations and the facilities duty manager.", "", "Keep access lists current and recheck room controls after facilities changes."),
    "ISO.A7.4": _control("compliant", "medium", "Door alarms and camera coverage are checked during facility shifts and exceptions are sent to the facility owner.", ("physical_security",), ("physical_security", "controls_drill"), "physical_security", "Door alarms and camera coverage are checked at the start of each facilities shift; recorded exceptions are sent to the Facilities Manager.", "", "Sample shift checks and follow up any missed inspection."),
    "ISO.A7.5": _control("compliant", "low", "Environmental safeguards cover the staffed premises and have current inspection and maintenance records.", ("physical_security",), ("physical_security",), "physical_security", "Smoke detection, fire suppression and temperature alarms were inspected by the building service provider on 12 August.", "", "Retain provider inspection certificates and due dates in the facilities calendar."),
    "ISO.A7.6": _control("compliant", "low", "Access to secure rooms is limited to authorized support roles and maintenance visits are escorted.", ("physical_security",), ("physical_security",), "physical_security", "A facilities work order records the technician, maintenance window and escort for equipment repairs in secure rooms.", "", "Continue recording each visitor, escort and work order for secure-area access."),
    "ISO.A7.7": _control("compliant", "low", "Personnel receive clear-screen and clear-desk direction for office, depot and remote work.", ("remote_work", "policy"), ("remote_work", "policy_acknowledgements"), "remote_work", "The clear desk and clear screen reminder was included in the July staff bulletin and depot supervisor briefing.", "", "Check the practice during the next depot walk-through and manager briefing."),
    "ISO.A7.8": _control("compliant", "low", "Equipment is kept in locked, raised and protected locations away from loading and water hazards.", ("physical_security", "asset_inventory"), ("physical_security",), "physical_security", "Network equipment is kept in locked cabinets above floor level and away from the loading bay and water line.", "", "Inspect equipment placement after any office or depot move."),
    "ISO.A7.9": _control("compliant", "medium", "Off-premises devices are managed, encrypted and tied to named personnel and remote-work rules.", ("remote_work", "asset_inventory"), ("remote_work", "hr_records"), "remote_work", "Lost or stolen equipment is reported to the service desk immediately so the device can be isolated and its credentials reviewed.", "", "Reconcile assigned endpoint records to personnel changes and investigate late returns."),
    "ISO.A7.10": _control("compliant", "medium", "Media custody, handling, deletion and disposal are defined and recorded.", ("media_register", "records_protection"), ("media_register",), "media_register", "Four retired storage devices were collected on 12 August; the disposal provider issued serial-linked destruction receipts on 19 August.", "", "Keep receipts tied to the asset serial and confirm the destruction provider remains approved."),
    "ISO.A7.11": _control("compliant", "low", "Supporting utilities are inspected and maintenance evidence is retained for the office and depots.", ("physical_security",), ("physical_security",), "physical_security", "The depot generator was load-tested on 21 August; the office UPS battery warning was replaced on 22 August.", "", "Continue scheduled load and alarm tests and retain the contractor work orders."),
    "ISO.A7.12": _control("compliant", "low", "Facility inspections include cable condition, route protection and prompt correction of observed issues.", ("physical_security",), ("physical_security",), "physical_security", "A cable tray inspection on 17 September found one loose patch-cord label, corrected before the inspector left.", "", "Repeat cable tray checks after network moves and retain findings in the inspection record."),
    "ISO.A7.13": _control("compliant", "low", "Equipment maintenance is authorized, scheduled and performed with a recorded escort in secure rooms.", ("physical_security", "change_management"), ("physical_security",), "physical_security", "A facilities work order records the technician, maintenance window and escort for equipment repairs in secure rooms.", "", "Review technician identity and post-maintenance condition before closing each work order."),
    "ISO.A7.14": _control("compliant", "low", "Retired media and equipment are checked before reuse or sent for documented secure destruction.", ("media_register",), ("media_register", "asset_inventory"), "media_register", "Equipment scheduled for reuse is reset and checked by IT Operations; failed storage media is destroyed through the contracted secure disposal service.", "", "Retain reset evidence or provider destruction receipt for each retired item."),

    # Annex A.8 Technological controls.
    "ISO.A8.1": _control("compliant", "medium", "Managed endpoints are assigned to users and protected through encryption, updates and malware controls.", ("remote_work", "asset_inventory"), ("remote_work", "configuration_baseline"), "remote_work", "Company laptops use full-disk encryption, endpoint protection, centrally managed updates and screen lock after ten minutes.", "", "Reconcile enrolled devices to active personnel and investigate any late return."),
    "ISO.A8.2": _control("partially_compliant", "high", "Administrator membership is restricted, but two privileged accounts lacked an owner review decision.", ("policy", "configuration_baseline"), ("access_export", "logging_review"), "access_export", "Administrator accounts VH-0034 and VH-0178 have no reviewer decision because their manager response was outstanding.", "Two privileged identities remained without an affirmative reviewer decision at cutoff.", "Obtain owner decisions and perform a separate monthly sample of privileged groups."),
    "ISO.A8.3": _control("partially_compliant", "high", "Role groups and service owner approvals restrict information access, but the access review did not include every production service.", ("policy", "roles"), ("access_q2", "access_export"), "policy", "Access is granted for a recorded role and business need, approved by the line manager and service owner, and removed when that need ends.", "The TMS and driver app were omitted and open leaver actions weaken assurance that restrictions remain current.", "Complete owner review for every production service and verify open removals are disabled."),
    "ISO.A8.4": _control("compliant", "medium", "Private repositories use protected branches, named accounts and separated merge approval.", ("sdlc_standard", "supplier_contracts"), ("app_test_report", "outsourced_dev_review"), "sdlc_standard", "Repositories are private, protected branches require peer review and production secrets are stored outside source code.", "", "Review source membership and contractor expiry dates each month."),
    "ISO.A8.5": _control("compliant", "medium", "Authentication uses multifactor requirements and controlled administrator identities, with current samples of access activity.", ("policy", "remote_work"), ("cloud_review", "logging_review"), "cloud_review", "The Cloud Identity owner exported administrator activity on 12 September and confirmed no unapproved admin grant in the sample.", "", "Continue reviewing authentication exceptions and emergency recovery access."),
    "ISO.A8.6": _control("compliant", "low", "Service owners review resource utilization and forecast demand before capacity headroom becomes constrained.", ("capacity_report",), ("capacity_report", "objectives"), "capacity_report", "The quarter review found no production service above 78 percent sustained capacity and no dispatch queue older than the operating target.", "", "Review seasonal delivery volume and capacity trends before the next peak period."),
    "ISO.A8.7": _control("compliant", "low", "Production images and endpoints receive managed malware protection and alerts are reviewed.", ("configuration_baseline",), ("configuration_baseline", "logging_review"), "configuration_baseline", "The 19 September malware console export showed all 280 enrolled endpoints reporting current signatures.", "", "Investigate missed check-ins and retain endpoint protection coverage reports."),
    "ISO.A8.8": _control("compliant", "medium", "Vulnerability scans, severity targets and owner treatment are defined and monitored for production services.", ("vulnerability_report", "configuration_baseline"), ("vulnerability_report", "change_management"), "vulnerability_report", "The September scan found one high issue in a test image and three medium library updates; production services had no overdue critical issue at cutoff.", "", "Close the medium library item by its target date and retain the next scan result."),
    "ISO.A8.9": _control("compliant", "low", "Approved baselines, expiry-bound deviations and monthly configuration comparison are documented and sampled.", ("configuration_baseline",), ("configuration_baseline", "change_management"), "configuration_baseline", "Configuration changes are compared with the approved baseline during the monthly platform review.", "", "Recheck any baseline exception before its expiry and retain the closure result."),
    "ISO.A8.10": _control("compliant", "medium", "Record owners control deletion requests and retain confirmation for sampled service records and media.", ("ropa", "records_protection", "media_register"), ("media_register", "records_protection"), "media_register", "Two user deletion requests were completed on 6 and 22 September, with owner confirmation attached to the service desk ticket.", "", "Continue sampling deletion completion against retention triggers and legal holds."),
    "ISO.A8.11": _control("compliant", "medium", "Test information is masked before it is copied into the integration test environment.", ("sdlc_standard", "records_protection"), ("media_register", "app_test_report"), "media_register", "A test database copy was masked before use in the integration test environment on 14 September.", "", "Retain the masking check with each test data request and verify no direct production export is used."),
    "ISO.A8.12": _control("partially_compliant", "high", "Approved transfer restrictions are documented, but no current technical monitoring sample demonstrates prevention of unauthorized data exfiltration.", ("policy", "network_review"), ("logging_review", "network_review"), "policy", "Information owners set retention periods and authorize disposal. Restricted information must not be copied into test accounts without masking.", "The evidence shows handling rules and network controls but no tested data leakage prevention rule or alert sample.", "Define the Restricted-data monitoring boundary and test a safe detection case before reporting coverage."),
    "ISO.A8.13": _control("partially_compliant", "high", "Nightly backups ran, but there was no restore test in the quarter and failover did not restore a retained copy.", ("backup_log", "policy"), ("backup_log", "dr_report"), "backup_log", "No restore test was recorded between 1 July and 30 September 2026.", "Backup job success alone does not establish that data can be restored within the required recovery point and time.", "Perform the scheduled database restore, record sample integrity and recovery time, and retest quarterly."),
    "ISO.A8.14": _control("compliant", "low", "The hosted dispatch service has a secondary region and the August exercise met its recovery objective.", ("dr_report", "asset_inventory"), ("dr_report", "change_management"), "dr_report", "The recovered queue lagged by 4 minutes at first login and reached the recorded recovery point within the agreed 15 minute objective.", "", "Maintain the failover exercise and separately test backup restoration."),
    "ISO.A8.15": _control("compliant", "medium", "Security-relevant identity, service, administrator and network events are collected with defined retention.", ("logging_review",), ("logging_review", "incident_log"), "logging_review", "Identity, administrator, network gateway and dispatch application events are forwarded to the managed log workspace.", "", "Retain the sampled log availability and retention checks for each quarter."),
    "ISO.A8.16": _control("compliant", "medium", "A monitoring desk reviews priority alerts and routes significant cases to service owners.", ("logging_review", "incident_plan"), ("logging_review", "incident_log"), "logging_review", "The monitoring desk reviews priority alerts during staffed hours and pages the on-call engineer for a critical service alert.", "", "Exercise the on-call path during the planned incident tabletop."),
    "ISO.A8.17": _control("compliant", "low", "Production services use a common time source and drift is monitored through scheduled health reports.", ("logging_review",), ("logging_review", "change_management"), "logging_review", "Production services synchronize to the approved time source; the platform checks drift during its weekly health report.", "", "Investigate missed time-source checks and retain correction records."),
    "ISO.A8.18": _control("compliant", "medium", "Privileged system utilities are restricted to the platform administrator group and their use is logged.", ("configuration_baseline", "policy"), ("logging_review", "access_export"), "configuration_baseline", "Privileged command-line utilities are limited to the platform administrator group and activity is forwarded to the managed log workspace.", "", "Sample utility access and activity logs during the monthly administrator review."),
    "ISO.A8.19": _control("compliant", "medium", "Production software installation is restricted to an approved release group and change record.", ("change_management", "configuration_baseline"), ("change_ticket_shot", "deployment_shot"), "change_management", "Software installation on production systems is limited to the platform release group and approved automation account.", "", "Continue matching production build identifiers to approved change tickets."),
    "ISO.A8.20": _control("compliant", "medium", "Production and office networks use managed gateways, denied-by-default inbound paths and reviewed service routes.", ("network_review",), ("network_review", "change_management"), "network_review", "Network rules require an owner, business reason and review date; default inbound routes are denied at the managed gateway.", "", "Review exposed paths after service or provider changes."),
    "ISO.A8.21": _control("compliant", "medium", "Network services have named providers and owners, with service status and security expectations reviewed.", ("network_review", "supplier_contracts"), ("network_review", "supplier_register"), "network_review", "The managed network provider's August service review recorded no unresolved critical outage or unapproved route change.", "", "Retain service performance and change records at the quarterly supplier review."),
    "ISO.A8.22": _control("compliant", "medium", "Corporate, guest and production paths are segmented and were tested for separation in the period.", ("network_review",), ("network_review", "logging_review"), "network_review", "The Network Operations Lead compared the depot guest network and corporate route on 18 September and confirmed guest clients could not reach the dispatch segment.", "", "Repeat the segmentation check after network rule changes."),
    "ISO.A8.23": _control("compliant", "low", "The managed web gateway blocks disallowed categories and records tested exceptions.", ("network_review",), ("network_review", "logging_review"), "network_review", "The claims web gateway blocked three test categories on 19 September; the result was recorded in the change log.", "", "Review category and exception rules with the business owners each quarter."),
    "ISO.A8.24": _control("compliant", "medium", "Cryptographic protections, key ownership, rotation and administrator access are defined and sampled.", ("crypto_key_log", "policy"), ("crypto_key_log", "logging_review"), "crypto_key_log", "The 12 September review confirmed two production keys rotated within their scheduled period and one development key retired after a contractor change.", "", "Exercise key recovery and retain evidence of the next scheduled rotation."),
    "ISO.A8.25": _control("compliant", "medium", "Internal integration work uses a defined secure lifecycle with separate review, testing, approval and deployment roles.", ("sdlc_standard", "change_management"), ("app_test_report", "deployment_shot"), "sdlc_standard", "The standard applies to the four-person integration team and supplier engineers who build or change Veldhara software connections.", "", "Keep lifecycle records for both internal work and occasional vendor-assisted development."),
    "ISO.A8.26": _control("compliant", "medium", "Application security and privacy requirements are recorded before implementation and traced to service data needs.", ("sdlc_standard", "privacy_notice"), ("app_test_report", "change_ticket_shot"), "app_test_report", "The route integration ticket records authentication, data minimization, error handling and audit logging requirements before development began.", "", "Review requirements whenever the app or data use changes."),
    "ISO.A8.27": _control("compliant", "medium", "Architecture review addresses role boundaries, data fields, expired sessions and event integrity for the integration.", ("sdlc_standard", "app_test_report"), ("app_test_report", "change_ticket_shot"), "app_test_report", "The engineering review included an abuse case for an expired driver session and a replayed delivery event.", "", "Retain abuse-case review for new interfaces and material architecture changes."),
    "ISO.A8.28": _control("compliant", "medium", "The development standard sets coding safeguards and protected review before changes can enter production.", ("sdlc_standard",), ("app_test_report", "change_ticket_shot"), "sdlc_standard", "Engineers follow input validation, safe error handling, dependency review and logging rules for route and driver information.", "", "Keep peer review evidence and address secure coding findings before merge."),
    "ISO.A8.29": _control("compliant", "medium", "Material application changes receive automated, integration and security checks before release acceptance.", ("sdlc_standard",), ("app_test_report", "change_ticket_shot"), "app_test_report", "The 26 September test run passed 42 unit checks, 11 integration checks and six security cases before release approval.", "", "Preserve failing test and retest history with the release record."),
    "ISO.A8.30": _control("partially_compliant", "high", "Vendor development is contractually restricted and sampled, but broader supplier assurance and subcontractor screening evidence are incomplete.", ("outsourced_dev_review", "supplier_contracts"), ("outsourced_dev_review", "app_test_report"), "outsourced_dev_review", "The Supplier Manager did not complete a broader security performance review of development support during the quarter.", "No current evidence package was received for supplier secure development training or subcontractor screening.", "Complete a supplier development review and obtain current personnel and subcontractor assurance."),
    "ISO.A8.31": _control("compliant", "medium", "Development, test and production accounts are separated and production secrets and data are protected.", ("sdlc_standard", "change_management"), ("app_test_report", "deployment_shot"), "sdlc_standard", "Development, test and production accounts are separated; production data is masked before use in test.", "", "Review environment membership and secret separation during the quarterly access sample."),
    "ISO.A8.32": _control("compliant", "medium", "Production changes require documented risk, test, approval, rollback and post-deployment evidence.", ("change_management",), ("change_ticket_shot", "deployment_shot"), "change_ticket_shot", "Production approval: Release Manager | 26 Sep 2026 16:20", "", "Continue next-day independent review of emergency changes."),
    "ISO.A8.33": _control("compliant", "medium", "Test records use masked synthetic data with controlled access and an owner acceptance record.", ("sdlc_standard", "records_protection"), ("app_test_report", "media_register"), "app_test_report", "The test environment used masked driver identifiers and synthetic route records; no live payroll or location export was copied into the test service.", "", "Retain data provenance and masking checks with each test pack."),
    "ISO.A8.34": _control("compliant", "low", "Internal testing used read-only access and an independent audit process with no production data changes.", ("internal_audit", "roles"), ("internal_audit", "management_review"), "internal_audit", "The audit account was read-only and the team recorded no production data changes during testing.", "", "Keep audit-test access time-bound and revoke it when fieldwork closes."),
}


DOCUMENTS["soa"]["headers"] = ("Control", "Applicability", "Individual decision basis", "Implementation status", "Evidence record", "Owner")
DOCUMENTS["soa"]["rows"] = tuple(
    (control_id, record["applicability"], record["rationale"], record["answer"], DOCUMENTS[record["primary"]]["filename"], DOCUMENTS[record["primary"]]["owner"])
    for control_id, record in CONTROLS.items()
    if control_id.startswith("ISO.A")
)
DOCUMENTS["soa"]["date"] = "2026-10-05"
DOCUMENTS["soa"]["sections"].append(("Cutoff status compilation", ["The applicability decisions were approved on 24 September. Implementation status and the individual evidence references were reconciled on 5 October 2026. Open deficiencies remain applicable."]))
DOCUMENTS["ropa"]["date"] = "2026-09-30"
DOCUMENTS["dr_report"]["date"] = "2026-08-22"
DOCUMENTS["risk_register"]["date"] = "2026-09-25"
DOCUMENTS["objectives"]["date"] = "2026-09-30"
DOCUMENTS["prior_baseline"]["date"] = "2025-10-05"
DOCUMENTS["internal_audit"]["date"] = "2026-10-05"
DOCUMENTS["internal_audit"]["sections"].append(("Quarter-end follow-up addendum dated 5 October 2026", [
    "The original fieldwork ran from 8 to 15 September. The Results section above includes the subsequent September review and quarter-end reconciliation, not observations claimed to exist during fieldwork.",
    "On 5 October the independent auditor reconciled the signed 18 September access review and 30 September export. This confirmed one completed monthly cycle covering nine of eleven services, four terminated enabled accounts and eight overdue approved removals at quarter end.",
    "The Audit Committee Chair accepted this final compilation on 5 October. The open findings and 16 October evidence request remain unchanged; no remediation closure is asserted.",
]))
DOCUMENTS["management_review"]["date"] = "2026-10-05"
DOCUMENTS["management_review"]["sections"].append(("Cutoff compilation addendum dated 5 October 2026", [
    "The 24 September meeting reviewed July-September period-to-date measures and the records available that day. The original minutes and owner decisions were approved on 28 September.",
    "The Information Security Lead finalized quarter-end metrics on 30 September. The Company Secretary attached those metrics and the final audit follow-up on 5 October; these later attachments were not represented as available at the original meeting.",
    "The Managing Director accepted the cutoff compilation on 5 October. The original decisions, action owners and due dates remain those agreed at the 24 September meeting; the addendum records status and does not assert another meeting or closed actions.",
]))
for _key in ("policy", "incident_plan", "internal_audit", "management_review", "soa"):
    DOCUMENTS[_key]["modified_date"] = "2026-10-05"


def validate_scenario() -> None:
    """Check scope breadth, evidence references and exact citation integrity."""
    annex_ids = {control_id for control_id in CONTROLS if control_id.startswith("ISO.A")}
    clause_ids = {control_id for control_id in CONTROLS if control_id.startswith("ISO.C")}
    if len(annex_ids) != 93 or len(clause_ids) != 23 or len(CONTROLS) != 116:
        raise ValueError(f"Expected 93 Annex A and 23 clause records; got {len(annex_ids)} and {len(clause_ids)}")
    if len(_ACCESS_EXPORT_ROWS) != 220 or len({row[0] for row in _ACCESS_EXPORT_ROWS}) != 220:
        raise ValueError("The September access export must contain 220 distinct records")
    searchable = {
        key: "\n".join(
            [line for _, lines in document["sections"] for line in lines]
            + ["\t".join(str(cell) for cell in row) for row in document.get("rows", ())]
        )
        for key, document in DOCUMENTS.items()
    }
    for control_id, control in CONTROLS.items():
        refs = set(control["design"] + control["operating"] + [control["primary"]])
        if refs - DOCUMENTS.keys():
            raise ValueError(f"{control_id} references unknown documents: {sorted(refs - DOCUMENTS.keys())}")
        if control["quote"] not in searchable[control["primary"]]:
            raise ValueError(f"{control_id} citation is absent from {control['primary']}")
        if control["answer"] != CONTROL_OUTCOME_TO_ANSWER[control["outcome"]]:
            raise ValueError(f"{control_id} answer does not match its outcome")
        if control["outcome"] == "compliant" and (not control["design"] or not control["operating"]):
            raise ValueError(f"{control_id} is compliant without design and operating evidence")


validate_scenario()
