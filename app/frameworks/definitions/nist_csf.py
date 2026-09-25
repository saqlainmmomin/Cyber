"""
NIST Cybersecurity Framework (CSF) 2.0 definition.

Covers the complete CSF 2.0 Core (NIST CSWP 29, February 2024, Appendix A):
106 subcategories across 6 functions and 22 categories.
  - Govern (31)   - Identify (21)   - Protect (22)
  - Detect (11)   - Respond (13)    - Recover (8)

Ids follow NIST.<FUNCTION>.<CATEGORY>.<NN>; `reference` carries the CSF
identifier (e.g. GV.RM-05). Gaps in numbering are CSF 2.0's own (subcategories
relocated from CSF 1.1). Titles and descriptions are the pack's own wording and
reference the CSF outcome rather than reproduce it.
"""

from app.frameworks.schema import (
    Control,
    Domain,
    EvidenceRequest,
    FrameworkDefinition,
    QuestionDef,
    RedFlagPattern,
    ScopeQuestion,
    Section,
)

# ── Domain 1: GOVERN (GV) ──────────────────────────────────────────────────
# NEW in CSF 2.0 — establishes and monitors cybersecurity risk management
# strategy, expectations, and policy.

_GV_OC = Section(
    key="gv_oc",
    title="Organizational Context",
    weight=0.20,
    controls=[
        Control(
            id="NIST.GV.OC.01",
            title="Organizational mission understanding",
            description="The organizational mission is understood and informs cybersecurity risk management.",
            reference="GV.OC-01",
            criticality="high",
            tags=["governance", "mission", "risk-context"],
        ),
        Control(
            id="NIST.GV.OC.02",
            title="Internal and external stakeholders",
            description="Internal and external stakeholders are understood, and their needs and expectations about cybersecurity risk management are understood and taken into account.",
            reference="GV.OC-02",
            criticality="medium",
            tags=["governance", "stakeholders", "requirements"],
        ),
        Control(
            id="NIST.GV.OC.03",
            title="Legal and regulatory requirements",
            description="Legal, regulatory, and contractual requirements regarding cybersecurity — including privacy and civil liberties obligations — are understood and managed.",
            reference="GV.OC-03",
            criticality="critical",
            tags=["governance", "compliance", "legal-requirements", "regulatory"],
        ),
        Control(
            id="NIST.GV.OC.04",
            title="Critical objectives and dependencies",
            description="Critical objectives, capabilities and services that external stakeholders rely on or expect from the organization are understood and communicated.",
            reference="GV.OC-04",
            criticality="high",
            tags=["governance", "critical-services", "dependencies", "business-impact"],
        ),
        Control(
            id="NIST.GV.OC.05",
            title="Organizational dependencies",
            description="The outcomes, capabilities and services that the organization itself relies on are understood and communicated.",
            reference="GV.OC-05",
            criticality="medium",
            tags=["governance", "priorities", "risk-appetite"],
        ),
    ],
)

_GV_RM = Section(
    key="gv_rm",
    title="Risk Management Strategy",
    weight=0.20,
    controls=[
        Control(
            id="NIST.GV.RM.01",
            title="Risk management objectives",
            description="Risk management objectives are established and agreed to by organizational stakeholders.",
            reference="GV.RM-01",
            criticality="critical",
            tags=["governance", "risk-management", "strategy"],
        ),
        Control(
            id="NIST.GV.RM.02",
            title="Risk appetite and tolerance",
            description="Risk appetite and risk tolerance statements are established, communicated, and maintained.",
            reference="GV.RM-02",
            criticality="high",
            tags=["governance", "risk-appetite", "risk-tolerance"],
        ),
        Control(
            id="NIST.GV.RM.03",
            title="Risk management activities",
            description="Cybersecurity risk management activities and outcomes are included in enterprise risk management processes.",
            reference="GV.RM-03",
            criticality="high",
            tags=["governance", "enterprise-risk", "integration"],
        ),
        Control(
            id="NIST.GV.RM.04",
            title="Strategic risk direction",
            description="Strategic direction that describes appropriate risk response options is established and communicated.",
            reference="GV.RM-04",
            criticality="medium",
            tags=["governance", "risk-response", "strategy"],
        ),
        Control(
            id="NIST.GV.RM.05",
            title="Risk communication lines",
            description="Defined channels exist across the organization for raising and escalating cybersecurity risk, including risk that originates with suppliers and other third parties.",
            reference="GV.RM-05",
            criticality="medium",
            tags=["governance", "risk-communication", "escalation", "third-party"],
        ),
        Control(
            id="NIST.GV.RM.06",
            title="Standardized risk method",
            description="Cybersecurity risks are calculated, recorded, categorized and prioritized using one documented method that is shared across the organization.",
            reference="GV.RM-06",
            criticality="high",
            tags=["governance", "risk-methodology", "risk-scoring", "prioritization"],
        ),
        Control(
            id="NIST.GV.RM.07",
            title="Positive risk consideration",
            description="Opportunities (positive risks) are described and brought into the organization's cybersecurity risk discussions alongside threats.",
            reference="GV.RM-07",
            criticality="low",
            tags=["governance", "risk-management", "opportunities"],
        ),
    ],
)

_GV_RR = Section(
    key="gv_rr",
    title="Roles, Responsibilities & Authorities",
    weight=0.15,
    controls=[
        Control(
            id="NIST.GV.RR.01",
            title="Organizational leadership responsibility",
            description="Leaders own and answer for cybersecurity risk, and build a culture that is risk-aware, ethical and committed to continual improvement.",
            reference="GV.RR-01",
            criticality="critical",
            tags=["governance", "leadership", "accountability", "culture"],
        ),
        Control(
            id="NIST.GV.RR.02",
            title="Cybersecurity roles and responsibilities",
            description="Roles, responsibilities, and authorities related to cybersecurity risk management are established, communicated, understood, and enforced.",
            reference="GV.RR-02",
            criticality="high",
            tags=["governance", "roles-responsibilities", "organizational-structure"],
        ),
        Control(
            id="NIST.GV.RR.03",
            title="Adequate resourcing",
            description="Adequate resources are allocated commensurate with the cybersecurity risk strategy, roles, responsibilities, and policies.",
            reference="GV.RR-03",
            criticality="high",
            tags=["governance", "resourcing", "budget", "capability"],
        ),
        Control(
            id="NIST.GV.RR.04",
            title="Cybersecurity in HR practices",
            description="Cybersecurity is included in human resources practices.",
            reference="GV.RR-04",
            criticality="medium",
            tags=["governance", "human-resources", "people", "employment-lifecycle"],
        ),
    ],
)

_GV_PO = Section(
    key="gv_po",
    title="Policy",
    weight=0.15,
    controls=[
        Control(
            id="NIST.GV.PO.01",
            title="Cybersecurity policy",
            description="A policy for managing cybersecurity risks is established based on organizational context, cybersecurity strategy, and priorities and is communicated and enforced.",
            reference="GV.PO-01",
            criticality="critical",
            tags=["governance", "policy", "cybersecurity-strategy"],
        ),
        Control(
            id="NIST.GV.PO.02",
            title="Policy review and update",
            description="Policy is reviewed, updated, communicated, and enforced to reflect changes in requirements, threats, technology, and organizational mission.",
            reference="GV.PO-02",
            criticality="high",
            tags=["governance", "policy", "review", "continuous-improvement"],
        ),
    ],
)

