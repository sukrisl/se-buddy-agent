# SE Buddy

SE Buddy is a reusable systems-engineering collaborator for Model-Based Systems Engineering (MBSE) in Eclipse Capella. It uses the Arcadia method. One installation serves a project in any engineering domain.

It helps an engineer to examine an architecture that changes, to think about a change against the design intent of that architecture, to keep decisions and the reasons for them, and to keep traceability. It changes the model only with authorisation.

Three parties do the work. Claude Code is the reasoning layer. The `se-buddy` command-line interface is the deterministic layer: it reads, queries, validates and records, and it does not reason. The engineer makes every architecture decision and gives every authorisation.

> [!warning] Note
> SE Buddy is not an autonomous systems engineer. It advises, and the engineer decides.

## Status

**v0.1.0 — Phases 0–3 of 4 complete.** See [CHANGELOG.md](CHANGELOG.md) for
what shipped when, [log/log-0001-se_buddy_agent_spec.md](log/log-0001-se_buddy_agent_spec.md)
Sec.11 for the phase plan, and [SPEC-COVERAGE.md](SPEC-COVERAGE.md) for a
line-by-line account of every spec requirement and how it's enforced.

What works today, concretely:

- **Bootstraps itself.** `bin/se-buddy` (or `bin\se-buddy.cmd` on Windows)
  builds and repairs its own virtualenv on every invocation, no separate
  install step.
- **Reads a real Capella model.** `inspect`/`search`/`show`/`trace` work
  against the model, its diagrams, and every project record (ADRs,
  proposals, changes, asks, register rows) — bounded output, truncation
  always stated.
