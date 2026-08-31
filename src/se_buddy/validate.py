"""Six validation layers (spec Sec.7.2). Each is separately reportable;
none measures completeness - that is `perspective`'s question (spec
Sec.2.2 rule 1, not built in this phase - see SPEC-COVERAGE.md), and
reading a structural pass as a completeness pass is exactly the failure
spec Sec.13 checks for.

Five layers get real, automated checks, appropriately scoped rather than
exhaustive (documented per-layer below and in SPEC-COVERAGE.md).
`architectural` reports `UNKNOWN`: whether the model obeys a *free-text*
design rule ("no single point of failure") is a reasoning-layer judgement,
not something a deterministic check can verify - C04 makes `UNKNOWN` a
real, honest outcome, not a softened pass.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

from se_buddy.memory_domains import load_viewpoints
from se_buddy.registers import REGISTER_PREFIXES, load_register

LAYERS = ("structural", "representation", "interface", "traceability", "consistency", "architectural")


@dataclasses.dataclass(frozen=True)
class Finding:
    layer: str
    severity: str  # PASS | WARN | ERROR | UNKNOWN
    message: str


def _root_uuids(model) -> set[str]:
    """The project root and the five layer roots legitimately have no
    `.parent` - excluded from the structural orphan check below.
    """
    uuids = set()
    try:
        uuids.add(model.project.uuid)
    except Exception:
        pass
    for layer_attr in ("oa", "sa", "la", "pa", "epbs"):
        layer = getattr(model, layer_attr, None)
        if layer is not None:
            uuids.add(layer.uuid)
    return uuids


def check_structural(model) -> list[Finding]:
    """Is what exists well-formed against the metamodel? Spec example:
    "a LogicalComponent with no parent package." capellambse itself
    enforces required-attrs at object construction and load time, so a
    model that loaded at all has already passed the deepest structural
    checks the library can perform; what is left to check here is
    containment orphaning outside the recognised roots.
    """
    roots = _root_uuids(model)
    orphans = []
    for element in model.search():
        if element.uuid in roots:
            continue
        if getattr(element, "parent", "sentinel-not-none") is None:
            orphans.append(element)
    if orphans:
        return [Finding("structural", "WARN", f"{len(orphans)} element(s) have no parent")]
    return [Finding("structural", "PASS", "every non-root element has a parent")]


def check_representation(model) -> list[Finding]:
    """Do the diagrams still match the semantic model? Spec example: "an
    element on a diagram that no longer exists in .capella." Checked by
    actually resolving every diagram's visible nodes - a stale reference
    surfaces as an exception from capellambse's own resolution.
    """
    broken = 0
    for diagram in model.diagrams:
        try:
            list(diagram.nodes)
        except Exception:
            broken += 1
    total = len(model.diagrams)
    if broken:
        return [Finding("representation", "ERROR", f"{broken}/{total} diagram(s) fail to resolve their nodes")]
    return [Finding("representation", "PASS", f"all {total} diagram(s) resolve their nodes")]


def check_interface(model) -> list[Finding]:
    """Do the exchanges hold together? Spec example: "a FunctionalExchange
    with no ExchangeItem allocated." Checks functional and component
    exchanges for allocated items - real capellambse fields confirmed
    directly (`exchanged_items`, `convoyed_informations` - the
    `exchange_items`/`allocated_exchange_items` names are deprecated
    aliases for the same thing).
    """
    findings = []
    fe = model.search("FunctionalExchange")
    fe_empty = [e for e in fe if not e.exchanged_items]
    if fe_empty:
        findings.append(
            Finding("interface", "WARN", f"{len(fe_empty)}/{len(fe)} functional exchange(s) carry no ExchangeItem")
        )
    ce = model.search("ComponentExchange")
    ce_empty = [e for e in ce if not e.convoyed_informations]
    if ce_empty:
        findings.append(
            Finding("interface", "WARN", f"{len(ce_empty)}/{len(ce)} component exchange(s) carry no ExchangeItem")
        )
    if not findings:
        findings.append(Finding("interface", "PASS", "every exchange carries at least one ExchangeItem"))
    return findings


def check_traceability(root: Path, model) -> list[Finding]:
    """Do the links required by C07 exist and resolve? Checks register
    cross-references specifically (spec example given, "a requirement with
    no verification row"): every `requirements` row should be cited by at
    least one `verification` row's `requirement_id`.
    """
    requirements = load_register(root, "requirements")
    verification = load_register(root, "verification")
    verified_ids = {row.get("requirement_id") for row in verification.values()}
    unverified = [rid for rid in requirements if rid not in verified_ids]
    if unverified:
        return [
            Finding(
                "traceability",
                "WARN",
                f"{len(unverified)}/{len(requirements)} requirement(s) have no verification row",
            )
        ]
    if requirements:
        return [Finding("traceability", "PASS", f"all {len(requirements)} requirement(s) have a verification row")]
    return [Finding("traceability", "UNKNOWN", "no requirements are recorded yet to check")]


def check_consistency(root: Path, model) -> list[Finding]:
    """Does the model agree with the registers and records? Checks every
    register row's `links` against the current model - spec example
    given ("a risk treatment citing a component that was renamed") isn't
    directly detectable (uuids survive a rename), but a link to a uuid
    that no longer *exists* at all is, and is the sharper failure mode.
    """
    dangling = 0
    total_links = 0
    for register in REGISTER_PREFIXES:
        for row in load_register(root, register).values():
            for link in row.get("links") or []:
                total_links += 1
                try:
                    model.by_uuid(link)
                except KeyError:
                    dangling += 1
    if dangling:
        return [Finding("consistency", "ERROR", f"{dangling}/{total_links} register link(s) do not resolve in the model")]
    if total_links:
        return [Finding("consistency", "PASS", f"all {total_links} register link(s) resolve in the model")]
    return [Finding("consistency", "UNKNOWN", "no register rows link to the model yet to check")]


def check_architectural(root: Path) -> list[Finding]:
    """Does it obey this project's recorded rules? A free-text design rule
    ("no single point of failure") cannot be verified by a deterministic
    check - this reports `UNKNOWN` and names what a reasoning-layer review
    (`arch-review`) needs to check by hand, per C04.
    """
    viewpoints = load_viewpoints(root)
    if not viewpoints:
        return [Finding("architectural", "UNKNOWN", "no viewpoints recorded - project style is unrecorded (spec C02)")]
    names = ", ".join(v.get("name", "?") for v in viewpoints)
    return [
        Finding(
            "architectural",
            "UNKNOWN",
            f"{len(viewpoints)} recorded viewpoint(s) ({names}) need a reasoning-layer review "
            "(`arch-review`) - a design rule in free text cannot be checked by code",
        )
    ]


def run_all_layers(root: Path, model) -> list[Finding]:
    findings: list[Finding] = []
    findings += check_structural(model)
    findings += check_representation(model)
    findings += check_interface(model)
    findings += check_traceability(root, model)
    findings += check_consistency(root, model)
    findings += check_architectural(root)
    return findings


def summarize(findings: list[Finding]) -> str:
    """One-line validation summary (spec Sec.9: a CHANGE stores this, not
    the full report - "the validation report is reproducible by re-running
    validate at that commit," spec Sec.9's own note on where the full
    report actually lives).
    """
    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding.severity] = counts.get(finding.severity, 0) + 1
    parts = ", ".join(f"{n} {sev}" for sev, n in sorted(counts.items()))
    return parts or "no findings"
