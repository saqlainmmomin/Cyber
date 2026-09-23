"""TDD ("red") contract suite for P2-2, the citation model.

Written before the implementation. It pins the interface that
``tasks/handoffs/2026-09-23-p2-2-citation-model.md`` specifies, and must turn
green WITHOUT edits to its assertions. Scenario numbers in the docstrings match
the handoff's "Test scenarios" section.

Module under contract (does not exist yet): ``app.services.citations`` --
``LOCATION_TYPES``, ``CITATION_KEYS``, ``WHOLE_ITEM_REF``,
``MAX_EXCERPT_CHARS``, ``CitationError``, ``CitableSource``,
``normalize_with_offsets``, ``locate_excerpt``, ``text_span_citation``,
``whole_item_citation``, ``citable_sources``, ``cite_quotes``,
``validate_citations``, ``dumps_citations``, ``loads_citations``,
``attach_citations`` and ``resolve_citations``.

Every service-dependent test resolves the module through ``cit()`` as its first
statement, so before implementation each fails with
``ModuleNotFoundError: No module named 'app.services.citations'`` -- a failure
for the right reason, not a typo in this file. The schema tests fail on the
missing revision ``3d8b6f0a2c51``.

Test-DB strategy: identical to ``tests/test_evidence_service.py`` -- a
file-backed SQLite database built by ``alembic upgrade head`` with
``PRAGMA foreign_keys=ON`` on every connection, ``settings.upload_dir``
redirected to ``tmp_path``, and ``app.services.evidence.extract_text`` replaced
by a deterministic fake keyed on the uploaded bytes (no pdfplumber, no LLM).
"""

from __future__ import annotations

import importlib
import json
import logging
import subprocess
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 - register all ORM tables
from app.config import settings
from app.models.assessment import Assessment, AssessmentDocument
from app.models.client import Client
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.desk_review import DeskReviewFinding
from app.models.engagement import Engagement

REPO_ROOT = Path(__file__).resolve().parents[1]
P2_2_REVISION = "3d8b6f0a2c51"
P2_1_REVISION = "7a3f1e2b9c80"
SERVICE_MODULE = "app.services.citations"

POLICY_TEXT = (
    "Section 4 - Retention.\n\n"
    "Personal data is RETAINED for seven years.  The  company   obtains\tconsent "
    "before processing. Access requires authoriza-\n  tion by the DPO."
)
BREACH_TEXT = "Breach notification: the Board is notified within 72 hours of detection."


def cit():
    """The module under contract. Imported lazily so a missing module fails
    each test individually (FAILED) instead of erroring collection."""

    return importlib.import_module(SERVICE_MODULE)


def ev():
    return importlib.import_module("app.services.evidence")


# --------------------------------------------------------------------------- #
# Fixtures (same shape as tests/test_evidence_service.py)
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module", autouse=True)
def _register_frameworks():
    from app.main import _register_frameworks as register

    register()


@pytest.fixture(autouse=True)
def upload_root(tmp_path, monkeypatch) -> Path:
    root = tmp_path / "uploads"
    root.mkdir()
    monkeypatch.setattr(settings, "upload_dir", str(root))
    return root


def _alembic_config(db_path: Path) -> Config:
    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return config


@pytest.fixture()
def db_path(tmp_path) -> Path:
    path = tmp_path / "citations.sqlite3"
    command.upgrade(_alembic_config(path), "head")
    return path


@pytest.fixture()
def engine(db_path):
    eng = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

    @event.listens_for(eng, "connect")
    def _enable_foreign_keys(dbapi_connection, _record):  # pragma: no cover
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    yield eng
    eng.dispose()


@pytest.fixture()
def db(engine):
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def http(db, db_path, monkeypatch):
    from app.database import get_db
    from app.main import app
    from app.routers.web import templates
    from app.template_config import configure_templates

    configure_templates(templates)
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{db_path}")

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def texts(monkeypatch) -> dict[bytes, str]:
    """Deterministic extractor: the extracted text of an upload is whatever
    this dict maps its bytes to (default: a fixed filler sentence)."""

    mapping: dict[bytes, str] = {}

    def _fake_extract(path, file_type):
        return mapping.get(Path(path).read_bytes(), "Filler text with nothing to cite.")

    monkeypatch.setattr(ev(), "extract_text", _fake_extract)
    return mapping


