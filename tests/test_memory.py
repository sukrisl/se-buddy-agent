import tempfile
import unittest
from pathlib import Path

from se_buddy.memory import allocate_id, next_id, render_citation


class TestNextId(unittest.TestCase):
    def test_first_id_is_0001(self):
        self.assertEqual(next_id("ADR", []), "ADR-0001")

    def test_sequential_allocation(self):
        self.assertEqual(next_id("ADR", ["ADR-0001", "ADR-0002"]), "ADR-0003")

    def test_ignores_other_kinds(self):
        self.assertEqual(next_id("ASK", ["ADR-0001", "ASK-0004"]), "ASK-0005")

    def test_unknown_kind_rejected(self):
        with self.assertRaises(ValueError):
            next_id("BOGUS", [])

    def test_does_not_renumber_on_gaps(self):
        # id is stable for the life of the ask/record (spec Sec.9) - a
        # deleted ADR-0002 must not let a future ADR reuse its number.
        self.assertEqual(next_id("ADR", ["ADR-0001", "ADR-0005"]), "ADR-0006")


class TestAllocateId(unittest.TestCase):
    def test_scans_directory_for_existing_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "ADR-0001.yaml").write_text("x", encoding="utf-8")
            (directory / "ADR-0002.yaml").write_text("x", encoding="utf-8")
            self.assertEqual(allocate_id("ADR", directory), "ADR-0003")

    def test_missing_directory_starts_at_one(self):
        directory = Path(tempfile.gettempdir()) / "does-not-exist-se-buddy-test"
        self.assertEqual(allocate_id("ADR", directory), "ADR-0001")


class TestRenderCitation(unittest.TestCase):
    def test_renders_id_and_claim(self):
        self.assertEqual(
            render_citation("ADR-0007", "device owns schedule execution"),
            "ADR-0007 (device owns schedule execution)",
        )


if __name__ == "__main__":
    unittest.main()
