"""Tests the dispatch logic beneath the TTY gate directly (spec Sec.2.3:
"Tests exercise the layer beneath the gate directly") - never `run()`,
which is the gated CLI entry point and cannot run non-interactively by
design.
"""

import tempfile
import unittest
from pathlib import Path

from se_buddy.ask_store import get_ask, sync_profile_gaps
from se_buddy.changes import file_change, load_followup
from se_buddy.commands.write_answer import AnswerError, answer_ask
from se_buddy.knowledge import load_knowledge
from se_buddy.profile import ProfileGap

VALID_CHANGE = {
    "claim": "x",
    "tier": "judgement",
    "date": "2026-08-31",
    "supersedes": [],
    "proposal": None,
    "authority": "engineer said go",
    "diff_summary": "x",
    "validation_summary": "x",
    "manual_followup": [],
}


def _raise_one_ask(root: Path, act: str, object_: str = "test object") -> str:
    gap = ProfileGap(object=object_, done_when="test done_when", act=act)
    asks = sync_profile_gaps(root, [gap], today="2026-08-31")
    return next(iter(asks))


class TestConfirmReview(unittest.TestCase):
    def test_confirm_lands_in_knowledge_yaml(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ask_id = _raise_one_ask(root, "CONFIRM")
            landed = answer_ask(
                root, ask_id, {"answer": "yes, agreed", "provenance": "email"}, today="2026-09-01"
            )
            self.assertEqual(landed, "se-buddy/knowledge.yaml")
            rows = load_knowledge(root)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["ask_id"], ask_id)
            self.assertEqual(rows[0]["answer"], "yes, agreed")
            self.assertIsNotNone(get_ask(root, ask_id)["answered"])

    def test_confirm_without_answer_field_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ask_id = _raise_one_ask(root, "CONFIRM")
            with self.assertRaises(AnswerError):
                answer_ask(root, ask_id, {})

    def test_review_also_lands_in_knowledge_yaml(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ask_id = _raise_one_ask(root, "REVIEW")
            answer_ask(root, ask_id, {"answer": "accepted as-is"})
            self.assertEqual(len(load_knowledge(root)), 1)


class TestPrioritise(unittest.TestCase):
    def test_sets_sequence_on_named_asks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # all three must be raised in one sync call - sync_profile_gaps
            # reconciles against the *full* current gap list each time, so
            # raising them one at a time would auto-resolve the earlier ones.
            gaps = [
                ProfileGap(object="object-a", done_when="x", act="SUPPLY"),
                ProfileGap(object="object-b", done_when="x", act="SUPPLY"),
                ProfileGap(object="sequencing question", done_when="x", act="PRIORITISE"),
            ]
            asks = sync_profile_gaps(root, gaps, today="2026-08-31")
            by_object = {a["object"]: aid for aid, a in asks.items()}
            a, b, prioritise_ask = by_object["object-a"], by_object["object-b"], by_object["sequencing question"]
            answer_ask(root, prioritise_ask, {"sequence": [b, a]})
            self.assertEqual(get_ask(root, b)["sequence"], 1)
            self.assertEqual(get_ask(root, a)["sequence"], 2)
            self.assertIsNotNone(get_ask(root, prioritise_ask)["answered"])

    def test_unknown_ask_in_sequence_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prioritise_ask = _raise_one_ask(root, "PRIORITISE")
            with self.assertRaises(AnswerError):
                answer_ask(root, prioritise_ask, {"sequence": ["ASK-9999"]})


class TestDraw(unittest.TestCase):
    def test_draw_ticks_the_matching_followup_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            followup = [{"object": "o", "done_when": "drawn on the diagram", "blocks": "b", "default": "n"}]
            file_change(root, "CHANGE-0001", dict(VALID_CHANGE), followup)
            ask_id = load_followup(root, "CHANGE-0001")[0]["id"]

            landed = answer_ask(root, ask_id, {})

            self.assertEqual(landed, "se-buddy/changes/CHANGE-0001.followup.yaml")
            item = load_followup(root, "CHANGE-0001")[0]
            self.assertIsNotNone(item["answered"])
            self.assertEqual(item["answered"]["act"], "DRAW")

    def test_already_ticked_draw_item_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            followup = [{"object": "o", "done_when": "d", "blocks": "b", "default": "n"}]
            file_change(root, "CHANGE-0001", dict(VALID_CHANGE), followup)
            ask_id = load_followup(root, "CHANGE-0001")[0]["id"]
            answer_ask(root, ask_id, {})
            with self.assertRaises(AnswerError):
                answer_ask(root, ask_id, {})

    def test_draw_ask_not_in_any_followup_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(AnswerError):
                answer_ask(Path(tmp), "ASK-9999", {})


class TestRefusedActs(unittest.TestCase):
    def test_supply_is_refused_names_write_memory_or_register(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ask_id = _raise_one_ask(root, "SUPPLY")
            with self.assertRaises(AnswerError) as ctx:
                answer_ask(root, ask_id, {})
            self.assertIn("write memory", str(ctx.exception))
            self.assertIn("write register", str(ctx.exception))

    def test_decide_is_refused_names_write_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ask_id = _raise_one_ask(root, "DECIDE")
            with self.assertRaises(AnswerError) as ctx:
                answer_ask(root, ask_id, {})
            self.assertIn("write memory", str(ctx.exception))

    def test_authorise_is_refused_names_write_apply(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ask_id = _raise_one_ask(root, "AUTHORISE")
            with self.assertRaises(AnswerError) as ctx:
                answer_ask(root, ask_id, {})
            self.assertIn("write apply", str(ctx.exception))


class TestGeneralFailures(unittest.TestCase):
    def test_unknown_ask_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(AnswerError):
                answer_ask(Path(tmp), "ASK-9999", {"answer": "x"})

    def test_already_answered_ask_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ask_id = _raise_one_ask(root, "CONFIRM")
            answer_ask(root, ask_id, {"answer": "yes"})
            with self.assertRaises(AnswerError):
                answer_ask(root, ask_id, {"answer": "yes again"})


if __name__ == "__main__":
    unittest.main()