# --------------------------------------------------------------------------- #
# Seed helpers
# --------------------------------------------------------------------------- #


def _seed_hierarchy(db, *, assessments=1, client_name="Acme Corp"):
    client = Client(name=client_name, industry="Technology", size="medium")
    db.add(client)
    db.flush()
    engagement = Engagement(client_id=client.id, name=f"{client_name} gap", status="active")
    db.add(engagement)
    db.flush()
    created = []
    for _ in range(assessments):
        assessment = Assessment(
            company_name=client_name,
            industry="Technology",
            company_size="medium",
            selected_frameworks=json.dumps(["dpdpa"]),
            engagement_id=engagement.id,
        )
        db.add(assessment)
        created.append(assessment)
    db.commit()
    return client, engagement, created


def _pdf(tag: str) -> bytes:
    return b"%PDF-1.4\n% CyberAssess citation test " + tag.encode() + b"\n%%EOF\n"


def _upload(db, texts, assessment, *, tag, text_value, filename):
    content = _pdf(tag)
    texts[content] = text_value
    return ev().ingest_upload(
        db,
        assessment_id=assessment.id,
        filename=filename,
        content=content,
        category="privacy_policy",
    )


def _new_version(db, texts, evidence_id, *, tag, text_value, filename="policy-v2.pdf"):
    content = _pdf(tag)
    texts[content] = text_value
    return ev().ingest_new_version(
        db,
        evidence_id=evidence_id,
        filename=filename,
        content=content,
        change_reason="Annual refresh",
    )


def _conclusion(db, assessment, *, requirement_id="CH2.CONSENT.1"):
    conclusion = Conclusion(
        assessment_id=assessment.id,
        requirement_id=requirement_id,
        framework_id="dpdpa",
        outcome="partially_compliant",
        rationale="Consent is obtained but not recorded.",
        evidence_summary="Privacy policy section 4.",
        gaps_identified="No consent log.",
        risk_level="medium",
        recommended_action="Implement a consent log.",
        ai_proposed=True,
    )
    db.add(conclusion)
    db.flush()
    revision = ConclusionRevision(conclusion_id=conclusion.id, actor="system:analysis", action="proposed")
    db.add(revision)
    db.flush()
    return conclusion, revision


class _StatementCounter:
    def __init__(self, engine):
        self.engine = engine
        self.count = 0

    def _count(self, conn, cursor, statement, parameters, context, executemany):
        self.count += 1

    def __enter__(self):
        event.listen(self.engine, "before_cursor_execute", self._count)
        return self

    def __exit__(self, *exc):
        event.remove(self.engine, "before_cursor_execute", self._count)


# --------------------------------------------------------------------------- #
# 1-3. Pure location functions
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("excerpt", "expected_span", "expected_slice"),
    [
        ("retained for seven years", (41, 65), "RETAINED for seven years"),
        ("obtains consent before processing", (83, 116), "obtains\tconsent before processing"),
        ("requires authorization by", (125, 154), "requires authoriza-\n  tion by"),
        ("Section 4 - Retention.", (0, 22), "Section 4 - Retention."),
    ],
    ids=["case", "whitespace-and-tab", "hyphenation", "document-start"],
)
def test_locate_excerpt_returns_raw_offsets(excerpt, expected_span, expected_slice):
    """Scenario 1: case, whitespace runs, tabs and line-break hyphenation are
    normalized for matching, but offsets index the RAW extracted text."""
    c = cit()
    span = c.locate_excerpt(POLICY_TEXT, excerpt)
    assert span == expected_span
    assert POLICY_TEXT[span[0]:span[1]] == expected_slice


