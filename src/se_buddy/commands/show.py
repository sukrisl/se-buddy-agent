"""`se-buddy show <id>` - one element, relationships, diagrams, citations (spec Sec.7.3)."""

from __future__ import annotations

import warnings

from se_buddy.commands._common import add_limit_argument, add_model_argument, load_model_or_die, truncate

# Behavioural elements are read, not judged (spec Sec.2.2) - this command
# treats a FunctionalChain/Scenario/StateMachine exactly like a structural
# element: name, parent, diagrams, and whatever relationships it has. No
# special-casing per class.

RELATIONSHIP_ITEM_LIMIT = 5


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser("show", help="one element or record, relationships, diagrams")
    parser.add_argument("id", help="a model element UUID (record ids arrive with the write path)")
    add_model_argument(parser)
    add_limit_argument(parser, default=15)
    parser.set_defaults(func=run)


def run(args) -> int:
    model = load_model_or_die(args)
    if model is None:
        return 1

    try:
        element = model.by_uuid(args.id)
    except KeyError:
        print(
            f"se-buddy: {args.id!r} is not a model element in this model. "
            "Record ids (ADR-nnnn etc.) aren't retrievable yet - the write path "
            "that creates them doesn't exist until a later phase."
        )
        return 1

    print(f"{type(element).__name__} {args.id}")
    name = getattr(element, "name", "")
    if name:
        print(f"  name: {name}")

    parents = list(_iter_ancestors(element))
    if parents:
        chain = " > ".join(getattr(p, "name", "") or type(p).__name__ for p in reversed(parents))
        print(f"  parent chain: {chain}")

    diagrams = list(getattr(element, "diagrams", []) or [])
    if diagrams:
        shown, truncated = truncate(diagrams, args.limit)
        names = ", ".join(d.name for d in shown)
        suffix = f" (truncated from {len(diagrams)}, --limit {args.limit})" if truncated else ""
        print(f"  on {len(diagrams)} diagram(s): {names}{suffix}")

    relationships = relationship_attrs(element)
    shown_rels, rel_truncated = truncate(sorted(relationships), args.limit)
    for attr in shown_rels:
        value = relationships[attr]
        sample_items, item_truncated = truncate(list(value), RELATIONSHIP_ITEM_LIMIT)
        sample = ", ".join(getattr(v, "name", "") or type(v).__name__ for v in sample_items)
        suffix = f", +{len(value) - len(sample_items)} more" if item_truncated else ""
        print(f"  {attr}: {len(value)} ({sample}{suffix})")
    if rel_truncated:
        print(f"  ... {len(relationships) - len(shown_rels)} more relationship kinds not shown (--limit {args.limit})")

    return 0


def _iter_ancestors(element):
    seen = 0
    current = element
    while True:
        parent = getattr(current, "parent", None)
        if parent is None or parent is current:
            return
        yield parent
        current = parent
        seen += 1
        if seen > 50:  # containment trees are not this deep; stop rather than loop forever
            return


def relationship_attrs(element) -> dict:
    """Every non-empty ElementList-valued attribute on `element`'s class.

    Deprecated aliases (e.g. `.exchanges` for `.component_exchanges`) are
    excluded by turning their warning into an error and skipping - this is
    what keeps the list to the current, non-redundant names instead of
    reporting the same relationship twice under two spellings.
    """
    from capellambse.model import ElementList

    found: dict = {}
    for attr in dir(type(element)):
        if attr.startswith("_") or attr in ("diagrams", "visible_on_diagrams"):
            continue
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error")
                value = getattr(element, attr)
        except Exception:
            continue
        if isinstance(value, ElementList) and len(value) > 0:
            found[attr] = value
    return found
