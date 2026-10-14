"""
UCF library schema: row dataclasses, allowed values and column lists.

Stdlib only. The data format contract is docs/ucf/drafts/FORMAT.md.
"""

from __future__ import annotations

from dataclasses import dataclass

# -- enum value sets -------------------------------------------------------

FRAMEWORKS = ("iso27001", "nist_csf", "dpdpa")
SOURCE_CODES = {"iso": "iso27001", "nist": "nist_csf", "dpdpa": "dpdpa"}  # file code -> framework key
ORIGINS = ("iso", "nist", "dpdpa")
# id number ranges by control origin (inclusive). Privacy domains: dpdpa only, 1 to 99.
ORIGIN_ID_RANGES = {"iso": (1, 39), "nist": (40, 69), "dpdpa": (70, 99)}
PRIVACY_ID_RANGE = (1, 99)

RECORD_KINDS = ("clause", "annex", "subcategory", "requirement")
ISO_THEMES = ("Organizational", "People", "Physical", "Technological")  # empty also allowed
IMPORTANCE = ("critical", "high", "medium", "low")
CONTROL_TYPES = ("preventive", "detective", "corrective")
FREQUENCIES = ("continuous", "per_event", "monthly", "quarterly", "annual", "ad_hoc")

MATCH_TYPES = ("equal", "req_smaller", "req_bigger", "overlap", "none")
COVERAGES = ("full", "partial", "none")
ALLOWED_PAIRS = frozenset(
    {
        ("equal", "full"),
        ("req_smaller", "full"),
        ("req_bigger", "partial"),
        ("overlap", "partial"),
        ("none", "none"),
    }
)

KEY_SETTING_LAYERS = ("base",) + FRAMEWORKS

# The seven framework subsets, in report order.
FRAMEWORK_SUBSETS: tuple[frozenset[str], ...] = (
    frozenset({"iso27001"}),
    frozenset({"nist_csf"}),
    frozenset({"dpdpa"}),
    frozenset({"iso27001", "nist_csf"}),
    frozenset({"iso27001", "dpdpa"}),
    frozenset({"nist_csf", "dpdpa"}),
    frozenset({"iso27001", "nist_csf", "dpdpa"}),
)


def subset_label(subset: frozenset[str]) -> str:
    return "+".join(f for f in FRAMEWORKS if f in subset)


# -- column lists (the exact header of each table) ---------------------------

DOMAIN_COLUMNS = ("code", "name", "owner_role", "privacy", "sort")
ROLE_COLUMNS = ("role",)
RECORD_COLUMNS = ("framework", "record_id", "reference", "title", "kind", "group")
ATOM_COLUMNS = ("framework", "record_id", "atom_id", "source_ref", "paraphrase", "needs_verification")
CONTROL_COLUMNS = ("id", "title", "domain", "iso_theme", "goal", "owner_role", "importance", "origin", "note")
MAPPING_COLUMNS = (
    "source_framework",
    "record_id",
    "source_ref",
    "atom_id",
    "unified_control_id",
    "match_type",
    "coverage",
    "reason",
    "primary",
    "remainder_of",
    "remainder_immaterial",
    "immaterial_reason",
)
FIELD_COLUMNS = (
    "id",
    "statement",
    "why_asked",
    "how_to_ask",
    "question",
    "expected_evidence",
    "good_looks_like",
    "test",
    "baseline_risk",
    "applicability",
    "control_type",
    "frequency",
    "key_settings",
)
# Client- and consultant-facing text fields: no framework name, numbers only via key_settings.
TEXT_FIELDS = (
    "statement",
    "why_asked",
    "how_to_ask",
    "question",
    "expected_evidence",
    "good_looks_like",
    "test",
    "baseline_risk",
    "applicability",
    "key_settings",
)


# -- rows ------------------------------------------------------------------


@dataclass(frozen=True)
class Domain:
    code: str
    name: str
    owner_role: str
    privacy: bool
    sort: int
    src: str = ""


@dataclass(frozen=True)
class Record:
    framework: str
    record_id: str
    reference: str
    title: str
    kind: str
    group: str
    src: str = ""


@dataclass(frozen=True)
class Atom:
    framework: str
    record_id: str
    atom_id: str
    source_ref: str
    paraphrase: str
    needs_verification: bool
    src: str = ""


@dataclass(frozen=True)
class KeySetting:
    layer: str
    setting: str


@dataclass(frozen=True)
class Control:
    """A unified control: the controls_* skeleton row joined with its fields_* row.

    Field columns are empty strings and has_fields is False when no fields row exists.
    """

    id: str
    title: str
    domain: str
    iso_theme: str
    goal: str
    owner_role: str
    importance: str
    origin: str
    note: str
    src: str = ""
    # fields (joined on id)
    has_fields: bool = False
    fields_src: str = ""
    statement: str = ""
    why_asked: str = ""
    how_to_ask: str = ""
    question: str = ""
    expected_evidence: str = ""
    good_looks_like: str = ""
    test: str = ""
    baseline_risk: str = ""
    applicability: str = ""
    control_type: str = ""
    frequency: str = ""
    key_settings_raw: str = ""
    key_settings: tuple[KeySetting, ...] = ()
    key_settings_errors: tuple[str, ...] = ()

    def text_fields(self) -> dict[str, str]:
        """Name to text for every field in TEXT_FIELDS. key_settings contributes setting text only."""
        out = {name: getattr(self, name) for name in TEXT_FIELDS if name != "key_settings"}
        out["key_settings"] = " | ".join(ks.setting for ks in self.key_settings)
        return out


@dataclass(frozen=True)
class MappingRow:
    source_framework: str
    record_id: str
    source_ref: str
    atom_id: str
    unified_control_id: str  # empty on a `none` row
    match_type: str
    coverage: str
    reason: str
    primary: bool
    remainder_of: str
    remainder_immaterial: bool
    immaterial_reason: str
    src: str = ""
