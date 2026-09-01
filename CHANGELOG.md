# Changelog

Human-facing summary of what shipped, release by release. For the
per-change audit trail (surface/breaking/action/why, spec Sec.5.5), see
[AGENT-LOG.md](AGENT-LOG.md); for what's enforced vs. instructed against
the spec, see [SPEC-COVERAGE.md](SPEC-COVERAGE.md).

## Unreleased

First real install into a project that isn't this repo, and everything
that install broke. Nothing here changes what the agent may assert or who
authorises it; it is all install path, project setup, and one piece of
Sec.5.2 that was specified and never built.

### Added

**`profile.yaml` is detected, not typed.** Its four fields are facts the
project already records — the one `.capella` in the root, its `.aird`, the
`Capella_Version` marker inside the model, the `<name>` in Eclipse's
`.project` — so `se_buddy.profile_detect` reads them and shows each with
the file it came from. `se-buddy write-profile` (new, TTY-gated) writes
them after the engineer confirms values they can see the source of. Pass a
YAML file to override any of them; that is the ordinary path, not an
escape hatch. A partial detection refuses rather than writing three fields
out of four, which would read as configured and fail later.

**`se-buddy write-domain` (new, TTY-gated)** replaces hand-editing
`domain.md` in a text editor. `project-init` now interviews the six spec
Sec.5.4 sections, drafts the pack, and hands it to the engineer to write.
This is the `write-memory viewpoints` pattern — agent-drafted, engineer-run
— applied to the one piece of engineering judgement that was previously
*ungated and forbidden*, and therefore fell through to Notepad. What stays
forbidden is unchanged and is the point of the interview: the agent must
not supply the judgement, only transcribe it.

**`se-buddy write-claude-md` (new)** generates the consuming project's thin
`CLAUDE.md` (spec Sec.5.2), which was specified and never built. It points
at `se-buddy/` and states the rules that always hold, and carries no
architectural content. Not gated, because it writes only between two
markers and never touches anything outside them: no `CLAUDE.md` creates
one, an existing block is replaced in place, an existing file without one
is appended to. Re-running it is idempotent.

### Fixed

**`doctor` no longer claims more than it checked.** It reported
"installation is sound" — interpreter, venv, pin and profile all `[ok]` —
on an install where Claude Code had loaded none of the eighteen skills.
Every line of that report was true; none of it answered the question being
asked. `doctor` now prints three sections (`install`, `runtime`,
`profile`), and its closing line distinguishes "the deterministic layer is
sound" from "the plugin is loaded".

The new `install` section (`src/se_buddy/install.py`) checks the manifest,
the on-disk layout, and — the one that actually bit — whether the working
directory *is* the project root, since a project-scope skills-directory
plugin loads only from the session's primary working directory and does
not walk up. It also checks `hooks/hooks.json` is present and parseable,
because the `PreToolUse` write guards are one of the two write-protection
layers and they exist only while the plugin is loaded.

**A plugin load can now be confirmed.** `/se-buddy:doctor` (new skill)
runs `se-buddy doctor` and reports it. Its real output is the fact that it
ran at all: a slash command cannot resolve unless the plugin carrying it
loaded, so this is proof by construction rather than a check. `doctor`
itself can report a load positively where the plugin's `bin/` is on
`PATH`, and reports an explicit unknown otherwise — never a failure, since
a human running the launcher from a terminal is the expected case.

**Rust is no longer a prerequisite on any platform that has a wheel.**
`bin/_bootstrap.py` installed capellambse by building
`vendor/py-capellambse` from source unconditionally, which needs `rustc`
and `cargo`, and which for a systems engineer rather than a developer is
where the install tended to stop. It now installs the pinned version from
a prebuilt wheel (`--only-binary`) and falls back to the vendored source
only where no wheel matches — which is also the only path that still
demands Rust, and the message now says so and why. Verified by rebuilding
the venv from scratch with Rust removed from `PATH`.

The trade, stated plainly: the submodule pinned an exact commit and a
version pin does not. `==` still fixes the version and `doctor` still
refuses on drift (spec Sec.7.1), but the artefact now comes from an index
rather than a SHA this repository records. Hash-pinning the wheel in
`lockfile` would recover that and is not done here.

**"profile complete" over an unedited template.** `check_completeness`
asked only whether `domain.md` existed. On the real install that meant a
pack whose heading still read `# Domain pack: <replace with your domain's
name>`, with the template's own instructions to the reader above it,
counted as complete. `se_buddy.domain_pack` now checks the six Sec.5.4
sections and reports leftover skeleton markers, split deliberately:
structural gaps (a section missing or empty) are facts and `write-domain`
refuses on them; placeholder detection is a heuristic and only ever
reports — as `SUPPLY` asks, and in the write gate where a human reads it.

**The write-guard hook would have blocked `write-claude-md`.** Its verb
pattern was `write-(\w+)`, which stops at a hyphen, so it read
`write-claude-md` as the verb `write-claude` — not in its exemption set,
so it blocked an ungated verb the agent is meant to run, naming a verb
that does not exist. The pattern now accepts hyphenated verb names and the
exemption set is explicit (`propose`, `claude-md`). An unknown
`write-x-y` still fails closed.

