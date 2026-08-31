---
name: model-plan
description: Write the proposal - a CP-nnnn whose proposed_changes is a real capellambse.decl document, filed with automatic authority.
---

# model-plan

## Purpose

Turn a bounded, impact-assessed change into a filed `CP-nnnn` (spec
Sec.6.1, Sec.9): the full record, with `proposed_changes` written as an
actual `capellambse.decl` YAML document (spec Sec.7.1's SHOULD - "the
proposal *is* the executable change"), not a prose description of one.

## When to invoke

After `model-impact` has bounded what a change touches, or directly when
the change is small and obvious enough that impact analysis is a lookup
(D5).

## Inputs

The bounded change (from `model-impact`, or directly known), and the
target element(s)' real uuids (`!uuid` references need them exactly).

## Context required

`model-impact`'s findings, the target elements' real uuids and current
state (`show`), and any citable viewpoint/principle the change serves
(`arch-viewpoint`) - a CP's `facts` and `alternatives` fields should cite
these, not restate them (D3).

## Procedure

1. Declare tier (D1) - usually `judgement`, `decision` only if the change
   itself required settling an architectural question first (in which
   case that's `arch-decide`'s job, done *before* this skill runs).
2. Draft the decl document. Reference existing elements with `!uuid
   <real-uuid>` (never a fabricated one - `write propose`/`plan`/`write
   apply` all resolve these against the live model and fail loudly on a
   bad one, spec Sec.10.2's "validate targets" step). Chain new elements
   together with `!promise <id>`/`promise_id:` where one new element
   references another that doesn't have a uuid yet.
3. Fill every Sec.9 CP field: `intent`, `facts`, `assumptions`,
   `unknowns`, `affected_elements` (from `model-impact`), the decl
   document as `proposed_changes`, `alternatives`, `verification_
   implications`, `open_questions`, `diagram_cost`, `provenance`.
   `facts`/`alternatives`/`unknowns`/`open_questions`/`verification_
   implications`/`provenance` are enforced (spec Sec.9) - an empty
   `unknowns`/`open_questions` list is a real, complete answer ("nothing
   outstanding"), not a placeholder to fill with noise.
4. File it: `se-buddy write propose draft.yaml --model <path>` -
   **automatic authority, not TTY-gated** (spec Sec.7.3: "a proposal
   asserts what *could* be done, not what is true"). This is the one
   modelling-track write the agent runs itself.
5. Immediately follow with `se-buddy plan CP-nnnn` (`model-plan`'s own
   sibling command, not a separate skill) to show the engineer what it
   would actually do before they consider authorising it.

## Outputs

The filed `CP-nnnn`, plus the `plan` dry-run output (what would be
created/deleted, what would need drawing) - always ending in an
`AUTHORISE` ask (D8) naming the CP and what `write apply` would need.

## Commands used

`se-buddy write propose` (automatic authority), `se-buddy plan`,
`se-buddy show` (to get real uuids right).

## Authority constraints

Filing the CP is automatic (C05, spec Sec.7.3's explicit carve-out).
**Applying it is not** - that is `write apply --authorized-by`, TTY-gated,
and this skill never runs it. The `AUTHORISE` ask this skill ends on is
exactly what hands that decision to the engineer.

## Failure handling

If `se-buddy plan` reports the decl document doesn't resolve against the
current model (a bad `!uuid`, a target that's moved or been deleted since
`model-impact` looked), fix the draft and re-propose - don't try to patch
around it by loosening a `!find` criterion into something that might match
the wrong element.

## Interaction with other skills

Consumes `model-impact`. `arch-viewpoint`/`arch-decide` supply the
reasoning a CP's `facts`/`alternatives` cite. Hands off to the engineer's
own `write apply` (no skill runs it - see `model-apply` below for what the
agent *can* do around that boundary).
