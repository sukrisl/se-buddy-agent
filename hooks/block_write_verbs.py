"""PreToolUse hook: blocks any `se-buddy write-*` Bash invocation except
`write-propose` (spec Sec.10.1, Sec.7.3).

Spec Sec.10.1, verbatim: "any invocation matching the `se-buddy write`
prefix, except `write propose`." The matcher (a Claude Code `PreToolUse`
matcher only filters by tool name, confirmed against current docs) cannot
express that exception itself, so it lives in this script's own logic -
matched broadly and deliberately (a substring search for `write-` after
`se-buddy`, not a narrow regex tied to today's exact invocation style),
since spec Sec.7.3 itself warns that "a hook matching a drifting list of
verb names is a hook that stops working quietly."

This is the second, necessary-but-not-sufficient defence layer (spec
Sec.2.3): `se_buddy.gate`'s TTY check is what actually matters and cannot
be bypassed by reloading a stale hook; this hook's job is to make the
write attempt visible and stop it early, not to be the last word.
"""

from __future__ import annotations

import json
import re
import sys

_WRITE_VERB = re.compile(r"se-buddy(\.cmd)?\s+write-(\w+)", re.IGNORECASE)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    command = (payload.get("tool_input") or {}).get("command") or ""

    for match in _WRITE_VERB.finditer(command):
        verb = match.group(2).lower()
        if verb == "propose":
            continue
        print(
            f"se-buddy: `write-{verb}` must be run by the engineer, directly, in their "
            "own interactive terminal (spec Sec.2.3) - the CLI's own TTY gate refuses it "
            "from here too, but this hook stops the attempt before it reaches the CLI at all.",
            file=sys.stderr,
        )
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
