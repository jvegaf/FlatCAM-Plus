"""The version has one source: ``pyproject.toml``.

``flatcam_plus.version`` no longer carries the number: it reads ``[project] version`` from
``pyproject.toml`` at import time, and every build script reads that same file with the tool it
already uses. Two hand-maintained numbers drifted once — the README announced 1.1.0 while the
module said 1.2.0 — so this pins the whole chain: pyproject, then the module, then the scripts.
"""

import os
import pathlib
import re
import subprocess
import sys
import tomllib

import pytest

# Scripts that only consume the version: they must get it from pyproject.toml.
VERSION_READERS = (
    os.path.join("packaging", "linux", "build_linux_portable.sh"),
    os.path.join("packaging", "macos", "build_macos_dmg.sh"),
    os.path.join("packaging", "windows", "build_windows_installer.ps1"),
    "FlatCAMPlus_x64_installer_generator.bat",
)

# The release helper writes the version into pyproject.toml and the release date into the module.
VERSION_WRITER = os.path.join("packaging", "windows", "update_version.ps1")

# Bundles must ship the manifest, because the frozen app reads its version from it. The batch
# wrapper only drives the Windows installer script, so it builds nothing itself.
BUNDLE_SCRIPTS = (
    os.path.join("packaging", "linux", "build_linux_portable.sh"),
    os.path.join("packaging", "macos", "build_macos_dmg.sh"),
    os.path.join("packaging", "windows", "build_windows_installer.ps1"),
    "build_standalone.ps1",
)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_repo_file(relative_path):
    with open(os.path.join(REPO_ROOT, relative_path), encoding="utf-8") as handle:
        return handle.read()


def declared_version():
    with open(os.path.join(REPO_ROOT, "pyproject.toml"), "rb") as handle:
        return tomllib.load(handle)["project"]["version"]


def test_package_exposes_the_version_metadata():
    from flatcam_plus.version import APP_NAME, APP_VERSION, APP_VERSION_DATE

    assert APP_NAME == "FlatCAM Plus"
    assert re.fullmatch(r"\d+\.\d+\.\d+", APP_VERSION)
    assert re.fullmatch(r"\d{4}\.\d{2}\.\d{2}", APP_VERSION_DATE)


def test_the_module_reports_the_pyproject_version():
    from flatcam_plus.version import APP_VERSION

    assert APP_VERSION == declared_version()


def test_the_module_holds_no_version_number_of_its_own():
    text = read_repo_file(os.path.join("flatcam_plus", "version.py"))

    assert not re.search(r'APP_VERSION\s*=\s*["\']\d', text), "the number belongs in pyproject.toml"
    assert "tomllib" in text


def test_the_old_root_module_is_gone():
    assert not os.path.exists(os.path.join(REPO_ROOT, "appVersion.py"))


def test_every_version_reader_asks_pyproject():
    for script in VERSION_READERS:
        text = read_repo_file(script)
        assert "pyproject.toml" in text, script
        assert "version.py" not in text, script


def test_the_release_helper_writes_pyproject_and_the_release_date():
    text = read_repo_file(VERSION_WRITER)

    assert "pyproject.toml" in text
    assert "version.py" in text and "APP_VERSION_DATE" in text


def test_every_bundle_ships_the_manifest():
    for script in BUNDLE_SCRIPTS:
        shipped = [
            line
            for line in read_repo_file(script).splitlines()
            if "add-data" in line and "pyproject.toml" in line
        ]
        assert shipped, script


def test_pyproject_is_bom_free():
    """tomllib rejects a BOM, so the manifest has to stay plain UTF-8."""
    raw = (pathlib.Path(REPO_ROOT) / "pyproject.toml").read_bytes()

    assert not raw.startswith(b"\xef\xbb\xbf")
    assert tomllib.loads(raw.decode("utf-8"))["project"]["version"] == declared_version()


def test_the_release_helper_never_writes_a_bom():
    for line in read_repo_file(VERSION_WRITER).splitlines():
        if "WriteAllText" in line:
            assert "${utf8NoBom}" in line or "$utf8NoBom" in line, line
            assert "[System.Text.Encoding]::UTF8" not in line, line


def test_the_release_helper_writes_the_date_the_module_declares():
    text = read_repo_file(VERSION_WRITER)

    assert 'Get-Date -Format "yyyy.MM.dd"' in text


def test_the_windows_regex_hits_the_project_entry():
    """The .ps1 and .bat pattern must find [project] version and nothing earlier."""
    pattern = re.compile(r'^version\s*=\s*"([^"]+)"')
    hits = [
        match.group(1)
        for line in read_repo_file("pyproject.toml").splitlines()
        for match in [pattern.match(line)]
        if match
    ]

    assert hits == [declared_version()]


def test_the_module_falls_back_to_the_installed_distribution(monkeypatch):
    """An installed wheel has no manifest beside the package: the metadata carries the number."""
    import flatcam_plus.version as version_module

    monkeypatch.setattr(version_module, "_locate_pyproject", lambda: None)

    assert version_module._read_app_version() == declared_version()


def test_the_module_raises_when_neither_source_answers(monkeypatch):
    import flatcam_plus.version as version_module

    monkeypatch.setattr(version_module, "_locate_pyproject", lambda: None)
    monkeypatch.setattr(version_module, "_installed_distribution_version", lambda: None)

    with pytest.raises(RuntimeError, match="the version cannot be read"):
        version_module._read_app_version()


def test_the_bundle_reads_the_manifest_beside_the_executable(tmp_path):
    bundle = tmp_path / "bundle"
    (bundle / "flatcam_plus").mkdir(parents=True)
    (bundle / "pyproject.toml").write_bytes(
        (pathlib.Path(REPO_ROOT) / "pyproject.toml").read_bytes()
    )
    (bundle / "flatcam_plus" / "__init__.py").write_text("", encoding="utf-8")
    (bundle / "flatcam_plus" / "version.py").write_text(
        read_repo_file(os.path.join("flatcam_plus", "version.py")), encoding="utf-8"
    )
    code = (
        "import sys; sys._MEIPASS = {0!r}\n"
        "from flatcam_plus.version import APP_VERSION\n"
        "print(APP_VERSION)\n".format(str(bundle))
    )

    finished = subprocess.run(
        [sys.executable, "-c", code], cwd=bundle, capture_output=True, text=True
    )

    assert finished.returncode == 0, finished.stderr
    assert finished.stdout.strip() == declared_version()


def test_documented_manual_builds_ship_the_manifest():
    """Every PyInstaller recipe in PACKAGING.md must add pyproject.toml as data."""
    recipes = re.findall(
        r"python -m PyInstaller flatcam_plus/launcher\.py.*?```", read_repo_file("PACKAGING.md"), re.S
    )

    assert recipes
    for recipe in recipes:
        assert '--add-data "pyproject.toml:."' in recipe, recipe
        assert '--add-data "flatcam_plus/assets:flatcam_plus/assets"' in recipe, recipe
