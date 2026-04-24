"""
GDPR (EU) 2016/679 framework definition.

Based on the General Data Protection Regulation, covering Articles 5-49,
organized by 6 domains:
  - Lawfulness & Transparency (Art 5-6, 12-14)
  - Data Subject Rights (Art 15-22)
  - Data Controller Obligations (Art 25, 30, 35, 37-39, 5(1)(c)(e))
  - Data Processor & Transfers (Art 28, 44-49)
  - Security & Breach (Art 32-34)
  - Accountability & Governance (Art 5(2), 31)

Total: ~45 assessable controls.
"""

from app.frameworks.schema import (
    Control,
    Domain,
    FrameworkDefinition,
    QuestionDef,
    RedFlagPattern,
    ScopeQuestion,
    Section,
)

# ── Domain 1: Lawfulness & Transparency ─────────────────────────────────

_LAWFUL_BASIS = Section(
    key="lawful_basis",
    title="Lawful Basis for Processing",
    weight=0.55,
    controls=[
        Control(
            id="GDPR.ART6.1",
            title="Identification of lawful basis",
            description="The controller shall identify and document the appropriate lawful basis under Article 6(1) for each processing activity before processing begins.",
            reference="Art 6(1)",
            criticality="critical",
            tags=["lawful-basis", "documentation", "accountability"],
        ),
        Control(
            id="GDPR.ART6.2",
            title="Consent standards",
            description="Where consent is the lawful basis, it shall be freely given, specific, informed, unambiguous, and as easy to withdraw as to give. Records of consent must be maintained.",
            reference="Art 6(1)(a), Art 7",
            criticality="critical",
            tags=["consent", "lawful-basis", "data-subject-rights"],
        ),
        Control(
            id="GDPR.ART6.3",
            title="Legitimate interest assessment",
            description="Where legitimate interest is relied upon, the controller shall conduct and document a balancing test weighing the controller's interest against the data subject's rights and freedoms.",
            reference="Art 6(1)(f)",
            criticality="high",
            tags=["lawful-basis", "legitimate-interest", "risk-assessment"],
        ),
        Control(
            id="GDPR.ART6.4",
            title="Purpose limitation and compatibility",
            description="Personal data shall be collected for specified, explicit and legitimate purposes and not further processed in a manner incompatible with those purposes.",
            reference="Art 5(1)(b), Art 6(4)",
            criticality="critical",
            tags=["lawful-basis", "purpose-limitation", "data-minimization"],
        ),
        Control(
            id="GDPR.ART9.1",
            title="Special category data safeguards",
            description="Processing of special categories of personal data (racial/ethnic origin, health, biometrics, etc.) is prohibited unless an explicit exception under Article 9(2) applies, with appropriate safeguards documented.",
            reference="Art 9",
            criticality="critical",
            tags=["special-categories", "lawful-basis", "sensitive-data"],
        ),
    ],
)

_TRANSPARENCY_NOTICE = Section(
    key="transparency_notice",
    title="Transparency & Notice",
    weight=0.45,
    controls=[
        Control(
            id="GDPR.ART12.1",
            title="Transparent communication",
            description="Information and communications relating to processing shall be provided in a concise, transparent, intelligible and easily accessible form, using clear and plain language.",
            reference="Art 12(1)",
            criticality="high",
            tags=["privacy-notice", "transparency", "communication"],
        ),
        Control(
            id="GDPR.ART13.1",
            title="Privacy notice — direct collection",
            description="When personal data is collected from the data subject, the controller shall provide identity, purposes, lawful basis, recipients, transfer details, retention period, and rights information at the time of collection.",
            reference="Art 13",
            criticality="critical",
            tags=["privacy-notice", "transparency", "data-collection"],
        ),
        Control(
            id="GDPR.ART14.1",
            title="Privacy notice — indirect collection",
            description="When data is not obtained directly from the data subject, the controller shall provide the same information as Art 13 plus the source and categories of data, within one month or at first communication.",
            reference="Art 14",
            criticality="high",
            tags=["privacy-notice", "transparency", "third-party-data"],
        ),
        Control(
            id="GDPR.ART12.2",
            title="Layered and accessible notices",
            description="Privacy notices shall use layered approaches where appropriate (short notice + full policy) and be available in accessible formats for different audiences.",
            reference="Art 12(1), Art 12(7)",
            criticality="medium",
            tags=["privacy-notice", "transparency", "accessibility"],
        ),
    ],
)

# ── Domain 2: Data Subject Rights ───────────────────────────────────────

_ACCESS_PORTABILITY = Section(
    key="access_portability",
    title="Access & Portability",
    weight=0.35,
    controls=[
        Control(
            id="GDPR.ART15.1",
            title="Right of access",
            description="Data subjects shall have the right to obtain confirmation of processing and access to their personal data along with supplementary information, fulfilled within one month.",
            reference="Art 15",
            criticality="critical",
            tags=["data-subject-rights", "right-of-access", "transparency"],
        ),
        Control(
            id="GDPR.ART15.2",
            title="Subject access request process",
            description="The controller shall have a documented process for receiving, verifying identity, and responding to subject access requests within the prescribed time limits, including provisions for extensions and refusals.",
            reference="Art 12(3-4), Art 15",
            criticality="high",
            tags=["data-subject-rights", "right-of-access", "process"],
        ),
        Control(
            id="GDPR.ART20.1",
            title="Right to data portability",
            description="Where processing is based on consent or contract and carried out by automated means, data subjects shall receive their data in a structured, commonly used, machine-readable format and have the right to transmit it to another controller.",
            reference="Art 20",
            criticality="high",
            tags=["data-subject-rights", "data-portability", "interoperability"],
        ),
    ],
)

