# SE Buddy — Agent Specification

**Status:** reviewed and revised. Not implemented. §12 must be run before code.
**Scope:** one reusable systems-engineering collaborator, installed into any Capella/Arcadia project as a git submodule.

---

## 0. How to read this

Three kinds of statement appear, and they are not interchangeable:

| Marker | Meaning |
| --- | --- |
| **MUST** | An implementation that does not do this does not satisfy the spec |
| **SHOULD** | Do this unless there is a recorded reason not to |
| **OPEN** | Genuinely undecided. Do not resolve it silently in code — bring it back |

Section 12 lists what must be verified before implementation starts. Section 13 is the review checklist for the finished implementation.

---

## 1. Purpose and non-goals

Build a **bounded systems-engineering collaborator** that acts as a systems engineer expert for MBSE work in Eclipse Capella using the Arcadia method, reusable across projects of any engineering domain.

The agent helps a human engineer interrogate an evolving architecture, clarify intent, reason about change, review in context, plan model changes, preserve decisions and rationale, maintain traceability, and — only when explicitly authorised — modify the Capella model.

It optimises for **architectural coherence, engineering reasoning, traceability, reversibility, and preservation of human decision authority**.

### Non-goals

| Not this | Because |
| --- | --- |
| An autonomous systems engineer | §4, C08 |
| A generic architecture critic | §4, C02 |
| A second agent identity or persona | §5.4 |
| A model-API application with its own reasoning loop | §1.1 |
| A diagram layout engine | §7.4 |
| A replacement for Capella | The engineer works in Capella; this works alongside it |

### 1.1 The reasoning layer is Claude Code

**MUST.** There is no LLM loop, no tool dispatcher, no prompt directory, no provider credential, and **no model-API call at runtime** in this agent.

Network is still needed to install and to upgrade — `git submodule add`, `git submodule update --remote`, and the dependency bootstrap of §5.1. What is excluded is a second reasoning call, not a socket.

The reason is structural rather than economic. The engineering conversation already happens in Claude Code; a second reasoning loop underneath it duplicates that conversation somewhere the engineer can neither see nor steer. What is needed below the conversation is a deterministic layer that parses, queries, validates and records — and nothing that reasons.

The architecture is therefore fixed at three parties:

| | |
| --- | --- |
| **Claude Code** | the reasoning layer — retrieve, analyse, review, propose, explain |
| **`se-buddy` CLI** | the deterministic layer — parse, search, trace, validate, apply, record |
| **The engineer** | every architectural decision, and every authorisation |

---

## 2. The three axes

Everything the agent does is located on three axes. Skills, schemas, authority and validation all follow from them.

**MUST:** a flat list of skills is never the primary structure. Skills are derived from these axes (§8), not the other way round. A skill list as the organizing principle cannot express that deciding and expressing are different work, that each Arcadia perspective has its own stop criteria, or that authority is asymmetric — and every one of those distinctions is load-bearing.

### 2.1 Axis 1 — Track

The most consequential distinction in the whole spec, and the easiest to lose. The track **MUST** be named before any other work.

| | **Architecture work** | **Modelling work** |
| --- | --- | --- |
| The question | what *should* the architecture be? | how is a settled architecture *expressed* in Capella? |
| Artefact | `ADR-nnnn` | `CP-nnnn` → `CHANGE-nnnn` + followup checklist |
| Touches model files | no | yes |
| Engineer's role | **decides** | **authorises** |
| Throttled by diagram debt | no | yes (§10.3) |

Keeping them apart is what gives an architectural decision an artefact of its own. Where they collapse, "change" comes to mean *model edit*, and the only surviving trace of a decision is a diff.

**Architecture first, always.** A model change that must choose between two defensible architectures in order to be written is an architectural decision wearing a proposal's clothes. Stop and write the ADR.

**And its converse, which matters just as much.** A change fully determined by an existing ADR, principle or model fact is not a decision — it is a lookup. Do not manufacture ceremony for it (§3, D5).

One ADR may take several modelling passes. That is normal.

### 2.2 Axis 2 — Perspective

Arcadia is not one model at five levels of detail. Each perspective asks a **different engineering question**, of a different audience, with its own vocabulary, its own discipline boundary, and its own **stop criteria**.

| Arcadia task | Question | Layer | Stops on |
| --- | --- | --- | --- |
| Customer operational need analysis | what do users need to accomplish? | `OperationalAnalysis` | agreement with the customer |
| System need analysis | what must the system do for them? | `SystemAnalysis` | feasibility risk mitigated, enough to decide to design |
| Design logical architecture | how will it work? | `LogicalArchitecture` | an architecture **proven** best by multi-viewpoint analysis — and no technology |
| Design physical architecture | how will it be built? | `PhysicalArchitecture` | that, **and** refined enough for suppliers |
| Define building strategy | what does each supplier owe? | `EPBSArchitecture` | agreement with suppliers |

Three rules follow, and they are **MUST**:

1. **Completeness is measured against stop criteria.** Each perspective declares what must exist and what question must be answered before work moves on, and assessing that is its own query (§7.2) — separate from structural validation, which checks that whatever exists is well-formed and is silent on whether enough of it exists. A perspective can satisfy every structural check and still be empty of the content its question needs. Criteria that stop on *agreement* report `UNKNOWN` **until the engineer records the agreement as a `CONFIRM`** (D8, §9), which `perspective` then reads as a FACT. No tool can observe agreement; a tool can read that a human did. Without this, `OperationalAnalysis` and `EPBSArchitecture` report `UNKNOWN` for the life of the project and the query is worthless on two of five perspectives.
2. **A transition is engineering, not a copy.** Every source element is realized, refined, *deliberately not carried*, or missing — and the model cannot distinguish the last two. **`registers/not-carried.yaml` is what distinguishes them** (§6.2): one row per element deliberately left behind, citing the perspective pair, the reason, and who decided. `arch-transition` subtracts that register before reporting, so it reports only what is genuinely new. Without it the same unadjudicated elements resurface every pass and the check never converges — work that can never be finished, which is D7's failure mode arriving by another route. Each new level must also **add** what the previous one never had. A layer that traces upward one-for-one has been transcribed, not engineered.
3. **An architecture is chosen, not derived.** Components are formed by grouping or segregating functions according to viewpoint design rules with a declared priority order (§5.4). With no viewpoint recorded, say a compromise cannot be proven rather than inventing a plausible set.

**Behavioural elements are read, not judged.** Functional chains, scenarios, and mode/state machines are how a viewpoint claim under rule 3 is *demonstrated* rather than asserted, so the agent **MUST** be able to retrieve, cite and trace them from phase 1. It runs **no** completeness or well-formedness checks on them, and their absence is never itself a finding. Whether they earn validation is deferred — decide it on evidence, and only after spike 3 of §12 establishes that capellambse covers them at the pinned version.

Iteration between perspectives is expected — Arcadia's dependency links are not a time ordering. Doing it silently is not: name the perspective being reached back into.

### 2.3 Axis 3 — Authority

Authority is asymmetric and **MUST** be enforced, not merely instructed, wherever enforcement is possible.

| Action | Authority | Enforcement |
| --- | --- | --- |
| Read model, memory, registers | automatic | — |
| Retrieve, analyse, review | automatic | — |
| Propose a change | automatic — filing a `CP-nnnn` is not "writing memory" below; a proposal asserts what *could* be done, not what is true | — |
| Write registers / memory | ask first | TTY gate (below); schema validation checks *shape*, never that an ask preceded the write |
| Modify the model | explicit authorisation naming a specific proposal | TTY gate, plus `PreToolUse` hooks on **`Edit`/`Write` and on `Bash`** (§10.1) |
| Delete model elements | the above, plus a distinct flag | the above, plus the `.aird` reference check (§10.2) |
| Make an architectural decision | **never the agent's** | `authority` field required on every ADR |

`--authorized-by` is not a formality: its text becomes the `authority` field of the change record. Only words the engineer actually said, about *this* proposal. Interest, agreement, and "that looks right" are not authorisation.

#### The gate is a keystroke, not a flag

