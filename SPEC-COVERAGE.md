# Spec coverage

Written alongside the implementation, from the first commit, per spec Sec.13.
For each requirement: where it lives, whether it is **enforced** (code
refuses the wrong behaviour) or **instructed** (only asked for), and — if
instructed — whether it could be enforced and why it is not yet.

This file grows one phase at a time (spec Sec.11). It now covers Phase 0
(the `bin/` launcher, the vendored venv, `doctor`'s venv/version checks)
and Phase 1 (capellambse loading, `inspect`/`search`/`show`/`trace`/`asks`,
`project-init`'s scaffolding, id allocation, and the shared + architecture
skills). Requirements that need registers, records or the write path are
out of scope until Phase 2/3 — listed at the bottom as not-yet-applicable,
not as failing.

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

**Design note — two skills describe a write step that doesn't exist yet.**
`arch-decide` (files an ADR) and `risk-manage` (tracks/closes a register
row) are both explicitly in Phase 1's scope (spec Sec.11), but their final
step needs `write memory`/`write register`, which are TTY-gated and arrive
in Phase 2. Both `SKILL.md` files describe the complete procedure (that's
what makes them correct long-term) and say plainly, in their own
"Authority constraints" section, that recording is pending — the agent
drafts the full content and presents it in conversation, and never claims
something was filed when it wasn't. `project-init` follows the identical
pattern for `viewpoints.yaml`/`principles.yaml` content.

## Not yet applicable (later phases)

Sec.13's review questions 1–3, 6–10, 12–16 need registers, records, the
write path, or a second installed project — Phase 2/3/4. Question 11
("does `doctor` refuse on a version or interpreter mismatch") was answered
in Phase 0.
