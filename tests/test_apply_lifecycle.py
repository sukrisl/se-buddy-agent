import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import capellambse

from se_buddy.apply_lifecycle import (
    ApplyError,
    _check_no_diagram_references,
    _load_model_or_apply_error,
    apply_cp,
    check_drift,
    check_tree_clean,
    restore_snapshot,
    snapshot_dir,
    take_snapshot,
)
from se_buddy.changes import ChangeError, load_change, load_followup
from se_buddy.decl_ops import DryRunResult
from se_buddy.model import ModelResolutionError
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
    "intent": "exercise the apply lifecycle in tests",
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
    """Copies the real fixture into a fresh git repo at `root/model/`,
    committed - `check_tree_clean` needs real git state to check against.
    """
    dest = root / "model"
    shutil.copytree(FIXTURE_SOURCE, dest)
    _git(["init", "--quiet"], dest)
    _git(["config", "user.email", "test@example.com"], dest)
    _git(["config", "user.name", "Test"], dest)
    _git(["add", "."], dest)
    _git(["commit", "--quiet", "-m", "initial"], dest)
    return next(dest.glob("*.aird"))


class TestCheckTreeClean(unittest.TestCase):
    def test_clean_tree_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aird = _git_repo_with_fixture(root)
            check_tree_clean(aird.parent, aird)  # should not raise

    def test_dirty_capella_file_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aird = _git_repo_with_fixture(root)
            capella = aird.with_suffix(".capella")
            capella.write_text(capella.read_text(encoding="utf-8") + "\n<!-- dirty -->", encoding="utf-8")
            with self.assertRaises(ApplyError):
                check_tree_clean(aird.parent, aird)

    def test_dirty_model_in_a_subdirectory_relative_path_is_detected(self):
        """Regression test for the confirmed bug: passing the full
        (already-parent-containing) path to `git status` while `cwd` was
        already that same parent doubled the segment
        (`model/model/Project.aird`), so git matched nothing and a
        genuinely dirty subdirectory-relative model was reported clean.
        Every other test in this class uses an absolute `aird` path built
        straight from a tempdir, which never exhibited the doubling - this
        one specifically uses a relative "model/<name>" path with the
        process cwd set to the repo root, the exact layout that triggered
        it.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / "model"
            shutil.copytree(FIXTURE_SOURCE, dest)
            _git(["init", "--quiet"], root)
            _git(["config", "user.email", "test@example.com"], root)
            _git(["config", "user.name", "Test"], root)
            _git(["add", "."], root)
            _git(["commit", "--quiet", "-m", "initial"], root)

            aird_name = next(dest.glob("*.aird")).name
            capella = dest / aird_name.replace(".aird", ".capella")
            capella.write_text(capella.read_text(encoding="utf-8") + "\n<!-- dirty -->", encoding="utf-8")

            original_cwd = Path.cwd()
            os.chdir(root)
            try:
                relative_aird = Path("model") / aird_name
                with self.assertRaises(ApplyError):
                    check_tree_clean(root, relative_aird)
            finally:
                os.chdir(original_cwd)


class TestCheckDrift(unittest.TestCase):
    def test_matching_hash_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aird = _git_repo_with_fixture(root)
            from se_buddy.model import hash_model_files

            check_drift({"id": "CP-0001", "model_hash": hash_model_files(aird)}, aird)  # should not raise

    def test_mismatched_hash_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aird = _git_repo_with_fixture(root)
            with self.assertRaises(ApplyError):
                check_drift({"id": "CP-0001", "model_hash": "stale-hash"}, aird)


class TestSnapshotRoundTrip(unittest.TestCase):
    def test_snapshot_then_restore_recovers_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aird = _git_repo_with_fixture(root)
            capella = aird.with_suffix(".capella")
            original = capella.read_text(encoding="utf-8")

            directory = take_snapshot(root, aird, "CHANGE-0001")
            self.assertEqual(directory, snapshot_dir(root, "CHANGE-0001"))

            capella.write_text(original + "\n<!-- mutated -->", encoding="utf-8")
            self.assertNotEqual(capella.read_text(encoding="utf-8"), original)

            restore_snapshot(aird, directory)
            self.assertEqual(capella.read_text(encoding="utf-8"), original)


class TestCheckNoDiagramReferences(unittest.TestCase):
    def test_element_on_a_diagram_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aird = _git_repo_with_fixture(root)
            with self.assertRaises(ApplyError):
                _check_no_diagram_references(root, str(aird), frozenset({HOGWARTS_LC_UUID}))

    def test_nonexistent_uuid_is_a_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aird = _git_repo_with_fixture(root)
            _check_no_diagram_references(root, str(aird), frozenset({"not-a-real-uuid"}))  # no raise


class TestApplyCp(unittest.TestCase):
    def test_full_cycle_creates_change_and_modifies_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aird = _git_repo_with_fixture(root)
            cp = file_cp(root, dict(VALID_CP_BASE), aird)

            before_capella = aird.with_suffix(".capella").read_text(encoding="utf-8")

            change = apply_cp(root, cp["id"], "engineer said: go ahead, test run", model_arg=str(aird), today="2026-08-31")

            self.assertEqual(change["proposal"], cp["id"])
            # capellambse creates the LogicalComponent *and* its owning Part
            # for this decl document - confirmed directly beforehand.
            self.assertIn("2 element(s) created", change["diff_summary"])
            self.assertTrue(load_change(root, change["id"]))
            followup = load_followup(root, change["id"])
            self.assertEqual(len(followup), 2)
            self.assertTrue(all(item["id"].startswith("ASK-") for item in followup))

            after_capella = aird.with_suffix(".capella").read_text(encoding="utf-8")
            self.assertNotEqual(before_capella, after_capella)
            self.assertIn("TestSubComponent", after_capella)

            # snapshot exists and matches the pre-apply state exactly
            snap = snapshot_dir(root, change["id"]) / "Model Test 7.0.capella"
            self.assertEqual(snap.read_text(encoding="utf-8"), before_capella)

            # re-loading the saved model for real confirms the new element persisted
            reloaded = capellambse.MelodyModel(aird)
            names = [c.name for c in reloaded.search("LogicalComponent")]
            self.assertIn("TestSubComponent", names)

    def test_missing_authorized_by_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aird = _git_repo_with_fixture(root)
            cp = file_cp(root, dict(VALID_CP_BASE), aird)
            with self.assertRaises(ApplyError):
                apply_cp(root, cp["id"], "", model_arg=str(aird))

    def test_dirty_tree_refuses_before_any_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aird = _git_repo_with_fixture(root)
            cp = file_cp(root, dict(VALID_CP_BASE), aird)
            capella = aird.with_suffix(".capella")
            capella.write_text(capella.read_text(encoding="utf-8") + "\n<!-- dirty -->", encoding="utf-8")
            with self.assertRaises(ApplyError):
                apply_cp(root, cp["id"], "engineer said go", model_arg=str(aird))
            self.assertFalse(snapshot_dir(root, "CHANGE-0001").exists())

    def test_bad_target_reference_refuses_cleanly(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aird = _git_repo_with_fixture(root)
            cp_data = dict(VALID_CP_BASE)
            cp_data["proposed_changes"] = "- parent: !uuid 00000000-0000-0000-0000-000000000000\n  extend:\n    components: []\n"
            cp = file_cp(root, cp_data, aird)
            with self.assertRaises(ApplyError):
                apply_cp(root, cp["id"], "engineer said go", model_arg=str(aird))
            self.assertFalse(snapshot_dir(root, "CHANGE-0001").exists())

    def test_unknown_cp_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aird = _git_repo_with_fixture(root)
            with self.assertRaises(ApplyError):
                apply_cp(root, "CP-9999", "engineer said go", model_arg=str(aird))

    def test_open_followup_blocks_a_new_apply(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aird = _git_repo_with_fixture(root)
            cp1 = file_cp(root, dict(VALID_CP_BASE), aird)
            apply_cp(root, cp1["id"], "engineer said go", model_arg=str(aird), today="2026-08-31")

            # need a fresh CP proposed against the now-modified model hash
            cp2 = file_cp(root, dict(VALID_CP_BASE), aird)
            with self.assertRaises(ApplyError) as ctx:
                apply_cp(root, cp2["id"], "engineer said go again", model_arg=str(aird))
            self.assertIn("followup", str(ctx.exception))


class TestApplyCpDeleteEnforcement(unittest.TestCase):
    """`dry_run` is mocked here rather than exercised for real: a real
    delete of the fixture's elements was confirmed live to cascade into
    unrelated capellambse crashes (a dangling `Part` reference breaking
    `model.search()` afterwards), which is a capellambse-side fragility
    unrelated to the enforcement bug under test. Mocking isolates the one
    thing this module is actually responsible for: refusing (or not) based
    on `DryRunResult.deleted` and the `delete` flag.
    """

    def test_deletion_without_delete_flag_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aird = _git_repo_with_fixture(root)
            cp = file_cp(root, dict(VALID_CP_BASE), aird)
            fake_result = DryRunResult(
                created=frozenset(), deleted=frozenset({HOGWARTS_LC_UUID}), before_count=1, after_count=0
            )
            with patch("se_buddy.apply_lifecycle.dry_run", return_value=fake_result):
                with self.assertRaises(ApplyError) as ctx:
                    apply_cp(root, cp["id"], "engineer said go", model_arg=str(aird), delete=False)
            self.assertIn("--delete", str(ctx.exception))
            self.assertFalse(snapshot_dir(root, "CHANGE-0001").exists())

    def test_deletion_with_delete_flag_and_no_diagram_references_proceeds_past_the_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aird = _git_repo_with_fixture(root)
            cp = file_cp(root, dict(VALID_CP_BASE), aird)
            # A fake uuid in `deleted` can never be found by `by_uuid`, so
            # `_check_no_diagram_references` treats it as a no-op (already
            # covered by `TestCheckNoDiagramReferences.
            # test_nonexistent_uuid_is_a_noop`) - the apply then proceeds
            # on the real (undeleted) model and succeeds normally, proving
            # `--delete` plus a clean diagram check does not, itself, block
            # anything.
            fake_result = DryRunResult(
                created=frozenset(), deleted=frozenset({"not-a-real-uuid"}), before_count=1, after_count=0
            )
            with patch("se_buddy.apply_lifecycle.dry_run", return_value=fake_result):
                change = apply_cp(root, cp["id"], "engineer said go", model_arg=str(aird), delete=True, today="2026-08-31")
            self.assertTrue(load_change(root, change["id"]))


class TestApplyCpRecordFailureRestoresSnapshot(unittest.TestCase):
    def test_file_change_failure_restores_the_snapshot_and_raises_apply_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aird = _git_repo_with_fixture(root)
            cp = file_cp(root, dict(VALID_CP_BASE), aird)
            before_capella = aird.with_suffix(".capella").read_text(encoding="utf-8")

            with patch("se_buddy.apply_lifecycle.file_change", side_effect=RuntimeError("disk full")):
                with self.assertRaises(ApplyError) as ctx:
                    apply_cp(root, cp["id"], "engineer said go", model_arg=str(aird), today="2026-08-31")
            self.assertIn("restored from snapshot", str(ctx.exception))

            after_capella = aird.with_suffix(".capella").read_text(encoding="utf-8")
            self.assertEqual(before_capella, after_capella)
            self.assertFalse(load_change(root, "CHANGE-0001"))


class TestLoadModelOrApplyError(unittest.TestCase):
    def test_resolution_failure_is_wrapped_as_apply_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(ApplyError):
                _load_model_or_apply_error(root, "does-not-exist.aird")

    def test_diagram_reference_check_wraps_resolution_failure_too(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(ApplyError):
                _check_no_diagram_references(root, "does-not-exist.aird", frozenset({HOGWARTS_LC_UUID}))


if __name__ == "__main__":
    unittest.main()
