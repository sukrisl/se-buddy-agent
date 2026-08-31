"""`se-buddy trace <id>` - what it traces to, what traces to it, what breaks (spec Sec.6.3, C07)."""

from __future__ import annotations

from se_buddy.commands._common import (
    add_depth_argument,
    add_limit_argument,
    add_model_argument,
    element_summary,
    load_model_or_die,
    truncate,
)
from se_buddy.commands.show import relationship_attrs


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser("trace", help="what it traces to, what traces to it, what breaks")
    parser.add_argument("id", help="a model element UUID")
    add_model_argument(parser)
    add_limit_argument(parser)
    add_depth_argument(parser)
    parser.set_defaults(func=run)


def run(args) -> int:
    model = load_model_or_die(args)
    if model is None:
        return 1

    try:
        target = model.by_uuid(args.id)
    except KeyError:
        print(f"se-buddy: {args.id!r} is not a model element in this model.")
        return 1

    print(f"{type(target).__name__} {args.id}")

    outgoing = relationship_attrs(target)
    outgoing_total = sum(len(v) for v in outgoing.values())
    print(f"  traces to: {outgoing_total} reference(s) across {len(outgoing)} relationship kinds")

    incoming = _reverse_closure(model, target, args.depth)
    print(f"  traced from: {len(incoming)} reference(s) within depth {args.depth}")
    shown, truncated = truncate(incoming, args.limit)
    for referencing_obj, attr in shown:
        print(f"    {element_summary(referencing_obj)} via .{attr}")
    if truncated:
        print(f"    ... truncated from {len(incoming)} (--limit {args.limit})")

    diagrams = list(getattr(target, "diagrams", []) or [])
    if diagrams:
        print(
            f"  what breaks: appears on {len(diagrams)} diagram(s) - "
            "removing it would leave a dangling representation there (spec Sec.7.4)"
        )
    if incoming:
        print(
            f"  what breaks: {len(incoming)} reference(s) above would dangle "
            "if this element were removed"
        )

    return 0


def _reverse_closure(model, target, depth: int) -> list[tuple[object, str]]:
    """Breadth-first closure over `model.find_references`, bounded by `depth`.

    `ModelElement` is not hashable (confirmed directly against real
    capellambse: `hash(element)` raises `TypeError`) even though `==` works
    structurally - so dedup here is keyed on `.uuid` strings, never on the
    elements themselves or a `set()` of them.
    """
    visited = {target.uuid}
    frontier = {target.uuid: target}
    found: list[tuple[object, str]] = []

    for _ in range(depth):
        next_frontier: dict[str, object] = {}
        for obj in frontier.values():
            for referencing_obj, attr, _index in model.find_references(obj):
                ref_uuid = getattr(referencing_obj, "uuid", None)
                if ref_uuid is None or ref_uuid in visited:
                    continue
                visited.add(ref_uuid)
                next_frontier[ref_uuid] = referencing_obj
                found.append((referencing_obj, attr))
        if not next_frontier:
            break
        frontier = next_frontier

    return found
