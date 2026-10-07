"""Contract tests for P6-10b: v2 Stage 4, Finding-grounded engagement narrative at report draft.

Handoff: tasks/handoffs/2026-09-28-p6-10-remediation-and-narrative.md (D-P6-10-G..P).
Plan: docs/plans/2026-09-25-001-grounded-analysis-and-deliverables-plan.md, Part B Stage 4,
Part D2 (per-framework posture paragraph) and D-P6-F. Written before the implementation; on
`main` they fail only because the code does not exist. No network: `llm_client.call_llm` fails
the test, and `narrative._call_llm` is patched per test. No WeasyPrint needed: board-report
generation is exercised with `board_report.render_pdf` patched.
"""

from __future__ import annotations

import importlib
import json
import re

import pytest

from app.models.report_snapshot import ReportSnapshot
from app.services import board_report, report_snapshots
from app.services.grounding.prompts import BEGIN_MARKER, END_MARKER
from tests.p6_10_support import (  # noqa: F401 - fixtures are used by name
    DP_FINDING_DESCRIPTION,
    FakeLLM,
    REVIEWER,
    _no_network_llm,
    _register_frameworks,
    analysed_assessment,
    create_finding,
    db,
    db_path,
    engine,
    events,
    gate,
    http,
    metadata,
    released_assessment,
    upload_root,
    user_prompt,
)

ALL_SECTIONS = ["executive", "framework-dpdpa", "framework-iso27001", "cross-framework"]
SECTION_RE = re.compile(r"^Section: (\S+)$", re.M)
EXEC_TEXT = "Consent and access governance are the main weaknesses across the assessment."
DP_TEXT = "Consent collection does not meet the standard for a freely given, specific consent."
ISO_TEXT = "User access is not reviewed on a demonstrable schedule."
CROSS_TEXT = "Both frameworks point to weak control over who can access personal data."


def _service():
    return importlib.import_module("app.services.narrative")


def _aliases(db, assessment) -> dict[str, str]:
    """framework_id -> alias of that framework's (single) finding in the fixture."""
    return {ref.framework_id: ref.alias for ref in _service().finding_refs(db, assessment)}


def _default_reply(aliases):
    def _reply(request):
        section = SECTION_RE.search(user_prompt(request)).group(1)
        f_iso, f_dp = aliases["iso27001"], aliases["dpdpa"]
        return {
            "executive": {"sentences": [{"text": EXEC_TEXT, "finding_refs": [f_iso, f_dp]}]},
            "framework-dpdpa": {"sentences": [{"text": DP_TEXT, "finding_refs": [f_dp]}]},
            "framework-iso27001": {"sentences": [{"text": ISO_TEXT, "finding_refs": [f_iso]}]},
            "cross-framework": {"sentences": [{"text": CROSS_TEXT, "finding_refs": [f_dp, f_iso]}]},
        }[section]
    return _reply


def _fake(monkeypatch, responder) -> FakeLLM:
    fake = FakeLLM(responder)
    monkeypatch.setattr(_service(), "_call_llm", fake)
    return fake


def _generate(http, assessment, section_id=""):
    return http.post(
        f"/api/assessments/{assessment.id}/narrative/generate",
        data={"section_id": section_id, "reviewer_name": REVIEWER},
    )


def _state(db, assessment):
    db.expire_all()
    return _service().state(db, assessment)


def _section(db, assessment, section_id):
    return next(s for s in _state(db, assessment).sections if s.section_id == section_id)


def _accept(http, db, assessment, section_id, text, *, findings_sha256=None):
    return http.post(
        f"/api/assessments/{assessment.id}/narrative/{section_id}/accept",
        data={
            "text": text,
            "findings_sha256": findings_sha256 or _state(db, assessment).findings_sha256,
            "reviewer_name": REVIEWER,
        },
    )


def _accept_all(http, db, assessment):
    a = _aliases(db, assessment)
    texts = {
        "executive": f"{EXEC_TEXT} [{a['iso27001']}, {a['dpdpa']}]",
        "framework-dpdpa": f"{DP_TEXT} [{a['dpdpa']}]",
        "framework-iso27001": f"{ISO_TEXT} [{a['iso27001']}]",
        "cross-framework": f"{CROSS_TEXT} [{a['dpdpa']}, {a['iso27001']}]",
    }
    for section_id, text in texts.items():
        response = _accept(http, db, assessment, section_id, text)
        assert response.status_code == 200, response.text


