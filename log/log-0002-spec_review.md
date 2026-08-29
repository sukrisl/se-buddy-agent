# SE Buddy — Review of log-0001 before implementation

**Reviewing:** `log/log-0001-se_buddy_agent_spec.md` at e099c89
**Asked for:** coverage, consistency, conflicts, redundancy
**Written in the spec's own idiom:** every citation carries its claim (D3), each finding fits one screen (D4), asks are collected at the end in D8 shape.

---

## 0. Verdict

The spec is unusually well-formed. Three things in it are load-bearing and correct, and I checked them rather than assuming:

- **§5.1 distribution is accurate.** A directory under `.claude/skills/` with `.claude-plugin/plugin.json` does auto-load as `<name>@skills-dir`; project scope does gate on workspace trust; project-scope plugins do *not* walk up to the repo root; background monitors genuinely do not load from project scope; `SKILL.md` is live while `hooks/`, `.mcp.json`, `agents/` need `/reload-plugins`. Every constraint in that table checks out against the current docs. **`bin/` is also confirmed** — executables there are added to the Bash tool's `PATH` while the plugin is enabled, which is what §7.3 needs.
- **§7.1's pin is real.** `v0.8.1` exists (2026-01-20). Two facts the spec should absorb, in E4 below.
- **§2 / §3 are the right spine.** Deriving skills from track × perspective × authority, and separating the four deliberation failure modes, is the part of this spec that will still be right in a year.

What follows is what I would fix before writing code. Findings are ranked: **B** blocks implementation, **C** consistency, **R** redundancy, **G** coverage, **E** efficiency.

---

## B — Resolve before implementing

### B1. The authority axis is not enforced. It rests on Claude Code's Bash prompt.

**Where:** §2.3 (`Modify the model | explicit authorisation | PreToolUse hook + CLI`), §10.1, §13 Q8.

§10.1's hook blocks `Edit`/`Write` on `.capella` and `.aird`. Nothing gates **Bash**. The agent can run:

    se-buddy apply CP-0022 --authorized-by "yes, go ahead"

and no code refuses it. `--authorized-by` is free text the agent types; §2.3's "only words the engineer actually said" is instructed, not enforced. The same hole voids §10.1 itself — the guard stops `Edit`/`Write` but not `cp`, `mv`, `python -c`, or a shell redirect onto the model file.

In practice the gate today is Claude Code's own Bash permission prompt. That is outside the spec, and it disappears the moment a project allowlists `Bash(se-buddy:*)` — which a project *will* do, because §7.3's read commands are called constantly and prompting on each is intolerable.

This matters more than any other finding because §13 Q8 will pass, `SPEC-COVERAGE.md` will record authority as **enforced**, and it will not be.

**Suggested fix**, strongest first:

1. `apply` / `revert` / `remember` / `record` refuse unless stdin is a TTY and the engineer types a confirmation the agent never sees. The agent then *cannot* authorise, structurally.
2. A `PreToolUse` hook on `Bash` matching the write verbs, so the write path stays gated even under an allowlist.
3. Split the CLI so read verbs are safely allowlistable and write verbs carry a separate binary name; the generated project README states that the write binary must never be allowlisted, and `doctor` reads `.claude/settings*.json` and reports it if it is.
4. Add to §13: *"Can the agent apply a change without a human keystroke?"*

### B2. §5.1 promises no install step; §12.8 says there must be one.

**Where:** §5.1 ("no marketplace, no install step, no copying"; "vendors its own pinned dependencies as nested submodules") against §12.8 ("capellambse pulls `lxml` and other C-extension packages that cannot be vendored by submodule… **This is unresolved and blocks phase 1**").

A direct contradiction inside one document. §5.1's constraint table asserts vendoring solves dependencies; §12.8 concedes it cannot. §11 Phase 1 does not list the bootstrap among its contents even though §12.8 says it blocks that phase.

**Suggested fix:** decide the bootstrap now — it changes §5.1's promise, §7.3 (`doctor` must detect and repair), and Phase 1's contents. Recommendation: `bin/se-buddy` is a thin launcher that creates and populates a venv under the submodule on first run, `doctor` reports and repairs it, and §5.1's row becomes *"first run in a fresh clone builds a venv; network required once"*. Then say that in the README instead of claiming zero install.

