"""TDD ("red") contract suite for P6-7b: one-click "add to RFI" from the requirement card.

Handoff: ``tasks/handoffs/2026-09-28-p6-7b-add-to-rfi.md``. Plan:
``docs/plans/2026-09-25-001-grounded-analysis-and-deliverables-plan.md``, Part D D1
item 5 and D2 item 5. Written by the designer before the implementation; it must
turn green WITHOUT edits. If an assertion looks wrong, report it in the handoff's
Results; do not change it. Scenario numbers match the handoff.

Under contract (does not exist yet): ``app.services.rfi_evidence_requests``, the
two ``/api/assessments/{id}/rfi-requests/...`` routes, the additive
``MissingEvidence`` / ``RequirementCard`` fields, the ``evidence_request`` RFI item
kind and the card and RFI-page markup. Before implementation these tests fail with
``ModuleNotFoundError``, a 404/405 for the missing routes, or an assertion on
missing markup. Scenario 12 (the file-set guard) passes before and after.

No live LLM. v2 runs come from the real v2 pipeline with the P6-4 provider fakes
(the P6-7a builder); after each fixture is built every ``llm_client.call_llm``
call fails the test. Approvals record a report basis first
(``tests/report_period_helper.py``, D-P6-G).
"""

from __future__ import annotations

import dataclasses
import hashlib
import importlib
import io
import json
import re
import subprocess
from html import unescape
from pathlib import Path

import pdfplumber
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 - register all ORM tables
from app.config import settings
from app.database import get_db
from app.frameworks.registry import FrameworkRegistry
from app.main import app
from app.models.audit_event import AuditEvent
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.report_snapshot import ReportSnapshot
from app.services import conclusion_review, report_snapshots, rfi_requests
from tests.report_period_helper import record_test_period
from tests.test_p6_3b_v2_flag import Q_CONSENT, add_evidence, policy_text
from tests.test_p6_4_v2_judge import e2e_script
from tests.test_p6_7_requirement_card import (
    approve,
    build_v2,
    card_html,
    conclusion,
    conclusions_page,
    forbid_llm,
    latest_run,
    open_tag,
    seed_assessment,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

# Exact copy pinned by the handoff (D-P6-7b-*).
REQUESTED_ACTION = "rfi.evidence_requested"
WITHDRAWN_ACTION = "rfi.evidence_request_withdrawn"
ITEM_KIND = "evidence_request"
REQUESTED_GROUP = "Additional evidence requested"
OTHER_TITLE = "Additional evidence"
ITEM_STATUS = "Specific evidence requested for the requirements listed"
REQUEST_TEXT_FORMAT = "{detail} Requested for {framework_name} {requirement_id}: {requirement_title}."
STATE_REQUESTED = "Added to the draft RFI. Generate a new RFI version to send it."
STATE_ISSUED = "Sent in RFI {version_label} as {item_id}."
ADDED_TOAST = "Added to the draft RFI"
ALREADY_TOAST = "Already on the draft RFI"
WITHDRAWN_TOAST = "Removed from the draft RFI"
ALREADY_WITHDRAWN_TOAST = "Not on the draft RFI"
STALE_MESSAGE = "The missing-evidence list changed since you loaded it. Reload the card and try again."
NOT_FOUND_MESSAGE = "Evidence request not found."
CONCLUSION_NOT_FOUND = "Conclusion not found"
PAGE_NOTE = "Evidence requests you added from requirement cards are included."
V1_SOURCE_KEYS = {"schema_version", "framework_ids", "checklist_sha256", "conclusion_versions"}

# The scripted judge adds missing evidence to two judged requirements that share
# the ``privacy_policy`` document type across frameworks, plus one ``other``.
DPDPA_RID = "CH2.CONSENT.2"  # response only, no claim: judged, partially compliant
ISO_RID = "ISO.A5.2"  # non-compliant on the CLUSTER_002 claims
DPDPA_PRIVACY = "A privacy notice that names the grievance officer and the complaint route"
DPDPA_OTHER = "Board minutes approving the notice"
ISO_PRIVACY = "The approved policy with its last review date"
MISSING = {
    DPDPA_RID: [
        {"document_type": "privacy_policy", "what_it_would_show": DPDPA_PRIVACY},
        {"document_type": "other", "what_it_would_show": DPDPA_OTHER},
    ],
    ISO_RID: [{"document_type": "privacy_policy", "what_it_would_show": ISO_PRIVACY}],
}


def rer():
    """app.services.rfi_evidence_requests, imported lazily so each test fails on its own."""
    return importlib.import_module("app.services.rfi_evidence_requests")


def scripted(rid, criterion_ids, claim_ids, request):
    value = e2e_script(rid, criterion_ids, claim_ids, request)
    if rid in MISSING:
        value["missing_evidence"] = [dict(entry) for entry in MISSING[rid]]
    return value


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module", autouse=True)
def _register_frameworks():
    from app.main import _register_frameworks as register

    register()


@pytest.fixture()
def db_path(tmp_path):
    path = tmp_path / "p6-7b.sqlite3"
    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{path}")
    command.upgrade(config, "head")
    return path


@pytest.fixture()
def db(db_path):
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def http(db, db_path, tmp_path, monkeypatch):
    from app.routers.web import templates
    from app.template_config import configure_templates

    configure_templates(templates)
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    monkeypatch.setattr(settings, "upload_dir", str(upload_dir))
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{db_path}")

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def flag_v2(monkeypatch):
    monkeypatch.setattr(settings, "analysis_pipeline_version", "v2")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def build(db, monkeypatch, *, frameworks=("dpdpa", "iso27001"), refuse_llm=True):
    assessment = build_v2(db, monkeypatch, frameworks=frameworks, script=scripted)
    assessment.scope_answers = json.dumps({})
    db.commit()
    if refuse_llm:
        forbid_llm(monkeypatch)
    return assessment


def expected_text(framework_id, requirement_id, detail):
    framework = FrameworkRegistry.get(framework_id)
    return REQUEST_TEXT_FORMAT.format(
        detail=detail.rstrip(".") + ".",
        framework_name=framework.name,
        requirement_id=requirement_id,
        requirement_title=framework.get_control(requirement_id).title,
    )


def expected_title(framework_id, document_type):
    """The pack's client-facing label, else the humanised document type (as P6-7a's card)."""
    labels = {item.document_type: item.label for item in FrameworkRegistry.get(framework_id).evidence_requests}
    return labels.get(document_type, document_type.replace("_", " ").capitalize())


def expected_key(framework_id, requirement_id, document_type, detail):
    raw = "\x1f".join((framework_id, requirement_id, document_type, " ".join(detail.split())))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def add_url(assessment, row):
    return f"/api/assessments/{assessment.id}/rfi-requests/{row.id}"


def withdraw_url(assessment, row):
    return f"/api/assessments/{assessment.id}/rfi-requests/{row.id}/withdraw"


def add(http, assessment, row, key, reviewer="Priya"):
    return http.post(add_url(assessment, row), data={"request_key": key, "reviewer_name": reviewer})


def withdraw(http, assessment, row, key, reviewer="Priya", origin=None):
    data = {"request_key": key, "reviewer_name": reviewer}
    if origin is not None:
        data["origin"] = origin
    return http.post(withdraw_url(assessment, row), data=data)


def rfi_events(db, row=None):
    query = db.query(AuditEvent).filter(AuditEvent.action.in_((REQUESTED_ACTION, WITHDRAWN_ACTION)))
    if row is not None:
        query = query.filter(AuditEvent.entity_id == row.id)
    return query.order_by(AuditEvent.created_at).all()


def li_for(html, key):
    tag = open_tag(html, "data-rfi-request-key", key)
    start = html.index(tag)
    return tag, unescape(html[start: html.index("</li>", start)])


def draft(db, assessment):
    db.expire_all()
    return rfi_requests.build_rfi_document(db, assessment)


def requested_items(document):
    return [item for item in document["items"] if item["kind"] == ITEM_KIND]


def generate(http, assessment):
    return http.post(
        f"/api/assessments/{assessment.id}/rfi/versions",
        files=[("reviewer_name", (None, "Priya"))],
    )


def issue(http, assessment, snapshot_id):
    return http.post(
        f"/api/assessments/{assessment.id}/rfi/versions/{snapshot_id}/issue",
        data={"reviewer_name": "Priya"},
    )


def _git(*args) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, check=True, capture_output=True, text=True
    ).stdout


