"""`se-buddy inspect` - model + diagrams + memory overview, in counts (spec Sec.7.3, D6)."""

from __future__ import annotations

import collections
from pathlib import Path

from se_buddy.commands._common import LAYER_ATTRS, add_model_argument, load_model_or_die
from se_buddy.profile import check_completeness


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser("inspect", help="model + diagrams + memory overview, in counts")
    add_model_argument(parser)
    parser.set_defaults(func=run)


def layer_counts(layer) -> dict[str, int]:
    """Counts every `all_*` accessor a layer actually has (spec Sec.2.2:
    perspectives are not symmetric - `epbs` has fewer of these than the
    other four, and this reports whatever exists rather than assuming a
    fixed shape).
    """
    counts: dict[str, int] = {}
    for attr in sorted(dir(type(layer))):
        if not attr.startswith("all_"):
            continue
        try:
            value = getattr(layer, attr)
            counts[attr] = len(value)
        except Exception:
            continue
    return counts


def run(args) -> int:
    model = load_model_or_die(args)
    if model is None:
        return 1

    print("model")
    for layer_attr in LAYER_ATTRS:
        layer = getattr(model, layer_attr, None)
        if layer is None:
            continue
        counts = layer_counts(layer)
        total = sum(counts.values())
        nonzero = {k: v for k, v in counts.items() if v}
        print(f"  {layer_attr}: {total} elements across {len(nonzero)} kinds")

    print("diagrams")
    by_type = collections.Counter(str(d.type) for d in model.diagrams)
    print(f"  {len(model.diagrams)} diagrams in {len(by_type)} types")

    print("profile")
    gaps = check_completeness(Path.cwd())
    if gaps:
        print(f"  incomplete: {len(gaps)} SUPPLY asks open (see `se-buddy asks`)")
    else:
        print("  complete")

    return 0
