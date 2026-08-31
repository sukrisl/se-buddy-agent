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

PROFILE_DIRNAME = "se-buddy"


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
        for field in ("model_path", "aird_path", "capella_version", "project_name"):
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
