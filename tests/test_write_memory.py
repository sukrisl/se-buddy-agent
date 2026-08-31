"""Tests the dispatch logic beneath the TTY gate directly, never `run()` -
same testing philosophy as tests/test_write_answer.py (spec Sec.2.3).
"""

import tempfile
import unittest
from pathlib import Path

from se_buddy.commands.write_memory import WriteMemoryError, write_content
from se_buddy.decisions import load_adr
from se_buddy.memory_domains import load_glossary, load_rows, load_viewpoints
from tests.test_decisions import VALID_ADR


class TestWriteContent(unittest.TestCase):
    def test_decisions_dispatches_to_file_adr(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            written = write_content(root, "decisions", dict(VALID_ADR))
            self.assertEqual(written["id"], "ADR-0001")
            self.assertIsNotNone(load_adr(root, "ADR-0001"))

    def test_decisions_without_authority_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            adr = dict(VALID_ADR)
            del adr["authority"]
            with self.assertRaises(WriteMemoryError):
                write_content(Path(tmp), "decisions", adr)

    def test_principles_dispatches_to_upsert_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            written = write_content(
                root, "principles", {"statement": "x", "provenance": "p", "status": "active"}
            )
            self.assertEqual(written["id"], "PRIN-0001")
            self.assertEqual(len(load_rows(root, "principles")), 1)

    def test_assumptions_dispatches_to_upsert_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            written = write_content(
                root, "assumptions", {"statement": "x", "provenance": "p", "status": "unverified"}
            )
            self.assertEqual(written["id"], "ASSUME-0001")

    def test_viewpoints_dispatches_to_upsert_viewpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_content(root, "viewpoints", {"name": "safety", "design_rules": ["x"], "priority": 1})
            self.assertEqual(len(load_viewpoints(root)), 1)

    def test_glossary_dispatches_to_upsert_glossary_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_content(root, "glossary", {"term": "Arcadia", "definition": "the method"})
            self.assertEqual(len(load_glossary(root)), 1)

    def test_knowledge_is_not_a_write_memory_domain(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(WriteMemoryError):
                write_content(Path(tmp), "knowledge", {"answer": "x"})


if __name__ == "__main__":
    unittest.main()