# --------------------------------------------------------------------------- #
# Scenario 1: the card offers a prefilled, deterministic request per missing item
# --------------------------------------------------------------------------- #


def test_scenario_1_card_offers_prefilled_add_for_v2_missing_evidence(db, http, monkeypatch, flag_v2):
    assessment = build(db, monkeypatch)
    module = rer()
    row = conclusion(db, assessment, "dpdpa", DPDPA_RID)
    html = card_html(conclusions_page(http, assessment), row.id)

    for entry in MISSING[DPDPA_RID]:
        key = expected_key("dpdpa", DPDPA_RID, entry["document_type"], entry["what_it_would_show"])
        assert module.request_key("dpdpa", DPDPA_RID, entry["document_type"], entry["what_it_would_show"]) == key
        tag, body = li_for(html, key)
        assert f'data-missing-evidence="{entry["document_type"]}"' in tag
        assert 'data-rfi-state="available"' in tag
        text = expected_text("dpdpa", DPDPA_RID, entry["what_it_would_show"])
        assert module.request_text("dpdpa", DPDPA_RID, entry["document_type"], entry["what_it_would_show"]) == text
        preview = open_tag(body, "data-rfi-request-preview")
        assert text in body[body.index(preview):]
        form = open_tag(body, "data-rfi-add-form")
        assert f'hx-post="{add_url(assessment, row)}"' in form
        assert f'hx-target="#conclusion-card-{row.id}"' in form
        assert f'name="request_key" value="{key}"' in body
        assert "Add to draft RFI" in body
        assert "data-rfi-withdraw-form" not in body

    # The card field is additive: the new MissingEvidence / RequirementCard fields trail and default.
    from app.services import requirement_card

    fields = [field.name for field in dataclasses.fields(requirement_card.MissingEvidence)]
    assert fields[:3] == ["document_type", "label", "what_it_would_show"]
    assert fields[3:] == ["request_key", "request_text", "rfi_state", "rfi_status_label"]
    card_fields = dataclasses.fields(requirement_card.RequirementCard)
    assert card_fields[-1].name == "other_rfi_requests" and card_fields[-1].default == ()

    # Deterministic text: no LLM was called (forbid_llm), and the text is stable across renders.
    again = card_html(conclusions_page(http, assessment), row.id)
    assert again == html
    assert rfi_events(db) == []


# --------------------------------------------------------------------------- #
# Scenario 2: add is one audit event, lands in the draft RFI, and is idempotent
# --------------------------------------------------------------------------- #


