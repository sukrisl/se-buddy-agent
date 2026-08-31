"""`se-buddy write baseline <name>` - a manifest and a git tag (spec Sec.6.4, Sec.7.3).

TTY-gated. The manifest-building (`se_buddy.baseline.write_baseline`) is
gate-free and unit-tested directly; the git tag step below needs a real
git repository and is exercised live rather than by unit test - it never
pushes anywhere (spec doesn't ask it to, and pushing is a materially
different, higher-blast-radius action this command has no business
taking).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from se_buddy.baseline import BaselineError, write_baseline
from se_buddy.commands._common import add_model_argument
from se_buddy.gate import GateRefused, confirm
from se_buddy.model import ModelResolutionError, resolve_model_path


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser("write-baseline", help="a manifest and a git tag (spec Sec.6.4)")
    parser.add_argument("name", help="the baseline's name, also used as the git tag")
    parser.add_argument("--force", action="store_true", help="overwrite an existing baseline of the same name")
    add_model_argument(parser)
    parser.set_defaults(func=run)


def run(args) -> int:
    root = Path.cwd()
    try:
        aird_path = resolve_model_path(root, args.model)
    except ModelResolutionError as exc:
        print(f"se-buddy: {exc}")
        return 1

    try:
        confirm(f"About to write baseline {args.name!r} and tag git at HEAD")
    except GateRefused as exc:
        print(f"se-buddy: {exc}")
        return 1

    try:
        path = write_baseline(root, args.name, aird_path, force=args.force)
    except BaselineError as exc:
        print(f"se-buddy: {exc}")
        return 1

    tag = subprocess.run(
        ["git", "tag", args.name], cwd=root, capture_output=True, text=True
    )
    if tag.returncode != 0:
        print(f"se-buddy: wrote {path}, but the git tag failed: {tag.stderr.strip()}")
        return 1

    print(f"wrote {path} and tagged git as {args.name!r}")
    return 0
