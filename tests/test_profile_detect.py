import tempfile
import unittest
from pathlib import Path

from se_buddy.profile_detect import detect

CAPELLA = """<?xml version="1.0" encoding="UTF-8"?>

<!--Capella_Version_7.0.1-->
<org.polarsys.capella.core.data.capellamodeller:Project xmi:version="2.0"/>
"""

AFM = """<?xml version="1.0" encoding="UTF-8"?>
<metadata:Metadata xmi:version="2.0">
  <viewpointReferences vpId="org.polarsys.capella.core.viewpoint" version="6.1.0"/>
</metadata:Metadata>
"""

DOT_PROJECT = """<?xml version="1.0" encoding="UTF-8"?>
<projectDescription>
\t<name>model-iot_platform</name>
\t<comment></comment>
</projectDescription>
"""


def _project(base: Path, *, capella=CAPELLA, afm=AFM, project=DOT_PROJECT, stem="model") -> Path:
    if capella is not None:
        (base / f"{stem}.capella").write_text(capella, encoding="utf-8")
    (base / f"{stem}.aird").write_text("<aird/>", encoding="utf-8")
    if afm is not None:
        (base / f"{stem}.afm").write_text(afm, encoding="utf-8")
    if project is not None:
        (base / ".project").write_text(project, encoding="utf-8")
    return base


class TestDetect(unittest.TestCase):
    def test_all_four_fields_come_from_the_projects_own_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _project(Path(tmp))
            found = detect(root)

            self.assertEqual(found.model_path.value, "model.capella")
            self.assertEqual(found.aird_path.value, "model.aird")
            self.assertEqual(found.capella_version.value, "7.0.1")
            self.assertEqual(found.project_name.value, "model-iot_platform")
            self.assertEqual(found.undetermined(), [])

    def test_the_version_marker_does_not_swallow_the_comment_terminator(self):
        # Found against a real model: a charset including `-` matched
        # "7.0.1--" out of `<!--Capella_Version_7.0.1-->`.
        with tempfile.TemporaryDirectory() as tmp:
            root = _project(Path(tmp))
            self.assertEqual(detect(root).capella_version.value, "7.0.1")

    def test_a_prerelease_version_survives(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _project(Path(tmp), capella="<!--Capella_Version_7.1.0-RC2-->\n")
            self.assertEqual(detect(root).capella_version.value, "7.1.0-RC2")

    def test_the_afm_is_the_fallback_when_the_capella_has_no_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _project(Path(tmp), capella="<project/>\n")
            found = detect(root)
            self.assertEqual(found.capella_version.value, "6.1.0")
            self.assertIn(".afm", found.capella_version.provenance)

    def test_the_afm_fallback_ignores_the_xml_declarations_own_version(self):
        # Every .afm opens with `<?xml version="1.0" ...?>`; a bare
        # `version="..."` match returned that, which would have put
        # `capella_version: 1.0` into a real profile.
        with tempfile.TemporaryDirectory() as tmp:
            root = _project(Path(tmp), capella="<project/>\n")
            self.assertNotEqual(detect(root).capella_version.value, "1.0")

    def test_the_core_viewpoints_version_wins_over_other_referenced_ones(self):
        afm = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            "<metadata:Metadata>\n"
            '  <viewpointReferences vpId="org.polarsys.capella.vp.other" version="2.5.0"/>\n'
            '  <viewpointReferences vpId="org.polarsys.capella.core.viewpoint" version="6.1.0"/>\n'
            "</metadata:Metadata>\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = _project(Path(tmp), capella="<project/>\n", afm=afm)
            self.assertEqual(detect(root).capella_version.value, "6.1.0")

    def test_two_capella_files_is_an_ambiguity_reported_not_guessed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _project(Path(tmp))
            (root / "other.capella").write_text(CAPELLA, encoding="utf-8")

            found = detect(root)

            self.assertIsNone(found.model_path.value)
            self.assertIn("name the right one yourself", found.model_path.provenance)
            self.assertIn("model_path", found.undetermined())

    def test_a_missing_file_reports_why_rather_than_returning_a_guess(self):
        with tempfile.TemporaryDirectory() as tmp:
            found = detect(Path(tmp))
            self.assertEqual(found.undetermined(), ["model_path", "aird_path", "capella_version", "project_name"])
            self.assertIn("no *.capella", found.model_path.provenance)
            self.assertIn("no .project", found.project_name.provenance)

    def test_a_project_descriptor_without_a_name_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _project(Path(tmp), project="<projectDescription/>\n")
            found = detect(root)
            self.assertIsNone(found.project_name.value)
            self.assertIn("no <name>", found.project_name.provenance)

    def test_as_dict_omits_undetermined_fields_rather_than_nulling_them(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _project(Path(tmp), project=None)
            self.assertNotIn("project_name", detect(root).as_dict())

    def test_every_field_is_rendered_with_the_file_it_came_from(self):
        with tempfile.TemporaryDirectory() as tmp:
            rendered = detect(_project(Path(tmp))).rendered()
            self.assertEqual(len(rendered), 4)
            for line in rendered:
                self.assertIn("(from ", line)


if __name__ == "__main__":
    unittest.main()
