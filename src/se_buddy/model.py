"""Model loading (spec Sec.6.3, Sec.7.1).

Every `se-buddy` invocation is a fresh process (spec Sec.5.1) - there is
deliberately no cross-invocation cache of the *parsed* model here. Why:
`capellambse.MelodyModel` wraps live `lxml.etree._Element` objects and does
not survive `pickle` (confirmed directly against the real vendored
capellambse: `pickle.dumps(model)` raises `TypeError: cannot pickle
'lxml.etree._Element' object`), and building a second, serializable index of
model facts to work around that would itself violate Sec.6.3's "every fact
has exactly one representation" - a stale second copy of the model is
exactly what that principle rules out.

On the one real fixture measured (`vendor/py-capellambse/tests/data/models/
test7_0`, a 1,484-element Capella 7.0 model, ~2.4 MB `.aird` + ~366 KB
`.capella`), cold parse costs ~250-370ms. That number, and the pickling
failure, are recorded in SPEC-COVERAGE.md as direct evidence for spike 6
(bin/ vs MCP, Sec.12) rather than routed around here with home-grown
caching machinery.

`hash_model_files` is built anyway: Sec.10.2's apply lifecycle needs a model
hash to detect drift ("the model hash matches what was last parsed"), and
that hashing logic doesn't depend on anything write-path-specific.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import capellambse
import yaml
from capellambse import cli_helpers

from se_buddy.profile import profile_dir


class ModelResolutionError(Exception):
    """No model could be found or loaded - reported plainly, never a raw
    capellambse traceback, for the failure modes an engineer hits day to
    day (spec Sec.5.1's "never a stack trace" applied to this layer too)."""


def resolve_model_path(root: Path, explicit: str | None) -> str:
    """Resolves what to hand to `capellambse.MelodyModel`.

    `explicit` (a CLI `--model` value) always wins. Otherwise falls back to
    `se-buddy/profile.yaml`'s `aird_path` - the profile is what a real
    project uses; `--model` exists for development, and for reasoning ahead
    of a completed profile (spec Sec.5.3: "the agent MAY retrieve, explain
    and reason" before the profile is complete).
    """
    if explicit:
        return explicit

    profile_yaml = profile_dir(root) / "profile.yaml"
    if not profile_yaml.exists():
        raise ModelResolutionError(
            "no --model given and se-buddy/profile.yaml does not exist yet. "
            "Pass --model <path to .aird>, or run project-init first."
        )

    data = yaml.safe_load(profile_yaml.read_text(encoding="utf-8")) or {}
    aird_path = data.get("aird_path")
    if not aird_path:
        raise ModelResolutionError(
            "se-buddy/profile.yaml has no aird_path set yet - pass --model <path to .aird>"
        )
    return aird_path


def load_model(root: Path, explicit: str | None = None) -> capellambse.MelodyModel:
    """Loads a model, resolving its location per `resolve_model_path`.

    Catches every exception `loadcli`/the underlying parse can raise, not a
    hand-picked subset - a code review found `lxml` XML-syntax errors and a
    few other capellambse-internal failure types slipping past the original
    `(FileNotFoundError, ValueError, TypeError)` list as raw tracebacks, the
    exact thing this function exists to prevent. `KeyboardInterrupt`/
    `SystemExit` still propagate since they're not `Exception` subclasses.
    """
    path = resolve_model_path(root, explicit)
    try:
        return cli_helpers.loadcli(path)
    except Exception as exc:
        raise ModelResolutionError(f"could not load a model from {path!r}: {exc}") from exc


def hash_model_files(aird_path: str | Path) -> str:
    """Hashes the `.afm`/`.aird`/`.capella` fragments of a local,
    single-fragment model (same stem, sibling files - the layout every
    vendored fixture and every real single-model project uses). Missing
    siblings are skipped, so this also works against a bare `.aird` in
    isolation. A remote or multi-fragment/library model's drift story is a
    separate, unopened question (spec Sec.12's open items).
    """
    aird = Path(aird_path)
    hasher = hashlib.sha256()
    for suffix in (".afm", ".aird", ".capella"):
        sibling = aird.with_suffix(suffix)
        if sibling.exists():
            hasher.update(sibling.read_bytes())
    return hasher.hexdigest()
