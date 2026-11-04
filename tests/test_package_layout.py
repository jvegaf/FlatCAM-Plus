"""The migrated modules and packages live inside the package.

T4.2b moved the modules that only ``appMain`` and the preferences manager imported by name and
deleted the pool module nothing referenced; T4.3 moved ``camlib``, the geometry and G-code core;
T4.4 moved ``appTool``, the base class of every tool and editor plugin, T4.4b moved
``appPreProcessor``, whose contract the path-loaded preprocessors import, T4.6 moved
``appMain``, the application controller ``flatcam.py`` instantiates, and T4.7 moved the two
vendored dependency packages, ``descartes`` and ``libs``. T1 of the package consolidation
started the application packages moving, beginning with ``appCommon``, the shared helpers,
updater and recent-project loader the controller, the GUI, the tools and ``flatcam.py`` import.
This test pins those facts so a later phase cannot leave a half-migrated tree behind.
"""

import importlib.util
import os
import re

import pytest

PACKAGE_MODULES = (
    "defaults",
    "appDatabase",
    "appProcess",
    "appWorker",
    "appWorkerStack",
    "camlib",
    "appTool",
    "appPreProcessor",
    "appTranslation",
    "appMain",
)
DELETED_MODULES = ("appPool",)

# Application packages that used to be top-level importables and are now subpackages of
# ``flatcam_plus``. ``appCommon`` is the first of the eight; each later slice adds its own entry
# here so a root copy or a root-name importer cannot come back.
APP_PACKAGES = ("appCommon",)
APP_MODULES = (
    "appCommon",
    "appCommon.AutoUpdater",
    "appCommon.Common",
    "appCommon.RegisterFileKeywords",
    "appCommon.recent_projects",
)

# Directories that used to be top-level importables and are now subpackages. They are vendored
# code, so a real PyPI ``descartes`` (or any other ``libs``) silently wins over them once the
# bare name resolves anywhere else on ``sys.path``. ``libs`` also shipped without an
# ``__init__.py``, so it was only importable as a namespace package.
VENDORED_PACKAGES = ("descartes", "libs")
VENDORED_MODULES = ("descartes", "descartes.patch", "libs", "libs.qdarktheme")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def root_name_import(name):
    """Match every way a module can import a root-level module called ``name``.

    Both forms matter: ``from appTranslation import x`` and the bare ``import appTranslation as
    y`` that 168 of the 172 pre-T4.5 sites used. The dotted suffix covers the vendored
    subpackages (``import libs.qdarktheme.themes.dark.stylesheet as qdarksheet``,
    ``from descartes.patch import PolygonPatch``). The migrated forms
    (``from flatcam_plus import appTranslation``, ``from . import camlib``) and a
    ``sys.modules.setdefault('appTranslation', ...)`` compatibility line must not match.
    """
    escaped = re.escape(name)
    return re.compile(
        r"^\s*(?:from\s+{0}(?:\.[\w.]*)?\s+import\b"
        r"|import\s+{0}(?:\.[\w.]*)?(?:\s+as\s+\w+)?\s*(?:,|$|\s*#))".format(escaped),
        re.MULTILINE,
    )


def test_the_root_name_guard_matches_both_import_forms():
    offender = root_name_import("appTranslation")

    assert offender.search("import appTranslation as fcTranslate\n")
    assert offender.search("import appTranslation\n")
    assert offender.search("from appTranslation import restart_program\n")
    assert not offender.search("from flatcam_plus import appTranslation as fcTranslate\n")
    assert not offender.search("from . import appTranslation as fcTranslate\n")
    assert not offender.search("sys.modules.setdefault('appTranslation', sys.modules[__name__])\n")


def test_the_root_name_guard_matches_the_dotted_subpackage_forms():
    offender = root_name_import("libs")

    assert offender.search("import libs.qdarktheme\n")
    assert offender.search("import libs.qdarktheme.themes.dark.stylesheet as qdarksheet\n")
    assert offender.search("from libs.qdarktheme.main import load_stylesheet\n")
    assert not offender.search("import flatcam_plus.libs.qdarktheme\n")
    assert not offender.search("from flatcam_plus.libs.qdarktheme import load_stylesheet\n")


@pytest.mark.parametrize("name", PACKAGE_MODULES)
def test_module_imports_from_the_package(name):
    module = importlib.import_module("flatcam_plus." + name)
    assert module.__name__ == "flatcam_plus." + name


@pytest.mark.parametrize("name", PACKAGE_MODULES + DELETED_MODULES)
def test_no_root_copy_is_left_behind(name):
    assert not os.path.exists(os.path.join(REPO_ROOT, name + ".py"))


@pytest.mark.parametrize("name", APP_MODULES)
def test_the_app_modules_import_from_the_package(name):
    module = importlib.import_module("flatcam_plus." + name)
    assert module.__name__ == "flatcam_plus." + name


@pytest.mark.parametrize("name", APP_PACKAGES)
def test_no_root_copy_of_the_app_package_is_left_behind(name):
    assert not os.path.exists(os.path.join(REPO_ROOT, name))


@pytest.mark.parametrize("name", VENDORED_MODULES)
def test_the_vendored_modules_import_from_the_package(name):
    module = importlib.import_module("flatcam_plus." + name)
    assert module.__name__ == "flatcam_plus." + name


@pytest.mark.parametrize("name", VENDORED_PACKAGES)
def test_no_root_copy_of_the_vendored_package_is_left_behind(name):
    assert not os.path.exists(os.path.join(REPO_ROOT, name))


@pytest.mark.parametrize("name", VENDORED_PACKAGES)
def test_the_bare_vendored_name_does_not_resolve_to_this_repository(name):
    """The shadowing risk: nothing in this tree may be reached through the bare name."""
    try:
        spec = importlib.util.find_spec(name)
    except ModuleNotFoundError:
        spec = None
    origin = getattr(spec, "origin", None)
    if origin:
        assert not os.path.realpath(origin).startswith(os.path.realpath(REPO_ROOT) + os.sep)


def test_the_vendored_theme_root_resolves_inside_the_package():
    """qdarktheme finds its own SVG resources from its module location, not from a fixed path."""
    from flatcam_plus.libs.qdarktheme.util import get_qdarktheme_root_path

    expected = os.path.realpath(os.path.join(REPO_ROOT, "flatcam_plus", "libs", "qdarktheme"))
    assert os.path.realpath(get_qdarktheme_root_path()) == expected


@pytest.mark.parametrize("name", PACKAGE_MODULES + APP_PACKAGES + VENDORED_PACKAGES)
def test_no_module_outside_the_package_imports_the_root_name(name):
    offender = root_name_import(name)
    for directory, _, filenames in os.walk(REPO_ROOT):
        if os.path.join(REPO_ROOT, ".git") in directory or ".venv" in directory:
            continue
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            path = os.path.join(directory, filename)
            with open(path, encoding="utf-8") as handle:
                if offender.search(handle.read()):
                    pytest.fail("{} still imports the root module {}".format(path, name))


def test_the_pre_t44b_module_name_still_resolves():
    moved = importlib.import_module("flatcam_plus.appPreProcessor")
    assert importlib.import_module("appPreProcessor") is moved


def test_the_pre_t45_module_name_still_resolves():
    moved = importlib.import_module("flatcam_plus.appTranslation")
    assert importlib.import_module("appTranslation") is moved
