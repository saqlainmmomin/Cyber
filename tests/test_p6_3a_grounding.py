"""TDD ("red") contract suite for P6-3a, the v2 grounding core.

Written by the designer before the implementation. It pins the interface that
``tasks/handoffs/2026-09-26-p6-3-v2-stages-0-1.md`` specifies and must turn
green WITHOUT edits to its assertions. If an assertion looks wrong, report it
in the handoff's Results; do not change it. Scenario numbers match the
handoff's "Test scenarios" section.

Package under contract (does not exist yet): ``app.services.grounding`` with
the modules ``sources``, ``chunking``, ``metadata``, ``batches``, ``prompts``,
``schemas``, ``claims`` and ``pipeline``.

Every package-dependent test resolves it through ``g()`` as its first
statement. Before implementation each fails with
``ModuleNotFoundError: No module named 'app.services.grounding'``, which is a
failure for the right reason, not a mistake in this file.

No live LLM is used. The provider client is faked at ``llm_client._client`` so
the real ``llm_client.call_llm`` runs and writes real call records. The
package seam ``pipeline._call_llm`` is only wrapped (spied) where a scenario
checks request kwargs. Fixtures are invented and live in
``tests/grounding_fixtures/``.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import random
import re
import subprocess
import threading
import time
import unicodedata
import uuid
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 - register all ORM tables
from app.config import settings
from app.database import Base
from app.services import llm_client
from app.services.citations import locate_excerpt, normalize_with_offsets, validate_citations

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "grounding_fixtures"
PACKAGE = "app.services.grounding"

BEGIN = "<<<BEGIN UNTRUSTED DOCUMENT TEXT>>>"
END = "<<<END UNTRUSTED DOCUMENT TEXT>>>"
NEUTRAL_END = "‹‹‹END UNTRUSTED DOCUMENT TEXT›››"

INFOSEC = "infosec_policy.txt"
PRIVACY = "privacy_notice.txt"
INJECTED = "injected_vendor_letter.txt"

DUP_SENTENCE = (
    "All production access is reviewed by the system owner every quarter and "
    "exceptions are recorded in the access register."
)

EXPECTED_REJECTION_REASONS = (
    "over_call_cap",
    "malformed_item",
    "no_valid_requirement",
    "quote_too_long",
    "quote_too_short",
    "quote_outside_chunk",
    "quote_in_other_document",
    "quote_unicode_mismatch",
    "quote_not_found",
    "quote_in_truncation_marker",
    "support_no",
    "support_partial_unusable",
    "support_missing",
    "support_unit_failed",
)

PINNED_METRIC_KEYS = {
    "sources", "empty_sources", "chunks", "batches", "extraction_calls_planned",
    "extraction_calls", "extraction_retries", "support_calls", "support_retries",
    "proposed", "rejected_by_reason", "located", "merged_duplicates", "support",
    "verified", "verified_by_framework", "requirements_with_claims",
    "unknown_requirement_ids", "unverified_attributes_dropped",
    "support_unknown_refs", "delimiter_collisions", "derived_from_image_claims",
    "tokens", "failed_units", "grounding_failure_rate", "batch_system_prompt_sha256",
}

EXTRACTION_TAG = re.compile(r"^b\d+/\d+\|c\d+/\d+(\+retry)?$")
SUPPORT_TAG = re.compile(r"^c\d+/\d+:s\d+/\d+(\+retry|\+missing(\+retry)?)?$")
SUPPORT_ITEM = re.compile(
    r"^\[(c\d+)\]\nstatement: ([^\n]*)\n" + re.escape(BEGIN) + r"\n(.*?)\n" + re.escape(END),
    re.M | re.S,
)


# --------------------------------------------------------------------------- #
# Module under contract
# --------------------------------------------------------------------------- #


def g(module: str = ""):
    """The package under contract, imported lazily so a missing package fails
    each test individually (FAILED) instead of erroring collection."""

    return importlib.import_module(PACKAGE + (f".{module}" if module else ""))


# --------------------------------------------------------------------------- #
# Fixtures and helpers that do not need the package
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module", autouse=True)
def _register_frameworks():
    from app.main import _register_frameworks as register

    register()


@pytest.fixture(autouse=True)
def _serial_by_default(monkeypatch):
    monkeypatch.setattr(settings, "llm_max_concurrency", 1)


def read_fixture(name: str) -> str:
    with open(FIXTURES / name, encoding="utf-8", newline="") as handle:
        return handle.read()


def neutralise(text: str) -> str:
    return text.replace("<<<", "‹‹‹").replace(">>>", "›››")


def norm(text: str) -> str:
    return normalize_with_offsets(text)[0]


def candidate_sentences(text: str, *, ascii_only: bool = False) -> list[str]:
    found: list[str] = []
    for line in text.splitlines():
        for sentence in re.split(r"(?<=[.!?])\s+", line.strip()):
            sentence = sentence.strip()
            if not 40 <= len(sentence) <= 400:
                continue
            if "<<<" in sentence or ">>>" in sentence or sentence.endswith("-"):
                continue
            if ascii_only and not sentence.isascii():
                continue
            if sentence not in found:
                found.append(sentence)
    return found


def item(quote, statement, ids, *, kind="design", period=None, owner=None) -> dict:
    return {
        "quote": quote,
        "statement": statement,
        "kind": kind,
        "stated_period": period,
        "stated_owner": owner,
        "requirement_ids": list(ids),
    }


def make_source(name=None, *, text=None, n=1, filename=None, mime="text/plain", category="other"):
    SourceDocument = g("sources").SourceDocument
    if text is None:
        text = read_fixture(name)
    return SourceDocument(
        source_id=f"ev:v-{n}",
        evidence_id=f"e-{n}",
        evidence_version_id=f"v-{n}",
        legacy_document_id=None,
        filename=filename or name or f"doc-{n}.txt",
        category=category,
        mime_type=mime,
        text=text,
    )


def fixture_sources(*names):
    return [make_source(name, n=index + 1) for index, name in enumerate(names)]


def chunks_of(source):
    return [chunk for chunk in g("chunking").chunk_sources([source])]


def chunk_containing(chunks, source, raw: str):
    index = source.text.index(raw)
    for chunk in chunks:
        if chunk.source_id == source.source_id and chunk.start <= index and index + len(raw) <= chunk.end:
            return chunk
    raise AssertionError(f"fixture precondition: {raw[:40]!r} is not inside a single chunk")


def claims_with(claim_set, *, statement=None, model_quote=None):
    return [
        claim
        for claim in claim_set.claims
        if (statement is None or claim.statement == statement)
        and (model_quote is None or claim.model_quote == model_quote)
    ]


def reasons(claim_set) -> dict:
    return claim_set.metrics["rejected_by_reason"]


def _response(text: str, prompt_tokens: int, completion_tokens: int, stream: bool):
    usage = SimpleNamespace(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        prompt_tokens_details=SimpleNamespace(cached_tokens=0),
    )
    if not stream:
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=text), finish_reason="stop")],
            usage=usage,
        )
    return iter(
        [
            SimpleNamespace(
                choices=[SimpleNamespace(delta=SimpleNamespace(content=text), finish_reason="stop")],
                usage=None,
            ),
            SimpleNamespace(choices=[], usage=usage),
        ]
    )


def _system_text(system) -> str:
    if isinstance(system, str):
        return system
    return "".join(block.get("text", "") for block in system)


def happy_extract(ctx):
    sentences = candidate_sentences(ctx.chunk_text)
    if not sentences:
        return []
    quote = sentences[0]
    return [item(quote, f"Stated: {quote}", [ctx.ids[0]])]


def yes_support(entry, ctx):
    return {"verdict": "yes", "supported_statement": None}


class FakeLLM:
    """A provider-level fake answering per prompt.

    Extraction calls are recognised by the absence of support items; the fake
    identifies the chunk from the ``document:`` and ``part:`` header lines and
    the batch from the ``- <id> [`` lines of the system prompt.
    """

    def __init__(self, sources, framework_ids, *, extract=happy_extract, support=yes_support,
                 support_unit=None, jitter=False):
        self.sources = list(sources)
        self.by_filename = {
            neutralise(s.filename.replace("\r", "").replace("\n", "")[:200]): s for s in self.sources
        }
        self.chunks = {
            (chunk.source_id, chunk.ordinal): chunk
            for chunk in g("chunking").chunk_sources(self.sources)
        }
        self.batches = g("batches").extraction_batches(framework_ids)
        self.batch_by_ids = {batch.requirement_ids: batch for batch in self.batches}
        self.extract = extract
        self.support = support
        self.support_unit = support_unit
        self.jitter = jitter
        self.lock = threading.Lock()
        self.in_flight = 0
        self.max_in_flight = 0
        self.seen = Counter()
        self.extraction_calls: list = []
        self.support_calls: list = []
        self.total_calls = 0

    def install(self, monkeypatch):
        monkeypatch.setattr(
            llm_client,
            "_client",
            SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=self.create))),
        )
        return self

    def create(self, **kwargs):
        with self.lock:
            self.in_flight += 1
            self.total_calls += 1
            self.max_in_flight = max(self.max_in_flight, self.in_flight)
        try:
            if self.jitter:
                time.sleep(random.random() * 0.005)
            messages = kwargs["messages"]
            system = _system_text(messages[0]["content"])
            user = messages[1]["content"]
            with self.lock:
                attempt = self.seen[(system, user)]
                self.seen[(system, user)] += 1
            if SUPPORT_ITEM.search(user):
                out = self._support(system, user, attempt)
            else:
                out = self._extract(system, user, attempt)
            if isinstance(out, BaseException):
                raise out
            text = out if isinstance(out, str) else json.dumps(out)
            return _response(
                text,
                max(1, len(system + user) // 4),
                max(1, len(text) // 4),
                bool(kwargs.get("stream")),
            )
        finally:
            with self.lock:
                self.in_flight -= 1

    def _extract(self, system, user, attempt):
        filename = re.search(r"^document: (.*)$", user, re.M).group(1)
        ordinal = int(re.search(r"^part: (\d+) of (\d+)$", user, re.M).group(1))
        ids = tuple(re.findall(r"^- (\S+) \[", system, re.M))
        batch = self.batch_by_ids[ids]
        source = self.by_filename[filename]
        chunk = self.chunks[(source.source_id, ordinal)]
        ctx = SimpleNamespace(
            source=source,
            chunk=chunk,
            chunk_text=source.text[chunk.start:chunk.end],
            ids=ids,
            batch=batch,
            attempt=attempt,
            system=system,
            user=user,
        )
        with self.lock:
            self.extraction_calls.append(ctx)
        out = self.extract(ctx)
        if isinstance(out, list):
            return {"claims": out}
        return out

    def _support(self, system, user, attempt):
        entries = [
            SimpleNamespace(ref=ref, statement=statement, quote=quote)
            for ref, statement, quote in SUPPORT_ITEM.findall(user)
        ]
        ctx = SimpleNamespace(entries=entries, attempt=attempt, system=system, user=user)
        with self.lock:
            self.support_calls.append(ctx)
        if self.support_unit is not None:
            out = self.support_unit(ctx)
            if out is not None:
                return out
        verdicts = []
        for entry in entries:
            verdict = self.support(entry, ctx)
            if verdict is not None:
                verdicts.append({"ref": entry.ref, **verdict})
        return {"verdicts": verdicts}


def run(sources, framework_ids):
    return g("pipeline").run_stages_0_1(sources, framework_ids)


def install_spy(monkeypatch):
    pipeline = g("pipeline")
    original = pipeline._call_llm
    calls: list[dict] = []
    lock = threading.Lock()

    def spy(**kwargs):
        with lock:
            calls.append(dict(kwargs))
        return original(**kwargs)

    monkeypatch.setattr(pipeline, "_call_llm", spy)
    return calls


# --------------------------------------------------------------------------- #
# DB helpers (scenarios 2 and 16)
# --------------------------------------------------------------------------- #


@pytest.fixture()
def db(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'grounding.sqlite3'}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


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


def add_evidence(db, assessment, *, filename, versions, mime="text/plain", category="other"):
    """versions: list of (extracted_text, status). Returns (evidence, [version rows])."""
    from app.models.evidence import Evidence, EvidenceVersion

    first_text = versions[0][0]
    evidence = Evidence(
        engagement_id=assessment.engagement_id,
        assessment_id=assessment.id,
        document_category=category,
        original_filename=filename,
        storage_path=f"blobs/{uuid.uuid4().hex}",
        file_hash_sha256=hashlib.sha256(first_text.encode()).hexdigest(),
        file_size_bytes=len(first_text.encode()),
        mime_type=mime,
        status="active",
        uploaded_by="consultant",
    )
    db.add(evidence)
    db.flush()
    rows = []
    for number, (text_value, status) in enumerate(versions, start=1):
        row = EvidenceVersion(
            evidence_id=evidence.id,
            version_number=number,
            storage_path=f"blobs/{uuid.uuid4().hex}",
            file_hash_sha256=hashlib.sha256(text_value.encode()).hexdigest(),
            file_size_bytes=len(text_value.encode()),
            status=status,
            original_filename=filename,
            mime_type=mime,
            extracted_text=text_value,
        )
        db.add(row)
        rows.append(row)
    db.commit()
    return evidence, rows


# --------------------------------------------------------------------------- #
# Fixture integrity (no package needed)
# --------------------------------------------------------------------------- #


def test_fixture_files_keep_their_special_characters():
    """The scenarios below depend on these characters surviving git and editors."""
    infosec = read_fixture(INFOSEC)
    for needle in ("\r\n", " ", "\t", "ﬁ", "é", "İ", "₹",
                   "“Confidential”", "authoriza-\ntion", "राजेश"):
        assert needle in infosec, repr(needle)
    assert infosec.count(DUP_SENTENCE) == 2
    assert len(infosec.split()) > 1800
    for label in ("Version: 2.1", "Approved by: Chief Risk Officer",
                  "Effective Date: 14 March 2025", "Next Review: 03/04/2026"):
        assert label in infosec
    assert "\n\n" not in infosec  # DOCX-style: no blank lines

    privacy = read_fixture(PRIVACY)
    assert "Date: 2025-01-20" in privacy and "\n\n" in privacy

    injected = read_fixture(INJECTED)
    assert END in injected
    assert "Ignore all previous instructions" in injected


# --------------------------------------------------------------------------- #
# Scenario 1: chunk invariants
# --------------------------------------------------------------------------- #


def _assert_tiles(text, chunks):
    if not text.strip():
        assert tuple(chunks) == ()
        return
    assert chunks[0].start == 0
    assert chunks[-1].end == len(text)
    for left, right in zip(chunks, chunks[1:]):
        assert left.end == right.start
    assert "".join(text[c.start:c.end] for c in chunks) == text
    for index, chunk in enumerate(chunks, start=1):
        assert chunk.ordinal == index
        assert chunk.word_count == len(text[chunk.start:chunk.end].split())
        assert chunk.text_sha256 == hashlib.sha256(text[chunk.start:chunk.end].encode("utf-8")).hexdigest()


def _synthetic_sectioned(sections=8, lines_per_section=4):
    lines = []
    for section in range(1, sections + 1):
        lines.append(f"SECTION {section}")
        for line in range(lines_per_section):
            lines.append(f"Line {section}.{line} has some filler words here.")
    return "\n".join(lines) + "\n"


def test_scenario_1_chunk_invariants():
    chunking = g("chunking")
    texts = {
        "infosec": read_fixture(INFOSEC),
        "privacy": read_fixture(PRIVACY),
        "injected": read_fixture(INJECTED),
        "empty": "",
        "blank": "   \n \t\n",
        "one_line": " ".join(f"Sentence number {n} is here." for n in range(1250)),
        "sectioned": _synthetic_sectioned(),
    }
    for name, text in texts.items():
        source = make_source(text=text, filename=f"{name}.txt")
        for min_words, max_words in ((800, 1500), (10, 40)):
            chunks = chunking.chunk_source(source, min_words=min_words, max_words=max_words)
            again = chunking.chunk_source(source, min_words=min_words, max_words=max_words)
            assert chunks == again
            _assert_tiles(text, chunks)
            if not chunks:
                continue
            for chunk in chunks[:-1]:
                assert chunk.word_count <= max_words, (name, chunk)
            assert chunks[-1].word_count <= max_words + 199, name
            for chunk in chunks:
                assert chunk.chunk_id == f"{source.source_id}#{chunk.ordinal}"
                assert chunk.source_id == source.source_id

    one_line = make_source(text=texts["one_line"], filename="one_line.txt")
    pieces = chunking.chunk_source(one_line, min_words=800, max_words=1500)
    assert len(pieces) >= 4
    assert all(piece.word_count <= 1500 for piece in pieces)

    infosec = make_source(text=texts["infosec"], filename=INFOSEC)
    assert len(chunking.chunk_source(infosec, min_words=800, max_words=1500)) >= 2


def test_scenario_1_headings_close_chunks_after_min_words():
    chunking = g("chunking")
    text = _synthetic_sectioned()
    source = make_source(text=text, filename="sectioned.txt")
    chunks = chunking.chunk_source(source, min_words=10, max_words=40)
    assert chunks[0].heading == "SECTION 1"
    heading_starts = [m.start() for m in re.finditer(r"^SECTION \d+$", text, re.M)]
    # the merged last chunk is the only allowed exception
    for chunk in chunks[:-1]:
        for position in heading_starts:
            if chunk.start < position < chunk.end:
                assert len(text[chunk.start:position].split()) < 10, (chunk, position)


def test_scenario_1_chunk_sources_assigns_global_index(monkeypatch):
    chunking = g("chunking")
    monkeypatch.setattr(settings, "v2_chunk_min_words", 800)
    monkeypatch.setattr(settings, "v2_chunk_max_words", 1500)
    sources = fixture_sources(INFOSEC, PRIVACY, INJECTED)
    chunks = chunking.chunk_sources(sources)
    assert [chunk.global_index for chunk in chunks] == list(range(1, len(chunks) + 1))
    order = [s.source_id for s in sources]
    assert [order.index(c.source_id) for c in chunks] == sorted(order.index(c.source_id) for c in chunks)
    assert chunking.chunk_sources(sources) == chunks


# --------------------------------------------------------------------------- #
# Scenario 2: offset fidelity under unicode and whitespace
# --------------------------------------------------------------------------- #

S2_OK = [
    (
        "Staff must treat all data marked “Confidential” as restricted and must not share it "
        "outside the company’s approved systems.",
        "STAFF MUST treat all data marked \"Confidential\" as restricted and must not share it "
        "outside the company's approved systems.",
    ),
    (
        "Multi-factor authentication is mandatory for all remote access,\tincluding vendor support "
        "sessions,\r\nand is enforced by the identity provider.",
        "multi-factor authentication is mandatory for all remote access, including vendor support "
        "sessions, and is enforced by the identity provider.",
    ),
    (
        "Privileged access requires written authoriza-\ntion from the information security team "
        "before it is granted.",
        "Privileged access requires written authorization from the information security team "
        "before it is granted.",
    ),
    (
        "The Chief Information Security Officer, राजेश कुमार, "
        "based in the İstanbul liaison office, approves every exception above ₹5,00,000 in writing.",
        "the chief information security officer, राजेश कुमार, "
        "based in the İstanbul liaison office, approves every exception above ₹5,00,000 in writing.",
    ),
]
S2_UNICODE_MISMATCH = [
    (
        "Every ﬁrewall rule change is logged and reviewed by the network team within five working days.",
        "Every firewall rule change is logged and reviewed by the network team within five working days.",
    ),
    (
        "The annual security résumé report is presented to the board of directors each April.",
        "The annual security résumé report is presented to the board of directors each April.",
    ),
]


def test_scenario_2_offset_fidelity_under_unicode_and_whitespace(db, monkeypatch):
    grounding = g()
    assessment = seed_assessment(db)
    text = read_fixture(INFOSEC)
    _evidence, (version,) = add_evidence(db, assessment, filename=INFOSEC, versions=[(text, "active")])
    (source,) = grounding.load_source_documents(db, assessment.id)
    assert source.text == text
    assert source.evidence_version_id == version.id

    chunks = chunks_of(source)
    targets = [(raw, model, "ok") for raw, model in S2_OK] + [
        (raw, model, "mismatch") for raw, model in S2_UNICODE_MISMATCH
    ]
    by_chunk: dict[str, list] = {}
    for index, (raw, model, _kind) in enumerate(targets):
        chunk = chunk_containing(chunks, source, raw)
        by_chunk.setdefault(chunk.chunk_id, []).append((index, model))

    def extract(ctx):
        if ctx.batch.index != 1:
            return []
        return [
            item(model, f"Target {index}.", [ctx.ids[0]])
            for index, model in by_chunk.get(ctx.chunk.chunk_id, [])
        ]

    FakeLLM([source], ["dpdpa"], extract=extract).install(monkeypatch)
    claim_set = run([source], ["dpdpa"])

    for index, (raw, model, kind) in enumerate(targets):
        found = claims_with(claim_set, model_quote=model)
        if kind == "mismatch":
            assert found == [], raw
            continue
        assert len(found) == 1, raw
        claim = found[0]
        assert claim.quote == raw
        assert claim.quote == text[claim.start:claim.end]
        chunk = chunk_containing(chunks, source, raw)
        assert claim.chunk_id == chunk.chunk_id
        assert chunk.start <= claim.start < claim.end <= chunk.end
        assert norm(claim.quote) == norm(model)
        assert claim.citation == {
            "evidence_version_id": version.id,
            "location_type": "text_span",
            "location_ref": f"chars:{claim.start}-{claim.end}",
            "excerpt": raw,
        }
        assert validate_citations(db, [claim.citation], assessment_id=assessment.id) == [claim.citation]
    assert reasons(claim_set)["quote_unicode_mismatch"] == 2


def test_scenario_2_seeded_offset_property(monkeypatch):
    source = make_source(INFOSEC)
    chunks = chunks_of(source)
    monkeypatch.setattr(settings, "v2_max_claims_per_call", 1000)
    rng = random.Random(0)
    planned: dict[str, list] = {}
    distorted_by_statement: dict[str, str] = {}
    for number in range(200):
        chunk = rng.choice(chunks)
        chunk_text = source.text[chunk.start:chunk.end]
        start = rng.randrange(0, len(chunk_text) - 30)
        length = rng.randint(30, 300)
        quote = chunk_text[start:start + length]
        if rng.random() < 0.7:
            quote = " ".join(quote.split())
        if rng.random() < 0.5:
            quote = quote.replace("“", '"').replace("”", '"').replace("’", "'")
        roll = rng.random()
        if roll < 0.2:
            quote = quote.upper()
        elif roll < 0.4:
            quote = quote.lower()
        statement = f"Random claim {number}."
        distorted_by_statement[statement] = quote
        planned.setdefault(chunk.chunk_id, []).append((quote, statement))

    def extract(ctx):
        if ctx.batch.index != 1:
            return []
        return [item(q, s, [ctx.ids[0]]) for q, s in planned.get(ctx.chunk.chunk_id, [])]

    FakeLLM([source], ["dpdpa"], extract=extract).install(monkeypatch)
    claim_set = run([source], ["dpdpa"])
    chunk_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    accepted = 0
    for claim in claim_set.claims:
        if claim.statement not in distorted_by_statement:
            continue
        accepted += 1
        chunk = chunk_by_id[claim.chunk_id]
        assert chunk.start <= claim.start < claim.end <= chunk.end
        assert claim.quote == source.text[claim.start:claim.end]
        assert norm(claim.quote) == norm(distorted_by_statement[claim.statement])
    print(f"P6-3a property check: {accepted}/200 distorted quotes accepted")
    assert accepted >= 150


# --------------------------------------------------------------------------- #
# Scenario 3: hallucinated quotes and every rejection reason
# --------------------------------------------------------------------------- #


def test_scenario_3_rejection_vocabulary_is_closed_and_ordered():
    assert tuple(g("claims").REJECTION_REASONS) == EXPECTED_REJECTION_REASONS


def _s3_setup():
    infosec = make_source(INFOSEC, n=1)
    privacy = make_source(PRIVACY, n=2)
    chunks = chunks_of(infosec)
    assert len(chunks) >= 2
    first, second = chunks[0], chunks[1]
    first_text = infosec.text[first.start:first.end]
    second_text = infosec.text[second.start:second.end]
    other_chunk_line = next(
        s for s in candidate_sentences(second_text)
        if locate_excerpt(first_text, s) is None and locate_excerpt(privacy.text, s) is None
    )
    straddle = " ".join(infosec.text[second.start - 80:second.start + 80].split())
    assert locate_excerpt(infosec.text, straddle) is not None
    assert locate_excerpt(first_text, straddle) is None
    other_doc_line = next(
        s for s in candidate_sentences(privacy.text) if locate_excerpt(infosec.text, s) is None
    )
    valid_line = candidate_sentences(first_text, ascii_only=True)[0]
    return infosec, privacy, first, {
        "fabricated": "Kestrel Ledger encrypts every backup with quantum-safe keys held in Zurich.",
        "other_chunk": other_chunk_line,
        "straddle": straddle,
        "other_doc": other_doc_line,
        "valid": valid_line,
    }


S3_CASES = {
    "fabricated": ("quote_not_found", 1),
    "other_chunk": ("quote_outside_chunk", 1),
    "straddle": ("quote_outside_chunk", 1),
    "other_doc": ("quote_in_other_document", 1),
    "too_short": ("quote_too_short", 1),
    "too_long": ("quote_too_long", 1),
    "malformed": ("malformed_item", 1),
    "invented_ids": ("no_valid_requirement", 1),
    "over_cap": ("over_call_cap", 5),
}


@pytest.mark.parametrize("case", sorted(S3_CASES))
def test_scenario_3_hallucinated_and_invalid_items_are_rejected(case, monkeypatch):
    g()
    infosec, privacy, first, lines = _s3_setup()

    def bad_items(ids):
        valid_id = ids[0]
        if case in ("fabricated", "other_chunk", "straddle", "other_doc"):
            return [item(lines[case], f"Case {case}.", [valid_id])]
        if case == "too_short":
            return [item("Yes.", "Case too short.", [valid_id])]
        if case == "too_long":
            return [item("x" * 700, "Case too long.", [valid_id])]
        if case == "malformed":
            return [item(lines["valid"], "Case malformed.", [valid_id], kind="maybe")]
        if case == "invented_ids":
            return [item(lines["valid"], "Case invented.", ["NOT.A.REAL.ID"])]
        return [item(lines["valid"], f"Over cap statement {n}.", [valid_id]) for n in range(30)]

    def extract(ctx):
        if ctx.batch.index == 1 and ctx.chunk.chunk_id == first.chunk_id:
            return bad_items(ctx.ids)
        return []

    FakeLLM([infosec, privacy], ["dpdpa"], extract=extract).install(monkeypatch)
    claim_set = run([infosec, privacy], ["dpdpa"])
    reason, count = S3_CASES[case]
    counts = reasons(claim_set)
    assert set(counts) == set(EXPECTED_REJECTION_REASONS)
    assert counts[reason] == count
    assert sum(counts.values()) == count
    rejected = [r for r in claim_set.rejected if r.reason == reason]
    assert len(rejected) == count
    assert all(r.batch == "b1/3" and r.chunk_id == first.chunk_id for r in rejected)
    if case == "over_cap":
        assert len(claim_set.claims) == 25
    else:
        assert claim_set.claims == ()
    if case == "invented_ids":
        assert claim_set.metrics["unknown_requirement_ids"] == 1


def test_scenario_3_truncation_marker_quote_is_rejected(monkeypatch):
    g()
    body = read_fixture(PRIVACY)
    text = body + "\n\n[... truncated to first 5000 words ...]"
    source = make_source(text=text, filename="truncated.txt")
    tail_words = " ".join(body.split()[-6:])
    quote = f"{tail_words} [... truncated to first 5000 words"
    assert locate_excerpt(text, quote) is not None

    def extract(ctx):
        return [item(quote, "Case truncation.", [ctx.ids[0]])] if ctx.batch.index == 1 else []

    FakeLLM([source], ["dpdpa"], extract=extract).install(monkeypatch)
    claim_set = run([source], ["dpdpa"])
    assert reasons(claim_set)["quote_in_truncation_marker"] == 1
    assert claim_set.claims == ()


# --------------------------------------------------------------------------- #
# Scenario 4: the span is the chunk's occurrence
# --------------------------------------------------------------------------- #


def test_scenario_4_repeated_sentence_cites_the_chunks_occurrence(monkeypatch):
    g()
    source = make_source(INFOSEC)
    chunks = chunks_of(source)
    first_index = source.text.index(DUP_SENTENCE)
    second_index = source.text.rindex(DUP_SENTENCE)
    assert chunks[0].start <= first_index < chunks[0].end
    last = chunks[-1]
    assert last.start <= second_index < last.end

    def extract(ctx):
        if ctx.batch.index == 1 and ctx.chunk.chunk_id == last.chunk_id:
            return [item(DUP_SENTENCE, "Access is reviewed quarterly.", [ctx.ids[0]])]
        return []

    FakeLLM([source], ["dpdpa"], extract=extract).install(monkeypatch)
    claim_set = run([source], ["dpdpa"])
    (claim,) = claim_set.claims
    assert claim.chunk_id == last.chunk_id
    assert (claim.start, claim.end) == (second_index, second_index + len(DUP_SENTENCE))
    assert claim.citation["location_ref"] == f"chars:{second_index}-{second_index + len(DUP_SENTENCE)}"
    assert claim.citation["location_ref"] != f"chars:{first_index}-{first_index + len(DUP_SENTENCE)}"


# --------------------------------------------------------------------------- #
# Scenario 5: closed-set tags
# --------------------------------------------------------------------------- #


def test_scenario_5_tags_outside_the_batch_are_dropped(monkeypatch):
    g()
    source = make_source(PRIVACY)
    batches = g("batches").extraction_batches(["dpdpa"])
    in_batch = batches[0].requirement_ids[0]
    other_batch = batches[1].requirement_ids[0]
    quote = candidate_sentences(source.text)[0]

    def extract(ctx):
        if ctx.batch.index == 1:
            return [item(quote, "Tagging case.", [in_batch, "ISO.A8.99", other_batch])]
        return []

    FakeLLM([source], ["dpdpa"], extract=extract).install(monkeypatch)
    claim_set = run([source], ["dpdpa"])
    (claim,) = claim_set.claims
    assert claim.requirement_ids == (in_batch,)
    assert claim_set.metrics["unknown_requirement_ids"] == 2


# --------------------------------------------------------------------------- #
# Scenario 6: cross-framework tagging and merge (D-P6-C)
# --------------------------------------------------------------------------- #

THREE = ["dpdpa", "iso27001", "nist_csf"]


def _s6_batches():
    batches = g("batches").extraction_batches(THREE)

    def fw_ids(batch, prefix):
        return [rid for rid in batch.requirement_ids if rid.startswith(prefix)]

    batch_a = next(b for b in batches if fw_ids(b, "ISO.") and fw_ids(b, "NIST."))
    batch_b = next(
        b for b in batches
        if b.index != batch_a.index and any(not r.startswith(("ISO.", "NIST.")) for r in b.requirement_ids)
    )
    iso_id = fw_ids(batch_a, "ISO.")[0]
    nist_id = fw_ids(batch_a, "NIST.")[0]
    dpdpa_id = next(r for r in batch_b.requirement_ids if not r.startswith(("ISO.", "NIST.")))
    return batch_a, batch_b, iso_id, nist_id, dpdpa_id


def test_scenario_6_same_fact_from_two_batches_merges_across_frameworks(monkeypatch):
    g()
    source = make_source(PRIVACY)
    batch_a, batch_b, iso_id, nist_id, dpdpa_id = _s6_batches()
    quote = candidate_sentences(source.text)[1]
    statement = "Consent can be withdrawn at any time."

    def extract(ctx):
        if ctx.batch.index == batch_a.index:
            return [item(quote, statement, [iso_id, nist_id])]
        if ctx.batch.index == batch_b.index:
            return [item(quote, statement, [dpdpa_id])]
        return []

    fake = FakeLLM([source], THREE, extract=extract).install(monkeypatch)
    claim_set = run([source], THREE)
    (claim,) = claim_set.claims
    assert claim.requirement_ids == (dpdpa_id, iso_id, nist_id)
    assert claim.framework_ids == ("dpdpa", "iso27001", "nist_csf")
    assert claim.tag_status == "suggested"
    assert len(claim.origins) == 2
    assert {origin["batch"] for origin in claim.origins} == {batch_a.label, batch_b.label}
    assert claim_set.metrics["merged_duplicates"] == 1
    seen = [e for ctx in fake.support_calls for e in ctx.entries if e.statement == statement]
    assert len(seen) == 1


def test_scenario_6_different_statements_stay_separate_and_kind_conflict_flags(monkeypatch):
    g()
    source = make_source(PRIVACY)
    batch_a, batch_b, iso_id, nist_id, dpdpa_id = _s6_batches()
    quote = candidate_sentences(source.text)[1]

    def extract(ctx):
        if ctx.batch.index == batch_a.index:
            return [
                item(quote, "Statement one.", [iso_id]),
                item(quote, "Shared statement.", [nist_id], kind="design"),
            ]
        if ctx.batch.index == batch_b.index:
            return [
                item(quote, "Statement two.", [dpdpa_id]),
                item(quote, "Shared statement.", [dpdpa_id], kind="operating"),
            ]
        return []

    FakeLLM([source], THREE, extract=extract).install(monkeypatch)
    claim_set = run([source], THREE)
    assert len(claims_with(claim_set, statement="Statement one.")) == 1
    assert len(claims_with(claim_set, statement="Statement two.")) == 1
    (shared,) = claims_with(claim_set, statement="Shared statement.")
    assert shared.kind_conflict is True
    assert shared.needs_review is True
    first_batch_kind = "design" if batch_a.index < batch_b.index else "operating"
    assert shared.kind == first_batch_kind
    assert claim_set.metrics["merged_duplicates"] == 1


# --------------------------------------------------------------------------- #
# Scenario 7: support semantics
# --------------------------------------------------------------------------- #


def test_scenario_7_support_semantics(monkeypatch):
    g()
    source = make_source(INFOSEC)
    first = chunks_of(source)[0]
    first_text = source.text[first.start:first.end]
    lines = [
        s for s in candidate_sentences(first_text, ascii_only=True)
        if s != DUP_SENTENCE and "annually" not in s.lower()
    ]
    assert len(lines) >= 7
    quote_of = {
        "STMT-YES": lines[0],
        "STMT-NO": lines[1],
        "STMT-P-OK": lines[2],
        "STMT-P-NULL": lines[3],
        "STMT-MISSING": lines[4],
        "STMT-MISSING-ONCE": lines[5],
        "STMT-P1": lines[6],
        "STMT-P2": lines[6],
        "STMT-ATTR": lines[0],
    }
    raw_quotes = set(quote_of.values()) | {DUP_SENTENCE}

    def extract(ctx):
        if ctx.batch.index != 1 or ctx.chunk.chunk_id != first.chunk_id:
            return []
        items = [
            item(quote.upper(), statement, [ctx.ids[0]],
                 period="annually" if statement == "STMT-ATTR" else None)
            for statement, quote in quote_of.items()
        ]
        items.append(item(DUP_SENTENCE.upper(), "STMT-PERIOD", [ctx.ids[0]], period="every quarter"))
        return items

    violations: list[str] = []
    seen_statements = Counter()

    def support(entry, ctx):
        if entry.quote not in raw_quotes:
            violations.append(entry.quote)
        seen_statements[entry.statement] += 1
        statement = entry.statement
        if statement == "STMT-NO":
            return {"verdict": "no", "supported_statement": None}
        if statement == "STMT-P-OK":
            return {"verdict": "partial", "supported_statement": "Only the supported part."}
        if statement == "STMT-P-NULL":
            return {"verdict": "partial", "supported_statement": None}
        if statement in ("STMT-P1", "STMT-P2"):
            return {"verdict": "partial", "supported_statement": "Merged supported statement."}
        if statement == "STMT-MISSING":
            return None
        if statement == "STMT-MISSING-ONCE" and seen_statements[statement] == 1:
            return None
        return {"verdict": "yes", "supported_statement": None}

    fake = FakeLLM([source], ["dpdpa"], extract=extract, support=support).install(monkeypatch)
    claim_set = run([source], ["dpdpa"])

    assert violations == []
    counts = reasons(claim_set)
    assert counts["support_no"] == 1
    assert counts["support_partial_unusable"] == 1
    assert counts["support_missing"] == 1

    (yes,) = claims_with(claim_set, statement="STMT-YES")
    assert yes.support == "yes" and yes.original_statement is None
    assert yes.quote == quote_of["STMT-YES"]
    assert yes.model_quote == quote_of["STMT-YES"].upper()

    (partial,) = claims_with(claim_set, statement="Only the supported part.")
    assert partial.original_statement == "STMT-P-OK"
    assert partial.support == "partial" and partial.needs_review is True

    assert len(claims_with(claim_set, statement="STMT-MISSING-ONCE")) == 1
    assert claims_with(claim_set, statement="STMT-MISSING") == []
    retry_calls = [
        ctx for ctx in fake.support_calls
        if {e.statement for e in ctx.entries} <= {"STMT-MISSING", "STMT-MISSING-ONCE"}
    ]
    assert len(retry_calls) == 1
    assert {e.statement for e in retry_calls[0].entries} == {"STMT-MISSING", "STMT-MISSING-ONCE"}

    (merged,) = claims_with(claim_set, statement="Merged supported statement.")
    assert merged.original_statement == "STMT-P1"
    assert merged.quote == quote_of["STMT-P1"]

    (period,) = claims_with(claim_set, statement="STMT-PERIOD")
    assert period.stated_period is not None and norm(period.stated_period) == "every quarter"
    (attr,) = claims_with(claim_set, statement="STMT-ATTR")
    assert attr.stated_period is None
    assert claim_set.metrics["unverified_attributes_dropped"] == 1


# --------------------------------------------------------------------------- #
# Scenario 8: failure semantics
# --------------------------------------------------------------------------- #


def _s8_run(monkeypatch, *, extract_override=None, support_unit=None):
    source = make_source(INFOSEC)
    first = chunks_of(source)[0]

    def extract(ctx):
        if ctx.batch.index == 2 and ctx.chunk.chunk_id == first.chunk_id and extract_override:
            return extract_override(ctx)
        return happy_extract(ctx)

    fake = FakeLLM([source], ["dpdpa"], extract=extract, support_unit=support_unit).install(monkeypatch)
    claim_set = run([source], ["dpdpa"])
    unit_calls = [
        ctx for ctx in fake.extraction_calls
        if ctx.batch.index == 2 and ctx.chunk.chunk_id == first.chunk_id
    ]
    return claim_set, first, unit_calls


def test_scenario_8_double_parse_failure_marks_unit_failed(monkeypatch):
    g()
    claim_set, first, unit_calls = _s8_run(monkeypatch, extract_override=lambda ctx: "not json at all")
    batch_two = g("batches").extraction_batches(["dpdpa"])[1]
    assert len(unit_calls) == 2
    (failed,) = claim_set.failed_units
    assert failed.stage == "claim_extraction"
    assert failed.error == "parse_failure"
    assert failed.chunk_id == first.chunk_id
    assert failed.requirement_ids == batch_two.requirement_ids
    assert failed.label.startswith("b2/3|c1/")
    assert claim_set.status == "incomplete"
    assert claim_set.affected_framework_ids() == ("dpdpa",)
    assert claim_set.claims != ()


def test_scenario_8_parse_failure_then_success_recovers(monkeypatch):
    g()
    claim_set, _first, unit_calls = _s8_run(
        monkeypatch,
        extract_override=lambda ctx: "not json" if ctx.attempt == 0 else happy_extract(ctx),
    )
    assert len(unit_calls) == 2
    assert claim_set.status == "complete"
    assert claim_set.failed_units == ()
    assert claim_set.metrics["extraction_retries"] == 1


def test_scenario_8_transport_exception_fails_unit_without_retry(monkeypatch):
    g()
    claim_set, _first, unit_calls = _s8_run(
        monkeypatch, extract_override=lambda ctx: RuntimeError("boom")
    )
    assert len(unit_calls) == 1
    (failed,) = claim_set.failed_units
    assert "RuntimeError" in failed.error
    assert claim_set.status == "incomplete"


def test_scenario_8_support_unit_failure_rejects_its_candidates(monkeypatch):
    g()
    claim_set, _first, _calls = _s8_run(
        monkeypatch, support_unit=lambda ctx: RuntimeError("support down")
    )
    assert claim_set.claims == ()
    assert reasons(claim_set)["support_unit_failed"] >= 1
    assert claim_set.status == "incomplete"
    assert all(unit.stage == "claim_support" for unit in claim_set.failed_units)
    assert claim_set.affected_framework_ids() == ("dpdpa",)


# --------------------------------------------------------------------------- #
# Scenario 9: budget
# --------------------------------------------------------------------------- #


def test_scenario_9_budget_is_checked_before_any_call(monkeypatch):
    grounding = g()
    source = make_source(INFOSEC)
    planned = len(chunks_of(source)) * len(g("batches").extraction_batches(["dpdpa"]))
    monkeypatch.setattr(settings, "v2_max_extraction_calls", 1)
    fake = FakeLLM([source], ["dpdpa"]).install(monkeypatch)
    with pytest.raises(grounding.ClaimBudgetExceeded) as excinfo:
        run([source], ["dpdpa"])
    assert excinfo.value.planned == planned
    assert excinfo.value.cap == 1
    assert str(planned) in str(excinfo.value)
    assert fake.total_calls == 0


def test_scenario_9_no_text_gives_complete_empty_set(monkeypatch):
    g()
    source = make_source(text="  \n\t ", filename="blank.txt")
    fake = FakeLLM([source], ["dpdpa"]).install(monkeypatch)
    claim_set = run([source], ["dpdpa"])
    assert claim_set.status == "complete"
    assert claim_set.claims == () and claim_set.llm_calls == ()
    assert claim_set.metrics["extraction_calls_planned"] == 0
    assert fake.total_calls == 0


# --------------------------------------------------------------------------- #
# Scenario 10: batch table
# --------------------------------------------------------------------------- #

BATCH_TABLE = {
    ("dpdpa",): [19, 20, 2],
    ("iso27001",): [20, 17, 20, 15, 20, 1],
    ("nist_csf",): [20, 14, 16, 11, 19, 19, 7],
    ("dpdpa", "iso27001"): [19, 18, 19, 19, 20, 15, 20, 4],
    ("dpdpa", "iso27001", "nist_csf"): [18, 17, 20, 19, 19, 19, 20, 16, 18, 16, 15, 10, 15, 18],
}


def test_scenario_10_batch_table(monkeypatch):
    batches_mod = g("batches")
    from app.frameworks.registry import FrameworkRegistry

    monkeypatch.setattr(settings, "v2_extraction_batch_max_requirements", 20)
    for framework_ids, sizes in BATCH_TABLE.items():
        batches = batches_mod.extraction_batches(list(framework_ids))
        assert [len(b.requirement_ids) for b in batches] == sizes, framework_ids
        assert [b.index for b in batches] == list(range(1, len(sizes) + 1))
        assert all(b.count == len(sizes) for b in batches)
        assert [b.label for b in batches] == [f"b{i}/{len(sizes)}" for i in range(1, len(sizes) + 1)]
        all_ids = [rid for b in batches for rid in b.requirement_ids]
        expected = [c.id for fid in framework_ids for c in FrameworkRegistry.get(fid).all_controls()]
        assert len(all_ids) == len(set(all_ids))
        assert set(all_ids) == set(expected)
        order = batches_mod.requirement_order(list(framework_ids))
        for batch in batches:
            assert list(batch.requirement_ids) == sorted(batch.requirement_ids, key=order.get)
            present = [fid for fid in framework_ids
                       if any(rid in {c.id for c in FrameworkRegistry.get(fid).all_controls()}
                              for rid in batch.requirement_ids)]
            assert list(batch.framework_ids) == present
        assert batches_mod.extraction_batches(list(framework_ids)) == batches

    three = batches_mod.extraction_batches(["dpdpa", "iso27001", "nist_csf"])
    assert three[0].group_keys[0] == "CLUSTER_001"
    assert three[0].requirement_ids[0] == "CH4.SDF.1"
    assert three[-1].group_keys[-1] == "iso27001:legal_compliance"
    assert "ISO.A5.32" in three[-1].requirement_ids
    assert three[-1].requirement_ids[-1] == "NIST.RC.CO.04"

    with pytest.raises(ValueError):
        batches_mod.extraction_batches(["not_a_framework"])
    with pytest.raises(ValueError):
        batches_mod.extraction_batches(["dpdpa", "dpdpa"])


def test_scenario_10_oversized_cluster_is_split(monkeypatch):
    batches_mod = g("batches")
    from app.frameworks.registry import FrameworkRegistry
    from app.frameworks.schema import Control, Domain, FrameworkDefinition, Section

    controls = [
        Control(id=f"SYN.{n}", title=f"Synthetic {n}", description="d", reference="r", criticality="low")
        for n in range(1, 46)
    ]
    framework = FrameworkDefinition(
        id="synthetic_p63",
        name="Synthetic",
        version="1",
        domains={"d": Domain(key="d", title="D", weight=1.0,
                             sections={"s": Section(key="s", title="S", weight=1.0, controls=controls)})},
    )
    monkeypatch.setitem(FrameworkRegistry._frameworks, "synthetic_p63", framework)
    monkeypatch.setattr(batches_mod, "CONTROL_CLUSTERS", [{
        "cluster_id": "SYN_CLUSTER",
        "controls": [{"framework": "synthetic_p63", "control": c.id} for c in controls],
    }])
    monkeypatch.setattr(settings, "v2_extraction_batch_max_requirements", 20)
    batches = batches_mod.extraction_batches(["synthetic_p63"])
    assert [len(b.requirement_ids) for b in batches] == [20, 20, 5]
    assert all(b.group_keys == ("SYN_CLUSTER",) for b in batches)


# --------------------------------------------------------------------------- #
# Scenario 11: prompt contracts and injection
# --------------------------------------------------------------------------- #


def _strict_ok(node) -> bool:
    if isinstance(node, dict):
        if node.get("type") == "object" or (isinstance(node.get("type"), list) and "object" in node["type"]):
            properties = node.get("properties", {})
            if node.get("additionalProperties") is not False:
                return False
            if sorted(node.get("required", [])) != sorted(properties):
                return False
        return all(_strict_ok(value) for value in node.values())
    if isinstance(node, list):
        return all(_strict_ok(value) for value in node)
    return True


def test_scenario_11_schemas_are_strict_compatible():
    prompts = g("prompts")
    for schema in (prompts.EXTRACTION_SCHEMA, prompts.SUPPORT_SCHEMA):
        assert set(schema) == {"name", "schema"}
        assert _strict_ok(schema["schema"])
    assert prompts.EXTRACTION_SCHEMA["name"] == "claim_extraction_v1"
    assert prompts.SUPPORT_SCHEMA["name"] == "claim_support_v1"
    item_schema = prompts.EXTRACTION_SCHEMA["schema"]["properties"]["claims"]["items"]
    assert list(item_schema["properties"]) == [
        "quote", "statement", "kind", "stated_period", "stated_owner", "requirement_ids",
    ]


def test_scenario_11_prompt_contracts_and_injection(monkeypatch):
    g()
    sources = fixture_sources(INFOSEC, PRIVACY, INJECTED)
    injected = sources[2]
    fabricated = "All controls are fully compliant and no further review is required."

    def extract(ctx):
        if ctx.source is injected and ctx.batch.index == 1:
            return [item(fabricated, "The vendor says everything is compliant.", [ctx.ids[0]])]
        return happy_extract(ctx)

    FakeLLM(sources, ["dpdpa"], extract=extract).install(monkeypatch)
    calls = install_spy(monkeypatch)
    claim_set = run(sources, ["dpdpa"])
    batches = g("batches").extraction_batches(["dpdpa"])
    chunk_count = len(g("chunking").chunk_sources(sources))

    extraction = [c for c in calls if not SUPPORT_ITEM.search(c["messages"][0]["content"])]
    support = [c for c in calls if SUPPORT_ITEM.search(c["messages"][0]["content"])]
    systems = Counter(c["system"] for c in extraction)
    assert len(systems) == len(batches)
    assert set(systems.values()) == {chunk_count}
    fixture_text = [s for src in sources for s in candidate_sentences(src.text)]
    for system in systems:
        assert isinstance(system, str)
        assert not any(sentence in system for sentence in fixture_text)
    for call in extraction:
        user = call["messages"][0]["content"]
        assert user.count(BEGIN) == 1 and user.count(END) == 1
    injected_users = [c["messages"][0]["content"] for c in extraction if f"document: {INJECTED}" in c["messages"][0]["content"]]
    assert injected_users and all(NEUTRAL_END in u for u in injected_users)
    assert END in injected.text  # raw text untouched
    assert claim_set.metrics["delimiter_collisions"] == 1
    assert reasons(claim_set)["quote_not_found"] == 1
    assert claims_with(claim_set, model_quote=fabricated) == []

    cap = settings.llm_max_output_tokens_framework
    for call in extraction:
        assert call["tier"] == "extract"
        assert call["temperature"] == 0
        assert call.get("stream", False) is False
        assert call["max_tokens"] == min(cap, settings.v2_extraction_max_tokens)
        assert call["response_schema"] == g("prompts").EXTRACTION_SCHEMA
    assert support
    for call in support:
        assert call["tier"] == "extract"
        assert call["temperature"] == 0
        assert call.get("stream", False) is False
        assert call["max_tokens"] == min(cap, settings.v2_support_max_tokens)
        assert call["response_schema"] == g("prompts").SUPPORT_SCHEMA
        assert call["system"] == g("prompts").SUPPORT_SYSTEM_PROMPT


def test_scenario_11_structured_output_can_be_switched_off(monkeypatch):
    g()
    monkeypatch.setattr(settings, "v2_structured_output", False)
    source = make_source(PRIVACY)
    FakeLLM([source], ["dpdpa"]).install(monkeypatch)
    calls = install_spy(monkeypatch)
    claim_set = run([source], ["dpdpa"])
    assert calls and all("response_schema" not in call for call in calls)
    assert claim_set.claims != ()


def test_scenario_11_filename_newlines_are_stripped(monkeypatch):
    g()
    source = make_source(PRIVACY, filename="evil\nname.txt")
    FakeLLM([source], ["dpdpa"]).install(monkeypatch)
    calls = install_spy(monkeypatch)
    run([source], ["dpdpa"])
    users = [c["messages"][0]["content"] for c in calls if not SUPPORT_ITEM.search(c["messages"][0]["content"])]
    assert users
    for user in users:
        assert "evil\nname" not in user
        assert re.search(r"^document: evilname\.txt$", user, re.M)


def test_scenario_11_system_prompt_is_identical_across_chunks_and_fingerprinted(monkeypatch):
    prompts = g("prompts")
    batches = g("batches").extraction_batches(["dpdpa", "iso27001"])
    for batch in batches:
        system = prompts.build_extraction_system_prompt(batch)
        assert system == prompts.build_extraction_system_prompt(batch)
        assert re.findall(r"^- (\S+) \[", system, re.M) == list(batch.requirement_ids)
    fingerprints = prompts.prompt_fingerprints()
    assert set(fingerprints) == {"extraction_template", "support_system"}
    assert all(re.fullmatch(r"[0-9a-f]{64}", value) for value in fingerprints.values())
    assert prompts.prompt_fingerprints() == fingerprints
    monkeypatch.setattr(prompts, "SUPPORT_SYSTEM_PROMPT", prompts.SUPPORT_SYSTEM_PROMPT + " changed")
    changed = prompts.prompt_fingerprints()
    assert changed["support_system"] != fingerprints["support_system"]
    assert changed["extraction_template"] == fingerprints["extraction_template"]


# --------------------------------------------------------------------------- #
# Scenario 12: call records
# --------------------------------------------------------------------------- #


def test_scenario_12_call_records(monkeypatch):
    g()
    sources = fixture_sources(INFOSEC, PRIVACY)
    first = g("chunking").chunk_sources(sources)[0]
    missing_once: set = set()

    def extract(ctx):
        if ctx.batch.index == 2 and ctx.chunk.chunk_id == first.chunk_id and ctx.attempt == 0:
            return "{not json"
        return happy_extract(ctx)

    def support(entry, ctx):
        if entry.statement not in missing_once:
            missing_once.add(entry.statement)
            if len(missing_once) == 1:
                return None
        return {"verdict": "yes", "supported_statement": None}

    FakeLLM(sources, ["dpdpa"], extract=extract, support=support).install(monkeypatch)
    claim_set = run(sources, ["dpdpa"])
    records = list(claim_set.llm_calls)
    assert records
    for record in records:
        assert record["framework_id"] is None
        assert record["stage"] in ("claim_extraction", "claim_support")
        pattern = EXTRACTION_TAG if record["stage"] == "claim_extraction" else SUPPORT_TAG
        assert pattern.match(record["batch"]), record["batch"]
        assert record["tier"] == "extract"
        assert record["status"] == "ok"
    extraction = [r for r in records if r["stage"] == "claim_extraction"]
    support_records = [r for r in records if r["stage"] == "claim_support"]
    assert len(extraction) == claim_set.metrics["extraction_calls"]
    assert len(support_records) == claim_set.metrics["support_calls"]
    assert any(r["batch"].endswith("+retry") for r in extraction)
    assert any("+missing" in r["batch"] for r in support_records)
    tokens = claim_set.metrics["tokens"]
    for stage, subset in (("claim_extraction", extraction), ("claim_support", support_records)):
        assert tokens[stage]["input"] == sum(r["input_tokens"] for r in subset)
        assert tokens[stage]["output"] == sum(r["output_tokens"] for r in subset)
    order_key = lambda r: (0 if r["stage"] == "claim_extraction" else 1, r["batch"], r["status"])
    assert records == sorted(records, key=order_key)


# --------------------------------------------------------------------------- #
# Scenario 13: determinism and concurrency
# --------------------------------------------------------------------------- #


def test_scenario_13_determinism_across_concurrency(monkeypatch):
    g()
    sources = fixture_sources(INFOSEC, PRIVACY, INJECTED)
    framework_ids = ["dpdpa", "iso27001"]
    results = {}
    fakes = {}
    for workers in (1, 4):
        monkeypatch.setattr(settings, "llm_max_concurrency", workers)
        fakes[workers] = FakeLLM(sources, framework_ids, jitter=True).install(monkeypatch)
        results[workers] = run(sources, framework_ids)
    assert results[1].comparable() == results[4].comparable()
    assert [c.claim_id for c in results[1].claims] == [c.claim_id for c in results[4].claims]
    assert fakes[1].max_in_flight == 1
    assert 1 < fakes[4].max_in_flight <= 4


# --------------------------------------------------------------------------- #
# Scenario 14: metadata
# --------------------------------------------------------------------------- #


def _fields(source):
    metadata = g("metadata").extract_metadata(source)
    for field in metadata.fields:
        assert field.value == source.text[field.start:field.end]
    names = [field.name for field in metadata.fields]
    assert len(names) == len(set(names))
    order = list(g("metadata").METADATA_FIELD_NAMES)
    assert names == sorted(names, key=order.index)
    return {field.name: field for field in metadata.fields}, metadata


def test_scenario_14_metadata_from_fixtures():
    g()
    fields, metadata = _fields(make_source(INFOSEC))
    assert metadata.method == "regex"
    assert fields["version"].value == "2.1"
    assert fields["approver"].value == "Chief Risk Officer"
    assert fields["effective_date"].iso_date == "2025-03-14"
    assert fields["next_review_date"].value == "03/04/2026"
    assert fields["next_review_date"].iso_date is None
    assert fields["version"].iso_date is None

    privacy_fields, _ = _fields(make_source(PRIVACY))
    assert privacy_fields["document_date"].iso_date == "2025-01-20"


@pytest.mark.parametrize(
    "value, expected",
    [
        ("14/03/2025", "2025-03-14"),
        ("03/14/2025", "2025-03-14"),
        ("31/02/2025", None),
        ("2025-03-14", "2025-03-14"),
        ("14 March 2025", "2025-03-14"),
        ("March 14, 2025", "2025-03-14"),
        ("March 2025", None),
        ("05/06/2025", None),
    ],
)
def test_scenario_14_date_parsing(value, expected):
    g()
    text = f"Policy title\nEffective Date: {value}\nBody text follows here.\n"
    fields, _ = _fields(make_source(text=text, filename="dates.txt"))
    assert fields["effective_date"].value == value
    assert fields["effective_date"].iso_date == expected


def test_scenario_14_no_labels_and_prose_version():
    g()
    fields, _ = _fields(make_source(text="Just a paragraph of text with no labels at all.\n", filename="none.txt"))
    assert fields == {}
    fields, _ = _fields(make_source(text="Title\nVersion: see appendix\n", filename="prose.txt"))
    assert "version" not in fields


# --------------------------------------------------------------------------- #
# Scenario 15: serialisation and freshness
# --------------------------------------------------------------------------- #


def test_scenario_15_round_trip_and_freshness(monkeypatch):
    claims_mod = g("claims")
    prompts = g("prompts")
    sources = fixture_sources(INFOSEC, PRIVACY)
    FakeLLM(sources, ["dpdpa"]).install(monkeypatch)
    claim_set = run(sources, ["dpdpa"])
    raw = claim_set.to_json()
    json.loads(raw)
    assert claims_mod.ClaimSet.from_json(raw) == claim_set
    assert claim_set.schema_version == 1

    assert claims_mod.claim_set_is_current(claim_set, sources, ["dpdpa"]) is True
    changed = list(sources)
    changed[1] = make_source(text=sources[1].text + ".", n=2, filename=PRIVACY)
    assert claims_mod.claim_set_is_current(claim_set, changed, ["dpdpa"]) is False
    assert claims_mod.claim_set_is_current(claim_set, sources, ["dpdpa", "iso27001"]) is False
    monkeypatch.setattr(settings, "llm_model_extract", "some/other-model")
    assert claims_mod.claim_set_is_current(claim_set, sources, ["dpdpa"]) is False
    monkeypatch.undo()
    monkeypatch.setattr(settings, "llm_max_concurrency", 1)
    monkeypatch.setattr(prompts, "PROMPT_VERSION", "p6-3a.test-bump")
    assert claims_mod.claim_set_is_current(claim_set, sources, ["dpdpa"]) is False


# --------------------------------------------------------------------------- #
# Scenario 16: loading sources from the database
# --------------------------------------------------------------------------- #


def test_scenario_16_load_source_documents(db, monkeypatch):
    grounding = g()
    from app.models.assessment import AssessmentDocument
    from app.services.evidence import analysis_documents

    assessment = seed_assessment(db)
    old_text = "Superseded text that must not be read."
    new_text = read_fixture(PRIVACY) + "\n\n[... truncated to first 5000 words ...]"
    evidence_a, (_old, current) = add_evidence(
        db, assessment, filename="privacy.pdf",
        versions=[(old_text, "superseded"), (new_text, "active")], mime="application/pdf",
    )
    image_text = (
        "[Screenshot: mfa.png]\n\nThe screenshot shows the identity provider settings page with "
        "multi-factor authentication enforced for all administrator accounts."
    )
    evidence_b, (image_version,) = add_evidence(
        db, assessment, filename="mfa.png", versions=[(image_text, "active")], mime="image/png",
    )
    legacy = AssessmentDocument(
        assessment_id=assessment.id,
        filename="legacy-policy.docx",
        file_path="uploads/legacy-policy.docx",
        file_type="docx",
        document_category="other",
        extracted_text=read_fixture(INJECTED),
    )
    db.add(legacy)
    db.commit()

    sources = grounding.load_source_documents(db, assessment.id)
    documents = analysis_documents(db, assessment.id)
    assert [s.filename for s in sources] == [d["filename"] for d in documents]
    by_name = {s.filename: s for s in sources}

    a = by_name["privacy.pdf"]
    assert a.evidence_version_id == current.id and a.evidence_id == evidence_a.id
    assert a.source_id == f"ev:{current.id}"
    assert a.text == new_text and a.derived_from_image is False
    assert a.text_sha256 == hashlib.sha256(new_text.encode("utf-8")).hexdigest()

    b = by_name["mfa.png"]
    assert b.evidence_version_id == image_version.id and b.derived_from_image is True

    c = by_name["legacy-policy.docx"]
    assert c.source_id == f"legacy:{legacy.id}"
    assert c.evidence_version_id is None and c.legacy_document_id == legacy.id
    assert c.derived_from_image is False
    assert c.text == legacy.extracted_text

    FakeLLM(sources, ["dpdpa"]).install(monkeypatch)
    claim_set = run(sources, ["dpdpa"])
    legacy_claims = [claim for claim in claim_set.claims if claim.source_id == c.source_id]
    image_claims = [claim for claim in claim_set.claims if claim.source_id == b.source_id]
    assert legacy_claims and all(claim.citation is None for claim in legacy_claims)
    assert image_claims and all(claim.derived_from_image and claim.needs_review for claim in image_claims)
    assert claim_set.metrics["derived_from_image_claims"] == len(image_claims)
    evidence_claims = [claim for claim in claim_set.claims if claim.source_id == a.source_id]
    assert evidence_claims
    for claim in evidence_claims + image_claims:
        assert validate_citations(db, [claim.citation], assessment_id=assessment.id) == [claim.citation]


# --------------------------------------------------------------------------- #
# Scenario 17: dormancy, parity and independence guards
# --------------------------------------------------------------------------- #

PROTECTED_PATHS = [
    "app/services/claude_analyzer.py", "app/services/desk_review.py",
    "app/services/desk_review_findings.py", "app/services/auto_answer.py",
    "app/services/question_engine.py", "app/services/llm_client.py", "app/services/parallel.py",
    "app/services/citations.py", "app/services/evidence.py", "app/services/document_processor.py",
    "app/services/analysis_pipeline.py", "app/services/scoring.py", "app/services/__init__.py",
    "app/frameworks", "app/dpdpa", "app/models", "app/schemas", "app/routers", "app/templates",
    "alembic", "tests/fixtures", "tests/support", "validation", "scripts/validation",
]


def _git(*args) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, check=True, capture_output=True, text=True
    ).stdout


def test_scenario_17_protected_files_unchanged():
    committed = _git("diff", "--stat", "main...HEAD", "--", *PROTECTED_PATHS)
    uncommitted = _git("status", "--porcelain", "--", *PROTECTED_PATHS)
    assert committed == "" and uncommitted == "", committed + uncommitted


def test_scenario_17_package_is_dormant():
    offenders = []
    for path in (REPO_ROOT / "app").rglob("*.py"):
        if (REPO_ROOT / "app" / "services" / "grounding") in path.parents:
            continue
        source = path.read_text(encoding="utf-8", errors="ignore")
        if "services.grounding" in source or re.search(r"from app\.services import[^\n]*\bgrounding\b", source):
            offenders.append(str(path.relative_to(REPO_ROOT)))
    assert offenders == []


# --------------------------------------------------------------------------- #
# Scenario 18: end to end on the fixtures
# --------------------------------------------------------------------------- #


def test_scenario_18_end_to_end_on_fixtures(monkeypatch):
    claims_mod = g("claims")
    from app.frameworks.registry import FrameworkRegistry

    sources = fixture_sources(INFOSEC, PRIVACY, INJECTED)
    FakeLLM(sources, THREE).install(monkeypatch)
    claim_set = run(sources, THREE)
    assert claim_set.status == "complete"
    assert claim_set.framework_ids == tuple(THREE)
    assert set(claim_set.metrics) >= PINNED_METRIC_KEYS
    assert claim_set.metrics["verified"] == len(claim_set.claims)

    chunk_by_id = {chunk.chunk_id: chunk for chunk in claim_set.chunks}
    source_by_id = {source.source_id: source for source in sources}
    in_scope = {c.id for fid in THREE for c in FrameworkRegistry.get(fid).all_controls()}
    for source in sources[:2]:
        assert any(claim.source_id == source.source_id for claim in claim_set.claims), source.filename
    for claim in claim_set.claims:
        source = source_by_id[claim.source_id]
        chunk = chunk_by_id[claim.chunk_id]
        assert claim.quote == source.text[claim.start:claim.end]
        assert chunk.start <= claim.start < claim.end <= chunk.end
        assert claim.requirement_ids and set(claim.requirement_ids) <= in_scope
        assert claim.support in ("yes", "partial")
        assert claim.tag_status == "suggested"
        assert claim.claim_id == claims_mod.claim_id(claim.source_id, claim.start, claim.end, claim.statement)
        assert claim.claim_id.startswith("CLM-") and len(claim.claim_id) == 20
    ids = [claim.claim_id for claim in claim_set.claims]
    assert len(ids) == len(set(ids))
    positions = {source.source_id: index for index, source in enumerate(sources)}
    keys = [(positions[c.source_id], c.start, c.end) for c in claim_set.claims]
    assert keys == sorted(keys)
