"""`se-buddy write propose draft.yaml` - file a CP (spec Sec.7.3, automatic authority).

**Not TTY-gated.** This is the one write verb the spec explicitly grants
automatic authority (spec Sec.7.3): "a proposal asserts what *could* be
done, not what is true." It still lives under `write` because it does
create a file and should be visible in the transcript - it is just not
behind `se_buddy.gate`.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from se_buddy.commands._common import add_model_argument
from se_buddy.model import ModelResolutionError, resolve_model_path
from se_buddy.proposals import ProposalError, file_cp


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser("write-propose", help="file a CP (spec Sec.7.3, automatic authority)")
    parser.add_argument("draft_file", help="path to a YAML file with the proposal content")
    add_model_argument(parser)
    parser.set_defaults(func=run)


def run(args) -> int:
    draft_path = Path(args.draft_file)
    if not draft_path.exists():
        print(f"se-buddy: {draft_path} does not exist")
        return 1
    draft = yaml.safe_load(draft_path.read_text(encoding="utf-8")) or {}

    root = Path.cwd()
    try:
        aird_path = resolve_model_path(root, args.model)
    except ModelResolutionError as exc:
        print(f"se-buddy: {exc}")
        return 1

    try:
        cp = file_cp(root, draft, aird_path)
    except ProposalError as exc:
        print(f"se-buddy: {exc}")
        return 1

    print(f"filed {cp['id']}")
    return 0
