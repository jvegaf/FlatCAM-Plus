"""The version lives in the package, and every build script has to read it there.

The four build scripts extracted ``APP_VERSION`` with a regex over ``appVersion.py``, so moving
the metadata without them silently ships a package with the wrong version. This test is the
guard for that coupling while the rest of the modules move too.
"""

import os
import re

PACKAGING_SCRIPTS = (
    os.path.join("packaging", "linux", "build_linux_portable.sh"),
    os.path.join("packaging", "macos", "build_macos_dmg.sh"),
    os.path.join("packaging", "windows", "build_windows_installer.ps1"),
    os.path.join("packaging", "windows", "update_version.ps1"),
    "FlatCAMPlus_x64_installer_generator.bat",
)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_script(relative_path):
    with open(os.path.join(REPO_ROOT, relative_path), encoding="utf-8") as handle:
        return handle.read()


def test_package_exposes_the_version_metadata():
    from flatcam_plus.version import APP_NAME, APP_VERSION, APP_VERSION_DATE

    assert APP_NAME == "FlatCAM Plus"
    assert re.fullmatch(r"\d+\.\d+\.\d+", APP_VERSION)
    assert re.fullmatch(r"\d{4}\.\d{2}\.\d{2}", APP_VERSION_DATE)


def test_the_old_root_module_is_gone():
    assert not os.path.exists(os.path.join(REPO_ROOT, "appVersion.py"))


def test_every_build_script_reads_the_package_version_file():
    for script in PACKAGING_SCRIPTS:
        text = read_script(script)
        assert "appVersion.py" not in text, script
        assert "flatcam_plus" in text and "version.py" in text, script
