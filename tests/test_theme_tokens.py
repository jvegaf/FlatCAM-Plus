"""Generated-stylesheet assertions for the two-theme main window (S3, S5, S6).

The panel stylesheets are plain strings built from ``modern_panel_colors()`` and the
theme-branching helpers in ``flatcam_plus.appGUI.PanelStyles``, so every rule below is
checkable without a display server or a running application.
"""

import pytest

from flatcam_plus.appGUI import PanelStyles

LIGHT = "light"
DARK = "dark"

#: Task T3 / design/system.md "Proposed additions": small muted text that must pass AA.
HINT_STRONG = {LIGHT: "#5f6b7e", DARK: "#a8a8a8"}
#: One accent per theme. The light one is the vendor sheet's call-to-action blue, the
#: dark one is the panel dict's existing orange.
ACCENT = {LIGHT: "#0081db", DARK: "#ff6900"}
#: The light focus tint that measured 1.21:1 against the border it replaced.
DEFECTIVE_LIGHT_FOCUS = "#b9d1ff"


class StubApp:
    """Minimal stand-in for the application object the style helpers read."""

    def __init__(self, theme):
        self.options = {"global_theme": theme}
        self.resource_location = ""


@pytest.fixture(params=[LIGHT, DARK], ids=[LIGHT, DARK])
def theme(request):
    return request.param


@pytest.fixture
def app(theme):
    return StubApp(theme)


def block(stylesheet, selector):
    """Return the declarations of the rule that starts at ``selector``."""
    start = stylesheet.index(selector)
    body_start = stylesheet.index("{", start) + 1
    body_end = stylesheet.index("}", body_start)
    return stylesheet[body_start:body_end]


def test_panel_colors_expose_hint_strong(theme):
    colors = PanelStyles.modern_panel_colors(StubApp(theme))
    assert colors["hint_strong"] == HINT_STRONG[theme]
    # ``hint`` stays available for large or decorative use.
    assert colors["hint"] in ("#6f7b8e", "#999999")


def test_tab_labels_use_hint_strong(app):
    value = HINT_STRONG[app.options["global_theme"]]
    declarations = f"color: {value};"

    panel_sheet = PanelStyles.modern_panel_stylesheet(app)
    assert declarations in block(panel_sheet, "QTabBar::tab {")

    preferences_sheet = PanelStyles.modern_preferences_tabbar_stylesheet(app)
    assert declarations in block(preferences_sheet, "QTabBar::tab {")

    workspace_sheet = PanelStyles.modern_workspace_tabbar_stylesheet(app)
    assert declarations in block(workspace_sheet, "QTabBar::tab {")


def test_accent_helper_returns_one_accent_per_theme(theme):
    assert PanelStyles.modern_accent_colors(StubApp(theme))["accent"] == ACCENT[theme]


def test_input_focus_rule_is_perceivable_in_both_themes(app):
    theme = app.options["global_theme"]
    sheet = PanelStyles.modern_panel_stylesheet(app)

    input_focus = block(sheet, "QLineEdit:focus")
    assert ACCENT[theme] in input_focus
    assert "border: 2px solid" in input_focus
    # The 2px border is offset by 1px less padding, so focus shifts no layout.
    assert "padding: 3px 6px;" in input_focus

    combo_focus = block(sheet, "QComboBox:focus")
    assert ACCENT[theme] in combo_focus
    assert "padding: 3px 27px 3px 6px;" in combo_focus

    button_focus = block(sheet, "QPushButton:focus")
    assert ACCENT[theme] in button_focus
    assert "padding: 4px 6px;" in button_focus


def test_light_focus_no_longer_uses_the_pale_border_tint():
    sheet = PanelStyles.modern_panel_stylesheet(StubApp(LIGHT))
    assert ACCENT[LIGHT] in block(sheet, "QLineEdit:focus")
    assert DEFECTIVE_LIGHT_FOCUS not in block(sheet, "QLineEdit:focus")
    assert f"border: 2px solid {DEFECTIVE_LIGHT_FOCUS}" not in sheet


def test_checked_indicators_use_the_theme_accent(app):
    theme = app.options["global_theme"]
    sheet = PanelStyles.modern_panel_stylesheet(app)

    checked = block(sheet, "QCheckBox::indicator:checked")
    assert f"border-color: {ACCENT[theme]};" in checked
    assert f"border-color: {DEFECTIVE_LIGHT_FOCUS};" not in sheet


def test_project_tree_selected_row_has_a_non_colour_cue(app):
    theme = app.options["global_theme"]
    sheet = PanelStyles.modern_project_view_stylesheet(app)

    selected = block(sheet, "QTreeView::item:selected")
    hover = block(sheet, "QTreeView::item:hover")

    assert "font-weight: 600;" in selected
    assert f"border-left: 3px solid {ACCENT[theme]};" in selected
    # The border is compensated in the padding so the row text does not jump.
    assert "padding: 5px 5px 5px 2px;" in selected
    assert "font-weight" not in hover
    assert "border-left" not in hover


def test_project_tree_header_is_styled_and_kind_header_is_secondary(app):
    theme = app.options["global_theme"]
    sheet = PanelStyles.modern_project_view_stylesheet(app)

    assert "QHeaderView::section {" in sheet
    header = block(sheet, "QHeaderView::section {")
    assert "font-weight: 600;" in header
    assert "color:" in header

    kind_header = block(sheet, "QHeaderView::section:last")
    assert f"color: {HINT_STRONG[theme]};" in kind_header


def test_density_tokens_match_the_token_source(app):
    panel_sheet = PanelStyles.modern_panel_stylesheet(app)
    project_sheet = PanelStyles.modern_project_view_stylesheet(app)

    item = block(project_sheet, "QTreeView::item {")
    assert "min-height: 24px;" in item
    assert "border-radius: 5px;" in item

    root = block(panel_sheet, 'QWidget[modernPanelRoot="true"]')
    assert "border-radius: 8px;" in root

    frame = block(PanelStyles.modern_panel_frame_stylesheet(app), "FCFrame")
    assert "border: 1px solid" in frame
    assert "border-radius: 8px;" in frame

    for sheet in (panel_sheet, project_sheet):
        assert "box-shadow" not in sheet
