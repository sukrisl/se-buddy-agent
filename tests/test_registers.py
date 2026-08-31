import tempfile
import unittest
from pathlib import Path

from se_buddy.registers import (
    RegisterError,
    find_row,
    find_rows_linking,
    load_register,
    upsert_row,
)


class TestUpsertRow(unittest.TestCase):
    def test_new_row_allocates_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            row = upsert_row(
                root,
                "risks-system",
                {
                    "claim": "single point of failure in retry logic",
                    "status": "identified",
                    "owner": "engineer",
                    "provenance": "spotted during arch-transition",
                    "links": ["0d2edb8f-fa34-4e73-89ec-fb9a63001440"],
                    "likelihood": "medium",
                    "impact": "high",
                    "treatment": "mitigate",
                },
            )
            self.assertEqual(row["id"], "RISKSYS-0001")

    def test_second_row_increments(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = {
                "claim": "x",
                "status": "identified",
                "owner": "o",
                "provenance": "p",
                "links": [],
                "likelihood": "low",
                "impact": "low",
                "treatment": "accept",
            }
            row1 = upsert_row(root, "risks-project", dict(base))
            row2 = upsert_row(root, "risks-project", dict(base))
            self.assertEqual(row1["id"], "RISKPRJ-0001")
            self.assertEqual(row2["id"], "RISKPRJ-0002")

    def test_update_existing_row_by_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = {
                "claim": "x",
                "status": "identified",
                "owner": "o",
                "provenance": "p",
                "links": [],
                "likelihood": "low",
                "impact": "low",
                "treatment": "accept",
            }
            created = upsert_row(root, "risks-system", dict(base))
            updated = upsert_row(root, "risks-system", {**created, "status": "closed"})
            self.assertEqual(updated["id"], created["id"])
            self.assertEqual(updated["status"], "closed")
            rows = load_register(root, "risks-system")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[created["id"]]["status"], "closed")

    def test_update_nonexistent_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(RegisterError):
                upsert_row(Path(tmp), "risks-system", {"id": "RISKSYS-9999", "claim": "x", "status": "s"})

    def test_missing_required_field_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(RegisterError):
                upsert_row(Path(tmp), "risks-system", {"status": "identified"})  # no claim

    def test_not_carried_requires_reason_and_decider(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(RegisterError):
                upsert_row(
                    Path(tmp),
                    "not-carried",
                    {
                        "claim": "x",
                        "status": "closed",
                        "source_element_id": "uuid-1",
                        "from_perspective": "sa",
                        "to_perspective": "la",
                        # reason/decided_by deliberately omitted
                    },
                )

    def test_unknown_register_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(RegisterError):
                upsert_row(Path(tmp), "bogus-register", {"claim": "x", "status": "s"})


class TestFindRow(unittest.TestCase):
    def test_finds_row_by_id_across_registers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            row = upsert_row(
                root,
                "verification",
                {
                    "claim": "interface tested",
                    "status": "open",
                    "owner": "o",
                    "provenance": "p",
                    "links": [],
                    "method": "test",
                    "requirement_id": "REQ-0001",
                },
            )
            found = find_row(root, row["id"])
            self.assertIsNotNone(found)
            self.assertEqual(found[0], "verification")

    def test_missing_id_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(find_row(Path(tmp), "REQ-9999"))


class TestFindRowsLinking(unittest.TestCase):
    def test_finds_rows_that_link_a_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = "0d2edb8f-fa34-4e73-89ec-fb9a63001440"
            upsert_row(
                root,
                "risks-system",
                {
                    "claim": "risk on Hogwarts LC",
                    "status": "identified",
                    "owner": "o",
                    "provenance": "p",
                    "links": [target],
                    "likelihood": "low",
                    "impact": "low",
                    "treatment": "accept",
                },
            )
            hits = find_rows_linking(root, target)
            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0][0], "risks-system")

    def test_no_links_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(find_rows_linking(Path(tmp), "no-such-uuid"), [])


if __name__ == "__main__":
    unittest.main()
