import logging
import re
from typing import Self

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    database_url: str = "sqlite:///data/dpdpa.db"
    upload_dir: str = "uploads"
    max_document_words: int = 5000
    max_total_document_words: int = 20000
    claude_model: str = "claude-sonnet-4-20250514"
    session_secret: str = "change-me-in-production"
    auditor_username: str = "admin"
    auditor_password: str = "admin"
    firm_name: str = "CyberAssess"
    firm_logo_path: str | None = None
    firm_primary_hex: str = "#2563eb"

    @field_validator("firm_primary_hex")
    @classmethod
    def validate_hex_color(cls, v: str) -> str:
        if not re.match(r"^#[0-9a-fA-F]{6}$", v):
            raise ValueError("firm_primary_hex must be a 6-digit hex color like #2563eb")
        return v

    @model_validator(mode="after")
    def warn_insecure_defaults(self) -> Self:
        if self.session_secret == "change-me-in-production":
            logger.warning(
                "Default session_secret is active; configure a deployment-specific secret"
            )
        if self.auditor_password == "admin":
            logger.warning(
                "Default auditor_password is active; configure a deployment-specific password"
            )
        return self

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
