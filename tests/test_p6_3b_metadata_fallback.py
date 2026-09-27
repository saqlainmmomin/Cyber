"""TDD ("red") contract suite for the P6-3b metadata LLM fallback.

Written by the designer before the implementation; see
``tasks/handoffs/2026-09-27-p6-3b-v2-flag-and-adapter.md`` (D-P6-3b-H) and
scenario 12. It must turn green WITHOUT edits. Before implementation every test
fails with ``ModuleNotFoundError: No module named
'app.services.grounding.metadata_fallback'`` or an ``AttributeError`` from
``monkeypatch.setattr`` on the new settings.

The provider is faked at ``llm_client._client`` (shared with
``tests/test_p6_3b_v2_flag.py``), so the real P6-3a pipeline builds the claim
set that the fallback then fills.
"""

from __future__ import annotations

import importlib
import json
import threading

import pytest

from app.config import settings
from tests.test_p6_3b_v2_flag import (
    BEGIN,
    END,
    FakeProvider,
    Q_CONSENT,
    excerpt_of,
    make_source,
    policy_text,
)

OWNER = "Head of Information Security"
ISSUED = "12 March 2025"
PROSE = (
    f"This policy is owned by the {OWNER} and was issued on {ISSUED} after a review by the risk committee."
)


def fb():
    return importlib.import_module("app.services.grounding.metadata_fallback")


@pytest.fixture(scope="module", autouse=True)
def _register_frameworks():
    from app.main import _register_frameworks as register

    register()


def claim_set_for(monkeypatch, sources, provider):
    from app.services.grounding import run_stages_0_1

    provider.install(monkeypatch)
    return run_stages_0_1(sources, ["dpdpa"])


def fields_of(claim_set, index=0) -> dict:
    return {field["name"]: field for field in claim_set.sources[index]["metadata"]["fields"]}


def spy_seam(monkeypatch):
    module = fb()
    original = module._call_llm
    calls = []
    lock = threading.Lock()

    def spy(**kwargs):
        with lock:
            calls.append(dict(kwargs))
        return original(**kwargs)

    monkeypatch.setattr(module, "_call_llm", spy)
    return calls


def test_scenario_12_verified_fields_are_added_and_unverified_dropped(monkeypatch):
    from app.services.grounding.metadata import METADATA_FIELD_NAMES

    module = fb()
    text = "Version: 2.1\n" + PROSE + "\n" + Q_CONSENT + "\n"
    answer = {"fields": [
        {"name": "owner", "value": OWNER},                      # located: kept
        {"name": "document_date", "value": ISSUED},              # located: kept, dated
        {"name": "approver", "value": "Board of Directors"},     # not in text
        {"name": "author", "value": OWNER},                      # not a requested field
        {"name": "owner", "value": "risk committee"},            # duplicate name: first wins
        {"name": "effective_date", "value": "x" * 81},           # over 80 characters
    ]}
    provider = FakeProvider(metadata=lambda user: answer)
    source = make_source(text, filename="policy.pdf")
    claim_set = claim_set_for(monkeypatch, [source], provider)
    assert "owner" not in fields_of(claim_set) and "version" in fields_of(claim_set)
    calls = spy_seam(monkeypatch)

    filled = module.fill_metadata_gaps(claim_set, [source])

    assert len(calls) == 1
    request = calls[0]
    assert request["tier"] == "extract" and request["stream"] is False and request["temperature"] == 0
    assert request["max_tokens"] == min(settings.llm_max_output_tokens_framework, module.METADATA_FALLBACK_MAX_TOKENS)
    assert request["system"] == module.METADATA_FALLBACK_SYSTEM_PROMPT
    assert request["response_schema"] == module.METADATA_FALLBACK_SCHEMA
    user = request["messages"][0]["content"]
    missing = [name for name in METADATA_FIELD_NAMES if name != "version"]
    assert user.splitlines()[0] == "Find these fields: " + ", ".join(missing)
    assert user.count(BEGIN) == 1 and user.count(END) == 1
    assert excerpt_of(user) == text[claim_set.chunks[0].start:claim_set.chunks[0].end]

    fields = fields_of(filled)
    assert list(fields) == [name for name in METADATA_FIELD_NAMES if name in fields]
    assert set(fields) == {"version", "owner", "document_date"}
    assert fields["version"]["method"] == "regex"
    for name, value in (("owner", OWNER), ("document_date", ISSUED)):
        field = fields[name]
        assert field["method"] == "llm_verified" and field["label"] is None
        assert field["value"] == value == text[field["start"]:field["end"]]
    assert fields["document_date"]["iso_date"] == "2025-03-12"
    assert fields["owner"]["iso_date"] is None
    assert filled.sources[0]["metadata"]["method"] == "regex+llm_verified"
    assert filled.metrics["metadata_fallback"] == {
        "calls": 1, "failed": 0, "fields_proposed": 6, "fields_verified": 2, "fields_rejected": 4,
    }
    # Nothing else about the claim set changes, and the call is recorded after Stage 1's.
    assert filled.claims == claim_set.claims and filled.status == claim_set.status
    assert filled.llm_calls[: len(claim_set.llm_calls)] == claim_set.llm_calls
    extra = filled.llm_calls[len(claim_set.llm_calls):]
    assert [(r["stage"], r["framework_id"], r["batch"], r["tier"]) for r in extra] == [
        ("metadata_fallback", None, "m1/1", "extract")
    ]
    assert json.loads(filled.to_json())["metrics"]["metadata_fallback"]["fields_verified"] == 2