_RECTIFICATION_ERASURE = Section(
    key="rectification_erasure",
    title="Rectification, Erasure & Restriction",
    weight=0.40,
    controls=[
        Control(
            id="GDPR.ART16.1",
            title="Right to rectification",
            description="Data subjects shall have the right to obtain rectification of inaccurate personal data and completion of incomplete data without undue delay.",
            reference="Art 16",
            criticality="high",
            tags=["data-subject-rights", "rectification", "data-quality"],
        ),
        Control(
            id="GDPR.ART17.1",
            title="Right to erasure (right to be forgotten)",
            description="Data subjects shall have the right to obtain erasure of personal data where specific grounds apply (consent withdrawn, no longer necessary, unlawful processing, etc.), including notification to third parties.",
            reference="Art 17",
            criticality="critical",
            tags=["data-subject-rights", "right-to-erasure", "data-deletion"],
        ),
        Control(
            id="GDPR.ART17.2",
            title="Erasure propagation to third parties",
            description="Where the controller has made personal data public, it shall take reasonable steps to inform other controllers processing the data that the data subject has requested erasure of links, copies or replications.",
            reference="Art 17(2)",
            criticality="high",
            tags=["data-subject-rights", "right-to-erasure", "third-party"],
        ),
        Control(
            id="GDPR.ART18.1",
            title="Right to restriction of processing",
            description="Data subjects shall have the right to obtain restriction of processing where accuracy is contested, processing is unlawful, the controller no longer needs the data, or pending objection verification.",
            reference="Art 18",
            criticality="medium",
            tags=["data-subject-rights", "restriction", "processing-limitation"],
        ),
        Control(
            id="GDPR.ART19.1",
            title="Notification obligation for rectification/erasure/restriction",
            description="The controller shall communicate any rectification, erasure or restriction of processing to each recipient to whom data was disclosed, unless impossible or involving disproportionate effort.",
            reference="Art 19",
            criticality="medium",
            tags=["data-subject-rights", "notification", "third-party"],
        ),
    ],
)

_OBJECTION_ADM = Section(
    key="objection_adm",
    title="Objection & Automated Decision-Making",
    weight=0.25,
    controls=[
        Control(
            id="GDPR.ART21.1",
            title="Right to object",
            description="Data subjects shall have the right to object to processing based on public interest or legitimate interest, including profiling. The right to object to direct marketing shall be absolute.",
            reference="Art 21",
            criticality="high",
            tags=["data-subject-rights", "right-to-object", "direct-marketing"],
        ),
        Control(
            id="GDPR.ART22.1",
            title="Automated individual decision-making",
            description="Data subjects shall have the right not to be subject to decisions based solely on automated processing, including profiling, which produce legal or similarly significant effects, except where authorized by law, contract, or explicit consent.",
            reference="Art 22",
            criticality="high",
            tags=["data-subject-rights", "automated-decision-making", "profiling", "ai-governance"],
        ),
        Control(
            id="GDPR.ART22.2",
            title="Safeguards for automated decisions",
            description="Where automated decision-making is permitted, the controller shall implement suitable safeguards including the right to obtain human intervention, express their point of view, and contest the decision.",
            reference="Art 22(3)",
            criticality="high",
            tags=["data-subject-rights", "automated-decision-making", "human-oversight"],
        ),
    ],
)

# ── Domain 3: Data Controller Obligations ───────────────────────────────

_DESIGN_DEFAULT = Section(
    key="design_default",
    title="Data Protection by Design & Default",
    weight=0.20,
    controls=[
        Control(
            id="GDPR.ART25.1",
            title="Data protection by design",
            description="The controller shall implement appropriate technical and organisational measures (such as pseudonymisation) designed to implement data-protection principles effectively and integrate safeguards into processing.",
            reference="Art 25(1)",
            criticality="critical",
            tags=["privacy-by-design", "technical-measures", "data-minimization"],
        ),
        Control(
            id="GDPR.ART25.2",
            title="Data protection by default",
            description="The controller shall implement measures to ensure that by default only personal data necessary for each specific purpose is processed, with regard to amount, extent, storage period and accessibility.",
            reference="Art 25(2)",
            criticality="high",
            tags=["privacy-by-design", "data-minimization", "default-settings"],
        ),
    ],
)

_RECORDS = Section(
    key="records",
    title="Records of Processing Activities",
    weight=0.20,
    controls=[
        Control(
            id="GDPR.ART30.1",
            title="Record of processing activities — controller",
            description="The controller shall maintain a written record of processing activities including purposes, data categories, recipients, transfers, retention periods, and technical/organisational security measures.",
            reference="Art 30(1)",
            criticality="critical",
            tags=["accountability", "documentation", "data-inventory", "records-of-processing"],
        ),
        Control(
            id="GDPR.ART30.2",
            title="Record of processing activities — processor",
            description="Each processor shall maintain a record of all categories of processing activities carried out on behalf of controllers, including transfers and security measures.",
            reference="Art 30(2)",
            criticality="high",
            tags=["accountability", "documentation", "processor-management", "records-of-processing"],
        ),
    ],
)

_DPIA = Section(
    key="dpia",
    title="Data Protection Impact Assessment",
    weight=0.20,
    controls=[
        Control(
            id="GDPR.ART35.1",
            title="DPIA requirement and process",
            description="Where processing is likely to result in a high risk to rights and freedoms, the controller shall carry out a DPIA containing a systematic description, necessity/proportionality assessment, risk assessment, and mitigation measures.",
            reference="Art 35",
            criticality="critical",
            tags=["dpia", "risk-assessment", "privacy-by-design", "accountability"],
        ),
        Control(
            id="GDPR.ART35.2",
            title="DPIA trigger identification",
            description="The controller shall have criteria and processes to identify when a DPIA is required, including systematic monitoring, large-scale special category processing, and systematic evaluation of individuals.",
            reference="Art 35(3)",
            criticality="high",
            tags=["dpia", "risk-assessment", "process"],
        ),
        Control(
            id="GDPR.ART36.1",
            title="Prior consultation with supervisory authority",
            description="Where a DPIA indicates high residual risk, the controller shall consult the supervisory authority before processing, providing prescribed information about the planned processing.",
            reference="Art 36",
            criticality="high",
            tags=["dpia", "supervisory-authority", "regulatory-engagement"],
        ),
    ],
)

