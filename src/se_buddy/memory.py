"""Id allocation and citation rendering (spec Sec.3 D3, D8; Sec.7.2 `memory`).

Pure logic, no write path. `allocate_id` is what a future `se-buddy write
propose`/`write memory`/`write answer` will call to name a new record or
ask; nothing calls it yet in Phase 1 since none of those verbs exist. It is
built now, and unit-tested directly, because every later phase needs it and
the id format (spec Sec.9's `ADR-nnnn` / `CP-nnnn` / `CHANGE-nnnn` /
`ASK-nnnn`) is fixed by the spec, not something to redesign per-writer.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

from se_buddy.schemas import RECORD_KINDS

_ID_RE_TEMPLATE = r"({kind}-\d+)"


def next_id(kind: str, existing_ids: Iterable[str]) -> str:
    """Returns the next sequential id of `kind`, given the ids already in use.

    `id` is allocated on write, stable, and never authored by hand (spec
    Sec.9) - this is the one place that allocation happens, so a record or
    ask always gets its id from here rather than a writer inventing one.
    """
    if kind not in RECORD_KINDS:
        raise ValueError(f"unknown record kind {kind!r}; expected one of {sorted(RECORD_KINDS)}")

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