def test_scenario_2_add_records_one_event_updates_the_draft_and_is_idempotent(db, http, monkeypatch, flag_v2):
    assessment = build(db, monkeypatch)
    row = conclusion(db, assessment, "dpdpa", DPDPA_RID)
    version_before = row.version
    revisions_before = db.query(ConclusionRevision).filter_by(conclusion_id=row.id).count()
    before = draft(db, assessment)
    assert set(before["source"]) == V1_SOURCE_KEYS and before["schema_version"] == 1
    assert requested_items(before) == []

    detail = DPDPA_PRIVACY
    key = expected_key("dpdpa", DPDPA_RID, "privacy_policy", detail)
    response = add(http, assessment, row, key)
    assert response.status_code == 200, response.text
    assert response.headers["X-Toast-Message"] == ADDED_TOAST
    assert response.headers["X-Toast-Type"] == "success"
    assert f'id="conclusion-card-{row.id}"' in response.text
    tag, body = li_for(response.text, key)
    assert 'data-rfi-state="requested"' in tag
    assert STATE_REQUESTED in body
    assert "data-rfi-add-form" not in body
    withdraw_form = open_tag(body, "data-rfi-withdraw-form")
    assert f'hx-post="{withdraw_url(assessment, row)}"' in withdraw_form

    events = rfi_events(db)
    assert len(events) == 1
    event = events[0]
    assert (event.action, event.entity_type, event.entity_id, event.actor) == (
        REQUESTED_ACTION, "conclusion", row.id, "consultant:Priya",
    )
    run = latest_run(db, assessment, "dpdpa")
    assert json.loads(event.metadata_json) == {
        "request_key": key,
        "framework_id": "dpdpa",
        "requirement_id": DPDPA_RID,
        "document_type": "privacy_policy",
        "title": expected_title("dpdpa", "privacy_policy"),
        "request": expected_text("dpdpa", DPDPA_RID, detail),
        "analysis_run_id": run.id,
    }

    after = draft(db, assessment)
    assert after["schema_version"] == 2
    assert after["source"]["schema_version"] == 2
    assert set(after["source"]) == V1_SOURCE_KEYS | {"evidence_requests"}
    assert after["source"]["evidence_requests"] == [[row.id, key]]
    assert {k: v for k, v in after["source"].items() if k not in ("schema_version", "evidence_requests")} == {
        k: v for k, v in before["source"].items() if k != "schema_version"
    }
    items = requested_items(after)
    assert len(items) == 1
    item = items[0]
    assert item == {
        "item_id": item["item_id"],
        "kind": ITEM_KIND,
        "title": json.loads(event.metadata_json)["title"],
        "request": expected_text("dpdpa", DPDPA_RID, detail),
        "required": True,
        "requirements": [["dpdpa", DPDPA_RID]],
        "document_type": "privacy_policy",
        "control_reference": None,
        "conclusion_id": None,
        "conclusion_version": None,
        "group": REQUESTED_GROUP,
        "request_refs": [[row.id, key]],
    }
    # Appended after every existing item, numbering continues.
    assert after["items"][: len(before["items"])] == before["items"]
    assert item["item_id"] == f"RFI-{len(before['items']) + 1:03d}"
    assert after["totals"] == before["totals"] | {
        "items": before["totals"]["items"] + 1,
        "required": before["totals"]["required"] + 1,
        "evidence_requests": 1,
    }

    # Double click: no second event, same draft bytes, a distinct toast.
    again = add(http, assessment, row, key, reviewer="Someone else")
    assert again.status_code == 200
    assert again.headers["X-Toast-Message"] == ALREADY_TOAST
    assert len(rfi_events(db)) == 1
    assert rfi_requests.canonical_bytes(draft(db, assessment)) == rfi_requests.canonical_bytes(after)

    # The Conclusion is untouched: no revision, no version bump (adding evidence is not a decision).
    db.refresh(row)
    assert row.version == version_before
    assert db.query(ConclusionRevision).filter_by(conclusion_id=row.id).count() == revisions_before
    # And the card's approval blocker is unchanged by the request (no new gate).
    record_test_period(db, assessment)  # P6-6: D-P6-G
    db.commit()
    card = conclusion_review.conclusion_card(db, assessment_id=assessment.id, conclusion_id=row.id)
    assert card.approval_blocker != rer().RFI_REQUEST_STALE_MESSAGE
    assert not any(
        token in (card.approval_blocker or "") for token in ("RFI", "draft RFI", "evidence request")
    )


# --------------------------------------------------------------------------- #
# Scenario 3: refusals write nothing
# --------------------------------------------------------------------------- #


