"""Shared `capellambse.decl` operations (spec Sec.7.1, Sec.10.2's "validate targets").

`se-buddy plan` (a pure dry run) and `write apply`'s preflight/`--delete`
-precondition checks both need the same primitive: apply a decl document
to a model in memory, without ever calling `.save()`, and see what
changed. Confirmed safe directly against the vendored `decl.py`: `apply()`
never touches the filesystem itself, and carries no state across calls
(`Promise`/`deferred` are fresh locals per call) - so applying to a
throwaway model and discarding it has no side effect beyond that model
object being garbage collected.
"""

from __future__ import annotations

import io
import dataclasses

from capellambse import decl


class DeclError(Exception):
    """A decl document does not resolve/apply cleanly - reported plainly."""


@dataclasses.dataclass(frozen=True)
class DryRunResult:
    created: frozenset
    deleted: frozenset
    before_count: int
    after_count: int


def _element_uuids(model) -> set:
    return {element.uuid for element in model.search()}


def dry_run(model, decl_text: str) -> DryRunResult:
    """Applies `decl_text` to `model` in memory (never `.save()`s) and
    returns what changed. Raises `DeclError` - never a raw exception from
    `capellambse.decl` - if the document doesn't resolve or apply cleanly.
    """
    before = _element_uuids(model)
    try:
        decl.apply(model, io.StringIO(decl_text))
    except Exception as exc:  # decl raises plain ValueError/KeyError/TypeError
        raise DeclError(str(exc)) from exc
    after = _element_uuids(model)
    return DryRunResult(
        created=frozenset(after - before),
        deleted=frozenset(before - after),
        before_count=len(before),
        after_count=len(after),
    )
