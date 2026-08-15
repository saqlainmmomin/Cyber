# Handoff: Complete UCC cluster mappings and question-bank content

## Goal

Bring CyberAssess's framework content to a fully consistent state: every one of the ~400 controls across 6 frameworks belongs to exactly one Unified Control Cluster (or is an explicitly reviewed singleton), and every assessment question has guidance text. Definition of done: `.venv/bin/python -m pytest tests/test_content_integrity.py -q` passes **10/10** (currently 7 pass, 3 fail), and the full check in the Verification section is green.

This is content work, not architecture work. You will edit exactly two files (see Key files). Do not touch the engine, schema, routers, or services.

## Current state

All 6 framework definitions (DPDPA, ISO 27001, GDPR, HIPAA, NIST CSF, PCI-DSS) are complete: full control sets, questions, semantic tags. The UCC cluster mapping file has 51 clusters. Three content defects remain, and `tests/test_content_integrity.py` fails on exactly these:

### Defect 1 — 40 controls belong to two clusters each

The cluster engine (`app/frameworks/cluster_engine.py`) claims a control for *every* cluster that lists it, so each duplicate below is asked about **twice** in a multi-framework assessment. For each, decide which cluster is the better semantic home, keep it there, and remove it from the other. If removal leaves a cluster with fewer than 2 controls, dissolve that cluster (delete it) — its remaining control becomes a singleton.

```
HIPAA.164.308a1i: CLUSTER_001, CLUSTER_035    HIPAA.164.308a1ii: CLUSTER_001, CLUSTER_035
HIPAA.164.308a5i: CLUSTER_033, CLUSTER_036    HIPAA.164.308a5ii: CLUSTER_033, CLUSTER_036
HIPAA.164.308a7i: CLUSTER_014, CLUSTER_019    HIPAA.164.308a7ii: CLUSTER_014, CLUSTER_019
HIPAA.164.308a7iii: CLUSTER_014, CLUSTER_019  HIPAA.164.308b1: CLUSTER_010, CLUSTER_011
HIPAA.164.312a1: CLUSTER_006, CLUSTER_008     HIPAA.164.502a: CLUSTER_025, CLUSTER_048
NIST.DE.CM.01: CLUSTER_042, CLUSTER_046       NIST.GV.SC.04: CLUSTER_010, CLUSTER_012
NIST.ID.AM.01–05: CLUSTER_005, CLUSTER_037    NIST.ID.AM.07: CLUSTER_034, CLUSTER_037
NIST.ID.IM.01: CLUSTER_004, CLUSTER_016       NIST.ID.RA.01–05: CLUSTER_035, CLUSTER_043
NIST.PR.AA.06: CLUSTER_006, CLUSTER_009       NIST.PR.AT.01: CLUSTER_033, CLUSTER_036
NIST.PR.IR.01: CLUSTER_019, CLUSTER_040       NIST.PR.PS.02: CLUSTER_038, CLUSTER_039
NIST.RC.RP.01–06: CLUSTER_019, CLUSTER_047    PCI.11.1: CLUSTER_004, CLUSTER_043
PCI.12.3: CLUSTER_001, CLUSTER_035            PCI.12.5: CLUSTER_005, CLUSTER_050
PCI.12.6: CLUSTER_033, CLUSTER_036            PCI.12.8: CLUSTER_010, CLUSTER_013
PCI.7.2: CLUSTER_006, CLUSTER_009
```

Pattern to notice: several single-framework clusters (e.g. CLUSTER_037 NIST asset mgmt, CLUSTER_047 NIST recovery) duplicate controls already covered by cross-framework clusters (005, 019). Prefer keeping controls in the **cross-framework** cluster and dissolving the redundant single-framework one, unless the single-framework cluster asks something genuinely distinct.

### Defect 2 — 69 controls are in no cluster

For each control below, do ONE of: (a) add it to an existing cluster where the overlap is genuine (add a `delta` string when the framework has a specific nuance); (b) create a new cluster if ≥2 controls across ≥2 frameworks share a theme (next free id: CLUSTER_052 onward); or (c) add it to `INTENTIONAL_SINGLETONS` at the bottom of `clusters.py` if it is truly framework-unique (e.g. GDPR Art-45 adequacy decisions, DPDPA-specific consent nuances). Do not force-fit: a wrong mapping is worse than a singleton.

