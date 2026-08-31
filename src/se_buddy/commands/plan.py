"""`se-buddy plan CP-nnnn` - dry run: what would change, what must be drawn by hand (spec Sec.7.3).

Automatic authority, read-only in effect: applies the CP's `proposed_changes`
to a model loaded fresh for this purpose, never calls `.save()`, and
reports what would happen (spec Sec.7.1's confirmed-safe dry-run pattern -
see `se_buddy.decl_ops`).
"""

from __future__ import annotations

from pathlib import Path

from se_buddy.commands._common import add_model_argument, load_model_or_die
from se_buddy.decl_ops import DeclError, dry_run
from se_buddy.proposals import load_cp


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser("plan", help="dry run: what would change, what must be drawn by hand")
    parser.add_argument("cp_id", help="a CP-nnnn id, from `se-buddy proposals` or the filed record")
    add_model_argument(parser)
    parser.set_defaults(func=run)


def run(args) -> int:
    root = Path.cwd()
    cp = load_cp(root, args.cp_id)
    if cp is None:
        print(f"se-buddy: {args.cp_id} is not a known proposal")
        return 1

    decl_text = cp.get("proposed_changes")
    if not decl_text:
        print(f"se-buddy: {args.cp_id} has no proposed_changes to plan against")
        return 1

    model = load_model_or_die(args)
    if model is None:
        return 1

    try:
        result = dry_run(model, decl_text)
    except DeclError as exc:
        print(f"se-buddy: proposed_changes does not apply cleanly: {exc}")
        return 1

    print(f"{args.cp_id}: {cp.get('claim', '')}")
    print(f"  would create {len(result.created)} element(s), delete {len(result.deleted)}")
    print(f"  model would go from {result.before_count} to {result.after_count} elements")

    if result.created:
        print(f"  {len(result.created)} newly-created element(s) will need drawing by hand:")
        for target_uuid in sorted(result.created):
            try:
                element = model.by_uuid(target_uuid)
            except KeyError:
                continue
            name = getattr(element, "name", "") or target_uuid
            print(f"    {type(element).__name__} {name!r} ({target_uuid})")

    return 0