def test_scenario_12_only_the_first_chunk_is_read(monkeypatch):
    module = fb()
    monkeypatch.setattr(settings, "v2_chunk_min_words", 10)
    monkeypatch.setattr(settings, "v2_chunk_max_words", 40)
    first = policy_text(Q_CONSENT)
    later = "\n".join(["Routine operations continue as described in the earlier sections."] * 12)
    text = first + "SECOND PART\n" + later + "\n" + PROSE + "\n"
    source = make_source(text)
    seen = []

    def answer(user):
        seen.append(excerpt_of(user))
        return {"fields": [{"name": "owner", "value": OWNER}]}

    claim_set = claim_set_for(monkeypatch, [source], FakeProvider(metadata=answer))
    assert len([c for c in claim_set.chunks if c.source_id == source.source_id]) >= 2
    filled = module.fill_metadata_gaps(claim_set, [source])
    first_chunk = claim_set.chunks[0]
    assert seen == [text[first_chunk.start:first_chunk.end]]
    assert OWNER not in seen[0]
    assert "owner" not in fields_of(filled)
    assert filled.metrics["metadata_fallback"]["fields_rejected"] == 1


def test_scenario_12_skips_images_empty_sources_and_never_raises(monkeypatch):
    module = fb()
    image = make_source("[Screenshot: idp.png]\n\n" + PROSE + "\n", n=1, filename="idp.png", mime="image/png")
    empty = make_source("", n=2, filename="empty.pdf")
    failing = make_source(PROSE + "\n", n=3, filename="failing.pdf")
    garbled = make_source(policy_text(Q_CONSENT), n=4, filename="garbled.pdf")

    def answer(user):
        if "failing.pdf" in user:
            return RuntimeError("provider exploded")
        return "not json"

    claim_set = claim_set_for(monkeypatch, [image, empty, failing, garbled], FakeProvider(metadata=answer))
    filled = module.fill_metadata_gaps(claim_set, [image, empty, failing, garbled])
    assert filled.sources == claim_set.sources
    assert filled.metrics["metadata_fallback"] == {
        "calls": 2, "failed": 2, "fields_proposed": 0, "fields_verified": 0, "fields_rejected": 0,
    }
    extra = filled.llm_calls[len(claim_set.llm_calls):]
    assert sorted(r["batch"] for r in extra) == ["m1/2", "m2/2"]


def test_scenario_12_structured_output_switch_and_setting(monkeypatch):
    module = fb()
    monkeypatch.setattr(settings, "v2_structured_output", False)
    source = make_source(PROSE + "\n")
    claim_set = claim_set_for(monkeypatch, [source], FakeProvider())
    calls = spy_seam(monkeypatch)
    module.fill_metadata_gaps(claim_set, [source])
    assert len(calls) == 1 and "response_schema" not in calls[0]
    schema = module.METADATA_FALLBACK_SCHEMA
    assert schema["name"] == "metadata_fallback_v1"
    item = schema["schema"]["properties"]["fields"]["items"]
    assert item["additionalProperties"] is False and item["required"] == ["name", "value"]


def test_scenario_12_desk_review_respects_the_setting(monkeypatch, tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.database import Base
    from app.models.desk_review import DeskReviewSummary
    from tests.test_p6_3b_v2_flag import add_evidence, raw_of, run_desk_review, seed_assessment

    engine = create_engine(f"sqlite:///{tmp_path / 'fb.sqlite3'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    try:
        monkeypatch.setattr(settings, "analysis_pipeline_version", "v2")
        answer = {"fields": [{"name": "owner", "value": OWNER}]}
        for enabled in (True, False):
            monkeypatch.setattr(settings, "v2_metadata_fallback", enabled)
            provider = FakeProvider(metadata=lambda user: answer).install(monkeypatch)
            assessment = seed_assessment(db)
            add_evidence(db, assessment, filename="policy.pdf", text=PROSE + "\n" + Q_CONSENT + "\n")
            run_desk_review(db, assessment)
            raw = raw_of(db, assessment)
            owner = [f for f in raw["claim_set"]["sources"][0]["metadata"]["fields"] if f["name"] == "owner"]
            catalog = json.loads(
                db.query(DeskReviewSummary).filter_by(assessment_id=assessment.id).one().document_catalog
            )
            if enabled:
                assert provider.kinds().count("metadata") == 1
                assert owner and owner[0]["method"] == "llm_verified"
                assert catalog[0]["metadata"]["method"] == "regex+llm_verified"
            else:
                assert provider.kinds().count("metadata") == 0
                assert owner == [] and "metadata_fallback" not in raw["claim_set"]["metrics"]
    finally:
        db.close()
        engine.dispose()
