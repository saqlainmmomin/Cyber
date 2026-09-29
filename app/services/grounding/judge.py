"""DB-free, batched v2 requirement judging over verified claims."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from app.config import settings
from app.frameworks.mappings.clusters import CONTROL_CLUSTERS
from app.frameworks.prompts import _expand_cluster_responses, desk_review_flag_types
from app.frameworks.registry import FrameworkRegistry
from app.services import llm_client
from app.services.document_categories import document_categories
from app.services.grounding.claims import ClaimSet
from app.services.grounding import injection
from app.services.grounding import judge_prompts
from app.services.parallel import run_bounded

JUDGE_FLAGS = (
    "no_inputs",
    "unknown_claim_id",
    "unknown_criterion_id",
    "criteria_incomplete",
    "criterion_met_without_claim",
    "model_criteria_inconsistency",
    "unsupported_assertion",
    "applicability_proposed",
    "claims_truncated",
    "retried",
    "analysis_incomplete",
    "framework_divergence",
    "suspected_instruction",
)
RISK_LEVELS = ("low", "medium", "high", "critical")
PRIORITY_BY_RISK = {"critical": 1, "high": 2, "medium": 3, "low": 4}
POSITIVE_ANSWERS = ("fully_implemented", "partially_implemented", "yes", "partial")
IMPLICIT_SUFFIX = ".IMPLICIT"
V2_EXCLUDED_RED_FLAGS = {"dpdpa": ("gdpr_copy_paste", "ccpa_copy_paste")}

DOWNGRADE_GAP_STATEMENT = (
    "The model proposed compliant, but not every test criterion is met by a verified claim."
)
INCOMPLETE_GAP_STATEMENT = (
    "This requirement was not judged: the model did not return it after one retry. "
    "Run analysis again."
)
NO_INPUTS_GAP_STATEMENT = "No verified claim or confirmed questionnaire response addresses this requirement."
FRAMEWORK_NOT_JUDGED_MESSAGE = (
    "Analysis for {name} returned no usable judgment for any requirement "
    "(first error: {error}). Run analysis again."
)
CLAIM_SET_INCOMPLETE_MESSAGE = (
    "Analysis for {name} was not run: desk review for this framework is incomplete. "
    "Run desk review again."
)


@dataclass(frozen=True)
class JudgeBatch:
    index: int
    count: int
    framework_id: str
    requirement_ids: tuple[str, ...]

    @property
    def label(self) -> str:
        return f"j{self.index}/{self.count}"


@dataclass(frozen=True)
class _Unit:
    framework_id: str
    batch: JudgeBatch
    requirement_ids: tuple[str, ...]
    retry: bool = False

    @property
    def label(self) -> str:
        return self.batch.label + ("+retry" if self.retry else "")


def _call_llm(*, tier: str, stream: bool = False, **request) -> dict:
    return llm_client.call_llm(tier, stream=stream, **request)


def criteria_for(control) -> tuple[str, tuple[dict, ...]]:
    if control.test_criteria:
        return (
            "approved",
            tuple(
                {
                    "criterion_id": criterion.id,
                    "kind": criterion.kind,
                    "statement": criterion.statement,
                }
                for criterion in control.test_criteria
            ),
        )
    return (
        "fallback",
        ({
            "criterion_id": f"{control.id}{IMPLICIT_SUFFIX}",
            "kind": "design",
            "statement": control.description,
        },),
    )


def judge_batches(framework_id: str, requirement_ids: Sequence[str]) -> tuple[JudgeBatch, ...]:
    limit = settings.v2_judge_batch_max_requirements
    if limit <= 0:
        raise ValueError("v2_judge_batch_max_requirements must be greater than zero")
    wanted = set(requirement_ids)
    framework = FrameworkRegistry.get(framework_id)
    pieces: list[tuple[str, ...]] = []
    for domain in framework.domains.values():
        for section in domain.sections.values():
            ids = [control.id for control in section.controls if control.id in wanted]
            for start in range(0, len(ids), limit):
                pieces.append(tuple(ids[start:start + limit]))

    grouped: list[list[str]] = []
    for piece in pieces:
        if grouped and len(grouped[-1]) + len(piece) <= limit:
            grouped[-1].extend(piece)
        else:
            grouped.append(list(piece))
    count = len(grouped)
    return tuple(
        JudgeBatch(index=index, count=count, framework_id=framework_id, requirement_ids=tuple(ids))
        for index, ids in enumerate(grouped, 1)
    )


def red_flag_keys(framework_id: str) -> tuple[str, ...]:
    excluded = set(V2_EXCLUDED_RED_FLAGS.get(framework_id, ()))
    return tuple(key for key in desk_review_flag_types(framework_id) if key not in excluded)


def deterministic_risk(criticality: str, outcome: str) -> str:
    base = criticality if criticality in RISK_LEVELS else "medium"
    if outcome in ("compliant", "not_applicable"):
        return "low"
    if outcome == "non_compliant":
        return base
    return RISK_LEVELS[max(0, RISK_LEVELS.index(base) - 1)]


def priority_for_risk(risk_level: str) -> int:
    return PRIORITY_BY_RISK[risk_level]


def conclusion_outcome_for(outcome: str) -> str:
    return "insufficient_evidence" if outcome == "not_applicable_proposed" else outcome


def _response_map(responses: Sequence[dict], framework_id: str, control_ids: set[str]) -> dict[str, dict]:
    expanded = _expand_cluster_responses(list(responses), framework_id, control_ids)
    result: dict[str, dict] = {}
    for response in expanded:
        control_id = response.get("question_id")
        if control_id in control_ids and control_id not in result:
            result[control_id] = response
    return result


def _claim_prompt_value(claim, source_by_id: dict[str, dict]) -> dict:
    source = source_by_id.get(claim.source_id, {})
    return {
        "claim_id": claim.claim_id,
        "kind": claim.kind,
        "filename": claim.filename,
        "category": source.get("category", "other"),
        "statement": claim.statement,
        "quote": claim.quote,
        "derived_from_image": claim.derived_from_image,
    }


def _context(
    framework_id: str,
    control,
    claim_set: ClaimSet | None,
    responses: Sequence[dict],
    source_by_id: dict[str, dict],
    scope: set[str] | None,
    source_texts: Mapping[str, str] | None,
    quarantine: dict[str, tuple[str, ...]],
) -> dict:
    criteria_source, criteria = criteria_for(control)
    claims = claim_set.claims_for_requirement(control.id) if claim_set is not None else ()
    quarantined_claim_ids = []
    safe_claims = []
    for claim in claims:
        markers = injection.claim_markers(claim, source_texts)
        if markers:
            quarantined_claim_ids.append(claim.claim_id)
            quarantine.setdefault(claim.claim_id, markers)
        else:
            safe_claims.append(claim)
    shown = tuple(safe_claims[: settings.v2_judge_max_claims_per_requirement])
    response_map = _response_map(responses, framework_id, {control.id})
    response_value = response_map.get(control.id)
    response = None
    if response_value is not None:
        response = {
            "question_id": response_value.get("question_id"),
            "answer": response_value.get("answer"),
            "answer_source": response_value.get("answer_source") or "human",
            "notes": response_value.get("notes"),
        }
    return {
        "framework_id": framework_id,
        "framework": FrameworkRegistry.get(framework_id),
        "control": control,
        "criteria_source": criteria_source,
        "criteria": criteria,
        "all_claims": claims,
        "shown_claims": tuple(_claim_prompt_value(claim, source_by_id) for claim in shown),
        "shown_claim_objects": tuple(shown),
        "claims_available": len(safe_claims),
        "quarantined_claim_ids": tuple(quarantined_claim_ids),
        "response": response,
        "scope_excluded": scope is not None and control.id not in scope,
    }


def _base_record(context: dict, *, outcome: str, batch: str | None = None) -> dict:
    criteria = [
        {
            **criterion,
            "result": "no_evidence",
            "claim_ids": [],
            "original_result": None,
        }
        for criterion in context["criteria"]
    ]
    response = context["response"]
    response_out = None if response is None else {
        key: response[key] for key in ("question_id", "answer", "answer_source")
    }
    return {
        "framework_id": context["framework_id"],
        "requirement_id": context["control"].id,
        "batch": batch,
        "criteria_source": context["criteria_source"],
        "criteria": criteria,
        "contradictions": [],
        "model_outcome": None,
        "outcome": outcome,
        "conclusion_outcome": conclusion_outcome_for(outcome),
        "gap_statement": "",
        "missing_evidence": [],
        "red_flags": [],
        "absences": [],
        "cited_claim_ids": [],
        "response": response_out,
        "unsupported_assertion": False,
        "applicability_proposed": False,
        "analysis_incomplete": False,
        "scope_excluded": False,
        "flags": [],
        "dropped_claim_ids": [],
        "claims_available": context["claims_available"],
        "claims_shown": len(context["shown_claims"]),
        "framework_divergence": None,
        "risk_level": "low",
        "priority": 4,
    }


def _flags(flag_set: set[str]) -> list[str]:
    return [flag for flag in JUDGE_FLAGS if flag in flag_set]


def _finish_record(record: dict, context: dict, flag_set: set[str]) -> dict:
    outcome = record["conclusion_outcome"]
    record["risk_level"] = deterministic_risk(context["control"].criticality, outcome)
    record["priority"] = priority_for_risk(record["risk_level"])
    record["quarantined_claim_ids"] = list(context["quarantined_claim_ids"])
    if record["quarantined_claim_ids"]:
        flag_set.add("suspected_instruction")
    record["flags"] = _flags(flag_set)
    return record


def _no_input_record(context: dict) -> dict:
    record = _base_record(context, outcome="insufficient_evidence")
    record["gap_statement"] = NO_INPUTS_GAP_STATEMENT
    record["absences"] = [
        {"criterion_id": criterion["criterion_id"], "statement": criterion["statement"]}
        for criterion in context["criteria"]
    ]
    framework = context["framework"]
    record["missing_evidence"] = [
        {"document_type": request.document_type, "what_it_would_show": request.reason}
        for request in framework.evidence_requests
        if context["control"].id in request.maps_to
    ][:3]
    flags = {"no_inputs"}
    if context["claims_available"] > len(context["shown_claims"]):
        flags.add("claims_truncated")
    if (
        context["response"] is not None
        and context["response"].get("answer") in POSITIVE_ANSWERS
    ):
        record["unsupported_assertion"] = True
        flags.add("unsupported_assertion")
    return _finish_record(record, context, flags)


def _scope_excluded_record(context: dict) -> dict:
    record = _base_record(context, outcome="not_applicable")
    record["scope_excluded"] = True
    if context["claims_available"] > len(context["shown_claims"]):
        record["flags"] = ["claims_truncated"]
    return _finish_record(record, context, set(record["flags"]))


def _append_dropped(dropped: list[str], claim_id: object) -> None:
    if isinstance(claim_id, str) and claim_id not in dropped:
        dropped.append(claim_id)


def _judged_record(context: dict, item: dict, *, batch: str, retried: bool) -> dict:
    shown_ids = [claim["claim_id"] for claim in context["shown_claims"]]
    shown_set = set(shown_ids)
    flag_set: set[str] = set()
    dropped: list[str] = []
    cited_candidates: set[str] = set()

    raw_criteria = item.get("criteria", [])
    accepted_criteria: dict[str, dict] = {}
    criterion_ids = {criterion["criterion_id"] for criterion in context["criteria"]}
    for raw in raw_criteria:
        if not isinstance(raw, dict):
            continue
        raw_claim_ids = raw.get("claim_ids", [])
        if not isinstance(raw_claim_ids, list):
            raw_claim_ids = []
        valid_claim_ids: list[str] = []
        for claim_id in raw_claim_ids:
            if claim_id not in shown_set:
                _append_dropped(dropped, claim_id)
                flag_set.add("unknown_claim_id")
            elif isinstance(claim_id, str) and claim_id not in valid_claim_ids:
                valid_claim_ids.append(claim_id)
        criterion_id = raw.get("criterion_id")
        if criterion_id not in criterion_ids:
            flag_set.add("unknown_criterion_id")
            continue
        if criterion_id in accepted_criteria:
            continue
        result = raw.get("result")
        if result not in judge_prompts.CRITERION_RESULTS:
            result = "no_evidence"
        original_result = None
        if result == "met" and not valid_claim_ids:
            result = "no_evidence"
            original_result = "met"
            flag_set.add("criterion_met_without_claim")
        accepted_criteria[criterion_id] = {
            "criterion_id": criterion_id,
            "result": result,
            "claim_ids": valid_claim_ids,
            "original_result": original_result,
        }
        cited_candidates.update(valid_claim_ids)

    criteria = []
    for criterion in context["criteria"]:
        value = accepted_criteria.get(criterion["criterion_id"])
        if value is None:
            flag_set.add("criteria_incomplete")
            value = {
                "criterion_id": criterion["criterion_id"],
                "result": "no_evidence",
                "claim_ids": [],
                "original_result": None,
            }
        criteria.append({**criterion, **value})

    response = context["response"]
    response_ref = response["question_id"] if response is not None else None
    contradictions = []
    raw_contradictions = item.get("contradictions", [])
    if isinstance(raw_contradictions, list):
        for raw in raw_contradictions:
            if not isinstance(raw, dict):
                continue
            claim_id = raw.get("claim_id")
            if claim_id not in shown_set:
                _append_dropped(dropped, claim_id)
                flag_set.add("unknown_claim_id")
                continue
            if response_ref is None or raw.get("response_ref") != response_ref:
                continue
            contradiction = {
                "claim_id": claim_id,
                "response_ref": response_ref,
                "note": str(raw.get("note") or "")[:300],
            }
            contradictions.append(contradiction)
            cited_candidates.add(claim_id)

    allowed_flags = set(red_flag_keys(context["framework_id"]))
    red_flags = []
    raw_red_flags = item.get("red_flags", [])
    if isinstance(raw_red_flags, list):
        for raw in raw_red_flags:
            if not isinstance(raw, dict):
                continue
            raw_claim_ids = raw.get("claim_ids", [])
            if not isinstance(raw_claim_ids, list):
                raw_claim_ids = []
            valid_claim_ids = []
            for claim_id in raw_claim_ids:
                if claim_id not in shown_set:
                    _append_dropped(dropped, claim_id)
                    flag_set.add("unknown_claim_id")
                elif isinstance(claim_id, str) and claim_id not in valid_claim_ids:
                    valid_claim_ids.append(claim_id)
            if raw.get("check") not in allowed_flags or not valid_claim_ids:
                continue
            red_flags.append({
                "check": raw["check"],
                "claim_ids": valid_claim_ids,
                "note": str(raw.get("note") or "")[:300],
            })
            cited_candidates.update(valid_claim_ids)

    categories = set(document_categories([context["framework_id"]]))
    missing_evidence = []
    raw_missing = item.get("missing_evidence", [])
    if isinstance(raw_missing, list):
        for raw in raw_missing:
            if not isinstance(raw, dict):
                continue
            document_type = raw.get("document_type")
            if not isinstance(document_type, str) or document_type not in categories:
                document_type = "other"
            missing_evidence.append({
                "document_type": document_type,
                "what_it_would_show": str(raw.get("what_it_would_show") or "")[:300],
            })
            if len(missing_evidence) == 3:
                break

    result_by_id = {criterion["criterion_id"]: criterion for criterion in criteria}
    outcome = item["outcome"]
    conclusion_outcome = conclusion_outcome_for(outcome)
    if outcome == "compliant" and any(
        criterion["result"] != "met" for criterion in criteria
    ):
        outcome = "insufficient_evidence"
        conclusion_outcome = "insufficient_evidence"
        flag_set.add("model_criteria_inconsistency")
        gap_statement = DOWNGRADE_GAP_STATEMENT
    elif item["outcome"] == "compliant":
        gap_statement = ""
    else:
        gap_statement = str(item.get("gap_statement") or "")[:600]
    if item["outcome"] == "not_applicable_proposed":
        flag_set.add("applicability_proposed")

    absences = [
        {"criterion_id": criterion["criterion_id"], "statement": criterion["statement"]}
        for criterion in criteria
        if criterion["result"] == "no_evidence"
    ]
    cited_claim_ids = [claim_id for claim_id in shown_ids if claim_id in cited_candidates]
    unsupported = (
        (
            response is not None and response.get("answer") in POSITIVE_ANSWERS
        )
        or conclusion_outcome in ("compliant", "partially_compliant")
    ) and not cited_claim_ids
    if unsupported:
        flag_set.add("unsupported_assertion")
    if context["claims_available"] > len(context["shown_claims"]):
        flag_set.add("claims_truncated")
    if retried:
        flag_set.add("retried")

    record = {
        "framework_id": context["framework_id"],
        "requirement_id": context["control"].id,
        "batch": batch,
        "criteria_source": context["criteria_source"],
        "criteria": criteria,
        "contradictions": contradictions,
        "model_outcome": item["outcome"],
        "outcome": outcome,
        "conclusion_outcome": conclusion_outcome,
        "gap_statement": gap_statement,
        "missing_evidence": missing_evidence,
        "red_flags": red_flags,
        "absences": absences,
        "cited_claim_ids": cited_claim_ids,
        "response": None if response is None else {
            key: response[key] for key in ("question_id", "answer", "answer_source")
        },
        "unsupported_assertion": unsupported,
        "applicability_proposed": item["outcome"] == "not_applicable_proposed",
        "analysis_incomplete": False,
        "scope_excluded": False,
        "flags": [],
        "dropped_claim_ids": dropped,
        "claims_available": context["claims_available"],
        "claims_shown": len(context["shown_claims"]),
        "framework_divergence": None,
        "risk_level": "low",
        "priority": 4,
    }
    return _finish_record(record, context, flag_set)


def _incomplete_record(context: dict, batch: str) -> dict:
    record = _base_record(context, outcome="insufficient_evidence", batch=batch)
    record["gap_statement"] = INCOMPLETE_GAP_STATEMENT
    record["analysis_incomplete"] = True
    flags = {"retried", "analysis_incomplete"}
    if context["claims_available"] > len(context["shown_claims"]):
        flags.add("claims_truncated")
    if (
        context["response"] is not None
        and context["response"].get("answer") in POSITIVE_ANSWERS
    ):
        record["unsupported_assertion"] = True
        flags.add("unsupported_assertion")
    return _finish_record(record, context, flags)


def _strip_code_fence(value: str) -> str:
    value = value.strip()
    if value.startswith("```"):
        lines = value.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        value = "\n".join(lines).strip()
    return value


def _parse_reply(reply: Any, requirement_ids: Sequence[str]) -> tuple[dict[str, dict], int, str | None]:
    text = reply.get("text") if isinstance(reply, dict) else reply
    if not isinstance(text, str):
        return {}, 0, "invalid_response"
    try:
        parsed = json.loads(_strip_code_fence(text))
    except (TypeError, json.JSONDecodeError):
        return {}, 0, "invalid_response"
    if not isinstance(parsed, dict) or not isinstance(parsed.get("requirements"), list):
        return {}, 0, "invalid_response"
    accepted: dict[str, dict] = {}
    unknown = 0
    usable_seen = False
    allowed = set(requirement_ids)
    for item in parsed["requirements"]:
        if not isinstance(item, dict):
            continue
        requirement_id = item.get("requirement_id")
        if requirement_id not in allowed:
            unknown += 1
            continue
        if requirement_id in accepted:
            continue
        if (
            item.get("outcome") not in judge_prompts.JUDGE_MODEL_OUTCOMES
            or not isinstance(item.get("criteria"), list)
        ):
            continue
        accepted[requirement_id] = item
        usable_seen = True
    return accepted, unknown, None if usable_seen else "invalid_response"


def _system_and_request(
    unit: _Unit,
    contexts: Mapping[str, dict],
    framework_ids: Sequence[str],
) -> dict:
    selected = [contexts[requirement_id] for requirement_id in unit.requirement_ids]
    framework = FrameworkRegistry.get(unit.framework_id)
    other_names = [
        FrameworkRegistry.get(framework_id).name
        for framework_id in framework_ids
        if framework_id != unit.framework_id
    ]
    doc_types = document_categories([unit.framework_id])
    flags = red_flag_keys(unit.framework_id)
    criterion_ids = [
        criterion["criterion_id"]
        for context in selected
        for criterion in context["criteria"]
    ]
    return {
        "tier": "judge",
        "stream": False,
        "temperature": 0,
        "max_tokens": settings.v2_judge_max_tokens,
        "system": judge_prompts.build_judge_system_prompt(
            framework,
            other_names,
            selected,
            doc_types,
            flags,
        ),
        "messages": [{
            "role": "user",
            "content": judge_prompts.build_judge_user_prompt(selected),
        }],
        "json_output": True,
    } | ({
        "response_schema": judge_prompts.build_judge_schema(
            unit.requirement_ids,
            criterion_ids,
            doc_types,
            flags,
        )
    } if settings.v2_structured_output else {})


def _run_unit(unit: _Unit, contexts: Mapping[str, dict], framework_ids: Sequence[str]):
    request = _system_and_request(unit, contexts, framework_ids)
    with llm_client.call_tag(
        stage="judge",
        framework_id=unit.framework_id,
        batch=unit.label,
    ):
        return _call_llm(**request)


def _batch_index(value: object) -> int:
    match = re.search(r"j(\d+)/", str(value or ""))
    return int(match.group(1)) if match else 0


def _sorted_calls(calls: Sequence[dict], framework_ids: Sequence[str]) -> tuple[dict, ...]:
    positions = {framework_id: index for index, framework_id in enumerate(framework_ids)}
    return tuple(sorted(
        calls,
        key=lambda call: (
            positions.get(call.get("framework_id"), len(positions)),
            1 if "+retry" in str(call.get("batch", "")) else 0,
            _batch_index(call.get("batch")),
            call.get("attempt", 1),
            call.get("status", ""),
        ),
    ))


def _record_error(exc: BaseException | None) -> str | None:
    if exc is None:
        return None
    return f"{type(exc).__name__}: {exc}"[:300]


def _empty_metrics(framework, contexts: Sequence[dict]) -> dict:
    criteria_counts = {"approved": 0, "fallback": 0}
    for context in contexts:
        criteria_counts[context["criteria_source"]] += 1
    return {
        "requirements": len(contexts),
        "scope_excluded": 0,
        "no_inputs": 0,
        "sent_to_judge": 0,
        "judged": 0,
        "retried_requirements": 0,
        "analysis_incomplete": 0,
        "downgraded_compliant": 0,
        "dropped_claim_ids": 0,
        "quarantined_claims": len({
            claim_id
            for context in contexts
            for claim_id in context["quarantined_claim_ids"]
        }),
        "unsupported_assertions": 0,
        "applicability_proposed": 0,
        "unknown_requirement_ids": 0,
        "calls": 0,
        "retry_calls": 0,
        "divergences": 0,
        "criteria_source": criteria_counts,
    }


def divergence_check(judgments: Mapping[str, Sequence[dict]]) -> tuple[dict, ...]:
    divergences = []
    framework_ids = list(judgments)
    for cluster in CONTROL_CLUSTERS:
        member_ids = {
            (member["framework"], member["control"])
            for member in cluster["controls"]
        }
        present = [
            (framework_id, record["requirement_id"], record["conclusion_outcome"])
            for framework_id in framework_ids
            for record in judgments[framework_id]
            if (framework_id, record["requirement_id"]) in member_ids
        ]
        compliant = [item for item in present if item[2] == "compliant"]
        non_compliant = [item for item in present if item[2] == "non_compliant"]
        compliant = [
            item for item in compliant
            if any(other[0] != item[0] for other in non_compliant)
        ]
        non_compliant = [
            item for item in non_compliant
            if any(other[0] != item[0] for other in compliant)
        ]
        if compliant and non_compliant:
            divergences.append({
                "cluster_id": str(cluster["cluster_id"]),
                "compliant": [[framework_id, requirement_id] for framework_id, requirement_id, _ in compliant],
                "non_compliant": [[framework_id, requirement_id] for framework_id, requirement_id, _ in non_compliant],
                "acknowledged": False,
            })
    return tuple(divergences)


@dataclass(frozen=True)
class JudgmentSet:
    framework_ids: tuple[str, ...]
    judgments: dict
    failed_frameworks: dict
    divergences: tuple
    metrics: dict
    llm_calls: tuple
    prompt_version: str
    prompt_fingerprint: str
    claim_set_id: str | None
    quarantined: dict = field(default_factory=dict)


def run_stage_2(
    claim_set: ClaimSet | None,
    framework_ids: Sequence[str],
    responses: Sequence[dict],
    *,
    applicable_requirements: Sequence[str] | None = None,
    max_workers: int | None = None,
    source_texts: Mapping[str, str] | None = None,
) -> JudgmentSet:
    framework_ids = tuple(framework_ids)
    source_by_id = {
        source["source_id"]: source
        for source in (claim_set.sources if claim_set is not None else ())
    }
    affected = set(claim_set.affected_framework_ids()) if claim_set is not None else set()
    scope = (
        set(applicable_requirements)
        if isinstance(applicable_requirements, (list, tuple, set)) and applicable_requirements
        else None
    )
    contexts_by_framework: dict[str, dict[str, dict]] = {}
    sent_units: list[_Unit] = []
    metrics_by_framework: dict[str, dict] = {}
    failed_frameworks: dict[str, str] = {}
    quarantine: dict[str, tuple[str, ...]] = {}

    for framework_id in framework_ids:
        framework = FrameworkRegistry.get(framework_id)
        controls = framework.all_controls()
        contexts = {
            control.id: _context(
                framework_id,
                control,
                claim_set,
                responses,
                source_by_id,
                scope,
                source_texts,
                quarantine,
            )
            for control in controls
        }
        contexts_by_framework[framework_id] = contexts
        if framework_id in affected:
            failed_frameworks[framework_id] = CLAIM_SET_INCOMPLETE_MESSAGE.format(name=framework.name)
            continue
        metrics = _empty_metrics(framework, tuple(contexts.values()))
        metrics["scope_excluded"] = sum(1 for context in contexts.values() if context["scope_excluded"])
        metrics["no_inputs"] = sum(
            1
            for context in contexts.values()
            if not context["scope_excluded"]
            and not context["shown_claims"]
            and context["response"] is None
        )
        sent_ids = [
            control.id
            for control in controls
            if not contexts[control.id]["scope_excluded"]
            and (contexts[control.id]["shown_claims"] or contexts[control.id]["response"] is not None)
        ]
        metrics["sent_to_judge"] = len(sent_ids)
        metrics_by_framework[framework_id] = metrics
        batches = judge_batches(framework_id, sent_ids)
        sent_units.extend(
            _Unit(framework_id=framework_id, batch=batch, requirement_ids=batch.requirement_ids)
            for batch in batches
        )

    primary_results: list[tuple[_Unit, dict[str, dict], int, str | None]] = []
    retry_units: list[_Unit] = []
    accepted: dict[str, dict[str, tuple[dict, str, bool]]] = {
        framework_id: {} for framework_id in framework_ids if framework_id in metrics_by_framework
    }
    first_errors: dict[str, str] = {}
    workers = settings.v2_max_concurrency if max_workers is None else max_workers

    with llm_client.collect_calls() as calls:
        primary_raw = run_bounded(
            lambda unit: _run_unit(unit, contexts_by_framework[unit.framework_id], framework_ids),
            sent_units,
            max_workers=workers,
        )
        for unit, (reply, exc) in zip(sent_units, primary_raw):
            if exc is not None:
                parsed, unknown, error = {}, 0, _record_error(exc)
            else:
                parsed, unknown, error = _parse_reply(reply, unit.requirement_ids)
            metrics_by_framework[unit.framework_id]["unknown_requirement_ids"] += unknown
            if error and unit.framework_id not in first_errors:
                first_errors[unit.framework_id] = error
            for requirement_id, item in parsed.items():
                accepted[unit.framework_id][requirement_id] = (item, unit.label, False)
            missing = tuple(
                requirement_id
                for requirement_id in unit.requirement_ids
                if requirement_id not in parsed
            )
            if missing:
                metrics_by_framework[unit.framework_id]["retried_requirements"] += len(missing)
                retry_units.append(_Unit(
                    framework_id=unit.framework_id,
                    batch=unit.batch,
                    requirement_ids=missing,
                    retry=True,
                ))
            primary_results.append((unit, parsed, unknown, error))
        retry_raw = run_bounded(
            lambda unit: _run_unit(unit, contexts_by_framework[unit.framework_id], framework_ids),
            retry_units,
            max_workers=workers,
        )
        still_missing: dict[str, list[tuple[str, str]]] = {
            framework_id: [] for framework_id in accepted
        }
        for unit, (reply, exc) in zip(retry_units, retry_raw):
            if exc is not None:
                parsed, unknown, error = {}, 0, _record_error(exc)
            else:
                parsed, unknown, error = _parse_reply(reply, unit.requirement_ids)
            metrics_by_framework[unit.framework_id]["unknown_requirement_ids"] += unknown
            if error and unit.framework_id not in first_errors:
                first_errors[unit.framework_id] = error
            for requirement_id, item in parsed.items():
                accepted[unit.framework_id][requirement_id] = (item, unit.label, True)
            for requirement_id in unit.requirement_ids:
                if requirement_id not in parsed:
                    still_missing[unit.framework_id].append((requirement_id, unit.label))

        judgments: dict[str, tuple[dict, ...]] = {}
        for framework_id in framework_ids:
            if framework_id not in metrics_by_framework:
                continue
            contexts = contexts_by_framework[framework_id]
            metrics = metrics_by_framework[framework_id]
            sent_count = metrics["sent_to_judge"]
            if sent_count and not accepted[framework_id]:
                framework = FrameworkRegistry.get(framework_id)
                failed_frameworks[framework_id] = FRAMEWORK_NOT_JUDGED_MESSAGE.format(
                    name=framework.name,
                    error=first_errors.get(framework_id, "invalid_response"),
                )
                continue
            records: dict[str, dict] = {}
            for control in FrameworkRegistry.get(framework_id).all_controls():
                context = contexts[control.id]
                if context["scope_excluded"]:
                    record = _scope_excluded_record(context)
                elif not context["shown_claims"] and context["response"] is None:
                    record = _no_input_record(context)
                elif control.id in accepted[framework_id]:
                    item, batch, retried = accepted[framework_id][control.id]
                    record = _judged_record(context, item, batch=batch, retried=retried)
                else:
                    retry_entry = next(
                        (batch for requirement_id, batch in still_missing[framework_id]
                         if requirement_id == control.id),
                        "j1/1+retry",
                    )
                    record = _incomplete_record(context, retry_entry)
                records[control.id] = record
            judgments[framework_id] = tuple(records.values())

            metrics["judged"] = sum(
                1 for record in records.values() if record["model_outcome"] is not None
            )
            metrics["analysis_incomplete"] = sum(
                1 for record in records.values() if record["analysis_incomplete"]
            )
            metrics["downgraded_compliant"] = sum(
                1 for record in records.values()
                if "model_criteria_inconsistency" in record["flags"]
            )
            metrics["dropped_claim_ids"] = sum(
                len(record["dropped_claim_ids"]) for record in records.values()
            )
            metrics["unsupported_assertions"] = sum(
                1 for record in records.values() if record["unsupported_assertion"]
            )
            metrics["applicability_proposed"] = sum(
                1 for record in records.values() if record["applicability_proposed"]
            )
            metrics["calls"] = sum(
                1 for unit in sent_units if unit.framework_id == framework_id
            )
            metrics["retry_calls"] = sum(
                1 for unit in retry_units if unit.framework_id == framework_id
            )

        divergences = divergence_check(judgments)
        for divergence in divergences:
            cluster_id = divergence["cluster_id"]
            involved = {
                framework_id
                for framework_id, requirement_id in divergence["compliant"] + divergence["non_compliant"]
            }
            for framework_id in involved:
                metrics_by_framework[framework_id]["divergences"] += 1
                updated = []
                for record in judgments[framework_id]:
                    if [framework_id, record["requirement_id"]] in (
                        divergence["compliant"] + divergence["non_compliant"]
                    ):
                        record["framework_divergence"] = cluster_id
                        record["flags"] = _flags(set(record["flags"]) | {"framework_divergence"})
                    updated.append(record)
                judgments[framework_id] = tuple(updated)

        for framework_id in failed_frameworks:
            metrics_by_framework.pop(framework_id, None)

        primary_count = len(sent_units)
        retry_count = len(retry_units)
        # The explicit metrics count request units, not provider retry attempts.
        for framework_id, metrics in metrics_by_framework.items():
            if metrics["calls"] == 0 and framework_id in {
                unit.framework_id for unit in sent_units
            }:
                metrics["calls"] = sum(1 for unit in sent_units if unit.framework_id == framework_id)
            if metrics["retry_calls"] == 0 and framework_id in {
                unit.framework_id for unit in retry_units
            }:
                metrics["retry_calls"] = sum(1 for unit in retry_units if unit.framework_id == framework_id)

    return JudgmentSet(
        framework_ids=framework_ids,
        judgments=judgments,
        failed_frameworks={framework_id: failed_frameworks[framework_id] for framework_id in framework_ids if framework_id in failed_frameworks},
        divergences=tuple(divergences),
        metrics={framework_id: metrics_by_framework[framework_id] for framework_id in framework_ids if framework_id in metrics_by_framework},
        llm_calls=_sorted_calls(calls, framework_ids),
        prompt_version=judge_prompts.JUDGE_PROMPT_VERSION,
        prompt_fingerprint=judge_prompts.judge_prompt_fingerprint(),
        claim_set_id=claim_set.claim_set_id if claim_set is not None else None,
        quarantined=quarantine,
    )
