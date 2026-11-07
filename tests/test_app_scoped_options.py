"""A project file must not carry the options that belong to the application.

The theme is chosen in Preferences, applied once at start-up, and changing it needs a
restart: ``appMain`` sets the application stylesheet before any widget exists and never
re-applies it afterwards. ``appHandlers/appIO.open_project`` merges the project's stored
options into ``app.options``, and ``save_project`` stores that dict whole —
``global_theme`` included.

So a project saved under the light theme flipped the option back to ``light`` on open.
Every panel built afterwards is styled from ``PanelStyles.modern_panel_colors(app)``,
which reads that option, so the object properties panel came back white inside a dark
window: the chrome kept the theme it started with, and the panel followed the project.

``version`` rides the same dict. A project saved by 1.3.1 puts ``version: 1.3.1`` into
``app.options``; ``quit_application`` copies options into defaults, ``save_defaults``
writes them, and the next launch compares that value with the running build's version in
``defaults.py::__is_old_defaults``. A mismatch while the build is beta resets every
preference (``defaults.py:1049``), which is the "Found old preferences files" loop.

These tests use the real application fixture because the defect is a wiring defect: the
two halves (start-up styling and project loading) only meet in ``App``.
"""

import json

import pytest

from flatcam_plus.appGUI import PanelStyles
from flatcam_plus.version import APP_VERSION

DARK_SURFACE = "#262626"
LIGHT_SURFACE = "#ffffff"


@pytest.fixture
def app_theme_guard(fc_app):
    """Restore what a project load mutates; ``fc_app`` is session-scoped."""
    saved = {
        "global_theme": fc_app.options.get("global_theme"),
        "global_appearance": fc_app.options.get("global_appearance"),
        "project_filename": getattr(fc_app, "project_filename", None),
        "block_autosave": getattr(fc_app, "block_autosave", None),
        "global_save_compressed": fc_app.options.get("global_save_compressed"),
    }
    try:
        yield fc_app
    finally:
        for key, value in saved.items():
            if key.startswith("global_"):
                fc_app.options[key] = value
            else:
                setattr(fc_app, key, value)


def _write_project(path, theme):
    """The smallest project that exercises the options merge."""
    path.write_text(
        json.dumps(
            {
                "objs": [],
                "options": {"global_theme": theme, "global_appearance": theme},
                "version": APP_VERSION,
            }
        )
    )
    return path


def test_opening_a_project_does_not_change_the_theme(app_theme_guard, tmp_path):
    app = app_theme_guard
    app.options["global_theme"] = "dark"
    app.options["global_appearance"] = "dark"
    assert PanelStyles.modern_panel_colors(app)["surface"] == DARK_SURFACE

    project = _write_project(tmp_path / "light-project.FlatPrj", "light")
    # open_project() only queues parse_worker on the application's pool; the merge this
    # test is about happens in restore_project_handler, which the worker calls. Driving the
    # handler keeps the same code path and makes the assertion observable.
    proj_dict = json.loads(project.read_text())
    app.f_handlers.restore_project_handler(proj_dict, str(project), False, False, True, False)

    assert app.project_filename == str(project), "the project load did not reach the options merge"
    assert PanelStyles.modern_panel_colors(app)["surface"] == DARK_SURFACE, (
        "opening a project saved under the light theme changed the theme that styles "
        f"panels; global_theme={app.options.get('global_theme')!r}"
    )


def test_saving_a_project_does_not_persist_the_version(app_theme_guard, tmp_path):
    app = app_theme_guard
    app.options["global_save_compressed"] = False

    project = tmp_path / "saved.FlatPrj"
    app.f_handlers.save_project(str(project), silent=True)

    stored = json.loads(project.read_text())
    assert "version" not in stored["options"], (
        "the project stores the application version inside its options, so opening it "
        "after an upgrade makes the next launch treat the preferences as old"
    )


def test_saving_a_project_does_not_persist_the_theme(app_theme_guard, tmp_path):
    app = app_theme_guard
    app.options["global_theme"] = "dark"
    app.options["global_save_compressed"] = False

    project = tmp_path / "saved.FlatPrj"
    app.f_handlers.save_project(str(project), silent=True)

    stored = json.loads(project.read_text())
    assert "global_theme" not in stored["options"], (
        "the project file carries the application theme, so opening it elsewhere can "
        "restyle that session"
    )
    assert "global_appearance" not in stored["options"]
