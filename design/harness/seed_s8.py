"""Seed deterministic S8 specimens into throwaway SQLite databases.

The base seed reuses the S4 builders (through the existing S5 base-data helper)
and keeps the clock frozen. Each S8 group owns a ``seed_s8_<group>.py`` module
that exposes ``SCREEN_STATES`` and ``apply``/``route`` helpers. States that are
rendered through a ``PREVIEW_PAGES`` fixture or a mockup ``?state=`` are marked
as ``preview-state`` by the group module. Client-facing fixtures must use a
fixed fake token, never a real token.
"""

from __future__ import annotations

import argparse
import importlib
import json
import pkgutil
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import app.models  # noqa: F401 - register every model before create_all()
from app.config import settings
from app.database import Base
from app.models.firm_settings import FirmSettings
from design.harness.seed_s4 import FROZEN_NOW, _report_basis_event
from design.harness.seed_s5 import _base_data, _register_frameworks


def _group_modules():
    import design.harness as harness_package

    for module in pkgutil.iter_modules(harness_package.__path__):
        if module.name.startswith("seed_s8_"):
            yield importlib.import_module(f"design.harness.{module.name}")


def screen_states() -> dict[str, tuple[str, ...]]:
    """Return the screen/state registry contributed by all S8 groups."""
    states: dict[str, tuple[str, ...]] = {}
    for module in _group_modules():
        states.update(module.SCREEN_STATES)
    return states


def _module_for(screen: str):
    for module in _group_modules():
        if screen in module.SCREEN_STATES:
            return module
    raise ValueError(f"unknown screen {screen!r}")


def seed_s8(output: str | Path, *, screen: str, state: str = "default") -> dict:
    """Create one deterministic database for one S8 screen state."""
    _register_frameworks()
    module = _module_for(screen)
    if state not in module.SCREEN_STATES[screen]:
        raise ValueError(f"unknown state {state!r} for {screen}")

    output_path = Path(output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    settings.upload_dir = str(output_path.with_suffix(".uploads"))
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()
    engine = create_engine(f"sqlite:///{output_path}")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(FirmSettings(id=1, archived_retention_years=7, accent_theme="midnight", updated_at=FROZEN_NOW))
        data = _base_data(db, include_assessment=True)
        assessment, engagement = data["assessments"][0], data["engagements"][0]
        result = module.apply(db, screen, state, assessment, engagement, data) or {}
        db.add(_report_basis_event(assessment))
        db.flush()
        db.commit()
        assessment_id = assessment.id
    engine.dispose()

    alembic_config = Config(str(REPO_ROOT / "alembic.ini"))
    alembic_config.set_main_option("sqlalchemy.url", f"sqlite:///{output_path}")
    command.stamp(alembic_config, "head")
    return {
        "output": str(output_path),
        "screen": screen,
        "state": state,
        "assessment_id": assessment_id,
        "data_state": result.get("data_state", "database"),
        "note": result.get("note", ""),
        "frozen_now": FROZEN_NOW.isoformat(),
        "alembic": "head",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="/tmp/yozora-s8.sqlite3")
    parser.add_argument("--screen")
    parser.add_argument("--state", default="default")
    parser.add_argument("--list", action="store_true", help="print every screen and state, then exit")
    args = parser.parse_args()
    if args.list:
        print(json.dumps(screen_states(), indent=2, sort_keys=True))
        return
    print(json.dumps(seed_s8(args.output, screen=args.screen, state=args.state), sort_keys=True))


if __name__ == "__main__":
    main()
