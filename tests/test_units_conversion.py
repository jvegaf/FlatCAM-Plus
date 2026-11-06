"""The unit arithmetic must round-trip before anything live is converted.

Converting a project is the one operation here that can quietly destroy a user's geometry, so
the maths is pinned on its own: both directions, identity when the units already match, and a
round trip that has to return the original coordinates.
"""

import pytest
from shapely.geometry import LineString, Point, box

from flatcam_plus.appCommon import units

TOLERANCE = 1e-9


def test_conversion_factor_both_directions():
    assert units.conversion_factor("MM", "IN") == pytest.approx(1.0 / 25.4)
    assert units.conversion_factor("IN", "MM") == pytest.approx(25.4)


def test_conversion_factor_is_one_for_the_same_units():
    assert units.conversion_factor("MM", "MM") == 1.0
    assert units.conversion_factor("in", "IN") == 1.0


def test_normalize_units_accepts_the_spellings_the_app_uses():
    assert units.normalize_units("mm") == units.MM
    assert units.normalize_units(" MM ") == units.MM
    assert units.normalize_units("inch") == units.IN
    with pytest.raises(ValueError):
        units.normalize_units("furlongs")


def test_a_length_converts_to_the_expected_number():
    assert units.convert_length(25.4, "MM", "IN") == pytest.approx(1.0)
    assert units.convert_length(1.0, "IN", "MM") == pytest.approx(25.4)


def test_a_length_round_trips_within_tolerance():
    original = 12.3456789
    there = units.convert_length(original, "MM", "IN")
    back = units.convert_length(there, "IN", "MM")
    assert back == pytest.approx(original, abs=TOLERANCE)


def test_geometry_converts_and_round_trips():
    original = box(0.0, 0.0, 25.4, 50.8)

    inches = units.convert_geometry(original, "MM", "IN")
    assert list(inches.bounds) == pytest.approx([0.0, 0.0, 1.0, 2.0])

    back = units.convert_geometry(inches, "IN", "MM")
    assert list(back.bounds) == pytest.approx(list(original.bounds), abs=TOLERANCE)


def test_geometry_conversion_preserves_the_shape_type():
    line = LineString([(0, 0), (10, 0), (10, 10)])
    converted = units.convert_geometry(line, "MM", "IN")
    assert converted.geom_type == line.geom_type
    assert len(converted.coords) == len(line.coords)


def test_matching_units_return_the_same_object():
    """Callers compare identity to decide whether anything needs replacing."""
    original = Point(1.0, 2.0)
    assert units.convert_geometry(original, "MM", "MM") is original


def test_a_geometry_list_converts_element_wise():
    geometries = [Point(0, 0), Point(25.4, 25.4)]
    converted = units.convert_geometry_list(geometries, "MM", "IN")

    assert len(converted) == 2
    assert converted[1].x == pytest.approx(1.0)
    assert converted[1].y == pytest.approx(1.0)

    back = units.convert_geometry_list(converted, "IN", "MM")
    assert back[1].x == pytest.approx(25.4, abs=TOLERANCE)


def test_a_geometry_list_in_matching_units_is_copied_not_shared():
    geometries = [Point(0, 0)]
    converted = units.convert_geometry_list(geometries, "MM", "MM")
    assert converted == geometries
    assert converted is not geometries