_GV_OV = Section(
    key="gv_ov",
    title="Oversight",
    weight=0.10,
    controls=[
        Control(
            id="NIST.GV.OV.01",
            title="Risk management strategy review",
            description="Cybersecurity risk management strategy outcomes are reviewed to inform and adjust strategy and direction.",
            reference="GV.OV-01",
            criticality="high",
            tags=["governance", "oversight", "review", "strategic-alignment"],
        ),
        Control(
            id="NIST.GV.OV.02",
            title="Risk strategy coverage review",
            description="The cybersecurity risk management strategy is reviewed and adjusted to ensure coverage of organizational requirements and risks.",
            reference="GV.OV-02",
            criticality="medium",
            tags=["governance", "oversight", "strategy-review"],
        ),
        Control(
            id="NIST.GV.OV.03",
            title="Risk management performance evaluation",
            description="The performance of organizational cybersecurity risk management is evaluated and reviewed to identify adjustments that are needed.",
            reference="GV.OV-03",
            criticality="medium",
            tags=["governance", "oversight", "performance-measurement"],
        ),
    ],
)

_GV_SC = Section(
    key="gv_sc",
    title="Supply Chain Risk Management",
    weight=0.20,
    controls=[
        Control(
            id="NIST.GV.SC.01",
            title="Supply chain risk management program",
            description="A cybersecurity supply chain risk management program, strategy, objectives, policies, and processes are established and agreed to by organizational stakeholders.",
            reference="GV.SC-01",
            criticality="high",
            tags=["supply-chain", "third-party", "program", "governance"],
        ),
        Control(
            id="NIST.GV.SC.02",
            title="Supply chain roles and responsibilities",
            description="Cybersecurity roles and responsibilities for suppliers, customers, and partners are established, communicated, and coordinated internally and externally.",
            reference="GV.SC-02",
            criticality="high",
            tags=["supply-chain", "third-party", "roles-responsibilities"],
        ),
        Control(
            id="NIST.GV.SC.03",
            title="Supply chain integration",
            description="Cybersecurity supply chain risk management is integrated into cybersecurity and enterprise risk management, risk assessment, and improvement processes.",
            reference="GV.SC-03",
            criticality="medium",
            tags=["supply-chain", "integration", "enterprise-risk"],
        ),
        Control(
            id="NIST.GV.SC.04",
            title="Supplier criticality prioritization",
            description="Suppliers are known and prioritized by criticality.",
            reference="GV.SC-04",
            criticality="high",
            tags=["supply-chain", "supplier-assessment", "criticality"],
        ),
        Control(
            id="NIST.GV.SC.05",
            title="Supply chain requirements in contracts",
            description="Requirements to address cybersecurity risks in supply chains are established, prioritized, and integrated into contracts and other types of agreements with suppliers and other relevant third parties.",
            reference="GV.SC-05",
            criticality="high",
            tags=["supply-chain", "contracts", "third-party", "due-diligence"],
        ),
        Control(
            id="NIST.GV.SC.06",
            title="Supplier pre-engagement due diligence",
            description="Before a formal relationship with a supplier or other third party begins, the organization plans for it and performs due diligence to reduce the associated risk.",
            reference="GV.SC-06",
            criticality="high",
            tags=["supply-chain", "due-diligence", "onboarding", "third-party"],
        ),
        Control(
            id="NIST.GV.SC.07",
            title="Supplier risk management over the relationship",
            description="Risks from each supplier, its products and services, and other third parties are identified, recorded, prioritized, assessed, treated and monitored for as long as the relationship lasts.",
            reference="GV.SC-07",
            criticality="high",
            tags=["supply-chain", "third-party", "supplier-monitoring", "risk-assessment"],
        ),
        Control(
            id="NIST.GV.SC.08",
            title="Suppliers in incident planning and recovery",
            description="Relevant suppliers and other third parties take part in the organization's incident planning, response and recovery activities.",
            reference="GV.SC-08",
            criticality="medium",
            tags=["supply-chain", "incident-response", "recovery", "third-party"],
        ),
        Control(
            id="NIST.GV.SC.09",
            title="Supply chain security across the life cycle",
            description="Supply chain security practices form part of the cybersecurity and enterprise risk programs, and how well they perform is monitored across the life cycle of technology products and services.",
            reference="GV.SC-09",
            criticality="medium",
            tags=["supply-chain", "lifecycle-management", "performance-monitoring"],
        ),
        Control(
            id="NIST.GV.SC.10",
            title="Supplier exit provisions",
            description="Supply chain risk management plans cover what must happen when a partnership or service agreement ends.",
            reference="GV.SC-10",
            criticality="medium",
            tags=["supply-chain", "offboarding", "contracts", "termination"],
        ),
    ],
)

# ── Domain 2: IDENTIFY (ID) ─────────────────────────────────────────────────

_ID_AM = Section(
    key="id_am",
    title="Asset Management",
    weight=0.35,
    controls=[
        Control(
            id="NIST.ID.AM.01",
            title="Hardware asset inventory",
            description="Inventories of hardware managed by the organization are maintained.",
            reference="ID.AM-01",
            criticality="high",
            tags=["asset-management", "hardware", "inventory"],
        ),
        Control(
            id="NIST.ID.AM.02",
            title="Software asset inventory",
            description="Inventories of software, services, and systems managed by the organization are maintained.",
            reference="ID.AM-02",
            criticality="high",
            tags=["asset-management", "software", "inventory"],
        ),
        Control(
            id="NIST.ID.AM.03",
            title="Network communication mapping",
            description="Representations of the organization's authorized network communication and internal and external network data flows are maintained.",
            reference="ID.AM-03",
            criticality="medium",
            tags=["asset-management", "network", "data-flow", "mapping"],
        ),
        Control(
            id="NIST.ID.AM.04",
            title="External service inventory",
            description="Inventories of services provided by suppliers are maintained.",
            reference="ID.AM-04",
            criticality="medium",
            tags=["asset-management", "third-party", "services", "inventory"],
        ),
        Control(
            id="NIST.ID.AM.05",
            title="Asset prioritization",
            description="Assets are prioritized based on classification, criticality, resources, and impact on the mission.",
            reference="ID.AM-05",
            criticality="high",
            tags=["asset-management", "classification", "criticality", "prioritization"],
        ),
        Control(
            id="NIST.ID.AM.07",
            title="Data inventory and classification",
            description="Inventories of data and corresponding metadata for designated data types are maintained.",
            reference="ID.AM-07",
            criticality="high",
            tags=["asset-management", "data-inventory", "classification", "data-governance"],
        ),
        Control(
            id="NIST.ID.AM.08",
            title="Asset life-cycle management",
            description="Systems, hardware, software, services, and data are managed throughout their life cycles.",
            reference="ID.AM-08",
            criticality="medium",
            tags=["asset-management", "lifecycle-management", "decommissioning"],
        ),
    ],
)

