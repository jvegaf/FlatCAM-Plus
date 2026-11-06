"""Paths the application resolves for itself must not depend on the process CWD.

``App.__init__`` chdirs to ``app_home``, so every later lookup of ``assets/`` or
``preprocessors/`` silently depends on that directory being the one that holds them. The data
directories ship inside the package, so ``app_home`` is the package directory and it stays
correct in a checkout, in an installed wheel and in a frozen bundle.
"""

import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGE_DIR = os.path.join(REPO_ROOT, "flatcam_plus")


def test_resource_root_is_absolute(fc_app):
    assert os.path.isabs(fc_app.resource_location)


def test_preprocessor_root_is_absolute(fc_app):
    assert os.path.isabs(fc_app.preprocessorpaths)


def test_still_resolves_after_a_cwd_change(fc_app, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert os.path.isdir(fc_app.resource_location)
    assert os.path.isdir(fc_app.preprocessorpaths)


def test_resources_load_from_the_anchored_root(fc_app):
    assert os.path.isfile(os.path.join(fc_app.resource_location, "splash.png"))


def test_app_home_is_the_package_directory(fc_app):
    assert os.path.realpath(fc_app.app_home) == os.path.realpath(PACKAGE_DIR)


def test_the_repository_root_no_longer_holds_the_data_directories():
    for name in ("assets", "locale", "preprocessors", "config"):
        assert not os.path.exists(os.path.join(REPO_ROOT, name)), name


def test_app_home_holds_the_data_directories(fc_app):
    for name in ("assets", "locale", "preprocessors"):
        assert os.path.isdir(os.path.join(fc_app.app_home, name))


def test_the_process_cwd_is_the_anchored_root(fc_app):
    assert os.path.realpath(os.getcwd()) == os.path.realpath(fc_app.app_home)