def test_scenario_3_stale_foreign_and_v1_requests_are_refused(db, http, monkeypatch, flag_v2):
    from app.services import analysis_pipeline
    assessment = build(db, monkeypatch)
    row = conclusion(db, assessment, "dpdpa", DPDPA_RID)
    before = rfi_requests.canonical_bytes(draft(db, assessment))

    stale = add(http, assessment, row, "0" * 16)
    assert stale.status_code == 409
    assert stale.json() == {"detail": STALE_MESSAGE}
    assert stale.headers["X-Toast-Type"] == "error"

    blank = add(http, assessment, row, "")
    assert blank.status_code == 409 and blank.json() == {"detail": STALE_MESSAGE}

    # A key from another Conclusion's card is stale on this one.
    iso = conclusion(db, assessment, "iso27001", ISO_RID)
    iso_key = expected_key("iso27001", ISO_RID, "privacy_policy", ISO_PRIVACY)
    assert add(http, assessment, row, iso_key).status_code == 409

    other = seed_assessment(db, ("dpdpa",))
    key = expected_key("dpdpa", DPDPA_RID, "privacy_policy", DPDPA_PRIVACY)
    foreign = http.post(add_url(other, row), data={"request_key": key, "reviewer_name": "Priya"})
    assert foreign.status_code == 404 and foreign.json() == {"detail": CONCLUSION_NOT_FOUND}
    unknown = http.post(
        f"/api/assessments/{assessment.id}/rfi-requests/no-such-conclusion",
        data={"request_key": key, "reviewer_name": "Priya"},
    )
    assert unknown.status_code == 404 and unknown.json() == {"detail": CONCLUSION_NOT_FOUND}

    # v1 cards list suggested documents but offer no add control, and the route refuses them.
    v1 = seed_assessment(db, ("iso27001",))
    add_evidence(db, v1, filename="policy.pdf", text=policy_text(Q_CONSENT))
    context = analysis_pipeline.start_runs(db, assessment_id=v1.id, framework_ids=["iso27001"])
    analysis_pipeline.record_framework_run(
        db, context, framework_id="iso27001",
        assessments=[{
            "requirement_id": "ISO.A5.2", "compliance_status": "non_compliant",
            "current_state": "Roles are not assigned.", "evidence_quote": "",
            "gap_description": "No roles.", "risk_level": "low", "remediation_action": "Assign roles.",
        }],
        desk_review_data=None, gap_report_id="legacy-report",
    )
    db.commit()
    v1_row = conclusion(db, v1, "iso27001", "ISO.A5.2")
    v1_html = card_html(conclusions_page(http, v1), v1_row.id)
    request = next(
        item for item in FrameworkRegistry.get("iso27001").evidence_requests if "ISO.A5.2" in item.maps_to
    )
    assert open_tag(v1_html, "data-missing-evidence", request.document_type)
    assert "data-rfi-add-form" not in v1_html and "data-rfi-request-key" not in v1_html
    v1_key = expected_key("iso27001", "ISO.A5.2", request.document_type, request.reason)
    refused = add(http, v1, v1_row, v1_key)
    assert refused.status_code == 409 and refused.json() == {"detail": STALE_MESSAGE}

    assert rfi_events(db) == []
    assert rfi_requests.canonical_bytes(draft(db, assessment)) == before


# --------------------------------------------------------------------------- #
# Scenario 4: withdraw, re-add, idempotent withdraw, unknown withdraw
# --------------------------------------------------------------------------- #


def test_scenario_4_withdraw_restores_the_prior_draft_and_history_is_append_only(db, http, monkeypatch, flag_v2):
    assessment = build(db, monkeypatch)
    row = conclusion(db, assessment, "dpdpa", DPDPA_RID)
    key = expected_key("dpdpa", DPDPA_RID, "privacy_policy", DPDPA_PRIVACY)
    before = draft(db, assessment)
    assert add(http, assessment, row, key).status_code == 200

    response = withdraw(http, assessment, row, key)
    assert response.status_code == 200, response.text
    assert response.headers["X-Toast-Message"] == WITHDRAWN_TOAST
    tag, body = li_for(response.text, key)
    assert 'data-rfi-state="available"' in tag and "data-rfi-add-form" in body
    events = rfi_events(db)
    assert [event.action for event in events] == [REQUESTED_ACTION, WITHDRAWN_ACTION]
    assert events[1].entity_id == row.id and events[1].entity_type == "conclusion"
    assert json.loads(events[1].metadata_json) == {"request_key": key, "document_type": "privacy_policy"}

    # With no active request the draft and its source are byte-identical to before (schema 1).
    assert rfi_requests.canonical_bytes(draft(db, assessment)) == rfi_requests.canonical_bytes(before)

    # Withdrawing again is a no-op; withdrawing a never-requested key is a 404.
    again = withdraw(http, assessment, row, key)
    assert again.status_code == 200 and again.headers["X-Toast-Message"] == ALREADY_WITHDRAWN_TOAST
    unknown = withdraw(http, assessment, row, "f" * 16)
    assert unknown.status_code == 404 and unknown.json() == {"detail": NOT_FOUND_MESSAGE}
    assert len(rfi_events(db)) == 2

    # Re-adding appends a new event; nothing is updated or removed.
    assert add(http, assessment, row, key).headers["X-Toast-Message"] == ADDED_TOAST
    assert [event.action for event in rfi_events(db)] == [REQUESTED_ACTION, WITHDRAWN_ACTION, REQUESTED_ACTION]
    assert [item["request_refs"] for item in requested_items(draft(db, assessment))] == [[[row.id, key]]]


# --------------------------------------------------------------------------- #
# Scenario 5: requests reach the client only through a new, issued RFI version
# --------------------------------------------------------------------------- #


