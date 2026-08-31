"""`se-buddy register <name> [filter]` - any register of spec Sec.6.2 (spec Sec.7.3, automatic authority)."""

from __future__ import annotations

from pathlib import Path

from se_buddy.commands._common import add_limit_argument, truncate
from se_buddy.registers import RegisterError, load_register
from se_buddy.schemas import REGISTER_PREFIXES


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser("register", help="any register of spec Sec.6.2")
    parser.add_argument("name", choices=sorted(REGISTER_PREFIXES), help="which register")
    parser.add_argument("filter", nargs="?", default=None, help="substring to match against claim/status")
    add_limit_argument(parser)
    parser.set_defaults(func=run)


def run(args) -> int:
    try:
        rows = load_register(Path.cwd(), args.name)
    except RegisterError as exc:
        print(f"se-buddy: {exc}")
        return 1

    items = list(rows.values())
    if args.filter:
        needle = args.filter.lower()
        items = [r for r in items if needle in f"{r.get('claim', '')} {r.get('status', '')}".lower()]

    shown, truncated = truncate(items, args.limit)
    for row in shown:
        print(f"{row['id']} [{row.get('status', '?')}] {row.get('claim', '')}")
    if truncated:
        print(f"{len(shown)} shown, truncated from {len(items)} (--limit {args.limit})")
    else:
        print(f"{len(shown)} shown")
    return 0
