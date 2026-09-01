# Agent change history

Format and purpose: spec Sec.5.5. Newest first, append-only, never rewritten.

---

## AC-0008 — 2026-09-01 — Project setup: detect the profile, interview the domain pack, generate CLAUDE.md

```
surface   cli (three new verbs), skill (project-init rewritten), schema
          (profile.yaml gains a generated header; content unchanged), test
breaking  no, with one behaviour change worth reading: `se-buddy doctor`
          and `se-buddy asks` now report SUPPLY gaps against a domain.md
          that is still template text. A project that was reporting
          "profile complete" over an unedited pack will start reporting
          asks - the asks are correct, and were always true
action    projects on the previous revision: re-run `se-buddy doctor`
          after updating; if new domain.md asks appear, the pack was
          never finished. `se-buddy write-claude-md` is new and worth
          running once
why       AC-0007 fixed getting the plugin loaded. This fixes what a
          project has to do next, which was the other half of the same
          complaint: hand-writing a profile and a six-section domain pack
          in a text editor, with nothing checking the result
```

**`profile.yaml` did not need a human at all.** Its four fields are facts
already written in the project's own files - the one `.capella` in the
root, its `.aird`, the `Capella_Version` marker inside the model, the
`<name>` in Eclipse's `.project`. `se_buddy.profile_detect` reads them and
returns each with the file it came from; `se-buddy write-profile` shows
both and writes only after a typed confirmation.

The provenance is the part that matters. The old objection to this was
spec Sec.5's "nothing project-specific belongs in agent-authored content",
which is about content the agent *originates* - reading a version marker
out of a file the engineer committed is the same class of act as
`se-buddy search`. Showing where each value came from is what keeps it
that way: the engineer checks a value against its source instead of
trusting it, and the TTY gate is still what commits it.

**`domain.md` needed a human, but not a text editor.** Sec.5.4 makes every
line of the pack binding as a project requirement, so the agent must not
invent it - that part was right and is unchanged. What was wrong was the
conclusion drawn from it: `skills/project-init/SKILL.md` forbade the agent
from writing the file at all, and handed over a six-section template.

That put `domain.md` in a category of one. `write-memory viewpoints` is
also engineering judgement, and it is agent-drafted and TTY-gated: the
agent writes down what the engineer said, the engineer runs the write.
`domain.md` was the only piece of judgement that was *ungated and
forbidden*, so it fell through to Notepad - an asymmetry that cost the
entire authoring experience and bought no safety the gate did not already
provide. `se-buddy write-domain` closes it; `project-init` now interviews
the six sections and drafts the pack.

Worth being precise, since this is the rule being changed: the constraint
was never on who types the file, only on who supplies the judgement. The
interview is what enforces the part that matters, and the skill's Failure
handling still refuses to infer a pack from a README or from the model.

**Nothing checked the result, which is how the first install ended up with
a real pack under the heading "# Domain pack: <replace with your domain's
name>", with the template's own instructions to the reader still above
it - and `doctor` calling that complete.** `check_completeness` asked only
whether the file existed. `se_buddy.domain_pack` now checks Sec.5.4's six
sections, with the two kinds of finding deliberately kept apart:

  - structural (a section missing or empty) is a fact about the document,
    and `write-domain` refuses on it;
  - a leftover `<placeholder>` or the template's preamble is a heuristic,
    so it is reported - as `SUPPLY` asks, and in the write gate where a
    human reads it before confirming - and never given a veto. Sec.5.3
    says completeness reports and does not block, and a regex is not
    entitled to be the exception.

**`CLAUDE.md` (Sec.5.2) was specified and never built.** `se-buddy
write-claude-md` generates it: thin, pointing at `se-buddy/`, stating the
rules that always hold, carrying no architectural content. Not gated, and
the reasoning is the same one that governs `write propose` and
`se_buddy.scaffold` - authority follows what a write can assert and what
it can lose. This one asserts nothing the engineer must judge, and it
writes only between two markers, so there is no overwrite case to guard:
no file creates one, an existing block is replaced in place, an existing
file without one is appended to. Idempotent.

