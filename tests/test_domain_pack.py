import unittest
from pathlib import Path

from se_buddy import domain_pack
from tests import complete_domain_pack

TEMPLATE = Path("templates/domains/generic.md")


class TestDomainPackCheck(unittest.TestCase):
    def test_a_complete_pack_has_no_gaps_of_either_kind(self):
        gaps = domain_pack.check(complete_domain_pack())
        self.assertEqual(gaps.structural, [])
        self.assertEqual(gaps.skeleton_signals, [])
        self.assertTrue(gaps.is_complete)

    def test_the_shipped_template_is_reported_as_a_skeleton(self):
        # The regression that started this: an unedited template used to
        # satisfy `check_completeness` outright.
        gaps = domain_pack.check(TEMPLATE.read_text(encoding="utf-8"))
        self.assertFalse(gaps.is_complete)
        self.assertTrue(gaps.has_template_preamble)
        self.assertTrue(gaps.placeholders)

    def test_the_shipped_template_is_structurally_complete(self):
        # It has all six headings - which is exactly why existence-only and
        # heading-only checks both passed it, and why the placeholder
        # heuristic has to exist at all.
        self.assertEqual(domain_pack.check(TEMPLATE.read_text(encoding="utf-8")).structural, [])

    def test_every_required_section_is_reported_when_missing(self):
        gaps = domain_pack.check("# Domain pack: example\n")
        self.assertEqual(set(gaps.missing_sections), set(domain_pack.REQUIRED_SECTIONS))
        self.assertEqual(len(gaps.structural), len(domain_pack.REQUIRED_SECTIONS))

    def test_a_heading_with_no_body_is_empty_not_missing(self):
        text = complete_domain_pack().replace(
            "Real content for applicable standards.", ""
        )
        gaps = domain_pack.check(text)
        self.assertEqual(gaps.missing_sections, [])
        self.assertEqual(gaps.empty_sections, ["Applicable standards"])

    def test_headings_match_case_insensitively(self):
        text = complete_domain_pack().replace("## Applicable standards", "## APPLICABLE STANDARDS")
        self.assertEqual(domain_pack.check(text).structural, [])

    def test_placeholders_are_reported_verbatim_so_a_false_positive_is_visible(self):
        text = complete_domain_pack() + "\n- <standard> <clause> - <what it requires>\n"
        gaps = domain_pack.check(text)
        self.assertIn("<standard>", gaps.placeholders)
        self.assertIn("<clause>", gaps.placeholders)

    def test_placeholders_do_not_make_a_pack_structurally_invalid(self):
        # The split that matters: heuristics report, they never refuse.
        # `write domain` keys off `structural`, so this must stay empty.
        text = complete_domain_pack() + "\n- <placeholder>\n"
        gaps = domain_pack.check(text)
        self.assertEqual(gaps.structural, [])
        self.assertTrue(gaps.skeleton_signals)

    def test_an_angle_bracket_spanning_a_line_is_not_a_placeholder(self):
        text = complete_domain_pack() + "\nlatency < 100 ms and\nthroughput > 1000/s\n"
        self.assertEqual(domain_pack.check(text).placeholders, [])

    def test_capitalised_generics_are_not_treated_as_placeholders(self):
        text = complete_domain_pack() + "\nThe handler is a `Map<String, Device>`.\n"
        self.assertEqual(domain_pack.check(text).placeholders, [])

    def test_many_placeholders_are_summarised_rather_than_all_listed(self):
        text = complete_domain_pack() + "\n" + "\n".join(f"- <ph{i}>" for i in range(9))
        signal = next(s for s in domain_pack.check(text).skeleton_signals if "placeholder" in s)
        self.assertIn("9 unreplaced", signal)
        self.assertIn("more", signal)


if __name__ == "__main__":
    unittest.main()
