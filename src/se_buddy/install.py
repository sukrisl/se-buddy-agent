"""Install integrity - can Claude Code actually see this plugin? (spec Sec.5.3)

`doctor` historically answered one question only: is the *Python* layer
sound? Interpreter floor, venv, pin, profile completeness. All four can pass
- and did, on the first real install - while the layer the engineer actually
came for, the eighteen skills of the reasoning layer, was not loaded at all.
Nothing in that report was false. It just answered a different question than
the one being asked, and printed "installation is sound" while doing it.

Claude Code loads `<root>/.claude/skills/<name>/` as the plugin
`<name>@skills-dir` only when all three of these hold:

  1. `.claude-plugin/plugin.json` is present and parseable;
  2. the session's *primary* working directory is `<root>` itself -
     project-scope skills-directory plugins do not walk up to the repository
     root the way plain skills and commands do, so launching from a
     subdirectory, or opening the project as an *additional* working
     directory, silently loads nothing;
  3. the engineer has accepted the workspace trust dialog for `<root>` -
     trusting a parent folder, or running with `-p`, is not enough.

(1) and (2) are facts on disk and this module checks them. (3) is not
observable from a subprocess, and neither is the load itself: nothing the CLI
can read tells it whether Claude Code is even running.

There is one honest positive signal available. An enabled plugin's `bin/`
directory is added to the PATH the Bash tool runs with, so if this process was
started by Claude Code with the plugin loaded, `<root>/bin` is on PATH. That
confirms a load; its absence proves nothing (a human running the launcher from
an ordinary terminal is the expected case), so it is reported as a
confirmation or as an explicit unknown, never as a failure.

What closes the remaining gap is not a check this layer can run at all: it is
`/se-buddy:doctor`, whose own existence is the proof, since a slash command
cannot resolve unless the plugin carrying it loaded. So this module ends by
saying so, rather than letting a column of `[ok]` lines imply a coverage they
do not have.
"""

from __future__ import annotations

import dataclasses
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

#: `Finding.key` for the plugin-load line - the one finding `doctor`'s summary
#: has to single out, and the one whose wording is most likely to be reworded.
PLUGIN_LOADED = "plugin-loaded"

#: Interpreter names a hook command may invoke, recognised in the order the
#: command itself lists them. Read out of `hooks.json` rather than hardcoded
#: as a preference here, so this check cannot drift from what the config
#: actually does.
_INTERPRETERS = re.compile(r"\b(python3|python)\b")

#: The `.py` guards a hook command runs, as written in `hooks.json`.
_HOOK_SCRIPT = re.compile(r"hooks/(\w+\.py)")

#: A payload the Edit/Write guard MUST block. If feeding this to the guard
#: does not produce exit 2, the layer is not working, whatever the config says.
_BLOCKED_PAYLOAD = json.dumps({"tool_input": {"file_path": "model.capella"}})


@dataclasses.dataclass(frozen=True)
class Finding:
    """One install check, in `doctor`'s three-state shape.

    `unknown` is a first-class outcome here, not a soft failure: several of
    the conditions that decide whether the plugin loaded are genuinely not
    observable from this process, and reporting them as `[ok]` or `[FAIL]`
    would both be inventions.
    """

    status: str  # "ok" | "fail" | "unknown"
    message: str
    key: str = ""  # stable identifier, for callers that must not match on prose

    @property
    def failed(self) -> bool:
        return self.status == "fail"


@dataclasses.dataclass(frozen=True)
class Layout:
    """Where this checkout sits, and what that implies about loading.

    `kind` is one of:
      "project"       - `<project>/.claude/skills/<dir>`; reaches everyone who
                        clones the project, but loads only from `<project>` as
                        the primary working directory, and only once trusted.
      "personal"      - `~/.claude/skills/<dir>`; loads in every project, with
                        no trust gate and no working-directory rule.
      "not-installed" - anywhere else: a development checkout of this repo, or
                        an install put somewhere Claude Code will not look.
    """

    kind: str
    dir_name: str
    project_root: Path | None


