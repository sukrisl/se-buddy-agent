"""Baselines (spec Sec.6.4).

"se-buddy write baseline <name> writes baselines/<name>.yaml: the model
file hash, every register row id with its status, the open ask ids, and
the date. It tags git at the same commit. That is the whole feature - a
manifest and a tag, no gate model, no readiness engine."

The manifest-building logic here is deliberately gate-free and directly
testable; only the git tag step (in `commands/write_baseline.py`) needs a
real git repo and is exercised live rather than by unit test.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import yaml

from se_buddy.ask_store import open_asks
from se_buddy.atomic_write import atomic_write_text
from se_buddy.model import hash_model_files
from se_buddy.registers import load_register
from se_buddy.schemas import REGISTER_PREFIXES

_VALID_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class BaselineError(Exception):
    """A baseline name is unsafe, or `write_baseline` would silently
    overwrite an existing one."""


def _validate_name(name: str) -> None:
    """`name` becomes both a filename (`f"{name}.yaml"`) and a git tag - a
    code review found no validation at all here, so `..`/`/` in `name`
    could write outside `baselines_dir`. Excluding `/` and `\\` from the
    allowed charset alone already rules out a multi-segment path; `..` and
    a trailing `.` are rejected too since Windows treats a trailing dot
    specially and git rejects `..` in tag names outright.
    """
    if not _VALID_NAME.match(name) or ".." in name or name.endswith("."):
        raise BaselineError(
            f"{name!r} is not a valid baseline name - use letters, digits, '.', '_', '-' only, "
            "no '..' and no trailing '.'"
        )


def baselines_dir(root: Path) -> Path:
    return root / "se-buddy" / "baselines"


def baseline_path(root: Path, name: str) -> Path:
    return baselines_dir(root) / f"{name}.yaml"


def build_manifest(root: Path, aird_path: str | Path, today: str | None = None) -> dict:
    """Builds the baseline content (spec Sec.6.4) - no I/O beyond reading
    the register files and the model files needed to hash them.
    """
    today = today or date.today().isoformat()

    register_rows = {}
    for register in REGISTER_PREFIXES:
        rows = load_register(root, register)
        register_rows[register] = {row_id: row.get("status") for row_id, row in rows.items()}

    return {
        "date": today,
        "model_hash": hash_model_files(aird_path),
        "registers": register_rows,
        "open_ask_ids": sorted(open_asks(root).keys()),
    }


def write_baseline(
    root: Path, name: str, aird_path: str | Path, today: str | None = None, *, force: bool = False
) -> Path:
    _validate_name(name)
    path = baseline_path(root, name)
    if path.exists() and not force:
        raise BaselineError(f"{path} already exists - pass force=True to overwrite")
    manifest = build_manifest(root, aird_path, today=today)
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(path, yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True))
    return path


def load_baseline(root: Path, name: str) -> dict | None:
    path = baseline_path(root, name)
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8"))