_DPO = Section(
    key="dpo",
    title="Data Protection Officer",
    weight=0.15,
    controls=[
        Control(
            id="GDPR.ART37.1",
            title="DPO designation",
            description="The controller and processor shall designate a DPO where processing is carried out by a public authority, core activities require regular and systematic monitoring at scale, or core activities consist of large-scale special category processing.",
            reference="Art 37",
            criticality="high",
            tags=["dpo", "governance", "organizational-structure"],
        ),
        Control(
            id="GDPR.ART38.1",
            title="DPO position and independence",
            description="The controller shall ensure the DPO is involved in all data protection matters, provided with necessary resources, and not given instructions regarding exercise of their tasks. The DPO shall report to the highest management level.",
            reference="Art 38",
            criticality="high",
            tags=["dpo", "governance", "independence"],
        ),
        Control(
            id="GDPR.ART39.1",
            title="DPO tasks and engagement",
            description="The DPO shall inform and advise, monitor compliance, provide advice on DPIAs, cooperate with the supervisory authority, and act as the contact point. The DPO shall have regard to the risk associated with processing.",
            reference="Art 39",
            criticality="medium",
            tags=["dpo", "governance", "advisory"],
        ),
    ],
)

_MINIMIZATION_RETENTION = Section(
    key="minimization_retention",
    title="Data Minimization & Storage Limitation",
    weight=0.25,
    controls=[
        Control(
            id="GDPR.ART5C.1",
            title="Data minimization",
            description="Personal data shall be adequate, relevant and limited to what is necessary in relation to the purposes for which they are processed.",
            reference="Art 5(1)(c)",
            criticality="high",
            tags=["data-minimization", "purpose-limitation", "privacy-by-design"],
        ),
        Control(
            id="GDPR.ART5E.1",
            title="Storage limitation and retention policy",
            description="Personal data shall be kept in a form permitting identification for no longer than necessary. The controller shall have documented retention schedules and deletion/anonymisation procedures.",
            reference="Art 5(1)(e)",
            criticality="high",
            tags=["data-retention", "storage-limitation", "data-deletion"],
        ),
        Control(
            id="GDPR.ART5D.1",
            title="Data accuracy",
            description="Personal data shall be accurate and, where necessary, kept up to date. Every reasonable step must be taken to ensure inaccurate data is erased or rectified without delay.",
            reference="Art 5(1)(d)",
            criticality="medium",
            tags=["data-quality", "accuracy", "rectification"],
        ),
    ],
)

# ── Domain 4: Data Processor & Transfers ────────────────────────────────

_PROCESSOR = Section(
    key="processor",
    title="Processor Requirements",
    weight=0.45,
    controls=[
        Control(
            id="GDPR.ART28.1",
            title="Processor due diligence and selection",
            description="The controller shall use only processors providing sufficient guarantees to implement appropriate technical and organisational measures so that processing meets GDPR requirements.",
            reference="Art 28(1)",
            criticality="high",
            tags=["processor-management", "third-party", "due-diligence"],
        ),
        Control(
            id="GDPR.ART28.2",
            title="Data processing agreement",
            description="Processing by a processor shall be governed by a written contract setting out subject-matter, duration, nature and purpose, data types, categories of data subjects, and controller obligations and rights.",
            reference="Art 28(3)",
            criticality="critical",
            tags=["processor-management", "contracts", "data-processing-agreement"],
        ),
        Control(
            id="GDPR.ART28.3",
            title="Sub-processor authorization and oversight",
            description="The processor shall not engage another processor without prior specific or general written authorization of the controller, with the same data protection obligations imposed by contract.",
            reference="Art 28(2), Art 28(4)",
            criticality="high",
            tags=["processor-management", "sub-processor", "supply-chain"],
        ),
    ],
)

_INTERNATIONAL_TRANSFERS = Section(
    key="international_transfers",
    title="International Data Transfers",
    weight=0.55,
    controls=[
        Control(
            id="GDPR.ART44.1",
            title="Transfer principles and governance",
            description="Any transfer of personal data to a third country or international organisation shall comply with the conditions in Chapter V, including all other GDPR provisions.",
            reference="Art 44",
            criticality="critical",
            tags=["cross-border", "data-transfer", "governance"],
        ),
        Control(
            id="GDPR.ART45.1",
            title="Adequacy decision reliance",
            description="Transfers may take place where the Commission has decided that the third country ensures an adequate level of protection. The controller shall monitor continued adequacy.",
            reference="Art 45",
            criticality="high",
            tags=["cross-border", "data-transfer", "adequacy-decision"],
        ),
        Control(
            id="GDPR.ART46.1",
            title="Standard contractual clauses (SCCs)",
            description="In the absence of an adequacy decision, transfers may take place subject to appropriate safeguards such as standard contractual clauses adopted by the Commission, supplemented by transfer impact assessments where necessary.",
            reference="Art 46(2)(c)",
            criticality="high",
            tags=["cross-border", "data-transfer", "sccs", "safeguards"],
        ),
        Control(
            id="GDPR.ART47.1",
            title="Binding corporate rules (BCRs)",
            description="Intra-group transfers may rely on binding corporate rules approved by the competent supervisory authority, containing all elements specified in Article 47(2).",
            reference="Art 47",
            criticality="medium",
            tags=["cross-border", "data-transfer", "bcrs", "intra-group"],
        ),
        Control(
            id="GDPR.ART49.1",
            title="Derogations for specific situations",
            description="In the absence of adequacy or appropriate safeguards, transfers may only occur under specific derogations (explicit consent, contract necessity, public interest, legal claims, vital interests) which must be strictly interpreted.",
            reference="Art 49",
            criticality="medium",
            tags=["cross-border", "data-transfer", "derogations"],
        ),
    ],
)

# ── Domain 5: Security & Breach ─────────────────────────────────────────