_ID_RA = Section(
    key="id_ra",
    title="Risk Assessment",
    weight=0.40,
    controls=[
        Control(
            id="NIST.ID.RA.01",
            title="Vulnerability identification",
            description="Vulnerabilities in assets are identified, validated, and recorded.",
            reference="ID.RA-01",
            criticality="critical",
            tags=["risk-assessment", "vulnerability-management", "scanning"],
        ),
        Control(
            id="NIST.ID.RA.02",
            title="Threat intelligence receipt",
            description="Cyber threat intelligence is received from information sharing forums and sources.",
            reference="ID.RA-02",
            criticality="medium",
            tags=["risk-assessment", "threat-intelligence", "information-sharing"],
        ),
        Control(
            id="NIST.ID.RA.03",
            title="Threat identification",
            description="Internal and external threats to the organization are identified and recorded.",
            reference="ID.RA-03",
            criticality="high",
            tags=["risk-assessment", "threat-identification", "threat-modeling"],
        ),
        Control(
            id="NIST.ID.RA.04",
            title="Impact and likelihood assessment",
            description="Potential impacts and likelihoods of threats exploiting vulnerabilities are identified and recorded.",
            reference="ID.RA-04",
            criticality="high",
            tags=["risk-assessment", "impact-analysis", "likelihood", "risk-scoring"],
        ),
        Control(
            id="NIST.ID.RA.05",
            title="Risk determination",
            description="Threats, vulnerabilities, likelihoods, and impacts are used to understand inherent risk and inform risk response prioritization.",
            reference="ID.RA-05",
            criticality="critical",
            tags=["risk-assessment", "risk-determination", "prioritization"],
        ),
        Control(
            id="NIST.ID.RA.06",
            title="Risk response selection",
            description="Risk responses are chosen, prioritized, planned, tracked, and communicated.",
            reference="ID.RA-06",
            criticality="high",
            tags=["risk-assessment", "risk-response", "risk-treatment"],
        ),
        Control(
            id="NIST.ID.RA.07",
            title="Change and exception management",
            description="Changes and exceptions are controlled, evaluated for their effect on risk, recorded and tracked to closure.",
            reference="ID.RA-07",
            criticality="high",
            tags=["risk-assessment", "change-management", "exceptions", "risk-acceptance"],
        ),
        Control(
            id="NIST.ID.RA.08",
            title="Vulnerability disclosure handling",
            description="Established processes exist to receive, analyze and respond to vulnerabilities reported to the organization.",
            reference="ID.RA-08",
            criticality="medium",
            tags=["risk-assessment", "vulnerability-disclosure", "vulnerability-management"],
        ),
        Control(
            id="NIST.ID.RA.09",
            title="Hardware and software integrity verification",
            description="Hardware and software are checked for authenticity and integrity before they are acquired and put into use.",
            reference="ID.RA-09",
            criticality="medium",
            tags=["risk-assessment", "integrity", "authenticity", "acquisition"],
        ),
        Control(
            id="NIST.ID.RA.10",
            title="Critical supplier pre-acquisition assessment",
            description="Suppliers judged critical are assessed before their products or services are acquired.",
            reference="ID.RA-10",
            criticality="high",
            tags=["risk-assessment", "supply-chain", "critical-suppliers", "acquisition"],
        ),
    ],
)

_ID_IM = Section(
    key="id_im",
    title="Improvement",
    weight=0.25,
    controls=[
        Control(
            id="NIST.ID.IM.01",
            title="Improvement from evaluations",
            description="Improvements are identified from evaluations.",
            reference="ID.IM-01",
            criticality="medium",
            tags=["improvement", "evaluation", "continuous-improvement"],
        ),
        Control(
            id="NIST.ID.IM.02",
            title="Improvement from testing",
            description="Improvements are identified from security tests and exercises, including those done in coordination with suppliers and relevant third parties.",
            reference="ID.IM-02",
            criticality="medium",
            tags=["improvement", "testing", "exercises", "tabletop"],
        ),
        Control(
            id="NIST.ID.IM.03",
            title="Improvement from execution",
            description="Improvements are identified from execution of operational processes, procedures, and activities.",
            reference="ID.IM-03",
            criticality="medium",
            tags=["improvement", "operational-feedback", "process-optimization"],
        ),
        Control(
            id="NIST.ID.IM.04",
            title="Incident response and operational cyber plans",
            description="Incident response plans and other cybersecurity plans that affect operations exist and are communicated, kept current and improved.",
            reference="ID.IM-04",
            criticality="critical",
            tags=["improvement", "incident-response-plan", "planning", "business-continuity"],
        ),
    ],
)

# ── Domain 3: PROTECT (PR) ──────────────────────────────────────────────────

_PR_AA = Section(
    key="pr_aa",
    title="Identity Management, Authentication & Access Control",
    weight=0.25,
    controls=[
        Control(
            id="NIST.PR.AA.01",
            title="Identity and credential management",
            description="Identities and credentials for authorized users, services, and hardware are managed by the organization.",
            reference="PR.AA-01",
            criticality="critical",
            tags=["access-control", "identity-management", "credentials"],
        ),
        Control(
            id="NIST.PR.AA.02",
            title="Identity proofing",
            description="Identities are proofed and bound to credentials based on the context of interactions.",
            reference="PR.AA-02",
            criticality="high",
            tags=["access-control", "identity-proofing", "authentication"],
        ),
        Control(
            id="NIST.PR.AA.03",
            title="Authentication",
            description="Users, services, and hardware are authenticated.",
            reference="PR.AA-03",
            criticality="critical",
            tags=["access-control", "authentication", "mfa"],
        ),
        Control(
            id="NIST.PR.AA.04",
            title="Identity assertions",
            description="Identity assertions are protected, conveyed, and verified.",
            reference="PR.AA-04",
            criticality="high",
            tags=["access-control", "identity-assertions", "federation"],
        ),
        Control(
            id="NIST.PR.AA.05",
            title="Access permissions and authorizations",
            description="Access permissions, entitlements, and authorizations are defined in a policy, managed, enforced, and reviewed, and incorporate the principles of least privilege and separation of duties.",
            reference="PR.AA-05",
            criticality="critical",
            tags=["access-control", "least-privilege", "separation-of-duties", "authorization"],
        ),
        Control(
            id="NIST.PR.AA.06",
            title="Physical access management",
            description="Physical access to assets is managed, monitored, and enforced commensurate with risk.",
            reference="PR.AA-06",
            criticality="high",
            tags=["access-control", "physical-security", "physical-access"],
        ),
    ],
)

_PR_AT = Section(
    key="pr_at",
    title="Awareness & Training",
    weight=0.15,
    controls=[
        Control(
            id="NIST.PR.AT.01",
            title="Security awareness",
            description="Personnel are provided with awareness and training so that they possess the knowledge and skills to perform general tasks with cybersecurity risks in mind.",
            reference="PR.AT-01",
            criticality="high",
            tags=["awareness", "training", "security-culture"],
        ),
        Control(
            id="NIST.PR.AT.02",
            title="Specialized role training",
            description="Individuals in specialized roles are provided with awareness and training so that they possess the knowledge and skills to perform relevant tasks with cybersecurity risks in mind.",
            reference="PR.AT-02",
            criticality="high",
            tags=["awareness", "training", "privileged-users", "specialized-roles"],
        ),
    ],
)

_PR_DS = Section(
    key="pr_ds",
    title="Data Security",
    weight=0.25,
    controls=[
        Control(
            id="NIST.PR.DS.01",
            title="Data-at-rest protection",
            description="The confidentiality, integrity, and availability of data-at-rest are protected.",
            reference="PR.DS-01",
            criticality="critical",
            tags=["data-security", "encryption", "data-at-rest", "confidentiality"],
        ),
        Control(
            id="NIST.PR.DS.02",
            title="Data-in-transit protection",
            description="The confidentiality, integrity, and availability of data-in-transit are protected.",
            reference="PR.DS-02",
            criticality="critical",
            tags=["data-security", "encryption", "data-in-transit", "tls"],
        ),
        Control(
            id="NIST.PR.DS.10",
            title="Data-in-use protection",
            description="The confidentiality, integrity, and availability of data-in-use are protected.",
            reference="PR.DS-10",
            criticality="high",
            tags=["data-security", "data-in-use", "memory-protection"],
        ),
        Control(
            id="NIST.PR.DS.11",
            title="Backup management",
            description="Backups of data are created, protected, maintained, and tested.",
            reference="PR.DS-11",
            criticality="high",
            tags=["data-security", "backup", "recovery", "business-continuity"],
        ),
    ],
)

