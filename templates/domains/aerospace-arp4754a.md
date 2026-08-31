# Domain pack: Aerospace (ARP4754A)

An illustrative example, not a default (spec Sec.5.4) - copy this to
`se-buddy/domain.md` and edit every section to match your actual programme
and certification basis before it means anything. Structurally modelled on
[`ajhcs/mbse-agents`](https://github.com/ajhcs/mbse-agents)'s aerospace
pack, which the spec names as a good structural reference.

## Applicable standards

- SAE ARP4754A - "Guidelines for Development of Civil Aircraft and Systems": development assurance level (DAL) assignment and the requirements-capture/validation/verification lifecycle
- SAE ARP4761 - safety assessment process feeding DAL and failure-condition classification
- DO-178C / DO-254 - software and hardware item-level assurance, downstream of the system-level items this pack covers

Replace with the clauses that actually bite for your certification basis - a
generic list of "the standards this domain has" is not what this section is
for.

## Lifecycle crosswalk

| ARP4754A phase | Arcadia perspective | Expected artefact |
| --- | --- | --- |
| Aircraft/System Function Development | OperationalAnalysis | Operational activities, operational capabilities agreed with the customer |
| Allocation of Aircraft Functions to Systems | SystemAnalysis | System functions, system capabilities, feasibility evidence |
| Development of System Architecture | LogicalArchitecture | Logical components, functional chains, viewpoint-driven boundary decisions |
| Allocation of System Requirements to Items | PhysicalArchitecture | Physical components, physical links, supplier-facing interfaces |
| Item Requirements / Verification | EPBSArchitecture | Configuration items, build strategy, supplier obligations |

## Baseline viewpoints

- **Safety**: no single function chain concentrates a catastrophic failure condition in one physical component - priority 1
- **Certification traceability**: every requirement resolves to a verification method before PDR - priority 2
- **Weight/power budget**: physical allocation stays within the platform's mass and power envelope - priority 3

## Evidence expectations

- At PDR: operational and system capabilities agreed, feasibility risk mitigated (spec Sec.2.2's SystemAnalysis stop criterion)
- At CDR: logical architecture proven by multi-viewpoint analysis, physical architecture refined enough for suppliers
- At certification: full requirements-to-verification traceability, safety assessment closed against ARP4761

## Reviewer attack surfaces

- **Mistake:** allocating a function to a component before the functional chain crossing safety-critical boundaries is identified.
  **Why it's wrong:** the safety assessment (ARP4761) then drives a physical redesign instead of informing the logical one.
  **Correct approach:** trace every functional chain against the safety viewpoint before physical allocation (spec Sec.2.2 rule 3).
- **Mistake:** treating a system-level requirement as satisfied because a lower-level item requirement exists with a similar name.
  **Why it's wrong:** name similarity is not traceability (spec C07) - the registers/verification row (spec Sec.6.2) is the only source of truth.
  **Correct approach:** require an explicit `registers/verification.yaml` row citing both ids before closing the requirement.

## Verification patterns

- Functional requirement: verified by test, against a functional chain scenario
- Safety requirement: verified by analysis, against ARP4761 failure-condition classification
- Interface requirement: verified by inspection, against the `interface` validation layer's findings (spec Sec.7.2)
