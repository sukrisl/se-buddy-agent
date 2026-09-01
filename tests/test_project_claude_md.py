import tempfile
import unittest
from pathlib import Path

from se_buddy.project_claude_md import BEGIN, END, apply_block, render, write

PROFILE = {
    "model_path": "model.capella",
    "aird_path": "model.aird",
    "capella_version": "7.0.1",
    "project_name": "IoT Platform",
}


class TestRender(unittest.TestCase):
    def test_a_complete_profile_reaches_the_block(self):
        text = render(PROFILE)
        self.assertIn("IoT Platform", text)
        self.assertIn("model.capella", text)
        self.assertIn("7.0.1", text)

    def test_an_absent_profile_says_so_rather_than_inventing_a_project(self):
        text = render(None)
        self.assertIn("not complete yet", text)
        self.assertIn("/se-buddy:project-init", text)

    def test_a_partial_profile_degrades_without_naming_files_it_does_not_know(self):
        text = render({"project_name": "IoT Platform"})
        self.assertIn("IoT Platform", text)
        self.assertIn("the `.capella` or `.aird` files", text)

    def test_the_block_is_delimited_at_both_ends(self):
        text = render(PROFILE)
        self.assertIn(BEGIN, text)
        self.assertIn(END, text)


class TestApplyBlock(unittest.TestCase):
    def test_no_existing_file_creates_one_holding_only_the_block(self):
        block = render(PROFILE)
        text, action = apply_block(None, block)
        self.assertEqual(action, "created")
        self.assertEqual(text, block)

    def test_an_existing_block_is_replaced_in_place(self):
        existing = f"# My project\n\nSome prose.\n\n{BEGIN}\nSTALE_MARKER\n{END}\n\nTrailing prose.\n"
        text, action = apply_block(existing, render(PROFILE))

        self.assertEqual(action, "updated in place")
        self.assertNotIn("STALE_MARKER", text)
        self.assertIn("Some prose.", text)
        self.assertIn("Trailing prose.", text)

    def test_a_file_without_the_block_is_appended_to_never_overwritten(self):
        existing = "# My project\n\nRules the engineer wrote themselves.\n"
        text, action = apply_block(existing, render(PROFILE))

        self.assertEqual(action, "appended")
        self.assertTrue(text.startswith(existing))
        self.assertIn(BEGIN, text)

    def test_regenerating_is_idempotent(self):
        block = render(PROFILE)
        once, _ = apply_block("# Mine\n\nProse.\n", block)
        twice, action = apply_block(once, block)

        self.assertEqual(action, "updated in place")
        self.assertEqual(once, twice)
        self.assertEqual(twice.count(BEGIN), 1)

    def test_content_outside_the_block_survives_a_profile_change(self):
        first, _ = apply_block("# Mine\n\nKeep me.\n", render(PROFILE))
        second, _ = apply_block(first, render({**PROFILE, "project_name": "Renamed"}))

        self.assertIn("Keep me.", second)
        self.assertIn("Renamed", second)
        self.assertNotIn("IoT Platform", second)


class TestWrite(unittest.TestCase):
    def test_writes_claude_md_at_the_project_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path, action = write(root, PROFILE)
            self.assertEqual(path, root / "CLAUDE.md")
            self.assertEqual(action, "created")
            self.assertIn("IoT Platform", path.read_text(encoding="utf-8"))

    def test_a_second_write_does_not_duplicate_the_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, PROFILE)
            path, action = write(root, PROFILE)
            self.assertEqual(action, "updated in place")
            self.assertEqual(path.read_text(encoding="utf-8").count(BEGIN), 1)

    def test_an_engineers_own_claude_md_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "CLAUDE.md").write_text("# House rules\n\nAlways run make.\n", encoding="utf-8")

            write(root, PROFILE)

            text = (root / "CLAUDE.md").read_text(encoding="utf-8")
            self.assertIn("Always run make.", text)
            self.assertIn("IoT Platform", text)


if __name__ == "__main__":
    unittest.main()
