"""DPDPA test criteria: DRAFT v1 for Saqlain's sign-off (P6-2a).

NOT attached to any `Control` and never imported by prompts or analyzers.
P6-2b converts the *approved* review sheet (tasks/criteria-review/) into
pack code. Until then these criteria must not reach an LLM.

Sources (primary, retrieved 2026-09-25):
- Digital Personal Data Protection Act, 2023 (No. 22 of 2023), MeitY copy
  https://www.meity.gov.in/static/uploads/2024/06/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf
  (byte-identical to e-Gazette https://egazette.gov.in/WriteReadData/2023/248045.pdf)
- DPDP Rules, 2025, G.S.R. 846(E) of 13 Nov 2025
  https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf
- Commencement notification G.S.R. 843(E) of 13 Nov 2025
  https://www.meity.gov.in/static/uploads/2025/11/c56ceae6c383460ca69577428d36828b.pdf
- Corrigendum G.S.R. 892(E) of 10 Dec 2025 (typographical only)
  https://www.meity.gov.in/static/uploads/2025/12/3c7ebbae0e5456f493f486e6845df86b.pdf

House style (D4): own words, references only. `source_basis` says
"practice" where a criterion goes beyond the Act and Rules, and notes where
the repo's requirement definition (app/dpdpa/framework.py) cites a
different provision or scopes the duty differently from the law.
"""

from __future__ import annotations

from app.frameworks.schema import TestCriterion

# ── Commencement notes (verified against G.S.R. 843(E) and Rules r.1) ─────

_MAY27 = (
    "Not in force at 2026-09-25. Commences 18 months after the 13 Nov 2025 "
    "Gazette (Act: G.S.R. 843(E) cl.(c); Rules: r.1(4)), i.e. mid-May 2027."
)
_NOV26 = (
    "Not in force at 2026-09-25. Consent Manager registration (Act s.6(9), "
    "Rules r.4) commences one year after the 13 Nov 2025 Gazette, i.e. mid-Nov "
    "2026; the fiduciary's own consent duties (s.6(1)-(8)) commence mid-May 2027."
)
_SDF = (
    "Not in force at 2026-09-25. s.10 and r.13 commence mid-May 2027 and apply "
    "only once the Central Government notifies the entity (or its class) as an "
    "SDF under s.10(1). A reported Jan 2026 proposal to shorten this window was "
    "not found as a gazetted amendment on MeitY's DPDP Rules page (checked 2026-09-25)."
)
_PRACTICE = (
    "Practice, not a statutory duty. The related Act/Rules provisions commence "
    "mid-May 2027 (not in force at 2026-09-25)."
)
_S16 = (
    _MAY27 + " No country or territory restricted under s.16(1) was found on "
    "MeitY's pages at 2026-09-25."
)
_SECTORAL = (
    "Sectoral localisation laws preserved by s.16(2) apply on their own terms and "
    "may already be in force; DPDPA s.16 itself commences mid-May 2027."
)

D, O = "design", "operating"
HIGH, MED, LOW = "high", "medium", "low"

# criterion_id -> (drafter_confidence, in_force_note). Review-sheet metadata
# only; P6-2b decides whether any of it survives into pack code.
DPDPA_CRITERIA_REVIEW_META: dict[str, tuple[str, str]] = {}


def _criteria(req_id: str, *rows: tuple[str, str, str, str, str, str]) -> tuple[TestCriterion, ...]:
    """rows: (kind, statement, evidence_hint, source_basis, confidence, in_force_note)."""
    out = []
    for n, (kind, statement, evidence_hint, source_basis, confidence, note) in enumerate(rows, 1):
        cid = f"{req_id}.TC{n}"
        out.append(TestCriterion(cid, statement, kind, evidence_hint, source_basis))
        DPDPA_CRITERIA_REVIEW_META[cid] = (confidence, note)
    return tuple(out)


