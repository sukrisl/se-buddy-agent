import shutil
import tempfile
import unittest
from pathlib import Path

import capellambse

from se_buddy.registers import upsert_row
from se_buddy.validate import (
    check_architectural,
    check_consistency,
    check_interface,
    check_representation,
    check_structural,
    check_traceability,
    run_all_layers,
    summarize,
)

FIXTURE_SOURCE = (
    Path(__file__).resolve().parents[1] / "vendor" / "py-capellambse" / "tests" / "data" / "models" / "test7_0"
)
HOGWARTS_LC_UUID = "0d2edb8f-fa34-4e73-89ec-fb9a63001440"


def _load_fixture_model(tmp: str):
    dest = Path(tmp) / "model"
    shutil.copytree(FIXTURE_SOURCE, dest)
    aird = next(dest.glob("*.aird"))
    return capellambse.MelodyModel(dest), Path(tmp)


class TestStructural(unittest.TestCase):
    def test_real_fixture_has_no_orphans(self):
        with tempfile.TemporaryDirectory() as tmp:
            model, _ = _load_fixture_model(tmp)
            findings = check_structural(model)
            self.assertTrue(all(f.severity == "PASS" for f in findings), findings)


class TestRepresentation(unittest.TestCase):
    def test_real_fixture_diagrams_all_resolve(self):
        with tempfile.TemporaryDirectory() as tmp:
            model, _ = _load_fixture_model(tmp)
            findings = check_representation(model)
            self.assertTrue(all(f.severity == "PASS" for f in findings), findings)


class TestInterface(unittest.TestCase):
    def test_real_fixture_has_unallocated_exchanges(self):
        # Confirmed directly against the real fixture: most functional and
        # component exchanges here carry no ExchangeItem - a real, non-
        # trivial WARN finding, not a contrived one.
        with tempfile.TemporaryDirectory() as tmp:
            model, _ = _load_fixture_model(tmp)
            findings = check_interface(model)
            self.assertTrue(any(f.severity == "WARN" for f in findings), findings)


class TestTraceability(unittest.TestCase):
    def test_no_requirements_reports_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            model, root = _load_fixture_model(tmp)
            findings = check_traceability(root, model)
            self.assertEqual(findings[0].severity, "UNKNOWN")

    def test_unverified_requirement_is_a_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            model, root = _load_fixture_model(tmp)
            upsert_row(
                root,
                "requirements",
                {"claim": "x", "status": "open", "owner": "o", "provenance": "p", "links": [], "statement": "x"},
            )
            findings = check_traceability(root, model)
            self.assertEqual(findings[0].severity, "WARN")

    def test_verified_requirement_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            model, root = _load_fixture_model(tmp)
            req = upsert_row(
                root,
                "requirements",
                {"claim": "x", "status": "open", "owner": "o", "provenance": "p", "links": [], "statement": "x"},
            )
            upsert_row(
                root,
                "verification",
                {
                    "claim": "verified by test",
                    "status": "closed",
                    "owner": "o",
                    "provenance": "p",
                    "links": [],
                    "method": "test",
                    "requirement_id": req["id"],
                },
            )
            findings = check_traceability(root, model)
            self.assertEqual(findings[0].severity, "PASS")


class TestConsistency(unittest.TestCase):
    def test_dangling_link_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            model, root = _load_fixture_model(tmp)
            upsert_row(
                root,
                "risks-system",
                {
                    "claim": "x", "status": "open", "owner": "o", "provenance": "p",
                    "links": ["not-a-real-uuid"], "likelihood": "low", "impact": "low", "treatment": "accept",
                },
            )
            findings = check_consistency(root, model)
            self.assertEqual(findings[0].severity, "ERROR")

    def test_real_link_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            model, root = _load_fixture_model(tmp)
            upsert_row(
                root,
                "risks-system",
                {
                    "claim": "x", "status": "open", "owner": "o", "provenance": "p",
                    "links": [HOGWARTS_LC_UUID], "likelihood": "low", "impact": "low", "treatment": "accept",
                },
            )
            findings = check_consistency(root, model)
            self.assertEqual(findings[0].severity, "PASS")


class TestArchitectural(unittest.TestCase):
    def test_no_viewpoints_reports_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            findings = check_architectural(Path(tmp))
            self.assertEqual(findings[0].severity, "UNKNOWN")


class TestRunAllLayers(unittest.TestCase):
    def test_covers_all_six_layers(self):
        with tempfile.TemporaryDirectory() as tmp:
            model, root = _load_fixture_model(tmp)
            findings = run_all_layers(root, model)
            self.assertEqual({f.layer for f in findings}, {
                "structural", "representation", "interface", "traceability", "consistency", "architectural",
            })


class TestSummarize(unittest.TestCase):
    def test_counts_by_severity(self):
        from se_buddy.validate import Finding

        findings = [Finding("structural", "PASS", "x"), Finding("interface", "WARN", "y"), Finding("interface", "WARN", "z")]
        self.assertEqual(summarize(findings), "1 PASS, 2 WARN")

    def test_empty_findings(self):
        self.assertEqual(summarize([]), "no findings")


if __name__ == "__main__":
    unittest.main()
