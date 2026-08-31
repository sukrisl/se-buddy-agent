import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from se_buddy.atomic_write import atomic_write_text


class TestAtomicWriteText(unittest.TestCase):
    def test_writes_the_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "record.yaml"
            atomic_write_text(path, "hello")
            self.assertEqual(path.read_text(encoding="utf-8"), "hello")

    def test_overwrites_existing_content_fully(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "record.yaml"
            path.write_text("a much longer original line of content", encoding="utf-8")
            atomic_write_text(path, "short")
            self.assertEqual(path.read_text(encoding="utf-8"), "short")

    def test_leaves_the_original_untouched_if_the_write_fails(self):
        """The regression this exists for: a crash mid-write must never
        leave a truncated file in place of the original.
        """
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "record.yaml"
            path.write_text("original content", encoding="utf-8")

            with patch("os.replace", side_effect=OSError("simulated crash")):
                with self.assertRaises(OSError):
                    atomic_write_text(path, "new content")

            self.assertEqual(path.read_text(encoding="utf-8"), "original content")
            leftover_temp_files = [p for p in Path(tmp).iterdir() if p.name != "record.yaml"]
            self.assertEqual(leftover_temp_files, [])

    def test_no_temp_file_left_behind_on_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "record.yaml"
            atomic_write_text(path, "hello")
            self.assertEqual(list(Path(tmp).iterdir()), [path])


if __name__ == "__main__":
    unittest.main()