_PR_PS = Section(
    key="pr_ps",
    title="Platform Security",
    weight=0.20,
    controls=[
        Control(
            id="NIST.PR.PS.01",
            title="Configuration management practices",
            description="Configuration management practices are defined and applied across the organization's hardware, software and platforms.",
            reference="PR.PS-01",
            criticality="high",
            tags=["platform-security", "configuration-management", "hardening"],
        ),
        Control(
            id="NIST.PR.PS.02",
            title="Software maintenance",
            description="Software is maintained, replaced, and removed commensurate with risk.",
            reference="PR.PS-02",
            criticality="high",
            tags=["platform-security", "patching", "software-lifecycle"],
        ),
        Control(
            id="NIST.PR.PS.03",
            title="Hardware maintenance",
            description="Hardware is maintained, replaced, and removed commensurate with risk.",
            reference="PR.PS-03",
            criticality="medium",
            tags=["platform-security", "hardware-lifecycle", "maintenance"],
        ),
        Control(
            id="NIST.PR.PS.04",
            title="Log record generation",
            description="Log records are generated and made available for continuous monitoring.",
            reference="PR.PS-04",
            criticality="high",
            tags=["platform-security", "logging", "monitoring", "audit-trail"],
        ),
        Control(
            id="NIST.PR.PS.05",
            title="Installation and execution prevention",
            description="Installation and execution of unauthorized software is prevented.",
            reference="PR.PS-05",
            criticality="high",
            tags=["platform-security", "application-whitelisting", "endpoint-security"],
        ),
        Control(
            id="NIST.PR.PS.06",
            title="Secure software development",
            description="Secure software development practices are integrated, and their performance is monitored throughout the software development life cycle.",
            reference="PR.PS-06",
            criticality="high",
            tags=["platform-security", "sdlc", "secure-development"],
        ),
    ],
)

_PR_IR = Section(
    key="pr_ir",
    title="Technology Infrastructure Resilience",
    weight=0.15,
    controls=[
        Control(
            id="NIST.PR.IR.01",
            title="Network and environment protection",
            description="Networks and environments are protected from unauthorized logical access and usage.",
            reference="PR.IR-01",
            criticality="critical",
            tags=["resilience", "network-security", "segmentation", "firewall"],
        ),
        Control(
            id="NIST.PR.IR.02",
            title="Environmental threat protection",
            description="The organization's technology assets are protected from environmental threats.",
            reference="PR.IR-02",
            criticality="medium",
            tags=["resilience", "environmental-protection", "physical-security"],
        ),
        Control(
            id="NIST.PR.IR.03",
            title="Resilience mechanisms",
            description="Mechanisms are implemented to achieve resilience requirements in normal and adverse situations.",
            reference="PR.IR-03",
            criticality="high",
            tags=["resilience", "redundancy", "availability", "business-continuity"],
        ),
        Control(
            id="NIST.PR.IR.04",
            title="Adequate resource capacity",
            description="Adequate resource capacity to ensure availability is maintained.",
            reference="PR.IR-04",
            criticality="medium",
            tags=["resilience", "capacity-management", "availability"],
        ),
    ],
)

# ── Domain 4: DETECT (DE) ───────────────────────────────────────────────────

_DE_CM = Section(
    key="de_cm",
    title="Continuous Monitoring",
    weight=0.55,
    controls=[
        Control(
            id="NIST.DE.CM.01",
            title="Network monitoring",
            description="Networks and network services are monitored to find potentially adverse events.",
            reference="DE.CM-01",
            criticality="critical",
            tags=["detection", "network-monitoring", "ids-ips"],
        ),
        Control(
            id="NIST.DE.CM.02",
            title="Physical environment monitoring",
            description="The physical environment is monitored to find potentially adverse events.",
            reference="DE.CM-02",
            criticality="medium",
            tags=["detection", "physical-monitoring", "surveillance"],
        ),
        Control(
            id="NIST.DE.CM.03",
            title="Personnel activity monitoring",
            description="Personnel activity and technology usage are monitored to find potentially adverse events.",
            reference="DE.CM-03",
            criticality="high",
            tags=["detection", "user-monitoring", "insider-threat", "ueba"],
        ),
        Control(
            id="NIST.DE.CM.06",
            title="External service provider monitoring",
            description="External service provider activities and services are monitored to find potentially adverse events.",
            reference="DE.CM-06",
            criticality="high",
            tags=["detection", "third-party-monitoring", "supply-chain"],
        ),
        Control(
            id="NIST.DE.CM.09",
            title="Computing hardware and software monitoring",
            description="Computing hardware and software, runtime environments, and their data are monitored to find potentially adverse events.",
            reference="DE.CM-09",
            criticality="critical",
            tags=["detection", "endpoint-monitoring", "edr", "runtime-monitoring"],
        ),
    ],
)

_DE_AE = Section(
    key="de_ae",
    title="Adverse Event Analysis",
    weight=0.45,
    controls=[
        Control(
            id="NIST.DE.AE.02",
            title="Adverse event analysis",
            description="Potentially adverse events are analyzed to better understand associated activities.",
            reference="DE.AE-02",
            criticality="high",
            tags=["detection", "event-analysis", "siem"],
        ),
        Control(
            id="NIST.DE.AE.03",
            title="Event correlation",
            description="Information is correlated from multiple sources.",
            reference="DE.AE-03",
            criticality="high",
            tags=["detection", "correlation", "log-correlation"],
        ),
        Control(
            id="NIST.DE.AE.04",
            title="Impact estimation",
            description="The estimated impact and scope of adverse events are understood.",
            reference="DE.AE-04",
            criticality="high",
            tags=["detection", "impact-analysis", "scope-determination"],
        ),
        Control(
            id="NIST.DE.AE.06",
            title="Adverse event information distribution",
            description="Information on adverse events is provided to authorized staff and tools.",
            reference="DE.AE-06",
            criticality="high",
            tags=["detection", "alerting", "information-distribution"],
        ),
        Control(
            id="NIST.DE.AE.07",
            title="Threat information integration",
            description="Cyber threat intelligence and other contextual information are integrated into the analysis.",
            reference="DE.AE-07",
            criticality="medium",
            tags=["detection", "threat-intelligence", "contextual-analysis"],
        ),
        Control(
            id="NIST.DE.AE.08",
            title="Incident declaration",
            description="Incidents are declared when adverse events meet the defined incident criteria.",
            reference="DE.AE-08",
            criticality="high",
            tags=["detection", "incident-declaration", "incident-criteria", "thresholds"],
        ),
    ],
)

# ── Domain 5: RESPOND (RS) ──────────────────────────────────────────────────

