---
name: risk-manage
description: Identify, assess and treat a risk against both registers (system and project). Tracking and closing need register writes that are not yet wired up (see Authority constraints).
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

`registers/risks-system.yaml` and `registers/risks-project.yaml` (Phase
2+, once registers exist to read/write).

## Procedure

1. **Identify**: state the risk in one line, which register it belongs in,
   and why (the system-vs-project test above).
2. **Assess**: likelihood, impact, and what evidence supports the
   assessment (C01 - label it FACT if retrieved, ASSUMPTION if not).
3. **Treat**: propose a treatment (avoid/mitigate/transfer/accept), and
   whether it implies an architectural change (route to `arch-decide`/
   modelling-track skills) or a process change (stays a project-risk
   treatment).
4. **Track / Close**: these are register mutations - see Authority
   constraints below.

## Outputs

A risk entry in D8-adjacent shape: what it is, which register, assessment,
proposed treatment, and (D8) a `SUPPLY` or `DECIDE` ask for whatever needs
the engineer's input to proceed.

## Commands used

`se-buddy register risks-system`, `se-buddy register risks-project`
(read); `se-buddy write register` (Phase 2+, TTY-gated).

## Authority constraints

Identify and assess are automatic-authority reasoning (C05) - no gate.
**Treat, track, and close all end in a register row**, and
`se-buddy write register` is TTY-gated (spec Sec.6.2: "the only route" into
a register) and does not exist yet in this installed phase (Phase 2). Until
then: complete identify/assess/treat in full and present the row content
directly to the engineer, stating plainly that recording it is pending -
do not claim a risk has been logged when it hasn't been. This mirrors
`arch-decide`'s handling of its own pending write step.

## Failure handling

Never write a system risk into `risks-project.yaml` or vice versa to avoid
deciding which register applies (spec Sec.6.2's separation is a MUST, not
a convenience). If genuinely both apply (a system risk with a schedule
consequence), file both, cross-referencing by id once ids exist to
cross-reference.

## Interaction with other skills

`arch-transition` and `arch-perspective` are common sources of system
risks (unadjudicated gaps, unmet feasibility criteria). `arch-decide`
picks up a risk whose treatment requires an architectural decision.
