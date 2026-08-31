import tempfile
import unittest
from pathlib import Path

from se_buddy.ask_store import (
    all_asks,
    get_ask,
    mark_answered,
    open_asks,
    set_sequence,
    sync_profile_gaps,
)
from se_buddy.profile import ProfileGap

GAP_A = ProfileGap(object="se-buddy/profile.yaml", done_when="it exists")
GAP_B = ProfileGap(object="se-buddy/domain.md", done_when="it exists")


class TestSyncProfileGaps(unittest.TestCase):
    def test_first_sync_allocates_stable_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asks = sync_profile_gaps(root, [GAP_A, GAP_B], today="2026-08-31")
            self.assertEqual(len(asks), 2)
            self.assertEqual(set(a["object"] for a in asks.values()), {GAP_A.object, GAP_B.object})

    def test_second_sync_with_same_gaps_does_not_reallocate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = sync_profile_gaps(root, [GAP_A], today="2026-08-31")
            second = sync_profile_gaps(root, [GAP_A], today="2026-09-01")
            self.assertEqual(set(first.keys()), set(second.keys()))

    def test_cleared_gap_auto_resolves(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sync_profile_gaps(root, [GAP_A, GAP_B], today="2026-08-31")
            after = sync_profile_gaps(root, [GAP_A], today="2026-09-01")  # GAP_B cleared
            resolved = [a for a in after.values() if a["object"] == GAP_B.object][0]
            self.assertIsNotNone(resolved["answered"])
            self.assertEqual(resolved["answered"]["act"], "auto-resolved")
            self.assertEqual(len(open_asks(root)), 1)

    def test_regressed_gap_gets_a_new_id_not_the_old_one(self):
        # spec Sec.6.1: "history is superseded, never rewritten" - a
        # re-opened gap is a new ask, the old resolved one stays as-is.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = sync_profile_gaps(root, [GAP_A], today="2026-08-31")
            first_id = next(iter(first))
            sync_profile_gaps(root, [], today="2026-09-01")  # resolved
            third = sync_profile_gaps(root, [GAP_A], today="2026-09-02")  # regressed
            open_now = open_asks(root)
            self.assertEqual(len(open_now), 1)
            self.assertNotIn(first_id, open_now)
            self.assertEqual(all_asks(root)[first_id]["answered"]["act"], "auto-resolved")


class TestMarkAnswered(unittest.TestCase):
    def test_marks_answered_and_leaves_open_asks_correct(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asks = sync_profile_gaps(root, [GAP_A], today="2026-08-31")
            ask_id = next(iter(asks))
            mark_answered(root, ask_id, "CONFIRM", "knowledge.yaml", today="2026-09-01")
            self.assertEqual(open_asks(root), {})
            self.assertEqual(get_ask(root, ask_id)["answered"]["act"], "CONFIRM")

    def test_unknown_id_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(KeyError):
                mark_answered(Path(tmp), "ASK-9999", "CONFIRM", "knowledge.yaml")


class TestSetSequence(unittest.TestCase):
    def test_sets_sequence_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asks = sync_profile_gaps(root, [GAP_A], today="2026-08-31")
            ask_id = next(iter(asks))
            set_sequence(root, ask_id, 1)
            self.assertEqual(get_ask(root, ask_id)["sequence"], 1)


if __name__ == "__main__":
    unittest.main()
