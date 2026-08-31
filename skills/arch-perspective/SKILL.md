---
name: arch-perspective
description: Which Arcadia perspective is this, and is it done? Reports against each perspective's own stop criteria, not a generic completeness score.
---

# arch-perspective

## Purpose

Answer "which Arcadia perspective is this work in, and has it reached that
perspective's own stop criterion" (spec Sec.2.2). Completeness is measured
against what a perspective's question needs, never against structural
validation - a perspective can pass every structural check and still be
empty of the content its question requires.

## When to invoke

"Are we done with operational analysis", "what's missing from the logical
architecture", or any question about progress through OA -> SA -> LA -> PA
-> EPBS.

## Inputs

A layer name (`oa`/`sa`/`la`/`pa`/`epbs`) or enough context to infer one.

## Context required

The model (via `se-buddy inspect`/`search`), the relevant
`skills/arch-perspective/references/*.md` file for that perspective's
question and stop criterion, and `knowledge.yaml` for any `CONFIRM`ed
agreement facts (once records exist - Phase 2+; until then, agreement-based
criteria report `UNKNOWN`, not `PASS`, per rule 1 below).

## Procedure

1. Load the reference for the perspective in question:
   `references/operational-analysis.md`, `system-analysis.md`,
   `logical-architecture.md`, `physical-architecture.md`, or
   `epbs-architecture.md`.
2. **Rule 1 (agreement-based criteria are UNKNOWN until confirmed).**
   OperationalAnalysis and EPBSArchitecture stop on *agreement* - a tool
   cannot observe agreement, only that a human recorded it. Report
   `UNKNOWN` unless a `CONFIRM` answer exists in `knowledge.yaml`. This is
   not a workaround; it is the correct answer until that record exists.
3. **Rule 2 (a transition is engineering, not a copy).** When checking
   whether this perspective adds what the previous one lacked, subtract
   `registers/not-carried.yaml` before reporting what's "still missing" -
   an element deliberately left behind is not an open gap. (Registers
   arrive in Phase 2; until then, report every source element as
   unadjudicated rather than silently assuming intent.)
4. **Rule 3 (an architecture is chosen, not derived).** For LA/PA, check
   that component groupings cite a viewpoint and its priority
   (`se-buddy memory viewpoints`, once `write memory` exists - Phase 2).
   With none recorded, say a compromise cannot be proven; never invent a
   plausible-sounding one.
5. Retrieve behavioural elements (functional chains, scenarios, state
   machines) as evidence for rule 3's viewpoint claims - read and cite
   them (spec Sec.2.2), never validate their completeness or
   well-formedness; that determination is deferred pending spike 3 of
   spec Sec.12.
6. Report per-perspective: what exists (counts, D6), what the stop
   criterion needs, and whether it's met, `UNKNOWN`, or open.

## Outputs

One block per perspective checked: question, current counts, stop
criterion, verdict (met / `UNKNOWN` / open with asks).

## Commands used

`se-buddy inspect`, `se-buddy search --layer <layer>`, `se-buddy show`,
`se-buddy register not-carried` (Phase 2+), `se-buddy memory viewpoints`
(Phase 2+).

## Authority constraints

Read-only; automatic authority (C05). Reporting a stop criterion as met or
`UNKNOWN` is not a decision - only the engineer's `CONFIRM` makes an
agreement-based criterion citable as fact (rule 1).

## Failure handling

Never report `PASS` on an agreement-based criterion without a `CONFIRM`
record, and never treat structural well-formedness as evidence of
completeness (spec Sec.7.2: these are different, separately-reportable
layers).

## Interaction with other skills

`arch-transition` covers the handoff *between* two perspectives
specifically (spec Sec.8.1 names it a weaker future-merge candidate into
this skill - "a transition finding and a completeness finding are
genuinely different outputs"). `arch-viewpoint` supplies the design-rule
evidence rule 3 needs. `retrieve-context` supplies the raw counts.
