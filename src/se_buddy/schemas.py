"""Record and ask schemas (spec Sec.9).

Pure validation logic, no I/O. Nothing in Phase 1 writes a record or an ask
yet - `se-buddy write memory`/`write register`/`write answer` are Phase 2/3 -
but the shapes are needed now by `se-buddy asks` (which reads whatever
ask-shaped entries exist) and by later phases, so they are built once here
rather than re-derived per writer.
"""

from __future__ import annotations

import dataclasses

# The closed D8 act vocabulary (spec Sec.3). An ask whose act is not one of
# these is not a defect in this list - it is a defect in whatever produced
# the ask.
ACTS = frozenset(
    {
        "DECIDE",
        "AUTHORISE",
        "CONFIRM",
        "REVIEW",
        "DRAW",
        "SUPPLY",
        "PRIORITISE",
    }
)

# Record kinds that get sequential ids (spec Sec.9, Sec.3 D8).
RECORD_KINDS = frozenset({"ADR", "CP", "CHANGE", "ASK"})


class SchemaError(ValueError):
    """A record or ask is missing a field spec Sec.9 marks as enforced."""


@dataclasses.dataclass(frozen=True)
class ValidationResult:
    """errors are enforced-field violations (spec Sec.9: "Enforced").

    warnings are the fields Sec.9 calls "required but not enforced" - a
    schema can see a line is present, not that it says anything - so their
    absence is reported, never rejected.
    """

    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_ask(data: dict) -> ValidationResult:
    """Validates one ask/open-item against spec Sec.9's D8 shape.

    `act` and `done_when` are enforced: "An open item missing act or
    done_when is rejected. These are the two fields whose absence makes an
    item unanswerable, and an unanswerable item is indistinguishable from a
    lost one." `object`, `blocks` and `default` are required but not
    enforced - reported as warnings, never rejected on their own.
    """
    errors: list[str] = []
    warnings: list[str] = []

    act = data.get("act")
    if not act:
        errors.append("act is required (spec Sec.9: enforced)")
    elif act not in ACTS:
        errors.append(f"act {act!r} is not one of {sorted(ACTS)}")

    if not data.get("done_when"):
        errors.append("done_when is required (spec Sec.9: enforced)")

    for field in ("object", "blocks", "default"):
        if not data.get(field):
            warnings.append(f"{field} is required but not enforced (spec Sec.9)")

    return ValidationResult(tuple(errors), tuple(warnings))


def validate_record_base(data: dict) -> ValidationResult:
    """Validates the fields every record carries, regardless of kind (spec Sec.9)."""
    errors: list[str] = []
    for field in ("id", "claim", "tier", "date"):
        if not data.get(field):
            errors.append(f"{field} is required on every record (spec Sec.9)")
    if data.get("tier") not in (None, "lookup", "judgement", "decision"):
        errors.append(f"tier {data.get('tier')!r} must be lookup, judgement or decision")
    if "supersedes" not in data:
        errors.append("supersedes is required on every record, even if empty (spec Sec.9)")
    return ValidationResult(tuple(errors))
