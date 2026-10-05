"""Focused route and registry checks for the S8 Requests/RFI previews."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.config import settings
from app.database import get_db
from app.main import app
from app.models.assessment import Assessment
from design.harness.seed_s8 import screen_states, seed_s8


def test_s8_requests_and_rfi_states_are_registered():
    states = screen_states()
    assert states["b6-magic_links"] == ("default", "empty", "error", "loading", "newlink", "revoke")
    assert states["b6-rfi"] == ("default", "error", "issue", "loading", "noscope", "versions")


def test_s8_preview_routes_render_every_requests_state(tmp_path):
    original_database_url = settings.database_url
    for screen, states in (
        ("b6-magic_links", screen_states()["b6-magic_links"]),
        ("b6-rfi", screen_states()["b6-rfi"]),
    ):
        for state in states:
            db_path = Path(tmp_path) / f"{screen}-{state}.sqlite3"
            info = seed_s8(db_path, screen=screen, state=state)
            engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
            db = sessionmaker(bind=engine)()
            settings.database_url = f"sqlite:///{db_path}"
            settings.upload_dir = str(db_path.with_suffix(".uploads"))

            def override_db():
                yield db

            app.dependency_overrides[get_db] = override_db
            try:
                with TestClient(app, raise_server_exceptions=False) as client:
                    response = client.get(
                        f"/design/pages/{screen}?assessment_id={info['assessment_id']}&state={state}"
                    )
                assert response.status_code == 200, (screen, state, response.text[:500])
            finally:
                app.dependency_overrides.clear()
                db.close()
                engine.dispose()
    settings.database_url = original_database_url
