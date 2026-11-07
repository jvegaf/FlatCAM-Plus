"""The launcher must explain a missing Tcl/Tk instead of raising a bare ImportError.

``tkinter`` is a stdlib module, but its ``_tkinter`` extension links against the system
``libtk``. No Python dependency list can install that library, so a stock ``uv sync`` on
Linux can leave the app unstartable while ``pyproject.toml`` looks complete. The raw
``ImportError: libtk8.6.so: cannot open shared object file`` names a library the user never
asked for and never sees mentioned in the project requirements.

These tests block ``tkinter`` from inside the process so the condition is reproduced on any
machine, whether or not the interpreter under test has Tcl/Tk installed.
"""

import os
import subprocess
import sys
import textwrap

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Importing the launcher reaches ``flatcam_plus.appMain``, which imports ``tkinter`` at module
# scope. Fail the import the way a missing ``libtk`` does, and record it so the assertion can
# tell the blocker apart from an unrelated failure.
_BLOCKED_TKINTER_SCRIPT = textwrap.dedent(
    """
    import sys

    class _BlockTkinter:
        def find_spec(self, fullname, path=None, target=None):
            if fullname == "tkinter" or fullname.startswith("tkinter."):
                raise ImportError(
                    "libtk8.6.so: cannot open shared object file: No such file or directory"
                )
            return None

    sys.meta_path.insert(0, _BlockTkinter())

    import flatcam_plus.launcher
    sys.stderr.write("FALLBACK: launcher imported without Tcl/Tk\\n")
    """
)


def _run_without_tkinter():
    return subprocess.run(
        [sys.executable, "-c", _BLOCKED_TKINTER_SCRIPT],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )


def test_missing_tcl_tk_exits_non_zero():
    result = _run_without_tkinter()

    assert result.returncode != 0, (
        "the launcher continued past a missing Tcl/Tk; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "FALLBACK: launcher imported without Tcl/Tk" not in result.stderr, (
        "the launcher imported normally after tkinter failed"
    )


def test_missing_tcl_tk_names_the_system_package():
    result = _run_without_tkinter()
    output = result.stdout + result.stderr

    # The user has to learn three things: that Tcl/Tk is the problem, that it is a system
    # package rather than a Python one, and which command installs it on their platform.
    assert "Tcl/Tk" in output, f"the message never names Tcl/Tk; got: {output!r}"
    assert "tk" in output, f"the message never names the system package; got: {output!r}"
    assert "pacman" in output or "apt" in output or "dnf" in output, (
        f"the message gives no install command for any Linux distribution; got: {output!r}"
    )


def test_missing_tcl_tk_reports_the_underlying_cause():
    result = _run_without_tkinter()
    output = result.stdout + result.stderr

    assert "libtk8.6.so" in output, (
        f"the message drops the underlying import error; got: {output!r}"
    )
    assert "Traceback (most recent call last)" not in output, (
        f"the user still gets a bare traceback instead of guidance; got: {output!r}"
    )
