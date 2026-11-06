"""The AUR package is a ``-bin`` PKGBUILD kept in this repository.

``makepkg`` is the only real validator and it only runs on Arch, so these guards check the
contract this repository can control: the names, the release asset the package downloads, the
launcher it writes, and the metadata it installs from the same tag the release is cut from.
"""

import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUR_DIR = os.path.join(REPO_ROOT, "packaging", "aur")
PKGBUILD = os.path.join(AUR_DIR, "PKGBUILD")
SRCINFO = os.path.join(AUR_DIR, ".SRCINFO")
UPDATE_SCRIPT = os.path.join(AUR_DIR, "update_aur.sh")


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def test_the_package_is_a_binary_repackaging_of_the_release():
    pkgbuild = read(PKGBUILD)

    assert re.search(r"^pkgname=flatcam-plus-bin$", pkgbuild, re.M)
    assert '_release="${url}/releases/download/v${pkgver}"' in pkgbuild
    assert "FlatCAMPlus-${pkgver}-linux-x86_64.tar.gz::${_release}" in pkgbuild
    assert re.search(r"^arch=\('x86_64'\)$", pkgbuild, re.M)
    assert "!strip" in pkgbuild, "stripping a frozen bundle breaks its bundled libraries"


def test_the_version_is_the_manifest_version():
    import tomllib

    with open(os.path.join(REPO_ROOT, "pyproject.toml"), "rb") as handle:
        manifest = tomllib.load(handle)["project"]["version"]
    pkgbuild = read(PKGBUILD)

    assert re.search(r"^pkgver={0}$".format(re.escape(manifest)), pkgbuild, re.M), (
        "pkgver must match pyproject.toml; update_aur.sh keeps them in step"
    )


def test_the_package_installs_the_same_layout_and_metadata_as_the_others():
    pkgbuild = read(PKGBUILD)

    for path in (
        '"$pkgdir/opt/flatcam-plus"',
        '"$pkgdir/usr/bin/flatcam-plus"',
        "/usr/share/applications/flatcam-plus.desktop",
        "/usr/share/metainfo/flatcam-plus.metainfo.xml",
        "/usr/share/icons/hicolor/256x256/apps/flatcam-plus.png",
    ):
        assert path in pkgbuild, path
    assert "FLATCAM_PLUS_HOME" in pkgbuild, "the launcher has to honour the same override"


def test_the_metadata_files_come_from_the_tag_that_ships_them():
    pkgbuild = read(PKGBUILD)

    assert '_assets="${url}/raw/v${pkgver}/packaging/linux"' in pkgbuild
    assert "flatcam-plus.desktop::${_assets}/flatcam-plus.desktop" in pkgbuild
    assert "flatcam-plus.metainfo.xml::${_assets}/flatcam-plus.metainfo.xml" in pkgbuild
    assert "raw/v${pkgver}/flatcam_plus/assets/resources/app256.png" in pkgbuild


def test_the_srcinfo_matches_the_pkgbuild():
    srcinfo = read(SRCINFO)
    pkgbuild = read(PKGBUILD)

    assert "pkgbase = flatcam-plus-bin" in srcinfo
    version = re.search(r"^pkgver=(.+)$", pkgbuild, re.M).group(1)
    assert "\tpkgver = {0}".format(version) in srcinfo
    assert srcinfo.count("source = ") == pkgbuild.count("::")


def test_the_update_script_checks_for_its_toolchain():
    """It needs makepkg to regenerate .SRCINFO, and says so instead of failing halfway."""
    script = read(UPDATE_SCRIPT)

    assert "command -v makepkg" in script
    assert "makepkg is not on PATH" in script
    assert "makepkg --printsrcinfo" in script


def test_the_update_script_needs_a_version():
    import subprocess

    finished = subprocess.run([UPDATE_SCRIPT], capture_output=True, text=True, timeout=120)

    assert finished.returncode == 2
    assert "usage" in finished.stderr