def test_locate_excerpt_handles_smart_quotes_and_misses():
    """Scenario 1."""
    c = cit()
    raw = "We will obtain the user’s “explicit” consent."
    assert c.locate_excerpt(raw, "user's \"explicit\" consent") == (19, 44)
    assert c.locate_excerpt(POLICY_TEXT, "encryption at rest") is None
    assert c.locate_excerpt(POLICY_TEXT, "") is None
    assert c.locate_excerpt(POLICY_TEXT, "   \n\t ") is None
    assert c.locate_excerpt("", "anything") is None


def test_normalize_with_offsets_contract():
    """Scenario 1: one offset per normalized character, each pointing at the
    raw character it came from; collapsed whitespace maps to the first
    whitespace character of the run."""
    c = cit()
    normalized, offsets = c.normalize_with_offsets("  Ab  C’d-\n e ")
    assert normalized == "ab c'de"
    assert offsets == [2, 3, 4, 6, 7, 8, 12]
    assert c.normalize_with_offsets("") == ("", [])


@pytest.mark.parametrize(
    ("source_text", "quote"),
    [
        (POLICY_TEXT, "retained for seven years"),
        (POLICY_TEXT, "obtains consent before processing"),
        (POLICY_TEXT, "requires authorization by"),
        (POLICY_TEXT, "encryption at rest"),
        ("We will obtain the user’s “explicit” consent.", "user's \"explicit\" consent"),
        (BREACH_TEXT, "notified within 72 hours"),
        (BREACH_TEXT, "notified within 24 hours"),
    ],
    ids=["case", "whitespace", "hyphenation", "miss", "smart-quotes", "hit", "near-miss"],
)
def test_locate_excerpt_agrees_with_analysis_grounding(source_text, quote):
    """Scenario 2: citation location and the analyzer's existing quote
    grounding (``_ground_evidence_quotes``) accept exactly the same quotes, so
    no quote the pipeline treats as grounded is uncitable, and vice versa."""
    c = cit()
    from app.services.claude_analyzer import _ground_evidence_quotes

    grounded = bool(_ground_evidence_quotes({"R": [quote]}, [{"text": source_text}]))
    assert (c.locate_excerpt(source_text, quote) is not None) is grounded


def test_citation_constructors():
    """Scenario 3."""
    c = cit()
    assert c.LOCATION_TYPES == ("text_span", "whole_item")
    assert c.CITATION_KEYS == ("evidence_version_id", "location_type", "location_ref", "excerpt")
    assert c.WHOLE_ITEM_REF == "whole"
    assert c.MAX_EXCERPT_CHARS == 2000

    source = c.CitableSource(evidence_id="e1", version_id="v1", filename="policy.pdf", text=POLICY_TEXT)
    assert c.text_span_citation(source, "retained for seven years") == {
        "evidence_version_id": "v1",
        "location_type": "text_span",
        "location_ref": "chars:41-65",
        "excerpt": "RETAINED for seven years",
    }
    assert c.text_span_citation(source, "encryption at rest") is None
    assert c.whole_item_citation(source) == {
        "evidence_version_id": "v1",
        "location_type": "whole_item",
        "location_ref": "whole",
        "excerpt": "",
    }
    long_source = c.CitableSource(evidence_id="e2", version_id="v2", filename="long.pdf", text="x" * 2001)
    assert c.text_span_citation(long_source, "x" * 2001) is None
    assert c.text_span_citation(long_source, "x" * 2000)["location_ref"] == "chars:0-2000"


# --------------------------------------------------------------------------- #
# 4-5. Sources and quote citation
# --------------------------------------------------------------------------- #


