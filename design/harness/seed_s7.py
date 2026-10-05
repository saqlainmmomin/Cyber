"""Seed deterministic S7 specimens (analysis, review, report, narrative, board inputs).

One throwaway SQLite database per screen state, frozen clock, the mockup companies
(Meridian Ledger Technologies, Loomwire Labs, Kestrel Advisory). Builders come from
``seed_s4``/``seed_s5``; neither is edited. Each slice group owns a module named
``seed_s7_<group>.py`` that exposes ``SCREEN_STATES`` (screen -> states) and
``apply(db, screen, state, assessment, engagement, data) -> dict``; the returned dict may
carry ``data_state`` (``database`` or ``preview-state``) and ``note`` (how the state was
produced). States reached through ``PREVIEW_PAGES`` fixtures or the mockup's own
``?state=`` are marked ``preview-state``.
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
from app.database import Base
from app.models.firm_settings import FirmSettings
from design.harness.seed_s4 import FROZEN_NOW, _report_basis_event
from design.harness.seed_s5 import _base_data, _register_frameworks


def _group_modules():
    import design.harness as harness_package

    for module in pkgutil.iter_modules(harness_package.__path__):
        if module.name.startswith("seed_s7_"):
            yield importlib.import_module(f"design.harness.{module.name}")


def screen_states() -> dict[str, tuple[str, ...]]:
    states: dict[str, tuple[str, ...]] = {}
    for module in _group_modules():
        states.update(module.SCREEN_STATES)
    return states


def _module_for(screen: str):
    for module in _group_modules():
        if screen in module.SCREEN_STATES:
            return module
    raise ValueError(f"unknown screen {screen!r}")


def seed_s7(output: str | Path, *, screen: str, state: str = "default") -> dict:
    """Create one deterministic database for one S7 screen state and stamp Alembic head."""
    _register_frameworks()
    module = _module_for(screen)
    if state not in module.SCREEN_STATES[screen]:
        raise ValueError(f"unknown state {state!r} for {screen}")

    output_path = Path(output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
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
    parser.add_argument("--output", default="/tmp/yozora-s7.sqlite3")
    parser.add_argument("--screen")
    parser.add_argument("--state", default="default")
    parser.add_argument("--list", action="store_true", help="print every screen and state, then exit")
    args = parser.parse_args()
    if args.list:
        print(json.dumps(screen_states(), indent=2, sort_keys=True))
        return
    print(json.dumps(seed_s7(args.output, screen=args.screen, state=args.state), sort_keys=True))


if __name__ == "__main__":
    main()
