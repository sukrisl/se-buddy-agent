"""Command dispatch for `se-buddy` (spec Sec.7.3).

Phase 1 wires up every automatic-authority read verb except `memory`,
`register`, `perspective`, `validate`, `followup`, `plan`, `baseline` and
`export` - those need registers, records or the write path that arrive in
later phases. Every `write` verb is Phase 2/3.
"""

from __future__ import annotations

import argparse
import warnings

from se_buddy import doctor
from se_buddy.commands import asks, inspect, search, show, trace

# capellambse warns (FutureWarning) on every access to a deprecated alias or
# an absent-but-not-erroring field (e.g. `.name` on a class that has none -
# spec research finding: this never raises, it warns and returns ""). Our
# commands introspect broadly across arbitrary element types on purpose
# (spec Sec.2.2: behavioural elements are read generically, not judged
# per-class), so this fires constantly and is expected, not a defect to
# surface on every run - D4's "one screen" ethos means it should not drown
# the actual answer. `show`'s relationship scan turns it back into an error
# locally where the warning itself is the useful signal (excluding
# deprecated aliases from the relationship list); this is the default for
# everything else.
warnings.filterwarnings("ignore", category=FutureWarning)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="se-buddy")
    sub = parser.add_subparsers(dest="command", required=True)
    for module in (doctor, inspect, search, show, trace, asks):
        module.add_parser(sub)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