### B3. The D8 act vocabulary is not closed over the storage model.

**Where:** §3 D8 (seven acts, each with a "Produces" column) against §5.2 (layout) and §9 (schemas).

Trace each act to where its product lands:

| Act | Produces | Has a file? | Has a command? |
| --- | --- | --- | --- |
| `DECIDE` | `ADR-nnnn` | yes | `remember decisions` |
| `AUTHORISE` | `--authorized-by` text | yes (`CHANGE.authority`) | `apply` |
| `CONFIRM` | "a FACT the agent may then cite" | **no** | **no** |
| `REVIEW` | "acceptance, or a correction" | **no** | **no** |
| `DRAW` | "a ticked followup item" | file yes | **no tick command** |
| `SUPPLY` | viewpoint, principle, requirement, risk | partly | **no register write** |
| `PRIORITISE` | "a sequence" | **no** | **no** |

Four of seven acts produce something the spec then has nowhere to put. Because the reasoning layer is Claude Code (§1.1) and its context does not survive a session, an unpersisted answer is a *lost* answer — the agent asks again next session, which is precisely the cost D8 exists to avoid.

`CONFIRM` is the sharpest case: D8 says it produces "a FACT the agent may then cite", and C01 says a fact must cite an element or record id. A confirmed fact with no record id cannot be cited under the agent's own rules.

**Suggested fix:** give `CONFIRM`, `REVIEW` and `PRIORITISE` a home. `knowledge.yaml` plausibly takes CONFIRM and REVIEW (one row each: the ask it answers, the answer, date, provenance). PRIORITISE is a field on the ask itself — a `sequence:` written back. Then add one write verb, `se-buddy answer <ask-id> <file>`, that closes an ask; B3a becomes a special case of it.

### B3a. A followup checklist can never be ticked.

**Where:** §10.3 (`apply` **MUST** refuse while any followup checklist is unticked) against §7.3 (`se-buddy followup` sits under "Read-only unless marked").

There is no command to tick an item. The engineer could hand-edit `CHANGE-nnnn.followup.md`, but §9 requires every followup line to carry the enforced D8 fields, and a hand-edited Markdown file is not schema-validated (see C1).

As written, the second `apply` in a project's life is unreachable.

### B4. Registers are read-only. Phase 2 depends on writing them.

**Where:** §7.3 (`se-buddy register <name> [filter]` under "Read-only unless marked"; `remember` domains are `principles | decisions | assumptions | viewpoints | knowledge` — no register) against §8.1 (`risk-manage  identify → assess → treat → track → close, both registers`) and §11 Phase 2.

There is no write path to `registers/`. `risk-manage` cannot do four of its five verbs, and `SUPPLY` cannot deliver a requirement or a risk (B3).

**Suggested fix:** `se-buddy register-write <name> row.yaml`, or fold registers into the `remember` domain list and rename the command — which also fixes C5.

### B5. §6.3 assumes a resident process; §7.3 specifies one-shot commands. This decides spike 6.

**Where:** §6.3 ("Transitive closure is a graph walk over objects **already in memory**") against §7.3 (independent CLI invocations) and §12.6 (`bin/` vs MCP, "decide on evidence, not preference").

A one-shot `bin/` command re-parses the whole `.capella` on every call. A working session makes tens of calls. Nothing holds a parsed model between them, so §6.3's premise is false under §7.3's design.

Spike 6's stated criteria are "simpler / avoids per-server approval" against "structured results". They omit the criterion that will actually decide it: **model load time × calls per session.** An MCP server is a resident process that parses once; `bin/` is not, unless you add a cache or a daemon.

**Suggested fix:** rewrite §12.6 to measure cold-parse time on a representative model first, then decide. If parse costs more than a second or two, either MCP wins or `bin/` needs a cache keyed on the model file hash — and that cache is also the mechanism G6 needs.

---

## C — Consistency

### C1. Followup checklists are Markdown but carry an enforced YAML schema.

§5.2 lays them out as `changes/CHANGE-nnnn.followup.md`. §9 says every followup checklist line **MUST** carry `act`/`object`/`done_when`/`blocks`/`default`, and "**Enforced:** an open item missing `act` or `done_when` is rejected". A `.md` file cannot be schema-validated without a parser you would have to write — which contradicts §7.1's "do not hand-roll".

