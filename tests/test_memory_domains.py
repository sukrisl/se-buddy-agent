import tempfile
import unittest
from pathlib import Path

from se_buddy.memory_domains import (
    MemoryDomainError,
    load_glossary,
    load_rows,
    load_viewpoints,
    upsert_glossary_entry,
    upsert_row,
    upsert_viewpoint,
)


class TestUpsertRow(unittest.TestCase):
    def test_new_principle_allocates_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            row = upsert_row(
                Path(tmp),
                "principles",
                {"statement": "prefer composition over inheritance", "provenance": "team", "status": "active"},
            )
            self.assertEqual(row["id"], "PRIN-0001")

    def test_second_assumption_increments(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = {"statement": "x", "provenance": "p", "status": "unverified"}
            a = upsert_row(root, "assumptions", dict(base))
            b = upsert_row(root, "assumptions", dict(base))
            self.assertEqual(a["id"], "ASSUME-0001")
            self.assertEqual(b["id"], "ASSUME-0002")

    def test_update_existing_row_by_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            created = upsert_row(root, "assumptions", {"statement": "x", "provenance": "p", "status": "unverified"})
            updated = upsert_row(root, "assumptions", {**created, "status": "confirmed"})
            self.assertEqual(updated["id"], created["id"])
            rows = load_rows(root, "assumptions")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["status"], "confirmed")

    def test_missing_statement_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(MemoryDomainError):
                upsert_row(Path(tmp), "principles", {"provenance": "p", "status": "active"})

    def test_unknown_domain_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(MemoryDomainError):
                upsert_row(Path(tmp), "bogus", {"statement": "x"})

    def test_update_nonexistent_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(MemoryDomainError):
                upsert_row(Path(tmp), "principles", {"id": "PRIN-9999", "statement": "x"})


class TestUpsertViewpoint(unittest.TestCase):
    def test_new_viewpoint_requires_design_rules_and_priority(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(MemoryDomainError):
                upsert_viewpoint(Path(tmp), {"name": "safety"})

    def test_valid_viewpoint_is_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            upsert_viewpoint(root, {"name": "safety", "design_rules": ["no SPOF"], "priority": 1})
            viewpoints = load_viewpoints(root)
            self.assertEqual(len(viewpoints), 1)
            self.assertEqual(viewpoints[0]["priority"], 1)

    def test_upsert_by_name_updates_in_place(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            upsert_viewpoint(root, {"name": "safety", "design_rules": ["rule a"], "priority": 1})
            upsert_viewpoint(root, {"name": "safety", "design_rules": ["rule a", "rule b"], "priority": 2})
            viewpoints = load_viewpoints(root)
            self.assertEqual(len(viewpoints), 1)
            self.assertEqual(viewpoints[0]["priority"], 2)


class TestUpsertGlossaryEntry(unittest.TestCase):
    def test_requires_term_and_definition(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(MemoryDomainError):
                upsert_glossary_entry(Path(tmp), {"term": "Arcadia"})

    def test_valid_entry_upserts_by_term(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            upsert_glossary_entry(root, {"term": "Arcadia", "definition": "the method"})
            upsert_glossary_entry(root, {"term": "Arcadia", "definition": "the method, v2"})
            entries = load_glossary(root)
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["definition"], "the method, v2")


if __name__ == "__main__":
    unittest.main()
