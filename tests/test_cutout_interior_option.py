"""The Cutout auto-interior option and the offset branch it switches.

``tools_cutout_auto_interior`` defaults to on, because the contour classification it guards is
already unconditional in the Cutout tool: defaulting to off would silently send every user's
internal slots to the wrong side of the material. It is an escape hatch, and turning it off
must restore exactly what the tool did before the classification existed — every contour takes
the exterior path, nothing is classified and nothing is warned about.

These tests drive the real plugin object built by the application fixture, through the two
production methods the freeform Cutout job calls: the classification gate and the per-contour
offset. The job itself runs inside a Qt worker behind ``app.proc_container`` and a source
object, so it is not reachable from a test; the two methods are what it calls, verbatim.
"""

import math

import pytest
from shapely import LineString, MultiLineString, Polygon

import flatcam_plus.appPlugins.ToolCutOut as tool_cutout
from flatcam_plus import defaults as app_defaults
from flatcam_plus.appDatabase import ToolsDB2
from flatcam_plus.appGUI.GUIElements import FCCheckBox

OPTION = "tools_cutout_auto_interior"

MARGIN = 0.1
CUT_DIA = 2.0


def _band(coords, width=0.254):
    """A Gerber profile path: the drawn line buffered with the aperture width / 2."""
    return LineString(coords).buffer(width / 2)


def _outline():
    return _band([(0, 0), (100, 0), (100, 60), (0, 60), (0, 0)])


def _circle_band(cx, cy, radius, width=0.254, segments=64):
    """A circular Gerber profile path, buffered with the aperture width / 2."""
    coords = []
    for i in range(segments + 1):
        angle = 2 * math.pi * i / segments
        coords.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return _band(coords, width)


def _slot():
    return _band([(20, 20), (40, 20), (40, 40), (20, 40), (20, 20)])


class WarningRecorder:
    def __init__(self):
        self.messages = []

    def warning(self, message, *args, **kwargs):
        self.messages.append(message % args if args else message)

    def debug(self, message, *args, **kwargs):
        self.messages.append(message % args if args else message)


@pytest.fixture
def cutout(fc_app, monkeypatch):
    """The Cutout plugin the application built, reset to its shipped defaults."""
    tool = fc_app.cutout_tool
    tool.set_tool_ui()
    saved = fc_app.options[OPTION]
    yield tool
    fc_app.options[OPTION] = saved


@pytest.fixture
def logged(cutout, monkeypatch):
    """Capture every warning and debug line the plugin's logger receives."""
    recorder = WarningRecorder()
    monkeypatch.setattr(cutout.app.log, "warning", recorder.warning)
    monkeypatch.setattr(cutout.app.log, "debug", recorder.debug)
    return recorder


# ============================================================================
# S4 — the option exists, defaults to on, and the tool shows it
# ============================================================================

def test_the_option_is_registered_in_the_cutout_family_and_defaults_to_on():
    factory = app_defaults.AppDefaults.factory_defaults

    assert OPTION in factory
    assert factory[OPTION] is True
    # The family it joins: the other Cutout options are declared around it.
    for neighbour in ("tools_cutout_gap_type", "tools_cutout_tooldia", "tools_cutout_margin"):
        assert neighbour in factory


def test_the_cutout_tool_offers_the_option_with_the_shipped_default(cutout):
    assert cutout.ui.auto_interior_cb.get_value() is True

    cutout.app.options[OPTION] = False
    cutout.set_tool_ui()
    try:
        assert cutout.ui.auto_interior_cb.get_value() is False
    finally:
        cutout.app.options[OPTION] = True
        cutout.set_tool_ui()


def test_a_classifying_run_reports_how_many_holes_it_found(cutout, logged):
    cutout.ui.auto_interior_cb.set_value(True)

    interior = cutout._auto_interior_indices([_outline(), _slot()])

    assert interior == {1}
    reports = [message for message in logged.messages if "classified" in message]
    assert len(reports) == 1
    assert "1" in reports[0]
    assert "holes" in reports[0]


# ============================================================================
# S5 — off means exactly the pre-classification behaviour
# ============================================================================

def test_with_the_option_off_the_contours_are_never_classified(cutout, monkeypatch):
    cutout.ui.auto_interior_cb.set_value(False)

    calls = []
    monkeypatch.setattr(
        tool_cutout.CutOut,
        "_classify_contours",
        staticmethod(lambda *args, **kwargs: calls.append(args) or {1}),
    )

    assert cutout._auto_interior_indices([_outline(), _slot()]) == set()
    assert calls == []


