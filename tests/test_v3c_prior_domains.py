"""V3-C backend: per-domain prior scores in the board report's prior-period comparison.

Handoff: tasks/handoffs/2026-10-04-v3c-prior-domain-scores.md. Each compared framework entry in
`prior_period["frameworks"]` carries `domains`: the current document's domain order, matched to the
prior report's stored `framework_sections` by domain_id, compared only when both scores are numbers.
Board report PDFs are stubbed (`stub_render`): WeasyPrint is not needed here.
"""

from __future__ import annotations

import json

from app.services import report_snapshots
from tests.p6_9_support import (  # noqa: F401  (fixtures are used by name)
    PERIOD_1,
    _no_llm,
    _register_frameworks,
    build,
    db,
    db_path,
    gate,
    http,
    new_engagement,
    release,
    released_assessment,
    stub_render,
    upload_root,
)
from tests.test_p6_9_prior_period import FRAMEWORKS, P1_OUTCOMES, _craft_issued, _current, _issued_period

DOMAIN_KEYS = {"domain_id", "title", "prior_score", "current_score", "score_delta", "compared"}


def _sections(document):
    return {section["framework_id"]: section for section in document["framework_sections"]}


def _released_base(db, http, gate, monkeypatch, engagement):
    """An un-issued P1 assessment and its built document, to craft prior sidecars from."""
    p1, _ = released_assessment(
        db, http, gate, monkeypatch, engagement, frameworks=FRAMEWORKS, outcomes=P1_OUTCOMES, period=PERIOD_1,
    )
    release(db, p1)
    return p1, build(db, p1)


def test_domains_compare_two_issued_reports_in_current_order(db, http, gate, monkeypatch, stub_render):
    engagement = new_engagement(db)
    _, p1_snapshot = _issued_period(db, http, gate, monkeypatch, engagement, period=PERIOD_1)
    prior_sections = _sections(report_snapshots.read_board_report_document(db, p1_snapshot))
    p2 = _current(db, http, gate, monkeypatch, engagement)
    document = build(db, p2)
    current_sections = _sections(document)

    deltas = []
    for entry in document["prior_period"]["frameworks"]:
        framework_id = entry["framework_id"]
        assert entry["compared"] is True
        current_domains = current_sections[framework_id]["domains"]
        prior_scores = {d["domain_id"]: d["score"] for d in prior_sections[framework_id]["domains"]}
        assert [d["domain_id"] for d in entry["domains"]] == [d["domain_id"] for d in current_domains]
        for row, current in zip(entry["domains"], current_domains):
            assert set(row) == DOMAIN_KEYS
            assert row["title"] == current["title"]
            assert row["current_score"] == current["score"]
            assert row["prior_score"] == prior_scores[current["domain_id"]]
            both = row["prior_score"] is not None and row["current_score"] is not None
            assert row["compared"] is both
            if both:
                assert row["score_delta"] == round(row["current_score"] - row["prior_score"], 1)
                deltas.append(row["score_delta"])
            else:
                assert row["score_delta"] is None
    # The P1 -> P2 outcomes move at least one domain score.
    assert any(delta != 0 for delta in deltas)


def test_domain_out_of_scope_in_one_report_is_not_compared(db, http, gate, monkeypatch, stub_render):
    engagement = new_engagement(db)
    p1, base = _released_base(db, http, gate, monkeypatch, engagement)
    p2 = _current(db, http, gate, monkeypatch, engagement)
    current = _sections(build(db, p2))["dpdpa"]["domains"]
    scored = [d for d in current if d["score"] is not None]
    assert scored, "fixture needs at least one scored DPDPA domain"
    target = scored[0]["domain_id"]

    crafted = json.loads(json.dumps(base))
    for domain in _sections(crafted)["dpdpa"]["domains"]:
        if domain["domain_id"] == target:
            domain["score"], domain["rating"] = None, None
    _craft_issued(db, p1, crafted)

    domains = {d["domain_id"]: d for d in build(db, p2)["prior_period"]["frameworks"][0]["domains"]}
    assert domains[target]["prior_score"] is None
    assert domains[target]["current_score"] == scored[0]["score"]
    assert (domains[target]["compared"], domains[target]["score_delta"]) == (False, None)
    # Out of scope in the current report: the row is still present, uncompared.
    for domain in current:
        if domain["score"] is None:
            row = domains[domain["domain_id"]]
            assert (row["current_score"], row["score_delta"], row["compared"]) == (None, None, False)


def test_prior_without_framework_sections_keeps_domains_uncompared(db, http, gate, monkeypatch, stub_render):
    engagement = new_engagement(db)
    p1, base = _released_base(db, http, gate, monkeypatch, engagement)
    legacy = json.loads(json.dumps(base))
    legacy.pop("framework_sections")
    _craft_issued(db, p1, legacy)
    p2 = _current(db, http, gate, monkeypatch, engagement)
    document = build(db, p2)

    for entry in document["prior_period"]["frameworks"]:
        assert entry["compared"] is True
        current = _sections(document)[entry["framework_id"]]["domains"]
        assert [d["domain_id"] for d in entry["domains"]] == [d["domain_id"] for d in current]
        assert all(d["prior_score"] is None and d["score_delta"] is None for d in entry["domains"])
        assert not any(d["compared"] for d in entry["domains"])

    # A section with no `domains` key behaves the same.
    no_domains = json.loads(json.dumps(base))
    for section in no_domains["framework_sections"]:
        section.pop("domains")
    _craft_issued(db, p1, no_domains)
    entries = build(db, p2)["prior_period"]["frameworks"]
    assert all(d["prior_score"] is None for entry in entries for d in entry["domains"])


def test_new_framework_and_edition_change_have_no_domains(db, http, gate, monkeypatch, stub_render):
    engagement = new_engagement(db)
    p1, base = _released_base(db, http, gate, monkeypatch, engagement)
    p2 = _current(db, http, gate, monkeypatch, engagement)

    edition = json.loads(json.dumps(base))
    for framework in edition["frameworks"]:
        if framework["framework_id"] == "iso27001":
            framework["version"] = "2013"
    _craft_issued(db, p1, edition)
    frameworks = {f["framework_id"]: f for f in build(db, p2)["prior_period"]["frameworks"]}
    assert frameworks["iso27001"]["compared"] is False
    assert frameworks["iso27001"]["domains"] == []
    assert frameworks["dpdpa"]["domains"]

    dpdpa_only = json.loads(json.dumps(base))
    dpdpa_only["frameworks"] = [f for f in dpdpa_only["frameworks"] if f["framework_id"] == "dpdpa"]
    _craft_issued(db, p1, dpdpa_only)
    frameworks = {f["framework_id"]: f for f in build(db, p2)["prior_period"]["frameworks"]}
    assert (frameworks["iso27001"]["compared"], frameworks["iso27001"]["domains"]) == (False, [])


def test_no_prior_shape_is_unchanged(db, http, gate, monkeypatch, stub_render):
    lonely = _current(db, http, gate, monkeypatch, new_engagement(db, company="Lonely Ltd"))
    comparison = build(db, lonely)["prior_period"]
    assert comparison["status"] == "no_prior"
    assert set(comparison) == {"status", "intro", "notes", "prior", "frameworks", "changes", "totals"}
    assert comparison["frameworks"] == []
