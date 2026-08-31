import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from se_buddy.apply_lifecycle import apply_cp
from se_buddy.commands.write_revert import RevertError, revert_change
from se_buddy.proposals import file_cp

FIXTURE_SOURCE = (
    Path(__file__).resolve().parents[1] / "vendor" / "py-capellambse" / "tests" / "data" / "models" / "test7_0"
)
HOGWARTS_LC_UUID = "0d2edb8f-fa34-4e73-89ec-fb9a63001440"

VALID_CP_BASE = {
    "claim": "add a TestSubComponent under Hogwarts",
    "tier": "judgement",
    "date": "2026-08-31",
    "supersedes": [],
    "intent": "exercise write-revert in tests",
    "facts": ["Hogwarts LC exists at a known uuid"],
    "assumptions": [],
    "unknowns": [],
    "affected_elements": [HOGWARTS_LC_UUID],
    "proposed_changes": (
        "- parent: !uuid " + HOGWARTS_LC_UUID + "\n"
        "  extend:\n"
        "    components:\n"
        "      - name: TestSubComponent\n"
    ),
    "alternatives": "none - a test fixture",
    "verification_implications": "none",
    "open_questions": [],
    "diagram_cost": 0,
    "provenance": "test fixture",
}


def _git(args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


def _git_repo_with_fixture(root: Path) -> Path:
    dest = root / "model"
    shutil.copytree(FIXTURE_SOURCE, dest)
    _git(["init", "--quiet"], dest)
    _git(["config", "user.email", "test@example.com"], dest)
    _git(["config", "user.name", "Test"], dest)
    _git(["add", "."], dest)
    _git(["commit", "--quiet", "-m", "initial"], dest)
    return next(dest.glob("*.aird"))


class TestRevertChange(unittest.TestCase):
    def test_unknown_change_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aird = _git_repo_with_fixture(root)
            with self.assertRaises(RevertError):
                revert_change(root, "CHANGE-9999", str(aird))

    def test_dirty_tree_after_apply_raises_revert_error_not_apply_error(self):
        """Applying never commits (spec Sec.10.2: "Git history is the
        engineer's"), so the tree is always dirty right after a real
        apply - the most common revert scenario. A code review found
        `revert_change` called `check_tree_clean` without catching the
        `ApplyError` it raises, so this exact scenario crashed with a type
        `run()`'s own `except RevertError` never caught. Confirmed live
        before the fix: the tree here is genuinely dirty (uncommitted by
        design) and this must come back as `RevertError`, not a bare
        `ApplyError` escaping past this function.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aird = _git_repo_with_fixture(root)
            cp = file_cp(root, dict(VALID_CP_BASE), aird)
            change = apply_cp(root, cp["id"], "engineer said go", model_arg=str(aird), today="2026-08-31")

            with self.assertRaises(RevertError):
                revert_change(root, change["id"], str(aird))

    def test_missing_snapshot_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aird = _git_repo_with_fixture(root)
            from se_buddy.changes import file_change

            file_change(
                root,
                "CHANGE-0001",
                {
                    "claim": "manual work",
                    "tier": "judgement",
                    "date": "2026-08-31",
                    "supersedes": [],
                    "proposal": "",
                    "authority": "engineer said so",
                    "diff_summary": "manual",
                    "validation_summary": "manual",
                    "manual_followup": [],
                },
                [],
            )
            with self.assertRaises(RevertError):
                revert_change(root, "CHANGE-0001", str(aird))

    def test_full_apply_then_commit_then_revert_restores_byte_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aird = _git_repo_with_fixture(root)
            before_capella = aird.with_suffix(".capella").read_text(encoding="utf-8")

            cp = file_cp(root, dict(VALID_CP_BASE), aird)
            change = apply_cp(root, cp["id"], "engineer said go", model_arg=str(aird), today="2026-08-31")

            # commit so the tree is clean again, matching how an engineer
            # actually gets to a revertable state after a real apply
            _git(["add", "."], aird.parent)
            _git(["commit", "--quiet", "-m", "apply"], aird.parent)

            revert_change(root, change["id"], str(aird))
            self.assertEqual(aird.with_suffix(".capella").read_text(encoding="utf-8"), before_capella)


if __name__ == "__main__":
    unittest.main()
