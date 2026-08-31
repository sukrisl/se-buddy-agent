# Agent change history

Format and purpose: spec Sec.5.5. Newest first, append-only, never rewritten.

---

## AC-0006 — 2026-08-31 — Pre-production hardening: full code review, 15 findings fixed

```
surface   code (no CLI/schema surface change), hook, test
breaking  no
action    none
why       before pointing this agent at a real Capella project, a full
          review (not just the diff) of every phase's implementation was
          asked for explicitly, to find what could still break against
          real engineering data before it did
```

A `code-review --level high` pass (10 finder angles + verification) across
the entire implementation confirmed 15 findings; all 15 were fixed, each
with a regression test, plus two more real gaps found while writing those
tests. Full detail, file by file: SPEC-COVERAGE.md's "Phase 3 hardening
pass" section.

The two most consequential: `--delete` was checked for diagram references
only when passed, never enforced as *required* when a proposal actually
deleted something, so an omitted flag let a deletion through unchecked;
and `check_tree_clean()` silently reported a genuinely dirty tree as clean
whenever the model lived in a subdirectory, because the git path arguments
doubled the `cwd` prefix already applied. Both confirmed live, pre-fix,
before being corrected. Also fixed: two swallowed-exception gaps in the
apply lifecycle, an unvalidated baseline name (path traversal), a
crash-not-a-refusal in `write revert` (the single most common revert
scenario - right after an apply, tree still dirty by design), a dropped-
row bug in `write memory`'s save path, a missing `show PRIN-nnnn`/
`ASSUME-nnnn` dispatch branch, an edge-dropping bug in `trace`'s reverse
closure, an uncaught `EOFError` in the TTY gate, a write-order bug in
`file_change()` that could silently lose an owed `DRAW` followup on a
crash, a `write-*` hook regex too narrow to catch its own module-
invocation form, and two `schemas.py` presence-check bugs (`diagram_cost:
0` read as missing; a dead no-op branch in `validate_change`). Beyond the
15: no automated test existed for `write_revert.py` at all (now does), and
every YAML writer in this codebase used a non-atomic `write_text`, risking
a truncated/corrupted record file on a crash mid-write - a new
`atomic_write_text()` (temp file + `os.replace()`) now backs all eight of
them.

**Verified by regression test, not just by inspection.** Every fix has a
test that demonstrably exercises the original failure mode (several
confirmed failing against the pre-fix code before the fix landed, not
assumed). 179 tests total, full suite green.

---

## AC-0005 — 2026-08-31 — Phase 3: controlled modification

```
surface   cli, schema, hook, skill
breaking  no
action    none
why       the agent can now propose, dry-run, apply, validate, record and
          revert real changes to the model, with a snapshot/restore
          safety net and the write path's second defence layer (hooks) -
          this is the phase spec Sec.11 calls "a real change applies and
          reverts cleanly"
```

Adds `write-propose` (automatic authority, spec Sec.7.3's explicit
carve-out - the only write verb with no TTY gate); `plan` (a dry run,
safe by construction - `capellambse.decl.apply()` confirmed directly to
never touch the filesystem itself); `write-apply`
(`src/se_buddy/apply_lifecycle.py`, the full spec Sec.10.2 sequence:
check tree, check drift, preflight-validate targets, snapshot, apply,
save, re-parse, six-layer validate, diff, record - restores the snapshot
on any failure); `write-record` (manual Capella work, no snapshot since
nothing was ever under se-buddy's control to snapshot); `write-revert`
(restores a `CHANGE`'s snapshot, refuses cleanly if none exists);
`validate` (`src/se_buddy/validate.py`, five real automated layers plus
`architectural`, which reports `UNKNOWN` and names the recorded
viewpoints rather than fabricating a verdict on free-text design rules no
deterministic check can read); `write-answer`'s `DRAW` case (now ticks a
real `CHANGE-nnnn.followup.yaml` entry, completing what Phase 2 stubbed as
a refusal); `followup` (renders checklists as Markdown); `show`'s
extension to resolve `ADR`/`CP`/`CHANGE`/`ASK`/register-row ids, not only
model uuids (a real staleness bug found and fixed, not spec-mandated on
its own); and both write-guard hooks
(`hooks/hooks.json`, `hooks/block_capella_write.py`,
`hooks/block_write_verbs.py` - Python, not shell, for the same Windows-
portability reason `bin/se-buddy.cmd` exists).

**Verified live and thoroughly, not just unit-tested.** The single most
consequential run: proposed a real change against the real `test7_0`
fixture, applied it for real (the `.capella` file on disk changed, a
fresh model reload confirmed the new element persisted), then reverted it
and confirmed the file was restored **byte-identical** to before. Every
write verb this codebase has ever shipped - Phase 2's and this phase's -
was invoked directly from this session's own non-interactive shell and
refused every time, which is precisely spec Sec.13 Question 8's
prescribed attack. `validate`'s `interface` layer produces genuine,
non-contrived findings on the real fixture (confirmed by direct
introspection before writing the check, not arranged after). The two
hooks' own logic was tested directly against the exact JSON shape Claude
Code sends; live firing inside a real, enabled plugin session was not
verified, and is stated as such rather than assumed.

**One dependency deferred by explicit decision:** `model-export`/
`se-buddy export` needs `capellambse-context-diagrams`, confirmed not
present anywhere in this repo. Left unbuilt, with `model-export`'s
`SKILL.md` saying so plainly. `se-buddy perspective` remains the other
open phasing-table gap, carried over from Phase 2, still unblocking
nothing. See `SPEC-COVERAGE.md`.

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
