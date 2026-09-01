"""Profile completeness (spec Sec.5.3).

The PROFILE layer lives in a consuming project's `se-buddy/` directory, not
in this repo. Phase 1 does not write it - `project-init` only scaffolds an
empty skeleton (see SPEC-COVERAGE.md's Phase 1 section on why the TTY gate
blocks anything more than that until Phase 2) - but `se-buddy doctor` and
`se-buddy asks` both need to report what is missing, as `SUPPLY` asks, per
Sec.5.3's doctor table: this check never refuses, only reports.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import yaml

from se_buddy import domain_pack
from se_buddy.atomic_write import atomic_write_text

PROFILE_DIRNAME = "se-buddy"

#: The four fields spec Sec.5.3 requires of `profile.yaml`, in the order they
#: are written. Single source for the completeness check, the validator and
#: the renderer, so the three cannot drift apart.
REQUIRED_PROFILE_FIELDS = ("model_path", "aird_path", "capella_version", "project_name")


@dataclasses.dataclass(frozen=True)
class ProfileGap:
    """One missing/incomplete piece of the profile, in D8 shape (spec Sec.3).

    Deliberately carries no `id`: an id is allocated once and stays stable
    (spec Sec.9), but a gap is recomputed fresh on every run from whatever
    files currently exist - persisting an id for it would itself be a write,
    which Phase 1 does not have. Once `write memory` exists (Phase 2), a
    gap like this becomes the trigger for a real, persisted `ASK-nnnn`.
    """

    object: str
    done_when: str
    act: str = "SUPPLY"
    blocks: str = "confident architectural judgements (spec Sec.5.3)"
    default: str = "none - architectural judgements report the project style as unrecorded until this is supplied"
    #: Live specifics behind this gap, for `doctor` to print. Deliberately
    #: NOT persisted by `ask_store.sync_profile_gaps`: an ask is written once
    #: and keeps its text, so anything that varies run to run (a count, a
    #: list of the placeholders currently present) would be frozen at
    #: whatever it happened to be the first time and quietly go stale.
    #: `done_when` states the invariant requirement; this states today's
    #: evidence.
    detail: tuple[str, ...] = ()


def profile_dir(root: Path) -> Path:
    return root / PROFILE_DIRNAME


def check_completeness(root: Path) -> list[ProfileGap]:
    """Returns what project-init's four requirements (spec Sec.5.3) still lack.

    Empty once `profile.yaml`, `domain.md`, `viewpoints.yaml` (>=1 viewpoint
    with `design_rules` and a `priority`) and `principles.yaml` (may be
    empty, but must exist and explicitly acknowledge that) are all present.
    """
    gaps: list[ProfileGap] = []
    pdir = profile_dir(root)

    profile_yaml = pdir / "profile.yaml"
    if not profile_yaml.exists():
        gaps.append(
            ProfileGap(
                object="se-buddy/profile.yaml",
                done_when="it exists with resolvable .capella/.aird paths, Capella version, and a project name",
            )
        )
    else:
        data = _load_yaml(profile_yaml) or {}
        for field in REQUIRED_PROFILE_FIELDS:
            if not data.get(field):
                gaps.append(
                    ProfileGap(
                        object=f"se-buddy/profile.yaml: {field}",
                        done_when=f"{field} is set",
                    )
                )

    domain_md = pdir / "domain.md"
    if not domain_md.exists():
        gaps.append(
            ProfileGap(
                object="se-buddy/domain.md",
                done_when="the domain pack exists (spec Sec.5.4)",
            )
        )
    else:
        # Existence was the whole check until now, which is how a real
        # install reported "profile complete" over a file still headed
        # "# Domain pack: <replace with your domain's name>". Sec.5.4's six
        # sections are binding as project requirements once recorded, so an
        # unreplaced skeleton is not an empty pack - it is example prose
        # being read as something the project asserts.
        #
        # One gap, not one per finding: `ask_store.sync_profile_gaps` keys an
        # ask on `object` alone, so N gaps sharing `se-buddy/domain.md` became
        # N asks that could then never be updated or resolved independently.
        # Caught against the real project, which grew ASK-0009 and ASK-0010
        # for one unfinished file. The findings ride along as `detail`.
        pack = domain_pack.check(domain_md.read_text(encoding="utf-8"))
        findings = pack.structural + pack.skeleton_signals
        if findings:
            gaps.append(
                ProfileGap(
                    object="se-buddy/domain.md",
                    done_when=(
                        "every spec Sec.5.4 section is present and filled in, with no "
                        "template placeholders or instructions left"
                    ),
                    detail=tuple(findings),
                )
            )

    viewpoints_yaml = pdir / "viewpoints.yaml"
    if not viewpoints_yaml.exists():
        gaps.append(
            ProfileGap(
                object="se-buddy/viewpoints.yaml",
                done_when="it exists with at least one viewpoint carrying design_rules and a priority",
            )
        )
    else:
        data = _load_yaml(viewpoints_yaml) or {}
        viewpoints = data.get("viewpoints") or []
        if not viewpoints:
            gaps.append(
                ProfileGap(
                    object="se-buddy/viewpoints.yaml",
                    done_when="at least one viewpoint is recorded, each with design_rules and a priority",
                )
            )
        else:
            for vp in viewpoints:
                if not vp.get("design_rules") or vp.get("priority") is None:
                    name = vp.get("name", "<unnamed>")
                    gaps.append(
                        ProfileGap(
                            object=f"se-buddy/viewpoints.yaml: {name}",
                            done_when="design_rules and priority are both set (spec Sec.9: rejected without both)",
                        )
                    )

    principles_yaml = pdir / "principles.yaml"
    if not principles_yaml.exists():
        gaps.append(
            ProfileGap(
                object="se-buddy/principles.yaml",
                done_when="it exists, even if empty - and empty is explicitly acknowledged (spec Sec.5.3)",
            )
        )
    else:
        data = _load_yaml(principles_yaml)
        if data is None or "principles" not in data:
            gaps.append(
                ProfileGap(
                    object="se-buddy/principles.yaml",
                    done_when="it explicitly acknowledges an empty list, e.g. `principles: []`",
                )
            )

    return gaps


def _load_yaml(path: Path):
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return None
    return yaml.safe_load(text)


class ProfileWriteError(Exception):
    """A `write profile` request could not be satisfied - reported plainly."""


_PROFILE_HEADER = """\
# se-buddy project profile (spec Sec.5.3, Sec.5.2 - PROFILE layer).
#
# Written by `se-buddy write-profile`, which is TTY-gated: every value below
# was read out of this project's own files (the .capella, its .aird, the
# .project descriptor) and then confirmed by the engineer at a terminal
# before it was written. Nothing here was invented by the agent, and nothing
# here was accepted without a human seeing where it came from.
#
# Re-run `se-buddy write-profile` to change any of it. Editing this file by
# hand also works and nothing will stop you - it is ordinary YAML - but the
# gated verb is what keeps `se-buddy doctor` and `se-buddy asks` agreeing
# with reality.
"""


def render_profile(fields: dict) -> str:
    """Renders `profile.yaml` from the four Sec.5.3 fields, header and all.

    Hand-rolled rather than `yaml.safe_dump`ed over the template because the
    header is the part that tells the next reader how this file came to say
    what it says, and a dump would drop every comment in it.
    """
    lines = [_PROFILE_HEADER, ""]
    width = max(len(f) for f in REQUIRED_PROFILE_FIELDS) + 2
    for field in REQUIRED_PROFILE_FIELDS:
        value = fields[field]
        # Quote anything YAML would otherwise read as a number or a bool -
        # `capella_version: 7.0` is a float, and `7.0.1` is not, so a project
        # on a two-part version would silently change type without this.
        rendered = yaml.safe_dump(value, default_flow_style=True).strip().rstrip("...").strip()
        lines.append(f"{field + ':':<{width}}{rendered}")

    last_ac = fields.get("last_acknowledged_ac")
    if last_ac:
        lines.append(f"{'last_acknowledged_ac:':<{width}}{last_ac}")
    else:
        lines.append("")
        lines.append("# The newest AGENT-LOG.md AC-nnnn this project has seen (spec Sec.5.5):")
        lines.append("# last_acknowledged_ac:")

    return "\n".join(lines) + "\n"


def validate_profile(root: Path, fields: dict) -> dict:
    """Checks the four fields are present and that both paths resolve.

    Path resolution is checked here rather than left to first use because
    Sec.5.3 asks for "resolvable .capella and .aird paths" specifically - a
    profile naming a file that isn't there is the failure mode that turns
    every later command's error into a confusing one.
    """
    cleaned: dict = {}
    for field in REQUIRED_PROFILE_FIELDS:
        value = fields.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ProfileWriteError(f"{field} is missing or empty - all four fields are required")
        cleaned[field] = value.strip() if isinstance(value, str) else value

    for field, suffix in (("model_path", ".capella"), ("aird_path", ".aird")):
        value = str(cleaned[field])
        if not value.endswith(suffix):
            raise ProfileWriteError(f"{field} is {value!r}, which does not end in {suffix}")
        if not (root / value).is_file():
            raise ProfileWriteError(f"{field} is {value!r}, which does not resolve under {root}")

    if "last_acknowledged_ac" in fields:
        cleaned["last_acknowledged_ac"] = fields["last_acknowledged_ac"]
    return cleaned


def write_profile(root: Path, fields: dict) -> Path:
    """Validates and writes `se-buddy/profile.yaml`. Raises `ProfileWriteError`."""
    cleaned = validate_profile(root, fields)
    pdir = profile_dir(root)
    pdir.mkdir(parents=True, exist_ok=True)
    path = pdir / "profile.yaml"
    atomic_write_text(path, render_profile(cleaned))
    return path


def write_domain(root: Path, text: str) -> Path:
    """Validates and writes `se-buddy/domain.md`. Raises `ProfileWriteError`.

    Refuses on structural gaps only (a required Sec.5.4 section missing or
    empty). The skeleton heuristics - leftover placeholders, the template's
    own instructions - are reported by `se_buddy.domain_pack` and shown in
    the write gate, deliberately without a veto: see that module's docstring.
    """
    gaps = domain_pack.check(text)
    if gaps.structural:
        raise ProfileWriteError(
            "domain.md is missing required spec Sec.5.4 content: " + "; ".join(gaps.structural)
        )
    pdir = profile_dir(root)
    pdir.mkdir(parents=True, exist_ok=True)
    path = pdir / "domain.md"
    atomic_write_text(path, text if text.endswith("\n") else text + "\n")
    return path
