"""Opt-in contract tests for the P4-3 performance benchmark."""

from __future__ import annotations

import json
import os
from pathlib import Path
from statistics import median

import pytest
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.main import _register_frameworks
from app.models.analysis_run import AnalysisRun
from app.models.assessment import Assessment
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.evidence import Evidence, EvidenceVersion
from app.models.finding import Finding
from app.models.report import GapReport
from app.services import conclusion_review
from app.services.citations import resolve_citations
from scripts.benchmark_performance import (
    PLAN_COUNTS,
    THRESHOLD_SECONDS,
    benchmark_client,
    build_database,
    format_table,
    main,
    run_benchmarks,
    search_engagement_evidence,
    seed_benchmark_dataset,
)


pytestmark = pytest.mark.skipif(
    os.environ.get("CYBERASSESS_RUN_BENCHMARKS") != "1",
    reason="set CYBERASSESS_RUN_BENCHMARKS=1 to run the P4-3 benchmarks",
)

_BENCH_ENGINE = None


@pytest.fixture(scope="module")
def bench(tmp_path_factory):
    global _BENCH_ENGINE
    root = tmp_path_factory.mktemp("p4-3-performance")
    db_path = root / "benchmark.sqlite3"
    upload_dir = root / "uploads"
    upload_dir.mkdir()
    _register_frameworks()

    with pytest.MonkeyPatch.context() as monkeypatch:
        url, engine = build_database(db_path)
        monkeypatch.setattr(settings, "database_url", url)
        monkeypatch.setattr(settings, "upload_dir", str(upload_dir))
        _BENCH_ENGINE = engine
        try:
            handle = seed_benchmark_dataset(engine)
            results = run_benchmarks(url, engine, handle)
            (root / "benchmark-results.json").write_text(
                json.dumps(results, indent=2, sort_keys=True) + "\n"
            )
            print(format_table(results))
            yield handle, results
        finally:
            engine.dispose()
            _BENCH_ENGINE = None


def _db():
    return sessionmaker(bind=_BENCH_ENGINE)()


def _operation(results, name):
    return next(operation for operation in results["operations"] if operation["name"] == name)


def test_seed_counts_and_a0_shape(bench):
    handle, _results = bench
    assert all(handle.counts[key] == value for key, value in PLAN_COUNTS.items())

    db = _db()
    try:
        a0 = db.get(Assessment, handle.a0_id)
        conclusions = (
            db.query(Conclusion).filter(Conclusion.assessment_id == handle.a0_id).all()
        )
        assert len(conclusions) == 228
        assert {conclusion.framework_id for conclusion in conclusions} == {
            "dpdpa",
            "iso27001",
            "nist_csf",
        }
        assert (
            db.query(ConclusionRevision)
            .join(Conclusion, Conclusion.id == ConclusionRevision.conclusion_id)
            .filter(Conclusion.assessment_id == handle.a0_id)
            .count()
            == 1083
        )
        assert (
            db.query(AnalysisRun)
            .filter_by(assessment_id=handle.a0_id)
            .count()
            == 12
        )
        assert (
            db.query(Assessment).filter(Assessment.id == handle.a0_id).one().review_status
            == "approved"
        )
        assert db.query(Assessment).filter(Assessment.id == handle.a0_id).count() == 1
        assert (
            db.query(GapReport).filter(GapReport.assessment_id == handle.a0_id).count()
            == 1
        )
        history = json.loads(
            db.query(GapReport)
            .filter(GapReport.assessment_id == handle.a0_id)
            .one()
            .legacy_history
        )
        assert len(history) == 3
        assert db.query(Conclusion).filter(Conclusion.assessment_id == a0.id).count() == 228
        assert db.query(ConclusionRevision).count() == 3000
    finally:
        db.close()


