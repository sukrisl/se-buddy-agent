---
name: model-record
description: What was written, and what is still owed - records manual Capella work as a CHANGE, or reads back what write apply already recorded.
---

# model-record

## Purpose

Cover both directions of "what was written": reading back a `CHANGE-nnnn`
that `write apply` already produced, and helping the engineer record work
they did *manually* in Capella, outside the agent entirely (`write
record` - spec Sec.7.3).

## When to invoke

After the engineer reports doing manual Capella work not covered by any
CP/apply cycle, or when asked what a specific `CHANGE-nnnn` actually did.

## Inputs

For reading: a `CHANGE-nnnn` id. For recording manual work: a description
of what the engineer did, and (if it matches a proposal they implemented
by hand instead of through `write apply`) the `CP-nnnn` it corresponds to.

## Context required

`se-buddy validate`'s current output (this skill runs it fresh against
whatever state the model is actually in - `write record` computes
`validation_summary` for real, against the model as it currently stands,
not a stale prior read).

## Procedure

**Reading a CHANGE:**
1. `se-buddy followup` for its checklist status; the `CHANGE-nnnn.yaml`
   record itself for `diff_summary`/`validation_summary`/`authority`.
2. Report plainly, citing the record id (D3).

**Recording manual work:**
1. Run `se-buddy validate` against the model as it now stands - this
   becomes the CHANGE's real `validation_summary`.
2. Draft the record: `claim`, `authority` (the engineer's own words - this
   is still gated the same as every other write, spec Sec.2.3, even
   though there's no `--authorized-by` flag on `write record` itself),
   `diff_summary` (the engineer's own description of what changed - there
   is no automatic diff to compute here, since se-buddy never saw a
   "before" state it controlled), `proposal` (a `CP-nnnn` if this
   implements one, blank if not), `manual_followup` (what's still owed -
   an empty list is a real, complete answer, not a placeholder).
3. Hand the draft to the engineer to run themselves: `se-buddy write
   record draft.yaml`.
4. **No snapshot exists for a `write record`-created CHANGE** - `write
   revert` has nothing to restore to and refuses cleanly if asked. Say
   this plainly if the engineer later asks about reverting manual work;
   it is not a limitation to route around, it is the honest answer (the
   model was never under se-buddy's control for this change in the first
   place).

## Outputs

Either a plain read-back of an existing `CHANGE`, or a drafted record
ready for the engineer to file via `write record`.

## Commands used

`se-buddy followup`, `se-buddy validate`, `se-buddy write record`
(drafted by the agent, run by the engineer).

## Authority constraints

The agent never runs `write record` itself - same TTY-gate boundary as
every other write verb (spec Sec.2.3). Reading back an existing `CHANGE`
is automatic authority (C05).

## Failure handling

Never fabricate a `diff_summary` from guesswork about what the engineer
probably did - ask them directly, and if they can't describe it precisely
enough, that's a D9-shaped problem ("bound the ask") before it's a
recording problem.

## Interaction with other skills

Consumes `model-validate`'s fresh read. May cite a `CP-nnnn` from
`model-plan` if the manual work implements an existing proposal by hand
instead of through `model-apply`.
