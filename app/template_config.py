from __future__ import annotations

from sqlalchemy import select

from app.config import settings


NAV_ITEMS = (
    {"key": "home", "label": "Home", "href": "/", "icon": "home", "available": True},
    {"key": "clients", "label": "Clients", "href": "/clients", "icon": "building", "available": False},
    {"key": "engagements", "label": "Engagements", "href": "/engagements", "icon": "briefcase", "available": True},
    {"key": "review", "label": "Review", "href": "/review", "icon": "inbox", "available": False},
    {"key": "evidence", "label": "Evidence", "href": "/evidence", "icon": "folder", "available": False},
    {"key": "reports", "label": "Reports", "href": "/reports", "icon": "report", "available": True},
    {"key": "settings", "label": "Settings", "href": "/settings", "icon": "settings", "available": True},
)


def _nav_section(path: str) -> str:
    """Return the IA section for a request path.

    Assessment and engagement sub-pages belong to Engagements until their
    cross-engagement routes are introduced by later slices.
    """
    if path == "/" or not path:
        return "home"
    if path.startswith("/clients"):
        return "clients"
    if path.startswith("/engagements") or path.startswith("/assessments"):
        return "engagements"
    if path.startswith("/review"):
        return "review"
    if path.startswith("/evidence"):
        return "evidence"
    if path.startswith("/reports"):
        return "reports"
    if path.startswith("/settings"):
        return "settings"
    return "home"


def _review_count(request) -> int:
    """Count unresolved conclusion decisions with one database query.

    The row set contains the latest revision candidates; state reduction stays
    in Python so the context processor does not reproduce review_queue's
    conclusion-card query graph.
    """
    db = getattr(request.state, "db", None)
    if db is None:
        return 0

    from app.models.assessment import Assessment
    from app.models.conclusion import Conclusion, ConclusionRevision

    rows = db.execute(
        select(
            Conclusion.id,
            ConclusionRevision.action,
            ConclusionRevision.created_at,
            ConclusionRevision.actor,
        )
        .join(Assessment, Assessment.id == Conclusion.assessment_id)
        .outerjoin(
            ConclusionRevision,
            ConclusionRevision.conclusion_id == Conclusion.id,
        )
        .where(Assessment.status != "archived")
        .order_by(Conclusion.id, ConclusionRevision.created_at)
    ).all()
    latest: dict[str, tuple[str | None, str | None]] = {}
    for conclusion_id, action, _created_at, actor in rows:
        latest[conclusion_id] = (action, actor)

    locking_actions = {"approved", "edited"}
    return sum(
        1
        for action, _actor in latest.values()
        if action not in locking_actions
    )


def _navigation_context(request):
    section = _nav_section(request.url.path)
    return {
        "nav_items": [
            dict(item, current=item["key"] == section)
            for item in NAV_ITEMS
            if item["available"]
        ],
        "review_count": _review_count(request),
    }


def _assessment_engagement_context(request):
    """Keep engagement-level tools in the redirected assessment overview DOM."""
    path_parts = request.url.path.strip("/").split("/")
    if len(path_parts) != 2 or path_parts[0] != "assessments":
        return {}
    db = getattr(request.state, "db", None)
    override_generator = None
    if db is None:
        from app.database import get_db

        override = getattr(request.app, "dependency_overrides", {}).get(get_db)
        if override is None:
            return {}
        candidate = override()
        if not hasattr(candidate, "__next__"):
            db = candidate
        else:
            override_generator = candidate
            try:
                db = next(override_generator)
            except StopIteration:
                return {}

    from app.models.assessment import Assessment
    from app.models.engagement import Engagement
    from app.services import retention
    from app.services.magic_links import client_upload_rows, magic_link_rows

    try:
        assessment = db.get(Assessment, path_parts[1])
        engagement = db.get(Engagement, assessment.engagement_id) if assessment and assessment.engagement_id else None
        if engagement is None:
            return {}
        return {
            "engagement": engagement,
            "engagement_id": engagement.id,
            "magic_links": magic_link_rows(db, engagement.id),
            "client_uploads": client_upload_rows(db, engagement.id),
            "retention": retention.retention_state(db, engagement),
        }
    finally:
        if override_generator is not None:
            override_generator.close()


def configure_templates(templates):
    """Set template globals. Safe to call multiple times (idempotent)."""
    from app.services.report_basis import basis_for

    templates.env.globals["branding"] = {
        "firm_name": settings.firm_name,
        "firm_primary_hex": settings.firm_primary_hex,
        "has_custom_nav_color": settings.firm_primary_hex != "#2563eb",
    }
    templates.env.globals["NAV_ITEMS"] = NAV_ITEMS
    # PR #99 may provide this from FirmSettings; S1 keeps the approved default.
    templates.env.globals["firm_accent"] = "midnight"
    templates.env.globals["accent_custom_hex"] = None
    templates.env.globals["accent_on_accent"] = "#FFFFFF"
    templates.env.globals["accent_dark_hex"] = None
    templates.env.globals["report_basis_for"] = basis_for
    if _navigation_context not in templates.context_processors:
        templates.context_processors.append(_navigation_context)
    templates.env.globals["assessment_engagement_context"] = _assessment_engagement_context
