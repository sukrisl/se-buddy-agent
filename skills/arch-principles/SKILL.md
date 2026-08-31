---
name: arch-principles
description: Standing rules, assumptions, constraints, and lessons - what the project asserts about itself, distinct from an ADR (one decision) or a viewpoint (a design rule with a priority).
---

# arch-principles

## Purpose

Surface, and help the engineer supply, the project's standing rules
(`principles.yaml`), and track what the agent has had to assume in their
absence (`assumptions.yaml`). Spec Sec.5.2: "'project rules' and
'principles' are the same thing... as against an assumption (unverified,
MEMORY) or a viewpoint (a design rule with a priority, PROFILE)" - keeping
these three apart is this skill's whole job.

## When to invoke

"What are our standing rules", "is this assumption ever going to get
confirmed", or whenever another skill (most often `arch-review`) needs to
know whether something is a settled principle or still an open assumption.

## Inputs

None specific - either a direct question about principles, or an implicit
call from another skill checking project style.

## Context required

`se-buddy/principles.yaml` (may be empty, must exist and explicitly
acknowledge that - spec Sec.5.3) and `se-buddy/assumptions.yaml`/
`knowledge.yaml`.

## Procedure

1. Read `principles.yaml`. If empty (even though it exists), say plainly
   that no standing rules are recorded yet (C02) - this is a real,
   different state from the file not existing at all, and both are
   distinct from "principles exist but don't cover this case."
2. When another skill needs an assumption because a principle doesn't
   cover the case at hand: label it **ASSUMPTION** (C01), state what would
   turn it into a fact (a `CONFIRM`), and note it as a `SUPPLY`/`CONFIRM`
   ask rather than silently treating the assumption as settled for the
   rest of the response.
3. Never record an assumption *as* a principle. An assumption is
   unverified and MEMORY-layer; a principle is the project's own
   standing, asserted rule and PROFILE-layer. Conflating them is exactly
   the boundary-loss spec Sec.5 warns is "lost in small increments."

## Outputs

The current principle set (or its explicit absence), and/or a labelled
assumption with its path to becoming a fact.

## Commands used

`se-buddy memory principles`, `se-buddy memory assumptions`,
`se-buddy write memory principles`/`write memory assumptions` (drafted by
the agent, run by the engineer - spec Sec.2.3).

## Authority constraints

Read-only; automatic authority (C05). Recording a new principle or
assumption is `SUPPLY`: the agent drafts the row
(`statement`/`provenance`/`status`) and the engineer runs `write memory
principles`/`write memory assumptions` themselves, interactively - the
agent never runs it. Recording that the agent *had* to make an assumption
in the first place (the C01 labelling itself, in conversation) is
automatic; only *persisting* it to `assumptions.yaml` is gated. Promoting
an assumption to a confirmed fact is the engineer's `CONFIRM` (via
`write answer`), not this skill's to grant itself.

## Failure handling

An assumption the agent acts on and never surfaces is a silently-absorbed
default (spec Sec.3: "a default the agent then acts on MUST be recorded as
an ASSUMPTION, never absorbed silently"). If this skill is invoked and
finds the caller has already proceeded on an unlabelled assumption, flag
it rather than let it pass.

## Interaction with other skills

Feeds `arch-review` (C02's style-awareness check) and `arch-decide` (an
ADR's context section may cite a principle, never restate one already on
record).
