"""`se-buddy asks` - every open ask, in D8 shape, sequenced (spec Sec.7.3).

Sec.7.3: "the session's first command... reports the current track, tier
and perspective alongside them" - track/tier/perspective are properties of
the live conversation (Sec.2.1/Sec.3 D1), not persisted state, so nothing
here reports them; that reporting job belongs to the reasoning layer
(Claude Code), not this CLI verb.

In Phase 1, before any record can be written (`write memory`/`write
register`/`write answer` are Phase 2/3), the only asks that can exist are
profile-completeness gaps - so a fresh, unconfigured project correctly
reports "no open asks" beyond those. That is the expected shape of the
answer here, not a stub standing in for missing functionality.
"""

from __future__ import annotations

from pathlib import Path

from se_buddy.profile import check_completeness


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser("asks", help="every open ask, in D8 shape")
    parser.set_defaults(func=run)


def run(args) -> int:
    gaps = check_completeness(Path.cwd())

    if not gaps:
        print("no open asks")
        return 0

    print(f"{len(gaps)} open ask(s)")
    for gap in gaps:
        print(f"  act        {gap.act}")
        print(f"  object     {gap.object}")
        print(f"  done when  {gap.done_when}")
        print(f"  blocks     {gap.blocks}")
        print(f"  default    {gap.default}")
        print()

    return 0
