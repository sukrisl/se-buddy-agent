---
name: model-validate
description: Is the model well-formed, do the diagrams still match? Runs and interprets the six validation layers - never a completeness check.
---

# model-validate

## Purpose

Run and interpret `se-buddy validate`'s six layers (spec Sec.7.2) against
the current model, distinguishing a real finding from `perspective`'s
different question (completeness - not built as its own command in this
phase, see SPEC-COVERAGE.md, but the distinction still holds: a
structural pass is never evidence of completeness, spec Sec.13).

## When to invoke

After any model change (`write apply` runs this automatically as part of
its own lifecycle, spec Sec.10.2 - this skill is for checking *outside*
that moment: before proposing a change, after manual Capella work, or on
request).

## Inputs

None beyond the current model/registers state.

## Context required

`se-buddy validate`'s output, and `se-buddy/viewpoints.yaml` (the
`architectural` layer names the recorded viewpoints it can't itself
check - this skill is what actually checks them, by reading the model
against each rule).

## Procedure

1. Run `se-buddy validate`.
2. Report each layer's findings with its severity, never collapsed into
   one pass/fail (spec Sec.7.2: "each layer is separately reportable").
3. For `structural`/`representation`/`interface`/`traceability`/
   `consistency`: these are real, automated findings - treat an `ERROR`
   as blocking, a `WARN` as worth raising but not necessarily blocking.
4. For `architectural`: it always reports `UNKNOWN` (spec C04) with the
   recorded viewpoints named - **this skill's own job is to actually read
   the model against each named design rule** and render a real verdict
   in conversation, citing the specific rule and priority (`arch-viewpoint`
   supplies these). Never let `UNKNOWN` stand in as "nothing to check" -
   it means "code can't check this, a human/reasoning-layer read is
   needed," and this skill is that read.
5. Never report a validation pass as evidence the model or a perspective
   is *complete* (spec Sec.7.2, spec Sec.13's own review question 6) -
   name explicitly that these are well-formedness checks, not a
   completeness measure.

## Outputs

Findings grouped by layer, each labelled with severity and evidence;
`architectural` findings additionally carry the reasoning-layer's own
verdict against each named viewpoint, cited by rule and priority (D3).

## Commands used

`se-buddy validate`, `se-buddy memory viewpoints` (for `architectural`'s
manual read).

## Authority constraints

Read-only; automatic authority (C05). A validation finding is not itself
a decision about whether to fix it - that's `arch-review`/`arch-decide`'s
territory if the finding turns out to be architectural, or a direct
`model-plan` if it's a straightforward model fix.

## Failure handling

Never read a validation `PASS` on five layers as license to skip the
`architectural` layer's manual check - `UNKNOWN` is not a softer pass, and
skipping it is exactly the shortcut C04 exists to prevent.

## Interaction with other skills

`write apply` calls the underlying six-layer check automatically; this
skill is for every other moment a validation read is needed, and is what
gives `architectural`'s `UNKNOWN` an actual answer. Findings that turn out
to require an architectural decision route to `arch-decide`.