def _patch_renderer(monkeypatch):
    from app.utils import html_pdf

    monkeypatch.setattr(board_report, "render_pdf", lambda document: b"%PDF-1.7 p6-10 test\n")
    monkeypatch.setattr(html_pdf, "renderer_label", lambda: "weasyprint test")


def _generate_board(http, assessment):
    return http.post(
        f"/api/assessments/{assessment.id}/snapshots",
        data={"type": "board_report", "reviewer_name": REVIEWER},
    )


def _document(db, assessment):
    from datetime import datetime, timezone

    db.expire_all()
    return board_report.build_document(
        db, assessment, snapshot_id=None, version_label="v1",
        generated_at=datetime(2026, 9, 28, 10, 0, tzinfo=timezone.utc),
    )


def _narrative_sentences(document):
    narrative = document["summary"]["narrative"]
    sentences = [s for key in ("executive", "cross_framework") for s in narrative[key] or []]
    for framework in document["summary"]["frameworks"]:
        sentences += framework["narrative"] or []
    assert sentences, "the caller accepted every section first"
    return sentences


# ---------------------------------------------------------------------------


def test_scenario_1_closed_set_aliases_sections_and_empty_state(db, http, gate, monkeypatch):
    """D-P6-10-H: findings get F-aliases in top-risk order; sections follow the frameworks that have findings."""
    service = _service()
    assert service.TIER == "synthesize"
    assert service.AUDIT_DRAFTED == "assessment.narrative_drafted"
    assert service.AUDIT_ACCEPTED == "assessment.narrative_accepted"
    assert service.AUDIT_DISCARDED == "assessment.narrative_discarded"
    assessment, conclusions, dp, iso = released_assessment(db, http, gate, monkeypatch)
    refs = service.finding_refs(db, assessment)
    # ISO finding is critical, DPDPA finding is high: board_report top-risk order.
    assert [(r.alias, r.framework_id, r.requirement_id) for r in refs] == [
        ("F1", "iso27001", iso[0]),
        ("F2", "dpdpa", dp[0]),
    ]
    assert service.section_ids(assessment, refs) == ALL_SECTIONS
    state = _state(db, assessment)
    assert [s.section_id for s in state.sections] == ALL_SECTIONS
    assert all(s.status == "none" and not s.stale and s.sentences == () for s in state.sections)
    assert len(state.findings_sha256) == 64

    single, *_ = released_assessment(db, http, gate, monkeypatch, frameworks=("iso27001",))
    assert service.section_ids(single, service.finding_refs(db, single)) == ["executive", "framework-iso27001"]


def test_scenario_2_generation_requests_are_grounded_and_never_ask_for_numbers(db, http, gate, monkeypatch):
    """One synthesize-tier call per section; the schema enum is that section's closed set; findings are untrusted data."""
    assessment, *_ = released_assessment(db, http, gate, monkeypatch)
    aliases = _aliases(db, assessment)
    fake = _fake(monkeypatch, _default_reply(aliases))
    response = _generate(http, assessment)
    assert response.status_code == 200, response.text
    assert response.json()["sections"] == {section: "generated" for section in ALL_SECTIONS}
    assert len(fake.requests) == 4
    by_section = {SECTION_RE.search(user_prompt(r)).group(1): r for r in fake.requests}
    assert sorted(by_section) == sorted(ALL_SECTIONS)
    for section, request in by_section.items():
        assert request["tier"] == "synthesize" and request["temperature"] == 0
        schema = request["response_schema"]
        assert schema["name"] == "narrative_section_v1"
        item = schema["schema"]["properties"]["sentences"]["items"]
        assert set(item["properties"]) == {"text", "finding_refs"}
        enum = set(item["properties"]["finding_refs"]["items"]["enum"])
        expected = {aliases["dpdpa"]} if section == "framework-dpdpa" else (
            {aliases["iso27001"]} if section == "framework-iso27001" else set(aliases.values())
        )
        assert enum == expected, section
        prompt = user_prompt(request)
        assert "%" not in prompt and "score" not in prompt.lower()
        assert BEGIN_MARKER in prompt and END_MARKER in prompt
        if section == "framework-dpdpa":
            inside = prompt[prompt.index(BEGIN_MARKER):prompt.rindex(END_MARKER)]
            assert DP_FINDING_DESCRIPTION in inside
            assert "Access reviews are informal" not in prompt  # other framework's finding is out of the closed set

    state = _state(db, assessment)
    assert all(s.status == "draft" for s in state.sections)
    drafted = events(db, "assessment.narrative_drafted", assessment.id)
    assert len(drafted) == 4
    data = metadata(drafted[0])
    assert {"section_id", "basis_sha256", "status", "sentences", "dropped", "prompt_sha256",
            "prompt_version", "calls", "error_type"} <= set(data)
    assert data["calls"][0]["tier"] == "synthesize" and data["calls"][0]["stage"] == "narrative"
    # Unaccepted drafts never reach a client document.
    document = _document(db, assessment)
    assert document["summary"]["narrative"] == {"executive": None, "cross_framework": None}
    assert all(f["narrative"] is None for f in document["summary"]["frameworks"])
    assert EXEC_TEXT not in json.dumps(document)