def test_scenario_5_requests_flow_into_the_next_issued_version_only(db, http, monkeypatch, flag_v2):
    assessment = build(db, monkeypatch)
    row = conclusion(db, assessment, "dpdpa", DPDPA_RID)
    key = expected_key("dpdpa", DPDPA_RID, "privacy_policy", DPDPA_PRIVACY)

    first = generate(http, assessment)
    assert first.status_code == 200, first.text
    first_id = first.json()["snapshot_id"]
    assert add(http, assessment, row, key).status_code == 200

    # The older draft no longer matches the source: it cannot be issued.
    stale = issue(http, assessment, first_id)
    assert stale.status_code == 409
    assert stale.json() == {"detail": rfi_requests.RFI_STALE_MESSAGE}

    second = generate(http, assessment)
    assert second.status_code == 200, second.text
    second_id = second.json()["snapshot_id"]
    assert issue(http, assessment, second_id).status_code == 200
    snapshot = db.get(ReportSnapshot, second_id)
    document = report_snapshots.read_rfi_document(db, snapshot)
    [item] = requested_items(document)
    assert item["request_refs"] == [[row.id, key]]
    assert document["source"]["evidence_requests"] == [[row.id, key]]

    pdf = http.get(f"/api/assessments/{assessment.id}/snapshots/{second_id}/file")
    with pdfplumber.open(io.BytesIO(pdf.content)) as parsed:
        text = " ".join((page.extract_text() or "") for page in parsed.pages)
    text = " ".join(text.split())
    assert item["item_id"] in text and REQUESTED_GROUP in text
    assert "grievance officer" in text

    # The card now shows the issued state with the version label and item id.
    html = card_html(conclusions_page(http, assessment), row.id)
    tag, body = li_for(html, key)
    assert 'data-rfi-state="issued"' in tag
    assert STATE_ISSUED.format(version_label="v2", item_id=item["item_id"]) in body
    assert open_tag(body, "data-rfi-withdraw-form")

    # Withdrawing later never touches the issued version (write-once, P5-6).
    sidecar = report_snapshots.rfi_document_path(snapshot).read_bytes()
    pdf_bytes = report_snapshots.snapshot_path(snapshot).read_bytes()
    assert withdraw(http, assessment, row, key).status_code == 200
    assert report_snapshots.rfi_document_path(snapshot).read_bytes() == sidecar
    assert report_snapshots.snapshot_path(snapshot).read_bytes() == pdf_bytes
    assert requested_items(draft(db, assessment)) == []
    rows = report_snapshots.rfi_snapshot_rows(
        db, assessment, current_source=rfi_requests.current_source(db, assessment),
    )
    issued_row = next(r for r in rows if r.snapshot.id == second_id)
    assert issued_row.state == "issued" and issued_row.source_changed


# --------------------------------------------------------------------------- #
# Scenario 6: one document requested once across frameworks; "other" stays separate
# --------------------------------------------------------------------------- #


def test_scenario_6_requests_merge_by_document_type_across_frameworks(db, http, monkeypatch, flag_v2):
    assessment = build(db, monkeypatch)
    dpdpa = conclusion(db, assessment, "dpdpa", DPDPA_RID)
    iso = conclusion(db, assessment, "iso27001", ISO_RID)
    dpdpa_privacy = expected_key("dpdpa", DPDPA_RID, "privacy_policy", DPDPA_PRIVACY)
    dpdpa_other = expected_key("dpdpa", DPDPA_RID, "other", DPDPA_OTHER)
    iso_privacy = expected_key("iso27001", ISO_RID, "privacy_policy", ISO_PRIVACY)
    for row, key in ((iso, iso_privacy), (dpdpa, dpdpa_other), (dpdpa, dpdpa_privacy)):
        assert add(http, assessment, row, key).status_code == 200

    document = draft(db, assessment)
    items = requested_items(document)
    assert [item["document_type"] for item in items] == ["privacy_policy", "other"]
    privacy, other = items
    # Ordered by the first active request; the document is asked for once.
    assert privacy["requirements"] == [["iso27001", ISO_RID], ["dpdpa", DPDPA_RID]]
    assert privacy["request_refs"] == [[iso.id, iso_privacy], [dpdpa.id, dpdpa_privacy]]
    assert privacy["request"] == " ".join((
        expected_text("iso27001", ISO_RID, ISO_PRIVACY),
        expected_text("dpdpa", DPDPA_RID, DPDPA_PRIVACY),
    ))
    assert privacy["title"] == expected_title("iso27001", "privacy_policy")
    assert other["title"] == OTHER_TITLE
    assert other["requirements"] == [["dpdpa", DPDPA_RID]]
    assert other["request"] == expected_text("dpdpa", DPDPA_RID, DPDPA_OTHER)
    assert document["source"]["evidence_requests"] == sorted(
        [[iso.id, iso_privacy], [dpdpa.id, dpdpa_other], [dpdpa.id, dpdpa_privacy]]
    )
    assert document["totals"]["evidence_requests"] == 2

    # Withdrawing one framework's request leaves the other's in the same item.
    assert withdraw(http, assessment, iso, iso_privacy).status_code == 200
    privacy_after = next(
        item for item in requested_items(draft(db, assessment)) if item["document_type"] == "privacy_policy"
    )
    assert privacy_after["requirements"] == [["dpdpa", DPDPA_RID]]
    assert privacy_after["request_refs"] == [[dpdpa.id, dpdpa_privacy]]

    # Rendered items reuse the document-row shape with the new status line.
    rendered = [r for r in rfi_requests.render_items(draft(db, assessment)) if r["chapter"] == REQUESTED_GROUP]
    assert [r["current_status"] for r in rendered] == [ITEM_STATUS, ITEM_STATUS]
    assert rendered[0]["requirements"] == [DPDPA_RID] and rendered[0]["requirement_id"] == ""
    assert rendered[0]["priority"] == "Required"


# --------------------------------------------------------------------------- #
# Scenario 7: framework-conditional copy
# --------------------------------------------------------------------------- #


