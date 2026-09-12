import logging

from app.config import Settings


def test_settings_warn_when_shipped_credentials_are_active(caplog, monkeypatch):
    monkeypatch.delenv("SESSION_SECRET", raising=False)
    monkeypatch.delenv("AUDITOR_PASSWORD", raising=False)

    with caplog.at_level(logging.WARNING, logger="app.config"):
        Settings(_env_file=None)

    messages = [record.getMessage() for record in caplog.records]
    assert any("session_secret" in message for message in messages)
    assert any("auditor_password" in message for message in messages)


def test_settings_do_not_warn_for_custom_credentials(caplog):
    with caplog.at_level(logging.WARNING, logger="app.config"):
        Settings(
            session_secret="a-deployment-specific-session-secret",
            auditor_password="a-deployment-specific-password",
            _env_file=None,
        )

    assert not caplog.records
