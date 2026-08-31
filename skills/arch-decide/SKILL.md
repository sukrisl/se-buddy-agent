---
name: arch-decide
description: Settle an architectural question between stated options, and file the ADR that records it.
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
decisions <file>` (spec Sec.7.3), TTY-gated and enforcing the `authority`
field - **the agent never runs this itself.** It drafts the ADR body in
full (everything except `authority`, which only the engineer's own words
can fill - spec Sec.2.3), and the engineer runs the write, interactively,
in their own terminal, once they've actually decided. Never present an ADR
as filed until the engineer confirms they ran it - filing an ADR is
allocating a permanent `ADR-nnnn` and writing a file that is never
rewritten, only superseded (spec Sec.6.1), so there is no "undo" if this
runs ahead of a real decision.

## Failure handling

If the "decision" turns out to be fully determined already (D5's
converse), stop and say so instead of manufacturing two options where only
one is real. If `write memory decisions` refuses because the drafted body
is missing a required field beyond `authority`, that's the ADR draft
itself being incomplete (spec Sec.9) - fix the draft, don't strip the
field to get past validation.

## Interaction with other skills

Consumes `arch-viewpoint` (option evidence), `arch-review`,
`arch-perspective`'s findings. `write-plain` tightens the final draft
before presenting it. `write memory decisions` is the literal next step
after this skill's output.