def test_citable_sources_follow_the_evidence_membership_rule(db, texts):
    """Scenario 4: in-scope, active Evidence only, each with its ACTIVE version;
    mapped-in Evidence included; superseded versions, archived Evidence and
    un-migrated AssessmentDocument rows excluded; ordered like
    analysis_documents' evidence part."""
    c = cit()
    e = ev()
    _client, _engagement, (a, b) = _seed_hierarchy(db, assessments=2)
    first = _upload(db, texts, a, tag="one", text_value=POLICY_TEXT, filename="policy.pdf")
    v2 = _new_version(db, texts, first.evidence.id, tag="one-v2", text_value="Policy v2 text.")
    archived = _upload(db, texts, a, tag="arch", text_value="Archived text.", filename="old.pdf")
    e.transition_evidence(db, evidence_id=archived.evidence.id, to_status="archived", actor="consultant")
    db.commit()
    mapped = _upload(db, texts, b, tag="mapped", text_value=BREACH_TEXT, filename="breach.pdf")
    e.map_evidence(
        db,
        evidence_id=mapped.evidence.id,
        assessment_id=a.id,
        framework_id="dpdpa",
        requirement_id="CH2.CONSENT.1",
        relevance="supporting",
        actor="consultant",
    )
    db.commit()
    db.add(
        AssessmentDocument(
            assessment_id=a.id,
            filename="legacy.pdf",
            file_path="/nonexistent/legacy.pdf",
            file_type="pdf",
            document_category="other",
            extracted_text="Legacy text.",
        )
    )
    db.commit()

    sources = c.citable_sources(db, a.id)
    assert sources == [
        c.CitableSource(
            evidence_id=first.evidence.id,
            version_id=v2.version.id,
            filename="policy-v2.pdf",
            text="Policy v2 text.",
        ),
        c.CitableSource(
            evidence_id=mapped.evidence.id,
            version_id=mapped.version.id,
            filename="breach.pdf",
            text=BREACH_TEXT,
        ),
    ]
    assert [s.evidence_id for s in c.citable_sources(db, b.id)] == [mapped.evidence.id]


def test_cite_quotes_prefers_named_document_and_drops_ungrounded(caplog):
    """Scenario 5."""
    c = cit()
    policy = c.CitableSource(evidence_id="e1", version_id="v1", filename="policy.pdf", text=POLICY_TEXT)
    breach = c.CitableSource(evidence_id="e2", version_id="v2", filename="breach.pdf", text=BREACH_TEXT)
    dup = c.CitableSource(evidence_id="e3", version_id="v3", filename="copy.pdf", text=BREACH_TEXT)
    secret_quote = "a fabricated sentence nobody wrote"

    with caplog.at_level(logging.WARNING, logger=SERVICE_MODULE):
        result = c.cite_quotes(
            [policy, breach, dup],
            [
                "notified within 72 hours",
                "",
                "retained for seven years",
                secret_quote,
                "notified within 72 hours",
            ],
            preferred_filename="copy.pdf",
        )

    assert result == [
        {
            "evidence_version_id": "v3",
            "location_type": "text_span",
            "location_ref": "chars:34-58",
            "excerpt": "notified within 72 hours",
        },
        {
            "evidence_version_id": "v1",
            "location_type": "text_span",
            "location_ref": "chars:41-65",
            "excerpt": "RETAINED for seven years",
        },
    ]
    warnings = [r for r in caplog.records if r.name == SERVICE_MODULE]
    assert [r.getMessage() for r in warnings] == ["Citation grounding dropped 1 ungrounded quote(s)"]
    assert secret_quote not in caplog.text

    # No preferred filename: first source in order wins.
    (only,) = c.cite_quotes([policy, breach, dup], ["notified within 72 hours"])
    assert only["evidence_version_id"] == "v2"
    assert c.cite_quotes([], ["anything"]) == []


# --------------------------------------------------------------------------- #
# 6-7. Validation and serialization
# --------------------------------------------------------------------------- #


def _valid_span(version_id):
    return {
        "evidence_version_id": version_id,
        "location_type": "text_span",
        "location_ref": "chars:41-65",
        "excerpt": "RETAINED for seven years",
    }


