"""Shared test fixtures.

Only what more than one test module needs. `complete_domain_pack()` arrived
with AC-0008: `check_completeness` now checks `domain.md`'s *content* against
spec Sec.5.4's six sections, not just its existence, so a test that wants a
complete profile can no longer get away with writing `# Domain\\n`.
"""

from __future__ import annotations

from se_buddy.domain_pack import REQUIRED_SECTIONS


def complete_domain_pack() -> str:
    """The smallest `domain.md` that satisfies spec Sec.5.4.

    Deliberately built from `REQUIRED_SECTIONS` rather than pasted, so that
    adding a required section makes every test using this fixture keep
    passing for the right reason instead of silently going stale.
    """
    lines = ["# Domain pack: example", ""]
    for section in REQUIRED_SECTIONS:
        lines += [f"## {section}", "", f"Real content for {section.lower()}.", ""]
    return "\n".join(lines)
