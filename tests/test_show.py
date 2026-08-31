import tempfile
import unittest
from pathlib import Path

from se_buddy.ask_store import sync_profile_gaps
from se_buddy.changes import file_change
from se_buddy.commands.show import _show_record
from se_buddy.decisions import file_adr
from se_buddy.profile import ProfileGap
from se_buddy.proposals import file_cp
from se_buddy.registers import upsert_row
from tests.test_decisions import VALID_ADR
from tests.test_proposals import VALID_CP


class TestShowRecord(unittest.TestCase):
    def test_shows_an_adr(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            adr = file_adr(root, dict(VALID_ADR))
            self.assertEqual(_show_record(root, adr["id"], "ADR"), 0)

    def test_shows_a_cp(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aird = root / "model.aird"
            aird.write_text("x", encoding="utf-8")
            cp = file_cp(root, dict(VALID_CP), aird)
            self.assertEqual(_show_record(root, cp["id"], "CP"), 0)

    def test_shows_a_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            change = {
                "claim": "x", "tier": "judgement", "date": "2026-08-31", "supersedes": [],
                "proposal": None, "authority": "engineer said go", "diff_summary": "1 created",
                "validation_summary": "ok", "manual_followup": [],
            }
            written = file_change(root, "CHANGE-0001", change, [])
            self.assertEqual(_show_record(root, written["id"], "CHANGE"), 0)

    def test_shows_an_ask_store_ask(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asks = sync_profile_gaps(root, [ProfileGap(object="x", done_when="y")], today="2026-08-31")
            ask_id = next(iter(asks))
            self.assertEqual(_show_record(root, ask_id, "ASK"), 0)

    def test_shows_a_followup_ask(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            change = {
                "claim": "x", "tier": "judgement", "date": "2026-08-31", "supersedes": [],
                "proposal": None, "authority": "engineer said go", "diff_summary": "1 created",
                "validation_summary": "ok", "manual_followup": [],
            }
            followup = [{"object": "o", "done_when": "d", "blocks": "b", "default": "n"}]
            file_change(root, "CHANGE-0001", change, followup)
            from se_buddy.changes import load_followup

            ask_id = load_followup(root, "CHANGE-0001")[0]["id"]
            self.assertEqual(_show_record(root, ask_id, "ASK"), 0)

    def test_shows_a_register_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            row = upsert_row(
                root,
                "risks-system",
                {
                    "claim": "x", "status": "open", "owner": "o", "provenance": "p",
                    "links": [], "likelihood": "low", "impact": "low", "treatment": "accept",
                },
            )
            self.assertEqual(_show_record(root, row["id"], "RISKSYS"), 0)

    def test_unknown_record_id_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(_show_record(Path(tmp), "ADR-9999", "ADR"))


if __name__ == "__main__":
    unittest.main()
