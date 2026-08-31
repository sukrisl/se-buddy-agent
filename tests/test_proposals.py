import tempfile
import unittest
from pathlib import Path

from se_buddy.proposals import ProposalError, file_cp, load_cp

VALID_CP = {
    "claim": "extract retry logic into a shared component",
    "tier": "judgement",
    "date": "2026-08-31",
    "supersedes": [],
    "intent": "reduce duplicated retry handling",
    "facts": ["three components implement near-identical retry loops"],
    "assumptions": [],
    "unknowns": ["whether all three retry policies are actually equivalent"],
    "affected_elements": ["0d2edb8f-fa34-4e73-89ec-fb9a63001440"],
    "proposed_changes": [{"parent": "!uuid 0d2edb8f-fa34-4e73-89ec-fb9a63001440", "extend": {}}],
    "alternatives": "leave as-is: one line, rejected - triples the maintenance surface",
    "verification_implications": "existing retry tests must still pass unmodified",
    "open_questions": [],
    "diagram_cost": 0,
    "provenance": "spotted during arch-review",
}


class TestFileCp(unittest.TestCase):
    def _fixture_aird(self, root: Path) -> Path:
        aird = root / "model.aird"
        aird.write_text("x", encoding="utf-8")
        return aird

    def test_allocates_id_and_captures_model_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aird = self._fixture_aird(root)
            cp = file_cp(root, dict(VALID_CP), aird)
            self.assertEqual(cp["id"], "CP-0001")
            self.assertTrue(cp["model_hash"])
            self.assertEqual(load_cp(root, "CP-0001")["intent"], VALID_CP["intent"])

    def test_second_cp_increments(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aird = self._fixture_aird(root)
            first = file_cp(root, dict(VALID_CP), aird)
            second = file_cp(root, dict(VALID_CP), aird)
            self.assertEqual(first["id"], "CP-0001")
            self.assertEqual(second["id"], "CP-0002")

    def test_missing_facts_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aird = self._fixture_aird(root)
            cp = dict(VALID_CP)
            del cp["facts"]
            with self.assertRaises(ProposalError):
                file_cp(root, cp, aird)

    def test_supplying_an_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aird = self._fixture_aird(root)
            with self.assertRaises(ProposalError):
                file_cp(root, {**VALID_CP, "id": "CP-0001"}, aird)


class TestLoadCp(unittest.TestCase):
    def test_missing_cp_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(load_cp(Path(tmp), "CP-9999"))


if __name__ == "__main__":
    unittest.main()
