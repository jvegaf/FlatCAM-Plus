"""The Flatpak we publish is built from the manifest in ``packaging/flatpak``.

PyYAML is not a project dependency, so these guards read the manifest as text and resolve the
paths it names against the filesystem: that catches a renamed asset, a source that points at
nothing, or a sandbox permission that would quietly be too broad. The manifest itself is parsed by
``flatpak-builder`` in CI, which is the only thing that can validate the rest of it.
"""

import os
import re
import subprocess
import xml.etree.ElementTree as ElementTree

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLATPAK_DIR = os.path.join(REPO_ROOT, "packaging", "flatpak")
MANIFEST = os.path.join(FLATPAK_DIR, "io.github.thebestgoodguy.FlatCAMPlus.yml")
BUILD_SCRIPT = os.path.join(FLATPAK_DIR, "build_flatpak.sh")
LINUX_DIR = os.path.join(REPO_ROOT, "packaging", "linux")


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def manifest_sources():
    return re.findall(r"^\s+path: (.+)$", read(MANIFEST), re.MULTILINE)


def test_every_manifest_source_resolves_from_the_manifest_directory():
    """dist/ is where the build puts the payload, so only the tracked sources can be checked."""
    sources = [source.strip() for source in manifest_sources()]

    assert sources
    payload = [source for source in sources if source.startswith("../../dist/")]
    checked_in = [source for source in sources if source not in payload]
    assert payload == ["../../dist/linux"], "the payload source is the bundle the other packages use"
    assert checked_in, sources
    for source in checked_in:
        assert os.path.exists(os.path.normpath(os.path.join(FLATPAK_DIR, source))), source


def test_the_app_id_is_the_one_the_metadata_announces():
    metainfo = ElementTree.parse(os.path.join(LINUX_DIR, "flatcam-plus.metainfo.xml")).getroot()
    declared = re.search(r"^app-id: (.+)$", read(MANIFEST), re.MULTILINE).group(1).strip()

    assert declared == metainfo.find("id").text
    assert "flatcam-plus" in read(MANIFEST).split("command:")[1].splitlines()[0]


def test_the_sandbox_asks_for_no_more_than_it_needs():
    manifest = read(MANIFEST)

    assert "--filesystem=home" not in manifest
    assert "--filesystem=host" not in manifest
    assert "--socket=fallback-x11" in manifest
    assert "--device=dri" in manifest, "the plot canvas needs the GPU"
    assert "--env=FLATCAM_PLUS_HOME=/app/lib/flatcam-plus" in manifest, (
        "the launcher the deb and the rpm install only knows /opt"
    )


def test_the_build_installs_the_files_a_desktop_expects():
    manifest = read(MANIFEST)

    for destination in (
        "/app/lib/flatcam-plus",
        "/app/bin/flatcam-plus",
        "/app/share/applications/flatcam-plus.desktop",
        "/app/share/icons/hicolor/256x256/apps/flatcam-plus.png",
        "/app/share/metainfo/flatcam-plus.metainfo.xml",
    ):
        assert destination in manifest, destination


def test_the_build_script_takes_the_version_from_the_manifest():
    script = read(BUILD_SCRIPT)

    assert "pyproject.toml" in script and "tomllib" in script
    assert "flatpak-builder" in script and "build-bundle" in script
    assert ".flatpak" in script


def test_the_build_script_explains_a_missing_toolchain(tmp_path):
    finished = subprocess.run(
        [BUILD_SCRIPT, "--skip-bundle"],
        capture_output=True,
        text=True,
        env=dict(os.environ, PATH="/usr/bin:/bin"),
        timeout=120,
    )

    assert finished.returncode == 1
    assert "flatpak-builder is not on PATH" in finished.stderr


def test_the_build_script_rejects_an_unknown_argument():
    finished = subprocess.run([BUILD_SCRIPT, "--bogus"], capture_output=True, text=True, timeout=120)

    assert finished.returncode == 2
    assert "unknown argument" in finished.stderr


def test_the_release_publishes_the_flatpak_next_to_the_packages():
    release = read(os.path.join(REPO_ROOT, ".github", "workflows", "release.yml"))

    assert "packaging/flatpak/build_flatpak.sh" in release
    assert "dist/installer/*.flatpak" in release
    assert re.search(r"needs: \[linux-packages, windows-installer, flatpak, meta\]", release)


def test_the_workflow_uses_flags_flatpak_actually_has():
    """Flatpak 1.14 rejects --yes; the install has to use its own spelling."""
    release = read(os.path.join(REPO_ROOT, ".github", "workflows", "release.yml"))
    flatpak_lines = [line for line in release.splitlines() if "flatpak install" in line]

    assert flatpak_lines, "the pipeline no longer installs a runtime"
    for line in flatpak_lines:
        assert "--yes" not in line, line
        assert " -y " in line or "--assumeyes" in line, line
