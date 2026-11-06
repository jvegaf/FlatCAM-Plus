"""Version metadata for FlatCAM Plus.

``pyproject.toml`` is the single source of truth: this module reads ``[project] version`` from it
instead of carrying a copy of the number, and every build script reads the same file.

The three ways the application runs each reach that number differently:

* from a checkout, ``pyproject.toml`` sits one level above the package;
* from a frozen bundle, the build scripts ship it beside the executable (``sys._MEIPASS``);
* from an installed wheel nothing sits beside the package, so the installed distribution metadata
  carries the version that ``pyproject.toml`` declared at build time.
"""

import sys
import tomllib
from importlib import metadata
from pathlib import Path

APP_NAME = "FlatCAM Plus"
APP_VERSION_DATE = "2026.11.05"
APP_RELEASE_CHANNEL = "beta"
APP_BETA = True

DISTRIBUTION_NAME = "flatcam-plus"


def _locate_pyproject():
    """The manifest for this run, or ``None`` when the package is installed without one."""
    module_dir = Path(__file__).resolve().parent
    candidates = [module_dir.parent / "pyproject.toml"]
    bundle_dir = getattr(sys, "_MEIPASS", None)
    if bundle_dir:
        candidates.append(Path(bundle_dir) / "pyproject.toml")
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def _installed_distribution_version():
    """The version recorded when the distribution was built, or ``None`` when nothing is installed."""
    try:
        return metadata.version(DISTRIBUTION_NAME)
    except metadata.PackageNotFoundError:
        return None


def _read_app_version():
    manifest = _locate_pyproject()
    if manifest is not None:
        with manifest.open("rb") as handle:
            return tomllib.load(handle)["project"]["version"]

    installed = _installed_distribution_version()
    if installed:
        return installed

    raise RuntimeError(
        "the version cannot be read: no pyproject.toml beside the package and no installed "
        "{} distribution. Reinstall the project (``uv sync``) or ship the manifest.".format(
            DISTRIBUTION_NAME
        )
    )


APP_VERSION = _read_app_version()

__version__ = APP_VERSION
