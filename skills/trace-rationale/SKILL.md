---
name: trace-rationale
description: Why it looks like this, and who decided - resolving an element or a choice back to the record and citation that explains it.
---

# trace-rationale

## Purpose

Answer "why does this look like this, and who decided" by resolving back
to the record (ADR/CP/CHANGE) that explains a choice, not by inferring a
reason from the model's current shape.

Spec Sec.8.1 names this skill and `retrieve-context` as the strongest
future-merge candidate. Kept separate for now, on purpose - merge only on
evidence of real misrouting between them.

## When to invoke

"Why was this built this way", "who decided this", "does a decision exist
for X" - any question about intent or history, not current state.

## Inputs

An element id, or a description of the choice being questioned.

## Context required

Whatever decision/proposal/change records exist. In a project with no
records yet (nothing has reached the write path, e.g. a fresh Phase-1-only
installation), the honest answer is "no decision record exists for this" -
never a plausible-sounding guess constructed from the model shape (C01: an
inference is not a fact, and a guess presented without that label is worse
than admitting the record doesn't exist).

## Procedure

1. Resolve the element via `se-buddy show <id>` and check its citations.
2. If a citing record exists, follow it and render every reference in
   `ID (claim)` form (D3) - never a bare id, and never restate the full
   record when a one-line claim will do.
3. If no record exists, distinguish two cases and say which:
   - the model predates any recorded decision (a real, reportable gap -
     C04), or
   - this was never actually decided, just built - which is itself a
     finding worth surfacing, not silently backfilled with an invented
     rationale.
4. Do not synthesise a plausible-sounding "why" from the model's structure
   alone. Structure is a FACT; the reason for the structure is not
   inferable from the structure itself.

## Outputs

Prose, `lookup` or `judgement` tier. Cite every record found; state
plainly when none exists.

## Commands used

`se-buddy show`, `se-buddy trace`.

## Authority constraints

Read-only; automatic authority (C05).

## Failure handling

An `UNKNOWN` rationale is a valid, complete answer (C04) - do not let D4's
"one screen" pressure turn "no record exists" into a fabricated one-liner
that sounds like a citation but isn't.

## Interaction with other skills

Called from `frame-request` when the request is plainly about history
rather than current state. `arch-review` calls this when checking whether
a finding contradicts an existing decision, not just current model shape.