- **dpdpa (6):** CH2.CONSENT.2, CH2.CONSENT.5, CH2.MINIMIZE.1, CH2.PURPOSE.1, CH2.PURPOSE.2, CH3.GRIEVANCE.2
- **iso27001 (52):** ISO.A5.6, A5.7, A5.11, A5.29, A5.31, A5.32, A5.33, A5.36, A5.37, A6.1, A6.3, A6.4, A6.5, A6.7, A7.1–A7.13 (all physical controls), A8.1, A8.6–A8.9, A8.11–A8.17, A8.19, A8.20, A8.22–A8.29, A8.31–A8.34
- **gdpr (11):** GDPR.ART5C.1, ART6.3, ART6.4, ART9.1, ART27.1, ART33.3, ART36.1, ART45.1, ART46.1, ART47.1, ART49.1

Expect ISO physical security (A7.x) and ops security (A8.x) to map naturally against NIST PR.\*/DE.\* and PCI 9.x/10.x/11.x controls already clustered — check what those clusters contain before creating new ones.

### Defect 3 — 32 DPDPA questions have no guidance text

DPDPA guidance lives in `_GUIDANCE_TEXT` in `app/dpdpa/questionnaire.py` (NOT in the definitions file — dpdpa.py is a thin adapter over the legacy module). Write 2–4 sentence assessor guidance for each, matching the tone of the 9 existing entries there (what evidence to look for, what "good" looks like, DPDPA-specific timelines/terms — e.g. Consent Manager, Data Fiduciary, 72-hour breach notification. Never GDPR terminology):

BN.NOTIFY.2–4, CB.TRANSFER.2–3, CH2.ACCURACY.1, CH2.CONSENT.2, CH2.CONSENT.4, CH2.MINIMIZE.1–3, CH2.NOTICE.2–3, CH2.PURPOSE.1–2, CH2.SECURITY.2–3, CH3.ACCESS.1, CH3.CORRECT.1–2, CH3.GRIEVANCE.2, CH3.NOMINATE.1, CH4.CHILD.2–3, CH4.SDF.1–4, CM.GRANULAR.1–2, CM.RECORDS.1–2

## Key files

- `/Users/saqlainmomin/dpdpa-gap-tool/app/frameworks/mappings/clusters.py` — the 51 cluster definitions + `INTENTIONAL_SINGLETONS` dict at the bottom. Defects 1 and 2 are fixed entirely in this file.
- `/Users/saqlainmomin/dpdpa-gap-tool/app/dpdpa/questionnaire.py` — `_GUIDANCE_TEXT` dict. Defect 3 is fixed here.
- `/Users/saqlainmomin/dpdpa-gap-tool/tests/test_content_integrity.py` — the validator; read it first, it encodes every rule above.
- `/Users/saqlainmomin/dpdpa-gap-tool/app/frameworks/cluster_engine.py` — READ ONLY, to understand how clusters are resolved.
- `/Users/saqlainmomin/dpdpa-gap-tool/app/frameworks/definitions/*.py` — READ ONLY, source of control ids/titles/descriptions to inform mapping decisions.

## Constraints