def test_scenario_7_request_copy_is_framework_conditional(db, http, monkeypatch, flag_v2):
    module = rer()
    iso_text = module.request_text("iso27001", ISO_RID, "privacy_policy", ISO_PRIVACY)
    iso = FrameworkRegistry.get("iso27001")
    assert iso.name in iso_text and iso.get_control(ISO_RID).title in iso_text
    dpdpa = FrameworkRegistry.get("dpdpa")
    assert dpdpa.name not in iso_text
    assert not re.search(r"DPDPA|Data Principal|Data Fiduciary|Digital Personal Data", iso_text)
    assert dpdpa.name in module.request_text("dpdpa", DPDPA_RID, "privacy_policy", DPDPA_PRIVACY)

    # Every fixed string P6-7b adds names no framework.
    for name in (
        "RFI_REQUESTED_GROUP", "RFI_OTHER_TITLE", "RFI_EVIDENCE_REQUEST_STATUS", "REQUEST_TEXT_FORMAT",
        "STATE_REQUESTED_LABEL", "STATE_ISSUED_LABEL", "ADDED_TOAST", "ALREADY_TOAST", "WITHDRAWN_TOAST",
        "ALREADY_WITHDRAWN_TOAST", "RFI_REQUEST_STALE_MESSAGE", "RFI_REQUEST_NOT_FOUND_MESSAGE",
        "RFI_PAGE_REQUESTS_NOTE", "REQUEST_DETAIL_FALLBACK",
    ):
        value = getattr(module, name)
        assert not re.search(r"DPDPA|ISO|NIST|GDPR|HIPAA|PCI|Data Principal|India", value), name
    assert module.RFI_REQUESTED_GROUP == REQUESTED_GROUP
    assert module.REQUEST_TEXT_FORMAT == REQUEST_TEXT_FORMAT
    assert module.REQUESTED_ACTION == REQUESTED_ACTION and module.WITHDRAWN_ACTION == WITHDRAWN_ACTION

    # Empty detail falls back to the pack's reviewed reason, then to the generic line.
    reason = next(item.reason for item in iso.evidence_requests if item.document_type == "privacy_policy")
    assert module.request_text("iso27001", ISO_RID, "privacy_policy", "  ").startswith(" ".join(reason.split()))
    assert module.request_text("iso27001", ISO_RID, "other", "").startswith(module.REQUEST_DETAIL_FALLBACK)

    # An ISO-only assessment's card and draft carry no DPDPA copy.
    assessment = build(db, monkeypatch, frameworks=("iso27001",))
    row = conclusion(db, assessment, "iso27001", ISO_RID)
    key = expected_key("iso27001", ISO_RID, "privacy_policy", ISO_PRIVACY)
    html = card_html(conclusions_page(http, assessment), row.id)
    assert dpdpa.name not in html
    assert add(http, assessment, row, key).status_code == 200
    item_bytes = json.dumps(requested_items(draft(db, assessment)))
    assert dpdpa.name not in item_bytes and "DPDPA" not in item_bytes


# --------------------------------------------------------------------------- #
# Scenario 8: the RFI page lists requests and can withdraw them
# --------------------------------------------------------------------------- #


def test_scenario_8_rfi_page_lists_and_withdraws_requests(db, http, monkeypatch, flag_v2):
    assessment = build(db, monkeypatch)
    page = http.get(f"/assessments/{assessment.id}/rfi")
    assert page.status_code == 200
    assert "data-rfi-requests" not in page.text and PAGE_NOTE not in page.text

    row = conclusion(db, assessment, "dpdpa", DPDPA_RID)
    key = expected_key("dpdpa", DPDPA_RID, "privacy_policy", DPDPA_PRIVACY)
    assert add(http, assessment, row, key).status_code == 200
    page = http.get(f"/assessments/{assessment.id}/rfi").text
    assert PAGE_NOTE in page
    assert page.count(f'data-rfi-kind="{ITEM_KIND}"') == 1
    entry = open_tag(page, "data-rfi-request", key)
    assert f'data-conclusion-id="{row.id}"' in entry
    start = page.index(entry)
    body = unescape(page[start: page.index("</li>", start)])
    assert expected_text("dpdpa", DPDPA_RID, DPDPA_PRIVACY) in body
    assert f"dpdpa:{DPDPA_RID}" in body and "Priya" in body
    form = open_tag(body, "data-rfi-withdraw-form")
    assert f'hx-post="{withdraw_url(assessment, row)}"' in form
    assert 'name="origin" value="rfi"' in body

    response = withdraw(http, assessment, row, key, origin="rfi")
    assert response.status_code == 200
    assert response.headers["HX-Redirect"] == f"/assessments/{assessment.id}/rfi"
    assert response.headers["X-Toast-Message"] == WITHDRAWN_TOAST
    assert "data-rfi-requests" not in http.get(f"/assessments/{assessment.id}/rfi").text

    source = (REPO_ROOT / "app/templates/pages/rfi.html").read_text()
    assert "|safe" not in source and "'" not in source


# --------------------------------------------------------------------------- #
# Scenario 9: frozen text survives re-analysis; the card keeps a withdraw control
# --------------------------------------------------------------------------- #


