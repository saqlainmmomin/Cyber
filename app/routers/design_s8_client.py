"""Debug-only S8 client page fixtures for the pixel gate."""

from __future__ import annotations

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.firm_settings import FirmSettings
from app.models.magic_link import MagicLink
from app.routers import magic
from app.routers.design import DB_PREVIEWS, PREVIEW_PAGES
from app.routers.web import templates


def _active_link(db: Session) -> MagicLink:
    link = db.get(MagicLink, "s8-client-active")
    if link is None:  # pragma: no cover - the harness always seeds it
        raise LookupError("S8 client fixture link is missing")
    return link


def _preview_upload(request: Request, db: Session):
    state = request.query_params.get("state", "default")
    if state not in {"default", "uploading", "done", "error"}:
        state = "default"
    context = magic._upload_context(request, db, _active_link(db))
    context["preview_state"] = state
    items = [dict(item) for item in context["items"]]
    if state == "uploading":
        items[2].update(uploading=True, filename="access-review-q4.xlsx")
    elif state == "done":
        for item, filename in zip(
            items,
            (
                "consent-withdrawal-v3.pdf",
                "breach-runbook-2026.docx",
                "access-review-q4.xlsx",
                "vendor-dpa-register.xlsx",
            ),
        ):
            item.update(received=True, filename=filename)
        context["preview_received_count"] = len(items)
    elif state == "error":
        context["error"] = "The file is over the 25 MB limit. Upload a smaller copy."
    context["preview_items"] = items
    return templates.TemplateResponse("magic/upload.html", context)


def _preview_invalid(request: Request, db: Session):
    state = request.query_params.get("state", "expired")
    if state not in {"expired", "revoked", "unknown"}:
        state = "expired"
    links = {
        "expired": db.get(MagicLink, "s8-client-expired"),
        "revoked": db.get(MagicLink, "s8-client-revoked"),
    }
    context = magic._invalid_context(request, db, links.get(state))
    context["invalid_state"] = state
    # The fixture is a standalone visual state, while production copy is derived
    # from link_status at request time. Keep the mockup's contact action available
    # without changing the production firm's stored settings.
    if db.get(FirmSettings, 1) is not None:
        context["firm_contact_email"] = db.get(FirmSettings, 1).contact_email or "requests@cyberassess.example"
    return templates.TemplateResponse("magic/invalid.html", context)


PREVIEW_PAGES["b6-magic_upload"] = _preview_upload
PREVIEW_PAGES["b6-magic_invalid"] = _preview_invalid
PREVIEW_PAGES["b7-link-expired"] = _preview_invalid
DB_PREVIEWS.update({"b6-magic_upload", "b6-magic_invalid", "b7-link-expired"})
