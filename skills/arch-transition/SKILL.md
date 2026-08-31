---
name: arch-transition
description: The handover between two Arcadia perspectives - what's new, what's realized, what was deliberately left behind, and what's simply missing.
---

# arch-transition

## Purpose

Check the handoff between two adjacent perspectives specifically (spec
Sec.2.2 rule 2): every source element is realized, refined, deliberately
not carried, or missing - and the model alone cannot distinguish the last
two. This is a narrower question than `arch-perspective`'s "is this
perspective done" (spec Sec.8.1 names this pair a weaker future-merge
candidate than `retrieve-context`/`trace-rationale` - "a transition finding
and a completeness finding are genuinely different outputs").

## When to invoke

"What didn't make it from SA into LA", "did we lose anything going from
logical to physical", or any question framed as a handoff between two
named perspectives rather than one perspective's own completeness.

## Inputs

The two adjacent perspectives in question (e.g. `sa` -> `la`).

## Context required

Both perspectives' elements (`se-buddy search --layer <each>`),
`registers/not-carried.yaml` (Phase 2+ for writing; until it exists,
nothing has been adjudicated yet, so treat every source element as
unadjudicated rather than assuming silent omission is fine).

## Procedure

1. Enumerate the source perspective's elements that should transition
   (spec Sec.2.2's crosswalk in `se-buddy/domain.md` names what's expected
   at each gate).
2. For each, check: realized in the target perspective, refined (present
   but changed), cited in `not-carried.yaml` with a reason and decider, or
   genuinely missing.
3. **Subtract `not-carried.yaml` before reporting** (rule 2) - a row there
   closes that element's gap; without the register (Phase 1: it doesn't
   exist to write to yet), report every non-transitioned element as
   unadjudicated, and say plainly that the register isn't available yet
   rather than treating the absence as "nothing was left behind on
   purpose."
4. Check the converse too: does the target perspective add anything the
   source never had? A target that traces upward one-for-one has been
   transcribed, not engineered (spec Sec.2.2) - that's a finding in its
   own right, not a pass.

## Outputs

Counts (D6): N realized, N refined, N cited as not-carried, N
unadjudicated - with the unadjudicated list itself exempt from brevity
(D7) since it's open work.

## Commands used

`se-buddy search --layer`, `se-buddy trace`, `se-buddy register
not-carried` (Phase 2+).

## Authority constraints

Read-only; automatic authority (C05). Deciding that an element should be
deliberately not carried is a `SUPPLY` act landing in
`not-carried.yaml` (naming the perspective pair, reason, and decider) -
this skill reports the gap, it does not close it unilaterally.

## Failure handling

Never let an unadjudicated element resurface silently pass-by-pass without
being named - that's exactly the "work that can never be finished" failure
mode spec Sec.2.2 warns the register exists to prevent.

## Interaction with other skills

`arch-perspective` calls this for its own rule-2 check at each perspective
boundary. `risk-manage` may pick up an unadjudicated element as a system
risk if it represents a real capability gap, not just a documentation gap.
