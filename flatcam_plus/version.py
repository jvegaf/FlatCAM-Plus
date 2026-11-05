"""Version metadata for FlatCAM Plus.

``pyproject.toml`` is the single source of truth: this module reads ``[project] version`` from it
instead of carrying a copy of the number. The build scripts ship ``pyproject.toml`` inside the
bundle for the same reason, so a frozen build reports the version it was built from.
"""

import sys
import tomllib
from pathlib import Path

APP_NAME = "FlatCAM Plus"
APP_VERSION_DATE = "2026.11.05"
APP_RELEASE_CHANNEL = "beta"
APP_BETA = True


def _locate_pyproject():
    """The checkout's file when running from source, the bundled copy when frozen."""
    module_dir = Path(__file__).resolve().parent
    candidates = [module_dir.parent / "pyproject.toml"]
    bundle_dir = getattr(sys, "_MEIPASS", None)
    if bundle_dir:
        candidates.append(Path(bundle_dir) / "pyproject.toml")
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise RuntimeError(
        "pyproject.toml is missing: the build did not ship it, so the version cannot be read from "
        "{}".format(", ".join(str(candidate) for candidate in candidates))
    )


def _read_app_version():
    with _locate_pyproject().open("rb") as handle:
        return tomllib.load(handle)["project"]["version"]


APP_VERSION = _read_app_version()

__version__ = APP_VERSION
