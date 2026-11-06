"""The command line has to answer ``--version``.

A packaged build is verified without a display: the installer runs the binary, asks it for its
version and compares it with the package metadata. The application parses ``sys.argv`` with
``getopt`` at import time and exits 2 on an unknown option, so before this flag existed there was
no way to ask a bundle what it was.

The entry point is ``python -m flatcam_plus``; the repository root stays on ``PYTHONPATH`` so the
probe works in a plain checkout as well as in an environment that installed the project.
"""

import os
import subprocess
import sys
import tomllib

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_cli(*arguments):
    environment = dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONPATH=REPO_ROOT)
    return subprocess.run(
        [sys.executable, "-m", "flatcam_plus", *arguments],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=environment,
        timeout=180,
    )


def declared_version():
    with open(os.path.join(REPO_ROOT, "pyproject.toml"), "rb") as handle:
        return tomllib.load(handle)["project"]["version"]


def test_version_flag_prints_the_version_and_exits_zero():
    finished = run_cli("--version")

    assert finished.returncode == 0, finished.stderr
    assert declared_version() in finished.stdout


def test_the_help_text_lists_the_version_flag():
    finished = run_cli("-h")

    assert finished.returncode == 0
    assert "--version" in finished.stdout
