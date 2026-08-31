"""`se-buddy write record draft.yaml` - record work the engineer did by hand in Capella (spec Sec.7.3).

TTY-gated. No snapshot/apply step: the model was already changed outside
se-buddy's control, so there is nothing for this command to do or undo -
`write revert` on a CHANGE filed this way has nothing to restore to and
refuses cleanly, which is honest rather than a limitation to route around.
`validation_summary` is computed for real, against the model as it
currently stands; `diff_summary` and `manual_followup` are the engineer's
own description of what they did and what (if anything) is still owed.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml

from se_buddy.changes import ChangeError, changes_dir, file_change
from se_buddy.commands._common import add_model_argument, load_model_or_die
from se_buddy.gate import GateRefused, confirm
from se_buddy.memory import allocate_id
from se_buddy.validate import run_all_layers, summarize


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser("write-record", help="record work the engineer did by hand in Capella")
    parser.add_argument("draft_file", help="path to a YAML file describing the manual work")
    add_model_argument(parser)
    parser.set_defaults(func=run)


def run(args) -> int:
    draft_path = Path(args.draft_file)
    if not draft_path.exists():
        print(f"se-buddy: {draft_path} does not exist")
        return 1
    draft = yaml.safe_load(draft_path.read_text(encoding="utf-8")) or {}

    root = Path.cwd()
    model = load_model_or_die(args)
    if model is None:
        return 1

    try:
        confirm(f"About to record manual work: {draft.get('claim', '<no claim given>')}")
    except GateRefused as exc:
        print(f"se-buddy: {exc}")
        return 1

    findings = run_all_layers(root, model)
    validation_summary = summarize(findings)

    change_id = allocate_id("CHANGE", changes_dir(root))
    change = {
        "claim": draft.get("claim"),
        "tier": draft.get("tier", "judgement"),
        "date": draft.get("date") or date.today().isoformat(),
        "supersedes": draft.get("supersedes", []),
        "proposal": draft.get("proposal"),
        "authority": draft.get("authority"),
        "diff_summary": draft.get("diff_summary"),
        "validation_summary": validation_summary,
        "manual_followup": draft.get("manual_followup", []),
    }

    try:
        written = file_change(root, change_id, change, change["manual_followup"])
    except ChangeError as exc:
        print(f"se-buddy: {exc}")
        return 1

    print(f"recorded {written['id']}")
    print(f"  {validation_summary}")
    return 0