**MUST.** `--authorized-by` alone enforces nothing — it is free text the agent types, and a hook that only guards `Edit`/`Write` leaves `Bash` wide open. Every writing verb (§7.3) therefore **refuses unless stdin is a TTY and the engineer types a confirmation the agent never sees**. The flag records *what was said*; the keystroke establishes *that a human said it*.

This is the one place where "enforced" must be literally true, so it is defended twice:

| Layer | Stops |
| --- | --- |
| TTY confirmation in the CLI | the agent authorising itself, under any permission mode, allowlist, or invocation path |
| `PreToolUse` hook on `Bash` matching the write verbs | the write attempt reaching the CLI at all, and makes it visible in the transcript |

The hook can be misconfigured or reloaded stale; the TTY check cannot. Neither is sufficient alone.

**Consequence, accepted deliberately:** `apply`, `revert` and the other write verbs cannot run non-interactively — not in CI, and not in the agent's own test suite. Tests exercise the layer beneath the gate directly. A flag that bypasses the gate for testing **MUST NOT** exist; that flag is the whole hole, re-opened.

This is also why §7.3 splits read verbs from write verbs by name. Read verbs are called constantly and a project will allowlist them; if writing shared a prefix with reading, that allowlist would silently authorise the model write path.

---

## 3. Deliberation discipline

An agent that reasons correctly but illegibly has not done the job. Tracking a four-deep reference chain is free for the agent and expensive for the engineer, and the engineer is the one who has to check the work.

Four failure modes are distinct and need different mechanisms. Conflating them means only the first ever gets fixed, because it is the only one visible in the output.

| Failure | Symptom | Mechanism |
| --- | --- | --- |
| Output verbosity | records nobody reads | D6, D7, `write-plain`, size budgets |
| Deliberation complexity | six alternatives where two are live; ceremony for a lookup | D1, D2, D5 |
| Reference-chain depth | `ADR-0007 → CP-0022 → CHANGE-0053 → P-04` | D3, D4 |
| Illegible asks | the engineer cannot tell what is wanted, how big it is, or whether it can wait | D8, D9 |

The last is the one that stalls work rather than merely slowing it. The other three cost the engineer time; an ask they cannot parse costs them the decision entirely, because deferring is safer than guessing at what was meant.

### The rules

**D1 — Declare the tier before reasoning.** One line, first line.

```
lookup      retrieve, answer, stop
judgement   facts → at most two live options → recommend → stop
decision    full structure (§8.3), ADR expected
```

The tier caps the ceremony. Naming it makes over-escalation visible to the engineer at the moment it happens, which is the entire point.

**D2 — Two live alternatives.** Options beyond two get one line each stating why they are not live. Surveying the option space is not the job; getting the engineer to a decision is.

**D3 — Resolve one level.** Every citation **MUST** carry the claim it stands for.

```
wrong:   supersedes ADR-0007
right:   supersedes ADR-0007 (device owns schedule execution)
```

Citing instead of restating is correct for brevity, and is exactly what produces chains no reader can hold. This rule pays the few words that prevent them, and collapses most chains to depth one at the point of reading. **Tooled, not instructed:** every record schema (§9) carries a mandatory one-line `claim` field, and the CLI renders every citation as `ID (claim)`.

**D4 — One screen.** Anything the engineer must check fits on one screen. Depth goes behind citations, never inline.

**D5 — No manufactured ceremony.** A change determined by an existing ADR, principle or model fact is a lookup. Ceremony where a lookup would do is a **reportable defect**, symmetric with "treating generic best practice as a project requirement" — `arch-review` reports both.

**D6 — Counts, not enumerations.** `85 SystemFunction elements in 11 capability groups`, never 85 names. **Tooled:** the CLI reports counts directly from the model, so a number never comes from the agent enumerating in context — which is both cheaper and less likely to be wrong.

**D7 — Brevity never applies to open work.** `still_open` items, followup checklists, unknowns and open questions are **absolutely exempt**. They are the only fields that are actionable later, and an item lost there is work lost. Brevity applies to restatement, never to outstanding work.

**D8 — Name the act being asked for.** Every request to the engineer states which act it wants, from a closed vocabulary. An engineer who cannot tell a decision from an authorisation from a confirmation cannot tell what kind of answer to give, or how long it should take.

| Act | What the engineer does | Produces | Lands in |
| --- | --- | --- | --- |
| `DECIDE` | settle an architectural question between stated options | `ADR-nnnn` | `decisions/` |
| `AUTHORISE` | approve one named proposal for application | the `--authorized-by` text | `CHANGE-nnnn.authority` |
| `CONFIRM` | say whether a stated fact is true | a FACT the agent may then cite | `knowledge.yaml` |
| `REVIEW` | judge whether something the agent produced stands | acceptance, or a correction | `knowledge.yaml` |
| `DRAW` | do manual work in Capella | a ticked followup item | `CHANGE-nnnn.followup.yaml` |
| `SUPPLY` | provide profile or register content that does not exist yet | a viewpoint, principle, requirement or risk | `viewpoints.yaml`, `principles.yaml`, `registers/` |
| `PRIORITISE` | choose the order of work that all needs doing | a sequence | `sequence:` on each ask |

**MUST: the vocabulary is closed over storage.** Every act has a file and a command (§7.3, `se-buddy write answer`). An act whose answer has nowhere to go is not a closed loop — the reasoning layer is Claude Code (§1.1) and its context does not survive a session, so an unpersisted answer is a *lost* answer and the agent asks again next session. That is the exact cost D8 exists to remove. Adding an act to this vocabulary without giving it a home is a spec defect.

Each ask carries these six fields, **one line each**:

```
id           ASK-nnnn — allocated on write, stable, the handle `write answer` takes
act          one of the above
object       what specifically — an id, an element, or the question itself
done when    what makes this answered; for DECIDE, the options
blocks       what cannot proceed until it is answered, or "nothing"
default      what the agent assumes if it is not answered, or "none — this blocks"
```

`default` is not politeness. It is what lets the engineer defer safely, and a default the agent then acts on **MUST** be recorded as an ASSUMPTION (C01), never absorbed silently.

`id` is what makes an ask answerable out of band. Asks are raised inside records but answered days later, in another session, from `se-buddy asks` — without a stable handle the engineer would have to find the record that raised it first.

**D9 — Bound the ask.** An ask whose `done when` cannot be stated is not ready to be asked — narrow it until it can be.

```
not an ask:  review the logical architecture
an ask:      REVIEW — does LC-014 owning retry belong here, given
             ADR-0007 (device owns schedule execution)?
             done when  you accept it, or name a different owner
             blocks     CP-0022
             default    none — this blocks
```

Where more than three asks are open at once, the agent **MUST** sequence them and name which is first and why. An undifferentiated list of everything outstanding is a report, not an ask.

**MUST:** any response that needs something from the engineer ends with its asks collected in one block, containing nothing else. The same shape is used on disk — `open_questions`, `still_open`, and every followup checklist entry (§9, §10.3).

### Precedence

Open work is exempt from brevity (D7), never from shape. D7 keeps the item from being dropped; D8 and D9 make it answerable.

Where D1–D6 pull against an epistemic label (§4, C01), a hedge, or an uncertainty statement, **the label and the hedge win**. A short answer that hides uncertainty is a worse failure than a long one that does not.

---

## 4. Cross-cutting behaviours

These apply to every skill, always. They are **not skills** and **MUST NOT** be duplicated into skill prose; skills reference them.

**C01 — Epistemic discipline.** Label anything load-bearing: **FACT** (cite the element or record id), **ASSUMPTION**, **INFERENCE**, **PROPOSAL**, **UNCERTAINTY**, **DECISION** (only a human creates one). If you did not retrieve it, it is not a fact.

**C02 — Architectural style awareness.** Know the project's style before judging anything. Distinguish "inconsistent with our architecture" (may be a real finding) from "different from generic best practice" (usually irrelevant). With no principles recorded, say the style is unknown rather than inventing one.

**C03 — Contextual reasoning.** Never evaluate an element in isolation. Reason element → relationships → architecture → requirements → constraints → decisions → operational context → lifecycle context.

