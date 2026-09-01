---
name: project-init
description: Take a project from "just installed the submodule" to a complete profile - detect profile.yaml from the project's own files, interview the domain pack, and gate on completeness.
---

# project-init

## Purpose

Get a new project from "just installed the submodule" to a profile
`se-buddy doctor` reports as complete (spec Sec.5.3): `profile.yaml`,
`domain.md`, `viewpoints.yaml`, `principles.yaml`.

The engineer supplies the judgement. This skill supplies everything that
is not judgement — which is more than it used to be, and the difference is
the point. `profile.yaml`'s four fields are facts already written in the
project's own files; the domain pack is judgement, but *transcribing* an
engineer's judgement under a write gate is what `write-memory` already
does everywhere else in this agent. Neither is a reason to hand someone a
six-section template and a text editor.

## When to invoke

A fresh project with no `se-buddy/` directory, or an existing one where
`se-buddy doctor` still reports `SUPPLY` asks against the profile. Run
`/se-buddy:doctor` first on a fresh install — an incomplete profile and an
unloaded plugin look similar from the outside and have nothing to do with
each other.

## Inputs

Nothing required. A domain pack choice
(`se_buddy.scaffold.available_domain_packs()` names what's shipped in
`templates/domains/`, e.g. `generic`, `aerospace-arp4754a`) if the
engineer wants to start from one; the six sections are interviewed either
way.

## Context required

The project root (for detection), and `templates/` for any pack used as a
starting shape.

## Procedure

1. **Scaffold the containers** (`se_buddy.scaffold.scaffold_profile`) if
   `se-buddy/` does not exist. Inert template text, no gate, refuses to
   overwrite. Ask which domain pack to start from, or confirm `generic` —
   never guess a domain silently.

2. **Detect `profile.yaml`** (`se_buddy.profile_detect.detect`). Show all
   four fields **with the file each was read from** — the provenance is
   not decoration, it is what lets the engineer check the value instead of
   trusting it. Where detection came up empty, say what was looked at and
   why it failed; never fill the gap yourself.

3. **Have the engineer run `se-buddy write-profile`** — TTY-gated, so they
   run it, not you. It re-detects, shows the same four lines, and writes
   only after a typed confirmation. Where a value should differ from what
   the project records (`.project` says `model-iot_platform`, the engineer
   wants `IoT Platform`), that is `se-buddy write-profile fields.yaml`
   with a file you drafted — the ordinary path, not an escape hatch.

4. **Interview the domain pack.** Six sections, spec Sec.5.4:

   | Section | What to ask for |
   | --- | --- |
   | Applicable standards | Which standards *this* project is held to, and the clauses a reviewer will actually cite — not every standard in the domain |
   | Lifecycle crosswalk | Their lifecycle phases, mapped onto the five Arcadia perspectives, and the artefact expected at each |
   | Baseline viewpoints | The non-functional concerns, each with design rules and a priority order |
   | Evidence expectations | What a reviewer, auditor or customer asks to see, and at which gate |
   | Reviewer attack surfaces | Known anti-patterns: the mistake, why it is wrong, the correct approach |
   | Verification patterns | How each kind of claim in this domain is normally verified |

   Ask; do not propose answers and invite agreement. A domain pack is
   binding as a project requirement once recorded (Sec.5.4), so a section
   the engineer merely nodded at is worse than one left open — it reads
   afterwards as something the project asserted. Where they don't know
   yet, leave a `SUPPLY` ask rather than filling it.

5. **Draft the pack, show it in full, and have the engineer run
   `se-buddy write-domain draft.md`.** Gated like every other write. It
   refuses on a missing or empty Sec.5.4 section, and reports leftover
   placeholders in the confirmation prompt without refusing on them.

6. **Draft viewpoints and principles**, and have the engineer run
   `se-buddy write-memory viewpoints` / `write-memory principles`. The
   pack's Baseline viewpoints section is the source for these, but
   `viewpoints.yaml` is what `arch-viewpoint` reads — the pack is not.

