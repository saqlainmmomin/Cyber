from app.config import Settings, settings


def resolve_theme(config: Settings | None = None) -> dict[str, str | None]:
    config = config or settings
    return {
        "firm_name": config.firm_name,
        "logo_path": config.firm_logo_path,
        "primary": config.firm_color_primary,
        "secondary": config.firm_color_secondary,
        "accent": config.firm_color_accent,
    }
