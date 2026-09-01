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
    def test_two_gaps_sharing_an_object_allocate_one_ask(self):
        """One open ask per object, even when the caller breaks that rule.

        `open_objects` was computed once before the loop, so duplicate-object
        gaps each got their own id - and every later run then matched only
        the first, leaving the rest permanently unupdatable. Seen for real:
        one unfinished `domain.md` produced ASK-0009 and ASK-0010.
        """
        with tempfile.TemporaryDirectory() as tmp:
            duplicate = ProfileGap(object=GAP_B.object, done_when="a second finding")

            asks = sync_profile_gaps(Path(tmp), [GAP_B, duplicate], today="2026-08-31")

            self.assertEqual(len(asks), 1)

    def test_a_duplicate_object_does_not_accumulate_across_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            duplicate = ProfileGap(object=GAP_B.object, done_when="a second finding")
            sync_profile_gaps(root, [GAP_B, duplicate], today="2026-08-31")
            asks = sync_profile_gaps(root, [GAP_B, duplicate], today="2026-09-01")
            self.assertEqual(len(asks), 1)

    def test_detail_is_not_persisted_onto_the_ask(self):
        # An ask is written once and keeps its text, so anything that varies
        # run to run must stay off it or it silently goes stale.
        with tempfile.TemporaryDirectory() as tmp:
            gap = ProfileGap(
                object=GAP_B.object, done_when="it is complete", detail=("3 placeholders",)
            )
            asks = sync_profile_gaps(Path(tmp), [gap], today="2026-08-31")
            self.assertNotIn("detail", next(iter(asks.values())))

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