_SECURITY = Section(
    key="security",
    title="Security of Processing",
    weight=0.45,
    controls=[
        Control(
            id="GDPR.ART32.1",
            title="Appropriate technical and organisational measures",
            description="The controller and processor shall implement appropriate security measures taking into account the state of the art, costs, nature/scope/context/purposes of processing, and risks to data subjects.",
            reference="Art 32(1)",
            criticality="critical",
            tags=["encryption", "security", "technical-measures", "risk-assessment"],
        ),
        Control(
            id="GDPR.ART32.2",
            title="Pseudonymisation and encryption",
            description="Security measures shall include, as appropriate, pseudonymisation and encryption of personal data to reduce risks from unauthorized access or disclosure.",
            reference="Art 32(1)(a)",
            criticality="high",
            tags=["encryption", "pseudonymisation", "security", "technical-measures"],
        ),
        Control(
            id="GDPR.ART32.3",
            title="Resilience and availability",
            description="The controller shall ensure ongoing confidentiality, integrity, availability and resilience of processing systems and services, and the ability to restore availability and access in a timely manner following an incident.",
            reference="Art 32(1)(b)(c)",
            criticality="high",
            tags=["security", "resilience", "availability", "business-continuity"],
        ),
        Control(
            id="GDPR.ART32.4",
            title="Security testing and evaluation",
            description="The controller shall have a process for regularly testing, assessing and evaluating the effectiveness of technical and organisational security measures.",
            reference="Art 32(1)(d)",
            criticality="high",
            tags=["security", "testing", "audit", "continuous-improvement"],
        ),
    ],
)

_BREACH = Section(
    key="breach",
    title="Breach Notification",
    weight=0.55,
    controls=[
        Control(
            id="GDPR.ART33.1",
            title="Breach notification to supervisory authority",
            description="In the case of a personal data breach, the controller shall notify the competent supervisory authority without undue delay and where feasible within 72 hours, unless unlikely to result in risk to rights and freedoms.",
            reference="Art 33(1)",
            criticality="critical",
            tags=["breach-notification", "supervisory-authority", "incident-response"],
        ),
        Control(
            id="GDPR.ART33.2",
            title="Breach documentation and record-keeping",
            description="The controller shall document all personal data breaches including facts, effects and remedial action taken, enabling the supervisory authority to verify compliance.",
            reference="Art 33(5)",
            criticality="high",
            tags=["breach-notification", "documentation", "incident-response"],
        ),
        Control(
            id="GDPR.ART33.3",
            title="Processor breach notification to controller",
            description="The processor shall notify the controller without undue delay after becoming aware of a personal data breach.",
            reference="Art 33(2)",
            criticality="high",
            tags=["breach-notification", "processor-management", "incident-response"],
        ),
        Control(
            id="GDPR.ART34.1",
            title="Communication of breach to data subjects",
            description="When a breach is likely to result in a high risk to rights and freedoms, the controller shall communicate the breach to affected data subjects without undue delay in clear and plain language.",
            reference="Art 34",
            criticality="critical",
            tags=["breach-notification", "data-subject-rights", "communication"],
        ),
    ],
)

# ── Domain 6: Accountability & Governance ───────────────────────────────

_ACCOUNTABILITY = Section(
    key="accountability",
    title="Accountability Principle",
    weight=0.55,
    controls=[
        Control(
            id="GDPR.ART5.1",
            title="Accountability and demonstrable compliance",
            description="The controller shall be responsible for and be able to demonstrate compliance with all data protection principles (lawfulness, fairness, transparency, purpose limitation, minimization, accuracy, storage limitation, integrity/confidentiality).",
            reference="Art 5(2)",
            criticality="critical",
            tags=["accountability", "governance", "documentation", "compliance"],
        ),
        Control(
            id="GDPR.ART24.1",
            title="Controller responsibility and governance framework",
            description="The controller shall implement appropriate technical and organisational measures to ensure and demonstrate that processing is performed in accordance with the GDPR, reviewed and updated as necessary.",
            reference="Art 24",
            criticality="high",
            tags=["accountability", "governance", "management-commitment"],
        ),
        Control(
            id="GDPR.ART24.2",
            title="Data protection policies",
            description="Where proportionate, the controller shall implement appropriate data protection policies covering all processing activities.",
            reference="Art 24(2)",
            criticality="high",
            tags=["accountability", "policy", "governance"],
        ),
    ],
)

_SUPERVISORY = Section(
    key="supervisory",
    title="Supervisory Authority Cooperation",
    weight=0.45,
    controls=[
        Control(
            id="GDPR.ART31.1",
            title="Cooperation with supervisory authority",
            description="The controller and processor shall cooperate with the supervisory authority in the performance of its tasks, on request.",
            reference="Art 31",
            criticality="high",
            tags=["supervisory-authority", "governance", "regulatory-engagement"],
        ),
        Control(
            id="GDPR.ART27.1",
            title="Representative in the Union",
            description="Where the controller or processor is not established in the EU but processes data of EU data subjects, a representative in the Union shall be designated in writing.",
            reference="Art 27",
            criticality="medium",
            tags=["governance", "representation", "regulatory-engagement"],
        ),
    ],
)

# ── Assemble domains ────────────────────────────────────────────────────

_LAWFULNESS_TRANSPARENCY = Domain(
    key="lawfulness_transparency",
    title="Lawfulness & Transparency",
    weight=0.20,
    sections={
        "lawful_basis": _LAWFUL_BASIS,
        "transparency_notice": _TRANSPARENCY_NOTICE,
    },
)

_DATA_SUBJECT_RIGHTS = Domain(
    key="data_subject_rights",
    title="Data Subject Rights",
    weight=0.20,
    sections={
        "access_portability": _ACCESS_PORTABILITY,
        "rectification_erasure": _RECTIFICATION_ERASURE,
        "objection_adm": _OBJECTION_ADM,
    },
)

_CONTROLLER_OBLIGATIONS = Domain(
    key="controller_obligations",
    title="Data Controller Obligations",
    weight=0.25,
    sections={
        "design_default": _DESIGN_DEFAULT,
        "records": _RECORDS,
        "dpia": _DPIA,
        "dpo": _DPO,
        "minimization_retention": _MINIMIZATION_RETENTION,
    },
)

_PROCESSOR_TRANSFERS = Domain(
    key="processor_transfers",
    title="Data Processor & Transfers",
    weight=0.15,
    sections={
        "processor": _PROCESSOR,
        "international_transfers": _INTERNATIONAL_TRANSFERS,
    },
)

