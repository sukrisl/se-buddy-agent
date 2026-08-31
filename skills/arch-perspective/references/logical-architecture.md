# LogicalArchitecture

**Question:** how will it work?

**Layer:** `LogicalArchitecture` (`model.la`)

**Stop criterion:** an architecture proven best by multi-viewpoint
analysis - and no technology. Not agreement-based; assessable against the
model plus recorded viewpoints (`viewpoints.yaml`, Phase 2+ for writing,
but readable via `se-buddy memory viewpoints` once init has scaffolded a
project that has filled it in).

## What to expect present

- Logical components (`model.la.all_components`) formed by grouping or
  segregating system functions - per spec Sec.2.2 rule 3, this grouping
  MUST cite a viewpoint and its priority. A component boundary with no
  cited viewpoint is not yet justified, whatever it looks like.
- Logical functions and function exchanges, component exchanges
  (`all_functions`, `all_function_exchanges`, `all_component_exchanges`).
- Functional chains (`all_functional_chains`) demonstrating how a
  viewpoint claim actually holds across the architecture, not just
  asserted for one component in isolation.
- Interfaces between logical components, still technology-free.

## Common attack surface

A component boundary that "just looks right" with no viewpoint cited -
this is exactly rule 3's failure mode: "say a compromise cannot be proven
rather than inventing a plausible set." A boundary chosen because it maps
neatly onto an org chart or a prior codebase's module structure, with no
stated design rule, is a finding, not a pass.

Also watch for technology leaking in here (a component named after a
specific piece of hardware or a specific vendor's product) - that belongs
in `PhysicalArchitecture`.

## Transition in from SystemAnalysis, out to PhysicalArchitecture

Every system function should be allocated to exactly the logical
components the viewpoint analysis justifies - not one-for-one carried
across (spec Sec.2.2: "a layer that traces upward one-for-one has been
transcribed, not engineered"). Going out: logical components get realized
by physical components once "refined enough for suppliers" is also true,
which is `PhysicalArchitecture`'s additional bar.
