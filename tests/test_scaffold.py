import tempfile
import unittest
from pathlib import Path

from se_buddy.profile import check_completeness
from se_buddy.scaffold import ScaffoldError, available_domain_packs, scaffold_profile


class TestScaffoldProfile(unittest.TestCase):
    def test_scaffolds_all_four_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            written = scaffold_profile(root, domain_pack="generic")
            self.assertEqual(len(written), 4)
            for path in written:
                self.assertTrue(path.exists())

    def test_unknown_domain_pack_is_reported_not_invented(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ScaffoldError):
                scaffold_profile(Path(tmp), domain_pack="does-not-exist")

    def test_refuses_to_overwrite_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scaffold_profile(root, domain_pack="generic")
            with self.assertRaises(ScaffoldError):
                scaffold_profile(root, domain_pack="generic")

    def test_force_does_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scaffold_profile(root, domain_pack="generic")
            # should not raise
            scaffold_profile(root, domain_pack="generic", force=True)

    def test_scaffolded_profile_still_reports_gaps_since_its_a_skeleton(self):
        # Scaffolding creates the files, not their content - a freshly
        # scaffolded profile has placeholders, not real answers, so
        # completeness is still open (spec Sec.5.3's four requirements are
        # about content, e.g. `capella_version` being set, not just
        # file existence for profile.yaml specifically).
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scaffold_profile(root, domain_pack="generic")
            gaps = check_completeness(root)
            self.assertTrue(any("profile.yaml" in g.object for g in gaps))
            self.assertTrue(any("viewpoints.yaml" in g.object for g in gaps))


class TestAvailableDomainPacks(unittest.TestCase):
    def test_includes_shipped_packs(self):
        packs = available_domain_packs()
        self.assertIn("generic", packs)
        self.assertIn("aerospace-arp4754a", packs)


if __name__ == "__main__":
    unittest.main()