def test_scenario_9_request_text_is_frozen_when_reanalysis_changes_missing_evidence(db, http, monkeypatch, flag_v2):
    from tests.test_p6_4_v2_judge import JudgeProvider
    from tests.test_p6_7_requirement_card import _trigger

    # The fake judge stays installed for the re-analysis; no real LLM is reachable.
    assessment = build(db, monkeypatch, refuse_llm=False)
    row = conclusion(db, assessment, "dpdpa", DPDPA_RID)
    key = expected_key("dpdpa", DPDPA_RID, "privacy_policy", DPDPA_PRIVACY)
    assert add(http, assessment, row, key).status_code == 200
    frozen = requested_items(draft(db, assessment))

    changed = "A notice that shows the retention period for each purpose"

    def rescripted(rid, criterion_ids, claim_ids, request):
        value = e2e_script(rid, criterion_ids, claim_ids, request)
        if rid == DPDPA_RID:
            value["missing_evidence"] = [{"document_type": "privacy_policy", "what_it_would_show": changed}]
        return value

    JudgeProvider(script=rescripted).install(monkeypatch)
    assert _trigger(db, assessment)["status"] == "completed"
    forbid_llm(monkeypatch)

    # The draft keeps the text the consultant saw when they clicked.
    assert requested_items(draft(db, assessment)) == frozen
    html = card_html(conclusions_page(http, assessment), row.id)
    new_key = expected_key("dpdpa", DPDPA_RID, "privacy_policy", changed)
    new_tag, _ = li_for(html, new_key)
    assert 'data-rfi-state="available"' in new_tag
    old = open_tag(html, "data-rfi-request", key)
    assert 'data-rfi-state="requested"' in old
    start = html.index(old)
    body = unescape(html[start: html.index("</li>", start)])
    assert expected_text("dpdpa", DPDPA_RID, DPDPA_PRIVACY) in body
    assert open_tag(body, "data-rfi-withdraw-form")
    assert withdraw(http, assessment, row, key).status_code == 200
    assert requested_items(draft(db, assessment)) == []


# --------------------------------------------------------------------------- #
# Scenario 10: the P5-6 contract is unchanged when nobody adds a request
# --------------------------------------------------------------------------- #


def test_scenario_10_no_requests_means_the_p5_6_document_is_unchanged(db, http, monkeypatch, flag_v2):
    module = rer()
    assessment = build(db, monkeypatch)
    document = draft(db, assessment)
    assert document["schema_version"] == rfi_requests.RFI_DOCUMENT_SCHEMA_VERSION == 1
    assert set(document["source"]) == V1_SOURCE_KEYS
    assert set(document["totals"]) == {"items", "documents", "requirements", "required"}
    assert all(item["kind"] in ("document", "requirement") for item in document["items"])
    assert module.active_requests(db, assessment.id) == []
    assert "request_refs" not in rfi_requests.canonical_bytes(document).decode()


# --------------------------------------------------------------------------- #
# Scenario 11: standing guards (routes, sources, no LLM, no migration)
# --------------------------------------------------------------------------- #


def test_scenario_11_routes_and_source_guards():
    module = rer()
    paths = {route.path for route in app.routes if "rfi-requests" in getattr(route, "path", "")}
    assert paths == {
        "/api/assessments/{assessment_id}/rfi-requests/{conclusion_id}",
        "/api/assessments/{assessment_id}/rfi-requests/{conclusion_id}/withdraw",
    }
    # No new route under /conclusions (tests/test_conclusion_approval.py pins that set).
    assert not any("/conclusions" in path for path in paths)
    for path in ("app/services/rfi_evidence_requests.py", "app/services/rfi_requests.py"):
        source = (REPO_ROOT / path).read_text()
        for token in (".commit(", "delete", "llm_client", "services.grounding", "analysis_v2", "UPDATE "):
            assert token not in source, (path, token)
    source = (REPO_ROOT / "app/services/rfi_evidence_requests.py").read_text()
    assert "report_snapshots.create" not in source and "issue_snapshot" not in source
    assert dataclasses.is_dataclass(module.ActiveRequest) and module.ActiveRequest.__dataclass_params__.frozen
    versions = sorted((REPO_ROOT / "alembic" / "versions").glob("*.py"))
    assert not any("rfi_request" in path.name or "evidence_request" in path.name for path in versions)


# --------------------------------------------------------------------------- #
# Scenario 12: file-set guard (green before and after implementation)
# --------------------------------------------------------------------------- #

P6_7B_APP_FILES = {
    "app/services/rfi_evidence_requests.py",
    "app/services/rfi_requests.py",
    "app/services/requirement_card.py",
    "app/routers/requirement_review.py",
    "app/templates/components/requirement_card_body.html",
    "app/templates/pages/rfi.html",
}
P6_7B_FORBIDDEN = (
    "app/services/report_snapshots.py", "app/services/board_report.py", "app/services/approved_report.py",
    "app/services/conclusion_review.py", "app/services/analysis_v2.py", "app/services/grounding",
    "app/services/analysis_pipeline.py", "app/services/scoring.py", "app/services/report_basis.py",
    "app/services/magic_links.py", "app/services/review_queue.py", "app/services/standalone_workpaper.py",
    "app/models", "alembic", "app/utils", "app/routers/snapshots.py", "app/routers/web.py",
    "app/routers/conclusions.py", "app/routers/magic.py", "app/routers/reports.py",
    "app/templates/reports", "app/templates/base.html", "app/templates/components/conclusion_card.html",
    "app/templates/partials/rfi_links.html", "app/frameworks", "app/dpdpa", "app/config.py", "app/main.py",
    "requirements.txt", ".github", "Dockerfile", "scripts", "validation",
)
# P6-9 (tasks/handoffs/2026-09-28-p6-9-soa-roadmap-comparison.md) lands after P6-7b and
# legitimately touches these; tests/test_p6_9_file_set.py guards its file set.
# P6-2e: signed ISO / NIST criteria attach to the packs.
P6_2E_APP_FILES = {"app/frameworks/criteria/__init__.py", "app/frameworks/criteria/iso27001.py", "app/frameworks/criteria/nist_csf.py", "app/frameworks/definitions/iso27001.py", "app/frameworks/definitions/nist_csf.py"}
P6_9_APP_FILES = {
    "app/services/soa.py", "app/services/remediation_groups.py", "app/services/prior_period.py",
    "app/routers/soa.py", "app/templates/pages/soa.html", "app/main.py",
    "app/services/board_report.py", "app/templates/reports/board_report.html",
    "app/templates/pages/report_snapshots.html",
}


