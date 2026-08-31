# Agent change history

Format and purpose: spec Sec.5.5. Newest first, append-only, never rewritten.

---

## AC-0001 — 2026-08-31 — Phase 0 bootstrap: launcher, venv, and doctor's venv/version checks

```
surface   cli, dependency
breaking  no - first release
action    none
why       a working `se-buddy` entry point is the precondition for every later
          phase; safety and reasoning machinery are only worth building once
          something can actually run (spec Sec.11)
```

Adds `bin/se-buddy` and `bin/se-buddy.cmd` (spec Sec.5.1), which bootstrap or
repair `vendor/.venv` on every invocation and then exec into it; the
`vendor/py-capellambse` submodule pinned at `v0.8.1`; `pyproject.toml`
declaring `capellambse==0.8.1` as the single source of the pin; `lockfile`
pinning every transitive dependency; and `se-buddy doctor`, scoped for this
phase to the venv-presence/completeness check (repaired automatically) and
the capellambse-version-vs-pin check (refused, never silently reinstalled —
spec Sec.7.1).

**Known gap, not silently resolved:** capellambse 0.8.1 builds a Rust
extension (`vendor/py-capellambse/Cargo.toml`, via pyo3). Installing it from
the vendored source therefore needs a Rust toolchain (`rustc`, `cargo`) on
the machine running the bootstrap — spec Sec.5.1 does not mention this
prerequisite. The bootstrap detects a missing toolchain and refuses with a
clear message rather than a build-tool stack trace, but does not install
Rust itself. See the README's Prerequisites section and the note in
`SPEC-COVERAGE.md`.
