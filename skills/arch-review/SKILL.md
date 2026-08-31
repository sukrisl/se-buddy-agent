---
name: arch-review
description: Is this right, given our principles, ADRs and domain pack? Distinguishes a real finding from generic best practice, and ceremony from a lookup.
---

# arch-review

## Purpose

Judge whether an architectural choice holds up against *this project's*
recorded rules - principles, ADRs, viewpoints, and the domain pack's
reviewer attack surfaces (spec Sec.5.4: everything in `domain.md` is
binding once a project adopts it). Distinct from `arch-viewpoint` (surfaces
the concerns) and `arch-decide` (settles a new question) - this skill
reviews something that already exists or has been proposed.

## When to invoke

"Is this right", "does this hold up", "review this component/boundary/
decision" - always at `judgement` or `decision` tier (D1), never `lookup`.

## Inputs

The element, boundary, or proposal under review.

## Context required

`se-buddy/principles.yaml`, `se-buddy/viewpoints.yaml`, existing ADRs
(Phase 2+ for records; Phase 1 reviews against principles/viewpoints only,
stating plainly that no ADR history exists yet), and `se-buddy/domain.md`'s
"Reviewer attack surfaces" section.

## Procedure

1. **C02 first**: know the project's style before judging. If
   `principles.yaml`/`viewpoints.yaml` are empty, state that the style is
   unrecorded (spec Sec.5.3: never claim soundness against an incomplete
   profile) - this caps every finding that follows at a lower confidence,
   not a blocker to reviewing at all.
2. Check the finding against two, and only two, sources of "wrong":
   - **project-specific**: contradicts a recorded principle, ADR, or
     viewpoint priority - a real finding.
   - **domain-specific**: matches a named attack surface in
     `se-buddy/domain.md` - binding once the project has adopted that
     domain pack (Sec.5.4), a real finding.
3. Explicitly reject a third category: "different from generic best
   practice" with no project or domain source cited. C02: usually
   irrelevant, and reporting it anyway is symmetric with D5's manufactured
   ceremony - `arch-review` reports both failure directions.
4. **D5 applies to the review itself, not just to what it's reviewing**: if
   the answer is fully determined by an existing ADR/principle/model fact,
   say so as a lookup, not a decision-tier review with invented
   alternatives.
5. Use `arch-transition`/`arch-perspective` findings as inputs where the
   review concerns a boundary or a perspective handoff, rather than
   re-deriving them.

## Outputs

Full Sec.8.3 structure at `decision` tier (only sections that aren't
empty); prose at `judgement` tier. Every finding labelled per C01 and
sourced to project-specific or domain-specific, never bare.

## Commands used

`se-buddy memory principles`, `se-buddy memory viewpoints`, `se-buddy show`,
`se-buddy trace`.

## Authority constraints

A review produces a finding or a recommendation, never a decision (C08) -
even a review that concludes "this is wrong" ends in an `ASK` (D8: likely
`REVIEW` back to the engineer, or `DECIDE` if it turns out to be an
architectural question, not a lookup).

## Failure handling

Two failures are symmetric and both reportable (D5): treating generic best
practice as a project requirement, and manufacturing decision-tier ceremony
for something a lookup would answer. Report either when it happens,
including when *this skill* is the one about to do it.

## Interaction with other skills

Reads from `arch-viewpoint`, `arch-perspective`, `arch-transition`,
`retrieve-context`/`trace-rationale`. Escalates to `arch-decide` when a
review finding turns out to require settling a genuine architectural
question rather than citing an existing one.