- **Keeps project memory.** Registers (risks, requirements, stakeholder
  expectations, verification, not-carried, in Sec.6.2's six kinds),
  principles, viewpoints, glossary, assumptions and ADRs are all readable
  and, through the TTY-gated `write-*` verbs, writable.
- **Proposes, previews, and applies real model changes**, end to end:
  `write-propose` files a proposal as an executable `capellambse.decl`
  document; `plan` dry-runs it with nothing written to disk; `write-apply`
  runs the full check-tree → check-drift → snapshot → apply → re-validate →
  record sequence, and restores the pre-apply snapshot on *any* failure;
  `write-revert` restores a change from its snapshot; `validate` runs six
  layers of findings (five real, one honest `UNKNOWN` where no deterministic
  check can judge a free-text design rule).
- **Refuses to run unattended, on two independent layers.** Every write verb
  except `write-propose` refuses unless it's run by a human at a real
  interactive terminal (the TTY gate, `src/se_buddy/gate.py`) — no bypass
  flag exists anywhere, by design. A second, independent layer
  (`hooks/hooks.json`'s `PreToolUse` hooks) blocks the same write verbs, and
  direct edits to `.capella`/`.aird`, before Claude Code's own tool-dispatch
  loop gets there at all.
- **Went through a full pre-production hardening pass.** Every phase's
  implementation (not just the latest diff) was reviewed for defects before
  this was pointed at a real project; 15 confirmed findings were fixed, plus
  two more found while writing their regression tests (see AGENT-LOG.md's
  `AC-0006`). 179 tests pass.

**Deliberately not built yet**, each a scoped decision recorded in
SPEC-COVERAGE.md rather than an oversight:

- `se-buddy perspective [<layer>]` — the dedicated per-perspective
  completeness command. `arch-perspective`'s skill already works without it
  via `inspect`/`search`/`show`/`trace`.
- `se-buddy export`/`model-export` — needs `capellambse-context-diagrams`,
  not currently vendored. The skill describes the procedure without a
  working command.
- **Phase 4: a second project installing this fresh**, as a submodule in a
  project that isn't this repo, has not been tried. Everything above has
  only ever been exercised inside this repo, against the fixture model
  vendored with capellambse. This is the one open question before treating
  a real Capella project's results as fully representative of how the
  plugin behaves once installed.
- Two things can, by construction, only be verified by a human actually
  doing them, not by the agent that built this: a human typing the TTY
  gate's confirmation at a real terminal, and the `PreToolUse` hooks firing
  live inside a real, enabled Claude Code plugin session. Both are expected
  to work — the logic behind each is unit-tested directly — but neither has
  been watched happen for real yet.

## How Claude Code finds this: skills, not CLAUDE.md

This repository *is* the Claude Code plugin (`.claude-plugin/plugin.json`
names it `se-buddy`). There is no `CLAUDE.md` here, and that's intentional,
not an oversight — this repo has nothing to point a `CLAUDE.md` *at*: it's
the tool itself, not a project using the tool.

The entry point for an agent working with this codebase is
[`skills/`](skills/): one directory per skill, each a self-contained
`SKILL.md` (purpose, when to invoke, inputs, procedure, commands used,
authority constraints, failure handling — the ten-section shape spec
Sec.8.2 asks for). Claude Code auto-discovers them once the plugin is
installed and exposes each as `/se-buddy:<name>`. There are eighteen:

| Skill | What it's for |
| --- | --- |
| `project-init` | Scaffold a new project's `se-buddy/` profile and gate on its completeness |
| `frame-request`, `retrieve-context`, `trace-rationale`, `write-plain` | Shared behaviours every other skill builds on (D1–D9, C01–C08) |
| `arch-perspective`, `arch-viewpoint`, `arch-transition`, `arch-review`, `arch-decide`, `arch-principles` | The architecture track — reasoning about the model against recorded viewpoints and principles, filing ADRs |
| `risk-manage` | Track and close risk-register rows |
| `model-impact`, `model-plan`, `model-apply`, `model-validate`, `model-record`, `model-export` | The modelling track — propose, dry-run, apply, validate and record real model changes (`model-export` documents the procedure only; see Status) |

Every skill cites [`references/cross-cutting-behaviours.md`](references/cross-cutting-behaviours.md)
(C01–C08) and [`references/deliberation-discipline.md`](references/deliberation-discipline.md)
(D1–D9) rather than restating them — read those two files first if you want
the rules every skill assumes.

Skills are the *reasoning* layer's entry point; `se-buddy` (via `bin/`) is
the *deterministic* layer's — a skill's own "Commands used" section always
names exactly which `se-buddy` verbs it calls, so you can trace any skill
down to the code that actually runs.

**One real gap worth knowing about:** spec Sec.5.2 says a project that
installs `se-buddy` as a submodule should get a thin, generated `CLAUDE.md`
of its own — living in *that* project, not this one — pointing at its
`se-buddy/profile.yaml`. `project-init` does not generate this yet; it only
scaffolds the four `se-buddy/` profile files. Not currently tracked as a
phase gap in SPEC-COVERAGE.md — worth raising if you want it built before
a real install.

## Prerequisites

- Python 3.11+ on `PATH` as `python3` or `python`.
- Network, the first time `bin/se-buddy` (or `bin\se-buddy.cmd`) runs in a clone, to install the pinned dependencies.
- `git submodule update --init --recursive`, so `vendor/py-capellambse` is checked out — never `--remote` together with `--recursive` (spec Sec.7.1).
- **A Rust toolchain (`rustc`, `cargo`).** capellambse 0.8.1 builds a Rust extension, and the bootstrap installs it from the vendored source rather than a prebuilt index wheel (spec Sec.5.1), so building it locally needs one. On Windows, the GNU-target toolchain (`winget install Rustlang.Rust.GNU`, or <https://rustup.rs> with the `x86_64-pc-windows-gnu` target) avoids also needing Visual Studio Build Tools — verified working on this repo. `se-buddy doctor` refuses with a clear message if no toolchain is found.

## Install

```bash
git clone --recursive <this-repo-url>
cd se-buddy-agent
bin/se-buddy doctor
```

On Windows, use `bin\se-buddy.cmd doctor` instead. `doctor` is always the
right first command: it builds/repairs the venv, checks the interpreter
floor and the installed capellambse version against the pin, and — once a
project profile exists — reports profile completeness, model drift, and
outstanding record-schema problems.

## How to use it

**As a Claude Code plugin (the intended path).** Add this repo as a
submodule of your Capella project and let Claude Code discover the skills
in [`skills/`](skills/) (see the section above). In conversation, ask for
`/se-buddy:project-init` to scaffold a profile, then work through the
architecture track (`arch-viewpoint`, `arch-review`, `arch-decide`, …) or
the modelling track (`model-impact`, `model-plan`, `model-apply`, …) as
skills — each one drafts, and hands off to you for anything that writes.

**As a CLI directly**, for development or for exercising a command by hand.
Every command is `bin/se-buddy <verb> [args]` (`bin\se-buddy.cmd` on
Windows) from inside the project directory; `--model <path>` overrides
`se-buddy/profile.yaml`'s model path where one is needed.

A typical first real session, once a profile exists:

```bash
bin/se-buddy doctor                      # is the install and the profile sound?
bin/se-buddy inspect                     # counts: elements, diagrams, open asks
bin/se-buddy search "retry"              # find elements by name/summary
bin/se-buddy show <uuid-or-record-id>    # one element or record, in full
bin/se-buddy trace <uuid-or-record-id>   # what it traces to/from, what breaks

bin/se-buddy write-propose cp.yaml       # file a proposal (no gate: asserts nothing yet)
bin/se-buddy plan CP-0001                # dry run: what would change, on disk untouched
bin/se-buddy write-apply CP-0001 \
  --authorized-by "engineer said go"     # TTY-gated: applies, validates, records, snapshots
bin/se-buddy validate                    # six layers of findings against the current model
bin/se-buddy write-revert CHANGE-0001    # restore a change from its snapshot, byte-identical
```

Read verbs (`doctor`, `inspect`, `search`, `show`, `trace`, `asks`,
`register`, `baseline`, `memory`, `plan`, `validate`, `followup`) run
anywhere, including non-interactively. Every `write-*` verb except
`write-propose` refuses outside a real interactive terminal — this is
deliberate (see Status above), so scripting one will always fail with a
clear message, not silently succeed.

| Command | What it does |
| --- | --- |
| `doctor` | Is this installation and profile sound? Repairs the venv; reports the rest |
| `inspect` | Model + diagrams + memory overview, in counts |
| `search <text>` | Elements by name/summary |
| `show <id>` | One element or record, relationships, diagrams, citations |
| `trace <id>` | What it traces to, what traces to it, what breaks |
| `asks` | Every open ask, in D8 shape |
| `register <name>` | Read one register (Sec.6.2) |
| `baseline <name>` | Read a recorded baseline (Sec.6.4) |
| `memory <domain>` | Read principles/viewpoints/glossary/assumptions/knowledge/decisions |
| `plan CP-nnnn` | Dry run: what would change, what must be drawn by hand |
| `validate` | Six layers of findings, with evidence |
| `followup` | Manual diagram work still owed, rendered as Markdown |
| `write-register <name> row.yaml` | The only route into a register (gated) |
| `write-answer ASK-nnnn a.yaml` | Close one ask (gated) |
| `write-baseline <name> [--force]` | Write a manifest and a git tag (gated) |
| `write-memory <domain> d.yaml` | File a principle/viewpoint/glossary/assumption/ADR (gated) |
| `write-propose cp.yaml` | File a CP (automatic authority, no gate) |
| `write-apply CP-nnnn --authorized-by "…"` | Apply an authorised proposal (gated) |
| `write-record change.yaml` | Record manual Capella work (gated) |
| `write-revert CHANGE-nnnn` | Revert a change from its snapshot (gated) |

## Testing

```bash
PYTHONPATH=src vendor/.venv/Scripts/python.exe -m unittest discover -s tests
```

179 tests, no network required once the venv is built.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).