def test_validate_citations_happy_path_and_query_budget(db, engine, texts):
    """Scenario 6."""
    c = cit()
    _client, _engagement, (a,) = _seed_hierarchy(db)
    up = _upload(db, texts, a, tag="p", text_value=POLICY_TEXT, filename="policy.pdf")
    vid = up.version.id
    citations = [
        _valid_span(vid),
        {"evidence_version_id": vid, "location_type": "text_span", "location_ref": "chars:83-116",
         "excerpt": "obtains\tconsent before processing"},
        {"evidence_version_id": vid, "location_type": "text_span", "location_ref": "chars:0-22",
         "excerpt": "Section 4 - Retention."},
        {"evidence_version_id": vid, "location_type": "text_span", "location_ref": "chars:125-154",
         "excerpt": "requires authoriza-\n  tion by"},
        {"location_type": "whole_item", "excerpt": "", "location_ref": "whole", "evidence_version_id": vid},
    ]
    assessment_id = a.id
    db.expire_all()
    with _StatementCounter(engine) as counter:
        normalized = c.validate_citations(db, citations, assessment_id=assessment_id)
    assert counter.count <= 3, f"validate_citations issued {counter.count} statements"
    assert normalized == [{k: cc[k] for k in c.CITATION_KEYS} for cc in citations]
    assert all(list(cc) == list(c.CITATION_KEYS) for cc in normalized)
    assert c.validate_citations(db, [], assessment_id=assessment_id) == []


def test_validate_citations_rejections(db, texts):
    """Scenario 6: exact messages, first failing rule wins, index-prefixed."""
    c = cit()
    e = ev()
    _client, _engagement, (a, b) = _seed_hierarchy(db, assessments=2)
    up = _upload(db, texts, a, tag="p", text_value=POLICY_TEXT, filename="policy.pdf")
    other = _upload(db, texts, b, tag="other", text_value=BREACH_TEXT, filename="breach.pdf")
    vid = up.version.id
    v2 = _new_version(db, texts, up.evidence.id, tag="p2", text_value=POLICY_TEXT + " Revised.")

    def reject(citations, message):
        with pytest.raises(c.CitationError) as info:
            c.validate_citations(db, citations, assessment_id=a.id)
        assert info.value.message == message
        assert info.value.status_code == 422

    good = _valid_span(v2.version.id)
    reject({"evidence_version_id": vid}, "Citations must be a list.")
    reject([good, {"evidence_version_id": vid}],
           "Citation 1: must have exactly the keys evidence_version_id, location_type, location_ref, excerpt.")
    reject([{**good, "extra": "x"}],
           "Citation 0: must have exactly the keys evidence_version_id, location_type, location_ref, excerpt.")
    reject(["not a dict"],
           "Citation 0: must have exactly the keys evidence_version_id, location_type, location_ref, excerpt.")
    reject([{**good, "excerpt": None}], "Citation 0: all fields must be strings.")
    reject([{**good, "location_type": "page"}], "Citation 0: unknown location_type 'page'.")
    reject([{**good, "evidence_version_id": "missing"}], "Citation 0: evidence version 'missing' not found.")
    reject([_valid_span(vid)], f"Citation 0: evidence version '{vid}' is not active and cannot be cited.")
    reject([{**_valid_span(other.version.id), "location_ref": "chars:0-6", "excerpt": "Breach"}],
           f"Citation 0: evidence version '{other.version.id}' is not in scope for this assessment.")
    reject([{**good, "location_type": "whole_item"}],
           "Citation 0: whole_item citations must have location_ref 'whole' and an empty excerpt.")
    for bad_ref in ("chars:71-47", "chars:10-10", "chars:0-99999", "chars:-1-5", "p.4", "chars:01-5"):
        reject([{**good, "location_ref": bad_ref}], f"Citation 0: invalid text_span location_ref '{bad_ref}'.")
    reject([{**good, "excerpt": "retained for seven years"}],
           "Citation 0: excerpt does not match the cited evidence text.")
    long_text = "y" * 2500
    long_up = _upload(db, texts, a, tag="long", text_value=long_text, filename="long.pdf")
    reject([{"evidence_version_id": long_up.version.id, "location_type": "text_span",
             "location_ref": "chars:0-2001", "excerpt": "y" * 2001}],
           "Citation 0: excerpt exceeds 2000 characters.")
    reject([good, dict(good)], "Citation 1: duplicate citation.")

    # Evidence-level status matters too: an invalidated Evidence cannot be cited.
    e.transition_evidence(db, evidence_id=up.evidence.id, to_status="invalidated", actor="consultant",
                          reason="Wrong entity")
    db.commit()
    reject([good], f"Citation 0: evidence version '{v2.version.id}' is not active and cannot be cited.")