_SECURITY_BREACH = Domain(
    key="security_breach",
    title="Security & Breach",
    weight=0.10,
    sections={
        "security": _SECURITY,
        "breach": _BREACH,
    },
)

_ACCOUNTABILITY_GOVERNANCE = Domain(
    key="accountability_governance",
    title="Accountability & Governance",
    weight=0.10,
    sections={
        "accountability": _ACCOUNTABILITY,
        "supervisory": _SUPERVISORY,
    },
)

# ── Dependency DAG ──────────────────────────────────────────────────────

_GDPR_DEPENDENCIES: dict[str, list[str]] = {
    # Consent depends on lawful basis identification
    "GDPR.ART6.2": ["GDPR.ART6.1"],
    # Legitimate interest assessment depends on lawful basis identification
    "GDPR.ART6.3": ["GDPR.ART6.1"],
    # Privacy notices require lawful basis to be identified first
    "GDPR.ART13.1": ["GDPR.ART6.1"],
    "GDPR.ART14.1": ["GDPR.ART6.1"],
    # Layered notices build on the core privacy notice
    "GDPR.ART12.2": ["GDPR.ART13.1"],
    # SAR process requires access right to be established
    "GDPR.ART15.2": ["GDPR.ART15.1"],
    # Erasure propagation requires erasure right
    "GDPR.ART17.2": ["GDPR.ART17.1"],
    # Notification obligation depends on the underlying rights
    "GDPR.ART19.1": ["GDPR.ART16.1", "GDPR.ART17.1", "GDPR.ART18.1"],
    # Automated decision-making safeguards depend on ADM identification
    "GDPR.ART22.2": ["GDPR.ART22.1"],
    # Privacy by default depends on privacy by design
    "GDPR.ART25.2": ["GDPR.ART25.1"],
    # DPIA triggers depend on DPIA process
    "GDPR.ART35.2": ["GDPR.ART35.1"],
    # Prior consultation depends on DPIA
    "GDPR.ART36.1": ["GDPR.ART35.1"],
    # DPO position/tasks depend on DPO designation
    "GDPR.ART38.1": ["GDPR.ART37.1"],
    "GDPR.ART39.1": ["GDPR.ART37.1"],
    # Sub-processor oversight depends on processor agreement
    "GDPR.ART28.3": ["GDPR.ART28.2"],
    # Transfer mechanisms depend on transfer governance
    "GDPR.ART45.1": ["GDPR.ART44.1"],
    "GDPR.ART46.1": ["GDPR.ART44.1"],
    "GDPR.ART47.1": ["GDPR.ART44.1"],
    "GDPR.ART49.1": ["GDPR.ART44.1"],
    # Breach documentation depends on notification obligation
    "GDPR.ART33.2": ["GDPR.ART33.1"],
    # Communication to data subjects depends on breach notification process
    "GDPR.ART34.1": ["GDPR.ART33.1"],
    # Processor breach notification supports controller notification
    "GDPR.ART33.3": ["GDPR.ART33.1"],
    # Data protection policies depend on accountability principle
    "GDPR.ART24.2": ["GDPR.ART5.1"],
}

# ── Root cause clusters ─────────────────────────────────────────────────

_GDPR_ROOT_CAUSE_CLUSTERS: dict[str, dict] = {
    "policy": {
        "title": "Data Protection Policy & Documentation Program",
        "description": "Develop, formalize and maintain privacy policies, notices, and processing records that demonstrate GDPR compliance.",
        "typical_requirements": [
            "GDPR.ART5.1", "GDPR.ART12.1", "GDPR.ART13.1", "GDPR.ART14.1",
            "GDPR.ART24.2", "GDPR.ART30.1",
        ],
    },
    "people": {
        "title": "Privacy Awareness & Data Protection Training",
        "description": "Build a privacy-aware culture through targeted training, DPO engagement, and clear roles and responsibilities.",
        "typical_requirements": [
            "GDPR.ART37.1", "GDPR.ART38.1", "GDPR.ART39.1", "GDPR.ART31.1",
        ],
    },
    "process": {
        "title": "Data Protection Process & Rights Fulfilment",
        "description": "Establish repeatable processes for data subject rights, consent management, DPIA, breach response, and lawful basis assessment.",
        "typical_requirements": [
            "GDPR.ART6.1", "GDPR.ART6.2", "GDPR.ART15.2", "GDPR.ART17.1",
            "GDPR.ART33.1", "GDPR.ART35.1",
        ],
    },
    "technology": {
        "title": "Privacy-Enhancing Technology & Security Controls",
        "description": "Implement or upgrade technical measures including encryption, pseudonymisation, access controls, and privacy by design/default.",
        "typical_requirements": [
            "GDPR.ART25.1", "GDPR.ART25.2", "GDPR.ART32.1", "GDPR.ART32.2",
            "GDPR.ART32.3", "GDPR.ART20.1",
        ],
    },
    "governance": {
        "title": "Data Protection Governance & Accountability Framework",
        "description": "Establish management oversight, regulatory engagement, international transfer governance, and processor management framework.",
        "typical_requirements": [
            "GDPR.ART24.1", "GDPR.ART28.2", "GDPR.ART44.1", "GDPR.ART5.1",
        ],
    },
}

# ── Scope questions ─────────────────────────────────────────────────────

