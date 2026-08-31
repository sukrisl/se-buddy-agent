---
name: arch-decide
description: Settle an architectural question between stated options, and produce the ADR that records it. Full procedure is spec-complete; recording is not yet wired up (see Authority constraints).
---

# arch-decide

## Purpose

Bring an architecture-track question (spec Sec.2.1: "what *should* the
architecture be") to a decision, structured so the engineer can settle it
in one read, and produce the `ADR-nnnn` that preserves the reasoning
(spec Sec.6.1).

## When to invoke

`frame-request` routes here once a question is confirmed architecture-track
and genuinely undetermined by existing ADRs/principles/model facts (D5's
converse: if it's already determined, it's a lookup, not this skill).

## Inputs

The architectural question, and (from `retrieve-context`/`arch-review`/
`arch-viewpoint`) the facts and viewpoint context bearing on it.

## Context required

Existing ADRs (to check `supersedes`), recorded viewpoints and principles,
and the model facts the decision turns on.

## Procedure

1. Declare tier `decision` (D1) - this skill only runs at that tier.
2. State the question in one line.
3. **D2: two live alternatives.** Name at most two live options; anything
   else gets one line stating why it's not live. Surveying the option
   space is not the job - getting the engineer to a decision is.
4. For each live option, state the viewpoint(s) it serves and at what
   priority (via `arch-viewpoint`), the consequences, and the evidence
   (functional chains/scenarios demonstrating the claim, per spec Sec.2.2).
5. Recommend one option, plainly, with the reasoning that would let the
   engineer disagree productively.
6. Draft the ADR body per spec Sec.9's required fields: question, context,
   alternatives (one line each), chosen option, rationale, consequences,
   evidence, and `authority` - left blank, since only the engineer's own
   words fill it (spec Sec.2.3: "`--authorized-by`... only words the
   engineer actually said").
7. End with a single `DECIDE` ask (D8) naming the two live options as
   `done when`.

## Outputs

The Sec.8.3 structure at `decision` tier, ending in the `DECIDE` ask. The
drafted ADR body, ready for the engineer's decision.

## Commands used

`se-buddy memory viewpoints`, `se-buddy memory decisions` (to check
`supersedes`), `se-buddy show`, `se-buddy trace`.

## Authority constraints

**An architectural decision is never the agent's (C08, spec Sec.2.3): a
human `DECIDE`s.** Filing the resulting record is `se-buddy write memory
decisions <file>` (spec Sec.7.3), which is TTY-gated and requires the
`authority` field - and that write path does not exist yet in this
installed phase (it arrives with Phase 2's TTY gate). Until then: draft
the ADR body in full as described above, present it directly in
conversation, and tell the engineer plainly that formal recording is
pending - do not claim the ADR has been filed, and do not skip drafting it
just because filing isn't automated yet. The reasoning is exactly as
useful to the engineer either way; only the persistence step is missing.

## Failure handling

If the "decision" turns out to be fully determined already (D5's
converse), stop and say so instead of manufacturing two options where only
one is real.

## Interaction with other skills

Consumes `arch-viewpoint` (option evidence), `arch-review`,
`arch-perspective`'s findings. `write-plain` tightens the final draft
before presenting it. Once Phase 2 lands, `write memory` becomes the
literal next step after this skill's output - nothing about the procedure
above changes, only whether the ADR gets persisted.
