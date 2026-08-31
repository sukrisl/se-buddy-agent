import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import se_buddy.changes as changes_module
from se_buddy.ask_store import sync_profile_gaps
from se_buddy.changes import (
    ChangeError,
    any_followup_open,
    change_path,
    file_change,
    find_followup_item,
    followup_all_ticked,
    followup_path,
    load_change,
    load_followup,
    mark_followup_item_done,
    open_followup_items,
)
from se_buddy.profile import ProfileGap

VALID_CHANGE = {
    "claim": "extracted retry logic into RetryPolicy",
    "tier": "judgement",
    "date": "2026-08-31",
    "supersedes": [],
    "proposal": "CP-0001",
    "authority": "engineer said: go ahead, 2026-08-31 standup",
    "diff_summary": "3 elements changed, 1 created",
    "validation_summary": "all six layers pass",
    "manual_followup": [],
}


class TestFileChange(unittest.TestCase):
    def test_writes_both_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            change = file_change(root, "CHANGE-0001", dict(VALID_CHANGE), [])
            self.assertEqual(change["id"], "CHANGE-0001")
            self.assertIsNotNone(load_change(root, "CHANGE-0001"))
            self.assertEqual(load_followup(root, "CHANGE-0001"), [])

    def test_followup_items_get_ask_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            followup = [
                {"object": "[LAB] diagram", "done_when": "RetryPolicy is drawn on it", "blocks": "nothing", "default": "none - this blocks"}
            ]
            file_change(root, "CHANGE-0001", dict(VALID_CHANGE), followup)
            items = load_followup(root, "CHANGE-0001")
            self.assertEqual(len(items), 1)
            self.assertTrue(items[0]["id"].startswith("ASK-"))
            self.assertEqual(items[0]["act"], "DRAW")

    def test_followup_ids_dont_collide_with_ask_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sync_profile_gaps(root, [ProfileGap(object="x", done_when="y")], today="2026-08-31")
            # ASK-0001 is now taken by the profile gap
            followup = [{"object": "o", "done_when": "d", "blocks": "b", "default": "n"}]
            file_change(root, "CHANGE-0001", dict(VALID_CHANGE), followup)
            items = load_followup(root, "CHANGE-0001")
            self.assertEqual(items[0]["id"], "ASK-0002")

    def test_missing_authority_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            change = dict(VALID_CHANGE)
            del change["authority"]
            with self.assertRaises(ChangeError):
                file_change(Path(tmp), "CHANGE-0001", change, [])

    def test_duplicate_change_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            file_change(root, "CHANGE-0001", dict(VALID_CHANGE), [])
            with self.assertRaises(ChangeError):
                file_change(root, "CHANGE-0001", dict(VALID_CHANGE), [])

    def test_crash_between_writes_leaves_the_followup_file_orphaned_and_blocking(self):
        """A code review found the two files written in the opposite
        order: change record first, then followup. A crash between them
        left a CHANGE on disk with no followup file at all, so
        `any_followup_open` (which only scans `*.followup.yaml`) saw
        nothing owed and would have let a later apply through with a real
        DRAW item silently lost. Followup is now written first, so the
        same crash instead leaves an orphaned followup file with no
        matching CHANGE yet - still detected and still blocking, the
        fail-safe direction.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            followup = [{"object": "o", "done_when": "d", "blocks": "b", "default": "n"}]
            target = change_path(root, "CHANGE-0001")
            original_atomic_write_text = changes_module.atomic_write_text

            def flaky_atomic_write_text(path, *args, **kwargs):
                if path == target:
                    raise RuntimeError("simulated crash")
                return original_atomic_write_text(path, *args, **kwargs)

            with patch.object(changes_module, "atomic_write_text", flaky_atomic_write_text):
                with self.assertRaises(RuntimeError):
                    file_change(root, "CHANGE-0001", dict(VALID_CHANGE), followup)

            self.assertTrue(followup_path(root, "CHANGE-0001").exists())
            self.assertIsNone(load_change(root, "CHANGE-0001"))
            self.assertTrue(any_followup_open(root))


class TestFollowupTracking(unittest.TestCase):
    def test_any_followup_open_true_until_ticked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            followup = [{"object": "o", "done_when": "d", "blocks": "b", "default": "n"}]
            file_change(root, "CHANGE-0001", dict(VALID_CHANGE), followup)
            self.assertTrue(any_followup_open(root))
            self.assertFalse(followup_all_ticked(root, "CHANGE-0001"))

            ask_id = load_followup(root, "CHANGE-0001")[0]["id"]
            mark_followup_item_done(root, "CHANGE-0001", ask_id, today="2026-09-01")

            self.assertFalse(any_followup_open(root))
            self.assertTrue(followup_all_ticked(root, "CHANGE-0001"))

    def test_find_followup_item_across_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            followup = [{"object": "o", "done_when": "d", "blocks": "b", "default": "n"}]
            file_change(root, "CHANGE-0001", dict(VALID_CHANGE), followup)
            ask_id = load_followup(root, "CHANGE-0001")[0]["id"]
            found = find_followup_item(root, ask_id)
            self.assertEqual(found[0], "CHANGE-0001")

    def test_open_followup_items_empty_when_none_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(open_followup_items(Path(tmp)), [])


if __name__ == "__main__":
    unittest.main()
