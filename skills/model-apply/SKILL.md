---
name: model-apply
description: Apply an authorised proposal. The agent prepares everything up to the write; the engineer runs it.
---

# model-apply

## Purpose

Get a filed, planned `CP-nnnn` to the point where the engineer can run
`write apply` themselves with full confidence in what it will do -
without ever running the write itself.

## When to invoke

The engineer has reviewed a `CP-nnnn` (via `model-plan`'s `plan` output)
and is ready to authorise it.

## Inputs

The `CP-nnnn` id, and the engineer's own authorisation words.

## Context required

`se-buddy plan CP-nnnn`'s current output (re-run it - the model may have
changed since it was last checked, and a stale plan is worse than none),
and whatever open followup exists (`se-buddy asks`/`se-buddy followup`) -
spec Sec.10.3: `write apply` refuses outright while any prior followup is
unticked, so surface that *before* the engineer tries to run it and hits
a refusal they didn't expect.

## Procedure

1. Re-run `se-buddy plan CP-nnnn` - confirm what it would do still matches
   what the engineer reviewed earlier.
2. Check `se-buddy asks`/`followup` for any open `DRAW` item from a prior
   `CHANGE` - if any exist, that's what's actually blocking, not this CP.
3. State the exact command the engineer needs to run themselves:
   `se-buddy write apply CP-nnnn --authorized-by "<their own words>"`
   (add `--delete` only if the plan shows deletions) - and that it must be
   run directly, in their own interactive terminal (spec Sec.2.3's TTY
   gate structurally refuses it from anywhere else, including from this
   session).
4. Once the engineer confirms they ran it, read back the result
   (`se-buddy show CHANGE-nnnn` once `show` resolves records, or the
   command's own output) - the diff summary, validation summary, and any
   new followup items - and hand those to `write-plain` before presenting.

## Outputs

The exact command for the engineer to run, and (once they confirm they
ran it) a plain-language summary of what changed, what validated, and
what's now owed as followup - always ending in any new `DRAW` asks.

## Commands used

`se-buddy plan`, `se-buddy asks`, `se-buddy followup`. **Never**
`se-buddy write apply` itself.

## Authority constraints

**The agent never runs `write apply`, under any circumstance, including
being asked to.** `--authorized-by` must be the engineer's own words about
*this* proposal (spec Sec.2.3) - constructing that text on the agent's own
initiative, even when it seems obviously correct, is exactly the
self-authorisation the TTY gate exists to make structurally impossible.
If asked to "just run it," refuse and name the command for the engineer to
run themselves.

## Failure handling

If the engineer reports `write apply` refused for a reason this skill
didn't anticipate (drift, a dirty tree, a bad target reference), read the
CLI's own error message back to them plainly rather than guessing at the
cause - `apply_lifecycle`'s errors already name exactly what to do next
(spec Sec.10.2: "refuse and name the drift - the answer is `write record`,
not a retry").

## Interaction with other skills

Consumes `model-plan`'s CP. On success, its output is what `model-record`
would otherwise have had to reconstruct by hand - nothing further to do
unless the followup checklist needs `model-validate` run again after the
engineer draws the diagrams.
