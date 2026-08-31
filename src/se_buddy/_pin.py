"""Reads the capellambse pin out of pyproject.toml.

Stdlib-only, on purpose: bin/_bootstrap.py imports this module under the bare
system interpreter, before the vendored venv (and therefore capellambse)
exists. Keeping this file free of third-party imports is what lets it be
imported at that point.

pyproject.toml is the single place the pin is written (spec Sec.7.1: "the two
[pyproject.toml and the vendored submodule] MUST agree"). Both the bootstrap
and `se-buddy doctor` read it from here rather than each carrying their own
copy of the version string.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

# Floor set by the capellambse==0.8.1 pin (v0.8.1 dropped Python 3.10) -
# spec Sec.5.1: "Python floor Set by the pin, not by us". Not derived
# automatically because nothing installable exists yet at the point this is
# checked; move it only alongside a pin change, per Sec.7.1.
MIN_PYTHON = (3, 11)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_pin() -> str:
    """Returns the pinned capellambse version, e.g. "0.8.1"."""
    pyproject = repo_root() / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    for dep in data.get("project", {}).get("dependencies", []):
        if dep.startswith("capellambse=="):
            return dep.split("==", 1)[1].strip()
    raise LookupError(
        f"{pyproject} does not pin capellambse==<version> under [project.dependencies]"
    )
