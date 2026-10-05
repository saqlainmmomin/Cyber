from design.harness.seed_s7 import screen_states


def test_report_preview_states_are_registered():
    states = screen_states()
    assert states["b5-report"] == ("released", "not-released", "loading")
    assert states["b5-no-report"] == ("default",)


def test_loading_preview_is_registered_with_database_harness():
    from app.routers import design

    assert "b5-report-loading" in design.PREVIEW_PAGES
    assert "b5-report-loading" in design.DB_PREVIEWS
