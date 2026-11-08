"""A frozen build must find its data inside the package, not beside the executable.

PyInstaller 6 lays an onedir bundle out as ``<app>/FlatCAM-Plus`` plus ``<app>/_internal/``, and
``--add-data`` puts every data directory inside ``_internal`` too. The application resolves its data
from the package directory, so the bundle has to place them at ``_internal/flatcam_plus/``: this
probe builds that shape and asserts the application resolves the data from it.

The source checkout is covered by ``tests/test_app_paths.py``; this is the frozen half, which no
packaging script could prove before.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import PurePosixPath

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGE_DIR = os.path.join(REPO_ROOT, "flatcam_plus")
DATA_DIRECTORIES = ("assets", "config", "locale", "preprocessors")


def test_a_frozen_tree_resolves_the_data_inside_the_package(tmp_path):
    internal = tmp_path / "FlatCAM-Plus" / "_internal"
    internal.mkdir(parents=True)
    shutil.copytree(
        PACKAGE_DIR,
        internal / "flatcam_plus",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    # The bundle ships the manifest here too: the version module reads it at import.
    shutil.copy(os.path.join(REPO_ROOT, "pyproject.toml"), internal / "pyproject.toml")

    probe = (
        "from flatcam_plus.appMain import _APP_ROOT\n"
        "import os\n"
        "print(os.path.realpath(_APP_ROOT))\n"
        "print(all(os.path.isdir(os.path.join(_APP_ROOT, name)) "
        "for name in {0!r}))\n".format(DATA_DIRECTORIES)
    )
    finished = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=str(internal),
        capture_output=True,
        text=True,
        env=dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONPATH=str(internal)),
        timeout=300,
    )

    assert finished.returncode == 0, finished.stderr
    resolved, data_found = finished.stdout.split()
    assert resolved == os.path.realpath(str(internal / "flatcam_plus"))
    assert data_found == "True"


BUILD_SCRIPTS = (
    os.path.join("packaging", "linux", "build_linux_portable.sh"),
)

# ``pyproject.toml`` is the one file that has to stay at the bundle root: the version module reads it
# from ``sys._MEIPASS``. Everything else has to land inside the package.
MANIFEST_DESTINATION = "."


def test_the_build_scripts_ship_the_data_into_the_package():
    """PyInstaller puts ``--add-data`` under ``<_internal>/<dest>``, which must be the package."""
    pattern = re.compile(r'--add-data\s+"([^"]+)"')
    for script in BUILD_SCRIPTS:
        with open(os.path.join(REPO_ROOT, script), encoding="utf-8") as handle:
            destinations = [
                entry.split(":", 1)[-1] for entry in pattern.findall(handle.read())
            ]
        assert destinations, script
        for destination in destinations:
            assert not destination.startswith("/"), (script, destination)
            assert ".." not in destination, (script, destination)
            assert ";" not in destination, (script, destination)
            assert not destination.startswith("_internal"), (
                "PyInstaller already nests --add-data under _internal",
                script,
                destination,
            )
            assert destination == MANIFEST_DESTINATION or destination.startswith(
                "flatcam_plus/"
            ), (
                "the data directories live inside the package, so the bundle destination has to "
                "match; anything else leaves _APP_ROOT pointing at an empty directory",
                script,
                destination,
            )


def test_the_windows_helper_ships_the_data_into_the_package():
    """The Windows script builds its data arguments differently, so it needs its own guard."""
    with open(
        os.path.join(REPO_ROOT, "packaging", "windows", "build_windows_installer.ps1"),
        encoding="utf-8",
    ) as handle:
        pairs = re.findall(r'New-PyInstallerDataArg\s+"([^"]+)"\s+"([^"]+)"', handle.read())

    assert pairs
    for source, destination in pairs:
        assert destination and not destination.startswith("_internal"), (source, destination)
        assert "\\" not in destination and ":" not in destination, (source, destination)
        # PyInstaller 6 treats the destination as a directory and appends the basename of the
        # source. Naming the destination after the source basename therefore nests the file inside
        # a directory of that name: the manifest landed in "_internal/pyproject.toml/pyproject.toml",
        # so version.py found no file and the frozen app could not start.
        assert destination != PurePosixPath(source.replace("\\", "/")).name, (
            "PyInstaller appends the source basename to the destination, so this pair nests the "
            'file inside a directory of its own name; use "." for a file source',
            source,
            destination,
        )
        assert destination == MANIFEST_DESTINATION or destination.startswith(
            "flatcam_plus/"
        ), (
            "the data directories live inside the package, so the bundle destination has to "
            "match; anything else leaves _APP_ROOT pointing at an empty directory",
            source,
            destination,
        )

    # The version module reads the manifest from the bundle root at import time, so the pair has to
    # exist; deleting the line must not silently pass this guard.
    assert ("pyproject.toml", MANIFEST_DESTINATION) in pairs, pairs


def test_freeze_support_runs_before_the_application_import(tmp_path):
    """A frozen ``forkserver`` child must answer the handshake before ``sys.argv`` is parsed.

    Python 3.14 made ``forkserver`` the default start method on Linux, and its child is
    re-executed with a ``-c "from multiprocessing.forkserver import main; main(...)"`` style
    command line. ``flatcam_plus.appMain`` parses ``sys.argv`` with getopt in the ``App`` class
    body, so importing it in that child raises ``getopt.GetoptError`` and calls ``sys.exit(2)``
    before the handshake is answered; the parent then dies on ``ConnectionResetError`` when it
    builds its ``Pool``. ``freeze_support()`` therefore has to run at module level, before any
    import that can parse the command line.
    """
    probe = (
        "import multiprocessing, sys\n"
        "calls = []\n"
        "def spy():\n"
        "    calls.append('flatcam_plus.appMain' in sys.modules)\n"
        "multiprocessing.freeze_support = spy\n"
        "import flatcam_plus.launcher  # noqa: F401\n"
        "print('CALLS', calls)\n"
        "print('APPMAIN', 'flatcam_plus.appMain' in sys.modules)\n"
    )
    finished = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=dict(
            os.environ,
            QT_QPA_PLATFORM="offscreen",
            HOME=str(tmp_path),
            XDG_CONFIG_HOME=str(tmp_path / ".config"),
            PYTHONPATH=REPO_ROOT,
        ),
        timeout=300,
    )

    assert finished.returncode == 0, finished.stderr
    lines = {line.split(" ", 1)[0]: line.split(" ", 1)[1] for line in finished.stdout.splitlines()}
    # The import has to reach the application, or a probe that never imports it would pass.
    assert lines.get("APPMAIN") == "True", finished.stdout
    assert lines.get("CALLS") == "[False]", (
        "freeze_support() has to run before the import that parses sys.argv; a frozen forkserver "
        "child re-executes the entry point with its own -c command line, and appMain's "
        "import-time getopt exits on it before the handshake is answered",
        finished.stdout,
    )