def test_with_the_option_off_every_contour_takes_the_exterior_path(cutout, logged):
    cutout.ui.auto_interior_cb.set_value(False)
    object_geo = [_outline(), _slot()]

    interior_indices = cutout._auto_interior_indices(object_geo)
    assert interior_indices == set()

    for index, contour in enumerate(object_geo):
        shape = cutout._gerber_contour_shape(contour, index, MARGIN, CUT_DIA, interior_indices)
        # Exactly what the tool did before the classification existed: offset outside the
        # contour's exterior ring, with no interior ring anywhere in the branch.
        expected = contour.buffer(MARGIN + abs(CUT_DIA / 2)).exterior
        assert shape.equals(expected)

    assert logged.messages == []


def test_with_the_option_off_a_negative_margin_is_unchanged(cutout, logged):
    cutout.ui.auto_interior_cb.set_value(False)
    contour = _slot()

    shape = cutout._gerber_contour_shape(contour, 0, -MARGIN, CUT_DIA, set())

    expected = contour.buffer(-(-MARGIN) + abs(CUT_DIA / 2)).interiors
    assert len(shape) == len(expected)
    for ring, wanted in zip(shape, expected):
        assert LineString(ring).equals(LineString(wanted))
    assert logged.messages == []


# The contours the pre-c848b5a offset is pinned over: a closed thin band, a circular band, a
# band carrying two rings, a polygon carrying three holes, and an open path with no exterior
# ring at all.
PRE_C848B5A_CONTOURS = {
    'rectangular-band': _outline(),
    'circular-band': _circle_band(0, 0, 30),
    'band-with-two-interior-rings': Polygon(
        [(0, 0), (40, 0), (40, 20), (0, 20), (0, 0)],
        [
            [(5, 5), (15, 5), (15, 15), (5, 15), (5, 5)],
            [(25, 5), (35, 5), (35, 15), (25, 15), (25, 5)],
        ],
    ),
    'polygon-with-three-holes': Polygon(
        [(0, 0), (60, 0), (60, 20), (0, 20), (0, 0)],
        [
            [(5, 5), (15, 5), (15, 15), (5, 15), (5, 5)],
            [(20, 5), (30, 5), (30, 15), (20, 15), (20, 5)],
            [(35, 5), (45, 5), (45, 15), (35, 15), (35, 5)],
        ],
    ),
    'open-linestring': LineString([(10, 10), (50, 10)]),
}


def pre_c848b5a_gerber_contour_shape(contour, margin, cut_dia):
    """The per-contour Gerber offset exactly as it stood before ``c848b5a``.

    Provenance: the revision before the classification landed, commit 6e4e7e3, file
    ``appPlugins/ToolCutOut.py``, the ``else`` branch of ``CutOut.on_freeform_cutout`` that
    iterates ``geom_struct``:

        if margin >= 0:
            geom_struct = (geom_struct.buffer(margin + abs(cut_dia / 2))).exterior
        else:
            geom_struct_buff = geom_struct.buffer(-margin + abs(cut_dia / 2))
            geom_struct = geom_struct_buff.interiors

    This expression is the specification S5 pins, so it is reproduced here on purpose: it is
    the historical behaviour, and the production code has to keep matching it when the option
    is off. It is a literal of plain shapely calls, not a reimplementation of any current
    production path, so the test stays a characterisation of the old output in any checkout.
    """
    if margin >= 0:
        return contour.buffer(margin + abs(cut_dia / 2)).exterior
    return contour.buffer(-margin + abs(cut_dia / 2)).interiors


@pytest.mark.parametrize(
    'contour',
    PRE_C848B5A_CONTOURS.values(),
    ids=list(PRE_C848B5A_CONTOURS),
)
@pytest.mark.parametrize('margin', [-0.5, 0.0, 0.5], ids=['negative', 'zero', 'positive'])
@pytest.mark.parametrize('cut_dia', [0.8, 2.0])
def test_with_the_option_off_the_offset_is_the_pre_c848b5a_expression(
        cutout, contour, margin, cut_dia):
    """S5: off means every contour takes the old exterior path, on every branch.

    The gate is off, so the interior set is empty, and ``_gerber_contour_shape`` has to
    produce exactly the historical output for a positive margin (the exterior ring), a zero
    margin and a negative one (the interior rings).
    """
    cutout.ui.auto_interior_cb.set_value(False)
    assert cutout._auto_interior_indices([contour]) == set()

    shape = cutout._gerber_contour_shape(contour, 0, margin, cut_dia, set())
    expected = pre_c848b5a_gerber_contour_shape(contour, margin, cut_dia)

    if margin < 0:
        assert len(shape) == len(expected)
        for ring, wanted in zip(shape, expected):
            assert LineString(ring).equals(LineString(wanted))
    else:
        assert shape.equals(expected)


