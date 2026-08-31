"""Shared helpers for CLI verbs (spec Sec.7.3).

Kept small and boring on purpose: every command bounds its output and
reports truncation (spec Sec.6.3), and D6 wants counts rendered plainly
rather than each command reinventing its own formatting.
"""

from __future__ import annotations

import warnings
from pathlib import Path

from se_buddy.model import ModelResolutionError, load_model

DEFAULT_LIMIT = 20
DEFAULT_DEPTH = 2

# Every layer a BlockArchitecture exposes on capellambse.MelodyModel, in
# Arcadia order (spec Sec.2.2's table). `epbs` is real but thinner than the
# other four - code iterating this MUST NOT assume every layer has the same
# `all_*` accessors (confirmed directly: epbs has no all_components, for
# instance).
LAYER_ATTRS = ("oa", "sa", "la", "pa", "epbs")


def add_model_argument(parser) -> None:
    parser.add_argument(
        "--model",
        help="path to a .aird file (overrides se-buddy/profile.yaml)",
        default=None,
    )


def add_limit_argument(parser, default: int = DEFAULT_LIMIT) -> None:
    parser.add_argument(
        "--limit",
        type=int,
        default=default,
        help=f"maximum results to return (default {default})",
    )


def add_depth_argument(parser, default: int = DEFAULT_DEPTH) -> None:
    parser.add_argument(
        "--depth",
        type=int,
        default=default,
        help=f"maximum trace depth (default {default})",
    )


def load_model_or_die(args) -> object:
    """Loads a model for a command, printing one clean line on failure.

    Returns None on failure - callers check for that and return exit code 1,
    keeping every command's own `run()` free of try/except boilerplate.
    """
    try:
        return load_model(Path.cwd(), getattr(args, "model", None))
    except ModelResolutionError as exc:
        print(f"se-buddy: {exc}")
        return None


def truncate(items: list, limit: int) -> tuple[list, bool]:
    """Bounds `items` to `limit`, reporting whether anything was cut.

    Spec Sec.6.3: "Any truncation is reported - a silently truncated trace
    reads as a complete one, and a wrong answer that looks complete is
    worse than a slow one."
    """
    if len(items) <= limit:
        return items, False
    return items[:limit], True


def element_summary(element) -> str:
    """Renders one element as `Type "Name" (uuid)`, tolerating types that
    have no `.name` (spec finding: `.name` never raises - it warns and
    returns "" - so this never needs a try/except for that specific case).
    """
    name = getattr(element, "name", "") or "<unnamed>"
    uuid = getattr(element, "uuid", "?")
    return f'{type(element).__name__} "{name}" ({uuid})'


def suppress_capellambse_deprecations():
    """Context manager: silences FutureWarning/DeprecationWarning while
    probing attributes generically (see commands/show.py) - capellambse
    emits these for every legacy alias (e.g. `.exchanges` for
    `.component_exchanges`), and D4's "one screen" ethos means our own
    output shouldn't be drowned in library deprecation noise for aliases
    we never asked to see in the first place.
    """
    return warnings.catch_warnings()
