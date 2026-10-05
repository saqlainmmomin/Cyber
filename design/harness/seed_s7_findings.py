"""Deterministic S7 findings specimens for the approved mockup states."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from app.models.action import Action
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.evidence import Evidence, EvidenceVersion
from app.models.finding import Finding
from design.harness.seed_s4 import SEED_ACTOR, _audit


SCREEN_STATES = {
    "b5-findings": ("default", "create", "empty"),
    "b5-finding-card": (
        "open",
        "in-progress",
        "no-evidence",
        "verify",
        "verified",
        "legacy",
        "source-changed",
        "migrated",
        "add-action",
    ),
    "b7-dark-dense": ("dense",),
}

OWNER = "Meridian infrastructure"
BACKUP_TITLE = "Backups are not encrypted at rest"
BACKUP_DESCRIPTION = (
    "Production databases are encrypted. Nightly backups to the secondary region are not, "
    "so a copy of customer records sits unencrypted."
)


def _at(day: int, hour: int = 12) -> datetime:
    return datetime(2026, 9, day, hour, tzinfo=timezone.utc)


def _date(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, tzinfo=timezone.utc)


def _history_entry(
    action: str,
    actor: str,
    timestamp: str,
    *,
    notes: str | None = None,
    changes: dict | None = None,
    evidence: dict | None = None,
) -> dict:
    entry = {
        "actor": actor,
        "action": action,
        "timestamp": timestamp,
        "notes": notes,
        "changes": changes or {},
    }
    if evidence is not None:
        entry["evidence"] = evidence
    return entry


def _created(title: str, *, owner: str | None, target: datetime | None) -> dict:
    return _history_entry(
        "created",
        SEED_ACTOR,
        "2026-09-22T09:00:00+00:00",
        changes={
            "title": {"from": None, "to": title},
            "owner": {"from": None, "to": owner},
            "target_date": {"from": None, "to": target.date().isoformat() if target else None},
            "status": {"from": None, "to": "open"},
        },
    )


def _started() -> dict:
    return _history_entry(
        "status_changed",
        "consultant:Arjun Mehta",
        "2026-09-26T10:00:00+00:00",
        changes={"status": {"from": "open", "to": "in_progress"}},
    )


def _closure(evidence: dict) -> dict:
    return _history_entry(
        "closed",
        "consultant:Arjun Mehta",
        "2026-09-28T11:00:00+00:00",
        changes={"status": {"from": "in_progress", "to": "closed"}},
        evidence=evidence,
    )


def _verified() -> dict:
    return _history_entry(
        "verified",
        SEED_ACTOR,
        "2026-09-30T12:00:00+00:00",
        changes={"status": {"from": "closed", "to": "verified"}},
    )


def _conclusion(
    db,
    assessment,
    conclusion_id: str,
    requirement_id: str,
    *,
    decided: str = "approved",
    reopened: bool = False,
) -> Conclusion:
    conclusion = Conclusion(
        id=conclusion_id,
        assessment_id=assessment.id,
        framework_id="dpdpa",
        requirement_id=requirement_id,
        outcome="partially_compliant",
        rationale="Production databases are encrypted, but backup encryption is incomplete.",
        evidence_summary="Backup configuration evidence was reviewed.",
        gaps_identified="Nightly backups to the secondary region are not encrypted at rest.",
        risk_level="medium",
        recommended_action="Enable encryption on backup storage.",
        ai_proposed=False,
        created_at=_at(15),
        updated_at=_at(20),
    )
    db.add(conclusion)
    db.flush()
    db.add(
        ConclusionRevision(
            id=f"revision-proposed-{conclusion_id}",
            conclusion_id=conclusion_id,
            actor="system:analysis",
            action="proposed",
            citations_json="[]",
            created_at=_at(15),
        )
    )
    db.add(
        ConclusionRevision(
            id=f"revision-{decided}-{conclusion_id}",
            conclusion_id=conclusion_id,
            actor=SEED_ACTOR,
            action=decided,
            created_at=_at(24),
        )
    )
    if reopened:
        db.add(
            ConclusionRevision(
                id=f"revision-reopened-{conclusion_id}",
                conclusion_id=conclusion_id,
                actor=SEED_ACTOR,
                action="reopened",
                created_at=_at(29),
            )
        )
    db.flush()
    return conclusion


def _evidence_rows(db, assessment, engagement) -> dict[str, dict]:
    rows = {}
    for index, filename in enumerate(("backup_encryption_config.pdf", "kms_key_policy.pdf")):
        digest = f"{index + 1:064x}"
        evidence_id = f"evidence-s7-{assessment.id}-{index}"
        version_id = f"evidence-version-s7-{assessment.id}-{index}"
        db.add(
            Evidence(
                id=evidence_id,
                engagement_id=engagement.id,
                assessment_id=assessment.id,
                original_filename=filename,
                storage_path=f"evidence/{engagement.id}/{filename}",
                file_hash_sha256=digest,
                file_size_bytes=2048,
                mime_type="application/pdf",
                status="active",
                uploaded_by=SEED_ACTOR,
                created_at=_at(20 + index),
            )
        )
        db.add(
            EvidenceVersion(
                id=version_id,
                evidence_id=evidence_id,
                version_number=index + 1,
                storage_path=f"evidence/{engagement.id}/{filename}",
                file_hash_sha256=digest,
                file_size_bytes=2048,
                status="active",
                original_filename=filename,
                mime_type="application/pdf",
                created_at=_at(20 + index),
            )
        )
        rows[filename] = {
            "evidence_id": evidence_id,
            "evidence_version_id": version_id,
            "version_number": index + 1,
            "sha256": digest,
            "filename": filename,
        }
    db.flush()
    return rows


def _action(
    action_id: str,
    finding_id: str,
    title: str,
    *,
    owner: str | None,
    target: datetime | None,
    status: str,
    history: list[dict],
) -> Action:
    return Action(
        id=action_id,
        finding_id=finding_id,
        title=title,
        owner=owner,
        responsibility="client" if owner else None,
        target_date=target,
        status=status,
        history_json=json.dumps(history),
        created_at=_at(22),
        updated_at=_at(29),
    )


def _finding(
    db,
    assessment,
    engagement,
    *,
    finding_id: str,
    conclusion_id: str,
    requirement_id: str,
    title: str,
    description: str,
    severity: str,
    priority: int,
    status: str,
    actions: list[Action],
    origin: str = "consultant",
) -> Finding:
    _conclusion(db, assessment, conclusion_id, requirement_id)
    finding = Finding(
        id=finding_id,
        assessment_id=assessment.id,
        conclusion_id=conclusion_id,
        title=title,
        description=description,
        business_impact="Unencrypted backups increase the impact of a storage compromise.",
        recommendation="Enable encryption on backup storage and test restore procedures.",
        severity=severity,
        priority=priority,
        status=status,
        created_at=_at(22),
        updated_at=_at(29),
    )
    db.add(finding)
    db.flush()
    for action in actions:
        action.finding_id = finding.id
        db.add(action)
    if origin == "consultant":
        db.add(
            _audit(
                f"audit-finding-created-{finding_id}",
                action="finding_created",
                entity_type="finding",
                entity_id=finding_id,
                created_at=_at(22),
                metadata={"assessment_id": assessment.id, "conclusion_id": conclusion_id},
            )
        )
    db.flush()
    return finding


def _make_backup_action(
    finding_id: str,
    *,
    status: str,
    history: list[dict],
    owner: str | None = OWNER,
    target: datetime | None = _date(2026, 11, 30),
) -> Action:
    return _action(
        f"action-{finding_id}-primary",
        finding_id,
        "Enable encryption on backup storage",
        owner=owner,
        target=target,
        status=status,
        history=history,
    )


def _backup_state(db, assessment, engagement, state: str) -> None:
    finding_id = f"finding-s7-backups-{assessment.id}"
    conclusion_id = f"conclusion-s7-backups-{assessment.id}"
    evidence = _evidence_rows(db, assessment, engagement) if state != "no-evidence" else {}
    closure_evidence = evidence.get("backup_encryption_config.pdf")
    created = _created("Enable encryption on backup storage", owner=OWNER, target=_date(2026, 11, 30))
    history = [created]
    status = "open"
    finding_status = "open"
    origin = "consultant"
    reopened = False

    if state in {"in-progress", "no-evidence", "source-changed", "add-action"}:
        started = _started()
        if state == "add-action":
            started["notes"] = "Waiting on the key rotation window."
        history.append(started)
        status = finding_status = "in_progress"
        reopened = state == "source-changed"
    elif state == "verify":
        history.extend([_started(), _closure(closure_evidence)])
        status = "closed"
        finding_status = "in_progress"
    elif state == "verified":
        history.extend([_started(), _closure(closure_evidence), _verified()])
        status = "verified"
        finding_status = "resolved"
    elif state == "legacy":
        history.append(_started())
        status = "closed"
        finding_status = "in_progress"
    elif state == "migrated":
        history = [
            _history_entry(
                "imported",
                "system:migration",
                "2026-08-12T09:00:00+00:00",
                changes={"status": {"from": None, "to": "open"}},
            )
        ]
        status = finding_status = "open"
        origin = "migrated"
    elif state != "open":
        raise ValueError(state)

    actions = [
        _make_backup_action(
            finding_id,
            status=status,
            history=history,
            owner=None if state == "migrated" else OWNER,
            target=None if state == "migrated" else _date(2026, 11, 30),
        )
    ]
    if state == "open":
        actions.append(
            _action(
                f"action-{finding_id}-secondary",
                finding_id,
                "Add a restore test for encrypted backups",
                owner=OWNER,
                target=_date(2026, 12, 31),
                status="open",
                history=[_created("Add a restore test for encrypted backups", owner=OWNER, target=_date(2026, 12, 31))],
            )
        )
    _finding(
        db,
        assessment,
        engagement,
        finding_id=finding_id,
        conclusion_id=conclusion_id,
        requirement_id="CH2.SECURITY.1",
        title=BACKUP_TITLE,
        description=BACKUP_DESCRIPTION,
        severity="medium",
        priority=2,
        status=finding_status,
        actions=actions,
        origin=origin,
    )
    if reopened:
        conclusion = db.get(Conclusion, conclusion_id)
        db.add(
            ConclusionRevision(
                id=f"revision-reopened-{conclusion_id}",
                conclusion_id=conclusion.id,
                actor=SEED_ACTOR,
                action="reopened",
                created_at=_at(29),
            )
        )
        db.flush()


def _eligible(db, assessment) -> None:
    _conclusion(db, assessment, f"conclusion-s7-eligible-{assessment.id}", "CH2.SECURITY.1")


def _list_findings(db, assessment, engagement, *, dense: bool = False) -> None:
    rows = (
        ("consent", "CH2.CONSENT.3", "No in-app consent withdrawal", "high", 1, "open", "open", "Client", "30 Nov 2026"),
        ("mfa", "CH2.SECURITY.2", "Three service accounts exempt from MFA", "high", 1, "in_progress", "in_progress", "Client", "15 Nov 2026"),
        ("dr", "CH2.SECURITY.3", "DR failover exceeded the 4-hour RTO", "medium", 2, "in_progress", "in_progress", "Shared", "31 Dec 2026"),
        ("notice", "CH2.NOTICE.1", "Privacy notice available in English only", "medium", 2, "resolved", "verified", "Client", "Done"),
    )
    if dense:
        rows += (
            ("processor", "CH2.SECURITY.4", "Processor contracts lack deletion clauses", "medium", 2, "open", "open", "Shared", "15 Dec 2026"),
            ("retention", "CH2.MINIMIZE.1", "No retention schedule for support tickets", "low", 3, "open", "open", "Client", "15 Dec 2026"),
            ("children", "CH2.CHILD.1", "Age gate for children's data not verified", "low", 3, "open", "open", "Shared", "15 Dec 2026"),
            ("cookie", "CH2.NOTICE.2", "Cookie banner pre-selects analytics", "low", 3, "in_progress", "in_progress", "Client", "15 Dec 2026"),
            ("grievance", "CH3.GRIEVANCE.1", "Grievance officer contact outdated on website", "low", 3, "resolved", "verified", "Client", "Done"),
        )
        rows = rows[:8]
    for key, requirement_id, title, severity, priority, finding_status, action_status, owner, target_label in rows:
        target = None if target_label == "Done" else datetime.strptime(target_label, "%d %b %Y").replace(tzinfo=timezone.utc)
        action_history = [_created(f"Fix: {title}", owner=owner, target=target)]
        if action_status != "open":
            action_history.append(_started())
        if action_status == "verified":
            action_history.extend(
                [
                    _closure({
                        "evidence_id": "evidence-s7-list",
                        "evidence_version_id": "version-s7-list",
                        "version_number": 1,
                        "sha256": "0" * 64,
                        "filename": "policy.pdf",
                    }),
                    _verified(),
                ]
            )
        _finding(
            db,
            assessment,
            engagement,
            finding_id=f"finding-s7-{key}-{assessment.id}",
            conclusion_id=f"conclusion-s7-{key}-{assessment.id}",
            requirement_id=requirement_id,
            title=title,
            description=title,
            severity=severity,
            priority=priority,
            status=finding_status,
            actions=[
                _action(
                    f"action-s7-{key}-{assessment.id}",
                    f"finding-s7-{key}-{assessment.id}",
                    f"Fix: {title}",
                    owner=owner,
                    target=target,
                    status=action_status,
                    history=action_history,
                )
            ],
        )


def apply(db, screen: str, state: str, assessment, engagement, data) -> dict:
    if screen == "b5-findings":
        if state in {"default", "create"}:
            _eligible(db, assessment)
            _list_findings(db, assessment, engagement)
        return {
            "data_state": "database",
            "note": "Approved conclusion and four findings seeded as database rows."
            if state != "empty"
            else "No approved conclusion or finding rows seeded.",
        }
    if screen == "b5-finding-card":
        _backup_state(db, assessment, engagement, state)
        return {"data_state": "database", "note": f"Finding card seeded in the {state} state."}
    if screen == "b7-dark-dense":
        _list_findings(db, assessment, engagement, dense=True)
        return {"data_state": "database", "note": "Eight findings seeded for the dense dark specimen."}
    raise ValueError(screen)


def route(screen: str, state: str, assessment_id: str) -> str:
    """The live findings route: list, create form (?create=), finding detail (?finding=)."""
    base = f"/assessments/{assessment_id}/findings"
    if screen == "b5-findings" and state == "create":
        return f"{base}?create=conclusion-s7-eligible-{assessment_id}"
    if screen == "b5-finding-card":
        detail = f"{base}?finding=finding-s7-backups-{assessment_id}"
        return detail + ("&add=1" if state == "add-action" else "")
    return base
