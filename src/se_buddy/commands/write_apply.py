"""`se-buddy write apply CP-nnnn --authorized-by "..."` [--delete] (spec Sec.7.3).

TTY-gated. `apply_cp()` (the full spec Sec.10.2 sequence) and `run()` (the
gate + CLI wrapper) are separate on purpose - tests call `apply_cp()`
directly, never `run()` (spec Sec.2.3's testing philosophy).
"""

from __future__ import annotations

from pathlib import Path

from se_buddy.apply_lifecycle import ApplyError, apply_cp
from se_buddy.commands._common import add_model_argument
from se_buddy.gate import GateRefused, confirm


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser("write-apply", help="apply an authorised proposal (spec Sec.10.2)")
    parser.add_argument("cp_id", help="a CP-nnnn id")
    parser.add_argument(
        "--authorized-by",
        required=True,
        help="only words the engineer actually said, about this proposal (spec Sec.2.3)",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="this proposal deletes model elements - requires the distinct flag (spec Sec.2.3)",
    )
    add_model_argument(parser)
    parser.set_defaults(func=run)


def run(args) -> int:
    root = Path.cwd()

    try:
        confirm(f"About to apply {args.cp_id} - authorized by: {args.authorized_by}")
    except GateRefused as exc:
        print(f"se-buddy: {exc}")
        return 1

    try:
        change = apply_cp(
            root,
            args.cp_id,
            args.authorized_by,
            model_arg=args.model,
            delete=args.delete,
        )
    except ApplyError as exc:
        print(f"se-buddy: {exc}")
        return 1

    print(f"applied {args.cp_id} as {change['id']}")
    print(f"  {change['diff_summary']}")
    print(f"  {change['validation_summary']}")
    if change["manual_followup"]:
        print(f"  {len(change['manual_followup'])} manual followup item(s) - see `se-buddy asks`")
    print("this does not commit - git history is yours (spec Sec.10.2)")
    return 0