# LLM request deadline (claude/llm-request-deadline): wall-clock cap per provider call.
LLM_DEADLINE_FILES = {"app/config.py", "app/services/llm_client.py"}
# P6-8 B2 (tasks/handoffs/2026-09-28-p6-8-b2-docx-xlsx.md): DOCX/XLSX exports; tests/test_p6_8_b2_docx_xlsx.py guards them.
P6_8_B2_APP_FILES = {
    "app/services/board_exports.py", "app/routers/snapshots.py", "app/templates/pages/report_snapshots.html",
}

# P6-10 (tasks/handoffs/2026-09-28-p6-10-remediation-and-narrative.md, revised 2026-10-01): lands after
# B2 and P6-9; tests/test_p6_10a_remediation_draft.py and tests/test_p6_10b_narrative.py guard this set.
P6_10_APP_FILES = {
    "app/services/remediation_draft.py", "app/services/narrative.py", "app/routers/drafting.py",
    "app/main.py", "app/templates/partials/remediation_draft.html",
    "app/templates/components/conclusion_card.html", "app/templates/pages/narrative.html",
    "app/services/board_report.py", "app/templates/reports/board_report.html",
    "app/templates/pages/report_snapshots.html", "app/services/board_exports.py",
}
P6_10_EXTRA_PATHS = {"tests/golden/p6_8_board_document.json"}


from tests.p6_8_v3a_paths import V3A_APP_PATHS, V3A_EXCLUDES  # P6-8 V3-A per-PR allowance
from tests.p6_8_v3b_paths import V3B_APP_PATHS, V3B_EXCLUDES, is_v3b_path  # P6-8 V3-B per-PR allowance
from tests.yozora_backend_paths import YOZORA_BACKEND_APP_PATHS, YOZORA_BACKEND_EXCLUDES  # Yozora backend per-PR allowance
from tests.yozora_paths import YOZORA_EXCLUDES, YOZORA_S1_PATHS, YOZORA_S2_PATHS, YOZORA_S3_PATHS, YOZORA_S4_PATHS, YOZORA_S6_PATHS  # Yozora per-PR allowance


def _changed(*args: str) -> set[str]:
    return set(_git("diff", "--name-only", *args, "--", "app").split())


def test_scenario_12_p6_7b_touches_only_its_files():
    changed = _changed("main...HEAD") | _changed("HEAD") | set(
        _git("ls-files", "--others", "--exclude-standard", "app").split()
    )
    changed -= P6_9_APP_FILES
    changed -= P6_2E_APP_FILES
    changed -= LLM_DEADLINE_FILES
    changed -= P6_8_B2_APP_FILES
    changed -= set(V3A_APP_PATHS)  # P6-8 V3-A (tasks/handoffs/2026-10-01-board-report-v3-deck.md)
    changed = {path for path in changed if not is_v3b_path(path)}  # P6-8 V3-B
    changed -= P6_10_APP_FILES
    changed -= set(YOZORA_BACKEND_APP_PATHS)  # Yozora backend (tasks/handoffs/2026-10-03-yozora-backend-features.md)
    changed -= set(YOZORA_S1_PATHS)  # Yozora S1 (tasks/handoffs/2026-10-01-yozora-s1-handoff.md)
    changed -= set(YOZORA_S2_PATHS)  # Yozora S2 (tasks/handoffs/2026-10-01-yozora-s2-handoff.md)
    changed -= set(YOZORA_S4_PATHS)  # Yozora S4 (tasks/handoffs/2026-10-01-yozora-s4-handoff.md)
    changed -= set(YOZORA_S3_PATHS)  # Yozora S3 (tasks/handoffs/2026-10-01-yozora-s3-handoff.md)
    changed -= set(YOZORA_S6_PATHS)  # Yozora per-PR allowance
    assert changed <= P6_7B_APP_FILES, sorted(changed - P6_7B_APP_FILES)
    p6_9 = [f":(exclude){path}" for path in sorted(P6_9_APP_FILES | P6_2E_APP_FILES)]
    # P6-5b (tasks/handoffs/2026-09-28-p6-5-v2-ab-and-flip.md) lands after P6-7b: harness only.
    p6_9 += [f":(exclude)scripts/validation/{name}" for name in ("run_company.py", "ab_compare.py", "score.py")]
    p6_9 += [":(exclude)scripts/convert_criteria.py"]  # P6-2e
    p6_9 += [f":(exclude){path}" for path in sorted(LLM_DEADLINE_FILES)]
    p6_9 += [f":(exclude){path}" for path in sorted(P6_8_B2_APP_FILES | {"requirements.txt"})]  # P6-8 B2
    p6_9 += V3A_EXCLUDES  # P6-8 V3-A
    p6_9 += V3B_EXCLUDES  # P6-8 V3-B
    p6_9 += YOZORA_BACKEND_EXCLUDES  # Yozora backend
    p6_9 += YOZORA_EXCLUDES  # Yozora S1
    p6_9 += [f":(exclude){path}" for path in sorted(P6_10_APP_FILES | P6_10_EXTRA_PATHS)]  # P6-10
    forbidden = _git("diff", "--name-only", "main...HEAD", "--", *P6_7B_FORBIDDEN, *p6_9).split()
    forbidden += _git("diff", "--name-only", "HEAD", "--", *P6_7B_FORBIDDEN, *p6_9).split()
    assert forbidden == []
