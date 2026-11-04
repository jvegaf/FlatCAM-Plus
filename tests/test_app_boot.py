"""Headless startup smoke test.

Boots the real application the way ``flatcam.py`` does, without a display: a broken import,
an unregistered tool plugin, a preprocessor that fails to load or a main window that never
appears all surface here.
"""

import os

from PyQt6.QtCore import QSettings

from appGUI.MainGUI import MainGUI


def test_boots_headless_into_a_main_window(fc_app):
    assert isinstance(fc_app.ui, MainGUI)
    assert fc_app.ui.isVisible()


def test_keeps_its_state_inside_the_isolated_home(fc_app, isolated_home):
    settings_file = QSettings("Open Source", "FlatCAM_Plus").fileName()
    assert settings_file.startswith(isolated_home)
    assert os.path.isfile(settings_file)
    assert fc_app.data_path.startswith(isolated_home)


def test_installs_the_tool_plugins(fc_app):
    assert len(fc_app.app_plugins) >= 20
    for tool in (fc_app.cutout_tool, fc_app.isolation_tool, fc_app.drilling_tool, fc_app.milling_tool):
        assert tool in fc_app.app_plugins


def test_loads_the_gcode_preprocessors(fc_app):
    assert len(fc_app.preprocessors) >= 20
    assert "default" in fc_app.preprocessors
    assert "GRBL_11" in fc_app.preprocessors
