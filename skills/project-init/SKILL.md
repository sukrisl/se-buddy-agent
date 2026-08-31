---
name: project-init
description: Scaffold a new project's profile (profile.yaml, domain.md, viewpoints.yaml, principles.yaml) and gate on its completeness.
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
3. Tell the engineer plainly these are skeletons with placeholders, not a
   completed profile, and that two different things happen next: they
   hand-edit `profile.yaml`'s four fields and `domain.md`'s six sections
   themselves (spec Sec.5.4) and commit the result - no verb writes
   either of those - while a real viewpoint or principle goes through
   `write memory viewpoints`/`write memory principles` once drafted.
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

`se-buddy doctor`, `se-buddy asks`, `se-buddy write memory viewpoints`/
`write memory principles` (drafted by the agent, run by the engineer).
Scaffolding itself is not a CLI verb (spec Sec.7.3 does not name one for
it) - it is invoked as part of this skill's own procedure, backed by
`se_buddy.scaffold`.

## Authority constraints

**Scaffolding is not `write memory`, and is not TTY-gated** - it creates
container files with inert template content, never engineering judgement
the agent asserts as true, the same carve-out spec Sec.7.3 gives
`write propose` ("a proposal asserts what *could* be done, not what is
true"). It refuses to overwrite an existing profile by default, so it
cannot silently clobber the engineer's own edits.

**Two different paths for filling the skeletons in, and they don't mix.**
A real viewpoint or a real principle is `write memory viewpoints`/
`write memory principles` (spec Sec.7.3) - TTY-gated, same as every other
write verb: the agent drafts the content, the engineer runs the write
themselves. `profile.yaml`'s four fields (`model_path`, `aird_path`,
`capella_version`, `project_name`) and `domain.md`'s six sections are
**not** a `write memory` domain at all - spec Sec.7.3's domain list is
`principles, viewpoints, glossary, assumptions, knowledge, decisions`,
and neither `profile.yaml` nor `domain.md` is on it. Those two are always
hand-edited by the engineer directly, in their own editor, and committed
themselves - this skill's job for them is only to scaffold the skeleton
and report what's still missing, never to write their content through any
verb.

## Failure handling

If the engineer asks project-init to "just fill in" the profile from
context clues (an existing README, a model file's own metadata), refuse -
that is inventing project-specific content the agent has no authority to
assert (spec Sec.5: nothing project-specific belongs in agent-authored
content). For `profile.yaml`/`domain.md`, say plainly that these are
hand-edited, not agent-written, regardless of what's said in conversation.
For `viewpoints.yaml`/`principles.yaml`, draft the content and tell the
engineer to run `write memory` themselves - never write it on their
behalf even if they've clearly stated what they want.

## Interaction with other skills

Every architecture-track skill's C02 check depends on what this skill
scaffolds eventually being filled in. `arch-viewpoint`/`arch-principles`
read the results once populated.
