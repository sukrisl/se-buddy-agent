"""`se-buddy write answer ASK-nnnn a.yaml` - closes one ask (spec Sec.7.3).

One verb because every ask has the same shape (spec Sec.9) and the answer
needs to land wherever its `act` belongs (spec Sec.3 D8):

    CONFIRM, REVIEW  -> append a row to se-buddy/knowledge.yaml
    PRIORITISE       -> write `sequence:` onto each ask named in a.yaml
    DRAW             -> tick the matching CHANGE-nnnn.followup.yaml entry
    DECIDE, SUPPLY   -> refuse, name the verb that fits (write memory / write register)
    AUTHORISE        -> refuse, name write apply --authorized-by (spec Sec.3 D8:
                        AUTHORISE lands in CHANGE-nnnn.authority, a different
                        verb entirely - not in spec Sec.7.3's dispatch table
                        explicitly, but follows directly from D8's own act
                        definitions, so it is refused the same way DECIDE/SUPPLY are)

TTY-gated. `answer_ask()` (the dispatch logic) and `run()` (the gate +
CLI wrapper) are separate on purpose: tests call `answer_ask()` directly,
never `run()` - spec Sec.2.3's accepted testing philosophy for every write
verb.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml

from se_buddy.ask_store import get_ask, mark_answered, set_sequence
from se_buddy.gate import GateRefused, confirm
from se_buddy.knowledge import append_knowledge_row


class AnswerError(Exception):
    """An ask could not be answered as asked - reported plainly."""


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser("write-answer", help="close one ask (spec Sec.7.3)")
    parser.add_argument("ask_id", help="an ASK-nnnn id, from `se-buddy asks`")
    parser.add_argument("answer_file", help="path to a YAML file with the answer content")
    parser.set_defaults(func=run)


def answer_ask(root: Path, ask_id: str, answer: dict, today: str | None = None) -> str:
    """Dispatches `answer` by the ask's act. Returns where it landed.

    Raises `AnswerError` for a refused act or a malformed answer - never
    silently does nothing.
    """
    today = today or date.today().isoformat()
    ask = get_ask(root, ask_id)
    if ask is None:
        raise AnswerError(f"{ask_id} is not a known ask - see `se-buddy asks`")
    if ask.get("answered") is not None:
        raise AnswerError(f"{ask_id} is already answered ({ask['answered']})")

    act = ask["act"]

    if act in ("CONFIRM", "REVIEW"):
        if not answer.get("answer"):
            raise AnswerError(f"{act} needs an `answer` field in the answer file")
        append_knowledge_row(
            root,
            {
                "ask_id": ask_id,
                "act": act,
                "answer": answer["answer"],
                "date": today,
                "provenance": answer.get("provenance", "engineer, via write answer"),
            },
        )
        mark_answered(root, ask_id, act, "knowledge.yaml", today=today)
        return "se-buddy/knowledge.yaml"

    if act == "PRIORITISE":
        sequence = answer.get("sequence")
        if not sequence:
            raise AnswerError("PRIORITISE needs a `sequence` list of ask ids in the answer file")
        for position, named_id in enumerate(sequence, start=1):
            if get_ask(root, named_id) is None:
                raise AnswerError(f"{named_id!r} in the sequence is not a known ask")
            set_sequence(root, named_id, position)
        mark_answered(root, ask_id, act, "sequence: on each named ask", today=today)
        return "sequence: on each named ask"

    if act == "DRAW":
        raise AnswerError(
            "DRAW closes by ticking a CHANGE-nnnn.followup.yaml entry, and no "
            "followup checklist can exist yet - it's created by `write apply`, "
            "which needs the modelling write path (not built in this phase)."
        )

    if act in ("DECIDE", "SUPPLY"):
        verb = "write memory" if act == "DECIDE" else "write memory or write register"
        raise AnswerError(
            f"{act} is refused here - its product is a record with its own schema "
            f"(spec Sec.7.3). Use `se-buddy {verb}` instead."
        )

    if act == "AUTHORISE":
        raise AnswerError(
            "AUTHORISE is refused here - it lands in CHANGE-nnnn.authority via "
            "`se-buddy write apply CP-nnnn --authorized-by \"...\"`, a different verb."
        )

    raise AnswerError(f"unknown act {act!r} on {ask_id}")


def run(args) -> int:
    answer_path = Path(args.answer_file)
    if not answer_path.exists():
        print(f"se-buddy: {answer_path} does not exist")
        return 1
    answer = yaml.safe_load(answer_path.read_text(encoding="utf-8")) or {}

    try:
        confirm(f"About to answer {args.ask_id}")
    except GateRefused as exc:
        print(f"se-buddy: {exc}")
        return 1

    try:
        landed = answer_ask(Path.cwd(), args.ask_id, answer)
    except AnswerError as exc:
        print(f"se-buddy: {exc}")
        return 1

    print(f"{args.ask_id} answered - landed in {landed}")
    return 0
