---
name: project-init
description: Scaffold a new project's profile (profile.yaml, domain.md, viewpoints.yaml, principles.yaml) and gate on its completeness. Scaffolds only - filling in content still needs the write path (see Authority constraints).
---

# project-init

## Purpose

Get a new project from "just installed the submodule" to a profile
`se-buddy doctor` can actually check (spec Sec.5.3): `profile.yaml`,
`domain.md`, `viewpoints.yaml`, `principles.yaml`.

## When to invoke

A fresh project with no `se-buddy/` directory yet, or an existing one
missing one of the four required files.

## Inputs

A domain pack choice (`se-buddy scaffold --list-domains` names what's
shipped in `templates/domains/`, e.g. `generic`, `aerospace-arp4754a`), and
the model paths for `profile.yaml`.

## Context required

`templates/profile.yaml`, `templates/viewpoints.yaml`,
`templates/principles.yaml`, and the chosen `templates/domains/<name>.md`.

## Procedure

1. Ask which domain pack fits, or confirm `generic` if none of the shipped
   examples match - never guess a domain silently.
2. Scaffold the four files (`se_buddy.scaffold.scaffold_profile`): copies
   inert template text into `se-buddy/profile.yaml`, `domain.md`,
   `viewpoints.yaml`, `principles.yaml`. Refuses to overwrite an existing
   file unless the engineer explicitly asks to replace it.
3. Tell the engineer plainly: these are skeletons with placeholders, not a
   completed profile. `profile.yaml`'s four fields (`model_path`,
   `aird_path`, `capella_version`, `project_name`), a real viewpoint with
   `design_rules` and a `priority`, and the domain pack's six sections
   (spec Sec.5.4) all still need real content, supplied and committed by
   the engineer.
4. Run `se-buddy doctor` (or `se-buddy asks`) to show what's still open as
   `SUPPLY` asks - this is the actual completeness gate (spec Sec.5.3),
   and it stays open until the engineer has filled the skeletons in.
5. **MUST NOT** report the project as initialised while any of the four
   Sec.5.3 requirements remain open (structural existence is not the same
   as content completeness - `check_completeness` checks both).

## Outputs

The four scaffolded files, plus the `SUPPLY` asks naming what's still
needed - always ending in that ask block (D8), never a bare "done."

## Commands used

`se-buddy doctor`, `se-buddy asks`. Scaffolding itself is not yet a CLI
verb (spec Sec.7.3 does not name one for it) - it is invoked as part of
this skill's own procedure, backed by `se_buddy.scaffold`.

## Authority constraints

**Scaffolding is not `write memory`, and is not TTY-gated** - it creates
container files with inert template content, never engineering judgement
the agent asserts as true, the same carve-out spec Sec.7.3 gives
`write propose` ("a proposal asserts what *could* be done, not what is
true"). It refuses to overwrite an existing profile by default, so it
cannot silently clobber the engineer's own edits.

**Filling the skeletons with real content is a different, gated action.**
A real viewpoint, a real principle, a real project name are all
`write memory` (spec Sec.7.3), which is TTY-gated and does not exist until
Phase 2. Until then, this skill scaffolds and reports gaps; it does not,
and must not, write real profile content on the engineer's behalf even if
they state it in conversation - present what they said back to them and
say plainly that recording it needs a step this installed phase doesn't
have yet.

## Failure handling

If the engineer asks project-init to "just fill in" the profile from
context clues (an existing README, a model file's own metadata), refuse -
that is inventing project-specific content the agent has no authority to
assert (spec Sec.5: nothing project-specific belongs in agent-authored
content), and it is exactly the kind of write the TTY gate exists to
prevent from happening quietly.

## Interaction with other skills

Every architecture-track skill's C02 check depends on what this skill
scaffolds eventually being filled in. `arch-viewpoint`/`arch-principles`
read the results once populated.