**Fix:** make it `CHANGE-nnnn.followup.yaml` and render Markdown on demand, or explicitly downgrade that enforcement to instructed and record it in `SPEC-COVERAGE.md`.

### C2. `revert` takes the wrong id.

§7.3 has `se-buddy revert CP-nnnn`. Snapshots are per-apply (§5.2, §10.2), records are `CHANGE-nnnn`, and nothing says a CP may be applied only once — §10.3 bounds passes, not proposals. Revert should key on the thing that has a snapshot: `se-buddy revert CHANGE-nnnn`.

### C3. "Ask first" is labelled as enforced by schema validation. Schema validation cannot enforce it.

§2.3 row: `Write registers / memory | ask first | schema validation`. Schema validation checks shape, not whether an ask preceded the write. §10 opens by demanding the enforced/instructed distinction stay "visible throughout" — this row breaks it in the very table that defines the distinction. Mark it **instructed**, or TTY-gate the write verbs per B1 and it becomes genuinely enforced.

Minor, same row: §7.3 cites C08 for `remember`; C08 is decision authority. C05 / §2.3 is the applicable rule.

### C4. `doctor` cannot report agent-log entries newer than the pinned commit.

§5.5: "`se-buddy doctor` **MUST** report entries newer than the commit the project has pinned."

The submodule working tree *is* that commit, so its `AGENT-LOG.md` contains nothing newer by construction. The set is always empty. After `--remote` the pin has already moved, so those entries are no longer "newer" either.

**Fix:** `profile.yaml` records the last acknowledged `AC-nnnn`; `doctor` reports every entry in the checked-out log newer than that, and prompts to acknowledge. That gives the intended behaviour — after `--remote` the engineer sees exactly what arrived — with no fetch required.

### C5. The layer boundary in §5 is not reflected in the layout or the CLI.

- §5 lists **"project rules"** in PROFILE. No file in §5.2 holds it. If it is `principles.yaml`, §5 should not list both.
- `assumptions.yaml`, `knowledge.yaml` and `glossary.yaml` appear in §5.2 but in **neither** layer's contents column in §5.
- **`glossary.yaml` has no command.** Not a `memory` domain (`principles | decisions | assumptions | viewpoints | knowledge`), not a register, not a record. It can be neither read nor written.
- `se-buddy memory` spans PROFILE (`principles`, `viewpoints`) and MEMORY (`decisions`), so the command name asserts a boundary the command crosses.

**Fix:** reconcile §5's contents column against §5.2 item by item; add `glossary` to the domain list; either rename `memory` to something layer-neutral or split it.

### C6. `write-plain` is in two phases.

§11 Phase 1 contents include "shared … skills", which per §8.1 includes `write-plain`. Phase 2 lists `write-plain` again. Pick Phase 1 — §6.1's size budgets apply to ADRs written there.

### C7. "Read-only unless marked" is false as stated.

§7.3's header says read-only unless marked, then lists `propose` (writes `CP-nnnn`) and `record` (writes `CHANGE-nnnn`) unmarked. In a spec whose spine is authority, the command table should mark every verb that writes, and say *what* it writes: model, memory, or profile.

### C8. The five validation layers are named once and never defined.

§7.2 gives `validate` five layers — *structural, representation, architectural, traceability, consistency* — and §7.3 echoes "five layers". Nothing says what each checks.

Meanwhile §2.2 rule 1 draws a hard line between structural validation and perspective completeness, and §13 Q6 polices it: *"Is structural validation read anywhere as perspective completeness?"* An implementer cannot answer Q6 against a boundary the spec never draws. The **architectural** layer is the ambiguous one — it sounds like `arch-review`'s job (§8.1) and like `perspective`'s job (§2.2).

**Fix:** define the five, one line each, with one example finding apiece.

### C9. "No network dependency" is literally false.

§1.1: "no provider credential, and **no network dependency** in this agent." Install (§5.1), upgrade (`--remote`) and the Python bootstrap (§12.8) all need network. The intended claim is *no model-API calls at runtime*. Say that — a MUST that is false as written invites an implementer to argue with the section that matters most.

### C10. Domain-pack attack surfaces sit on an undrawn side of the C02/D5 line.

