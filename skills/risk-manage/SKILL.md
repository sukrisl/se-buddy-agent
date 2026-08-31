---
name: risk-manage
description: Identify, assess, treat, track and close a risk against both registers (system and project) - the full cycle, backed by real register writes.
---

# risk-manage

## Purpose

Work a risk through identify -> assess -> treat -> track -> close, keeping
**system risk** (operational/system, drives architectural decisions) and
**project risk** (schedule/resource/process, blocks a review meeting)
strictly separate (spec Sec.6.2: "different owners, different review
cadences and different treatments; merging them means one of the two is
always reviewed on the wrong schedule").

## When to invoke

A risk surfaces during any other skill's work - an `arch-transition` gap
that represents a real capability hole, a feasibility concern found during
`arch-perspective`'s SystemAnalysis check, a schedule concern raised in
conversation.

## Inputs

The risk description, and which register it belongs in - system or
project. If unclear, ask: does this drive an architectural decision
(system) or block a review/process milestone (project)? Never file to
"whichever register is open" by default.

## Context required

`se-buddy/registers/risks-system.yaml` and
`se-buddy/registers/risks-project.yaml` - readable via `se-buddy register`,
written via `se-buddy write register` (spec Sec.6.2: "the only route" into
a register).

## Procedure

1. **Identify**: state the risk in one line, which register it belongs in,
   and why (the system-vs-project test above).
2. **Assess**: likelihood, impact, and what evidence supports the
   assessment (C01 - label it FACT if retrieved, ASSUMPTION if not).
3. **Treat**: propose a treatment (avoid/mitigate/transfer/accept), and
   whether it implies an architectural change (route to `arch-decide`/
   modelling-track skills) or a process change (stays a project-risk
   treatment). Draft the row: `claim`, `status`, `owner`, `provenance`,
   `links` (to the model elements the risk concerns), `likelihood`,
   `impact`, `treatment`.
4. **Track**: once the engineer authorises the write (TTY gate,
   Sec.2.3 - the agent drafts the row content and presents it; a human
   runs `se-buddy write register risks-system row.yaml` themselves,
   directly, in their own terminal), the row exists with a stable id and
   `status` reflects where the risk actually is (`identified` ->
   `assessing` -> `treating` -> ...).
5. **Close**: the engineer runs `write register` again with the same `id`
   and `status: closed` - `upsert_row` updates the existing row in place
   rather than creating a duplicate (spec Sec.6.2: it's still the same
   risk).

## Outputs

A risk entry in D8-adjacent shape: what it is, which register, assessment,
proposed treatment - handed to the engineer as row content ready for
`write register`, plus (D8) a `SUPPLY` or `DECIDE` ask for anything that
needs the engineer's judgement before the row can be written at all
(e.g. which treatment to pick).

## Commands used

`se-buddy register risks-system`, `se-buddy register risks-project`
(read); `se-buddy write register` (write, TTY-gated); `se-buddy trace
<id>` to check what a risk's `links` connect to, and what registers cite a
given model element.

## Authority constraints

Identify and assess are automatic-authority reasoning (C05) - no gate.
Treat, track and close all end in a register write, and **the agent never
runs `write register` itself** - it drafts the row and the engineer runs
the write, interactively, themselves (spec Sec.2.3's TTY gate: the write
verb structurally cannot succeed from an agent's own tool call). Never
present a risk as logged, tracked, or closed until the engineer confirms
they actually ran the write.

## Failure handling

Never write a system risk into `risks-project.yaml` or vice versa to avoid
deciding which register applies (spec Sec.6.2's separation is a MUST, not
a convenience). If genuinely both apply (a system risk with a schedule
consequence), file both, cross-referencing by id.

## Interaction with other skills

`arch-transition` and `arch-perspective` are common sources of system
risks (unadjudicated gaps, unmet feasibility criteria). `arch-decide`
picks up a risk whose treatment requires an architectural decision.
