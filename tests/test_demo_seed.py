"""Lean contract test for the Veldhara walkthrough seed."""

from __future__ import annotations

import json
import os
import re
import sqlite3
import subprocess
import sys
import uuid
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SEED = REPO_ROOT / "scripts" / "demo" / "seed_demo.py"
CLIENT_NAME = "Veldhara Logistics Pvt Ltd."


def _run_seed(db_path: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["OPENROUTER_KEY"] = ""
    return subprocess.run(
        [sys.executable, str(SEED), "--db", str(db_path)],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )


def test_demo_seed_contract_and_idempotence(tmp_path: Path) -> None:
    db_path = tmp_path / "demo.db"
    developer_db = REPO_ROOT / "data" / "dpdpa.db"
    developer_mtime = developer_db.stat().st_mtime_ns if developer_db.exists() else None

    first = _run_seed(db_path)
    assert first.returncode == 0, first.stdout + first.stderr
    assert "Manifest:" in first.stdout
    assert "URLs:" in first.stdout
    assert "Skipped:" in first.stdout

    with sqlite3.connect(db_path) as db:
        client = db.execute(
            "SELECT id FROM clients WHERE name = ?", (CLIENT_NAME,)
        ).fetchone()
        assert client is not None
        client_id = client[0]
        assessments = db.execute(
            "SELECT id, description, selected_frameworks FROM assessments "
            "WHERE company_name = ? ORDER BY created_at",
            (CLIENT_NAME,),
        ).fetchall()
        assert len(assessments) == 4
        by_description = {row[1]: (row[0], json.loads(row[2])) for row in assessments}
        prior_id, prior_frameworks = by_description[
            "FY2025-26 baseline (DPDPA + ISO 27001)"
        ]
        current_id, current_frameworks = by_description[
            "FY2026-27 reassessment (DPDPA + ISO 27001)"
        ]
        scope, applicable = db.execute("SELECT scope_answers, applicable_requirements FROM assessments WHERE id = ?", (current_id,)).fetchone()
        assert json.loads(scope)["ISO.SCP.3"] == "both"
        assert len(json.loads(applicable)) == 99
        raw_basis, = db.execute("SELECT metadata_json FROM audit_events WHERE entity_id = ? AND action = 'assessment.report_basis_updated' ORDER BY created_at DESC LIMIT 1", (current_id,)).fetchone()
        basis = json.loads(raw_basis)["after"]
        assert basis["period_start"] == "2026-07-01"
        assert basis["period_end"] == "2026-09-30"
        assert basis["evidence_cutoff"] == "2026-10-05"
        interim_id, interim_frameworks = by_description["Interim ISO 27001 check"]
        nist_id, nist_frameworks = by_description["NIST CSF 2.0 baseline"]
        assert prior_frameworks == current_frameworks == ["dpdpa", "iso27001"]
        assert interim_frameworks == ["iso27001"]
        assert nist_frameworks == ["nist_csf"]

        prior_conclusions = db.execute(
            "SELECT id FROM conclusions WHERE assessment_id = ?", (prior_id,)
        ).fetchall()
        assert len(prior_conclusions) == 15
        assert db.execute(
            "SELECT COUNT(*) FROM conclusion_revisions "
            "WHERE action = 'approved' AND conclusion_id IN "
            "(SELECT id FROM conclusions WHERE assessment_id = ?)",
            (prior_id,),
        ).fetchone()[0] == 15
        assert db.execute(
            "SELECT COUNT(*) FROM audit_events WHERE action = 'assessment.released' "
            "AND entity_id = ?", (prior_id,)
        ).fetchone()[0] == 1

        current_conclusions = db.execute(
            "SELECT id, outcome FROM conclusions WHERE assessment_id = ?", (current_id,)
        ).fetchall()
        assert len(current_conclusions) == 99
        assert sum(outcome == "not_applicable" for _, outcome in current_conclusions) == 1
        assert db.execute(
            "SELECT COUNT(*) FROM conclusion_revisions "
            "WHERE action = 'approved' AND conclusion_id IN "
            "(SELECT id FROM conclusions WHERE assessment_id = ?)",
            (current_id,),
        ).fetchone()[0] == 99
        assert db.execute(
            "SELECT COUNT(*) FROM findings WHERE assessment_id = ?", (current_id,)
        ).fetchone()[0] == 6
        assert db.execute(
            "SELECT COUNT(*) FROM report_snapshots WHERE assessment_id = ? "
            "AND is_issued = 1", (current_id,)
        ).fetchone()[0] >= 1

        mapped = db.execute("SELECT v.original_filename, u.relevance FROM evidence_uses u JOIN evidence e ON e.id = u.evidence_id JOIN evidence_versions v ON v.evidence_id = e.id WHERE u.assessment_id = ? AND u.requirement_id = 'ISO.A5.18'", (current_id,)).fetchall()
        assert ("Veldhara_Access_Review_Q2_FY26.docx", "primary") in mapped
        assert ("Veldhara_User_Access_Review_Export.xlsx", "supporting") in mapped
        access_text, = db.execute("SELECT v.extracted_text FROM evidence_versions v JOIN evidence e ON e.id = v.evidence_id WHERE e.assessment_id = ? AND v.original_filename = 'Veldhara_User_Access_Review_Export.xlsx'", (current_id,)).fetchone()
        assert len(set(re.findall(r"VH-\d{4}", access_text))) == 220
        assert "VH-0220" in access_text
        assert db.execute("SELECT count(*) FROM evidence_uses u JOIN evidence e ON e.id = u.evidence_id JOIN evidence_versions v ON v.evidence_id = e.id WHERE u.assessment_id = ? AND v.original_filename LIKE '%Dec_2023%'", (current_id,)).fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM evidence_versions v JOIN evidence e ON e.id = v.evidence_id WHERE e.assessment_id = ? AND v.original_filename NOT IN ('Veldhara_ISMS_Baseline_Operating_Log_2025.docx', 'Veldhara_Access_Review_Dec_2023.docx')", (prior_id,)).fetchone()[0] == 0
        for raw_citations, in db.execute("SELECT r.citations_json FROM conclusion_revisions r JOIN conclusions c ON c.id = r.conclusion_id WHERE c.assessment_id = ? AND r.action = 'proposed'", (current_id,)):
            citations = json.loads(raw_citations)
            for citation in citations:
                text, = db.execute("SELECT extracted_text FROM evidence_versions WHERE id = ?", (citation["evidence_version_id"],)).fetchone()
                start, end = map(int, citation["location_ref"].removeprefix("chars:").split("-"))
                assert text[start:end] == citation["excerpt"]

        interim_conclusions = db.execute(
            "SELECT id FROM conclusions WHERE assessment_id = ?", (interim_id,)
        ).fetchall()
        assert len(interim_conclusions) == 6
        assert db.execute(
            "SELECT COUNT(*) FROM conclusion_revisions "
            "WHERE action = 'approved' AND conclusion_id IN "
            "(SELECT id FROM conclusions WHERE assessment_id = ?)",
            (interim_id,),
        ).fetchone()[0] == 3
        assert db.execute(
            "SELECT COUNT(*) FROM audit_events WHERE action = 'assessment.released' "
            "AND entity_id = ?", (interim_id,)
        ).fetchone()[0] == 0

        assert db.execute(
            "SELECT COUNT(*) FROM conclusions WHERE assessment_id = ?", (nist_id,)
        ).fetchone()[0] == 0
        nist_total = db.execute(
            "SELECT COUNT(*) FROM questionnaire_responses WHERE assessment_id = ?",
            (nist_id,),
        ).fetchone()[0]
        assert nist_total > 0
        assert 0.2 <= nist_total / 106 <= 0.8
        assert db.execute(
            "SELECT COUNT(*) FROM evidence WHERE assessment_id = ?", (nist_id,)
        ).fetchone()[0] == 2

        assert db.execute(
            "SELECT COUNT(*) FROM evidence_versions v JOIN evidence e ON e.id = v.evidence_id "
            "WHERE e.engagement_id = ? AND COALESCE(TRIM(v.extracted_text), '') = ''",
            (db.execute(
                "SELECT id FROM engagements WHERE client_id = ? ORDER BY created_at LIMIT 1",
                (client_id,),
            ).fetchone()[0],),
        ).fetchone()[0] == 0
        answer_sources = {
            row[0]
            for row in db.execute(
                "SELECT DISTINCT answer_source FROM questionnaire_responses "
                "WHERE assessment_id IN (SELECT id FROM assessments WHERE company_name = ?)",
                (CLIENT_NAME,),
            ).fetchall()
        }
        assert answer_sources <= {
            None,
            "human",
            "human_override",
            "document",
            "document_confirmed",
            "inferred",
        }

        followup_count = db.execute(
            "SELECT COUNT(*) FROM questionnaire_responses "
            "WHERE assessment_id = ? AND question_id LIKE 'FU.%'",
            (current_id,),
        ).fetchone()[0]
        if "follow-ups skipped: needs S0b" not in first.stdout:
            assert followup_count == 2
            from scripts.demo.pack import register_frameworks
            from app.frameworks.questionnaire_builder import build_multi_questionnaire, compute_excluded_controls

            register_frameworks()
            questions = build_multi_questionnaire(current_frameworks, compute_excluded_controls(current_frameworks, applicable))
            controls_by_parent = {question["cluster_id"]: {member["control_id"] for member in question["controls"]} for question in questions}
            followups = db.execute("SELECT question_id, notes FROM questionnaire_responses WHERE assessment_id = ? AND question_id LIKE 'FU.%'", (current_id,)).fetchall()
            covered = [controls_by_parent[question_id.removeprefix("FU.").rsplit(".", 1)[0]] for question_id, _ in followups]
            assert any("CH2.CONSENT.3" in ids for ids in covered)
            assert any("ISO.A5.19" in ids for ids in covered)
            assert all(notes and "question" in notes.lower() for _, notes in followups)

        unrelated_id = str(uuid.uuid4())
        db.execute(
            "INSERT INTO clients (id, name, industry, size, retention_years, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            (unrelated_id, "Unrelated Demo Client", "other", "small", 7),
        )
        db.commit()

    second = _run_seed(db_path)
    assert second.returncode == 0, second.stdout + second.stderr
    with sqlite3.connect(db_path) as db:
        assert db.execute(
            "SELECT COUNT(*) FROM clients WHERE name = ?", (CLIENT_NAME,)
        ).fetchone()[0] == 1
        assert db.execute(
            "SELECT COUNT(*) FROM assessments WHERE company_name = ?", (CLIENT_NAME,)
        ).fetchone()[0] == 4
        assert db.execute(
            "SELECT COUNT(*) FROM clients WHERE id = ?", (unrelated_id,)
        ).fetchone()[0] == 1

    current_mtime = developer_db.stat().st_mtime_ns if developer_db.exists() else None
    assert current_mtime == developer_mtime
