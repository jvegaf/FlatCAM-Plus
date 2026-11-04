"""Paths the application resolves for itself must not depend on the process CWD.

``App.__init__`` chdirs to the directory that holds ``appMain.py``, so every later lookup of
``assets/`` or ``preprocessors/`` silently depends on that directory being where the modules
live. T4 moves those modules, so the dependency has to go first.
"""

import os


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
