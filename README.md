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

- **Bootstraps itself, locally.** The launcher (`bin/se-buddy`, or
  `bin\se-buddy.cmd` on Windows) builds and repairs its own virtualenv,
  inside the submodule, on every invocation — no separate install step,
  and nothing touches your shell's `PATH` or anything outside the project.
  It installs capellambse from a prebuilt wheel where one matches the
  platform, so no compiler is needed; the vendored source build (which does
  need Rust) is the fallback, not the default.
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
  loop gets there at all. **The hook layer exists only while the plugin is
  loaded** — an install that never loaded has the TTY gate and nothing else,
  which is one more reason `/se-buddy:doctor` is step 5 of Install.
- **Went through a full pre-production hardening pass.** Every phase's
  implementation (not just the latest diff) was reviewed for defects before
  this was pointed at a real project; 15 confirmed findings were fixed, plus
  two more found while writing their regression tests (see AGENT-LOG.md's
  `AC-0006`). 193 tests pass.

**Deliberately not built yet**, each a scoped decision recorded in
SPEC-COVERAGE.md rather than an oversight:

- `se-buddy perspective [<layer>]` — the dedicated per-perspective
  completeness command. `arch-perspective`'s skill already works without it
  via `inspect`/`search`/`show`/`trace`.
- `se-buddy export`/`model-export` — needs `capellambse-context-diagrams`,
  not currently vendored. The skill describes the procedure without a
  working command.
- **Phase 4: a second project installing this fresh** has now been tried
  once, against a real Capella model, and it found the install path's two
  worst problems: nothing anywhere could tell you whether the plugin had
  actually loaded (`doctor` reported "installation is sound" while every
  skill was unreachable), and the Rust prerequisite was self-inflicted.
  Both are fixed — see the CHANGELOG. What that install has *not* yet
  exercised is the modelling track end to end against a real model, so
  treat those results as still open.
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
installed and exposes each as `/se-buddy:<name>`. There are nineteen:

| Skill | What it's for |
| --- | --- |
| `doctor` | Confirm the install is complete — including the one thing the CLI can't check, that the plugin loaded |
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

One thing needs to already be on your machine:

1. **Python 3.11 or later**, on `PATH` as `python3` or `python`.

That's it on the common platforms. capellambse ships prebuilt wheels for
macOS (Apple silicon and Intel), Linux (glibc and musl, x86-64 and arm64)
and Windows, and the launcher installs one of those — nothing is compiled.

**A Rust toolchain is needed only where no wheel matches your platform.**
There, the launcher falls back to building capellambse from the vendored
source, and that needs `rustc` + `cargo`. It will say so plainly if it ever
happens, naming the reason:

- macOS/Linux: install from <https://rustup.rs>.
- Windows: `winget install Rustlang.Rust.GNU` — this avoids also needing
  Visual Studio Build Tools.

If Python is missing or too old, `doctor` (step 5 below) tells you plainly
rather than failing with a stack trace — so if you're not sure, let it
check for you.

You'll also need network access, but only once: the first `se-buddy`
command in a fresh clone downloads the pinned dependencies, and every run
after that works offline.

## Install

Five steps, in this order. Steps 3 and 4 are the ones that are easy to
skip and the ones that decide whether anything works — the submodule being
on disk is not the same as the plugin being loaded.

**1. Add the submodule** at the path Claude Code auto-loads from:

```bash
git submodule add https://github.com/sukrisl/se-buddy-agent.git .claude/skills/se-buddy
```

**2. Check out the nested submodule:**

```bash
git submodule update --init --recursive
```

**3. Start Claude Code at the project root** — the directory holding
`.claude/`, not a subdirectory of it:

```bash
claude
```

A project-scope plugin loads only from the session's *primary* working
directory and does **not** walk up to the repository root the way plain
skills do. Starting in a subdirectory, or opening the project as an
*additional* working directory, silently loads nothing.

**4. Accept the workspace-trust prompt.** Project plugins come from the
repository rather than from you, so they load only behind the same trust
gate that governs project permissions. Trusting a parent folder, or
running with `-p`, is not enough. Declining leaves every step below
looking installed and doing nothing.

**5. Verify, from inside Claude Code:**

```
/se-buddy:doctor
```

This is the check that actually answers "am I set up?". **If that command
does not exist, the plugin did not load** — go to Troubleshooting below;
nothing further will work until it does. If it runs, it reports the
install, runtime and profile sections and names your next step.

Once the plugin is loaded, its `bin/` is on the `PATH` Claude Code's Bash
tool uses, so `se-buddy` works as a bare command:

