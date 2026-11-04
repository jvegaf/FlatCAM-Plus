"""The migrated modules live inside the package.

T4.2b moved the modules that only ``appMain`` and the preferences manager imported by name and
deleted the pool module nothing referenced; T4.3 moved ``camlib``, the geometry and G-code core;
T4.4 moved ``appTool``, the base class of every tool and editor plugin, T4.4b moved
``appPreProcessor``, whose contract the path-loaded preprocessors import, and T4.6 moved
``appMain``, the application controller ``flatcam.py`` instantiates. This test pins those facts
so a later phase cannot leave a half-migrated tree behind.
"""

import importlib
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

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def root_name_import(name):
    """Match every way a module can import a root-level module called ``name``.

    Both forms matter: ``from appTranslation import x`` and the bare ``import appTranslation as
    y`` that 168 of the 172 pre-T4.5 sites used. The migrated forms
    (``from flatcam_plus import appTranslation``, ``from . import camlib``) and a
    ``sys.modules.setdefault('appTranslation', ...)`` compatibility line must not match.
    """
    escaped = re.escape(name)
    return re.compile(
        r"^\s*(?:from\s+{0}\s+import\b|import\s+{0}(?:\s+as\s+\w+)?\s*(?:,|$|\s*#))".format(escaped),
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


@pytest.mark.parametrize("name", PACKAGE_MODULES)
def test_module_imports_from_the_package(name):
    module = importlib.import_module("flatcam_plus." + name)
    assert module.__name__ == "flatcam_plus." + name


@pytest.mark.parametrize("name", PACKAGE_MODULES + DELETED_MODULES)
def test_no_root_copy_is_left_behind(name):
    assert not os.path.exists(os.path.join(REPO_ROOT, name + ".py"))


@pytest.mark.parametrize("name", PACKAGE_MODULES)
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
