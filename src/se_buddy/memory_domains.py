"""`write memory`'s non-register, non-decision domains (spec Sec.7.3):
principles and assumptions (stable-id rows, PROFILE/MEMORY-layer rather
than a spec Sec.6.2 register), and viewpoints/glossary (keyed by a
natural name/term - spec Sec.9 asks for `design_rules`/`priority` on a
viewpoint, nothing that implies an opaque id).

Structurally mirrors `se_buddy.registers` (one file, upsert by key) since
it's the same underlying shape, but kept in its own module: these files
live at `se-buddy/<domain>.yaml`, not under `se-buddy/registers/`, and
`principles`/`viewpoints` are PROFILE layer while `assumptions` is
MEMORY layer (spec Sec.5.2) - a distinction that matters for who's
expected to edit them, even though the code doesn't need to care.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from se_buddy.atomic_write import atomic_write_text
from se_buddy.memory import next_id
from se_buddy.schemas import (
    MEMORY_DOMAIN_PREFIXES,
    validate_glossary_entry,
    validate_memory_row,
    validate_viewpoint,
)


class MemoryDomainError(Exception):
    """A `write memory` row could not be written as given - reported plainly."""


def _domain_path(root: Path, filename: str) -> Path:
    return root / "se-buddy" / f"{filename}.yaml"


def _load_list(path: Path, key: str) -> list[dict]:
    if not path.exists():
        return []
    return (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get(key) or []


def _save_list(path: Path, key: str, items: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(path, yaml.safe_dump({key: items}, sort_keys=False, allow_unicode=True))


# --- principles / assumptions: stable-id rows ---


def load_rows(root: Path, domain: str) -> list[dict]:
    return _load_list(_domain_path(root, domain), domain)


def upsert_row(root: Path, domain: str, row: dict) -> dict:
    """Adds a new row (allocating an id) or updates an existing one by id -
    same shape as `se_buddy.registers.upsert_row`, for the same reason: an
    assumption's `status` moves from unverified to confirmed without
    becoming a different assumption.

    Rows with no `id` are preserved across the save - a code review found
    the original version built `by_id` from only the id-bearing rows and
    then saved `by_id.values()` alone, so any row that had somehow lost or
    never had an id (e.g. hand-edited YAML) was silently dropped the next
    time anyone wrote to this domain.
    """
    if domain not in MEMORY_DOMAIN_PREFIXES:
        raise MemoryDomainError(
            f"unknown memory domain {domain!r}; expected one of {sorted(MEMORY_DOMAIN_PREFIXES)}"
        )

    rows = load_rows(root, domain)
    unidentified = [r for r in rows if not r.get("id")]
    by_id = {r["id"]: r for r in rows if r.get("id")}

    row_id = row.get("id")
    if row_id:
        if row_id not in by_id:
            raise MemoryDomainError(f"{row_id!r} does not exist in {domain} - nothing to update")
    else:
        row_id = next_id(MEMORY_DOMAIN_PREFIXES[domain], by_id.keys())
        row = {**row, "id": row_id}

    result = validate_memory_row(domain, row)
    if not result.ok:
        raise MemoryDomainError(
            f"row for {domain} failed validation:\n" + "\n".join(f"  - {e}" for e in result.errors)
        )

    by_id[row_id] = row
    _save_list(_domain_path(root, domain), domain, unidentified + list(by_id.values()))
    return row


def find_row(root: Path, domain: str, row_id: str) -> dict | None:
    for row in load_rows(root, domain):
        if row.get("id") == row_id:
            return row
    return None


# --- viewpoints: keyed by name ---


def load_viewpoints(root: Path) -> list[dict]:
    return _load_list(_domain_path(root, "viewpoints"), "viewpoints")


def upsert_viewpoint(root: Path, viewpoint: dict) -> dict:
    result = validate_viewpoint(viewpoint)
    if not result.ok:
        raise MemoryDomainError(
            "viewpoint failed validation:\n" + "\n".join(f"  - {e}" for e in result.errors)
        )
    viewpoints = load_viewpoints(root)
    by_name = {v["name"]: v for v in viewpoints}
    by_name[viewpoint["name"]] = viewpoint
    _save_list(_domain_path(root, "viewpoints"), "viewpoints", list(by_name.values()))
    return viewpoint


# --- glossary: keyed by term ---


def load_glossary(root: Path) -> list[dict]:
    return _load_list(_domain_path(root, "glossary"), "glossary")


def upsert_glossary_entry(root: Path, entry: dict) -> dict:
    result = validate_glossary_entry(entry)
    if not result.ok:
        raise MemoryDomainError(
            "glossary entry failed validation:\n" + "\n".join(f"  - {e}" for e in result.errors)
        )
    entries = load_glossary(root)
    by_term = {e["term"]: e for e in entries}
    by_term[entry["term"]] = entry
    _save_list(_domain_path(root, "glossary"), "glossary", list(by_term.values()))
    return entry
