import unittest

from se_buddy.schemas import validate_ask, validate_change, validate_cp, validate_record_base

VALID_CP = {
    "id": "CP-0001",
    "claim": "extract retry logic into a shared component",
    "tier": "judgement",
    "date": "2026-08-31",
    "supersedes": [],
    "intent": "reduce duplicated retry handling",
    "facts": ["three components implement near-identical retry loops"],
    "assumptions": [],
    "unknowns": [],
    "affected_elements": ["0d2edb8f-fa34-4e73-89ec-fb9a63001440"],
    "proposed_changes": [{"parent": "!uuid 0d2edb8f-fa34-4e73-89ec-fb9a63001440", "extend": {}}],
    "alternatives": "leave as-is",
    "verification_implications": "existing retry tests must still pass unmodified",
    "open_questions": [],
    "diagram_cost": 0,
    "provenance": "spotted during arch-review",
}

VALID_CHANGE = {
    "id": "CHANGE-0001",
    "claim": "extracted retry logic into RetryPolicy",
    "tier": "judgement",
    "date": "2026-08-31",
    "supersedes": [],
    "proposal": "CP-0001",
    "authority": "engineer said: go ahead, 2026-08-31 standup",
    "diff_summary": "3 elements changed, 1 created",
    "validation_summary": "all six layers pass",
    "manual_followup": [],
}


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


class TestValidateCp(unittest.TestCase):
    def test_diagram_cost_zero_is_not_a_missing_field(self):
        """A code review found `diagram_cost` missing from
        `_CP_PRESENCE_ONLY_FIELDS`, so `bool(0)` treated a legitimate
        "nothing to draw" answer as absent and warned about it on every
        CP that had one.
        """
        result = validate_cp(dict(VALID_CP))
        self.assertTrue(result.ok)
        self.assertNotIn("diagram_cost is required but not enforced on a CP (spec Sec.9)", result.warnings)

    def test_missing_diagram_cost_is_still_a_warning(self):
        cp = dict(VALID_CP)
        del cp["diagram_cost"]
        result = validate_cp(cp)
        self.assertIn("diagram_cost is required but not enforced on a CP (spec Sec.9)", result.warnings)

    def test_missing_facts_is_enforced(self):
        cp = dict(VALID_CP)
        cp["facts"] = []
        result = validate_cp(cp)
        self.assertFalse(result.ok)


class TestValidateChange(unittest.TestCase):
    def test_complete_change_is_valid(self):
        result = validate_change(dict(VALID_CHANGE))
        self.assertTrue(result.ok)
        self.assertEqual(result.warnings, ())

    def test_empty_manual_followup_is_not_a_missing_field(self):
        result = validate_change(dict(VALID_CHANGE))
        self.assertNotIn(
            "manual_followup is required but not enforced on a CHANGE (spec Sec.9)", result.warnings
        )

    def test_missing_manual_followup_is_enforced(self):
        change = dict(VALID_CHANGE)
        del change["manual_followup"]
        result = validate_change(change)
        self.assertFalse(result.ok)
        self.assertIn("manual_followup is required on every CHANGE (spec Sec.9: enforced)", result.errors)

    def test_missing_authority_is_enforced(self):
        change = dict(VALID_CHANGE)
        del change["authority"]
        result = validate_change(change)
        self.assertFalse(result.ok)

    def test_missing_proposal_is_a_warning_not_an_error(self):
        change = dict(VALID_CHANGE)
        change["proposal"] = None
        result = validate_change(change)
        self.assertTrue(result.ok)
        self.assertIn("proposal is required but not enforced on a CHANGE (spec Sec.9)", result.warnings)


if __name__ == "__main__":
    unittest.main()
