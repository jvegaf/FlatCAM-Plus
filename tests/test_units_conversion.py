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


class _StubObject:
    """Mimics an object whose convert_units either works or silently refuses."""

    def __init__(self, name, refuses=False, bounds=(0.0, 0.0, 25.4, 25.4)):
        from shapely.geometry import box

        self.obj_options = {"name": name}
        self.units = units.MM
        self.refuses = refuses
        self._box = box(*bounds)
        self.solid_geometry = [self._box]

    def convert_units(self, target):
        if self.refuses:
            return  # Gerber.convert_units returns early when the file declared units
        factor = units.conversion_factor(self.units, target)
        from shapely import transform as rebase

        self._box = rebase(self._box, lambda coords: coords * factor)
        self.solid_geometry = [self._box]
        self.units = target


def test_convert_objects_converts_everything_when_all_accept():
    first = _StubObject("top_copper")
    second = _StubObject("drill")

    ok, refused = units.convert_objects([first, second], "MM", "IN")

    assert ok is True
    assert refused == []
    assert first.units == "IN"
    assert first.solid_geometry[0].bounds == pytest.approx((0.0, 0.0, 1.0, 1.0))
    assert second.units == "IN"


def test_a_silent_refusal_rolls_back_the_objects_already_converted():
    """The whole point: no half-converted project, ever."""
    willing = _StubObject("top_copper")
    refusing = _StubObject("declared_units", refuses=True)

    ok, refused = units.convert_objects([willing, refusing], "MM", "IN")

    assert ok is False
    assert refused == ["declared_units"]
    assert willing.units == "MM", "a converted object was not rolled back"
    assert willing.solid_geometry[0].bounds == pytest.approx((0.0, 0.0, 25.4, 25.4))
    assert refusing.units == "MM"


def test_matching_units_touch_nothing():
    obj = _StubObject("top_copper")
    ok, refused = units.convert_objects([obj], "MM", "MM")
    assert ok is True
    assert refused == []
    assert obj.units == "MM"


def test_an_empty_project_converts_trivially():
    ok, refused = units.convert_objects([], "MM", "IN")
    assert ok is True
    assert refused == []


def test_an_object_without_convert_units_counts_as_a_refusal():
    """Crashing here would strand the project in whatever state earlier objects reached."""

    class _NoConversion:
        def __init__(self):
            self.obj_options = {"name": "legacy_object"}

    willing = _StubObject("top_copper")
    legacy = _NoConversion()

    ok, refused = units.convert_objects([willing, legacy], "MM", "IN")

    assert ok is False
    assert refused == ["legacy_object"]
    assert willing.units == "MM", "the converted object was not rolled back"