_GDPR_SCOPE_QUESTIONS = [
    ScopeQuestion(
        id="GDPR.SCP.1",
        question="Does your organisation process personal data of individuals located in the EU/EEA?",
        help_text="GDPR applies to processing of personal data of EU/EEA data subjects, regardless of where the controller is established.",
        type="single_select",
        options=[
            {"value": "yes_established", "label": "Yes — we are established in the EU/EEA"},
            {"value": "yes_offering", "label": "Yes — we offer goods/services to EU/EEA individuals"},
            {"value": "yes_monitoring", "label": "Yes — we monitor behaviour of EU/EEA individuals"},
            {"value": "no", "label": "No EU/EEA data subjects"},
        ],
    ),
    ScopeQuestion(
        id="GDPR.SCP.2",
        question="What is the scale and nature of your personal data processing activities?",
        help_text="Large-scale processing triggers additional obligations (DPO, DPIA, records of processing).",
        type="single_select",
        options=[
            {"value": "large_scale_sensitive", "label": "Large-scale processing including special category data"},
            {"value": "large_scale", "label": "Large-scale processing of ordinary personal data"},
            {"value": "moderate", "label": "Moderate-scale processing (multiple systems/processes)"},
            {"value": "small", "label": "Small-scale processing (limited data, few processes)"},
        ],
    ),
    ScopeQuestion(
        id="GDPR.SCP.3",
        question="Does your organisation transfer personal data outside the EU/EEA?",
        help_text="International transfers require adequacy decisions, SCCs, BCRs, or specific derogations under Chapter V.",
        type="single_select",
        options=[
            {"value": "yes_adequacy", "label": "Yes — to countries with adequacy decisions"},
            {"value": "yes_safeguards", "label": "Yes — using SCCs/BCRs/other safeguards"},
            {"value": "yes_unsure", "label": "Yes — transfer mechanisms not fully established"},
            {"value": "no", "label": "No international transfers"},
        ],
    ),
    ScopeQuestion(
        id="GDPR.SCP.4",
        question="Does your organisation act as a controller, processor, or both?",
        help_text="Controllers and processors have different obligations. Joint controllership adds further requirements.",
        type="single_select",
        options=[
            {"value": "controller", "label": "Data controller only"},
            {"value": "processor", "label": "Data processor only"},
            {"value": "both", "label": "Both controller and processor (depending on activity)"},
            {"value": "unsure", "label": "Not clearly determined"},
        ],
    ),
]

# ── Questions ───────────────────────────────────────────────────────────
# Substantive questions per control — not generic "have you implemented X?"

