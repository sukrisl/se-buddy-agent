"""`se-buddy write-claude-md` (spec Sec.5.2).

Generates the consuming project's thin `CLAUDE.md`, the one Sec.5.2's
project layout asks for and nothing built until now.

Not TTY-gated, and `se_buddy.project_claude_md`'s docstring says why in
full: the file asserts nothing the engineer must judge, and the managed
block cannot destroy anything they wrote. Authority in this codebase
follows what a write can assert and what it can lose - not the fact that it
touches a file.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from se_buddy import project_claude_md
from se_buddy.profile import profile_dir


def add_parser(subparsers) -> None:
    subparsers.add_parser(
        "write-claude-md",
        help="generate the project's thin CLAUDE.md pointing at its profile (spec Sec.5.2)",
    ).set_defaults(func=run)


def run(_args) -> int:
    root = Path.cwd()

    profile_path = profile_dir(root) / "profile.yaml"
    profile = None
    if profile_path.is_file():
        try:
            profile = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            # Worth generating anyway: the block degrades to "the profile is
            # not complete yet", which is both true and the more useful
            # thing to tell a reader than nothing at all.
            print(f"se-buddy: {profile_path} could not be parsed ({exc}) - generating without it")

    path, action = project_claude_md.write(root, profile)
    print(f"{action} the se-buddy block in {path}")
    if not profile:
        print("se-buddy: profile is absent or incomplete - re-run this after `write-profile`")
    return 0