def test_dumps_and_loads_citations():
    """Scenario 7: canonical JSON; NULL means 'not captured', '[]' means
    'captured, none'."""
    c = cit()
    citations = [_valid_span("v1")]
    raw = c.dumps_citations(citations)
    assert raw == json.dumps(citations, sort_keys=True)
    assert c.dumps_citations([]) == "[]"
    assert c.loads_citations(raw) == citations
    assert c.loads_citations(None) == []
    assert c.loads_citations("[]") == []
    with pytest.raises(c.CitationError) as info:
        c.loads_citations('{"not": "a list"}')
    assert info.value.message == "Stored citations are not a JSON array."


# --------------------------------------------------------------------------- #
# 8-9. Conclusion revisions and resolution
# --------------------------------------------------------------------------- #


def test_attach_citations_to_conclusion_revision(db, texts):
    """Scenario 8: the plan's contract -- a conclusion revision carries citation
    JSON and every citation resolves to a valid EvidenceVersion."""
    c = cit()
    _client, _engagement, (a,) = _seed_hierarchy(db)
    up = _upload(db, texts, a, tag="p", text_value=POLICY_TEXT, filename="policy.pdf")
    sources = c.citable_sources(db, a.id)
    citations = c.cite_quotes(sources, ["retained for seven years", "obtains consent before processing"])
    _conclusion_row, revision = _conclusion(db, a)

    returned = c.attach_citations(db, revision=revision, citations=citations)
    db.commit()
    assert returned is revision
    db.expire_all()
    stored = db.get(ConclusionRevision, revision.id)
    assert json.loads(stored.citations_json) == citations
    resolved = c.resolve_citations(db, stored.citations_json)
    assert [r["resolved"] for r in resolved] == [True, True]
    assert {r["evidence_id"] for r in resolved} == {up.evidence.id}
    assert {r["evidence_version_id"] for r in resolved} == {up.version.id}

    with pytest.raises(c.CitationError) as info:
        c.attach_citations(db, revision=stored, citations=[])
    assert info.value.message == "Citations on a conclusion revision are immutable once set."


def test_attach_citations_validates_before_writing(db, texts):
    """Scenario 8."""
    c = cit()
    _client, _engagement, (a,) = _seed_hierarchy(db)
    _upload(db, texts, a, tag="p", text_value=POLICY_TEXT, filename="policy.pdf")
    _conclusion_row, revision = _conclusion(db, a)
    with pytest.raises(c.CitationError):
        c.attach_citations(db, revision=revision, citations=[_valid_span("missing")])
    assert revision.citations_json is None

    c.attach_citations(db, revision=revision, citations=[])
    db.commit()
    db.expire_all()
    assert db.get(ConclusionRevision, revision.id).citations_json == "[]"


def test_resolve_citations_reports_currency_and_missing_versions(db, engine, texts):
    """Scenario 9."""
    c = cit()
    _client, _engagement, (a,) = _seed_hierarchy(db)
    up = _upload(db, texts, a, tag="p", text_value=POLICY_TEXT, filename="policy.pdf")
    raw = c.dumps_citations(c.cite_quotes(c.citable_sources(db, a.id), ["retained for seven years"]))
    _new_version(db, texts, up.evidence.id, tag="p2", text_value="Rewritten policy.")
    stale_raw = json.dumps(json.loads(raw) + [
        {"evidence_version_id": "gone", "location_type": "whole_item", "location_ref": "whole", "excerpt": ""}
    ])

    db.expire_all()
    with _StatementCounter(engine) as counter:
        resolved = c.resolve_citations(db, stale_raw)
    assert counter.count <= 2, f"resolve_citations issued {counter.count} statements"
    first, missing = resolved
    assert first == {
        "evidence_version_id": up.version.id,
        "location_type": "text_span",
        "location_ref": "chars:41-65",
        "excerpt": "RETAINED for seven years",
        "resolved": True,
        "evidence_id": up.evidence.id,
        "filename": "policy.pdf",
        "version_number": 1,
        "version_status": "superseded",
        "evidence_status": "active",
        "is_current": False,
    }
    assert missing == {
        "evidence_version_id": "gone",
        "location_type": "whole_item",
        "location_ref": "whole",
        "excerpt": "",
        "resolved": False,
        "evidence_id": None,
        "filename": None,
        "version_number": None,
        "version_status": None,
        "evidence_status": None,
        "is_current": False,
    }
    assert c.resolve_citations(db, None) == []


# --------------------------------------------------------------------------- #
# 10. Desk review produces citations
# --------------------------------------------------------------------------- #


def test_desk_review_persists_citations(db, http, texts, monkeypatch):
    """Scenario 10."""
    c = cit()
    import app.services.desk_review as desk_review

    _client, _engagement, (a,) = _seed_hierarchy(db)
    policy = _upload(db, texts, a, tag="p", text_value=POLICY_TEXT, filename="policy.pdf")
    breach = _upload(db, texts, a, tag="b", text_value=BREACH_TEXT, filename="breach.pdf")
    legacy = AssessmentDocument(
        assessment_id=a.id,
        filename="legacy.pdf",
        file_path="/nonexistent/legacy.pdf",
        file_type="pdf",
        document_category="other",
        extracted_text="Legacy retention schedule: ten years.",
    )
    db.add(legacy)
    db.commit()

    def _fake(documents, company_name, industry):
        return {
            "evidence_map": {
                "CH2.CONSENT.1": [
                    # grounded in the named document
                    {"document": "policy.pdf", "quote": "obtains consent before processing", "location": "s4"},
                    # document misnamed by the model: still grounded, in breach.pdf
                    {"document": "policy.pdf", "quote": "notified within 72 hours", "location": "p1"},
                    # fabricated quote
                    {"document": "policy.pdf", "quote": "we encrypt everything", "location": "p9"},
                    # only in a legacy (un-migrated) document: not citable
                    {"document": "legacy.pdf", "quote": "ten years", "location": "p2"},
                ]
            },
            "absence_findings": [
                {"requirement_id": "CH2.NOTICE.1", "description": "No notice.", "severity": "high"}
            ],
            "signal_flags": [
                {"document": "breach.pdf", "requirement_ids": ["CH2.CONSENT.1"], "description": "Board only.",
                 "severity": "medium", "source_quote": "", "location": ""},
            ],
            "document_catalog": [],
            "coverage_summary": {},
        }

    monkeypatch.setattr(desk_review, "_call_claude_desk_review", _fake)
    summary = desk_review.run_desk_review(a.id, db)
    assert summary.status == "completed", summary.error_message

    db.expire_all()
    rows = db.query(DeskReviewFinding).order_by(DeskReviewFinding.id).all()
    by_quote = {r.source_quote: r for r in rows if r.finding_type == "evidence"}
    assert json.loads(by_quote["obtains consent before processing"].citations_json) == [{
        "evidence_version_id": policy.version.id,
        "location_type": "text_span",
        "location_ref": "chars:83-116",
        "excerpt": "obtains\tconsent before processing",
    }]
    assert json.loads(by_quote["notified within 72 hours"].citations_json) == [{
        "evidence_version_id": breach.version.id,
        "location_type": "text_span",
        "location_ref": "chars:34-58",
        "excerpt": "notified within 72 hours",
    }]
    assert by_quote["we encrypt everything"].citations_json == "[]"
    assert by_quote["ten years"].citations_json == "[]"
    assert by_quote["ten years"].document_id == legacy.id
    (absence,) = [r for r in rows if r.finding_type == "absence"]
    assert absence.citations_json == "[]"
    (signal,) = [r for r in rows if r.finding_type == "signal"]
    assert json.loads(signal.citations_json) == [{
        "evidence_version_id": breach.version.id,
        "location_type": "whole_item",
        "location_ref": "whole",
        "excerpt": "",
    }]
    for row in rows:
        c.validate_citations(db, c.loads_citations(row.citations_json), assessment_id=a.id)

    body = http.get(f"/api/assessments/{a.id}/desk-review").json()
    api_evidence = {f["source_quote"]: f for f in body["findings"]["evidence"]}
    assert api_evidence["obtains consent before processing"]["citations"][0]["evidence_version_id"] == (
        policy.version.id
    )
    assert api_evidence["we encrypt everything"]["citations"] == []
    assert "document_id" in api_evidence["ten years"]
    assert body["findings"]["signals"][0]["citations"][0]["location_type"] == "whole_item"
    assert "citations" not in body["findings"]["absences"][0]


