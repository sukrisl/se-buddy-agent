import unittest

from se_buddy.schemas import validate_ask, validate_record_base


class TestValidateAsk(unittest.TestCase):
    def test_full_ask_is_valid(self):
        result = validate_ask(
            {
                "id": "ASK-0001",
                "act": "REVIEW",
                "object": "LC-014 owning retry",
                "done_when": "you accept it, or name a different owner",
                "blocks": "CP-0022",
                "default": "none - this blocks",
            }
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.warnings, ())

    def test_missing_act_is_enforced(self):
        result = validate_ask({"done_when": "x", "object": "x", "blocks": "x", "default": "x"})
        self.assertFalse(result.ok)
        self.assertIn("act is required (spec Sec.9: enforced)", result.errors)

    def test_missing_done_when_is_enforced(self):
        result = validate_ask({"act": "SUPPLY", "object": "x", "blocks": "x", "default": "x"})
        self.assertFalse(result.ok)
        self.assertIn("done_when is required (spec Sec.9: enforced)", result.errors)

    def test_unknown_act_is_rejected(self):
        result = validate_ask({"act": "GUESS", "done_when": "x"})
        self.assertFalse(result.ok)

    def test_missing_object_blocks_default_are_warnings_not_errors(self):
        result = validate_ask({"act": "SUPPLY", "done_when": "x"})
        self.assertTrue(result.ok)
        self.assertEqual(len(result.warnings), 3)


class TestValidateRecordBase(unittest.TestCase):
    def test_complete_record_is_valid(self):
        result = validate_record_base(
            {
                "id": "ADR-0007",
                "claim": "device owns schedule execution",
                "tier": "decision",
                "date": "2026-08-31",
                "supersedes": [],
            }
        )
        self.assertTrue(result.ok)

    def test_missing_claim_is_enforced(self):
        result = validate_record_base(
            {"id": "ADR-0007", "tier": "decision", "date": "2026-08-31", "supersedes": []}
        )
        self.assertFalse(result.ok)

    def test_bad_tier_is_rejected(self):
        result = validate_record_base(
            {
                "id": "ADR-0007",
                "claim": "x",
                "tier": "vibes",
                "date": "2026-08-31",
                "supersedes": [],
            }
        )
        self.assertFalse(result.ok)

    def test_missing_supersedes_is_enforced_even_when_empty_is_intended(self):
        result = validate_record_base(
            {"id": "ADR-0007", "claim": "x", "tier": "decision", "date": "2026-08-31"}
        )
        self.assertFalse(result.ok)


if __name__ == "__main__":
    unittest.main()
