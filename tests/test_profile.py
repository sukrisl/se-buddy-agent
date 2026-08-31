import tempfile
import unittest
from pathlib import Path

from se_buddy.profile import check_completeness, profile_dir


class TestCheckCompleteness(unittest.TestCase):
    def test_missing_everything_reports_four_top_level_gaps(self):
        with tempfile.TemporaryDirectory() as tmp:
            gaps = check_completeness(Path(tmp))
            objects = {g.object for g in gaps}
            self.assertIn("se-buddy/profile.yaml", objects)
            self.assertIn("se-buddy/domain.md", objects)
            self.assertIn("se-buddy/viewpoints.yaml", objects)
            self.assertIn("se-buddy/principles.yaml", objects)
            for gap in gaps:
                self.assertEqual(gap.act, "SUPPLY")

    def test_complete_profile_reports_no_gaps(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdir = profile_dir(root)
            pdir.mkdir()
            (pdir / "profile.yaml").write_text(
                "model_path: model.capella\n"
                "aird_path: model.aird\n"
                "capella_version: '7.0.1'\n"
                "project_name: Example\n",
                encoding="utf-8",
            )
            (pdir / "domain.md").write_text("# Domain\n", encoding="utf-8")
            (pdir / "viewpoints.yaml").write_text(
                "viewpoints:\n"
                "  - name: safety\n"
                "    design_rules: [\"no single point of failure\"]\n"
                "    priority: 1\n",
                encoding="utf-8",
            )
            (pdir / "principles.yaml").write_text("principles: []\n", encoding="utf-8")

            self.assertEqual(check_completeness(root), [])

    def test_viewpoint_missing_priority_is_a_gap(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdir = profile_dir(root)
            pdir.mkdir()
            (pdir / "viewpoints.yaml").write_text(
                "viewpoints:\n"
                "  - name: safety\n"
                "    design_rules: [\"no single point of failure\"]\n",
                encoding="utf-8",
            )
            gaps = check_completeness(root)
            self.assertTrue(any("safety" in g.object for g in gaps))

    def test_principles_file_without_key_is_a_gap(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdir = profile_dir(root)
            pdir.mkdir()
            (pdir / "principles.yaml").write_text("# nothing yet\n", encoding="utf-8")
            gaps = check_completeness(root)
            self.assertTrue(any(g.object == "se-buddy/principles.yaml" for g in gaps))


if __name__ == "__main__":
    unittest.main()
