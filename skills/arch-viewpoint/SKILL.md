---
name: arch-viewpoint
description: The non-functional concerns bearing on a boundary decision, their design rules, and their priority order.
---

# arch-viewpoint

## Purpose

Surface the non-functional concerns (safety, weight, maintainability,
cost, ...) that justify a component boundary, with each concern's design
rules and its priority relative to the others (spec Sec.2.2 rule 3: "an
architecture is chosen, not derived"). This is the evidence
`arch-perspective` checks for at LA/PA, and the reasoning `arch-review`
checks a proposed boundary against.

## When to invoke

"Why is this grouped this way", "what design rules apply here", or before
proposing any component boundary at LA/PA.

## Inputs

The component or boundary in question, or a request for the project's
whole baseline viewpoint set.

## Context required

`se-buddy/viewpoints.yaml` (the project's recorded viewpoints, PROFILE
layer - readable once `project-init` + `write memory` have populated it,
Phase 2+) and `se-buddy/domain.md`'s "Baseline viewpoints" section (spec
Sec.5.4 - the domain's starting set, which a project copies and edits).

## Procedure

1. Read `se-buddy/viewpoints.yaml`. If empty or missing, say so plainly
   (C02: "with no principles recorded, say the style is unknown" applies
   to viewpoints identically) - do not fall back to inventing a plausible
   viewpoint from `domain.md` alone; the domain pack is a starting point a
   project must actually adopt (Sec.5.4), not a default this skill assumes
   silently.
2. For a specific boundary question, name which recorded viewpoints bear
   on it and in what priority order.
3. Where two viewpoints conflict on the same boundary (e.g. safety wants
   segregation, cost wants consolidation), the recorded priority order
   decides - state which viewpoint won and why, citing its priority
   number, not just its name.
4. If no viewpoint is recorded yet, this is a `SUPPLY` ask (D8) naming the
   specific missing viewpoint, not a generic "profile is incomplete"
   restatement.

## Outputs

A named list of applicable viewpoints, each with its design rule and
priority, and - for a specific boundary - which one is decisive and why.

## Commands used

`se-buddy memory viewpoints` (Phase 2+, once `write memory` exists to
populate it - until then, read `se-buddy/viewpoints.yaml` directly as
scaffolded by `project-init`).

## Authority constraints

Read-only; automatic authority (C05). Recording a *new* viewpoint is
`SUPPLY` (D8), landing in `viewpoints.yaml` via `write memory` - TTY-gated,
Phase 2+. This skill surfaces what's missing; it does not invent content
to fill the gap.

## Failure handling

Never present a viewpoint as the project's own when it was only ever an
unadopted line in a `templates/domains/*.md` example (spec Sec.5.4: "never
active by default"). C02 governs the distinction sharply here.

## Interaction with other skills

Feeds `arch-perspective` (rule 3's evidence) and `arch-review` (checking a
proposed boundary against the recorded priority order). `arch-decide`
calls this when an ADR needs to state which viewpoint the decision serves.
