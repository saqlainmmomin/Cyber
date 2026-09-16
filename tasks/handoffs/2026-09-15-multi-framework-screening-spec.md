# Multi-framework domain screening — approved design specification

**Date:** 2026-09-15  
**Source:** `tasks/handoffs/2026-09-15-multi-framework-screening-design-brief.md`  
**Decision:** Option B approved by Saqlain on 2026-09-15  
**Readiness:** content-ready; model-facing implementation waits for the WS #5/WS #7 cluster contract  
**Legacy invariant:** the existing DPDPA `SCREENING_DOMAINS` and
`run_screening_pass()` path remain unchanged.

## Decision record

Multi-framework screening uses Unified Control Clusters rather than separate
framework-native question sets. An organization answers one screening catalog for the
selected assessment, and the catalog is filtered to clusters containing at least one
selected, applicable control.

The catalog contains nine questions:

- Governance is split into governance/accountability/risk and third-party/workforce
  governance. The original 13-cluster group spans different evidence families and
  organizational owners.
- Security is split into identity/access safeguards and technical/application/physical
  safeguards. A single question across all 12 clusters would invite generic answers that
  cannot support reliable inference.
- Cross-border transfers and children's data remain separate. They have unrelated
  applicability tests, evidence, owners, and legal semantics. Both are conditional.

The screening result is an advisory signal, not a final audit verdict. It may pre-fill a
matching cluster question when the signal is high-confidence, but it must not manufacture
independent final verdicts for every member control.

## Approved question catalog

Question wording is deliberately framework-neutral, CISO-interview style, and asks for
specific operating evidence. `covers` is exhaustive and exclusive across the 52 authored
clusters in `CONTROL_CLUSTERS`.

<!-- catalog:start -->

### MFSD.GOVERNANCE_ACCOUNTABILITY — Governance, accountability and risk

**Question:** How does your organization govern privacy and information-security risk?
Describe leadership oversight, accountable roles, approved policies, risk and processing
inventories, privacy or security review in projects, independent assurance, and how these
arrangements are reviewed and improved. Include specific examples of ownership, approval,
review cadence, and recent decisions or audit outcomes.

**Covers:** `CLUSTER_001`, `CLUSTER_002`, `CLUSTER_003`, `CLUSTER_004`, `CLUSTER_005`,
`CLUSTER_035`, `CLUSTER_051`.

### MFSD.THIRD_PARTY_WORKFORCE — Third-party and workforce governance

**Question:** How do you manage privacy and security obligations involving suppliers,
processors, sub-processors, employees, and contractors? Describe due diligence, contract
requirements, ongoing supplier monitoring, acceptable-use and confidentiality duties,
training, and how non-compliance or changing risk is handled. Include recent evidence from
onboarding, reviews, training, or remediation.

**Covers:** `CLUSTER_010`, `CLUSTER_011`, `CLUSTER_012`, `CLUSTER_013`, `CLUSTER_033`,
`CLUSTER_036`.

### MFSD.IDENTITY_ACCESS — Identity and access safeguards

**Question:** How does your organization ensure that only authorized people and systems
can access sensitive information and critical services? Describe identity lifecycle,
access approvals and reviews, least privilege, authentication and credential protection,
privileged access, emergency access, and monitoring of administrative activity. Include
how joiner, mover, leaver, and high-risk access events work in practice.

**Covers:** `CLUSTER_006`, `CLUSTER_007`, `CLUSTER_008`, `CLUSTER_009`.

### MFSD.TECHNICAL_PHYSICAL_SECURITY — Technical, application and physical safeguards

**Question:** What technical and physical safeguards protect your systems, facilities,
and sensitive data? Describe secure configuration, endpoint and malware protection,
network segmentation, encryption and key management, logging and monitoring,
vulnerability testing, secure software development, and physical access controls. Include
the tools, owners, review frequencies, and recent evidence that these controls operate.

**Covers:** `CLUSTER_038`, `CLUSTER_039`, `CLUSTER_040`, `CLUSTER_041`, `CLUSTER_042`,
`CLUSTER_043`, `CLUSTER_044`, `CLUSTER_045`.

### MFSD.INCIDENT_RESPONSE — Incident detection, response and recovery

**Question:** How does your organization detect, assess, contain, document, communicate,
and recover from privacy or security incidents? Describe the response plan, workforce
reporting, monitoring and triage, evidence preservation, regulatory and individual
notification, continuity and recovery, lessons learned, and recent exercises or incidents.

**Covers:** `CLUSTER_014`, `CLUSTER_015`, `CLUSTER_016`, `CLUSTER_017`, `CLUSTER_018`,
`CLUSTER_019`, `CLUSTER_046`, `CLUSTER_047`.

### MFSD.DATA_PROTECTION — Transparency and data lifecycle protection

