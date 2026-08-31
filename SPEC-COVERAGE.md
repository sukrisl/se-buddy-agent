# Spec coverage

Written alongside the implementation, from the first commit, per spec Sec.13.
For each requirement: where it lives, whether it is **enforced** (code
refuses the wrong behaviour) or **instructed** (only asked for), and — if
instructed — whether it could be enforced and why it is not yet.

This file grows one phase at a time (spec Sec.11). What follows is Phase 0
only: the `bin/` launcher, the vendored venv, and `se-buddy doctor`'s venv
and version checks. Requirements that need a profile, a model, registers,
skills or hooks are out of scope until the phase that introduces them —
they are listed at the bottom as not-yet-applicable, not as failing.

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

## Known gap surfaced during implementation

**Rust toolchain.** capellambse 0.8.1 links a Rust extension
(`vendor/py-capellambse/Cargo.toml`, via `pyo3`). Sec.5.1 requires installing
it *from the vendored source* rather than from an index — "installing from
`vendor/py-capellambse` rather than from an index is what keeps the
submodule commit load-bearing instead of decorative" — but says nothing
about a Rust toolchain being a prerequisite for that build, and the
development machine used to build and test this phase does not have one.

This was not resolved silently. The bootstrap implements Sec.5.1 as written
(build from the vendored source), preflights for `rustc`/`cargo`, and
refuses with a clear, actionable message when they are absent — verified
directly. The full success path (a real capellambse building from source)
could not be exercised on this machine; the venv-creation, local-path
install, lockfile install, `PYTHONPATH` wiring, exec, and `doctor` reporting
mechanics were instead verified end-to-end against a fake stand-in package
matching capellambse's name, version and install shape, with the Rust
preflight temporarily disabled in a throwaway copy — never in the files
described here.

This affects spike 1 and spike 5 of Sec.12 (both assume the round-trip and
the submodule install work "end to end" without naming a toolchain
prerequisite) and belongs on the list the engineer decides, not something
this implementation should paper over.

## Not yet applicable (later phases)

Everything else in spec Sec.13's sixteen review questions needs a profile,
a model, registers, records, skills or hooks that Phase 0 does not build:
questions 1–3, 6–10, 12–16 apply once Phase 1 (profile, `project-init`,
skills) and Phase 3 (write path, hooks) exist. Question 11 ("does `doctor`
refuse on a version or interpreter mismatch") is answered above — yes.