§5.4 requires `domain.md` to carry "Reviewer attack surfaces: known anti-patterns". C02 says distinguish "inconsistent with our architecture" (a real finding) from "different from generic best practice" (usually irrelevant), and D5 makes "treating generic best practice as a project requirement" a **reportable defect**.

Domain-pack attack surfaces *are* domain best practice — but the project supplied them, and that is what makes them binding. `arch-review` needs this stated, or it will either suppress real findings or trip D5 on every one of them.

**Fix:** one line in §5.4 — *content in `domain.md` is project-supplied and therefore binding as a project requirement; C02 and D5 apply to anything the agent brings from outside the profile.*

---

## R — Redundancy

- **R1.** "Never combine `--remote` with `--recursive`" appears three times: §5.1 constraint table, §7.1 drift table, §7.1 README MUST. Keep the drift table (it explains *why*) and cite it from the other two.
- **R2. `trace-rationale` and `retrieve-context` overlap.** "what exists, how it relates, **and what was decided**" against "why it looks like this, **and who decided**". Both answer the decision question; both are served by `se-buddy show` + `trace`. §8.1 already names `arch-transition`→`arch-perspective` as the first merge candidate; these two are the second, and unlike that pair they produce the same artefact (none) at the same authority level (read) — which is exactly the test §8.1 sets for merging.
- **R3. `model-validate` / `validate`'s architectural layer / `arch-review`** form a three-way overlap that C8 has to resolve anyway.
- **R4.** §6.1 states the no-copying rule twice ("each cites the one before it and none copies it"; "a change record cannot *contain* the diff or the validation report"), and §9's `CHANGE-nnnn` row a third time. §9's row is the enforceable one; §6.1's second sentence is the keeper; the first is prose.

Note the spec restates its core rules across §2 / §4 / §9 / §13 by design — rule, behaviour, schema, review question. That is a spec doing its job, not redundancy. R1–R4 are the cases where the restatement carries no new enforcement.

---

## G — Coverage

Things a real Arcadia workflow needs that the spec does not name. G1–G4 are the ones I would not implement without.

### G1. Interfaces and exchanges are never mentioned.

`ComponentExchange`, `FunctionalExchange`, `ExchangeItem`, ports and interfaces appear nowhere in 735 lines. In Arcadia practice this is where the highest-value automated checks live and where integration risk concentrates:

- a `FunctionalExchange` with no `ExchangeItem` allocated
- a `ComponentExchange` carrying no functional exchange
- a port with no exchange, or an exchange crossing a boundary no viewpoint permits
- an `ExchangeItem` whose elements have no requirement behind them

`trace` (§6.3) would traverse them incidentally, but nothing *checks* them. This is the largest single coverage gap: it is exactly "engineering judgement, not Capella mechanics" (§7.2), so no library will supply it, and it is the class of finding an engineer cannot cheaply get by eye.

**Fix:** name interface consistency explicitly as one of the five validation layers (C8), and add exchanges and `ExchangeItem`s to `trace`'s closure.

### G2. Functional chains, scenarios, and modes/states are absent.

§2.2 says LogicalArchitecture stops on "an architecture **proven** best by multi-viewpoint analysis". In practice that proof runs through functional chains and scenarios — they are how a viewpoint claim is demonstrated rather than asserted. Modes and states play the same role for availability and degradation arguments. None appear.

At minimum, say whether they are in scope for Phase 1 retrieval. If out, put it in §1's non-goals — a systems engineer will expect them, and silence reads as oversight rather than boundary.

### G3. "Deliberately not carried" has no artefact, so `arch-transition` generates permanent noise.

§2.2 rule 2 is one of the best paragraphs in the spec: every source element is realized, refined, *deliberately not carried*, or missing — "**and the model cannot distinguish the last two**".

The spec identifies the gap and then assigns nothing to close it. So every run of `arch-transition` reports the same unknowns, forever, and the engineer re-adjudicates the same elements every pass. That is the failure mode D7 protects against arriving by another route: not lost work, but work that can never be *finished*.

**Fix:** a `not-carried` register (or an ADR subtype) recording element id, the perspective pair, why it is not carried, and who decided. `arch-transition` then reports only what is genuinely new. This is the highest-leverage single addition in this review — it converts a permanently noisy check into a converging one.

