"""Deterministic consultant review queue over Conclusion cards."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.frameworks.mappings.clusters import CONTROL_CLUSTERS
from app.frameworks.registry import FrameworkRegistry
from app.services import conclusion_review
from app.services.requirement_card import ClaimView

QUEUE_RISK_LEVELS = ("low", "medium", "high", "critical")
RISK_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
STATE_RANK = {"pending": 0, "rejected": 1, "approved": 2, "edited": 2}
QUEUE_FLAGS = ("inconsistency", "unsupported_assertion", "divergence")


@dataclass(frozen=True)
class QueueEntry:
    card: conclusion_review.ConclusionCard
    risk: str
    flags: tuple[str, ...]
    key: tuple


@dataclass(frozen=True)
class QueueGroup:
    group_key: str
    cluster_id: str | None
    topic: str | None
    entries: tuple[QueueEntry, ...]
    shared_claims: tuple[ClaimView, ...]

    @property
    def shared(self) -> bool:
        return len(self.entries) > 1


def deterministic_queue_risk(criticality: str, outcome: str) -> str:
    base = criticality if criticality in QUEUE_RISK_LEVELS else "medium"
    if outcome in ("compliant", "not_applicable"):
        return "low"
    if outcome == "non_compliant":
        return base
    return QUEUE_RISK_LEVELS[max(0, QUEUE_RISK_LEVELS.index(base) - 1)]


def queue_risk(framework_id: str, requirement_id: str, outcome: str) -> str:
    framework = FrameworkRegistry.get_or_none(framework_id)
    control = framework.get_control(requirement_id) if framework is not None else None
    if control is None:
        return "medium"
    return deterministic_queue_risk(control.criticality, outcome)


def queue_flags(card) -> tuple[str, ...]:
    requirement = card.requirement
    if requirement is None:
        return ()
    flags = []
    if "model_criteria_inconsistency" in requirement.flags or requirement.contradictions:
        flags.append("inconsistency")
    if requirement.unsupported_assertion:
        flags.append("unsupported_assertion")
    if requirement.divergence is not None and not requirement.divergence.acknowledged:
        flags.append("divergence")
    return tuple(flag for flag in QUEUE_FLAGS if flag in flags)


def _topic_by_cluster() -> dict[str, str]:
    return {
        cluster["cluster_id"]: cluster["topic"]
        for cluster in CONTROL_CLUSTERS
        if cluster.get("cluster_id") and cluster.get("topic")
    }


def build_queue(cards) -> list[QueueGroup]:
    topic_by_cluster = _topic_by_cluster()
    entries = []
    for position, card in enumerate(cards):
        flags = queue_flags(card)
        risk = queue_risk(
            card.conclusion.framework_id,
            card.conclusion.requirement_id,
            card.conclusion.outcome,
        )
        key = (
            STATE_RANK.get(card.state, 0),
            RISK_RANK[risk],
            tuple(flag not in flags for flag in QUEUE_FLAGS),
            position,
        )
        entries.append(QueueEntry(card=card, risk=risk, flags=flags, key=key))

    by_cluster: dict[str, list[QueueEntry]] = {}
    singles: list[QueueEntry] = []
    for entry in entries:
        cluster_id = entry.card.conclusion.cluster_id
        if cluster_id:
            by_cluster.setdefault(cluster_id, []).append(entry)
        else:
            singles.append(entry)

    groups: list[QueueGroup] = []
    for cluster_id, members in by_cluster.items():
        ordered = tuple(sorted(members, key=lambda entry: entry.key))
        if len(ordered) < 2:
            entry = ordered[0]
            groups.append(
                QueueGroup(
                    group_key=f"single-{entry.card.conclusion.id}",
                    cluster_id=None,
                    topic=None,
                    entries=(entry,),
                    shared_claims=(),
                )
            )
            continue
        seen_claims: set[str] = set()
        shared_claims = []
        for entry in ordered:
            requirement = entry.card.requirement
            for claim in requirement.claims if requirement is not None else ():
                if claim.claim_id not in seen_claims:
                    seen_claims.add(claim.claim_id)
                    shared_claims.append(claim)
        groups.append(
            QueueGroup(
                group_key=cluster_id,
                cluster_id=cluster_id,
                topic=topic_by_cluster.get(cluster_id),
                entries=ordered,
                shared_claims=tuple(shared_claims),
            )
        )

    for entry in singles:
        groups.append(
            QueueGroup(
                group_key=f"single-{entry.card.conclusion.id}",
                cluster_id=None,
                topic=None,
                entries=(entry,),
                shared_claims=(),
            )
        )
    groups.sort(key=lambda group: group.entries[0].key)
    return groups


def review_queue(db: Session, assessment_id: str) -> list[QueueGroup]:
    return build_queue(conclusion_review.conclusion_cards(db, assessment_id))
