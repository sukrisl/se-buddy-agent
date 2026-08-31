"""`se-buddy trace <id>` - what it traces to, what traces to it, what breaks (spec Sec.6.3, C07, Sec.11).

Phase 2 extends this across model *and* registers (spec Sec.11's Phase 2
scope: "trace across model and registers"): `<id>` may be a model uuid or
a register row id, and a model uuid's trace also reports every register
row that cites it via `links`.
"""

from __future__ import annotations

from pathlib import Path

from se_buddy.commands._common import (
    add_depth_argument,
    add_limit_argument,
    add_model_argument,
    element_summary,
    load_model_or_die,
    truncate,
)
from se_buddy.commands.show import relationship_attrs
from se_buddy.memory import render_citation
from se_buddy.registers import find_row, find_rows_linking


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser("trace", help="what it traces to, what traces to it, what breaks")
    parser.add_argument("id", help="a model element UUID or a register row id")
    add_model_argument(parser)
    add_limit_argument(parser)
    add_depth_argument(parser)
    parser.set_defaults(func=run)


def run(args) -> int:
    root = Path.cwd()

    register_hit = find_row(root, args.id)
    if register_hit is not None:
        _trace_register_row(args, register_hit)
        return 0

    model = load_model_or_die(args)
    if model is None:
        return 1

    try:
        target = model.by_uuid(args.id)
    except KeyError:
        print(f"se-buddy: {args.id!r} is not a model element or a register row id in this project.")
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

    citing_rows = find_rows_linking(root, args.id)
    if citing_rows:
        print(f"  cited by {len(citing_rows)} register row(s):")
        for register, row in citing_rows:
            print(f"    {register}: {render_citation(row['id'], row.get('claim', ''))}")

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
    if citing_rows:
        print(
            f"  what breaks: {len(citing_rows)} register row(s) above cite this element - "
            "removing it invalidates their `links`"
        )

    return 0


def _trace_register_row(args, hit: tuple[str, dict]) -> None:
    register, row = hit
    print(f"register row {row['id']} ({register})")
    print(f"  {render_citation(row['id'], row.get('claim', ''))}")
    print(f"  status: {row.get('status', '?')}")
    links = row.get("links") or []
    shown, truncated = truncate(links, args.limit)
    print(f"  links to {len(links)} id(s):")
    for linked_id in shown:
        print(f"    {linked_id}")
    if truncated:
        print(f"    ... truncated from {len(links)} (--limit {args.limit})")


def _reverse_closure(model, target, depth: int) -> list[tuple[object, str]]:
    """Breadth-first closure over `model.find_references`, bounded by `depth`.

    `ModelElement` is not hashable (confirmed directly against real
    capellambse: `hash(element)` raises `TypeError`) even though `==` works
    structurally - so dedup here is keyed on `.uuid` strings, never on the
    elements themselves or a `set()` of them.

    Two separate `.uuid` sets are kept on purpose - a code review found the
    original single `visited` set conflated "already queued as a BFS node"
    with "already recorded as an edge," so a second, distinct
    attribute-edge into an object already reached (e.g. an object that
    references the target through two different relationship attrs, or is
    reached again one level deeper via a different attr) was silently
    dropped from `found` instead of reported. `visited_uuids` still
    controls BFS expansion (each node's neighbours are only walked once);
    `seen_edges`, keyed on `(uuid, attr)`, controls what gets recorded, so
    every distinct edge into an object is kept even when the object itself
    was already visited.
    """
    visited_uuids = {target.uuid}
    frontier = {target.uuid: target}
    found: list[tuple[object, str]] = []
    seen_edges: set[tuple[str, str]] = set()

    for _ in range(depth):
        next_frontier: dict[str, object] = {}
        for obj in frontier.values():
            for referencing_obj, attr, _index in model.find_references(obj):
                ref_uuid = getattr(referencing_obj, "uuid", None)
                if ref_uuid is None:
                    continue
                edge_key = (ref_uuid, attr)
                if edge_key not in seen_edges:
                    seen_edges.add(edge_key)
                    found.append((referencing_obj, attr))
                if ref_uuid not in visited_uuids:
                    visited_uuids.add(ref_uuid)
                    next_frontier[ref_uuid] = referencing_obj
        if not next_frontier:
            break
        frontier = next_frontier

    return found
