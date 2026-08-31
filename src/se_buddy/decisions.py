"""ADRs (spec Sec.6.1, Sec.9): one file per record, `se-buddy/decisions/ADR-nnnn.yaml`.

Narrative records stay as files in git (spec Sec.6.1: "they are prose,
they are history, and C06 reversibility depends on `git diff` working on
them") - unlike registers, which are one file holding many rows (spec
Sec.6.2). `se-buddy write memory decisions d.yaml` is the only writer.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from se_buddy.atomic_write import atomic_write_text
from se_buddy.memory import allocate_id
from se_buddy.schemas import validate_adr


class DecisionError(Exception):
    """An ADR could not be filed as given - reported plainly."""


def decisions_dir(root: Path) -> Path:
    return root / "se-buddy" / "decisions"


def file_adr(root: Path, adr: dict) -> dict:
    """Allocates an `ADR-nnnn` id and writes `decisions/ADR-nnnn.yaml`.

    Refuses an `adr` that already carries an `id` - spec Sec.6.1: "history
    is superseded, never rewritten." A correction is a new ADR citing
    `supersedes`, never an edit to an old one, so there is no update path
    here at all (unlike a register row or a viewpoint).
    """
    if adr.get("id"):
        raise DecisionError(
            "an ADR is never rewritten (spec Sec.6.1) - file a new ADR with "
            f"supersedes: [{adr['id']!r}] instead of reusing its id"
        )

    directory = decisions_dir(root)
    adr_id = allocate_id("ADR", directory)
    adr = {**adr, "id": adr_id}

    result = validate_adr(adr)
    if not result.ok:
        raise DecisionError(
            "ADR failed validation:\n" + "\n".join(f"  - {e}" for e in result.errors)
        )

    directory.mkdir(parents=True, exist_ok=True)
    atomic_write_text(directory / f"{adr_id}.yaml", yaml.safe_dump(adr, sort_keys=False, allow_unicode=True))
    return adr


def load_adr(root: Path, adr_id: str) -> dict | None:
    path = decisions_dir(root) / f"{adr_id}.yaml"
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8"))
