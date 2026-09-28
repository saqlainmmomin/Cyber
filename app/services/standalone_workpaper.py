"""Render the Workpaper as a self-contained offline HTML document."""

from __future__ import annotations

from pathlib import Path

from fastapi.templating import Jinja2Templates

from app.services import workpaper
from app.template_config import configure_templates


TEMPLATE = "reports/workpaper_standalone.html"

_templates = Jinja2Templates(
    directory=Path(__file__).resolve().parents[1] / "templates"
)
configure_templates(_templates)


def render(db, assessment) -> str:
    document = workpaper.build_workpaper(db, assessment)
    return _templates.get_template(TEMPLATE).render(
        assessment=assessment,
        wp=document,
    )
