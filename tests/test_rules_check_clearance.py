"""Rules check: clearance filters on a layer whose aperture macro flashes a pad.

The three clearance rules in ``flatcam_plus/appPlugins/ToolRulesCheck.py`` collect every
aperture's ``solid`` geometry into a plain list and hand that list to ``MultiPolygon(...)``.
An aperture macro contributes a ``MultiPolygon`` as a single solid, so the list can hold a
nested ``MultiPolygon`` and the constructor rejects it with
``ValueError: Sequences of multi-polygons are not valid arguments``. The same crash was
already fixed in the Gerber parser and in the isolation/NCC distance paths, so a board that
parses and isolates fine could still not be rule-checked.

Two committed inputs cover it: ``tests/data/thermal_pad_macro.gbr`` is a ``THM_3SEG`` macro
whose flashed pad is stored as one nested ``MultiPolygon``, and ``tests/data/square_outline.gbr``
is a plain outline stored as a single ``Polygon``. ``tests/data/thermal_pad_macro_two_flash.gbr``
is the same macro flashed twice, at (4, 4) and (8, 8) mm: two nested solids, which is the case
where flattening alone left the rules counting and slicing a multi-part result, so the old code
failed on ``len()`` and iteration instead of on the constructor. ``tests/data/two_drills.drl``
supplies the Excellon side of the annular ring rule.

Every rule is driven through the same dict shape the plugin builds in ``RulesCheck.execute``:
``{'name': ..., 'apertures': <gerber>.tools}`` for a Gerber layer and
``{'name': ..., 'tools': <excellon>.tools}`` for a drill file.
"""

import math

import pytest
from shapely import Polygon

from flatcam_plus.appParsers.ParseExcellon import Excellon
from flatcam_plus.appParsers.ParseGerber import Gerber
from flatcam_plus.appPlugins.ToolRulesCheck import RulesCheck

RULE = "clearance"

# The macro pad is one 2.2 mm flash centred on (4, 4) mm, so its envelope is 2.9..5.1 mm.
PAD_LEFT, PAD_BOTTOM, PAD_RIGHT, PAD_TOP = 2.9, 2.9, 5.1, 5.1
# The two-flash input flashes the same pad again at (8, 8) mm, so the pair of pads spans
# 2.9..9.1 mm on both axes: a location between the two pads cannot leave that envelope.
TWO_FLASH_RIGHT = TWO_FLASH_TOP = 9.1
# The plain outline is a 10x10 mm board.
BOARD_LEFT, BOARD_BOTTOM, BOARD_RIGHT, BOARD_TOP = 0.0, 0.0, 10.0, 10.0


@pytest.fixture(scope="module")
def macro_layer(fc_app, sample_input):
    """A Gerber layer whose single solid is a nested ``MultiPolygon``."""
    gerber = Gerber(app=fc_app, steps_per_circle=64)
    assert gerber.parse_lines(sample_input("thermal_pad_macro.gbr")) is None
    return {"name": "macro", "apertures": gerber.tools}


@pytest.fixture(scope="module")
def multi_flash_layer(fc_app, sample_input):
    """A Gerber layer whose macro is flashed twice: two nested ``MultiPolygon`` solids."""
    gerber = Gerber(app=fc_app, steps_per_circle=64)
    assert gerber.parse_lines(sample_input("thermal_pad_macro_two_flash.gbr")) is None
    return {"name": "two_flash", "apertures": gerber.tools}


@pytest.fixture(scope="module")
def outline_layer(fc_app, sample_input):
    """The plain control: a Gerber layer whose solid geometry never nests."""
    gerber = Gerber(app=fc_app, steps_per_circle=64)
    assert gerber.parse_lines(sample_input("square_outline.gbr")) is None
    return {"name": "outline", "apertures": gerber.tools}


@pytest.fixture(scope="module")
def drill_layer(fc_app, sample_input):
    """The Excellon side the annular ring rule pairs the Gerber layer with."""
    excellon = Excellon(app=fc_app)
    excellon.parse_lines(sample_input("two_drills.drl"))
    # ``create_geometry`` is written for ``ExcellonObject``, which defines this attribute and
    # stores it in every tool; the bare parser has none, and the first drill hit then aborts
    # the loop after adding its own polygon. Pass the same empty default the object uses so
    # both hits from the sample reach ``solid_geometry``.
    excellon.default_data = {}
    excellon.create_geometry()
    assert len(excellon.tools[1]["solid_geometry"]) == 2
    return {"name": "drills", "tools": excellon.tools}


def one_violation(result):
    """Unpack the ``(rule, [violation])`` shape every clearance rule returns."""
    rule, violations = result
    assert rule == RULE
    assert isinstance(violations, list)
    assert len(violations) == 1
    return violations[0]


def assert_points_within(points, left, bottom, right, top):
    """Every recorded violation location is a real point inside the given envelope."""
    assert isinstance(points, list)
    assert points
    for point in points:
        assert isinstance(point, tuple)
        assert len(point) == 2
        x, y = point
        assert math.isfinite(x) and math.isfinite(y)
        assert left <= x <= right, (point, "outside", left, right)
        assert bottom <= y <= top, (point, "outside", bottom, top)


def test_inside_clearance_accepts_a_macro_solid(macro_layer):
    # Used to raise "Sequences of multi-polygons are not valid arguments".
    violation = one_violation(
        RulesCheck.check_inside_gerber_clearance(macro_layer, 20.0, RULE)
    )
    assert violation["name"] == "macro"
    assert_points_within(violation["points"], PAD_LEFT, PAD_BOTTOM, PAD_RIGHT, PAD_TOP)


