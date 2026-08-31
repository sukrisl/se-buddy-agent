# OperationalAnalysis

**Question:** what do users need to accomplish?

**Layer:** `OperationalAnalysis` (`model.oa`)

**Stop criterion:** agreement with the customer. This is an
agreement-based criterion (spec Sec.2.2 rule 1) - report `UNKNOWN` unless
a `CONFIRM` exists in `knowledge.yaml` recording that the customer actually
agreed. No structural check can substitute for this.

## What to expect present

- Operational activities and processes (`model.oa.all_activities`,
  `all_operational_processes`) describing what actors do, not what a
  system will do for them.
- Operational actors and entities (`all_actors`, `all_entities`) - the
  people and organisations in the customer's world.
- Activity exchanges and entity exchanges - what flows between actors, in
  the actors' own vocabulary, before any system exists to carry it.
- Capabilities the customer needs (`all_capabilities`), traceable forward
  into `SystemAnalysis`'s capabilities once that perspective starts.

## Common attack surface

Describing a system's internal behaviour here, dressed up as an
"operational activity" - the tell is an activity named after a system
component rather than a human or organisational actor. That's a
`SystemAnalysis` concern arriving too early; flag it as a perspective
mismatch (spec Sec.2.2 rule 2: iteration between perspectives is normal,
but it must be named, not silent).

## Transition in from nowhere, out to SystemAnalysis

There is no perspective before this one; everything here is either
customer-supplied or observed. Transitioning out: every operational
activity should be realized or refined by a system function, deliberately
not carried (cite the row in `registers/not-carried.yaml`, once that
register exists), or flagged as an open gap.