_RS_MA = Section(
    key="rs_ma",
    title="Incident Management",
    weight=0.30,
    controls=[
        Control(
            id="NIST.RS.MA.01",
            title="Incident response plan execution",
            description="The incident response plan is executed in coordination with relevant third parties once an incident is declared.",
            reference="RS.MA-01",
            criticality="critical",
            tags=["response", "incident-response-plan", "coordination"],
        ),
        Control(
            id="NIST.RS.MA.02",
            title="Incident triage and validation",
            description="Incident reports are triaged and validated.",
            reference="RS.MA-02",
            criticality="high",
            tags=["response", "triage", "validation", "prioritization"],
        ),
        Control(
            id="NIST.RS.MA.03",
            title="Incident categorization and prioritization",
            description="Incidents are categorized and prioritized.",
            reference="RS.MA-03",
            criticality="high",
            tags=["response", "categorization", "prioritization", "severity"],
        ),
        Control(
            id="NIST.RS.MA.04",
            title="Incident escalation",
            description="Incidents are escalated or elevated as needed.",
            reference="RS.MA-04",
            criticality="high",
            tags=["response", "escalation", "management-notification"],
        ),
        Control(
            id="NIST.RS.MA.05",
            title="Recovery initiation criteria",
            description="The criteria for initiating incident recovery are applied.",
            reference="RS.MA-05",
            criticality="medium",
            tags=["response", "recovery-criteria", "decision-making"],
        ),
    ],
)

_RS_AN = Section(
    key="rs_an",
    title="Incident Analysis",
    weight=0.25,
    controls=[
        Control(
            id="NIST.RS.AN.03",
            title="Root cause analysis",
            description="Analysis is performed to determine what has taken place during an incident and the root cause of the incident.",
            reference="RS.AN-03",
            criticality="high",
            tags=["response", "analysis", "root-cause", "forensics"],
        ),
        Control(
            id="NIST.RS.AN.06",
            title="Investigation actions",
            description="Actions performed during an investigation are recorded, and the records' integrity and provenance are preserved.",
            reference="RS.AN-06",
            criticality="medium",
            tags=["response", "investigation", "evidence-preservation", "chain-of-custody"],
        ),
        Control(
            id="NIST.RS.AN.07",
            title="Incident data collection and preservation",
            description="Incident data and metadata are collected and their integrity and provenance are preserved.",
            reference="RS.AN-07",
            criticality="high",
            tags=["response", "data-collection", "forensic-analysis", "integrity"],
        ),
        Control(
            id="NIST.RS.AN.08",
            title="Incident scope estimation",
            description="An incident's magnitude is estimated and validated.",
            reference="RS.AN-08",
            criticality="high",
            tags=["response", "scope-estimation", "impact-assessment"],
        ),
    ],
)

_RS_CO = Section(
    key="rs_co",
    title="Incident Response Reporting & Communication",
    weight=0.25,
    controls=[
        Control(
            id="NIST.RS.CO.02",
            title="Stakeholder incident notification",
            description="Internal and external stakeholders are notified of incidents.",
            reference="RS.CO-02",
            criticality="high",
            tags=["response", "communication", "internal-notification"],
        ),
        Control(
            id="NIST.RS.CO.03",
            title="Incident information sharing",
            description="Information is shared with designated internal and external stakeholders.",
            reference="RS.CO-03",
            criticality="medium",
            tags=["response", "information-sharing", "coordination"],
        ),
    ],
)

_RS_MI = Section(
    key="rs_mi",
    title="Incident Mitigation",
    weight=0.20,
    controls=[
        Control(
            id="NIST.RS.MI.01",
            title="Incident containment",
            description="Incidents are contained.",
            reference="RS.MI-01",
            criticality="critical",
            tags=["response", "containment", "isolation", "mitigation"],
        ),
        Control(
            id="NIST.RS.MI.02",
            title="Incident eradication",
            description="Incidents are eradicated.",
            reference="RS.MI-02",
            criticality="critical",
            tags=["response", "eradication", "remediation"],
        ),
    ],
)

# ── Domain 6: RECOVER (RC) ──────────────────────────────────────────────────

_RC_RP = Section(
    key="rc_rp",
    title="Incident Recovery Plan Execution",
    weight=0.55,
    controls=[
        Control(
            id="NIST.RC.RP.01",
            title="Recovery plan execution",
            description="The recovery portion of the incident response plan is executed once initiated from the incident response process.",
            reference="RC.RP-01",
            criticality="critical",
            tags=["recovery", "recovery-plan", "execution", "business-continuity"],
        ),
        Control(
            id="NIST.RC.RP.02",
            title="Recovery action selection",
            description="Recovery actions are selected, scoped, prioritized, and performed.",
            reference="RC.RP-02",
            criticality="high",
            tags=["recovery", "prioritization", "action-planning"],
        ),
        Control(
            id="NIST.RC.RP.03",
            title="Restoration asset integrity verification",
            description="The integrity of backups and other restoration assets is verified before using them for restoration.",
            reference="RC.RP-03",
            criticality="high",
            tags=["recovery", "backup-verification", "integrity", "restoration"],
        ),
        Control(
            id="NIST.RC.RP.04",
            title="Mission function consideration",
            description="Critical mission functions and cybersecurity risk management are considered to establish post-incident operational norms.",
            reference="RC.RP-04",
            criticality="high",
            tags=["recovery", "mission-functions", "operational-norms"],
        ),
        Control(
            id="NIST.RC.RP.05",
            title="Recovery completeness verification",
            description="The integrity of restored assets is verified, systems and services are restored, and normal operating status is confirmed.",
            reference="RC.RP-05",
            criticality="high",
            tags=["recovery", "verification", "restoration-validation"],
        ),
        Control(
            id="NIST.RC.RP.06",
            title="End of recovery declaration",
            description="The end of incident recovery is declared based on criteria, and incident-related documentation is completed.",
            reference="RC.RP-06",
            criticality="medium",
            tags=["recovery", "closure", "documentation", "lessons-learned"],
        ),
    ],
)

_RC_CO = Section(
    key="rc_co",
    title="Incident Recovery Communication",
    weight=0.45,
    controls=[
        Control(
            id="NIST.RC.CO.03",
            title="Recovery activity communication",
            description="Recovery activities and progress in restoring operational capabilities are communicated to designated internal and external stakeholders.",
            reference="RC.CO-03",
            criticality="high",
            tags=["recovery", "communication", "stakeholder-updates"],
        ),
        Control(
            id="NIST.RC.CO.04",
            title="Public update communication",
            description="Public updates on incident recovery are shared using approved methods and messaging.",
            reference="RC.CO-04",
            criticality="medium",
            tags=["recovery", "public-communication", "reputation-management"],
        ),
    ],
)

# ── Assemble domains ────────────────────────────────────────────────────────

_GOVERN = Domain(
    key="govern",
    title="Govern (GV)",
    weight=0.15,
    sections={
        "gv_oc": _GV_OC,
        "gv_rm": _GV_RM,
        "gv_rr": _GV_RR,
        "gv_po": _GV_PO,
        "gv_ov": _GV_OV,
        "gv_sc": _GV_SC,
    },
)

_IDENTIFY = Domain(
    key="identify",
    title="Identify (ID)",
    weight=0.15,
    sections={
        "id_am": _ID_AM,
        "id_ra": _ID_RA,
        "id_im": _ID_IM,
    },
)

_PROTECT = Domain(
    key="protect",
    title="Protect (PR)",
    weight=0.25,
    sections={
        "pr_aa": _PR_AA,
        "pr_at": _PR_AT,
        "pr_ds": _PR_DS,
        "pr_ps": _PR_PS,
        "pr_ir": _PR_IR,
    },
)