def test_inside_clearance_accepts_a_macro_flashed_twice(multi_flash_layer):
    # Two nested solids reach MultiPolygon(...) as a plain list, and the multi-part result then
    # has to be counted and sliced as parts. Both pads are closer than the 20 mm window, so the
    # rule reports the pairs it measured between them.
    violation = one_violation(
        RulesCheck.check_inside_gerber_clearance(multi_flash_layer, 20.0, RULE)
    )
    assert violation["name"] == "two_flash"
    assert_points_within(
        violation["points"], PAD_LEFT, PAD_BOTTOM, TWO_FLASH_RIGHT, TWO_FLASH_TOP
    )


def test_gerber_to_gerber_clearance_accepts_a_macro_flashed_twice(
    multi_flash_layer, outline_layer
):
    # The same two nested solids against a plain outline layer. A location here is the midpoint
    # between a pad edge and the board outline, so it can leave the pads' envelope and is only
    # bounded by the 10x10 mm board.
    violation = one_violation(
        RulesCheck.check_gerber_clearance([multi_flash_layer, outline_layer], 20.0, RULE)
    )
    assert violation["name"] == ["two_flash", "outline"]
    assert_points_within(violation["points"], BOARD_LEFT, BOARD_BOTTOM, BOARD_RIGHT, BOARD_TOP)


def test_inside_clearance_for_a_plain_outline_is_unchanged(outline_layer):
    # Baseline recorded before the macro input was made safe: the single solid flattens to
    # one polygon, so the rule still reports that it has nothing to compare against.
    assert RulesCheck.check_inside_gerber_clearance(outline_layer, 20.0, RULE) == (
        RULE,
        [{"name": "outline", "points": ["Failed. Only one polygon."]}],
    )


def test_inside_clearance_keeps_the_clear_polarity_path(outline_layer):
    # A clear aperture makes the rule build a plain list of trimmed solids instead of a
    # MultiPolygon; that list still has to be counted and sliced, not treated as geometry.
    solid = outline_layer["apertures"][10]["geometry"][0]["solid"]
    # A 0.4 mm square inside the 1 mm wide ring the outline traces, so it trims the solid.
    trim = Polygon([(0.0, 0.0), (0.4, 0.0), (0.4, 0.4), (0.0, 0.4)])
    assert trim.within(solid)
    layer = {
        "name": "trimmed",
        "apertures": {10: {"geometry": [{"solid": solid, "clear": trim}]}},
    }
    assert RulesCheck.check_inside_gerber_clearance(layer, 20.0, RULE) == (
        RULE,
        [{"name": "trimmed", "points": []}],
    )


def test_gerber_to_gerber_clearance_accepts_a_macro_solid_as_the_copper_layer(
    macro_layer, outline_layer
):
    # Used to raise "Sequences of multi-polygons are not valid arguments".
    violation = one_violation(
        RulesCheck.check_gerber_clearance([macro_layer, outline_layer], 20.0, RULE)
    )
    assert violation["name"] == ["macro", "outline"]
    assert_points_within(violation["points"], BOARD_LEFT, BOARD_BOTTOM, BOARD_RIGHT, BOARD_TOP)


def test_gerber_to_gerber_clearance_accepts_a_macro_solid_as_the_outline_layer(
    outline_layer, macro_layer
):
    # Used to raise "Sequences of multi-polygons are not valid arguments".
    violation = one_violation(
        RulesCheck.check_gerber_clearance([outline_layer, macro_layer], 20.0, RULE)
    )
    assert violation["name"] == ["outline", "macro"]
    assert_points_within(violation["points"], BOARD_LEFT, BOARD_BOTTOM, BOARD_RIGHT, BOARD_TOP)


def test_gerber_to_gerber_clearance_for_plain_outlines_is_unchanged(outline_layer):
    # Baseline recorded before the macro input was made safe: two identical 10x10 mm
    # outlines overlap, so the only filter hit is the overlapping edge pair.
    violation = one_violation(
        RulesCheck.check_gerber_clearance([outline_layer, outline_layer], 20.0, RULE)
    )
    assert violation["name"] == ["outline", "outline"]
    assert violation["points"] == [pytest.approx((-0.5002501250625312, 0.0))]


def test_annular_ring_accepts_a_macro_solid(macro_layer, drill_layer):
    # Used to raise "Sequences of multi-polygons are not valid arguments".
    violation = one_violation(
        RulesCheck.check_gerber_annular_ring([macro_layer, drill_layer], 40.0, RULE)
    )
    assert violation["name"] == ["macro", "drills"]
    # A location is the midpoint between a copper edge and a drill outline, and the sample
    # drills sit at (10, 10) and (20, 20), so it can lie outside the 10x10 mm board.
    assert_points_within(violation["points"], -1.0, -1.0, 21.0, 21.0)


def test_annular_ring_for_a_plain_outline_is_unchanged(outline_layer, drill_layer):
    # Baseline recorded before the macro input was made safe.
    violation = one_violation(
        RulesCheck.check_gerber_annular_ring([outline_layer, drill_layer], 40.0, RULE)
    )
    assert violation["name"] == ["outline", "drills"]
    # One location per drill hit, in ascending distance order.
    assert violation["points"] == [
        pytest.approx((10.447889788362563, 10.044731335150324)),
        pytest.approx((15.035443771623257, 15.035443771623257)),
    ]
