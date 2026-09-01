"""Command dispatch for `se-buddy` (spec Sec.7.3).

Phase 3 adds `write-propose` (automatic authority - the one write verb
with no TTY gate, spec Sec.7.3), `plan`, `write-apply`, `write-record`,
`write-revert`, `validate`, `followup`. Still missing: `perspective` and
`export` - flagged, not built, per SPEC-COVERAGE.md (both were explicit,
scoped decisions, not oversights).

`write-profile` and `write-domain` (AC-0008) are the init-time pair: they
replaced hand-editing `se-buddy/profile.yaml` and `se-buddy/domain.md` in a
text editor, which was the one authoring path in this codebase that had no
verb behind it at all.

Every `write-*` verb except `write-propose` is TTY-gated (spec Sec.2.3,
`se_buddy.gate`) - it will refuse when run from here, or from any other
non-interactive shell.
"""

from __future__ import annotations

import argparse
import warnings

from se_buddy import doctor
from se_buddy.commands import (
    asks,
    baseline,
    followup,
    inspect,
    memory,
    plan,
    register,
    search,
    show,
    trace,
    validate,
    write_answer,
    write_apply,
    write_baseline,
    write_claude_md,
    write_domain,
    write_memory,
    write_profile,
    write_propose,
    write_record,
    write_register,
    write_revert,
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
        plan,
        validate,
        followup,
        write_profile,
        write_domain,
        write_claude_md,
        write_register,
        write_answer,
        write_baseline,
        write_memory,
        write_propose,
        write_apply,
        write_record,
        write_revert,
    ):
        module.add_parser(sub)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
