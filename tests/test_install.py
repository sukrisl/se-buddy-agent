import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from se_buddy.install import (
    PLUGIN_LOADED,
    _hook_commands,
    check_hooks,
    check_install,
    describe_layout,
)

#: The repository's own `hooks/`, copied into each fixture rather than stubbed.
#: `check_hooks` runs a guard for real, so a stub would test the stub.
REAL_HOOKS = Path(__file__).resolve().parents[1] / "hooks"


def _plugin_root(base: Path, *, name: str = "se-buddy", manifest: object = ...) -> Path:
    """Builds a minimally loadable plugin tree at `base` and returns its root."""
    root = base
    (root / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    if manifest is ...:
        manifest = {"name": name, "version": "0.1.0"}
    if manifest is not None:
        (root / ".claude-plugin" / "plugin.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
    shutil.copytree(REAL_HOOKS, root / "hooks", dirs_exist_ok=True)
    return root


def _installed(base: Path, *, dir_name: str = "se-buddy", name: str = "se-buddy") -> Path:
    """A project-scope install: <base>/.claude/skills/<dir_name>."""
    return _plugin_root(base / ".claude" / "skills" / dir_name, name=name)


def _by_key(findings, key):
    return next(f for f in findings if f.key == key)


class TestDescribeLayout(unittest.TestCase):
    def test_project_scope_is_recognised_and_names_the_project_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            layout = describe_layout(base / ".claude" / "skills" / "se-buddy", home=base / "home")
            self.assertEqual(layout.kind, "project")
            self.assertEqual(layout.project_root, base)

    def test_personal_scope_is_distinguished_from_project_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            layout = describe_layout(home / ".claude" / "skills" / "se-buddy", home=home)
            self.assertEqual(layout.kind, "personal")
            self.assertIsNone(layout.project_root)

    def test_a_development_checkout_is_not_installed(self):
        with tempfile.TemporaryDirectory() as tmp:
            layout = describe_layout(Path(tmp) / "src" / "se-buddy-agent", home=Path(tmp))
            self.assertEqual(layout.kind, "not-installed")

    def test_a_shallow_path_does_not_crash_on_missing_parents(self):
        # `.claude/skills/x` needs three parents; anything shorter must fall
        # through rather than raise looking for parents[2].
        layout = describe_layout(Path(Path(os.sep).anchor or os.sep) / "x", home=Path.home())
        self.assertEqual(layout.kind, "not-installed")


class TestCheckInstall(unittest.TestCase):
    def test_a_correct_project_install_at_the_root_has_no_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = _installed(base)
            findings = check_install(root, base, path_env="", home=base / "elsewhere")
            self.assertEqual([f.message for f in findings if f.failed], [])

    def test_running_from_a_subdirectory_fails_and_names_the_project_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = _installed(base)
            sub = base / "subsystem"
            sub.mkdir()

            findings = check_install(root, sub, path_env="", home=base / "elsewhere")

            failures = [f for f in findings if f.failed]
            self.assertEqual(len(failures), 1)
            self.assertIn(str(base), failures[0].message)

    def test_personal_scope_has_no_working_directory_rule(self):
        # A personal-scope plugin loads in every project, so being run from
        # somewhere else is not a failure the way it is for project scope.
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            root = _installed(home)
            elsewhere = Path(tmp) / "some-project"
            elsewhere.mkdir(parents=True)

            findings = check_install(root, elsewhere, path_env="", home=home)

            self.assertEqual([f.message for f in findings if f.failed], [])

    def test_a_missing_manifest_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = _plugin_root(base / ".claude" / "skills" / "se-buddy", manifest=None)
            findings = check_install(root, base, path_env="", home=base / "elsewhere")
            self.assertTrue(any(f.failed and "plugin.json" in f.message for f in findings))

    def test_unparseable_manifest_fails_rather_than_raising(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = _plugin_root(base / ".claude" / "skills" / "se-buddy", manifest=None)
            (root / ".claude-plugin" / "plugin.json").write_text("{not json", encoding="utf-8")
            findings = check_install(root, base, path_env="", home=base / "elsewhere")
            self.assertTrue(any(f.failed for f in findings))

    def test_missing_hooks_fails_because_a_write_guard_layer_would_be_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = _installed(base)
            (root / "hooks" / "hooks.json").unlink()
            findings = check_install(root, base, path_env="", home=base / "elsewhere")
            self.assertTrue(any(f.failed and "hooks.json" in f.message for f in findings))

    def test_directory_name_disagreeing_with_the_manifest_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = _installed(base, dir_name="se_buddy_agent", name="se-buddy")
            findings = check_install(root, base, path_env="", home=base / "elsewhere")
            self.assertTrue(
                any("se_buddy_agent" in f.message and "se-buddy" in f.message for f in findings)
            )

    def test_bin_on_path_confirms_the_plugin_is_loaded(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = _installed(base)
            (root / "bin").mkdir()

            findings = check_install(
                root, base, path_env=str(root / "bin"), home=base / "elsewhere"
            )

            self.assertEqual(_by_key(findings, PLUGIN_LOADED).status, "ok")

    def test_bin_absent_from_path_is_unknown_never_a_failure(self):
        # Absence proves nothing - a human running the launcher from an
        # ordinary terminal is the expected case, and must not be told the
        # install is broken.
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = _installed(base)

            finding = _by_key(check_install(root, base, path_env="", home=base / "x"), PLUGIN_LOADED)

            self.assertEqual(finding.status, "unknown")
            self.assertIn("/se-buddy:doctor", finding.message)

    def test_the_write_guard_is_run_not_merely_parsed(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = _installed(base)
            findings = check_install(root, base, path_env="", home=base / "elsewhere")
            self.assertTrue(any("write guards run under" in f.message for f in findings))

    def test_path_entries_that_cannot_be_resolved_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = _installed(base)
            (root / "bin").mkdir()
            path_env = os.pathsep.join(["", "\x00bogus", str(root / "bin")])

            findings = check_install(root, base, path_env=path_env, home=base / "elsewhere")

            self.assertEqual(_by_key(findings, PLUGIN_LOADED).status, "ok")


class TestCheckHooks(unittest.TestCase):
    """The layer that used to be checkable only by parsing its own config.

    Every one of these passed as `[ok]` under the old existence-and-JSON
    check, on a platform where the guards did not run at all.
    """

    def test_the_shipped_config_runs_a_guard_that_blocks(self):
        findings = check_hooks(Path(__file__).resolve().parents[1])
        self.assertEqual([f.message for f in findings if f.failed], [])
        self.assertTrue(any("block a .capella edit" in f.message for f in findings))

    def test_no_interpreter_on_path_is_a_failure_not_an_ok(self):
        # The real bug, in the form it took on macOS and modern Debian: the
        # config is perfectly valid JSON naming a `python` that isn't there,
        # and Claude Code lets the tool call proceed when a hook's
        # interpreter is missing.
        with tempfile.TemporaryDirectory() as tmp:
            root = _plugin_root(Path(tmp))
            (root / "hooks" / "hooks.json").write_text(
                json.dumps(
                    {
                        "hooks": {
                            "PreToolUse": [
                                {
                                    "matcher": "Edit",
                                    "hooks": [
                                        {
                                            "type": "command",
                                            "command": "nosuchpython hooks/block_capella_write.py",
                                        }
                                    ],
                                }
                            ]
                        }
                    }
                ),
                encoding="utf-8",
            )

            findings = check_hooks(root)

            self.assertTrue(findings[0].failed)
            self.assertIn("silently absent", findings[0].message)

    def test_a_config_naming_a_script_that_does_not_exist_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _plugin_root(Path(tmp))
            (root / "hooks" / "block_capella_write.py").unlink()
            findings = check_hooks(root)
            self.assertTrue(any(f.failed and "does not exist" in f.message for f in findings))

    def test_a_guard_that_stops_blocking_is_caught(self):
        # A guard that exits 0 on a .capella edit is worse than a missing
        # one: the config, the script and the interpreter all look right.
        with tempfile.TemporaryDirectory() as tmp:
            root = _plugin_root(Path(tmp))
            (root / "hooks" / "block_capella_write.py").write_text(
                "import sys\nsys.exit(0)\n", encoding="utf-8"
            )
            findings = check_hooks(root)
            self.assertTrue(any(f.failed and "did not block" in f.message for f in findings))

    def test_a_config_declaring_no_commands_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _plugin_root(Path(tmp))
            (root / "hooks" / "hooks.json").write_text(
                json.dumps({"hooks": {}}), encoding="utf-8"
            )
            findings = check_hooks(root)
            self.assertTrue(any(f.failed and "no hook commands" in f.message for f in findings))

    def test_every_shipped_hook_command_prefers_python3_and_falls_back(self):
        # The fix itself: bare `python` is what broke on macOS/Linux, so both
        # the presence of the fallback and its order are load-bearing.
        config = json.loads((REAL_HOOKS / "hooks.json").read_text(encoding="utf-8"))
        commands = _hook_commands(config)

        self.assertEqual(len(commands), 2)
        for command in commands:
            with self.subTest(command=command):
                self.assertIn("command -v python3", command)
                self.assertIn("exec python3", command)
                self.assertIn("exec python ", command)
                self.assertLess(command.index("exec python3"), command.index("exec python "))
                # `exec`, not a plain call: the shell must be replaced so the
                # guard's exit 2 is what Claude Code sees as the block.
                self.assertNotIn("; python ", command)


if __name__ == "__main__":
    unittest.main()
