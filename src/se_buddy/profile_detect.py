"""Deriving `profile.yaml`'s four fields from the project on disk (spec Sec.5.3).

`project-init` used to scaffold `profile.yaml` as four empty keys and tell
the engineer to fill them in by hand, on the grounds that nothing
project-specific may be agent-authored (spec Sec.5). That reasoning holds
for `domain.md`, which is engineering judgement. It does not hold here.

All four fields are facts already recorded in the project's own files:

  model_path       the .capella file in the project root
  aird_path        the matching .aird
  capella_version  the `Capella_Version_x.y.z` marker Capella writes into
                   the .capella itself, or the viewpoint `version` in the .afm
  project_name     the `<name>` in Eclipse's .project descriptor

Reading a fact out of a file the engineer already committed is retrieval,
not invention, so this module reads them. What it does *not* do is decide
they are true: every field comes back with the provenance it was read from,
`project-init` shows both, and the value reaches `profile.yaml` only through
the TTY-gated `write profile` - so the engineer confirms a value they can
see the source of, rather than typing out four things the tool could already
see. Where a project disagrees (`.project` says `model-iot_platform`, the
engineer wants `IoT Platform`), overriding is the normal path, not an
escape hatch.

Everything here degrades to `None` with a stated reason rather than
guessing. Two `.capella` files in one root is an ambiguity only the engineer
can settle, and a silent pick of the alphabetically-first one would be
exactly the kind of confident wrong answer this project's spec spends
Sec.3 preventing.
"""

from __future__ import annotations

import dataclasses
import re
from pathlib import Path

#: A version like `7.0.1`, or `7.0.1-rc1`. Every `-` must be followed by at
#: least one alphanumeric, which is what stops the `.capella` pattern below
#: swallowing the `-->` that closes the comment it lives in - caught against
#: a real model, where the naive charset yielded "7.0.1--".
_VERSION = r"[0-9][0-9A-Za-z.]*(?:-[0-9A-Za-z.]+)*"

#: Capella writes this comment into the second line of every `.capella`
#: file, e.g. `<!--Capella_Version_7.0.1-->`.
_CAPELLA_VERSION = re.compile(rf"Capella_Version_({_VERSION})")

#: The `.afm` records the same version as an attribute of a
#: `<viewpointReferences>` element. Anchored on that element name rather than
#: on `version="` alone, because every `.afm` opens with an XML declaration
#: carrying `version="1.0"` and a bare match returns *that* - caught by test,
#: and it would have put `capella_version: 1.0` into a real profile.
#: `(?<![-:\w])` keeps it off `xmi:version` for the same reason.
_AFM_VERSION = re.compile(rf'<viewpointReferences[^>]*(?<![-:\w])version="({_VERSION})"')

#: Preferred over any other `<viewpointReferences>` when a file has several:
#: the Capella core viewpoint is the one whose version `profile.yaml` means.
_AFM_CORE_VIEWPOINT = re.compile(
    rf'<viewpointReferences[^>]*vpId="org\.polarsys\.capella\.core\.viewpoint"'
    rf'[^>]*(?<![-:\w])version="({_VERSION})"'
)

#: Eclipse's project descriptor. Same reasoning as above - one element.
_PROJECT_NAME = re.compile(r"<name>\s*(.+?)\s*</name>", re.DOTALL)

#: Only the head of a `.capella` is read: they run to megabytes, and both
#: markers this module wants sit in the first few lines.
_HEAD_BYTES = 8192

FIELDS = ("model_path", "aird_path", "capella_version", "project_name")


@dataclasses.dataclass(frozen=True)
class Detected:
    """One field, and where its value came from - or why there isn't one."""

    value: str | None
    provenance: str

    @property
    def found(self) -> bool:
        return self.value is not None


@dataclasses.dataclass(frozen=True)
class Detection:
    model_path: Detected
    aird_path: Detected
    capella_version: Detected
    project_name: Detected

    def as_dict(self) -> dict[str, str]:
        """Only the fields that were actually found - never a `None` value."""
        return {
            field: getattr(self, field).value
            for field in FIELDS
            if getattr(self, field).found
        }

    def undetermined(self) -> list[str]:
        return [field for field in FIELDS if not getattr(self, field).found]

    def rendered(self) -> list[str]:
        """One `field: value  (from ...)` line per field, for the engineer to read."""
        lines = []
        for field in FIELDS:
            found = getattr(self, field)
            value = found.value if found.found else "<not determined>"
            lines.append(f"{field}: {value}  (from {found.provenance})")
        return lines


def _read_head(path: Path) -> str:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            return handle.read(_HEAD_BYTES)
    except OSError as exc:
        return f"<unreadable: {exc}>"


def _single(root: Path, pattern: str) -> Detected:
    """The one file matching `pattern` in `root`, or a stated reason there isn't."""
    try:
        matches = sorted(p for p in root.glob(pattern) if p.is_file())
    except OSError as exc:
        return Detected(None, f"{root} could not be listed: {exc}")

    if not matches:
        return Detected(None, f"no {pattern} file in {root}")
    if len(matches) > 1:
        names = ", ".join(p.name for p in matches)
        return Detected(
            None,
            f"{len(matches)} {pattern} files in {root} ({names}) - name the right one yourself",
        )
    return Detected(matches[0].name, f"the only {pattern} in {root}")


def _capella_version(root: Path, model: Detected) -> Detected:
    if model.found:
        head = _read_head(root / model.value)
        match = _CAPELLA_VERSION.search(head)
        if match:
            return Detected(match.group(1), f"the Capella_Version marker in {model.value}")

    afm = _single(root, "*.afm")
    if afm.found:
        head = _read_head(root / afm.value)
        # The core viewpoint's own version first; any viewpoint reference
        # second. A project with several referenced viewpoints would
        # otherwise report whichever happened to be declared first.
        match = _AFM_CORE_VIEWPOINT.search(head) or _AFM_VERSION.search(head)
        if match:
            return Detected(match.group(1), f"the viewpoint version in {afm.value}")

    return Detected(None, "no Capella_Version marker in the .capella and no readable .afm")


def _project_name(root: Path) -> Detected:
    descriptor = root / ".project"
    if not descriptor.is_file():
        return Detected(None, f"no .project descriptor in {root}")
    match = _PROJECT_NAME.search(_read_head(descriptor))
    if not match:
        return Detected(None, "the .project descriptor has no <name> element")
    return Detected(match.group(1), "the <name> in .project")


def detect(root: Path) -> Detection:
    """Reads what `profile.yaml`'s four fields can be read from, under `root`."""
    model = _single(root, "*.capella")
    return Detection(
        model_path=model,
        aird_path=_single(root, "*.aird"),
        capella_version=_capella_version(root, model),
        project_name=_project_name(root),
    )
