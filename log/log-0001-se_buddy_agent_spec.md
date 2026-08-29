# SE Buddy — Agent Specification

**Status:** draft for review. Not implemented.
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

**MUST.** There is no LLM loop, no tool dispatcher, no prompt directory, no provider credential, and no network dependency in this agent.

The reason is structural rather than economic. The engineering conversation already happens in Claude Code; a second reasoning loop underneath it duplicates that conversation somewhere the engineer can neither see nor steer. What is needed below the conversation is a deterministic layer that parses, queries, validates and records — and nothing that reasons.

The architecture is therefore fixed at three parties:

| | |
| --- | --- |
| **Claude Code** | the reasoning layer — retrieve, analyse, review, propose, explain |
| **`se-buddy` CLI** | the deterministic layer — parse, index, query, validate, apply, record |
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

1. **Completeness is measured against stop criteria.** Each perspective declares what must exist and what question must be answered before work moves on, and assessing that is its own query (§7.2) — separate from structural validation, which checks that whatever exists is well-formed and is silent on whether enough of it exists. A perspective can satisfy every structural check and still be empty of the content its question needs. Criteria that stop on *agreement* always report `UNKNOWN`, because no tool can observe agreement.
2. **A transition is engineering, not a copy.** Every source element is realized, refined, *deliberately not carried*, or missing — and the model cannot distinguish the last two. Each new level must also **add** what the previous one never had. A layer that traces upward one-for-one has been transcribed, not engineered.
3. **An architecture is chosen, not derived.** Components are formed by grouping or segregating functions according to viewpoint design rules with a declared priority order (§5.4). With no viewpoint recorded, say a compromise cannot be proven rather than inventing a plausible set.

Iteration between perspectives is expected — Arcadia's dependency links are not a time ordering. Doing it silently is not: name the perspective being reached back into.

### 2.3 Axis 3 — Authority

Authority is asymmetric and **MUST** be enforced, not merely instructed, wherever enforcement is possible.

| Action | Authority | Enforcement |
| --- | --- | --- |
| Read model, memory, registers | automatic | — |
| Retrieve, analyse, review | automatic | — |
| Propose a change | automatic | — |
| Write registers / memory | ask first | schema validation |
| Modify the model | explicit authorisation naming a specific proposal | `PreToolUse` hook + CLI |
| Delete model elements | the above, plus a distinct flag | CLI |
| Make an architectural decision | **never the agent's** | `authority` field required on every ADR |

`--authorized-by` is not a formality: its text becomes the `authority` field of the change record. Only words the engineer actually said, about *this* proposal. Interest, agreement, and "that looks right" are not authorisation.

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

**D6 — Counts, not enumerations.** `85 SystemFunction elements in 11 capability groups`, never 85 names. **Tooled:** the index (§6.3) makes this a `GROUP BY` rather than an in-context enumeration, which is both cheaper and correct.

**D7 — Brevity never applies to open work.** `still_open` items, followup checklists, unknowns and open questions are **absolutely exempt**. They are the only fields that are actionable later, and an item lost there is work lost. Brevity applies to restatement, never to outstanding work.

**D8 — Name the act being asked for.** Every request to the engineer states which act it wants, from a closed vocabulary. An engineer who cannot tell a decision from an authorisation from a confirmation cannot tell what kind of answer to give, or how long it should take.

| Act | What the engineer does | Produces |
| --- | --- | --- |
| `DECIDE` | settle an architectural question between stated options | `ADR-nnnn` |
| `AUTHORISE` | approve one named proposal for application | the `--authorized-by` text |
| `CONFIRM` | say whether a stated fact is true | a FACT the agent may then cite |
| `REVIEW` | judge whether something the agent produced stands | acceptance, or a correction |
| `DRAW` | do manual work in Capella | a ticked followup item |
| `SUPPLY` | provide profile or register content that does not exist yet | a viewpoint, principle, requirement or risk |
| `PRIORITISE` | choose the order of work that all needs doing | a sequence |

Each ask carries these five fields, **one line each**:

