import tempfile
import unittest
from pathlib import Path

from se_buddy.decisions import DecisionError, file_adr, load_adr

VALID_ADR = {
    "claim": "device owns schedule execution",
    "tier": "decision",
    "date": "2026-08-31",
    "supersedes": [],
    "question": "who owns retry scheduling?",
    "context": "two candidates own timing today",
    "alternatives": "device-owned vs cloud-owned, one line each",
    "chosen_option": "device-owned",
    "rationale": "network partition tolerance",
    "consequences": "device firmware carries the retry state",
    "evidence": "functional chain FC-0007 demonstrates the failover path",
    "authority": "engineer said: go with device-owned, 2026-08-31 standup",
}


class TestFileAdr(unittest.TestCase):
    def test_allocates_id_and_writes_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            adr = file_adr(root, dict(VALID_ADR))
            self.assertEqual(adr["id"], "ADR-0001")
            loaded = load_adr(root, "ADR-0001")
            self.assertEqual(loaded["chosen_option"], "device-owned")

    def test_second_adr_increments(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = file_adr(root, dict(VALID_ADR))
            second = file_adr(root, dict(VALID_ADR))
            self.assertEqual(first["id"], "ADR-0001")
            self.assertEqual(second["id"], "ADR-0002")

    def test_missing_authority_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            adr = dict(VALID_ADR)
            del adr["authority"]
            with self.assertRaises(DecisionError):
                file_adr(Path(tmp), adr)

    def test_supplying_an_id_is_rejected(self):
        # spec Sec.6.1: "history is superseded, never rewritten" - an ADR
        # is never updated in place, only superseded by a new one.
        with tempfile.TemporaryDirectory() as tmp:
            adr = {**VALID_ADR, "id": "ADR-0001"}
            with self.assertRaises(DecisionError):
                file_adr(Path(tmp), adr)

    def test_missing_claim_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            adr = dict(VALID_ADR)
            del adr["claim"]
            with self.assertRaises(DecisionError):
                file_adr(Path(tmp), adr)


class TestLoadAdr(unittest.TestCase):
    def test_missing_adr_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(load_adr(Path(tmp), "ADR-9999"))


if __name__ == "__main__":
    unittest.main()
