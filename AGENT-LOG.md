# Agent change history

Format and purpose: spec Sec.5.5. Newest first, append-only, never rewritten.

---

## AC-0002 — 2026-08-31 — Phase 1: model reading, inspect/search/show/trace/asks, project-init scaffolding, shared + architecture skills

```
surface   cli, skill, schema, template
breaking  no
action    none
why       the agent needs a real, trusted semantic understanding of a
          model before any write path is worth building on top of it
          (spec Sec.11's Phase 1 gate)
```

Adds `se-buddy inspect|search|show|trace|asks` (spec Sec.7.3), backed by
`src/se_buddy/model.py` (capellambse loading, resolved from `--model` or
`se-buddy/profile.yaml`); `src/se_buddy/schemas.py`/`memory.py` (the D8 ask
shape, `ADR/CP/CHANGE/ASK-nnnn` id allocation, `ID (claim)` citation
rendering); `src/se_buddy/profile.py`/`scaffold.py` and the
`project-init` skill (scaffolds `se-buddy/{profile.yaml,domain.md,
viewpoints.yaml,principles.yaml}` from `templates/`, without a TTY gate,
since scaffolding an inert skeleton asserts no engineering content — the
same carve-out spec Sec.7.3 gives `write propose`); and twelve `SKILL.md`
files (the four shared skills, all seven architecture-track skills
including `arch-perspective`'s five per-perspective references, and
`project-init`), each referencing `references/cross-cutting-behaviours.md`
(C01–C08) and `references/deliberation-discipline.md` (D1–D9) rather than
restating them.

**Rust toolchain gap from AC-0001: resolved.** A Rust GNU-target toolchain
was installed and verified to build capellambse from the vendored source
cleanly. `se-buddy doctor`, and every command added in this entry, was
verified against real capellambse and the real Capella 7.0 fixture shipped
in `vendor/py-capellambse/tests/data/models/test7_0` — not mocked.

**Known gap, not silently resolved:** spec Sec.6.3's cross-invocation parse
cache was not built. `capellambse.MelodyModel` does not survive `pickle`
(confirmed directly), and a parallel serializable index of model facts
would itself violate Sec.6.3's "every fact has exactly one representation."
`hash_model_files()` exists for Sec.10.2's future drift check; nothing
caches the parsed model itself. Cold parse on the one real fixture measured
is ~250–370ms for 1,484 elements — recorded as direct evidence for spike 6
(bin/ vs MCP, spec Sec.12), not routed around. See `SPEC-COVERAGE.md`.

**Design note:** `arch-decide` and `risk-manage` both describe a write step
(`write memory`/`write register`) that doesn't exist until Phase 2. Both
skills draft their full content and say so plainly rather than silently
stopping short or pretending the write happened — see `SPEC-COVERAGE.md`'s
Phase 1 section.

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