def test_scenario_3_code_strips_sentences_that_break_the_closed_set(db, http, gate, monkeypatch):
    """Every sentence must cite known in-section findings; measured values, single-framework
    cross sentences and legal copy in a standards-only section are dropped with a reason."""
    assessment, *_ = released_assessment(db, http, gate, monkeypatch)
    a = _aliases(db, assessment)

    def _reply(request):
        section = SECTION_RE.search(user_prompt(request)).group(1)
        if section == "framework-iso27001":
            return {"sentences": [
                {"text": ISO_TEXT + " [F1]", "finding_refs": [a["iso27001"]]},
                {"text": "Consent failures breach the DPDPA.", "finding_refs": [a["iso27001"]]},
            ]}
        if section == "cross-framework":
            return {"sentences": [
                {"text": CROSS_TEXT, "finding_refs": [a["dpdpa"], a["iso27001"]]},
                {"text": "Access is the only theme.", "finding_refs": [a["iso27001"]]},
            ]}
        return {"sentences": [
            {"text": EXEC_TEXT, "finding_refs": [a["iso27001"]]},
            {"text": "Overall compliance scored 62% this period.", "finding_refs": [a["iso27001"]]},
            {"text": "A claim with no support.", "finding_refs": []},
            {"text": "A claim citing an unknown finding.", "finding_refs": ["F9"]},
            {"text": "A claim citing a finding outside this section.", "finding_refs": [a["iso27001"]]},
        ]}

    _fake(monkeypatch, _reply)
    assert _generate(http, assessment).status_code == 200
    reasons = {}
    for section in _state(db, assessment).sections:
        reasons[section.section_id] = sorted(d["reason"] for d in section.dropped)
    executive = _section(db, assessment, "executive")
    assert [s["text"] for s in executive.sentences] == [EXEC_TEXT, "A claim citing a finding outside this section."]
    assert reasons["executive"] == ["measured_value", "no_reference", "unknown_reference"]
    dpdpa = _section(db, assessment, "framework-dpdpa")
    assert dpdpa.sentences == ()  # every DPDPA sentence cited the ISO finding
    assert dpdpa.status == "none"
    assert reasons["framework-dpdpa"] == ["no_reference"] + ["unknown_reference"] * 4
    iso = _section(db, assessment, "framework-iso27001")
    assert [s["text"] for s in iso.sentences] == [ISO_TEXT], "bracketed refs are stripped from text"
    assert reasons["framework-iso27001"] == ["framework_copy"]
    cross = _section(db, assessment, "cross-framework")
    assert [s["text"] for s in cross.sentences] == [CROSS_TEXT]
    assert reasons["cross-framework"] == ["single_framework"]
    statuses = [metadata(e)["status"] for e in events(db, "assessment.narrative_drafted", assessment.id)]
    assert sorted(statuses) == ["failed", "ok", "ok", "ok"]


