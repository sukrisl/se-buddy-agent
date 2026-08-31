"""`se-buddy followup` - manual diagram work still owed, rendered as Markdown (spec Sec.6.1, Sec.7.3).

Spec Sec.6.1: "`se-buddy followup` renders them as Markdown on demand; the
readable form is generated, not stored." The underlying data stays
schema-validated YAML (`se_buddy.changes`) - this command is the render
step, never a second place the data itself lives.
"""

from __future__ import annotations

from pathlib import Path

from se_buddy.changes import changes_dir, load_followup


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser("followup", help="manual diagram work still owed, rendered as Markdown")
    parser.set_defaults(func=run)


def run(args) -> int:
    root = Path.cwd()
    directory = changes_dir(root)
    change_ids = sorted(p.name.removesuffix(".followup.yaml") for p in directory.glob("*.followup.yaml")) if directory.exists() else []

    if not change_ids:
        print("no followup checklists exist yet")
        return 0

    for change_id in change_ids:
        items = load_followup(root, change_id)
        if not items:
            continue
        print(f"## {change_id}\n")
        for item in items:
            box = "x" if item.get("answered") is not None else " "
            print(f"- [{box}] {item['id']}: {item['object']} - {item['done_when']}")
        print()

    return 0