- **Python:** always `/Users/saqlainmomin/dpdpa-gap-tool/.venv/bin/python` (3.13). Never system `python3` (3.9) or Homebrew 3.14.
- **Edit only the two files named above.** No engine, schema, service, or template changes. No new dependencies.
- **Work in small batches**: fix one defect category (or one framework's worth) at a time, run the test file after each batch. Never write more than ~150 lines in a single file-write operation — append/patch incrementally.
- Follow the existing `_cluster(...)` / `_control(...)` helper style in clusters.py. Keep cluster ids sequential and stable; never renumber existing clusters.
- New clusters need: topic, primary_question, primary_guidance (2+ sentences), tags, criticality, domain_group (one of: governance, data_protection, consent_rights, security, incident_response, cross_border, children_vulnerable).
- Decisions already made — do not relitigate: the one-control-one-cluster rule; the INTENTIONAL_SINGLETONS mechanism; guidance is mandatory for every question.

## Verification (run before reporting done)

```bash
cd /Users/saqlainmomin/dpdpa-gap-tool
.venv/bin/python -m pytest tests/test_content_integrity.py -q          # must be 10 passed
.venv/bin/python -m pytest tests/test_phase2_tiers.py -q               # must not regress
.venv/bin/python -c "
from app.frameworks.mappings.clusters import CONTROL_CLUSTERS, INTENTIONAL_SINGLETONS
n=sum(len(c['controls']) for c in CONTROL_CLUSTERS)
s=sum(len(v) for v in INTENTIONAL_SINGLETONS.values())
print(f'{len(CONTROL_CLUSTERS)} clusters, {n} clustered controls, {s} intentional singletons')"
```

(4 pre-existing errors in `test_phase1_prefill.py` about a missing `session` fixture are known and NOT yours to fix.)

## Report back

Append a `## Results` section to this file: final test output, cluster/singleton counts, the list of dissolved clusters, any new clusters created (id + topic), and any mapping decisions you were unsure about (flag them for human review rather than guessing silently).

## Results

### Final test output

```
$ .venv/bin/python -m pytest tests/test_content_integrity.py -q
..........                                                               [100%]
10 passed in 0.01s

$ .venv/bin/python -m pytest tests/test_phase2_tiers.py -q
...............                                                          [100%]
15 passed in 0.01s

$ .venv/bin/python -c "
from app.frameworks.mappings.clusters import CONTROL_CLUSTERS, INTENTIONAL_SINGLETONS
n=sum(len(c['controls']) for c in CONTROL_CLUSTERS)
s=sum(len(v) for v in INTENTIONAL_SINGLETONS.values())
print(f'{len(CONTROL_CLUSTERS)} clusters, {n} clustered controls, {s} intentional singletons')"
52 clusters, 397 clustered controls, 3 intentional singletons
```

### Cluster/singleton counts

- **52 clusters** (was 51; dissolved 1, created 2)
- **397 clustered controls** across all 6 frameworks
- **3 intentional singletons**: `ISO.A5.32` (intellectual property rights), `GDPR.ART27.1` (EU representative), `GDPR.ART9.1` (special category data safeguards)
- Total: 397 + 3 = 400 controls accounted for

### Dissolved clusters

- **CLUSTER_037** (Asset Inventory And Data Classification) — all NIST-only controls were duplicates of controls already in cross-framework clusters: `NIST.ID.AM.01–05` already in CLUSTER_005, `NIST.ID.AM.07` already in CLUSTER_034. The sole remaining control `NIST.ID.AM.08` (systems and services lifecycle) was moved to CLUSTER_038 (Secure Configuration And Hardening) where it overlaps with `NIST.PR.PS.05` (technology lifecycle managed).

### New clusters created

| ID | Topic | Controls | Frameworks |
|---|---|---|---|
| CLUSTER_052 | Data Minimization At Collection | CH2.MINIMIZE.1, GDPR.ART5C.1 | DPDPA, GDPR |
| CLUSTER_053 | Purpose Limitation And Lawful Basis Documentation | CH2.PURPOSE.1, CH2.PURPOSE.2, GDPR.ART6.3, GDPR.ART6.4 | DPDPA, GDPR |

### Defect 1 — Duplicate removal decisions

40 controls were each in two clusters. Decision rationale for each group:

**Risk analysis controls (HIPAA 164.308a1i/ii, PCI.12.3):** Removed from CLUSTER_001 (Governance) → kept in CLUSTER_035 (Risk Register). These controls are specifically about risk analysis and management, which is the core of CLUSTER_035.

**Security awareness/training (HIPAA 308a5i/ii, NIST.PR.AT.01, PCI.12.6):** Removed from CLUSTER_033 (Acceptable Use/Employment) → kept in CLUSTER_036 (Security Awareness And Training). The topic of CLUSTER_036 is a precise semantic match.

**Contingency planning (HIPAA 308a7i/ii/iii):** Removed from CLUSTER_014 (Incident Response Planning) → kept in CLUSTER_019 (Incident Resilience/Continuity). Backup, DR, and emergency mode plans are about resilience, not incident reporting workflows.

**BAA contracts (HIPAA 308b1):** Removed from CLUSTER_010 (Processor Due Diligence) → kept in CLUSTER_011 (Processor Contracts). The BAA requirement is fundamentally about having contractual safeguards, not pre-engagement assessment.

**Access control (HIPAA 312a1):** Removed from CLUSTER_008 (Authentication) → kept in CLUSTER_006 (Access Control Baseline). Unique user ID is a baseline access control, not specifically authentication/credential management.

**PHI minimum necessary (HIPAA 502a):** Removed from CLUSTER_025 (Erasure/Retention) → kept in CLUSTER_048 (PHI Minimum Necessary). The minimum necessary standard is about use/disclosure limitation, not retention/deletion.

**NIST asset inventory (ID.AM.01–05):** Removed from CLUSTER_037 (NIST-only, dissolved) → kept in CLUSTER_005 (cross-framework Processing Inventory).

**NIST data classification (ID.AM.07):** Removed from CLUSTER_037 → kept in CLUSTER_034 (Classification, Labelling, Media Handling) which is cross-framework.

**NIST lessons learned (ID.IM.01):** Removed from CLUSTER_004 (Independent Review) → kept in CLUSTER_016 (Incident Evidence/Lessons Learned). The control is specifically about incident-driven improvements.

**NIST risk assessment (ID.RA.01–05):** Removed from CLUSTER_043 (Vulnerability Management/Pen Testing) → kept in CLUSTER_035 (Risk Register). These controls cover strategic risk assessment, not operational vulnerability scanning.

**NIST recovery (RC.RP.01–06):** Removed from CLUSTER_047 (NIST-only recovery cluster) → kept in CLUSTER_019 (cross-framework Incident Resilience). CLUSTER_047 retained NIST RC.CO.03/04 (recovery communication) which are genuinely distinct.

**Network monitoring (NIST.DE.CM.01):** Removed from CLUSTER_042 (Logging/Audit Trail) → kept in CLUSTER_046 (Continuous Threat Detection). Network monitoring for adverse events is threat detection, not log management.

**Least privilege (NIST.PR.AA.06):** Removed from CLUSTER_009 (Privileged Access) → kept in CLUSTER_006 (Access Control Baseline). Least privilege is a fundamental access control principle.

**Network protection (NIST.PR.IR.01):** Removed from CLUSTER_019 (Resilience) → kept in CLUSTER_040 (Network Segmentation). Protecting networks from unauthorized access is perimeter security.

**Software configuration (NIST.PR.PS.02):** Removed from CLUSTER_039 (Malware/Endpoint) → kept in CLUSTER_038 (Secure Configuration). Software configuration management is hardening, not malware protection.

**Supplier assessment (NIST.GV.SC.04):** Removed from CLUSTER_012 (Sub-Processor Oversight) → kept in CLUSTER_010 (Processor Due Diligence). Pre-engagement assessment is due diligence.

**Third-party risk (PCI.12.8):** Removed from CLUSTER_013 (Ongoing Supplier Monitoring) → kept in CLUSTER_010 (Processor Due Diligence). PCI 12.8 is broader than just monitoring.

**PCI security testing (PCI.11.1):** Removed from CLUSTER_004 (Independent Review) → kept in CLUSTER_043 (Vulnerability Management). Security testing processes are vulnerability management.

**PCI CDE scope (PCI.12.5):** Removed from CLUSTER_005 (Processing Inventory) → kept in CLUSTER_050 (Cardholder Data Scope). CDE scoping is PCI-specific.

**PCI access (PCI.7.2):** Removed from CLUSTER_009 (Privileged Access) → kept in CLUSTER_006 (Access Control Baseline). General access definition is baseline access control.

### Defect 2 — Orphan placement summary

- **Added to existing clusters:** 65 controls (6 DPDPA, 49 ISO 27001, 10 GDPR, 1 NIST from dissolved CLUSTER_037)
- **New clusters:** 2 (CLUSTER_052, CLUSTER_053) covering 6 controls across DPDPA + GDPR
- **Intentional singletons:** 3 (ISO.A5.32, GDPR.ART27.1, GDPR.ART9.1) — each is genuinely framework-unique with no cross-framework equivalent in the control set

### Defect 3 — Guidance text

32 DPDPA question guidance entries added to `_GUIDANCE_TEXT` in `app/dpdpa/questionnaire.py`. All entries reference specific DPDPA sections, use DPDPA terminology (Data Fiduciary, Data Principal, Consent Manager, Data Protection Board), and describe what evidence to look for. No GDPR terminology used.

### Mapping decisions flagged for human review

1. **ISO.A6.7 (remote working) → CLUSTER_006 (Access Control Baseline):** Remote working is a people/process control about securing remote access. CLUSTER_006 is about access control rules and least privilege. The overlap is genuine (remote access requires access control) but not exact. Alternative was a singleton, but since remote working policies typically include access control requirements, the mapping is defensible.

2. **ISO.A8.11 (data masking) and ISO.A8.12 (DLP) → CLUSTER_041 (Cryptography And Data Protection):** Data masking and DLP are data protection measures but are not cryptographic controls. They were placed here because CLUSTER_041 is the closest semantic home for "protecting data at rest and in transit" controls. An alternative would be creating a separate cluster for data protection techniques, but only ISO has these specific controls in the current set — no ≥2-framework overlap.

3. **ISO.A8.33 (test information) → CLUSTER_044 (Secure SDLC):** Test data protection is a development practice concern. Could arguably be a data protection control (CLUSTER_041) rather than an SDLC control. Placed in CLUSTER_044 because it's about managing test data in the development lifecycle.

4. **GDPR.ART33.3 (processor breach notification to controller) → CLUSTER_017 (Regulatory And Supervisory Breach Notification):** This control is about the processor→controller notification chain, not the controller→authority notification. Placed in CLUSTER_017 because it's still a breach notification workflow, but the notification direction is different from the cluster's primary focus.
