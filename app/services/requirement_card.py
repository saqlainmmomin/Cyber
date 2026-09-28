"""Read-only requirement-card views for grounded analysis proposals."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date

from sqlalchemy import literal_column, select
from sqlalchemy.orm import Session

from app.frameworks.registry import FrameworkRegistry
from app.models.analysis_run import AnalysisRun
from app.models.assessment import Assessment
from app.models.audit_event import AuditEvent
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.evidence import Evidence, EvidenceVersion
from app.services import desk_review_v2, report_basis
from app.services.citations import resolve_citations

FALLBACK_CRITERIA_LABEL = "Judged against the control description; no approved test criteria yet"
APPROVED_CRITERIA_LABEL = "Judged against approved test criteria"
V1_SOURCE_LABEL = "Proposed by the v1 analysis: no criteria checklist or verified claims are available for this requirement."
NO_RUN_LABEL = "No analysis run is linked to this conclusion."
REASON_COMPLIANT = "Every test criterion is met by at least one verified claim."
REASON_SCOPE_EXCLUDED = "Outside the recorded assessment scope."
NO_RESPONSE_LABEL = "No confirmed questionnaire response."
NO_CLAIMS_LABEL = "No verified claim addresses this requirement."
UNSUPPORTED_ASSERTION_LABEL = "Unsupported assertion: no verified evidence supports this response or proposal."
SHARED_EVIDENCE_LABEL = "Evidence for this group is shown once, above."
MISSING_EVIDENCE_RFI_NOTE = "Approved insufficient-evidence conclusions are added to the next RFI version."
V1_MISSING_EVIDENCE_LABEL = "Suggested by the framework's evidence request list."
DIVERGENCE_SENTENCE = (
    "The same verified claims were judged Compliant under {compliant} and "
    "Non-Compliant under {non_compliant}. Requirements can legitimately differ; "
    "acknowledge that you have reviewed this before approving."
)
DIVERGENCE_ACK_REQUIRED_MESSAGE = "Acknowledge the framework divergence note before approving this conclusion."
NO_DIVERGENCE_MESSAGE = "This conclusion has no framework divergence note to acknowledge."
DIVERGENCE_STALE_MESSAGE = "The framework divergence note changed since you loaded it. Reload the card and review it again."
CONCLUSION_NOT_FOUND_MESSAGE = "Conclusion not found"
DIVERGENCE_ACK_ACTION = "conclusion.divergence_acknowledged"
AUDIT_ENTITY_TYPE = "conclusion"
ACK_NOTE_MAX_CHARS = 500
ANSWER_SOURCE_LABELS = {"human": "Entered in the questionnaire"}
CRITERION_SYMBOLS = {"met": "✓", "not_met": "✗", "no_evidence": "?"}
CLAIM_KINDS = ("design", "operating", "context")
DATE_FIELDS = ("effective_date", "document_date")
SPAN_CONTEXT_CHARS = 1500
WHOLE_PREVIEW_CHARS = 3000
SPAN_INVALID_MESSAGE = "Citation span not found in this evidence version."
VERSION_NOT_FOUND_MESSAGE = "Evidence version not found"
_SPAN_REF = re.compile(r"^chars:(0|[1-9]\d*)-(0|[1-9]\d*)$")
_V1_GAP_OUTCOMES = {"partially_compliant", "non_compliant", "insufficient_evidence"}

CHIPS = {
    "currency:current": ("Current evidence version", "ok"),
    "currency:superseded": ("Cites a superseded evidence version", "warn"),
    "currency:none": ("No cited evidence", "neutral"),
    "period:not_recorded": ("Assessment period not recorded", "neutral"),
    "period:dated": ("Evidence dated on or before the cut-off", "ok"),
    "period:after_cutoff": ("Evidence dated after the cut-off", "warn"),
    "period:undated": ("Evidence has no document date", "warn"),
    "period:unknown": (
        "Document dates unavailable: desk review changed since this analysis",
        "neutral",
    ),
    "scope:in_scope": ("In recorded scope", "ok"),
    "scope:excluded": ("Outside recorded scope", "warn"),
    "scope:not_recorded": ("Scope not recorded", "neutral"),
    "kind:design": ("Design evidence", "neutral"),
    "kind:operating": ("Operating evidence", "neutral"),
    "kind:context": ("Context only", "neutral"),
    "support:needs_review": ("A cited claim is only partly supported by its quote", "warn"),
    "support:image": ("Includes text read from an image", "neutral"),
    "analysis:incomplete": ("Analysis incomplete: not judged after one retry", "warn"),
    "grounding:grounded": ("Quote found in the evidence", "ok"),
    "grounding:ungrounded": ("Quote not found in the evidence", "warn"),
}


@dataclass(frozen=True)
class ClaimView:
    claim_id: str
    statement: str
    quote: str
    kind: str
    filename: str
    href: str | None
    needs_review: bool
    derived_from_image: bool


@dataclass(frozen=True)
class CriterionRow:
    criterion_id: str
    statement: str
    kind: str
    result: str
    symbol: str
    claim_ids: tuple[str, ...]
    met_without_claim: bool


@dataclass(frozen=True)
class ResponseView:
    question_id: str
    answer: str
    answer_label: str
    source_label: str


@dataclass(frozen=True)
class Contradiction:
    claim_id: str
    note: str


@dataclass(frozen=True)
class QualityChip:
    key: str
    label: str
    tone: str


@dataclass(frozen=True)
class MissingEvidence:
    document_type: str
    label: str
    what_it_would_show: str


@dataclass(frozen=True)
class DivergenceNote:
    cluster_id: str
    analysis_run_id: str
    compliant: tuple[tuple[str, str], ...]
    non_compliant: tuple[tuple[str, str], ...]
    sentence: str
    acknowledged: bool
    acknowledged_by: str | None
    acknowledged_at: object | None
    note: str | None


@dataclass(frozen=True)
class CardContext:
    assessment: object
    runs: dict[str, AnalysisRun]
    envelopes: dict[str, dict]
    basis: report_basis.ReportBasis
    source_dates: dict[str, date | None]
    claim_set_id: str | None
    acks: dict[tuple[str, str, str], AuditEvent]


@dataclass(frozen=True)
class SpanView:
    evidence_id: str
    version_id: str
    filename: str
    version_number: int
    is_current: bool
    location_ref: str
    whole: bool
    available: bool
    before: str
    span: str
    after: str
    truncated_before: bool
    truncated_after: bool


@dataclass(frozen=True)
class RequirementCard:
    source: str
    analysis_run_id: str | None
    proposed_outcome: str | None
    reason: str | None
    criteria_source: str | None
    criteria_label: str | None
    criteria: tuple[CriterionRow, ...]
    claims: tuple[ClaimView, ...]
    response: ResponseView | None
    contradictions: tuple[Contradiction, ...]
    unsupported_assertion: bool
    analysis_incomplete: bool
    flags: tuple[str, ...]
    quality: tuple[QualityChip, ...]
    missing_evidence: tuple[MissingEvidence, ...]
    missing_evidence_label: str | None
    divergence: DivergenceNote | None


class RequirementCardError(Exception):
    status_code = 400

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _safe_json(raw: str | None) -> dict | None:
    try:
        value = json.loads(raw or "")
    except (TypeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _source_dates(claim_set) -> dict[str, date | None]:
    dates: dict[str, date | None] = {}
    if claim_set is None:
        return dates
    for source in claim_set.sources:
        fields = ((source.get("metadata") or {}).get("fields") or []) if isinstance(source, dict) else []
        source_date = None
        for field_name in DATE_FIELDS:
            field = next(
                (item for item in fields if isinstance(item, dict) and item.get("name") == field_name),
                None,
            )
            iso_date = field.get("iso_date") if field else None
            if iso_date:
                try:
                    source_date = date.fromisoformat(iso_date)
                except (TypeError, ValueError):
                    source_date = None
                break
        if isinstance(source, dict) and source.get("source_id"):
            dates[source["source_id"]] = source_date
    return dates


def load_context(db: Session, assessment, proposals, conclusion_ids) -> CardContext:
    proposal_list = [proposal for proposal in proposals if proposal is not None]
    run_ids = {proposal.analysis_run_id for proposal in proposal_list if proposal.analysis_run_id}
    runs = {}
    if run_ids:
        runs = {
            run.id: run
            for run in db.execute(select(AnalysisRun).where(AnalysisRun.id.in_(run_ids))).scalars().all()
        }

    envelopes: dict[str, dict] = {}
    for run_id, run in runs.items():
        envelope = _safe_json(run.claims_json)
        if envelope is not None:
            envelopes[run_id] = envelope

    claim_set = None
    if any(envelope.get("analysis_pipeline_version") == "v2" for envelope in envelopes.values()):
        claim_set = desk_review_v2.load_claim_set(db, assessment.id)

    acknowledgement_by_key: dict[tuple[str, str, str], AuditEvent] = {}
    ids = [conclusion_id for conclusion_id in conclusion_ids if conclusion_id]
    if ids:
        events = db.execute(
            select(AuditEvent)
            .where(
                AuditEvent.action == DIVERGENCE_ACK_ACTION,
                AuditEvent.entity_type == AUDIT_ENTITY_TYPE,
                AuditEvent.entity_id.in_(ids),
            )
            .order_by(AuditEvent.created_at, literal_column("audit_events.rowid"))
        ).scalars().all()
        for event in events:
            metadata = _safe_json(event.metadata_json)
            if not metadata:
                continue
            run_id = metadata.get("analysis_run_id")
            cluster_id = metadata.get("cluster_id")
            if not isinstance(run_id, str) or not isinstance(cluster_id, str):
                continue
            acknowledgement_by_key.setdefault((event.entity_id, run_id, cluster_id), event)

    return CardContext(
        assessment=assessment,
        runs=runs,
        envelopes=envelopes,
        basis=report_basis.current_basis(db, assessment),
        source_dates=_source_dates(claim_set),
        claim_set_id=claim_set.claim_set_id if claim_set is not None else None,
        acks=acknowledgement_by_key,
    )


def _entry_for(context: CardContext, proposal: ConclusionRevision | None) -> tuple[str, str, dict, dict] | None:
    if proposal is None or not proposal.analysis_run_id:
        return None
    run = context.runs.get(proposal.analysis_run_id)
    envelope = context.envelopes.get(proposal.analysis_run_id)
    if run is None or envelope is None or not isinstance(envelope.get("claims"), list):
        return None
    entry = next(
        (
            claim
            for claim in envelope["claims"]
            if isinstance(claim, dict) and claim.get("revision_id") == proposal.id
        ),
        None,
    )
    if entry is None or not isinstance(entry.get("item"), dict):
        return None
    source = "v2" if envelope.get("analysis_pipeline_version") == "v2" else "v1"
    return source, run.id, envelope, entry


def _claim_view(claim: dict) -> ClaimView:
    citation = claim.get("citation")
    href = None
    if isinstance(citation, dict):
        version_id = citation.get("evidence_version_id")
        location_ref = citation.get("location_ref")
        if version_id and location_ref:
            href = f"/evidence-versions/{version_id}/span?ref={location_ref}#cited-span"
    return ClaimView(
        claim_id=str(claim.get("claim_id", "")),
        statement=claim.get("statement") or "",
        quote=claim.get("quote") or "",
        kind=claim.get("kind") or "",
        filename=claim.get("filename") or "",
        href=href,
        needs_review=bool(claim.get("needs_review")),
        derived_from_image=bool(claim.get("derived_from_image")),
    )


def _criterion_rows(item: dict, cited_ids: set[str]) -> tuple[CriterionRow, ...]:
    rows = []
    for criterion in item.get("criteria") or ():
        if not isinstance(criterion, dict):
            continue
        result = criterion.get("result") or ""
        claim_ids = tuple(
            claim_id
            for claim_id in criterion.get("claim_ids") or ()
            if isinstance(claim_id, str) and claim_id in cited_ids
        )
        rows.append(
            CriterionRow(
                criterion_id=criterion.get("criterion_id") or "",
                statement=criterion.get("statement") or "",
                kind=criterion.get("kind") or "",
                result=result,
                symbol=CRITERION_SYMBOLS.get(result, "?"),
                claim_ids=claim_ids,
                met_without_claim=criterion.get("original_result") == "met",
            )
        )
    return tuple(rows)


def _response_view(item: dict) -> ResponseView | None:
    response = item.get("response")
    if not isinstance(response, dict) or not response.get("answer"):
        return None
    answer = str(response["answer"])
    source = response.get("answer_source") or "human"
    return ResponseView(
        question_id=response.get("question_id") or "",
        answer=answer,
        answer_label=answer.replace("_", " ").capitalize(),
        source_label=ANSWER_SOURCE_LABELS.get(source, f"Source: {source}"),
    )


def _missing_evidence_v2(framework_id: str, item: dict) -> tuple[MissingEvidence, ...]:
    framework = FrameworkRegistry.get_or_none(framework_id)
    requests = {
        request.document_type: request.label
        for request in framework.evidence_requests
    } if framework is not None else {}
    return tuple(
        MissingEvidence(
            document_type=request.get("document_type") or "",
            label=requests.get(
                request.get("document_type"),
                (request.get("document_type") or "").replace("_", " ").capitalize(),
            ),
            what_it_would_show=request.get("what_it_would_show") or "",
        )
        for request in item.get("missing_evidence") or ()
        if isinstance(request, dict)
    )


def _missing_evidence_v1(framework_id: str, requirement_id: str, outcome: str) -> tuple[MissingEvidence, ...]:
    if outcome not in _V1_GAP_OUTCOMES:
        return ()
    framework = FrameworkRegistry.get_or_none(framework_id)
    if framework is None:
        return ()
    return tuple(
        MissingEvidence(request.document_type, request.label, request.reason)
        for request in framework.evidence_requests
        if requirement_id in request.maps_to
    )[:3]


def _currency_chip(citations: list[dict]) -> QualityChip:
    resolved = [citation for citation in citations if citation.get("resolved")]
    if not resolved:
        key = "currency:none"
    elif any(not citation.get("is_current") for citation in resolved):
        key = "currency:superseded"
    else:
        key = "currency:current"
    label, tone = CHIPS[key]
    return QualityChip(key, label, tone)


def _scope_chip(envelope: dict, item: dict, requirement_id: str, *, source: str) -> QualityChip:
    if source == "v2":
        inputs = envelope.get("inputs") or {}
        applicable = inputs.get("applicable_requirements")
        excluded = bool(item.get("scope_excluded"))
        if isinstance(applicable, list) and applicable:
            key = "scope:in_scope" if requirement_id in applicable and not excluded else "scope:excluded"
        elif excluded:
            key = "scope:excluded"
        else:
            key = "scope:not_recorded"
    else:
        key = "scope:excluded" if item.get("scope_enforced") else "scope:not_recorded"
    label, tone = CHIPS[key]
    return QualityChip(key, label, tone)


def _period_chip(context: CardContext, envelope: dict, claims: tuple[dict, ...]) -> QualityChip:
    if context.claim_set_id is None or envelope.get("claim_set_id") != context.claim_set_id:
        key = "period:unknown"
    elif not context.basis.period_recorded:
        key = "period:not_recorded"
    else:
        dates = [context.source_dates.get(claim.get("source_id")) for claim in claims]
        if any(value is not None and value > context.basis.evidence_cutoff for value in dates):
            key = "period:after_cutoff"
        elif any(value is None for value in dates):
            key = "period:undated"
        else:
            key = "period:dated"
    label, tone = CHIPS[key]
    return QualityChip(key, label, tone)


def _divergence_note(
    context: CardContext,
    conclusion: Conclusion,
    run_id: str,
    envelope: dict,
    item: dict,
) -> DivergenceNote | None:
    cluster_id = item.get("framework_divergence")
    if not cluster_id:
        return None
    divergence = next(
        (
            value for value in envelope.get("divergences") or ()
            if isinstance(value, dict) and value.get("cluster_id") == cluster_id
        ),
        None,
    )
    if divergence is None:
        return None
    compliant = tuple(
        tuple(member)
        for member in divergence.get("compliant") or ()
        if isinstance(member, (list, tuple)) and len(member) == 2
    )
    non_compliant = tuple(
        tuple(member)
        for member in divergence.get("non_compliant") or ()
        if isinstance(member, (list, tuple)) and len(member) == 2
    )

    def member_label(member: tuple[str, str]) -> str:
        framework = FrameworkRegistry.get_or_none(member[0])
        return f"{framework.name if framework else member[0].upper()} {member[1]}"

    event = context.acks.get((conclusion.id, run_id, cluster_id))
    metadata = _safe_json(event.metadata_json) if event is not None else None
    return DivergenceNote(
        cluster_id=cluster_id,
        analysis_run_id=run_id,
        compliant=compliant,
        non_compliant=non_compliant,
        sentence=DIVERGENCE_SENTENCE.format(
            compliant=", ".join(member_label(member) for member in compliant),
            non_compliant=", ".join(member_label(member) for member in non_compliant),
        ),
        acknowledged=event is not None,
        acknowledged_by=(event.actor.removeprefix("consultant:") if event is not None else None),
        acknowledged_at=(event.created_at if event is not None else None),
        note=(metadata.get("note") if metadata else None),
    )


def _quality_v2(
    context: CardContext,
    envelope: dict,
    item: dict,
    claims: tuple[dict, ...],
    claim_views: tuple[ClaimView, ...],
    citations: list[dict],
    conclusion: Conclusion,
) -> tuple[QualityChip, ...]:
    result = [_currency_chip(citations)]
    if claims:
        result.append(_period_chip(context, envelope, claims))
    result.append(_scope_chip(envelope, item, conclusion.requirement_id, source="v2"))
    kinds = {claim.get("kind") for claim in claims}
    for kind in CLAIM_KINDS:
        if kind in kinds:
            key = f"kind:{kind}"
            label, tone = CHIPS[key]
            result.append(QualityChip(key, label, tone))
    if claims and any(claim_view.needs_review for claim_view in claim_views):
        label, tone = CHIPS["support:needs_review"]
        result.append(QualityChip("support:needs_review", label, tone))
    if claims and any(claim_view.derived_from_image for claim_view in claim_views):
        label, tone = CHIPS["support:image"]
        result.append(QualityChip("support:image", label, tone))
    if item.get("analysis_incomplete"):
        label, tone = CHIPS["analysis:incomplete"]
        result.append(QualityChip("analysis:incomplete", label, tone))
    return tuple(result)


def _quality_v1(envelope: dict, item: dict, citations: list[dict], conclusion: Conclusion) -> tuple[QualityChip, ...]:
    result = [_currency_chip(citations), _scope_chip(envelope, item, conclusion.requirement_id, source="v1")]
    grounded = (item.get("quality") or {}).get("evidence_quote_grounded")
    if grounded is not None:
        key = "grounding:grounded" if grounded else "grounding:ungrounded"
        label, tone = CHIPS[key]
        result.append(QualityChip(key, label, tone))
    return tuple(result)


def build_card(context: CardContext, conclusion: Conclusion, proposal: ConclusionRevision | None, citations) -> RequirementCard:
    entry = _entry_for(context, proposal)
    if entry is None:
        return RequirementCard(
            source="none", analysis_run_id=None, proposed_outcome=None, reason=None,
            criteria_source=None, criteria_label=None, criteria=(), claims=(),
            response=None, contradictions=(), unsupported_assertion=False,
            analysis_incomplete=False, flags=(), quality=(), missing_evidence=(),
            missing_evidence_label=None, divergence=None,
        )

    source, run_id, envelope, claim_entry = entry
    item = claim_entry["item"]
    if source == "v1":
        outcome = claim_entry.get("outcome")
        quality = claim_entry.get("quality") or {}
        return RequirementCard(
            source="v1", analysis_run_id=run_id, proposed_outcome=outcome,
            reason=item.get("gap_description") or None, criteria_source=None,
            criteria_label=V1_SOURCE_LABEL, criteria=(), claims=(), response=None,
            contradictions=(), unsupported_assertion=bool(quality.get("unsupported_assertion")),
            analysis_incomplete=False, flags=(),
            quality=_quality_v1(envelope, claim_entry, citations, conclusion),
            missing_evidence=_missing_evidence_v1(
                conclusion.framework_id, conclusion.requirement_id, outcome
            ),
            missing_evidence_label=V1_MISSING_EVIDENCE_LABEL if outcome in _V1_GAP_OUTCOMES else None,
            divergence=None,
        )

    verified = {
        claim.get("claim_id"): claim
        for claim in envelope.get("verified_claims") or ()
        if isinstance(claim, dict) and claim.get("claim_id")
    }
    cited_ids = []
    for claim_id in item.get("cited_claim_ids") or ():
        if isinstance(claim_id, str) and claim_id in verified and claim_id not in cited_ids:
            cited_ids.append(claim_id)
    cited_records = tuple(verified[claim_id] for claim_id in cited_ids)
    claim_views = tuple(_claim_view(claim) for claim in cited_records)
    contradictions = tuple(
        Contradiction(contradiction.get("claim_id") or "", contradiction.get("note") or "")
        for contradiction in item.get("contradictions") or ()
        if isinstance(contradiction, dict) and contradiction.get("claim_id") in cited_ids
    )
    criteria_source = item.get("criteria_source")
    criteria_label = {"fallback": FALLBACK_CRITERIA_LABEL, "approved": APPROVED_CRITERIA_LABEL}.get(criteria_source)
    outcome = item.get("conclusion_outcome")
    if item.get("scope_excluded"):
        reason = REASON_SCOPE_EXCLUDED
    elif item.get("gap_statement"):
        reason = item["gap_statement"]
    elif outcome == "compliant":
        reason = REASON_COMPLIANT
    else:
        reason = None
    return RequirementCard(
        source="v2", analysis_run_id=run_id, proposed_outcome=outcome, reason=reason,
        criteria_source=criteria_source, criteria_label=criteria_label,
        criteria=_criterion_rows(item, set(cited_ids)), claims=claim_views,
        response=_response_view(item), contradictions=contradictions,
        unsupported_assertion=bool(item.get("unsupported_assertion")),
        analysis_incomplete=bool(item.get("analysis_incomplete")),
        flags=tuple(item.get("flags") or ()),
        quality=_quality_v2(context, envelope, item, cited_records, claim_views, citations, conclusion),
        missing_evidence=_missing_evidence_v2(conclusion.framework_id, item),
        missing_evidence_label=None,
        divergence=_divergence_note(context, conclusion, run_id, envelope, item),
    )


def approval_blocker(card: RequirementCard | None) -> str | None:
    if card is not None and card.divergence is not None and not card.divergence.acknowledged:
        return DIVERGENCE_ACK_REQUIRED_MESSAGE
    return None


def _latest_proposal(db: Session, conclusion_id: str) -> ConclusionRevision | None:
    return db.execute(
        select(ConclusionRevision)
        .where(
            ConclusionRevision.conclusion_id == conclusion_id,
            ConclusionRevision.action == "proposed",
        )
        .order_by(
            ConclusionRevision.created_at.desc(),
            literal_column("conclusion_revisions.rowid").desc(),
        )
        .limit(1)
    ).scalar_one_or_none()


def card_for(db: Session, conclusion: Conclusion, proposal: ConclusionRevision | None) -> RequirementCard:
    assessment = db.get(Assessment, conclusion.assessment_id)
    context = load_context(
        db, assessment=assessment,
        proposals=[proposal] if proposal is not None else [],
        conclusion_ids=[conclusion.id],
    )
    citations = resolve_citations(db, proposal.citations_json if proposal is not None else None)
    return build_card(context, conclusion, proposal, citations)


def divergence_blocker(db: Session, conclusion: Conclusion, proposal: ConclusionRevision | None) -> str | None:
    return approval_blocker(card_for(db, conclusion, proposal))


def acknowledge_divergence(
    db: Session,
    *,
    assessment_id: str,
    conclusion_id: str,
    analysis_run_id: str,
    cluster_id: str,
    note: str | None,
    actor: str,
) -> tuple[AuditEvent, bool]:
    conclusion = db.get(Conclusion, conclusion_id)
    if conclusion is None or conclusion.assessment_id != assessment_id:
        raise RequirementCardError(CONCLUSION_NOT_FOUND_MESSAGE, 404)
    proposal = _latest_proposal(db, conclusion.id)
    card = card_for(db, conclusion, proposal)
    divergence = card.divergence
    if divergence is None:
        raise RequirementCardError(NO_DIVERGENCE_MESSAGE)
    if divergence.analysis_run_id != analysis_run_id or divergence.cluster_id != cluster_id:
        raise RequirementCardError(DIVERGENCE_STALE_MESSAGE, 409)

    context = load_context(
        db, conclusion, [proposal] if proposal is not None else [], [conclusion.id]
    )
    existing = context.acks.get((conclusion.id, analysis_run_id, cluster_id))
    if existing is not None:
        return existing, False

    cleaned_note = " ".join((note or "").split())[:ACK_NOTE_MAX_CHARS] or None
    event = AuditEvent(
        actor=actor,
        action=DIVERGENCE_ACK_ACTION,
        entity_type=AUDIT_ENTITY_TYPE,
        entity_id=conclusion.id,
        metadata_json=json.dumps(
            {
                "analysis_run_id": analysis_run_id,
                "cluster_id": cluster_id,
                "compliant": [list(member) for member in divergence.compliant],
                "non_compliant": [list(member) for member in divergence.non_compliant],
                "note": cleaned_note,
            },
            sort_keys=True,
        ),
    )
    db.add(event)
    db.flush()
    return event, True


def span_view(db: Session, version_id: str, ref: str) -> SpanView:
    version = db.get(EvidenceVersion, version_id)
    evidence = db.get(Evidence, version.evidence_id) if version is not None else None
    if version is None or evidence is None:
        raise RequirementCardError(VERSION_NOT_FOUND_MESSAGE, 404)
    if ref != "whole":
        match = _SPAN_REF.fullmatch(ref or "")
        if match is None:
            raise RequirementCardError(SPAN_INVALID_MESSAGE)
        start, end = (int(value) for value in match.groups())
        if start >= end or (version.extracted_text is not None and end > len(version.extracted_text)):
            raise RequirementCardError(SPAN_INVALID_MESSAGE)
    text = version.extracted_text
    current = version.status == "active" and evidence.status == "active"
    if text is None:
        return SpanView(
            evidence_id=evidence.id, version_id=version.id, filename=version.original_filename,
            version_number=version.version_number, is_current=current, location_ref=ref,
            whole=ref == "whole", available=False, before="", span="", after="",
            truncated_before=False, truncated_after=False,
        )
    if ref == "whole":
        return SpanView(
            evidence_id=evidence.id, version_id=version.id, filename=version.original_filename,
            version_number=version.version_number, is_current=current, location_ref=ref,
            whole=True, available=True, before=text[:WHOLE_PREVIEW_CHARS], span="", after="",
            truncated_before=False, truncated_after=len(text) > WHOLE_PREVIEW_CHARS,
        )
    match = _SPAN_REF.fullmatch(ref)
    start, end = (int(value) for value in match.groups())
    before_start = max(0, start - SPAN_CONTEXT_CHARS)
    after_end = min(len(text), end + SPAN_CONTEXT_CHARS)
    return SpanView(
        evidence_id=evidence.id, version_id=version.id, filename=version.original_filename,
        version_number=version.version_number, is_current=current, location_ref=ref,
        whole=False, available=True, before=text[before_start:start], span=text[start:end],
        after=text[end:after_end], truncated_before=before_start > 0,
        truncated_after=after_end < len(text),
    )
