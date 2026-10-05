"""Focused contracts for the S8 versions-group page and visual-state registry."""

from pathlib import Path

from design.harness.seed_s8 import screen_states


ROOT = Path(__file__).resolve().parents[1]


def test_s8_versions_group_registers_the_handoff_state_matrix():
    states = screen_states()
    assert states["b6-report_snapshots"] == (
        "default", "empty", "error", "issue", "loading", "board", "unreleased"
    )
    assert states["b6-soa"] == ("default", "empty", "error", "loading", "saving", "saved")
    assert states["b6-comparison"] == ("default", "empty", "error", "iso", "loading")


def test_s8_versions_templates_keep_report_seg_and_page_contracts():
    snapshots = (ROOT / "app/templates/pages/report_snapshots.html").read_text()
    soa = (ROOT / "app/templates/pages/soa.html").read_text()
    comparison = (ROOT / "app/templates/pages/comparison.html").read_text()

    assert '{{ report_seg(assessment, "versions") }}' in snapshots
    assert '{{ report_seg(assessment, "applicability") }}' in soa
    assert 'data-soa-save' in soa and 'fetch(form.getAttribute(' in soa
    assert 'data-current-report-link' in comparison
    assert "Framework Scores" in comparison
    assert "Overall Score" not in comparison