**Two detection bugs, both found by tests rather than by inspection, both
of which would have written a wrong value into a real profile.** The
`Capella_Version` character class swallowed the `-->` closing its own
comment (`7.0.1--`), caught against the real model. The `.afm` fallback
matched the first `version="..."` in the file, which is always the XML
declaration's `version="1.0"`. Both are anchored now, and the `.afm` path
prefers the Capella core viewpoint where a project references several.

**The write guards never ran on macOS or modern Linux, and the check that
was supposed to notice could not have.** `hooks.json` invoked both guards
as bare `python`. That binary does not exist on macOS 12.3+ or current
Debian/Ubuntu - only `python3` does - and Claude Code treats a hook whose
interpreter is missing as a *non-blocking* error, so the tool call
proceeds. On those platforms the second of the two write-protection layers
this project advertises simply was not there, and nothing said so:
`hooks.json` was present, valid JSON, and pointed at scripts that existed,
which is all `doctor` was checking. `bin/se-buddy` and `bin/_bootstrap.py`
have always tried `python3` before `python`; the hook config was the one
place that did not.

Both commands now prefer `python3` with a `python` fallback, in POSIX `sh`
(which covers `sh` and Git Bash), using `exec` so the guard's exit 2
reaches Claude Code as the block rather than the shell's own status.

The fix that matters more is `install.check_hooks`: `doctor` now resolves
the interpreter the config names and *runs* a guard against a payload it
must refuse, asserting exit 2. This is the same lesson as AC-0007's, in a
second place - the old check tested a proxy (does the config parse?) that
was true in exactly the case where the thing itself was broken. Its
remaining limit is stated in the function rather than left implied: it
does not reproduce Claude Code's shell selection, so a Windows install
with no Git Bash, where the commands fall through to PowerShell and would
not parse, passes this check. That case is in the README.

**Two asks for one unfinished file - AC-0008's own domain check, caught by
running it against the real project.** `ask_store.sync_profile_gaps` keys
an open ask on `object` alone, and computed its `open_objects` set once
before the loop. The new `domain.md` content check emitted one gap per
finding, every one of them carrying the object `se-buddy/domain.md`, so
model-iot_platform grew `ASK-0009` and `ASK-0010` for a single file.
Neither could be updated or resolved independently afterwards, since every
later run matched only the first - and the placeholder *count* had been
frozen into `done_when` at whatever it was the first time, an ask being
written once and never rewritten.

Fixed in three places, because the invariant deserved to be defended
rather than merely obeyed: `check_completeness` emits one gap per object,
whose `done_when` states the invariant requirement; the run-to-run
specifics move to a new `ProfileGap.detail` that `sync_profile_gaps` does
not persist and `doctor` prints; and `sync_profile_gaps` grows
`open_objects` inside its loop so a future caller that emits duplicate
objects gets one ask rather than silently reproducing this.

**Adding an ungated verb broke the write-guard hook, which is worth
recording as the cost of that carve-out rather than as a footnote.**
`block_write_verbs.py` matched `write-(\w+)`, and `\w` stops at a hyphen,
so it read `write-claude-md` as the verb `write-claude` - absent from its
exemption set, so the second defence layer blocked a verb the agent is
supposed to run, under a name that does not exist. The pattern now takes
hyphenated verb names and the exemption set is explicit and annotated
(`propose`, `claude-md`), tied to the one property that puts a verb in it:
the CLI itself does not gate it. An unknown `write-x-y` still fails
closed. Caught here rather than in a real session only because the hook's
own tests were extended alongside the verb.

258 tests pass (was 193). One existing test changed rather than broke:
`test_profile`'s complete-profile case wrote `# Domain\n` as its domain
pack, which is no longer one - it now uses a `tests.complete_domain_pack()`
fixture built from `REQUIRED_SECTIONS`, so adding a required section keeps
it passing for the right reason instead of going stale.

---

