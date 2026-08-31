"""`se-buddy write memory <domain> d.yaml` (spec Sec.7.3).

Domains: `principles`, `viewpoints`, `glossary`, `assumptions`,
`decisions`. Deliberately not `knowledge`: spec Sec.9 requires every
`knowledge.yaml` row to carry the `ASK-nnnn` it answers, which only
`write answer`'s `CONFIRM`/`REVIEW` path supplies - a direct `write
memory knowledge` would have no ask id to satisfy that with (see
SPEC-COVERAGE.md's design note on this).

TTY-gated (spec Sec.2.3). `write_content()` (dispatch + validation) and
`run()` (gate + CLI wrapper) are separate on purpose: tests call
`write_content()` directly, never `run()` - the same pattern as every
other write verb in this codebase.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from se_buddy.decisions import DecisionError, file_adr
from se_buddy.gate import GateRefused, confirm
from se_buddy.memory_domains import MemoryDomainError, upsert_glossary_entry, upsert_row, upsert_viewpoint

DOMAINS = ("principles", "viewpoints", "glossary", "assumptions", "decisions")


class WriteMemoryError(Exception):
    """A `write memory` request could not be satisfied - reported plainly."""


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser(
        "write-memory", help="principles/viewpoints/glossary/assumptions/decisions (spec Sec.7.3)"
    )
    parser.add_argument("domain", choices=DOMAINS)
    parser.add_argument("content_file", help="path to a YAML file with the content to write")
    parser.set_defaults(func=run)


def write_content(root: Path, domain: str, content: dict) -> dict:
    try:
        if domain == "decisions":
            return file_adr(root, content)
        if domain == "viewpoints":
            return upsert_viewpoint(root, content)
        if domain == "glossary":
            return upsert_glossary_entry(root, content)
        if domain in ("principles", "assumptions"):
            return upsert_row(root, domain, content)
    except (DecisionError, MemoryDomainError) as exc:
        raise WriteMemoryError(str(exc)) from exc
    raise WriteMemoryError(
        f"unknown domain {domain!r}; expected one of {DOMAINS} "
        "('knowledge' goes through `write answer` instead, not `write memory`)"
    )


def run(args) -> int:
    path = Path(args.content_file)
    if not path.exists():
        print(f"se-buddy: {path} does not exist")
        return 1
    content = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    summary = (
        content.get("claim")
        or content.get("name")
        or content.get("term")
        or content.get("statement")
        or "<no summary given>"
    )
    try:
        confirm(f"About to write memory: {args.domain} - {summary}")
    except GateRefused as exc:
        print(f"se-buddy: {exc}")
        return 1

    try:
        written = write_content(Path.cwd(), args.domain, content)
    except WriteMemoryError as exc:
        print(f"se-buddy: {exc}")
        return 1

    label = written.get("id") or written.get("name") or written.get("term")
    print(f"wrote {label} to {args.domain}")
    return 0