7. **Generate the project's `CLAUDE.md`** with `se-buddy write-claude-md`
   (spec Sec.5.2). Thin and generated: it points at `se-buddy/` and states
   the rules that always hold, and holds no architectural content itself.
   Ungated, because it writes only inside a delimited block and leaves
   everything the engineer wrote outside it untouched — so re-run it after
   any profile change. Say which of the three things it did (created,
   updated in place, appended).

8. **Run `se-buddy doctor`** (or `se-buddy asks`) and report what is still
   open as `SUPPLY` asks. This is the completeness gate (Sec.5.3), and it
   now checks `domain.md`'s *content* against the six sections, not just
   that the file exists.

9. **MUST NOT** report the project as initialised while any Sec.5.3
   requirement remains open. Structural existence is not content
   completeness, and `check_completeness` checks both.

## Outputs

A complete profile, or an explicit list of what is still missing as
`SUPPLY` asks — always ending in that ask block (D8), never a bare "done."

## Commands used

`se-buddy write-profile`, `se-buddy write-domain`,
`se-buddy write-memory viewpoints`/`principles`, `se-buddy write-claude-md`,
`se-buddy doctor`, `se-buddy asks`. The three gated writes are drafted by
the agent and run by the engineer. Scaffolding the empty containers is not
a CLI verb (spec Sec.7.3 names none) and is backed by `se_buddy.scaffold`.

## Authority constraints

**Everything that asserts project content goes through a TTY gate, and the
agent runs none of it.** That is the whole rule, and it is now uniform:
`write-profile`, `write-domain` and `write-memory` are all gated (spec
Sec.2.3), all agent-drafted, all engineer-run. Scaffolding empty
containers stays ungated — it creates files with inert template content
and asserts nothing, the same carve-out Sec.7.3 gives `write propose`.

**Detection is retrieval, not authorship.** Reading `model_path` out of
the one `.capella` in the root, or `capella_version` out of that file's
own version marker, is the same class of act as `se-buddy search` — it
reports what the project already records. It is not covered by Sec.5's
"nothing project-specific belongs in agent-authored content", which is
about content the agent *originates*. The gate is still what commits it.

**Transcription is not invention.** Writing down what the engineer said
about their domain, showing it to them, and having them run the gated
write is exactly the `write-memory viewpoints` pattern, and a viewpoint is
no less a piece of engineering judgement than a domain pack. What remains
forbidden is supplying the judgement itself — see Failure handling.

## Failure handling

**If the engineer asks you to "just fill in" the domain pack from context
clues** — an existing README, the model's own contents, what the domain
generally believes — refuse, and say why: Sec.5.4 makes every line of
`domain.md` binding as a project requirement, so an inferred attack
surface becomes something the project is held to without anyone having
decided it. Interview instead. This is unchanged, and it is the rule the
whole gated-transcription route exists to protect: the constraint was
never on who types the file, only on who supplies the judgement.

**If detection is ambiguous** — two `.capella` files, no `.project`, no
version marker — report what was looked at and what was found, and ask.
Do not pick the alphabetically-first candidate, and do not write a partial
`profile.yaml`: three of four fields set reads as configured and fails
later, further from the cause. `write-profile` refuses a partial profile
for the same reason.

**If `write-domain` refuses**, it names the missing or empty section.
That is a drafting gap, not a tooling problem — return to step 4 for that
section rather than working around the check.

**If the engineer wants to hand-edit** `se-buddy/profile.yaml` or
`se-buddy/domain.md` directly, that works and nothing prevents it; they
are ordinary files. Say plainly that `doctor` is then the only thing
keeping the result honest, and re-run it.

## Interaction with other skills

`/se-buddy:doctor` runs before this on a fresh install — a profile cannot
be scaffolded by a plugin that never loaded. Every architecture-track
skill's C02 check depends on what this skill records;
`arch-viewpoint`/`arch-principles` read the results once populated.
