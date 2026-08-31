"""Id allocation and citation rendering (spec Sec.3 D3, D8; Sec.7.2 `memory`).

Pure logic, no write path of its own. `se-buddy write register` and
`write answer` (Phase 2) call `next_id`/`allocate_id` to name a new
register row or `ASK-nnnn`; `write propose`/`write memory` (not yet
scoped to a phase) will do the same for `CP`/`ADR`/`CHANGE`. One allocator
for every id kind, so the sequencing rule (spec Sec.9: stable, never
renumbered, never hand-authored) lives in exactly one place.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

from se_buddy.schemas import RECORD_KINDS, REGISTER_PREFIXES

_ID_RE_TEMPLATE = r"({kind}-\d+)"

# Every prefix next_id/allocate_id will accept: narrative-record kinds
# (spec Sec.9) plus each register's row prefix (spec Sec.6.2). Kept as one
# set here since the allocator itself doesn't care which of the two a
# prefix belongs to - only that it's a real, known one.
_KNOWN_KINDS = RECORD_KINDS | set(REGISTER_PREFIXES.values())


def next_id(kind: str, existing_ids: Iterable[str]) -> str:
    """Returns the next sequential id of `kind`, given the ids already in use.

    `id` is allocated on write, stable, and never authored by hand (spec
    Sec.9) - this is the one place that allocation happens, so a record or
    ask always gets its id from here rather than a writer inventing one.
    """
    if kind not in _KNOWN_KINDS:
        raise ValueError(f"unknown id kind {kind!r}; expected one of {sorted(_KNOWN_KINDS)}")

    prefix = f"{kind}-"
    highest = 0
    for existing in existing_ids:
        if not existing.startswith(prefix):
            continue
        suffix = existing[len(prefix) :]
        if suffix.isdigit():
            highest = max(highest, int(suffix))
    return f"{prefix}{highest + 1:04d}"


def allocate_id(kind: str, directory: Path) -> str:
    """Scans `directory` for existing `<kind>-nnnn` ids and allocates the next one.

    Matches on filename stems (e.g. `ADR-0007.yaml` -> `ADR-0007`) so it
    works directly against a `decisions/`/`proposals/`/`changes/` directory
    once those exist, without the caller having to parse anything first.
    """
    pattern = re.compile(_ID_RE_TEMPLATE.format(kind=re.escape(kind)))
    existing: list[str] = []
    if directory.exists():
        for path in directory.iterdir():
            match = pattern.match(path.stem)
            if match:
                existing.append(match.group(1))
    return next_id(kind, existing)


def render_citation(record_id: str, claim: str) -> str:
    """Renders a citation as `ID (claim)` (spec Sec.3 D3).

    "Every citation MUST carry the claim it stands for" - this is the one
    place that rendering happens, so every command that shows a citation
    goes through it instead of hand-formatting `f"{id} ({claim})"` itself.
    """
    return f"{record_id} ({claim})"
