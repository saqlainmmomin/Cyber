import logging
import re
from typing import Literal, Self

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

_DEFAULT_SESSION_SECRET = "change-me-in-production"
_DEFAULT_AUDITOR_PASSWORD = "admin"


class Settings(BaseSettings):
    database_url: str = "sqlite:///data/dpdpa.db"
    upload_dir: str = "uploads"
    # Safety bound for pathological files at extraction, not an analysis cap;
    # v1 prompts remain bounded by max_total_document_words.
    max_document_words: int = 200000
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
    # found `reasoning: {"exclude": true}` unreliably honored by it: 5
    # identical calls against the real screening prompt returned
    # reasoning-token usage of 0, 0, 4292, 6573, and 8192 (i.e. the entire
    # budget). Flash turned out to reason too on some OpenRouter providers
    # (live, 2026-09-26): `exclude` only hides reasoning, it doesn't stop it,
    # and reasoning expands to fill whatever max_tokens allows. llm_client.py
    # therefore sends `reasoning: {"enabled": false}` on every call.
    llm_model_extract: str = "deepseek/deepseek-v4-flash"
    llm_model_judge: str = "deepseek/deepseek-v4-flash"
    llm_model_synthesize: str = "deepseek/deepseek-v4-flash"
    llm_model_vision: str = "anthropic/claude-sonnet-4"
    llm_timeout_seconds: float = 300.0
    # Wall-clock cap on one provider call, including reading a whole stream.
    # llm_timeout_seconds is an httpx per-phase timeout: its read timer resets
    # whenever bytes arrive, and OpenRouter sends keep-alive bytes while a
    # request is stuck upstream, so a stuck call never times out on it (live,
    # 2026-09-30: every in-flight c3 request hung for over an hour, twice).
    # The longest legitimate call seen took ~342 s.
    llm_request_deadline_seconds: float = 600.0
    llm_max_retries: int = 2
    llm_max_concurrency: int = 4
    llm_batch_threshold_controls: int = 90
    llm_batch_max_controls: int = 25
    # Output ceiling for registry-path framework calls (desk review, evidence
    # extraction, judge). A 93-control ISO judge answer needs ~16k+ tokens and
    # was truncated at the old 16,384 (live smoke 2026-09-25); DeepSeek V4 Flash
    # allows 384k output. The curated DPDPA single-framework path keeps its own
    # limits so its golden recordings stay byte-identical.
    llm_max_output_tokens_framework: int = 65536
    v2_chunk_min_words: int = 800
    v2_chunk_max_words: int = 1500
    v2_extraction_batch_max_requirements: int = 20
    v2_max_claims_per_call: int = 25
    v2_support_batch_max_claims: int = 25
    v2_min_quote_chars: int = 20
    v2_max_quote_chars: int = 600
    v2_max_extraction_calls: int = 600
    v2_extraction_max_tokens: int = 8192
    v2_support_max_tokens: int = 4096
    v2_structured_output: bool = True
    # Desk-review pipeline selector; v1 remains the default until the P6-5 gate.
    analysis_pipeline_version: Literal["v1", "v2"] = "v1"
    # Worker count for every pool in the v2 desk-review pipeline.
    v2_max_concurrency: int = 6
    # Whether v2 fills regex-missed document metadata with a verified LLM pass.
    v2_metadata_fallback: bool = True
    # Bounded, deterministic settings for the v2 Stage 2 requirement judge.
    v2_judge_batch_max_requirements: int = 15
    v2_judge_max_tokens: int = 8192
    v2_judge_max_claims_per_requirement: int = 25
    # v2 desk-review "what is missing" pass that feeds DPDPA pre-fill suppression.
    v2_missing_pass: bool = False
    v2_missing_max_tokens: int = 8192
    recover_interrupted_on_startup: bool = True
    session_secret: str = _DEFAULT_SESSION_SECRET
    auditor_username: str = "admin"
    auditor_password: str = _DEFAULT_AUDITOR_PASSWORD
    firm_name: str = "CyberAssess"
    firm_logo_path: str | None = None
    firm_primary_hex: str = "#2563eb"
    firm_color_primary: str = "#161A5C"
    firm_color_secondary: str = "#2D3FD3"
    firm_color_accent: str = "#12B3A6"
    aws_external_id_secret: str = ""

    @field_validator("firm_color_primary", "firm_color_secondary", "firm_color_accent")
    @classmethod
    def validate_firm_color(cls, v: str) -> str:
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", v):
            raise ValueError("firm colors must be 6-digit hex colors like #161A5C")
        return v

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
