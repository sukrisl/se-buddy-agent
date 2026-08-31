# EPBSArchitecture

**Question:** what does each supplier owe?

**Layer:** `EPBSArchitecture` (`model.epbs`)

**Stop criterion:** agreement with suppliers. Agreement-based (spec
Sec.2.2 rule 1) - report `UNKNOWN` unless a `CONFIRM` exists recording
that suppliers actually agreed to what they owe.

## What to expect present

- Configuration items (`model.epbs.all_configuration_items`) - this
  perspective is real but thinner than the other four: it has no
  `all_components`/`all_actors`/`all_actor_exchanges` (confirmed directly
  against capellambse 0.8.1). Do not treat that absence as a defect in the
  model; it's the shape of this perspective.
- A realization link back to the physical architecture
  (`physical_architecture_realizations`/`realized_physical_architecture`)
  - EPBS packages what PA already refined, it does not re-derive it.

## Common attack surface

Treating EPBS as "just another layer with the usual accessors" and
reporting a structural absence (no `all_components`, say) as a gap. It
isn't one - `arch-perspective`'s own generic per-layer counting must not
assume symmetry across perspectives (spec Sec.2.2's own framing of this
layer, confirmed against the real metamodel).

The other real attack surface: asserting supplier agreement from the
existence of configuration items alone. A configuration item is a FACT
about the model; supplier agreement is a separate, human fact that only a
`CONFIRM` record establishes.

## Transition in from PhysicalArchitecture

This is the last perspective - there is nothing to transition out to.
Every physical component that needs a supplier should map to a
configuration item, or be deliberately excluded with a cited reason.