**Question:** How do you provide transparency and protect regulated data throughout its
lifecycle? Describe notices at and after collection, privacy contact and complaint
channels, data minimization, classification and handling, retention and secure deletion,
and any sector-specific scoping, de-identification, or minimum-necessary practices.
Include how these requirements are implemented and evidenced across systems and records.

**Covers:** `CLUSTER_020`, `CLUSTER_021`, `CLUSTER_022`, `CLUSTER_025`, `CLUSTER_034`,
`CLUSTER_048`, `CLUSTER_050`, `CLUSTER_052`.

### MFSD.CONSENT_RIGHTS — Consent, lawful use and individual rights

**Question:** How does your organization establish lawful and purpose-limited use of
personal data and enable individuals to exercise their rights? Describe consent capture,
records, granularity and withdrawal; access, correction, restriction, objection, erasure,
portability and representative requests; downstream notifications; disclosure accounting;
and safeguards for automated decisions. Include request channels, ownership, response
times, and recent evidence.

**Covers:** `CLUSTER_023`, `CLUSTER_024`, `CLUSTER_026`, `CLUSTER_027`, `CLUSTER_028`,
`CLUSTER_029`, `CLUSTER_030`, `CLUSTER_049`, `CLUSTER_053`.

### MFSD.CROSS_BORDER — Cross-border transfer governance

**Question:** Does your organization transfer regulated or sensitive data across national
borders, including through cloud providers, remote access, affiliates, or processors? If
so, describe how transfers are identified and approved, which countries and data are
involved, the legal or contractual safeguards used, localization restrictions, supplier
controls, and how transfer arrangements are monitored and reviewed.

**Covers:** `CLUSTER_031`.

**Applicability:** Ask only when `cross_border_transfers` is true or unknown and the
selected, applicable control set contains a member of this cluster. A confirmed false
signal suppresses the question; it does not create an implemented verdict.

### MFSD.CHILDREN_VULNERABLE — Children's data and age assurance

**Question:** Does your organization process personal data of children or other people
requiring age- or guardian-based protections? If so, describe age assurance, parental or
guardian authorization, elevated handling controls, prevention of harmful processing or
targeted monitoring, and how product or processing decisions account for the individual's
best interests. Include specific implementation and review evidence.

**Covers:** `CLUSTER_032`.

**Applicability:** Ask only when DPDPA is selected, `processes_children_data` is true or
unknown, and the selected, applicable control set contains a member of this cluster. A
confirmed false signal suppresses the question; it does not create an implemented verdict.

<!-- catalog:end -->

## Framework and scope filtering

The catalog is static, but the targets passed to screening are dynamic:

1. Start with the assessment's selected framework IDs and applicable control IDs.
2. For each authored cluster, retain only member controls that are both selected and
   applicable.
3. Remove a cluster when no member remains.
4. Remove a domain question when none of its covered clusters remains.
5. Apply the cross-border and children conditions above after framework/control filtering.
6. Preserve authored catalog order and cluster order.

Routing must use `assessment.frameworks == ["dpdpa"]` for the frozen legacy path and
`assessment.frameworks != ["dpdpa"]` for the future cluster path. Do not branch on
`assessment.is_multi_framework`; it is false for ISO-only and NIST-only assessments.

## Shared cluster contract required before implementation

WS #5 and WS #7 must settle one shared, prompt-independent contract before the new
screening service is built.

### Stable identity and scope

`ClusterScope` must expose:

- stable canonical `cluster_id`;
- authoritative `domain_group` from `CONTROL_CLUSTERS`, not tag re-inference;
- topic, primary question, guidance, and criticality;
- selected and applicable member controls, each carrying framework ID, control ID,
  description, criticality, and specificity delta;
- an explicit mapping between canonical cluster IDs and questionnaire IDs when the UI
  retains `SINGLE.<control_id>` identities.

This resolver must be shared by screening, questionnaire construction, analysis, and
scoring. The current behavior that converts every single-framework assessment into
`SINGLE.*` questions cannot be silently assumed compatible with `CLUSTER_*` screening
signals.

### Context assembly

`ClusterContext` should combine only context relevant to the target cluster:

- organization and risk profile;
- the matching domain-screening answer;
- cluster/questionnaire responses;
- desk-review findings and evidence;
- scoped document excerpts.

WS #5 measures the quality, cost, latency, and evidence-filtering behavior of this input.
Screening and the final analyzer should consume the same assembler rather than maintain
parallel expansion logic.

### Typed outputs and status adapters

Screening produces a separate advisory type:

```text
ClusterScreeningSignal
  cluster_id: str
  suggested_status: implemented | partial | not_implemented | not_applicable | unknown
  confidence: high | medium | low
  reasoning: str
  source_domain_id: str
  framework_ids: list[str]
  contract_version: str
  model_provenance: optional object
```

The existing scoring `Status` vocabulary is canonical internally. Explicit adapters map:

