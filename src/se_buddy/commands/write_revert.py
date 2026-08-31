"""`se-buddy write revert CHANGE-nnnn` (spec Sec.7.3, Sec.10.1).

"`write revert` takes a CHANGE-nnnn, not a CP-nnnn" - the snapshot is
per-apply and the record is the change, so the change is the only id that
identifies a reversible event (spec Sec.7.3).

TTY-gated. `revert_change()` and `run()` are separate on purpose, same
testing pattern as every other write verb.
"""

from __future__ import annotations

from pathlib import Path

from se_buddy.apply_lifecycle import check_tree_clean, restore_snapshot, snapshot_dir
from se_buddy.changes import load_change
from se_buddy.commands._common import add_model_argument
from se_buddy.gate import GateRefused, confirm
from se_buddy.model import ModelResolutionError, resolve_model_path


class RevertError(Exception):
    """A revert could not be completed as asked - reported plainly."""


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser("write-revert", help="revert a CHANGE from its snapshot (spec Sec.7.3)")
    parser.add_argument("change_id", help="a CHANGE-nnnn id")
    add_model_argument(parser)
    parser.set_defaults(func=run)


def revert_change(root: Path, change_id: str, model_arg: str | None = None) -> None:
    change = load_change(root, change_id)
    if change is None:
        raise RevertError(f"{change_id} is not a known CHANGE")

    try:
        aird_path = Path(resolve_model_path(root, model_arg))
    except ModelResolutionError as exc:
        raise RevertError(str(exc)) from exc

    check_tree_clean(root, aird_path)

    directory = snapshot_dir(root, change_id)
    if not directory.exists():
        raise RevertError(
            f"no snapshot exists for {change_id} - it was likely filed via `write record` "
            "(manual work has nothing for se-buddy to snapshot or revert)"
        )

    restore_snapshot(aird_path, directory)


def run(args) -> int:
    try:
        confirm(f"About to revert {args.change_id} from its snapshot")
    except GateRefused as exc:
        print(f"se-buddy: {exc}")
        return 1

    try:
        revert_change(Path.cwd(), args.change_id, args.model)
    except RevertError as exc:
        print(f"se-buddy: {exc}")
        return 1

    print(f"reverted {args.change_id} - the model files now match the pre-apply snapshot")
    return 0