def describe_layout(root: Path, *, home: Path | None = None) -> Layout:
    """Classifies `root` (the plugin root) by where it sits on disk."""
    home = (home or Path.home()).resolve()
    parents = root.parents

    if len(parents) < 3 or (parents[0].name, parents[1].name) != ("skills", ".claude"):
        return Layout(kind="not-installed", dir_name=root.name, project_root=None)

    enclosing = parents[2]
    if enclosing.resolve() == home:
        return Layout(kind="personal", dir_name=root.name, project_root=None)
    return Layout(kind="project", dir_name=root.name, project_root=enclosing)


def _read_manifest_name(root: Path) -> tuple[str | None, str | None]:
    """Returns (name, error). Exactly one of the two is ever non-None."""
    manifest = root / ".claude-plugin" / "plugin.json"
    if not manifest.exists():
        return None, f"{manifest} is missing - without it nothing loads as a plugin"
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"{manifest} could not be read as JSON: {exc}"
    name = data.get("name")
    if not name:
        return None, f"{manifest} has no `name` - that field is the skill namespace"
    return name, None


def _bin_is_on_path(root: Path, path_env: str) -> bool:
    """Whether `<root>/bin` is on `path_env` - see this module's docstring."""
    try:
        target = (root / "bin").resolve()
    except OSError:
        return False
    for entry in path_env.split(os.pathsep):
        if not entry:
            continue
        try:
            if Path(entry).resolve() == target:
                return True
        except OSError:
            continue
    return False


def _hook_commands(hooks: dict) -> list[str]:
    """Every `command` string in a `hooks.json`, whatever events it declares."""
    commands: list[str] = []
    for entries in (hooks.get("hooks") or {}).values():
        for entry in entries or []:
            for hook in (entry or {}).get("hooks") or []:
                command = (hook or {}).get("command")
                if isinstance(command, str):
                    commands.append(command)
    return commands


def _resolve_interpreter(commands: list[str]) -> tuple[str | None, list[str]]:
    """The first interpreter named by the hook commands that is on PATH.

    Returns (resolved name or None, every name the commands named). Order is
    taken from the command text, so `python3`-then-`python` here follows the
    config rather than a second opinion held in this file.
    """
    named: list[str] = []
    for command in commands:
        for name in _INTERPRETERS.findall(command):
            if name not in named:
                named.append(name)
    for name in named:
        if shutil.which(name):
            return name, named
    return None, named


