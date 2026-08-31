"""PreToolUse hook: blocks Edit/Write on `*.capella`/`*.aird` (spec Sec.10.1).

"The first alone is not a guard. It stops the two tools that name a file
and leaves every other route open - and it says nothing about the CLI,
which is the route that actually modifies the model." This hook is
exactly that first, necessary-but-not-sufficient layer; `se_buddy.gate`
(spec Sec.2.3) is the layer that actually matters. Neither is sufficient
alone.

Python, not shell - this project's own portability rule (spike 5, spec
Sec.12): a shebang script does not execute natively on Windows, and
Python 3.11+ is already this project's hard floor, so it costs nothing
extra to require here too.

Reads Claude Code's `PreToolUse` JSON from stdin (`tool_input.file_path`).
Exits 2 with a stderr message to block; 0 to allow. Malformed/unexpected
input fails *open* (exit 0) rather than blocking every Edit/Write in the
session - this hook's only job is `.capella`/`.aird`, and refusing to be
sure about anything else is not this hook's call to make.
"""

from __future__ import annotations

import json
import sys


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    file_path = (payload.get("tool_input") or {}).get("file_path") or ""
    normalized = file_path.replace("\\", "/").lower()

    if normalized.endswith(".capella") or normalized.endswith(".aird"):
        print(
            "se-buddy: .capella/.aird files are never edited directly (spec Sec.10.1) - "
            "use `se-buddy write propose` and `se-buddy write apply` instead.",
            file=sys.stderr,
        )
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
