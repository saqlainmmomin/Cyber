from app.config import settings


def configure_templates(templates):
    """Set template globals. Safe to call multiple times (idempotent)."""
    from app.services.report_basis import basis_for

    templates.env.globals["branding"] = {
        "firm_name": settings.firm_name,
        "firm_primary_hex": settings.firm_primary_hex,
        "has_custom_nav_color": settings.firm_primary_hex != "#2563eb",
    }
    templates.env.globals["report_basis_for"] = basis_for
