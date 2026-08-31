"""`se-buddy doctor` - is this installation sound? (spec Sec.5.3)

Phase 0 scope only: the venv and version checks of Sec.5.1 / Sec.7.1.
Profile completeness, model reachability, register/record validity and
AGENT-LOG acknowledgement arrive with the phases that give the agent a
profile, a model and registers to check against (Sec.5.3's table lists all
six; the other four are `no-op: reports nothing yet` until then).

By the time this module runs, bin/_bootstrap.py has already run under the
system interpreter and either found a working venv or rebuilt one - so
"present" and "capellambse importable" are already guaranteed here. What
this module still has to do itself is the one check Sec.7.1 says must
*refuse* rather than be silently repaired: a capellambse version that has
drifted from the pin.
"""

from __future__ import annotations

import sys

from se_buddy._pin import MIN_PYTHON, read_pin


def _floor_ok() -> bool:
    v = sys.version_info
    return (v.major, v.minor) >= MIN_PYTHON


def run() -> int:
    ok = True
    lines: list[str] = []

    have = sys.version.split()[0]
    want = ".".join(map(str, MIN_PYTHON))
    if _floor_ok():
        lines.append(f"[ok]   interpreter {have} (floor is {want})")
    else:
        ok = False
        lines.append(f"[FAIL] interpreter {have} is below the floor {want}")

    lines.append(f"[ok]   venv present at {sys.prefix}")

    pin = read_pin()
    installed = None
    try:
        import capellambse

        installed = capellambse.__version__
    except ImportError as exc:
        ok = False
        lines.append(f"[FAIL] capellambse is not importable in this venv: {exc}")

    if installed is not None:
        if installed == pin:
            lines.append(f"[ok]   capellambse {installed} matches the pin")
        else:
            ok = False
            lines.append(
                f"[FAIL] capellambse {installed} does not match the pin {pin} "
                "(this venv was changed outside se-buddy - see spec Sec.7.1)"
            )

    print("\n".join(lines))
    if ok:
        print("se-buddy doctor: installation is sound")
        return 0
    print("se-buddy doctor: refusing - fix the above and re-run", file=sys.stderr)
    return 1
