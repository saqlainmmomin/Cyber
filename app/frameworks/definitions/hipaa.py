"""
HIPAA framework definition.

Based on the HIPAA Security Rule (45 CFR Part 164 Subpart C), Privacy Rule
(45 CFR Part 164 Subpart E), and Breach Notification Rule (45 CFR Part 164
Subpart D), organized into 4 domains:
  - Administrative Safeguards (17 controls)
  - Physical Safeguards (8 controls)
  - Technical Safeguards (12 controls)
  - Privacy Rule Requirements (14 controls)

Total: 51 controls.
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

# ── Domain 1: Administrative Safeguards (§164.308) ─────────────────────────

_ADMIN_SECURITY_MGMT = Section(
    key="security_management",
    title="Security Management Process",
    weight=0.25,
    controls=[
        Control(
            id="HIPAA.164.308a1i",
            title="Risk analysis",
            description="Conduct an accurate and thorough assessment of the potential risks and vulnerabilities to the confidentiality, integrity, and availability of electronic protected health information (ePHI) held by the covered entity or business associate.",
            reference="§164.308(a)(1)(ii)(A)",
            criticality="critical",
            tags=["risk-assessment", "ephi", "administrative", "foundational"],
        ),
        Control(
            id="HIPAA.164.308a1ii",
            title="Risk management",
            description="Implement security measures sufficient to reduce risks and vulnerabilities to a reasonable and appropriate level to comply with the Security Rule.",
            reference="§164.308(a)(1)(ii)(B)",
            criticality="critical",
            tags=["risk-management", "security-measures", "administrative"],
        ),
        Control(
            id="HIPAA.164.308a1iii",
            title="Sanction policy",
            description="Apply appropriate sanctions against workforce members who fail to comply with the security policies and procedures of the covered entity or business associate.",
            reference="§164.308(a)(1)(ii)(C)",
            criticality="high",
            tags=["sanctions", "policy-enforcement", "workforce", "administrative"],
        ),
        Control(
            id="HIPAA.164.308a1iv",
            title="Information system activity review",
            description="Implement procedures to regularly review records of information system activity, such as audit logs, access reports, and security incident tracking reports.",
            reference="§164.308(a)(1)(ii)(D)",
            criticality="high",
            tags=["audit-logs", "monitoring", "activity-review", "administrative"],
        ),
    ],
)

_ADMIN_WORKFORCE = Section(
    key="workforce_security",
    title="Workforce Security",
    weight=0.15,
    controls=[
        Control(
            id="HIPAA.164.308a3i",
            title="Authorization and supervision",
            description="Implement procedures for the authorization and/or supervision of workforce members who work with ePHI or in locations where it might be accessed.",
            reference="§164.308(a)(3)(ii)(A)",
            criticality="high",
            tags=["authorization", "supervision", "workforce", "administrative"],
        ),
        Control(
            id="HIPAA.164.308a3ii",
            title="Workforce clearance procedure",
            description="Implement procedures to determine that the access of a workforce member to ePHI is appropriate.",
            reference="§164.308(a)(3)(ii)(B)",
            criticality="high",
            tags=["clearance", "background-check", "workforce", "administrative"],
        ),
        Control(
            id="HIPAA.164.308a3iii",
            title="Termination procedures",
            description="Implement procedures for terminating access to ePHI when the employment of, or other arrangement with, a workforce member ends.",
            reference="§164.308(a)(3)(ii)(C)",
            criticality="high",
            tags=["termination", "offboarding", "access-revocation", "administrative"],
        ),
    ],
)

_ADMIN_INFO_ACCESS = Section(
    key="information_access",
    title="Information Access Management",
    weight=0.15,
    controls=[
        Control(
            id="HIPAA.164.308a4i",
            title="Access authorization",
            description="Implement policies and procedures for granting access to ePHI, for example, through access to a workstation, transaction, program, process, or other mechanism.",
            reference="§164.308(a)(4)(ii)(B)",
            criticality="high",
            tags=["access-authorization", "ephi", "access-control", "administrative"],
        ),
        Control(
            id="HIPAA.164.308a4ii",
            title="Access establishment and modification",
            description="Implement policies and procedures that, based upon the covered entity's or business associate's access authorization policies, establish, document, review, and modify a user's right of access to a workstation, transaction, program, or process.",
            reference="§164.308(a)(4)(ii)(C)",
            criticality="high",
            tags=["access-management", "provisioning", "user-lifecycle", "administrative"],
        ),
    ],
)

_ADMIN_AWARENESS = Section(
    key="security_awareness",
    title="Security Awareness & Training",
    weight=0.15,
    controls=[
        Control(
            id="HIPAA.164.308a5i",
            title="Security awareness and training program",
            description="Implement a security awareness and training program for all members of its workforce (including management).",
            reference="§164.308(a)(5)(i)",
            criticality="critical",
            tags=["training", "awareness", "workforce", "administrative"],
        ),
        Control(
            id="HIPAA.164.308a5ii",
            title="Security reminders",
            description="Provide periodic security updates and reminders to workforce members.",
            reference="§164.308(a)(5)(ii)(A)",
            criticality="medium",
            tags=["security-reminders", "awareness", "ongoing-education", "administrative"],
        ),
        Control(
            id="HIPAA.164.308a5iii",
            title="Protection from malicious software",
            description="Implement procedures for guarding against, detecting, and reporting malicious software.",
            reference="§164.308(a)(5)(ii)(B)",
            criticality="high",
            tags=["malware-protection", "endpoint-security", "awareness", "administrative"],
        ),
        Control(
            id="HIPAA.164.308a5iv",
            title="Log-in monitoring",
            description="Implement procedures for monitoring log-in attempts and reporting discrepancies.",
            reference="§164.308(a)(5)(ii)(C)",
            criticality="high",
            tags=["login-monitoring", "access-monitoring", "anomaly-detection", "administrative"],
        ),
        Control(
            id="HIPAA.164.308a5v",
            title="Password management",
            description="Implement procedures for creating, changing, and safeguarding passwords.",
            reference="§164.308(a)(5)(ii)(D)",
            criticality="high",
            tags=["password-management", "credential-security", "administrative"],
        ),
    ],
)

_ADMIN_CONTINGENCY = Section(
    key="contingency_plan",
    title="Contingency Plan",
    weight=0.20,
    controls=[
        Control(
            id="HIPAA.164.308a7i",
            title="Data backup plan",
            description="Establish and implement procedures to create and maintain retrievable exact copies of ePHI.",
            reference="§164.308(a)(7)(ii)(A)",
            criticality="critical",
            tags=["backup", "data-recovery", "business-continuity", "administrative"],
        ),
        Control(
            id="HIPAA.164.308a7ii",
            title="Disaster recovery plan",
            description="Establish (and implement as needed) procedures to restore any loss of ePHI data.",
            reference="§164.308(a)(7)(ii)(B)",
            criticality="critical",
            tags=["disaster-recovery", "business-continuity", "ephi", "administrative"],
        ),
        Control(
            id="HIPAA.164.308a7iii",
            title="Emergency mode operation plan",
            description="Establish (and implement as needed) procedures to enable continuation of critical business processes for protection of ePHI while operating in emergency mode.",
            reference="§164.308(a)(7)(ii)(C)",
            criticality="high",
            tags=["emergency-mode", "business-continuity", "critical-processes", "administrative"],
        ),
        Control(
            id="HIPAA.164.308a7iv",
            title="Testing and revision procedures",
            description="Implement procedures for periodic testing and revision of contingency plans.",
            reference="§164.308(a)(7)(ii)(D)",
            criticality="high",
            tags=["testing", "contingency-testing", "plan-revision", "administrative"],
        ),
    ],
)

_ADMIN_EVALUATION = Section(
    key="evaluation",
    title="Evaluation & BAA Management",
    weight=0.10,
    controls=[
        Control(
            id="HIPAA.164.308a8",
            title="Security evaluation",
            description="Perform a periodic technical and nontechnical evaluation, based initially upon the standards implemented under this rule and, subsequently, in response to environmental or operational changes affecting the security of ePHI.",
            reference="§164.308(a)(8)",
            criticality="high",
            tags=["evaluation", "periodic-review", "compliance-assessment", "administrative"],
        ),
        Control(
            id="HIPAA.164.308b1",
            title="Business associate agreements",
            description="A covered entity may permit a business associate to create, receive, maintain, or transmit ePHI on the covered entity's behalf only if the covered entity obtains satisfactory assurances in the form of a written contract or arrangement.",
            reference="§164.308(b)(1)",
            criticality="critical",
            tags=["business-associate", "baa", "third-party", "contracts", "administrative"],
        ),
    ],
)

# ── Domain 2: Physical Safeguards (§164.310) ───────────────────────────────

_PHYS_FACILITY = Section(
    key="facility_access",
    title="Facility Access Controls",
    weight=0.50,
    controls=[
        Control(
            id="HIPAA.164.310a1",
            title="Contingency operations facility access",
            description="Establish (and implement as needed) procedures that allow facility access in support of restoration of lost data under the disaster recovery plan and emergency mode operations plan.",
            reference="§164.310(a)(2)(i)",
            criticality="high",
            tags=["facility-access", "contingency", "disaster-recovery", "physical"],
        ),
        Control(
            id="HIPAA.164.310a2",
            title="Facility security plan",
            description="Implement policies and procedures to safeguard the facility and the equipment therein from unauthorized physical access, tampering, and theft.",
            reference="§164.310(a)(2)(ii)",
            criticality="high",
            tags=["facility-security", "physical-security", "access-control", "physical"],
        ),
        Control(
            id="HIPAA.164.310a3",
            title="Access control and validation procedures",
            description="Implement procedures to control and validate a person's access to facilities based on their role or function, including visitor control, and control of access to software programs for testing and revision.",
            reference="§164.310(a)(2)(iii)",
            criticality="high",
            tags=["access-validation", "visitor-control", "role-based-access", "physical"],
        ),
        Control(
            id="HIPAA.164.310a4",
            title="Maintenance records",
            description="Implement policies and procedures to document repairs and modifications to the physical components of a facility which are related to security.",
            reference="§164.310(a)(2)(iv)",
            criticality="medium",
            tags=["maintenance", "documentation", "facility-management", "physical"],
        ),
    ],
)

_PHYS_WORKSTATION_DEVICE = Section(
    key="workstation_device",
    title="Workstation & Device Security",
    weight=0.50,
    controls=[
        Control(
            id="HIPAA.164.310b",
            title="Workstation use",
            description="Implement policies and procedures that specify the proper functions to be performed, the manner in which those functions are to be performed, and the physical attributes of the surroundings of a specific workstation or class of workstation that can access ePHI.",
            reference="§164.310(b)",
            criticality="high",
            tags=["workstation-use", "acceptable-use", "ephi-access", "physical"],
        ),
        Control(
            id="HIPAA.164.310c",
            title="Workstation security",
            description="Implement physical safeguards for all workstations that access ePHI, to restrict access to authorized users.",
            reference="§164.310(c)",
            criticality="high",
            tags=["workstation-security", "physical-safeguards", "access-restriction", "physical"],
        ),
        Control(
            id="HIPAA.164.310d1",
            title="Device and media disposal",
            description="Implement policies and procedures to address the final disposition of ePHI, and/or the hardware or electronic media on which it is stored.",
            reference="§164.310(d)(2)(i)",
            criticality="critical",
            tags=["media-disposal", "data-sanitization", "ephi", "physical"],
        ),
        Control(
            id="HIPAA.164.310d2",
            title="Media re-use",
            description="Implement procedures for removal of ePHI from electronic media before the media are made available for re-use.",
            reference="§164.310(d)(2)(ii)",
            criticality="high",
            tags=["media-reuse", "data-sanitization", "ephi", "physical"],
        ),
    ],
)

# ── Domain 3: Technical Safeguards (§164.312) ──────────────────────────────

_TECH_ACCESS_CONTROL = Section(
    key="access_control",
    title="Access Control",
    weight=0.30,
    controls=[
        Control(
            id="HIPAA.164.312a1",
            title="Unique user identification",
            description="Assign a unique name and/or number for identifying and tracking user identity.",
            reference="§164.312(a)(2)(i)",
            criticality="critical",
            tags=["user-identification", "identity-management", "access-control", "technical"],
        ),
        Control(
            id="HIPAA.164.312a2",
            title="Emergency access procedure",
            description="Establish (and implement as needed) procedures for obtaining necessary ePHI during an emergency.",
            reference="§164.312(a)(2)(ii)",
            criticality="high",
            tags=["emergency-access", "break-glass", "business-continuity", "technical"],
        ),
        Control(
            id="HIPAA.164.312a3",
            title="Automatic logoff",
            description="Implement electronic procedures that terminate an electronic session after a predetermined time of inactivity.",
            reference="§164.312(a)(2)(iii)",
            criticality="medium",
            tags=["session-management", "automatic-logoff", "inactivity-timeout", "technical"],
        ),
        Control(
            id="HIPAA.164.312a4",
            title="Encryption and decryption at rest",
            description="Implement a mechanism to encrypt and decrypt ePHI at rest.",
            reference="§164.312(a)(2)(iv)",
            criticality="critical",
            tags=["encryption-at-rest", "data-protection", "ephi", "technical"],
        ),
    ],
)

_TECH_AUDIT = Section(
    key="audit_controls",
    title="Audit Controls",
    weight=0.20,
    controls=[
        Control(
            id="HIPAA.164.312b",
            title="Audit controls",
            description="Implement hardware, software, and/or procedural mechanisms that record and examine activity in information systems that contain or use ePHI.",
            reference="§164.312(b)",
            criticality="critical",
            tags=["audit-controls", "logging", "monitoring", "ephi", "technical"],
        ),
        Control(
            id="HIPAA.164.312b2",
            title="Audit log review and reporting",
            description="Implement procedures to regularly review audit logs for suspicious activity, unauthorized access attempts, and policy violations.",
            reference="§164.312(b)",
            criticality="high",
            tags=["log-review", "audit-analysis", "monitoring", "technical"],
        ),
    ],
)

_TECH_INTEGRITY = Section(
    key="integrity_controls",
    title="Integrity Controls",
    weight=0.20,
    controls=[
        Control(
            id="HIPAA.164.312c1",
            title="Mechanism to authenticate ePHI",
            description="Implement electronic mechanisms to corroborate that ePHI has not been altered or destroyed in an unauthorized manner.",
            reference="§164.312(c)(2)",
            criticality="high",
            tags=["data-integrity", "authentication", "ephi", "technical"],
        ),
        Control(
            id="HIPAA.164.312c2",
            title="Person or entity authentication",
            description="Implement procedures to verify that a person or entity seeking access to ePHI is the one claimed.",
            reference="§164.312(d)",
            criticality="critical",
            tags=["authentication", "identity-verification", "access-control", "technical"],
        ),
    ],
)

_TECH_TRANSMISSION = Section(
    key="transmission_security",
    title="Transmission Security",
    weight=0.30,
    controls=[
        Control(
            id="HIPAA.164.312e1",
            title="Integrity controls for transmission",
            description="Implement security measures to ensure that electronically transmitted ePHI is not improperly modified without detection until disposed of.",
            reference="§164.312(e)(2)(i)",
            criticality="high",
            tags=["transmission-integrity", "data-integrity", "communication-security", "technical"],
        ),
        Control(
            id="HIPAA.164.312e2",
            title="Encryption in transit",
            description="Implement a mechanism to encrypt ePHI whenever deemed appropriate during transmission over an electronic communications network.",
            reference="§164.312(e)(2)(ii)",
            criticality="critical",
            tags=["encryption-in-transit", "tls", "communication-security", "technical"],
        ),
        Control(
            id="HIPAA.164.312e3",
            title="Secure messaging and email",
            description="Implement policies and technical controls to ensure ePHI transmitted via email or messaging is encrypted and access-controlled.",
            reference="§164.312(e)",
            criticality="high",
            tags=["secure-messaging", "email-security", "encryption", "technical"],
        ),
        Control(
            id="HIPAA.164.312e4",
            title="Remote access security",
            description="Implement technical controls to secure remote access sessions that involve ePHI, including VPN, multi-factor authentication, and session encryption.",
            reference="§164.312(e)",
            criticality="high",
            tags=["remote-access", "vpn", "mfa", "session-security", "technical"],
        ),
    ],
)

# ── Domain 4: Privacy Rule Requirements (§164.500-528) ─────────────────────

_PRIVACY_USE_DISCLOSURE = Section(
    key="use_disclosure",
    title="Use & Disclosure of PHI",
    weight=0.35,
    controls=[
        Control(
            id="HIPAA.164.502a",
            title="Minimum necessary standard",
            description="When using or disclosing PHI or when requesting PHI from another covered entity or business associate, a covered entity or business associate must make reasonable efforts to limit PHI to the minimum necessary to accomplish the intended purpose.",
            reference="§164.502(b)",
            criticality="critical",
            tags=["minimum-necessary", "data-minimization", "phi", "privacy"],
        ),
        Control(
            id="HIPAA.164.502b",
            title="Treatment, payment, and operations (TPO) uses",
            description="Define and document permitted uses and disclosures of PHI for treatment, payment, and health care operations without individual authorization.",
            reference="§164.502(a)(1)",
            criticality="high",
            tags=["tpo", "permitted-uses", "phi", "privacy"],
        ),
        Control(
            id="HIPAA.164.508a",
            title="Uses and disclosures requiring authorization",
            description="Obtain valid individual authorization for uses and disclosures of PHI not otherwise permitted or required, including marketing, sale of PHI, and psychotherapy notes.",
            reference="§164.508",
            criticality="critical",
            tags=["authorization", "consent", "marketing", "phi", "privacy"],
        ),
        Control(
            id="HIPAA.164.514a",
            title="De-identification of PHI",
            description="Implement policies to de-identify PHI through either expert determination or safe harbor methods so that the information is no longer individually identifiable.",
            reference="§164.514(a-b)",
            criticality="high",
            tags=["de-identification", "safe-harbor", "expert-determination", "privacy"],
        ),
    ],
)

_PRIVACY_INDIVIDUAL_RIGHTS = Section(
    key="individual_rights",
    title="Individual Rights",
    weight=0.35,
    controls=[
        Control(
            id="HIPAA.164.520",
            title="Notice of privacy practices",
            description="Provide individuals with adequate notice of the uses and disclosures of PHI that may be made by the covered entity, and of the individual's rights and the covered entity's legal duties with respect to PHI.",
            reference="§164.520",
            criticality="critical",
            tags=["notice", "privacy-practices", "transparency", "individual-rights", "privacy"],
        ),
        Control(
            id="HIPAA.164.524",
            title="Right of access to PHI",
            description="Provide individuals the right to inspect and obtain a copy of their PHI in a designated record set, in the form or format requested if readily producible, within 30 days of the request.",
            reference="§164.524",
            criticality="critical",
            tags=["right-of-access", "data-subject-rights", "phi", "individual-rights", "privacy"],
        ),
        Control(
            id="HIPAA.164.526",
            title="Right to request amendment",
            description="Permit individuals to request amendment of their PHI in a designated record set and act on the request within 60 days.",
            reference="§164.526",
            criticality="high",
            tags=["amendment", "data-correction", "individual-rights", "privacy"],
        ),
        Control(
            id="HIPAA.164.528",
            title="Accounting of disclosures",
            description="Provide individuals with an accounting of disclosures of their PHI made by the covered entity in the six years prior to the request.",
            reference="§164.528",
            criticality="high",
            tags=["accounting-disclosures", "transparency", "individual-rights", "privacy"],
        ),
        Control(
            id="HIPAA.164.522",
            title="Right to request restrictions",
            description="Permit individuals to request restrictions on certain uses and disclosures of PHI, and comply with agreed-upon restrictions.",
            reference="§164.522",
            criticality="medium",
            tags=["restrictions", "individual-rights", "phi", "privacy"],
        ),
        Control(
            id="HIPAA.164.522b",
            title="Right to request confidential communications",
            description="Permit individuals to request to receive communications of PHI by alternative means or at alternative locations.",
            reference="§164.522(b)",
            criticality="medium",
            tags=["confidential-communications", "individual-rights", "privacy"],
        ),
    ],
)

_PRIVACY_BREACH_NOTIFICATION = Section(
    key="breach_notification",
    title="Breach Notification Rule",
    weight=0.30,
    controls=[
        Control(
            id="HIPAA.164.404a",
            title="Notification to individuals",
            description="Following the discovery of a breach of unsecured PHI, notify each individual whose unsecured PHI has been, or is reasonably believed to have been, accessed, acquired, used, or disclosed as a result of such breach, without unreasonable delay and no later than 60 days.",
            reference="§164.404",
            criticality="critical",
            tags=["breach-notification", "individual-notification", "incident-response", "privacy"],
        ),
        Control(
            id="HIPAA.164.406",
            title="Notification to HHS",
            description="Notify the Secretary of HHS of breaches of unsecured PHI. Breaches affecting 500 or more individuals must be reported without unreasonable delay. Breaches affecting fewer than 500 individuals may be reported annually.",
            reference="§164.406",
            criticality="critical",
            tags=["hhs-notification", "breach-reporting", "regulatory", "privacy"],
        ),
        Control(
            id="HIPAA.164.408",
            title="Notification to media",
            description="For breaches affecting more than 500 residents of a state or jurisdiction, provide notice to prominent media outlets serving the state or jurisdiction without unreasonable delay and no later than 60 days.",
            reference="§164.408",
            criticality="high",
            tags=["media-notification", "breach-notification", "public-notice", "privacy"],
        ),
        Control(
            id="HIPAA.164.414",
            title="Business associate breach notification obligations",
            description="A business associate shall, following the discovery of a breach of unsecured PHI, notify the covered entity of such breach without unreasonable delay and no later than 60 days.",
            reference="§164.414",
            criticality="critical",
            tags=["business-associate", "breach-notification", "third-party", "privacy"],
        ),
    ],
)

# ── Assemble domains ──────────────────────────────────────────────────────

_ADMINISTRATIVE = Domain(
    key="administrative",
    title="Administrative Safeguards",
    weight=0.30,
    sections={
        "security_management": _ADMIN_SECURITY_MGMT,
        "workforce_security": _ADMIN_WORKFORCE,
        "information_access": _ADMIN_INFO_ACCESS,
        "security_awareness": _ADMIN_AWARENESS,
        "contingency_plan": _ADMIN_CONTINGENCY,
        "evaluation": _ADMIN_EVALUATION,
    },
)

_PHYSICAL = Domain(
    key="physical",
    title="Physical Safeguards",
    weight=0.15,
    sections={
        "facility_access": _PHYS_FACILITY,
        "workstation_device": _PHYS_WORKSTATION_DEVICE,
    },
)

_TECHNICAL = Domain(
    key="technical",
    title="Technical Safeguards",
    weight=0.30,
    sections={
        "access_control": _TECH_ACCESS_CONTROL,
        "audit_controls": _TECH_AUDIT,
        "integrity_controls": _TECH_INTEGRITY,
        "transmission_security": _TECH_TRANSMISSION,
    },
)

_PRIVACY = Domain(
    key="privacy",
    title="Privacy Rule Requirements",
    weight=0.25,
    sections={
        "use_disclosure": _PRIVACY_USE_DISCLOSURE,
        "individual_rights": _PRIVACY_INDIVIDUAL_RIGHTS,
        "breach_notification": _PRIVACY_BREACH_NOTIFICATION,
    },
)

# ── Dependency DAG ────────────────────────────────────────────────────────

_HIPAA_DEPENDENCIES: dict[str, list[str]] = {
    # Risk management depends on risk analysis
    "HIPAA.164.308a1ii": ["HIPAA.164.308a1i"],
    # Sanction policy needs risk management foundation
    "HIPAA.164.308a1iii": ["HIPAA.164.308a1ii"],
    # Activity review depends on risk analysis
    "HIPAA.164.308a1iv": ["HIPAA.164.308a1i"],
    # Workforce clearance needs authorization policy
    "HIPAA.164.308a3ii": ["HIPAA.164.308a3i"],
    # Termination needs clearance procedures
    "HIPAA.164.308a3iii": ["HIPAA.164.308a3ii"],
    # Access establishment needs access authorization policy
    "HIPAA.164.308a4ii": ["HIPAA.164.308a4i"],
    # Contingency plan chain
    "HIPAA.164.308a7ii": ["HIPAA.164.308a7i"],  # DR needs backup
    "HIPAA.164.308a7iii": ["HIPAA.164.308a7ii"],  # Emergency mode needs DR
    "HIPAA.164.308a7iv": ["HIPAA.164.308a7i", "HIPAA.164.308a7ii"],  # Testing needs plans
    # Audit log review depends on audit controls
    "HIPAA.164.312b2": ["HIPAA.164.312b"],
    # Encryption in transit depends on integrity controls
    "HIPAA.164.312e2": ["HIPAA.164.312e1"],
    # BA breach notification depends on individual notification
    "HIPAA.164.414": ["HIPAA.164.404a"],
    # HHS and media notification depend on individual notification
    "HIPAA.164.406": ["HIPAA.164.404a"],
    "HIPAA.164.408": ["HIPAA.164.404a"],
    # Evaluation depends on risk analysis
    "HIPAA.164.308a8": ["HIPAA.164.308a1i"],
    # Technical access control needs administrative access policies
    "HIPAA.164.312a1": ["HIPAA.164.308a4i"],
}

# ── Root cause clusters ───────────────────────────────────────────────────

_HIPAA_ROOT_CAUSE_CLUSTERS: dict[str, dict] = {
    "policy": {
        "title": "HIPAA Policy & Procedure Development",
        "description": "Develop, formalize, and publish HIPAA-compliant policies and procedures covering privacy, security, and breach notification requirements.",
        "typical_requirements": [
            "HIPAA.164.308a1iii", "HIPAA.164.502a", "HIPAA.164.508a",
            "HIPAA.164.520", "HIPAA.164.310b",
        ],
    },
    "people": {
        "title": "Workforce Training & Awareness Program",
        "description": "Establish and maintain a comprehensive security awareness and training program covering ePHI handling, privacy practices, and incident reporting.",
        "typical_requirements": [
            "HIPAA.164.308a5i", "HIPAA.164.308a5ii", "HIPAA.164.308a3i",
            "HIPAA.164.308a3ii", "HIPAA.164.308a3iii",
        ],
    },
    "process": {
        "title": "Operational Process & Compliance Formalization",
        "description": "Establish repeatable processes for risk analysis, access management, breach notification, individual rights fulfillment, and business associate oversight.",
        "typical_requirements": [
            "HIPAA.164.308a1i", "HIPAA.164.308a4i", "HIPAA.164.404a",
            "HIPAA.164.524", "HIPAA.164.308b1",
        ],
    },
    "technology": {
        "title": "Technical Security Controls Implementation",
        "description": "Implement or upgrade technical controls including encryption, access control, audit logging, transmission security, and endpoint protection.",
        "typical_requirements": [
            "HIPAA.164.312a1", "HIPAA.164.312a4", "HIPAA.164.312b",
            "HIPAA.164.312e2", "HIPAA.164.312c2",
        ],
    },
    "governance": {
        "title": "HIPAA Governance & Compliance Program",
        "description": "Establish privacy and security officer roles, risk assessment program, periodic evaluations, and business associate agreement management.",
        "typical_requirements": [
            "HIPAA.164.308a1i", "HIPAA.164.308a8", "HIPAA.164.308b1",
            "HIPAA.164.406",
        ],
    },
}

# ── Scope questions ───────────────────────────────────────────────────────

_HIPAA_SCOPE_QUESTIONS = [
    ScopeQuestion(
        id="HIPAA.SCP.1",
        question="What type of HIPAA-regulated entity is your organization?",
        help_text="Covered entities include health plans, health care clearinghouses, and health care providers who transmit health information electronically. Business associates perform functions on behalf of covered entities involving PHI.",
        type="single_select",
        options=[
            {"value": "covered_entity_provider", "label": "Covered Entity — Health Care Provider"},
            {"value": "covered_entity_plan", "label": "Covered Entity — Health Plan"},
            {"value": "covered_entity_clearinghouse", "label": "Covered Entity — Health Care Clearinghouse"},
            {"value": "business_associate", "label": "Business Associate"},
            {"value": "hybrid_entity", "label": "Hybrid Entity (designated health care component)"},
            {"value": "unsure", "label": "Not yet determined"},
        ],
    ),
    ScopeQuestion(
        id="HIPAA.SCP.2",
        question="Does your organization create, receive, maintain, or transmit electronic protected health information (ePHI)?",
        help_text="ePHI includes any individually identifiable health information maintained or transmitted in electronic form. This determines applicability of the Security Rule.",
        type="single_select",
        options=[
            {"value": "yes_high_volume", "label": "Yes — high volume (10,000+ records)"},
            {"value": "yes_moderate", "label": "Yes — moderate volume (1,000-10,000 records)"},
            {"value": "yes_low", "label": "Yes — low volume (under 1,000 records)"},
            {"value": "no", "label": "No"},
        ],
    ),
    ScopeQuestion(
        id="HIPAA.SCP.3",
        question="Does your organization engage business associates who access or handle PHI on your behalf?",
        help_text="Business associates include IT vendors, cloud hosting providers, billing companies, consultants, and any entity that creates, receives, maintains, or transmits PHI on behalf of a covered entity.",
        type="single_select",
        options=[
            {"value": "yes_many", "label": "Yes — many (10+ business associates)"},
            {"value": "yes_few", "label": "Yes — a few (1-10 business associates)"},
            {"value": "no", "label": "No"},
            {"value": "unsure", "label": "Unsure"},
        ],
    ),
    ScopeQuestion(
        id="HIPAA.SCP.4",
        question="Does your organization operate in multiple states or handle PHI across state lines?",
        help_text="Multi-state operations may trigger additional state-level breach notification laws and privacy requirements beyond HIPAA.",
        type="single_select",
        options=[
            {"value": "yes_multi_state", "label": "Yes — multi-state operations"},
            {"value": "single_state", "label": "No — single state only"},
            {"value": "international", "label": "Yes — including international operations"},
        ],
    ),
]

# ── Question text ─────────────────────────────────────────────────────────
# One question per control, following the same pattern as ISO 27001

_HIPAA_QUESTIONS: dict[str, QuestionDef] = {}


def _generate_hipaa_questions() -> dict[str, QuestionDef]:
    """Generate question definitions for all HIPAA controls."""
    qs = {}
    for domain in [_ADMINISTRATIVE, _PHYSICAL, _TECHNICAL, _PRIVACY]:
        for section in domain.sections.values():
            for ctrl in section.controls:
                qs[ctrl.id] = QuestionDef(
                    control_id=ctrl.id,
                    question=f"Has your organization implemented {ctrl.title.lower()}? ({ctrl.reference})",
                    guidance=ctrl.description,
                )
    return qs


_HIPAA_QUESTIONS = _generate_hipaa_questions()

# ── Red flag patterns ─────────────────────────────────────────────────────

_HIPAA_RED_FLAGS = [
    RedFlagPattern(
        pattern="No designated Privacy or Security Officer",
        description="HIPAA requires designation of a Privacy Officer and a Security Officer responsible for development and implementation of policies. Absence indicates fundamental non-compliance.",
        severity="high",
    ),
    RedFlagPattern(
        pattern="Missing or outdated risk analysis",
        description="No documented risk analysis of ePHI, or risk analysis not updated after significant changes to systems, operations, or environment. This is the most commonly cited HIPAA violation in OCR enforcement actions.",
        severity="high",
    ),
    RedFlagPattern(
        pattern="No Business Associate Agreements on file",
        description="PHI shared with vendors or contractors without executed BAAs, or BAAs that lack required provisions such as breach notification obligations and safeguard requirements.",
        severity="high",
    ),
    RedFlagPattern(
        pattern="Unencrypted ePHI at rest or in transit",
        description="ePHI stored on servers, laptops, or portable media without encryption, or transmitted via unencrypted email or HTTP. While encryption is addressable, lack of it without a documented alternative is a major risk.",
        severity="high",
    ),
    RedFlagPattern(
        pattern="No breach notification procedures documented",
        description="No written procedures for identifying, investigating, and reporting breaches of unsecured PHI within the required 60-day timeframe to individuals, HHS, and media (for large breaches).",
        severity="high",
    ),
    RedFlagPattern(
        pattern="Generic or absent workforce training records",
        description="No evidence of HIPAA-specific security and privacy training for workforce members, or training materials that are generic and not tailored to the organization's policies, systems, and PHI handling procedures.",
        severity="medium",
    ),
]

# ── Framework definition ──────────────────────────────────────────────────

HIPAA_DEFINITION = FrameworkDefinition(
    id="hipaa",
    name="HIPAA",
    version="2013",
    description="HIPAA Security Rule, Privacy Rule & Breach Notification Rule (45 CFR Part 164)",
    domains={
        "administrative": _ADMINISTRATIVE,
        "physical": _PHYSICAL,
        "technical": _TECHNICAL,
        "privacy": _PRIVACY,
    },
    dependencies=_HIPAA_DEPENDENCIES,
    root_cause_clusters=_HIPAA_ROOT_CAUSE_CLUSTERS,
    scope_questions=_HIPAA_SCOPE_QUESTIONS,
    questions=_HIPAA_QUESTIONS,
    red_flag_patterns=_HIPAA_RED_FLAGS,
)
