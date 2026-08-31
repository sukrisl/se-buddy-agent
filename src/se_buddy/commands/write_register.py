"""`se-buddy write register <name> row.yaml` - the only route into a register (spec Sec.6.2, Sec.7.3).

TTY-gated (spec Sec.2.3). The gate check (`gate.confirm`) and the write
logic (`registers.upsert_row`) are deliberately separate calls: tests
exercise `upsert_row` directly (see tests/test_registers.py) and never
this module's `run()`, exactly as spec Sec.2.3 expects ("Tests exercise
the layer beneath the gate directly").
"""

from __future__ import annotations

from pathlib import Path

import yaml

from se_buddy.gate import GateRefused, confirm
from se_buddy.registers import RegisterError, upsert_row
from se_buddy.schemas import REGISTER_PREFIXES


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser("write-register", help="the only route into a register (spec Sec.6.2)")
    parser.add_argument("name", choices=sorted(REGISTER_PREFIXES))
    parser.add_argument("row_file", help="path to a YAML file with the row content")
    parser.set_defaults(func=run)


def run(args) -> int:
    row_path = Path(args.row_file)
    if not row_path.exists():
        print(f"se-buddy: {row_path} does not exist")
        return 1
    row = yaml.safe_load(row_path.read_text(encoding="utf-8")) or {}

    verb = "updating" if row.get("id") else "adding a new row to"
    try:
        confirm(f"About to write register row: {verb} {args.name} - {row.get('claim', '<no claim given>')}")
    except GateRefused as exc:
        print(f"se-buddy: {exc}")
        return 1

    try:
        written = upsert_row(Path.cwd(), args.name, row)
    except RegisterError as exc:
        print(f"se-buddy: {exc}")
        return 1

    print(f"wrote {written['id']} to {args.name}")
    return 0
