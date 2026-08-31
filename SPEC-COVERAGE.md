# Spec coverage

Written alongside the implementation, from the first commit, per spec Sec.13.
For each requirement: where it lives, whether it is **enforced** (code
refuses the wrong behaviour) or **instructed** (only asked for), and — if
instructed — whether it could be enforced and why it is not yet.

This file grows one phase at a time (spec Sec.11). It now covers Phase 0
(bootstrap), Phase 1 (the read path), and Phase 2 (registers, `write
register`, `write answer`, `write baseline`, and the TTY gate). Requirements
that need the modelling write path or a second installed project are out
of scope until Phase 3/4 — listed at the bottom as not-yet-applicable, not
as failing.

## Phase 0 requirements

| # | Requirement | Spec | Where | Status |
| - | --- | --- | --- | --- |
| 1 | `bin/se-buddy` is a launcher, not the program: checks the venv, bootstraps/repairs it, then execs the real entry point | Sec.5.1 | [bin/se-buddy](bin/se-buddy), [bin/_bootstrap.py](bin/_bootstrap.py) | **Enforced** — every invocation runs `ensure_venv()` before exec; there is no code path that skips it |
| 2 | Windows gets its own entry point, since a shebang script does not execute there | Sec.5.1 | [bin/se-buddy.cmd](bin/se-buddy.cmd) | **Enforced** by having the file; both launchers were run end-to-end (POSIX via bash, Windows via `cmd.exe`) against the same fixture with identical outcomes |
| 3 | Venv is created at `vendor/.venv`, capellambse installed **from the vendored submodule**, transitive deps from the pinned lockfile | Sec.5.1 | [bin/_bootstrap.py](bin/_bootstrap.py) `build_venv()` | **Enforced** — `pip install --no-deps <vendor/py-capellambse>` then `pip install -r lockfile`, in that order, never from an index |
| 4 | The venv is build output: never committed | Sec.5.1 | [.gitignore](.gitignore) | **Instructed** — `.gitignore` stops an accidental `git add .`, but `git add -f` would still work. Not enforced further; a pre-commit hook could reject a staged `vendor/.venv/` path, but nothing in Phase 0 needs it yet |
| 5 | `se-buddy doctor` reports venv presence/completeness and interpreter version, and **repairs** a broken venv rather than only reporting it | Sec.5.1, Sec.5.3 | [bin/_bootstrap.py](bin/_bootstrap.py) `ensure_venv()`, run unconditionally by both launchers before `doctor`'s own code runs | **Enforced**. Verified directly: deleting `vendor/.venv` and re-running `doctor` rebuilds it and reports success, on both launchers |
| 6 | Python floor (3.11, set by the pin) — refuse below it, naming both versions | Sec.5.1 | [bin/_bootstrap.py](bin/_bootstrap.py) `check_interpreter_floor()`; re-reported by [src/se_buddy/doctor.py](src/se_buddy/doctor.py) | **Enforced** at the earliest possible point (before any venv work), and reported again once inside the venv |
| 7 | Offline clone fails with one clear message naming the lockfile and venv path — never a stack trace from an import | Sec.5.1 | [bin/_bootstrap.py](bin/_bootstrap.py) `_diagnose_pip_failure()`, `build_venv()` | **Enforced** for the failure modes that were actually reachable and tested: missing/empty vendored submodule, missing lockfile, pip failing to reach the index. All three were run and produce a one-line message, never a traceback |
| 8 | `capellambse==0.8.1` in `pyproject.toml` and the `vendor/py-capellambse` submodule pin **MUST agree** | Sec.7.1 | [pyproject.toml](pyproject.toml), submodule pin, [src/se_buddy/_pin.py](src/se_buddy/_pin.py) | **Enforced by construction, not by a check**: `pyproject.toml` is the *only* place the version string is written; the bootstrap and `doctor` both read it from there via `_pin.read_pin()` instead of carrying a second copy. There is no separate assertion that the submodule commit matches, because there is nothing left for it to drift against in-repo — the risk that remains is a human bumping one without the other in the same commit, which Sec.7.1's process (both move together, authorised, recorded in AGENT-LOG.md) covers as instructed discipline, not tooling |
| 9 | `doctor` compares the *running* `capellambse.__version__` against the pin and **refuses** on mismatch, naming both versions — this is the check that matters | Sec.7.1 | [src/se_buddy/doctor.py](src/se_buddy/doctor.py) `run()` | **Enforced.** Verified directly: hand-editing the installed package's version inside the venv (simulating drift from outside se-buddy) makes `doctor` exit non-zero and name both versions, without silently reinstalling over it |
| 10 | `SPEC-COVERAGE.md` written from the first commit | Sec.13 | this file | Structural — satisfied by existing |
| 11 | Any surface change adds one `AGENT-LOG.md` entry in the same commit | Sec.5.5 | [AGENT-LOG.md](AGENT-LOG.md) `AC-0001` | **Instructed** — nothing currently checks that a commit touching `bin/`, `src/se_buddy/`, `pyproject.toml` or the submodule pin also touches `AGENT-LOG.md`. Could be enforced with a pre-commit hook; not built in Phase 0 |

