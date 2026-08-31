# PhysicalArchitecture

**Question:** how will it be built?

**Layer:** `PhysicalArchitecture` (`model.pa`)

**Stop criterion:** everything `LogicalArchitecture` required, **and**
refined enough for suppliers. Not agreement-based; assessable directly.

## What to expect present

- Physical components (`model.pa.all_components`) realizing logical
  components, now with technology committed.
- Physical links and physical exchanges (`all_physical_links`,
  `all_physical_exchanges`) - the concrete connections logical component
  exchanges are realized by.
- Physical paths (`all_physical_paths`) where routing/topology matters.
- Interfaces refined to the point a supplier could actually implement
  against them - a named connector, protocol, or physical medium, not just
  a logical port.

## Common attack surface

A physical component that realizes a logical one but adds nothing a
supplier needs (spec Sec.2.2: "each new level must also add what the
previous one never had" - a one-for-one physical mirror of the logical
architecture is transcription, not engineering). Also watch for weight/
power/cost budgets (viewpoint-driven, domain-specific - see
`se-buddy/domain.md`'s baseline viewpoints) being ignored at this stage,
since this is where they actually bite.

## Transition in from LogicalArchitecture, out to EPBSArchitecture

Every logical component should be realized by a physical one, or
deliberately not carried with a cited reason (`registers/not-carried.yaml`,
Phase 2+). Going out: physical components and their interfaces become the
configuration items `EPBSArchitecture` builds a supplier agreement around -
that packaging, not further technical refinement, is the next
perspective's job.