def test_a0_product_shapes(bench):
    handle, _results = bench
    db = _db()
    try:
        proposed = (
            db.query(ConclusionRevision)
            .join(Conclusion, Conclusion.id == ConclusionRevision.conclusion_id)
            .filter(
                Conclusion.assessment_id == handle.a0_id,
                ConclusionRevision.action == "proposed",
            )
            .all()
        )
        cited_revision = next(
            revision
            for revision in proposed
            if json.loads(revision.citations_json or "[]")
        )
        citations = json.loads(cited_revision.citations_json)
        assert any(citation["location_type"] == "text_span" for citation in citations)
        resolved = resolve_citations(db, cited_revision.citations_json)
        assert any(
            citation["resolved"]
            and citation["is_current"]
            and db.get(Evidence, citation["evidence_id"]).engagement_id
            for citation in resolved
        )
        assert (
            db.query(ConclusionRevision)
            .join(Conclusion, Conclusion.id == ConclusionRevision.conclusion_id)
            .filter(
                Conclusion.assessment_id == handle.a0_id,
                ConclusionRevision.action == "proposal_withheld",
            )
            .count()
            > 0
        )
        cards = conclusion_review.conclusion_cards(db, handle.a0_id)
        expected_findings = sum(
            card.state in ("approved", "edited")
            and card.conclusion.outcome in conclusion_review.GAP_OUTCOMES
            for card in cards
        )
        assert (
            db.query(Finding).filter(Finding.assessment_id == handle.a0_id).count()
            == expected_findings
        )
        assert (
            db.query(EvidenceVersion).filter(EvidenceVersion.status == "active").count()
            == 250
        )
        assert (
            db.query(EvidenceVersion)
            .filter(EvidenceVersion.status == "superseded")
            .count()
            == 250
        )
    finally:
        db.close()


def test_dashboard_operation(bench):
    handle, results = bench
    assert _operation(results, "portfolio_dashboard")["status_code"] == 200
    assert _operation(results, "portfolio_dashboard")["passed"]
    with benchmark_client(settings.database_url, _BENCH_ENGINE) as client:
        body = client.get("/").text
    for client_number in range(1, 6):
        assert f"Benchmark Client {client_number}" in body


def test_workpaper_operation(bench):
    handle, results = bench
    assert _operation(results, "workpaper_3_framework")["status_code"] == 200
    assert _operation(results, "workpaper_3_framework")["passed"]
    with benchmark_client(settings.database_url, _BENCH_ENGINE) as client:
        body = client.get(f"/assessments/{handle.a0_id}/workpaper").text
    for anchor in (
        "wp-dpdpa-CH2.CONSENT.1",
        "wp-iso27001-ISO.A5.1",
        "wp-nist_csf-NIST.GV.OC.01",
    ):
        assert anchor in body


def test_report_operation(bench):
    handle, results = bench
    operation = _operation(results, "gap_report_pdf_3_framework")
    assert operation["status_code"] == 200
    assert operation["passed"]
    with benchmark_client(settings.database_url, _BENCH_ENGINE) as client:
        response = client.get(f"/api/assessments/{handle.a0_id}/report/pdf")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content.startswith(b"%PDF")


def test_evidence_search_operation(bench):
    handle, results = bench
    assert _operation(results, "evidence_search_engagement")["passed"]
    db = _db()
    try:
        rows = search_engagement_evidence(db, handle.e0_id, "retention schedule")
        assert len(rows) == 70
        assert all(
            evidence.engagement_id == handle.e0_id and version.status == "active"
            for evidence, version in rows
        )
        assert search_engagement_evidence(db, handle.e0_id, "zz-no-such-term") == []
    finally:
        db.close()


def test_results_json_contract(bench):
    _handle, results = bench
    assert set(results) == {
        "threshold_seconds",
        "environment",
        "seed_seconds",
        "counts",
        "operations",
    }
    assert results["threshold_seconds"] == THRESHOLD_SECONDS
    assert [operation["name"] for operation in results["operations"]] == [
        "portfolio_dashboard",
        "workpaper_3_framework",
        "gap_report_pdf_3_framework",
        "evidence_search_engagement",
    ]
    expected_operation_keys = {
        "name",
        "target",
        "status_code",
        "bytes",
        "runs_seconds",
        "median_seconds",
        "max_seconds",
        "statements",
        "breakdown",
        "passed",
    }
    for operation in results["operations"]:
        assert set(operation) == expected_operation_keys
        assert len(operation["runs_seconds"]) == 5
        assert operation["median_seconds"] == pytest.approx(median(operation["runs_seconds"]))


def test_benchmark_uses_isolated_database(bench):
    _handle, _results = bench
    benchmark_path = Path(settings.database_url.removeprefix("sqlite:///"))
    assert benchmark_path.is_file()
    assert benchmark_path.parent.name.startswith("p4-3-performance")


def test_cli_refuses_existing_database(tmp_path):
    existing = tmp_path / "already-exists.sqlite3"
    contents = b"keep this file unchanged"
    existing.write_bytes(contents)
    assert main(["--db", str(existing)]) == 2
    assert existing.read_bytes() == contents