def test_scenario_4_consultant_edits_are_validated_and_accepted_text_reaches_the_report(db, http, gate, monkeypatch):
    """The edit page shows `text [F1]` lines; accept validates references; only accepted text is in the document."""
    service = _service()
    assessment, conclusions, dp, iso = released_assessment(db, http, gate, monkeypatch)
    a = _aliases(db, assessment)
    _fake(monkeypatch, _default_reply(a))
    assert _generate(http, assessment).status_code == 200

    page = http.get(f"/assessments/{assessment.id}/narrative")
    assert page.status_code == 200
    html = page.text
    for section in ALL_SECTIONS:
        assert f'data-narrative-section="{section}"' in html
    assert f"{DP_TEXT} [{a['dpdpa']}]" in html
    assert f'data-finding-ref="{a["iso27001"]}"' in html
    assert _state(db, assessment).findings_sha256 in html

    no_ref = _accept(http, db, assessment, "framework-dpdpa", DP_TEXT)
    assert no_ref.status_code == 422 and no_ref.headers["X-Toast-Type"] == "error"
    unknown = _accept(http, db, assessment, "framework-dpdpa", f"{DP_TEXT} [F9]")
    assert unknown.status_code == 422 and "F9" in unknown.json()["detail"]
    outside = _accept(http, db, assessment, "framework-dpdpa", f"{DP_TEXT} [{a['iso27001']}]")
    assert outside.status_code == 422
    stale = _accept(http, db, assessment, "framework-dpdpa", f"{DP_TEXT} [{a['dpdpa']}]", findings_sha256="0" * 64)
    assert stale.status_code == 409 and stale.json()["detail"] == service.STALE_PAGE_MESSAGE
    missing = _accept(http, db, assessment, "framework-nist_csf", f"{DP_TEXT} [{a['dpdpa']}]")
    assert missing.status_code == 404
    assert events(db, "assessment.narrative_accepted", assessment.id) == []

    edited = "Consent is pre-ticked, so it is not freely given."
    ok = _accept(http, db, assessment, "framework-dpdpa", f"{edited} [{a['dpdpa']}]\n\n")
    assert ok.status_code == 200, ok.text
    (event,) = events(db, "assessment.narrative_accepted", assessment.id)
    data = metadata(event)
    assert data["section_id"] == "framework-dpdpa"
    assert data["sentences"] == [{"text": edited, "finding_ids": [_service().finding_refs(db, assessment)[1].finding_id]}]
    assert event.actor == f"consultant:{REVIEWER}"
    assert _section(db, assessment, "framework-dpdpa").status == "accepted"

    document = _document(db, assessment)
    summary = {f["framework_id"]: f for f in document["summary"]["frameworks"]}
    finding_id = service.finding_refs(db, assessment)[1].finding_id
    # Revision 2026-10-01 (D-P6-10-K): each sentence carries the stable finding ids next to the
    # build-time aliases, so the v3 deck can map them to R-xx without reading the database.
    assert summary["dpdpa"]["narrative"] == [{
        "text": edited,
        "finding_ids": [finding_id],
            "finding_refs": ["R-02"],
        "citations": [{"finding_id": finding_id, "framework_id": "dpdpa", "requirement_id": dp[0]}],
    }]
    assert summary["iso27001"]["narrative"] is None  # still an unaccepted draft
    assert document["summary"]["narrative"] == {"executive": None, "cross_framework": None}
    assert document["schema_version"] == board_report.DOCUMENT_SCHEMA_VERSION == 3  # revision 2026-10-01 (F7)

    html = board_report.render_html(document, embed_fonts=False)
    assert 'data-narrative="framework-dpdpa"' in html
    assert edited in html and "R-02" in html and f"[{dp[0]}]" not in html
    assert service.NARRATIVE_NOTE in html
    assert EXEC_TEXT not in html and ISO_TEXT not in html