### G4. Two of five perspectives can never report done, and the fix already exists in the spec.

§2.2 stop criteria: OperationalAnalysis stops on "agreement with the customer", EPBS on "agreement with suppliers". §7.2: "agreement-based criteria always `UNKNOWN`". So `se-buddy perspective OperationalAnalysis` returns UNKNOWN on every run for the life of the project. Honest, and useless.

The machinery to fix it is already specified and unused: D8's `CONFIRM` act "Produces: **a FACT the agent may then cite**". An engineer confirming "the customer signed off on OA at review R3" turns UNKNOWN into FACT.

**Fix:** wire `CONFIRM` to a record (B3) and let `perspective` read it. Agreement criteria then report `UNKNOWN` *until confirmed*, which is the real semantics.

### G5. No baseline or gate concept, though the domain pack demands gate evidence.

§5.4 requires `domain.md` to state "what a reviewer, auditor or customer will ask to see, **and at which gate**". Nothing in the agent knows what a gate is, or which model state satisfied one. `snapshots/` is per-apply, not per-gate.

For any project actually held to a standard — which §5.4 assumes — "what did the model look like at PDR, and which requirements were verified then" is a question that *will* be asked. A light answer: `se-buddy baseline <name>` writes a manifest — model file hash, register row ids and statuses, open ask ids — and tags git. Cheap, and it makes §5.4's evidence expectations actionable rather than descriptive.

### G6. Nothing detects that the model changed under the agent.

§1 is explicit that "the engineer works in Capella; this works alongside it". So the `.capella` file changes outside the agent, mid-session, routinely — and Capella may hold it open with unsaved state.

`se-buddy apply` (§10.2) validates targets against a model parsed at some earlier point. If the engineer edited in Capella since, apply overwrites their work or fails confusingly. `se-buddy record` exists to capture hand edits, but nothing *detects* that there are any.

**Fix:** hash the model at parse; re-check immediately before apply and refuse on mismatch, naming the drift; `doctor` and `inspect` report "model changed since last parse — run `record`?". The hash also serves B5's cache.

### G7. Delete is not wired to the diagram inventory.

§7.4 gives read access to which elements appear on which diagram — required "for impact analysis and for the followup checklist". §10.2 requires a distinct flag for deletion but never consults that inventory.

Deleting an element that appears in `.aird` leaves dangling representations in a file the agent must never write (§7.4). The engineer finds out when Capella complains.

**Fix:** `--delete` refuses, or emits `DRAW` followups, for every diagram the inventory says references the target. All the pieces are specified; only the wiring is missing.

### G8. Git discipline is unstated.

Everything is "YAML in git" and C06 reversibility depends on `git diff`, but nothing says whether `apply` requires a clean working tree, whether it commits, or what `revert` means against uncommitted changes. And `snapshots/` puts a full `.capella` copy in git per apply — on a real model, tens of MB per change, with no retention policy.