## AC-0007 — 2026-09-01 — Install path: make "installed" verifiable, and drop the Rust prerequisite

```
surface   cli (doctor output), skill (new: doctor), bootstrap, test
breaking  no
action    none - `se-buddy doctor`'s output changed shape (three sections)
          but no verb, flag or schema did. Projects already installed pick
          this up on the next `git submodule update --remote`
why       the first install into a project that isn't this repo (Phase 4)
          failed in a way nothing in the agent could see or report, and
          failed again on a prerequisite that turned out to be avoidable
```

Two defects, both in the install path rather than in anything the spec
governs, both found by actually doing the Phase 4 install instead of
reasoning about it.

**`doctor` answered a different question than the one being asked, and
said "installation is sound" while doing it.** On the real install it
reported interpreter, venv, pin and profile all `[ok]`, exit 0 — while
Claude Code had loaded none of the eighteen skills. Every line was true.
None of them touched the layer the engineer had installed the thing for.

The cause is that a project-scope skills-directory plugin loads only from
the session's *primary* working directory and does not walk up to the
repository root the way plain skills do, and only once the workspace-trust
prompt is accepted. Neither condition was documented, and neither was
checked. `src/se_buddy/install.py` now checks what is checkable from a
subprocess — manifest, layout, working directory, `hooks/hooks.json`
presence — and `doctor` prints it as an `install` section ahead of
`runtime` and `profile`.

What it deliberately does **not** do is claim the plugin loaded. Nothing a
subprocess can read establishes that. `doctor` reports it positively only
where the plugin's `bin/` is on `PATH` (which happens only when Claude
Code has it enabled), reports an explicit unknown otherwise — never a
failure, since a human running the launcher from a terminal is the normal
case — and its closing line now says "the deterministic layer is sound"
rather than "installation is sound" when that is all it established.

The other half is `/se-buddy:doctor` (new skill). It is proof by
construction rather than a check: a slash command cannot resolve unless
the plugin carrying it loaded, so a skill that runs *is* the evidence.
That is the last step of Install.

Worth recording as a safety consequence, not only a usability one: the
`PreToolUse` write guards are one of the two independent write-protection
layers (spec Sec.10.1), and they exist only while the plugin is loaded. An
install that silently never loaded had the TTY gate and nothing else, and
nothing said so.

**Rust was a prerequisite because of a choice here, not because of
capellambse.** `bin/_bootstrap.py` installed capellambse by building
`vendor/py-capellambse` from source unconditionally, which needs `rustc`
and `cargo`. capellambse 0.8.1 publishes eight `cp311-abi3` wheels —
macOS arm64/x86-64, manylinux and musllinux aarch64/x86-64, win32/amd64 —
so on every platform this realistically targets, nothing needed compiling.
For a systems engineer rather than a developer, installing a Rust
toolchain is where the install tended to stop.

The bootstrap now installs the pinned version from a wheel
(`--only-binary :all:`) and falls back to the vendored source only where
no wheel matches. That fallback is the only path that still demands Rust,
and its message now names the reason it was reached. Wheel-attempt
failures are diagnosed separately from lockfile-install failures, because
"could not find a version that satisfies" means *offline* in one context
and *no wheel for this platform* in the other, and conflating them sends
the engineer after the wrong problem.

The trade, recorded because it is real: the submodule pinned an exact
commit and a version pin does not. `==` still fixes the version and
`doctor` still refuses on drift from it (Sec.7.1), but the artefact now
comes from an index rather than a SHA this repository records.
Hash-pinning the wheel in `lockfile` would recover that; it is not done.

**Verified live, not by inspection.** The venv was deleted and rebuilt
from scratch with `rustc`/`cargo` removed from `PATH`: it installed the
wheel and reached `capellambse 0.8.1 matches the pin` in 49 seconds. The
no-wheel fallback was exercised separately against a version that has none
and produced the Rust message with the correct reason, not the offline
one. 193 tests pass (was 179); the 14 new ones cover the install checks,
including that a missing `bin/` on `PATH` is reported as unknown rather
than as a failure.

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