def test_scenario_5_changed_findings_make_sections_stale_and_block_the_board_report(db, http, gate, monkeypatch):
    """D-P6-10-L/M: a draft or stale section blocks generation (409); regenerate touches only stale sections."""
    service = _service()
    assessment, conclusions, dp, iso = released_assessment(db, http, gate, monkeypatch)
    _patch_renderer(monkeypatch)
    no_narrative = _generate_board(http, assessment)
    assert no_narrative.status_code == 200, "no narrative at all is allowed; the slots stay empty"

    a = _aliases(db, assessment)
    fake = _fake(monkeypatch, _default_reply(a))
    assert _generate(http, assessment).status_code == 200
    drafts_only = _generate_board(http, assessment)
    assert drafts_only.status_code == 409
    assert drafts_only.json()["detail"].startswith(service.NOT_READY_MESSAGE)
    _accept_all(http, db, assessment)
    db.expire_all()
    assert service.report_blockers(db, assessment) == []
    assert _generate_board(http, assessment).status_code == 200

    # A new DPDPA finding (low severity, so aliases F1/F2 do not move).
    create_finding(
        http, assessment, conclusions[("dpdpa", dp[3])],
        title="Retention is undefined", description="No retention schedule.",
        severity="low", priority=3, action="Adopt a retention schedule",
    )
    stale = {s.section_id: s.stale for s in _state(db, assessment).sections}
    assert stale == {"executive": True, "framework-dpdpa": True, "framework-iso27001": False, "cross-framework": True}
    blocked = _generate_board(http, assessment)
    assert blocked.status_code == 409
    detail = blocked.json()["detail"]
    assert all(section in detail for section in ("executive", "framework-dpdpa", "cross-framework"))
    assert "framework-iso27001" not in detail
    stale_doc = _document(db, assessment)
    assert stale_doc["summary"]["narrative"]["executive"] is None, "stale accepted text is never shown"
    assert {f["framework_id"]: f["narrative"] is not None for f in stale_doc["summary"]["frameworks"]} == {
        "dpdpa": False, "iso27001": True,
    }

    fake.requests.clear()
    result = _generate(http, assessment)
    assert result.json()["sections"] == {
        "executive": "generated", "framework-dpdpa": "generated",
        "framework-iso27001": "skipped", "cross-framework": "generated",
    }
    assert len(fake.requests) == 3
    assert _generate_board(http, assessment).status_code == 409  # new drafts are not accepted yet
    _accept_all(http, db, assessment)
    assert _generate_board(http, assessment).status_code == 200


def test_scenario_6_issued_snapshot_freezes_the_accepted_text(db, http, gate, monkeypatch):
    """The version's JSON sidecar holds the narrative; later edits never change an existing version."""
    assessment, *_ = released_assessment(db, http, gate, monkeypatch)
    _patch_renderer(monkeypatch)
    _accept_all(http, db, assessment)
    first = _generate_board(http, assessment)
    assert first.status_code == 200, first.text
    snapshot_id = first.json()["snapshot_id"]
    snapshot = db.get(ReportSnapshot, snapshot_id)
    frozen = report_snapshots.read_board_report_document(db, snapshot)
    assert frozen["summary"]["narrative"]["executive"][0]["text"] == EXEC_TEXT
    assert frozen["summary"]["narrative"]["cross_framework"][0]["text"] == CROSS_TEXT
    assert frozen["schema_version"] == 3
    # The sidecar keeps the stable ids with the aliases, in the accepted order (iso27001 first).
    refs = {ref.framework_id: ref for ref in _service().finding_refs(db, assessment)}
    executive = frozen["summary"]["narrative"]["executive"][0]
    assert executive["finding_ids"] == [refs["iso27001"].finding_id, refs["dpdpa"].finding_id]
    assert executive["finding_refs"] == ["R-01", "R-02"]

    a = _aliases(db, assessment)
    revised = "Access governance is the priority for the board."
    assert _accept(http, db, assessment, "executive", f"{revised} [{a['iso27001']}]").status_code == 200
    issued = http.post(
        f"/api/assessments/{assessment.id}/snapshots/{snapshot_id}/issue",
        data={"reviewer_name": REVIEWER},
    )
    assert issued.status_code == 200, issued.text
    db.expire_all()
    snapshot = db.get(ReportSnapshot, snapshot_id)
    assert snapshot.is_issued
    assert report_snapshots.read_board_report_document(db, snapshot) == frozen

    second = _generate_board(http, assessment)
    assert second.status_code == 200
    newer = report_snapshots.read_board_report_document(db, db.get(ReportSnapshot, second.json()["snapshot_id"]))
    assert newer["summary"]["narrative"]["executive"][0]["text"] == revised


