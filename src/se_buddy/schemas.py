"""Record and ask schemas (spec Sec.9).

Pure validation logic, no I/O. `se-buddy write register`/`write answer`
(Phase 2) and `write memory` (not yet scoped to any phase - see
SPEC-COVERAGE.md) all validate against the shapes defined here rather than
each writer inventing its own.
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

# Registers (spec Sec.6.2) and the id prefix each one's rows allocate
# under. Kept separate from RECORD_KINDS because a register row and a
# narrative record are different data shapes (Sec.6.1 vs Sec.6.2) even
# though both go through the same id allocator (se_buddy.memory).
REGISTER_PREFIXES = {
    "requirements": "REQ",
    "stakeholder-expectations": "STK",
    "risks-system": "RISKSYS",
    "risks-project": "RISKPRJ",
    "verification": "VER",
    "not-carried": "NC",
}

# Every register row carries these regardless of which register it's in
# (spec Sec.9's "Register row" line: "id, claim, status, owner,
# provenance, links to model elements and records").
REGISTER_BASE_FIELDS = ("id", "claim", "status", "owner", "provenance", "links")

# Fields beyond the base that make each register meaningful. Sec.9 spells
# out not-carried.yaml's fields exactly ("source element id, the
# perspective pair, reason, who decided, or the ADR that decides a
# batch"); the rest aren't enumerated in the spec text, so these are a
# documented completion, not literal spec text (see SPEC-COVERAGE.md).
REGISTER_EXTRA_FIELDS = {
    "requirements": ("statement",),
    "stakeholder-expectations": ("stakeholder",),
    "risks-system": ("likelihood", "impact", "treatment"),
    "risks-project": ("likelihood", "impact", "treatment"),
    "verification": ("method", "requirement_id"),
    "not-carried": ("source_element_id", "from_perspective", "to_perspective", "reason", "decided_by"),
}


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


def validate_register_row(register: str, data: dict) -> ValidationResult:
    """Validates one row against `register`'s schema.

    `id`, `claim` and `status` are enforced on every register - a row
    lacking any of them can't be tracked at all. `owner`, `provenance` and
    `links`, and each register's extra fields, are required but not
    enforced by default, matching Sec.9's ask-field treatment - except
    `not-carried.yaml`'s `reason`/`decided_by`, which Sec.9 states as
    enforced explicitly: "reason and decider required - a row without them
    re-states the unknown it exists to close."
    """
    if register not in REGISTER_PREFIXES:
        raise ValueError(f"unknown register {register!r}; expected one of {sorted(REGISTER_PREFIXES)}")

    errors: list[str] = []
    warnings: list[str] = []

    for field in ("id", "claim", "status"):
        if not data.get(field):
            errors.append(f"{field} is required on every register row (spec Sec.9)")

    for field in ("owner", "provenance", "links"):
        if not data.get(field):
            warnings.append(f"{field} is required but not enforced (spec Sec.9)")

    hard_enforced = {"not-carried": ("reason", "decided_by")}.get(register, ())
    for field in REGISTER_EXTRA_FIELDS.get(register, ()):
        if data.get(field):
            continue
        if field in hard_enforced:
            errors.append(f"{field} is required on {register} rows (spec Sec.9: enforced)")
        else:
            warnings.append(f"{field} is required but not enforced for {register} rows")

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
