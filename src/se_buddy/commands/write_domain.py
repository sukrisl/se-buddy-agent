"""`se-buddy write-domain draft.md` (spec Sec.5.4).

The verb that ends `domain.md`'s hand-editing - without ending the
engineer's authorship of it.

`domain.md` is engineering judgement, and spec Sec.5.4 makes every word of
it binding as a project requirement, so the agent must not invent it. That
much the old design had right. What it got wrong was the conclusion: it
forbade the agent from writing the file *at all* and sent the engineer to a
text editor with a six-section template. The result, on the first real
install, was a domain pack carrying genuine content under the heading
"# Domain pack: <replace with your domain's name>", with the template's own
instructions to the reader still sitting above it - and `doctor` calling
that complete.

The authority model this codebase already uses everywhere else fits here
exactly. `write-memory viewpoints` is also engineering judgement, and it is
agent-drafted and TTY-gated: the agent writes down what the engineer said,
the engineer runs the write. Transcription under a gate is not invention.
`domain.md` was the one piece of judgement that was ungated *and*
forbidden, so it fell through to Notepad - an asymmetry that cost the whole
authoring experience and bought no safety that the gate does not already
provide.

So: `project-init` interviews, drafts, and hands the draft to the engineer,
who runs this. It refuses on structural gaps (a Sec.5.4 section missing or
empty) and *reports* the skeleton heuristics in the gate prompt, where a
human reads them before typing anything - see `se_buddy.domain_pack` on why
a heuristic must not acquire a veto.
"""

from __future__ import annotations

from pathlib import Path

from se_buddy import domain_pack
from se_buddy.gate import GateRefused, confirm
from se_buddy.profile import ProfileWriteError, write_domain


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser(
        "write-domain", help="write se-buddy/domain.md from a drafted pack (spec Sec.5.4)"
    )
    parser.add_argument("draft_file", help="path to the drafted domain pack, in Markdown")
    parser.set_defaults(func=run)


def write_text(root: Path, text: str) -> Path:
    return write_domain(root, text)


def run(args) -> int:
    path = Path(args.draft_file)
    if not path.exists():
        print(f"se-buddy: {path} does not exist")
        return 1
    text = path.read_text(encoding="utf-8")

    gaps = domain_pack.check(text)
    if gaps.structural:
        print(f"se-buddy: {path} is not a complete domain pack (spec Sec.5.4):")
        for gap in gaps.structural:
            print(f"  - {gap}")
        return 1

    root = Path.cwd()
    existing = root / "se-buddy" / "domain.md"

    print(f"About to write se-buddy/domain.md from {path}")
    print(f"  all six spec Sec.5.4 sections present, {len(text)} bytes")
    if existing.exists():
        print(f"  this REPLACES the existing {existing} ({existing.stat().st_size} bytes)")
    if gaps.skeleton_signals:
        # Surfaced, never used to refuse. A human reading this before typing
        # a confirmation is the check; a regex is not entitled to be one.
        print("  still looks partly unedited:")
        for signal in gaps.skeleton_signals:
            print(f"    - {signal}")
    print()

    try:
        confirm("Write this domain pack to se-buddy/domain.md?")
    except GateRefused as exc:
        print(f"se-buddy: {exc}")
        return 1

    try:
        written = write_text(root, text)
    except ProfileWriteError as exc:
        print(f"se-buddy: {exc}")
        return 1

    print(f"wrote {written}")
    return 0