# ============================================================================
# S2 — an interior contour contributes all of its rings
# ============================================================================

def test_an_interior_contour_with_two_rings_contributes_both(cutout, logged):
    cutout.ui.auto_interior_cb.set_value(True)
    # A partition wall inside a slot: the band encloses two regions, so buffering it leaves
    # two interior rings. Only the first one used to be carried into the cut.
    two_hole_band = Polygon(
        [(0, 0), (40, 0), (40, 20), (0, 20), (0, 0)],
        [
            [(5, 5), (15, 5), (15, 15), (5, 15), (5, 5)],
            [(25, 5), (35, 5), (35, 15), (25, 15), (25, 5)],
        ],
    )
    object_geo = [_outline(), two_hole_band]

    interior_indices = cutout._auto_interior_indices(object_geo)
    assert interior_indices == {1}

    shape = cutout._gerber_contour_shape(two_hole_band, 1, MARGIN, CUT_DIA, interior_indices)

    buffered = two_hole_band.buffer(MARGIN + abs(CUT_DIA / 2))
    assert len(buffered.interiors) == 2
    assert isinstance(shape, MultiLineString)
    assert len(shape.geoms) == 2
    for ring in buffered.interiors:
        wanted = LineString(ring)
        assert any(LineString(line).equals(wanted) for line in shape.geoms)


def test_the_contributed_rings_are_accepted_by_the_cut_handler(cutout):
    """The multi-ring shape must survive the rest of the job, not just the branch."""
    cutout.ui.auto_interior_cb.set_value(True)
    two_hole_band = Polygon(
        [(0, 0), (40, 0), (40, 20), (0, 20), (0, 0)],
        [
            [(5, 5), (15, 5), (15, 15), (5, 15), (5, 5)],
            [(25, 5), (35, 5), (35, 15), (25, 15), (25, 5)],
        ],
    )
    interior_indices = cutout._auto_interior_indices([_outline(), two_hole_band])
    shape = cutout._gerber_contour_shape(two_hole_band, 1, MARGIN, CUT_DIA, interior_indices)

    cut_paths, rest_paths = cutout.any_cutout_handler(shape, abs(CUT_DIA), 'None', 4.0, MARGIN)

    buffered = two_hole_band.buffer(MARGIN + abs(CUT_DIA / 2))
    assert len(cut_paths) == len(buffered.interiors) == 2
    assert all(not path.is_empty for path in cut_paths)
    for ring in buffered.interiors:
        wanted = LineString(ring)
        assert any(LineString(path).equals(wanted) for path in cut_paths)


# ============================================================================
# S3 — the wiring never degrades to silence
# ============================================================================

def test_an_interior_contour_without_a_hole_falls_back_loudly(cutout, logged):
    """A contour tiny enough to be swallowed by its own offset has no inside to cut."""
    tiny_pad = Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])
    buffered = tiny_pad.buffer(MARGIN + abs(CUT_DIA / 2))
    assert not buffered.interiors

    shape = cutout._gerber_contour_shape(tiny_pad, 4, MARGIN, CUT_DIA, {4})

    assert shape.equals(buffered.exterior)
    assert len(logged.messages) == 1
    assert "4" in logged.messages[0]


# ============================================================================
# S4 — the option is a Cutout preference, not only a tool-panel switch
# ============================================================================

def test_the_preferences_group_carries_the_option_with_the_shipped_default(fc_app):
    """Edit -> Preferences offers the option, bound the way its neighbours are bound.

    ``ToolsCutoutPrefGroupUI`` builds the widgets and ``PreferencesUIManager`` binds each one
    to an option key; a widget the manager does not list is a control the user can toggle and
    the application then ignores.
    """
    group = fc_app.ui.plugin_pref_form.tools_cutout_group
    manager = fc_app.preferencesUiManager

    widget = manager.defaults_form_fields[OPTION]
    assert widget is group.auto_interior_cb
    assert isinstance(widget, FCCheckBox)

    try:
        fc_app.defaults[OPTION] = False
        manager.defaults_write_form()
        assert widget.get_value() is False
    finally:
        fc_app.defaults[OPTION] = True
        manager.defaults_write_form()

    assert widget.get_value() is True
    assert fc_app.defaults[OPTION] is True