- `implemented` to questionnaire `fully_implemented` and legacy screening `compliant`;
- `partial` to `partially_implemented` and `partially_compliant`;
- `not_implemented` to `not_implemented` and `non_compliant`;
- `not_applicable` to questionnaire `not_applicable`;
- `unknown` to no pre-fill and legacy `not_assessed`.

`ClusterScreeningSignal` is not `ClusterVerdict`. A final verdict remains evidence-backed,
scored, and owned by the analyzer/scoring contract.

## Inference and pre-fill policy

- The model may return signals only for the supplied target cluster IDs.
- Missing targets are filled as `unknown`/low; unknown, duplicate, or out-of-scope IDs are
  rejected or ignored with an observable validation result.
- A domain answer can support different statuses for different covered clusters. The
  model must not copy one domain-level status across all targets.
- High-confidence `implemented` or `partial` signals may pre-fill only the matching
  questionnaire question through the stable identity mapping.
- `not_implemented`, `not_applicable`, `unknown`, and medium/low-confidence signals never
  auto-fill. They remain visible context for human review.
- Existing human or document-derived responses are never overwritten. Re-running
  screening is idempotent and must not duplicate response rows.
- A screening signal never expands directly into final member-control verdicts. Member
  expansion occurs only where the shared cluster contract explicitly needs framework
  views.
- Persisted results record the selected framework set and contract version so changing
  frameworks or mappings invalidates stale signals safely.

## Implementation sequencing

1. **Prerequisite correction:** make explicit cluster `domain_group` authoritative and
   settle canonical-cluster-to-question identity, including ISO-only, NIST-only, and the
   intentional singleton `SINGLE.ISO.A5.32`.
2. **WS #5 spike:** use `ClusterScope`, `ClusterContext`, the canonical status vocabulary,
   and a typed final-verdict schema. Record the go/no-go evidence required by the main
   plan.
3. **WS #7:** if the spike passes, implement the shared cluster analyzer contract. If it
   selects per-domain analysis instead, reuse that batching contract.
4. **Cluster screening:** add the new catalog/service as a thin producer of
   `ClusterScreeningSignal`, then wire routes, questionnaire modulation, and persistence.
5. **Legacy verification:** prove DPDPA-only screening remains behaviorally and
   structurally unchanged.

No cluster-screening prompt, parser, or persistence code should be implemented before
steps 1–3 settle the reusable contract. This avoids creating a second cluster-facing
model interface that WS #7 would immediately have to replace.

## Implementation acceptance criteria

- DPDPA-only uses the original nine `SD.*` questions, prompt, parser, persistence, and
  pre-fill policy unchanged.
- DPDPA+ISO, ISO+NIST, DPDPA+ISO+NIST, ISO-only, and NIST-only all route to the cluster
  path and see only relevant questions/targets.
- Every selected, applicable authored cluster is reachable from exactly one screening
  question; every intentional singleton is explicitly screened or exempted.
- Explicit domain groups remain stable at runtime, including `cross_border` and
  `children_vulnerable`.
- Parser validation covers hallucinated IDs, invalid values, missing targets, duplicates,
  and out-of-scope targets.
- Persistence tests cover every status/confidence combination, idempotent reruns, and
  preservation of human/document responses.
- Multi-framework questionnaire rendering shows inferred status, reasoning, source, and
  correct tier statistics when a pre-fill is eligible.
- Changing selected frameworks or applicable controls invalidates incompatible saved
  cluster screening results.
- The shared expansion path maps a persisted cluster answer only to selected member
  controls for downstream framework views.
- Existing DPDPA golden tests remain unchanged and green.

## Spot-check record

The complete catalog is mechanically checked for 52/52 coverage, exactly once. The
following ten-cluster adversarial sample spans all seven source domain groups:

| Cluster | Catalog question | Scope judgment |
|---|---|---|
| `CLUSTER_002` | Governance, accountability and risk | Roles and DPO ownership belong with governance accountability. |
| `CLUSTER_011` | Third-party and workforce governance | Processor contract terms belong with supplier governance. |
| `CLUSTER_035` | Governance, accountability and risk | Risk register and threat intelligence feed organizational risk oversight. |
| `CLUSTER_007` | Identity and access safeguards | Identity lifecycle and access reviews are core IAM practices. |
| `CLUSTER_041` | Technical, application and physical safeguards | Cryptography is a technical safeguard and is explicitly prompted. |
| `CLUSTER_017` | Incident detection, response and recovery | Regulatory notification is part of the incident lifecycle. |
| `CLUSTER_025` | Transparency and data lifecycle protection | Retention, erasure and deletion are lifecycle controls. |
| `CLUSTER_029` | Consent, lawful use and individual rights | Consent governance and records are explicitly covered. |
| `CLUSTER_031` | Cross-border transfer governance | It has distinct transfer-law applicability and evidence. |
| `CLUSTER_032` | Children's data and age assurance | It has distinct age/guardian applicability and safeguards. |

Each sampled cluster is reachable by one question, is semantically in scope for that
question, and is not duplicated elsewhere in the catalog.
