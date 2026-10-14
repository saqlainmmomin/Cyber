"""
Unified control framework (UCF) library: schema and loader.

Static authored data, loaded from CSV and JSON files in one folder. Nothing in the
app reads this package yet. Stdlib only; do not import the rest of the app here.
"""

from .loader import Library, load_library, parse_control_id, parse_key_settings
from .schema import (
    Atom,
    Control,
    Domain,
    KeySetting,
    MappingRow,
    Record,
)

__all__ = [
    "Atom",
    "Control",
    "Domain",
    "KeySetting",
    "Library",
    "MappingRow",
    "Record",
    "load_library",
    "parse_control_id",
    "parse_key_settings",
]
