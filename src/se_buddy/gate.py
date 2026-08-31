"""The write-verb confirmation gate (spec Sec.2.3).

"MUST. `--authorized-by` alone enforces nothing... Every writing verb
therefore refuses unless stdin is a TTY and the engineer types a
confirmation the agent never sees."

The load-bearing property here isn't the cleverness of the confirmation
text - it's that an agent's own tool-call shell never has an interactive
stdin/stdout in the first place (this Bash tool included: commands run
non-interactively, with no human at the other end of stdin). So the real
gate is `isatty()`: false for every agent-issued command by construction,
true only when a human runs `se-buddy write ...` themselves, directly, in
their own terminal. The typed confirmation past that point is a
deliberate-action safeguard against an accidental keystroke, not the
primary defence.

Spec Sec.2.3, verbatim: "A flag that bypasses the gate for testing MUST
NOT exist; that flag is the whole hole, re-opened." There is accordingly
no override parameter anywhere in this module, under any name. Tests
exercise the write logic beneath this gate directly - never this function
- exactly as spec Sec.2.3 accepts: "apply, revert and the other write
verbs cannot run non-interactively - not in CI, and not in the agent's own
test suite."

The second layer of defence (a `PreToolUse` hook on `Bash`, spec Sec.10.1)
is Phase 3. This module is the CLI-side half only, which is what spec
Sec.11 lists for Phase 2. Sec.2.3 is explicit that neither layer is
sufficient alone - a project running this phase without Phase 3's hook
yet is running with only the first of the two defences.
"""

from __future__ import annotations

import sys


class GateRefused(Exception):
    """A write verb was refused by the TTY gate."""


def confirm(action: str, expected: str = "yes") -> None:
    """Refuses unless run at a real interactive terminal, then requires a
    typed confirmation. Raises `GateRefused` on any failure to confirm -
    never returns anything to indicate a "soft" no; the caller's write
    simply does not happen.
    """
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        raise GateRefused(
            f"{action} needs a human at an interactive terminal - this session's "
            "stdin/stdout isn't one. Run this command yourself, directly, not "
            "through an agent, script, or CI job."
        )

    print(action)
    print(f"Type {expected!r} to confirm, anything else to cancel:")
    response = input("> ")
    if response != expected:
        raise GateRefused(f"{action} - cancelled, confirmation text did not match")
