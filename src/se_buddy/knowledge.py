"""`se-buddy/knowledge.yaml` (spec Sec.5.2, Sec.9): CONFIRM and REVIEW
answers, with provenance.

Append-only (MEMORY layer, spec Sec.5.2) - a row here is never rewritten
or removed, only added to, since it records what an engineer actually
said at a point in time. Written only by `write_answer.answer_ask()`
(spec Sec.7.3: `write answer` is the one verb that populates it).
"""

from __future__ import annotations

from pathlib import Path

import yaml

from se_buddy.atomic_write import atomic_write_text

REQUIRED_FIELDS = ("ask_id", "act", "answer", "date", "provenance")


def knowledge_path(root: Path) -> Path:
    return root / "se-buddy" / "knowledge.yaml"


def load_knowledge(root: Path) -> list[dict]:
    path = knowledge_path(root)
    if not path.exists():
        return []
    return (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("rows") or []


def append_knowledge_row(root: Path, row: dict) -> None:
    """Appends one row (spec Sec.9: "the ASK-nnnn answered, the act (CONFIRM
    or REVIEW), the answer, date, provenance" - all required, "the ask id
    is required - a fact with no provenance is not citable under C01").
    """
    for field in REQUIRED_FIELDS:
        if not row.get(field):
            raise ValueError(f"{field} is required on a knowledge.yaml row (spec Sec.9)")

    rows = load_knowledge(root)
    rows.append(row)
    path = knowledge_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(path, yaml.safe_dump({"rows": rows}, sort_keys=False, allow_unicode=True))
