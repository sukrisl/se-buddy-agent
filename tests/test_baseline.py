import tempfile
import unittest
from pathlib import Path

from se_buddy.ask_store import sync_profile_gaps
from se_buddy.baseline import build_manifest, load_baseline, write_baseline
from se_buddy.profile import ProfileGap
from se_buddy.registers import upsert_row


class TestBuildManifest(unittest.TestCase):
    def _fixture_model_files(self, root: Path) -> Path:
        aird = root / "model.aird"
        aird.write_text("aird content", encoding="utf-8")
        (root / "model.capella").write_text("capella content", encoding="utf-8")
        return aird

    def test_manifest_has_all_four_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aird = self._fixture_model_files(root)
            manifest = build_manifest(root, aird, today="2026-08-31")
            self.assertEqual(manifest["date"], "2026-08-31")
            self.assertTrue(manifest["model_hash"])
            self.assertIn("risks-system", manifest["registers"])
            self.assertEqual(manifest["open_ask_ids"], [])

    def test_manifest_includes_register_row_statuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aird = self._fixture_model_files(root)
            row = upsert_row(
                root,
                "risks-system",
                {
                    "claim": "x",
                    "status": "open",
                    "owner": "o",
                    "provenance": "p",
                    "links": [],
                    "likelihood": "low",
                    "impact": "low",
                    "treatment": "accept",
                },
            )
            manifest = build_manifest(root, aird, today="2026-08-31")
            self.assertEqual(manifest["registers"]["risks-system"][row["id"]], "open")

    def test_manifest_includes_open_ask_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aird = self._fixture_model_files(root)
            sync_profile_gaps(root, [ProfileGap(object="x", done_when="y")], today="2026-08-31")
            manifest = build_manifest(root, aird, today="2026-08-31")
            self.assertEqual(len(manifest["open_ask_ids"]), 1)


class TestWriteAndLoadBaseline(unittest.TestCase):
    def test_round_trips(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aird = root / "model.aird"
            aird.write_text("x", encoding="utf-8")
            write_baseline(root, "pdr", aird, today="2026-08-31")
            loaded = load_baseline(root, "pdr")
            self.assertEqual(loaded["date"], "2026-08-31")

    def test_missing_baseline_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(load_baseline(Path(tmp), "does-not-exist"))


if __name__ == "__main__":
    unittest.main()