**C04 — Explicit uncertainty.** Known, unknown, ambiguous, insufficient and conflicting are all reportable. `UNKNOWN` is a real validation outcome, not a softened pass. Never invent missing architectural context.

**C05 — Least authority.** Per §2.3.

**C06 — Reversibility.** Every modification must be inspectable, diffable, traceable and reversible. Snapshots automatic, revert available.

**C07 — Traceability preservation.** On creating or modifying anything: what does this trace to, what traces to this, which relationships depend on it, could this invalidate existing traceability, what verification is affected?

**C08 — Human decision authority.** The agent advises; the engineer decides. A recommendation is not a decision. A proposed change is not an approved change. Permission to modify the model is not permission to change architectural intent.

### Keep these five apart

```
MODEL                 What exists?
ARCHITECTURE          How is the system structured?
ARCHITECTURAL INTENT  Why is it structured this way?
ENGINEERING HISTORY   How did we arrive here?
AGENT ACTION          What should happen next?
```

---

## 5. Reusability

Three layers, with a hard boundary between them.

| Layer | Contents | Owner | Lifecycle |
| --- | --- | --- | --- |
| **AGENT** | skills, C01–C08, D1–D9, Arcadia perspective reference, `se-buddy` CLI, schemas, hooks | this repo | versioned, shared, never edited in a project |
| **PROFILE** | model paths, domain pack, viewpoints + priority, principles (the project's standing rules), glossary | the project | authored at init, evolves |
| **MEMORY** | ADRs, proposals, change records, followup checklists, registers, assumptions, confirmed knowledge, baselines | the project | append-mostly |

Every file in §5.2 belongs to exactly one of these rows; a file in neither is a defect in this table or in the layout, never an accepted third thing. "Project rules" and "principles" are the same thing and `principles.yaml` holds them — a rule the project asserts about itself, as against an assumption (unverified, MEMORY) or a viewpoint (a design rule with a priority, PROFILE).

**MUST:** no project name, no domain assumption, and no project-specific rule appears anywhere in the AGENT layer.

This is the boundary most easily lost, and it is lost in small increments rather than all at once. A skill description that names the project, a working rule that names one model element, an example that assumes one domain — each is individually harmless and collectively welds the agent to one repository. §13 checks it first for that reason.

### 5.1 Distribution

**MUST:** the agent installs as a git submodule at a path Claude Code auto-loads.

```bash
git submodule add <se-buddy-agent-url> .claude/skills/se-buddy
```

A directory under a project's `.claude/skills/` containing `.claude-plugin/plugin.json` loads automatically as a **skills-directory plugin** named `se-buddy@skills-dir` — no marketplace, no copying, and no per-project configuration. Skills become `/se-buddy:frame-request` and so on. Hooks, MCP configuration and the CLI travel with the submodule.

Constraints this imposes, all of which **MUST** be documented in the project README that init generates:

| Constraint | Consequence |
| --- | --- |
| Project-scope plugins require accepting the workspace trust dialog | First run in a fresh clone needs one interactive confirmation |
| Project-scope plugins load **only** from the session's primary working directory — they do not walk up to the repo root | Claude Code must be started at the project root, or moved there with `/cd` |
| Background monitors do not load from project scope at all | **Do not design any feature around monitors** |
| MCP servers get per-server approval; LSP starts only after trust | Keep the CLI as `bin/`, not MCP, unless MCP earns its place (§12) |
| `SKILL.md` edits are live; `hooks/`, `.mcp.json`, `agents/` changes are not | After `git submodule update`, run `/reload-plugins` |
| `bin/` is added to the Bash tool's `PATH` while the plugin is enabled | This is how `se-buddy` is reachable; it needs no shell configuration |
| Python dependencies cannot travel by submodule | First run bootstraps a venv — below |

Version pinning is the submodule commit. `git submodule update --remote` is the upgrade, and it is the project's decision when to take it.

#### The dependency bootstrap

capellambse pulls `lxml` and other C-extension packages. Those are wheels, not source a submodule can carry, so the "no install step" ambition cannot survive contact with them. What survives is **no install step the engineer has to perform**.

**MUST:** `bin/se-buddy` is a launcher, not the program. On every invocation it checks for the venv at `vendor/.venv`; if absent or incomplete it creates it, installs capellambse **from the vendored submodule** and its transitive dependencies from the pinned lockfile (§7.1), then execs the real entry point. Installing from `vendor/py-capellambse` rather than from an index is what keeps the submodule commit load-bearing instead of decorative — the pin is then the thing that actually runs, which is what makes `doctor`'s version check meaningful. It also means the clone **MUST** be `--recursive`, per the drift rules in §7.1.

Consequences, all of which **MUST** be in the generated README:

| | |
| --- | --- |
| First invocation in a fresh clone | Slow, and needs network once. Every later invocation is a process spawn |
| The venv is not in git | It is build output. `.gitignore` it; never commit it |
| `se-buddy doctor` | Reports venv presence, completeness and the interpreter version, and **repairs** a broken one rather than only reporting it |
| Python floor | Set by the pin, not by us — v0.8.1 dropped Python 3.10, so **3.11 minimum**. `doctor` checks the running interpreter and refuses below it, naming both versions (§7.1) |
| Offline clone | Fails with one clear message naming the lockfile and the venv path — never a stack trace from an import |

`bin/` also needs a Windows entry point. A shebang script does not execute there, so ship `bin/se-buddy.cmd` alongside the POSIX script, both delegating to `python -m se_buddy`. Windows is a first-class target, not a port (spike 5, §12).

### 5.2 Repository layout

Agent repo (this one), which is also the plugin root:

```
.claude-plugin/plugin.json      name: se-buddy
skills/<name>/SKILL.md          §8
skills/arch-perspective/references/   one file per Arcadia perspective
hooks/hooks.json                write guards: Edit/Write on model files, Bash on write verbs (§10.1)
bin/se-buddy                    launcher — bootstraps the venv, then execs (§5.1)
bin/se-buddy.cmd                the same, for Windows
src/se_buddy/                   §7
templates/                      profile scaffolding written by init
templates/domains/              example domain packs (§5.4)
vendor/py-capellambse/          nested submodule, pinned v0.8.1 (§7.1)
vendor/.venv/                   build output — gitignored, never committed (§5.1)
pyproject.toml                  capellambse==0.8.1
lockfile                        every transitive dependency, pinned (§7.1)
SPEC.md                         this document
SPEC-COVERAGE.md                §13 — written from the first commit
AGENT-LOG.md                    §5.5 — one entry per change that reaches a project
```

Concrete project, after `git submodule add` and `/se-buddy:project-init`:

```
<project>.capella               semantic model — written only via se-buddy write apply
<project>.aird                  diagrams — the engineer's, read-only to tooling
CLAUDE.md                       thin; generated; points at the profile
.claude/skills/se-buddy/        THE SUBMODULE — never edited here
se-buddy/                       PROFILE + MEMORY, all project-owned
  profile.yaml                  model paths, Capella version, domain packs, last-seen AC (§5.5)
  domain.md                     the domain pack (§5.4) — init refuses without it
  viewpoints.yaml               non-functional concerns, design rules, priority order   PROFILE
  principles.yaml               the project's standing rules                            PROFILE
  glossary.yaml                 project vocabulary                                      PROFILE
  assumptions.yaml              unverified, awaiting a CONFIRM                          MEMORY
  knowledge.yaml                CONFIRM and REVIEW answers, with provenance (D8)        MEMORY
  registers/                    §6.2, including not-carried.yaml (§2.2 rule 2)          MEMORY
  decisions/ADR-nnnn.yaml       architecture track
  proposals/CP-nnnn.yaml        modelling track
  changes/CHANGE-nnnn.yaml
  changes/CHANGE-nnnn.followup.yaml    schema-validated; rendered as Markdown on demand
  baselines/<name>.yaml         what the model and registers looked like at a gate (§6.4)
  snapshots/                    pre-apply model copies — pruned once the CHANGE is committed
```

The layer each file belongs to is marked where it is not obvious. `assumptions.yaml` and `knowledge.yaml` are the two halves of one loop: an assumption is what the agent had to invent to proceed, and a `CONFIRM` moves it into `knowledge.yaml` as something citable (C01).

### 5.3 What init demands

`/se-buddy:project-init` **MUST** refuse to report completion until the profile contains:

1. `profile.yaml` — resolvable `.capella` and `.aird` paths, Capella version, project name
2. `domain.md` — the domain pack (§5.4)
3. `viewpoints.yaml` — at least one viewpoint with `design_rules` and a `priority`
4. `principles.yaml` — may be empty, but must exist and be explicitly acknowledged as empty

Until then the agent **MAY** retrieve, explain and reason, and **MUST** state on every architectural judgement that the project style is unrecorded (C02). It **MUST NOT** claim an architecture is sound, or that a viewpoint compromise is proven, against an incomplete profile.

`se-buddy doctor` is the one command that answers "is this installation sound?" It reports, and where it can, repairs:

| Check | Refuses on failure? |
| --- | --- |
| Profile completeness — the four items above | no; reports what is missing as `SUPPLY` asks |
| Model reachability, and whether the model changed outside the agent (§10.2) | no; reports the drift |
| Register and record schema validity | no; names the offending rows |
| The venv: present, complete, and the interpreter at or above the floor (§5.1) | **yes** — and repairs it rather than only reporting |
| Running `capellambse.__version__` against the pin (§7.1) | **yes** |
| Agent changes newer than the last acknowledged `AC-nnnn` (§5.5) | no; reports them with their `action` lines |

The two refusals are the two conditions under which every other answer would be untrustworthy rather than merely incomplete.

### 5.4 Domain packs

The domain is the *only* thing that varies between projects and is *not* derivable from the model. It is supplied by the project, demanded at init, and consumed by `arch-viewpoint` as the project's **baseline viewpoint set**.

`domain.md` **MUST** contain:

| Section | Content |
| --- | --- |
| Applicable standards | the ones this project is actually held to, with the clauses that bite |
| Lifecycle crosswalk | domain lifecycle phases ↔ the five Arcadia perspectives ↔ expected artefacts |
| Baseline viewpoints | the non-functional concerns of this domain, each with **design rules** and a **priority order** — this is what makes it a viewpoint rather than an essay |
| Evidence expectations | what a reviewer, auditor or customer will ask to see, and at which gate |
| Reviewer attack surfaces | known anti-patterns: the mistake, why it is wrong, the correct approach |
| Verification patterns | how claims in this domain are normally verified |

**MUST: everything in `domain.md` is binding as a project requirement.** It is project-supplied, and that is what makes it binding — not whether it happens to coincide with what the domain generally believes. C02 and D5 govern only what the agent brings from *outside* the profile. Without this line `arch-review` has no way to read the attack-surface section: it would either suppress real findings as "generic best practice" (C02) or report every one of them as a D5 defect for treating best practice as a requirement. Both readings are wrong, and both are available.

[`ajhcs/mbse-agents`](https://github.com/ajhcs/mbse-agents) is a good structural reference — its crosswalk tables, numbered attack surfaces, and clause-level standards mapping are the shape wanted, and its aerospace pack maps ARP4754A phases onto OA/SA/LA/PA directly.

Two deliberate departures from that reference, both open to challenge:

- **No persona.** Drop identity, personality traits, experience narrative, communication style and success metrics. A domain pack is **data consumed by `arch-viewpoint`**, not a second agent identity. Two identities in one session is a direct route to the incoherent, over-elaborate deliberation §3 exists to prevent — and a trait like "resistant to compliance theatre" is not checkable by anything.
- **No unverifiable success metrics.** Completion is measured against perspective stop criteria (§2.2) and register state, both of which are queryable.

**SHOULD:** ship two or three reference packs in `templates/domains/` as starting points. They are examples the project copies and edits — never agent-layer content, never active by default.

---

### 5.5 Agent change history

The agent is consumed by several projects, each pinned to a submodule commit (§5.1). Git records what changed in the agent; it does not tell a project whether the change reaches them, or what they must do about it. `AGENT-LOG.md` at the agent repo root carries that, and nothing else.

**MUST:** any change to a **surface** — a skill, a hook, the CLI, a schema, a perspective reference, a template, or a pinned dependency — adds one entry to `AGENT-LOG.md` **in the same commit** as the change. Newest first, append-only, never rewritten.

One entry, five lines:

```
## AC-0007 — 2026-09-14 — arch-viewpoint now requires a priority order
surface   schema, skill
breaking  yes — a viewpoints.yaml without `priority` now fails validation
action    SUPPLY a priority order for each recorded viewpoint, then run se-buddy doctor
why       a viewpoint that cannot decide a boundary cannot justify a component breakdown
```

| Field | Content |
| --- | --- |
| heading | id, date, and the claim in one line (D3) |
| `surface` | which of the seven changed — this is what tells a project whether to read on |
| `breaking` | `no`, or `yes` and what breaks in a project that upgrades |
| `action` | what the project must do, named as a D8 act, or `none` |
| `why` | one line |

**What is not logged:** refactoring with no behavioural change, internal reorganisation, documentation typos, anything invisible from a consuming project. A log that records everything is a second git history and gets read as rarely.

**Where it is read.** `profile.yaml` records the last `AC-nnnn` the project acknowledged. `se-buddy doctor` **MUST** report every entry in the checked-out `AGENT-LOG.md` newer than that, with its `action` line, and offer to acknowledge them. That is the entire point of the file: after `git submodule update --remote`, the engineer sees what reached them and what it asks of them, instead of reading a diff of the agent's source.

The acknowledgement pointer is what makes this work at all. The submodule working tree *is* the pinned commit, so "entries newer than the pin" is empty by construction — the log can only ever describe history up to the commit you are standing on. Comparing against what the project last *read* is a different question, and it is the one that has an answer.

An entry whose change alters whether a requirement is enforced or instructed **MUST** also update `SPEC-COVERAGE.md` (§13) in the same commit.

---

## 6. Engineering memory

Split by **data shape**, not by convenience — narrative records as files (§6.1) and spreadsheet-shaped registers as tabular text (§6.2). Both are YAML in git, and they are the only representation (§6.3).

### 6.1 Narrative records — files

`ADR-nnnn`, `CP-nnnn`, `CHANGE-nnnn` and followup checklists stay as files in git. They are prose, they are history, and C06 reversibility depends on `git diff` working on them.

**MUST:** each cites the one before it and **none copies it**. A record that restates its source is a transcript: everything in it is already available where it came from, and none of it is what a later reader came for.

**Followup checklists are `CHANGE-nnnn.followup.yaml`, not Markdown.** §9 enforces the D8 fields on every checklist line, and a Markdown file cannot be schema-validated without a parser §7.1 says not to write — so the one place items are most likely to be lost would be the one place enforcement was cosmetic. `se-buddy followup` renders them as Markdown on demand; the readable form is generated, not stored.

Size budgets — guidance, per D4:

```
ADR-nnnn      under 4 KB    the decision, not the argument for it
CP-nnnn       under 6 KB    excluding proposed_changes, which is data
CHANGE-nnnn   under 3 KB    counts and citations, no diff, no report
```

**MUST (enforced):** a change record cannot *contain* the diff or the validation report — it stores a one-line summary of each. D7 exemptions apply absolutely.

### 6.2 Registers — tabular text

Genuinely spreadsheet-shaped, and where most cross-cutting queries live:

```
registers/requirements.yaml
registers/stakeholder-expectations.yaml
registers/risks-system.yaml         operational and system risk
registers/risks-project.yaml        schedule, resource, process risk
registers/verification.yaml
registers/not-carried.yaml          elements deliberately left behind at a transition
```

**MUST:** system risk and project risk are separate registers. A project risk that blocks a review meeting and a system risk that drives an architectural decision have different owners, different review cadences and different treatments; merging them means one of the two is always reviewed on the wrong schedule.

**MUST:** registers are writable. `se-buddy write register` is the only route, and `SUPPLY` and `risk-manage` both depend on it — a register the agent can only read cannot support "identify → assess → treat → track → close", which is four-fifths of what `risk-manage` is for.

**`not-carried.yaml`** exists because §2.2 rule 2 names a distinction the model cannot make. One row per source element deliberately not carried forward, citing the perspective pair, the reason, and who decided — so `arch-transition` reports only what has not yet been adjudicated. Rows are `SUPPLY`-able individually; where one rationale covers many elements, an ADR states it once and the rows cite that ADR rather than repeating it (D3).

**Requirements flow both ways.** A requirement may arrive from a customer or be derived from the model after the architecture settles, and neither is the privileged direction — the register is the single representation (§6.3) whichever way a row got there. Every row therefore carries `provenance` naming its origin, because a customer-supplied requirement and one the project derived have different authority to change. ReqIF import is the obvious mechanism for the first direction and is **deferred, not rejected**: name it when a project actually exchanges requirements, and note that capellambse's requirements extension is the least certain part of the pin (spike 3, §12).

Format: one file per register, rows keyed by stable id, YAML. One file per row is the alternative if concurrent editing ever becomes real; it is not, for one engineer, and it costs readability. **OPEN.**

### 6.3 Answering cross-cutting questions

**MUST:** every fact has exactly one representation — a register row, a record, or a model element. A question that spans them is answered by loading them and joining in code.

Joins live inside named commands, not in ad-hoc traversal by the reasoning layer. `se-buddy register`, `se-buddy trace`, `se-buddy followup` and `se-buddy asks` each load what they need — registers through the schema loader, model elements through capellambse — and return rows carrying ids. A question asked twice returns the same shape both times, and every answer is citable as a FACT (C01).

`se-buddy trace <id>` is the cross-cutting one: given any id — an element, a register row, a record — it reports what that id traces to, what traces to it, and what breaks if it changes (C07). Transitive closure is a graph walk over the loaded object graph.

**The model is parsed once per session, not once per command.** A CLI invocation is a fresh process, so "loaded" is a claim about caching, not something a one-shot command gets for free: parse the model, cache the result keyed on the file hash (§10.2), and reuse it until the hash moves. Without this a session of thirty commands parses the model thirty times, and the cost lands on every question the engineer asks. This is also the decisive input to `bin/` versus MCP (spike 6, §12) — an MCP server holds the parse across calls by construction, and `bin/` must earn the same property with a cache.

**MUST: every command bounds its output.** `inspect`, `trace`, `search`, `asks` and `show` all have a default limit and, where they walk a graph, a default depth; `--limit` and `--depth` widen them. **Any truncation is reported** — a silently truncated trace reads as a complete one, and a wrong answer that looks complete is worse than a slow one. This is D6 applied to the tool rather than to the prose: the reason counts beat enumerations is that the reasoning layer's context is the scarce resource, and an unbounded closure spends it faster than any amount of restatement.

### 6.4 Baselines

§5.4 requires the domain pack to say what evidence a reviewer wants **and at which gate**. Nothing else in the agent knows what a gate is, so that requirement would describe something no query could answer.

`se-buddy write baseline <name>` writes `baselines/<name>.yaml`: the model file hash, every register row id with its status, the open ask ids, and the date. It tags git at the same commit. That is the whole feature — a manifest and a tag, no gate model, no readiness engine.

It answers one question that will certainly be asked and cannot be reconstructed later: *what did the model and the registers look like when we passed that review?* Snapshots (§10.2) do not answer it, because they are per-apply and hold the model alone.

## 7. The toolkit

### 7.1 Build on py-capellambse

**MUST:** model access goes through [`py-capellambse`](https://github.com/DSD-DBS/py-capellambse) (Apache-2.0, Deutsche Bahn, headless — no Java, no Capella install). Do not hand-roll XML manipulation: it is where maintenance burden accumulates fastest, it is not differentiating work, and it is the part most likely to break on a Capella version bump.

| Concern | Source |
| --- | --- |
| Load, traverse, query the semantic model | `capellambse` typed object model |
| Apply a change proposal | `capellambse.decl` — declarative YAML apply, with `Promise` / `FindBy` / `UUIDReference` for forward and existing references |
| Diagram inventory from `.aird` | `capellambse` |
| Rendered context diagrams | `capellambse-context-diagrams` (§7.4) |
| Model diff | `capella-diff-tools`, if it fits; otherwise ours |
| Requirements and PVMT viewpoints | `capellambse` extension support |

#### The version is pinned, and the pin is verified

**MUST:** py-capellambse is pinned to **v0.8.1**, vendored as a submodule of the agent repo at `vendor/py-capellambse`, and declared as `capellambse==0.8.1` in `pyproject.toml`. The two **MUST** agree.

**MUST:** `se-buddy doctor` compares the *running* `capellambse.__version__` against the pin and **refuses to run** on a mismatch, naming both versions. This is the check that matters. A pin that is never verified does not prevent a broken agent — it only records what should have been installed, and every other measure here is a way of making the mismatch unlikely rather than impossible.

**Drift, and where it can actually come from.** `git clone --recursive` and `git submodule update --recursive` check out the *recorded* commit, so neither moves the pin. Only `--remote` fetches a branch tip. Therefore:

| | |
| --- | --- |
| `git submodule update --init --recursive` | **safe** — restores v0.8.1 exactly. This is the normal command |
| `git submodule update --remote` on the agent submodule | the project's upgrade of the *agent*, taken deliberately (§5.1) |
| `git submodule update --remote --recursive` | **MUST NOT be run.** It would move py-capellambse to whatever the tracked branch points at |

**MUST:** the agent repo's README states that `--remote` is never combined with `--recursive`, and the pinned version is recorded in `AGENT-LOG.md` at the commit that set it, so the intended version is readable without inspecting submodule metadata.

#### What this particular pin brings with it

A pin is not just a number; it fixes behaviour and a floor. At v0.8.1 specifically:

| | |
| --- | --- |
| **Python 3.11 minimum** | v0.8.1 dropped 3.10. This sets the floor `doctor` enforces (§5.1) — it is imposed by the pin, so moving the pin can move it |
| **`search()` matches types exactly by default** | Changed in v0.8.0. `se-buddy search` is built directly on this, and any recipe written against 0.7.x behaviour is wrong here |
| **Requirements extension is the least certain surface** | Known gaps against Capella 7.0.1. `registers/requirements.yaml` and the `Requirements and PVMT` row above both depend on it — spike 3 tests it first, not last |

None of these is a reason to move the pin. They are the reason the pin is *verified* rather than merely declared: the failure mode is not "we are on an old version", it is "we are on a version whose behaviour we assumed".

**Changing the pin is an authorised, recorded act.** A version bump is a change to the `dependency` surface (§5.5), and:

1. spike 1 and spike 2 of §12 are re-run against the new version — a round-trip that was clean at one version is not evidence about another;
2. the bump is authorised by the engineer, never taken because a newer release exists;
3. an `AGENT-LOG.md` entry records it with `surface: dependency`, `breaking:` stating what changes for a project, and `action:` naming what each project must do;
4. `pyproject.toml` and the submodule commit move in the same commit.

A transitive-dependency lockfile **MUST** accompany the pin. Pinning `capellambse` alone leaves `lxml` and the rest floating, and a C-extension dependency moving underneath is the same failure by another route.

`capellambse.decl`'s YAML is structurally the same thing a `CP-nnnn` already is. **SHOULD:** make `proposed_changes` a `decl` document directly, so the proposal *is* the executable change rather than something translated into one. This removes an entire translation layer and the class of bug that lives in it — a proposal that reviews correctly but applies as something else.

### 7.2 What stays ours

These encode engineering judgement, not Capella mechanics, and no library will provide them:

| Module | Responsibility |
| --- | --- |
| `validate` | six layers of findings, each `PASS` `WARN` `ERROR` `UNKNOWN` with evidence — defined below |
| `perspective` | each Arcadia perspective's expected content and stop criteria; agreement-based criteria `UNKNOWN` until confirmed (§2.2 rule 1); Capella's own root elements discounted so an untouched layer reads as untouched |
| `schemas` | record and register validation, including the mandatory `claim` field (D3), the ask shape and `id` (D8) and the D7 exemptions |
| `trace` | closure over model and registers for one id: what it traces to, what traces to it, what breaks if it changes (C07). Exchanges and `ExchangeItem`s are edges in this graph, not endpoints |
| `memory` | id allocation (records **and** `ASK-nnnn`), citation rendering as `ID (claim)`, ask collection and sequencing (D8, D9), followup tracking |

#### The six validation layers

**MUST:** each layer is separately reportable, and none of them measures completeness. Completeness is `perspective`'s question (§2.2 rule 1), and reading a validation pass as a completeness pass is the failure §13 checks for — which is only checkable if the layers are defined rather than merely listed.

| Layer | Asks | Example finding |
| --- | --- | --- |
| `structural` | is what exists well-formed against the metamodel? | a `LogicalComponent` with no parent package |
| `representation` | do the diagrams still match the semantic model? | an element on a diagram that no longer exists in `.capella` |
| `interface` | do the exchanges hold together? | a `FunctionalExchange` with no `ExchangeItem` allocated |
| `traceability` | do the links required by C07 exist and resolve? | a requirement with no verification row, or a dangling realization |
| `consistency` | does the model agree with the registers and records? | a risk treatment citing a component that was renamed |
| `architectural` | does it obey *this project's* recorded rules? | a boundary that violates a viewpoint design rule in `viewpoints.yaml` |

`architectural` is the layer that needs the profile, and it is the one that reports `UNKNOWN` rather than `PASS` against an incomplete one (§5.3, C02). It answers whether the model breaks a rule the project wrote down. `arch-review` is the *conversation* about whether a rule is the right rule — a different question, at a different tier, producing a different artefact.

`interface` earns its own layer rather than living inside `consistency` because it is where integration defects concentrate and where an engineer is least able to find them by eye. An exchange that carries nothing, a port that connects nothing, an interface no requirement justifies — each is cheap to detect, expensive to discover late, and invisible in any single diagram.

### 7.3 CLI surface

**The surface is split by authority, not by whether bytes reach disk.** Everything the agent may do on its own has a short name. Everything that needs the engineer lives under `se-buddy write`. Names are indicative; the split is not.

This is the shape §2.3's gate requires. A project *will* allowlist the read verbs — they are called constantly and prompting on each is intolerable — so if writing shared a prefix with reading, that allowlist would silently authorise the model write path. One prefix is also all the `Bash` hook has to match, and a hook matching a drifting list of verb names is a hook that stops working quietly.

Automatic authority:

```bash
se-buddy doctor                    # is this installation sound? (§5.3)
se-buddy inspect                   # model + diagrams + memory overview, in counts (D6)
se-buddy search <words>            # elements by name/summary; --kind --layer --limit
se-buddy show <id>                 # one element or record, relationships, diagrams, citations
se-buddy trace <id>                # what it traces to, what traces to it, what breaks (§6.3)
se-buddy memory <domain> [text]    # principles | viewpoints | glossary | assumptions
                                   #   | knowledge | decisions
se-buddy register <name> [filter]  # any register of §6.2, including not-carried
se-buddy perspective [<layer>]     # one Arcadia perspective against its own stop criteria
se-buddy validate                  # six layers of findings with evidence (§7.2)
se-buddy followup                  # manual diagram work still owed, rendered as Markdown
se-buddy asks                      # every open ask, in D8 shape, sequenced, with ASK ids
se-buddy plan CP-nnnn              # dry run: what would change, what must be drawn by hand
se-buddy baseline [<name>]         # read a recorded baseline (§6.4)
se-buddy export <element>          # §7.4
se-buddy write propose draft.yaml  # file a proposal; §2.3 grants this automatically
```

Requires the engineer — every one **TTY-gated** per §2.3:

```bash
se-buddy write memory <domain> d.yaml     # principles, viewpoints, glossary, assumptions,
                                          #   knowledge, decisions (an ADR needs `authority`)
se-buddy write register <name> row.yaml   # the only route into a register
se-buddy write answer ASK-nnnn a.yaml     # close one ask — see below
se-buddy write record draft.yaml          # record work the engineer did by hand in Capella
se-buddy write baseline <name>            # §6.4
se-buddy write apply CP-nnnn --authorized-by "<what the engineer actually said>"
se-buddy write apply CP-nnnn --authorized-by "..." --delete
se-buddy write revert CHANGE-nnnn
```

**`write propose` is the one write with automatic authority,** and the exception is deliberate. §2.3 grants proposing automatically because a proposal asserts nothing about what is *true* or what *will happen* — only about what could be done, which is the agent's job. It lives under `write` because it does create a file and should be visible in the transcript; it is not gated because gating it would put a keystroke between the engineer and every draft.

**`write revert` takes a `CHANGE-nnnn`, not a `CP-nnnn`.** The snapshot is per-apply and the record is the change, so the change is the only id that identifies a reversible event. A proposal is not one — nothing says a `CP` may be applied only once, and `revert CP-nnnn` has no answer if it was applied twice.

**`write answer` is how every D8 act closes.** One verb, because every ask has the same shape (§9) and the answer needs to land wherever that act belongs (§3, D8):

| Ask's `act` | `write answer` does |
| --- | --- |
| `CONFIRM`, `REVIEW` | append a row to `knowledge.yaml` with the ask id and provenance |
| `PRIORITISE` | write `sequence:` onto each ask named |
| `DRAW` | tick the entry in `CHANGE-nnnn.followup.yaml` |
| `DECIDE`, `SUPPLY` | refuse, and name the verb that fits — `write memory` or `write register` |

`DECIDE` and `SUPPLY` are refused rather than absorbed because their products are records with their own schemas, and an ADR filed through a generic answer verb would skip the `authority` requirement that makes it an ADR at all.

Two flags apply across the surface:

| Flag | Effect |
| --- | --- |
| `--tier lookup\|judgement\|decision` | caps output to what that tier can use — a lookup gets counts and ids, a decision gets evidence. D1 makes the agent declare a tier; this is what makes the declaration do work rather than only announce it |
| `--limit` / `--depth` | widen the defaults of §6.3. Truncation is always reported |

**`se-buddy asks` is the session's first command.** The reasoning layer's context does not survive a session (§1.1), so the open asks are what "where were we" means here. It reports the current track, tier and perspective alongside them. Nothing else reconstructs that, and re-deriving it by reading records costs more than the whole rest of the session's retrieval.

### 7.4 Diagram policy — deliberately thin

Traceability is the core need. Diagrams are not, and this section is bounded so they stay that way.

| Capability | In scope |
| --- | --- |
| Read the diagram inventory from `.aird` — which diagrams exist, which elements appear on each | **Yes.** Required for impact analysis and for the followup checklist |
| Write `.aird` | **Never.** Every representation in it was placed by hand; it is the engineer's work |
| Render a context diagram for a document or review pack | **Yes — one command, one skill.** Generated on demand, written to an image file, never stored in `.aird`, never authoritative |
| Synthesise layout, placement, sizing, visual grouping | **No.** Recorded as a deferred option, deliberately not specified here |

The consequence: hand-drawing debt persists under this policy, so the throttle on it persists too (§10.3).

**OPEN.** If generated context diagrams turn out to carry reviews and documents adequately, hand-placed `.aird` could narrow to the diagrams that genuinely need human composition, and the throttle could relax. That is a change to make on evidence once the agent is in real use, never an assumption built in ahead of it.

---

## 8. Skills

Skills are **derived from §2**, not an organizing principle. Invoke by name; `frame-request` routes unless the request is plainly a lookup.

### 8.1 Catalogue

```
shared
  frame-request     what is being asked, which track, which tier (D1)
  retrieve-context  what exists, how it relates, what was decided
  trace-rationale   why it looks like this, and who decided
  write-plain       say it so it cannot be misread; apply the size budgets

architecture track
  arch-perspective  which Arcadia perspective is this, and is it done?
  arch-viewpoint    the non-functional concerns, their design rules and priority
  arch-transition   the handover between two perspectives
  arch-review       is this right, given our principles, ADRs and domain pack?
  arch-decide       settle it; write the ADR
  arch-principles   standing rules, assumptions, constraints, lessons
  risk-manage       identify → assess → treat → track → close, both registers

modelling track
  model-impact      what would this touch, and what must be redrawn?
  model-plan        write the proposal
  model-apply       apply an authorised proposal
  model-validate    is the model well-formed, do the diagrams still match?
  model-record      what was written, and what is still owed
  model-export      render a context diagram into a document (§7.4)

project
  project-init      scaffold and gate the profile (§5.3)
```

Eighteen. Skills are cheap to load and expensive to *route*; the risk is `frame-request` sending work to the wrong one. **SHOULD:** if routing proves unreliable in practice, merge. Do not merge pre-emptively: each separation above exists because the two concerns produce different artefacts or sit at different authority levels — which is also the test for which merge to take first.

By that test the order is:

1. **`trace-rationale` into `retrieve-context`.** They produce the same artefact (none) at the same authority level (read), both answer "what was decided", and both are served by `show` + `trace`. Nothing in the stated test keeps them apart.
2. **`arch-transition` into `arch-perspective`.** Weaker: a transition finding and a completeness finding are genuinely different outputs, so this one costs something.

Recording the order is not permission to take it. Merge on evidence of misrouting, and note in `AGENT-LOG.md` what the evidence was.

**Requirements management is not a skill here.** Requirements are a register (§6.2) and a perspective output; `arch-perspective` and `retrieve-context` cover them. Add a skill only if the register alone proves insufficient in use.

**`write-plain`** applies ASD-STE100 Simplified Technical English — for readers who have no author to ask — plus the §6.1 budgets and D6. Precedence per §3: the epistemic label always wins over the shorter phrasing.

### 8.2 Skill file structure

Each `SKILL.md` **MUST** cover: purpose · when to invoke · inputs · context required · procedure · outputs · commands used · authority constraints · failure handling · interaction with other skills.

**MUST NOT** restate C01–C08 or D1–D9 in prose. Reference them.

**MUST NOT** name a project, a domain, or a specific model element.

### 8.3 Response structure

For substantial reasoning, use these sections, **omitting any that would be empty**: Understanding · Facts · Assumptions · Unknowns · Architectural Context · Analysis · Risks · Benefits · Recommendation · Proposed Change · Traceability · Verification Implications · **Asks**.

**Asks is always last, and always in the D8 shape.** It is the only section the engineer must act on, so nothing else belongs in it and nothing that needs acting on belongs anywhere else.

For `lookup` and most `judgement` work, answer in prose. D1 governs; the full structure is a `decision`-tier instrument and using it lower is a D5 defect.

---

## 9. Schemas

Every record **MUST** carry:

```yaml
id:            # ADR-nnnn | CP-nnnn | CHANGE-nnnn
claim:         # ONE LINE. What this record says. Rendered with every citation (D3)
tier:          # lookup | judgement | decision (D1)
date:
supersedes:    # [] — history is superseded, never rewritten
```

Every open item — an `open_questions` entry, a `still_open` entry, or a followup checklist line — **MUST** carry the D8 fields:

```yaml
id:            # ASK-nnnn — allocated on write, stable for the life of the ask
act:           # DECIDE | AUTHORISE | CONFIRM | REVIEW | DRAW | SUPPLY | PRIORITISE
object:        # one line
done_when:     # one line
blocks:        # one line, or "nothing"
default:       # one line, or "none — this blocks"
sequence:      # integer, or absent — written by a PRIORITISE answer
answered:      # absent while open; on close: date, the answering act, where it landed
```

**Enforced:** an open item missing `act` or `done_when` is rejected. These are the two fields whose absence makes an item unanswerable, and an unanswerable item is indistinguishable from a lost one. `id` is allocated by the CLI, never authored.

`object`, `blocks` and `default` are **required but not enforced** — a schema can see that a line is present, not that it says anything. §3 states all six as MUST; SPEC-COVERAGE records which are which, and this is the clearest case in the spec of the enforced/instructed line falling inside one field list rather than between two.

Beyond that, stated as intent rather than a final field list:

| Record | Must additionally carry | Enforced |
| --- | --- | --- |
| `ADR-nnnn` | question, context, alternatives (one line each), chosen option, rationale, consequences, evidence, **`authority`** | `authority` is required — an ADR cannot be filed as the agent's |
| `CP-nnnn` | intent, facts, assumptions, unknowns, affected elements, `proposed_changes` (§7.1), alternatives, verification implications, open questions, diagram cost, provenance | rejected if facts, alternatives, unknowns, open questions, verification implications or provenance are missing |
| `CHANGE-nnnn` | the proposal cited, `authority` verbatim, one-line diff summary, one-line validation summary, `manual_followup` | cannot contain the diff or the report; `manual_followup` required |
| Register row | id, claim, status, owner, provenance, links to model elements and records | schema per register |
| Viewpoint | `design_rules`, `priority` | rejected without both — a viewpoint that cannot decide a boundary is not a viewpoint |
| Principle / assumption / knowledge | provenance, status | required |
| `knowledge.yaml` row | the `ASK-nnnn` answered, the act (`CONFIRM` or `REVIEW`), the answer, date, provenance | the ask id is required — a fact with no provenance is not citable under C01 |
| `not-carried.yaml` row | source element id, the perspective pair, reason, who decided, or the ADR that decides a batch | reason and decider required — a row without them re-states the unknown it exists to close |
| `baselines/<name>.yaml` | model file hash, register row ids with statuses, open ask ids, date, git tag | written whole by the CLI, never hand-edited |

**Where the diff and the validation report actually live.** Neither is stored. The diff is derivable at any time from the `snapshots/` copy taken before the apply (§10.2), and the validation report is reproducible by re-running `validate` at that commit. This is why §6.1 can forbid storing them without losing them — an implementer reading that prohibition alone would reasonably invent a `diffs/` directory, and that directory is a second representation of something git already holds (§6.3).

---

## 10. Enforcement

Instructions that can be enforced **MUST** be enforced. Keep the distinction between **enforced** (code refuses the wrong behaviour) and **instructed** (a prompt asks for it) visible throughout, and record it per requirement in §13.

### 10.1 Write guards

Two `PreToolUse` hooks ship in the submodule, and both are **MUST**:

| Hook | Blocks |
| --- | --- |
| on `Edit` / `Write` | any write to `.capella` or `.aird` |
| on `Bash` | any invocation matching the `se-buddy write` prefix, except `write propose` (§7.3) |

The first alone is not a guard. It stops the two tools that name a file and leaves every other route open — `cp`, `mv`, `python -c`, a shell redirect — and it says nothing about the CLI, which is the route that actually modifies the model. A guard that covers the paths nobody uses and not the path everybody uses records an intention rather than enforcing one.

Neither hook is the real gate. The TTY confirmation in the CLI is (§2.3), because a hook lives in a file the agent can read, and `/reload-plugins` can leave a stale one in force. The hooks make the attempt visible and stop it early; the TTY check makes it impossible.

If a hook blocks, the answer is to write a proposal, not to find another way in.

### 10.2 Apply lifecycle

```
check tree → check drift → validate targets → snapshot → apply
    → re-parse → validate → diff → record
```

**MUST** leave the model exactly as it was on any failure — before the write by not making it, after the write by restoring the snapshot. "Untouched" means the bytes are unchanged at the end, not that no write was attempted.

Four preconditions, each refusing rather than warning:

| Precondition | Why |
| --- | --- |
| The `.capella` and `.aird` files are **clean in git** | A revert needs a point to return to. Only the model files — refusing on any uncommitted change anywhere would block apply during most real sessions |
| The model hash matches what was last parsed | The engineer works in Capella alongside the agent (§1). If they have edited since, apply would overwrite their work. On mismatch, refuse and name the drift — the answer is `write record`, not a retry |
| Every followup checklist is ticked | §10.3 |
| For `--delete`: no diagram in the `.aird` inventory references the target | Deleting an element that appears on a diagram leaves a dangling representation in a file the agent must never repair (§7.4). Refuse, or emit the affected diagrams as `DRAW` followups and let the engineer decide |

**`apply` does not commit.** It writes the model, the `CHANGE-nnnn` and the followup checklist, and stops. Git history is the engineer's, and an agent that writes it has taken an authority §2.3 never granted. Snapshots are pruned once their `CHANGE` is committed — at that point git holds the prior state and `snapshots/` is a second copy of it, which on a real model is tens of megabytes per change (§6.3).

Deletion requires a distinct flag beyond authorisation.

### 10.3 One pass, one change

**Modelling track only.** A pass produces at most one `CHANGE-nnnn`: one bounded change, answering one engineering question, whose followup checklist the engineer can draw and check in a single Capella session against a single diff.

Every checklist entry is an ask in the D8 shape with `act: DRAW` and its own `ASK-nnnn`, naming the diagram and what makes it done — not a description of the model change that caused it.

`apply` **MUST** refuse while any followup checklist is unticked. Entries are ticked by `se-buddy write answer ASK-nnnn` (§7.3), which is TTY-gated like every other write — the engineer says the drawing is done, and the agent cannot say it for them. Without that verb the rule deadlocks: the second `apply` in a project's life would be unreachable, because nothing could ever clear the first one's checklist.

An override flag exists; the agent **MUST NOT** add it on its own initiative — bring the refusal to the engineer.

This rule exists solely to throttle hand-drawing debt (§7.4). It has nothing to say about architecture work: reasoning and ADRs are not rate-limited by diagram debt. If §7.4's open question resolves, this relaxes with it.

---

## 11. Phasing

Do not implement everything at once. The write path is the tempting place to start and the wrong one: safety machinery is only worth its cost once the reasoning it guards is trusted, and it is the read path that earns that trust.

| Phase | Contents | Gate to the next |
| --- | --- | --- |
| **0 — Bootstrap** | the `bin/` launcher and venv, POSIX and Windows, `doctor`'s venv and version checks (§5.1) | `se-buddy doctor` runs from a fresh recursive clone on both platforms, and repairs a deleted venv |
| **1 — Read and reason** | capellambse loading and the parse cache, `inspect`/`search`/`show`/`trace`/`asks`, behavioural-element retrieval (§2.2), `project-init`, `ASK-nnnn` allocation, shared + architecture skills including `write-plain`, C01–C08, D1–D9 | The agent maintains a useful semantic understanding and produces reasoning the engineer trusts. **No write path exists yet, gated or otherwise.** |
| **2 — Registers and answers** | register schemas, `write register`, `write answer`, the TTY gate, `knowledge.yaml`, `not-carried.yaml`, `risk-manage`, `trace` across model and registers, `write baseline` | Registers answer real questions the model alone could not, and an ask raised in one session is closed in another |
| **3 — Controlled modification** | `write propose` / `plan` / `write apply` / `write record` / `write revert`, `validate`'s six layers, both write guard hooks, modelling skills | Phase 1 reasoning is trusted, and a real change applies and reverts cleanly |
| **4 — Portability proof** | a second project installed from scratch by submodule + init | **The real acceptance test.** Nothing project-specific leaked into the agent layer |

Phase 4 is not optional polish. Reuse is the point, and it is unproven until a second project runs on the same submodule without editing it.

---

## 12. Verify before implementing

**OPEN — these are spikes, not assumptions. Run them first; each can change the spec.**

1. **capellambse round-trip.** Load a real `.capella` (Capella 7.0.1), save unchanged, diff the XML. If the round-trip is dirty, §7.1 changes and §7.2 grows substantially. *Everything downstream depends on this one.*
2. **`decl.apply()` against a real proposal.** Replay a known change and compare the resulting model against the expected state, element by element. Confirms §7.1's "the proposal *is* the change".
3. **Ontology coverage.** capellambse claims "most of the present Capella ontology", and "most" is the load-bearing word. Establish what is *not* covered for the element kinds actually in use. Test in this order, hardest-known first: the **requirements extension** (there are known gaps against Capella 7.0.1, and `registers/requirements.yaml` depends on it); **functional chains at Physical architecture**; then **exchanges and `ExchangeItem`s**, which the `interface` validation layer needs (§7.2); then behavioural elements — scenarios, mode/state machines — which §2.2 requires the agent to retrieve.
4. **`.aird` read fidelity.** Confirm the diagram inventory needed by `model-impact`, the followup checklist, and the `--delete` reference check (§10.2) is retrievable.
5. **Submodule install, end to end.** Fresh project, `git submodule add` into `.claude/skills/se-buddy`, trust dialog, `/reload-plugins`, invoke a skill, fire both hooks. **On Windows and on POSIX**, with `bin/se-buddy.cmd` as a named deliverable rather than a portability afterthought — a shebang script does not execute on Windows, and that is the development platform.
6. **CLI as `bin/` vs MCP server.** Measure **cold parse time on a representative model** before arguing the merits: a working session issues tens of commands, so the real quantity is parse cost × calls per session. An MCP server holds the parse across calls by construction; `bin/` must earn the same property with the hash-keyed cache of §6.3, and if that cache is hard the comparison changes. Simplicity and per-server approval are the tie-breakers, not the criteria.
7. **Diagram generation quality.** Does a generated context diagram actually carry a review? Answers §7.4's open question and gates §10.3.
8. **The TTY gate, end to end.** Confirm the write verbs refuse without a TTY under the permission modes and allowlists a project will really use, and that the `Bash` hook matches `se-buddy write` without catching `write propose` (§10.1). This is the spike for §2.3, and §2.3 is the spec's spine.

**Resolved since first draft — verify, do not re-open.** How Python dependencies reach a fresh clone was open and blocking. It is decided: the `bin/` launcher builds and repairs a venv, installing capellambse from the vendored submodule and its transitive dependencies from the lockfile (§5.1). Phase 0 exists to prove it on both platforms.

Also open, and for the engineer rather than a spike:

- Register file granularity (§6.2)
- Whether behavioural elements ever earn validation rather than retrieval alone (§2.2)
- Whether one agent installation should ever serve several models in one repo, given that project-scope plugins load only from the primary working directory (§5.1)

---

## 13. Reviewing an implementation against this spec

**MUST:** `SPEC-COVERAGE.md` is written alongside the implementation, from the first commit. Written afterwards it becomes archaeology; written alongside, it is what makes review possible at all. For each requirement it states:

- where it lives
- **enforced** (code refuses the wrong behaviour) or **instructed** (a prompt asks for it)
- if instructed, whether it *could* be enforced and why it is not

The review questions, in priority order:

1. Does any project name, domain assumption or model element appear in the agent layer? (§5)
2. Is a flat skill list the primary structure? (§2)
3. Can an architectural decision be recorded without a human `authority`? (§2.3)
4. Does any citation render without its claim? (D3)
5. Does a change record contain a diff or a validation report? (§6.1)
6. Is structural validation read anywhere as perspective completeness? (§2.2)
7. Is there a second representation of the registers or the model anywhere? (§6.3)
8. **Can the agent apply a change without a human keystroke?** Try it: allowlist the CLI in `.claude/settings.json` and invoke `write apply` from Bash. The guards hold only if this fails. (§2.3, §10.1)
9. Can an ask be produced without `act` or `done_when`, or without an `ASK-nnnn`? (D8, §9)
10. Did a surface change land without an `AGENT-LOG.md` entry in the same commit? (§5.5)
11. Does `doctor` refuse to run when the installed capellambse is not the pinned version, or the interpreter is below the floor? (§7.1, §5.1)
12. Did a second project install and run without editing the submodule? (§11, phase 4)
13. Does every D8 act have somewhere its answer is written, and a verb that writes it? (§3, §7.3)
14. Does any command return an unbounded result set, or truncate without saying so? (§6.3)
15. Does `apply` detect that the model changed outside the agent, and refuse? (§10.2)
16. Is any file in the project layout in neither the PROFILE nor the MEMORY row? (§5)

Question 8 is the one to run first and the one most likely to pass on inspection and fail in fact. Every other guard in this spec assumes it holds.

---

## 14. The objective

The objective is not:

> Build an AI that can edit Capella.

The objective is:

> **Build a reusable AI collaborator that maintains a useful understanding of an evolving system architecture, reasons about proposed changes within that architecture's own design intent, preserves the reasoning and traceability behind engineering decisions — and does all of it in a form a human engineer can check without effort.**

Capella manipulation is an implementation capability. The product is the **engineering reasoning layer around the model**, and the reasoning must be legible, not merely correct.
