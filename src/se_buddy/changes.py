"""CHANGE-nnnn records and followup checklists (spec Sec.6.1, Sec.9, Sec.10.3).

One file per record (`se-buddy/changes/CHANGE-nnnn.yaml`), plus a
schema-validated followup checklist as its own file
(`CHANGE-nnnn.followup.yaml`) rather than embedded prose - spec Sec.6.1:
"the one place items are most likely to be lost would be the one place
enforcement was cosmetic."

Every followup entry is an ask in the D8 shape with `act: DRAW` and its
own `ASK-nnnn` (spec Sec.10.3) - allocated from the *same* id space
`se_buddy.ask_store` uses, since both are "every open ask" as far as
`se-buddy asks`/`write answer` are concerned, even though they're stored
in different files (spec Sec.6.1's followup file vs Sec.3 D8's asks.yaml
for automatically-detected gaps).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml

from se_buddy.ask_store import all_asks
from se_buddy.memory import next_id
from se_buddy.schemas import validate_ask, validate_change


class ChangeError(Exception):
    """A CHANGE could not be filed as given - reported plainly."""


def changes_dir(root: Path) -> Path:
    return root / "se-buddy" / "changes"


def change_path(root: Path, change_id: str) -> Path:
    return changes_dir(root) / f"{change_id}.yaml"


def followup_path(root: Path, change_id: str) -> Path:
    return changes_dir(root) / f"{change_id}.followup.yaml"


def _all_used_ask_ids(root: Path) -> set[str]:
    """Every `ASK-nnnn` currently allocated anywhere - `asks.yaml` plus
    every existing followup checklist - so a new followup entry's id can
    never collide with either.
    """
    ids = set(all_asks(root).keys())
    directory = changes_dir(root)
    if directory.exists():
        for path in directory.glob("*.followup.yaml"):
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            for item in data.get("followup", []):
                if item.get("id"):
                    ids.add(item["id"])
    return ids


def file_change(root: Path, change_id: str, change: dict, followup: list[dict]) -> dict:
    """Writes `CHANGE-nnnn.yaml` and `CHANGE-nnnn.followup.yaml` together.

    `change_id` is supplied by the caller (`apply_lifecycle`/`write_record`
    both allocate it themselves, since they need it before this point too
    - to name the snapshot directory, for instance) rather than allocated
    here, unlike every other record kind in this codebase.
    """
    if (change_path(root, change_id)).exists():
        raise ChangeError(f"{change_id} already exists - a CHANGE is never rewritten (spec Sec.6.1)")

    change = {**change, "id": change_id}
    result = validate_change(change)
    if not result.ok:
        raise ChangeError(
            "CHANGE failed validation:\n" + "\n".join(f"  - {e}" for e in result.errors)
        )

    used_ids = _all_used_ask_ids(root)
    followup_with_ids = []
    for i, item in enumerate(followup):
        item = dict(item)
        item.setdefault("act", "DRAW")
        if not item.get("id"):
            item["id"] = next_id("ASK", used_ids)
            used_ids.add(item["id"])
        item.setdefault("answered", None)
        item_result = validate_ask(item)
        if not item_result.ok:
            raise ChangeError(
                f"followup item {i} failed validation:\n"
                + "\n".join(f"  - {e}" for e in item_result.errors)
            )
        followup_with_ids.append(item)

    directory = changes_dir(root)
    directory.mkdir(parents=True, exist_ok=True)
    change_path(root, change_id).write_text(
        yaml.safe_dump(change, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    followup_path(root, change_id).write_text(
        yaml.safe_dump({"followup": followup_with_ids}, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return change


def load_change(root: Path, change_id: str) -> dict | None:
    path = change_path(root, change_id)
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_followup(root: Path, change_id: str) -> list[dict]:
    path = followup_path(root, change_id)
    if not path.exists():
        return []
    return (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("followup") or []


def open_followup_items(root: Path) -> list[tuple[str, dict]]:
    """Every unticked `(change_id, item)` across every followup checklist -
    what `se-buddy asks` merges in alongside `ask_store`'s asks.
    """
    directory = changes_dir(root)
    if not directory.exists():
        return []
    found = []
    for path in sorted(directory.glob("*.followup.yaml")):
        change_id = path.name.removesuffix(".followup.yaml")
        for item in load_followup(root, change_id):
            if item.get("answered") is None:
                found.append((change_id, item))
    return found


def find_followup_item(root: Path, ask_id: str) -> tuple[str, dict] | None:
    """Searches every followup checklist for `ask_id`, ticked or not -
    `write_answer` needs to distinguish "not a DRAW ask at all" from
    "already ticked," which an open-only search can't do. Returns
    `(change_id, item)`.
    """
    directory = changes_dir(root)
    if not directory.exists():
        return None
    for path in sorted(directory.glob("*.followup.yaml")):
        change_id = path.name.removesuffix(".followup.yaml")
        for item in load_followup(root, change_id):
            if item["id"] == ask_id:
                return change_id, item
    return None


def mark_followup_item_done(root: Path, change_id: str, ask_id: str, today: str | None = None) -> dict:
    today = today or date.today().isoformat()
    items = load_followup(root, change_id)
    for item in items:
        if item["id"] == ask_id:
            item["answered"] = {"date": today, "act": "DRAW", "where": f"{change_id}.followup.yaml"}
            followup_path(root, change_id).write_text(
                yaml.safe_dump({"followup": items}, sort_keys=False, allow_unicode=True),
                encoding="utf-8",
            )
            return item
    raise ChangeError(f"{ask_id} is not in {change_id}'s followup checklist")


def followup_all_ticked(root: Path, change_id: str) -> bool:
    return all(item.get("answered") is not None for item in load_followup(root, change_id))


def any_followup_open(root: Path) -> bool:
    """spec Sec.10.3: `apply` MUST refuse while any followup checklist is
    unticked - across *every* CHANGE, not just the most recent one.
    """
    return bool(open_followup_items(root))
