"""Persisted asks (spec Sec.3 D8, Sec.11's Phase 2 gate).

"An ask raised in one session is closed in another" needs a *stable*
`ASK-nnnn` id across sessions. `se-buddy/asks.yaml` gives an automatically
-detected gap (currently: profile-completeness gaps from
`se_buddy.profile`) that stable id, the first time it's seen.

Persisting a gap's existence is not TTY-gated: it records an observable
fact (this file is missing this field), asserting no engineering content
the agent invented - the same carve-out `write propose` already gets
(spec Sec.7.3: "a proposal asserts what *could* be done, not what is
true"). *Answering* a persisted ask is a different, gated action
(`se-buddy write answer`, `src/se_buddy/commands/write_answer.py`).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml

from se_buddy.memory import next_id
from se_buddy.profile import ProfileGap

STORE_FILENAME = "asks.yaml"


def store_path(root: Path) -> Path:
    return root / "se-buddy" / STORE_FILENAME


def _load(root: Path) -> dict:
    path = store_path(root)
    if not path.exists():
        return {}
    return (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("asks") or {}


def _save(root: Path, asks: dict) -> None:
    path = store_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump({"asks": asks}, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def sync_profile_gaps(root: Path, gaps: list[ProfileGap], today: str | None = None) -> dict:
    """Reconciles persisted asks against the current profile gaps.

    Allocates a stable `ASK-nnnn` for every gap seen for the first time
    (matched on `object`, which is deterministic for the same underlying
    condition), and auto-resolves any persisted, still-open ask whose gap
    has since cleared - distinct from a real engineer answer: `act` on the
    resolution is `"auto-resolved"`, never one of the seven D8 acts, so
    nothing here can be mistaken for a human having answered anything.
    """
    today = today or date.today().isoformat()
    asks = _load(root)
    current_objects = {gap.object for gap in gaps}

    for ask in asks.values():
        if ask.get("answered") is None and ask["object"] not in current_objects:
            ask["answered"] = {"date": today, "act": "auto-resolved", "where": "condition cleared"}

    open_objects = {a["object"] for a in asks.values() if a.get("answered") is None}
    for gap in gaps:
        if gap.object in open_objects:
            continue
        ask_id = next_id("ASK", asks.keys())
        asks[ask_id] = {
            "act": gap.act,
            "object": gap.object,
            "done_when": gap.done_when,
            "blocks": gap.blocks,
            "default": gap.default,
            "raised": today,
            "answered": None,
        }

    _save(root, asks)
    return asks


def all_asks(root: Path) -> dict:
    return _load(root)


def open_asks(root: Path) -> dict:
    return {aid: a for aid, a in _load(root).items() if a.get("answered") is None}


def get_ask(root: Path, ask_id: str) -> dict | None:
    return _load(root).get(ask_id)


def mark_answered(root: Path, ask_id: str, act: str, where: str, today: str | None = None) -> dict:
    today = today or date.today().isoformat()
    asks = _load(root)
    if ask_id not in asks:
        raise KeyError(ask_id)
    asks[ask_id]["answered"] = {"date": today, "act": act, "where": where}
    _save(root, asks)
    return asks[ask_id]


def set_sequence(root: Path, ask_id: str, sequence: int) -> None:
    asks = _load(root)
    if ask_id not in asks:
        raise KeyError(ask_id)
    asks[ask_id]["sequence"] = sequence
    _save(root, asks)
