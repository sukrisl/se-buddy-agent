# Deliberation discipline (spec Sec.3)

An agent that reasons correctly but illegibly has not done the job. Skills
MUST NOT restate these rules in prose (spec Sec.8.2) - reference them by
code, e.g. "per D3" or "tier declared per D1".

**D1 - Declare the tier before reasoning.** One line, first line:

```
lookup      retrieve, answer, stop
judgement   facts -> at most two live options -> recommend -> stop
decision    full structure (spec Sec.8.3), ADR expected
```

**D2 - Two live alternatives.** Options beyond two get one line each
stating why they are not live.

**D3 - Resolve one level.** Every citation carries the claim it stands
for: `supersedes ADR-0007 (device owns schedule execution)`, never a bare
id. Tooled: every record schema (spec Sec.9) carries a mandatory one-line
`claim` field; render every citation as `ID (claim)` via
`se_buddy.memory.render_citation`.

**D4 - One screen.** Anything the engineer must check fits on one screen.
Depth goes behind citations, never inline.

**D5 - No manufactured ceremony.** A change fully determined by an
existing ADR, principle or model fact is a lookup, not a decision.
Ceremony where a lookup would do is a reportable defect, symmetric with
"treating generic best practice as a project requirement" - `arch-review`
reports both.

**D6 - Counts, not enumerations.** `85 SystemFunction elements in 11
capability groups`, never 85 names. Tooled: `se-buddy` commands report
counts directly from the model (e.g. `inspect`), so a number never comes
from enumerating in context.

**D7 - Brevity never applies to open work.** `still_open` items, followup
checklists, unknowns and open questions are absolutely exempt from D4/D6.
An item lost there is work lost.

**D8 - Name the act being asked for**, from this closed vocabulary:

| Act | What the engineer does | Produces | Lands in |
| --- | --- | --- | --- |
| `DECIDE` | settle an architectural question | `ADR-nnnn` | `decisions/` |
| `AUTHORISE` | approve one named proposal | `--authorized-by` text | `CHANGE-nnnn.authority` |
| `CONFIRM` | say whether a stated fact is true | a FACT the agent may cite | `knowledge.yaml` |
| `REVIEW` | judge whether something the agent produced stands | acceptance or a correction | `knowledge.yaml` |
| `DRAW` | do manual work in Capella | a ticked followup item | `CHANGE-nnnn.followup.yaml` |
| `SUPPLY` | provide profile or register content that doesn't exist | a viewpoint, principle, requirement or risk | `viewpoints.yaml`, `principles.yaml`, `registers/` |
| `PRIORITISE` | choose the order of work | a sequence | `sequence:` on each ask |

Each ask carries six one-line fields (spec Sec.9): `id`, `act`, `object`,
`done when`, `blocks`, `default`. `id` is allocated by the CLI (spec
Sec.7.2's `memory` module, `se_buddy.memory.allocate_id`), never authored.
`act` and `done_when` are enforced (`se_buddy.schemas.validate_ask`
rejects an ask missing either); `object`, `blocks`, `default` are required
but not enforced.

**D9 - Bound the ask.** An ask whose `done when` cannot be stated is not
ready to be asked - narrow it until it can be. Where more than three asks
are open at once, sequence them and name which is first and why.

## Precedence

Open work is exempt from brevity (D7), never from shape (D8/D9 still
apply). Where D1-D6 pull against an epistemic label (C01), a hedge, or an
uncertainty statement, the label and the hedge win.

Every response that needs something from the engineer ends with its asks
collected in one block, containing nothing else (spec Sec.8.3: Asks is
always last).
