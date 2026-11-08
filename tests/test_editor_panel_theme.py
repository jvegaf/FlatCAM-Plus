"""The four object editors must carry the same panel chrome as every object editor.

``FlatCAMObj.build_ui`` styles the properties panel root with
``apply_modern_panel_style``. The GCode, Geometry, Excellon and Gerber editor UIs build
their own widget tree and attach it to that same panel, so without the same call they
fall back to the application stylesheet's flat background: no ``surface`` token, no
rounded panel border, no panel typography, and ``FCFrame`` children keep the QSettings
palette instead of the theme tokens.

The paint assertion is the one that catches the real regression: the property alone says
the panel was told it is a panel root, while only painting proves the tokens reached the
widget. The sampled point sits in the root's own layout margin so no child paints it.
"""

import importlib

import pytest

from flatcam_plus.appGUI import PanelStyles

DARK_SURFACE = "#262626"

# module, class, attribute holding the root widget attached to the properties panel
EDITOR_UIS = [
    ("flatcam_plus.appEditors.appGCodeEditor", "AppGCodeEditorUI", "edit_widget"),
    ("flatcam_plus.appEditors.appGeoEditor", "AppGeoEditorUI", "geo_edit_widget"),
    ("flatcam_plus.appEditors.appExcEditor", "AppExcEditorUI", "exc_edit_widget"),
    ("flatcam_plus.appEditors.appGerberEditor", "AppGerberEditorUI", "grb_edit_widget"),
]


@pytest.fixture
def dark_theme(fc_app):
    """Apply the dark theme, then restore it: ``fc_app`` is session-scoped."""
    saved = {key: fc_app.options.get(key) for key in ("global_theme", "global_appearance")}
    fc_app.options["global_theme"] = "dark"
    fc_app.options["global_appearance"] = "dark"
    try:
        yield fc_app
    finally:
        for key, value in saved.items():
            if value is None:
                fc_app.options.pop(key, None)
            else:
                fc_app.options[key] = value


def _painted_color(widget, x, y):
    """Colour of one pixel after Qt has parsed and painted the widget's stylesheet."""
    widget.resize(300, 600)
    widget.show()
    widget.repaint()
    image = widget.grab().toImage()
    assert not image.isNull(), "widget produced no image to sample"
    return image.pixelColor(x, y)


@pytest.mark.parametrize(
    "module_name,class_name,root_attr", EDITOR_UIS, ids=[entry[1] for entry in EDITOR_UIS]
)
def test_editor_root_carries_the_panel_chrome(dark_theme, module_name, class_name, root_attr):
    app = dark_theme
    colors = PanelStyles.modern_panel_colors(app)
    assert colors["surface"] == DARK_SURFACE, "the dark theme guard did not take effect"

    editor_ui = getattr(importlib.import_module(module_name), class_name)(app)
    root = getattr(editor_ui, root_attr)

    painted = _painted_color(root, 5, 5)
    assert painted.name() == colors["surface"], (
        "%s attaches its widget tree to the properties panel without "
        "apply_modern_panel_style(root, app): the root painted %s instead of the panel "
        "surface token %s" % (class_name, painted.name(), colors["surface"])
    )

    assert root.property("modernPanelRoot") is True, (
        "%s root does not expose modernPanelRoot, so the panel stylesheet cannot select it"
        % class_name
    )
