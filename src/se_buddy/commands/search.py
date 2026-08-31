"""`se-buddy search <words>` - elements by name/summary (spec Sec.7.3)."""

from __future__ import annotations

from se_buddy.commands._common import (
    LAYER_ATTRS,
    add_limit_argument,
    add_model_argument,
    element_summary,
    load_model_or_die,
    truncate,
)


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser("search", help="elements by name/summary")
    parser.add_argument("words", nargs="*", help="substrings to match against name/description")
    parser.add_argument("--kind", help="a Capella class name, e.g. LogicalComponent")
    parser.add_argument("--layer", choices=LAYER_ATTRS, help="restrict to one Arcadia layer")
    add_model_argument(parser)
    add_limit_argument(parser)
    parser.set_defaults(func=run)


def run(args) -> int:
    model = load_model_or_die(args)
    if model is None:
        return 1

    below = getattr(model, args.layer, None) if args.layer else None

    if args.kind:
        try:
            # subclasses=True: search() is exact-type-match by default (spec
            # research, confirmed against real capellambse 0.8.1) - a
            # free-text `--kind` search should be broader than that, not
            # silently miss every subclass.
            results = list(model.search(args.kind, below=below, subclasses=True))
        except Exception as exc:
            print(f"se-buddy: --kind {args.kind!r} is not searchable: {exc}")
            return 1
    else:
        results = list(model.search(below=below)) if below is not None else list(model.search())

    words = [w.lower() for w in args.words]
    if words:
        results = [el for el in results if _matches(el, words)]

    shown, truncated = truncate(results, args.limit)
    for element in shown:
        print(element_summary(element))

    if truncated:
        print(f"{len(shown)} shown, truncated from {len(results)} (--limit {args.limit})")
    else:
        print(f"{len(shown)} shown")
    return 0


def _matches(element, words: list[str]) -> bool:
    name = (getattr(element, "name", "") or "").lower()
    description = (getattr(element, "description", "") or "").lower()
    haystack = f"{name} {description}"
    return all(word in haystack for word in words)
