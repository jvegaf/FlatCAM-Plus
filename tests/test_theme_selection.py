"""The UI theme is a user choice: light and dark are both selectable and both persist.

Covers S1 of ``odd/tasks/two-theme-main-window.md``: the appearance preference offers dark, and no
preferences path silently rewrites an explicit choice back to light. The choice survives a restart
through two observables, because the test session boots the application only once: the preferences
file the next start loads (``current_defaults_<version>.FlatConfig``) and the ``theme`` key the
application writes into ``QSettings`` and reads back when it builds its widgets.
"""

import json
import os

from PyQt6.QtCore import QSettings

SETTINGS_ORGANIZATION = "Open Source"
SETTINGS_APPLICATION = "FlatCAM_Plus"

THEME_OPTION = "global_theme"
APPEARANCE_OPTION = "global_appearance"


def _settings():
    return QSettings(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)


def _persisted_defaults_path(fc_app):
    return os.path.join(
        fc_app.preferencesUiManager.data_path,
        "current_defaults_%s.FlatConfig" % fc_app.defaults.version,
    )


def _persisted_default(fc_app, option):
    with open(_persisted_defaults_path(fc_app), encoding="utf-8") as handle:
        return json.load(handle).get(option)


def _set_theme(fc_app, theme):
    """Put the application in the state a launch with ``theme`` leaves behind."""
    settings = _settings()
    settings.setValue("theme", theme)
    settings.sync()

    for option in (THEME_OPTION, APPEARANCE_OPTION):
        fc_app.defaults[option] = theme
        fc_app.options[option] = theme


def test_save_defaults_keeps_dark_theme(fc_app):
    """Saving preferences must not turn an explicit dark choice back into light."""
    previous_settings = _settings().value("theme", type=str)

    _set_theme(fc_app, "dark")
    try:
        fc_app.preferencesUiManager.save_defaults(silent=True)

        assert _settings().value("theme", type=str) == "dark"
        assert _persisted_default(fc_app, THEME_OPTION) == "dark"
    finally:
        settings = _settings()
        settings.setValue("theme", previous_settings)
        settings.sync()


def test_save_defaults_keeps_light_theme(fc_app):
    """The light theme keeps working exactly as before."""
    previous_settings = _settings().value("theme", type=str)

    _set_theme(fc_app, "light")
    try:
        fc_app.preferencesUiManager.save_defaults(silent=True)

        assert _settings().value("theme", type=str) == "light"
        assert _persisted_default(fc_app, THEME_OPTION) == "light"
    finally:
        settings = _settings()
        settings.setValue("theme", previous_settings)
        settings.sync()


def test_applying_dark_then_shutting_down_keeps_dark(fc_app, monkeypatch):
    """The path a user actually takes: pick Dark, press Apply, then quit.

    ``App.quit_application`` (appMain.py:3787) copies ``options`` over ``defaults`` before
    saving. A theme the user just applied must survive that copy: applying a preference
    that reaches ``defaults`` but not ``options`` would be reverted at shutdown, which
    looks exactly like "I chose dark and nothing changed".
    """
    from flatcam_plus.appGUI.preferences import PreferencesUIManager as PUM

    class _AutoConfirm:
        """Stands in for the modal restart dialog so Apply can run unattended."""

        def __init__(self, *args, **kwargs):
            self._first = None

        def addButton(self, *args, **kwargs):
            token = object()
            if self._first is None:
                self._first = token
            return token

        def exec(self):
            return 0

        def clickedButton(self):
            return self._first

        def __getattr__(self, name):
            return lambda *args, **kwargs: None

    previous_settings = _settings().value("theme", type=str)
    radio = fc_app.ui.general_pref_form.general_gui_group.appearance_radio
    original = radio.get_value()

    monkeypatch.setattr(PUM, "FCMessageBox", _AutoConfirm)
    monkeypatch.setattr(fc_app, "on_app_restart", lambda *args, **kwargs: None, raising=False)

    try:
        radio.set_value("dark")
        fc_app.preferencesUiManager.on_save_button(save_to_file=True)

        # Then the shutdown path that follows, in the shape quit_application uses.
        fc_app.defaults.update(fc_app.options)
        fc_app.preferencesUiManager.save_defaults(silent=True)

        # What the next launch loads, which is what decides the theme it renders.
        assert fc_app.options[THEME_OPTION] == "dark"
        assert _persisted_default(fc_app, THEME_OPTION) == "dark"
        # ``QSettings`` is only refreshed at startup from ``options`` (appMain:621-622), so it
        # legitimately still holds the old value here; the option above is what it will be
        # written from.
    finally:
        radio.set_value(original)
        for option in (THEME_OPTION, APPEARANCE_OPTION):
            fc_app.defaults[option] = original
            fc_app.options[option] = original
        settings = _settings()
        settings.setValue("theme", previous_settings)
        settings.sync()


def test_appearance_control_offers_both_themes(fc_app):
    """The appearance radio is visible, offers dark, and feeds the theme option the app reads."""
    radio = fc_app.ui.general_pref_form.general_gui_group.appearance_radio
    original = radio.get_value()

    assert sorted(radio.values()) == ["dark", "light"]
    assert radio.isHidden() is False

    try:
        radio.set_value("dark")
        assert radio.get_value() == "dark"

        fc_app.preferencesUiManager.defaults_read_form()
        assert fc_app.defaults[THEME_OPTION] == "dark"
    finally:
        radio.set_value(original)
        for option in (THEME_OPTION, APPEARANCE_OPTION):
            fc_app.defaults[option] = original
            fc_app.options[option] = original
