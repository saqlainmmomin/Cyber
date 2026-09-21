"""PW-1: Verify questionnaire_responses rebuild preserves cluster_id and answer_source."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import create_engine, text

from app.main import _ensure_questionnaire_answer_constraint


def test_rebuild_preserves_cluster_id_and_answer_source(tmp_path):
    db_path = tmp_path / "rebuild.db"
    engine = create_engine(f"sqlite:///{db_path}")

    with engine.connect() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE questionnaire_responses (
                    id VARCHAR(36) NOT NULL PRIMARY KEY,
                    assessment_id VARCHAR(36) NOT NULL,
                    question_id VARCHAR(50) NOT NULL,
                    answer VARCHAR(20) NOT NULL,
                    notes TEXT,
                    evidence_reference TEXT,
                    na_reason TEXT,
                    confidence TEXT,
                    cluster_id VARCHAR(80),
                    answer_source VARCHAR(20) DEFAULT 'human',
                    submitted_at DATETIME NOT NULL
                )
                """
            )
        )
        row_id = str(uuid.uuid4())
        conn.execute(
            text(
                """
                INSERT INTO questionnaire_responses
                    (id, assessment_id, question_id, answer, cluster_id, answer_source, submitted_at)
                VALUES (:id, :aid, :qid, :answer, :cid, :src, :ts)
                """
            ),
            {
                "id": row_id,
                "aid": "assess-1",
                "qid": "q-1",
                "answer": "fully_implemented",
                "cid": "UCC.01",
                "src": "document",
                "ts": datetime.now(timezone.utc).isoformat(),
            },
        )
        conn.commit()

        _ensure_questionnaire_answer_constraint(conn)
        conn.commit()

        row = conn.execute(
            text("SELECT cluster_id, answer_source FROM questionnaire_responses WHERE id = :id"),
            {"id": row_id},
        ).fetchone()

    engine.dispose()

    assert row is not None
    assert row[0] == "UCC.01"
    assert row[1] == "document"