**Fix:** state it. Suggestion: `apply` requires the model file clean, does **not** commit (the engineer's call), and snapshots are retained N deep or pruned once a `CHANGE` is committed — the git history is the real archive.

### G9. Requirements have no import path.

§8.1 correctly declines a requirements-management skill. But `registers/requirements.yaml` then has to be typed by hand, while §7.1 already lists "Requirements and PVMT viewpoints — `capellambse` extension support". Real projects exchange requirements as ReqIF. One line acknowledging import as a deferred option stops the register looking like an oversight.

### G10. `bin/` needs a Windows entry point.

§12.5 says "Confirm on Windows specifically" — good. Concretely: a shebang script in `bin/` does not execute on Windows. Ship `bin/se-buddy.cmd` (or a `.ps1`) alongside the POSIX script, or invoke via `python -m se_buddy`. This is the actual development platform, so it belongs in the spike as a named deliverable rather than a confirmation.

---

## E — Efficiency

### E1. No command bounds its output. This will decide whether the agent is usable.

`inspect` ("model + diagrams + memory overview"), `trace` (transitive closure), `asks` ("every open ask across records") and `show` are all unbounded. On a real Capella model, one `trace` can return thousands of rows straight into the reasoning layer's context.

D6 already has the right instinct — counts, not enumerations, computed by the CLI. Extend it to a **MUST** on the CLI surface: every command has a default limit and depth, `--limit`/`--depth` widen it, and **any truncation is reported**, never silent. A silently truncated trace reads as a complete one, which is worse than a slow one.

### E2. Session resume is unspecified, and `asks` is already the answer.

The reasoning layer is Claude Code (§1.1), so context does not survive a session. `se-buddy asks` — "every open ask across records, in D8 shape, sequenced" — is exactly the right resume surface. Say so: name it the documented first command of every session, and have it print the current track, tier and perspective alongside the asks. A large practical win for one line of spec, and it is what makes the second session as good as the first.

### E3. Pass the tier down to the CLI.

D1 makes the agent declare `lookup | judgement | decision` first. Nothing downstream consumes it. A `--tier` flag that caps output — a lookup gets counts and ids, a decision gets evidence — makes D1 mechanically useful instead of purely declarative, and pays for itself in context on every lookup.

### E4. Two facts about the pin to absorb into §7.1.

- **v0.8.1 drops Python 3.10.** The spec states no Python floor. It must, and `doctor` should check it — part of B2's bootstrap.
- **v0.8.0 changed `search()` to exact type matches by default.** `se-buddy search` (§7.3) is a core read verb built directly on this. Any recipe written against 0.7.x behaviour is wrong at the pin.

Also worth noting: the library README claims coverage of "most of the present Capella ontology" and publishes no Capella version compatibility matrix. §12.1 tests against Capella 7.0.1 and §12.3 tests ontology coverage — both correctly scoped. Keep §12.1 first; it is the one that can invalidate §7.1.

---

## Suggested additions to §13

The review questions are good. Four to add, each tracking a finding above:

13. Can the agent apply a change without a human keystroke? (B1)
14. Does every D8 act have somewhere its answer is written? (B3)
15. Does any command return an unbounded result set, or truncate silently? (E1)
16. Does `apply` detect that the model changed outside the agent? (G6)

---

## Asks

    act        REVIEW
    object     B1 — apply is gated only by Claude Code's Bash prompt, which an allowlist removes
    done when  you pick one of the four fixes, or accept the exposure and record it in
               SPEC-COVERAGE as instructed
    blocks     phase 3, and the honesty of §13 Q8
    default    none — this blocks

    act        DECIDE
    object     B2 — the Python bootstrap: venv built by bin/ on first run, a documented
               pip install -e, or something else
    done when  §5.1's "no install step" row is rewritten to match, and Phase 1 lists the bootstrap
    blocks     phase 1 (§12.8 says so itself)
    default    none — this blocks

    act        DECIDE
    object     B3/B4 — where CONFIRM, REVIEW and PRIORITISE answers are written, and the single
               write verb that closes an ask
    done when  each of the seven D8 acts has a file and a command
    blocks     phase 2 (risk-manage cannot write); B3a unblocks the second apply
    default    none — this blocks

    act        SUPPLY
    object     E4 — the Python floor implied by capellambse v0.8.1, for §7.1 and the doctor check
    done when  §7.1 states it and doctor checks it
    blocks     nothing — but it is part of B2
    default    assume >=3.11 and record it as an ASSUMPTION

    act        PRIORITISE
    object     G1–G4 are all worth doing; G3 (a "not carried" record) is the one I would take first
    done when  you name the order
    blocks     nothing
    default    G3, then G4, then G1, then G2 — G3 and G4 each convert a permanently-unknown check
               into a converging one for a few lines of schema; G1 adds the highest-value new
               findings; G2 may turn out to be a non-goal

**First: B2.** It is the only one the spec already declares blocking, and its answer changes §5.1, §7.3 and Phase 1's contents — so every other edit is cheaper once it lands.

---

## Open on my side

The brief asked me to check coverage "from my previous workflow". Nothing in this repo records what that workflow was — no memory files, no notes, one spec and four commits. So G1–G10 are derived from Arcadia practice and from the spec's own internal commitments, not from your prior process. If you describe how you were doing this before — what you tracked, where it lived, which steps were manual and which were the ones you actually resented — I can run the coverage pass again against that specifically. It is the one section of this review that is currently reasoning from first principles where it should be reasoning from evidence.
