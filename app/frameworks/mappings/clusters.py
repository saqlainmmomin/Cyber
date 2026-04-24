"""
Unified Control Cluster (UCC) mapping data.

Maps overlapping controls across frameworks into clusters. Each cluster
represents a single assessable topic — the assessment asks one primary
question per cluster, with framework-specific follow-ups for deltas.

This file is the source of truth for cross-framework de-duplication.
Currently contains DPDPA mappings only; other frameworks will be added
as their definitions are generated (Codex workflow).

Schema per cluster:
    cluster_id: str         — stable identifier (e.g. "UCC.CONSENT.001")
    topic: str              — human-readable topic
    tags: list[str]         — semantic tags (union of member controls)
    primary_question: str   — merged question covering the baseline
    primary_guidance: str   — guidance for the primary question
    controls: list[dict]    — member controls:
        framework: str      — framework id
        control: str        — control id within that framework
        delta: str | None   — what this framework uniquely adds beyond the baseline
"""

# ── Cluster definitions ───────────────────────────────────────────────────
#
# V1: DPDPA-only (singleton clusters). Multi-framework clusters will be
# added when ISO 27001, GDPR, HIPAA, NIST CSF, and PCI-DSS definitions
# are generated. The cluster_engine handles unmatched controls as singletons,
# so this file only needs to contain clusters where cross-framework mapping
# actually de-duplicates something.

CONTROL_CLUSTERS: list[dict] = [
    # ── Governance & Oversight ─────────────────────────────────────────
    # (Will be populated with cross-framework mappings, e.g.:
    #   DPDPA CH4.SDF.1 (DPO) ↔ GDPR Art.37 (DPO) ↔ HIPAA Privacy Officer)

    # ── Consent & Lawful Basis ─────────────────────────────────────────

    # ── Data Subject Rights ────────────────────────────────────────────

    # ── Security Safeguards ────────────────────────────────────────────

    # ── Breach / Incident Response ─────────────────────────────────────

    # ── Cross-Border Transfers ─────────────────────────────────────────

    # ── Children & Vulnerable Persons ──────────────────────────────────
]
