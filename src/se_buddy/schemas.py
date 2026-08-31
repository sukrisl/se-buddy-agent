"""Record and ask schemas (spec Sec.9).

Pure validation logic, no I/O. `se-buddy write register`, `write answer`
and `write memory` all validate against the shapes defined here rather
than each writer inventing its own.
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

# `write memory` domains whose rows get a stable, citable id (spec Sec.9:
# "Principle / assumption / knowledge | provenance, status | required").
# `viewpoints` and `glossary` are deliberately absent here - they're keyed
# by a natural name/term instead (spec Sec.9 asks for `design_rules`/
# `priority` on a viewpoint and nothing that implies an opaque id).
# `knowledge` is absent too: every knowledge.yaml row must carry the
# `ASK-nnnn` it answers (spec Sec.9), which only `write answer`'s
# CONFIRM/REVIEW path supplies - see SPEC-COVERAGE.md's design note.
MEMORY_DOMAIN_PREFIXES = {
    "principles": "PRIN",
    "assumptions": "ASSUME",
}

# An ADR's fields beyond the base record (spec Sec.9's ADR row). `authority`
# is the one enforced field - "an ADR cannot be filed as the agent's."
ADR_EXTRA_FIELDS = (
    "question",
    "context",
    "alternatives",
    "chosen_option",
    "rationale",
    "consequences",
    "evidence",
    "authority",
)

# A CP's fields beyond the base record (spec Sec.9's CP row): "rejected if
# facts, alternatives, unknowns, open questions, verification implications
# or provenance are missing" - those six are enforced; the rest (including
# `proposed_changes` itself) are required but not enforced by the schema,
# literal to spec Sec.9's own wording even though a CP with no changes to
# propose is of limited use - `se-buddy plan`/`write apply` separately
# refuse to act on an empty `proposed_changes`, as their own precondition.
CP_EXTRA_FIELDS = (
    "intent",
    "facts",
    "assumptions",
    "unknowns",
    "affected_elements",
    "proposed_changes",
    "alternatives",
    "verification_implications",
    "open_questions",
    "diagram_cost",
    "provenance",
)
CP_ENFORCED_FIELDS = frozenset(
    {"facts", "alternatives", "unknowns", "open_questions", "verification_implications", "provenance"}
)

# A CHANGE's fields beyond the base record (spec Sec.9's CHANGE row):
# "cannot contain the diff or the report; manual_followup required."
# `authority` is enforced too - a CHANGE with no authority is exactly the
# unauthorised model write spec Sec.2.3 exists to prevent, whether it came
# from `write apply --authorized-by` or `write record`'s own draft.
CHANGE_EXTRA_FIELDS = ("proposal", "authority", "diff_summary", "validation_summary", "manual_followup")
CHANGE_ENFORCED_FIELDS = frozenset({"authority", "manual_followup"})


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


def validate_adr(data: dict) -> ValidationResult:
    """Validates an ADR: the base record fields, plus Sec.9's ADR row.

    `authority` is enforced - "an ADR cannot be filed as the agent's"
    (spec Sec.9, spec Sec.2.3) - every other ADR-specific field is
    required but not enforced, matching the base record's own treatment.
    """
    base = validate_record_base(data)
    errors = list(base.errors)
    warnings = list(base.warnings)

    for field in ADR_EXTRA_FIELDS:
        if data.get(field):
            continue
        if field == "authority":
            errors.append(
                "authority is required on every ADR (spec Sec.9) - "
                "an ADR cannot be filed as the agent's"
            )
        else:
            warnings.append(f"{field} is required but not enforced on an ADR (spec Sec.9)")

    return ValidationResult(tuple(errors), tuple(warnings))


def validate_memory_row(domain: str, data: dict) -> ValidationResult:
    """Validates a principles/assumptions row (spec Sec.9: "Principle /
    assumption / knowledge | provenance, status | required").
    """
    if domain not in MEMORY_DOMAIN_PREFIXES:
        raise ValueError(f"unknown memory domain {domain!r}; expected one of {sorted(MEMORY_DOMAIN_PREFIXES)}")

    errors: list[str] = []
    warnings: list[str] = []

    if not data.get("statement"):
        errors.append(f"statement is required on every {domain} row")
    for field in ("provenance", "status"):
        if not data.get(field):
            warnings.append(f"{field} is required but not enforced (spec Sec.9)")

    return ValidationResult(tuple(errors), tuple(warnings))


_CP_PRESENCE_ONLY_FIELDS = frozenset({"unknowns", "open_questions", "diagram_cost"})


def validate_cp(data: dict) -> ValidationResult:
    """Validates a CP: the base record fields, plus Sec.9's CP row.

    `facts`, `alternatives`, `unknowns`, `open_questions`,
    `verification_implications` and `provenance` are enforced - Sec.9,
    verbatim: "rejected if [these] are missing." `unknowns`,
    `open_questions` and `diagram_cost` are checked for *presence*, not
    truthiness - an empty list is a real, good answer ("nothing
    outstanding"), and `diagram_cost: 0` is a real, good answer ("nothing
    to draw") that `bool(0)` would otherwise treat as absent - a code
    review found exactly that: `diagram_cost` was warned-about-as-missing
    on every CP that legitimately had none. Same treatment `validate_change`
    gives `manual_followup`.
    """
    base = validate_record_base(data)
    errors = list(base.errors)
    warnings = list(base.warnings)

    for field in CP_EXTRA_FIELDS:
        if field in _CP_PRESENCE_ONLY_FIELDS:
            present = field in data and data[field] is not None
        else:
            present = bool(data.get(field))
        if present:
            continue
        if field in CP_ENFORCED_FIELDS:
            errors.append(f"{field} is required on every CP (spec Sec.9: enforced)")
        else:
            warnings.append(f"{field} is required but not enforced on a CP (spec Sec.9)")

    return ValidationResult(tuple(errors), tuple(warnings))


_CHANGE_PRESENCE_ONLY_FIELDS = frozenset({"manual_followup"})


def validate_change(data: dict) -> ValidationResult:
    """Validates a CHANGE: the base record fields, plus Sec.9's CHANGE row.

    `authority` and `manual_followup` are enforced - Sec.9: "manual_followup
    required," and an unauthorised CHANGE is exactly what spec Sec.2.3
    exists to prevent. `manual_followup` is checked for *presence*, not
    truthiness - an empty list is a valid, meaningful answer ("nothing left
    to draw by hand"), same treatment `validate_cp` gives `unknowns`/
    `open_questions`/`diagram_cost`.

    A code review found this used to compute `present` for every field
    with `not in (None, "")`, then unconditionally overwrite it with an
    `is not None` check specifically for `manual_followup` - a dead
    no-op, since `[] not in (None, "")` and `[] is not None` already agree
    for every real value this field takes. Rewritten to share
    `validate_cp`'s actual pattern: a presence-only field set, checked
    directly, instead of a same-field special case with no behavioural
    effect.
    """
    base = validate_record_base(data)
    errors = list(base.errors)
    warnings = list(base.warnings)

    for field in CHANGE_EXTRA_FIELDS:
        if field in _CHANGE_PRESENCE_ONLY_FIELDS:
            present = field in data and data[field] is not None
        else:
            present = bool(data.get(field))
        if present:
            continue
        if field in CHANGE_ENFORCED_FIELDS:
            errors.append(f"{field} is required on every CHANGE (spec Sec.9: enforced)")
        else:
            warnings.append(f"{field} is required but not enforced on a CHANGE (spec Sec.9)")

    return ValidationResult(tuple(errors), tuple(warnings))


def validate_viewpoint(data: dict) -> ValidationResult:
    """Sec.9: "Viewpoint | design_rules, priority | rejected without both -
    a viewpoint that cannot decide a boundary is not a viewpoint."
    """
    errors: list[str] = []
    if not data.get("name"):
        errors.append("name is required to key a viewpoint")
    if not data.get("design_rules"):
        errors.append("design_rules is required on every viewpoint (spec Sec.9: rejected without it)")
    if data.get("priority") is None:
        errors.append("priority is required on every viewpoint (spec Sec.9: rejected without it)")
    return ValidationResult(tuple(errors))


def validate_glossary_entry(data: dict) -> ValidationResult:
    errors: list[str] = []
    if not data.get("term"):
        errors.append("term is required to key a glossary entry")
    if not data.get("definition"):
        errors.append("definition is required on every glossary entry")
    return ValidationResult(tuple(errors))
