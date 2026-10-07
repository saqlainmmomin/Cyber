"""TDD ("red") contract suite for P6-3b: the v2 flag, desk-review branch and adapter.

Written by the designer before the implementation. It pins the interface in
``tasks/handoffs/2026-09-27-p6-3b-v2-flag-and-adapter.md`` and must turn green
WITHOUT edits. If an assertion looks wrong, report it in the handoff's Results;
do not change it. Scenario numbers match the handoff's "Test scenarios".

Modules under contract (do not exist yet): ``app.services.desk_review_v2`` and
``app.services.grounding.metadata_fallback``; new settings
``analysis_pipeline_version``, ``v2_max_concurrency`` and
``v2_metadata_fallback``; a ``max_workers`` keyword on ``run_stages_0_1``; and a
precomputed-citation path in ``desk_review._persist_findings``. Before
implementation these tests fail with ``ModuleNotFoundError``, an
``AttributeError`` from ``monkeypatch.setattr(settings, <new setting>, ...)``,
``KeyError`` on ``Settings.model_fields``, ``TypeError`` on the new keyword, or
an assertion on the missing behaviour. Two structural guards
(``test_scenario_2_desk_review_v1_lines_are_only_added_to`` and
``test_scenario_11_p6_3a_prompts_unchanged``) pass before and after.

No live LLM. The provider client is faked at ``llm_client._client`` so the real
``llm_client.call_llm`` and the real P6-3a pipeline run and write real call
records. Documents are invented for this file.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import re
import threading
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 - register all ORM tables
from app.config import Settings, settings
from app.database import Base
from app.services import llm_client

REPO_ROOT = Path(__file__).resolve().parents[1]
BEGIN = "<<<BEGIN UNTRUSTED DOCUMENT TEXT>>>"
END = "<<<END UNTRUSTED DOCUMENT TEXT>>>"
SUPPORT_ITEM = re.compile(
    r"^\[(c\d+)\]\nstatement: ([^\n]*)\n" + re.escape(BEGIN) + r"\n(.*?)\n" + re.escape(END),
    re.M | re.S,
)

# Invented sentences (Kestrel Ledger, a fictional payments start-up).
Q_DPO = "The Board has appointed a Data Protection Officer who reports to the Chief Executive Officer."
Q_ROLES = "Information security roles and responsibilities are defined and allocated by the Chief Risk Officer."
Q_CONSENT = "Personal data is processed only after the data principal gives free and specific consent."
Q_ACCESS = "Access rights to production systems are reviewed every quarter by the system owner."
Q_SCREEN = "The identity provider settings page shows multi-factor authentication enforced for administrators."

DEFAULT_TAGS = {
    Q_DPO: ("CH4.SDF.1",),
    Q_ROLES: ("ISO.A5.2",),
    Q_CONSENT: ("CH2.CONSENT.1",),
    Q_ACCESS: ("ISO.A5.18", "CH4.SDF.1"),
    Q_SCREEN: ("ISO.A5.17", "CH2.CONSENT.2"),
}


def policy_text(*sentences: str) -> str:
    return "Kestrel Ledger Privacy and Security Policy\n" + "\n".join(sentences) + "\n"


def v2():
    return importlib.import_module("app.services.desk_review_v2")


def fallback():
    return importlib.import_module("app.services.grounding.metadata_fallback")


# --------------------------------------------------------------------------- #
# Fake provider
# --------------------------------------------------------------------------- #


def _response(text: str):
    usage = SimpleNamespace(
        prompt_tokens=100,
        completion_tokens=max(1, len(text) // 4),
        prompt_tokens_details=SimpleNamespace(cached_tokens=0),
    )
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=text), finish_reason="stop")],
        usage=usage,
    )


def _system_text(system) -> str:
    return system if isinstance(system, str) else "".join(b.get("text", "") for b in system)


def excerpt_of(user: str) -> str:
    """The wrapped text of an extraction or fallback user prompt."""
    body = user.split(BEGIN + "\n", 1)[1].rsplit("\n" + END, 1)[0]
    return body.split("\n----\n", 1)[1] if "\n----\n" in body else body


class FakeProvider:
    """Answers extraction, support and metadata-fallback calls deterministically.

    Extraction: every tagged quote found in the excerpt is returned, tagged with
    its IDs that the batch shows (a quote with none is omitted). Support: yes.
    Metadata fallback (any other system prompt): ``metadata(user)`` or no fields.
    """

    def __init__(self, tags=None, *, fail_extraction=None, raise_extraction=None, metadata=None):
        self.tags = dict(DEFAULT_TAGS if tags is None else tags)
        self.fail_extraction = fail_extraction
        self.raise_extraction = raise_extraction
        self.metadata = metadata
        self.lock = threading.Lock()
        self.calls: list[tuple[str, dict]] = []

    def install(self, monkeypatch):
        monkeypatch.setattr(
            llm_client,
            "_client",
            SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=self.create))),
        )
        return self

    def kinds(self) -> list[str]:
        return [kind for kind, _ in self.calls]

    def create(self, **kwargs):
        system = _system_text(kwargs["messages"][0]["content"])
        user = kwargs["messages"][1]["content"]
        if SUPPORT_ITEM.search(user):
            kind = "support"
        elif re.search(r"^- \S+ \[", system, re.M):
            kind = "extraction"
        else:
            kind = "metadata"
        with self.lock:
            self.calls.append((kind, kwargs))
        if kind == "support":
            verdicts = [
                {"ref": ref, "verdict": "yes", "supported_statement": None}
                for ref, _statement, _quote in SUPPORT_ITEM.findall(user)
            ]
            return _response(json.dumps({"verdicts": verdicts}))
        if kind == "metadata":
            out = self.metadata(user) if self.metadata else {"fields": []}
            if isinstance(out, BaseException):
                raise out
            return _response(out if isinstance(out, str) else json.dumps(out))
        ids = tuple(re.findall(r"^- (\S+) \[", system, re.M))
        if self.raise_extraction and self.raise_extraction(ids):
            raise RuntimeError("provider exploded")
        if self.fail_extraction and self.fail_extraction(ids):
            return _response("this is not json")
        text = excerpt_of(user)
        claims = []
        for quote, quote_ids in self.tags.items():
            shown = [rid for rid in quote_ids if rid in ids]
            if quote in text and shown:
                claims.append({
                    "quote": quote,
                    "statement": f"Stated: {quote}",
                    "kind": "design",
                    "stated_period": None,
                    "stated_owner": None,
                    "requirement_ids": shown,
                })
        return _response(json.dumps({"claims": claims}))


# --------------------------------------------------------------------------- #
# Fixtures and DB helpers
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module", autouse=True)
def _register_frameworks():
    from app.main import _register_frameworks as register

    register()


@pytest.fixture()
def db(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'p6_3b.sqlite3'}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def flag_v2(monkeypatch):
    monkeypatch.setattr(settings, "analysis_pipeline_version", "v2")


def seed_assessment(db, frameworks=("dpdpa",)):
    from app.models.assessment import Assessment
    from app.models.client import Client
    from app.models.engagement import Engagement

    client = Client(name=f"Kestrel Ledger {uuid.uuid4().hex[:6]}", industry="Technology", size="medium")
    db.add(client)
    db.flush()
    engagement = Engagement(client_id=client.id, name="Kestrel gap", status="active")
    db.add(engagement)
    db.flush()
    assessment = Assessment(
        company_name="Kestrel Ledger Pvt Ltd",
        industry="Technology",
        company_size="medium",
        selected_frameworks=json.dumps(list(frameworks)),
        engagement_id=engagement.id,
    )
    db.add(assessment)
    db.commit()
    return assessment


def add_evidence(db, assessment, *, filename, text, mime="application/pdf", category="privacy_policy"):
    from app.models.evidence import Evidence, EvidenceVersion

    evidence = Evidence(
        engagement_id=assessment.engagement_id,
        assessment_id=assessment.id,
        document_category=category,
        original_filename=filename,
        storage_path=f"blobs/{uuid.uuid4().hex}",
        file_hash_sha256=hashlib.sha256(text.encode()).hexdigest(),
        file_size_bytes=len(text.encode()),
        mime_type=mime,
        status="active",
        uploaded_by="consultant",
    )
    db.add(evidence)
    db.flush()
    version = EvidenceVersion(
        evidence_id=evidence.id,
        version_number=1,
        storage_path=f"blobs/{uuid.uuid4().hex}",
        file_hash_sha256=hashlib.sha256(text.encode()).hexdigest(),
        file_size_bytes=len(text.encode()),
        status="active",
        original_filename=filename,
        mime_type=mime,
        extracted_text=text,
    )
    db.add(version)
    db.commit()
    return evidence, version


def add_legacy(db, assessment, *, filename, text):
    from app.models.assessment import AssessmentDocument

    row = AssessmentDocument(
        assessment_id=assessment.id,
        filename=filename,
        file_path=f"uploads/{filename}",
        file_type=filename.rsplit(".", 1)[-1],
        document_category="other",
        extracted_text=text,
    )
    db.add(row)
    db.commit()
    return row


def findings(db, assessment):
    from app.models.desk_review import DeskReviewFinding

    return (
        db.query(DeskReviewFinding)
        .filter(DeskReviewFinding.assessment_id == assessment.id)
        .order_by(DeskReviewFinding.id)
        .all()
    )


def summary_of(db, assessment):
    from app.models.desk_review import DeskReviewSummary

    return db.query(DeskReviewSummary).filter_by(assessment_id=assessment.id).one()


def raw_of(db, assessment) -> dict:
    return json.loads(summary_of(db, assessment).raw_ai_response)


def run_desk_review(db, assessment):
    from app.services.desk_review import run_desk_review as run

    return run(assessment.id, db)


def make_source(text, *, n=1, filename=None, mime="text/plain", category="other", legacy=False):
    from app.services.grounding.sources import SourceDocument

    return SourceDocument(
        source_id=f"legacy:l-{n}" if legacy else f"ev:v-{n}",
        evidence_id=None if legacy else f"e-{n}",
        evidence_version_id=None if legacy else f"v-{n}",
        legacy_document_id=f"l-{n}" if legacy else None,
        filename=filename or f"doc-{n}.txt",
        category=category,
        mime_type=mime,
        text=text,
    )


# --------------------------------------------------------------------------- #
# Scenario 1: settings
# --------------------------------------------------------------------------- #


def test_scenario_1_setting_defaults():
    fields = Settings.model_fields
    assert fields["analysis_pipeline_version"].default == "v1"
    assert fields["v2_max_concurrency"].default == 6
    assert fields["v2_metadata_fallback"].default is True
    assert fields["llm_max_concurrency"].default == 4  # Q6: v1 stays 4
    with pytest.raises(ValueError):
        Settings(analysis_pipeline_version="v3")
    env_example = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")
    for name in ("ANALYSIS_PIPELINE_VERSION", "V2_MAX_CONCURRENCY", "V2_METADATA_FALLBACK"):
        assert re.search(rf"^# {name}=", env_example, re.M), name


# --------------------------------------------------------------------------- #
# Scenario 2: flag-off parity
# --------------------------------------------------------------------------- #


def _v1_result():
    return {
        "document_catalog": [{"filename": "policy.pdf", "document_type": "Privacy Policy",
                              "coverage_areas": ["CH2.CONSENT.1"], "summary": "Policy."}],
        "evidence_map": {"CH2.CONSENT.1": [{"quote": Q_CONSENT, "document": "policy.pdf",
                                             "location": "Section 1"}]},
        "absence_findings": [{"requirement_id": "CH2.CONSENT.3", "description": "No withdrawal.",
                              "severity": "high"}],
        "signal_flags": [],
        "coverage_summary": {"CH2.CONSENT.1": "adequate", "CH2.CONSENT.3": "absent"},
    }


def _row_shape(rows):
    """Row content without per-assessment ids (evidence_version_id differs per seed)."""
    return [
        (r.framework_id, r.finding_type, r.requirement_id, r.content, r.severity,
         r.source_quote, r.source_location,
         [{k: v for k, v in c.items() if k != "evidence_version_id"} for c in json.loads(r.citations_json)])
        for r in rows
    ]


def test_scenario_2_flag_off_runs_v1_only_and_is_identical(db, monkeypatch):
    from app.services import desk_review

    desk_review_v2 = v2()

    def boom(*_args, **_kwargs):
        raise AssertionError("v2 must not run with the flag off")

    monkeypatch.setattr(desk_review_v2, "run_desk_review_v2", boom)
    monkeypatch.setattr(desk_review_v2, "run_stages_0_1", boom)
    monkeypatch.setattr(desk_review, "_call_claude_desk_review", lambda **_kw: _v1_result())
    workers = []
    real_run_bounded = desk_review.run_bounded
    monkeypatch.setattr(
        desk_review,
        "run_bounded",
        lambda fn, items, *, max_workers: workers.append(max_workers) or real_run_bounded(fn, items, max_workers=max_workers),
    )
    provider = FakeProvider().install(monkeypatch)

    runs = []
    for explicit in (False, True):
        if explicit:
            monkeypatch.setattr(settings, "analysis_pipeline_version", "v1")
        assessment = seed_assessment(db)
        add_evidence(db, assessment, filename="policy.pdf", text=policy_text(Q_CONSENT))
        summary = run_desk_review(db, assessment)
        assert summary.status == "completed"
        raw = raw_of(db, assessment)
        assert "claim_set" not in raw and "analysis_pipeline_version" not in raw
        runs.append((raw, _row_shape(findings(db, assessment)),
                     json.loads(summary_of(db, assessment).coverage_summary)))

    assert runs[0] == runs[1]
    assert runs[0][2] == {"CH2.CONSENT.1": "adequate", "CH2.CONSENT.3": "absent"}  # v1 is not capped
    assert provider.calls == []
    assert workers == [settings.llm_max_concurrency] * 2


# --------------------------------------------------------------------------- #
# Scenario 3: the v2 branch calls run_stages_0_1 correctly
# --------------------------------------------------------------------------- #


def test_scenario_3_v2_branch_invokes_stages_with_full_documents(db, monkeypatch, flag_v2):
    from app.services import desk_review
    from app.services.grounding import load_source_documents

    desk_review_v2 = v2()
    monkeypatch.setattr(settings, "v2_max_concurrency", 3)
    monkeypatch.setattr(settings, "llm_max_concurrency", 4)
    monkeypatch.setattr(desk_review, "_call_claude_desk_review", lambda **_kw: pytest.fail("v1 seam called"))
    monkeypatch.setattr(desk_review, "_call_framework_desk_review", lambda *_a, **_kw: pytest.fail("v1 seam called"))
    FakeProvider().install(monkeypatch)

    assessment = seed_assessment(db, ("dpdpa", "iso27001"))
    long_text = policy_text(Q_DPO) + " ".join(["Filler words describe routine operations."] * 4200) + "\n"
    assert len(long_text.split()) > settings.max_total_document_words
    add_evidence(db, assessment, filename="long.pdf", text=long_text)
    add_legacy(db, assessment, filename="legacy.docx", text=policy_text(Q_ROLES))

    seen = []
    real = desk_review_v2.run_stages_0_1

    def spy(sources, framework_ids, **kwargs):
        seen.append((list(sources), tuple(framework_ids), kwargs, dict(llm_client._tags.get())))
        return real(sources, framework_ids, **kwargs)

    monkeypatch.setattr(desk_review_v2, "run_stages_0_1", spy)
    summary = run_desk_review(db, assessment)

    assert summary.status == "completed"
    assert len(seen) == 1
    sources, framework_ids, kwargs, tags = seen[0]
    assert sources == load_source_documents(db, assessment.id)
    assert sources[0].text == long_text  # no 20k-word truncation
    assert framework_ids == ("dpdpa", "iso27001")
    assert kwargs == {"max_workers": 3}
    assert tags.get("framework_id") is None  # never inside call_tag(framework_id=...)


# --------------------------------------------------------------------------- #
# Scenario 4: persistence of the claim set
# --------------------------------------------------------------------------- #


def test_scenario_4_claim_set_persisted_outside_claims_key(db, monkeypatch, flag_v2):
    from app.models.analysis_run import AnalysisRun
    from app.services.grounding import load_source_documents
    from app.services.grounding.claims import ClaimSet, claim_set_is_current

    provider = FakeProvider().install(monkeypatch)
    assessment = seed_assessment(db, ("dpdpa", "iso27001"))
    add_evidence(db, assessment, filename="policy.pdf", text=policy_text(Q_DPO, Q_ROLES, Q_CONSENT))
    summary = run_desk_review(db, assessment)
    assert summary.status == "completed" and summary.error_message is None

    raw = raw_of(db, assessment)
    assert raw["schema_version"] == 2
    assert raw["analysis_pipeline_version"] == "v2"
    assert set(raw["frameworks"]) == {"dpdpa", "iso27001"}
    assert all(entry["status"] == "completed" for entry in raw["frameworks"].values())
    assert "claims" not in raw  # the v1 AnalysisRun envelope's key is never reused
    assert db.query(AnalysisRun).count() == 0

    stored = ClaimSet.from_json(json.dumps(raw["claim_set"]))
    loaded = v2().load_claim_set(db, assessment.id)
    assert loaded == stored
    assert loaded.status == "complete"
    assert {claim.quote for claim in loaded.claims} == {Q_DPO, Q_ROLES, Q_CONSENT}
    assert claim_set_is_current(loaded, load_source_documents(db, assessment.id), assessment.frameworks)

    assert raw["llm_calls"] == raw["claim_set"]["llm_calls"]
    stages = [record["stage"] for record in raw["llm_calls"]]
    assert stages.count("claim_extraction") == provider.kinds().count("extraction") == 8
    assert stages.count("claim_support") == provider.kinds().count("support")
    assert stages.count("metadata_fallback") == provider.kinds().count("metadata") == 1
    assert all(record["framework_id"] is None for record in raw["llm_calls"])

    empty = seed_assessment(db)
    assert v2().load_claim_set(db, empty.id) is None


def test_scenario_4_v1_summary_has_no_claim_set(db, monkeypatch):
    from app.services import desk_review

    monkeypatch.setattr(desk_review, "_call_claude_desk_review", lambda **_kw: _v1_result())
    assessment = seed_assessment(db)
    add_evidence(db, assessment, filename="policy.pdf", text=policy_text(Q_CONSENT))
    run_desk_review(db, assessment)
    assert v2().load_claim_set(db, assessment.id) is None


# --------------------------------------------------------------------------- #
# Scenario 5: the adapter
# --------------------------------------------------------------------------- #


def _claim_set(monkeypatch, sources, framework_ids, provider=None):
    from app.services.grounding import run_stages_0_1

    (provider or FakeProvider()).install(monkeypatch)
    return run_stages_0_1(sources, framework_ids)


def test_scenario_5_adapter_maps_claims_and_caps_coverage(monkeypatch):
    from app.frameworks.registry import FrameworkRegistry

    adapter = v2().claims_to_desk_review_result
    sources = [
        make_source(policy_text(Q_DPO, Q_ROLES, Q_CONSENT, Q_ACCESS), n=1, filename="policy.pdf",
                    category="privacy_policy"),
        make_source(policy_text(Q_DPO), n=2, filename="old.docx", legacy=True),
        make_source("[Screenshot: idp.png]\n\n" + Q_SCREEN + "\n", n=3, filename="idp.png", mime="image/png"),
        make_source("", n=4, filename="empty.pdf"),
    ]
    claim_set = _claim_set(monkeypatch, sources, ["dpdpa", "iso27001"])
    assert claim_set.status == "complete"
    chunk_by_id = {chunk.chunk_id: chunk for chunk in claim_set.chunks}

    for framework_id in ("dpdpa", "iso27001"):
        result = adapter(claim_set, framework_id)
        control_ids = [c.id for c in FrameworkRegistry.get(framework_id).all_controls()]
        assert set(result) == {"document_catalog", "evidence_map", "absence_findings",
                               "signal_flags", "coverage_summary"}
        assert result["absence_findings"] == [] and result["signal_flags"] == []  # Q2
        tagged = {rid for claim in claim_set.claims for rid in claim.requirement_ids if rid in control_ids}
        assert list(result["coverage_summary"]) == control_ids
        for rid, level in result["coverage_summary"].items():
            assert level == ("partial" if rid in tagged else "not_covered")  # Q1: never adequate
        assert list(result["evidence_map"]) == [rid for rid in control_ids if rid in tagged]
        for rid, items in result["evidence_map"].items():
            expected = [claim for claim in claim_set.claims if rid in claim.requirement_ids]
            assert [entry["claim_id"] for entry in items] == [claim.claim_id for claim in expected]
            for entry, claim in zip(items, expected):
                chunk = chunk_by_id[claim.chunk_id]
                assert entry["quote"] == claim.quote
                assert entry["document"] == claim.filename
                assert entry["location"] == (chunk.heading or f"Part {chunk.ordinal}")
                assert entry["citation"] == claim.citation
                assert entry["statement"] == claim.statement
                assert entry["kind"] == claim.kind and entry["support"] == claim.support
                assert entry["tag_status"] == "suggested"
                assert entry["needs_review"] == claim.needs_review
                assert entry["derived_from_image"] == claim.derived_from_image
        catalog = result["document_catalog"]
        assert [entry["filename"] for entry in catalog] == [s.filename for s in sources]
        for entry, source in zip(catalog, claim_set.sources):
            assert entry["document_type"] == source["category"]
            assert entry["metadata"] == source["metadata"]
            assert entry["derived_from_image"] == source["derived_from_image"]
            source_tags = {rid for c in claim_set.claims if c.source_id == source["source_id"]
                           for rid in c.requirement_ids}
            assert entry["coverage_areas"] == [rid for rid in control_ids if rid in source_tags]

    dpdpa = adapter(claim_set, "dpdpa")
    iso = adapter(claim_set, "iso27001")
    assert "ISO.A5.2" not in dpdpa["evidence_map"] and "CH4.SDF.1" not in iso["evidence_map"]
    # One claim tagged across frameworks appears under both (D-P6-C).
    access = next(claim for claim in claim_set.claims if claim.quote == Q_ACCESS)
    assert access.claim_id in [e["claim_id"] for e in dpdpa["evidence_map"]["CH4.SDF.1"]]
    assert access.claim_id in [e["claim_id"] for e in iso["evidence_map"]["ISO.A5.18"]]
    # Legacy claims have no citation; screenshot claims are kept and flagged (Q3).
    legacy_entries = [e for e in dpdpa["evidence_map"]["CH4.SDF.1"] if e["document"] == "old.docx"]
    assert legacy_entries and all(e["citation"] is None for e in legacy_entries)
    screen = iso["evidence_map"]["ISO.A5.17"]
    assert [e["quote"] for e in screen] == [Q_SCREEN]
    assert screen[0]["derived_from_image"] is True and screen[0]["needs_review"] is True
    assert dpdpa["coverage_summary"]["CH2.CONSENT.2"] == "partial"


def test_scenario_5_no_claims_means_not_covered_everywhere(monkeypatch):
    from app.frameworks.registry import FrameworkRegistry

    sources = [make_source(policy_text("Nothing in this sentence matches any tagged quote at all."))]
    claim_set = _claim_set(monkeypatch, sources, ["dpdpa"])
    result = v2().claims_to_desk_review_result(claim_set, "dpdpa")
    assert result["evidence_map"] == {}
    assert result["coverage_summary"] == {
        c.id: "not_covered" for c in FrameworkRegistry.get("dpdpa").all_controls()
    }
    assert result["document_catalog"][0]["coverage_areas"] == []


# --------------------------------------------------------------------------- #
# Scenario 6: _persist_findings with a precomputed citation
# --------------------------------------------------------------------------- #


def test_scenario_6_persist_findings_uses_precomputed_citation(db, monkeypatch):
    from app.services import desk_review
    from app.services.citations import dumps_citations

    assessment = seed_assessment(db)
    grounded = {
        "evidence_version_id": "v-precomputed",
        "location_type": "text_span",
        "location_ref": "chars:120-205",
        "excerpt": Q_CONSENT,
    }
    relocated = []
    real_cite = desk_review.cite_quotes

    def cite_spy(sources, quotes, **kwargs):
        relocated.append(list(quotes))
        return real_cite(sources, quotes, **kwargs)

    monkeypatch.setattr(desk_review, "cite_quotes", cite_spy)
    result = {
        "evidence_map": {
            "CH2.CONSENT.1": [
                {"quote": Q_CONSENT, "document": "policy.pdf", "location": "Part 1", "citation": grounded},
                {"quote": Q_DPO, "document": "old.docx", "location": "Part 1", "citation": None},
                {"quote": Q_ACCESS, "document": "policy.pdf", "location": "Section 2"},
            ]
        },
        "absence_findings": [],
        "signal_flags": [],
    }
    desk_review._persist_findings(
        db=db, assessment_id=assessment.id, framework_id="dpdpa", result=result,
        doc_id_by_filename={}, sources=[],
    )
    db.commit()
    rows = findings(db, assessment)
    assert [row.source_quote for row in rows] == [Q_CONSENT, Q_DPO, Q_ACCESS]
    assert rows[0].citations_json == dumps_citations([grounded])
    assert rows[1].citations_json == "[]"
    assert relocated == [[Q_ACCESS]]  # only the item without a precomputed citation is re-located


# --------------------------------------------------------------------------- #
# Scenario 7: pre-fill from v2 output (P5-4 keeps working)
# --------------------------------------------------------------------------- #


def test_scenario_7_dpdpa_only_prefill_from_v2(db, monkeypatch, flag_v2):
    from app.models.desk_review import DeskReviewFinding
    from app.models.questionnaire import QuestionnaireResponse
    from app.services.desk_review_findings import finding_has_grounded_citation
    from app.services.question_engine import build_adaptive_questionnaire

    FakeProvider().install(monkeypatch)
    assessment = seed_assessment(db)
    _evidence, version = add_evidence(db, assessment, filename="policy.pdf", text=policy_text(Q_CONSENT))
    summary = run_desk_review(db, assessment)
    assert summary.status == "completed"

    coverage = json.loads(summary.coverage_summary)
    assert coverage["CH2.CONSENT.1"] == "partial"
    assert set(coverage.values()) == {"partial", "not_covered"}

    rows = findings(db, assessment)
    assert {row.finding_type for row in rows} == {"evidence"}  # Q2: no absence or signal rows
    consent = [row for row in rows if row.requirement_id == "CH2.CONSENT.1"]
    assert len(consent) == 1 and consent[0].source_quote == Q_CONSENT
    assert finding_has_grounded_citation(consent[0])
    citation = json.loads(consent[0].citations_json)[0]
    start, end = map(int, citation["location_ref"].removeprefix("chars:").split("-"))
    assert citation["evidence_version_id"] == version.id
    assert version.extracted_text[start:end] == Q_CONSENT == citation["excerpt"]

    responses = db.query(QuestionnaireResponse).filter_by(assessment_id=assessment.id).all()
    assert [(r.question_id, r.answer, r.confidence, r.answer_source) for r in responses] == [
        ("CH2.CONSENT.1", "partially_implemented", "medium", "document")
    ]
    questions = {
        q["id"]: q
        for section in build_adaptive_questionnaire(assessment.id, db)["sections"]
        for q in section.get("questions", [])
    }
    assert questions["CH2.CONSENT.1"]["status"] == "pre_filled"
    assert questions["CH2.CONSENT.1"]["pre_fill_answer"] == "partially_implemented"
    assert questions["CH2.CONSENT.2"]["status"] != "pre_filled"
    assert db.query(DeskReviewFinding).filter_by(assessment_id=assessment.id, finding_type="absence").count() == 0


def test_scenario_7_ucc_cluster_prefill_from_v2(db, monkeypatch, flag_v2):
    from app.models.questionnaire import QuestionnaireResponse
    from app.services.question_engine import CLUSTER_EVIDENCE_NOTE, build_adaptive_questionnaire

    def cluster_002(assessment):
        return next(
            q
            for section in build_adaptive_questionnaire(assessment.id, db)["sections"]
            for q in section.get("questions", [])
            if q["id"] == "CLUSTER_002"
        )

    FakeProvider().install(monkeypatch)
    both = seed_assessment(db, ("dpdpa", "iso27001"))
    add_evidence(db, both, filename="policy.pdf", text=policy_text(Q_DPO, Q_ROLES))
    assert run_desk_review(db, both).status == "completed"
    question = cluster_002(both)
    assert question["status"] == "pre_filled"
    assert (question["pre_fill_answer"], question["pre_fill_confidence"], question["pre_fill_source"]) == (
        "partially_implemented", "medium", "document",
    )
    row = db.query(QuestionnaireResponse).filter_by(assessment_id=both.id, question_id="CLUSTER_002").one()
    assert (row.answer, row.confidence, row.answer_source) == ("partially_implemented", "medium", "document")
    assert db.query(QuestionnaireResponse).filter_by(assessment_id=both.id, answer="fully_implemented").count() == 0

    one_member = seed_assessment(db, ("dpdpa", "iso27001"))
    add_evidence(db, one_member, filename="policy.pdf", text=policy_text(Q_DPO))
    assert run_desk_review(db, one_member).status == "completed"
    question = cluster_002(one_member)
    assert question["status"] == "active"
    assert question["desk_review_note"] == CLUSTER_EVIDENCE_NOTE
    assert json.loads(summary_of(db, one_member).coverage_summary)["ISO.A5.2"] == "not_covered"


def test_scenario_7_v1_judge_reads_v2_findings(db, monkeypatch, flag_v2):
    from app.services.claude_analyzer import _evidence_from_desk_review
    from app.services.desk_review_findings import load_desk_review_data

    FakeProvider().install(monkeypatch)
    assessment = seed_assessment(db, ("dpdpa", "iso27001"))
    add_evidence(db, assessment, filename="policy.pdf", text=policy_text(Q_DPO, Q_ROLES, Q_ACCESS))
    run_desk_review(db, assessment)
    data = load_desk_review_data(db, assessment)
    assert data["absence_findings"] == [] and data["signal_flags"] == []
    assert _evidence_from_desk_review(data) == {
        "CH4.SDF.1": [Q_DPO, Q_ACCESS],
        "ISO.A5.2": [Q_ROLES],
        "ISO.A5.18": [Q_ACCESS],
    }


# --------------------------------------------------------------------------- #
# Scenario 8: failure mapping over affected_framework_ids()
# --------------------------------------------------------------------------- #


def test_scenario_8_incomplete_claim_set_fails_only_affected_frameworks(db, monkeypatch, flag_v2):
    from app.frameworks.registry import FrameworkRegistry
    from app.services.desk_review import DESK_REVIEW_PARTIAL_MESSAGE
    from app.services.desk_review_findings import failed_desk_review_frameworks
    from app.services.grounding.batches import extraction_batches

    iso_only = [b for b in extraction_batches(["dpdpa", "iso27001"])
                if all(rid.startswith("ISO.") for rid in b.requirement_ids)]
    assert iso_only  # precondition: some batches hold only ISO controls
    FakeProvider(fail_extraction=lambda ids: all(rid.startswith("ISO.") for rid in ids)).install(monkeypatch)
    assessment = seed_assessment(db, ("dpdpa", "iso27001"))
    add_evidence(db, assessment, filename="policy.pdf", text=policy_text(Q_DPO, Q_ROLES, Q_CONSENT))
    summary = run_desk_review(db, assessment)

    iso_name = FrameworkRegistry.get("iso27001").name
    assert summary.status == "completed"
    assert summary.error_message == DESK_REVIEW_PARTIAL_MESSAGE.format(names=iso_name)
    assert failed_desk_review_frameworks(summary) == ["iso27001"]
    raw = raw_of(db, assessment)
    claim_set = v2().load_claim_set(db, assessment.id)
    assert claim_set.status == "incomplete" and claim_set.affected_framework_ids() == ("iso27001",)
    assert len(claim_set.failed_units) == len(iso_only)
    assert raw["frameworks"]["iso27001"] == {
        "status": "error",
        "error": v2().V2_INCOMPLETE_MESSAGE.format(
            name=iso_name, count=len(iso_only), error="parse_failure"
        ),
    }
    assert iso_name in raw["frameworks"]["iso27001"]["error"]
    assert raw["frameworks"]["dpdpa"]["status"] == "completed"
    rows = findings(db, assessment)
    assert rows and {row.framework_id for row in rows} == {"dpdpa"}
    coverage = json.loads(summary.coverage_summary)
    assert not any(rid.startswith("ISO.") for rid in coverage)


def test_scenario_8_every_framework_affected_means_error(db, monkeypatch, flag_v2):
    from app.frameworks.registry import FrameworkRegistry

    FakeProvider(raise_extraction=lambda ids: True).install(monkeypatch)
    assessment = seed_assessment(db)
    add_evidence(db, assessment, filename="policy.pdf", text=policy_text(Q_CONSENT))
    summary = run_desk_review(db, assessment)
    claim_set = v2().load_claim_set(db, assessment.id)
    assert claim_set is not None and claim_set.status == "incomplete"
    first_error = claim_set.failed_units[0].error
    assert first_error.startswith("RuntimeError: ")
    expected = v2().V2_INCOMPLETE_MESSAGE.format(
        name=FrameworkRegistry.get("dpdpa").name, count=len(claim_set.failed_units), error=first_error,
    )
    assert summary.status == "error" and summary.error_message == expected
    assert db.get(type(assessment), assessment.id).desk_review_status == "error"
    assert raw_of(db, assessment)["frameworks"]["dpdpa"] == {"status": "error", "error": expected}
    assert findings(db, assessment) == []


def test_scenario_8_budget_exceeded_fails_every_framework_before_any_call(db, monkeypatch, flag_v2):
    from app.frameworks.registry import FrameworkRegistry
    from app.services.desk_review import DESK_REVIEW_ALL_FAILED_MESSAGE

    provider = FakeProvider().install(monkeypatch)
    monkeypatch.setattr(settings, "v2_max_extraction_calls", 1)
    assessment = seed_assessment(db, ("dpdpa", "iso27001"))
    add_evidence(db, assessment, filename="policy.pdf", text=policy_text(Q_DPO))
    summary = run_desk_review(db, assessment)

    names = ", ".join(FrameworkRegistry.get(fid).name for fid in ("dpdpa", "iso27001"))
    assert summary.status == "error"
    assert summary.error_message == DESK_REVIEW_ALL_FAILED_MESSAGE.format(names=names)
    raw = raw_of(db, assessment)
    message = v2().V2_BUDGET_MESSAGE.format(planned=8, cap=1)
    assert "8" in message and "1" in message
    assert raw["frameworks"] == {fid: {"status": "error", "error": message} for fid in ("dpdpa", "iso27001")}
    assert raw["claim_set"] is None and raw["llm_calls"] == []
    assert provider.calls == []
    assert v2().load_claim_set(db, assessment.id) is None


def test_scenario_8_unexpected_error_fails_every_framework(db, monkeypatch, flag_v2):
    def broken(*_args, **_kwargs):
        raise KeyError("programming error")

    monkeypatch.setattr(v2(), "run_stages_0_1", broken)
    assessment = seed_assessment(db)
    add_evidence(db, assessment, filename="policy.pdf", text=policy_text(Q_DPO))
    summary = run_desk_review(db, assessment)
    expected = v2().V2_FAILED_MESSAGE.format(error="KeyError: 'programming error'")
    assert summary.status == "error" and summary.error_message == expected
    assert raw_of(db, assessment)["frameworks"]["dpdpa"] == {"status": "error", "error": expected}


# --------------------------------------------------------------------------- #
# Scenario 9: concurrency (Q6)
# --------------------------------------------------------------------------- #


def test_scenario_9_run_stages_max_workers(monkeypatch):
    from app.services.grounding import pipeline

    workers = []
    real = pipeline.run_bounded

    def spy(fn, items, *, max_workers):
        workers.append(max_workers)
        return real(fn, items, max_workers=max_workers)

    monkeypatch.setattr(pipeline, "run_bounded", spy)
    monkeypatch.setattr(settings, "llm_max_concurrency", 2)
    sources = [make_source(policy_text(Q_CONSENT))]
    FakeProvider().install(monkeypatch)
    pipeline.run_stages_0_1(sources, ["dpdpa"])
    assert workers and set(workers) == {2}  # P6-3a default unchanged
    workers.clear()
    pipeline.run_stages_0_1(sources, ["dpdpa"], max_workers=5)
    assert workers and set(workers) == {5}


# --------------------------------------------------------------------------- #
# Scenario 10: end to end through the API route
# --------------------------------------------------------------------------- #


def test_scenario_10_api_route_runs_v2(tmp_path, monkeypatch, flag_v2):
    from alembic import command
    from alembic.config import Config
    from fastapi.testclient import TestClient

    from app.database import get_db
    from app.main import app as fastapi_app

    path = tmp_path / "route.sqlite3"
    cfg = Config(str(REPO_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{path}")
    command.upgrade(cfg, "head")
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{path}")
    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})
    session = sessionmaker(bind=engine)()

    def override():
        yield session

    FakeProvider().install(monkeypatch)
    assessment = seed_assessment(session, ("dpdpa", "iso27001"))
    add_evidence(session, assessment, filename="policy.pdf", text=policy_text(Q_DPO, Q_ROLES))
    fastapi_app.dependency_overrides[get_db] = override
    try:
        with TestClient(fastapi_app) as client:
            posted = client.post(f"/api/assessments/{assessment.id}/desk-review")
            fetched = client.get(f"/api/assessments/{assessment.id}/desk-review")
    finally:
        fastapi_app.dependency_overrides.clear()
        session.close()
        engine.dispose()
    assert posted.status_code == 200, posted.text
    body = posted.json()
    assert body["status"] == "completed" and body["failed_frameworks"] == []
    assert body["finding_count"] == 2
    assert fetched.status_code == 200
    assert Q_DPO in fetched.text and Q_ROLES in fetched.text


# --------------------------------------------------------------------------- #
# Scenario 11: structural guards
# --------------------------------------------------------------------------- #


def test_scenario_11_only_desk_review_v2_imports_grounding():
    importers = []
    for path in (REPO_ROOT / "app").rglob("*.py"):
        if (REPO_ROOT / "app" / "services" / "grounding") in path.parents:
            continue
        source = path.read_text(encoding="utf-8", errors="ignore")
        if "services.grounding" in source or re.search(r"from app\.services import[^\n]*\bgrounding\b", source):
            importers.append(str(path.relative_to(REPO_ROOT)))
    # P6-4 (tasks/handoffs/2026-09-28-p6-4-v2-stage-2-judge.md) allows exactly one
    # more importer, the v2 analysis service. Any other importer still fails.
    assert "app/services/desk_review_v2.py" in importers
    # P6-10 (tasks/handoffs/2026-09-28-p6-10-remediation-and-narrative.md) adds the two
    # drafting services, which reuse grounding.prompts.wrap_untrusted only.
    assert set(importers) <= {
        "app/services/desk_review_v2.py", "app/services/analysis_v2.py",
        "app/services/remediation_draft.py", "app/services/narrative.py",
    }


def test_scenario_11_p6_3a_prompts_unchanged():
    """The v2 extraction and support prompts are P6-3a's; P6-3b adds no wording."""
    from app.services.grounding import prompts

    assert prompts.PROMPT_VERSION == "p6-3a.1"
