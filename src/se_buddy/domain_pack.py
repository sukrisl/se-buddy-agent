"""What makes `se-buddy/domain.md` a domain pack rather than a skeleton.

Spec Sec.5.4 names six sections `domain.md` **MUST** contain, and Sec.5.4's
closing rule is what makes them load-bearing: "everything in `domain.md` is
binding as a project requirement". `arch-review` reads the attack-surface
section as project requirements rather than as advisory best practice
(C02/D5), so a section that is still template text is not a harmless
omission - it is unreplaced example prose being treated as something the
project asserts.

Until now nothing checked any of this. `check_completeness` asked only
whether the file existed, which is why a real install could report "profile
complete" over a `domain.md` whose heading still read
"# Domain pack: <replace with your domain's name>" and whose standards
section still read "- <standard> <clause> - <what it requires, one line>".

Two kinds of gap, deliberately kept apart because they carry different
authority:

  - **structural** (a required section is missing, or has no body): a fact
    about the document, not a judgement. `write domain` refuses on these.
  - **skeleton signals** (leftover `<placeholder>` markers, the template's
    own instructions to the reader): a heuristic. A domain pack could in
    principle contain angle-bracket prose legitimately, so these are
    surfaced - in the write gate, and as `SUPPLY` asks - and never used to
    refuse. Sec.5.3 is explicit that completeness "reports what is missing",
    it does not block, and a heuristic is exactly the kind of check that
    must not acquire a veto.
"""

from __future__ import annotations

import dataclasses
import re

#: Spec Sec.5.4's table, in its order. Matched case-insensitively against
#: `##` headings so a project may capitalise its own headings differently.
REQUIRED_SECTIONS = (
    "Applicable standards",
    "Lifecycle crosswalk",
    "Baseline viewpoints",
    "Evidence expectations",
    "Reviewer attack surfaces",
    "Verification patterns",
)

#: A leftover fill-me-in marker from `templates/domains/*.md`, e.g.
#: `<standard>`, `<what it requires, one line>`, `<n>`. Anchored on a
#: lowercase first character and forbidden from spanning a line so that
#: ordinary prose (`Foo<Bar>`, a stray `<`) is less likely to trip it - and
#: because this is a heuristic either way, every hit is reported verbatim so
#: a false positive is visible as one rather than mysterious.
_PLACEHOLDER = re.compile(r"<[a-z][^<>\n]*>")

#: The instruction paragraph `templates/domains/*.md` opens with. Its
#: presence means the file was copied and not yet rewritten - it addresses
#: the reader, so it cannot be part of a real pack.
_TEMPLATE_PREAMBLE = "Copy this file to"

_HEADING = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


@dataclasses.dataclass(frozen=True)
class DomainPackGaps:
    """What `domain.md` still lacks. Empty on every count means complete."""

    missing_sections: list[str]
    empty_sections: list[str]
    placeholders: list[str]
    has_template_preamble: bool

    @property
    def structural(self) -> list[str]:
        """Gaps that are facts about the document - `write domain` refuses on these."""
        return [f"section {s!r} is missing" for s in self.missing_sections] + [
            f"section {s!r} has no content" for s in self.empty_sections
        ]

    @property
    def skeleton_signals(self) -> list[str]:
        """Gaps that are heuristics - reported, never used to refuse."""
        signals: list[str] = []
        if self.has_template_preamble:
            signals.append(
                "the template's own instructions to the reader are still present "
                f"({_TEMPLATE_PREAMBLE!r} ...)"
            )
        if self.placeholders:
            shown = ", ".join(self.placeholders[:5])
            more = f" (+{len(self.placeholders) - 5} more)" if len(self.placeholders) > 5 else ""
            signals.append(f"{len(self.placeholders)} unreplaced placeholder(s): {shown}{more}")
        return signals

    @property
    def is_complete(self) -> bool:
        return not self.structural and not self.skeleton_signals


def _sections(text: str) -> dict[str, str]:
    """Maps each `##` heading (lowercased) to the body text beneath it."""
    matches = list(_HEADING.finditer(text))
    found: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        found[match.group(1).strip().lower()] = text[start:end]
    return found


def check(text: str) -> DomainPackGaps:
    """Reports every gap in `text` as a domain pack (spec Sec.5.4)."""
    sections = _sections(text)

    missing: list[str] = []
    empty: list[str] = []
    for required in REQUIRED_SECTIONS:
        body = sections.get(required.lower())
        if body is None:
            missing.append(required)
        elif not body.strip():
            empty.append(required)

    placeholders = sorted(set(_PLACEHOLDER.findall(text)))

    return DomainPackGaps(
        missing_sections=missing,
        empty_sections=empty,
        placeholders=placeholders,
        has_template_preamble=_TEMPLATE_PREAMBLE in text,
    )
