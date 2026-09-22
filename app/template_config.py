from app.config import settings


def configure_templates(templates):
    """Set template globals. Safe to call multiple times (idempotent)."""
    templates.env.globals["branding"] = {
        "firm_name": settings.firm_name,
        "firm_primary_hex": settings.firm_primary_hex,
        "has_custom_nav_color": settings.firm_primary_hex != "#2563eb",
    }