_DETECT = Domain(
    key="detect",
    title="Detect (DE)",
    weight=0.15,
    sections={
        "de_cm": _DE_CM,
        "de_ae": _DE_AE,
    },
)

_RESPOND = Domain(
    key="respond",
    title="Respond (RS)",
    weight=0.15,
    sections={
        "rs_ma": _RS_MA,
        "rs_an": _RS_AN,
        "rs_co": _RS_CO,
        "rs_mi": _RS_MI,
    },
)

_RECOVER = Domain(
    key="recover",
    title="Recover (RC)",
    weight=0.15,
    sections={
        "rc_rp": _RC_RP,
        "rc_co": _RC_CO,
    },
)

# ── Dependency DAG ──────────────────────────────────────────────────────────

_NIST_CSF_DEPENDENCIES: dict[str, list[str]] = {
    # Governance foundations must exist before operational controls
    "NIST.GV.PO.01": ["NIST.GV.OC.03", "NIST.GV.RM.01"],  # Policy needs legal context + risk objectives
    "NIST.GV.PO.02": ["NIST.GV.PO.01"],  # Policy review needs policy
    "NIST.GV.OV.01": ["NIST.GV.RM.01"],  # Oversight needs risk strategy
    "NIST.GV.SC.05": ["NIST.GV.SC.01"],  # Contract requirements need SCRM program
    "NIST.GV.SC.04": ["NIST.GV.SC.01"],  # Supplier assessment needs SCRM program
    "NIST.GV.RM.06": ["NIST.GV.RM.01"],  # Standard risk method needs risk objectives
    "NIST.GV.SC.06": ["NIST.GV.SC.01"],  # Supplier due diligence needs SCRM program
    "NIST.GV.SC.07": ["NIST.GV.SC.04"],  # Ongoing supplier risk needs supplier criticality
    "NIST.GV.SC.10": ["NIST.GV.SC.05"],  # Supplier exit needs contractual requirements
    "NIST.ID.RA.10": ["NIST.GV.SC.04"],  # Critical supplier assessment needs supplier criticality
    # Risk assessment chain
    "NIST.ID.RA.04": ["NIST.ID.RA.01", "NIST.ID.RA.03"],  # Impact/likelihood needs vulns + threats
    "NIST.ID.RA.05": ["NIST.ID.RA.04"],  # Risk determination needs impact/likelihood
    "NIST.ID.RA.06": ["NIST.ID.RA.05"],  # Risk response needs risk determination
    # Asset management feeds risk
    "NIST.ID.RA.01": ["NIST.ID.AM.01", "NIST.ID.AM.02"],  # Vuln ID needs HW/SW inventory
    # Access control chain
    "NIST.PR.AA.05": ["NIST.GV.PO.01"],  # Access permissions need policy
    "NIST.PR.AA.03": ["NIST.PR.AA.01"],  # Authentication needs identity management
    "NIST.PR.AA.04": ["NIST.PR.AA.03"],  # Identity assertions need authentication
    # Detection feeds response
    "NIST.DE.AE.04": ["NIST.DE.AE.02"],  # Impact estimation needs event analysis
    "NIST.DE.AE.08": ["NIST.DE.AE.02"],  # Incident declaration needs event analysis
    "NIST.RS.MA.01": ["NIST.DE.AE.08", "NIST.ID.IM.04"],  # IR plan execution needs incident declaration and plan
    # Response chain
    "NIST.RS.MA.03": ["NIST.RS.MA.02"],  # Categorization needs triage
    "NIST.RS.MA.04": ["NIST.RS.MA.03"],  # Escalation needs categorization
    "NIST.RS.MI.02": ["NIST.RS.MI.01"],  # Eradication needs containment
    # Recovery chain
    "NIST.RC.RP.02": ["NIST.RC.RP.01"],  # Recovery action selection needs plan execution
    "NIST.RC.RP.05": ["NIST.RC.RP.03"],  # Recovery completeness needs backup verification
    "NIST.RC.RP.06": ["NIST.RC.RP.05"],  # End of recovery needs completeness verification
    "NIST.RC.CO.03": ["NIST.RC.RP.01"],  # Recovery communication needs plan execution
}

# ── Root cause clusters ─────────────────────────────────────────────────────

_NIST_CSF_ROOT_CAUSE_CLUSTERS: dict[str, dict] = {
    "policy": {
        "title": "Cybersecurity Policy & Governance Framework",
        "description": "Develop, formalize, and communicate cybersecurity policies, risk appetite statements, and governance structures.",
        "typical_requirements": [
            "NIST.GV.PO.01", "NIST.GV.PO.02", "NIST.GV.OC.03",
            "NIST.GV.RM.01", "NIST.GV.RM.02",
        ],
    },
    "people": {
        "title": "Cybersecurity Workforce & Awareness Program",
        "description": "Train staff, establish security culture, define roles and responsibilities, and ensure adequate resourcing.",
        "typical_requirements": [
            "NIST.GV.RR.01", "NIST.GV.RR.02", "NIST.GV.RR.03",
            "NIST.GV.RR.04", "NIST.PR.AT.01", "NIST.PR.AT.02",
        ],
    },
    "process": {
        "title": "Operational Process & Risk Management Maturity",
        "description": "Establish repeatable processes for risk assessment, asset management, incident response, and recovery.",
        "typical_requirements": [
            "NIST.ID.RA.05", "NIST.ID.RA.06", "NIST.RS.MA.01",
            "NIST.RS.MA.02", "NIST.RC.RP.01", "NIST.ID.AM.05",
            "NIST.ID.IM.04", "NIST.ID.RA.07",
        ],
    },
    "technology": {
        "title": "Technical Security Controls & Infrastructure",
        "description": "Implement or upgrade technical controls including identity management, data protection, platform security, and monitoring.",
        "typical_requirements": [
            "NIST.PR.AA.01", "NIST.PR.AA.03", "NIST.PR.DS.01",
            "NIST.PR.DS.02", "NIST.PR.IR.01", "NIST.DE.CM.01",
            "NIST.DE.CM.09",
        ],
    },
    "governance": {
        "title": "Executive Oversight & Strategic Risk Alignment",
        "description": "Establish board-level oversight, integrate cybersecurity into enterprise risk management, and ensure continuous improvement.",
        "typical_requirements": [
            "NIST.GV.OC.01", "NIST.GV.OV.01", "NIST.GV.OV.02",
            "NIST.GV.RM.03", "NIST.ID.IM.01", "NIST.ID.IM.02",
        ],
    },
}

# ── Scope questions ─────────────────────────────────────────────────────────

