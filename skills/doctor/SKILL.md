---
name: doctor
description: Confirm the install is complete - run se-buddy doctor and report what the CLI alone cannot establish, namely that the plugin loaded at all.
---

# doctor

## Purpose

Answer "am I set up?" completely, which `se-buddy doctor` on its own cannot
do. The CLI can check the interpreter, the venv, the pin, the layout on
disk and profile completeness. It cannot check whether Claude Code loaded
this plugin, because nothing a subprocess can read says so.

This skill closes that gap by construction rather than by checking: a
slash command cannot resolve unless the plugin carrying it loaded, so if
this skill is running at all, `se-buddy@skills-dir` is enabled. That fact
is this skill's actual output, and it is the one an engineer finishing an
install is trying to get.

## When to invoke

The last step of Install, before `project-init`. Again whenever a
`/se-buddy:*` command stops resolving, a write guard does not appear to
fire, or `se-buddy` stops working as a bare command.

## Inputs

None.

## Context required

None. Deliberately: this skill has to work in a project whose profile does
not exist yet, which is exactly the state it is most often run in.

## Procedure

1. Run `se-buddy doctor` as a bare command. If it is not found, fall back
   to `.claude/skills/se-buddy/bin/se-buddy doctor`
   (`.claude\skills\se-buddy\bin\se-buddy.cmd doctor` on Windows) and say
   which of the two worked - the bare form resolving means the plugin's
   `bin/` reached PATH, and the fallback being needed is itself a finding
   worth reporting, not a detail to smooth over.
2. Report the three sections it prints (`install`, `runtime`, `profile`)
   as they stand. Do not re-summarise a `[FAIL]` line as a warning, and do
   not describe a `[ ]` line as passing.
3. State plainly that the plugin is loaded, and why that is now known:
   this skill ran. Where `doctor`'s own plugin-load line says it could not
   confirm this from the CLI, say that the two are consistent - the CLI
   could not see it, this skill is the evidence - rather than reporting
   them as a contradiction.
4. If `doctor` exited non-zero, the failing checks are the answer. Give
   them, and the remedy each one names, and stop - do not proceed to
   `project-init` on a failed install.
5. If `doctor` exited zero, name the next step: `/se-buddy:project-init`
   if `se-buddy/` does not exist yet, otherwise whichever track the
   engineer came for.

## Outputs

The three sections, unedited in substance; an explicit statement that the
plugin is loaded; and either the failing checks with their remedies, or
the next step. Ends in an ask block (D8) where anything is still open.

## Commands used

`se-buddy doctor`. Nothing else - this skill must work before a profile
exists, so it cannot depend on any verb that reads one.

## Authority constraints

Read-only. `doctor` repairs the venv (spec Sec.5.1) and that is the only
thing this skill causes to be written; it asserts nothing about the
project and touches no record. No TTY gate applies.

## Failure handling

If neither the bare command nor the explicit path runs, do not diagnose
from the model or from the project's contents - report the launcher error
verbatim and point at the README's Troubleshooting table, which maps that
error to its cause. A launcher that cannot start is a Python or checkout
problem (spec Sec.5.1), never an architecture one, and guessing past it
would produce a confident answer about the wrong layer.

If `doctor` reports the working directory is not the project root, say
that no skill loaded *from this project* and that the ones the engineer
can see come from somewhere else - a personal-scope install, or another
project. Do not treat this skill running as proof the project's own copy
is fine; it is not.

## Interaction with other skills

Runs before `project-init` on a new install, and before anything else when
an install is in doubt. Every other skill assumes what this one verifies.
