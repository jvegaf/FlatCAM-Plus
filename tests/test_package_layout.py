"""The migrated modules live inside the package.

T4.2b moved the modules that only ``appMain`` and the preferences manager imported by name and
deleted the pool module nothing referenced; T4.3 moved ``camlib``, the geometry and G-code core;
T4.4 moved ``appTool``, the base class of every tool and editor plugin, and T4.4b moved
``appPreProcessor``, whose contract the path-loaded preprocessors import. This test pins those
facts so a later phase cannot leave a half-migrated tree behind.
"""

import importlib
import os

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
)
DELETED_MODULES = ("appPool",)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.mark.parametrize("name", PACKAGE_MODULES)
def test_module_imports_from_the_package(name):
    module = importlib.import_module("flatcam_plus." + name)
    assert module.__name__ == "flatcam_plus." + name


@pytest.mark.parametrize("name", PACKAGE_MODULES + DELETED_MODULES)
def test_no_root_copy_is_left_behind(name):
    assert not os.path.exists(os.path.join(REPO_ROOT, name + ".py"))


@pytest.mark.parametrize("name", PACKAGE_MODULES)
def test_no_module_outside_the_package_imports_the_root_name(name):
    offender = "from {} import".format(name)
    for directory, _, filenames in os.walk(REPO_ROOT):
        if os.path.join(REPO_ROOT, ".git") in directory or ".venv" in directory:
            continue
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            path = os.path.join(directory, filename)
            with open(path, encoding="utf-8") as handle:
                if offender in handle.read():
                    pytest.fail("{} still imports the root module {}".format(path, name))


def test_the_pre_t44b_module_name_still_resolves():
    moved = importlib.import_module("flatcam_plus.appPreProcessor")
    assert importlib.import_module("appPreProcessor") is moved


def test_the_pre_t45_module_name_still_resolves():
    moved = importlib.import_module("flatcam_plus.appTranslation")
    assert importlib.import_module("appTranslation") is moved
