"""Bootstraps the vendored venv for se-buddy (spec Sec.5.1).

Run by bin/se-buddy and bin/se-buddy.cmd, under the bare system interpreter,
before every command - never from inside vendor/.venv itself. That split
matters: rebuilding a venv from its own python would mean deleting the
directory holding the interpreter that is currently running.

On success this script prints exactly one line to stdout: the path to the
venv's python. Everything else - progress, and any failure - goes to
stderr, and failures are reported as one clear message, never a raw
traceback (spec Sec.5.1: "never a stack trace from an import").
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from se_buddy._pin import MIN_PYTHON, read_pin  # noqa: E402  (path set up above)

VENV_DIR = ROOT / "vendor" / ".venv"
VENDOR_SRC = ROOT / "vendor" / "py-capellambse"
LOCKFILE = ROOT / "lockfile"


class BootstrapError(Exception):
    """A clean, user-facing bootstrap failure."""


def _fail(message: str) -> None:
    raise BootstrapError(message)


def check_interpreter_floor() -> None:
    v = sys.version_info
    if (v.major, v.minor) < MIN_PYTHON:
        have = f"{v.major}.{v.minor}.{v.micro}"
        want = ".".join(map(str, MIN_PYTHON))
        _fail(
            f"this interpreter is Python {have}; se-buddy needs {want}+ "
            f"(the capellambse pin's floor). Install a newer Python and re-run."
        )


def venv_python() -> Path:
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def venv_is_importable() -> bool:
    """Whether the venv exists and capellambse can be imported in it.

    Deliberately does not check the *version* - a pin mismatch inside an
    otherwise-working venv is `se-buddy doctor`'s job to catch and refuse on
    (spec Sec.7.1), not something the launcher silently reinstalls over.
    """
    py = venv_python()
    if not py.exists():
        return False
    proc = _run([str(py), "-c", "import capellambse"])
    return proc.returncode == 0


def _diagnose_pip_failure(proc: subprocess.CompletedProcess) -> str:
    output = (proc.stdout or "") + (proc.stderr or "")
    lowered = output.lower()
    offline_markers = (
        "temporary failure in name resolution",
        "failed to establish a new connection",
        "network is unreachable",
        "connection timed out",
        "could not find a version that satisfies",
        "max retries exceeded",
        "name or service not known",
    )
    if any(marker in lowered for marker in offline_markers):
        return (
            "could not reach the package index - this clone looks offline. "
            f"se-buddy needs network once, to install the pinned dependencies "
            f"from {LOCKFILE} into {VENV_DIR}."
        )
    tail = "\n".join(output.strip().splitlines()[-8:])
    return f"pip exited {proc.returncode}. Last output:\n{tail}"


def _wheel_failure_reason(proc: subprocess.CompletedProcess) -> str:
    """Why the prebuilt-wheel attempt did not install anything.

    Kept separate from `_diagnose_pip_failure` because the two contexts read
    the same pip output differently. "could not find a version that satisfies"
    is an offline symptom when installing from the lockfile, but under
    `--only-binary` it is the ordinary, online answer for a platform with no
    wheel - diagnosing that as "this clone looks offline" would send the
    engineer after the wrong problem.
    """
    output = (proc.stdout or "") + (proc.stderr or "")
    lowered = output.lower()

    if "no matching distribution" in lowered or "could not find a version" in lowered:
        return "no prebuilt wheel matches this platform and interpreter"

    offline_markers = (
        "temporary failure in name resolution",
        "failed to establish a new connection",
        "network is unreachable",
        "connection timed out",
        "max retries exceeded",
        "name or service not known",
    )
    if any(marker in lowered for marker in offline_markers):
        return "the package index was unreachable"

    tail = output.strip().splitlines()
    return f"pip exited {proc.returncode}: {tail[-1] if tail else 'no output'}"


def _install_capellambse(py: Path, pin: str) -> None:
    """Installs capellambse=={pin}: prebuilt wheel first, vendored source second.

    capellambse ships abi3 wheels for macOS (arm64/x86-64), manylinux and
    musllinux (aarch64/x86-64) and Windows (win32/amd64), so on every platform
    this project realistically targets there is a wheel and nothing is
    compiled. Building from `vendor/py-capellambse` instead - which is what
    this did unconditionally until now - forced a Rust toolchain onto every
    engineer installing this, and for a systems engineer rather than a
    developer that is where the install tends to stop.

    The vendored submodule stays, as the fallback for a platform with no wheel
    and as the offline route, so nothing that used to work stops working.

    What this trades away, stated plainly because it is a real cost: the
    submodule pinned an exact commit, and a version pin does not. `==` fixes
    the version, and `doctor` still refuses on drift from it (spec Sec.7.1),
    but the artefact now comes from an index rather than from a SHA this
    repository records. Hash-pinning the wheel in `lockfile` would recover
    that; it is not done here.
    """
    print(f"se-buddy: installing capellambse=={pin} from a prebuilt wheel ...", file=sys.stderr)
    proc = _run(
        [str(py), "-m", "pip", "install", "--no-deps", "--only-binary", ":all:", f"capellambse=={pin}"]
    )
    if proc.returncode == 0:
        return

    reason = _wheel_failure_reason(proc)
    print(f"se-buddy: {reason} - falling back to {VENDOR_SRC}", file=sys.stderr)

    if not VENDOR_SRC.exists() or not any(VENDOR_SRC.iterdir()):
        _fail(
            f"could not install a prebuilt capellambse=={pin} wheel ({reason}), and "
            f"{VENDOR_SRC} is missing or empty so there is nothing to build from "
            "instead. Run: git submodule update --init --recursive"
        )

    if shutil.which("cargo") is None or shutil.which("rustc") is None:
        _fail(
            f"could not install a prebuilt capellambse=={pin} wheel ({reason}), so it "
            f"has to be built from {VENDOR_SRC} - and that needs a Rust toolchain "
            "(rustc/cargo), which is not on PATH. Install one from https://rustup.rs "
            "and re-run `se-buddy doctor`."
        )

    print(f"se-buddy: building capellambse=={pin} from {VENDOR_SRC} ...", file=sys.stderr)
    proc = _run([str(py), "-m", "pip", "install", "--no-deps", str(VENDOR_SRC)])
    if proc.returncode != 0:
        _fail(f"building capellambse from {VENDOR_SRC} failed: {_diagnose_pip_failure(proc)}")


def build_venv(pin: str) -> None:
    if not LOCKFILE.exists():
        _fail(f"{LOCKFILE} is missing - cannot install pinned dependencies without it")

    if VENV_DIR.exists():
        shutil.rmtree(VENV_DIR, ignore_errors=True)

    print(f"se-buddy: creating the venv at {VENV_DIR} ...", file=sys.stderr)
    proc = _run([sys.executable, "-m", "venv", str(VENV_DIR)])
    if proc.returncode != 0:
        shutil.rmtree(VENV_DIR, ignore_errors=True)
        _fail(f"could not create the venv: {proc.stderr.strip()}")

    # A half-built venv is worse than none: `venv_is_importable` would keep
    # returning False and every subsequent run would rebuild from scratch
    # without ever saying why. Any failure past this point removes it.
    try:
        _install_capellambse(venv_python(), pin)

        print(f"se-buddy: installing pinned dependencies from {LOCKFILE} ...", file=sys.stderr)
        proc = _run([str(venv_python()), "-m", "pip", "install", "-r", str(LOCKFILE)])
        if proc.returncode != 0:
            _fail(
                f"installing pinned dependencies from {LOCKFILE} failed: "
                f"{_diagnose_pip_failure(proc)}"
            )
    except BootstrapError:
        shutil.rmtree(VENV_DIR, ignore_errors=True)
        raise


def ensure_venv() -> Path:
    """Ensures vendor/.venv exists and capellambse imports in it. Returns its python."""
    check_interpreter_floor()
    if not venv_is_importable():
        print("se-buddy: venv missing or incomplete - bootstrapping", file=sys.stderr)
        build_venv(read_pin())
        if not venv_is_importable():
            _fail("venv still not importable after bootstrapping - see the messages above")
    return venv_python()


def main() -> int:
    try:
        py = ensure_venv()
    except BootstrapError as exc:
        print(f"se-buddy: {exc}", file=sys.stderr)
        return 1
    print(py)
    return 0


if __name__ == "__main__":
    sys.exit(main())
