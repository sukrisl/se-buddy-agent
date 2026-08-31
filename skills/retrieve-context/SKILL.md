---
name: retrieve-context
description: What exists and how it relates - grounding an answer in the model and memory before reasoning about it.
---

# retrieve-context

## Purpose

Answer "what exists, how does it relate" by loading the model and whatever
memory exists - never by recalling or assuming.

Spec Sec.8.1 names this skill and `trace-rationale` as the strongest
candidate for a future merge (same artefact - none - at the same authority
level - read). They stay separate skills for now: "recording the order is
not permission to take it." Merge only on evidence of real misrouting, and
note that evidence in `AGENT-LOG.md`.

## When to invoke

Any question whose answer is "look it up" and does not turn on *why* it
looks that way - for the "why", see `trace-rationale`.

## Inputs

An element id, a record id, or a name/kind/layer to search on.

## Context required

Whatever the model and memory currently contain - retrieved fresh each
time (spec Sec.6.3: the model is parsed once per invocation, never assumed
from a prior turn).

## Procedure

1. If the object is named or its id is known: `se-buddy show <id>`.
2. If it needs finding first: `se-buddy search <words> [--kind] [--layer]`,
   then `show` on the result(s) that matter.
3. For "what does this affect / what would break": `se-buddy trace <id>`.
4. Label every retrieved fact **FACT** (C01) and cite it by source id.
   Anything not directly retrieved is the agent's own inference and must be
   labelled as one.

## Outputs

Prose for a `lookup`/`judgement` tier (D1); retrieval alone rarely
escalates to `decision` tier.

## Commands used

`se-buddy show`, `se-buddy search`, `se-buddy trace`.

## Authority constraints

Read-only; automatic authority (C05). Retrieving and citing is never
itself a proposal or a decision (C08).

## Failure handling

- `show`/`search`/`trace` truncate and report it (spec Sec.6.3) - carry
  that reporting into the response; a truncated result presented as
  complete is worse than one that admits it's partial.
- If the model can't be loaded or the profile is missing, say so plainly
  (C04: `UNKNOWN` is a real, reportable outcome).

## Interaction with other skills

Feeds every other skill - `arch-review`, `arch-perspective` and
`arch-decide` all retrieve context before judging it. For "why was this
decided", use `trace-rationale` instead; this skill does not resolve
rationale.