# --------------------------------------------------------------------------- #
# 11-12. Schema and standing guards
# --------------------------------------------------------------------------- #


def test_p2_2_revision_is_head_and_reshapes_schema(db_path, engine):
    """Scenario 11."""
    script = ScriptDirectory.from_config(_alembic_config(db_path))
    assert script.get_revision("4e8c1a9d2b57").down_revision == P2_2_REVISION
    assert script.get_revision(P2_2_REVISION).down_revision == P2_1_REVISION

    inspector = inspect(engine)
    assert "citations" not in inspector.get_table_names()
    columns = {col["name"]: col for col in inspector.get_columns("desk_review_findings")}
    assert columns["citations_json"]["nullable"] is True
    assert str(columns["citations_json"]["type"]).upper() == "TEXT"

    assert "Citation" not in app.models.__all__
    assert not hasattr(app.models, "Citation")
    assert not (REPO_ROOT / "app" / "models" / "citation.py").exists()


def test_p2_2_downgrade_restores_citations_table_and_refuses_with_data(db, db_path, engine):
    """Scenario 11."""
    config = _alembic_config(db_path)
    assert ScriptDirectory.from_config(config).get_revision("4e8c1a9d2b57").down_revision == P2_2_REVISION
    _client, _engagement, (a,) = _seed_hierarchy(db)
    assessment_id = a.id
    db.close()
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO desk_review_findings (assessment_id, finding_type, content, severity, "
                "citations_json, created_at) VALUES (:aid, 'absence', 'x', 'low', '[]', '2026-09-23 00:00:00')"
            ),
            {"aid": assessment_id},
        )
    engine.dispose()
    with pytest.raises(RuntimeError, match="Refusing to downgrade past P2-2"):
        command.downgrade(config, P2_1_REVISION)

    with engine.begin() as conn:
        conn.execute(text("UPDATE desk_review_findings SET citations_json = NULL"))
    engine.dispose()
    command.downgrade(config, P2_1_REVISION)
    inspector = inspect(create_engine(f"sqlite:///{db_path}"))
    assert "citations" in inspector.get_table_names()
    assert "citations_json" not in {c["name"] for c in inspector.get_columns("desk_review_findings")}
    assert any(
        fk["referred_table"] == "evidence_versions" and fk["constrained_columns"] == ["evidence_version_id"]
        for fk in inspector.get_foreign_keys("citations")
    )
    assert "ix_citations_evidence_version_id" in {i["name"] for i in inspector.get_indexes("citations")}

    command.upgrade(config, "head")
    assert "citations" not in inspect(create_engine(f"sqlite:///{db_path}")).get_table_names()


def test_no_code_references_the_dropped_citations_model():
    """Scenario 12: the JSON column is the only citation store."""
    result = subprocess.run(
        ["grep", "-rnE", r"app\.models\.citation|from app\.models import .*\bCitation\b|\bCitation\(",
         "app", "scripts", "--include=*.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.stdout == "", result.stdout
