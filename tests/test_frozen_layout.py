"""A frozen build must find its data next to the package, not next to the executable.

PyInstaller 6 lays an onedir bundle out as ``<app>/FlatCAM-Plus`` plus ``<app>/_internal/``, and
``--add-data`` puts every data directory inside ``_internal`` too. ``_APP_ROOT`` is
``dirname(dirname(__file__))``, so the package and the data have to stay siblings: this probe builds
that shape and asserts the application resolves the data from it.

The source checkout is covered by ``tests/test_app_paths.py``; this is the frozen half, which no
packaging script could prove before.
"""

import os
import re
import shutil
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIRECTORIES = ("assets", "preprocessors")


def test_a_frozen_tree_resolves_the_data_beside_the_package(tmp_path):
    internal = tmp_path / "FlatCAM-Plus" / "_internal"
    internal.mkdir(parents=True)
    shutil.copytree(
        os.path.join(REPO_ROOT, "flatcam_plus"),
        internal / "flatcam_plus",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    for name in DATA_DIRECTORIES:
        (internal / name).mkdir()
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
    assert resolved == os.path.realpath(str(internal))
    assert data_found == "True"


BUILD_SCRIPTS = (
    os.path.join("packaging", "linux", "build_linux_portable.sh"),
    os.path.join("packaging", "macos", "build_macos_dmg.sh"),
)


def test_the_build_scripts_keep_the_data_inside_the_bundle_root():
    """PyInstaller puts ``--add-data`` under ``<_internal>/<dest>``, which is what ``_APP_ROOT`` is."""
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
