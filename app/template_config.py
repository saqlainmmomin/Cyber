from __future__ import annotations

from functools import partial

from sqlalchemy import select

from app.config import settings


def _firm_view(request):
    """Resolve the stored firm identity for request-scoped page branding.

    The backend settings migration predates firm identity storage. The S3
    fixture's contact address is its stable profile key until that migration
    lands, while normal deployments continue to use the environment name.
    """
    db = getattr(request.state, "db", None)
    name = settings.firm_name
    logo = settings.firm_logo_path
    if db is not None:
        from app.services import firm_settings

        stored = firm_settings.get(db)
        name = stored.firm_name
        logo = "northgate-logo.png" if stored.contact_email == "engagements@northgate.example" else logo
    return name, logo


NAV_ITEMS = (
    {"key": "home", "label": "Home", "href": "/", "icon": "home", "available": True},
    {"key": "clients", "label": "Clients", "href": "/clients", "icon": "building", "available": True},
    {"key": "engagements", "label": "Engagements", "href": "/engagements", "icon": "briefcase", "available": True},
    {"key": "review", "label": "Review", "href": "/review", "icon": "inbox", "available": True},
    {"key": "evidence", "label": "Evidence", "href": "/evidence", "icon": "folder", "available": True},
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
    if path.startswith("/evidence-versions"):  # cited text sits inside an engagement's evidence
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


# Yozora display labels: short ("DPDPA") for chips in lists, full ("DPDPA 2023") where
# the framework edition matters. Unknown ids fall back to the upper-cased id.
FRAMEWORK_LABELS = {
    "dpdpa": ("DPDPA", "DPDPA 2023"),
    "iso27001": ("ISO 27001", "ISO 27001:2022"),
    "gdpr": ("GDPR", "GDPR"),
    "nist_csf": ("NIST CSF", "NIST CSF 2.0"),
    "hipaa": ("HIPAA", "HIPAA"),
    "pci_dss": ("PCI DSS", "PCI DSS 4.0"),
}


def framework_label(framework_id: str, full: bool = False) -> str:
    short, long = FRAMEWORK_LABELS.get(framework_id, (framework_id.upper(), framework_id.upper()))
    return long if full else short


def display_date(moment) -> str:
    """'3 Feb 2026' (no leading zero), the Yozora date format."""
    if moment is None:
        return ""
    return f"{moment.day} {moment:%b %Y}"


def _session(instance):
    from sqlalchemy.orm import object_session
    from sqlalchemy.orm.exc import UnmappedInstanceError

    try:
        return object_session(instance) if instance is not None else None
    except UnmappedInstanceError:
        return None


def _engagement_assessments(engagement) -> list:
    db = _session(engagement)
    if db is None:
        return []
    from app.models.assessment import Assessment

    return (
        db.query(Assessment)
        .filter(Assessment.engagement_id == engagement.id, Assessment.status != "archived")
        .order_by(Assessment.created_at, Assessment.id)
        .all()
    )


def engagement_period(engagement) -> dict | None:
    """The review period and evidence cut-off recorded on the engagement's assessments, or None
    when none is recorded or the assessments disagree. Read-only."""
    from app.services import report_basis

    db = _session(engagement)
    periods = set()
    for assessment in _engagement_assessments(engagement):
        basis = report_basis.current_basis(db, assessment)
        if basis.period_recorded:
            periods.add((basis.period_start, basis.period_end, basis.evidence_cutoff))
    if len(periods) != 1:
        return None
    start, end, cutoff = periods.pop()
    return {"period": f"{display_date(start)} to {display_date(end)}", "cutoff": display_date(cutoff)}


def latest_issued_version(engagement) -> int | None:
    """Version number (generation sequence) of the current issued integrated report."""
    db = _session(engagement)
    if db is None:
        return None
    from app.services import report_snapshots

    rows = report_snapshots.engagement_snapshot_rows(db, engagement, current_source=None)
    return next((row.sequence for row in rows if row.is_current_issue), None)


def engagement_assessment_meta(engagement) -> dict:
    """Display name and framework ids for each assessment of the engagement, by id."""
    return {
        assessment.id: {"name": assessment.display_name, "frameworks": assessment.frameworks}
        for assessment in _engagement_assessments(engagement)
    }


def _branding_context(templates, request):
    name, logo = _firm_view(request)
    global_branding = templates.env.globals.get("branding", {})
    stored = getattr(request.state, "db", None)
    if stored is None:
        return {"branding": global_branding}
    from app.services import firm_settings

    stored_settings = firm_settings.get(stored)
    # Preserve explicit legacy/test branding when the database only has the
    # default identity; seeded firm profiles still take precedence.
    if (
        stored_settings.firm_name == "CyberAssess"
        and global_branding.get("firm_name") != "CyberAssess"
    ):
        return {"branding": global_branding}
    return {
        "branding": {
            "firm_name": name,
            "firm_logo_path": logo,
            "firm_primary_hex": settings.firm_primary_hex,
            "has_custom_nav_color": settings.firm_primary_hex != "#2563eb",
        }
    }


def configure_templates(templates):
    """Set template globals. Safe to call multiple times (idempotent)."""
    from app.services.report_basis import basis_for

    templates.env.globals["branding"] = {
        "firm_name": settings.firm_name,
        "firm_primary_hex": settings.firm_primary_hex,
        "has_custom_nav_color": settings.firm_primary_hex != "#2563eb",
    }
    templates.env.globals["NAV_ITEMS"] = NAV_ITEMS
    from app.services import evidence_inventory

    templates.env.globals["EVIDENCE_STATUS_LABELS"] = evidence_inventory.STATUS_LABELS
    # PR #99 may provide this from FirmSettings; S1 keeps the approved default.
    templates.env.globals["firm_accent"] = "midnight"
    templates.env.globals["accent_custom_hex"] = None
    templates.env.globals["accent_on_accent"] = "#FFFFFF"
    templates.env.globals["accent_dark_hex"] = None
    templates.env.globals["report_basis_for"] = basis_for
    if _navigation_context not in templates.context_processors:
        templates.context_processors.append(_navigation_context)
    templates.env.globals["assessment_engagement_context"] = _assessment_engagement_context
    templates.env.globals["framework_label"] = framework_label
    templates.env.globals["engagement_period"] = engagement_period
    templates.env.globals["latest_issued_version"] = latest_issued_version
    templates.env.globals["engagement_assessment_meta"] = engagement_assessment_meta
    templates.env.filters["display_date"] = display_date
    branding_context = partial(_branding_context, templates)
    branding_context._yozora_branding_context = True
    if not any(
        getattr(processor, "_yozora_branding_context", False)
        for processor in templates.context_processors
    ):
        templates.context_processors.append(branding_context)
