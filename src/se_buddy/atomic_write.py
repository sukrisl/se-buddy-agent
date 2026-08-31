"""Atomic text writes for every record/register file this codebase owns.

A code review found every writer in this codebase wrote its YAML with a
plain `path.write_text(...)` - not atomic. `write_text` truncates the
target file before writing the new content, so a process killed mid-write
(a crash, `Ctrl-C`, an out-of-disk condition) leaves a truncated, unparsable
file in place of whatever was there before - corrupting a CHANGE record, a
register, or the ask store, not just failing to update it. `os.replace` is
atomic on both POSIX and Windows when the temp file and the target are on
the same volume (guaranteed here: the temp file is written into the
target's own parent directory), so a reader only ever sees the old
complete content or the new complete content, never a partial write.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def atomic_write_text(path: Path, content: str, encoding: str = "utf-8") -> None:
    directory = path.parent
    fd, tmp_name = tempfile.mkstemp(dir=directory, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding=encoding) as handle:
            handle.write(content)
        os.replace(tmp_name, path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise
