import logging
import re
from typing import Self

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

_DEFAULT_SESSION_SECRET = "change-me-in-production"
_DEFAULT_AUDITOR_PASSWORD = "admin"


class Settings(BaseSettings):
    database_url: str = "sqlite:///data/dpdpa.db"
    upload_dir: str = "uploads"
    max_document_words: int = 5000
    max_total_document_words: int = 20000

    # OpenRouter-backed LLM client (app/services/llm_client.py) — every
    # Claude call site in the app goes through this now; there is no direct
    # Anthropic SDK usage left. See tasks/handoffs/ for the workstream that
    # migrated claude_analyzer.py first, then the remaining 6 call sites.
    openrouter_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    # Per-tier model selection. All three text tiers are DeepSeek Flash —
    # chosen from a single fixture comparison run, not a broad evaluation;
    # treat as a monitored rollout and flip independently once validated
    # further. `vision` is kept on a separate, vision-capable model since
    # none of the DeepSeek text tiers accept image input — verify this
    # model id against OpenRouter's current catalog before relying on it.
    #
    # `judge` was DeepSeek Pro (a reasoning model) until a live smoke test
    # found `reasoning: {"exclude": true}` (see llm_client.py) unreliably
    # honored by it: 5 identical calls against the real screening prompt
    # returned reasoning-token usage of 0, 0, 4292, 6573, and 8192 (i.e. the
    # entire budget) — a 60% failure rate (empty/truncated JSON) that more
    # max_tokens didn't fix, since reasoning simply expanded to fill whatever
    # budget was given. Flash is not a reasoning model and doesn't have this
    # failure mode.
    llm_model_extract: str = "deepseek/deepseek-v4-flash"
    llm_model_judge: str = "deepseek/deepseek-v4-flash"
    llm_model_synthesize: str = "deepseek/deepseek-v4-flash"
    llm_model_vision: str = "anthropic/claude-sonnet-4"
    llm_timeout_seconds: float = 300.0
    llm_max_retries: int = 2
    llm_max_concurrency: int = 4
    recover_interrupted_on_startup: bool = True
    session_secret: str = _DEFAULT_SESSION_SECRET
    auditor_username: str = "admin"
    auditor_password: str = _DEFAULT_AUDITOR_PASSWORD
    firm_name: str = "CyberAssess"
    firm_logo_path: str | None = None
    firm_primary_hex: str = "#2563eb"
    aws_external_id_secret: str = ""

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

    # "ignore" (not the pydantic-settings default of "forbid") so a leftover
    # ANTHROPIC_API_KEY/CLAUDE_MODEL in a developer's local .env from before
    # this migration doesn't hard-fail startup.
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