_NIST_CSF_SCOPE_QUESTIONS = [
    ScopeQuestion(
        id="NIST.SCP.1",
        question="Is your organization part of critical infrastructure (e.g., energy, healthcare, financial services, transportation)?",
        help_text="NIST CSF was originally developed for critical infrastructure sectors. Recorded as context for the consultant; it does not change which CSF outcomes are assessed.",
        type="single_select",
        options=[
            {"value": "yes_regulated", "label": "Yes — regulated critical infrastructure sector"},
            {"value": "yes_voluntary", "label": "Yes — but CSF adoption is voluntary"},
            {"value": "no", "label": "No — not critical infrastructure"},
        ],
    ),
    ScopeQuestion(
        id="NIST.SCP.2",
        question="What is your organization's current CSF implementation tier?",
        help_text="CSF 2.0 defines 4 tiers: Partial (Tier 1), Risk Informed (Tier 2), Repeatable (Tier 3), Adaptive (Tier 4). Recorded as your self-assessed starting point for the consultant; it does not change which outcomes are assessed or how they are scored.",
        type="single_select",
        options=[
            {"value": "tier1", "label": "Tier 1 — Partial (ad-hoc, reactive)"},
            {"value": "tier2", "label": "Tier 2 — Risk Informed (some risk awareness, not org-wide)"},
            {"value": "tier3", "label": "Tier 3 — Repeatable (formal policies, org-wide)"},
            {"value": "tier4", "label": "Tier 4 — Adaptive (continuous improvement, lessons learned)"},
            {"value": "unknown", "label": "Unknown / not yet assessed"},
        ],
    ),
    ScopeQuestion(
        id="NIST.SCP.3",
        question="Does your organization manage operational technology (OT) or industrial control systems (ICS)?",
        help_text="OT/ICS environments have unique cybersecurity considerations. Recorded as context for the consultant; the CSF outcomes in this assessment are not OT-specific and all remain in scope.",
        type="single_select",
        options=[
            {"value": "yes", "label": "Yes — OT/ICS systems in scope"},
            {"value": "no", "label": "No — IT systems only"},
            {"value": "converged", "label": "Yes — converged IT/OT environment"},
        ],
    ),
    ScopeQuestion(
        id="NIST.SCP.4",
        question="Has your organization developed a CSF organizational profile (current or target)?",
        help_text="A CSF profile aligns framework outcomes with business requirements, risk tolerance, and resources.",
        type="single_select",
        options=[
            {"value": "both", "label": "Yes — both current and target profiles"},
            {"value": "current_only", "label": "Yes — current profile only"},
            {"value": "target_only", "label": "Yes — target profile only"},
            {"value": "no", "label": "No — no profile developed yet"},
        ],
    ),
]

_NIST_CSF_EVIDENCE_REQUESTS = [
    EvidenceRequest("csf_profiles", "CSF Current and Target Organizational Profiles (if developed)", "Shows which CSF outcomes you have prioritised and where you are today; used as context for every conclusion.", False),
    EvidenceRequest("risk_management_strategy", "Cybersecurity risk management strategy, including risk appetite and tolerance statements", "Evidence for organisational context (GV.OC-01, GV.OC-04, GV.OC-05) and risk management strategy, risk communication and opportunity handling (GV.RM-01 to GV.RM-05, GV.RM-07).", True, ("NIST.GV.OC.01", "NIST.GV.OC.04", "NIST.GV.OC.05", "NIST.GV.RM.01", "NIST.GV.RM.02", "NIST.GV.RM.03", "NIST.GV.RM.04", "NIST.GV.RM.05", "NIST.GV.RM.07")),
    EvidenceRequest("security_policy", "Cybersecurity policy, with evidence of periodic review", "Evidence for policy establishment and review (GV.PO-01, GV.PO-02).", True, ("NIST.GV.PO.01", "NIST.GV.PO.02")),
    EvidenceRequest("roles_responsibilities", "Cybersecurity roles, responsibilities and resourcing (organisation chart or RACI)", "Evidence for leadership accountability, roles and resourcing (GV.RR-01 to GV.RR-03).", False, ("NIST.GV.RR.01", "NIST.GV.RR.02", "NIST.GV.RR.03")),
    EvidenceRequest("hr_security", "HR security procedures (screening, onboarding, leaver process)", "Evidence for cybersecurity in human resources practices (GV.RR-04).", False, ("NIST.GV.RR.04",)),
    EvidenceRequest("leadership_oversight", "Leadership / board cybersecurity oversight reports and meeting minutes", "Evidence for oversight of the risk strategy and its performance (GV.OV-01 to GV.OV-03).", False, ("NIST.GV.OV.01", "NIST.GV.OV.02", "NIST.GV.OV.03")),
    EvidenceRequest("legal_register", "Register of legal, regulatory and contractual cybersecurity requirements", "Evidence for stakeholder and legal requirements (GV.OC-02, GV.OC-03).", False, ("NIST.GV.OC.02", "NIST.GV.OC.03")),
    EvidenceRequest("supplier_security", "Supplier security policy, supplier register and sample supplier agreements", "Evidence for supply chain risk management across the supplier life cycle (GV.SC-01 to GV.SC-10), critical-supplier assessment before acquisition (ID.RA-10), external service inventory (ID.AM-04) and provider monitoring (DE.CM-06).", True, ("NIST.GV.SC.01", "NIST.GV.SC.02", "NIST.GV.SC.03", "NIST.GV.SC.04", "NIST.GV.SC.05", "NIST.GV.SC.06", "NIST.GV.SC.07", "NIST.GV.SC.08", "NIST.GV.SC.09", "NIST.GV.SC.10", "NIST.ID.RA.10", "NIST.ID.AM.04", "NIST.DE.CM.06")),
    EvidenceRequest("asset_inventory", "Hardware, software and data inventories, with classification", "Evidence for asset management (ID.AM-01, ID.AM-02, ID.AM-05, ID.AM-07, ID.AM-08).", True, ("NIST.ID.AM.01", "NIST.ID.AM.02", "NIST.ID.AM.05", "NIST.ID.AM.07", "NIST.ID.AM.08")),
    EvidenceRequest("risk_assessment", "Cybersecurity risk assessment and risk register", "Evidence for threat identification, impact and likelihood, risk determination and response (ID.RA-03 to ID.RA-06) and the organisation's standard risk method (GV.RM-06).", True, ("NIST.ID.RA.03", "NIST.ID.RA.04", "NIST.ID.RA.05", "NIST.ID.RA.06", "NIST.GV.RM.06")),
    EvidenceRequest("vulnerability_management", "Vulnerability and patch management procedure, with recent scan reports", "Evidence for vulnerability identification (ID.RA-01), threat intelligence (ID.RA-02), vulnerability disclosure handling (ID.RA-08) and software maintenance (PR.PS-02).", True, ("NIST.ID.RA.01", "NIST.ID.RA.02", "NIST.ID.RA.08", "NIST.PR.PS.02")),
    EvidenceRequest("access_control_policy", "Access control policy and recent user access review records", "Evidence for identity, authentication and access management (PR.AA-01 to PR.AA-05).", True, ("NIST.PR.AA.01", "NIST.PR.AA.02", "NIST.PR.AA.03", "NIST.PR.AA.04", "NIST.PR.AA.05")),
    EvidenceRequest("physical_security", "Physical access and environmental protection procedures", "Evidence for physical access management (PR.AA-06), physical environment monitoring (DE.CM-02) and asset protection (PR.IR-02).", False, ("NIST.PR.AA.06", "NIST.DE.CM.02", "NIST.PR.IR.02")),
    EvidenceRequest("training_records", "Security awareness training programme and completion records", "Evidence for awareness and specialised-role training (PR.AT-01, PR.AT-02).", True, ("NIST.PR.AT.01", "NIST.PR.AT.02")),
    EvidenceRequest("cryptography_policy", "Data protection and encryption standard (at rest, in transit, in use)", "Evidence for data security (PR.DS-01, PR.DS-02, PR.DS-10).", False, ("NIST.PR.DS.01", "NIST.PR.DS.02", "NIST.PR.DS.10")),
    EvidenceRequest("backup", "Backup policy and restore test records", "Evidence for backups (PR.DS-11) and recovery integrity checks (RC.RP-03).", False, ("NIST.PR.DS.11", "NIST.RC.RP.03")),
    EvidenceRequest("configuration_baselines", "Secure configuration / hardening baselines, software execution controls and integrity checks for acquired hardware and software", "Evidence for configuration management, hardware maintenance and execution prevention (PR.PS-01, PR.PS-03, PR.PS-05) and authenticity and integrity checks before hardware and software are used (ID.RA-09).", False, ("NIST.PR.PS.01", "NIST.PR.PS.03", "NIST.PR.PS.05", "NIST.ID.RA.09")),
    EvidenceRequest("change_management", "Change management procedure, sample change records and the exception (risk acceptance) register", "Evidence for change and exception management (ID.RA-07).", False, ("NIST.ID.RA.07",)),
    EvidenceRequest("sdlc_policy", "Secure software development practices", "Evidence for secure software development (PR.PS-06).", False, ("NIST.PR.PS.06",)),
    EvidenceRequest("logging_monitoring", "Logging and monitoring standard, with evidence of alert review or SIEM use", "Evidence for log generation (PR.PS-04), continuous monitoring (DE.CM-01, DE.CM-03, DE.CM-09) and adverse event analysis, correlation, distribution and threat context (DE.AE-02, DE.AE-03, DE.AE-06, DE.AE-07).", True, ("NIST.PR.PS.04", "NIST.DE.CM.01", "NIST.DE.CM.03", "NIST.DE.CM.09", "NIST.DE.AE.02", "NIST.DE.AE.03", "NIST.DE.AE.06", "NIST.DE.AE.07")),
    EvidenceRequest("network_security", "Network architecture / data flow diagram and network protection standard", "Evidence for network communication mapping (ID.AM-03) and network protection (PR.IR-01).", False, ("NIST.ID.AM.03", "NIST.PR.IR.01")),
    EvidenceRequest("breach_procedure", "Incident response plan and escalation procedures", "Evidence for the incident response plan (ID.IM-04), incident management, containment, eradication and stakeholder communication (RS.MA-01 to RS.MA-05, RS.MI-01, RS.MI-02, RS.CO-02, RS.CO-03) and incident impact and declaration (DE.AE-04, DE.AE-08).", True, ("NIST.ID.IM.04", "NIST.RS.MA.01", "NIST.RS.MA.02", "NIST.RS.MA.03", "NIST.RS.MA.04", "NIST.RS.MA.05", "NIST.RS.MI.01", "NIST.RS.MI.02", "NIST.RS.CO.02", "NIST.RS.CO.03", "NIST.DE.AE.04", "NIST.DE.AE.08")),
    EvidenceRequest("incident_log", "Incident register and post-incident reports for the last 12 months", "Evidence for incident analysis (RS.AN-03, RS.AN-06 to RS.AN-08) and improvement from execution (ID.IM-03).", False, ("NIST.RS.AN.03", "NIST.RS.AN.06", "NIST.RS.AN.07", "NIST.RS.AN.08", "NIST.ID.IM.03")),
    EvidenceRequest("business_continuity", "Recovery and business continuity plans, with latest test results", "Evidence for recovery plan execution and communication (RC.RP-01, RC.RP-02, RC.RP-04 to RC.RP-06, RC.CO-03, RC.CO-04) and resilience mechanisms and capacity (PR.IR-03, PR.IR-04).", True, ("NIST.RC.RP.01", "NIST.RC.RP.02", "NIST.RC.RP.04", "NIST.RC.RP.05", "NIST.RC.RP.06", "NIST.RC.CO.03", "NIST.RC.CO.04", "NIST.PR.IR.03", "NIST.PR.IR.04")),
    EvidenceRequest("exercise_records", "Incident response and recovery exercise / tabletop reports, with resulting improvement actions", "Evidence for improvement from evaluations and tests (ID.IM-01, ID.IM-02).", False, ("NIST.ID.IM.01", "NIST.ID.IM.02")),
]

