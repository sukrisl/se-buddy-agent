"""`se-buddy asks` - every open ask, in D8 shape, sequenced (spec Sec.7.3).

Sec.7.3: "the session's first command... reports the current track, tier
and perspective alongside them" - track/tier/perspective are properties of
the live conversation (Sec.2.1/Sec.3 D1), not persisted state, so nothing
here reports them; that reporting job belongs to the reasoning layer
(Claude Code), not this CLI verb.

Every run reconciles `se-buddy/asks.yaml` against the current profile
gaps first (`ask_store.sync_profile_gaps`) - a gap gets a stable
`ASK-nnnn` the first time it's seen, and auto-resolves once its underlying
condition clears. That reconciliation is what makes "an ask raised in one
session is closed in another" (spec Sec.11's Phase 2 gate) true: the id
this command prints today is the same id `se-buddy write answer` (or a
later `asks` run noticing the gap cleared) will act on tomorrow.
"""

from __future__ import annotations

from pathlib import Path

from se_buddy.ask_store import open_asks, sync_profile_gaps
from se_buddy.profile import check_completeness


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser("asks", help="every open ask, in D8 shape")
    parser.set_defaults(func=run)


def run(args) -> int:
    root = Path.cwd()
    gaps = check_completeness(root)
    sync_profile_gaps(root, gaps)
    open_ = open_asks(root)

    if not open_:
        print("no open asks")
        return 0

    ordered = sorted(open_.items(), key=lambda kv: (kv[1].get("sequence") is None, kv[1].get("sequence", 0), kv[0]))
    print(f"{len(ordered)} open ask(s)")
    for ask_id, ask in ordered:
        print(f"  id         {ask_id}")
        print(f"  act        {ask['act']}")
        print(f"  object     {ask['object']}")
        print(f"  done when  {ask['done_when']}")
        print(f"  blocks     {ask['blocks']}")
        print(f"  default    {ask['default']}")
        if ask.get("sequence") is not None:
            print(f"  sequence   {ask['sequence']}")
        print()

    return 0
