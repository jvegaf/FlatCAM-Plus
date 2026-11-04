"""Shared setup for the FlatCAM Plus test suite.

The application is one process-wide ``App`` object built by ``flatcam.py``. Tests that need
the real wiring build it once, headless and offline, under an isolated ``HOME`` so a test
run never reads or writes the developer's ``~/.FlatCAM`` settings.
"""

import os
import sys
import tempfile

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# ``appMain.App`` parses ``sys.argv`` with getopt at import time and exits on unknown
# options, so the arguments pytest was started with must not leak into the application.
sys.argv = ["flatcam"]

# Qt must not need a display server, and the engine is chosen before the app exists.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def isolated_home():
    """Point the application at a throwaway data directory for the whole session."""
    home = tempfile.mkdtemp(prefix="flatcam-test-home-")
    os.environ["HOME"] = home
    os.environ["XDG_CONFIG_HOME"] = os.path.join(home, ".config")
    return home


@pytest.fixture(scope="session")
def fc_app(isolated_home):
    """Build the real application once, headless, and shut it down at the end."""
    from PyQt6 import QtWidgets

    qapp = QtWidgets.QApplication.instance() or QtWidgets.QApplication(["flatcam"])

    from appMain import App

    app = App(qapp=qapp, startup_project_request=None)
    try:
        yield app
    finally:
        app.quit_application()
        qapp.processEvents()
