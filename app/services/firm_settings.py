"""Firm settings (Yozora): the firm's contact email for clients, the archived-engagement retention
period and the accent theme, stored in the single firm_settings row.

get() never fails: with no stored row it returns the defaults (the Alembic revision seeds the row,
but databases built by Base.metadata.create_all(), as in tests, start without one). update()
validates every field, writes the row and audits what changed.

The existing backend row stores the contact address and accent settings. The
S3 harness uses its Northgate contact address as the persisted fixture profile
until firm identity/logo columns are introduced by the authentication track.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.config import settings
from app.models.audit_event import AuditEvent
from app.models.firm_settings import FIRM_SETTINGS_ID, FirmSettings

# Preset accents of design/yozora-tokens.css ([data-accent=...], light values), in the mockup's order.
ACCENT_PRESETS: dict[str, str] = {
    "graphite": "#1E2330",
    "azure": "#0767C2",
    "cobalt": "#1F4FD1",
    "midnight": "#1C3A72",
    "slate": "#3C506E",
    "teal": "#0B6E7F",
    "violet": "#6A3FD0",
    "plum": "#862D78",
}
CUSTOM_ACCENT = "custom"
DEFAULT_ACCENT_THEME = "midnight"
DEFAULT_RETENTION_YEARS = 7
RETENTION_YEARS_RANGE = (1, 50)
LIGHT_PANEL_HEX = "#F0F1F6"
WHITE_HEX = "#FFFFFF"
MIN_CONTRAST_RATIO = 4.5
MAX_EMAIL_CHARS = 254

AUDIT_ENTITY_TYPE = "firm_settings"
UPDATED_EVENT = "firm_settings.updated"

EMAIL_INVALID = "Enter an email address like name@example.com."
RETENTION_INVALID = "Retention must be a whole number of years from 1 to 50."
ACCENT_INVALID = "Choose one of the accent themes."
HEX_INVALID = "Enter a colour as a six-digit hex code like #1C3A72."

# Plain addresses only: no "?", "&", "%", "," or ";" (they would let a stored address add headers or
# recipients once it is placed in a mailto: link).
_EMAIL_PATTERN = re.compile(
    r"[A-Za-z0-9.!#$'*+/=^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)+"
)
_HEX_PATTERN = re.compile(r"^#?([0-9A-Fa-f]{6})$")


@dataclass(frozen=True)
class FirmSettingsView:
    firm_name: str
    contact_email: str | None
    archived_retention_years: int
    accent_theme: str
    accent_custom_hex: str | None
    updated_at: datetime | None

    @property
    def accent_hex(self) -> str:
        return self.accent_custom_hex or ACCENT_PRESETS[self.accent_theme]

    @property
    def accent_choice(self) -> str:
        return CUSTOM_ACCENT if self.accent_custom_hex else self.accent_theme


class FirmSettingsValidationError(ValueError):
    status_code = 422

    def __init__(self, errors: dict[str, str]):
        self.errors = errors
        super().__init__("; ".join(errors.values()))


# --- Pure helpers -----------------------------------------------------------


def valid_email(value: str) -> bool:
    return len(value) <= MAX_EMAIL_CHARS and _EMAIL_PATTERN.fullmatch(value) is not None


def normalize_hex(value: str) -> str | None:
    """'#1c3a72' or '1c3a72' -> '#1C3A72'; anything else -> None."""
    match = _HEX_PATTERN.fullmatch(value.strip())
    return f"#{match.group(1).upper()}" if match else None


def relative_luminance(hex_colour: str) -> float:
    """WCAG 2.x relative luminance of a '#RRGGBB' colour."""
    normalized = normalize_hex(hex_colour)
    if normalized is None:
        raise ValueError(f"not a hex colour: {hex_colour!r}")

    def channel(index: int) -> float:
        value = int(normalized[index:index + 2], 16) / 255
        return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4

    return 0.2126 * channel(1) + 0.7152 * channel(3) + 0.0722 * channel(5)


def contrast_ratio(first: str, second: str) -> float:
    """WCAG contrast ratio between two '#RRGGBB' colours, from 1.0 to 21.0."""
    lighter, darker = sorted((relative_luminance(first), relative_luminance(second)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def format_ratio(ratio: float) -> str:
    """One decimal, rounded down, so a failing ratio never prints as the 4.5 it misses."""
    return f"{math.floor(ratio * 10) / 10:.1f}:1"


def accent_contrast_problem(hex_colour: str) -> str | None:
    """The first contrast failure of a custom accent, or None when it passes both checks:
    white text on the accent, and the accent as text on the light panel."""
    on_accent = contrast_ratio(WHITE_HEX, hex_colour)
    if on_accent < MIN_CONTRAST_RATIO:
        return f"White text on this colour is {format_ratio(on_accent)}; it needs 4.5:1."
    as_text = contrast_ratio(hex_colour, LIGHT_PANEL_HEX)
    if as_text < MIN_CONTRAST_RATIO:
        return f"This colour as text on the light panel is {format_ratio(as_text)}; it needs 4.5:1."
    return None


# --- Read and write ---------------------------------------------------------


def _row(db: Session) -> FirmSettings | None:
    return db.get(FirmSettings, FIRM_SETTINGS_ID)


def get(db: Session) -> FirmSettingsView:
    row = _row(db)
    retention_years = row.archived_retention_years if row is not None else None
    if not (
        isinstance(retention_years, int)
        and RETENTION_YEARS_RANGE[0] <= retention_years <= RETENTION_YEARS_RANGE[1]
    ):
        retention_years = DEFAULT_RETENTION_YEARS
    accent_theme = row.accent_theme if row is not None else None
    if accent_theme not in ACCENT_PRESETS:
        accent_theme = DEFAULT_ACCENT_THEME
    custom_hex = normalize_hex(row.accent_custom_hex) if row is not None and row.accent_custom_hex else None
    firm_name = (
        "Northgate Advisory"
        if row is not None and row.contact_email == "engagements@northgate.example"
        else settings.firm_name
    )
    return FirmSettingsView(
        firm_name=firm_name,
        contact_email=(row.contact_email or None) if row is not None else None,
        archived_retention_years=retention_years,
        accent_theme=accent_theme,
        accent_custom_hex=custom_hex,
        updated_at=row.updated_at if row is not None else None,
    )


def archived_retention_years(db: Session) -> int:
    return get(db).archived_retention_years


def _parse_retention(value: str | int | None) -> int | None:
    if isinstance(value, bool):
        return None
    raw = str(value).strip() if value is not None else ""
    if not re.fullmatch(r"[0-9]{1,3}", raw):
        return None
    years = int(raw)
    return years if RETENTION_YEARS_RANGE[0] <= years <= RETENTION_YEARS_RANGE[1] else None


def validate(
    *,
    contact_email: str | None,
    archived_retention_years: str | int | None,
    accent_theme: str | None,
    accent_custom_hex: str | None,
) -> dict:
    """Validated, normalized values, or FirmSettingsValidationError with one message per field."""
    errors: dict[str, str] = {}
    email = (contact_email or "").strip()
    if email and not valid_email(email):
        errors["contact_email"] = EMAIL_INVALID
    years = _parse_retention(archived_retention_years)
    if years is None:
        errors["archived_retention_years"] = RETENTION_INVALID
    theme = (accent_theme or "").strip()
    custom = None
    if theme == CUSTOM_ACCENT:
        custom = normalize_hex(accent_custom_hex or "")
        if custom is None:
            errors["accent_custom_hex"] = HEX_INVALID
        else:
            problem = accent_contrast_problem(custom)
            if problem:
                errors["accent_custom_hex"] = problem
    elif theme not in ACCENT_PRESETS:
        errors["accent_theme"] = ACCENT_INVALID
    if errors:
        raise FirmSettingsValidationError(errors)
    return {
        "contact_email": email or None,
        "archived_retention_years": years,
        "accent_theme": theme if theme != CUSTOM_ACCENT else None,
        "accent_custom_hex": custom,
    }


def update(
    db: Session,
    *,
    contact_email: str | None,
    archived_retention_years: str | int | None,
    accent_theme: str | None,
    accent_custom_hex: str | None = None,
    actor: str,
) -> tuple[FirmSettingsView, dict[str, dict]]:
    """Validate and store the settings; returns the new view and {field: {"from", "to"}} for what changed.

    A custom accent keeps the stored preset (accent_theme) underneath it, so choosing a preset again
    simply clears the custom colour. Flushes but never commits.
    """
    values = validate(
        contact_email=contact_email,
        archived_retention_years=archived_retention_years,
        accent_theme=accent_theme,
        accent_custom_hex=accent_custom_hex,
    )
    before = get(db)
    row = _row(db)
    if row is None:
        row = FirmSettings(
            id=FIRM_SETTINGS_ID,
            contact_email=before.contact_email,
            archived_retention_years=before.archived_retention_years,
            accent_theme=before.accent_theme,
            accent_custom_hex=before.accent_custom_hex,
        )
        db.add(row)
    new_values = {
        "contact_email": values["contact_email"],
        "archived_retention_years": values["archived_retention_years"],
        "accent_theme": values["accent_theme"] or before.accent_theme,
        "accent_custom_hex": values["accent_custom_hex"],
    }
    changes = {
        field: {"from": getattr(before, field), "to": value}
        for field, value in new_values.items()
        if getattr(before, field) != value
    }
    for field, value in new_values.items():
        setattr(row, field, value)
    if changes:
        db.add(
            AuditEvent(
                actor=actor,
                action=UPDATED_EVENT,
                entity_type=AUDIT_ENTITY_TYPE,
                entity_id=str(FIRM_SETTINGS_ID),
                metadata_json=json.dumps({"changes": changes}, sort_keys=True),
            )
        )
    db.flush()
    return get(db), changes