def test_a_changed_preference_reaches_the_option_the_tool_reads(fc_app):
    """Applying preferences carries the value down the same path the neighbours use.

    ``PreferencesUIManager.on_save_button`` reads the form into ``defaults`` and then copies
    ``defaults`` over ``app.options``; the Cutout tool reads ``app.options`` when it builds its
    own panel. A key missing from the form mapping never reaches either.
    """
    widget = fc_app.ui.plugin_pref_form.tools_cutout_group.auto_interior_cb
    manager = fc_app.preferencesUiManager
    tool = fc_app.cutout_tool

    try:
        widget.set_value(False)
        manager.on_save_button(save_to_file=False)

        assert fc_app.defaults[OPTION] is False
        assert fc_app.options[OPTION] is False

        tool.set_tool_ui()
        assert tool.ui.auto_interior_cb.get_value() is False
    finally:
        widget.set_value(True)
        manager.on_save_button(save_to_file=False)
        tool.set_tool_ui()

    assert fc_app.options[OPTION] is True


def test_the_neighbouring_cutout_preferences_still_round_trip(fc_app):
    """The shared preference plumbing still carries the options that already used it."""
    group = fc_app.ui.plugin_pref_form.tools_cutout_group
    manager = fc_app.preferencesUiManager
    original = group.convex_box.get_value()

    try:
        group.convex_box.set_value(not original)
        manager.on_save_button(save_to_file=False)
        assert fc_app.options["tools_cutout_convexshape"] is (not original)
    finally:
        group.convex_box.set_value(original)
        manager.on_save_button(save_to_file=False)

    assert fc_app.options["tools_cutout_convexshape"] is original


@pytest.fixture
def tools_db(fc_app):
    """A Tools Database editor built on the running application, without touching its file."""
    return ToolsDB2(app=fc_app, callback_on_tool_request=lambda tool: None)


def test_the_tools_database_cutout_form_binds_the_option(tools_db):
    """A database edit has to know which option the checkbox drives.

    ``update_storage`` and ``form_to_storage`` look the widget up in ``name2option``; a
    control that is in neither dictionary is a checkbox that silently edits nothing.
    """
    widget = tools_db.form_fields[OPTION]

    assert widget is tools_db.ui.cutout_auto_interior_cb
    assert isinstance(widget, FCCheckBox)
    assert tools_db.name2option[widget.objectName()] == OPTION


def test_a_tools_database_preset_loads_the_option_into_the_form(tools_db):
    """Opening a preset shows the value it stores, so the user can see and change it."""
    record = {"name": "cutout preset", "tooldia": 1.0, "data": {OPTION: False}}

    tools_db.storage_to_form(record)

    assert tools_db.ui.cutout_auto_interior_cb.get_value() is False


def test_a_new_tools_database_preset_starts_from_the_option(fc_app, monkeypatch):
    """The cutout data template is what a fresh database preset carries.

    The UI side effects of adding a row are stubbed out and normalization is bypassed, so the
    template is the only place the value can come from.
    """
    db = ToolsDB2(app=fc_app, callback_on_tool_request=lambda tool: None)
    monkeypatch.setattr(db, "normalize_tool_preset", lambda record: record)
    monkeypatch.setattr(db, "update_storage", lambda: None)
    monkeypatch.setattr(db, "build_db_ui", lambda: None)
    monkeypatch.setattr(db, "on_tool_target_changed", lambda *args, **kwargs: None)
    known_ids = set(db.db_tool_dict)

    db.on_tool_add()

    new_ids = set(db.db_tool_dict) - known_ids
    assert len(new_ids) == 1
    assert db.db_tool_dict[new_ids.pop()]["data"][OPTION] is True


def test_the_neighbouring_database_cutout_field_still_round_trips(tools_db):
    """The cutout section of the database editor still loads the values it always did."""
    record = {"name": "cutout preset", "tooldia": 1.0,
              "data": {"tools_cutout_convexshape": True, OPTION: True}}

    tools_db.storage_to_form(record)

    assert tools_db.ui.cutout_convex_box.get_value() is True
    assert tools_db.ui.cutout_auto_interior_cb.get_value() is True
