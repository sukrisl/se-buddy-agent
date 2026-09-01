import tempfile
import unittest
from pathlib import Path

import yaml

from se_buddy.profile import (
    ProfileWriteError,
    check_completeness,
    profile_dir,
    render_profile,
    write_domain,
    write_profile,
)
from tests import complete_domain_pack

FIELDS = {
    "model_path": "model.capella",
    "aird_path": "model.aird",
    "capella_version": "7.0.1",
    "project_name": "IoT Platform",
}


def _root(base: Path) -> Path:
    (base / "model.capella").write_text("<project/>", encoding="utf-8")
    (base / "model.aird").write_text("<aird/>", encoding="utf-8")
    return base


class TestRenderProfile(unittest.TestCase):
    def test_the_rendered_file_parses_back_to_the_same_four_values(self):
        parsed = yaml.safe_load(render_profile(FIELDS))
        for field, value in FIELDS.items():
            self.assertEqual(parsed[field], value)

    def test_a_two_part_version_stays_a_string_not_a_float(self):
        # `capella_version: 7.0` is a float to YAML and `7.0.1` is not, so a
        # project on a two-part version would silently change type.
        parsed = yaml.safe_load(render_profile({**FIELDS, "capella_version": "7.0"}))
        self.assertEqual(parsed["capella_version"], "7.0")
        self.assertIsInstance(parsed["capella_version"], str)

    def test_the_header_explains_how_the_file_came_to_say_this(self):
        self.assertIn("TTY-gated", render_profile(FIELDS))


class TestWriteProfile(unittest.TestCase):
    def test_writes_a_file_that_clears_every_profile_yaml_gap(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _root(Path(tmp))
            write_profile(root, FIELDS)
            objects = {g.object for g in check_completeness(root)}
            self.assertNotIn("se-buddy/profile.yaml", objects)
            for field in FIELDS:
                self.assertNotIn(f"se-buddy/profile.yaml: {field}", objects)

    def test_creates_the_profile_directory_if_it_is_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _root(Path(tmp))
            self.assertFalse(profile_dir(root).exists())
            self.assertTrue(write_profile(root, FIELDS).exists())

    def test_a_missing_field_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _root(Path(tmp))
            with self.assertRaises(ProfileWriteError):
                write_profile(root, {k: v for k, v in FIELDS.items() if k != "project_name"})

    def test_an_empty_field_is_refused_the_same_as_a_missing_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _root(Path(tmp))
            with self.assertRaises(ProfileWriteError):
                write_profile(root, {**FIELDS, "project_name": "   "})

    def test_a_model_path_that_does_not_resolve_is_refused(self):
        # Sec.5.3 asks for resolvable paths specifically: a profile naming a
        # file that isn't there fails later, further from the cause.
        with tempfile.TemporaryDirectory() as tmp:
            root = _root(Path(tmp))
            with self.assertRaises(ProfileWriteError) as caught:
                write_profile(root, {**FIELDS, "model_path": "absent.capella"})
            self.assertIn("does not resolve", str(caught.exception))

    def test_a_model_path_with_the_wrong_suffix_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _root(Path(tmp))
            with self.assertRaises(ProfileWriteError) as caught:
                write_profile(root, {**FIELDS, "model_path": "model.aird"})
            self.assertIn(".capella", str(caught.exception))

    def test_nothing_is_written_when_validation_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _root(Path(tmp))
            with self.assertRaises(ProfileWriteError):
                write_profile(root, {**FIELDS, "model_path": "absent.capella"})
            self.assertFalse((profile_dir(root) / "profile.yaml").exists())


class TestWriteDomain(unittest.TestCase):
    def test_writes_a_pack_that_clears_every_domain_md_gap(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_domain(root, complete_domain_pack())
            objects = [g.object for g in check_completeness(root)]
            self.assertNotIn("se-buddy/domain.md", objects)

    def test_refuses_a_pack_missing_a_required_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ProfileWriteError) as caught:
                write_domain(Path(tmp), "# Domain pack: example\n")
            self.assertIn("Sec.5.4", str(caught.exception))

    def test_accepts_a_structurally_complete_pack_that_still_has_placeholders(self):
        # The heuristic reports; it must not refuse. `write-domain`'s CLI
        # surfaces these in the gate prompt for a human to judge instead.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            written = write_domain(root, complete_domain_pack() + "\n- <leftover>\n")
            self.assertTrue(written.exists())

    def test_a_pack_written_without_a_trailing_newline_gets_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            written = write_domain(root, complete_domain_pack().rstrip("\n"))
            self.assertTrue(written.read_text(encoding="utf-8").endswith("\n"))


class TestCompletenessOverContent(unittest.TestCase):
    def test_the_shipped_template_no_longer_counts_as_a_domain_pack(self):
        # The regression this whole change exists for: scaffolding then
        # doing nothing used to report the profile complete.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdir = profile_dir(root)
            pdir.mkdir(parents=True)
            (pdir / "domain.md").write_text(
                Path("templates/domains/generic.md").read_text(encoding="utf-8"), encoding="utf-8"
            )
            gaps = [g for g in check_completeness(root) if g.object == "se-buddy/domain.md"]
            self.assertTrue(gaps)

    def test_at_most_one_gap_per_object(self):
        """`ask_store` keys an ask on `object` alone, so two gaps sharing one
        object become two asks for one condition that can never afterwards be
        updated or resolved apart. Caught against the real project, which grew
        ASK-0009 and ASK-0010 for a single unfinished `domain.md`."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdir = profile_dir(root)
            pdir.mkdir(parents=True)
            # The shipped template trips several findings at once - a missing
            # heading, the preamble, and a fistful of placeholders.
            (pdir / "domain.md").write_text(
                Path("templates/domains/generic.md").read_text(encoding="utf-8"), encoding="utf-8"
            )

            objects = [g.object for g in check_completeness(root)]

            self.assertEqual(len(objects), len(set(objects)), objects)

    def test_the_domain_gap_states_an_invariant_and_carries_todays_evidence(self):
        # `done_when` is persisted once and keeps its text, so a count in it
        # would freeze. The varying part rides on `detail`, which is not.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdir = profile_dir(root)
            pdir.mkdir(parents=True)
            (pdir / "domain.md").write_text(
                complete_domain_pack() + "\n- <leftover>\n", encoding="utf-8"
            )

            gap = next(g for g in check_completeness(root) if g.object == "se-buddy/domain.md")

            self.assertNotIn("1 unreplaced", gap.done_when)
            self.assertIn("Sec.5.4", gap.done_when)
            self.assertTrue(any("<leftover>" in d for d in gap.detail))

    def test_domain_gaps_are_supply_asks_like_every_other_gap(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdir = profile_dir(root)
            pdir.mkdir(parents=True)
            (pdir / "domain.md").write_text("# Domain pack: example\n", encoding="utf-8")
            for gap in check_completeness(root):
                self.assertEqual(gap.act, "SUPPLY")


if __name__ == "__main__":
    unittest.main()
