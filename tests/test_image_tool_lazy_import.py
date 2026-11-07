"""Importing the Image tool must not import pyppeteer.

``flatcam_plus/appPlugins/ToolImage.py`` imported ``check_chromium`` from
``pyppeteer.chromium_downloader`` at module scope, and ``appMain`` imports every tool
plugin at start-up, so the whole ``pyppeteer`` package (plus ``websockets``, ``urllib3``,
``tqdm`` and ``appdirs``) was pulled in on every launch to answer one question: "is a
Chromium binary present?".  That check only matters when an image is imported in trace
mode.

The cost is not only start-up time: ``pyppeteer/us_keyboard_layout.py`` contains invalid
escape sequences, so Python 3.14 prints ``SyntaxWarning`` noise the first time that file
is compiled.  Importing the check where it is used keeps both consequences inside the
trace path.

These tests run in a fresh interpreter so ``sys.modules`` reflects one import, not the
state pytest accumulated.
"""

import os
import subprocess
import sys
import textwrap

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_IMPORT_SCRIPT = textwrap.dedent(
    """
    import importlib
    import sys

    tool_image = importlib.import_module("flatcam_plus.appPlugins.ToolImage")

    print("PYPPETEER_IMPORTED=%s" % ("pyppeteer" in sys.modules))
    print("CHECK_CHROMIUM_CALLABLE=%s" % callable(tool_image.check_chromium))
    """
)

_CALL_SCRIPT = textwrap.dedent(
    """
    import importlib

    tool_image = importlib.import_module("flatcam_plus.appPlugins.ToolImage")

    result = tool_image.check_chromium()
    print("RESULT_TYPE=%s" % type(result).__name__)
    """
)


def _run(script):
    return subprocess.run(
        [sys.executable, "-c", script],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )


def test_importing_the_image_tool_does_not_import_pyppeteer():
    result = _run(_IMPORT_SCRIPT)

    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "PYPPETEER_IMPORTED=False" in result.stdout, (
        "importing flatcam_plus.appPlugins.ToolImage pulled pyppeteer into sys.modules; "
        f"stdout={result.stdout!r}"
    )
    assert "CHECK_CHROMIUM_CALLABLE=True" in result.stdout, (
        f"ToolImage.check_chromium is not reachable at module scope; stdout={result.stdout!r}"
    )


def test_check_chromium_still_answers_after_the_lazy_import():
    result = _run(_CALL_SCRIPT)

    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "RESULT_TYPE=bool" in result.stdout, (
        "the deferred check_chromium import did not return a bool; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