```bash
se-buddy doctor
```

From an ordinary terminal outside Claude Code, use the explicit local path
instead — nothing is ever added to your own shell's `PATH`:

```bash
.claude/skills/se-buddy/bin/se-buddy doctor
```

(`.claude\skills\se-buddy\bin\se-buddy.cmd doctor` on Windows.) `doctor`
bootstraps the venv and, once a profile exists, reports profile
completeness, model drift, and record-schema problems.

**6. Scaffold the profile:** `/se-buddy:project-init`.

### Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| No `/se-buddy:*` commands exist | Plugin never loaded | Work down this table |
| …and you started Claude Code in a subdirectory | Project plugins don't walk up to the repo root | Restart at the root, or `/cd` there |
| …and the project is an *additional* working directory | Only the primary one is scanned | Make it the primary directory |
| …and you declined workspace trust | Project plugins load only once trusted | Restart and accept; trusting a parent folder isn't enough |
| …and you edited `hooks/`, `.mcp.json` or `agents/` | Those aren't hot-reloaded | `/reload-plugins` |
| …and none of the above | Manifest or layout | `se-buddy doctor` — its `install:` section names the cause |
| `se-buddy: command not found` inside Claude Code | Plugin not loaded (its `bin/` never reached `PATH`) | As above; meanwhile use the explicit path |
| Launcher asks for a Rust toolchain | No prebuilt wheel matched your platform | Install Rust per Prerequisites — the message names the reason |
| `doctor` says "installation is sound" but no skills work | You ran the CLI, which cannot see the reasoning layer | That wording is gone; upgrade, then use `/se-buddy:doctor` |

`se-buddy doctor` deliberately does **not** claim the install is complete
on its own. It can check the interpreter, venv, pin, on-disk layout and
profile, but nothing a subprocess can read tells it whether Claude Code
loaded the plugin — so it says which of the two it verified. `/se-buddy:doctor`
covers both, and proves the load by construction: a slash command cannot
resolve unless the plugin carrying it loaded.

## How to use it

Work through Claude Code: it discovers the skills in [`skills/`](skills/)
automatically once the plugin is enabled. Run `/se-buddy:doctor` first to
confirm it is, then `/se-buddy:project-init`
to scaffold a profile, then work through the architecture track
(`arch-viewpoint`, `arch-review`, `arch-decide`, …) or the modelling track
(`model-impact`, `model-plan`, `model-apply`, …) as skills — each one
drafts, and hands off to you for anything that writes.

Every skill's "Commands used" section names the `se-buddy` verbs it calls
underneath, and you can run any of them yourself too. Inside Claude Code,
with the plugin loaded, `se-buddy` is a bare command — the plugin's `bin/`
is on the Bash tool's `PATH`. From your own terminal, prefix the local
path; nothing is ever exported to your shell's `PATH`. `--model <path>`
overrides `se-buddy/profile.yaml`'s model path where one is needed.

```bash
se-buddy doctor                      # is the install and the profile sound?
se-buddy inspect                     # counts: elements, diagrams, open asks
se-buddy search "retry"              # find elements by name/summary
se-buddy show <uuid-or-record-id>    # one element or record, in full
se-buddy trace <uuid-or-record-id>   # what it traces to/from, what breaks

se-buddy write-propose cp.yaml       # file a proposal (no gate: asserts nothing yet)
se-buddy plan CP-0001                # dry run: what would change, on disk untouched
se-buddy write-apply CP-0001 \
  --authorized-by "engineer said go" # TTY-gated: applies, validates, records, snapshots
se-buddy validate                    # six layers of findings against the current model
se-buddy write-revert CHANGE-0001    # restore a change from its snapshot, byte-identical
```

Outside Claude Code, the same commands with the path spelled out:

```bash
.claude/skills/se-buddy/bin/se-buddy doctor
```

Read verbs (`doctor`, `inspect`, `search`, `show`, `trace`, `asks`,
`register`, `baseline`, `memory`, `plan`, `validate`, `followup`) run
anywhere, including non-interactively. Every `write-*` verb except
`write-propose` refuses outside a real interactive terminal — this is
deliberate (see Status above), so scripting one will always fail with a
clear message, not silently succeed.

| Command | What it does |
| --- | --- |
| `doctor` | Install layout, runtime and profile, in three sections. Repairs the venv; reports the rest. Cannot see whether the plugin loaded — use `/se-buddy:doctor` for that |
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

193 tests, no network required once the venv is built.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).