def test_scenario_7_idempotent_generation_regenerate_cap_and_failures(db, http, gate, monkeypatch):
    """Current sections are skipped; a named section regenerates; 3 attempts per section basis; failures keep state."""
    service = _service()
    assessment, *_ = released_assessment(db, http, gate, monkeypatch)
    a = _aliases(db, assessment)
    fake = _fake(monkeypatch, _default_reply(a))
    assert _generate(http, assessment).status_code == 200
    assert len(fake.requests) == 4
    again = _generate(http, assessment)
    assert again.json()["sections"] == {section: "skipped" for section in ALL_SECTIONS}
    assert len(fake.requests) == 4

    assert _generate(http, assessment, "executive").json()["sections"] == {"executive": "generated"}
    assert _generate(http, assessment, "executive").json()["sections"] == {"executive": "generated"}
    assert _generate(http, assessment, "executive").json()["sections"] == {"executive": "limit_reached"}
    assert len(fake.requests) == 6
    assert service.MAX_DRAFTS_PER_SECTION_BASIS == 3

    ok_text = f"{ISO_TEXT} [{a['iso27001']}]"
    assert _accept(http, db, assessment, "framework-iso27001", ok_text).status_code == 200

    def _boom(_request):
        raise RuntimeError("provider down")

    fake.responder = _boom
    failed = _generate(http, assessment, "framework-iso27001")
    assert failed.status_code == 200
    assert failed.json()["sections"] == {"framework-iso27001": "failed"}
    assert failed.headers["X-Toast-Type"] == "error"
    iso = _section(db, assessment, "framework-iso27001")
    assert iso.status == "accepted" and [s["text"] for s in iso.sentences] == [ISO_TEXT]
    last = events(db, "assessment.narrative_drafted", assessment.id)[-1]
    assert metadata(last)["status"] == "failed" and metadata(last)["error_type"] == "RuntimeError"

    fake.responder = lambda _request: "not json"
    assert _generate(http, assessment, "framework-dpdpa").json()["sections"] == {"framework-dpdpa": "failed"}
    unknown = _generate(http, assessment, "framework-nist_csf")
    assert unknown.status_code == 404


def test_scenario_8_release_and_findings_are_prerequisites_and_discard_unblocks(db, http, gate, monkeypatch):
    """Drafting and accepting need a released report with approved findings; discarding a section removes it."""
    service = _service()
    assessment, conclusions, dp, iso = analysed_assessment(db, gate, monkeypatch)
    fake = _fake(monkeypatch, lambda _request: {"sentences": []})
    page = http.get(f"/assessments/{assessment.id}/narrative")
    assert page.status_code == 200
    assert _generate(http, assessment).status_code == 403
    assert fake.requests == []

    released, *_ = released_assessment(db, http, gate, monkeypatch)
    no_findings, *_ = released_assessment(db, http, gate, monkeypatch, frameworks=("iso27001",), findings=False)
    empty = _generate(http, no_findings)
    assert empty.status_code == 400 and empty.json()["detail"] == service.NO_FINDINGS_MESSAGE
    assert fake.requests == []

    a = _aliases(db, released)
    fake.responder = _default_reply(a)
    _patch_renderer(monkeypatch)
    assert _generate(http, released).status_code == 200
    assert _generate_board(http, released).status_code == 409
    for section in ALL_SECTIONS:
        response = http.post(
            f"/api/assessments/{released.id}/narrative/{section}/discard",
            data={"reviewer_name": REVIEWER},
        )
        assert response.status_code == 200, response.text
    assert all(s.status == "none" for s in _state(db, released).sections)
    assert len(events(db, "assessment.narrative_discarded", released.id)) == 4
    assert _generate_board(http, released).status_code == 200


