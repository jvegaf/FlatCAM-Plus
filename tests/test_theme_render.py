"""Both themes must actually paint, and a new process must actually load the chosen one.

``test_theme_tokens`` pins the stylesheet *text*; this file pins its *effect*. Two
layers, because they catch different regressions:

* A fast layer that hands the generated stylesheets to real Qt widgets and samples
  the painted pixels. Breaking a token, a selector or a rule leaves the strings
  plausible but stops the colour reaching the screen; only painting catches that.
* One slow layer that boots the application in a subprocess twice. A persisted theme
  is what the next launch loads, and that wiring lives in ``appMain`` before any
  widget exists, so it cannot be exercised in the already-booted session fixture.
"""

import glob
import json
import os
import subprocess
import sys

import pytest
from PyQt6 import QtCore, QtGui, QtWidgets

from flatcam_plus.appGUI import PanelStyles

THEMES = ["light", "dark"]


class _AppStub:
    """Only what the panel-dict helpers read: the theme option."""

    def __init__(self, theme):
        self.options = {"global_theme": theme}


def _painted_color(widget, x, y):
    """Colour of one pixel after Qt has parsed and painted the widget's stylesheet."""
    widget.resize(160, 120)
    widget.show()
    widget.repaint()
    image = widget.grab().toImage()
    assert not image.isNull(), "widget produced no image to sample"
    return image.pixelColor(x, y)


@pytest.mark.parametrize("theme", THEMES)
def test_panel_root_paints_the_surface_token(fc_app, theme):
    """The panel background must be the theme's ``surface``, not a default grey."""
    colors = PanelStyles.modern_panel_colors(_AppStub(theme))

    root = QtWidgets.QWidget()
    root.setObjectName("modernPanelRoot")
    root.setProperty("modernPanelRoot", True)
    root.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)
    root.setStyleSheet(PanelStyles.modern_panel_stylesheet(_AppStub(theme)))

    painted = _painted_color(root, 80, 60)

    assert painted.name() == colors["surface"], (
        "%s panel root painted %s, expected surface %s"
        % (theme, painted.name(), colors["surface"])
    )


@pytest.mark.parametrize("theme", THEMES)
def test_project_tree_paints_its_background_and_keeps_the_header(fc_app, theme):
    """The tree must paint ``surface`` and keep a visible header for the Kind column."""
    colors = PanelStyles.modern_panel_colors(_AppStub(theme))

    tree = QtWidgets.QTreeView()
    tree.setHeaderHidden(False)
    tree.setStyleSheet(PanelStyles.modern_project_view_stylesheet(_AppStub(theme)))

    painted = _painted_color(tree, 80, 100)

    assert painted.name() == colors["surface"], (
        "%s tree painted %s, expected surface %s"
        % (theme, painted.name(), colors["surface"])
    )
    assert tree.isHeaderHidden() is False


def _probe(home):
    """Boot the real application in a fresh process and return what it loaded."""
    completed = subprocess.run(
        [sys.executable, os.path.join(os.path.dirname(__file__), "theme_probe.py"), home],
        capture_output=True,
        text=True,
        timeout=600,
    )
    for line in completed.stdout.splitlines():
        if line.startswith("PROBE "):
            return json.loads(line[len("PROBE "):])
    raise AssertionError(
        "probe produced no result. stdout=%r stderr=%r"
        % (completed.stdout[-2000:], completed.stderr[-2000:])
    )


def _profile_file(home):
    matches = sorted(glob.glob(os.path.join(home, ".FlatCAM", "current_defaults_*.FlatConfig")))
    assert matches, "the first boot did not write a preferences file"
    return matches[0]


def test_a_new_process_boots_with_the_persisted_theme(tmp_path):
    """The bug class this pins: you choose dark, and the next launch comes back light.

    The first boot establishes a profile (and consumes the first-run reset), the
    preference is then changed on disk the way a saved choice would leave it, and a
    second, genuinely separate process must load dark.
    """
    home = str(tmp_path / "home")
    os.makedirs(home)

    first = _probe(home)
    assert first["theme"] == "light", "a fresh profile should start light"

    path = _profile_file(home)
    with open(path, encoding="utf-8") as handle:
        stored = json.load(handle)
    stored["global_theme"] = "dark"
    stored["global_appearance"] = "dark"
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(stored, handle)

    second = _probe(home)

    assert second["theme"] == "dark", "the persisted choice did not survive the restart"
    assert second["dark_resources"] is True, "dark theme did not switch the resource set"
    assert second["vendor_sheet_chars"] > 0, "no vendor stylesheet was applied"

    # The same boot proves the tree change reached the running window, not just the model.
    assert second["tree_header_hidden"] is False
    assert second["tree_columns"] == 2
    assert second["kind_header"], "the Kind column has no header label"