## Gap surfaced in Phase 0, resolved during Phase 1

**Rust toolchain.** capellambse 0.8.1 links a Rust extension
(`vendor/py-capellambse/Cargo.toml`, via `pyo3`). Sec.5.1 requires installing
it *from the vendored source* rather than from an index, but says nothing
about a Rust toolchain being a prerequisite for that build. Phase 0 flagged
this rather than routing around it (a fake stand-in package stood in for
the mechanics-only test).

**Resolved**: a Rust GNU-target toolchain (`Rustlang.Rust.GNU`, via
`winget` — chosen over the MSVC path specifically to avoid also needing a
multi-GB Visual Studio Build Tools install) was installed and verified to
build capellambse from the vendored source cleanly, with no separate
system-wide MinGW install needed (Rust's official windows-gnu distribution
bundles a self-contained linker). `se-buddy doctor` now passes for real,
not mocked. This is still worth documenting in the README's prerequisites
(spike 5, Sec.12) as a real, non-obvious install step for anyone building
this repo fresh on Windows.

## Phase 1 requirements

| # | Requirement | Spec | Where | Status |
| - | --- | --- | --- | --- |
| 12 | capellambse loading, resolved from `--model` or `se-buddy/profile.yaml`, never a raw traceback for a missing/misconfigured model | Sec.6.3, Sec.5.1 | [src/se_buddy/model.py](src/se_buddy/model.py) `load_model`/`resolve_model_path` | **Enforced.** Verified against the real `vendor/py-capellambse/tests/data/models/test7_0` fixture through both launchers |
| 13 | The model is parsed once per session, cached keyed on file hash | Sec.6.3 | — | **Not built, on evidence, not by default.** `MelodyModel` does not survive `pickle` (confirmed: `TypeError: cannot pickle 'lxml.etree._Element' object`), and a parallel serializable index would itself violate Sec.6.3's "every fact has exactly one representation." Cold parse on the one real fixture measured (1,484 elements, ~2.4 MB `.aird`) is ~250–370ms. `hash_model_files()` is still built (needed by Sec.10.2's future drift check) but nothing caches the parsed object across process invocations. This is direct evidence for spike 6 (bin/ vs MCP, Sec.12), not routed around |
| 14 | `inspect`/`search`/`show`/`trace`/`asks`, each bounding output and reporting truncation | Sec.7.3, Sec.6.3, D6 | [src/se_buddy/commands/](src/se_buddy/commands/) | **Enforced** — `--limit`/`--depth` on every command that can return an unbounded set; truncation always stated in the output. Verified against the real fixture: real per-layer counts, a real UUID resolving through `show`, a real 2-hop reverse-reference closure through `trace` (a Logical→Physical→Configuration-item realization chain) |
| 15 | Behavioural elements (functional chains, scenarios, state machines) are retrievable, citable and traceable, with no completeness/well-formedness check run on them | Sec.2.2 | `show`/`trace`'s generic relationship introspection | **Enforced by construction** — `show`/`trace` treat every element generically (no per-class special-casing), so a `FunctionalChain`/`Scenario`/`StateMachine` is handled exactly like a structural element, and no validation layer runs on it because none exists yet at all (Phase 3) |
| 16 | `project-init` scaffolds `profile.yaml`/`domain.md`/`viewpoints.yaml`/`principles.yaml`, refuses to overwrite, and `doctor` reports what's still missing as `SUPPLY` asks | Sec.5.3 | [skills/project-init/SKILL.md](skills/project-init/SKILL.md), [src/se_buddy/scaffold.py](src/se_buddy/scaffold.py), [src/se_buddy/profile.py](src/se_buddy/profile.py) | **Partially enforced, deliberately.** Scaffolding and the completeness check are both real and tested end-to-end (scaffold → `doctor` → correct `SUPPLY` ask count). Filling the skeletons with real content is `write memory`, TTY-gated, Phase 2 — see the design note below |
| 17 | `ASK-nnnn` id allocation, `ID (claim)` citation rendering (D3), the D8 ask shape with `act`/`done_when` enforced | Sec.9, Sec.3 | [src/se_buddy/memory.py](src/se_buddy/memory.py), [src/se_buddy/schemas.py](src/se_buddy/schemas.py) | **Enforced**, unit-tested directly. Nothing calls `allocate_id` from a live write command yet since none exist — built now so Phase 2/3 writers have one place to allocate from, not their own copy |
| 18 | Shared + architecture-track skills (`frame-request`, `retrieve-context`, `trace-rationale`, `write-plain`, `arch-perspective` + one reference per Arcadia perspective, `arch-viewpoint`, `arch-transition`, `arch-review`, `arch-decide`, `arch-principles`, `risk-manage`), referencing C01–C08/D1–D9 rather than restating them | Sec.8.1, Sec.8.2 | [skills/](skills/), [references/cross-cutting-behaviours.md](references/cross-cutting-behaviours.md), [references/deliberation-discipline.md](references/deliberation-discipline.md) | **Instructed** (skill prose, not code) — Sec.8.2's ten-section structure followed in each; each cites C-codes/D-codes rather than restating them. Not mechanically checkable without a linter over the markdown; none written for this phase |
| 19 | `.claude-plugin/plugin.json` names the plugin so skills auto-discover and namespace as `/se-buddy:<name>` | Sec.5.1 | [.claude-plugin/plugin.json](.claude-plugin/plugin.json) | Structural. Not yet exercised end-to-end as a real submodule install (that proof is Phase 4's explicit job, spec Sec.11) |

**Design note, updated in Phase 2 — one of two pending write steps is now
real.** Phase 1 flagged that `arch-decide` (files an ADR) and `risk-manage`
(tracks/closes a register row) both describe a write step that didn't
exist yet. `risk-manage`'s is now real: `write register` exists, and its
`SKILL.md` was updated in Phase 2 to say so (its "Authority constraints"
section no longer says "pending" — it says the agent drafts the row and
the engineer runs the write themselves, per the TTY gate). `arch-decide`'s
ADR-filing still isn't real — see the Phase 2 gaps below.

## Phase 2 requirements

| # | Requirement | Spec | Where | Status |
| - | --- | --- | --- | --- |
| 20 | **The TTY gate**: every write verb refuses unless run at a genuine interactive terminal, no bypass parameter of any kind | Sec.2.3 | [src/se_buddy/gate.py](src/se_buddy/gate.py) | **Enforced.** Verified live: `write-register`, `write-answer` and `write-baseline`, invoked directly by me through both the POSIX and (transitively, same code path) Windows launcher, all refused with the same clear message — my own shell has no interactive stdin/stdout, so this is the real refusal path, not a simulated one. The positive path (a human confirming) cannot be verified by me and is not claimed as verified — spec Sec.2.3 accepts exactly this limitation ("cannot run non-interactively — not in CI, and not in the agent's own test suite"). The second defence layer (`PreToolUse` hook on `Bash`, Sec.10.1) is Phase 3; this phase ships the CLI-side half only |
| 21 | Register schemas (base fields + per-register extras), one file per register, add/update-by-id | Sec.6.2, Sec.9 | [src/se_buddy/schemas.py](src/se_buddy/schemas.py), [src/se_buddy/registers.py](src/se_buddy/registers.py) | **Enforced** for `id`/`claim`/`status` on every register and `reason`/`decided_by` on `not-carried` (spec Sec.9's explicit wording); other fields are warned-not-rejected, matching Sec.9's own enforced/instructed split. Per-register extra fields beyond `not-carried`'s spelled-out shape are a documented completion (see the note below), not literal spec text |
| 22 | `se-buddy write register <name> row.yaml` — the only route into a register | Sec.6.2, Sec.7.3 | [src/se_buddy/commands/write_register.py](src/se_buddy/commands/write_register.py) | **Enforced.** TTY-gated (item 20); the write logic (`registers.upsert_row`) is called directly by unit tests, never through the gate, per Sec.2.3 |
| 23 | `se-buddy write answer ASK-nnnn a.yaml` dispatches by act: `CONFIRM`/`REVIEW` → `knowledge.yaml`; `PRIORITISE` → `sequence:` on named asks; `DRAW` → refuses (no followup checklist can exist before Phase 3); `DECIDE`/`SUPPLY` → refuse, name `write memory`/`write register` | Sec.7.3 | [src/se_buddy/commands/write_answer.py](src/se_buddy/commands/write_answer.py) `answer_ask()` | **Enforced**, all six branches unit-tested directly (CONFIRM, REVIEW, PRIORITISE, DRAW-refused, DECIDE-refused, SUPPLY-refused), plus `AUTHORISE`-refused — not in Sec.7.3's literal dispatch table, added because it follows directly from D8's own act definition and Sec.7.3 gives no other verb `write answer` could plausibly hand it to |
| 24 | `se-buddy trace <id>` extended across model **and** registers | Sec.11 | [src/se_buddy/commands/trace.py](src/se_buddy/commands/trace.py) | **Enforced.** Verified live end-to-end against the real fixture: a real risk row linking a real model uuid shows up under `trace <uuid>` ("cited by 1 register row(s)"), and `trace <row-id>` resolves the row and its links in the other direction |
| 25 | `se-buddy write baseline <name>`: model hash + register row statuses + open ask ids + date, and a git tag at the same commit | Sec.6.4 | [src/se_buddy/baseline.py](src/se_buddy/baseline.py), [src/se_buddy/commands/write_baseline.py](src/se_buddy/commands/write_baseline.py) | **Enforced.** TTY-gated; manifest content unit-tested directly, and the git-tag step verified live in a throwaway repo (never the agent repo itself, and never pushed anywhere) |
| 26 | An ask raised in one session is closed (or auto-resolved) in another | Sec.11's Phase 2 gate | [src/se_buddy/ask_store.py](src/se_buddy/ask_store.py) | **Enforced, via a documented addition** — see the design note below. Verified live: ran `se-buddy asks` twice against a fresh scaffolded project, confirmed the four `SUPPLY` ids were identical across both runs, then fixed one gap (`domain.md`) and confirmed its ask auto-resolved on the next run while keeping its original id and a historical `answered: auto-resolved` record |

**Design note — asks needed a persistence mechanism the spec's CLI surface
doesn't explicitly name.** Sec.11's Phase 2 gate ("an ask raised in one
session is closed in another") needs a *stable* id across sessions, but
Phase 1 deliberately didn't allocate real ids for profile gaps (nothing
existed to persist them to), and neither `write memory` nor `write
propose` — the two things Sec.3 D8 says normally "raise an ask inside a
record" — are listed under Phase 2 *or* Phase 3 in Sec.11's table. Rather
than block this phase's own gate on that absence, `se-buddy asks`/`doctor`
now allocate and persist a stable id the first time a gap is seen (a new
`se-buddy/asks.yaml`, MEMORY-layer, append-only), auto-resolving it once
the condition clears. This is not TTY-gated, on the same reasoning `write
propose` gets its own carve-out (Sec.7.3): recording an observable gap
asserts no engineering content the agent invented. `write answer` closes
these for real when their act permits it (`CONFIRM`/`REVIEW`/`PRIORITISE`);
`SUPPLY`-acted profile gaps are correctly *refused* by `write answer` per
Sec.7.3's own table and can only be resolved by the condition actually
being fixed — which is exactly what the auto-resolve path demonstrates.

**Register field shapes beyond Sec.9's literal text.** Sec.9 spells out
`not-carried.yaml`'s fields exactly but doesn't enumerate the others.
`likelihood`/`impact`/`treatment` (both risk registers), `method`/
`requirement_id` (verification), `statement` (requirements) and
`stakeholder` (stakeholder-expectations) were added as the minimum needed
to make `risk-manage`'s cycle and the other registers actually usable —
documented here as a completion, not spec text, per Sec.13's own review
discipline.

## Two gaps found in the phasing table itself (Sec.11)

Neither of these is resolved unilaterally — both are flagged for whoever
owns the spec to assign to a phase:

1. **`write memory`** (writes `principles.yaml`/`viewpoints.yaml`/
   `glossary.yaml`/`assumptions.yaml`/`knowledge.yaml`/`decisions/`, per
   Sec.7.3's CLI table) does not appear in Phase 2's *or* Phase 3's content
   list in Sec.11, even though Sec.7.3 groups it with `write register`/
   `write answer`/`write baseline` under the identical TTY-gated umbrella,
   and Phase 3's explicit content is unambiguously about the *model*
   write path (`write propose`/`plan`/`write apply`/`write record`/`write
   revert`), which `write memory` has nothing to do with. Consequence:
   `arch-decide`'s ADR-filing and `project-init`'s viewpoint/principle
   completion both remain pending past Phase 2, not because either skill
   is incomplete, but because the verb they both end in has no assigned
   phase at all.
2. **`se-buddy perspective [<layer>]`** (Sec.7.2/Sec.7.3's dedicated
   per-perspective completeness command) is likewise absent from every
   phase's content list. Not built in Phase 2 — `arch-perspective`'s skill
   already works via `inspect`/`search`/`show`/`trace` without it, so
   nothing is blocked, but the command itself remains unbuilt.

## Not yet applicable (later phases)

Sec.13's review questions 1–3, 6, 9, 10, 12–16 need the modelling write
path, hooks, or a second installed project — Phase 3/4. Question 7 ("is
there a second representation of the registers or the model anywhere?")
is answered now: no — `se_buddy.registers` is the only reader/writer of
register files, and `trace`'s register-citation logic reads through it
rather than re-deriving register content. Question 11 was answered in
Phase 0.

**Question 8 ("can the agent apply a change without a human keystroke?")
is only fully answerable once `write apply` exists (Phase 3), but its
underlying mechanism was tested now, on every write verb that currently
exists.** The question's own prescribed attack — "allowlist the CLI... and
invoke [it] from Bash" — is exactly what happened live in this phase:
`write-register`, `write-answer` and `write-baseline` were all invoked
directly from this Bash tool, and all three refused. That doesn't close
the question (it reopens the moment `write apply` exists and needs the
same check run against it specifically, plus Phase 3's second defence
layer), but it's real, positive evidence that the gate mechanism itself
holds under the exact attack Sec.13 names, not a promise deferred to later.
