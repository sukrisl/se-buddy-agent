"""`se-buddy memory <domain> [text]` (spec Sec.7.3, automatic authority)."""

from __future__ import annotations

from pathlib import Path

from se_buddy.commands._common import add_limit_argument, truncate
from se_buddy.decisions import decisions_dir, load_adr
from se_buddy.knowledge import load_knowledge
from se_buddy.memory_domains import load_glossary, load_rows, load_viewpoints

DOMAINS = ("principles", "viewpoints", "glossary", "assumptions", "knowledge", "decisions")


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser(
        "memory", help="principles/viewpoints/glossary/assumptions/knowledge/decisions"
    )
    parser.add_argument("domain", choices=DOMAINS)
    parser.add_argument("filter", nargs="?", default=None, help="substring to match")
    add_limit_argument(parser)
    parser.set_defaults(func=run)


def run(args) -> int:
    root = Path.cwd()

    if args.domain == "decisions":
        directory = decisions_dir(root)
        ids = sorted(p.stem for p in directory.glob("ADR-*.yaml")) if directory.exists() else []
        if args.filter:
            ids = [i for i in ids if args.filter.lower() in i.lower()]
        shown, truncated = truncate(ids, args.limit)
        for adr_id in shown:
            adr = load_adr(root, adr_id) or {}
            print(f"{adr_id}: {adr.get('claim', '')}")
        _print_count(shown, truncated, len(ids), args.limit)
        return 0

    if args.domain == "knowledge":
        rows = load_knowledge(root)
    elif args.domain == "viewpoints":
        rows = load_viewpoints(root)
    elif args.domain == "glossary":
        rows = load_glossary(root)
    else:
        rows = load_rows(root, args.domain)

    if args.filter:
        needle = args.filter.lower()
        rows = [r for r in rows if needle in str(r).lower()]

    shown, truncated = truncate(rows, args.limit)
    for row in shown:
        print(_summarize(args.domain, row))
    _print_count(shown, truncated, len(rows), args.limit)
    return 0


def _summarize(domain: str, row: dict) -> str:
    if domain == "viewpoints":
        return f"{row.get('name')}: priority {row.get('priority')} - {row.get('design_rules')}"
    if domain == "glossary":
        return f"{row.get('term')}: {row.get('definition')}"
    if domain == "knowledge":
        return f"{row.get('ask_id')} [{row.get('act')}]: {row.get('answer')}"
    return f"{row.get('id', '?')} [{row.get('status', '?')}]: {row.get('statement', '')}"


def _print_count(shown, truncated, total, limit) -> None:
    if truncated:
        print(f"{len(shown)} shown, truncated from {total} (--limit {limit})")
    else:
        print(f"{len(shown)} shown")
