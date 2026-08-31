"""CP-nnnn proposals (spec Sec.6.1, Sec.9, Sec.7.1): one file per record,
`se-buddy/proposals/CP-nnnn.yaml`.

Filing a proposal is automatic authority (spec Sec.7.3: "`write propose`
is the one write with automatic authority... a proposal asserts what
*could* be done, not what is true") - unlike every other write verb in
this codebase, `file_cp()` has no TTY gate above it.

`proposed_changes` is a `capellambse.decl` document directly (spec
Sec.7.1's SHOULD: "make `proposed_changes` a `decl` document directly, so
the proposal *is* the executable change"). `model_hash` captures the
model's hash at proposal time - spec Sec.10.2's drift check ("the model
hash matches what was last parsed") needs a reference point spec Sec.9
doesn't literally name on the CP schema; this is that reference point,
documented as a completion in SPEC-COVERAGE.md.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from se_buddy.atomic_write import atomic_write_text
from se_buddy.memory import allocate_id
from se_buddy.model import hash_model_files
from se_buddy.schemas import validate_cp


class ProposalError(Exception):
    """A CP could not be filed as given - reported plainly."""


def proposals_dir(root: Path) -> Path:
    return root / "se-buddy" / "proposals"


def file_cp(root: Path, cp: dict, aird_path: str | Path) -> dict:
    """Allocates a `CP-nnnn` id and writes `proposals/CP-nnnn.yaml`.

    Refuses a `cp` that already carries an `id` - spec Sec.6.1: "history
    is superseded, never rewritten." A revised proposal is a new CP citing
    `supersedes`, never an edit to an old one.
    """
    if cp.get("id"):
        raise ProposalError(
            "a CP is never rewritten (spec Sec.6.1) - file a new CP with "
            f"supersedes: [{cp['id']!r}] instead of reusing its id"
        )

    directory = proposals_dir(root)
    cp_id = allocate_id("CP", directory)
    cp = {**cp, "id": cp_id, "model_hash": hash_model_files(aird_path)}

    result = validate_cp(cp)
    if not result.ok:
        raise ProposalError(
            "CP failed validation:\n" + "\n".join(f"  - {e}" for e in result.errors)
        )

    directory.mkdir(parents=True, exist_ok=True)
    atomic_write_text(directory / f"{cp_id}.yaml", yaml.safe_dump(cp, sort_keys=False, allow_unicode=True))
    return cp


def load_cp(root: Path, cp_id: str) -> dict | None:
    path = proposals_dir(root) / f"{cp_id}.yaml"
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8"))
