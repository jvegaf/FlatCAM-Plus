"""Shared setup for the FlatCAM Plus test suite.

The application is one process-wide ``App`` object built by ``flatcam.py``. Tests that need
the real wiring build it once, headless and offline, under an isolated ``HOME`` so a test
run never reads or writes the developer's ``~/.FlatCAM`` settings.

The repository root is on ``sys.path`` through the ``pythonpath`` setting in
``pyproject.toml``, not through an insert here: the application packages live beside
``flatcam_plus`` at the root and are imported by name.
"""

import os
import sys
import tempfile

import pytest

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# ``flatcam_plus.appMain.App`` parses ``sys.argv`` with getopt at import time and exits on
# unknown options, so the arguments pytest was started with must not leak into the application.
sys.argv = ["flatcam"]

# Qt must not need a display server, and the engine is chosen before the app exists.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Both variables must be in place before the first module imports Qt: Qt resolves and caches
# its user-scope settings directory at first use, so setting them from a fixture is too late
# and the app would write into the real ``~/.config``.
SESSION_HOME = tempfile.mkdtemp(prefix="flatcam-test-home-")
os.environ["HOME"] = SESSION_HOME
os.environ["XDG_CONFIG_HOME"] = os.path.join(SESSION_HOME, ".config")


@pytest.fixture(scope="session")
def isolated_home():
    """The throwaway data directory the whole session is confined to."""
    return SESSION_HOME


@pytest.fixture(scope="session")
def fc_app(isolated_home):
    """Build the real application once, headless, and shut it down at the end."""
    from PyQt6 import QtWidgets

    qapp = QtWidgets.QApplication.instance() or QtWidgets.QApplication(["flatcam"])

    from flatcam_plus.appMain import App

    app = App(qapp=qapp, startup_project_request=None)
    try:
        yield app
    finally:
        app.quit_application()
        qapp.processEvents()


@pytest.fixture(scope="session")
def sample_input():
    """Read a sample manufacturing file from ``tests/data`` as a parser line list."""

    def read(name):
        with open(os.path.join(DATA_DIR, name), encoding="utf-8") as handle:
            return handle.read().splitlines()

    return read
