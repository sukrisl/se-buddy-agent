"""Project-init scaffolding (spec Sec.5.3).

Creates the profile skeleton without the TTY gate: it asserts no
engineering content, only creates a container the engineer then edits and
commits themselves - the same carve-out spec Sec.7.3 gives `write propose`.
Filling these templates with real judgement (a real viewpoint, a real
principle) is `se-buddy write memory`, which needs the TTY gate that
arrives in Phase 2 - so this module only ever copies inert template text,
never invents profile content itself.
"""

from __future__ import annotations

from pathlib import Path

from se_buddy.profile import profile_dir

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"
DOMAINS_DIR = TEMPLATES_DIR / "domains"


class ScaffoldError(Exception):
    """A scaffold request could not be satisfied - reported plainly."""


def available_domain_packs() -> list[str]:
    return sorted(p.stem for p in DOMAINS_DIR.glob("*.md"))


def scaffold_profile(root: Path, *, domain_pack: str, force: bool = False) -> list[Path]:
    """Writes the four spec Sec.5.3 skeleton files under `root/se-buddy/`.

    Refuses to overwrite an existing file unless `force=True` - scaffolding
    is for a new project; clobbering an existing, possibly-edited profile
    is a different and much riskier action this function deliberately does
    not perform.
    """
    if domain_pack not in available_domain_packs():
        raise ScaffoldError(
            f"no domain pack named {domain_pack!r}; available: {available_domain_packs()}"
        )

    pdir = profile_dir(root)
    pdir.mkdir(parents=True, exist_ok=True)

    written = [
        _copy(pdir / "profile.yaml", TEMPLATES_DIR / "profile.yaml", force),
        _copy(pdir / "domain.md", DOMAINS_DIR / f"{domain_pack}.md", force),
        _copy(pdir / "viewpoints.yaml", TEMPLATES_DIR / "viewpoints.yaml", force),
        _copy(pdir / "principles.yaml", TEMPLATES_DIR / "principles.yaml", force),
    ]
    return written


def _copy(dest: Path, source: Path, force: bool) -> Path:
    if dest.exists() and not force:
        raise ScaffoldError(
            f"{dest} already exists - project-init does not overwrite an existing profile"
        )
    dest.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return dest