_GDPR_QUESTION_MAP: dict[str, tuple[str, str]] = {
    # Domain 1 — Lawfulness & Transparency
    "GDPR.ART6.1": (
        "How does your organisation determine and document the lawful basis for each processing activity, and how is this communicated to processing teams?",
        "Check for a lawful basis register or mapping table linked to the records of processing activities.",
    ),
    "GDPR.ART6.2": (
        "When consent is used as the lawful basis, what mechanisms ensure it is freely given, specific, informed, and unambiguous — and how do you handle withdrawal?",
        "Look for consent management platforms, granular consent forms, withdrawal mechanisms, and audit trails.",
    ),
    "GDPR.ART6.3": (
        "For processing based on legitimate interest, can you provide examples of documented balancing tests, and how do you reassess them when circumstances change?",
        "A legitimate interest assessment (LIA) template should weigh the necessity, impact on data subjects, and any safeguards.",
    ),
    "GDPR.ART6.4": (
        "How does your organisation assess compatibility when personal data collected for one purpose is considered for a new, different purpose?",
        "Look for a compatibility assessment checklist aligned to Art 6(4) criteria (link, context, nature, consequences, safeguards).",
    ),
    "GDPR.ART9.1": (
        "What controls are in place to identify when special category data is being processed, and which Art 9(2) exceptions apply?",
        "Check for a special category data register and documented conditions for processing (e.g., explicit consent, employment law).",
    ),
    "GDPR.ART12.1": (
        "How do you ensure privacy communications are genuinely understandable to your audience, including vulnerable groups or non-native speakers?",
        "Look for readability testing, user research on privacy notices, or plain-language review processes.",
    ),
    "GDPR.ART13.1": (
        "Walk through how your privacy notice is presented at the point of data collection — does it cover all Art 13 mandatory elements?",
        "Mandatory elements: controller identity, DPO contact, purposes, lawful basis, recipients, transfers, retention, rights, right to complain, automated decisions.",
    ),
    "GDPR.ART14.1": (
        "When personal data is obtained from sources other than the data subject, how and when do you provide the required Art 14 information?",
        "Check timing (within one month or at first communication) and whether the source of data is disclosed.",
    ),
    "GDPR.ART12.2": (
        "Do you use layered or just-in-time privacy notices, and how do you ensure they remain consistent with the full privacy policy?",
        "Layered notices provide key information upfront with links to detailed policy. Check for version control across layers.",
    ),
    # Domain 2 — Data Subject Rights
    "GDPR.ART15.1": (
        "What information do you provide in response to a subject access request, and how do you handle requests involving third-party data?",
        "Art 15 requires a copy of data plus supplementary information. Check for redaction procedures when third-party data is involved.",
    ),
    "GDPR.ART15.2": (
        "Describe your end-to-end process for handling a subject access request from receipt to response, including identity verification and escalation paths.",
        "Look for a documented procedure with SLAs, identity verification steps, search procedures, and approval workflows.",
    ),
    "GDPR.ART20.1": (
        "In what formats can data subjects receive their personal data for portability, and have you tested the export with common importing services?",
        "Structured, commonly used, machine-readable format required (e.g., JSON, CSV, XML). Interoperability testing is good practice.",
    ),
    "GDPR.ART16.1": (
        "How do data subjects request correction of inaccurate data, and how do you propagate corrections across systems and third parties?",
        "Check for a correction request workflow and mechanisms to cascade changes to downstream systems and processors.",
    ),
    "GDPR.ART17.1": (
        "What is your process for evaluating and executing erasure requests, including assessing applicable exceptions (e.g., legal obligation, public interest)?",
        "Look for an erasure decision tree covering all six grounds for erasure and all exceptions.",
    ),
    "GDPR.ART17.2": (
        "When data has been made public or shared with third parties, how do you inform them of an erasure request?",
        "Check for a register of data recipients and a notification procedure for propagating erasure downstream.",
    ),
    "GDPR.ART18.1": (
        "Under what circumstances would you restrict rather than erase personal data, and how is restriction technically enforced?",
        "Restriction means data is stored but not processed. Look for technical flagging mechanisms and staff procedures.",
    ),
    "GDPR.ART19.1": (
        "How do you track and notify recipients when data has been rectified, erased, or restricted?",
        "A recipient register and notification log should exist, covering all disclosures in the processing record.",
    ),
    "GDPR.ART21.1": (
        "How are objections to processing handled, particularly for direct marketing — is the process immediate and absolute for marketing?",
        "Direct marketing objections must be honoured immediately. Check for suppression lists and automated opt-out mechanisms.",
    ),
    "GDPR.ART22.1": (
        "Does your organisation make solely automated decisions with legal or significant effects, and if so, how are data subjects informed and given alternatives?",
        "Look for an inventory of automated decision-making systems, including profiling, with associated legal bases.",
    ),
    "GDPR.ART22.2": (
        "What safeguards exist for individuals subject to automated decisions — can they request human review, and who provides it?",
        "Check for a human review escalation path, trained reviewers, and documented criteria for overriding automated decisions.",
    ),
    # Domain 3 — Controller Obligations
    "GDPR.ART25.1": (
        "How is data protection integrated into the design phase of new systems, products, or processing activities — can you give a recent example?",
        "Look for privacy design checklists, privacy engineering reviews, or PbD assessments in project management workflows.",
    ),
    "GDPR.ART25.2": (
        "What default settings does your organisation apply to limit data collection and access, and how are these enforced technically?",
        "Examples: default privacy settings, minimal data fields, access restrictions, automatic data expiry.",
    ),
    "GDPR.ART30.1": (
        "How complete and current are your records of processing activities, and who is responsible for maintaining them?",
        "RoPA should cover all Art 30(1) fields. Check update frequency, ownership, and whether it reflects actual processing.",
    ),
    "GDPR.ART30.2": (
        "Where you act as a processor, do you maintain separate records of processing categories as required by Art 30(2)?",
        "Processor records should include processor/controller names, processing categories, transfers, and security measures.",
    ),
    "GDPR.ART35.1": (
        "Describe a recent DPIA you conducted — what methodology was used and how were risks mitigated?",
        "A DPIA should contain systematic description, necessity assessment, risk evaluation, and mitigation measures per Art 35(7).",
    ),
    "GDPR.ART35.2": (
        "What criteria or screening process do you use to determine whether a DPIA is required before new processing begins?",
        "Look for a DPIA screening checklist based on Art 35(3) criteria and supervisory authority lists.",
    ),
    "GDPR.ART36.1": (
        "Has your organisation ever needed to consult a supervisory authority following a DPIA, and what was the process?",
        "Prior consultation is required when high risk remains after mitigation. Check for escalation criteria and authority contact procedures.",
    ),
    "GDPR.ART37.1": (
        "On what basis was the decision made to appoint (or not appoint) a DPO, and is the assessment documented?",
        "Mandatory for public authorities, large-scale monitoring, and large-scale special category processing. Voluntary appointment is encouraged.",
    ),
    "GDPR.ART38.1": (
        "How is the DPO's independence ensured — do they report directly to senior management and are they free from conflicts of interest?",
        "Check reporting line, absence of instructions on task performance, protection from dismissal, and adequate resources.",
    ),
    "GDPR.ART39.1": (
        "How does the DPO practically fulfil their advisory, monitoring, and contact-point responsibilities on a day-to-day basis?",
        "Look for evidence of DPO involvement in DPIAs, training programmes, compliance monitoring, and supervisory authority liaison.",
    ),
    "GDPR.ART5C.1": (
        "How does your organisation assess whether the personal data collected for each purpose is truly necessary and not excessive?",
        "Look for data mapping exercises, field-level justification, and periodic reviews of data collected vs. actually used.",
    ),
    "GDPR.ART5E.1": (
        "Do you have documented retention schedules, and how is automated or manual deletion/anonymisation triggered when retention periods expire?",
        "Check for a retention schedule linked to processing purposes, automated deletion jobs, and exception handling.",
    ),
    "GDPR.ART5D.1": (
        "What processes ensure personal data remains accurate and up to date, and how are inaccuracies detected and corrected?",
        "Look for data quality checks, user self-service updates, periodic verification processes, and accuracy KPIs.",
    ),
    # Domain 4 — Processor & Transfers
    "GDPR.ART28.1": (
        "What due diligence do you perform on processors before engagement, and how do you verify their data protection capabilities?",
        "Check for a processor assessment questionnaire, certification reviews (ISO 27001, SOC 2), and ongoing monitoring.",
    ),
    "GDPR.ART28.2": (
        "Do your data processing agreements contain all mandatory Art 28(3) clauses, and when were they last reviewed?",
        "Mandatory clauses: instructions, confidentiality, security, sub-processors, data subject rights assistance, audit rights, deletion/return.",
    ),
    "GDPR.ART28.3": (
        "How are sub-processors managed — do you maintain a register and have a process for authorizing or objecting to new sub-processors?",
        "Check for sub-processor registers, notification procedures, and contractual flow-down of GDPR obligations.",
    ),
    "GDPR.ART44.1": (
        "How does your organisation identify and govern all international data transfers, including those via cloud services or remote access?",
        "Data mapping should identify all transfers outside the EEA, including indirect transfers (e.g., cloud hosting, support teams).",
    ),
    "GDPR.ART45.1": (
        "For transfers to countries with adequacy decisions, how do you monitor whether the adequacy status remains valid?",
        "The Commission periodically reviews adequacy decisions. Check awareness of the current list and any changes.",
    ),
    "GDPR.ART46.1": (
        "How were your standard contractual clauses implemented, and have you conducted transfer impact assessments for high-risk destinations?",
        "Post-Schrems II, SCCs alone may be insufficient. Transfer impact assessments evaluate the legal framework in the recipient country.",
    ),
    "GDPR.ART47.1": (
        "If your organisation uses binding corporate rules, how was approval obtained and how are they enforced across the group?",
        "BCRs require supervisory authority approval and must be legally binding and enforceable throughout the corporate group.",
    ),
    "GDPR.ART49.1": (
        "Under what circumstances does your organisation rely on derogations for transfers, and how is the strict interpretation requirement met?",
        "Derogations should be exceptional and not used for systematic transfers. Check for documentation of necessity assessments.",
    ),
    # Domain 5 — Security & Breach
    "GDPR.ART32.1": (
        "How did your organisation determine the 'appropriate' level of security, and what risk assessment methodology was used?",
        "Art 32 requires consideration of state of the art, costs, processing context, and risks. Look for a documented risk assessment.",
    ),
    "GDPR.ART32.2": (
        "Where and how are pseudonymisation and encryption applied to personal data, and what key management practices are in place?",
        "Check for encryption at rest and in transit, pseudonymisation techniques (tokenisation, hashing), and key management procedures.",
    ),
    "GDPR.ART32.3": (
        "What measures ensure the ongoing availability and resilience of processing systems, including disaster recovery and backup procedures?",
        "Look for backup schedules, recovery time objectives, redundancy measures, and tested business continuity plans.",
    ),
    "GDPR.ART32.4": (
        "How frequently are your security measures tested (e.g., penetration testing, vulnerability scanning), and how are findings remediated?",
        "Check for a testing schedule, remediation SLAs, and evidence that findings lead to actual improvements.",
    ),
    "GDPR.ART33.1": (
        "Walk through your breach notification process — how would you detect a breach, assess its severity, and notify the supervisory authority within 72 hours?",
        "Look for a breach response plan with escalation triggers, severity classification, notification templates, and clock-start procedures.",
    ),
    "GDPR.ART33.2": (
        "How do you document personal data breaches, including near-misses, and is this breach register regularly reviewed for trends?",
        "A breach register should capture all incidents regardless of notification obligation, with root cause analysis and trend reporting.",
    ),
    "GDPR.ART33.3": (
        "How do your processing agreements ensure processors notify you of breaches without undue delay, and has this been tested?",
        "Check for breach notification clauses in DPAs, defined notification timeframes (e.g., 24-48 hours), and tabletop exercises.",
    ),
    "GDPR.ART34.1": (
        "What criteria do you use to determine whether a breach must be communicated to affected individuals, and what channels are used?",
        "High risk to rights and freedoms triggers individual notification. Check for criteria, template communications, and channel selection.",
    ),
    # Domain 6 — Accountability & Governance
    "GDPR.ART5.1": (
        "What evidence can your organisation produce to demonstrate compliance with each GDPR principle if challenged by a supervisory authority?",
        "Accountability requires documentary evidence: policies, training records, DPIAs, processing records, audit reports, consent records.",
    ),
    "GDPR.ART24.1": (
        "What governance structures (committees, reporting lines, review cycles) are in place to ensure ongoing GDPR compliance?",
        "Look for a privacy governance framework, regular management reporting, compliance monitoring, and periodic reviews.",
    ),
    "GDPR.ART24.2": (
        "Are your data protection policies comprehensive, regularly updated, and effectively communicated to all relevant staff?",
        "Policies should cover all processing activities, be reviewed annually, and have documented staff acknowledgement.",
    ),
    "GDPR.ART31.1": (
        "Has your organisation established a process for cooperating with supervisory authority requests, and who is the designated contact?",
        "Check for a regulatory engagement procedure, designated contact point (DPO if appointed), and response SLAs.",
    ),
    "GDPR.ART27.1": (
        "If your organisation is not established in the EU, have you designated a representative and is this clearly communicated to data subjects?",
        "The representative must be established in a Member State where data subjects are located and named in privacy notices.",
    ),
}


