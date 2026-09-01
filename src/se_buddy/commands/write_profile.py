"""`se-buddy write-profile [fields.yaml]` (spec Sec.5.3).

The verb that ends `profile.yaml`'s hand-editing. `project-init` used to
scaffold four empty keys and send the engineer to a text editor, because
spec Sec.5's "nothing project-specific belongs in agent-authored content"
was read as covering this file. It does cover `domain.md`, which is
judgement. It does not cover four values already written down in the
project's own `.capella`, `.aird` and `.project` - reading those is
retrieval, and the file the values land in asserts nothing on its own.

So this verb detects them (`se_buddy.profile_detect`), shows each one with
the file it was read from, and writes only what a human confirms at a
terminal. TTY-gated like every other write verb (spec Sec.2.3): the agent
can propose the whole thing and still cannot commit any of it.

With no argument it writes what detection found. With a YAML file it writes
that instead, which is the override path for a project whose preferred
`project_name` is not the one Eclipse recorded - the common case, not an
escape hatch.

`write_fields()` (validation + write) and `run()` (detection + gate + CLI)
are separate on purpose: tests call `write_fields()` directly, never
`run()` - the same pattern as every other write verb here.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from se_buddy.gate import GateRefused, confirm
from se_buddy.profile import (
    REQUIRED_PROFILE_FIELDS,
    ProfileWriteError,
    write_profile,
)
from se_buddy.profile_detect import detect


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser(
        "write-profile",
        help="write se-buddy/profile.yaml from the project's own files (spec Sec.5.3)",
    )
    parser.add_argument(
        "fields_file",
        nargs="?",
        default=None,
        help="optional YAML with the four fields; omit to use what detection found",
    )
    parser.set_defaults(func=run)


def write_fields(root: Path, fields: dict) -> Path:
    return write_profile(root, fields)


def run(args) -> int:
    root = Path.cwd()

    if args.fields_file:
        path = Path(args.fields_file)
        if not path.exists():
            print(f"se-buddy: {path} does not exist")
            return 1
        fields = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        source_lines = [f"{f}: {fields.get(f, '<missing>')}" for f in REQUIRED_PROFILE_FIELDS]
        origin = str(path)
    else:
        detection = detect(root)
        fields = detection.as_dict()
        source_lines = detection.rendered()
        origin = "this project's own files"

        undetermined = detection.undetermined()
        if undetermined:
            # Refusing here rather than writing a partial profile: a file
            # with three of four fields set reads as configured and fails
            # later, further from the cause. The provenance lines above
            # already say what was looked at and why it came up empty.
            print(f"se-buddy: could not determine {', '.join(undetermined)} from {root}:")
            for line in source_lines:
                print(f"  {line}")
            print(
                "\nse-buddy: pass a YAML file with the four fields instead - "
                "`se-buddy write-profile fields.yaml`"
            )
            return 1

    print(f"About to write se-buddy/profile.yaml from {origin}:")
    for line in source_lines:
        print(f"  {line}")
    print()

    try:
        confirm("Write these four fields to se-buddy/profile.yaml?")
    except GateRefused as exc:
        print(f"se-buddy: {exc}")
        return 1

    try:
        written = write_fields(root, fields)
    except ProfileWriteError as exc:
        print(f"se-buddy: {exc}")
        return 1

    print(f"wrote {written}")
    return 0