# ── Question text ──────────────────────────────────────────────────────────
# One question per control, following the same pattern as ISO 27001

_NIST_CSF_QUESTIONS: dict[str, QuestionDef] = {}


def _generate_nist_csf_questions() -> dict[str, QuestionDef]:
    """Generate question definitions for all NIST CSF 2.0 controls."""
    qs = {}
    for domain in [_GOVERN, _IDENTIFY, _PROTECT, _DETECT, _RESPOND, _RECOVER]:
        for section in domain.sections.values():
            for ctrl in section.controls:
                qs[ctrl.id] = QuestionDef(
                    control_id=ctrl.id,
                    question=f"Has your organization implemented {ctrl.title.lower()}? ({ctrl.reference})",
                    guidance=ctrl.description,
                )
    return qs


_NIST_CSF_QUESTIONS = _generate_nist_csf_questions()

# ── Red flag patterns ──────────────────────────────────────────────────────

_NIST_CSF_RED_FLAGS = [
    RedFlagPattern(
        pattern="Govern function absence",
        description="No evidence of the Govern function (new in CSF 2.0): missing risk management strategy, undefined roles and responsibilities, no organizational context documented.",
        severity="high",
    ),
    RedFlagPattern(
        pattern="Tier mismatch with claims",
        description="Organization claims Tier 3 or 4 maturity but lacks formal, documented, and repeatable processes for risk management and incident response.",
        severity="high",
    ),
    RedFlagPattern(
        pattern="Detection without response capability",
        description="Monitoring and detection tools deployed but no defined incident response plan, escalation procedures, or designated response team.",
        severity="high",
    ),
    RedFlagPattern(
        pattern="Asset inventory gaps",
        description="Organization cannot produce current hardware, software, or data inventories, making risk assessment and vulnerability management unreliable.",
        severity="medium",
    ),
    RedFlagPattern(
        pattern="Supply chain blind spots",
        description="No supplier inventory, no cybersecurity requirements in contracts, and no monitoring of third-party services despite significant outsourcing.",
        severity="high",
    ),
    RedFlagPattern(
        pattern="Recovery plan never tested",
        description="Recovery and business continuity plans exist on paper but have never been tested through tabletop exercises or simulations.",
        severity="medium",
    ),
    RedFlagPattern(
        pattern="Profile without action",
        description="CSF profiles (current/target) have been developed but no gap analysis or roadmap exists to move from current to target state.",
        severity="medium",
    ),
]

# ── Framework definition ────────────────────────────────────────────────────

NIST_CSF_DEFINITION = FrameworkDefinition(
    id="nist_csf",
    name="NIST CSF",
    version="2.0",
    description="NIST Cybersecurity Framework (CSF) 2.0 — Risk-based approach to managing cybersecurity risk across 6 functions",
    domains={
        "govern": _GOVERN,
        "identify": _IDENTIFY,
        "protect": _PROTECT,
        "detect": _DETECT,
        "respond": _RESPOND,
        "recover": _RECOVER,
    },
    dependencies=_NIST_CSF_DEPENDENCIES,
    root_cause_clusters=_NIST_CSF_ROOT_CAUSE_CLUSTERS,
    scope_questions=_NIST_CSF_SCOPE_QUESTIONS,
    questions=_NIST_CSF_QUESTIONS,
    red_flag_patterns=_NIST_CSF_RED_FLAGS,
    evidence_requests=_NIST_CSF_EVIDENCE_REQUESTS,
)