DPDPA_CRITERIA_DRAFT: dict[str, tuple[TestCriterion, ...]] = {
    # ── Chapter 2: Consent ────────────────────────────────────────────────
    "CH2.CONSENT.1": _criteria(
        "CH2.CONSENT.1",
        (D, "Every consent request requires a clear affirmative action by the data principal; consent is never inferred from silence, a pre-ticked box, inactivity or continued use of the service.",
         "consent_forms (screenshots of every consent capture flow)", "DPDPA s.6(1)", HIGH, _MAY27),
        (D, "Every consent request names the specified purpose(s) for which the personal data will be processed.",
         "consent_forms", "DPDPA s.6(1); DPDP Rules 2025 r.3(b)(ii)", HIGH, _MAY27),
        (D, "The data principal is offered the option to read the consent request in English or in a language listed in the Eighth Schedule to the Constitution.",
         "consent_forms (language selector screenshot)",
         "DPDPA s.6(3) [repo cites s.6(1)-(2); the language duty sits in s.6(3)]. How many Eighth Schedule languages must be offered is not settled by the text. 'Clear and plain language' is not tested: it is not binary",
         MED, _MAY27),
        (D, "No consent request contains a term by which the data principal waives a right under the Act or agrees to processing that would breach the Act or another law.",
         "consent_forms; privacy_policy (terms linked from consent flows)", "DPDPA s.6(2)", HIGH, _MAY27),
        (O, "Consent screens captured from the live web/app during the assessment period match the approved consent design (affirmative action, purpose stated, no pre-selected choices).",
         "consent_forms (dated live screenshots or screen recording)", "DPDPA s.6(1)", HIGH, _MAY27),
    ),
    "CH2.CONSENT.2": _criteria(
        "CH2.CONSENT.2",
        (D, "Where one collection point serves more than one purpose, the consent request lists each purpose as a separate item rather than a single combined purpose.",
         "consent_forms",
         "DPDPA s.6(1) ('specific'); DPDP Rules 2025 r.3(b)(ii) [repo cites s.6(3), which concerns language and contact details]. Per-purpose consent is a reading of 'specific', not express text",
         MED, _MAY27),
        (D, "The accompanying notice gives an itemised description of the personal data processed for each listed purpose.",
         "privacy_policy; consent_forms", "DPDP Rules 2025 r.3(b)(i)", HIGH, _MAY27),
        (O, "Sampled consent records store a consent status for each purpose separately, not one combined flag.",
         "consent log extract (sample of data principals)", "DPDPA s.6(1), s.6(10)", MED, _MAY27),
    ),
    "CH2.CONSENT.3": _criteria(
        "CH2.CONSENT.3",
        (D, "The notice or consent flow tells the data principal how to withdraw consent (link or described means).",
         "privacy_policy; consent_forms", "DPDPA s.5(1)(ii); DPDP Rules 2025 r.3(c)(i)", HIGH, _MAY27),
        (D, "Withdrawing consent takes no more steps, and uses no less accessible a channel, than giving it did (e.g. consent given in-app can be withdrawn in-app).",
         "consent_forms (side-by-side give/withdraw flows)",
         "DPDPA s.6(4) [repo cites s.6(6)-(7); the withdrawal right sits in s.6(4), s.6(7) concerns Consent Managers]; DPDP Rules 2025 r.3(c)(i)",
         HIGH, _MAY27),
        (D, "A documented procedure makes the organisation stop the processing that relied on a withdrawn consent within a defined period, unless processing without consent is required or authorised by law.",
         "consent_forms; retention_policy (withdrawal procedure)", "DPDPA s.6(6)", HIGH, _MAY27),
        (D, "The withdrawal procedure requires the organisation to make its Data Processors stop processing that data principal's personal data.",
         "vendor_agreements; withdrawal procedure", "DPDPA s.6(6)", HIGH, _MAY27),
        (O, "For a sample of withdrawals in the period, records show processing stopped (including at processors) within the defined period.",
         "withdrawal log sample; processor instruction records", "DPDPA s.6(6) ('within a reasonable time')", MED, _MAY27),
    ),
    "CH2.CONSENT.4": _criteria(
        "CH2.CONSENT.4",
        (D, "Every Consent Manager through which the organisation receives consents appears on the Data Protection Board's published list of registered Consent Managers.",
         "Consent Manager agreement; extract of the Board's published register",
         "DPDPA s.6(9); DPDP Rules 2025 r.4(2)(a). Registration is the Consent Manager's obligation; the fiduciary-side test is using only registered ones",
         HIGH, _NOV26),
        (D, "The organisation's systems accept consent given, reviewed or withdrawn through the Consent Manager and act on it the same way as consent given directly.",
         "consent_forms; Consent Manager integration documentation",
         "DPDPA s.6(7). Whether a fiduciary must support Consent Managers at all, or only honour those it onboards, is not settled by the text",
         LOW, _MAY27),
        (O, "A reconciliation of Consent Manager records against internal consent status for a sample of data principals shows withdrawals made via the Consent Manager were applied.",
         "Consent Manager consent/withdrawal records; internal consent log extract", "DPDPA s.6(4), s.6(6), s.6(7)", MED, _MAY27),
    ),
    "CH2.CONSENT.5": _criteria(
        "CH2.CONSENT.5",
        (D, "A documented process obtains a parent's verifiable consent before any personal data of a child (under 18) is processed, except processing covered by a Fourth Schedule exemption the organisation has recorded.",
         "parental_consent", "DPDPA s.9(1), s.2(f); DPDP Rules 2025 r.10(1), r.12", HIGH, _MAY27),
        (D, "The process checks that the person consenting as parent is an identifiable adult, using identity and age details already reliably held or details/virtual token from an authorised entity (e.g. a Digital Locker provider).",
         "parental_consent; age_verification", "DPDP Rules 2025 r.10(1)(a)-(b)", HIGH, _MAY27),
        (D, "Where a lawful guardian consents for a person with disability, the process checks the guardian was appointed by a court, a designated authority or a local level committee.",
         "parental_consent (guardian verification procedure)", "DPDPA s.9(1); DPDP Rules 2025 r.11(1)", HIGH, _MAY27),
        (O, "For a sample of child accounts, records show the parent's consent and the verification method used, dated before the child's data was first processed.",
         "parental_consent (consent and verification records sample)", "DPDPA s.9(1); DPDP Rules 2025 r.10(1)", HIGH, _MAY27),
    ),
    # ── Chapter 2: Notice ─────────────────────────────────────────────────
    "CH2.NOTICE.1": _criteria(
        "CH2.NOTICE.1",
        (D, "A notice is presented before or together with every consent request, not only linked from a site footer.",
         "privacy_policy; consent_forms",
         "DPDPA s.5(1) [repo says 'at or before collection'; the Act ties the notice to consent requests, not to data collected under a s.7 legitimate use]",
         HIGH, _MAY27),
        (D, "The notice itemises the personal data collected and states the specified purpose(s) and the goods, services or uses each purpose enables.",
         "privacy_policy", "DPDPA s.5(1)(i); DPDP Rules 2025 r.3(b)", HIGH, _MAY27),
        (D, "The notice gives a link (or describes another means) through which the data principal can withdraw consent and exercise her rights.",
         "privacy_policy",
         "DPDPA s.5(1)(ii); DPDP Rules 2025 r.3(c)(i)-(ii) [extends the repo description, which names only data and purpose, to the statutory minimum content]",
         MED, _MAY27),
        (D, "The notice describes how the data principal can complain to the Data Protection Board of India.",
         "privacy_policy",
         "DPDPA s.5(1)(iii); DPDP Rules 2025 r.3(c)(iii) [extends the repo description to the statutory minimum content]",
         MED, _MAY27),
        (D, "The notice can be read in English or, at the data principal's option, in a language listed in the Eighth Schedule to the Constitution.",
         "privacy_policy (language options)", "DPDPA s.5(3). Number of languages required is not settled by the text", MED, _MAY27),
    ),
    "CH2.NOTICE.2": _criteria(
        "CH2.NOTICE.2",
        (D, "The organisation has identified the data principals whose personal data it processes on consent given before the Act's notice and consent provisions commenced.",
         "data_flow_diagram (legacy consent population)",
         "DPDPA s.5(2), s.1(2). 'Commencement' is read per provision (s.1(2)), i.e. consents given before mid-May 2027",
         MED, _MAY27),
        (D, "A retrospective notice template states the personal data held, the purposes it has been processed for, how to withdraw consent and exercise rights, and how to complain to the Board.",
         "privacy_policy (retrospective notice template)", "DPDPA s.5(2)(a)(i)-(iii)", HIGH, _MAY27),
        (O, "Dispatch records (email, in-app or other channel) show the retrospective notice was sent to the identified data principals, with dates.",
         "notice dispatch log", "DPDPA s.5(2)(a) ('as soon as reasonably practicable'); what counts as timely after commencement is untested",
         MED, _MAY27),
    ),
    "CH2.NOTICE.3": _criteria(
        "CH2.NOTICE.3",
        (D, "Each consent request gives contact details of the DPO (if an SDF) or of a person authorised to respond to data principals exercising their rights.",
         "consent_forms; privacy_policy",
         "DPDPA s.6(3) [repo cites s.5(1); the contact-details duty sits in s.6(3), s.8(9) and Rules r.9]. 'DPO' is defined only for SDFs (s.2(l)); 'grievance officer' is not an Act term",
         HIGH, _MAY27),
        (D, "The business contact information of the DPO, or of a person who can answer data principals' questions about processing, is prominently published on the website or app.",
         "privacy_policy (website/app screenshot)", "DPDPA s.8(9); DPDP Rules 2025 r.9", HIGH, _MAY27),
        (O, "A sample of responses to rights requests in the period includes that business contact information.",
         "grievance_mechanism (sample rights-request responses)", "DPDP Rules 2025 r.9", HIGH, _MAY27),
    ),
    # ── Chapter 2: Purpose limitation ─────────────────────────────────────
    "CH2.PURPOSE.1": _criteria(
        "CH2.PURPOSE.1",
        (D, "A processing record (ROPA or data inventory) links every processing activity to either a specified purpose in a consent notice or a named s.7 legitimate use.",
         "data_flow_diagram", "DPDPA s.4(1), s.2(za)", HIGH, _MAY27),
        (O, "Sampled processing activities (e.g. a marketing campaign, an analytics use, a data share) each map to a purpose in the notice under which consent was taken, or to a recorded s.7 basis.",
         "data_flow_diagram; consent_forms; campaign or data-share records", "DPDPA s.4(1)", HIGH, _MAY27),
    ),
    "CH2.PURPOSE.2": _criteria(
        "CH2.PURPOSE.2",
        (D, "A register lists each processing activity carried out without consent and names the specific s.7 clause relied on (e.g. s.7(a) voluntary provision, s.7(i) employment).",
         "data_flow_diagram; hr_privacy_notices", "DPDPA s.7", HIGH, _MAY27),
        (D, "For each s.7(a) use, the register records the purpose for which the data was voluntarily provided and how the data principal's indication that she does not consent stops the use.",
         "data_flow_diagram", "DPDPA s.7(a)", MED, _MAY27),
        (D, "No register entry relies on a ground that is not in s.7 (e.g. 'legitimate interests' or 'contractual necessity' in the GDPR sense).",
         "data_flow_diagram; privacy_policy", "DPDPA s.4(1)(b), s.7", HIGH, _MAY27),
    ),
    # ── Chapter 2: Minimisation & storage limitation ──────────────────────
    "CH2.MINIMIZE.1": _criteria(
        "CH2.MINIMIZE.1",
        (D, "Each personal data field collected on the basis of consent is mapped to the specified purpose that needs it.",
         "data_flow_diagram (field-to-purpose mapping); consent_forms",
         "DPDPA s.6(1) (consent limited to data necessary for the purpose) [repo cites s.4(1)]. The Act has no general minimisation duty for s.7 uses",
         MED, _MAY27),
        (O, "Sampled collection forms or API payloads contain no field that the mapping marks as unnecessary or omits.",
         "consent_forms; data_flow_diagram; form/API schema extracts", "DPDPA s.6(1)", MED, _MAY27),
    ),
    "CH2.MINIMIZE.2": _criteria(
        "CH2.MINIMIZE.2",
        (D, "The retention procedure requires erasure when consent is withdrawn or when it is reasonable to assume the specified purpose is no longer served, whichever comes first, unless a named law requires retention.",
         "retention_policy", "DPDPA s.8(7)(a)", HIGH, _MAY27),
        (D, "The procedure requires Data Processors to erase personal data the organisation made available to them when erasure is triggered.",
         "retention_policy; vendor_agreements", "DPDPA s.8(7)(b)", HIGH, _MAY27),
        (D, "If the organisation is an e-commerce entity or social media intermediary with at least 2 crore registered users in India, or an online gaming intermediary with at least 50 lakh, the procedure erases a user's data after three years without her approaching it or exercising rights (excluding account and virtual-token access).",
         "retention_policy", "DPDPA s.8(8); DPDP Rules 2025 r.8(1), Third Schedule", HIGH, _MAY27),
        (D, "For organisations in the Third Schedule classes, the procedure warns the data principal at least 48 hours before inactivity-based erasure.",
         "retention_policy; erasure warning template", "DPDP Rules 2025 r.8(2)", HIGH, _MAY27),
        (O, "Erasure job logs or erasure records for the period show personal data past its erasure trigger was actually erased.",
         "retention_policy; deletion job logs / erasure records sample", "DPDPA s.8(7)", HIGH, _MAY27),
    ),
    "CH2.MINIMIZE.3": _criteria(
        "CH2.MINIMIZE.3",
        (D, "A retention schedule sets a retention period or erasure trigger for each personal data category or processing purpose.",
         "retention_policy", "DPDPA s.8(7); the schedule document itself is practice", MED, _PRACTICE),
        (D, "Where the schedule keeps data after its purpose is served, it names the law that requires the retention.",
         "retention_policy", "DPDPA s.8(7)", HIGH, _MAY27),
        (D, "No schedule period erases personal data, associated traffic data or processing logs sooner than one year after the processing, unless another law requires otherwise.",
         "retention_policy", "DPDP Rules 2025 r.8(3), Seventh Schedule", HIGH, _MAY27),
        (O, "Retention or deletion settings on a sample of systems holding personal data match the schedule's periods.",
         "retention_policy; system configuration screenshots", "DPDPA s.8(7)", MED, _MAY27),
    ),
    # ── Chapter 2: Accuracy ───────────────────────────────────────────────
    "CH2.ACCURACY.1": _criteria(
        "CH2.ACCURACY.1",
        (D, "The organisation has identified the processing in which personal data is used to make a decision affecting the data principal or is disclosed to another Data Fiduciary.",
         "data_flow_diagram", "DPDPA s.8(3)", MED, _MAY27),
        (D, "For that processing, documented controls check the data's completeness, accuracy and consistency (e.g. validation at capture, source reconciliation) before it is used or disclosed.",
         "data quality procedure; data_flow_diagram",
         "DPDPA s.8(3) [repo says 'reasonable efforts'; the Act says the fiduciary 'shall ensure' completeness, accuracy and consistency, but only for decision-making or onward disclosure]",
         LOW, _MAY27),
        (O, "Records for the period show the checks ran (e.g. validation-failure reports or data-quality review logs) and flagged errors were corrected.",
         "data-quality reports; correction records", "DPDPA s.8(3)", MED, _MAY27),
    ),
    # ── Chapter 2: Security ───────────────────────────────────────────────
    "CH2.SECURITY.1": _criteria(
        "CH2.SECURITY.1",
        (D, "The security policy covers all personal data the organisation holds or controls, including data processed for it by Data Processors.",
         "security_policy", "DPDPA s.8(5) [repo cites s.8(4); the security-safeguards duty sits in s.8(5)]; DPDP Rules 2025 r.6(1)", HIGH, _MAY27),
        (D, "Access to personal data is logged, and the logs are monitored and reviewed so unauthorised access can be detected, investigated and remediated.",
         "logging_monitoring; security_policy", "DPDP Rules 2025 r.6(1)(c)", HIGH, _MAY27),
        (D, "Backups or equivalent measures let processing continue if personal data is destroyed or access to it is lost.",
         "backup; business continuity plan", "DPDP Rules 2025 r.6(1)(d)", HIGH, _MAY27),
        (D, "Access logs and the personal data needed to investigate unauthorised access are kept for at least one year, unless another law requires otherwise.",
         "logging_monitoring; retention_policy", "DPDP Rules 2025 r.6(1)(e)", HIGH, _MAY27),
        (O, "Log-review records for the period show that reviews of access to personal data actually took place and anomalies were followed up.",
         "logging_monitoring (review records, SIEM alert tickets)", "DPDP Rules 2025 r.6(1)(c)", HIGH, _MAY27),
    ),
    "CH2.SECURITY.2": _criteria(
        "CH2.SECURITY.2",
        (D, "Personal data is protected by at least one of encryption, obfuscation, masking or tokenisation.",
         "cryptography_policy; security_policy",
         "DPDP Rules 2025 r.6(1)(a) [repo requires encryption specifically; the Rules accept any of the four measures]", HIGH, _MAY27),
        (D, "Personal data sent over networks is encrypted in transit.",
         "cryptography_policy; security_policy", "practice (r.6(1)(a) is not transit-specific)", MED, _PRACTICE),
        (D, "Access to the computer resources holding personal data is restricted to authorised users through defined access controls.",
         "access_control_policy", "DPDP Rules 2025 r.6(1)(b)", HIGH, _MAY27),
        (D, "Access rights to personal data are granted on a least-privilege, need-to-know basis.",
         "access_control_policy", "practice (supports r.6(1)(b))", MED, _PRACTICE),
        (O, "An access review of systems holding personal data was completed in the last 12 months and removed access no longer needed.",
         "access_control_policy (access review records)", "practice (supports r.6(1)(b))", MED, _PRACTICE),
    ),
    "CH2.SECURITY.3": _criteria(
        "CH2.SECURITY.3",
        (D, "Every Data Processor that processes personal data for the organisation is engaged under a signed contract.",
         "vendor_agreements", "DPDPA s.8(2)", HIGH, _MAY27),
        (D, "Each Data Processor contract requires the processor to take reasonable security safeguards.",
         "vendor_agreements", "DPDP Rules 2025 r.6(1)(f)", HIGH, _MAY27),
        (D, "Each Data Processor contract requires the processor to stop processing and to erase personal data when the organisation instructs it to.",
         "vendor_agreements",
         "DPDPA s.6(6), s.8(7)(b) (fiduciary must cause processors to cease and erase; a contract term is the usual means, not an express requirement)",
         MED, _MAY27),
        (D, "Each Data Processor contract limits the processor to processing on the organisation's behalf and instructions.",
         "vendor_agreements", "DPDPA s.2(k), s.8(1); the explicit instructions term is practice", MED, _MAY27),
        (O, "Every processor in the organisation's processor/vendor register has a current signed contract on file (sample reconciliation).",
         "vendor_agreements; processor register", "DPDPA s.8(2)", HIGH, _MAY27),
    ),
    # ── Chapter 3: Rights ─────────────────────────────────────────────────
    "CH3.ACCESS.1": _criteria(
        "CH3.ACCESS.1",
        (D, "The website or app publishes how a data principal can request information about her personal data and which identifier she must give.",
         "privacy_policy", "DPDP Rules 2025 r.14(1)", HIGH, _MAY27),
        (D, "The access-request response template includes a summary of the personal data processed and of the processing activities.",
         "access request procedure; response template", "DPDPA s.11(1)(a)", HIGH, _MAY27),
        (D, "The response template names all other Data Fiduciaries and Data Processors the data was shared with and describes what was shared (subject to the s.11(2) law-enforcement carve-out).",
         "access request procedure; response template; vendor_agreements", "DPDPA s.11(1)(b), s.11(2)", HIGH, _MAY27),
        (O, "Sampled access requests in the period received a response containing the data summary and the recipient information.",
         "access request log; sample responses", "DPDPA s.11(1)", HIGH, _MAY27),
    ),
    "CH3.CORRECT.1": _criteria(
        "CH3.CORRECT.1",
        (D, "The website or app publishes a means for data principals to request correction, completion or updating of their personal data.",
         "privacy_policy; grievance_mechanism", "DPDPA s.12(1); DPDP Rules 2025 r.14(1)", HIGH, _MAY27),
        (D, "The procedure requires correcting inaccurate or misleading data, completing incomplete data and updating data when a data principal asks.",
         "rights request procedure", "DPDPA s.12(2)", HIGH, _MAY27),
        (O, "Sampled correction requests in the period show the change was made in the system of record.",
         "rights request log; before/after record extracts", "DPDPA s.12(2)", HIGH, _MAY27),
    ),
    "CH3.CORRECT.2": _criteria(
        "CH3.CORRECT.2",
        (D, "The website or app publishes a means for data principals to request erasure of their personal data.",
         "privacy_policy; grievance_mechanism", "DPDPA s.12(3) [repo cites s.12(2); erasure sits in s.12(3)]; DPDP Rules 2025 r.14(1)", HIGH, _MAY27),
        (D, "The procedure erases personal data on request unless retention is necessary for the specified purpose or required by law.",
         "rights request procedure; retention_policy",
         "DPDPA s.12(3) [repo scopes the right to data 'no longer necessary'; the Act lets the data principal request erasure at any time, with retention allowed only for the specified purpose or legal compliance]",
         LOW, _MAY27),
        (D, "An accepted erasure request also triggers erasure at the Data Processors holding that data.",
         "rights request procedure; vendor_agreements", "DPDPA s.8(1), s.8(7)(b), s.12(3)", MED, _MAY27),
        (O, "Each sampled erasure request in the period was closed either with evidence of erasure or with a recorded retention ground.",
         "rights request log; erasure records", "DPDPA s.12(3)", HIGH, _MAY27),
    ),
    "CH3.GRIEVANCE.1": _criteria(
        "CH3.GRIEVANCE.1",
        (D, "The website or app publishes how a data principal can submit a grievance about the organisation's handling of her personal data or rights.",
         "grievance_mechanism; privacy_policy", "DPDPA s.8(10), s.13(1)", HIGH, _MAY27),
        (D, "A named role or individual is responsible for handling data principal grievances (for an SDF, the DPO is the point of contact).",
         "grievance_mechanism; dpo_appointment",
         "DPDPA s.8(10), s.10(2)(a)(iv). A named handler is required by the Act only for SDFs; otherwise practice",
         MED, _MAY27),
        (O, "A grievance log for the period records each grievance's receipt date, subject and outcome.",
         "grievance_mechanism (grievance log)", "DPDPA s.8(10) ('effective mechanism'); the log itself is practice", MED, _MAY27),
    ),
    "CH3.GRIEVANCE.2": _criteria(
        "CH3.GRIEVANCE.2",
        (D, "The website or app publishes the period within which grievances will be answered, and that period is no more than 90 days.",
         "grievance_mechanism", "DPDPA s.13(2); DPDP Rules 2025 r.14(3)", HIGH, _MAY27),
        (O, "Every sampled grievance in the period was answered within the published period.",
         "grievance_mechanism (grievance log with receipt and response dates)", "DPDPA s.13(2); DPDP Rules 2025 r.14(3)", HIGH, _MAY27),
        (D, "Grievance responses tell the data principal she may complain to the Data Protection Board once the grievance process is exhausted.",
         "grievance_mechanism (response template)",
         "DPDPA s.5(1)(iii), s.13(3) require the notice to say how to complain to the Board; telling her at response stage is practice",
         MED, _MAY27),
        (D, "Measures exist to meet the published period (e.g. ticketing with due-date alerts and an escalation path).",
         "grievance_mechanism", "DPDP Rules 2025 r.14(3) ('appropriate technical and organisational measures')", MED, _MAY27),
    ),
    "CH3.NOMINATE.1": _criteria(
        "CH3.NOMINATE.1",
        (D, "The organisation publishes a means for a data principal to nominate one or more individuals to exercise her rights if she dies or becomes incapacitated.",
         "privacy_policy; nomination form", "DPDPA s.14(1); DPDP Rules 2025 r.14(4)", HIGH, _MAY27),
        (D, "A procedure defines how a nominee's request is verified (death or incapacity, and nominee identity) and acted on.",
         "rights request procedure", "DPDPA s.14(1)-(2); the verification steps are practice", MED, _MAY27),
        (O, "Nominations made are recorded against the data principal's account and can be retrieved.",
         "nomination records sample", "DPDP Rules 2025 r.14(4); record-keeping is practice", MED, _MAY27),
    ),
    # ── Chapter 4: Children ───────────────────────────────────────────────
    "CH4.CHILD.1": _criteria(
        "CH4.CHILD.1",
        (D, "A documented rule prohibits tracking and behavioural monitoring of children, apart from Fourth Schedule exemptions the organisation has recorded.",
         "privacy_policy; parental_consent; analytics policy",
         "DPDPA s.9(3) [repo cites s.9(2); the tracking/advertising ban is s.9(3)]; DPDP Rules 2025 r.12", HIGH, _MAY27),
        (D, "A documented rule prohibits advertising targeted at children.",
         "privacy_policy; advertising/ad-tech policy", "DPDPA s.9(3) [repo cites s.9(2)]", HIGH, _MAY27),
        (O, "For accounts identified as children, analytics and ad-tech configuration shows behavioural tracking and ad personalisation switched off.",
         "ad-tech/SDK configuration screenshots; age_verification", "DPDPA s.9(3)", HIGH, _MAY27),
        (D, "Where a Fourth Schedule exemption is relied on (e.g. an educational institution, or location tracking for a child's safety), the class or purpose and its condition are recorded.",
         "data_flow_diagram; exemption record", "DPDPA s.9(4); DPDP Rules 2025 r.12, Fourth Schedule", HIGH, _MAY27),
    ),
    "CH4.CHILD.2": _criteria(
        "CH4.CHILD.2",
        (D, "The organisation has assessed its processing of children's personal data for likely detrimental effects on their well-being and recorded the result.",
         "dpia_reports (children's data assessment)",
         "DPDPA s.9(2) [repo cites s.9(3); the well-being duty is s.9(2)]. The Act prohibits the processing but does not require an assessment; the assessment is how compliance is shown (practice)",
         MED, _MAY27),
        (D, "Processing the assessment finds likely to harm children's well-being is prohibited or blocked by a documented control.",
         "dpia_reports; product/content policy",
         "DPDPA s.9(2); DPDP Rules 2025 Fourth Schedule Pt B item 5. 'Detrimental effect on well-being' is not defined",
         LOW, _MAY27),
    ),
    "CH4.CHILD.3": _criteria(
        "CH4.CHILD.3",
        (D, "Onboarding determines whether the user is a child (under 18) before processing her data beyond what that check needs.",
         "age_verification",
         "DPDPA s.9(1), s.2(f); DPDP Rules 2025 Fourth Schedule Pt B item 6. Neither the Act nor the Rules mandates a specific age check of the child; r.10 verifies the parent. Needed in practice to know when s.9(1) applies",
         MED, _MAY27),
        (D, "Accounts identified as a child's are flagged so the parental-consent, tracking and targeted-advertising restrictions apply to them.",
         "age_verification; parental_consent", "DPDPA s.9(1), s.9(3)", HIGH, _MAY27),
        (O, "Sampled onboarding records show the age declaration or check result stored against the account.",
         "age_verification (onboarding records sample)", "DPDPA s.9(1); record-keeping is practice", MED, _MAY27),
    ),
    # ── Chapter 4: Significant Data Fiduciary ─────────────────────────────
    "CH4.SDF.1": _criteria(
        "CH4.SDF.1",
        (D, "A DPO has been formally appointed (appointment letter or board resolution).",
         "dpo_appointment", "DPDPA s.10(2)(a)", HIGH, _SDF),
        (D, "The DPO is an individual based in India.",
         "dpo_appointment", "DPDPA s.10(2)(a)(ii)", HIGH, _SDF),
        (D, "The DPO is responsible to the Board of Directors or equivalent governing body, and the reporting line is documented.",
         "dpo_appointment; organisation chart", "DPDPA s.10(2)(a)(iii)", HIGH, _SDF),
        (D, "The DPO is named as the point of contact for the grievance redressal mechanism.",
         "dpo_appointment; grievance_mechanism", "DPDPA s.10(2)(a)(iv)", HIGH, _SDF),
        (O, "Board or governing-body minutes from the last 12 months show the DPO reporting to it.",
         "board minutes; dpo_appointment", "practice (evidences s.10(2)(a)(iii))", MED, _SDF),
    ),
    "CH4.SDF.2": _criteria(
        "CH4.SDF.2",
        (D, "An independent data auditor is appointed under a documented engagement to evaluate compliance with the Act.",
         "audit_reports (auditor engagement letter)", "DPDPA s.10(2)(b)", HIGH, _SDF),
        (D, "The data auditor has no role in the processing or in designing the controls being audited.",
         "audit_reports (engagement letter, independence declaration)", "DPDPA s.10(2)(b). 'Independent' is not defined; this is a reading of it", MED, _SDF),
        (O, "The data auditor has issued an audit report within the last 12 months.",
         "audit_reports", "DPDPA s.10(2)(b); DPDP Rules 2025 r.13(1)", HIGH, _SDF),
    ),
    "CH4.SDF.3": _criteria(
        "CH4.SDF.3",
        (D, "The DPIA method covers a description of data principals' rights and of the processing purposes, and the assessment and management of risks to those rights.",
         "dpia_reports (methodology)", "DPDPA s.10(2)(c)(i)", HIGH, _SDF),
        (O, "A DPIA was completed within each 12-month period since the SDF notification.",
         "dpia_reports", "DPDP Rules 2025 r.13(1)", HIGH, _SDF),
        (O, "The person who carried out the DPIA furnished a report of its significant observations to the Data Protection Board.",
         "dpia_reports; Board submission acknowledgement", "DPDP Rules 2025 r.13(2)", HIGH, _SDF),
        (D, "Documented due diligence checks that algorithmic software used to process personal data is not likely to pose a risk to data principals' rights.",
         "dpia_reports; algorithm/model risk assessments",
         "DPDP Rules 2025 r.13(3) [not named in the repo requirement; placed here as the closest risk-assessment duty]",
         MED, _SDF),
    ),
    "CH4.SDF.4": _criteria(
        "CH4.SDF.4",
        (D, "An audit plan schedules an audit of compliance with the Act and Rules at least once every 12 months.",
         "audit_reports (audit plan)", "DPDPA s.10(2)(c)(ii) [repo cites s.10(2)(d), which does not exist]; DPDP Rules 2025 r.13(1)", HIGH, _SDF),
        (O, "An audit was completed within each 12-month period since the SDF notification.",
         "audit_reports", "DPDP Rules 2025 r.13(1)", HIGH, _SDF),
        (O, "The person who carried out the audit furnished a report of its significant observations to the Data Protection Board.",
         "audit_reports; Board submission acknowledgement", "DPDP Rules 2025 r.13(2)", HIGH, _SDF),
    ),
    # ── Consent management (detailed) ─────────────────────────────────────
    "CM.RECORDS.1": _criteria(
        "CM.RECORDS.1",
        (D, "Each consent record captures the purpose(s), the date and time, the capture channel and the version of the notice shown.",
         "consent log schema; consent_forms",
         "DPDPA s.6(10) puts the burden of proving notice and consent on the fiduciary; the record fields are practice", MED, _MAY27),
        (D, "Consent records also capture each withdrawal with its date and time.",
         "consent log schema", "DPDPA s.6(4), s.6(10); record fields are practice", MED, _MAY27),
        (O, "For a sample of data principals, the organisation can produce the notice version given and the matching consent record.",
         "consent log extract; notice version archive", "DPDPA s.6(10)", HIGH, _MAY27),
    ),
    "CM.RECORDS.2": _criteria(
        "CM.RECORDS.2",
        (D, "A documented trigger requires new notice and consent before personal data is processed for a purpose not covered by the existing consent.",
         "consent_forms; privacy_policy (change procedure)", "DPDPA s.4(1), s.5(1), s.6(1), s.2(za)", HIGH, _MAY27),
        (O, "Where a new purpose was introduced in the period, records show fresh consent was collected before the new processing started.",
         "consent log extract; product change records", "DPDPA s.4(1), s.6(1)", HIGH, _MAY27),
        (D, "Consent is re-confirmed at a defined interval even where purposes have not changed.",
         "consent_forms (refresh policy)",
         "practice [repo includes refresh 'after a reasonable period'; the Act sets no consent expiry. Inactivity erasure (r.8, Third Schedule) is the nearest statutory analogue]",
         LOW, _PRACTICE),
    ),
    "CM.GRANULAR.1": _criteria(
        "CM.GRANULAR.1",
        (D, "The consent interface provides a separate unticked control for each optional purpose.",
         "consent_forms",
         "DPDPA s.6(1) ('specific'); DPDP Rules 2025 r.3(b)(ii) [repo cites s.6(3), which concerns language and contact details]. Largely overlaps CH2.CONSENT.2",
         MED, _MAY27),
        (D, "Refusing or withdrawing one optional purpose leaves consent for the other purposes unchanged.",
         "consent_forms; consent log schema", "DPDPA s.6(1), s.6(4)", MED, _MAY27),
        (O, "Consent records contain data principals with mixed per-purpose states, showing partial consent works in practice.",
         "consent log extract", "DPDPA s.6(1)", MED, _MAY27),
    ),
    "CM.GRANULAR.2": _criteria(
        "CM.GRANULAR.2",
        (D, "Access to the service is not made conditional on consent to processing that the service does not need.",
         "consent_forms; terms of service", "DPDPA s.6(1) ('unconditional'; consent limited to data necessary for the purpose, see the s.6(1) illustration)", HIGH, _MAY27),
        (D, "Consent screens show the accept and decline options with equal prominence.",
         "consent_forms",
         "practice ('dark patterns' is not a DPDPA term; pre-selection also fails s.6(1) 'clear affirmative action')", MED, _PRACTICE),
        (O, "A test sign-up that declines every optional purpose completes and reaches the core service.",
         "consent_forms (recorded walkthrough)", "DPDPA s.6(1)", HIGH, _MAY27),
    ),
    # ── Cross-border transfer ─────────────────────────────────────────────
    "CB.TRANSFER.1": _criteria(
        "CB.TRANSFER.1",
        (D, "An inventory lists every flow of personal data outside India with the destination country and the recipient.",
         "cross_border_safeguards; data_flow_diagram", "practice (needed to apply s.16(1) and r.15)", MED, _PRACTICE),
        (D, "A procedure checks destinations against any country or territory restricted by Central Government notification and stops transfers to them.",
         "cross_border_safeguards", "DPDPA s.16(1)", HIGH, _S16),
        (D, "A named owner tracks Central Government orders on making transferred personal data available to foreign States and applies them to transfers.",
         "cross_border_safeguards", "DPDP Rules 2025 r.15 (content depends on future general or special orders)", MED, _MAY27),
        (O, "Hosting regions of a sample of systems holding personal data match the transfer inventory.",
         "cloud hosting configuration; cross_border_safeguards", "practice", MED, _PRACTICE),
    ),
    "CB.TRANSFER.2": _criteria(
        "CB.TRANSFER.2",
        (D, "Recipients outside India that act as Data Processors are engaged under a signed contract that requires reasonable security safeguards.",
         "vendor_agreements; cross_border_safeguards", "DPDPA s.8(2); DPDP Rules 2025 r.6(1)(f)", HIGH, _MAY27),
        (D, "Transfer agreements oblige the overseas recipient to comply with any restriction the organisation must meet under r.15 orders.",
         "cross_border_safeguards",
         "DPDP Rules 2025 r.15; a contract term is one means, not a stated requirement, and no r.15 order has been found",
         LOW, _MAY27),
        (D, "Agreements with overseas recipients that are themselves Data Fiduciaries impose data protection obligations on them.",
         "cross_border_safeguards",
         "practice [repo requires contractual safeguards for all transfers; the Act uses a restricted-country model (s.16(1)) and does not require transfer contracts]",
         LOW, _PRACTICE),
        (O, "Every flow in the cross-border inventory has a matching signed agreement on file.",
         "cross_border_safeguards; vendor_agreements", "practice (s.8(2) for processor flows)", MED, _PRACTICE),
    ),
    "CB.TRANSFER.3": _criteria(
        "CB.TRANSFER.3",
        (D, "A register records each sectoral law or regulator direction applicable to the organisation that requires personal data to be stored in, or kept within, India.",
         "legal_register; cross_border_safeguards", "DPDPA s.16(2) (preserves stricter sectoral transfer laws); the register is practice", MED, _SECTORAL),
        (D, "For each localisation requirement in the register, the storage location of the affected data is documented as India.",
         "cross_border_safeguards; data_flow_diagram", "DPDPA s.16(2)", MED, _SECTORAL),
        (D, "If the organisation is an SDF, a control keeps personal data specified by the Central Government under r.13(4), and the traffic data about its flow, from leaving India.",
         "cross_border_safeguards", "DPDP Rules 2025 r.13(4); no data has yet been specified", LOW, _SDF + " No personal data has yet been specified under r.13(4)."),
        (O, "Hosting configuration for data under a localisation requirement shows India regions only, including backups and DR copies.",
         "cloud hosting configuration; backup", "DPDPA s.16(2); DPDP Rules 2025 r.13(4)", MED, _SECTORAL),
    ),
    # ── Breach notification ───────────────────────────────────────────────
    "BN.NOTIFY.1": _criteria(
        "BN.NOTIFY.1",
        (D, "The breach procedure requires an initial intimation to the Data Protection Board without delay on becoming aware of a personal data breach, describing its nature, extent, timing, location and likely impact.",
         "breach_procedure", "DPDPA s.8(6); DPDP Rules 2025 r.7(2)(a)", HIGH, _MAY27),
        (D, "The procedure requires a detailed follow-up report to the Board within 72 hours of becoming aware of the breach, or within a longer period the Board allows on a written request.",
         "breach_procedure",
         "DPDP Rules 2025 r.7(2)(b) [the 72-hour period comes from the Rules; Act s.8(6) sets no timeline]", HIGH, _MAY27),
        (D, "The Board report template covers updated details of the breach, its facts and causes, mitigation measures, findings on who caused it, measures to prevent recurrence, and a report of the intimations sent to data principals.",
         "breach_procedure (Board report template)", "DPDP Rules 2025 r.7(2)(b)(i)-(vi)", HIGH, _MAY27),
        (D, "The procedure applies to every personal data breach as defined in the Act, with no harm or materiality threshold for intimating the Board.",
         "breach_procedure", "DPDPA s.2(u), s.8(6)", HIGH, _MAY27),
        (O, "For each personal data breach in the period, records show the initial intimation and the detailed report reached the Board on time.",
         "incident_log; Board submission records", "DPDP Rules 2025 r.7(2)", HIGH, _MAY27),
    ),
    "BN.NOTIFY.2": _criteria(
        "BN.NOTIFY.2",
        (D, "The breach procedure requires intimating each affected data principal without delay, through her user account or a communication channel she registered.",
         "breach_procedure", "DPDPA s.8(6); DPDP Rules 2025 r.7(1)", HIGH, _MAY27),
        (D, "The data principal notification template covers the breach's nature, extent and timing; likely consequences for her; mitigation measures taken; steps she can take; and a contact for queries.",
         "breach_procedure (notification template)", "DPDP Rules 2025 r.7(1)(a)-(e)", HIGH, _MAY27),
        (D, "The procedure notifies every affected data principal, with no risk or harm threshold.",
         "breach_procedure", "DPDPA s.8(6); DPDP Rules 2025 r.7(1)", HIGH, _MAY27),
        (O, "For each personal data breach in the period, records show affected data principals were sent a notification containing the template content.",
         "incident_log; notification dispatch records", "DPDP Rules 2025 r.7(1)", HIGH, _MAY27),
    ),
    "BN.NOTIFY.3": _criteria(
        "BN.NOTIFY.3",
        (D, "An approved incident response plan covers detection, containment, investigation, notification and remediation of personal data breaches.",
         "breach_procedure", "practice (supports DPDPA s.8(5); DPDP Rules 2025 r.6(1)(c), r.7)", MED, _PRACTICE),
        (D, "The plan names the roles that decide a breach has occurred and that send the Board and data principal intimations.",
         "breach_procedure", "practice (supports DPDP Rules 2025 r.7)", MED, _PRACTICE),
        (D, "The plan includes a method for identifying affected data principals and their registered contact channels.",
         "breach_procedure", "DPDP Rules 2025 r.7(1) (needed to notify each affected data principal)", MED, _MAY27),
        (O, "The plan was exercised (tabletop or real incident) in the last 12 months and lessons were recorded.",
         "breach_procedure; incident_log; exercise report", "practice", MED, _PRACTICE),
    ),
    "BN.NOTIFY.4": _criteria(
        "BN.NOTIFY.4",
        (D, "A breach register records each personal data breach with its facts, effects and remedial actions.",
         "incident_log", "practice (content mirrors DPDP Rules 2025 r.7(2)(b))", MED, _PRACTICE),
        (D, "Each register entry records when the Board and the affected data principals were intimated.",
         "incident_log", "practice (evidences DPDP Rules 2025 r.7(1)-(2))", MED, _PRACTICE),
        (O, "Every personal data breach in the security incident log for the period appears in the breach register.",
         "incident_log; security incident tickets", "practice", MED, _PRACTICE),
    ),
}
