# Domain pack: <replace with your domain's name>

Copy this file to `se-buddy/domain.md` and replace every section. This is
an inert example (spec Sec.5.4) - it becomes binding only once a project
adopts and edits it; nothing in it is a default this agent assumes.

Every section below is required by spec Sec.5.4. `se-buddy doctor` checks
that this file exists, not that it is complete - an incomplete domain pack
is still better reviewed by a human than silently invented by the agent
(spec C02: "with no principles recorded, say the style is unknown rather
than inventing one" applies here too).

## Applicable standards

List the standards this project is actually held to, and the specific
clauses that bite. Not every standard in the domain - only the ones a
reviewer or auditor for *this* project will actually cite.

- <standard> <clause> - <what it requires, one line>

## Lifecycle crosswalk

Map this domain's lifecycle phases onto the five Arcadia perspectives
(spec Sec.2.2) and name what artefact is expected at each.

| Domain phase | Arcadia perspective | Expected artefact |
| --- | --- | --- |
| <phase> | OperationalAnalysis | <artefact> |
| <phase> | SystemAnalysis | <artefact> |
| <phase> | LogicalArchitecture | <artefact> |
| <phase> | PhysicalArchitecture | <artefact> |
| <phase> | EPBSArchitecture | <artefact> |

## Baseline viewpoints

The non-functional concerns of this domain. Each one needs a priority
order to be usable (spec Sec.9) - copy the shape into `se-buddy/
viewpoints.yaml` once you've filled this in, since that file, not this one,
is what `arch-viewpoint` actually reads.

- <viewpoint name>: <what it's protecting> - priority <n>

## Evidence expectations

What a reviewer, auditor or customer will ask to see, and at which gate
(spec Sec.6.4 - this is the only place that knows what "a gate" means; the
rest of the agent doesn't).

- At <gate name>: <evidence expected>

## Reviewer attack surfaces

Known anti-patterns in this domain: the mistake, why it's wrong, the
correct approach. `arch-review` treats these as binding project
requirements once recorded here (spec Sec.5.4) - distinct from generic
best practice, which C02 says to treat as advisory only.

- **Mistake:** <what people get wrong>
  **Why it's wrong:** <consequence>
  **Correct approach:** <what to do instead>

## Verification patterns

How claims in this domain are normally verified - the evidence an
`arch-review` finding should ask for before it's accepted as closed.

- <claim type>: verified by <method>
