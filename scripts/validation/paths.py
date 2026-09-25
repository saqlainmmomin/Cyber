"""Pack and run paths, including the runner's client-visible allow-list."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATION_ROOT = REPO_ROOT / "validation"


def pack_dir(slug: str, validation_root: Path | None = None) -> Path:
    root = validation_root or VALIDATION_ROOT
    path = root / "companies" / slug
    if not path.is_dir():
        raise FileNotFoundError(f"Company pack not found: {slug} ({path})")
    return path


def client_visible_files(slug: str, validation_root: Path | None = None) -> list[Path]:
    """Return only materials that may be supplied to the assessment runner."""
    base = pack_dir(slug, validation_root)
    paths: list[Path] = [base / "company.json"]
    visible = base / "client_visible"
    if visible.exists():
        paths.extend(path for path in visible.rglob("*") if path.is_file())
    for name in ("question_pack.intake.json", "question_pack.questionnaire.json"):
        path = base / name
        if path.is_file():
            paths.append(path)
    rendered = base / "rendered"
    if rendered.exists():
        paths.extend(path for path in rendered.rglob("*") if path.is_file())
    return sorted(set(paths))


def load_client_visible(slug: str, validation_root: Path | None = None) -> dict[str, Path]:
    base = pack_dir(slug, validation_root)
    return {path.relative_to(base).as_posix(): path for path in client_visible_files(slug, validation_root)}


def run_root(out_dir: Path | str) -> Path:
    return Path(out_dir).expanduser().resolve()