def test_scenario_9_board_report_reads_narrative_without_any_llm_call(db, http, gate, monkeypatch):
    """Building, previewing and generating the board report never calls the model (D-P6-10-N)."""
    assessment, *_ = released_assessment(db, http, gate, monkeypatch)
    _accept_all(http, db, assessment)

    def _refuse(**_kwargs):
        raise AssertionError("the board report must not call the narrative model")

    monkeypatch.setattr(_service(), "_call_llm", _refuse)
    _patch_renderer(monkeypatch)
    document = _document(db, assessment)
    assert set(document["summary"]["narrative"]) == {"executive", "cross_framework"}
    assert document["summary"]["narrative"]["executive"][0]["citations"][0]["framework_id"] in ("dpdpa", "iso27001")
    for sentence in _narrative_sentences(document):
        assert set(sentence) == {"text", "finding_ids", "finding_refs", "citations"}
    preview = http.get(f"/api/assessments/{assessment.id}/board-report/preview")
    assert preview.status_code == 200
    assert EXEC_TEXT in preview.text and CROSS_TEXT in preview.text
    for section in ("executive", "cross-framework", "framework-dpdpa", "framework-iso27001"):
        assert f'data-narrative="{section}"' in preview.text
    assert _generate_board(http, assessment).status_code == 200
    versions = http.get(f"/assessments/{assessment.id}/snapshots")
    assert versions.status_code == 200
    assert f'data-narrative-link href="/assessments/{assessment.id}/narrative"' in versions.text


def test_scenario_11_sidecar_refs_join_to_top_risk_ranks_without_the_database(db, http, gate, monkeypatch):
    """Revision 2026-10-01 (F7): `finding_ids` is the stable join key, `finding_refs` the build-time F-alias.

    F<n> is the n-th finding in top-risk order, so the v3 deck's R-xx for a cited finding can be read
    from the document alone: `top_risks[].finding_id` (and later `observations[].finding_id`).
    """
    assessment, *_ = released_assessment(db, http, gate, monkeypatch)
    _accept_all(http, db, assessment)
    document = _document(db, assessment)
    rank = {risk["finding_id"]: index + 1 for index, risk in enumerate(document["top_risks"])}
    assert len(rank) == 2
    for sentence in _narrative_sentences(document):
        assert len(sentence["finding_ids"]) == len(set(sentence["finding_ids"])) == len(sentence["finding_refs"])
        assert sentence["finding_ids"] == [c["finding_id"] for c in sentence["citations"]]
        assert sentence["finding_refs"] == [f"R-{rank[finding_id]:02d}" for finding_id in sentence["finding_ids"]]
    # Re-derived at build time from the live approved set; the accept events keep only ids (D-P6-10-I).
    (accepted, *_rest) = events(db, "assessment.narrative_accepted", assessment.id)
    assert set(metadata(accepted)["sentences"][0]) == {"text", "finding_ids"}


def test_scenario_12_board_exports_accept_schema_v3_with_the_v3_layout(db, http, gate, monkeypatch):
    """Revision 2026-10-01 (D-P6-10-K) and P6-8 V3-B: a v3 sidecar exports through the v3 XLSX; DOCX is retired for v3."""
    import io

    import openpyxl

    from app.services import board_exports as exports

    assert exports.SUPPORTED_SCHEMA_VERSIONS == (1, 2, 3)
    assert exports.ROADMAP_INTROS[3] == exports.ROADMAP_INTROS[2]
    assessment, *_ = released_assessment(db, http, gate, monkeypatch)
    _patch_renderer(monkeypatch)
    _accept_all(http, db, assessment)
    first = _generate_board(http, assessment)
    assert first.status_code == 200, first.text
    snapshot = db.get(ReportSnapshot, first.json()["snapshot_id"])
    frozen = report_snapshots.read_board_report_document(db, snapshot)
    assert frozen["schema_version"] == 3
    sha = "ab" * 32

    # P6-8 V3-B: a v3 sidecar exports the v3 workbook (not the v2 About layout) and DOCX is retired for v3.
    book = openpyxl.load_workbook(io.BytesIO(exports.render_xlsx(frozen, document_sha256=sha)))
    assert tuple(book.sheetnames) == tuple(
        name for name in exports.XLSX_SHEETS_V3 if name != "Statement of Applicability" or frozen["soa"]
    )
    assert "About" not in book.sheetnames
    with pytest.raises(exports.DocumentSuperseded):
        exports.render_docx(frozen, document_sha256=sha)
    with pytest.raises(exports.UnsupportedDocument):
        exports.render_docx(dict(frozen, schema_version=4), document_sha256=sha)
