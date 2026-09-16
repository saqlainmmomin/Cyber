import logging
import re
from typing import Self

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

_DEFAULT_SESSION_SECRET = "change-me-in-production"
_DEFAULT_AUDITOR_PASSWORD = "admin"


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    database_url: str = "sqlite:///data/dpdpa.db"
    upload_dir: str = "uploads"
    max_document_words: int = 5000
    max_total_document_words: int = 20000
    claude_model: str = "claude-sonnet-4-20250514"

    # OpenRouter-backed LLM client (app/services/llm_client.py). Only
    # claude_analyzer.py uses this today — see tasks/handoffs/ for the
    # workstream that migrated it off the Anthropic SDK directly.
    openrouter_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    # Per-tier model selection. All three default to the same Claude model via
    # its OpenRouter id so the transport swap is behavior-neutral; flip these
    # independently once each tier's model choice has been validated against
    # the golden fixture.
    llm_model_extract: str = "deepseek/deepseek-v4-flash"
    llm_model_judge: str = "deepseek/deepseek-v4-pro"
    llm_model_synthesize: str = "deepseek/deepseek-v4-flash"
    session_secret: str = _DEFAULT_SESSION_SECRET
    auditor_username: str = "admin"
    auditor_password: str = _DEFAULT_AUDITOR_PASSWORD
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
        if self.session_secret == _DEFAULT_SESSION_SECRET:
            logger.warning(
                "Default session_secret is active; configure a deployment-specific secret"
            )
        if self.auditor_password == _DEFAULT_AUDITOR_PASSWORD:
            logger.warning(
                "Default auditor_password is active; configure a deployment-specific password"
            )
        return self

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
