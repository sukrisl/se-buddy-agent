import json
import subprocess
import sys
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "hooks" / "block_write_verbs.py"


def _run(command: str) -> subprocess.CompletedProcess:
    payload = json.dumps({"tool_input": {"command": command}})
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=payload,
        capture_output=True,
        text=True,
    )


class TestBlockWriteVerbs(unittest.TestCase):
    def test_write_apply_via_the_launcher_is_blocked(self):
        result = _run("bin/se-buddy write-apply CP-0001 --authorized-by 'go'")
        self.assertEqual(result.returncode, 2)

    def test_write_propose_is_the_explicit_exception(self):
        result = _run("bin/se-buddy write-propose foo.yaml")
        self.assertEqual(result.returncode, 0)

    def test_the_two_new_gated_verbs_are_blocked(self):
        for command in ("bin/se-buddy write-profile", "bin/se-buddy write-domain draft.md"):
            with self.subTest(command=command):
                self.assertEqual(_run(command).returncode, 2)

    def test_a_hyphenated_ungated_verb_is_not_blocked(self):
        # `\w+` stopped at the second hyphen, so `write-claude-md` read as
        # the verb `write-claude` - not in the exemption set, so an ungated
        # verb the agent is meant to run was blocked, under a verb name
        # that does not exist.
        result = _run("bin/se-buddy write-claude-md")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_an_unknown_hyphenated_verb_still_fails_closed(self):
        result = _run("bin/se-buddy write-something-else")
        self.assertEqual(result.returncode, 2)

    def test_a_read_verb_is_not_blocked(self):
        result = _run("bin/se-buddy inspect")
        self.assertEqual(result.returncode, 0)

    def test_unrelated_command_is_not_blocked(self):
        result = _run("git status")
        self.assertEqual(result.returncode, 0)

    def test_flags_between_se_buddy_and_the_verb_are_still_caught(self):
        """A code review found the original regex required `write-` to
        follow `se-buddy`/`se-buddy.cmd` with nothing but whitespace in
        between, so any flag before the verb (a completely normal CLI
        invocation) slipped straight past the hook uncaught.
        """
        result = _run("se-buddy --model model/Project.aird write-apply CP-0001 --authorized-by 'go'")
        self.assertEqual(result.returncode, 2)

    def test_module_invocation_form_is_caught_too(self):
        """A code review found the original regex matched the literal
        hyphenated `se-buddy` token only, missing the underscore module
        form (`python -m se_buddy ...`), a real, working way to invoke
        this same CLI.
        """
        result = _run("PYTHONPATH=src python -m se_buddy write-apply CP-0001 --authorized-by 'go'")
        self.assertEqual(result.returncode, 2)

    def test_malformed_stdin_does_not_crash_the_hook(self):
        result = subprocess.run(
            [sys.executable, str(HOOK)], input="not json", capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
