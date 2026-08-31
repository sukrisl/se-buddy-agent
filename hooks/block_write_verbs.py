"""PreToolUse hook: blocks any `se-buddy write-*` Bash invocation except
`write-propose` (spec Sec.10.1, Sec.7.3).

Spec Sec.10.1, verbatim: "any invocation matching the `se-buddy write`
prefix, except `write propose`." The matcher (a Claude Code `PreToolUse`
matcher only filters by tool name, confirmed against current docs) cannot
express that exception itself, so it lives in this script's own logic -
matched broadly and deliberately, since spec Sec.7.3 itself warns that "a
hook matching a drifting list of verb names is a hook that stops working
quietly."

Matched as two independent checks - "does this command mention se-buddy
at all" and "does this command contain a write-* verb at all" - rather
than one regex requiring them adjacent. A code review found the original
single pattern (`se-buddy(\\.cmd)?\\s+write-(\\w+)`) required `write-` to
follow `se-buddy`/`se-buddy.cmd` with nothing but whitespace between them,
missing both `se-buddy --model x.aird write-apply ...` (flags in between)
and the module-invocation form `python -m se_buddy write-apply ...`
(underscore, no literal "se-buddy" token at all). Splitting the check
trades a small false-positive risk (blocking a command that happens to
mention both "se_buddy"/"se-buddy" and "write-something" for unrelated
reasons) for much better recall - the correct tradeoff for a defence-in-
depth hook whose only job is to catch attempts the TTY gate would refuse
anyway.

This is the second, necessary-but-not-sufficient defence layer (spec
Sec.2.3): `se_buddy.gate`'s TTY check is what actually matters and cannot
be bypassed by reloading a stale hook; this hook's job is to make the
write attempt visible and stop it early, not to be the last word.
"""

from __future__ import annotations

import json
import re
import sys

_HAS_SE_BUDDY = re.compile(r"se[-_]buddy", re.IGNORECASE)
_WRITE_VERB = re.compile(r"\bwrite-(\w+)\b", re.IGNORECASE)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    command = (payload.get("tool_input") or {}).get("command") or ""

    if not _HAS_SE_BUDDY.search(command):
        return 0

    for match in _WRITE_VERB.finditer(command):
        verb = match.group(1).lower()
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
