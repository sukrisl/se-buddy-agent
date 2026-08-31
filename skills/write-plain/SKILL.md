---
name: write-plain
description: Say it so it cannot be misread - Simplified Technical English, the Sec.6.1 size budgets, and D6, applied to whatever another skill produced.
---

# write-plain

## Purpose

Make a response legible to a reader who has no author to ask. Applies
ASD-STE100 Simplified Technical English discipline, plus spec Sec.6.1's
record size budgets and D6's "counts, not enumerations" - to whatever
another skill has already drafted, not as a skill invoked for its own
sake.

## When to invoke

Before finalising any `judgement`- or `decision`-tier response, and before
any record (ADR/CP/CHANGE) is drafted for the engineer to review - even
though nothing writes those records yet in this phase, the same clarity
pass applies to what gets shown in conversation now.

## Inputs

A draft response or record body from another skill.

## Context required

None beyond the draft itself.

## Procedure

1. Short sentences, one idea each. Active voice. No noun-stacking.
2. Apply the Sec.6.1 size budgets as a target even where nothing is being
   written to disk yet: `ADR-nnnn` under 4 KB (the decision, not the
   argument for it), `CP-nnnn` under 6 KB excluding `proposed_changes`,
   `CHANGE-nnnn` under 3 KB (counts and citations, no diff, no report).
3. Apply D6: replace an enumeration with a count wherever the count alone
   answers the question (`85 SystemFunction elements in 11 capability
   groups`, never 85 names).
4. Apply D3: every citation carries its claim, rendered `ID (claim)`.
5. **Precedence, and it is absolute (spec Sec.3):** where brevity would
   hide an epistemic label (C01), a hedge, or an uncertainty statement, the
   label and the hedge win. A short answer that hides uncertainty is a
   worse failure than a long one that doesn't.
6. **D7 is exempt from all of the above.** `still_open` items, followup
   checklists, unknowns and open asks are never shortened - brevity applies
   to restatement, never to outstanding work.

## Outputs

The same content, tightened - never new content, and never a shortened
version of an open item.

## Commands used

None. This is a prose/formatting pass, not a retrieval step.

## Authority constraints

None beyond whatever authority the underlying content already carries -
this skill changes phrasing, never claims, facts, or authorisation.

## Failure handling

If applying the size budget or D6 would require dropping a label, a hedge,
or an open item to fit, stop shortening - the content wins, per the
precedence rule above. Report the response is longer than the guidance
size rather than silently dropping something load-bearing.

## Interaction with other skills

Runs last, over whatever `arch-review`, `arch-decide`, `arch-perspective`
or any other skill has produced. Never runs before D1's tier has been
declared - the tier is what determines how much structure (spec Sec.8.3)
this pass is tightening in the first place.
