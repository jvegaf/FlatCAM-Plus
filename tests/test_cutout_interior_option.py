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

import pytest
from shapely import LineString, MultiLineString, Polygon

import flatcam_plus.appPlugins.ToolCutOut as tool_cutout
from flatcam_plus import defaults as app_defaults

OPTION = "tools_cutout_auto_interior"

MARGIN = 0.1
CUT_DIA = 2.0


def _band(coords, width=0.254):
    """A Gerber profile path: the drawn line buffered with the aperture width / 2."""
    return LineString(coords).buffer(width / 2)


def _outline():
    return _band([(0, 0), (100, 0), (100, 60), (0, 60), (0, 0)])


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
