# Agent change history

Format and purpose: spec Sec.5.5. Newest first, append-only, never rewritten.

---

## AC-0004 — 2026-08-31 — Phase 2, second pass: write memory

```
surface   cli, schema
breaking  no
action    none
why       write_answer's DECIDE/SUPPLY refusal (AC-0003) pointed engineers
          at a command that didn't exist, and arch-decide/project-init's
          ADR-filing and viewpoint/principle completion had nowhere to
          land - closed on the user's explicit decision rather than left
          for Phase 3, since it was already a real, shipped bug
```

Adds `se-buddy write-memory <domain> d.yaml` for `principles`,
`viewpoints`, `glossary`, `assumptions`, `decisions` (`src/se_buddy/
commands/write_memory.py`, `memory_domains.py`, `decisions.py`), the
matching read verb `se-buddy memory <domain>`, and the ADR-specific schema
(`question`/`context`/`alternatives`/`chosen_option`/`rationale`/
`consequences`/`evidence`/`authority`, with `authority` enforced per spec
Sec.9). `knowledge` is deliberately not a `write memory` domain - every
`knowledge.yaml` row needs the `ASK-nnnn` it answers (spec Sec.9), which
only `write answer` supplies.

TTY-gated, same pattern as every other write verb. Verified live: wrote a
real viewpoint and a real ADR (bypassing the gate directly, per spec
Sec.2.3's testing philosophy - never `run()`), read both back through
`se-buddy memory`, and confirmed `doctor`'s open-ask count dropped and the
viewpoints `SUPPLY` ask auto-resolved on the next `se-buddy asks` run.
`arch-decide`, `project-init` and `arch-principles`'s `SKILL.md` files
were updated to drop their "pending" language now that the write step
they each end in is real.

One phasing-table gap remains open, left unbuilt on the user's explicit
decision: `se-buddy perspective [<layer>]` (Sec.7.2/Sec.7.3). Nothing
currently depends on it. See `SPEC-COVERAGE.md`.

---

## AC-0003 — 2026-08-31 — Phase 2: registers, write register/answer/baseline, the TTY gate

```
surface   cli, schema
breaking  no
action    none
why       registers give the agent somewhere to put facts the model can't
          hold (risks, verification, what wasn't carried across a
          perspective transition), and the TTY gate is the precondition
          for any of that - or anything else - to be written safely
          (spec Sec.11's Phase 2 gate, spec Sec.2.3)
```

Adds `src/se_buddy/gate.py` (the TTY confirmation gate, spec Sec.2.3 - no
bypass parameter, by design); `src/se_buddy/registers.py`/`schemas.py`
(register schemas and load/save for the six registers under `se-buddy/
registers/`); `se-buddy register`/`write-register` (spec Sec.6.2's "the
only route" into a register); `se-buddy/knowledge.py` and `write-answer`
(dispatches `CONFIRM`/`REVIEW`/`PRIORITISE`/`DRAW`/`DECIDE`/`SUPPLY`/
`AUTHORISE` per spec Sec.7.3's table); `se-buddy/baseline.py` and
`write-baseline` (manifest + local git tag, spec Sec.6.4); `trace`
extended across model and registers; and `se_buddy/ask_store.py`, which
gives a detected gap a stable `ASK-nnnn` id across sessions so `write
answer`/auto-resolution have something real to close (see
`SPEC-COVERAGE.md`'s design note - this fills a gap the spec's own CLI
surface doesn't explicitly name a mechanism for).

**Verified live, not just unit-tested:** every write verb, invoked
directly from this session's own shell, refused with the TTY gate's clear
message - the actual attack spec Sec.13 Question 8 names. `trace` across
model and registers was run against a real risk row linking a real
model uuid from the `test7_0` fixture, in both directions. `asks` was run
twice against a fresh project to confirm id stability, then a gap was
fixed and confirmed to auto-resolve on the next run. The baseline git-tag
step was run once, for real, in a throwaway repository (never this one,
never pushed).

**Two gaps found in the spec's own phasing table, not resolved
unilaterally:** `write memory` and `se-buddy perspective` are absent from
every phase's content list in Sec.11. Consequence: `arch-decide`'s
ADR-filing (flagged pending since Phase 1) is still pending;
`risk-manage`'s track/close is not (this phase gave it `write register`
for real, and its `SKILL.md` was updated to say so). See
`SPEC-COVERAGE.md` for the reasoning.

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
