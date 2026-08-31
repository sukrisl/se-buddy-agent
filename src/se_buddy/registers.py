"""Register load/save (spec Sec.6.2).

One file per register, rows keyed by stable id - the spec's own stated
lean on the OPEN granularity question ("it is not, for one engineer" -
Sec.6.2). Six registers live under `se-buddy/registers/`:
`requirements`, `stakeholder-expectations`, `risks-system`,
`risks-project`, `verification`, `not-carried`.

This module is the only place a register file is read or written - `se-
buddy register <name>` (read) and `se-buddy write register <name> row.yaml`
(gated write, spec Sec.7.3) both go through it, so "the only route" (spec
Sec.6.2) is true in the code, not just in the CLI help text.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from se_buddy.memory import next_id
from se_buddy.schemas import REGISTER_PREFIXES, validate_register_row


class RegisterError(Exception):
    """A register operation could not be completed - reported plainly."""


def registers_dir(root: Path) -> Path:
    return root / "se-buddy" / "registers"


def register_path(root: Path, register: str) -> Path:
    if register not in REGISTER_PREFIXES:
        raise RegisterError(
            f"unknown register {register!r}; expected one of {sorted(REGISTER_PREFIXES)}"
        )
    return registers_dir(root) / f"{register}.yaml"


def load_register(root: Path, register: str) -> dict[str, dict]:
    """Returns `{row_id: row}` for `register`. Empty dict if the file doesn't exist yet."""
    path = register_path(root, register)
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("rows") or {}


def save_register(root: Path, register: str, rows: dict[str, dict]) -> Path:
    path = register_path(root, register)
    path.parent.mkdir(parents=True, exist_ok=True)
    # sort_keys=False preserves insertion order (row id ascending, since
    # callers only ever add/update - a diff-friendly register is worth
    # more than an alphabetised one to an engineer reviewing `git diff`.
    path.write_text(
        yaml.safe_dump({"rows": rows}, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return path


def upsert_row(root: Path, register: str, row: dict) -> dict:
    """Adds a new row (allocating an id) or updates an existing one by id.

    A `row` carrying an existing `id` updates that row in place - needed
    for `risk-manage`'s track/close (a risk's `status` changes over its
    life; it's still the same risk, same id). A `row` with no `id` is
    treated as new and gets one allocated here, never supplied by the
    caller (spec Sec.9: ids are allocated, not authored).

    Raises `RegisterError` (never a bare `schemas.SchemaError`) on a row
    that fails validation, naming every error - the caller decides whether
    to report warnings.
    """
    rows = load_register(root, register)

    row_id = row.get("id")
    if row_id:
        if row_id not in rows:
            raise RegisterError(f"{row_id!r} does not exist in {register} - nothing to update")
    else:
        row_id = next_id(REGISTER_PREFIXES[register], rows.keys())
        row = {**row, "id": row_id}

    result = validate_register_row(register, row)
    if not result.ok:
        raise RegisterError(
            f"row for {register} failed validation:\n" + "\n".join(f"  - {e}" for e in result.errors)
        )

    rows[row_id] = row
    save_register(root, register, rows)
    return row


def find_row(root: Path, target_id: str) -> tuple[str, dict] | None:
    """Searches every register for a row whose id is `target_id`.

    Returns `(register_name, row)`, or None. Used by `se-buddy trace` to
    resolve a register-row id the same way `show`/`trace` resolve a model
    uuid (spec Sec.7.2 `trace`: "closure over model and registers for one id").
    """
    for register in REGISTER_PREFIXES:
        rows = load_register(root, register)
        if target_id in rows:
            return register, rows[target_id]
    return None


def find_rows_linking(root: Path, target_id: str) -> list[tuple[str, dict]]:
    """Every register row (in any register) whose `links` cites `target_id`.

    The other half of "trace across model and registers" (spec Sec.11):
    given a model element's uuid, which registers reference it.
    """
    found: list[tuple[str, dict]] = []
    for register in REGISTER_PREFIXES:
        for row in load_register(root, register).values():
            if target_id in (row.get("links") or []):
                found.append((register, row))
    return found