```
act          one of the above
object       what specifically — an id, an element, or the question itself
done when    what makes this answered; for DECIDE, the options
blocks       what cannot proceed until it is answered, or "nothing"
default      what the agent assumes if it is not answered, or "none — this blocks"
```

`default` is not politeness. It is what lets the engineer defer safely, and a default the agent then acts on **MUST** be recorded as an ASSUMPTION (C01), never absorbed silently.

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
| **PROFILE** | model paths, domain pack, viewpoints + priority, principles, project rules, glossary | the project | authored at init, evolves |
| **MEMORY** | ADRs, proposals, change records, registers | the project | append-mostly |

**MUST:** no project name, no domain assumption, and no project-specific rule appears anywhere in the AGENT layer.

This is the boundary most easily lost, and it is lost in small increments rather than all at once. A skill description that names the project, a working rule that names one model element, an example that assumes one domain — each is individually harmless and collectively welds the agent to one repository. §13 checks it first for that reason.

### 5.1 Distribution

**MUST:** the agent installs as a git submodule at a path Claude Code auto-loads.

```bash
git submodule add <se-buddy-agent-url> .claude/skills/se-buddy
```

A directory under a project's `.claude/skills/` containing `.claude-plugin/plugin.json` loads automatically as a **skills-directory plugin** named `se-buddy@skills-dir` — no marketplace, no install step, no copying. Skills become `/se-buddy:frame-request` and so on. Hooks, MCP configuration and the CLI travel with the submodule.

Constraints this imposes, all of which **MUST** be documented in the project README that init generates:

| Constraint | Consequence |
| --- | --- |
| Project-scope plugins require accepting the workspace trust dialog | First run in a fresh clone needs one interactive confirmation |
| Project-scope plugins load **only** from the session's primary working directory — they do not walk up to the repo root | Claude Code must be started at the project root, or moved there with `/cd` |
| Background monitors do not load from project scope at all | **Do not design any feature around monitors** |
| MCP servers get per-server approval; LSP starts only after trust | Keep the CLI as `bin/`, not MCP, unless MCP earns its place (§12) |
| `SKILL.md` edits are live; `hooks/`, `.mcp.json`, `agents/` changes are not | After `git submodule update`, run `/reload-plugins` |

Version pinning is the submodule commit. `git submodule update --remote` is the upgrade, and it is the project's decision when to take it.

### 5.2 Repository layout

Agent repo (this one), which is also the plugin root:

```
.claude-plugin/plugin.json      name: se-buddy
skills/<name>/SKILL.md          §8
skills/arch-perspective/references/   one file per Arcadia perspective
hooks/hooks.json                model-file write guard (§10.1)
bin/                            se-buddy CLI entry point
src/se_buddy/                   §7
templates/                      profile scaffolding written by init
templates/domains/              example domain packs (§5.4)
SPEC.md                         this document
SPEC-COVERAGE.md                §13 — written from the first commit
```

Concrete project, after `git submodule add` and `/se-buddy:project-init`:

```
<project>.capella               semantic model — written only via se-buddy apply
<project>.aird                  diagrams — the engineer's, read-only to tooling
CLAUDE.md                       thin; generated; points at the profile
.claude/skills/se-buddy/        THE SUBMODULE — never edited here
se-buddy/                       PROFILE + MEMORY, all project-owned
  profile.yaml                  model paths, Capella version, active domain packs
  domain.md                     the domain pack (§5.4) — init refuses without it
  viewpoints.yaml               non-functional concerns, design rules, priority order
  principles.yaml               standing rules
  assumptions.yaml  knowledge.yaml  glossary.yaml
  registers/                    §6.2
  decisions/ADR-nnnn.yaml       architecture track
  proposals/CP-nnnn.yaml        modelling track
  changes/CHANGE-nnnn.yaml
  changes/CHANGE-nnnn.followup.md
  snapshots/                    pre-apply model copies
  index.db                      DERIVED, gitignored (§6.3)
```

### 5.3 What init demands

`/se-buddy:project-init` **MUST** refuse to report completion until the profile contains:

