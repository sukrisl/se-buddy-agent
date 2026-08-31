---
name: model-impact
description: What would this change touch, and what must be redrawn? The modelling-track counterpart to arch-transition - impact analysis before a proposal is even drafted.
---

# model-impact

## Purpose

Before drafting a CP, establish what a candidate change would actually
touch: which model elements, which registers cite them, which diagrams
would need manual redrawing (spec Sec.7.4 - `.aird` is the engineer's,
never written by tooling). This is what `model-plan` drafts *from*, not a
substitute for it.

## When to invoke

`frame-request` routes here once a request is confirmed modelling-track
(spec Sec.2.1: "how is a settled architecture expressed in Capella") and
before a `CP-nnnn` exists - if a CP already exists, `se-buddy plan CP-nnnn`
answers this same question directly against the actual proposed content.

## Inputs

The element(s) or boundary the change concerns.

## Context required

The model (`show`/`trace`), and every register row that cites the
affected elements (`trace <id>` already reports these in both directions).

## Procedure

1. Resolve the target element(s): `se-buddy show <id>`.
2. Trace what depends on them: `se-buddy trace <id>` - reports outgoing
   references, incoming references, and citing register rows in one call
   (spec Sec.11: "trace across model and registers").
3. Check `.diagrams`/`visible_on_diagrams` (surfaced by `show`/`trace`
   directly) for what would need manual redrawing - this is the
   "diagram cost" a later CP's `diagram_cost` field states.
4. If anything traced back would be *deleted*, check whether it still
   appears on a diagram - `write apply --delete` refuses outright if so
   (spec Sec.10.2); flag this now rather than let the proposal discover
   it at apply time.
5. Summarise: what's affected (counts, D6), what's cited by registers,
   what diagram work this implies.

## Outputs

A bounded impact summary - affected element count, citing register rows,
diagram redraw estimate - feeding directly into `model-plan`'s CP draft
(`affected_elements`, `diagram_cost`).

## Commands used

`se-buddy show`, `se-buddy trace`, `se-buddy register`.

## Authority constraints

Read-only; automatic authority (C05).

## Failure handling

If impact can't be bounded (the change touches an unclear or very large
set of elements), say so rather than estimating - D9 applies to a `CP`'s
`affected_elements` the same way it applies to any other ask: an
unboundable change is not ready to be proposed yet.

## Interaction with other skills

Feeds `model-plan`. Reuses `arch-transition`'s register-subtraction logic
in spirit (not-carried elements aren't "impact," they're already
adjudicated) without duplicating its perspective-pair framing.
