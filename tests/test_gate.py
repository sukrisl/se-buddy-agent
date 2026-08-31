import builtins
import unittest
from unittest.mock import patch

from se_buddy.gate import GateRefused, confirm


class TestConfirm(unittest.TestCase):
    def test_refuses_when_not_a_tty(self):
        with patch("sys.stdin.isatty", return_value=False), patch("sys.stdout.isatty", return_value=True):
            with self.assertRaises(GateRefused):
                confirm("about to do something")

    def test_refuses_when_confirmation_text_does_not_match(self):
        with patch("sys.stdin.isatty", return_value=True), patch("sys.stdout.isatty", return_value=True):
            with patch.object(builtins, "input", return_value="no"):
                with self.assertRaises(GateRefused):
                    confirm("about to do something")

    def test_succeeds_on_matching_confirmation(self):
        with patch("sys.stdin.isatty", return_value=True), patch("sys.stdout.isatty", return_value=True):
            with patch.object(builtins, "input", return_value="yes"):
                confirm("about to do something")  # should not raise

    def test_eof_on_stdin_is_a_clean_refusal_not_a_crash(self):
        """A code review found `input()`'s `EOFError` (stdin closed after
        `isatty()` passed but before a line arrived) was never caught here,
        so it escaped past every caller's `except GateRefused` as a raw
        crash instead of the clean refusal every other "no confirmation
        given" path produces.
        """
        with patch("sys.stdin.isatty", return_value=True), patch("sys.stdout.isatty", return_value=True):
            with patch.object(builtins, "input", side_effect=EOFError):
                with self.assertRaises(GateRefused):
                    confirm("about to do something")


if __name__ == "__main__":
    unittest.main()