1. `profile.yaml` — resolvable `.capella` and `.aird` paths, Capella version, project name
2. `domain.md` — the domain pack (§5.4)
3. `viewpoints.yaml` — at least one viewpoint with `design_rules` and a `priority`
4. `principles.yaml` — may be empty, but must exist and be explicitly acknowledged as empty

Until then the agent **MAY** retrieve, explain and reason, and **MUST** state on every architectural judgement that the project style is unrecorded (C02). It **MUST NOT** claim an architecture is sound, or that a viewpoint compromise is proven, against an incomplete profile.

`se-buddy doctor` reports profile completeness, model reachability, index freshness and submodule version.

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

[`ajhcs/mbse-agents`](https://github.com/ajhcs/mbse-agents) is a good structural reference — its crosswalk tables, numbered attack surfaces, and clause-level standards mapping are the shape wanted, and its aerospace pack maps ARP4754A phases onto OA/SA/LA/PA directly.

Two deliberate departures from that reference, both open to challenge:

- **No persona.** Drop identity, personality traits, experience narrative, communication style and success metrics. A domain pack is **data consumed by `arch-viewpoint`**, not a second agent identity. Two identities in one session is a direct route to the incoherent, over-elaborate deliberation §3 exists to prevent — and a trait like "resistant to compliance theatre" is not checkable by anything.
- **No unverifiable success metrics.** Completion is measured against perspective stop criteria (§2.2) and register state, both of which are queryable.

**SHOULD:** ship two or three reference packs in `templates/domains/` as starting points. They are examples the project copies and edits — never agent-layer content, never active by default.

---

## 6. Engineering memory

Split by **data shape**, not by convenience.

### 6.1 Narrative records — files

`ADR-nnnn`, `CP-nnnn`, `CHANGE-nnnn` and followup checklists stay as text files in git. They are prose, they are history, and C06 reversibility depends on `git diff` working on them.

**MUST:** each cites the one before it and **none copies it**. A change record that restates the proposal and pastes the diff and the validation report is a transcript rather than a record: everything in it is already available at its source, and none of it is what a later reader came for.

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
```

**MUST:** system risk and project risk are separate registers. A project risk that blocks a review meeting and a system risk that drives an architectural decision have different owners, different review cadences and different treatments; merging them means one of the two is always reviewed on the wrong schedule.

Format: one file per register, rows keyed by stable id, YAML. One file per row is the alternative if concurrent editing ever becomes real; it is not, for one engineer, and it costs readability. **OPEN.**

### 6.3 The index — derived SQLite

**MUST:** `index.db` is a **derived artefact**. It is gitignored, rebuilt from files and the Capella model by `se-buddy index`, and is never a source of truth. A binary in git gives unresolvable merge conflicts and destroys diff review on exactly the records that most need reviewing.

It holds: model elements and relationships (loaded via capellambse), every register row, and record *metadata* — id, claim, dates, authority, links — but never record bodies.

The prize is a single join across model and registers that neither Capella nor a directory of YAML can answer:

> which unmitigated system risks touch Logical Architecture components that realize an unverified requirement?

It also makes D6 real: counts become `GROUP BY` rather than an in-context enumeration.

`se-buddy doctor` **MUST** report index staleness against source file mtimes, and every query result **SHOULD** carry the index timestamp so a stale answer is visible rather than silent.

---

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

`capellambse.decl`'s YAML is structurally the same thing a `CP-nnnn` already is. **SHOULD:** make `proposed_changes` a `decl` document directly, so the proposal *is* the executable change rather than something translated into one. This removes an entire translation layer and the class of bug that lives in it — a proposal that reviews correctly but applies as something else.

### 7.2 What stays ours

These encode engineering judgement, not Capella mechanics, and no library will provide them:

| Module | Responsibility |
| --- | --- |
| `validate` | structural / representation / architectural / traceability / consistency findings, each `PASS` `WARN` `ERROR` `UNKNOWN` with evidence |
| `perspective` | each Arcadia perspective's expected content and stop criteria; agreement-based criteria always `UNKNOWN`; Capella's own root elements discounted so an untouched layer reads as untouched |
| `schemas` | record and register validation, including the mandatory `claim` field (D3), the ask shape (D8) and the D7 exemptions |
| `index` | §6.3 |
| `memory` | id allocation, citation rendering as `ID (claim)`, ask collection and sequencing (D8, D9), followup tracking |

### 7.3 CLI surface

Read-only unless marked. Names are indicative, not binding.

```bash
se-buddy doctor                    # profile completeness, model reachability, index freshness
se-buddy index                     # rebuild index.db from files + model
se-buddy inspect                   # model + diagrams + memory overview
se-buddy search <words>            # elements by name/summary; --kind --layer --limit
se-buddy show <id>                 # one element or record, relationships, diagrams, citations
se-buddy query "<sql>"             # the join of §6.3
se-buddy memory <domain> [text]    # principles | decisions | assumptions | viewpoints | knowledge
se-buddy register <name> [filter]  # requirements | stakeholder-expectations | risks-* | verification
se-buddy perspective [<layer>]     # one Arcadia perspective against its own stop criteria
se-buddy validate                  # five layers of findings with evidence
se-buddy followup                  # manual diagram work still owed
se-buddy asks                      # every open ask across records, in D8 shape, sequenced
se-buddy propose draft.yaml        # file a proposal; never touches the model
se-buddy plan CP-nnnn              # dry run: what would change, what must be drawn by hand
se-buddy record draft.yaml         # record work the engineer did by hand in Capella
se-buddy remember <domain> d.yaml  # WRITES MEMORY — ask first (C08)
se-buddy export <element>          # §7.4
```

Modification, and the only route to it:

```bash
se-buddy apply CP-nnnn --authorized-by "<what the engineer actually said>"
se-buddy apply CP-nnnn --authorized-by "..." --delete
se-buddy revert CP-nnnn
```

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

Eighteen. Skills are cheap to load and expensive to *route*; the risk is `frame-request` sending work to the wrong one. **SHOULD:** if routing proves unreliable in practice, merge — starting with `arch-transition` into `arch-perspective`. Do not merge pre-emptively: each separation above exists because the two concerns produce different artefacts or sit at different authority levels.

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
act:           # DECIDE | AUTHORISE | CONFIRM | REVIEW | DRAW | SUPPLY | PRIORITISE
object:        # one line
done_when:     # one line
blocks:        # one line, or "nothing"
default:       # one line, or "none — this blocks"
```

**Enforced:** an open item missing `act` or `done_when` is rejected. These are the two fields whose absence makes an item unanswerable, and an unanswerable item is indistinguishable from a lost one.

Beyond that, stated as intent rather than a final field list:

| Record | Must additionally carry | Enforced |
| --- | --- | --- |
| `ADR-nnnn` | question, context, alternatives (one line each), chosen option, rationale, consequences, evidence, **`authority`** | `authority` is required — an ADR cannot be filed as the agent's |
| `CP-nnnn` | intent, facts, assumptions, unknowns, affected elements, `proposed_changes` (§7.1), alternatives, verification implications, open questions, diagram cost, provenance | rejected if facts, alternatives, unknowns, open questions, verification implications or provenance are missing |
| `CHANGE-nnnn` | the proposal cited, `authority` verbatim, one-line diff summary, one-line validation summary, `manual_followup` | cannot contain the diff or the report; `manual_followup` required |
| Register row | id, claim, status, owner, links to model elements and records | schema per register |
| Viewpoint | `design_rules`, `priority` | rejected without both — a viewpoint that cannot decide a boundary is not a viewpoint |
| Principle / assumption / knowledge | provenance, status | required |

---

## 10. Enforcement

Instructions that can be enforced **MUST** be enforced. Keep the distinction between **enforced** (code refuses the wrong behaviour) and **instructed** (a prompt asks for it) visible throughout, and record it per requirement in §13.

### 10.1 Model file guard

A `PreToolUse` hook shipped in the submodule **MUST** block `Edit`/`Write` against `.capella` and `.aird`. Model changes go through `se-buddy apply`, which snapshots, validates, diffs and records. If the hook blocks, the answer is to write a proposal, not to find another way in.

### 10.2 Apply lifecycle

```
validate targets → snapshot → apply → re-parse → validate → diff → record
```

**MUST** abort leaving the file untouched on any failure. Deletion requires a distinct flag beyond authorisation.

### 10.3 One pass, one change

**Modelling track only.** A pass produces at most one `CHANGE-nnnn`: one bounded change, answering one engineering question, whose followup checklist the engineer can draw and check in a single Capella session against a single diff.

Every checklist entry is an ask in the D8 shape with `act: DRAW`, naming the diagram and what makes it done — not a description of the model change that caused it.

`apply` **MUST** refuse while any followup checklist is unticked. An override flag exists; the agent **MUST NOT** add it on its own initiative — bring the refusal to the engineer.

This rule exists solely to throttle hand-drawing debt (§7.4). It has nothing to say about architecture work: reasoning and ADRs are not rate-limited by diagram debt. If §7.4's open question resolves, this relaxes with it.

---

## 11. Phasing

Do not implement everything at once. The write path is the tempting place to start and the wrong one: safety machinery is only worth its cost once the reasoning it guards is trusted, and it is the read path that earns that trust.

| Phase | Contents | Gate to the next |
| --- | --- | --- |
| **1 — Read and reason** | capellambse loading, index, `doctor`, `inspect`/`search`/`show`/`query`, `project-init`, shared + architecture skills, C01–C08, D1–D9 | The agent maintains a useful semantic understanding and produces reasoning the engineer trusts. **No model write access exists yet.** |
| **2 — Registers** | register schemas, `risk-manage`, the model-and-register join, `write-plain` | Registers answer real questions the model alone could not |
| **3 — Controlled modification** | `propose` / `plan` / `apply` / `validate` / `record` / `revert`, the write guard hook, modelling skills | Phase 1 reasoning is trusted, and a real change applies and reverts cleanly |
| **4 — Portability proof** | a second project installed from scratch by submodule + init | **The real acceptance test.** Nothing project-specific leaked into the agent layer |

Phase 4 is not optional polish. Reuse is the point, and it is unproven until a second project runs on the same submodule without editing it.

---

## 12. Verify before implementing

**OPEN — these are spikes, not assumptions. Run them first; each can change the spec.**

1. **capellambse round-trip.** Load a real `.capella` (Capella 7.0.1), save unchanged, diff the XML. If the round-trip is dirty, §7.1 changes and §7.2 grows substantially. *Everything downstream depends on this one.*
2. **`decl.apply()` against a real proposal.** Replay a known change and compare the resulting model against the expected state, element by element. Confirms §7.1's "the proposal *is* the change".
3. **Ontology coverage.** capellambse claims "most of the present Capella ontology". Establish what is *not* covered for the element kinds actually in use, and whether any gap blocks a real change.
4. **`.aird` read fidelity.** Confirm the diagram inventory needed by `model-impact` and the followup checklist is retrievable.
5. **Submodule install, end to end.** Fresh project, `git submodule add` into `.claude/skills/se-buddy`, trust dialog, `/reload-plugins`, invoke a skill, fire a hook. Confirm on Windows specifically.
6. **CLI as `bin/` vs MCP server.** `bin/` is simpler and avoids per-server approval; MCP gives structured results. Decide on evidence, not preference.
7. **Diagram generation quality.** Does a generated context diagram actually carry a review? Answers §7.4's open question and gates §10.3.

Also open, and for the engineer rather than a spike:

- Register file granularity (§6.2)
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
7. Is `index.db` in git, or treated as a source of truth? (§6.3)
8. Does the write guard hold against `Edit` / `Write` on model files? (§10.1)
9. Can an ask be produced without `act` or `done_when`? (D8, §9)
10. Did a second project install and run without editing the submodule? (§11, phase 4)

---

## 14. The objective

The objective is not:

> Build an AI that can edit Capella.

The objective is:

> **Build a reusable AI collaborator that maintains a useful understanding of an evolving system architecture, reasons about proposed changes within that architecture's own design intent, preserves the reasoning and traceability behind engineering decisions — and does all of it in a form a human engineer can check without effort.**

Capella manipulation is an implementation capability. The product is the **engineering reasoning layer around the model**, and the reasoning must be legible, not merely correct.
