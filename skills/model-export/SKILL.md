---
name: model-export
description: Render a context diagram into a document. Describes the intended procedure - the underlying command is not built yet (see Authority constraints).
---

# model-export

## Purpose

Render a generated context diagram for a document or review pack (spec
Sec.7.4): "Generated on demand, written to an image file, never stored in
`.aird`, never authoritative." Diagrams stay deliberately thin in this
spec - this is the one place synthesis (not hand-placement) is in scope
at all, and only for this narrow purpose.

## When to invoke

An engineer needs a diagram for a document, review pack, or presentation
- not for the model itself, which is never touched by this skill (spec
Sec.7.4: "Write `.aird`: Never").

## Inputs

The element(s) to centre the context diagram on, and where the rendered
image should go.

## Context required

The element(s)' identity (`se-buddy show`) - the actual rendering would
need `capellambse-context-diagrams` (spec Sec.7.1's table names it as the
intended tool: `.context_diagram`/`.tree_view` attributes on a model
element).

## Procedure

1. Resolve the target element(s) via `se-buddy show`/`se-buddy search`.
2. State clearly that rendering itself is not available in this installed
   version (see Authority constraints) - do not attempt to hand-draw a
   diagram description as a substitute; that is exactly the kind of
   synthesis spec Sec.7.4 keeps out of scope.
3. If a rendered diagram is genuinely needed now, say so as a `SUPPLY`
   ask (D8): the dependency (`capellambse-context-diagrams`) and the
   command (`se-buddy export`) both need to be added first, which is a
   decision for whoever maintains this installation, not something to
   work around in-conversation.

## Outputs

Either "not available yet" stated plainly with the `SUPPLY` ask above, or
(once built) the rendered image's path.

## Commands used

`se-buddy show`, `se-buddy search` (to resolve the target). `se-buddy
export <element>` **does not exist yet.**

## Authority constraints

**This skill's core capability is not built.** `capellambse-context-
diagrams` is not vendored or otherwise present in this repo (confirmed
directly - no trace of it anywhere under `vendor/`), and adding it is a
genuinely new external dependency, deferred by explicit decision rather
than by oversight (spec Sec.7.4 already frames the whole diagram story as
"deliberately thin," and this is the piece that stayed thin). Read-only
context-gathering here (`show`/`search`) is automatic authority (C05);
there is no write path in this skill at all, gated or otherwise, because
there is nothing yet for a write path to call.

## Failure handling

Never render a diagram by any other means as a substitute (an ASCII
sketch, a hand-described layout, an unrelated tool) - that is inventing a
second, uncontrolled representation of the model's context exactly where
spec Sec.7.4 says representation belongs to the engineer alone.

## Interaction with other skills

Would consume `model-impact`'s or `retrieve-context`'s element resolution
once built. Nothing currently depends on this skill's output existing.
