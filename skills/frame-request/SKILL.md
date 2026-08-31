---
name: frame-request
description: What is being asked, which track, which tier - the router for everything else. Invoke first unless the request is plainly a lookup (spec Sec.8).
---

# frame-request

## Purpose

Name what is actually being asked before doing it: which axis-1 track
(architecture or modelling, spec Sec.2.1), which tier (spec D1), and which
skill the request actually belongs to. This is the one skill whose job is
routing, not answering.

## When to invoke

Any request that is not plainly a single-command lookup (spec Sec.8:
"Invoke by name; `frame-request` routes unless the request is plainly a
lookup"). A request for a specific `se-buddy show <id>`-shaped answer
doesn't need routing; "should we split this component" does.

## Inputs

The engineer's request, in whatever form it arrived - a question, a change
they want, a diagram they're looking at.

## Context required

Nothing beyond the request itself. Do not load the full model or profile
before knowing which skill needs it; that's `retrieve-context`'s job, one
step later.

## Procedure

1. **Name the track first** (spec Sec.2.1). Ask: does this question ask
   what the architecture *should be* (architecture track -> an ADR is the
   artefact, the engineer decides) or how a settled architecture is
   *expressed* in Capella (modelling track -> a CP/CHANGE, the engineer
   authorises)? This is the most consequential distinction in the spec and
   the easiest to lose - get it right before anything else.
2. **Check the converse.** Is this actually determined already by an
   existing ADR, principle, or model fact? If so, it's a lookup (D5), not
   a decision wearing a proposal's clothes - route to a direct answer, not
   a heavier skill.
3. **Name the tier** (D1): `lookup`, `judgement`, or `decision`. State it
   as the first line of whatever response follows.
4. **Route** to the skill whose artefact and authority level match:
   - "what exists / what was decided / why" with no judgement needed ->
     `retrieve-context` or `trace-rationale`
   - "is this right, given our principles/ADRs" -> `arch-review`
   - "which Arcadia perspective, and is it done" -> `arch-perspective`
   - "what are the non-functional concerns here" -> `arch-viewpoint`
   - "handing off between two perspectives" -> `arch-transition`
   - "settle this architectural question" -> `arch-decide`
   - "record a standing rule/assumption/constraint" -> `arch-principles`
   - "identify/assess/treat a risk" -> `risk-manage`
   - modelling-track requests (impact, plan, apply, validate, record,
     export) -> the corresponding `model-*` skill (arrives with the phase
     that gives it a write path - see that skill's own scope note)
   - a brand-new project with no profile yet -> `project-init`
5. If more than one skill plausibly applies, name both and say which is
   first and why (D9's sequencing rule applies to routing too).

## Outputs

One line naming: track, tier, and the skill being handed off to. Nothing
else - the actual answer belongs to whichever skill is invoked next.

## Commands used

None directly. `se-buddy asks` is worth checking first in a new session
(spec Sec.7.3: "the session's first command") to see what was already
open before framing a new request.

## Authority constraints

Routing carries no authority beyond read (per
`references/cross-cutting-behaviours.md`, C05). Naming a track or tier is
not itself a decision or a proposal.

## Failure handling

If the track genuinely cannot be named from the request alone, ask - a
DECIDE-vs-AUTHORISE ambiguity left unresolved corrupts every artefact that
follows (spec Sec.2.1).

## Interaction with other skills

Every other skill assumes `frame-request` has already run, even when that
run was instant and silent (a plain lookup). `write-plain`'s size budgets
and D6 apply to whatever skill is routed to next, not to this one.
