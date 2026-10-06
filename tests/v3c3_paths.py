"""Scoped V3-C3 XLSX parity paths for the per-PR file-set guards."""

V3C3_XLSX_PATHS = (
    "app/services/board_exports.py",
    "tests/test_p6_8_v3c3_extra.py",
    "tasks/handoffs/2026-10-06-v3c3-pptx-xlsx-parity.md",
    # The adjacent V3-C2 handoff is already present on this branch and must remain
    # visible to the older V3-B guard until the dependent deck work lands.
    "tasks/handoffs/2026-10-06-v3c2-deck-build.md",
)
