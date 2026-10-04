"""Focused route contracts for the S4 engagement surfaces."""

import json
from datetime import datetime, timezone

from app.models.audit_event import AuditEvent
from app.models.report_snapshot import ReportSnapshot
from app.services.engagement_factory import add_assessment_to_engagement
from tests.yozora_support import (  # noqa: F401 - fixtures are used by name
    _register_frameworks,
    db,
    db_path,
    engine,
    http,
    upload_root,
)
from tests.yozora_support import seed_engagement


def test_engagements_list_is_available_and_uses_the_engagement_row(db, http):
    _client, engagement, _assessment = seed_engagement(db)
    page = http.get("/engagements")
    assert page.status_code == 200
    assert engagement.name in page.text
    assert f'href="/engagements/{engagement.id}"' in page.text


def test_engagements_list_empty_state_is_available(db, http):
    page = http.get("/engagements")
    assert page.status_code == 200
    assert "No engagements yet" in page.text


def test_reports_index_has_an_empty_state_without_issued_versions(http):
    page = http.get("/reports")
    assert page.status_code == 200
    assert "No issued reports" in page.text


def test_reports_index_links_an_issued_version_to_its_engagement_reports_tab(db, http):
    _client, engagement, _assessment = seed_engagement(db)
    snapshot = ReportSnapshot(
        id="snapshot-s4-issued",
        engagement_id=engagement.id,
        type="integrated_report",
        format="pdf",
        storage_path=f"reports/engagements/{engagement.id}/snapshot-s4-issued.pdf",
        generated_at=datetime(2026, 9, 29, 12, tzinfo=timezone.utc),
        is_issued=True,
    )
    db.add_all([
        snapshot,
        AuditEvent(
            id="audit-s4-generated",
            actor="consultant:Reviewer",
            action="report_snapshot.generated",
            entity_type="report_snapshot",
            entity_id=snapshot.id,
            metadata_json=json.dumps({"size_bytes": 1024}),
            created_at=datetime(2026, 9, 29, 12, tzinfo=timezone.utc),
        ),
        AuditEvent(
            id="audit-s4-issued",
            actor="consultant:Reviewer",
            action="report_snapshot.issued",
            entity_type="report_snapshot",
            entity_id=snapshot.id,
            metadata_json="{}",
            created_at=datetime(2026, 9, 29, 14, tzinfo=timezone.utc),
        ),
    ])
    db.commit()
    page = http.get("/reports")
    assert page.status_code == 200
    assert "Integrated engagement report (PDF)" in page.text
    assert f'href="/engagements/{engagement.id}/integrated-reports"' in page.text


def test_two_assessment_engagement_renders_stage_and_next_step(db, http):
    client, engagement, _assessment = seed_engagement(db)
    add_assessment_to_engagement(
        db,
        engagement=engagement,
        client=client,
        name="Operations",
        description="Operations scope",
        framework_ids=["dpdpa"],
    )
    page = http.get(f"/engagements/{engagement.id}")
    assert page.status_code == 200
    assert "Stage and next step" in page.text
    assert "Upload evidence" in page.text or "Scope" in page.text


# --- Visible, working controls (no hidden stand-ins) --------------------------------------
# Every action on these pages must be a control the user can see. These helpers parse the page
# and treat an element as hidden when it, or any ancestor, has display:none, the hidden
# attribute, the sr-only class, or is a type=hidden input.

from html.parser import HTMLParser  # noqa: E402

from app.services import retention  # noqa: E402

_VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class _Tree(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack: list[tuple[str, dict]] = []
        self.elements: list[tuple[str, dict, list[dict]]] = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.elements.append((tag, attrs, [a for _, a in self.stack]))
        if tag not in _VOID:
            self.stack.append((tag, attrs))

    def handle_startendtag(self, tag, attrs):
        self.elements.append((tag, dict(attrs), [a for _, a in self.stack]))

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break


def _hidden(attrs: dict) -> bool:
    style = (attrs.get("style") or "").replace(" ", "").lower()
    return (
        "display:none" in style
        or "hidden" in attrs
        or "sr-only" in (attrs.get("class") or "").split()
        or attrs.get("type") == "hidden"
    )


def _matches(attrs: dict, match: dict) -> bool:
    """Keyword names map to attributes (data_issue_control -> data-issue-control); True means present."""
    for key, value in match.items():
        name = key.replace("_", "-")
        if value is True:
            if name not in attrs:
                return False
        elif attrs.get(name) != value:
            return False
    return True


def _main(html: str) -> str:
    start = html.index('<main class="shell-content page">')
    return html[start : html.index("</main>", start)]


def _elements(html: str, tag: str, **match) -> list[tuple[dict, bool]]:
    """(attrs, visible) for each element of the page content matching tag and attributes."""
    tree = _Tree()
    tree.feed(_main(html))
    found = []
    for element_tag, attrs, ancestors in tree.elements:
        if element_tag != tag:
            continue
        if not _matches(attrs, match):
            continue
        visible = not _hidden(attrs) and not any(_hidden(ancestor) for ancestor in ancestors)
        found.append((attrs, visible))
    return found


def _visible(html: str, tag: str, **match) -> list[dict]:
    return [attrs for attrs, visible in _elements(html, tag, **match) if visible]


def _assert_no_display_none(html: str):
    assert "display:none" not in _main(html).replace(" ", ""), "page content hides markup with display:none"


def _integrated_snapshot(db, engagement, snapshot_id, generated_at, *, issued=False):
    snapshot = ReportSnapshot(
        id=snapshot_id,
        engagement_id=engagement.id,
        type="integrated_report",
        format="pdf",
        storage_path=f"reports/engagements/{engagement.id}/{snapshot_id}.pdf",
        generated_at=generated_at,
        is_issued=issued,
    )
    db.add(snapshot)
    db.flush()
    db.add(
        AuditEvent(
            id=f"audit-generated-{snapshot_id}",
            actor="consultant:Priya Sharma",
            action="report_snapshot.generated",
            entity_type="report_snapshot",
            entity_id=snapshot_id,
            metadata_json=json.dumps({"size_bytes": 1887437, "sha256": "a" * 64}),
            created_at=generated_at,
        )
    )
    if issued:
        db.add(
            AuditEvent(
                id=f"audit-issued-{snapshot_id}",
                actor="consultant:Priya Sharma",
                action="report_snapshot.issued",
                entity_type="report_snapshot",
                entity_id=snapshot_id,
                metadata_json="{}",
                created_at=generated_at,
            )
        )
    db.commit()


def _two_assessment_engagement(db):
    client, engagement, first = seed_engagement(db)
    add_assessment_to_engagement(
        db, engagement=engagement, client=client, name="Operations", description="Operations scope", framework_ids=["dpdpa"],
    )
    return client, engagement, first


def test_integrated_report_versions_have_visible_download_issue_and_name(db, http):
    _client, engagement, _assessment = seed_engagement(db)
    _integrated_snapshot(db, engagement, "snap-v1", datetime(2026, 9, 11, 12, tzinfo=timezone.utc), issued=True)
    _integrated_snapshot(db, engagement, "snap-v2", datetime(2026, 9, 30, 12, tzinfo=timezone.utc))
    page = http.get(f"/engagements/{engagement.id}/integrated-reports").text
    api = f"/api/engagements/{engagement.id}/integrated-reports"
    downloads = _visible(page, "a", data_download_version=True)
    assert sorted(a["href"] for a in downloads) == [f"{api}/snap-v1/file", f"{api}/snap-v2/file"]
    assert all(a.get("hx-boost") == "false" and "download" in a for a in downloads)
    issue_buttons = _visible(page, "button", data_modal_open="issue-modal")
    assert len(issue_buttons) == 1
    (form,) = [attrs for attrs, _ in _elements(page, "form", data_issue_control=True)]
    assert form["hx-post"] == f"{api}/snap-v2/issue" and form["hx-include"] == "#reviewer-name"
    assert _visible(page, "input", id="reviewer-name")
    assert _visible(page, "form", data_generate_control=True)[0]["hx-post"] == api
    # The issue-state specimen opens the same modal, with the real form inside it.
    specimen = http.get(f"/engagements/{engagement.id}/integrated-reports?state=issue").text
    assert _visible(specimen, "form", data_issue_control=True)
    assert "Issue version 2 of the integrated report?" in specimen
    _assert_no_display_none(page)


def test_engagement_overview_archive_unarchive_and_tools_are_visible(db, http):
    _client, engagement, first = _two_assessment_engagement(db)
    page = http.get(f"/engagements/{engagement.id}").text
    assert _visible(page, "button", data_archive_engagement=True)
    (archive,) = [attrs for attrs, _ in _elements(page, "form", data_archive_control=True)]
    assert archive["hx-post"] == f"/api/engagements/{engagement.id}/archive" and archive["hx-include"] == "#reviewer-name"
    assert _visible(page, "input", id="reviewer-name")
    assert _visible(page, "a", href=f"/engagements/{engagement.id}/aws-evidence")
    assert _visible(page, "a", href=f"/assessments/{first.id}")
    assert any(attrs.get("hx-post") == f"/engagements/{engagement.id}/magic-links" for attrs in _visible(page, "form"))
    _assert_no_display_none(page)

    assert http.post(f"/api/engagements/{engagement.id}/archive", data={"reviewer_name": "Priya"}).status_code == 200
    archived = http.get(f"/engagements/{engagement.id}").text
    assert _visible(archived, "button", data_modal_open="unarchive-modal")
    (unarchive,) = [attrs for attrs, _ in _elements(archived, "form", data_unarchive_control=True)]
    assert unarchive["hx-post"] == f"/api/engagements/{engagement.id}/unarchive" and unarchive["hx-include"] == "#reviewer-name"
    purge_links = _visible(archived, "a", data_purge_preview_link=True)
    assert purge_links and all(a["href"] == f"/engagements/{engagement.id}/purge" for a in purge_links)
    assert "by Priya" in archived
    _assert_no_display_none(archived)


def test_purge_page_shows_counts_reasons_and_the_typed_name_form(db, http):
    _client, engagement, _assessment = _two_assessment_engagement(db)
    assert http.post(f"/api/engagements/{engagement.id}/archive", data={"reviewer_name": "Priya"}).status_code == 200
    blocked = http.get(f"/engagements/{engagement.id}/purge").text
    assert _visible(blocked, "li", data_purge_reason="retention_not_elapsed")
    plan = retention.build_purge_plan(db, db.get(type(engagement), engagement.id))
    assert len(_visible(blocked, "tr", data_purge_count=True)) == len(plan.row_counts)
    assert not _elements(blocked, "form", data_purge_form=True)
    _assert_no_display_none(blocked)

    event = db.query(AuditEvent).filter(AuditEvent.entity_id == engagement.id, AuditEvent.action == "engagement.archived").one()
    event.created_at = datetime(2010, 1, 1, tzinfo=timezone.utc)
    db.commit()
    eligible = http.get(f"/engagements/{engagement.id}/purge").text
    assert _visible(eligible, "button", data_modal_open="purge-modal")
    (form,) = [attrs for attrs, _ in _elements(eligible, "form", data_purge_form=True)]
    assert form["hx-post"] == f"/api/engagements/{engagement.id}/purge" and form["data-confirm-value"] == engagement.name
    inputs = {attrs.get("name"): attrs for attrs, _ in _elements(eligible, "input") if attrs.get("id") in {"confirm-name", "reviewer-name"}}
    assert set(inputs) == {"confirm_name", "reviewer_name"} and "value" not in inputs["confirm_name"]
    specimen = http.get(f"/engagements/{engagement.id}/purge?state=confirm").text
    assert _visible(specimen, "form", data_purge_form=True)
    _assert_no_display_none(eligible)


def test_new_engagement_new_client_fields_and_roadmap_frameworks_are_visible(db, http):
    seed_engagement(db, client_name="Meridian")
    page = http.get("/engagements/new?state=new-client").text
    for field_id in ("company_name", "industry", "company_size"):
        assert _visible(page, "input" if field_id == "company_name" else "select", id=field_id), field_id
    roadmap = _visible(page, "label", data_roadmap_framework=True)
    assert len(roadmap) == 3
    assert all(label["title"] == "Roadmap — control data present, analysis pipeline coming" for label in roadmap)
    disabled = {attrs["value"] for attrs in _visible(page, "input", name="selected_frameworks") if "disabled" in attrs}
    assert disabled == {"gdpr", "hipaa", "pci_dss"}
    existing = http.get("/engagements/new").text
    client_options = [attrs.get("value") for attrs, _ in _elements(existing, "option") if attrs.get("value")]
    assert client_options and all(value.count("-") == 4 for value in client_options if value not in {"gap_assessment", "audit", "readiness"})
    _assert_no_display_none(page)
    _assert_no_display_none(existing)


def test_new_engagement_new_client_posts_industry_and_size(db, http):
    response = http.post(
        "/engagements",
        data={
            "client_mode": "new", "company_name": "Visible Client", "industry": "fintech", "company_size": "sme",
            "engagement_name": "Visible engagement", "engagement_type": "gap_assessment", "selected_frameworks": "dpdpa",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    from app.models.client import Client

    client = db.query(Client).filter(Client.name == "Visible Client").one()
    assert (client.industry, client.size) == ("fintech", "sme")


def test_engagement_list_rows_are_the_visible_links(db, http):
    _client, engagement, _assessment = seed_engagement(db)
    page = http.get("/engagements").text
    rows = _visible(page, "tr", data_engagement_row=True)
    assert [row["data-href"] for row in rows] == [f"/engagements/{engagement.id}"]
    assert _visible(page, "a", href=f"/engagements/{engagement.id}")
    _assert_no_display_none(page)


def test_remediation_export_and_rollup_are_visible(db, http):
    _client, engagement, _assessment = seed_engagement(db)
    page = http.get(f"/engagements/{engagement.id}/remediation").text
    (export,) = _visible(page, "a", data_export_actions=True)
    assert export["href"] == f"/engagements/{engagement.id}/remediation/export.xlsx"
    assert export.get("hx-boost") == "false" and "download" in export
    _assert_no_display_none(page)
