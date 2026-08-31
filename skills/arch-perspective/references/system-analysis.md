# SystemAnalysis

**Question:** what must the system do for them?

**Layer:** `SystemAnalysis` (`model.sa`)

**Stop criterion:** feasibility risk mitigated, enough to decide to
design. Not agreement-based (unlike `OperationalAnalysis`/
`EPBSArchitecture`) - this one can be assessed against model and register
content directly, once risk registers exist (Phase 2+). Until then, report
what's present and let the engineer judge sufficiency; do not assert
"feasibility risk mitigated" from model shape alone (C04).

## What to expect present

- System functions and function exchanges (`model.sa.all_functions`,
  `all_function_exchanges`) realizing the operational activities that were
  deliberately carried forward.
- System capabilities (`all_capabilities`), tracing back to operational
  capabilities.
- System actors and components (`all_actors`, `all_components`) - the
  system's boundary and what sits outside it.
- Interfaces (`all_interfaces`) at the system boundary, named but not yet
  physically realized.
- Missions (`all_missions`) where the domain uses them.

## Common attack surface

Jumping straight to a physical or technology-committed design here - the
tell is a "system function" that only makes sense given one specific
implementation choice. `LogicalArchitecture`'s stop criterion explicitly
requires "no technology" (spec Sec.2.2's table); if technology has already
crept in at `SystemAnalysis`, that's an even earlier violation worth
flagging.

## Transition in from OperationalAnalysis, out to LogicalArchitecture

Every carried-forward operational activity should be realized by a system
function (spec Sec.2.2 rule 2 - check `registers/not-carried.yaml` for
what was deliberately left behind, once that register exists). Going out:
system functions get grouped into logical components according to a
declared viewpoint (rule 3) - that grouping is `LogicalArchitecture`'s job,
not this one's.