def _build_gdpr_questions() -> dict[str, QuestionDef]:
    """Build QuestionDef instances from the question map."""
    qs: dict[str, QuestionDef] = {}
    for control_id, (question, guidance) in _GDPR_QUESTION_MAP.items():
        qs[control_id] = QuestionDef(
            control_id=control_id,
            question=question,
            guidance=guidance,
        )
    return qs


_GDPR_QUESTIONS = _build_gdpr_questions()

# ── Red flag patterns ───────────────────────────────────────────────────

_GDPR_RED_FLAGS = [
    RedFlagPattern(
        pattern="Consent used as a default lawful basis",
        description="Organisation relies on consent for all processing without considering more appropriate bases (contract, legitimate interest), suggesting a superficial lawful basis analysis.",
        severity="high",
    ),
    RedFlagPattern(
        pattern="Privacy notices not updated since pre-GDPR",
        description="Privacy notices reference the Data Protection Directive (95/46/EC), lack Art 13/14 mandatory elements, or have not been reviewed since May 2018.",
        severity="high",
    ),
    RedFlagPattern(
        pattern="No records of processing activities",
        description="Organisation cannot produce a RoPA or has only a partial inventory, indicating fundamental accountability gaps.",
        severity="high",
    ),
    RedFlagPattern(
        pattern="International transfers without documented safeguards",
        description="Personal data is transferred outside the EEA (e.g., via US cloud providers) without documented SCCs, adequacy reliance, or transfer impact assessments.",
        severity="high",
    ),
    RedFlagPattern(
        pattern="Breach response plan untested or missing",
        description="No documented breach response procedure, or the 72-hour notification timeline has never been rehearsed through tabletop exercises.",
        severity="medium",
    ),
    RedFlagPattern(
        pattern="Data subject rights requests handled ad hoc",
        description="No formal process for handling access, erasure, or portability requests — responses are inconsistent or exceed statutory deadlines.",
        severity="medium",
    ),
]

# ── Framework definition ────────────────────────────────────────────────

GDPR_DEFINITION = FrameworkDefinition(
    id="gdpr",
    name="GDPR",
    version="2016/679",
    description="General Data Protection Regulation (EU) 2016/679 — comprehensive data protection framework for EU/EEA personal data processing",
    domains={
        "lawfulness_transparency": _LAWFULNESS_TRANSPARENCY,
        "data_subject_rights": _DATA_SUBJECT_RIGHTS,
        "controller_obligations": _CONTROLLER_OBLIGATIONS,
        "processor_transfers": _PROCESSOR_TRANSFERS,
        "security_breach": _SECURITY_BREACH,
        "accountability_governance": _ACCOUNTABILITY_GOVERNANCE,
    },
    dependencies=_GDPR_DEPENDENCIES,
    root_cause_clusters=_GDPR_ROOT_CAUSE_CLUSTERS,
    scope_questions=_GDPR_SCOPE_QUESTIONS,
    questions=_GDPR_QUESTIONS,
    red_flag_patterns=_GDPR_RED_FLAGS,
)