def check_hooks(root: Path) -> list[Finding]:
    """Whether the write guards can actually run - not merely whether the config parses.

    The distinction is the whole point of this function. `hooks.json` parsed
    cleanly on every platform where the guards were silently dead: they
    invoked bare `python`, which does not exist on macOS 12.3+ or modern
    Debian/Ubuntu, and Claude Code treats a hook whose interpreter is missing
    as a non-blocking error - so the tool call proceeds and the layer is
    simply gone. Checking the config told you nothing about that.

    So this resolves the interpreter the config names and *runs* a guard
    against a payload it must refuse, asserting exit 2.

    What it does not do, stated rather than implied: it does not reproduce
    Claude Code's shell selection. The commands are POSIX `sh`, which covers
    `sh` and Git Bash; a Windows install with no Git Bash falls back to
    PowerShell, where they would not parse. This check would still pass
    there, because the interpreter and the guard are both fine - it is the
    shell that is not. That case is called out in the README rather than
    detected here.
    """
    hooks_path = root / "hooks" / "hooks.json"
    if not hooks_path.exists():
        return [
            Finding(
                "fail",
                f"{hooks_path} is missing - the PreToolUse write guards (spec Sec.10.1) "
                "cannot load",
            )
        ]

    try:
        config = json.loads(hooks_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [Finding("fail", f"{hooks_path} could not be read as JSON: {exc}")]

    commands = _hook_commands(config)
    if not commands:
        return [Finding("fail", f"{hooks_path} declares no hook commands")]

    findings: list[Finding] = []

    for name in sorted({s for c in commands for s in _HOOK_SCRIPT.findall(c)}):
        if not (root / "hooks" / name).is_file():
            findings.append(
                Finding("fail", f"hooks.json runs hooks/{name}, which does not exist")
            )
    if findings:
        return findings

    interpreter, named = _resolve_interpreter(commands)
    if interpreter is None:
        return [
            Finding(
                "fail",
                f"none of the interpreters hooks.json names ({', '.join(named) or 'none'}) "
                "is on PATH, so the write guards would not run - and Claude Code lets a "
                "tool call proceed when a hook's interpreter is missing, so the layer "
                "would be silently absent. Install Python and re-run",
            )
        ]

    guard = root / "hooks" / "block_capella_write.py"
    try:
        proc = subprocess.run(
            [interpreter, str(guard)],
            input=_BLOCKED_PAYLOAD,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return [Finding("fail", f"could not run the write guard under {interpreter}: {exc}")]

    if proc.returncode != 2:
        return [
            Finding(
                "fail",
                f"the write guard ran under {interpreter} but did not block a .capella "
                f"edit (exit {proc.returncode}, expected 2) - the second write-protection "
                "layer is not working",
            )
        ]

    findings.append(
        Finding("ok", f"write guards run under {interpreter} and block a .capella edit")
    )
    return findings


def check_install(
    root: Path,
    cwd: Path,
    *,
    path_env: str | None = None,
    home: Path | None = None,
) -> list[Finding]:
    """What can, and cannot, be established about this install from here.

    `root` is the plugin root (this repository); `cwd` is where the engineer
    ran the command. Both are passed in rather than read off the process, so
    that this is testable without moving the interpreter around.
    """
    findings: list[Finding] = []
    path_env = os.environ.get("PATH", "") if path_env is None else path_env

    name, manifest_error = _read_manifest_name(root)
    if manifest_error is not None:
        findings.append(Finding("fail", manifest_error))
    else:
        findings.append(Finding("ok", f"manifest names the plugin {name!r}"))

    layout = describe_layout(root, home=home)

    if layout.kind == "not-installed":
        findings.append(
            Finding(
                "unknown",
                f"layout: {root} is not under a `.claude/skills/` directory, so Claude "
                "Code will not auto-load it. Expected for a development checkout of "
                "this repository; for a project install see the README's Install steps",
            )
        )
    elif layout.kind == "personal":
        findings.append(
            Finding(
                "ok",
                f"layout: personal scope (~/.claude/skills/{layout.dir_name}) - loads in "
                "every project, with no trust gate and no working-directory rule",
            )
        )
    else:
        findings.append(Finding("ok", f"layout: project scope under {layout.project_root}"))

    if name is not None and layout.kind != "not-installed" and layout.dir_name != name:
        findings.append(
            Finding(
                "unknown",
                f"the directory is named {layout.dir_name!r} but the manifest names the "
                f"plugin {name!r}. Rename the directory to {name!r} so the two agree - "
                "which of them wins is not worth relying on",
            )
        )

    if layout.kind == "project":
        project_root = layout.project_root
        assert project_root is not None  # guaranteed by describe_layout
        if cwd.resolve() != project_root.resolve():
            findings.append(
                Finding(
                    "fail",
                    f"working directory is {cwd}, not {project_root}. A project-scope "
                    "plugin loads only from the primary working directory and does not "
                    f"walk up, so nothing loads from here. Start Claude Code at "
                    f"{project_root}, or move the session there with `/cd`",
                )
            )
        else:
            findings.append(
                Finding("ok", f"working directory is the project root {project_root}")
            )

    findings.extend(check_hooks(root))

    loaded_name = f"{name or layout.dir_name}@skills-dir"
    if _bin_is_on_path(root, path_env):
        findings.append(
            Finding(
                "ok",
                f"plugin is loaded: this ran with {root / 'bin'} on PATH, which happens "
                f"only when Claude Code has {loaded_name} enabled",
                key=PLUGIN_LOADED,
            )
        )
    else:
        findings.append(
            Finding(
                "unknown",
                "plugin load is NOT checkable from here - expected when you run the "
                "launcher yourself. Confirm it inside Claude Code with "
                f"`/se-buddy:doctor`; if that command does not exist, {loaded_name} did "
                "not load and no skill is available. See the README's Troubleshooting",
                key=PLUGIN_LOADED,
            )
        )

    return findings
