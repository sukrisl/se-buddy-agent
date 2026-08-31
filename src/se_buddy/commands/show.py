"""`se-buddy show <id>` - one element or record, relationships, diagrams, citations (spec Sec.7.3)."""

from __future__ import annotations

import re
import warnings
from pathlib import Path

from se_buddy.ask_store import get_ask
from se_buddy.changes import find_followup_item, load_change, load_followup
from se_buddy.commands._common import add_limit_argument, add_model_argument, load_model_or_die, truncate
from se_buddy.decisions import load_adr
from se_buddy.memory import render_citation
from se_buddy.proposals import load_cp
from se_buddy.registers import find_row

# Behavioural elements are read, not judged (spec Sec.2.2) - this command
# treats a FunctionalChain/Scenario/StateMachine exactly like a structural
# element: name, parent, diagrams, and whatever relationships it has. No
# special-casing per class.

RELATIONSHIP_ITEM_LIMIT = 5

# A model uuid never matches this shape (a short prefix, a dash, digits) -
# checked before touching the model at all, so a record lookup never pays
# a ~300ms parse for something that was never going to be a model element.
_RECORD_ID_RE = re.compile(r"^([A-Za-z]+)-\d+$")


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser("show", help="one element or record, relationships, diagrams")
    parser.add_argument("id", help="a model element UUID, or a record/ask/register-row id")
    add_model_argument(parser)
    add_limit_argument(parser, default=15)
    parser.set_defaults(func=run)


def run(args) -> int:
    root = Path.cwd()
    match = _RECORD_ID_RE.match(args.id)
    if match:
        handled = _show_record(root, args.id, match.group(1).upper())
        if handled is not None:
            return handled
        print(f"se-buddy: {args.id!r} looks like a record id but does not match any known kind")
        return 1

    model = load_model_or_die(args)
    if model is None:
        return 1

    try:
        element = model.by_uuid(args.id)
    except KeyError:
        print(f"se-buddy: {args.id!r} is not a model element, record, ask or register row in this project.")
        return 1

    print(f"{type(element).__name__} {args.id}")
    name = getattr(element, "name", "")
    if name:
        print(f"  name: {name}")

    parents = list(_iter_ancestors(element))
    if parents:
        chain = " > ".join(getattr(p, "name", "") or type(p).__name__ for p in reversed(parents))
        print(f"  parent chain: {chain}")

    diagrams = list(getattr(element, "diagrams", []) or [])
    if diagrams:
        shown, truncated = truncate(diagrams, args.limit)
        names = ", ".join(d.name for d in shown)
        suffix = f" (truncated from {len(diagrams)}, --limit {args.limit})" if truncated else ""
        print(f"  on {len(diagrams)} diagram(s): {names}{suffix}")

    relationships = relationship_attrs(element)
    shown_rels, rel_truncated = truncate(sorted(relationships), args.limit)
    for attr in shown_rels:
        value = relationships[attr]
        sample_items, item_truncated = truncate(list(value), RELATIONSHIP_ITEM_LIMIT)
        sample = ", ".join(getattr(v, "name", "") or type(v).__name__ for v in sample_items)
        suffix = f", +{len(value) - len(sample_items)} more" if item_truncated else ""
        print(f"  {attr}: {len(value)} ({sample}{suffix})")
    if rel_truncated:
        print(f"  ... {len(relationships) - len(shown_rels)} more relationship kinds not shown (--limit {args.limit})")

    return 0


def _show_record(root: Path, record_id: str, prefix: str) -> int | None:
    """Dispatches a record/ask/register-row id to its loader. Returns an
    exit code, or `None` if `record_id` didn't match anything (the caller
    reports "not found").
    """
    if prefix == "ADR":
        adr = load_adr(root, record_id)
        if adr is None:
            return None
        print(f"ADR {record_id}")
        print(f"  {render_citation(record_id, adr.get('claim', ''))}")
        print(f"  chosen: {adr.get('chosen_option', '')}")
        print(f"  authority: {adr.get('authority', '')}")
        if adr.get("supersedes"):
            print(f"  supersedes: {', '.join(adr['supersedes'])}")
        return 0

    if prefix == "CP":
        cp = load_cp(root, record_id)
        if cp is None:
            return None
        print(f"CP {record_id}")
        print(f"  {render_citation(record_id, cp.get('claim', ''))}")
        print(f"  intent: {cp.get('intent', '')}")
        print(f"  affected elements: {len(cp.get('affected_elements') or [])}")
        print(f"  has proposed_changes: {'yes' if cp.get('proposed_changes') else 'no'}")
        return 0

    if prefix == "CHANGE":
        change = load_change(root, record_id)
        if change is None:
            return None
        print(f"CHANGE {record_id}")
        print(f"  {render_citation(record_id, change.get('claim', ''))}")
        print(f"  proposal: {change.get('proposal') or '(none - recorded manually)'}")
        print(f"  authority: {change.get('authority', '')}")
        print(f"  {change.get('diff_summary', '')}")
        print(f"  {change.get('validation_summary', '')}")
        followup = load_followup(root, record_id)
        open_count = sum(1 for item in followup if item.get("answered") is None)
        print(f"  followup: {open_count}/{len(followup)} still open")
        return 0

    if prefix == "ASK":
        ask = get_ask(root, record_id)
        if ask is not None:
            print(f"ASK {record_id}")
            print(f"  act: {ask['act']}")
            print(f"  object: {ask['object']}")
            print(f"  done when: {ask['done_when']}")
            print(f"  answered: {ask.get('answered') or 'not yet'}")
            return 0
        followup_hit = find_followup_item(root, record_id)
        if followup_hit is not None:
            change_id, item = followup_hit
            print(f"ASK {record_id} (followup on {change_id})")
            print(f"  act: {item['act']}")
            print(f"  object: {item['object']}")
            print(f"  done when: {item['done_when']}")
            print(f"  answered: {item.get('answered') or 'not yet'}")
            return 0
        return None

    register_hit = find_row(root, record_id)
    if register_hit is not None:
        register, row = register_hit
        print(f"register row {record_id} ({register})")
        print(f"  {render_citation(record_id, row.get('claim', ''))}")
        print(f"  status: {row.get('status', '?')}")
        return 0

    return None


def _iter_ancestors(element):
    seen = 0
    current = element
    while True:
        parent = getattr(current, "parent", None)
        if parent is None or parent is current:
            return
        yield parent
        current = parent
        seen += 1
        if seen > 50:  # containment trees are not this deep; stop rather than loop forever
            return


def relationship_attrs(element) -> dict:
    """Every non-empty ElementList-valued attribute on `element`'s class.

    Deprecated aliases (e.g. `.exchanges` for `.component_exchanges`) are
    excluded by turning their warning into an error and skipping - this is
    what keeps the list to the current, non-redundant names instead of
    reporting the same relationship twice under two spellings.
    """
    from capellambse.model import ElementList

    found: dict = {}
    for attr in dir(type(element)):
        if attr.startswith("_") or attr in ("diagrams", "visible_on_diagrams"):
            continue
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error")
                value = getattr(element, attr)
        except Exception:
            continue
        if isinstance(value, ElementList) and len(value) > 0:
            found[attr] = value
    return found
