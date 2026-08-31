"""Command dispatch for `se-buddy` (spec Sec.7.3).

Phase 2 (plus its second pass) adds `register`/`write-register`,
`write-answer`, `baseline`/`write-baseline`, and `memory`/`write-memory`
(principles/viewpoints/glossary/assumptions/decisions - `knowledge` is
read-only here, populated only via `write-answer`). Still missing:
`perspective`, `validate`, `followup`, `plan`, `export`, and every
modelling-track write verb (`write-propose`/`write-apply`/`write-record`/
`write-revert`) - see SPEC-COVERAGE.md for which of those are genuinely
unassigned to any phase in the spec's own phasing table, versus scoped to
Phase 3.

Every `write-*` verb is TTY-gated (spec Sec.2.3, `se_buddy.gate`) - it
will refuse when run from here, or from any other non-interactive shell.
"""

from __future__ import annotations

import argparse
import warnings

from se_buddy import doctor
from se_buddy.commands import (
    asks,
    baseline,
    inspect,
    memory,
    register,
    search,
    show,
    trace,
    write_answer,
    write_baseline,
    write_memory,
    write_register,
)

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
    for module in (
        doctor,
        inspect,
        search,
        show,
        trace,
        asks,
        register,
        baseline,
        memory,
        write_register,
        write_answer,
        write_baseline,
        write_memory,
    ):
        module.add_parser(sub)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
