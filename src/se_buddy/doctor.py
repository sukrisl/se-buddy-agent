"""`se-buddy doctor` - is this installation sound? (spec Sec.5.3)

Phase 0 added the venv and version checks of Sec.5.1/Sec.7.1. Phase 1 added
profile completeness (Sec.5.3's table: "refuses? no; reports what is missing
as SUPPLY asks"). Model reachability, register/record validity and AGENT-LOG
acknowledgement arrive with the phases that give the agent registers and
records to check against.

By the time this module runs, bin/_bootstrap.py has already run under the
system interpreter and either found a working venv or rebuilt one - so
"present" and "capellambse importable" are already guaranteed here. What this
module still has to do itself is the one check Sec.7.1 says must *refuse*
rather than be silently repaired: a capellambse version that has drifted from
the pin.

Three sections, because "is this installation sound?" turned out to be three
questions and the first real install failed the one nothing was asking.
`install` is whether Claude Code can see the plugin at all (se_buddy.install);
`runtime` is the interpreter, venv and pin; `profile` is Sec.5.3 completeness.
The runtime and profile sections can pass in full while every skill is
unreachable, so the summary line below never claims more than the install
section could actually establish.
"""

from __future__ import annotations

import sys
from pathlib import Path

from se_buddy._pin import MIN_PYTHON, read_pin, repo_root
from se_buddy.install import PLUGIN_LOADED, Finding, check_install
from se_buddy.profile import check_completeness

_MARKERS = {"ok": "[ok]  ", "fail": "[FAIL]", "unknown": "[ ]   "}


def _render(finding: Finding) -> str:
    return f"  {_MARKERS[finding.status]} {finding.message}"


def _floor_ok() -> bool:
    v = sys.version_info
    return (v.major, v.minor) >= MIN_PYTHON


def _runtime_findings() -> list[Finding]:
    findings: list[Finding] = []

    have = sys.version.split()[0]
    want = ".".join(map(str, MIN_PYTHON))
    if _floor_ok():
        findings.append(Finding("ok", f"interpreter {have} (floor is {want})"))
    else:
        findings.append(Finding("fail", f"interpreter {have} is below the floor {want}"))

    findings.append(Finding("ok", f"venv present at {sys.prefix}"))

    pin = read_pin()
    try:
        import capellambse

        installed = capellambse.__version__
    except ImportError as exc:
        findings.append(Finding("fail", f"capellambse is not importable in this venv: {exc}"))
        return findings

    if installed == pin:
        findings.append(Finding("ok", f"capellambse {installed} matches the pin"))
    else:
        findings.append(
            Finding(
                "fail",
                f"capellambse {installed} does not match the pin {pin} (this venv was "
                "changed outside se-buddy - see spec Sec.7.1)",
            )
        )
    return findings


def _profile_findings(root: Path) -> list[Finding]:
    gaps = check_completeness(root)
    if gaps:
        return [
            Finding(
                "unknown",
                f"profile incomplete: {len(gaps)} SUPPLY ask(s) - see `se-buddy asks`",
            )
        ]
    return [Finding("ok", "profile complete")]


def run() -> int:
    cwd = Path.cwd()
    install = check_install(repo_root(), cwd)
    runtime = _runtime_findings()
    profile = _profile_findings(cwd)

    for heading, findings in (
        ("install", install),
        ("runtime", runtime),
        ("profile", profile),
    ):
        print(f"{heading}:")
        for finding in findings:
            print(_render(finding))

    failed = [f for f in install + runtime + profile if f.failed]
    if failed:
        print(
            f"\nse-buddy doctor: refusing - {len(failed)} check(s) failed above, "
            "fix them and re-run",
            file=sys.stderr,
        )
        return 1

    # The deliberate non-claim (see this module's docstring). Everything the
    # CLI can reach is sound; whether the *reasoning* layer loaded is a thing
    # only the reasoning layer can answer, so say which of the two this was.
    if any(f.key == PLUGIN_LOADED and f.status == "ok" for f in install):
        print("\nse-buddy doctor: installation is sound and the plugin is loaded")
    else:
        print(
            "\nse-buddy doctor: the deterministic layer is sound. Plugin load is "
            "unconfirmed from here - run `/se-buddy:doctor` inside Claude Code to "
            "check the reasoning layer too"
        )
    return 0


def add_parser(subparsers) -> None:
    subparsers.add_parser("doctor", help="is this installation sound? (spec Sec.5.3)").set_defaults(
        func=lambda _args: run()
    )