**Two detection bugs, both caught by tests against a real model.** The
`Capella_Version` pattern's character class swallowed the `-->` closing
its own comment, yielding `7.0.1--`. The `.afm` fallback matched the first
`version="..."` in the file, which is the XML declaration's `version="1.0"`
— it would have written `capella_version: 1.0` into a real profile. Both
are now anchored, and the `.afm` path prefers the Capella core viewpoint's
own version where a project references several.

### Changed

README: Install is now six numbered steps, with the two that decide
whether anything works — start at the project root, accept workspace trust
— called out rather than implied, plus a symptom/cause/fix Troubleshooting
table. Examples use `se-buddy` as a bare command, which is what it is
inside Claude Code once the plugin's `bin/` reaches `PATH`; the explicit
local path is given as the outside-Claude-Code form rather than the only
form. Prerequisites no longer lists Rust unconditionally.

`project-init`'s skill was rewritten around the interview flow. Its old
rule - that `profile.yaml` and `domain.md` are "permanently hand-edited
by design" - was a skill-level decision, not a spec constraint: Sec.5.4
requires the pack to exist and be project-supplied, and never says a
human must type it into an editor.

246 tests pass (was 179).

## v0.1.0 — 2026-08-31

First release. Phases 0–3 of the spec's four-phase plan
([log/log-0001-se_buddy_agent_spec.md](log/log-0001-se_buddy_agent_spec.md)
Sec.11). Phase 4 (a second project installing this fresh) is the one
remaining gate before this is proven outside its own development.

### Added

**Bootstrap.** `bin/se-buddy` / `bin/se-buddy.cmd` build and repair their
own virtualenv on every run, from the vendored `capellambse` submodule and
a pinned lockfile — never an index install. `se-buddy doctor` reports and
repairs venv/interpreter/version problems.

**Reading a model.** `inspect`, `search`, `show`, `trace`, `asks` — bounded
output, truncation always stated, behavioural elements (functional chains,
scenarios, state machines) read generically rather than judged.

**Project memory.** Six registers (Sec.6.2), principles, viewpoints,
glossary, assumptions and ADRs — readable via `register`/`memory`/`show`,
writable via the TTY-gated `write-register`/`write-memory`/`write-answer`.
`write-baseline` records a manifest (model hash, register statuses, open
asks) and a git tag.

**Controlled model modification, end to end.** `write-propose` files a
proposal as a real `capellambse.decl` document (automatic authority, no
gate — a proposal asserts nothing yet). `plan` dry-runs it with nothing
written to disk. `write-apply` runs the full lifecycle — check the tree is
clean, check for drift since the proposal was filed, snapshot the model,
apply, re-parse, run six validation layers, write the change record —
restoring the pre-apply snapshot on any failure. `write-revert` restores a
change from its snapshot. `validate` runs five real, automated layers plus
an honest `UNKNOWN` for the one layer (`architectural`) no deterministic
check can judge on its own.

**Two independent write-safety layers.** The TTY gate (`se_buddy/gate.py`)
refuses every write verb except `write-propose` unless run by a human at a
real interactive terminal — no bypass flag exists, by design. `PreToolUse`
hooks (`hooks/hooks.json`) independently block the same verbs, and direct
edits to `.capella`/`.aird`, before Claude Code's own tool-dispatch loop
gets there.

**Eighteen skills** (`skills/`) covering project setup, the architecture
track, and the modelling track, each following the spec's ten-section
shape and citing the shared cross-cutting-behaviour/deliberation-discipline
references instead of restating them.

### Fixed (pre-release hardening pass)

Before this release was pointed at a real Capella project, the full
implementation — every phase, not just the latest diff — was reviewed for
defects. 15 confirmed findings were fixed, each with a regression test,
plus two more of the same severity found while writing those tests. Full
detail: SPEC-COVERAGE.md's "Phase 3 hardening pass" section; summary:
AGENT-LOG.md's `AC-0006`.

The two most consequential: `--delete` was checked for diagram references
only when the flag was passed, never enforced as *required* when a
proposal actually deleted something; and the dirty-tree check silently
passed a genuinely dirty tree whenever the model lived in a subdirectory,
because of a doubled path segment. Also fixed: two swallowed-exception
gaps in the apply lifecycle, an unvalidated baseline name (path
traversal), a crash instead of a clean refusal in `write-revert`'s most
common scenario, a dropped-row bug in `write-memory`'s save path, a
missing `show`-command dispatch branch for principles/assumptions, an
edge-dropping bug in `trace`'s reverse closure, an uncaught `EOFError` in
the TTY gate, a write-order bug that could silently lose an owed diagram
followup on a crash, a write-verb-blocking hook regex too narrow to catch
its own module-invocation form, and two schema presence-check bugs. Every
YAML writer in the codebase was also switched to an atomic write (temp
file + rename), so a crash mid-write can no longer corrupt a record.

### Known gaps (by design, not oversight)

- `se-buddy perspective [<layer>]` — not built; `arch-perspective`'s skill
  works without it.
- `se-buddy export`/`model-export` — needs `capellambse-context-diagrams`,
  not vendored; the skill documents the procedure without a working
  command.
- A generated, thin `CLAUDE.md` in a *consuming* project (spec Sec.5.2) —
  `project-init` scaffolds the profile but does not yet generate this
  file.
- Phase 4 (a second, independently installed project) has not been
  exercised.
- The TTY gate's positive path (a human actually confirming) and the
  `PreToolUse` hooks firing inside a real, enabled Claude Code session
  cannot be verified by the agent that builds this — both are unit-tested
  on their own logic, but neither has been watched happen live yet.
